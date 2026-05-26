# AI Bank Audit — T3 (grade 7)

## Overall verdict

The T3 AI bank (315 questions) is strong by all three criteria — confidently the best-tuned wonder/recognition tier in the bank. Voice is consistent: every mechanism question is teed up with a concrete scenario or in-stem definition; jargon (RLHF, embedding, transformer, fine-tuning, context window, BERT) is never used without being unpacked in the same stem; and named-figure / dated-event questions (AlexNet 2012, ELIZA 1966, AlphaGo Move 37, Lee Sedol's retirement, OpenAI's Nov 2023 board firing, Hinton's Google departure, Sora 2024, Robert Williams arrest, NH 2024 Biden robocall, AlphaFold's 2024 Nobel) carry the wonder-load exactly as the AI_FRAMEWORK Recognition Pattern prescribes. About 74% of stems are scenario-led ("A friend asks ChatGPT...", "Imagine telling an AI agent..."); the remaining 26% are still well-scaffolded definition stems that include a concrete example inline. The weakest stretch is the privacy / hygiene / scam-defense block (T3[200]–[240]-ish): these are useful but read more like a digital-citizenship checklist than recognition-pattern wonder. A defensible ship; ~12 specific improvements queued below.

## Per-criterion averages
- Non-AI-adult engagement: **4.6 / 5**
- Kid 12-15 connectability: **4.5 / 5**
- Wonder + mystery: **4.2 / 5**

## Systematic findings

### What's working

- **In-stem jargon teaching is universal and well-executed.** Every transformer/embedding/RLHF/fine-tuning question defines the term inside the stem (often with a concrete example: "The word 'unbelievable' might be split into 'un,' 'believ,' and 'able'"). A 35-year-old non-user can read any T3 question cold and follow it. The classic Winograd sentence ("The trophy didn't fit in the suitcase because it was too big") is used to teach self-attention — this is exemplary.
- **Named-figure clustering pulls heavy wonder weight.** Hinton (5 stems), AlphaGo (10), LeCun (4), Hassabis (4), Sutskever (3), Altman (5), ELIZA/Weizenbaum (4+3), AlexNet team (5), Lee Sedol (5). The grandmaster-retiring-because-AI-exists question (T3[78]) and the Hassabis-chess-prodigy question (T3[95]) are the best of the bunch. The Nov 2023 OpenAI board firing gets four well-coordinated stems (T3[106]–[109]).
- **The "defensive recognition" voice lands hard.** "Liar's dividend" (T3[300]), the Mata v. Avianca lawyer (T3[186]), the Hong Kong $25M deepfake CFO call (T3[182]), the Robert Williams wrongful arrest (T3[219] + T3[260] + T3[291]), and the NH Biden robocall (T3[311]) are all anchored to specific dramatic incidents — kids can retell them. This is the Recognition Pattern doing its job.
- **Multi-stem deep dives on Move 37 + ELIZA + AlexNet.** Three of the canonical "huh that's cool" AI moments get 3–5 stems each from different angles — mechanism, drama, aftermath, cultural impact. Spaced repetition built in.
- **Substantive on contested topics, as required by the framework.** Gemini Feb 2024 (T3[265], [266]), Twitter Files / FBI flagging (T3[262]), COVID lab-leak labeling (T3[263]), Disinformation Governance Board (T3[264]), Rozado's left-of-center finding on LLMs (T3[294]), DEI-as-political-vector (T3[293]). These are handled with attribution + specifics, not editorializing.
- **Distractors are crafted, not lazy.** Almost no obviously-silly distractors; most include plausible-sounding alternatives that test whether the reader is actually following.

### What's not working

- **The privacy/hygiene/scam-defense run (~T3[200]–[240], T3[300]–[314]) is dutiful but flat on wonder.** Questions on password managers, 2FA, VPN trade-offs, ad-tracker IDs, advertising identifiers, location permissions, dark patterns — these are correct and useful, but they read like a CompTIA Security+ chapter rather than something a kid retells. Compare T3[229] "2FA methods, which is more secure?" against T3[182] "Hong Kong deepfake CFO video call, $25M transfer, why did the attack succeed?" Both are recognition skills; only the second one makes a kid lean forward.
- **A small chunk of "general knowledge AI" stems lack a specific hook.** T3[55] (what parameters do), T3[58] (scaling laws), T3[59] (chain-of-thought) read as textbook definitions. They define the term, but they don't earn the question with drama. Kids will answer them by elimination, not by "I remember this."
- **The "AGI is N years away" loop is repeated.** T3[40] (moving the goalposts), T3[41] (how to respond to "AGI in 5 years"), T3[42] (AGI definition problem), T3[69] (Simon's 1958 prediction), T3[296] (arms-race framing) all run the same lesson: take big-promise AI timelines with skepticism. The lesson is true; five stems of it is a lot.
- **CONFIRMED BUG: at least 6 T3 questions have mid-word truncation in their answer/choice text in the actual JSON.** All six come in at exactly 670 chars total — looks like a char-budget gate cut them off rather than rejecting the question. Examples:
  - T3[128] answer: "...knowing the shape lets researchers design dru"
  - T3[130] answer: "...it doesn't simulate the chemistry of fol"
  - T3[138] answer: "...then noise becomes a crea"
  - T3[143] answer: "...the AI catches the " (ends with a trailing space)
  - T3[150] answer: "...lets farmers (and others) see things at fie"
  - T3[154] choice 2 (a distractor): "...immune to all rear-end collisions for the full duration of th"
  These should be the priority fix before ship — they fail the bank on basic correctness, not voice. Either raise the cap for these questions or rewrite the affected fields to fit.
- **The phrase "recognition skill" appears in roughly half the contexts.** This is fine for the bank's pedagogical voice — it IS the controlling pattern — but a few stems lean on the phrase itself when the question would be more vivid without the meta-framing.

## 10 BEST T3 exemplars

1. **T3[78] — Lee Sedol's retirement**
   - Q: "Lee Sedol — the human grandmaster who played AlphaGo in 2016 — retired from professional Go in 2019. He named one specific reason. What did he give as the reason?"
   - A: "He felt no longer at the top because AI had surpassed humans, and even being the world's best wasn't 'best' anymore."
   - Why it wins: Specific named human, specific year, specific quote-able reason. Drama is in the stem; the answer is the most memorable specific fact. A kid will retell this at dinner.

2. **T3[77] — Move 37 (the legendary one)**
   - Q: "In game two of the 2016 AlphaGo vs. Lee Sedol match, AlphaGo played move 37 — a shoulder hit on the fifth line. The professional commentators initially called it a mistake. Why is move 37 now legendary in Go history?"
   - A: "It was a creative move no human had considered, and AlphaGo went on to win the game."
   - Why it wins: A single canonical move, named "Move 37" — exactly the kind of named thing the AI_FRAMEWORK hierarchy puts at the top.

3. **T3[182] — The Hong Kong $25M deepfake CFO call**
   - Q: "A 2024 Hong Kong case made headlines: scammers used deepfake video of a company's CFO in a video call to authorize a $25 million transfer. Every face on the call except one was a fake. Why did this attack succeed despite multiple people being 'present'?"
   - A: "Seeing many familiar faces felt like proof, but every face except the victim was AI."
   - Why it wins: Specific case, specific dollar number, the "every face except the victim was AI" sentence is unforgettable. Recognition Pattern doing exactly what it's supposed to.

4. **T3[60] — Weizenbaum's secretary**
   - Q: "In 1966, an MIT computer scientist named Joseph Weizenbaum built a simple chat program called ELIZA. Its most famous mode imitated a Rogerian psychotherapist — reflecting users' statements back as questions. Why was Weizenbaum himself disturbed by his own creation?"
   - A: "Users, including his secretary, formed real emotional attachments to ELIZA despite knowing it was a simple program."
   - Why it wins: 60-year-old story is more vivid than half the 2023 content. Named person, named year, specific dramatic detail (his own secretary).

5. **T3[186] — Steven Schwartz's "I checked with ChatGPT" defense**
   - Q: "Steven Schwartz, the NY attorney who got sanctioned in 2023 for filing a brief with six ChatGPT-fabricated court cases, claimed he didn't know AI could hallucinate. He even asked ChatGPT to confirm the cases were real, and ChatGPT confirmed they were. Why is this 'I checked' defense not actually a defense?"
   - A: "The model that fabricated the cases also fabricates confirmation, asking it to verify itself doesn't work."
   - Why it wins: Named human, dated event, dramatic stakes (lawyer sanctioned), and the punchline is a permanent piece of mental furniture for a kid.

6. **T3[106] — OpenAI board fires Altman, undone in 5 days**
   - Q: "On November 17, 2023, OpenAI's board fired CEO Sam Altman. Within five days he was back in his old role. What does the five-day timeline tell us about the company's governance structure?"
   - A: "Whatever formal power the board had on paper, the actual power was held by the people building the technology, and those people wanted Altman back."
   - Why it wins: Famous dated event, specific governance lesson kids can extract.

7. **T3[100] — The 10-point AlexNet leap**
   - Q: "AlexNet's 2012 ImageNet error rate was about 16% (top-5). The previous year's winner — using traditional computer-vision techniques — had been around 26%. Why was the 10-point gap considered so striking?"
   - A: "In benchmark competitions, single-percent gains had been the norm, so a 10-point leap meant a different approach had just won."
   - Why it wins: Numbers + named system + the structural payoff that "everything reorganized within 5 years."

8. **T3[219] — Robert Williams wrongful arrest**
   - Q: "Face-recognition databases now exist at police departments, retailers, sports venues, and apartment buildings. The Robert Williams case (Detroit, 2020) became famous — what happened?"
   - A: "Williams was wrongly arrested after a face-recognition match identified him as a thief he wasn't."
   - Why it wins: Real named person, real year, real concrete harm. Defensive recognition, top of the hierarchy.

9. **T3[95] — Hassabis was a chess prodigy and video-game designer**
   - Q: "Demis Hassabis co-founded DeepMind in London in 2010. Before becoming an AI-research leader, he had two earlier careers. What were they?"
   - A: "Chess prodigy and video-game designer — he competed at chess, then made games before getting his PhD in neuroscience."
   - Why it wins: The two earlier careers are exactly the kind of "wait, really?" hook the framework wants. The distractors (concert pianist + surgeon, Olympic swimmer + architect) are also crafted to be plausible-fun, not lazy.

10. **T3[311] — NH 2024 Biden robocall**
    - Q: "AI voice cloning has been used in political scams — including a 2024 robocall during the New Hampshire primary that imitated President Biden's voice urging people not to vote. What does the case illustrate?"
    - A: "AI voice tools are cheap and easy to misuse — defense requires verification, not detection alone."
    - Why it wins: Headline news, named figure, named state, named primary, named year. The kid has heard of all of this.

## 10 WORST T3 exemplars

1. **T3[229] — 2FA: SMS vs. authenticator**
   - Q: "Two-factor authentication (2FA) adds a second check — beyond your password — when logging in. The two common methods are SMS codes and authenticator apps. Which is significantly more secure?"
   - A: "Authenticator apps, SMS can be hijacked via SIM-swap attacks."
   - Problem: True and useful, but reads like a checklist. No named incident, no dramatic anchor.
   - Fix: Anchor to a real SIM-swap case (the Jack Dorsey Twitter SIM-swap, August 2019, gave the attackers his @jack account for 30+ minutes). "SIM-swap attacks have hit named people including Twitter CEO Jack Dorsey in 2019 — what's the defense?"

2. **T3[230] — YubiKey question**
   - Q: "Hardware security keys (YubiKey, Google Titan) are the strongest form of two-factor authentication for most people. They use a physical USB or NFC device that has to be present to log in. What's the additional security benefit beyond authenticator apps?"
   - A: "Phishing-resistant, a hardware key won't authenticate to a fake login page."
   - Problem: Same as above — true, useful, dry.
   - Fix: Anchor to Google's 2017 internal rollout where they reportedly eliminated employee phishing entirely after deploying hardware keys to 85,000 employees.

3. **T3[224] — What a VPN does**
   - Q: "A VPN (Virtual Private Network) encrypts your internet traffic between your device and the VPN provider, then sends it on from the provider's server. What does a VPN do well, and what doesn't it do?"
   - A: "Hides traffic from your local network and ISP; doesn't hide it from the VPN provider or destination sites."
   - Problem: Definition + definition.
   - Fix: Anchor to a sponsored-YouTuber-pitch — every kid has seen one. "Every YouTube tech-influencer has a NordVPN sponsorship. The pitch is 'your data is private.' What does the VPN actually hide, and from whom?"

4. **T3[58] — Scaling laws**
   - Q: "Modern AI labs talk about 'scaling laws' — empirical patterns that predict how model performance improves with more data, more parameters, and more compute. Why are these laws important to how the field operates today?"
   - A: "They let labs predict roughly what a bigger model will be able to do before they spend the money to train it."
   - Problem: Truly textbook. No human, no event, no number.
   - Fix: Anchor to a specific scaling-law prediction (e.g., Kaplan 2020 OpenAI paper, or DeepMind's Chinchilla 2022 finding that "GPT-3 was too big for its training data"). Name the lab and the year.

5. **T3[296] — Arms-race framing**
   - Q: "Big AI labs sometimes describe their work as an 'arms race' — to AGI, to capability, to market share. What's the worry the arms-race framing creates, regardless of who wins?"
   - A: "Pressure to ship fast erodes time spent on safety, testing, and considered choices about what to build."
   - Problem: Wholly abstract. Just an observation about rhetoric.
   - Fix: Anchor to Bing's February 2023 launch with "Sydney" persona melting down on users. "In Feb 2023 Microsoft rushed Bing Chat to market against Google. Within a week it was telling reporters it loved them and wanted them to leave their spouses. What does this episode illustrate about arms-race AI deployment?"

6. **T3[31] — Bigger context windows / quadratic cost**
   - Q: "Bigger context windows sound strictly better — more text the model can use! Why do they come with real tradeoffs the user should be aware of?"
   - A: "Attention cost grows fast with length, so bigger context windows are slower, more expensive, and sometimes less accurate."
   - Problem: Stem teases a single bullet ("strictly better!" "real tradeoffs") with no specific scene. The "lost in the middle" finding mentioned in context is more concrete than what the stem actually frames.
   - Fix: Lead with the "lost in the middle" finding — "Research has shown that LLMs handed a 100-page document tend to remember what's at the top and bottom but lose the middle. Why does this happen, and what does it tell you about long context windows?"

7. **T3[55] — What parameters do**
   - Q: "An LLM's 'parameters' are the numbers — usually billions of them — that get adjusted during training and stay fixed afterwards. What role do parameters actually play when you chat with the model?"
   - A: "They're the learned weights that determine, given the input so far, the probabilities for each possible next token."
   - Problem: Definition → restated definition. The "billions of them" hook is wasted.
   - Fix: Compare two specific named models with different parameter counts (GPT-2: 1.5B; GPT-3: 175B; Llama 70B: 70B). "If GPT-2 had 1.5 billion parameters and GPT-3 had 175 billion, what is it that those extra parameters are doing when you chat?"

8. **T3[59] — Chain-of-thought**
   - Q: "Some AI tasks need a model to 'show its work' — write out reasoning steps before giving a final answer. What's that prompting technique commonly called?"
   - A: "Chain-of-thought prompting, where the user asks the model to 'think step by step' before answering."
   - Problem: Vocabulary lookup, not recognition. Could appear in T1 unchanged.
   - Fix: Anchor to the Wei et al. 2022 Google paper that introduced it, or to the surprising finding that adding "Let's think step by step" to a math prompt jumped accuracy on certain benchmarks substantially. Give the kid a fact.

9. **T3[40] — AGI moving goalposts**
   - Q: "'Artificial General Intelligence' has been five years away for over five decades. Each time a milestone falls — chess (Deep Blue, 1997), Go (AlphaGo, 2016), professional-level text (modern LLMs) — the definition of AGI shifts to exclude what was just achieved. What's that pattern called?"
   - A: "Moving the goalposts — the test keeps being restated to exclude what AI has already accomplished."
   - Problem: This one is actually OK — but it appears alongside T3[41], T3[42], T3[69], T3[296] all teaching variants of the same skepticism lesson. By the fourth or fifth, the wonder is gone. Pick one and let it stand.
   - Fix: Drop T3[41] (general "how should you respond to AGI-in-5 prediction") and T3[42] (general "AGI is hard to define") — keep this one because it has the named milestone list.

10. **T3[206] — Productive AI homework workflow**
    - Q: "Students using AI for homework have two distinct workflows. One actually helps you learn; the other prevents you from learning. What's the productive workflow?"
    - A: "Ask for explanations of concepts, then work problems yourself; use AI to check your work after."
    - Problem: Wisdom-bullet stem. Reads like a parent talking, not a wonder hook.
    - Fix: Anchor to a documented finding — e.g., MIT's June 2025 EEG study showing reduced brain activity in students who outsourced essays to ChatGPT. "A 2025 MIT study put students through essay-writing tasks while measuring brain activity. The students who outsourced to ChatGPT showed reduced engagement in language and memory regions of the brain. What's the productive way to use AI for school work?"

## Recommended action

**Fix the truncation bug first, then ship; cleanup pass optional:**
- **Critical (do not ship without):** Six T3 questions have mid-word-truncated answers or distractors in the source JSON — T3[128], [130], [138], [143], [150], [154]. All are exactly 670 chars total. A character-budget gate appears to have silently truncated them rather than rejecting. Rewrite the affected text to fit, or raise the cap for these specific questions.
- **Recommended (~12 stems, low priority):** Anchor the digital-hygiene checklist questions (T3[200]–[240], the password/2FA/VPN/permissions block, and T3[58], T3[59], T3[296], T3[206]) to specific named incidents or research findings. These currently pass gates but underperform on the Recognition Pattern. ~30–45 min of work to lift average wonder score from 4.2 to ~4.6.
- **Optional:** Thin the AGI-skepticism stems from 5 to 2 — the message is now overrepresented.

T3 is solidly in shippable shape and the strongest tier-3 of any wonder subject I've audited so far.
