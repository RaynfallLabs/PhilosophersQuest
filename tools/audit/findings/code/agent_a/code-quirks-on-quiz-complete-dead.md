---
id: code-quirks-on-quiz-complete-dead
dimension: code
severity: P2
title: `on_quiz_complete` hook is never called — Apollo and Cassandra quirks unreachable
status: open
systems: [quirks, quiz_engine]
evidence:
  - src/quirk_system.py:442 — `def on_quiz_complete(self, mode, subject, score, correct_count, wrong_count, success, ...)` defined
  - src/quirk_system.py:447-454 — Apollo (#23): max-chain hits with weapon, tracked only via `on_quiz_complete`
  - src/quirk_system.py:456-461 — Cassandra (#12): pass threshold with >=2 wrong, tracked only via `on_quiz_complete`
  - `grep -rn on_quiz_complete src/` returns ZERO callers — the hook is dead code
  - src/quiz_engine.py:371-380 — `_end(success)` fires the per-quiz `callback(result)` but no `on_quiz_complete` invocation
verified: true
discovered: 2026-05-15

---

## What's wrong

The `QuirkSystem.on_quiz_complete` hook (quirk_system.py:442) is defined but never invoked anywhere in the codebase. A simple `grep -rn on_quiz_complete src/` returns only the definition.

This silently breaks two quirks:
- **Apollo (#23)** — "10 max-chain hits with current weapon's max_chain_length on math chain mode". Counter `max_chain_hits` is only incremented inside `on_quiz_complete`. Unlockable in theory; un-incrementable in practice.
- **Cassandra (#12)** — "Pass 10 threshold quizzes with ≥2 wrong answers". Counter `cassandra_scrapes` is only incremented inside `on_quiz_complete`. Same fate.

Neither quirk will ever unlock in the game's current state. Both are listed in `_QUIRK_PROGRESS` (quirk_system.py:1131-area) so the encyclopedia/quirks UI will still show them at 0% progress with no path to advancing them — a player who stares at the rubric and tries to chain-hit ten times accomplishes nothing.

A parallel dead hook is `on_disease_drain` (filed separately as `code-quirks-on-disease-drain-dead`).

## How to reproduce / where it fires

1. Open the Quirks screen (W key).
2. Find Apollo (#23) — progress reads 0/10 max-chain hits.
3. Equip a weapon with `max_chain_length` of, say, 5.
4. Get into 100 combats, max-chaining every time.
5. Apollo progress remains 0/10.

Trace verifying it can't fire:
- Where in the codebase would `on_quiz_complete` be called? It needs `mode`, `subject`, `score`, `correct_count`, `wrong_count`, `success` — i.e., everything from `QuizResult` plus mode. The natural call site is wherever quizzes finish (i.e., in the `_end` of `quiz_engine.py` or in the per-caller `callback`).
- Neither location currently calls it. Confirmed by `grep`.

## Suggested fix

Two possible call sites; either works:

**Option A** (centralized, recommended): Add the call inside `QuizEngine._end` at quiz_engine.py:371. But `QuizEngine` does not know about `QuirkSystem`. Pass it in via constructor, or expose a second hook similar to `on_answer`. Pattern:

```python
# in QuizEngine.__init__
self.on_quiz_complete: callable | None = None

# in _end
if self.on_quiz_complete:
    self.on_quiz_complete(self.mode.value, self.subject, self.score,
                          self.correct_count, self.asked_count - self.correct_count, success)

# in Game.__init__ (main.py)
self.quiz_engine.on_quiz_complete = self._on_quiz_complete_hook

# in Game (main.py)
def _on_quiz_complete_hook(self, mode, subject, score, correct, wrong, success):
    qs = getattr(self, 'quirk_system', None)
    if qs:
        qs.on_quiz_complete(
            mode=mode, subject=subject, score=score,
            correct_count=correct, wrong_count=wrong, success=success,
            while_blinded=self.player.has_effect('blinded'),
            while_confused=self.player.has_effect('confused'),
            while_hallucinating=self.player.has_effect('hallucinating') or self.player.has_effect('hallucinating_pot'),
        )
```

**Option B** (per-caller): Add the call to each `on_complete` callback in game_combat.py (combat), game_magic.py (scrolls/wands/spells), food_system.py (cooking/harvest), etc. More invasive but allows site-specific filtering.

## Notes

Encyclopedia/quirks UI shows progress for these quirks based on a counter that never increments. Players who read the unlock condition and try to satisfy it will be confused and frustrated — this is a P2 because it's a silent feature failure across two visible-to-player quirks.
