"""Remove the dark-political-history cluster (eugenics / forced sterilization /
Tuskegee / Belmont-from-Tuskegee / Guatemala / Aktion T4) from the SCIENCE bank
(2026-06-07, user direction). Per the user: "if anything that should go in
History, not science." Science keeps real science facts, the scientist
wonder-stories pillar, and the contested-METHOD critique (vaccines/climate/COVID
as 'science as religion' refuted by the scientific method) -- but NOT the
eugenics dark-history recitation, which belongs to the History bank.

Kept (false positives / genuine science): idx712 Mendel-chromosomes, idx1030
leptons ("Who ordered that?"), idx1272 institutions-vs-practice-of-medicine
(a COVID-mandate recognition question -- a kept 264-pillar item).

Removed questions are stashed to science_eugenics_removed.json so they can be
relocated to the History bank later. Round-trip guarded.
"""
import json
import re
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / 'science.json'
STASH = Path(__file__).resolve().parent / 'science_eugenics_removed.json'

REMOVE_IDX = {
    462, 463, 726, 727, 728, 729, 730, 731, 733, 735,
    981, 982, 983, 984, 985, 986, 987, 988, 990,
    1222, 1223, 1224, 1225, 1226, 1227, 1228, 1229, 1235, 1236, 1279,
}
KEEP_FALSE_POS = {712, 1030, 1272}
PAT = (r'eugenic|steriliz|buck v|tuskegee|belmont|nuremberg|aktion t4|'
       r'madison grant|davenport|laughlin|cold spring harbor|guatemala|sanger|'
       r'feeble-minded|passing of the great race')


def blob(q):
    return (q.get('question', '') + ' ' + ' '.join(q.get('choices', []))
            + ' ' + q.get('context', '')).lower()


def main():
    orig = PATH.read_text(encoding='utf-8')
    qs = json.loads(orig)

    # detect formatting so we round-trip byte-for-byte
    trailing = orig[len(orig.rstrip('\n')):]
    fmt = None
    for flag in (False, True):
        if json.dumps(qs, indent=2, ensure_ascii=flag) == orig.rstrip('\n'):
            fmt = flag
            break
    assert fmt is not None, 'cannot round-trip science.json -- formatting mismatch'

    assert not (REMOVE_IDX & KEEP_FALSE_POS), 'keep/remove overlap!'
    # verify every removal really is dark-history (not a mis-indexed science Q)
    for i in sorted(REMOVE_IDX):
        assert re.search(PAT, blob(qs[i])), \
            f'idx{i} does not look like eugenics/dark-history: {qs[i]["question"][:70]!r}'
    # verify the keeps are NOT dark-history-primary (sanity)
    print('keeping (false-positive science):')
    for i in sorted(KEEP_FALSE_POS):
        print(f'  idx{i} T{qs[i]["tier"]}: {qs[i]["question"][:70]}')

    removed = [qs[i] for i in sorted(REMOVE_IDX)]
    STASH.write_text(json.dumps(removed, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'\nstashed {len(removed)} removed questions -> {STASH.name}')

    new = [q for j, q in enumerate(qs) if j not in REMOVE_IDX]
    assert len(new) == len(qs) - len(REMOVE_IDX)
    PATH.write_text(json.dumps(new, indent=2, ensure_ascii=fmt) + trailing, encoding='utf-8')

    import collections
    tiers = collections.Counter(q.get('tier') for q in new)
    print(f'science.json: {len(qs)} -> {len(new)} questions (removed {len(removed)})')
    print('new per-tier:', dict(sorted(tiers.items())))


if __name__ == '__main__':
    main()
