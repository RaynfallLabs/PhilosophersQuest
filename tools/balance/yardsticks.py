"""
The yardsticks every system is sized against, measured from the live game.

Offline tooling (not loaded at runtime).

    python tools/balance/yardsticks.py            # print the tables
    python tools/balance/yardsticks.py --times    # also print recorded answer times

`floor_curve.py` holds the two tables the GAME reads (ONE_ATTACK and
HEALTH_BAR). This tool recomputes them from the material tables, the clock
rule and the answer model, so they can be refreshed after a balance change;
tests/test_yardsticks.py fails if the stored tables drift from what this
computes.

One attack = what a weapon typical of the floor does in a single chain at
that floor's clock, for the child the game is balanced for (95% right on
tier-1 sums, 90% on tier 2, 85% below). Seconds per answer are the recorded
figures when enough real answers exist (answer_times.json, written by the
game), else the working guesses below.
"""
from __future__ import annotations

import math
import os
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Working guesses for seconds per math answer by tier. Tier 1 is confirmed by
# the owner's own play (6 to 7 answers in 11 seconds). The rest are guesses.
GUESS_SECONDS = {1: 1.8, 2: 2.6, 3: 4.5, 4: 6.0, 5: 7.0}
KID_ACC = {1: 0.95, 2: 0.90, 3: 0.85, 4: 0.85, 5: 0.85}
MIN_SAMPLES = 40          # real answers needed before a tier's guess is replaced
FLOORS = (1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)


def math_seconds() -> tuple[dict, dict]:
    """(seconds per answer by tier, how many real answers back each)."""
    from quiz_engine import load_answer_times
    rec = load_answer_times()
    out, n = dict(GUESS_SECONDS), {t: 0 for t in GUESS_SECONDS}
    for tier in GUESS_SECONDS:
        row = rec.get(f"math|{tier}")
        if row and row.get("right", 0) >= MIN_SAMPLES:
            out[tier] = row["seconds_right"] / row["right"]
            n[tier] = int(row["right"])
    return out, n


def clock(floor: int) -> int:
    """The combat clock a player has on `floor` with no build: Wisdom."""
    from player import Player
    return 10 + int(floor) // Player.DEPTH_WIS_EVERY


def chain_multiplier(tier: int, seconds: float, sec_per_answer: float,
                     trials: int = 4000, rng: random.Random | None = None) -> tuple[float, float]:
    """(mean of chain^1.15, mean chain) for one attack."""
    rng = rng or random.Random(tier * 1000 + int(seconds))
    acc = KID_ACC[tier]
    tot = chains = 0.0
    for _ in range(trials):
        t, c = 0.0, 0
        while True:
            dt = rng.lognormvariate(math.log(sec_per_answer), 0.3)
            if t + dt > seconds:
                break
            t += dt
            if rng.random() < acc:
                c += 1
            else:
                break
        tot += c ** 1.15
        chains += c
    return tot / trials, chains / trials


def one_attack_table(samples: int = 400) -> dict:
    """{floor: (damage of one attack, mean chain, typical weapon base)}."""
    from items import pick_random_weapon_for_floor
    secs, _ = math_seconds()
    out = {}
    for floor in FLOORS:
        rng = random.Random(floor)
        dmg, chain, base = [], [], []
        for _ in range(samples):
            w = pick_random_weapon_for_floor(floor, rng)
            if w is None or getattr(w, "requires_ammo", None):
                continue
            m, c = chain_multiplier(w.quiz_tier, clock(floor), secs[w.quiz_tier], trials=300, rng=rng)
            dmg.append(w.base_damage * m)
            chain.append(c)
            base.append(w.base_damage)
        out[floor] = (statistics.median(dmg), statistics.mean(chain), statistics.median(base))
    return out


def main() -> int:
    import floor_curve
    secs, n = math_seconds()
    print("seconds per math answer by tier:",
          {t: (round(s, 2), "recorded" if n[t] else "guess") for t, s in secs.items()})
    table = one_attack_table()
    print("\nfloor  clock  weapon base  mean chain  ONE ATTACK   one monster  attacks to kill   stored")
    for floor, (dmg, chain, base) in table.items():
        hp = floor_curve.target_hp(floor)
        print(f"{floor:5} {clock(floor):6} {base:12.0f} {chain:11.1f} {dmg:11.0f} {hp:13.0f} "
              f"{hp / max(1, dmg):16.1f} {floor_curve.one_attack(floor):8.0f}")
    print("\nONE_ATTACK =", {f: int(round(v[0])) for f, v in table.items()})
    print("HEALTH_BAR =", floor_curve.HEALTH_BAR, "(from the simulator's steady cook)")
    if "--times" in sys.argv:
        from quiz_engine import load_answer_times
        rec = load_answer_times()
        if not rec:
            print("\nNo answer times recorded yet. Play the game; they are saved "
                  "beside quiz_history.json as answer_times.json.")
        else:
            print("\nsubject|tier        answers  right%  sec/answer  sec/right answer")
            for key in sorted(rec):
                r = rec[key]
                if r["n"]:
                    print(f"{key:18} {r['n']:8} {100 * r['right'] / r['n']:6.0f} "
                          f"{r['seconds'] / r['n']:10.2f} "
                          f"{(r['seconds_right'] / r['right']) if r['right'] else 0:12.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
