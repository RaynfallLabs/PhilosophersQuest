"""Is this reward code real?

    py tools/dad/check_code.py                          asks for the name and the code
    py tools/dad/check_code.py Robyn QUACK-NYEF-YZF5     or give them on the line
    py tools/dad/check_code.py --for Corwin Xyz DOOM-ABCD-EFGH
                                                        checked with the Seeker name Xyz,
                                                        recorded for the kid Corwin
    py tools/dad/check_code.py --no-record ...           check without writing it down
    py tools/dad/check_code.py --allow-duplicate ...     record a code another kid used

A code is made for the Seeker name the child plays under (the name on the
Seeker page, F4 on the game's title screen), so it is checked with that name.
``--for`` gives the badge to a kid whose Seeker name is not his or her own.

A real code is recorded in Documents\\PQ_Dad\\redeemed.csv, so the same code
shown twice says when it was first redeemed, and a code already used for one
kid is flagged when it comes back for another. Works with every key you have
kept (src/_dad_key.py), so codes from older builds still check.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dadlib  # noqa: E402
from dadlib import seeker_codes  # noqa: E402

RARITY = {'common': 'bronze', 'rare': 'silver', 'epic': 'gold', 'legendary': 'violet'}


def verify(seeker: str, code: str, *, kid: str | None = None, record_it: bool = True,
           data_path: str | None = None, allow_duplicate: bool = False) -> dict:
    """What one code is, as data (check() words it; the Code Validator draws
    it). ``seeker``: the Seeker name the code is checked with. ``kid``: who
    the badge goes to (``seeker`` when not given); the ledger records it
    under the kid.

    'status' is one of:
    * 'dev': a DEV code (from a copy built without the key); never recorded.
    * 'fake': not a real code for this Seeker name.
    * 'already': the kid holds this achievement already (the ledger 'row').
    * 'duplicate': this exact code is in the ledger for another kid (the
      earlier 'row', with its kid and date). Not recorded unless
      ``allow_duplicate``, when it is recorded as 'new' with 'duplicate_of'.
    * 'new': recorded ('recorded' says whether it was written down).
    A real code also carries its 'achievement' (the data entry), 'category'
    name and key 'label'; every answer carries 'seeker' and 'kid'."""
    kid = kid or seeker
    achs = dadlib.achievements(data_path)
    cats = dadlib.categories(data_path)
    base = {'seeker': seeker, 'kid': kid}
    if str(code).strip().upper().startswith('DEV'):
        return {**base, 'status': 'dev'}
    hit = seeker_codes.check_code(code, seeker, [(a['id'], a['code_word']) for a in achs])
    if hit is None:
        return {**base, 'status': 'fake'}
    aid, label = hit
    a = next(x for x in achs if x['id'] == aid)
    out = {**base, 'achievement': a, 'label': label,
           'category': cats.get(a['category'], a['category'])}
    before = dadlib.redeemed(kid, aid)
    if before:
        return {**out, 'status': 'already', 'row': before}
    norm = seeker_codes.normalise_name(kid)
    others = [r for r in dadlib.find_code(code)
              if seeker_codes.normalise_name(r.get('seeker', '')) != norm]
    if others and not allow_duplicate:
        return {**out, 'status': 'duplicate', 'row': others[0]}
    if record_it:
        dadlib.record(kid, dadlib.code_key(code), aid, a['name'])
    out = {**out, 'status': 'new', 'recorded': record_it}
    if others:
        out['duplicate_of'] = others[0]
    return out


def check(seeker: str, code: str, *, kid: str | None = None, record_it: bool = True,
          data_path: str | None = None, allow_duplicate: bool = False) -> str:
    """The answer line for one code."""
    v = verify(seeker, code, kid=kid, record_it=record_it, data_path=data_path,
               allow_duplicate=allow_duplicate)
    other = kid and seeker_codes.normalise_name(kid) != seeker_codes.normalise_name(seeker)
    if v['status'] == 'dev':
        return ('NOT A REAL CODE. It is a DEV code, from a copy of the game built '
                'without your key.')
    if v['status'] == 'fake':
        return f'NOT A REAL CODE for {seeker}.'
    a = v['achievement']
    what = (f'REAL CODE: {seeker}, "{a["name"]}" ({v["category"]}, '
            f'{a["rarity"]}, {RARITY.get(a["rarity"], "")} frame).')
    if v['status'] == 'already':
        if other:
            return what + f' Already redeemed for {v["row"].get("seeker") or kid} on {v["row"]["date"]}.'
        return what + f' Already redeemed on {v["row"]["date"]}.'
    if v['status'] == 'duplicate':
        row = v['row']
        return what + (f' This code was already used for {row.get("seeker", "")} on '
                       f'{dadlib.nice_date(row.get("date"))}. Not recorded again '
                       f'(add --allow-duplicate to give it to {v["kid"]} anyway).')
    if v['recorded']:
        return what + ' First time you have seen this code. ' + (
            f'Recorded for {kid}.' if other else 'Recorded.')
    return what + ' First time you have seen this code (not recorded).'


def _options(argv) -> tuple[dict, list[str]]:
    """({'record_it', 'allow_duplicate', 'kid'}, the other words) from the
    command line. ``--for Corwin`` and ``--for=Corwin`` both name the kid."""
    opts = {'record_it': True, 'allow_duplicate': False, 'kid': None}
    args: list[str] = []
    it = iter(argv)
    for a in it:
        if a == '--no-record':
            opts['record_it'] = False
        elif a == '--allow-duplicate':
            opts['allow_duplicate'] = True
        elif a == '--for':
            opts['kid'] = next(it, '').strip() or None
        elif a.startswith('--for='):
            opts['kid'] = a.split('=', 1)[1].strip() or None
        elif not a.startswith('--'):
            args.append(a)
    return opts, args


def main(argv):
    opts, args = _options(argv)
    dadlib.require_real_key()
    if len(args) >= 2:
        print(check(args[0], ' '.join(args[1:]), **opts))
        return
    while True:
        seeker = input('Seeker name (Enter to stop): ').strip()
        if not seeker:
            return
        code = input('Code: ').strip()
        print(check(seeker, code, **opts))
        print()


if __name__ == '__main__':
    main(sys.argv[1:])
