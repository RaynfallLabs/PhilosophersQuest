# Progression

**Status:** v2.18.0 (shipped 2026-10-02)
**Code:** `src/quirk_system.py` (1633 lines), `src/hero_specials.py` (997 lines), `src/welcome_screen.py` (997 lines)
**Data:** build dicts + hero tables are in-code (no JSON); `player.quirk_progress`, `player.unlocked_quirks`, `player.power_uses`, `player.power_cooldowns`, `player.hero_passives`, `player.hero_specials`, `player.hero_special_cooldowns` persist in the save pickle.
**Related docs:** [combat](combat.md), [items](items.md), [quests_mysteries](quests_mysteries.md), [save_bonus](save_bonus.md), [status_effects](status_effects.md), [quiz_engine](quiz_engine.md)

## Purpose
Progression is everything that makes a run richer after turn 1 that isn't an item on the ground or a floor transition. It covers three parallel layers that stack on top of the player's base build:

1. **Quirks** — ~100 named Bofuri-style traits unlocked by playing in a specific way (not by XP). Each is a one-shot threshold on a quirk-progress counter maintained by the `QuirkSystem` dispatcher. Rewards are either a permanent stat/effect bump or an `[ACTIVE POWER]` on the V-menu.
2. **Hero specials** — one or more AI-escalator-chain active abilities (plus optional cooldown) attached to a specific secret build. Dispatched through `hero_specials._DISPATCH` by effect id.
3. **Hero passives** — set-of-strings on `player.hero_passives`; checked at hook sites in `combat.py`, `player.py`, `monster.py`, `game_menus.py`. One or more per build; several builds carry only passives.

Secret builds are the harness that bundles the above with a themed starting kit, a sprite, a stat spread, and a chronicle journal entry. The build itself isn't a mechanic — it's the vehicle for the hero's specials + passives, with a few metadata flags (`_immortal`, `_qa_tools`, `_elder_blood`) that light up extra once-per-run or once-per-floor powers.

## Design intent
A run gets more interesting over time without granting bigger numbers at a predictable rate. The quirk layer is Bofuri in intent: do something *unusual* 15 times and you earn a trait that rewards that unusual thing. Nobody chases quirks on the critical path — you stumble into them because you played oddly, and the unlock popup is the moment the game surprises you. The hero layer is at the other end: it's chosen explicitly at the welcome screen (and rewards a kid for *knowing* the hero's name).

**Why both?** Hero specials are chosen with high intention and arrive on turn 1. Quirks arrive late, by accident, and the ones a particular run earns are a fingerprint of the player's style — a wanderer gets Ahasverus + Iron Ration + Metabolic + Ancestral Memory, a sorcerer gets Merlin + Tesla + Morgan + Arcane Surge, a tanky brawler gets Boudicca + Spartacus + Darwin + Leonidas. Two players with identical builds finish with different stat blocks.

**Rewards are either permanent or power-ish, never flat damage.** Stat bumps (+1 STR / +2 WIS / +3 CON) and permanent status effects (telepathy, regeneration, levitation, warning) make up most of the trait rewards. Active powers are limited-use (1-5 uses, no cooldown) or cooldown-based — intentionally rare so a quirk unlock is still a decision when to burn it, not a free damage spike.

**Quirks that promised untimed-subject timer bonuses now bump the right stat instead.** The engine lost per-subject timers in May 2026 (only math is timed; see `quiz_engine.md`). 16 non-math timer quirks and 3 all-subject timer quirks still carry their original `_timer_bonus` call, but the helper now also grants `+1 WIS / +1 PER / +1 INT / +1 CON` depending on the subject so the reward still has teeth. The player-facing parenthetical that mentions "if the subject ever becomes timed" is SYSTEMS_AUDIT §8 P4 (text drift) — pending copy sweep.

**Secret builds are intentional fun; do not demystify them.** The welcome screen's gold `[*] SECRET BUILD ACTIVE!` flare is a deliberate reward moment for a kid typing in a hero name. Builds are not listed, labeled by alias, or hinted at anywhere in the UI. See `feedback_secret_build_is_fun.md`.

## Data model / schema

### Quirk schema

A quirk is defined across six parallel dicts in `quirk_system.py`, all keyed by the quirk id string:

| Dict                 | Role                                                              |
|----------------------|-------------------------------------------------------------------|
| `_QUIRK_NAMES`       | id → display name (e.g. `'mithridates'` → "The Mithridates Protocol") |
| `_QUIRK_FLAVOR`      | id → flavor quote shown on unlock                                 |
| `_QUIRK_TRIGGER`     | id → "what the player did" sentence (second-person, past tense)   |
| `_QUIRK_EFFECTS`     | id → "what the reward does" sentence (shown on unlock + in V-menu)|
| `_QUIRK_PROGRESS`    | id → `(progress_key, threshold, is_set)` for the progress bar     |
| `_QUIRK_ORDER`       | ordered id list for the per-run quirk screen                      |
| `_ACTIVE_POWER_DEFS` | id → `{'uses', 'cooldown', 'label', 'desc'}` for active-power quirks |

The progress key points at a counter living on `player.quirk_progress`. `is_set=True` means the counter is actually a Python `set` (distinct-X-count). A `threshold = -1` marks a quirk whose unlock depends on more than one counter (Archimedes = sci ≥ 50 AND eco ≥ 50; Hypatia = math ≥ 50 AND sci ≥ 50; Ragnarok = L100 arrival at ≤ 10 HP). Those special cases are handled inline in `get_quirk_progress`.

### Trigger → quirk dispatcher (`QuirkSystem.on_*`)

The `QuirkSystem` class owns the full trigger surface. Every game event funnels through one of its `on_*` methods; each method does its own counter bump + threshold check and calls `_award(...)` (or `_award_power(...)` for V-menu actives) exactly once. Mastery of the quirk list is a side effect of walking this table:

| Dispatcher               | Called from                                                   |
|--------------------------|---------------------------------------------------------------|
| `on_wait(near_monsters)` | `.`-wait command (main.py)                                    |
| `on_move()`              | successful tile step (main.py)                                |
| `on_stair_use(level)`    | stair up/down (main.py)                                       |
| `on_floor_entered(level)`| after `_change_level`                                         |
| `on_stairs_taken_fast()` | stair use within 30 turns of floor entry                      |
| `on_floor_explored(pct)` | every FOV refresh; fires once per 99%+-explored dungeon_level |
| `on_quiz_answer(...)`    | per-individual-question hook from quiz_engine                 |
| `on_quiz_complete(...)`  | per-session hook from quiz_engine                             |
| `on_kill(...)`           | monster death (combat.py)                                     |
| `on_take_damage(...)`    | `player.take_damage` consumer                                 |
| `on_trap_triggered(t)`   | container trap fired                                          |
| `on_lockpick_fail(c,l)`  | lockpick-quiz fail on trapped chest                           |
| `on_lockpick_success()`  | lockpick-quiz pass                                            |
| `on_harvest(...)`        | post-harvest, success/fail + monster poisons                  |
| `on_food_eaten(...)`     | cook v2 pass path                                             |
| `on_potion_drunk()`      | potion consumer                                               |
| `on_scroll_read(...)`    | scroll consumer                                               |
| `on_wand_zapped(...)`    | wand consumer                                                 |
| `on_item_equipped(...)`  | equip hook                                                    |
| `on_item_unequipped(...)`| unequip hook                                                  |
| `on_prayer(hp_pct)`      | prayer success                                                |
| `on_recall_lore()`       | recall-lore use                                               |
| `on_spell_cast(hp_pct)`  | spell cast success                                            |
| `on_examine_used()`      | examine-menu open                                             |
| `on_status_applied(...)` | status effect gain                                            |
| `on_disease_drain(s,a)`  | disease tick that drains a stat                               |
| `on_turn()`              | every `advance_turn` — the per-turn tracker                   |
| `on_item_identified(id)` | post-identify (quiz-pass path)                                |
| `on_combat_started()`    | combat initiation (used by Orpheus streak reset)              |
| `on_status_reflected()`  | reflect-status fires (Perseus)                                |
| `on_teleport()`          | any teleport (wand / teleportitis / Elder Blood blink)        |

### Award effect shape

Rewards fall into a small number of families, applied via a tiny lambda or named helper:

| Family                   | Shape of apply_fn                                           | Example quirks                                            |
|--------------------------|-------------------------------------------------------------|-----------------------------------------------------------|
| `stat_bump`              | `pl.apply_stat_bonus(STAT, N)`                              | Tiresias (PER +2), Boudicca (STR +2), Darwin (CON +3), Caesar (all +1) |
| `perm_effect`            | `pl.add_effect(name, -1)` (duration -1 = permanent)         | Odin (telepathy), Prometheus (regenerating), Siegfried (magic_resist), Mithridates (poison_resist), Buddha (displacement), Ahasverus (searching), Job (levitating), Cerberus (warning), Paracelsus (drain_resist), Cu Chulainn (fear_immune) |
| `save_bonus_all`         | `pl.quirk_progress['save_bonus_all'] = N`                   | Perseus (+2 to all saves)                                 |
| `flag_bonus`             | `pl.quirk_progress[FLAG] = value`                           | Beowulf (+5 unarmed base), Hermes (double haste duration), Wanderlust (SP drain halved), Musashi (chain-1 damage uses mid-multiplier), Orpheus (floor-start slow), Norns (halve recall-lore CD), Fisher King (halve prayer CD), Jormungandr (+1 max_chain on named weapon), Hephaestus (-1 equip threshold on named slot), Thor (+2 enchant on named weapon), Persephone (half SP/HP on ruined meals) |
| `timer_bonus(subj, N)`   | `pl.quiz_timer_bonuses[subj] += N` **plus** `+N/3` to subject-flavored stat | Scheherazade, Merlin, Shakespeare, Tesla, De Medici, Sisyphus, Penelope, Ibn Battuta, Shiva, Confucius, Kali, Asclepius, Dionysus, Apollo, Ramanujan, Athena, Circe, Galileo (16 total; see below) |
| `all_timer_bonus(N)`     | +N on all 10 subjects **plus** `+N WIS`                     | Sibyl, Zoroaster, Machiavelli                             |
| `[POWER x N]`            | `_award_power` seeds `power_uses[id]=N` / `power_cooldowns[id]=0` and the V-menu dispatcher | 26 active-power quirks (see §Active powers) |

### Progress tracker fields on `player.quirk_progress`

The dict stores counters, sets, bools, and nested dicts side-by-side. A few examples:

- Simple counter: `'math_correct_run': 500` (Ramanujan unlock), `'tile_moves': 15000` (Ahasverus), `'ruined_meals': 15` (Tantalus).
- Set-of-distinct-X: `'enkidu_harvested': {'rat', 'bat', 'wyrm', ...}` (20 species = Enkidu), `'scheherazade_scrolls': {...}` (12 scroll ids = Scheherazade).
- Dict-of-counts (per-key max): `'thor_weapon_combats': {'longsword_iron': 23}` (30 same-weapon combats = Thor), `'kali_kills': {'kobold': 100, ...}` (100 same-kind kills = Kali).
- Episode-latch: `'rasputin_was_low': True` (held across turns until HP rises above 5%; prevents a single hit counting repeatedly).
- Floor-set: `'leonidas_kill_floors': {3, 7, 12, ...}` (30 distinct = Leonidas).
- Behavior flag: `'wanderlust_active': True`, `'persephone_active': True`, `'musashi_active': True` — read by combat / food / damage code paths.

Dict/set states are picklable; the engine does not care if `_setstate_` restores an old shape — `_set_add` and `_dict_inc` are defensive and reseed the field if it comes back as the wrong type.

### Hero specials — active ability schema

`HERO_SPECIALS` maps a lowercased build name to **either** a single special dict or a list of them (Ash Williams has 3), or `None` (passive-only builds like Geralt, Ciri, Nikola Tesla, Miyamoto Musashi). A single entry shape:

```python
{
    'id':           'hero_hermetic_step',   # unique power id (prefix 'hero_')
    'name':         'Hermetic Step',        # V-menu label
    'desc':         'Short-range teleport…',# V-menu subtitle
    'cooldown':     200,                    # turns until reusable
    'effect':       'teleport_self',        # key into _DISPATCH
    'boss_immune':  True,                   # (optional) skip bosses in status apply
    'self_cost_hp': 5,                      # (optional) HP paid on activation
    'ammo_id':      'shotgun_shell',        # (optional, gain_ammo only)
    'tier_effects': {0: {...}, 1: {...}, 2: {...}, 3: {...}, 4: {...}, 5: {...}},
}
```

`tier_effects[chain]` is the parameter dict for the effect handler at that chain depth. Chain 0 is "fizzle" (printed warning line, no mechanical effect). Chain 5 is the signature payoff. The quiz is always `escalator_chain` + `subject='ai'` + `tier=1` + `max_chain=5`.

### Hero passives — set of strings

`HERO_PASSIVES` is a flat `dict[build_name -> list[str]]`. On game start, `main.py:2024` copies the list into `player.hero_passives: set[str]`. Each string is a feature flag that one specific hook site in combat/player/monster reads via `in hero_passives`.

### Journal entries

`HERO_JOURNAL[build_name] -> str`. A short in-character opening paragraph logged to the chronicle at game start. Not mechanical — only flavor. Dad, Titivillus, and Corwin have journal entries; the "fluff" builds without hero specials still get a journal line.

### Secret-build dict shape (`welcome_screen.py::SECRET_BUILDS`)

```python
"<lowercased name>": {
    # Base stats (override player defaults; omitted = 10)
    "STR": 14, "CON": 12, "DEX": 16, "INT": 10, "WIS": 10, "PER": 10,

    # Metadata (underscore-prefixed; stat loop skips)
    "_sprite":          "player_hermes",             # assets/tiles/env/<_sprite>.png
    "_start_weapon":    ("rapier", "iron"),          # id, OR (type, material)
    "_start_melee":     "chainsaw_prosthetic",       # fills melee slot
    "_start_shield":    ("light_wooden", "oak"),
    "_start_armor":     "hermes_sandals_early",
    "_start_wand":      "wand_of_force_dart",
    "_start_book":      "spellbook_magic_dart",
    "_start_accessory": "ring_of_intellect",
    "_start_extra_acc": ["dreamspun_sketchbook"],    # list of extras
    "_start_ammo":      "iron_arrow",
    "_start_spells":    ["sign_aard", "sign_igni"],  # pre-known spells
    "_start_potions":   ["potion_of_healing"],
    "_start_soul_spheres": 4,                        # count of starting spheres
    "_start_unusual_sphere": True,                   # one wildcard sphere
    "_no_dagger":       True,                        # skip default iron_dagger
    "_equip_armor":     True,                        # auto-equip _start_armor
    "_lock_melee":      True,                        # welded melee (Ash's chainsaw)
    "_immortal":        True,                        # cannot die (Dad only)
    "_qa_tools":        True,                        # Shift+I / Shift+W dev tools
    "_elder_blood":     True,                        # Ciri's 3-cooldown V-menu kit
    "_greeting":        "custom chronicle line",
}
```

The welcome screen matches `name_buf.lower()` against the dict. Match → `(name, build_dict)`. No match → `(name, None)` and the player gets the default kit.

## Flow — public API

### Quirk check loop

Nothing polls the quirk list. Every `on_*` method bumps the right counter, checks the threshold inline, and calls `_award` **exactly once** (the `self.is_unlocked(qid)` guard is the one-shot). The unlock path:

1. `_award(qid, name, apply_fn)` adds `qid` to `player.unlocked_quirks`.
2. `apply_fn(player)` fires (stat bump / add_effect / flag write).
3. `game.add_message("TRAIT UNLOCKED: …", 'loot')` logs the breadcrumb.
4. `game._log_chronicle(...)` adds the first-person reflection line.
5. `game._show_quirk_unlock_popup(name, effect, trigger, flavor)` **pauses the game** on a modal popup so the moment lands (SYSTEMS_AUDIT §7 confirmed the popup is wired, including after a bad save restore).

Active-power quirks go through `_award_power` instead, which also seeds `power_uses[id]` and `power_cooldowns[id]=0` from `_ACTIVE_POWER_DEFS` so the V-menu entry becomes usable immediately. `tick_powers()` runs each turn to decrement cooldowns.

### Hero special activation (V-menu path)

1. Player opens the V-menu (`game_menus.py::open_power_menu`).
2. The menu enumerates: quirk-granted actives, hero specials from `player.hero_specials`, Elder Blood powers (Ciri), armor-granted actives (Seven-League Boots, Gilgamesh's Bribe), charged accessories (Lyre of Orpheus, Hand of Glory), the Scales of Michael one-shot.
3. On select, if `pid.startswith('hero_')`, dispatch goes to `_activate_hero_special(pid)`.
4. Cooldown is set **immediately** (`pl.hero_special_cooldowns[pid] = special['cooldown']`) regardless of the quiz outcome. Burning the ability is paid upfront.
5. The quiz engine starts: `mode='escalator_chain', subject='ai', tier=1, max_chain=5`.
6. On quiz complete, callback dispatches `resolve_active_special(game, special, chain=result.score)` which looks up `special['effect']` in `_DISPATCH` and calls the handler with `(game, special, tier_effects[chain], chain)`.

### Hero passive consumption

Passives are never "activated." Each hook site checks `in player.hero_passives` at the moment it matters:

| Passive                 | Hook site                                                    |
|-------------------------|--------------------------------------------------------------|
| `will_to_power`         | `combat.py:1208` (+30% damage at <30% HP); `player.py:742` (immune to fear/charm at ≤30% HP) |
| `witcher_mutations`     | `combat.py:1212` (+20% damage vs all monsters)               |
| `witcher_resists`       | `player.py:293` (×0.85 fire/cold/lightning/acid/poison damage) |
| `niten_ichi_ryu`        | `combat.py:1222` (+15% damage when a non-ammo weapon is in the primary slot — fixed in v2.18 after the dual-wield gate was found dead; now any melee counts) |
| `demigod_hide_25`       | `player.py:289` (×0.75 physical damage)                      |
| `elder_blood_escape`    | `player.py:300` (auto-teleport once per floor at ≤25% HP)   |
| `vengeance_wakes`       | `player.py:316` (auto-berserk 8t at ≤50% HP)                 |
| `cynic_detachment`      | `combat.py:1242` (cursed weapon doesn't apply its -1 damage) |
| `plato_no_shard`        | `game_menus.py:735`, `game_render.py:4430` (identify menu without the Philosopher's Shard) |
| `resonant_frequency`    | `monster.py:680` (shock counter equal to `dmg//3` on every melee hit against the player) |

### V-menu composite

Any time the player opens V, the menu is rebuilt live from (in order):
- `_ACTIVE_POWER_DEFS` matches in `player.unlocked_quirks` (quirk-granted) — 26 entries
- `player.hero_specials` list items — 0, 1, or 3 per build
- Elder Blood 3-pack if `secret_build._elder_blood` — 3 entries (`elder_blink`, `elder_charge`, `elder_scream`)
- Armor-granted (Seven-League Step, Gilgamesh's Bribe) — per-floor once
- Charged accessories (Lyre, Hand of Glory, etc.) — per-charge
- Scales of Michael one-shot
- "Bind Odinkiller" when the appropriate thread tag is set

If the result list is empty the menu prints the (slightly stale) "Earn quirks to unlock them!" message — flagged in SYSTEMS_AUDIT §7 P4 because hero specials, Elder Blood, armor, and accessory powers also surface here.

## Quirks by trigger family

~100 quirks are enumerated below, grouped by how they're earned. Thresholds are from `_QUIRK_PROGRESS`; triggers from `_QUIRK_TRIGGER`; rewards from `_QUIRK_EFFECTS`.

### Combat-counter quirks

Awarded on `on_kill` / `on_take_damage` / `on_status_applied` / `on_status_reflected`.

| id          | Name                              | Trigger                                              | Reward                             |
|-------------|-----------------------------------|------------------------------------------------------|------------------------------------|
| `musashi`   | Musashi's Empty Strike            | 30 kills at chain exactly 1                          | Chain-1 damage uses 2nd multiplier instead of weakest |
| `valkyrie`  | The Valkyrie's Eye                | 25 ranged kills                                      | DEX +1                             |
| `beowulf`   | Beowulf's Vow                     | 10 unarmed wins                                      | Unarmed attacks +5 base damage     |
| `gawain`    | Gawain's Bargain                  | 6 wins starting at ≤40% HP                           | CON +1                             |
| `cuchulainn`| Cu Chulainn's Riastrad            | 5 kills while feared                                 | STR +2 **and** permanent `fear_immune` (v2.15.0 upgrade from flat STR+1) |
| `kali`      | Kali's Dance                      | 100 kills of same monster kind (max over dict)       | WIS +1 (timer_bonus theology 3)    |
| `thor`      | Thor's Oath                       | 30 combats with same weapon id (max over dict)       | That weapon gets +2 permanent enchant |
| `athena`    | Athena's Owl                      | See 50 distinct `known_monster_ids`                  | WIS +1 (timer_bonus history 4)     |
| `boudicca`  | Boudicca's Fury                   | 50 kills while below 40% HP (`hp_pct_before < 0.40`) | STR +2                             |
| `spartacus` | The Gladiator's Defiance          | 20 kills while any debuff is active                  | STR +1, CON +1                     |
| `leonidas`  | The Last Stand                    | Kill on 30 distinct dungeon floors                   | CON +2                             |
| `caesar`    | Veni Vidi Vici                    | 300 kills in one run                                 | All stats +1                       |
| `rasputin`  | Rasputin's Constitution           | 5 separate ≤5% HP survivals                          | CON +2                             |
| `green_knight` | The Green Knight               | Survive 5 single hits dealing ≥30% max_hp            | CON +1                             |
| `fenrir`    | Fenrir's Chains                   | 150 debuff-turns across any `_DEBUFF_EFFECTS`        | CON +1                             |
| `prometheus`| Prometheus Unbound                | 10 bleeding episodes of ≥5 turns                     | Permanent regenerating (+1 HP/t)   |
| `loki`      | Loki's Gambit                     | Wear 5 cursed items for 10+ turns each               | WIS +2                             |
| `darwin`    | Survival of the Fittest           | 8 distinct debuff types in one run                   | CON +3                             |
| `paracelsus`| Paracelsus' Doctrine              | Disease drains 5 total stat points                   | Permanent drain + disease resistance |
| `siegfried` | Siegfried's Bath                  | Eat ingredients from monsters with 5 distinct effect types | Permanent magic resistance   |
| `mithridates`| The Mithridates Protocol         | Eat 5 monster kinds that had previously poisoned you | Permanent poison + disease immunity |
| `perseus`   | Perseus' Reflection               | Reflect 5 status effects back at monsters            | +2 to all saving throws (writes `save_bonus_all`) |
| `apollo`    | Apollo's Perfection               | 10 max-chain hits (chain ≥ weapon.max_chain_length)  | INT +1 + math timer +3s            |

### Resource / consumable quirks

Awarded on `on_harvest` / `on_food_eaten` / `on_potion_drunk` / `on_scroll_read` / `on_wand_zapped` / `on_item_identified` / `on_lockpick_*` / `on_prayer` / `on_spell_cast`.

| id            | Name                       | Trigger                                              | Reward                             |
|---------------|----------------------------|------------------------------------------------------|------------------------------------|
| `enkidu`      | Enkidu's Wildness          | Harvest 20 distinct species                          | STR +1                             |
| `asclepius`   | Asclepius' Serpent         | Harvest 15 distinct poisonous species                | WIS +1 (timer_bonus animal 4)      |
| `tantalus`    | Tantalus' Resolve          | Eat 15 quality-0 ruined meals                        | STR +1                             |
| `persephone`  | Persephone's Descent       | Quality-5 meals from 5 distinct ingredient sources   | Ruined meals still yield half SP/HP |
| `circe`       | Circe's Cauldron           | Cook from 5 distinct `bonus_type` categories         | CON +1 (timer_bonus cooking 4)     |
| `scheherazade`| Scheherazade's Tongue      | Read 12 distinct unidentified scrolls                | INT +1 (timer_bonus grammar 5)     |
| `shakespeare` | The Bard's Tongue          | Read 50 scrolls total                                | INT +1 (timer_bonus grammar 5)     |
| `merlin`      | Merlin's Apprenticeship    | Zap 10 distinct unidentified wands                   | INT +1 (timer_bonus science 4)     |
| `tesla`       | Tesla's Circuit            | Zap 50 wands total                                   | INT +1 (timer_bonus science 5)     |
| `dionysus`    | Dionysus' Vision           | Drink 10 potions while hallucinating                 | WIS +1 (timer_bonus philosophy 3)  |
| `sisyphus`    | Sisyphus' Mastery          | Fail lockpick on 10 distinct trapped chests          | WIS +1 (timer_bonus economics 5)   |
| `de_medici`   | De Medici's Treasury       | 20 successful lockpicks                              | WIS +1 (timer_bonus economics 4)   |
| `job`         | Job's Endurance            | Trigger 5 distinct trap types                        | Permanent levitating               |
| `penelope`    | Penelope's Mastery         | 100 total armor/shield equip or unequip actions      | PER +1 (timer_bonus geography 3)   |
| `hephaestus`  | Hephaestus' Obsession      | Same armor piece equipped 15 times (max over dict)   | Writes `hephaestus_slot` → -1 equip threshold on that slot |
| `jormungandr` | Jormungandr's Cycle        | Equip/unequip same weapon 20 times (max over dict)   | +1 max_chain on that weapon        |
| `fisher_king` | The Fisher King's Vigil    | Pray 6 times at ≤15% HP                              | Prayer cooldown permanently halved |
| `zoroaster`   | The Prophet's Vigil        | Pray successfully on 15 distinct dungeon floors      | WIS +1 (all_timer_bonus 1)         |
| `morgan`      | Morgan le Fay              | Cast 6 spells at ≤20% HP                             | INT +2                             |

### Social / spatial quirks

Awarded on `on_kill` / `on_stair_use` / `on_floor_entered` / `on_floor_explored` / `on_combat_started` (Orpheus streak).

| id            | Name                       | Trigger                                              | Reward                                            |
|---------------|----------------------------|------------------------------------------------------|---------------------------------------------------|
| `orpheus`     | Orpheus' Lyre              | Stand beside monsters for 10 turns without combat × 5 | Writes `orpheus_active=True` → monsters start slowed 5t on each new floor |
| `ariadne`     | Ariadne's Thread           | Escape 10 floors within 30 turns of arriving         | INT +1                                            |
| `atalanta`    | Winged Feet                | Escape 10 floors within 25 turns of arriving         | DEX +2                                            |
| `theseus`     | Theseus in the Labyrinth   | Fully explore 5 dungeon floors                       | PER +1                                            |
| `ibn_battuta` | Ibn Battuta's Road         | Fully explore 30 distinct floors                     | PER +1 (timer_bonus geography 4)                  |
| `cerberus`    | Cerberus                   | 300 total stair uses                                 | Permanent warning                                 |
| `ragnarok`    | Ragnarok's Survivor        | Descend to level 100 at ≤10 HP                       | CON +5                                            |
| `ahasverus`   | Ahasverus                  | 15,000 tile moves                                    | Permanent searching                               |
| `wanderlust_q`| The Endless Wanderer       | 20,000 tile moves                                    | Writes `wanderlust_active=True` → SP drain from movement halved |
| `odin`        | Odin's Vigil               | 12,960 total `.` waits                               | Permanent telepathy                               |
| `buddha`      | The Buddha's Stillness     | 500 waits near hostile monsters                      | Permanent displacement                            |
| `narcissus`   | Narcissus                  | Open the examine menu 30 times                       | PER +1                                            |
| `hermes`      | Hermes' Wings              | 8+ teleports (any source)                            | Writes `hermes_active=True` → hasted duration permanently doubled |
| `norns`       | The Norns' Thread          | Use Recall Lore 20 times                             | Writes `norns_active=True` → recall-lore CD -50%  |
| `nostradamus` | The Prophet's Eye          | Recall Lore 10 times while mentally debuffed         | WIS +3                                            |

### Knowledge / quiz-answer quirks

Awarded on `on_quiz_answer` / `on_quiz_complete`.

| id             | Name                       | Trigger                                              | Reward                             |
|----------------|----------------------------|------------------------------------------------------|------------------------------------|
| `tiresias`     | Tiresias' Gift             | 25 correct while blinded                             | PER +2                             |
| `anansi`       | Anansi's Clarity           | 20 correct while confused                            | INT +1                             |
| `medusa`       | Medusa's Gaze              | Correct answer in 5 separate blinded episodes        | DEX +2                             |
| `cassandra`    | Cassandra's Persistence    | 50 total wrong answers in one run (retargeted 2026-09-24) | WIS +1                        |
| `ramanujan`    | The Infinite Sum           | 500 correct math in one run                          | INT +1 + math timer +5s            |
| `solomon_q`    | Wisdom of Solomon          | 100 correct philosophy                               | WIS +2                             |
| `confucius`    | The Analects               | 50 correct philosophy while Blessed                  | WIS +1 (timer_bonus philosophy 4)  |
| `galileo`      | Galileo's Heresy           | 100 correct science                                  | INT +1 (timer_bonus science 3)     |
| `archimedes`   | Give Me a Lever            | 50 sci AND 50 eco correct (special condition)        | INT +1                             |
| `hypatia`      | Hypatia's Legacy           | 50 math AND 50 sci correct (special condition)       | INT +2                             |
| `machiavelli`  | The Prince                 | 500 correct answers in one run                       | WIS +1 (all_timer_bonus 1)         |
| `sibyl`        | The Sibyl of Cumae         | 500 correct answers before dungeon_level 20          | +2s on all subject timers          |

### Timer quirks — stat-bump retarget (2026-09-24 fix)

The 16 non-math timer quirks below all route through `_timer_bonus(subj, N)`. Pre-fix, N seconds landed on `quiz_timer_bonuses[subj]` and were silently discarded because only math is timed. Post-fix, the helper also awards `+max(1, N // 3)` points to a subject-appropriate stat so the reward lands even when the timer line is dead:

| Subject    | Stat granted | Quirks                                               |
|------------|--------------|------------------------------------------------------|
| math       | INT          | Ramanujan, Apollo                                    |
| science    | INT          | Merlin, Tesla, Galileo                               |
| grammar    | INT          | Scheherazade, Shakespeare                            |
| philosophy | WIS          | Dionysus, Shiva, Confucius                           |
| history    | WIS          | Athena                                               |
| theology   | WIS          | Kali                                                 |
| economics  | WIS          | Sisyphus, De Medici                                  |
| animal     | WIS          | Asclepius                                            |
| geography  | PER          | Penelope, Ibn Battuta                                |
| cooking    | CON          | Circe                                                |

The player-facing parenthetical ("+Ns if the subject ever becomes timed") still ships in the trigger/reward copy for all 16; SYSTEMS_AUDIT §7 P4 and §8 flag it as text drift pending a sweep. In v2.18.0 the 11 item-card threshold strings were part of a similar audit wave (not yet fixed).

### Timer quirks — all-subjects (still math-targeted copy)

Three quirks still call `_all_timer_bonus(N)` which puts +N on every subject timer **and** grants +N WIS. The player-facing description reads "math combat quiz timer +Ns" because math is in fact the only subject that lands:

- `machiavelli` — The Prince (500 correct in one run) — all_timer +1 + WIS +1
- `zoroaster` — The Prophet's Vigil (pray on 15 distinct floors) — all_timer +1 + WIS +1
- `sibyl` — The Sibyl of Cumae (500 correct before L20) — all_timer +2 (no stat bump beyond the stacked +2 on `math`)

### Per-turn quirks (`on_turn`)

The per-turn tracker runs housekeeping each `advance_turn`:

| id        | Trigger                                                     | Reward                              |
|-----------|-------------------------------------------------------------|-------------------------------------|
| `shiva`   | 100 turns under hallucinating                               | WIS +1 (timer_bonus philosophy 5)   |
| `fenrir`  | 150 debuff-turns (one tick per turn where any `_DEBUFF_EFFECTS` is active) | CON +1                 |
| `prometheus` | 10 bleeding episodes of ≥5 turns each                    | Permanent regenerating              |
| `loki`    | 5 cursed items each worn 10+ turns                          | WIS +2                              |
| `orpheus` | 5 sessions of "monster adjacent, no combat for 10 turns"    | `orpheus_active` flag               |
| `sibyl`   | 500 correct + dungeon_level < 20 (checked each turn)        | +2s all subjects                    |
| `duck_of_doom` | 2026 turns wearing the Duck of Doom headgear           | Hatches a Waddlekind pet            |

Several per-turn power quirks also live here (venom_lore, reality_anchor, runic_armor, astral_form, atlas_burden) — see §Active powers.

### Mystery-reward quirks

Three quirks are architecturally quirks (unlocked via `_award`) but their _trigger_ is a mystery outcome rather than a counter. These are the "secret ladder" rewards: a mystery you solved pays out a quirk whose provenance looks organic:

- **Mimir** → granted on solving the Mimir's Well mystery (all-timer +1, which populates every subject's bonus). Per SYSTEMS_AUDIT §3 P1, the +1 on 9 untimed subjects is dead; only math benefits.
- **Fisher King** → the Fisher King's Vigil quirk is a separate counter path (6 prayers at ≤15% HP), not a mystery reward. The naming overlap with the Grail mystery (`mystery_system.py`) is intentional theming — same king, two surfaces.
- **Grail** → the Grail mystery grants permanent save-bonus-all via `apply_mystery_reward`; the quirk-equivalent reward routes through the normal perseus/mithridates style grant on the player stat block.

See [quests_mysteries](quests_mysteries.md) for the twelve mystery payouts and `mystery_system.py::apply_mystery_reward` for exact wiring.

## Active powers (quirk-granted V-menu entries)

26 quirks grant an entry on the V-menu via `_award_power` + `_ACTIVE_POWER_DEFS`. Shape:

```python
_ACTIVE_POWER_DEFS[id] = {
    'uses':     3,   # uses-based (no cooldown decrement)
    'cooldown': 0,   # cooldown-based (unlimited while ready) -- ONLY one of {uses, cooldown} is >0
    'label':    'Metabolic Surge',
    'desc':     'Restore 100 SP instantly.',
}
```

| id                   | Trigger                                                   | Uses / CD    | Effect                              |
|----------------------|-----------------------------------------------------------|--------------|-------------------------------------|
| `metabolic`          | 5,000 tiles moved                                         | x3           | Restore 100 SP                      |
| `iron_ration`        | 15,000 tiles moved                                        | x5           | Restore 100 SP                      |
| `shadow_step`        | 2,500 tiles while invisible                               | x3           | Invisible + Phasing 5t              |
| `wandering_star`     | 15 teleports                                              | CD 50t       | Random teleport                     |
| `time_dilation`      | 25 consecutive correct                                    | x1           | Time Stop 10t                       |
| `ouroboros`          | 1,000 correct in one run                                  | x1           | Hasted + Shielded + Regenerating 20t |
| `eye_storm`          | 5 damage-free floors                                      | x3           | Invisible + Blessed 10t             |
| `ancestral_q`        | Fully explore 10 floors                                   | x2           | Clairvoyance 20t                    |
| `sage_counsel`       | 50 correct history                                        | x3           | Blessed 15t                         |
| `focused_scholar`    | 500 total correct                                         | x2           | Brilliance 10t                      |
| `mind_fortress`      | 30 correct while mentally debuffed                        | x3           | Clear all mental debuffs            |
| `philosophers_stone` | Identify 200 items                                        | x1           | Blessed + Brilliance 10t            |
| `atlas_burden`       | Carry ≥90% weight for 100 turns                           | x2           | Heroism 20t                         |
| `zeus_bolt`          | Hasted 15 times in a run                                  | x3           | Shock Resist + Hasted 15t           |
| `gorgon_ward`        | Survive petrifying 3 times                                | x2           | Sleep Resist + Displacement 15t     |
| `phoenix_rising`     | Survive at ≤5% HP 10 times                                | x1           | Fully restore HP                    |
| `iron_will`          | Take damage 10 times while paralyzed                      | x2           | Shielded + Reflecting 10t           |
| `battle_trance`      | 200 kills                                                 | x3           | Heroism 15t                         |
| `second_sight`       | Recall Lore 5 times while blinded                         | x3           | Telepathy + Clairvoyance 15t        |
| `arcane_surge`       | 20 spells cast in one run                                 | x2           | Brilliance 10t + restore all MP     |
| `death_wish`         | 10 wins at ≤10% HP                                        | x3           | Heroism + Hasted 10t                |
| `mirror_mind`        | Identify 100 items                                        | x2           | Reflecting + Magic Resist 10t       |
| `venom_lore`         | 5 turns poisoned+diseased simultaneously                  | x3           | Poison Resist 20t + cures poison    |
| `war_cry`            | 15 kills while feared                                     | x3           | Hasted 8t                           |
| `temporal_shield`    | Take 50 hits in a run                                     | x2           | Shielded 25t                        |
| `mystic_eye`         | Enter 10 distinct floors with Telepathy active            | x3           | Telepathy + Clairvoyance + Warning 15t |
| `life_drain`         | 25 kills at ≤15% HP                                       | x3           | Restore 25% max HP                  |
| `reality_anchor`     | 5 turns confused+hallucinating simultaneously             | x2           | Clear all debuffs                   |
| `runic_armor`        | 10 turns with fire+cold+shock resists all active          | x2           | Fire + Cold + Shock defenses 10t    |
| `astral_form`        | 100 turns invisible                                       | x2           | Levitate + Invisible + Phase 8t     |

Dispatch for the V-menu "quirk power" branch lives in `game_menus.py::_activate_power`. Each pid routes to a block of `pl.add_effect(...)` calls plus a flavor `add_message`.

The cooldown decrementer is `QuirkSystem.tick_powers()` → called once per `advance_turn`.

## Hero specials — the 19 active abilities + `_DISPATCH`

19 unique hero actives spread across 15 builds; Ash Williams has 3. Dispatcher: `hero_specials._DISPATCH`.

```python
_DISPATCH = {
    'identify_n':           _eff_identify_n,
    'confuse_visible':      _eff_confuse_visible,
    'self_heal':            _eff_self_heal,
    'self_aoe_fire':        _eff_self_aoe_fire,
    'self_buff_stand':      _eff_self_buff_stand,
    'fear_visible':         _eff_fear_visible,
    'reveal_floor':         _eff_reveal_floor,
    'teleport_self':        _eff_teleport_self,
    'charm_visible':        _eff_charm_visible,
    'damage_single':        _eff_damage_single,
    'drain_attractive':     _eff_drain_attractive,
    'self_buff_berserk':    _eff_self_buff_berserk,
    'gain_ammo':            _eff_gain_ammo,
    'heal_pet':             _eff_heal_pet,
    'paralyze_target':      _eff_paralyze_target,
    'summon_sketch_helper': _eff_summon_sketch_helper,
    'heal_and_crit_buff':   _eff_heal_and_crit_buff,
    'reveal_radius':        _eff_reveal_radius,
    'aoe_heal_self':        _eff_aoe_heal_self,
}
```

| Build                          | Special ID                     | Name              | Effect                 | Cooldown | T5 payoff                                                       |
|--------------------------------|--------------------------------|-------------------|------------------------|----------|-----------------------------------------------------------------|
| aristotle of stagira           | `hero_aristotles_catalogue`    | Aristotle's Catalogue | `identify_n`       | 400      | Identify all unidentified items (count=999)                     |
| socrates of athens             | `hero_maieutic_question`       | Maieutic Question | `confuse_visible`      | 300      | Confuse 3 humanoids, 8t, +slowed                                |
| pythagoras of samos            | `hero_harmony_of_spheres`      | Harmony of Spheres| `self_heal`            | 250      | 5d6 HP + cleanse 2 debuffs                                      |
| prometheus the firebearer      | `hero_liver_bound_fire`        | Liver-Bound Fire  | `self_aoe_fire`        | 350      | r=3, 6d6 fire + burn 4t (self costs 5 HP regardless)            |
| leonidas of sparta             | `hero_spartan_stand`           | Spartan Stand     | `self_buff_stand`      | 350      | AC -5, 75% counter-strike, 12t                                  |
| alexander the great            | `hero_conquer_the_field`       | Conquer the Field | `fear_visible`         | 400      | Fear all visible non-boss 7t + immobilize 2t                    |
| theseus of athens              | `hero_labyrinth_sense`         | Labyrinth Sense   | `reveal_floor`         | 500      | Full map + all traps + stairs + items identified                |
| hermes trismegistus            | `hero_hermetic_step`           | Hermetic Step     | `teleport_self`        | 200      | Any-tile teleport + Hasted 3t                                   |
| odysseus of ithaca             | `hero_cunning_stratagem`       | Cunning Stratagem | `charm_visible`        | 400      | Charm 2 non-boss 20t                                            |
| merlin ambrosius               | `hero_stardrop`                | Stardrop          | `damage_single`        | 300      | 10d6 single-target (×0.5 vs bosses)                             |
| ash williams (1 of 3)          | `hero_give_me_some_sugar`      | Give Me Some Sugar| `drain_attractive`     | 300      | Drain 40 HP from `female_attractive`-tagged target + charm 3t   |
| ash williams (2 of 3)          | `hero_she_bitch_lets_go`       | Yo, She-Bitch! Let's Go! | `self_buff_berserk`| 350  | Berserk 12t + fear_immune + crit_buff + permanent STR +2        |
| ash williams (3 of 3)          | `hero_this_is_my_boomstick`    | This... Is My BOOMSTICK! | `gain_ammo`     | 400     | 30 shotgun_shell shells + next shot is AoE                      |
| ash ketchum                    | `hero_i_choose_you`            | I Choose You!     | `heal_pet`             | 250      | Full heal pet + cleanse all pet debuffs                         |
| ada augusta byron lovelace     | `hero_difference_engine`       | Difference Engine | `paralyze_target`      | 300      | Paralyze 6t + slow 8t on nearest non-boss                       |
| leonardo di ser piero da vinci | `hero_codex_sketch`            | Codex Sketch      | `summon_sketch_helper` | 400      | Summon a 40-level 3d8+6-damage SketchedPet for 40 turns         |
| saint joan of arc              | `hero_standard_of_the_maid`    | Standard of the Maid | `heal_and_crit_buff`| 350     | +50 HP + next 5 hits crit                                       |
| sir arthur conan doyle's sherlock holmes | `hero_deduction`     | Deduction         | `reveal_radius`        | 400      | r=99 reveal + identify all items                                |
| saint hildegard von bingen     | `hero_viriditas`               | Viriditas         | `aoe_heal_self`        | 350      | +50 HP + cleanse all debuffs                                    |

**Builds with no active (passives-only or kit-only):**
- `plato of athens` — passive `plato_no_shard`
- `friedrich nietzsche` — passive `will_to_power`
- `diogenes of sinope` — passive `cynic_detachment`
- `achilles son of peleus` — passive `demigod_hide_25`
- `geralt of rivia` — passives `witcher_mutations`, `witcher_resists`
- `ciri riannon` — passive `elder_blood_escape` + Elder Blood 3-pack (see below)
- `boudicca queen of the iceni` — passive `vengeance_wakes`
- `miyamoto musashi the sword saint` — passive `niten_ichi_ryu`
- `nikola tesla the wizard of menlo park` — passive `resonant_frequency`
- `dad` — kit only (`_immortal: True`, no quiz)
- `titivillus` — kit only (`_qa_tools: True`, no quiz; see QA section)
- Non-hero flavor builds `corwin`, `cain`, `fianna`, `fluffs`, `robyn` — no specials, no passives, no journal entries beyond the kit

**Boss immunity.** When a special sets `'boss_immune': True`, the resolver filters its target list with `is_boss_or_huge(m)` (`hero_specials.py:19`) which flags `m.is_boss` or `m.max_hp > 500`. Status-apply specials skip bosses; damage specials still hit them at ×0.5 (`_eff_damage_single`, `_eff_self_aoe_fire`).

**Idempotence of buffs.** `_eff_self_buff_stand` and `_eff_self_buff_berserk` both do `max(cur, dur)` on refresh — recasting at lower chain never weakens an active buff.

## Hero passives — the 10 flag strings

Set-of-strings in `player.hero_passives` from `HERO_PASSIVES`:

| Passive                | Build(s)                 | Hook site                   | Effect                                               |
|------------------------|--------------------------|-----------------------------|------------------------------------------------------|
| `plato_no_shard`       | plato of athens          | `game_menus.py:735`, `game_render.py:4430` | Identify menu usable without the Philosopher's Shard |
| `will_to_power`        | friedrich nietzsche      | `combat.py:1208`, `player.py:742` | +30% damage at <30% HP; immune to fear/charm at ≤30% |
| `cynic_detachment`     | diogenes of sinope       | `combat.py:1242`            | Cursed weapon's -1 BUC damage penalty does not apply |
| `demigod_hide_25`      | achilles son of peleus   | `player.py:289`             | ×0.75 physical damage                                |
| `witcher_mutations`    | geralt of rivia          | `combat.py:1212`            | +20% damage vs all monsters                          |
| `witcher_resists`      | geralt of rivia          | `player.py:293`             | ×0.85 fire/cold/lightning/acid/poison incoming       |
| `elder_blood_escape`   | ciri riannon             | `player.py:300`             | Once-per-floor auto-teleport at ≤25% HP              |
| `vengeance_wakes`      | boudicca queen of the iceni | `player.py:316`         | Auto-berserk 8t at ≤50% HP (if not already berserk)  |
| `niten_ichi_ryu`       | miyamoto musashi         | `combat.py:1222`            | +15% damage with any non-ammo primary weapon (v2.18 fix — pre-fix required a ranged slot that Musashi can't fill with his starting kit) |
| `resonant_frequency`   | nikola tesla             | `monster.py:680`            | Shock counter equal to `dmg//3` on every melee hit against the player |

All ten are consumed at hook sites (SYSTEMS_AUDIT §3 verified) — no passive is "dead" post-v2.18.

## Elder Blood — Ciri's 3-cooldown kit

Ciri's `_elder_blood: True` metadata flag unlocks a separate V-menu block on top of her passive. In `game_menus.py:1027-1047`:

| pid              | Label  | Cooldown | Effect                                                   |
|------------------|--------|----------|----------------------------------------------------------|
| `elder_blink`    | Blink  | 8t       | Teleport to safety ("The Elder Blood bends space")       |
| `elder_charge`   | Charge | 12t      | Next melee attack deals ×3 damage                        |
| `elder_scream`   | Scream | 20t      | Cold damage to all visible enemies                       |

Shared mechanic: all three are **cooldown-only** (not use-limited), the dispatch is inline in `_activate_power` (not in `hero_specials._DISPATCH`), and they stack with the `elder_blood_escape` passive. The passive is the "oh crap" bailout at ≤25% HP; the 3-pack is for offensive and mobility choice. Ciri is the only "elder blood hero" — the metadata was designed for a potential future hero but no second build sets `_elder_blood: True` as of v2.18.

## Secret builds — the 32-entry roster

`SECRET_BUILDS` currently ships 32 entries (grouped below). Name match is case-insensitive against the player's typed name. Match → the stat dict overrides defaults and the metadata underscore-fields seed the starting kit via `main.py:1900+`.

### Great philosophers (INT/WIS, physically frail)
`aristotle of stagira`, `socrates of athens`, `plato of athens`, `friedrich nietzsche`, `pythagoras of samos`, `prometheus the firebearer`, `diogenes of sinope`

### Warriors
`achilles son of peleus`, `leonidas of sparta`, `alexander the great`, `theseus of athens`

### Rogues
`hermes trismegistus`, `odysseus of ithaca`

### Mages
`merlin ambrosius`

### IP / Pop-culture
`ash williams` (3 specials), `geralt of rivia` (Witcher), `ciri riannon` (Elder Blood), `ash ketchum` (pet trainer)

### New legendary builds (multi-word full names)
`ada augusta byron lovelace`, `leonardo di ser piero da vinci`, `boudicca queen of the iceni`, `saint joan of arc maid of orleans`, `sir arthur conan doyle's sherlock holmes`, `miyamoto musashi the sword saint`, `saint hildegard von bingen`, `nikola tesla the wizard of menlo park`

### Family / flavor builds (kids' names, no specials or passives)
`corwin`, `cain`, `fianna`, `fluffs`, `robyn`

### Legendary flags (secret-of-secrets)
- `dad` — all stats 20, `punch_in_the_face` weapon, `_immortal: True`, chronicle "Dad has arrived. Everything will be fine." Confirmed from the welcome screen's "Did you mean Dad?" easter egg when the player types "god" (`welcome_screen.py:463-465`).
- `titivillus` — the Scribe of Errors QA build. `_qa_tools: True` grants Shift+I (immortal toggle) and Shift+W (floor warp). **Gated behind `PQ_QA_MODE=1` env var or `--qa` CLI flag as of v2.18.0** (`welcome_screen.py:471-476`); before the gate the name alone unlocked the dev tools, which SYSTEMS_AUDIT §7 P1 flagged. With neither flag set, the typed name is treated as a plain run — no stats, no kit, no QA tools.

### Metadata flags on build dicts (quick reference)

| Flag                       | Effect                                                                             |
|----------------------------|------------------------------------------------------------------------------------|
| `_sprite`                  | Env sprite name (`assets/tiles/env/<name>.png`)                                    |
| `_start_weapon`            | id string OR `(type, material)` tuple                                              |
| `_start_melee`             | Secondary melee weapon (dual-wielding setups like Musashi, Ash)                    |
| `_start_shield`            | id or tuple                                                                        |
| `_start_armor` / `_equip_armor` | Starting armor + auto-equip                                                   |
| `_start_wand` / `_start_book` | Starting arcane kit                                                             |
| `_start_accessory` / `_start_extra_acc` | Starting accessory + extras list                                       |
| `_start_ammo`              | Starting ammo id                                                                   |
| `_start_spells`            | Pre-known spell list                                                               |
| `_start_potions`           | Pre-granted potions                                                                |
| `_start_soul_spheres`      | Count of starting Soul Spheres (Ash Ketchum: 4)                                    |
| `_start_unusual_sphere`    | Grant one wildcard Soul Sphere                                                     |
| `_no_dagger`               | Skip the default `iron_dagger` kit grant                                           |
| `_lock_melee`              | Melee slot welded (Ash's chainsaw cannot be unequipped)                            |
| `_immortal`                | Can't die (Dad only — HP snaps back on would-be-death)                             |
| `_qa_tools`                | Shift+I / Shift+W dev tools; gated behind env var in v2.18                         |
| `_elder_blood`             | Ciri's 3-cooldown V-menu kit                                                       |
| `_greeting`                | Custom chronicle line on run start                                                 |

### Starting kit resolution (`main.py::_give_starting_kit`)

The kit builder reads the metadata fields in a fixed order: `_no_dagger` suppresses the default kit, then `_start_weapon` / `_start_melee` / `_start_shield` / `_start_armor` / `_start_wand` / `_start_book` / `_start_accessory` / `_start_extra_acc` / `_start_ammo` resolve by id or by `(type, material)` lookup against the item registry. `_start_spells` adds entries to `player.known_spells`. `_start_potions` push ready-to-drink potions. `_start_soul_spheres` + `_start_unusual_sphere` call into the Soul Sphere spawn path.

After the kit is placed, the hero wiring (`main.py:2013-2033`) looks up `(get_specials_for_build, get_passives_for_build, get_journal_for_build)` on the lowercased typed name and populates `player.hero_specials` / `hero_passives` / logs the journal line.

## Invariants (don't break)

- **Quirks are one-shot. `_award(qid, ...)` must check `is_unlocked(qid)` first.** Re-awarding would double-apply the stat bump or re-fire the unlock popup.
- **Unlock popup pauses the game.** `_show_quirk_unlock_popup` is a modal; it must land for the player to see the reward even in combat. Save/load must restore `unlocked_quirks` + `quirk_progress` + `power_uses` + `power_cooldowns` as a tuple — none of them have cross-game persistence.
- **Non-math timer bonuses now bump a stat.** `_timer_bonus(subj, N)` and `_all_timer_bonus(N)` BOTH grant stat bonuses alongside the (silently-dead) seconds. Do not remove the stat bump path when sweeping the "if the subject ever becomes timed" copy.
- **Hero special cooldown is paid upfront.** `_activate_hero_special` sets `hero_special_cooldowns[pid] = special['cooldown']` **before** the quiz starts. Fizzling at chain 0 still spent the cooldown — the risk is intentional.
- **Boss immunity is handler-local.** Each `_eff_*` with `boss_immune` filters its own target list via `is_boss_or_huge`. If you add a new effect, do not rely on the dispatcher to filter — check in the handler.
- **Elder Blood passive and 3-pack are independent.** The passive gates on `in player.hero_passives`; the 3-pack gates on `(secret_build or {}).get('_elder_blood')`. A hero can hypothetically have one without the other, though only Ciri ships both.
- **Secret-build QA tools require `PQ_QA_MODE=1` or `--qa`.** The gate landed in v2.18.0 so the Titivillus name alone no longer unlocks Shift+I / Shift+W. Casual players stumbling on the name get a plain run.
- **"Secret build" labeling is deliberate.** The welcome screen's gold `[*] SECRET BUILD ACTIVE!` label and the "Did you mean Dad?" easter egg are intentional discovery moments. Do not replace the label with the explicit hero name, do not list the builds anywhere in the UI, and do not add tooltips that spoil the name mapping.
- **`niten_ichi_ryu` gate changed in v2.18.** The original gate required `weapon AND ranged_weapon`, which was unreachable with Musashi's two-melee kit (SYSTEMS_AUDIT §3 P1 found the bug). Current gate: any non-ammo weapon in the primary slot. Do not revert.
- **`QuirkSystem.__getstate__` drops `self.game`.** The game reference holds pygame surfaces that can't be pickled; it's rebound by `load_state`. If you add new state to QuirkSystem, make it picklable or exclude it.

## Interactions

- **[combat](combat.md)** — hero passives `will_to_power` / `witcher_mutations` / `niten_ichi_ryu` / `cynic_detachment` all read in the damage multiplier path (`combat.py:1200-1245`). Hero buffs `crit_buff` / `berserk` / `stand_ac` / `fear_immune` are status flags set by hero specials and consumed on the next relevant combat event. Quirk flags `beowulf_unarmed_bonus` (+5 unarmed base), `musashi_active` (chain-1 mid-multiplier), `thor_qualifying_weapon` (+2 enchant) also read from combat.py damage calc.
- **[items](items.md)** — quirks unlocked by item use: `scheherazade` + `shakespeare` (scrolls), `merlin` + `tesla` (wands), `dionysus` (potions), `penelope` + `hephaestus` + `jormungandr` (equipment cycling). Hero `aristotle` + `sherlock_holmes` specials interact with the item identification state. Starting-kit items are resolved from the item registry at build-start.
- **[quests_mysteries](quests_mysteries.md)** — Mimir mystery grants an all-timer bonus (mostly dead reward; see SYSTEMS_AUDIT §3 P1). The Fisher King's Vigil quirk and the Grail mystery theme share the Grail-legend naming but trigger independently. The duck_of_doom quirk is a 2026-turn mystery-adjacent ladder that hatches a pet.
- **[save_bonus](save_bonus.md)** — Perseus quirk writes `quirk_progress['save_bonus_all'] = 2` which is read by `Player.save_bonus_for(cat)` in the "innate" lane (never clamped off, additive with the Torque of Lugh + equipment lanes).
- **[status_effects](status_effects.md)** — permanent effect rewards (odin, buddha, ahasverus, cerberus, prometheus, mithridates, paracelsus, siegfried, job, cu chulainn) all route through `pl.add_effect(name, -1)`. The `-1` duration marks the effect permanent; `tick_all` leaves it alone. Hero `will_to_power` returns `False` out of `add_effect('feared'|'charmed', ...)` when the HP gate fires — the effect is never applied.
- **[quiz_engine](quiz_engine.md)** — hero specials open an `escalator_chain` quiz on `subject='ai'`. The `_timer_bonus` subject map and `quiz_timer_bonuses` dict live in the player state the engine reads from `start_quiz`.

## History of major decisions

- **2026-05-28** — Bofuri-style quirk system shipped. Initial 50 quirks with the counter-dispatch pattern; one wrong-answer-ends-threshold semantic hadn't landed yet.
- **2026-05-29** — Zero-tolerance threshold rule locked in (see quiz_engine.md). Cassandra's "pass a threshold with 2+ wrong" trigger became unreachable; the retarget to "50 total wrong in a run" happened later.
- **2026-05-31** — Harvest+Cook redesign; per-floor stat cap added. Several cooking quirks (Tantalus / Persephone / Circe) started depending on cook-path hooks; SYSTEMS_AUDIT §5 later found `main.py::_cook_compound` wasn't calling `on_food_eaten`, so these three are currently unreachable via normal play.
- **2026-06-01** — Case-exact answer compare in quiz engine (grammar bug); unrelated but shipped alongside quirk balance.
- **2026-07-18** — v2.4.0 — repo/distro cleanup. Quirk count expanded to ~100; active-power quirks (26 of the current set) added in this wave with the `_award_power` / `_ACTIVE_POWER_DEFS` fork.
- **2026-08-06** — Identify v3. The quirks that trigger on identify (`philosophers_stone` at 200, `mirror_mind` at 100) continued to work via `on_item_identified` because v3 kept the "successful identify" callback. Masteries + 277 blessings got pruned; the related `plato_no_shard` passive gained prominence.
- **2026-09-05** — Hero system Phase 3B. 19 hero actives wired through `_DISPATCH`; 10 hero passives wired at their hook sites. Hero specials granted at game start (not earned).
- **2026-09-06** — v2.9.0. System-change sweep rule codified (CLAUDE.md). Grammar v2 shipped alongside.
- **2026-09-24** — Timer-quirk retarget: 16 non-math + 3 all-subject timer quirks got stat bumps so the reward lands even though only math is timed. Cassandra retargeted from "pass threshold with wrongs" to "50 total wrong in a run" (persistence, not success-with-noise, matches the mythic character).
- **2026-10-02 (v2.18.0)** — Systems audit + fix wave. `niten_ichi_ryu` gate relaxed to any non-ammo primary weapon; `_qa_tools` gated behind `PQ_QA_MODE=1`; `cuchulainn` upgraded from flat STR+1 to STR+2 + permanent `fear_immune`. 16 non-math timer-quirk parentheticals + 3 all-subject copies flagged for a copy sweep.

## Testing
- `tests/test_quirk_award.py`, `tests/test_quirk_dispatcher.py`, `tests/test_quirk_progress.py` — pin the award path (one-shot guard, `apply_fn` fires once, `_show_quirk_unlock_popup` call), the `on_*` dispatcher wiring, and `get_quirk_progress` reporting for simple + set + dict + special-condition quirks.
- `tests/test_quirk_timer_retarget.py` — covers the 2026-09-24 fix: `_timer_bonus(subj, N)` grants both the subject-flavored stat bump and the (currently dead) timer entry; `_all_timer_bonus(N)` grants +N WIS.
- `tests/test_hero_specials.py` — exercises `_DISPATCH` → each `_eff_*` handler with chain 0..5; checks boss immunity (`is_boss_or_huge` skip for status, ×0.5 for damage); verifies `_activate_hero_special` pays the cooldown upfront and dispatches `resolve_active_special` from the quiz callback.
- `tests/test_hero_passives.py` — pins each passive's hook site: Niten +15% dmg (any non-ammo weapon), Will to Power at <30% HP (dmg + fear/charm immunity), Elder Blood escape (once per floor at ≤25%), Vengeance Wakes auto-berserk 8t at ≤50%, Demigod Hide ×0.75 physical, Witcher resists ×0.85 elementals, Cynic Detachment cursed weapon has no BUC penalty, Plato no-shard identify path, Tesla shock counter.
- `tests/test_secret_builds.py` — pins the SECRET_BUILDS lookup (case-insensitive), the `_qa_tools` env-var gate (name alone with no `PQ_QA_MODE` returns `build=None`), the Dad `_immortal` snap-back-to-full-HP flow, and Ash Williams's 3-special list form.

## Known rough edges

From SYSTEMS_AUDIT.md:

- **§3 P1 — Mimir's Well reward is 9/10 dead** (`mystery_system.py::mimir_reward`): the mystery grants an all-timer +1 that lands on 10 subjects but only `math` is timed. The quirk-adjacent `all_timer` lane patched itself with a +1 WIS; the mystery reward hasn't. Pending rewrite as math-only or a substantive non-timer reward.
- **§5 P1 — Cooking quirks unreachable via normal play** (`main.py::_cook_compound`): the reachable compound-cook path never calls `on_food_eaten`, so Tantalus (15 ruined), Persephone (5 distinct Q5 sources), Circe (5 distinct bonus_types) **cannot unlock** via the main cook flow. Only the marked-unreachable `_cook_item` path invokes it.
- **§5 P1 — Job's Endurance partially dead** (`main.py::_lockpick.on_complete`): passes static `'chest_fail'` trap-type string. Job's 5-distinct-trap-type trigger can only ever receive one entry.
- **§3 P2 — Sisyphus boulder mystery may be un-completable for low-STR builds** (Diogenes STR 5): the 25-tiles-over-carry-limit mechanic is impossible under that stat floor.
- **§7 P1 — Titivillus QA gate** fixed in v2.18.0 (`PQ_QA_MODE=1` env var or `--qa` CLI flag). Prior to v2.18 the name alone unlocked Shift+I / Shift+W.
- **§7 P2 — 16 non-math timer quirks + 3 all-subject timer quirks** carry parenthetical "+Ns if the subject ever becomes timed" copy that is honest-but-noisy. The retarget already granted stat bumps; copy sweep pending (Scheherazade, Merlin, Sisyphus, Asclepius, Penelope, Dionysus, Athena, Shiva, Circe, Kali, Ibn Battuta, Tesla, De Medici, Confucius, Galileo, Shakespeare — plus Sibyl, Zoroaster, Machiavelli "applies to math combat" awkward phrasing).
- **§7 P2 — `game_menus.py::_open_power_menu:1122`** empty-menu message says "Earn quirks to unlock them!" — but hero specials, Elder Blood, armor actives, and charged accessories all surface here too.
- **§3 P2 — `armor.json::green_knights_plate`** declares `equip_chain_mode: escalator_chain` with T5 passives, but the item has no spawn path (one of 7 `quest_spawn_*` methods never implemented). The whole chain-equip integration is dead until the spawn methods ship.
- **§7 P5 — "MASTERY!" vocabulary** has ~50 string references across game_render / fantasy_ui / main that pre-date the 2026-08-06 identify-v3 ship (which removed masteries). Pending full sweep.
