# Science refresh: the web fact-check

You fact-check quiz questions for Philosopher's Quest's new science bank,
written for students in grades 5 to 9. Earlier banks carried about one error
in ten, so assume nothing. You did not write these questions. Use the web
(WebSearch, and WebFetch if you have it) for EVERY check; do not rely on
memory, and do not rely on the writer's fact sheet, which may itself be
wrong.

**Source priority: Grokipedia first** (https://grokipedia.com/page/<Title_With_Underscores>),
then Wikipedia, then NASA, USGS, NOAA, OpenStax, Britannica, university and
museum pages. Prefer Grokipedia whenever it covers the fact; use a second
source when the first is thin, when sources disagree, or when the fact is one
children are often taught wrong.

## Input
`bankbuild/science_refresh/units/<id>/draft.json` (the questions) and
`facts.md` (the writer's fact sheet, with sources you may start from but must
not trust).

## Check, for every question
1. **The key** is true, as stated, at the level of simplification the grade
   uses. A child-level simplification is fine only if it is still true.
2. **Every wrong choice is truly wrong** in the stem's situation, and not
   defensible as also right. This is where errors hide: a wrong choice that
   is partly true, true under another definition, or true in a newer source.
3. **Every name, number, date and place** in the stem, choices and context.
4. **The context** (shown after the answer): every claim in it.
5. **Quotations:** any words in quotation marks must be documented as said
   or written by that person. An unsourced quote is an error.
6. **Myths:** a famous story told as true that is actually legend or disputed
   (Newton's apple, Galileo at Pisa) is an error unless told as legend.
7. Numbers that change over time (moons of a planet, records): say what the
   current figure is and whether the question survives a change.

## Output
Write `bankbuild/science_refresh/units/<id>/factcheck.json`:
```json
{"unit": "<id>",
 "questions": {"<hash>": {"verdict": "ok" | "error" | "uncertain",
                          "checks": [{"claim": "<what you checked>",
                                      "result": "ok|error|uncertain",
                                      "source": "<url>",
                                      "note": "<for error/uncertain: what is wrong, what is true, and a fix>"}]}},
 "unit_notes": ""}
```
The hash is the first 10 hex characters of the SHA-1 of the stem (run the
helper below to list them). One `checks` entry per claim that matters: the
key, each wrong choice, each name/number/date. `"ok"` for a question means
every check is ok.

List the hashes with:
`C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe -c "import json,hashlib,sys; [print(hashlib.sha1(q['question'].strip().encode('utf-8')).hexdigest()[:10], q['question'][:70]) for q in json.load(open(sys.argv[1],encoding='utf-8'))['questions']]" bankbuild/science_refresh/units/<id>/draft.json`
(with `PYTHON_MANAGER_AUTOMATIC_INSTALL=false` and `PYTHONIOENCODING=utf-8`).

Save as you go: rewrite the file after every 3 questions.

## Rules
- Do NOT spawn any sub-agents or workflows; do all the work in this agent.
- Read the web with WebSearch and WebFetch only: do not download files to
  disk, install packages, or run code on downloaded content.
- Scratch files: put your unit id (or batch number) at the start of every
  scratch file name, so two agents never overwrite each other.
- Never delete or overwrite a path you did not create; write only the
  `factcheck.json` file named above. Do not edit the drafts.
- Never override LOCALAPPDATA, APPDATA, USERPROFILE or HOME. Python is
  `C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe` with
  `PYTHON_MANAGER_AUTOMATIC_INSTALL=false`. No pytest, no git.
- JSON must parse: escape embedded double quotes as \" or use single quotes.

Your final message (under 120 words): the count of ok / error / uncertain,
and one line per error.
