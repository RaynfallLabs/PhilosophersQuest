# Full Systems Audit — Philosopher's Quest

**Date started:** 2026-09-27
**Scope:** every monster, item, quest, mechanic, and UI element in the game — looking for broken, stale, unbalanced, irrelevant, or improvable code, data, and text.

## Baseline: current rules

**Quiz engine (from `src/quiz_engine.py`):**
- Zero-tolerance threshold: one wrong answer ends a threshold quiz. Only Tablet of Destinies reroll.
- Chain v2: wrong answer no longer zeros chain; strike lands at achieved chain.
- Timer: only `math` is timed by default. All others (grammar, science, philosophy, geography, history, animal, cooking, theology, economics, trivia, ai) are untimed.
- Per-run mastery auto-passes fully-cleared tiers.
- Escalator caps at tier 5.

**System-level (from CLAUDE.md + memory):**
- Identify v3 (2026-08-06): one philosophy Q at derived id_tier. Right = full ID, wrong = Stunned 10t. NO masteries.
- Cook v2, Harvest v4, Lockpick v3: one question per attempt; resource consumed on attempt.
- SP soft-boundary via generous food + cook. Damage failsafe at 0 SP.
- Save-bonus gradient (never immunity, hard-capped in `save_bonus_for`).
- Karma -10..+10, prayer cooldown 100-280t, magic_resist blocks magical debuffs.
- BUC system per-instance.
- Chain combat v2: peak-chain damage formula, 11 materials, 22 class mechanics, 149 unique weapon procs.
- Removed 2026-08-06: identify masteries, class masteries, family masteries. `stuffies → carry_bonus` field.

**Recently audited & fixed (2026-09-24, see `ITEM_QUIZ_AUDIT.md`):**
- 25 Dad-reward scrolls now `single_copy` + threshold=1.
- Ring of Pythia, Hamsa Hand, Torque of Lugh, Crown of Brahma, Cassandra quirk retargeted.
- 5 T4-T5 unique books + Dead Sea Scroll: threshold=1.
- 18 non-math timer quirks now grant stat bumps.
- ~166 ingredient/prime_cut temp_descs fixed. 10 container thresholds reset.

---

## Category status (fills in as agents report)

| Category | Status | Notes |
|---|---|---|
| Monsters (527) | ✅ 20 findings, 5 P1 | agent 1 |
| Weapons + ammo + combat | ✅ 36 findings, 4 P1 | agent 2 |
| Quest systems + secret builds | ✅ 4 P1 (7 quest armors unreachable), 6 P2 | agent 3 |
| Death + bones + karma + prayer | ✅ 19 findings, 3 P1 | agent 4 |
| Cooking + harvest + lockpick + containers | ✅ 5 bugs + 11 dead fields, 1 cross-system | agent 5 |
| Dungeon + level + pets | ✅ 56 findings, 8 P1 | agent 6 |
| UI: menus + fantasy screens + HUD | ✅ 32 findings, 1 P1 | agent 7 |
| UI: rendering + help + tooltips | ✅ 25 findings (11 threshold-copy drift) | agent 8 |
| Status effects + spells + save-bonus | ✅ 29 findings (13 spell desc/code drift) | agent 9 |
| Save + meta + data quality | ✅ 21 findings (24 spoilered artifacts) | agent 10 |

---

## Findings sections (fills in as agents report)

### 1. Monsters (527 audited across monsters.json, monster.py, monster_classes.py, boss_levels.py)

**P1 (hard mechanical breaks):**
- `src/monster.py::Monster.__init__` — `is_boss` from JSON is **silently dropped**. `__init__` never reads `defn['is_boss']`. 11 monsters (`abaddon_destroyer`, all 7 `seal_demon_*`, `iron_patriarch`, `whispering_crone`, `blood_archon`) rely on this flag; only Abaddon recovers because `boss_levels._spawn_boss` overrides after construction. The other 10 fall through the `max_hp>500` fallback in `hero_specials.is_boss_or_huge`, and their HP dice mean below 500 — routinely **not boss-immune** to charm/paralyze/confuse/sleep.
- `src/level_manager.py::_try_spawn_seal_demon / _try_spawn_mini_boss` — neither call sets `mb.is_boss=True` after construction. Forced seal-demon path also dropped.
- `src/monster.py::DeathMonster.take_damage` — signature `(self, amount)` drops `damage_type` and `ignore_resistance` kwargs. Any typed hit against Death (reflect procs, lightning splash, mirror-of-souls, chain-passive callbacks at ascension) → `TypeError`.
- `data/monsters.json::grave_knight` — `enraged_pattern='fenrir_rage'` but no `rage_interval` and no `rage_damage_bonus`. Enrage swap is a functional no-op.
- `data/monsters.json::asmodeus, surtur, ymir_last_spawn, hrungnirs_ghost` — `is_mini_boss=True` with **no `spawn_chance`**. `_roll_planned_mini_bosses` filters `spawn_chance<=0` out. Zero hardcoded spawn refs elsewhere. **Four legendary bosses can never spawn.**

**P2 (hazardous / balance):**
- `air_elemental` min_level=4, 2d10+8 avg 19 dmg (peak_floor=14, spread=10) — Gaussian tail reaches F4 where player has ~25-40 HP. One-shot risk.
- `water_elemental` min_level=7 (2d10+6); `stone_giant` min_level=10 (3d8+10 avg 23). Same early-appearance-of-late-damage.
- `mythic_hydra::enraged_multi_attack_count=4` but only 3 attacks. Falls through to "fire all". `4` is misleading data.
- `abaddon_destroyer::chain_break_on_hit=0.35` sets `player._chain_disrupt_pending=True` but nothing reads that flag. Dead-wired.

**P3 (dead code / stale rewards):**
- `harvest_threshold` on all 527 monsters — threaded to `Corpse` but not read anywhere. `food_system.harvest_corpse` uses threshold=1 unconditionally. `bones.py:148` and 4 sites in `game_encounters.py` set 99 as "unharvestable" hint — no effect.
- `attack_effects` (baba_yaga, ravanas_arm, anansi) — 0 readers.
- `mortal_weapon_floor` (celestial_guardian) — 0 readers.
- `ingredient_id` on 525/527 monsters — comment at `food_system.py:1091` says corpse "no longer carries an ingredient_id"; still populated.
- `stone_golem, moss_sentinel, ettin_warchief` — have `enraged_pattern` and `enrage_at_hp_pct` but missing rage fields; enrage provides only AI-pattern swap.

**P4 (UI-rot / conflicting flags):**
- 7 dragon-tier monsters use `treasure.item_tier` 6-10; design cap is 1-5. `_spawn_treasure_item` accepts silently.
- `blood_archon`, `seal_demon_wrath..seal_demon_silence` — **both** `is_boss=True` **and** `is_mini_boss=True`. Conflict.
- `hrungnirs_ghost::enraged_multi_attack_count=0` explicit — enrage doesn't escalate. Likely typo.

**P5 (cleanup / dead duplicates):**
- `boss_levels.py::_make` — defined twice (lines 533 and 646, identical). Harmless duplicate.
- `mind_flayer`, `asmodeus` attack type='psionic' — not in `_damage_multiplier` set. Treated as unresistable 1.0. Rename to `psychic` or document.
- `Monster._DEFAULTS::is_boss: False` is authoritative today because `__init__` never reads defn.

**IMPROVEMENTS:**
- One-line fix: `self.is_boss = bool(defn.get('is_boss', False))` in `Monster.__init__` — repairs boss-immunity for 10 mini-bosses.
- Deprecate `harvest_threshold` field system-wide OR wire it into "corpse too tough" UI hint.
- Deprecate `is_boss` vs `is_mini_boss` — pick one canonical semantic.
- Wire or drop `chain_break_on_hit`.
- Give the four orphan legendaries a `spawn_chance` or forced-spawn path.
- Trim `attack_effects` and `mortal_weapon_floor` from JSON.
- Fix `DeathMonster.take_damage` to accept/discard extra kwargs.
- Delete one `_make` duplicate in `boss_levels.py`.

**VERIFIED OK:**
- All 17 status-effect ids in attacks map to real `status_effects.py` entries.
- All 15 `ai_pattern` values map to real dispatch branches.
- All 11 `summon_kind` targets reference real monster ids.
- 0 references to family/class/monster-class/identify masteries in monster code.
- 0 monsters with min_level>100, peak_floor<min_level, or peak_floor>100.
- All HP dice + attack damage strings parseable.
- All 5 multi-tile monsters late-game with NW-shift fallback.
- `green_knight::revive_once_on_death` correct.
- `vampire`+`ancient_vampire_lord` drain_heals_self both wired to drain attacks.

### 5. Cooking + harvest + lockpick + containers (7 files audited)

**P1 (live bugs):**
- `main.py::_cook_compound` — the reachable compound-cook path **never calls** `_qs_cook.on_food_eaten(...)`. Only the marked-unreachable `_cook_item` does. **Three cooking quirks — Tantalus (15 ruined meals), Persephone (5 distinct Q5 sources), Circe (5 distinct bonus_types) — cannot unlock via normal play.**
- `food_system.py::_apply_recipe_outcome` — v2.6.4 outcomes carry a `tier` field, not legacy `quality`. `main.py:4681-4693` still greps `messages` for `"quality N"` to feed `on_food_eaten`; regex never matches; quality is always 0 even on T5 success.
- `main.py::_lockpick.on_complete` — passes static `'chest_fail'` trap-type string; Job's Endurance quirk (5 distinct trap types) can only ever receive one entry.
- `main.py:4544` — success/fail detection uses `bool(result.get('loot')) or gold>0`. A successful pick with zero items and zero gold misclassifies as failure and fires trap-fail hooks despite no trap firing. Currently unreachable (min gold is 5) but fragile.
- `main.py:1955-1957::_new_game` — comment says "Master Lockpick", but grants `picks[0]` = **basic lockpick** (min_level=1, max_durability=5). Harmless (durability is dead) but naming ↔ reality mismatch.

**P2 (hazardous):**
- `mystery_system.py:181` — mystery cooking challenge uses `escalator_chain` threshold=5. Violates the v3 one-Q flow rule. Any cook-quiz in a mystery bypasses the current model.

**P3 (dead JSON fields — 11):**
- `harvest_threshold` (monsters)
- `ingredient_id` (corpses)
- `quiz_threshold` (containers — recently patched to 1 but field is unread)
- `trapped` + `trap` block (containers — every trapped chest carries full `trap:{...}` decoration; real traps come from `data/chest_traps.json`)
- `extra_item_chance` (containers)
- `max_durability`, `durability`, `durability_loss_success`, `durability_loss_failure` (lockpicks — 4 fields)
- `temp_power`/`temp_duration`/`temp_desc`/`stat_grant`/`trophy_desc`/`trophy_permanent_power`/`trophy_recipe_name` on 527 `prime_cuts.json` entries (only `is_trophy` is read)

**Dead JSON entries:**
- 4 lockpick types (`mithril_lockpick`, `diamond_lockpick`, `philosophers_pick`, and basic `lockpick` if you count the name-mismatch)
- 6 `_comment_*` string entries polluting `cook_outcomes.outcomes` — a stray `outcome_id: "_comment_t1"` would AttributeError

**Dead code (10 items):**
- `food_system.py`: SINGLE_MULT, COMPOUND_MULT, _potency, _single_max_hp, _compound_max_hp, _cooking_heal, _cooking_sp, _apply_tier_outcome
- `main.py::_cook_item` (whole path — noted unreachable)
- `food_system.py::cook_ingredient` (Single tab is gone)
- 25/26 entries in `_TEMP_POWER_REMAP` (only `petrify_resist` sees live use)
- Two legacy tier_outcomes fallback branches in `game_render.py`

**P4 (stale text/comments):**
- `player.py:446::on_level_change` docstring — refers to retired quality gradient / Q3+ singles.
- `food_system.py:120-125` docstring "Q1 = raw SP … Q2-Q5 scale upward".
- `main.py:4710::_cook_item` uses 'mediocre' string that never appears in v2.6.4 output.

**P5 (cleanup):**
- Filter or move `_comment_*` keys in `_load_outcomes()` (single string-entry defense).

**IMPROVEMENTS:**
- Wire `on_food_eaten` into `_cook_compound` OR migrate the quirk hooks to the outcome tier field directly.
- Read `outcome.tier` in `on_food_eaten` instead of regex-scraping "quality N".
- Read the real trap-type from `chest_traps.json` in `on_trap_triggered`.
- Grant `master_lockpick` at `_new_game`, not `picks[0]`.
- Fix or remove mystery-system cooking chain.
- Sweep dead JSON/code — 11 fields + 10 code items + 4 JSON entries.

**VERIFIED OK:**
- Cook cadence: 1 Q, threshold=1, subject='cooking', tier from outcome.
- Cook SP soft-boundary: T1 avg 58.7 SP, T5 avg 151.9 SP (matches memory).
- Harvest cadence: 1 Q, threshold=1, subject='animal', tier from `corpse.harvest_tier`.
- Harvest outcome map: 527 prime-cut IDs all map to real ingredients.
- Lockpick cadence: 1 Q, threshold=1, subject='economics'.
- Recipe → outcome wiring: all 614 recipes have `outcome_id`; zero orphans.
- Trap fires on quiz failure only; universal fail-trap by chest tier.
- All chest-trap effect names present in `EFFECT_INFO`.
- Persephone salvage branch reads correct archetype for ruined path.
- Corpse+ingredient resource-loss semantics correct (consumed pre-callback).
- Container quiz_threshold=1 verified in all 10 chest entries.

### 2. Weapons + ammo + combat (96 weapons, 14 ammo, 2 combat modules)

**P1 (signature effect never fires):**
- `weapon.json::vulcans_brand` — material `"volcanic iron"` (space) doesn't match the material-file id `volcanic_iron` (underscore). `_load_material_tags()` returns nothing; effective_against / vulnerabilities never apply.
- `weapon.json::kladenets (Samosek)` — `counterAttackChance: 0.25` loaded as `counter_attack_chance` but **no consumer exists**. The self-swinger's signature counter-attack is dead.
- `weapon.json::anduril` — `undead_bonus: 2.5` loaded, but `combat.py:1075-1077` applies a hardcoded `1.5×` when > 1.0. The 2.5 value is ignored. Also `is_unique + effective_against=[undead]` gives another 1.5× → 2.25× double-dip, never the intended 2.5×.
- `weapon.json::boomstick` — design_notes promise a chain-5 AOE/shotgun spread, but no wiring exists. Shotgun identity is fiction.

**P2 (mis-route / persistent state / class mismatch):**
- `weapon.json::boomstick` — `weapon_class: "ranged"` routes through the BOW specials ladder (bleeding / blinded / piercing shot / vitals ×2) instead of CROSSBOW. `template_basis: "crossbow"` — specials should match.
- `game_combat.py::_fire_ranged` — crossbow-reload check uses literal `'crossbow'` (line 1484). Boomstick's `weapon_class: 'ranged'` bypasses it, so the shotgun fires with zero reload.
- `weapon.json::curtana` — `spare_kill_max_hp_per_floor: 5` uses `weapon._spare_kill_floor_hp` counter that is **never reset** in `_change_level`. Per-floor silently becomes per-run.
- `weapon.json::mjolnir_shard` — design_notes claim a chain-5 lightning proc; no wiring exists. Only the parent Mjolnir has `chain_lightning_at_chain_n`.
- `combat.py::player_attack` — `attack_chain_cap_bonus` (Ring of Gawain, Torque of Lugh) applied ONLY when `_max_chain is not None` (line 1983). Every weapon with `chain_exponent=1.15` sets `_max_chain=None` → the bonus is effectively dead everywhere.
- `game_combat.py::_fire_ranged` — sets `_combat_monsters_ref` etc. but NOT `_combat_game_ref` (unlike `_start_combat` at 1775). Latent bug for any weapon-side mechanic that reaches for game via a ranged shot.

**P3 (dead data / misleading fields):**
- `weapon.json::(hunt_captains_sword, wendigo_fang, echidna_fang, vulcans_brand)::equip_threshold` — dead: no weapon-equip quiz path exists.
- `weapon.json::ruyi_jingu_bang::chain_modulated_reach` — `can_melee_attack` uses `max(v)` regardless of chain. Targeting always uses biggest reach; the "staff grows with chain" fantasy is a lie at chain 0.
- `weapon.json::chandrahas` + `chandrahasa` — two nearly identically-named entries (T4 finesse-3.0× and T5 normal-2.0×). Likely duplicate; both spawn under different tier bands.
- `items.py::Weapon` — `equipped_monster_aggro_radius`, `equipped_sound_radius_modifier`, `_karma_disappear_rolled_this_floor` loaded but no consumers. Dead fields.
- `weapon.json::sword_of_michael::max_chain_length=6` — silently overridden by `@property` returning `len(chain_multipliers)`. Works incidentally; JSON field is authoritative-in-name-only.

**P4 (naming / material drift):**
- 21 uniques reference material names that don't exist as material files ("divine iron", "divine bronze", "dark iron", "enchanted iron", "spectral iron", "legendary", "bone", "fang", "hardwood", "wood", "gold", "leather", "dad"). Pure lore strings pretending to be material links.
- `combat.py::_BYPASS_DR_TIERS` — only lists 7 weapon classes; 2h and light classes never bypass DR at any chain rung. Design intent unclear.
- `ammo.json::shotgun_shell` — `min_level: 9999`; Boomstick same. No natural discovery path.
- Ranged weapons consume ammo BEFORE the quiz — chain 0 (miss) still burns ammo. Unarmed melee whiffs are free.

**P5 (nitpicks):**
- `chainsaw_prosthetic` — symbol `"("` when every other melee uses `")"`. Renders backwards.
- `punch_in_the_face` — `material: "dad"`. Cute; any material lookup silently returns 1.0.
- `sword_of_damocles` — `cursedMissBacklash=2` + `damoclean_counter_auto_kill=true` stacks penalty on a T2 sword.
- `gram + broken_gram` — `min_level: 9999`, only obtainable via the Odin altar throw-reforge. No in-game hint besides `fafnir_blood` potion.

**IMPROVEMENTS:**
- Normalize material naming (underscore ids everywhere OR make `_load_material_tags` also index space-names).
- Wire Boomstick + Mjolnir Shard chain-5 procs OR strip the misleading design_notes.
- Fix `undead_multiplier` to use the numeric value AND gate the `effective_against` 1.5× so uniques with explicit multipliers don't double-dip.
- Reset `_spare_kill_floor_hp` in `_change_level` (Curtana per-floor cap).
- Route Boomstick's `_weapon_key` to `crossbow` (matches template_basis) AND apply reload lockout — or define a new `'shotgun'` key.
- Add `player._combat_game_ref = self` in `_fire_ranged` for symmetry.
- Delete dead-load Weapon fields OR wire consumers.
- Remove `equip_threshold` from weapon JSON.
- Merge `chandrahas` and `chandrahasa` OR clearly differentiate names.

**VERIFIED OK (highlights, 30+ uniques):**
- soul_reaver, dawnbreaker, excalibur, durendal, joyeuse, curtana, pharaohs_crook, venomfang, gungnir, fail_not, hrunting, harpe, tyrfing, mjolnir, zulfiqar, gandiva, laevateinn, spear_of_longinus, sudarshana, chrysaor, stormbringer, parashu, meleager_spear, skofnung, carnwennan, akinakes_acrisius, atalanta_bow, kusanagi, oathkeeper, caliburn, sword_of_michael, gram / broken_gram (Odin altar reforge lives), sling_of_david (infiniteAmmo works).
- Chain-v2: chain 0 = miss, cursed_miss_backlash consistent everywhere.
- Tablet reroll + Ring of Scheherazade one_thousand_and_one gated correctly in both melee and ranged.

### 3. Quest systems + secret builds (9 quest chains + 12 mysteries + 38 encounters + 30 secret builds)

**P1 (functional / unreachable content):**
- `hero_specials.py::niten_ichi_ryu (miyamoto musashi)` — passive gate is `weapon AND ranged_weapon`, but Musashi ships **two melee** (`_start_weapon: longsword`, `_start_melee: shortsword`). `ranged_weapon` slot only accepts `requires_ammo` weapons. Signature +15% dual-wield bonus **dead** until a bow is picked up. Contradicts journal "Two swords are better than one."
- `data/items/armor.json::quest_spawn_{nemean,green_knight,serpent,arachne,erlking,anansi,nidhoggr}` — 7 boss-drop unique armors declare `spawn_method: quest_spawn_X` and `min_level: 9999`. **No code in `src/` implements any of the 7 quest_spawn methods.** Items UNREACHABLE. Chain-equip flows dead.
- `mystery_system.py::mimir_reward` — `all_timer_bonus: 1` populates `player.quiz_timer_bonuses[<subject>]` for all 10 subjects, but only `math` is timed. 9/10 dead. Reward text: "all quiz timers+1s".
- `armor.json::green_knights_plate` — `equip_chain_mode: escalator_chain`, T5 `passive_second_beheading_returns` and stacked `tier_bonuses`. Item has no spawn path (P1 above). Entire chain-equip integration dead / untested.

**P2 (balance under zero-tolerance):**
- `mystery_system.py::solomon` — threshold 6/8 history T3. Under zero-tolerance: "6 correct in a row." Values tuned pre-zero-tolerance.
- `mystery_system.py::grail/fisher_king/oracle/mjolnir/sphinx` — same pattern; `total_qs` is decorative.
- `quirk_system.py:1540::sisyphus` — reward text openly admits "economics quiz timer +5s applies if economics ever becomes timed."
- `mystery_system.py::sisyphus` physical challenge — 25 tiles OVER carry limit while holding 30-lb boulder. STR-starved builds (Diogenes STR 5) may be un-completable.
- `shield.json::bronze_aegis` — pre-form shield with unimplemented `quest_spawn_aegis_pre` at `min_level: 1` (not 9999). Plot-locked pre-form ungated.
- `game_encounters.py::_apply_npc_reward('random_wand')` — reward branch exists but no encounter uses it. Dead.

**P3 (design flags):**
- `npc_encounters.py::deadite_woman option 3` — "It's a trick, get an ax" grants karma +1 AND 30-60 gold **at no cost**. Option 1 grants karma +1 despite triggering an ambush + 10% HP damage. Naive-help punished, cynical trickery rewarded. Karma logic inverted.
- `npc_encounters.py::azarael_demon` — "Shatter the chains" pays STR+2 + 200 gold at karma -1. One -1 rarely tips a tier; cost:reward mispriced.
- `artifact.json::plot_locked` — field appears on many quest items but never referenced in `src/`. Doc-only; real gating is `min_level: 9999`.
- `mystery_system.py::pandora invert_result` — winning gives BAD outcome; losing gives THE reward.
- `MysteryKeyItem symbol='P'` — collides with player symbol; cosmetic.
- `weapon.json::excalibur.design_notes` — says "peak 5.0x at chain-5" but `chainMultipliers` peak = 2.0. Doc/data mismatch.

**P4 (spawn/regen edges):**
- `_JUDGMENT_TIERS` — karma=10 requires 10 "+1" blocks. Reachable but fragile.
- `spawn_mystery_for_level` — 60% per generation, no lifetime cap. Same mystery re-generatable on save/reload if never triggered.
- `spawn_merchant` — 20% per floor, no per-run cap. 20+ merchants theoretically possible.
- `_maybe_spawn_magic_carrot` — spawns at floor `randint(1, 19)`; if player skips that floor, unicorn quest becomes uncompletable.
- `MYSTERIES['cauldron']` — escalator_chain success requires chain ≥ 5 with zero-tolerance. Playable but demanding.

**P5 (cleanup):**
- `hero_specials.py::"nikola tesla"` — HERO_SPECIALS entry is None (passive-only); OK.
- `_start_cow_encounter` — poke count 10 persists on Game; no reset between floors.
- `judge_karma` fallback branch is unreachable per docstring.
- `forge_mjolnir::chainMultipliers` has 6 entries (chain 0-5), Excalibur has 5. Nonstandard.

**IMPROVEMENTS:**
- Implement the 7 quest-armor spawn methods OR delete the JSON (right now ~15KB of dead stat blocks/lore).
- Retune mystery thresholds for zero-tolerance semantics (halve or reframe).
- Rewrite Mimir's Well reward as math-only or replace with substantive mechanical reward.
- Musashi passive: trigger on two equipped melee, OR retitle to "melee + ranged combo".
- Strike the dead economics-timer parenthetical from Sisyphus quirk text.
- Add per-run merchant cap (3-4).
- Self-repair Magic Carrot: drop on any 1-19 floor player visits.
- Invert karma on deadite ambush (naive-help karma 0 or -1; cynical option karma +1 with mechanic reward only, no karma bonus).
- Add explicit tests for the 7 quest-armor spawn paths.

**VERIFIED OK:**
- Bronze Bull → Ariadne shrine (L12→L17), Eye of Graeae → Athena shrine (L29→L37), Broken Gram → Odin altar (L48/L53 — both drop-on-altar and throw-over-altar paths work; `_throw_weapon` game_combat.py:293-315 correct), Gleipnir 6-component quest (L62-77→L76), Vidar's Sandal (10 leather scraps→L79 altar), L99 Altar of Judgment (all 5 tiers), Philosopher's Shard (Plato bypass, Diogenes shard-drop tracked), Duck of Doom (2026-turn transform), Excalibur cast_me_away (HP≤25%, once per run), Cow Level (30-39 spawn, 10 pokes→L999, exit portal returns to origin), Ethereal Unicorn state machine (4 states, karma-negative fled path, 5-tier chain quiz rewards).
- Merchant NPC: 20% per floor, price = tier × class × weight, Soul Sphere 15% inclusion.
- All 12 mysteries: correct trigger predicates + rewards route through `apply_mystery_reward`.
- 30 karma NPC encounters: 10 blocks, trigger items exist, all cost/reward types have handlers.
- 5 flavor NPCs: trades work, rewards granted.
- Hero passives: plato_no_shard, will_to_power, cynic_detachment, demigod_hide_25, witcher_mutations/resists, elder_blood_escape, vengeance_wakes, resonant_frequency all consumed at hook sites.
- Hero active specials: all 19 route through `_DISPATCH`; each resolver handles `boss_immune`.
- Judgment karma clamp `-10..+10` matches design.
- Fisher King `fisher_cooldown` consumed at game_divine.py:981-982.

### 9. Status effects + spells + save-bonus (3 files: 527 monsters not in scope)

**P1 (functional):**
- `status_effects.py::berserk` — in BOTH `DEBUFFS` (line 126) AND `BUFFS` (line 147). `dispel_magic`/`drain_magic`/`cancellation` in `game_magic.py` will strip berserk off monsters as a buff, while UI debuff filters also show it. Ambiguous classification.
- `status_effects.py::apply_debuff_with_save` — for effects **not** in `SAVE_STAT` (poisoned, bleeding, burning, etc.) the save bonus is BYPASSED (line 431). Torque of Lugh `save_bonus: {cat: all, amount: 3}` **does not help** against these debuffs, despite text implying "all saves".
- `game_magic.py::abjuration` (line 1065-1086) — wand handler calls `target.status_effects.clear()` on the monster, stripping player-applied DoTs (poisoned/burning/petrifying/bleeding). Inconsistent with `cancellation` / `dispel_magic` / `drain_magic` which strip only BUFFS. Stale pre-v2-audit dispatch.
- **13 spell desc/code duration mismatches (systemic chain=5/chain_scale=1.0 fossil):**
  - `magic_shield_spell` T3 aliased to same 12-turn 'shielded' as T1 `mage_armor_spell` — tier progression dropped.
  - `stoneskin_spell` desc "30 turns" → actual 25.
  - `greater_haste_spell` desc "25 turns" → actual 10 (identical to Haste).
  - `phase_door_spell` desc "12 turns" → actual 15.
  - `reflect_spell` desc "20 turns" → actual 15.
  - `counterspell_spell` desc "15 turns" → actual 12.
  - `detect_monsters_spell` desc "15 turns" → actual 20.
  - `imprisonment_spell` desc "40 turns" → actual 60 (capped by MAX_EFFECT_DURATION).
  - `paralyze_spell` / `hold_monster_spell` desc "10/5 turns" → both 8.
  - `slow_spell` desc "6 turns" → actual 10.
  - `fear_spell` desc "8 turns" → actual 10.
  - `annihilate_spell::threshold_pct = 0.10 + chain * 0.05` pinned at 0.35 by fossil chain=5.
  - `power_word_kill_spell::INT * chain * 4` = INT*20 — a hidden `chain=5` fossil; silently breaks if chain alias ever changes.
- `game_magic.py::magic_missile` handler (line 1876) BYPASSES `_spell_damage` and MAGIC_TIER_MULT. Force-family spells under-scale relative to all other damage families.

**P2 (missing / mis-scoped):**
- `status_effects.py::doom_dot` — in `EFFECT_INFO` but missing from BOTH `DEBUFFS` and `BUFFS`. UI filters keyed on those sets drop it. No `_EXPIRE_MSGS` entry either.
- `status_effects.py::petrifying` — has `SAVE_STAT='CON'` but not in `HARD_CONTROL`. Successful save merely halves duration; the val==1 death tick means half-duration can still fully kill. Save should negate outright.
- `status_effects.py::_RESIST_BLOCKS::drain_resist` — blocks only `{'diseased'}` (also blocked by `poison_resist`, so functionally redundant). Never gates the `draining` HP tick despite the display name promising "immune to stat drain".
- `spells.py::elder_scream` — `mp_cost: 10` at `tier: 2`. Outside T2 5-8 MP band.
- `status_effects.py::stunned` — capped at 3 and in HARD_CONTROL, but its real semantic is soft (may stumble, quiz timer -25%). HARD_CONTROL's "no refresh, no reapply, +3 grace" is an over-strong stunlock preemption.

**P3 (cosmetic / stale):**
- `_EXPIRE_MSGS` missing entries for many effects: armor_crack, sundered, deep_wound, ruptured, impaled, heal_blocked, blade_flow, melee_dmg_reduction, reloading, save_guard_CON/WIS/DEX/all, stand_ac, crit_buff, fear_immune, boomstick_aoe_next, control_immune, parry_armed, riposte_armed, see_invisible, warning, searching, truesight, dark_vision, identify_sight, life_save.
- `MAX_EFFECT_DURATION=60` — non-CONTROL effects use `current + duration` additive stacking. Asymmetric with CONTROL's refresh-max.
- `_EFFECT_NOUN['stunned']` maps to 'daze' but expire line uses "no longer stunned" — save-flavor vs expire-flavor wording drift.
- `petrifying` missing `_EXPIRE_MSGS` entry.

**IMPROVEMENTS:**
- Add `berserk` to only one of BUFFS/DEBUFFS; adjust dispel_magic list accordingly.
- Wire `save_bonus_for` into `apply_debuff_with_save` for the no-SAVE_STAT branch.
- Rewrite `abjuration` to strip only BUFFS from the target (match cancellation).
- Sweep the 13 spell duration mismatches — replace `_active_spell_tier`-driven values, delete chain fossils.
- Fix `magic_missile` to route through `_spell_damage` for tier scaling.
- Add `doom_dot` to DEBUFFS + `_EXPIRE_MSGS`.
- Move `petrifying` into `HARD_CONTROL` OR document that save halves.
- Wire `drain_resist` into the `draining` effect gate.
- Elder Scream: mp_cost 6-8, not 10.
- Add explicit `stunned` in a new SOFT_CONTROL group with refresh semantics.

**VERIFIED OK:**
- `save_bonus_for` gradient math: `perm + min(timed, 3)` clamped to 5. Perseus + Torque + Hamsa = perm 7 → clamped 5. Cap works.
- `apply_effect` HARD_CONTROL guard: refuses reapply while locked + during 3-turn grace. No permalock hole.
- `_RESIST_BLOCKS::magic_resist` blocks `{confused, charmed, silenced, feared, hallucinating, hallucinating_pot}`.
- `grendel_grip` tick-clear correct for Coif of Beowulf.
- All spells' quiz call: `mode='threshold', subject='science', threshold=1, tier=spell.tier` (with spellbook_chain_bonus reducing effective tier). No chain-v1 fossils in quiz.
- All spell effect IDs in `LEARNABLE_SPELLS` have a dispatch branch (verified 60+ effects).
- Wand contract: `mode='threshold', subject='science', threshold=1, tier=wand.tier`.
- Hamsa Hand / Torque of Lugh / Pectoral of Amun / Amulet of Fortitude save_bonus paths all traced through `_gear_save_bonus`.
- No mastery/class_masteries/stuffie mastery references anywhere in status_effects/spells/game_magic. Identify-v3 removal clean.
- Perseus quirk `save_bonus_all: 2` routed correctly through `_quirk_save_bonus`.

### 4. Death + bones + karma + prayer

**P1 (hard breaks):**
- `src/main.py::_do_exit` — calls `_on_game_over()` BEFORE setting `self.defeat_reason='fled'`. Bones always records `defeat_reason='died'` on flee (and on victory).
- `src/main.py::_on_game_over` — unconditionally saves a bones file on VICTORY (a `has_stone` win still routes here). Produces a "ghost of a winner" haunting L1 in future runs; plays the `'death'` sound on the victory screen.
- `src/bones.py::save_bones` — persists `player.level` which **doesn't exist on Player**. Hard-coded to 1 forever, so ghost damage collapses to `1d4+1` regardless of dungeon depth. Ghosts are trivial from L1 through L100.

**P2 (hazardous / balance):**
- `src/game_divine.py::_start_pray.on_complete` — Fisher King unlock reads `hp_pct` AFTER `_resolve_simple_prayer` restored HP. A chain ≥ 2 prayer heals above 15%, so the `hp_pct ≤ 0.15` gate fails. Only chain-1 (SP-only) prayers count toward Fisher King.
- `src/bones.py::spawn_ghost` — flavor line renders `"who fled on this floor"` verbatim from `defeat_reason` (nonsensical for a ghost).
- `src/game_divine.py::_start_pray / _confirm_divine_intercession` — passes `extra_seconds` + `base_seconds` for theology (untimed). Dead computation at three call sites.
- `src/combat.py::Penitent kill_count_karma_adjust` — `_g.karma = cur_karma + 1` bypasses the [-10, 10] clamp. Currently safe (only fires when karma < 0) but any future path could break the invariant.

**P3–P5 (dead code / UI-rot / cleanup):**
- `bones.py::save_bones` dead `isinstance(equipped, dict)` guard; hard-coded ghost `min_level:1 max_level:100 harvest_tier:0 harvest_threshold:99`; ghost `treasure` dict dead (ground gear placed separately).
- `game_divine.py::_KARMA_VERSES` only 'fallen' defines key `0`; other tiers rely on a chain-0-shim at line 872. Saintly tier has no chain-0 verse (silent "The heavens are silent." fallthrough).
- `highscore_system.py::add_score` — same-day same-score name collision can hit two entries; `_load` silently returns `[]` on corruption without logging.
- `main.py::_on_game_over` plays `_snd.play('death')` even on victory.
- `crash_handler.py` — no guard if `player` itself is `None`; inner try/except swallows the traceback.
- `game_divine.py::_resolve_simple_prayer` — 3 separate cooldown-halving exit points, fragile.

**IMPROVEMENTS:**
- Refactor `_on_game_over` to take explicit `reason` + `is_victory`, skip `save_bones` on victory, called AFTER `defeat_reason` is set.
- Wire ghost damage to `max_level_reached` from `level_manager`, or drop damage-scaling entirely.
- Capture `hp_pct` pre-prayer for Fisher King measurement.
- New helper `Player.get_quiz_time_kwargs(subject)` returning `{}` for untimed subjects — uniform caller pattern.
- New helper `_adjust_karma(delta)` on Game to centralise the ±10 clamp.
- Bones-file schema stability test (round-trip).

**VERIFIED OK (highlights):**
- Bones consume-on-load prevents infinite haunting.
- Karma clamp `-10..+10` in `_award_encounter_outcome`.
- `save_bonus_for` hard-caps at +5 (timed lane +3).
- All death paths except `_do_exit` set `defeat_reason='died'` correctly.
- 9 cascading death-preventions (Rand's Heart, Ankh of Isis, Green Knight's Plate, Tyet of Isis, Winged Sandals psychopomp, Doom of Ragnarok, Joan's Breastplate, Asmodeus Pact-Blood, Jade Cicada) — consume-once semantics correct.
- Divine Intercession is once-per-run; off-altar uses threshold=5/total_qs=5/T5 theology.
- Fisher King halves cooldown, floor of 1t.
- No mastery references in bones / prayer / highscore / save.

### 6. Dungeon + level + pets (dungeon.py + level_manager.py + pet_system.py; 56 findings)

**P1 (functional bugs):**
- `pet_system.py::random_species` — includes `'duck_of_doom'` in the pool. Soul Sphere throws, Summon Guardian, and Gate spells can produce a Waddlekind at any floor **without** the 2026-turn Duck-on-Head quirk. Leak.
- `main.py::_duck_of_doom_transform` — never calls `apply_late_pickup_bonus`. Hatched Waddlekind starts at L1 (21 HP / 3 dmg); on realistic hatch floors (F20+) it dies in one hit.
- `level_manager.py::_roll_planned_mini_bosses` — secondary-slot collision loop (`while target in planned: target += 1`) doesn't skip boss floors {20,40,60,80,100}. Mini-boss silently vanishes because `generate_boss_level` ignores the plan.
- `dungeon.py::_generate_maze_dungeon::_apply_terrain` — water pools (level ≥ 10) and ice rooms (level ≥ 40) can sever maze connectivity. No post-terrain reachability check.
- `bones.py::spawn_ghost` — skips monster-occupancy check. Ghost can co-locate with a mini-boss or seal demon placed earlier the same turn.
- `dungeon.py::spawn_items(traps)` — trap types tier-agnostic; polymorph/teleport traps can hit F1 player. Trap count caps at 3 floor-wide even at F100.
- `hero_specials.py::_eff_summon_sketch_helper` — `attacks=[{'damage': '1d8+2'}]` fixed across all tiers 1-5. SketchedPet damage never scales with hero-special tier; only duration and helper.min_level scale.
- `pet_system.py::FenrirPet` — species dict uses legacy fields `special_name`/`special_status` but has NO `specials` list. `available_specials()` returns `[]`; Fenrir has no listable specials in the pet menu.

**P2 (balance / persistent-state / spawn-collision):**
- `level_manager.py::_roll_planned_mini_bosses::band 5 upper bound is 100 (a boss floor)`. pf=100 pre-shifts to 99, but the collision loop can advance target back into 100.
- `_SEAL_DEMON_LEVELS` — 7 forced-spawn floors sit inside mini-boss band 5. A non-seal random mini-boss with peak_floor==83 can spawn on the same floor as the forced Wrath demon; both spawn.
- `_apply_terrain (ice rooms)` — random pick from `rooms[1:]` can be `rooms[-1]` (stairs-down room), forcing a slippery slide onto the exit.
- `_apply_terrain (lava rivers)` — lava gated on `not dungeon.is_maze`, but water is NOT — mazes at f10/30/50/70/90 can be flooded.
- `spawn_items (vault gold)` — `rng.randint(level*5, level*15)` per inner tile; up to ~6000 gold uncapped at F100.
- `pet_system.py::Pet._move_toward` — pets don't consult `dungeon.pits` or `dungeon.traps`. Pets step into player-dug pits and repeatedly trigger floor traps.
- `pet_system.py::_SPECIES['duck_of_doom']::specials.sometimes_goose` — `targeting='visible_all'` uses game.visible on the caster; unverifiable that pet resolves correctly (many hero specials lack that path).
- `hero_specials.py::_eff_summon_sketch_helper` — spawns at `(px, py)` with no walkability/occupancy check. Player-tile overlap.
- `pet_system.py::SketchedPet::tick_duration` — no explicit call site was found. If uncalled, the sketch is permanent (design says timed 15-40t).
- `sketchedpet.get_attack_damage` — ignores `quiz_accuracy`; base Pet uses 0.5-1.2× multiplier. Sketch pets don't benefit from chain accuracy.

**P3 (dead code / stale legacy fields):**
- Boss floor set duplicated in 3 places: `dungeon.py::_BOSS_LEVELS`, `boss_levels.py::BOSS_LEVELS`, inline in `level_manager.py::_roll_planned_mini_bosses` lines 160, 169.
- `level_manager.py::generate` second `_place_stone` block (lines 92-95) is dead — L100 branch always returns first.
- FenrirPet/SketchedPet/DadPet/UnicornPet all set `self._special_cooldown` (singular) alongside `_special_cooldowns` (dict). Dead legacy attribute.
- `_populate_hidden_chambers` and `_spawn_monster_den_extras` exploit the "spawn_monsters skips first" convention twice — rename or refactor.
- `pet_system.py::Pet.gain_xp` — L100 cap silently drops residual XP.
- `pet_system.py::apply_late_pickup_bonus` — only called from Soul Sphere path; Duck transform, hero-special, and spell-summon paths never call it.
- `bones.py::_place_cursed_gear` — increments `tile_idx` but doesn't check ground_items overlap; bones item stacks on pre-placed floor item.

**P4 (cosmetic / small nits):**
- `dungeon.py::_add_extra_connections` — pairs only within 5-30 tile distance. Long-diagonal rooms never get loop edges on wide maps.
- `_generate_maze` — mutates `sys.setrecursionlimit` globally without a lock (thread-unsafe if dungeon gen ever moves off main thread).
- `_assign_dark_rooms` — stores dark_rooms as set of centers; consumer must reverse-lookup by tile every FOV query (slow at scale).
- `pet_system.py::_SPECIES['duck_of_doom']` — `element='psychic'`, `damage_type='psychic'`. No psychic resistance in standard resistance table; damage is effectively untyped.

**P5 (cleanup):**
- Extract 13 tile constants (WALL..ICE) with an `is_hazard(x,y)` helper.
- `bones.py::load_bones` 50% roll runs before file-existence check; wasted call.
- `spawn_items::trap dict` deep-copy shares RGB tuple (mutation-safety only).
- No `family mastery` / `monster class mastery` / mastery references anywhere in pet_system.py — clean.

**IMPROVEMENTS:**
- Reachability check after `_apply_terrain` on mazes.
- Trap tier scaling by floor band.
- Sync `DUCK_OF_DOOM_TURNS_REQUIRED` (main.py) with `_QUIRK_UNLOCKS['duck_of_doom_turns']` — single source.
- Add `apply_late_pickup_bonus` call in Duck transform + hero-special + spell-summon paths.
- Sketch helper: scale `attacks[]` damage dice by tier.
- Give Fenrir a `specials` list.
- Consolidate boss-floor set into one constant module.

**VERIFIED OK:**
- Bones return re-curses gear correctly; Kilt of the Pharaoh preserves one item.
- No mastery references in pet_system.py or level_manager.py.
- Waddlekind 2026-turn quirk gate is correct in main.py.
- Corridor width bump for f76+ works.
- All 7 seal demons exist in monsters.json.
- Pet `command` field ('return'/'stay'/'wander') branches correctly.
- Cow Level (999) routes through `generate_boss_level` correctly.

### 7. UI: menus + fantasy screens + HUD (5 files, 32 findings)

**P1 (functional):**
- `game_menus.py:1608::_activate_gold_offering` — literal `{cost}` and `{target.name}` reach the log **unsubstituted**. String is `.format(tname=...)` only; needs to be an f-string or `.format(cost=cost, target=target, tname=target.name)`.

**P2 (hazardous):**
- `welcome_screen.py:320::SECRET_BUILDS["titivillus"]` — `_qa_tools: True` grants Shift+I immortal toggle and Shift+W floor warp. Hidden dev/QA build **exposed to anyone typing "titivillus"** at name entry.

**P3 (dead-promise / stale copy):**
- 16 non-math timer quirks have parenthetical dead promises (Scheherazade, Merlin, Sisyphus, Asclepius, Penelope, Dionysus, Athena, Shiva, Circe, Kali, Ibn Battuta, Tesla, De Medici, Confucius, Galileo, Shakespeare) — the retarget already grants stat bumps; the "+Ns if the subject ever becomes timed" tail is honest but noisy.
- 3 all-subjects timer quirks (Sibyl, Zoroaster, Machiavelli) have awkward "applies to math combat" copy.
- `game_menus.py:1206, 1110 (sage_counsel)` — "all quiz timers extended" / "+25% quiz timer" is math-only.
- `_open_power_menu:1122` empty-menu message says "Earn quirks to unlock them!" — hero specials, elder blood, armor-granted, and carried-artifact powers all surface here too.
- `game_menus.py:60/65/112` — dead `'single'` cook-tab branch (`_COOK_TABS` has only `('Recipes','compound')`).

**P4 (verification needed):**
- `hud_context.py::hud_item_name` — under Identify v3, TYPE-known / INSTANCE-unknown should render as `"unidentified <true name>"`. Helper flips to `item.name` as soon as `knows_item_type` returns True; no "unidentified" prefix inserted. Verify upstream naming or fix.
- `hud_context.py:170-241::active_power_rows` — Gleipnir Bind Odinkiller shown always `"ready"` with no cooldown row; if a cooldown is ever added, HUD won't reflect it.
- `hud_context.py` bleed — `game_render.py:1034` renders `"Quiz timer: {math_t}s (combat) to {econ_t}s (text-heavy)"` — implies per-subject timing exists (rot).
- `game_menus.py:1391::sketch_manifest` targeting hint says "TAB to cycle" — verify STATE_TARGET handler wires TAB.

**P5:**
- `welcome_screen.py:809` footer omits F2 for leaderboard (only shown on the leaderboard panel).
- `welcome_screen.py:194 SECRET_BUILDS["dad"]` — `_immortal: True`, all stats 20. Intended easter egg but same channel as titivillus.

**VERIFIED OK:**
- Every menu state has global ESC dismiss (game_input.py:88-169). No orphaned modals.
- Hero specials wired correctly via `pl.hero_specials` + `hero_special_cooldowns` + `hero_`-prefix dispatch.
- Identify v3 menu: single philosophy quiz, Shard requirement (Plato exempt), corpses flattened, `id_level<5` filter.
- `panel.py` and `fantasy_ui.py`: pure chrome, no mechanic strings.
- `FP.SUBJECT` map complete for 12 subjects.
- No `chain break`/`mulligan`/`identify mastery`/`class mastery`/`family mastery` strings anywhere in `_QUIRK_EFFECTS` / `_QUIRK_TRIGGER` / `_QUIRK_FLAVOR`.

### 8. UI: rendering + help + tooltips (game_render.py, ui.py, hud_context.py, main.py; note: no `help_screens.py` — help lives in game_render.py::_draw_help_screen)

**P1 (actively lies to player):**
- `ui.py::Sidebar._derived L248` — `(f"Picks {getattr(player, 'lockpick_charges', 0)}", …)`. `player.lockpick_charges = 0` at init and never incremented (floor lockpicks convert to gold in `main.py:4181-4188`; Master Lockpick is permanent with no charge check). Sidebar permanently reads **"Picks 0"**. Actively lies every frame.
- `game_render.py::_draw_character_sheet L1032-1035` — `f"  Quiz timer:    {math_t}s (combat) to {econ_t}s (text-heavy)  x{timer_mod}"`. Computes economics-timer figure though every non-math subject is untimed. Character sheet asserts a text-heavy timer that doesn't exist.
- `game_render.py::_draw_character_sheet L1036-1038` — `f"    +{int_bonus}s on magic subjects (INT bonus)"`. Magic subjects (science) are untimed; INT bonus never fires.

**P2 (systemic UI-rot — threshold copy omits zero-tolerance rule):**
- 11 item-card / lore-dossier strings say `"Equip threshold: N correct"` or `"Quiz Threshold: N correct answers"` without mentioning "any wrong = fail":
  - `_kit_item_details` L6464 (Armor), L6478 (Shield), L6501 (Accessory), L6511 (Wand), L6520 (Scroll), L6530 (Spellbook)
  - `_draw_lore_dossier_screen` L7224 (Armor), L7235 (Shield), L7246 (Accessory), L7251 (Wand), L7255 (Scroll), L7294 (Spellbook)
- Player reads "3 correct" and reasonably assumes wrongs are permitted.

**P3 (help-text incomplete for v3 / chain-v2 / zero-tolerance):**
- `_draw_help_screen L8258-8303` — entire panel is a keybind list; **no mention** of zero-tolerance, chain v2 milestone ranks, math-only timing, identify v3 / cook v2 / lockpick v3 / harvest v4. New player can't learn these from `?`.
- `_draw_help_screen L8276` — "Identify item or study corpse" is confusable with the `;` Study Journal. Recommend "Identify item / corpse (1 philosophy Q)".
- `_draw_help_screen` — **no H** binding listed (harvest); pygame.K_h → `_harvest()`.
- `_draw_help_screen` — **no C** binding listed (cook menu); pygame.K_c → `_open_cook_menu()`.
- No reference to the CLAUDE.md subject→action mapping table anywhere in help.

**P4 (term drift — "mastery" vocabulary lingers post-removal):**
- `game_render.py::_draw_active_powers L5051` — `subtitle="Earned through quirk mastery -- each power has limited uses."` Uses the banned term.
- `game_render.py::_discoveries_sections L4060` — `tier_bits.append(f"T{ti} MASTERED")`. Per-run tier mastery is retained, but shares vocabulary with removed class/family mastery. Consider "T{ti} CLEARED".
- `main.py::_on_quiz_answer L4806-4811` — `add_message("MASTERY! …Tier X {subj} now succeeds automatically.")` + `_log_chronicle("Achieved Tier X {subj} mastery -- cleared the entire tier.")`.
- `quirk_system.py L1540, L1583` — awkward "if economics ever becomes timed" hedge in player-facing description.

**P5 (opaque / other):**
- `_draw_identify_menu L4403` — `f"Shard: {'carried' if has_shard else 'passive or override'}"`. "passive or override" is opaque jargon.
- `ui.py::Sidebar._effects L285-317` — effect chips iterate without a hard cap; overflow drops silently past bottom (no "+N more" like POWERS has).
- `quiz_engine.py::start_quiz L189` — `total_qs = threshold * 1.5`. Dead math under zero-tolerance; UI reading `total_qs` inherits stale semantics.
- `_draw_quiz L2156` — `c_text = f"{qe.correct_count} / {qe.required}"` shows threshold ratio but no visible "1 wrong = fail" cue anywhere in the quiz modal.
- Comment `game_render.py:56-58` — describes "mastery-progression 1-4" as legacy prose; code path is current identify-v3.

**IMPROVEMENTS:**
- Delete Sidebar "Picks 0" row OR replace with a live lockpick indicator.
- Rewrite `_draw_character_sheet` timer line: `f"Quiz timer: {math_t}s (combat only). Other subjects untimed."`
- Add a helper `f"Equip: {N} correct (any wrong = fail)"` and sweep all 11 threshold strings.
- Add a "System rules" panel to `_draw_help_screen` covering zero-tolerance, chain v2 ranks, math-only timing, subject→action mapping (or link to it).
- Add H and C bindings to help.
- Rename "quirk mastery" copy in `_draw_active_powers` and either rename or gloss `T{ti} MASTERED`.
- Rewrite `MASTERY!` toast/chronicle to something like `TIER {N} {subj} CLEARED — auto-passes this run.`
- Trim the "if economics ever becomes timed" parenthetical from Sisyphus/quirk copy.
- `_draw_identify_menu` shard row: "Shard active" / "Shard needed" concrete label.
- Cap effect chip rendering with `+N more` (mirror POWERS overflow hint).
- Consider showing a "1 wrong = fail" marker in the quiz modal on threshold quizzes.

**VERIFIED OK:**
- `_draw_cook_menu L4479-4481` — "Cooking uses one cooking question. Right = full meal; wrong = ruined." Matches cook v2. Explicit v2.15.0 UI-rot fix.
- `_draw_lore_kit_lines L2827-2828` — matches cook v2.
- `_draw_identify_menu L4405-4406` — matches identify v3.
- `_draw_scroll_menu L4353` — accurate.
- `_draw_help_screen L8293-8294` — "Pray (theology chain)", "Divine Intercession (1/run)" accurate.
- `_draw_quiz L2144-2158` — chain-v2 rank display + per-milestone scaling.
- `_draw_quiz L2188-2214` — timer bar only rendered when `qe.timed`. Comment at 2188-2192 correctly enumerates untimed quizzes.
- `_draw_combat_hud L2412-2467` — polynomial + array chain damage projections; SPACE-cancels behavior current.
- `_identify_status_label L53-68` — current identify-v3 model; legacy save fallback intentional.
- `_draw_lore_dossier_screen L7195-7217` — v2.15.0 UI-rot fix. Crit label removed, chain-exponent shown honestly.
- `hud_context.py` — pure data helpers, no stale mechanics.
- `ui.py::MessageLog`, `text_layout.py` — no mechanic references.
- `_kit_item_details` Weapon block (L6440-6455) — no threshold string.
- Grep for `mulligan` / `chain break` / `identify mastery` in `src/` — no surviving stale mechanic strings in rendered text.

### 10. Save + meta + data quality (save_system.py, highscore_system.py, crash_handler.py, paths.py, JSON data)

**P1 (spoilers / unspawnable / unicode):**
- `data/items/artifact.json` — **24 artifacts** have `identified: false` + `id_level: 0` but **no `unidentified_name`**. Since `Artifact` inherits `self.unidentified_name = defn.get('unidentified_name', defn['name'])`, `_display_name` renders the TRUE name for unknown items. Major spoiler for: Philosopher's Stone, Bronze Bull Idol, Eye of the Graeae, Sound of a Cat's Footstep, Roots of a Woman's Beard, Root of a Mountain, Breath of a Fish, Spittle of a Bird, Sinew of a Bear's Sensitivity, Gleipnir, leather scrap, all 7 Seven Seals, Scales of Michael, Cursed Lodestone, Sealed Dispatch, Palladium, Tablet of Destinies, Vidar's Sandal.
- Same file: `Palladium`, `Tablet of Destinies` have `id_level: null` — flows through `int(defn.get("id_level", 5 if identified else 0))`. `int(None)` would raise `TypeError` unless coerced elsewhere. Verify.
- `data/items/scroll.json::scroll_of_nine_hells` — `floorSpawnWeight` all-zero AND no `peak_weight`/`spread`. **Unspawnable.**
- `data/items/scroll.json::scroll_of_chromatic_doom` — same. **Unspawnable.**
- `data/monsters.json`, `data/items/armor.json`, `data/items/ingredient.json` — `N��h�ggr's Scale` and related lore contain corrupted Unicode (U+FFFD replacement chars where `ð` should be). Visible in-game.

**P2 (save-lifecycle / bestiary):**
- `data/monsters.json::*.ingredient_id` on 525/527 monsters — writes an OLD-scheme id (`rat_meat`, `goblin_flesh`, `insect_carapace`, `spectral_essence`, …). Harvest v4 ignores it. **`game_render.py::_draw_bestiary_page:7104` at `id_level>=2` calls `load_ingredient_for(subject.ingredient_id)` → returns None** because those ids don't exist in `ingredient.json`. Bestiary "Ingredient:" / "Solo cook:" / recipe hint lines never render.
- `data/monsters.json::*.harvest_threshold` on all 527 monsters — no code reads it. Harvest v4 uses threshold=1 unconditionally. Dead field.
- `src/player.py::__setstate__` — migrates only `known_forms`/`known_materials`. Does NOT strip removed-mastery attrs (`class_masteries`, `subject_mastery_xp`, family-mastery blessing pools, `stuffies_active`, `_active_stuffies`). Old pickles carry dead attrs forever.
- `src/save_system.py::_save_path` — `re.sub(r'[^\w\-]', '_', name.lower())` doesn't dedupe. "Alice!" and "Alice?" both → `save_alice_.pkl`. Permadeath clobber risk.

**P3 (hygiene / duplicate-name):**
- `data/items/accessory.json::Caduceus of Hermes` vs `data/items/wand.json::Caduceus of Hermes` — same display name, different mechanics (regen amulet vs 7d6 heal wand). No explicit `id` field; item loader keys by name. Name-based lookup would collapse them.
- `data/items/armor.json::Níðhöggr's Scale` (tier-5 cloak, min_level 9999) vs `data/items/ingredient.json::Níðhöggr's Scale` (trophy). Same display name, different types.
- `data/items/cook_outcomes.json::trophy_medusa` — `temp_power: "petrify_resist"` is NOT in `status_effects.BUFFS`/`DEBUFFS`; works only via `food_system.py:206-208` legacy alias `petrify_resist → save_guard_CON`. Data lies to itself (self-comment says "canonical status_effects").
- `data/items/wand.json::ruby_rod` — all-zero band table but `peak_weight: 3.0`, `spread: 6`, `peak_floor: 92` set. Not unspawnable (Gaussian wins) but misleading data rot.

**P4 (dead field / cosmetic):**
- `data/items/*.json::spawn_method` (12 unique values, including all 7 `quest_spawn_*`) — ZERO consumers in `src/`. Purely documentary; any typo would silently rot.
- `data/monsters.json::abyssal_locust` — L98, HP 2d8, max damage 6. Quest-spawned by Abaddon (intentional swarm), but shape is indistinguishable from a data typo. Gate with a `quest_only` tag.
- `src/save_system.py::save_game` — no schema/version field in the pickled state dict. No migration hook.
- `src/save_system.py::save_game` — `game.quiz_engine.get_deck_state()` not `getattr`-guarded (every other field is). Refactor-fragile.
- `src/save_system.py::save_game` — mixes bare `game.xxx` (player_gold, dungeon_level) with `getattr(game, ..., default)` idioms. Refactor-hazardous.
- `src/highscore_system.py::_score_file_path` — computed at module import; no file locking. Two concurrent instances would race on `_save()`.

**P5 (cleanup):**
- `src/highscore_system.py::add_score` — rank-recovery walks by `(score, name, date)`; two runs with identical score/name/day return first hit only.
- `src/save_system.py::_find_unpicklable` — culprit list capped at 8; can miss additional bad attrs. Documented.

**IMPROVEMENTS:**
- Add `unidentified_name` to all 24 spoilered artifacts (e.g., Seals → "sealed metal disc", Tablet → "obsidian tablet", Palladium → "ancient wooden idol").
- Fix `Palladium` / `Tablet of Destinies` `id_level: null` → `0` or `5`.
- Add `peak_weight` + `spread` OR fix bands for `scroll_of_nine_hells` + `scroll_of_chromatic_doom`.
- Sweep-fix Unicode corruption on Níðhöggr strings (armor.json, ingredient.json, monsters.json lore).
- Bestiary path: either remove `subject.ingredient_id` from `_draw_bestiary_page` and route via `prime_cuts.json`, OR rewrite each monster's `ingredient_id` to `<monster_id>_prime`/`_trophy`.
- Add `pop` for removed-mastery attrs in `Player.__setstate__` — clean old saves.
- Dedupe `_save_path` output on collision (append counter).
- Give one of the two "Caduceus of Hermes" a distinct display name, OR add explicit `id` fields.
- Move Medusa cook_outcome to a canonical status name or extend `_TEMP_POWER_REMAP` note.
- Sweep `spawn_method` field: either wire a consumer OR move into a comment/`_meta` block.
- Add a `schema_version` to save state + a load-time migration hook (deferred item #5 from CLAUDE.md).

**VERIFIED OK:**
- `paths.py` (`_root`, `data_path`, `save_dir`) — dev/frozen split correct, cross-platform data dirs correct.
- `crash_handler._project_root` — uses `game_log.log_dir()` with fallback; no hardcoded legacy path.
- `crash_handler.write_crash_report` — emergency save invoked before crash file write. Correct order.
- `highscore_system._calc_score` — uses only `turn_count`, `max_level_reached`, `monsters_killed`, and Philosopher's Stone check. Zero dead mastery-XP references.
- Atomic save writes (`tmp + os.replace`) — matches CLAUDE.md save-lifecycle invariant.
- Monster peak_floor/min_level/thac0 — no OOB.
- Item `tier > 5` — none.
- Item `min_level > 100` — all 57 hits are boss/quest/plot-locked.
- Recipe `outcome_id → cook_outcomes.outcomes` — 0 missing.
- Chest-trap `effect` — 15/15 canonical.
- Cook outcome `temp_power` — 42/43 canonical (only `petrify_resist` non-canonical, aliased).
- Monster spawn pool (`dungeon._build_spawn_pool`) — story-locked entries correctly gated by `peak_weight <= 0`.

---

## Priority-ordered summary (10 agents, ~330 unique findings)

### **P0 (game-breaking / spoiler / never-fires) — 8 items**

1. **`data/items/artifact.json` — 24 artifacts missing `unidentified_name`** — Seven Seals, Michael's Scales, Palladium, Tablet of Destinies, Philosopher's Stone all render their true names on pickup. Major plot spoiler.
2. **`Monster.__init__` silently drops `is_boss` from JSON** — 10 mini-bosses (blood_archon, iron_patriarch, whispering_crone, all 7 seal demons) are routinely NOT boss-immune to charm/paralyze/confuse/sleep from hero specials + spells.
3. **`main.py::_cook_compound` never calls `on_food_eaten`** — 3 cooking quirks (Tantalus, Persephone, Circe) permanently unreachable via normal play.
4. **7 quest-spawn armor methods unimplemented** — Nemean Pelt, Green Knight's Plate, Serpent, Arachne, Erlking, Anansi, Nidhoggr; all UNREACHABLE (`spawn_method: quest_spawn_X` + `min_level: 9999`, no code implements).
5. **4 legendary mini-bosses can never spawn** — asmodeus, surtur, ymir_last_spawn, hrungnirs_ghost have `is_mini_boss: True` but no `spawn_chance`; filter drops them; no hardcoded spawn refs.
6. **`hero_specials.py::niten_ichi_ryu`** — Miyamoto Musashi's signature dual-wield passive is DEAD (gate requires ranged, kit ships two melee).
7. **`game_menus.py:1608::_activate_gold_offering`** — literal `{cost}` and `{target.name}` reach the log unsubstituted (bad `.format` call).
8. **`ui.py::Sidebar._derived L248`** — "Picks 0" hardcoded lie every frame (lockpick_charges is never incremented).

### **P1 (functional bugs) — ~25 items**

**Combat / monsters:**
- `DeathMonster.take_damage` signature crashes on typed hits (missing `damage_type`/`ignore_resistance` kwargs).
- `weapon.json::vulcans_brand` — material `"volcanic iron"` (space) doesn't match `volcanic_iron` (underscore). Signature effect never applies.
- `weapon.json::kladenets` — `counterAttackChance: 0.25` loaded but no consumer. Self-swinger counter dead.
- `weapon.json::gungnir` — `neverMiss: true` field has no reader. Signature accuracy dead.
- `data/monsters.json::grave_knight` — `enraged_pattern='fenrir_rage'` but no `rage_interval`/`rage_damage_bonus`. Enrage is a no-op.

**Spells:**
- 13 spell descriptions vs code durations mismatched (stoneskin 30→25, greater_haste 25→10, phase_door 12→15, reflect 20→15, counterspell 15→12, detect_monsters 15→20, imprisonment 40→60, paralyze 10→8, hold_monster 5→8, slow 6→10, fear 8→10, magic_shield_spell same as mage_armor_spell, annihilate/PWK pinned by chain=5 fossil).
- `game_magic.py::abjuration` strips ALL player-applied DoTs from monster (inconsistent with cancellation/dispel).
- `magic_missile` handler bypasses MAGIC_TIER_MULT; entire Force spell family under-scales.
- `status_effects.py::berserk` in both BUFFS and DEBUFFS (classification ambiguous).
- `status_effects.py::apply_debuff_with_save` bypasses `save_bonus_for` for non-SAVE_STAT effects (Torque of Lugh doesn't save vs poison/bleeding/burning despite text).

**Pets / dungeon:**
- `pet_system.py::random_species` leaks `duck_of_doom` (Waddlekind spawnable without quirk).
- `main.py::_duck_of_doom_transform` never calls `apply_late_pickup_bonus` (hatched Waddlekind combat-useless at F20+).
- `level_manager.py::_roll_planned_mini_bosses` — secondary-slot collision loop can land on boss floors {20,40,60,80,100}, silently voiding the mini-boss.
- `dungeon.py::_apply_terrain` — water/ice can sever maze connectivity.
- `level_manager.py::_try_spawn_seal_demon / _try_spawn_mini_boss` — never set `is_boss=True` after construction (compounds Monster.init bug).

**Cook / harvest / lock:**
- `main.py:4681-4693` — regex-scrapes "quality N" from messages that no longer contain it. Quality always 0.
- `main.py::_lockpick.on_complete` — passes static `'chest_fail'` trap-type; Job's Endurance can only ever register 1 entry (needs 5 distinct).
- `main.py:1955-1957::_new_game` — grants `picks[0]` (basic lockpick, min_level=1), not `master_lockpick` as comment claims.

**Data quality:**
- `scroll_of_nine_hells` — unspawnable (all-zero band, no peak_weight/spread).
- `scroll_of_chromatic_doom` — unspawnable (same).
- `mystery_system.py::mimir_reward` — `all_timer_bonus: 1` populates all 10 subjects but only math is timed. 9/10 dead.
- `armor.json::green_knights_plate` — entire chain-equip integration (T5 passive_second_beheading_returns + tier_bonuses) dead because item is unspawnable.

**Save/meta:**
- `game_render.py::_draw_bestiary_page:7104` — `load_ingredient_for(subject.ingredient_id)` returns None for 525/527 monsters because ids are old-scheme (`rat_meat`, etc.) not in `ingredient.json`. Bestiary "Ingredient:" / "Solo cook:" lines never render.
- `Palladium` and `Tablet of Destinies` have `id_level: null` — potential `int(None)` TypeError.

### **P2 (balance / hazardous / stale-under-zero-tolerance) — ~40 items**

- 5 mystery thresholds inherit pre-zero-tolerance tuning (solomon 6/8, grail 4/6, oracle 4/6, mjolnir, sphinx) — under one-wrong-fails they're much harder than tuned.
- `mystery_system.py::sisyphus` boulder challenge may be un-completable for STR-starved builds (Diogenes STR 5).
- `welcome_screen.py:320::titivillus` — Shift+I immortal + Shift+W floor warp exposed to anyone typing "titivillus" at name entry. QA cheat still live.
- 3 dragon-tier low-min-level monsters (air_elemental L4, water_elemental L7, stone_giant L10) — Gaussian spawn tail can one-shot new player.
- 7 dragon-tier monsters use `treasure.item_tier: 6-10` (design cap 1-5).
- `mystery_system.py:181` cooking challenge uses `escalator_chain` threshold=5 (violates v3 one-Q rule).
- 11 threshold-copy strings across item cards / lore dossier say "N correct" without "any wrong = fail" cue.
- `_draw_character_sheet` shows fictitious economics timer + INT-magic timer bonus.
- `_draw_help_screen` has ZERO mention of zero-tolerance, chain v2, math-only timing, subject→action mapping.
- `_draw_help_screen` missing H (harvest) and C (cook) bindings entirely.
- `abyssal_locust` L98 max damage 6 — should be `quest_only` tag.

### **P3-P5 (dead-fields, cosmetic, cleanup) — ~200 items**

- **Dead JSON fields (12 categories):** `harvest_threshold` (527 monsters), `ingredient_id` (525 monsters), `attack_effects` (3 monsters), `mortal_weapon_floor` (celestial_guardian), `chain_break_on_hit` (abaddon), 7 dead prime_cut fields on 527 entries, `spawn_method` (all items — no consumer), 5 lockpick durability fields, `container.trapped`+`container.trap`, `container.extra_item_chance`, `quiz_threshold` on containers (unread), `plot_locked` (never referenced).
- **Dead JSON entries:** 3 unused lockpick types (`mithril_lockpick`, `diamond_lockpick`, `philosophers_pick`); 6 `_comment_*` polluting `cook_outcomes.outcomes`.
- **Dead code:** 8 items in food_system (SINGLE_MULT, COMPOUND_MULT, _potency, etc.), `_cook_item` path in main.py, `cook_ingredient` path, 25/26 entries in `_TEMP_POWER_REMAP`, two `tier_outcomes` fallback branches in game_render, duplicate `_make` in boss_levels.py, ~50 "mastery" vocabulary strings (MASTERY! toast, MASTERED tier labels, "Earned through quirk mastery" subtitle, "if X ever becomes timed" quirk parentheticals).
- **Duplicate constants:** Boss floor set in 3 places; `_SPECIES['duck_of_doom']` element='psychic' with no consumer; duplicate item names `Caduceus of Hermes` (accessory vs wand) and `Níðhöggr's Scale` (armor vs ingredient).
- **Unicode corruption:** Níðhöggr name mangled in 3 JSON files.
- **UI overflow:** Effect chips silently drop past bottom (no `+N more` hint).
- **Cook outcome:** `trophy_medusa::petrify_resist` — non-canonical status alias, works via legacy `_TEMP_POWER_REMAP` only.
- **Text drift:** 20+ "MASTERY!"/"MASTERED"/quirk-timer parentheticals; character sheet + Sisyphus + Mimir Well UI still promise timers on untimed subjects.

### **Improvement opportunities (cross-cutting) — ~30 items**

**Quick wins (< 30 min each):**
- Fix `Monster.__init__` to read `defn['is_boss']` — one line, unblocks 10 mini-bosses' boss-immunity.
- Add `unidentified_name` to 24 artifacts — one JSON pass.
- Delete Sidebar "Picks 0" row.
- Rewrite `_draw_character_sheet` timer line to "math combat only, other subjects untimed".
- Fix `_activate_gold_offering` `{cost}` / `{target.name}` format bug.
- Fix `_new_game` to grant `master_lockpick`, not `picks[0]`.
- Add H and C to help panel.
- Trim "if economics ever becomes timed" parenthetical from Sisyphus + 15 other quirks.
- Fix corrupt Unicode Níðhöggr in 3 JSON files.

**Medium (30 min – 2 hrs each):**
- Sweep 11 threshold-copy strings to include "any wrong = fail".
- Sweep 13 spell duration descs to match code.
- Add "System rules" panel to `_draw_help_screen`.
- Fix `_draw_bestiary_page::load_ingredient_for` — route via `prime_cuts.json`.
- Add `pop` for removed-mastery attrs in `Player.__setstate__`.
- Retune 5 mystery thresholds for zero-tolerance semantics.
- Migrate `magic_missile` to `_spell_damage` for tier scaling.
- Rewrite `abjuration` to strip only BUFFS.
- Add `apply_late_pickup_bonus` call to Duck transform + hero-special + spell-summon paths.
- Wire `_qs_cook.on_food_eaten` into compound-cook path.

**Larger (design + implementation):**
- Implement OR delete the 7 quest-armor spawn methods (currently ~15KB dead JSON).
- Add `spawn_chance` OR forced-spawn paths for the 4 orphaned legendaries.
- Fix `niten_ichi_ryu` to trigger on 2 equipped melee OR retitle.
- Redesign Mimir's Well reward to be substantive under math-only timing.
- Sweep `spawn_method` field — wire a consumer OR move to `_meta`.
- Add `schema_version` + migration hook to save state.
- Deprecate `harvest_threshold` + `is_boss` vs `is_mini_boss` semantic collision.
- Rewrite `MASTERY!` toast/chronicle to `TIER {N} CLEARED`.
- Karma balance rework on deadite ambush (Option 1 vs Option 3 inverted).
- Add per-run merchant cap (3-4).
- Self-repair Magic Carrot: drop on any 1-19 floor visited.

---

## Totals

- **10 categories audited, ~330 unique findings.**
- **8 P0 (game-breaking / spoiler).**
- **~25 P1 (functional bugs).**
- **~40 P2 (balance + hazardous + stale-under-zero-tolerance).**
- **~200 P3-P5 (dead fields, cosmetic, cleanup).**
- **~30 improvement opportunities.**
- Extensive VERIFIED OK sections (mechanics that survived intact).
- Zero P0 crashes on the normal play surface — highest-severity live-play issues are the 24 spoilered artifacts and the 10 mini-bosses losing boss-immunity.
