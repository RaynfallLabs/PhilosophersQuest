"""Check a voice-pass writer's batch before it is judged.

    py -m bankbuild.voice.check <subject> <batch>

Reads bNNN_in.json, bNNN_changes.json and bNNN_notes.json and FAILS when:
  * a question of the batch is not accounted for exactly once (replaced,
    deleted in a merge, or listed in notes "unchanged");
  * a stem left unchanged breaks the house-voice lint;
  * a plain rewrite changes the answer, the choices, the context or the tier
    (only the stem changes, unless the question survives a merge);
  * a merge's survivor takes an answer that is not one of its group's keys,
    or a wrong answer not found among the group's choices, or names no tier;
  * a question is deleted without being absorbed in a merge;
  * a twin group of the packet is neither merged nor listed in "not_twins";
  * a new stem shares a run of 6 or more words with its topic's card (the
    card would then fail its own gate: it must never copy a stem), outside
    a sentence both of them quote;
  * the change file adds or re-topics questions (not part of this pass);
  * `stage check` fails (the subject's quizgen gates, the bank ratchets and
    the house-voice lint, on every changed question).
Exit code 1 on any failure.
"""
from __future__ import annotations

import sys

from bankbuild.cards import stage
from bankbuild.cards.gate import _sentence_ngrams
from bankbuild.voice.common import (bpath, load_notes, pending_changes, pending_packet,
                                    read_json, stem_hash)
from bankbuild.voice.lint import _QUOTED, lint_stem


_LIVE: dict[str, dict] = {}


def _live(subject: str) -> dict[str, dict]:
    """The shipped bank by stem hash (the packet's contexts have their
    sources stripped, so a plain rewrite is compared with the real field)."""
    if subject not in _LIVE:
        from bankbuild.cards.common import load_questions
        _LIVE[subject] = {stem_hash(q['question']): q for q in load_questions(subject)}
    return _LIVE[subject]


def problems(subject: str, batch: int) -> list[str]:
    pkt = pending_packet(subject, batch)
    ch = pending_changes(subject, batch)
    notes = load_notes(subject, batch)
    errs: list[str] = []
    qmap: dict[str, tuple[str, dict]] = {}
    card_of: dict[str, str] = {}
    for t in pkt['topics']:
        card_of[t['topic']] = t.get('card', '')
        for q in t['questions']:
            qmap[q['hash']] = (t['topic'], q)
    if ch.get('add') or ch.get('retopic'):
        errs.append('the voice pass neither adds nor re-topics questions')
    replaced = {r['hash']: r for r in ch.get('replace') or []}
    deleted = set(ch.get('delete') or [])
    # Entries for ladders already applied are history, not this round's work.
    full = read_json(bpath(subject, batch, 'in'))
    open_topics = {x['topic'] for x in pkt['topics']}
    applied = {q['hash'] for t in full['topics'] if t['topic'] not in open_topics
               for q in t['questions']}
    unchanged = set(notes['unchanged']) - applied
    notes['merges'] = [m for m in notes['merges'] if m.get('keep') not in applied]
    for h in sorted(set(replaced) | deleted | unchanged):
        if h not in qmap:
            errs.append(f'{h}: not a question of this batch')
    for h, (t, q) in qmap.items():
        n = (h in replaced) + (h in deleted) + (h in unchanged)
        if n != 1:
            errs.append(f'{h} ({t}): accounted for {n} times (replace, delete or unchanged: once)')

    # Merges.
    keep_of: dict[str, dict] = {}
    absorbed_all: set[str] = set()
    for m in notes['merges']:
        k, ab = m.get('keep', ''), list(m.get('absorbed') or [])
        if k not in qmap:
            errs.append(f'merge: keep {k} is not in this batch')
            continue
        if k in deleted:
            errs.append(f'merge: keep {k} is also deleted')
        if not ab:
            errs.append(f'merge {k}: absorbs nothing')
        for h in ab:
            if h not in deleted:
                errs.append(f'merge {k}: absorbed {h} is not deleted')
        if m.get('tier') not in (1, 2, 3, 4, 5):
            errs.append(f'merge {k}: needs a tier (1-5), rated for the merged question')
        absorbed_all |= set(ab)
        keep_of[k] = m
    # A twin of a question already applied in another batch's ladder: the
    # writer drops it and names the live twin (notes "cross_twins").
    live_h = set(_live(subject))
    for d in notes['cross_twins']:
        if d.get('drop') in applied:
            continue                      # an applied ladder's drop
        if d.get('drop') not in deleted:
            errs.append(f'cross_twins: {d.get("drop")} is not deleted')
        if d.get('twin') not in live_h:
            errs.append(f'cross_twins: twin {d.get("twin")} is not a live question')
        if not str(d.get('why', '')).strip():
            errs.append(f'cross_twins: {d.get("drop")} needs a why')
        absorbed_all.add(d.get('drop'))
    for h in sorted(deleted - absorbed_all):
        errs.append(f'{h}: deleted but not absorbed in any merge')

    # Rewrites.
    for h, r in replaced.items():
        if h not in qmap:
            continue
        t, q = qmap[h]
        new = r.get('new') or {}
        stem = new.get('question', q['stem'])
        m = keep_of.get(h)
        if m is None:
            live = _live(subject).get(h, {})
            for f, old in (('answer', q['answer']), ('choices', q['choices']),
                           ('context', live.get('context')), ('tier', q['tier'])):
                if f in new and new[f] != old:
                    errs.append(f'{h} ({t}): a plain rewrite keeps its {f} as it is')
        else:
            group = [h] + list(m.get('absorbed') or [])
            keys = {qmap[g][1]['answer'] for g in group if g in qmap}
            pool = {c for g in group if g in qmap for c in qmap[g][1]['choices']}
            ans = new.get('answer', q['answer'])
            if ans not in keys:
                errs.append(f'merge {h}: the answer must be one of the group\'s keys')
            for c in new.get('choices', q['choices']):
                if c not in pool:
                    errs.append(f'merge {h}: choice "{c[:50]}" is not from the group')
            if new.get('tier', q['tier']) != m.get('tier'):
                errs.append(f'merge {h}: the new question\'s tier must be the merge\'s tier')
        # A sentence both quote (a grammar example under test, a title, a
        # famous line) is the thing being asked about, not a copy.
        # (grammar only: its cards carry no teaches map, so the card gate
        # test skips them; elsewhere the card gate forgives no quotation.)
        quoted = set()
        if subject == 'grammar':
            for seg in _QUOTED.findall(stem):
                quoted |= _sentence_ngrams(seg, 6)
        shared = (_sentence_ngrams(stem, 6) & _sentence_ngrams(card_of.get(t, ''), 6)) - quoted
        if shared:
            errs.append(f'{h} ({t}): the stem copies 6 words of its card: '
                        f'"{" ".join(sorted(shared)[0])}"')
    for h in unchanged:
        if h in qmap:
            t, q = qmap[h]
            f, _w = lint_stem(q['stem'], subject, q['tier'])
            if f:
                errs.append(f'{h} ({t}): left unchanged but breaks the voice lint: {", ".join(f)}')

    # Twin groups.
    named_off = {n.get('group') if isinstance(n, dict) else n for n in notes['not_twins']}
    for g, members in (pkt.get('twin_groups') or {}).items():
        hs = [mm['hash'] for mm in members]
        if not all(h in qmap for h in hs):
            continue                  # some of it is already applied
        if not any(h in deleted for h in hs) and g not in named_off:
            errs.append(f'twin group {g} ({", ".join(hs)}): merge it, or list it in '
                        'notes "not_twins" with the reason')
    return errs


def giveaways(subject: str, batch: int) -> list[str]:
    """Warnings: a stem that prints ANOTHER rung's keyed answer (a reader who
    meets both gets one free). A name most of the ladder's stems carry (its
    own subject, Medea in Medea's ladder) is not counted."""
    import re
    pkt = pending_packet(subject, batch)
    ch = pending_changes(subject, batch)
    rep = {r['hash']: r.get('new') or {} for r in ch.get('replace') or []}
    deleted = set(ch.get('delete') or [])
    out = []
    for t in pkt['topics']:
        rungs = []
        for q in t['questions']:
            if q['hash'] in deleted:
                continue
            new = rep.get(q['hash'], {})
            rungs.append((q['hash'], new.get('question', q['stem']), new.get('answer', q['answer']),
                          new.get('choices', q['choices'])))
        for h, _stem, ans, _ch in rungs:
            core = re.sub(r'^(the|a|an)\s+', '', str(ans).strip(), flags=re.I).lower()
            if len(core) < 4:
                continue
            rx = re.compile(r'(?<![\w-])' + re.escape(core) + r'(?![\w-])')
            hits = [(h2, s2) for h2, s2, _a, c2 in rungs
                    if h2 != h and rx.search(s2.lower()) and ans not in c2]
            if hits and len(hits) < max(2, len(rungs) // 2):
                for h2, _s2 in hits:
                    out.append(f'{h2} ({t["topic"]}): the stem prints "{ans}", the answer of {h}')
    return out


def main() -> None:
    subject, batch = sys.argv[1], int(sys.argv[2])
    errs = problems(subject, batch)
    for e in errs:
        print('  FAIL', e)
    for w in giveaways(subject, batch):
        print('  warn', w, '(cut it if nothing else is lost)')
    ch = pending_changes(subject, batch)
    n_stage = stage.check(subject, [ch]) if ch else 0
    total = len(errs) + n_stage
    print(f'{subject} b{batch:03d}: {len(errs)} batch failures, {n_stage} stage failures')
    sys.exit(1 if total else 0)


if __name__ == '__main__':
    main()


__all__ = ['problems', 'stem_hash']
