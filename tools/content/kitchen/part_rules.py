"""Can a run cook it? The part-frequency rules of the recipe book.

The kitchen rebuild, slice K1b (COOKING_REBUILD_PLAN_2026_11_14). Brandon's aim:
big payoff meals that a kid earns by hunting and by saving parts, never meals
that need luck. ``part_freq.json`` holds the simulator's measure of how often
each harvestable part turns up in a mastery run (``part_freq.py`` makes it).
From it:

* a part is COMMON when it turns up in at least ``common_share`` of runs, or it
  is common food (``data/items/food.json``, not rare) or a foraged find;
* rule 1, a legendary feast: every part but its gate (the first ingredient: the
  trophy, or the boss part a trophy-less feast is keyed to) is common, or an
  EARLY part (first found by floor ``early_floor``) that turns up in at least
  ``early_share`` of runs. The gate is the hunt; the rest is effort, not luck;
* rule 2, an ordinary multi-dish: at most ONE part is not common, so finding a
  rare part means you can cook its dishes.

A food is rare (philosopher's tea, deep fungi, the void ration) when its
largest ``floor_spawn_weight`` is under ``rare_food_weight``; rare food counts
as an uncommon part. Used by ``build_kitchen.py`` (its check) and
``restructure.py``; ``tests/test_kitchen_part_freq.py`` pins the same rules
from the game data.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FREQ_PATH = os.path.join(HERE, 'part_freq.json')


def load_freq(path: str = FREQ_PATH) -> dict:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def rare_foods(food_json: dict, limit: float) -> set:
    """Foods whose best spawn weight on any floor is under `limit`."""
    out = set()
    for fid, rec in food_json.items():
        weights = (rec.get('floor_spawn_weight') or {}).values()
        if weights and max(weights) < limit:
            out.add(fid)
    return out


class PartRules:
    """`role_of(p)` is 'prime' / 'trophy' / 'dungeon' for an ingredient, or
    'food' for common food. Parts the frequency file does not list are a
    problem (a new monster part: regenerate the file)."""

    def __init__(self, freq: dict, role_of, rare_food: set):
        self.freq = freq
        self.rules = freq['rules']
        self.parts = freq['parts']
        self.role_of = role_of
        self.rare_food = set(rare_food)

    def known(self, p) -> bool:
        return self.role_of(p) in ('food', 'dungeon') or p in self.parts

    def share(self, p) -> float:
        """The share of runs a part turns up in (food and forage: always)."""
        role = self.role_of(p)
        if role in ('food', 'dungeon'):
            return 0.0 if p in self.rare_food else 1.0
        return float(self.parts.get(p, {}).get('share_of_runs', 0.0))

    def first_floor(self, p):
        return self.parts.get(p, {}).get('median_first_floor')

    def is_common(self, p) -> bool:
        role = self.role_of(p)
        if role in ('food', 'dungeon'):
            return p not in self.rare_food
        return self.share(p) >= self.rules['common_share']

    def is_early_saved(self, p) -> bool:
        """An early part a saving hero reliably banks for a feast."""
        if self.role_of(p) in ('food', 'dungeon'):
            return False
        ff = self.first_floor(p)
        return (ff is not None and ff <= self.rules['early_floor']
                and self.share(p) >= self.rules['early_share'])

    def feast_ok(self, p) -> bool:
        return self.is_common(p) or self.is_early_saved(p)

    def completable(self, parts) -> float:
        """The chance a run turns up every part (independent parts)."""
        x = 1.0
        for p in dict.fromkeys(parts):
            if self.role_of(p) in ('food', 'dungeon'):
                continue
            x *= self.share(p)
        return x

    def problems(self, dishes: dict) -> list:
        """`dishes`: id -> {'ingredients' or 'parts': [...], 'legendary': bool}."""
        out = []
        for did, d in dishes.items():
            parts = list(dict.fromkeys(d.get('ingredients') or d.get('parts')))
            if len(parts) < 2 or d.get('song'):
                continue        # a song's dish is two rare foods by design (songs.py)
            for p in parts:
                if not self.known(p):
                    out.append(f'{did}: {p} has no frequency in part_freq.json (regenerate it)')
            if d.get('legendary'):
                bad = [p for p in parts[1:] if not self.feast_ok(p)]
                if bad:
                    out.append(f'{did} (feast): {bad} turn up too rarely; only the gate '
                               f'{parts[0]} may be rare')
            else:
                rare = [p for p in parts if not self.is_common(p)]
                if len(rare) > 1:
                    out.append(f'{did}: {len(rare)} uncommon parts {rare}; a dish holds at most one')
        return out

    def summary(self, dishes: dict) -> dict:
        feasts = [d for d in dishes.values() if d.get('legendary')]
        multis = [d for d in dishes.values()
                  if len(set(d.get('ingredients') or d.get('parts'))) > 1]

        def parts(d):
            return list(dict.fromkeys(d.get('ingredients') or d.get('parts')))
        return {
            'feasts': len(feasts),
            'feasts_half': sum(1 for d in feasts if self.completable(parts(d)) >= 0.5),
            'feasts_half_given_gate': sum(1 for d in feasts if self.completable(parts(d)[1:]) >= 0.5),
            'multis': len(multis),
            'multis_half': sum(1 for d in multis if self.completable(parts(d)) >= 0.5),
            'multis_never': sum(1 for d in multis if self.completable(parts(d)) == 0),
        }
