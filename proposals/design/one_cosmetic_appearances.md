# One Cosmetic Appearance Per Functional Type

**Status:** Proposal (audit complete; no live files changed)
**Date:** 2026-06-07
**Scope:** `data/items/accessory.json`, `src/items.py`, `src/dungeon.py`, `src/main.py`, `src/save_system.py`

---

## Headline

The duplication bug is **isolated to rings and amulets** (`data/items/accessory.json`). Wands, potions, and scrolls are already 1:1 (one functional type → one fixed appearance). For accessories there are up to **8 separate JSON items per functional type** (e.g. 8× "ring of warning", 7× "ring of searching", 6× "ring of telepathy"), each spawning independently, so a single run can rain four differently-named "ring of searching" items that are mechanically identical.

**Recommended fix:** Collapse each *purely cosmetic* accessory group to **one functional definition** carrying a **pool of appearance strings**, and assign **one appearance per functional type per run** via a game-start shuffle (mirrors the existing `_lore_levels` per-run randomization and the classic NetHack/roguelike pattern). Identification already keys to the functional type via `known_class_ids` + `get_mastery_class`, so the mystery gameplay is preserved unchanged.

**Effort:** ~1 focused session. The data merge is the bulk of the work (mechanical JSON edit, scriptable); the code change is small (~60 lines across 3 files) because the type-keyed identification machinery already exists.

---

## Findings (the three questions)

### 1. Are the variants purely cosmetic, or do some differ mechanically?

**Mixed — and this is the load-bearing nuance.** Grouping every accessory by display `name`:

| Group pattern | Variants | Effects within group |
|---|---|---|
| `ring of warning` | 8 | **identical** (`status: warning`) |
| `ring of searching` | 7 | **identical** (`status: searching`) |
| `ring of telepathy` | 6 | **identical** (`status: telepathy`) |
| `ring of regeneration` | 5 | **identical** (`status: regenerating`) |
| `ring of {fire,cold,shock,poison,sleep} resist` | 2 each | **identical** |
| `amulet of {warning,searching,telepathy}` | 2 each | **identical** |
| **`ring of {strength,con,dex,int,wis,per}`** | 4 each | **DIFFER — tiered** |
| **`amulet of {strength,con,dex,int,wis,per}`** | 2 each | **DIFFER — tiered** |

The stat rings are **not cosmetic variants** — they are **power tiers wearing the same name**. Example, `ring of strength`:

| id | unidentified_name | amount | min_level | quiz_tier | peak_floor |
|---|---|---|---|---|---|
| `ring_strength_iron` | iron ring | **+1** | 1 | 1 | 6 |
| `ring_strength_steel` | steel ring | **+2** | 8 | 2 | 13 |
| `ring_strength_adamantine` | adamantine ring | **+3** | 25 | 3 | 30 |
| `ring_strength_mithril` | mithril ring | **+3** | 25 | 3 | 30 |

So today a +1 and a +3 strength ring **both display as "ring of strength"** — a *second, pre-existing bug*: the names don't disambiguate power. (And because `get_mastery_class` slugs them all to `ring_of_strength`, identifying the +1 already reveals the *name* of the +3 — but they keep separate `known_item_ids`, so the (n/5) ID markers and stacking diverge.)

**Implication for the fix:** the cosmetic groups should collapse to ONE item. The stat groups should **NOT** be flattened to one effect — they must either (a) keep distinct, *disambiguated* names (e.g. "ring of strength +1 / +2 / +3", or "lesser/greater/master ring of strength"), or (b) collapse to one functional type with a single canonical amount. Recommended: **rename to disambiguate (option a)** so the power tiers remain but stop sharing a name; then they too become 1:1 (one appearance per distinct name) and are swept up by the same appearance-pool mechanism. The mithril/adamantine pair (both +3) is a genuine cosmetic dupe within a tier and can merge.

### 2. Is there any existing per-game appearance randomization?

**No.** Each variant is a fixed-appearance JSON item. `unidentified_name` is a static string baked into the definition (`items.py:627` `Accessory.__init__`, also Wand/Potion/Scroll). At spawn (`dungeon.spawn_items`, line 1390-1401) the loader pulls **every** accessory variant into `magic_pool` and `_place_one` drops them independently. Nothing shuffles or assigns appearances per run. (The only per-run randomization precedents are `self._lore_levels` and the carrot/unicorn/cow target floors in `main.__init__` — good templates to follow.)

The identification side, however, is **already type-keyed and ready**:
- `_display_name` (`main.py:5403`) shows `item.name` if `item.identified` **or** `item.id in known_item_ids` **or** `get_mastery_class(item) in known_class_ids`; else `item.unidentified_name`.
- `_propagate_identification` (`game_magic.py:3718`) adds the seed item's `get_mastery_class(...)` to `known_class_ids`, so identifying ONE copy already names the whole class.
- `reconcile_item_identification` (`player.py:1106`) stamps freshly-acquired copies of a known type.

This means the *recognition* model the user wants ("know one Ring of Searching, know them all") is **already implemented**. The bug is purely that **multiple distinct appearances exist for one type and all spawn**, defeating the "exactly one mundane description" intent and cluttering the pack.

### 3. Functional types with redundant variants + counts

Purely-cosmetic redundancy (the real targets):

```
ring of warning        8   ring of fire resist    2
ring of searching      7   ring of cold resist    2
ring of telepathy      6   ring of shock resist   2
ring of regeneration   5   ring of poison resist  2
                           ring of sleep resist   2
amulet of warning      2   amulet of searching    2   amulet of telepathy 2
```

Tiered (same name, different power — rename to disambiguate, don't flatten):

```
ring of strength/constitution/dexterity/intellect/wisdom/perception   4 each
amulet of strength/constitution/dexterity/intellect/wisdom/perception 2 each
```

Wands (91), potions (39), scrolls (50): **0 redundant groups** — already 1:1.

> **Note on the prior stopgap:** spawn weights were divided down so a 7-variant group doesn't out-spawn a 1-variant type (visible as `floorSpawnWeight` 11 for searching vs 20 for strength, peak_weight 0.4 flat). That balances *spawn frequency* but does nothing about the core problem — multiple looks still exist and still drop. It is superseded by this fix and the per-type weight can be restored to its natural value once each type is a single item.

---

## The Fix

### Design

Adopt the classic roguelike model, scoped to accessories:

1. **One functional definition per type.** Each cosmetic group becomes a single JSON entry. Its `unidentified_name` is no longer a fixed string but is *assigned at game start* from a shared appearance pool.
2. **A per-run appearance pool**, shuffled once, dealing exactly one appearance to each functional type. This run "malachite ring" = ring of searching; next run maybe "silver ring". Mystery preserved.
3. **Identification stays keyed to the functional type** (already true via `known_class_ids`/`get_mastery_class`). No change to the identify quiz flow.

### A. Data change — `data/items/accessory.json`

**A1. Collapse the cosmetic groups.** For each of {warning, searching, telepathy, regeneration, the 5 resist rings, the 3 cosmetic amulets}, keep **one** entry per type and delete the rest. Suggested canonical ids: `ring_of_warning`, `ring_of_searching`, `ring_of_telepathy`, `ring_of_regeneration`, `ring_of_fire_resist`, … `amulet_of_searching`, etc. Each canonical entry:
   - keeps `effects`, `slot`, `min_level`, `quiz_tier`, `equip_threshold`, `lore`, `peak_floor`, `spread`;
   - **drops** the now-meaningless material-specific `unidentified_name` (a generic fallback like `"a ring"` / `"an amulet"` stays for safety, but it's overwritten per run);
   - **drops** the per-variant `color` divergence (color follows the assigned appearance — see A3), or keeps a neutral default;
   - restores its natural `floorSpawnWeight` (undo the divide-by-variant-count stopgap).

   The deleted material variants' *flavor* (each had a bespoke `lore` paragraph) collapses to the single canonical entry's lore. That's acceptable: lore is shown at the *identified/type* level, not per appearance.

   Net accessory.json: the cosmetic groups go from (8+7+6+5+2×5+2×3 = 42) entries to **11** entries — about **31 fewer** items.

**A2. Disambiguate the tiered stat groups (do NOT flatten).** Rename so power tiers stop sharing a display `name`:
   - `ring of strength` → keep three named tiers, e.g. **"ring of strength"** (+1), **"ring of greater strength"** (+2), **"ring of master strength"** (+3). Merge the +3 adamantine/mithril cosmetic dupe into the single +3 entry (pick one appearance pool, see A3).
   - Apply the same rename scheme to con/dex/int/wis/per rings and the strength/etc. amulets.
   - After renaming, each tier is its own 1:1 functional type and flows through the same appearance-pool mechanism. `CLASS_MASTERY_BLESSINGS` keys in `class_masteries.py` (e.g. `ring_of_strength`) must gain the new slugs (`ring_of_greater_strength`, `ring_of_master_strength`) or the blessing map must be made tier-agnostic — see Risks.

   *(Alternative if renaming is unwanted: collapse each stat group to ONE entry with a single canonical amount and let enchant/BUC carry variance. Simpler data, but loses the +1/+2/+3 progression the bell-curve floor weights were tuned around. Renaming is preferred.)*

**A3. Define the appearance pool.** Two options:
   - **(Preferred) External pool file** `data/items/accessory_appearances.json` with two lists, e.g.
     ```json
     {
       "ring":   [{"name": "silver ring",    "color": [200,200,210]},
                  {"name": "malachite ring",  "color": [60,160,80]},
                  {"name": "sapphire ring",   "color": [40,80,220]}, …],
       "amulet": [{"name": "jade amulet",     "color": [80,160,80]}, …]
     }
     ```
     Seed it by harvesting the `unidentified_name`+`color` pairs already present in the deleted variants (they're well-written and numerous — 40+ ring looks, plenty for the ~17 ring types + headroom). Must contain **≥ (number of unidentified ring types)** ring appearances and **≥ (number of amulet types)** amulet appearances.
   - **(Fallback) Inline `appearance_pool` array** on each appearance-bearing slot type. More coupling; prefer the external file.

   Appearances are pooled **per slot** (`ring` vs `amulet`) so a ring never gets an "amulet" look.

### B. Code change

**B1. `items.py` — load the pool, don't bake the name.** Add a cached loader:
```python
_APPEARANCE_CACHE = None
def load_accessory_appearances() -> dict:
    global _APPEARANCE_CACHE
    if _APPEARANCE_CACHE is None:
        with open(data_path('data','items','accessory_appearances.json'), encoding='utf-8') as f:
            _APPEARANCE_CACHE = json.load(f)
    return _APPEARANCE_CACHE
```
`Accessory.__init__` keeps reading `unidentified_name` (generic fallback) — appearance assignment happens via B2, which sets `item.unidentified_name` (and `item.color`) on the instance.

**B2. `main.py` — assign appearances once at game start.** In `Game.__init__`, after the player exists, build the per-run map (follows the `_lore_levels` precedent at `main.py:135`):
```python
self._appearance_map = self._roll_appearance_map()   # {functional_class_key: {"name":…, "color":[…]}}
```
where `_roll_appearance_map` enumerates the unidentified accessory *types* (one per functional class — use `get_mastery_class` on a loaded copy, or the canonical id), shuffles the slot-appropriate pool with `random.Random()`, and deals 1:1. Only assign to types that are NOT identified-by-default (skip uniques and `plain silver ring`-style story items, which carry their own fixed look).

   Apply the map wherever an accessory enters the world. Cleanest single chokepoint: **`dungeon.spawn_items`** already builds the accessory pool — stamp there. But accessories also arrive from chests, NPC gifts, hero specials, and starting gear. The robust approach is a **stamp helper** called from `_place_one` (floor), container-loot resolution, and `reconcile_item_identification`'s sibling path. Simplest correct implementation: a method
```python
def apply_appearance(self, item):
    amap = getattr(self, '_appearance_map', None)
    if not amap or not isinstance(item, Accessory) or item.is_unique:
        return
    look = amap.get(get_mastery_class(item))
    if look:
        item.unidentified_name = look['name']
        item.color = tuple(look['color'])
```
   called at item-creation/placement sites. Because `_display_name` only shows `unidentified_name` while the type is unknown, stamping at spawn is sufficient and never leaks once identified.

**B3. `dungeon.spawn_items`** — after `magic_pool = … load_items('accessory') …`, the placed accessory instances get `game.apply_appearance(inst)` (pass the game/appearance-map down, or stamp in `main` right after the floor is generated by walking `ground_items`). Restore the natural `floorSpawnWeight` values (undo the stopgap divide).

**B4. `class_masteries.py`** — add the new tiered slugs to `CLASS_MASTERY_BLESSINGS` (from A2), or refactor the stat-ring blessings to look up by stat rather than exact slug.

### C. Save migration

State is pickled as a flat dict (`save_system.save_game`, line 83) using the `getattr(game, …, default)` pattern, so **adding `'_appearance_map'` to the save dict is automatically backward-compatible** (old saves return the default; new saves persist the map). Steps:

1. **Persist the map:** add `'_appearance_map': getattr(game, '_appearance_map', {})` to the `save_game` state dict, and restore it in `load_state` with a `hasattr` guard that **rolls a fresh map if missing** (so a pre-fix save still gets consistent per-run appearances going forward).
2. **Heal in-flight items:** the existing `_migrate_buc_all` sweep (`main.py:758`) already walks every owned + ground + stored item and calls `reconcile`. Add an `apply_appearance` call alongside `reconcile` in its `owned()`/ground loops so that:
   - items whose old `ring_*` id was deleted in the merge get re-pointed (see step 3), and
   - surviving unidentified accessories adopt the run's assigned appearance (no more "ivory ring" + "silver ring" both meaning searching in one save).
3. **Deleted-id remap:** because A1/A2 remove variant ids (`ring_searching_malachite`, `ring_strength_mithril`, …), old saves holding those instances must remap to the surviving canonical id. Add a small `_LEGACY_ACCESSORY_ID_REMAP = {old_id: new_id}` table and, in the migration sweep, rewrite `item.id` (and re-resolve effects/name from the canonical definition if needed). Items already **identified** keep working because `_display_name` falls back to `item.name` (unchanged for cosmetic merges; updated for the renamed stat tiers). Unidentified deleted-id items pick up the canonical type + the run's appearance.

   *(If a clean-cutover is acceptable for in-progress saves, a lighter alternative is to leave stale-id items as-is — they'll still function via their pickled fields — and only apply the new system to newly-spawned items. The remap is the thorough option; the user's "this should be fixed" suggests thoroughness is wanted, but the remap table is the one genuinely fiddly piece.)*

---

## Fallback (if per-game shuffle is too invasive)

**One fixed appearance per type.** Skip B2/B3/C-step-1 entirely: after collapsing each cosmetic group to one entry (A1) and disambiguating stat tiers (A2), simply give each surviving entry a **single hand-picked `unidentified_name`** (e.g. ring of searching = always "silver ring"). No appearance map, no shuffle, no per-run state, no remap-on-load beyond the deleted-id table.

- **Pros:** Eliminates the duplication (the user's literal stated intent — "exactly one mundane description") with **data-only changes plus the id-remap**; near-zero code; trivial to reason about; no save-format addition.
- **Cons:** Loses the across-runs mystery (every run, "silver ring" is searching), so an experienced player memorizes the table after one playthrough — appearances become a fixed cipher rather than a per-run puzzle. This is *weaker* than classic roguelike behavior but **still satisfies the verbatim requirement** of one description per type.

**Tradeoff verdict:** The per-game shuffle is only ~40-50 extra lines over the fallback (one map-roll, one stamp helper, three call sites, one save field). Given the identification plumbing is already type-keyed, the shuffle is worth it — it's what makes "identify the mystery" gameplay actually replayable. Recommend shuffle; keep fallback in pocket if the deleted-id remap proves hairier than expected.

---

## Risks

1. **Tiered stat rings sharing a name (pre-existing bug).** The biggest correctness trap: flattening strength/con/dex/etc. to one effect would silently nerf +2/+3 rings or buff +1 rings and break the bell-curve floor weighting. **Must disambiguate by name, not flatten.** Verify each renamed tier still has sane `min_level`/`quiz_tier`/`peak_floor`.
2. **Mastery-class slugs.** `get_mastery_class` slugs accessories by **name**. Merging cosmetic variants is safe (same name → same slug, already collapses). But **renaming stat tiers changes their slug**, so `CLASS_MASTERY_BLESSINGS` keys and any saved `known_class_ids`/`unlocked_class_masteries` referencing `ring_of_strength` need the new slugs (B4) — and old saves may carry the old slug (harmless leftover, but the new-tier blessing won't fire until re-identified). Decide whether to migrate `known_class_ids` slugs too.
3. **Pool exhaustion.** If the appearance pool has fewer entries than unidentified types, the shuffle deals duplicates → two types share a look (re-introduces ambiguity). Add a load-time assertion: `len(pool[slot]) >= num_unidentified_types[slot]`. There's ample raw material (40+ ring looks across the deleted variants) so this is just a guard.
4. **Color/icon coupling.** Each old variant carried its own `color`; the renderer's `_resolve_item_sprite_path` may key on id/color. Appearances now own the color (A3) — confirm unidentified accessories render from `item.color` (set by the stamp) and not a per-id sprite, or the look/color can desync.
5. **Deleted-id remap coverage.** Any code path referencing a deleted id by string literal (starting-gear grants in `main.py:1567`, hero specials, NPC gifts, tests) must be updated to the canonical id. Grep for the specific deleted ids before deleting.
6. **Stat-ring blessing double-stacking.** If multiple tiers map to the same class blessing AND the player wears two tiers, confirm the class blessing applies once (existing `class_acc_stat_bonus` semantics) — renaming tiers to distinct classes actually *avoids* this, but check the "while any is worn" wording in the blessing descriptions stays accurate.
7. **Play-test reachability.** Rings/amulets are common early loot, so this is **easily reachable in a few minutes of play** — per the project's play-test rule, the user should confirm in-person that (a) only one look per type appears in a run, (b) identifying one names all copies, (c) the (n/5) markers and stacking behave, and (d) renamed stat tiers read sensibly. Pair with a data-layer test (load accessory.json, assert no two non-unique entries share a `name`; assert appearance pool ≥ type count) and a pure-function test for `_roll_appearance_map` (deterministic 1:1 deal, no dupes).

---

## File/line references

- Variant data: `data/items/accessory.json` (24 names with >1 entry; cosmetic vs tiered split above)
- Accessory load + `unidentified_name`: `src/items.py:620-678`, generic load `src/items.py:989-996`
- Spawn pool (all variants placed): `src/dungeon.py:1384-1401`
- Name resolution (already type-keyed): `src/main.py:5403-5429`
- Class-recognition propagation: `src/game_magic.py:3718-3779`
- Functional-class key: `src/class_masteries.py:28-50`; blessing map `:68+`
- Per-acquisition stamp + `knows_item_type`: `src/player.py:1088-1126`; `known_class_ids` init `:212`
- Per-run randomization precedent: `src/main.py:133-148` (`_lore_levels`, cow/carrot/unicorn floors)
- Save dict + load compat shims: `src/save_system.py:83-153`; `src/main.py:394-448`, migration sweep `:758-784`
