# Identify System — Design (v2)

The I-key identify flow + the corpse-study flow are mechanically
identical: same quiz mode (`escalator_chain`), same subject
(`philosophy`), same 5-tier reveal map, same `id_level` field, same
resume semantics. This doc covers both. The only differences are
**target object type** and **what each reveal level unlocks**.

This doc is the SYSTEM-OF-RECORD. Earlier evolution lives in the
Claude-side auto-memory (`project_identify_rebuild_2026_05_17`,
`project_identify_design`); the current behavior lives here.

---

## §1 Tier reveal map (5 levels)

Each chain rung the kid completes raises `id_level` by 1 and reveals
the next layer. Levels are cumulative — reaching level N means levels
1..N are all unlocked.

| Level | Items                          | Corpses                                              |
|-------|--------------------------------|-------------------------------------------------------|
| 0     | (nothing known — obfuscated)   | (nothing studied — just name + symbol from sight)     |
| 1     | Real name                      | Basic stats (HP, AC, damage)                          |
| 2     | + BUC aura (blessed/cursed)    | + Tags & immediate combat info                        |
| 3     | + Stats (damage, AC, …)        | + Family recognition; propagates to kin on the floor  |
| 4     | + Lore text                    | + Full lore (sets `lore_known_monster_ids`)           |
| 5     | + Mastery blessing (permanent) | + Family mastery blessing (one per family, permanent) |

After level 5, the entry is removed from the identify menu:
- Item uniques: filtered when `item.id in player.unlocked_masteries`
- Item commons: filtered when `id_level >= 5`
- Corpses: filtered when `lore_identified` (lore_known) — equivalent to id_level >= 4
  for the menu-visibility check, with level 5 still claimable via study

(The corpse menu filter at `game_menus.py:670` uses
`not i.lore_identified and monster_id not in lore_known`; once a kid
has done the lore-reveal level for that monster_id, every corpse of
that species drops out of the menu.)

---

## §2 State model

### `Item.id_level: int`

Range 0..5, on the base `Item` class. Initialized by every subclass
constructor as `int(defn.get('id_level', 5 if self.identified else 0))`.

`Item.identified` is a **backward-compat property** that reads
`id_level >= 4`. Setter: `True` raises id_level to ≥ 4; `False` resets
to 0. Old code that reads `item.identified` continues to work; new
code should query `id_level` directly when it cares about specific
levels (1=name, 2=BUC, 3=stats, 4=lore, 5=mastery).

### `Corpse.id_level: int`

Same range, same semantics. `lore_identified` is the corpse-specific
backward-compat property: `id_level >= 4`. The lore screen is the same
machinery items use (`STATE_LORE`).

### Player-side stores

| Field                                       | What it remembers                                              |
|---------------------------------------------|----------------------------------------------------------------|
| `player.known_item_ids: set[str]`           | item.id values whose real name has been revealed (level ≥ 1)   |
| `player.known_class_ids: set[str]`          | mastery_class values whose name propagates to all instances    |
| `player.unlocked_masteries: dict[id, blessing]`        | per-unique mastery (chain-5 reveal)                |
| `player.unlocked_class_masteries: dict[class_id, blessing]` | per-class mastery for commons (Ring of Strength etc.) |
| `player.lore_known_monster_ids: set[str]`   | monster_ids whose lore (≥ level 4) has been revealed           |
| `player.unlocked_monster_class_masteries: dict[family, blessing]` | per-family corpse mastery (level 5)         |
| `player.total_identifies: int`              | career-arc counter (crossings into "full ID" — level ≥ 3 items / ≥ 4 corpses) |
| `player.philosopher_tier_claimed: set[int]` | which career thresholds have fired (25/75/125/200/300)         |

---

## §3 Menu flow (the I key)

`_open_identify_menu()` in `game_menus.py`:

1. Require `philosophers_shard` in inventory — unless the player has
   the **Plato passive** `plato_no_shard` (perceives items via their
   ideal forms; bypasses the shard requirement).
2. Build the menu from three sources:
   - Inventory items where `_needs_identify(item)` is True
   - Ground items at the player's tile that aren't corpses, same filter
   - Corpses at the player's tile that aren't lore-identified
3. `_needs_identify(item)` filter:
   - Uniques: `item.id not in player.unlocked_masteries` (so kid can
     return after id_level 4 to claim mastery)
   - Non-uniques: `id_level < 5` (so Pattern-Recognition'd items at
     level 3 can still be studied for lore + mastery)
4. Render via `_draw_identify_menu()` in `game_render.py`. Entries
   look like:

       Iron Short Sword  (2/5)        weapon  tier 2
       gold ring        (0/5)         accessory  tier 1
       Goblin corpse    (3/5)         Corpse

   The `(N/5)` marker appears next to the name for every entry in the
   menu (N is always 0..4 because 5 filters out). See
   `items.id_progress_marker()`.

5. Pick a letter → `_identify_menu_input()` → routes to either
   `_identify_item(item)` (for items) or `_examine_corpse_direct(corpse)`
   (for corpses). There is **NO pre-quiz chooser** (the F/B chooser was
   a 2026-05-18 regression; deleted in commit 69fefec).

---

## §4 Quiz resume rule (the core mechanic)

Both `_identify_unique_item` (`src/game_magic.py`) and
`_start_corpse_identify` (`src/main.py`) compute:

```python
previous_level = int(getattr(target, 'id_level', 0))
start_tier, max_chain = identify_resume_params(previous_level)
# items.identify_resume_params:
#   start_tier = min(previous_level + 1, 5)
#   max_chain  = max(5 - previous_level, 1)
```

| `previous_level` | `start_tier` | `max_chain` | What happens                                  |
|:-:|:-:|:-:|---|
| 0 | 1 | 5 | Fresh full identify — chain T1..T5 (same as old behavior) |
| 1 | 2 | 4 | Resume — skip T1, answer T2..T5                          |
| 2 | 3 | 3 | Resume — skip T1-T2, answer T3..T5                       |
| 3 | 4 | 2 | Resume — only T4..T5                                     |
| 4 | 5 | 1 | One question for mastery                                 |

The quiz then escalates as normal: each correct answer advances to the
next tier; one wrong answer ends the chain. `result.score` returns the
**chain length** (number of consecutive correct from `start_tier`).
On completion:

```python
chain = int(result.score)
new_level = max(previous_level, min(previous_level + chain, 5))
target.id_level = new_level
```

Key invariants:
- `id_level` **monotonically increases**. A failed attempt never lowers
  it. (`max(previous, …)`)
- `id_level` never exceeds 5. (`min(…, 5)`)
- The level the kid achieves equals where they failed minus one. If
  they had `previous_level=2` and answer T3+T4 correctly but miss T5,
  chain=2 → `new_level = 2 + 2 = 4`. Next attempt starts at T5.

### Failure-message disambiguation

Both flows distinguish "first attempt failure" from "partial-progress
retry failure" — a kid who already had `previous_level >= 1` sees
"gain no **new** insight" so they don't feel they lost ground:

```python
if chain == 0:
    msg = ("You ponder the {x} but gain no insight."
           if previous_level == 0 else
           "You ponder the {x} but gain no new insight.")
```

(Item path uses this exact phrasing. Corpse path uses the equivalent
"You study but learn nothing new (still level N/5).")

---

## §5 Reveal hooks (per-level side-effects)

Both flows run the same `>=` checks against `new_level`, so the side
effects fire correctly whether the kid crossed the threshold from level
0 or from a partial level. No re-firing on already-claimed levels.

### Items (`_identify_unique_item` in `game_magic.py`)

| `new_level >= N` | Side effect                                                |
|:-:|---|
| 1 | `item.identified = True`; `player.known_item_ids.add(item.id)`; real-name message |
| 2 | `item.buc_known = True`; BUC-aura message                  |
| 3 | Stats now visible in display; push `STATE_LORE` if item has lore |
| 4 | Lore now visible in lore screen                            |
| 5 | `_claim_mastery(item)` — adds blessing to player; one-time |

Career-arc counter (`_on_full_identify`) fires once per item, the
first time `new_level >= 3` (the threshold for "full ID" on items —
the kid can read the stats).

`_propagate_identification(item.id)` is called at every reveal level —
it raises id_level on all OTHER instances of the same id (commons:
mastery_class) to a cap (3 for uniques to preserve mastery, 5 for
commons since there's no mastery to gate).

### Corpses (`_start_corpse_identify` in `main.py`)

| `new_level >= N` | Side effect                                                            |
|:-:|---|
| 1 | Stats visible in lore screen                                            |
| 2 | Tags visible                                                            |
| 3 | Family recognized — all same-family corpses bumped to id_level ≥ 3      |
| 4 | `lore_known_monster_ids.add(monster_id)`; full lore visible; career-arc tick |
| 5 | `_claim_monster_family_mastery(corpse)` — family blessing applied       |

The corpse-of-same-monster-id propagation is direct: all `Corpse`
instances on the ground or in the player's inventory with the same
`monster_id` get their id_level bumped to the new level. The family
propagation at level ≥ 3 uses `monster_classes.get_monster_family()`.

---

## §6 Free-identify hooks (bypass the quiz)

These paths set `id_level` directly without running the philosophy
quiz. The resume rule still applies the next time the kid opens the
menu — a free-identify to level 3 means the next quiz starts at T4.

| Hook | Path | Effect |
|---|---|---|
| Cloak of Odin T2+ (`identify_one_per_floor_free`) | `_identify_unique_item` early-return | Bumps to `id_level >= 3`; 1 use per floor |
| Plato passive (`plato_no_shard`) | `_open_identify_menu` | Allows menu access without `philosophers_shard` (does NOT change id_level) |
| Pattern Recognition (career arc, threshold 75) | `_pickup` | Common items with `quiz_tier <= 1 + floor//30` auto-identify to `id_level=3` on pickup |
| Philosopher's Mantle (career arc, threshold 300) | `_pickup` | Auto `buc_known=True` on every pickup |
| Altar D-press (quick BUC) | `_altar_buc_identify` (`game_divine.py`) | Sets `buc_known=True` only; does NOT change id_level |

---

## §7 Bank, subject, and tier mapping

- **Subject**: `philosophy` (both item and corpse identify)
- **Mode**: `escalator_chain`
- **Start tier**: dynamic via `identify_resume_params` (was hardcoded 1
  pre-2026-05-28)
- **Max chain**: dynamic via same helper (was hardcoded 5)
- **Timer**: `base_seconds=player.get_quiz_timer('philosophy')`,
  multiplied by `timer_modifier`, plus INT and (corpse only) extra
  philosophy seconds.

The escalator engine pulls T1 questions, then T2 on correct answer,
etc. With the new `start_tier` parameter, it begins at the kid's
resume tier instead — saving them from re-answering tiers they already
passed.

---

## §8 What this REPLACES / NEVER REINTRODUCE

- ❌ **F/B chooser popup before the quiz** (2026-05-18 regression,
  deleted commit 69fefec). One action, one quiz, depth of result
  matches depth of effort.
- ❌ **Re-asking T1/T2 questions on every retry** (pre-2026-05-28).
  The resume rule above replaces this.
- ❌ **Atomic threshold-mode reveal for commons** (pre-2026-05-18).
  All items now use escalator-chain.

---

## §9 Test coverage

`tests/test_identify.py` (Pygame-free, pure-function unit tests):

- `id_level` defaults across subclasses (Weapon/Accessory/Potion/…)
- `mastery_blessing` field loaded from JSON; allowed kinds list
- Career-arc thresholds: 25 (+1 INT), 75 (Pattern Recognition flag),
  125 (+1 PER), 200 (+1 WIS), 300 (Philosopher's Mantle)
- Combat-time mastery hooks on weapons
- Quick-BUC does NOT count toward career arc
- **Identify resume helpers** (`identify_resume_params`,
  `id_progress_marker`) — added 2026-05-28
- **Chain-to-id_level algebra** (`new_level = previous + chain`,
  capped + monotonic)

Pygame-driven play-testing is required for menu rendering and the
end-to-end quiz flow — see `CLAUDE.md` Play-test Rule.

---

## §10 Files

| Location | Role |
|---|---|
| `src/items.py:21+` | `id_level` field on base + subclasses; `identify_resume_params()` and `id_progress_marker()` pure helpers |
| `src/game_menus.py:632 _open_identify_menu` | Menu population + filter |
| `src/game_menus.py:688 _identify_menu_input` | Pick → route to item/corpse identify |
| `src/game_render.py:2546 _draw_identify_menu` | Menu render; appends `(N/5)` marker |
| `src/game_magic.py:2466 _identify_unique_item` | Item identify quiz (uses resume helper) |
| `src/game_magic.py:2577 _claim_mastery` | Mastery blessing application |
| `src/game_magic.py:3072 _propagate_identification` | Cross-instance id_level sync |
| `src/main.py:4892 _start_corpse_identify` | Corpse identify quiz (uses resume helper) |
| `src/main.py:4966 _claim_monster_family_mastery` | Corpse family-mastery application |
| `src/class_masteries.py` | `get_mastery_class()` + `CLASS_MASTERY_BLESSINGS` for commons |
| `src/monster_classes.py` | `get_monster_family()` + `MONSTER_FAMILY_BLESSINGS` for corpses |
| `tests/test_identify.py` | Pure-function tests (47 as of 2026-05-28) |

---

## §11 Item-name composition (added 2026-05-28)

Common items (weapons / armor / shields generated from a template +
material) have two display names — `name` (identified) and
`unidentified_name`. Both are composed at instantiation time in
`items.py`.

### The bug this section documents fixing

Naive compose was:
```python
name              = f"{mat['name']} {tpl['name']}"
unidentified_name = f"{mat['unidentified_descriptor']} {tpl['name']}"
```

Two structural problems with the JSON data this concat couldn't see:

1. **Templates carry the material word.** 32 of ~50 armor/shield
   templates have a material word baked into their `name` field
   ("light wooden shield", "iron boots", "chain shirt"). Naive concat
   with the material prefix produced "oak light wooden shield" or
   "iron iron boots" — material doubled.
2. **Material `unidentified_descriptor`s are written as noun
   phrases**, not adjective phrases. Many start with an article ("a
   wooden plank") or end in an object noun ("a faintly blue blade").
   Worse: shields fall back to the weapons material pool when an
   armor-pool material isn't found (`get_material('armor', id) or
   get_material('weapons', id)`), so a wooden shield could get a
   weapon-specific descriptor ending in "blade" or "haft", producing
   "a wooden haft light wooden shield".

The user's report: "pale fibrous wood light round wood shield" — same
shape: weapon-pool ash descriptor `"a pale fibrous wood"` + shield
template `"light wooden shield"`.

### The fix (no JSON edits)

Two pure helpers in `items.py` normalize each side before concat:

```python
def _strip_redundant_material_words(tpl_name: str) -> str:
    """'light wooden shield' -> 'light shield'; 'iron boots' -> 'boots';
    'tower shield' -> 'tower shield' (unchanged). Never strips to empty."""

def _normalize_descriptor(desc: str) -> str:
    """'a wooden plank' -> 'wooden'; 'a faintly blue blade' -> 'faintly blue';
    'pale silvery metal' -> 'pale silvery metal' (unchanged). Strips a
    leading article and trailing object-noun. Never strips to empty."""

def compose_item_name(mat_name, tpl_name):
    return f"{mat_name} {_strip_redundant_material_words(tpl_name)}".strip()

def compose_unidentified_name(mat_descriptor, tpl_name):
    cleaned_desc = _normalize_descriptor(mat_descriptor)
    cleaned_tpl  = _strip_redundant_material_words(tpl_name)
    return f"{cleaned_desc} {cleaned_tpl}".strip()
```

Wired into all three `instantiate_*` functions
(`instantiate_weapon`, `instantiate_armor`, `instantiate_shield`).

### Strip lists

These const sets in `items.py` define what counts as "generic material
word" and "weapon-specific tail noun". Add to them if a future template
or material descriptor surfaces a new offender:

```python
GENERIC_MATERIAL_WORDS = {
    'wood', 'wooden', 'iron', 'steel', 'leather', 'plate',
    'chain', 'cloth', 'silk', 'linen', 'hide', 'padded',
    'studded', 'scale', 'bronze', 'silver', 'gold', 'mithril',
    'banded', 'ringmail', 'chainmail', 'splint',
}
DESCRIPTOR_TAIL_NOUNS = {
    'blade', 'haft', 'timber', 'plank', 'plate', 'board',
    'hide', 'cloth', 'fabric', 'leather', 'weapon', 'thing',
}
```

Note: `'wood'` is in `GENERIC_MATERIAL_WORDS` but NOT in
`DESCRIPTOR_TAIL_NOUNS`. That's deliberate — the descriptor side keeps
"wood" because it carries the pre-identify material hint to the
player ("pale fibrous wood ... shield" tells them it's some kind of
wood before they know it's ash). The template side strips "wood" /
"wooden" because the material prefix already conveys that.

### Worked examples

| material | template | before (identified) | after | before (unidentified) | after |
|---|---|---|---|---|---|
| oak | light wooden shield | oak light wooden shield | **oak light shield** | a wooden plank light wooden shield | **wooden light shield** |
| ash | light wooden shield | ash light wooden shield | **ash light shield** | a pale fibrous wood light wooden shield | **pale fibrous wood light shield** |
| iron | iron boots | iron iron boots | **iron boots** | a plain blade iron boots | **plain boots** |
| steel | plate helm | steel plate helm | **steel helm** | well-forged steel plate helm | **well-forged steel helm** |
| mithril | plate helm | mithril plate helm | **mithril helm** | pale silvery metal plate helm | **pale silvery metal helm** |
| oak | kite shield | oak kite shield (unchanged) | oak kite shield | a wooden plank kite shield | **wooden kite shield** |

### Why runtime, not data rewrite

Fixing the 32 templates' `name` fields and 30 materials' descriptors
in JSON would be the "more proper" fix, but:

1. The runtime helpers work on any future template/material data the
   same way — they enforce the rule structurally rather than relying
   on every author getting the data right.
2. Existing save games already store composed names on item
   instances; a data rewrite wouldn't fix those.
3. The helpers are testable and have invariants (never strip to
   empty, idempotent on already-clean strings) the data couldn't
   express.

If a future material descriptor or template name shows a new failure
mode (some word that's neither a generic-material nor a tail-noun but
still wrong), add it to the appropriate const set and the
test_identify.py composition tests.
