"""Cooking-overhaul migration (2026-06-07).

Rewrites every recipe's `ingredients` array to the richer, monster-COMBINATION
costs approved in proposals/design/cooking_recipes_overhaul.md (with refinements):

    family   (12)  : 2 family + 4 assorted              (was 1 + 3)
    prime    (514) : 1 prime + 2 family + 4 assorted     (was 1 + 1 + 2)
    trophy   (13)  : 1 trophy + 2 family + 5 assorted     (was 1 + 1 + 3)
    master   (51)  : 2 CO-SPAWNING primes + 2 family + 3 assorted
    dungeon  (29)  : 1 special + 1 prime + 2 family + 3 assorted
    basic    (1)   : DELETED  (assorted parts are now eaten as jerky)

Clustering (master recipes): the two primes a master needs must come from
monsters whose spawn bells OVERLAP on some floor, so the player can collect both
on one stretch of floors. For each master we (a) keep the best-overlapping pair
of its OWN named primes when such a pair exists, else (b) keep one named prime
and repick the partner from the highest-overlap monster in the SAME family. The
2 family slots are derived from the kept primes' families.

tier_outcomes, name, description, temp_power, stat_grant, etc. are left
BYTE-FOR-BYTE intact -- only the `ingredients` list (and the deletion of the
basic stew) changes.

Round-trip guarded: detects the file's ensure_ascii style and writes it back the
same way. Idempotent: re-running on an already-migrated file is a no-op.

Run:  python data/items/_migrate_recipe_costs.py
      python data/items/_migrate_recipe_costs.py --check   (report only, no write)
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent                      # data/
RECIPE_PATH  = HERE / 'recipes.json'
MONSTER_PATH = DATA / 'monsters.json'
PRIME_PATH   = HERE / 'prime_cuts.json'
ING_PATH     = HERE / 'ingredient.json'

ASSORTED = 'assorted_monster_parts'

# Target composition (counts of assorted/family added; primes/trophy/special kept).
N_ASSORTED = {'family': 4, 'prime': 4, 'trophy': 5, 'master_prime': 3, 'dungeon_keyed': 3}
N_FAMILY   = {'family': 2, 'prime': 2, 'trophy': 2, 'master_prime': 2, 'dungeon_keyed': 2}


# ----------------------------------------------------------------------
# load + helpers
# ----------------------------------------------------------------------
def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def _detect_ensure_ascii(path: Path) -> bool:
    """True if the file was written with ensure_ascii=True (has \\uXXXX escapes
    and no raw non-ASCII bytes). Mirrors how the file is stored so a round-trip
    doesn't flip the encoding of every accented dish name."""
    raw = path.read_text(encoding='utf-8')
    backslash_u = chr(92) + 'u'
    has_escapes = backslash_u in raw
    has_raw_nonascii = any(ord(c) > 127 for c in raw)
    if has_escapes and not has_raw_nonascii:
        return True
    if has_raw_nonascii and not has_escapes:
        return False
    # Mixed / ambiguous: default to True (the recipes.json convention).
    return True


def _classify(ing: str) -> str:
    if ing == ASSORTED:
        return 'assorted'
    if ing.startswith('family_'):
        return 'family'
    if ing.endswith('_trophy'):
        return 'trophy'
    if ing.endswith('_prime'):
        return 'prime'
    return 'special'


def _bell(mdefs: dict, mid: str, L: int) -> float:
    d = mdefs.get(mid, {})
    if d.get('min_level', 1) > L:
        return 0.0
    pf = d.get('peak_floor', d.get('min_level', 1))
    sp = max(1, d.get('spread', 10))
    return math.exp(-((L - pf) ** 2) / (2 * sp * sp))


def _present(mdefs: dict, mid: str, thresh: float = 0.05) -> set[int]:
    """Floors (1..100) where the monster has a non-negligible spawn weight."""
    return {L for L in range(1, 101) if _bell(mdefs, mid, L) >= thresh}


# ----------------------------------------------------------------------
# master-recipe clustering
# ----------------------------------------------------------------------
def _pair_for_master(rid: str, primes_named: list[str], mdefs: dict,
                     primes_meta: dict, report: list[str]) -> tuple[list[str], list[str]]:
    """Return (two prime-ingredient ids, two family ids) for a master recipe.

    primes_named: monster_ids of the recipe's CURRENT named primes (order = recipe order).
    Strategy:
      1) best-overlapping 2-combo of the recipe's OWN named primes, else
      2) keep the first named prime (recipe signature) + repick partner from the
         highest-overlap monster in that prime's family.
    """
    fam_of = {m: primes_meta[m]['family'] for m in primes_meta}
    present = {m: _present(mdefs, m) for m in primes_named}

    # (1) try own primes
    best = None
    for i in range(len(primes_named)):
        for j in range(i + 1, len(primes_named)):
            a, b = primes_named[i], primes_named[j]
            ov = present[a] & present[b]
            if ov and (best is None or len(ov) > best[0]):
                best = (len(ov), a, b)
    if best is not None:
        a, b = best[1], best[2]
        # keep recipe order
        keep = [m for m in primes_named if m in (a, b)]
        fams = [f'family_{fam_of[keep[0]]}', f'family_{fam_of[keep[1]]}']
        return [f'{m}_prime' for m in keep], fams

    # (2) repick: keep the prime whose family matches a required family if possible,
    # else the first named prime; partner = best same-family co-spawner.
    keep = primes_named[0]
    keep_present = _present(mdefs, keep)
    keep_fam = primes_meta[keep]['family']
    partner = None
    best_ov = 0
    for m, meta in primes_meta.items():
        if m == keep or meta['is_trophy'] or meta['family'] != keep_fam:
            continue
        ov = len(keep_present & _present(mdefs, m))
        if ov > best_ov:
            best_ov, partner = ov, m
    if partner is None:
        # Should not happen for these data; degrade to keeping a single prime twice
        # would be wrong (two distinct copies needed). Fall back to first two named.
        report.append(f"  WARN {rid}: no same-family co-spawner for {keep}; "
                      f"kept original first two named primes (may not co-spawn).")
        keep2 = primes_named[:2]
        fams = [f'family_{fam_of[m]}' for m in keep2]
        return [f'{m}_prime' for m in keep2], fams
    report.append(f"  REPICK {rid}: {keep}_prime + {partner}_prime "
                  f"(co-spawn {min(keep_present & _present(mdefs, partner))}"
                  f"-{max(keep_present & _present(mdefs, partner))})")
    fams = [f'family_{keep_fam}', f'family_{primes_meta[partner]['family']}']
    return [f'{keep}_prime', f'{partner}_prime'], fams


# ----------------------------------------------------------------------
# core rewrite
# ----------------------------------------------------------------------
def build_new_ingredients(recipes: dict, mdefs: dict, primes_meta: dict,
                          report: list[str]) -> dict[str, list[str]]:
    """Compute the new ingredients list for every (kept) recipe id."""
    new: dict[str, list[str]] = {}
    for rid, r in recipes.items():
        cls = r.get('recipe_class', '')
        if cls == 'basic':
            continue  # deleted
        ings = r.get('ingredients', [])
        roles = Counter(_classify(i) for i in ings)

        if cls == 'family':
            fam = next(i for i in ings if _classify(i) == 'family')
            new[rid] = [fam, fam] + [ASSORTED] * N_ASSORTED['family']

        elif cls == 'prime':
            prime = next(i for i in ings if _classify(i) == 'prime')
            # auto-cluster: family of THIS monster (co-spawns with itself by def)
            mon = prime[:-len('_prime')]
            fam = f"family_{primes_meta[mon]['family']}"
            new[rid] = [prime, fam, fam] + [ASSORTED] * N_ASSORTED['prime']

        elif cls == 'trophy':
            trophy = next(i for i in ings if _classify(i) == 'trophy')
            # existing family in the recipe (themed); fall back to monster's family
            fam = next((i for i in ings if _classify(i) == 'family'), None)
            if fam is None:
                mon = trophy[:-len('_trophy')]
                fam = f"family_{primes_meta.get(mon, {}).get('family', 'beast')}"
            new[rid] = [trophy, fam, fam] + [ASSORTED] * N_ASSORTED['trophy']

        elif cls == 'dungeon_keyed':
            special = next(i for i in ings if _classify(i) == 'special')
            prime = next(i for i in ings if _classify(i) == 'prime')
            fam = next((i for i in ings if _classify(i) == 'family'), None)
            if fam is None:
                mon = prime[:-len('_prime')]
                fam = f"family_{primes_meta[mon]['family']}"
            new[rid] = [special, prime, fam, fam] + [ASSORTED] * N_ASSORTED['dungeon_keyed']

        elif cls == 'master_prime':
            named = [i[:-len('_prime')] for i in ings if _classify(i) == 'prime']
            primes2, fams2 = _pair_for_master(rid, named, mdefs, primes_meta, report)
            # Special: archon recipe required family_celestial + family_demon and
            # had NO assorted. Preserve its DISTINCT family identity rather than
            # collapsing to the kept primes' families.
            orig_fams = [i for i in ings if _classify(i) == 'family']
            if len(set(orig_fams)) == 2 and roles['assorted'] == 0:
                fams2 = orig_fams
            new[rid] = primes2 + fams2 + [ASSORTED] * N_ASSORTED['master_prime']

        else:
            report.append(f"  WARN {rid}: unknown recipe_class {cls!r}; left unchanged.")
            new[rid] = list(ings)
    return new


def already_migrated(recipes: dict) -> bool:
    """Idempotency check: basic stew gone AND a sample prime has the new shape."""
    if 'basic_monster_stew' in recipes:
        return False
    for rid, r in recipes.items():
        if r.get('recipe_class') == 'prime':
            roles = Counter(_classify(i) for i in r.get('ingredients', []))
            return roles['assorted'] == 4 and roles['family'] == 2 and roles['prime'] == 1
    return False


def main(check_only: bool = False) -> int:
    recipes = _load(RECIPE_PATH)
    mdefs = _load(MONSTER_PATH)
    primes_meta = _load(PRIME_PATH).get('primes', {})
    ingredients = _load(ING_PATH)

    report: list[str] = []

    if already_migrated(recipes):
        print('Recipes already migrated (basic stew gone, prime shape = new). No-op.')
        return 0

    new_ings = build_new_ingredients(recipes, mdefs, primes_meta, report)

    # Validate: every referenced ingredient must exist.
    bad = {}
    for rid, ings in new_ings.items():
        for i in ings:
            if i not in ingredients:
                bad.setdefault(rid, []).append(i)
    if bad:
        print('ABORT: new recipes reference non-existent ingredients:')
        for rid, miss in bad.items():
            print(f'  {rid}: {miss}')
        return 1

    # Floor-clustering verification: every non-assorted, non-special monster part
    # in a recipe must share a common floor band with the others.
    cluster_fail = _verify_clusters(new_ings, mdefs, primes_meta)

    # Build the output dict: drop basic stew, replace ingredients, keep all else.
    out = {}
    for rid, r in recipes.items():
        if rid == 'basic_monster_stew':
            continue
        nr = dict(r)  # shallow copy preserves key order + tier_outcomes verbatim
        nr['ingredients'] = new_ings[rid]
        out[rid] = nr

    # Summary
    print('=== Recipe migration summary ===')
    cls_counts = Counter(r.get('recipe_class') for r in out.values())
    for c, n in sorted(cls_counts.items()):
        print(f'  {c}: {n}')
    print('  (basic_monster_stew deleted)')
    if report:
        print('--- master clustering notes ---')
        for line in report:
            print(line)
    if cluster_fail:
        print('--- CLUSTERING FAILURES (primes do NOT share a floor band) ---')
        for line in cluster_fail:
            print('  ' + line)
    else:
        print('--- clustering: every recipe\'s monster parts share a floor band. OK ---')

    if check_only:
        print('\n(--check: no file written)')
        return 0

    ensure_ascii = _detect_ensure_ascii(RECIPE_PATH)
    RECIPE_PATH.write_text(
        json.dumps(out, indent=2, ensure_ascii=ensure_ascii) + '\n',
        encoding='utf-8')
    print(f'\nWrote {len(out)} recipes to {RECIPE_PATH} (ensure_ascii={ensure_ascii}).')
    return 0


def _verify_clusters(new_ings: dict, mdefs: dict, primes_meta: dict) -> list[str]:
    """Return human-readable failures where a recipe's monster-derived parts
    (primes/trophies) share NO common floor band. Family/assorted/special are
    floor-agnostic (families stack across the whole family; special is foraged)."""
    fails = []
    for rid, ings in new_ings.items():
        mons = []
        for i in ings:
            cl = _classify(i)
            if cl == 'prime':
                mons.append(i[:-len('_prime')])
            elif cl == 'trophy':
                mons.append(i[:-len('_trophy')])
        if len(mons) < 2:
            continue
        bands = [_present(mdefs, m) for m in mons]
        common = set.intersection(*bands) if bands else set()
        if not common:
            ranges = {m: (min(_present(mdefs, m)) if _present(mdefs, m) else None,
                          max(_present(mdefs, m)) if _present(mdefs, m) else None)
                      for m in mons}
            fails.append(f'{rid}: {ranges}')
    return fails


if __name__ == '__main__':
    sys.exit(main(check_only='--check' in sys.argv))
