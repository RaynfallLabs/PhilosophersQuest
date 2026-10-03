# Context-Blurb System

**Status:** Phase 2 shipped (data layer + UI). Phase 3 (bank authoring) and the
pipeline-level gate (Phase 0 / Phase 6) are tracked in `ORIENTATION_AUDIT_PLAN.md`.

**Owner:** `src/quiz_engine.py` (data), `src/game_input.py` (keybind),
`src/game_render.py` (modal), `src/main.py` (state transition), `src/game_states.py`
(state constant).

---

## 1. Rule

Every quiz question belongs to a **topic ladder** (one philosopher's ladder, one
war's ladder, one scientist's ladder, …). Each ladder gets **ONE context blurb**
that carries the WHO / WHAT / WHY orientation a tenth-grader needs to make sense
of every rung in the ladder.

- Blurb is **strictly answer-free**: it must not state, paraphrase, or trivially
  imply any T1-T5 keyed fact in its own ladder.
- Blurb is **opt-in and manual**: the player presses **C** during a quiz to
  open the modal. The modal never auto-opens (user preference locked
  2026-10-03). The quiz_engine still sets `pending_context_auto_open` on a
  fresh (subject, topic), but `Game.update()` reads the flag only to clear
  it — the auto-open transition has been removed.
- Blurb is **math-safe**: the math quiz timer pauses while the modal is open;
  all other subjects are already untimed.
- Blurb is **discoverable but not loud**: a small `[C] context` hint appears on
  the quiz panel ONLY when a blurb exists for the current question. No hint
  means "nothing to show" rather than teasing a dead key.

See `ORIENTATION_AUDIT_PLAN.md` §Rules for the full policy, including the leak
gate the bank pipeline enforces (adversarial judge in `bank_pipeline.wf.js`).

---

## 2. Data layout

```
data/question_contexts/
  philosophy.json
  history.json
  economics.json
  ai.json
  theology.json
  geography.json
  science.json
  trivia.json
  animal.json
  cooking.json
```

Each per-subject file is a JSON object:

```json
{
  "<topic-slug>": {
    "context_blurb": "<200-400 word WHO / WHAT / WHY blurb>"
  },
  ...
}
```

- `<topic-slug>` matches the `topic` field on each question in
  `data/questions/<subject>.json`.
- The loader is tolerant: `{topic: "bare string"}` is also accepted (treated as
  the blurb). Any entry missing a non-empty string blurb is skipped.
- A missing per-subject file is non-fatal — that subject simply has no blurbs.

The ten listed subjects are the P0 banks. `math` and `grammar` deliberately
skip the system (snappy-rote; nothing to orient on).

### Join-key caveat (2026-10-03)

Current `data/questions/<subject>.json` entries do **not** carry a `topic`
field — `bankbuild/bank.py::cmd_merge` drops the topic when flattening ladders
to the live bank. Until the pipeline is updated to include the topic in the
flattened shape, the modal is a no-op for every shipped question (the loader
and modal are harmless; they just never fire). Phase 3 of the orientation
plan surfaces this as the first merge-step change the bank-authoring agents
need to make. See `bankbuild/PIPELINE.md §16`.

The context modal design does NOT depend on the question's `tier` or any
other field — only `(subject, topic)`.

---

## 3. UI flow

```
STATE_QUIZ --[C]-------> STATE_QUIZ_CONTEXT --[C | ESC | SPACE | RET]-> STATE_QUIZ
            (manual only;
             auto-open removed
             2026-10-03)
```

1. **Entry (manual).** In STATE_QUIZ, `K_c` is intercepted by
   `_quiz_input`. If a blurb exists for the current `(subject, topic)`:
   - `quiz_engine.pause_timer()` freezes the math countdown.
   - `quiz_engine.mark_context_seen(...)` records the topic so the one-shot
     auto-open never re-fires for the rest of the session.
   - `pending_context_auto_open` is cleared (so if a manual press and a
     pending auto-open coincide, we don't fire the transition twice).
   - `self.state = STATE_QUIZ_CONTEXT`.
   If no blurb exists, a message-log entry says
   `"No context available for this question."` and the state does not change.

2. **Entry (auto) — REMOVED 2026-10-03.** The quiz_engine still computes a
   `pending_context_auto_open` flag when `_next_question` sees a fresh
   `(subject, topic)` with a blurb (the engine-side logic remains intact
   and tested — see `test_context_blurbs.py`). But `Game.update()` no
   longer transitions to `STATE_QUIZ_CONTEXT` on that flag; it just
   clears it. Player preference: context must be a deliberate action, not
   an interruption. If you want to restore auto-open, re-enable the four
   lines in `Game.update()` that call `mark_context_seen` + `pause_timer`
   + state-flip.

3. **Draw.** The state dispatcher in `game_render.py` first calls
   `_draw_quiz()` (so the quiz panel sits beneath the modal), then
   `_draw_quiz_context_modal()`. The modal matches the item/bestiary dossier
   chrome via `_ui_modal_panel` + `_ui_subpanel` + `_ui_footer` so it reads
   as "another dossier screen" rather than a brand-new widget. Dimensions:
   `max_w=1200`, `max_h=600`, border `FP.LORE_BLUE_BORDER`; body font
   `get_font('body', 20)` with a scrollable interior for very long blurbs.

4. **Exit.** `_quiz_context_input` accepts `C`, `ESC`, `SPACE`, or `RET`;
   the top-level `K_ESCAPE` handler also catches STATE_QUIZ_CONTEXT. All
   paths call `quiz_engine.resume_timer()` and set state back to
   `STATE_QUIZ`. The quiz question + choices are untouched; the player
   returns to the exact same question with the clock unpaused.

### The hint on the quiz panel

A single-line hint `[C] context` is drawn at the bottom-right of the quiz
panel in muted text (`FP.FADED_TEXT`), gated on
`quiz_engine.current_context_blurb()` returning non-None. When no blurb
exists for a question, the hint is omitted — the key is a no-op and we
don't advertise it. This is the discoverability layer per Rule 4 in
`ORIENTATION_AUDIT_PLAN.md`.

---

## 4. Timer handling

Only math is timed (combat chain mode). The system treats pause/resume as a
boolean flag on the engine:

```python
qe.pause_timer()        # idempotent; also safe on untimed quizzes
qe.resume_timer()       # idempotent
qe._timer_paused        # bool; update() skips time_remaining decrement when True
qe._timer_paused_at     # informational snapshot of time_remaining at pause
```

`QuizEngine.update(dt)` reads `_timer_paused` in its ASKING branch:

```python
if self.timed and self.time_remaining > 0 and not self._timer_paused:
    self.time_remaining = max(0.0, self.time_remaining - dt)
```

The countdown resumes from whatever `time_remaining` holds — the pause does
not add elapsed-while-paused back on; it simply freezes the clock. (The
`_timer_paused_at` snapshot is kept for tests / debugging; it is not
consulted by any gameplay code.)

`start_quiz` clears `_timer_paused` + `_timer_paused_at` +
`pending_context_auto_open`, so a fresh quiz always starts un-paused and
with no stale auto-open from the previous session.

---

## 5. Session-seen tracking

```python
qe._quiz_context_seen: set[tuple[str, str]]
```

- Populated by `mark_context_seen(subject, topic)` on every modal open
  (manual or auto).
- Lives for the lifetime of the `QuizEngine` instance. A **new game**
  constructs a fresh engine (`main.py::__init__`), so the seen set resets.
- **Not persisted** across runs — see §7 Future extension points.
- Floor transitions / save-load within a run reuse the same engine, so the
  seen set is preserved (same as the mastery and recency state).

---

## 6. File ownership + public API

| File | Role |
|------|------|
| `src/game_states.py`     | Adds `STATE_QUIZ_CONTEXT = 'quiz_context'`. |
| `src/quiz_engine.py`     | Loader (`_load_context_blurbs`), public helpers (`get_context_blurb`, `current_context_blurb`, `mark_context_seen`, `pause_timer`, `resume_timer`), auto-open check (`_check_context_auto_open`, flag `pending_context_auto_open`), seen set (`_quiz_context_seen`), pause state (`_timer_paused`, `_timer_paused_at`). |
| `src/game_input.py`      | `K_c` dispatch inside `_quiz_input`; `_quiz_context_input` for the modal state; ESC-cancel wiring at the top-level handler. |
| `src/game_render.py`     | `_draw_quiz_context_modal`; `[C] context` hint on the standard quiz panel; state-dispatch entry. |
| `src/main.py`            | `STATE_QUIZ_CONTEXT` import; auto-open transition in `Game.update()`. |
| `data/question_contexts/`| Per-subject JSON files (one per bank in `_CONTEXT_SUBJECTS`); a `_README.txt` names the shape. |
| `tests/test_context_blurbs.py` | Loader resilience, pause/resume behavior, auto-open hook, state-wiring smoke. |

Public API (anything new on `QuizEngine`):

```python
get_context_blurb(subject: str, topic: str | None) -> str | None
current_context_blurb() -> str | None
mark_context_seen(subject: str, topic: str | None) -> None
pause_timer() -> None
resume_timer() -> None
reload_context_blurbs() -> None   # test hook
# Public attributes:
pending_context_auto_open: tuple[str, str] | None
```

No existing public API was renamed or changed; the pause/resume methods are
pure additions. The pre-existing `on_answer` / `on_complete` / `callback`
contract is untouched.

---

## 7. Future extension points (defer)

- **Per-player persistent "seen topics" across runs.** Save the
  `_quiz_context_seen` set to the run-level save, so a mid-run save-load
  does not re-fire auto-open. Already the behavior inside a single process;
  the extension is persistence across process restarts. Trivial once we
  pick a storage location (save pickle vs separate JSON file in `save_dir`).
- **"Dismiss forever" per-topic.** Add a toggle on the modal footer that
  moves the topic into a persistent "I know this one" set, hiding both
  auto-open and the `[C]` hint on future encounters.
- **Reveal lane for topics-without-blurbs.** Once Phase 3 ships, every
  question SHOULD have a blurb. Until then, consider surfacing the set of
  topics that lack a blurb as an audit screen for the bank-authoring agents.
- **Scroll bar on long blurbs.** The reader already scrolls via
  `_ui_draw_scroll_lines`; a visible scrollbar track would help if blurbs
  routinely exceed one screen (they shouldn't — 200-400 words fit on a
  600-tall panel).
- **Pipeline schema change (REQUIRED before Phase 3 ships).** Update
  `bankbuild/bank.py::cmd_merge` so flattened questions carry their
  `topic` string. The current merge drops it — see §2 Join-key caveat.
