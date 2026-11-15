# Monsters

## Status
Shipped and heavily reworked through v2.18.0 (commit `409e15d`, 2026-09-27). The 527-entry catalog, Monster class, AI dispatch, boss levels, and spawn pool are in production. A systems audit landed a wave of P0/P1 fixes in v2.18.0 (`is_boss` JSON wire, 4 orphan legendaries given `spawn_chance`, DeathMonster kwargs, chain-break dead-wire noted). Several dead JSON fields (`harvest_threshold`, `ingredient_id`, `attack_effects`, `mortal_weapon_floor`, `chain_break_on_hit`) survive on disk for pickle compat and because the audit opted to document-rather-than-migrate.

## Code
- `src/monster.py` — the Monster class, `_DEFAULTS`, `__getattr__` back-compat shim, `take_damage`, `attack`, `take_turn` dispatch, 14 AI pattern methods, and `DeathMonster` subclass. 1750 lines.
- `src/monster_classes.py` — `get_monster_family(...)`, a thin reader of each monster's written `family` field (one of 22; see [monster_families](monster_families.md)). The old tag-priority guess (`FAMILY_PRIORITY`) was retired 2026-10-18.
- `src/family_lore.py`, `src/family_edges.py`, `src/game_families.py` — monster family knowledge: who is in which family, the tiers a hero earns by studying kinds, and the techniques each tier grants ([monster_families](monster_families.md)).
- `src/boss_levels.py` — hand-crafted boss floors `L20/40/60/80/100` plus `COW_LEVEL=999`. One static map per level with hand-placed stairs, pillars/altars/ice patches, and a single `_spawn_boss(dungeon, boss_id, boss_room)` placement with NW-shift fallback for multi-tile bosses.
- `src/level_manager.py` — floor-generation front door. Pre-rolls planned mini-bosses at run start, forces seal-demon spawns on `L83/85/87/89/91/93/97`, and routes boss floors through `boss_levels.generate_boss_level`.
- `src/dungeon.py::_build_spawn_pool` (line 1230), `_footprint_fits`, `_spawn_one_in_room`, `spawn_monsters`, `populate_floor` — the procedural pool and placement.
- `src/game_combat.py::_drop_treasure`, `_spawn_treasure_item`, `_spawn_archer_ammo`, `_spawn_boss_scroll`, `_spawn_unique_item`, `_make_corpse` — death-side loot and corpse creation.
- `src/combat.py::_damage_multiplier` — the step a typed hit takes (weak x2, resisted x0.5, shrugs off x0.25: `data/affinity_rules.json`); `weapon_type_multiplier` for a weapon blow (form x substance, capped x3).
- `data/family_affinity.json` + `tools/content/affinity_pass.py` — the lore profiles that write every kind's `weaknesses`, `resistances`, `shrugs_off`, `status_immune`, `status_weak`.
- `src/hero_specials.py::is_boss_or_huge` (line 19) — the `boss_immune` gate used by charm / paralyze / sleep / confuse / immobilize.
- `src/geom.py` — footprint helpers (`is_adjacent`, `occupied_tiles`, `all_occupied_tiles`, `monster_at_tile`) that handle multi-tile bosses correctly; the Monster class routes through these rather than comparing `(m.x, m.y)` directly.

## Data
- `data/monsters.json` — 574 monster definitions keyed by id. 28,712 lines (every monster is a top-level key with `name`, `symbol`, `color`, `hp`, `attacks`, `ai_pattern`, …).

## Related
- [combat](combat.md) — damage pipeline (THAC0, resistance multiplier, dragon_scales, status DCs), chain mode, chain-passives.
- [world](world.md) — procedural dungeon generation, rooms, special-rooms, hidden chambers that cross-call the monster spawn pool.
- [quests_mysteries](quests_mysteries.md) — the 7-seal / Abaddon arc, bones ghosts, mystery/encounter spawns that bypass the pool.
- [food_system](food_system.md) — harvest resolution. `harvest_tier` on the monster becomes `corpse.harvest_tier`; the prime-cut drop is looked up by `monster.kind` in `data/prime_cuts.json` (NOT by the dead `ingredient_id` field).

## Purpose
The game needs a large, varied bestiary that:
1. Reads from data (JSON) — no hardcoded monsters outside of the DeathMonster failsafe and the boss-level loaders.
2. Scales smoothly with depth — common at a monster's `peak_floor`, rare at the edges, with no jarring tier gates. Shallow fodder phases out; late threats phase in.
3. Supports distinctive AI (hit-and-run minotaur, gaze-attack gorgon, phase-wall vampire, rage wolf, swarm angel, flanking goblins) without a NetHack-sized zoo of hardcoded behaviours — AI shapes are composed from JSON flags.
4. Lets hand-crafted bosses co-exist with procedural spawns on the same floor and the same game-loop (same Monster class, same `take_turn` dispatch).

## Design intent

### "574 monsters" without 574 classes
Every monster is an instance of the single `Monster` class. Behavioural differences come from JSON fields — `ai_pattern` picks a dispatch branch, flags like `can_charge` / `can_phase_blink` / `prefers_flank` compose on top of it, and status/damage interactions come from the `attacks[]` and `resistances`/`weaknesses`/`tags` arrays. `monster_classes.py` is NOT an OO hierarchy; it reads the written `family` field.

### Bell-curve spawn, no hard tiers
`_build_spawn_pool(level)` loops over every monster definition with `peak_weight > 0` and `min_level <= level` and computes a Gaussian weight at `distance = level - peak_floor` with sigma `= spread`. A monster appears everywhere its bell has mass; dropouts (bell < 0.005) fall out entirely rather than clamping to a floor. The lore-floor `min_level` is still a hard gate (seal demons don't appear on L1), but there's no `max_level` — late peaks simply have thin tails into the shallows and vice versa. This replaces an older min/max-level clamp that produced "all giant rats on floors 1-5, zero giant rats ever again."

### `peak_weight = 0` means "not in the random pool"
Bosses, seal demons, forced quest spawns, and the four orphan legendaries carry `peak_weight: 0`. They are placed by `level_manager` / `boss_levels` / mystery/encounter paths, never from `_build_spawn_pool`. The field is overloaded: `peak_weight > 0` means "procedurally spawnable at depth"; `peak_weight == 0` means "someone else places this."

### Mini-boss PRE-ROLLING
On run start, `LevelManager.__init__` calls `_roll_planned_mini_bosses()`, which iterates five 20-floor bands (`1-20`, `21-40`, `41-60`, `61-80`, `81-100`) and in each band fills a primary slot (90% chance) and a secondary slot (30% chance). Each slot picks weighted by `spawn_chance`. Expected total per 100-floor run: 5 × 1.2 = **6 mini-bosses**, range 4-8. The placement floor is the chosen mini-boss's `peak_floor` (shifted ±1 if it collides with a boss floor or a planned slot). This replaces first-eligible-wins greedy placement — now every band member has weighted odds every run.

### Seal demons are FORCED, not rolled
`_SEAL_DEMON_LEVELS = {83, 85, 87, 89, 91, 93, 97}` → 7 fixed seal-demon ids. `_try_spawn_seal_demon` runs after mini-boss pre-rolling, is-mini-boss aware (the pre-roller ignores `seal_demon_*` ids), and guarantees placement. Each seal-demon kill is tracked in `game.seals_broken`; at 7/7 the game logs the "way to the Pit stands open" Journal entry.

### Boss immunity: a two-step check, now with a JSON wire
`hero_specials.is_boss_or_huge(monster)` is the one function status-application code calls. Through v2.17 it was effectively `max_hp > 500`, since `Monster.__init__` silently dropped the JSON `is_boss` field. v2.18.0 added `self.is_boss = bool(defn.get('is_boss', False))` to `__init__` — the fallback stays as a safety net, but 10 mini-bosses (`iron_patriarch`, `whispering_crone`, `blood_archon`, 7 `seal_demon_*`) now get boss-immunity properly instead of relying on their HP dice happening to exceed 500. `boss_immune: True` on a hero special says "this status skips bosses"; the check is monster-side (`is_boss_or_huge`) and the special-side flag just gates whether to apply the check.

### Multi-tile monsters are NW-anchored rectangles
The default `footprint` is `[1, 1]` (every regular monster). Five bosses declare `[2, 2]`:
- `fafnir_dragon` — L58-62, hand-placed in Dragon Hoard (L60).
- `tiamat` — L85-95, procedural at depth.
- `surtur` — L87-93, procedural at depth.
- `ymir_last_spawn` — L82-88, procedural at depth.
- `hrungnirs_ghost` — L80-85, procedural at depth.

A multi-tile monster occupies 4 tiles with its anchor at the NW corner. `Monster._can_move_to` validates every footprint tile is walkable (and phase-walls where applicable). `geom.monster_at_tile` / `is_adjacent` / `occupied_tiles` must be used everywhere the game queries "is monster at (x, y)" — a raw `(m.x, m.y)` compare would miss the SE 3 tiles of a 2×2. `boss_levels._spawn_boss` shifts the anchor NW up to 3 tiles if the naïve room center can't fit the whole footprint. `dungeon._footprint_fits` enforces the same at procedural spawn.

## Schema — a Monster JSON entry

A single key in `data/monsters.json`. The id is the JSON key; the id is also written back into the defn as `defn['id']` by `boss_levels._load_boss` and both spawn paths.

### Core identity

| field | type | required | notes |
|---|---|---|---|
| `name` | str | yes | Display name. Lowercase for common monsters (`"giant rat"`), Title Case + descriptor for bosses (`"Fafnir the Dragon"`). Singular: one creature is "Lesser Erinys", never the plural "Erinyes" (round 3). A kind named for its master ("Fionn's Hound", "Set's Jackal") takes no article, like a named foe (`monster._is_proper`). |
| `pronoun` | `"it"` / `"he"` / `"she"` | yes (all 583) | How every line speaks of it (round 3, 2026-11-14; Brandon: "it unless clearly humanoid, then use appropriate: most will be he, but some, clearly feminine ... should be she"). `it`: beasts, vermin, swarms, oozes, plants, constructs, elementals, the mindless, bare-bone skeletons, bodiless ghosts, and demons and aberrations (their lore says "it"). `he`: anything shaped and minded like a person (goblinkin, giants, mortals, the corporeal humanoid dead: zombies, ghouls, wights, mummies, vampires, liches with a body), the named gods and heroes. `she`: every `female_attractive` kind (Ash's Give Me Some Sugar), hags, witches, gorgons, valkyries, the Furies, the Sphinx, the Keres, and any kind whose name or lore makes her a woman. `monster.pronouns(m)` gives (subject, object, possessive): an unseen creature or an un-sprung lurker is "it", a pickled monster from before the field takes its kind's (`kind_pronoun`), a polymorphed one the new kind's. `monster.fill(m, text)` puts `{The}`, `{the}`, `{A}`, `{a}`, `{he}`, `{He}`, `{him}`, `{his}`, `{His}`, `{himself}` into a data line (tells, senses, Recall Lore, war-bands, the affinity lines, family technique lines). Pets: `Pet.pronouns()` (Sherlock and Shep "he", Irene "she", the cloaked Emberpup "he", any other "it"). |
| `symbol` | str | yes | Single ASCII character for the ASCII fallback renderer (`r`, `D`, `A`). Follows NetHack glyph conventions (lower = humanoid/animal; upper = boss/large). |
| `color` | [int, int, int] | yes | RGB tuple cast to tuple on load. |
| `hp` | str (dice) | yes | Dice notation (`"2d6"`, `"125d12+695"`). Parsed by `dice.roll`. A pure digit string is accepted as a flat HP (`"1"` for DeathMonster). |
| `speed` | int | default 10 | Scheduling tempo. `>= 14` → double-move. `< 8` → `(8 - speed) / 10` chance to skip a turn (speed 6 skips 20%, speed 4 skips 40%, …). Variable-speed logic lives inside `take_turn`. |
| `min_level` | int | default 1 | Hard floor-gate (lore plausibility). `_build_spawn_pool` rejects outright if `min_level > level`. |
| `max_level` | int or null | default null | Soft cap — currently unused in the Gaussian pool; retained for pickle compat. |
| `peak_floor` | int | default `min_level` | Center of the Gaussian bell. The depth where this monster is most common. |
| `spread` | int | default 10 | Sigma of the Gaussian. Larger spread = flatter, wider range. Clamped to `>= 1`. |
| `peak_weight` | float | default 0 | Peak Gaussian weight (common ~ 1-10, rare ~ 0.5). `peak_weight <= 0` ⇒ monster is EXCLUDED from the procedural pool (bosses, seal demons, orphan legendaries). |
| `spawn_chance` | float | optional | Only read by `_roll_planned_mini_bosses` — the per-slot weight for mini-boss selection. Unrelated to `peak_weight`. |
| `frequency` | int | legacy, default 3 | Only consulted inside `_spawn_one_in_room` for pack-size scaling (`freq >= 5` → +1 max). Not the main spawn knob. |
| `thac0` | int | default `max(-10, 20 - min_level)` | AD&D-style "to-hit AC 0." Lower is more accurate. Since 3.3.2 rebaked to the armour line by `tools/balance/rebake_thac0.py` (a typical monster hits a hero of its floor about 55% of the time; [armour.md](armour.md)). |
| `thac0_lore` | int | | The written THAC0 before the rebake: the tool always starts from it, keeping half of each monster's accuracy against its band. |

### Boss / role flags

| field | type | notes |
|---|---|---|
| `is_boss` | bool | **Read from JSON since v2.18.0.** Grants boss-immunity to charm/paralyze/sleep/confuse via `hero_specials.is_boss_or_huge`. Also lifts `min_hit_chance` from 5% to 25%. Carried by: `abaddon_destroyer`, the 7 `seal_demon_*`, `iron_patriarch`, `whispering_crone`, `blood_archon`. **Fallback:** `max_hp > 500` also counts as boss, regardless of this flag — the hand-crafted boss-level `_spawn_boss` additionally forces `boss.is_boss = True` after construction. |
| `is_mini_boss` | bool | Candidate for the pre-rolled mini-boss slot system. 36 monsters carry this flag; `_roll_planned_mini_bosses` filters out `seal_demon_*` (forced path) and `spawn_chance <= 0`. **Known overlap:** `blood_archon` + the 7 seal demons carry BOTH `is_boss` and `is_mini_boss` — audited as a conflict P4, kept as-is. |
| `is_seal_demon` | bool | 7 monsters. On death, `game_combat._drop_treasure` adds the corresponding seal to `game.seals_broken` and writes a Journal line. 7/7 opens the Abyss narrative. |
| `is_allied` | bool | Allied monster (currently only `heavenly_angel`). Does not attack the player; dispatched to `seek_locust` AI. |
| `boss_immune` | — | NOT a Monster field; this is a flag on `hero_specials` entries declaring "my effect should skip bosses." The monster side is `is_boss` / `is_boss_or_huge`. |

### AI shape

| field | type | notes |
|---|---|---|
| `ai_pattern` | str | One of 15 values — see §"AI dispatch" below. Default `aggressive`. |
| `perception_range` | int | default 8 | How far a monster SEES (Chebyshev), along a real line of sight (`senses.clear_view`). It no longer notices through walls. `passive_silent_walk` (Hand of Glory, Boots of Elvenkind) halves it against the wearer and silences footsteps. See "Senses" below. |
| `alert_radius` | int | default 5 | Chebyshev radius for `alert_nearby` (same-kind allies wake up when I'm adjacent to the player). |
| `alert_all_tag` | bool | default False | Warlord/horn-blower mode — alert any monster sharing at least one tag, not just same-kind. |
| `aggression` | — | Not a Monster field; "aggression" is expressed via `ai_pattern` + flags, not a scalar. |
| `pack` | bool | default False | Spawner hint: when this monster is picked for a room, extra copies also spawn in the same room. Pack size scales with depth (1-2 shallow, 2-3 mid, 2-4 deep) and gets +1 max when `frequency >= 5`. |
| `pack_dependent` | bool | default False | Re-evaluates aggression each turn: `aggressive` when `pack_min_allies` same-kind/tag allies are within 5 tiles, else `cowardly`. Four monsters use this: `goblin_kingslayer`, `bandit_thug`, `bandit_archer`, `cult_initiate`. |
| `pack_min_allies` | int | default 1 | Threshold used by `pack_dependent`. |
| `prefers_flank` | bool | default False | Rotates approach direction 90° when an ally is already pressuring the player on the same vector. 3 monsters. |
| `can_phase_walls` | bool | default False | Movement can pass through `dungeon.phasing_walls`. Three monsters: `asterion_minotaur` (hit-and-run), `elder_vampire`, `ancient_vampire_lord`. |
| `can_phase_blink` | bool | default False | Chance to teleport adjacent when `>= 3` tiles from the player. 7 monsters. |
| `phase_blink_chance` | float | default 0.30 | Per-turn chance when eligible. |
| `can_charge` | bool | default False | Arms a damage multiplier when approaching the player on a cardinal or diagonal axis at distance 2-5. 7 monsters. |
| `charge_bonus_mult` | float | default 1.5 | Damage multiplier when a charged attack lands. |
| `regeneration` | int | default 0 | HP per turn. Blocked by `burning`, `deep_wound`, `ruptured`. 16 monsters (trolls, hydras, green knight, Baba Yaga, Abaddon@15, Mythic Hydra@5). |
| `revive_once_on_death` | bool | default False | First kill pops back up at `revive_hp_pct`. **Green Knight only** — the beheading-game pact. |
| `revive_hp_pct` | float | default 0.5 | HP fraction after revive. |
| `drain_heals_self` | float | default 0.0 | 1.0 = full heal from damage of drain attacks; 0.5 = half. Two monsters: `vampire` 1.0, `ancient_vampire_lord` 1.0. |
| `pull_chance` | float | default 0.0 | Grappler family — chance a hit drags the player one tile toward the monster. Charybdis / kraken. |
| `gaze_paralyze` | int | default 0 | Paralysis duration on gaze. Blocked by blindness (sight_radius 0); reflected by Aegis of Athena (shield turns gaze back on Medusa). `floating_eye` 4, `medusa_gorgon` 3. |
| `gaze_cooldown` | int | default 4 | Turns between gazes. |
| `gaze_group` | str | default "" | Gazers in one group share one gaze: when any of them uses it, every living member waits out the cooldown, so the group never paralyses twice in one turn. `stheno_gorgon` and `euryale_gorgon` ("gorgon_sisters"; Stheno 2 turns, Euryale 1). |
| `dragon_scales` | float | default 0 | Fraction of damage absorbed in `combat.py`'s melee pipeline. `fafnir_dragon` 0.8. |

### Lore-driven behaviour keys (late-game monsters, 2026-10)

| field | type | notes |
|---|---|---|
| `after_theft` | str | default `"flee"` | What a thief does once it holds a haul: `"flee"` runs from the hero, `"teleport"` first vanishes to a far part of the floor (the leprechauns). See `theft.py`. |
| `disguise` | dict | default none | What an un-sprung `mimic`-AI creature is drawn as: `{"item": <item sprite id>, "name": ...}` (a chest) or `{"tile": "stairs_down", "name": ...}` (the Hellmouth, seated by `false_stairs.py`). Read by `unseen.disguise`; shown in the bestiary as "Poses as". |
| `fearless` | bool | default False | Never flees and cannot be frightened (`Monster.resists_control` refuses `feared`, and it is stripped each turn). The galla. The Bestiary says "Fearless" only once the kind is known, like its other immunities. |
| `kill_chronicle` | str | default "" | The Journal line written when this mini-boss dies, instead of the generic one (`game_combat` kill handler). |
| `kill_pair` / `kill_pair_chronicle` | str / str | default "" | A named pair: the partner's monster id, and a second Journal line written only when the second of the two dies (after her own `kill_chronicle`). Stheno and Euryale (MON-10). |
| `pack_size` | [min, max] | default none | Fixes a lore pack's number, leader included (the three Furies, Keres three to five). Overrides the depth-scaled pack roll in `dungeon._spawn_one_in_room`. |
| `proper_noun` | bool | default False | The name is a person's name, so `the_name` never adds "the". |
| `sight_sign` | str | default "" | What the eye sees of it, said the first time the hero sees the kind whatever he knows of it (`Game._maybe_tell`) and by Observe: a sight, not lore. `{The}` / `{the}` name it. Old Nickel's leaf cloak. |
| `wary` | dict | default none | It does not start the fight (`Monster._wary_turn`, winning-build plan 3.8): it watches (`senses.sees`, so an invisible hero goes unseen), keeps `keep` tiles off inside its own room (`_wary_home`), warns once inside `radius` (`warn`), and fights from the moment the hero comes beside it, corners it or strikes it first (`provoked`: `struck` / `cornered` / `close` lines). It swipes at no pet until provoked. Old Nickel, who wears the Bloomleaf Cloak (`src/emberpup_encounter.py` (BloomleafMixin)); his room never holds the pup, a stall or one of the Road's people (an anchor, a story NPC, the unicorn, an escort), and no encounter NPC is set down in it. |
| `quarrelsome` | bool | default False | While confused it strikes a neighbour of its own kind instead of stumbling (the Sown Men). |
| `quarrels_when_struck_by_thrown` | int | default 0 | Turns of confusion a thrown object inflicts on it (Cadmus's stone); pairs with `quarrelsome`. |
| `splits` | dict | default none | `{"by": "weak_blow" \| [damage forms], "share", "into", "max"}`: struck the wrong way it divides or lets out another creature. See `splitting.py`. |
| `stationary` | bool | default False | Documents a creature that never moves (the Black Knight). Not read from JSON: the `BlackKnight` class sets it, and `ai_pattern: sessile` does the work. |
| `weighs_heart` | bool | default False | Its blows are scaled by the hero's karma: `monster.heart_weight` = `1 - 0.04 × karma` (harder on a low karma). The bestiary line stays oblique and never names karma. |

### Enrage / phase-change

| field | type | notes |
|---|---|---|
| `enrage_at_hp_pct` | float | default 0 | One-way phase swap: when HP drops to `≤ max_hp × this`, `ai_pattern` is replaced by `enraged_pattern`. 15 monsters. |
| `enraged_pattern` | str | | Target AI pattern. For bosses this is usually `aggressive` after a `summoner` or `abaddon` opening phase. **Audit note:** `grave_knight` sets `enraged_pattern: fenrir_rage` but omits `rage_interval` / `rage_damage_bonus` — the swap is a functional no-op. |
| `rage_interval` | int | default 0 | Fenrir rage: every N turns, a rage stack is added, triggering escalating damage/speed. 0 = no rage. |
| `rage_damage_bonus` | str (dice) | | Extra damage per stack per attack. |
| `multi_attack_count` | int | default 0 | Fires the first N attacks per turn (not random choice). Enables Tiamat/Asmodeus/Abaddon phase-1 2-of-5 ramp. |
| `enraged_multi_attack_count` | int | default 0 | Swap value after enrage. `0` means "no swap." `mythic_hydra` sets 4 but only has 3 attacks → falls through to "fire all" (audit P2 — misleading data). `hrungnirs_ghost` sets 0 explicitly (likely typo). |
| `multi_attack_always` | bool | default False | Always fires every attack per turn — the legacy Abaddon path. Equivalent to `multi_attack_count == len(attacks)`. |

### Summon / spawn flags

| field | type | notes |
|---|---|---|
| `summon_kind` | str or [str] | Monster id(s) to summon. Empty = no summoner. 12 monsters carry a value: `ancient_lich`, `skeleton_mage`, `skeleton_necromancer`, `skeleton_lich`, `banshee_lich`, `cult_hierophant`, `imp_lord`, `snake_charmer`, `whispering_crone`, `crypt_summoner`, `tiamat`, `asmodeus`. |
| `summon_cooldown` | int | default 5 | Turns between summons. |
| `summon_max` | int | default 4 | Hard cap on summoned minions this encounter. |
| `locust_interval` | int | default 0 | Abaddon-specific: turns between locust-swarm bursts. |
| `locust_count` | [min, max] | default [0, 0] | Range of locusts per burst. |
| `base_resistances` | [str] | | Abaddon's base resistance set (surfaced during the locust-ring quest mechanic). |

### Combat / attacks

How an attack is said (round 3): `monster.attack_line` gives "The Goblin hits you with his rusty knife for 3 damage!", with the creature's possessive; an attack whose name is a verb is said as one ("The Gelatinous Cube engulfs you for 4 damage!", `data/combat_lines.json` `attack_verbs`), and a proper word keeps its capital ("Euryale's wail", `proper_words`). First sight and Observe say the kind with its article ("You see a Skeleton", "an Orc Scout", but "Arachne": `monster.a_name`).

An `attacks[]` is a list of attack dicts. One is picked each turn (`random.choice`), with ranged-word heuristics overriding when `ai_pattern == 'ranged'` and the player is non-adjacent.

| attack field | type | notes |
|---|---|---|
| `name` | str | Display name. Underscore-to-space for message rendering. Ranged routing scans the lowercased name for words like `shoot`, `arrow`, `bolt`, `spit`, `hurl`, `volley`, `ray`, `blast`, `breath`, `spike`, `gaze`, `song`, `wail`, `charm`, `psionic`, `cast`, `bow`, `sling`, `javelin`, `spore`, `shock`, `hex` → treats the attack as ranged. |
| `damage` | str (dice) | Dice notation. |
| `delivery` | str | How the attack lands: blow, bite, sting, trample, grapple, touch, ranged, breath, gaze, voice (`tools/content/tag_attack_delivery.py`; `guards.delivery` reads one made at runtime). Picks the minor armour slot that guards it ([armour.md](armour.md) §3). |
| `type` | str | Damage type. Known values: `acid`, `blunt`, `cold`, `drain`, `fire`, `holy`, `lightning`, `magic`, `necrotic`, `physical`, `pierce`, `poison`, `psionic`, `shadow`, `slash`. **`psionic`** is NOT in `_damage_multiplier`'s set — treated as `1.0` unresistable (audit P5). |
| `ranged` | bool | Optional explicit ranged flag. |
| `piercing` | bool | Optional — allows the attack to shoot through intervening allied monsters (sets `_piercing_collateral` on this monster for the game loop to resolve). |
| `effect` | str | Status effect to apply on hit. One of 17 ids: `bleeding`, `blinded`, `burning`, `confused`, `cursed`, `diseased`, `feared`, `frozen`, `hallucinating`, `paralyzed`, `poisoned`, `silenced`, `sleeping`, `slowed`, `stunned`, `teleportitis`, `weakened`. All 17 verified in `status_effects.py`. |
| `effect_chance` | float | default 0.30 | Probability of attempting the effect. |
| `effect_duration` | str or int | default 5 | Dice or int, parsed by `dice.roll_duration`. |
| `effect_save_dc` | int | default `min(18, 12 + min_level // 7)` | DC vs the player's saving-throw stat. |
| `subtype` | str | Occasionally present — informational, not read by combat. |
| `bonus_vs` | {effect: float} | Damage multiplier when the hero is under that status (the mara's trample: `{"sleeping": 1.5}`). First matching effect wins; the hit message says so. Read in `Monster._resolve_blow`. |
| `steal` | str | `"gold"`, `"item"` or `"any"`: a landed blow may rob the hero (see `theft.py` below). |
| `steal_chance` | float | default 1.0 | Chance a landed `steal` blow actually steals. |

**Multi-attack vs multi-type.** A monster has ONE `attacks[]` list; `multi_attack_count` chooses how many to fire per turn in sequence, with their own THAC0 rolls and damage dice. `_fenrir_multi_attack(player, attack_limit=N)` is the central multi-attack path — it skips attack selection and fires the first N (or all when limit = 0).

### Resistance / weakness

- `resistances: [str]` — damage types that get `×0.5`.
- `weaknesses: [str]` — damage types that get `×2` (`×1.5` until the 2026-11-13 lore pass).
- `shrugs_off: [str]` — damage types that get `×0.25` (a swarm against a sword, a shade against any blow). No full immunity.
- `status_immune: [str]` — effects that never take hold (`Monster.add_effect` refuses them; the line says why).
- `status_weak: [str]` — effects that take hold without a big foe's resist roll and last `×1.5`; the token `fear_of_fire` makes a fire hit put it to flight (never written on a named foe, who is never routed).
- All five are written from lore by `tools/content/affinity_pass.py` out of `data/family_affinity.json`: edit the profile and rerun the pass, never the lists by hand (`tests/test_affinity_lore.py` checks they match). Numbers in `data/affinity_rules.json`.
- `base_resistances: [str]` — Abaddon-only, used while the locust-ring quest step is active.

`combat._damage_multiplier` (a typed hit) picks the BEST step across its damage types; `combat.weapon_type_multiplier` (a weapon blow) takes the best FORM step times the SUBSTANCE step (its material via `_MATERIAL_EFFECTIVE_AGAINST`, holy if blessed, a unique's own bane), capped at x3. The old hard-coded fallback (silver for every undead and demon, iron for every fey) is gone: silver's `effective_against` names the undead and shapeshifters, the devils carry `silver` and the fair folk `iron` in their weaknesses (`data/family_affinity.json`). Every monster attack is typed: the lore pass gave each plain `physical` one a form (slash, pierce, blunt) by its name and delivery, so armour that resists a form answers it.

**Known resistance types across all monsters** (15): `acid`, `blunt`, `cold`, `drain`, `fire`, `holy`, `lightning`, `magic`, `necrotic`, `pain`, `pierce`, `poison`, `shadow`, `slash`.

**Known weakness types** (14): `acid`, `blunt`, `cold`, `divine`, `drain`, `fire`, `holy`, `iron`, `lightning`, `magic`, `necrotic`, `pierce`, `shadow`, `slash` — plus `silver`/`iron` injected by the fallback for `undead`/`demon`/`fey` tags.

### Tags

A free-form list. Tags drive weapons and materials (silver vs undead, cold iron vs fey, the Dragonslayer Ring, `bonus_damage_vs_tag`, `effective_against`), `alert_all_tag` (wider-radius alert), `pack_dependent` (finding pack allies) and `resists_control` (mindless constructs and plants). Tags do NOT decide a monster's family: that is the separate `family` field below.

### Family

Every monster carries ONE `family` (one of the 22 in `data/monster_families.json`), chosen by what the creature IS in its lore and written by `tools/content/assign_monster_families.py` (`--write`, `--check`, `--sheet` for the 138 lore-settled borderline picks, `--rates` for what a run meets). `Monster.family` reads it; an old saved monster or corpse looks it up by kind. The Bones ghost is a Ghost; Death, the secret cow and the ethereal unicorn have none. Monster family knowledge is in [monster_families](monster_families.md).

**All tags in use across 527 monsters** (32): `aberration`, `bandit`, `beast`, `boss`, `caster`, `celestial`, `construct`, `cultist`, `demon`, `demon-touched`, `dragon`, `elemental`, `evil`, `female_attractive`, `fey`, `fiend`, `giant`, `gnoll`, `goblinoid`, `horror`, `humanoid`, `kobold`, `legendary`, `orc`, `outsider`, `plant`, `reptile`, `rogue`, `serpent-cult`, `shapeshifter`, `undead`.

### Loot — `treasure` dict

```json
"treasure": {
  "gold": [50, 150],
  "item_chance": 0.60,
  "item_tier": 3,
  "unique_drop_id": "echidna_fang",
  "boss_scroll_id": "scroll_of_the_hoard",
  "ammo_drop": { "ammo_id": "iron_arrow", "chance": 0.65, "count_range": [3, 8] }
}
```

| field | type | notes |
|---|---|---|
| `gold` | [min, max] | Rolled uniformly; `0, 0` yields no gold. |
| `item_chance` | float | 0..1 chance to drop a procedural common from `_spawn_treasure_item`: half the time gear, half a "magic" item whose class comes from `container_system.DROP_MAGIC_SHARE` (potion 33, accessory 22, scroll 20, wand 20, ammo 5; it went by how many kinds each class has, which made a third of these rings). |
| `item_tier` | int | 1-5. `_spawn_treasure_item` scales the "effective floor" as `max(1, tier * 5)` and rolls (30% weapon, 10% armor, 10% shield, 50% magic-pool from `accessory`/`wand`/`scroll`/`potion`/`ammo`) excluding uniques. **Cap:** 5. The pre-v2.18.0 catalog had 7 dragon-tier monsters with `item_tier` 6-10 (audit P4); those were clamped to 5 in the v2.18.0 pass. Current catalog is 1=61, 2=99, 3=151, 4=116, 5=100. |
| `unique_drop_id` | str | Mini-boss fixed drop — looked up by id in the unique-item pools. 20 monsters have one (Talos → `bronze_aegis`, Echidna → `echidna_fang`, Camazotz → `obsidian_talisman`, Cacus → `vulcans_brand`, The Sphinx → `sphinx_crown`, Baba Yaga → `iron_mortar_wand`, Set's Jackal → `anubis_scales`, Charybdis → `sailor's_amulet`, Ravana's Arm → `ring_of_iron_grip`, Wendigo → `wendigo_fang`, Wild Hunt Captain → `hunt_captains_sword`, each of the 7 seal demons → `seal_of_*`, …). |
| `boss_scroll_id` | str | Fafnir / Abaddon style — a one-shot scroll of the hoard / abyss. |
| `ammo_drop` | dict | Archer monsters carry quivers. 8 archers use this: `skeletal_archer`, `bone_archer`, `drow_warrior`, `orc_archer`, `goblin_sniper`, `gnoll_archer`, `bandit_archer`, `shadow_archer`. |
| `treasure_chance` | float | 0..1 chance to drop one piece of treasure (gem, jewellery, old coin, art; `src/treasure.py`), weighted to the floor like any loot. Written by `tools/balance/gold_by_lore.py` from `purse` (2026-10-18): dragons 0.03-0.09 by age, vampires and liches 0.025, thieves 0.02, leaders x2 (measured with gold_sim.py so treasure is about a tenth of a shallow floor's worth and three quarters of a deep one's). |
| `treasure_kinds` | [str] | Which kinds it may drop (`gem`, `jewellery`, `coins`, `art`); absent means any. Thieves: small and dear; the buried dead: grave goods. |

### Harvest

- `harvest_tier` (int, default 1) — 1-5. Threaded into the `Corpse` and read at harvest time (`food_system`). The ingredient dropped is looked up by `monster.kind` in `data/items/harvest_map.json` (close kin share one). See [food_system](food_system.md).
- `harvest_threshold` — **DEAD JSON field.** Still populated on all 527 monsters, still read into `Monster.__init__` and threaded onto `Corpse` for pickle compat, but no code consumes it. Harvest v4 (2026-08-06) is one-question, threshold=1 unconditionally. `bones.py:148` and 4 `game_encounters.py` sites set `99` as "unharvestable hint" — no effect.
- `ingredient_id` — **DEAD JSON field** on 525/527 monsters. Harvest v4 resolves the drop via `data/items/harvest_map.json`, not this field. The old-scheme id (`rat_meat`, `goblin_flesh`, `insect_carapace`, `spectral_essence`, …) is still written to disk. **Known downstream rot:** `game_render.py::_draw_bestiary_page` at `id_level >= 2` calls `load_ingredient_for(subject.ingredient_id)` and gets `None` — the bestiary "Ingredient:" / "Solo cook:" lines never render for these monsters (audit P3).

### Lore

- `lore` (str) — bestiary text and corpse-identify reveal.
- `bestiary_hint` — occasionally present on bosses, used by the bestiary UI as a tagline above lore.
- The audit queue notes: `Níðhöggr` lore in monsters.json has U+FFFD replacement chars where `ð` should be (visible in-game — sweep pending).

### `_meta` and post-v2.18.0 documentation fields

Several monsters carry a `_meta` sub-object or inline annotations added by the v2.18.0 audit wave:
- `_meta.spawn_method` — informational: `"planned_mini_boss"` / `"forced_seal"` / `"procedural"` / `"quest_only"` / `"boss_floor"`. Not read by game code.
- `_meta.plot_role` — informational tag used by the audit; not read.
- `quest_only` — proposed but not yet universal flag; `abyssal_locust` is called out as a candidate (L98 2d8-max-6 shape is indistinguishable from a data typo without this gate).

### Dead JSON fields documented but KEPT on disk (v2.18.0 decision — pickle-compat)

- `harvest_threshold` — all 527 monsters.
- `ingredient_id` — 525/527 monsters.
- `attack_effects` — `baba_yaga`, `ravanas_arm`, `anansi` (3 monsters). Zero readers.
- `mortal_weapon_floor` — `celestial_guardian` (1 monster). Zero readers.
- `chain_break_on_hit` — `abaddon_destroyer` (1 monster). Sets `player._chain_disrupt_pending = True`, but nothing reads that flag. Dead-wired.

The v2.18.0 commit kept these on disk because migrating would break every pickled save; `Monster.__init__` reads them, defaults them, and ignores them.

## Senses: how a monster notices the hero (Dungeon Alive, 2026-11-12)

Brandon: "NONE automatically know where you are unless it's thematically and lore appropriate." Until 3.4.0 every monster noticed the hero within 8 tiles THROUGH STONE, and then knew where he was for the rest of the floor. Now `Monster._spots_player` calls `senses.notice` (`src/senses.py`, data in `data/senses.json`).

**How a monster notices him:**
- **Sight:** a line of sight within `perception_range` (+4 for `keen_sight`). Walls, closed doors and tall fixtures (statues, stalagmites) block it; water and low furniture don't. An invisible hero is unseen except by `truesight` (celestials).
- **Sound:** the game emits noises through `Game._make_noise(kind)`:
  - footsteps each turn the hero moves (`step_radius`: 3 at DEX 10, quieter with DEX, +1 under a Heavy load and +2 when Burdened or Overloaded, +1 in medium body armour and +2 in heavy, +1 more in metal unless it is quiet (`gear.footstep_tiles`), silent with Cat's Footfall or silent walking);
  - `melee` 5, `shot` 4, `spell` 5, `door` 4, `coin` 3, `struck` 5 (a monster's blow on him);
  - an alarm rouses within 12; the squeaky board rouses within 20 (it called the whole floor until Brandon's play-test of 2026-11-12, when a floor-1 fight with every waking creature in 8 tiles coming to look was "a SHIT TON of monsters all descended on me at once").

  `senses.resolve_noises` runs at the top of `_do_monster_turns`. Sound travels along open ground round corners (BFS `sound_map`), a closed door costs 3, and stone stops it. A sound gives the monster a PLACE (`_goal`), not the hero. A monster already tracking him hears footsteps 3 tiles further, so a chase goes round corners.
- **Lore senses** (`families` and `monsters` in the JSON; a kind's list replaces its family's, but `blind` always holds):

  | Sense | Who has it | How it works |
  |---|---|---|
  | `scent` 8 | dragons 10, Fenrir 12, wolves and hounds, bears, trolls and giants ("Fee-fi-fo-fum"), werebeasts, ghouls, vampires, rats, the galla 12 | goes through walls; invisibility doesn't hide you |
  | `tremor` 5 | snakes, spiders, scorpions, oozes 2, plants 1, earth elementals, the gorgon sisters 10 | through walls; fails while the hero stands still or levitates |
  | `lifesense` 6 | ghosts, wights, draugr, death knights, deadites, jiangshi | the dead feel the living through walls |
  | `echo` 7 | bats, hook horrors, Camazotz | needs a clear path; sees an invisible hero |
  | `mindsense` 8 | mind flayers, intellect devourers | |
  | `guilt` 14 | the Erinyes | only when karma < 0 |
  | `master` | Asterion, Abaddon, Death | always knows, in his own house |

  The first time on a floor that a kind finds him by a lore sense within 12 tiles, `senses._first_line` marks it (`_sense_how`), and `Game._say_sense_lines` says one of its three `lines` (2026-11-12):
  - **known:** he sees it and knows the kind (`family_lore.knowledge` KNOWN). The sense is explained: "It has your scent, and walls will not hide you from it."
  - **seen:** he sees it but doesn't know it. Only what it does: "lifts its head, sniffs the air, and turns toward you".
  - **unseen:** he can't see it. Never named: "Somewhere close, something sniffs the air, and stops."

**What a monster does with what it knows:**
- **Hunting** (`_tracking`): it senses him this turn. `_standard_move` charges straight in when it has a clear view, and otherwise takes a real BFS path round the walls (`senses.step_toward`), also when a pillar or another creature blocks the straight way.
- **Searching** (`_goal`): it lost him, or heard something, or was roused (`senses.rouse`: an ally's cry, `alert_monsters_near`, the squeaky board). It goes to the place, looks about for 6-12 turns (14-22 if roused), then gives up and says `lost_line` if the hero can see it.
- **Its own business** (`_job`), set by `senses.assign_jobs` in `LevelManager.generate` (both branches):
  - `wander` (roams room to room, lingering), `guard` (keeps its post), or `sleep` (300-700 turns; a "z" is drawn over it);
  - weights by family in `jobs`;
  - a room's creatures share one job, so a pack sleeps together;
  - **a monster den sleeps** (G3);
  - named foes, bosses, ambushers, mimics and rooted things guard.

  A creature woken by a noise keeps watch afterwards.
- **Waking:**
  - footsteps within 2 tiles wake a sleeper 25% of the time (6% further away), with the deep sleepers' DEX, burden and Cat's Footfall odds;
  - a fight within half its reach wakes one 40% of the time (15% further off). A sleeper gets ONE chance to wake a turn, at the most waking noise it heard: a fight is two noises a round, and a roll for each made the sleepers near it all but sure to wake;
  - the Hand of Glory keeps everyone asleep;
  - zoo, graveyard and barracks deep sleepers keep `sleepers.py`'s odds, and only a fight within 3 tiles may break their sleep (20%).

**`_aware` keeps its old meaning:** the monster has noticed the hero once. That's what ambushers, mimics, naming, the Fenrir rage and the Abaddon swarms read. A monster made aware by the game itself (a summons, an announced foe, an old save's hunter) gets one lead to where the hero is now. A wanderer arrives knowing nothing. It goes to see a loud noise from the last 40 turns only if that sound reaches the tile it came in on, along open ground (`senses.sound_map`, the noise's own reach: a fight 5 tiles, an alarm 12). Otherwise it roams. (Before 3.5.1 every newcomer was sent to the last fight from anywhere on the floor.) The wanderer cap counts `_tracking` hunters. When newcomers come at all is the floor's clock (Wanderers, below).

**Other changes in the same slice:**
- G6: `hit_and_run`, `dancer`, `fenrir_rage` and `abaddon` call `_spots_player` (they used to hunt from anywhere).
- The `dragon` pattern uses scent in place of the old 10-tile check.
- Ambushers spring only on what they can see or touch.
- G8: an alerted or aggravated `sessile` monster stays rooted.
- G5: an archer that's adjacent steps back half the time to a tile 2 away that still has the shot (`_step_back`).
- Dagger backstab now counts any target that isn't tracking the hero.
- Observe (`;`) adds the state line (`status_lines`). How a creature hunts (`senses_line`) is shown once its kind is known.

**Scavengers (C3).** `data/senses.json` lists them under `scavengers`: ghouls, ghasts, the otyugh, charnel hounds and their kin, and any vermin or ooze. When one is idle (not hunting, not searching, awake) and smells a corpse within 8 tiles, `CombatMixin._scavenge_prep` gives it that place (`_scavenge`), and it walks there whatever its post. It eats for 3 turns, so a harvest is a race; it heals a quarter of its health and the corpse is gone. The hero sees "X is feeding on the corpse.", and Observe says "It is busy with a corpse."

**G7.** Phase-blink now fires for the patterns that never reached it. An archer or a summoner blinks out to a clear shot 4 tiles away; Lyssa (hit-and-run) blinks in beside the hero. Asterion lowers his horns for a charge in his hunting state, not only once enraged. **QA:** Shift+A on the Titivillus build lists the floor's Dungeon Alive content and shows the map; pressed again, it sets down a war-band.

Tests: `tests/test_senses.py`.

## War-bands (Dungeon Alive slice 5, 2026-11-12)

Brandon: monsters must "pose a real challenge and players need to pay attention to lore, weaknesses, abilities". A war-band (`data/war_bands.json`, `src/war_bands.py`) makes camp in one big room on 55% of the floors in its range, from floor 1, never more than one band a floor. Floors 1-6 also hold the two small bands, a goblin scouting party (a hobgoblin and his goblins) and a gang of footpads (3.5.1: a floor's own encounters carry the fight; see Wanderers). It replaces that room's ordinary roll. `LevelManager.generate` calls `war_bands.place_band` after the hidden chambers.

**Bands:**

| Band | Floors | When the leader falls |
|---|---|---|
| goblin war-band | 3-55 | rout |
| gnoll pack | 6-40 | rout |
| bandit crew | 3-45 | rout |
| cult circle | 8-70 | rout |
| necromancer and his dead | 9-80 | crumble |
| giant and his hounds | 8-80 | rout |
| Fair Folk hunt | 4-60 | rout |
| warband of devils | 36-98 | quarrel |

**Roster:** a leader plus `guard`, `shooter`, `caster` and `healer` kinds. Only kinds in the floor's own `_floor_pool` are used, so a band is never out of its depth. Each member carries `_band` (uid), `_band_id`, `_band_role`, `_band_leader` and `_job_fixed`, so `senses.assign_jobs` leaves its watch alone. Either a sentry and the leader keep watch while the rest sleep, or all stand guard.

**In play:**
- **Roused together.** When one of a band notices the hero, `senses.notice` calls `war_bands.alarm`, which rouses the rest to the place.
- **Healers.** A healer mends any bandmate (`_healer_turn`), whatever its kind.
- **Nerve.** A follower whose leader lives never flees when hurt.
- **The leader falls** (`CombatMixin._band_member_died`, called from `_on_monster_killed`):
  - `rout`: every follower is `feared` for 12 turns;
  - `crumble`: the restless dead he raised fall where they stand, and the rest are feared;
  - `quarrel`: followers turn `quarrelsome` and `confused` for 8 turns, so they fight each other.
- **Half the band down:** each follower flees with a 50% chance.
- **A great blow.** A maths chain of `nerve_chain` (6) or more on the living leader makes about half his followers falter (`feared` for 4 turns), with the band's `break_line`.

**Knowing pays.** On arrival, `_announce_band` says the band's `line`, which is sound and signs only and never names the band's kind. If the hero knows the leader's kind (`family_lore.knowledge` KNOWN: studied, its page opened, or its family at Lore), it says the `known_line` instead, which names the roster and how to break it. Recognise alone is not enough (2026-11-12). The camp is furnished by `decor.furnish_band_camp`: the fire and banner near the middle, bedrolls round the fire, bones and candles in one group against a wall.

Observe (`war_bands.observe_line`, data `observe`) says what anyone can see:
- **a follower:** "It marches with a goblin war-band."
- **the leader:** "The rest of the band keep glancing at it, as if waiting for orders."
- **the leader, to a hero who knows its kind:** "It leads the band." plus what happens when it falls, by the band's morale ("If it falls, the dead it raised will fall with it.").

## Tells: a dangerous creature shows what it can do (slice 5)

The tells live in `data/tells.json` and `src/tells.py`. Each tell has three parts:
- **sign:** what the eye sees;
- **does:** what the creature can do to the hero;
- **counter:** what to do about it.

How much is said follows `family_lore.knowledge` (Brandon, 2026-11-12: the notes must not give away what a creature is or how to beat it before the hero knows it, and two corpses must not teach a whole family):

| Level | When | Said |
|---|---|---|
| UNKNOWN | nothing known | the sign only |
| KIN | its family at Recognise or Forewarned, the kind never studied | the sign, "It is one of {kin}.", and what it does, never the counter |
| KNOWN | the kind studied, its page opened (Thoth, Omnisight, Recall Lore at chain 5, the Wand of Probing, a gate boss's quest step), or its family at Lore (`full_lore_tier`, 3) | the sign, what it does and the counter, then what it is made of (`tells.lore_lines`): its weaknesses ("Fire and acid hurt it most."), what it resists and shrugs off ("A crushing blow does little to it; a cutting blow and a thrust hardly touch it."), and its nature ("It cannot be put to sleep, poisoned or charmed. Fire puts it to flight."). A kind with no tell and no sign is named first ("You know what the skeleton is made of.", `tells.known_lead`), so "it" has a creature to stand for |

- **First sight:** the first time in a run the hero sees a kind, `_maybe_tell` says its worst tell at what he knows, and at KNOWN what it is made of, tell or no tell (winning-build plan 3.1). It is said again the first time he sees the kind after he knows it better. This is tracked in `_dungeon_alive['told_level']` ({kind: level}, saved); an old save's `told` list counts as told at UNKNOWN.
- **Observe:** says up to 2 tells at the same level, and at KNOWN what it is made of (`tells.lore_lines`). A KIN creature adds "You know its kind, but not how to beat it. Study its corpse."; how it hunts (`senses_line`) is said only at KNOWN.
- **The Bestiary:** a KIN kind's page opens, but its weaknesses, resistances, what it shrugs off and its nature read "not yet studied" until it is KNOWN; at KNOWN the page shows "Weak to", "Resists", "Shrugs Off", "Immune To" and "Falls Easily To".
- **The hit lines, the Strike Now preview and the combat strip's weakness tag** follow the same levels: see [combat](combat.md), "Knowledge decides what the line says".
- **Honest about reach:** `tells.reach` is 'far' when the creature can put the effect on the hero from across a room. That covers a gaze, or an attack a ranged, dragon, healer, summoner or rooted creature uses at range (the same test as `Monster.attack`). A far effect gets `counter_far`, or the shared `far_counter` ("keep stone between you"), and never "fight it from a distance".
- **Splitting:** the line names the blows that split the creature, from its own `splits.by`.
- **What counts as a tell:** attack effects with `effect_chance` of at least 0.1, plus these flags: gaze, splits, revives, drain-heals, regeneration, summons, pull, SP drain, charge, phase-blink. They are ranked by `order`, worst first.

Tests: `tests/test_monster_notes.py`, and the Observe cases in `tests/test_observe_bestiary.py`.

**Patrols (C5).** A wandering monster now arrives beside a stair the hero can't see, as if coming down or up it, instead of out of nowhere. It goes to a fight or alarm it can hear from there, or roams.

## Wanderers: the floor's clock (3.5.1)

Brandon, play-testing floor 1: "I just don't think we need a constant stream of monsters... I'd rather have a larger population at first, with complex encounters set up, then a trickle if you hang around TOO LONG, but give the player some time to explore... walking back and forth becomes a massive chore."

Until 3.5.1 a newcomer came every 22 turns from the hero's first turn on a floor, whenever it held fewer than about what it started with (`wander_alive_cap`). Every kill was replaced within 22 turns, and newcomers were half of all floor-1 fights (51%, measured on 24 maps, crossing and back).

`src/wanderers.py` keeps a clock on each floor (`dungeon._wander_clock`) of the turns the hero has spent there. `main._maybe_wander_spawn` ticks it once a world turn; `main._place_wanderer` brings a newcomer in when it is due, if the caps allow.

- **Time to explore.** Nothing new comes for the floor's grace, `floor_curve.wander_grace(tour)` = `WANDER_GRACE_FLAT` (100) + `WANDER_GRACE_PER_TILE` (2) × the floor's explore tour. The tour (`wanderers.explore_tour`, kept on the floor) is the walk of a full explore: from the up stair, the nearest room not yet seen each time, every room, then the down stair. Its median is 224 tiles on floor 1, 330 on floor 5 and about 500 from floor 12, so the grace is about 550 turns on floor 1 and 1,100 deep. A thorough explore walks about 1.5 tours; the rest is time to fight and catch your breath.
- **The floor stirs.** At `WANDER_WARN_SHARE` (85%) of the grace, one `warning` line says he has been here a long while. When the grace runs out, a `stirs` line says things are coming (`data/senses.json` `wanderers`).
- **A trickle.** The first newcomer comes as the grace runs out. The gap to the next starts at `WANDER_TRICKLE_START` (60 turns) and shortens to `wander_interval(level)` (22 turns to floor 50, 40 at floor 100) over `WANDER_TRICKLE_RAMP` (600) turns (`floor_curve.wander_gap`). So a hero camped on a floor long after he has seen it all meets the old pressure again. Resting is never safe forever.
- **Coming back.** Time spent off a floor settles it by as much, down to one full tour of quiet (at least 100 turns) before the trickle starts over, and the lines may be said again. A gap of 3 turns or less is haste or a stair hop and settles nothing.
- **The floor's own.** The fighting is done by what a floor is made with. The per-room roll's base is 0.62 (was 0.50), `MIN_FLOOR_MONSTERS` is 8 (was 6), and war-bands camp on 55% of floors from floor 1. Floor 1 starts with about 13 monsters (was 10), and 70% of floor-1 maps hold a set piece, a band or a den (was 18%).

The simulator ticks the same clock (`Run.pass_time`, `snap.tour`).

Tests: `tests/test_floor_clock.py`, `tests/test_wanderers_hear_or_roam.py`.

Tests: `tests/test_war_bands.py`.

## AI dispatch (15 patterns)

`take_turn` dispatches on `self.ai_pattern` after the common pre-flight (immobilised, slowed, enrage swap, pack-dependent re-evaluation, flee-when-hurt flag). Dispatch is `if/elif` on string match — the matching chain is in `monster.py` lines ~826-867. **Count by pattern** across 527 monsters (counted 2026-05; there are 574 now):

| pattern | count | dispatch | one-line behaviour |
|---|---|---|---|
| `aggressive` | 332 | fall-through to `_standard_move` after awareness/flee/charge gates | Approach player greedily, attack when adjacent. The default. |
| `ranged` | 101 | `_spots_player` then `_ranged_turn` | Shoot from LOS at distance 2-6, retreat if too close, approach if too far. Will take a melee swing if cornered. Piercing-ranged monsters fire through intervening allies when blocked. |
| `sessile` | 29 | strikes what is adjacent (or in range, if it has a ranged attack) | Rooted: never walks, even alerted or aggravated (G8, 2026-11-12). Fungal / coral / mimic-adjacent. |
| `ambush` | 23 | lurks; springs within 5 tiles on a hero it can see or touch | Invisible until sprung, then `aggressive`. |
| `hit_and_run` | 17 | `_hit_and_run_turn` (`hunting` → `retreating` → `hiding`) | Asterion-style. Attacks 1-2 times, retreats through phasing walls for 3 turns, then hides 4-6 turns before hunting again. |
| `summoner` | 8 | `_summoner_turn` | Once it has spotted the hero (`_spots_player`, the same detection check as every hunter), spawns a minion every `summon_cooldown` turns up to `summon_max`, otherwise behaves ranged. Sets `_wants_summon` for `main.py::_spawn_summoner_minion` to resolve. |
| `healer` | 6 | `_healer_turn` | Heals the most-damaged adjacent same-kind/tag ally by `heal_amount_pct × max_hp` (needs no sight of the hero). Falls back to ranged / aggressive when nothing to heal, once it has spotted the hero (`_spots_player`). 6 monsters: `orc_priest`, `goblin_warpriest`, `cult_priest`, `viper_priestess`, `plague_witch`, `deep_one_priest`. |
| `cowardly` | 3 | `_standard_move` with inverted direction | Runs from the player; also the fallback for `pack_dependent` when alone. |
| `dancer` | 2 | `_dancer_turn` | Medusa & Lamia. Approach normally when far; when adjacent, pick a *different* adjacent-to-player tile each turn before striking. Hard to pin without chokepoints. |
| `mimic` | 2 | `_mimic_turn` | Inert until the player steps adjacent; then `_mimic_surprise = True`, pattern flips to `aggressive`, first attack lands at `×1.75` damage. |
| `fenrir_rage` | 1 | `_fenrir_rage_turn` | Fenrir only. Every `rage_interval` turns, gains a rage stack. 5 escalating log messages. At 3+ stacks: speed → 14 (double-move), `attack()` fires every attack per turn (bypasses random choice). `reset_rage()` is called by the Gleipnir binding. |
| `abaddon` | 1 | `_abaddon_turn` | Abaddon only. Aggressive movement + `_wants_locust_spawn` flag every `locust_interval` turns. Game loop reads the flag and spawns `locust_count` `abyssal_locust`s. |
| `seek_locust` | 1 | `_seek_locust_turn` | `heavenly_angel` only. Walks toward the nearest `abyssal_locust`; adjacent → sets `_annihilate_target` for the game loop. Never targets the player. |
| `grid_bug` | 1 | overrides `_move_candidates` to cardinals only | Can only step N/S/E/W, no diagonals. NetHack-grid-bug fossil. |

**Total:** 15 dispatch branches, all verified against the audit — "all 15 `ai_pattern` values map to real dispatch branches."

### Attack-time flow (abridged)

1. `return_to_hand_ward` consumed → auto-miss.
2. `gaze_paralyze` cooldown fires its own branch (blind player / Aegis reflect / save-vs-DC) with full mitigation sweep for the fall-through swing.
3. **Fenrir rage ≥ 3** → `_fenrir_multi_attack(player)` (all attacks).
4. `multi_attack_count` → first N attacks via `_fenrir_multi_attack(player, attack_limit=N)`. `enraged_multi_attack_count` swaps N on enrage. `multi_attack_always` or `multi_attack_count ≥ len(attacks)` fires all.
5. Ranged routing picks a ranged-worded attack when `ai_pattern=='ranged'` and non-adjacent.
6. THAC0 roll: `d20 >= thac0 - player_ac` hits (touch attacks against touch AC), `nat 1` always misses, `nat 20` always hits; a named foe lands 15% of its numerical misses (`MIN_HIT_NAMED`), an ordinary one none. Then the minor slots' guards (`guards.guard_keep`): a share of the damage turned aside, a share of the rider shrugged off.
7. Mitigations: confused 30% miss, blinded 40% miss, displacement 30% miss, Monkey King dodge, Hermes votive sandals, Aegis Gorgoneion petrify-on-hit, Nemean Lion unskinnable floor-at-1, Mirror of Souls, Resonant Frequency shock, Spartan Stand counter.
8. Damage: rage stacks → `+rage_damage_bonus` roll each; charge bonus (`charge_bonus_mult × dmg`); mimic surprise `×1.75`; weakened `//2`; sundered `×0.70`; summoned `//2` under Ring of Solomon; back-attack multiplier when player faces away.
9. Shield reflect (fire/cold), spell-reflect chain-passive, Mirror of Souls, Gorgoneion petrify — all post-damage.
10. Drain: CON -1 if not `drain_resist`; `drain_heals_self` returns a fraction as HP.
11. Chain-disrupt: sets `_chain_disrupt_pending` (currently dead-wired per audit — no reader).
12. Pull-on-hit: sets `_pending_pull_toward` for the game loop.
13. Status-effect application: `effect_chance` roll → `apply_debuff_with_save` with `effect_save_dc`, reflecting bounces 50% back to attacker.

## Boss levels (`src/boss_levels.py`)

Static hand-crafted maps, 80 × 50 tiles, one per boss floor. All share a layout convention: `rooms[0]` has `STAIRS_UP`, final room has `STAIRS_DOWN` (except L100 — Philosopher's Stone replaces the stair), boss spawns in the main chamber (second-to-last room).

| level | id | boss | shape | notable terrain |
|---|---|---|---|---|
| 20 | `asterion_minotaur` | Minotaur | Labyrinth: 3 parallel E-W corridors with vertical connectors, walled dead-ends, central boss chamber, treasure alcoves | `dungeon.phasing_walls` set that only Asterion can walk through (hit-and-run AI). Treasure alcoves off the boss chamber. |
| 40 | `medusa_gorgon` | Medusa | Hellenic temple: entrance portico, long central nave with altar and pillars, two pairs of side chapels, inner sanctum | **4 pillars inside the boss room** — LOS blockers against gaze. Side-chapel doors. |
| 60 | `fafnir_dragon` | Fafnir | Cavern: twisting antechamber chain → wide hoard chamber (stalagmite WALL tiles for cover) → deepest dragon's lair | Fafnir is `[2, 2]` footprint — `_spawn_boss` NW-shifts the anchor if the room center can't fit the whole quad. Rock formations in the lair for cover. |
| 80 | `fenrir_wolf` | Fenrir | Frozen Asgardian hall: grand hall + altar of Odin, barracks side rooms, secondary hall, throne room | **4 ICE tile patches** in the throne room for slip tactics. Frozen pillars for cover. |
| 100 | `abaddon_destroyer` | Abaddon | Abyssal ring: entry ledge, outer ring of 6 chambers, cross-connecting corridors, spoke corridors into the Void Throne, altar ring (6 ALTAR tiles) | **No STAIRS_DOWN** — Philosopher's Stone is spawned by `LevelManager._place_stone` instead. 4 doors into the boss arena. Crumbled void-throne WALL tiles for minimal cover. |
| 999 | `cow_king` + 40-50 `hell_bovine` | Cow King | Moo Moo Farm: large open pasture, fenced perimeter (scattered WALL pillars for cover), Cow King's pen in the corner | Portal back home via `STAIRS_DOWN` in the entry area. 40-50 hell bovines seeded across the pasture. **Secret** — not reachable from `BOSS_LEVELS`. |

`boss_levels.generate_boss_level(level_num)` is the entrypoint. `_make(tiles, rooms, level)` → `Dungeon`. `_spawn_boss(dungeon, boss_id, boss_room)` loads the JSON def, instantiates `Monster(defn, cx, cy)`, forces `boss.is_boss = True` (the override that compensated for the pre-v2.18.0 silent `is_boss` drop), and NW-shifts the anchor for `footprint != (1, 1)`.

**Known duplicate** (audit P5): `_make` is defined twice in `boss_levels.py` (lines 533 and 646, identical). Harmless.

## Spawn pool construction (`dungeon._build_spawn_pool`)

```
for id, defn in monsters.json:
    if defn.peak_weight <= 0: skip             # story-locked (bosses, orphans)
    if defn.min_level > level: skip            # lore floor
    bell = exp(-distance² / (2 × spread²))     # distance = level - peak_floor
    if bell < 0.005: skip                      # vanishingly rare — drop entirely
    weight = max(0.02, peak_weight × bell)
    pool[id] = {...defn, _spawn_freq: weight}
```

Both procedural placement callers go through `_spawn_one_in_room(room, eligible, dungeon, monsters, rng)` which:
1. Shuffles the room's inner tiles.
2. For each tile: validates footprint fits (`_footprint_fits`), picks a monster via `_weighted_choice(eligible, rng)`, places.
3. If the placed monster has `pack: true`, places `base_min..base_max` extras in the same room (scaled by depth and `frequency`).

**Two top-level population paths:**
- `spawn_monsters(rooms, level, dungeon, min_count, max_count)` — fixed total count, each in a random room; skips room 0. Used for targeted clusters (zoo, graveyard, barracks, den extras, hidden-chamber lairs, wandering spawns). Intentionally LUMPS.
- `populate_floor(rooms, level, dungeon, occupancy)` — rolls EVERY room independently with per-room probability `occupancy` (0.62 shallow → 0.95 deep). This is the baseline for a floor; packs/dens/zoos cluster intentionally on top. Guarantees at least one monster on any non-empty floor.

The baseline occupancy comes from `LevelManager.generate` as `density = min(FLOOR_DENSITY_BASE + level_num / 130, 0.95)`, with `dungeon.FLOOR_DENSITY_BASE` = 0.62 (0.50 before 3.5.1).

**Known convention trap** (audit P5 / level_manager docstring): `spawn_monsters` skips `rooms[0]`. Both `_spawn_monster_den_extras` and `_populate_hidden_chambers` exploit this by passing `[dummy, target_room]` so the target becomes "room 1" and gets populated. If `spawn_monsters` ever drops the skip-first convention, BOTH call sites must change together.

## Mini-boss planning (`LevelManager._roll_planned_mini_bosses`)

Bands = `(1,20), (21,40), (41,60), (61,80), (81,100)`.

Per band:
1. Collect candidates: `is_mini_boss` **AND** not `seal_demon_*` **AND** `spawn_chance > 0` **AND** `band_lo ≤ peak_floor ≤ band_hi`.
2. Primary slot (p=0.90): weighted pick by `spawn_chance`. Target floor = `peak_floor`, or `peak_floor - 1` if that collides with a `_BOSS_LEVELS` entry (20/40/60/80/100). Record in `planned[target]`.
3. Secondary slot (p=0.30): same pool minus the already-placed id. Walk the target forward if it collides with another planned slot or a boss floor; abort if it walks past `band_hi`.

**At floor-generate time** (`_try_spawn_mini_boss`): if `self._planned_mini_bosses[level_num]` is set and that id hasn't been placed yet, pick a middle room (not first or last), find a free walkable tile, instantiate — v2.18.0 added the implicit `is_boss` wire via `Monster.__init__`, so a mini-boss now gets boss-immunity automatically without an explicit `mb.is_boss = True` override at this call site.

## Seal demons

| level | id | drop |
|---|---|---|
| 83 | `seal_demon_wrath` | `seal_of_wrath` |
| 85 | `seal_demon_pestilence` | `seal_of_pestilence` |
| 87 | `seal_demon_famine` | `seal_of_famine` |
| 89 | `seal_demon_war` | `seal_of_war` |
| 91 | `seal_demon_death` | `seal_of_death` |
| 93 | `seal_demon_earthquake` | `seal_of_earthquake` |
| 97 | `seal_demon_silence` | `seal_of_silence` |

Note: there is NO seal-demon on floor 95. The levels are prime-ish by narrative convention.

`_try_spawn_seal_demon` runs AFTER `_try_spawn_mini_boss` on every procedural floor. Idempotent via `self._placed_mini_bosses`. Each kill calls `game_combat._handle_death` → adds the matching seal id to `game.seals_broken`, writes a Journal line, at 7/7 triggers the "ALL SEVEN SEALS ARE BROKEN" narrative pulse.

## Mini-boss tuning (2026-11-14)

Brandon: "are our mini-bosses still working and tuned?" They were placed (every planned one, 331 of 331) but not tuned: after the weapon curve (2026-11-12) the mastery hero killed every band mini-boss, legendary wanderer and seal demon in 1 to 5 of his attacks for a median 0-15% of his health. "Yes, tune them."

**Who.** `tools/balance/mini_boss_bands.py` owns 38 foes (`roster()`): the 26 band mini-bosses `_roll_planned_mini_bosses` rolls (`is_mini_boss`, `spawn_chance > 0`; Iron Patriarch, Whispering Crone and Blood Archon among them), the 5 legendary wanderers (`legendary` tag) and the 7 seal demons. The gate bosses, the Cow King, Old Nickel and Euryale (Stheno's escort, `spawn_chance` 0) are not in it.

**How a foe is written (LORE, NOT FLOOR).** Real numbers in `data/monsters.json`, written by `mini_boss_bands.py --write` from its `FOES` table:
- `hp`: its health in ordinary monsters of its peak floor (`floor_curve.target_hp`).
- `blows`: what it lands in one turn if every blow hits (the attacks `Monster.attack` fires: the first N of a `multi_attack_count` under the attack count, all of a flurry, else one at random), as a share of a steady cook's health bar there (`floor_curve.health_bar`). At most `BLOWS_CAP` 30% of a bar, and the enraged flurry (`enraged_multi_attack_count`) at most `RAGE_CAP` 45%: no turn is a one-blow death.
- To-hit: `named_thac0` = the armour line (`rebake_thac0.measure_line`, the mean AC a plain hero wears on that floor) + `NAMED_NEED` 6 + the foe's own `aim` (0 for all today). An ordinary monster needs a 10 against that hero; a named foe needs a 6. A big blow that rarely lands is luck; a surer, smaller one is a fight the kid can read, and his armour still takes a point off the roll for every point he wears. `rebake_thac0.py` calls `named_thac0` for these foes, and `respawn_by_hp.apply_stat_fixes` and `tools/content/late_game_monsters_2026_10.py` leave their health and dice to the band tool.
- `HP_CAP`: no foe is tankier than 90% of Abaddon (`test_no_mini_boss_is_tankier_than_abaddon`). The legendary wanderers, Níðhöggr's Fragment and Abyzou reach it first: they are dangerous rather than long.

**The bands** (`BANDS`, checked by `tests/test_mini_boss_bands.py`): band mini-boss hp 7-24 ordinary monsters, blows 5-30% of a bar; legendary 17-24, 18-30%; seal demon 11-19, 14-30%. Where in the band a foe sits was measured foe by foe so the mastery hero needs about six attacks for each (the family is the length of the fight): a foe whose hide, resistances, regeneration or second life turns his usual blows needs less health to last as long (the Green Knight 7.4, Stheno 7.5, Baba Yaga 8.6, Talos 10.6), one he cuts through needs more (Echidna 22.7, the Erlking 20.9). A foe whose technique bites carries fewer dice (the Bonnacon's burning dung, the Wild Hunt Captain's pace, Ravana's paralysing grab). Each `FOES` entry has a line of lore saying why.

**Techniques added** (each also a tell, `data/tells.json` by its effect): Talos's **Red-Hot Hug** (grapple, burning: he heated himself in the fire and hugged his victims) beside his Crush, two blows a turn; Cacus's Fire Breath now burns and his **Breath of Smoke** blinds (Virgil's smoke and darkness; it replaced his Slam); the Sphinx's **Whispered Riddle** (voice, confusion: the clock on every sum runs short; wax in the ears stops it) beside her Rake and Bite, three blows a turn; the Nemean Lion's Claw bleeds (its own claws were the only thing that could cut its hide); the Calydonian Boar charges (`can_charge`, x1.5). The Bonnacon's dung burns a little less often (25%, was 35%): at floor 6 the burn was the whole fight. `combat_lines.json` gives the two new verbs ("Talos hugs you to a red-hot chest", "The Sphinx puts a riddle to you"); a riddle that misses "fails to take hold of you" (`monster._MIND_WORDS`).

**How it was measured.** `tools/balance/mini_boss_fights.py heroes` runs the kid-model simulator (100 runs a profile, mastery, committed, mastery_dex, mastery_mage) and saves each living hero at the start of each foe's floor; `fight` then fights every foe against those heroes from the current data, the way `difficulty_sim.Run._boss_side_fights` does (full health, debuffs cleared, the foe alone, no quest layer), so a retune is measured in a few minutes. Final numbers, 400 fights a foe a profile (median attacks / median share of health lost / deaths):

| Group | Mastery before | Mastery after | Committed before | Committed after | DEX / mage after |
|---|---|---|---|---|---|
| Band (26) | 2 / 4% / 0% | 6 / 25% / 0.2% | 4 / 12% / 0.2% | 12 / 124% / 5% | 7-8 / 30-34% / 0.1-0.4% |
| Legendary (5) | 2 / 0% / 0% | 7 / 14% / 0% | 3 / 6% / 0% | 13 / 178% / 7% | 9 / 21-26% / 0-0.2% |
| Seal demon (7) | 2 / 2% / 0% | 5 / 14% / 0% | 4 / 12% / 0% | 11 / 140% / 2% | 7-8 / 18-21% / 0-0.1% |

Whole runs (100 a profile, kid model, the same seeds before and after): mastery won 91% before and 92% after, mastery_dex 86% and 89%, mastery_mage 89% and 92% (each about 6 points either way), with no mastery death on floors 61-99 in either; committed fell from 9% to 2%, its deaths spread over the named fights it now has to survive (seven seal demons in a row among them).

"Lost" counts what potions and prayers put back during the fight, so a committed kid's 124% is more than a whole bar spent. The deep foes whose blows are fire, cold, poison or drain (Mammon, Samael, Abyzou, Tiamat, Asmodeus, the Wendigo) cost a prepared mastery hero little (7-14%): his resistances halve them and his toughness takes more. That is preparation paying, and an unprepared kid meets the full blow.

**What the simulator does not model** about these foes: summons (the Crone's dead, Tiamat's young dragons, Asmodeus's bone devils), a charge for anything but Asterion (the Boar, the Blood Archon), Charybdis's pull, Asmodeus's blink, Mammon's hunger (`sp_drain`), Euryale beside Stheno (the side fight is Stheno alone), and the hero's own confusion and blindness beyond the shorter clock (no stumbling, nothing hidden). Heroes wielding the Green Chapel Axe were left out: its returning blow (half of a max-chain blow back on the wielder, uncapped) kills a deep hero outright whatever he fights.

**Old saves.** A mini-boss already set down on a saved floor keeps the numbers it was made with (a `Monster` is pickled whole); every one not yet met uses the new data.

## Multi-tile monster placement

Five monsters declare `footprint: [2, 2]`:

| id | min / peak | spawn path | fits-fallback |
|---|---|---|---|
| `fafnir_dragon` | L58-60 | hand-placed (`_spawn_boss` in `_level_60_lair`) | NW-shift up to 3 tiles |
| `tiamat` | ~L85-95 | procedural (`_spawn_one_in_room` with `_footprint_fits`) | tile skipped if footprint overlaps wall/monster |
| `surtur` | L87-90 | procedural | same |
| `ymir_last_spawn` | L82-85 | procedural | same |
| `hrungnirs_ghost` | L80-82 | procedural | same |

Both placement paths validate ALL 4 footprint tiles before committing — `_footprint_fits` checks walkability + occupancy, `_can_move_to` checks walls + phase-wall exceptions per step. `geom.monster_at_tile(x, y, monsters)` returns the monster whose anchor-plus-footprint covers `(x, y)` — this is the correct way to query "is a monster here?" and must be used anywhere the code touches collision/adjacency involving multi-tile bosses.

## Treasure drop (`game_combat._drop_treasure`)

Sequence on `Monster` death:
1. `_make_corpse(monster)` — builds a `Corpse` with `harvest_tier`, `harvest_threshold`, `ingredient_id`, `lore`, and a `monster_def` dict carrying `hp`/`thac0`/`attacks`/`resistances`/`weaknesses`/`speed`/`tags`/`peak_floor`. Copies `monster.family` onto the corpse. Auto-identifies if `monster.kind` is in `player.studied_monster_ids` (studied by the hero himself; a kind the Book of Thoth only opened still asks, so its study counts for its family).
2. `_drop_treasure(monster)`:
   - Roll `gold` in `treasure.gold` range → `add_gold_to_tile` → "drops N gold" message.
   - Roll `item_chance` → `_spawn_treasure_item(x, y, item_tier)` (common pool, excludes uniques; `effective_floor = max(1, tier * 5)`).
   - Roll `treasure_chance` → one piece of treasure (`treasure.roll`, of `treasure_kinds`) → "drops a Burmese Ruby".
   - If `ammo_drop` → `_spawn_archer_ammo` (archer monsters drop a stack of their declared ammo id).
   - If `boss_scroll_id` → `_spawn_boss_scroll` (fixed drop from Fafnir / Abaddon).
   - If `unique_drop_id` → `_spawn_unique_item` (mini-boss fixed drop, looked up by id across unique pools).

### The orphan legendaries — v2.18.0 unlocked them

Before v2.18.0, four `is_mini_boss` legendaries had NO `spawn_chance`, so `_roll_planned_mini_bosses` filtered them out silently and no hardcoded spawn path existed. The v2.18.0 fix wave gave each one `spawn_chance = 1.0`:

| id | min_level | peak_floor | spawn_chance |
|---|---|---|---|
| `asmodeus` | 92 | 93 | 1.0 |
| `surtur` | 87 | 90 | 1.0 |
| `ymir_last_spawn` | 82 | 85 | 1.0 |
| `hrungnirs_ghost` | 80 | 82 | 1.0 |

All four are now candidates for the band-5 (81-100) mini-boss slots. `surtur`, `ymir_last_spawn`, and `hrungnirs_ghost` are also `[2, 2]` footprint — they rely on `_footprint_fits` to find a 4-tile free pocket.

### `item_tier` cap (v2.18.0 clamp)

The design cap is 1-5 and `_spawn_treasure_item` scales as `effective_floor = tier * 5`. Pre-v2.18.0, 7 dragon-tier monsters carried `item_tier` 6-10 (would have produced `effective_floor` 30-50 — plausible numerically but outside the documented 1-5 schema). The v2.18.0 catalog is strictly within 1-5 (verified: current counts 1=61, 2=99, 3=151, 4=116, 5=100).

## Special monster modules (2026-10)

**Theft (`src/theft.py`).** An attack with `steal` that lands rolls `steal_chance`; the monster notes the wish (`_wants_steal`) and the game carries it out right after the blow (`theft.steal`), because gold belongs to the Game, not the Player. `"gold"` takes a share of the purse (`economy.THEFT_PURSE_SHARE`), `"item"` one unworn pack item (bright magical kinds three times as likely), `"any"` either. Worn or wielded gear, containers and scripted quest pieces are never stolen. A thief takes one haul and then runs (`after_theft: flee`) or vanishes at least `TELEPORT_MIN_DISTANCE` tiles away first (`teleport`); it never leaves the floor. Whatever it carries falls on its tile when it dies (`theft.give_back`, called from the kill handler).

**Splitting (`src/splitting.py`).** `Monster.take_damage` asks `blow_splits`: with `by: "weak_blow"` a blow under `share` of the original health splits it (Blood of Tiamat); with a list of damage forms, only a blow made wholly of those forms does (a black pudding cut by an axe, not a thrusting sword; spells count by element). Without `into` the creature divides and the new body takes half the remaining health; with `into` the blow lets out that creature instead (Azhi Dahaka's vermin). `max` caps the splits of a whole lineage. The split is counted on the monster (`_pending_splits`) and `spawn_pending(game)` places the bodies on free adjacent tiles at the end of every action, whatever caused the wound.

**False stairs, the Hellmouth (`src/false_stairs.py`).** A `mimic`-AI monster with `disguise: {"tile": "stairs_down"}` is drawn as a down stair until it springs (`unseen.disguise`, `renderer.draw_disguise`). `seat` decides where it may lie so it never costs the hero the way down: plain floor only (no fixture on it), the real down stair kept and still reachable from the up stair with the false tile blocked, reachable ground outside the arrival room, at least `MIN_STAIR_DISTANCE` from the real stair, at most `MAX_PER_FLOOR` per floor, and none on a floor without a real down stair. It runs at floor generation (`level_manager`, before the floor is dressed and again after it, since a statue in a maze corridor or a doorway can make its tile the only way through: round 3, 2026-11-14) and on every floor entry (`Game._settle_monsters`).

**The Black Knight (`src/black_knight.py`).** An easter egg, every run since Dungeon Alive slice 8 (2026-11-12; it was one run in four): on one floor from 15 to 19 the `black_knight` stands on a short bridge over a strip of water across a corridor that always has another way round. With no corridor that suits he takes a doorway with a way round, and failing that a tile in a room (never the arrival room) where he cuts nothing off (`black_knight.find_site`: `bridge`, `doorway`, `room`). He is never set down where he would be the only way through: on a floor with no such tile he waits for the next visit (round 3, 2026-11-14; he used to take any free tile). `BlackKnight(Monster)` never moves; any single action takes him down to the next of the 75 / 50 / 25 per cent marks and no further (one limb per action, ticked by `Game._advance_turn` before and after the world moves), the last leg needs a blow that leaves him on 1 and another to take it, and his attack changes with each stage. When his sword arm goes, his sword (`flesh_wound` in `data/items/weapon.json`) falls on the bridge. At 0 he is not killed: a torso that calls it a draw and swaps places with the hero. Run state is `game._black_knight` (`floor`, `spawned`, `outcome`, `sword_dropped`); text lives in `data/black_knight.json`.

**The Stray Kids (`src/stray_kids.py`, `src/game_stray_kids.py`; 2026-11-13, the dance-off 2026-11-14).** An easter egg, every run, for Brandon's kids. On one floor from 8 to 12 a gold shrine to the K-pop band Stray Kids (`sk_idol` in `data/fixtures.json`) stands against a room's wall (`decor.place_event_stand`, which never cuts the floor off). It calls the hero over the first time he sees it (`idol.call`); Observe shows a shrine plainly Stray Kids to a fan (SKZ, STAY, eight little dancers) without naming them; walking into it hums and invites a proper touch; walking into it again, from the same spot, touches it and takes the hero to the Zombie Stage (L997, a side floor: [world](world.md)). There the eight members (`sk_zombie_<member>` in `data/monsters.json`: restless dead, never rolled anywhere, no gold, no harvest) stand posed in a V at the far end of the stage hall (`stage.formation`, Bang Chan at its point). They are **performers, not foes** (`ZombieMember`: `is_allied`, so no blow, spell or pet touches them, nothing holds them, and they never strike; polymorph still passes them by, WB-C06/D06). The first time the hero sets foot on the stage (`stray_kids.on_stage`) the band strikes a pose and **"B-B-B-BOSS BATTLE! DANCE OFF!"** fills the map (`_stray_kids_announce`: the effects runtime's `dance_off_banner`, the kill banner's `StrikeFinisher` with a banner of its own, bigger and 2.4 s long; the `dance_off` fanfare in `sound_system`; the line in the log; `stage.tell` says what the dance-off is). Once the banner is over and play is calm (`_stray_kids_frame`, every frame) the dance-off opens on the Mooble's dance screen (`game_mooble_dance.py`, owner `stray_kids`; `rhythm.py` judges): **Practise** first, free, no stakes, no turn, as often as wanted (Space; D to the dance-off; Esc: Not Yet), then the **dance-off**: eight rounds of **Simon Says**, one member leading each in the members' order (Bang Chan first), his own sprite on the screen stepping with each step (no dance poses yet), his opening line above (`dance_off.leaders.<member>.open`), the band's faces under it, the fallen dimmed. Round r (0 first) dances the first `first_steps + r * steps_per_round` steps of the written `choreography`, one a beat (4 steps up to 11), at `bpm_first + r * bpm_per_round` (84 up to 112): a count-in, his call, then the hero's turn over the same bars (whole bars with at least a beat of rest: `stray_kids.phrase_beats`). It is danced from memory (`memory`): once the hero's turn comes the call's arrows go dark and his own row shows only where each step falls until it is judged. A round is won with 75% of its steps in time and no more than 2 misses. **Won:** its leader falls to the dance through the kill handler like any death (`_sk_fall` sets `_danced_down`, so he is not "slain": `_on_monster_killed` still raises the `kill` event and the kill quirks, and `_stray_kids_member_died` says he crumbles into glitter, writes his Journal line and, for the last, drops the photo). **Lost:** his roast (`leaders.<member>.roast`) and the **earworm** (`stray_kids.earworm`): his song (his attack with a hindrance, a voice first) gets stuck in the hero's head, its quip said, its hindrance for its turns (confusion, sleep, a stun, dazzle or weakness), and its dice in damage, never more than `max_damage` and never the last hit point; the round starts again with a strike gone. **Three strikes** (`strikes`) a dance-off: out of them, the band laughs (`laugh`), the members still standing go back to their places (`settle_band`; the fallen stay fallen), and the hero is set down at the edge of the stage (`stage_edge`), shaken but alive; walking into any member challenges them again (`_stray_kids_bump`, `stage.challenge_again`), and the stage door still leads out. Esc leaves the card, and the first round's card of a dance-off before it is danced; after that a dance-off is danced through. Winning, or losing it, is the turn. Each member has a roast of a well-known fan in-joke in his lore, his Observe line (`observe_line`, with `dance_off.observe_tell`) and his song's quip: Bang Chan never sleeps, Lee Know's cat matters more than you (he sometimes pets it instead of shouting), Changbin's villain act keeps slipping, Hyunjin's hair flips, Han raps too fast to follow, Felix's black-belt kicks barely register, Seungmin roasts your outfit, I.N is babied. While the hero walks the stage after the announcement, a member in sight now and then shouts (`shouting`). They leave no corpse (`_no_corpse`) and crumble into glitter; the hero knows them on arrival (`lore_known_monster_ids`). The last to fall leaves the **Autographed Stray Kids Photo** (`data/items/scroll.json`, effect `summon_stray_kids`, a one-of-a-kind keepsake: never sold or stolen). Read (one grammar question; a bad read keeps it), it is spent and the band, alive (`StarDancer`, `sk_star_<member>`), dances round the hero for `stars.dance_turns` turns: allies that neither strike nor are struck, and every monster near them (`stray_kids.near_show`, `can_watch`: not named foes, not the mindless, not what cannot be stunned, not the blind) is held watching (stunned for `watch_turns`, the longer of the two holds, never the sum). The watch line is said only of a creature the show really held; a named foe in sight says `unmoved_named` ("Lamia has seen better shows, and does not stop."), a mindless one or a swarm that cannot be stunned `unmoved` ("The Scarab Swarm pays the show no mind."), once each a show (round 3). The show ends one way, with its bow: its turns run out, or the hero leaves the floor (the stars came for him: `_stray_kids_leaving`, from `Game._change_level`), so a revisit never finds it running on. A save mid-show loads with the show going on; a save while the dance-off screen is open opens it again on load at the start of the current round with the strikes that were left (`dancing`); a save on the stage from before the dance-off (the band fighting in formation) loads with the band back in its places as performers (`_stray_kids_after_load`). Achievement hooks, the same as when the band was fought: every member's fall raises the Seeker's `kill` (monster `sk_zombie_<member>`, family `restless_dead`, from `_on_monster_killed`), and the last one's fall sets `photo_dropped` and `outcome` 'cleared', writes the `stray_kids:cleared` Journal line and drops the photo. Every line is made up, never a real lyric, reworded or not: `shouts.songs` riff on the songs' titles and concepts (Case 143's 1-4-3 pager code and police video, Christmas EveL's naughty-list pun, God's Menu's chefs, Thunderous's singer-and-nagger pun and goblin dance, Maniac's Frankenstein stitches, Chk Chk Boom turning Deadpool down), and each member has a riff of his own. Text and numbers: `data/stray_kids.json`. Run state `game._stray_kids` (`floor`, `spawned`, `touched`, `return_floor`, `outcome`, `photo_dropped`, `challenge`, `dancing`, `lost`). QA: Shift+K on the Titivillus build sets the idol beside the hero; pressed again, the photo in the pack; on the stage with the band standing, the dance-off at once. Art: `tools/content/genart/briefs/stray_kids.json`, installed by `install_stray_kids.py`. Tests: `tests/test_stray_kids.py` (the data, the Simon Says rules, the earworm, the performers, the dance-off won, lost and challenged again, saves old and new); the whole run through the real keys (the idol on its floor, the stage, the announcement, practice twice, a round lost on purpose and the rest won on time, the photo, the spent idol, the show and who watches it, a save mid-show, leaving mid-show): `tests/test_stray_kids_journey.py`.

## Invariants

- **Every monster is a `Monster` instance.** No subclassing except `DeathMonster`. Behaviour variance comes from JSON fields, not Python classes.
- **`peak_weight > 0` ⇔ in the procedural pool.** `peak_weight == 0` is the "story-locked" signal. Bosses, seal demons, orphan legendaries are all `peak_weight == 0`; placement goes through `level_manager` or `boss_levels`.
- **`min_level` is a hard lore gate**, `peak_floor` is a Gaussian center. No `max_level` cap in the current pool code.
- **Boss immunity is monster-side.** `is_boss_or_huge(m) = m.is_boss or m.max_hp > 500`. The `boss_immune` flag lives on hero specials and gates whether to apply the check.
- **`_adjacent_to(player)` is footprint-aware.** Multi-tile bosses are adjacent if the player is adjacent to ANY of their 4 tiles.
- **The game-loop drives one `Monster.take_turn` per tick per monster.** Status-effect ticks live in `Game._advance_turn`, not in `take_turn`, because double-ticking would halve durations and double DOT damage.
- **Pre-rolled mini-boss slots are deterministic for a run.** `_planned_mini_bosses` is populated in `__init__`; re-visiting a floor doesn't re-roll (idempotent via `_placed_mini_bosses`).
- **Seal demons always spawn on their floor.** Even if the player dies and reloads mid-floor, idempotency via `_placed_mini_bosses` prevents double-spawn.

## Interactions with other systems

- **Combat** — `combat.py::player_attack` reads `monster.resistances`, `monster.weaknesses`, `monster.dragon_scales`, `monster.tags` (for material effective_against), `monster.footprint` (for AOE), `monster.is_boss` (for status DCs). `monster.take_damage(amount, damage_type, ignore_resistance)` is the one damage entrypoint.
- **Food system** — `game_combat._make_corpse` threads `harvest_tier`, `monster.kind`, `monster_def` tags onto the `Corpse`. `food_system.harvest_corpse` resolves the ingredient by `monster.kind` in `data/items/harvest_map.json`.
- **Quests / mysteries** — seal demons mutate `game.seals_broken`. Abaddon's locust bursts set `_wants_locust_spawn` for the game loop to spawn `abyssal_locust`. Angels' `seek_locust` targets locusts via `_annihilate_target`.
- **Hero specials** — `is_boss_or_huge(m)` gates charm/paralyze/confuse/sleep/immobilize. `boss_immune` on a special says "respect `is_boss_or_huge`."
- **World / dungeon** — `dungeon.phasing_walls` is a per-dungeon set of wall tiles the Minotaur (and only the Minotaur, in practice) can pass through. `_populate_hidden_chambers` keyword-themes monsters via `monster.kind` / `monster.name` substring matches.
- **Bones** — `bones.py::spawn_ghost` instantiates a ghost `Monster` on a floor from a prior run's death.
- **Save system** — `Monster._DEFAULTS` + `__getattr__` back-compat shim is the forward-compatible pickle contract: new fields added to `__init__` must also be added to `_DEFAULTS` so old pickles don't `AttributeError`.

## History

- 2026-08-06 — Harvest v4. `harvest_threshold`, `ingredient_id` become dead fields (kept on disk for pickle compat).
- 2026-05-19 — Density rebuild + bell-curve spawn pool. `_build_spawn_pool` replaces the old min/max-level clamp.
- 2026-06-06 — Per-room population pass. `populate_floor` added; `spawn_monsters` kept for intentional clustering.
- Pre-v2.18 — Pre-rolled mini-boss planning via `_roll_planned_mini_bosses`.
- 2026-09-27 (v2.18.0, commit `409e15d`) — Full systems audit + fix wave:
  - `is_boss` JSON wire fixed. 10 mini-bosses recover boss-immunity.
  - 4 orphan legendaries given `spawn_chance = 1.0`.
  - `DeathMonster.take_damage` accepts `damage_type` / `ignore_resistance` kwargs.
  - `item_tier` clamped to 1-5 for the 7 dragon-tier offenders.
  - Known dead JSON fields documented: `harvest_threshold`, `ingredient_id`, `attack_effects`, `mortal_weapon_floor`, `chain_break_on_hit`.

## Testing

- Unit tests under `tests/` cover: HP dice parse, attack dice parse, bell-curve weights (`tools/balance/curve.py` is the source of truth for the curve), `_damage_multiplier` resistance/weakness tables, mini-boss planning determinism.
- The audit path is `tools/audit/` + the `SYSTEMS_AUDIT.md` report. See its §1 for the complete v2.18.0 monster findings list.
- `tests/test_mini_boss_bands.py`: every band mini-boss, legendary wanderer and seal demon sits in its band against `floor_curve` (health and blows), the data matches `mini_boss_bands.py`, no turn is a one-blow death, none is tankier than the final boss, each has a tell, and each aims truer than its floor.
- Multi-tile placement is tested by instantiating each of the 5 footprint-`[2,2]` monsters in a procedural room and asserting all 4 tiles land on walkable floor.
- No play-test is practical for most of the 527-monster catalog; this is the regime where [play-test rule has limits](../feedback_play_test_limits.md) applies — logic tests on JSON + pure-function tests on `_damage_multiplier` / `_build_spawn_pool` / mini-boss planning are the primary guards.

## Appendix: full mini-boss roster (36)

The `is_mini_boss` flag identifies the pool `_roll_planned_mini_bosses` draws from (minus the 7 seal demons, which take a forced path, and historically minus the 4 orphans — now fixed in v2.18.0).

Alphabetical, with the key diagnostic fields:

| id | peak_floor | spawn_chance | unique_drop_id | ai_pattern | footprint |
|---|---|---|---|---|---|
| `anansi` | — | set | — | summoner-ish | 1×1 |
| `arachne` | — | set | — | — | 1×1 |
| `asmodeus` | 93 | 1.0 (v2.18.0) | — | summoner | 1×1 |
| `asterion_minotaur` | 20 | 0 (hand-placed L20) | — | hit_and_run | 1×1 |
| `baba_yaga` | — | set | `iron_mortar_wand` | — | 1×1 |
| `blood_archon` | — | set | — | — | 1×1 |
| `cacus` | — | set | `vulcans_brand` | — | 1×1 |
| `camazotz` | — | set | `obsidian_talisman` | — | 1×1 |
| `charybdis` | — | set | `sailors_amulet` | — | 1×1 |
| `cow_king` | 999 | 0 (hand-placed Cow Level) | — | — | 1×1 |
| `echidna` | — | set | `echidna_fang` | — | 1×1 |
| `erlking` | — | set | — | — | 1×1 |
| `green_knight` | — | set | — | aggressive + revive | 1×1 |
| `hrungnirs_ghost` | 82 | 1.0 (v2.18.0) | — | aggressive | 2×2 |
| `jormungandr_juvenile` | — | set | — | — | 1×1 |
| `lamia` | — | set | — | dancer | 1×1 |
| `medusa_gorgon` | 40 | 0 (hand-placed L40) | — | dancer | 1×1 |
| `nemean_lion` | — | set | — | aggressive | 1×1 |
| `nidhoggr_fragment` | — | set | — | — | 1×1 |
| `rangda` | — | set | — | — | 1×1 |
| `ravanas_arm` | — | set | `ring_of_iron_grip` | — | 1×1 |
| `seal_demon_wrath` | 83 | — (forced) | `seal_of_wrath` | — | 1×1 |
| `seal_demon_pestilence` | 85 | — (forced) | `seal_of_pestilence` | — | 1×1 |
| `seal_demon_famine` | 87 | — (forced) | `seal_of_famine` | — | 1×1 |
| `seal_demon_war` | 89 | — (forced) | `seal_of_war` | — | 1×1 |
| `seal_demon_death` | 91 | — (forced) | `seal_of_death` | — | 1×1 |
| `seal_demon_earthquake` | 93 | — (forced) | `seal_of_earthquake` | — | 1×1 |
| `seal_demon_silence` | 97 | — (forced) | `seal_of_silence` | — | 1×1 |
| `sets_jackal` | — | set | `anubis_scales` | — | 1×1 |
| `surtur` | 90 | 1.0 (v2.18.0) | — | — | 2×2 |
| `talos` | — | set | `bronze_aegis` | — | 1×1 |
| `the_sphinx` | — | set | `sphinx_crown` | — | 1×1 |
| `tiamat` | — | set | — | summoner | 2×2 |
| `wendigo` | — | set | `wendigo_fang` | — | 1×1 |
| `wild_hunt_captain` | — | set | `hunt_captains_sword` | — | 1×1 |
| `ymir_last_spawn` | 85 | 1.0 (v2.18.0) | — | — | 2×2 |

The audit also notes `asterion_minotaur`, `medusa_gorgon`, and `cow_king` as `is_mini_boss` with **no `spawn_chance`** — all three are intentionally hand-placed (L20 / L40 / L999), so they never need the random pool. The pre-roller filters them correctly on the "no spawn_chance" rule.

## Appendix: elemental resistance table semantics

`combat._damage_multiplier(damage_types: list[str], monster) -> float`:

```
# Load material tags (effective_against → implicit weakness tags)
# Example: silver weapon vs undead/demon → appends 'silver' to weaknesses
# Example: cold_iron weapon vs fey → appends 'cold_iron' to weaknesses

mults = []
for dt in damage_types:
    if dt in weaknesses: mults.append(1.5)
    elif dt in resistances: mults.append(0.5)
    else: mults.append(1.0)
return max(mults) if mults else 1.0
```

**Key properties:**
- Multi-type attacks (`slash+pierce`) take the BEST multiplier — monster-side resists don't stack across types.
- `ignore_resistance=True` on `take_damage` clamps the returned multiplier to `>= 1.0` (weaknesses still trigger, resistances don't). Used by chain-equip Heart of Ahriman unmaking_sense proc on spell crits.
- `psionic` is NOT in the game's canonical set — treated as unresistable `1.0` for any monster. Rename to `psychic` is the audit-suggested fix.
- Legacy fallbacks: `silver` weakness is injected for `undead`+`demon` tags; `iron` weakness is injected for `fey` tag. The data-driven material system is authoritative, these are safety nets.

## Appendix: status effect DC math

Attack-side status application (both the normal path and the gaze fall-through):

```
dc = min(18, atk.get('effect_save_dc', 12 + self.min_level // 7))
roll = random.random() < atk.get('effect_chance', 0.30)
if roll:
    if reflecting_proc and random() < 0.50:
        reflect to attacker
    else:
        apply_debuff_with_save(player, effect_id, duration, dc)
```

- Base DC = `12 + min_level // 7` (grows 1 per 7 lore floors; L1 = DC 12, L50 = DC 19 → clamped to 18, L100 = DC 26 → clamped to 18). Monster JSON can override via `effect_save_dc`.
- Save stat is per-effect, read from `status_effects.SAVE_STAT`.
- `apply_debuff_with_save` returns `(applied, message)` which the caller may suffix to the attack-hit message.
- Gaze paralyze uses the same DC formula.

The attack-table status-effect ids are 17 (verified in `status_effects.py`): `bleeding`, `blinded`, `burning`, `confused`, `cursed`, `diseased`, `feared`, `frozen`, `hallucinating`, `paralyzed`, `poisoned`, `silenced`, `sleeping`, `slowed`, `stunned`, `teleportitis`, `weakened`.

**Who can bleed (3.3.3):** `data/monster_blood.json`, read by `monster.kind_can_bleed` and `Monster.can_bleed`. A creature with no blood never takes `bleeding` (`add_effect`, `hold`, the weapon and pet procs that write it straight in; `tick_effects` drops one left by an old save) and is never called "bleeding". Order: the kind's own entry (`bleeds` / `bloodless`), then `bleeding_families` (vampires), then `bloodless_families` (ghosts, constructs, elementals, oozes, plants) or `bloodless_tags` (undead, construct, plant), else it bleeds. The fleshy dead (ghouls, zombies, revenants, deadites, the wendigo) bleed; liches, bone witches and the jiangshi do not.

## Appendix: `_DEFAULTS` and the pickle-compat shim

`Monster._DEFAULTS` is a class-level dict of EVERY attribute `__init__` sets, each mapped to its initial value. `__getattr__` consults `_DEFAULTS` on `AttributeError` — so an old pickled Monster from before the multi-tile feature inherits `footprint = (1, 1)` automatically on first access, without needing a migration.

**Rule:** every new field added to `__init__` MUST also be added to `_DEFAULTS` in the same commit. Otherwise old saves `AttributeError` on first access.

## Known rough edges

- **`grave_knight.enraged_pattern = fenrir_rage`** without `rage_interval` or `rage_damage_bonus` — enrage swap is a no-op (audit P1). Needs rage fields OR a different pattern.
- **`abaddon_destroyer.chain_break_on_hit`** sets `player._chain_disrupt_pending` but nothing reads it. Dead-wired (audit P2).
- **`mythic_hydra.enraged_multi_attack_count = 4`** but only 3 attacks — falls through to "fire all." Misleading data.
- **`hrungnirs_ghost.enraged_multi_attack_count = 0`** explicit — enrage doesn't escalate. Likely typo.
- **`blood_archon` + 7 seal demons carry BOTH `is_boss` and `is_mini_boss`** — conflicting classification. The two flags should be mutually exclusive by design intent but aren't enforced.
- **`mind_flayer`, `asmodeus`** attack type `psionic` — not in `_damage_multiplier`'s set. Treated as unresistable `1.0`. Rename to `psychic` or add to the resistance table.
- **`air_elemental` (min_level=4, 2d10+8), `water_elemental` (min_level=7, 2d10+6), `stone_giant` (min_level=10, 3d8+10)** — Gaussian tails reach floors where player HP is 25-40 and the damage dice can one-shot (audit P2 — hazard flag, not fixed).
- **`abyssal_locust`** — L98, HP 2d8, max damage 6. Only spawned via Abaddon's locust burst but the shape in JSON is indistinguishable from a data typo. A `quest_only` tag would gate it from any accidental procedural placement path (none currently applies, but the shape is fragile).
- **`_make` defined twice in `boss_levels.py`** (lines 533, 646, identical). Harmless duplicate.
- **Níðhöggr lore** in monsters.json carries U+FFFD replacement chars where `ð` should be. Visible in-game. Related rot in `armor.json` and `ingredient.json`.
- **Dead JSON fields** (`harvest_threshold`, `ingredient_id`, `attack_effects`, `mortal_weapon_floor`, `chain_break_on_hit`) — kept on disk for pickle-compat per v2.18.0 decision. A later pass could migrate them out.
