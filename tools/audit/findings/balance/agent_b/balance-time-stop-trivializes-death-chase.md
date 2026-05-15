---
id: balance-time-stop-trivializes-death-chase
dimension: balance
severity: P1
title: Time-stop sources (scroll/wand/spell/quirk-power) trivialize the Death chase
status: open
systems: [death_chase, scrolls, wands, spells, quirks, escape_phase]
floors_affected: [1, 100]
evidence:
  - balance_curves_agent_b.json:death_chase_difficulty.time_stop_sources
  - src/game_combat.py:1351-1354 (time_stopped blocks ALL monster turns, including Death)
  - data/items/scroll.json:scroll_of_time_stop (min_level 40)
  - data/items/wand.json:wand_of_time_stop (min_level 60, charges_min/max not zero)
  - src/spells.py:104-108 (time_freeze_spell, T5, mp 20)
  - src/quirk_system.py:1183 + 1562 (time_dilation quirk power → time_stop 10 turns)
  - src/main.py:1421-1447 (flux_capacitor — special drop, 10-turn time_stop)
discovered: 2026-05-15
---

## What's out of balance

`game_combat.py:1351-1354` short-circuits the entire monster phase if the player has `time_stopped`:
```python
def _do_monster_turns(self):
    if self.player.has_effect('time_stopped'):
        return
```
That `return` runs BEFORE the Death-pursuit branch at line 1357. Result: **time_stopped freezes Death the same as any other monster**. The Death chase mechanic — escalating speed, prayer-freeze as desperate measure, the *terror* of the pursuit — is bypassed by any of these:

| Source | Min floor | Duration |
|---|---|---|
| `scroll_of_time_stop` | L40 | 10 turns |
| `wand_of_time_stop` | L60 | 10 turns/zap (multi-charge) |
| `time_freeze_spell` | T5 spellbook | 5 turns |
| `time_dilation` quirk power | unlocked at 25 correct in a row | 10 turns, x1 use |
| `flux_capacitor` (rare drop) | special | 10 turns |
| `chronal pebble` from mystery (search code) | — | also adds turns |

A single wand of time_stop with 5-7 charges (typical roll, see balance_curves_agent_b.json :: wands_by_min_level) is **50-70 free turns of immunity** to Death — enough to climb several floors during the climax phases (75% / 100% / 125%) without ever being touched. Prayer is supposed to be the desperate one-shot trick (~4-8 freeze turns with a 100-turn cooldown). Time-stop is the casual every-floor trick.

The Death chase carries the entire emotional weight of Act III. It's the *point* of climbing 100 floors only to climb back. If the player carries a stocked wand, the chase is administrative.

## Curve evidence

`balance_curves_agent_b.json :: death_chase_difficulty` documents the speed escalation and prayer-freeze formula. `time_stopped_blocks_death: true` is the trigger row. The prayer-freeze gives 4-8 turns *once per 100-280 turn cooldown* — that's the intended ceiling. A 7-charge wand multiplies the protection budget by ~9x with no cooldown.

Compare across acts:
- Act II (Abaddon): the holy-fire altars and Sword path break Act II (see `balance-abaddon-trivialised-by-sword-of-michael.md`).
- Act III (Death chase): time-stop sources break Act III.
- Act IV (secret victory): the abyssal shimmer is a fixed-location ritual, not a stat fight — but the player must SURVIVE the chase to reach it, and time-stop guarantees that survival.

So the curve evidence is: every endgame fail-state has a get-out-of-jail consumable in the deliverable.

## Suggested re-tuning

1. **Death immune to time_stop.** Mirror the pattern Death already has for take_damage (`monster.py:1036-1037` returns 0) and add_effect (`monster.py:1046-1047` is a no-op). Add a special-case in `_do_monster_turns` so the time_stopped check runs *after* Death takes her turn, or check `if monster is self.death_monster` to bypass the freeze.
2. Alternatively: keep time_stop effective vs Death but **drastically reduce duration** when the chase is active (3 turns max instead of 10) — call it "Death's gaze pierces the frozen instant."
3. Reduce wand_of_time_stop charges to charges_min=1, charges_max=2 so a single wand cannot carry the whole ascent.

The Death chase finding should land as P1 because the chase is the entire third-act emotional payoff. If the dad-and-kid reward economy is built on the chronicle quote *"Death itself. I need to run"* — and the player is in fact strolling — the contract collapses.

## Notes

- The same finding could be made narrower (just the wand) but the cluster matters: scroll, wand, spell, quirk, and rare drop *all* freeze Death. Closing one channel without the others doesn't fix it.
- The `time_dilation` quirk power is a one-shot per-run; less severe.
- Cross-system reach: this finding touches scrolls (grammar quiz to read), wands (science quiz to identify), spells (grammar quiz to learn + science to cast), quirks (passive), and the chase mechanic itself.
