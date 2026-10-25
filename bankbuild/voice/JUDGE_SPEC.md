# Voice pass: judge spec

A writer has rewritten some quiz ladders into the house voice (`docs/quiz/HOUSE_VOICE.md`, the Chronicler) and merged questions that asked the same fact twice. You check the result. You are a hostile reader: the writer's word counts for nothing.

## Input
`_voice/<subject>/bNNN_judge_in.json`: for each topic, its teaching `card`, and for each question: its `hash`, the new `stem`, four `choices` (shuffled, the key not marked), and `before`: the old stem it replaces (several old stems when questions were `merged` into it).

## For every question
1. **Pick (cold).** Using ONLY the card, pick the choice the card supports. Do not use outside knowledge, even when you are sure. Copy the card's deciding sentence word for word as `quote` (one sentence, or part of one); if the card supports none, or two, pick the one it leans to and write `"NONE"`.
2. **Same question?** Compare the new stem with `before`. `same` is `true` when the new stem asks for the same fact as the old one (for a merge: the fact the old stems shared), so the same choice is right for the same reason. It is `false` when the question changed, a detail a reader needs to pick the key was lost, or the stem now leans toward a wrong answer.
3. **New or changed fact?** If the new stem states anything that is in neither `before` nor the card, or states a fact differently from them (a detail moved, a quantifier tightened, "a close relative" become "it", "faint" become "sharp"), write that claim in `new_fact`. Otherwise `""`. Rewording is not a new fact; a new or altered number, name, date, place, cause, quality or event is. A stem that now disagrees with its card or its own choices fails here too.
4. **Tier, for a `merged` question only:** rate it 1 to 5 against the subject's tier rubric (`bankbuild/subjects/<subject>.json` `tier_note`, or `docs/quiz/subjects/<subject>.md` for ai and trivia), **as if the reader had NOT read the card**: how much does a 15-year-old need to know, or how far must he reason, to answer it? Every card teaches every answer, so "the card makes it easy" is true of every question and says nothing about its tier. Compare it with the ladder's other questions at each tier.
5. `note`: anything else wrong with the question (unfair, gives the answer away, wrong pronoun, singular they), else `""`.

## For every ladder
- `voice`, 1 to 5: does the ladder read as ONE storyteller, the Chronicler, in the house shape (scene, then facts, then a short question; third person; the person or scene first, not the date; no "you" outside "Suppose you..."; no hype or quiz-talk)? 5: all of it, and it reads well aloud. 4: one or two small slips. 3 or less: a stem in another register (encyclopedia entry, chatty explainer, puzzle-book), a date-first opener, mixed tenses, or a stem that is hard to follow. Say which stems in `notes`.
- `twins_left`: pairs of hashes in the ladder that still ask the same fact (`[]` when there are none).

## Output
Write `_voice/<subject>/bNNN_judge.json`:
```json
{"<topic>": {"voice": 5, "notes": "", "twins_left": [],
             "q": {"<hash>": {"pick": "<exact choice text>", "quote": "<exact card sentence or NONE>",
                              "same": true, "new_fact": "", "tier": 3, "note": ""}}}}
```
`tier` only for merged questions. Copy choice text exactly. Save as you go: rewrite the file after every 5 topics.

Then run, from the repo root:
`C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe -m bankbuild.voice.judge score <subject> <batch>`

Your final message is the score command's output. Do not edit stems, cards or changes, and do not re-judge to raise the score. Do not start any sub-agents.
