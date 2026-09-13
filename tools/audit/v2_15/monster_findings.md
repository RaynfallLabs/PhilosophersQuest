# Monster audit findings — v2.15.0 readiness

- Total: 24 findings
- P0: 0, P1: 11, P2: 2, P3: 1, P4: 10
- Files reviewed: data/monsters.json (527 entries) + src/monster.py (1733 lines) + src/combat.py + src/game_combat.py + src/food_system.py + src/game_render.py + src/level_manager.py + src/boss_levels.py + tools/balance/CURVE.md + tools/balance/rebase_monster_hp_report.md
- Cross-refs run:
  - `treasure.unique_drop_id` → weapon.json / armor.json / artifact.json / accessory.json / shield.json
  - `treasure.boss_scroll_id` → scroll.json
  - `treasure.ammo_drop.ammo_id` → ammo.json
  - `ingredient_id` → ingredient.json
  - `summon_kind` → monsters.json self-refs
  - `attacks[].type` and `resistances`/`weaknesses` → combat.py `_damage_multiplier` + player damage-type paths
  - `attacks[].effect` → status_effects.py `apply_debuff_with_save`
  - `ai_pattern` → monster.py `if self.ai_pattern ==` dispatch (aggressive, cowardly, sessile, ambush, ranged, healer, summoner, mimic, hit_and_run, dancer, fenrir_rage, abaddon, seek_locust, grid_bug)
  - Every JSON field name → monster.py `defn.get(...)` consumers + Grep across `src/`

Note: `is_boss` is set at spawn time for the 5 spine bosses in `src/boss_levels.py:89` (asterion_minotaur, medusa_gorgon, fafnir_dragon, fenrir_wolf, abaddon_destroyer). Mini-bosses spawned via `level_manager.py._try_spawn_mini_boss` do **not** get `is_boss` back-patched — their JSON value is authoritative.

---

## P0 — crash-risk

None found. All required fields (`id, name, symbol, color, hp, attacks, min_level`) are present on all 527 monsters. Colors are all `[r,g,b]` triples of ints in 0-255. Symbols are all 1-char strings. Damage strings all parse as dice or ints. `max_level >= min_level` where set.

---

## P1 — mechanically-broken

### [P1] baba_yaga — signature drop points to nonexistent item
**File**: data/monsters.json (baba_yaga)
**Issue**: `treasure.unique_drop_id = "iron_mortar_wand"` — this id does not exist in `data/items/wand.json`, `weapon.json`, `artifact.json`, or any other item file.
**Evidence**: `treasure: {"gold":[130,260], "item_chance":1.0, "item_tier":4, "unique_drop_id":"iron_mortar_wand", "boss_scroll_id":"scroll_of_baba_yaga"}`; grep across `data/items/*.json` returns no matches.
**Fix**: add an `iron_mortar_wand` wand/artifact in `data/items/`, or change the id to an existing baba-yaga-appropriate drop (e.g. `wand_of_the_witch`, if one exists) or set `unique_drop_id: null`.

### [P1] asmodeus — signature drop points to nonexistent item
**File**: data/monsters.json (asmodeus)
**Issue**: `treasure.unique_drop_id = "ruby_rod"` — not present in any item JSON.
**Evidence**: `treasure.unique_drop_id: "ruby_rod"`; item-id search across `data/items/*.json` finds nothing.
**Fix**: create the `ruby_rod` artifact/wand in `data/items/artifact.json` (Asmodeus' canonical Rod of Asmodeus fits) or repoint to an existing endgame drop.

### [P1] tiamat — boss scroll drop points to nonexistent scroll
**File**: data/monsters.json (tiamat)
**Issue**: `treasure.boss_scroll_id = "scroll_of_chromatic_doom"` — not present in `data/items/scroll.json`.
**Evidence**: cross-ref of all 28 `boss_scroll_id` refs shows only tiamat and asmodeus (below) miss.
**Fix**: add `scroll_of_chromatic_doom` to scroll.json (tie-in to tiamat's five chromatic breaths) or repoint.

### [P1] asmodeus — boss scroll drop points to nonexistent scroll
**File**: data/monsters.json (asmodeus)
**Issue**: `treasure.boss_scroll_id = "scroll_of_nine_hells"` — not present in `data/items/scroll.json`.
**Evidence**: same audit as above.
**Fix**: add `scroll_of_nine_hells` to scroll.json or repoint.

### [P1] baba_yaga — regeneration silently zero (typo field name)
**File**: data/monsters.json (baba_yaga)
**Issue**: field is written as `"regen": 3`. `monster.py:286` reads `getattr(self, 'regeneration', 0)`; there is no `regen` reader anywhere in `src/`. Baba Yaga never regenerates as intended.
**Evidence**: `baba_yaga: regen=3 regeneration=None`.
**Fix**: rename `"regen"` → `"regeneration"` in the JSON.

### [P1] green_knight — regeneration silently zero (typo field name)
**File**: data/monsters.json (green_knight)
**Issue**: same `"regen": 5` typo. The Green Knight's "beheading game" pact combines `revive_once_on_death` (wired, works) with steady regen (dead field). Between the revive and later hits, the knight is supposed to be healing back — currently he does not.
**Evidence**: `green_knight: regen=5 regeneration=None`; `revive_once_on_death: true, revive_hp_pct: 0.5`.
**Fix**: rename `"regen"` → `"regeneration"`.

### [P1] surtur — enrage phase never fires (falsy enraged_pattern gates the flip)
**File**: data/monsters.json (surtur)
**Issue**: `enrage_at_hp_pct: 0.4`, `enraged_multi_attack_count: 4`, but `enraged_pattern: null`. `monster.py:782` gates the enrage flip on `self.enraged_pattern` being truthy, so `_enraged` never becomes True; consequently `enraged_multi_attack_count` also never activates. Surtur has no phase 2.
**Evidence**: `enrage_at_hp_pct=0.4 enraged_pattern=None enraged_multi_attack_count=4`.
**Fix**: set `enraged_pattern: "aggressive"` (or a real pattern) so the flip fires; the enraged multi-attack count kicks in from that point.

### [P1] ymir_last_spawn — enrage phase never fires (same shape as surtur)
**File**: data/monsters.json (ymir_last_spawn)
**Issue**: `enrage_at_hp_pct: 0.35`, `enraged_multi_attack_count: 3`, `enraged_pattern: null`. Phase 2 never activates.
**Evidence**: same as above.
**Fix**: set `enraged_pattern: "aggressive"`.

### [P1] hrungnirs_ghost — enrage phase never fires (same shape as surtur)
**File**: data/monsters.json (hrungnirs_ghost)
**Issue**: `enrage_at_hp_pct: 0.3`, `enraged_pattern: null`. Phase transition never fires.
**Evidence**: same shape as above.
**Fix**: set `enraged_pattern: "aggressive"` (or `"fenrir_rage"` if a rage-stack second phase is intended).

### [P1] tiamat / asmodeus / medusa / baba_yaga / lamia / rangda / anansi — mini-bosses missing/false `is_boss`, so min_hit_chance is 5% instead of 25%
**File**: data/monsters.json (multiple)
**Issue**: `monster.py:389, 483, 1497` compute `is_boss = getattr(self, 'is_boss', False)` with NO `max_hp>500` fallback (unlike combat.py / game_magic.py which OR the HP fallback). Then `min_hit = 0.25 if is_boss else 0.05`. These mini-bosses spawn via `level_manager._try_spawn_mini_boss`, which does not back-patch `is_boss` (unlike `boss_levels._spawn_boss:89`, which sets it True for the 5 spine bosses). Result: a heavily-armored player can miss-lock these mini-bosses at ~5% hit floor, not the intended 25% "boss floor".
**Evidence**: `tiamat.is_boss=false`, `asmodeus.is_boss=false`, `surtur.is_boss=false`, `ymir_last_spawn.is_boss=false`, `hrungnirs_ghost.is_boss=false` (all explicit `false`); `medusa`, `baba_yaga`, `lamia`, `rangda`, `anansi` — field absent entirely.
**Fix**: set `is_boss: true` on all `is_mini_boss: true` entries whose HP > 500 (nine monsters). Alternative: change `monster.py:389/483/1497` to `getattr(self, 'is_boss', False) or self.max_hp > 500` to match the pattern used elsewhere in `game_magic.py`.

### [P1] hit_and_run monsters other than Asterion cannot phase walls, so their "hide" state is inert
**File**: data/monsters.json (14 monsters: brigand, hugin_raven, changeling, puca, quasit, shadow_demon, imp, homunculus, shade, wererat, pixie_swarm, satyr_trickster, boggart, carbuncle)
**Issue**: `ai_pattern: "hit_and_run"` with no `can_phase_walls`. `_hit_and_run_turn` retreats via `_phase_move` for 3 turns then sits in 'hiding' state 4-6 turns doing nothing (`return False`). Asterion vanishes into phasing walls; these 14 monsters sit exposed on open floor for ~7 turns after every 1-2 hits — the player just walks up and kills them while they wait. Mechanic is broken for the whole family.
**Evidence**: `if m.get('ai_pattern')=='hit_and_run' and not m.get('can_phase_walls')` — 14 matches.
**Fix**: either (a) give small/tricksy mobs a non-wall-based hide (invisibility for the hiding duration), (b) switch these entries to `ambush` or a new `harass` pattern, or (c) grant `can_phase_walls: true` if hiding in a wall is thematically OK (probably not for brigand/wererat, arguably fine for shade/shadow_demon).

---

## P2 — balance

### [P2] Late-game mini-bosses have thac0 markedly worse than same-level trash mobs
**File**: data/monsters.json (banshee_lich, frostfang_giant, crypt_summoner, shadow_archer, veiled_inquisitor, lava_elemental, iron_patriarch, whispering_crone, medusa_gorgon, greater_mimic — see evidence)
**Issue**: bucketed by (min_level // 10) peer median, several named/mini-boss entries have thac0 ≥ 6 worse than their peer median. In practice they hit prepared players LESS often than random spawn-pool monsters at the same band. Combined with the P1 `is_boss`/`min_hit_chance` issue above, some of these will genuinely miss-lock.
**Evidence**:
- L60-69 peer median thac0 = -6.5. `banshee_lich` L66 thac0=1, `frostfang_giant` L62 thac0=1, `crypt_summoner` L62 thac0=1, `shadow_archer` L63 thac0=1, `veiled_inquisitor` L64 thac0=1, `lava_elemental` L68 thac0=0.
- L30-39 peer median thac0 = 2. `iron_patriarch` L35 thac0=5, `medusa_gorgon` L38 thac0=2 (OK by median but low for a boss — CURVE.md L40 target is 2 to -4).
- L50-59 peer median thac0 = -3. `whispering_crone` L55 thac0=-3 (at median — but as a boss should be ≥ 4 below).
- L30-39 `greater_mimic` L33 thac0=5 (peer median 2).
**Fix**: run a pass to bring named/mini-boss thac0 into the "at or better than peer median" invariant; per CURVE.md §4 the spine bosses want the low end of their band. Suggested: banshee_lich → -7, frostfang_giant → -6, crypt_summoner → -6, shadow_archer → -7, veiled_inquisitor → -6, lava_elemental → -6, iron_patriarch → -5, greater_mimic → -3.

### [P2] abaddon_destroyer treasure.item_tier=10 vs peer range 1-8
**File**: data/monsters.json (abaddon_destroyer)
**Issue**: `treasure.item_tier: 10`. `game_combat.py:831` maps `effective_floor = max(1, tier * 5)`, so item_tier=10 → effective_floor 50. Player is on floor 100 when they kill Abaddon; the drop pool caps at mid-game gear. Peers (tiamat 8, asmodeus 7, surtur 6, seal demons 4) sit in the 4-8 range.
**Evidence**: `item_tier` distribution `{1:61, 2:99, 3:151, 4:116, 5:93, 6:3, 7:2, 8:1, 10:1}`. The `10` is only Abaddon.
**Fix**: either raise `item_tier` on tiamat/asmodeus/abaddon to 15-20 and rely on the floor cap to still-max-out (needs a look at loot pools), or leave and accept the pool cap — but 10 as-is gives Abaddon L50 loot, which is worse than Fenrir's territory. Recommend `item_tier: 20` (effective_floor 100 = anything).

---

## P3 — UI-rot

### [P3] Every monster's `ingredient_id` points to a stale name — identify screen silently reports "Ingredient: none" for every corpse
**File**: data/monsters.json (525 of 527 entries)
**Issue**: The 2026-05-31 harvest redesign (see `food_system.py:1099` comment: "corpse no longer carries an ingredient_id") migrated cooking ingredients to `data/items/ingredient.json` keyed by `<monster_id>_prime` (e.g. `giant_rat_prime`). The `ingredient_id` field on monsters.json still holds the OLD names (`rat_meat`, `goblin_flesh`, `bone_shard`, `dragon_scale`, …). But `game_render.py:6759-6774` still reads `corpse.ingredient_id` at identify level ≥ 2 and calls `load_ingredient_for(ingredient_id)` — which returns `None` because the id isn't in `ingredient.json`. The fallback branch runs `mechanics.append(("Ingredient: none", ...))`, so the identify screen lies for every corpse.
**Evidence**: 525 monster entries reference ingredient ids like `rat_meat`, `goblin_flesh`, `dragon_scale`, `demon_heart`, `spider_silk`, etc.; `ingredient.json` contains none of these — its keys are all `<monster_id>_prime` (538 keys). `giant_rat.ingredient_id="rat_meat"` → `rat_meat` is not in ingredient.json → renderer falls to "Ingredient: none".
**Fix** (pick one):
1. Delete the `ingredient_id` field from all 525 monsters (canonical since 2026-05-31 says corpse doesn't carry one), then have `game_render.py:6759` derive `f"{monster_id}_prime"` from the corpse's monster kind and call `load_ingredient_for(...)` on that.
2. Global find/replace `ingredient_id: "<x>"` → `ingredient_id: "<monster_id>_prime"` in monsters.json (cheap, but keeps the dead-legacy field alive).
Cheaper immediate patch: in `game_render.py`, use `corpse.kind + "_prime"` instead of `corpse.ingredient_id`.

---

## P4 — nit

### [P4] cult_zealot — `resistances: ["shadow","pain"]`; "pain" is not a damage type the game emits
**File**: data/monsters.json (cult_zealot)
**Issue**: no attack in monsters.json uses `type: "pain"`, no spell/wand path in `src/` emits `damage_type="pain"`. `pain` in the resistance list is dead.
**Evidence**: attack-type histogram: `{physical:386, lightning:19, magic:118, poison:81, acid:10, drain:74, cold:42, necrotic:28, pierce:37, blunt:72, fire:59, slash:79, psionic:2, shadow:46, holy:4}` — no "pain".
**Fix**: drop `"pain"` from cult_zealot's resistances (or rename to a real type like `psychic`/`shadow`).

### [P4] tiamat / asmodeus — `weaknesses: [..., "divine"]` is a dead value
**File**: data/monsters.json (tiamat, asmodeus)
**Issue**: no weapon's `damage_types` includes `"divine"` (the theme is served by `holy` and by the `ignore_resistances` weapon flag). `divine` in monster weaknesses will never match.
**Evidence**: tiamat `weaknesses: ["holy","divine"]`, asmodeus `weaknesses: ["holy","divine"]`. Both already list `holy` — that's the working one.
**Fix**: drop the `"divine"` entry; `holy` already covers Sword-of-Michael damage.

### [P4] erlking / baba_yaga / wild_hunt_captain — `iron` in weaknesses is redundant
**File**: data/monsters.json (erlking, baba_yaga, wild_hunt_captain)
**Issue**: `combat.py:786` auto-adds `iron` to weaknesses for any monster with the `fey` tag. All three have `tags: ["fey"]`, so the JSON `iron` is redundant.
**Evidence**: `combat.py:786-788` "Legacy hardcoded fallbacks (kept for safety while the new data lands)". Harmless duplicate.
**Fix**: leave in (harmless) OR remove now that the data-driven material-effective-against system is live.

### [P4] baba_yaga / ravanas_arm / anansi — dead `attack_effects` field
**File**: data/monsters.json (baba_yaga, ravanas_arm, anansi)
**Issue**: the top-level `attack_effects` array is never consumed anywhere in `src/`. The real per-attack effects live inline on `attacks[].effect / effect_chance / effect_duration` (wired at `monster.py:715`). All three monsters already have those inline entries, so the extra `attack_effects` is duplicate/legacy.
**Evidence**: `grep -rn "attack_effects" src/` returns no matches (checked). All three monsters have `attacks[].effect` set correctly.
**Fix**: delete `attack_effects` from these three monsters.

### [P4] celestial_guardian — dead `mortal_weapon_floor` field
**File**: data/monsters.json (celestial_guardian)
**Issue**: `mortal_weapon_floor: true` — no consumer in `src/`. Presumably intended as "cannot be damaged by mundane weapons unless from a specific floor" but nothing reads it.
**Evidence**: `grep -rn "mortal_weapon_floor" src/` returns nothing.
**Fix**: either wire it up (a `_damage_multiplier` guard in `combat.py`) or delete the field.

### [P4] tiamat / asmodeus — `multi_attack_always: true` is redundant alongside `multi_attack_count < len(attacks)`
**File**: data/monsters.json (tiamat, asmodeus)
**Issue**: `monster.py:427-435` checks `_macnt > 0 and _macnt < len(self.attacks)` first — for tiamat mac=3 with 5 attacks, this branch wins and `multi_attack_always` is never consulted. Same for asmodeus (mac=2, 4 attacks).
**Evidence**: tiamat has `multi_attack_always: true, multi_attack_count: 3, len(attacks)=5`; asmodeus has `multi_attack_always: true, multi_attack_count: 2, len(attacks)=4`.
**Fix**: drop `multi_attack_always` from both — the count field is doing the work. (If the intent was "fire all attacks at rage phase", that's what `enraged_multi_attack_count` is for, which is already set to 5/4 respectively.)

### [P4] heavenly_angel — empty `attacks: []` is a special case, worth a comment
**File**: data/monsters.json (heavenly_angel)
**Issue**: `attacks: []` is the ONLY monster with zero attacks. It's by design (seek_locust AI, `is_allied: true`, never attacks the player). But `Monster.attack()` at monster.py:345 has a "floating eye" fallback (gaze paralyze) that fires when `attacks` is empty — if any code path ever wires the angel adjacent to the player, that gaze fires. Low real-world risk because `is_allied` gates it out, but a code comment or an explicit inert `attacks: [{"name":"none","damage":"0","type":"physical"}]` would remove the ambiguity.
**Evidence**: only heavenly_angel matches `attacks: []` (all 526 others have ≥1). See monster.py:345 fallback.
**Fix**: add a one-line comment in the JSON (`"_comment": "empty attacks by design; is_allied gates the fallback"`) or an inert attack entry.

### [P4] Native L91-99 monster pool is thin (content gap)
**File**: data/monsters.json (L91-99 band)
**Issue**: only 10 monsters have `min_level` in 91-99: 2 endgame elites (apocalypse_herald, wormwood_blight), 1 more mid-tier (iron_horseman), 1 nidhoggr fragment, 2 seal demons, and the abaddon fight ensemble (abaddon_destroyer, abyssal_locust, heavenly_angel, asmodeus). The regular spawn pool for these floors leans hard on L81-90 residuals. CURVE.md §8 explicitly calls this out: "≥10 distinct active species per band; add 4-5 new Abaddon-elite species at L91-99."
**Evidence**: `sum(1 for m in mon.values() if 91 <= m.get('min_level',1) <= 99) == 10`.
**Fix**: content addition, not a data bug. Track under CURVE.md Tier-C content roadmap.

### [P4] Ranged AI monsters with only one attack
**File**: data/monsters.json (dark_elf, storm_elemental, orc_shaman, skeletal_archer, skeleton_archer, will_o_wisp, will_o_wisp_lesser, myconid_worker)
**Issue**: `ai_pattern: "ranged"` but only 1 attack in `attacks[]`. `monster.py:450` special-cases "at distance with ≥2 attacks, pick a ranged one"; with only 1 attack, that fallback is a no-op. The ranged AI still positions correctly (they maintain distance, reposition, shoot), but they use the same single attack for melee-adjacent as for distance. Design smell, not a bug.
**Evidence**: `[mid for mid,m in mon.items() if m.get('ai_pattern')=='ranged' and len(m.get('attacks',[])) < 2]` — 8 matches.
**Fix**: consider adding a weak melee shove attack to each, or acknowledge single-attack ranged is fine.

### [P4] Duplicate `regeneration` on other regen monsters is fine; note the two typo cases (already P1)
**File**: n/a (informational)
**Issue**: only 2 monsters had the `regen` field-name typo (baba_yaga, green_knight — see P1). Every other regenerating monster (abaddon_destroyer 15, tiamat 15, asmodeus 18, surtur 12, ymir_last_spawn 10, mythic_hydra 5, flesh_colossus 6) uses the correct `regeneration` field.
**Evidence**: field name histogram check.
**Fix**: none — informational, confirming the P1 fix is scoped to 2 entries.

---

## Positive findings (validated clean, worth noting)

- All 8 `treasure.ammo_drop.ammo_id` references resolve in `data/items/ammo.json`.
- All 27 valid `boss_scroll_id` references (of 29 total) resolve in `data/items/scroll.json` (only tiamat and asmodeus break — see P1).
- All 12 `summon_kind` references (single or list) resolve to real monsters in `monsters.json`.
- Every `ai_pattern` in use (aggressive 332, ranged 101, sessile 29, ambush 23, hit_and_run 17, summoner 8, healer 6, cowardly 3, dancer 2, mimic 2, fenrir_rage 1, abaddon 1, seek_locust 1, grid_bug 1) is handled by `monster.py`.
- All 17 attack `effect` names in use (slowed, confused, poisoned, paralyzed, blinded, burning, weakened, stunned, bleeding, frozen, feared, diseased, sleeping, cursed, hallucinating, silenced, teleportitis) are defined in `src/status_effects.py`.
- HP band fit is broadly on-curve per `tools/balance/rebase_monster_hp_report.md`. The one non-boss HP outlier caught (`gnoll_archer` L11 HP avg 11) is a low-HP ranged skirmisher — small but arguably intentional; not flagged.
- Colors, symbols, footprints, dice strings all parse cleanly.
- 5 multi-tile bosses (`fafnir_dragon`, `tiamat`, `surtur`, `ymir_last_spawn`, `hrungnirs_ghost`) all correctly use `footprint: [2, 2]`.
- All 7 seal demons drop the correct `seal_of_*` artifact (7/7 match against artifact.json).
- Alert / perception / pack / flank / charge / phase-blink / pull / drain-heals / revive-once wiring all check out — every JSON flag has a live consumer.
