# Armour, shields, rings and amulets

**Since 3.3.2** (bug bash 3.3.2, commits "Armour 1/7" to "Armour 7/7"). The
design and its proof: [docs/design/ARMOR_REDESIGN_PLAN.md](../design/ARMOR_REDESIGN_PLAN.md)
(revision 3) and `tools/balance/armor_model.py`. Read this before touching
AC, a monster's to-hit, an armour slot, an enchantment, a ring or the gear
loot roll.

**Code:** `src/gear.py` (levels, tiers, thresholds, AC, the loot split, and
its last section, What armour does beyond AC: forms, elements, wards, the
weight class),
`src/defence.py` (the defence model: AC, dodge, speed, the load tiers),
`src/guards.py` (what the minor slots guard), `src/enchantments.py` (the
minor-slot enchantments), `src/rings.py` (ring and amulet kinds),
`src/gear_saves.py` (old saves), `src/items.py` (`instantiate_armor`,
`instantiate_shield`, `Armor.relevel`, `Accessory.relevel`,
`pick_random_gear_for_floor`).
**Data:** `data/gear_rules.json`, `data/armor_guards.json`,
`data/enchantments.json`, `data/ring_kinds.json`, `data/templates/armor`
and `shields`, `data/materials/armor`, `data/items/armor.json`, `shield.json`,
`accessory.json`. The forms and elements are written, with their lore and
their price, by `tools/content/armour_profiles_2026_11.py`.

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
  template goes by its weight class's bell (`weight_class_bells`). Five
  light and medium body templates carry a second bell, `deep_bell`
  (Brandon's defence-model decision 20, 2026-11-17): studded leather (from
  35), hide (45), padded (45), the hauberk (32) and scale (50) come back on
  the deep floors in the deep materials they take, so a Dexterity hero
  finds a drakeskin or dragonhide jerkin, a spider-silk or elven-silk coat,
  a mithril hauberk, dragonscale mail. They keep their template's AC
  (studded leather 3 + its plus against full plate's 8 + its plus): the
  lower AC is the trade for the dodge and the speed. Body finds by class,
  light / medium / heavy: floors 41-60 9 / 12 / 79%, 61-80 22 / 22 / 56%,
  81-100 30 / 25 / 45% (they were 0 / 1 / 99%, 0 / 0 / 100% and
  0 / 0 / 100%). (2026-11-12: by weight class alone, any heavy find from
  floor 12 could be full plate, and the average hero wore it by floor 30,
  after which the plus was the only armour left to find.);
- the **material** gives the weight, what wear can touch it (rust, acid,
  fire), the name and, on body armour, the elements it turns or lets
  through (section 1c; until 2026-11-13 it "never gave protection");
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
breastplate is a new kind), and the unique itself for a named piece (one
quiz each). A ring or amulet KIND is known by kind AND tier (Brandon,
2026-11-16: "a deeper level of a known kind asks its own quiz"; it was the
kind at every level, so a Ring of Greater Protection V on floor 95 asked
nothing once any Protection ring was worn): `Player.by_hand_ring_tiers`
holds the highest tier of each kind put on (`known_by_hand.ring_tier`, the
tier its quiz is set at, `gear.tier_for_level`: a lesser and a greater
form share one). That tier or lower goes on with no quiz; a higher one
asks its own once. Belts have no kinds today (each a named piece, one
quiz). An old save counts a worn ring at its own tier and a ring kind
known but not worn at the kind's first tier
(`known_by_hand.migrate_ring_tiers`). A chain-equip legend remembers the best
chain reached on it (`Player.by_hand_tiers`): put back on, it goes on at
that tier with no quiz, or the hero attunes again to climb (the best is
kept). Learnt for the run (`Player.known_by_hand`, saved); an old save
counts what is worn as known, and a hero's starting kit is known. A cursed
piece still refuses to come off. The Kit, the @ sheet and the equip menu
mark a known kind "Known by Hand" (BY HAND in the equip menu), and a line
says so when it fires ("You have worn one of these before. On it goes.").

**One disguise per kind** (round 3, 2026-11-14). Because Known by Hand
tells kinds apart, two kinds may never share an unidentified name: the BY
HAND mark, or an equip with no quiz, would say which one it is. The name
may show the material's class (cloth, hide, metal) but belongs to one
kind. A common piece's disguise is `items.material_unidentified_name`: the
material's `disguise` kept as written when it has one, else its flavour
`unidentified_descriptor` trimmed to fit (`compose_unidentified_name`).
Linen and rawhide both trimmed to "Rough" (a Rough Cloak was either), so
they are "Rough Cloth" and "Rough Hide" now (Brandon: "a linen and hide
plate are not both 'rough' but 'rough cloth' and 'rough hide'"); an old
save's pieces take today's disguise on load
(`Game._migrate_recompose_composite_items`). `tests/test_disguises.py`
checks every kind any spawn path can make, named pieces and the run's dealt
ring and amulet looks included.

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
A friend coming into view (an encounter's person, the unicorn, an allied
angel: `game_combat._is_bystander`) does not stop it; a hero who falls
asleep or is paralysed stops where he is, as if he had said no; and a
piece that is no longer in the pack (a thief's blow took it) is dropped
from the action with a line, spending no more turns (bug bash 2026-11-13,
WB-A02 to A04).
The Hephaestus quirk halves both times. A first-time kind's quiz comes
before the donning. **A failed equip quiz costs the donning time**
(Brandon, 2026-11-16: "LORE over FLOOR means that I expect lore and logic
to take priority over artificial balance... use the equip length as
'lost' turns on a failure"; it cost one turn): the hero struggles with the
piece for its donning turns and gives up (`game_dressing._equip_failed`:
"You struggle with the {piece} for {n} turns and give up.": heavy body
armour five, full plate six, a ring or shield one). The turns
pass one at a time through `_advance_turn`, so the monsters act on each;
a blow does not stop them (they are already spent), only death or a
change of floor or screen. Armour and shields (`_start_armor_quiz`), rings,
amulets and belts (`_equip_accessory`) and an attuning legend
(`_start_chain_equip_quiz`) all pay it. A one-turn piece into an empty slot is exactly the old
equip: on, then the monsters act.

**At Your Back** (`Player.readied_weapon`). A melee weapon in the pack,
readied from the Kit or the @ sheet (R); S on the map swaps it with the one
in the hand in one turn. It stays in the pack (its weight counts), a
cursed blade in the hand will not let go, and a two-hander will not come
out past a shield that will not come off (an ordinary shield goes to the
pack, as for any two-handed equip). **The shield comes back** (Brandon's
play-test, 2026-11-16: "it doesn't automatically swap BACK my shield"): the
shield a two-hander sent to the pack is remembered (`Player._shield_slung`,
set in `Player._apply_equip`), and a one-hander taken up again, by S or the
Kit's Equip, puts it back on the arm in the same one turn (Brandon: "ready
swapping weapon set should only take 1 turn, even if you equip a shield as
well"; "You sling the Greatsword at your back and draw the Shortsword and
take up your Buckler."; `DressingMixin._slung_shield`,
`_shield_back_on`). It is let go when another shield goes on or it leaves
the pack; a loadout's own shield slot decides for a kit.

**Remembered pieces** (`src/loadouts.py`, round 3, 2026-11-14; Brandon:
"persist sets under the quickswapping function if a weapon is dropped or
thrown"; it reversed bug bash WB-A06). The weapon At Your Back and every
kit keep a piece that leaves the pack by being **dropped, thrown or
stolen**. While it is away the Kit lists it last, "Silver Mace (not
carried)" (source "At Your Back", Lore its only action), the @ sheet's Back
row and the Loadouts screen say "(not carried)", and S says "Your Silver
Mace is not with you. Pick it up again and S draws it." Picked up again (a
dead thief gives it back, `theft.give_back`), it is in its place again by
itself, and one line after the pickup says so ("The Silver Mace is At Your
Back again.", "The Iron Helm is back in Kit One.":
`DressingMixin._sets_note_back`). It is **let go for good** when sold
(`game_traders._trader_sell`), destroyed (a thrown weapon that shatters, a
cursed piece the smith cuts off), used up or made into another object:
`DressingMixin._sets_prune` lets go of a remembered piece found nowhere in
the world any more (not on any floor's ground or in a chest there, not in a
thief's hands), at most once a turn and before every save. A smith's
reforge works the same object, so the reforged weapon keeps its place.
Readying another weapon simply replaces the remembered one. The pieces are
the very objects, saved in one pickle with the floors, so identity
survives a save; an old save has none.

**Loadouts** (`src/loadouts.py`, Shift+E). Three saved kits (Kit One, Kit
Two, Kit Three; N renames): the wielded and readied weapons, shield, the
eight armour slots, amulet, belt and rings, saved as the very objects (S
saves what is worn). Putting one on takes the sum of the turns of the
pieces that change, the piece in each one's way coming off counted in.
The Loadouts screen shows it per piece beside each (`DressingMixin._kit_rows`:
"6 turns", "On now", "Not carried", "Stays off"), with the total under them
("2 pieces change: 7 turns in all.") and on the list ("7 turns to
change"), and the confirmation names each change ("Changes: Body 6 turns,
Shield 1 turn."; Brandon's play-test, 2026-11-16). A piece not with the hero (dropped, thrown,
stolen: see Remembered pieces) is skipped with a line and costs nothing,
a piece not known by hand is refused ("put it on once first"), and a slot
that was empty when the kit was saved is left alone.

## 1c. What armour does beyond AC (winning-build plan 3.3, 2026-11-13)

Brandon: "Ensure that kit armor defenses are IMPORTANT beyond AC; materials
can change weight and resistances, block certain monster attacks and status
effects... a REAL choice to kit and armor, not just what has the best AC",
and "BALANCE armor and Dex (light vs heavy)... so that there are many ways
to play". This reversed the 3.3.2 rule that the material gives "the weight
and the wear, never protection" (decision 3). Every gift has a price.
Code: `gear.py`, What armour does beyond AC.

**The template sets the forms** (`forms`, `forms_words`, `forms_note` in
`data/templates/armor/*.json`; body armour only, and the tower shield):

| Build | Slash | Pierce | Blunt | |
|---|---|---|---|---|
| Plate, full plate, breastplate | x0.75 | x0.85 | | turns an edge; a hammer still rings it |
| Mail (chain shirt, ring mail, chainmail) | x0.75 | **x1.15** | | rings part under a point |
| Scale, banded, splint | x0.8 | x0.9 | | |
| Padded | x0.9 | | **x0.75** | quilting soaks a blow |
| Leather, studded leather, hide | x0.9 | | x0.85 | |
| Tower shield | | x0.9 | | a wall to hide behind |

**The material sets the elements** (`protection`, `protection_words` in
`data/materials/armor/*.json`, with `protection_note` and
`protection_price`), on the BODY armour only (a whole kit of leather would
otherwise pay the fire eight times; a shield is held, not worn). They
replaced the material files' `resistances` / `weaknesses` lists, which
nothing read for damage. The shape:

- metal conducts (lightning x1.25) and iron rusts; bronze, hematite and
  mithril never rust, and no named or legendary piece does unless its lore
  says so (status_effects.md, "No legend rusts"); cloth and leather catch
  fire (x1.25) and scorch;
- dragonscale fire x0.5 (cold x1.15), dragonhide fire x0.7, drakeskin 0.85;
  silk catches an arrowhead (pierce x0.9, spider silk 0.85);
- adamantine slash and pierce x0.85, heavy; titanforged blunt x0.8, heavier;
  tungsten blunt x0.85; glassteel turns the elements x0.9 but a hammer
  shatters it (blunt x1.2);
- cobalt steel is the frost iron (cold x0.75, fire x1.15), sunsteel the
  volcanic (fire x0.75, cold x1.15), soulsteel the silver mail (drain and
  necrotic x0.75), hematite holds the life in (drain x0.8);
- ring iron is cold iron: it **wards** off fey glamour;
- mithril is `quiet` (no clank) and `casting_free` (no spell tax);
  orichalcum and godweave cast freely too.

There are no iron, steel, silver, cold iron, frost iron or volcanic ARMOUR
material files (those are weapon materials, and every armour material has
its own art), so the plan's rows sit on the armour materials whose lore
fits (the notes say which).

**Wards** (`wards` on the material, `data/gear_rules.json` `wards`): a
rider the body armour's material stops outright, told in the log. Cold iron
(`fey_glamour`): a fair-folk attack's confusion, charm, sleep or
hallucination. Dragonscale and dragonhide (`flame`): burning, from anything.
Checked in `Monster._apply_attack_effect` after the minor-slot guards.

**A named piece keeps its own** `damage_resistances` (its JSON wins: no
template form or material element is added). Its weight class is its
template's, and whether it is `metal` is written in its JSON by its lore
(the Lorica of Caesar yes, the Hide of the Nemean Lion no).

**Where it bites**: `Player.take_damage` multiplies a typed blow by
`Player.get_armor_resistance` = `gear.worn_factor` (the product of every
worn piece's `gear.piece_profile`), beside the hero's own resistances and
after the shield, the stance and Achilles' hide. It is the one place: a
lining (a trader's, on a cloak or shirt) joins `piece_profile`.

**Light vs heavy** (by the BODY armour's weight class; no body armour is
light; `data/gear_rules.json` `armour_weight`, and `defence` for the speed):

| | Light | Medium | Heavy |
|---|---|---|---|
| Dodge (Dexterity's and worn gear's) | full | half | none |
| Dexterity's quickness (`defence.class_speed_share`) | full | half | none |
| Speed it costs (`defence.armour_drag`) | none | 6% | 12% |
| Full speed from (`defence.fit_strength`) | any Strength | Strength 13 | Strength 16 |
| Footsteps (`senses.step_radius`) | +0 | +1 | +2, metal +1 more |
| A spell's mana in METAL | x1 | x1.5 | x2 |

Mithril, orichalcum and godweave cast freely; mithril and godweave make no
clank. Each footstep tile makes a deep sleeper a quarter readier to stir
(`sleepers.factor`). `Player.spell_mp_cost` (rings, then armour) is what
`_invoke_spell` charges and the spell menu shows.

**The defence model** (Brandon's approved design, 2026-11-16; `src/defence.py`,
`data/gear_rules.json` `defence`; tuned with `tools/balance/difficulty_sim.py`
and `monte_carlo.py`, set `defence`, against the plate kid, the Dexterity kid
and the Secret Builds the kids play):

- **AC** comes from armour, the shield and magic only (`Player.get_ac`).
  Dexterity gives none. Until 2026-11-16 it gave up to 6 points in light
  armour, 3 in medium and 0 in heavy (`dex_ac_cap`), and a Dexterity hero
  in studded leather (3 + 6) out-armoured full plate (8) deep down; a
  clumsy hero's minus went with it.
- **Dodge** (`Player.dodge_chance`): `dodge_per_dex` a point of Dexterity
  over 10, at most `dodge_cap` (1.25% and 40%), then the
  body armour's share (all, half, none) and the load's (`load.<tier>.dodge`).
  Only a blow from beside the hero can be slipped (`Monster._slipped`).
- **Speed** (`Player.get_speed`): 10 is ordinary, the scale of a monster's
  `speed`. Dexterity adds `speed_per_dex` a point over 10, at most
  `speed_cap` (1% and 20%), and the body armour leaves
  all of that quickness, half or none (`speed_share`, as the dodge: a
  nimble hero in plate is no quicker for his Dexterity); medium and heavy
  body armour cost `armour_drag`, and Strength pays it back,
  `str_payback` a point over 10 (`defence.fit_strength`: a hero strong
  enough for his plate is at 10, whatever his Dexterity);
  the load costs `load.<tier>.speed`. Speed boots multiply it and haste
  doubles it. Every monster's damage was sized for a hero at speed 10: only
  armour too heavy for the hero's Strength and a load he chose to carry
  take him under it, and Dexterity and light armour may take him over.
- **How speed acts** (`defence.world_turns`, `Game._advance_turn`): each
  action moves the world's clock on by 10/speed of a turn and the world
  takes a turn for each whole turn passed: at 11 the monsters miss one
  action in eleven, at 9 they take two turns one action in nine. The
  Slowed status still costs the hero his own turn (`_do_move`).
- **Shown plainly**: the sidebar (AC in the DERIVED grid, then one line
  `Dodge 12%   Speed 11.2`, `Sidebar._nimble`) and the
  character sheet (AC, Dodge, Speed, always), and each body armour's card
  ("Heavy metal: no dodge or quickness, slower below Strength 16,
  ...").

**Weight that bites** (`data/gear_rules.json` `load`, `Player.load_tier`,
`defence.load_tier`; Brandon, 2026-11-16: "Light load at half, minor dodge
penalty, Heavy at 70%, larger dodge penalty and speed penalty, and Burdened
at 90% (larger penalties)"): everything worn or packed counts, except
cooking ingredients, which weigh nothing (Brandon, 2026-11-16: food,
rations and cooked dishes keep their weight). The limit is Strength's
(`20 + 8 x STR`) plus 3 lb a point of Constitution over 10
(`con_carry`).

| Load | Over | Dodge left | Speed lost | Footsteps |
|---|---|---|---|---|
| Light | half the limit | three quarters | none | +1 |
| Heavy | 70% | half | 10% | +2 |
| Burdened | 90% | none | 25% | +3 |
| Overloaded | the limit itself | none | half | +3 |

Past the limit nothing more can be picked up; a hero who is there anyway
(lost Strength, an old save, the Boulder) is Overloaded. The speed replaces
the old rule that every second Burdened step cost the dungeon an extra turn
(and every Overloaded step one); Marius' Mule keeps his stride under Light,
Heavy and Burdened (`Player.keeps_stride`). The quiz clocks and the AC are
untouched. A Heavy load or worse is the "heavy pack" a sleeper hears and
thin ice will not hold (`Player.is_heavy`). The sidebar, the @ sheet and the
log say which (`ui.carry_state`, `Game._note_burden`). (Until 2026-11-16:
Heavy over half, half the dodge; Burdened over three quarters, no dodge,
half Dexterity's AC, every second step a turn. Brandon, 2026-11-14: "heavy
at 50%, burdened at 75%, overloaded at 100%".)

**The card** says it in one honest line (`gear.protection_line`: "Turns an
edge: slash x0.75; parts under a point: pierce x1.15; conducts lightning
x1.25; cold iron: fey glamour slides off") and the weight class in another
(`gear.weight_line`: "Heavy metal: no dodge or quickness, slower below
Strength 16, footsteps +3, spells cost x2 MP; rusts."), on the Kit,
the @ sheet and the lore page.

**Measured** (`tools/balance/armour_incoming.py`): against the game's own
attack mix, the par body armour takes 1% off typed damage on floor 1, 4%
on floors 10-20, 3-5% on 30-80, 9% on 100. The monsters' to-hit was baked
to the AC of armour and shield alone (section 2), which is what AC is now.

**The Monte Carlo of the defence model** (`tools/balance/monte_carlo.py`
set `defence`, 100 runs a cell, kid model, accuracy 0.95, 2026-11-16): the
plate kid (mastery, STR and CON) wins 93% (96% of those alive after floor
60 win), the Dexterity kid in light armour 79% (89%), committed 1%, casual
0%; the Secret Builds Fianna 87%, Fluffs 87%, Corwin 93%, Cain 97%, Hermes
78%, Odysseus 87%. Deep down every mastery kid has Strength 30-48, so the
armour's drag only bites on floors 10-40. **No common light or medium body
armour drops past floor 40** (body finds by class, light / medium / heavy:
floor 20 26 / 53 / 21%, floor 30 4 / 30 / 66%, floor 40 0 / 6 / 94%, floor
60 on all heavy): a deep Dexterity hero wears the hide or studded leather of
floor 20 (AC 5-7 with its wear) and lives on his dodge and speed, so a
Dexterity build's deep AC waits on light armour that keeps spawning deep.

## 2. AC: body armour and shield only

`Player.get_ac()` = 10 - (body base + plus) - (shield base + plus) -
BUC of those two - effects (invisible, shielded, stance, parry, procs).
Dexterity gives no AC since the defence model of 2026-11-16 (section 1c).
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

**Linings** (winning build 3.5, 2026-11-13; `smithing.py`). An armourer
(Brannoc, Brunhild) lines a worn cloak or shirt against one element: fire,
cold, lightning or poison. That element's damage from any source is x0.75
while the piece is worn (`gear.piece_profile` multiplies it in, so the
damage and the Kit's resistance column read one number; two lined pieces
against one element stack). It is
the piece's own `lining` field, never `damage_resistances`, which the
old-save migration clears on common pieces. One lining to a piece; the Kit
card and the shop card say "Lined with salamander's wool, the stone cloth
that will not burn: fire does 25% less harm to you while you wear it."
whether the piece is identified or not (the hero watched it done). A stall
where fire breathes below may rack a cloak already lined (priced with the
lining: `economy.stock_price`).

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

## 6b. Press or Guard, the parry, and the named counters (slice 5)

`Player.get_ac` adds, beside the armour's own rules: the stance (Guard 2
points better, Press 2 worse: `stance.stance_ac`) and a two-hander's parry
held with no shield (`stance.parry_ac`; template, class and tier in
`data/arsenal.json parry`). Combat.md has the damage side.

**Named counters** (`src/counters.py`, `data/arsenal.json counters`). An
item's `counters` (or its shield template's) names techniques it blocks
outright:

| Technique | Piece | What it does | Its price |
|---|---|---|---|
| `gaze` | the **mirror shield** (`data/templates/shields/mirror_shield.json`; the Aegis of Athena too) | any gaze attack does nothing: no damage, no rider (`Monster._resolve_blow`, the gaze_paralyze and floating-eye paths) | AC 1, metal only: the AC a kite or tower shield would give |
| `voice` | **beeswax earplugs** (accessory, slot `none`), put in or taken out with the Kit's Apply, one turn | a voice attack's rider never takes hold | while in, he hears nothing: no war-band heard on arriving, no pet's warning growl (`counters.deafened`) |
| `fey_glamour` | the **cold-iron charm** (accessory, slot `none`), carried | the Fair Folk's confusion, charm, sleep and visions slide off (the cold-iron body armour's ward rule, `gear_rules.json wards`) | none but carrying it |

The rider check is in `Monster._apply_attack_effect`, right after the rider's
own chance roll. A shield template's `spawn_bell` may carry a fourth number,
its height beside the others (`gear.template_weight`): the mirror shield is
0.35, rarer than a kite shield at its peak. A metal shield is found from
about floor 10, so no mirror shield can be had before that. The tells'
counter lines name these pieces (data/tells.json); `counters.names_for(m,
key)` gives the techniques that answer one creature's tell.

## 7. Where gear comes from

A find of common gear is a weapon, an armour piece or a shield
**45 / 45 / 10** (`gear_rules.json` `loot_split`, `gear.pick_gear_class`,
`items.pick_random_gear_for_floor`): floor rooms, monster drops and chests'
gear all roll it, and an armour find is any of the eight slots evenly.
Traders stock from the same rolls.

## 8. Old saves

What a common piece does to a blow is read live from its template and
material (`gear.piece_profile`), so an old save's armour turns, conducts
and wards exactly as a new one does; the recompose clears its own
`damage_resistances` (a pre-3.3.2 save carried the old flat material
numbers there) and writes its `template_basis`. A named piece takes its
`metal` (and `quiet`, `casting_free`, `wards`) from today's data
(`gear_saves.refresh_named`). The load tier is worked out afresh on load.

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
Back, Loadouts, saves), `test_armour_choice.py` (forms, elements, wards,
light vs heavy, noise, casting, the load, cards, old saves, the data gates),
`test_carry_weight.py`, `test_defence_model.py` (the defence model: AC, dodge,
speed, the armour's drag and Strength's payback, the load tiers, the
scheduler, the simulator's guards).
