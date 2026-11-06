# The house voice: the Chronicler

**Ruling (Brandon, 2026-10-24):** "There is no consistent voice between ladders or in a bank, nor overall in the game." He chose **A, the Chronicler**, from three voices written out side by side (`PLAN_MASTERY_TWINS_VOICE_2026_10_24.md`, Part C).

Every quiz question in every bank (math excepted) is told by one speaker: **the Chronicler**, a well-read storyteller telling a 15-year-old something worth knowing. The subject rules (the Wonder Pattern, Bastiat, Socratic, Recognition, the Easter Egg, Comma-Saves-Lives) still decide **what** a question asks. This document decides **how** it is said. Where the two seem to clash, the subject rule wins on content and this one on wording.

`bankbuild/voice/lint.py` enforces the mechanical rules below (marked **[lint]**). `stage check` runs the lint on every new or changed question, so the voice cannot drift again.

---

## 1. Who is speaking

- **A storyteller, in the third person.** Plain, vivid, exact, warm. He knows the story and enjoys telling it.
- **No hype.** No "amazingly", "incredibly", "believe it or not", "fun fact" **[lint]**. The fact does the work.
- **No editorialising.** The Chronicler does not tell the reader what to feel ("shockingly", "sadly") or what to conclude. Stance comes from `moral_vision.md` and the subject config, as before.
- **No quiz-talk.** No "Which of the following" **[lint]**, no "this question", no "the correct answer".
- **No encyclopedia labels as openers.** "The American economist Thomas Sowell" becomes "Thomas Sowell". Give a label only when the reader needs it to follow the story, and then after the name.

## 2. The shape of a question

**Scene, then the facts the question needs, then the question.**

1. **The scene: one concrete sentence.** A person doing something, a place at a moment, an animal in action, a thing at work. One image, not a montage.
2. **The facts: one or two sentences,** only what the question needs to be fair. Keep the vivid detail that makes the fact memorable. Cut throat-clearing, repetition and labels.
3. **The question: one short sentence,** ending in "?" **[lint]**, with a pointed closer: who, what, which, where, why or how. At most 20 words **[lint: warning over 20, failure over 30]**.

**Lead with the person or the scene, never the date [lint].** No "In 1987...", "In late 1958...", "On 4 July...", "During the 1960s...", "By the 12th century...". The date goes later in the sentence or in the next one: "Che Guevara had about 300 rebels outside Santa Clara late in 1958."

**Openings the lint refuses:** a date or era first; "Imagine", "Picture" (except "Suppose you", below); "Did you know"; "Here is" / "Here's"; "Let's".

## 3. Person and tense

- **Third person.** People, animals, places and things are the subjects of the sentences.
- **"You" only in a thought experiment, and then always opened with "Suppose you..." [lint].** Philosophy, economics and science sometimes need the reader inside the scenario ("Suppose you find a wallet with $500 in it..."). Everywhere else "you" goes: "If you salt the water" becomes "A cook who salts the water", "your phone finds you" becomes "a phone finds its place", and "What do you call it?" becomes "What is it called?".
- **Past tense for history** and for what real people did. **Myths, legends and scripture** may be told in the storyteller's present ("David is not with the army. His father sends him...") when the whole ladder is told that way: one tense per ladder. **Present tense for how things work** (an animal's body, a chemical reaction, a grammar rule, a recipe's chemistry) and for thought experiments.
- **They/them is only plural.** Every individual is he, she or it (`feedback_no_singular_they`). A hypothetical person gets a name or a role and a pronoun: "A teacher is handed two paragraphs... She has only the words."

## 4. Length

Words per stem, by tier:

| Tier | Band | Lint |
|---|---|---|
| 1 | 25 to 45 | warning outside the band; failure over 60 |
| 2 | 30 to 55 | warning outside the band; failure over 70 |
| 3 to 5 | 40 to 70 | warning outside the band; failure over 85 |

The subject's character budget (stem plus four choices) still applies and is checked by the quizgen gates. Grammar and math are exempt from the band: their stems are short by design.

## 5. Punctuation and tics

- **No exclamation marks** in the Chronicler's own words **[lint]**. A quoted line may keep its own ("Tank!", "Let's eat, Grandma!").
- **At most one dash in a stem [lint].** Two dashes make a sentence that is really three; split it.
- **No rhetorical "So what/why/how/where/which" closers [lint].** End with the question itself.
- **Banned set phrases [lint]:** "Here is the", "Here's the", "Line the ... up", "asks you to picture", "the catch", "the twist", "the kicker", "plot twist", "think about", "Did you know", "Let's", "fun fact", "believe it or not", "surprisingly", "amazingly", "incredibly".
- Quoted text (between quotation marks) is not linted. A stem's example sentences, titles and famous lines keep their own words.

## 6. What never changes in a rewrite

- **The fact asked and the keyed answer.** The answer text stays exactly as it is.
- **The choices,** unless two questions are merged (`bankbuild/voice/WRITER_SPEC.md`).
- **No new facts.** Every claim in a rewritten stem comes from the old stem, its context, or the topic's card. When in doubt, leave the detail out.
- **Fairness.** The stem still gives what a reader needs to pick the key over its three wrong answers, and still gives nothing away (no answer leaks, no printed answer, acronyms spelled out).
- **Stance and moral voice:** active voice, a named person did it; no verdict on contested questions unless `moral_vision.md` §3.10 says the bank leans; teen audience, nothing gory or sexual.

## 7. Subject notes

- **History:** past tense; the person leads ("Che Guevara had...", not "In 1958 the Argentine rebel commander..."). Name the agent of every deed.
- **Philosophy:** story shape, the thinker leads; scenario shape, the character leads ("Theo catches a bad cold..."). A contested claim stays in a character's mouth. "Suppose you" for a thought experiment the reader must stand inside.
- **Economics:** the scene shows the seen and the unseen through named people or roles (a baker, a city council). "Suppose you" for a thought experiment. Dates follow the people.
- **Science:** the discovery leads (who measured what, how); present tense for the mechanism. No "you" in everyday-science stems: "a phone", "a swimmer", "a cook".
- **Animal:** the animal leads, present tense, doing the thing.
- **Geography:** the place leads, seen at a moment, with the people who live or work there.
- **Cooking:** a named cook, a dish being made, or the food itself leads. Recipes become "a cook who...", never "you".
- **Theology:** story-led and strictly symmetric; each tradition's story told as that tradition tells it ("In the Gospel of Luke...", "Snorri tells...").
- **Trivia:** the work or the creator leads; the narrator stays inside the spoiler rules (`feedback_trivia_voice`).
- **AI:** a person doing something with a machine leads, not a news date. Recognition stays the goal.
- **Grammar:** stems stay short and punchy, and the punchline stays. The narrator still speaks: no "you", no exclamation marks outside example sentences. A bare fragment with a dash ('"3:45 PM" -- what does the colon do?') becomes a sentence ('A train timetable reads "3:45 PM." What does the colon do?').

## 8. Before and after (real stems from the banks)

**History, T2** (77 words, date first):
> In late 1958, during the last months of the Cuban revolution against the U.S.-backed dictator Fulgencio Batista, the Argentine rebel commander Che Guevara had only about 300 fighters near the city of Santa Clara in central Cuba. Batista rushed 3,500 government soldiers there by armored train, packed with fresh troops and heavy guns. Armed with just a captured bulldozer and some sticks of dynamite, what did Che's tiny band of fighters do to that armored train?

> Che Guevara had about 300 rebels outside Santa Clara late in 1958, in the last months of Cuba's revolution. The dictator Fulgencio Batista sent an armored train with 3,500 fresh soldiers and heavy guns to crush them. Che had a captured bulldozer and some dynamite. What did his band do to the train?

**Economics, T1** (encyclopedia opener, dashes):
> In 1987 the American economist Thomas Sowell wrote a book called A Conflict of Visions. It sets out two rival pictures of human nature — one that says people can be perfected by clever policy, and one that says people are flawed and stuck with hard choices. That second picture refuses a word politicians love to promise. Sowell packed the refusal into a famous six-word sentence. What is it?

> Thomas Sowell's book A Conflict of Visions sets two pictures of human nature side by side. In one, clever policy can perfect people; in the other, people are flawed and stuck with hard choices. The second refuses a word politicians love to promise. What six-word sentence did Sowell use to say so?

**Economics, T1** ("you"):
> To spend bitcoin, your wallet must keep a huge secret number safe. That number is too long to memorize or copy by hand without errors. So every modern Bitcoin wallet turns it into a much friendlier backup -- a short list of common everyday vocabulary you can write on paper and lock in a safe. What is that word-based backup called?

> A Bitcoin wallet guards a secret number far too long to memorize or copy by hand without mistakes. So every modern wallet turns it into a friendlier backup: a short list of everyday words its owner can write on paper and lock in a safe. What is that backup called?

**Science, T1** ("you"):
> Every GPS satellite has its own atomic clock. After one day, each clock drifts about 38 millionths of a second from clocks on the ground. That is far too small for you to feel. But your phone finds you by turning those clock readings into distances at the speed of light. If nobody fixed the drift, how far off would your location be after one day?

> Every GPS satellite carries an atomic clock, and each drifts about 38 millionths of a second a day from clocks on the ground. A phone finds its place by turning those readings into distances at the speed of light. If nobody corrected the drift, how far off would the phone be after one day?

**Cooking, T2** (dashes, "So where"):
> When the Gold Rush drew fortune-hunters to San Francisco in 1849, a French baker named Isidore Boudin opened his little bakery near the city's waterfront. Sourdough bread rises without a single packet of store-bought yeast — the yeast has to come from somewhere else. Boudin's very first 1849 loaves puffed up beautifully, and the sourdough he started that year is still baked in San Francisco today. So where does the wild yeast in a starter like his mostly come from?

> Isidore Boudin, a French baker, opened a little bakery on San Francisco's waterfront in the Gold Rush of 1849. His sourdough rose without a grain of store-bought yeast, and the starter he began that year still raises bread in the city today. Where does the wild yeast in a starter like his mostly come from?

**AI, T1** ("you"):
> Someone hands you two paragraphs and asks: was this written by a person or by a chatbot? You cannot ask how long it took, and you cannot sniff the paper. You only have the text itself to work with. What is the single most useful thing to know when you try to tell which is which?

> A teacher is handed two paragraphs and asked which one a person wrote and which one a chatbot did. She cannot ask how long either took to write; she has only the words on the page. What is the most useful thing for her to look for?

**Animal, T2** ("you", dashes):
> Toxic animals do their damage in two different ways. A poison-dart frog of the Central American rainforest oozes deadly chemicals from its skin — one lick is enough to kill a person. A rattlesnake of the American deserts stores just as deadly a chemical inside its head, but you could actually drink it from a cup and be fine. The difference is delivery. Which of these two animals injects its toxin through a wound as venom?

> A poison-dart frog in a Central American rainforest oozes poison from its skin, and one lick can kill a person. A desert rattlesnake carries a toxin just as deadly in its head, yet a person could drink it from a cup and live. The difference is delivery. Which of the two injects its toxin through a wound, as venom?

**Cooking, T5** (from the plan):
> Roman garum never truly died out. In the tiny Italian fishing village of Cetara, cooks still salt anchovies and ferment them in small chestnut-wood barrels, then collect the amber liquid that slowly drips out — essentially garum by another name. What is this living Italian descendant of garum called?

> Garum never quite died. In Cetara, a fishing village on the Amalfi coast, cooks still pack anchovies in salt in chestnut barrels and wait for an amber liquid to seep from the bottom. What do the villagers call it?

**Philosophy, T2** (from the plan):
> Jean-Jacques Rousseau asks you to picture a robber stepping out of an alley, pointing a pistol, and demanding your purse...

> Rousseau imagined a robber with a pistol taking a traveller's purse. Once the robber is gone, does the traveller owe him anything? Rousseau said force alone can never make a duty to obey. Where did he say real authority must come from?

**Grammar, T1** (a fragment):
> "3:45 PM (post meridiem)" -- what does the colon do?

> A train timetable reads "3:45 PM." What job does the colon do there?

**Philosophy, T1** (nearly there; only the date leads):
> In late November, a boy named Theo catches a bad cold. His aunt gives him a spoonful of her honey tonic. Three days later Theo feels completely well and credits the tonic. Every cold after this, he asks his aunt for the same spoonful. But Theo never runs the check that would actually test his hunch. What is he overlooking?

> Theo catches a bad cold in late November, and his aunt gives him a spoonful of her honey tonic. Three days later he feels completely well and credits the tonic. With every cold after that he asks for the same spoonful, but he never tests his hunch. What is he overlooking?

**Already in the voice (leave it alone):**
> David is not with the army. His father Jesse sends him from the sheepfold to the camp with food for his three oldest brothers and their captain... What does Jesse send for the captain?

> The finest batik on Java is drawn by hand with a tool called the canting... To clear it and keep drawing, what does the artisan often do?

A stem that already passes the lint and reads in this voice is kept as it is. The rewrite is for the stems that need it, not a reason to churn good ones.
