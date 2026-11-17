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


def verify(seeker: str, code: str, *, record_it: bool = True,
           data_path: str | None = None) -> dict:
    """What one code is, as data (check() words it; the Code Validator draws
    it). 'status' is 'dev', 'fake', 'already' (with the ledger 'row') or
    'new' ('recorded' says whether it was written down). A real code also
    carries its 'achievement' (the data entry), 'category' name and key
    'label'."""
    achs = dadlib.achievements(data_path)
    cats = dadlib.categories(data_path)
    if str(code).strip().upper().startswith('DEV'):
        return {'status': 'dev', 'seeker': seeker}
    hit = seeker_codes.check_code(code, seeker, [(a['id'], a['code_word']) for a in achs])
    if hit is None:
        return {'status': 'fake', 'seeker': seeker}
    aid, label = hit
    a = next(x for x in achs if x['id'] == aid)
    out = {'seeker': seeker, 'achievement': a, 'label': label,
           'category': cats.get(a['category'], a['category'])}
    before = dadlib.redeemed(seeker, aid)
    if before:
        return {**out, 'status': 'already', 'row': before}
    if record_it:
        dadlib.record(seeker, code.strip().upper(), aid, a['name'])
    return {**out, 'status': 'new', 'recorded': record_it}


def check(seeker: str, code: str, *, record_it: bool = True, data_path: str | None = None) -> str:
    """The answer line for one code."""
    v = verify(seeker, code, record_it=record_it, data_path=data_path)
    if v['status'] == 'dev':
        return ('NOT A REAL CODE. It is a DEV code, from a copy of the game built '
                'without your key.')
    if v['status'] == 'fake':
        return f'NOT A REAL CODE for {seeker}.'
    a = v['achievement']
    what = (f'REAL CODE: {seeker}, "{a["name"]}" ({v["category"]}, '
            f'{a["rarity"]}, {RARITY.get(a["rarity"], "")} frame).')
    if v['status'] == 'already':
        return what + f' Already redeemed on {v["row"]["date"]}.'
    if v['recorded']:
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
