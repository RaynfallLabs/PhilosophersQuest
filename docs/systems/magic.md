# Magic Subsystem

Reference-grade documentation for the entire magic pipeline: **spells**
(learned, MP-cost, cast via one science question), **wands** (charge-based,
cast via one science question), and **spellbooks** (learned by passing one
grammar question). Covers the cast contract, MP cost bands, damage scaling,
the self-buff duration table, the dispatch surface for 60+ effects, and
every drift fixed by the v2.18 full-systems audit.

Related docs: [items](items.md), [combat](combat.md),
[status_effects](status_effects.md), [progression](progression.md).

---

## 1. Overview

Magic in Philosopher's Quest is quiz-gated like every other player-facing
mechanic, with three distinct delivery vehicles:

| Vehicle    | Subject  | Difficulty source   | Cost          | Fail penalty            |
|------------|----------|---------------------|---------------|-------------------------|
| Spell      | science  | `spell.tier`        | MP (fixed)    | MP wasted (fizzle)      |
| Wand       | science  | `wand.tier`         | 1 charge      | Charge still consumed   |
| Spellbook  | grammar  | `book.tier`         | the book      | Book destroyed (one-read)|

All three use a `threshold` quiz with `threshold=1` (regular items; unique
artifact books also use 1 in the shipped data — see §9). The quiz is the
only randomness in the player's cast; everything else — damage dice,
durations, saves — is deterministic given the roll and the spell/wand's
authored `power` field.

**All magic code lives in `src/game_magic.py` (`MagicMixin`), with the
spell catalog in `src/spells.py` and the item classes in `src/items.py`.**

---

## 2. The cast quiz contract

Every spell cast runs the identical shape:

```python
self.quiz_engine.start_quiz(
    mode='threshold',
    subject='science',
    tier=_effective_tier,
    callback=on_complete,
    threshold=1,
    total_qs=1,
    wisdom=self.player.WIS,
    timer_modifier=self.player.get_quiz_timer_modifier(),
    extra_seconds=self.player.get_int_quiz_bonus() +
                  self.player.get_quiz_extra_seconds('science'),
    base_seconds=self.player.get_quiz_timer('science'),
)
```
_(from `game_magic.py::_start_spell_quiz`, lines ~1270-1282.)_

### What each field means for a cast

- `mode='threshold'` — binary pass/fail (not escalator or chain). Escalator
  chain was retired for spells in v2.12.0. See the fossil note in §8.
- `subject='science'` — all learned spells ask science questions. Spellbook
  learning is the one grammar-subject touchpoint in the magic pipeline.
- `threshold=1` + `total_qs=1` — one question; right = effect; wrong =
  fizzle. v2.18 reconfirmed this shape for every learned spell.
- `tier=_effective_tier` — the authoritative difficulty handle. The
  player's `spellbook_chain_bonus` (Ring of Scheherazade T4+) reduces
  effective tier by N; a T4 spell cast at effective T3 draws a T3 science
  question. See §4 for how this feeds into damage.
- `wisdom`, `extra_seconds`, `base_seconds`, `timer_modifier` — standard
  quiz timing hooks; INT grants bonus seconds on science quizzes.

### MP is deducted **before** the quiz

`_invoke_spell` subtracts `spell['mp_cost']` from `self.player.mp` **before**
the quiz starts (whether the spell needs targeting or not). The quiz
callback (`on_complete`) therefore sees the MP as already gone:

```python
# _start_spell_quiz on_complete
if not result.success:
    self.add_message(f"The {spell['name']} fizzles -- MP wasted.", 'warning')
    self._advance_turn()
    return
_snd.play('spell_cast')
self._apply_spell_effect(spell, target)
```

Design intent: **wrong answer = you still paid**. This is the SP soft
boundary and resource-loss-as-penalty rule applied to magic — a failed
cast burns MP the same way a failed harvest burns the corpse. No stacked
backlash on top.

### Robe of the Magus overrides

Two chain-equip passives (checked at `_invoke_spell` + the cast callback)
alter the raw contract:

- **`free_cast_once_per_floor`** — pops the next spell's `mp_cost` to 0
  (one cast per floor, consumed via `consume_passive_charge`).
- **`double_cast_at_peak_tier`** — if the successful cast was `tier >= 5`,
  `_apply_spell_effect` fires a **second** time with the same target.

See `src/chain_passives.py` for the passive wiring.

### Targeted vs non-targeted

Each spell declares `needs_target: True|False`.

- **Targeted** (`fire_bolt`, `magic_missile`, `paralyze`, `smite`, etc.) —
  `_invoke_spell` opens the targeting cursor first, scans visible monsters,
  sorts by Manhattan distance, picks the nearest as the initial cursor,
  and parks the game in `STATE_TARGET`. Only once ENTER confirms does the
  science quiz run. If no monster is visible, the cast is cancelled with
  no MP cost.
- **Non-targeted** (self-buffs, mass-effect spells, utility) — go straight
  to the quiz.

---

## 3. MP cost bands

MP cost is **fixed per tier** per the v2.12.0 catalog comment:

| Tier | MP band  | Examples                                 |
|------|----------|------------------------------------------|
| T1   | 2 - 5    | Magic Dart (2), Mage Armor (3), Blink (3), Knock (4), Igni (4) |
| T2   | 5 - 8    | Magic Missile (5), Cold Bolt (6), Haste (7), Mapping (7)      |
| T3   | 8 - 12   | Fireball (10), Smite (10), Phase Door (10), Counterspell (10) |
| T4   | 12 - 18  | Meteor (16), Greater Heal (15), Chain Lightning (15)          |
| T5   | 18 - 25  | Wish (25), Annihilation (25), Cataclysm (24), Dissolution (22)|

### Audit note — the one band violator

Pre-v2.18, `elder_scream` (Ciri's Elder Blood T2 signature) carried
`mp_cost: 10` at `tier: 2` — 2 above the T2 ceiling. The v2.18 fix lowered
it to `mp_cost: 8` to fit the band:

```python
'elder_scream': {
    # v2.15+ audit sync: mp_cost 10 -> 8 to fit the T2 band (5..8).
    'name': 'Scream', 'effect': 'mass_ice', 'power': '2d4',
    'mp_cost': 8, 'tier': 2, 'quiz_tier': 2, 'needs_target': False,
    ...
},
```

All 60+ other learnable spells sit inside their tier's band.

---

## 4. Damage scaling — `MAGIC_TIER_MULT` and `_spell_damage`

Damage from spells and wands routes through a single scaling formula.

### Per-tier multipliers

```python
# game_magic.py top-of-module
MAGIC_TIER_MULT = {1: 3.0, 2: 2.5, 3: 2.0, 4: 1.75, 5: 1.5}
```

- Bigger boost on low tiers (where early-game spells felt like
  afterthoughts next to chain-weapon damage).
- Modest boost on T5 (where the authored dice — `10d10` for Annihilation,
  `9d8` for Dissolution, etc. — were already respectable).

### `_spell_damage(base_dmg, chain=5)`

The common damage path for spells:

```python
def _spell_damage(self, base_dmg: int, chain: int = 5) -> int:
    from chain_passives import apply_spell_damage_passives
    tier = int(getattr(self, '_active_spell_tier', 5) or 5)
    tier_mult = MAGIC_TIER_MULT.get(tier, 1.5)
    dmg, c, a = apply_spell_damage_passives(
        self.player, base_dmg * tier_mult * (1.0 + self.player.INT * 0.1))
    self._last_spell_crit, self._last_spell_anti_being = c, a
    return max(1, int(dmg))
```

Three multipliers stack:
1. `base_dmg` — rolled from the spell's authored `power` string via
   `dice.roll`.
2. `tier_mult` — read from `MAGIC_TIER_MULT` keyed by `_active_spell_tier`
   (set at the top of every `_apply_spell_effect` call).
3. INT boost — `(1.0 + INT * 0.1)` — INT 10 = 1.0x, INT 15 = 1.5x,
   INT 20 = 2.0x.

Then chain-equip passives (`apply_spell_damage_passives`) layer on top for
crit chance and anti-being-type bonuses.

### `_wand_tier_damage(base_dmg, tier)`

The wand variant omits the chain-passive overlay (wands don't carry the
spellcrit/anti-being passives) but applies the same tier + INT formula:

```python
def _wand_tier_damage(self, base_dmg: int, tier: int) -> int:
    tier_mult = MAGIC_TIER_MULT.get(int(tier), 1.5)
    return max(1, int(base_dmg * tier_mult * (1.0 + self.player.INT * 0.1)))
```

### The `chain` arg is a back-compat fossil

`_spell_damage(base_dmg, chain)` still accepts `chain` for signature
back-compat, but the arg is ignored. Spells retired chain scaling in
v2.12.0; `_active_spell_tier` is now the sole driver. See §8 for the
fossil cleanup done in v2.18.

### Audit fix: `magic_missile` now routes through `_spell_damage`

Pre-v2.18, the `magic_missile` targeted-handler computed per-missile
damage with a bespoke INT+base inline expression that **bypassed
`MAGIC_TIER_MULT` entirely**. A T5 Force Storm or wand_of_force_cataclysm
output ~56 damage vs ~198 for other T5 damage spells.

The v2.18 fix routes both the spell handler and the wand handler through
the standard tier-mult path. From `_apply_spell_effect`:

```python
# v2.15+ audit sync: route per-missile damage through _spell_damage so
# MAGIC_TIER_MULT applies (previously the missile handler bypassed tier
# scaling entirely).
_MISSILE_COUNT = {1: 1, 2: 3, 3: 5, 4: 7, 5: 9}
missiles = _MISSILE_COUNT.get(_tier, 1)
total_dmg = 0
for _ in range(missiles):
    if not target.alive:
        break
    base_dmg = _roll(power) if power else 4
    per_missile = self._spell_damage(base_dmg, chain)
    ...
```

Missile count scales by tier (T1 1 / T2 3 / T3 5 / T4 7 / T5 9); each
missile's damage runs the full tier-mult + INT stack.

---

## 5. `_SELF_BUFF_DURATIONS` — the aliased buff table

Non-targeted self-buff spells use a shared dispatch table keyed by
`effect`. The table maps `effect_id → (status_name, base_duration)`:

```python
_SELF_BUFF_DURATIONS = {
    'shield_self':        ('shielded',     12),
    'haste_self':         ('hasted',       10),
    'invisibility_self':  ('invisible',    15),
    'reflect_self':       ('reflecting',   15),
    # 2026 spell expansion — self buffs that re-use existing statuses
    'stoneskin_self':     ('shielded',     25),    # longer shielded; "skin of stone"
    'counterspell_self':  ('magic_resist', 12),    # anti-spell shield
    'foresight_self':     ('clairvoyant',  30),    # long detect-all
    'resurrection_self':  ('life_save',    50),    # one-shot revive
    'greater_invis_self': ('invisible',    25),    # longer invis
    # Missing-handler audit: phase_door + levitate were falling through.
    'phase_self':         ('phasing',      15),    # walk through walls
    'levitation_self':    ('levitating',   12),    # float over floor traps
    # v2.15+ audit sync: T3 Magic Shield needs its own duration
    # (T1 mage_armor_spell = 12; T3 magic_shield_spell = 20). And
    # T5 Greater Haste needs to be meaningfully longer than T2 Haste
    # (10) — T5 = 20 turns.
    'magic_shield_self':  ('shielded',     20),
    'greater_haste_self': ('hasted',       20),
}
```
_(from `game_magic.py::_apply_spell_effect`, lines ~1848-1868.)_

Dispatch is a single branch at the end of the self-buff handler block:

```python
if effect in _SELF_BUFF_DURATIONS:
    eff_name, base_dur = _SELF_BUFF_DURATIONS[effect]
    dur = max(2, int(base_dur * chain_scale))
    self.player.add_effect(eff_name, dur)
    self.add_message(f"{spell['name']} -- {eff_name} for {dur} turns!", 'success')
    return
```

### v2.18 audit fixes

Two **new** aliases were added so T3 Magic Shield and T5 Greater Haste
have **distinct** durations from their lower-tier siblings:

- `magic_shield_self` — 20 turns of `shielded` (was aliased to
  `shield_self` → 12 turns, erasing the tier progression over T1 Mage
  Armor).
- `greater_haste_self` — 20 turns of `hasted` (was aliased to
  `haste_self` → 10 turns, identical to T2 Haste).

Spells.py was updated in the same commit so the T3 `magic_shield_spell`
and T5 `greater_haste_spell` entries now point at these new effect IDs:

```python
'magic_shield_spell': {
    # v2.15+ audit sync: given a distinct effect id so its 20-turn duration
    # is not aliased to mage_armor_spell's 12 turns. Tier progression fix.
    'name': 'Magic Shield', 'effect': 'magic_shield_self', ...
},
'greater_haste_spell': {
    # v2.15+ audit sync: distinct effect id + 20-turn duration ...
    'name': 'Greater Haste', 'effect': 'greater_haste_self', ...
},
```

Two **existing** aliases (`phase_self`, `levitation_self`) were added in
the same audit wave because the handlers were falling through to the
targeted-spell path and silently doing nothing — those spells had
`needs_target: False` but the pre-audit dispatch assumed otherwise.

### Buff spells not in the table

Several buff-adjacent effects have **dedicated handlers** earlier in
`_apply_spell_effect` rather than table entries:

- `displacement_self` → `displacement` status, hard-coded 20 turns.
- `cleanse_self` → removes the first debuff from `player.status_effects`.
- `empower_next` → sets `empowered: 1` for a next-attack triple damage.
- `detect_monsters_spell` → `clairvoyant` status, 20 turns.

The table is the **shared-shape** path; dedicated handlers exist whenever
the effect does something structurally different.

---

## 6. Spell effects — the dispatch surface

`_apply_spell_effect(spell, target)` is one big `if effect == 'X'` chain,
~900 lines. The surface divides into categories.

### 6.1 Damage families

| Family    | Element    | Spells                                                      |
|-----------|------------|-------------------------------------------------------------|
| fire      | fire       | Fire Spark, Fire Bolt, Fireball, Meteor, Cataclysm          |
| cold      | cold       | Frost Touch, Cold Bolt, Ice Storm, Cone of Cold             |
| lightning | lightning  | Spark, Lightning Bolt, Chain Lightning, Storm of Vengeance  |
| acid      | acid       | Acid Dart, Acid Arrow, Dissolution                          |
| force     | pure force | Magic Dart, Magic Missile, Force Barrage, Force Storm, Annihilation |
| holy      | holy       | Smite (bypasses all resists), Turn Undead, Sunburst         |
| life-drain| necrotic   | Drain Life, Soul Drain                                      |
| shadow    | mixed      | (via Witcher sign variants + necromancy spells)             |

All damage routes through `_spell_damage(base_dmg, chain)` → full
tier-mult + INT scaling → `monster.take_damage(scaled, element)` so
resistances apply. Smite is the exception — it writes directly to
`target.hp` with no element passed, bypassing resistances by design
(holy fire is unresistible).

### 6.2 Status spells (targeted single)

Dispatch sets a status with a chain-scaled duration (chain=5 fossil →
`chain_scale=1.0` → full base duration) after `_boss_resist_cc` samples
whether a boss resists:

- `sleep_monster` — `sleeping`, 6t
- `confuse_monster` — `confused`, 10t
- `paralyze_monster` — `paralyzed`, 8t (used by both T2 Hold Monster + T4 Paralyze)
- `slow_monster_spell` — `slowed`, 10t
- `fear_monster_spell` — `feared`, 10t + sets `ai_pattern='cowardly'`
- `aard_blast` — damage + `stunned`, 3t

### 6.3 Mass-status spells (AOE)

Dispatch iterates every visible monster, boss-saves individually, and
applies a shared duration. Added in the v2.12.0 family split:

```python
_MASS_STATUS = {
    'mass_slow':    ('slowed',   8),
    'mass_fear':    ('feared',   10),
    'mass_confuse': ('confused', 12),
}
```

`mass_sleep` has its own branch earlier — the T4+ variant upgrades the
status from `sleeping` to `paralyzed` (the stronger lock):

```python
_stier = int(spell.get('tier', spell.get('quiz_tier', 2)))
status_name = 'paralyzed' if _stier >= 4 else 'sleeping'
dur = 10 if status_name == 'sleeping' else 8
```

Deep Slumber (T5) and Mass Paralyze (T5) both route through this effect,
upgrading to the paralyze variant.

### 6.4 Self-buff spells

Routed through `_SELF_BUFF_DURATIONS` (see §5). The buffs themselves —
`shielded`, `hasted`, `invisible`, `reflecting`, `clairvoyant`,
`phasing`, `levitating`, `magic_resist`, `life_save`, `displacement` —
are documented in [status_effects](status_effects.md).

### 6.5 Utility spells

- **`teleport_self`** (Blink T1, Elder Blink) — handled at top-level
  (v2.18 fix: previously nested inside the `if target is not None:`
  block, so blink spells with `needs_target=False` ran the quiz and did
  nothing).
- **`teleport_away_spell`** — teleport nearest visible monster; if none,
  teleport self. Bosses teleport but return aggro'd.
- **`phase_door_spell`** — self-only; grants `phasing` status (walk
  through walls). Uses `_SELF_BUFF_DURATIONS['phase_self']`.
- **`knock_spell`** — unlock nearest `Container` within 3 tiles.
- **`dispel_magic`** — strip BUFFS only from a single target (not DoTs).
- **`drain_magic`** (wand) — same strip, mirror of dispel.
- **`cancellation`** (wand) — same shape.
- **`detect_monsters_spell`** — reveal + 20t clairvoyance.
- **`light_spell`** — reveal tiles in radius 15 (self-tier scales up to full floor).
- **`cleanse_self`** — pop one debuff.
- **`identify_item`** (Detect Magic / Identify / Omnisight family) — a
  three-tier BUC reveal: T1 reveals magic items in sight, T3 adds
  inventory, T5 adds equipped.

### 6.6 Kill-threshold / lethal spells

- **`annihilate`** (T5 Annihilation) — hard-coded 35% HP threshold:
  non-boss visibles at or below 35% max_hp are instakilled; above
  threshold take `max_hp // 3`; bosses take `max(20, max_hp // 4)` and
  are never instakilled.

  ```python
  # v2.15+ audit sync: chain scaling retired. Fossil expression
  # `0.10 + chain * 0.05` pinned at chain=5 (0.35) since that's what has
  # been shipping. Hardcode the intended 35% HP threshold.
  if effect == 'annihilate':
      threshold_pct = 0.35
      ...
  ```

- **`power_word_kill`** (T5) — instakill if target HP at or below
  `INT * 20`. Bosses immune (take `INT * 5` consolation damage). The
  threshold is a hard-coded pin of the chain=5 fossil expression:

  ```python
  # v2.15+ audit sync: chain retired. Fossil expression
  # `INT * chain * 4` pinned at chain=5 (INT * 20).
  threshold = self.player.INT * 20
  ```

- **`disintegrate_spell`** (T5) — 50% instakill vs non-bosses, else
  `spell.power` (10d8) damage scaled by `_spell_damage`.
- **`imprisonment`** (T5) — paralyze a target up to 60 turns (effectively
  removes from combat; `MAX_EFFECT_DURATION` caps the display).
- **`banishment`** (T4) — instakill if target carries any of
  `{fey, demon, celestial, elemental}` tags and is not a boss; otherwise
  a brief consolation paralyze.

### 6.7 Summons

- **`summon_guardian`** (T3) — spawn one pet near player; level =
  `max(1, dungeon_level // 3)`.
- **`gate`** (T5) — spawn one pet at ~2x the Summon Guardian level,
  `max(3, dungeon_level // 2)`.
- **`summon_undead_horde`** (T5 Army of Darkness) — summon 5 undead pets
  via `_summon_undead_pets(count=5)`.

### 6.8 Fallback

If an `effect` string doesn't match any branch, the targeted path falls
through to a generic damage path:

```python
# Fallback: generic targeted damage
scaled = max(1, int((_r(power) if power else 6) * chain_scale))
actual = target.take_damage(scaled)
self.add_message(f"The {effect.replace('_', ' ')} hits ...")
```

This is the safety net for any future spell that ships without an
explicit handler. In the current catalog, every `effect` in
`LEARNABLE_SPELLS` has a matching dispatch branch (verified by the
systems audit).

---

## 7. Wand contract

Wands follow the same shape as spells with three key differences:

1. Resource = charges, not MP.
2. Fail still consumes a charge (v2.11.0 rule).
3. Cursed wand carries an extra 3% misfire chance **on top** of the
   fail-consumes-charge rule.

### Quiz call

```python
# v2.11.0: All wands use threshold=1 (single science question at the
# wand's authoritative tier). Power is baked into the wand's tier.
self.quiz_engine.start_quiz(
    mode='threshold',
    subject='science',
    tier=getattr(wand, 'tier', wand.quiz_tier),
    callback=on_complete,
    threshold=1,
    wisdom=self.player.WIS,
    timer_modifier=self.player.get_quiz_timer_modifier(),
    extra_seconds=self.player.get_int_quiz_bonus() +
                  self.player.get_quiz_extra_seconds('science'),
    base_seconds=self.player.get_quiz_timer('science'),
)
```

### Charge accounting

```python
# v2.11.0: charge consumed REGARDLESS of success. Fail = wasted zap.
wand.charges -= 1

if not result.success:
    self.add_message(
        "The wand fizzes and fails to fire -- the charge is wasted.",
        'warning')
    if wand.charges <= 0:
        self.add_message(
            "The wand crumbles to dust -- it is spent.", 'warning')
        self.player.remove_from_inventory(wand)
    ...
```

When a wand drops to 0 charges it crumbles immediately (removed from
inventory in-place).

### Pre-quiz escape hatches

Three wand paths **skip the quiz entirely**:

- **Philosopher's Wrench** — tool, not magic. Zero-quiz use via
  `_use_philosophers_wrench`.
- **Flux Capacitor** — "gift from the universe": burns a charge, grants
  10 turns `time_stopped`, no quiz.
- **Empty wand** — if `wand.charges <= 0` at invocation, the wand
  crumbles with no quiz.

### Targeting

Wands with an effect in the `_TARGETED_EFFECTS` set (~30 effects
including every monster-status and single-target damage spell) open the
targeting cursor first — the quiz only runs after ENTER confirms. Same
pattern as targeted spells.

### BUC on wands

Blessed wands roll **one extra charge** at spawn (both `charges` and
`max_charges`). Cursed wands roll one fewer (minimum 1) **and** carry
the 3% post-success misfire that wastes the charge again.

### Wand damage path

Damage wands call `_wand_tier_damage(base_dmg, wand.quiz_tier)` with the
`roll(wand.power)` result. The function returns
`base * MAGIC_TIER_MULT[tier] * (1 + INT * 0.1)`. See §4.

### Wand duration path

Non-damage status wands call either:
- `_wand_tier_duration(default_base, tier)` — a legacy linear scale from
  `game_helpers.wand_tier_duration` (base is interpreted per-tier).
- `_wand_effect_duration(wand, default_base)` — v2.11.0 preference:
  **reads the wand's authored duration from `wand.power`** (plain integer
  string like `"5"` or `"30"`); falls back to the tier-scaled default if
  `power` is missing or looks like a dice string.

Prefer `_wand_effect_duration` for any new status wand — it lets the
wand JSON author the duration directly.

### Audit fix: `abjuration` now strips only BUFFS

Pre-v2.18, the T5 `abjuration` wand called `target.status_effects.clear()`
on the monster, wiping **all** status effects — including player-applied
DoTs (poisoned, burning, petrifying, bleeding), which are the player's
investment. That was inconsistent with the three sibling effects
(`cancellation`, `dispel_magic`, `drain_magic`) which already stripped
only BUFFS.

v2.18 brought abjuration into line:

```python
elif effect == 'abjuration':
    target = self._nearest_visible_monster()
    # v2.15+ audit sync: strip BUFFS only from the target — mirrors
    # `cancellation` / `dispel_magic` / `drain_magic`. The previous
    # `clear()` also wiped player-applied DoTs (poison, bleed, burn,
    # petrify), which are the player's investment.
    cleared_monster = 0
    if target:
        from status_effects import BUFFS as _BUFFS
        _monster_buffs = [e for e in list(target.status_effects) if e in _BUFFS]
        for _e in _monster_buffs:
            target.status_effects.pop(_e, None)
        cleared_monster = len(_monster_buffs)
    # Purge player debuffs
    from status_effects import DEBUFFS
    cleared_player = [e for e in list(self.player.status_effects) if e in DEBUFFS]
    for e in cleared_player:
        del self.player.status_effects[e]
    ...
```

The player-debuff purge was always correct (abjuration also cleanses the
caster) and was kept.

### Wand effects by category

The wand dispatch surface is broader than spells — ~70 distinct effects.
The main groups are:

- **Character buffs/heals:** `heal`, `extra_heal`, `restore_body`,
  `shield_self`, `fire_shield`, `cold_shield`, `regeneration_self`,
  `reflect_self`, `phase_self`, `haste_self`, `invisibility_self`,
  `levitation_self`, `boost_str`, `boost_con`, `boost_int`.
- **World effects:** `digging`, `light`, `sunlight`, `secret_door_detection`,
  `opening`, `mapping`, `clairvoyance`, `detect_treasure`, `detect_monsters`,
  `probing`.
- **Monster-targeted damage:** `fire_bolt`, `cold_bolt`, `lightning_bolt`
  (line AOE), `acid_spray`, `magic_missile`, `striking`, `drain_life`,
  `death_ray` (70% instakill), `disintegrate` (85% instakill),
  `turn_undead`.
- **Monster-targeted status:** `sleep_monster`, `slow_monster`,
  `confuse_monster`, `paralyze_monster`, `blind_monster`, `stoning`,
  `cancellation`, `polymorph_monster`, `fear_monster`, `charm_monster`,
  `poison_monster`, `disease_monster`, `curse_monster`, `teleport_monster`,
  `weaken_monster`, `drain_magic`, `dispel_magic`.
- **Mass effects:** `earthquake`, `explosion`, `mass_confuse`, `mass_sleep`,
  `mass_slow`, `time_stop`, `nova` (whole-floor fire damage),
  `life_transfer` (half-HP steal), `abjuration` (buff-strip + self-cleanse),
  `knock` (unlock nearest within 5).
- **Chaos / wonder:** `wonder` (10 random outcomes), `iron_mortar` (7 random
  outcomes — Baba Yaga's unique T5).
- **Signature artifacts:** `wish` (shows "cannot yet speak" — the spell
  variant handles the actual bounded wish-grab-bag), `create_monster`.

Every wand defn in `data/items/wand.json` sets `tier`, `quiz_tier`,
`effect`, `power`, `charges_min`/`charges_max`/`max_charges`, and
spawn-pool fields (`peak_floor`, `peak_weight`, `spread`,
`floor_spawn_weight`).

### Panic Wave specialization

`wand_of_panic_wave` is the T5 `fear_monster` variant: when the id
matches, the effect expands from "fear the targeted monster" to "fear
EVERY visible non-boss for the wand's duration" — a bonus wand-level
override inside the `fear_monster` branch.

---

## 8. The `chain=5` / `chain_scale=1.0` fossil

Spells pre-v2.12.0 used an **escalator chain** cast flow: the player
answered one science question per chain step, difficulty escalating per
rung, and spell power/duration scaled with chain length (1..5). v2.12.0
retired that model, moving tier to a FIXED property of the spell
(authored in `LEARNABLE_SPELLS`) and switching to a single
threshold=1 cast.

The retirement was intentionally **soft**: `_apply_spell_effect` still
defines two local names at the top so the pre-existing handler bodies
compile unchanged:

```python
# v2.12.0: chain retired. Local aliases keep the existing handler
# bodies working without a mass edit: chain=5 => chain_scale=1.0 =>
# all buff durations fire at full base. Any message that formerly
# embedded "(chain N)" now just says "(chain 5)" -- harmless echo,
# since MP was already deducted before this call.
chain = 5
chain_scale = 1.0
```

**Behavior:** every `int(X * chain_scale)` evaluates to `int(X * 1.0)` =
`X`, so all durations fire at full base. Every `chain * K` evaluates to
`5 * K`. This is why the mass-paralyze base durations, the per-arc
decay in Chain Lightning (3 extra jumps hard-coded), etc., all look like
constants — they *are* constants, pinned at the chain=5 point.

### v2.18 fossil cleanups

Two expressions were leaking fossil math into shipped behavior and were
hard-coded in the audit:

- **`annihilate_spell::threshold_pct`** was `0.10 + chain * 0.05`
  (= 0.35 at chain=5). Replaced with a literal `threshold_pct = 0.35`
  — the intended live value — and the comment documents the fossil.
- **`power_word_kill::threshold`** was `INT * chain * 4` (= `INT * 20`).
  Replaced with `self.player.INT * 20` and a sister expression
  `INT * chain * 1` (= `INT * 5`) for the boss consolation damage became
  `self.player.INT * 5`.

The expressions were algebraically identical to their replacements —
no behavior change — but silently depended on the alias `chain = 5`
staying unchanged forever. v2.18 removed the dependency.

### Legacy chain refs that remain

A few live expressions still **read** `chain` or `chain_scale` without
causing drift:

- `int(X * chain_scale)` for duration scaling — a no-op multiplier.
- `shots = max(2, chain)` in Meteor Swarm — pinned at 5 shots.
- `_max_arcs = 3` in Chain Lightning — the hard-coded replacement for
  the former `chain - 2` expression.
- Status-duration expressions like `max(2, int(6 * chain_scale))` — a
  no-op floor; the floors (2, 3, 4) are retained so a future
  configurable chain could still clamp.

These are all **safe** fossils — they document the pin point without
behaving differently from a hard-coded constant.

---

## 9. Spellbook learning

Spellbooks sit in the inventory until read. Each entry has:

- `spell_id` — the key into `LEARNABLE_SPELLS` the book teaches.
- `spell_name` — mirror of the spell's name, for the menu.
- `mp_cost` — written to `player.known_spells[spell_id]` on success.
- `tier` + `quiz_tier` — authoritative difficulty.
- `quiz_threshold` — number of grammar questions to pass; `1` for every
  spellbook in the shipped data (including the five unique artifacts).
- `is_unique` — flag; sets the book outside the regular spawn pool via
  `min_level: 9999` in dungeon spawn logic.
- `is_consumable_artifact` — flag; routes through `_read_book_of_thoth`
  instead of the normal learn-a-spell path.

### Read contract

```python
# v2.12.0 spellbook-read: ONE grammar question at book.tier (regular
# books, quiz_threshold=1) or THREE (unique artifact books like the
# Necronomicon/Sefer Yetzirah, quiz_threshold=3). Right = spell learned.
# Wrong = book DESTROYED unless Ring of Scheherazade (`scroll_save_on_fail`)
# or a `single_copy` book preserves it -- mirrors the v2.10.0 scroll-read
# contract. Spellbooks are one-read even on success (you internalize the
# spell, the physical text is consumed).
```

Dispatch flow:

1. **Consumable artifact short-circuit** — `is_consumable_artifact` →
   `_read_book_of_thoth`. The Book of Thoth is the only such book
   shipped. Grammar quiz with its own tier/threshold; success grants
   omniscience (full identify + corpse lore + wand recharge), failure
   lands Setne's curse (3d6 psychic + 20t stunned + 3 random items
   forget their type). The book is **always consumed**.
2. **Already-known early-out** — if `spell_id in player.known_spells`,
   emit a message and return without burning the book.
3. **Necronomicon** — stateful multi-question "Say The Words" quiz
   handled by `_necronomicon_quiz`.
4. **Standard path** — one grammar question at effective tier
   (`spellbook_chain_bonus` reduces); on success, the spell is added to
   `player.known_spells[spell_id] = mp_cost`, the book is identified,
   removed from inventory, and `_log_chronicle` records the learning.

### Fail payloads

On a failed grammar quiz:

- **Ring of Scheherazade (`scroll_save_on_fail`)** — the book survives
  but is not identified; player can retry.
- **`single_copy`** — same preservation path.
- **Otherwise** — the book is identified, removed from inventory, and
  "the tome resists your reading, its pages crumbling to dust."

### Threshold ladder

The shipped data uses `quiz_threshold: 1` for every spellbook, including
all five unique entries (necronomicon, sefer_yetzirah, book_of_thoth,
and two others). The code comment in `items.py::Spellbook` describes an
"override to 3" that is not currently used — the Spellbook base class
defaults to 1 and no shipped book overrides. The Book of Thoth path has
its own `getattr(book, 'quiz_threshold', 3)` fallback that defaults to 3
if the field is missing, but the shipped data sets 1 explicitly.

### Quiz call (standard path)

```python
_effective_tier = int(getattr(book, 'tier', book.quiz_tier))
try:
    from chain_passives import get_spellbook_chain_bonus
    _effective_tier = max(1, _effective_tier - get_spellbook_chain_bonus(self.player))
except ImportError:
    pass

_threshold = int(book.quiz_threshold)

self.quiz_engine.start_quiz(
    mode='threshold',
    subject='grammar',
    tier=_effective_tier,
    callback=on_complete,
    threshold=_threshold,
    total_qs=_threshold,
    wisdom=self.player.WIS,
    timer_modifier=self.player.get_quiz_timer_modifier(),
    extra_seconds=self.player.get_int_quiz_bonus() +
                  self.player.get_quiz_extra_seconds('grammar'),
    base_seconds=self.player.get_quiz_timer('grammar'),
)
```

### Spellbook JSON schema

Each entry in `data/items/spellbook.json`:

```json
{
  "name": "...",
  "spell_id": "fire_bolt_spell",
  "spell_name": "Fire Bolt",
  "mp_cost": 6,
  "tier": 2,
  "quiz_tier": 2,
  "quiz_threshold": 1,
  "is_unique": false,
  "identified": false,
  "unidentified_name": "...",
  "item_class": "spellbook",
  "peak_floor": ...,
  "peak_weight": ...,
  "spread": ...,
  "floor_spawn_weight": {...},
  "container_loot_tier": "...",
  "weight": 0.3
}
```

---

## 10. Spell description sync — the 13 v2.18 fixes

The v2.18 audit found **13 drift points** between `spells.py` descriptions
and the actual duration/magnitude the code applied. The descriptions are
what the player sees on the spellbook card and the cast menu; drift here
is a UX lie. All 13 were brought into sync in the same audit wave:

| Spell                 | Pre-v2.18 desc            | Actual code            | Fix action                           |
|-----------------------|---------------------------|------------------------|--------------------------------------|
| `stoneskin_spell`     | "30 turns"                | 25 turns applied       | Desc 30 → 25                         |
| `greater_haste_spell` | "25 turns"                | 10 turns (aliased)     | New `greater_haste_self`; desc → 20  |
| `phase_door_spell`    | "12 turns"                | 15 turns applied       | Desc 12 → 15                         |
| `reflect_spell`       | "20 turns"                | 15 turns applied       | Desc 20 → 15                         |
| `counterspell_spell`  | "15 turns"                | 12 turns applied       | Desc 15 → 12                         |
| `detect_monsters_spell`| "15 turns"               | 20 turns applied       | Desc 15 → 20                         |
| `imprisonment_spell`  | "40 turns"                | up to 60 (CC-capped)   | Desc 40 → "up to 60 turns (capped)"  |
| `paralyze_spell`      | "10 turns"                | 8 turns applied        | Desc 10 → 8                          |
| `hold_monster_spell`  | "5 turns"                 | 8 turns applied        | Desc 5 → 8                           |
| `slow_spell`          | "6 turns"                 | 10 turns applied       | Desc 6 → 10                          |
| `fear_spell`          | "8 turns"                 | 10 turns applied       | Desc 8 → 10                          |
| `magic_shield_spell`  | aliased to T1 mage armor  | 12 (same as T1)        | New `magic_shield_self`; 20 turns    |
| `annihilate` / `power_word_kill` | chain fossil in body | pinned at chain=5 | Fossil expressions hard-coded        |

For the two "new effect ID" fixes (`magic_shield_self`,
`greater_haste_self`), the drift was in **behavior**, not just text — a
T3 spell was literally doing the same thing as its T1 sibling. See §5.

The v2.18 audit also confirmed the systemic reason for the 13 fixes:
retiring chain=5 as a soft alias in v2.12.0 kept the game shippable but
left every `chain * K` and `chain_scale * X` expression as a silent pin.
When new spells were authored at non-pin values the drift crept in
because nothing in the audit path cross-referenced desc text against the
resolved runtime values.

---

## 11. Known-spells state and the m-menu

The player's known spells live in `player.known_spells`, a
`dict[spell_id -> mp_cost]`. The m-menu (opened via the `m` key, see
`game_input.InputMixin`) iterates this dict, looks up each entry in
`LEARNABLE_SPELLS`, and renders the cast menu. Pressing a letter runs
`_invoke_spell(spell_id)`.

Lifecycle:

- **Spawned:** empty dict on new character (unless the welcome-screen
  character build grants Witcher signs or Elder Blood spells, which are
  pre-populated as signature spells outside the regular drop pool).
- **Grown via `_learn_from_spellbook`** on each successful read.
- **Carved out?** No. Known spells persist for the character's life.
  Death wipes them with the save. There is no spell-forgetting
  mechanic shipped.

---

## 12. Save-state surface

- `player.known_spells` — dict of learned spells; persists across save.
- `player.known_item_ids` — set of identified item ids; mapping which
  specific spellbook/wand/scroll was identified lives here.
- `player.recall_lore_cooldown` — Recall Lore (trivia-escalator; see
  `_start_recall_lore`) is magic-adjacent and tracked in player state.
- Buff statuses (shielded, hasted, etc.) live in
  `player.status_effects` — see [status_effects](status_effects.md).

Wand `charges` is a per-instance item attribute (not player state), so
it serializes with the inventory. Spellbooks consumed on learn have no
save surface — they're removed from inventory.

---

## 13. Cross-references

- **[items](items.md)** — Wand, Scroll, Spellbook class definitions and
  the JSON schemas that feed them.
- **[combat](combat.md)** — the shared damage pipeline that spells and
  wands feed through (`monster.take_damage(scaled, element)`).
- **[status_effects](status_effects.md)** — definitions, durations, and
  behaviors of the buffs/debuffs spells apply (`shielded`, `hasted`,
  `invisible`, `reflecting`, `phasing`, `levitating`, `clairvoyant`,
  `magic_resist`, `displacement`, `life_save`, `empowered`,
  `time_stopped`).
- **[progression](progression.md)** — MP max, INT scaling, WIS quiz
  timer, Robe-of-the-Magus / Ring-of-Scheherazade chain passives, how
  spell learning feeds the player's capability curve.

---

## 14. Quick reference — the v2.18 audit delta

Summary of every magic change shipped in v2.18:

1. **`abjuration` (wand T5)** — now strips BUFFS only from the target
   (was `status_effects.clear()`). Keeps player-applied DoTs intact.
2. **`magic_missile` (spell + wand)** — now routes through
   `_spell_damage` / `_wand_tier_damage` so `MAGIC_TIER_MULT` applies.
3. **`magic_shield_self` (new)** — distinct 20-turn `shielded`
   duration; `magic_shield_spell` (T3) rewired to it.
4. **`greater_haste_self` (new)** — distinct 20-turn `hasted`
   duration; `greater_haste_spell` (T5) rewired to it.
5. **13 spell description syncs** — see §10 table.
6. **`elder_scream`** — mp_cost 10 → 8 to fit the T2 MP band.
7. **`annihilate` + `power_word_kill`** — fossil `chain * K`
   expressions hard-coded to their chain=5 values.
8. **`teleport_self` top-level handler** — moved out of the
   `if target is not None:` block so blink spells with
   `needs_target=False` actually fire.
9. **`phase_self` + `levitation_self`** — added as
   `_SELF_BUFF_DURATIONS` entries (handlers were falling through).

Together these are a single audit-driven cleanup pass: the mechanic
contract was correct in v2.12.0, but five years of catalog growth under
a soft chain=5 fossil had let a dozen drift points accumulate. v2.18
re-anchored every magnitude to the shipped runtime value and documented
the fossil in-source so a future chain-system revival won't silently
move numbers.
