# Item / Power / Quirk vs Current Quiz Rules — Full Audit

**Date:** 2026-09-24
**Scope:** every quirk, hero-special, non-weapon item, magic item, and quest artifact vs the current quiz-engine rules.

## Fixes applied (2026-09-24) — 1,643 tests pass

**P0 — safety:**
- 25 Dad-reward scrolls (`Scroll of the Labyrinth` through `Scroll of the Pasture`) — `quiz_threshold` dropped to 1 AND `single_copy: true` added. One wrong grammar Q no longer destroys the real-world reward code.

**P1 — hard breaks:**
- `hints.json:56` — chain-v1 hint rewritten for chain-v2 (wrong freezes the chain, doesn't collapse it).
- **Crown of Brahma** — added the missing `tier_bonuses["5"]` block (AC +7, INT +4, MP +35, regen, resistances, four-faces FOV, free cast once/floor). Chain-5 is now the peak.
- **Ring of Pythia** — `identify_timer_bonus: 2` (dead: philosophy is untimed) replaced with `identify_tier_reduction: 1`, wired via new `Player.get_identify_tier_reduction()` and consumed in `_identify_item`.
- **Hamsa Hand** — `rotating_subject_chain_cap` (dead: 3/3 subjects untimed) replaced with `save_bonus: {"cat": "all", "amount": 2}` — real evil-eye protection.
- **Torque of Lugh** — `rotating_subject_chain_cap` (dead: 5/6 subjects untimed) replaced with `save_bonus: {"cat": "all", "amount": 3}` + `attack_chain_cap_bonus: 1`. `chain_passives.get_attack_chain_cap_bonus` extended to read the flat field.
- **Cassandra quirk** — trigger retargeted from "pass a threshold quiz with ≥ 2 wrong" (unreachable under zero-tolerance) to "answer 50 questions wrong in one run" (persistent through wrong answers = on-theme).

**P2 — hazardous unique books/scrolls:**
- **Book of Thoth**, **Lemegeton**, **Sefer Yetzirah**, **Picatrix** — `quiz_threshold: 3` → 1. Difficulty comes from the T4/T5 grammar tier, not from a streak that could destroy the consumable artifact.
- **Necronomicon** — inert `quiz_threshold: 3` reset to 1. The custom `_necronomicon_quiz` flow no longer applies a 10+WIS timer to grammar (grammar is untimed under the engine contract).
- **Dead Sea Scroll** — `quiz_threshold: 3` → 1 AND `single_copy: true` added.

**P3 — dead-code redesigns:**
- **18 non-math timer-bonus quirks** — `_timer_bonus`/`_all_timer_bonus` now grant a subject-appropriate stat bump in addition to the dead-until-timing-changes seconds. Effect strings rewritten so unlocks describe the real reward (e.g., Ibn Battuta: "PER +1 (geography quiz timer +4s applies if geography ever becomes timed)").
- **~83 ingredients + ~83 prime_cuts** — misleading `temp_desc` "+5 sec on all quizzes" rewritten to "clarified thought; grants Brilliance while active" (matches how `food_system.py` actually consumes the temp_power).
- **10 containers** — dead `quiz_threshold` values (some > tier 5 cap) reset to 1 to match the hardcoded lockpick v3 flow.
- **`_quick_buc_check`** — deleted (never called anywhere; `threshold=3, total_qs=5` was unreachable under zero-tolerance).

**P4 — lore rewrites:**
- Ancile shield lore ("granting extra time on all mental challenges") → "steadies the arm in combat, granting extra time under the pressure of a duel."
- Ring of Wisdom / Ring of Greater Wisdom / Amulet of Greater Wisdom / Sphinx Crown — lore lines promising "quiz timing" rewritten to talk about wisdom, judgment, and pressure without invoking a dead mechanic.

**P5 — cleanup:**
- Removed the retired rotating-subject bookkeeping from `main._change_level` (kept the `_rotating_chain_subject = None` stub for save-compat).
- Removed the dead `_rotating_chain_subject` +3s branch from `Player.get_quiz_extra_seconds`.
- Deleted `tests/test_rotating_subject_message_gate.py` (mechanic retired).
- Updated `tests/test_engine_wave6_remaining.py`, `tests/test_group_cd_residuals.py`, `tests/test_spells.py` to match the new contracts.

**Not fixed (deliberate design calls not made in this pass):**
- The systemic "non-math is untimed" policy is unchanged. Timer bonuses still store into `quiz_timer_bonuses` for future compatibility, but only math actually consumes them.
- Pandora's Box and Aladdin's Lamp (disabled `min_level: 9999` artifacts with pre-zero-tolerance threshold shapes) — left as-is; they need a full mechanic redesign before enabling.
- `Player.SUBJECT_TIMER`'s 11 non-math rows still exist — kept for symmetry / future re-timing decisions. Not called at runtime except from math combat.
- `mastery_class` docstring/dict-key in `main.py:814,838` — kept for save/API stability.
- Every non-math `start_quiz` caller still passes `base_seconds`, `extra_seconds`, `timer_modifier` — engine silently ignores them.

---


## Current quiz rules (baseline for the audit)

From `src/quiz_engine.py`:

1. **Zero-tolerance threshold** (2026-05-29 change): any wrong answer immediately ends a threshold quiz. Only the Tablet of Destinies grants a one-time reroll.
2. **Chain v2**: a wrong answer NO LONGER zeros the chain; the strike/effect lands at whatever chain was achieved (chain 0 = miss on the first question = no effect).
3. **Timer policy**: ONLY the `math` subject is timed by default. Every other subject (geography / history / animal / cooking / science / philosophy / grammar / economics / theology / trivia / ai) is UNTIMED — `timer_seconds=0`, `time_remaining=0`, and any `extra_seconds` passed to `start_quiz` is discarded.
4. **Per-run mastery**: once every distinct question at a `(subject, tier)` is answered correctly in a run, that tier auto-passes future rounds. Auto-passed rounds DO NOT call `on_quiz_answer`.
5. **Escalator caps at tier 5.**
6. **Identify v3** (2026-08-06): one philosophy Q at derived id_tier. Right = full ID; wrong = Stunned 10t flat. No mastery stores.
7. **Cook v2 / Harvest v4 / Lockpick v3**: one question per attempt; the target ingredient/corpse/lock is consumed on attempt (resource loss IS the penalty).

---

## Category status

| Category | Status | Findings |
|---|---|---|
| Quirks (100) | ✅ | 1 broken (Cassandra), 18 dead-code timer rewards |
| Hero specials (~30) | ✅ | 0 broken — chain-v2 compatible |
| Armor + shield (96) | ✅ | 1 hard break (Crown of Brahma), 1 dead field (Ancile) |
| Accessory + artifact (~170) | ✅ | 3 hard breaks (Pythia, Hamsa Hand, Torque), 2 disabled items, 4 stale lore |
| Magic — wand / spellbook / spells (272) | ✅ | 5 hazardous T4-T5 books, several dead-code paths |
| Scroll / potion / food / lockpick / container (~560) | ✅ | **P0 real-world bug (25 Dad-reward scrolls)**, 82+ ingredient UI-rot |
| chain_passives (18 passives) | ✅ | 0 breaks — all chain-v2 compliant |
| Codebase grep for stale terms | ✅ | 1 live in-game hint teaches wrong rule (`hints.json:56`) |

---

## Quirks (audited by Claude directly)

### BROKEN

**Cassandra** (`quirk_system.py:458-462`) — trigger: "pass a threshold quiz with ≥ 2 wrong answers." Under zero-tolerance, any wrong answer immediately ends a threshold quiz; only the Tablet of Destinies can survive **one** wrong. Trigger `wrong_count >= 2` is now unreachable in a successful threshold quiz. **Cassandra is unlockable-in-theory-only.**

### DEAD-CODE REWARDS (unlockable but the promised bonus has no runtime effect)

Every quirk that grants "subject-X quiz timer +N seconds" for a **non-math** subject has zero runtime effect because non-math subjects are untimed by default. The player still unlocks the quirk, still sees the reward text, but the timer bonus is silently discarded by `quiz_engine.start_quiz` when `timed=False`. The list:

| Quirk | Reward text | Subject | Status |
|---|---|---|---|
| Scheherazade | Grammar timer +5 | grammar | DEAD |
| Merlin | Science timer +4 | science | DEAD |
| Sisyphus | Economics timer +5 | economics | DEAD |
| Asclepius | Animal timer +4 | animal | DEAD |
| Dionysus | Philosophy timer +3 | philosophy | DEAD |
| Athena | History timer +4 | history | DEAD |
| Circe | Cooking timer +4 | cooking | DEAD |
| Confucius | Philosophy timer +4 | philosophy | DEAD |
| Ibn Battuta | Geography timer +4 | geography | DEAD |
| Galileo | Science timer +3 | science | DEAD |
| Kali | Theology timer +3 | theology | DEAD |
| Tesla | Science timer +5 | science | DEAD |
| De Medici | Economics timer +4 | economics | DEAD |
| Shakespeare | Grammar timer +5 | grammar | DEAD |
| Shiva | Philosophy timer +5 | philosophy | DEAD |
| Penelope | Geography timer +3 | geography | DEAD |
| Machiavelli | All-subjects +1 | all | PARTIAL — only math bit works |
| Zoroaster | All-subjects +1 | all | PARTIAL — only math bit works |
| Sibyl | All-subjects +2 | all | PARTIAL — only math bit works |

Ramanujan (math +5) and Apollo (math +3) work as advertised.

### WORKS, but with a caveat

- **Auto-pass bypass** — `_auto_pass_mastered_round` at `quiz_engine.py:515-562` does NOT call `on_answer` / `on_quiz_answer`. So per-run correct-answer quirks (Ramanujan, Solomon, Galileo, Confucius, Machiavelli, Ouroboros, Time Dilation, Mind Fortress, Focused Scholar, Sage's Counsel, etc.) stop counting once a `(subject, tier)` is mastered for the run. Not "broken" — it's the design — but worth documenting.
- Every non-timer-bonus quirk trigger checked (Musashi chain-1, Apollo max-chain, Beowulf unarmed, Thor same-weapon, etc.) survives chain-v2 and zero-tolerance.

---

## Hero specials (audited by Claude directly)

All active specials in `hero_specials.py` route through `_activate_hero_special` in `game_menus.py:1466`, which calls `start_quiz(mode='escalator_chain', subject='ai', max_chain=5)`. The `resolve_active_special` dispatcher clamps chain to 0..5 and looks up `tier_effects[chain]`, with `chain 0` intentionally being the "fizzle" tier for every special (identify 0 items, confuse 0 targets, 0d0 damage dice, duration 0, etc.). Chain-v2 is fully compatible.

Passive builds (Plato, Nietzsche, Diogenes, Achilles, Geralt, Ciri, Boudicca, Musashi, Tesla) don't touch the quiz engine.

**No issues.**

---

## Timer-bonus dead-code — root cause (for future rebuilds)

The plumbing works this way:
- `player.get_quiz_extra_seconds(subject)` accumulates: `quiz_timer_bonuses[subject]` (quirks + mystery events) + Ancile shield's `quiz_timer_bonus` + Ring of Pythia's `identify_timer_bonus` (philosophy) + Torque of Lugh's rotating +3.
- The result is passed as `extra_seconds` to `quiz_engine.start_quiz`.
- `start_quiz` at line 194-204: `if not timed: self.timer_seconds = 0` — the extra_seconds is only consumed inside the `else` (timed=True) branch.
- `timed` defaults to `subject == 'math'`.
- Nowhere in the codebase does anyone pass `timed=True` explicitly for a non-math subject.

So every non-math timer bonus is silently dropped. Affected items include:
- Ancile shield's `quiz_timer_bonus` (applies to all subjects; only helps in math)
- Ring of Pythia's `identify_timer_bonus` for philosophy — **dead**, philosophy is untimed
- Torque of Lugh / Hamsa Hand's rotating +3 — only helps when the rotating subject happens to be math

---

## PENDING sections

Filled in by parallel agent reports:

### Armor + shield + armor_procs (96 items audited)

**BROKEN:**

- **Crown of Brahma** (`armor.json`) — `equip_chain_mode="chain"` with `max_chain=5`, but `tier_bonuses` only defines tiers 1-4. When a player hits chain 5, `apply_tier_bonuses(player, item, 5)` → `get_tier_bonuses` returns `{}` → **zero chain bonuses applied.** A player who nails all five questions is strictly worse off than one who fails on question 5 (loses INT +3, MP +25, regenerating, +2 magic / +1 fire / +1 lightning resist, four-faces 360° FOV). Fix: add a `"5": { ... }` block, or drop `max_chain` to 4.

**COSMETIC / UI-rot:**

- **Ancile shield** (`shield.json`) — `quiz_timer_bonus: 2` and lore claims "granting extra time on all mental challenges." Mechanically only helps math (the sole timed subject). Lore is stale under the untimed-except-math policy.

**Also confirmed OK:**

- All 12 chain-equip armor pieces with complete tier 1-5 tables (Dragon-Sewn Mail of Sigurd, Helm of Hades, Morrigan's Cloak, Robe of the Magus, Green Knight's Plate, Aegishjalmr, Winged Sandals of Hermes, Cloak of Odin, Helm of Aragorn, Robes of Solomon, Armor of Ragnarok).
- All chain-equip shields (Greater Aegis of Athena, Aegis of Athena, Smoking Mirror of Tezcatlipoca).
- Cow King's Horns `chain_bonus: 1` — consumed by `combat.py:882-885` for math combat; works under chain-v2.
- No armor/shield references removed masteries or old identify system.
- `armor_procs.py` is a pure lookup registry — no quiz calls.

**Non-issue caveats:**

- `equip_threshold` on chain-equip items is dead-data (chain-equip skips the threshold path). Not a bug, but the field is misleading in JSON.
- Chain-equip default subject is `geography` (untimed) — `extra_seconds` in the equip quiz is discarded, but chain-equip doesn't rely on it.

### Accessory + artifact (~170 items audited)

**BROKEN (hard functional breaks):**

- **Ring of Pythia** (`accessory.json`) — `identify_timer_bonus: 2`. `Player.get_quiz_extra_seconds` adds +2s for `subject == 'philosophy'`, but `quiz_engine.start_quiz` sets `timed=(subject=='math')` so the identify quiz has `timer_seconds=0` and `extra_seconds` is discarded. **The ring's signature power never fires.**
- **Hamsa Hand** (`accessory.json`) — `rotating_subject_chain_cap: [theology, history, grammar]`. All three subjects in the pool are untimed. Rotating +3s never applies. **A T4 unique amulet whose signature power fires 0% of the time. Worst break in the audit.**
- **Torque of Lugh** (`accessory.json`, T5) — `rotating_subject_chain_cap: [math, history, science, grammar, economics, theology]`. Fires on math floors only (1/6). Also the field NAME says `"chain_cap"` (implying attack-chain length) but the implementation only grants +3 timer seconds — the flavor is misaligned with the mechanic.

**DISABLED items with quiz-rule mismatches (redesign needed before ever enabling):**

- **Pandora's Box** (`artifact.json`) — `use_quiz_mode='threshold'`, `threshold=3/total=4` relies on the old miss-tolerant threshold. Under zero-tolerance any wrong answer aborts. Also `_disabled_reason` set + `min_level: 9999` + chaos_table dispatcher never implemented.
- **Aladdin's Lamp** (`artifact.json`) — `use_quiz_mode='escalator_threshold'`, `threshold=4/total=5`. Same zero-tolerance mismatch. Same disabled state.

**COSMETIC / stale lore:**

- **Sphinx Crown** — lore says "extends the time available for all mental challenges" (no matching field; only math is timed anyway).
- **Ring of Wisdom / Ring of Greater Wisdom / Amulet of Greater Wisdom** — lore promises "improving quiz timing" but there's no timer field and non-math quizzes are untimed.

**Verified OK:**

- Tablet of Destinies reroll — wired correctly (`game_combat.py:1555 & 1765` set `_reroll_flag`; `quiz_engine.py:221` reads it; per-floor reset in `main.py:1247`).
- All chain-equip accessories (Necklace of Harmonia, Heart of Ahriman, Tyet of Isis, Kavacha-Kundala, Solomon's Authority, Idunn's Apple, Ring of Gawain, Ring of Scheherazade, Anklet of Atalanta) — route through `chain_equip.is_chain_equip → _start_chain_equip_quiz` correctly. Modes 'escalator_chain' and 'chain'.
- Ring of Gawain's `attack_chain_cap_bonus`, Ring of Scheherazade's `grammar_chain_cap_bonus` / `spellbook_chain_bonus` / `scroll_save_on_fail` / `one_thousand_and_one` — all have live consumers.
- T4/T5 named passives verified: surya's_gift, reassembly, life_save_resets_per_floor, atalantas_choice, three_apples, three_oclock, beautiful_ruin, anti_being, aesir_young, first_hit_absorb, solomonic_key, weaken_summoned.
- **Vidar's Sandal** `vidar_instant_kill_fenrir` — triggers on math attack chain ≥ 1. Compatible with chain-v2 (chain 0 = miss = no proc; chain ≥ 1 lands as intended).
- Escalator caps at T5 — every accessory `tier_bonuses` table stops at "5".
- Chain-equip flow correctly handles chain=0 by skipping equip entirely ("does not recognize you") — chain-v2's "wrong doesn't zero" doesn't accidentally equip with no bonuses.

### Magic — wand / spellbook / spells / game_magic (272 items audited)

**HAZARDOUS under zero-tolerance (5 unique/consumable T4-T5 books that pre-date 2026-05-29):**

- **Book of Thoth** (`spellbook.json`) — `quiz_threshold: 3` at grammar T5 AND `consumable_artifact: true`. One wrong answer on any of 3 T5 grammar Qs routes to the curse: 3d6 psychic + de-ID 3 items + 20-turn Stunned. Book is always consumed (Ring of Scheherazade can't save consumable_artifacts). **Worst realistic hazard.**
- **Lemegeton** (`spellbook.json`) — `quiz_threshold: 3` at grammar T5, unique. One wrong = book destroyed (unless Ring of Scheherazade equipped).
- **Sefer Yetzirah / Picatrix** (`spellbook.json`) — `quiz_threshold: 3` at grammar T4, unique. Same hazard tier.
- **Necronomicon** (`spellbook.json`, custom `_necronomicon_quiz`) — bypasses zero-tolerance by design (asks all 3 Qs regardless). Also applies a `10 + WIS` timer to a grammar quiz which is otherwise UNTIMED. Both may be intentional theming, but they diverge from the current engine contract.

These items were authored before the 2026-05-29 zero-tolerance change and haven't been recalibrated. **Decision needed:** intentional artifact-difficulty spikes, or lower thresholds to 1?

**DEAD CODE:**

- `game_magic._quick_buc_check` — `threshold=3, total_qs=5, subject='philosophy'`. Zero-tolerance ends the quiz before Q4/5 can ever be asked, so `total_qs=5` is dead. Function is also never referenced anywhere in `src/`.
- `player.get_int_quiz_bonus()` — advertised as "+seconds for science/grammar/philosophy quizzes." All three are UNTIMED, so every magic call site (wand zap, spell cast, spellbook learn, Book of Thoth, identify, quick_buc_check) passes a bonus that `quiz_engine` never consumes. Only meaningful remaining caller is math combat.
- Every magic start_quiz caller (`_invoke_wand`, `_start_spell_quiz`, `_learn_from_spellbook`, `_read_book_of_thoth`, `_identify_item`, `_quick_buc_check`) passes `timer_modifier`, `extra_seconds`, and `base_seconds` for a subject that is untimed. Dead args, harmless but noisy.

**COSMETIC / spec-drift:**

- `game_magic._read_book_of_thoth` header comment (lines 65-70) frames per-tier scaling as "chain-5-ish weapon hit" — chain retired for spells/wands in v2.11.0 / v2.12.0. Comment-only rot.
- `game_magic._apply_spell_effect` sets local `chain = 5` / `chain_scale = 1.0` as back-compat shims; string comment "just say (chain 5)" suggests some user-visible message may still surface "(chain 5)" — worth grepping.

**Verified OK:**

- All **91 wands** — `quiz_threshold: 1` (single science Q). Zero-tolerance safe.
- All **80 regular spellbooks** — `quiz_threshold: 1`. Safe.
- All **88 spells** in `spells.py` — cast contract is threshold=1 science at `spell.tier` via `_start_spell_quiz`.
- `_start_recall_lore` — `escalator_chain` trivia tier=1, `max_chain=5`. Handles chain-v2 correctly (chain 0 = "Nothing surfaces").
- `_identify_item` — threshold=1 philosophy at derived id_tier. Right = identify, wrong = Stunned 10t. Identify v3 compliant.
- `get_spellbook_chain_bonus` — reduces effective tier (not threshold). Compatible.
- Ring of Scheherazade `scroll_save_on_fail` — saves the BOOK object after quiz fail; not a mid-quiz reroll, no conflict with Tablet.
- No spell/wand grants a mid-quiz second chance.

### Scroll / potion / food / ingredient / lockpick / container (~560 items audited)

**CRITICAL — real-world reward loss:**

- **25 Dad-reward scrolls** (`Scroll of the Labyrinth`, `Scroll of the Gorgon`, `Scroll of the Dragon-Hoard`, `Scroll of Ragnarok`, `Scroll of the Abyss`, `Scroll of Arachne`, `Scroll of Lamia`, `Scroll of Talos`, `Scroll of Echidna`, `Scroll of the Erlking`, `Scroll of Camazotz`, `Scroll of Cacus`, `Scroll of the Sphinx`, `Scroll of Rangda`, `Scroll of the Lion`, `Scroll of Baba Yaga`, `Scroll of Jormungandr`, `Scroll of Set`, `Scroll of the Green`, `Scroll of Charybdis`, `Scroll of Ravana`, `Scroll of the Wendigo`, `Scroll of the Hunt`, `Scroll of Anansi`, `Scroll of Nidhoggr`, `Scroll of the Pasture`) — every one has `quiz_threshold: 2` and NO `single_copy` flag. Under zero-tolerance, one wrong grammar answer ends the quiz and `game_magic.py:2259` permanently removes the scroll — **destroying the real-world reward code the kids are supposed to redeem** (LABYRINTH-MMXXV-I, GORGON-MMXXV-II, DRAGONHOARD-MMXXV-III, RAGNAROK-MMXXV-IV, MOO-MOO-FARM-I, etc.). Only `scroll_lake_of_fire` and `scroll_deaths_bane` are on the `single_copy` whitelist. **Fix: drop threshold to 1 OR add `single_copy: true` to all 25.**

**HAZARDOUS:**

- **Dead Sea Scroll** — `quiz_threshold: 3`, no `single_copy`. Zero-tolerance means one wrong of 3 T5 grammar Qs destroys the artifact-tier scroll. Less awful than the Dad rewards but same axis.

**COSMETIC / dead-code:**

- **Container `quiz_threshold` fields** (10 containers with values 2-6) — legacy dead data. `items.py:979` comments "quiz_threshold is unused by the new flow" and `container_system.py:108` hardcodes `threshold=1`. Field should either be stripped from JSON or reset to 1 to avoid future misreads. **6 is above the tier-5 cap and impossible anyway.**
- **~82 ingredients with `temp_power: "quiz_timer_bonus"`** (Goblin Prime and many others) — temp_desc still claims "+5 sec on all quizzes" but only math is timed and `food_system.py:209` remaps `quiz_timer_bonus` to the `brilliance` status (+1 INT / +1 WIS, ~1 sec of math timer). Massive UI-rot from the timer rules change.

**Verified OK:**

- All ~53 regular scrolls with `quiz_threshold: 1` — safe.
- `scroll_lake_of_fire` and `scroll_deaths_bane` — protected via `single_copy: true`.
- All 35 potions — no quiz gate on drink.
- All 18 foods — `eat` path has no quiz.
- Cook path — `threshold=1` cooking Q; ingredient consumed on attempt (v4). Compliant.
- Harvest path — `threshold=1` animal Q; corpse consumed on attempt (v4). Compliant.
- All 5 lockpicks — v3 flow: one economics Q at `container.quiz_tier`, hardcoded `threshold=1`. Compliant.
- Container `quiz_tier` (1-5, falls back to `tier`) — drives difficulty correctly.
- Container traps fire on quiz FAILURE, not on threshold cascade — unaffected by rule change.
- `recipes.json` — no chain/escalator/quiz_mode/quality fields; cook v3 is outcome-driven.
- Tablet of Destinies reroll — wired for all threshold quizzes including scroll reads.

### chain_passives (audited by Claude directly)

`src/chain_passives.py` is a pure lookup module — it reads `_chain_passives` that `chain_equip.apply_tier_bonuses` writes at equip time. It does NOT call `quiz_engine.start_quiz` directly. As long as `chain_equip` handles chain-v2 correctly (verified: `apply_tier_bonuses` returns empty dict for `tier <= 0`, so chain 0 = miss-on-first = no bonus applied), chain_passives is fine.

Three quiz-adjacent passives worth flagging (but they work):
- `attack_chain_cap_bonus` (max chain length +1) — extends chain quizzes cleanly under chain-v2.
- `grammar_chain_cap_bonus` (Ring of Scheherazade) — reduces scroll-read TIER. Still valid.
- `spellbook_chain_bonus` (v2.12.0) — reduces spellbook cast tier. Still valid.

**No chain_passives issues.**

### Codebase-wide stale-term grep (~140+ hits scanned)

**LIVE player-facing rot:**

- **`data/hints.json:56`** — In-game hint reads *"A chain unbroken builds; a chain broken collapses."* This describes chain-v1 (a broken chain "collapses"). Under chain-v2 the strike still lands at the achieved chain — the hint teaches the WRONG rule to the player. **Fix this hint.**

**Redundant / suspect string:**

- `src/main.py:2949` — chronicle string *"no second chances"* appears near Tablet of Destinies context; the Tablet DOES grant a second chance. Worth reviewing.

**Historical mastery references (documentation of removal — mostly OK to leave, but noisy):**

- ~13 code comments in `game_magic.py`, `items.py`, `main.py`, `player.py`, `game_render.py`, `quirk_system.py` narrating the 2026-08-06 mastery removal. All accurate. The English word "Mastery" in quirk names (Sisyphus' Mastery, Penelope's Mastery) is fine — flavor only.
- `src/main.py:814, 838` — docstring/dict-key still literally named `mastery_class`. Rename to `type_id` (or similar) for future-reader clarity.
- Two test-only fake-Player stubs (`test_potion_power_rolls.py:39`, `test_bugbatch_2_0_3.py:369`) reference removed attributes — dead but harmless (regression guards for old-save loads).

**Zero real chain-v1 assumptions in `chain_passives.py` or elsewhere in `src/` — all live code is chain-v2 compliant.**

**Zero `id_mastery` / `identify_mastery` / `mastery_bonus` references** — clean.

**Systemic dead-code (timer bonuses for non-math)** — already summarized in the "Timer-bonus dead-code" section above. Full list:

- 19 `_timer_bonus`/`_all_timer_bonus` quirk awards in `quirk_system.py` targeting non-math subjects.
- Mystery reward `all_timer_bonus: 1` (`mystery_system.py:84, 473-479`).
- Ancile shield `quiz_timer_bonus: 2` (`shield.json`).
- Ring of Pythia `identify_timer_bonus: 2` (`accessory.json`).
- Torque of Lugh / Hamsa Hand rotating +3s (only math slot fires).
- ~30 `prime_cuts.json` entries with `temp_power: "quiz_timer_bonus"`.
- ~60 `ingredient.json` entries with `temp_power: "quiz_timer_bonus"`.
- Every non-math `get_quiz_timer()` / `base_seconds=` call site (magic + prayer + food + lockpick + AI encounters + identify + scroll — 20+ locations) computes a timer that `quiz_engine.start_quiz` immediately zeroes.
- `Player.SUBJECT_TIMER` in `player.py:12-30` defines base+wis-scale for 11 non-math subjects that are never consumed.
- `game_render.py:1032-1034` displays an econ timer that will never be enforced.

**Chain_passives.py** — 0 chain-v1 assumptions. All 18 passives are chain-agnostic or chain-v2 compatible.

---

## Priority-ordered breakage summary

### P0 — real-world impact (fix first)

1. **25 Dad-reward scrolls destroyed on one wrong grammar answer.** `scroll_of_the_labyrinth` through `scroll_of_the_pasture` — every one carries `quiz_threshold: 2` and lacks `single_copy: true`. Under zero-tolerance, one wrong Q ends the quiz and `game_magic.py:2259` permanently removes the scroll — **wiping the LABYRINTH-MMXXV-I / GORGON-MMXXV-II / DRAGONHOARD-MMXXV-III / RAGNAROK-MMXXV-IV / MOO-MOO-FARM-I reward codes the kids are supposed to redeem.** Fix: set `quiz_threshold: 1` OR add `single_copy: true` to all 25.

### P1 — hard functional breaks (signature powers dead)

2. **Ring of Pythia** — `identify_timer_bonus: 2` never fires (philosophy is untimed). Signature power dead.
3. **Hamsa Hand** — `rotating_subject_chain_cap: [theology, history, grammar]`, all three untimed. T4 unique's signature power fires 0% of the time.
4. **Torque of Lugh** — rotating +3s fires only on math floors (1 in 6). Also field name says "chain_cap" but implementation only adds seconds.
5. **Crown of Brahma** — `equip_chain_mode="chain"` with `max_chain=5` but `tier_bonuses` only defines tiers 1-4. Chain 5 = zero bonuses. Fix: add `"5"` block or drop `max_chain` to 4.
6. **Cassandra quirk** — trigger "pass threshold quiz with ≥ 2 wrong answers" is unreachable under zero-tolerance + one-time Tablet reroll. Redesign trigger.
7. **`data/hints.json:56`** — chain-v1 hint text ("chain broken collapses") teaches the WRONG rule under chain-v2. Rewrite hint.

### P2 — hazardous but arguably intentional (design call)

8. **Book of Thoth** — `quiz_threshold: 3` grammar T5, `consumable_artifact` (Scheherazade can't save). One wrong on 3 T5 Qs routes to the curse (3d6 psychic + de-ID 3 items + Stunned 20t). Authored pre-2026-05-29; needs recalibration decision.
9. **Lemegeton / Sefer Yetzirah / Picatrix** — `quiz_threshold: 3` grammar T4-T5. Ring of Scheherazade saves the book but the quiz still costs the attempt. Same hazard axis.
10. **Necronomicon** — bypasses zero-tolerance by design AND applies a 10+WIS timer to an untimed grammar quiz. Diverges from the engine contract; may be intentional.
11. **Dead Sea Scroll** — `quiz_threshold: 3`, no `single_copy`. Destroyed on first wrong.
12. **Pandora's Box / Aladdin's Lamp** — DISABLED artifacts (`_disabled_reason` + `min_level: 9999`) with threshold quizzes that assume miss-tolerance. Need redesign before enabling.

### P3 — dead-code / stale-flavor rewards (unlock, but reward has no runtime effect)

13. **18 quirks with non-math timer bonuses** (Scheherazade, Merlin, Sisyphus, Asclepius, Dionysus, Athena, Circe, Confucius, Ibn Battuta, Galileo, Kali, Tesla, De Medici, Shakespeare, Shiva, Penelope, Machiavelli, Zoroaster, Sibyl). Player still unlocks the quirk; the promised seconds are silently discarded.
14. **Ancile shield** `quiz_timer_bonus: 2` — active only for math combat; lore promises "extra time on all mental challenges."
15. **~82 ingredients + ~30 prime_cuts with `temp_power: "quiz_timer_bonus"`** — desc claims "+5 sec on all quizzes" but `food_system.py:209` remaps to `brilliance` (+1 INT / +1 WIS, ~1s of math timer). Mass UI-rot.
16. **Mystery event `all_timer_bonus: 1`** (`mystery_system.py:84`) — reaches every subject; only math slot works.
17. **Container `quiz_threshold` fields** (10 containers, values 2-6, one is above the T5 cap) — dead JSON per `items.py:979` comment. Strip or reset to 1.

### P4 — cosmetic / lore

18. Sphinx Crown / Ring of Wisdom / Ring of Greater Wisdom / Amulet of Greater Wisdom — lore promises "improving quiz timing" with no matching field.
19. `main.py:2949` chronicle string *"no second chances"* near Tablet — Tablet DOES grant a second chance.
20. `main.py:814, 838` docstring/dict-key `mastery_class` — rename post identify-v3 removal.
21. `game_magic.py:65-70` header comment references retired chain-v2-for-spells framing.
22. Various historical `masteries were removed` narration comments — accurate but noisy.

### P5 — dead-argument / call-site cleanup

23. Every non-math `start_quiz` caller (~20 call sites) computes `base_seconds`, `extra_seconds`, `timer_modifier` for a subject that `quiz_engine` immediately forces to `timed=False`. Wasted work; also `Player.SUBJECT_TIMER` has 11 non-math rows that are never consumed.
24. `game_magic._quick_buc_check` — `threshold=3, total_qs=5` (total_qs unreachable under zero-tolerance), AND function is never referenced.
25. `game_render.py:1032-1034` displays an economics timer that will never be enforced.

---

## Cross-cutting policy questions the audit surfaces

1. **Timer policy** — dozens of items and quirks assume non-math subjects can be timed. Either (a) allow non-math timed quizzes when the player carries a timer bonus (make the ~18 quirks meaningful again + Ancile + Pythia + Hamsa Hand + Torque + food procs + mystery rewards), OR (b) redesign all of those to grant a non-timer bonus, OR (c) accept the current dead state and prune the plumbing (`Player.SUBJECT_TIMER` non-math rows, `quiz_timer_bonuses` dict, `all_timer_bonus`, `identify_timer_bonus`, `rotating_subject_chain_cap` timer half).
2. **Threshold zero-tolerance retrofit** — 5 unique T4-T5 spellbooks + Dead Sea Scroll + the 25 Dad-reward scrolls all use `quiz_threshold: 2` or `3` from before 2026-05-29. Sweep every JSON `quiz_threshold > 1` and decide: keep the difficulty spike, drop to 1, or add a save.
3. **Cassandra quirk** — either redesign the trigger to be reachable under zero-tolerance (e.g., "get 10 questions wrong across all threshold quizzes"), or retire it.
4. **Identify-v3 leftovers** — Ring of Pythia's field, `mastery_class` naming, and any lore text that promises "identify masteries" should be swept.

---

## Audit totals

- Categories audited: **quirks (100), hero specials (~30), armor + shield (96), accessory + artifact (~170), magic (272), non-combat items (~560), chain_passives (18 passives), codebase-wide grep sweep**.
- Files read: 30+.
- Distinct findings: **~50 concrete issues** across P0-P5 tiers.
- Real-world-impact bugs: **1** (P0: destroyable reward scrolls).
- Hard mechanical breaks: **5** (P1: Pythia, Hamsa Hand, Torque, Crown of Brahma, Cassandra).
- UI-facing stale rule: **1** (chain-v1 hint text).
