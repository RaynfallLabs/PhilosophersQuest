# Chain Effects — Foundation Plan

**Date:** 2026-10-03
**Source doc:** `docs/math_quiz_effects_design.md` (user's uploaded design — the north star for math-combat chain feedback)
**Scope broadening:** per user direction, this is **not** a one-off math-combat polish. It's the foundation we'll build future effects on (identify success, scroll-read, level-up, boss death, quest reveals, etc.). Math combat is the first consumer; the architecture must be general.

---

## Goals (ranked)

1. **Math combat gets the chain-feedback experience the design doc describes** — immediate per-answer response, persistent per-rank aura, milestone bursts, bounded particles, reduced-motion opt-in, context-pause-aware.
2. **Future effects can plug in without rewriting the plumbing.** New effect = new entry in a config + handler, not a new module and not new integration points inside `_draw_quiz`.
3. **Clean up what we already have** — the full-screen MAX CHAIN celebration currently fires on ~12 routine actions (prayer, hero specials, fountain, trap disarm, haggle, …). Retire that firing for routine moments; keep it (temporarily) for the two cases where it's actually earned (Divine Intercession, Unicorn chain-5 pet-unlock).

---

## The system — one controller, many effects

### `src/effects_runtime.py` (new)

A general-purpose visual-effects layer that observes game state and renders bounded visuals. Not quiz-specific; chain feedback is just its first consumer.

```python
class EffectsRuntime:
    """Pluggable visual effects. Independent of QuizEngine/game state;
    other systems feed observations and request effect bursts."""

    def __init__(self, config_path: str): ...
    def register(self, effect_id: str, handler: 'EffectHandler'): ...

    # Observational — called every tick from game.update(); idempotent.
    def observe(self, scope_id: str, snapshot: dict): ...

    # Imperative — call directly for one-shot events (level-up, boss death).
    def fire(self, effect_id: str, context: dict): ...

    # Lifecycle.
    def reset_scope(self, scope_id: str): ...
    def update(self, dt: float, paused: bool = False): ...

    # Drawing.
    def draw_background(self, surface, protected_rect): ...
    def draw_foreground(self, surface, protected_rects: list): ...
```

**Why this shape:**
- `scope_id` is a generic session key, not a quiz_id — a chain quiz is one scope, a cook attempt is another, a boss encounter is another. Chain's "monotonically increasing session ID" is a special case.
- `observe(scope, snapshot)` is idempotent → safe to call every frame.
- `fire(effect, context)` is for events that happen once and don't need snapshotting (treasure drop, level up).
- `protected_rects` is universal — any effect that overlays visuals must respect them.
- Pause support is a top-level kwarg; `paused=True` freezes timers without discarding state.

### `data/ui/effects_config.json` (new)

Not a chain-specific file. Each effect declares its trigger, visual params, and reduced-motion fallback.

```json
{
  "chain_math_combat": {
    "handler": "chain_aura_pulse",
    "scope": "quiz_session",
    "ranks": [...],
    "milestones": [3, 5, 8, 10, 15, 20, 25, 30, 35],
    "particle_budget": 64,
    "aura_opacity_cap": 0.65,
    "palette_transitions": {...},
    "reduced_motion": {
      "disable": ["particles", "rotating_runes"],
      "replace_milestone": "static_highlight_300ms"
    }
  },
  "level_up_burst": {
    "handler": "radial_burst",
    "scope": "one_shot",
    ...
  }
}
```

Validation at load time; a malformed effect falls back to no-op with a diagnostic log so combat still works.

### `src/effects/` subdirectory (new)

One file per handler. Chain-aura-pulse lives in `src/effects/chain_aura.py`. Future handlers (radial burst, orb pop, text wave) live beside it. Each handler implements the `EffectHandler` protocol:

```python
class EffectHandler(Protocol):
    def ingest(self, snapshot: dict) -> list[FireEvent]: ...
    def update(self, dt: float) -> None: ...
    def draw_bg(self, surface, rect) -> None: ...
    def draw_fg(self, surface, protected_rects) -> None: ...
```

---

## Phase breakdown

### PHASE 0 — Legacy cleanup + session identity (prerequisite)

- Add `_session_id` counter to `QuizEngine.__init__`; increment in `start_quiz` and expose as a public attribute. Fixes the "two consecutive zero-chain sessions" problem the design doc flags.
- Add `celebrate_on_max: bool = False` kwarg to `start_quiz`. The existing `celebrating` flag only sets when `max_chain reached AND celebrate_on_max=True`. **Default False** retires the full-screen takeover for the ~12 routine chain-mode call sites.
- Set `celebrate_on_max=True` at exactly two call sites: `_confirm_divine_intercession` and the Unicorn boon quiz in `game_encounters.py`. All other call sites get the default (no celebration).
- Legacy array-chain unique weapons — audit `data/items/weapon.json` for weapons that ship with `chain_multipliers` arrays and no `chain_exponent`. These currently trigger celebration on chain-5. **Judgment call:** either migrate them to polynomial (set `chain_exponent: 1.15` + delete array) OR add `celebrate_on_max=False` to the combat.py `start_quiz` path explicitly. I'd choose the explicit path — simpler, no balance change.
- Keep `_draw_celebration` + its state intact for the two live cases. We'll migrate those two to the new system in a later phase but it's not blocking.

**Estimated effort:** 1 Opus agent, ~45 min. 1 modified file (quiz_engine.py), 1 light-touch file (game_divine.py), 1 light-touch file (game_encounters.py), 1 call-site sweep in combat.py.

### PHASE 1 — Build the runtime + first consumer (math combat chain)

- `src/effects_runtime.py` — the `EffectsRuntime` class above.
- `src/effects/chain_aura.py` — the first handler. Implements per-answer pulse + persistent border aura + milestone bursts + reduced-motion fallback. Bounded particle budget 64, bounded rotation speeds, bounded alpha surface size.
- `data/ui/effects_config.json` — ships with ONE effect defined (`chain_math_combat`); schema accommodates future effects.
- Hook into `_draw_quiz`:
  - Call `effects_runtime.observe(scope_id=qe._session_id, snapshot={...})` after each `QuizEngine.update()`.
  - Compute panel geometry as today; pass it as `protected_rects` to `effects_runtime.draw_background` and `.draw_foreground`.
  - Draw ordering: dim overlay → effects background → opaque panel + text → effects foreground.
- Context-modal pause: `_draw_quiz` already checks `qe._timer_paused`; the effects runtime reads the same flag.
- Reduced-motion: first version via env var `PQ_REDUCED_MOTION=1` (fastest to ship — no settings UI required). A proper toggle lives in the eventual settings system (future work).

**Explicit scope restriction:** this handler activates ONLY for `subject='math' AND mode=CHAIN AND combat target present`. Study-mode math, equipment-math-quiz (none today, but hypothetical), and mystery math-chain stay unchanged.

**Estimated effort:** 1 Opus agent, 3-5 hours. New files: 3. Modified files: 2 (game_render.py `_draw_quiz`, main.py `update()`).

### PHASE 2 — Preview + lifecycle tests

- `src/dev_tools/effects_preview.py` — standalone pygame window with keyboard controls: `[`/`]` chain up/down, `R` right, `W` wrong, `T` timeout, `N` new session, `M` toggle reduced-motion, `C` toggle context pause. Uses the actual EffectsRuntime path, not a mock.
- Lifecycle tests (new file `tests/test_effects_runtime.py`):
  - Load config → validates every known handler + palette + bounds.
  - `observe()` idempotency — repeated calls with identical snapshot do NOT emit extra bursts.
  - Milestone single-fire — including chain jumps (auto-pass tiered mastery) and chains >20.
  - Wrong-answer / timeout do not emit success bursts and do not erase chain state.
  - `reset_scope()` clears particle pools cleanly; two consecutive zero-chain sessions each get their first-answer pulse.
  - `paused=True` freezes timers; `paused=False` resumes without replay.
  - Non-math subjects / non-combat chain-mode quizzes get no effect.
  - Chains > 100 stay within particle + opacity bounds.
- Frame captures at chains 0, 1, 3, 5, 10, 15, 20, 25 (normal + reduced motion) saved under `docs/audits/effects_preview_YYYY-MM-DD/`.

**Estimated effort:** 1 Opus agent, 2-3 hours. New files: 2. Modified: 0.

### PHASE 3 — Extend to one more consumer (prove the pattern)

Pick ONE non-chain effect to validate that the runtime generalizes. I'd propose:

**Option A — Identify success orb** (grammar/philosophy threshold-mode). Fires on `_identify_item` success. Scope = one-shot event, not per-session. Tests `fire()` path.

**Option B — Scroll-read success flourish** (grammar threshold). Fires on `_read_scroll` success. Same shape as A but for a different subject/mode.

**Option C — Level-up / stat-gain burst** (not quiz-scoped at all). Fires on `player.level_up()` and `player.gain_stat()`. Tests fully event-driven effects outside the quiz UI.

**I'd recommend A (identify success).** Identify is already a high-moment "aha" interaction. An orb-pop effect reinforces it. Keeps us close to the quiz-adjacent space where the runtime already has integration points; proves the one-shot `fire()` path without needing a brand-new call-site integration (`_identify_item` already has a success callback).

**Estimated effort:** 1 Opus agent, 2 hours.

### PHASE 4 — In-person playtest + ship

- Launch (`python src/main.py`) — fight several monsters, observe chain 1/5/10/15/20 feel.
- Tune `effects_config.json` based on readability + feel. User-driven; agent proposes concrete deltas but user makes the final calls.
- Confirm: identify-success orb is satisfying but not disruptive.
- Confirm: Divine Intercession + Unicorn still show the full-screen takeover (not broken by Phase 0 gating).
- `pytest tests/ -q` green.
- v2.21.0 commit + tag + push → CI build.

**Estimated effort:** me, direct. ~30 min for the commit/ship cycle. Playtest time is on you.

### PHASE 5 — Migrate the two remaining `_draw_celebration` call sites (optional, later)

The full-screen Divine Intercession + Unicorn celebration stays live through Phase 4. Phase 5 (future, not in this plan) migrates them into the EffectsRuntime as named effects (`divine_intercession_takeover`, `unicorn_bond_takeover`) so the entire visual-effects surface is one system.

---

## Total scope + cost

| Phase | Deliverable | Opus agent est. |
|---|---|---|
| 0 | Legacy cleanup + session_id + celebrate_on_max gate | ~45 min |
| 1 | EffectsRuntime + first chain handler | ~4 hours |
| 2 | Preview tool + lifecycle tests | ~2 hours |
| 3 | One extension effect (identify orb) | ~2 hours |
| 4 | Playtest + ship v2.21.0 | ~30 min (me) |
| **Total** | | **~9 Opus-hours + playtest** |

All agents `model: 'opus'` per memory. Phases 0-3 can be a single Opus agent per phase, OR Phases 0, 1, 2 fired in sequence (each depends on the previous) and Phase 3 as a separate agent after Phase 2 lands.

---

## Open decisions needed from you

1. **Legacy array-chain unique weapons** — migrate them to polynomial `chain_exponent` (silent balance change, more work), OR gate them explicitly with `celebrate_on_max=False` (simpler, no balance change). I lean (b).

2. **Phase 3 extension choice** — identify orb (my pick), scroll-read flourish, or level-up burst?

3. **Reduced-motion mechanism** — env var `PQ_REDUCED_MOTION=1` for the first version (my proposal), or build a tiny settings UI in Phase 1?

4. **Phase 5 migration of Divine Intercession + Unicorn** — do now (part of Phase 1) for architectural purity, or defer until after v2.21 ships?

5. **Shipping cadence** — one v2.21.0 release at Phase 4 (my proposal), or ship v2.21.0 after Phase 1 (chain effects only) and v2.22.0 after Phase 3?

Give me the calls and I fire Phase 0 immediately.
