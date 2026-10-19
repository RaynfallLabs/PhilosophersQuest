"""Drop singular-they allow-list entries whose text a rewritten card removed.

    py -m bankbuild.cards.prune_they_allow

tests/test_no_singular_they.py keeps an ALLOW list of plural-referent phrases
found in data files, and fails when an entry no longer matches anything.
Rewriting a context card removes old phrases, so run this after a merge.
Only entries for data/question_contexts/ files are touched.
"""
from __future__ import annotations

import importlib.util
import re

from bankbuild.cards.common import ROOT

TEST = ROOT / 'tests' / 'test_no_singular_they.py'


def main() -> None:
    spec = importlib.util.spec_from_file_location('_they', TEST)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    flagged: dict[str, list[str]] = {}
    for rel, text in mod._all_strings():
        if mod.find_singular_they(text):
            flagged.setdefault(rel, []).append(text)
    stale = [k for k in mod.ALLOW
             if ('question_contexts' in k[0] or 'data/questions/' in k[0]) and not any(k[1] in t for t in flagged.get(k[0], []))]
    if not stale:
        print('no stale card entries')
        return
    src = TEST.read_text(encoding='utf-8')
    for _rel, phrase in stale:
        src = re.sub(r"\n[^\n]*'" + re.escape(phrase) + r"'\)?:[^\n]*", '', src, count=1)
        print(f'dropped: {phrase}')
    TEST.write_text(src, encoding='utf-8')


if __name__ == '__main__':
    main()
