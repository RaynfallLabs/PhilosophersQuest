# Equipment balance review (armour, shields, weapons) — 2026-11-07

Brandon, playtest of 3.3.1: "I have a small shield, and then I found a tower
shield. Tower shield has a flat better AC bonus (+3) but the same 2 question
tier 1 geo equip cost. I am afraid we do not have a good distribution of items
at every tier with higher thresholds, and that they aren't balanced across all
levels. Needs a deep review."

Everything below was measured from the game's own code and data on
`release/3.3.2` (`instantiate_armor` / `instantiate_shield` /
`instantiate_weapon`, `material_spawn_weight`, `tools/balance/loot_census.py`
for what runs really find). Nothing has been changed yet; section 5 is the
proposal and section 6 the decisions it needs.

---

## 1. How gear is built and priced today

- **Every common piece is template x material.** `data/items/*.json` holds
  only uniques; commons come from `data/templates/{armor,shields,weapons}` (34
  armour, 5 shield, 22 weapon templates) times `data/materials/{armor,weapons}`
  (45 armour, 50 weapon materials).
- **AC** = template base AC + material AC bonus (`items.py` ~2425, ~2478).
- **Quiz tier** (geography, for armour and shields) = the **material's** tier.
- **Equip threshold** (how many questions):
  - armour: the **template's** weight class only (light 1, medium 2, heavy 3;
    `tests/test_armor_template_thresholds.py`). Not AC, not material, not depth.
  - **shields: never set** (`instantiate_shield`), so `Shield.__init__`
    defaults it to **2** for every common shield at every depth (`items.py:937`).
  - uniques: written per item (1-5).
  - accessories (history): written per item, and they do rise with tier
    (tier 1 mostly 2 ... tier 5 3-5). Accessories are the one family that works.
- **Spawn**: the material is drawn first by its depth bell, then the template
  **uniformly** among those that fit. The templates' floor bands ("tower:
  F60-100") are design notes only; no code reads them.
- **Weapons**: no equip quiz; the cost is the material's maths tier on every
  swing. The weapon curve is smooth within each tier and steps at tier lines.

## 2. The shield case, exactly

| Oak shield | AC | Weight | Questions | Geo tier |
|---|---|---|---|---|
| Buckler | 0 | 1.8 lb | 2 | 1 |
| Light (the start shield) | 1 | 4.5 lb | 2 | 1 |
| Tower | 3 | 27 lb | 2 | 1 |

A tower shield is +2 AC over the start shield for the same quiz, and since the
template is picked uniformly, it is 12% of shield drops on floors 1-10 (40% on
91-100). Weight is its only cost ("slows reaction" in its note is not built).
Some uniques are worse than a free common: the Mycenaean Tower Shield is AC 3
for **3** questions; an Oak Tower is AC 3 for 2.

## 3. Findings

### A. Equip cost does not follow protection
1. **Shields are 2 questions at every depth**, buckler or tower, floor 1 or 99.
2. **Commons never cost more than 3.** Thresholds 4-5 exist only on uniques,
   so the deep floors have no common gear that asks more than the shallow ones.
   Only the geography tier rises with depth.
3. **Wide AC spread inside one cost**: body threshold 3 runs AC 4-6 at tier 1
   and 5-9 at tier 4; shields at threshold 2 run AC 1-6 at tier 4.
4. **Dominated templates** (more questions and weight for nothing):
   - every medium and heavy **minor-slot** piece (arms, hands, legs, feet) has
     the same base AC 1 as the light one: AC 4 costs 1 question in Elven Silk
     and 3 in Adamantine plate;
   - banded, chainmail and splint (3 questions, 35-40 lb) are beaten by scale
     (2 questions, base 4, 30 lb); ringmail by chain shirt;
   - great helm and plate helm (3) equal the steel helm (2);
   - heavy wooden shield (AC 1, 10 lb) is beaten by kite (AC 2, 10 lb).
5. The whole best-in-slot kit is **13 questions at every depth** (body 3, helm
   2, six minor slots at 1, shield 2).

### B. Distribution across floors
1. **Too strong too early**: hematite is a tier-1 metal on floors 8-48 that
   opens every metal template: Hematite Full Plate is **AC 6 at geo tier 1**
   from floor 8; an AC 3 tower shield from floor 1.
2. **Plateaus**: the best common kit changes only on floors 8, 16, 41 and 63,
   then **never again for 37 floors**. CURVE.md principle 8 asks for a
   meaningful upgrade every 2-3 floors.
3. **Tier 5 adds nothing over tier 4** (material bonuses +1..+3 in both; the
   best tier-5 shield is 6, as at tier 4).
4. **Thin start**: floors 1-10 have 6 shield materials and 26 body combinations.
5. Dead data: `leviathan_rib_armor` and `treant_heart_armor` fit no template
   and never spawn; tungsten is never a shield.

### C. The root problem: armour stops mattering around floor 15
Armour class only decides whether a blow lands (`monster.py` ~1141-1162);
nothing reduces damage. Once AC passes a monster's reach, an ordinary
monster still hits 30% of the time (`MIN_HIT_ORDINARY`; named foes 40%).

What a run actually wears (loot census, 6 runs, best non-cursed common
pieces found so far plus rings; DEX 10):

| Floor | Worn AC | Monsters hit | CURVE.md prepared / skilled |
|---|---|---|---|
| 1 | 8 | 60% | 7 / 4 |
| 5 | 2 | 39% | — |
| 10 | -3 | 36% | 4 / -2 |
| 15 | -6 | **32%** | — |
| 20 | -9 | 32% | 0 / -8 |
| 30 | -18 | 32% | -4 / -12 |
| 50 | -29 | 32% | -12 / -20 |
| 60 | -35 | 32% | -16 / -24 |
| 80 | -46 | 32% | -24 / -32 |
| 100 | -50 | 32% | -28 / -36 |

From about floor 15 to floor 100 the hit chance sits on the 30% floor, so
**no armour found after floor 15 changes how often the hero is hit**. Every
shield, every plate and every unique beyond that is felt only through its
resistances and procs. That is why the gear does not feel balanced across the
levels: past the early floors the AC number has nothing left to do. The data
also outruns both written targets (CURVE.md's "skilled" line and
`tools/balance/curve.py`, which says -14 at floor 100, "NOT -34"), which
disagree with each other.

### D. Weapons (for completeness)
Smooth inside each tier and stepped at tier lines by design. On floors 81-100
the best **unique** tops out at 519 base damage against 1,156 for the best
common (primordial maul): deep uniques fall behind commons.

## 4. Tests a rebalance touches
`test_armor_template_thresholds.py` (light 1 / medium 2 / heavy 3),
`test_balance_pass_2026_10.py` (quiz tier = material tier),
`test_loot_audit.py` (tier N first spawns no earlier than (N-1)x20-5),
`test_chest_templates.py`, `test_hide_armor_balance.py`, `test_carry_weight.py`
(full plate 65 lb, tower 30 lb), `test_unique_armor_pass.py`,
`test_json_wave3_armor_acc.py`, `test_balance.py`, `test_chain_equip.py`; for
weapons `test_chain_gradient.py`, `test_unique_weapon_scale.py`,
`test_yardsticks.py`. Save migration (`main.py` ~1464-1521) recomputes name and
AC for saved common **armour** only, not shields, thresholds or quiz tiers.

## 5. Proposal (three phases, smallest first)

**Phase 1: cost follows protection** (data and `instantiate_*`; playtestable)
- Shields get thresholds by weight class, like armour: buckler and light 1,
  heavy wooden and kite 2, tower 3.
- Heavier minor-slot templates earn their questions: light base AC 1, medium
  2, heavy 3 (or drop the medium and heavy minor templates). Same for helms
  (great and plate helm base 3) and the dominated body templates.
- Hematite becomes tier 2 (or loses the plate templates), so tier-1 plate
  disappears from floors 8-15.
- The dead materials either fit a template or are removed.

**Phase 2: a real curve across 100 floors** (needs decision 1)
- Enforce the templates' floor bands as spawn weights (a tower shield rare
  before about floor 30, common from 60), and smooth the material AC ladder
  so every tier adds (tier 1 +0, 2 +1, 3 +2, 4 +3, 5 +4).
- Common thresholds rise with the material as well as the template (decision
  2), so deep commons ask 4-5 questions and the late game has gear that
  costs what it gives.
- Retune with `tools/balance/loot_census.py` until worn AC tracks the chosen
  line; one test pins the census AC per band.

**Phase 3: make AC matter all the way down** (needs decision 3)
- Either keep AC on the curve AND raise monster to-hit in step with it
  (CURVE.md principle 5, baked into `monsters.json` by
  `tools/balance/scale_monsters.py`, per LORE NOT FLOOR), or give armour a
  second job past the hit floor (for example a share of damage turned aside),
  so a better shield on floor 70 is felt.

## 6. Decisions needed
1. **Which AC line is the target?** CURVE.md's "prepared" line (-28 at floor
   100), its "skilled" line (-36), or `curve.py`'s -14. Right now real runs
   are at -50.
2. **Should common equip cost rise with depth** (material tier adding a
   question at tiers 4-5), or stay template-only with depth carried by the
   geography tier?
3. **How should armour stay meaningful deep**: monster to-hit rising with the
   AC curve, or armour reducing damage past the hit floor?
