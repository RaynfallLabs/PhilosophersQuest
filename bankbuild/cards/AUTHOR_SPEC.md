# Teaching Context Cards: author spec

**The ruling (Brandon, 2026-10-18):** "The context tab SHOULD basically have every answer hinted at in it for the ladder. That allows the game to teach if the child is willing to learn, instead of guess and have to memorize over dozens of plays."

Every quiz question belongs to a topic ladder: 2 to 12 questions on ONE subject, spread over tiers 1 to 5. In a quiz the player can press **C** to read that topic's card. The card is the open book: a teenager who reads it should be able to answer every question in the ladder, because the card taught him the facts behind them.

## Your input
`_cards/<subject>/bNNN_in.json`: for each topic you get the old card, the length band, and every question with its hash, tier, stem, keyed answer, choices and the question's own `context`. The context is a checked explanation of the answer; it is your fact source.

## Your output
`_cards/<subject>/bNNN_cards.json`:
```json
{"<topic>": {"context_blurb": "<the card, paragraphs separated by \n\n>",
             "teaches": {"<question hash>": "<the ONE sentence of the card that carries that question's fact, copied exactly>"}}}
```
Every question hash in the ladder must appear in `teaches`.

## The card's shape
1. **Opening, 40 to 70 words:** who, what, where, why it matters, and the scene. Orient a 10th-grader who has never heard of this.
2. **Then one paragraph per tier present, in order from tier 1 to tier 5.** Tell it as ONE story that deepens as the ladder does, not as a list of facts.
   - Every question's keyed fact appears once, in the card's own words.
   - Each fact carries its WHY: the mechanism, the cause or the consequence. That is what makes it memorable (the Wonder Pattern).
   - If two questions share a fact, teach it once and point both `teaches` entries at the same sentence.
3. **Length:** inside `length.min_words` to `length.max_words`; aim for `target_words` (60 + 40 per question).

## Hard rules (the gate checks the first seven mechanically)
1. **Never copy the question.** No run of 6 or more words shared with any stem.
2. **Never paste a long choice.** A choice of more than 4 words must not appear word for word. Teach the fact in different words; the player should recognise it, not match it. Short keyed answers (a name, a place, a one-to-four-word thing like "masarepa" or "a whole raw egg") DO appear, because they are the fact.
3. **Never name 3 or more of one question's choices.** Don't tour the distractors.
4. **Never state a distractor's claim as true.** A common misconception may appear only when it is named as wrong ("Most people read a sell-by date as a safety date; it is a note to the store").
5. **No "the answer is"**, no quiz talk (question, tier, rung, ladder, stem, keyed, distractor), no sources, URLs or author notes ("this topic", "this card").
6. **`teaches` sentences are copied exactly** from the card, one complete sentence each.
7. **Length band.**
8. **Facts only from the input.** Use the question contexts, the stems' own scene-setting and the old card. Do not add new facts that you can't ground there. If a context is too thin to teach a question, make the fact explicit from the stem plus the keyed answer, and stay conservative.
9. **Voice and stance as the subject's questions:**
   - `bankbuild/subjects/<subject>.json` holds `voice_rule` and `framing`.
   - `docs/quiz/moral_vision.md` §3.10 says when the bank LEANS and when it stays neutral. A contested topic keeps NO verdict in the card either; attribute positions to the people who held them.
   - Active voice: a person did it, so name him or her.
10. **Audience: teenagers, grade-10 reading level.** Plain, vivid sentences. Mild darkness is fine; nothing gory or sexual.
11. **They/them is ONLY plural.** Every individual is he, she or it.
12. **Reasoning subjects** (philosophy, economics): the answer is often a reasoning move. Teach the MOVE through the story: what the thinker noticed, why the tempting alternative fails. Name the idea in context. For philosophy, never write "X said Y" as a bare attribution; show the reasoning.

## Worked example (cooking, 5 questions, tiers 1 to 4)
> The arepa is the daily bread of Venezuela and Colombia: a thick, round cake of corn dough, browned on a griddle until it is crisp outside and soft within. People in this corner of South America have cooked corn cakes like it for nearly three thousand years.
>
> What makes an arepa is its flour. Mexican tortilla dough begins with corn steeped in limewater, an ancient process called nixtamalization. Arepa flour, masarepa, never meets lime at all. Its corn is boiled in plain water, then dried and milled, so the flour is already cooked before it reaches the kitchen.
>
> In Venezuela the cake is cooked first and filled afterwards. The cook slices the hot arepa through its edge, opening it into a pocket the way you would open a bread roll, and packs it with pulled chicken, beans or soft white cheese. The best-loved filling, the reina pepiada, is chicken mashed with avocado.
>
> Colombia goes its own way. Colombian arepas are usually thinner and seldom opened up. When a Colombian cook wants a cheesy arepa, the cheese is worked into the dough by hand before the cake is shaped: the arepa de queso.
>
> For generations, Venezuelan breakfasts cost a morning of labour called la piladera: beating soaked kernels with a heavy pestle in a waist-high wooden mortar, the pilón. In 1954 the engineer Luis Caballero Mejías patented a precooked corn flour, and in 1960 it reached the shops as Harina P.A.N., sold with a slogan that cheered the end of the pounding.
>
> Along Colombia's Caribbean shore, street cooks found one more trick. They half-fry a cake, cut a slit along its edge, slide a whole raw egg inside and drop it back into the oil. The cake puffs, and the egg cooks sealed in its heart: the arepa de huevo.

## Your loop
1. Read this spec, the subject config and moral_vision §3.10 once.
2. Write every card in your batch to `bNNN_cards.json`. Save as you go: after every 5 cards, rewrite the file with all cards so far.
3. Run the gate: `C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe -m bankbuild.cards.gate <subject> <batch>` from the repo root. Fix every failure and re-run until all pass.
4. Self-check each card as a cold reader: could someone who read ONLY this card pick every keyed answer over its three distractors? If not, the card is missing that fact or teaching it too vaguely. Fix it.
5. Re-run the gate. Your final message: one line per card ("ok" or what you could not fix), then the gate's summary line.
