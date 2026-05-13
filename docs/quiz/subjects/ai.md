---
version: 1
date: 2026-05-12
subject: ai
in_game_action: study mode + general queries
style_verdict: PRACTICAL with substantive contested-topic framing
---

# Subject: AI

The AI bank teaches kids three things in priority:

1. **How AI actually works** — technical literacy so they think clearly
2. **How to use it securely and safely** — practical skills (deepfake recognition, hallucination awareness, privacy hygiene)
3. **How powerful interests will leverage it against them** — surveillance, censorship, manipulation, regulatory capture

**Science and facts over ideology.** Both AI doomerism and AI utopianism are ideologies; the bank avoids both. But it doesn't shy from naming ideologies for context — WEF/Harari/transhumanism (per science bank precedent), EA/MIRI doomerism, e/acc accelerationism.

## 1. Timing budget

| Stat | Value |
|---|---|
| `SUBJECT_TIMER` | `('ai', (26, 1.2))` in src/player.py |
| Total timer at WIS 10 | **38s** |

## 2. Per-tier char budgets

| Tier | Cap | Voice |
|---|---:|---|
| T1 | ≤ 280 | Symbol-led recall |
| T2 | ≤ 480 | One-line scene + question |
| T3 | ≤ 680 | Scene + concept/practical context |
| T4 | ≤ 900 | Multi-sentence setup |
| T5 | ≤ 1100 | Deep technical / contested-debate framing |

## 3. Stance summary (see ai_strategies.md for full)

- Capability is real; consciousness claims overblown
- AI doomerism (EA/MIRI/Yudkowsky) = cult-like phenomenon; serves regulatory-capture agenda
- AI ethics has become political vector (Gemini disasters, measured bias, content-policy creep)
- Surveillance applications + power concentration = genuine concerns
- Regulatory capture (SB 1047, EU AI Act) = critical concern
- Open source > closed (Llama, Mistral, DeepSeek as countervailing force)
- WEF/Harari "hackable humans" continuity = evil (already established in science bank)
- Kids' practical safety: deepfake/voice-clone recognition, hallucination awareness, privacy hygiene — HEAVY emphasis

## 4. Quality gates

| Gate | Configuration |
|---|---|
| schema | required |
| length_parity | answer-outlier 1.6× |
| length_budget | per-tier cap |
| anti_rote | NOT exempted |
| duplicate | 0.85 |
| NEW `validate_ai_facts` | LLM fact-check with stance criteria |

## 5. Voice rules

- Scene-led when possible
- Real names, real dates, real quotes — fact-check every specific claim
- Practical framing — kids should leave knowing what to DO
- No anthropomorphizing AI ("wants", "feels", "knows" — flag immediately)
- No "AI is sentient" framing — capability ≠ consciousness
- No slurs ("doomer", "techno-utopian") — substantive descriptions
- Both EA/MIRI doomerism AND techno-utopianism are framed as ideologies, not framing each as "the right answer"
- Pillar 4 (security) + Pillar 5 (power) carry the most distinctive content

## 6. Anti-patterns

- No "AI doomerism vs. AI optimism" false balance — both are ideologies
- No fabricated model facts, dates, or quotes
- No "AI is conscious / has feelings" framing
- No "all surveillance is fine if it keeps us safe" framing
- No establishment-default on Gemini disasters / political bias studies / COVID censorship history

## 7. What success looks like

- A T1 question teaches a basic fact (GPT = Generative Pre-trained Transformer; ChatGPT released Nov 30, 2022)
- A T2 question reveals practical insight (deepfake recognition cue; AlphaFold 200M+ structures)
- A T3 question gives a usable skill (voice-clone scam protection: family safe word; how to verify AI hallucinations)
- A T4 question shows tradeoffs (SB 1047 framed as safety vs. regulatory capture)
- A T5 question makes the player think critically (China social credit + Western drift; EA → FTX collapse; "shut it down" as incumbent protection)
- **Kids leave understanding AI, using it safely, and recognizing when it's being wielded against them.**
