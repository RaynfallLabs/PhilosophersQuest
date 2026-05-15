---
id: code-quirk-on-quiz-complete-never-called
dimension: code
severity: P2
title: `QuirkSystem.on_quiz_complete` defined but never called — Apollo and Cassandra quirks unreachable
status: open
systems: [quirks, quiz]
evidence:
  - src/quirk_system.py:442-461 — `on_quiz_complete` body handles Apollo (#23 max-chain math hits) and Cassandra (#12 threshold-quiz-with-2-wrong)
  - src/quirk_system.py — no internal call site
  - grep across `src/` — zero references to `on_quiz_complete` in any other module
  - src/main.py:2486-2500 — `_on_quiz_answer` calls `qs.on_quiz_answer` per-answer but never the per-completion hook
verified: true
discovered: 2026-05-15
---

## What's wrong
`QuirkSystem` defines a method `on_quiz_complete(mode, subject, score, correct_count, wrong_count, success, ...)` at `quirk_system.py:442`. Inside it, two named quirks are awarded:

- **Apollo (#23) — "Apollo's Perfection"**: granted after 10 math chain quizzes where `score >= weapon.max_chain_length` (a perfect chain). Reward: `_timer_bonus('math', 3)`.
- **Cassandra (#12) — "Cassandra's Persistence"**: granted after 10 threshold quizzes passed with ≥2 wrong answers. Reward: WIS +1.

Both quirks are documented in `_QUIRK_NAMES`, `_QUIRK_EFFECTS`, `_QUIRK_PROGRESS`, and the encyclopedia's quirks panel. The progress trackers `max_chain_hits` and `cassandra_scrapes` are configured. **But the method `on_quiz_complete` is never invoked.**

Grep across the entire `src/` tree shows no other module calls `qs.on_quiz_complete(...)`. The natural call sites would be:
1. The combat quiz callback in `combat.py:_callback` (post player_attack)
2. The threshold-quiz callbacks in `food_system.py`, `container_system.py`, `game_magic.py:_read_scroll`, etc.
3. Or centralised inside `quiz_engine._end()`

None of these invoke it. The `_on_quiz_answer` hook (`main.py:2466-2500`) calls `qs.on_quiz_answer(...)` per individual answer — that's a different code path. The per-completion hook is dead.

Consequence: Apollo and Cassandra cannot unlock through normal play. Their progress trackers stay at 0 forever. The encyclopedia displays them as 0% progress with no way to advance.

## How to reproduce / where it fires
1. Play through 50 floors landing 100+ max-chain math attacks (perfect chains on weapon's max length).
2. Check the Quirks panel — Apollo: 0% unlocked.
3. Same for Cassandra: pass 10+ threshold quizzes with 2 wrong answers each. Still 0%.

Call graph (the failure):
- `player_attack` → chain quiz → `combat.py:_callback` → on_complete → game advances. **No `on_quiz_complete` call.**
- `_read_scroll` → threshold quiz → on_complete → effect applied. **No `on_quiz_complete` call.**

## Suggested fix
Two options:

**Option A — Wire into the quiz engine `_end()`.** Add a second on-end hook similar to `on_answer`:

```python
# quiz_engine.py
self.on_complete = None   # optional callable(QuizResult, mode, subject)

def _end(self, success):
    ...
    if self.on_complete:
        self.on_complete(result, self.mode, self.subject)
    if self.callback:
        self.callback(result)
```

Then in `main.py:__init__`, after `self.quiz_engine.on_answer = self._on_quiz_answer`, set `self.quiz_engine.on_complete = self._on_quiz_complete` and add the method that forwards to `quirk_system.on_quiz_complete`.

**Option B — Call from each on_complete callback** (more places to touch, more drift risk). Add `qs.on_quiz_complete(...)` to every quiz callback that closes a quiz: combat callback, scroll callback, identify callback, harvest callback, cooking callback, container callback, prayer callback, recall lore callback, hack reality callback, learn spellbook callback. Brittle.

Option A is the canonical fix.

## Notes
The consensus baseline mentions the `on_teleport` double-count bug (now fixed) but did not flag this. This is a new finding in the quirk counter graph and explains why those two specific quirks were unreachable.

Inspecting other once-only-style quirks: Tiresias, Anansi, Medusa episode all fire correctly from `on_quiz_answer` (per-answer hook). Apollo and Cassandra need per-completion data that only exists after the quiz session ends. They're the only quirks blocked.
