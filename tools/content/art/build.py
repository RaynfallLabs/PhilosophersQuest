"""Redraw the game's sprites from the art modules in this folder.

Offline tooling (not loaded at runtime).

    python tools/content/art/build.py                 # report what each module covers
    python tools/content/art/build.py --write         # redraw everything into assets/tiles
    python tools/content/art/build.py --write weapon  # redraw one kind
    python tools/content/art/build.py --write --only goblin_sniper,wall

Every PNG under assets/tiles/{monsters,items,env} is listed by manifest.py
with a `kind`; the module of that name (monster_A/monster_A.py, weapon/weapon.py, ...)
in the folder of that name exposes draw(record) -> a 32x32 RGBA image. Art is written at 32x32 whatever
size the old file was: the renderer scales pixel art crisply to the tile.

The three large painted hero portraits (ranger, Robyn, wizard) are kept unless --paintings is given.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import manifest  # noqa: E402

# `player` was a painting too, on a solid white square: it is pixel art now.
PAINTINGS = {'player_ranger', 'player_robyn', 'player_wizard_f'}


def _load(kind: str):
    """Import <kind>/<kind>.py with its own folder first on the path. Two
    kinds may each have a helper called rig.py, so the previous kind's
    helpers are dropped from sys.modules before the next is loaded."""
    folder = HERE / kind
    if not (folder / f'{kind}.py').exists():
        return None
    for name, m in list(sys.modules.items()):
        f = getattr(m, '__file__', None) or ''
        if f and Path(f).resolve().parent.parent == HERE and Path(f).resolve().parent != folder:
            del sys.modules[name]
    sys.path[:] = [p for p in sys.path if Path(p).resolve().parent != HERE or Path(p).resolve() == folder]
    sys.path.insert(0, str(folder))
    return importlib.import_module(kind)


def main(argv: list[str]) -> int:
    write = '--write' in argv
    only = None
    if '--only' in argv:
        only = set(argv[argv.index('--only') + 1].split(','))
    kinds = [a for a in argv if not a.startswith('--') and (only is None or a not in ','.join(only))]
    recs = manifest.build()
    by: dict[str, list] = {}
    for r in recs:
        by.setdefault(r['kind'], []).append(r)
    total = bad = 0
    for kind, rs in sorted(by.items()):
        if kinds and kind not in kinds:
            continue
        mod = _load(kind)
        if mod is None:
            print(f'{kind}: {len(rs)} records, NO MODULE')
            continue
        n = 0
        for r in rs:
            if only is not None and r['id'] not in only:
                continue
            if r['folder'] == 'env' and r['id'] in PAINTINGS and '--paintings' not in argv:
                continue
            try:
                img = mod.draw(r)
                assert img.size == (32, 32) and img.mode == 'RGBA', (img.size, img.mode)
            except Exception as e:      # one bad drawing must not stop the rest
                bad += 1
                print(f'  FAILED {kind}/{r["id"]}: {e!r}')
                continue
            if write:
                img.save(manifest.TILES / r['folder'] / f"{r['id']}.png")
            n += 1
        total += n
        print(f'{kind}: {n} of {len(rs)} {"written" if write else "drawable"}')
    print(f'{total} sprites, {bad} failures')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
