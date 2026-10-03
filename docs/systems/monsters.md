# Monsters

## Status
Shipped and heavily reworked through v2.18.0 (commit `409e15d`, 2026-09-27). The 527-entry catalog, Monster class, AI dispatch, boss levels, and spawn pool are in production. A systems audit landed a wave of P0/P1 fixes in v2.18.0 (`is_boss` JSON wire, 4 orphan legendaries given `spawn_chance`, DeathMonster kwargs, chain-break dead-wire noted). Several dead JSON fields (`harvest_threshold`, `ingredient_id`, `attack_effects`, `mortal_weapon_floor`, `chain_break_on_hit`) survive on disk for pickle compat and because the audit opted to document-rather-than-migrate.

## Code
- `src/monster.py` — the Monster class, `_DEFAULTS`, `__getattr__` back-compat shim, `take_damage`, `attack`, `take_turn` dispatch, 14 AI pattern methods, and `DeathMonster` subclass. 1750 lines.
- `src/monster_classes.py` — `FAMILY_PRIORITY` and `get_monster_family(...)` — maps a monster's `tags` list to a single family label (`dragon`, `demon`, `celestial`, `undead`, `fey`, `aberration`, `construct`, `elemental`, `beast`, `humanoid`, `plant`, `reptile`) for display and family-targeted item effects (dragonslayer gear etc.). First match wins.
- `src/boss_levels.py` — hand-crafted boss floors `L20/40/60/80/100` plus `COW_LEVEL=999`. One static map per level with hand-placed stairs, pillars/altars/ice patches, and a single `_spawn_boss(dungeon, boss_id, boss_room)` placement with NW-shift fallback for multi-tile bosses.
- `src/level_manager.py` — floor-generation front door. Pre-rolls planned mini-bosses at run start, forces seal-demon spawns on `L83/85/87/89/91/93/97`, and routes boss floors through `boss_levels.generate_boss_level`.
- `src/dungeon.py::_build_spawn_pool` (line 1230), `_footprint_fits`, `_spawn_one_in_room`, `spawn_monsters`, `populate_floor` — the procedural pool and placement.
- `src/game_combat.py::_drop_treasure`, `_spawn_treasure_item`, `_spawn_archer_ammo`, `_spawn_boss_scroll`, `_spawn_unique_item`, `_make_corpse` — death-side loot and corpse creation.
- `src/combat.py::_damage_multiplier` (line 833) — the elemental resistance/weakness table.
- `src/hero_specials.py::is_boss_or_huge` (line 19) — the `boss_immune` gate used by charm / paralyze / sleep / confuse / immobilize.
- `src/geom.py` — footprint helpers (`is_adjacent`, `occupied_tiles`, `all_occupied_tiles`, `monster_at_tile`) that handle multi-tile bosses correctly; the Monster class routes through these rather than comparing `(m.x, m.y)` directly.

## Data
- `data/monsters.json` — 527 monster definitions keyed by id. 28,712 lines (every monster is a top-level key with `name`, `symbol`, `color`, `hp`, `attacks`, `ai_pattern`, …).

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

### "527 monsters" without 527 classes
Every monster is an instance of the single `Monster` class. Behavioural differences come from JSON fields — `ai_pattern` picks a dispatch branch, flags like `can_charge` / `can_phase_blink` / `prefers_flank` compose on top of it, and status/damage interactions come from the `attacks[]` and `resistances`/`weaknesses`/`tags` arrays. `monster_classes.py` is NOT an OO hierarchy; it's a tag → family lookup for display and item effects.

### Bell-curve spawn, no hard tiers
`_build_spawn_pool(level)` loops over every monster definition with `peak_weight > 0` and `min_level <= level` and computes a Gaussian weight at `distance = level - peak_floor` with sigma `= spread`. A monster appears everywhere its bell has mass; dropouts (bell < 0.005) fall out entirely rather than clamping to a floor. The lore-floor `min_level` is still a hard gate (seal demons don't appear on L1), but there's no `max_level` — late peaks simply have thin tails into the shallows and vice versa. This replaces an older min/max-level clamp that produced "all giant rats on floors 1-5, zero giant rats ever again."

### `peak_weight = 0` means "not in the random pool"
Bosses, seal demons, forced quest spawns, and the four orphan legendaries carry `peak_weight: 0`. They are placed by `level_manager` / `boss_levels` / mystery/encounter paths, never from `_build_spawn_pool`. The field is overloaded: `peak_weight > 0` means "procedurally spawnable at depth"; `peak_weight == 0` means "someone else places this."

### Mini-boss PRE-ROLLING
On run start, `LevelManager.__init__` calls `_roll_planned_mini_bosses()`, which iterates five 20-floor bands (`1-20`, `21-40`, `41-60`, `61-80`, `81-100`) and in each band fills a primary slot (90% chance) and a secondary slot (30% chance). Each slot picks weighted by `spawn_chance`. Expected total per 100-floor run: 5 × 1.2 = **6 mini-bosses**, range 4-8. The placement floor is the chosen mini-boss's `peak_floor` (shifted ±1 if it collides with a boss floor or a planned slot). This replaces first-eligible-wins greedy placement — now every band member has weighted odds every run.

### Seal demons are FORCED, not rolled
`_SEAL_DEMON_LEVELS = {83, 85, 87, 89, 91, 93, 97}` → 7 fixed seal-demon ids. `_try_spawn_seal_demon` runs after mini-boss pre-rolling, is-mini-boss aware (the pre-roller ignores `seal_demon_*` ids), and guarantees placement. Each seal-demon kill is tracked in `game.seals_broken`; at 7/7 the game logs the "way to the Pit stands open" chronicle entry.

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
| `name` | str | yes | Display name. Lowercase for common monsters (`"giant rat"`), Title Case + descriptor for bosses (`"Fafnir the Dragon"`). |
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
| `thac0` | int | default `max(-10, 20 - min_level)` | AD&D-style "to-hit AC 0." Lower is more accurate. Low-tier monsters start at 17-20; endgame bosses hit `-16` to `-20`. |

### Boss / role flags

| field | type | notes |
|---|---|---|
| `is_boss` | bool | **Read from JSON since v2.18.0.** Grants boss-immunity to charm/paralyze/sleep/confuse via `hero_specials.is_boss_or_huge`. Also lifts `min_hit_chance` from 5% to 25%. Carried by: `abaddon_destroyer`, the 7 `seal_demon_*`, `iron_patriarch`, `whispering_crone`, `blood_archon`. **Fallback:** `max_hp > 500` also counts as boss, regardless of this flag — the hand-crafted boss-level `_spawn_boss` additionally forces `boss.is_boss = True` after construction. |
| `is_mini_boss` | bool | Candidate for the pre-rolled mini-boss slot system. 36 monsters carry this flag; `_roll_planned_mini_bosses` filters out `seal_demon_*` (forced path) and `spawn_chance <= 0`. **Known overlap:** `blood_archon` + the 7 seal demons carry BOTH `is_boss` and `is_mini_boss` — audited as a conflict P4, kept as-is. |
| `is_seal_demon` | bool | 7 monsters. On death, `game_combat._drop_treasure` adds the corresponding seal to `game.seals_broken` and logs chronicle text. 7/7 opens the Abyss narrative. |
| `is_allied` | bool | Allied monster (currently only `heavenly_angel`). Does not attack the player; dispatched to `seek_locust` AI. |
| `boss_immune` | — | NOT a Monster field; this is a flag on `hero_specials` entries declaring "my effect should skip bosses." The monster side is `is_boss` / `is_boss_or_huge`. |

### AI shape

| field | type | notes |
|---|---|---|
| `ai_pattern` | str | One of 15 values — see §"AI dispatch" below. Default `aggressive`. |
| `perception_range` | int | default 8 | Chebyshev detection radius. Once a monster spots the player, `_aware = True` sticks for the floor's lifetime. `passive_silent_walk` (Hand of Glory) halves perception against the wearer. |
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
| `dragon_scales` | float | default 0 | Fraction of damage absorbed in `combat.py`'s melee pipeline. `fafnir_dragon` 0.8. |

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

An `attacks[]` is a list of attack dicts. One is picked each turn (`random.choice`), with ranged-word heuristics overriding when `ai_pattern == 'ranged'` and the player is non-adjacent.

| attack field | type | notes |
|---|---|---|
| `name` | str | Display name. Underscore-to-space for message rendering. Ranged routing scans the lowercased name for words like `shoot`, `arrow`, `bolt`, `spit`, `hurl`, `volley`, `ray`, `blast`, `breath`, `spike`, `gaze`, `song`, `wail`, `charm`, `psionic`, `cast`, `bow`, `sling`, `javelin`, `spore`, `shock`, `hex` → treats the attack as ranged. |
| `damage` | str (dice) | Dice notation. |
| `type` | str | Damage type. Known values: `acid`, `blunt`, `cold`, `drain`, `fire`, `holy`, `lightning`, `magic`, `necrotic`, `physical`, `pierce`, `poison`, `psionic`, `shadow`, `slash`. **`psionic`** is NOT in `_damage_multiplier`'s set — treated as `1.0` unresistable (audit P5). |
| `ranged` | bool | Optional explicit ranged flag. |
| `piercing` | bool | Optional — allows the attack to shoot through intervening allied monsters (sets `_piercing_collateral` on this monster for the game loop to resolve). |
| `effect` | str | Status effect to apply on hit. One of 17 ids: `bleeding`, `blinded`, `burning`, `confused`, `cursed`, `diseased`, `feared`, `frozen`, `hallucinating`, `paralyzed`, `poisoned`, `silenced`, `sleeping`, `slowed`, `stunned`, `teleportitis`, `weakened`. All 17 verified in `status_effects.py`. |
| `effect_chance` | float | default 0.30 | Probability of attempting the effect. |
| `effect_duration` | str or int | default 5 | Dice or int, parsed by `dice.roll_duration`. |
| `effect_save_dc` | int | default `min(18, 12 + min_level // 7)` | DC vs the player's saving-throw stat. |
| `subtype` | str | Occasionally present — informational, not read by combat. |

**Multi-attack vs multi-type.** A monster has ONE `attacks[]` list; `multi_attack_count` chooses how many to fire per turn in sequence, with their own THAC0 rolls and damage dice. `_fenrir_multi_attack(player, attack_limit=N)` is the central multi-attack path — it skips attack selection and fires the first N (or all when limit = 0).

### Resistance / weakness

- `resistances: [str]` — damage types that get `×0.5`.
- `weaknesses: [str]` — damage types that get `×1.5`.
- `base_resistances: [str]` — Abaddon-only, used while the locust-ring quest step is active.

`combat._damage_multiplier` picks the BEST multiplier across the attack's damage types (a slash+pierce weapon vs a slash-resistant pierce-weak monster rolls 1.5). Material-driven weaknesses are stacked on top from `_MATERIAL_EFFECTIVE_AGAINST` (silver vs undead/demon, cold-iron vs fey — the material system is the authoritative driver; a legacy hardcoded fallback keeps the old silver/iron rules alive for monsters pre-dating the material refactor).

**Known resistance types across all monsters** (15): `acid`, `blunt`, `cold`, `drain`, `fire`, `holy`, `lightning`, `magic`, `necrotic`, `pain`, `pierce`, `poison`, `shadow`, `slash`.

**Known weakness types** (14): `acid`, `blunt`, `cold`, `divine`, `drain`, `fire`, `holy`, `iron`, `lightning`, `magic`, `necrotic`, `pierce`, `shadow`, `slash` — plus `silver`/`iron` injected by the fallback for `undead`/`demon`/`fey` tags.

### Tags

A free-form list. Primary purpose: `monster_classes.get_monster_family` returns the first match from `FAMILY_PRIORITY` (`dragon`, `demon`, `celestial`, `undead`, `fey`, `aberration`, `construct`, `elemental`, `beast`, `humanoid`, `plant`, `reptile`). Secondary: `alert_all_tag` reads tags for wider-radius alert; `pack_dependent` reads tags to find pack allies; material-weakness lookup reads tags.

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
| `item_chance` | float | 0..1 chance to drop a procedural common from `_spawn_treasure_item`. |
| `item_tier` | int | 1-5. `_spawn_treasure_item` scales the "effective floor" as `max(1, tier * 5)` and rolls (30% weapon, 10% armor, 10% shield, 50% magic-pool from `accessory`/`wand`/`scroll`/`potion`/`ammo`) excluding uniques. **Cap:** 5. The pre-v2.18.0 catalog had 7 dragon-tier monsters with `item_tier` 6-10 (audit P4); those were clamped to 5 in the v2.18.0 pass. Current catalog is 1=61, 2=99, 3=151, 4=116, 5=100. |
| `unique_drop_id` | str | Mini-boss fixed drop — looked up by id in the unique-item pools. 20 monsters have one (Talos → `bronze_aegis`, Echidna → `echidna_fang`, Camazotz → `obsidian_talisman`, Cacus → `vulcans_brand`, The Sphinx → `sphinx_crown`, Baba Yaga → `iron_mortar_wand`, Set's Jackal → `anubis_scales`, Charybdis → `sailor's_amulet`, Ravana's Arm → `ring_of_iron_grip`, Wendigo → `wendigo_fang`, Wild Hunt Captain → `hunt_captains_sword`, each of the 7 seal demons → `seal_of_*`, …). |
| `boss_scroll_id` | str | Fafnir / Abaddon style — a one-shot scroll of the hoard / abyss. |
| `ammo_drop` | dict | Archer monsters carry quivers. 8 archers use this: `skeletal_archer`, `bone_archer`, `drow_warrior`, `orc_archer`, `goblin_sniper`, `gnoll_archer`, `bandit_archer`, `shadow_archer`. |

### Harvest

- `harvest_tier` (int, default 1) — 1-5. Threaded into the `Corpse` and read at harvest time (`food_system`). The actual prime-cut dropped is looked up by `monster.kind` in `data/prime_cuts.json`. See [food_system](food_system.md).
- `harvest_threshold` — **DEAD JSON field.** Still populated on all 527 monsters, still read into `Monster.__init__` and threaded onto `Corpse` for pickle compat, but no code consumes it. Harvest v4 (2026-08-06) is one-question, threshold=1 unconditionally. `bones.py:148` and 4 `game_encounters.py` sites set `99` as "unharvestable hint" — no effect.
- `ingredient_id` — **DEAD JSON field** on 525/527 monsters. Harvest v4 resolves the drop via `prime_cuts.json`, not this field. The old-scheme id (`rat_meat`, `goblin_flesh`, `insect_carapace`, `spectral_essence`, …) is still written to disk. **Known downstream rot:** `game_render.py::_draw_bestiary_page` at `id_level >= 2` calls `load_ingredient_for(subject.ingredient_id)` and gets `None` — the bestiary "Ingredient:" / "Solo cook:" lines never render for these monsters (audit P3).

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

## AI dispatch (15 patterns)

`take_turn` dispatches on `self.ai_pattern` after the common pre-flight (immobilised, slowed, enrage swap, pack-dependent re-evaluation, flee-when-hurt flag). Dispatch is `if/elif` on string match — the matching chain is in `monster.py` lines ~826-867. **Count by pattern** across 527 monsters:

| pattern | count | dispatch | one-line behaviour |
|---|---|---|---|
| `aggressive` | 332 | fall-through to `_standard_move` after awareness/flee/charge gates | Approach player greedily, attack when adjacent. The default. |
| `ranged` | 101 | `_ranged_turn` | Shoot from LOS at distance 2-6, retreat if too close, approach if too far. Will take a melee swing if cornered. Piercing-ranged monsters fire through intervening allies when blocked. |
| `sessile` | 29 | returns False immediately | Rooted — only responds if `_alerted` or player is `aggravated` (treated as aggressive). Fungal / coral / mimic-adjacent. |
| `ambush` | 23 | lurks at `dist > 5`, flips to `aggressive` once sprung | Invisible until player closes within 5 tiles. |
| `hit_and_run` | 17 | `_hit_and_run_turn` (`hunting` → `retreating` → `hiding`) | Asterion-style. Attacks 1-2 times, retreats through phasing walls for 3 turns, then hides 4-6 turns before hunting again. |
| `summoner` | 8 | `_summoner_turn` | Spawns a minion every `summon_cooldown` turns up to `summon_max`, otherwise behaves ranged. Sets `_wants_summon` for `main.py::_spawn_summoner_minion` to resolve. |
| `healer` | 6 | `_healer_turn` | Heals the most-damaged adjacent same-kind/tag ally by `heal_amount_pct × max_hp`. Falls back to ranged / aggressive when nothing to heal. 6 monsters: `orc_priest`, `goblin_warpriest`, `cult_priest`, `viper_priestess`, `plague_witch`, `deep_one_priest`. |
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
6. THAC0 roll: `d20 >= thac0 - player_ac` hits, `nat 1` always misses, `nat 20` always hits, `min_hit_chance` (25% boss / 5% regular) can save a numerical miss.
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
- `populate_floor(rooms, level, dungeon, occupancy)` — rolls EVERY room independently with per-room probability `occupancy` (0.50 shallow → 0.95 deep). This is the baseline for a floor; packs/dens/zoos cluster intentionally on top. Guarantees at least one monster on any non-empty floor.

The baseline occupancy comes from `LevelManager.generate` as `density = min(0.50 + level_num / 130, 0.95)`.

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

`_try_spawn_seal_demon` runs AFTER `_try_spawn_mini_boss` on every procedural floor. Idempotent via `self._placed_mini_bosses`. Each kill calls `game_combat._handle_death` → adds the matching seal id to `game.seals_broken`, logs chronicle, at 7/7 triggers the "ALL SEVEN SEALS ARE BROKEN" narrative pulse.

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
1. `_make_corpse(monster)` — builds a `Corpse` with `harvest_tier`, `harvest_threshold`, `ingredient_id`, `lore`, and a `monster_def` dict carrying `hp`/`thac0`/`attacks`/`resistances`/`weaknesses`/`speed`/`tags`/`peak_floor`. Auto-identifies if `monster.kind` is in `player.lore_known_monster_ids`.
2. `_drop_treasure(monster)`:
   - Roll `gold` in `treasure.gold` range → `add_gold_to_tile` → "drops N gold" message.
   - Roll `item_chance` → `_spawn_treasure_item(x, y, item_tier)` (common pool, excludes uniques; `effective_floor = max(1, tier * 5)`).
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
- **Food system** — `game_combat._make_corpse` threads `harvest_tier`, `monster.kind`, `monster_def` tags onto the `Corpse`. `food_system.harvest_corpse` resolves the prime cut by `monster.kind` in `data/prime_cuts.json`.
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
