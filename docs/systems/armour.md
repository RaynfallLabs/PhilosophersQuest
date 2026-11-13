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
  tower 3). Which template a find is goes by a bell by floor
  (`gear.template_weight`): body armour and shields carry their own
  (`spawn_bell`: peak, spread, first floor), so each arrives in its turn
  down the whole run (scale from floor 12, chainmail and breastplates from
  20, banded and splint from 30, plate from 42, full plate from 55; kite
  and heavy wooden shields from 10, the tower shield from 35). Every other
  template goes by its weight class's bell (`weight_class_bells`).
  (2026-11-12: by weight class alone, any heavy find from floor 12 could
  be full plate, and the average hero wore it by floor 30, after which the
  plus was the only armour left to find.);
- the **material** gives the weight, what wear can touch it (rust, acid)
  and the name. It never gives protection;
- the **enchantment level** 0-10 (0 = plain) is rolled when the piece is
  found (`gear.roll_level`, bells by floor in `gear_rules.json` `levels`).
  Its **tier** is `ceil(level / 2)`: the quiz tier, and on body armour and
  shields the plus (`gear.plus_for_level`). Odd levels are a tier's lesser
  form, even levels its greater ("of Greater Iron Will II").

**Threshold** (Brandon's ruling: complexity and benefit set it):
`gear.equip_threshold` = weight class (2 / 3 / 4) + benefit by tier
(0, 0, 1, 1, 2) + 2 for a named unique, at most 7. Rings, amulets and
belts: `gear.accessory_threshold` = slot (ring 2, amulet 3, belt 3) +
benefit (0, 1, 1, 2, 2) + 2 for a unique, at most 7. Each kind is asked
only once a run (Known by Hand, section 1b), so these rose by one on
2026-11-13 (they were 1 / 2 / 3 and ring 1, amulet 2, belt 2, unique +1,
cap 5). Geography and history are untimed and every topic has a teaching
card: at 97% a threshold of 6 still passes 83% of the time. The named
pieces' authored thresholds are written by the same rule
(`tools/content/known_by_hand_thresholds_2026_11.py`, idempotent).

Blessed works a level higher, cursed a level lower
(`enchantments.effective_level`); a cursed body armour or shield wears its
plus as a minus.

## 1b. Putting gear on (winning-build plan 3.4, 2026-11-13)

**Known by Hand** (`src/known_by_hand.py`). The first time the hero passes
the equip quiz for a KIND, every copy of that kind goes on with no quiz,
whatever its plus, enchantment level or blessing. The kind is the item's
id: material + template for a common piece (`iron_breastplate`; a mithril
breastplate is a new kind), the kind for a ring or amulet (its id carries
no level: `ring_of_protection` at every level), and the unique itself for
a named piece (one quiz each). A chain-equip legend remembers the best
chain reached on it (`Player.by_hand_tiers`): put back on, it goes on at
that tier with no quiz, or the hero attunes again to climb (the best is
kept). Learnt for the run (`Player.known_by_hand`, saved); an old save
counts what is worn as known, and a hero's starting kit is known. A cursed
piece still refuses to come off. The Kit, the @ sheet and the equip menu
mark a known kind "Known by Hand" (BY HAND in the equip menu), and a line
says so when it fires ("You have worn one of these before. On it goes.").

**Donning time** (`gear.don_turns` / `doff_turns`, `gear_rules.json`
`donning`). Body armour takes 1 turn light, 3 medium, 5 heavy, 6 for the
full plate template (`gear.template_of`: the template_basis, else read from
a common piece's id); a shield, a minor piece, a ring, an amulet and a belt
1. Taking off is half, rounded up. A swap is the old piece off, then the
new one on. The turns are a busy action (`src/busy.py`,
`game_dressing.DressingMixin._busy_run`): they pass one at a time through
`_advance_turn`, the piece counts (AC, guards) only on its last turn and
its slot is empty until then, and a hostile coming into view or a blow
landing (`game_combat` counts `_blows_on_hero`) stops it with "Keep
dressing? (Y/N)". Stopping leaves the piece in the pack (or still on).
The Hephaestus quirk halves both times. A first-time kind's quiz comes
before the donning. A one-turn piece into an empty slot is exactly the old
equip: on, then the monsters act.

**At Your Back** (`Player.readied_weapon`). A melee weapon in the pack,
readied from the Kit or the @ sheet (R); S on the map swaps it with the one
in the hand in one turn. It stays in the pack (its weight counts; a drop,
a sale or a theft lets go of it), a cursed blade in the hand will not let
go, and a two-hander will not come out past a shield that will not come
off (an ordinary shield goes to the pack, as for any two-handed equip).

**Loadouts** (`src/loadouts.py`, Shift+E). Three saved kits (Kit One, Kit
Two, Kit Three; N renames): the wielded and readied weapons, shield, the
eight armour slots, amulet, belt and rings, saved as the very objects (S
saves what is worn). Putting one on takes the sum of its pieces' turns,
shown before confirming; a piece not in the pack is skipped, a piece not
known by hand is refused ("put it on once first"), and a slot that was
empty when the kit was saved is left alone.

## 2. AC: body armour and shield only

`Player.get_ac()` = 10 - (body base + plus) - (shield base + plus) - DEX
(at most 3) - BUC of those two - effects (invisible, shielded, procs).
`Player.core_ac()` is the body and shield part; `gear.ac_value(item)` one
piece's. **No helm, gloves, boots, cloak, shirt, ring or amulet gives AC.**

Monster to-hit was rebaked to this line (`tools/balance/rebake_thac0.py`,
`thac0` in `monsters.json`, the original kept as `thac0_lore`): a typical
monster hits a hero of its floor about 55% of the time on every floor.
The line is the mean AC a hero wears (best body armour and best shield
found, from the game's own spawns), from what the plain hero starts with:
no armour, AC 10 (until 2026-11-12 it assumed leather and a shield, AC 7,
so the first floors' monsters were aimed three points too straight). It
runs AC 9 on floor 1, 2 on floor 20, -3 on 40, -7 on 60, -10 on 80 and
-11 on 100. A hero with a two-handed weapon gives up the shield: the
difficulty simulator weighs the heavier blow against the shield's AC
(`Run._choose_kit`) and, deep, the shield wins, since without one a
typical monster lands about 95% of its swings.

Because a hero finds about ten pieces of gear a floor deep down and keeps
the best, nearly every hero wears par: common armour only keeps you level
with the monsters. A named piece is what puts you ahead (section 6).
A miss that rolled short is a miss (`MIN_HIT_ORDINARY` 0); a named foe
still lands 15% of its misses (`MIN_HIT_NAMED`).

## 3. The minor slots guard families (`guards.py`)

Every attack carries a `delivery` (`monsters.json`, written by
`tools/content/tag_attack_delivery.py`): blow, bite, sting, trample,
grapple, touch, ranged, breath, gaze, voice. Each minor slot guards one
family (`data/armor_guards.json`):

| Slot | Family | Takes a share off the damage of | Stops a share of the riders |
|---|---|---|---|
| head | gazes and voices | voice, gaze | fear, confusion, sleep, hallucination, stun, blinding |
| hands | touches and grabs | touch, grapple | paralysis, holds, freezing |
| arms | arrows and missiles | ranged | their riders |
| legs | bites and stings | bite, sting | poison, disease |
| feet | trampling and snares | trample | slowed, held, frozen; stun from a blow |
| cloak | breath and elements | breath; fire, cold, lightning, acid | burning, frozen |
| shirt | poison and draining | poison, drain, necrotic | poison, disease, bleeding, weakening |

A piece's own guard is its weight class (light 5% / 3%, medium 10% / 6%,
heavy 15% / 9%), plus a guard enchantment of its family. Caps: 80%. A guard
never makes an attack miss: it takes a share off a matching hit's damage and
stops a share of what the hit carries, and the card says so in one line,
the make and the enchantment together (`guards.guard_text`; the enchantment
is not counted until the copy is known; `enchantments.is_slot_guard`).
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
  Striking is +4% to +6% (halved 2026-11-12: a small damage boost shortens
  fights by whole monster turns, and the model's straight line had priced
  it at half its worth).
- **craft**: the Scholar, Reader, Adept, Locksmith, Cook, Hunter, Kneeler,
  Wanderer: the first wrong answer of every Nth quiz on that subject is
  forgiven (N 6..3 by level, counted, never rolled; `quiz_engine.craft_hook`
  asks `Game._craft_forgives`); Swift Strokes (math seconds), the Hair Shirt
  (prayer cooldown).
- **way**: the powers moved off rings: Telepathy, Night Eyes, True Sight,
  Alertness, Searching, the Eagle (PER), Ogre Power (STR), Dexterity,
  Speed, Levitation, Elvenkind (silent steps), Displacement.
  - **Speed** raises the hero's speed rating (`Player.get_speed`, on the
    scale of a monster's `speed`: 10 is ordinary) by 5% to 8% (tiers IV-V).
    The world moves 10/speed of a turn each time the hero acts
    (`Game._advance_turn`, no dice): at 10.5 the monsters miss one action in
    twenty-one. Haste doubles the rating. Neither touches the quiz clock:
    Wisdom sets the clock (Brandon, 2026-11-12). Half a point of speed is
    worth about 0.8 AC points, so Speed sits a little above its budget on
    purpose. Named boots (the Greaves of Hermes, the Boots of Seven Leagues,
    the Winged Sandals) keep true haste by their lore.
  - **Displacement** is a ladder: 5% to 7.5% of monster attacks strike empty
    air (tiers III-V; `enchantments.displacement`). The spell's status keeps
    its 15% while it lasts; the larger counts.
  - See `NON_AC_GEAR_BALANCE_REPORT_2026_11_12.md` (root) for the fight
    simulator's numbers.

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
| Spell Turning | ring | takes 30 / 46 / 52 / 52 / 52% off the damage of magic, shadow and psionic attacks |
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
tier ladder's AC). One found by depth has at least `gear.named_ac_floor` of
its peak floor: the common par there plus 2 for body armour, 1 for a shield
(`gear_rules.json` `named_ac`, written by
`tools/balance/rebase_unique_armour.py`, which also raises a chain-equip
piece's ladder to it). Before 2026-11-12 most named body armours were one
to five points under the common plate of their own floor (the Armor of
Ragnarok 9 against 13); now Sigurd's mail is 14 and Ragnarok 15. Starting
and quest pieces keep their own. A named minor piece has no AC and one enchantment of its
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
`test_armor_template_thresholds.py`, `test_recompose_migration.py`,
`test_swapping_without_the_chore.py` (Known by Hand, donning, At Your
Back, Loadouts, saves).
