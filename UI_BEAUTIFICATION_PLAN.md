# UI Beautification Plan

**Date:** 2026-10-04
**Source:** user's uploaded `UI_CHANGES_REVIEW.md` (dated 2026-10-03), which describes a UI cleanup pass done in a parallel session that was **never merged into our codebase** — commit `46b5125` and the referenced test/audit files don't exist in our tree. The doc's section 3 ("Implemented UI cleanup") and section 4 ("Remaining UI improvements") are both TO-DO from our v2.21.0 state.

The chain-effects design in section 2 of the doc is **done** — shipped in v2.21.0 (`src/effects_runtime.py`, `src/effects/chain_aura.py`, etc.). Nothing to carry over from that section.

---

## What our code looks like today (verified)

| Item | Current state | Doc's "fix" status |
|---|---|---|
| `_threshold_line("Equip", N)` → `"Equip: N correct (any wrong = fail)"` | Repeated at 12+ sites (kit panel, lore dossier, inspectors) + the quiz modal subtitle | Doc says: remove from everywhere except the quiz modal. Not done in our tree. |
| Combat HUD row heights | `row_h = 64` fixed at `game_render.py:3021`; probably similar fixed offsets elsewhere | Doc says: measure font heights. Not done. |
| Sidebar attributes layout | Need to verify (currently 3-col × 2-row?) | Doc says: switch to 2-col × 3-row. Not done. |
| Sidebar "Depth" vs "Floor" | Need to verify duplicate exists | Doc says: delete Depth, keep Floor. Not done. |
| Panel footer `[C] context` hint vs scroll count | Need to verify overlap at narrow widths | Doc says: measure, split regions. Not done. |
| Decision menu count label | Need to verify 12px vs 22px overlap | Doc says: reserve dedicated area. Not done. |
| Message log token wrapping | Need to verify oversized tokens overflow | Doc says: use shared wrapping helper + zero-row guard. Not done. |
| Quiz layout truncation at small windows | HIGH priority in doc section 4 | Not done. |
| Tab strip overflow | HIGH priority in doc section 4 | Not done. |
| Item inspector repetition ("Appearance" / "Status" / "Type" / "Hidden" / "Next action") | MEDIUM priority — need to verify | Not done. |

---

## Scope decisions

**Fold the doc's sections 3 and 4 into one UI beautification pass.** No reason to split them — the "implemented elsewhere" work and the "remaining recommendations" all target the same spots and all need the same playtest cycle.

**Exclude from this pass:**
- Chain effects (done)
- Any gameplay / content change
- Any new feature beyond what the doc calls out

**Include:**
- All seven cleanup items from doc section 3
- The two HIGH-priority items from section 4 (layout pre-compute, tab overflow)
- The three MEDIUM-priority items from section 4 that have the biggest payoff (item-inspector simplification, combat-emphasis, sidebar budgeting)
- Skip: consolidate panel helpers (section 4 last row) — it's a refactor, not a visible beautification, defer

---

## The 10 fixes, ordered by impact

### P1 — Readability wins (do first)

1. **Remove repeated "(any wrong = fail)"** from inspectors / kit panels / lore dossier threshold lines. Keep it only in the quiz modal subtitle (where it's the sole context the player needs it). Change `_threshold_line(label, n)` to return `"Equip: 3 correct"` (no parenthetical). The quiz subtitle at `game_render.py:2205` stays as the single source of that warning. **Impact: removes 12 copies of the same warning from the UI.**

2. **Simplify item inspectors** — remove or compress "Appearance", "Status", "Type", "Hidden", "Next action" rows that duplicate what the name + stats already convey. Target: name → tier + slot → key stats → one meaningful action line.

3. **Combat HUD emphasis** — bigger target HP + current damage preview; de-emphasize weapon name, projection text, instruction hints. Font-size and color hierarchy only; no mechanic change.

### P2 — Layout correctness (prevents visual bugs)

4. **Measured combat row heights** — replace fixed `row_h = 64` + any hardcoded 18/46/64/82 offsets with actual font measurements. Prevents clipping when font sizes change.

5. **Pre-computed quiz panel layout** — measure complete content (question + 4 choices + timer + chain counter + context hint) before placing. If total exceeds window, scroll or shrink. Currently content can push beyond the panel edge on small windows.

6. **Tab strip overflow** — keep active tab visible when total tab width exceeds container. Options: scroll the tab strip, or collapse inactive tabs into "…".

7. **Panel footer regions** — split `[C] context` hint vs scroll count explicitly instead of centering across the full footer. Prevents overlap at narrow panel widths.

### P3 — Polish (do once P1+P2 land)

8. **Sidebar attributes 2-col × 3-row** — easier readability for 3-digit stat values.

9. **Delete sidebar "Depth" metric** — duplicates "Floor" in character identity. Frees one row.

10. **Message log token wrapping** — use shared wrap helper, add zero-row guard. Prevents oversized tokens from overflowing the log pane.

---

## Phase plan — 3 phases, 1 agent per phase

### PHASE 1 — P1 readability wins (visible impact, low risk)

Changes `_threshold_line` to drop the parenthetical, sweeps the 12+ call sites. Reworks item inspector row list (compress the 5 cosmetic rows into none). Reworks `_draw_combat_hud` font hierarchy. Updates the quiz-modal subtitle to be the sole "(any wrong = fail)" location.

Tests: existing threshold tests may pin the current `_threshold_line` output — update them to expect the no-parenthetical version. The quiz-subtitle test already checks for `"(any wrong = fail)"` — keep that.

**1 Opus agent, ~1 hour.**

### PHASE 2 — P2 layout correctness

Replace fixed row offsets with `font.get_height() + leading` calculations in `_draw_combat_hud` and nearby panels. Build a `_quiz_layout(qe, panel_rect)` helper that measures content height before draw. Add tab-overflow handling to the shared panel component. Split footer regions.

Tests: new rendered-spacing checks (adapted from the doc's `tests/test_ui_spacing.py` pattern). At minimum: combat rows don't overlap at two panel widths; footer hint doesn't overlap scroll count; tab strip keeps active tab visible when width is constrained.

**1 Opus agent, ~1.5-2 hours.**

### PHASE 3 — P3 polish

Sidebar 2-col attributes. Delete Depth. Message-log wrapping cleanup. Any other small polish surfaced by playtest after Phase 1+2 ships.

Tests: light — sidebar fits in standard window; message log doesn't overflow with pathological tokens.

**1 Opus agent, ~45 min.**

### PHASE 4 — Ship v2.22.0

Me, direct. Commit + tag + push → CI builds.

---

## Testing strategy

The doc notes: *"The project's play-test rule explicitly requires in-person verification for common UI changes. Automated checks do not establish that the whole game UI looks and feels correct."* True. But automated checks catch the pathological cases (overlapping text, zero-height panes) that are easy to introduce.

Pattern per phase:
1. Add rendered-geometry tests (not pixel-perfect — just text-bound regression checks) at two representative window sizes (1280×720 + 1920×1080).
2. Run `pytest tests/ -q` → must stay green.
3. Rely on user playtest for the "does it feel right?" dimension.

---

## Cost estimate

- Phase 1: 1 Opus agent, ~1 hour
- Phase 2: 1 Opus agent, ~1.5-2 hours
- Phase 3: 1 Opus agent, ~45 min
- Phase 4: me, direct, 20 min

**Total: ~4 Opus hours + your playtest + v2.22.0 ship.**

All agents `model: 'opus'` per memory rule.

---

## Open decisions needed from you

1. **Should Phase 2's "pre-computed quiz layout" scroll long content or shrink it?** Doc says "long untimed quizzes may need scrolling; short timed math stays fully visible." I lean: shrink the font slightly for text-heavy subjects (which are untimed), scroll if even that overflows.

2. **Item inspector simplification — how aggressive?** My proposal: keep name/tier/slot/equip-line/key-stats/one-action; drop everything else to an expandable detail view. Could be more or less aggressive.

3. **"Depth" metric** — delete entirely, or move the dungeon-level number somewhere else?

4. **Tab overflow** — scroll strip (preserves all tab labels, keyboard-navigable) OR collapse-to-"…" (prettier but hides tab names)?

5. **Ship cadence** — one v2.22.0 after Phase 3, OR ship v2.22.0 after Phase 1 (readability only) and v2.22.1 after Phase 2+3 (correctness + polish)?

Give me the calls and I fire Phase 1 immediately. Defaults if you say "go": my proposals above (shrink-then-scroll, moderate inspector trim, delete Depth, scroll tab strip, single v2.22.0 ship).
