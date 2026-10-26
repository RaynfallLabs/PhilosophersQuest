"""Release build: write src/_dad_key.py from the PQ_DAD_KEY secret.

    python tools/release/write_dad_key.py

The secret holds 'pq1:<hex>[,pq2:<hex>...]', current key LAST (made by
tools/dad/make_key.py --secret). Exit code 1, and no file, when the secret is
missing or malformed: a release must never ship with the public development
key, or its codes would be DEV codes no one can check.
"""
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'src', '_dad_key.py')
_PAIR = re.compile(r'^(pq\d+):([0-9a-f]{64})$')


def parse(value: str) -> tuple[str, dict]:
    keys = {}
    for part in (value or '').strip().split(','):
        m = _PAIR.match(part.strip())
        if not m:
            raise ValueError('PQ_DAD_KEY is not a list of pqN:<64 hex> pairs')
        keys[m.group(1)] = m.group(2)
    return list(keys)[-1], keys


def main() -> int:
    try:
        current, keys = parse(os.environ.get('PQ_DAD_KEY', ''))
    except ValueError as e:
        print(f'write_dad_key: {e}. Set the repository secret PQ_DAD_KEY '
              '(py tools/dad/make_key.py --secret | gh secret set PQ_DAD_KEY).')
        return 1
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('# Written by the release build from the PQ_DAD_KEY secret.\n'
                f'CURRENT = {current!r}\nKEYS = {keys!r}\n')
    print(f'write_dad_key: {len(keys)} key(s), current {current}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
