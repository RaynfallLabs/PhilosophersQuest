#!/usr/bin/env python
"""How heavy is what a hero carries? The measuring stick for the carry limit.

Three tables, all from the game's own code and data (item weights are never
changed here; they are deliberately realistic):

  1. START   every starting build (the plain hero and every secret build in
             welcome_screen.SECRET_BUILDS) through the real Game: worn + pack
             weight against the limit. Every build must start below Burdened.
  2. KITS    hand-built loadouts from the real templates and materials: the
             typical STR 10 kit, the same hero hoarding two spare suits and a
             rack of weapons, a STR 18-20 warrior in plate, a low-STR caster.
  3. DEPTH   what simulated players (tools/balance/difficulty_sim.py) actually
             wear, and their STR, floor by floor. The simulator picks armour
             by AC alone, so this is what a greedy player ends up wearing.

Usage
-----
    python tools/balance/carry_sim.py                      # current numbers
    python tools/balance/carry_sim.py --base 40 --per-str 6  # try a limit
    python tools/balance/carry_sim.py --depth-trials 0       # skip table 3

Standard library + the game's own modules. Never writes inside the repo.
"""
from __future__ import annotations

import argparse
import copy
import os
import random
import statistics as st
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SRC = os.path.join(_REPO, 'src')
for _p in (_SRC, os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import items as items_mod                        # noqa: E402
from player import Player                        # noqa: E402

# ---------------------------------------------------------------------------
# Supplies: what a hero carries besides gear. Counted from the item data
# (median weights: potion 0.4, scroll 0.1, wand 0.3, spellbook 0.3, ration
# 0.4-1.5, ingredient 0.25, ring 0.2).
# ---------------------------------------------------------------------------
SUPPLIES = (
    ('potion', 'potion_of_healing', 6),
    ('scroll', None, 5),
    ('wand', None, 2),
    ('spellbook', None, 1),
    ('food', 'bread_ration', 2),
    ('food', 'trail_rations', 1),
    ('ingredient', None, 12),
    ('accessory', None, 2),           # two rings worn
    ('lockpick', 'master_lockpick', 1),
)


def _first(cls, item_id=None):
    for it in items_mod.load_items(cls):
        if item_id is None or it.id == item_id:
            return copy.copy(it)
    raise LookupError(f"{cls}:{item_id}")


def supplies_weight() -> float:
    total = 0.0
    for cls, iid, n in SUPPLIES:
        if iid is None:
            ws = [float(getattr(i, 'weight', 0) or 0) for i in items_mod.load_items(cls)]
            w = st.median(ws)
        else:
            w = float(_first(cls, iid).weight)
        total += w * n
    return total + 0.1                            # the Philosopher's Shard


def arm(tpl, mat):
    return items_mod.instantiate_armor(tpl, mat)


def shield(tpl, mat):
    return items_mod.instantiate_shield(tpl, mat)


def weapon(tpl, mat):
    return items_mod.instantiate_weapon(tpl, mat)


def kits() -> list:
    """(name, STR, worn items, pack items, pack-extra pounds)."""
    sup = supplies_weight()
    # A mid-game set of ordinary metal (weight_mult 1.0: ring iron, chain steel,
    # tempered bronze): median body armour (20 lb), helm, boots, gloves, cloak.
    mid = [arm('chain_shirt', 'chain_steel'), arm('iron_helm', 'chain_steel'),
           arm('iron_boots', 'chain_steel'), arm('gauntlets', 'chain_steel'),
           arm('cloak', 'linen'), shield('kite_shield', 'chain_steel'),
           weapon('longsword', 'steel')]
    early = [arm('leather', 'leather'), arm('leather_cap', 'leather'),
             arm('leather_boots', 'leather'), shield('light_wooden', 'oak'),
             weapon('shortsword', 'iron')]
    plate = [arm('full_plate', 'chain_steel'), arm('great_helm', 'chain_steel'),
             arm('plate_vambraces', 'chain_steel'), arm('plate_gauntlets', 'chain_steel'),
             arm('plate_greaves', 'chain_steel'), arm('plate_boots', 'chain_steel'),
             arm('cloak', 'linen'), arm('padded_shirt', 'linen'),
             weapon('battleaxe', 'steel')]
    caster = [arm('padded', 'silk'), arm('cloak', 'silk'),
              weapon('quarterstaff', 'oak')]
    spares = [arm('chain_shirt', 'chain_steel'), arm('scale', 'chain_steel')]
    rack = [weapon(t, 'steel') for t in ('battleaxe', 'mace', 'greatsword', 'warhammer')]
    return [
        ("Floor 1-5 hero, leather + shield", 10, early, [weapon('dagger', 'iron')], sup),
        ("STR 10, typical mid kit", 10, mid, [weapon('shortbow', 'yew')], sup),
        ("STR 10, mid kit + 1 spare suit", 10, mid, [arm('chain_shirt', 'chain_steel')], sup),
        ("STR 10, mid kit + 2 suits + 4 weapons", 10, mid, spares + rack, sup),
        ("STR 10, full plate + kite", 10, plate + [shield('kite_shield', 'chain_steel')], [], sup),
        ("STR 14, full plate + kite", 14, plate + [shield('kite_shield', 'chain_steel')], [], sup),
        ("STR 18, full plate + kite", 18, plate + [shield('kite_shield', 'chain_steel')], [], sup),
        ("STR 20, full plate + tower", 20, plate + [shield('tower_shield', 'chain_steel')], [], sup),
        ("STR 20, plate + tower + 2 suits", 20, plate + [shield('tower_shield', 'chain_steel')], spares, sup),
        ("STR 6 caster, robe + staff", 6, caster, [], sup),
    ]


def kit_rows(base, per) -> list:
    rows = []
    for name, s, worn, pack, extra in kits():
        p = Player()
        p.STR = s
        for it in worn:
            p._apply_equip(it)
        p.inventory.extend(pack)
        total = p.get_current_weight() + extra
        lim = base + per * s
        rows.append((name, s, p.get_worn_weight(), p.get_pack_weight() + extra, total, lim))
    return rows


# ---------------------------------------------------------------------------
# 1. Starting builds through the real Game
# ---------------------------------------------------------------------------
def start_rows(base, per) -> list:
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((1, 1))
    import welcome_screen
    from main import Game
    builds = [('(plain hero)', None)] + sorted(welcome_screen.SECRET_BUILDS.items())
    rows = []
    for key, b in builds:
        random.seed(1)
        g = Game(screen, player_name=key if b else 'Adventurer', secret_build=b)
        p = g.player
        lim = base + per * p.STR
        rows.append((key, p.STR, p.get_worn_weight(), p.get_pack_weight(),
                     p.get_current_weight(), lim))
    return rows


# ---------------------------------------------------------------------------
# 3. What simulated players wear at depth
# ---------------------------------------------------------------------------
def depth_rows(trials, floors, profiles) -> dict:
    import difficulty_sim as ds
    out = {}
    marks = set(floors)
    for prof in profiles:
        rec = {f: [] for f in floors}
        orig = ds.Run.play_floor

        def play(self, floor, fights=True, _orig=orig, _rec=rec):
            r = _orig(self, floor, fights)
            if floor in marks:
                p = self.p
                _rec[floor].append((p.STR, p.get_worn_weight()))
            return r
        ds.Run.play_floor = play
        try:
            random.seed(7)
            cache = ds.FloorCache(6)
            knobs = ds.parse_knobs(None)
            for _ in range(trials):
                run = ds.Run(cache, prof, 0.95, 1.0, 'greedy', 1, knobs)
                for f in range(1, max(floors) + 1):
                    run.play_floor(f, fights=True)
                    if run.p.hp <= 0:
                        break
        finally:
            ds.Run.play_floor = orig
        out[prof] = rec
    return out


def pct(total, lim):
    return 100.0 * total / max(1, lim)


def mark(total, lim, share=Player.BURDENED_SHARE):
    if total > lim:
        return 'OVER'
    if total > lim * share:
        return 'Burdened'
    return 'ok'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--base', type=float, default=Player.CARRY_BASE)
    ap.add_argument('--per-str', type=float, default=Player.CARRY_PER_STR)
    ap.add_argument('--depth-trials', type=int, default=8)
    ap.add_argument('--no-start', action='store_true')
    a = ap.parse_args(argv)
    base, per = a.base, a.per_str
    print(f"Limit = {base:g} + {per:g} x STR   (STR 10 -> {base + 10 * per:g}); "
          f"Burdened above {Player.BURDENED_SHARE:.0%}\n")

    if not a.no_start:
        print("1. STARTING BUILDS (worn + pack, real Game)")
        print(f"   {'build':32s} {'STR':>3s} {'worn':>6s} {'pack':>6s} {'total':>6s} {'limit':>6s} {'%':>5s}")
        for key, s, w, pk, t, lim in start_rows(base, per):
            print(f"   {key[:32]:32s} {s:3d} {w:6.1f} {pk:6.1f} {t:6.1f} {lim:6.0f} "
                  f"{pct(t, lim):5.0f}  {mark(t, lim)}")
        print()

    print(f"2. KITS (supplies {supplies_weight():.1f} lb each: 6 potions, 5 scrolls, 2 wands,"
          " a book, 3 rations, 12 ingredients, 2 rings, lockpick)")
    print(f"   {'kit':40s} {'STR':>3s} {'worn':>6s} {'pack':>6s} {'total':>6s} {'limit':>6s} {'%':>5s}")
    for name, s, w, pk, t, lim in kit_rows(base, per):
        print(f"   {name:40s} {s:3d} {w:6.1f} {pk:6.1f} {t:6.1f} {lim:6.0f} "
              f"{pct(t, lim):5.0f}  {mark(t, lim)}")
    print()

    if a.depth_trials > 0:
        floors = (3, 6, 10, 15, 20, 30, 40, 60, 80)
        print(f"3. WHAT SIMULATED PLAYERS WEAR ({a.depth_trials} runs each, 95% accuracy;"
              " armour chosen by AC alone)")
        res = depth_rows(a.depth_trials, floors, ('casual', 'prepared', 'committed'))
        for prof, rec in res.items():
            print(f"   {prof}")
            for f in floors:
                rows = rec[f]
                if not rows:
                    continue
                strs = [r[0] for r in rows]
                worn = [r[1] for r in rows]
                s_med = st.median(strs)
                w_med = st.median(worn)
                w_hi = max(worn)
                lim = base + per * s_med
                print(f"     floor {f:3d}: n={len(rows):2d}  STR {s_med:5.1f}  worn med {w_med:5.1f}"
                      f"  max {w_hi:5.1f}  +supplies {w_med + supplies_weight():5.1f}"
                      f" / {lim:5.0f} = {pct(w_med + supplies_weight(), lim):4.0f}%")
    return 0


if __name__ == '__main__':
    sys.exit(main())
