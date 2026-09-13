# v2.15.0 Readiness Audit

**Date:** 2026-09-12
**Version audited:** v2.14.1 (commit `94b4156`)
**Method:** 7 parallel Opus agent swarms, one per domain. Read-only. No code changes.
**Per-domain reports:** `tools/audit/v2_15/{monster,weapon,armor,magic,cooking,quest,system}_findings.md`

---

## Severity totals — 92 findings

| Domain | P0 | P1 | P2 | P3 | P4 | Total |
|--------|---:|---:|---:|---:|---:|------:|
| Cooking | **1** | 3 | 1 | 5 | 3 | 13 |
| Monster | 0 | 11 | 2 | 1 | 10 | 24 |
| Armor / Shield / Accessory | 0 | 8 | 2 | 1 | 4 | 15 |
| Weapon | 0 | 4 | 3 | 3 | 3 | 13 |
| System / Integration | 0 | 3 | 3 | 5 | 3 | 14 |
| Magic | 0 | 2 | 2 | 2 | 3 | 9 |
| Quest | 0 | 1 | 0 | 2 | 1 | 4 |
| **TOTAL** | **1** | **32** | **13** | **19** | **27** | **92** |

**Severity rubric:**
- **P0** crash-risk or unrecoverable softlock
- **P1** advertised mechanic never fires / dead reference / silent breakage
- **P2** balance outlier or interaction anomaly
- **P3** UI-rot / stale text
- **P4** nit / cosmetic

---

## P0 findings — must fix before ship

### [P0] Class Ascension is dead — 14 boss trophy recipes unreachable, 4 ascension gates never open
**File:** `src/food_system.py` — `get_available_compound_recipes()`
**Issue:** The 2026-06-07 UX change reduced `_COOK_TABS` to just `[('Recipes','compound')]`, but the compound-recipe filter still requires `len(set(ings)) >= 2`. All 14 trophy recipes have exactly 1 ingredient (locked in by `test_class_ascension.py:82-84`), so they can never appear in the cook menu. The `_class_ascension` signal never fires → the F20/F40/F60/F80 class ascension gates never open.
**Blast radius:** Also drops **457 of 516 monster prime recipes** (88.6% — including `goblin_prime`, `mimic_prime`, `dark_elf_prime`, `fire_beetle_prime`) and **6 utility `u_*` recipes** (mushroom_tea, holy_broth, incense_tea, etc.). Only 59 primes appear in any multi-ingredient recipe.
**Fix:** Drop the `>= 2` filter, OR add a `Trophies` tab back with its own filter, OR mark trophy recipes with `always_available: true` and short-circuit.

---

## P1 findings — silent breakage / advertised mechanic never fires

Grouped by root-cause pattern.

### Pattern A: rename/redesign didn't sweep readers (7 findings)

The single most recurring pattern. New system ships but old field name still populated in data, old reader code path never updated.

- **`baby_yaga.regen` vs code `regeneration`** — regen mechanic never fires on Baba Yaga or Green Knight. `data/monsters.json` uses `regen`; `src/monster.py:277` reads `regeneration`.
- **Ingredient system UI shows "none" for every corpse** — `data/monsters.json` still has pre-2026-05-31 `ingredient_id` like `rat_meat`, but `ingredient.json` was re-keyed to `<monster_id>_prime`. `game_render.py:6759` silently returns `None`. One-line fix: use `corpse.kind + "_prime"`.
- **`baseDamage` (camelCase) overrides `base_damage`** — `items.py:306` puts camel first. My v2.14.0 rebase script only updated snake_case. Result: `chandrahas` runs at base 32 (target ~15), `meleager_spear` at 23 (target ~12), `punch_in_the_face` at 9999 (should be 35). Also 77 uniques have twin `chainMultipliers` arrays that disagree with `chain_multipliers` (camel wins → drives `max_chain_length`).
- **3 uniques still carry retired `cleave_at_max`** — `caladbolg`, `parashu`, `labrys`. Both class ladder AND legacy branch fire at max chain = double AoE + double bleeding.
- **`asmodeus.unique_drop_id="ruby_rod"`** — item doesn't exist.
- **`asmodeus.boss_scroll_id="scroll_of_nine_hells"`** — scroll doesn't exist.
- **`tiamat.boss_scroll_id="scroll_of_chromatic_doom"`** — scroll doesn't exist.
- **`baba_yaga.unique_drop_id="iron_mortar_wand"`** — item doesn't exist.

### Pattern B: chain combat v2 dispatch gaps (2 findings, MASSIVE blast radius)

- **`_weapon_key` in `combat.py:128-159` has no case for `class='blunt'` or `class='polearm'`** — every common mace, warhammer, flail, quarterstaff, club, maul, glaive from the material×template pipeline silently applies **zero chain-special effects**. Only uniques (which set `class='mace'/'warhammer'/'staff'/'glaive'`) get the ladder.
- **6 unique clubs get no chain-special ladder either** — `sigurds_shovel`, `sharur`, `heracles_club`, `theseus_club`, `cain_club`, `cuchulainn_hurley` all use `class='club'`, which `_weapon_key` doesn't handle. Docs never listed "club" as a canonical class.

### Pattern C: v2.14.0 C10/15/20 milestones are DEAD CODE (the big one)

- **Chain combat v2 tier-10/15/20 class-specials are UNREACHABLE.** No weapon template ships `chain_exponent`; every template caps at `chain_multipliers` length 3-6, and `quiz_engine._advance` auto-ends at that ceiling. **Every `tier == 10`, `15`, `20` branch in `_apply_chain_class_post_damage` (~200 lines) is dead code.** Chain ranks Brilliant / Genius / Prodigy / Mythic never fire. Migration Step 5 (rebase templates with `chain_exponent: 1.15`) was skipped.
- **Consequence:** `blade_flow`, `melee_dmg_reduction`, `ruptured`, `impaled` are all mechanically-correct but currently unreachable because they need C15/C20 grants. Only `blade_flow` has one live grant path (Soul Reaver innocent-kill).

### Pattern D: designed-but-never-wired sub-systems (dead JSON layer)

- **Shield-block sub-system unwired.** 27 legendary shields declare `block_chance`, `projectile_block`, `spell_block_chance`, `knockback_on_block`. Zero of these are loaded into `Shield.__init__` or read anywhere in src/. The whole "Mycenaean Tower vs Yama's Dharma-Watch" differentiation is invisible in play.
- **3 dead armor procs:** `quest_humility` (Sandals of Perseus), `descend_stairs_no_turn` (Greaves of Hermes), `death_save_bonus` (Tyet of Isis) — fields loaded, no code consumer.
- **3 dead unique-weapon flags:** `talos_sickle.ignore_armor`, `fragarach_the_whisperer.equipped_sound_radius_modifier`, `cain_club.equipped_monster_aggro_radius` — legendary identities are inert.
- **7 `seal_of_*` artifact entries orphaned.** Declare `shatter_on_pickup_with_chronicle` and `seal_demon_drop` — neither token appears in src/. The L100 gate works via a `seals_broken` counter, but the described "pick up the seal" moment never fires. Design doc already flagged.
- **Cu Chulainn's warp-spasm quirk is dead flavor** — earns "legendary Irish battle-frenzy", grants `STR +1` only. No berserk, no fear-immunity.

### Pattern E: missing status registration

- **`reloading` status not in `EFFECT_INFO` / `DEBUFFS` / `_EXPIRE_MSGS`** — renders as raw "Reloading: 1 turns" fallback text. Crossbow chain-15 skip-reload also has no user-visible feedback.

### Pattern F: magic dispatch orphans

- **`blink_spell` + `elder_blink` silently fizzle** after successful cast. `teleport_self` branch lives inside `if target is not None:` but both spells have `needs_target=False`. MP deducts, science quiz runs, nothing happens.
- **Wand `magic_missile` bypasses `MAGIC_TIER_MULT`** — deliberate comment predates v2.14.0. Result: T5 `wand_of_force_cataclysm` deals ~56 dmg vs ~198 for sister T5 wands. Whole force-wand line under-tuned.

### Pattern G: monster mechanic gates

- **`surtur`, `ymir_last_spawn`, `hrungnirs_ghost`** set `enrage_at_hp_pct` + `enraged_multi_attack_count` but have `enraged_pattern: null` — phase-2 flip gated on truthy pattern string, so the whole enrage phase (including count escalation) never activates.

### Pattern H: test coverage gap (structural risk)

- **Zero behavior tests** for the entire v2.14.0 surface — `blade_flow`, `armor_crack`, `deep_wound`, `impaled`, `ruptured`, `sundered`, `cancel_and_strike`, `_chain_bypass_dr`, `_crossbow_skip_reloads`, chain-special dispatch. Only one static source-check exists. No safety net when Pattern C's fix lands.

---

## P2 findings — balance & interaction

Brief:
- **Accessory `spell_crit` unit mismatch** — `get_spell_crit_chance()` divides by 100. Robe of the Magus authors as `10` (→10% correct). Amulet/Ruby line authors as `0.05/0.08/0.12` (→0.0005 etc, silent).
- **`sundered` description says "outgoing damage halved" but code uses `* 0.70` (−30%)** — docstrings triple-repeat the wrong claim at 3 sites.
- **ESC-in-quiz banks the chain identically to SPACE** despite the `# treat as chain-0 failure` comment. Chain 5 ESC → chain 5 hit (identical to SPACE).
- **Base damage on `chandrahas` at 32 vs formula target ~15** (see Pattern A camel-precedence bug) — 2× overshoot.
- **T5 utility spells at 20 MP** vs 22-25 spec (deep_slumber, terror, madness, greater_haste/invis, reflect, omnisight, foresight, mass_paralyze). Damage T5s all in-band.
- **Mini-boss thac0-drift** — L60-band mini-bosses hit less often than same-band trash mobs.
- **14 `hit_and_run` monsters without `can_phase_walls`** — "hide" turns into 4-6 free-kill windows for the player.
- **Pandora's Box + Aladdin's Lamp inert** — `_disabled_reason: "…dispatcher pending — vision audit 2026-05-30"`, quarantined at `min_level: 9999`. Safe (won't crash) but two flagship named artifacts remain dark.
- **Unique spellbook `mp_cost` overrides ignored** — `_learn_from_spellbook` stores per-book mp_cost but `_invoke_spell` reads from `LEARNABLE_SPELLS`. Picatrix / Sefer Yetzirah advertise higher costs, base wins. Harmless (player-favorable) data wart.
- **`amp` stacking cap** — `armor_crack` × `deep_wound` cap at +50% is correct, but not documented anywhere the player can see it.

---

## P3 findings — UI-rot / stale text

**Cluster A: crit still leaks in UI** (v2.14.0 retired crit, some strings didn't sweep)
- `game_render.py:7307` examine card shows "Perfect Chain Crit x{n}"
- `game_render.py:7312-7315` shows "Chain Multipliers: x0.5 …" — lies for polynomial weapons
- `game_render.py:3129` shows "chain x{max_chain_length}" — implies a cap that no longer exists

**Cluster B: cook menu text lies** (post-2026-06-07 UX + one-Q sweep)
- `game_render.py:4479` "Cooking uses an escalator-chain quiz. Higher chains improve the meal." — false, one-Q now
- `game_render.py:2825` labels recipe details "Chain outcomes" — no chain in cook
- `main.py:4620` "EVERY corpse yields Assorted Monster Parts" — false, harvest v3+ per-species

**Cluster C: sundered description mismatch** (see P2)

**Cluster D: single stragglers**
- Hand of Glory power menu says "for 4 turns" but JSON `paralyze_duration: 10`
- Judgment altar karma-0 "silence" branch reads like a missed `elif`
- 7 orphan `seal_of_*` artifact entries (also flagged P1 pattern D)

---

## P4 findings — nits

27 total across domains. Sample:
- Stale `_DEFAULT_MULTIPLIERS` comment in `combat.py` claiming "universal 5-chain"
- Stale ESC-in-quiz comment
- `_curve_note` fields on 96 uniques carry pre-v2.14 vocabulary no code consumes
- Various docstring mismatches after system renames

Full list in per-domain files.

---

## Systemic patterns to internalize

1. **The system-change sweep rule (CLAUDE.md, 2026-09-06) needs teeth.** Every major refactor since March has left dead JSON fields, stale UI text, unread code paths, orphan handlers. The recurring shape is: new code ships, old code path isn't RIPPED, old reader keeps running against new data → silent divergence. Ratchet: make the sweep a CI step (grep for `TODO_sweep` / `_disabled_reason` / retired-keyword text; fail build if present).

2. **camelCase vs snake_case load precedence** is a persistent foot-gun. `items.py` reads camel first, my scripts write snake. Fix: pick ONE canonical case, migrate all data to it, drop the `defn.get(camel, defn.get(snake, default))` pattern.

3. **Chain combat v2 shipped without templates opting in.** The most consequential single miss in this audit. All the class-special work I did in v2.14.0 is currently invisible in play because templates never got `chain_exponent`. When I fix this (Migration Step 5), a large surface goes live simultaneously — needs a real behavior-test net.

4. **Boss drops need a cross-check** — 4 items are declared as boss drops that don't exist. This is a class of bug pytest can't catch without a specific test.

5. **"Designed but never wired" sub-systems** (shield-block quartet, dead armor procs, orphan seals) are the pattern that hurts most narratively — kids find "Aspis of Mycenae" with cool lore, notice zero mechanical difference from a common shield. Deletion or wiring, but stop shipping in this half-state.

---

## Recommended fix priority for v2.15.0

**Must-fix (P0 + P1 chain-combat-v2 restoration):**
1. Cooking P0 — drop the `>= 2` filter or split trophy tab (unblocks class ascension entirely)
2. Templates ship `chain_exponent: 1.15` (unlocks all the C10/15/20 mechanics you already coded)
3. `_weapon_key` handles `blunt` / `polearm` / `club` (common maces/warhammers/staves get their ladder)
4. camelCase precedence swap (fixes 77 unique base_damage silently wrong)
5. Boss-drop items exist (create `iron_mortar_wand`, `ruby_rod`, `scroll_of_nine_hells`, `scroll_of_chromatic_doom` OR remove references)
6. `regeneration` field name unified across data + code
7. Ingredient reader uses `corpse.kind + "_prime"`
8. `reloading` status registered in `EFFECT_INFO` + `_EXPIRE_MSGS`
9. `enraged_pattern` populated for Surtur / Ymir / Hrungnir OR gate check dropped
10. Strip retired `cleave_at_max` from caladbolg / parashu / labrys
11. `teleport_self` branch pulled out of `if target is not None:` for blink spells

**Should-fix (rest of P1):**
- Wire shield-block quartet (or delete the fields on all 27 shields)
- Wire dead armor procs (quest_humility, descend_stairs_no_turn, death_save_bonus)
- Wire dead weapon flags (talos_sickle, fragarach, cain_club) or delete
- Cu Chulainn warp-spasm quirk — actual berserk state
- Wand `magic_missile` line goes through `MAGIC_TIER_MULT`
- Test coverage for v2.14.0 surface

**Nice-to-have (P2/P3):**
- UI-rot cleanup (crit references, cook chain text, sundered description)
- `spell_crit` unit unification
- ESC-in-quiz semantics (currently identical to SPACE)
- Pandora / Aladdin dispatcher wiring (or explicit deletion)

**Not blocking:** all P4 nits.

---

## Per-domain report files

- `tools/audit/v2_15/monster_findings.md` — 24 findings (P0:0, P1:11, P2:2, P3:1, P4:10)
- `tools/audit/v2_15/weapon_findings.md` — 13 findings (P0:0, P1:4, P2:3, P3:3, P4:3)
- `tools/audit/v2_15/armor_findings.md` — 15 findings (P0:0, P1:8, P2:2, P3:1, P4:4)
- `tools/audit/v2_15/magic_findings.md` — 9 findings (P0:0, P1:2, P2:2, P3:2, P4:3)
- `tools/audit/v2_15/cooking_findings.md` — 13 findings (P0:1, P1:3, P2:1, P3:5, P4:3)
- `tools/audit/v2_15/quest_findings.md` — 4 findings (P0:0, P1:1, P2:0, P3:2, P4:1)
- `tools/audit/v2_15/system_findings.md` — 14 findings (P0:0, P1:3, P2:3, P3:5, P4:3)

---

## Play-test gap flagged for you

Bugs I cannot verify without a human at the keyboard:
- Whether the chain-combat-v2 combat FEEL is actually broken (the audit found the code path is dead, but you may not notice because C5 mechanics still work — the whole point of the audit was to find this)
- Save/load state for `_crossbow_skip_reloads`, `_chain_bypass_dr`, `blade_flow` stacks (audit found no explicit persistence layer test)
- Whether the P3 UI text actually appears in real gameplay contexts
- Whether the 6 new v2.14.0 statuses render correctly in the HUD (they should, but audit couldn't test rendering)
