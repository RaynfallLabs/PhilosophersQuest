# Karma & Prayer

> Status: reference. Reflects v2.18.0 (`409e15d`, 2026-10-02).
> Scope: karma scale (-10..+10), 30 moral NPC encounters,
> 5 flavor NPC encounters, Ethereal Unicorn state machine, Magic
> Dungeon Carrot, Prayer v2 (`\` key), Divine Intercession
> (Shift+`\`), Fisher King cooldown mechanics, the Altar of the Last
> Judgment, and the Seven Seals gate.
>
> Related docs: [quests_mysteries](quests_mysteries.md) (Seven Seals
> quest chain, Fisher King mystery, Judgment altar's quest side),
> [items](items.md) (Sword of Michael, Scales of Michael, Ring of
> Command, Chandrahasa's karma-disappear), [progression](progression.md)
> (quirk unlocks surfaced by prayer + Oracle), [world](world.md)
> (bones), [combat](combat.md) (`invulnerable`, holy fire,
> `kill_count_karma_adjust` on Penitent's Blade).

---

## 1. Karma scale

### 1.1 Definition and clamp

Karma is a single integer stored on `Game.karma`, initialized to `0`
in `__init__`, saved and loaded through `save_system`. The scale is
**-10..+10 inclusive**, hard-clamped by every mutation site that
goes through `_apply_npc_choice`:

```python
# src/game_encounters.py:758
self.karma = max(-10, min(10, self.karma + karma_delta))
```

The clamp is enforced at the NPC-choice assignment and at the
Judgment outcome lookup (`npc_encounters.judge_karma` begins with
`karma = max(-10, min(10, karma))`). One off-path mutation exists —
Penitent's Blade `kill_count_karma_adjust` (combat.py) does
`_g.karma = cur_karma + 1` without re-clamping, and SYSTEMS_AUDIT §4
flags this as a latent invariant risk. In current code it only fires
at karma < 0, so the clamp holds in practice.

### 1.2 Starting karma

`self.karma: int = 0 # cumulative moral score (-10 to +10)` on
construction. There is no class-based starting karma — every run
begins at zero. The clamp is "hard" (not "soft"): once at +10,
further +1 options are no-ops numerically but still run their cost /
reward / outcome text.

### 1.3 Chronicle hooks on extremes

Hitting +10 or -10 for the first time logs a chronicle line
(`game_encounters.py:759-762`):

- First `karma == 10`: "I feel... clean. Like everything I've done
  down here has mattered. The dungeon feels lighter."
- First `karma == -10`: "Something inside me has gone cold. The
  dungeon doesn't frighten me anymore. That frightens me."

### 1.4 Who reads karma

Karma is consulted by:

- `game_divine._karma_tier` → selects one of five Bible-verse tiers
  for prayer flavor (saintly / righteous / neutral / slipping /
  fallen).
- `_resolve_simple_prayer` → scales prayer **magnitudes** (SP/HP/MP
  restore, blessing count, chain-5 shielded duration). Altar
  **doubles** the karma delta before application.
- `_altar_drop_reveal` → karma > 0 reveals truthfully (cursed items
  consumed, blessed items glow); karma < 0 lies deceptively (cursed
  "glows holy", blessed "drawn into black aura"); karma == 0 is
  silent.
- `_resolve_judgment` → L99 altar, one-shot, maps karma to five
  outcomes.
- `main.py:1619` → Chandrahasa-class weapons disappear on floor
  change when karma < 0 (`karma_disappear_proc`). Returns "to Shiva."
- `game_encounters._handle_unicorn_bump` → trusting-unicorn bump at
  karma < 0 makes the unicorn "recoil" and flee.
- `_apply_npc_choice` with `suryas_gift` chain passive → **doubles**
  reward on positive-karma deeds.

---

## 2. The 30 moral NPC encounters

### 2.1 Overview

The dungeon is divided into **10 level blocks** of 9 levels each.
Each block has **3 candidate encounters** defined in
`src/npc_encounters.py::ENCOUNTERS`. One encounter is selected per
block (`select_encounter_levels`), placed on a random non-boss level
inside the block, and the trigger item (if any) is pre-spawned 1-3
levels earlier so the player can arrive with it in-hand.

Blocks and level ranges (`npc_encounters._BLOCKS`):

| Block | Level range | Boss excluded |
|-------|-------------|---------------|
| 1 | 3-9 | — |
| 2 | 11-19 | — |
| 3 | 21-29 | — |
| 4 | 31-39 | — |
| 5 | 41-49 | — |
| 6 | 51-59 | — |
| 7 | 61-69 | — |
| 8 | 71-79 | — |
| 9 | 81-89 | — |
| 10 | 91-98 | 100 omitted |

Boss levels 20, 40, 60, 80, 100 are **excluded** from NPC spawns
(`_BOSS_LEVELS = frozenset({20, 40, 60, 80, 100})`).

### 2.2 Encounter schema

Each `ENCOUNTERS[i]` dict carries:

| Field | Meaning |
|-------|---------|
| `tag` | Unique id — used for `_encountered_npcs` set membership |
| `name`, `symbol`, `color` | Display |
| `block` | 1-10, must match a `_BLOCKS` entry |
| `trigger_item` | optional item id — if present, the item spawns `trigger_level_offset` floors (default 1) **before** the NPC |
| `text` | Encounter description (shown on screen 1) |
| `options` | Exactly 3 dicts (see below) |
| `sprite_id` | Monster sprite key, auto-populated from `_KARMA_SPRITES` if absent |

Each option carries `label`, `karma: {-2, -1, 0, +1}`, `outcome`,
`cost`, `reward`. By convention option 1 is the moral choice, option
2 is the "cannot help" neutral, option 3 is the selfish exploit. The
player is **never framed as cruel**; even -1 options read as
"pragmatic necessity" (SYSTEMS_AUDIT §3: "The player is never cruel;
even selfish options are framed as pragmatic necessity.").

Cost types: `food`, `healing_potion`, `potion`, `scroll`, `weapon`,
`gold`, `hp_percent`, `max_hp`, `sp`, `triggered_item`, `accept_item`,
`spawn_deadite_ambush`. See `npc_encounters.can_pay_cost` for the
full predicate.

Reward types: `gold`, `random_weapon` / `_armor` / `_shield` /
`_accessory` / `_potion` / `_scroll` / `_food` / `_wand`, `stat`,
`specific_item`, `multi`, `message`, `effect`, `enchant_weapon`.

### 2.3 Block × encounter table

The three candidates per block are listed below. One is chosen; the
pool prioritizes non-triggered encounters and samples at most one
triggered encounter per block.

**Block 1 (L3-9):**

| Tag | Name | Trigger | Karma options | Headline reward (karma -1 branch) |
|-----|------|---------|---------------|------------------------------------|
| `elara_amulet` | Lost Girl | `silverlight_pendant` (offset 1) | +1 / 0 / -1 | — (keep triggered item) |
| `brother_aldous` | Dying Monk | — | +1 / 0 / -1 | `saints_reliquary` accessory |
| `marta_ratchatcher` | Rat-Catcher | — | +1 / 0 / -1 | 2 potions + 1 food |

**Block 2 (L11-19):**

| Tag | Name | Trigger | Karma options | Headline reward (karma -1) |
|-----|------|---------|---------------|-----------------------------|
| `sir_aldric` | Burdened Knight | — | +1 (burden: `cursed_lodestone`) / 0 / -1 | CON +1 |
| `tam_thief` | Young Thief | — | +1 / 0 / -1 | 60-100 gold + random weapon |
| `helena_cartographer` | Injured Scholar | — | +1 / 0 / -1 | random scroll + 150-200 gold |

**Block 3 (L21-29):**

| Tag | Name | Trigger | Karma options | Headline reward (karma -1) |
|-----|------|---------|---------------|-----------------------------|
| `marcus_sword` | Grieving Father | `oathkeeper_sword` (offset 2) | +1 / 0 / -1 | — (keep sword) |
| `blinded_soldier` | Blinded Soldier | — | +1 / 0 / -1 | random armor + 100-150 gold |
| `dying_messenger` | Dying Courier | — | +1 (burden: `sealed_dispatch`) / 0 / -1 | 80-120 gold + random potion |
| `deadite_woman` | Moaning Woman | — | **0 / 0 / +1** (v2.18 — see §2.4) | — |

**Block 4 (L31-39):**

| Tag | Name | Trigger | Karma options | Headline reward (karma -1) |
|-----|------|---------|---------------|-----------------------------|
| `sister_marguerite` | Starving Nun | — | +1 / 0 / -1 | random accessory + 80-120 gold |
| `chained_priest` | Chained Priest | — | +1 / 0 / -1 | random scroll + potion + 100-150 gold |
| `old_konstantin` | Old Warrior | — | +1 / 0 / -1 | 150-200 gold + random accessory |

**Block 5 (L41-49):**

| Tag | Name | Trigger | Karma options | Headline reward (karma -1) |
|-----|------|---------|---------------|-----------------------------|
| `apprentice_healer` | Poisoned Herbalist | — | +1 / 0 / -1 | 2 potions + 1 food |
| `ghost_grave` | Ghost of Edwin | — | +1 (cost: max_hp -15) / 0 / -1 | 150-200 gold + random accessory |
| `deserter` | Legion Deserter | — | +1 / 0 / -1 | `officers_signet` accessory |

**Block 6 (L51-59):**

| Tag | Name | Trigger | Karma options | Headline reward (karma -1) |
|-----|------|---------|---------------|-----------------------------|
| `blind_seer` | Blind Seer | — | +1 / 0 / -1 | 2 scrolls + 1 potion |
| `trapped_seraph` | Caged Angel | — | +1 (cost: scroll) / 0 / -1 | WIS +1 |
| `weeping_mother` | Weeping Ghost | — | +1 (cost: sp 60) / 0 / -1 | random accessory |

**Block 7 (L61-69):**

| Tag | Name | Trigger | Karma options | Headline reward (karma -1) |
|-----|------|---------|---------------|-----------------------------|
| `ser_brennan` | Dying Knight | — | +1 / 0 / -1 | random weapon + random shield |
| `cursed_scholar` | Cursed Scholar | — | +1 (cost: hp -20%) / 0 / -1 | INT +2 |
| `fairy_jar` | Trapped Fairy | — | +1 (cost: potion) / 0 / -1 | DEX +1 |

**Block 8 (L71-79):**

| Tag | Name | Trigger | Karma options | Headline reward (karma -1) |
|-----|------|---------|---------------|-----------------------------|
| `penitent` | The Penitent | — | +1 / 0 / -1 | 200-300 gold + `penitents_blade` weapon |
| `roderic_shield` | Young Knight | `lionheart_shield` (offset 2) | +1 / 0 / -1 | — (keep shield) |
| `forgotten_prisoner` | Forgotten Prisoner | — | +1 (cost: gold 150) / 0 / -1 | 200-300 gold + random accessory |

**Block 9 (L81-89):**

| Tag | Name | Trigger | Karma options | Headline reward (karma -1 / -2) |
|-----|------|---------|---------------|----------------------------------|
| `fallen_paladin` | Fallen Paladin | — | +1 (cost: gold 200) / 0 / -1 | 200-300 gold + random armor |
| `azarael_demon` | Bound Demon | — | +1 (cost: scroll) / 0 / **-2** (v2.18) | STR +2, 200 gold |
| `child_shrine` | Small Shrine | — | +1 / 0 / -1 | random accessory + 150-200 gold |

**Block 10 (L91-98):**

| Tag | Name | Trigger | Karma options | Headline reward (karma -1) |
|-----|------|---------|---------------|-----------------------------|
| `dying_prophet` | Dying Prophet | — | +1 / 0 / -1 | `prophets_amulet` accessory |
| `petrified_adventurer` | Stone Statue | — | +1 (cost: scroll) / 0 / -1 | random weapon + random armor |
| `last_merchant` | Lost Merchant | — | +1 / 0 / -1 | random weapon + accessory + 200-300 gold |

### 2.4 v2.18 karma re-tunes

Two encounters had their karma deltas rebalanced in v2.18 after
dominant-strategy analysis.

**`deadite_woman` (Block 3)** — audit finding (SYSTEMS_AUDIT §3):
"'It's a trick, get an ax' granted karma +1 AND 30-60 gold at no cost.
Option 1 granted karma +1 despite triggering an ambush + 10% HP
damage. Naive-help punished, cynical trickery rewarded. Karma logic
inverted." v2.18 fix:

- Option 1 "Kneel down and try to help her" — karma **0** (was +1).
  Triggers the Deadite ambush (10% HP + spawns hostile). Naive-help
  no longer rewarded.
- Option 2 "Walk away" — karma 0 unchanged.
- Option 3 "'It's a trick. Get an ax.'" — karma **+1**, cost: none,
  **reward: none** (gold stripped, was 30-60). The player gets the
  pattern-recognition karma for correctly identifying the ambush,
  but no loot.

Current code (`npc_encounters.py:590-631`):

```python
'options': [
    {'label': "Kneel down and try to help her",
     'karma': 0,
     'cost': {'type': 'spawn_deadite_ambush'},
     'reward': None, ...},
    {'label': "Walk away — you can't help this woman",
     'karma': 0, 'cost': None, 'reward': None, ...},
    {'label': '"It\'s a trick. Get an ax."',
     'karma': +1, 'cost': None, 'reward': None, ...},
],
```

**`azarael_demon` (Block 9)** — audit finding: "'Shatter the chains'
pays STR+2 + 200 gold at karma -1. One -1 rarely tips a tier;
cost:reward mispriced." v2.18 fix: karma delta changed to **-2** so
freeing a bound demon actually costs a tier (two -2 events = -4 =
`slipping` tier → `fallen` tier if deep enough).

Current code: `'karma': -2` for the "Shatter the chains" option
(`npc_encounters.py:1580`).

### 2.5 Trigger item flow

Four encounters pre-spawn an item on a prior floor so the player
arrives with context:

| Encounter | `trigger_item` | Offset | Pre-spawn floor example |
|-----------|----------------|--------|-------------------------|
| `elara_amulet` | `silverlight_pendant` | 1 | NPC on L7 → pendant on L6 |
| `marcus_sword` | `oathkeeper_sword` | 2 | NPC on L23 → sword on L21 |
| `roderic_shield` | `lionheart_shield` | 2 | NPC on L75 → shield on L73 |

`get_trigger_item_levels(placements)` produces the `{item_id: floor}`
map at game start (`npc_encounters.py:1860`). The dungeon generator
plants these items on the computed floor during world setup.

Non-triggered encounters simply spawn as a sessile allied NPC
(`is_allied=True, hp=1, ai_pattern='sessile'`) on their chosen block
floor via `_maybe_spawn_npc` (`game_encounters.py:122`).

### 2.6 Encounter resolution flow

1. Player bumps the NPC → `_start_npc_encounter` sets
   `STATE_NPC_ENCOUNTER`, phase `text`.
2. ENTER → phase `options`. Three buttons appear with `label` only
   (**no karma or outcome preview** — "Options show action +
   justification only — no outcomes, no karma labels").
3. 1/2/3 → `_apply_npc_choice`:
   - Costs applied (`_get_filtered_inventory` surfaces item-pick for
     consumable costs).
   - Rewards applied via `_apply_npc_reward`.
   - `suryas_gift` chain passive doubles reward on karma_delta > 0.
   - Karma applied with clamp.
   - Phase → `outcome` with the chosen `outcome` text.
4. ENTER → `_close_npc_encounter(resolved=True)` kills the NPC,
   adds the tag to `_encountered_npcs`, logs a chronicle line.

### 2.7 Suryas Gift doubling

`chain_passives.player_has_passive(player, 'suryas_gift')` → the
Kavacha-Kundala chain. Any NPC option with `karma_delta > 0` applies
its reward **twice** when active, with message "Surya's gift doubles
the bounty of your good deed!" (`game_encounters.py:741-750`). This is
the one chain-wide synergy with the karma system; no negative-karma
chain exists.

---

## 3. The 5 flavor NPC encounters

Flavor NPCs are **non-karmic** encounters that add world-building and
trade without touching `self.karma`. They live in
`src/flavor_encounters.py::FLAVOR_ENCOUNTERS` and share the NPC
encounter UI (`_start_flavor_encounter` sets `_npc_is_flavor = True`
to skip karma processing).

**Spawn rate**: ~40% per non-boss floor, independent of karma NPCs.
Each flavor NPC is one-shot per run (tag added to
`_encountered_flavor_npcs`).

| Tag | Name | Level range | Options |
|-----|------|-------------|---------|
| `flv_wandering_merchant` | Wandering Merchant | L2-18 | (1) Trade food → random potion. (2) Trade 50 gold → random scroll. (3) Browse — nothing. |
| `flv_old_traveler` | Old Traveler | L1-15 | (1) Share food → WIS +1 (and silent-footed Odin hint). (2) Keep food — nothing. |
| `flv_frightened_goblin` | Cowering Goblin | L1-12 | (1) Accept trinket → random accessory. (2) Give food → random accessory **+ bonus random potion**. (3) Shoo — nothing. |
| `flv_dwarven_smith` | Dwarven Smith | L21-40 | (1) Pay 80 gold → `enchant_weapon +1` on equipped weapon. (2) Decline — nothing. |
| `flv_blind_oracle` | Blind Oracle | L41-60 | (1) Pay 30 SP → `clairvoyant` 50t. (2) Ask about dungeon — three-line omen (no mechanical effect). (3) Leave quietly — nothing. |

Flavor NPCs can **also** be loaded from `data/flavor_encounters.json`
if that file exists (`flavor_encounters.py:247-249`); the five above
are the hardcoded baseline. Additional entries from the JSON extend
the pool without changing the schema.

Related non-karmic encounters that live elsewhere:

- **Svirfneblin Trader** (`MerchantNPC`, `mystery_system.py:582`) —
  a general dungeon merchant with class-weighted stock (4-6 items by
  level bracket). 20% spawn per floor. 15% chance to carry a Soul
  Sphere. Price formula: `int(_BASE_PRICE * mult * tier * weight)`,
  min 5 gold. See [items.md](items.md) for the full price table.
- **Secret Cow** (`game_encounters._maybe_spawn_cow`) — see
  [quests_mysteries §2.9](quests_mysteries.md).

---

## 4. Ethereal Unicorn + Magic Carrot

A branching sub-encounter stitched across two spawn floors.

### 4.1 Magic Dungeon Carrot

- Spawn window: **L1-19**, guaranteed, one per run.
  (`_maybe_spawn_magic_carrot`, `game_encounters.py:227`).
- Target level is picked lazily (`_rng.randint(1, 19)`) on first
  eligible floor entry, so **in v2.18 it is self-repairing**: if the
  player skips the chosen floor the first time, the carrot still
  spawns on any 1-19 floor they visit, because the lazy target is
  re-rolled only once per run but the eligibility test runs on every
  descent.
- The item is `food/magic_dungeon_carrot` (loaded from `items.json`).
- Pickup is auto-identified (`identified: True` in-template).

### 4.2 Unicorn state machine

- Spawn window: **L21-39**, once per run
  (`_maybe_spawn_unicorn`, `game_encounters.py:266`).
- Target level: `_rng.randint(21, 39)` on first eligible entry.
- Monster class: sessile allied NPC with `_is_unicorn = True`,
  `_unicorn_state = 'wary'`, `_unicorn_wait = 0`,
  `_unicorn_eat_turns = 0`, `resistances = ['magic', 'holy']`,
  200 HP (defensive — she shouldn't be reachable as a target, but
  ambient AoE could clip her).

The state machine runs in `_tick_unicorn` (every player turn) and
`_handle_unicorn_bump` (on player bump).

**States**:

| State | Trigger to enter | Behavior | Exit |
|-------|------------------|----------|------|
| `wary` | Initial | Visible-and-within-8 ticks `_unicorn_wait`. First tick: "A beautiful white unicorn stands nearby. She watches you warily." | At `_unicorn_wait >= 3`: → `relaxing`. On player bump: flees (teleports to a tile ≥4 Manhattan away). |
| `relaxing` | 3 ticks of patient observation | Watches for a Magic Carrot on any ground tile within Chebyshev distance ≤2. | On carrot found: teleports to carrot tile, enters `eating`. On player bump: → `wary`, flees. |
| `eating` | Carrot adjacent | `_unicorn_eat_turns` ticks each turn. | At `>= 2`: carrot removed from ground, → `trusting`. On player bump: → `wary`, flees. |
| `trusting` | Finished the carrot | Player may now safely approach. | On player bump: **karma check** — if karma < 0, unicorn flees permanently (`alive=False`), "She senses darkness in your heart and gallops away!"; else launches the AI escalator chain quiz. |
| `fled` | Permanent | Dead NPC; cannot be re-engaged this run. | — |

### 4.3 Unicorn quiz + boon table

Successful approach at karma ≥ 0 triggers an **AI** `escalator_chain`
quiz, `tier=1`, `max_chain=5`. Boons stack by chain tier
(`_apply_unicorn_boons`, `game_encounters.py:465`):

| Chain | Boon |
|-------|------|
| 0 | "Nuzzles your hand gently, then trots away." Unicorn `fled`, no boon. |
| 1+ | `regenerating 30t` |
| 2+ | Full HP, SP, MP restore |
| 3+ | Uncurse every cursed equipped **and inventory** item (reports count) |
| 4+ | Permanent `magic_resist` **or** `poison_resist` (random) |
| 5 | **Unicorn joins as a pet** (`UnicornPet(x, y)`), unicorn NPC removed, chronicle entry logged ("She stayed."). The pet heals, cleanses afflictions, and senses hidden traps. |

Chain < 5 (even 4): unicorn departs after granting boons
("vanishes in a shimmer of light"). Chain == 5 is the only path to
pet-form.

### 4.4 Why the AI subject?

The unicorn's "most-memorable" rule is the Recognition Pattern
(RECOGNIZE fake content / power / mechanism / figure — see
`docs/quiz/subjects/ai.md`). The unicorn as a mythic creature is
being tested by **recognition**: the player must demonstrate they
can see things clearly, which pairs thematically with the karma
check.

---

## 5. Prayer v2 (the `\` key)

Pressing `\` on any tile launches `_start_pray` (`game_divine.py:768`).
v2.13.0 collapsed the multi-prayer picker into a single theology
escalator_chain quiz with stacking bonuses.

### 5.1 Baseline

- **Quiz**: `theology`, `escalator_chain`, `tier=1`, `max_chain=5`
  (chain caps at 5 because escalator caps at T5).
- **Cooldown gate**: `self.player.prayer_cooldown` must be ≤ 0.
  Message: "You cannot pray yet. (N turns remain)".
- **Altar bump**: if standing on an ALTAR tile, `at_altar = True` and
  "The altar amplifies your prayer." is appended to the kneeling line.
- **Karma verse**: at chain tier k (1-5), prints one Bible-verse pair
  from `_KARMA_VERSES[karma_tier][k]`. Five karma tiers:
  - `saintly` (karma +6..+10): Psalm 23 line + "Well done, good and
    faithful servant" at chain 5.
  - `righteous` (karma +1..+5): Peter/Isaiah/Philippians.
  - `neutral` (karma 0): Matthew 7:7 and Proverbs 3.
  - `slipping` (karma -1..-5): "Watch and pray" through "Create in
    me a clean heart."
  - `fallen` (karma -6..-10): "The wages of sin is death" and
    "How art thou fallen from heaven, O Lucifer."

### 5.2 Chain tier bonuses (stacking)

Bonuses **stack** — chain 5 applies all five bands. Magnitudes are
modified by karma (see §5.3). Baseline amounts:

| Chain | Bonus |
|-------|-------|
| 0 | "The heavens are silent." No bonus; cooldown still set. On karma `fallen`, "Examine your conscience." |
| ≥ 1 | Restore SP: `max(15, max_sp // 4) + karma_bonus_sp` |
| ≥ 2 | Restore HP: `max(15, max_hp // 4) + karma_bonus_hp` (plus message "Warmth washes over your wounds") |
| ≥ 3 | Restore MP: `max(5, max_mp // 4) + karma_bonus_mp` |
| ≥ 4 | **Uncurse** first worn cursed item **OR**, if nothing cursed, **bless** `1 + max(0, karma // 3)` random inventory items. At karma ≤ -5 the gift is refused outright. |
| ≥ 5 | Grant `shielded` for `max(1, 20 + karma_bonus_buff)` turns (`shielded` adds +3 AC per [combat.md](combat.md)). |

### 5.3 Karma magnitude scaling

Raw karma is **doubled at an altar**:

```python
karma_for_bonuses = karma * 2 if at_altar else karma
karma_bonus_sp   = max(-15, karma_for_bonuses)        # floored at -15
karma_bonus_hp   = max(-15, karma_for_bonuses)        # floored at -15
karma_bonus_mp   = max(-5,  karma_for_bonuses // 2)   # floored at -5
karma_bonus_buff = max(-15, karma_for_bonuses * 3)    # floored at -15
```

At karma +10 on altar: bonuses are built from `+20` → +20 SP, +20 HP,
+10 MP, +60 shielded turns on top of baselines. At karma -10 on
altar: bonuses are built from `-20` → the SP "restore" drains SP
(message: "Your prayer is answered coldly — strength drains from
you"), HP "restore" damages (floored at HP 1), MP "restore" drains
MP. The system doesn't black-hole prayer; it inverts into penalty.

### 5.4 Cooldown formula

```python
effective = chain + (1 if at_altar else 0)
player.prayer_cooldown = max(100, 100 + 25 * effective)
```

- Chain 0, off altar: 100 turns.
- Chain 5, on altar: `100 + 25 * 6 = 250` turns.

Then `_apply_prayer_cooldown_quirks` halves (**stacking**) the result
once per active flag:

- `fisher_king_active` quirk (progression unlock) — halves once.
- `fisher_king_mystery_active` (the Fisher King **mystery** reward,
  see §7) — halves again.

Both active → cooldown is quartered. Reference per
`reference_engine_caps.md`: the design cooldown band is 100-280
turns before Fisher-King halving.

### 5.5 L100 holy-fire override

On `dungeon_level == 100 and at_altar` with `chain > 0`:

- Burns `chain * 2` turns of Abaddon-resist-strip. The Abaddon
  Destroyer monster's `resistances` is set to `[]` for the duration,
  surfaced by `self.abaddon_resist_removed_turns`.
- The altar's position is added to `self._l100_altars_used`. Second
  prayer at the same L100 altar: "This altar's holy power has been
  spent."
- Stacking bonuses **also** apply (holy fire does not short-circuit
  the regular chain restoration).

Message: "Holy fire surges around the Destroyer! His defenses crumble
for N turns!" or "Holy fire blazes forth but finds no target."

---

## 6. Divine Intercession (Shift+`\`)

The "big ask." One attempt per run. Gated by
`player.divine_intercession_used` (not by `prayer_cooldown`).

### 6.1 Flow

1. Press Shift+`\` → `_start_divine_intercession` checks the
   once-per-run flag; if used, "You have already sought intercession
   this run. God's ear is not for spam."
2. Otherwise, state → `STATE_INTERCESSION_PROMPT` (a Y/N confirm).
3. On `Y`:
   - `player.divine_intercession_used = True` **before** the quiz
     launches (so a failed-mid-quiz exit still counts).
   - **At altar**: `theology escalator_chain tier=1 max_chain=5`.
     Success = `score >= 1` (one correct = full win).
   - **Off altar**: `theology threshold tier=5 threshold=5 total_qs=5`.
     Success = answer all five T5 theology questions correctly.
4. On `N`: state → PLAYER, "You step back from the altar's edge."

### 6.2 Success

`_resolve_intercession_success`:

- Full HP, MP, SP restore.
- Every `DEBUFFS`-registered status effect cleared (status_effects
  purged for anything in `status_effects.DEBUFFS`).
- `invulnerable 10t` effect added.
- A **random unspawned Artifact** materializes at the player's feet.
  Primary pool: `data/items/artifact.json` entries not currently in
  play. Fallback pool: `is_unique` items across weapon / armor /
  shield / accessory not in play. Both pools preserve the
  "not duplicating a running unique" invariant via `_in_play`.
  Spawned artifact is `identified = True` and `buc = 'blessed'`.
- Chronicle entry: "God set a {name} at my feet."

### 6.3 Failure

`_resolve_intercession_failure`:

- **Every** equipped item (weapon, ranged, shield, armor slots,
  accessory slots, amulet, belt) with a `buc` field is set to
  `'cursed'` and `buc_known = True`.
- `blinded 100t` effect added.
- Chronicle: "Sought intercession without the merit. God smote me."

The intent is "intercession is strictly higher-stakes than prayer":
success is a run-defining windfall; failure is near-run-ending.

### 6.4 Interaction with karma

Divine Intercession does **not** read karma anywhere. It is a pure
theology skill check. Prayer flavor is karma-tiered, but
intercession is godly / theological / binary. The karma hook is
elsewhere — see §5.3.

---

## 7. Fisher King cooldown (`fisher_cooldown`)

Two flags share near-identical names and both halve prayer cooldown:

| Flag | Source | Lifetime |
|------|--------|----------|
| `player.quirk_progress['fisher_king_active']` | **Fisher King quirk** (`quirk_system`, long-term unlock) | Permanent once unlocked |
| `player.quirk_progress['fisher_king_mystery_active']` | **Fisher King mystery** reward (`special: 'fisher_cooldown'`) | Permanent once the mystery is completed |

Both are consumed by `_apply_prayer_cooldown_quirks`
(`game_divine.py:976`):

```python
def _apply_prayer_cooldown_quirks(self):
    p = self.player
    if getattr(p, 'quirk_progress', {}).get('fisher_king_active'):
        p.prayer_cooldown = max(1, p.prayer_cooldown // 2)
    if getattr(p, 'quirk_progress', {}).get('fisher_king_mystery_active'):
        p.prayer_cooldown = max(1, p.prayer_cooldown // 2)
```

Each halves independently and stacks. SYSTEMS_AUDIT §4 flags the
read site as "`game_divine.py:981-982` — Fisher King cooldown-halving
chain confirmed, both branches wired."

See [quests_mysteries §3.5](quests_mysteries.md) for the mystery
side: Fisher King's Hall at L58-72, theology T4 threshold 2/7, Healing
Herb key item, reward max_hp +30 **plus** `special: 'fisher_cooldown'`.

---

## 8. Altar of the Last Judgment (L99)

### 8.1 The gate

Descent from L99 → L100 is **not possible** unless all seven Seven
Seals have been broken: `_descend_stairs` short-circuits with
"Seven seals hold the Pit closed. N remain unbroken." See
[quests_mysteries §2.6](quests_mysteries.md) for how seals are
collected (kill the seven seal demons on L83, L85, L87, L89, L91,
L93, L97; pick up each `seal_of_<kind>` artifact, which adds its id
to `game.seals_broken`).

### 8.2 The altar

`_create_judgment_altar` places `judgment_altar_pos` (an ALTAR tile)
in the largest non-start room on L99. Pressing `\` on this tile
short-circuits in `_start_pray` (`game_divine.py:772-780`):

```python
if self.dungeon_level == 99:
    jpos = getattr(self.dungeon, 'judgment_altar_pos', None)
    if jpos and (self.player.x, self.player.y) == jpos:
        if hasattr(self, '_judgment_resolved'):
            self.add_message("The altar is silent. It has already spoken.", 'info')
            return
        self._judgment_resolved = True
        self._resolve_judgment()
        return
```

The altar is a **one-shot**. Praying off-tile on L99 falls through
to normal Prayer v2.

### 8.3 Resolution

`_resolve_judgment` (`game_encounters.py:956`) → calls
`npc_encounters.judge_karma(self.karma)`, routes outcome:

**`_JUDGMENT_TIERS`** (`npc_encounters.py:1989-2027`):

| Karma range | Outcome key | Narrative |
|-------------|-------------|-----------|
| -10..-6 | `abaddon_empowered` | "Michael weighs your soul and recoils. 'You have walked in darkness.' The scales crash to the ground. A terrible power surges toward the Pit below. ABADDON IS EMPOWERED BY YOUR SINS." |
| -5..-1 | `locusts_strengthened` | "Michael weighs your soul and frowns. 'Your deeds are wanting.' The scales tip toward shadow. A buzzing fills the air. THE LOCUST SWARMS GROW LARGER AND MORE NUMEROUS." |
| 0 | `silence` | "The scales balance perfectly — and remain cold. 'You have done nothing worthy of praise or condemnation.' The altar falls silent. You receive nothing." |
| +1..+9 | `scales_granted` | "'You have walked in light.' The scales glow with golden fire. They lift from the altar and float into your hands. YOU RECEIVE THE SCALES OF MICHAEL." |
| +10 | `sword_and_scales` | "Michael descends in a pillar of white fire. He kneels... 'Rise, Paladin. Chosen of God. The Destroyer will know your name.' YOU RECEIVE THE SWORD AND SCALES OF MICHAEL. YOU ARE ANOINTED PALADIN AND CHOSEN OF GOD." |

### 8.4 Mechanical outcomes

`_resolve_judgment` applies:

- **sword_and_scales**: `self.player_title = 'Paladin'`,
  `sword_of_michael` weapon spawned into inventory (identified),
  `scales_of_michael` artifact spawned (identified), chronicle entry
  logged. State → `STATE_JUDGMENT` (show the text, press ENTER to
  dismiss).
- **scales_granted**: `scales_of_michael` only. Chronicle entry.
- **silence**: Nothing. Chronicle beat omitted.
- **locusts_strengthened**: `self._locusts_strengthened = True`.
  L100 generation reads this flag and emits larger locust swarms.
  Message: "The buzzing of locusts grows louder in the deep..."
- **abaddon_empowered**: `self._abaddon_empowered = True`. L100
  Abaddon spawns at **+50% HP** and gains an extra attack. Message:
  "A dark power surges into the depths below..."

The Judgment altar is independent of Prayer v2's cooldown — it does
not consume `prayer_cooldown` and does not touch `_karma_tier` verses.
It is its own, final theological object.

### 8.5 Reaching karma +10

Judgment at +10 requires **ten** `+1` NPC options across the run.
The maximum achievable count is 10 (one encounter per block, 10
blocks). SYSTEMS_AUDIT §3 flags this as "reachable but fragile" —
any `0` or `-1` option in any block means +10 is unreachable, and
some +1 options cost real resources (`sir_aldric` accepts a cursed
lodestone; `ghost_grave` costs max_hp -15; `trapped_seraph` costs a
scroll; `cursed_scholar` costs 20% HP; `weeping_mother` costs 60
SP; `fairy_jar` costs a potion; `forgotten_prisoner` costs 150 gold;
`fallen_paladin` costs 200 gold; `azarael_demon` costs a scroll).

A compounding wrinkle: Penitent's Blade's `kill_count_karma_adjust`
adds +1 to karma per N kills while equipped, which can push a
karma-negative player back to 0 (`combat.py` only fires at karma < 0).
This is the one non-NPC way to budge karma.

---

## 9. Bones + karma

Bones files (3-slot ring at `bones/bones_L<N>.json`) are written on
`_on_game_over`. Per SYSTEMS_AUDIT §4, bones **do not currently
carry a karma penalty on return**. The system is cosmetic + loot:

- Previous player's name becomes "Ghost of X".
- Previous player's dropped gear becomes cursed loot on the floor.
- First equipped item is marked "preserved."
- `save_bones` persists `player.level` which doesn't exist on
  `Player`, so ghost damage collapses to `1d4+1` regardless of
  previous player depth. Ghosts are "trivial from L1 through L100"
  per audit. P1 fix listed, not yet applied.
- Encountering a bones-level does **not** apply any `karma` delta.
  There is no karma-on-death bookkeeping.

Chronicle-level consequence only: see `_log_chronicle` entries for
disturbed graves (geography quiz) and the general
"I'm not proud of it" line on grave-dig.

For the full bones/ghost pipeline see [world.md](world.md).

---

## 10. Where things live (file index)

```
src/npc_encounters.py        -- ENCOUNTERS (30 moral), _BLOCKS,
                                select_encounter_levels,
                                get_trigger_item_levels,
                                can_pay_cost, get_inventory_filter,
                                _JUDGMENT_TIERS, judge_karma,
                                _KARMA_SPRITES
src/flavor_encounters.py     -- FLAVOR_ENCOUNTERS (5 baseline),
                                select_flavor_encounters,
                                data/flavor_encounters.json loader
src/game_encounters.py       -- _maybe_spawn_npc, _maybe_spawn_flavor_npc,
                                _start_npc_encounter,
                                _start_flavor_encounter,
                                _apply_npc_choice, _apply_npc_reward,
                                _generate_npc_reward_item,
                                _create_specific_npc_item,
                                _grant_burden_item,
                                _close_npc_encounter,
                                _maybe_spawn_magic_carrot,
                                _maybe_spawn_unicorn, _tick_unicorn,
                                _handle_unicorn_bump,
                                _start_unicorn_quiz, _apply_unicorn_boons,
                                _unicorn_flee,
                                _resolve_judgment, _maybe_spawn_cow
src/game_divine.py           -- _start_pray, _resolve_simple_prayer,
                                _apply_prayer_cooldown_quirks,
                                _show_prayer_verse, _karma_tier,
                                _KARMA_VERSES,
                                _start_divine_intercession,
                                _confirm_divine_intercession,
                                _resolve_intercession_success,
                                _resolve_intercession_failure,
                                _spawn_intercession_artifact,
                                _altar_drop_reveal
src/pet_system.py            -- UnicornPet
src/chain_passives.py        -- player_has_passive('suryas_gift')
                                reward-doubling hook
src/main.py                  -- self.karma init (L263), save/load (L597),
                                karma_disappear_proc (L1619)
```

---

## 11. Related reading

- [quests_mysteries](quests_mysteries.md) — Seven Seals quest chain,
  Judgment altar's quest side, Fisher King mystery.
- [items](items.md) — Sword/Scales of Michael, Chandrahasa family,
  cursed Lodestone, Pandora Key, Ring of Command, Penitent's Blade,
  Officer's Signet.
- [progression](progression.md) — Fisher King quirk, Odin / Hermes /
  Prometheus / Scheherazade / Merlin quirk hints (surfaced by
  Oracle), the Paladin title.
- [world](world.md) — Bones ring, dungeon generation.
- [combat](combat.md) — `invulnerable`, `shielded`, blinded,
  Penitent's Blade `kill_count_karma_adjust`, Chandrahasa
  `karma_disappear_proc`.
