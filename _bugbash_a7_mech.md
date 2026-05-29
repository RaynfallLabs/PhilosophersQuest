# Bug-bash A7 — Mechanics & balance edge cases (2026-05-28)

Findings from sweeping combat formula, identify, status effects, curse, karma,
floor progression, inventory, stack handling, boss rewards, mystery
probabilities, and pet AI.

---

## Combat / damage

### [WARN] Cursed-miss-backlash bypasses HP floor
**System**: combat
**File(s)**: `src/combat.py:213`
**Edge condition**: Cursed weapon with `cursed_miss_backlash > 0` (e.g. Tyrfing); player at low HP misses (chain == 0).
**What I see**:
```python
if weapon and getattr(weapon, 'cursed_miss_backlash', 0) > 0:
    player.hp -= weapon.cursed_miss_backlash
```
Raw subtract — does not floor at 0, does not flow through `take_damage`. If the
player is at 2 HP with a 5-damage backlash weapon, `player.hp` becomes -3, then
the next `is_dead()` check (which is `hp <= 0`) trips correctly — but the
intervening code paths that read `player.hp` see a negative value. Compare to
`returning_blow` at `combat.py:593` which correctly uses
`player.hp = max(0, player.hp - backlash)`.
**Reproducer**: Equip Tyrfing (or any weapon with `cursed_miss_backlash`). HP 2.
Attack and miss. `player.hp == -3`. Render code that does `int(hp / max_hp * 100)`
would show a negative percentage; some buff hooks check `hp <= max_hp * 0.3`
which would trigger spuriously on negative HP.
**Suggested fix**: `player.hp = max(0, player.hp - weapon.cursed_miss_backlash)`.
**Confidence**: HIGH

### [MINOR] `combat.py:357` consumes crit_buff even at value 1 (no-op condition)
**System**: combat
**File(s)**: `src/combat.py:354-357`
**Edge condition**: `crit_buff` set to 1, attack fires.
**What I see**:
```python
if getattr(player, 'status_effects', {}).get('crit_buff', 0) > 0:
    mult *= 1.5
    player.status_effects['crit_buff'] = max(0, player.status_effects['crit_buff'] - 1)
```
After consumption, `crit_buff` = 0 in the dict. The dict entry remains until
the next `tick_all` (status_effects.py:329-332 catches val == 0 and adds to
expire). Between consumption and expiry, `has_effect('crit_buff')` returns
False (it checks `!= 0`), but the entry lingers. Harmless — but if any UI
code iterates `status_effects.keys()` directly, it shows a phantom buff for
one tick.
**Reproducer**: Save inspection mid-turn after a crit_buff attack would show
`crit_buff: 0` in the dict.
**Suggested fix**: `pop()` the entry when it hits 0:
```python
new_val = player.status_effects['crit_buff'] - 1
if new_val > 0:
    player.status_effects['crit_buff'] = new_val
else:
    player.status_effects.pop('crit_buff', None)
```
**Confidence**: MEDIUM

### [MINOR] `crit_buff` with permanent (-1) value silently doesn't apply
**System**: combat
**File(s)**: `src/combat.py:354`
**Edge condition**: Status `crit_buff` accidentally set to -1 (permanent).
**What I see**: The `> 0` check at line 354 returns False for -1. The buff
exists per `has_effect()` (which checks `!= 0`) but doesn't fire in combat.
Same pattern applies to `berserk` at line 359. Currently no code sets these
to -1, but a future feature granting "permanent crit" would break.
**Suggested fix**: Compare `!= 0` to match `has_effect()` semantics, or
explicitly carve out the consume path: `if val == -1 or val > 0:`.
**Confidence**: LOW

---

## Status effects

### [WARN] `shielded` status description claims "+2 AC; physical damage halved" — only AC is wired for player
**System**: status
**File(s)**: `src/status_effects.py:82` (description), `src/player.py:514`, `src/player.py:165-205` (take_damage)
**Edge condition**: Player has `shielded` status (cast Mage Armor / Magic Shield / Stoneskin).
**What I see**: status_effects.py:82 describes shielded as "+2 AC; physical
damage halved". spells.py:40 describes Mage Armor as "Shimmering force gives
+2 AC, halves physical damage for 12 turns." But `player.take_damage` never
checks `shielded` — only `+2 AC` (player.py:514). The "physical damage
halved" half of the contract is missing on the player side. On monsters
(combat.py:275), `shielded` halves incoming damage. Asymmetric.
**Reproducer**: Cast Mage Armor (`shield_self` effect). Take a 10-physical-damage
attack. Player loses 10 HP (or 10 minus armor resistances) — not 5.
**Suggested fix**: In `player.take_damage`, add a halve-physical block:
```python
if damage_type == 'physical' and self.has_effect('shielded'):
    amount = (amount + 1) // 2  # round up so 1 damage stays 1
```
**Confidence**: HIGH

### [WARN] Quiz timer can become 0 or negative at very low WIS
**System**: quiz / status
**File(s)**: `src/player.py:610-615`
**Edge condition**: WIS drained to negative via repeated `diseased` ticks
(`status_effects.py:344`) or `drain_wis` potions (`food_system.py:633`).
WIS has no lower floor in `apply_stat_bonus` (`player.py:771-785`).
**What I see**:
```python
def get_quiz_timer(self, subject: str = 'math') -> int:
    base, wis_scale = self.SUBJECT_TIMER.get(subject, (10, 1.0))
    return round(base + self.WIS * wis_scale)
```
At math (base 8s, scale 0.8), WIS = -10 gives 0s. WIS = -20 gives -8s. The
quiz timer immediately expires. Combat becomes literally unplayable —
player can't ever answer a math question. There's no `max(MIN_TIMER, ...)`.
The `timer_modifier` (player.py:619) has a 0.40 floor multiplier, but base * 0
is still 0.
**Reproducer**: Drink ~10 cursed potions of `drain_wis`. WIS goes to 0 or
negative. Try to attack a monster — quiz times out before you can read it.
**Suggested fix**: Floor the timer:
```python
return max(3, round(base + self.WIS * wis_scale))  # 3-second minimum
```
**Confidence**: HIGH

### [MINOR] `MAX_EFFECT_DURATION` cap (60) silently truncates legitimate long buffs
**System**: status
**File(s)**: `src/status_effects.py:14, 312`
**Edge condition**: Player casts a spell that grants 30 turns of regenerating
while already at 35 turns remaining.
**What I see**:
```python
player.status_effects[effect] = min(current + duration, MAX_EFFECT_DURATION)
```
With MAX = 60, current = 35, duration = 30 → result = 60 (truncated from 65).
Mostly harmless, but `_resolve_specific_prayer` at game_divine.py grants
multi-tier buffs that can add up to 50 turns of a single status; combining
two of these silently drops 40 turns. Not visible to the player.
**Suggested fix**: Either lift the cap to 120 for buffs, or surface a "You
feel the effect at its strongest!" message when truncation hits.
**Confidence**: LOW

---

## Inventory / stacks

### [WARN] Stack-merge silently drops BUC of incoming item when stacks have hidden BUC
**System**: inventory / identify
**File(s)**: `src/player.py:746-754`
**Edge condition**: Player has stack of 3 healing potions (hidden BUC,
underlying BUC = 'cursed'). Picks up another healing potion (hidden BUC,
underlying = 'blessed'). Stacks merge into 4 with the existing stack's BUC.
**What I see**:
```python
both_known = getattr(existing, 'buc_known', False) and getattr(item, 'buc_known', False)
if both_known and getattr(existing, 'buc', 'uncursed') != getattr(item, 'buc', 'uncursed'):
    continue  # known-different BUC: separate stacks
existing.count = getattr(existing, 'count', 1) + getattr(item, 'count', 1)
```
Stacks only stay separate if BOTH BUCs are known and differ. Otherwise the
incoming item's BUC silently disappears — the stack carries only one BUC for
4 potions that originally had two distinct BUCs.
**Reproducer**: Spawn in a cursed potion of healing and a blessed potion of
healing (same id, different BUC). With BUC hidden on both, they merge. Drink
one — the player sees the existing stack's BUC effect, not the average. The
blessed potion is effectively lost.
**Suggested fix**: When merging unidentified-BUC potions, either keep stacks
separate always (safer), or randomise which BUC the merged stack carries.
**Confidence**: MEDIUM

### [WARN] Ranged-attack ammo consumed before quiz; ESC wastes the arrow
**System**: combat / inventory
**File(s)**: `src/game_combat.py:1290-1294`
**Edge condition**: Player fires bow at monster. Quiz starts. Player presses
ESC to cancel.
**What I see**:
```python
# Decrement stack or remove
if getattr(ammo_item, 'count', 1) > 1:
    ammo_item.count -= 1
else:
    self.player.inventory.remove(ammo_item)
```
This runs BEFORE `quiz_engine.start_quiz`. ESC cancellation
(`game_input.py:71` `quiz_engine._end(success=False)`) calls the on_complete
callback with chain 0 — which is treated as "miss" — but the ammo is gone.
Compare to wands: `wand.charges -= 1` is INSIDE `on_complete` and only fires
on `result.success` (`game_magic.py:233`).
**Reproducer**: Have 10 arrows. Fire at monster. ESC. Inventory shows 9
arrows. Repeat 9 times. You're out of ammo without firing a single shot.
**Suggested fix**: Move ammo decrement into `on_complete` after `chain > 0`.
On chain==0 (miss/cancel), refund the ammo.
**Confidence**: HIGH

### [WARN] Spell MP consumed before quiz; ESC wastes MP
**System**: magic / inventory
**File(s)**: `src/game_magic.py:1060, 1074`
**Edge condition**: Player casts spell. ESC during quiz.
**What I see**: `self.player.mp -= mp_cost` is at line 1060 (targeted) and
1074 (non-targeted), BEFORE `_start_spell_quiz`. ESC during the spell quiz
loses the MP. The `11_edge_cases.md` audit (#10) explicitly claims "MP is
consumed only on success path" but the code shows otherwise.
**Reproducer**: Have 10 MP. Cast Magic Missile (4 MP). ESC. MP shows 6.
Repeat 2× until you have 2 MP and can't cast anything.
**Suggested fix**: Either move MP debit into `on_complete` (gated on
`chain > 0`), or refund MP on ESC by inspecting `result.score == 0`. Update
`11_edge_cases.md` to reflect reality.
**Confidence**: HIGH

### [MINOR] Carry-limit boundary at exactly the limit accepts items
**System**: inventory
**File(s)**: `src/player.py:742`
**Edge condition**: Player at exactly carry-limit (e.g. 100/100) tries to
pick up a 0-weight item OR an item that would push total to exactly the limit.
**What I see**: `if item_weight + self.get_current_weight() > self.get_carry_limit():`
uses strict `>`. Item weight 0 + current weight 100 = 100, which is NOT
> 100, so the item is accepted. Same for any pickup whose new total exactly
equals the limit. That's the intended "you can hold up to the cap" behavior,
but `current_weight` returns FLOAT, while `carry_limit` returns INT. Floating
point arithmetic could push 99.999... > 100 spuriously, or 100.0001 <= 100
to silently accept overweight. Latches on very-small-weight items
(potions, ingredients of weight 0.5).
**Reproducer**: Have 99.5 weight, pick up 0.5-weight item. Total becomes 100.0
(or 99.9999... due to float imprecision). Marginal cases possible.
**Suggested fix**: Round to a known precision or use Decimal for weights.
Minor — current code rarely hits this in practice.
**Confidence**: LOW

---

## Cooking softcap

### [WARN] Cooking HP softcap doesn't truly cap at low floors
**System**: cooking / balance
**File(s)**: `src/player.py:388-402, 321-339`
**Edge condition**: Player at F1 cooks ingredients repeatedly.
**What I see**:
```python
def cooking_softcap(self) -> int:
    idx = max(0, min(100, self.deepest_floor_reached))
    return max(1, self._COOKING_SOFTCAP_BY_FLOOR[idx])  # floor 1-10 returns 1

def increase_max_hp(self, amount, from_cooking=False):
    if from_cooking:
        softcap = self.cooking_softcap()
        cap_factor = max(0.20, 1.0 - self.cooking_hp_gained / softcap)
        amount = max(1, int(amount * cap_factor))   # ← floor at 1 breaks the cap
        self.cooking_hp_gained += amount
    self.max_hp += amount
```
At F1, softcap = 1. `cooking_hp_gained` starts at 0. First cook of a 5-HP
recipe: cap_factor = max(0.20, 1 - 0/1) = 1.0 → applied = 5 HP. Now
cooking_hp_gained = 5. Next cook: cap_factor = max(0.20, 1 - 5/1) = 0.20 →
applied = max(1, int(5 * 0.20)) = 1 HP. Every subsequent cook always grants
≥ 1 HP because of the `max(1, ...)` floor. There is no actual ceiling.
**Reproducer**: Stay on F1 (or any low floor). Harvest 50 corpses (or use a
cheat). Cook each. Player's max HP grows by ~50 + (first cook's full amount)
even though the F1 softcap is 1.
**Suggested fix**: Either drop the `max(1, ...)` floor so applied can go to
0 when cap_factor is too small, or use a strict cap: `applied = min(amount,
max(0, softcap - cooking_hp_gained))`.
**Confidence**: HIGH

### [MINOR] Per-stat cooking cap uses a hard ceiling but the API floors at 1 anyway
**System**: cooking / balance
**File(s)**: `src/player.py:363-386`
**Edge condition**: Player has already hit per-stat softcap (e.g. STR at 15
on F100) and cooks again.
**What I see**:
```python
applied = max(1, scaled) if amount >= 1 and headroom > 0 else 0
applied = min(applied, headroom)
self.cooking_stat_gained[stat] += applied
```
Reads cleanly when above cap → returns 0. But if `headroom == 0` and the
function is called with amount=1: scaled = min(1, 0) = 0, applied = max(1, 0)
if amount >= 1 and headroom > 0 — but headroom > 0 is FALSE, so applied = 0.
Correct. So at exactly the cap, returns 0. Good. Edge case: when headroom
is between 0 and 1 (impossible since integers), no issue. This one is
actually fine — including for completeness.
**Suggested fix**: None needed.
**Confidence**: LOW (turned out to be non-bug after walk-through)

---

## Identify

### [MINOR] `identify_resume_params` clamps previous_level >= 5 to (5, 1) — re-running mastered ID wastes a quiz
**System**: identify
**File(s)**: `src/items.py:17-32`
**Edge condition**: Player runs the identify quiz on an already-mastered
item (id_level = 5).
**What I see**:
```python
prev = max(0, min(int(previous_level), 5))
start_tier = min(prev + 1, 5)   # = 5
max_chain = max(5 - prev, 1)    # = 1
return start_tier, max_chain
```
For id_level=5, this returns (5, 1) — a one-question tier-5 quiz. The
quiz runs, the answer is checked, the result is "no new insight" because
`new_level = max(previous_level, ...)` can't exceed 5. The player wastes a
turn answering a hard question for nothing.
**Reproducer**: Identify Excalibur to mastery (id_level=5). Try to identify
it again from the I-menu. The quiz starts and runs.
**Suggested fix**: Filter id_level=5 items out of the identify menu (per
items.py:38 comment "5 is filtered out elsewhere"), OR early-return in
`_identify_unique_item` if `previous_level >= 5`.
**Confidence**: LOW (UI filtering likely handles this; verifying would require
running the menu)

---

## Floor progression

### [MINOR] `_descend_stairs` doesn't bound the new level above 100
**System**: floor
**File(s)**: `src/main.py:1988`
**Edge condition**: Player on level 100 (the deepest legal level) tries to
descend further.
**What I see**: `self._change_level(self.dungeon_level + 1, enter_from_top=True)`
unconditionally adds 1. There's a seal-gate check at L99→L100 but no check
for "you're already at the bottom." L100 has no STAIRS_DOWN (it's the boss
floor with the Stone), so the `if self.dungeon.tiles[py][px] != STAIRS_DOWN`
check at line 1972 protects this in practice. But if someone places stairs
on L100 (via `_dig_pit`-style features or future scripted content), L101
would be requested.
**Reproducer**: Synthetic — `_change_level(101)` would attempt to generate
floor 101, which isn't in `BOSS_LEVELS` and would generate as a procedural
dungeon. The Cooking softcap arrays are sized 101 entries
(`_COOKING_SOFTCAP_BY_FLOOR[idx]` clamped via `min(100, ...)`), so HP cap
would degrade gracefully. But mob HP curve scales unbounded (1.025^(pf - 20)).
**Suggested fix**: Explicit clamp in `_descend_stairs`:
```python
new_lvl = min(100, self.dungeon_level + 1)
if new_lvl == self.dungeon_level:
    self.add_message("There is nothing deeper than this.", 'info')
    return
self._change_level(new_lvl, enter_from_top=True)
```
**Confidence**: LOW (no current path reaches it)

---

## Bones

### [MINOR] `load_bones` 50% RNG silently fails without consuming the file
**System**: bones
**File(s)**: `src/bones.py:82-85`
**Edge condition**: Player visits a level matching a bones file.
**What I see**:
```python
def load_bones(dungeon_level: int):
    if random.random() > 0.50:
        return None        # ← file NOT consumed
    ...
```
The 50% RNG returns None without consuming the bones file. Across N future
runs, the bones file remains and the bone has a 50% chance EACH new-level
generation. Effective probability of bones eventually spawning is
1 - 0.5^N which approaches 1 — but a single bones file can hypothetically
spawn the ghost multiple times if a player revisits the floor multiple
times. Wait — checking code, `level_manager.save()` snapshots after
generation, so revisits hit the saved state, not regeneration. Still, across
RUNS, a single bones file with very unlucky RNG could persist forever, taking
up one of the 3 `_MAX_BONES` slots and blocking new bones from being saved
(eviction is by mtime, so the unused one gets evicted first — actually OK).
**Reproducer**: Save a bones file. Start a new run. Visit the matching floor
50 times across new runs without triggering the 50% RNG. The file stays put.
**Suggested fix**: Move the 50% check INSIDE the file-existence block, OR
remove the 50% and rely on the rarity of dying on matching floors.
Alternatively, decrement a "spawn chance" counter inside the bones file each
visit, making it more likely over time.
**Confidence**: LOW

---

## Karma / encounters

### [PASS] Karma clamps correctly at ±10
**System**: karma
**File(s)**: `src/game_encounters.py:752`, `src/npc_encounters.py:2032`
**What I see**: `self.karma = max(-10, min(10, self.karma + karma_delta))` —
canonical clamp. No silent overflow. Both add/subtract sites use this
pattern. Good.

---

## Subject ↔ action mapping drift

### [MINOR] AI subject is used as a catch-all for non-canonical actions
**System**: quiz / mapping
**File(s)**:
- `src/game_menus.py:1294` (sketch_manifest power)
- `src/game_combat.py:976, 1036` (stuffie_fire_breath, sketch_manifest)
- `src/main.py:2805` (trap disarm)
- `src/main.py:3656` (hack reality / XYZZY)
- `src/game_divine.py:428` (fountain)
- `src/game_encounters.py:449` (judgment reward)
**Edge condition**: Per CLAUDE.md, AI is not in the canonical Subject →
Action table. The actions above use AI as a "default subject" without
documentation.
**What I see**: CLAUDE.md lists 10 subjects with explicit actions; AI is
absent. But ~6 game systems use AI for their quiz. Either AI should be
added to the canonical mapping with an explicit action, or these uses
should be re-pointed to existing subjects.
**Suggested fix**: Either add AI to CLAUDE.md as "AI = special/utility
actions (hack reality, fountains, traps)", or migrate fountain → philosophy,
trap disarm → economics, etc. to fit the canonical table.
**Confidence**: LOW (design call, not a bug)

### [MINOR] CLAUDE.md "WIS — +1 second per point" doesn't match per-subject scaling
**System**: docs / quiz timer
**File(s)**: `CLAUDE.md` (Player Stats), `src/player.py:18-30`
**Edge condition**: Reading CLAUDE.md to understand WIS behavior.
**What I see**: CLAUDE.md says "WIS — Quiz timer bonus (+1 second per point)".
Actual `SUBJECT_TIMER` scales range from 0.8 (math) to 1.7 (theology). Only
grammar matches "+1 per point". User-facing docs (Memory Note
project_subject_timer.md) reflect the actual per-subject table, but
CLAUDE.md does not.
**Suggested fix**: Update CLAUDE.md Player Stats line to:
"WIS — Quiz timer bonus (scales per subject; see SUBJECT_TIMER)".
**Confidence**: HIGH (verified mismatch)

---

## Boss rewards / treasure

### [PASS] Boss scrolls / unique drops all resolve
**System**: boss
**Files**: `data/monsters.json` × `data/items/scroll.json`
**What I see**: 26 monsters reference `boss_scroll_id`; all 26 scroll IDs
exist in scroll.json. 26 monsters reference `unique_drop_id`; all 26 exist.
No missing references. `_spawn_boss_scroll` silently no-ops if the scroll
is missing (`main.py:4211-4215`), so even a future mis-reference wouldn't
crash — just silently fail to drop. Defensive but masks data bugs.
**Suggested fix (optional)**: Log a warning when the template lookup fails:
```python
if template is None:
    print(f"WARNING: boss scroll {scroll_id!r} not found", file=sys.stderr)
```

---

## Pet AI

### [MINOR] Pet attacks weapon-bound monster of player without awareness
**System**: pet
**File(s)**: `src/game_combat.py:2057, 2071-2085`
**Edge condition**: Player has Cloak of the Morrigan (chain-equip passive
`death_omen_mark` marks a specific monster for +25% damage in
`combat.py:432-434`). Pet attacks that monster first, kills it, denies the
player the bonus damage on the marked target.
**What I see**: Pet AI in `pet.take_turn(...)` doesn't consult
`player._death_omen_target`. The pet runs its own targeting logic and may
swing first.
**Reproducer**: Equip Cloak of the Morrigan T5. Have a pet adjacent to the
floor's highest-level monster. Pet kills it before player attacks. Player
never gets the mark bonus.
**Suggested fix**: Either A) make the mark transfer to another monster on
target death (re-pick highest-level), or B) accept that pets can pre-empt
player buffs (current behavior). Document either way.
**Confidence**: MEDIUM

### [MINOR] Pet "stay" command position is enforced via AI not via tile check
**System**: pet
**File(s)**: `src/pet_system.py:164` (command), `src/game_combat.py:2120` (adjacent damage)
**Edge condition**: Pet on `stay` command becomes adjacent to a teleporting
monster.
**What I see**: Stay just means "no auto-follow", but adjacent monsters can
still attack the pet (`game_combat.py:2120` `max(abs(m.x - pet.x), abs(m.y -
pet.y)) <= 1`). If a monster teleports to be adjacent to a stayed pet, the
pet eats the swipe with no chance to react. Probably intended, but worth
noting.
**Suggested fix**: None — design as-is.
**Confidence**: LOW

---

## Quiz engine / tier handling

### [PASS] Escalator caps correctly at tier 5
**System**: quiz
**Files**: `src/quiz_engine.py:340`
**What I see**: `self.tier = min(self.tier + 1, 5)` correctly clamps the
escalating tier. Prayer's `effective` value (game_divine.py:911) can reach
chain + at_altar + saintly = 7, but the prayer-resolve sites only check
`>= 3` and `>= 5`, so 6/7 collapse to the highest tier behavior. Intentional.

### [MINOR] Quiz timer floor applies AFTER WIS scaling but not before
**System**: quiz
**File(s)**: `src/quiz_engine.py:145-147`
**Edge condition**: WIS goes negative → base_seconds returned by
`get_quiz_timer` is 0 or negative → `timer_seconds = round(0 * 1.0) + extra
= 0`. The 0.40 floor in `get_quiz_timer_modifier` doesn't help because the
modifier is multiplied AGAINST a 0 base.
**What I see**: `self.timer_seconds = round(base_seconds * timer_modifier) + extra_seconds`
returns 0 if base_seconds is 0. There's no `max(MIN, ...)` floor.
**Reproducer**: Drain WIS to -10 via cursed potions. Trigger a combat quiz.
Timer is 0s. Quiz times out instantly on the next update tick.
**Suggested fix**: After computing `timer_seconds`, floor it:
```python
self.timer_seconds = max(3, round(base_seconds * timer_modifier) + extra_seconds)
```
Pairs with the player.py fix above.
**Confidence**: HIGH

---

## Curse mechanic

### [PASS] Cursed items block unequip and drop
**System**: curse
**Files**: `src/player.py:808-813`, `src/main.py:5038-5046`
**What I see**: `try_unequip_slot` returns (False, "welded") for cursed
items. `_do_drop_item` blocks drop of equipped cursed items. All equip
swap paths (player.py:822, 836, 845, 857, 875, 894) call `try_unequip_slot`
before swapping. Audited clean.

### [MINOR] Cursed wand misfire (3%) wastes charge but doesn't grant ID progress
**System**: curse / wand
**File(s)**: `src/game_magic.py:236-242`
**Edge condition**: Cursed wand misfires (3% roll). Charge is consumed,
no effect fires.
**What I see**: The `_advance_turn` happens but `_apply_wand_effect` is
skipped, meaning no on-hit identification triggers. If the player has the
`identify_one_per_floor_free` passive or similar, the misfire still consumes
the turn without granting whatever ID bonus a successful fire would.
**Reproducer**: Cursed Wand of Cold. Cast in empty space. 3% of the time
the message "cursed wand misfires" appears and the charge is gone. Compare
to wands that hit nothing — still grant ID via `wand.identified = True`
(line 222), which is OUTSIDE the misfire skip. So ID does propagate.
Actually, line 222 fires before line 236 — so ID happens regardless of
misfire. OK, this is fine. Marking as PASS-on-review.
**Suggested fix**: None.
**Confidence**: LOW (false alarm)

---

## Summary

**Total findings**: 18
- **HIGH severity (WARN)**: 6
  - Cursed-miss-backlash bypasses HP floor (combat.py:213)
  - Shielded "physical halved" not implemented for player
  - Quiz timer can go to 0 / negative at low WIS
  - Stack-merge drops BUC of incoming item
  - Ranged ammo consumed before quiz; ESC wastes ammo
  - Spell MP consumed before quiz; ESC wastes MP
- **MEDIUM severity**: 3
  - crit_buff at 0 lingers in dict between ticks
  - Pet pre-empts death_omen_mark target before player
  - Stack-merge BUC handling (medium because uncommon)
- **HIGH-confidence MINOR (docs)**: 1
  - CLAUDE.md "+1 second per WIS" doesn't match actual scaling
- **LOW severity / informational**: 8
  - crit_buff permanent (-1) silently no-ops
  - MAX_EFFECT_DURATION truncation
  - Carry-limit float precision
  - Cooking softcap soft (low confidence on impact)
  - Per-stat softcap (turned out OK on review)
  - identify_resume_params at id_level=5 (likely UI-filtered)
  - load_bones 50% non-consuming RNG (slow burn)
  - Descend past L100 (no current path)
  - AI subject usage as catch-all
  - Pet stay + teleport interaction
- **PASS items audited**: 4
  - Karma clamps at ±10
  - Boss scroll references all resolve
  - Escalator tier caps at 5
  - Cursed item unequip / drop checks
  - Cursed wand misfire ID propagation

**Top 5 by gameplay impact**:
1. Quiz timer can go to 0 at very low WIS — combat becomes unwinnable
2. Spell MP / ranged ammo wasted on ESC — UX violation, drains resources
3. Shielded buff missing damage halving — major spell broken on player
4. Cooking softcap doesn't truly cap — long-term balance breach
5. Cursed-miss-backlash to negative HP — minor; deeply confuses UI/buffs
