---
id: balance-quirk-stat-stacking-overflows-progression
dimension: balance
severity: P2
title: ~12 CON-granting quirks + accessory stat rings + prayer WIS bonus produce uncoordinated raw-stat inflation
status: open
systems: [quirks, accessories, prayer, player_stats]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_b.json:quirks (gawain CON+1, fenrir CON+1, leonidas CON+2, ragnarok CON+5, rasputin CON+2, green_knight CON+1, darwin CON+3, spartacus CON+1)
  - balance_curves_agent_b.json:accessories_by_min_level (ring_constitution_garnet stat CON +3 at L25, multiple variants)
  - src/quirk_system.py:1474-1577 (effect table)
  - src/game_divine.py:801-806 (prayer effective>=8 grants permanent WIS+1, max 3 times)
discovered: 2026-05-15
---

## What's out of balance

Stat bonuses are awarded by ~30 different quirks (per `_QUIRK_EFFECTS`), by stat rings (~36 at L25 per accessory pool), by prayer boons (up to +3 WIS via `prayer_boon_count`), by mystery encounters (per mystery_system.py), and by stat-granting cooked recipes (per food_system.py). None of these subsystems know about each other.

Counting just CON-granting quirks at default thresholds:
- `gawain` +1, `fenrir` +1, `green_knight` +1, `spartacus` +1 (passive +1 each)
- `rasputin` +2, `leonidas` +2 (passive +2 each)
- `darwin` +3 (passive +3)
- `ragnarok` +5 (descended to L100 with ≤10 HP)
- `caesar` +1 (all stats +1)

Theoretical max from quirks alone: 1+1+1+1+2+2+3+5+1 = **+17 CON from quirks** in a single run (most unlockable in normal play). Plus a `ring_constitution_garnet` (+3) equipped permanently. Plus +5 base = STR/CON 30+.

CON 30 → BASE_HP + 30 = 50 base, plus all cooking gains. CON 30 + ring_dexterity (+3) + DEX-quirks gives DEX 23-25. The player's stat sheet at end-of-run reads like a 20th-level D&D character.

The progression problem is **uncoordinated stacking**: each quirk was tuned in isolation (`rasputin` for survival, `darwin` for adaptation, `ragnarok` for the prophetic-descent moment), but at run-end they all stack. A "kid plays 30 hours and unlocks 60 quirks" run produces unkillable stats.

## Curve evidence

`balance_curves_agent_b.json :: quirks` enumerates every stat bonus. Filter `effect` for `CON +N`: 8 distinct quirks contribute. Filter for `WIS +N`: 6 quirks (loki +2, cassandra +1, solomon +2, diogenes +2, nostradamus +3, +"caesar all stats +1"). Filter for `DEX +N`: 4 quirks.

Compare to single-source progression in NetHack (the soft external benchmark per CONTEXT.md): stat increases come ALMOST EXCLUSIVELY from gain-stat potions/spells, with hard ceilings. PQ has the same hard ceiling implied (stats roll natural 1-25-ish on input + bonuses) but no shared budget.

## Suggested re-tuning

1. **Shared budget**: cap total quirk-granted stat bonuses to a pool, e.g. 12 points across all stats. After 12 points, quirks award alternative benefits (flavor unlock, hint, etc.) instead of stat. This makes player choice meaningful — pick which quirks to "redeem" for stat.
2. **Diminishing returns** on stat-from-quirk: 1st +N is full, 2nd +N is half, 3rd is quarter, etc. (CON ring + rasputin + leonidas + darwin = 2+2+3+1*3+... etc.).
3. **Soft cap on stats themselves**: declining HP yield once CON > 25 (similar to COOKING_HP_SOFTCAP).

Option (3) is the simplest and matches the cooking-softcap pattern that already exists.

## Notes

- This finding interacts strongly with `balance-cooking-hp-softcap-defeats-late-game-threat.md`. The cooking softcap exists; a CON softcap doesn't.
- The dev clearly thought about this for cooking (`COOKING_HP_SOFTCAP` + diminishing-returns formula `player.py:194-207`) but didn't extend the pattern to other stat sources.
- Cross-system: quirks + accessories + prayer + cooking. All grant stat bonuses. None coordinate. Single-system "this one quirk is too powerful" misses the pattern.
- Speculation: ~30-40 hour player who unlocks ~60 quirks is the intended L100-victory player. That player will benefit from the cumulative bonuses. The bonuses should be earned mastery, not unlocked auto-power.
