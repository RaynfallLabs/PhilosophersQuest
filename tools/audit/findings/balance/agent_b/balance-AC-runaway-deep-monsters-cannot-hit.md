---
id: balance-ac-runaway-deep-monsters-cannot-hit
dimension: balance
severity: P2
title: At full L100 loadout AC reaches ~-33; regular deep-floor monsters need d20 = 17+ to land hits, and bosses are floored at 25% hit
status: open
systems: [armor, shields, accessories, combat_to_hit, monsters]
floors_affected: [60, 100]
evidence:
  - balance_curves_agent_b.json:player_baseline.best_ac_reachable_at_L100
  - balance_curves_agent_b.json:armor_by_min_level (adamantine_armor ac 9, helm 5, etc.)
  - balance_curves_agent_b.json:shields_by_min_level (tower_shield_of_ajax ac 6)
  - src/player.py:238-264 (get_ac())
  - src/monster.py:268-285 (to_hit = thac0 - player_ac, min_hit_chance)
discovered: 2026-05-15
---

## What's out of balance

Computed in `balance_curves_agent_b.json :: player_baseline`: best per-slot armor (head 5, body 9, arms 3, hands 3, legs 4, feet 3, cloak 3, shirt 2 = 32 total) + best shield (tower_shield_of_ajax ac 6) + DEX 20 mod (+5) → **AC = 10 - 5 - 32 - 6 = -33**.

A regular deep monster (e.g. an ancient dragon, thac0 ≈ -16 — and -16 is the floor among deep monsters per `balance_curves_agent_b.json :: monsters_by_floor[L80+].min_thac0`) computes `to_hit = thac0 - AC = -16 - (-33) = 17`. They need a natural d20 of 17 or higher (≈ 20%) to hit on the roll. The `min_hit_chance = 0.05` for non-bosses (`monster.py:275`) is the floor — but ALL the regular monsters at deep floors still fall back to a 5% floor on a fail-the-roll.

Bosses have `min_hit_chance = 0.25` (`monster.py:275`) — so Abaddon, Fenrir, Fafnir DO land 25% of the time regardless of AC. That works. But the **regular spawnable population** at deep floors essentially can't touch the optimized player.

This invalidates two systems simultaneously:
1. **Armor progression**: the upgrade curve from L41 (half_plate ac 6) → L81 (adamantine_armor ac 9) only matters if THAC0 keeps pace. It doesn't; thac0 floors at -16 from L40+.
2. **Monster ecosystem at deep floors**: the AI variety (ranged, ambush, hit-and-run) is wasted because they all whiff. Only damage-on-effect (sp_drain, poison-DoT) can land. The locust SP drain at L100 becomes the only real regular-monster threat.

## Curve evidence

`balance_curves_agent_b.json :: monsters_by_floor[L41-L50].min_thac0 = -16`. Then L51-L60, L61-L70, L71-L80, L81-L90: ALL -16. There is no monster THAC0 progression past L40.

`balance_curves_agent_b.json :: armor_by_min_level` shows ac_bonus going 1→2→3→...→9 across floors 1-81. The player keeps climbing the AC mountain; monsters stop climbing the to-hit mountain at L40.

This is why `min_hit_chance` exists at all (`monster.py:275`) — the dev knew this AC inflation was happening. But applying 0.05 to regular monsters is admitting "to-hit math has stopped working." Make to-hit math work or make 0.05 floor higher.

## Suggested re-tuning

1. Add thac0 = -20 to L70+ regular monsters; thac0 = -24 to L90+. This restores progression — at -24 vs AC -33 the roll is 11+ on d20 (50% hit).
2. Raise non-boss `min_hit_chance` from 0.05 to 0.15 for monsters with min_level ≥ 60. Below that, AC scaling is fine.
3. Cap `ac_bonus` slots so a single armor slot can't exceed 6. Currently adamantine_armor ac 9 is single-handedly contributing 9/33 of the absolute AC ceiling.

Pair (1) and (3) — they fix the curve from both ends.

## Notes

- This finding sits on top of `balance-cooking-hp-softcap-defeats-late-game-threat.md`: even if AC scaling were fine, the player's HP pool absorbs everything. AC + HP together = invulnerability.
- A real test would be: `pytest -k "monster_thac0_curve"` — does the median thac0 of spawnable monsters monotonically decrease with floor? Currently it plateaus at -16 from L40 onward.
- Cross-system: armor system + monster system. Single-system polish (e.g. "this one armor is too good") is not the finding; the curve mismatch is.
