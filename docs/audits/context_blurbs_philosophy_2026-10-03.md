# Context Blurbs — Philosophy — 2026-10-03

**Phase 3 agent:** Context-Blurb Phase 3 for the PHILOSOPHY bank
**Source of ladders:** `bankbuild/philosophy/ladders/*.json` (365 files) + `bankbuild/philosophy/register.json` (367 topic entries)
**Output:** `data/question_contexts/philosophy.json`

---

## Summary

- **Topics processed:** 367 of 367 (every register topic covered)
- **Blurbs written:** 367, keyed by topic `id` (slug) as the join key
- **Average blurb length:** 163.1 words (range 120-201, target 150-220, 3-5 sentences)
- **Ladder files on disk:** 365; two register topics (`descartes-dream-argument`, `the-is-ought-problem-in-ethics`) have no ladder file and were authored from `scope` + `framing_note` alone
- **Encoding mismatches patched at merge time:** 1 (chunk 5 wrote `Godel's Incompleteness Theorems` plain-ASCII while the register has the umlaut `Gödel's`; a NFD-normalized fuzzy match reconciled it)
- **Duplicate / extra / missing blurbs:** 0

## Workflow

1. Enumerated all 367 topics from `bankbuild/philosophy/register.json` and loaded the matching per-topic Q+choices from `bankbuild/philosophy/ladders/<id>.json`.
2. Chunked topics into 8 batches of ~46 and launched 8 Opus sub-agents in parallel (concurrent-limit forced them to go in two waves).
3. Each sub-agent authored a WHO/WHAT/WHY blurb per topic, walked every rung's `choices` to self-check for keyed-answer leaks, generalized when a leak was detected, and wrote to `tmp/chunk_N_output.json`.
4. Coordinator merged all 8 chunks, re-keyed by `id` (not `name`) per coordinator correction, and wrote the final `data/question_contexts/philosophy.json`.

## Topics where leak prevention forced a notably general blurb

Reported by the sub-agents during their self-check pass. These were rewritten to keep all four choices on every rung plausible from the blurb alone.

### Classical / Pre-Socratic (chunk 0)
- **The Allegory of the Cave** — kept the setup abstract because T1 answers include both the imprisonment duration and what the prisoners take to be real
- **Atlantis as Plato's Invention** — rewritten twice; the pedagogical surprise *is* the keyed T3 answer, so the blurb hints at an assumption-worth-checking without naming the correction
- **Socratic Irony** — stayed at meta-commentary level ("a particular posture") because the posture description is the T3 answer
- **The Tripartite Soul and the Chariot** — generalized away from "three parts" and "two horses"
- **Virtue as Habit** — gave only the "character-as-craft" frame without the mechanism (keyed almost every rung)
- **The Theory of Forms** — described the puzzle but kept "the Forms" vague since "perfect-chair-is-more-real" is a T2 answer

### Eastern & Hellenistic (chunk 1)
- **The View From Above** — the practice itself is the T3 answer; described the setup without naming the "rise above / look down" move
- **The Obstacle Is the Way** — named the fact of a reframe without stating its content
- **The Junzi** — gestured at "something quietly explosive" without identifying the earned-nobility reframe
- **Death Is Nothing to Us** — generalized Lucretius's symmetry argument to "the main surviving objections"
- **Mencius: Human Nature Is Good** — named only "a very young child in a very dangerous moment" without identifying the sprouts argument
- **Diogenes topics** — mentioned jar/lamp/encounter at surface level without saying what any one of them proves
- **Confucian Golden Rule** — dropped "five centuries before Jesus" (T2 answer); generalized to "his own corner of the ancient world"

### Medieval / Islamic & Jewish (chunk 2)
- **The Mu'tazila vs the Ash'ari** — described *that* there was a fork about God and justice without mapping positions to school names
- **The Problem of Universals** — did not name the three canonical positions (realism/nominalism/moderate realism)
- **The Six Orthodox Schools** — gave general character without naming which Darshana specializes in logic/atomism/dualism
- **Duns Scotus** — dropped the "dunce" etymology (direct T answer)
- **Al-Ghazali on Causation** — generalized away from "we never SEE the necessity" phrasing
- **Pascal's Wager** — described him as "polymath" rather than "mathematician who co-invented probability theory" (keyed T3)

### Early Modern & Kant (chunk 3)
- **The Crooked Timber of Humanity** — the ladder *is* the famous Kant quotations; blurb orients on "quoted single sentences" without naming them
- **The Murderer at the Door** — dropped "Gestapo officer" (keyed answer); generalized to "modern versions reappear in every philosophy class"
- **The Copernican Revolution & Cosmic Humility** — accepted irreducible overlap with heliocentric content since the topic title itself telegraphs it
- **Pascal's Thinking Reed**, **Hegel's Philosophy of History**, **Spinoza biography** — kept at abstract register (shape of moves rather than specific conclusions)

### 19th-century / Marx / Rousseau / etc. (chunk 4)
- **Rousseau's Noble Savage** — stripped the amour-propre definition
- **Marx & Communist Manifesto** — removed reading-room, cotton-mill, hungry-children specifics
- **The Nazi Forgery** — removed Aryan-colony and Peter-Gast specifics
- **The Last Man** — removed near-verbatim T3 answer paraphrase
- **Existence Precedes Essence** — removed near-verbatim T1 tool-answer paraphrase
- **Montesquieu** — removed "He was blind by the time he finished it"
- **Burke** — removed the "living / dead / unborn" paraphrase
- **Marketplace of Ideas** — softened the Holmes attribution (which the ladder tests as a misquote)
- **Candlemakers' Petition** — removed "costs nothing, floods the market every day" (sun hint)
- **"From Each According to His Ability"** — removed "steer effort toward the work needed" phrasing
- **Who Nietzsche Was** — removed specific age "twenty-four"
- **Adam Smith** — removed "feed you not out of love but out of self-interest" T1 paraphrase
- **Berlin's Two Concepts** — removed "pike and minnow" literal T4 quote
- **Wollstonecraft** — generalized "ornamental uselessness"
- **Acton** — removed "judging kings and popes more leniently" (direct T2 paraphrase)
- **Mill's Harm Principle** — removed "inflammatory speaker in front of an angry crowd" (corn-dealer leak)
- **Leviathan Frontispiece** — removed the "facing inward" claim (actual answer is faces outward)

### Existentialism / Analytic / Great Problems (chunk 5)
- **Kierkegaard's Leap** — avoided the engagement-break tactic, the knight's appearance, and the "commitment reason can't prove" phrasing
- **Abraham & the Knight of Faith** — did not describe outward appearance
- **Anxiety: The Dizziness of Freedom** — did not state that anxiety "wells up from freedom"; some residual overlap with option A on T3 is unavoidable since the handle *is* the topic
- **Grand Inquisitor** — avoided "arrest," "crowd bows," and the freedom/bread exchange
- **Underground Man** — avoided "spite" as the explicit motive
- **Sartre: Condemned** — kept the Nobel response generic
- **Bad Faith** — kept the "over-attentive performance" oblique
- **Camus / Myth of Sisyphus** — framed via "ancient Greek story about a man punished by the gods" rather than naming the boulder
- **Gettier** — named the three stock scenes but did not state the "truth-by-luck" diagnosis
- **Brain in a Vat / Regress / Foundationalism / Ship of Theseus / Personal Identity / Parfit** — framed the puzzles without preferring any contested option
- **Gödel** — named Einstein and Hilbert in context without identifying which friend/goal is keyed where

### Metaphysics / Ethics / Aesthetics / Life (chunk 6)
- **Ship of the Self: Brain Transplant** — rewrote to present all three personhood views (memory / body / soul) in parallel
- **Consequentialism / Utilitarianism** — avoided Mill's "Socrates dissatisfied" line (two choices contain "Socrates"); paraphrased the slogan at arm's length
- **The Meaning of Life** — dropped "imagine Sisyphus happy," the keyed "gentle irony" line, and Tolstoy's specific hidden-cord detail

### Fallacies & Reasoning (chunk 7)
- Appeal to Ignorance, Slippery Slope, Continuum Fallacy, Modus Ponens / Tollens / Converse-Inverse — all abstract shapes; blurbs describe the family + history + why-it-endures without mirroring the specific keyed-phrase formulations in the rungs

## Troublesome topics

Topics where the self-check loop had to iterate most or where the blurb landed noticeably general:

1. **Atlantis as Plato's Invention** — the entire pedagogical surprise *is* the keyed T3 answer
2. **The Copernican Revolution & Cosmic Humility** — ladder's T3 answer is literally that Earth is an ordinary planet orbiting the Sun; irreducible overlap accepted
3. **Anxiety: The Dizziness of Freedom** — handle is also keyed phrase
4. **The Confessions as the first autobiography** — the whole substance is that the book turned inward; said "something different, something that reshaped what a book could be" without ever using "inward"
5. **Anselm's Ontological Argument** vs **The Ontological Argument & Its Critics** — overlapping scope; separated by foregrounding biography/Proslogion in the first and the Gaunilo/Kant critic sequence in the second
6. **The Is-Ought Problem in Ethics**, **Descartes' Dream Argument** — no ladder file on disk; authored from register scope + framing_note alone
7. **Diogenes topics** — every famous image (jar, lamp, Alexander retort, plucked chicken) is keyed somewhere in the Cynic strand
8. **Scope-close-to-answer topics (Marx Manifesto, Existence Precedes Essence, Nazi Forgery)** — the register's own `scope` field was nearly a plot summary of the ladder; rewrites preserved WHO/WHAT/WHY orientation while handing specific facts to the ladder
9. **Gödel's Incompleteness Theorems** — chunk 5 keyed the output with plain `Godel`; a NFD-normalized fuzzy match reconciled it to the register's `Gödel` at merge time (no re-run needed)

## Format verification

- UTF-8, `indent=2`, `ensure_ascii=False`
- 367 unique keys, all matching register `id` slugs exactly
- No empty `context_blurb` fields
- No duplicates
- Prose paragraphs only; no bullets, markdown, emojis

## Deliverables

- **Output file:** `C:/Users/brand/Documents/PhilosophersQuest/data/question_contexts/philosophy.json`
- **Scratch chunks:** `C:/Users/brand/.claude/jobs/2501f37a/tmp/chunk_{0..7}_output.json`
- **This report:** `C:/Users/brand/Documents/PhilosophersQuest/docs/audits/context_blurbs_philosophy_2026-10-03.md`
