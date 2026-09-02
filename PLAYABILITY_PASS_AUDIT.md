# Playability Pass Audit — v2.6.1 / v2.6.2 / v2.6.3

**Executed autonomously overnight 2026-09-01 per Brandon's "keep going until you're done" instruction. Read in the morning.**

Full path: `C:\Users\brand\Documents\PhilosophersQuest\PLAYABILITY_PASS_AUDIT.md`

---

## Ship state

| version | tag | commit | GitHub release |
|---|---|---|---|
| v2.6.1 | `v2.6.1` | `66a705b` | https://github.com/RaynfallLabs/PhilosophersQuest/releases/tag/v2.6.1 |
| v2.6.2 | `v2.6.2` | `f3f1312` | https://github.com/RaynfallLabs/PhilosophersQuest/releases/tag/v2.6.2 |
| v2.6.3 | `v2.6.3` | `1f4d8de` | https://github.com/RaynfallLabs/PhilosophersQuest/releases/tag/v2.6.3 |
| audit docstring cleanup | (no tag) | `0cd85d8` | — |

`origin/main` HEAD: `0cd85d8`. Local matches remote. Working tree clean.

**Still your call (matches every prior x.y.0 ship):** `ISCC installer\setup.iss` + `gh release upload v2.6.3 installer\PhilosophersQuest_Setup.exe --clobber` (and optionally the same for v2.6.1 / v2.6.2 if you want their pages to carry the exe).

---

## What each version did

### v2.6.1 — Harvest v3
- `src/food_system.py:harvest_corpse` swapped from `mode='escalator_chain', max_chain=5` to `mode='threshold', threshold=1, total_qs=1, tier=<derived from corpse.harvest_tier>`
- Right → full tier-appropriate haul via existing `_harvest_outcome_for_tier(tier, monster_id)`. Wrong → corpse ruined, no ingredients, no stun
- Reward gradient preserved via `harvest_tier` field on each monster's JSON (100 T1 / 106 T2 / 154 T3 / 101 T4 / 64 T5)
- Cut: 5 Q → 1 Q per corpse

### v2.6.2 — Cook v3
- `src/food_system.py:cook_compound_recipe` and `cook_ingredient` swapped from `escalator_chain` to `threshold` 1-Q at recipe-class-derived tier
- `_RECIPE_CLASS_TIER`: family=2, prime=3, master_prime=4, trophy=5, dungeon_keyed=5
- Right → full peak (T5) outcome for the recipe. Wrong → ruined, ingredients consumed either way
- Cut: 5 Q → 1 Q per cook

### v2.6.3 — Identify v3.1 (split form × material knowledge)
- Two new sets on Player: `known_forms` and `known_materials` (see `src/player.py:198-205`)
- `src/items.py` adds `form_id(item)`, `material_id(item)`, `is_split_type_known(player, item)`
- Successful identify (`_propagate_identification`) fills BOTH sets. Philosopher's Stone (`_auto_identify_all`) too
- `Player.knows_item_type` now routes through split knowledge in addition to `known_item_ids` / `known_class_ids`
- `_display_name` in `main.py` now uses `player.knows_item_type` — auto-known items show their true name in inventory / ground / menus
- BUC and enchant stay per-instance — the identify quiz still exists, just usually not needed to know what an item IS
- Combinatorics: 22 weapon forms + 52 weapon materials = 74 unlocks cover all 1,144 possible weapon combos
- Migration: `Player.__setstate__` backfills empty sets on load from pre-2.6.3 saves

### v2.6.3+audit — Docstring cleanup
- `src/food_system.py` module header + `_harvest_outcome_for_tier` + `make_corpse` docstrings updated to reflect current v3 cadence (was still describing the old escalator_chain flow). No behavior change.

---

## Files touched (comprehensive)

**v2.6.1:**
- `src/food_system.py` — `harvest_corpse` rewritten
- `src/layout.py` — VERSION 2.6.0 → 2.6.1
- `installer/setup.iss` — AppVersion 2.6.0 → 2.6.1
- `tests/test_harvest_cook_integration.py` — MockQuizEngine `scripted_success` param; MockCorpse `harvest_tier` param; escalator-mode tests replaced with threshold-mode tests; +2 new tests (tier-derivation, clamp behavior)

**v2.6.2:**
- `src/food_system.py` — `_RECIPE_CLASS_TIER`, `_recipe_quiz_tier`, `cook_compound_recipe`, `cook_ingredient`
- `src/layout.py` — 2.6.1 → 2.6.2
- `installer/setup.iss` — 2.6.1 → 2.6.2
- `tests/test_harvest_cook_integration.py` — +4 new cook-v3 tests

**v2.6.3:**
- `src/items.py` — `form_id`, `material_id`, `is_split_type_known` helpers
- `src/player.py` — `known_forms`, `known_materials` sets; `knows_item_type` extended; `__setstate__` added for migration
- `src/game_magic.py` — `_propagate_identification` and `_auto_identify_all` fill split sets
- `src/main.py` — `_display_name` uses `player.knows_item_type` (auto-splits)
- `src/layout.py` — 2.6.2 → 2.6.3
- `installer/setup.iss` — 2.6.2 → 2.6.3
- `tests/test_identify_split_knowledge.py` — NEW; 11 tests

**Audit cleanup:**
- `src/food_system.py` — docstrings only
- `_archive/sweep_2026_09_01/science_tellgate.json` — swept from `data/questions/` (tellgate scan re-run left a build artifact in the bundle path; the packaging test caught it)

---

## Test suite

- Before playability pass: 1597 pass / 0 fail
- After v2.6.1: 1598 pass
- After v2.6.2: 1602 pass
- After v2.6.3 + audit: **1613 pass / 0 fail** (28 legacy tests skip, unchanged)
- +16 new tests total (2 harvest v3 + 4 cook v3 + 11 identify v3.1, minus renames)
- `tests/test_packaging.py` passing (verified after the tellgate sweep)

---

## Deferred design debt (from prior conversation, still deferred)

**Science bank lane-drift sweep** — 15 of 18 stance-heavy howscience/medicine/legal ladders drifted into pure political/legal/Holocaust-operational history (Aktion T4, WEF/Great Reset, 1986 NCVIA, Tuskegee, Unit 731, etc). Full rubric + verdicts preserved at `bankbuild/science/_cli_state/audit_lanestrict_all.json` and memory `project_science_bank_rebuild`. Would delete 9 + trim 6, ~98 rungs (~2.6% of bank). You said "leave it as is for now" — sweep on your next word.

---

## Playtesting checklist (per CLAUDE.md play-test rule)

All three changes are trivially reachable in a few minutes of play. Autonomous mode skipped the play-test gate per your instruction; sanity below.

**Harvest (v2.6.1):**
- [ ] Kill any monster, try to harvest — should see ONE animal question, no chain
- [ ] Right answer → full haul (assorted / family / prime as expected for that monster tier)
- [ ] Wrong answer → corpse ruined, no ingredients, no stun

**Cook (v2.6.2):**
- [ ] Cook any recipe (family, prime, trophy) — should see ONE cooking question
- [ ] Right answer → full peak effect (SP, HP, temp powers, etc.)
- [ ] Wrong answer → ingredients gone, dish ruined, no stun
- [ ] Q difficulty scales with recipe complexity (trophy = T5, family = T2)

**Identify (v2.6.3):**
- [ ] First iron long sword: unidentified until you quiz-ID it
- [ ] After ID: inventory shows "Iron Long Sword" (already worked pre-v2.6.3)
- [ ] Pick up a second iron long sword: also shows true name (already worked)
- [ ] **NEW** — pick up a steel long sword: STILL unidentified, but if you already IDed a steel item, now it shows the true name (form=longsword known + material=steel known)
- [ ] **NEW** — pick up an iron short sword: still unidentified until you ID it, THEN every future iron short sword auto-shows
- [ ] Once you have 4-5 forms and 4-5 materials known, most floor loot should render with true names on pickup — the whole design win
- [ ] BUC / enchant still hidden until per-instance identify (unchanged)

---

## Health checks that passed post-audit

- `python -m pytest tests/ --tb=short` — 1613 passed / 0 failed / 28 skipped
- `python -m PyInstaller PhilosophersQuest.spec --noconfirm` — builds cleanly (5.15 MB exe + `dist/PhilosophersQuest/_internal/data/questions/science.json` = 3,682 questions verified)
- `python bankbuild/dedup_overlap_scan.py --subject=science` — 0 candidate pairs (unchanged from ship)
- `python bankbuild/tellgate.py bank data/questions/science.json` — 13 flags (unchanged)
- `git status` — working tree clean
- Version consistency — `src/layout.py:VERSION == installer/setup.iss:AppVersion == "2.6.3"`
- Bundle path — no stray bank-build artifacts in `data/questions/` (verified by `test_bundled_dirs_contain_only_runtime_files`)

---

## Notes / caveats

- **Uniques unchanged.** Sword of Michael, Hrunting, etc. still route through per-item `known_item_ids`. Split-knowledge deliberately doesn't apply — a unique's whole identity IS its instance.
- **The identify quiz still exists.** The chore-reduction win in v2.6.3 is that you rarely need to run it — you can equip by name. BUC/enchant surprises only matter if you're about to commit. Some players will still choose to identify defensively; that's fine.
- **Failure penalty on cook feels heavy** to some tastes (ingredients gone). If play-test shows it's punishing to the point of not-cooking, the option is a "T1 outcome floor" on failure (get basic-tier reward instead of nothing) — but per the "resource loss IS the cost" design principle you set, ship as-is and revisit if play confirms the friction.
- **Old escalator_chain references elsewhere.** Combat (math), prayer (theology), scrolls (grammar), wands (science), mystery events, boss hero-specials, chest lockpicking, altar cooking-challenges all still use escalator_chain modes. They're LOW-frequency actions where the chain is the point (or in combat's case, the chain IS the game). Not in scope for this pass.

---

## What's on disk

- Local + remote HEAD: `0cd85d8` on `main`
- Three release pages live at github.com/RaynfallLabs/PhilosophersQuest/releases
- One frozen exe at `dist/PhilosophersQuest/PhilosophersQuest.exe` (v2.6.3, 5.15 MB, bundled bank has 3,682 science questions)
- No stray uncommitted files. Working tree clean.
