# A2 Cross-System Integration Bug Bash

Audit of how mature systems interact. Surface: save/load, state transitions,
derived stats, masteries, identify, status effects, combat hooks, level
transitions, equipment loops, spell dispatch.

Tools used: targeted greps + read of the key files identified in the prompt
(`src/save_system.py`, `src/main.py`, `src/player.py`, `src/game_magic.py`,
`src/game_menus.py`, `src/status_effects.py`, `src/chain_passives.py`,
`src/chain_equip.py`, `src/level_manager.py`, `src/monster_classes.py`,
`src/items.py`, `proposals/v2_audit/07_systems.md`,
`proposals/v2_audit/IDENTIFY_SYSTEM.md`).

Status of memory note (`project_identify_rebuild_2026_05_17`): MOST mastery
kinds called out as "no at-site hook" ARE wired today (`class_acc_ac_bonus`,
`class_acc_regen_bonus`, `class_acc_passive_radius`, `class_acc_resist_bonus`,
`class_acc_sp_burn_bonus`, `class_acc_quirk`, `class_scroll_potency`,
`class_scroll_persist`, `class_scroll_extra_uses`, `potion_potency_bonus`,
`potion_duration_bonus`, `gold_finds_pct`, `resurrect_to_full`). Two kinds
remain unwired (see Finding M1). Spell handler audit in `07_systems.md` is
LARGELY out of date — the 10 missing spell effects all have handlers now
(`game_magic.py` 1137-1599). Carry-forwards from those audits are noted
where still relevant.

---

## CATEGORY A: SAVE/LOAD ROUNDTRIP

### [CRITICAL] Per-floor "consumed charge" Game-side flags not pickled — save/reload exploit
**Systems**: save_system → game per-floor state
**File(s)**: `src/save_system.py:22-90`, `src/main.py:740-744`, `src/game_combat.py:1378-1389`
**What I see**: Four per-floor one-shot charges live on `self` (the Game), not on the player object, and are NOT in the save dict: `_first_hit_used` (Babr-e Bayan), `_death_save_used` (Jade Cicada), `_tarnhelm_used` (Tarnhelm), `_quiz_reroll_used` (Tablet of Destinies). Each callsite reads via `getattr(self, '_xxx_used', False)`, so on reload (where these are missing from `state` and never restored in `load_state`) they default to False — i.e. the per-floor charge is fully refreshed.

`level_mgr` IS saved, and `_chain_passive_charges` lives on the player (so it IS saved via pickle of the Player object). The Game-side charges were never added to either persistence path.
**Reproducer / when it triggers**: 1. Equip Tablet of Destinies. 2. Pick a fight; use the reroll on a wrong combat answer. `_quiz_reroll_used = True`. 3. Save & quit. 4. Reload. 5. Pick another fight on the same floor; reroll is available again.
**Suggested fix**: Add these four fields to `save_game` state dict and `load_state` (mirroring the other per-floor flags around line 477). Or move them onto the player object so pickle catches them.
**Confidence**: HIGH

### [CRITICAL] `_cow_return_level` not saved — cow-level escape goes to L0
**Systems**: save_system → cow-level state
**File(s)**: `src/save_system.py:67-71`, `src/main.py:127`, `src/game_encounters.py:91, 110`
**What I see**: `_cow_return_level` is set in `_enter_cow_level` (game_encounters.py:91) to remember where to come back to. It's NOT in the save dict (only `_cow_level`, `_cow_spawned`, `_cow_level_done`, `_cow_poke_count` are saved). The constructor default is `0` (`main.py:127`). If the player saves while on the cow level and reloads, `_cow_return_level` is restored to 0, and `_exit_cow_level` then calls `_change_level(0, ...)` — descending into nothing.
**Reproducer / when it triggers**: Save while on the secret cow floor → reload → take the portal → game tries to load level 0.
**Suggested fix**: Add `'_cow_return_level': getattr(game, '_cow_return_level', 0)` to the save dict, and restore in `load_state`.
**Confidence**: HIGH

### [WARN] `_lore_subject` and other transient pointers not saved
**Systems**: save_system → STATE_LORE
**File(s)**: `src/save_system.py:22-84`, `src/main.py:91, 4946`
**What I see**: `_lore_subject` is the pointer that `_draw_lore_screen` reads to render the lore overlay. It is not saved. If the player saves WHILE on STATE_LORE — they can press ESC to exit the lore screen before saving, so this is mostly only triggered by reload-into-the-middle of the lore reveal. Same applies to `_active_mystery_altar` (not in save). The game uses ESC to leave LORE state, so the user would need to save from the LORE screen via a non-standard path.
**Reproducer / when it triggers**: Edge case. Save (programmatically) while STATE_LORE is current → reload puts you in STATE_LORE with `_lore_subject=None` → render error.
**Suggested fix**: On `load_state`, force state to STATE_PLAYER (currently it implicitly is, but `_lore_subject` ref is gone anyway). Defensive: `_draw_lore_screen` should bail if `_lore_subject is None`.
**Confidence**: MEDIUM

### [MINOR] `_chronicle_abaddon_start` flag not saved
**Systems**: save_system → chronicle dedup
**File(s)**: `src/save_system.py:22-84`, `src/game_combat.py:1351-1353`
**What I see**: `_chronicle_abaddon_start` is a one-shot guard so the Abaddon-encounter chronicle line only fires once. Not saved → reload mid-floor → chronicle line will duplicate next time Abaddon is engaged.
**Reproducer / when it triggers**: Engage Abaddon, save, reload, engage again — chronicle line fires twice.
**Suggested fix**: Add to save dict.
**Confidence**: HIGH

---

## CATEGORY B: STATE TRANSITION CLEANUP

### [CRITICAL] ESC from spell-target state leaks `_pending_spell` and BURNS MP without casting
**Systems**: game_input (ESC) → game_magic (spell cast)
**File(s)**: `src/game_input.py:90-103`, `src/game_magic.py:1060-1067`
**What I see**: A targeted spell flow:
1. `_cast_spell` deducts MP at line 1060 BEFORE entering STATE_TARGET.
2. Sets `_pending_spell`, `_pending_spell_id`, enters STATE_TARGET.
3. ESC handler at `game_input.py:92-102` clears `_pending_wand`, `_pending_power`, `_pending_pet_special` — but NOT `_pending_spell` or `_pending_spell_id`.
4. MP is gone, spell is cancelled, no refund.

Net: cancelling a targeted spell mid-aim costs MP for nothing. And the dangling `_pending_spell` remains — would only be reused if the player happens to start ANOTHER spell flow that funnels through the same confirm path; rare but not impossible.
**Reproducer / when it triggers**: Cast Magic Missile, see the targeting cursor, hit ESC → mana was burned but no spell fired and no message acknowledges the cost.
**Suggested fix**: In the STATE_TARGET ESC branch, refund MP if `_pending_spell` is set, then null both `_pending_spell` and `_pending_spell_id`.
**Confidence**: HIGH

### [WARN] STATE_LORE exit does not clear `_lore_subject`
**Systems**: game_input → render state
**File(s)**: `src/game_input.py:960-962`
**What I see**: `_lore_input` flips to STATE_PLAYER but doesn't `self._lore_subject = None`. Pointer dangles until next overwrite. Harmless for render (only painted in STATE_LORE) but it's an integration smell — the next assignment is at `_identify_unique_item` callback, `_examine_corpse_direct`, etc., so the dangling ref also keeps a strong reference alive, blocking GC of items removed from inventory.
**Reproducer / when it triggers**: Identify item to lore, ESC out, sell/drop the item — `_lore_subject` still holds a reference until the next identify.
**Suggested fix**: `_lore_input`: `self._lore_subject = None` on exit.
**Confidence**: MEDIUM

### [MINOR] STATE_IDENTIFY_MENU does not null `identify_menu_items` on exit
**Systems**: game_menus → identify menu state
**File(s)**: `src/game_menus.py:677, 700`
**What I see**: `identify_menu_items` is populated at open, never cleared on close. Harmless because every open path resets it, but the same dangling-ref smell as STATE_LORE.
**Confidence**: LOW

---

## CATEGORY C: DERIVED STAT RECOMPUTATION

### [CRITICAL] `_claim_monster_family_mastery` `int_bonus` stomps chain-equip max_mp_bonus
**Systems**: identify (mastery) → player.max_mp
**File(s)**: `src/main.py:4993-4996`
**What I see**: Aberration family blessing (`kind = 'int_bonus'`) is applied with:
```python
self.player.INT += int(blessing.get('value', 0) or 0)
self.player.max_mp = self.player.BASE_MP + self.player.INT
```
This direct assignment STOMPS any prior `max_mp` bonuses applied by chain-equip mp_bonus / max_mp_bonus passives (e.g. Robe of the Magus), permanent accessory effects, or one-shot wonder/wish stat bumps. If `BASE_MP + INT < current max_mp`, mp will silently drop, then `mp = min(mp, max_mp)` is also missing here, so mp could exceed max_mp.
**Reproducer / when it triggers**: 1. Equip Robe of the Magus → tier 5 → +50 max_mp (passive `max_mp_bonus: 50`). 2. Identify an aberration corpse to chain-5 → `int_bonus` mastery fires. 3. max_mp drops from (BASE+INT+50) to (BASE+INT+1), losing 49 max_mp.
**Suggested fix**: Use `self.player.apply_stat_bonus('INT', value)` — that path correctly increments both INT and max_mp WITHOUT clobbering other contributors. Mirrors the celestial `wisdom_bonus` style on the line above (which uses `+=` not assignment).
**Confidence**: HIGH

### [WARN] `apply_stat_bonus('STR', -N)` does not clamp `sp` after dropping `max_sp`
**Systems**: status_effects (disease) → player.sp
**File(s)**: `src/player.py:771-786`, `src/status_effects.py:340-345`
**What I see**: `apply_stat_bonus` clamps `hp` when CON changes and `mp` when INT changes — but does NOT clamp `sp` when STR changes:
```python
elif stat == 'STR':
    self.max_sp += amount      # no sp = min(sp, max_sp)
```
Disease can drain STR (`status_effects.py:343-344`) at random; if sp was at max_sp, after the drain `sp > max_sp` until the next event that touches sp.
**Reproducer / when it triggers**: Full SP at max, get diseased, RNG hits STR drain — sp now exceeds max_sp until next combat/cook tick.
**Suggested fix**: Add `self.sp = min(self.sp, self.max_sp)` to the STR branch.
**Confidence**: HIGH

### [MINOR] `apply_stat_bonus` lacks the AC max-clamp / negative guard
**Systems**: status_effects/items → player AC
**File(s)**: `src/player.py:773-776`
**What I see**: `apply_stat_bonus('AC', amount)` just adds to `_accessory_ac_bonus`, never clamps. Two diseases stacking + cursed gear could theoretically push the bonus arbitrarily — but AC is recomputed each call via `get_ac`, so this doesn't matter mechanically. Cosmetic / consistency.
**Confidence**: LOW

---

## CATEGORY D: MASTERY HOOKS

### [WARN] Two mastery kinds still have no read site
**Systems**: identify mastery → use-site queries
**File(s)**: `src/game_magic.py:2698`, `src/class_masteries.py:359`
**What I see**: Memory note `project_identify_rebuild_2026_05_17` flagged a long list of mastery kinds with no at-site hook. Most are now wired (see header). Two remain:
- `accessory_buff_duration_bonus` — emitted as the unique-accessory default blessing at `game_magic.py:2698`. No reader anywhere in `src/`. Player sees "Buffs from the X last 5 turns longer" but nothing fires.
- `class_acc_buff_duration_bonus` (the class-level twin) IS read at `player.py:468` — that one works.

The unique-default fallback is `accessory_buff_duration_bonus`, so any legendary unique accessory whose `mastery_blessing` is None falls into this path and silently no-ops.
**Reproducer / when it triggers**: Identify a unique accessory that lacks an explicit `mastery_blessing` in JSON → chain-5 → message says +5 turn buff duration → effect is fake.
**Suggested fix**: Either (a) wire a reader for `accessory_buff_duration_bonus` in `player.add_effect` alongside the `class_acc_buff_duration_bonus` block, or (b) change the default at `game_magic.py:2698` to a class-keyed kind that is read.
**Confidence**: HIGH

### [WARN] `buff_duration_bonus` (bare) inner kind has no reader
**Systems**: items.json mastery_blessing → use-site
**File(s)**: `data/items/accessory.json:4228, 6454, 6654`, `src/main.py:3109-3120`
**What I see**: Three accessory entries use the shape `{"kind": "accessory_passive_strength", "value": {"kind": "buff_duration_bonus", "value": N}}`. The OUTER kind (`accessory_passive_strength`) IS read at `main.py:3109,3120` — but those readers only match inner `gold_multiplier` / `gold_finds_pct` / `passive_regen_bonus`. Inner `buff_duration_bonus` has no reader. Players who chain-5 these three uniques see the mastery message, but the buff-duration effect never lands.
**Reproducer / when it triggers**: Identify one of these three uniques to chain 5 → mastery applied to player.unlocked_masteries but the kind never reads → buffs continue at base duration.
**Suggested fix**: Add a reader for the `(accessory_passive_strength → buff_duration_bonus)` shape in `player.add_effect`, or change the JSON to use a kind that has a reader. Audit the other inner kinds nested under `accessory_passive_strength` for the same gap.
**Confidence**: HIGH

---

## CATEGORY E: ITEM IDENTIFICATION CROSS-STATE

### [CRITICAL] `_propagate_identification` only touches inventory + only sets `buc_known`
**Systems**: identify → ground items, containers, id_level propagation
**File(s)**: `src/game_magic.py:3087-3121`, `proposals/v2_audit/IDENTIFY_SYSTEM.md:286-292`
**What I see**: The IDENTIFY_SYSTEM.md doc explicitly states:
> `_propagate_identification(item.id)` is called at every reveal level — it raises id_level on all OTHER instances of the same id (commons: mastery_class) to a cap (3 for uniques to preserve mastery, 5 for commons since there's no mastery to gate).

The implementation does NOT raise `id_level` on other instances. It only:
1. Adds to `known_item_ids` and `known_class_ids` sets.
2. Walks `player.inventory` only, setting `buc_known = True` on matches.

Two gaps from the doc:
- Ground items at the player's tile / in other rooms are not touched. If a Wand of Magic Missile is in inventory and another is on the floor of the same level, identifying one doesn't bump the other's id_level.
- Even within inventory, `id_level` is not raised on the OTHER copies — they remain at level 0 until separately identified.

**Reproducer / when it triggers**: Have two identical wands. Identify one to level 3 via philosophy quiz. Open the identify menu: the second wand still shows `(0/5)` and starts the quiz fresh from T1, not T4 (resume).
**Suggested fix**: In `_propagate_identification`, iterate `player.inventory + self.ground_items + [i for c in containers for i in c.contents]` (if applicable). For each item with matching `id` OR matching `mastery_class` (for commons), set `id_level = max(current, new_level)` with the cap-per-uniqueness rule from the doc.
**Confidence**: HIGH

### [WARN] `Item.identified` is a plain attribute, not the property the doc claims
**Systems**: identify → display/menu state
**File(s)**: `src/items.py:69, 80, 124, 187, 237, 270, …`, `proposals/v2_audit/IDENTIFY_SYSTEM.md:50-58`
**What I see**: IDENTIFY_SYSTEM.md §2 says:
> `Item.identified` is a **backward-compat property** that reads `id_level >= 4`. Setter: `True` raises id_level to ≥ 4; `False` resets to 0.

Reality: every subclass declares `self.identified` as a plain bool in `__init__`. There is no `@identified.property` on `Item`. The doc is wrong, OR the property is missing.

Symptom: Wand `identify` scroll effect (`game_magic.py:2118-2121`) sets `unknown.identified = True` but doesn't touch `id_level`. The identify menu's `(N/5)` marker then continues to show `(0/5)` for an "identified" item; resume rules treat it as fresh.
**Reproducer / when it triggers**: Read a scroll of identify on a Wand. Open the identify menu — Wand still listed with marker `(0/5)`, philosophy quiz starts at T1, even though the name is already revealed.
**Suggested fix**: Either (a) implement `identified` as a property on `Item` per the doc, or (b) update all scroll/wand identify paths to also `setattr(item, 'id_level', max(id_level, 4))` whenever they set `identified = True`.
**Confidence**: HIGH

### [WARN] `_auto_identify_all` caps uniques at id_level 4 but unique chain may already be at 5
**Systems**: identify → Philosopher's Stone pickup
**File(s)**: `src/game_magic.py:3134-3146`
**What I see**: `_stone_id` does `it.id_level = max(int(getattr(it, 'id_level', 0)), cap)` where `cap = 4 if is_unique else 5`. `max(...)` prevents downgrade. Good. But the comment says "Uniques cap at id_level=4 — lore is shown, but the chain-5 mastery still requires the player to run the philosophy chain quiz." That logic is fine for fresh uniques. For an already-mastered unique (id_level=5), `max(5, 4) = 5`, preserved. OK — no bug, but verify with a unique the player has already mastered before grabbing the Stone.
**Confidence**: HIGH (no bug, included as positive confirmation)

---

## CATEGORY F: STATUS EFFECT DURATION EDGE CASES

### [CRITICAL] Stacked accessory-granted status drops when ANY copy unequipped
**Systems**: items → status_effects → equipped accessories
**File(s)**: `src/main.py:3962-3963, 3973-3974`, `src/player.py:881, 901`, `src/chain_equip.py:197`
**What I see**: Many accessory categories grant a permanent status as their primary effect (8 amulet/ring kinds grant `warning`, 7 grant `searching`, 6 grant `telepathy`, 5 grant `regenerating`, etc. — see `data/items/accessory.json`).

Unequip path (`main.py:3962-3974`, `player.py:881, 901`, `chain_equip.py:197`) does:
```python
if 'status' in fx:
    self.player.status_effects.pop(fx['status'], None)
```
This pops UNCONDITIONALLY, without checking whether any other equipped item still grants that status. Wearing two Rings of Warning and unequipping ONE drops the `warning` effect entirely.
**Reproducer / when it triggers**: Equip Ring of Searching #1. Equip Ring of Searching #2 — both grant `searching` (permanent). Unequip #1. Player now has `searching` = 0; Ring #2 is still on but its status is gone.
**Suggested fix**: Refactor to "recompute status from equipped sources on equip/unequip". On any equip/unequip, iterate all currently equipped items (`weapon`, `shield`, `armor_slots`, `accessory_slots`, `amulet_slot`) and rebuild the set of permanent statuses they collectively grant. Replace the unconditional `pop` with a "remove only if no other equipped item still grants it" check.
**Confidence**: HIGH

### [WARN] Status removed early (e.g. via `pop`) bypasses on-end reversal
**Systems**: status_effects → on-expire side effects
**File(s)**: `src/status_effects.py:415-436`
**What I see**: The expire hook (status_effects.py:415-436) only fires when an effect transitions to `to_expire` (i.e. natural decrement to 0). Code paths that remove an effect via `player.status_effects.pop(name, None)` (food_system.py:466, game_menus.py:1013, etc.) BYPASS the reversal. Critical cases:
- `pop('heroism')` skips `apply_stat_bonus('STR', -2)` → STR stays +2 after the effect ends.
- `pop('brilliance')` skips INT-1/WIS-1 reversal.
- `pop('berserk')` skips STR refund (`_berserk_str_bonus`).
- `pop('stand_ac')` skips `_stand_ac_bonus`/`_stand_counter_pct` reset.

There are many `pop` sites (Rand's Heart amulet at player.py:271, prayer purge at game_divine.py:1025, etc.) that may strip these buffs early.
**Reproducer / when it triggers**: Drink Heroism potion (STR +2). Trigger an effect that pops every debuff/buff (e.g. Rand's Heart death save, prayer purge, Holy Water). STR stays at +2 permanently.
**Suggested fix**: Centralize: replace direct `pop` with a `remove_effect(player, name)` helper that runs the same end-of-tick reversal logic before deleting.
**Confidence**: HIGH

### [MINOR] Missing expire messages for several effects in EFFECT_INFO
**Systems**: status_effects display
**File(s)**: `src/status_effects.py:238-289`
**What I see**: EFFECT_INFO has 50+ entries; _EXPIRE_MSGS misses: `petrifying`, `riposte_armed`, `parry_armed`, `see_invisible`, `disint_resist`, `identify_sight`, `stand_ac`, `crit_buff`, `fear_immune`, `boomstick_aoe_next`, `life_save`, and the seven `*_resist` effects. Most are permanent and won't expire normally; `parry_armed` (2t from quarterstaff) and `crit_buff` are timed and would expire silently with no UX feedback.
**Suggested fix**: Add expire strings for the timed ones.
**Confidence**: HIGH

### [MINOR] `apply_effect` allows negative-duration immortal effects (theoretical)
**Systems**: status_effects API
**File(s)**: `src/status_effects.py:309-312`
**What I see**: If a caller passes `duration = -5` (not -1), the result is `min(current + (-5), 60)` which goes negative. The tick loop only decrements `val > 0`; negative values stay forever. No current callers pass negative non-(-1) durations, but the API surface is fragile.
**Suggested fix**: Reject `duration < -1` at the top of `apply_effect`.
**Confidence**: HIGH (no current trigger, but defensive)

---

## CATEGORY G: COMBAT → STATUS → QUIRK

### [WARN] `on_status_applied` quirk hook only fires from monster melee combat
**Systems**: combat → status_effects → quirk_system
**File(s)**: `src/game_combat.py:1899-1905`, `src/quirk_system.py:844`
**What I see**: The set-diff trick that detects "newly applied status effects after this turn's combat" only runs at `game_combat.py:1899-1905` — i.e., when a monster has just hit the player. Statuses applied by:
- Drinking a potion (food_system → add_effect)
- Reading a scroll
- Standing in a fire/lava tile  
- Chain-equip on_equip_status
- Wand backfire / cursed wand effects
- Trap effects (game_combat traps section)
… all bypass the quirk system's `on_status_applied`. Any quirk that listens for "got X status" only fires for melee-monster-applied X.
**Reproducer / when it triggers**: A quirk that tracks "got poisoned 10 times" never advances when poisoning comes from a green dragon's poison spit (poison damage type) but only when a monster melee-hits and applies the status.
**Suggested fix**: Centralize status-application accounting in `add_effect` / `apply_effect` — fire the quirk hook from there with a source-type kwarg ('combat'/'potion'/'trap'/etc.).
**Confidence**: MEDIUM (depends on which quirks actually listen; not surveyed in detail)

---

## CATEGORY H: LEVEL TRANSITION STATE

### [WARN] Per-floor death pursuer speed flag survives floor change correctly, BUT `_chronicle_abaddon_start` doesn't reset
**Systems**: level_manager → chronicle
**File(s)**: `src/game_combat.py:1351`
**What I see**: `_chronicle_abaddon_start` is set ONCE per Abaddon engagement to dedup the chronicle line. It is NOT reset on _change_level. So if the player engages Abaddon on floor 99, leaves, comes back — line never repeats. That's actually the intended behavior (chronicle = once-per-event), so this is NOT a bug. But the same lack of reset for many `_X_used` per-floor flags IS a bug (covered above).
**Confidence**: HIGH (positive confirmation, not a bug)

### [MINOR] `_notified_rooms = set()` reset per floor but not pre-saved
**Systems**: level_manager → save
**File(s)**: `src/main.py:703`, `src/save_system.py`
**What I see**: `_notified_rooms` is a set of `(cx, cy)` that the player has been notified about for special rooms. Reset on `_change_level`. Not saved — so a save mid-floor reloads with `_notified_rooms = set()` (the attribute is set to {} by `_change_level` only; the constructor sets it at `main.py:130` for the initial level, but `load_state` doesn't init it). If `load_state` brings back a saved level and `_notified_rooms` doesn't exist, accessing it later may AttributeError — let me check… actually `main.py:130` sets it in `__init__`, and `load_state` doesn't reset it, so the constructor's empty set persists. Notifications fire again on revisited rooms after reload. Cosmetic.
**Suggested fix**: Either save `_notified_rooms` or accept the re-notification cost.
**Confidence**: MEDIUM (cosmetic)

---

## CATEGORY I: EQUIPMENT LOOPS

### [WARN] `revert_tier_bonuses` strips chain-equip status unconditionally — same stack-bug
**Systems**: chain_equip → status_effects
**File(s)**: `src/chain_equip.py:196-197`
**What I see**: At chain-equip unequip, `for status_name in getattr(item, '_chain_statuses', []): player.status_effects.pop(status_name, None)`. If a chain-equip item granted `truesight`, and the player also wears a `Truesight Amulet` granting the same status permanently, unequipping the chain item pops `truesight` even though the amulet should still maintain it.
**Reproducer / when it triggers**: Equip an amulet that grants permanent `phasing`. Equip a chain-equip armor that ALSO grants `phasing` at tier 3. Take off the armor → phasing is gone, despite the amulet still being on.
**Suggested fix**: Same as Finding F-1 — convert to a "rebuild from equipped sources" approach.
**Confidence**: HIGH

### [MINOR] `_apply_equip` Accessory swap-out reverses old stat bonuses but doesn't re-sort?
**Systems**: player equip
**File(s)**: `src/player.py:887-927`
**What I see**: Note at the end: `self.inventory.sort(key=lambda i: i.name.lower())` re-sorts. Good. But the swap-out only triggers for amulets (`old_fx` reversal). For ring slots: the new ring is INSERTED into the first empty slot — no replacement. So no reversal needed. Consistent.
**Confidence**: HIGH (no bug, positive confirmation)

---

## CATEGORY J: SPELL → GAME STATE

### [WARN] `_apply_spell_effect` has asymmetric fallback: targeted = generic damage, non-targeted = silent no-op
**Systems**: game_magic spell dispatch
**File(s)**: `src/game_magic.py:1128-1942`
**What I see**: For UNTARGETED effects, the function falls through every `if effect == 'foo': return` block and then through the `if target is not None:` outer block. If `target is None` and no match, function returns implicitly — silent no-op. For TARGETED effects, there's a `else: # Fallback: generic targeted damage` at line 1934-1941 that does damage.

Memory note `project_identify_rebuild_2026_05_17` (and the 07_systems.md audit) flagged 9 untargeted spells that silently no-op. **AS OF TODAY** (verified by greps in the dispatcher), all 9 have handlers wired in — the audit is now stale. But the architectural risk remains: a typo in a future spell's `effect` string would silently fail for non-targeted and silently damage-fall-through for targeted. The asymmetry hides bugs.
**Reproducer / when it triggers**: Add a new spell with `effect: 'foo_bar'` (no handler). If `needs_target: False` → MP is burned, nothing happens, no error. If `needs_target: True` → does small damage.
**Suggested fix**: Add a fallback at the end of `_apply_spell_effect` for the non-targeted path: warn message + refund MP. Better: dispatch on a dict of effect → handler with a strict KeyError.
**Confidence**: HIGH

### [WARN] Cleanse spell only removes ONE debuff (the first in iteration order)
**Systems**: game_magic spell dispatch → status_effects
**File(s)**: `src/game_magic.py:1239-1248`
**What I see**: `cleanse_self` does `active = [e for e in player.status_effects if e in DEBUFFS]; removed = active[0]; player.status_effects.pop(removed, None)`. So you cast Cleanse with 4 debuffs — only one comes off. Even at chain 5, only one. The spell description in `spells.py` says "remove one negative status effect", so that matches description — but chain-scaling is the spec for every other utility spell. Probably intended as a single-debuff spell? Either way, it's the only spell ignoring chain. Flag for design review.
**Confidence**: MEDIUM (matches the spell's text but breaks chain-scaling consistency)

---

## CATEGORY K: BOOK-KEEPING & DOC DRIFT

### [WARN] `proposals/v2_audit/07_systems.md` is stale on spell handlers
**Systems**: audit doc → reality
**File(s)**: `proposals/v2_audit/07_systems.md:11-39`
**What I see**: The audit lists 10 missing spell handlers. As of today, all 10 (`identify_item`, `mass_sleep`, `levitation_self`, `mapping`, `phase_self`, `turn_undead`, `wish`, `annihilate`, `dispel_magic`) have handlers in `_apply_spell_effect`. Tests in `tests/test_spell_handlers.py` cover them.
**Suggested fix**: Mark the doc resolved; preserve as a regression-history note.
**Confidence**: HIGH

### [WARN] IDENTIFY_SYSTEM.md doc claims property semantics that don't exist
**Systems**: doc → code
**File(s)**: `proposals/v2_audit/IDENTIFY_SYSTEM.md:50-60`
**What I see**: The doc says "`Item.identified` is a backward-compat property". The code has it as a plain instance attribute on every subclass. (See Finding E-2.)
**Suggested fix**: Either implement the property (more work, fixes E-2) or update the doc to match reality.
**Confidence**: HIGH

---

## CATEGORY L: MISC

### [MINOR] `_pending_pet_special_pet` set but cleared only via ESC, not natural completion
**Systems**: game_combat pet specials → state
**File(s)**: `src/main.py:167`, `src/game_input.py:92-102`
**What I see**: `_pending_pet_special_pet` is set when targeting a pet special. ESC clears it (good). On confirm + execute, is it cleared? Skimmed `_confirm_power_target` and downstream — `_pending_power` is, but the pet-specific fields may not be. Low confidence — would need a deeper trace. Worth verifying.
**Confidence**: LOW

### [MINOR] `petrifying` effect has tick logic but no expire message — possible silent escape
**Systems**: status_effects display
**File(s)**: `src/status_effects.py:356-364, 238-289`
**What I see**: If the player is petrifying and CURED before the petrify-death tick fires (e.g. via a Cure Petrify scroll that pops the status), no expire message displays. The current pop-based removal path (E-2 in tick) doesn't trigger `_EXPIRE_MSGS['petrifying']` because that key doesn't exist anyway.
**Suggested fix**: Add `'petrifying': ('You feel solid again. The stone curse breaks.', 'success')` to `_EXPIRE_MSGS`. And, per Finding F-2, route all status removals through a helper that fires the message.
**Confidence**: HIGH

---

## SUMMARY COUNT

**CRITICAL** (data loss / crash / silently wrong gameplay): **6**
- A-1: per-floor charge flags not pickled (save/load exploit)
- A-2: `_cow_return_level` not saved (warp to L0)
- B-1: spell-target ESC burns MP without casting
- C-1: monster-family `int_bonus` stomps max_mp
- E-1: `_propagate_identification` is incomplete vs. doc
- F-1: stacked-status unequip drops all copies

**WARN** (probable bug not user-visible / data correctness): **12**
- A-3: `_lore_subject` not saved
- B-2: STATE_LORE doesn't clear `_lore_subject`
- C-2: `apply_stat_bonus('STR')` doesn't clamp sp
- D-1: `accessory_buff_duration_bonus` (default unique mastery) has no reader
- D-2: nested `buff_duration_bonus` inner-kind not read
- E-2: `Item.identified` not a property despite doc claim
- F-2: status `pop` bypasses on-end reversal (heroism STR, berserk STR, brilliance, stand_ac)
- G-1: `on_status_applied` quirk hook only fires from melee combat
- I-1: chain-equip revert strips shared statuses
- J-1: spell dispatcher asymmetric fallback
- J-2: Cleanse spell ignores chain (matches text, breaks pattern)
- K-1+K-2: audit/doc drift

**MINOR** (cleanup / nit): **6**
- A-4: `_chronicle_abaddon_start` not saved
- B-3: identify_menu_items not cleared
- C-3: AC bonus unclamped
- F-3: missing expire messages for several effects
- F-4: negative durations theoretically immortal
- H-1: `_notified_rooms` re-notifies on reload
- I-2: equip Accessory swap-out (positive confirmation)
- L-1: `_pending_pet_special_pet` cleanup not verified
- L-2: `petrifying` missing expire message

**Total: 6 CRITICAL + 12 WARN + 9 MINOR = 27 findings.**
