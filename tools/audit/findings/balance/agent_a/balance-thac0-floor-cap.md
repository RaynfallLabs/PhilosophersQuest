---
id: balance-thac0-floor-cap
dimension: balance
severity: P2
title: Mini-boss thac0 hard-capped at -16 from F40 onward — DEX/AC investment plateaus for hit avoidance
status: open
systems: [monsters, accessories, armor, dex_scaling]
floors_affected: [40, 100]
evidence:
  - balance_curves_agent_a.json:boss_stats.minibosses (all L40+ minibosses have thac0=-16)
  - balance_curves_agent_a.json:boss_stats.abaddon.thac0 (-16)
  - balance_curves_agent_a.json:boss_stats.fenrir.thac0 (-16)
  - data/monsters.json (rangda L40 thac0=-3, BUT all higher minibosses at -16)
  - src/player.py:240-245 (`get_ac`: base 10 - DEX mod / 2 - armor + shield + status)
discovered: 2026-05-15
---

## What's out of balance

In AD&D-style THAC0 mechanics (To Hit Armor Class 0), a monster's thac0 is the d20 roll needed to hit AC 0. Lower is better for the monster. The player's AC reduces what the monster needs to roll. With thac0 -16, the monster needs `-16 - player_AC` on d20 to hit. For a typical player AC of -5 (mid-game), that's a roll of -11 on d20 — meaning the monster cannot fail; **it hits 100% of the time**.

From `boss_stats.minibosses`, every mini-boss from L42-L97 has thac0 -16. So does Fenrir (L80), Abaddon (L100), the seal demons (L83-L97), and Death (-20 per src/monster.py:1020).

This means: **DEX investment, AC armor, and shield AC are useless for hit-avoidance against any mini-boss or boss from F40 onward.** The only late-game defense is:

- Displacement / Reflecting / Invisible status effects (which work probabilistically)
- HP soaking (which feeds the cooking-HP-dominates problem, see balance-cooking-hp-economy-dominates)
- Resistance / damage_resistances (which cap damage but don't avoid hits)

For the **geography quiz** (armor/shield equipping), this also means: equipping armor/shields in the late game only mitigates damage via `damage_resistances` and `enchant_bonus`, never hit-rate. The implicit player understanding "AC matters" breaks down at F40.

Compare to early-game where thac0 sits at 16-18: a goblin (thac0 19) needs `19 - player_AC` to hit. With player AC 5 that's roll 14+ — 35% hit rate. AC investment matters.

## Curve evidence

- `boss_stats.minibosses` thac0 progression:
  - rangda L40: -3 (anomaly — much weaker thac0)
  - nemean_lion L45: -3
  - baba_yaga L50: -3
  - jormungandr_juvenile L55: -7
  - sets_jackal L58: -9
  - green_knight L63: -13
  - charybdis L68: -15
  - All from L70+: -16 (the floor)
- `boss_stats.abaddon.thac0`: -16
- Normal monster thac0 from monster intro table:
  - F30: thac0 ranges -10 to 0
  - F40: -16 to -3
  - F50+: largely -16
- The flatline at -16 begins around F35-F40 and persists through F100.

## Suggested re-tuning

Two options:

1. **Continue scaling thac0 downward**: from F40-F100, thac0 should drift -16 → -20 → -24 → -28 to keep AC scaling relevant. Player AC ceiling is roughly -25 with full late-game gear (10 base - 4 DEX mod - 9 from Panoply L70 - 4 from dragonscale - 6 from tower_shield_ajax - 4 from displacement and bless), so monster thac0 should keep pace.
2. **Lower the floor on hit calculations**: implement minimum 5% miss chance (natural 20 doesn't auto-hit in many d20 variants; you could do a natural 1 = auto-miss). At least make hit-avoidance NEVER 100%.

The first option preserves the THAC0 metaphor; the second is a band-aid.

## Notes

Cross-system: monster definitions (thac0 floor), player accessory effects (DEX rings, AC enchants), armor (ac_bonus + enchant_bonus), and the implicit defensive contract communicated by AC numbers in the UI. If the UI shows "AC -12" and the player thinks that matters at F80, they're being misled.

This is also entangled with the `balance-cooking-hp-economy-dominates` finding: when hit-avoidance is impossible, HP becomes the only defensive lever, which makes cooking-HP overpowered by default. Fixing thac0 scaling would re-balance the defensive economy across multiple slots.

The rangda L40 / nemean_lion L45 / baba_yaga L50 thac0=-3 entries are anomalies — they're notably less accurate than peers at the same floor. Could be intentional (e.g. nemean_lion has high HP/damage but low accuracy), or could be tuning oversights. Worth flagging separately if VOICE/CODE notices.
