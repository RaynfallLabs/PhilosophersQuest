# AI Bank Audit — T1 + T2 (grades 5–6)

Scope: T1 = 214 questions, T2 = 227 questions, 441 total. Methodology: stratified read of all 441 stems + answers (random distractor inspection where called for), plus jargon/scene/named-drama density counts (160/227 T2 stems contain no scene/family/kid words by strict regex; 16 T2 stems contain a named jargon term, all defined in-context).

## Overall verdict

The T1+T2 band is **good enough to ship**, with one consistent weak axis. The bank's voice is genuinely accessible: a non-AI adult can read almost any question and understand what's being asked, jargon is reliably defined in-context (transformer, parameters, tokens, hallucination, open-weight all get glossed when they appear), and the bank threads three voices — definitional ("what does X mean"), scene-based ("a chatbot tells you a confident fact, what's the move"), and named-historical ("Hinton, Hassabis, Kasparov, Move 37, Schwartz the $5K lawyer") — which together keep the tier interesting. Defensive-recognition is the strongest pillar throughout: voice-clone scams, deepfake tells (hands, ears, garbled signage, em-dashes), Schwartz's hallucinated citations, "set a family safe word" all land. The weakness is corporate-governance content: T2 has ~17 questions about CEO firings, board drama, restructurings, capped-profit structures, Snowden's XKeyscore, the Disinformation Governance Board, the Twitter Files, China's 2017 National Intelligence Law, and Productivity Score — most of which presume the reader thinks "boards fire CEOs" is interesting, when a 12-year-old's hook on the OpenAI saga is "the company fired its leader and the workers revolted and he was back in 5 days" — and the bank does sometimes capture that drama, just not consistently. Ship as-is for T1, tighten ~12 T2 corporate-context questions before T2 is at the same level.

## Per-criterion averages

- **Non-AI-adult engagement:** 4.4 / 5 (T1 = 4.6, T2 = 4.2)
- **Kid 12–15 connectability:** 3.9 / 5 (T1 = 4.2, T2 = 3.6)
- **Wonder + mystery:** 3.7 / 5 (T1 = 3.6, T2 = 3.8)

T1 is meaningfully stronger on connectability (kid-world scenes: TikTok, phone calls from "grandma," math homework, school essays, voice clones of "your cousin"). T2 climbs on wonder (more named figures, more specific dates, more story-shape) but slips on connectability (boards, lawsuits, governance bodies, FTX collapse, Snowden — content for an adult who reads the news).

## Systematic findings

### What's working

1. **Jargon-in-context discipline is real.** Out of 16 T2 stems containing a named technical term (transformer, parameter, token, context window, backpropagation, open-weight, neural network), every single one defines the term in the same sentence or the immediate setup. T2 #14 picturing "175 billion marbles" as a swimming pool of parameters, T2 #16 calling the context window "a sliding window over your conversation," T2 #36 calling backprop "nudges each weight in a helpful direction" — these are the gold-standard moves. No T1 stem assumes a term the reader hasn't been handed.

2. **Defensive-recognition pillar is the bank's beating heart.** Voice-clone safe-word questions (T1 #36, #128, #147, #159, #165, #175; T2 #122, #123, #162) repeatedly hook into "your cousin calls crying for money — what do you do" — concrete, dramatic, kid-relevant, and tells the kid a real defense. Deepfake tells (hands, finger counts, garbled signage, em-dashes, "delve into," ear asymmetry, blinking patterns) are taught as recognition skills with the AI's actual failure modes named. This is the bank doing its job: teaching the kid to recognize fake content.

3. **Named figures arrive with story-shape, not labels.** Hassabis appears as "co-founder of DeepMind AND chess prodigy AND video-game designer AND 2024 Nobel-Chemistry winner" rather than a dropped name (T2 #62, #63). Hinton appears as "left Google in 2023 AND won 2024 Nobel in Physics AND said 'AI will replace radiologists in 5 years' a decade ago" (T1 #59, #123, T2 #73–75). Kasparov "complained IBM had human help, IBM denied" (T2 #41). Ken Jennings's famous Simpsons-quoting concession (T2 #43) is in the bank, which is delightful.

4. **The Schwartz $5K lawyer arc is taught three different ways.** T1 #136 sets up the event ("six fake citations"), T1 #148 nails the fine amount, T1 #163 lifts the lesson ("verify AI citations before using them"), T2 #126 + #150 + #163 + #150 reinforce the move. This is well-orchestrated: kid encounters the same dramatic event from four angles across both tiers.

5. **Wonder shows up in unexpected places.** T1 #71 (ELIZA, 1966 MIT therapist chatbot — Joseph Weizenbaum named), T2 #98 (pre-AlphaFold proteins took months/years per protein via X-ray crystallography — a real "huh, that's interesting" reveal), T2 #43 (Ken Jennings: "I, for one, welcome our new computer overlords" — quoting the Simpsons), T2 #57 (Sedol's retirement "top players could no longer be 'the best'") all land with story-shape.

### What's not working

1. **The corporate-governance cluster is voice-mismatched.** About 12 T2 questions presume the reader is interested in board dynamics, restructuring, governance, productivity scoring, lawsuits, agency operations — content for a Wall Street Journal reader, not a 12–15-year-old. T2 #71 ("Can a non-profit board with safety oversight actually govern…") asks the kid to care about a structural-governance question they have zero stake in. T2 #190 ("OpenAI was founded as one kind of organization and is being restructured into another. What's the shift?") is a stem-aspect-mismatch failure: there's drama in the Altman firing, but the question is about org-chart redesign. T2 #200 (Microsoft Productivity Score "drew criticism") — a kid doesn't have a workplace.

2. **Some T2 distractors break the "could be plausibly true" bar by reaching for absurd.** Multiple T2 questions pair a correct answer with three obviously-absurd distractors: T2 #14 ("a tea cup," "a thimble," "the volume of an entire small country" — the right answer "a small swimming pool" is the only one that could be true). T2 #93 ("Doctors print copies of proteins at home"). T2 #114 "the exact mood of each individual corn plant." T2 #178 "platform reads your mind through the camera." This is fine for T1 (it teaches the right answer fast) but at T2 it makes the question too easy — the kid wins by spotting the silly, not by understanding the concept.

3. **Dry definitional T1 questions stack early.** T1 #1–#16 are nearly all "what's the short name for X" — LLM, transformer, parameters, training, generative, tokens, context window, neural network. A kid hitting this run learns vocabulary but doesn't see wonder until T1 #36 or so. The fix is interleaving, not removal — scatter ELIZA, the Schwartz lawyer, voice-clone scenes earlier and bury the "what's it called" questions deeper.

4. **A few T2 questions ask the kid to evaluate ideology rather than recognize patterns.** T2 #186 ("misinformation labels can in practice silence views that later prove valid") and T2 #226 ("how much government influence shapes platform decisions") are framed as opinions the kid is supposed to hold; the surrounding distractors are absurd ("Twitter ran by volunteers"), which means the question is effectively undefeatable but only because the alternatives are silly. This is OK content for a bank with the project's moral-vision posture, but it would be stronger if the choices were competing serious framings rather than absurd straws.

5. **Some T1 questions could give the kid a real fact instead of an absurd negative-multiple-choice.** T1 #40 ("which is NOT a real chatbot — ChatBuddy-X9") and T1 #41 ("which is NOT a real image generator — PixelMaster-Z") are fill-in-the-fake questions that don't teach the kid anything they didn't know. Better to ask "ChatGPT is from OpenAI; Claude is from Anthropic; Gemini is from ___" — pure positive identification.

## 10 BEST exemplars (combined T1+T2)

**T1 #110**
> Q: AlphaGo's famous moment was 'Move 37' in a 2016 game against Lee Sedol. Why is the move so often remembered?
> A: It surprised top human players

Wonder + named figure + specific event + the answer is the actual reason (not a label). This is the bank's "Move 37" question and it's properly held back as the answer to a "why is this remembered" question, not buried in a definition.

**T1 #36**
> Q: Voice clones can sound exactly like a real person from just seconds of recorded audio. What habit best protects your family?
> A: Set a family safe word in advance

Defensive recognition, kid-family hook, dramatic threat, actionable answer. This is the template the bank should hit on every recognition pillar.

**T1 #148**
> Q: The 2023 New York lawyer who cited fake court cases from ChatGPT was fined how much?
> A: About 5,000 dollars

Specific number + named event + the drama is the number itself ($5K is small enough to surprise but real enough to remember). Wonder Pattern adapted for AI.

**T1 #71**
> Q: An early chatbot built at MIT in 1966 by Joseph Weizenbaum used simple pattern-matching to imitate a therapist. What was it called?
> A: ELIZA

Named first chatbot, named creator, specific year, specific institution, specific behavior (imitating a therapist). All the wonder pillars in one stem.

**T2 #43**
> Q: Ken Jennings, the human champion Watson defeated, wrote a famously gracious sentence at the end of his final answer. What did he write?
> A: 'I, for one, welcome our new computer overlords.' — quoting an old Simpsons episode

The answer is a memorable cultural reference that lands. This is the bank teaching wonder by handing the kid a quotable line.

**T2 #63**
> Q: Demis Hassabis had an unusual background before AI. What was he widely known for in his teens?
> A: Being a chess prodigy and later a designer of video games

Named figure + counterintuitive backstory (chess prodigy → video games → AI lab → Nobel). This is the "named things > generic labels" rule done correctly.

**T2 #98**
> Q: Before AlphaFold, how did scientists usually figure out the 3D shape of a protein?
> A: By growing crystals of the protein and firing X-rays at them, often taking months or years per protein

The answer itself is the wonder. "Growing crystals and firing X-rays" is so vivid that the kid retains both the old method and (by contrast) why AlphaFold mattered.

**T2 #122**
> Q: A scammer calls your house in your mother's exact voice, saying she's in trouble and needs money sent right now. What's the family's best defense set up ahead of time?
> A: A family safe word that real Mom would know but a voice clone would not

Concrete scene, concrete threat, concrete defense, family hook. T2-grade complexity but the kid-stake is preserved from T1.

**T2 #16**
> Q: Picture a chatbot's context window as a sliding window over your conversation. What slips out of view as the chat grows longer?
> A: The oldest messages — they leave the window first as new ones come in at the other end

Definitional, but with a concrete visual metaphor (sliding window over conversation). Teaches the term and the mechanism in one sentence.

**T2 #41**
> Q: Garry Kasparov reacted strongly to the 1997 loss. What was his recurring complaint about the match?
> A: He suspected IBM had received human help during games, which IBM denied

Wonder + drama + the answer hands the kid a feud they didn't know about. Specific year, specific complaint, specific denial. Kid retells this at dinner.

## 10 WORST exemplars (combined T1+T2)

**T1 #40**
> Q: Out of these four chatbot names, which one is NOT actually real?
> A: ChatBuddy-X9 from a friendly lab

Spot-the-fake-name question teaches nothing. The kid wins by recognizing fakeness, not knowledge. **Fix:** Replace with "OpenAI makes ChatGPT. Anthropic makes Claude. Google makes ___" — positive identification.

**T1 #67**
> Q: The 2012 ImageNet-winning network from Hinton's team is sometimes named after a grad student on the team. What's the network called?
> A: AlexNet

This is fine information but the wonder is missing. The interesting fact is "named after Alex Krizhevsky," not "the network is called AlexNet." **Fix:** "The 2012 ImageNet winner ushered in deep learning. The network was named after which member of Hinton's team?" — Answer: "Alex Krizhevsky." Move the wonder into the answer.

**T1 #61**
> Q: Yann LeCun is the Chief AI Scientist at which company?
> A: Meta

Pure rote attribution. No story, no scene, no wonder. This is the kind of question the project memory says is banned in wonder subjects but AI may exempt — except even here, LeCun has a story (CNN inventor, pushes back on AI doom). **Fix:** "Yann LeCun is famous for pushing back publicly against AI-doomer scenarios. He's the Chief AI Scientist at which company?" — keeps the same answer, adds his identity.

**T1 #74**
> Q: OpenAI was originally founded as a non-profit research lab in which year?
> A: 2015

Bare date question. No drama, no scene. The kid memorizes 2015 with no anchor. **Fix:** Pair with the actual interesting fact — "OpenAI was founded as a non-profit by Sam Altman, Elon Musk, and others in which year?" — kid retains the founders' names AND the year.

**T2 #5**
> Q: An LLM is called 'large' for one specific reason — not because of the company that built it. What is that reason?
> A: The model has a huge number of internal numbers (parameters) and is trained on a huge amount of text

The answer is dry-textbook. The question is sound but the answer choice should hint at the wonder of "billions of parameters." **Fix:** "The model has billions of internal numbers (parameters) and is trained on trillions of words." Same content, the numbers do the work.

**T2 #71**
> Q: The November 2023 OpenAI board drama raised a deeper question that watchers couldn't help asking. Which question?
> A: Can a non-profit board with safety oversight actually govern the people building powerful AI?

Stem-aspect mismatch: kid sees "OpenAI board drama" (juicy) and the question asks them to care about non-profit governance theory (not juicy). **Fix:** Rewrite to keep the drama — "When the OpenAI board fired Altman in November 2023, what did most employees do?" Answer: "About 700 of them threatened to quit and follow him to Microsoft." Real drama, real number, real stakes.

**T2 #190**
> Q: OpenAI was originally founded as one kind of organization and is being restructured into another. What's the shift?
> A: Founded as a non-profit research lab; later restructured toward for-profit

This is corporate-restructuring trivia. A 12-year-old has no foothold. **Fix:** Either drop or rewrite — "OpenAI was founded as a non-profit in 2015 with Elon Musk among the funders. Musk later split from the company. Why?" — disagreement story, named figure, real conflict.

**T2 #196**
> Q: In 2013, Edward Snowden's leaks revealed an NSA system that could search internet activity at huge scale. What was it called?
> A: XKeyscore

A 12-year-old in 2026 wasn't alive in 2013. Snowden is genuine adult-recognition content. **Fix:** Either reframe with kid stake ("government search system that could read anyone's emails") OR drop and replace with something contemporary (e.g., the 2024 NetChoice / school monitoring drama).

**T2 #200**
> Q: Microsoft introduced a 'Productivity Score' feature for businesses some years ago. Why did it draw criticism?
> A: It scored individual employees in ways that felt like surveillance

Workplace-surveillance content for someone without a workplace. **Fix:** Pivot to school surveillance — "Some US schools use software like Gaggle to scan student writing. Why have these tools drawn criticism?" Answer: "False alarms about innocent text plus chilling effect on student speech." Same lesson, kid's actual world.

**T2 #221**
> Q: What's the simplest reason a major fraud's collapse should make people re-examine the causes it funded?
> A: Funding shapes which voices get heard, and major funding by a fraudster bent the conversation

Abstract policy-philosophy question. The kid sees no concrete event in the stem (the FTX/SBF setup is only in T2 #208, not anchored here). **Fix:** Anchor explicitly — "In 2022, FTX collapsed and its founder Sam Bankman-Fried was later convicted. Bankman-Fried had been the largest funder of AI-safety research. What did the collapse force in that field?" — names, year, conviction, concrete consequence.

## Recommended action

**Ship T1 as-is** (or after a 5-question cosmetic tweak — see T1 #40, #41, #61, #67, #74 in the worst list). The tier is 4.2 / 5 on connectability and 3.6 / 5 on wonder, with disciplined jargon and strong defensive-recognition coverage. A kid will engage.

**Minor rewrite of ~12 T2 questions** before T2 is at the same level: the corporate-governance cluster (board drama framed as governance theory rather than as drama, restructurings asked as org-chart questions, productivity scoring without a workplace stake, Snowden trivia from before the kid was born). Roughly:

- T2 #71, #189, #190 — keep Altman drama, reframe to employees/stakes rather than board theory
- T2 #196 — replace XKeyscore with a contemporary surveillance event
- T2 #200 — pivot from workplace Productivity Score to school monitoring (Gaggle/GoGuardian)
- T2 #221 — anchor the FTX claim with names + numbers + conviction
- T2 #185 (Twitter Files) and T2 #226 (Twitter Files redux) — currently abstract; either drop one or anchor in a specific Musk/Taibbi document drop
- T2 #192 (Disinformation Governance Board) — depends on whether the bank wants this contemporary-politics content; if yes, anchor with the actual fired official (Nina Jankowicz)

This is ~5% of T2 — not a major rewrite, more a "tighten the corporate cluster" pass. The rest of T2 is strong.
