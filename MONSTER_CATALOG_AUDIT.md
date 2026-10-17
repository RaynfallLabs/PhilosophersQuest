# Monster catalog audit by depth (2026-10-17)

Brandon asked: "most of the ambush and hidden happens through mostly early content, and we
have a bit of a gap in late game monsters... see if we have a robust enough monster catalog
or if it gets one dimensional later."

**Short answer:** it does get one-dimensional. Past floor 80 the game is two patterns
(aggressive and ranged), about 15 to 27 real faces, and a handful of status effects. Ambush,
mimics, summoners, healers, hit-and-run and phase creatures fade out between floors 60 and 80
and are effectively gone by floor 81. Ranged and spellcasting threats are fine late. Status
effects are common but narrow late.

Part 1 is the measurement, part 2 the gaps, part 3 a ranked proposal (nothing in part 3 is
built; it waits for Brandon). Part 4 says what this change set did (invisible monsters and
the mimic fix).

## How this was measured

Monsters are not picked by `min_level`. `dungeon._build_spawn_pool(floor)` gives every
randomly spawning monster (`peak_weight > 0`) a weight of `peak_weight x bell`, where the
bell is a normal curve around `peak_floor` with width `spread`; a monster is left out below
its `min_level` or where its bell falls under 0.005, and never weighs less than 0.02.
`populate_floor`, dens, zoos, graveyards and lairs all draw from that pool. Bosses,
mini-bosses, seal demons and the chest mimics (`peak_weight 0`) are placed by
`level_manager` / `container_system` and are not counted.

For each floor I took every monster's share of that floor's pool and averaged the shares
over the ten floors of each band. So "18%" means "18% of the monsters that spawn in this
band". **Effective faces** is the exponential of the Shannon entropy of the band's shares:
how many equally common monsters would give the same variety. It is the honest version of
"distinct monsters", because 271 kinds can be eligible on floors 1-10 while many of them are
one-in-a-thousand stragglers.

Threat traits are read from the data: an attack whose name holds a ranged word
(`monster._RANGED_WORDS`) or an `ai_pattern` of `ranged` counts as ranged; the `caster` tag
or a magic/psionic attack counts as caster; status categories come from each attack's
`effect` (with `effect_chance > 0`), drain also from `drain` attacks and `drain_heals_self` /
`sp_drain`. All tables below are the catalog **before** this change set (`git HEAD`
`fce6832d`), so they show the problem as found.

## Part 1: the numbers

### Faces per band

| Band | Eligible kinds | Kinds at >=1% of spawns | Effective faces | Top 3 kinds share | Most common |
|---|---|---|---|---|---|
| 1-10 | 271 | 0 | 239 | 3% | Troglodyte 1%, Skeleton Archer 1%, grid bug 1% |
| 11-20 | 321 | 30 | 151 | 6% | Owlbear 2%, kobold dragonshield 2%, orc marauder 2% |
| 21-30 | 184 | 33 | 69 | 12% | dire wolf alpha 4%, Cave Troll 4%, cult zealot 4% |
| 31-40 | 101 | 45 | 69 | 10% | water elemental 3%, air elemental 3%, Vine Horror 3% |
| 41-50 | 105 | 39 | 72 | 9% | orc warlord 3%, veteran knight 3%, abyssal hound 3% |
| 51-60 | 112 | 36 | 56 | 13% | abyssal hound 5%, skeleton horde 5%, war troll 4% |
| 61-70 | 83 | 42 | 46 | 15% | zombie legion 5%, shadow assassin 5%, ancient vampire lord 4% |
| 71-80 | 72 | 36 | 44 | 18% | locust swarmlord 8%, Astral Horror 5%, titan 4% |
| 81-90 | 64 | 27 | 27 | 25% | void seraph 8%, apocalypse herald 8%, wormwood blight 8% |
| 91-100 | 40 | 15 | 17 | 32% | pit executioner 12%, iron horseman 10%, wormwood blight 10% |

Single floors make the slide plainer: effective faces are about 134 on floor 1, 210 on floor
10, 67 on floor 20, 52 on floor 50, 39 on floor 70, 24 on floor 85 and 14.5 on floor 100,
where the pit executioner alone is one spawn in seven.

### AI pattern mix (share of spawns, %; kinds at >=0.5% in brackets)

| Band | aggressive | ranged | ambush | mimic | hit_and_run | summoner | healer | sessile | cowardly | other |
|---|---|---|---|---|---|---|---|---|---|---|
| 1-10 | 59 (30) | 18 (9) | 10 (7) | 0 (0) | 7 (5) | 0 (0) | <1 (0) | 4 (4) | 1 (1) | 1 |
| 11-20 | 70 (43) | 12 (6) | 8 (5) | 0 (0) | <1 (0) | 3 (2) | 4 (3) | 2 (1) | <1 (0) | <1 |
| 21-30 | 68 (36) | 16 (10) | 9 (3) | 0 (0) | 0 (0) | 2 (3) | 4 (2) | 1 (1) | 0 (0) | 0 |
| 31-40 | 69 (42) | 13 (9) | 11 (7) | <1 (0) | 0 (0) | 2 (1) | 4 (2) | <1 (0) | 0 (0) | 0 |
| 41-50 | 62 (39) | 17 (13) | 9 (5) | 2 (1) | 2 (1) | 4 (2) | 4 (2) | 0 (0) | 0 (0) | <1 |
| 51-60 | 63 (29) | 16 (10) | 6 (2) | 3 (2) | 4 (2) | 5 (3) | 3 (1) | 0 (0) | 0 (0) | 0 |
| 61-70 | 65 (33) | 15 (11) | 6 (2) | 2 (1) | 5 (2) | 6 (2) | 1 (1) | 0 (0) | 0 (0) | 0 |
| 71-80 | 75 (30) | 17 (10) | 2 (1) | 1 (1) | 2 (1) | 3 (2) | <1 (0) | 0 (0) | 0 (0) | 0 |
| 81-90 | 73 (23) | 26 (7) | <1 (0) | <1 (0) | <1 (0) | <1 (0) | 0 (0) | 0 (0) | 0 (0) | 0 |
| 91-100 | 71 (15) | 29 (6) | 0 (0) | 0 (0) | <1 (0) | <1 (0) | 0 (0) | 0 (0) | 0 (0) | 0 |

(hit_and_run on floors 1-10 is mostly the imps, quasits and shades that blink; "other" is the
grid bug, the dancer and the dragon AI.)

### Threat types (share of spawns carrying it, %)

| Band | Melee | Ranged | Caster | Any status | Summon | Stealth (ambush/mimic) | Invisible | Phase/blink | Regen/heal | Swarm (pack) | Resists a weapon form | Resists 3+ elements |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1-10 | 94 | 24 | 23 | 76 | 1 | 10 | 0 | 7 | 1 | 11 | 9 | 13 |
| 11-20 | 99 | 31 | 27 | 83 | 3 | 8 | 0 | 2 | 6 | 1 | 8 | 23 |
| 21-30 | 97 | 43 | 23 | 77 | 2 | 9 | 0 | 3 | 11 | 4 | 19 | 23 |
| 31-40 | 97 | 34 | 21 | 83 | 2 | 12 | 0 | 2 | 7 | 4 | 30 | 18 |
| 41-50 | 100 | 36 | 20 | 75 | 4 | 11 | 0 | 5 | 7 | 9 | 29 | 19 |
| 51-60 | 100 | 41 | 21 | 67 | 5 | 9 | 0 | 8 | 8 | 14 | 19 | 25 |
| 61-70 | 100 | 39 | 24 | 74 | 6 | 8 | 0 | 11 | 5 | 14 | 17 | 29 |
| 71-80 | 100 | 34 | 32 | 77 | 3 | 3 | 0 | 9 | 4 | 9 | 13 | 40 |
| 81-90 | 100 | 51 | 37 | 84 | <1 | <1 | 0 | 2 | 4 | 6 | 18 | 38 |
| 91-100 | 100 | 52 | 30 | 78 | <1 | 0 | 0 | <1 | 3 | 5 | 25 | 33 |

### Status effects (share of spawns that can inflict it, %)

| Band | Poison/disease | Paralysis/stun/freeze/sleep | Drain | Fear | Confusion | Blind | Slow | Weaken | Bleed/burn | Silence | Teleportitis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1-10 | 21 | 13 | 3 | 2 | 16 | 7 | 20 | 2 | 4 | 0 | <1 |
| 11-20 | 25 | 20 | 10 | 3 | 13 | 5 | 23 | 9 | 6 | 0 | <1 |
| 21-30 | 16 | 14 | 14 | 3 | 10 | 5 | 15 | 13 | 12 | 0 | 0 |
| 31-40 | 10 | 27 | 13 | 7 | 15 | 4 | 15 | 3 | 20 | 2 | 0 |
| 41-50 | 5 | 34 | 11 | 6 | 12 | 2 | 13 | 2 | 28 | 3 | 0 |
| 51-60 | 5 | 29 | 12 | 4 | 8 | 5 | 9 | 5 | 25 | 1 | 0 |
| 61-70 | 8 | 25 | 13 | 6 | 5 | 11 | 7 | 7 | 24 | <1 | 0 |
| 71-80 | 12 | 21 | 25 | 12 | 10 | 8 | 8 | 14 | 11 | 0 | 0 |
| 81-90 | 12 | 26 | 36 | 14 | 9 | 1 | 5 | 22 | 13 | 0 | 0 |
| 91-100 | 11 | 32 | 29 | 11 | 5 | <1 | 2 | 18 | 21 | 0 | 0 |

Steal, splitting and petrification do not appear in any band: no monster mechanic exists for
the first two, and the `petrifying` status is never inflicted by an ordinary monster.

### Tags, deep

Floors 91-100 are 61% demon, 29% undead, 23% outsider (a monster can carry several tags).
That fits Abaddon's pit, but it also means nearly everything deep shares the same weakness
(holy) and the same answer.

## Part 2: the gaps, ranked

1. **Late bands collapse to two patterns.** From floor 81, aggressive plus ranged is 99-100%
   of spawns. Summoner, healer, hit-and-run, ambush, mimic, sessile and cowardly are each
   under 1%. A deep floor is "bigger bruisers plus archers and casters".
2. **Stealth thins out and then disappears.** Ambush plus mimic is 8-12% of spawns on floors
   1-70, 3% on 71-80, under 1% on 81-90 and zero on 91-100. Only the shadow assassin (peak
   60) and the Gilded Mimic (peak 58) carry it past floor 60. This is exactly Brandon's
   impression.
3. **Too few faces deep.** Effective faces fall from 69-72 in floors 21-50 to 46 (61-70), 27
   (81-90) and 17 (91-100). On floor 100 three kinds are a third of all spawns.
4. **Status variety narrows late.** Deep status is drain, paralysis/stun, weaken and bleed.
   Blindness (under 1%), slow (2%), confusion (5%) and silence (zero after floor 70) fade;
   poison never recovers from its mid-game dip. Teleportitis is one early monster. No steal.
5. **Target-priority fights vanish late.** Summoners peak on floors 61-70 (6%) and are gone by
   81; healers end at 60; regenerating or healing creatures are 3-4% deep. Nothing deep says
   "kill that one first".
6. **Swarms are thin deep.** Packs are 9-14% on floors 41-70 and 5-6% from 81, so area magic
   has little to do late.
7. **Phase and blink end at 80.** They live mostly on the Astral Horror and the vampire lords
   (51-80); 2% on 81-90, nearly none after.
8. **Floors 21-30 are a small dip in variety** (69 effective faces, but top three 12% and packs
   only 4%), between the very wide early catalog and the steady middle.

What is fine: ranged threats (24% early rising to about 50% deep), spellcasters (20-37%,
highest deep), early variety (huge), and resistances that call for a counter (13-40% of
spawns resist three or more elements; 9-30% resist a weapon form).

## Part 3: proposal (not built; for Brandon's review)

Ranked by how much of the gap each closes. Numbers follow LORE, NOT FLOOR: each new creature
gets real base data written for the floor its story puts it on, then
`tools/balance/respawn_by_hp.py --write` seats it. "Data only" means monsters.json plus art;
"needs code" names the small mechanic it needs.

| # | Proposal | Band | AI pattern | What makes it play differently | Cost |
|---|---|---|---|---|---|
| 1 | **Re-tune the five deep regulars by their own lore.** Wormwood Blight: the star that made a third of the waters bitter (Revelation 8:10-11): poison and blind. Void Seraph: silence (no spells) and teleportitis. Iron Horseman: `can_charge` and stun. Apocalypse Herald: fear. Pit Executioner keeps bleed. | 81-100 | unchanged | These five are about half of all spawns on floors 81-100, so their status lines decide how varied the deep game feels. Brings back blind, silence, poison and teleport where they are missing. | Data only |
| 2 | **Keres**, the Greek death-spirits who fought over the dying on battlefields, dragging them off by the ankles (Hesiod, *Shield of Heracles*). | 85-100 | aggressive, `pack` of 3-5 | The first real deep swarm: low health each, many bodies, drain plus bleed. Area spells and chain kills matter deep again. | Data only |
| 3 | **Hellmouth**: the jaws of Leviathan that swallow the damned in medieval Doom paintings and mystery plays. | 81-100 | mimic (disguised as the down staircase or a doorway) | The map lies to you deep down. Stepping beside the "stairs" springs it; a hold (`immobilized`) plus acid. Teaches suspicion of the most-wanted tile. | Needs code: `disguise` from an env tile (a few lines beside the new item disguise) |
| 4 | **Grendel's Mother**, who came up out of the mere to take vengeance, and against whom Beowulf's sword Hrunting failed (Beowulf). | 78-90 | ambush | A deep ambusher that drags (`pull_chance` already exists) and resists slash and pierce, so the player has to change weapon or spell. | Data only |
| 5 | **The Witch of Endor's line**: the medium who raised the shade of Samuel for King Saul (1 Samuel 28). | 80-95 | summoner (raises Darkhelm Shades or dread wraiths) | Returns "kill the caster first" to the deep game, and brings invisible minions with it. | Data only |
| 6 | **The Furies (Erinyes, greater)**: Alecto, Megaera and Tisiphone, who hounded Orestes for blood-guilt (Aeschylus, *Eumenides*). An `erinyes_lesser` already exists at floor 10. | 81-95 | hit_and_run, a pack of three | Harries and withdraws, fear and blind; three bodies that will not stand still. | Data only |
| 7 | **Blood of Tiamat**: Marduk split Tiamat in two to make sky and earth (Enuma Elish); her blood still crawls. | 85-100 | aggressive | Splits when struck by a weak blow; one big hit kills it outright. Rewards a long maths chain over many small hits, which is the skill the game trains. | Needs code: `splits_under` (spawn a half-HP copy when a blow is under a share of max HP). The same rule would give the floor-10 black pudding its classic split. |
| 8 | **Ganglot, Hel's handmaid** (Gylfaginning names Hel's servants Ganglati and Ganglot, "the slow-walkers"). | 80-95 | healer | Mends the dead around her and slows the hero; the deep game's first "heal the group" target. | Data only |
| 9 | **Stheno and Euryale**, Medusa's immortal sisters, who chased Perseus after he took her head. | 60-75 | dancer or aggressive with `gaze_paralyze` | A petrifying gaze outside the Medusa fight: blindfold and Aegis matter again, and `revive_once_on_death` fits "immortal". | Data only (they would be named pair-uniques: Brandon's call) |
| 10 | **Gashadokuro**: the Japanese giant skeleton built from the bones of the unburied famine dead, said to come silently and bite heads off. | 70-85 | ambush, 2x2 footprint | A big deep ambusher; the multi-tile code already exists. | Data only |
| 11 | **Thieves that steal**, plus **Autolycus' heir** (Odysseus's grandfather, the master thief taught by Hermes, who could make stolen things look like something else). Today the bandit thief, both leprechauns and the Ethereal Filcher steal nothing. | 5-10 (existing), 55-75 (new) | hit_and_run or cowardly after the theft | Takes gold or one unworn item and runs; the player chases to get it back. A whole kind of threat the game does not have. | Needs code: a `steal` attack effect |
| 12 | **Strix**, the Roman night-bird that drank the blood of sleepers (Ovid, *Fasti* 6). | 21-30 | hit_and_run, `pack` of 3 | Fills the floor 21-30 dip with a swarm that bites and pulls back, drain plus sleep. | Data only |
| 13 | **Two more invisible creatures by lore, if wanted later.** The air elemental (floor 35, its lore already says "nearly invisible") and the poltergeist (floor 1, "has no shape to show"). Not done now: the air elemental is one of the commonest faces on floors 31-40, and an invisible thrower on floors 1-3 comes before the player has any way to see it. | 1-3, 31-40 | unchanged | More invisible enemies without new art. | Data only |
| 14 | **A common way to see the unseen.** Today: cooked see-invisible meals, the beholder and cyclops prime cuts, three true-sight uniques, three telepathy accessories, the Detect Monsters spell and (new in this change) the wand of sunlight. Proposal: a potion of see invisible in the ordinary potion pool from about floor 30. | 30+ | n/a | Keeps the invisible creatures fair once there are more of them. | Data only (and a potion effect) |

If Brandon picks only three: 1 (biggest effect, data only), 2 and 3 (swarm and stealth back
in the deepest band).

## Part 4: what this change set already did

**Invisible monsters** (`invisible: true`, every rule in `src/unseen.py`). Two existing
creatures whose lore already said nobody sees them, and four new ones, weighted deep:

| Monster | Band (peak floor) | Pattern | Lore hook | Base numbers |
|---|---|---|---|---|
| Haunting Presence (existing) | 1-5 (1) | ambush | "no face and no voice", a cold spot | 6d6 HP, Frighten 1d2 fear |
| Dread Wraith (existing) | 20-28 (23) | aggressive | reaches through from just outside the world | 55d8+36 HP (283), drain 2d6+2, paralysing wail |
| Huldufolk Raider (new) | 38-48 (42) | aggressive, flanks | Icelandic hidden folk | 120d10+330 HP (990), knife 2d8+11 bleed, Led Astray 2d6+12 confuse |
| Darkhelm Shade (new) | 57-70 (62) | aggressive | the helm of Hades, worn by Athena at Troy and by Perseus | 280d10+860 HP (2,400), spear 3d8+20 bleed, Grave Chill 2d8+21 slow |
| Whirlwind Jinni (new) | 71-85 (76) | aggressive, blinks | jinn of smokeless fire who ride dust-devils (Qur'an 55:15, 7:27; Lane) | 385d10+2100 HP (4,218), fire 4d10+16 burn, 3d8+22 confuse |
| Nibelung Hoard-Warden (new) | 84-100 (90) | aggressive | Alberich's Tarnkappe (Nibelungenlied) | 480d12+3070 HP (6,190), 5d10+25 stun, pick 4d8+20 bleed |

`respawn_by_hp.py --write` re-seated none of them: each sits on the floor its HP was built for.
Invisible share of spawns after the change: about 1% on floors 1-20, 1-3% on 21-70, 5% on
71-90 and 6% on 91-100 (roughly one creature in twenty deep: "not a ton").

**Mimic fix.** The Lurking Horror and the Gilded Mimic (`ai_pattern: mimic`) now carry a
`disguise` (an iron chest; a spilled dragon hoard) and are drawn as it until they spring;
look describes the chest, the sidebar does not list them, and a mimic that has just burst
out of a chest is no longer drawn as a chest beside the hero.

Scripts used for these tables live in the session scratchpad; the patch itself is
`tools/content/add_invisible_monsters_2026_10.py` (idempotent).
