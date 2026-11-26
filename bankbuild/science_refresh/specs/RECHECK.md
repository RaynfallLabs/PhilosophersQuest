# Science refresh: the re-check of revised questions

You are a fresh, hostile reviewer. A writer revised some quiz questions after
a judge and a fact-checker found problems. You check ONLY the questions the
revision changed or added. Anything you fail is dropped from the bank, so be
fair and exact.

The bank is for students in grades 5-9 (T1 = 5th grade, T2 = 6th, T3 = 7th,
T4 = 8th, T5 = 9th). Read `bankbuild/science_refresh/config.json` once.

## Input, per unit (`bankbuild/science_refresh/units/<id>/`)
`final.json`: its `revised` and `added` maps name the questions to check
(by the new hash); the questions themselves are in its `questions` list.
`judge.json` and `factcheck.json` say what was wrong before; `facts.md` has
the sources.

## For each revised or added question
1. **Facts, on the web** (Grokipedia first, then Wikipedia, NASA, USGS, NOAA,
   OpenStax, Britannica): the key is true; every wrong choice is truly wrong;
   every name, number and date; the context.
2. **The old problem is fixed** (read the old issue in judge.json /
   factcheck.json).
3. **No new problem:** no knowledge tell (answer workable from the stem's
   words, a stem clause ruling out a choice, a standout answer), the fact is
   this grade's content, the question is clear to this grade, exactly one
   defensible answer, the Chronicler voice (no "you" outside "Suppose you",
   no date first, no exclamation), no singular "they".

## Output
Write `bankbuild/science_refresh/units/<id>/recheck.json`:
```json
{"unit": "<id>",
 "questions": {"<new hash>": {"verdict": "pass" | "fail",
                              "why": "<for fail: the remaining problem>",
                              "sources": ["<url>"]}}}
```

## Rules
- Do NOT spawn any sub-agents or workflows; do all the work in this agent.
- Never delete or overwrite a path you did not create; write only the
  `recheck.json` files. Do not edit questions.
- Never override LOCALAPPDATA, APPDATA, USERPROFILE or HOME. Python is
  `C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe` with
  `PYTHON_MANAGER_AUTOMATIC_INSTALL=false`. No pytest, no git.
- JSON must parse: escape embedded double quotes as \" or use single quotes.

Your final message (under 100 words): per unit, pass / fail counts and one
line per fail.
