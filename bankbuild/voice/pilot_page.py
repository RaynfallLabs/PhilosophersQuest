"""Build the before/after review page for voice-pass batches.

    py -m bankbuild.voice.pilot_page <out.html> <subject>:<batch> [<subject>:<batch> ...]

For every ladder: each surviving question's old stem beside its new one,
the keyed answer, the merges (the stems folded into a survivor), the
lint before and after, and the judge's voice score when the batch has one.
The page is plain HTML (no scripts), themed for light and dark.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

from bankbuild.cards.common import ROOT
from bankbuild.voice.common import bpath, load_changes, load_notes, read_json
from bankbuild.voice.lint import lint_stem

LABEL = {'ai': 'AI'}

CSS = """
:root {
  /* Layout: a reading column of ladders; each question is a before / after pair. */
  --bg: #f3f4f8; --panel: #ffffff; --ink: #1c2033; --muted: #5d6378; --line: #d9dce6;
  --accent: #5b45c9; --gold: #8a6410; --old: #eef0f5; --bad: #a3352b; --good: #2f7a4b;
  --display: "Cinzel", "Trajan Pro", Georgia, serif;
  --body: "Source Serif 4", Georgia, "Times New Roman", serif;
  --mono: "IBM Plex Mono", ui-monospace, Consolas, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #0e1222; --panel: #161b30; --ink: #e6e7f0; --muted: #9aa0b8; --line: #2a3150;
  --accent: #b8a6ff; --gold: #e3c06a; --old: #121729; --bad: #ef8a7f; --good: #7fd19c;
  color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #0e1222; --panel: #161b30; --ink: #e6e7f0; --muted: #9aa0b8; --line: #2a3150;
  --accent: #b8a6ff; --gold: #e3c06a; --old: #121729; --bad: #ef8a7f; --good: #7fd19c;
  color-scheme: dark }
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--ink); font: 17px/1.55 var(--body);
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 24px 64px; }
main { max-width: 1180px; margin: 0 auto; display: grid; gap: 28px; }
h1, h2, h3 { font-family: var(--display); font-weight: 600; text-wrap: balance; margin: 0; }
h1 { font-size: 2rem; letter-spacing: .02em; }
h2 { font-size: 1.45rem; color: var(--accent); letter-spacing: .03em; }
h3 { font-size: 1.1rem; }
p { margin: 0; max-width: 70ch; }
.intro { display: grid; gap: 12px; }
.tally { display: flex; flex-wrap: wrap; gap: 8px 18px; font: 14px/1.4 var(--mono); color: var(--muted); }
.tally b { color: var(--ink); font-weight: 600; }
nav { display: flex; flex-wrap: wrap; gap: 8px; }
nav a { font: 13px var(--mono); color: var(--accent); text-decoration: none; border: 1px solid var(--line);
  border-radius: 999px; padding: 4px 10px; background: var(--panel); }
nav a:focus-visible, nav a:hover { border-color: var(--accent); outline: none; }
section.subject { display: grid; gap: 18px; }
article.ladder { background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  padding: 18px 18px 8px; display: grid; gap: 4px; }
.ladder-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 6px 16px; }
.meta { font: 13px var(--mono); color: var(--muted); }
.voice { font: 13px var(--mono); padding: 2px 8px; border-radius: 6px; border: 1px solid var(--line); }
.voice.pass { color: var(--good); border-color: var(--good); }
.voice.fail { color: var(--bad); border-color: var(--bad); }
.q { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 20px; padding: 14px 0;
  border-top: 1px solid var(--line); }
.q:first-of-type { border-top: 0; }
.col { min-width: 0; display: grid; gap: 6px; align-content: start; }
.label { font: 11px var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.stem { margin: 0; }
.before .stem { color: var(--muted); background: var(--old); border-radius: 6px; padding: 8px 10px; font-size: 15.5px; }
.after .stem { padding: 8px 0; }
.absorbed { font-size: 14.5px; color: var(--muted); border-left: 2px solid var(--line); padding-left: 10px; }
.answer { font-size: 15px; color: var(--gold); }
.answer span { font: 11px var(--mono); letter-spacing: .08em; text-transform: uppercase; margin-right: 6px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { font: 12px var(--mono); padding: 1px 7px; border-radius: 5px; border: 1px solid var(--line); color: var(--muted); }
.chip.bad { color: var(--bad); border-color: var(--bad); }
.chip.good { color: var(--good); border-color: var(--good); }
.chip.merge { color: var(--accent); border-color: var(--accent); }
.same { color: var(--muted); font-style: italic; font-size: 15px; }
.notes { font-size: 15px; color: var(--muted); }
@media (max-width: 760px) { .q { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""


def _e(s: str) -> str:
    return html.escape(str(s or ''))


def _chips(rules: list[str], kind: str) -> str:
    return ''.join(f'<span class="chip {kind}">{_e(r)}</span>' for r in rules)


def ladder_html(subject: str, t: dict, changes: dict, notes: dict, score: dict) -> tuple[str, dict]:
    rep = {r['hash']: r.get('new') or {} for r in changes.get('replace') or []}
    deleted = set(changes.get('delete') or [])
    merges = {m['keep']: m for m in notes['merges']}
    qs = {q['hash']: q for q in t['questions']}
    counts = {'rewritten': 0, 'unchanged': 0, 'merged away': 0}
    rows = []
    for q in t['questions']:
        h = q['hash']
        if h in deleted:
            counts['merged away'] += 1
            continue
        new = rep.get(h)
        old_f = lint_stem(q['stem'], subject, q['tier'])[0]
        absorbed = ''
        m = merges.get(h)
        tier = q['tier']
        if m:
            tier = (new or {}).get('tier', m.get('tier', tier))
            absorbed = ''.join(f'<p class="absorbed">Folded in (T{qs[a]["tier"]}): {_e(qs[a]["stem"])}</p>'
                               for a in m.get('absorbed') or [] if a in qs)
        if new:
            counts['rewritten'] += 1
            stem = new.get('question', q['stem'])
            answer = new.get('answer', q['answer'])
            after = f'<p class="stem">{_e(stem)}</p>'
            new_f = lint_stem(stem, subject, int(tier))[0]
            after_chips = _chips(new_f, 'bad') or '<span class="chip good">voice lint: clean</span>'
        else:
            counts['unchanged'] += 1
            stem, answer = q['stem'], q['answer']
            after = '<p class="stem same">Kept word for word: already in the voice.</p>'
            after_chips = '<span class="chip good">voice lint: clean</span>'
        tier_note = (f'T{q["tier"]} → T{tier}' if int(tier) != int(q['tier']) else f'T{tier}')
        merge_chip = (f'<span class="chip merge">merged: {len(m.get("absorbed") or [])} folded in</span>'
                      if m else '')
        rows.append(f'''<div class="q">
  <div class="col before"><span class="label">Before · T{q["tier"]}</span>
    <p class="stem">{_e(q["stem"])}</p>{absorbed}
    <div class="chips">{_chips(old_f, "bad") or '<span class="chip">voice lint: clean</span>'}</div></div>
  <div class="col after"><span class="label">After · {tier_note}</span>{after}
    <p class="answer"><span>Answer</span>{_e(answer)}</p>
    <div class="chips">{merge_chip}{after_chips}</div></div>
</div>''')
    sc = score.get(t['topic'])
    voice = ''
    if sc:
        cls = 'pass' if sc.get('pass') else 'fail'
        voice = f'<span class="voice {cls}">judge: voice {sc.get("voice")}/5{"" if sc.get("pass") else ", needs work"}</span>'
    merges_txt = ''.join(f'<p class="notes">Merge: {_e(m.get("why", ""))}</p>'
                         for m in notes['merges'] if m['keep'] in qs)
    nottw = ''.join(f'<p class="notes">Not twins ({_e(n.get("group", ""))}): {_e(n.get("why", ""))}</p>'
                    for n in notes['not_twins'] if isinstance(n, dict)
                    and any(q['twin_group'] == n.get('group') for q in t['questions']))
    head = (f'<div class="ladder-head"><h3>{_e(t.get("title") or t["topic"])}</h3>'
            f'<span class="meta">{counts["rewritten"]} rewritten · {counts["unchanged"]} kept · '
            f'{counts["merged away"]} merged away</span>{voice}</div>')
    return f'<article class="ladder">{head}{merges_txt}{nottw}{"".join(rows)}</article>', counts


def build(pairs: list[tuple[str, int]]) -> str:
    sections, nav = [], []
    total = {'rewritten': 0, 'unchanged': 0, 'merged away': 0, 'ladders': 0}
    for subject, batch in pairs:
        pkt = read_json(bpath(subject, batch, 'in'))
        changes = load_changes(subject, batch)
        notes = load_notes(subject, batch)
        sp = bpath(subject, batch, 'score')
        score = read_json(sp) if sp.exists() else {}
        name = LABEL.get(subject, subject.title())
        arts = []
        for t in pkt['topics']:
            a, c = ladder_html(subject, t, changes, notes, score)
            arts.append(a)
            for k in c:
                total[k] += c[k]
            total['ladders'] += 1
        sections.append(f'<section class="subject" id="{subject}"><h2>{_e(name)}</h2>{"".join(arts)}</section>')
        nav.append(f'<a href="#{subject}">{_e(name)}</a>')
    tally = (f'<div class="tally"><span><b>{total["ladders"]}</b> ladders</span>'
             f'<span><b>{total["rewritten"]}</b> stems rewritten</span>'
             f'<span><b>{total["unchanged"]}</b> kept as they were</span>'
             f'<span><b>{total["merged away"]}</b> merged away as twins</span></div>')
    return f'''<title>Chronicler Voice Pilot</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>{CSS}</style>
<main>
<div class="intro">
  <h1>The Chronicler: pilot ladders</h1>
  <p>Three ladders from every bank, rewritten in the house voice (docs/quiz/HOUSE_VOICE.md) and with their same-fact twins merged. On the left, each question as it is in the game now; on the right, the new stem. The answers and the facts are unchanged. A merged question shows the stems folded into it.</p>
  <p>Read a few ladders per bank. Mark anything that sounds wrong, too plain, too long, or not like one storyteller, and the voice guide gets adjusted before the other 3,650 ladders.</p>
  {tally}
  <nav>{"".join(nav)}</nav>
</div>
{"".join(sections)}
</main>
'''


def main() -> None:
    out = Path(sys.argv[1])
    pairs = []
    for arg in sys.argv[2:]:
        s, b = arg.split(':')
        pairs.append((s, int(b)))
    out = out if out.is_absolute() else ROOT / out
    out.write_text(build(pairs), encoding='utf-8')
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
