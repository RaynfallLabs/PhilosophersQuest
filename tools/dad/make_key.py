"""Make the secret key that reward codes are signed with.

    py tools/dad/make_key.py              make the key (once; refuses to replace one)
    py tools/dad/make_key.py --rotate     add a new key; old codes still check
    py tools/dad/make_key.py --secret     print the value GitHub's release build needs

The key is written to src/_dad_key.py, which git ignores: the repo is public,
so the key must never be committed. Keep a copy in your password manager. If
the key is lost, codes made with it can never be checked again.

The release build reads the same keys from the GitHub Actions secret
PQ_DAD_KEY. To set it without the key passing through your shell history:

    py tools/dad/make_key.py --secret | gh secret set PQ_DAD_KEY

NEVER drop an old key: a Seeker's profile is sealed with the key that wrote it
last, and a profile whose key is gone reads as an edited file.
"""
import os
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dadlib  # noqa: E402

HEADER = ('# The reward-code key, made by tools/dad/make_key.py.\n'
          '# NEVER commit this file: the repo is public (src/seeker_codes.py).\n')


def read_keys(path: str = dadlib.KEY_FILE) -> tuple[str | None, dict]:
    if not os.path.exists(path):
        return None, {}
    scope: dict = {}
    with open(path, encoding='utf-8') as f:
        exec(f.read(), scope)                     # our own two-line file
    return scope.get('CURRENT'), dict(scope.get('KEYS', {}))


def write_keys(current: str, keys: dict, path: str = dadlib.KEY_FILE):
    body = HEADER + f'CURRENT = {current!r}\nKEYS = {{\n'
    body += ''.join(f'    {k!r}: {v!r},\n' for k, v in keys.items()) + '}\n'
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(body)
    os.replace(tmp, path)


def secret_value(current: str, keys: dict) -> str:
    """'pq1:<hex>,pq2:<hex>' with the current key LAST (write_dad_key.py)."""
    order = [k for k in keys if k != current] + [current]
    return ','.join(f'{k}:{keys[k]}' for k in order)


def main(argv):
    current, keys = read_keys()
    if '--secret' in argv:
        if not keys:
            sys.exit('No key yet. Run this script without --secret first.')
        print(secret_value(current, keys))
        return
    if keys and '--rotate' not in argv:
        sys.exit(f'A key already exists ({dadlib.KEY_FILE}). It was NOT replaced. '
                 'Use --rotate to add a new one.')
    n = 1 + max([int(k[2:]) for k in keys if k[2:].isdigit()] or [0])
    label = f'pq{n}'
    keys[label] = secrets.token_hex(32)
    write_keys(label, keys)
    print(f'Key {label} written to {dadlib.KEY_FILE} (git ignores it).')
    print('Now: keep a copy of that file in your password manager, and give the')
    print('release build its copy with:')
    print('    py tools/dad/make_key.py --secret | gh secret set PQ_DAD_KEY')


if __name__ == '__main__':
    main(sys.argv[1:])
