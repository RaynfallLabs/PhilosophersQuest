"""Regenerate `tests/data/magpick_violations_baseline.json` from the current bank state.

Run after a batch of Wonder-Pattern-§4 fixes. The gate rule is that the
baseline can only ever shrink. See `tests/test_magpick_wonder_pattern.py`
for the rule.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'tests'))
from test_magpick_wonder_pattern import BANKS, scan_bank  # type: ignore


def main() -> None:
    baseline: dict[str, list[int]] = {}
    total = 0
    for bank in BANKS:
        ids = scan_bank(bank)
        if ids:
            baseline[bank] = ids
            total += len(ids)
    out = ROOT / 'tests' / 'data' / 'magpick_violations_baseline.json'
    out.write_text(json.dumps(baseline, indent=2), encoding='utf-8')
    print(f'Regenerated baseline at {out}')
    print(f'Total flagged questions: {total}')
    for bank, ids in baseline.items():
        print(f'  {bank}: {len(ids)}')


if __name__ == '__main__':
    main()
