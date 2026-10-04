# Conventions — Cross-Cutting Rules

**v2.23.0** (shipped 2026-10-04)

Short, dense, actionable. If you only read one doc, read this one.
Everything here is enforced by code, by player experience, or by the
project memory. Breaking one of these rules will usually surface as a
play-test regression or an audit finding.

---

## 1. Zero-tolerance threshold quizzes

**Rule:** any wrong answer in a threshold-mode quiz ends that quiz as a
failure.

- Lives in `src/quiz_engine.py::QuizState`. The `threshold` and
  `escalator_threshold` modes both close on first wrong.
- Chain-mode (combat only, see §2) is the exception.
- The only in-game override is the **Tablet of Destinies** reroll.
- Historical: pre-zero-tolerance thresholds like "6 correct in a row"
  are still tuned loosely in some mystery altars — SYSTEMS_AUDIT §3 P2
  notes `solomon`, `grail`, `oracle`, `mjolnir`, `sphinx`.

**Player-facing surface:**
- The quiz modal does **not** print the rule. v2.22.0 moved the
  `(any wrong = fail)` warning off the item cards and into a red
  subtitle under the quiz-header counter; the 2026-10-04 playtest
  (v2.23.0) removed that subtitle as well. The rule itself is
  unchanged — only the on-screen reminder is gone.
- A threshold quiz that needs more than one correct answer shows
  `{correct_count} / {required}` in the header. One-question quizzes
  (identify, harvest, cook, lockpick) show no counter at all — "0 / 1"
  tells the player nothing.
- Every item card / lore dossier / bestiary string that prints a
  threshold value uses `_threshold_line(label, n)` from
  `game_render.py:54` → **"Equip: 3 correct"**. Do not hand-roll a
  threshold line, and do not re-add the parenthetical — not to the
  helper, not to a caller, and not to the quiz modal (see §12 of
  [ui.md](ui.md)).

**If you forget this rule:** nothing on screen will correct you. New
copy that implies partial credit ("3 of 5", "best of") reads as true
to the player, because the quiz modal no longer states the
zero-tolerance rule. See SYSTEMS_AUDIT §8 P2 for the original 11 call
sites (migrated 2026-10-02, de-duplicated 2026-10-03, subtitle removed
2026-10-04).

---

## 2. Chain v2 (combat only)

**Rule:** combat uses `QuizMode.CHAIN`. A wrong answer **does not zero
the chain** — the strike lands at the achieved chain. Chain 0 (first
answer wrong) is a miss. Peak-chain damage, not threshold-count.

- Damage: `base * (chain ** chain_exponent) * damage_type_multiplier`
  on polynomial weapons, or `base * chain_multipliers[chain-1] * dm`
  on legacy array weapons. See `combat.player_attack` and
  `game_render._draw_combat_hud`.
- `chain_exponent` defaults to 1.15 unarmed and on most weapons;
  legacy array weapons set `chain_multipliers` directly.
- `cursed_miss_backlash` fires only when the chain closes at 0.
- The player can **SPACE** to strike-now at any chain ≥ 1 — the quiz
  closes, the strike lands at that chain.
- Threshold quizzes do NOT use chain. "Chain break" is dead vocabulary;
  do not re-introduce it.

**Milestone ranks** are rendered in `_draw_quiz` via `_chain_rank` —
the counter grows font-size at chain 10+ and recolors at each
milestone. This is the one place "chain" is a visible scoring unit.

---

## 3. Math is the only timed subject

**Rule:** the chain-math quiz in combat has a per-WIS timer. Everything
else is **untimed**.

- Table: `src/player.py::SUBJECT_TIMER` — currently holds only
  the `'math'` row `(0, 1.0)` (flat WIS seconds). All other subjects
  are untimed; the engine forces `timed=False` for them at
  `quiz_engine.py:191-193`. Non-math rows were purged 2026-10-03
  to make the "only math is timed" rule obvious from the data.
- `QuizEngine` sets `qe.timed = False` for non-math quizzes.
  `_draw_quiz` suppresses the timer bar entirely (L2220 branch).
- **Dead copy to delete on sight:** any help text that says "quiz
  timers extended" / "+Ns on magic subjects" / "all quiz timers" —
  the mimir-well reward, Sisyphus parenthetical, and 16 other quirks
  still carry the "if X ever becomes timed" tail. See SYSTEMS_AUDIT §8
  P3 and the `Character Sheet` lines 1032-1038 of `game_render.py`.
- Timer-granting rewards for non-math subjects **do not fire**. Design
  rule for new rewards: if the subject isn't math, grant a stat bump
  or a save bonus, not a timer bump.

---

## 4. Resource loss IS the penalty

**Rule:** a quiz-gated action that CONSUMES the target on attempt
(harvest, cook, equip, lockpick) does not need a stacked stun or
debuff on failure. The lost corpse / ingredient / chest-tier / gear
slot IS the cost.

Current one-question binary actions (each v3+):
- **Cook v2** — `food_system.py`; 1 cooking Q at the recipe's outcome
  tier; wrong = ruined meal (ingredient destroyed).
- **Harvest v4** — `food_system.py`; 1 animal Q at `corpse.harvest_tier`;
  wrong = corpse destroyed.
- **Lockpick v3** — `main.py`; 1 economics Q at chest tier; wrong =
  trap from `chest_traps.json` (NOT a quiz penalty — the trap IS the
  consequence of a failed pick, matched to chest tier not floor tier,
  v2.6.6 fix).
- **Identify v3** — exception, see §5. Identify does NOT consume the
  item, so it carries a 10-turn stun on failure.

**If you forget this rule:** cook / harvest / lockpick get doubled
penalties that make them unfun. See the memory bullet
"resource-loss-is-the-penalty".

---

## 5. Flow over gradient for high-frequency actions

**Rule:** high-frequency quiz-gated actions (identify, harvest, cook)
get ONE question with a binary outcome. The reward for playing well is
that the **game flows** — not tier-scaled loot.

- Identify v3 (2026-08-06): one philosophy Q at derived id_tier. Right
  = full ID. Wrong = Stunned 10 turns. **NO masteries.** No tier
  progression. All three mastery stores (class, family, identify)
  deleted.
- Harvest v4: one animal Q at `corpse.harvest_tier`. Right = prime cut
  OR trophy. Wrong = corpse gone.
- Cook v2: one cooking Q at `outcome.tier`. Right = outcome applied
  (SP / HP / temp buff / permanent bonus for trophies). Wrong = ruined
  meal.
- Low-frequency attempts (pray, boss math, mythic scroll) MAY use
  chain quizzes — chain is for peak events, not routine ones.

**Design principle:** escalator chains sound rewarding on paper but
ruin real play by punishing novice performance on routine actions. If
a new system is high-frequency, it is one-Q binary.

---

## 6. No masteries (2026-08-06 removal)

**Rule:** none of class, family, or identify masteries exist.
`stuffies` is a plain `carry_bonus` field.

Removed stores (migrated out of saves by `player.__setstate__`, see
[save_meta.md](save_meta.md)):
- `class_masteries`
- `subject_mastery_xp`
- `identify_masteries`
- `family_mastery_blessings`, `family_masteries`
- `weapon_masteries`, `shield_masteries`
- `stuffies_active`, `_active_stuffies`

**Vocabulary cleanup:**
- "MASTERY!" toast was renamed to **"TIER N {subj} CLEARED"** in
  `main._on_quiz_answer` L4929.
- Discoveries panel renders **"T{ti} CLEARED"**, not
  "T{ti} MASTERED" — `_discoveries_sections` L4087.
- Per-run tier-clear (auto-pass) is still a thing — a (subject, tier)
  that has had every distinct question answered correctly in this run
  auto-succeeds for the rest of the run. The vocabulary moved from
  "mastered" to "cleared" to disambiguate.

**If you see any of these in UI or logs, fix it in the same commit:**
`class mastery`, `family mastery`, `identify mastery`, `weapon mastery`,
`shield mastery`, `MASTERY!`, "Earned through quirk mastery", `MASTERED`
(as a stand-alone badge). The two remaining legitimate uses of the word
"mastery" are the flavor strings in `quirk_system.py` L1497 and L1503.

---

## 7. Save-bonus gradient (never immunity)

**Rule:** stacking save bonuses gives a defense gradient, never
hard-caps to immunity.

- `Player.save_bonus_for(cat)` — permanent bonuses stack, timed bonuses
  stack SEPARATELY and cap at **+3**, final total capped at **+5**.
- Pass-through for non-SAVE_STAT effects (poison, bleeding, burning)
  bypasses the bonus; the Torque of Lugh "all saves" promise is weaker
  than its copy — see SYSTEMS_AUDIT §9 P1.
- Categories: `CON`, `WIS`, `DEX`, `all`.
- Code lives in `src/player.py`; gear wiring in `_gear_save_bonus`,
  quirks in `_quirk_save_bonus`.

Never add a save-bonus path that bypasses `save_bonus_for`. The cap is
the whole point.

---

## 8. Karma clamp −10..+10

**Rule:** karma lives in `Game.karma`. Clamped to −10..+10 everywhere
except two edge cases that are flagged in the audit.

- Primary setter: `_award_encounter_outcome` applies the clamp.
- Judgment tiers (`_JUDGMENT_TIERS` in `game_divine.py`) map the clamped
  value to a tier at the L99 altar.
- Penitent weapon's `kill_count_karma_adjust` bypasses the clamp
  (safe today because it only triggers when karma < 0 — see
  SYSTEMS_AUDIT §4 P2).
- If you add a new karma-grant path, use the helper, not raw
  `self.karma += n`. (A `_adjust_karma(delta)` helper is a recommended
  consolidation point.)

---

## 9. SP soft-boundary + damage failsafe

**Rule:** SP = 0 still starves the player (damage over time). The
softness comes from **generous supply** — cook tier averages (58 SP at
T1 → 156 SP at T5) and food restores (20–115 SP) are tuned so that
normal play never bottoms the tank. Raw prime cuts are a 10–30 SP
emergency.

- Do NOT remove starvation damage.
- Cook outcome tier bands:
  - T1: SP 30–50, HP 0–6, 30t buff
  - T2: SP 50–75, HP 4–10, 60t buff
  - T3: SP 75–110, …
  - T5 (trophies): SP ~150, HP ~22, 200t buff + `permanent_power`
- Raw ingredient SP values live on `ingredient.json::raw_sp` and sit
  at 10–30; the player uses raw to buy time to cook, not to live off.

---

## 10. Chain-v2 miss semantics ≠ chain break

**Rule:** `combat.py` has one path for "the strike happened at chain
N". A miss (chain 0) is a strike that landed at zero multiplier — not a
"chain break" (that term is retired).

- `_chain_disrupt_pending` is a dead-wired flag on
  `abaddon_destroyer`; no code reads it. Delete when touching that
  monster.
- `chain_break_on_hit: 0.35` on Abaddon is similarly dead.
- `attack_chain_cap_bonus` (Ring of Gawain, Torque of Lugh) applies
  ONLY when `_max_chain is not None` — currently never, because every
  chain-exponent weapon leaves `_max_chain` unset. See SYSTEMS_AUDIT
  §2 P2.

---

## 11. Secret builds are intentional fun — do not demystify

**Rule:** `welcome_screen.SECRET_BUILDS` ships 30+ hidden character
names (philosophers, warriors, Dad, Titivillus, etc.) that unlock when
the player types that name at the welcome prompt. The surprise IS the
feature. Do not list them in help text, do not spoil them in the
encyclopedia.

- **One exception: Titivillus is gated** behind the `PQ_QA_MODE=1`
  environment variable or the `--qa` CLI flag
  (`welcome_screen.py:472-476`). A build with `_qa_tools: True`
  returns None if neither gate is set, so a casual player who
  guesses the name does NOT get Shift+I immortal or Shift+W floor
  warp. The `dad` build (`_immortal: True`, all stats 20) remains an
  intended easter egg.

See the memory bullet "secret-build-fun" and SYSTEMS_AUDIT §7 P2.

---

## 12. "Run it" means source, not bundle

**Rule:** when the user says "run it" or "launch", it means
`python src/main.py`. Never the dist exe — the frozen build writes to
`%APPDATA%\PhilosophersQuest\` (different save dir, different
highscores file) and masks dev changes. Kill prior `python.exe`
before relaunching.

Codified in `paths.py::save_dir()` — see [save_meta.md](save_meta.md).

---

## 13. System-change sweep rule (added 2026-09-06)

**Rule:** when a game system is renamed, redesigned, or removed, do a
**full-codebase grep for the OLD system's terms, symbols, field
names, comment references, help text, message strings, and menu
labels** — not just the direct call sites. Fix stale UI, tooltips,
log messages, docstrings, and comments **in the SAME commit** as the
mechanical change.

**High-risk files to check every time:**

1. `src/game_render.py` — menus, panels, cards, lore screens
2. `src/game_menus.py` + `src/fantasy_ui.py` — menu strings
3. All `add_message(...)` / `_log_chronicle(...)` calls in
   `src/main.py` + mixins
4. `src/game_render.py::_draw_help_screen` — help text + System Rules
   card bullets
5. Docstrings and comments in `src/main.py` (mixed-system file)
6. `src/mystery_system.py` challenge configs
7. `src/quirk_system.py` descriptions + flavor strings
8. `src/hero_specials.py` — passive gates, special descriptions
9. Any `data/*.json` schema fields on the retired system
10. `src/ui.py::Sidebar._derived` + `_effects` + `_powers` labels

**Pytest will NOT catch text-only regressions.** A menu that still
says "5/5" when the system is now binary passes every test. When in
doubt, `rg` for the old term across ALL of `src/` and read every hit.

**Save-file compatibility with old written state is a separate
concern** — usually document as-is in `player.__setstate__`, only
migrate on explicit user request. See
[save_meta.md](save_meta.md#migration).

---

## 14. Zero API spend — all LLM work via Opus subagents

**Rule:** every Agent / Workflow / sub-agent call sets `model: "opus"`.
No direct Anthropic API spend. Project memory: "No API spend, explicit
Opus."

Not a code rule but a workflow invariant — breaking it burns the
user's budget silently.

---

## 15. Deliverables go in the project root with a loud name

**Rule:** anything the user must READ (audit reports, migration
summaries, playtest instructions) goes in the project root with a loud
`SCREAMING_SNAKE_CASE.md` name AND a full absolute path quoted when
mentioned in chat. Scratch work stays in `_archive/` or `_scratch/`
subdirs.

See `C:\Users\brand\Documents\PhilosophersQuest\SYSTEMS_AUDIT.md` and
`...\ITEM_QUIZ_AUDIT.md` for the pattern.

---

## 16. Play-test rule has limits

**Rule:** for randomized loot, late-game content, deep-dungeon spawns,
or probabilistic effects, play-testing is impractical. Write logic
tests instead — at minimum a data-layer test (load the JSON, assert
the mechanical fields are set correctly), and a pure-function test
where the mechanic is implemented in a standalone module.

For player-facing mechanics easily reachable in a few minutes of play
(combat basics, equipping common gear, food prep, common UI), the
user plays the game in person before the feature is "done". Claude
can't drive Pygame, so unit tests alone don't prove the feature
works — say so explicitly.

---

## 17. Execute fully then play-test once

**Rule:** when the user approves a multi-phase task, implement ALL
phases autonomously, validate via pytest, and surface ONE consolidated
play-test request at the end. Never checkpoint-and-ask mid-task.

Project memory: "Execute fully, then ONE play-test."

---

## 18. Visual effects runtime + reduced motion

**Rule:** visual effects (per-answer chain feedback, fullscreen
takeovers, the identify orb, the end-of-attack strike finisher) live
in the
`EffectsRuntime` (`src/effects_runtime.py`) with per-effect handlers
under `src/effects/`. Config is `data/ui/effects_config.json`.
Adding a new effect = append a config block + a handler class +
register it in `build_default_runtime`. See
`docs/design/effects_runtime.md` for the authoring guide and
the handler protocol.

Reduced-motion mode is Phase 1 opt-in via the env var
`PQ_REDUCED_MOTION=1`:

```powershell
$env:PQ_REDUCED_MOTION='1'; python src/main.py
```

Each handler reads the per-effect `reduced_motion.disable` list from
its config (`"particles"`, `"rotating_runes"`) + optional
`shorten_to_ms` (one-shot), `static_ms` (strike finisher) or
`replace_milestone` (chain). A proper
in-game settings UI for this toggle is future work -- Phase 1 ships
the env var only.

---

## 19. Display names are title case (v2.23.0)

**Rule:** the player never sees an all-lowercase name. Data files
author most item and monster names in lowercase (`"giant rat"`,
`"ring of magic resist"`); `src/naming.py` normalises them at the
source so no call site has to remember.

- `naming.proper_name(name)` → `"Ring of Magic Resist"`,
  `"Ox-Hide Shield"`. Joining words (`of`, `the`, `and`, …) stay
  lowercase except at the start. Words that already carry capitals
  (`"STR+1"`, `"McCoy"`) pass through untouched, so it is safe to
  apply twice.
- `naming.ProperNameAttr` is a descriptor on `Item.name`,
  `Item.unidentified_name`, `Monster.name` and `Corpse.monster_name`.
  It normalises on write **and** on read, so objects unpickled from an
  older save display correctly with no save migration.
- `game_helpers.fix_name_case` now delegates to `proper_name`.
- `game_render._cap(raw)` (L66) title-cases a raw data value for a
  panel — material, slot, damage type, aura, weapon class
  (`'two_handed sword'` → `'Two Handed Sword'`).
- The type-known prefix is `"Unidentified <true name>"`, capital U
  (`hud_context.hud_item_name`, `main._display_name`).

**If you forget this rule:** a new panel that prints `item.material`
or `atk['type']` raw shows `iron` / `fire_resist` next to title-cased
neighbours. Wrap raw data ids in `_cap()`; never print them bare.
`tests/test_naming.py` asserts every item and monster name in the
data files comes out capitalised.

---

## File-location cheat sheet (where each rule is enforced)

| Rule | File | Function / constant |
|---|---|---|
| Zero-tolerance | `src/quiz_engine.py` | `QuizState`, threshold branch |
| Threshold copy | `src/game_render.py` | `_threshold_line(label, n)` L54 |
| Title-case names | `src/naming.py` | `proper_name`, `ProperNameAttr`; `game_render._cap` |
| Chain v2 | `src/combat.py` | `player_attack`; `chain_exponent` |
| Math-only timing | `src/player.py` | `SUBJECT_TIMER`, `get_quiz_timer` |
| Resource loss | `src/food_system.py`, `src/main.py` | `_cook_compound`, `_harvest`, `_lockpick` |
| One-Q flow | `src/food_system.py`, `src/main.py` | cook / harvest / identify all pass `threshold=1` |
| No masteries | `src/player.py::__setstate__` | pops dead attrs |
| Save-bonus cap | `src/player.py` | `save_bonus_for(cat)` — hard cap 5 |
| Karma clamp | `src/main.py` + mixins | `_award_encounter_outcome` |
| SP failsafe | `src/player.py` | starvation damage loop |
| Secret builds | `src/welcome_screen.py` | `SECRET_BUILDS`, `_qa_tools` gate |
| System-sweep rule | this doc | §13 — manual discipline, not enforced |
