"""Pixel diff of two UI captures (tools/ui/capture.py output).

    python tools/ui/diff.py                       # baseline vs capture, every size found
    python tools/ui/diff.py --a _genart/ui/baseline --b _genart/ui/capture --sizes 1600x900
    python tools/ui/diff.py --only quiz_          # screens whose name contains these

For every screen present in both trees it reports the share of pixels that
changed and the bounding box of the change, and writes a diff image to
``_genart/ui/diff/<size>/<screen>.png``: the AFTER frame dimmed to 30 %, with
every changed pixel painted solid red, so a reviewer sees at a glance where the
change landed. Unchanged screens get no image. A summary table is written to
``_genart/ui/diff/SUMMARY.md``.

Exit code: 0 always (a diff is information, not a failure) unless a screen is
missing from one side, which is reported and gives exit code 1.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

import numpy as np  # noqa: E402
import pygame  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
A_DIR = ROOT / '_genart' / 'ui' / 'baseline'
B_DIR = ROOT / '_genart' / 'ui' / 'capture'
OUT_DIR = ROOT / '_genart' / 'ui' / 'diff'


def load_rgb(path: Path) -> np.ndarray:
    surf = pygame.image.load(str(path))
    # (w, h, 3) -> (h, w, 3)
    return pygame.surfarray.array3d(surf).swapaxes(0, 1).astype(np.int16)


def diff_pair(a_path: Path, b_path: Path, out_path: Path | None):
    """Return a dict describing the difference between two PNGs."""
    a = load_rgb(a_path)
    b = load_rgb(b_path)
    if a.shape != b.shape:
        return {'size_mismatch': True, 'pct': 100.0, 'changed': -1, 'bbox': None,
                'max_delta': 255}
    delta = np.abs(a - b)
    mask = delta.max(axis=2) > 0
    changed = int(mask.sum())
    total = mask.size
    res = {'size_mismatch': False, 'changed': changed,
           'pct': 100.0 * changed / total, 'bbox': None,
           'max_delta': int(delta.max()) if changed else 0}
    if changed:
        ys, xs = np.nonzero(mask)
        res['bbox'] = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        if out_path is not None:
            img = (b * 0.3).astype(np.uint8)
            img[mask] = (255, 0, 0)
            surf = pygame.surfarray.make_surface(img.swapaxes(0, 1))
            out_path.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(surf, str(out_path))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--a', default=str(A_DIR), help='BEFORE tree (default: baseline)')
    ap.add_argument('--b', default=str(B_DIR), help='AFTER tree (default: capture)')
    ap.add_argument('--out', default=str(OUT_DIR))
    ap.add_argument('--sizes', nargs='*', help='e.g. 1600x900 (default: every size in A)')
    ap.add_argument('--only', nargs='*', help='substrings of screen names')
    args = ap.parse_args(argv)

    a_root, b_root, out = Path(args.a), Path(args.b), Path(args.out)
    sizes = args.sizes or sorted(p.name for p in a_root.iterdir()
                                 if p.is_dir() and 'x' in p.name)
    lines = ['# UI capture diff', '',
             f'BEFORE `{a_root}`  vs  AFTER `{b_root}`', '',
             '| Size | Screen | Changed px | % | Max channel delta | Bounding box (x0,y0,x1,y1) |',
             '|---|---|---|---|---|---|']
    missing = 0
    n_changed = 0
    for size in sizes:
        a_dir, b_dir = a_root / size, b_root / size
        names = sorted({p.stem for p in a_dir.glob('*.png')} |
                       {p.stem for p in b_dir.glob('*.png')})
        if args.only:
            names = [n for n in names if any(o in n for o in args.only)]
        print(f'\n{size}')
        for name in names:
            ap_, bp_ = a_dir / f'{name}.png', b_dir / f'{name}.png'
            if not ap_.exists() or not bp_.exists():
                side = 'BEFORE' if not ap_.exists() else 'AFTER'
                print(f'  MISSING in {side}: {name}')
                lines.append(f'| {size} | `{name}` | missing in {side} | | | |')
                missing += 1
                continue
            r = diff_pair(ap_, bp_, out / size / f'{name}.png')
            if r['changed'] == 0:
                print(f'  {name:<28}  identical')
                continue
            n_changed += 1
            print(f"  {name:<28}  {r['pct']:7.3f} %  ({r['changed']} px, "
                  f"max delta {r['max_delta']}, bbox {r['bbox']})")
            lines.append(f"| {size} | `{name}` | {r['changed']} | {r['pct']:.3f} | "
                         f"{r['max_delta']} | {r['bbox']} |")
    out.mkdir(parents=True, exist_ok=True)
    (out / 'SUMMARY.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'\n{n_changed} changed screen(s); {missing} missing. Images + SUMMARY.md in {out}')
    return 1 if missing else 0


if __name__ == '__main__':
    pygame.init()
    sys.exit(main())
