"""Is this reward code real?

    py tools/dad/check_code.py                          asks for the name and the code
    py tools/dad/check_code.py Robyn QUACK-NYEF-YZF5     or give them on the line
    py tools/dad/check_code.py --no-record ...           check without writing it down

A real code is recorded in Documents\\PQ_Dad\\redeemed.csv, so the same code
shown twice says when it was first redeemed. Works with every key you have
kept (src/_dad_key.py), so codes from older builds still check.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dadlib  # noqa: E402
from dadlib import seeker_codes  # noqa: E402

RARITY = {'common': 'bronze', 'rare': 'silver', 'epic': 'gold', 'legendary': 'violet'}


def check(seeker: str, code: str, *, record_it: bool = True, data_path: str | None = None) -> str:
    """The answer line for one code."""
    achs = dadlib.achievements(data_path)
    cats = dadlib.categories(data_path)
    if str(code).strip().upper().startswith('DEV'):
        return ('NOT A REAL CODE. It is a DEV code, from a copy of the game built '
                'without your key.')
    hit = seeker_codes.check_code(code, seeker, [(a['id'], a['code_word']) for a in achs])
    if hit is None:
        return f'NOT A REAL CODE for {seeker}.'
    aid, _label = hit
    a = next(x for x in achs if x['id'] == aid)
    what = (f'REAL CODE: {seeker}, "{a["name"]}" ({cats.get(a["category"], a["category"])}, '
            f'{a["rarity"]}, {RARITY.get(a["rarity"], "")} frame).')
    before = dadlib.redeemed(seeker, aid)
    if before:
        return what + f' Already redeemed on {before["date"]}.'
    if record_it:
        dadlib.record(seeker, code.strip().upper(), aid, a['name'])
        return what + ' First time you have seen this code. Recorded.'
    return what + ' First time you have seen this code (not recorded).'


def main(argv):
    record_it = '--no-record' not in argv
    args = [a for a in argv if not a.startswith('--')]
    dadlib.require_real_key()
    if len(args) >= 2:
        print(check(args[0], ' '.join(args[1:]), record_it=record_it))
        return
    while True:
        seeker = input('Seeker name (Enter to stop): ').strip()
        if not seeker:
            return
        code = input('Code: ').strip()
        print(check(seeker, code, record_it=record_it))
        print()


if __name__ == '__main__':
    main(sys.argv[1:])
