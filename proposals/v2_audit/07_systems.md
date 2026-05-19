# V2 Audit — 07 Systems (Spells, Prayers, Statuses, Quirks, Hero Specials, Class Masteries)

Scope: `src/game_magic.py`, `src/game_divine.py`, `src/status_effects.py`,
`src/quirk_system.py`, `src/hero_specials.py`, `src/class_masteries.py`.
Read-only audit; no balance/semantics changes made.

Tests: `py -m pytest tests/ -q` -> **476 passed in 63.45s**.

---

## Critical findings (would crash or silently break on use)

### A. Spells with no handler in `_apply_spell_effect` (silent no-op or wrong fallback)
`game_magic.py:1128 _apply_spell_effect` dispatches by `effect` string. Nine
spell effects defined in `LEARNABLE_SPELLS` are never matched — for
non-targeted spells they silently no-op (MP is spent, nothing happens); for
the one targeted case, the player gets the bottom-of-function generic-damage
fallback at line 1744-1750 instead of the intended dispel.

| spell_id | effect | needs_target | result today |
| --- | --- | --- | --- |
| `detect_magic_spell` | `identify_item` | False | silent no-op (MP wasted) |
| `sleep_mass_spell` | `mass_sleep` | False | silent no-op |
| `mass_paralyze_spell` | `mass_sleep` | False | silent no-op |
| `levitate_spell` | `levitation_self` | False | silent no-op |
| `mapping_spell` | `mapping` | False | silent no-op |
| `phase_door_spell` | `phase_self` | False | silent no-op |
| `turn_undead_spell` | `turn_undead` | False | silent no-op |
| `wish_spell` | `wish` | False | silent no-op |
| `annihilation_spell` | `annihilate` | False | silent no-op |
| `dispel_magic_spell` | `dispel_magic` | True | targeted-fallback damage, not dispel |

Same effect name handlers DO exist in `_apply_wand_effect` for several of
these (`mapping`, `identify_item`, `mass_sleep`, `wish`, `turn_undead`,
`annihilate`). The spell dispatcher does not call into the wand dispatcher;
these are duplicated functionality that was never wired for the spell side.

These spells fail silently on every cast — no exception, no crash, but the
player has no way to know the spell isn't working. **High-impact bug**.

### B. Class mastery kinds with no use-site
`class_masteries.py` declares blessings whose comment at `game_magic.py:2443-2448`
claims they are "lazy/passive — query `player.unlocked_class_masteries` at
use-site". Verified by grep: there is **no read site** for
`unlocked_class_masteries` anywhere in `src/` except the initializer in
`player.py:144` and the writer in `game_magic.py:_claim_mastery`. So the
following kinds resolve to nothing when mastered:

| kind | classes affected | status |
| --- | --- | --- |
| `class_acc_ac_bonus` | `ring_of_protection` | declared lazy, no read site |
| `class_acc_regen_bonus` | `ring_of_regeneration`, `amulet_of_regeneration` | declared lazy, no read site |
| `class_acc_passive_radius` | `ring_of_searching/telepathy/warning/clairvoyance` + 3 amulets | declared lazy, no read site |
| `class_acc_resist_bonus` | 7 resist-ring/amulet classes | declared lazy, no read site |
| `class_acc_sp_burn_bonus` | `ring_of_sustenance` | declared lazy, no read site |
| `class_acc_quirk` | `ring_of_speed/invisibility/levitation/displacement` | declared lazy, no read site |
| `class_scroll_potency` | `scroll_of_heal/extra_heal` | declared lazy, no read site |
| `class_scroll_persist` | `scroll_of_mapping` | declared lazy, no read site |
| `class_scroll_extra_uses` | `scroll_of_identify/teleport` | declared lazy, no read site |
| `class_acc_buff_duration_bonus` | default-blessing fallback for accessories | declared lazy, no read site |
| `potion_potency_bonus` | `potion_of_healing/extra_healing/full_healing` + uniques | only declared, not read at potion drink |
| `potion_duration_bonus` | `potion_of_speed/strength` | declared lazy, no read site |

The eagerly-applied kinds (`class_acc_stat_bonus`, `wand_extra_charge`,
`spellbook_mp_discount`, `accessory_stat_bonus`) DO work because
`_apply_mastery_once` mutates state at mastery time.

Player-visible message reads "Mastery gained: …" but the bonus is real for
only 12 of 47 mastery classes today.

### C. Status effects referenced but not defined
- **`parry_armed`** (combat.py:572-573, player.py:469) — gives +2 AC for 2
  turns from quarterstaff defensive_parry at chain 5. Has no entry in
  `EFFECT_INFO`, not in `BUFFS`, no expiry message, no UI label. Functional
  (the dict read returns 0 when absent) but it's an orphan effect:
  no visible status badge, no expiry message, never decremented anywhere
  visible in this audit's scope.
- **`see_invisible`** (main.py:1374, main.py:3517) — checked when stepping
  into dark rooms (`has_effect('see_invisible')`) and shown as a UI label
  in the buff list. No entry in `EFFECT_INFO`, no `BUFFS` membership. Read
  only — nothing ever sets it. Permanent no-op.

Note: `_pending_chain_escape` and `_pending_elder_escape` are intentional
single-tick signal flags (main.py:2194, 2199) and `stuck_in_pit` is used on
monsters (not on player), so those three are NOT broken — they're patterns
that happen to live in `status_effects` dicts.

---

## Other findings (not critical — flag for design review)

### Spells: handler fallback is wrong subject
`game_magic.py:1744` falls back to "generic targeted damage" for any
unmatched targeted effect. This means a bug or typo in a spell effect's name
silently turns it into a damage spell. Better: log a warning and refund MP.

### Class mastery `default_blessing_for_class` produces unimplemented kinds
`class_masteries.py:344-358` returns `class_acc_buff_duration_bonus` (no
use-site) and `potion_potency_bonus` (no use-site) as fallbacks. Both will be
silently broken if they ever fire.

### Status effect `disint_resist` defined but never referenced
`EFFECT_INFO['disint_resist']` exists and is in `BUFFS`, but no item or
mechanic in `src/` grants or checks for it. Either flag for removal or wire
it to the disintegration kill chance.

### Status effects defined but never referenced in src/
- `doomed` (definition present, tick handler exists in status_effects.py
  itself — applied by some item somewhere; partial)
- `draining` (definition + tick, applied by cursed ring presumably)
- `strangulation` (definition + tick, no grant site found in src/)
- `teleportitis` (definition + tick, no grant site found)

These all have working tick handlers; they just don't have any visible grant
path in the code I audited. May be granted from JSON-driven items via
`add_effect` strings in the items dataset (not in my scope).

### Quirks system — clean
- 100 quirks defined across `_QUIRK_NAMES`, `_QUIRK_PROGRESS`, `_QUIRK_TRIGGER`,
  `_QUIRK_EFFECTS` — all four dicts have identical keys (no orphans either
  direction).
- 30 power quirks in `_ACTIVE_POWER_DEFS`; all 30 names present in the master
  `_QUIRK_NAMES` table.
- All hooks (`on_kill`, `on_quiz_answer`, `on_move`, `on_take_damage`,
  `on_status_applied`, etc.) consistently use the `_QUIRK_PROGRESS` key
  before unlocking. No "defined but never reachable" quirks found.
- `_DEBUFF_EFFECTS` in `quirk_system.py:13-16` is a duplicate of part of
  `DEBUFFS` from `status_effects.py:97-104`. Drift risk if one is updated
  but not the other; flag for consolidation.

### Hero specials — clean
- 19 active specials across 22 builds; every `effect` key resolves to a
  handler in `_DISPATCH` (verified by cross-ref script).
- 10 hero passives across 9 builds; all 10 passive strings have ≥1 use-site
  in `combat.py` / `player.py` / `main.py` / `monster.py` / `game_menus.py`.
  No orphan passive names.

### Prayers — clean
- 8 prayer ids in `PRAYERS`; all 8 have handlers in the `dispatch` dict
  (`game_divine.py:962-971`). Cooldowns 100-280t range correctly enforced
  via `prayer_cooldown` baseline `max(100, 80 + effective * 25)` and
  `cooldown_bonus_full` extras up to +400.
- Karma gates correct: damned (-10) blocks all but Pater Noster; fallen (-6)
  blocks specialty prayers. Verified by reading both `_start_pray` menu
  building (line 832-863) and `_resolve_specific_prayer`.

### Spellbook -> spell_id mapping is complete
Every `spell_id` in `data/items/spellbook.json` (51 entries) has a
corresponding entry in `LEARNABLE_SPELLS`. The reverse — 8 unused
LEARNABLE_SPELLS entries (`sign_*`, `elder_*`) are intentional: they're
character-build signature spells loaded directly into `player.known_spells`
at character creation, not via spellbook drops. Confirmed by `spells.py:14`
docstring.

### Damage immunity / shield immunity / debuffs lists current
- `DAMAGE_IMMUNITY` covers fire/cold/lightning/poison/drain/magic — every
  damage type used by wand/spell handlers I read maps cleanly.
- `SHIELD_IMMUNITY` covers fire/cold; both checked in `take_damage`-style
  flows (not in scope to verify, but the data is intact).
- `_RESIST_BLOCKS` includes magic_resist blocking confused/charmed/silenced/
  feared/hallucinating (per 2026 memory note). Consistent.

---

## Auto-fixes applied
None. All findings here are either bugs requiring design decisions (e.g.
"should `mapping_spell` reuse the wand handler, or have its own?") or
non-critical inconsistencies. No obvious dict typos found.

---

## Suggested follow-up (not done as part of this audit)

1. **Wire up the 10 missing spell handlers** in `_apply_spell_effect`. Most
   can re-use the wand-side implementations almost verbatim. Highest player
   impact: `mapping_spell`, `wish_spell`, `levitate_spell`, `dispel_magic_spell`.
2. **Wire up the 35 mastery-class blessings** that currently no-op. Either:
   - Add use-site reads in `player.py` (AC, regen, passive radius, resist,
     SP burn, quirk extends) and `food_system.py` (potion potency/duration);
     OR
   - Demote them to one-shot eager applies in `_apply_mastery_once`.
3. **Decide on `parry_armed`** — add to `EFFECT_INFO` + `BUFFS` so it shows
   in the UI, or rename to `riposte_armed` (its near-twin) and consolidate.
4. **Decide on `see_invisible`** — add to `EFFECT_INFO` and find an item
   that grants it, or remove the read and rely on `truesight` (already
   defined and has the "see all monsters regardless of invisibility"
   description).
5. **Consolidate `_DEBUFF_EFFECTS`** in `quirk_system.py` with `DEBUFFS` in
   `status_effects.py` — import the canonical set instead of duplicating.
