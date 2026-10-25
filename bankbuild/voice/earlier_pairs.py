"""List every pair an EARLIER batch's notes (not_twins / cross_twins / pending
pairs) recorded against a question of batch N, with the earlier writer's
reason, so the batch-N writer keeps what earlier batches deferred to and drops
what they kept. Writes _voice/<subject>/bNNN_earlier_pairs.md.

    py -m bankbuild.voice.earlier_pairs <subject> <batch>
"""
import json
import re
import sys

from bankbuild.cards.common import load_questions, stem_hash
from bankbuild.voice.common import WORK

SUBJECT, N = sys.argv[1], int(sys.argv[2])
W = WORK / SUBJECT
live = {stem_hash(q['question']): q for q in load_questions(SUBJECT)}
mine = {}
for t in json.loads((W / f'b{N:03d}_in.json').read_text(encoding='utf-8'))['topics']:
    for q in t['questions']:
        mine[q['hash']] = (t['topic'], q)
lines = [f'# {SUBJECT} b{N:03d}: pairs earlier batches recorded against your questions', '',
         'Each entry: your question, then what the earlier writer decided and why.',
         '- **cross_twins**: the earlier batch DROPPED its copy because yours is live. KEEP yours',
         '  (do not drop or merge it away); it is now the only question on that fact.',
         '- **not_twins**: the earlier batch KEPT its copy. Apply the ownership rule: if the',
         "  earlier one is the fact's own ladder (an animal's, a place's) or the note says the later batch drops its",
         '  copy) and yours is a broad ladder, drop yours as a cross twin of the earlier',
         f"  question's live hash (search data/questions/{SUBJECT}.json by its answer: the earlier",
         "  hash may be pre-rewrite). If YOURS is the fact's own ladder, keep it (not_twins).",
         '  If the two really ask different facts, keep both (not_twins).',
         '- **pending_pairs**: the earlier writer named which ladder should own the fact; if it says',
         "  yours should drop, drop yours as a cross twin (unless it is your ladder's only tier-1 rung).",
         '  A LEAD RULING line under an entry overrides the writer: follow it.', '']
n = 0
for p in sorted(W.glob('b0*_notes.json')):
    b = int(p.name[1:4])
    if b >= N:
        continue
    notes = json.loads(p.read_text(encoding='utf-8'))
    for kind in ('not_twins', 'cross_twins', 'pending_pairs'):
        for e in notes.get(kind, []):
            hs = set(re.findall(r'\b[0-9a-f]{10}\b', json.dumps(e)))
            for h in sorted(hs & set(mine)):
                topic, q = mine[h]
                n += 1
                lines += [f'- **{topic}** {h} (T{q["tier"]}) key: "{q["answer"]}"',
                          f'  - b{b:03d} {kind}: {e.get("why", "")}']
                # The lead's ruling on a pending pair overrides the writer's guess.
                ruling = e.get('lead') or e.get('RESOLVED')
                if ruling:
                    lines.append(f'  - LEAD RULING (follow this): {ruling}')
                lines.append('')
(W / f'b{N:03d}_earlier_pairs.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f'b{N:03d}: {n} pairs')
