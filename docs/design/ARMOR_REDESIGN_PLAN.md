# Armour redesign: core AC, slot wards, slot-only enchantments (plan)

Brandon, 2026-11-07, after the equipment review
(`EQUIPMENT_BALANCE_REVIEW_2026_11_07.md`): "armor is so broken. We need to
fix this. How does AD&D do this? Maybe only the core armor and shield matter
for AC, and other items, like a helm, gloves, cloak give you protection from
certain attack types and carry enchantments that can ONLY be found on those
items... let's plan."

Status: **plan, awaiting rulings** (section 8). Nothing is built.

---

## 1. Why the current model cannot be tuned

Nine slots add AC (body, head, arms, hands, legs, feet, cloak, shirt, shield),
plus rings, blessings, enchantment and DEX. Each slot's AC is small, but nine
of them stack, and every new material tier raises all nine at once. A real
run wears AC -6 by floor 15 and -50 by floor 100 (loot census). Monster
accuracy climbs too (median THAC0 19 on floors 1-10, -15 on 91-100), but it
cannot keep up, so from about floor 15 every blow is decided by the 30% hit
floor (`monster.MIN_HIT_ORDINARY`) and no armour found after that changes
anything. The minor slots are also the cheapest AC in the game (one question
each), so they are where most of the overshoot comes from.

## 2. How AD&D does it

- **Armour type sets the base AC** (2e: leather 8, chain 5, plate 3, full plate
  1, from an unarmoured 10). **A shield improves it by one** (more with its
  magic). Magic armour and shields add their plus. DEX adds a little. That is
  nearly all of AC.
- **Other worn gear does not give AC.** Helms, gauntlets, boots, girdles and
  cloaks are where the *special* magic lives, and each kind has its own
  family: helms of telepathy or brilliance, gauntlets of ogre power or
  dexterity, boots of speed, elvenkind or levitation, cloaks of displacement,
  elvenkind or the bat. You find them only on that kind of item.
- **The few exceptions are named protection items** (ring or cloak of
  protection; bracers of defense, which only help a wearer with no armour).
  They do not pile freely on top of magic armour. 3e made this a rule:
  bonuses of the same type (armour, shield, deflection, natural armour) do
  not stack; only the best of each counts.
- **Touch attacks ignore armour** (3e "touch AC"): a ghoul's touch or a
  wraith's drain does not care how thick your plate is.
- **AC stays inside about 10 to -10**, and monster accuracy climbs with Hit
  Dice, so good armour keeps mattering at every level. Only a natural 20 is
  sure to hit.

## 3. The model for Philosopher's Quest

### 3.1 AC comes from the core only

```
AC = 10 - body armour - shield - (their enchantment and blessing)
        - DEX (cap 3) - one protection source (the best ring / cloak of
          protection, capped) - temporary effects (shielded, stand, parry...)
```

- Helm, arms, hands, legs, feet, cloak (unless it is a cloak of protection)
  and shirt give **no AC**.
- Body armour by weight class, before material: light 1-2, medium 3-4, heavy
  5-6, full plate 7. Material adds by tier (+0 at tier 1 up to about +3 at tier
  5). Shields: buckler and light 1, kite 2, tower 3 (the tower also turns aside
  more missiles), material +0 to +2.
- **The AC line** (what a prepared hero wears; tuned with
  `tools/balance/loot_census.py`):

  | Floor | 1 | 10 | 20 | 30 | 50 | 70 | 100 |
  |---|---|---|---|---|---|---|---|
  | Prepared AC | 8 | 5 | 2 | 0 | -4 | -8 | -12 |

  The best possible kit runs a few points better; an unarmoured hero is 10.
  This is close to `tools/balance/curve.py`'s -14 at floor 100.
- **Monster accuracy is rebaked to the line** (LORE NOT FLOOR: written into
  `monsters.json` by `tools/balance/scale_monsters.py`, never multiplied at
  runtime): a typical monster hits a prepared hero about 55% of the time, an
  under-armoured one about 75%, a best-kit one about 35%. With AC bounded, the
  30% hit floor can drop to the natural 20 (5%) for ordinary monsters
  (decision 4).
- Equip cost follows protection: body and shield questions by weight class
  (light 1, medium 2, heavy 3), and shields finally get theirs (buckler and
  light 1, kite 2, tower 3).

### 3.2 The minor slots: a ward each

Every minor slot **guards against particular kinds of attack**, using the
attack data that already exists (1,153 monster attacks; delivery classified
from their names, `ranged` flag and damage type):

| Slot | Guards against | Share of monster attacks | Riders it shrugs off |
|---|---|---|---|
| Head (helm) | voice and mind (wail, mind blast, charm, hex), gaze | 7% | confused, feared, stunned, sleeping, hallucinating |
| Cloak | breath and spray; fire, cold, acid, lightning washing over you | 5% (+ elemental damage) | burning, frozen |
| Hands (gloves, gauntlets) | touch (draining, death, rotting touch, pseudopods, engulf), grapple | 10% | paralyzed, weakened, drain |
| Arms (bracers) | ranged (bolts, rays, shards, hurled things) | 8% | blinded, stunned (from missiles) |
| Legs (greaves, leggings) | bites, stings, tail strikes | 15% | poisoned, bleeding |
| Feet (boots) | trample and charge; traps, ice, water, rubble underfoot | 2% + hazards | slowed, immobilized |
| Shirt | what gets under the armour | (any delivery) | poisoned, diseased, bleeding (weaker than legs) |

- **What a ward does** (decision 2): against a matching attack, (a) a chance
  to shrug off its rider effect, and (b) a share of its damage turned aside.
- **Strength** comes from what the piece is: template weight class (light,
  medium, heavy) and material tier, written in a small table
  (`data/armor_wards.json`), capped (about 60-75%). So plate gauntlets
  finally beat cloth gloves at something: they hold a draining touch better.
- **Touch ignores the core** (from 3e): a touch attack is rolled against AC
  without body armour and shield; the gloves' ward is the defence. This also
  makes the hero's own touch spells and the monsters' touch attacks two sides
  of one rule.
- Each monster attack gets a `delivery` field in `monsters.json` (written once
  by a tool from the classification above, checked by hand for the odd ones).

### 3.3 Enchantments found only on their slot

A minor-slot piece may carry one enchantment from **its own slot's family**,
found nowhere else (AD&D's helms of telepathy, gauntlets of ogre power, boots
of elvenkind), many tied to the game's own systems:

| Slot | Enchantments (examples) |
|---|---|
| Head | Telepathy (sense minds through walls); Clarity (+seconds on one subject's quiz clock); Night Sight; Iron Will (no fear) |
| Cloak | Protection (the one AC exception, +1 to +3); Displacement (the first blow of a fight misses); Elvenkind (sleepers stay asleep: `sleepers.py`); the Bat (float, in the dark) |
| Hands | Ogre Power (STR); Dexterity; the Thief (lockpicking: a gentler economics quiz); Spellfire (touch spells hit harder) |
| Arms | Defense (AC only with no body armour: the caster's path); Archery (bows); Parrying |
| Legs | Endurance (SP); Springing; Sure-Footing |
| Feet | Speed; Elvenkind (silent steps); Levitation; Striding (no slow); Water Walking |
| Shirt | Health (regeneration); Warmth (cold); Fortune |

- Data in `data/enchantments.json` (id, slot, tiers, what it hooks). Commons
  roll none or one, the chance and tier set by the material (by what the piece
  is, not the floor). The name shows it once known: "Iron Helm of Clarity".
- Hidden until identified (philosophy), like every other property.
- The equip cost of a minor piece is set by its enchantment (1 question plain,
  more for a strong one), so cost follows power here too.
- The 56 minor-slot uniques keep their stories and specials; their AC is
  rewritten as ward strength and (where it fits the lore) a slot enchantment.

### 3.4 Rings and amulets
Accessories (history quiz) keep their own powers. A ring of protection
becomes the other "protection source": only the best one counts (decision 3).

## 4. What changes in the code

- `player.get_ac`: core only, plus the capped protection source.
- `monster.py` attack resolution: the attack's delivery, the touch rule, the
  ward (rider save and damage share) after a hit lands; the hit floor.
- `items.py` composition: minor-slot templates lose base AC; wards from the
  table; enchantment roll and naming. Shields get thresholds.
- New data: `data/armor_wards.json`, `data/enchantments.json`, `delivery` on
  every monster attack; rebaked `thac0` in `monsters.json`.
- Blessing on a minor piece: +1 ward step instead of +1 AC
  (`altar.blessing_helps` stays true for them).
- The Kit and character sheet show a piece's ward and enchantment instead of
  an AC figure; help screen, hints, docs (system-change sweep rule).
- Saves: worn and carried minor pieces are recomputed on load (the existing
  armour recompose in `main.py` ~1464 is the template); shields' and thresholds'
  new numbers reach saved items the same way.

## 5. Build order (each phase ends playable)

1. **Rulings and the AC line** (this document).
2. **Core AC + shields**: `get_ac` core-only, body and shield numbers, shield
   thresholds, monster accuracy rebake, the hit floor. Minor slots keep a
   small temporary AC until phase 3 lands, so no build ships naked.
3. **Wards**: delivery on every attack, the ward table, the combat hook, the
   touch rule; minor-slot AC removed in the same commit.
4. **Slot enchantments**: data, roll, naming, identification, equip cost,
   each hook.
5. **Uniques pass**: the 56 minor-slot uniques (and any body or shield unique
   whose numbers no longer fit).
6. **Saves, text sweep, docs, census check, tests** (many tests pin today's
   numbers; see the review's section 4).

Play-test points: after phase 2 (does AC feel right on floors 1-20?), after
phase 3 (does a helm feel worth wearing against a wailing spirit?), after 4.

## 6. Size and where it lives

This is a 3.4 release, not a 3.3.2 bug fix: it changes combat at every depth
and touches saves. It belongs on its own branch (`release/3.4.0`, cut from
`release/3.3.2` once 3.3.2 ships) and probably several sessions, one phase
each.

## 7. Risks

- Hero builds and uniques balanced on today's AC (Spartan Stand, parry, the
  Hannibal cuirass procs) need a look once the line is lower.
- The 13 questions to suit up today will change shape (fewer AC questions,
  more for strong enchantments); the total should stay about the same.
- Tests that pin AC numbers will move; each change is checked against the
  census, not just made to pass.

## 8. Rulings needed

1. **Core AC only** (body, shield, enchantment, DEX, one protection source):
   yes?
2. **What a ward does**: shrug off the rider, turn aside a share of the
   damage, or both?
3. **Protection source**: only the best of ring and cloak of protection
   counts (3e style), or none at all outside the core?
4. **The hit floor**: down to the natural 20 for ordinary monsters once AC
   is bounded (named foes keep a higher one)?
5. **The AC line in 3.1**: right shape, or a different floor-100 figure?
6. **Release**: 3.4.0 on its own branch after 3.3.2 ships?
