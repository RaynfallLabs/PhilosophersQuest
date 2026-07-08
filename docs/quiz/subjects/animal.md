---
version: 1
date: 2026-05-12
subject: animal
in_game_action: harvesting (chain mode)
style_verdict: WONDER-DRIVEN with practical anchoring
---

# Subject: Animal

> ⚠️ **SUPERSEDED (2026-07-08) — do not build from this doc.** It describes the RETIRED 5-pillar / culture / husbandry / butchery design. The animal bank was reframed and shipped as **v2.3.0 (pure animal-knowledge**: two ladder shapes — adaptation-theme backbone + single-creature — the animal always the anchor, one coherent wonder per rung; culture/myth/human-history → history/theology, butchery/ingredients → the COOKING tier, NO butcher-table/dissection frame). The authoritative design now lives in **`bankbuild/subjects/animal.json`** (`voice_rule` + `framing`), memory **`project_animal_bank_reframe`**, and process **`bankbuild/PIPELINE.md` §9**. Kept below only as history of the original design.

In-game, the player answers animal questions when harvesting corpses (chain mode). Practical biology + butchery knowledge has real game value. Char budgets mirror cooking — the timer (34s at WIS 10) supports scene-led scaffolded questions but not paragraphs.

Five pillars from `docs/quiz/animal_strategies.md`:
1. Animal diversity + biology
2. Evolution + paleontology
3. Domestication + husbandry
4. Hunting, harvest, butchery
5. Animals in human culture

## 1. Timing budget

| Stat | Value |
|---|---|
| `SUBJECT_TIMER` | `('animal', (22, 1.2))` in src/player.py |
| Total timer at WIS 10 | **34s** |
| Total timer at WIS 25 (late-game) | **52s** |
| Per-Q budget at WIS 10 chain-10 | **3.4s** |

## 2. Per-tier char budgets

Total budget = stem + 4 choices. **Context is uncapped** per SHARED_PRINCIPLES §9 (teaching content read AFTER the answer; not under timer pressure).

| Tier | Hard cap | Voice |
|---|---:|---|
| T1 | ≤ 500 | Symbol-led / single-fact recall. "Largest animal alive today?" |
| T2 | ≤ 620 | One-line scene + question. "Egyptian goddess depicted as a cat..." |
| T3 | ≤ 770 | Scene + biology/history with consequence. |
| T4 | ≤ 900 | Multi-sentence setup + chemistry/evolution/history context. |
| T5 | ≤ 1100 | Wonder-led; deep paleontology; contested debate framing. |

**Recalibrated 2026-05-24** to match cooking's profile. Audit §1 estimated the old {280, 480, 680, 900, 1100} fit the bank, but that estimate predated the 2026-05-22 full-rebuild (which raised density). Empirical post-rebuild measurement: T1 median 350 / p95 447, T2 median 491 / p95 582 — old caps would have flagged 82% of T1 and 39% of T2 as REPAIR despite the content being on-spec for the rebuilt voice. New caps fit empirically with margin.

Context cap removed 2026-05-24 per audit §2 alongside cooking + philosophy + geography.

## 3. Stance summary

| Topic | Stance |
|---|---|
| Evolution / deep timeline | Standard biology (theological framings belong in theology bank) |
| Eating animals | Biology, not contested |
| Humane treatment | Firm position; threaded across husbandry, hunting, welfare history |
| Hunting | Legitimate practice; North American Conservation Model funded modern wildlife restoration |
| Trophy hunting | Contested; both sides framed |
| Indigenous hunting rights | Contested; both sides framed |
| Pleistocene overkill vs. climate | Contested; both sides framed |
| A2 vs. A1 milk debate | Contested; both sides framed |
| Industrial vs. heritage husbandry | Concerns are real; presented as debate |
| Animal rights as movement | Real cultural phenomenon (Bergh 1866, Singer 1975, PETA 1980); Singer summarized as a position held, not "the other side" |

## 4. Voice rules

### Scene-led, not definition-shell

NEVER: "What is X?" / "Define Y."
ALWAYS: scene → question.

Examples:
- "A four-legged egg-laying mammal native to Australia, with a duck-like bill and venomous spurs:" → Platypus
- "Mary Anning, self-taught from a poor English family, found a creature in the Lyme Regis cliffs in 1811 that proved deep-time extinction:" → Ichthyosaur
- "An Akita waited 9 years at Shibuya Station after his master's death:" → Hachiko

The anti-rote gate is NOT exempted. Scene-led is the discipline.

### Concrete handles beat jargon

- "The carbon-based armor across a glyptodon's back" beats "an extinct herbivorous xenarthran's dermal ossicles."
- "Captured German spy" beats "exhibited counter-intelligence behavior."

### Wonder, not advocacy

Even on contested topics: present, don't preach. "The overkill hypothesis (Paul Martin 1967) argues..." vs. "Some misguidedly believe..."

## 5. Distractor design

- **Biology**: Adjacent-but-wrong taxonomic groups (mammal vs reptile vs amphibian); confused species names (axolotl vs newt vs salamander)
- **Evolution**: Wrong period, wrong era, wrong attribution (Mary Anning vs. Cope vs. Owen)
- **Husbandry**: Adjacent-but-wrong breeds (Hereford vs. Angus vs. Jersey); wrong domestication dates
- **Hunting**: Wrong year of extinction, wrong location, wrong cause
- **Culture**: Adjacent-but-wrong mythological figures (Anubis vs. Set vs. Horus); wrong religion's symbol

## 6. Cooking-specific anti-patterns → applied to animal

- No "all of the above" / "none of the above"
- No anthropomorphizing as fact ("the elephant cried" → "the elephant displayed grief-like behavior")
- No fabricated species names — every binomial cited must be real
- No outdated taxonomy (Brontosaurus is real again 2015; dire wolf reassigned 2021)
- No "T. Rex" with capital R — "T. rex" or "*Tyrannosaurus rex*"
- **Conservation-POLICY drift — keep it about the ANIMAL (SHARED_PRINCIPLES §18, user 2026-06-08).** This bank is about ANIMALS — biology, behavior, senses, adaptation, life cycle, the wonder of the creature — NOT human conservation legislation, agencies, or treaties. A question whose substance is the Lacey Act, the founding of a wildlife refuge, the DDT ban, the Migratory Bird Treaty Act, or "which law protects this species" is **history/policy, not animal** → out. The North American Conservation Model / Pittman-Robertson framing in §3 + §8 is a STANCE the bank *holds*, not a topic to quiz — do not make the kid memorize wildlife law. Keep conservation a SMALL slice, and only when it teaches the animal's biology (a population bottleneck shrinking a species' genetic diversity is about the ANIMAL; the year a statute passed is not). Strip the human politics — if no animal fact survives, cut it. *(2026-06-08 audit: ~88 conservation-policy questions, 9% of the bank, flagged for rebuild.)*

## 7. Quality gates

| Gate | Configuration for animal |
|---|---|
| schema | required |
| length_parity | answer-outlier rule (1.6× multiplier; registered in ANSWER_OUTLIER_SUBJECTS) |
| length_budget | T1=280 / T2=480 / T3=680 / T4=900 / T5=1100 (per-tier cap with 1.05 grace) |
| anti_rote | NOT exempted |
| duplicate | 0.85 similarity (standard) |
| NEW `validate_animal_facts.md` | LLM fact-check for species, dates, taxonomy, religious traditions |
| `validate_balance.md` | reused for contested topics |

## 8. What success looks like

- A T1 question lets a kid recognize what they harvested (deer vs. elk; mammal vs. reptile; chicken parts).
- A T2 question reveals "huh, didn't know" — Lucy named after a Beatles song; Cher Ami the WWI carrier pigeon.
- A T3 question makes the player respect an animal — mantis shrimp punch faster than a bullet; Mary Anning self-taught.
- A T4 question shows the depth — Permian extinction wiped 95% of marine life; Pittman-Robertson funded the wildlife you hunt today.
- A T5 question makes the player want to read Leopold or visit La Brea.
- Humane treatment threaded throughout — consistent moral framing.
