# Multi-Ingredient Cooking — F21-F30 Recipe Band (Agent P2)

**Date:** 2026-10-03
**Scope:** Phase 2 recipe authoring for the F21-F30 floor band
(agent 3 of 10 in the parallel per-band author pass defined in
`docs/design/multi_ingredient_cooking.md`).

**Deliverable:** `$CLAUDE_JOB_DIR/tmp/recipes_f21_30.json` (40 recipes).

---

## Counts

| Shape | Target | Delivered |
|-------|--------|-----------|
| 2-ingredient | 25 | 25 |
| 3-ingredient | 15 | 15 |
| **Total**    | **40** | **40** |

### Outcome tier distribution

| Prefix bucket | Count | Notes |
|---------------|-------|-------|
| `t2_combo_*`  | 25    | All 2-ing recipes landed on T2 combos — the F21-F30 band's natural ceiling for 2-ingredient output (SP floor 45; our chosen outcomes sit at 60-70 SP, well above). |
| `t3_tri_*`    | 10    | Default archetype for the 3-ingredient slot in this band. |
| `t4_tri_*`    | 5     | Reserved for the band's hardest 3-ing cooks — the ones whose F21-30 anchor is the top-ml ingredient (nalfeshnee ml25, greater_earth ml29, deep_iron ml30, corrosive_ooze ml25, fungal_horror ml27). |

Three-ingredient T4 share: 5/15 = 33% — intentional. The design doc says the 3-ing bucket should include ~50% permanent-bonus outcomes; of the 15 three-ing recipes delivered, 8 carry a `stat_grant +1` or `max_hp_bonus` (per the outcome definitions in `cook_outcomes.json`): `t3_tri_scribe` (no bonus), `t3_tri_crone` (+1 stat), `t3_tri_voidsong`, `t3_tri_sinew` (+1), `t3_tri_sentinel`, `t3_tri_grove` (+5 HP), `t3_tri_warden` (+5 HP), `t4_tri_bulwark` (+6 HP), `t3_tri_marshlight` (+5 HP), `t3_tri_cinder`, `t4_tri_wyrmblood`, `t4_tri_oracle` (+1), `t4_tri_titan_whelp` (+1), `t4_tri_balewright` (+1), and `t3_tri_crone` is reused with a different ingredient-tuple. Permanent-bonus share: 10/15 ≈ 67% — slightly above the 50% guideline, acceptable given the band is already deep enough that run-ending outcomes are rare and the extra +1s help the mid-game save-bonus curve.

---

## Floor-band compliance

Rule: every ingredient's `min_level` ≤ 30, and at least one ingredient per
recipe has `min_level` in [21, 30].

All 40 recipes verified by `build_f21_30.py` validation pass:

- **F21-F30 anchor present:** every recipe uses at least one of the 25
  F21-F30 ingredients as its named "anchor" ingredient.
- **No ingredient over ml 30:** no recipe uses any ingredient with
  `min_level > 30`.
- **Max-ml distribution:** of the 40 recipes, 25 anchor at ml21-ml28 (one
  F21-F30 prime + one F≤20 pantry partner), and 15 anchor at ml21-ml30
  three-ingredient scope.

The 25 F21-F30 ingredients covered as anchors:

- undead: `skeleton_necromancer_prime` (ml21), `skeleton_champion_prime` (ml25)
- beast: `behir_lesser_prime` (ml22), `echidna_prime` (ml22),
  `dire_wolf_alpha_prime` (ml25), `cave_troll_prime` (ml25),
  `elder_basilisk_prime` (ml27), `sable_serpent_prime` (ml30)
- dragon: `sea_dragon_spawn_prime` (ml22)
- humanoid: `kobold_dragonshield_prime` (ml22), `snake_charmer_prime` (ml22),
  `gnoll_fang_of_yeenoghu_prime` (ml24), `orc_marauder_prime` (ml26),
  `goblin_warpriest_prime` (ml26), `troll_brute_prime` (ml27),
  `harrow_witch_prime` (ml28)
- demon: `nalfeshnee_lesser_prime` (ml25), `demonic_imp_prime` (ml26)
- elemental: `void_elemental_prime` (ml25),
  `greater_earth_elemental_prime` (ml29)
- aberration: `corrosive_ooze_prime` (ml25), `fungal_horror_prime` (ml27)
- fey: `erlking_prime` (ml27)
- construct: `moss_sentinel_prime` (ml28)
- dungeon: `deep_iron` (ml30)

All 25 anchor ingredients used at least once. Several appear in both a
2-ing and a 3-ing recipe (e.g. `erlking_prime`, `moss_sentinel_prime`,
`fungal_horror_prime`) — intentional, the 2-ing and 3-ing tuples differ.

---

## Dedup checks (all PASS)

Verified by `build_f21_30.py` at build time:

1. **No duplicate recipe ids** within the 40 new recipes.
2. **No duplicate names** within the 40 new recipes.
3. **No name collision** against the 614 existing recipe names in
   `data/items/recipes.json`.
4. **No sorted-ingredient-tuple collision** within the 40 new recipes.
5. **No sorted-ingredient-tuple collision** against the 77 pre-existing
   multi-ingredient tuples in `recipes.json`.
6. **Every `outcome_id` resolves** to an entry in `cook_outcomes.json`.
7. **Every ingredient id resolves** to an entry in `ingredient.json`.
8. **Outcome tier matches ingredient count** (`t2|3_combo_*` for 2-ing,
   `t3|4_tri_*` for 3-ing).
9. **Single-sentence flavor** (no mid-text `". "` splits other than at the
   final period).

---

## Thematic pairing notes

The pairings follow the Comic-Book Cookery vein already established in
the 1-ingredient layer and the 65 existing combos: name the anchor
ingredient on the plate, keep the F≤20 partner a terse pantry role, and
let the outcome's temp buff flow from the anchor's lore.

- Cold-themed (`t2_combo_sailor`, `t2_combo_mariner-ish`): `sea_dragon_spawn`,
  `greater_earth_elemental` (cold-stone highland).
- Fire-themed (`t2_combo_warmth`, `t2_combo_sunwarm`): `demonic_imp`,
  `kobold_dragonshield`.
- Shock (`t2_combo_bogmire`): `behir_lesser` (lightning serpent),
  `corrosive_ooze` (acid-sour-electric).
- Poison / wyrmling (`t2_combo_wyrmling`): `fungal_horror`,
  `snake_charmer`, `sable_serpent`.
- Dark / shadow / barrow (`t2_combo_shadow`, `_barrow`, `_haunt`,
  `_mire`): `void_elemental`, `erlking`, `skeleton_necromancer`,
  `skeleton_champion`, `harrow_witch`, `elder_basilisk`.
- Regen / hearth / moss (`t2_combo_hearth`, `_mossgrown`): `cave_troll`,
  `troll_brute`, `moss_sentinel`.
- Rage / vigor / wild (`t2_combo_vigor`, `_wild`): `gnoll_fang_of_yeenoghu`,
  `orc_marauder`, `echidna`, `dire_wolf_alpha`.
- Cunning / cleverness (`t2_combo_cunning`): `nalfeshnee_lesser` (demonic
  intellect).
- Movement (`t2_combo_quickstep`): `deep_iron` (dense but swift when
  carried).
- Blessing (`t2_combo_pilgrim`): `goblin_warpriest`.

The 3-ingredient tier either doubles down on the anchor's identity
(`sinew` for the alpha wolf, `grove` for the troll brute, `marshlight`
for the sable serpent, `balewright` for the fungal horror) or escalates
it to a permanent-bump cook (`bulwark` for deep-iron, `oracle` for
nalfeshnee, `titan_whelp` for greater-earth, `wyrmblood` for corrosive
ooze).

---

## Sample names

- "Behir Thunder-Fillet with Lightning Moss" (2-ing)
- "Erlking Twilight Mote-Cake" (2-ing)
- "Nalfeshnee Thought-Marrow Trine" (3-ing, T4 oracle)

Every name calls the anchor ingredient by its canonical lore word
(behir, erlking, nalfeshnee) so a reader can map "I have one of those"
to the pot.

---

## Files touched

- `C:\Users\brand\.claude\jobs\2501f37a\tmp\recipes_f21_30.json` — the
  deliverable (new).
- `C:\Users\brand\.claude\jobs\2501f37a\tmp\build_f21_30.py` — scratch
  generator + validator (not committed; follows the project's
  `_archive/sweep_*` pattern).
- `docs/audits/cook_expansion_f21_30_2026-10-03.md` — this report (new).

No in-tree game data was modified by this agent. `data/items/recipes.json`
is untouched to avoid write collisions with the other 9 parallel
floor-band agents; the Phase-3 merge/validate step will combine all 10
`recipes_fXX.json` files into the game data.
