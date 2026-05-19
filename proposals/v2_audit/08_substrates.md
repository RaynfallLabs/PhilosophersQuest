# V2 Audit — Substrates (chest templates / containers / ammo / lockpicks)

Scope:
- `data/chest_templates.json` (12 entries — active)
- `data/items/container.json` (10 entries — **legacy, never loaded**)
- `data/items/ammo.json` (14 entries — active)
- `data/items/lockpick.json` (5 entries — only `lockpick[0]` is actually used)

Tests: **476 passed in 63.75s.** No edits applied — all findings below are report-only because the live data is clean and the dead files do not break anything.

---

## chest_templates.json — 12 entries — PASS

All required fields present on every template (id, name, symbol, color, lore, tier, quiz_tier, gold_range, trap_chance, loot_table, rare_chance_chain3, spawn_weight_by_band). All 6 floor bands have positive-weight templates:

| Band      | Total | Spawnable templates |
|-----------|-------|---------------------|
| L1_15     | 100   | 4 (wooden, jewelry, apothecary, merchant) |
| L16_30    | 135   | 8 |
| L31_50    | 130   | 9 |
| L51_70    | 133   | 11 (peak variety) |
| L71_90    | 128   | 10 |
| L91_100   | 95    | 6 (scholar/warlord/ornate/gilded/reliquary/dragon) |

Loot table categories used across all templates — **every key is recognized** by `container_system._COMMON_CATEGORIES` and `cat_classes`:

```
accessory, ammo, armor_common, artifact, gold_bonus, ingredient,
magic, potion, scroll, shield_common, spellbook, wand, weapon_common
```

`rare_chance_chain3` ladder is monotonic by tier and matches the prompt's reference values:

```
wooden_chest        tier 1   0.01
apothecary_chest    tier 1   0.02
iron_lockbox        tier 2   0.03
merchant_strongbox  tier 2   0.03
scholar_satchel     tier 3   0.04
jewelry_box         tier 2   0.05    (slight outlier — see notes)
crypt_chest         tier 3   0.05
warlord_warchest    tier 3   0.06
ornate_chest        tier 4   0.12
gilded_chest        tier 4   0.20
reliquary           tier 5   0.35
dragon_hoard        tier 5   0.40
```

`pre_identified: true` appears **only** on `merchant_strongbox`, as required.

### Observations (no fixes applied)
- `jewelry_box` is tier 2 but has rare=0.05 (= tier 3 crypt_chest). Defensible — accessory-only templates are intentionally more generous since they bypass the gear-common floor. Flagging only.
- `apothecary_chest` has identical `spawn_weight_by_band: 25` across L1–90 then 0 at L91_100 — by design (apothecary is band-agnostic), but the abrupt 25→0 cutoff at floor 91 means the deep-dungeon player loses access to one of two ingredient chests (`gilded_chest` doesn't carry ingredients). If endgame alchemy is in scope this is a real loss; if not, leave it.
- `merchant_strongbox` carries a flat 5/5/5/5/5 across L1–90 → 0 at L91_100. Pre-identified loot late game would still be useful; intentional cap.
- All 12 templates pass `tests/test_chest_templates.py` (the 8 tests there cover load shape, band coverage, chain curve, chain 0 empty, chain 5 fat, rare-scales-with-chain, and the 5-run 12–22 unique target).

---

## container.json — 10 entries — LEGACY / DEAD CODE

**Verdict: file is no longer loaded anywhere in src/.** Grep confirms zero call sites for `load_items('container')`. The `Container` class is now instantiated **only** from `chest_templates.json` via `dungeon.pick_container()` (dungeon.py:1334) which synthesizes a `defn` dict directly. The 10 entries (`wooden_chest`, `trapped_chest`, `iron_chest`, `spiked_chest`, `steel_vault`, `shock_trap_vault`, `enchanted_coffer`, `cursed_coffer`, `dragon_hoard`, `inferno_chest`) are pre-rebuild artifacts.

Note: there is a naming collision — `wooden_chest` and `dragon_hoard` exist in *both* container.json and chest_templates.json with different fields. Because nothing loads container.json, this collision is harmless today, but if anyone later writes `load_items('container')`, they will get the legacy entries (different gold ranges, different trap structures).

### Report-only recommendation
- **Safe to delete `data/items/container.json`.** The `'container': Container` entry in `_CLASS_MAP` (items.py:547) can stay — it's referenced by the Container class itself, not by the file. Not removing the file here per repo rule "don't delete validated content without asking."
- If kept, no action needed — it's inert.

---

## ammo.json — 14 entries — PASS with notes

All 14 entries have the required fields (id, name, symbol, color, weight, ammo_type, tier). Standard tier ladder is clean:

```
Tier 1 (lvl 1+):   iron_arrow,        iron_bolt          +0 dmg, 10-30/25 count
Tier 2 (lvl 21+):  steel_arrow,       steel_bolt         +1 dmg, 8-24/20  count
Tier 3 (lvl 41+):  hardened_gold_*,                      +2 dmg, 6-18/16  count
Tier 4 (lvl 61+):  diamond_*,                            +3 dmg, 5-15/12  count
Tier 5 (lvl 81+):  dragonbone_arrow,  adamantine_bolt    +5 dmg, 4-12/10  count
```

Damage progression `0, 1, 2, 3, 5` is the gentle geometric the curve expects. Counts taper inversely with tier so power × ammo stays roughly flat per find. Float spawn-weight tables per ammo cover the full 1–100 floor range.

### Special ammo (3 named — not flagged is_unique)
- `arrows_of_eros` — tier 3, +3 dmg, 3-4 count, lvl 20+, value 2000
- `arrows_of_artemis` — tier 5, +8 dmg, 4-6 count, lvl 30+, value 5000
- `bolts_of_zeus` — tier 5, +15 dmg, 2-3 count, lvl 55+, value 7000

These have `containerLootTier` and `floorSpawnWeight` tuned for rarity but **do not carry `is_unique: true`**. Consequence: in `container_system._build_unique_pool` they are filtered OUT of the unique pool, so the chest unique-slot will never roll them. They can still drop on the floor via `dungeon.spawn_items()` magic_pool (which doesn't gate on is_unique), but the discovery feel is "random rare drop" rather than "one of N uniques in this run."

If the intent is that gilded_chest / dragon_hoard's `ammo` category can pull these as the rare slot, add `is_unique: true` to those three entries. **Reporting only — no edit.** The current behavior is internally consistent.

### Shotgun shell (intentional)
- `shotgun_shell` — `min_level: 9999`, tier 3, +4 dmg, 10-20 count. Confirmed Ash-only (hero special at `hero_specials.py:241`, welcome_screen.py:215 starting kit). The 9999 gate correctly prevents floor spawn. Working as designed.

---

## lockpick.json — 5 entries — 4 of 5 are ORPHANS

The CLAUDE.md memory and `container_system.py` docstring both state "The Master Lockpick is a permanent inventory item; no charges to track." Reality is more confused:

- `main.py:1139` does `picks = load_items('lockpick'); master = copy.copy(picks[0])`. JSON ordering means `picks[0]` is the **basic `lockpick`**, NOT the master lockpick. The starting inventory gets the basic one.
- The starting lockpick has `durability: 5/5, ds=1, df=2` — but **no code path consumes durability.** Grep for `durability` finds only `items.py:339-345` (constructor) and `ui.py:280-289` (display). There is no decrement anywhere.
- `master_lockpick`, `mithril_lockpick`, `diamond_lockpick`, `philosophers_pick` are not referenced in src/ at all (only in `data/patch_items.py`, which is offline tooling).
- No chest template's `loot_table` includes `lockpick`. They cannot drop from chests. They cannot drop from monsters (no `treasure.unique_drop_id` references). They cannot drop from `dungeon.spawn_items` (which only loads `weapon/armor/shield/accessory/wand/scroll/spellbook/ammo`).

### Report-only recommendations
1. **The 4 non-basic lockpicks are dead content.** Safe to delete from `data/items/lockpick.json`, or alternatively keep just `philosophers_pick` and add a chest-template `loot_table` entry (`reliquary` would be thematic). Status quo: they exist as inert JSON.
2. **`picks[0]` in main.py is brittle.** If anyone reorders the JSON dict, the starting pick changes. The fix is `next((p for p in picks if p.id == 'master_lockpick'), picks[0])` — but this would also change the displayed name on the HUD. Since durability is never consumed and the system documents "Master Lockpick is permanent," the simplest cleanup is:
   - Either reduce `data/items/lockpick.json` to a single `master_lockpick` entry and rename it `lockpick` for clarity, or
   - Strip the `Lockpick` class's durability fields and the UI display block since durability is no longer a game mechanic.
3. **Durability UI is misleading.** `ui.py:280-289` shows `5/5` next to the lockpick name, implying degradation. Either remove the UI block or replace with a static "Lockpick" indicator.

None of these are bugs that block play — the lockpick "just works" because of how chain-economics has supplanted durability. They're cleanup opportunities.

---

## Summary

### What's in good shape
- **chest_templates.json**: 12 templates, every band covered, every loot category recognized by container_system, rare ladder sensible, pre_identified flag correctly scoped. Already validated by 8 dedicated tests.
- **ammo.json**: 14 entries, all required fields, clean tier curve, intentional Ash-only shotgun gate.

### Legacy / cleanup candidates (NOT TOUCHED — report-only per repo rules)
- `data/items/container.json` (10 entries): completely unloaded; safe to delete; ghost-collides with chest_templates.json on `wooden_chest`/`dragon_hoard` ids.
- `data/items/lockpick.json` entries 2-5 (`master_lockpick`, `mithril_lockpick`, `diamond_lockpick`, `philosophers_pick`): unreachable in current code; no drop path, no chest category.
- `main.py:1139` `picks[0]` is order-dependent — comment claims "Master Lockpick" but code grabs basic `lockpick`. Self-healing because durability isn't consumed, but documentation/UX mismatch.
- `ui.py:280-289` displays lockpick durability which the game never decrements.
- 3 named ammo entries (`arrows_of_eros`, `arrows_of_artemis`, `bolts_of_zeus`) lack `is_unique: true`, so they can never be the rare slot in a chest — only floor spawns.

### Broken refs
- None. Every active code path resolves cleanly.

### Tests
- **476/476 passed.** No edits made → no regression risk.

### Files touched
- None (audit pass only).

### Files referenced
- `C:\Users\brand\Documents\PhilosophersQuest\data\chest_templates.json`
- `C:\Users\brand\Documents\PhilosophersQuest\data\items\container.json`
- `C:\Users\brand\Documents\PhilosophersQuest\data\items\ammo.json`
- `C:\Users\brand\Documents\PhilosophersQuest\data\items\lockpick.json`
- `C:\Users\brand\Documents\PhilosophersQuest\src\container_system.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\items.py` (Container, Ammo, Lockpick classes; load_chest_templates)
- `C:\Users\brand\Documents\PhilosophersQuest\src\dungeon.py:1180-1380` (pick_container, band helper)
- `C:\Users\brand\Documents\PhilosophersQuest\src\main.py:1139` (starting pick), `src\main.py:4961-4964` (Ammo/Lockpick label)
- `C:\Users\brand\Documents\PhilosophersQuest\src\ui.py:280-289` (lockpick durability UI — orphaned)
- `C:\Users\brand\Documents\PhilosophersQuest\tests\test_chest_templates.py`
