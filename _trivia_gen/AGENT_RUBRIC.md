# Trivia Generation Agent Rubric

You are a generation agent for the Philosopher's Quest **trivia** bank rebuild. This bank is the **geek-dad canon** — the user's deep-cut canon for his kids. *Ready Player One* vibe. Make them want to GO seek out the source.

## REQUIRED READING FIRST (in this order)

1. **`docs/quiz/moral_vision.md`** — SUPREME stance reference
2. **`proposals/v2_audit/SHARED_PRINCIPLES.md`** — esp. §13 Wonder Pattern, §14 story-in-stem, §15 no weasel closers, §16 teach-before-test
3. **`proposals/v2_audit/TRIVIA_FRAMEWORK.md`** — the voice rule (Easter Egg Pattern + cultural-osmosis carve-out + 10 spoiler-allowed franchises)
4. **`proposals/v2_audit/TRIVIA_TEMPLATES.md`** — per-tier stem patterns
5. **`docs/quiz/subjects/trivia.md`** — canonical stance (geek-dad-canon framing, 2026-05-14)
6. **`docs/quiz/trivia_strategies.md`** — comprehensive 5-pillar content spec with hundreds of strategy IDs (your topic source-of-truth)
7. **`tools/quizgen/exemplars/trivia.py`** — 30 voice anchors
8. **`tools/quizgen/gates/trivia.py`** — the gates you must pass

## THE CONTROLLING RULE — Easter Egg Pattern

**The most memorable trivia question reveals a cool detail, scene, lore-nugget, or production fact that makes the kid want to GO experience the source — without ruining the story.**

- Lead with NAMED THINGS in the stem (people, places, dates, scenes, weapons, moves)
- Pay off with the most memorable specific cool fact
- Closer is POINTED and CONCRETE ("What did he say?", "What was the score?", "Who composed?", "What was the kill-screen level?")
- NO weasel closers ("What's the recognition?", "What does this illustrate?" — BANNED)

## CULTURAL-OSMOSIS CARVE-OUT (CRITICAL)

The bank traffics confidently in cultural touchstones. Facts that have crossed into broader cultural knowledge **independent of experiencing the source** are testable:

- Secret identities: Bruce Wayne = Batman, Clark Kent = Superman, Peter Parker = Spider-Man
- Origin stories: radioactive spider, Wayne parents in the alley, Krypton, gamma bomb, super-soldier serum
- Foundational setup: Frodo carries the Ring, Yoda is a Jedi Master, Cloud was in SOLDIER
- Decades-old culturally-memed lines: "Luke, I am your father", "I'll be back", "Inconceivable!", "I'm your huckleberry"

**Litmus test**: *"Could a kid who has never seen/read/played this still know this fact from broader culture?"*

## 10 SPOILER-ALLOWED FRANCHISES

For these — internal plot fair game (kids have seen them):
1. My Hero Academia
2. Hajime no Ippo
3. Harry Potter
4. Star Wars original trilogy (IV/V/VI)
5. MCU through Endgame (2008-2019, 23 films)
6. Toilet-Bound Hanako Kun
7. Dragon Ball (DB + DBZ — Super NOT in scope)
8. Scott Pilgrim
9. Princess Bride
10. Super Mario Bros Movie 2023

**Governing principle when uncertain: "If in doubt, include content but avoid spoiler."**

## TIER CAPS (total characters: stem + 4 choices + answer; context uncapped)

| Tier | Cap | Voice |
|---|---:|---|
| T1 | ≤ 280 (hard ≤ 294) | OBVIOUS — Pikachu, Mario, Sonic, Bruce Wayne = Batman, "Luke I am your father" |
| T2 | ≤ 480 (hard ≤ 504) | Casual fan — Akira director Otomo 1988, Pac-Man Iwatani pizza-slice |
| T3 | ≤ 680 (hard ≤ 714) | Real fan — DK kill screen Level 22, Howard's Cross Plains Texas 1932, Patty Patterson-Gimlin Oct 20 1967 |
| T4 | ≤ 900 (hard ≤ 945) | Deep fan — Mitchell vs Wiebe King of Kong, Eva episode 25/26 collapse, Watchmen smiley-face |
| T5 | ≤ 1100 (hard ≤ 1155) | Ready Player One — Minus World, Princess Bride opening Hardball II Amiga, Akira's Geinoh Yamashirogumi chorus |

## CHOICE-SHAPE RULES

- All four choices share dash structure (all em-dash, or none)
- Similar surface shapes (noun phrase + noun phrase, or sentence + sentence)
- Length parity 1.30 max/min between distractors
- Correct answer can be up to 1.6× the average distractor length (trivia is in ANSWER_OUTLIER_SUBJECTS)
- Plausible distractors from the same era / franchise / category

## BANNED CONTENT

- **Post-Endgame MCU** (Multiverse of Madness, Love and Thunder, No Way Home as a film, all Disney+ Marvel shows)
- **Disney-era Star Wars** (sequel trilogy, Mandalorian, Andor, Ahsoka, Rogue One, Solo)
- **Post-Attitude-Era wrestling** (post-WM18 March 17 2002)
- **Post-Legends MtG** (post-June 1994)
- **Modern D&D errata** (5e ancestry rewrites, alignment removal, sensitivity reads)
- **Plot spoilers OUTSIDE the 10 allowed franchises** — Sephiroth/Aerith, Sixth Sense ending, Keyser Söze, Snape's true allegiance (HP is allowed but apply judgment), Tony's snap is fine (MCU allowed)
- **Credulous cryptid framing** ("Bigfoot is REAL", "Atlantis DID exist")
- **Bare year-recall** as primary test without dramatic context

## VALIDATION HARNESS — every question

```python
import sys
sys.path.insert(0, r"C:/Users/brand/Documents/PhilosophersQuest")
from tools.quizgen.audit.validate import validate_rewrite, build_bank_indices

empty_bank: list[dict] = []
dup, ans = build_bank_indices(empty_bank)

q = {"tier": 3, "question": "...", "answer": "...", "choices": [...], "context": "..."}
r = validate_rewrite("trivia", q, bank=empty_bank, dup_index=dup, answer_index=ans, replace_idx=None)
# Only include r["verdict"] in {"PASS", "SOFT_WARN"}
```

## INCREMENTAL SAVE (recommended)

After every ~10 validated questions, save partial output to your assigned JSON file. Socket disconnects have hit prior runs — incremental saves preserve work.

## OUTPUT

Write your validated questions to your assigned file as a JSON array of question dicts.

## ASSIGNED SLICE

(Your specific agent prompt will tell you exactly which topic cluster to cover and the target count.)
