# Chest Template Rebuild — Design Spec

Replaces tier-based chest loot with 12 named templates, each with a thematic loot table. Quiz mode switches from threshold (pass/fail) to escalator-chain Economics. Chain reached scales loot weights — better economists get better drops, with bounded upside.

**Goal**: target ~10-15 uniques per 100-floor run (user's "rare and special" intent), with chest templates as the floor highlight per user's earlier direction.

---

## Chain curve (balance-careful)

Chain reached on the Economics escalator becomes a `chain_mult` applied to the template's rare/unique weights:

| Chain | Name | rare_mult | item_count | Flavor |
|---|---|---|---|---|
| 0 | Failed | — | 0 (chest stays locked) | "You fumble the lock." |
| 1 | Pried | 0.25× | 1 | "You wedge it open. Just barely." |
| 2 | Cracked | 0.50× | 2 | "The mechanism gives." |
| 3 | Opened | 1.00× | 2-3 | Baseline — competent. |
| 4 | Picked clean | 1.50× | 3 | "Almost like it wanted to open." |
| 5 | Master thief | 2.00× | 3-4 (+1 bonus) | "The lock yields. You see EVERYTHING." |

Critically: **chain 5 only doubles rare odds, doesn't 10x them**. Prevents endgame chest flood. Also adds +1 common item at chain 5 — "more loot" rather than "guaranteed unique."

---

## Templates (12 total)

Each entry: spawn weight by floor band, loot table (item-category weights), and rare/unique chance at chain 3 (baseline).

| Template | Floor band | Theme | Item categories (weights) | Rare% @ chain 3 |
|---|---|---|---|---|
| **wooden_chest** | L1-30 (common); L30-50 (rare) | Battered traveler's box | gear 60, potion 20, ammo 10, scroll 10 | 1% |
| **iron_lockbox** | L10-50 (common); L50-70 (rare) | Mid-tier locked storage | gear 40, magic 30, accessory 20, ammo 10 | 3% |
| **jewelry_box** | L5-80 (uncommon) | Small ornate ring/amulet | accessory 70, gold 30 | 5% (accessory-only) |
| **apothecary_chest** | L1-80 (common) | Wax-sealed bottles | potion 50, ingredient 40, scroll 10 | 2% |
| **scholar_satchel** | L20-80 (uncommon) | Leather + brass clasps | spellbook 40, scroll 40, wand 20 | 4% (magic-only) |
| **warlord_warchest** | L20-70 (uncommon) | Iron-bound campaigner's | weapon 50, armor 30, shield 20 | 6% (gear-only) |
| **merchant_strongbox** | L1-80 (uncommon) | Already-identified mix | mixed 100 (all items pre-id'd) | 3% |
| **pirate_cache** | L1-80 (uncommon) | Random + heavy gold | gold 50, gear 20, magic 20, ammo 10 | 4% |
| **crypt_chest** | L15-80 (uncommon, near undead) | Decaying bone-clasped | undead-themed loot (corpses, scrolls) | 5% |
| **ornate_chest** | L25-70 (rare) | Engraved + filigree | magic 50, accessory 30, gear 20 | 12% |
| **gilded_chest** | L50-90 (rare) | Gold-leafed, heavy | magic 40, gear 30, accessory 20, gold 10 | 20% |
| **reliquary** | L60-100 (very rare) | Bone, iron, sealing wax | artifact-themed, high unique chance | 35% |
| **dragon_hoard** | L70-100 (very rare) | Massive coin-piled crate | gold 30, gear 40, magic 30 | 40% |

**(13 templates — one over budget, but the variety justifies it. Can prune `pirate_cache` if you want exactly 12.)**

---

## Spawn weights per floor band

Each floor rolls 1-3 chests; each chest picks a template weighted by floor band:

| Floor | Common templates | Uncommon | Rare | Very rare |
|---|---|---|---|---|
| L1-15 | wooden 60, apothecary 30, jewelry 10 | merchant 5, pirate 5 | — | — |
| L16-30 | wooden 30, iron 30, apothecary 20, jewelry 10, scholar 10 | warlord 10, ornate 5, pirate 5 | — | — |
| L31-50 | iron 30, apothecary 20, jewelry 15, scholar 15 | warlord 15, ornate 15, gilded 5 | gilded 5 | — |
| L51-70 | iron 20, apothecary 15, scholar 15, jewelry 10 | warlord 15, ornate 15, gilded 10 | reliquary 5, dragon 3 | — |
| L71-90 | apothecary 10, jewelry 10, scholar 15 | warlord 10, ornate 15, gilded 20 | reliquary 10, dragon 8 | dragon_hoard 5 |
| L91-100 | — | scholar 10, warlord 10, ornate 15, gilded 25 | reliquary 20, dragon 15 | dragon_hoard 10 |

So early floors mostly wooden/apothecary/jewelry; late floors heavy on ornate/gilded/reliquary/dragon.

---

## Math: simulated uniques per 100-floor run

Assumptions:
- 1.7 chests per floor average
- Player averages chain 3 (median competence)
- Per-chest rare roll = (template rare%) × (chain_mult)
- Plus floor unique drops (current 0.5%/room × 20 rooms = 10%/floor — keep for now)
- Plus boss fixed drops (~5 per run from named drops)

**Chest uniques per run** (chain 3 baseline):
- L1-15 (15 floors): mostly wooden/apothecary @ 1-2% rare. ~25 chests × 1.5% × 1.0 = ~0.4 uniques
- L16-30 (15): mix, ~3% avg. 25 chests × 3% = ~0.8
- L31-50 (20): jewelry/ornate creeping in, ~5% avg. 34 × 5% = ~1.7
- L51-70 (20): ornate/gilded mid. ~8% avg. 34 × 8% = ~2.7
- L71-90 (20): gilded/reliquary common. ~15% avg. 34 × 15% = ~5.1
- L91-100 (10): late-game heavy. ~22% avg. 17 × 22% = ~3.7

**Total chest uniques: ~14.4**

**Plus floor drops**: 0.5%/room × 20 rooms × 100 floors = 10 uniques (but if we also reduce floor drop rate per other proposal: ~3-5 uniques)

**Plus boss fixed drops**: ~5 uniques

**Sum: ~22-25 uniques per run at chain 3.**

That's higher than target 10-15. Three options to tighten:

1. **Reduce floor drop rate**: 0.5%/room → 0.15%/room (cuts floor uniques to ~3)
2. **Reduce template rare%**: cut each template's rare% by 30-40%
3. **Both**

If we apply (1) AND mild (2), total per run lands around 13-17 uniques. That hits the user's "rare and special" target while preserving the per-chest excitement.

**Recommendation**: Apply both — reduce floor drops AND mildly trim rare% on the high-tier templates (reliquary 35→25, dragon_hoard 40→30, gilded 20→15).

After trim:
- Chest uniques: ~10
- Floor drops: ~3
- Boss fixed: ~5
- **Total: ~18 per run**

Still close. To hit exactly 10-15, drop chain-3 multiplier from 1.0× to 0.75× (so median player gets 75% of baseline rare odds; chain 5 still gets 2.0× = 1.5× of pre-trim). That brings total to **~13 per run**.

---

## Implementation surface

| File | Change |
|---|---|
| `data/chest_templates.json` (NEW) | 12 template specs with loot tables |
| `src/container_system.py` | Replace `_generate_loot` + add template lookup; switch quiz to escalator_chain |
| `src/dungeon.py` | Update chest spawn to use template weights per floor band |
| `src/items.py` Container class | Add `template_id` field |
| Tests | Simulate balance, verify ~13 uniques/run, no template orphans |

Estimated work: 1 medium subagent for spec + impl, ~2-3 hours.

---

## Open call: confirm before I build

Three things to confirm:

1. **13 templates OK** (one over budget), or prune to 12 by dropping `pirate_cache` (or another you'd rather lose)?
2. **Balance trim**: apply the recommended floor-drop cut + high-tier rare% trim + chain-3 multiplier 1.0→0.75? Target ~13 uniques/run.
3. **Chain 0 = chest stays locked** (current behavior) is preserved — if player fails the chain entirely, the chest doesn't open. Good?
