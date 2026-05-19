# Loot + Dungeon Audit — 2026-05-19

Two systems audited per the user's request: loot/treasure spawn and dungeon generation. Two clear bugs already fixed inline (committed). Larger design recommendations below for review before any further changes.

---

## Shipped fixes (commits `cd44949`, this commit)

### 1. Monster + chest drop pool leak (CRITICAL)

**Problem**: `data/items/weapon.json`, `armor.json`, `shield.json` contain ONLY uniques (commons are template-instantiated via `pick_random_*_for_floor` helpers in `items.py`). Both `_spawn_treasure_item` (monster kill) and `_generate_loot` (chest open) used `load_items('weapon')` as their "common" pool — which is empty for those classes. So:

- Every weapon/armor/shield dropped by a monster's `item_chance` roll was a **legendary**
- Chests fell through to `unique_pool` even at T1 because the regular pool had no weapon/armor/shield commons in it

This explains the user's "we have so much content but it feels off." Uniques were over-spawning.

**Fix**:
- `_spawn_treasure_item` now uses `pick_random_weapon_for_floor` / `pick_random_armor_for_floor` / `pick_random_shield_for_floor` for those classes; explicitly filters `is_unique` from the accessory/wand/scroll pool.
- `_generate_loot` injects `container_tier + 1` template-rolled commons per applicable class so the common pool is never empty for gear.

**Verified**: T3 chest at floor 30 now drops 89% common / 11% unique (matches design intent of 8% unique chance per pick at T3).

### 2. Plant ingredients didn't spawn on floor

**Problem**: User reported "food items, for ingredients, should be spawning on floor." Audit found `food.json` (17 entries) spawns on floor at 2-4/level, but `ingredient.json` (325 entries) only came from harvested corpses. Plant-source ingredients (mushrooms, herbs, fungi, sap, roots — ~14 entries) should appear naturally on dungeon floors.

**Fix**: Added a 1-3-per-floor plant-ingredient spawn pass in `dungeon.py:spawn_items`, gated by keyword match against the ingredient name (mushroom/herb/berry/leaf/root/fungus/moss/flower/seed/grain/wheat/grass/vine/spice/lichen/bark/sap). Monster-derived ingredients (meat, glands, hides) still come from harvest-only.

---

## Audit findings — Loot

### Spawn density per floor (current, after fixes)

| Source | Volume | Notes |
|---|---|---|
| Common gear (weapon/armor/shield) | 33% × rooms × split (60/20/15/5) | Template+material, bell-curve weighted |
| Magic items (accessory/wand/scroll/spellbook/ammo) | 25% × rooms | Bell-curve weighted |
| Floor uniques | 0.5% × rooms (~1-in-25 floors) | Rare lucky finds |
| Containers (chests) | 1 guaranteed + 55%/25%/11% diminishing | Tiered loot, NOW correctly weighted common-vs-unique |
| Food | 2-4 per floor | Bread, fruit, healing herbs |
| Plant ingredients | 1-3 per floor (NEW) | Mushrooms, herbs, fungi for cooking |
| Potions | 1-2 per floor | Bell-curve weighted |
| Soul Sphere | 5% per floor | Quest mechanic |
| Special room (1 max) | 35% per floor | Treasury/library/shrine/zoo/beehive/etc. |
| Mystery altar | Conditional per `mystery_system` | Floor-gated events |
| Travelling merchant | Conditional | Floor-gated NPCs |

### Monster drops

- **522 monsters total, 514 have `item_chance > 0`** (98% can drop items)
- **26 have `unique_drop_id`** (fixed legendary drops, e.g., Fafnir → Fafnir's Blood). All 26 resolved cleanly.
- **26 have `boss_scroll_id`** (fixed boss reward scrolls). All 26 resolved cleanly.
- Item_chance distribution: 0 (8), 0-0.1 (66), 0.1-0.3 (152), 0.3-0.6 (209), 0.6+ (87). 87 monsters with >60% drop chance is high — most are bosses/mini-bosses which is correct, but worth verifying that common trash isn't sitting at 60%+.

### Recommendation: Chest as "the big win"

User specifically said chests should be the FLOOR HIGHLIGHT. Current chest math (after fix):

| Tier | Categories | max_tier | Legendary | Unique chance |
|---|---|---|---|---|
| 1 | weapon/armor/ammo/potion | 2 | no | 0% |
| 2 | + accessory/shield | 3 | no | 2% |
| 3 | + scroll/wand | 4 | no | 8% |
| 4 | + spellbook | 5 | no | 20% |
| 5 | all | 5 | YES | 40% |

This is well-designed. The fix to the common pool means T4-T5 chests now actually feel like the "BIG WINS" — high-tier commons with occasional legendaries — rather than just dumping randomly.

**Suggested adjustments** (optional):
- Bump T1-T2 chest extra-item chance from default to guarantee 2-3 items minimum, so even early chests feel rewarding.
- Consider a "deluxe roll" on T4-T5: guaranteed 1 unique slot IF the player has cleared certain milestones (e.g., killed a boss this run). Rewards progression.
- Audit the 87 monsters with >60% item_chance to make sure they're bosses/notable foes, not common trash.

---

## Audit findings — Dungeon Generation

### Map sizing (the core problem)

| Metric | Philosopher's Quest | NetHack |
|---|---|---|
| Map size | 80×50 = **4,000 tiles** | 80×21 = 1,680 tiles |
| Room count | 8 (L1) → 16 (L9+) | 5-9 |
| Room area % | **13-20%** of map | ~10% but on smaller map |
| Floor% (rooms + corridors) | 16-21% non-maze | ~50% |
| Result | Big map, sparse rooms, long corridors | Compact map, dense events |

PQ maps are **2.4× the area of NetHack** with similar room counts. The result: long, empty corridors between meaningful encounters. User's "too big/empty, padding feels" is structurally correct.

Levels 10/30/50/70/90 are **maze levels** (47% floor) — these are intentional and probably fine.

### Special rooms

10 types defined (treasury, library, shrine, monster_den, zoo, beehive, graveyard, barracks, swamp, throne_room) — great variety. BUT:

- Only **35% chance** of a special room per floor
- Only **ONE special room max** per floor
- So 65% of floors have zero "special" content beyond random spawns

NetHack lets multiple special rooms (shop + vault + zoo on same level is common).

### Stairs / connectivity

- Stairs UP in first room, DOWN in last room — linear path
- 70% door placement
- Secret doors + hidden chambers (good!)
- Vault generation (good!)
- Extra connections for loops (good — prevents tree-only layouts)

### Recommendations — Dungeon (NEED YOUR REVIEW)

**Option A — Shrink the map (recommended)**:
- 80×50 → **60×35 = 2,100 tiles** (closer to NetHack ratio)
- Same room count → much denser
- Less corridor walking, more "meat per step"
- Risk: feels cramped if player likes spacious layouts. Could offer per-build "spacious" alternative.

**Option B — Pack more content into the existing map**:
- Allow **2 special rooms** per floor (45-50% chance of first, then 30% chance of second)
- Add more themed mini-events to "empty" rooms: bookshelves, alchemy tables, prayer alcoves with small interactables
- Increase corridor encounters (occasional traps, ambushes, gold piles in corridors)

**Option C — Both, lighter on each**:
- 70×40 = 2,800 tiles (smaller but not too much)
- 2 special rooms allowed
- Higher room count cap (16 → 20)

**Option D — Themed levels** (NetHack-like):
- Every 5th non-boss level is themed: "fungal forest" (all rooms have plant ingredients + fungus monsters), "abandoned library" (heavy scroll/spellbook drops, ghostly librarians), "ancient bazaar" (merchants, friendly traders, locked chests), "infested mine" (close-packed corridors, vermin packs)
- Adds variety without changing base gen
- Risk: more code, more JSON, but BIG fun payoff

### Recommendation order

If you want one swing: **A + D**. Shrinking the map fixes the structural "feels padded" complaint; themed levels solve the "rooms feel like filler" complaint. Together they give a NetHack-like density of memorable floors without restructuring the BSP generator.

If conservative: just **B** (pack more content into existing maps), evaluate, decide on size change later.

---

## Open questions for the user

1. **Map size — A, B, C, or D?** Or keep as-is and tune content only?
2. **Themed levels** — appetite for adding 3-5 themes (fungal forest, abandoned library, etc.)? Each is ~50-100 lines of dungeon-gen code + small JSON additions.
3. **Special room frequency** — allow 2 per floor by default?
4. **Monster drop curve** — review the 87 monsters at >60% item_chance? Might find common trash over-tuned.
5. **Chest "big win" emphasis** — guarantee 2-3 items minimum at T1-T2 chests?
