# The science refresh (2026-11-25)

Brandon approved the plan on 2026-11-25: a new science bank of **1,000
questions, exactly 200 a tier**, where each tier is a school grade (T1 = 5th
grade, T2 = 6th, T3 = 7th, T4 = 8th, T5 = 9th). It replaces the 3,503-question
story-ladder bank. The tier is the grade's SUBJECT MATTER, plus clarity for
that grade; length is never a rule.

The bank is built in **units, not ladders**: about 115 units of 8-10
questions, each one piece of ONE grade's curriculum, in ONE tier, naming its
line in `curriculum_map.json` (TEKS grades 5-8, Biology and IPC; the Core
Knowledge Sequence; NGSS as the cross-check).

## Files
- `config.json`: the refresh's rules (tiers as grades, voice, stance at T4-T5
  only, lanes). Supersedes `bankbuild/subjects/science.json`'s design; that
  file's `framing` still governs the stance units.
- `curriculum_map.json` / `.md`: the grade-by-grade map.
- `units.json`: the unit list.
- `units/<id>/`: one folder per unit: `facts.md`, `draft.json`, `gates.json`,
  `judge.json`, `factcheck.json`, `final.json`, `recheck.json`, `card.json`,
  `state.json`.
- `specs/`: the agent briefs, one per step.

## One unit, start to finish (plan section 4)
1. Research and author (one agent, `specs/RESEARCH_AUTHOR.md`): `facts.md`
   (Grokipedia first, a source on every fact) and `draft.json`.
2. Mechanical gates: `py -m bankbuild.science_refresh.gates <id>`.
3. Adversarial judge (a fresh agent, `specs/JUDGE.md`): `judge.json`.
4. Web fact-check (a fresh agent, `specs/FACTCHECK.md`): `factcheck.json`.
5. One revision (`specs/REVISE.md`): `final.json`; then a fresh re-check of
   every changed question (`specs/RECHECK.md`): `recheck.json`; then
   `py -m bankbuild.science_refresh.finalize <id>` drops what still fails.
6. Teaching card (`specs/CARD.md` on top of `bankbuild/cards/AUTHOR_SPEC.md`):
   `py -m bankbuild.science_refresh.cards packet <batch> <ids>`, the writer,
   `py -m bankbuild.cards.gate science <batch>`,
   `py -m bankbuild.cards.judge packet science <batch>`, a cold reader
   (`bankbuild/cards/JUDGE_SPEC.md`), `py -m bankbuild.cards.judge score science <batch>`,
   then `py -m bankbuild.science_refresh.cards save <batch>`.
Each step leaves its file, so a usage wall costs only the step in flight:
look at which files a unit has to see where it stands.

## Rules for every agent
At most 3 at once, all Opus, none spawning others; never delete what it did
not make; never override LOCALAPPDATA, APPDATA, USERPROFILE or HOME; Python is
`C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe` with
`PYTHON_MANAGER_AUTOMATIC_INSTALL=false`.
