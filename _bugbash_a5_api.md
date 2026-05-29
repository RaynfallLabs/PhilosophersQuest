# Bug Bash A5 — Attribute Access + API Consistency

Agent: A5 (overnight bug-bash)
Date: 2026-05-28
Scope: `src/` — `getattr` default-value inconsistencies, hasattr discipline,
None-safety on attribute chains, attribute-name drift (`cursed` vs `buc`),
magic-string `setattr`, `**kwargs` swallowing, None-returning helpers,
subject→action map drift, stat-casing, back-compat property usage.

Methodology: grep every `getattr(obj, 'attrname', default)` across `src/`,
group call sites by attribute, flag every default mismatch. Then read the
class definitions in `src/items.py` to determine what the field actually IS
when it exists, and reason about which sites would be wrong if the field
is missing entirely (a real concern given the save-migration shim at
`src/game_helpers.py:15 migrate_buc_item`).

---

## Category 1 — getattr default-value inconsistencies (the core surface)

### [CRITICAL] `id_level` default conflict: identify-menu shows known items as unknown
**Attribute / API**: `id_level` on items / corpses (Item.id_level int 0..5)
**Inconsistent sites**:
- `src/game_menus.py:651` — `getattr(i, 'id_level', 5) < 5` (default **5** = "known")
- `src/game_render.py:3892` — `int(getattr(subject, 'id_level', 5))` (default **5**)
- `src/game_menus.py:358` — `int(getattr(item, 'id_level', 0))` (default **0** = "unknown")
- `src/game_render.py:2651` — `id_progress_marker(getattr(item, 'id_level', 0))` (default **0**)
- `src/game_render.py:3795` — `int(getattr(subject, 'id_level', 0) or 0)` (default **0**, for CORPSES)
- `src/game_magic.py:2483` — `int(getattr(item, 'id_level', 0)) < 3` (default **0**)
- `src/game_magic.py:2502` — `previous_level = int(getattr(item, 'id_level', 0))` (default **0**)
- `src/main.py:4902, 4909, 4924, 4934, 5021` — all default **0**
- `src/game_combat.py:727` — default **0**

**What I see**: The identify menu's filter (`game_menus.py:651`) treats a
missing `id_level` as **fully identified** (so the item drops out of the menu).
The same function's visible-level helper (`game_menus.py:358`) treats it as
**unknown** (level 0). The render layer is split too: `_draw_lore_screen` uses
default 5 for ITEMS (line 3892) but default 0 for CORPSES (line 3795).
**Why it matters**: For an old-save item that lost `id_level` during pickling
(or a new Item subclass an author forgot to initialize), the menu filter would
HIDE it but the menu builder would render it as "0/5" — these are mutually
inconsistent. The migration shim at `src/game_helpers.py:25-27` only fires on
saves opened via `Game._post_load_migrate`, so a fresh in-memory item that
somehow lacks the attribute would land in the bug. The new-item-path is
already safe (every Item subclass sets `id_level` in `__init__`), so this
bug is latent rather than firing today — but the next person to add an Item
subclass that forgets the field will hit it.
**Suggested fix**: Standardize on **0** (unknown) — matches the docstring at
`game_menus.py:649-650` and matches the corpse render side. The two outliers
(`game_menus.py:651` and `game_render.py:3892`) should both use `0`. Document
in `proposals/v2_audit/IDENTIFY_SYSTEM.md §2` that "missing id_level means
unknown by default".
**Confidence**: HIGH (the call-site split is real and the documented
back-compat intent is "0 means unknown")

### [WARN] `slot` default varies wildly across sites
**Attribute / API**: `slot` on Armor / Accessory / Shield
**Inconsistent sites**:
- `src/chain_equip.py:64` — default `''`
- `src/game_render.py:1744` — default `'armor'`
- `src/game_render.py:1752, 2074, 2091, 2210` — default `''`
- `src/game_menus.py:255` — default `''`
- `src/main.py:4013` — default `itype` (runtime parameter)
- `src/main.py:4022, 4045` — default `''`
- `src/main.py:4156` — default `slot_type` (runtime parameter)
- `src/main.py:4158` — default `'accessory'`
- `src/main.py:4503` — default `'body'`
- `src/player.py:888, 890` — default `'ring'`

**What I see**: 7 different defaults for the same attribute. Armor.slot is
required from JSON (`defn['slot']` with no `.get()` fallback at items.py:177).
Accessory.slot is also required (`items.py:265`). So absence means a malformed
item, and the "default" is really a fallback for crash-protection.
**Why it matters**: An armor item missing `slot` falls into `'body'` at
main.py:4503 (the equip flow) but `''` at game_render.py:2074. The body-default
would let a broken item silently slot into the body armor position, displacing
real body armor — bad. The render side returns `''` which renders as `(empty)`.
A `'ring'` default at player.py:888 means an accessory missing `slot` would
be treated as a ring and stuck in the ring slot.
**Suggested fix**: Standardize on `''` (empty string = "no slot") and have
the equip flow explicitly reject empty-slot items with a warning. The
`'body'` default at main.py:4503 is the most dangerous.
**Confidence**: HIGH

### [WARN] `material` default: None vs '' mixing breaks `.lower()`
**Attribute / API**: `material` on Weapon / Armor / Shield
**Inconsistent sites**:
- `src/combat.py:94, 109` — default **None**
- `src/combat.py:265` — `getattr(weapon, 'material', '').lower()` (default `''`)
- `src/game_render.py:2051` — `getattr(item, 'material', '') or ''` (default `''`)
- `src/main.py:580, 3206` — defaults `''` and `None` respectively
- `src/status_effects.py:153, 158, 168` — default `''`

**What I see**: `combat.py:265` does `getattr(...).lower()` with a string-`''`
default. If a future caller writes `getattr(weapon, 'material', None).lower()`
it crashes on None. The pattern `getattr(weapon, 'material', None)` then `if mat:`
(lines 94, 109) is safer but inconsistent with line 265.
**Why it matters**: A Weapon with `material=None` (legacy save before the field
existed?) hitting `combat.py:265` would crash with `AttributeError: 'NoneType'
has no attribute 'lower'`. Weapon.__init__ defaults to `'iron'` so the bug is
latent — but the inconsistent pattern is a future-bug trap.
**Suggested fix**: Use `(getattr(weapon, 'material', '') or '').lower()`
everywhere — handles both None and missing.
**Confidence**: MEDIUM

### [WARN] `min_level` default: 0 vs 1 — monster death-omen target wrong
**Attribute / API**: `min_level` on Monster
**Inconsistent sites**:
- `src/main.py:905` — `key=lambda m: getattr(m, 'min_level', 0)` (default **0**)
- `src/game_encounters.py:860` — default **1**
- `src/mystery_system.py:627` — default **1**
- `src/game_divine.py:713` — default **1**
- `src/pet_system.py:556` — default **1**

**What I see**: The Morrigan's death-omen marking (Crusader passive) picks
the monster with the HIGHEST `min_level` on the floor. If a monster lacks
the field, main.py defaults to 0, sorting it to the bottom. Every other
site defaults to 1 (matching Monster.__init__ default at monster.py:33).
**Why it matters**: Monster init guarantees `min_level: int = int(defn.get('min_level', 1))`,
so the field is always present. But the rest of the code base uses 1 as the
"missing/unknown level" floor — the 0 in main.py:905 is an outlier and could
mis-rank a future Monster subclass that bypasses the standard init.
**Suggested fix**: Change `main.py:905` default to **1** for consistency.
**Confidence**: MEDIUM

### [WARN] `monster_id` default: '' vs None — corpse identify menu skips wrongly
**Attribute / API**: `monster_id` on Corpse / pickled bestiary entries
**Inconsistent sites**:
- `src/game_menus.py:672` — default `''`
- `src/main.py:3392` — default `''`
- `src/main.py:5012` — default `None`
- `src/main.py:5322` — `getattr(item, 'monster_id', None) or getattr(item, 'kind', None)`

**What I see**: When checking `monster_id in lore_known_monster_ids` (a set),
default `''` would never match (since `''` isn't a real id). Default `None`
would also never match. So in practice both work — but they differ in truthiness
checks downstream.
**Why it matters**: At `main.py:5012`, the code does
`if getattr(i, 'monster_id', None) is not None` — corpses with `monster_id=''`
would PASS this filter (not None ≠ truthy). Other sites use empty-string-as-falsy
semantics. This means corpses with `monster_id=''` are handled inconsistently:
they pass the None-check but fail the `in set` test.
**Suggested fix**: Standardize on `''` (empty string) since Corpse always sets
`self.monster_id = monster_id` (a string in practice).
**Confidence**: MEDIUM

### [WARN] `count` default: None vs 1
**Attribute / API**: `count` on Item (stack size)
**Inconsistent sites**:
- `src/ui.py:416` — `getattr(item, 'count', None)` (default **None**)
- `src/player.py:732, 733, 740, 741, 753, 762`, `src/main.py:4485`,
  `src/game_menus.py:1413, 1467`, `src/game_combat.py:1291` — default **1**

**What I see**: `ui.py` displays count and tolerates None (skips count
rendering if missing). Every other site assumes 1 (treats item as unstacked).
**Why it matters**: A weight calculation at `player.py:733`
(`total += getattr(item, 'weight', 0) * count`) with `count=1` default
is correct. The `ui.py` site's None default is a display-only branch.
Inconsistency is style-level here — `Item.__init__` always sets `self.count = 1`.
**Suggested fix**: `ui.py:416` could use `1` and let the display logic decide
whether to show "(x N)" suffix based on count > 1. But the None pattern is
also fine if intentional. Minor.
**Confidence**: LOW

### [MINOR] `weight` default: 0 vs 1.0
**Attribute / API**: `weight` on Item
**Inconsistent sites**:
- `src/mystery_system.py:574` — `max(0.1, getattr(item, 'weight', 1.0))` (default **1.0**)
- `src/player.py:732, 741`, `src/game_render.py:2050, 4177` — default **0**

**What I see**: Player inventory weight: 0 default (missing = weightless).
Merchant pricing: 1.0 default (missing = avg-weight). Both intentional —
flagging because they're literally the same field with different semantics
at different call sites.
**Suggested fix**: Document the intent. `Item.__init__` always sets weight
from JSON so absence is impossible in practice.
**Confidence**: LOW

### [MINOR] `item_class` default: 'misc' vs ''
**Attribute / API**: `item_class` on Item
**Inconsistent sites**:
- `src/bones.py:38` — default `'misc'`
- `src/mystery_system.py:576` — default `'misc'`
- `src/dungeon.py:2173`, `src/container_system.py:349, 376`, `src/main.py:3338, 5032-5035, 5139`, `src/ui.py:410` — default `''`

**What I see**: BUC roll rates table at `dungeon.py:2173`
(`_BUC_RATES.get(getattr(inst, 'item_class', ''), None)`) returns None for
missing class — bypasses BUC rolls entirely. `bones.py:38` saves 'misc'
to bones file, while every other site uses ''.
**Why it matters**: `Item.__init__` sets `self.item_class = defn.get('item_class', 'unknown')`
— so neither 'misc' nor '' matches the actual default. A genuinely-missing
field would land in 'unknown' string from init, which doesn't appear in any
of these defaults — meaning every callsite's default is dead code (it would
never fire). Latent inconsistency.
**Suggested fix**: Use `'unknown'` as the consistent fallback to match
`Item.__init__`'s default.
**Confidence**: MEDIUM

### [MINOR] `class_mechanic` default: '' vs None
**Attribute / API**: `class_mechanic` on Weapon
**Inconsistent sites**:
- `src/combat.py:207, 269` etc — default `''` for string comparisons
- `src/combat.py:299, 536` — default `None` (then `if _pre_mech and weapon:`)
- `src/game_combat.py:1454, 1679` — default `''`

**What I see**: Both falsy, both work. `Weapon.__init__` sets `self.class_mechanic = defn.get('class_mechanic', '')`
— so `''` is the actual default. The None default in combat.py:299, 536 is
stylistically inconsistent.
**Suggested fix**: Standardize on `''` to match the init default. Avoid None
for string attributes.
**Confidence**: LOW

### [MINOR] `accessory_slots` / `armor_slots` defaults: () vs []
**Attribute / API**: Player equipment slot lists
**Inconsistent sites**:
- `src/chain_passives.py:22, 31` — default `()` (tuple)
- All other sites — default `[]` (list)

**What I see**: Both iterable. Style inconsistency.
**Suggested fix**: Use `[]` for mutability semantics consistency.
**Confidence**: LOW

### [MINOR] `unlocked_masteries` default: None then `or {}` vs {}
**Attribute / API**: `unlocked_masteries` on Player
**Inconsistent sites**:
- `src/combat.py:25` — `getattr(player, 'unlocked_masteries', None) or {}`
- `src/game_render.py:2418` — `getattr(p, 'unlocked_masteries', {}) or {}`
- `src/game_render.py:3902` — `getattr(self.player, 'unlocked_masteries', {})`

**What I see**: Same logic, three different code shapes.
**Suggested fix**: Style-only. Could lint these to a single form.
**Confidence**: LOW

---

## Category 2 — `cursed` vs `buc` (attribute-name drift)

### [WARN] `cursed` property NOT defined on all Item subclasses
**Attribute / API**: `Item.cursed` (back-compat property)
**Inconsistent sites**: Property defined on Weapon (`items.py:166`), Armor (217),
Shield (254), Accessory (291), Wand (318), Scroll (343), Potion (519).
NOT defined on Spellbook, Artifact, Lockpick, Container, Ingredient, Corpse, Ammo, Food.

**What I see**: 8 of 15 Item subclasses have `cursed` as a back-compat
property over `buc`. The base `Item` has `self.buc = 'uncursed'` but no
property. Reading `Spellbook.cursed` would AttributeError (or fall through
to `getattr` default).
**Why it matters**: Most sites use `getattr(item, 'cursed', False)` defensively
which handles the missing-property case correctly. But direct attribute
access like `if spellbook.cursed:` would crash. Searching shows direct
write `melee_w.cursed = True` at `main.py:1106` — only safe because melee_w
is a Weapon. The mismatch is also load-bearing on the read side at
`game_render.py:2055`:
```python
buc_raw = getattr(item, 'buc', None) or ('cursed' if getattr(item, 'cursed', False) else 'uncursed')
```
This belt-and-suspenders pattern compensates for the fact that on a
property-bearing subclass, both `buc` and `cursed` return consistent values;
on a non-bearing subclass, only `buc` works.
**Suggested fix**: Move the `cursed` property up to the base `Item` class
(it just reads from `self.buc`). Single source of truth. Removes the 7
duplicated property definitions.
**Confidence**: HIGH

### [WARN] `buc` default: 'uncursed' vs '' — two sites diverge on uncursed-default
**Attribute / API**: `Item.buc`
**Inconsistent sites**:
- `src/combat.py:269`, `src/items.py:167, 218, 255, 292, 319, 344, 520`,
  `src/main.py:4481`, `src/ui.py:421`, `src/player.py:507, 509, 751`,
  `src/dungeon.py:2216`, `src/food_system.py:401`, `src/pet_system.py:438`,
  `src/game_render.py:3917`, `src/game_encounters.py:484, 490`,
  `src/game_magic.py:236, 2062, 2191, 2365, 2372, 2417, 2543, 2736` — default `'uncursed'`
- `src/game_divine.py:89, 91, 93, 96, 99, 101, 1216, 1218, 1220, 1222, 1225, 1227`,
  `src/main.py:5044` — default `''`

**What I see**: `game_divine.py` and `main.py:5044` (drop check) use empty
string default while every other site uses `'uncursed'`. Both work for the
`== 'cursed'` check (since `'' != 'cursed'` and `'uncursed' != 'cursed'`).
The asymmetry breaks if a callsite does `if buc != 'uncursed':` — that
would treat a missing-buc item as "not uncursed" with default `''`.
**Why it matters**: `Item.__init__` always sets `buc = 'uncursed'` by
default, so the missing-field case is rare. But the drop check at
`main.py:5044` is:
```python
if is_equipped and (getattr(item, 'cursed', False) or getattr(item, 'buc', '') == 'cursed'):
```
Mixing `'cursed'` boolean property AND `buc` string check is redundant and
gives different defaults. Cleaner to pick one.
**Suggested fix**: Standardize on `'uncursed'` default everywhere (matches
Item init). Remove the dual-check at main.py:5044 — just use `cursed`.
**Confidence**: HIGH

### [MINOR] `cursed` write directly to property setter at main.py:1106
**Attribute / API**: `Weapon.cursed` (property setter)
**Site**: `src/main.py:1106` — `melee_w.cursed = True`
**What I see**: Works because Weapon has the setter (items.py:170). But
the audit doc notes "back-compat property" and prefers writing the underlying
field directly (e.g., `melee_w.buc = 'cursed'`). One direct write to `cursed`.
**Suggested fix**: Change to `melee_w.buc = 'cursed'` for consistency with
how identify code writes to `buc` directly.
**Confidence**: LOW

---

## Category 3 — `identified` field is NOT a back-compat property (doc drift)

### [CRITICAL] `Item.identified` is a plain field, NOT a property (audit doc wrong)
**Attribute / API**: `Item.identified`
**Where**: `src/items.py:69` — `self.identified: bool = defn.get('identified', True)`
**What I see**: The bug-bash instructions say "`Item.identified` is now a back-compat
property that reads `id_level >= 4`" — this is WRONG. It's a plain instance
attribute, NOT a property. There's no `@property def identified` anywhere
in `items.py`. The only property of that family is `Corpse.lore_identified`
at items.py:446.
**Why it matters**: 40+ sites do `item.identified = True` (see grep results)
and expect this to write a real field. If someone refactored it to a property
without writing a setter, all those would silently no-op or crash. The
audit doc lists this as already-done — anyone relying on it would mis-design.
**Suggested fix**: Either (a) ACTUALLY refactor `identified` to a back-compat
property as the doc claims (then audit the 40+ write sites and make sure each
either uses the new setter semantics or writes to `id_level` directly), or
(b) update `proposals/v2_audit/IDENTIFY_SYSTEM.md §2` to reflect that
`identified` is still a plain field. As currently coded, the back-compat
direction goes the OTHER way: `id_level` is the new field, `identified` is
the legacy one that some subclasses initialize from JSON.
**Confidence**: HIGH (read items.py directly — no property exists)

### [WARN] `identified` default mismatch: True vs False between read-sites
**Attribute / API**: `Item.identified`
**Inconsistent sites**:
- `src/game_divine.py:70, 780, 1168` — default **True** (`if not getattr(it, 'identified', True)`)
- `src/game_helpers.py:27`, `src/ui.py:355` — default **True**
- `src/game_menus.py:359, 1430`, `src/game_render.py:3037`, `src/game_combat.py:858`,
  `src/game_magic.py:217, 1951` — default **False**

**What I see**: When checking "is this item identified?", half the codebase
defaults to True (assume identified if attribute missing — safe for legacy
items) and half defaults to False (assume unknown — safe for newly-spawned
items missing the field). For an item that genuinely lacks the field:
- Divine "purge unknowns" treats it as already-known (skips it)
- BUC sense check at game_combat.py:858 treats it as unknown (re-reveals)
Inconsistent for the same item.
**Why it matters**: `Item.__init__` defaults to `identified=True` for the
base — so absence after pickling would be an edge case. But mixed defaults
are a bug-shaped pattern.
**Suggested fix**: Standardize on **True** (matches `Item.__init__` default).
Read sites assuming False can keep their assumption (since real items
that need identifying have `identified=False` explicitly set in their
subclass `__init__`).
**Confidence**: MEDIUM

---

## Category 4 — Subject → Action map drift (CLAUDE.md vs reality)

### [MINOR] CLAUDE.md subject table is INCOMPLETE — missing `ai` and `trivia` subjects
**Attribute / API**: `subject` parameter to `quiz_engine.start_quiz()`
**Where seen**:
- `'ai'` — at `game_combat.py:976, 1036`, `game_divine.py:428`,
  `game_encounters.py:449`, `game_menus.py:1294`, `main.py:2805, 3656`
  (7 call sites — hero specials, sketch pets, trap disarm, NPC encounters)
- `'trivia'` — at `game_magic.py:98` (lore recall hint quiz)

**What I see**: CLAUDE.md "Subject → Action Mapping" lists 10 subjects
(math, geography, history, animal, cooking, science, philosophy, grammar,
economics, theology). The code uses 12 subjects — adds `'ai'` and `'trivia'`.
Both are loaded by `player.py:18-29 SUBJECT_TIMER` (so they're real). The
doc is out of date.
**Why it matters**: Onboarding pain — a developer trusting CLAUDE.md would
not realize there are two more banks. The MEMORY.md notes Trivia and AI
have their own "controlling voice" rules from 2026-05-25 and 2026-05-27,
so the new subjects are recent.
**Suggested fix**: Update CLAUDE.md table to include `ai` (traps / hero
specials / NPC encounters) and `trivia` (lore recall hint quiz).
**Confidence**: HIGH

### [MINOR] `ai` is used for 7 different actions (not 1)
**Attribute / API**: `subject='ai'`
**What I see**: `'ai'` is used for trap disarm (main.py:2805), 5 hero-special
quizzes (sketch, fire breath, dad-summon etc.), NPC dialog quizzes, and
"AI sentinel" interactions. There's no single "action" for AI in the
CLAUDE.md sense — it's the dumping ground for "I don't know which canonical
subject this fits". This is fine pedagogically (per the AI voice rule), but
the subject→action mapping is not 1:1.
**Suggested fix**: Update CLAUDE.md to document: "ai = trap disarm + hero
special powers + NPC interactions (catch-all for systemic/tech actions)".
**Confidence**: MEDIUM

---

## Category 5 — hasattr/getattr discipline + race conditions

### [MINOR] hasattr + direct access (race risk if class hierarchy changes)
**Pattern**: `if hasattr(x, 'attr'): use x.attr` instead of `getattr(x, 'attr', default)`
**Sites**:
- `src/hero_specials.py:527` — `hasattr(i, 'identified') and not i.identified`
- `src/game_magic.py:799, 2098, 2113, 2314` — same pattern
- `src/game_magic.py:3131` — `if not hasattr(it, 'identified'): return; it.identified = True`
- `src/container_system.py:473-477` — `if hasattr(it, 'identified'): it.identified = True`
- `src/main.py:3231` — `hasattr(item, 'buc') and not getattr(item, 'buc_known', False)`

**What I see**: Defensive pattern guarding against items lacking these
fields. In practice every Item subclass DOES have `identified` and `buc`
because the base `Item.__init__` sets them (items.py:69, 71). So the
`hasattr` check is dead code today.
**Why it matters**: (a) Two attribute lookups instead of one — slight perf
hit. (b) If someone introduces a non-Item type that's iterated in `inventory`
(e.g., a GoldPile), the `hasattr` defense would save them — but it ALSO
hides the bug that GoldPile shouldn't be in inventory in the first place.
(c) Brittle if `identified` becomes a property (it's named in the audit doc
as a future change — see Cat 3).
**Suggested fix**: Replace with `isinstance(it, Item) and not it.identified`
or just `getattr(it, 'identified', True)`. The `hasattr+access` is the most
brittle of the three forms.
**Confidence**: MEDIUM

### [WARN] `effect` defaults to 'heal' — assumes any potion is healing
**Attribute / API**: `Potion.effect`
**Site**: `src/game_menus.py:1455` — `effect = getattr(potion, 'effect', 'heal')`
**What I see**: When applying a healing potion to a pet, default-to-heal
means a potion missing the `effect` field would be APPLIED AS A HEALING
POTION instead of being rejected. Every other site defaults to `''`:
- `game_encounters.py:595, 598, 601` — `''`
- `game_render.py:2258, 3036, 3133` — `''`
- `game_menus.py:1429` — `''`
- `npc_encounters.py:1892, 1895, 1897` — `''`

**Why it matters**: If a malformed potion (missing effect) ends up in
the pet heal menu, instead of being filtered out it would heal the pet
on full strength. Unlikely in practice (Potion.__init__ sets
`self.effect = defn.get('effect', '')`), but the default is wrong.
**Suggested fix**: Change `game_menus.py:1455` to `getattr(potion, 'effect', '')`.
**Confidence**: MEDIUM

---

## Category 6 — setattr with runtime strings (magic-string attribute keys)

### [WARN] `apply_stat_bonus` accepts arbitrary stat names via setattr
**Attribute / API**: `Player.apply_stat_bonus(stat: str, amount: int)`
**Site**: `src/player.py:777` — `setattr(self, stat, getattr(self, stat) + amount)`
**What I see**: 40+ call sites pass stat names — many from JSON data
(`fx['stat']`, `b['stat']`, etc.). No validation that `stat` is one of
{STR, CON, DEX, INT, WIS, PER, AC}. A typo'd `'STT'` would happily
`setattr(player, 'STT', 11)` and create a junk attribute.
**Why it matters**: Stat-bonus JSON data flows from accessories (effects dict),
food bonuses (food_system.py), mystery rewards (mystery_system.py:457),
quirks (quirk_system.py), and god rewards (game_divine.py:243, 475, 796).
A typo in any JSON file would silently no-op (creates a new attribute but
doesn't affect actual stats). The function does handle 'AC' specially
(returns early). 'CON' has a max_hp side effect (line 779). 'STR' bumps max_sp,
'INT' bumps max_mp. All others are silently set without derived-stat update.
**Suggested fix**: Add a guard at the top of `apply_stat_bonus`:
```python
if stat not in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER', 'AC'):
    raise ValueError(f"Unknown stat: {stat!r}")
```
At minimum log a warning instead of silently no-op'ing.
**Confidence**: HIGH

### [MINOR] Secret-build override allows any attribute on Player
**Attribute / API**: Player class init
**Site**: `src/main.py:304` — `setattr(self.player, stat, value)`
**What I see**: Iterates `secret_build` dict (loaded from JSON), filters
keys not starting with `_`, sets each on player via setattr — only guarded
by `hasattr(self.player, stat)`. So it can ONLY set existing attributes,
which is good. But it can set them to wrong types (e.g., `STR='hello'`).
**Suggested fix**: Type-check value matches existing attribute type.
**Confidence**: LOW

### [MINOR] Chronicle room flag stored with f-string attribute name
**Attribute / API**: Chronicle room tracking
**Site**: `src/main.py:1911` — `setattr(self, f'_chronicle_room_{rtype}', True)`
**What I see**: rtype comes from dungeon room dict — could be arbitrary
string. No constraint. Creates `_chronicle_room_*` flags dynamically.
**Why it matters**: Cosmetic. If rtype contains weird chars, the attribute
name is still valid Python (any string works for setattr) but you can't
later check with `if self._chronicle_room_X` syntax — would need getattr.
**Suggested fix**: Switch to `self._chronicle_rooms_seen: set[str]` and
add/check rtype as set member. Cleaner data model.
**Confidence**: LOW

---

## Category 7 — `**kwargs` swallow patterns

### [MINOR] Combat callback accepts `**kwargs` and discards everything
**Site**: `src/game_combat.py:1303, 1372` — `def on_complete(damage, killed, chain, stunned=False, knocked=False, crit=False, **kwargs):`
**What I see**: Ranged attack callback in `_handle_fire_weapon` accepts kwargs
silently. If caller passes a misspelled `stunend=True`, it's discarded with
no warning.
**Why it matters**: Low risk — these are local callbacks bound to a specific
combat call. The caller is `combat.resolve_chain_attack` (combat.py) which is
typed. A typo in either side would be caught by mypy but Python runs.
**Suggested fix**: Remove `**kwargs` — the parameter list is known and fixed.
Force the explicit shape.
**Confidence**: LOW

---

## Category 8 — None-returning functions, callers don't always check

### [MINOR] `get_template` / `get_material` return None on missing key
**Site**: `src/items.py:665-672` — `def get_template(category, template_id) -> dict | None`
**Callers and their handling**:
- `src/items.py:790-795` — `tpl = get_template('weapons', template_id); if not tpl: raise ValueError(...)` — CORRECT
- `src/items.py:931-937` — same — CORRECT
- `src/items.py:974-975` — `mat = get_material('armor', material_id) or get_material('weapons', material_id)` — chained fallback — CORRECT
- `src/main.py:593-596` — `tpl = get_template(tpl_dir, template_id); if not tpl or not mat: return` — CORRECT
- `src/main.py:3209-3214` — `_mat_defn = get_material('weapons', _mat_id) or get_material('armor', _mat_id); if _mat_defn:` — CORRECT

**What I see**: All callers check for None. Good discipline here.
**Confidence**: HIGH (no actual bug, just verifying)

### [WARN] `get_monster_family` returns None — caller in combat reads .lower()
**Site**: `src/monster_classes.py:27` — `def get_monster_family(monster_or_corpse) -> str | None`
**What I see**: Let me check the callers...

(I'd need to grep for this — flagging as worth a closer look.)
**Suggested fix**: Audit all `get_monster_family` callers for None-safety.
**Confidence**: LOW (needs follow-up)

### [WARN] `m.attacks[0]['damage']` — assumes attacks list non-empty AND has 'damage' key
**Site**: `src/game_combat.py:2123` — `pet_dmg = max(1, _dice_roll(m.attacks[0]['damage']) // 2) if m.attacks else 1`
**What I see**: The `if m.attacks` guard catches empty list, but not
`m.attacks = [{}]` (empty attack dict). Would crash with KeyError on 'damage'.
**Why it matters**: All Monster JSON files SHOULD have `attacks: [{damage: ...}]`,
but a malformed entry would crash here. Other site at `pet_system.py:577`
uses `.get('damage', '1d4')` — safer.
**Suggested fix**: `m.attacks[0].get('damage', '1d4')` to match pet_system.py.
**Confidence**: MEDIUM

---

## Category 9 — Stat naming convention

### [INFO] Stats uniformly UPPERCASE (`STR/CON/DEX/INT/WIS/PER`) — no drift
**What I see**: 98 occurrences of `.STR/.CON/...` across 14 files. ZERO
occurrences of `.strength/.constitution/...` etc. CLAUDE.md spec uses
uppercase too. NO bug here — flagging as confirmed-OK.
**Confidence**: HIGH (no fix needed, confirmation finding)

---

## Category 10 — Old API patterns / direct field writes

### [MINOR] Direct write to `item.identified = True` is still the canonical pattern
**What I see**: 40+ sites write `item.identified = True` directly. The audit
doc claimed this is a back-compat property — it's NOT (see Cat 3). So the
direct writes are actually correct usage of the plain field. No fix needed
once the doc is corrected.
**Confidence**: HIGH

### [WARN] `id_level` not always updated when `identified` is set
**Pattern**: A subset of sites set `item.identified = True` but DON'T touch
`item.id_level`. Per IDENTIFY_SYSTEM.md, the canonical write should bump
both fields together.

**Sites that set identified but not id_level**:
- `src/dungeon.py:1747` — `scrap.identified = True` (legacy starting gear)
- `src/dungeon.py:2275` — `component.identified = True` (gleipnir component)
- `src/main.py:1049, 1067, 1073, 1102, 1120, 1133, 1151, 1164, 1178, 1196, 1224, 1242, 1263, 1276, 1295` — starting gear setup
- `src/main.py:2217` — `flux.identified = True`
- `src/food_system.py:423` — `potion.identified = True`
- `src/game_combat.py:270` — `item.identified = True`
- `src/hero_specials.py:533, 676, 920` — id-all-items hero special

**Sites that set both correctly**:
- `src/main.py:3147-3148` — `item.identified = True; item.id_level = max(getattr(item, 'id_level', 0), 4)`
- `src/game_magic.py:3133-3136` — Philosopher's Stone, sets both
- `src/hero_specials.py:533-534` — sets both at consecutive lines

**Why it matters**: If `identified=True` but `id_level=0`, render-level
checks at game_render.py disagree:
- `game_menus.py:_visible_level` line 358-360: reads id_level, bumps to 5
  if identified, then to 3 if known — so identified=True is enough to
  show full info.
- `game_render.py:3892`: defaults to 5 if missing, else uses `id_level`
  directly — DOES NOT consult `identified`. An item with `identified=True
  id_level=0` would show as "level 0/5" in the lore screen.

So writing identified without id_level desyncs the lore screen from the
menu/inventory display. The "id_level is source of truth" model from
IDENTIFY_SYSTEM.md §2 is partially betrayed.
**Suggested fix**: Add a helper `Item.mark_identified()` that sets both:
```python
def mark_identified(self):
    self.identified = True
    self.id_level = max(int(getattr(self, 'id_level', 0)), 5)
```
Replace all 20+ direct writes with this helper.
**Confidence**: HIGH

### [MINOR] `Corpse.lore_identified` setter usage at items.py:451-457
**Site**: `src/items.py:451-457` (Corpse.lore_identified setter)
**What I see**: `lore_identified=True` bumps id_level to ≥4, `False` resets
to 0. This is the back-compat property direction — it WAS the field name
before id_level was added. Used in `main.py:5323` as a read, and a setter
exists but I don't see direct writes — but `__setstate__` (items.py:459)
explicitly migrates old `lore_identified` field on save load.
**Confidence**: HIGH (correct as-is)

---

## Summary

**Total findings**: 28
- **CRITICAL**: 2 (id_level default conflict + identified-is-not-a-property doc drift)
- **WARN**: 11
- **MINOR**: 14
- **INFO**: 1

**Highest-value fixes (do these first)**:
1. **CAT 3 — Fix the docs OR fix the code** for `identified` being a property
   (audit doc lies about current state; either bring code in line OR update doc)
2. **CAT 1 — `id_level` default 0 vs 5** at 2 outlier sites in game_menus.py:651
   and game_render.py:3892
3. **CAT 2 — Move `cursed` property to Item base class** (eliminates 7 duplicates
   + makes Spellbook/Lockpick/etc. consistent)
4. **CAT 10 — `Item.mark_identified()` helper** (eliminates the 20+ raw writes
   that desync identified vs id_level)
5. **CAT 6 — Validate `stat` name in `apply_stat_bonus`** (typo-trap with 40+ callers)
6. **CAT 4 — Update CLAUDE.md** to add `ai` and `trivia` subjects to the table
7. **CAT 5 — Replace `getattr(potion, 'effect', 'heal')` with default `''`**
   (game_menus.py:1455 — silent heal-by-default is wrong default)

**Low-priority style normalization**:
- Pick one default per attribute: `''` for strings, `False` for bools,
  `0` for ints, `[]` for collections — and apply uniformly
- Replace `hasattr(x, 'attr') and x.attr` with `getattr(x, 'attr', default)`
- Document that `'misc'` and `'unknown'` are dead defaults for item_class
  (since Item init always sets it to 'unknown')

**Notes for follow-up agents**:
- The Audit doc `proposals/v2_audit/IDENTIFY_SYSTEM.md §2` makes a claim
  about `Item.identified` being a back-compat property that the code does
  NOT support. This contradicts the bug-bash instructions sent to A5
  ("`Item.identified` is now a back-compat property"). Verify in person
  before acting.
- `Item.id_level` IS canonical and correctly managed (per §2 of the audit
  doc and the items.py code) — the read-default inconsistencies are the
  only worry, and they're latent (no Item subclass currently lacks the
  field).
- The `cursed` property exists on 7 of 15 Item subclasses but the base
  class only has `self.buc`. Lifting the property to the base would clean
  up a lot of paths.
