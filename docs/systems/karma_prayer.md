# Karma & Prayer

> Status: reference. Reflects v2.18.0 (`409e15d`, 2026-10-02) plus the
> deeds/karma redesign of 2026-10-17 (`DEEDS_KARMA_DESIGN.md`): the karma
> gate and the Road are both ON (`data/karma_rules.json: gate_enabled`,
> `road_enabled`).
> Scope: karma scale (-10..+10), 30 block-anchor encounters, 141
> story and flavor encounters, the Road, Ethereal Unicorn state machine, Magic
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
**-10..+10 inclusive**.

**Every change goes through `karma.adjust(game, delta, kind=, source=)`**
(`src/karma.py`); `tests/test_single_karma_entry_point.py` fails on any
other write in `src/`. The five sites today:

| Site | Call |
|------|------|
| NPC / flavor choice (`game_encounters._apply_outcome`) | `kind = karma_kind` (untyped karma is logged and ignored with the gate on) |
| Oath kept / broken (`game_encounters._keep_oath` / `_break_oath`, `setne_tomb`) | `+1` `'oath'` into the earliest open block since it was sworn / `-1` `'betray'` |
| Constancy and negative patterns (`karma.evaluate_patterns`; a negative pattern is paid on the next new floor by `karma.settle_due_patterns`, so one act never costs more than -1) | `+1` `'constancy'` (at most +2 a run) / `-1` `'pattern'` |
| Emberpup first feed | nothing with the gate on (kindness, not a weighed deed); `+1` `'legacy'` only if the gate is switched off |
| Emberpup attack | `-1`, `'cruelty'` |
| Ring of Gyges (`combat.py`) | `-1`, `'cruelty'` (each blow that lands on an innocent while invisible) |
| Penitent's Blade (`combat.py`) | `+1`, `'recovery'`: only while karma < 0, never above 0 |

With `data/karma_rules.json: gate_enabled = true` (shipped) the soul is
weighed under the **block cap**: at most **+1 per 10-floor block** from
encounter choices and oaths, first come first served
(`Game._deeds['karma']['slots']`; the block is that of the deepest floor
reached). The positive kinds are `forgo` (refusing a greater temptation),
`judgment` (only in a passed quiz beside a naive sibling), `stance` (the
right side at a visible cost), `owning` (telling the person you wronged the
truth about it, at a visible cost, only where the deeds say you did it;
Brandon, 2026-10-18) and `oath` (a kept promise fills the earliest open
block since it was sworn). Constancy (`temperance`, `faithful`,
`discerning`, `steadfast`, `honest`: persistence across blocks) pays up to
+2 a run. **Submitting to an unjust "justice" is surrender, not courage:**
before an encounter `authority` with `just: false`, a `submit` choice never
pays and walking away or resisting never costs (the validator's `unjust`
rule; ENCOUNTER_STORIES_DRAFT Part J10).
Negatives (`cruelty`, `betray`, `sacrilege`, `stance_wrong`, `pattern`) are
not block-capped, but **no single loss is bigger than one** (Brandon,
2026-10-18: "Max karma drop is -1"): `karma.adjust` clamps any bigger ask to
-1 and logs it (`karma.MAX_LOSS`), with the gate on or off, and the validator
rejects karma below -1. **Betrayal is not justice:** handing over an innocent,
someone who trusted you or a person of conscience costs -1 (`betray`, or
`cruelty` for selling a captive); handing a guilty person to lawful judgement
costs nothing, and where judgment is rewarded it still pays (Silas, Lucan).
See `DEEDS_KARMA_DESIGN.md` §11.14. A broken oath costs -1 betray; a lapsed
oath costs 0 but blocks `faithful`. Naive kindness never
gives karma and always carries a material cost; light encounters never give
karma. There is no `reckless` karma kind. Every call writes a ledger entry.
With the gate off (kept only as a switch) every kind would apply as the old
inline formulas did. See `DEEDS_KARMA_DESIGN.md` §3 and §11.

### 1.2 Starting karma

`self.karma: int = 0 # cumulative moral score (-10 to +10)` on
construction. There is no class-based starting karma — every run
begins at zero. The clamp is "hard" (not "soft"): once at +10, or
once the block's slot is filled, further +1 options are no-ops numerically but still run their cost /
reward / outcome text.

### 1.3 Journal hooks on extremes

An NPC or flavor choice that takes karma from below 8 to 8 or more
(the Sword of Michael's threshold), or that takes it to -10, writes a
`soul` line in the Journal (`game_encounters._apply_outcome`), once a
run each (`once='soul:clean'` / `'soul:cold'`, Phase 4). Only an
encounter choice triggers it (the Emberpup, Gyges and the Penitent's
Blade never do). Constancy and negative-pattern rules write their own
`soul` lines (`karma._soul_line`, text in `data/karma_rules.json`).

- Crossing to 8+: "I feel clean, as if everything I have done down
  here has counted. The dungeon feels lighter."
- Reaching -10: "Something inside me has gone cold. The
  dungeon doesn't frighten me anymore. That frightens me."

### 1.3a Where the number is shown

Only on the Judgment card (L99) and the F2 debug overlay. The Journey
screen no longer prints it (Brandon, 2026-10-17); Recall Lore
(`data/hints.json`) carries oblique hints on how the soul is weighed
instead.

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
- `_apply_outcome` with `suryas_gift` chain passive → **doubles**
  reward on positive-karma deeds, only when an award was actually
  applied (a block already filled earns no doubling).

---

## 2. The 30 block anchors

### 2.1 Overview

The dungeon is divided into **10 level blocks** of 9 levels each.
Each block has **3 candidate encounters** defined in
`data/npc_encounters.json`, loaded as `src/npc_encounters.py::ENCOUNTERS`. With the Road on
(shipped), one encounter per block binds at run start to the band's anchor slot
(`road.bind_anchors`, a floor inside the block range below), and the trigger item (if any)
is pre-spawned 1-3 levels earlier so the player can arrive with it in-hand. With the Road
off the legacy `select_encounter_levels` picks a random non-boss level in the block instead.

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
| `options` | Today 3 dicts each; the engine shows up to 4 visible (see below) |
| `sprite_id` | Monster sprite key, auto-populated from `_KARMA_SPRITES` if absent |
| `role`, `stakes`, `band` | Filled by `encounter_schema.normalise`: anchors are `anchor` / `medium` / the block's floors, flavor `story` / `light` / `[min_level, max_level]`. The renderer never reads `stakes`. |

**Schema extensions (DEEDS_KARMA_DESIGN section 4; all shipped content uses them since the
2026-10 story rewrite, ENCOUNTER_STORIES_DRAFT.md):** quiz options (`quiz` + `pass` / `fail`
outcomes, applied when the quiz ends; an exit mid-quiz settles as the fail), `requires` /
`forbids` conditions on deeds, oaths, stats, items and floor, `hidden` and `hidden_group`,
`text_variants` / `outcome_variants`, `then: "options"`, `deeds`, `oath` / `oath_keep` /
`oath_break` / `oath_release`, `person_status`, `thread` / `thread_close`, `schedule`,
`delayed`, `escort`, `fight`, `karma_kind`. Keys 1-4 pick the **visible** options.
Also `fail_by_correct`, `per_miss`, `play_all`, `oath_lapse`, `people` / `people_lines`,
`seal_door`, `expel_up`, `hostile`, `stakes` (light / medium / high) and `fight` as one
`{monster_id, count}` or a list. `tools/encounters/validate.py` (`--all`, `--budget`) checks
all of it.

Each option carries `label`, an outcome (or a quiz with `pass` and `fail`), and optionally
`cost`, `reward`, `karma` with its `karma_kind` (+1 only as forgo, judgment, owning or stance,
or through a kept oath; a loss is never more than -1, whatever the wrong), and `submit` (the
choice hands someone to the encounter's `authority`, `{"who", "just", "why"}`, or does what
it demands).
Naive kindness carries 0 and a real consequence; light encounters carry 0 throughout.

Cost types: `food`, `healing_potion`, `potion`, `scroll`, `weapon`,
`gold`, `hp_percent`, `max_hp`, `sp`, `hp`, `mp`, `random_item`,
`triggered_item`, `accept_item`, `spawn_deadite_ambush`, and (new, all a
share of the player's OWN pool) `hp_pct`, `sp_pct`, `mp_pct`,
`max_hp_pct`, `gold_pct` (a CHOSEN share has a floor, `economy.pct_cost`:
an empty purse cannot pay it), plus `triggered_item_id` (take the item with
this id from the pack or a worn slot), `stat` (lose stat points),
`armor_enchant` (the worn armour loses a point), `multi` (several costs
at once) and a `count` on item costs (give back two potions). See `npc_encounters.can_pay_cost` for the
full predicate. The `healing_potion` picker lists only potions, scrolls
and wands the player KNOWS heal (`npc_encounters.known_healer`: copy
identified or type known; bug bash 4, call 32), plus the Heal spell.
Listing true healers among unidentified items leaked what they were.

Reward items are fully identified when handed over
(`items.grant_identified`, call 7).

Reward types: `gold`, `random_weapon` / `_armor` / `_shield` /
`_accessory` / `_potion` / `_scroll` / `_food` / `_wand`, `stat`,
`specific_item`, `multi`, `message`, `effect`, `enchant_weapon`,
`hp_restore` / `sp_restore` / `mp_restore`, and the new
`hp_restore_pct` / `sp_restore_pct` / `mp_restore_pct` (a share of the
player's own maximum), `gold_pct` / `gold_pct_loss`, `armor_enchant`,
`random_artifact`, and `effect` with `floors` (lasts N floors).
Economy refactor (2026-10-17, [economy.md](economy.md)): `service`
(`{"service": "repair"}`: a person's trade, `game_traders._render_service`;
the option cannot be paid for when there is nothing to do); a `gold`
reward may carry `purse_pct` (the written sum or that share of the purse,
whichever is more: a deep temptation that bites at every depth); a `gold`
cost may be `{"share": "potion", "markup": 1.5}` (a vendor at the trader's
price on its floor) or `{"service": "repair", "points": 2}`. A `forgo`
option's karma counts only when the gold turned down was at least 10% of
the purse at the time (`economy.forgo_is_real`,
`EncountersMixin._forgone_gold`).
`economy.price_encounter` rescales gold in
`cost`, `reward`, `fail_reward`, and in nested `pass` / `fail`,
`delayed[*].reward` and escort `on_arrive` / `on_fail`.

### 2.3 Block × encounter table

Generated from `data/npc_encounters.json` (2026-10 story rewrite). One candidate per block
binds per run; a triggered anchor binds a non-triggered fallback with it.

| Block | Tag | Name | Stakes | Karma paths | Notes |
|---|---|---|---|---|---|
| 1 | `marta_ratchatcher` | Rat-Catcher | medium | cruelty (-1) |  |
| 1 | `elara_amulet` | Lost Girl | medium | forgo, cruelty (-1) | trigger `silverlight_pendant`, fallback `marta_ratchatcher` |
| 1 | `grumwald_toll` | Grumwald | medium | forgo, cruelty (-1) |  |
| 2 | `sir_aldric` | Burdened Knight | medium | oath sworn, cruelty (-1) |  |
| 2 | `tam_thief` | Young Thief | medium | judgment |  |
| 2 | `helena_cartographer` | Injured Cartographer | medium | cruelty (-1) |  |
| 3 | `marcus_sword` | Grieving Father | medium | forgo, cruelty (-1) | trigger `oathkeeper_sword`, fallback `chained_priest` |
| 3 | `last_potion` | Last Potion | medium | none | contested; tragedy: costly |
| 3 | `chained_priest` | Two Prisoners | medium | judgment |  |
| 4 | `dying_messenger` | Dying Courier | medium | oath sworn, cruelty (-1) |  |
| 4 | `old_konstantin` | Old Warrior | medium | judgment | tragedy: unsavable |
| 4 | `reliquary` | Sister Marguerite | medium | oath sworn, sacrilege (-1) |  |
| 5 | `ghost_grave` | Ghost of Hal | medium | sacrilege (-1) |  |
| 5 | `deserter` | Legion Deserter | medium | judgment, cruelty (-1) |  |
| 5 | `grain_committee` | Grain Committee | medium | stance, betray (-1: informing on the village) | stance: 3.1,3.2 |
| 6 | `blind_seer` | Blind Seer | medium | none | tragedy: unsavable |
| 6 | `trapped_seraph` | Caged Angel | medium | judgment, cruelty (-1) |  |
| 6 | `slavers_wagon` | Slaver's Wagon | medium | stance, stance_wrong (-1) | stance: 1,9 |
| 7 | `ser_brennan` | Dying Knight | medium | oath sworn, cruelty (-1) | tragedy: unsavable |
| 7 | `cursed_scholar` | Cursed Scholar | high | judgment, cruelty (-1) |  |
| 7 | `fairy_jar` | Trapped Fairy | medium | cruelty (-1), forgo |  |
| 8 | `penitent` | The Penitent | medium | judgment, cruelty (-1) |  |
| 8 | `roderic_shield` | Young Knight | medium | none | contested; trigger `lionheart_shield`, fallback `penitent` |
| 8 | `forgotten_prisoner` | Forgotten Prisoner | medium | judgment, cruelty (-1) |  |
| 9 | `fallen_paladin` | Fallen Paladin | medium | cruelty (-1) | contested |
| 9 | `azarael_demon` | Bound Demon | high | forgo, sacrilege (-1) |  |
| 9 | `live_not_by_lies` | Locust Checkpoint | medium | stance_wrong (-1), stance | stance: 1 |
| 10 | `dying_prophet` | Dying Prophet | medium | cruelty (-1) |  |
| 10 | `petrified_adventurer` | Stone Statue | medium | cruelty (-1) | escort |
| 10 | `last_merchant` | Pomfrey Quill | medium | forgo, cruelty (-1) | escort |

### 2.4 Karma deltas

The Deadite (`deadite_woman`, now a light story encounter) gives 0 on every option (P16).
The only -2s are freeing Azarael (`azarael_demon`) and giving the family to Death
(`flv_deaths_chessboard`). Oath keeps pay +1 at the keep (the altar hook for Aldric and the
Book of Thoth, or an `oath_keep` option); swearing pays nothing; a break costs -1 betray.

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

1. Player bumps the NPC → `_start_npc_encounter` (via `_npc_open`) sets
   `STATE_NPC_ENCOUNTER`, phase `text` (scene text after
   `text_variants`). A spent encounter whose NPC is still standing
   (the game was closed on the outcome page or mid-quiz) just leaves.
2. ENTER → `_npc_show_options`, phase `options`. Up to four **visible**
   options appear with `label` only (**no karma or outcome preview**).
3. 1-4 → `_apply_npc_choice`, the commit point:
   - Cost paid (`_npc_pay_cost`; `_get_filtered_inventory` surfaces
     item-pick for consumable costs).
   - Encounter marked spent (`_npc_mark_spent`).
   - A quiz option starts its quiz; its `pass` or `fail` branch is
     applied by `_npc_quiz_done`. Otherwise `_apply_outcome(option)`:
     reward, `suryas_gift` doubling, bonus reward, karma via
     `karma.adjust`, deeds, then phase `outcome`.
4. ENTER → `_npc_outcome_continue`: back to the list for a
   `then: "options"` outcome, else `_close_npc_encounter(resolved=True)`
   kills the NPC and writes a Journal line.

### 2.7 Suryas Gift doubling

`chain_passives.player_has_passive(player, 'suryas_gift')` → the
Kavacha-Kundala chain. Any encounter option whose karma award was
actually applied (a +1 that filled an open block) applies its reward
**twice** when active, with message "Surya's gift doubles the bounty of
your good deed!" (`game_encounters._apply_outcome`). This is
the one chain-wide synergy with the karma system; no negative-karma
chain exists.

---

## 3. The 141 story and flavor encounters

They live in `data/flavor_encounters.json` (no hardcoded list), loaded as
`src/flavor_encounters.py::FLAVOR_ENCOUNTERS`, and share the NPC encounter UI
(`_start_flavor_encounter` sets `_npc_is_flavor = True`). Light encounters (vendors,
moments) carry 0 karma; medium and high story encounters may offer one gated point;
`callback_only` follow-ups are placed only by an earlier choice's `schedule`.

**Placement** (the Road, shipped on): each 10-floor band has one anchor slot, one medium
slot (two in the odd bands 1, 3, 5, 7, 9), one high slot in the even bands, and the rest
light (`road.py`); a slot binds on first arrival from the encounters whose `requires` hold
then. Callbacks (`schedule`) and delayed rewards land N floors after the deed that opened
them, and The Gate (`flv_the_gate`, floors 94-98) is a run-start callback
(`karma_rules.json: run_start_schedule`) that reads `data/gate_lines.json` about the people
met on the way down. The old ~40%-per-floor roll (`select_flavor_encounters`) only places
encounters if the Road is switched off. Each is one-shot per run.

**Setne's Tomb** (`src/setne_tomb.py`, `data/setne_tomb.json`) is a sealed room on one
run-rolled floor of 45-65 and the only source of the Book of Thoth. Reading the book does
not consume it (its power is spent after one read; it shows as "Book of Thoth (Read)"). It
must be laid on an altar within its due floors (oath `thoth_return`), or the dead come for
it (`flv_dead_come_for_the_book`, hostile).

| Tag | Name | Floors | Stakes | Karma paths | Notes |
|---|---|---|---|---|---|
| `flv_singed_squire` | Singed Squire | 1-5 | light | none |  |
| `flv_frightened_goblin` | Gikk | 1-12 | light | none |  |
| `flv_rat_king_tiny` | Very Small Rat King | 1-12 | light | none |  |
| `flv_wat_lamplighter` | Wat Rowe | 1-12 | medium | oath sworn |  |
| `flv_young_scribe` | Young Scribe | 1-14 | light | none |  |
| `flv_old_traveler` | Old Traveler | 1-15 | medium | none | disguise: odin |
| `flv_wandering_herbalist` | Wandering Herbalist | 1-16 | light | none |  |
| `flv_goblin_salesman` | Brix | 1-18 | light | none |  |
| `flv_lost_merchant` | Barnaby Thrupp, Lost Merchant | 1-18 | light | none |  |
| `flv_baucis_table` | Baucis and Philemon | 2-9 | light | none | disguise: zeus |
| `flv_frightened_pilgrim` | Wynn the Pilgrim | 2-14 | light | none | escort |
| `flv_mapmaker` | Osric the Mapmaker | 2-33 | light | none |  |
| `flv_martin_dream` | Saint Martin | 2-98 | light | none | callback |
| `flv_child_with_lantern` | Tilly Hollins | 3-15 | light | none |  |
| `flv_millers_thumb` | Hob Tanner | 3-16 | medium | forgo |  |
| `flv_apprentice_alchemist` | Tibbet, Apprentice Alchemist | 3-17 | light | none |  |
| `flv_seventh_lamp` | The Seventh Lamp | 3-17 | medium | oath keep, oath break (-1) | callback |
| `flv_three_mushrooms` | Luminous Mushrooms | 3-18 | light | none |  |
| `flv_crying_bait` | Crying Girl | 4-14 | medium | judgment |  |
| `flv_charons_obol` | Drowned Girl | 4-15 | light | none |  |
| `flv_treasure_hunter_desperate` | Desperate Treasure-Hunter | 4-35 | light | none |  |
| `flv_singing_bones` | The Singing Bones | 4-40 | light | none |  |
| `flv_moneylender_purse` | Moneylender's Purse | 5-15 | medium | none | contested |
| `deadite_woman` | Moaning Woman | 5-18 | light | none |  |
| `flv_saint_martin` | Freezing Beggar | 5-18 | light | none |  |
| `flv_broken_automaton` | Broken Automaton | 5-20 | light | none |  |
| `flv_weeping_ghost` | Old Nan and the Cat | 5-20 | light | none |  |
| `flv_frozen_viper` | Frozen Viper | 6-16 | light | none |  |
| `flv_three_purses` | Father of Three | 6-19 | medium | forgo |  |
| `flv_cursed_mirror` | Ornate Mirror | 6-20 | light | none |  |
| `flv_stone_fox` | Stone Fox | 6-20 | light | none |  |
| `flv_limping_lion` | Limping Lion | 8-18 | light | none |  |
| `flv_ysolde_gate` | Ysolde | 8-21 | light | none | callback |
| `flv_davy_under_beam` | Davy Hollins | 8-22 | light | none | tragedy: costly |
| `flv_echo_voice` | The Voice in the Wall | 8-79 | light | none |  |
| `flv_diogenes_lantern` | Diogenes | 10-30 | light | none |  |
| `flv_lena_returns` | Lena | 11-45 | medium | none | callback; escort |
| `flv_ostrander_pit` | Ostrander | 12-20 | medium | none |  |
| `flv_grumwald_second_bridge` | Grumwald | 13-29 | light | none | callback |
| `flv_elspeth_comes` | Elspeth | 13-35 | medium | none | callback |
| `flv_man_who_is_owed` | Man Who Is Owed | 14-30 | medium | stance | stance: 3.9 |
| `flv_samsons_riddle` | Samson | 15-19 | high | cruelty (-1), forgo |  |
| `flv_pied_piper` | The Piper | 15-34 | high | judgment | tragedy: costly |
| `flv_aldric_cairn` | Sir Aldric | 17-35 | light | none | callback; tragedy: unsavable |
| `flv_lion_remembers` | Great Lion | 18-38 | medium | none | callback; trigger `lions_thorn`, fallback `None` |
| `flv_ostrander_lantern` | Ostrander | 19-41 | light | none | callback |
| `flv_lawspeaker_rock` | Lawspeaker's Rock | 20-38 | medium | judgment, cruelty (-1) |  |
| `flv_old_spearman` | Talkative Old Spearman | 21-26 | light | none |  |
| `flv_lost_caravan_guard` | Tarek the Guard | 21-32 | light | none |  |
| `flv_brendans_whale` | Saint Brendan | 21-34 | medium | none |  |
| `flv_wounded_scout` | Wounded Scout | 21-34 | light | none |  |
| `flv_food_vendor_dungeon` | Bramble the Vendor | 21-36 | light | none |  |
| `flv_dwarven_smith_marta` | Brunhild Irontemper | 21-38 | light | none |  |
| `flv_rust_collector` | Old Veska | 22-35 | light | none |  |
| `flv_apprentice_runescribe` | Apprentice Runescribe | 22-36 | light | none |  |
| `flv_thokk` | Thökk | 22-42 | medium | forgo | tragedy: unsavable; disguise: loki |
| `flv_trembler` | Aristodemus | 22-44 | medium | cruelty (-1) | contested; escort |
| `flv_plague_doctor` | Doctor Finch | 23-38 | light | none |  |
| `flv_robes_ambush` | Morrow | 24-34 | light | none | callback |
| `flv_battle_weary_veteran` | Calla Strand | 24-38 | light | none |  |
| `flv_exposed_child` | Exposed Child | 24-44 | medium | stance, stance_wrong (-1) | stance: 9,3.10 |
| `flv_ink_stained_scholar` | Scholar Evaine | 25-40 | light | none |  |
| `flv_gyges_ring` | Gyges | 25-46 | medium | forgo |  |
| `flv_boundary_stone` | Boundary Stone | 26-50 | medium | judgment |  |
| `flv_mnemonic_monk` | Brother Osias | 27-40 | light | none |  |
| `flv_utgard_contests` | Courteous Giant | 28-39 | medium | none |  |
| `flv_whispering_hermit` | The Hermit | 30-40 | light | none |  |
| `flv_mimirs_well` | Mimir's Well | 30-62 | light | none |  |
| `flv_sword_in_anvil` | Sword in the Anvil | 31-39 | medium | betray (-1) |  |
| `flv_damocles_feast` | Damocles | 31-56 | high | judgment |  |
| `flv_witch_finder` | The Witch-Finder | 31-65 | high | judgment |  |
| `flv_moth_woman` | The Moth Woman | 32-40 | light | none |  |
| `flv_shade_bargainer` | The Shade | 33-40 | light | none |  |
| `flv_watch_post` | Watch Sergeant | 35-53 | medium | oath keep | callback; trigger `sealed_dispatch`, fallback `None` |
| `flv_ancient_guardian_chess` | The Brass Warden | 35-70 | high | none |  |
| `flv_reliquary_chapel` | Brothers of the Deep Watch | 37-53 | medium | oath keep, oath break (-1) | callback |
| `flv_coffin_bearer` | Last Bearer | 41-47 | medium | oath sworn |  |
| `flv_false_merchant_goblin` | "Legitimate" Merchant | 41-54 | light | none |  |
| `flv_crying_giant` | Grieving Giant | 41-55 | light | none |  |
| `flv_echo_child` | Echo Child | 41-55 | light | none |  |
| `flv_philosophical_fungus` | The Thinking Mushroom | 41-56 | medium | none |  |
| `flv_two_mothers` | Two Mothers | 41-90 | medium | judgment |  |
| `flv_trapped_spirit_mason` | Weeping Mason | 42-58 | light | none |  |
| `flv_relic_broker` | Relic Broker | 43-55 | medium | oath break (-1) | callback; trigger `cuthberts_gospel`, fallback `None` |
| `flv_wandering_oracle_bone` | Oracle Bones Merchant | 43-57 | light | none |  |
| `flv_time_lost_soldier` | The Lost Soldier | 43-74 | light | none |  |
| `flv_abyss_cartographer` | Cartographer Issek | 43-75 | light | none |  |
| `flv_ormonds_granary` | Ormond's Granary | 44-55 | light | none | callback |
| `flv_bottled_constellation` | Star Merchant | 44-60 | light | none |  |
| `flv_charons_return` | Charon | 44-95 | light | none | callback |
| `flv_ghost_librarian_junior` | The Cataloguing Spirit | 44-97 | light | none |  |
| `flv_antigone` | Antigone | 45-58 | medium | betray (-1: informing on her, marked villain) | contested |
| `flv_sorrow_lantern` | Lantern of Regret | 45-58 | light | none |  |
| `flv_setne_tomb` | Setne's Tomb | 45-65 | high | oath sworn, forgo | callback; tragedy: unsavable |
| `flv_dragons_accountant` | Snerk Ledgerscale | 45-88 | medium | judgment, cruelty (-1) |  |
| `flv_disguised_dionysus` | The Merry Wanderer | 46-60 | light | none | disguise: dionysus |
| `flv_stone_singer` | Stone Singer | 46-60 | light | none |  |
| `flv_dream_weaver` | Dream Weaver | 47-60 | light | none |  |
| `flv_cuthbert_chapel` | Brother Sacristan | 48-61 | medium | oath keep | callback; trigger `cuthberts_gospel`, fallback `None` |
| `flv_pardoner` | The Pardoner | 48-80 | medium | cruelty (-1), forgo |  |
| `weeping_mother` | Weeping Mother | 50-60 | light | none |  |
| `flv_andvaris_pool` | Andvari | 50-64 | medium | cruelty (-1), forgo |  |
| `flv_disguised_hermes` | Swift Stranger | 50-64 | medium | none | disguise: hermes |
| `flv_azarias` | Azarias | 50-70 | medium | none | disguise: raphael; escort |
| `flv_the_mast` | The Mast | 52-66 | medium | none | contested |
| `flv_dead_come_for_the_book` | Neferkaptah | 54-98 | high | oath break (-1) | callback |
| `flv_socrates_cell` | Socrates | 55-70 | high | none | contested |
| `flv_thorleif_skald` | Thorleif Grimsson | 60-74 | medium | oath sworn | tragedy: unsavable |
| `flv_abyssal_wine_merchant` | Pellok the Very Lost | 61-74 | light | none |  |
| `flv_abyssal_alchemist` | Alchemist Mourne | 61-76 | light | none |  |
| `flv_mad_knight_riddle` | Sir Lorvaine the Certain | 62-77 | light | none |  |
| `flv_melancholy_old_champion` | The Last Champion | 63-98 | light | none |  |
| `flv_squire_tobyn` | Squire Tobyn | 64-78 | medium | oath keep, oath break (-1) | callback |
| `flv_echo_of_dead_wizard` | The Lingering Echo | 64-79 | light | none |  |
| `flv_skalds_stone` | Rune-Stone | 64-84 | medium | oath keep, oath break (-1) | callback |
| `flv_green_girdle` | Lady Bertilak | 65-71 | medium | forgo |  |
| `flv_vafthrudnir` | Vafthrudnir | 65-85 | high | none |  |
| `flv_crossroads_fiddler` | Crossroads Fiddler | 66-80 | medium | sacrilege (-1), forgo | disguise: devil |
| `flv_djinn_in_a_bottle` | Something in a Bottle | 66-80 | light | none |  |
| `flv_avatar_athena` | Grey-Eyed Woman | 66-90 | medium | none | disguise: athena |
| `flv_invisible_archivist` | The Unseen Archivist | 68-80 | light | none |  |
| `flv_mirror_of_past_self` | The Mirror Shade | 70-80 | light | none |  |
| `flv_deaths_chessboard` | Death | 71-98 | high | forgo, cruelty (-1) |  |
| `flv_trapped_god_fragment` | Dim Light in the Stone | 72-100 | light | none |  |
| `flv_defector` | Kneeling Herald | 80-98 | medium | judgment |  |
| `flv_humorous_imp_salesman` | Disreputable Imp | 81-92 | light | none |  |
| `flv_practical_golem_medic` | Medical Construct | 81-93 | light | none |  |
| `flv_dying_hero_berengar` | Berengar the Gold | 81-95 | light | none |  |
| `flv_final_merchant_ortolan` | Ortolan the Last Merchant | 81-98 | light | none |  |
| `flv_time_lost_general` | The General Out of Time | 83-96 | light | none |  |
| `flv_dying_oracle_cassandra` | Weeping Prophet | 84-99 | light | none |  |
| `flv_wondrous_memory_keeper` | Keeper of Last Memories | 85-100 | light | none |  |
| `flv_rolands_horn` | Roland | 86-96 | medium | oath sworn, cruelty (-1) | tragedy: unsavable |
| `flv_last_philosopher` | Boethius | 86-98 | medium | none | tragedy: unsavable |
| `flv_paladin_end` | Sir Oswin | 86-98 | light | none | callback |
| `flv_wondrous_star_being` | Fallen Constellation | 87-100 | light | none |  |
| `flv_eerie_mirror_walker` | The One Behind You | 88-100 | light | none |  |
| `flv_philosophical_entity_void` | The Enumerated Self | 88-100 | light | none |  |
| `flv_rolands_horn_gate` | The Black Gate | 91-98 | medium | oath keep, oath break (-1) | callback |
| `flv_ruth_gale` | Ruth Gale | 92-98 | light | none | callback |
| `flv_the_gate` | Old Fisherman | 94-98 | light | none | callback |

Related non-karmic encounters that live elsewhere:

- **The traders** (`MerchantNPC` in `mystery_system.py`; `traders.py`,
  `game_traders.py`, `data/traders.json`): Grindle the Deep Gnome Trader
  and five named specialists, planned once a run and placed on arrival;
  a gate camp (Old Mags Thorn, the sutler) on floors 19, 39, 59 and 79.
  They sell, buy and sell services. Deeds move their prices (a wronged
  merchant, a friend come back, a kept oath's credit, rumours of charity),
  never karma. See [economy.md](economy.md).
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
| 5 | **Unicorn joins as a pet** (`UnicornPet(x, y)`), unicorn NPC removed, Journal entry written ("She stayed."). The pet heals, cleanses afflictions, and senses hidden traps. |

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
| ≥ 4 | **Uncurse** first worn cursed item **OR**, if nothing cursed, **bless** `1 + max(0, karma // 3)` random inventory items (never treasure or a Soul Sphere, which take no blessing; named as the hero knows them). At karma ≤ -5 the gift is refused outright. |
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
- One prayer a visit (bug bash 4, ruling 25): an unanswered prayer
  (chain 0) at a fresh altar puts it in `self._l100_altars_tried`. That
  altar then honours the prayer cooldown and gives no holy fire again
  until the hero leaves floor 100 and comes back (`_change_level` clears
  the set; it is saved). It used to be retried at once until answered.

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
  Spawned artifact is `buc = 'blessed'` and fully identified
  (`items.grant_identified`: id level 5, blessing known, type known).
- Journal (`soul`): "Begged for intercession and was answered. Every wound closed, and God set a {name} at my feet."

### 6.3 Failure

`_resolve_intercession_failure`:

- **Every** equipped item (weapon, ranged, shield, armor slots,
  accessory slots, amulet, belt) with a `buc` field is set to
  `'cursed'` and `buc_known = True`.
- `blinded 100t` effect added.
- Journal (`soul`): "Begged for intercession I had not earned. God answered anyway, just not kindly." 

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
| +1..+7 | `scales_granted` | "'You have walked in light.' The scales glow with golden fire. They lift from the altar and float into your hands. YOU RECEIVE THE SCALES OF MICHAEL." |
| +8..+10 | `sword_and_scales` | "Michael descends in a pillar of white fire. He kneels... 'Rise, Paladin. Chosen of God. The Destroyer will know your name.' YOU RECEIVE THE SWORD AND SCALES OF MICHAEL. YOU ARE ANOINTED PALADIN AND CHOSEN OF GOD." |

### 8.4 Mechanical outcomes

`_resolve_judgment` applies:

- **sword_and_scales**: `self.player_title = 'Paladin'`,
  `sword_of_michael` weapon spawned into inventory (identified),
  `scales_of_michael` artifact spawned (identified), Journal entry
  written. State → `STATE_JUDGMENT` (show the text, press ENTER to
  dismiss).
- **scales_granted**: `scales_of_michael` only. Journal entry.
- **silence**: Nothing. Journal beat omitted.
- **locusts_strengthened**: `self._locusts_strengthened = True`.
  L100 generation reads this flag and emits larger locust swarms.
  Message: "The buzzing of locusts grows louder in the deep..."
- **abaddon_empowered**: `self._abaddon_empowered = True`. L100
  Abaddon spawns at **+50% HP** and gains an extra attack. Message:
  "A dark power surges into the depths below..."

The Judgment altar is independent of Prayer v2's cooldown — it does
not consume `prayer_cooldown` and does not touch `_karma_tier` verses.
It is its own, final theological object.

### 8.5 Reaching the Sword (karma +8)

The Sword of Michael needs **8** (it needed exactly 10 until the
threshold moved). Under the block cap a run can earn at most +10 from
the ten blocks (one gated +1 each, from a forgo, judgment, owning, stance
or kept oath) plus up to +2 constancy, so 8 is the reward for being
principled, careful and faithful all run, not for being kind
(`DEEDS_KARMA_DESIGN.md` §3.5). Naive kindness pays nothing; most gated
+1s cost something real, and a block already filled pays nothing more.

Outside encounters, karma moves through the Penitent's Blade
(`kill_count_karma_adjust`, +1 per N kills, only while karma < 0, never
above 0), the Ring of Gyges (-2 for striking an innocent while
invisible) and the Emberpup (-2 for attacking it; feeding it gives
nothing); all go through `karma.adjust` (§1.1).

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

Journal-level consequence only: the first grave dug writes the
"I am not proud of it" line (`once='first_grave'`).

For the full bones/ghost pipeline see [world.md](world.md).

---

## 10. Where things live (file index)

```
src/karma.py                 -- adjust (the single entry point),
                                gate_enabled, evaluate_patterns;
                                rules in data/karma_rules.json
src/deeds.py                 -- the deeds register (Game._deeds): deeds,
                                oaths, people, threads, condition check,
                                old-save migrate
src/chronicle.py             -- structured journal entries (Game._chron
                                writes them; _log_chronicle is a shim),
                                the voice lint, the Journal views and
                                "Your Story" (Roads Not Taken, this run
                                only); legacy migrate
src/encounter_schema.py      -- normalise, visible_options, text
                                variants, quiz_passed
tools/encounters/validate.py -- the encounter validator CLI
src/npc_encounters.py        -- ENCOUNTERS (30 anchors), _BLOCKS,
                                select_encounter_levels,
                                get_trigger_item_levels,
                                can_pay_cost, get_inventory_filter,
                                _JUDGMENT_TIERS, judge_karma,
                                _KARMA_SPRITES
src/flavor_encounters.py     -- FLAVOR_ENCOUNTERS (all from
                                data/flavor_encounters.json),
                                select_flavor_encounters (the legacy
                                roll, used only with the Road off; never
                                rolls a callback_only follow-up)
src/road.py                  -- the Road (road_enabled, on): slots,
                                roles, binding, callback targets, seed
src/setne_tomb.py            -- Setne's Tomb (floor 45-65 roll, sealed
                                room, seal_door / expel_up) and the Book
                                of Thoth's altar return (oath
                                thoth_return); data/setne_tomb.json
src/game_road.py             -- RoadMixin: _road_arrive (oath lapse,
                                delayed rewards, callbacks, slot
                                binding, anchor fallback), schedule
src/escort_system.py         -- Escort, EscortMixin, occupants()
src/game_encounters.py       -- _maybe_spawn_npc, _maybe_spawn_flavor_npc,
                                _start_npc_encounter,
                                _start_flavor_encounter,
                                _apply_npc_choice (commit point),
                                _apply_outcome, _npc_pay_cost,
                                _npc_quiz_done, _apply_npc_reward,
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
