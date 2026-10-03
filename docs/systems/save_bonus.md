# Save Bonus (Gradient Defense)

**Status:** v2.18.0 (shipped 2026-10-02)
**Code:** `src/player.py::save_bonus_for` + `_gear_save_bonus` + `_quirk_save_bonus` (lines ~679-730); consumer at `src/status_effects.py::apply_debuff_with_save` (lines ~464-505)
**Data:** `data/items/*.json` (`save_bonus: {cat, amount}` on gear); `data/items/cook_outcomes.json` (`temp_power: save_guard_*` + `temp_amount`); `src/main.py::_apply_save_affinity` (build-level innate dicts)
**Related docs:** [status_effects](status_effects.md), [quiz_engine](quiz_engine.md), [items](items.md), [food_system](food_system.md), [combat](combat.md), [progression](progression.md); design doc: [`docs/design/save_bonus_audit.md`](../design/save_bonus_audit.md)

## Purpose
A flat `+N` to the player's d20 saving-throw roll per category (CON / WIS / DEX), summed from every source and hard-capped by `save_bonus_for`. It is the gradient defensive tier between "no defense" (plain save roll) and "full immunity" (resist items). It's the single highest-leverage identity-conversion win the content audit surfaced — hundreds of samey `+1 stat` items + masteries + quirks collapse into memorable CON/WIS/DEX saves without inventing new subsystems.

## Design intent
The game had two defensive tiers before this: nothing, or the small set of `_RESIST_BLOCKS` resists (hard immunity to a debuff class). Everything in between was raw stat bumps feeding d20 math implicitly. The save-bonus system makes that implicit gradient *explicit*: a flat `+N` per category that stacks across equipment, build affinity, quirks, and cooked wards, hard-capped so it never degenerates to immunity.

**Three defensive tiers** (ordered by how early they short-circuit):

```
no defense  →  SAVE BONUSES (the gradient)  →  full immunity (resist items)
                 ← this doc ←
```

- **No defense** — the player eats the save roll unmodified.
- **Save bonuses (gradient)** — `d20 + stat_mod + N` where N tops out at +5. A ceiling of +5 against a monster DC capped at ~18 still leaves a real failure chance at depth, so stacking never reaches immunity.
- **Full immunity** — short-circuits `apply_effect` before the save roll even fires. Rare, item-gated (poison_resist, sleep_resist, drain_resist, fire_resist, cold_resist, magic_resist, disint_resist). Save bonuses NEVER promote to this tier.

**The gradient guardrail**: `save_bonus_for` caps the total at **+5 overall**, with the **timed lane (cooked wards + powers) contributing at most +3**. Diminishing returns via hard cap, not reduced marginal benefit — the simple shape kept parse-at-a-glance readability over cute math.

**Two lanes (no overlap):**

| Lane          | Sources                                                | Lifetime           | Cap per-lane |
|---------------|--------------------------------------------------------|--------------------|--------------|
| **Permanent** | equipment `save_bonus`, build `save_affinity`, quirk passives | while equipped / passive | +5 total |
| **Timed**     | cooked "ward" food, active powers, hero specials       | N turns (chain-scaled) | +3 |

Total cap is `min(perm + min(timed, 3), 5)`. Both lanes combined still cannot exceed +5.

**Only CON / WIS / DEX map to saves.** STR / INT / PER remain pure stat bumps — this keeps those three as a true contrast tier (not everything becomes a save). The `_EFFECT_NOUN` + `_SAVE_FLAVOR` tables tie CON = body, WIS = will, DEX = reflex, so saves read as flavorful stat-identity, not dice-and-DCs.

**A design decision: resource loss still lands on saves.** DoTs (poison, bleed, burning, doom_dot, drain) have no `SAVE_STAT` entry and bypass the stat-save branch, but **as of v2.18.0 they still consult `save_bonus_for('CON')`** for a flat duration reduction (floor 1). This upholds "resource loss IS the penalty" (DoTs still land) while rewarding an invested CON save profile with shorter-lived afflictions. Pre-v2.18.0 the Torque of Lugh's `{all: 3}` was quietly dead against DoTs despite the "all saves" text.

**See [`docs/design/save_bonus_audit.md`](../design/save_bonus_audit.md)** for the full 2026-06-03 scoping audit: it defined the Option-B scope that shipped, catalogued the overlap pools (114 flat `+stat` accessories, 60 `accessory_stat_bonus` masteries, 40 flat-stat quirks, 110 mis-remapped control-resist dishes), named the specific items/quirks/recipes to convert, and set the +5/+3 cap philosophy.

## Data model / schema

### `save_bonus` on gear (JSON)
Mirrors the `{stat, amount}` and `{type, amount}` shapes used elsewhere:
```json
"save_bonus": {"cat": "CON", "amount": 2}
"save_bonus": {"cat": "all", "amount": 3}
```
- `cat`: `'CON' | 'WIS' | 'DEX' | 'all'`.
- `amount`: integer (can be negative, though no in-tree gear uses that).
- `'all'` applies to every category in `save_bonus_for`'s read.

Loaded at `src/items.py:255`: `self.save_bonus = defn.get('save_bonus', None)`. Scanned live by `_gear_save_bonus` on every call — no equip-time bookkeeping.

### Player fields

```python
# All dicts: {'CON' | 'WIS' | 'DEX' | 'all' -> int}

self._save_bonus:   dict = {}     # equipment grants (unused in the live path —
                                  # the scan is live via _gear_save_bonus; this
                                  # field is reserved and defensive-init only)
self.save_affinity: dict = {}     # innate build affinity (set from main._apply_save_affinity)
self._save_guard:   dict = {}     # TIMED lane magnitude (companion to save_guard_* status)
```

The companion-field pattern (status flag for duration + `player._x` field for magnitude) mirrors `_stand_ac_bonus` (Leonidas) — see save_bonus_audit.md §2.

### `save_guard_<cat>` statuses (BUFFS)
Four status ids register the timed lane:
```python
'save_guard_CON':   ('Body Ward',   (150, 230, 170), 'Bonus to resisting paralysis / sleep / stun'),
'save_guard_WIS':   ('Mind Ward',   (160, 200, 245), 'Bonus to resisting confusion / fear / charm'),
'save_guard_DEX':   ('Reflex Ward', (205, 230, 150), 'Bonus to resisting slow / immobilize'),
'save_guard_all':   ('Warded',      (210, 230, 255), 'Bonus to all saving throws'),
```
Each ward is in `BUFFS` (so `dispel_magic` targeting the player cannot wipe their own wards; cleanse flows that strip debuffs do NOT touch them).

Expiry hook in `status_effects.tick_all`:
```python
if effect.startswith('save_guard_'):
    _g = getattr(player, '_save_guard', None)
    if isinstance(_g, dict):
        _g.pop(effect[len('save_guard_'):], None)
```

### Quirk passive flags
`quirk_progress` keys consumed by `_quirk_save_bonus`:
- `save_bonus_CON` / `save_bonus_WIS` / `save_bonus_DEX` — category-specific permanent bonus.
- `save_bonus_all` — flat permanent `+N` across all categories.

Example wire (Perseus quirk):
```python
lambda pl: pl.quirk_progress.update({'save_bonus_all': 2})
```
(`src/quirk_system.py:1086`)

Also seeded at game-start in `main.py:561-562` so a mid-conversion save that had the old "halve debuffs" branch gets automatically upgraded.

## Flow — the +5 formula

### `Player.save_bonus_for(cat: str) -> int`
```python
def save_bonus_for(self, cat: str) -> int:
    if cat not in ('CON', 'WIS', 'DEX'):
        return 0

    def _amt(d):
        if not isinstance(d, dict):
            return 0
        return int(d.get(cat, 0) or 0) + int(d.get('all', 0) or 0)

    # --- Permanent lane: equipment grants + innate affinity + quirks
    perm = (_amt(getattr(self, '_save_bonus', None))
            + _amt(getattr(self, 'save_affinity', None))
            + self._gear_save_bonus(cat)
            + self._quirk_save_bonus(cat))

    # --- Timed lane: wards gated by their companion status, capped at +3
    se    = self.status_effects
    guard = getattr(self, '_save_guard', None) or {}
    timed = 0
    if se.get(f'save_guard_{cat}', 0):
        timed += int(guard.get(cat, 0) or 0)
    if se.get('save_guard_all', 0):
        timed += int(guard.get('all', 0) or 0)
    timed = min(timed, 3)

    return min(perm + timed, 5)
```

**Call sites:** two live consumers.
1. `status_effects.py:494` — `apply_debuff_with_save` adds `save_bonus_for(stat)` to the d20 roll.
2. `status_effects.py:489` — `apply_debuff_with_save` non-SAVE_STAT branch (v2.18.0) uses `save_bonus_for('CON')` to shrink DoT durations.

### `Player._gear_save_bonus(cat) -> int`
Live scan — no bookkeeping on equip/unequip:
```python
def _gear_save_bonus(self, cat: str) -> int:
    total = 0
    slots = [self.weapon, getattr(self, 'ranged_weapon', None), self.shield,
             self.amulet_slot, getattr(self, 'belt_slot', None)]
    slots.extend(self.armor_slots)
    slots.extend(self.accessory_slots)
    for it in slots:
        sb = getattr(it, 'save_bonus', None) if it is not None else None
        if isinstance(sb, dict) and sb.get('cat') in (cat, 'all'):
            total += int(sb.get('amount', 0) or 0)
    return total
```
Covers all equipped slots including the belt, amulet, ranged weapon, 8 armor slots, and 4 accessory slots. An item whose `save_bonus.cat == 'all'` contributes to every category.

### `Player._quirk_save_bonus(cat) -> int`
```python
def _quirk_save_bonus(self, cat: str) -> int:
    qp = getattr(self, 'quirk_progress', None) or {}
    return int(qp.get(f'save_bonus_{cat}', 0) or 0) + int(qp.get('save_bonus_all', 0) or 0)
```

### How the save math uses this (`apply_debuff_with_save`)
See [status_effects.md](status_effects.md) for the full flow. Core shape:
```python
stat  = SAVE_STAT.get(effect)                       # 'CON' / 'WIS' / 'DEX' or None
mod   = (int(getattr(player, stat, 10)) - 10) // 2  # d20 stat mod
bonus = player.save_bonus_for(stat)                 # <-- +N gradient
roll  = randint(1, 20) + mod + bonus
# roll >= dc + HARD_CONTROL -> NEGATE
# roll >= dc + SOFT_CONTROL -> HALVE duration
# roll <  dc                -> FULL duration lands
```

For effects **not** in `SAVE_STAT` (poisoned, bleeding, burning, diseased, doom_dot, draining):
```python
# v2.18.0: non-SAVE_STAT branch now respects save_bonus_for('CON')
_sb  = int(player.save_bonus_for('CON'))
_dur = max(1, int(duration) - _sb)
applied = player.add_effect(effect, _dur)
```

### Build affinity (innate permanent)
`main.py:400 / 450::_apply_save_affinity` reads a `_save_bonus` key from the hero's build metadata (`SECRET_BUILDS` + the main stat loop at `main.py:316`) and writes it to `player.save_affinity`. Example build keys:
- Stalwart / CON (Leonidas, Boudicca, Achilles)
- Sage / WIS (Socrates, Joan, Hildegard)
- Scout / DEX (Hermes, Ciri, Musashi)
- Frail casters: no save affinity (fragility is the design)

Shipped as pure data in build metadata — zero engine changes beyond the init-time read.

### Cooked wards (timed)
`food_system.py:289` write path:
```python
# When a cooked outcome resolves to a save_guard_* temp_power, write BOTH
# the status (gated by _TEMP_POWER_REMAP) AND the magnitude.
if canonical.startswith('save_guard_'):
    cat = canonical[len('save_guard_'):]        # 'CON' | 'WIS' | 'DEX' | 'all'
    amount = min(3, max(1, int(outcome.get('temp_amount', 2))))
    if not hasattr(player, '_save_guard') or player._save_guard is None:
        player._save_guard = {}
    player._save_guard[cat] = amount
    player.add_effect(canonical, duration)       # BUFF status; _save_guard magnitude
```

The magnitude is clamped `[1, 3]` at the write — the +3 cap applies at both ingress AND in `save_bonus_for`, so there's no path to a +4 ward even with buggy data. When a ward's status expires, `tick_all` pops the magnitude; `save_bonus_for` reads 0 for that cat on the next call.

Legacy control-resist aliases in `food_system._TEMP_POWER_REMAP` route the old `paralyze_resist` / `stunned_resist` / `confused_resist` / `charm_resist` / `feared_resist` / `hallucinate_resist` / `petrify_resist` recipe fields into the correct `save_guard_*` ward family (fixes the ~110 mis-remapped dishes bug — audit §4).

## Invariants (don't break)

- **Hard cap +5 total.** `return min(perm + timed, 5)`. Immunity remains the exclusive job of `_RESIST_BLOCKS`. If stacking ever reaches "always saves at depth," you've broken the design — monster DC caps at ~18 and the +5 ceiling leaves real failure room.
- **Timed lane +3 cap.** `timed = min(timed, 3)` inside `save_bonus_for`. Even stacking `save_guard_WIS` + `save_guard_all` cannot exceed +3 from the timed lane.
- **`save_guard_*` are BUFFS** — register in `status_effects.BUFFS`, not DEBUFFS. Cleanse flows that strip debuffs must not touch wards.
- **Companion-field discipline.** The duration lives in `player.status_effects['save_guard_CON']`; the magnitude lives in `player._save_guard['CON']`. Both must exist for the timed lane to read non-zero; both are cleared when the status expires (`tick_all` pops `_save_guard`).
- **STR / INT / PER NEVER get a save category.** Early `if cat not in ('CON', 'WIS', 'DEX'): return 0` guard. Keep this — it's the contrast tier that keeps stat bumps distinct from save bumps.
- **Live gear scan.** Do not add equip-time bookkeeping to `_save_bonus`; `_gear_save_bonus` scans slots fresh on every call. Bookkeeping would drift from BUC rechecks / corrosion / equip swaps.
- **DoTs still land on saves.** Non-SAVE_STAT effects use `save_bonus_for('CON')` to REDUCE duration (floor 1), NOT to NEGATE. "Resource loss IS the penalty."
- **The design doc is load-bearing.** Any new save-bonus content (new gear, new wards, build-affinity additions) should fit the §2 framework: `{cat, amount}` shape, feeds through `save_bonus_for`, respects the +5 / +3 caps. See [`docs/design/save_bonus_audit.md`](../design/save_bonus_audit.md).
- **The non-SAVE_STAT branch is `save_bonus_for('CON')`, not `save_bonus_for(stat)` for the missing stat.** Hard-coded to CON because DoTs are body afflictions; WIS/DEX saves don't apply to poison/bleed/burn.

## Interactions

- **[status_effects](status_effects.md)** — the one consumer. `apply_debuff_with_save` reads `save_bonus_for(stat)` for stat-save branches and `save_bonus_for('CON')` for non-SAVE_STAT branches. The `save_guard_*` statuses are registered + tick-cleaned there.
- **[items](items.md)** — equipped gear's `save_bonus: {cat, amount}` field is scanned live by `_gear_save_bonus`. Flagship amulets: Amulet of Fortitude (CON+3), Amulet of Insight (WIS+3), Pectoral of Amun, Hamsa Hand, Torque of Lugh ({all: 3}), Kavacha Kundala, Menat of Hathor. See `tests/test_save_bonus_content.py` for the pinned set.
- **[food_system](food_system.md)** — cooked wards (`save_guard_CON/WIS/DEX/all`) are the TIMED lane. Chain length scales duration; magnitude clamped `[1, 3]` at the write.
- **[progression](progression.md)** — innate build affinity (Stalwart / Sage / Scout / Frail-caster) via `_apply_save_affinity` + `SECRET_BUILDS._save_bonus` metadata.
- **[quests_mysteries](quests_mysteries.md)** — the Perseus quirk, Hamsa Hand, Torque of Lugh, Amulet of Fortitude artifact grants pay out in save bonuses.
- **[combat](combat.md)** — chain-equip's `death_save_bonus` (chain_passives.py) is a SEPARATE system — bonus to the once-per-death resurrection save, not the status-effect save. Do not confuse.

## History of major decisions

- **2026-06-03** — Save-bonus audit (`docs/design/save_bonus_audit.md`). Scoping decided: Option B (full gradient + recipe fix). Framework established: one `save_bonus_for` aggregator; `{cat, amount}` value shape; two lanes with no overlap; +5 total / +3 timed caps.
- **2026-06 (post-audit ship):**
  - `save_bonus_for` added to `Player`; one-line insertion in `apply_debuff_with_save`.
  - 12 monster-family masteries (fey → WIS, aberration → WIS, undead → WIS, dragon → CON, demon → WIS, etc.) converted. The fey charm-halve and aberration duration-subtract special cases in `add_effect` retired into one uniform mechanism. (Later removed entirely when all masteries were deleted 2026-08-06; the save-bonus content survived in gear/quirks/wards.)
  - **PERSEUS** quirk: `halve all incoming debuff durations` branch deleted → `{all: +2}` save bonus. Legible, capped, no double-dip with the new save math.
  - Build affinity data: ~10 archetype builds got `_save_bonus` metadata.
  - Recipe ward family: `_TEMP_POWER_REMAP` wired to `save_guard_CON/WIS/DEX`; fixed ~110 mis-remapped control-resist dishes that promised specific protections and silently fired the wrong resist (bug #1 in audit §4).
  - Equipment conversions: Amulet of Fortitude (CON+3), Amulet of Insight (WIS+3), Anklet of Atalanta (DEX), Kavacha Kundala / Menat of Hathor (CON). Several named unique accessories gained save_bonus as part of their chain-equip ladder.
- **2026-08-06** — All three mastery stores removed from the game. Save-bonus content stayed intact (it was already migrated to gear/quirks/wards for identity reasons).
- **2026-10-02 (v2.18.0)** — `apply_debuff_with_save` non-SAVE_STAT branch now respects `save_bonus_for('CON')` (duration reduction). Pre-v2.18.0, DoTs (poison, bleed, burning, doom_dot, draining) silently bypassed save bonuses — Torque of Lugh's `{all: 3}` was dead against them despite the "all saves" text. The cap philosophy still holds (DoTs still LAND; only duration shrinks, floor 1).

## Testing
- `tests/test_save_bonus_content.py` (100 lines) — pins:
  - Equipped gear's `save_bonus` field is read via `_gear_save_bonus`.
  - Perseus quirk grants `{all: +2}` via `_quirk_save_bonus`.
  - Flagship amulets (Fortitude / Insight / Hamsa / Torque / Pectoral) have the expected `save_bonus` payloads.
  - Build affinity is applied from the hero's build metadata on game start.
  - Old saves without `save_affinity` / `_save_bonus` / `_save_guard` dicts load cleanly (backwards-compatible — defensive-init in `main.py:552-555`).
- `tests/test_status_lock.py` (relevant section, ~160 lines) — pins:
  - `save_bonus_for` sums permanent lanes and hard-caps at +5.
  - Timed ward is gated by status presence AND capped at +3.
  - `_save_guard` cleared when the companion status expires.
  - `save_bonus_for` actually improves save odds (statistical: 1000-roll Monte Carlo at a fixed DC).
  - Cooked ward grants both the status and sets `_save_guard[cat]` capped at +3.
  - Cooked ward amount clamped to +3 even if `temp_amount` is higher.
  - Cooked ward defaults to +2 when `temp_amount` is unspecified.
  - Control-resist `_TEMP_POWER_REMAP` targets are wards (BUFF), not raw resists.
  - Bad-food control routes through save-failure landing path.
  - Bad-food control save can negate hard control.
  - Bad-food noncontrol debuff duration unchanged by the new save branch (regression guard).

## Known rough edges

From SYSTEMS_AUDIT.md:
- **§9 VERIFIED OK** — `save_bonus_for` gradient math pins: `perm + min(timed, 3)` clamped to 5. Perseus (+2) + Torque (+3) + Hamsa (+2) = perm 7 → clamped 5. Cap holds. `apply_effect` HARD_CONTROL guard refuses re-apply while locked + during the 3-turn grace. All flagship save-bonus items (Hamsa / Torque / Pectoral / Amulet of Fortitude) traced through `_gear_save_bonus`. Perseus quirk's `save_bonus_all: 2` routed correctly through `_quirk_save_bonus`.
- **§9 P1 (pre-v2.18.0, now fixed)** — `apply_debuff_with_save` previously bypassed `save_bonus_for` for non-SAVE_STAT effects. Torque of Lugh's `{all: 3}` did not help against poison/bleed/burning/doom_dot/draining despite "all saves" text. **Fixed in v2.18.0** by routing the no-SAVE_STAT branch through `save_bonus_for('CON')` for duration reduction (min 1 turn).
- **§5 P2** — `mystery_system.py:181` cooking challenge uses `escalator_chain` threshold=5, which can author cooked wards outside the ward family's normal clamp path. Verify that mystery-cook outcomes still route through `food_system._apply_recipe_outcome` (which does the `[1, 3]` clamp).
- **§3.4 (audit doc)** — Future expansion directions documented but not shipped: (a) **"Steel Yourself" active power** — timed `save_guard_all` proactive buff distinct from the existing reactive mind_fortress / reality_anchor cleanses; (b) **Leonidas Spartan Stand tier-scaled save grant**; (c) **Option C coverage expansion** — route trap debuffs and non-attack-source debuffs through `apply_debuff_with_save` so saves apply consistently everywhere (today a WIS-save build still gets confused with no save by a confusion trap).
- **Open design questions from audit §8** that remain unresolved: (a) saves on traps/non-attack debuffs (coverage decision); (b) food ward duration — fixed vs chain-scaled (current: chain-scaled per `food_system._apply_recipe_outcome`); (c) Open question re: `_save_bonus` field — currently a reserved defensive init slot, no shipped content writes to it (all gear grants go through `_gear_save_bonus` live scan). Candidate for cleanup if nothing lands content there.

## Reference — the audit source

The full scoping audit lives at [`docs/design/save_bonus_audit.md`](../design/save_bonus_audit.md). Key sections to re-read when extending:
- **§1-2** — the one-mechanic-one-insertion-point framework; value shape; the `save_bonus_for` consumer at `status_effects.py:404`; the gradient guardrail philosophy.
- **§3** — overlap pools catalog (items / masteries / quirks / recipes / builds): 114 flat-stat accessories, 60 `accessory_stat_bonus` masteries, ~40 flat-stat quirks, ~110 mis-remapped control-resist dishes. Explicit "best-conversions" lists.
- **§4** — incidental bugs: `_TEMP_POWER_REMAP` mis-fires (fixed in ship) and `undead` family mastery "immune to fear" dead code (realized by the family→WIS save conversion).
- **§5** — the coverage caveat: saves bite only where `apply_debuff_with_save` is used (monster attack path + gaze attacks). Trap debuffs and non-attack sources still route through plain `add_effect`.
- **§6** — three scope options. Option B (full gradient + recipe fix) is what shipped.
- **§7** — Option B concrete phase order (6 steps + play-test).
- **§8** — open design questions.
