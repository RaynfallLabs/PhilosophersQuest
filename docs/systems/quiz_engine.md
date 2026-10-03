# Quiz Engine

**Status:** v2.18.0 (shipped 2026-10-02)
**Code:** `src/quiz_engine.py` (680 lines)
**Data:** `data/questions/<subject>.json` (12 subjects); `<save_dir>/quiz_history.json` (cross-game recency)
**Related docs:** [status_effects](status_effects.md), [combat](combat.md), [save_bonus](save_bonus.md), [identify_v3](identify_v3.md), [food_system](food_system.md), [magic](magic.md), [karma_prayer](karma_prayer.md), [containers_lockpick](containers_lockpick.md)

## Purpose
Every quiz-gated action in Philosopher's Quest routes through one engine. The engine owns the question deck, the quiz state machine, the timer, the scoring (chain / threshold), the per-run subject mastery that auto-passes cleared tiers, and the Tablet of Destinies' one-time reroll. "Knowledge is power" is a UI slogan — this file is what makes it mechanical.

## Design intent
The engine replaces every "random chance" roll in a traditional roguelike with a knowledge check. Combat attacks, equipping armor, lockpicking, cooking, praying, identifying — all funnel through `start_quiz(...)`. Four quiz modes cover the ways an action can be measured: threshold (do you know enough?), chain (how long can you stay right?), and the two escalator variants that climb the tier curve.

Two load-bearing rules shape everything else. **Zero-tolerance** (2026-05-29): one wrong answer ends a threshold quiz. There are no mulligans anywhere in the game except the Tablet of Destinies. **Chain v2** (v2.14.0, 2026-05-18): a wrong answer in a chain quiz **no longer zeros** the chain — the strike lands at whatever chain was achieved before the miss. Pressing SPACE mid-question locks in the current chain and strikes. These two rules together make the quiz the risk/reward engine: in chain mode, each new correct answer is "do I bank or push for more?" In threshold mode, every question is a cliff.

**Math-only timing** (post-2026-05-11): the on-screen countdown appears for exactly one subject — `math` (combat attacks). Every other subject is untimed by default. Combat was designated the pressure point because chain-mode plus a hostile monster is already a tension loop; everything else (identify, lockpick, equip, prayer, cook, magic, harvest, etc.) is read-the-question content the player should get to actually read. The `base_seconds` for each subject is still kept in `Player.SUBJECT_TIMER` and still routes through the timer wiring — but subjects other than math are called with `timed=False` (auto-detected if not forced) and the timer bar is never rendered.

**Per-run mastery** (shipped mid-2026): a `(subject, tier)` pair is "mastered" once every distinct question at that tier has been answered correctly within the current run. A mastered tier auto-passes with no question shown; in escalator modes the engine climbs to the next tier automatically (the player always fights at their frontier); if the whole reachable ladder is mastered, the quiz succeeds outright. Mastery is per-run — fresh games start empty. It persists in the save pickle so save/load mid-run keeps your progress; it is NOT in cross-game `quiz_history.json`.

**Escalator cap at T5**: `_escalate()` clamps `tier = min(tier + 1, 5)`. No subject has T6+ content; climbing beyond 5 would silently fall back to the T5 pool anyway.

**Tablet of Destinies reroll**: the artifact grants one re-ask per floor (not per-quiz). It's wired via `quiz_engine._reroll_flag`, read on `start_quiz` into `reroll_available`, consumed on first wrong answer, and the "used this floor" flag lives on `Game`. Works in both chain and threshold modes.

## Data model / schema

### `QuizMode` (Enum)
```python
THRESHOLD           = "threshold"           # Correct X of N (zero-tolerance)
CHAIN               = "chain"               # Score = chain length until wrong/timer/SPACE
ESCALATOR_THRESHOLD = "escalator_threshold" # Questions escalate tier each round
ESCALATOR_CHAIN     = "escalator_chain"     # Chain mode + tier climbs per rung
```

### `QuizState` (Enum)
```python
IDLE      # No active quiz
ASKING    # Question displayed, awaiting answer
RESULT    # Correct/wrong flash (RESULT_DISPLAY_TIME=0.8s / WRONG_DISPLAY_TIME=3.0s)
COMPLETE  # _end() called; callback fired
```

### `QuizResult` (dataclass)
```python
@dataclass
class QuizResult:
    success: bool
    score:   int   # chain length for chain modes; correct count for threshold modes
    correct: int
    asked:   int
```

### Question JSON row
Each file in `data/questions/<subject>.json` is a flat list of:
```json
{
  "question": "Which Greek letter denotes the ratio of a circle's circumference to its diameter?",
  "choices":  ["pi", "phi", "psi", "theta"],
  "answer":   "pi",
  "tier":     1
}
```
- `tier` (int, 1-5): the tier bucket for the deck. Missing → treated as tier 1.
- `answer` is compared **case-exact** after `strip()` (grammar capitalization bank requires this, 2026-06-01 fix).
- Choice order is **always shuffled** per question so the correct-answer position never leaks.

### Engine state (set by `start_quiz`)
| Field                     | Type              | Role                                              |
|---------------------------|-------------------|---------------------------------------------------|
| `state`                   | QuizState         | IDLE / ASKING / RESULT / COMPLETE                 |
| `mode`                    | QuizMode          | Current quiz mode                                 |
| `subject`, `tier`         | str, int          | Current pool key                                  |
| `required`                | int               | Threshold target (correct answers needed)         |
| `total_qs`                | int               | Max questions asked (threshold modes)             |
| `max_chain`               | int \| None       | Chain-mode auto-success ceiling                   |
| `timed`                   | bool              | True only for `math` by default                   |
| `timer_seconds`           | int               | Starting timer value (0 when untimed)             |
| `time_remaining`          | float             | Current countdown                                 |
| `score`                   | int               | Chain length (chain) or correct count (threshold) |
| `chain`                   | int               | Current chain length                              |
| `correct_count`           | int               | Right answers given                               |
| `asked_count`             | int               | Questions asked                                   |
| `reroll_available`        | bool              | Tablet of Destinies reroll pending                |
| `reroll_was_used`         | bool              | Reroll fired this quiz                            |
| `auto_passed`             | int               | Rounds auto-passed via mastery                    |
| `just_mastered`           | tuple \| None     | One-shot UI flag — (subject, tier) just mastered  |
| `celebrating`             | bool              | Showing MAX CHAIN banner before `_end`            |

### Persistent deck state
- `_decks: dict[(subject, tier) -> list[question]]` — shuffled pool for each key.
- `_deck_idx: dict[key -> int]` — next position to draw.
- `_last_q: dict[key -> question]` — avoid showing the exact-same question twice back-to-back on reshuffle.
- `_seen: dict[key -> set[str]]` — question texts already shown this run.
- `_recent: dict[key -> list[str]]` — bounded last-N questions, persisted to `<save_dir>/quiz_history.json` (`_CROSS_GAME_RECENT_CAP = 30`).

### Per-run mastery state
- `_retired: dict[(subject, tier) -> set[str]]` — questions correctly answered this run (retired from the deck).
- `_mastered: set[(subject, tier)]` — tiers whose every distinct question has been retired.
- `_tier_size: dict[key -> int]` — cached count of distinct questions at exactly that tier.

Mastery is persisted in the per-save pickle via `get_deck_state() / restore_deck_state()`. The pickled payload is **seen + retired + mastered only** — NOT the shuffled decks themselves. Decks rebuild from the current JSON on next `start_quiz`, so bank updates always take effect on load (old pickled decks were serving stale questions pre-fix).

## Flow — public API

### `QuizEngine.__init__()`
Builds an empty engine. Immediately calls `_load_cross_game_history()` which reads `<save_dir>/quiz_history.json` (if present) and seeds `_seen` so the first deck built per `(subject, tier)` pushes recently-shown questions to the back. Missing / corrupt file is non-fatal.

### `load_questions(subject) -> list`
Caches the subject's JSON (`data/questions/<subject>.json`) in `_cache`. Missing / malformed file: warns to stderr and caches `[]` (quiz will fail gracefully via the empty-pool guard).

### `start_quiz(mode, subject, tier, callback, threshold=3, max_chain=None, wisdom=10, timer_modifier=1.0, extra_seconds=0, base_seconds=None, total_qs=None, timed=None)`
The one entry point. Sets up pool + state, writes `reroll_available` from the sticky `_reroll_flag` (set by Game before the call), and either calls `_next_question()` or short-circuits to `_end(success=False)` if the pool is empty.

Timer policy:
- `timed=None` auto-detects: `timed = (subject == 'math')`.
- `timed=False`: `timer_seconds = 0`, `time_remaining = 0.0`. The tick loop and renderer both check `self.timed` and skip the countdown entirely.
- `timed=True`: `timer_seconds = round(base_seconds * timer_modifier) + extra_seconds`. If `base_seconds` is None (legacy callers), falls back to `(10 + wisdom)`.

Pool build order (identical for `start_quiz` and `_escalate`):
1. `pool = [q for q in all_qs if q.tier == tier]`
2. If empty, fall back to the nearest **lower** tier (tier-1, tier-2, …, 1).
3. If still empty, fall back to `all_qs[:]`.
4. `_shuffle_unseen_first(deck_key, pool)` — unseen questions placed before seen ones.

`callback(QuizResult)` fires exactly once from `_end`.

**Call sites** (one line per site shown; see Interactions below for the full map):
- `combat.py:1994` — chain-mode math attack (every melee + ranged shot)
- `game_combat.py:997` — wand (threshold-1 science at wand.tier)
- `game_combat.py:1081/1141` — ranged weapon miss paths
- `game_divine.py:289/369/609/680/805/1064/1076` — prayer / divine intercession / altar branches
- `game_magic.py:106/276/1270/2312/3119/3432/3473` — spell targeting / scroll / spellbook
- `food_system.py:428/489/566` — cook (threshold-1 cooking at outcome.tier)
- `container_system.py:103` — lockpick (threshold-1 economics)
- `game_encounters.py:453` — NPC-reward quizzes
- `game_menus.py:1499` — identify menu (one philosophy Q at `id_tier`)
- `main.py:3900/5026/5648/5707/5793/6585/6879` — equip armor/shield/accessory, scroll, mystery challenges, etc.

### `answer(choice: str) -> bool`
Submit the player's choice. No-op outside `ASKING`. Does case-exact `strip()`-compare against `current_question['answer']`. On correct: increments `correct_count`, `chain`, and calls `_record_correct_for_mastery()` (retires the question text; marks the tier mastered if every distinct question is retired). On wrong: chain is **not** zeroed. Updates `score` per mode. Fires `on_answer(is_correct)` hook. Transitions to `RESULT`.

### `update(dt: float)`
Called each frame with delta time in seconds. Handles:
1. Celebration timer (`MAX CHAIN!` banner for 1.5s before `_end`).
2. ASKING + timed: counts down `time_remaining`; on expiry, logs a wrong answer **without zeroing the chain** (chain-v2) and transitions to RESULT.
3. RESULT: counts down `result_timer`; on expiry, calls `_advance()`.

### `cancel_and_strike() -> bool`
Chain-combat-v2 SPACE handler. Freezes the current chain into `score` and ends the quiz immediately as success. Valid only in chain modes while `ASKING`. Downstream combat callback treats `score >= 1` as a landed strike at that chain, `score == 0` as a miss.

### `active` (property)
`state not in (IDLE, COMPLETE)`.

### `get_deck_state() / restore_deck_state(state)`
Save-system hooks. Persists ONLY `_seen`, `_retired`, `_mastered`. Decks rebuild from current JSON on next `start_quiz` — ensures bank updates always propagate to loaded games.

### `is_mastered(subject, tier) -> bool` / `mastered_tiers() -> set`
Public reads for UI (bestiary, character sheet, chronicle).

## Internal flow

### `_next_question()`
1. If `is_mastered(subject, tier)` → `_auto_pass_mastered_round()` and return.
2. Draw up to `len(_pool) * 2 + 1` candidates from the deck, skipping any question text already in `_retired[(subject, tier)]`.
3. On deck exhaustion mid-draw: `_shuffle_unseen_first()` and keep going (with a swap-first guard against the same question re-opening the pool).
4. If every candidate is retired → mark `_mastered` and auto-pass.
5. Record the chosen question in `_seen` + `_recent` (cross-game recency; capped at 2× `_CROSS_GAME_RECENT_CAP`, trimmed to the last 30).
6. Persist `_deck_idx` + `_last_q` immediately (so `_end` doesn't need to duplicate).
7. Shuffle `confused_order` (choice display order).
8. Transition to `ASKING`.

### `_advance()`
Called when the RESULT flash ends. Mode-specific:

**Chain modes** (`CHAIN`, `ESCALATOR_CHAIN`):
- Wrong answer → if `reroll_available`, consume it (restore chain to max(chain, 1)), re-ask the same question; otherwise `_end(success=True)` (chain always "succeeds"; score = chain length achieved).
- `max_chain` reached → set `celebrating = True` with `celebration_text='MAX CHAIN!'` for 1.5s; `_end` fires after the banner.
- Otherwise → if `ESCALATOR_CHAIN`, call `_escalate()`; then `_next_question()`.

**Threshold modes** (`THRESHOLD`, `ESCALATOR_THRESHOLD`):
- Wrong answer → consume reroll if available; otherwise `_end(success = correct_count >= required)`. **Zero-tolerance** (2026-05-29): the quiz ends on first miss regardless of how many are left.
- `correct_count >= required` → `_end(success=True)`.
- `asked_count >= total_qs` without reaching threshold → `_end(success=False)`.
- Otherwise → if `ESCALATOR_THRESHOLD`, call `_escalate()`; then `_next_question()`.

### `_escalate()`
Clamps `tier = min(tier + 1, 5)`. Builds the next tier's deck using the same tier → fallback-lower-tier → all-questions order. Resumes the persistent `_deck_idx` for the new key.

### `_auto_pass_mastered_round()`
When a `(subject, tier)` is mastered, the engine burns no question:
1. Bumps `correct_count`, `chain`, `asked_count`, `auto_passed` by 1.
2. Updates `score` per mode.
3. Chain modes:
   - `max_chain` reached → `_end(success=True)`.
   - `ESCALATOR_CHAIN` → `_escalate()`; if the new tier is the same (already at T5) → `_end(success=True)`; otherwise `_next_question()` (may itself be mastered — recurses).
   - Plain CHAIN, fully mastered → set chain to `max_chain or 5` and `_end(success=True)`.
4. Threshold modes:
   - `correct_count >= required` → `_end(success=True)`.
   - `ESCALATOR_THRESHOLD` → `_escalate()`; if top tier and also mastered → success even if the raw `correct_count` is below `required` (Sphinx/Mjolnir T3 threshold=4 used to auto-fail a fully-mastered player who had only banked 3 passes).
   - Plain threshold, mastered → `_end(success=True)`.

### `_end(success)`
Transitions to `COMPLETE`, calls `_persist_cross_game_history()` (atomic write of the last-N shown questions per subject/tier to `<save_dir>/quiz_history.json`; non-fatal on OSError), fires `on_complete` + `callback` with the final `QuizResult`.

## Scoring summary (what the caller gets)

| Mode                  | `score` field              | `success` field                      |
|-----------------------|----------------------------|--------------------------------------|
| THRESHOLD             | `correct_count`            | `correct_count >= required`          |
| CHAIN                 | `chain` (length achieved)  | `True` always (chain never "fails"); score 0 means missed first Q |
| ESCALATOR_THRESHOLD   | `correct_count`            | `correct_count >= required` (or mastered-ladder override) |
| ESCALATOR_CHAIN       | `chain`                    | `True` always                        |

**Downstream contract:** combat treats chain-mode `score == 0` as a weapon miss and `score >= 1` as a landed strike at that chain. Threshold-mode callers inspect `success` directly.

## Timer wiring

### `Player.SUBJECT_TIMER` (recalibrated 2026-05-11)
Keyed `(base_seconds, wis_scale)`; `timer = base + WIS * scale`:
```python
'math':       ( 0, 1.0)   # combat — flat WIS seconds (chain v2)
'science':    (24, 1.2)   # concept questions
'grammar':    (20, 1.0)   # sentence-level analysis
'trivia':     (26, 1.2)
'geography':  (28, 1.2)
'history':    (34, 1.6)
'animal':     (34, 1.6)
'ai':         (45, 1.5)
'philosophy': (50, 1.5)
'cooking':    (44, 1.6)
'theology':   (50, 1.7)
'economics':  (50, 1.7)
```

Only `math` is actually timed in-game — the non-math values are kept because callers still pass `base_seconds` for symmetry and the character sheet references them (though the "+Ns on text-heavy subjects" line is UI-rot flagged in SYSTEMS_AUDIT.md §8 P1).

### Status-effect timer modifiers (via `Player.get_quiz_timer_modifier()`)
- `blinded`: ×0.70
- `stunned`: ×0.75
- `hallucinating`: ×0.80
- `confused`: ×0.55 (also shuffles choices)
- `blessed`: ×1.25

### `extra_seconds` adds
- `get_int_quiz_bonus()` — magical subjects (science) get +(INT-10)/2 seconds. Dead on everything but math today because science is untimed. Flagged in SYSTEMS_AUDIT.md §8 P1.
- `get_quiz_extra_seconds(subject)` — per-subject bonuses from quirks (Scheherazade, Merlin, Sisyphus, etc.) and Mimir's Well. Also dead on untimed subjects — flagged as the "if X ever becomes timed" quirk-text rot in SYSTEMS_AUDIT.md §7 P3.

## Tablet of Destinies reroll (one-time per floor)

| Step | What | Where |
|------|------|-------|
| 1    | Game checks `_has_tablet_of_destinies()` + `_quiz_reroll_used` flag       | `main.py:4912-4914`, `game_combat.py:1548/1758` |
| 2    | Game writes `quiz_engine._reroll_flag = <True/False>` before `start_quiz` | `game_combat.py:1555` |
| 3    | `start_quiz` reads sticky flag into `reroll_available`                    | `quiz_engine.py:221` |
| 4    | On first wrong answer, `_advance()` consumes `reroll_available`, sets `reroll_was_used=True`, re-poses the same question | `quiz_engine.py:400-406` (chain) / `425-428` (threshold) |
| 5    | Caller inspects `reroll_was_used` and marks `_quiz_reroll_used=True` + logs "The Tablet of Destinies cracks — fate rewritten!" | `game_combat.py:1620-1625` |
| 6    | `_change_level` clears `_quiz_reroll_used` so a fresh floor regrants the reroll | `main.py:649/1273` |

In chain modes, consuming the reroll also restores `chain = max(chain, 1)` so the Tablet never leaves the player below chain-1 on a reroll save.

## Invariants (don't break)

- **Zero-tolerance threshold:** `_advance()` must end the quiz on the FIRST wrong answer in threshold modes, with success tied to the already-accumulated correct_count. Only the Tablet reroll bypasses this, and only once.
- **Chain-v2 wrong does not zero chain:** `answer()` increments nothing on wrong; `_advance()` ends the chain with `success=True` and `score=chain`. Timer expiry follows the same rule. If you ever add a "chain-reset-on-wrong" codepath, you break the design.
- **Case-exact answer compare:** `choice.strip() == correct.strip()`. Do NOT lowercase — the grammar bank intentionally ships 4-choice sets that differ only by case.
- **Escalator caps at T5:** `_escalate()` clamps `min(tier + 1, 5)`. Do not raise this without authoring T6 content.
- **Mastery is per-run, not cross-game:** `get_deck_state()` returns `_retired + _mastered`; `_load_cross_game_history()` does NOT touch them. Add anything mastery-adjacent to the pickle, never to `quiz_history.json`.
- **Decks are NEVER pickled, only seen/retired/mastered are:** pickling question objects served stale questions after bank updates. `restore_deck_state` must leave `_decks / _deck_idx / _last_q` empty.
- **Timer is set once in `start_quiz` and runs continuously** — do NOT reset per question. Chain-mode pressure comes from the whole chain racing one clock.
- **`timed` auto-detects to math-only.** New quiz-gated actions must NOT inherit `timed=True` unless explicitly chosen; the renderer and tick loop both read `self.timed`.
- **Empty-pool guard must stay in both `start_quiz` and `_next_question`:** a missing/malformed JSON OR an escalator-fallback that lands in an empty tier must call `_end(success=False)` rather than index `_pool[0]`.
- **Choice order is always shuffled** via `confused_order`. The engine never reveals the correct-answer position.

## Interactions

- **[combat](combat.md)** — every attack calls `start_quiz(mode='chain', subject='math', tier=weapon.quiz_tier, max_chain=..., callback=...)` from `combat.py:1994`. Chain length drives the polynomial damage multiplier `mult = chain ** chain_exponent` (default 1.15, uniques override). Chain 0 = miss, chain >= 1 = landed strike at that chain. SPACE (`cancel_and_strike`) locks in the current chain mid-question.
- **[status_effects](status_effects.md)** — threshold-quiz failure (wrong answer) in identify fires `apply_effect(player, 'stunned', 10)` via `game_menus.py` → `main.py`. The `_timer_modifier` is read from `Player.get_quiz_timer_modifier()`, which inspects `has_effect('blinded' / 'stunned' / 'confused' / 'hallucinating' / 'blessed')`.
- **[save_bonus](save_bonus.md)** — no direct quiz-engine integration, but the Tablet reroll and status-effect timer are the engine's two defensive buffers (save bonuses are a third defense against monster-inflicted debuffs — see save_bonus.md).
- **[identify_v3](identify_v3.md)** — identify v3 (2026-08-06) uses ONE threshold-1 philosophy quiz at the item's `id_tier`. Right = full ID, wrong = `Stunned 10t`. No masteries, no chains.
- **[food_system](food_system.md)** — cook v2 uses one threshold-1 cooking quiz at `outcome.tier`. Right = full meal, wrong = ruined ingredients. Harvest uses one threshold-1 animal quiz at `corpse.harvest_tier`. (All one-Q, binary outcome per the "flow > gradient" rule.)
- **[containers_lockpick](containers_lockpick.md)** — lockpick v3 uses one threshold-1 economics quiz; wrong fires a chest trap by chest tier.
- **[magic](magic.md)** — spells + wands: threshold-1 science quizzes at the spell's/wand's tier. Spellbook chain bonus can reduce effective tier.
- **[karma_prayer](karma_prayer.md)** — pray/divine intercession: theology chain or escalator_threshold T5 depending on branch. Full liturgy at `game_divine.py:289/369/609/680/805/1064/1076`.
- **[quests_mysteries](quests_mysteries.md)** — mystery challenges use varied modes; Solomon/Grail/Sphinx/Mjolnir use threshold modes whose tuning predates zero-tolerance (SYSTEMS_AUDIT.md §3 P2).
- **[progression](progression.md)** — `just_mastered` and `auto_passed` surface in the chronicle and bestiary; `_mastered` is read by UI to tag tiers "T{n} CLEARED" (formerly "MASTERED" — vocabulary pending sweep per SYSTEMS_AUDIT.md §8 P4).

## History of major decisions

- **2026-05-11** — SUBJECT_TIMER recalibrated for learning-focused play; wonder subjects got scaffolded reading time (34-50s).
- **2026-05-18** — Chain combat v2 shipped. Wrong answer no longer zeros the chain; polynomial multiplier replaces per-rung arrays on common templates; SPACE-to-strike added (`cancel_and_strike`).
- **2026-05-29** — Zero-tolerance rule locked in: threshold modes end on first wrong answer. "No mulligans in ANY quiz mode."
- **2026-06-01** — Answer compare switched from case-fold to case-exact after a grammar bug: capitalization questions had 4 choices differing only by case, and lowercase comparison made every choice correct.
- **2026-06-06** — Cross-game `quiz_history.json` added; new games avoid recently-shown questions deterministically (previously relied on luck of the shuffle).
- **2026-07-18** — Deck pickle format changed: save pickles the seen-set only, NOT the shuffled decks. Bank updates now always take effect on load.
- **2026-08-06** — Identify v3: one philosophy question at `id_tier`, no masteries, binary outcome, Stunned 10t on fail. Harvest v4 and Lockpick v3 shipped alongside — all three "resource-consumed-on-attempt" systems use threshold-1.
- **2026-08-11** — Science-bank "test-it-yourself" voice baked into the T1-T3 scaffolding — further argument for keeping science untimed.
- **2026-10-02 (v2.18.0)** — Audit sync wave: 11 threshold-copy strings (item cards + lore dossiers) flagged for "any wrong = fail" clarification (SYSTEMS_AUDIT.md §8 P2); character-sheet timer line flagged as lie (§8 P1); `_draw_help_screen` flagged for missing zero-tolerance / chain-v2 / math-only timing explanations (§8 P3).

## Testing
- `tests/test_quiz_engine.py` (570 lines, ~30 tests) — covers QuizResult shape, threshold success/zero-tolerance, chain scoring, max_chain celebration + end, escalator tier climb + T5 cap, escalator chain tier climb, timer base_seconds + extras + legacy fallback + modifier, timer expiry failure flow, empty bank graceful fail, malformed JSON handling, deck tier isolation + persistence across sessions, answer no-op outside ASKING, case-exact whitespace-insensitive compare, `start_quiz` accepting QuizMode or str, invalid-mode raise, active-property lifecycle, `timed` default true/false for math/non-math + explicit overrides, untimed-quiz tick-no-op, untimed-chain ends via wrong-answer not timer.
- `tests/test_quiz_cross_game_memory.py` (77 lines) — pins `quiz_history.json` seed into `_seen` and the bounded recency cap.
- `tests/test_quiz_deck_no_stale.py` (49 lines) — pins the "decks rebuild from current JSON on load" invariant.
- `tests/test_death_from_status_tick.py` — pins Stunned-10t-on-identify-fail still ticks + expires cleanly (quiz engine fires `add_effect` through main.py).

## Known rough edges
From SYSTEMS_AUDIT.md:
- **§8 P2 (11 strings)** — item cards / lore dossiers say "Equip threshold: N correct" / "Quiz Threshold: N correct answers" without the "any wrong = fail" cue. Player reads "3 correct" and reasonably expects wrongs to be permitted. Needs copy sweep.
- **§8 P1** — `ui.py::Sidebar._derived` shows "Picks 0" every frame (dead row — `lockpick_charges` is never incremented post-v3). Delete or wire.
- **§8 P1** — `_draw_character_sheet L1032-1038` asserts a per-subject timer gradient ("Math 16s → Economics 46s") and an INT-magic timer bonus; both are fiction under math-only timing.
- **§8 P3** — `_draw_help_screen` has zero mention of zero-tolerance, chain v2 milestone ranks, math-only timing, identify v3 / cook v2 / lockpick v3 / harvest v4. New players can't learn these from `?`.
- **§8 P5** — `start_quiz` still computes `total_qs = ceil(threshold * 1.5)`; UI reads it and shows ratios like "0/5" that mean nothing under zero-tolerance.
- **§3 P2** — 5 mystery thresholds (solomon 6/8, grail 4/6, oracle 4/6, mjolnir, sphinx) were tuned pre-zero-tolerance; now harder than designed. Retune pending.
- **§5 P2** — `mystery_system.py:181` cooking challenge uses `escalator_chain` threshold=5, which violates the v3 one-Q cook rule. Any cook-quiz in a mystery bypasses the current model.
- **§3 P1** — `mystery_system.py::mimir_reward` populates `player.quiz_timer_bonuses[<subject>]` for all 10 subjects, but only math is timed → 9/10 reward branches dead.
- **§3 P3** — 16 non-math timer quirks still carry parenthetical "+Ns if the subject ever becomes timed" copy. Retarget already granted stat bumps; copy sweep pending.
