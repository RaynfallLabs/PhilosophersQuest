# EffectsRuntime -- Design

**Date:** 2026-10-03 (Phase 1 landing); Phase 3 section appended same day
**Supersedes:** parts of the legacy `QuizEngine.celebrating` + `_draw_celebration` pair; the previous `effects_runtime_phase_1.md` filename (shed now that the runtime has grown past Phase 1).
**Context:** Phase 1 of CHAIN_EFFECTS_PLAN.md built the general-purpose visual-effects runtime; Phase 0 landed the `session_id` + `celebrate_on_max` gate on the engine. Phase 1 migrated math-combat chain feedback onto the runtime and moved the two legitimate full-screen takeovers (Divine Intercession, Unicorn boon) onto the same system so there is one place that owns visual effects. Phase 3 (this doc, §11) adds the first non-chain effect -- the identify-success orb -- which validates that the runtime generalises.

Later phases (preview tool, lifecycle tests, additional consumers) build on this foundation without touching it.

---

## 1. Why an EffectsRuntime at all

Before Phase 1 the game had exactly one visual-effects path -- the hard-coded `_draw_celebration` function in `game_render.py` plus a `celebrating` flag on `QuizEngine`. That path fired on every chain quiz that hit `max_chain`, which turned out to be ~22 call sites (prayer, equip, hero specials, fountain, mystery altar, …). The "MAX CHAIN!" takeover became visual spam, and the design doc called for in-combat per-answer feedback that the hard-coded path couldn't express.

The post-Phase-1 shape:

```
QuizEngine ---snapshot---> EffectsRuntime --dispatch--> handlers
                                 |                       |
Game ---fire(effect, ctx)------->+                       |
                                 |                       v
game_render --draw_bg/fg/overlay-+---------->  (per-handler pygame paint)
```

A single pluggable runtime owns every visual effect. Each named effect has a config block (visual params, thresholds, reduced-motion fallback) and a handler class. New effects plug in by appending to the config file and registering a handler class -- no edits to `_draw_quiz`, `main.update()`, or `render()`.

## 2. The handler protocol

All handlers duck-type the following methods. Any method a handler leaves out is silently skipped by the runtime, so a one-shot handler can omit `ingest()` and an observational handler can omit `trigger()`:

| Method                            | Called from              | Purpose                                                                                                                       |
|-----------------------------------|--------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| `ingest(snapshot: dict)`          | `runtime.observe()`      | Receive an idempotent per-frame state snapshot. The handler diffs vs. its own history to decide whether to spawn visuals.     |
| `trigger(context: dict)`          | `runtime.fire()`         | Start a one-shot event (takeover, pop, flash).                                                                                |
| `update(dt: float, reduced: bool)`| `runtime.update()`       | Advance internal timers, update particles, interpolate colours.                                                               |
| `draw_bg(surface, panel_rect, reduced)` | `runtime.draw_background()` | Paint behind the quiz panel (border aura, glow halo).                                                                     |
| `draw_fg(surface, protected, reduced)`  | `runtime.draw_foreground()` | Paint in front of the quiz panel, culled against protected rects (question text, choices, timer, counter).                 |
| `draw_overlay(surface, reduced)`  | `runtime.draw_top_overlay()` | Paint over everything else as the last step of a frame (fullscreen takeovers).                                             |
| `reset()`                         | tests / preview tool     | Clear all state back to construction defaults.                                                                                |
| `reset_scope(scope_id)`           | `runtime.reset_scope()`  | Clear state associated with one scope (e.g. end-of-quiz).                                                                     |

### Snapshot contract

`main.py::Game.update()` builds the following snapshot every frame and passes it to `runtime.observe(scope_id=qe.session_id, snapshot=snapshot)`:

```python
{
    'subject':           qe.subject,            # str
    'mode':              qe.mode,               # QuizMode enum
    'chain':             qe.chain,              # int
    'asked_count':       qe.asked_count,        # int
    'correct_count':     qe.correct_count,      # int
    'last_correct':      qe.last_correct,       # bool | None
    'quiz_state':        qe.state,              # QuizState enum
    'has_combat_target': self.combat_target is not None,
    'state':             self.state,            # game STATE_* key
}
```

The runtime enriches it with `scope_id` and `_reduced_motion` before passing to each handler.

### Fire context

`runtime.fire(effect_id, context)` passes an arbitrary dict to the handler. The runtime enriches it with `_reduced_motion`. Phase 1 handlers do not read anything else off `context`, but future ones can -- e.g. an identify-orb effect might take `{'item_name': 'Wand of Fire', 'rarity': 'uncommon'}`.

## 3. Config schema (`data/ui/effects_config.json`)

The config is a JSON dict with a `_meta` block and an `effects` object. Keys are effect ids used by `runtime.observe` (via snapshot gating) and `runtime.fire`. Example (abridged, see the file for full values):

```json
{
  "_meta": {"version": 1, "notes": "..."},
  "effects": {
    "chain_math_combat": {
      "handler": "chain_aura_pulse",
      "scope": "quiz_session",
      "activates_when": {
        "subject": "math",
        "mode": "chain",
        "has_combat_target": true
      },
      "ranks": [ {"threshold": 0, ...}, ... ],
      "milestones": [3, 5, 8, 10, 15, 20, 25, 30, 35],
      "particle_budget": 64,
      "pulse_duration_ms": 220,
      "burst_duration_ms": 650,
      "reduced_motion": {
        "disable": ["particles", "rotating_runes"],
        "replace_milestone": "static_highlight_300ms"
      }
    },
    "divine_intercession_takeover": {
      "handler": "fullscreen_takeover",
      "scope": "one_shot",
      "duration_ms": 1800,
      "art": "divine_intercession",
      "palette": "gold_white",
      "reduced_motion": {"disable": ["rotating_runes"], "shorten_to_ms": 900}
    }
  }
}
```

| Key                 | Meaning                                                                                               |
|---------------------|-------------------------------------------------------------------------------------------------------|
| `handler`           | The class that implements this effect. Phase 1 shipping: `chain_aura_pulse`, `fullscreen_takeover`.   |
| `scope`             | Documentation; the runtime does not read it in Phase 1. `quiz_session` means per-quiz; `one_shot` means stand-alone trigger. |
| `activates_when`    | A dict of fields the snapshot must match before the handler engages. Any key missing from the snapshot or non-equal fails the gate. |
| `reduced_motion`    | Per-effect `disable` list + optional `shorten_to_ms` (for one-shot) and `replace_milestone` (for chain). |
| Any other key       | Passed as-is to the handler's `__init__` via `runtime.effect_config(id)`.                             |

**Validation:** `_load_config` tolerates a missing file, bad JSON, or a missing `effects` object -- in all those cases the runtime registers no effects and all draw calls are no-ops. The game stays playable. Per-effect validation lives in each handler's constructor and also degrades gracefully (bad `ranks` fall back to a hardcoded default, etc.).

## 4. The two shipped handlers

### 4.1 `ChainAuraPulse` (`src/effects/chain_aura.py`)

Driven by `observe()` snapshots; keeps state per `scope_id`. Scope change wipes the state (new quiz = clean particle pool).

**Visuals:**
- **Persistent border aura** -- a rounded-rect glow around the quiz panel. Colour + opacity interpolate between rank thresholds (0 → white, 1 → pale green, 3 → Solid green, 5 → Sharp yellow, 8 → Brilliant orange, 10 → Genius red, 15 → Prodigy gold, 20 → Mythic pink). Drawn in `draw_bg` so the opaque panel masks it over the panel's interior.
- **Per-answer pulse** -- `pulse_duration_ms` (220 ms) border highlight boost on every correct answer. Up to 8 bounded sparks spawn near the counter position (anchor coordinates in `_Particle._ANCHOR_X/_Y`).
- **Milestone burst** -- `burst_duration_ms` (650 ms) heavier border bloom + up to 32 sparks on milestone crossings. Jumping multiple milestones (e.g. an auto-pass tiered mastery from 0 to 8) fires AT MOST ONE burst for the highest crossed milestone, via the `_last_milestone_fired` tracker.

**Rendering budget:**
- Particle pool is bounded by `particle_budget` (default 64). Over-budget spawns are dropped.
- The border-aura overlay surface is cached and reused across frames (resized only when the panel geometry changes).
- Particles each render through a tiny per-particle SRCALPHA surface, allocated on demand (3×3 px) so there is no per-frame GC churn.
- All timers are driven by `dt` in seconds; no `pygame.time.get_ticks()` dependency, so a paused update loop freezes the effect cleanly.

**Reduced motion** (`PQ_REDUCED_MOTION=1`):
- Particles are not spawned (both `_on_correct_answer` and `_on_milestone` gate on `_particles_allowed`).
- Rotating runes are n/a for this handler.
- Milestone replacement: a 300 ms static border highlight paints via `draw_bg` instead of the particle burst (`_static_highlight_ms` + `_static_highlight_color`).

**Protected rects:** `draw_fg` is passed the list of rects the panel owns -- question text, choice cards, timer bar, counter stack. Any particle whose bbox intersects any protected rect is culled. The handler never paints into those rects.

**Activation gate:** The handler's `_matches()` reads `activates_when` from config. Phase 1 ships `{subject: 'math', mode: 'chain', has_combat_target: true}` so non-math quizzes, non-chain modes, and chain quizzes with no monster (e.g. mystery altar chain) all skip the aura silently. Future reasoning/trivia modes can get their own entries in the config without touching Python.

### 4.2 `FullscreenTakeover` (`src/effects/fullscreen_takeover.py`)

One instance per registered effect id so Divine Intercession and Unicorn-bond each have their own timer and art.

**Visuals:**
- Warm overlay wash (`gold_white` → amber; `lavender_white` → violet).
- Two counter-rotating rune circles via `fantasy_ui.draw_rune_circle` (same shape as the legacy `_draw_celebration`).
- `draw_candle_glow` at centre for the gold bloom.
- Filigree-bordered headline + glow (`draw_glow_text`) + sub-line.

The visuals are a faithful translation of the pre-Phase-1 `_draw_celebration` function but parameterised by palette and headline text, driven off `self._elapsed_ms` instead of the engine's countdown timer.

**Timing contract:**
- `duration_ms` (default 1800) is the total hold.
- Progress 0 → 0.8 holds full brightness; 0.8 → 1.0 eases to zero so the takeover peels off cleanly.
- Re-triggering while already active restarts the timer (the second call wins) -- a stale trigger from an aborted quiz can't glue two hold windows together.

**Reduced motion:**
- `disable: ['rotating_runes']` -- the runes are replaced with two static ring outlines so no spinning geometry is painted.
- `shorten_to_ms: 900` -- halves the hold so the player doesn't sit through the full 1.8 s.

**Why `draw_overlay` (top phase) rather than `draw_fg`:** by the time these fire, the quiz has already completed and the game is back in STATE_PLAYER. The takeover needs to paint over whatever state-specific rendering just finished. Putting it in `draw_overlay` (called at the end of `render()` just before `pygame.display.flip()`) keeps it independent of state.

## 5. Integration points

| File                       | Change                                                                                                                                                    |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `src/effects_runtime.py`   | New module. `EffectsRuntime` + `build_default_runtime` factory.                                                                                           |
| `src/effects/__init__.py`  | New package init -- doc only.                                                                                                                             |
| `src/effects/chain_aura.py`| New handler.                                                                                                                                              |
| `src/effects/fullscreen_takeover.py` | New handler.                                                                                                                                     |
| `data/ui/effects_config.json` | New config, three effects.                                                                                                                             |
| `PhilosophersQuest.spec`   | Added `('data/ui', 'data/ui')` so the frozen bundle includes the config.                                                                                  |
| `src/main.py`              | Imports `build_default_runtime`; `Game.__init__` stores `self.effects_runtime`; `Game.update()` builds the snapshot + calls `observe` + `update`.         |
| `src/game_render.py`       | `_draw_quiz` calls `effects_runtime.draw_background` before the opaque panel and `draw_foreground` with protected rects after the panel; `render()` calls `draw_top_overlay` as the last step. `_draw_celebration` was deleted; the `qe.celebrating` short-circuit was deleted. Added `_quiz_protected_rects` helper. |
| `src/game_divine.py`       | `_confirm_divine_intercession` no longer passes `celebrate_on_max=True`; `on_complete` now calls `effects_runtime.fire('divine_intercession_takeover', {})` on success. |
| `src/game_encounters.py`   | `_start_unicorn_quiz` no longer passes `celebrate_on_max=True`; `on_complete` now calls `effects_runtime.fire('unicorn_bond_takeover', {})` for score >= 1. |
| `tests/test_celebrate_on_max_gate.py` | Updated Phase-0 opt-in checks to Phase-1 fire() checks; added the "no src file opts in anymore" invariant.                                     |

## 6. Reduced motion

Phase 1 ships env-var only: set `PQ_REDUCED_MOTION=1` before launching the game. The runtime reads it in `__init__` once. There is no runtime toggle, no in-game settings UI. A proper settings panel is deliberately deferred -- Phase 1 is foundation + first consumer; a settings UI is its own body of work.

How to verify locally:
```powershell
$env:PQ_REDUCED_MOTION='1'; python src/main.py
```

What should change:
- Chain aura: no particles anywhere; border aura stays steady; milestones flash a 300 ms steady highlight instead of a particle burst.
- Fullscreen takeovers: the two rune circles are replaced with static ring outlines; the hold shortens from 1.8 s to 0.9 s.

Env var not set / set to anything other than `'1'` → full motion.

## 7. Adding a new effect

Walkthrough of adding an **identify success orb** (the Phase 3 target):

1. Append a block to `data/ui/effects_config.json`:
   ```json
   "identify_success_orb": {
     "handler": "orb_pop",
     "scope": "one_shot",
     "duration_ms": 700,
     "palette": "orchid_white",
     "reduced_motion": {"disable": ["particles"], "shorten_to_ms": 350}
   }
   ```
2. Add `src/effects/orb_pop.py` with an `OrbPop` class implementing `trigger`, `update`, and `draw_overlay` (and leaving `ingest`/`draw_bg`/`draw_fg` out).
3. Register it in `effects_runtime.build_default_runtime`:
   ```python
   from effects.orb_pop import OrbPop
   runtime.register('identify_success_orb',
                    OrbPop(runtime.effect_config('identify_success_orb')))
   ```
4. Call `self.effects_runtime.fire('identify_success_orb', {'item_name': ...})` from the identify-success path.

The runtime's drawing hooks, protected-rect contract, snapshot plumbing, and reduced-motion plumbing are reused as-is. The author doesn't touch `_draw_quiz`, `render()`, `main.update()`, or the Python call sites of any other effect.

## 8. Testing + verification

Phase 1 scope: smoke tests + the Phase-0 regression suite (`tests/test_celebrate_on_max_gate.py` has been updated to assert the new `fire()` call sites). The dedicated unit-test harness + the preview tool are Phase 2 scope.

Smoke checks performed:

- `python -c "from effects_runtime import build_default_runtime; rt = build_default_runtime()"` -- returns successfully, registers three handlers.
- `python -c "import main"` -- imports clean (no syntax error, no circular import).
- `pytest tests/ -q` -- 1660 pass, 29 skipped (Phase-0 baseline).
- `PQ_REDUCED_MOTION=1` env var honored (particles suppressed, takeover `_total_ms` halved).

## 9. Non-goals / what Phase 1 explicitly does NOT do

- No lifecycle unit tests for the runtime (Phase 2).
- No preview tool (Phase 2).
- No new consumer beyond chain-math-combat + the two legacy takeover migrations (Phase 3 picks the next).
- No settings UI for reduced motion (future).
- No persistence of effect state across saves (not needed -- all effects are per-session).

## 11. Phase 3: `identify_success_orb`

Phase 3 of CHAIN_EFFECTS_PLAN.md adds the first non-chain consumer to prove that the plumbing above generalises beyond math combat. The identify flow (identify-v3, 2026-08-06) is a single philosophy question: right = full identification, wrong = Stunned 10 turns. Success is the "aha!" moment and benefits from a bounded celebratory flourish; failure is already punished by the stun, so the orb only fires on the success branch.

### 11.1 Handler

`src/effects/identify_orb.py` implements the `IdentifyOrb` class. One registered instance per runtime -- re-firing while active restarts the timer so a quick second identify can't stack two orbs.

Visual plan (full motion):

- **Phase 0 (0 -> 200 ms).** Orb grows from radius 0 to peak radius ~48 px with an ease-out quadratic curve.
- **Phase 1 (200 -> 700 ms).** Orb hovers at peak radius; alpha pulses sinusoidally; up to 12 orbit sparks circle the orb.
- **Phase 2 (700 -> 1200 ms).** Orb expands to ~120 px while alpha fades to 0.

Rendering budget: the particle pool is capped at `particle_budget` (default 12); the orb surface is cached and resized on demand to the current radius; each orbit spark allocates one tiny SRCALPHA surface per frame.

Draw phase: `draw_overlay` (top-level), matching the Divine Intercession / Unicorn pattern. By the time the orb fires, the identify quiz modal has already closed and the game is back in STATE_PLAYER (or STATE_LORE after the item ID path pushes the lore screen). Painting in the top-overlay phase keeps the orb independent of state-specific rendering.

### 11.2 Anchor-point convention

Callers provide the orb's screen-space centre via the context dict:

```python
self.effects_runtime.fire('identify_success_orb',
                          {'anchor_x': cx, 'anchor_y': cy})
```

Missing / non-integer coords fall back to the window centre (`layout.WINDOW_W // 2`, `layout.WINDOW_H // 2`). The handler never crashes on a bad anchor -- in the worst case it paints centre-screen.

The two Phase-3 call sites both anchor at screen centre: the identified item's inventory slot isn't rendered on the map at the fire moment (the quiz modal just vanished), so centre-screen keeps the "aha" visible wherever the player is looking.

### 11.3 Call sites

| File                | Function                        | Trigger                                                                                      |
|---------------------|---------------------------------|----------------------------------------------------------------------------------------------|
| `src/game_magic.py` | `_identify_item.on_complete`    | Success branch of the item-identify callback (after the aura message, before the lore push). |
| `src/main.py`       | `_start_corpse_identify.on_complete` | Success branch of the corpse-identify callback (after the chronicle log + success message). |

Both call sites gate on `getattr(result, 'success', False)` -- the failure (stun) branch intentionally does NOT fire the orb.

### 11.4 Reduced-motion fallback

With `PQ_REDUCED_MOTION=1`:

- `disable: ["orbit_sparks", "expansion_phase"]` -- no orbital spark pool spawn, no expand-and-fade.
- `replace_with: "static_pulse_300ms"` -- the full 3-phase animation is replaced wholesale with a single 300 ms ring that expands slightly and fades to 0.

The handler stores a `_reduced_mode` flag at trigger time (not just at update time) so the trigger-time orbit-spark spawn can be gated on the same decision. Flipping the env var mid-session is tolerated: already-active orbs continue on whichever path they started on.

### 11.5 Tests

`tests/test_identify_orb.py` covers:

- Handler is registered and its config block parses.
- `fire()` activates the handler and records the anchor.
- Missing anchor falls back to window centre.
- Animation drains after `duration_ms` so no leaked state persists.
- Re-triggering mid-animation restarts the timer with the new anchor.
- Reduced-motion mode skips the orbit-spark spawn and expires at 300 ms.
- Static grep check: both call sites fire the orb in their success branch.
- Static grep check: neither call site's failure (stun) branch fires the orb.

## 10. Open questions queued for Phase 2+

- **Protected-rect bundle shape.** Phase 1 uses rough rectangles for the four quiz regions. Finer rects (per choice card, per status line) would let effects slide into negative space; defer until the preview tool reveals the pain.
- **Scope automatic reset.** Currently the chain-aura handler notices scope changes itself in `ingest()`. A declarative-scope path on the runtime (so other handlers get free reset-on-boundary semantics) might be nicer; wait until a second scoped effect is wanted before building it.
- **Particle anchor coordinates.** Hardcoded in `_Particle` (`_ANCHOR_X = 1300, _ANCHOR_Y = 100`). The counter position actually depends on panel geometry; the handler should receive panel geometry via the snapshot. Phase 2's preview tool will make this visible.
