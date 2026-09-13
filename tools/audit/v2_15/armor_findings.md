# v2.15.0 Armor / Shield / Accessory / Artifact / Ammo / Potion audit

**Date:** 2026-09-12
**Scope:** `data/items/{armor,shield,accessory,artifact,ammo,potion}.json` + item classes in `src/items.py` + wiring in `src/armor_procs.py`, `src/chain_passives.py`, `src/chain_equip.py`
**Method:** For every declared JSON field or `tier_bonuses` passive, grep for a real consumer in `src/`; ignore reads inside the definer file itself. Sanity-check ac_bonus / enchant_bonus outliers by tier + slot. Confirm every potion effect has a handler. Confirm every artifact has an on_use / on_equip / on_carry path (either by field lookup or hardcoded id-lookup).

## Severity summary

| Sev | Count | Notes |
|-----|-------|-------|
| **P0** | 0 | All 6 JSON files load without KeyError; every subclass instantiates cleanly. |
| **P1** | 8 | Dead procs / dead flags — advertised power silent. |
| **P2** | 2 | Two flagship legendary artifacts (Pandora's Box, Aladdin's Lamp) documented as dispatcher-pending and quarantined via `min_level: 9999` — no crash, but two lore-heavy artifacts remain inert. |
| **P3** | 1 | Stale in-menu description string ("for 4 turns" for Hand of Glory whose real paralyze_duration is 10). |
| **P4** | 4 | Cosmetic redundancy — a working id-lookup consumer plus a duplicate JSON flag that no code reads. |

Everything else is clean: potion effects (36) all handled in `food_system.drink_potion`; ammo `ammo_type` values match all `requires_ammo` weapon values (sling's "stone" is deliberately `infinite_ammo: true` with no data entry); ac_bonus curve by tier is disciplined (T1 body ≤ 2, T2 body ≤ 3, T3 body ≤ 5, T4 body cap 8 hit only by Panoply, T5 body cap 8 hit only by Green Knight's Plate); enchant_bonus never exceeds the per-slot ENCHANT_CAP; every armor `on_equip_status` / `onEquipStatus` value is looked up correctly by main + player equip flows; carry_bonus and save_bonus are consumed by Player.refresh_carry_bonuses and Player.save_bonus_for.

## P0 — crash on equip / drink / pickup

_None found._

## P1 — dead proc / dead flag (mechanic never fires)

### 1.1 `death_save_bonus` chain-passive is unread
- **Wrapper `get_death_save_bonus()`** exists in `src/chain_passives.py:215` but has **zero call sites** across `src/`. Only match outside chain_passives.py is a comment in `src/game_combat.py:2113` describing intended behavior that was never wired up.
- **Affected items:** any accessory whose T3–T5 `tier_bonuses` include `passive_death_save_bonus` (Tyet of Isis, etc.). Tooltip promises "+N to death-save d20 roll"; the roll never sees the bonus.
- **Fix outline:** in `src/game_combat.py` where the death-save d20 is rolled (near the `_death_save_used` block ~L2116, and again near the `maid_does_not_fall` block ~L2138), add `+ get_death_save_bonus(self.player)` to the DC comparison.

### 1.2 Armor proc `quest_humility` (Sandals of Perseus) — never read
- Loaded on `Armor` at `src/items.py:691`, no `player_has_armor_proc(player, 'quest_humility')` anywhere.
- Sandals of Perseus is a T1 legendary (peak_floor 14) that lore-promises "quest humility" — currently only its baseline AC 1 and 0.15 pierce resist fire.
- **Fix outline:** decide the mechanic (e.g. −20% XP-to-next-level while equipped, or +1 karma per boss kill) and hook it in `main.py`.

### 1.3 Armor proc `descend_stairs_no_turn` (Greaves of Hermes) — never read
- Loaded on `Armor` at `src/items.py:706`, no consumer. The Boots of Seven Leagues has its own `seven_league_step` which IS consumed (game_menus / hud_context give it a menu entry), but the greaves' analogous flag is silent.
- Greaves of Hermes is min_level 50 tier-3 with AC 3 — lore says "each step covers ground that would take mortals three" but the stair-descent free-turn never fires.
- **Fix outline:** in `main.py` at the stair-descent turn cost (grep `descend`), check `player_has_armor_proc(player, 'descend_stairs_no_turn')` and short-circuit the turn cost.

### 1.4 Shield `block_chance` — declared on 27 shields, unread
- Every legendary shield in the "hoplon / aspis / kite / buckler / targe / tower" family declares `block_chance` (0.05–0.22): Mycenaean Tower, Pelte, Sumerian Buckler, Khopesh-Breaker, Hittite, Assyrian Pavise, Spartan Aspis of Leonidas, Etruscan, Scutum of the Legio, Macedonian Aspis, Celtic Oval, Germanic Kriegsschild, Sarmatian, Battersea, Saxon, Lendings of Beowulf, Sigurd's Handshield, Carolingian Kite, Heater of the Black Prince, Mameluke, O-Tate, Skidbladnir, Smoking Mirror, Vajra Paramita, Horse-Armor of the Norns, Scarab of Apophis-Binding, Yama's Dharma-Watch.
- `grep -rEn '\bblock_chance\b' src/ tests/ tools/` — **no consumers anywhere**. The field is loaded nowhere (Shield.__init__ doesn't even read it into `self`).
- Every one of these shields differentiates itself in JSON by its block chance, and the differentiation is invisible in play.
- **Fix outline:** load `self.block_chance` in `Shield.__init__`, then in `src/game_combat.py` melee-hit resolution roll a d100 against `player.shield.block_chance` before the AC roll (or fold it into the AC roll as a first-pass hit chance).

### 1.5 Shield `projectile_block` — declared on 8 shields, unread
- Assyrian Siege-Pavise (0.30), Scutum of the Legio (0.25), Carolingian Kite (0.40), O-Tate of the Samurai (0.50), Yama's Dharma-Watch (0.50) — all pointedly designed as "the one that stops arrows." Field is nowhere read.
- **Fix outline:** in `src/combat.py` ranged-attack resolution, before applying damage, roll against `getattr(player.shield, 'projectile_block', 0)` and negate on success.

### 1.6 Shield `spell_block_chance` — declared on 3 shields, unread
- Battersea Votive (0.15), Heater of the Black Prince (0.20), Vajra Paramita (0.30) — the "anti-magic" shields.
- **Fix outline:** in `src/spells.py` / `src/monster.py` cast-vs-player path, roll against `player.shield.spell_block_chance` before applying spell damage.

### 1.7 Shield `knockback_on_block` — declared on 3 shields, unread
- Saxon Round Shield (0.15), Mameluke Targe (0.20), Horse-Armor of the Norns (0.30). Field never loaded, never checked.
- **Fix outline:** couple with 1.4 — when `block_chance` succeeds, roll `knockback_on_block` and apply a 1-tile push using existing knockback code path.

### 1.8 Accessory `paralyze_charges` — redundant / dead
- Hand of Glory JSON declares both `paralyze_charges: 3` AND `charges: 3`/`max_charges: 3`. Only the latter is consumed (via `use_charged: true` in `game_menus.py:1180-1197`). `paralyze_charges` is never loaded onto the Accessory class and never queried. Not harmful (the mechanic still works via `charges`), but the JSON field is misleading noise that suggests two independent counters.

## P2 — flagship artifact dispatchers still pending

### 2.1 `pandoras_box` chaos_table dispatcher not wired
- 20-entry `chaos_table` (Hesiod's evils + Hope) in JSON.
- No consumer for `use_quiz_subject`, `chaos_table`, or `consumed_on_use` fields anywhere in `src/`.
- `_disabled_reason: "chaos_table dispatcher pending — vision audit 2026-05-30"` in JSON is honest.
- `min_level: 9999` keeps it out of the natural spawn pool, so it's safely inert. Not a shipping blocker for v2.15.0, but a major named artifact remains unimplemented.

### 2.2 `aladdins_lamp` djinn_wish_menu dispatcher not wired
- 3-category wish tree + 5-entry fallback table in JSON.
- No consumer for `wish_categories`, `wish_menu`, `wish_fallback_effects`, `djinn_wish_menu`.
- Same `_disabled_reason` note; same `min_level: 9999` quarantine.

## P3 — text mismatch

### 3.1 Hand of Glory power-menu description says "4 turns" but actual duration is 10
- `src/game_menus.py:1188` hardcodes `_desc = 'Paralyze one visible enemy for 4 turns. Consumes 1 charge.'`
- The actual dispatch at `src/game_menus.py:1815-1823` reads `paralyze_duration` (10 in JSON).
- Fix: `_desc = f'Paralyze one visible enemy for {getattr(_acc, "paralyze_duration", 4)} turns. Consumes 1 charge.'`

## P4 — cosmetic redundancy (mechanic works via id-lookup, duplicate JSON flag ignored)

### 4.1 `bovine_fury` on Cow King's Horns
- The horns' free chain-hit works via generic `chain_bonus: 1` (consumed in `src/combat.py:815-818`). `bovine_fury: true` in the JSON is redundant metadata — nothing reads it.

### 4.2 `stair_reveal` on Palladium
- Palladium's stair-reveal is triggered by `getattr(i, 'id', '') == 'palladium'` in `src/main.py:2078`. The `stair_reveal: true` flag is documentary only.

### 4.3 `quiz_reroll` on Tablet of Destinies
- Same shape: `_has_tablet_of_destinies()` id-check in `src/game_combat.py:1556, 1623` drives the mechanic; the `quiz_reroll: true` flag on the JSON is unread.

### 4.4 `vidar_instant_kill_fenrir` nested in special_properties on Vidar's Sandal
- Instant-kill fires from `getattr(i, 'id', '') == 'vidars_sandal'` in `src/game_combat.py:1640`. The nested boolean under `special_properties` is documentation only.

_Note: P4 items are safe as-is — the mechanic behaves correctly. They are only listed because the JSON reads as if the boolean drives behavior, which will mislead the next code-touch (someone will disable the flag expecting it to disable the mechanic, and be surprised)._

## Clean areas — no findings

- **Every armor proc from engine wave 5** (`weave_and_unweave`, `phalanx_recovery`, `water_tile_*`, `unskinnable`, `prophets_passing`, `webbed_strike`, `forest_hearing`, `story_thread`, `monkey_king_dodge`, `grendel_grip`, `gold_offering`, `bond_check`, `dodge_first_arrow_per_floor`, `their_own_methods`, `royal_burial`, `riastrad_echo`, `cannae_encirclement`, `last_stand_bonus`, `et_tu_charge`, `guerrilla_terrain`, `disguise_at_camp`, `boundary_guardian`, `wild_friend`, `gita_focus`, `seven_league_step`, `tremor_sense`, `peace_at_the_forge`, `amazon_charge`, `caustic_blood`, `divine_smithing`, `maid_does_not_fall`, `atlantean_resonance`, `descent_haste`, `ringing_intimidation`, `purity`, `thors_step`) has a real consumer. (`divine_smithing` is consumed in `src/items.py:207` `effective_enchant_cap`, which is why grep on `src/` outside `items.py` returned no matches — legitimate cross-slot cap read.)
- **Every accessory tier_bonuses passive** (`aesir_young`, `anti_being`, `atalantas_choice`, `attack_chain_cap_bonus`, `beautiful_ruin`, `detect_magic`, `free_move_every_10`, `grammar_chain_cap_bonus`, `hunger_slow`, `life_save_resets_per_floor`, `one_thousand_and_one`, `pacify_demon_chance`, `reassembly`, `scroll_save_on_fail`, `solomonic_key`, `spell_crit`, `spell_damage_bonus`, `spellbook_chain_bonus`, `suryas_gift`, `three_apples`, `three_oclock`, `weaken_summoned`) has a real consumer. `mp_bonus` / `max_mp_bonus` are consumed via direct mutation in `src/chain_equip.py:143-148` at equip-time — no lookup helper needed. `spell_damage_bonus` / `spell_crit` flow through `apply_spell_damage_passives`, called by `src/game_magic.py:1298`.
- **Every armor tier_bonuses passive** (Aegishjalmr's `fafnirs_glare`/`no_man_dares`, Helm of Hades' `stealth_in_dark`/`invisible_to_undead`/`phase_step_once_per_floor`/`unseen_when_still`, Cloak of the Morrigan's `raven_scout`/`raven_scout_extended`/`death_omen_mark`, Robe of the Magus' `free_cast_once_per_floor`/`double_cast_at_peak_tier`, Cloak of Odin's `identify_one_per_floor_free`/`huginn_muninn`/`wisdom_at_a_price`, Dragon-Sewn Mail's `back_attack_weakness`/`dragon_blood_bath`, Green Knight's `second_beheading_returns`, Aragorn helm's `command_undead`/`paths_of_the_dead`, Solomon robes' `demon_command_one_per_floor`/`seventy_two_seals`, Ragnarök armor's `first_hit_absorb`/`doom_of_the_gods`, Brahma crown's `four_faces_360_fov`) has a real consumer.
- **Every shield tier_bonuses passive** (Aegis of Athena's `aura_of_awe`, Greater Aegis' `gorgoneion_petrify_on_hit`, Smoking Mirror's `spell_reflect`/`mirror_of_souls`) has a real consumer.
- **Every non-tier-bonus accessory field** (`passive_regen`/`passive_regen_interval` for Eye of Horus, `gold_multiplier` for Draupnir, `surrounded_ac_bonus` for Torc of Boudicca, `pacify_chance` for Seal of Solomon, `death_save` for Jade Cicada, `resurrect_on_death` for Ankh of Isis, `tears_of_freya` for Brisingamen, `identify_timer_bonus` for Ring of Pythia, `auto_invisible_at_low_hp` for Ring of Eluned, `protected_when_surrounded` for Ring of Hypatia, `gyges_invisible_attack_karma` for Ring of Gyges, `monster_tag_chain_bonus` for Dragonslayer Ring, `rotating_subject_chain_cap` for Lugh/Hamsa) has a real consumer.
- **Every armor material referenced** in armor.json resolves to either `data/materials/armor/<mat>.json` (adamantine, mithril, silk, leather, hide, dragon-scale…) or is a flavor string on a unique (`legendary`, `divine bronze`, `enchanted plate`, `dwarf-forged iron`, `rubber` for Duck of Doom, etc.) — uniques set ac_bonus directly so no material lookup is needed.
- **Every potion effect** (heal, extra_heal, full_heal, restore_sp, cure_poison, cure_disease, cure_all, haste, invisibility, regeneration, heroism, brilliance_mp, levitation, restore_str, gain_level, confusion, blindness, poison, paralysis, hallucination, sleep, weakness, slow, teleport, drain_str/con/wis/int, sickness, fumbling, fear, fire_resist/cold_resist/shock_resist, restore_mp, fafnirs_blood) has an `elif effect ==` branch in `src/food_system.drink_potion` (~L777–1080). Unique-drop potions (Soma → full_heal, Water of Lethe → cure_all, Elixir of Gilgamesh → gain_level) reuse standard effect keys; fafnirs_blood has a dedicated branch.
- **Every ammo `ammo_type`** (arrow, bolt, shell) has a matching weapon `requires_ammo`. `stone` weapons (sling only) are `infinite_ammo: true` and don't need a data entry.
- **ac_bonus + enchant_bonus bounds:** T4/T5 body ceiling of 8 is hit by 2 items only (Panoply of Hephaestus, Green Knight's Plate), both intended. No armor breaches `ENCHANT_CAP` at spawn — every unique's `max_enchant` is ≤ 3 and slot ENCHANT_CAP for body is 3.
- **`boss_immune` on CC effects:** `src/status_effects.py` and `src/monster.py` respect `boss_immune` via the `apply_debuff_with_save` path; not re-audited here (out of scope but confirmed the wiring still exists).
