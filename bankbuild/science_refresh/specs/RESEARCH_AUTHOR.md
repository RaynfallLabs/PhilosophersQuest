# Science refresh: research and author one unit

You build ONE unit of the new science quiz bank for Philosopher's Quest, a
Pygame roguelike where every action is a quiz question (science powers magic
and wands). The new bank has 1,000 questions, 200 a tier, and **each tier is a
school grade: T1 = 5th grade, T2 = 6th, T3 = 7th, T4 = 8th, T5 = 9th.** Your
unit sits in ONE tier and is one piece of that grade's curriculum. Your brief
names the unit (its id, title, tier, grade, strand, curriculum-map lines,
scope, and any old-bank topics you may quarry).

Read first (once): `bankbuild/science_refresh/config.json` (the tier rules,
voice and lanes) and `docs/quiz/HOUSE_VOICE.md` (the Chronicler voice).

## Step 1: research, then write the fact sheet
Write `bankbuild/science_refresh/units/<id>/facts.md`.
- Number every fact: `F1`, `F2`, ... One fact per line, in plain words, then
  its source URL(s). Aim for 14-20 facts so the questions have room to choose.
- **Sources: Grokipedia FIRST** (https://grokipedia.com/page/<Title_With_Underscores>),
  then Wikipedia, NASA, USGS, NOAA, OpenStax, Britannica, university pages.
  Prefer Grokipedia whenever it covers the fact; corroborate anything a
  child could be taught wrong with a second source.
- Every number, name and date you will use needs a source on its line.
- Note any common MISCONCEPTION a student of this grade holds about the
  unit's facts (seasons from distance to the Sun, heavy things falling
  faster, the tongue map): misconceptions make honest wrong choices.
- If you quarry an old-bank topic (T3-T5 only, named in your brief), read it
  with `python -c` from `data/questions/science.json` (filter by `topic`).
  Treat every old fact as UNVERIFIED: the old banks carried about 1 error in
  10. Source it again like any other fact, or leave it out.
- Facts must be TRUE at the simplified level a child meets them. "The Moon
  shines by reflected sunlight" is true; "the Sun is an average star" is a
  half-truth (it outshines most stars in our galaxy): do not teach it.

## Step 2: author the questions
Write `bankbuild/science_refresh/units/<id>/draft.json`:
```json
{"unit": "<id>",
 "questions": [
  {"tier": 1, "topic": "<id>",
   "question": "<the stem>",
   "answer": "<the keyed choice, copied exactly>",
   "choices": ["<four choices, the answer among them>", "...", "...", "..."],
   "context": "<1-3 sentences shown after the answer>",
   "facts": ["F3"],
   "grade_note": "<one line: why a typical student of this grade is taught this fact>"}
 ]}
```
Write the number of questions your brief asks for (usually 10), each on a
DIFFERENT fact, together covering the unit's scope. Never key the same answer
twice. Mix the question shapes (what, which, why, what happens when, what does
this show).

**The tier is the grade's subject matter.** The test is the FACT: would a
typical student of this grade be taught it? Every question must be CLEAR to a
student of this grade, first time: plain words, one thing asked, one right
answer. Length is not a rule: write what the question needs to be clear and
fair, and no more.
- **T1 (5th grade):** the basic facts every kid should know, almost by
  memory. Ask plainly ("Which planet is closest to the Sun?"). A short
  concrete picture helps ("A puddle is gone after a sunny afternoon. Where did
  the water go?"). Naming a part, a process or a thing from a description is
  allowed, as long as the name cannot be worked out from the description's own
  words.
- **T2 (6th grade):** a basic fact and its simple why: the job a part does,
  the reason a thing happens, what follows from it.
- **T3 (7th grade):** apply and explain. Use the idea on a new case (predict,
  classify, explain), and tell the first discovery stories the grade teaches.
- **T4 (8th grade):** mechanisms and the experiments that found them: what
  was done, what was seen, what it showed.
- **T5 (9th grade):** how we know: what an observation shows, what a control
  rules out, which result would disprove a claim; honest open questions said
  to be open; stance topics only where the brief's framing note asks.

**The voice (the Chronicler; the gate lints it).** Third person. "You" only
inside a thought experiment that opens "Suppose you...". Present tense for how
things work, past tense for what people did. No exclamation marks. At most one
dash (prefer none). Never open with a date ("In 1847, ..."): the person or the
scene leads, the date follows. No "Which of the following", "Imagine",
"Picture", "Did you know", "Here is", "Let's", "think about", hype words
("amazingly", "surprisingly", "incredibly"), or capital letters for stress.
End with ONE question sentence, ending in "?". Every individual is he, she or
it: **they/them is ONLY plural, never one person.** Capitalise the Sun, the
Moon, Earth and the planets' names.

**Choices (where most questions fail).**
- All four are the same kind of thing (four planets, four cell parts, four
  water-cycle steps) and structurally parallel, of similar length. The answer
  is never the longest, the only specific one, or the only one with a number.
- Wrong choices are adjacent-but-wrong real science: the mix-ups students of
  this grade really make, the common misconception, and from T3 the
  respectable wrong theories of the past, told honestly.
- All four stay LIVE given everything the stem says. Nothing in the stem may
  rule a wrong choice out, and no word of the stem may point at the answer.
- Exactly one choice is right. A wrong choice that is also partly true is a
  broken question: fix it or swap it.
- Never "all of the above", "none of these", or a joke choice.
- Numbers are answers only when the number IS the basic fact (eight planets,
  water boils at 100 degrees Celsius) or the stem builds the expectation it
  breaks. Never key a bare year to a "what year" stem.
- Spell out any acronym the first time it appears in a stem, or put it in
  brackets after the words ("deoxyribonucleic acid (DNA)").

**The tells (the gate and a hostile judge both look for them).**
- The stem prints the answer, or shares a two-word phrase with the answer and
  no wrong choice.
- RESTATEMENT: the stem describes the solution and the answer just names it
  in the same words.
- A stem clause that rules out a choice ("this planet has no rings" when two
  choices are ringed giants).
- An answer that a careful kid who does not know the fact could still pick
  from grammar, length or wording alone.

**Context** (shown after the player answers): 1-3 sentences in this grade's
words saying why the answer is right, and where useful why the tempting wrong
choice is wrong. No URLs, no "Source:", no quiz talk ("the answer", "this
question", "distractor").

**Lanes.** A specific animal's own anatomy or behaviour is the animal bank's;
kitchen chemistry is cooking's; named places and landforms are geography's;
war and politics are history's; AI is the AI bank's. Teach the general science
(adaptations in general, the water cycle, how a volcano works), not the
creature, the recipe or the place.

**Accuracy.** Every key, every wrong choice (truly wrong), every name, number
and date comes from your fact sheet. No invented quotations: quote only words
your source quotes. Tell famous myths as myths. Attribute contested claims to
the people who made them.

## Step 3: gate and self-check
From the repo root run:
`C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe -m bankbuild.science_refresh.gates <id>`
(with the environment variable `PYTHON_MANAGER_AUTOMATIC_INSTALL=false`).
Fix every FAIL and re-run until there are none. The `UNIT names no line of
the curriculum map` failure is the lead's to fix: ignore only that one. WARN
lines are worth a look; INFO lines (lengths) are information only. FLAG lines
are possible tells for the judge: read each and fix any that is real.

Then read every question as a typical student of this grade who has NOT
studied the unit, and again as one who has:
1. Is it clear what is asked, first time, in this grade's words?
2. Could the first student pick the answer from the stem's words alone?
3. Is every wrong choice really wrong, and could the second student defend
   any of them?
4. Is the fact taught in this grade?
Fix what fails. Then re-run the gate.

## Rules
- Do NOT spawn any sub-agents or workflows; do all the work in this agent.
- Never delete or overwrite a path you did not create. Write only inside
  `bankbuild/science_refresh/units/<id>/`.
- Never override LOCALAPPDATA, APPDATA, USERPROFILE or HOME, and never run
  Python with a changed environment except `PYTHON_MANAGER_AUTOMATIC_INSTALL=false`.
  Python is `C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe`.
  Do not run pytest. Do not touch git.
- JSON must parse: escape embedded double quotes as \" or use single quotes.
- If the Windows console shows odd characters (`â€"`), that is the console,
  not the file. Set `PYTHONIOENCODING=utf-8` before printing.

Your final message (under 150 words): the number of facts and questions, the
gate's last summary line, and anything you could not source or were unsure
of.
