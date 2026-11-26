# Science refresh: the one revision

You revise one or more units of Philosopher's Quest's new science bank
(grades 5-9: T1 = 5th grade ... T5 = 9th). Each question has been through the
mechanical gates, a hostile judge and a web fact-check. You get ONE revision
round; whatever still fails after it is dropped. So fix properly, or drop.

Read once: `bankbuild/science_refresh/config.json`,
`bankbuild/science_refresh/specs/RESEARCH_AUTHOR.md` (the craft rules the
questions must meet) and `docs/quiz/HOUSE_VOICE.md`.

## Input, per unit (`bankbuild/science_refresh/units/<id>/`)
`draft.json` (the questions), `facts.md`, `gates.json`, `judge.json`,
`factcheck.json`.

## What to do
For every question, decide KEEP, REVISE or DROP:
- **KEEP** when the judge said ok, the fact-check said ok, and the gates show
  no FAIL.
- **REVISE** when any of them found a real problem: every fact-check `error`;
  every judge `high` or `medium` issue; every gate FAIL. A `low` issue or an
  `uncertain` fact-check is yours to weigh: fix it when the fix is cheap and
  safe. Use the judge's suggested fix when it is good; write a better one when
  it is not. Keep the question on the SAME fact where you can.
- **DROP** when the question cannot be made right and fair, or when the
  judge said drop and you agree.
A fact-check error is never kept as it is. Any new or changed fact must be
checked on the web now (Grokipedia first), and its source added to
`facts.md` as a new numbered line (append; never rewrite the writer's lines).

You may add a replacement question on a different fact of the unit's scope
when you drop one, but only if you research and source its fact now. A unit
should end with at least 8 questions where its scope allows.

## Output
Write `bankbuild/science_refresh/units/<id>/final.json`:
```json
{"unit": "<id>",
 "questions": [ {same shape as draft.json, revised where needed} ],
 "revised": {"<new hash>": {"old_hash": "<draft hash>", "why": "<what was wrong, what changed>"}},
 "added":   {"<new hash>": "<why it was added, its fact ids>"},
 "dropped": [{"old_hash": "<draft hash>", "question": "<the stem>", "why": "<reason>"}]}
```
KEEP questions are copied unchanged (their hash stays the same). The hash is
the first 10 hex characters of the SHA-1 of the stem text (stripped, UTF-8).

Then run the gate on the finals:
`C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe -m bankbuild.science_refresh.gates --kind final <id>`
and fix every FAIL (ignore only `UNIT names no line of the curriculum map`
if the lead has not filled the unit's map lines yet). A gate-only fix counts
as part of this one revision.

## Before you finish: re-check your own changes the way the re-checker will
A fresh re-checker reads every question you changed or added, and anything it
fails is dropped. In the first 40 units, nearly every drop at the re-check was
a NEW tell the revision itself brought in. For each changed or added question,
check these in turn:
1. Read the stem, then each wrong choice. Does any word or clause in the stem
   rule that choice out? ("floats in water" rules out "sinks to the bottom";
   "pulls it up until the thread is tight" rules out "no pull".) If so,
   reword the stem or swap the choice.
2. Does the key echo a word or idea of the stem that no wrong choice shares?
3. Is the key the longest choice, the only specific one, or the only one in
   science words?
4. Could a careful student who does not know the fact rule out two choices by
   common sense alone? Then only two are live: replace the weak ones.
5. Does the new context give away another question's answer in the unit?
Fix what fails before you write `final.json`.

## Rules
- Do NOT spawn any sub-agents or workflows; do all the work in this agent.
- Read the web with WebSearch and WebFetch only: do not download files to
  disk, install packages, or run code on downloaded content.
- Scratch files: put your unit id (or batch number) at the start of every
  scratch file name, so two agents never overwrite each other.
- Never delete or overwrite a path you did not create, except that you write
  `final.json` and append to `facts.md` in the units you were given.
- Never override LOCALAPPDATA, APPDATA, USERPROFILE or HOME. Python is
  `C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe` with
  `PYTHON_MANAGER_AUTOMATIC_INSTALL=false`. No pytest, no git.
- They/them is only plural; every individual is he, she or it.
- JSON must parse: escape embedded double quotes as \" or use single quotes.

Your final message (under 150 words): per unit, kept / revised / dropped /
added, and the gate's last summary line.
