# Wand Cull Report

**Source:** `tools/balance/generated/data/wand.json` (112 wands from Generator F)
**Output:** `tools/balance/generated/data/wand.json.culled` (87 wands)
**Removed:** 25 wands
**Target was:** ~80; landed at 87 (above target, but below 90 ceiling and without sacrificing any meaningfully distinct mechanic)

## Method

1. Grouped all 112 wands by their `effect` field.
2. Within each effect group, treated entries as true duplicates when (a) they share the same `effect`, (b) `power` is identical (or both empty for status wands), and (c) the lore-described mechanical difference does not correspond to any field the engine actually reads (i.e., the engine will execute the exact same handler for both).
3. For multi-tier chains where higher tiers add **real numerical power** (different damage dice, different durations encoded in `power`, distinctly different effect strings), kept all tiers — these are genuine power-band variants.
4. For multi-tier status-only chains (`power: ""`, only `quiz_tier` / `charges_max` / `peak_floor` differ), trimmed the **middle rung** of three-tier chains and merged same-tier duplicates outright. This preserves a low-floor and a deep-floor variant for spawn-band diversity while removing the flavor-only middle.
5. Preserved every entry that delivers a unique mechanic (named uniques, `iron_mortar`, `lantern_of_diogenes`, `caduceus_wand`, every single-occurrence effect).

## Merge Decisions (25)

### Same-tier true duplicates — pure flavor twins (10)

| Dropped | Merged into | Effect | Tier | Rationale |
|---|---|---|---|---|
| `wand_of_lethargy` | `wand_of_slow` | slow_monster | T1 | Identical tier/charges/power; "slow" is the conventional name. |
| `wand_of_slumber` | `wand_of_sleep` | sleep_monster | T1 | Identical fields; "sleep" is the iconic NetHack/D&D name. |
| `wand_of_darkness` | `wand_of_blindness` | blind_monster | T2 | Identical fields; lore claims sphere-of-shadow vs flash but `effect` is same handler. |
| `wand_of_swiftness` | `wand_of_speed` | haste_self | T2 | Identical fields; "speed" is the standard label. |
| `wand_of_concealment` | `wand_of_invisibility` | invisibility_self | T2 | Identical fields; "invisibility" is the canonical name. |
| `wand_of_levitation` | `wand_of_flight` | levitation_self | T2 | Identical fields; "flight" is the more evocative of the pair and the lore positions it as the real-magic version. |
| `wand_of_cold` | `wand_of_frost` | cold_bolt | T2 | Identical 2d4 / T2 / charges 6; "frost" is the more evocative name. (Higher cold tiers — ice, glaciation — preserved.) |
| `wand_of_venom` | `wand_of_poison` | poison_monster | T3→T2 | Same effect, no power scaling — pure flavor. |
| `wand_of_plague` | `wand_of_poison` | poison_monster | T3→T2 | Same effect, no power scaling, no duration field — three poison wands collapsed to one. |
| `wand_of_illumination` | `wand_of_light` | light | T1 | Identical fields; "light" is the canonical name. (Lantern of Diogenes preserved — it's a named unique artifact.) |

### Cross-tier middle-rung trims — status chains where no numerical scaling occurs (8)

These effects have `power: ""` and the engine cannot distinguish tier-to-tier in actual gameplay. Kept the bottom and top rungs for spawn-band diversity; dropped the redundant middle rung.

| Dropped | Merged into | Effect | Rationale |
|---|---|---|---|
| `wand_of_bewilderment` | `wand_of_confusion` / `wand_of_madness` | confuse_monster | T2 middle rung; T1 confusion + T3 madness preserved. |
| `wand_of_dread` | `wand_of_fear` / `wand_of_terror` | fear_monster | T2 middle rung; T1 fear + T3 terror preserved. |
| `wand_of_withering` | `wand_of_aging` | weaken_monster | Both `power: ""`; aging's lore (years forced onto target) is more vivid. |
| `wand_of_rot` | `wand_of_disease` | disease_monster | Both `power: ""`; disease is the cleaner umbrella name. |
| `wand_of_negation` | `wand_of_cancellation` | cancellation | Both `power: ""`; cancellation is the conventional anti-magic term. |
| `wand_of_reflection` | `wand_of_mirroring` | reflect_self | Same effect; T2 mirroring kept for accessibility. |
| `wand_of_vitality` | `wand_of_regeneration` | regeneration_self | Same effect; "regeneration" is the iconic name. |
| `wand_of_summoning` | `wand_of_create_monster` | create_monster | Same effect; create_monster is the iconic roguelike name. |

### Cross-tier same-effect — lore-flavored but mechanically identical (7)

These have visibly different lore (e.g., "petrification" describing skin-to-stone) but share an `effect` string with their predecessor, so the engine executes the same handler. Dropped to keep the wand pool compact.

| Dropped | Merged into | Effect | Rationale |
|---|---|---|---|
| `wand_of_transmutation` | `wand_of_polymorph` | polymorph_monster | T4 vs T3; same effect, no power field. |
| `wand_of_ethereality` | `wand_of_phasing` | phase_self | T4 vs T3; same effect, no duration field. |
| `wand_of_opening` | `wand_of_locksmithing` | knock | T3 vs T2; same effect; locksmithing has richer flavor and a sane min_level (20 vs the orphan-feeling 55). |
| `wand_of_domination` | `wand_of_charm_monster` | charm_monster | T3 vs T2; same effect string — lore describes a power difference the engine does not implement. |
| `wand_of_petrification` | `wand_of_paralysis` | paralyze_monster | Same effect; petrification's "damage resistance during paralysis" isn't a field on this entry. |
| `wand_of_tunneling` | `wand_of_digging` | digging | Same effect; lore says "moves more material per charge" but no per-charge volume field exists. |
| `wand_of_stoneskin` | `wand_of_shielding` | shield_self | Same effect string; lore variation isn't reflected in any data field. |

## Top 5 Hard Calls (judgment was non-obvious)

1. **`wand_of_petrification` → `wand_of_paralysis`.** Petrification has rich D&D pedigree as a distinct status. But the `effect` field is plain `paralyze_monster` and there's no damage-reduction sub-field, so the engine treats them identically. Dropped, but flagged: if the engine grows a `petrify_variant` flag this should come back.
2. **`wand_of_plague` AND `wand_of_venom` both merged into `wand_of_poison`.** Three poison wands at adjacent tiers, `power: ""` on all, no `duration` or `damage_per_turn` fields. Plague's lore describes a longer dot-progression but nothing in the data backs it up. Collapsed all three to the T2 entry.
3. **`wand_of_stoneskin` → `wand_of_shielding`.** Stoneskin is iconic D&D and "feels" distinct from a force-barrier. Same `effect: shield_self`, no `damage_reduction` field. Dropped reluctantly; flag for future split.
4. **Kept `wand_of_blindness` over `wand_of_darkness`.** Both T2 `blind_monster` with the same fields. Darkness's lore (light-absorbing sphere that defeats darkvision) was tempting, but "wand of blindness" is the canonical roguelike name and reads more clearly to a new player.
5. **Kept `wand_of_flight` over `wand_of_levitation`.** Generally I prefer the canonical roguelike term ("levitation"), but in this case the lore positions flight as the real-magic version of an essentially identical mechanic, and "flight" is the more evocative geek-dad name. The rule isn't dogmatic.

## Top 3 Couldn't-Merge Despite Shared Effect

1. **`wand_of_light` + `lantern_of_diogenes`** (both T1 `light`). Lantern of Diogenes is a **named unique artifact** with its own lore (Diogenes of Sinope, search for the honest man) and a `containerLootTier: rare` flag. Cannot merge — it's a unique drop.
2. **`wand_of_healing` (T1, 2d4) + `caduceus_wand` (T2, 3d4)**, both `effect: heal`. Caduceus is a named unique with `containerLootTier: rare` and meaningfully different power dice. Different floor band, different rarity tier, different power — keep both.
3. **`wand_of_turning` (T2, 2d4) + `wand_of_banishment` (T3, 4d4)**, both `effect: turn_undead`. Power doubles between them, charges differ (6 vs 3), and quiz_threshold rises (2 → 4). This is a real numerical scaling chain, not flavor doubling.

## Final tally

- **Removed:** 25 wands
- **Kept:** 87 wands
- **One remaining same-tier-same-effect pair:** `wand_of_light` and `lantern_of_diogenes` (a generic plus a named unique — by design).

87 is above the ~80 target but below the 90 ceiling. To go lower I would have to merge entries that the brief flags as "keep distinct" — different power dice on damage chains, or different effect strings entirely. I stopped here.
