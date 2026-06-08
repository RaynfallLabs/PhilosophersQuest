# Philosophy Rebuild Brief — 2026-06-06

This brief **amends** `PHILOSOPHY_FRAMEWORK.md` + `PHILOSOPHY_TEMPLATES.md` for the
surgical rebuild the user ordered 2026-06-06. Where this brief conflicts with the
older framework, **this brief + `docs/quiz/moral_vision.md` win** (moral_vision is
supreme). The generation swarm reads, in priority order: `moral_vision.md` →
this brief → `PHILOSOPHY_FRAMEWORK.md` → `PHILOSOPHY_TEMPLATES.md`.

> **STANCE GUARD (added 2026-06-07): rights are negative.** Never write or keep a
> question whose correct answer makes food, shelter, healthcare, housing, schooling,
> or a job a *natural / unalienable right* — those cost another's labor and are
> positive claims, not rights (Locke / Bastiat / Nozick). Relational duties
> (parent→child, promises, charity) are real, but they are the giver's duty, not the
> recipient's enforceable right; parental partiality stays just. Steel-man FDR's 1944
> economic bill of rights, never flame-bait it. See **moral_vision.md §3.9** +
> PHILOSOPHY_FRAMEWORK "Rights are negative." The lunch-ticket question was corrected
> under this rule (2026-06-07).

## Why a rebuild (the diagnosis, one paragraph)
~50% of the live 882-question bank is ONE template: a fabricated speaker recites
a position → *"Which view/school is X defending?"* → four `[School] — [200-char
definition]` choices. It is monotonous, name-recall in disguise, and unreadable
(a T5 record runs ~52 s of cold reading — longer than the chain timer). The
philosophers' actual lives are exiled to the `context` field (seen only on a
wrong answer); only 2.9% of stems name a real thinker. The **143 fallacy
questions (16%) are the one genuinely good thing** and are kept.

## The three amendments (user direction, 2026-06-06)

### A. Names in stems — ALLOWED for story/drama (moral_vision §8 supersedes the ban)
The old framework rule "philosopher names belong in `context`, always" is the
proximate cause of the "no history and drama" complaint. moral_vision §8's four
GOLD exemplars (Gödel demolishing Russell & Whitehead in 1931; Mises 1920;
Solzhenitsyn smuggling the *Gulag*; Douglass at Rochester) all name the figure in
a dramatic stem. **New rule:**
- A **story-led question about a real philosopher's life/drama MAY name them in
  the stem** (Socrates' trial + hemlock; Diogenes & Alexander; Hypatia; Boethius
  writing in his death cell; Seneca; Gödel; Solzhenitsyn). The drama is the HOOK;
  the question still tests a **reasoning move, a concept, or the most memorable
  specific fact** (History's Wonder Pattern), never "who said it."
- **Still BANNED:** bare attribution-recall — *"X said Y; what is it called?"* /
  *"Who wrote Z?"*. Naming a figure to *recite their doctrine for a label* is the
  banned move. Naming them to *tell their story* is the encouraged one. Test: if
  you deleted the name, does the question collapse into trivia (BAD) or still
  teach the move/fact (GOOD)?

### B. Negative-flag fallacy pillar (NEW — user's top priority: "build MORE of these")
Build many fallacy questions where a **trendy soundbite that *sounds* good but
collapses under simple logic** is the worked example — drawn from the
moral_vision negative flags (central planning / "real socialism," identity-
essentialism / "woke" slogans, "the science is settled," etc.). Hard rules so
these stay rigorous, not flame-bait:
1. **The answer is the substantive COLLAPSE, not the fallacy label.** Naming the
   move ("Equivocation — two meanings as one") is shallow — the kid, and often
   the speaker, already half-know it. The correct choice must articulate,
   eloquently and grounded in THIS scene, the *actual* error the slogan hides —
   the real distinction it blurs. The fallacy's NAME goes in the `context` field,
   teaching the label AFTER the reasoning lands. Canonical example —
   "silence is violence": the answer is *"Choosing not to act is not the same as
   attacking — it treats inaction as a violent act"* (the act/omission
   distinction), NOT *"Equivocation — two meanings as one."*
2. **Name the real distinction.** Each soundbite collapses on a specific,
   nameable confusion — find it and state it so a smart 12-year-old feels the
   click: act vs. omission ("silence is violence"); immune-to-evidence /
   unfalsifiable ("real socialism has never been tried"); defending the safe
   claim to dodge the live one ("we just mean fairness"); agreement mistaken for
   proof ("the science is settled"); the false binary that erases the honest
   middle ("with us or complicit").
3. **Steelman the slogan.** State it in its most sympathetic, real-world form —
   the version a sincere advocate would use; concede what's true in it ("the
   classmate agrees silence can be wrong, but…"). No cartoon strawman.
4. **Recognition, not verdict.** The answer is the reasoning error, NEVER
   "socialism is bad" / "woke is wrong." The student learns to SEE the move.
   (Passes moral_vision §7 viral test; flame-bait FAILS.)
5. **The slogan is the vehicle; the logic is the lesson.** A kid who learns the
   act/omission distinction on "silence is violence" can wield it anywhere. That
   transfer is the point.
Target: grow the fallacy ladder toward **25% of the bank**, with negative-flag
examples a substantial share of T3–T5 fallacies (alongside the existing kid-scene
fallacies, which stay).

### C. Distractor-distance rule (NEW — user's "feels 50/50" complaint)
"Many distractors are TOO CLOSE to the answer… splitting hairs by reading an
extra 50 words twice or thrice." Fix:
1. **Distinct in KIND, not in shade.** The wrong choices must be *different kinds
   of wrong*, graspable at a glance — not near-synonyms of the answer or of each
   other. (The killer is the old school-matching set: subjectivism vs cultural
   relativism vs realism vs expressionism — four long, blurry, same-family
   definitions. Retire that shape.)
2. **The scenario tie is the tell.** Correct answer references a specific token
   from THIS scene; distractors are generic. The reader confirms by the tie, not
   by out-reading three paragraphs.
3. **Short and parallel.** All four choices the same shape and within length
   parity (≤1.30 longest/shortest), but aimed at the LOW end of the envelope
   (see targets). If a reader must re-read a choice to tell it from the answer,
   the choice is wrong.
4. **One defensible answer.** Under the scene's stated reasoning, exactly one
   choice survives (the `single_defensible_answer` judge gate enforces this).

## De-emphasize the school-matching template
The "position-defended → which academic school?" pattern may remain a **minority**
shape (well-built, short, distinct choices) but must NOT dominate. Lead instead
with: fallacy-spotting (incl. negative-flag), story-led philosopher drama,
clean Gettier-style yes/no-reason, and thought-experiment "which view is the
character using" (with SHORT distinct schools). Kill the four-paragraph -ism
matrices outright (rewrite, don't patch).

## Length targets (TIGHTER than TEMPLATES §6 — halve the current totals)
Targets, not just caps. Median should sit BELOW these. Parity ≤1.30.

| Tier | Stem ≤ | Each choice ≤ | Total record ≤ | (current median) |
|---|---:|---:|---:|---:|
| T1 | 180 | 70  | 430 | 608 |
| T2 | 210 | 80  | 510 | 704 |
| T3 | 250 | 95  | 620 | 856 |
| T4 | 290 | 110 | 720 | 1038 |
| T5 | 330 | 125 | 820 | 1153 |

(The pipeline `length_budget.py` caps {660/770/930/1100/1200} remain the hard
ceiling; these targets sit well under them for readability.)

## Keep (do not relitigate)
- The 143 fallacy questions (expand, don't replace).
- `no_verdict_on_contested`: contested metaphysics/identity/free-will/mind-body
  → attribute the claim to a character, choices are competing schools.
- Steelmanned distractors; the substantive moral-vision stances (partiality is
  just; equity feminism; Hayekian knowledge-problem; care-ethics under critique).
- §14 story-in-stem, §15 no-weasel-closers, §16 teach-before-test.
- Wonder-bias scenery (knights, oracles, dragons, named canonical thought
  experiments) — but real philosopher drama now outranks invented scenes.

## The swarm (user-ordered process)
Generate → multi-lens review → editor → gates. Per question/batch:
1. **Generator** drafts candidates for a theme/tier from the exemplars + this brief.
2. **Specialist panel (parallel), each one lens:**
   - **Readability** — can a kid read all four choices once and decide? Flags
     hair-splitting, jargon, length.
   - **Wonder** — is the hook the most memorable specific thing? (Wonder Pattern.)
   - **Teacher** — does it actually teach a transferable move? Inline-teaching OK?
   - **Historian** — is the drama/figure/fact accurate and fairly stated?
   - **Game-designer** — does it play well in a chain quiz (pace, one clear answer,
     no re-reads)?
3. **Editor** synthesizes the panel into the final question (or rejects).
4. **Gates** (deterministic + judge) — see `PHILOSOPHY_TEMPLATES.md §8`.
5. **Sample-before-scale (§10):** show the user samples of the polished output
   before merging a batch into the bank.

Anchor exemplars: `philosophy_exemplars_v2.json` (this folder).
