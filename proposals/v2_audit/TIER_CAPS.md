# Universal Tier Caps (Absolute Grade Levels)

User's explicit grade mapping (multiple confirmations):
- T1 = 5th grade (~age 10)
- T2 = 6th grade (~age 11)
- T3 = 7th grade (~age 12)
- T4 = 8th grade (~age 13)
- T5 = 9-10th grade (~age 14-16)
- Above grade 10 → DROP from active quiz pool

## Absolute scorer caps

Combine Flesch-Kincaid grade level + per-subject jargon penalty.

```
def tier_for(fk_grade, jargon_score):
    if jargon_score >= 90 or fk_grade > 10:
        return None  # drop to dropped/ file
    if fk_grade <= 5 and jargon_score < 30:
        return 1
    if fk_grade <= 6 and jargon_score < 40:
        return 2
    if fk_grade <= 7 and jargon_score < 60:
        return 3
    if fk_grade <= 8 and jargon_score < 90:
        return 4
    if fk_grade <= 10:
        return 5
    return None
```

## Flesch-Kincaid grade level

```
FK = 0.39 × (words / sentences) + 11.8 × (syllables / words) - 15.59
```

Use the `textstat` package if available, otherwise compute inline (syllable counter: count vowel groups).

Apply to question stem ONLY (not choices/context — those are often shorter or vary widely).

## Topic coverage rule (CRITICAL — user emphasized)

After re-tier:
1. Cluster bank's questions by topic (keywords from stems + named entities + context tags if present)
2. For each topic with ≥3 questions in the bank:
   - If after re-tier a tier has 0 representatives of that topic AND another tier has the topic — generate 2-4 NEW questions at the empty tier
   - New questions must fit that tier's caps
3. Goal: every major topic has coverage at T2-T4 (T1 already covered by recent rebuild; T5 doesn't need coverage parity)

## Over-T5 items

Questions whose FK > 10 OR jargon ≥ 90 → move to `data/questions/dropped/<subject>.json`.
Keep them in the file (good source material) but they NEVER enter the active quiz pool.

The active bank loader only reads `data/questions/<subject>.json`, not `dropped/`.
