# Status Effects

**Status:** v2.18.0 (shipped 2026-10-02)
**Code:** `src/status_effects.py` (654 lines); `Player.add_effect` / `has_effect` / `tick_effects` live in `src/player.py`
**Data:** none directly; chest/trap/food/monster JSON references effect ids
**Related docs:** [save_bonus](save_bonus.md), [combat](combat.md), [quiz_engine](quiz_engine.md), [magic](magic.md), [food_system](food_system.md), [monsters](monsters.md), [items](items.md), [identify_v3](identify_v3.md)

## Purpose
A single registry + tick loop drives every timed status in the game: paralysis, poison, haste, invisibility, resistance halos, cooked wards, chain-combat specials, death-countdowns. One table defines display, color, and short text; four frozensets categorize behavior; `apply_effect` + `apply_debuff_with_save` + `tick_all` form the complete API.

## Design intent
NetHack-style "turn count tells the story" statuses are the backbone of roguelike combat identity. The design decisions that shape THIS file:

**One registry, one tick loop.** `EFFECT_INFO` is the single source of truth for every effect's display name, HUD color, and short description. UI (sidebar, bestiary, expire log) reads from here. `tick_all` walks `player.status_effects` once per turn and dispatches per-effect side effects. Adding a new effect = add one row to `EFFECT_INFO`, add the id to the right frozenset(s), optionally add an `_EXPIRE_MSGS` line, optionally add a dispatch branch in `tick_all`.

**Four categories gate behavior**, and effects can be in several of them:
- `BUFFS` — stripped by `dispel_magic` / `cancellation` / `drain_magic` targeting the player's own buffs.
- `DEBUFFS` — stripped by scrolls/prayers that "cleanse" the player.
- `HARD_CONTROL` — the autokill risk (paralysis, sleep, stun, freeze, immobilize, petrifying). D&D-save NEGATES; cannot be re-applied while active; followed by a 3-turn grace window.
- `SOFT_CONTROL` — degraded but not frozen (confuse, fear, charm, slow). D&D-save HALVES; refreshes to `max()` instead of stacking.

**Gradient defense, never immunity.** Three layers:
1. **Resist items** (`_RESIST_BLOCKS`) — hard immunity for a specific debuff class, short-circuits before the save math.
2. **Save bonuses** ([save_bonus.md](save_bonus.md)) — a +N to the d20 save roll (gradient; +5 total cap, +3 timed cap).
3. **No defense** — the save roll fires unmodified.

The important design rule: **saves + resists never overlap**. If `poison_resist` is active, the `poisoned` debuff never gets to the save roll at all — it's refused in `apply_effect`'s first branch. If `poison_resist` is absent, the save math fires (and `poisoned` has no `SAVE_STAT` so the CON-based duration-reduction branch applies — see [save_bonus.md](save_bonus.md) §apply_debuff_with_save).

**Hard-control anti-permalock guarantee.** A hard-control effect cannot be refreshed, re-applied while active, OR re-applied within the 3-turn `control_immune` grace window after it expires. This GUARANTEES free turns between every disable bout. Monsters that reliably re-cast paralysis still can't permalock.

**Control cap** per single application: `CONTROL_CAP` clamps individual durations so one failed save is never a death sentence even if the data file says "paralyze 20". `MAX_EFFECT_DURATION = 60` globally caps every effect (prevents infinite stacking on non-CONTROL effects which use `current + duration` additive stacking).

**Resource loss IS the penalty.** DoTs (poison/bleed/burning/doom_dot/draining) still land even on a successful save — the save only applies a flat CON-based duration reduction, min 1 turn (§apply_debuff_with_save non-SAVE_STAT branch). This preserves "the quiz-gated action cost IS the penalty" rule without making tanks poison-immune.

## Data model / schema

### `EFFECT_INFO: dict[str, (display_name, rgb, description)]`
All effect ids (debuff, buff, control, resistance, chain-combat-v2 specials, hero-special buffs) live here. The HUD color and short description are read directly for sidebar chips and expire-log entries. Example rows:
```python
'paralyzed':   ('Paralyzed',   (220,  50,  50), 'Cannot move or act'),
'poisoned':    ('Poisoned',    ( 80, 210,  60), 'Losing 1 HP per turn'),
'hasted':      ('Hasted',      (245, 245,  60), 'Monsters act half as often'),
'blessed':     ('Blessed',     (200, 240, 160), 'All quiz timers +25%; divine clarity'),
'petrifying':  ('Petrifying',  (205, 205, 130), 'Turning to stone -- find a cure!'),
'doom_dot':    ('Doom',        (140,  60, 200), 'Ticking damage as fraction of max HP per turn (Laevateinn)'),
'control_immune': ('Recovering', (200, 230, 255), 'Shaking it off -- briefly immune to being disabled'),
'save_guard_CON': ('Body Ward', (150, 230, 170), 'Bonus to resisting paralysis / sleep / stun'),
```

### `player.status_effects: dict[str, int]`
The one place every effect's duration lives. Values:
- `n > 0`  — active for `n` more turns.
- `-1`    — permanent (intrinsic, immutable via `apply_effect`).
- `0` / absent — not active.

Read with `player.has_effect(name)` (true for any non-zero value). Written only through `apply_effect` / `apply_debuff_with_save` / `tick_all`. Direct writes are allowed but discouraged — the `grendel_grip` tick-clear is the one in-tree exception.

### Core constants

```python
MAX_EFFECT_DURATION = 60    # Global hard cap on any effect's turn count
GRACE_TURNS         = 3     # Post-hard-control immunity window
```

### `BUFFS` (frozenset)
```python
{
  # Movement / perception / combat buffs
  'hasted', 'invisible', 'levitating', 'regenerating', 'telepathy',
  'warning', 'searching', 'clairvoyant', 'displacement', 'heroism', 'brilliance',
  'shielded', 'fire_shield', 'cold_shield', 'reflecting', 'phasing', 'time_stopped',
  'blessed', 'invulnerable',
  # Resistance effects (can be timed or permanent)
  'fire_resist', 'cold_resist', 'shock_resist', 'poison_resist',
  'sleep_resist', 'magic_resist', 'drain_resist', 'disint_resist',
  # Accessory-granted permanent buffs
  'life_save', 'sustained', 'truesight', 'dark_vision', 'identify_sight', 'spell_turning',
  'riposte_armed', 'parry_armed', 'see_invisible',
  # Hero special buffs (Phase 3B)
  'stand_ac', 'crit_buff', 'fear_immune', 'boomstick_aoe_next', 'berserk',
  # Chain combat v2 (v2.14.0) player-side buffs
  'blade_flow', 'melee_dmg_reduction',
  # Post-lock grace buff (set when a hard-control effect expires)
  'control_immune',
  # Cooked / power "ward" buffs — timed saving-throw bonuses
  'save_guard_CON', 'save_guard_WIS', 'save_guard_DEX', 'save_guard_all',
}
```
**v2.18.0 note:** `berserk` was previously double-classified (BUFFS + DEBUFFS). It grants +STR damage at the cost of HP/turn — net buff behavior — so it's a BUFF only. `abjuration` / `cancellation` / `dispel_magic` correctly strip it as an enchantment on the target now.

### `DEBUFFS` (frozenset)
```python
{
  # Classic NetHack debuffs
  'paralyzed', 'sleeping', 'stunned', 'confused', 'blinded', 'hallucinating',
  'poisoned', 'diseased', 'petrifying', 'strangulation', 'fumbling',
  'slowed', 'aggravated', 'teleportitis',
  # Mind-affecting / social
  'feared', 'charmed', 'cursed', 'weakened',
  # DoTs / curses
  'bleeding', 'doomed', 'draining', 'burning', 'frozen', 'corroding',
  # Movement locks
  'immobilized', 'in_pit', 'silenced',
  # Alternate potion label (same semantics as hallucinating)
  'hallucinating_pot',
  # Engine wave 3 (2026-05-30): Gae Dearg's wound-lingers
  'heal_blocked',
  # v2.18.0 audit sync: Laevateinn's doom_dot was in EFFECT_INFO but missing here
  'doom_dot',
  # Chain combat v2 (v2.14.0) weapon chain-special monster debuffs
  'armor_crack', 'sundered', 'deep_wound', 'ruptured', 'impaled',
  # v2.15.0: crossbow reload cooldown (sits here only so tick_all decrements it)
  'reloading',
}
```
**v2.18.0 note:** `doom_dot` was missing from DEBUFFS despite having an EFFECT_INFO row — status HUD and strip-debuffs paths dropped it silently. Fixed.

### `HARD_CONTROL` (frozenset)
```python
{'paralyzed', 'sleeping', 'immobilized', 'stunned', 'frozen', 'petrifying'}
```
Zero / near-zero player actions. Save NEGATES; cannot be re-applied while active or during the 3-turn grace.

**v2.18.0 note:** `petrifying` was moved into HARD_CONTROL. Its `val==1` tick fires the `_petrify_death` signal, so a half-duration save-halve could still kill. HARD_CONTROL semantics make a successful CON save negate it outright.

**v2.18.0 note:** `stunned`'s *gameplay* is soft (player still acts, with a -25% quiz timer + stumble), but it's deliberately kept in HARD_CONTROL so a successful save fully negates it and cannot be re-applied in the grace window. Removing it would allow fast monsters to stunlock the player to death. The SYSTEMS_AUDIT.md §9 P2 flagging on `stunned` is a known-but-chosen tradeoff.

### `SOFT_CONTROL` (frozenset)
```python
{'confused', 'feared', 'charmed', 'slowed'}
```
Degraded but not frozen. Save HALVES duration; refreshes to `max(current, new)` instead of stacking.

### `CONTROL`
```python
CONTROL = HARD_CONTROL | SOFT_CONTROL
```

### `SAVE_STAT: dict[effect_id -> stat]`
D&D-style saving throw category per effect:
```python
{
  'paralyzed': 'CON', 'sleeping': 'CON', 'stunned': 'CON', 'frozen': 'CON',
  'petrifying': 'CON',
  'confused':  'WIS', 'feared':   'WIS', 'charmed':  'WIS',
  'slowed':    'DEX', 'immobilized': 'DEX',
}
```
- CON (body) — physical disables.
- WIS (will) — mind-affecting.
- DEX (reflex) — movement locks.
- Effects **not in this map** (poison, bleed, burning, doom_dot, …) bypass the stat-save roll but still receive a CON-based duration reduction via `save_bonus_for('CON')` (v2.18.0 fix — see [save_bonus.md](save_bonus.md)).

### `CONTROL_CAP: dict[effect_id -> max_turns]`
Hard cap on a SINGLE application's duration. Clamps egregious data values so one failed save can't exceed design headroom:
```python
{
  'paralyzed': 4, 'sleeping': 5, 'stunned': 3, 'frozen': 4, 'immobilized': 4,
  'confused':  6, 'feared':   6, 'charmed':  6, 'slowed':    6,
}
```

### `_RESIST_BLOCKS: dict[resist_effect -> set[blocked_effect]]`
Hard immunity table. If the resist effect is active, the listed debuffs are refused outright at `apply_effect`'s first branch (before the save math):
```python
{
  'poison_resist': {'poisoned', 'diseased'},
  'sleep_resist':  {'sleeping', 'paralyzed'},
  'drain_resist':  {'diseased', 'draining'},     # v2.18.0: draining now blocked
  'fire_resist':   {'burning'},
  'cold_resist':   {'frozen'},
  'magic_resist':  {'confused', 'charmed', 'silenced', 'feared',
                    'hallucinating', 'hallucinating_pot'},
}
```
**v2.18.0 note:** `drain_resist` now blocks `draining` (the ring-of-strength-drain HP tick) — the display name "Drain Resist" now matches behavior. `diseased` is retained for symmetry with poison_resist.

### `DAMAGE_IMMUNITY: dict[damage_type -> immunity_status]`
Used by `Player.take_damage` to short-circuit incoming typed damage:
```python
{'fire': 'fire_resist', 'cold': 'cold_resist',
 'lightning': 'shock_resist', 'poison': 'poison_resist',
 'drain': 'drain_resist', 'magic': 'magic_resist'}
```

### `SHIELD_IMMUNITY: dict[damage_type -> shield_status]`
Overrides `DAMAGE_IMMUNITY` when the player has a shield effect active:
```python
{'fire': 'fire_shield', 'cold': 'cold_shield'}
```

### `_EXPIRE_MSGS: dict[effect_id -> (text, message_type)]`
HUD log line fired when a timed effect expires. Message types: `'info'`, `'success'`, `'warning'`, `'danger'`. v2.18.0 audit added the previously-missing entries for: `doom_dot`, `petrifying`, `armor_crack`, `sundered`, `deep_wound`, `ruptured`, `impaled`, `heal_blocked`, `blade_flow`, `save_guard_*` (4), `fear_immune`, `control_immune`, `parry_armed`, `riposte_armed`, `see_invisible`, `warning`, `searching`, `truesight`, `dark_vision`, `identify_sight`, `life_save`, `reloading`, `boomstick_aoe_next`, `crit_buff`, `stand_ac`, `melee_dmg_reduction`.

### Material categorization (gear damage from statuses)
```python
_RUSTPROOF = {'diamond', 'mithril', 'adamantine', 'dragonbone', 'dragonscale',
              'dragon scale', 'crystal', 'obsidian', 'divine', 'divine silk',
              'enchanted plate', 'spectral iron'}

_ORGANIC   = {'cloth', 'leather', 'hide', 'fur', 'silk', 'linen', 'wool', 'padded',
              'enchanted cloth', 'wood', 'hardwood', 'yew', 'ironwood', 'bone', 'fang'}

_FLAMMABLE = {'cloth', 'leather', 'hide', 'fur', 'silk', 'linen', 'wool', 'padded',
              'enchanted cloth', 'wood', 'hardwood', 'yew', 'bone'}
```
Consumed by `_can_corrode` / `_can_rust` / `_can_scorch` which the `corroding` / `burning` tick branches read to pick a random equipped-gear target and apply `-1 enchant_bonus` (down to -3 floor). `_corrode_random_gear`: 25% per-tick chance; `_scorch_random_gear`: 20%.

## Flow — public API

### `apply_effect(player, effect: str, duration: int) -> bool`
The one write path for status durations. Returns True if applied; False if blocked.

Decision order:
1. **`_RESIST_BLOCKS` short-circuit**: if any resist in the table covers this effect AND the player has that resist active, return False immediately. (This is why save bonuses do not stack with immunity.)
2. **Permanent (`-1`) guard**: if the effect is already permanent, refuse any further write.
3. **`duration == -1` write**: set permanent.
4. **`effect in CONTROL`**: clamp duration by `CONTROL_CAP`. Then:
   - **HARD_CONTROL**: refuse re-apply if already active OR if `control_immune` is in the grace window. Otherwise set `min(duration, MAX_EFFECT_DURATION)`.
   - **SOFT_CONTROL**: refresh to `max(current, duration)`, clamped. Never stacks.
5. **Everything else** (DoTs, buffs, resistances): `current + duration`, clamped to `MAX_EFFECT_DURATION`. Additive stacking is the non-CONTROL default.

**Call sites:** every effect-application path in the game routes through here, usually via `Player.add_effect`. Direct call sites include `food_system.py:289` (cooked wards write `save_guard_*` + magnitude), `game_magic.py` self-buff dispatchers (haste/shield/invis via `_SELF_BUFF_DURATIONS`), spell/wand effect handlers, and chain-combat weapon procs.

### `apply_debuff_with_save(player, effect, duration, dc) -> (applied: bool, message: str)`
MONSTER-inflicted debuffs route here (not through plain `apply_effect`). Two-gate model: the caller already passed the monster's `effect_chance` (skill at landing the blow). Here the player rolls `d20 + stat_mod + save_bonus` vs the DC:

```python
stat  = SAVE_STAT.get(effect)     # 'CON' / 'WIS' / 'DEX' or None
mod   = (int(getattr(player, stat, 10)) - 10) // 2
bonus = player.save_bonus_for(stat)
roll  = randint(1, 20) + mod + bonus
```

Branches:
- **No SAVE_STAT entry** (poison, bleed, burning, disease, doom_dot, …): the save roll is skipped, but `save_bonus_for('CON')` reduces the applied duration by a flat amount (floor 1). `applied = player.add_effect(effect, max(1, duration - sb))`. Message: `"You are <effect>!"` on success, `""` on refuse. (v2.18.0 fix — previously bypassed `save_bonus_for` entirely, so Torque of Lugh's `{all: 3}` didn't help against DoTs despite the text.)
- **`roll >= dc` + HARD_CONTROL**: full negate. Returns `(False, "<flavor> throws off the <noun>!")`. Flavor by stat: CON → "Your hardy constitution"; WIS → "Your strong will"; DEX → "Your quick footwork".
- **`roll >= dc` + SOFT_CONTROL**: half duration (floor 1). `applied = player.add_effect(effect, max(1, duration // 2))`. Message: `"<flavor> blunts the <noun> — it barely takes hold."`.
- **`roll < dc`** (failed save): full duration. `applied = player.add_effect(effect, duration)`. Message: `"The <noun> takes hold!"`.

Flavor messages read as player-feels-stat, not dice-and-DCs. Effect nouns via `_EFFECT_NOUN` (e.g. `'stunned' → 'stun'`, `'petrifying' → 'petrification'`). The return `applied` is always `add_effect`'s result — if a resist short-circuits even after a failed save, nothing lands.

**Call sites:** `monster.py:705` (generic monster-attack path, covers all ~332 monster melee/attack debuffs — see SYSTEMS_AUDIT.md §9 VERIFIED OK). Gaze attacks also route through this.

### `tick_all(player, dungeon=None) -> list[(text, type)]`
Advance one turn for every effect in `player.status_effects`. Returns a batched list of HUD messages. May mutate `player.hp` / stats / `status_effects`. Called once per player turn from `main.py:3158` (`self.player.tick_effects()`).

Flow:
1. **Grendel-grip pre-tick** (Coif of Beowulf armor proc): clears `paralyzed` / `strangulation` / `sleeping` immediately. The grip that strangled Grendel keeps you free.
2. **Per-effect dispatch** (ordered as they appear in `player.status_effects`):
   - `poisoned` + not `poison_resist` → 1 physical-type-poison damage; "The poison burns through you!"
   - `diseased` + not `poison_resist` AND not `drain_resist` → 8% / turn STR or CON -1 (dispatches `_disease_drain:<stat>:1` for Paracelsus quirk; UI line "The disease saps your strength! <stat> -1.")
   - `strangulation` → 2 physical damage; "You are being strangled!"
   - `regenerating` → +1 HP if below max
   - `petrifying` → threshold messages at val≤10, val≤6, val≤3; **`val==1`** emits the `_petrify_death` signal (death)
   - `bleeding` → 1 physical damage; "You are bleeding!"
   - `doomed` → 12% / turn -1 HP; "The doom curse gnaws at your life force!"
   - `draining` → 17% / turn -1 HP (now gated by `drain_resist` via `_RESIST_BLOCKS`); "The ring drains your life force!"
   - `burning` + not fire_resist/fire_shield → 1 fire damage + `_scorch_random_gear` (20% chance of -1 enchant on a flammable equipped item, floor -3)
   - `corroding` → `_corrode_random_gear` (25% chance of -1 enchant on a non-rustproof equipped item, floor -3)
   - `teleportitis` → 4% / turn emits `_teleport` signal
   - `weakened` / `frozen` — passive flags read at combat sites, no per-turn work here
3. **Decrement + queue expiry**: `val > 0` decrements by 1; expired keys go to `to_expire`.
4. **Expiry cleanup**:
   - Any HARD_CONTROL expiry grants `control_immune = GRACE_TURNS` (3 turns).
   - `save_guard_*` expiry pops the magnitude from `player._save_guard[<cat>]`.
   - `heroism` expiry: `apply_stat_bonus('STR', -2)`.
   - `brilliance` expiry: `apply_stat_bonus('INT', -1)` + `apply_stat_bonus('WIS', -1)`.
   - `stand_ac` expiry: `_stand_ac_bonus = 0` + `_stand_counter_pct = 0`.
   - `berserk` expiry: `player.STR -= _berserk_str_bonus` (direct STR write, not via `apply_stat_bonus`, because berserk is a combat damage bonus not a full stat buff).
   - Append `_EXPIRE_MSGS[effect]` to the output.

**Special signals** returned via messages (consumed by `main.py`):
- `'_teleport'` — teleport the player to a random tile.
- `'_petrify_death'` — player fully turns to stone.
- `'_disease_drain:<stat>:1'` — dispatch to Paracelsus quirk hook.

### `Player.add_effect(name, duration) -> bool`
Thin wrapper around `apply_effect` with a few additional policy gates:
- **Hermes quirk**: `hasted` duration is doubled when `quirk_progress.hermes_active`.
- **Will to Power hero passive**: `feared` / `charmed` refused when HP ≤ 30% of max.
- **Fear immunity**: `feared` refused while `fear_immune > 0` (Ash Williams' berserk chain ≥ 3).
- All other effects pass through to `apply_effect` unchanged.

(The retired Perseus "halve all debuff durations" branch previously lived here; it was converted to a `{all: +2}` save bonus and the branch deleted — see save_bonus.md history.)

### `Player.has_effect(name) -> bool`
`self.status_effects.get(name, 0) != 0`. The non-zero check means `-1` (permanent) counts.

### `Player.tick_effects() -> list[(msg, type)]`
Thin wrapper around `tick_all(self)`. Called once per player turn from `main.py:3158`.

## Invariants (don't break)

- **One-write-path:** all duration writes go through `apply_effect` (or `apply_debuff_with_save` which calls `add_effect` which calls `apply_effect`). The only in-tree exception is `grendel_grip`'s direct zeroing in `tick_all` and expiry stat-reversals.
- **`_RESIST_BLOCKS` short-circuits before saves:** full immunity never routes through the save math. If you move a check past this branch, you break the "resists + saves don't overlap" rule.
- **HARD_CONTROL anti-permalock:** cannot be refreshed, re-applied while active, or re-applied within the 3-turn grace. Monsters that reliably cast paralysis must never permalock. Grace window = `GRACE_TURNS = 3`.
- **SOFT_CONTROL refreshes, never stacks:** `max(current, new)`. Non-CONTROL effects use `current + new` additive stacking — asymmetric, intentional.
- **`MAX_EFFECT_DURATION = 60`:** every write clamps at this. CONTROL further clamps by `CONTROL_CAP`.
- **Permanent (`-1`) effects are immutable** via `apply_effect` — direct `status_effects[k] = -1` writes exist (intrinsic resistances from gear) and must be explicit.
- **`save_guard_*` is a BUFF**, not a DEBUFF — register in BUFFS, or cleanses will wipe the player's own wards.
- **`berserk` is a BUFF only (v2.18.0 fix).** It is NOT in DEBUFFS. If you double-classify, dispel_magic's dispatch becomes ambiguous.
- **`doom_dot` lives in DEBUFFS + has an `_EXPIRE_MSGS` entry.** Previously missing from both — don't re-regress.
- **`drain_resist` blocks `draining` + `diseased`.** (v2.18.0 — "Drain Resist" display name now matches behavior.)
- **`petrifying` is in HARD_CONTROL** (v2.18.0 fix). Save NEGATES; a halved duration could still kill via the val==1 death tick.
- **`stunned` stays in HARD_CONTROL** despite being semantically soft — removing it reopens the fast-monster stunlock death-spiral.
- **DoTs still land on saves** (poison/bleed/burning/doom_dot): save only reduces duration by `save_bonus_for('CON')`, min 1 turn. "Resource loss IS the penalty."
- **`control_immune` is a BUFF.** It's set BY tick_all when hard-control expires, and consumed BY apply_effect's HARD_CONTROL guard. Never set it from gameplay code directly.

## Interactions

- **[save_bonus](save_bonus.md)** — the gradient layer between "no defense" and "immunity." `apply_debuff_with_save` reads `player.save_bonus_for(stat)` as the +N on the d20 roll. Non-SAVE_STAT effects use `save_bonus_for('CON')` for duration reduction.
- **[quiz_engine](quiz_engine.md)** — identify-v3 failures apply `stunned 10t`. Timer modifier is read from `has_effect('blinded' / 'stunned' / 'confused' / 'hallucinating' / 'blessed')` (see quiz_engine.md "Status-effect timer modifiers").
- **[combat](combat.md)** — chain-combat-v2 weapon procs write statuses (`armor_crack`, `sundered`, `deep_wound`, `ruptured`, `impaled`, `blade_flow`, `melee_dmg_reduction`) via `apply_effect`. `take_damage` checks `DAMAGE_IMMUNITY` / `SHIELD_IMMUNITY` short-circuits.
- **[magic](magic.md)** — self-buffs use `_SELF_BUFF_DURATIONS` (game_magic.py:1848) to scale duration by chain_scale. Chain-5 shield spell → 12 × 5 = 60t (capped at MAX_EFFECT_DURATION). `dispel_magic` / `cancellation` / `drain_magic` strip BUFFS from target; `abjuration` currently strips ALL statuses (SYSTEMS_AUDIT.md §9 P1 flagged — should match the others).
- **[monsters](monsters.md)** — monster attacks route debuffs through `apply_debuff_with_save` at `monster.py:705`. 17/17 effect ids in monster attacks map to real EFFECT_INFO entries (VERIFIED OK).
- **[items](items.md)** — permanent accessory buffs (`life_save`, `sustained`, `truesight`, `dark_vision`, `identify_sight`, `spell_turning`) are written as `-1` on equip, cleared on unequip. Resistances from gear can be timed OR permanent.
- **[food_system](food_system.md)** — cooked wards (`save_guard_CON/WIS/DEX/all`) write a BUFF status + magnitude via `_TEMP_POWER_REMAP` → `food_system.py:289`. See [save_bonus.md](save_bonus.md).
- **[karma_prayer](karma_prayer.md)** — prayer branches apply/strip statuses (Blessed, Divine Intercession = `invulnerable`, Fisher King healing, etc.).

## History of major decisions

- **Mid-2026** — `apply_debuff_with_save` added (D&D-style saves). The engine switched from flat "effect_chance" rolls to a two-gate model (monster hit chance → player save). Massive playability win.
- **2026-05-30** — Chain-combat-v2 statuses added (armor_crack / sundered / deep_wound / ruptured / impaled / blade_flow / melee_dmg_reduction). Grendel-grip tick-clear added for Coif of Beowulf.
- **2026-06-03** — Save-bonus audit (`docs/design/save_bonus_audit.md`); Option B shipped. `save_guard_*` ward family added; Perseus halve-debuffs branch retired → `{all: +2}` save bonus.
- **2026-08-06** — Identify v3 ships. Stun-on-fail becomes the ID failure cost (not a mastery hit). `stunned` kept in HARD_CONTROL for anti-stunlock despite soft semantics.
- **2026-10-02 (v2.18.0 audit sync wave):**
  - `petrifying` moved into `HARD_CONTROL` (saves now negate instead of halving).
  - `berserk` removed from `DEBUFFS` (was double-classified; now BUFF-only).
  - `doom_dot` added to `DEBUFFS` + `_EXPIRE_MSGS`.
  - `drain_resist` now blocks `draining` in `_RESIST_BLOCKS` (display name matches behavior).
  - `apply_debuff_with_save` non-SAVE_STAT branch now respects `save_bonus_for('CON')` (Torque of Lugh `{all: 3}` finally helps against poison/bleed).
  - 13 spell duration descs synced to code values (stoneskin 30→25, greater_haste 25→10, phase_door 12→15, reflect 20→15, counterspell 15→12, detect_monsters 15→20, imprisonment 40→60, paralyze 10→8, hold_monster 5→8, slow 6→10, fear 8→10, magic_shield_spell distinct from mage_armor_spell at T3=20, annihilate / power_word_kill chain=5 fossil deglazed).
  - 24+ `_EXPIRE_MSGS` entries added for previously-silent expiries (armor_crack, sundered, deep_wound, ruptured, impaled, heal_blocked, blade_flow, save_guard_*, etc.).
  - `_EFFECT_NOUN['stunned']` fixed: 'daze' → 'stun' (save-flavor now matches expire-flavor).

## Testing
- `tests/test_status_lock.py` (308 lines) — pins:
  - HARD_CONTROL cannot be re-applied while active.
  - Single-application CONTROL_CAP enforcement.
  - SOFT_CONTROL refreshes (never stacks).
  - DoTs + buffs still stack additively.
  - Post-hard-control grace window blocks relock.
  - "Reapply every turn" cannot permalock.
  - Save NEGATES hard control.
  - Save messages are flavor, not math.
  - Save MINIMIZES soft control to half.
  - Failed save applies full duration but still capped.
  - `SAVE_STAT` mapping sanity.
  - `save_bonus_for` sums permanent lanes + hard-cap.
  - Timed-ward companion gated by status + capped at +3.
  - `_save_guard` cleared on ward expiry.
  - Save bonus actually improves save odds (statistical test).
  - Cooked-ward grants status + sets capped magnitude.
  - Cooked-ward amount clamped to +3.
  - Cooked-ward defaults to +2 when unspecified.
  - Control-resist remap targets are wards (not plain resists).
  - Bad-food control routes through save-failure landing.
  - Bad-food control save can negate hard control.
  - Bad-food noncontrol debuff unchanged.
- `tests/test_effect_wiring.py` — pins each effect's registration symmetry (EFFECT_INFO ↔ BUFFS/DEBUFFS presence).
- `tests/test_death_from_status_tick.py` — pins Stunned-10t-on-identify-fail still ticks + expires cleanly.
- `tests/test_effect_duration_dice.py` — pins effect duration dice parse + scale correctly.
- `tests/test_buc_effects.py` — pins BUC-driven buff/debuff application paths.

## Known rough edges

From SYSTEMS_AUDIT.md §9:
- **P1** — `game_magic.py::abjuration` (line 1065-1086) calls `target.status_effects.clear()` on the monster, stripping player-applied DoTs (poisoned/burning/petrifying/bleeding). Inconsistent with `cancellation` / `dispel_magic` / `drain_magic` which strip BUFFS only. Pre-v2-audit dispatch rot.
- **P1** — `game_magic.py::magic_missile` handler (line 1876) bypasses `_spell_damage` and `MAGIC_TIER_MULT`. Force-family spells under-scale relative to all other damage families.
- **P2** — `status_effects.py::stunned` cap=3 but semantic is soft (may stumble, quiz timer -25%). HARD_CONTROL's "no refresh, no reapply, +3 grace" is an over-strong anti-stunlock. Known tradeoff — kept because removing it reopens the fast-monster-stunlock death-spiral.
- **P2** — `spells.py::elder_scream` — `mp_cost: 10` at `tier: 2`. Outside T2 5-8 MP band.
- **P3** — `MAX_EFFECT_DURATION=60` with additive stacking on non-CONTROL effects is asymmetric with CONTROL's refresh-max. Non-CONTROL stacking stays additive by design (regen + regen = longer regen), but worth noting.
- **P3** — Alternate potion label `hallucinating_pot` has identical semantics to `hallucinating`; two ids exist so UI can tell them apart in flavor text. Verify both are in all the right sets if you touch either.
- **P3** — `cook_outcomes.json::trophy_medusa::temp_power = "petrify_resist"` is non-canonical; works only via the legacy `food_system._TEMP_POWER_REMAP` alias → `save_guard_CON`. Data lies to itself (self-comment says "canonical status_effects"). Pending cleanup.
