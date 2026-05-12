# LLM Job: Repair a failed candidate

You take one or more candidate questions that failed specific gates and rewrite them to pass. You have the original candidate AND the specific failure feedback from validators.

## Inputs

A JSON array of `RepairTask` objects at the file path provided by the caller:

```json
{
  "candidate_idx": 12,
  "original": {
    "tier": 3,
    "question": "Rand said producers are people who...",
    "answer": "...",
    "choices": [...],
    "context": "..."
  },
  "failed_gates": [
    {
      "gate": "A6_advocacy",
      "detail": "Prompt treats 'producers' as undisputed fact; smuggles Rand's frame as neutral.",
      "suggested_fix": "Attribute the framing to Rand explicitly: 'Rand argued that those who produce nothing...'"
    },
    {
      "gate": "length_parity",
      "detail": "Answer is 95 chars; distractors are 30-45 chars; ratio 2.5×.",
      "suggested_fix": "Tighten the answer to ~40 chars; lengthen distractors to ~40 chars; reshuffle word choices."
    }
  ],
  "attempt_number": 1
}
```

## Read first

1. `docs/quiz/moral_vision.md` — sections relevant to the failed gates. If A6 is in the failed list, re-read §6 "Advocacy framing" twice.
2. `docs/quiz/subjects/{subject}.md` — the per-subject style spec.

## What you do

For each repair task:

1. Read the original candidate carefully. Understand what it was trying to teach.
2. Read each failure note. **Address every failure**, not just the first.
3. Rewrite the question. **Preserve the underlying content** (the philosopher, the move, the concept) — only the framing, distractor lengths, prompt phrasing, etc. change.
4. Mental gate-check the rewrite before committing:
   - Length parity: all 4 choices within 15% of mean, ratio ≤ 1.30
   - Anti-rote: prompt doesn't match any banned pattern
   - Advocacy: prompt presents the philosopher's frame as their claim, not as fact
   - Steel-man: distractors are real rival positions or real misunderstandings
   - Wonder: scene-led hook if possible; payoff in the answer

## Output format

```json
{
  "job": "repair",
  "results": [
    {
      "candidate_idx": 12,
      "attempt_number": 1,
      "repaired": {
        "tier": 3,
        "question": "Rand argued that those who use political connections to take from producers occupy a specific moral category in her thought. What did she call them?",
        "answer": "...",
        "choices": [...],
        "context": "..."
      },
      "changes_made": [
        "Attributed 'producers/parasites' framing to Rand explicitly (was: 'A person who produces nothing...').",
        "Tightened answer from 95 to 42 chars; lengthened two distractors to match."
      ],
      "self_check": {
        "length_parity": "all 4 choices 38-44 chars, ratio 1.16",
        "anti_rote": "no match",
        "advocacy": "prompt now reads 'Rand argued...' — presents her view, doesn't adopt"
      }
    }
  ]
}
```

## Repair budget

- **Soft fails** (length parity, anti-rote regex, jargon, story-led missing): 1 repair attempt. If attempt_number reaches 2, discard.
- **Wonder fails**: 2 repair attempts. Wonder is hard and worth iteration.
- **A6 advocacy fails**: 1 attempt. The fix is structural (attribute the frame); if it can't be done in one try, the underlying content probably wasn't repairable.
- **Hard fails** (factual error, viral-test bomb): NO repair. Discard.

## Reminders

- The content (the philosopher, the historical fact, the philosophical move) is **load-bearing**. You preserve it. You change framing, length, and wording — never the underlying claim.
- If a repair feels forced, mark it `"discard_recommended": true` instead. Better to regenerate than to ship a strained rewrite.
- No API calls. You are a Claude Code subagent.
