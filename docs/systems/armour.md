# Armour, shields, rings and amulets

**Since 3.3.2** (bug bash 3.3.2, commits "Armour 1/7" to "Armour 7/7"). The
design and its proof: [docs/design/ARMOR_REDESIGN_PLAN.md](../design/ARMOR_REDESIGN_PLAN.md)
(revision 3) and `tools/balance/armor_model.py`. Read this before touching
AC, a monster's to-hit, an armour slot, an enchantment, a ring or the gear
loot roll.

**Code:** `src/gear.py` (levels, tiers, thresholds, AC, the loot split),
`src/guards.py` (what the minor slots guard), `src/enchantments.py` (the
minor-slot enchantments), `src/rings.py` (ring and amulet kinds),
`src/gear_saves.py` (old saves), `src/items.py` (`instantiate_armor`,
`instantiate_shield`, `Armor.relevel`, `Accessory.relevel`,
`pick_random_gear_for_floor`).
**Data:** `data/gear_rules.json`, `data/armor_guards.json`,
`data/enchantments.json`, `data/ring_kinds.json`, `data/templates/armor`
and `shields`, `data/materials/armor`, `data/items/armor.json`, `shield.json`,
`accessory.json`.

---

## 1. The item model

A common piece is **template x material x enchantment level**:

- the **template** gives the slot, the weight class (light / medium /
  heavy, its `armor_class_tier`) and, for body armour and shields only, the
  base AC (`base_ac_value`: padded 1 ... full plate 8; buckler 1, kite 2,
  tower 3);
- the **material** gives the weight, what wear can touch it (rust, acid)
  and the name. It never gives protection;
- the **enchantment level** 0-10 (0 = plain) is rolled when the piece is
  found (`gear.roll_level`, bells by floor in `gear_rules.json` `levels`).
  Its **tier** is `ceil(level / 2)`: the quiz tier, and on body armour and
  shields the plus (`gear.plus_for_level`). Odd levels are a tier's lesser
  form, even levels its greater ("of Greater Iron Will II").

**Threshold** (Brandon's ruling: complexity and benefit set it):
`gear.equip_threshold` = weight class (1 / 2 / 3) + benefit by tier
(0, 0, 1, 1, 2) + 1 for a named unique, at most 5. Rings, amulets and
belts: `gear.accessory_threshold` = slot (ring 1, amulet 2, belt 2) +
benefit (0, 1, 1, 2, 2) + 1 for a unique.

Blessed works a level higher, cursed a level lower
(`enchantments.effective_level`); a cursed body armour or shield wears its
plus as a minus.

## 2. AC: body armour and shield only

`Player.get_ac()` = 10 - (body base + plus) - (shield base + plus) - DEX
(at most 3) - BUC of those two - effects (invisible, shielded, procs).
`Player.core_ac()` is the body and shield part; `gear.ac_value(item)` one
piece's. **No helm, gloves, boots, cloak, shirt, ring or amulet gives AC.**

Monster to-hit was rebaked to this line (`tools/balance/rebake_thac0.py`,
`thac0` in `monsters.json`, the original kept as `thac0_lore`): a typical
monster hits a hero of its floor about 55% of the time on every floor.
A miss that rolled short is a miss (`MIN_HIT_ORDINARY` 0); a named foe
still lands 15% of its misses (`MIN_HIT_NAMED`).

## 3. The minor slots guard families (`guards.py`)

Every attack carries a `delivery` (`monsters.json`, written by
`tools/content/tag_attack_delivery.py`): blow, bite, sting, trample,
grapple, touch, ranged, breath, gaze, voice. Each minor slot guards one
family (`data/armor_guards.json`):

| Slot | Family | Turns aside damage of | Shrugs off riders |
|---|---|---|---|
| head | the mind and the senses | voice, gaze | fear, confusion, sleep, hallucination, stun, blinding |
| hands | touch and grip | touch, grapple | paralysis, holds, freezing |
| arms | missiles | ranged | their riders |
| legs | bites and stings | bite, sting | poison, disease |
| feet | footing | trample | slowed, held, frozen; stun from a blow |
| cloak | what washes over you | breath; fire, cold, lightning, acid | burning, frozen |
| shirt | what gets under the armour | poison, drain, necrotic | poison, disease, bleeding, weakening |

A piece's own guard is its weight class (light 5% / 3%, medium 10% / 6%,
heavy 15% / 9%), plus a guard enchantment of its family. Caps: 80%.
`guards.guard_keep(player, attack)` returns the share of damage and of the
rider chance kept; `monster.py` applies it. A **touch** attack rolls
against touch AC (the hero's AC without body armour and shield,
`guards.touch_ac`).

## 4. The enchantments (`enchantments.py`)

A minor piece of level 1+ carries ONE enchantment of its own slot, in four
lanes (`data/enchantments.json` `lanes` weights the roll):

- **guard**: Iron Will, Life-Grip, Deflection, Mailed Shins, Free Stride,
  Elementward and Vapourward (their own families), Vigor; Parrying (a melee
  blow from beside parried). Ladders priced by the armour model.
- **might**: Striking and Archery (more damage, `combat.strike_damage`).
- **craft**: the Scholar, Reader, Adept, Locksmith, Cook, Hunter, Kneeler,
  Wanderer: the first wrong answer of every Nth quiz on that subject is
  forgiven (N 6..3 by level, counted, never rolled; `quiz_engine.craft_hook`
  asks `Game._craft_forgives`); Swift Strokes (math seconds), the Hair Shirt
  (prayer cooldown).
- **way**: the powers moved off rings: Telepathy, Night Eyes, True Sight,
  Alertness, Searching, the Eagle (PER), Ogre Power (STR), Dexterity,
  Speed, Levitation, Elvenkind (silent steps), Displacement.

`from_tier` / `skip_tiers` say where an enchantment rolls. A worn stat
follows the piece (`Player.sync_worn_stats`); a worn flag is read by
`gear.wears_flag`. Wear takes a minor piece down a level; the smith gives it
back.

## 5. Rings and amulets (`rings.py`)

The commons are ten **kinds** (`data/ring_kinds.json`), each found at a
level on the same bells, so a ring found deep is a stronger ring:

| Kind | Slot | What it does, tier I .. V |
|---|---|---|
| Protection | ring | a saving throw: shrugs off 16 / 19 / 24 / 28 / 28% of any attack's rider |
| Spell Turning | ring | turns aside 30 / 46 / 52 / 52 / 52% of magic, shadow, psionic damage |
| Regeneration | ring | mends 11-33% of the health bar per hundred turns |
| Invisibility | ring | invisible; the veil slips when you strike and settles after 10 .. 2 quiet turns (from tier II) |
| Sustenance | ring | hunger comes on 33-75% more slowly |
| Wizardry | ring | spells cost 10-30% less mana |
| Life Saving | amulet | once, a killing blow leaves 25 / 50 / 75% of the health bar (from tier III) |
| Wisdom, Intellect, Constitution | amulet | +tier to the stat |

Two rings of one kind do not add: the stronger counts (as for the stats).
The cursed kinds (teleportitis, aggravation, fumbling, slowing, drain,
doom) are traps found at every depth. Every level of a kind is one learned
type (`items.type_class`). An Enchant Ring scroll moves a kind's level.

The 79 named rings and amulets keep their stories; a power that moved to
armour stays only where the item's lore makes it its own
(`tools/content/ring_kinds_2026_11.py`, `UNIQUE_REVIEW`, with the reason
for each). A unique may still break the rules about AC and powers where
Brandon says so (Hypatia keeps True Sight and her mob shield). The
Philosopher's Ring of Mastery carries Socrates' daimonion (`daimonion: 3`):
three times a floor, a wrong choice in any quiz is struck out before it
counts and the question stays open (`quiz_engine.daimonion_hook`,
`Game._daimonion_stops`).

## 6. Named armour and shields

`tools/content/unique_armor_ladder_2026_11.py`: a named piece's tier is a
step above the commons of its depth (never under its authored tier; start
kits and quest pieces keep theirs), its level that tier's greater form. A
named body armour or shield has base + plus AC (a chain-equip one keeps its
tier ladder's AC). A named minor piece has no AC and one enchantment of its
slot chosen by its lore (`PICKS`, with the reason); it keeps its name, card
and every signature power (`enchantments.apply_named`, the line in
`ench_line`).

## 7. Where gear comes from

A find of common gear is a weapon, an armour piece or a shield
**45 / 45 / 10** (`gear_rules.json` `loot_split`, `gear.pick_gear_class`,
`items.pick_random_gear_for_floor`): floor rooms, monster drops and chests'
gear all roll it, and an armour find is any of the eight slots evenly.
Traders stock from the same rolls.

## 8. Old saves

On load, after the composite recompose (`Game._migrate_recompose_composite_items`:
a common piece's AC from its template, an old minor plus as two levels a
point), `gear_saves.migrate`: an enchanted common keeps its name, a
pre-enchantment minor piece gets one enchantment (rolled from its id),
named pieces and rings take today's data (keeping blessing, knowledge,
wear, attunement and a higher scroll plus), worn statuses and stats
re-sync. A folded common ring heals into its kind at its old tier
(`LEGACY_ACCESSORY_ID_REMAP`); a ring whose power moved to armour has no
survivor and keeps working as the object it was.

## 9. Tests

`tests/test_bugbash_332_guards.py`, `_enchantments.py`, `_rings.py`,
`_unique_armor.py`, `_loot_split.py`, `_gear_saves.py`, `_cards.py`,
`test_armor_template_thresholds.py`, `test_recompose_migration.py`.
