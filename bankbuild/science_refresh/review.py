"""Write the review page for Brandon's one stop (plan section 10, step 3).

    py -m bankbuild.science_refresh.review <out.md> [--pilot-only]

The page carries: the unit list by tier and strand, with each unit's lines in
the curriculum map; then every pilot unit in full (every question, its choices
with the answer marked, its context, the teaching card), what the judge and
the fact-check caught, and the information-only length and reading figures.
"""
from __future__ import annotations

import sys
from collections import defaultdict

from bankbuild.cards.common import stem_hash
from bankbuild.science_refresh.common import (STRANDS, TIER_GRADE, UNITS_DIR, load_units, map_lines,
                                              read_json, unit_questions)
from bankbuild.science_refresh.stats import fk_grade, summarise

STRAND_NAME = {'physical': 'Physical', 'life': 'Life', 'earth': 'Earth and space', 'method': 'How we know'}
ORD = {1: '5th', 2: '6th', 3: '7th', 4: '8th', 5: '9th'}


def unit_table(units: list[dict], lines: dict) -> list[str]:
    out = []
    for tier in range(1, 6):
        tu = [u for u in units if u['tier'] == tier]
        n = sum(u.get('target_q', 0) for u in tu)
        out.append(f'\n### T{tier}: {ORD[tier]} grade ({len(tu)} units, {n} questions to write)\n')
        out.append('| # | Unit | Strand | Map lines | Writes | What it teaches |')
        out.append('|---|---|---|---|---|---|')
        for i, u in enumerate(sorted(tu, key=lambda u: (STRANDS.index(u['strand']), u['title'])), 1):
            ml = ', '.join(u.get('map_lines', []))
            star = '**pilot**' if u.get('pilot') else ''
            stance = '**stance**' if u.get('framing_note', '').startswith('STANCE') else ''
            scope = u.get('scope', '')
            if len(scope) > 230:
                scope = scope[:230].rsplit(' ', 1)[0] + '...'
            tags = ' '.join(x for x in (star, stance) if x)
            out.append(f"| {i} | {u['title']} | {STRAND_NAME[u['strand']]} | {ml} | {u.get('target_q', '')} | "
                       f"{(tags + ' ') if tags else ''}{scope.replace('|', '/')} |")
    return out


def strand_totals(units: list[dict]) -> list[str]:
    from bankbuild.science_refresh.common import HERE
    cfg = read_json(HERE / 'config.json', {})
    tgt = cfg.get('strand_targets_final', {})
    out = ['| Tier | ' + ' | '.join(STRAND_NAME[s] for s in STRANDS) + ' | All |',
           '|---|' + '---|' * (len(STRANDS) + 1)]
    for tier in range(1, 6):
        cells, tot = [], 0
        for s in STRANDS:
            n = sum(u.get('target_q', 0) for u in units if u['tier'] == tier and u['strand'] == s)
            tot += n
            cells.append(f"{n} (keep {tgt.get(str(tier), {}).get(s, '?')})")
        out.append(f'| T{tier} | ' + ' | '.join(cells) + f' | {tot} (keep 200) |')
    return out


def pilot_unit(u: dict, lines: dict) -> list[str]:
    d = UNITS_DIR / u['id']
    kind, qs = unit_questions(u['id'])
    final = read_json(d / 'final.json', {}) or {}
    draft = read_json(d / 'draft.json', {}) or {}
    judge = (read_json(d / 'judge.json', {}) or {}).get('questions', {})
    fc = (read_json(d / 'factcheck.json', {}) or {}).get('questions', {})
    card = read_json(d / 'card.json')
    out = [f"\n## Pilot T{u['tier']} ({ORD[u['tier']]} grade): {u['title']}\n"]
    out.append(f"Strand: {STRAND_NAME[u['strand']]}. Curriculum map: "
               + '; '.join(f"**{lid}** {lines[lid]['text'].rstrip('.')}" if lid in lines else lid
                           for lid in u.get('map_lines', []))
               + '.\n')
    nd = len(draft.get('questions', []))
    jv = defaultdict(int)
    for v in judge.values():
        jv[v.get('verdict', '?')] += 1
    fv = defaultdict(int)
    for v in fc.values():
        fv[v.get('verdict', '?')] += 1
    out.append(f"Written {nd}; judge: {dict(jv)}; fact-check: {dict(fv)}; "
               f"revised {len(final.get('revised') or {})}, added {len(final.get('added') or {})}, "
               f"dropped {len(final.get('dropped') or [])}; **{len(qs)} kept** ({kind}).\n")
    for i, q in enumerate(qs, 1):
        out.append(f"**{i}.** {q['question']}\n")
        for c in q['choices']:
            out.append(f"- {'**' + c + '** (answer)' if c == q['answer'] else c}")
        out.append(f"\n*After the answer:* {q.get('context', '')}\n")
    if final.get('dropped'):
        out.append('**Dropped, and why:**\n')
        for x in final['dropped']:
            out.append(f"- {x.get('question', '')} *({x.get('why', '')})*")
        out.append('')
    if final.get('revised'):
        out.append('**What the judge and the fact-check changed:**\n')
        for h, r in final['revised'].items():
            out.append(f"- {r.get('why', '')}")
        out.append('')
    if card:
        out.append(f"**The teaching card** ({card.get('words')} words; the player opens it with C):\n")
        for para in card['context_blurb'].split('\n\n'):
            out.append(f'> {para}\n>')
        out[-1] = out[-1].rstrip('>').rstrip()
        out.append('')
    else:
        out.append('*(No teaching card saved yet.)*\n')
    return out


def info_table(units: list[dict]) -> list[str]:
    out = ['| Tier | Questions | Stem words (median, range) | Reading grade (median) | Answer words (median) | Opens on a name/year/place |',
           '|---|---|---|---|---|---|']
    for u in sorted(units, key=lambda u: u['tier']):
        _k, qs = unit_questions(u['id'])
        s = summarise(qs)
        if not s['n']:
            continue
        out.append(f"| T{u['tier']} {u['title']} | {s['n']} | {s['stem_words_median']} ({s['stem_words_range'][0]}-{s['stem_words_range'][1]}) "
                   f"| {s['reading_grade_median']} | {s['answer_words_median']} | {s['story_share']}% |")
    return out


def old_bank_table() -> list[str]:
    import json
    from bankbuild.cards.common import QDIR
    qs = json.loads((QDIR / 'science.json').read_text(encoding='utf-8'))
    out = ['| Tier | Questions | Stem words (median, range) | Reading grade (median) | Answer words (median) | Opens on a name/year/place |',
           '|---|---|---|---|---|---|']
    for t in range(1, 6):
        s = summarise([q for q in qs if q.get('tier') == t])
        out.append(f"| old T{t} | {s['n']} | {s['stem_words_median']} ({s['stem_words_range'][0]}-{s['stem_words_range'][1]}) "
                   f"| {s['reading_grade_median']} | {s['answer_words_median']} | {s['story_share']}% |")
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    out_path = sys.argv[1]
    units = load_units()
    lines = map_lines()
    pilots = [u for u in units if u.get('pilot')]
    body = []
    body.append('\n# The unit list\n')
    body.append('Questions to WRITE per tier and strand (about 10% over, so the judges and the fact-check can drop the weak ones and each tier still keeps 200):\n')
    body += strand_totals(units)
    body += unit_table(units, lines)
    body.append('\n# The pilot: one unit a tier, every step run\n')
    for u in sorted(pilots, key=lambda u: u['tier']):
        body += pilot_unit(u, lines)
    body.append('\n# Information only (never gates)\n')
    body.append('Length, reading grade and story share, per pilot unit. Brandon ruled on 2026-11-25 that these are not rules.\n')
    body += info_table(pilots)
    body.append('\nThe same measures on the old bank (3,503 questions), for comparison:\n')
    body += old_bank_table()
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(body) + '\n')
    print(f'wrote {out_path}')


if __name__ == '__main__':
    main()
