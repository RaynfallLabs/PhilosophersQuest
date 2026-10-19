# Identify v3

**Scope.** The identify flow (items + corpses) as it stands post-2026-08-06:
one philosophy question at a derived tier, right = full ID, wrong =
Stunned 10 turns. No masteries, no partial id_levels, no resume math.

**One identification knows every copy (2026-10-18).** Brandon: "once
you've identified something, all further instances need to be fully
identified, including BUC status." Knowing a KIND (by the question, a
scroll, use, a trader, the Book of Thoth, a gift, Pattern Recognition)
fully identifies every copy of it: name, blessing or curse, enchantment.
That covers copies in the pack, on the floor, in chests, in trader stock
and every copy that turns up later. It is decided when the game asks
(`items.is_fully_known(item, player)`, `items.buc_known_to`), never
stamped on the copies, so forgetting a kind (cursed Scroll of Identify,
Book of Thoth's curse: `Game._forget_kind`) un-knows them all. A copy of a
known kind is never offered for identifying (`Game._needs_identify`).
The in-between "true name, curse unknown" state of the old True Name model
is gone (§6).

Source of truth: `src/game_magic.py::_identify_item`,
`src/game_menus.py::_open_identify_menu`,
`src/main.py::_start_corpse_identify`, `src/items.py::derive_id_tier`,
`src/hud_context.py::hud_item_name`. See also the memory
`project_identify_one_question_2026_08_06.md`.

---

## 1. Why v3 exists

Pre-v3 the identify system had three mastery stores
(`identify_masteries`, `family_mastery_blessings`, class-based
`class_masteries.py`), 277 blessings, and a tiered id_level ladder
(0–5) that gave partial reveals at 1, 2, 3, 4 before the final name.
It was Nethack-grade complexity for an action with one real question:
*what is this?*

Identify v3 deletes:
- all three mastery stores (`class_masteries`, `identify_masteries`,
  `family_mastery_blessings`),
- all 277 family-mastery blessings,
- the "stuffies" subsystem that overloaded mastery with carry bonuses
  (stuffies are now a plain `carry_bonus` field — see
  [items §10](items.md)),
- partial `id_level` 1–4 progression (only 0 and 5 are ever written by
  the new flow).

What stays:
- The philosopher career arc (`total_identifies`,
  `philosopher_tier_claimed`, Philosopher's Mantle). Each full identify
  bumps the counter.
- `id_level` as the save-compat int (0 or 5 written; `>= 4` means
  "name/lore revealed").

Save migration is explicit: `Player.__setstate__`
(`src/player.py:650`) pops the retired attrs
(`class_masteries`, `subject_mastery_xp`, `stuffies_active`,
`_active_stuffies`, `identify_masteries`, `family_mastery_blessings`,
`family_masteries`, `weapon_masteries`, `shield_masteries`) off the
loaded state before `__dict__.update`.

---

## 2. The flow (items)

Call graph:

```
I key
 └─ _open_identify_menu()                src/game_menus.py:732
      ├─ Shard gate                      (bypassed by plato_no_shard)
      ├─ build identify_menu_items       (inventory + ground tile + corpses)
      └─ STATE_IDENTIFY_MENU
             │
             │ Enter
             ▼
     _identify_menu_input(key)           src/game_menus.py:783
      ├─ corpse  → _examine_corpse_direct → _start_corpse_identify
      ├─ scroll-identify pending → _scroll_full_identify (no quiz)
      └─ otherwise → _identify_item(item)
                      src/game_magic.py:3056
                     ├─ (chain-equip passive one-free check)
                     ├─ tier = item_id_tier(item)        src/items.py:86
                     ├─ tier -= get_identify_tier_reduction (min 1)
                     ├─ quiz_engine.start_quiz(
                     │       mode='threshold',
                     │       subject='philosophy',
                     │       tier=tier,
                     │       threshold=1, total_qs=1,
                     │       base_seconds=philosophy timer, …)
                     └─ on_complete:
                         success → _full_identify(item)  →  STATE_LORE
                         failure → add_effect('stunned', 10) + msg
```

### Shard gate

`_open_identify_menu` (`src/game_menus.py:735`) requires the
**Philosopher's Shard** in inventory **unless** the player has the
Plato passive `plato_no_shard` (Form of Ideas — "perceives items via
their ideal forms"). The Shard is the fictional conduit for the
backlash: when you fail, "the Shard turns cold in your palm" and the
cost lands.

```python
plato_pass = 'plato_no_shard' in getattr(self.player, 'hero_passives', set())
if not plato_pass:
    has_shard = any(
        getattr(i, 'id', '') == 'philosophers_shard'
        for i in self.player.inventory
    )
    if not has_shard:
        self.add_message("You need the Philosopher's Shard to identify items.", 'warning')
        return
```

Carrying a shard that gets removed/lost blocks future identifies until
you find another one; Diogenes drops them in a specific side-arc.

The shard also enjoys a protective rule: the cursed Scroll of Identify
(amnesia variant) specifically **skips** the shard when picking a
candidate to de-identify ("bricking the ID system is too brutal",
`src/game_magic.py:3280`).

### The quiz

Mode: `threshold`. Subject: `philosophy`. Tier: derived (§5). Threshold:
`1` (one correct answer). Zero-tolerance applies: *any* wrong = fail.

Right answer → `_full_identify(item)`:
1. `item.id_level = 5`
2. `item.buc_known = True` (if the field exists)
3. `_propagate_identification(item.id, seed_item=item)` — the KIND
   joins the known sets, so every other copy, now and later, is fully
   identified too (blessing and enchantment included), and same-blessing
   stacks of it in the pack join up (`Player.merge_known_stacks`).
4. `quirk_system.on_item_identified(item.id)` fires once per instance
   crossing into full ID.
5. `player.total_identifies += 1`, `_check_philosopher_thresholds()`.
6. State transitions to `STATE_LORE` so the lore screen opens
   immediately — the whole story arrives at once.
7. Message: `"It is the {item.name}. You sense {aura}."` where
   `aura` ∈ `{"a holy radiance" (blessed), "a dark aura" (cursed),
   "no clinging aura" (uncursed)}`.

Wrong answer:
- `player.add_effect('stunned', 10)` — flat 10-turn stun
- Message: `"The Shard turns cold in your palm. Backlash floods your
  mind — you are Stunned (10 turns)."`
- Turn advances.

No partial reveal, no "you learn the BUC but not the name" state. One
Q, binary outcome.

### Timer

Pulled from `Player.get_quiz_timer('philosophy')`
(`src/player.py:864`): base 50s + 1.5 s/WIS, floor 5 s. INT grants
`get_int_quiz_bonus()` (+0.5 s per INT above 10) *for the subject
tier*; status effects multiply via `get_quiz_timer_modifier()`.

Note: the engine only *actually* times `math`; non-math `extra_seconds`
are discarded by the quiz engine but passed through for forward
compat.

---

## 3. Scroll of Identify (bypass path)

Scroll of Identify short-circuits the philosophy quiz entirely —
reading the scroll succeeded on grammar, which is the quiz we paid.

Three branches, routed by `game_magic._open_scroll_identify_picker`
and sibling helpers:

- **Single-pick** (normal Scroll of Identify) — opens the identify
  menu with `_scroll_identify_pending = True`. On select,
  `_scroll_full_identify(item)` reveals one item with no further
  quiz. ESC wastes the scroll's revelation.
- **Mass** (`_scroll_identify_mass(limit=N)`) — T2/T3 blessed scrolls
  reveal the first N unidentified items in inventory + current tile
  (a second copy of a kind just learnt is already known, so N counts
  kinds). Omnisight (T5) passes `limit=None` and reveals *every*
  unidentified item.
- **Cursed amnesia** (`_scroll_identify_amnesia`) — picks a random
  known thing in the pack (never the Shard, never treasure) and forgets
  its KIND (`_forget_kind`): the id, its accessory family and its form
  leave the known sets, and every copy the game can reach (worn, pack,
  floor, stored floors, chests, trader stock) drops to `id_level` 0 with
  its blessing unknown. The Book of Thoth's curse forgets three kinds the
  same way.

Omnisight also calls `_omnisight_corpse_reveal` so one carried corpse's
species joins `lore_known_monster_ids` (drives pre-identified corpse
spawns and bestiary lore).

Scroll of Identify never affects corpses — those always route through
the normal lore path (`_examine_corpse_direct` in the scroll-pending
branch, `src/game_menus.py:822`).

---

## 4. Corpse identify

Entry: standing on a corpse, press the examine key, or pick the corpse
from the identify menu. `_start_corpse_identify` (`src/main.py:6527`)
runs the same shape:

```python
quiz_engine.start_quiz(
    mode='threshold', subject='philosophy',
    tier=item_id_tier(corpse),
    threshold=1, total_qs=1, …)
```

On success:
- `corpse.id_level = 5`
- `player.lore_known_monster_ids.add(corpse.monster_id)` — the monster
  TYPE is known forever. Future kills spawn pre-identified corpses
  (see `game_combat._make_corpse`).
- Propagate to every corpse of the same monster on the floor + in the
  pack.
- `_lore_subject = corpse` → open lore screen.

On failure: same `stunned 10` backlash as items. Corpses are
"flattened" — treated as if they were an item of their `monster_id`,
with their id_tier derived the same way (§5).

An already-known corpse (type in `lore_known_monster_ids`) skips the
quiz and opens the lore screen directly (`_examine_corpse`,
`src/main.py:6603`).

---

## 5. Derived id_tier

`derive_id_tier` (`src/items.py:48`) is the pure function; `item_id_tier`
(`src/items.py:86`) wraps it over a live item/corpse instance.

Priority order:

1. **Explicit `id_tier` from JSON** (`item.id_tier`, 1–5). This wins.
2. **Gear tier** — weapons/armor/shields/ammo already encode depth by
   construction (material peak_floor → tier band at instantiate time).
3. **Harder of `quiz_tier` and depth band** — a scroll's `quiz_tier`
   is its *read* difficulty (deliberately easy on deep mythic
   scrolls), so the native spawn depth must be able to outvote it. A
   floor-90 Scroll of Ragnarok identifies at T5, not T1. "Depth band"
   = `_floor_band_tier(peak_floor)` or
   `_spawn_weight_band_tier(floor_spawn_weight)` as a fallback.
4. **`min_level` band** — for anything missing both peak_floor and a
   spawn-weight dict.
5. **Default 1**.

**Uniques never sit below tier 4** — a legendary yields only to deep
study. `is_split_type_known` and the derivation both honor this via
`c = max(c, 4) if is_unique else c`.

`_floor_band_tier(f)` = `max(1, min(5, (f - 1) // 20 + 1))`.
Band map: `1..20=T1 / 21..40=T2 / 41..60=T3 / 61..80=T4 / 81..100=T5`.

`_spawn_weight_band_tier({"<lo>-<hi>": w, …})` picks the band with the
highest weight and maps its midpoint through `_floor_band_tier`.

Corpse derivation (`Corpse.__init__`, `src/items.py:1027`): explicit
> monster peak_floor band > harvest_tier > 1. Harvest_tier is a *food*
stat, not a knowledge stat — an ancient lich (floor 90, barely
harvestable) must identify at T5; a meaty floor-17 sphinx must not
demand T5 from a kid with T1 philosophy skills.

### Accessory passives (tier reduction)

Equipped accessories can lower the effective id_tier by
`identify_tier_reduction` (field on `Accessory`,
`src/items.py:817`). `Player.get_identify_tier_reduction()`
(`src/player.py:915`) sums the field across amulet + rings + belt.
`_identify_item` subtracts it with a floor of 1 (tier never drops
below 1).

Current users:
- **Ring of Pythia** — `identify_tier_reduction: 1`
- **Torque of Lugh** — `identify_tier_reduction: 1`

(This field used to be `identify_timer_bonus` — identify v3 is
untimed-against-the-player beyond philosophy's base timer so the old
field was dead. Repurposed 2026-09-24.)

---

## 6. HUD rules (one identification knows every copy)

`hud_context.hud_item_name(player, item, include_count=False)` resolves
the display name through a two-state tree:

| State | Condition | Display |
|-------|-----------|---------|
| Known | this copy identified (`id_level >= 5`) **or** its kind known (`player.knows_item_type`) | true name, with a `Blessed` / `Cursed` prefix (`"Blessed Potion of Healing"`) |
| Unknown | neither | `unidentified_name` appearance, with `Cursed` only once an altar or a worn curse has shown it |

`hud_context.copy_fully_known` / `items.is_fully_known` is the one test;
`Game._display_name` (menus, messages), the Kit's BUC column, the lore
dossier, the shop, sell prices (`economy.sell_offer(identified=...)`)
and the identify menu all ask it, so every surface names an item the
same way.

**History.** From 2026-08-06 to 2026-10-18 a known type showed its true
name while each copy kept its own blessing and enchantment secret
("Potion of Healing (Curse Unknown)", `hud_context.unknown_copy_suffix`,
now deleted). Brandon found the per-copy identify too annoying in play,
so a known kind now knows every copy.

**Capitalisation (v2.23.0).** `item.name` / `item.unidentified_name`
always read back in title case through `naming.ProperNameAttr`. The item
dossier's identity panel shows a plain `Identified` / `Unidentified`
line and an `Appearance` field (the unidentified look, for recognising
the item on a later run) in place of the old `True name` row — see
[ui §16](ui.md). The art never changes with identification
(`feedback_item_art_is_the_item`).

### Type-knowledge keys

- `Player.known_item_ids: set[str]` — item ids identified this run.
- `Player.known_class_ids: set[str]` — classes identified by their
  type (collapsed accessory families: "Ring of Strength" for every
  material).
- `Player.known_forms: set[str]`, `Player.known_materials: set[str]`
  — identify v3.1 split-knowledge (2026-09-01). Learn `long_sword` +
  `iron` independently; every iron long sword then counts as a known
  kind (fully identified) without a per-id-slug event.
- `knows_item_type(item)` (`src/player.py`) is the kind predicate:
  hits on any of the three stores above (via `type_class`,
  `is_split_type_known`). `items.kind_is_known` wraps it and leaves out
  corpses (their own `lore_known_monster_ids`) and treasure (known by
  sight, valued by a trader: `treasure.py`).
- **Save/load.** The sets are pickled on the Player and read on demand,
  so nothing is stamped on items. `Game._rebuild_kind_knowledge` (called
  from `load_state`) makes them real sets, rebuilds accessory families
  from `known_item_ids` for a save that predates `known_class_ids`, and
  merges same-blessing stacks of known kinds.

### Weapons with `identified: false` default

Weapons spawn with `id_level = 5 if defn.get("identified", False) else
0`. Every real `weapon.json` entry has `"identified": false` so
weapons start fully unknown on spawn. Templated weapons spawned by
`instantiate_weapon` also start `identified: false` with
`unidentified_name` composed from the material descriptor + template
(`compose_unidentified_name`).

### Artifacts missing `unidentified_name` (v2.18.0 fix)

Pre-v2.18.0, 24 spoilered artifacts had no `unidentified_name` and
rendered their true names on pickup — major plot spoilers:

- Seven Seals (red/green/black/rust/pale/grey/silver) → `"sealed metal disc (<color>)"`
- Michael's Scales → `"ornate golden scales"`
- Palladium → `"ancient wooden idol"`
- Tablet of Destinies → `"obsidian tablet"`
- Philosopher's Stone → `"smooth red stone"`
- Philosopher's Shard → `"chunk of dark stone"`
- Pithos of Pandora → `"a sealed pithos"`
- Lamp of Diogenes / Aladdin's Lamp → `"a tarnished brass lamp"`
- Baetyl figurine → `"bronze figurine"`
- Eye of Graeae → `"cloudy glass eye"`
- Nereid's Whisper → `"silvery whisper in a bottle"`
- Soma Fibers → `"wisps of fine hair"`
- Harpy Mist → `"sealed vial of mist"`
- Eye-of-Horus elixir vial → `"tiny sealed vial"`
- Ariadne's Thread → `"coiled thread"`
- Nephthys ribbon → `"impossibly thin ribbon"`
- Pelops piece → `"leather scrap"`
- Vidar's sandal strap → `"old leather sandal"`
- Lodestone of Set → `"dark magnetic stone"`
- Writ sealed letter → `"wax-sealed letter"`

Every one of these is now wired through `hud_item_name`'s "type
unknown" branch so the display stays spoiler-safe until the kid
actually studies the artifact.

---

## 7. Backlash: why the stun?

Pre-v3 a wrong identify dropped a zero-chain confusion debuff. User
feedback 2026-05-29: a *blind attempt must carry a cost*. Identify's
unique position is that it does **not** consume the target (unlike
harvest, which consumes the corpse, or cook, which consumes the
ingredient). Resource loss is the natural penalty for consumptive
quiz-gated actions (see memory
`feedback_resource_loss_is_the_penalty.md`); because identify is
non-consumptive, the cost lives in a flat 10-turn stun instead.

Standard status rules apply — `stunned` reduces the quiz-timer
multiplier (`get_quiz_timer_modifier` × 0.75) and movement speed per
`status_effects.py`.

---

## 8. Career arc

Every call to `_full_identify` bumps `Player.total_identifies` and
calls `_check_philosopher_thresholds` (`src/game_magic.py:3154`).
Thresholds (10 / 25 / 50 / 100) grant one-time rewards tracked in
`philosopher_tier_claimed`. At 100 identifies the player gets
Philosopher's Mantle (`philosophers_mantle: True`) — auto-set
`buc_known = True` on every new pickup.

Quick-BUC peeks (altar drop-reveals, inspection stations) do **not**
count. Only full identifies through the one-question quiz, the Scroll
of Identify bypass, or corpse study.

---

## 9. Cross-references

- [items](items.md) — `derive_id_tier` field inputs; the schema fields
  it reads from (`tier`, `quiz_tier`, `peak_floor`,
  `floor_spawn_weight`, `min_level`, `is_unique`).
- [magic](magic.md) — Scroll of Identify effects, the omnisight
  branch.
- [food_system](food_system.md) — corpse harvest; harvest and
  identify use the *same* `item_id_tier` for a corpse but different
  subjects (animal vs philosophy).
- [progression](progression.md) — philosopher career thresholds,
  Philosopher's Mantle quirk.
- [ui](ui.md) — `hud_item_name` wiring into context rows, kit panel,
  item cards.

> **Monster families (2026-10-18).** A correct corpse study also records the kind in `player.studied_monster_ids`, which is what monster family tiers count (`docs/systems/monster_families.md`). Corpses now spawn pre-identified for kinds in `studied_monster_ids` (the hero's own studies); `lore_known_monster_ids` still opens the Bestiary page, and the Book of Thoth fills it without teaching any tier.
