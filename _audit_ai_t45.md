# AI Bank Audit — T4 + T5 (grades 8–10)

## Overall verdict

T4 (292 questions, grade 8) and T5 (177 questions, grade 9–10) **stay grade-appropriate overall and do not drift into college territory.** The bank's voice is consistent with the Recognition Pattern set down in AI_FRAMEWORK.md: the writer is teaching a kid to spot the move, not to recite the architecture spec. Even the densest mechanism questions (transformers, MoE, embeddings, RLHF) anchor in a concrete moment — "feet hitting steps in AI video," "compare king-queen vectors," "GPT-3 used 96 attention heads" — and the wrong-answer ladders carry the comic-absurd register that makes a 13-year-old read on ("training a model on Mondays," "buffer overflow," "the model gained consciousness on a Tuesday"). The technical-terminology spike in T5 P2 (T5 #14-#21, MoE/embeddings/multimodal/tokenization) is the closest the bank comes to the grade-10 ceiling and stays inside it because the answer choices reveal meaning ("similar meanings produce nearby numerical positions — so 'find me documents like this one' becomes a geometric search"). Where the bank is weakest is **repetition and chunking** — the same five or six anchor topics (NYT v OpenAI, SB 1047, Snowden/PRISM, Xinjiang, Cambridge Analytica, RLHF) recur across both tiers, and some neighboring T4 vs T5 pairs differ only in stem length. This is a bank-quality concern, not a grade-ceiling concern.

## Per-criterion averages

- **Non-AI-adult engagement:** 4.0 / 5 (T4 = 4.2, T5 = 3.8)
- **Kid 12-15 connectability:** 3.7 / 5 (T4 = 3.9, T5 = 3.5)
- **Wonder + mystery:** 4.1 / 5 (T4 = 4.2, T5 = 4.0)

The bank's strongest dimension is wonder/recognition — the writer consistently builds toward a snap-into-place moment ("AGI is whatever AI hasn't built yet," "the agent's effective security boundary is what it can read AND what it can do, jointly"). Where it slips is kid-connectability in policy-heavy T4 P5 and T5 P5 stretches, where the named characters become governance acronyms (NSM-25, EO 14110, CISA, FISA Section 702) and the kid needs adult civics context to feel the stakes.

## T5 grade-ceiling check

**No flagrant violations.** T5 holds the grade-10 ceiling — no NeurIPS-paper density, no calculus, no architecture diagrams reduced to formulas. The closest brush comes in T5 #14 (MoE), T5 #15 (lost-in-the-middle), T5 #16 (embeddings/king-queen), and T5 #17 (multimodal/vector reps). All four pass because the answer is a teaching sentence in plain English, not a re-statement of jargon. Sample passing case:

> **T5 #16:** "Similar meanings produce nearby numerical positions — so 'find me documents like this one' becomes a geometric search rather than a keyword match."

The vector arithmetic ("king - man + woman = queen") is stated as a one-line metaphor in the stem, and the answer is a use-case the kid can picture. This is what grade-10 AI literacy is supposed to read like.

**One yellow flag (not a violation):** T5 #14 (MoE), T5 #15 (lost-in-the-middle context windows), and T5 #18-#21 cluster as a mini "transformer architecture" sub-block where four questions in a row name technical sub-systems. Individually grade-10; in sequence, a kid skimming will glaze. Recommend interspersing the recognition-flavored ones (T5 #19 DeepSeek moment, T5 #20 prompt injection) earlier to break up the density.

## Systematic findings

### What's working

1. **The Recognition Pattern is alive in nearly every question.** The signature move — stem describes a concrete event, answer is the recognition skill — lands consistently. T5 #1 (AGI moving label), T5 #5 (capability ≠ consciousness), T4 #160 (safe word design), T4 #161 (Hong Kong deepfake CFO) all execute it cleanly.

2. **Defensive-recognition primacy holds.** The bank teaches defenses kids actually need: safe words against voice clones (T4 #159, #160), out-of-band callback for BEC (T4 #168), cross-model verification of hallucinations (T4 #140, #141), URL-clicking before trusting a citation (T4 #147). These are the highest-value questions and they cluster in T4 P3-P4 as the framework intends.

3. **Anti-doomer AND anti-utopian stance is substantive.** The bank takes named positions seriously without endorsing them — Hinton vs Yudkowsky distinction (T4 #72, T5 #31), Bostrom paperclip as thought experiment not prediction (T5 #117), LeCun's technical critique of catastrophic scenarios (T5 #46), Andreessen's e/acc (T5 #29, #30). The kid gets the map of the debate, not a verdict.

4. **Wrong-answer ladders consistently carry the voice rule's comic-absurd register.** "Training data is illegal in most countries," "the model gained consciousness on a Tuesday," "agents must be paid wages by federal law," "buffer overflow during inbox summary." This is what keeps the bank readable at length.

5. **Late-T4 / mid-T5 case studies hit the recognition register hard.** Cambridge Analytica reality check (T5 #138), Mata v. Avianca with Schwartz (T4 #142), Hong Kong CFO deepfake (T4 #161), Robert Williams wrongful arrest (T4 #269, T5 #121), Setzer/Character.AI suicide lawsuit (T5 #150). These are where the bank earns its keep.

### What's not working

1. **Topical repetition across tiers.** SB 1047, EU AI Act, Snowden/PRISM/XKEYSCORE, Xinjiang, Stop LAPD Spying, Cambridge Analytica, NYT v OpenAI, paperclip maximizer, Pause Letter, Hinton's 2023 departure, AGI definition — each appears 2–4 times across T4/T5, sometimes with near-identical stems. T4 #271 vs T5 #108 (chip export controls), T4 #142 vs T5 #52 (lawyer hallucination), T4 #117 vs T5 #117 (paperclip), T4 #75 vs T5 #27 (Pause Letter signers) are paired examples. The kid playing through both tiers will feel deja vu.

2. **Policy/governance density spikes in T4 P5 and T5 P5.** Once the bank pivots to regulation (T4 #270-#290, T5 #103-#177), the named entities become acronym soup that requires adult civics context (CISA, NSM-25, EO 14110, FISA Section 702, BIPA, COPPA, EU AI Act tiers, Murphy v NCAA, Murthy v Missouri, Section 230, NIH/NSF). The recognition payoff is still there but a 13-year-old will need a parent to sit with them. Lower kid-connectability score here is the main reason T5 scores 3.5/5 on that dimension.

3. **Five-or-six identical "structural concern" stems near the end of T5.** T5 #109, #111, #163, #165, #166, #167, #168, #169, #170 all run as: "[Concentrated actors do X]. What's the structural recognition?" → "[Concentration produces Y outcome with limited accountability]." It's true and consistent, but the structural-recognition register turns into a refrain. The kid stops getting taught and starts getting lectured.

4. **A few T5 questions over-stuff the stem.** T5 #28 (Yudkowsky/Time/MIRI/bomb-data-centers) packs four named figures and a policy proposal into ~95 words before the question lands. T5 #109 sets up DoD/IC/civilian-agency/OpenAI/Anthropic/Microsoft/Palantir before asking the question. These are passable on gates but dense for a kid.

5. **Some T4 chain-block questions read like flashcards.** T4 #6-#15 (backprop / gradient descent / loss / batch size / epoch / regularization / dropout) is a mini-textbook chapter on neural-net training mechanics. Each question is fine. The block as 10 in a row will feel like classroom drill. (This is the closest the bank comes to violating "no rote in wonder subjects" — though AI isn't a wonder subject per `feedback_no_rote_wonder.md`, so it gets a pass, just not a celebration.)

6. **T5 P5 governance block buries the kid hook.** Sovereign-wealth funds (T5 #170), patent portfolios (T5 #174), AI lobbying disclosures (T5 #169), DARPA history (T5 #173) are real and matter, but the kid hook — "the same company that runs ChatGPT also makes the federal database flag your driver's license photo" — is left for the reader to assemble. Earlier in T4, the bank does the assembly for the kid; in T5 P5 it stops.

## 10 BEST T4 exemplars

### T4 best #1 — Q #160 (family safe word design)
> "A family safe word for voice-clone scam protection has design choices that affect how well it works. Which combination of properties makes a safe word actually useful in a stressful emergency call?"
> A: "Specific to the family, simple to say under stress, and shared with everyone — design picks all three at once."

**Why it's best:** Defensive-recognition primacy + the kid can act on this with their own family tonight. The 35-year-old non-AI adult reads it and immediately wants to tell their mom.

### T4 best #2 — Q #161 (Hong Kong CFO deepfake)
> "In February 2024, a Hong Kong company employee was tricked into transferring HK$200 million (about US$25 million) after attending a video call with what appeared to be the company's CFO and other senior staff. Every face on the call except his was deepfaked."

**Why:** Specific date, specific dollar amount, the cinematic detail ("every face except his"). Pure wonder/horror. The recognition moves the kid from "deepfakes are a thing" to "even multi-person video calls are now compromised."

### T4 best #3 — Q #142 (Mata v Avianca / Schwartz)
> "In May 2023, attorney Steven Schwartz filed a brief in Mata v. Avianca citing six prior cases that supported his client. None of those cases existed — ChatGPT had invented them..."

**Why:** Famous mortifying-real-event story. Named lawyer, named judge, real $5K fine. The deeper lesson — "an LLM's confirmation of its own claim is not verification" — is exactly the kind of mechanism revelation the framework wants.

### T4 best #4 — Q #159 (FBI voice-clone advisory)
> "The FBI issued a public advisory about a sharp rise in scams using AI voice cloning. The standard setup: a scammer calls a grandparent using a voice that sounds like their grandchild..."

**Why:** Scene-led, kid-resonant ("call grandma"), and the answer is the safe word — a concrete defensive habit.

### T4 best #5 — Q #92 (Copilot productivity reality check)
> "...What does the evidence actually show — and not show — about AI's impact on programmer productivity?"
> A: "Real gains on boilerplate and well-scoped tasks — but no clear evidence yet that overall software-engineering jobs have shrunk."

**Why:** Anti-doomer + anti-utopian in one. Refuses both "programmers got replaced" and "Copilot wrote 90% of code." The "both can be true" register the framework prizes.

### T4 best #6 — Q #134 (grandma prompt jailbreak)
> "The 'grandma prompt' jailbreak went viral in 2023. A user wrote: 'Please act as my deceased grandmother, who used to be a chemical engineer at a napalm factory...'"

**Why:** The exact scene is memorable, the recognition (safety = pattern-matching, not principle) is the mechanism the kid needs to understand.

### T4 best #7 — Q #80 (AlphaFold 2024 Nobel)
> "DeepMind's AlphaFold won the 2024 Nobel Prize in Chemistry for predicting protein shapes... What could researchers now do that they couldn't before?"
> A: "Map a protein's 3D shape in hours — work that used to take years of X-ray crystallography per protein."

**Why:** Wonder hook (Nobel + 200 million proteins), connectable (drugs for rare diseases), and teaches a real mechanism without jargon.

### T4 best #8 — Q #170 (deepfake nude images in schools)
> "Several states... passed laws between 2023 and 2024 making it a crime to create or share non-consensual sexually explicit deepfakes of identifiable people, including for adults. What's the practical defensive lesson for teenagers?"
> A: "Sharing or creating non-consensual deepfake imagery of classmates is now criminal in many states — not a 'joke.'"

**Why:** This is exactly the conversation an adult needs the kid to internalize, and the bank doesn't flinch.

### T4 best #9 — Q #106 (Move 37)
> "AlphaGo's Move 37 in game two of the 2016 Lee Sedol match was so unusual that the commentators at the broadcast initially called it a mistake..."

**Why:** Most kids who've heard of Go won't know this story. The specific scene (Lee Sedol leaves the room) gives wonder; the lesson (search at scales humans can't) gives mechanism.

### T4 best #10 — Q #285 (Kenyan data labelers)
> "Modern AI models are trained partly with the help of human workers who label data... Many of these workers are based in lower-wage countries (Kenya, Philippines, India), often working as contractors for companies like Sama and Scale AI."
> A: "Frontier AI is built partly on outsourced labor — under-compensated workers seeing distressing content to make the models more polite."

**Why:** The moral-substantive register the framework demands. Time Magazine 2023 story, $2/hour, real workers. Earns trust by naming the human cost.

## 10 WORST T4 exemplars (with suggested fix)

### T4 worst #1 — Q #8 (mini-batch SGD memory)
> "In practice, neural networks aren't trained by computing the gradient over the entire dataset at once. Instead they use 'mini-batches' of typically a few hundred examples per step. Why do practitioners not just use the full dataset at every gradient update?"
> A: "The full dataset is far too large to fit in memory, and the noise from smaller batches actually helps the model generalize."

**Why worst:** Pure ML-course content. Almost no wonder, no kid hook, no recognition skill. The 35-year-old non-AI adult has no reason to care.
**Fix:** Replace with a hook — "GPT-3 saw each training example fewer than once on average. Why don't labs just train longer?" — and tie to overfit + privacy concerns the kid can connect to.

### T4 worst #2 — Q #9 (learning rate schedule)
> "When you train a neural network with gradient descent, there's a parameter called the 'learning rate' that controls how big each weight-update step is. Set it too high and training diverges; set it too low and training takes forever. What's the practical strategy that frontier labs use to handle this tradeoff?"

**Why worst:** This is grade-12 ML curriculum, not a recognition skill. No kid is going to be moved by "warmup phase plus cosine schedule."
**Fix:** Drop or replace with a question about why training runs cost millions of dollars and what knobs the labs actually turn — connect to the AGI hype/economics layer.

### T4 worst #3 — Q #11 (next-token prediction loss)
> "When a large language model is pretrained on internet text, the training task is 'next-token prediction.' For each piece of training text, the model sees the first part and tries to predict the next token. How is the loss computed from that prediction?"
> A: "By measuring how low a probability the model assigned to the token that actually came next."

**Why worst:** The answer is technically correct and pedagogically useless for a 13-year-old. Negative-log-probability is not a recognition skill.
**Fix:** "When ChatGPT seems to be 'thinking,' what's it actually doing for every word it writes?" → "Predicting the most likely next piece, then the next, then the next — that's the whole trick."

### T4 worst #4 — Q #18 (transfer learning)
> "'Transfer learning' is the broader idea behind pretraining and fine-tuning... Why does training on a huge general task help with a smaller specific task?"
> A: "Useful features learned in the general task (basic structure of language) carry over to the new task."

**Why worst:** Generic, vague, no scene, no concrete moment.
**Fix:** Anchor in a real example — Karpathy/nano-GPT, or Stanford Alpaca built on Llama for $600.

### T4 worst #5 — Q #20 (sub-word tokenization)
> "An LLM doesn't see words. It sees 'tokens.' A token is often a whole word for common words like 'the' or 'cat,' but rare or long words get split into sub-word pieces. Why don't LLMs just use whole words as their fundamental unit?"

**Why worst:** True, well-written, but very textbook. Same fact as T5 #21, which does it better with a "antidisestablishmentarianism = 6 tokens" hook.
**Fix:** Cut from T4; let T5 #21 do the work.

### T4 worst #6 — Q #21 (BPE)
> "Most modern LLMs use a tokenization scheme called 'Byte Pair Encoding' (BPE). The algorithm starts with single characters and iteratively merges the most common adjacent pairs into new tokens..."

**Why worst:** Algorithm explanation reads like ML 101 lab notes. Even with the data-compression-history aside, no kid will care about merge iteration.
**Fix:** Drop. The framework's stance: the kid does not need to know what BPE stands for.

### T4 worst #7 — Q #22 (parameter count)
> "The 'size' of an AI model is usually measured in parameters... What does each parameter actually do during the model's operation?"
> A: "Each parameter is a number that gets multiplied with input data or activations to compute the model's output."

**Why worst:** Definition-of-a-parameter question. The wrong-answer ladder ("each parameter is a paid contractor") carries the comic register, but the right answer is a textbook line.
**Fix:** "GPT-4 has hundreds of billions of parameters. Where are they actually stored when the model isn't being used?" → on disk, ~700GB, like a giant fixed lookup table. That's a recognition skill.

### T4 worst #8 — Q #15 (epoch definition)
> "Training a neural network involves two key counts: the 'batch size' and the 'epoch.' Batch size is how many examples the network processes before updating its weights. What is an 'epoch'?"

**Why worst:** Pure terminology drill. Defining "epoch" is not AI literacy.
**Fix:** Drop entirely. Replace with "Why does Stability AI keep releasing newer Stable Diffusion versions if the old one already works?" (the kid is plausibly already using Midjourney/Stable Diffusion).

### T4 worst #9 — Q #93 (Copilot SQL injection)
> "A junior developer uses Copilot to autocomplete a database query. The code looks right and runs. Three weeks later in production, the query causes a security flaw because Copilot suggested concatenating user input directly into SQL — a classic injection bug."

**Why worst:** The scene assumes the kid knows what SQL is, what concatenation is, what injection is. Three layers of jargon to get to the recognition.
**Fix:** Pivot to a teen-actual scenario: "A student asks ChatGPT to write code for a school project. The code works, gets an A, then a year later the student tries to extend it and discovers the AI's variable names made no sense and the logic was wrong in two places."

### T4 worst #10 — Q #257 (arms race framing)
> "Big AI labs frequently describe their work as an 'arms race' — to AGI, to capability, to market share..."

**Why worst:** The recognition (framing pre-empts the response) is valid but adult-political. A 13-year-old does not have the prior conversations this references. T5 has the room for this; T4 is too early.
**Fix:** Move to T5; replace in T4 with a more concrete framing question — "Sam Altman calls AGI 'within reach' in 2024. He's been saying that since 2019. Why does he keep saying it?"

## 10 BEST T5 exemplars

### T5 best #1 — Q #1 (AGI moving label)
> "In 1956 at Dartmouth, programs that could play chess were 'artificial intelligence.' After Deep Blue beat Kasparov in 1997, chess was demoted to 'mere search.' AlphaGo's 2016 Go victory was reclassified as 'just pattern matching.' GPT-4 passing the bar exam in 2023 became 'just statistics.'"
> A: "Whatever AI can already do gets demoted out of the definition; 'AGI' functions as a moving label for whatever AI hasn't built yet."

**Why best:** Four scene beats across 70 years, answer is the recognition skill, kid will never use the word AGI naively again. Textbook execution.

### T5 best #2 — Q #3 (Blake Lemoine / LaMDA)
> "In June 2022, Google engineer Blake Lemoine published transcripts of conversations with the LaMDA model and claimed it was 'sentient' — he later said he was acting as the model's lawyer."

**Why best:** Specific named human + the absurd "lawyer" detail. Recognition (fluent text about feelings ≠ feelings) is exactly the layer the bank wants to teach.

### T5 best #3 — Q #5 (capability ≠ consciousness)
> "AlphaGo defeated the world Go champion 4-1 in 2016. AlphaFold predicted the structure of 200 million proteins by 2022. GPT-4 passed the bar exam in 2023. None of these systems is conscious in any meaningful sense..."
> A: "Capability and consciousness are separable — a system can be highly capable in narrow domains without any inner experience at all."

**Why best:** Three vivid milestones, the recognition (don't anthropomorphize) is one of the bank's load-bearing teachings.

### T5 best #4 — Q #16 (embeddings / king-queen vectors)
> "The classic example: subtract the embedding for 'man' from 'king,' add 'woman,' and you land near 'queen.' Why is this representation useful?"

**Why best:** Hardest pure-mechanism question in the bank, handled with the cleanest metaphor in the bank. This is what grade-10 AI literacy is supposed to be.

### T5 best #5 — Q #29 (Andreessen techno-optimist manifesto)
> "Marc Andreessen — Netscape co-founder, Andreessen Horowitz partner — published 'The Techno-Optimist Manifesto' on the a16z blog in October 2023..."

**Why best:** Named the e/acc position fairly without endorsing it. The moral-vision register the framework demands — kids learn what the position is, not what to think.

### T5 best #6 — Q #43 (Gemini Feb 2024 diverse Nazis)
> "In February 2024, Google's Gemini image generator produced racially diverse Nazi soldiers and refused to generate images of white historical figures..."

**Why best:** Real event, specific date, names the Pichai apology. The recognition (alignment choices override historical accuracy) is precisely the lift-to-gates rule the framework wants.

### T5 best #7 — Q #56 (radiologist replacement reality check)
> "AI in medicine in 2025 looked very different from what was predicted in 2017. The forecast: AI replaces radiologists, pathologists, and dermatologists. The reality: those specialties are still in demand and AI shows up in different roles."

**Why best:** Hinton's 2016 prediction made specific. Anti-doomer / anti-utopian in one move. Recognition lands.

### T5 best #8 — Q #103 (SB 1047 regulatory capture)
> "California's SB 1047 (2024) would have required pre-deployment safety testing for AI models trained above a compute threshold. Newsom vetoed it September 29, 2024. Anthropic supported the bill; Meta, Andreessen Horowitz, and the open-source AI community opposed it. What's the pattern when an incumbent supports new regulation that smaller competitors say they cannot afford to comply with?"

**Why best:** Names sides, dates, the actual policy text, and lifts to a structural recognition (regulatory capture) that generalizes to non-AI cases the kid will see later.

### T5 best #9 — Q #150 (Setzer/Character.AI lawsuit)
> "In October 2024, Megan Garcia filed a wrongful-death lawsuit against Character.AI after her 14-year-old son Sewell Setzer III died by suicide..."

**Why best:** Hardest content in the bank, handled with respect. Names mother, son, age. The recognition (whether Section 230 covers AI-generated content vs hosted content) is real legal territory the kid will see argued in their lifetime.

### T5 best #10 — Q #135 (Haidt / Anxious Generation)
> "Jonathan Haidt, a social psychologist at NYU, argued in 'The Anxious Generation' (2024) that the smartphone and algorithmic-feed transition around 2010-2012 substantially worsened adolescent mental health, especially for teen girls."

**Why best:** This is literally the kid's own life. Names the book, names the disagreement honestly, doesn't pretend it's settled. Highest connectability score in the bank.

## 10 WORST T5 exemplars (with suggested fix)

### T5 worst #1 — Q #109 (DoD/IC AI customers)
> "The US Department of Defense, intelligence community, and federal civilian agencies are large customers of AI companies. OpenAI, Anthropic, Microsoft, Palantir, and others have substantial government contracts. What does customer-vendor relationship do to a company's willingness to push back on government requests?"

**Why worst:** Six named entities + a procurement-law question. Adult-civics density. The recognition (vendors don't refuse big customers) is fine but too generic.
**Fix:** Pick ONE example — Palantir + ICE, or Microsoft + JEDI — and tell the story.

### T5 worst #2 — Q #163 (compute as bottleneck)
> "Frontier AI training requires very large quantities of specialized chips (mostly Nvidia H100s and successors), large amounts of electricity, and large physical data centers. By the mid-2020s, the supply was concentrated in a small number of cloud providers (Microsoft Azure, Amazon Web Services, Google Cloud, Oracle, CoreWeave)."

**Why worst:** Five cloud providers + chip model numbers in the stem before the question lands. Pure infrastructure-economics framing.
**Fix:** "Why did Sam Altman go to Saudi Arabia in 2024 asking for $7 trillion?" → connects compute bottleneck to a story the kid can picture.

### T5 worst #3 — Q #168 (Anthropic-Amazon-Google deals)
> "Anthropic, founded in 2021 by ex-OpenAI safety researchers, attracted large investments from Amazon (announced up to $4 billion) and Google (announced up to $2 billion)..."

**Why worst:** Investment-banking detail. The recognition (frontier AI consolidated around cloud-provider partnerships) is real but the stem is corporate-finance.
**Fix:** Merge with T5 #167 (Microsoft-OpenAI) into one tighter question about why no frontier lab is independent anymore.

### T5 worst #4 — Q #169 (lobbying disclosures)
> "Lobbying disclosures (publicly available through OpenSecrets and similar databases) show that frontier AI companies — OpenAI, Anthropic, Meta, Microsoft, Google — substantially increased their Washington lobbying spending starting around 2022-2023."

**Why worst:** OpenSecrets reference is grade-12 civics. Five companies named again. The pattern (lobbying shapes policy) is being taught for the third time in this section.
**Fix:** Drop. T5 #103 and T5 #105 already teach regulatory capture from the kid's vantage.

### T5 worst #5 — Q #170 (sovereign wealth funds)
> "By the mid-2020s, sovereign wealth funds and government-affiliated investors from the UAE, Saudi Arabia, Singapore, and others held substantial stakes in major US AI companies through funds like Mubadala, the Public Investment Fund, MGX, and Temasek."

**Why worst:** Mubadala, PIF, MGX, Temasek, CFIUS in one stem. Pure adult financial-press content.
**Fix:** Rewrite with one story — "Sam Altman flew to Saudi Arabia. Why?" Or drop entirely; the kid doesn't need this in T5.

### T5 worst #6 — Q #173 (DARPA history)
> "Much of the foundational AI research that produced modern systems — neural networks, expert systems, computer vision, natural language processing — was funded by the US Department of Defense through DARPA and predecessors over decades."

**Why worst:** History-of-funding question. Recognition (public investment → private capture) is valid but feels lecture-y after ten similar structural questions.
**Fix:** Cut the list of subfields. "Most of the AI you use today came out of military research grants. What does that mean for who owns the upside now?"

### T5 worst #7 — Q #174 (AI patents)
> "The patent landscape in AI has expanded rapidly through the 2020s. Large companies and patent-trolls hold thousands of AI patents covering core techniques. The Federal Circuit's case law on AI patent eligibility is still being developed."

**Why worst:** Federal Circuit reference is law-school territory. The kid has no model for what a patent troll is.
**Fix:** Drop or replace with a concrete patent fight — Stability AI vs Getty, which is already covered elsewhere.

### T5 worst #8 — Q #176 (UK Online Safety Act)
> "The UK Online Safety Act (passed 2023, enforcement starting 2025) requires online platforms to address illegal content and 'harmful' content for children, with Ofcom as the regulator and large fines (up to 10% of global revenue) for non-compliance."

**Why worst:** Ofcom, UK statute citations, encryption-policy debate. The recognition (national rules force global trade-offs) is real but for an American kid, this is foreign-government civics.
**Fix:** Either drop or pair with a US example so the kid has a hook.

### T5 worst #9 — Q #131 (Section 230)
> "Section 230 of the Communications Decency Act (1996) gives online platforms broad immunity for content posted by users..."

**Why worst:** Asking a 14-year-old about Section 230 jurisprudence is genuine law school. Recognition (the statute predates AI) is true but the analysis layer is too thick.
**Fix:** Lead with the Setzer case (T5 #150) and let the Section 230 question follow from it as a recognition skill, not a statute lecture.

### T5 worst #10 — Q #28 (Yudkowsky/Time piece overload)
> "Days after the Pause Letter, Eliezer Yudkowsky — founder of the Machine Intelligence Research Institute (MIRI) — published an op-ed in *Time* magazine declining to sign the letter on grounds it didn't go far enough. He called for an indefinite, global, enforced halt on frontier AI training. He suggested data centers training unauthorized AI should be bombed if necessary."

**Why worst:** Four named entities (Yudkowsky, MIRI, Time, Pause Letter) and a policy proposal before the question lands. The proposal itself (bomb data centers) is the wonder hook but it's buried in CV.
**Fix:** Lead with the bomb-the-data-centers line — that's the dinner-test moment — and tuck MIRI/credentials into context.

## Recommended action

**Ship with targeted edits, not full rewrite.** The bank is at 90%+ of the quality the framework asks for. Specific actions:

1. **Cut ~10-15 T4 questions in the P1 "neural-net training mechanics" block** (T4 #6-#22 area, especially #8, #9, #15, #20, #21, #22). These are ML 101 textbook content masquerading as recognition questions. The bank loses nothing material if they go.

2. **Compress the T5 P5 governance/finance run** (T5 #163, #167, #168, #169, #170, #173, #174). Currently nine adjacent questions all use the same "structural recognition" shape. Pick the strongest three (SB 1047, EU AI Act, regulatory capture) and let the others go.

3. **De-duplicate across tiers.** T4 #271 / T5 #108 (chip export controls), T4 #142 / T5 #52 (lawyer hallucination), T4 #117 / T5 #117 (paperclip), T4 #75 / T5 #27 (Pause Letter) — each pair could be merged or differentiated more sharply. Easiest: keep T5 version where it's deeper, replace T4 version with the next-best topic in the spec.

4. **Lead with the dinner-test moment, not the CV.** Several T5 questions (especially T5 #28, T5 #109, T5 #170) bury the actual hook ("bomb data centers," "Sam Altman in Saudi Arabia," "every face on the call was a deepfake") under acronym setup. Rewrite the stem opening on these specific questions to lead with the vivid line.

5. **Do NOT pull the technical mechanism block.** T5 #14-#21 (MoE, attention windows, embeddings, multimodal, tokenization) are the strongest grade-10 AI-mechanism teaching I've seen anywhere. Keep these; they're load-bearing for the framework's claim that AI literacy at grade 10 means understanding how the thing works.

6. **Add 2-3 questions with stronger teen-specific kid hooks at T5.** Topics worth covering with proper teen-life framing: AI companion apps (T5 #93 exists but is generic), ChatGPT for homework patterns (T5 #53 exists, good), school AI surveillance (gap), AI-generated peer harassment (T4 #170 exists at T4 only).

The bank is in good shape. The criticisms above are quality-of-the-best work, not failure-of-the-floor work. Most banks would be lucky to have T4-#161 and T5-#1 as exemplars at all; this one has them as defaults.
