# Quest Flows (as the code works after the 2026-10-04 quest pass)

Each row is what the player does, step by step, and what the game does back.
"Checked by" says how I know: **test** means an automated test generates the
real floor or runs the real code; **read** means I or an auditor traced the
code but nothing executes it automatically. Nothing has been played.

## Main story

| Quest | Flow | Checked by | Still off from the design |
|---|---|---|---|
| The Stone | Descend 100 floors. Kill Abaddon on 100; the Stone drops where he falls. Pick it up. Climb back to floor 1 and leave by the up stairs. | test (drop), read (exit) | |
| Death's chase | Leaving floor 100 with the Stone spawns Death. He follows floor to floor, arriving a few tiles away: half speed on floors 99 to 76, then three quarters, equal, and faster than you from floor 25 up. He cannot be killed normally and time stop does not stop him. If you keep moving he does not get a blow in; his extra speed only closes distance. Stop beside him and the scythe lands. A successful prayer holds him for a few turns (more for a longer chain or at an altar). | test (bonus step, time stop rule), read (rest) | Never played. |
| Pit gate | The down stairs on floor 99 refuse until all seven seals are broken, and say how many remain. | read | |

## Gate bosses and their quest layers

| Quest | Flow | Checked by | Still off from the design |
|---|---|---|---|
| Ariadne's Thread (Asterion, floor 20) | 1. Floor 12: find the Bronze Bull Idol. 2. Floor 17: stand on the fountain (a bull's head is carved on the rim) and drop the Bull. Ariadne speaks and a wall becomes a door. 3. Take the Thread from the chamber. 4. Floor 20: arriving with the Thread lays the route to Asterion's hall on your map. While you carry it he cannot walk through walls, is slowed, and stops hit-and-run. | test (sealed chamber, lore, route), read (rest) | |
| Asterion and the Labyrinth | Floor 20 is a real maze, different every run, with loops and dead ends holding gold, gear and a healing potion. Asterion (600 HP) hunts you through the walls, charges for extra damage down a straight passage, strikes once or twice, then vanishes and waits. Below 30% HP he stops hiding and fights to the death. The stair down is beyond his hall and barred by a bronze grate while he lives. | test (maze, stair barred, his data), read (his AI) | The fight itself has never been played.
| Aegis of Athena (Medusa, floor 40) | 1. Floor 29: find the Eye of the Graeae. 2. Floor 37: drop it on an altar (the right one shows three old women passing something small). Athena speaks and a door opens. On any other floor the altar says it is the wrong place and you keep the Eye. 3. Take the Aegis and wear it as your shield. 4. Floor 40: when Medusa gazes she meets her own eyes, loses that turn and the next. About half her actions are gone. | test (sealed chamber, reflection at range), read (rest) | |
| Medusa and her temple | Her gaze now reaches eight tiles across open floor, every fourth turn: a failed save freezes you for three turns while she closes. A pillar between you breaks it, and the sanctum has eight. Up close she bites (3d8+4) and poisons. 1,100 HP. The stair is past her sanctum and choked with statues while she lives. | test (range, pillars, layout), read (damage) | The fight has never been played. |
| Blindfold (Medusa) | One is always in the lower-left side chapel on floor 40 (others drop at random from floor 30). Wear it: you see nothing, so the gaze does nothing, at range or up close. | test | You fight blind, feeling only what is within three tiles. |
| Medusa's trophy | Harvest and cook her. Permanent immunity to petrifying gazes. | test | |
| Sigurd's Shovel and the pit (Fafnir, floor 60) | 1. Floor 48: find the Broken Blade of Gram. 2. Floor 53: lay it on Odin's altar (a spear over a row of helmets is cut into the rim). It is consumed; Odin speaks; a door opens. 3. Take the Shovel. Wield it and swing at an empty floor tile beside you to dig a pit (30 stamina, 3 turns). 4. Floor 60: step into a pit. You stay crouched until you move. Fafnir's breath passes over you and he does not waste it: he comes to you. A melee blow from the pit ignores his scales and lands a quarter harder. Arrows from the pit still hit scales. | test (chamber, pit persists, melee only, he closes), read (damage) | |
| Fafnir and his lair | 2,000 HP, and his scales turn four fifths of any blow that is not from a pit or from Gram. He breathes once as you come in, then advances while the breath recharges (three turns), and fights with claw and bite up close. One old pit is already dug in his lair, so a player without the Shovel still has the answer. The hoard holds gold and gear. The stair is past the lair behind a curtain of his fire while he lives. | test (AI, lair, fallback pit, stair), read (damage) | The fight has never been played. Without a pit or Gram he is close to unbeatable, by design. |
| Reforged Gram (secret) | Same blade, same altar, but THROW the blade so its path passes over the altar, with the altar between you and where you aim. Standing on the altar or aiming at it does not count. Lightning; Gram lies whole on the altar; the Shovel door opens too. Gram ignores Fafnir's scales from anywhere and still gets its bonus against him. | test (throwable, never cursed, path rule), read (reforge) | The only hint comes from Fafnir's Blood, after he is dead. Gram asks tier-5 maths. |
| Fafnir's Blood | He drops it. Drinking starts an animal quiz chain of up to five, getting harder: the speech of birds. None right: a burned mouth (a fifth of your max HP). 1: full heal. 2: the birds' words come clear (the hint at the throw). 3: permanent fire resistance. 4: the birds warn you from now on (you sense monsters nearby, permanently). 5: +1 WIS. Each step adds to the ones before. | test (every step), read (the quiz start) |
| Gleipnir (Fenrir, floor 80) | 1. Collect six ingredients on floors 62, 65, 68, 71, 74, 77; each floor gives a one-line sign on arrival (cat's footstep, woman's beard behind a secret door, mountain root in a lava ring, fish's breath in a water ring, bird's spittle on an altar, bear's sinew among traps). 2. Floor 78: stand on the anvil with six cups and drop any one; the others go on from your pack. Fewer than six and it tells you how many cups are filled. 3. Take Gleipnir. 4. Floor 80: with Fenrir in sight and within six tiles, use "Bind Odinkiller". He is held for three turns and his rage is gone. Each cast costs one permanent stat point, in turn STR, DEX, CON. | test (ingredients reachable, forge floor, pack offering, range rule), read (the cast itself) | |
| Vidar's Sandal (secret) | 1. Pick up ten leather scraps on floors 5, 13, 21, 28, 35, 42, 50, 58, 66, 73. Each pickup tells you the count. 2. Floor 79: stand on the altar with the giant cobbler's last and drop one scrap; the rest follow from your pack. Fewer than ten: "It is not enough for a shoe." 3. Take the Sandal. 4. Floor 80: any hit on Fenrir with at least one right answer kills him. | test (scrap item, pack offering), read (the kill) | |
| Fenrir and his hall | 2,420 HP. His rage begins when he notices you, adds a die to each of his attacks every four turns, and stops at eight stacks; from three stacks he attacks three times a turn. When he attacks from an ice tile, half his lunges miss and he cannot flurry, so fighting him across the ice patches matters. The side rooms hold gold, gear and a healing potion. The stair is past his throne room, drifted shut while he lives. | test (rage, ice, stair, loot), read (damage) | The fight has never been played. |
| Seven seals | Floors 83, 85, 87, 89, 91, 93, 97 each hold one seal demon, with an omen on the stair. That floor's stair down is sealed with red wax until its keeper is dead, so none can be skipped. Each fights differently: Amon's wrath builds once he is hurt; Buer's breath carries disease; Mammon drains your stamina; Bael strikes three times a turn and rouses the floor; Samael heals from the wounds he deals; Beleth stuns; Abyzou silences and never stands still. Kill it: "Amon falls. The third of seven seals is broken." | test (stair sealed on all seven, each demon's trait in data), read (the fights) | Never played. |
| Last Judgment (floor 99) | Pray on the altar with the scales. Karma 8 to 10: Sword and Scales of Michael. 1 to 7: Scales. 0: nothing. -1 to -5: bigger locust swarms. -6 or lower: Abaddon has half again his HP. | test (tiers) | |
| Abaddon (floor 100) | Half of every blow is lost in the dark around him, on top of his resistances. Three ways through: pray at one of the six altars round the arena (each answers once, whatever your prayer cooldown) and holy fire strips his ward and resistances for two turns per right answer; or carry the Sword of Michael, which ignores both; or grind. He summons locusts once he notices you, twelve alive at most (sixteen if the Judgment went badly). The Scales call the Heavenly Host to meet the locusts one for one. Below 40% HP he attacks five times a turn. The Stone drops where he falls. | test (ward, altars usable, cap, Stone drop), read (rest) | Never played. Without an altar or the Sword he is very hard, by design. |
| Killing Death (secret) | 1. Floors 1 to 20: note the Abyssal Shimmer ("Revelation 20:14"). 2. Floors 21 to 49: find the Wrench. 3. Floors 50 to 79: find the Lake of Fire scroll. 4. Floors 80 to 99: find the Tablet. 5. Use the Wrench to fuse the Stone and the Tablet. 6. On the way up, drop the fused Tablet on the Shimmer. 7. Read the scroll while Death stands on the Shimmer. Death is destroyed, the Tablet returns to your hands, and you get the secret ending. | read | |

## Karma

| Quest | Flow | Checked by | Still off |
|---|---|---|---|
| Karma encounters | One NPC in each ten-floor block (ten per run), chosen from three or four candidates. Bump, read, pick one of three options. The kind option costs something and gives +1; the selfish one pays and gives -1 (the Bound Demon, -2). Karma runs -10 to +10 and feeds the Judgment. Reaching 8 writes a chronicle line. | test (data, block coverage), read (flow) | Kind options give no reward except karma and, for seven NPCs, a rumour. |
| Elara's pendant / Marcus's sword / Roderic's shield | The item appears one or two floors above the NPC. The NPC only appears if you picked it up. Return it (+1), return it for coin (0), or keep it (-1). | read | If you sold the item, only "keep it" or walking away remain. |
| Cursed Lodestone | Accept Sir Aldric's 20 lb stone (+1). It cannot be dropped. Lay it on any altar and it breaks. | read | |
| Sealed Dispatch | Accept the courier's dispatch (+1). If the Watch Post appears (floors 31 to 45, about four runs in ten), hand it over for gold, a potion and a blessing. | test (data) | No payoff if the Watch Post does not appear. Lore still says "the surface". |

## Roaming named foes

| Quest | Flow | Checked by | Still off |
|---|---|---|---|
| Mini-bosses (25) | Chosen when the run starts: each of five floor bands usually gets one, sometimes two. An omen line appears on arriving at its floor. Kill it for gold, an item, a reward scroll, sometimes a unique, and a chronicle entry. | test (placement, omens, drops) | The reward scroll prints a code "to show Dad" and nothing else. |
| Legends (Tiamat, Surtur, Asmodeus, Ymir's Last Spawn, Hrungnir's Ghost) | Each has a 50% chance to be in the run, once, on floors 82 to 95, never on a seal or boss floor. Omen on arrival. | test | Tiamat and Asmodeus never summon their minions. Three have no named drop. |
| Bonnacon (floor 6), Calydonian Boar (floor 27) | New. A squire or an old spearman on the floors above may tell you about it. The Boar drops Meleager's Spear. | test (data) | No art; both use a fallback sprite. |
| Bones ghost | If an earlier character died on this floor, half the time their ghost is here, as strong as the floor, guarding their old gear (cursed) and up to 500 gold. Announced once. | test (strength), read | |

## Secrets and oddities

| Quest | Flow | Checked by | Still off |
|---|---|---|---|
| Cow Level | One floor in 30 to 39 has a cow. Bump it and choose Poke ten times. A pasture of 40 to 50 Hell Bovines and the Cow King, who drops his Horns and a scroll. Leaving returns you to the floor you left. | test (depth not counted), read | After a save and reload the cow can be poked into the finished farm again. "Feed the cow" eats your first ingredient and does nothing. |
| Unicorn | Floors 1 to 19: find the Magic Carrot. Floors 21 to 39: when the unicorn appears, wait in her sight three turns, drop the carrot within two tiles, then bump her for a quiz. Longer chains give better boons; five right gives a healer pet. | read | With negative karma she takes the carrot and leaves, with no warning. |
| Duck of Doom | Floors 1 to 10: pick up the duck. It sticks to your head, cursed. Wear it 2,026 turns and it hatches into a pet and a quirk. | read | |
| Mystery altars (14) | A floor in a mystery's range has a 60% chance of one altar, with its key item in another room. Walk onto the altar; it describes itself and asks. Pay the key or cost, pass the quiz, take the reward. Each mystery once per run. | test (two new ones), read | A mystery you have already faced can still spawn later, silent. Ring of Command (Solomon's reward) does nothing. |
| Fountain / grave / throne | Press D. A quiz chain decides: bad at zero, better with each right answer, a permanent stat at five. Fountains and thrones may break after use; Ariadne's fountain never does. | test (Ariadne's), read | No limit on stat gains except the break chance. |
| Travelling merchant | About one floor in five. Stand beside him, press Y. H haggles once per item. | read | Prices are tiny for the depth. |

## New side quests

| Quest | Flow | Checked by |
|---|---|---|
| The Navigator's Boat | Floors 5 to 9. Walk onto the boat; two of three geography answers. +1 PER and 80 gold. | test |
| The Translator's Desk | Floors 73 to 77. Three of four grammar answers. +2 WIS, +1 INT. | test |
| The Old Couple's Table | Floors 2 to 9. Eat their supper (a little stamina), or put your own food on the table (more stamina, a blessing, +1 karma). | test |
| The Three Purses | Floors 11 to 19. 90 gold through the gap in secret (+1 karma), or 90 gold into his hand (a gift back). | test |
| Three Small Contests | Floors 28 to 39. Drink from the horn (+1 CON, costs stamina), lift the cat (+1 STR, more stamina), or wrestle the nurse (+1 WIS, a quarter of your HP). One only. | test |
| The Lion's Thorn | Floors 8 to 18: draw a thorn from a lion's paw (costs 10 HP) and keep the thorn. Floors 22 to 34: if you did, the lion is there. Hold out the thorn: +1 CON, gold, and a warning sense for a while. | test (always in order) |
| Saint Cuthbert's Gospel | Floors 41 to 47: accept the red book from a coffin bearer. Floors 48 to 53: a relic broker offers 350 to 450 gold for it (-1 karma). Floors 54 to 59: lay it on the reading desk for +2 WIS, a blessing, +1 karma. | test (always in order) |
| The Watch Post | Floors 31 to 45. See Sealed Dispatch above. | test |
