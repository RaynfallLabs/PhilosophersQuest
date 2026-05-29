# Bug Bash Triage — 2026-05-28

Synthesis of 305 findings across 7 agents. Tiered for overnight execution.

## Tier 1 — DEFINITE FIXES (safe, high-value, tonight)

### Critical gameplay bugs
- **A2-1**: Per-floor charges save-exploit (`_first_hit_used`, `_death_save_used`, `_tarnhelm_used`, `_quiz_reroll_used`) — save/load refreshes all
- **A2-2**: `_cow_return_level` not saved → reload warps to L0
- **A2-3**: ESC during spell-target burns MP, no refund
- **A2-4**: Monster `int_bonus` mastery uses `=` not `+=` → stomps chain-equip max_mp_bonus
- **A2-5**: `_propagate_identification` only syncs `buc_known`, only walks inventory (doc says id_level + all instances)
- **A2-6**: Stacked-status unequip uses unconditional pop → drops effect even if another item still grants it
- **A3-1**: `QuirkSystem.on_disease_drain` defined but never called → Paracelsus quirk cannot unlock
- **A5-1**: `id_level` default conflict (`5` at 2 sites vs `0` at all others) → standardize on `0`
- **A6-1**: 27 duplicate-choice questions (25 math, 1 AI, 1 grammar) — deterministic regenerate
- **A7-1**: Quiz timer goes to 0 at low WIS → unwinnable combat after cursed drain
- **A7-2**: Ranged ammo consumed before quiz; ESC loses arrow with no refund
- **A7-3**: Spell MP same pattern (same root cause as A2-3)
- **A7-4**: Shielded status promises "halves physical damage" — only wired for monsters
- **A7-5**: Stack-merge silently drops BUC info
- **A7-6**: Cursed-miss-backlash doesn't `max(0, hp - dmg)`

### Quick wins (1-3 lines each)
- **A8-X**: `main.py:3774` uses `'good'` message-type (typo for `'success'`) — falls back to info-grey
- **A8-Y**: 14 fake `try: from chain_passives import X; except ImportError: pass` blocks in `main.py` — dead defensive
- **A4-2**: 4 ring grammar names ("ring of hasted" → "ring of haste"; etc.)
- **A4-3**: `tungsten` armor material orphan — add `exotic_metal` to plate template

### UI critical
- **A1-1**: 3 pet sub-menus early-return missing footer hint (3 sites, same pattern)
- **A1-2**: Combat HUD monster name overflows into right column when long
- **A1-3**: Sidebar equip suffix-before-truncate eats the gameplay-critical info (enchant/cursed)
- **A1-4**: Drop-gold popup uses `GAME_H` instead of `WINDOW_H` (centering)

### Bank fixes (deterministic)
- **A6-1**: 27 math dup-choice fixes (regenerate distractors)
- **A6-2**: 5 trivia stem-leaks (rewrite stem)
- **A6-3**: 6 history generic-label "Mary Celeste pattern" rewrites
- **A6-4**: 6 weasel closers (4 AI, 2 economics)
- **A6-5**: 11 history T1 over-length stems → trim or promote tier

## Tier 2 — Safe overnight cleanups

- **A3**: Dead code removal (~17 functions, ~200 LOC; unused imports). One file at a time + retest.
- **A1**: Various WARN truncation fixes where pattern is clear (~20 sites).
- **A5**: Minor attribute-default standardizations where 1-line uniform replacements don't change behavior.
- **A8 LOW**: f-string-without-placeholder cleanup (F541), unused locals (F841).

## Tier 3 — DEFERRED for morning review

These need design decisions or carry behavioral risk:
- **A4-1**: 4 phantom artifacts (`pandoras_box`, `aladdins_lamp`, `palladium`, `tablet_of_destinies`) cannot spawn. Two have active handlers (dead code). Needs spawn-pool design — DO NOT autonomously change loot mechanics.
- **A4-4**: 26 artifacts lack `mastery_blessing` AND no Artifact branch in `_default_mastery_for` → silent no-op. Needs design choice between conservative default vs explicit per-artifact JSON authoring.
- **A8-HIGH**: 313-elif effect-dispatch refactor (4 functions). Multi-day handler-at-a-time work.
- **A8-HIGH**: `load_state` migration-table refactor (~180 lines compressed to 30). Risky overnight.
- **A8-HIGH**: render/handle_event mega-dispatch (~89 states). Same risk profile.
- **A5**: `apply_stat_bonus` typo validation, `slot` default standardization. Risk of changing silent-fail to explicit-fail breaks gameplay.
- **Doc drift**: `IDENTIFY_SYSTEM.md` `Item.identified` property claim wrong; `07_systems.md` spell-handler list is stale; `project_architecture.md` line count stale. Update in morning report.

## Execution plan

Batches, each = 1 commit + regression test:
1. **B1: Save/load critical fixes** (A2-1, A2-2, A2-6 cleanup)
2. **B2: Quick wins + Paracelsus** (A3-1, A8-X, A8-Y, A4-2, A4-3)
3. **B3: Combat MP/ammo refund + spell ESC fix** (A2-3, A7-2, A7-3)
4. **B4: Mastery + identify integrity** (A2-4, A2-5)
5. **B5: Status + combat math fixes** (A7-1, A7-4, A7-5, A7-6)
6. **B6: id_level default unification** (A5-1)
7. **B7: UI critical** (A1-1, A1-2, A1-3, A1-4)
8. **B8: Math dup-choices** (A6-1, 27 fixes)
9. **B9: Trivia stem-leaks + history generic-labels + weasels** (A6-2, A6-3, A6-4)
10. **B10: History T1 length** (A6-5)
11. **B11: Dead code removal** (A3, ~200 LOC, file-by-file)
12. **B12: Final A1 truncation sweep**

Skip rule: if any batch fails the 665-test regression, revert it, mark in morning report, move on.
