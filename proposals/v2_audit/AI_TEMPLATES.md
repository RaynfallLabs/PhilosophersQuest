# AI Templates (v2)

Per-tier approved stem patterns + anti-patterns. Companion to
`AI_FRAMEWORK.md` (the WHY); this is the WHAT.

Authoring rule: every new AI question should match an approved template
AND fit somewhere on the Recognition Pattern hierarchy (`AI_FRAMEWORK.md`
§1). When a question doesn't fit a template, refactor it to one — or
propose the template here.

---

## §1 Approved stem patterns by tier

### T1 patterns (grade 5 — vocab + daily-use literacy)

Length cap: ≤ 280 chars total. Vocab-teaching is the workhorse.

| Pattern | Example | Notes |
|---|---|---|
| Vocab-by-example | "ChatGPT and Claude are programs you can talk to in plain English. What general kind of AI is this?" → "A chatbot" | Show the concept first |
| Acronym-recall | "GPT in 'ChatGPT' stands for…" → "Generative Pre-trained Transformer" | T1 acronyms with kid-relevant context |
| Single-fact origin | "Who released ChatGPT in November 2022?" → "OpenAI" | Concrete, kid-known |
| Defensive-recognition primer | "An email looks like it came from your school but the principal's name is wrong and the link looks weird. What should you do?" → "Show it to a parent before clicking" | T1 entry into the safety pillar |
| Capability-vs-consciousness primer | "When a chatbot writes 'I'm sorry to hear that,' is it actually feeling sorry?" → "No — it's just words it learned to produce" | Foundational "what AI ISN'T" |

### T2 patterns (grade 6 — one-line scenarios + question)

Length cap: ≤ 480. Mini scenarios become the norm.

| Pattern | Example | Notes |
|---|---|---|
| Scenario + safety question | "A voice on the phone sounds like Grandma and asks you to send money urgently. The voice could be a clone. What's a smart family habit to set up FIRST?" → "A family safe word that only real Grandma would know" | The bank's signature voice-clone protection |
| Mechanism intro | "When you type a question into ChatGPT, what is the model literally doing on the inside?" → "Predicting which word comes next, one piece at a time" | Mechanism recognition at intro level |
| Verify-before-trust | "ChatGPT writes you a science paper paragraph that cites a study you don't recognize. Before you use it, what do you do?" → "Search for the study; if you can't find it, it's probably fake" | Hallucination defense |
| Historical-event-recall | "ChatGPT hit 100 million users faster than any product in history. About how many months did it take?" → "Two months" (Nov 2022 to Jan 2023) | T2 historical-recognition |
| What-AI-IS-NOT primer | "An LLM is not a calculator. Why not — what is it actually built to do?" → "Predict text, not compute numbers" | Mechanism recognition |

### T3 patterns (grade 7 — scene + technical/historical context)

Length cap: ≤ 680. Multi-sentence stems become common.

| Pattern | Example | Notes |
|---|---|---|
| Mechanism + example | "A neural network is called 'deep' when it has many layers stacked between input and output. Each layer processes the data a little further. Why does going deeper let the network handle more complex patterns?" | Mechanism recognition T3 |
| Defensive-skill (deepfake) | "You see a viral video of a celebrity saying something shocking. Three details often give away AI-generated video. Which is NOT a typical deepfake tell?" → (correct: "The background music is too loud") (distractors: blink rates, mouth-sync drift, finger counts) | The bank's signature defensive content |
| Agentic AI intro | "A chatbot answers questions. An AI 'agent' is different — it actually DOES things in the world. What lets an agent do this?" → "Tools — code execution, web search, function calls the AI is allowed to trigger" | The agent / agentic AI distinction kids must understand |
| Hallucination case | "In 2023 a New York lawyer named Steven Schwartz filed a court brief citing six cases. None of them existed — ChatGPT had invented them. What's the underlying reason an LLM does this?" → "It generates plausible-sounding text, not truth" | Mechanism + defensive recognition combined |
| Real-application celebration | "DeepMind's AlphaFold predicted the 3D structure of about 200 million proteins — essentially every protein in nature. Why is this a big deal for medicine?" → "Knowing a protein's shape lets researchers design drugs targeting it" | Wonder-compatible AI content |

### T4 patterns (grade 8 — multi-sentence setup + named concepts)

Length cap: ≤ 900. Named real-world cases dominate.

| Pattern | Example | Notes |
|---|---|---|
| Named event + question | "In February 2024, Google's Gemini image generator produced racially diverse Nazi soldiers and refused to generate images of white historical figures. The product was suspended. What problem does this case illustrate?" → "Alignment training can encode ideological choices that override historical accuracy" | The bank's signature power-recognition |
| Mechanism deep | "Transformers use a 'self-attention' mechanism introduced in the 2017 paper 'Attention Is All You Need.' Self-attention lets each word in the input look at every other word at once. Why was this a big improvement over older sequential approaches?" | Mechanism recognition T4 |
| Power-recognition multi-sentence | "In November 2023, OpenAI's board fired Sam Altman. Five days later he was rehired and the board members who fired him were gone. What deeper question did this episode raise about Big AI?" → "Whether the people building powerful AI can actually be governed" | Power recognition T4 |
| Open-source vs closed | "Meta releases Llama models with the weights downloadable. OpenAI keeps GPT weights private and only offers API access. What kind of countervailing force does open-weight AI provide?" → "It prevents a small group of companies from being the only ones who can run the technology" | Open-source celebration |
| Agentic AI deep | "An AI agent given access to a web browser, a code interpreter, and your calendar can do far more than a chatbot. But it can also make many more kinds of mistakes. Why is the safety challenge for agents categorically different from chatbots?" | T4 agentic AI deep dive |

### T5 patterns (grade 9-10 HARD CEILING — deep technical + contested debate)

Length cap: ≤ 1100. Stays grade-10-appropriate. No academic research-paper depth.

| Pattern | Example | Notes |
|---|---|---|
| Contested-debate framing | "Eliezer Yudkowsky's position is that frontier AI development should be 'shut down' globally. Marc Andreessen's October 2023 'Techno-Optimist Manifesto' argued the opposite. Both positions have something in common that's worth noticing. What?" → "Both treat AI as an inevitable historical force; they just disagree on whether to embrace or stop it" | T5 power-recognition signature |
| Regulatory-capture analysis | "California's SB 1047 would have required safety testing for large AI models. It was vetoed in September 2024. Critics argued it would protect incumbents like OpenAI and Anthropic from open-source competition. What's the general pattern at work?" → "Large companies often support regulation that smaller competitors can't afford" | T5 power-recognition pattern |
| AGI debate at depth | "'Artificial General Intelligence' has been predicted to be five years away for over five decades. The definition itself keeps shifting — when Deep Blue beat Kasparov in 1997, chess was no longer 'AGI-relevant.' What's this pattern called?" → "Moving goalposts" | AGI debate T5 |
| Real-event power-recognition | "In November 2022, FTX collapsed. Its founder Sam Bankman-Fried had been one of the largest funders of AI-safety nonprofits and the Effective Altruism movement. What did this expose about AI doomerism funding?" → "A significant share of AI-safety advocacy was downstream of FTX money" | T5 named-event with substance |
| Mechanism + societal | "Recommendation systems on TikTok, YouTube, and Instagram all use AI to maximize 'engagement.' Engagement is measured by clicks, watch-time, and shares. What happens when emotionally arousing content gets more engagement than calm content?" → "The systems amplify outrage and division because that's what the metric rewards" | T5 power-recognition mechanism |

---

## §2 Choice-shape conventions

### Length parity

AI is in `ANSWER_OUTLIER_SUBJECTS`. The 1.6× answer-outlier flex applies
— a longer mechanism-explanation answer can legitimately exceed
distractor lengths by up to 1.6×.

Distractors should still be in approximate parity with each other
(1.30 max/min ratio among distractors).

### Dash-shape parity

All four choices share dash usage (all em-dash, or none). Same rule as
wonder subjects — kids spot skim-tells.

### Distractor plausibility

Distractors must be:
- Real positions someone holds (for power-recognition questions) or
  real failure modes (for mechanism / safety questions)
- For mechanism questions: a sibling mechanism that's NOT the right
  answer (e.g., "loss function" vs "gradient descent" vs "backprop"
  vs "activation function")
- For defensive-recognition questions: plausible-wrong defense moves
  someone might actually try
- For figure-identification: other figures in adjacent positions
  (Yudkowsky / Bostrom for doomer end; Andreessen / LeCun for
  accelerationist end)

Banned distractor types:
- Made-up model names (Claude-7, GPT-8-Plus, etc.)
- Cartoon-villain framings ("AI wants to destroy us")
- Joke distractors that don't test anything

---

## §3 Anti-patterns (do not generate)

- **Doomer-vs-optimist false balance** — both are ideologies; present as
  such
- **Anthropomorphizing** — AI "wants", "feels", "knows", "thinks",
  "believes" without scare quotes
- **Fabricated facts** — invented model names, dates, papers, or events
- **AI-is-sentient framings** — capability ≠ consciousness
- **Establishment-default on contested topics** — name specifics
  (Gemini Feb 2024, Rozado 2023 study, Twitter Files, COVID label
  abuses, SB 1047, FTX collapse, OpenAI Nov 2023 board)
- **Slurs** — "doomer", "techno-bro", "AI bro", "luddite"
- **Alarmism** — kids face endless panic in the news; bank counters with
  measured recognition, not more panic
- **Above-grade-10 academic depth** — T5 stays grade-9-10; no
  research-paper terminology

---

## §4 Quotation convention

When a stem refers to a specific quote, named position, or product
output, the quote should be in single or double quotes. Example
sentences should be quoted. This isn't a hard gate (no
`gate_example_sentence_quoted` for AI) but it's the norm.

---

## §5 Source materials

- `docs/quiz/ai_strategies.md` (2026-05-12) — full strategy taxonomy
- `proposals/v2_audit/ai_review_2026_05_19.md` — prior bank audit
- `docs/quiz/moral_vision.md` — SUPREME stance reference

When authoring a new question:

1. Pick the strategy ID from `ai_strategies.md`
2. Pick the tier from §2 of the framework (grade-band ladder)
3. Pick the template from §1 above
4. Author the question
5. Self-validate against gates (`tools/quizgen/gates/ai.py`)
6. Score against the Recognition Pattern hierarchy
   (`AI_FRAMEWORK.md` §1)

---

*Authored 2026-05-25. Companion to `AI_FRAMEWORK.md`.*
