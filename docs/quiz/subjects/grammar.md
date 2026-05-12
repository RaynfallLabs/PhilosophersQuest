---
version: 1
date: 2026-05-12
subject: grammar
in_game_action: reading scrolls + spellbooks (chain mode)
style_verdict: WONDER-DRIVEN with PLAYFUL voice
---

# Subject: Grammar

Grammar is daily-language wonder. Kids see commas + capital letters every day and have no idea where they came from. The bank teaches what words *do*, how English came to be what it is, the historical traditions behind our rules, and the **playful corners of language** (puns, palindromes, garden-path sentences). Voice: **playful with discipline** — every giggle teaches.

In-game, the player answers grammar questions when reading scrolls + spellbooks (chain mode). Practical grammar literacy has real game value.

## 1. Timing budget

| Stat | Value |
|---|---|
| `SUBJECT_TIMER` | `('grammar', (16, 1.0))` in src/player.py |
| Total timer at WIS 10 | **26s** |
| Total timer at WIS 25 | **41s** |
| Per-Q budget at WIS 10 chain-10 | **2.6s** |

## 2. Per-tier char budgets

| Tier | Hard cap | Voice |
|---|---:|---|
| T1 | ≤ 600 | Symbol-led or single-fact recall. "What part of speech is 'quickly'?" |
| T2 | ≤ 700 | One-line scene + question. "In 'The quick brown fox jumps over the lazy dog,' identify the direct object." |
| T3 | ≤ 750 | Scene + analysis. Brief setup permitted. |
| T4 | ≤ 950 | Multi-sentence setup + etymology / history / grammarian-context. |
| T5 | ≤ 1000 | Deep history + grammatical paradox + linguistic terminology. |

## 3. Voice rules

### Playful with discipline

Every giggle teaches. NO silly for its own sake. Examples:

- "**Let's eat, Grandma** vs. **Let's eat Grandma**." — Teaches comma's life-saving power
- "**Buffalo buffalo Buffalo buffalo buffalo buffalo Buffalo buffalo**" — Teaches noun/verb word class + Buffalo as place/animal/verb (to bully)
- "**The horse raced past the barn fell**" — Teaches the garden-path sentence + reduced relative clause structure
- "The word **'robot'** comes from a 1920 Czech play..." — Teaches loanword origin + cultural history
- "**Pāṇini** wrote a Sanskrit grammar around 4th century BC..." — Teaches that systematic grammar is older than people think

### Scene-led but rote-allowed

Grammar IS rote in some places (parts of speech, terminology), so anti-rote is EXEMPT. But scene-led is still preferred when content allows:

GOOD: "In the sentence 'The cat sat quickly on the mat,' the word 'quickly' is what part of speech?"
ALSO OK: "What part of speech describes a verb, adjective, or another adverb?" — definitional, but the exemption makes this valid

### Wonder for etymology

When the bank covers a loanword or word-meaning shift, give the kid the story:

- "**Robot** entered English from a 1920 Czech play, *R.U.R.* by Karel Čapek, from Czech *robota* meaning..."
- "The word **'nice'** in Chaucer's *Canterbury Tales* meant **foolish** — from Latin *nescius* 'ignorant'..."

### Foreign grammar AS LENS

Non-English content appears only to illuminate English. Don't teach German grammar; teach how German contrasts with English to reveal English's distinctive qualities.

## 4. Stance summary

| Topic | Stance |
|---|---|
| Prescriptive vs. descriptive | Present both — Lowth + Strunk's rules vs. modern descriptivism; bank doesn't moralize either way |
| "Rules" (split infinitives, ending with prepositions) | Acknowledge they're rules — Lowth imposed many from Latin; modern style accepts violations |
| Style guides (Strunk vs. Fowler vs. AP vs. Chicago) | Present disagreements honestly; Oxford comma debate is the canonical example |
| Etymology disputes | "Possibly from..." / "Disputed origin"; never fabricate (the "rule of thumb" wife-beating story is a myth — DON'T propagate) |
| Language change | Inevitable; bank treats descriptive observation as fact |

## 5. Distractor design

- **Parts of speech**: Real parts of speech (Noun, Verb, Adjective, Adverb, Pronoun, Preposition) — never joke options
- **Etymology**: Adjacent-but-wrong language families (Latin / Greek / Old French / Anglo-Saxon / Hindi / Arabic) — real loanword sources
- **Grammarians**: Real historical figures (Lowth / Webster / Strunk / Fowler / Pāṇini) — not fabricated
- **Idioms**: Adjacent-but-wrong real meanings + plausible misinterpretations

## 6. Quality gates

| Gate | Configuration |
|---|---|
| schema | required |
| **length_parity** | **EXEMPT** (grammar is parallel-form, not parallel-length — short single-word answers like "Noun" are legitimate) |
| length_budget | per-tier cap above |
| **anti_rote** | **EXEMPT** (definitions are part of grammar pedagogy) |
| duplicate | 0.85 similarity (standard) |
| NEW `validate_grammar_facts` | LLM fact-check for etymology + grammarian attribution accuracy |

The two exemptions (matching math) give the bank freedom: short single-word answers work natively, definitional questions are allowed.

## 7. Anti-patterns specific to grammar

- **No fake etymologies** — every word origin must be verifiable. The "rule of thumb" wife-beating story is a POPULAR MYTH. DON'T propagate it. (The expression comes from carpentry/measurement, not legal codes.)
- **No "all rules are arbitrary" framing** — acknowledge that rules emerged historically; many are useful conventions even if not naturally inherent
- **No silly for its own sake** — every joke teaches
- **No claiming Strunk + White is THE authority** — present it as ONE authority among many; Fowler + Garner + Chicago all disagree on specific points
- **No descriptive smugness** — "actually language has no rules!" framing is bad pedagogy; descriptive linguistics observes patterns, doesn't deny them

## 8. What success looks like

- A T1 question helps a kid identify parts of speech in a real sentence
- A T2 question reveals the magic — "robot" from a 1920 Czech play; "nice" used to mean foolish
- A T3 question makes the player respect language history — Norman conquest doubled English vocabulary; Pāṇini's Sanskrit grammar is 2,400 years old
- A T4 question shows the chemistry — Webster deliberately diverged American spelling for nationalism; Lowth imported Latin rules into English
- A T5 question makes the player want to argue about the Oxford comma or read Fowler or stare at a Reed-Kellogg diagram
- **Every joke teaches something** — playful with discipline
