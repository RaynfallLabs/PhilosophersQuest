"""Drop a twin from a ladder the voice pass has already applied.

    py -m bankbuild.voice.post_drop <subject> <hash>[,<hash>...] --twin <live hash> --why "<the shared fact>" [--write]

A later batch can find that a question already in the bank asks the same fact
as one in an animal's own ladder (or another ladder that owns the story). This
deletes the applied question the way `apply` would: the card gate is run on
the ladder as it will stand first (a new failure stops it), then `stage.apply`
removes the question and its teaches entry, the index-keyed test baselines are
remapped and the voice-lint ratchet comes down. Each drop is logged in
_voice/<subject>/post_drops.json. Without --write it is a dry run.
"""
from __future__ import annotations

import json
import sys

from bankbuild.cards import stage
from bankbuild.cards.common import QDIR
from bankbuild.voice.apply import BASE, remap_baselines
from bankbuild.voice.check import _live, card_gate_after
from bankbuild.voice.common import WORK, read_json, status, write_json


def main() -> None:
    subject, hashes = sys.argv[1], sys.argv[2].split(',')
    twin = sys.argv[sys.argv.index('--twin') + 1]
    why = sys.argv[sys.argv.index('--why') + 1]
    write = '--write' in sys.argv
    live = _live(subject)
    missing = [h for h in hashes + [twin] if h not in live]
    if missing:
        sys.exit(f'not live questions: {missing}')
    # A question still in an unapplied batch belongs to that batch's writer:
    # drop it there (notes cross_twins), not here.
    done = set(status(subject)['done'])
    for pkt_path in sorted((WORK / subject).glob('b*_in.json')):
        for t in read_json(pkt_path)['topics']:
            if t['topic'] in done:
                continue
            clash = [q['hash'] for q in t['questions'] if q['hash'] in hashes]
            if clash:
                sys.exit(f'{clash} sit in {pkt_path.name} ({t["topic"]}), not yet applied: '
                         'drop them in that batch instead')
    changes = {'delete': hashes}
    errs = card_gate_after(subject, changes)
    if errs:
        sys.exit('the card gate would fail:\n  ' + '\n  '.join(errs))
    old_bank = json.loads((QDIR / f'{subject}.json').read_text(encoding='utf-8'))
    stage.apply(subject, [changes], write)
    if not write:
        print('(dry run: pass --write)')
        return
    new_bank = json.loads((QDIR / f'{subject}.json').read_text(encoding='utf-8'))
    for line in remap_baselines(subject, old_bank, new_bank, changes):
        print('  baseline', line)
    from bankbuild.voice.lint import bank_report
    vp = BASE / 'voice_lint_baseline.json'
    vbase = json.loads(vp.read_text(encoding='utf-8'))
    r = bank_report(subject)
    now = r['n'] - r['clean']
    if now < vbase.get(subject, now + 1):
        print(f'  voice lint baseline: {vbase.get(subject)} -> {now}')
        vbase[subject] = now
        vp.write_text(json.dumps(vbase, indent=2) + '\n', encoding='utf-8')
    lp = WORK / subject / 'post_drops.json'
    log = read_json(lp) if lp.exists() else []
    for h in hashes:
        q = live[h]
        log.append({'drop': h, 'topic': q.get('topic'), 'answer': q['answer'], 'twin': twin,
                    'twin_topic': live[twin].get('topic'), 'why': why})
    write_json(lp, log)
    print(f'{subject}: dropped {hashes} (twin {twin})')


if __name__ == '__main__':
    main()
