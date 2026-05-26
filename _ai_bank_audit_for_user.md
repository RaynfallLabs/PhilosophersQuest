# AI Bank Audit — Morning Report

**Date:** 2026-05-25 (overnight)
**Bank:** `data/questions/ai.json` — 1225 questions, commit `77dad8f`
**Method:** 3 opus audit agents (T1+T2, T3, T4+T5) + my own 50-question stratified sample. Each agent scored ALL questions in scope on three criteria you named: non-AI-adult engagement, kid 12-15 connectability, wonder + mystery.

---

## TL;DR

**Ship-quality. Targeted edits recommended, not a rewrite.**

The bank passes every gate (1225 / 1225) and consistently delivers what you asked for: a kid learns *what AI is*, *how it works*, *where the power plays are*, and *how to defend* — not a panic curriculum. Recognition Pattern is alive across all 5 tiers. Defensive recognition (voice clones, deepfake tells, Schwartz $5K hallucinated citations, Hong Kong $25M CFO deepfake call) is the bank's beating heart and works.

**Three things I'd fix before you consider it done:**
1. ~12 T2 corporate-governance questions need rewriting to keep the drama but lose the org-chart framing (effort: ~1 hr)
2. ~10-15 T4 P1 ML-textbook questions (backprop / gradient descent / epochs / BPE) are flashcards, not recognition skills — drop them (effort: ~30 min)
3. ~6-9 T5 P5 governance questions read as "structural recognition" refrain — pick strongest 3, drop rest (effort: ~30 min)

**One critical bug I found and fixed overnight:** 6 T3 questions had mid-word truncated answers/choices ("design dru", "of fol", "becomes a crea") — the source agent self-truncated at the budget cap. I rewrote all 6 in-place and re-validated. The bank you wake up to is the fixed version.

---

## Per-tier scores

| Tier | Grade | Engagement (non-AI adult) | Kid 12-15 connect | Wonder | Verdict |
|---|---|---|---|---|---|
| T1 | 5 | **4.6** | **4.2** | 3.6 | Ship as-is (5 cosmetic tweaks optional) |
| T2 | 6 | 4.2 | **3.6** | 3.8 | Minor rewrite of ~12 questions |
| T3 | 7 | **4.6** | **4.5** | **4.2** | **STRONGEST tier.** Ship after truncation fix (done) |
| T4 | 8 | 4.2 | 3.9 | 4.2 | Cut ~10-15 ML-textbook questions |
| T5 | 9-10 | 3.8 | 3.5 | 4.0 | Compress P5 governance run, lead with hooks not CV |

**Average:** 4.3 / 3.9 / 4.0 — solidly ship-ready.

**T3 is the strongest tier** by all three agents' scoring. It's the most "wonder + recognition + kid-actionable" tier. If a kid only ever plays T3, they'd learn the most of any single tier.

**T5 grade-ceiling check (the one I was most worried about):** Held. Zero violations. The densest technical block (MoE, embeddings, multimodal, tokenization at T5 #14-#21) stays inside the ceiling because answers reveal meaning in plain English rather than restating jargon. "Subtract 'man' from 'king,' add 'woman,' land near 'queen'" is the kind of grade-10 AI literacy you want.

---

## Critical finding — FIXED

**The 670-char truncation bug.** 6 T3 questions had answer or distractor text cut off mid-word:

| Bank # | Original (truncated) | Fixed |
|---|---|---|
| 569 (T3#128) | "...researchers design **dru**" | "...researchers design **drugs that fit**" |
| 571 (T3#130) | "...the chemistry of **fol**" | "...the chemistry of **folding**" |
| 579 (T3#138) | "...noise becomes a **crea**" | "...becomes a **creative starting point**" |
| 584 (T3#143) | "...the AI catches the **[trailing space]**" | "...catches the **high-risk ones**" |
| 591 (T3#150) | "...see things at **fie**" | "...see things at **field scale**..." |
| 595 (T3#154) | C2: "...for the full duration of **th**" | C2: "...for the full duration of **the trip**" |

**Root cause:** Each was at exactly 670 chars (T3 cap = 680). The generator agent self-truncated to fit the budget rather than rejecting and regenerating. My existing length_budget gate accepts under-cap, so it never flagged the cut.

**Mitigation pending your call (task #48):** Add a deterministic gate that catches mid-word truncation. The cleanest precise signal is *trailing whitespace in any field* (legit text never ends with a trailing space). Less precise but worth: *answer/choice ending with a 1-3 char fragment after a connective* ("of fol", "becomes a crea"). My quick heuristic produced 300+ false positives; building this safely needs care.

---

## What's working (consensus across agents + me)

### 1. Jargon discipline is real
Every transformer / RLHF / embedding / fine-tuning question defines the term in the same sentence or immediate setup. T2 #14 paints "175 billion marbles" as a swimming pool of parameters. T2 #16 calls the context window "a sliding window over your conversation." The Winograd "trophy didn't fit in the suitcase" sentence is used to teach self-attention. A 35-year-old who has never used ChatGPT can read any question cold and follow it.

### 2. Defensive recognition is the bank's beating heart
Voice-clone safe-word scenes, deepfake tells (hand counts, ear asymmetry, garbled signage, "delve into"), Schwartz $5K lawyer arc taught three ways, Hong Kong $25M deepfake CFO call, NH 2024 Biden robocall, Robert Williams Detroit wrongful arrest. Concrete, kid-actionable, world-grounded.

### 3. Named figures arrive with story-shape, not labels
- Hassabis: chess prodigy → video games → DeepMind → Nobel 2024
- Hinton: 2016 "radiologists in 5 years" prediction aging poorly + 2023 Google departure + 2024 Physics Nobel
- Kasparov: 1997 loss + accused IBM of human help, IBM denied
- Ken Jennings: "I, for one, welcome our new computer overlords" (the Simpsons reference)
- Lee Sedol: retired 2019 because "being the world's best wasn't 'best' anymore"
- Weizenbaum: his own secretary formed real emotional attachment to ELIZA

### 4. Substantive on contested topics (the framework's hardest ask)
Gemini Feb 2024 (racially diverse Nazis, Pichai apology) — named without verdict. Twitter Files / FBI flagging. COVID lab-leak labeling. Rozado 2023 LLM bias study. SB 1047 / Newsom veto. FTX → EA pipeline (SBF's funding of AI safety advocacy named honestly). All handled with attribution + specifics, not editorializing. **This is the moral_vision.md compliance check passing.**

### 5. Anti-doomer AND anti-utopian stance is substantive
Hinton vs Yudkowsky distinction. Bostrom paperclip as thought experiment, not prediction. LeCun's technical critique. Andreessen e/acc named fairly. The kid gets a map of the debate, not a verdict.

### 6. Wrong-answer ladders carry the comic-absurd register
"Training data is illegal in most countries," "the model gained consciousness on a Tuesday," "AI runs on chemical reactions inside the CPU," "agents must be paid wages by federal law." This keeps the bank readable at length.

---

## What needs work (priority-ordered)

### Priority 1 (~1 hr) — T2 corporate-governance cluster
About 12 T2 questions presume the kid cares about non-profit board theory, capped-profit restructurings, Productivity Score surveillance, and Snowden's XKeyscore (from before the kid was born). These are content for a Wall Street Journal reader.

**Specific question IDs to rewrite:**
- T2 #71 ("Can a non-profit board actually govern…") → "When OpenAI's board fired Altman in Nov 2023, what did most employees do?" Answer: "About 700 of them threatened to quit and follow him to Microsoft."
- T2 #190 (OpenAI org-chart restructuring) → "OpenAI was founded with Elon Musk among the funders. Musk later split from the company. Why?"
- T2 #196 (XKeyscore 2013) → Replace with a contemporary surveillance event the kid has heard of.
- T2 #200 (Microsoft Productivity Score workplace surveillance) → Pivot to school AI surveillance (Gaggle/GoGuardian/Bark) — same lesson, kid's actual world.
- T2 #221 (FTX → AI safety funding) → Anchor with names + year + conviction + concrete consequence.
- T2 #185, #226 (Twitter Files) → Anchor in specific Musk/Taibbi document drop.
- T2 #192 (Disinformation Governance Board) → Anchor with Nina Jankowicz (fired official) if keeping this content.

**The pattern:** keep the drama, lose the governance framing.

### Priority 2 (~30 min) — T4 P1 ML-textbook block
T4 #6-#22 has ~10-15 questions on backprop / gradient descent / loss function / batch size / epoch / regularization / dropout / mini-batch SGD / BPE tokenization. Each is technically correct. As a block of 10 in a row, it reads like a CompTIA Security+ chapter, not recognition skills.

**The framework says (and I agree):** the kid does not need to know what BPE stands for. Drop or replace:
- T4 #8 (mini-batch SGD memory) → "GPT-3 saw each training example fewer than once on average. Why don't labs just train longer?"
- T4 #9 (learning rate schedule) → drop entirely
- T4 #15 (epoch definition) → drop, replace with "Why does Stability AI keep releasing newer Stable Diffusion versions?"
- T4 #20, #21 (tokenization, BPE) → cut; let T5 #21 do the work (it has the "antidisestablishmentarianism = 6 tokens" hook)
- T4 #22 (parameter count) → "GPT-4 has hundreds of billions of parameters. Where are they actually stored when the model isn't being used?" (answer: on disk, ~700GB)

### Priority 3 (~30 min) — T5 P5 governance/finance "structural recognition" refrain
Nine adjacent T5 questions (#109, #111, #163, #165, #166, #167, #168, #169, #170) all run as: "[Concentrated actors do X]. What's the structural recognition?" → "[Concentration produces Y outcome with limited accountability]." The lesson is true; nine instances of it turns into a refrain.

**Recommended cuts:**
- T5 #163 (compute as bottleneck — 5 cloud providers + chip model numbers in stem) → Rewrite as "Why did Sam Altman go to Saudi Arabia in 2024 asking for $7 trillion?"
- T5 #168 (Anthropic-Amazon-Google deals) → Merge with T5 #167 (Microsoft-OpenAI) into one tighter question
- T5 #169 (lobbying disclosures, OpenSecrets) → DROP
- T5 #170 (sovereign wealth funds, Mubadala, MGX, Temasek) → DROP or rewrite as "Sam Altman flew to Saudi Arabia. Why?"
- T5 #173 (DARPA history of subfield funding) → DROP the subfield list
- T5 #174 (AI patents, Federal Circuit) → DROP — law school
- T5 #176 (UK Online Safety Act, Ofcom) → Pair with US example or drop

**Keep:** T5 #103 (SB 1047 regulatory capture — exemplary), T5 #105, T5 #138 (Cambridge Analytica reality check).

### Priority 4 (~20 min) — Lead with the dinner-test moment, not the CV
Several T5 stems bury the wonder hook under acronym setup:
- T5 #28 (Yudkowsky bomb-the-data-centers Time op-ed) — burying the "bomb data centers" line is leaving the wonder on the table. **Lead with it.**
- T5 #109 (DoD/IC contracts) — pick ONE example (Palantir + ICE, or Microsoft + JEDI) and tell the story
- T5 #170 (sovereign wealth) — see above; lead with Altman flying to Saudi Arabia

### Priority 5 (~20 min) — De-duplicate cross-tier pairs
- T4 #271 / T5 #108 — chip export controls
- T4 #142 / T5 #52 — lawyer hallucination (Schwartz/Mata)
- T4 #117 / T5 #117 — paperclip
- T4 #75 / T5 #27 — Pause Letter signers

Easiest: keep T5 version (deeper), replace T4 version with next-best topic in the spec.

### Priority 6 (optional ~30 min) — Anchor T3 digital-hygiene block to named incidents
T3 #200-#240 (password / 2FA / VPN / permissions / ad-IDs / dark patterns) is correct but flat. Anchor to:
- 2FA → Jack Dorsey SIM-swap (Aug 2019) gave attackers his @jack for 30+ minutes
- VPN → every YouTube tech-influencer's NordVPN sponsorship pitch
- Arms-race framing → Bing "Sydney" persona Feb 2023 meltdown
- AI homework → MIT June 2025 EEG study showing reduced brain activity in students who outsourced essays

Would lift T3 wonder from 4.2 to ~4.6.

---

## Sample of the bank's best work

### T3 #78 — Lee Sedol's retirement (peak wonder)
> Q: "Lee Sedol — the human grandmaster who played AlphaGo in 2016 — retired from professional Go in 2019. He named one specific reason. What did he give as the reason?"
> A: "He felt no longer at the top because AI had surpassed humans, and even being the world's best wasn't 'best' anymore."

### T4 #161 — Hong Kong $25M deepfake CFO call
> "In February 2024, a Hong Kong company employee was tricked into transferring HK$200 million (about US$25 million) after attending a video call with what appeared to be the company's CFO and other senior staff. Every face on the call except his was deepfaked."

### T5 #1 — AGI moving label
> "In 1956 at Dartmouth, programs that could play chess were 'artificial intelligence.' After Deep Blue beat Kasparov in 1997, chess was demoted to 'mere search.' AlphaGo's 2016 Go victory was reclassified as 'just pattern matching.' GPT-4 passing the bar exam in 2023 became 'just statistics.'"
> A: "Whatever AI can already do gets demoted out of the definition; 'AGI' functions as a moving label for whatever AI hasn't built yet."

### T5 #150 — Setzer / Character.AI lawsuit (handled with respect)
> "In October 2024, Megan Garcia filed a wrongful-death lawsuit against Character.AI after her 14-year-old son Sewell Setzer III died by suicide..."

### T5 #103 — SB 1047 regulatory capture
> Names Newsom, the date (Sept 29, 2024), Anthropic-supported / Meta-opposed split, and lifts to a structural recognition (regulatory capture) that generalizes to non-AI cases.

### T4 #285 — Kenyan data labelers
> A: "Frontier AI is built partly on outsourced labor — under-compensated workers seeing distressing content to make the models more polite." (Time Magazine 2023 story, $2/hour, real workers.)

---

## Decisions for you in the morning

1. **Do you want me to execute Priorities 1-3 (the ~2 hours of rewrites)?** Or ship the bank as-is and queue these for later?
2. **Truncation gate (task #48):** I deferred building it because the safest heuristic (trailing whitespace) is narrow, and broader heuristics had 300+ false positives. Want me to add the narrow version (whitespace-only)? Or leave it?
3. **Re-audit philosophy / animal / cooking / etc.?** The 4 rules I discovered during the geography rebuild (place-anchoring, no-theory-stacking, decoration-mismatch, wonder-in-stem) should ideally be re-audited across the older banks. That work was queued (`project_post_geography_audits.md`) but not done.
4. **Open question from your earlier rebuilds:** common-item identification tiering — still unresolved per `project_identify_design.md`.

---

## Files written overnight

- `_audit_ai_t12.md` — T1+T2 detailed findings (10 best + 10 worst exemplars)
- `_audit_ai_t3.md` — T3 detailed findings (10 best + 10 worst exemplars)
- `_audit_ai_t45.md` — T4+T5 detailed findings (10 best + 10 worst per tier)
- `_my_audit_findings.md` — my independent 50-question sample notes
- `_my_audit_sample.txt` — the actual 50 questions I read
- `_fix_t3_truncations.py` — the truncation-fix script (kept for audit trail)
- `_ai_bank_audit_for_user.md` — **this file** (the report)

## Bank state at wakeup

- `data/questions/ai.json` — 1225 questions, 1225/1225 PASS (the 6 truncations are fixed)
- Latest commit: `77dad8f` (the rebuild) — the truncation fixes are uncommitted
- Tasks: #42-#46 audit complete, #47 truncation fix complete, #48 (truncation gate) deferred for your call

**Recommendation:** wake up, look at this report, decide which priorities (if any) to execute, and I'll commit the truncation fix + any further work as a single follow-up commit.
