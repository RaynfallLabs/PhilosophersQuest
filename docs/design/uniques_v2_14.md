# Unique Weapon Rebuild — v2.14.0

**Status:** Design agreed 2026-09-11. Applied to `data/items/weapon.json`.
Companion doc to `chain_combat_v2.md` and `weapon_specials_v2_14.md`.

## The problem

96 uniques were tuned before v2.14.0 and now sit in an awkward spot:

- Their `chain_multipliers` arrays cap around 2.0× at chain 5, so under the new polynomial baseline (`n^1.15` → 6.5× at chain 5) they land **under** a tier-matched common. A T5 unique 2h warhammer at base 42 × 2.0 array = 84 dmg at chain 5, vs a tier-matched adamantine common 2h warhammer at base 19 × polynomial 6.5 = 124 dmg. **Uniques currently feel weaker than commons.**
- Many uniques carried `critMultiplier` fields that stopped meaning anything when crit was retired.
- Many uniques carried `class_mechanic` values (backstab, cleave_at_max, stun_at_max, defensive_parry, master_strike, quick_riposte, armor_pierce_at_max, bleed_at_max) that are now the **class chain-special ladder's job**. Leaving them in double-fires the effect.

## The plan (this doc)

1. **Every unique opts into the polynomial** — `chain_exponent: 1.15` set on all 96.
2. **`base_damage` rebased** so uniques land at ~1.5× tier-matched common (30-70% above common per the design principle).
3. **Class-mechanic redundancy retired** — the eight class-covered mechanics above are stripped from uniques; the class chain-special ladder covers them for free. Distinctive mechanics (`backstab` is dagger-only anyway, but `guaranteed_hit` for Fail-not, `returning_blow` for Green Chapel Axe, `finesse_dex` for Rapier-class uniques) stay.
4. **`critMultiplier` already stripped** (v2.14.0 commit).
5. **Iconic uniques keep bespoke `base_damage` overrides** — the 20-odd truly legendary weapons whose IDENTITY is "the damage number is bigger" get a bump above the formula.

## `base_damage` formula for the bulk

```
target_base = round(common_class_base × tier_mat_mult × 1.5)
```

Common class bases (from chain_combat_v2.md):

| Class | Common base |
|-------|-------------|
| Fist | 2 |
| Dagger | 3 |
| Rapier | 4 |
| 1h Sword | 5 |
| 1h Axe / Mace / Club | 6 |
| Spear | 5 |
| Staff | 8 |
| Glaive | 8 |
| Halberd | 7 |
| 2h Sword / Scimitar (large) | 8 |
| 2h Axe | 10 |
| 2h Warhammer / Morningstar (T5) | 11 |
| Bow | 4 |
| Crossbow | 8 |
| Sling | 2 |
| Ranged (catch-all) | 6 |

Tier material multipliers (implied):

| Tier | mult | Sample material |
|------|------|-----------------|
| T1 | 1.0 | iron / hardwood |
| T2 | 1.1 | steel / silver / bronze-upgraded |
| T3 | 1.25 | cold_iron / silver / legendary-mid |
| T4 | 1.4 | mithril / adamantine-early |
| T5 | 1.6 | adamantine / sunsteel / legendary-late |

Sample targets (formula only, no iconic bump):

| Class @ T5 | Target base | Chain 5 (poly) | Chain 15 | Chain 20 |
|-----------|-------------|----------------|----------|----------|
| Dagger | 7 | 46 | 160 | 255 |
| 1h Sword | 12 | 78 | 275 | 437 |
| Spear | 12 | 78 | 275 | 437 |
| 2h Sword | 19 | 124 | 435 | 691 |
| 2h Warhammer | 26 | 170 | 595 | 946 |
| Staff | 19 | 124 | 435 | 691 |

Iconic exception bumps (base kept high because the identity IS "hits like a truck"):

| Weapon | Formula target | Iconic base | Why |
|--------|----------------|-------------|-----|
| Sword of Michael | 12 | 18 | Anti-Abaddon divine role (also carries abaddon_bonus_damage) |
| Mjolnir | 26 | 32 | God-tier warhammer identity; chain lightning stacks on top |
| Dawnbreaker | 26 | 30 | First-Darkness ender vs undead (undead tag bonus stacks) |
| Stormbringer | 12 | 24 | Soul-eater lifesteal + `betrays_at_low_hp` risk warrants the bump |
| Tyrfing | 19 (2h) | 26 | Cursed hit-hard-or-hurt-yourself; `cursed_miss_backlash` tradeoff |
| Excalibur | 12 | 16 | Once-and-future king; kill_heal + purity signature |
| Anduril | 12 | 16 | Flame of the West; undead-multiplier signature |
| Gungnir | 12 | 15 | Never-misses; cannot_miss is the real gift |
| Gram (reforged) | 12 | 18 | Dragon-slayer; `ignore_resistances` is the real gift |
| Mistilteinn | 12 | 18 | Baldr's death; `damage_double_vs_resistant_at_max` stacks |
| Ruyi Jingu Bang | 19 | 24 | Sun Wukong's cudgel; `chain_modulated_reach` signature |
| Laevateinn | 19 | 26 | Doom-brand; `boss_doom_dot_at_chain_5` stacks |
| Aiglos | 12 | 16 | Elrond's spear; fire immunity + legendary role |
| Trident of Poseidon | 12 | 18 | Sea-god weapon; multi-type damage |
| Gandiva | 8 | 12 | Arjuna's bow; `multi_arrow_at_chain_5` stacks |
| Fail-not | 6 | 10 | Tristan's `guaranteed_hit` bow |
| Kusanagi | 12 | 16 | Grass-cutter; `surrounded_proc_bonus` (rewired to +25%) |
| Chandrahasa | 12 | 18 | Moon-blade; `low_hp_damage_bonus` scales with player desperation |
| Punch in the Face | 2 | 35 | Dad-tier joke Easter egg; not part of the balance curve |
| Wendigo's Fang | 7 | 12 | T5 dagger keeps a bump for its curse identity |
| Soul Reaver | 8 (scimitar → 1h) | 14 | Growth-on-innocent-kill mechanic is the real gift |
| Sudarshana Chakra | 8 | 14 | Vishnu's discus; T5 scimitar unique bump |

Every OTHER unique gets the plain formula target.

## Redundant `class_mechanic` values retired

These are now covered by the class chain-special ladder in `combat.py`. Stripped from uniques where they duplicate the class behavior:

- `bleed_at_max` — covered by dagger / 1h axe / 2h axe / spear chain 5
- `cleave_at_max` — covered by 1h axe chain 15, 2h axe chain 5+, 2h sword chain 5+, glaive chain 5+
- `cleave_at_max_plus_bleed` — covered by 2h axe chain 5+
- `stun_at_max` — covered by mace / 2h warhammer chain 5
- `stun_knockdown_at_max` — same as above, chain 10
- `defensive_parry` — covered by rapier chain 15 (`melee_dmg_reduction`)
- `quick_riposte` — covered by rapier chain 5 (`bleeding`) + chain 15 stance
- `master_strike` — covered by 1h sword chain 10 (bypass DR)
- `backstab` — covered by dagger identity (still fires on unaware kills; kept as a per-weapon flavor on Carnwennan / Ridill via a distinctive passive later)
- `armor_pierce_at_max` — covered by spear chain 10+ / 1h sword chain 10+
- `anti_heavy_at_max` — merged into universal `armor_crack` at mace / warhammer chain 10+

Kept as-is (still distinctive per-weapon):
- `finesse_dex` — DEX-instead-of-STR is a per-weapon build choice (Rapier uniques). Class doesn't cover it.
- `guaranteed_hit` — Fail-not identity (chain 0 → chain 1).
- `returning_blow` — Green Chapel Axe identity (max-chain backlash).
- `versatile` — bastard-sword-family +20% two-handed bonus.
- `str_bonus_range_7` — composite bow draw-weight identity.
- `ignores_all_armor` / `ignores_half_armor` — heavy/light crossbow signature (also covered by crossbow class special but the flag is the DATA driver).
- `ignores_shield` — flail identity (no class equivalent).
- `concussion_at_max`, `free_stones`, `rapid_shot_at_max`, `reach_2` — kept as class-common template mechanics on shortbow / sling / staff / spear commons; already retired from uniques.

## Per-unique execution plan

Bulk-applied via `tools/balance/rebase_uniques_v2_14.py`:

1. Set `chain_exponent: 1.15` on every unique
2. Compute `base_damage` per formula unless in the iconic-exception table
3. Strip redundant `class_mechanic` values (bleed_at_max, cleave_at_max, cleave_at_max_plus_bleed, stun_at_max, stun_knockdown_at_max, defensive_parry, quick_riposte, master_strike, armor_pierce_at_max, anti_heavy_at_max)
4. Preserve all other fields (lore, floor_spawn_weight, effects, effective_against, per-tag bonus damage, unique-only mechanics, quest interactions)

## Distinctive-passive audit

Every unique carries at least ONE distinctive mechanic beyond damage. This list confirms:

| Unique | Distinctive mechanic (kept / preserved) |
|--------|----------------------------------------|
| Atalanta's Bow | first_blood_bonus |
| Gungnir | cannot_miss |
| Fail-not | guaranteed_hit + cannot_miss_before_hurt |
| Excalibur | kill_heal_amount |
| Anduril | undead_multiplier + per-tag undead bonus |
| Gram (reforged) | ignore_resistances |
| Mjolnir | chain_lightning_at_chain_n + giant bonus |
| Dawnbreaker | undead bonus + holy damage type |
| Sword of Michael | abaddon_bonus_damage + holy_smite_message |
| Stormbringer | lifesteal + betrays_at_low_hp |
| Tyrfing | cursed_miss_backlash + cursed |
| Mistilteinn | damage_double_vs_resistant_at_max |
| Skofnung | chain_bonus_on_low_hp_window |
| Ruyi Jingu Bang | chain_modulated_reach |
| Gandiva | multi_arrow_at_chain_5 |
| Kusanagi | surrounded_proc_bonus (rewired to +25% dmg) |
| Kladenets | dragon bonus + skip_chain_warmup_vs_tag |
| Hrunting | one_shot_chain_save_per_floor |
| Harpe | petrify_on_crit (rewired to petrify at chain 15) |
| Chandrahasa | low_hp_damage_bonus |
| Chandrahas | prophecy_blade tag bonus |
| Cronus's Scythe | reap-death flavor + T3 adamantine T3-outlier premium |
| Sudarshana Chakra | thrown returning + adamantine T5 |
| Amenonuhoko | aoe_slow_on_kill |
| Trident of Poseidon | multi damage type + effective_against sea |
| Spear of Lugh | damage_bonus_vs_gaze |
| Gae Bulg / Gae Dearg | bone piercing + heal_blocked |
| Aiglos | wielder_fire_immunity + freeze_chance |
| Laevateinn | boss_doom_dot_at_chain_5 |
| Rod of Moses | quest-item flavor |
| Robin Hood's Longbow | stealth_damage_bonus |
| Bow of Rama | quest-item flavor |
| Sling of David | giant-slayer flavor |
| Wendigo's Fang | disease/curse tag |
| Vulcan's Brand | fire-damage tag proc |
| Green Chapel Axe | returning_blow + on_hit_regen |
| Khopesh of Anubis | kill_max_hp_bonus |
| Parashu | cleave_at_max (kept as legacy layered onto class ladder) |
| Caladbolg | cleave_at_max (kept as legacy) |
| Naegling | wave 2 mechanic |
| Punch in the Face | Dad-tier meta joke |
| Zulfiqar | anti-tag double bonus |
| Hunt Captain's Sword | spectral hunter flavor |
| Sword of Damocles | overhead-menace flavor |
| Broken Blade of Gram | quest starter (reforgeable) |
| Chainsaw Prosthetic | flavor T3 |
| Boomstick | flavor T3 |
| Net of Hephaestus | entangle utility (not a chain weapon) |

## Removed / demoted

None removed. Every unique kept.

- **Net of Hephaestus** stays but doesn't use chain-special ladder (its identity is entangle-on-hit, not a chain builder). Its class 'net' is not in the class-specials dispatch and thus no class chain effect fires — intentional.
- **Chainsaw Prosthetic** and **Boomstick** stay as T3 joke items with the formula base_damage.

## Follow-up (v2.14.1+)

- Per-unique deeper reworks for weapons whose lore promises more than a distinctive passive currently delivers (list to be assembled from playtest).
- Ranged uniques don't yet use the crossbow / bow / sling class-specials pathway consistently — the `_weapon_key()` catch-all `ranged` split needs verification for each ranged unique's requires_ammo string.
