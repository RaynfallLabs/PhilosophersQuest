# Question Quality Standard — Philosopher's Quest

## About the Game

Philosopher's Quest is an educational roguelike where **knowledge is power**. Every action in the game — combat, equipping gear, cooking, casting spells, lockpicking, praying — requires answering quiz questions. Performance determines outcome, not random chance.

The game has 12 quiz subjects, each tied to a game action:

| Subject | Game Action |
|---------|-------------|
| Math | Combat attacks (chain mode — more correct = more damage) |
| Geography | Equipping armor and shields |
| History | Equipping accessories |
| Animal | Harvesting monster corpses for ingredients |
| Cooking | Preparing food from ingredients |
| Science | Casting spells and using wands |
| Philosophy | Identifying unknown items |
| Grammar | Reading scrolls and studying spellbooks |
| Economics | Lockpicking and disarming traps |
| Theology | Praying at altars |
| Trivia | Drinking from fountains, recalling lore |
| AI | Special abilities (hack reality, manifest) |

**The player sees these questions constantly** — hundreds per run. Quality, clarity, and fairness are critical. A bad question doesn't just annoy the player — it costs them HP, food, equipment, or their life.

## Difficulty Tiers

Questions are tiered 1-5. The tier determines when and how they appear:

| Tier | Difficulty | Equivalent | Examples |
|------|-----------|------------|----------|
| **T1** | 5th grade|
| **T2** | 6th grade|
| **T3** |  7th grade|
| **T4** |8th grade |
| **T5** | 9th grade| 

**Escalator modes** start at T1 and increase tier with each correct answer. This means T1 questions are seen the MOST — they must be rock-solid.

## Answer Rules

1. **Answers must NOT restate the question.** If the question asks "What is the capital of France?", the answer is "Paris" — not "Paris, the capital of France" or "Paris, a city on the Seine and capital of France."

2. **Answers must be minimal.** Give the shortest correct response. No parenthetical clarifications, no "also known as", no supplementary facts baked into the answer. Extra context belongs in the `context` field, not the answer.

3. **Answers must NOT be lists** unless the question explicitly asks for a list. "What is X?" should have a single-concept answer, not "A, B, and C."

4. **Answers must NOT contain the question's key terms.** If the question says "Scrooge McDuck", no choice should contain "Scrooge McDuck."

## Choice Consistency Rules

5. **All 4 choices must follow the same grammatical pattern.** If one choice is a single proper noun, all must be single proper nouns. If one is a sentence, all must be sentences. Never mix bare nouns with full sentences.

6. **All 4 choices must be similar in length.** No choice should be more than ~1.5x the length of any other. The correct answer must not be visually distinguishable by length alone — not as the longest OR the shortest.

7. **All 4 choices must be plausible.** Every wrong answer must be a real concept from the same domain that could reasonably fool someone who doesn't know the subject. No joke answers, no obviously-wrong throwaways like "a type of food" or "none of the above."

## Question Rules

8. **Questions must be clear and unambiguous.** One correct answer only. If a question could have multiple valid answers, it's a bad question.

9. **Tier must match actual difficulty.** Use the tier table above. A question about chromosome mismatch in mule reproduction is NOT T1. A question about what sound a dog makes is NOT T3.

10. **Context must be educational.** The `context` field is shown after the player answers. It should teach something — explain WHY the answer is correct, give a memorable fact, or connect to the broader subject. This is where the educational value lives.

## Anti-Patterns (reject these)

- "What is the capital of X?" → "Y, the capital of X" (restates question)
- "What is X?" → "A, B, and C" (list answer to non-list question)
- "Who painted Y?" → "Leonardo da Vinci, the Renaissance master who..." (answer contains biography)
- Question about "Beagle Boys" → answer contains "Beagle Boys" (question term in answer)
- 3 choices are 5 words, 1 choice is 25 words (length outlier — either direction)
- 3 choices are nouns, 1 choice is a full sentence (grammar mismatch)
- Answer that only makes sense if you read the context field (answer must stand alone)
- Wrong answers that no reasonable person would ever pick ("banana" as an answer to a history question)

## Output Format

For each question in the CSV, fill in:
- **action**: `OK` if the question passes all rules, `FIX` if it needs changes, `DELETE` if unsalvageable
- **fixed_answer**: the corrected answer (only for FIX rows)
- **fixed_A through fixed_D**: the corrected choices (only for FIX rows — all 4 must be provided)
- **fixed_context**: corrected context (only if the context also needs fixing)

Leave fixed columns blank for OK and DELETE rows.

## Content Guidelines

Questions should be FUN, FUNNY, or inspire a sense a WONDER or CURIOSITY, where possible. 
Avoid progressive, woke, or leftist content.
Focus on American exceptionalism where appropriate and the superiority of Western thought.
 
