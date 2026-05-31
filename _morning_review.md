# Overnight Run — Morning Review (2026-05-30 → 2026-05-31)

User went to bed asking for: (1) ship every remaining deferred proc, (2) bug bash with audits, (3) comprehensive balance audit with LLM judges, (4) vision audit.

All four phases ran. **6 overnight commits**, **1107 tests passing** (up from 959 at start of session).

---

## Phase 1 — Built the remaining systems (no half-baked)

Engine wave 6 (commit `35887d0`) shipped the 12+ deferrals from the previous summary. New architecture:

- **Rest sites** at altar tiles. Standing on ALTAR triggers the rest-cycle bonuses on `phalanx_recovery` (Linothorax, +N HP regen/turn), `peace_at_the_forge` (Achilles vambraces, +N MP+SP/turn), `disguise_at_camp` (Mulan, full HP/MP/SP restore on tile-entry, re-fires per altar visit).
- **Charge-on-accessory** infrastructure. `Accessory` now carries `use_charged` / `charges` / `max_charges`. Equipped charged accessories appear in the power menu (V key). Lyre of Orpheus → 3-charge charm; Hand of Glory → 3-charge paralyze; generic future accessories default to 5-turn sleep.
- **Rotating-subject** chain bonus. Per-floor, equipped Torque of Lugh or Hamsa Hand picks a random subject from their pool; that subject's quizzes get +3s timer this floor. (Lugh: 6 subjects. Hamsa: 3 faiths — theology/history/grammar.)
- **Activated abilities**. Seven-League Step (Boots) and Gilgamesh's Bribe (Helm) both appear in the power menu when equipped and unused. Dash strides 7 tiles in facing direction. Bribe takes the nearest visible non-boss INT≥5 monster, pays 1d100 gold, paralyzes 1t.
- **Small per-item procs** all wired: `atlantean_resonance` (Orichalcum, 30-turn shielded), `royal_burial` (Pharaoh kilt — one bones item survives uncursed on death), `amazon_charge` (Hippolyta — 3+ straight-line steps arms +50% next melee), `purity` (Galahad — newly-equipped cursed items become uncursed), `ring_of_pythia` (+2s on philosophy), `ring_of_eluned` (<25% HP → invisible 10t, 1/floor), `ring_of_hypatia` (3+ surrounded → shielded 3t, 1/floor), `ring_of_gyges` (attacking NPC while invisible → -2 karma), `dragonslayer_ring` (dragon-tag damage bonus).

**Genuinely deferred / not implemented** (no clean engine fit):
- `bovine_fury` chain reroll — would need quiz_engine mid-stream interrupt
- `quest_humility` NPC encounter weighting — no encounter weight registry exists
- `descend_stairs_no_turn` — verified the engine already costs 0 turns on descent; flag is a no-op confirmation

34 new tests (test_engine_wave6_remaining.py) cover field loading + hook-site wiring + behavior smoke.

---

## Phase 2 — Bug bash (6 parallel opus agents)

Each agent surveyed a specific surface. Real bugs found and fixed (commit `1eb6fe1`):

| # | File:Line | Bug | Fix |
|---|-----------|-----|-----|
| 1 | game_menus.py power menu | Seven-League/Gold-Offering showed in menu after spent; could re-fire | Don't append to menu when `_used` flag is true |
| 2 | game_menus.py warning-exits | Returning False burned a turn on facing=0 or already-spent warnings | Return True on warnings (defer turn) |
| 3 | combat.py cannae_encirclement | Fired on ranged shots + counted target monster in adjacency (inflated +1) | Gate `if not ammo:` + skip target in `_adj` count |
| 4 | combat.py gyges karma | Drained karma on missed/0-damage swings while invisible | Gate `if actual > 0:` |
| 5 | main.py amazon_charge | `_amazon_charge_armed` not reset between floors — free +50% melee carried into next floor | Reset both `_amazon_charge_armed` and `_straight_line_steps` in `_change_level` |
| 6 | main.py rotating-subject | Floor-entry message fired even when no rotating accessory equipped (and re-fired every floor when equipped) | Only message when subject actually changes |
| 7 | player.py prophets_passing | Re-equip after a failed unequip would double-stack the +3 max MP | Guard `if _prophets_mp_grant == 0:` before granting |

**Cross-cutting notes** (verified OK):
- All `from armor_procs import` sites use try/except ImportError — no missing-module risk
- Save/load: every new player attribute is read via `getattr(player, '...', default)` — pre-wave-5/6 saves load safely
- Status registrations (`slowed`, `shielded`, `protected`) all present
- The two reset functions (`chain_passives.reset_per_floor_charges` and `armor_procs.reset_per_floor_charges`) operate on separate attrs and coexist cleanly

---

## Phase 3 — Balance audit (9 parallel opus agents)

### Weapons — uniques
Identified ~15 under-curve T4/T5 named swords. Bumped:
- fragarach/joyeuse/skofnung/harpe/brisingr: bd 13 → 15
- durendal/shamshir_e_zomorrodnegar: bd 17 → 20
- excalibur/spear_of_longinus/amenonuhoko: bd 22 → 26
- gae_bulg/zulfiqar/parashu: bd 14 → 18
- green_chapel_axe/net_of_hephaestus: bd 7 → 10

`achilles_spear` was flagged peak_floor=8 contradicts FSW (20-70), but it's a starter hero item — `test_achilles_spear_is_tier_1_now` pins it; left as-is.

### Weapons — commons
Material curve is broadly clean. Three real issues flagged but **deferred for morning review**:
- Slings systematically half-power (damage_modifier=0.6 across all variants)
- stormiron + meteoric_iron leap one or two material slots ahead of their pf
- primordial_stone ≈ void_touched at endgame (near-duplicates)

### Armor — uniques (60 items)
**Biggest single fix**: 5 chain-equip items were pre-granting their T5 climactic effect at T1 via top-level `onEquipStatus` / `first_hit_absorb`, defeating the entire escalator design. Stripped:
- dragon_mail_of_sigurd onEquipStatus (fire resist)
- winged_sandals_of_hermes onEquipStatus (hasted)
- helm_of_aragorn onEquipStatus (blessed)
- robes_of_solomon onEquipStatus (blessed)
- armor_of_ragnarok first_hit_absorb (now T4-only via passive)

### Armor — commons (45 materials)
Broadly coherent. Fixed: 4 material files duplicated 'fire' in both `weaknesses` and `vulnerabilities` (rawhide, cured/boiled_leather, treant_heart). Stripped from `vulnerabilities`.

**Deferred** (intentional but noted): rawhide vs leather redundancy at T1; vestigial `damage_mult` field in 15 armor materials.

### Shields (36 uniques)
- aegis_of_athena tier 1→4 (T1-tagged but T5-engineered with escalator)
- lionheart_shield ac_bonus 4→2 (AC 4 exceeds T1 cap)
- vajra_paramita ac_bonus 4→5 (bottom of T5; underdelivered)

### Accessories (199 items)
6 mass-production T4/T5 stat rings/amulets had equip_threshold=2 (template bug). Fixes:
- amulet_titan_constitution + amulet_archmage_intellect: threshold 2→4
- ring_protection_adamantine + philosophers_ring: threshold 2→3
- ring_strength_dragonbone/constitution_diamond/intellect_prismatic_deep: amount 4→3 + threshold 2→3
- shadow_walker_ring: was bare poison_resist; added DEX+3
- torque_of_lugh: rotating pool 10 subjects → 6 (10 was too broad to bite)
- ring_of_iron_grip: quiz_tier 4→2 (starter-grade pity)

### Consumables (wand/scroll/spellbook/potion/food)
- scroll_of_great_power: quiz_threshold 4→5 (was under-costed for permanent +1 to all 6 stats)
- wand_of_inferno: 5d6 → 4d8 (parity with wand_of_storm)
- wand_of_aging: added STR drain mechanic (was strictly worse than wand_of_disease)

**Deferred for morning**: spellbook_chain_lightning (T3) vs spellbook_chain_lightning_t4 (T4) point to the same spell_id — T4 is strictly worse per MP. Need a distinct spell or chain_max bump.

### Monsters
Curve smooth in HP/damage shape (TTK 1.2 → 1.9 → 3.8 → 6.6 turns across early/mid/deep/end), but **massive content reskinning**:
- F44 mass-clone tier: 24 monsters share `8d10+26 HP / THAC0 2 / 2d8+1d8 damage`
- F31 hydra/scylla/titanspawn/star_spawn/dread_wraith — 5 renamed identicals
- F60/F62/F92-94 clone clusters
- F31-F40 and F81-F90 are sparse bands (boring stretches)

**Critical numbers issue**: `ancient_dragon` at F90 has 5 atks/turn + 100 mean dmg + 148 burst — possible 1-turn TPK against ~189-HP player. Defer fix — needs a designer pass to either (a) buff player or (b) cap dragon attack count.

---

## Phase 4 — Vision audit + this report

Vision agent still running at write-time (will append findings below if completes before you wake).

---

## What I deliberately DIDN'T touch (judgment calls held for you)

1. **Slings being half-power across the board.** Looks intentional — design might want slings as throwback weapons. Audit recommended `damage_modifier 0.6 → 0.75`. Holding.
2. **Ancient_dragon 5-attacks 1-turn TPK.** Designer-level decision: cap dragon attacks, buff player, or accept it as "endgame screwjob."
3. **Monster content reskinning at F44 etc.** Adding distinctive stats to 30+ clones is a content design pass, not a balance fix.
4. **spellbook_chain_lightning T3/T4 dedup.** Either change the T4 spell_id or buff T4 chain_max — both are design decisions.
5. **rawhide vs leather T1 redundancy.** Either delete `leather.json` or bump rawhide peak_floor. Cosmetic but yours to call.
6. **Doc tweaks** (vision audit). Agent's findings will appear below.

---

## Tests + state

- Total tests: **1107** (was 959 at start of session)
- All passing
- New test files: `test_engine_wave5_armor_procs.py` (58 tests), `test_engine_wave5_accessory_passives.py` (11), `test_json_wave3_armor_acc.py` (45), `test_engine_wave6_remaining.py` (34)
- 6 commits this overnight session:
  - d745b05 quick-fix wave
  - 0ef4aa2 engine wave 5 (30+ armor procs)
  - 6e7e640 step C accessory verification
  - 0cf56fb json wave 3
  - 35887d0 engine wave 6 (rest sites, charges, rotating subject, dash, bribe, small procs)
  - 1eb6fe1 bug-bash + balance fixes

---

## Phase 4 results — Vision audit

Agent crawled `proposals/legendary_uniques/` + `proposals/v2_audit/` + `proposals/loot_and_dungeon_audit.md` and cross-referenced against current code.

### What the proposals promised AND is now shipped
- Chain-equip infrastructure (24 items) — all loading cleanly
- ~30 of the originally-deferred `passive_<flag>` keys now wired (engine waves 5+6)
- Engine waves 1–6 wired the bulk of weapon procs (cannot_miss, chain_lightning, return_to_hand_ward, etc.)
- ~30 flat-armor procs from `armor_shields.md` (phalanx_bonus, last_stand_bonus, riastrad_echo, webbed_strike, grendel_grip, disguise_at_camp, peace_at_the_forge, etc.)
- v2_audit/07_systems crit-fix A: 10 silent-no-op spells now have handlers
- v2_audit/07_systems status orphans (parry_armed, see_invisible) registered
- v2_audit/11_edge_cases: phasing-in-wall soft-lock fix + ring-slot-full guard
- loot_and_dungeon_audit loot leak fix + special-room frequency raised + plant ingredient spawn
- v2_audit/01_weapons adamantine drift fixed (canonical baseDamage shipped)

### Biggest single remaining vision gap
**`magic_accessories.md` USE-action dispatchers** (CRITICAL — known from WAKEUP.md:55):
- **Pandora's Box** `chaos_table` (20 entries) — JSON-only, zero src/ readers
- **Aladdin's Lamp** `wish_categories` / `wish_menu` / `wish_fallback_effects` — JSON-only, zero src/ readers  
- **Wand of Wonder legendary** `wonder_tables` (5 escalating tables) — JSON-only, zero src/ readers
- **Hand of Glory** `expended_curse` + `passive_silent_walk` + `passive_dark_vision` still deferred (paralyze_charges activation now ships via power menu, engine wave 6)

These are the three rich-table chaos/wish/wonder items. They look right in inventory, identify works, but **using them** does nothing. This is the highest-leverage single remaining design item.

### Weapon procs still deferred (from `weapons.md`)
- `terrain_buff_on_finisher` (Heracles' Olive-Club)
- `throwable_weapon_proc` (Hector's Javelin — engine has separate `_is_throwable_weapon` but not the per-combat consume/retrieve)
- `spawn_giant_on_male_humanoid_kill` (Cronus's Scythe)
- `summon_on_demon_kill_alternating` (Vel of Murugan / Shamshir / Cadmus — partial)
- `chain_no_reset_on_tagged_kill` (Parashu)
- `resurrect_pet_proc` (Mwindo's Conga-Scepter)
- `damoclean_counter_auto_kill` (Sword of Damocles — partial: counter resets only)

### Real conflicts found
1. **Sword of Michael dual-schema**: weapon.json:4697–4703 ships BOTH `chainMultipliers` (9-entry legacy) AND `chain_multipliers` (5-entry new-style). items.py:154 reads camelCase first, so legacy wins — but the snake_case array is dead. **Same dual-field shape exists on every weapon** (maxChainLength vs max_chain_length, baseDamage vs base_damage). Schema migration was never finished. Recommend stripping the snake_case duplicate fields once a migration test proves the camelCase paths are the truth.
2. **Brisingamen "Tears of Freya"**: proposal says gold drips on the floor each turn. JSON entry has no `tears_of_freya` flag; zero src/ readers for `gold_when_bleed` / `low_hp_gold`. Either ship the flag + handler OR rewrite the proc text to match the WIS+3+passive-regen that actually ships.
3. **v2_audit/01_weapons adamantine drift table** reports "22 uniques at 0.71×" — the rebuild ran and canonical values shipped, doc still says "drift unresolved". **Marked RESOLVED in `_morning_review.md` and reflected in WAKEUP.md.**

### Doc lines I updated inline (this overnight)
- `proposals/legendary_uniques/WAKEUP.md` known-followup #1 — marked engine waves 5/6 sweep as shipping ~30 of 60 passive flags; explicitly listed which ones
- `proposals/legendary_uniques/WAKEUP.md` known-followup #4 — Hand of Glory marked PARTIALLY SHIPPED (paralyze charges via power menu wired; expended_curse still deferred)
- `proposals/v2_audit/07_systems.md` — added 2026-05-30 status note at top marking §A spell-handlers and §C status-orphans as RESOLVED, §B mastery-kinds as PARTIALLY RESOLVED

### Doc tweaks held for your review
1. **`magic_accessories.md`** should get "DATA-ONLY — dispatcher pending" banners on the 4 new uniques (Hand of Glory, Pandora, Aladdin, Wand of Wonder Legendary). Vision agent suggests this is the single biggest remaining gap.
2. **`legendary_uniques/weapons.md`** should mark which procs are wired vs deferred per-entry. Engine waves 1–6 give a clean mapping.
3. **`loot_and_dungeon_audit.md:144–149`** open questions are a year stale — close them.
4. **A new top-level `STATUS.md`** (or amend WAKEUP.md) would help orient future-you on what's done vs deferred.

These four are judgment calls (which mechanic to ship vs which to remove from spec), so left for morning review.

---

## Bottom line

- Phase 1 shipped end-to-end (no half-baked).
- Phase 2 caught 7 real bugs; all fixed.
- Phase 3 balance audit applied ~40 JSON deltas across weapons/armor/shields/accessories/consumables.
- Phase 4 vision audit found the chaos/wish/wonder dispatcher gap as the biggest unstarted item.

**The biggest call you have to make in the morning**: do you want me to build the chaos/wish/wonder dispatchers? It's a substantial system (effect dispatch tables + RNG + 50-entry chaos table handling), but well-scoped — could be the next overnight project.

Recommended order if you say "go":
1. Build chaos/wish/wonder dispatcher infrastructure (Pandora's Box first since it's the simplest table)
2. Fill the remaining 7 weapon deferrals from `weapons.md`
3. Strip dead schema duplicates (snake_case vs camelCase migration cleanup)
4. Address the monster content reskinning at F31/F44/F60/F92 (distinct stat blocks)
