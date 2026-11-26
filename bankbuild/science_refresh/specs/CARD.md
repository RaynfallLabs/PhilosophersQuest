# Science refresh: teaching cards for one-tier units

The teaching-card rules are `bankbuild/cards/AUTHOR_SPEC.md` (read it whole,
including the notes from the science writers). This page says only what is
DIFFERENT for the refreshed science bank.

1. **A unit is one tier, so the card is one lesson, not a tier-by-tier
   story.** After the opening, teach the unit's facts in the order a teacher
   would: from the big idea to the parts, or along the story's own timeline.
   Group related facts into short paragraphs (usually 3 to 5).
2. **Write at the unit's grade, not grade 10.** A T1 card (5th grade) uses
   plain words and short sentences a 10-year-old reads easily; a T5 card (9th
   grade) may use the words the 9th-grade unit teaches. Define each science
   word in plain words where it first appears.
3. **The opening (40 to 70 words) orients that student:** what this is, where
   it is seen, why it matters. A picture a kid can hold beats a definition.
4. **Show how we know where the grade allows it:** at T1-T2 a thing a kid can
   see, measure or try (a shadow, a magnet, a thermometer); at T3-T5 the
   experiment and what it showed.
5. Everything else is AUTHOR_SPEC: every question's fact taught once, with its
   why; no 6-word run copied from a stem; no long choice pasted; never two of
   one question's wrong choices named; a misconception only when named as
   wrong; `teaches` copied word for word; facts only from the questions'
   contexts, stems and the unit's `facts.md`; the length band in the packet;
   no singular "they"; no quiz talk, sources or URLs.

## Your loop
1. Read `_cards/science/bNNN_in.json` (your batch) and, for each topic, the
   unit's `bankbuild/science_refresh/units/<topic>/facts.md`.
2. Write `_cards/science/bNNN_cards.json`
   (`{"<topic>": {"context_blurb": "...", "teaches": {"<hash>": "<sentence>"}}}`).
3. Run the gate from the repo root:
   `C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe -m bankbuild.cards.gate science <batch>`
   (with `PYTHON_MANAGER_AUTOMATIC_INSTALL=false`). Fix every failure; re-run
   until every card passes.
4. Self-check as a cold reader: from the card alone, could a student of that
   grade pick every keyed answer over its three wrong choices? Check every
   `teaches` sentence carries its own question's key.
5. Your final message: one line per card ("ok" or what you could not fix), the
   gate's summary line, and any "Question errors" you found.

## Rules
- Do NOT spawn any sub-agents or workflows; do all the work in this agent.
- Never delete or overwrite a path you did not create; write only your
  batch's `bNNN_cards.json` (and scratch files in `_cards/science/work_bNNN/`).
- Never override LOCALAPPDATA, APPDATA, USERPROFILE or HOME. Python is
  `C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe` with
  `PYTHON_MANAGER_AUTOMATIC_INSTALL=false`. No pytest, no git.
- They/them is only plural; every individual is he, she or it.
