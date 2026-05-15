---
id: balance-disintegrate-spell-dominant
dimension: balance
severity: P1
title: Disintegrate spell instakills ~90% of monsters through F45 — trivializes mid-late game
status: open
systems: [spells, monsters, magic, items_spellbook]
floors_affected: [30, 80]
evidence:
  - balance_curves_agent_a.json:spells_by_tier (Disintegrate T5, 18MP, 4d8 vs bosses)
  - balance_curves_agent_a.json:boss_stats.minibosses (Cacus L30 HP 550; The_Sphinx L35 HP 600; Rangda L40 HP 700)
  - balance_curves_agent_a.json:monsters_by_floor (most normal mobs F30-F55 have HP < 500)
  - src/game_magic.py:1498-1519 (disintegrate_spell handler)
  - src/game_magic.py:1499 (`is_boss = ... or target.max_hp > 500`)
  - src/game_magic.py:1501 (`kill_chance = 0.15 + chain * 0.15` — 0.30 at chain 1 ... 0.90 at chain 5)
discovered: 2026-05-15
---

## What's out of balance

The Disintegrate spell (T5 quiz, 18 MP) has an instant-kill mechanic: at chain 5 it has **90% kill chance** on any monster with `max_hp <= 500`. Looking at the deliverable `monsters_by_floor` and `minibosses`:

- All normal monsters introduced F30-F55 have avg HP between 85 and 360 — all in disintegrate range
- Mini-bosses Cacus (L30, HP 550 — just above threshold), but every F1-F30 mini-boss (Lamia 120, Arachne 100, Talos 300, Echidna 300, Erlking 350, Camazotz 500) is inside the disintegrate range
- The_Sphinx (L35, HP 600) — barely outside threshold
- Wendigo (L75, HP 1500) and later are safe

Once a player has a Disintegrate spellbook (data/items/spellbook.json has no Disintegrate spellbook explicitly — must be a learnable spell from somewhere else), every mid-game encounter becomes:

1. Cast Disintegrate at the dangerous monster.
2. 90% chance: dead.
3. 10% chance: still take 4d8 base damage scaled by chain.

At chain 5, 18 MP per cast. With INT 24 (achievable via accessories +5 + Brilliance) max_mp = 30+24 = 54, meaning 3 casts before rest. With the Arcane Surge power quirk (`balance_curves_agent_a.json:power_quirks`), MP is fully restored — so 5+ casts available before needing rest.

**This breaks the difficulty contract through F50 at minimum.** Players who reach T5 science quizzes can win every non-boss encounter through F50 with one button. Combat math (the core loop) becomes optional.

## Curve evidence

- `boss_stats.minibosses` rows showing HP ≤ 500: arachne (100), lamia (120), talos (300), echidna (300), erlking (350), camazotz (500), cacus (550 — just outside)
- Normal mob HP averages from deliverable `monsters_by_floor`:
  - F30 introductions avg 85 HP — all instakill-able
  - F40 introductions avg 263 HP — all instakill-able
  - F50 introductions avg 360 HP — all instakill-able
  - F70 introductions avg 552 HP — borderline (Wendigo 1500 safe, Titan/abyssal_behemoth borderline)
- `spells_by_tier`: Disintegrate desc: "Chain-scaling instant kill (30-90%). Bosses take 4d8 instead."
- Source: `src/game_magic.py:1499` — `is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500`. The OR-clause means anything with HP ≤ 500 is treated as non-boss regardless of `is_mini_boss` flag.

## Suggested re-tuning

Two changes recommended:

1. **Bump the instakill threshold OR respect the `is_mini_boss` flag**. Change line 1499 to `is_boss = getattr(target, 'is_boss', False) or getattr(target, 'is_mini_boss', False) or target.max_hp > 1000`. This protects all the L30-L45 mini-bosses (arachne, lamia, talos, echidna, erlking, camazotz, cacus, the_sphinx, rangda, nemean_lion) and most F40+ normal mobs.
2. **Add a per-floor cap or recharge cost** — disintegrate should be a once-per-floor or have a 50-turn cooldown to prevent chain-spam. T5 quizzes are appropriately gated, but the dominance comes from infinite repeatability once unlocked.

Alternative: make Disintegrate scale chain to damage (like Smite) rather than to kill chance, so it's a high-damage spell, not a save-or-die.

## Notes

Crosses 3 systems: spell mechanics (chain scaling), monster definitions (HP thresholds), and the magic system's MP recovery economy. This is the most dominant single mechanic in the game. The spellbook for Disintegrate is not in data/items/spellbook.json — it's a `LEARNABLE_SPELLS` entry only (src/spells.py:163-167) which may mean it's only available via specific code paths; verify with VOICE/CODE auditors. If the spell is only obtainable via rare drops/altars, severity might drop to P2, but the kill rate is so dominant it remains a P1 design hole.
