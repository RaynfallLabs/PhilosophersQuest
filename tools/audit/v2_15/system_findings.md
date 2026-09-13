# v2.15.0 Readiness Audit — System Integration + Code Hygiene

**Auditor:** claude opus 4.7 (system-integration + light code review pass)
**Date:** 2026-09-12
**Scope:** cross-system interactions + code hygiene across the chain combat v2 (v2.14.0/v2.14.1) surface area.
**Method:** read-only; no code changes; traced pipelines, grepped for UI-rot, spot-checked risky paths.

Severity: **P0** crash-risk · **P1** integration broken · **P2** interaction anomaly · **P3** UI-rot · **P4** nit

---

## Severity counts

| Level | Count |
|-------|-------|
| P0    | 0     |
| P1    | 3     |
| P2    | 3     |
| P3    | 5     |
| P4    | 3     |

---

## P1 — System integration broken

### P1-1 · Chain combat v2 tier-10/15/20 class-specials are UNREACHABLE

**Systems:** combat, weapons templates, quiz_engine

**Evidence:**
- `src/combat.py:244-668` — `_apply_chain_class_post_damage` dispatches specials at tiers 5/10/15/20 for every weapon class.
- `src/combat.py:1906` — `_max_chain = weapon.max_chain_length if weapon else len(_DEFAULT_MULTIPLIERS)`.
- `src/items.py:629-632` — `max_chain_length` is a property derived from `len(self.chain_multipliers)`.
- Every current weapon template (`tools/balance/generated/templates/weapons/*.json`) ships a 3-6 element `chain_multipliers` array. `max_chain_length` fields in JSON are ignored by items.py. No template sets `chainExponent` / `chain_exponent`.
  - dagger: 4 · light_crossbow: 4 · heavy_crossbow: 3 · club/composite_bow/glaive/great_axe/greatsword/longbow/maul/shortbow/shortsword: 5 · bastard_sword/battleaxe/flail/longsword/mace/quarterstaff/rapier/scimitar: 6.
- `src/quiz_engine.py:408-412` — `if self.max_chain and self.chain >= self.max_chain: celebrate + end`. Every quiz auto-ends at that ceiling.

**What breaks:** Because no weapon can chain past 6, `_apply_chain_class_post_damage` never enters the `tier == 10`, `tier == 15`, or `tier == 20` branches for ANY equipped weapon. All of the following code paths are currently dead:
- 1h Sword C10 bypass-DR, C15/C20 blade_flow stacking + guarded stance.
- Mace C10 armor_crack, C15 stun+armor_crack, C20 stun+armor_crack+bypass-DR.
- 2h Warhammer C10/C15/C20 stun-radius escalation.
- Bow C10 blind, C15 pierce (bypass-DR), C20 vitals x2 + blind + bleed.
- Crossbow C10 slow, C15 skip-reload, C20 ballista line.
- Every axe / spear / halberd / glaive / 2h sword / 2h axe / staff / fist / rapier / dagger / sling tier-10/15/20 branch.
- Every chain rank on the milestone table above "Sharp" (Brilliant/Genius/Prodigy/Mythic). The `_chain_rank` colors + big font at chain ≥ 10 in `game_render.py:2151` never fire.

**Cause:** The chain combat v2 design (`docs/design/chain_combat_v2.md`) is polynomial-unlimited (`mult = n^chain_exponent`, default 1.15). Migration Step 5 (rebase weapon templates, set `chainExponent`, drop the 5-rung array) was NOT executed. Only the material files (Step 6) and the timer (Step 1) were rebased.

**Fix direction:** ship the template rebase — set `chainExponent` on every common template, delete `chain_multipliers` (or leave a stub the polynomial path ignores), and give `max_chain_length` a very-high sentinel (e.g. return `MAX_EFFECT_DURATION` when `chain_exponent` is set). Otherwise the entire "class specials at 10/15/20" system is design-only.

---

### P1-2 · `reloading` status is not registered in `EFFECT_INFO`

**Systems:** status_effects, game_combat, game_render

**Evidence:**
- `src/game_combat.py:1545` — `self.player.status_effects['reloading'] = 2` (crossbow post-fire).
- `src/game_combat.py:1485` — reload gate reads `status_effects.get('reloading', 0)`.
- `src/status_effects.py:21-114` — no `'reloading'` entry in `EFFECT_INFO`.
- `src/status_effects.py:116-147` — not in `DEBUFFS` or `BUFFS`.
- `src/game_render.py:1078-1094` — Character-sheet status list renders it via the `else` fallback: raw id lowercased + no color + no description → "Reloading: 1 turns" with no source.

**Impact:** cosmetic in the character sheet (raw name) but the status is a first-class combat state the player needs to understand. Every other combat-relevant status is registered.

**Fix direction:** add `'reloading': ('Reloading', (200, 200, 240), 'Crossbow string being cranked — cannot fire.')` to `EFFECT_INFO`, add to `DEBUFFS` (it does gate an action), and add an expiry message `('The crossbow is loaded.', 'info')` to `_EXPIRE_MSGS`. The `tick_all` path in `status_effects.py:467-587` already handles the decrement generically, so no other wiring is needed.

---

### P1-3 · v2.14.0 chain-combat statuses + dispatch have no behavior tests

**Systems:** tests (coverage gap)

**Evidence:**
- `grep -l "blade_flow\|armor_crack\|deep_wound\|impaled\|ruptured\|sundered\|_crossbow_skip_reloads\|_chain_bypass_dr\|cancel_and_strike\|chain_exponent" tests/*.py` returns only `tests/test_engine_wave4_unique_mechanics.py`, and that hit is a static source-check (`assert "'blade_flow'" in src`), not a behavior test.
- No test exercises `_apply_chain_class_pre_damage` / `_apply_chain_class_post_damage`, the amp-cap arithmetic (armor_crack + deep_wound → +50%), the `_chain_bypass_dr` one-shot flag lifecycle, `_crossbow_skip_reloads` decrement, SPACE `cancel_and_strike`, or the sundered/ruptured/impaled monster-side hooks.
- 21 files listed as `M ...` in the conversation-open git status; the audit could not verify any of the chain combat v2 flow with unit tests.

**Impact:** every future refactor of `combat.py` risks silent breakage across ~500 lines of newly-shipped dispatch code. Play-test is the only current gate.

**Fix direction:** minimal at ship time — one behavior test per class-tier the player is likely to reach (i.e. tier-5 rows), plus an integration test that armor_crack + deep_wound stacks at 50% cap (not 75%), plus a smoke test that `cancel_and_strike` returns True in ASKING state / False in RESULT state / False in threshold mode.

---

## P2 — Interaction anomalies

### P2-1 · `sundered` description / docstring lies about the multiplier

**Systems:** status_effects, monster, player-facing text

**Evidence:**
- `src/status_effects.py:58` — `'sundered': (..., 'Broken limb: outgoing damage halved')` — the shown description is **halved**.
- `src/monster.py:399-401`, `560-561`, `1516-1518` — three call sites all use `dmg = max(1, int(dmg * 0.70))` (−30%, NOT halved).
- Two of the three docstrings ("Chain combat v2: sundered halves outgoing monster damage") repeat the wrong claim above the 0.70 line.

**Impact:** player-facing tooltip and code comments disagree with actual math. Not a crash, but the sidebar effect card promises −50% and the monster actually swings for −30%.

**Fix direction:** decide the intended magnitude (0.50 to match the description, or 0.70 which is the current tuned number that the P1-1 discussion above notes protects vs `weakened` stacking) and align the description + all three docstrings with the code.

---

### P2-2 · `weakened × sundered` stacking multiplies (not additive) — likely intended but undocumented

**Systems:** monster damage pipeline

**Evidence:**
- `src/monster.py:397-401` (and same shape at 555-561, 1514-1518): sequential ifs — `weakened` halves, THEN `sundered` × 0.70. Combined: `dmg * 0.5 * 0.70 = 0.35x`.

**Impact:** two debuffs stack MULTIPLICATIVELY on the monster's outgoing damage. A "sundered + weakened" mob deals 35% damage, effectively a 65% reduction. If design wants additive-capped stacking (like the armor_crack + deep_wound amp on the player-side offensive path), this is a pipeline inconsistency. If design wants multiplicative, the sundered description ("halved") oversells its solo effect and undersells the stacked case.

**Fix direction:** either cap combined outgoing debuffs at −50% analogous to the `_amp` block in `combat.py:1219-1225`, or document the multiplicative rule.

---

### P2-3 · ESC-during-quiz banks the chain, contradicting the comment ("treat as chain-0 failure")

**Systems:** game_input, quiz_engine

**Evidence:**
- `src/game_input.py:88-92` — `# Cancel the active quiz — treat as chain-0 failure` then `self.quiz_engine._end(success=False)`.
- `src/quiz_engine.py:666-680` — `_end` builds `QuizResult(success=success, score=self.score, ...)`. `self.score` is `self.chain` in chain modes (set by `answer()`:265 and `update()`:299). No zeroing.
- `src/combat.py:891-898` — chain-0 branch (real miss) is only hit when `result.score == 0`.

**Impact:** ESC in the middle of a math chain quiz behaves IDENTICALLY to SPACE — it banks the current chain and lands the strike. The comment saying it treats it as chain-0 failure is stale; behavior changed in chain combat v2 when wrong-answer chains stopped resetting. This is likely correct-by-design in the new model (chain always banks), but the game presents SPACE as the "strike now" affordance while silently offering ESC as a second, undocumented affordance for the same action. ESC in every OTHER menu closes the menu — using it mid-combat-quiz to bank a chain is a subtle inconsistency the help screen does not mention.

**Fix direction:** either (a) update the comment and treat ESC-in-quiz as an intentional escape hatch equivalent to SPACE, or (b) actually zero `self.score` before calling `_end(success=False)` so ESC becomes a real chain-0 abort separate from SPACE's bank. Pick one; the current state confuses debuggers.

---

## P3 — UI-rot / stale text

### P3-1 · Examine screen displays "Perfect Chain Crit x{n}" for a retired mechanic

**Systems:** examine UI, weapon inspection

**Evidence:**
- `src/game_render.py:7306-7307`:
  ```
  if subject.crit_multiplier > 1.0:
      specials.append(f"Perfect Chain Crit x{subject.crit_multiplier:.1f}")
  ```
- `src/combat.py:1078-1085` — "Chain combat v2 (v2.14.0): crit is retired. Chain IS the crit … The `crit` boolean is kept for on_complete kwargs so callers … still compile; it now stays False everywhere."
- `src/combat.py:1365` — "Bracers of Arjuna: Chain combat v2 … was 'crits' via crit_multiplier; retired to a straight 1.5x since crit is gone."

**Impact:** every unique weapon whose JSON still carries a nonzero `crit_multiplier` (Excalibur, Gram, Harpe, Kusanagi, Zulfiqar, Mjolnir, …) shows a stat line advertising a mechanic that no longer fires. The old system's terms leaked past the sweep.

**Fix direction:** drop the block, or replace it with the new equivalent (e.g. surface `chain_exponent`, `bonus_damage_vs_tag`, or a stanza that reads whichever unique-mechanic key drives the weapon's identity).

---

### P3-2 · Examine screen "Chain Multipliers: x0.5 x1.0 x1.5 x2.0 x2.5" is meaningless for the fist / any future polynomial weapon

**Systems:** examine UI

**Evidence:**
- `src/game_render.py:7312-7315` — prints `weapon.chain_multipliers` unconditionally.
- `src/combat.py:941-947` — actual damage uses `chain ** chain_exponent` when the weapon has `chain_exponent` set. `chain_multipliers` is inert on that path (see the `multipliers = None` branch).
- For any polynomial weapon `chain_multipliers` is still the fallback default `[0.5, 1.0, 1.5, 2.0, 2.5]` — the examined stat line then LIES about what a chain-5 hit will do.

**Impact:** currently latent (no weapon ships `chain_exponent`), but goes live the second Step 5 of the migration lands. Also latent for the fist, which uses `chain_exponent = 1.15` inline but has no weapon object to examine.

**Fix direction:** when `chain_exponent` is set, print the exponent + a reference table (e.g. "chain 5 → x6.5, chain 10 → x14.1"). Match the design doc's reference table.

---

### P3-3 · "chain x{item.max_chain_length or '?'}" in the pack view

**Systems:** kit / pack rendering

**Evidence:**
- `src/game_render.py:3129` — `detail = f"{...}  chain x{item.max_chain_length or '?'}"`.

**Impact:** for a polynomial weapon `max_chain_length` still returns 5 (the length of the default chain_multipliers list) and is not a mechanical ceiling. The display suggests a hard cap that does not exist under chain combat v2.

**Fix direction:** either drop the "chain x N" column for chain-v2 weapons or replace it with the base damage / exponent pair.

---

### P3-4 · Stale comment "Bare-hand chain table. Caps at the universal 5-chain like every common template" in `combat.py`

**Systems:** combat

**Evidence:**
- `src/combat.py:5-11` — `_DEFAULT_MULTIPLIERS` comment claims a "universal 5-chain" cap that the design doc explicitly retired (chain combat v2 is polynomial-unlimited by design).

**Impact:** documents a design that was superseded. Also cross-references the "Fixed 2026-05-19" note which pre-dates chain combat v2.

**Fix direction:** rewrite the comment to say "unarmed fallback used only when a weapon has neither `chain_exponent` nor `chain_multipliers`" (and note that unarmed itself uses the polynomial path at exponent 1.15).

---

### P3-5 · `game_render.py:2469` SPACE hint at chain 0 says "SPACE cancels (chain 0)" but SPACE at chain 0 also lands as a real miss (with all the cursed-weapon backlash etc. that a real miss triggers)

**Systems:** combat HUD

**Evidence:**
- `src/game_render.py:2469` — `"SPACE = strike now" if cur_chain >= 1 else "SPACE cancels (chain 0)"`.
- `src/quiz_engine.py:651-664` — `cancel_and_strike` always ends the quiz with `success=True` regardless of chain.
- `src/combat.py:891-898` — chain 0 goes through the real miss branch: cursed_miss_backlash applies, damoclean counter resets. Same as a wrong-answer miss on Q1.

**Impact:** the word "cancels" implies the attack didn't happen; in practice it did happen and cost you cursed-weapon HP or reset your Damoclean counter. Minor.

**Fix direction:** change the hint to "SPACE = give up (miss)" so the player understands they are eating the miss.

---

## P4 — Nits

### P4-1 · `items.py:316` treats `chain_exponent = 0.0` as missing

**Evidence:** `self.chain_exponent: float | None = float(_ce) if _ce else None`. `0.0` is falsy → None. Consistent with the combat.py path (which also treats `if _chain_exp and _chain_exp > 0` as "polynomial off"), but the `if _ce` pattern should be `if _ce is not None` if the field is ever set to explicit 0.0 by a designer testing "unarmed style" for a wand-like weapon.

### P4-2 · `_apply_chain_class_pre_damage` sets `player._chain_bypass_dr` as a one-shot side channel with no explicit reset if the callback returns early

**Evidence:** `src/combat.py:187-197` writes the flag; `src/combat.py:1241-1243` consumes it. The chain-0 early-return at line 897 fires BEFORE pre-damage runs, so no leakage on a miss. The `if monster.is_dead(): return` at 901 also runs before pre-damage. So the current lifecycle is safe — but the pattern is fragile: any new early-return between line ~960 and ~1244 would strand a `True` on the player. Consider consuming inside the pre-damage function itself and returning a bool for the caller to route.

### P4-3 · `_DEFAULT_MULTIPLIERS` is now mostly dead code

**Evidence:** `src/combat.py:941` — `_chain_exp = getattr(weapon, 'chain_exponent', None) if weapon else 1.15`. When weapon is None (fist), the polynomial path is taken; the `else multipliers = _DEFAULT_MULTIPLIERS` branch is unreachable for weapon==None. The only remaining use is `_max_chain` on line 1906 for the unarmed cap. Consider replacing `_max_chain = ... else 5` with a named constant (`FIST_MAX_CHAIN = 5`) and dropping the array.

---

## Well-wired vs shaky — the 6 new v2.14.0 statuses

| Status                | Wiring       | Notes |
|-----------------------|--------------|-------|
| `armor_crack`         | **solid**    | Applied by mace/warhammer post-damage; consumed by the `_amp` block at 1219-1225; caps additively with `deep_wound` at +50%; registered + colored + described in EFFECT_INFO; tick decrement via generic `tick_all`. |
| `deep_wound`          | **solid**    | Applied by fist/dagger post-damage; blocks regen (`monster.py:290-292`); adds +25% amp; correct stacking cap with `armor_crack`. |
| `ruptured`            | **solid**    | Dagger C20 signature; ticks 10% max_hp/turn in `monster.py:257-261`; blocks regen at 290-292. Only "shaky" note: the C20 tier that applies it is currently unreachable per P1-1. |
| `impaled`             | **solid**    | Same shape as `stuck_in_pit` — monster can still attack adjacent but cannot move (`monster.py:760-766`). Applied by spear C20; also unreachable in practice per P1-1. |
| `blade_flow`          | **shaky**    | Stack counter (max 10 via `_player_stack`), decrement per attack (`combat.py:1231-1236`), used to bypass DR. Only granted by 1h_sword C15/C20, 2h_sword C20, and Soul Reaver's `growth_on_innocent_kill` — the class-tier grants are UNREACHABLE (P1-1). Soul Reaver innocent-kill grant works, but is a rare corner case. Effectively, the whole system is exercised only via a niche unique. |
| `melee_dmg_reduction` | **shaky**    | Player-side buff, −30% incoming physical (`player.py:273-279`); OK on wiring, but ONLY granted by rapier/1h_sword/staff C15/C20/C10-radius branches (all unreachable per P1-1). Zero real coverage today. |
| *(bonus)* `reloading` | **broken cosmetic** | See P1-2. |

**Summary:** all six mechanics are wired correctly on the CONSUMER side (they apply their intended effect if the status is present). Four of them (`blade_flow`, `melee_dmg_reduction`, and effectively `ruptured` / `impaled`) have PRODUCER sides that never fire under the current weapon roster, so end-to-end they are theatre. Once the weapon template rebase (P1-1) ships, they all become live.

---

## UI-rot patterns found

- **Crit language:** one live leak (`Perfect Chain Crit` on the examine card, `game_render.py:7307`). Sweep is otherwise clean — `grep -Ei 'crit|critical'` across `src/` returned nothing new after the retirement.
- **Chain-array display:** `game_render.py:7312-7315` and `3129` both print static per-rung / max-chain values that will lie the second the polynomial path lights up. Currently correct-by-accident.
- **`_DEFAULT_MULTIPLIERS` comment** claims a "universal 5-chain" cap that was retired (`combat.py:5-11`).
- **ESC-in-quiz comment** claims "treat as chain-0 failure" (`game_input.py:90`); actual behavior banks the chain like SPACE.
- **`SPACE cancels (chain 0)`** hint (`game_render.py:2469`) elides the fact that a chain-0 SPACE still eats cursed-weapon backlash / Damoclean reset.

No stale "mastery", "cook v1", "harvest v1", "at max chain 5" strings were found in the src/ tree; the v2.9.1/v2.12.1 sweeps look clean.

---

## Notes / smaller findings

- **Circular imports:** none. `monster.py` imports `combat._line_of_sight` at module scope; `combat.py` never imports `monster` or `items` at module scope (only lazily inside functions via `from armor_procs import ...` / `from dice import ...`). Safe.
- **TODO / FIXME / HACK / XXX comments:** zero real ones in `src/` (one false positive: `STATE_HACK_REALITY` — that's a legit state name for the XYZZY-style AI hack feature, not a code marker).
- **camelCase / snake_case field handling on `Weapon`:** every field ships both spellings (`baseDamage`/`base_damage`, `chainExponent`/`chain_exponent`, `chainMultipliers`/`chain_multipliers`, `stunChance`/`stun_chance`, …) at load time (`items.py:298-350`), and the runtime path always reads the snake_case attribute. No divergent reader found.
- **`_crossbow_skip_reloads`:** decrement path (`game_combat.py:1540-1545`) is correct: skip counter is checked FIRST, so a shot with `skip > 0` never sets `reloading`. Persists cleanly across save/load (plain int attr on the player, no `__getstate__` filter). Interaction with `reloading` tick: `reloading = 2` at fire → ticks to 1 at end-of-turn → gate blocks next fire → any player action ticks to 0 → next fire allowed. Matches "fires every other turn" per design.
- **`chain_exponent` persistence:** `items.Weapon.__init__` reads both camelCase and snake_case, so an old pickled Weapon without the field will get `None` (falsy → array path), and a new-JSON weapon will get the float. Backward-compat safe.
- **Chain 0 miss handling:** the callback correctly guards `if chain == 0: on_complete(0, is_dead, chain); return` BEFORE any of the pre-damage / post-damage hooks fire. `blade_flow` stacks are NOT consumed on a miss (verified — decrement is downstream of the guard). Good.
- **`_amp` cap on player offense (armor_crack + deep_wound):** correctly hard-capped at +50% (`combat.py:1219-1225`, `min(0.50, _amp)`). Adding a third +25% status later would still cap at 50%.
- **Chain rank display:** `_chain_rank` at `game_render.py:2058-2064` returns descending-first, so higher milestones win when ties (e.g. chain 20 returns 'Mythic', not 'Prodigy'). Correct.
