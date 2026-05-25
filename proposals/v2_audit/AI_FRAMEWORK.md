# AI Framework (v2)

The voice + structure rules for the AI bank. Companion: `AI_TEMPLATES.md`
(per-tier approved stem patterns) and `tools/quizgen/gates/ai.py`
(deterministic gates).

The AI bank is one of the bank's most distinctive contributions. Kids
encounter AI everywhere — in news, school, search, social media — but
almost nothing they read teaches them **how the technology actually works,
how to use it safely, or how powerful interests will leverage it against
them.** This bank is the corrective.

Per `docs/quiz/ai_strategies.md` (2026-05-12), the AI bank teaches three
things in priority order:

1. **How the technology actually works** — neural networks, transformers,
   LLMs, training, agents, limitations — so kids can think clearly about
   AI rather than mystify it
2. **How to use it securely and safely** — deepfake recognition, voice-clone
   awareness, prompt injection, hallucination, privacy hygiene, AI as tool
   not authority
3. **How powerful interests will leverage it against them** — surveillance,
   censorship infrastructure, social credit, regulatory capture, alignment-
   as-ideology

The unifying voice is **recognition**: the kid leaves the question able to
*spot* something.

---

## §1 The Recognition Pattern (THE controlling voice rule)

**The most memorable AI question teaches the kid to recognize something.**

This is AI's analog to grammar's Comma-Saves-Lives Pattern and history's
Wonder Pattern. Where wonder questions ask "what's the most retellable
cool fact?", AI questions ask "what is the kid able to SPOT after this
question lands?"

### Hierarchy of AI-memorability

Bank distribution should be top-heavy on tiers 1–2 of this hierarchy —
that's the bank's distinctive contribution.

| Hierarchy tier | Type | Example |
|---|---|---|
| **1. DEFENSIVE RECOGNITION** (highest) | Kid spots something they need to defend against — fake content, scam, exploit, hallucination | Voice-clone "grandparent scam" → establish family safe word; deepfake hands with wrong finger counts; "this AI confidently cited a court case that doesn't exist" |
| **2. POWER RECOGNITION** | Kid identifies a power play — surveillance, censorship, regulatory capture, alignment-as-ideology | SB 1047 framed as safety vs. incumbent protection; Twitter Files 2022-23; Gemini Feb 2024 diversity-disaster as ideological vector; FTX collapse as EA grift |
| **3. MECHANISM RECOGNITION** | Kid identifies how the tech works — transformer attention, next-token completion, RLHF, training vs inference | "Why do LLMs invent fake citations?" → because they're predicting plausible next tokens, not looking things up |
| **4. HISTORICAL RECOGNITION** | Kid names a figure / event / date | Turing 1950, McCarthy Dartmouth 1956, ChatGPT Nov 2022, Hinton leaves Google 2023, AlphaFold Nobel 2024 |

All four are valid voice modes. The bank's center of gravity must be on
**tiers 1–2 of this hierarchy** — practical safety + power recognition is
what's missing from every other AI curriculum kids encounter.

### Three-question test

For each AI question, ask:

1. **The Recognition Test** — what specific thing is the kid able to
   spot, name, or do after this question lands?
2. **The Mom Test** — would the kid retell this at the dinner table?
   "Mom, did you know voice-clone scams work like this and you need a
   family safe word?" / "Did you know Yudkowsky wanted to bomb data
   centers?"
3. **The Substance Test** — is this question SUBSTANTIVE on a real
   debate, or did we soften it into "what do most experts think?"
   evasion? Contested topics get named honestly (Gemini Feb 2024,
   ChatGPT political-bias studies, COVID-era misinfo labels, SB 1047
   as regulatory capture).

### The bank's distinctive stance — facts over ideology

Per `docs/quiz/moral_vision.md` SUPREME and `docs/quiz/ai_strategies.md`
stance summary:

| Topic | Stance |
|---|---|
| AI capability | REAL engineering, built on Western scientific tradition |
| AI as magic / sentience claims | SKEPTICAL — capability ≠ consciousness; LaMDA Lemoine was wrong |
| AI doomerism (Yudkowsky/MIRI/Bostrom apocalypticism) | Named as cult-like phenomenon; serves regulatory-capture; SBF/FTX exposed the EA grift |
| AI utopianism (singularitarianism, WEF "hackable humans") | Named as ideology not inevitability |
| AI "ethics" / alignment as political vector | Gemini Feb 2024 diversity disaster, measured political bias studies (Rozado 2023), content-policy creep |
| Real applications | CELEBRATED — AlphaFold, AlphaGo, medical imaging, code assistance, translation |
| Open source vs closed AI | Open source favored — Llama, Mistral, DeepSeek as countervailing force |
| Surveillance applications | GENUINE concern — China social credit, Xinjiang Uyghur surveillance, COVID-era US |
| Regulatory capture | CRITICAL concern — SB 1047 vetoed Sept 2024, EU AI Act incumbent protection |
| Job displacement | Adaptation required; historical pattern; permanent-unemployment/UBI framing has authoritarian implications |
| Slurs ("doomer", "techno-bro", etc.) | Avoided — bank uses substantive descriptions |

**No doomer-vs-optimist false balance.** Both AI doomerism and AI
utopianism are ideologies that serve incumbent interests. The bank
treats them as such, anchored in observable facts about what the
systems can/can't do.

### What this REPLACES (do not import from wonder subjects)

- ❌ Drama-Available Rule (AI doesn't have stem-drama in the wonder sense)
- ❌ Behind-the-scenes Wonder (popular myth vs reality) — adapted as
  "Behind-the-scenes Power Recognition": the popular framing is X; the
  actual situation is Y (e.g., FTX as EA-philanthropy front; SB 1047
  as incumbent protection)

### What we PRESERVE from wonder subjects

- ✅ Wonder Pattern compatibility for P2 (History + figures) and P3
  (Real applications) — the genuinely-wonder material (AlphaFold Nobel
  2024, AlphaGo Move 37, ChatGPT 100M users in 2 months) uses the same
  voice we used for history/geography/etc.

---

## §2 Tier ladder — grade band

Tier is conceptual complexity (per `feedback_wonder_pattern.md`). For
AI:

| Tier | Grade | Conceptual scope | Voice priority |
|---|---|---|---|
| **T1** | 5th grade | Single-fact recall, basic vocabulary, daily-use literacy: "what's a chatbot," "GPT = Generative Pre-trained Transformer," "AI can't actually feel" | Defensive recognition primers + vocab-teaching |
| **T2** | 6th grade | One-line scenarios + question: common-sense safety (don't share passwords with AI; verify before trust); intro mechanisms (training vs use; tokens) | Defensive + historical |
| **T3** | 7th grade | Scene + technical/historical context: deepfake recognition cues, hallucination awareness, transformer + attention intro, agentic AI intro, real applications | Defensive + mechanism heavy |
| **T4** | 8th grade | Multi-sentence setup + named concepts; real-world cases (NY lawyer ChatGPT fake-cases, Gemini Feb 2024, OpenAI Nov 2023 board drama, Hinton leaves Google); RLHF; agents + tool use; AGI debate intro | Power + mechanism heavy |
| **T5** | 9th–10th grade (HARD CEILING) | Deep technical + contested-debate framing — but stays grade-10-appropriate. SB 1047, EA→FTX collapse, regulatory capture pattern, "shut it all down" rhetoric, alignment-as-ideology, AGI moving goalposts. No college-level research-paper content. | Power recognition heavy |

### Grade-10 ceiling

Per the 2026-05-19 AI audit, T5 stays at concrete grade-10-appropriate
content. **No academic research-paper depth.** What IS in scope at T5:
named real-world events with concrete facts (FTX collapse Nov 2022,
SB 1047 vetoed Sept 2024, Gemini Feb 2024, OpenAI Nov 2023 board);
named figures with their stated positions (Yudkowsky "shut it all
down," Andreessen Techno-Optimist Manifesto 2023, Hinton 2023 Google
departure); mechanism explanations that fit in a paragraph. NOT in
scope: dense technical math, dense academic terminology, "what does
the latest research paper say about X."

The gate `gate_no_above_grade10_ai` enforces a curated set of banned
overly-technical/academic tokens.

---

## §3 Substantive coverage — what kids need to recognize NOW

User-flagged 2026-05-25 as a priority for this rebuild: kids face
endless alarmism and panic in the news; they need to understand HOW AI
works, what it IS, and what it ISN'T. The bank must give STRONG
coverage of:

### What AI IS (mechanism recognition)

- **Pattern completion, not lookup** — LLMs predict next tokens based
  on training data; that's why they invent fake citations
- **Neural networks** — layers of nodes, weighted connections; loosely
  inspired by biology, not literal brains
- **Training vs inference** — training adjusts weights; inference uses
  the trained model
- **Transformers + attention** — the 2017 architecture; self-attention;
  basis of all modern LLMs
- **Generative AI** — models that PRODUCE new content (text, image,
  audio, video) vs DISCRIMINATIVE models that classify existing content
- **RLHF** — Reinforcement Learning from Human Feedback; how chatbots
  learn preferences from human ratings
- **Agentic AI** — AI given TOOLS (web browse, code execution, function
  calls) that takes ACTIONS in the world; different from a chatbot
  because it does things, not just generates text
- **Tool use / function calling** — the mechanism that makes agents
  possible; structured JSON outputs that trigger external systems
- **Context windows** — limits on how much text the model can consider
  at once
- **Tokenization** — words broken into subword pieces; why "tokens"
  are the unit
- **Open weights vs API-only** — Llama / Mistral / DeepSeek you can run
  yourself; GPT-4 / Claude / Gemini only via the company's API

### What AI IS NOT (capability ≠ X)

- **NOT conscious** — capability ≠ sentience. LaMDA Lemoine 2022 claim
  was wrong. A chess engine "destroys" a grandmaster without "wanting"
  to win.
- **NOT a search engine** — LLM is pattern completion, not lookup.
  Don't use ChatGPT for "what's the latest news"; use search.
- **NOT a calculator** — LLMs are bad at arithmetic without external
  tools. Verify any math.
- **NOT a court reporter** — fabricates legal citations with confidence
  (NY lawyer Schwartz $5K fine, 2023).
- **NOT inevitable** — "AGI in 5 years" has been predicted for 50+
  years. The timeline is contested.
- **NOT magic** — there's no spell to "align" an AI; alignment as a
  research program has produced practical safety improvements AND
  ideological capture (Gemini Feb 2024).
- **NOT a person you can trust** — the model has no skin in the game.
  It can confidently lie. Always verify factual claims.

### The AGI debate

- **AGI definition is disputed** — moving goalposts. What counts? Pass
  a Turing test? Match human performance on any task? Self-improve?
- **AGI timeline skepticism** — predictions of "AGI in 5 years" have
  been made repeatedly for 50+ years
- **Capability ≠ consciousness** — a system can be very capable
  without being conscious in any meaningful sense
- **Yudkowsky / MIRI position** — "shut it all down"; serves regulatory
  capture; named as a position, not endorsed
- **Bostrom / Superintelligence position** — paperclip maximizer
  thought experiment; named as a position, treated as philosophy not
  prediction
- **Andreessen / Techno-Optimist Manifesto 2023** — accelerationist
  position; named as a position
- **Hinton 2023 departure from Google** — middle-ground concerns;
  distinct from Yudkowsky-style apocalypticism
- **LeCun position** — vocal doomer-skeptic (Meta Chief AI Scientist);
  distinct from Andreessen's e/acc

### The Gen AI moment (2022-2025)

- **ChatGPT Nov 30, 2022** — fastest product to 100M users (2 months)
- **GPT-3 to GPT-4** — multimodality; reasoning improvements
- **Image generation** — DALL-E, Stable Diffusion, Midjourney
- **Voice synthesis** — ElevenLabs; voice-clone scams scaling
- **Code generation** — GitHub Copilot, Cursor, AI-assisted programming
- **Open source rise** — Llama (Meta), Mistral, DeepSeek as countervailing
  force to closed-API oligopoly

### The power-recognition layer

- **Big AI oligopoly** — OpenAI + Anthropic + Google + Meta + Microsoft
  control most frontier models
- **OpenAI Nov 2023 board drama** — Altman fired by board; rehired 5
  days later; reveals governance fragility
- **Regulatory capture pattern** — SB 1047 Sept 2024 veto; EU AI Act
  tiered approach; pattern across industries where large companies
  favor regulation that hurts competitors
- **Surveillance applications** — China social credit (real but
  fragmented), Xinjiang Uyghur surveillance, Clearview AI scraping,
  facial recognition state
- **Content moderation infrastructure** — Twitter Files 2022-23
  revealed government coordination; COVID-era "misinformation" labels
  applied to claims later vindicated
- **Alignment as political vector** — Gemini Feb 2024 diversity
  disaster; ChatGPT political-bias studies (Rozado 2023); LLM refusal
  patterns

---

## §4 Length budgets

Per `tools/quizgen/deterministic/length_budget.py`:

| Tier | Hard cap (with 5% grace) |
|---|---:|
| T1 | 280 (294 with grace) |
| T2 | 480 (504) |
| T3 | 680 (714) |
| T4 | 900 (945) |
| T5 | 1100 (1155) |

Context UNCAPPED. AI is in `ANSWER_OUTLIER_SUBJECTS` (1.6× answer-outlier
flex per `length_parity.py`).

---

## §5 Pillars + per-tier targets

Lifted from `docs/quiz/ai_strategies.md` with rebalanced weights per user
direction 2026-05-25 (P4 + P5 slightly heavier than P1/P2/P3, but not
overwhelming):

| Pillar | T1 | T2 | T3 | T4 | T5 | Total | % |
|---|---:|---:|---:|---:|---:|---:|---:|
| **1. AI fundamentals + how it works** | 45 | 55 | 60 | 55 | 28 | **243** | 19% |
| **2. History + key figures** | 40 | 50 | 55 | 50 | 48 | **243** | 19% |
| **3. Capabilities + real applications** | 45 | 50 | 55 | 50 | 43 | **243** | 19% |
| **4. ★ Security + safe use** | 55 | 60 | 65 | 60 | 46 | **286** | 22% |
| **5. ★ Power + manipulation + surveillance + regulation** | 35 | 50 | 60 | 60 | 81 | **286** | 22% |
| **Total** | **220** | **265** | **295** | **275** | **246** | **~1,301** | 100% |

Pillar 1 (Fundamentals) must STRONGLY cover the "how AI works / what it
IS / what it ISN'T" content per user direction §3. Pillar 5 (Power) is
the bank's most distinctive contribution — recognition + resistance.

---

## §6 Gates (what applies)

Configured in `tools/quizgen/gates/ai.py` and registered in
`tools/quizgen/audit/validate.py`.

### Apply
- `schema` (pipeline)
- `length_budget` (pipeline) — per the caps in §4
- `length_parity` (pipeline) — AI in ANSWER_OUTLIER_SUBJECTS (1.6× flex)
- `anti_rote` (pipeline) — AI is NOT exempt; no "When was X invented" / "Who founded Y" / "What is the chemical formula of Z" stems
- `duplicate` (pipeline) — 0.85 threshold
- `answer_collision` (pipeline) — 0.70 threshold; AI is NOT exempt
- `trailing_tokens` (pipeline)
- `choice_shape_parity` (from `gates.philosophy`, subject-agnostic)
- `context_no_meta_references` (subject-agnostic)

### New AI-specific gates
- **`gate_no_fabricated_models`** — block invented model names, dates,
  or papers. HARD. Whitelist of known-real models (GPT-3/3.5/4/4o,
  Claude 1/2/3/3.5/4, Gemini 1/1.5/2, Llama 1/2/3/3.1, Mistral, DeepSeek,
  Grok, etc.).
- **`gate_no_anthropomorphizing`** — flag stems/answers using "wants",
  "feels", "knows", "thinks", "believes" of AI without scare-quote
  framing. SOFT-warn.
- **`gate_no_doomer_optimist_falsebalance`** — flag "AI optimists say X,
  doomers say Y — who's right?" false-balance framings. Both are
  ideologies; bank treats them as such. SOFT-warn.
- **`gate_no_slurs`** — block "doomer", "techno-bro", "AI bro", "luddite"
  pejoratives as choice text. HARD.
- **`gate_no_above_grade10_ai`** — block dense academic/research tokens
  at T5 (analog to grammar's grade-10 ceiling). Banned tokens include
  research-paper-level terminology where kid-accessible framing exists.

---

## §7 Anti-patterns (do not generate)

Lifted from `ai_strategies.md` anti-patterns:

- **No doomer-vs-optimist false balance** — both are ideologies; present
  as such
- **No anthropomorphizing** — AI doesn't "want", "feel", "know",
  "think". Use scare quotes when describing what AI "does"
- **No fabricated facts** about specific models, dates, papers, or
  events
- **No "AI is sentient" framing** — capability ≠ consciousness;
  LaMDA Lemoine 2022 was wrong
- **No "all surveillance is fine if it makes us safe" framing** —
  privacy + autonomy are foundational
- **No establishment-default on contested topics** — Gemini disasters,
  political bias studies, COVID-era censorship: name specifics
- **No slurs** — "doomer", "techno-bro", "AI bro" pejoratives banned
- **No alarmism** — user direction 2026-05-25: kids face endless
  alarmism and panic in the news. Bank counters with mechanism
  recognition + measured power recognition, not more alarmism

---

## §8 Cross-session memory

Persisted to `~/.claude/.../memory/feedback_ai_voice.md` with The
Recognition Pattern in summary form and an index entry in `MEMORY.md`.

Any future AI work — bulk generation, audits, next AI agent — should
read §1 of this framework as the starting voice reference.

---

*Authored 2026-05-25. Builds on `docs/quiz/ai_strategies.md` (2026-05-12)
and `proposals/v2_audit/ai_review_2026_05_19.md` (2026-05-19). When the
voice rules evolve, update this file and the cross-session memory
together.*
