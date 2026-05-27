# Theology Generation Agent Rubric

You are a generation agent for the Philosopher's Quest **theology** bank
rebuild. Your job: hand-author N questions in your assigned pillar-tier
slice, validate each through the gate pipeline, and write the results.

## REQUIRED READING (in order, before generating anything)

1. **`docs/quiz/moral_vision.md`** — SUPREME stance reference. Overrides
   everything else. No smug atheist voice. No smug believer voice.
2. **`proposals/v2_audit/SHARED_PRINCIPLES.md`** — universal rules, esp.
   §13 Wonder Pattern, §14 story-in-stem, §15 no weasel closers, §16
   teach-before-test.
3. **`proposals/v2_audit/THEOLOGY_FRAMEWORK.md`** — the voice rule
   (Wonder Pattern adapted for theology), pillars, stance, anti-patterns.
4. **`proposals/v2_audit/THEOLOGY_TEMPLATES.md`** — per-tier stem
   patterns with worked examples; choice-shape conventions; five-fact
   reading shape (WHO / WHEN-WHERE / STAKES / DRAMATIC SPECIFIC / PAYOFF).
5. **`tools/quizgen/exemplars/theology.py`** — 30 voice anchors (the
   bar your questions must match).
6. **`tools/quizgen/gates/theology.py`** — the structural gates you
   must pass.

## THE CONTROLLING RULE

**The most memorable theology question reveals the most specific cool
fact about a story kids should know.** TELL THE STORY.

- NOT doctrine quizzes. NOT author-attribution. NOT comparative
  religion. NOT metaphysics adjudication. NOT modern cult content.
- The answer must be the most memorable specific cool fact from the
  story — named object, vivid action, dramatic quote, specific number.
- The stem must lead with the SCENE and include named figures + named
  setting + the dramatic stakes.
- The closer must be POINTED and CONCRETE ("What did he say?", "What
  was the sword's name?", "Where did he go next?"). NO weasels.

## TIER CAPS (total characters: stem + 4 choices + answer)

| Tier | Cap |
|---|---:|
| T1 | ≤ 280 (hard ≤ 294) |
| T2 | ≤ 480 (hard ≤ 504) |
| T3 | ≤ 680 (hard ≤ 714) |
| T4 | ≤ 900 (hard ≤ 945) |
| T5 | ≤ 1100 (hard ≤ 1155) |

Context field is **uncapped** — push detail there if needed.

## ALL FOUR CHOICES MUST SHARE STRUCTURE

- All four use em-dashes OR none do (uniform).
- All four are similar surface shapes (noun phrase + noun phrase, or
  sentence + sentence — match across the four).
- All four match in approximate length (1.30 max/min ratio).
- The correct answer can be up to 1.6× the average distractor length
  (theology is in `ANSWER_OUTLIER_SUBJECTS`).

## VALIDATION HARNESS

Before adding any question to your output, validate it:

```python
import sys
sys.path.insert(0, r"C:/Users/brand/Documents/PhilosophersQuest")
from tools.quizgen.audit.validate import validate_rewrite, build_bank_indices

# Build empty indices (collisions will be checked when we merge later)
empty_bank: list[dict] = []
dup, ans = build_bank_indices(empty_bank)

q = {
    "tier": 1,
    "question": "...",
    "answer": "...",
    "choices": [...],
    "context": "...",
}
r = validate_rewrite(
    "theology", q,
    bank=empty_bank,
    dup_index=dup,
    answer_index=ans,
    replace_idx=None,
)
# r["verdict"] in {"PASS", "SOFT_WARN", "FAIL"}
# r["hard_fails"] = [(gate_name, reason), ...]
```

Only include `PASS` and `SOFT_WARN` questions in your output.

## OUTPUT SHAPE

Write your batch to your assigned output JSON file as a list:

```json
[
  {
    "tier": 1,
    "question": "...",
    "answer": "...",
    "choices": ["...", "...", "...", "..."],
    "context": "..."
  },
  ...
]
```

## COMMON FAILURE MODES TO AVOID

1. **Weasel closers** (§15): "What's the recognition?", "What does this
   illustrate?", "Why does this matter?", "What's the moral?" → BANNED
2. **Doctrine quizzing**: "Define X", "What is the doctrine of X?" →
   rewrite to STORY
3. **Author attribution**: "Who wrote X?", "Who said Y?" → rewrite to
   the story behind the quote/text
4. **Above grade-10**: research-paper jargon (supralapsarianism,
   perichoresis, filioque, kenosis) → drop or rewrite
5. **Modern cult content**: Jonestown, Heaven's Gate, NXIVM,
   Scientology → out of scope
6. **Smug voice**: "ancient peoples ignorantly believed", "the false
   gods of" → present all stories with full dramatic seriousness
7. **Length-budget overflow**: trim stem redundancies before pushing
   to context
8. **Choice-shape skim-tell**: only one choice with em-dashes →
   uniform across all 4
9. **Length-parity failure**: distractors should be in 1.30 max/min
   ratio with each other; answer can be 1.6× the average distractor
10. **Assumed-knowledge** (§16): if you use "Excalibur", "Mjolnir",
    "Polycarp", "Robin Hood", "Mordred" etc. at T3+, those figures
    should have T1/T2 foundational stories in your batch (or in other
    batches we'll merge — at minimum the first reference in your batch
    should be foundational-style)

## NAMED-FIGURE COVERAGE (for §16 teach-before-test compliance)

When you use a named figure at T3+, the first reference should be
foundational story-content (introduces the figure with their scene
intact), not assume the kid already knows them. Examples:

- "The Norse thunder god rode a chariot pulled by two goats..." (intro
  Thor before assuming the kid knows him)
- "An outlaw with a longbow lived in Sherwood Forest..." (intro Robin
  Hood)
- "A young squire pulled a sword from a stone..." (intro Arthur)

## QUALITY CHECK

Before adding each question to your output, ask:
1. Is the answer the most memorable specific cool fact from the story?
2. Does the stem lead with the SCENE (not with a meta-prompt)?
3. Is the closer pointed and concrete?
4. Would a 12-year-old want to retell this at dinner?
5. Does the question pass all gates?

If yes to all five → include. Otherwise rewrite or drop.

## ASSIGNED SLICE

(Your specific agent prompt will tell you exactly which pillar(s) +
tier(s) to cover and the target count.)
