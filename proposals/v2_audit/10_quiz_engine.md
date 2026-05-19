# V2 Audit — 10 Quiz Engine

Scope: `src/quiz_engine.py` + every use-site (combat, equip, harvest, cook,
identify, lockpick, prayer, fountain/grave/throne, fenrir/mystery, wand,
spell, scroll, spellbook, recall lore, hack reality, hero special,
trap disarm, haggle, sketch/firebreath, corpse study, unicorn).

Tests: `py -m pytest tests/ -q` -> **538 passed in 62.43s**
(509 baseline + 29 new in `tests/test_quiz_engine.py`).

---

## 1. Mode coverage

| Mode | Status | Notes |
|---|---|---|
| `threshold` | PASS | Hits required correct -> success, ends early on impossibility. `score = correct_count`. |
| `chain` | PASS | Chain ends on wrong; `score = peak chain length`; `success` always True (combat resolves on chain alone). `max_chain` triggers celebration + end. |
| `escalator_threshold` | PASS | Tier bumps every question (cap 5); same accounting as threshold. |
| `escalator_chain` | PASS | Tier bumps every correct (cap 5); ends on wrong; same scoring as chain. `max_chain` celebrates + ends. |

### Engine dispatch (verified)

`QuizEngine.start_quiz` (`src/quiz_engine.py:97`) accepts mode as `str` or
`QuizMode` enum; string is coerced via `QuizMode(mode)` and raises `ValueError`
on unknown strings (tested in `test_invalid_mode_string_raises`).

`_advance` (`src/quiz_engine.py:270`) dispatches on `self.mode`:
- Chain modes: end on wrong (success=True, score=chain), advance on right,
  call `_escalate` only when mode is `ESCALATOR_CHAIN`.
- Threshold modes: end on threshold reached (early), on math-impossible
  (early), or on running out of questions. `_escalate` fires per-question
  only when mode is `ESCALATOR_THRESHOLD`.

### Result shape

`QuizResult(success, score, correct, asked)` (`quiz_engine.py:25`).

`score` semantics (`quiz_engine.py:186-187`):
- Chain/escalator-chain: peak chain length (matches what callers read via
  `result.score`).
- Threshold/escalator-threshold: `correct_count`.

All call-site readers verified to read the correct field:
- `combat.py:625` (chain math) — callback reads chain via `score`.
- `container_system.py:84` (escalator-chain econ) — `int(getattr(result,'score',0))`.
- `food_system.py:137,237` (escalator-chain cooking) — `min(5, result.score)`.
- `game_divine.py:320,421,661,732,878` — `result.score`.
- `game_combat.py:914,973` (sketch, firebreath) — `result.score`.
- `game_encounters.py:444` (unicorn) — `result.score`.
- `game_magic.py:88,1082,2501` (recall lore, spells, identify) — `result.score`.
- `game_menus.py:1279` (hero specials) — `int(result.score)`.
- `main.py:2628,3477,3949,4736,5048` (trap, hack, chain-equip, corpse-id, haggle) — `result.score`.

Threshold-mode callers correctly read `result.success`:
- `combat`, scrolls, spellbooks, harvest, wand-invoke, equip armor/accessory,
  altar-buc-identify, quick-buc, mystery (where `mode in chain` it overrides
  with chain threshold).

No "wrong-field" bugs found in this pass.

---

## 2. Bugs found + fixes applied

### A. Empty question bank crashed engine with `IndexError`
- **Site:** `quiz_engine.py:_next_question` -> `self._pool[self._pool_idx]`
- **Trigger:** Subject JSON file missing or empty; e.g. malformed JSON
  in `data/questions/<subject>.json`. The pre-existing audit
  `tools/audit/findings/code/agent_a/code-quiz-engine-empty-pool-crash.md`
  documented this as P3 dormant bug.
- **Fix:** `start_quiz` now checks the resolved pool; if empty, fires
  `_end(success=False)` immediately and the callback receives a clean
  failure result (no IndexError, no orphaned state). A defensive check in
  `_next_question` covers the same case if the escalator path leaves the
  pool empty.
- **Test:** `test_empty_bank_fails_gracefully`.

### B. `json.JSONDecodeError` not caught in `load_questions`
- **Site:** `quiz_engine.py:load_questions` only caught `FileNotFoundError`.
- **Trigger:** Hand-edited JSON with a syntax error would raise
  `JSONDecodeError`, propagate up through `start_quiz`, and crash mid-action.
- **Fix:** Catch both `FileNotFoundError` and `json.JSONDecodeError`; warning
  message updated to "Question file unusable: ... (<reason>)".
- **Test:** `test_load_questions_handles_malformed_json` (uses tmp_path +
  monkeypatch on `_QUESTIONS_DIR`).

### C. Unicorn quiz: `max_chain` missing — could chain past intended 0-5
- **Site:** `game_encounters.py:_start_unicorn_quiz` started an
  `escalator_chain` without `max_chain`.
- **Trigger:** With no cap, a player on a strong streak would keep getting
  asked questions until they finally missed. The handler comment
  ("`chain = result.score  # 0-5`") asserts the chain caps at 5, but
  the engine had no mechanism to enforce it. The boon ladder
  (`_apply_unicorn_boons`) doesn't read beyond `chain >= 5`, so extra
  questions added no value and just put pressure on the player.
- **Fix:** Added `max_chain=5` so the unicorn quiz matches the documented
  0-5 ladder and ends with a celebration on chain 5.

No other call-sites are missing `max_chain` where the chain ladder is
bounded. (`combat.py` deliberately uses the weapon-declared
`weapon.max_chain_length` to allow longer chains for some legendaries.)

---

## 3. Timer math

Engine formula (`quiz_engine.py:144-148`):

```
if base_seconds is not None:
    timer_seconds = round(base_seconds * timer_modifier) + extra_seconds
else:
    timer_seconds = round((10 + wisdom) * timer_modifier) + extra_seconds
```

Every call-site passes `base_seconds=player.get_quiz_timer(subject)`, so the
legacy path is dead in shipping code (kept for tests + safety). Verified in
the call-site inspection.

Per-subject base + WIS scale + effective timer at WIS 10:

| subject | base | wis_scale | WIS-10 timer |
|---|---:|---:|---:|
| math | 8 | 0.8 | 16 |
| grammar | 20 | 1.0 | 30 |
| science | 24 | 1.2 | 36 |
| trivia | 26 | 1.2 | 38 |
| geography | 28 | 1.2 | 40 |
| history | 34 | 1.6 | 50 |
| animal | 34 | 1.6 | 50 |
| cooking | 44 | 1.6 | 60 |
| ai | 45 | 1.5 | 60 |
| philosophy | 50 | 1.5 | 65 |
| theology | 50 | 1.7 | 67 |
| economics | 50 | 1.7 | 67 |

**Sanity:** content density vs timer budget matches CLAUDE.md's intent —
math snappy (16s @ WIS 10), philosophy/theology/economics roomy (65-67s).
`MEMORY.md:project_subject_timer.md` confirms this is the intended table.

**Timer expiry (`quiz_engine.py:207-219`):** when `time_remaining <= 0` the
engine forces a wrong answer (`last_correct = False`, `chain = 0`,
`asked_count += 1`) and enters `RESULT` state with the wrong-answer display
time. `on_answer(False)` fires. Then `_advance` runs.

`_advance` re-checks `time_remaining <= 0` and ends the quiz directly:
- Chain mode: success=True with current chain (0 if first question expired).
- Threshold modes: success based on `correct_count >= required` so far.

No grace period; no stamina drain. This is intentional — the per-subject
timer is the breathing room.

Test: `test_timer_expiry_fails_quiz_and_advances` verifies a 5s timer in
chain mode results in `success=True, score=0`.

---

## 4. Tier escalation

`_escalate` (`quiz_engine.py:320-340`):
- `tier = min(tier + 1, 5)` — hard cap at 5.
- Loads/builds a deck for the new tier from the cached bank.
- Falls back to nearest-lower tier if exact-tier pool is empty (defensive,
  shouldn't fire on current banks — see Section 5).
- Resets `_pool_idx` from the persistent deck position.

Behavior verified by tests:
- `test_escalator_chain_tier_climbs_each_rung` — T1 -> T2 -> T3 across
  correct answers.
- `test_escalator_threshold_escalates_tier_each_question` — T1 -> T2 -> T3
  across each question (correct OR not).
- `test_escalator_threshold_tier_caps_at_5` — T4 -> T5, then stays at 5.

`max_chain` (chain modes only):
- Hit max_chain -> celebration state (`celebrating=True`, text "MAX CHAIN!",
  timer 1.5s).
- After celebration timer expires (`update` ticks down), `_end(success=True)`
  fires with the final score.
- Test: `test_chain_max_chain_celebration_and_end`,
  `test_escalator_chain_max_chain_celebrates_and_ends`.

`tier=5, max_chain=5` is the common case; lockpick, prayer, fountain,
grave, throne, cooking, identify, haggle, hack reality, hero special,
fountain, trap-disarm, fenrir-bind all hit the chain-5 ceiling cleanly.

---

## 5. Question bank coverage

```
subject        T1     T2     T3     T4     T5  total
--------------------------------------------------
math          417    811    712    409    344   2693
science       492    701    147    587    460   2387
grammar       315    460    165    417    148   1505
trivia        854    708    598    712    600   3472
geography     859    699    702    694    354   3308
history       869    623    518    455    400   2865
animal        408    455    412    349    261   1885
ai            186    376    213    597    120   1492
philosophy    117    129    266    277    160    949
cooking       559    550    531    345    497   2482
theology      930    370    557    429    265   2551
economics     713    682    680    539    440   3054
```

**All 12 subjects have all 5 tiers populated.** No fallback path will fire
on the current banks. Verified by
`test_question_bank_coverage_all_subjects_all_tiers`.

Distribution skew worth noting (not a bug, just a known shape):
- `science T3` (147) and `grammar T5` (148) are thin relative to siblings —
  if the deck logic forced players to crawl repeatedly through these tiers
  in a single descent, repetition would feel high. With the persistent
  deck + shuffle-unseen-first walk, this is unlikely to surface in a single
  run (player would need 100+ T3 science quizzes to start seeing repeats).
- `ai T5` (120) and `philosophy T1-T2` (117/129) are similarly thin.
  Same conclusion — fine for a single run, but worth pulling into the
  "T5 expansion" bin if/when those subjects get a rebuild pass.

---

## 6. Tests added

`tests/test_quiz_engine.py` — **29 tests, all passing.**

Result shape:
1. `test_quizresult_fields`

Threshold mode:
2. `test_threshold_success_when_enough_correct`
3. `test_threshold_fail_when_not_enough_correct`
4. `test_threshold_early_exit_when_impossible`

Chain mode:
5. `test_chain_score_is_chain_length`
6. `test_chain_first_question_wrong_score_zero`
7. `test_chain_max_chain_celebration_and_end`

Escalator threshold:
8. `test_escalator_threshold_escalates_tier_each_question`
9. `test_escalator_threshold_tier_caps_at_5`

Escalator chain:
10. `test_escalator_chain_tier_climbs_each_rung`
11. `test_escalator_chain_score_is_chain_length`
12. `test_escalator_chain_max_chain_celebrates_and_ends`

Timer math:
13. `test_timer_base_seconds_plus_extra`
14. `test_timer_modifier_scales_base_only`
15. `test_timer_legacy_fallback_uses_wisdom`
16. `test_timer_expiry_fails_quiz_and_advances`

Bank loading + coverage:
17. `test_empty_bank_fails_gracefully`
18. `test_load_questions_handles_malformed_json`
19. `test_question_bank_coverage_all_subjects_all_tiers`

Deck invariants:
20. `test_deck_uses_only_requested_tier`
21. `test_deck_persists_across_sessions`

State machine + input:
22. `test_answer_noop_outside_asking_state`
23. `test_answer_is_case_and_whitespace_insensitive`

Mode plumbing:
24-27. `test_start_quiz_accepts_mode_strings` (param: 4 modes)
28. `test_invalid_mode_string_raises`

Lifecycle:
29. `test_active_property_lifecycle`

---

## 7. Use-site mode/subject summary

Verified each call-site uses the right (mode, subject, tier) triplet for its
action. No invalid mode strings found; no subject typos; all tiers clamp to
1..5 either by the engine or the caller.

| File:Line | Action | Mode | Subject | Tier |
|---|---|---|---|---|
| `combat.py:625` | Melee attack | `chain` | `math` | weapon.quiz_tier |
| `food_system.py:165` | Compound cook | `escalator_chain` | `cooking` | 1 |
| `food_system.py:210` | Harvest corpse | `threshold` | `animal` | corpse.harvest_tier |
| `food_system.py:277` | Single-ingredient cook | `escalator_chain` | `cooking` | 1 |
| `container_system.py:92` | Lockpick | `escalator_chain` | `economics` | container.quiz_tier |
| `game_encounters.py:447` | Unicorn boons | `escalator_chain` | `ai` | 1 |
| `game_divine.py:305` | Mystery altar | varies (data) | varies (data) | varies (data) |
| `game_divine.py:350` | Altar BUC upgrade | `escalator_chain` | `theology` | 1 |
| `game_divine.py:398` | Altar BUC identify | `threshold` | `theology` | 1 |
| `game_divine.py:426` | Fountain drink | `escalator_chain` | `ai` | 1 |
| `game_divine.py:666` | Grave dig | `escalator_chain` | `geography` | 1 |
| `game_divine.py:737` | Throne sit | `escalator_chain` | `history` | 1 |
| `game_divine.py:887` | Pray | `escalator_chain` | `theology` | 1 |
| `game_combat.py:862` | Wand zap (combat-cursor) | `threshold` | `science` | wand.quiz_tier |
| `game_combat.py:950` | Sketch Manifest | `escalator_chain` | `ai` | 1 |
| `game_combat.py:1010` | Stuffie Fire Breath | `escalator_chain` | `ai` | 1 |
| `game_magic.py:96` | Recall Lore | `escalator_chain` | `trivia` | 1 |
| `game_magic.py:254` | Wand zap (self/util) | `threshold` | `science` | wand.quiz_tier |
| `game_magic.py:1104` | Spell cast | `escalator_chain` | `science` | spell.quiz_tier |
| `game_magic.py:2045` | Scroll read | `threshold` | `grammar` | scroll.quiz_tier |
| `game_magic.py:2565` | Item identify | `escalator_chain` | `philosophy` | 1 |
| `game_magic.py:2737` | Quick BUC | `threshold` | `philosophy` | 1 |
| `game_magic.py:2808` | Spellbook learn | `threshold` | `grammar` | book.quiz_tier |
| `game_menus.py:1284` | Hero special | `escalator_chain` | `ai` | 1 |
| `main.py:2631` | Trap disarm | `escalator_chain` | `ai` | 1 |
| `main.py:3482` | Hack Reality | `escalator_chain` | `ai` | 1 |
| `main.py:3855` | Equip armor/shield | `threshold` | `geography` | item.quiz_tier |
| `main.py:3914` | Equip accessory | `threshold` | `history` | item.quiz_tier |
| `main.py:3997` | Chain-equip legendary | data-driven | data-driven | item.quiz_tier |
| `main.py:4781` | Corpse identify | `escalator_chain` | `philosophy` | 1 |
| `main.py:5065` | Haggle merchant | `escalator_chain` | `economics` | 1 |

This table matches the CLAUDE.md subject->action map exactly. The only
oddity worth flagging (not a bug, just a design observation): the AI
subject is overloaded — it's used for fountain, grave, throne wasn't AI
(history, geography), unicorn, trap disarm, hack reality, sketch
manifest, stuffie firebreath, hero specials. The bank has 1,492 questions
spanning tiers, so saturation isn't an immediate concern, but if the
project grows another AI-tagged action, the per-subject AI quiz queue
will be the first place to feel staleness.

---

## 8. Files changed

- `src/quiz_engine.py` — JSON decode catch + empty-pool graceful fail
  (in `load_questions`, `start_quiz`, `_next_question`).
- `src/game_encounters.py` — unicorn quiz now passes `max_chain=5`.
- `tests/test_quiz_engine.py` — new (29 tests).
- `proposals/v2_audit/10_quiz_engine.md` — this document.

No semantic changes to gameplay outside the bug fixes above. Subject
timer table, mode dispatch, scoring, and tier escalation all behave the
same as before.
