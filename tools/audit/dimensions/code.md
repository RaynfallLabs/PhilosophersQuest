# CODE — correctness audit

**Read `tools/audit/CONTEXT.md` first.**

## Mission
Find every real bug — single-system or cross-system. Trace invariants across the 7 mixins, the quiz engine, the save/load round-trip, the death-chase state machine, the quirk counter graph, and the status-effect lifecycle. The existing `data/audit/consensus.json` is your prior-art baseline; don't re-litigate confirmed P1–P4 entries there unless you're correcting them or extending them with new evidence. Find what that audit missed.

## Holistic rule exemption
**CODE is exempt from the ≥2-systems rule.** Single-file bugs are in scope. Report them.

## Required deliverable
`tools/audit/deliverables/code_invariant_map.md` — a short structured doc listing the cross-module invariants the codebase relies on, which file owns each, and which you verified vs. flagged as broken. Examples of invariants:
- "On answer, `quiz_engine.on_answer` callback fires for both correct, wrong, AND timeout cases" → check across all quiz callers
- "Every `add_effect()` that stacks must be balanced by a single `remove_effect()` regardless of stack count"
- "DeathMonster survives save/load round-trips because it's stored at game level, not in `self.monsters`"
- "`on_game_over()` is called exactly once per run and always before `delete_save()`"
- "Every quirk counter incremented in one place is decremented/reset only in the canonical place"

Each invariant gets: name, owner-file, status (verified / broken / suspect), evidence file:line.

## Seed threads (investigate at minimum)
1. **Death-chase state machine** — `death_pursues`, `death_monster`, speed escalation in `_handle_death_pursuit_speed` (search for it). Does it survive save/load? Can it desync? What happens if the player teleports? Drops the Stone? Dies during the chase?
2. **Quiz callbacks** — does `on_answer` fire on timeout? On wrong? On the *last* question of a chain? Does the chain-mode "success with score 0" path leak through any caller expecting `result.success` to mean "something happened"?
3. **Quirk counter graph** — there are ~80 quirks (`quirk_system.py:1097-1180`). Are any counters double-incremented? Never decremented? Counted from the wrong event? The existing audit caught one (`hermes_teleports`). Find more.
4. **Status-effect lifecycle** — `apply_effect` stacking, `tick_all` ordering, `_EXPIRE_MSGS` coverage, stat-bonus reapplication on stacked buffs. Check every potion path in `food_system.py:drink_potion`.
5. **Save/load round-trip** — what fields are NOT round-tripped? `correct_answers`, `wrong_answers`, and `_score_saved` are flagged in prior audit. What else? Walk every `state.get(...)` in `load_state()` and find missing keys vs. what `save_game()` actually writes.
6. **Permadeath enforcement** — is the save deleted *before* the game loop resumes on load? Are there code paths that load, crash, and leave the save intact?
7. **The secret victory path** — `_trigger_abyss`, `make_death_bane_scroll`, `complete_tablet_of_second_death`. Does the artifact combination logic handle weird inventory states (Stone held but cursed, Tablet held but unidentified, both held but no Shimmer on level)?
8. **Mixin MRO bugs** — methods called via `self._foo()` across mixins. Any silent shadowing? Any method defined in two mixins?
9. **`tick_effects` not called on monsters** — known finding. Verify it's still broken and trace every place that *should* call it.
10. **Math correctness in `dice.py`** — every JSON file that uses dice notation should parse; spot-check rare formats.

## Finding file schema
Filename: `tools/audit/findings/code/<id>.md` where `<id>` is `code-<short-kebab-slug>`.

```markdown
---
id: code-<slug>
dimension: code
severity: P1 | P2 | P3 | P4
title: <one-line>
status: open
systems: [<system1>, <system2>, ...]   # may be one for CODE
evidence:
  - <file>:<line> — <one-line note>
  - <file>:<line> — <one-line note>
verified: true | false   # true = traced the call graph; false = suspected
discovered: 2026-05-15
---

## What's wrong
<2–6 sentences>

## How to reproduce / where it fires
<concrete steps or call path>

## Suggested fix
<concrete patch direction>

## Notes
<optional caveats, alternatives>
```

## Severity guide (CODE-specific)
- **P1** — Crash, data loss, save-file exploit, secret-victory state corruption, permadeath bypass.
- **P2** — Silent corruption, save-state field missing, mixin invariant broken, quirk counter mis-counted in a way that materially shifts unlock timing.
- **P3** — Edge-case bug, narrow alert/notify regression, off-by-one with bounded blast radius.
- **P4** — Dead code, defensive check that fires but doesn't harm.

## Hard rules
- Two of you are running this dimension in consensus. Do *not* coordinate; do *not* read each other's output. Independent investigation is the point.
- For every finding, **trace the call graph at least once**. If you can't, set `verified: false`.
- Cite `file:line` for every claim.
- Do NOT propose fixes that require touching question banks (`data/questions/*.json`) — those are out of scope for this whole audit.
