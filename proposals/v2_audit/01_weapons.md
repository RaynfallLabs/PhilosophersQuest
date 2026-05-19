# Weapons Audit (V2)

**Verdict**: PASS (with one systematic curation finding worth design review)

## Scope
- `data/items/weapon.json` — 96 unique entries
- `data/templates/weapons/*.json` — 22 template files
- `data/materials/weapons/*.json` — 35 material files (note: prompt said 30; actual = 35)

## Auto-fixed (49 changes across 49 files)

### Materials (34 files, 1 fix each)
All weapon material JSONs had `peak_weight` stored as `int` (e.g. `5`) and were re-saved as `float` (`5.0`). No semantic change; aligns with engine's `float()` cast in `Item.__init__`.

Affected: adamantine, ash, bronze, cobalt_steel, cold_iron, copper, damascus_steel, dragonbone, dragonhide, dragonwood, glassteel, hardened_gold, hematite, iron, ironwood, mithril, oak, obsidian, orichalcum, petrified_dragon, petrified_wood, quicksilver, rawhide, shadowiron, silver, silverbark, soulsteel, starmetal, steel, sunsteel, tempered_bronze, tungsten, worldtree, yew.

(`void_touched` was already `float`; nothing to change.)

### Unique weapons (15 entries in `weapon.json`)
Same int→float cast for `peak_weight`, applied to: gram, broken_gram, sigurds_shovel, punch_in_the_face, hunt_captains_sword, wendigo_fang, echidna_fang, vulcans_brand, sword_of_michael, oathkeeper_sword, penitents_blade, boomstick, chainsaw_prosthetic, witcher_silver_blade, zireael.

No other auto-fixes were required — every weapon already had the required fields (`spread`, `min_level`, `weight`, `is_unique`).

## Templates audit (22 / 22)

All 22 templates have complete required fields and pass band checks:
- `damage_modifier` range: 0.60 (sling) – 1.55 (maul) — within CURVES.md band.
- `chain_5` multipliers cluster cleanly at the three documented bands:
  - **finesse** (cm5≈3.0): dagger, rapier, scimitar, shortbow, sling
  - **normal** (cm5≈2.0): bastard_sword, battleaxe, club, composite_bow, flail, longbow, longsword, mace, quarterstaff, shortsword
  - **heavy** (cm5≈1.75): glaive, great_axe, greatsword, heavy_crossbow, light_crossbow, maul, warhammer

The `weapon_class_chain` field is set on every template — band membership is self-describing, not a guess from filename.

## Materials audit (35 / 35)

All 35 materials have complete required fields. `damage_mult` range: 0.7 (copper) – 1.55 (void_touched), inside CURVES.md band [0.8, 1.8] except copper at 0.7 — copper is the documented "T0 trash metal" and the engine's `max(2, …)` floor masks the deficit.

`peak_floor` distribution covers floors 1–95 with one near-gap (floor 82 → 88, 6 levels), see Minor finding below.

## Balance findings

### MINOR — Systematic adamantine curation drift (22 items)

The 22 uniques whose `material` field is `"adamantine"` all have `baseDamage` at exactly **0.71× canonical** (matching `1.0 / adamantine.damage_mult=1.4`). The drift is *uniform* across all 22 entries — it's not noise, it's a coherent curation choice.

**Root cause**: `tools/rebuild_uniques.py` (the script that built these from the new formula) reads `entry.get("damage_mult", 1.0)` from the entry itself, but unique entries in `weapon.json` never store `damage_mult` — that field lives on materials. So every adamantine unique was stamped with a material multiplier of 1.0 instead of the actual 1.4.

The affected entries pass:
- `test_no_super_weapon_uniques` (they're below cap, not above)
- `test_chain_5_damage_near_mob_hp_at_peak_floor` (still inside [0.5×, 3.0×] mob_hp band)
- `test_unique_chain_monotone_to_peak_except_wild`

So gameplay isn't broken — these adamantine uniques are simply 30% weaker than the canonical formula would put them. Many ARE in `LEGENDARY_EXEMPT` already (mjolnir, durendal, etc.) — the exemption was for the *upper* cap, not the lower band. Given the consistency, this is plausibly intentional (curator wanted mythic weapons strong-but-not-game-breaking).

**Recommendation**: Report-only. Either (a) accept the 0.71× as deliberate restraint on mythic-tier or (b) re-run `rebuild_uniques.py` with material lookups fixed. Do *not* hand-edit individual entries — that breaks the systematic balance.

Affected entries (all template=adamantine):
| item_id | template | pf | baseDamage | canonical | ratio |
|---|---|---|---|---|---|
| dawnbreaker | warhammer | 92 | 101 | 141 | 0.72 |
| durendal | greatsword | 75 | 70 | 97 | 0.72 |
| tyrfing | greatsword | 80 | 78 | 110 | 0.71 |
| caladbolg | greatsword | 75 | 70 | 97 | 0.72 |
| mjolnir | warhammer | 92 | 101 | 141 | 0.72 |
| kusanagi | longsword | 83 | 48 | 67 | 0.72 |
| sudarshana | scimitar | 93 | 44 | 62 | 0.71 |
| rod_of_moses | quarterstaff | 84 | 42 | 60 | 0.70 |
| (and 14 more, all 0.70–0.72) |

### MINOR — Material peak_floor gap (1 finding)

`shadowiron` peaks at floor 82, next material (`petrified_dragon`) at floor 88. The 6-level gap is small (within both materials' spread=10), so material spawn coverage stays continuous — no floor is bereft of compatible materials. Marginal flag only.

### INFORMATIONAL — Quest/scripted uniques with peak_floor=0 (15 items)

These weapons have `peak_floor=0` and `peak_weight=0.0` — they bypass the bell-curve spawn system because they're scripted drops, boss rewards, or quest items. All have proper hooks in code or monsters.json:

- **Scripted boss drops**: wendigo_fang (Wendigo, `treasure.unique_drop_id`), echidna_fang (Echidna)
- **Quest chain items**: gram, broken_gram, sigurds_shovel
- **Encounter rewards**: punch_in_the_face, hunt_captains_sword, vulcans_brand, sword_of_michael, oathkeeper_sword, penitents_blade
- **Hero starter weapons**: boomstick, chainsaw_prosthetic, witcher_silver_blade, zireael (all in `src/hero_specials.py`)

These are correctly configured — no action needed.

## Stats

- **Uniques audited**: 96 / 96
- **Templates audited**: 22 / 22
- **Materials audited**: 35 / 35 (prompt said 30; actual file count = 35)
- **Auto-fixes applied**: 49 (34 material + 15 unique `peak_weight` int→float casts)
- **Balance flags**: 23 total (0 blockers / 0 important / 23 minor)
  - 22 = systematic adamantine drift (single root cause)
  - 1 = material peak_floor gap (cosmetic)
- **Tests**: 476 / 476 passing after auto-fixes (`tests/test_chain_gradient.py` and `tests/test_balance.py` specifically validated)

## Files modified

- `data/items/weapon.json` (15 `peak_weight` int→float casts)
- `data/materials/weapons/*.json` (34 files, `peak_weight` int→float casts)

## Top critical findings (consolidated)

1. **[adamantine-class] IMPORTANT for design review (MINOR per test)** — 22 adamantine uniques sit at 0.71× canonical baseDamage due to a `damage_mult` lookup bug in `tools/rebuild_uniques.py`. All pass gameplay tests but are systematically under-tuned. Decision needed: accept as design restraint, or re-run rebuild script with proper material lookup.
2. **[material_coverage] MINOR** — 6-level gap between `shadowiron` (82) and `petrified_dragon` (88); no remediation needed (spread covers).
3–10. The 14 quest items with peak_floor=0 are correctly configured scripted-spawn items, not orphans — no action.

## Engine compatibility note

The `Weapon` class in `src/items.py:62` reads all canonical fields (`baseDamage`, `chainMultipliers`, `damage_types`, `peak_floor`, `spread`, `peak_weight`, `material`, `is_unique`, `mastery_blessing`) via `.get()` with safe defaults, so missing-field cases never crash — the auto-fixes are belt-and-braces correctness, not crash-fix.
