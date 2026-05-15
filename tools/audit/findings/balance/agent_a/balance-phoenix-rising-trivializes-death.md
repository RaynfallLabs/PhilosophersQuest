---
id: balance-phoenix-rising-trivializes-death
dimension: balance
severity: P2
title: Phoenix Rising + cooking softcap = effective 1000+ HP bonus life; trivializes Abaddon and Death-chase
status: open
systems: [quirks, food_system, bosses, death_chase]
floors_affected: [80, 100]
evidence:
  - balance_curves_agent_a.json:power_quirks (phoenix_rising uses=1, effect "Fully restore HP")
  - src/game_menus.py:808-810 (`pl.hp = pl.max_hp`)
  - balance_curves_agent_a.json:stat_scaling.max_typical_late_game_hp_with_full_cooking_softcap (~1030)
  - balance_curves_agent_a.json:boss_stats.abaddon (HP 5000)
discovered: 2026-05-15
---

## What's out of balance

Phoenix Rising is a Power-quirk (unlocked via 10 near-death survivals) that fully restores HP on use (1 charge per run). Per `power_quirks` deliverable entry and `game_menus.py:808-810`: `pl.hp = pl.max_hp`.

For a player who has invested in cooking (max_hp ~1030 per `balance-cooking-hp-economy-dominates`), Phoenix Rising effectively grants **1000+ HP of bonus life**. Combined with the chained cooking-HP economy, this provides:

- Pre-Abaddon: full HP at 1030
- Take damage during Abaddon fight, HP dips to ~50
- Trigger Phoenix Rising → instant 1030 HP back
- Continue Abaddon fight with full pool

**Net effect**: the Abaddon fight has 2x effective HP (one full pool + one full pool from Phoenix). Combined with the cooking HP pool already being 23x baseline, the player has 46x baseline HP at Abaddon vs the design intent.

For the **Death-chase escape**, Phoenix Rising is similarly potent. Death does 2d12+15 per hit (avg 28). 1030 HP / 28 = 36 hits before dying. Phoenix Rising adds 36 more "free hits" worth of buffer. Combined with prayer-freeze (see `balance-death-chase-prayer-loop`), the chase becomes a cakewalk.

Other near-instant healing quirks:
- **Life Drain** (3 uses): "Restore 25% of max HP" — at max_hp 1030, that's 257 HP per use. 3 uses = 772 HP. Roughly equivalent to a second Phoenix.
- **Rasputin** quirk (5 survivals threshold per quirk_system.py:1104): unlocks on Rasputin-style "survived near death 5 times." Mechanics give Rasputin status (need to verify in quirk_system.py).

Stacking all healing: Phoenix (1x full restore) + Life Drain (3x 25%) + prayer (full restore at effective 7+ chain) + iron_ration / metabolic SP + altar healing = effectively infinite healing if executed.

## Curve evidence

- `power_quirks.phoenix_rising`: uses=1, effect="Fully restore HP"
- `power_quirks.life_drain`: uses=3, effect="Restore 25% of max HP"
- `stat_scaling.max_typical_late_game_hp_with_full_cooking_softcap`: ~1030
- `boss_stats.abaddon.hp`: 5000
- `boss_stats.abaddon.attacks`: avg damage per hit ~25-41 piercing
- Phoenix Rising charge restoration: src/game_menus.py:808-810 — single line `pl.hp = pl.max_hp`. No cap, no scaling.

Math: A 1030-HP player taking avg 35 dmg/turn from Abaddon survives 29 turns. Phoenix at any point doubles this to 58 turns. Within 58 turns of unhindered combat with Excalibur chain-10 (220 dmg/turn) = 12,760 damage potential. Abaddon HP 5000 falls in 23 turns. Half the Phoenix-extended budget unused.

## Suggested re-tuning

Three options:

1. **Phoenix Rising restores a CAPPED amount** — `pl.hp = min(pl.max_hp, pl.hp + 200)`. Caps the heal at 200 HP regardless of cooking-HP stack. Preserves the "lifeline" feel for non-cookers without giving cookers a 1000+ HP buffer.
2. **Phoenix Rising scales with quirk progress** — restores a percentage based on the unlock progress: 10 survivals = 50% restore, 20 survivals = 75%, 30 survivals = full restore. Makes earning Phoenix's full power a longer commitment.
3. **Phoenix Rising can only trigger at HP < 25% max_hp** — adds a "near-death" gate that prevents pre-emptive use. Currently it can fire at full HP (wasteful but legal). The gate makes it explicitly an emergency tool.

Option 1 is simplest. Option 3 is most thematic.

## Notes

Cross-system: Power-quirks (Phoenix Rising) × food_system (cooking HP softcap) × Abaddon boss × Death-chase mechanics × cooking HP softcap calculation.

This pairs with `balance-cooking-hp-economy-dominates` — the underlying root cause is the 1000 HP softcap on cooking. Fix cooking softcap and Phoenix Rising becomes naturally smaller. Fix Phoenix Rising alone leaves cooking-cap dominance.

For audit consistency: each Power-quirk that grants a percentage-of-max-HP or full-HP-restore needs cooking-cap interaction review. Life Drain (25% of max_hp) at 1030 HP = 257 HP per use; at non-cooker 44 HP = 11 HP per use. The disparity is 23x.
