"""Fix loot over-representation of multi-variant accessories (2026-06-07).

User: "I have found, like THREE wands of Detect Monster and 4 different Rings and
Amulets of Searching. Seems overweighted." Root cause: a functional accessory
(e.g. 'ring of searching') exists as N cosmetic appearance-variants
(ring_searching_silver, _malachite, _ivory, ...) and EACH variant carried the
full floorSpawnWeight. So a 7-variant ring spawned ~7x as often as a 1-variant
ring. "ring of warning" was 8x80=640; searching 7x80=560; telepathy 6x80=480.

Fix: scale each variant's floorSpawnWeight by 1/(variant count of its name), so
every FUNCTIONAL accessory type spawns at a single item's intended rate
regardless of how many cosmetic looks it has. Per-floor-band structure preserved.
Uniques (low weights, distinct names) are untouched. Round-trip guarded.
"""
import collections
import json
from pathlib import Path

PATH = Path(__file__).resolve().parent / 'accessory.json'


def main():
    orig = PATH.read_text(encoding='utf-8')
    acc = json.loads(orig)
    trailing = orig[len(orig.rstrip('\n')):]
    fmt = next((f for f in (False, True)
                if json.dumps(acc, indent=2, ensure_ascii=f) == orig.rstrip('\n')), None)
    assert fmt is not None, 'cannot round-trip accessory.json'

    # group ids by display name, counting only multi-variant COMMON groups
    by_name = collections.defaultdict(list)
    for iid, d in acc.items():
        by_name[d.get('name', iid)].append(iid)

    changed = []
    for name, ids in by_name.items():
        n = len(ids)
        if n < 2:
            continue
        for iid in ids:
            fsw = acc[iid].get('floorSpawnWeight') or acc[iid].get('floor_spawn_weight')
            if not isinstance(fsw, dict) or not fsw:
                continue
            key = 'floorSpawnWeight' if 'floorSpawnWeight' in acc[iid] else 'floor_spawn_weight'
            new = {band: max(1, round(w / n)) for band, w in fsw.items()}
            if new != fsw:
                acc[iid][key] = new
                changed.append((iid, name, n))

    PATH.write_text(json.dumps(acc, indent=2, ensure_ascii=fmt) + trailing, encoding='utf-8')

    # report the big offenders
    seen = {}
    for iid, name, n in changed:
        seen[name] = n
    print(f'normalized {len(changed)} variant items across {len(seen)} functional types:')
    for name, n in sorted(seen.items(), key=lambda x: -x[1]):
        ex = next(i for i, nm, _ in changed if nm == name)
        band = acc[ex].get('floorSpawnWeight', acc[ex].get('floor_spawn_weight', {}))
        per = band.get('1-20', '?')
        print(f'  {name:24} {n} variants -> each {per}/floor (was 80), category ~{n*per if isinstance(per,int) else "?"}')


if __name__ == '__main__':
    main()
