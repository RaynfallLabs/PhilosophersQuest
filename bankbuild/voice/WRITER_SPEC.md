# Voice pass: writer spec

**Two rulings from Brandon, 2026-10-24:**
1. "For the question rewrite, we don't need 'new' facts, we just need to combine the ones we have." Same-fact twins are **merged** from the questions already there.
2. "There is no consistent voice between ladders or in a bank, nor overall in the game." Every stem is told in **the house voice, the Chronicler**: `docs/quiz/HOUSE_VOICE.md`. Read it first and keep it open. It is the controlling document for how a stem is worded.

You take a batch of topic ladders. For each ladder you (a) merge its twins, then (b) put every stem into the house voice. **Keyed answers never change** (except that a merge's survivor takes one of its group's own keys). The ladder's teaching card stays as it is; its `teaches` entries follow your new stems automatically.

## Your input
`_voice/<subject>/bNNN_in.json`:
- `voice_rule`, `tier_note`, `framing`: the subject's own rules. They still decide WHAT a question asks.
- `twin_groups`: same-fact groups found earlier by two judges (`{group: [{hash, topic}]}`). A group may span two ladders of your batch.
- `topics`: each ladder's `title`, its `card` (the teaching card: everything the ladder tests, told as a story), and its questions: `hash`, `tier`, `stem`, `answer`, `choices`, `context` (a checked explanation of the answer), `lint` (what the house-voice lint says about the stem now), `twin_group`.

## Your output
1. `_voice/<subject>/bNNN_changes.json`, in `bankbuild/cards/stage.py`'s format:
   ```json
   {"replace": [{"hash": "<live hash>", "new": {"question": "<new stem>"}}],
    "delete": ["<hash absorbed in a merge>", ...]}
   ```
   A plain rewrite gives only `"question"`. A merge's survivor may also give `"answer"`, `"choices"`, `"context"` and `"tier"` (see Merges).
2. `_voice/<subject>/bNNN_notes.json`:
   ```json
   {"merges": [{"keep": "<hash>", "absorbed": ["<hash>", ...], "tier": 3,
                "why": "<one line: the shared fact, and why this tier>"}],
    "unchanged": ["<hash of a stem already in the voice, kept word for word>", ...],
    "not_twins": [{"group": "<tw-... from twin_groups>", "why": "<the two different facts>"}],
    "question_errors": [{"hash": "<hash>", "problem": "<what looks wrong>"}]}
   ```
Every question of the batch appears exactly once: replaced, deleted (absorbed in a merge), or listed as unchanged.

## Step 1: find the twins
Twins are two or more questions whose keys rest on **the same fact**: someone who knows the answer to one knows the answer to the other. The same topic is not enough (that's a ladder's job: one story, many facts). Two rungs that ask the same thing from different angles ARE twins ("What did Diogenes ask Alexander to do?" and "Diogenes told the conqueror to stop blocking what?").

- Read the whole ladder before writing anything. List its distinct facts; any fact asked twice is a twin pair.
- Every group in `twin_groups` that touches your batch must be merged, or listed in `not_twins` with the two different facts it actually asks (the earlier judges were 99% right, so this is rare).
- Twins across ladders: the question stays in the ladder whose story the fact belongs to (Leo Africanus's books stay in Timbuktu's ladder, not Mansa Musa's).

## Step 2: merge
For each twin group, ONE question survives:
- **Stem:** the clearest stem, or two stems combined into one, keeping each one's concrete detail. Then put it in the house voice.
- **Answer:** one of the group's keyed answers, word for word (the clearest; the card teaches it).
- **Wrong answers:** the strongest three from across the group, word for word. Each must be plainly wrong; none may be the key or a paraphrase of it.
- **Context:** the group's best-checked context, or two combined, with no new facts.
- **Tier (Brandon: "evaluate the new question for appropriate tier and put it there"):** rate the merged question against the subject's `tier_note` and give it that tier, in `new.tier` and in the merge's `tier`. Don't default to the lower or the higher of the old tiers; rate the question you made.
- The others are deleted (listed in `delete` and in the merge's `absorbed`).
- No new facts. Everything in the survivor comes from the group's stems, choices and contexts, or the card.

## Step 3: put every stem into the house voice
For every question that survives (merged or not):
- Follow `docs/quiz/HOUSE_VOICE.md`: the Chronicler, third person; scene, then the facts the question needs, then one short question; the person or the scene first, never the date; no "you" except in a "Suppose you..." thought experiment; the length band for the tier; no banned tics.
- **Keep:** the fact asked, everything a reader needs to pick the key over its three wrong answers, and the vivid detail that makes the fact memorable.
- **Cut:** encyclopedia labels ("the American economist"), throat-clearing, repetition, hype, and anything the question doesn't need.
- **No new facts.** Every claim must come from the old stem or the card (see the pilot lessons below on contexts). If you are not sure a detail is true, leave it out.
- **Don't give the answer away:** no word of the key that isn't in a wrong answer too, no printed answer, acronyms spelled out ("the Royal Mail Ship Norham Castle", not "(RMS)").
- **Don't copy the card.** A new stem may not share a run of 6 or more words with its ladder's card (the card would then fail its own gate). Retell; don't lift.
- **One ladder, one voice and one tense:** read your rewritten ladder top to bottom. It should sound like one storyteller telling one story.
- A stem that already passes the lint AND reads in the voice can stay word for word: list it in `unchanged`. Don't churn good stems; don't keep a stem just to save work.
- Stance and moral voice are unchanged (`docs/quiz/moral_vision.md` §3.10, the subject's `framing`): a person did it, so name him or her; a contested claim stays in a character's mouth; teen audience; **they/them is only plural**.

## Step 4: check, then fix until clean
From the repo root:
```
C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe -m bankbuild.voice.check <subject> <batch>
```
It checks the bookkeeping (every question accounted for once, merges consistent, plain rewrites keep answer/choices/context/tier), the card-copy rule, the unchanged stems' lint, and runs `stage check` on every changed question: the subject's quizgen gates, the bank ratchets (acronyms, answer leaks, choice parity, singular they) and the house-voice lint. Warnings marked "(it had this before the change)" are old problems you may leave; every FAIL must go. Re-run until it reports 0 failures.

Then read every rewritten ladder once more as a cold reader: is each question still fair, still asking the same thing, still in one voice?

## Rules of the road
- Save as you go: rewrite `bNNN_changes.json` and `bNNN_notes.json` after every 5 ladders.
- Scratch scripts go in `_voice/<subject>/work_bNNN/`, never a shared scratchpad. Other writers run beside you.
- Never edit `data/`. The lead applies your batch after the judge passes it.
- Do not start any sub-agents. Work alone.
- If the console shows `â€"` or `?` for dashes, that is the console: set `PYTHONIOENCODING=utf-8`. The data files are clean UTF-8.
- A question that looks wrong (a false key, a stem that contradicts its context, a wrong answer that is also right): don't fix the fact; list it in `question_errors`.

## Lessons from the pilot (2026-10-24)
- **Facts come from the old stem or the card.** The `context` is a checked explanation the player reads only after answering, and the judge cannot see it, so a stem detail taken from it alone cannot be verified: leave it out.
- **Hedges are facts too.** "Is thought to have", "historians reckon", "may", "has been documented" stay in the rewrite. Turning a hedge into a flat claim ("his work shortened the war") changes the fact.
- **Quantifiers are facts.** "Others" is not "the rest"; "some" is not "all"; "about 6,000" is not "6,000". A rewrite that tightens a quantifier changes the fact (a science stem turned "others" into "the rest" and became false).
- **No comparisons the sources don't make.** Don't reach for a parallel from another story to add colour (a theology stem added Noah's forty days of rain; it was in neither the old stem nor the card, and "Forty" was a wrong answer).
- **A merge must lose nothing the card teaches on its own.** Before merging, check the card: if it teaches the two keys as two separate facts, they are not twins (list them in `not_twins`). Two Feuerbach rungs the earlier judges paired turned out to be two facts.
- **Tier of a merged question:** rate it as if the reader had NOT read the card (the card teaches every answer, so "the card makes it easy" says nothing). How much must a 15-year-old know, or how far must he reason?
- **Giveaways between rungs:** `check` warns when a stem prints another rung's answer ("the stem prints X, the answer of <hash>"). Cut the giveaway wherever nothing the question needs is lost. The ladder's own subject (Medea in Medea's ladder) may stay.
- **Don't open two stems of a ladder the same way.** Vary the scene; a ladder whose stems all begin "Friedrich Hayek..." reads like a list.

## Your final message
One line per ladder: `<topic>: N rewritten, N unchanged, N merged away` (plus anything you could not fix), then the check's summary line, then the question errors.
