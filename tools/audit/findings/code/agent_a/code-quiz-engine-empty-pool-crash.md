---
id: code-quiz-engine-empty-pool-crash
dimension: code
severity: P3
title: Quiz engine crashes with IndexError if a subject's question file is missing or empty
status: open
systems: [quiz_engine, question_loading]
evidence:
  - src/quiz_engine.py:84-94 — `load_questions` silently returns `[]` if file is missing or unparseable, prints WARNING to stderr
  - src/quiz_engine.py:114-133 — `start_quiz` builds an empty `pool` if `all_qs` is empty (all the fallback branches fall through)
  - src/quiz_engine.py:235-244 — `_next_question` indexes `self._pool[self._pool_idx]` with no bounds-or-empty check
verified: true
discovered: 2026-05-15

---

## What's wrong

`load_questions` (quiz_engine.py:84) catches `FileNotFoundError` and returns `[]` after printing a warning to stderr. The warning does not prevent execution. Downstream, `start_quiz` (line 96) attempts to build a deck from `all_qs`:

```python
if deck_key not in self._decks:
    pool = [q for q in all_qs if q.get('tier', 1) == tier]
    if not pool:
        for fallback_t in range(tier - 1, 0, -1):
            pool = [q for q in all_qs if q.get('tier', 1) == fallback_t]
            if pool:
                break
    if not pool:
        pool = all_qs[:]
    pool = self._shuffle_unseen_first(deck_key, pool)
    self._decks[deck_key]    = pool
    self._deck_idx[deck_key] = 0
    self._last_q[deck_key]   = None
```

If `all_qs == []`, every branch leaves `pool` empty. The empty list is stored as the deck. Then:

```python
self._pool     = self._decks[deck_key]   # []
self._pool_idx = self._deck_idx[deck_key] # 0
self._next_question()
```

In `_next_question`:
```python
if self._pool_idx >= len(self._pool):   # 0 >= 0 → True, reshuffle empty
    reshuffled = self._shuffle_unseen_first(deck_key, self._pool)
    self._pool[:] = reshuffled
    ...
    self._pool_idx = 0
self.current_question = self._pool[self._pool_idx]   # IndexError: list index out of range
```

The traceback is caught by the main loop (main.py:4030-4036), so the game does not hard-crash. But the player sees an "Error: list index out of range" red message and the quiz silently aborts. State is left in STATE_QUIZ until the player ESCs.

Currently all 12 subjects in `SUBJECT_TIMER` have data files (`grep ls data/questions/*.json` returns all 12), so this bug is dormant. But:
- A new subject added without a JSON file would crash on first attempt.
- A corrupted JSON file (parse error) at present catches only `FileNotFoundError`, not `json.JSONDecodeError` — so any malformed JSON would surface as an unhandled exception during JSON load.

Looking at quiz_engine.py:87-93:
```python
try:
    with open(path, encoding='utf-8') as f:
        self._cache[subject] = json.load(f)
except FileNotFoundError:
    ...
```

A malformed JSON file (e.g., user edits and breaks the brackets) would raise `json.JSONDecodeError` which isn't caught here — propagates up through `start_quiz`, recovered to STATE_PLAYER by main.py's catch-all.

## How to reproduce / where it fires

Synthetic test (don't actually do this):
1. Rename `data/questions/math.json` to `math.json.bak`.
2. Start the game, swing at a monster.
3. `start_quiz('chain', 'math', ...)` runs. `load_questions('math')` prints "WARNING: Question file not found: ...", returns `[]`.
4. `start_quiz` builds empty deck.
5. `_next_question` → `self._pool[0]` → IndexError.
6. Player sees "Error: list index out of range" — combat aborted.

## Suggested fix

Defensive check in `_next_question`:

```python
def _next_question(self):
    if not self._pool:
        # No questions available for this subject -- fail gracefully
        self._end(success=False)
        return
    ...
```

And in `load_questions`, catch `json.JSONDecodeError` too:

```python
try:
    with open(path, encoding='utf-8') as f:
        self._cache[subject] = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    import sys
    print(f"WARNING: Question file unusable: {path} ({e})", file=sys.stderr)
    self._cache[subject] = []
```

Optional: in `start_quiz`, if pool is empty, log and immediately call `_end(success=False)` without ever calling `_next_question`.

## Notes

Dormant in current shipping content because all subject files exist and parse cleanly. P3 because the failure mode is silent player-facing error + aborted quiz. If a kid playing in an unfamiliar shell hits this in modified data, the cause will be opaque.
