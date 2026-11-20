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
- `data/monsters.json` — 609 monster definitions keyed by id (2026-11-17) (every monster is a top-level key with `name`, `symbol`, `color`, `hp`, `attacks`, `ai_pattern`, …).

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
On run start, `LevelManager.__init__` calls `_roll_planned_mini_bosses()` (the pure `level_manager.plan_mini_bosses`), which iterates five 20-floor bands (`1-20`, `21-40`, `41-60`, `61-80`, `81-100`), one per gate boss's domain, and in each band fills a FIRST slot (always) and a SECOND slot (30%): **a run meets one or two named foes in every band**, 6.5 a run (Brandon's ruling 13, 2026-11-16: "maybe one or two every 20 floors"). Each slot picks weighted by `spawn_chance` among the band's candidates (`band_candidates`: every rolled mini-boss whose `peak_floor` lies in the band, the legendary ones included). The placement floor is the chosen mini-boss's `peak_floor`, or the free floor of its band nearest it (`_free_floor`: never a gate, seal or other planned floor). Where each one sits is decided by its legend: see "Mini-bosses by lore" below.

### Seal demons are FORCED, not rolled
`_SEAL_DEMON_LEVELS = {83, 85, 87, 89, 91, 93, 97}` → 7 fixed seal-demon ids. `_try_spawn_seal_demon` runs after mini-boss pre-rolling, is-mini-boss aware (the pre-roller ignores `seal_demon_*` ids), and guarantees placement. Each seal-demon kill is tracked in `game.seals_broken`; at 7/7 the game logs the "way to the Pit stands open" Journal entry.

### Boss immunity: a two-step check, now with a JSON wire
`hero_specials.is_boss_or_huge(monster)` is the one function status-application code calls. Through v2.17 it was effectively `max_hp > 500`, since `Monster.__init__` silently dropped the JSON `is_boss` field. v2.18.0 added `self.is_boss = bool(defn.get('is_boss', False))` to `__init__` — the fallback stays as a safety net, but 10 mini-bosses (`iron_patriarch`, `whispering_crone`, `blood_archon`, 7 `seal_demon_*`) now get boss-immunity properly instead of relying on their HP dice happening to exceed 500. `boss_immune: True` on a hero special says "this status skips bosses"; the check is monster-side (`is_boss_or_huge`) and the special-side flag just gates whether to apply the check.

### Multi-tile monsters are NW-anchored rectangles
The default `footprint` is `[1, 1]` (every regular monster). Five bosses declare `[2, 2]`:
- `fafnir_dragon` — L58-62, hand-placed in Dragon Hoard (L60).
- `tiamat` — floor 88, a planned mini-boss of the abyss band.
- `surtur` — floor 90, likewise.
- `ymir_last_spawn` — floor 78, a planned mini-boss of the frost band (since 2026-11-17).
- `hrungnirs_ghost` — floor 86, a planned mini-boss of the abyss band.

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
| `spawn_chance` | float | optional | Only read by `_roll_planned_mini_bosses` (`plan_mini_bosses`) — the mini-boss's weight in its band's slots; 0 or none keeps a mini-boss out of the plan (hand-placed). The legendary ones carry 0.3 since 2026-11-17 (they ride their band's slots). Unrelated to `peak_weight`. |
| `frequency` | int | legacy, default 3 | Only consulted inside `_spawn_one_in_room` for pack-size scaling (`freq >= 5` → +1 max). Not the main spawn knob. |
| `thac0` | int | default `max(-10, 20 - min_level)` | AD&D-style "to-hit AC 0." Lower is more accurate. Since 3.3.2 rebaked to the armour line by `tools/balance/rebake_thac0.py` (a typical monster hits a hero of its floor about 55% of the time; [armour.md](armour.md)). |
| `thac0_lore` | int | | The written THAC0 before the rebake: the tool always starts from it, keeping half of each monster's accuracy against its band. |

### Boss / role flags

| field | type | notes |
|---|---|---|
| `is_boss` | bool | **Read from JSON since v2.18.0.** Grants boss-immunity to charm/paralyze/sleep/confuse via `hero_specials.is_boss_or_huge`. Also lifts `min_hit_chance` from 5% to 25%. Carried by: `abaddon_destroyer`, the 7 `seal_demon_*`, `iron_patriarch`, `whispering_crone`, `blood_archon`. **Fallback:** `max_hp > 500` also counts as boss, regardless of this flag — the hand-crafted boss-level `_spawn_boss` additionally forces `boss.is_boss = True` after construction. |
| `is_mini_boss` | bool | Candidate for the pre-rolled mini-boss slot system. 44 monsters carry this flag; `_roll_planned_mini_bosses` filters out `seal_demon_*` (forced path) and `spawn_chance <= 0` (32 are rolled). A mini-boss counts as a keystone kind of its family (`family_lore`). **Known overlap:** `blood_archon` + the 7 seal demons carry BOTH `is_boss` and `is_mini_boss` — audited as a conflict P4, kept as-is. |
| `is_seal_demon` | bool | 7 monsters. On death, `game_combat._drop_treasure` adds the corresponding seal to `game.seals_broken` and writes a Journal line. 7/7 opens the Abyss narrative. |
| `is_allied` | bool | Allied monster: `heavenly_angel` (does not attack the player; dispatched to `seek_locust` AI), the encounter people and performers, and the horns' allies (below). |
| `horn` | str | The horn that calls this kind (`data/horns.json`): Robin Hood's men, Arthur's knights, the einherjar, Charlemagne's host. With `is_allied`, `quest_only`, `frequency` 0 and `min_level` 0 it is never spawned or found; on the map it is a `horns.CalledAlly` built from this entry's `hp` and first attack. |
| `boss_immune` | — | NOT a Monster field; this is a flag on `hero_specials` entries declaring "my effect should skip bosses." The monster side is `is_boss` / `is_boss_or_huge`. |

### AI shape

| field | type | notes |
|---|---|---|
| `ai_pattern` | str | One of 16 values — see §"AI dispatch" below. Default `aggressive`. |
| `perception_range` | int | default 8 | How far a monster SEES (Chebyshev), along a real line of sight (`senses.clear_view`). It no longer notices through walls. `passive_silent_walk` (Hand of Glory, Boots of Elvenkind) halves it against the wearer and silences footsteps; a lit torch, lantern or Light spell lengthens it against the hero by the light's notice (`lights.shine`, 2026-11-19). See "Senses" below. |
| `alert_radius` | int | default 5 | Chebyshev radius for `alert_nearby` (same-kind allies wake up when I'm adjacent to the player). |
| `alert_all_tag` | bool | default False | Warlord/horn-blower mode — alert any monster sharing at least one tag, not just same-kind. |
| `aggression` | — | Not a Monster field; "aggression" is expressed via `ai_pattern` + flags, not a scalar. |
| `pack` | bool | default False | Spawner hint: when this monster is picked for a room, extra copies also spawn in the same room. `pack_size: [min, max]` counts the whole pack, leader included (every pack kind has one since the lore pass); without it the size scales with depth (1-2 extras shallow, 2-3 mid, 2-4 deep, +1 max when `frequency >= 5`). Whether a pack HUNTS as one is `data/packs.json` (see "Packs" below). |
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
| `gaze_cooldown` | int | default 4 | Turns between gazes (counted down in `tick_effects` for every gazer, AI-1). |
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
| `stalker` | dict | default none | The stalking coward's numbers (`ai_pattern: stalker_coward`, `Monster._stalker_turn`; Brandon 2026-11-17). He watches with his eyes (`senses.sees`, so an invisible hero goes unseen). **A false friend first:** from first sight he comes up to the hero and keeps `friend_keep` tiles off (a step back when the hero comes beside him, never more), and never strikes. He helps where it is safe (`_stalker_help`, `_safe_to_stab`): a monster at or under `help_below` of its health, in the hero's fight and beside the hero or held fast, he darts in on, stabs once with his first attack and steps back, at most once in `help_gap` turns, with a helper line (`_help_hit` for the game); never one at full health, never one free to hit him back, never a named foe or a story creature. **The reveal** (`_revealed`, for good): a hero in a `prey_on` state that he sees or hears, he darts in on still smiling; the act drops only the moment he reaches him, with a shout (danger colour, his bubble), and his blow that same moment (`_sneak_ready`, `Monster._resolve_blow`, `sneak_blow`) never misses its roll and lands `sneak_mult` times as hard (his spear). No cap: it can kill. Struck first, the act drops with no sneak attack. `_stalk_reveal` says why, for his line. **Revealed:** he strikes only a hero beside him, and only when he cannot back away (a wall or a corner); a hero coming at him he backs away from, toward his hoard (`_hoard`, in his own room `_wary_home`); a hero walking away he follows `keep` to `keep` + `slack` tiles off. A hero in a `prey_on` state (`resting`: the wait key this turn, `senses.TURN.rested` from `senses.note_rest`; or `sleeping`, `paralyzed`, `confused`, `stunned`) that he sees or is within `hears_prey` tiles of, he darts in on at `dash_steps` steps a turn and strikes; when it ends he backs off again. Out of sight `lose_after` turns he goes home to his hoard, and he is back there when the hero returns to the floor. He swipes at no pet until he has been in a fight (`_provoked`). `_stalk_event` (dash / prey / cornered / backs / follows / home) is what his turn did, for his lines. Old Nickel, who wears the Bloomleaf Cloak (`src/emberpup_encounter.py` (BloomleafMixin)); his lines are `data/old_nickel.json` (`src/old_nickel.py`); his room never holds the pup, a stall or one of the Road's people (an anchor, a story NPC, the unicorn, an escort), and no encounter NPC is set down in it. (It replaced `wary`, the kobold who kept to his room: a Nickel saved with it becomes a stalker, `_old_nickel_refresh`.) |
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
| `summon_kind` | str or [str] | Monster id(s) to summon. Empty = no summoner. Monsters that carry a value include `ancient_lich`, `skeleton_mage`, `skeleton_necromancer`, `skeleton_lich`, `banshee_lich`, `lich_sovereign` (its court of dead knights, 2026-11-17), `cult_hierophant`, `imp_lord`, `snake_charmer`, `whispering_crone`, `crypt_summoner`, `endor_medium`, `ushabti_overseer`, `tiamat`, `asmodeus`. |
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
| `unique_drop_id` | str | Mini-boss fixed drop (its signature piece) — looked up by id in the unique-item pools, or an enchanted piece made to a spec (`armor:<template>:<material>:<enchantment>:<level>`, the Bonnacon's cloak). Every rolled mini-boss but Tiamat has one (her signature is her boss scroll, the Scroll of Chromatic Doom), of its band's tier: see "Mini-bosses by lore". The seven seal demons drop their `seal_of_*`; Old Nickel the Bloomleaf Cloak. |
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
- **Sight:** a line of sight within `perception_range` (+4 for `keen_sight`; plus the brightest light's notice against a lit hero: a torch 2, the Light spell 3, the dark lantern's shutter 2; see [items](items.md), "Lights in the off hand"). Walls, closed doors and tall fixtures (statues, stalagmites) block it; water and low furniture don't. An invisible hero is unseen except by `truesight` (celestials).
- **Sound:** the game emits noises through `Game._make_noise(kind)`:
  - footsteps each turn the hero moves (`step_radius`: 3 at DEX 10, quieter with DEX, +1 under a Light load, +2 under a Heavy one and +3 when Burdened or Overloaded (data/senses.json noise, the four tiers of 2026-11-16), +1 in medium body armour and +2 in heavy, +1 more in metal unless it is quiet (`gear.footstep_tiles`), silent with Cat's Footfall or silent walking);
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
- G5: an archer that's adjacent steps back to a tile 2 away that still has the shot. (It was half the time, `_step_back`; since AI-2 it is every time it has a shot from there, at most twice running: `src/lanes.py`, see "The Tactical Mind".)
- Dagger backstab now counts any target that isn't tracking the hero.
- Observe (`;`) adds the state line (`status_lines`; a stalker on the hero's trail: "He follows you, smiling, offering to keep watch." as a false friend, "He is following you, just out of reach." once the act has dropped). How a creature hunts (`senses_line`) is shown once its kind is known.
- What the hero did this turn reaches the monsters through `senses.TURN` (`begin_turn`, from `CombatMixin._senses_begin_turn`): `moved`, `guilty`, and `rested` (2026-11-17), true when his action was a rest, the wait key (`senses.note_rest` in `_player_input`, read back by `senses.rested_on`). The stalking coward darts in on it (`stalker`, above). A hero asleep or paralysed is read from his statuses. (Searching a body with H is another still turn not yet counted as a rest: the harvest flow was being reworked at the time.)

**Scavengers (C3).** `data/senses.json` lists them under `scavengers`: ghouls, ghasts, the otyugh, charnel hounds and their kin, and any vermin or ooze. When one is idle (not hunting, not searching, awake) and smells a corpse within 8 tiles, `CombatMixin._scavenge_prep` gives it that place (`_scavenge`), and it walks there whatever its post. It eats for 3 turns, so a harvest is a race; it heals a quarter of its health and the corpse is gone. The hero sees "X is feeding on the corpse.", and Observe says "It is busy with a corpse."

**G7.** Phase-blink now fires for the patterns that never reached it. An archer or a summoner blinks out to a clear shot 4 tiles away; Lyssa (hit-and-run) blinks in beside the hero. Asterion lowers his horns for a charge in his hunting state, not only once enraged. **QA:** Shift+A on the Titivillus build lists the floor's Dungeon Alive content and shows the map; pressed again, it sets down a war-band.

Tests: `tests/test_senses.py`.

## War-bands (Dungeon Alive slice 5, 2026-11-12)

Brandon: monsters must "pose a real challenge and players need to pay attention to lore, weaknesses, abilities". A war-band (`data/war_bands.json`, `src/war_bands.py`) makes camp in one big room on 55% of the floors in its range, from floor 1, never more than one band a floor. Floors 1-6 hold only the two small bands, sized for a new hero (Brandon 2026-11-16, bug bash 3.5.1 Q12: a level-1 hero of 30 HP and AC 10 died in about 5 turns to a whole gang of footpads); the bigger bands (goblin raiders, the bandit crew, the gnoll pack) begin on floor 7 (they were from 3 and 6, about 10 HP a turn on a floor-3 hero). A goblin scouting party is a hobgoblin and at most two followers (goblins, perhaps a shaman, a sniper from floor 3): about 3 HP a turn on floor 1, at most 3.4. A gang of footpads is a couple: the captain and one more, a footpad or one gang in four an archer: about 3.4 HP a turn, at most 4. A band's `most_followers` caps its followers in all, whatever each role rolled (`war_bands.pick_band`). 3.5.1: a floor's own encounters carry the fight; see Wanderers. It replaces that room's ordinary roll. `LevelManager.generate` calls `war_bands.place_band` after the hidden chambers. The run's people are set down later and never in the camp (`war_bands.camp_tiles` / `outside_camp`): the Road's anchors and story folk, a trader's stall, the Emberpup, Old Nickel, the unicorn and the mouth of the Mooble's cave (bug bash 3.5.1).

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
- **Nerve.** A follower whose leader lives never breaks (Morale by Nature, below, leaves him to the band).
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

## Packs: kin that hunt together (2026-11-19)

Brandon, 2026-11-18: "add packs that fight 2+ at a time, the more diverse and unique our monsters are, the better"; the design he approved on 2026-11-19; and "rats swarm could add damage based on how many rats are adjacent to the player; build it". The rules are `src/packs.py`, the numbers and words `data/packs.json`.

**A pack, not a war-band.** A pack is a kin group of one lore family set down together (`pack`, `pack_size`). `dungeon._spawn_one_in_room` calls `packs.on_spawned`: the members share a `_pack` uid, a wolf pack may be led by its parent (`leader`: a wolf pack leader takes one place, 40%, when the floor's pool holds him), and a kobold pack lays its den's traps (only while the floor is first peopled: `level_manager` sets `dungeon._dens_open`). A war-band's member keeps to its band and never uses pack tactics (`packs.in_pack`). Neither does a friend, an encounter's person or a named foe.

**Which kinds hunt as a pack** (`packs`, by lore; every kind with `pack: true` and a `pack_size` is either here or among the `herds` with the reason it does not hunt as one, `tests/test_packs.py`):

| Pack | Kinds | In a corridor | Trick |
|---|---|---|---|
| rats | giant rat, dire rat | press on | swarm |
| wolves | wolf, wolf pack leader, dire wolf alpha, winter wolf | hold | hamstring (and they circle to his back) |
| jackals | jackal | hold | dart |
| hyenas | cave hyena | hold | harry |
| gnolls | gnoll, gnoll archer | hold | harry |
| goblins | goblin | hold (and sling) | sling, then charge |
| kobolds | kobold | hold | traps |
| ghouls | ghoul, ghast | hold | feast |
| harpies | harpy | hold | snatch |
| hounds | gravehound, shadow hound, blink dog, Fionn's hound, Hecate's hound, abyssal hound | hold | bay (and they circle) |

**The hunt** (`packs.hunt_turn`, called by `Monster.take_turn` for an aggressive pack hunter that knows where the hero is and is not beside him; `tactics` holds the numbers):
- **Far off or alone** (more than `engage_radius`, 5 tiles, or no packmate within `mates_radius`, 8): it comes on as any creature.
- **In the open** (`packs.slots`: the tiles beside the hero the pack can reach from its side with a short walk, at most `reach_nodes` tiles searched): each takes a free tile beside him on its own side (`packs.choose_spot`: farthest round from where the pack already presses him, the walk there kept off the tiles beside him), and claims it so the next goes elsewhere. Wolves and hounds (`circle`) make for his back: away from the way he faces (`_facing_dx/_dy`), or from the first of them on him.
- **At a choke** (`choke_slots`: one tile or none beside him can be reached from their side; a corridor, the far side of a doorway): the one already on him fights. The rest go round when there is another way to another side (`packs.round_path`: at most `round_nodes` tiles, `round_max` steps, kept `round_every` turns while he stands still). Failing that, they hold beyond the mouth out of his sight, in reach of it (`packs.hold_step`), for him to come out. A slinger holds where it can see him to pelt him. After `patience` (12) turns of holding, the nearest tries his luck. One hurt while it waits (an arrow, a flask) comes for him. Rats (`corridor: press`) pour in anyway: vermin do not think so far, so a corridor is the hero's answer to a swarm.
- **Hunt together** (`packs.alarm`, from `senses.notice` when one first finds him): the pack is roused to him as far as its cry carries round corners (`rouse_radius`, 8; a hound's bay much farther).
- **Lines** (`_pack_line`, said by `CombatMixin._pack_turn_after` after the monster's turn, once a fight for the pack): "The wolves will not follow you into the narrow way...", "One of the wolves slips away to come at you from another side.", "The goblins drop their slings and rush you together!"

**The tricks** (`tricks`; each has a tell, `pack_<trick>` in `data/tells.json`, ranked with the others, and a Bestiary line, `bestiary`, for a kind the hero knows):

| Trick | What it does | Numbers |
|---|---|---|
| swarm (rats) | Each rat's bite is worth more for every OTHER rat of its pack beside the hero (`packs.blow_mult`, in `Monster._resolve_blow`). One rat is a nuisance, four are deadly. Said when two or more others are on him and the count has grown. | +50% per other rat, at most +150% |
| hamstring (wolves) | A wolf's bite that lands while a packmate stands beside him may hamstring him: slowed, through the one rider path (guards, wards, the DEX save halves it). Never while he is already slowed. | 25% a landed bite, 3 turns (within CONTROL_CAP 6) |
| dart (jackals) | In the open a jackal that can reach him in one step darts in and snaps at once (no free blow for him); on its next turn beside him it darts back out of reach if a packmate is near to take its place. At most two on him at a time, each on its own beat. | max_in 2 |
| harry (hyenas, gnolls) | While he is below half his health their bites are worth more, they never run from him when hurt, and they do not wait at a corridor's mouth. | x1.3 below 50% |
| sling (goblins) | With a clear shot from 2-5 tiles a goblin pelts him with its Sling Stone while the pack gathers. When three (or all that live) are up within 5 tiles and each has thrown, they all rush him together. Into a choke they never rush: they keep pelting from the mouth. Beside him a goblin uses its knife. | Sling Stone 1d3 blunt, ranged |
| traps (kobolds) | A kobold den is set down with 1-2 hidden snares or caltrops within 3 tiles. Beside him, a kobold may back off a step and lay one on the tile it leaves (always when it is hurt); one laid where he can see it is shown. Monsters never set off an ordinary trap, so kobolds walk over their own. The trap kinds are data (`traps.kinds`): `_check_floor_trap` applies a trap's `effect` through the saving throw, `_fire_trap_on_monster` turns a rewired one on a monster, and both disarm at AI tier 1. | snare: immobilized 1-2 turns; caltrop: 1d4 pierce (a share of his health, as every trap) and slowed 3-4; 1 each, 40% a turn beside him |
| feast (ghouls) | When he is held (paralysed, asleep, stuck fast, stunned) every ghoul of the pack within 10 tiles comes for him past any mouth it held, and their bites on him are worth more. | x1.25 on a held hero |
| snatch (harpies) | A harpy's Talon Rake that lands may snatch food or a raw cut from his pack (`theft.steal` 'food'); she flies off with it and drops it where she dies. | 35% a landed rake |
| bay (hounds) | The first hound of a pack to find him bays: every hound of the pack the sound reaches is roused to him and keeps his scent (`packs.keep_scent`: it knows where he went) for 20 turns. Heard even out of sight. | radius 14, 20 turns |

**The new pack kinds** (`tools/content/add_pack_kinds_2026_11.py`, by the lore rubric): the **jackal** (floor ~2, 1-6: 4d4+4 HP, a 1d4 Snapping Bite, speed 14, packs of 2-3), the **wolf** (floor ~6, 4-10: 7d8+8 HP, a 1d6+1 Bite it lunges with, speed 14, packs of 2-3, sometimes led by a wolf pack leader), and the **cave hyena** (floor ~22, 18-26: the Ice Age hyena of Kirkdale Cave, 27d10+120 HP, a 2d8+5 Bone-Crushing Bite, packs of 3-4). The hyena is the cave hyena of tier 2 because the tier census holds tier 1's ordinary kinds to 35% (it stood at 190 of 546; two new ones fit). A wolf and a jackal are butchered as the pack leader is, a cave hyena as the gnolls (hyena meat). The goblin gained the Sling Stone its trick throws.

**The simulator** (`tools/balance/difficulty_sim.py`, knob `packs`, on by default): a pack's members come at the hero together rather than queue at the doorway (a rat pack half the time), and the tricks that change a fight's cost run in the monster's own code (the swarm, the hamstring, the harrying, the feast). The movement tricks have no map there. `packs=0` is the ablation.

Tests: `tests/test_packs.py` (data, the swarm's numbers, the choke and the hold on hand-made maps, and the tricks in a game).

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
| KNOWN | the kind studied, its page opened (Thoth, Omnisight, Recall Lore at chain 5, the Wand of Probing, a gate boss's quest step), or its family at Lore (`full_lore_tier`, 3) | the sign, what it does and the counter, then what it is made of, in ONE line that names it (`tells.lore_line`, 2026-11-16): "The Skeleton: weak to blunt, holy and silver weapons (or metals like it); resists slash, pierce, cold and poison; can't be put to sleep, poisoned or charmed." No multipliers (the help page defines the words), and nothing of a creature still hidden (named "something") until it is seen |

- **First sight:** the first time in a run the hero sees a kind, `_maybe_tell` says its worst tell at what he knows, and at KNOWN what it is made of, tell or no tell (winning-build plan 3.1). It is said again the first time he sees the kind after he knows it better. This is tracked in `_dungeon_alive['told_level']` ({kind: level}, saved); an old save's `told` list counts as told at UNKNOWN.
- **Observe:** says up to 2 tells at the same level, and at KNOWN what it is made of (`tells.lore_lines`). A KIN creature adds "You know its kind, but not how to beat it. Study its corpse."; how it hunts (`senses_line`) is said only at KNOWN.
- **The Bestiary:** (what a KNOWN page shows, with sizes, bane materials, scales, ward and regeneration: combat.md "What the hero is told of it", 3.5.1) a KIN kind's page opens, but its weaknesses, resistances, what it shrugs off and its nature read "not yet studied" until it is KNOWN; at KNOWN the page shows "Weak to", "Resists", "Shrugs Off", "Immune To" and "Falls Easily To".
- **The hit lines, the Strike Now preview and the combat strip's weakness tag** follow the same levels: see [combat](combat.md), "Knowledge decides what the line says".
- **Honest about reach:** `tells.reach` is 'far' when the creature can put the effect on the hero from across a room. That covers a gaze, or an attack a ranged, dragon, healer, summoner or rooted creature uses at range (the same test as `Monster.attack`). A far effect gets `counter_far`, or the shared `far_counter` ("keep stone between you"), and never "fight it from a distance".
- **Splitting:** the line names the blows that split the creature, from its own `splits.by`.
- **What counts as a tell:** attack effects with `effect_chance` of at least 0.1, plus these flags: gaze, splits, revives, drain-heals, regeneration, summons, pull, SP drain, charge, phase-blink, the trick of the creature's pack (`pack_swarm`, `pack_hamstring`...: see Packs), and its ways from the first wave of monster behaviour (`kind_data.tell_keys`: `breath_recharge`, `heals_allies`, `life_drain`, `light_shy`, `snuffs_light`, `raises_alarm`, `death_throes`, `relurks`, `hides_in_dark`, `shove`). They are ranked by `order`, worst first.

Tests: `tests/test_monster_notes.py`, and the Observe cases in `tests/test_observe_bestiary.py`.

**Patrols (C5).** A wandering monster now arrives beside a stair the hero can't see, as if coming down or up it, instead of out of nowhere. It goes to a fight or alarm it can hear from there, or roams.

## The lore pass: each monster's numbers from its own lore (2026-11-19)

Brandon, 2026-11-19: "Your fix SUCKS AGAIN, because you started using smoothing multipliers to hit a target ... NEVER DO THIS ... Fix the data at the source." And: "the more diverse and unique our monsters are, the better."

- **What it replaced.** Earlier passes had seated every ordinary monster on a floor curve. Every floor-1 kind bit for 1d2, and every floor-16 kind (troll, xorn, banshee, specter) hit for 1d8+2. On every floor a landed blow was about 5% of that floor's hero's health and a turn about 3%. On floors 4-22 the median monster had 56-73% of the anchor HP and died to one maths chain.
- **What it did.** 517 kinds were re-written by size, natural weapons or carried weapon, skill, speed and signature power. Each got its own dice, routines (`multi_attack_count`), HP, to-hit, rider durations, pack size and `opener`, with a one-line lore reason. The rules are in `docs/design/MONSTER_LORE_PASS_2026_11_19.md`: role ranges as a share of the hero who meets the monster, the engine's limits, and what not to touch. `tools/balance/apply_lore_pass.py` checks each proposal and writes it.
- **Where it stands.** `tools/balance/monster_bands.py` measures each floor against the simulated hero of that floor.
  - A turn now costs about 4-5.7% of the hero's health on average, and the hardest tenth of kinds costs 2.5-4 times the gentlest tenth.
  - About half the kinds open with their power.
  - The median HP sits at 0.85-1.1 of the anchor. Floors 4-11 are about 0.85, because early kinds linger many floors past their peak.
- **Weapons were not refitted.** The weapon curve sizes against a frozen copy of the 3.5.4 monsters (`tools/balance/weapon_curve_monsters_3_5_4.json`). Today's typical monster is 1.1-1.3 times that, most of all on floors 7-20. Refitting the weapons would hand back the one-blow kills.
- **The old tools now refuse to write:** `respawn_by_hp`, `scale_monsters`, `apply_difficulty_schedule`, `monster_pass_2026_11_17` and `late_game_monsters_2026_10` (`tools/balance/lore_pass_guard.py`). The tests that held monsters to the HP curve were retired. `tests/test_monster_lore_pass.py` holds the pass's own rails: no turn over a quarter of the peak floor's hero's health, riders within the engine's caps, no twin kinds from floor 4 down, every floor diverse.
- **Edit a monster one by one, by lore.** Check the result with `apply_lore_pass.py` and `monster_bands.py`.

## Openers: a creature's power before the hero strikes (2026-11-19)

Brandon: "openers for sure". The powers "dont seem to make a lot of difference" because a monster died to the first maths chain before it used one.

- **Data:** `"opener": {"attack": "<one of its attacks>", "range": N}` in `monsters.json`, written per creature from its lore.
  - Pounces, lunges and charges are range 1.
  - A first volley, a gaze, a song or a breath is range 2-7.
  - An optional `wind_up` overrides the tell line.
- **Range 1 (a pounce):** on the turn the creature closes to the hero, it strikes with that attack in the same turn (`Monster._pounce_now`). Without an opener, closing ends its turn and the hero strikes first.
- **Range 2 or more:** when it has noticed the hero and he is within range and in its line of sight, it opens with that attack (`Monster._opener_from_range`).
  - A missile flies at once.
  - A gaze, voice or breath is first drawn up for one turn (`monster.OPENER_WIND_UP`): "The basilisk fixes its eyes on you." That is the tell. The hero can answer it by closing, breaking line of sight, putting in wax or raising a mirror.
- **The blow** is an ordinary blow. To-hit, saves, the head guard, family wards and counters all apply.
- **Once a fight.** The opener is ready again only after the creature has lost the hero for `OPENER_RESET_TURNS` (5) turns.
- **The simulator** gives an opener one free blow when the monster joins a fight (`difficulty_sim.Run.fight`). That slightly over-counts the drawn-up powers, which the game lets the hero answer.
- **Tests:** `tests/test_monster_openers.py`.

## Monster behaviour, first wave (AI-1, 2026-11-19)

Brandon's MONSTERS AND MAGIC pass: "add depth to our bad guys". Each behaviour is a small pure module with a one-line hook in `monster.py`, its numbers and lines in `data/monster_ai.json` and its per-kind fields in `monsters.json` (read through `src/kind_data.py`, so an old save reads its kind's new fields with no migration; per-monster state lives in the creature's own `__dict__`, written as a new dict each time, so the simulator's copies and a split body share nothing). Lines go through `src/ai_lines.py`: a behaviour leaves (seen, unseen) and the Game says the seen one if the hero can see the creature, the unseen one (a sound, never a name) if not (`BehaviourMixin._ai_turn_after`, `src/game_behaviour.py`). Named foes, the allied angels, the encounter people, the unicorn, Death and the stalker are left alone unless a behaviour says otherwise. Each has a simulator knob, on by default (`tools/balance/sim_ai1.py`). The field shapes are listed in `_mm_2026_11_19/AI1/FIELDS.md`.

### Three fixes to the AI we had

- **The gaze looks again** (`fix_gaze_cooldown`). `_gaze_cooldown` was counted down only by the dancer AI, so the floating eye (sessile) gazed once in its life. It counts down in `Monster.tick_effects` now, one a turn, for every gazer; the dancer's own tick is gone (it would have ticked twice). The gorgon sisters still share one gaze.
- **Healers heal what matters** (`fix_healer`, `src/faction.py`). A healer mended any creature that shared any tag with it (an orc priest's 'humanoid' mended a bandit), spent its turn on a one-point scratch, and healed every turn. Now it mends only its own side (`ai_faction`: its war-band, else its pack, else its family, else its kind; the loose tags never make a side; pets, escorts, called allies, angels and encounter people never), only a friend under `heal_below` (0.6) of its health, the one beside the hero first, then the most hurt; then it rests its voice `heal_cooldown` (3) turns (`_heal_cd`). A band healer mends its band only. The line is unchanged ("The Orc Priest chants and heals the Orc Warrior for 30 HP!"). Tell: `heals_allies`.
- **Summoners call when it counts** (`fix_summoner`, `src/summoning.py`). The timer ran before the summoner had seen the hero, it called whatever the range, sight or need, and its cap counted every minion ever made. Now its timer runs only while it hunts the hero; when it is up it calls only with the hero within `reach` (8) and in its sight, and while fewer than `summon_live_cap` (2) of its own summoned stand (`_summoned_by`, set by `Game._spawn_summoner_minion`); `summon_max` stays the most it ever calls. The call is a one-turn chant ("The Skeleton Necromancer raises his hands and begins to chant."), and any real blow that lands on it in that turn breaks it (never a bleed, burn or poison ticking; `summoning.spoil` from `Monster.take_damage`): the call is spent and its timer starts again. The line names who broke it (`spoil_lines`): "Your blow breaks the Skeleton Necromancer's chant!", "Your Ember breaks...", "The blast breaks..." (a death throes), or "The Skeleton Necromancer is struck, and his chant breaks off." (a hazard, another creature). The ordinary summoners of other patterns (the ancient lich, the skeleton mage, the lich sovereign) chant the same way; Tiamat and Asmodeus keep their own tuned timers. The `summon_kind` tell's counter says to strike while it chants.

### Draws Breath (`breath_recharge`, `src/breath.py`)

A breath, once breathed, must be drawn again: `recharge` turns on the attack, else 3 for any `delivery: "breath"` attack of an ordinary kind (57 kinds: dragons, drakes, the winter wolf, the chimera, frost giants, a toad's acid spit...). Meanwhile the creature comes in with tooth and claw: the ranged AI (`_ranged_turn`) closes when its only shot is drawing (it used to breathe every turn it had a shot and step back from a hero who closed); a creature with no blow of its own keeps off; a flurry fires the next ready attack of its routine instead of a breath still drawing (`breath.flurry`); `Monster.attack` never uses a breath still drawing (`breath.choose`: another ready blow, never one from afar, else "The X draws a rattling breath."). Every blow spends its attack (`breath.spend` at the top of `_resolve_blow`), the opener too. When it is ready again the hero who can see it is told, by the breath's type ("Smoke curls from the Young Red Dragon's jaws."). Named foes keep their tuned flurries (their breaths recharge only when their data sets `recharge`); Fafnir keeps his own clock (`_breath_cd`, `DRAGON_BREATH_RECHARGE`, the same 3). State: `_recharge` ({attack: turns}). Tell: `breath_recharge` ("Close in while it draws breath"). Hero answers: close in while it draws breath, a dug pit, resistance, the cloak's guard against breath, a corner.

### Morale by Nature (`morale_by_nature`, `src/morale.py`)

The old rule: every aggressive creature that was not a named foe and had no more than 500 health fled under a quarter of its health for 8 turns, and fled again as long as it stayed hurt (the timer re-armed itself). A zombie or a golem ran from its wounds, a goblin on floor 2 broke, about half of every ordinary kind from floor 21 down never did (the 500 rule was depth by the back door), and a fleeing creature beside the hero went on swinging. Now each creature breaks the way its nature says (`data/monster_ai.json` `morale`: the kind's own `morale_style` / `morale` in `monsters.json`, else its family's row, else `withdraw` 10; a `construct`, `plant`, `ooze` or `mindless` tag, `fearless` or a `status_immune` "feared" make it `never`):

| style | who (family default) | when it breaks |
|---|---|---|
| `never` | restless dead, constructs, oozes, plants, elementals, ghosts; the cult zealot | It fights to the end ("The Zombie does not care that it is falling apart.", once). |
| `bolt` | vermin 6, birds 7, great beasts 8, serpents 8, shapeshifters 9 | It runs 8-12 turns, then has given up the fight (`_cowed`): it keeps away from a hero it can see, goes about its business when it cannot, and fights only when cornered. A ranged blow finishes it. |
| `regroup` | goblinkin 7, mortals 9; lizard-men, frog-men, cave-men | It runs for the nearest of its own side within 12 tiles (no nearer the hero than it is), and reaching them rouses everything of its side within 3 tiles of that one: the hero meets three goblins, not one. With nobody to run to it withdraws. |
| `withdraw` | fair folk 9, aberrations 11, giants 12, gorgons 12, legend 13, vampires and liches 13, demons 14, dragons 16, celestials 16; the veteran knight 14 | A fighting withdrawal of 8 turns ("The Hill Giant falls back, fighting as he goes."): it backs off a step at a time, and a hero who presses it is struck half the time (`withdraw_strikes`, 0.5); then back into the fight. |
| `yield` | the bandit thug, the bandit thief, the mercenary veteran 11, the cult initiate 7 | As regroup; caught with no friend to run to and nowhere to go, it throws down its weapon and its purse (its gold falls on its tile, `BehaviourMixin._ai_drop_purse`; what it stole too) and begs. It never strikes again (no blow on the hero or a pet, whatever holds it: checked at the top of its turn) and keeps out of his way; pets leave it alone; he may spare it or kill it (no karma either way, Brandon's call to review). A band's captain who yields is answered as if he had fallen (the band routs). |

- **Who:** every ordinary hunter keeps a nerve, whatever its way of fighting (`morale.RULED_PATTERNS`: melee, archers, hit-and-run, summoners, healers, ranged dragons, dancers, and a pack creature gone cowardly when alone). The rooted, a mimic or an ambusher still lying in wait, the stalker and named foes never break. (Until the audit only the melee kinds did: 144 ordinary kinds, the bandit archer among them, never broke.)
- **When:** a morale check (2d10 over its morale 0-20 breaks it) the first time it falls under a quarter of its health; again when it is under half and one of its side falls within 8 tiles and its sight (`morale.kin_fell`, from the kill handler); and after five landed blows in a row that did nothing (it cannot hurt the foe, penalty 2: `ai_blow.after_blow`). One check a trigger: it never re-arms itself. Healed above half it steadies and can break again later.
- **Running:** along the longest free way from the hero (a 6-step search of the ground about it, not the greedy step that walked into dead ends), or to its friends (`senses.step_toward`). Cornered beside the hero (no step away) it turns at bay for 3 turns: it strikes, +2 to hit, no flight ("The Goblin turns at bay, cornered!", once a life).
- **Kept as they were:** the galla (`fearless`), a war-band follower while his leader lives, a hyena or gnoll that smells a wounded hero (packs `harry`), a thief with a haul, the stalker. Named foes never break; there is no health test at all now.
- **State:** `_flee_timer`, `_wound_checked`, `_morale_check`, `_rally_to`, `_rallied`, `_bolting`, `_cowed`, `_at_bay`, `_zero_hits`, `_yielded`, all in the creature's own `__dict__` (an old save's monster reads none and has its family's nature).
- **Hero answers:** kill the runner before it reaches its friends (a sling, a bow, a wand); a cornered creature fights harder, so leave it a way out or finish it; fear works on deep mortals and beasts again; let a bolting beast go.
- **Simulator** (`ai_morale`): the real checks. A creature that breaks strikes no blow while it runs (the hero lands one at `CHASE_HIT_PROB`), except a withdrawing one, which strikes half its turns; a withdrawal comes back; a bolt leaves the fight when its run is spent and is found again and finished later half the time; a regroup with kin still waiting at the doorway goes back to the queue behind the next of them; a yield leaves, spared. At bay is not modelled (the simulator has no walls).

### Life Drained (`life_drained`, `src/life_drain.py`)

The drain type (67 kinds) cost a point of CON on a failed save, at most once a floor, never below CON 8, and most drainers hit like anyone else; the classic drainers (wight, wraith, barrow-wight, cairn-wight, fetch) struck with plain necrotic and drained nothing. Now a landed drain blow (type `drain`, or `drains_life: true` on the attack: those five) whose save fails (the old CON save, DC 12 + depth/7, with the family ward against draining) lowers the hero's max HP by `drain_share` (0.5) of the blow, at most 10% of his whole health from one blow and 25% in all, never below a new hero's health, kept in `player._life_drained`: "The Wight drains your life away! (Max HP -6)". It comes back: half at the next new floor down ("Sleep gives back some of what the dead took."), all from the physician's Restore (counted as points of 3 health in its price) and from the Mercy prayer at a chain of 4 (an altar counts one). `drain_resist` stops it. The old CON point stays for the greatest (`drain_con: true`: the lich, greater, ancient and arch-lich, the death lord), and named foes keep only the old CON rule. The blood-drinkers feed on it (`drain_heals_self` written by lore: vampire spawn, nosferatu, strigoi, vrykolakas 0.5; vampire lord and elder vampire 0.75; the strix and the ker 0.5). Tell: `life_drain`. Hero answers: kill it fast, the ward, prayer, the physician, the stairs.

### Grave Rot (`grave_rot`, `src/grave_rot.py`)

`diseased` cost a stat point about one bite in three and no health, and was gone in 4-8 turns; on a monster it ticked 0.4% a turn. Now, on the hero, while diseased his wounds do not mend by rest (`main._tick_hp_regen`) and every heal that goes through `Player.restore_hp` does half (potions, spells, prayers, meals; a drain wand's draw, a kill's heal and a worn piece's regeneration do not go through it; the stat sap stays); a monster's disease lasts its rider's own `effect_duration`, times the kind's `disease_linger` where its lore makes the sickness one that lingers (mummy rot 10; Pazuzu's spawn, Hel's handmaid, the plague ooze 8; the plague witch, Nidhogg's brood 6; the aboleth, the otyugh, the demon general, the abyssal dragon 5; the plague zombie, the harrow witch, the ghast-eater 4; the huecuva 3), at most 60 turns (`status_effects.MAX_EFFECT_DURATION`); a rat's bite, a zombie's claw, a wererat's or a death dog's bite keep their own few turns. (A first build lingered every disease x 10, which the lore never asked of a rat's bite; the simulation section of the AI-1 report says what it cost the slowest kid.) On a monster it costs `max_hp / 40` a turn (poison's rate) and stops its regeneration (a sick troll does not mend). Cured by the Potion of Cure Disease, the Mercy prayer at a chain of 4 (before its heal, so the heal is whole), the physician, a fountain's best water; `poison_resist` and `drain_resist` block it. The rubric's line on riders (`docs/design/MONSTER_LORE_PASS_2026_11_19.md`) now says what each one does.

### Light-Shy and Snuff the Light (`light_shy_and_snuff`, `src/light_shy.py`)

- **Light-shy** (`light_shy: true`: the six trolls, the dvergar hoard-wardens, the dark elves and drow, the shadows and shades, the nightwing, the darkmantle, the kobolds, the hidden folk): within the reach of a lit hero's light (its sight) it needs +2 to hit for each point of the light's glare (a carried light 1, the Everburning Lamp, the Hero's Lamp and Hecate's Torch 2, the Light spell 2, a torch held as a weapon 1), at most +4 (`ai_blow.to_hit_shift`). "The Troll flinches from your light." (once a fight).
- **The troll's wounds** (agent A's troll item; the lore now says it: "a strong light is the next best thing, and a troll hates it"): a regenerating light-shy creature standing in the light cannot close its wounds (`_regen_blocked`, a turn at a time, `BehaviourMixin._ai_turn_after`): "The Troll's wounds stop closing in your light."
- **Stone** (`turns_to_stone_in_light`: the trolls, the dvergar): three turns in the Light spell's glare and it is slowed 3 turns ("The Troll's hide stiffens in the light, like stone!"). Never petrified; named foes never.
- **Snuffers** (an attack's `snuffs_light`: the water elemental's Wave Crash, the air elemental's Vortex, the whirlwind jinni's Dust-Devil Blow, the darkmantle's Engulf Head, the shadow master's Shadow Claw half the time, the drow priestess's Divine Curse): a landed blow douses the light in the hero's hand, soaked for 3 turns (water), 1 (wind) or 2 (dark); `_toggle_light` refuses meanwhile ("The wick is soaked."). Dark also ends the Light spell. An everlasting light or one with a power is never snuffed.
- **Tells:** `light_shy`, `snuffs_light`. The price of a light stays: a lit hero is seen from farther.

### Gone Again (`hit_and_run_vanishes`, `src/gone_again.py`)

18 of 21 hit-and-run kinds cannot walk through walls, and after their blows they stood three tiles off in plain sight for 4-6 turns. Now one breaks off ("The Imp darts away to hide.") to the nearest tile out of the hero's sight within 12 tiles (round a corner, behind a pillar) and hides there; the hero coming within 2 tiles or seeing it, or any blow on it, ends the hiding and it fights. With no cover in reach it backs off as before. `hides_in_dark` (the shade, the shadow demon, the quasit, the imp, the boggart): while it hides it is unseen (`unseen.is_invisible`, `_dark_hidden`) if the hero carries no lit light and cannot see the invisible. Asterion and the phasing vampires are as they were.

### Raise the Alarm (`raise_the_alarm`, `src/alarm.py`)

`alarm` ({radius, tags?, line, line_unseen}) on a kind: the first time it sees the hero (`senses.notice`), once a floor, it shouts, and every creature of its side the sound reaches (`senses.sound_map`) within the radius is roused to him (its kind, band, pack, family, or a listed tag); sleepers wake as to a loud noise, never under the Hand of Glory; a sleeping, frightened or silenced lookout does not shout. It rouses only what is already on the floor. Kinds: the kobold, the kobold trapsetter and pack leader, the goblin and goblin sniper, the gnoll (a whooping laugh), the orc scout, the hobgoblin, the bandit thug, the cult initiate, Hugin, the Stymphalian bird, the harpy, the poltergeist (it knocks). Tell: `raises_alarm`.

### Death Throes (`death_throes`, `src/death_throes.py`)

`death_throes` ({type, share, radius, effect?, effect_duration?, line, warn_line, delivery?}): when it dies (not banished, not ashed, not a named foe) everything within its radius and its sight, the hero and the other creatures alike, takes `floor_curve.wound(share)` of its own health in that type and the rider through the usual save (`BehaviourMixin._ai_burst`; a `delivery: "voice"` rider is stopped by wax). It swells the turn it falls under a quarter of its health (`warn_line`, once). A creature the blast kills bursts after it, one at a time (a queue); the hero gets the kills. An `alarm_radius` on the throes is a cry that goes through stone (the mandrake's shriek, slice M): every creature that can hear within that many tiles is roused to the hero (`alarm.cry`; sleepers as to a loud noise, never under the Hand of Glory); wax in the ears still stops its stun (`delivery: "voice"`). A blast that breaks a summoner's chant says so ("The blast breaks..."). Kinds: the fire beetle (5%), the burning skeleton, the magma and lava elementals, the myconids (spores: hallucination, confusion), the gas spore, the plague zombie and zombie hulk and plague ooze (disease), the toxic jelly (poison), the crystal ooze (shards: bleeding), Pazuzu's spawn. Tell: `death_throes`.

**Gone Again and Back to the Web after the audit:** a bleed, a burn or a poison ticking is not a blow (`Monster.take_damage` inside `tick_effects`, the `_dot_tick` guard slice G uses): it ends no hiding, springs no lurker and breaks no chant.

### Back to the Web (`relurk`, `src/relurk.py`)

A sprung ambusher with `relurks` (the spiders, the piercer, the darkmantle, the lurker above, the trapper, the cloaker, the ettercap, the jorogumo, the crypt thing), under 60% of its health, out of the hero's sight 3 turns and not hunting him, goes back into hiding once a life: an ambusher again, unaware and unseen until it springs; no second surprise blow. A hero within 8 tiles hears it go ("Something scuttles away into the dark."). Tell: `relurks`.

### Shove (`shove_into_danger`, `src/shove.py`)

An attack's `shove` ({chance, aim}): a landed blow may throw the hero one tile straight back (a STR save, DC 13, keeps his feet); never into a wall, water, lava, a pit or a creature, never while he is held. The giants (hill, stone, frost: `aim`) throw him onto a hazard among the three tiles away from them, and the hazard's own rule fires (`BehaviourMixin._ai_resolve_shove`, after the monsters' turn, beside the pull). Kinds: the hill, stone and frost giants, the cyclops brute, the ettin, the ogres, the minotaurs, the troll brute and war troll, the cave bear, the iron and stone golems. Tell: `shove`.

### The simulator's knobs

`tools/balance/sim_ai1.py` (merged into `difficulty_sim.KNOB_DEFAULTS`): `ai_heal`, `ai_summon`, `ai_breath`, `ai_morale`, `ai_drain`, `ai_rot`, `ai_light`, `ai_vanish`, `ai_alarm`, `ai_throes`, `ai_relurk`, `ai_shove`, each 1 (the game's rule) by default; 0 is its ablation. Its docstring says what each models and what it cannot.

## The MONSTERS AND MAGIC kinds and their lore powers (2026-11-19)

Thirty-two kinds from real myth, folklore, scripture and natural history (D&D gave
only the mechanics; research in `_mm_2026_11_19/A/`), written by the lore rubric
against the hero of each kind's floor. The data is written by
`tools/content/add_mm_kinds_2026_11.py` from `tools/content/mm_kinds_data.py` and
`mm_kitchen_data.py` (idempotent; every wiring row: affinity entries, sizes, senses,
family assignment, harvest and the kitchen, packs.json herds, tells, hints, purse).

- **Tier 1:** mandrake, kappa, eloko, asanbosam, ahuizotl, khalkotauros, cu_sith,
  bulgasari, vetala, likho. **Tier 2:** centaur, nahual, blue_men_of_the_minch.
  **Tier 3:** vila, myrmekes (gold-digging ant), ponaturi, taniwha, impundulu,
  mapinguari, preta, upas_tree, nuckelavee, star_jelly. **Tier 4:** psoglav,
  waq_waq_tree, yuki_onna, yacumama, tsuchigumo. **Tier 5:** bhuta_vahana_yanta
  (Relic Guardian), reem (2x2), eitr, bakunawa.
- **Lore powers** (`src/lore_powers.py`, pure; the game's side `src/game_lore_powers.py`).
  Each is a field on the kind and says one line when it fires:
  - `countdown_voice`: the Cu-Sith barks every 3 of its turns while the hero is in its
    sight; the third bark is its attack (a voice: wax stops it). Between barks it stands
    and watches unless he is beside it, so he has the turns to get away; after the third it
    hunts like any hound. Out of its sight the count is lost.
  - `metal_eater`: the Bulgasari: a blade that can rust (status_effects._can_rust:
    iron and steel, never a unique) that lands may lose a point (items.wear_down), and
    the meal mends it, its body growing up to `grow_cap` past its health.
  - `weak_spot_chain` (+ `weak_spot_line`): a chain that long ignores the Mapinguari's
    resistances (combat.strike_damage).
  - `sheds_skin`: the Lindworm at each share in `at` throws off its wounds (bleeding,
    poison, cracked armour...; never a hold) and mends `heal_share`.
  - `on_stunned`: the Kappa stunned or held is weakened (its dish spills).
  - `blinded_loses`: Likho blinded cannot use the attacks named.
  - `appeased_by`: plain food (lore_powers.is_plain_food: never a dish cooked to
    carry) set down within 2 tiles is eaten and the creature keeps to itself for the
    floor; struck, the peace is broken. The Kappa and the Preta.
  - attack `steal: "offering"`: the Preta snatches plain food and eats it (theft.py).
  - `parley`: the Blue Men call a verse on first sight and hold their fire 6 turns;
    D answers (one question of `subject` at their tier); right, the pack is calm for
    the floor; wrong, they attack at once. Walk away or strike and they attack.
  - `gold_gatherer`: gold dropped within 2 tiles of a gold-digging ant is gathered
    up (and gone); the ant spends `turns` doing it.
  - `corpse_hop`: when the Vetala's body falls, the spirit rises in the nearest corpse
    within `radius` at `hp_share` of its health, at most `max_hops` times. Harvest or
    search the dead first.
  - attack `carry_off`: the Roc lifts the hero (`chance`, halved under a Heavy load)
    and sets him down `tiles` away on an explored, empty tile, held a turn.
  - attack `pulls`: the Yacumama's breath draws the hero a step toward it.
  - `hidden_overhead`: the Asanbosam and the star jelly hang above; a lit light (or
    the Light spell) shows them inside its glow (unseen.senses).
  - `talisman`: any scroll read while a Jiangshi can see the hero holds it 2 turns.
  - Two new senses (`data/senses.json`): `breath` (the jiangshi: a hero who rests holds
    his breath and is lost beyond arm's reach) and `blood_scent` (the Komodo brute: a
    bleeding hero is found through walls from 24 tiles).
- **AI-1's behaviours on these kinds** (shapes in `_mm_2026_11_19/AI1/FIELDS.md`;
  `tests/test_mm_kinds_ai1.py` shows each at work): `light_shy` (ponaturi, star_jelly),
  attack `snuffs_light: "dark"` with `snuff_chance` 0.5 (bakunawa), `death_throes`
  (mandrake: a voice, so wax stops its stun), `alarm` (waq_waq_tree: radius 10, `tags`
  naming the living that hear it, since an alarm rouses only its own side, here the
  plants, unless tags say more), `relurks` (asanbosam, ahuizotl, tsuchigumo), attack
  `recharge` 4 (catoblepas's gaze); the breath attacks take the default recharge, the
  drain blows take lasting health, and each kind keeps its family's nerve.
- **Fields that wait on slice AI-3's engine:** attack `hold` (taniwha), `aura`
  (mapinguari, upas_tree, ghast), `enraged_form` (nahual), `moves` (nuckelavee). Until
  then each is a sound monster on its plain attacks. `trail_hazard` (eitr) is written
  and not yet built.
- **QA key:** Shift+Y (Titivillus only) sets the next new kind down beside the hero.
- **Simulator:** knob `mm_powers` (default 1; 0 is the ablation): the powers run in
  the real code the simulator calls, the Cu-Sith's barks in its world turn, and the
  Blue Men's verse is answered before the fight.
- **Tests:** `tests/test_mm_kinds.py`, `tests/test_mm_kinds_ai1.py`.

## The Tactical Mind (AI-2, 2026-11-20)

Brandon: "extremely advanced AI is acceptable as long as we verify it works and there are no bugs". Every AI pattern was a fixed script: a hobgoblin walked straight at the hero and single file into his corridor. Now a creature with a **mind** weighs its turn. The scoring is pure (`src/tactics.py`, a frozen `View` in, an option out, no random draw, a plain attack wins every tie); `src/tactical_mind.py` builds the View from what the creature senses and carries the choice out with moves that already exist (`packs.hold_step`, `round_path`, `choose_spot`, `bfs`; `senses.step_toward`). Numbers, lines, Bestiary sentences and which kinds think are in `data/minds.json`. Two hooks in `Monster.take_turn` (the aggressive path, after the opener and the alarm; the ranged path, before `_ranged_turn`): `None` means today's code.

**Who thinks** (`tactical_mind.thinks`): a kind listed in `minds.json` `kinds` (or carrying its own `mind` in `monsters.json`), hunting the hero now (`_tracking`: it senses him, no omniscience), within `think_radius` (12), one tile big, not a pack hunter (`packs.in_pack`: the pack's hunt is its brain; a band's goblin thinks). Never: named foes, mini-bosses, seal demons, legends, allies, encounter people, the unicorn, Death, Old Nickel, pets, escorts, called allies; nor a creature asleep, held, frightened, charmed, confused, blinded or babbled (`CANNOT`), broken by its morale (fleeing, at bay, cowed, yielded, bolting, making for its friends), or a thief with a haul. Beasts, vermin and the mindless have no mind (the drilled skeleton warrior and the tsuchigumo, a yokai in a monk's shape, are the lore exceptions).

| Mind | Kinds (by lore) | What it values |
|---|---|---|
| cunning | goblinkin small folk (goblins in a band, kobold leaders, bugbears, gnoll lords), bandits, the psoglav | holds a corridor, waits for friends, its snares, a hurt pet |
| soldier | hobgoblins, orcs, mercenaries, the veteran knight, the sown men, einherjar, skeleton warriors, centaurs | holds a line, changes places, the feint, a doorway |
| trickster | dark elves and drow, the hidden folk, shadows, the kitsune, the rakshasa illusionist, the wisps, the vila, the yuki-onna, the Blue Men, the tsuchigumo | comes round, the dark edge |
| caster | the living hedge-casters (kobold sorcerer, goblin and orc shamans, apprentices, cultists, battle mage, harrow witch, drow mage, nahual) | keeps its distance and casts |

**The options** (each but a plain attack says one line the first time a fight uses it, once a side, again after 60 turns; a line is judged by what the hero could see when the creature decided, so a hold that steps out of sight is still told):
- **Wait at the Mouth** (`hold_choke`): the hero stands where only one of its side can reach him (a corridor). It goes round if there is a way (`packs.round_path`), else holds beyond the mouth out of his sight; out of his sight it keeps its post (`_tm_watch`, read by `senses.notice`) instead of walking in to look. At most `patience` (10) turns, then it comes. Not while it has a clear shot, is hurt, or he is pressed.
- **Wait for Numbers** (`wait_allies`): three to five tiles off, nobody on him yet, a friend coming on a few steps behind: it waits for him.
- **Come Round** (`flank`): a friend is on him: it takes a free tile on his far side (wolves' back-tile rule).
- **Out of Your Light** (`leave_light`, `dark_edge` kinds): in his sight it steps to a tile just beyond his light's reach from which it still sees him (three times a fight); out of it an archer shoots (he cannot see to shoot back), the rest lurk at the edge and strike first, closing and striking in one turn, when he comes within two tiles (once a fight). A brighter light leaves no dark within reach.
- **Hold the Door** (`hold_door`): a hurt soldier backs into a doorway, ten turns at most, only against a hero fighting beside a companion who could flank it, and one it can see.
- **Change Places** (`rotate`, soldiers): the front man under 40% swaps with a fresh soldier behind him (never onto a hazard, never a held one), and rests 6 turns before he may again.
- **Feigned Flight** (`feint`, soldiers of a band, once a band a floor): at a corridor's mouth the front man falls back into the room while two or more wait beside the mouth out of the hero's sight; a hero who steps out is struck by each of them, +2 to hit (`tactical_mind.hit_shift` via `ai_blow`). A hero who knows the kind (`family_lore.knowledge` KNOWN) is told it is a feint.
- **Go for the Weak One** (`focus_pet`, cunning): a pet under 35% within 6 tiles and in sight, the hero above 35%: it goes for the pet (`_focus`; the swipe pass then gives that pet its whole blow). At most half of those that can see the pet (at least one). Never the unicorn, a ridden Bococho, Dad or an escort. When the hero himself is under 35% they press him instead (hold and wait are off).
- **Over Their Own Snares** (`bait`, `knows_traps` kinds): it stands where the hero's straight way to it runs over a known trap or hazard (never his own rewired traps), 8 turns at most; a hidden trap is hinted at, never named. Its paths keep off them when it has another way (`senses.find_path` `avoid`).
- **The cast** (`cast`): a spell (`wards.is_cast`, as Silence means it) in reach with a clear shot, open by the gates (`attack_gates.blocks_attack` through `lanes.usable`). `tactical_mind.choose_cast` picks it (today one at random, as `Monster.attack` does); slice AI-3's `caster_ai.choose` is meant to decide there.

**The Captain's Orders** (`tactical_mind.band_order`): a band's leader gives an order once a turn, kept on `dungeon.band['order']`, while he leads (`tactical_mind.leader_of` / `commands`): alive, able to shout (none of `CANNOT`, not silenced), not broken by his morale (fleeing, at bay, cowed, yielded), hunting the hero, and answered by his band (AI-1's `war_bands.holds_nerve`: a captain who begs leads no one, a babbled follower cannot hear him). A band whose captain cannot lead answers as if he had fallen: no order, no screen, no feint. What he knows of the hero is what he SEES (`senses.sees`: his sight, its reach, invisibility); out of his sight he goes on his last picture of him (`dungeon.band['hero_seen']`), or knows nothing. The orders: `screen` (guards stand between him and the hero and the leader hangs back, before the fight is joined), `charge` (the hero seen under 40% or held: everyone presses; it holds until he is above 60%), `fall_back` (half the band down, once: those well clear gather round him for 6 turns). A new order is shouted (`orders` lines per band in `minds.json`); wax in the ears keeps out the words, not the orders.

**Archers Find a Lane** (`src/lanes.py`, every ranged-AI kind, mind or none, while it is its own master: not confused, blinded, babbled, held, frightened or charmed, and not broken by its morale): each MISSILE (`wards.is_missile`) reaches as its weapon does (an attack's own `range`, else the first word of `ranges.missiles`: longbow 8, Polyphemus's hurled crag 8, crossbow 7, bow 7, a giant's hurled boulder, rock, glacier or whetstone 7, shortbow 6, sling 5, hand crossbow 5, dart 5); every other distance attack (a breath, a gaze, a voice, a spit, a spell) reaches 6, as before; `Monster.attack` never picks one out of reach. A shot blocked by a friend: it steps to a lane (within 3 steps, 3+ tiles from the hero, a clear shot; it likes 4 tiles off, cover and the dark beyond his sight) or holds 4 turns, then comes on. Beside him it steps back when it has a shot from there, at most twice running. With no shot and no lane it comes no nearer than 2 tiles. Healers and summoners that borrow the ranged turn keep beside their friends (the lanes are the ranged pattern's).

**Wait Your Turn** (`senses.step_toward`, every hunter): a way round the creatures in front is taken only if it is at most `queue.slack` (6) steps longer than the straight way; behind one of its own side on the real way it waits `queue.wait` (3) turns with no new search and steps up as soon as the tile is free. It waits once: if the friend is still there, it goes round, and does not queue again until it has moved. It never waits behind a friend that will not move (asleep, held, rooted, frightened, charmed, confused, begging, running, or not hunting the hero), nor behind a pet or a stranger. A hunter that sees the hero with a creature on the straight line between them, already on its way round, keeps to that way (`senses.keeps_way_round`) instead of stepping back into the blocked line each turn, which used to hold it in place for ever. `senses.QUEUE` is the harness's ablation.

**They Learn Your Tricks** (`src/habits.py`): the lesson lives on the witness, a learner (cunning, soldier, trickster) that SAW the hero do it (`_tm_habits`, once a fight: 30 turns apart, remembered 300 turns). It tells its own war-band or pack while they hear it: a mate awake within 12 tiles. A creature of the same family elsewhere on the floor learns nothing, and when the witness dies what it saw dies with it ("leave no one to tell"). The habits: fighting from a narrow way (`choke_fighter`, the hero's melee; at 2 they hold harder and say so), two or more struck by one action of his (`opens_with_area`; at 1 they spread round him; `habits.close_action` at the start of `Game._advance_turn` and `world_over` at its end draw the line, so a worn item's blow in the world's turn, the Boots of Thor's arc, never joins his next action's), a shot from 4+ tiles followed by a step back (`kiter`; at 2 they stop waiting to be shot), a rest with a foe in sight (`rester_near_foes`; at 2 they rush a resting hero). Each habit says its line when it changes their play (and the hero's wounds say "press"). An invisible hero teaches nothing; a pet's deed is not his; a damage-over-time tick is never a blow.

**What the hero is told:** each mind's Bestiary sentence (and the dark edge, the snares, the archer's lane) at KNOWN (`game_render.monster_trait_lines`); tells `mind_cunning`, `mind_soldier`, `mind_trickster`, `mind_caster`, `dark_edge`, `knows_traps`, `band_orders`, last in `order` so a creature's worst power is still said first; the help page's "How the clever ones fight" (`data/ui/monster_ways.json`).

**State** (all in the creature's own `__dict__`, new values each time, every read with a default, so an old save and the simulator's copies need nothing): `_tm_plan` (option, turns left, the hero's tile and turn at the decision; dropped when he has moved more than 2 tiles or 3 turns have passed), `_tm_wait`, `_tm_watch`, `_tm_last`, `_tm_used`, `_tm_hp`, `_tm_edge`, `_tm_door`, `_tm_bait`, `_tm_dark_strike`, `_tm_rotated`, `_tm_feint`, `_tm_feinter`, `_tm_surprise`, `_focus`, `_lane`, `_lane_hold`, `_lane_backs`, `_queue_wait`, `_queue_step`, `_queue_spent`, `_tm_habits` (what it saw the hero do); on the floor `dungeon.band` (`order`, `order_turn`, `fell_back`, `feinted`, `hero_seen`...), `dungeon._tm_said`. A plan commits 2 turns (`commit_turns`) unless the hero comes beside it (only rotate, feint and focus are kept then) or it stops being open. After 20 turns out of touch with the hero its patience and tricks are its own again.

**Measured, then simulated:** `tools/balance/tactics_scenarios.py` sets real kinds on hand-made floors (a room and a corridor, an open room, a group strung out as roused one by one) with a scripted hero (a corridor camper who goes out after a shooter, and an advancer), runs the real `take_turn` with each part on and off, and counts the blows on the hero per creature slain. Its numbers feed `tools/balance/sim_ai2.py` (knobs `tac_mind`, `tac_lanes`, on by default). Tests: `tests/test_tactical_mind.py`.

## Wanderers: the floor's clock (3.5.1)

Brandon, play-testing floor 1: "I just don't think we need a constant stream of monsters... I'd rather have a larger population at first, with complex encounters set up, then a trickle if you hang around TOO LONG, but give the player some time to explore... walking back and forth becomes a massive chore."

Until 3.5.1 a newcomer came every 22 turns from the hero's first turn on a floor, whenever it held fewer than about what it started with (`wander_alive_cap`). Every kill was replaced within 22 turns, and newcomers were half of all floor-1 fights (51%, measured on 24 maps, crossing and back).

`src/wanderers.py` keeps a clock on each floor (`dungeon._wander_clock`) of the turns the hero has spent there. `main._maybe_wander_spawn` ticks it once a world turn; `main._place_wanderer` brings a newcomer in when it is due, if the caps allow.

- **Time to explore.** Nothing new comes for the floor's grace, `floor_curve.wander_grace(tour)` = `WANDER_GRACE_FLAT` (550; 100 until 2026-11-16) + `WANDER_GRACE_PER_TILE` (2) × the floor's explore tour, sized to a kid's real pace (`floor_curve.kid_pace`: 400 + 1.5 a tile, from Brandon's saves, about 700-950 turns on the first floors) with about a third to spare. The tour (`wanderers.explore_tour`, kept on the floor) is the walk of a full explore: from the up stair, the nearest room not yet seen each time, every room (beside its centre when a pool or a statue stands there), then the down stair. Its median is 224 tiles on floor 1, 330 on floor 5 and about 500 from floor 12, so the grace is about 950 turns on floor 1 and 1,550 deep (it was 550 and 1,100, and at his pace Brandon met newcomers on most floors). A thorough explore walks about 1.5 tours; the rest is time to fight and catch your breath. On a maze, where the rooms hold less than half the walkable ground (`wanderers.MAZE_ROOM_SHARE`: the maze floors 10-90 about 5%, the Labyrinth 13%, every other floor 73% or more), the tour also stops once in every 10-tile square of passage (`MAZE_BLOCK`): about 1,200-2,000 tiles, a grace of 3,000-4,500 turns. Its few clearings alone gave some maze floors a tour of 20 tiles and under two minutes' grace in 1,900 tiles of maze (bug bash 3.5.1).
- **The floor stirs.** At `WANDER_WARN_SHARE` (85%) of the grace, one `warning` line says he has been here a long while. When the grace runs out, a `stirs` line says things are coming (`data/senses.json` `wanderers`).
- **A trickle.** The first newcomer comes as the grace runs out. The gap to the next starts at `WANDER_TRICKLE_START` (60 turns) and shortens to `wander_interval(level)` (22 turns to floor 50, 40 at floor 100) over `WANDER_TRICKLE_RAMP` (600) turns (`floor_curve.wander_gap`). So a hero camped on a floor long after he has seen it all meets the old pressure again. Resting is never safe forever.
- **Coming back.** Time spent off a floor settles it by as much, down to one full tour of quiet (at least 100 turns) before the trickle starts over, and the lines may be said again. A gap of 3 turns or less is haste or a stair hop and settles nothing.
- **The floor's own.** The fighting is done by what a floor is made with. The per-room roll's base is 0.62 (was 0.50), `MIN_FLOOR_MONSTERS` is 8 (was 6), and war-bands camp on 55% of floors from floor 1. Floor 1 starts with about 13 monsters (was 10), and 70% of floor-1 maps hold a set piece, a band or a den (was 18%).

The simulator ticks the same clock (`Run.pass_time`, `snap.tour`).

Tests: `tests/test_floor_clock.py`, `tests/test_wanderers_hear_or_roam.py`.

Tests: `tests/test_war_bands.py`.

## AI dispatch (16 patterns)

`take_turn` dispatches on `self.ai_pattern` after the common pre-flight (immobilised, slowed, enrage swap, pack-dependent re-evaluation, morale: `src/morale.py`, the broken creature's run). Dispatch is `if/elif` on string match — the matching chain is in `monster.py` lines ~826-867. **Count by pattern** across 527 monsters (counted 2026-05; there are 574 now):

| pattern | count | dispatch | one-line behaviour |
|---|---|---|---|
| `aggressive` | 332 | fall-through to `_standard_move` after awareness/flee/charge gates (a kind with a mind weighs its turn first: the Tactical Mind) | Approach player greedily, attack when adjacent. The default. |
| `ranged` | 101 | `_spots_player`, the Tactical Mind for a kind with one, then `_ranged_turn` | Shoot from LOS within each missile's reach (`src/lanes.py`: 4-8 by weapon, else 6); a shot blocked by a friend steps to a lane or holds; beside the hero it steps back when it has a shot from there (twice running at most); with no shot and no lane it comes no nearer than 2. Will take a melee swing if cornered. Piercing-ranged monsters fire through intervening allies when blocked. |
| `sessile` | 29 | strikes what is adjacent (or in range, if it has a ranged attack) | Rooted: never walks, even alerted or aggravated (G8, 2026-11-12). Fungal / coral / mimic-adjacent. |
| `ambush` | 23 | lurks; springs within 5 tiles on a hero it can see or touch | Invisible until sprung, then `aggressive`. |
| `hit_and_run` | 17 | `_hit_and_run_turn` (`hunting` → `retreating` → `hiding`) | Asterion-style. Attacks 1-2 times, retreats through phasing walls for 3 turns, then hides 4-6 turns before hunting again. |
| `summoner` | 8 | `_summoner_turn` | Once it has spotted the hero (`_spots_player`), its timer runs (`summon_cooldown`); then, with the hero in reach and sight and fewer than `summon_live_cap` of its summoned standing, it chants a turn (a blow breaks it) and calls (`src/summoning.py`, AI-1), up to `summon_max`; otherwise behaves ranged. Sets `_wants_summon` for `main.py::_spawn_summoner_minion` to resolve. |
| `healer` | 7 | `_healer_turn` | Heals a badly hurt friend of its own side beside it (`src/faction.py`, AI-1: under `heal_below` of its health, the one fighting the hero first) by `heal_amount_pct × max_hp`, then rests `heal_cooldown` turns (needs no sight of the hero). Falls back to ranged / aggressive when nothing to heal, once it has spotted the hero (`_spots_player`). 7 monsters: `orc_priest`, `goblin_warpriest`, `cult_priest`, `viper_priestess`, `plague_witch`, `deep_one_priest`, `hels_handmaid`. |
| `cowardly` | 3 | `_standard_move` with inverted direction | Runs from the player; also the fallback for `pack_dependent` when alone. |
| `dancer` | 2 | `_dancer_turn` | Medusa & Lamia. Approach normally when far; when adjacent, pick a *different* adjacent-to-player tile each turn before striking. Hard to pin without chokepoints. |
| `mimic` | 2 | `_mimic_turn` | Inert until the player steps adjacent; then `_mimic_surprise = True`, pattern flips to `aggressive`, first attack lands at `×1.75` damage. |
| `fenrir_rage` | 1 | `_fenrir_rage_turn` | Fenrir only. Every `rage_interval` turns, gains a rage stack. 5 escalating log messages. At 3+ stacks: speed → 14 (double-move), `attack()` fires every attack per turn (bypasses random choice). `reset_rage()` is called by the Gleipnir binding. |
| `abaddon` | 1 | `_abaddon_turn` | Abaddon only. Aggressive movement + `_wants_locust_spawn` flag every `locust_interval` turns. Game loop reads the flag and spawns `locust_count` `abyssal_locust`s. |
| `seek_locust` | 1 | `_seek_locust_turn` | `heavenly_angel` only. Walks toward the nearest `abyssal_locust`; adjacent → sets `_annihilate_target` for the game loop. Never targets the player. |
| `grid_bug` | 1 | overrides `_move_candidates` to cardinals only | Can only step N/S/E/W, no diagonals. NetHack-grid-bug fossil. |
| `stalker_coward` | 1 | `_stalker_turn` (data `stalker`) | Old Nickel. A false friend two tiles off until the hero rests or is helpless, then a sneak attack three times as hard; after that he never closes in to fight: follows at a few tiles, backs off when approached, strikes only cornered beside the hero; darts in at double speed on a resting, sleeping, paralysed, confused or stunned hero. |

**Total:** 16 dispatch branches (`stalker_coward` added 2026-11-17), all verified against the audit — "all 15 `ai_pattern` values map to real dispatch branches."

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
10. Drain (`ai_blow.after_blow` -> `life_drain.after_blow`, AI-1): a failed save lowers max HP by half the blow (`_life_drained`); CON -1 once a floor only for `drain_con` kinds and named foes; nothing under `drain_resist`. `drain_heals_self` returns a fraction as HP.
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

### Where each kind lives: the monster pass (2026-11-17)

Brandon's rulings 11 ("monsters re-placed deeper + deep kinds: yes", until every tier holds 10-35% of the ordinary kinds) and 12 ("every family in every tier: yes") are baked into the data by `tools/balance/monster_pass_2026_11_17.py`, one table of moves, each with its reason from lore, and nine new deep kinds (`tools/content/monster_pass_new_kinds_2026_11_17.py`). The depth a creature's power belongs to follows the domains (`data/domains.json`): floors 21-40 Medusa's temple (the Greek monsters, the serpent folk, the mid-level killers of D&D standing about CR 4-9), 41-60 the Scorched Deep under Fafnir (fire and earth, the dark elves, and Egypt's dead around Setne's Tomb, floors 45-65), 61-80 Fenrir's rime halls (the Norse powers of Ragnarok: the einherjar, the valkyries, the draugr, Fenrir's whelp, the World Serpent's and Nidhoggr's broods), 81-100 the abyss under Abaddon (Tiamat's eleven monsters, the Titans of Tartarus, Revelation's riders and the princes of Hell). Some kinds that stay on floors 1-20 were re-seated inside them so floors 7-20 keep a full and fair population of their own.

A moved kind keeps its attacks' names, types, riders and deliveries; the pass writes its health at its new floor's median (`floor_curve.target_hp`, so `respawn_by_hp.py` keeps it there), its blows as hard against its new neighbours as against its old ones (the median blow of the kinds near that floor, within 0.85-1.2x), its THAC0 the same distance from its new neighbours' median, its spawn weight no higher than theirs, and its harvest and treasure tiers raised to the new band. The weapon materials were then re-baked to the new monster curve (`tools/balance/weapon_curve.py --write`). `tests/test_tier_distribution.py` holds both rulings.

The nine new kinds: Corpse-Swallower (`hraesvelg_eagle`, birds, floor 72), Rime-Thurs (giants, 70), Kallikantzaros (goblinkin, 68, a pack of three or four), Oni (goblinkin, 84, a band of two or three), Mushmahhu (serpents, 88), Nine-Tailed Fox (`kyubi_kitsune`, shapeshifters, 86), Geryon (legend, 89), Viy (gorgons, 90), Image of the Beast (constructs, 91).

**Known convention trap** (audit P5 / level_manager docstring): `spawn_monsters` skips `rooms[0]`. Both `_spawn_monster_den_extras` and `_populate_hidden_chambers` exploit this by passing `[dummy, target_room]` so the target becomes "room 1" and gets populated. If `spawn_monsters` ever drops the skip-first convention, BOTH call sites must change together.

## Mini-boss planning (`LevelManager._roll_planned_mini_bosses`)

Bands = `(1,20), (21,40), (41,60), (61,80), (81,100)`.

Per band (`level_manager.plan_mini_bosses`, ruling 13, 2026-11-17):
1. Candidates (`band_candidates`): `is_mini_boss` **AND** not `seal_demon_*` **AND** `spawn_chance > 0` **AND** `band_lo ≤ peak_floor ≤ band_hi`. The legendary ones (tag `legendary`) are candidates of their band like the rest; until 2026-11-17 each rolled on its own at 50%, all of them in floors 81-100.
2. FIRST slot (`_MINI_BOSS_FIRST_CHANCE` 1.0): a pick weighted by `spawn_chance`, set on its `peak_floor` or the free floor of its band nearest it (`_free_floor`: the peak, then one below, one above...; never a gate floor, a seal demon's floor or another planned floor).
3. SECOND slot (`_MINI_BOSS_SECOND_CHANCE` 0.30): the same, among the band's candidates not picked.

So a run meets one or two named foes in every band, never none and never three (`tests/test_mini_bosses_by_lore.py`), 6.5 a run besides the seven seals. **Old saves:** a level manager pickled under the old plan (`_plan_version` 1) is planned again on load for the floors not yet reached (`_replan_ahead`): what is behind the hero or already made is kept, and a band he is part-way through takes new foes only up to its fresh count.

**At floor-generate time** (`_try_spawn_mini_boss`): if `self._planned_mini_bosses[level_num]` is set and that id hasn't been placed yet, pick a middle room (not first or last), find a free walkable tile, instantiate — v2.18.0 added the implicit `is_boss` wire via `Monster.__init__`, so a mini-boss now gets boss-immunity automatically without an explicit `mb.is_boss = True` override at this call site. If his whole footprint fits nowhere (a 2 x 2 legend on a maze floor whose clearings the floor's own monsters fill: Surtur on 90, about one run in fourteen), `_carry_mini_boss` plans him on the next floor not yet made, within five, with no gate boss, seal demon or other planned mini-boss (bug bash 3.5.1; he used to be lost for the run).

## Mini-bosses by lore (2026-11-17)

Brandon's ruling 13 (2026-11-16): "mini-bosses with cool unique drops are supposed to be spread through the whole game, maybe one or two every 20 floors; gear they drop should be depth appropriate... why would they all be concentrated at the end game? Use lore to determine weaker vs later bosses." Before: the rolled roster was 3 / 6 / 5 / 7 / 10 by band (the five legendary ones all in 81-100), a run met 1.2 in each of the first four bands (none one run in ten) and about 3.7 in the last, and the drops' tiers ran from 1 to 5 whatever the floor (a tier-5 lion's hide on floor 55, a tier-2 ring on floor 80).

**Seats** (`tools/balance/mini_boss_seats.py`, `SEATS`, with the reason for each): each band is a gate boss's domain, and a foe sits in the band its legend's might belongs to, in lore order inside it: the weaker legend shallower, the mightier nearer the gate. The domain decides between two bands where the might is close (the winter things are Fenrir's frost; Vulcan's son and the jackal of the red desert the scorched caves). Seats stay off the gate floors, the seal floors and the last floor before a gate (19, 39, 59, 79), where common gear is already the next band's tier. The tool writes `peak_floor`, `min_level` (two above the seat, unless a lore floor two to ten above it was written), `harvest_tier` and `treasure.item_tier` (one above the band, at most 5), `treasure.gold` (0.415-0.77 of a floor's income at the seat, as before) and the drop; `mini_boss_bands.py --write` then re-tunes health, blows and THAC0 against the new floor. The field is 6 / 4 / 7 / 7 / 8 rolled foes by band (it was 3 / 6 / 5 / 7 / 10).

**Drops** (`tools/content/mini_boss_drops_2026_11_17.py`): each mini-boss drops one signature piece of its own legend on the kill, of the tier of its band, tier = (floor - 1) // 20 + 1. Each is `plot_locked` (the named-armour ladder keeps its tier; traders refuse it, thieves skip it as a unique) and its `peak_floor` is its foe's seat; a weapon's base is 1.25 times its class's common median there (`rebase_unique_weapons.py`), and body armour and shields keep the named-armour floor of the seat (`unique_armor_ladder_2026_11.dropped_by_mini_boss`). The census counts a drop on its foe's floor (`tier_census._dropped_by_mini_bosses`) and the simulator picks it up (`difficulty_sim._signature_drop`). Tiamat's signature is her boss scroll (the Scroll of Chromatic Doom, tier 5). Easter eggs are left as they were: Old Nickel's Bloomleaf Cloak (tier 2 on floors 1-8) and the Cow King's Horns (tier 3 from the Cow Level, entered from floors 30-39).

| Band | Floor | Mini-boss | Why here (lore) | Signature drop | Tier | Changed |
|---|---|---|---|---|---|---|
| 1 | 6 | Bonnacon | A bull of the bestiaries whose horns cannot hurt anyone; its only weapon is burning dung. The weakest legend there is: the game's first named fight. | Hide Cloak of Greater Elementward I (`armor:cloak:hide:elementward:2`) | 1 | drop tier 2 -> 1 |
| 1 | 9 | Arachne | A mortal weaver changed into a spider by Athena: cursed, not mighty. | Arachne's Silk Cloak (`arachne_silk_cloak`) | 1 | drop tier 2 -> 1 |
| 1 | 12 | Calydonian Boar | A boar, if a huge one, sent by Artemis to ravage Calydon. Atalanta's arrow drew its blood and Meleager's spear ended it: mortal hunters of the generation before Troy (it was floor 27). | Hide of the Calydonian Boar (`calydonian_boar_hide`) | 1 | floor 27 -> 12; new drop |
| 1 | 15 | Lamia | A grieving queen turned child-stealing daemon: a terror of nurseries, not of armies. | The Eyes of Lamia (`eyes_of_lamia`) | 1 | new drop |
| 1 | 17 | Nemean Lion | The first of Heracles' twelve labours, so before the Lernaean Hydra, his second (floor 23): a beast a mortal hero strangled with his arms (it was floor 55). | Hide of the Nemean Lion (`hide_of_nemean_lion`) | 1 | floor 55 -> 17; drop tier 5 -> 1 |
| 1 | 18 | Talos | Hephaestus' bronze guard who ran around Crete three times a day: met at the shore of Minos' island, the last guard before the Labyrinth (it was floor 21). | Bronze Aegis (`bronze_aegis`) | 1 | floor 21 -> 18 |
| 2 | 27 | Polyphemus | Poseidon's son, the shepherd giant of the Odyssey: a man-eater, but beaten with wine and a stake by one mortal. A named giant among the cyclopes of floors 26-30 (new). | Club of Polyphemus (`club_of_polyphemus`) | 2 | new; new drop |
| 2 | 29 | Erlking | Goethe's elf-king of the night mist: a death spirit who takes a child, not a host. | Mantle of the Erlking (`erlking_mantle`) | 2 | drop tier 3 -> 2 |
| 2 | 34 | Camazotz | The death bat of Xibalba's House of Bats: a god's creature in a temple of the dead. | Obsidian Talisman (`obsidian_talisman`) | 2 | drop tier 3 -> 2 |
| 2 | 37 | Echidna | The mother of monsters, Hesiod's kin of the Gorgons, in the deepest part of their temple: her brood is met around her (the Hydra 23, the Chimera 31) and after her (the Sphinx 44). She was floor 24. | Echidna's Fang (`echidna_fang`) | 2 | floor 24 -> 37 |
| 3 | 42 | The Iron Patriarch | A tyrant king sealed in his crypt in his coronation plate, still expecting an audience: a barrow-king of the dragon's caves, a man, not a monster, the least of their legends (kept at 42; on floor 32 his stun-locking hammer killed careful kids in the Monte Carlo). | The Patriarch's Gavel (`patriarchs_gavel`) | 3 | new drop |
| 3 | 43 | Stheno the Gorgon | Medusa's immortal sisters: when Perseus fled with her head they rose and chased him. They come for her killer the floors after hers (they were floor 67). | Brazen Hands of Stheno (`brazen_hands_of_stheno`) | 3 | floor 67 -> 43; new drop |
| 3 | 44 | The Sphinx | The riddler on the road to Thebes, whom the city could not beat for years and Oedipus beat with one answer: a monster of the heroic age, met after Echidna, whose brood Hesiod makes her (kept at 44). | Sphinx's Crown (`sphinx_crown`) | 3 | drop tier 2 -> 3 |
| 3 | 47 | Cacus | Vulcan's fire-breathing son in his smoking cave on the Aventine: the scorched caves are his (he was floor 39). | Vulcan's Brand (`vulcans_brand`) | 3 | floor 39 -> 47 |
| 3 | 50 | Rangda | Bali's widow-witch, queen of the leyaks, who fights the Barong forever and never loses. | Rangda's Keris (`rangdas_keris`) | 3 | new drop |
| 3 | 53 | Set's Jackal | The beast of Set, lord of the red desert and of storms: the scorched place is his country (it was floor 69). | Anubis's Scales (`anubis_scales`) | 3 | floor 69 -> 53; drop tier 2 -> 3 |
| 3 | 58 | Baba Yaga | The iron-toothed witch whose hut walks on chicken legs: older than any kingdom, met at the dragon's door. | Baba Yaga's Iron Mortar (`iron_mortar_wand`) | 3 | floor 60 -> 58; drop tier 4 -> 3 |
| 4 | 62 | The Whispering Crone | A fortune-teller buried alive whose dead come at her call. | The Crone's Burial Veil (`crones_burial_veil`) | 4 | new drop |
| 4 | 66 | Jörmungandr (Juvenile) | Fenrir's own brother, the World Serpent, young. | Serpent Scale Mail (`serpent_scale_mail`) | 4 | drop tier 5 -> 4 |
| 4 | 69 | Wendigo | The winter hunger of the northern forests, whose heart is ice: the frost is its country (it was floor 85). | Wendigo's Fang (`wendigo_fang`) | 4 | floor 85 -> 69; drop tier 5 -> 4 |
| 4 | 74 | The Green Knight | Morgan le Fay's enchanted knight, who keeps his chapel at the turn of the year, in the snow. | The Green Girdle (`green_girdle`) | 4 | drop tier 5 -> 4 |
| 4 | 76 | Wild Hunt Captain | The riders of the winter storm, Wotan's or Herne's: the frost is theirs (he was floor 90). | Hunt Captain's Sword (`hunt_captains_sword`) | 4 | floor 90 -> 76; drop tier 5 -> 4 |
| 4 | 77 | Charybdis | The whirlpool that swallows the sea three times a day, opposite Scylla (74). | Sailor's Amulet (`sailors_amulet`) | 4 | floor 78 -> 77; drop tier 2 -> 4 |
| 4 | 78 | Ymir's Last Spawn | A frost giant of the first morning, before the flood of Ymir's blood: the mightiest of the frost, met at Fenrir's door (it was floor 85). | Vambraces of the First Winter (`vambraces_of_the_first_winter`) | 4 | floor 85 -> 78; drop tier 5 -> 4 |
| 5 | 82 | Ravana's Arm | One arm of Ravana, king of the rakshasas, that did not die with him: a demon's remnant, the least of the abyss. | Ring of Iron Grip (`ring_of_iron_grip`) | 5 | floor 80 -> 82; drop tier 2 -> 5 |
| 5 | 84 | Blood Archon | An older grade of fiend who keeps his ledger in blood. | The Exsanguinating Blade (`exsanguinating_blade`) | 5 | floor 82 -> 84; new drop |
| 5 | 86 | Hrungnir's Ghost | The strongest of the giants, whom only Thor's hammer broke, walking again. | Hrungnir's Stone Shield (`hrungnirs_stone_shield`) | 5 | floor 82 -> 86 |
| 5 | 88 | Tiamat the Five-Headed Dragon Queen | The salt sea of the Enuma Elish, mother of gods and monsters: the abyss itself. | Scroll of Chromatic Doom (`scroll_of_chromatic_doom`) | 5 | floor 85 -> 88 |
| 5 | 90 | Surtur the Fire Giant Lord | The fire giant who burns the world at Ragnarok. | Surtur's Ember Mantle (`mantle_of_muspelheim`) | 5 | kept |
| 5 | 92 | Anansi | The spider who bought every story in the world from Nyame, the Sky God himself, and paid in full: a trickster of the gods' own rank, among the gods and the world's end (kept at 92). | Anansi's Web Cloak (`anansi_web_cloak`) | 5 | kept |
| 5 | 94 | Asmodeus, Prince of Hell | A prince of Hell, the last great fiend before the Pit. | Ruby Rod of Asmodeus (`ruby_rod`) | 5 | floor 93 -> 94 |
| 5 | 96 | Níðhöggr Fragment | The corpse-gnawer at the root of the World Tree, who flies on after Ragnarok: the last thing before the end. | Nidhoggr's Scale (`nidhoggr_scale`) | 5 | floor 95 -> 96 |

**Polyphemus** (new, floor 27): the Cyclops of the Odyssey, a named giant among the cyclopes of floors 26-30. His Olive-Trunk Club stuns and he hurls crags from range; blunt blows are wasted on him, the stake's point is not, and he falls to wine and a blinding (`status_weak` confused and blinded, his `family_affinity.json` kind entry). Family giants (a keystone kind), kin of the cyclopes in the kitchen (Cyclops Mutton Links), size huge, art `assets/tiles/monsters/polyphemus.png` (brief `tools/content/genart/briefs/mini_bosses_2026_11_17.json`), the Seeker's `quest_polyphemus` with its badge.

**Balance** (`tools/balance/monte_carlo.py`, kid model, accuracy 0.95, 100 runs a cell, the same seeds; the simulator now picks up a mini-boss's signature drop, `difficulty_sim._signature_drop`). Wins before and after: mastery 97% and 98%, Dexterity 93% and 95%, committed 19% and 19%, Fianna 92% and 94%, Fluffs 94% and 95%, Corwin 100% and 99%, Cain 98% and 99% (about 3-5 points either way is noise). The kids' runs lost to a mini-boss: 3 of 600 before (all on floors 66-88) and 4 of 600 after, each to a different foe (Polyphemus 27, Echidna 37, Jörmungandr 66, the Green Knight 74); none on an ordinary floor of a mini-boss band beyond the usual. In the side fights (a fresh hero at full health, the foe alone) a mastery kid needs a median 5-6 attacks in every band and loses 15-25% of his health; a committed kid 9-13 attacks. Three foes were re-tuned for their new floors on the way (each with its reason in `mini_boss_bands.py` and `mini_boss_seats.py` `TECHNIQUES`): the Nemean Lion on 17 (10x a floor's health, 16% of a bar a turn: at 14.5x and 25% it killed two careful kids in 115 fights, a blade does nothing to it and an early hero seldom has a club), the Calydonian Boar on 12 (blows 19%), Cacus (12.5x, twice the family's length before and after his move), and Polyphemus' club stuns 15% of the time. The Iron Patriarch was tried on floor 32 and kept on 42: his stunning hammer killed careful kids on 32 even with a one-turn stun.

**The kitchen** (`tools/content/kitchen/mini_boss_kitchen_2026_11_17.py`): the moved foes' parts moved with them; two dishes that no longer span the floors lost their cross-depth flag, and the build was re-run. The Sphinx stays at 44 and Anansi at 92 so the Wisdom stat dishes stay spread across the tiers.

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

**Who.** `tools/balance/mini_boss_bands.py` owns 39 foes (`roster()`): the 27 band mini-bosses (Polyphemus since 2026-11-17) `_roll_planned_mini_bosses` rolls (`is_mini_boss`, `spawn_chance > 0`; Iron Patriarch, Whispering Crone and Blood Archon among them), the 5 legendary wanderers (`legendary` tag) and the 7 seal demons. The gate bosses, the Cow King, Old Nickel and Euryale (Stheno's escort, `spawn_chance` 0) are not in it.

**How a foe is written (LORE, NOT FLOOR).** Real numbers in `data/monsters.json`, written by `mini_boss_bands.py --write` from its `FOES` table:
- `hp`: its health in ordinary monsters of its peak floor (`floor_curve.target_hp`).
- `blows`: what it lands in one turn if every blow hits (the attacks `Monster.attack` fires: the first N of a `multi_attack_count` under the attack count, all of a flurry, else one at random), as a share of a steady cook's health bar there (`floor_curve.health_bar`). At most `BLOWS_CAP` 30% of a bar, and the enraged flurry (`enraged_multi_attack_count`) at most `RAGE_CAP` 45%: no turn is a one-blow death.
- To-hit: `named_thac0` = the armour line (`rebake_thac0.measure_line`, the mean AC a plain hero wears on that floor) + `NAMED_NEED` 6 + the foe's own `aim` (0 for all today). An ordinary monster needs a 10 against that hero; a named foe needs a 6. A big blow that rarely lands is luck; a surer, smaller one is a fight the kid can read, and his armour still takes a point off the roll for every point he wears. `rebake_thac0.py` calls `named_thac0` for these foes, and `respawn_by_hp.apply_stat_fixes` and `tools/content/late_game_monsters_2026_10.py` leave their health and dice to the band tool.
- `HP_CAP`: no foe is tankier than 90% of Abaddon (`test_no_mini_boss_is_tankier_than_abaddon`). The deep legendary ones, Níðhöggr's Fragment and Abyzou reach it first: they are dangerous rather than long.

**The bands** (`BANDS`, checked by `tests/test_mini_boss_bands.py`): band mini-boss hp 7-24 ordinary monsters, blows 5-30% of a bar; legendary 17-24, 18-30%; seal demon 11-19, 14-30%. Where in the band a foe sits was measured foe by foe so the mastery hero needs about six attacks for each (the family is the length of the fight): a foe whose hide, resistances, regeneration or second life turns his usual blows needs less health to last as long (the Green Knight 7.4, Stheno 7.5, Baba Yaga 8.6, Talos 10.6), one he cuts through needs more (Echidna 22.7, the Erlking 20.9). A foe whose technique bites carries fewer dice (the Bonnacon's burning dung, the Wild Hunt Captain's pace, Ravana's paralysing grab). Each `FOES` entry has a line of lore saying why.

**Techniques added** (each also a tell, `data/tells.json` by its effect): Talos's **Red-Hot Hug** (grapple, burning: he heated himself in the fire and hugged his victims) beside his Crush, two blows a turn; Cacus's Fire Breath now burns and his **Breath of Smoke** blinds (Virgil's smoke and darkness; it replaced his Slam); the Sphinx's **Whispered Riddle** (voice, confusion: every sum's numbers swim before they settle; wax in the ears stops it) beside her Rake and Bite, three blows a turn; the Nemean Lion's Claw bleeds (its own claws were the only thing that could cut its hide); the Calydonian Boar charges (`can_charge`, x1.5). The Bonnacon's dung burns a little less often (25%, was 35%): at floor 6 the burn was the whole fight. `combat_lines.json` gives the two new verbs ("Talos hugs you to a red-hot chest", "The Sphinx puts a riddle to you"); a riddle that misses "fails to take hold of you" (`monster._MIND_WORDS`).

**How it was measured.** `tools/balance/mini_boss_fights.py heroes` runs the kid-model simulator (100 runs a profile, mastery, committed, mastery_dex, mastery_mage) and saves each living hero at the start of each foe's floor; `fight` then fights every foe against those heroes from the current data, the way `difficulty_sim.Run._boss_side_fights` does (full health, debuffs cleared, the foe alone, no quest layer), so a retune is measured in a few minutes. Final numbers, 400 fights a foe a profile (median attacks / median share of health lost / deaths):

| Group | Mastery before | Mastery after | Committed before | Committed after | DEX / mage after |
|---|---|---|---|---|---|
| Band (26) | 2 / 4% / 0% | 6 / 25% / 0.2% | 4 / 12% / 0.2% | 12 / 124% / 5% | 7-8 / 30-34% / 0.1-0.4% |
| Legendary (5) | 2 / 0% / 0% | 7 / 14% / 0% | 3 / 6% / 0% | 13 / 178% / 7% | 9 / 21-26% / 0-0.2% |
| Seal demon (7) | 2 / 2% / 0% | 5 / 14% / 0% | 4 / 12% / 0% | 11 / 140% / 2% | 7-8 / 18-21% / 0-0.1% |

Whole runs (100 a profile, kid model, the same seeds before and after): mastery won 91% before and 92% after, mastery_dex 86% and 89%, mastery_mage 89% and 92% (each about 6 points either way), with no mastery death on floors 61-99 in either; committed fell from 9% to 2%, its deaths spread over the named fights it now has to survive (seven seal demons in a row among them).

"Lost" counts what potions and prayers put back during the fight, so a committed kid's 124% is more than a whole bar spent. The deep foes whose blows are fire, cold, poison or drain (Mammon, Samael, Abyzou, Tiamat, Asmodeus, the Wendigo) cost a prepared mastery hero little (7-14%): his resistances halve them and his toughness takes more. That is preparation paying, and an unprepared kid meets the full blow.

**What the simulator does not model** about these foes: summons (the Crone's dead, Tiamat's young dragons, Asmodeus's bone devils), a charge for anything but Asterion (the Boar, the Blood Archon), Charybdis's pull, Asmodeus's blink, Mammon's hunger (`sp_drain`), Euryale beside Stheno (the side fight is Stheno alone), and the hero's own confusion and blindness beyond what they cost the clock (blindness its shorter clock, confusion the wait on every sum for its scrambled numbers to settle; no stumbling, nothing hidden). Heroes wielding the Green Chapel Axe were left out: its returning blow (half of a max-chain blow back on the wielder, uncapped) kills a deep hero outright whatever he fights.

**Old saves.** A mini-boss already set down on a saved floor keeps the numbers it was made with (a `Monster` is pickled whole); every one not yet met uses the new data.

## Multi-tile monster placement

Five monsters declare `footprint: [2, 2]`:

| id | min / peak | spawn path | fits-fallback |
|---|---|---|---|
| `fafnir_dragon` | L58-60 | hand-placed (`_spawn_boss` in `_level_60_lair`) | NW-shift up to 3 tiles |
| `tiamat` | 85 / 88 | the mini-boss plan (`_try_spawn_mini_boss` with `_footprint_fits`) | another room, then any reachable tile, then carried to a later floor (`_carry_mini_boss`) |
| `surtur` | 80 / 90 | the mini-boss plan | same |
| `ymir_last_spawn` | 76 / 78 | the mini-boss plan | same |
| `hrungnirs_ghost` | 80 / 86 | the mini-boss plan | same |

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

Since 2026-11-17 they ride the slots of their own band like every other mini-boss, at a weight of 0.3 (Ymir's Last Spawn in the frost, 61-80; the rest in the abyss): see "Mini-bosses by lore". (Until then each also rolled on its own at 50%.) `surtur`, `ymir_last_spawn`, and `hrungnirs_ghost` are also `[2, 2]` footprint — they rely on `_footprint_fits` to find a 4-tile free pocket.

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
- 2026-11-17 — The monster pass (rulings 11 and 12): 133 kinds moved out of floors 1-20 by their lore, 68 re-seated inside them, 28 moved across tiers in the deep, nine new deep kinds; every family has a kind in every tier and the ordinary kinds are 35 / 30 / 14 / 11 / 10% by tier (were 60 / 16 / 9 / 7 / 7). See "Where each kind lives" above.
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

## Appendix: full mini-boss roster (44)

The 32 rolled ones, with their seats and signature drops, are in the table of "Mini-bosses by lore" above (`tools/balance/mini_boss_seats.py` is the source). The other twelve are placed by hand: the gate floors' `asterion_minotaur` (20) and `medusa_gorgon` (40), the `cow_king` (the Cow Level, entered from floors 30-39), `old_nickel` (one floor of 1-8, the Emberpup's story), `euryale_gorgon` (beside Stheno, her `escort`) and the seven seal demons (83-97, forced). None of the twelve has a `spawn_chance` above 0, so the planner never draws them.

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
