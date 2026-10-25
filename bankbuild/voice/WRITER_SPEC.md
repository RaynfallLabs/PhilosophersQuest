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
- **A twin of a question already in the bank** (its ladder was applied in an earlier batch): delete yours and record it in notes `"cross_twins": [{"drop": "<your hash>", "twin": "<the live hash>", "why": "<the shared fact>"}]`. Find the live twin with a quick search of `data/questions/<subject>.json` (read only).

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
- **Kept stems are judged as hard as rewritten ones.** In philosophy b004, 9 of 22 ladders failed on voice because stems kept word for word still opened as an encyclopedia entry ("Confucius, who lived from about 551 to 479 BC..."), a commentator's aside ("It is easy to read Berlin as..."), a textbook definition ("Logicians call this slip..."), a passive study summary, or narrator "we/us". Passing the lint is not enough: keep a stem only if it already sounds like the Chronicler telling the story. When in doubt, rewrite.
- **The stem and its choices speak the same way.** Choices never change in a plain rewrite, so if they say "you" ("You should return the wallet"), keep the stem in a "Suppose you..." frame; don't move the stem to third person and leave the choices talking to the reader. Same for pronouns: if the key says "she", the stem must still make clear who "she" is.
- **Every stem opens on a person or a scene.** The judges fail a ladder for stems that open on any of these: a doctrine summary with no one acting ("There are two ways for a rule to fail"; lead with the person where you can, since a doctrine with the speaker tucked in mid-sentence, "Pain, Epicurus claimed, comes with...", is a slip the judges tolerate once, not a style), a generalisation ("People make two claims about...", "Most rules come with an if attached"), a biography entry ("born in 1902, grew up in..."), a citation frame (a book and its year as the subject: "Word and Object (1960) took up a hard job", "The Declaration of Independence (1776) holds..."), an institutional roll call, a step-by-step walk-through ("Step one... Step two..."), or a bare numbers drill. Turn the doctrine into a moment: the thinker at work, a scene that embodies the idea, or a character facing the choice, with exactly the facts the old stem and card give. Name the people the card names.
- **The closing question must fit all four choices.** Turning "What did he argue?" into "Where did he say the clash lies?" when three choices are positions, not places, leaves only the key answering the question. Read each choice as an answer to the new closer.
- **A contested verdict is never the narrator's.** Open with whose verdict it is ("Nietzsche gives a name to the verdict that..."), not with the verdict stated flat and attributed afterwards.
- **Prefer a named character to "you".** When the choices speak to "you", keep or restore the old stem's named scene (a boy and his father) rather than turning it into second person; "Suppose you..." is for a real thought experiment, not a patch.
- **Every stem stands alone.** A player meets one rung at a time, in any order: no "Next,", "Again,", "this time" or "the same philosopher" pointing back at another question, and the stem itself sets up every name and image its key and choices lean on (a stem that drops "the king agreed 'chariot' is only a word for the parts" orphans a key about names).
- **Don't open two stems of a ladder the same way.** Vary the scene; a ladder whose stems all begin "Friedrich Hayek..." reads like a list.

## Your final message
One line per ladder: `<topic>: N rewritten, N unchanged, N merged away` (plus anything you could not fix), then the check's summary line, then the question errors.
