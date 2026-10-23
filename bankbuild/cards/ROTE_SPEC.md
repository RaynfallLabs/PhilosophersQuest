# Rote context cards: the lesson, then one worked example

For the two **snappy-rote** subjects, **grammar** and **math**. These cards are
not like the teaching cards in `AUTHOR_SPEC.md`, and the difference is the whole
point.

**Ruling (Brandon, 2026-10-22).** Grammar: *"just teach the grammar lesson with
an example, kids can figure out from there."* Math: *"method cards and an
example."*

A wonder-subject card teaches every rung's fact, so a reader can answer the
whole ladder. A rote card does the opposite: it teaches the **rule or the
method**, shows it **worked once**, and then the kid **applies it**. Handing over
each answer would defeat the subject. So:

- **no `teaches` map** — do not write one;
- **no cold-reader judge** — these batches go gate → merge;
- a keyed answer of **four or more words must not appear verbatim** in the card.
  Pick a different example. Short keys are exempt and expected: a card about
  *affect* versus *effect* has to use both words, and a method card has to do
  arithmetic.

## Shape

```
{"<topic>": {"context_blurb": "..."}}
```

- **55–220 words.** Teach the rule, not the history. No sources, no URLs.
- Must contain a **worked example**, labelled: `Example:` or `Worked example:`
  (`Worked examples:` is fine for two).
- Two or three short paragraphs reads best: the rule, any sub-cases, then the
  example. Blank line between paragraphs.
- Grade-10 reader; the audience is teenagers.
- **No singular they.** Every individual is he, she or it.
- Active voice, and no quiz talk: never "rung", "ladder", "stem", "distractor",
  "this topic", "the kid should".
- Plain prose. No headings, bullets or markdown — it renders as flowing text in
  the game's C-key panel.

## Grammar

The bank's voice rule is **Comma-Saves-Lives, punchline-led**: a kid learns to
spot the mistake because the **wrong** version is funny or alarming, and the
jolt is the mnemonic. So the card may and should **show the misuse**:

> Example: "Let's eat, Grandma!" invites her to dinner. "Let's eat Grandma!"
> makes her the dinner.

A whole **wrong choice** may appear in the card — in grammar the misuse is the
lesson. Only the **keyed** answer is protected.

Give the rule in the terms a kid can carry: what the mark or the form does, when
it is needed, and the one test he can run on his own sentence ("read it aloud
and hear who is being spoken to"). Where a rule is genuinely optional or
disputed (the Oxford comma, a split infinitive, a sentence-ending preposition),
say so plainly rather than inventing a law.

## Math

A method card names the skill, gives the mental trick, and works one example
through, with numbers that are **not** one of that class's own questions. Say
*why* the method works where it is short to say ("the rule exists so that
everyone reading the same line of maths gets the same answer"). "Then the answer
is 35" is correct prose here.

The 27 shipped math cards are the reference implementation. Read a few before
writing anything.

## Commands

```
py -m bankbuild.cards.rote extract <subject> [--size 27]
py -m bankbuild.cards.rote gate <subject> <batch> [--quiet]
py -m bankbuild.cards.rote merge <subject> <batch> [<batch> ...]
```

Write `_cards/<subject>/bNNN_cards.json` and run the gate until the batch is
clean. Log any error you find in the **questions** themselves; do not edit
question data.

## Notes from the grammar writers (b001-b003)

- The keyed-answer rule bites hardest on **mnemonic and list** answers, not on
  example sentences. Keys like "Remember Affect Verb Effect Noun" or "for, and,
  nor, but, or, yet, so" are exactly what a card has to teach. Keep the content
  and break the sequence: reorder the list, or slip a word in ("for, and, nor,
  but, or, yet AND so"). Only the word ORDER protects you, since the comparison
  folds dashes and punctuation to spaces.
- A grammar key is often a short word plus a parenthetical gloss ("is
  (collective noun treated as singular)"), which clears four words even though
  the word itself is unavoidable. Printing the answer WORD is fine; it is the
  gloss, verbatim and in order, that trips the gate. Say it in your own words.
- The misuse goes IN the card, and that is what makes it stick: "bare with me",
  "The cat's are everywhere", "While eating the cat watched television". Writing
  only the correct version produces a flat card.
- 150-180 words with one three-sentence worked example at the end sits
  comfortably inside the window every time.
- Some grammar topics are near-duplicates of each other. Write each from a
  genuinely different angle (rule-first for one, usage-drift or a count/mass
  test for the other) or they read as copies in the C-key panel.
