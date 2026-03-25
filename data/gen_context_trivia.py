#!/usr/bin/env python3
"""
Generate context fields for all 601 trivia questions.
Each context is a 2-3 sentence educational explanation shown when the player gets it wrong.
"""
import json
import os

CONTEXTS = {
    # ========== MINECRAFT ==========
    "In Minecraft, what block do you need 4 of to craft a crafting table?":
        "Wood planks are the most fundamental crafting ingredient in Minecraft. You arrange four planks in a 2x2 grid to create the crafting table, which then unlocks the full 3x3 crafting grid. Each log you chop yields four planks, so one tree gets you started immediately.",

    "What year did Minecraft officially release for the public?":
        "Minecraft's full release (version 1.0) launched on November 18, 2011 at MineCon in Las Vegas. Notch had been developing it publicly since 2009 as an alpha/beta, but 2011 was the official 'out of beta' launch. It went on to become the best-selling video game of all time.",

    "In Minecraft, what happens when you sleep in a bed?":
        "Sleeping in a bed skips the night cycle and fast-forwards to daytime, despawning most hostile mobs in the process. It also resets your spawn point to the bed's location, so if you die you'll respawn there instead of the world spawn. In multiplayer, all players must be in bed for the skip to work.",

    "In Minecraft, what does a creeper do when it gets close to you?":
        "The Creeper is Minecraft's most iconic mob, silently sneaking up before detonating in an explosion that destroys nearby blocks. It was actually created by accident when Notch tried to make a pig model and mixed up the height and length values. The resulting creature was so unsettling that it became the game's unofficial mascot.",

    "In Minecraft, what is the name of the ghost enemy that only spawns in the Nether?":
        "Ghasts are enormous floating mobs that cry eerily and shoot explosive fireballs at players from long range. Their fireballs can actually be deflected back at them with a well-timed hit, making combat feel like a deadly game of tennis. Their tears are used as a brewing ingredient for regeneration potions.",

    "In Minecraft, what do you use to tame a wolf?":
        "Wolves in Minecraft are tamed by feeding them bones, which are commonly dropped by skeletons. Each bone has roughly a one-third chance of taming the wolf, and once tamed, it gains a collar and will follow and fight for you. You can even dye the collar different colors.",

    "In Minecraft, what tool is used to break dirt the fastest?":
        "Each tool type in Minecraft is optimized for specific block categories: shovels for dirt and sand, pickaxes for stone and ore, axes for wood. Using the wrong tool still works, but takes much longer. The shovel's speed advantage over bare hands becomes more dramatic with higher-tier materials.",

    "In Minecraft, what is the maximum enchantment level for most enchantments?":
        "Most Minecraft enchantments cap at level 3 (like Sharpness III from an enchanting table), though some go higher with an anvil and enchanted books. A few enchantments like Sharpness and Protection actually max at level 5 when using books. The enchanting table itself requires 15 bookshelves to reach its maximum level 30 offering.",

    "What is the final boss of Minecraft?":
        "The Ender Dragon resides in The End dimension, reached by finding and activating an End Portal with Eyes of Ender. Defeating it triggers Minecraft's iconic poem-style credits sequence, written by Julian Gough. The dragon can actually be resummoned using End Crystals for additional fights.",

    "What material is needed to make a Nether Portal in Minecraft?":
        "Obsidian is formed when water flows over a lava source block, and it takes nearly 10 seconds to mine even with a diamond pickaxe. You need at least 10 blocks arranged in a 4x5 frame (corners optional) to create a working Nether Portal. The portal can also be created without a diamond pickaxe by carefully placing lava and water to form obsidian in place.",

    "What is the name of the hostile mob that explodes when near a player?":
        "The Creeper is so iconic it appears on official Minecraft merchandise and the game's logo. Its distinctive 'ssss' sound before exploding has become one of gaming's most recognizable audio cues. Charged Creepers, created when lightning strikes nearby, produce an even bigger explosion.",

    "How many bookshelves are needed to unlock level 30 enchantments?":
        "Exactly 15 bookshelves placed one block away from the enchanting table with air in between unlocks the maximum level 30 enchantments. Each bookshelf requires 3 books and 6 planks to craft, so reaching max enchanting takes 45 books total. The bookshelves must be on the same level as or one block above the table.",

    "What mob drops Ender Pearls in Minecraft?":
        "Endermen are tall, dark, teleporting mobs that drop Ender Pearls when killed. These pearls are essential for locating and activating End Portals (when combined with Blaze Powder to make Eyes of Ender). Thrown Ender Pearls also teleport the player to where they land, at the cost of some fall damage.",

    "What three skulls are needed to summon the Wither?":
        "You need three Wither Skeleton skulls placed on top of four blocks of soul sand in a T-shape to summon the Wither. Wither Skeletons only spawn in Nether Fortresses, and the skull drop rate is just 2.5% without the Looting enchantment. The Wither is actually harder than the Ender Dragon for most players.",

    "What is the rare biome where Mooshrooms naturally spawn?":
        "Mushroom Fields (also called Mushroom Islands) are extremely rare island biomes where no hostile mobs naturally spawn, making them uniquely safe. Mooshrooms are special cows covered in mushrooms that can be 'milked' with a bowl to get mushroom stew. Shearing a Mooshroom turns it into a regular cow and drops mushrooms.",

    "What update added bees to Minecraft Java Edition?":
        "The Buzzy Bees update (1.15) released in December 2019, adding bees, beehives, bee nests, honey blocks, and honeycomb. Bees pollinate crops and flowers, actually speeding up crop growth when they return to their hive. The honey block introduced unique properties like reducing fall damage and slowing movement.",

    "What does a Nether Star drop from in Minecraft?":
        "The Wither is a player-summoned boss that drops a single Nether Star upon defeat. This star is used to craft a Beacon, one of the most powerful utility blocks in the game that grants area buffs like Speed and Strength. The Wither is the only renewable source of Nether Stars.",

    "What enchantment allows a pickaxe to yield more ore drops?":
        "Fortune increases the number of items dropped when mining ores, with Fortune III roughly doubling average yields from diamond ore. It does not work on ores that drop themselves (like iron or gold ore before 1.17). Fortune and Silk Touch are mutually exclusive enchantments.",

    "What new mob in Minecraft 1.19 is drawn to sound in the Deep Dark?":
        "The Warden is a terrifyingly powerful blind mob that hunts entirely by sound and vibration, introduced in the Wild Update (1.19). It has 500 HP (more than both bosses) and deals enough damage to kill a fully armored player in just two hits. Mojang designed it as a mob you're meant to sneak past, not fight.",

    "What item is used to ignite a Nether Portal?":
        "Flint and Steel is crafted from one iron ingot and one flint (dropped from gravel), and it ignites the purple portal effect inside an obsidian frame. Fire charges also work as an alternative lighter. In a pinch, players have used lava and flammable blocks to ignite portals without any flint and steel at all.",

    "What is the rarest ore found exclusively in the Nether?":
        "Ancient Debris spawns deep in the Nether (mostly around Y-level 15) and is blast-resistant, making bed explosions a popular mining strategy. Smelting it produces Netherite Scrap, and four scraps plus four gold ingots make one Netherite Ingot. Netherite gear is the strongest in the game and uniquely floats in lava.",

    "What is the currency used to trade with villagers in Minecraft?":
        "Emeralds are Minecraft's trading currency, and each villager profession offers different trades that unlock as you level them up. Emerald ore is actually rarer than diamond ore in the overworld, found only in mountain biomes. Most players get emeralds through trading rather than mining.",

    "What hostile mob in Minecraft drops a music disc when killed by a skeleton?":
        "When a Skeleton's arrow is the killing blow on a Creeper, the Creeper drops a random music disc. This mechanic encourages creative combat setups where players lure Creepers into skeleton firing lines. There are multiple discs with different tracks, composed by C418 and later Lena Raine.",

    "What biome generates the tall spires called 'Chorus Plants' in Minecraft?":
        "Chorus Plants grow exclusively on the outer End islands, accessible after defeating the Ender Dragon and finding an End Gateway. Their fruit can be eaten to randomly teleport the player short distances, and smelted into purpur blocks for building. The End's outer islands also contain End Cities with Elytra wings.",

    "What effect does the Silk Touch enchantment have?":
        "Silk Touch lets you mine blocks and collect them in their original form rather than their usual drop. This means you can pick up glass without breaking it, collect spawners, or grab ice blocks. It's mutually exclusive with Fortune, creating an interesting strategic choice for your pickaxe.",

    # ========== POKEMON ==========
    "What type is Pikachu in Pokemon?":
        "Pikachu is a pure Electric-type Pokemon, number 25 in the original Pokedex. It became the franchise mascot after the anime chose it as Ash's starter instead of the traditional Bulbasaur, Charmander, or Squirtle. Designer Atsuko Nishida originally based its design on a squirrel, not a mouse.",

    "In Pokemon, how many starter choices do you get at the beginning of most games?":
        "The classic trio of starter Pokemon follows a rock-paper-scissors balance: Grass beats Water, Water beats Fire, and Fire beats Grass. This three-way relationship has been the foundation of every mainline Pokemon game since 1996. Your rival typically picks whichever starter has a type advantage over yours.",

    "In Pokemon, which starter evolves into Charizard?":
        "Charmander evolves into Charmeleon at level 16, then into the fan-favorite Charizard at level 36. Despite looking like a dragon, Charizard is Fire/Flying type, not Fire/Dragon (a fact that frustrated fans for decades). It finally got Dragon typing through its Mega Evolution X form in Generation VI.",

    "In Pokemon, what type is Squirtle?":
        "Squirtle is a pure Water-type and one of the original three Kanto starters. Its name is a portmanteau of 'squirt' and 'turtle,' and it evolves into Wartortle and then Blastoise, who sports two water cannons on its shell. In the anime, Ash's Squirtle led a gang called the Squirtle Squad.",

    "What color is Pikachu?":
        "Pikachu's signature yellow color with brown stripes and red cheek pouches has made it one of the most recognizable characters in the world. The red cheek patches are actually electric sacs where it stores electricity. Female Pikachu have a heart-shaped notch at the end of their tail, a detail added in Generation IV.",

    "In Pokemon, what does Bulbasaur evolve into?":
        "Bulbasaur evolves into Ivysaur at level 16, with the bulb on its back growing into a larger bud. It then evolves into Venusaur at level 32, when the bud fully blooms into a massive flower. Bulbasaur is unique as both the first Pokemon in the Pokedex and the first dual-type starter (Grass/Poison).",

    "In the Pokemon anime, who are Ash's two main traveling companions in the original series?":
        "Misty, the Cerulean City Gym Leader specializing in Water types, and Brock, the Pewter City Gym Leader who specializes in Rock types, joined Ash in the very first season. Brock became famous for his comical crushes on every woman he met, while Misty's hot temper balanced Ash's recklessness. They remained the most beloved companion trio in the franchise's history.",

    "What type is Charizard?":
        "Despite looking like a quintessential dragon, Charizard is Fire/Flying, not Fire/Dragon. This typing means it takes 4x damage from Rock-type moves, making Stealth Rock particularly devastating. Game Freak finally gave it Dragon typing through Mega Charizard X in Pokemon X and Y.",

    "Which Pokemon is number 001 in the original Pokedex?":
        "Bulbasaur holds the honor of being number 001, making it literally the first Pokemon in the National Pokedex. It's a Grass/Poison dual-type, the only starter to begin with two types. Its name comes from 'bulb' (the plant on its back) and 'dinosaur' (saur).",

    "What does Pikachu evolve into?":
        "Pikachu evolves into Raichu when exposed to a Thunder Stone. In the anime, Ash's Pikachu famously refused to evolve after losing to Lt. Surge's Raichu, choosing to win the rematch as a Pikachu instead. Generation VII introduced Alolan Raichu, an Electric/Psychic variant that surfs on its tail.",

    "Who is Ash Ketchum's rival in the original Pokemon anime?":
        "Gary Oak, grandson of Professor Oak, was Ash's arrogant rival who always seemed one step ahead. His English name is a play on the original Japanese name Shigeru, which was actually named after Nintendo legend Shigeru Miyamoto. Gary famously traveled with cheerleaders and a convertible, a stark contrast to Ash's humble journey.",

    "What legendary Pokemon is found at the end of Cerulean Cave in Pokemon Red and Blue?":
        "Mewtwo, the genetically engineered clone of the mythical Mew, waits at the deepest level of Cerulean Cave as the game's ultimate catch. With a base stat total of 590 (680 with Mega Evolution), it was the strongest Pokemon in Generation I. The cave only becomes accessible after defeating the Elite Four.",

    "What type combination does Gengar have?":
        "Gengar is Ghost/Poison, which in Generation I actually made it vulnerable to Psychic types due to a programming bug (Ghost was supposed to be super effective against Psychic, but wasn't). It's the final evolution of Gastly through Haunter, requiring a trade to evolve. Gengar was one of the original 'trade evolution' Pokemon.",

    "Which generation introduced the Steel type?":
        "Generation II (Gold/Silver, 1999) introduced both Steel and Dark types to balance the game, particularly to counter the overpowered Psychic type from Gen I. Steel resists an incredible 10 types, making it the most defensively useful type in the game. Magnemite and Magneton were retroactively given the Steel type.",

    "What is the legendary Pokemon on the box art of Pokemon Gold?":
        "Ho-Oh, the Rainbow Pokemon, graces the cover of Pokemon Gold and represents rebirth and resurrection. According to the lore, Ho-Oh revived three unnamed Pokemon that perished in the Burned Tower fire, creating the Legendary Beasts Raikou, Entei, and Suicune. It actually appeared in the very first episode of the anime, years before Gold/Silver released.",

    "What is Eevee's Water-type evolution called?":
        "Vaporeon evolves from Eevee when exposed to a Water Stone, and its cellular composition is similar to water molecules, allowing it to melt into water and become invisible. It has the highest HP of all Eeveelutions. Eevee's multiple evolution paths (now eight total) make it one of the most versatile Pokemon in the franchise.",

    "Which Pokemon game introduced the Physical/Special split per individual move?":
        "Before Diamond and Pearl (2006), whether a move was Physical or Special was determined entirely by its type (e.g., all Fire moves were Special). Gen IV changed this so each individual move has its own category, meaning Fire Punch became Physical while Flamethrower stayed Special. This single change revolutionized competitive Pokemon strategy.",

    "Which gym leader in Kanto specializes in Rock-type Pokemon?":
        "Brock is the first Gym Leader you face in Kanto, and his Rock-type team (Geodude and Onix) creates a classic early-game challenge for Charmander starters. He later becomes a recurring character in the anime as Ash's traveling companion. His perpetually squinting eyes became one of the show's most iconic visual gags.",

    "What is the name of the evil organization in Pokemon Ruby and Sapphire?":
        "Ruby and Sapphire uniquely featured two rival evil teams: Team Magma wants to expand the land using Groudon, while Team Aqua wants to expand the sea using Kyogre. Which team serves as the primary antagonist depends on which version you play. Their conflicting goals and mutual hostility made for a more nuanced villain story than Team Rocket.",

    "Which Pokemon can learn the move Sketch, permanently copying any move?":
        "Smeargle can use Sketch to permanently copy the last move used by the opposing Pokemon, making it the most versatile move-learner in the game. This means Smeargle can theoretically learn almost any move in existence, though its terrible stats limit its competitive use. In Double Battles, partners can set up moves for Smeargle to Sketch.",

    "What is the Pokedex number of Mew?":
        "Mew is number 151, placed right after Mewtwo (150) at the very end of the original Kanto Pokedex. It was secretly programmed into the game by Shigeki Morimoto without management approval, making it one of gaming's most famous hidden secrets. Mew can learn every TM and HM move in the game.",

    "What type is super effective against Dragon type?":
        "Ice is super effective against Dragon, along with Dragon-type moves themselves and (from Gen VI onward) Fairy. In Generation I, Dragon's only weakness was other Dragon moves, and the only Dragon move (Dragon Rage) dealt fixed damage, making Dragons effectively unresistable. Ice Beam became the go-to Dragon counter for years.",

    "What is Ash's rival's name in the Sinnoh region?":
        "Paul is a cold, calculating trainer who judges Pokemon purely by strength and releases any he deems weak. His rivalry with Ash represents the philosophical clash between training with love versus training for power. Their final battle at the Sinnoh League is considered one of the best fights in the anime.",

    "Which move has 100% accuracy and always causes the target to flinch if used first?":
        "Fake Out is a Normal-type priority move that always causes flinching but can only be used on the first turn after switching in. This makes it invaluable in competitive doubles formats (VGC) for disrupting opponents' strategies on turn one. It deals minimal damage, but the guaranteed flinch is worth the move slot.",

    "What is the base stat total of Arceus?":
        "Arceus has a base stat total of 720, with 120 in every stat, making it one of the most powerful Pokemon ever created. Known as the 'Original One,' lore states it hatched from an egg in nothingness and created the entire Pokemon universe. Its Multitype ability lets it change type based on the Plate it holds.",

    "What Pokemon has the naturally highest base Speed stat (non-Mega, non-Legendary)?":
        "Ninjask has a base Speed stat of 160, the highest of any non-Mega, non-Legendary Pokemon. It evolves from Nincada at level 20, and uniquely, its evolution also produces Shedinja (a Ghost/Bug with only 1 HP) if you have an empty party slot and a spare Poke Ball. Its Speed Boost ability makes it even faster each turn.",

    "What attack does Ash's Pikachu most famously use in the anime?":
        "Thunderbolt is Pikachu's signature move in the anime, used countless times across hundreds of episodes. It's an 90-power Electric move with 100% accuracy and a 10% chance to paralyze. In the early anime, Pikachu's Thunderbolt was absurdly powerful, defeating Ground-types and even legendary Pokemon through sheer plot armor.",

    "Which city is home to the Kanto Pokemon League?":
        "Indigo Plateau sits atop a mountain range between Kanto and Johto, serving as the Pokemon League headquarters for both regions. Trainers must collect all eight gym badges and navigate Victory Road to reach it. In Generation II, players discover they can return to Kanto after beating the Johto League, effectively getting two regions in one game.",

    "What evil organization appears in the original Pokemon Red and Blue games?":
        "Team Rocket, led by the mysterious Giovanni (who is also the Viridian City Gym Leader), is the original Pokemon villain organization. They exploit Pokemon for profit through schemes like the Silph Co. takeover and the Game Corner. The anime made them iconic through the bumbling trio of Jessie, James, and Meowth.",

    "How many Eevee evolutions existed in Generation I?":
        "Generation I introduced three Eeveelutions: Vaporeon (Water Stone), Jolteon (Thunder Stone), and Flareon (Fire Stone). The total has since grown to eight, with Espeon and Umbreon in Gen II, Leafeon and Glaceon in Gen IV, and Sylveon in Gen VI. Fans have been hoping for a Ghost or Dragon Eeveelution for years.",

    "What is the name of Ash's Pikachu's evolved form that Ash refused?":
        "In the classic episode 'Electric Shock Showdown,' Ash's Pikachu was offered a Thunder Stone to evolve into Raichu after losing to Lt. Surge's Raichu. Pikachu slapped the stone away, choosing to beat Raichu on its own terms using speed over raw power. This moment cemented Pikachu's character as proud and determined.",

    "Which Pokemon is known as the Legendary Bird of Ice?":
        "Articuno is the Ice/Flying Legendary Bird, found in the Seafoam Islands in the original games. Its name combines 'arctic' with 'uno' (Spanish for 'one'), as it's the first of the trio. The other two are Zapdos (dos/two, Electric) and Moltres (tres/three, Fire).",

    "What is the name of the main character in Undertale?":
        "The player character in Undertale is named Frisk, though this isn't revealed until the True Pacifist ending. Throughout the game, the character you name at the start is actually a different entity entirely, Chara, the fallen human. This twist is one of Undertale's most celebrated narrative surprises.",

    "What is the name of Ash Ketchum's first Pokemon partner?":
        "Ash received Pikachu from Professor Oak because he overslept and missed out on the traditional three starters. Initially, Pikachu refused to obey Ash and even shocked him repeatedly. Their bond formed after Ash shielded Pikachu from a flock of angry Spearow, a moment that defined their lifelong partnership.",

    # ========== MY HERO ACADEMIA ==========
    "In My Hero Academia, what is the name of the main character?":
        "Izuku Midoriya, nicknamed 'Deku,' was born Quirkless in a world where 80% of people have superpowers. His encyclopedic knowledge of heroes and unbreakable determination caught the attention of All Might, who chose him as the successor to One For All. His hero notebook habit actually proves useful throughout the series.",

    "In My Hero Academia, what does the word Quirk refer to?":
        "Quirks are superhuman abilities that began manifesting in humans after the first luminescent baby was born in Qingqing, China. About 80% of the world's population has a Quirk, and they're incredibly diverse, ranging from simple mutations to reality-warping powers. Those born without Quirks, like young Izuku, face significant social stigma.",

    "In MHA, what is the name of Bakugo's explosive quirk?":
        "Bakugo's Quirk 'Explosion' lets him secrete nitroglycerin-like sweat from his palms and detonate it at will. The more he sweats, the more powerful his explosions become, making summer his peak season. His Quirk is actually a combination of his parents' abilities: his mother's glycerin secretion and his father's acid sweat.",

    "In My Hero Academia, what school do most heroes-in-training attend?":
        "U.A. High School (Yuuei) is Japan's most prestigious hero academy with an acceptance rate of less than 1 in 300. The school's motto is 'Plus Ultra,' borrowed from the historical motto of Spain meaning 'Further Beyond.' Its teaching staff includes pro heroes like Eraserhead (Aizawa) and Present Mic.",

    "In My Hero Academia, what is the name of All Might's ultimate ability?":
        "United States of Smash was All Might's final and most powerful attack, used to defeat All For One in their climactic battle at Kamino Ward. All Might names his attacks after U.S. states and cities (Detroit Smash, Texas Smash, etc.) because he trained in America. This ultimate move burned through the last embers of One For All in his body.",

    "In My Hero Academia, what is the name of All Might's quirk?":
        "One For All is a unique stockpiling Quirk that can be voluntarily passed from one user to the next, accumulating power with each generation. It was created when All For One forcibly gave a power-stockpiling Quirk to his seemingly Quirkless brother, who secretly had a Quirk for transferring Quirks. Izuku is the ninth wielder.",

    "What is Izuku Midoriya's hero name in My Hero Academia?":
        "Izuku chose the name 'Deku,' reclaiming the insult Bakugo used to call him (meaning 'useless' in Japanese). Ochaco Uraraka pointed out that 'Deku' sounds like the Japanese word for 'you can do it' (dekiru), inspiring Izuku to embrace it. This name transformation mirrors his journey from powerless dreamer to genuine hero.",

    "What is the name of the most powerful Quirk passed down through generations in MHA?":
        "One For All has been passed down through nine users, each adding their strength to the Quirk's stockpile. It was born from All For One's cruel experiment on his brother, who secretly had a transfer Quirk that merged with the forced stockpiling ability. By Izuku's time, it has accumulated over a century of power.",

    "What is All Might's real name in My Hero Academia?":
        "Toshinori Yagi is All Might's true identity, kept secret to protect his loved ones. After a devastating injury from All For One that destroyed his respiratory system and stomach, he can only maintain his muscular hero form for limited periods. His gaunt, skeletal true form is one of the series' most shocking reveals.",

    "What is Katsuki Bakugo's official hero name?":
        "Bakugo's official hero name, 'Great Explosion Murder God Dynamight,' is characteristically over-the-top and aggressive. He initially refused to choose a hero name, and the final name references both his explosive Quirk and All Might (his hidden motivation). The 'Dynamight' spelling is a deliberate tribute to his idol.",

    "What villain has a Quirk that can decay anything he touches in MHA?":
        "Tomura Shigaraki's Decay Quirk disintegrates anything he touches with all five fingers, and it evolved to spread to anything connected to the initial target. He was born as Tenko Shimura, the grandson of All Might's mentor Nana Shimura. All For One deliberately manipulated and raised him to become the ultimate symbol of destruction.",

    "What school do the Class 1-A heroes attend in MHA?":
        "UA High School's hero course is split into Class 1-A and 1-B, each with 20 students. The school's facilities include entire fake cities for combat training, a USJ rescue simulation center, and dorms (Heights Alliance) for student safety. Getting in requires passing both a written exam and a practical test against robots.",

    "What is Ochaco Uraraka's Quirk in MHA?":
        "Zero Gravity lets Uraraka make anything she touches with all five finger pads become weightless, up to about three tons. Overusing it causes severe nausea, which she's trained to suppress. She became a hero to earn money for her parents' struggling construction company, one of the series' most grounded motivations.",

    "What is the real name of the villain Dabi in MHA?":
        "Dabi is Toya Todoroki, Endeavor's eldest son who was presumed dead after his fire Quirk proved too powerful for his ice-adapted body. He burned himself as a child trying to earn his father's approval, and his patchwork skin is held together with surgical staples. His reveal was one of the manga's most anticipated twists.",

    "What is Shoto Todoroki's left side Quirk?":
        "Shoto's left side produces fire inherited from his father Endeavor, while his right side produces ice from his mother. For much of the series, he refused to use his fire side as rebellion against Endeavor's abusive 'Quirk marriage' breeding program. Izuku's words during the Sports Festival finally convinced him to embrace his full power.",

    "Who is the No. 2 Hero who becomes No. 1 after All Might's retirement?":
        "Endeavor (Enji Todoroki) spent his entire career obsessed with surpassing All Might, even arranging a Quirk marriage to breed a child who could. When he finally became No. 1 by default, he realized the hollow nature of his pursuit and began trying to atone. His character arc is one of the most complex in the series.",

    "What is the name of the villain group led by Shigaraki in MHA?":
        "The League of Villains was assembled by All For One and placed under Shigaraki's leadership as part of a long-term plan to destroy hero society. Its members include outcasts rejected by society, giving the group a tragic undercurrent. They later merged with the Meta Liberation Army to form the Paranormal Liberation Front.",

    "What is Tenya Iida's hero name?":
        "Tenya chose the name Ingenium to honor his older brother Tensei, the original Ingenium, who was paralyzed by the Hero Killer Stain. His Engine Quirk gives him car-exhaust-like pipes in his legs for incredible speed. His strict, rule-following personality makes him Class 1-A's class representative.",

    "What percentage of One For All power does Izuku first use in Full Cowl mode?":
        "Izuku developed Full Cowl to spread One For All's power evenly throughout his body at 5%, rather than concentrating 100% in one limb and shattering his bones. He got the idea from watching Gran Torino move like a bouncing ball. This was a breakthrough that made One For All practically usable for the first time.",

    "What Quirk does Himiko Toga possess?":
        "Toga's Transform Quirk lets her perfectly replicate anyone's appearance after ingesting their blood. She later awakened her Quirk further, gaining the ability to also copy the Quirk of the person she transforms into. Her obsession with blood and 'becoming' the people she loves makes her one of the series' most unsettling villains.",

    "Which MHA character has a navel laser Quirk?":
        "Yuga Aoyama fires a sparkling laser from his navel, but overuse causes stomach pain. His flashy personality and constant fourth-wall-breaking smiles at the camera made fans suspicious for years. That suspicion paid off when he was revealed to be the U.A. traitor, given his Quirk by All For One as a child.",

    "What is Tsuyu Asui's hero name?":
        "Froppy's frog-based Quirk gives Tsuyu a long prehensile tongue, wall-climbing ability, camouflage, and enhanced swimming. She's one of Class 1-A's most level-headed members, often providing the voice of reason. Her straightforward personality led to the running gag of her asking everyone to call her 'Tsu.'",

    "Who was the eighth wielder of One For All before Izuku?":
        "All Might (Toshinori Yagi) was the eighth and most famous wielder of One For All, maintaining peace as the 'Symbol of Peace' for decades. He received the Quirk from Nana Shimura, the seventh wielder, who was killed by All For One. All Might held One For All longer than any previous user.",

    "What is the first named move Izuku develops in MHA that concentrates One For All into one finger?":
        "Delaware Smash channels One For All through a finger flick, creating a powerful shockwave of compressed air. Izuku developed it because concentrating 100% power in a single finger broke fewer bones than using his whole arm. He named it after a U.S. state, following All Might's naming convention.",

    "What is the name of the USJ villain who was created to kill All Might?":
        "The original Nomu was a bio-engineered weapon with Shock Absorption and Super Regeneration Quirks, specifically designed to counter All Might's devastating punches. All For One created it by combining multiple Quirks into a brain-dead human vessel. All Might needed over 300 punches at 100% power to defeat it.",

    "Which MHA character is known as the hero 'Suneater'?":
        "Tamaki Amajiki is one of U.A.'s Big Three (the top three students) whose Manifest Quirk lets him transform body parts into anything he's eaten. Eating octopus gives him tentacle fingers; eating chicken gives him wings. Despite his incredible power, he has crippling social anxiety and can barely face a crowd.",

    "What is Endeavor's real name in MHA?":
        "Enji Todoroki is the Flame Hero: Endeavor, whose Hellflame Quirk produces and controls incredibly powerful fire. He holds the record for most villain cases solved in hero history, even surpassing All Might in that statistic. His journey from abusive father to repentant hero is one of the series' most divisive character arcs.",

    # ========== HAJIME NO IPPO ==========
    "What is the name of the main character in Hajime no Ippo?":
        "Ippo Makunouchi starts as a timid, bullied high school student who discovers boxing after being saved by middleweight champion Takamura. The manga by George Morikawa has been running since 1989, making it one of the longest-running sports manga ever. Ippo's journey from weakling to Japanese Featherweight Champion spans over 1,400 chapters.",

    "What is Ippo's signature move in Hajime no Ippo?":
        "The Dempsey Roll is a devastating weaving combination named after real-world heavyweight champion Jack Dempsey, who used a similar technique in the 1920s. Ippo shifts his weight side to side in a figure-eight pattern, building momentum for powerful hooks from both sides. Multiple rivals have developed counters specifically for this move.",

    "Which gym does Ippo train at in Hajime no Ippo?":
        "Kamogawa Boxing Gym is a small, old-school gym run by the legendary Coach Kamogawa, a former boxer who fought in the post-war era. Despite its humble appearance, it produces world-class fighters including Takamura, Ippo, and others. The gym's training methods are intensely physical and often unorthodox.",

    "What is the name of Ippo's coach in Hajime no Ippo?":
        "Genji Kamogawa is a former boxer who fought brutal bare-knuckle bouts in post-WWII Japan against American soldiers. His experience shapes his old-school, fundamentals-first training philosophy. His rivalry with Dankichi Hama (Sendo's trainer) dates back to their own boxing days.",

    "What weight class does Ippo Makunouchi compete in?":
        "Ippo fights at Featherweight (122-126 lbs / 55.3-57.2 kg), which requires careful weight management for someone with his naturally stocky build. His compact, muscular frame gives him exceptional punching power for the weight class, often compared to a much heavier hitter. Weight cutting is a recurring struggle in the series.",

    "Who is Ippo's main rival throughout Hajime no Ippo?":
        "Ichiro Miyata is an outboxer whose technical counter-punching style is the perfect foil to Ippo's aggressive infighting. Their fathers were former sparring partners, creating a generational rivalry. Despite both wanting an official match, fate keeps preventing their dream bout.",

    "What boxing style does Ippo use?":
        "The Peek-a-Boo style, made famous by trainer Cus D'Amato and his pupil Mike Tyson, involves keeping both gloves high near the face and bobbing/weaving aggressively to close distance. Ippo's short stature and incredible durability make it ideal for him to slip inside longer-armed opponents' reach. His style prioritizes devastating close-range power shots.",

    "What is the name of the punch Ippo throws in an upward arc like a leaping gazelle?":
        "The Gazelle Punch uses a powerful leg spring to launch an uppercut while surging forward, combining the momentum of a body shift with upward force. It's named after a gazelle's explosive leaping ability. Ippo uses it as a devastating lead-in that often sets up his Dempsey Roll.",

    "Who is the loud hot-headed boxer from Naniwa who repeatedly clashes with Ippo?":
        "Takeshi Sendo, the 'Naniwa Tiger,' is a wild slugger from Osaka whose ferocious fighting spirit matches Ippo's own. Their two championship fights are among the most brutal and celebrated bouts in the manga. Despite being fierce rivals in the ring, they develop a deep mutual respect.",

    "What weight class is Mamoru Takamura primarily a champion in?":
        "Takamura holds the Super Middleweight world title and aims to conquer all weight classes from Junior Middleweight to Heavyweight. He's portrayed as a once-in-a-generation natural talent whose only real limitations are his own personality and weight cutting. His bear-fighting scene is one of the manga's most legendary moments.",

    "What is Kimura's signature move in Hajime no Ippo?":
        "The Dragonfish Blow is a body blow that curves upward like a fish leaping from water, targeting the liver from an unexpected angle. Kimura developed it specifically for his title challenge, showing the dedication of even the gym's 'B-tier' fighters. Despite his losses, Kimura's technical creativity makes him a fan favorite.",

    "What is the technique Miyata uses involving slipping an incoming punch and countering simultaneously?":
        "The Cross Counter involves timing your punch to land at the exact moment your opponent's punch is fully extended, using their forward momentum against them. Miyata perfected this technique to compensate for his lack of natural punching power. The timing required is so precise that mistiming it by a fraction means taking the opponent's punch clean.",

    "Who is the Russian boxer who fights Miyata in Hajime no Ippo?":
        "Volg Zangief is a Russian boxer with exceptional fundamentals who becomes one of the most sympathetic characters in the series. He fights to support his sick mother back home and eventually wins a world title despite constant setbacks. His clean boxing style and gentle personality make him a fan favorite.",

    "Which boxer in Hajime no Ippo is nicknamed the 'Wild Tiger'?":
        "Sendo earned the 'Naniwa Tiger' nickname through his ferocious, wild fighting style that overwhelms opponents with relentless aggression. His signature Smash punch is thrown with reckless, full-body commitment. Despite appearing simple-minded, Sendo has surprising ring intelligence when cornered.",

    "What is the JBC Featherweight champion Ippo defeats to win his first title?":
        "Eiji Date was the reigning Japanese champion and former world title challenger whose experience and technique seemed insurmountable. His Heartbreak Shot (a corkscrew punch to the chin) was specifically designed to finish fights instantly. Ippo's victory over Date marked his transformation from promising prospect to true champion.",

    "What health condition threatens Ippo's career in his retirement arc?":
        "Punch Drunk Syndrome (chronic traumatic encephalopathy/CTE) symptoms began manifesting in Ippo through deteriorating reflexes, stumbling, and an inability to take punches he once absorbed easily. The manga treats this with unusual seriousness for a sports series, reflecting real-world concerns about brain damage in boxing. Ippo's temporary retirement and potential comeback remain the manga's central tension.",

    "What does young Ippo deliver for his mother's business at the start of the series?":
        "Ippo works on his mother's fishing boat, hauling in catches before and after school. This manual labor gave him exceptional grip strength and core power that translated directly into boxing prowess. His humble, hardworking background contrasts sharply with the flashier personalities in the boxing world.",

    # ========== STUDIO GHIBLI ==========
    "What are the names of the two sisters in My Neighbor Totoro?":
        "Satsuki (named after the Japanese month of May) is the responsible older sister, while four-year-old Mei (also a name for May) is the adventurous younger one. Both names meaning 'May' reflects the film's setting and the sisters' deep connection. The film was originally conceived as a single character before Miyazaki split the role into two sisters.",

    "What is the name of the magical cat-shaped bus in My Neighbor Totoro?":
        "The Catbus is a grinning, twelve-legged cat that serves as a fantastical form of public transportation through the countryside. Its destination sign actually changes throughout the film, reading different locations. It was inspired by the Japanese concept of bakeneko, supernatural cats that grow larger and more powerful with age.",

    "What are the small black fuzzy creatures in My Neighbor Totoro called?":
        "Soot Sprites (susuwatari) are tiny, round, black creatures that inhabit abandoned houses and scatter when disturbed. They also appear in Spirited Away, working in Kamaji's boiler room carrying coal. Miyazaki designed them as a simple, charming way to show the magical elements present in everyday rural life.",

    "Where is the sisters' mother during the events of My Neighbor Totoro?":
        "The girls' mother is recovering from an unspecified long-term illness at a nearby hospital, which provides the emotional core of the film. Miyazaki based this on his own childhood experience, as his mother spent years hospitalized with spinal tuberculosis. The family's move to the countryside was specifically to be closer to her hospital.",

    "What does Totoro give the girls that magically grows into a giant tree overnight?":
        "Totoro gives Satsuki and Mei a small package of acorn seeds, which they plant in their garden. That night, Totoro and the smaller spirits perform a magical growing ceremony that makes the seeds sprout into an enormous camphor tree. When the girls wake, the tree has returned to normal size, but the seeds have genuinely sprouted.",

    "What does Totoro use as an umbrella when waiting at the bus stop?":
        "Totoro uses a large leaf as a makeshift umbrella while waiting at the bus stop in the rain, one of the film's most iconic images. Satsuki had lent him her father's umbrella, and Totoro became fascinated by the sound of raindrops hitting it. This scene inspired the famous movie poster and Studio Ghibli's logo.",

    "What is the human girl's name in Spirited Away?":
        "Chihiro Ogino is a sulky ten-year-old who stumbles into the spirit world when her family takes a wrong turn during a move to a new town. Her character arc from whiny, fearful child to brave, compassionate heroine is the heart of the film. Spirited Away won the Academy Award for Best Animated Feature in 2003.",

    "What name does Chihiro work under at the bathhouse in Spirited Away?":
        "Yubaba steals most of the kanji from Chihiro's name, leaving only 'Sen.' Names hold power in the spirit world, and forgetting your real name traps you there forever. Haku warns Chihiro to never forget her true name, which becomes a crucial plot point.",

    "Who is the mysterious boy that helps Chihiro in Spirited Away?":
        "Haku appears as a young boy who works as Yubaba's apprentice, but he's actually a river spirit who once saved young Chihiro from drowning. His true name is Kohaku River (Nigihayami Kohakunushi), and he forgot it after his river was filled in for apartment construction. Remembering his name breaks Yubaba's control over him.",

    "What is Haku's true identity in Spirited Away?":
        "Haku is the spirit of the Kohaku River, which was paved over for urban development. As a child, Chihiro fell into his river and he carried her to shallow water, saving her life. Miyazaki used this as a metaphor for Japan's disappearing natural waterways and the spiritual cost of modernization.",

    "Who operates the boiler room in the bathhouse in Spirited Away?":
        "Kamaji is a spider-like old man with extendable arms who operates the bathhouse's boiler, assisted by tiny soot sprites carrying coal. Despite his gruff exterior, he helps Chihiro by pretending she's his granddaughter. He represents the overworked but kindhearted laborers that keep society running behind the scenes.",

    "What happens to Chihiro's parents when they eat the spirit world food?":
        "Chihiro's parents are transformed into pigs after greedily eating food meant for the spirits without permission. This transformation serves as both a literal plot device and Miyazaki's commentary on human greed and consumerism. Chihiro must work in the bathhouse to earn their freedom and eventually identify them among a herd of pigs.",

    "What is the name of the silent masked spirit in Spirited Away who follows Chihiro?":
        "No-Face (Kaonashi) is a lonely, shadowy spirit who absorbs the personality and desires of those around it. In the bathhouse, it becomes gluttonous and materialistic, but with Chihiro's kindness, it finds peace at Zeniba's cottage. Miyazaki described No-Face as representing a person without identity who takes on the traits of their environment.",

    "Who is Yubaba's twin sister in Spirited Away?":
        "Zeniba lives in a peaceful cottage far from the bathhouse and is temperamentally the opposite of her controlling twin sister. While Yubaba represents greed and control, Zeniba embodies warmth and simple living. She tells Chihiro that Yubaba's contract can be broken if Chihiro remembers certain things.",

    "What does Yubaba steal from Chihiro, trapping her in the spirit world?":
        "Yubaba takes Chihiro's name through a magical contract, renaming her 'Sen.' In the spirit world, forgetting your true name means you can never leave. This is a metaphor Miyazaki used for how overwork and conformity can make people forget who they truly are.",

    "What is Yubaba's oversized giant baby named in Spirited Away?":
        "Boh is Yubaba's enormous, pampered baby who throws destructive tantrums when upset. Zeniba transforms him into a mouse as part of a spell, and the experience of seeing the outside world changes him for the better. His character satirizes overprotective parenting and the spoiled children it produces.",

    "What is the name of the human protagonist in Princess Mononoke?":
        "Ashitaka is the last prince of the Emishi people, an actual historical group driven to northern Japan. After being cursed by a demon-possessed boar god, he journeys west to find a cure and becomes caught between nature and industrialization. His role as a mediator between both sides reflects Miyazaki's belief that environmental issues have no simple villains.",

    "San is raised by which god in Princess Mononoke?":
        "Moro is a 300-year-old wolf goddess who raised the human girl San after her parents abandoned her at the forest's edge. San fully identifies as a wolf and hates humans for destroying the forest. Moro's dying wish is for Ashitaka to save San from the hatred consuming her.",

    "What is the Forest Spirit also called in Princess Mononoke?":
        "The Shishigami (Deer God) is a serene, elk-like deity that can give and take life with a single touch. At night, it transforms into the colossal, translucent Nightwalker (Didarabocchi). When its head is severed by humans, its body becomes a destructive force that nearly destroys everything.",

    "What is Lady Eboshi's main goal in Princess Mononoke?":
        "Lady Eboshi built Iron Town as a haven for outcasts, lepers, and former brothel workers, while also seeking to kill the Forest Spirit and claim the forest's resources. She's one of Miyazaki's most nuanced antagonists: genuinely compassionate to her people but ruthlessly destructive toward nature. This moral complexity is central to the film's message.",

    "What curse does Ashitaka receive at the beginning of Princess Mononoke?":
        "A demon-possessed boar god named Nago attacks Ashitaka's village, and the demon's corruption spreads to his arm as he kills it. The curse gives him superhuman strength but will eventually kill him. The iron ball found inside Nago reveals that human weapons drove the boar god mad.",

    "Who puts a curse on Sophie in Howl's Moving Castle?":
        "The Witch of the Waste curses 18-year-old Sophie into the body of a 90-year-old woman out of jealousy over Howl's interest in her. The curse's severity fluctuates based on Sophie's emotional state, which is why she occasionally appears younger. The Witch herself is later revealed to be a victim of Madam Suliman's machinations.",

    "What is the name of the fire demon who powers Howl's castle?":
        "Calcifer is a fallen star who made a pact with young Howl, swallowing his heart to survive in exchange for powering the moving castle. This deal slowly corrupts Howl, making him increasingly inhuman. Calcifer's sardonic personality makes him one of Ghibli's most beloved supporting characters.",

    "What does Sophie's curse transform her into?":
        "Sophie is transformed into an elderly woman, but the curse has an interesting effect: freed from the anxiety of youth and appearance, she becomes more confident and assertive. Miyazaki uses the transformation to explore how people often become more themselves with age. The curse's strength visibly shifts based on Sophie's inner state.",

    "What is the name of the young boy apprentice in Howl's Moving Castle?":
        "Markl is Howl's young apprentice who disguises himself as an old man when answering the castle door to appear more intimidating. He's fiercely loyal to Howl and initially suspicious of Sophie before warming to her. His character doesn't appear in Diana Wynne Jones' original novel.",

    "What secret does Calcifer share with Sophie about his connection to Howl?":
        "Calcifer is literally powered by Howl's heart, which young Howl gave to the falling star to save its life. This is why breaking their contract could kill them both. Sophie's tears of compassion ultimately allow her to safely return Howl's heart, freeing both of them.",

    "What is the toxic jungle in Nausicaa of the Valley of the Wind called?":
        "The Sea of Corruption is a vast toxic jungle that has been slowly expanding across the post-apocalyptic world for a thousand years. Its giant fungi and insects produce poisonous spores lethal to humans. Nausicaa discovers that the jungle is actually purifying the polluted earth, and clean soil exists beneath it.",

    "What are the giant armored insect creatures in Nausicaa called?":
        "Ohmu are massive, armored, caterpillar-like creatures whose eyes shift from blue (calm) to red (enraged). They stampede when provoked, destroying everything in their path. Despite their terrifying appearance, they are intelligent and gentle beings that serve as guardians of the Sea of Corruption.",

    "What does Nausicaa ride through the wind on?":
        "The Mehve is a lightweight, jet-powered glider that Nausicaa pilots with exceptional skill through the toxic spore-filled skies. Its design was inspired by real-world hang gliders and Miyazaki's lifelong fascination with flight. Nausicaa's ability to fly represents her freedom and her role as a bridge between humans and nature.",

    "What is the name of the floating castle in Castle in the Sky?":
        "Laputa is an ancient, abandoned flying city whose name was borrowed from Jonathan Swift's 'Gulliver's Travels.' It holds immense military power through a giant crystal that can level entire cities. Miyazaki used it as a cautionary tale about the dangers of weaponized technology.",

    "What is the name of the young girl who falls from the sky in Castle in the Sky?":
        "Sheeta is a princess descended from Laputa's royal family, and her crystal pendant holds the key to the flying castle's power. She falls from a military airship at the film's start but is saved by the pendant's levitation power. She and Pazu must keep Laputa's destructive weapons from falling into the wrong hands.",

    "What is the name of the boy who catches Sheeta in Castle in the Sky?":
        "Pazu is an orphaned miner boy whose father once photographed Laputa from his airship, though no one believed him. He catches the unconscious, floating Sheeta and becomes her protector on the journey to find Laputa. His dream of vindicating his father's discovery drives much of the plot.",

    "Who is the main government villain in Castle in the Sky?":
        "Colonel Muska is a government agent who, like Sheeta, is descended from Laputa's royalty and seeks to use the city's weapons for world domination. His cold intelligence and ruthless ambition make him one of Ghibli's most menacing villains. His famous line 'I shall rule the earth!' has become iconic in Japanese pop culture.",

    "What is the name of Kiki's black cat in Kiki's Delivery Service?":
        "Jiji is Kiki's sarcastic, wise-cracking black cat companion who she can communicate with through her witch's abilities. Interestingly, in the original Japanese version, Jiji is more timid and supportive, while the English dub (voiced by Phil Hartman) made him wittier. When Kiki loses her magic, she temporarily loses the ability to understand Jiji.",

    "What service does Kiki set up in the new town in Kiki's Delivery Service?":
        "Kiki starts a flying delivery service, the only witch skill she's confident in, operating out of a bakery run by the kind Osono. The business forces her to interact with the community and builds her independence. Miyazaki based the story on his own daughter's experience of moving to a new city.",

    "What happens to Kiki's magic partway through Kiki's Delivery Service?":
        "Kiki loses her ability to fly and understand Jiji during a crisis of confidence, a metaphor for the creative burnout and self-doubt that young adults experience. Miyazaki said this reflects how artists lose inspiration when they try too hard or lose sight of why they started. Her magic returns when she has a genuine reason to fly again.",

    "What is the name of the boy who befriends Kiki in Kiki's Delivery Service?":
        "Tombo is an enthusiastic, aviation-obsessed boy whose genuine friendliness initially annoys Kiki but gradually wins her over. His dream of human-powered flight provides a parallel to Kiki's magical flying. When his experimental flying bicycle goes out of control, Kiki's desperate rescue attempt restores her powers.",

    "What are the names of the siblings in Grave of the Fireflies?":
        "Seita is a teenage boy and Setsuko is his four-year-old sister, orphaned during the firebombing of Kobe in World War II. The film, based on Akiyuki Nosaka's semi-autobiographical novel, is considered one of the most powerful anti-war films ever made. Nosaka wrote it as an apology to his own sister, who died of malnutrition during the war.",

    "What does young Setsuko keep her candy in throughout Grave of the Fireflies?":
        "The Sakuma fruit drops tin becomes the film's most heartbreaking symbol, representing the innocence and sweetness being stripped from the children's lives. As the candy runs out, Setsuko fills the empty tin with rocks and marbles, playing pretend. The tin appears in both the film's opening and closing scenes.",

    "In what war is Grave of the Fireflies set?":
        "The film takes place during the final months of World War II in Japan, specifically during the American firebombing campaign that devastated Japanese cities. The firebombing of Kobe on March 17, 1945 is the inciting event. Director Isao Takahata wanted to show war's impact on ordinary civilians rather than soldiers.",

    "What kills the children's mother at the beginning of Grave of the Fireflies?":
        "Their mother suffers severe burns during the firebombing of Kobe and dies shortly after in a makeshift hospital. Seita sees her mummified, bandaged body but hides this from Setsuko, beginning his tragic pattern of trying to shield her from reality. This scene was drawn from Nosaka's real wartime experience.",

    "Who is the protagonist of The Wind Rises?":
        "Jiro Horikoshi was a real Japanese aeronautical engineer whose life Miyazaki fictionalized for his final film. The movie blends his aviation career with elements from Tatsuo Hori's novel 'The Wind Has Risen,' adding a fictional romance. Miyazaki identified deeply with Jiro's dilemma of creating beautiful things that are used for destruction.",

    "What famous fighter plane does Jiro Horikoshi design in The Wind Rises?":
        "The Mitsubishi A6M Zero was Japan's primary fighter plane in WWII, feared for its exceptional range and maneuverability. The real Horikoshi achieved the military's impossible specifications by making the plane extremely lightweight, sacrificing armor and self-sealing fuel tanks. Miyazaki's film explores the moral weight of creating something beautiful that becomes a weapon of war.",

    # ========== DISNEY MOVIES ==========
    "What is the name of Simba's best friend in The Lion King?":
        "Nala is Simba's childhood friend who later finds him living in exile with Timon and Pumbaa. She convinces him to return to the Pride Lands and challenge Scar. In the original film, Nala was voiced by Moira Kelly, and her reunion with Simba plays out over the iconic 'Can You Feel the Love Tonight.'",

    "What is the name of Woody's horse in Toy Story?":
        "Bullseye is a toy horse from the fictional 'Woody's Roundup' TV show who first appears in Toy Story 2. Unlike most toys in the series, Bullseye doesn't speak, instead communicating through horse-like behaviors. He's fiercely loyal to Woody and was originally left behind in storage by his collector.",

    "What is the name of the fish in Finding Nemo who has memory problems?":
        "Dory suffers from short-term memory loss, which creates both comedy and genuine emotional moments throughout Finding Nemo. She was voiced by Ellen DeGeneres, whose performance was so beloved it spawned the sequel Finding Dory (2016). Despite her condition, Dory's optimism and kindness make her one of Pixar's most endearing characters.",

    "What is the name of the princess in Disney's Tangled?":
        "Rapunzel was Disney's 50th animated feature and their first CGI fairy tale princess. Her 70 feet of magical golden hair was a massive technical challenge for animators, requiring new software to render. The film's development took over a decade and cost approximately $260 million, making it one of the most expensive animated films ever.",

    "In Disney's The Lion King, who is Simba's evil uncle?":
        "Scar murdered his brother Mufasa by throwing him into a wildebeest stampede, then convinced young Simba it was his fault. Jeremy Irons' silky, sardonic voice performance defined the character, particularly in 'Be Prepared.' Scar's story is loosely based on Claudius from Shakespeare's Hamlet.",

    "What is the name of the little mermaid in the Disney classic?":
        "Ariel is the youngest of King Triton's seven daughters and her fascination with the human world drives the entire plot. She was the first Disney Princess to actively pursue her own goals rather than waiting to be rescued. Jodi Benson's voice performance, especially 'Part of Your World,' became instantly iconic.",

    "In Disney's Beauty and the Beast, what is the name of the enchanted candelabra?":
        "Lumiere is the Beast's suave, French-accented maitre d' who was transformed into a candelabra by the enchantress's spell. He performs the show-stopping 'Be Our Guest' musical number. His romantic rivalry with the feather duster Fifi (Babette) provides comic relief throughout the film.",

    "In Disney's Aladdin, what is the name of Aladdin's monkey companion?":
        "Abu is a kleptomaniac capuchin monkey whose sticky fingers frequently get Aladdin into trouble, most notably in the Cave of Wonders. He was originally going to be a parrot, but the character was changed to a monkey to differentiate him from Iago. Abu's loyalty to Aladdin is tested when Jafar transforms him into a toy.",

    "In DuckTales, what is Scrooge McDuck's famous pool filled with?":
        "Scrooge's Money Bin contains three cubic acres of gold coins that he famously dives into and swims through. In real life, diving into coins would be like diving into concrete, which the 2017 reboot actually joked about. The Money Bin represents Scrooge's wealth earned 'square,' one coin at a time through hard work.",

    "In Star Wars, what is the name of Luke Skywalker's mentor?":
        "Obi-Wan Kenobi, living under the alias 'Ben Kenobi,' watches over Luke on Tatooine for nearly two decades before revealing his Jedi heritage. Alec Guinness famously disliked the role despite it revitalizing his career, though he negotiated 2.25% of the film's gross profits. His ghost continues mentoring Luke throughout the trilogy.",

    "In Harry Potter, what house does Harry belong to?":
        "Gryffindor values bravery, daring, and chivalry, symbolized by its lion mascot and scarlet-and-gold colors. The Sorting Hat actually considered placing Harry in Slytherin due to his connection to Voldemort, but Harry's choice made the difference. J.K. Rowling named the house after the French 'gryffon d'or' meaning 'golden griffin.'",

    "What color is the Incredible Hulk?":
        "The Hulk is famously green, but he was originally grey in his first comic appearance (Incredible Hulk #1, 1962). Printing inconsistencies made the grey color look different on every page, so Stan Lee changed him to green starting with issue #2. The grey Hulk later returned as a separate personality called 'Joe Fixit.'",

    "In Disney's Hercules, who is Hercules' father?":
        "Zeus, king of the Greek gods, is Hercules' father in the Disney version. The film significantly simplified the mythology, as the Greek Heracles was actually the product of Zeus's affair with the mortal Alcmene. Disney made both parents gods to keep the story family-friendly.",

    "What is the name of the friendly ghost in the classic cartoon?":
        "Casper the Friendly Ghost first appeared in a 1945 Paramount cartoon and became Harvey Comics' most famous character. Unlike other ghosts, Casper just wants to make friends, but his appearance scares everyone away. The origin of his ghostly nature was deliberately kept vague in most versions to avoid addressing child death.",

    "In Disney's Lilo and Stitch, what number experiment is Stitch?":
        "Experiment 626 was designed by Dr. Jumba Jookiba to be the ultimate destructive force, programmed to destroy everything it touches. The number 626 was chosen because it sounds menacing while being easy to remember. Stitch's rehabilitation through Lilo's love and the concept of 'ohana' (family) is the film's core theme.",

    "In Marvel, what is the name of Thor's hammer?":
        "Mjolnir was forged in the heart of a dying star by the Dwarves of Nidavellir in Marvel lore. In Norse mythology, it was made by the dwarven brothers Sindri and Brokkr as part of a bet with Loki. The inscription reads 'Whosoever holds this hammer, if he be worthy, shall possess the power of Thor.'",

    "In Ben 10, what device allows Ben to transform into aliens?":
        "The Omnitrix is a watch-like device created by the alien genius Azmuth to promote understanding between species by literally walking in their shoes. It fell to Earth and attached itself to 10-year-old Ben Tennyson's wrist during a camping trip. Originally containing DNA of 10 aliens, its full database holds over a million species.",

    "In Disney's The Emperor's New Groove, what animal is Emperor Kuzco turned into?":
        "Yzma accidentally used a llama potion instead of the poison she intended, transforming the selfish emperor into a talking llama. The film went through years of troubled development, originally conceived as a serious epic called 'Kingdom of the Sun.' The final product's irreverent humor was a radical departure that became a cult classic.",

    "In Finding Nemo, what type of fish is Nemo?":
        "Nemo is an ocellaris clownfish (Amphiprion ocellaris), which naturally lives among the stinging tentacles of sea anemones. The film caused a massive spike in clownfish pet purchases, ironically threatening wild populations. Real clownfish are sequential hermaphrodites, meaning the dominant female's death causes the largest male to change sex.",

    "In Toy Story, who is Woody's main rival toy?":
        "Buzz Lightyear arrives as Andy's birthday present, threatening Woody's status as the favorite toy. Unlike Woody, Buzz doesn't initially know he's a toy, genuinely believing he's a space ranger. Tim Allen voiced Buzz, while Tom Hanks voiced Woody, creating one of cinema's most iconic duos.",

    "In Harry Potter, what is the name of the school Harry attends?":
        "Hogwarts School of Witchcraft and Wizardry is located in the Scottish Highlands and is hidden from Muggles by enchantments that make it appear as ruins. It was founded over a thousand years ago by four of the greatest witches and wizards of the age. The castle has 142 staircases, many of which move and change direction.",

    "In Star Wars, what weapon does Luke Skywalker use?":
        "Lightsabers are iconic energy swords powered by kyber crystals, and building one is a rite of passage for Jedi. Luke's first lightsaber was his father's blue blade, given to him by Obi-Wan. He later constructed his own green lightsaber before Return of the Jedi.",

    "In Disney's The Jungle Book, what is the name of the bear who befriends Mowgli?":
        "Baloo the bear teaches Mowgli about the 'Bare Necessities' of life in one of Disney's most beloved musical numbers. Phil Harris's laid-back voice performance defined the character as a fun-loving slacker. In Rudyard Kipling's original book, Baloo is actually a stern teacher of jungle law, quite different from Disney's version.",

    "In Disney's Snow White, how many dwarfs are there?":
        "The seven dwarfs (Doc, Grumpy, Happy, Sleepy, Bashful, Sneezy, and Dopey) were Disney's invention. The original Brothers Grimm fairy tale had unnamed dwarfs. Snow White and the Seven Dwarfs (1937) was the first full-length cel-animated feature film in motion picture history.",

    "In Marvel, what is Spider-Man's real name?":
        "Peter Parker was created by Stan Lee and Steve Ditko in 1962 as a relatable teenage hero dealing with everyday problems alongside supervillains. His origin story, being bitten by a radioactive spider and learning that 'with great power comes great responsibility,' is one of the most retold in comics. He was revolutionary as the first teenage superhero who wasn't a sidekick.",

    "In Disney's Peter Pan, who is the fairy who accompanies Peter?":
        "Tinker Bell is a fairy whose tiny body can only hold one emotion at a time, making her intensely jealous, loyal, or angry in rapid succession. She became so popular that she got her own franchise of spin-off films. In the original J.M. Barrie play, her dialogue was represented only by tinkling bells.",

    "In Disney's Sleeping Beauty, what is the name of the princess?":
        "Princess Aurora appears for only about 18 minutes of screen time in her own film and speaks fewer lines than any other Disney princess. The film took nearly a decade to produce and was Disney's most expensive animated film at the time. Its distinctive art style was inspired by medieval tapestries and Gothic art.",

    "In Disney's Cinderella, what does the fairy godmother turn into a carriage?":
        "The pumpkin-to-carriage transformation is one of Disney's most magical sequences, with the Fairy Godmother's 'Bibbidi-Bobbidi-Boo' becoming an instant classic song. Charles Perrault's 1697 version of the tale introduced the pumpkin carriage, glass slippers, and fairy godmother, none of which appeared in earlier versions. The spell breaks at midnight, adding urgency to Cinderella's evening.",

    "In Disney's Aladdin, what is the name of the villain who is the Sultan's advisor?":
        "Jafar is the Royal Vizier of Agrabah who secretly plots to steal a magic lamp and seize the throne. His design was inspired by the villain Maleficent, with animator Andreas Deja giving him a similar angular, sinister look. Jonathan Freeman voiced Jafar in both the film and the Broadway musical.",

    "In The Powerpuff Girls, what city do they protect?":
        "The City of Townsville is the perpetually endangered metropolis that somehow attracts an absurd number of supervillains and monsters. Its name is a playful generic placeholder that became iconic. Despite constant destruction, the city always seems fully rebuilt by the next episode.",

    "In Disney's Beauty and the Beast, what is the enchanted clock's name?":
        "Cogsworth is the Beast's anxious, rule-following majordomo who was transformed into a mantel clock. He serves as the foil to the free-spirited Lumiere, and their bickering provides much of the film's comedy. David Ogden Stiers voiced him with a stuffy, British-accented precision.",

    "In Disney's Mulan, what type of animal is Cri-Kee?":
        "Cri-Kee is a lucky cricket given to Mulan by her grandmother for the matchmaker visit, though he proves to be anything but lucky. Crickets are traditional symbols of good fortune in Chinese culture. Despite his tiny size, Cri-Kee gets into enormous trouble throughout the film.",

    "In Cars, what is the name of McQueen's best friend tow truck?":
        "Mater is a rusty but loveable tow truck voiced by Larry the Cable Guy, who improvised many of his lines. His full name is 'Tow Mater,' a play on 'tomater' (tomato). Despite his simple appearance, he becomes a spy in Cars 2 and is McQueen's most loyal friend.",

    "In Toy Story, who is Andy's neighbor that wants Woody?":
        "Sid Phillips is the destructive kid next door who mutilates and reassembles toys into horrifying creations. He's not truly evil but rather a creative kid who doesn't know toys are alive. When Woody breaks character to scare him, Sid's terrified reaction and subsequent gentle treatment of toys suggests he reformed.",

    "In Disney's The Little Mermaid, what does Ursula take from Ariel?":
        "Ursula takes Ariel's beautiful singing voice, storing it in a nautilus shell, in exchange for human legs. Without her voice, Ariel must make Prince Eric fall in love with her through actions alone within three days. Pat Carroll's performance as Ursula was partly inspired by the drag queen Divine.",

    "In Disney's Aladdin, what is the name of Jasmine's pet tiger?":
        "Rajah is Princess Jasmine's loyal, protective Bengal tiger who serves as both companion and guard. He's intimidating enough to scare off unwanted suitors but gentle enough to be Jasmine's cuddling partner. The animators studied real tigers to get his movements and expressions right.",

    "In Disney's Robin Hood, what animal represents Robin Hood?":
        "Disney's 1973 version cast Robin Hood as a charming, red fox, playing on the traditional association of foxes with cunning and cleverness. The entire cast was anthropomorphized animals, with Prince John as a scrawny lion and Little John as a bear. The film was made on a tight budget, reusing animation from previous Disney films.",

    "In Roblox, what is the name of the in-game currency?":
        "Robux replaced the original dual-currency system of Robux and Tix (Tickets) when Tix was removed in 2016. Players can purchase Robux with real money or earn them through creating and selling items or game passes. The Developer Exchange program allows creators to convert Robux back into real currency.",

    "In Disney's Hercules, who is the villain trying to take over Olympus?":
        "Hades, God of the Underworld, plots to overthrow Zeus by releasing the Titans during a planetary alignment. James Woods improvised much of his used-car-salesman delivery, making Hades one of Disney's most entertaining villains. In actual Greek mythology, Hades was generally a fair and neutral ruler, not a villain.",

    "What color is Sonic the Hedgehog?":
        "Sonic's signature blue color was chosen by Sega to match their cobalt blue logo, creating instant brand recognition. He was designed in 1991 by artist Naoto Ohshima to be Sega's mascot and rival to Nintendo's Mario. His blue hedgehog design was selected from several concepts, including a rabbit and an armadillo.",

    "In The Legend of Zelda: Ocarina of Time, what is the name of Link's fairy companion?":
        "Navi is a fairy assigned to Link by the Great Deku Tree, and her constant cry of 'Hey! Listen!' became one of gaming's most famous (and sometimes annoying) catchphrases. She guides Link throughout his quest across Hyrule and is essential for Z-targeting enemies. Despite players' mixed feelings about her interruptions, her departure at the end of the game is genuinely poignant.",

    "In Ben 10, what is the name of Ben's alien form made of fire?":
        "Heatblast is a Pyronite from the planet-star Pyros, and he was the very first alien Ben ever transformed into. His body is made of a magma-like substance covered in rocks, allowing him to generate and control fire. In the original series, ten-year-old Ben accidentally started a forest fire during his first transformation.",

    "In Disney's The Jungle Book, who is the King of the Apes?":
        "King Louie is a swinging orangutan who wants Mowgli to teach him the secret of man's 'red flower' (fire). Louis Prima's jazz-infused performance of 'I Wan'na Be Like You' is one of Disney's most memorable musical sequences. In the live-action remake, Louie was reimagined as a Gigantopithecus, an actual prehistoric ape.",

    "In Disney's Mulan, what is the name of the main antagonist?":
        "Shan Yu is the ruthless leader of the Hun army who invades China, and his design was made deliberately imposing with his massive build and predatory yellow eyes. His falcon scouts serve as extensions of his menacing presence. The real Hun invasions of China inspired the construction of the Great Wall.",

    "In Disney's The Princess and the Frog, what city is the movie set in?":
        "The film is set in 1920s New Orleans, making it the first Disney Princess film set in America and the first with an African American princess. The city's rich jazz culture, Creole cuisine, and bayou mysticism permeate every frame. Randy Newman's soundtrack authentically captures New Orleans' musical heritage.",

    "In Disney's Lilo and Stitch, where does the movie take place?":
        "Lilo & Stitch is set on the Hawaiian island of Kauai, and the filmmakers spent extensive time there to authentically capture the landscape and culture. It was one of the few Disney animated films not set in a fantastical location. The concept of 'ohana' (family) that drives the story is a genuine Hawaiian cultural value.",

    "In WALL-E, what is the name of the spaceship that humanity lives on?":
        "The Axiom is a massive luxury starliner built by Buy-N-Large corporation that was supposed to be a temporary home while Earth was cleaned up. After 700 years, its passengers have devolved into obese, screen-addicted consumers who can barely walk. The ship's AI, AUTO, has a secret directive to never return to Earth.",

    "In Disney's Pinocchio, what is the name of the boy who wants to be real?":
        "Pinocchio is a wooden puppet brought to life by the Blue Fairy, who promises he can become a real boy if he proves himself brave, truthful, and unselfish. The 1940 film was Walt Disney's second animated feature and is considered one of the greatest animated films ever made. Its famous message about lying (the growing nose) has become universal cultural shorthand.",

    "In Disney's Cinderella, what is the name of Cinderella's evil stepmother?":
        "Lady Tremaine is one of Disney's most realistic villains, using psychological manipulation rather than magic to control Cinderella. Her cold, calculating cruelty and the way she weaponizes her daughters makes her genuinely unsettling. Eleanor Audley also voiced Maleficent, making her the voice of two iconic Disney villains.",

    "In Disney's Robin Hood, who does Robin Hood always steal from to give to the poor?":
        "Robin Hood's 'steal from the rich, give to the poor' ethos has made him a folk hero for centuries. In Disney's version, the tyrannical Prince John (a thumb-sucking lion) overtaxes Nottingham's citizens while King Richard is away at the Crusades. The legend has been adapted hundreds of times across every medium.",

    "In Disney's Pinocchio, what is Pinocchio's defining physical feature that grows when he lies?":
        "Pinocchio's nose growing when he lies has become one of the most universally recognized symbols of dishonesty in world culture. In Carlo Collodi's original 1883 Italian novel, the nose-growing only happens a few times. Disney made it the character's defining trait, and 'Pinocchio nose' has entered common language as a metaphor for obvious lying.",

    "In Disney's Cinderella, what time must Cinderella leave the ball?":
        "The Fairy Godmother's magic expires at midnight, turning the carriage back into a pumpkin, the horses into mice, and Cinderella's gown back into rags. This deadline creates the film's dramatic tension and its most iconic scene: Cinderella fleeing down the palace steps as the clock strikes twelve. The glass slipper left behind becomes the key to her identity.",

    "In Disney's Snow White (1937), what is the name of the happy dwarf?":
        "Happy is exactly what his name suggests: the most cheerful and jovial of the seven dwarfs, always smiling and laughing. Walt Disney's team considered over 50 possible dwarf names during development, including Jumpy, Deafy, Wheezy, and Baldy. The final seven were chosen for their distinct, instantly recognizable personalities.",

    # ========== TIER 2 DISNEY / ANIMATED ==========
    "In Disney's Aladdin, who is the villain trying to marry Jasmine?":
        "Jafar seeks to marry Princess Jasmine as part of his scheme to become Sultan, using both manipulation and dark magic. He's one of Disney's most powerful sorcerers, eventually wishing to become an all-powerful genie himself. Ironically, that wish leads to his downfall, as genies are bound to their lamps.",

    "In Disney's Beauty and the Beast, who is the villain trying to marry Belle?":
        "Gaston is the arrogant, narcissistic town hero who believes Belle should marry him because he considers himself her only worthy match. He's unusual among Disney villains because he's genuinely popular and admired by the townspeople. His descent from lovable buffoon to murderous mob leader makes him surprisingly menacing.",

    "In DuckTales, what are the names of Scrooge McDuck's three nephews?":
        "Huey, Dewey, and Louie are Donald Duck's nephews left in Scrooge's care. Created by cartoonist Al Taliaferro in 1937, they were originally identical troublemakers. The 2017 DuckTales reboot gave each nephew a distinct personality and color-coded outfit.",

    "In Darkwing Duck, what is Darkwing Duck's catchphrase?":
        "While 'Let's get dangerous' is Darkwing's battle cry, his actual dramatic introduction speech starts with 'I am the terror that flaps in the night.' He follows this with a different metaphor each time ('I am the fingernail that scratches the chalkboard of your soul'). The show was a loving parody of Batman and pulp heroes.",

    "In Chip 'n Dale Rescue Rangers, what are the two main chipmunks named?":
        "Chip and Dale were originally created in 1943 as mischievous chipmunks who tormented Donald Duck and Pluto. Their names are a pun on 'Chippendale,' the famous 18th-century furniture designer. Rescue Rangers reimagined them as tiny detectives solving cases too small for the police.",

    "In TaleSpin, what character from The Jungle Book is repurposed as the pilot?":
        "Baloo the bear was reimagined as a freewheeling cargo pilot in the 1930s-inspired city of Cape Suzette. The show creatively repurposed several Jungle Book characters: Shere Khan became a corporate tycoon, and King Louie runs a nightclub. This was Disney's first animated show to feature ongoing story arcs.",

    "In The Powerpuff Girls, who created the Powerpuff Girls?":
        "Professor Utonium accidentally created the Powerpuff Girls by adding the mysterious 'Chemical X' to a mixture of sugar, spice, and everything nice. He serves as their loving, if occasionally overprotective, father figure. Creator Craig McCracken originally conceived the show as a college project called 'Whoopass Stew.'",

    "In Ben 10, how old is Ben when he finds the Omnitrix?":
        "Ben Tennyson was exactly 10 years old during a summer road trip with his grandfather Max and cousin Gwen when the Omnitrix pod crashed near their campsite. The watch attached to his wrist and wouldn't come off. The 'Ben 10' name is both his name-age combination and the number of initial alien forms.",

    "In Harry Potter, what is the name of Harry's owl?":
        "Hedwig is a snowy owl given to Harry by Hagrid as an 11th birthday present from Diagon Alley's Eeylops Owl Emporium. She serves as Harry's faithful mail carrier throughout the series. Her death in Deathly Hallows symbolizes the end of Harry's childhood innocence.",

    "In Star Wars, who is Luke Skywalker's father?":
        "Darth Vader's revelation to Luke in The Empire Strikes Back is cinema's most famous plot twist. The line is commonly misquoted as 'Luke, I am your father' when the actual line is 'No, I am your father.' Only a handful of people knew the twist before the premiere, including Mark Hamill who was told just before filming.",

    "In Disney's Lilo and Stitch, what is Stitch's original alien designation?":
        "Experiment 626 was Dr. Jumba Jookiba's masterwork: an indestructible, super-intelligent creature designed purely for destruction. The numbering system implied Jumba had created 625 previous experiments (later confirmed in the TV series). Stitch's supposed primary function was to destroy everything he touches, making his redemption through love all the more powerful.",

    "In The Incredibles, what is Mr. Incredible's real name?":
        "Bob Parr lives a frustrating suburban life as an insurance claims adjuster, hiding his super strength behind a desk. His midlife crisis about lost glory drives the first film's plot. Brad Bird based the family dynamics on his own experiences, with each family member's power reflecting their role.",

    "In Up, what is the name of the old man who floats his house with balloons?":
        "Carl Fredricksen is a retired balloon salesman who ties thousands of helium balloons to his house to fulfill his late wife Ellie's dream of visiting Paradise Falls. The film's opening montage of Carl and Ellie's life together is considered one of Pixar's most emotionally powerful sequences. Ed Asner voiced Carl with perfect grumpy tenderness.",

    "In Ratatouille, what is the name of the rat who wants to be a chef?":
        "Remy is a rat with an extraordinary sense of smell and taste who dreams of becoming a chef in Paris. He's inspired by the ghost of legendary chef Auguste Gusteau and his philosophy that 'anyone can cook.' Patton Oswalt voiced Remy, bringing genuine passion to the character's culinary ambitions.",

    "In Monsters, Inc., what is the name of the monster who scares children for a living?":
        "James P. 'Sully' Sullivan is Monsters, Inc.'s top Scarer, generating screams from children to power the monster world. John Goodman voiced him with warmth that makes his initial role as a professional fear-monger sympathetic. The film's central joke is that monsters are more afraid of children than children are of monsters.",

    "In Disney's Mulan, what is the name of the army captain Mulan serves under?":
        "Captain Li Shang is the son of General Li, tasked with training new recruits including the disguised Mulan. His training montage song 'I'll Make a Man Out of You' became one of Disney's most popular songs. He eventually discovers Mulan's secret but cannot bring himself to execute her as the law demands.",

    "In Goof Troop, what is the name of Goofy's son?":
        "Max Goof is Goofy's teenage son who is perpetually embarrassed by his well-meaning but goofy father. He later starred in A Goofy Movie (1995), where their father-son road trip became a cult classic. Max is one of the few Disney characters to visibly age across multiple appearances.",

    "In Pokemon, what is Ash Ketchum's goal?":
        "Ash's dream of becoming a Pokemon Master has driven the anime for over 25 years and 1,200+ episodes. The definition of 'Pokemon Master' was never clearly explained until the final season, where it seems to mean understanding and connecting with all Pokemon. He finally won a major league championship in the Alola region.",

    "In Cars, what is the name of the main race car character?":
        "Lightning McQueen was named after Pixar animator Glenn McQueen, who passed away in 2002 before the film's completion. His racing number 95 references the year Toy Story released. Owen Wilson's 'ka-chow!' catchphrase was improvised and became the character's signature.",

    "In Disney's The Lion King, what are the names of Simba's two comic relief friends?":
        "Timon (a meerkat) and Pumbaa (a warthog) rescue young Simba and teach him their carefree 'Hakuna Matata' philosophy. Nathan Lane and Ernie Sabella's chemistry was so perfect that they were originally auditioning for hyena roles before being cast together. Pumbaa was the first Disney character to fart on screen.",

    "In Harry Potter, what is the name of the sport played on broomsticks?":
        "Quidditch features four balls (Quaffle, two Bludgers, Golden Snitch), three types of players (Chasers, Beaters, Keepers) plus the Seeker, and two hoops per side. The Snitch catch ending the game and being worth 150 points has been criticized for making other scoring somewhat irrelevant. Real-world Quidditch leagues exist, played on foot with brooms between legs.",

    "In The Powerpuff Girls, what is the name of the main villain who is a super-intelligent chimpanzee?":
        "Mojo Jojo was once Professor Utonium's lab assistant, a normal chimp named Jojo who was accidentally exposed to Chemical X during the Powerpuff Girls' creation. The Chemical X enlarged his brain, giving him genius-level intelligence. His verbose, repetitive speaking pattern became one of the show's most quotable quirks.",

    "In DuckTales, what is the name of the inventor character?":
        "Gyro Gearloose is Duckburg's brilliant but absent-minded inventor whose creations range from helpful to catastrophically dangerous. Created by Carl Barks in 1952, he's built everything from a thinking cap to a robot that took over Duckburg. His Little Helper, a tiny robot with a lightbulb head, assists him in the lab.",

    "In Disney's The Jungle Book, what is the name of the black panther who protects Mowgli?":
        "Bagheera is the wise, protective black panther who found baby Mowgli and brought him to the wolf pack. He serves as the sensible counterpart to the carefree Baloo. In Kipling's original stories, Bagheera was born in captivity and bought his freedom, giving him a unique perspective on both human and animal worlds.",

    "In Disney's Hercules, who is Hercules' love interest?":
        "Megara (Meg) is a world-weary woman who sold her soul to Hades to save a former boyfriend who then abandoned her. Susan Egan voiced her with a sarcastic, guarded edge that made her one of Disney's most complex love interests. Her song 'I Won't Say I'm in Love' perfectly captures her reluctance to be vulnerable again.",

    "In Toy Story 3, where does Andy plan to go at the beginning of the movie?":
        "Andy is heading to college, and the question of what happens to his childhood toys drives the entire film's emotional stakes. The theme of growing up and letting go resonated deeply with audiences who were children when the original Toy Story released in 1995. Andy's final scene playing with the toys one last time before giving them away is considered one of Pixar's most emotional moments.",

    "In Disney's Tangled, who is the villain who raised Rapunzel?":
        "Mother Gothel kidnapped baby Rapunzel for the healing magic in her hair, raising her in an isolated tower for 18 years. She's one of Disney's most psychologically realistic villains, using gaslighting and emotional manipulation ('Mother Knows Best') rather than outright threats. Donna Murphy's performance captured a chillingly believable toxic parent.",

    "In Disney's The Princess and the Frog, who is the main female character?":
        "Tiana is Disney's first African American princess, a hardworking New Orleans waitress whose dream is to open her own restaurant. Unlike many Disney princesses, her motivation is career-driven rather than romance-driven. Anika Noni Rose voiced her with both determination and warmth.",

    "In Johnny Bravo, what does Johnny Bravo always carry?":
        "Johnny's oversized comb is always at the ready for maintaining his iconic Elvis-inspired pompadour hairstyle. His entire identity revolves around his appearance and his delusional belief that he's irresistible to women. The show was created by Van Partible and debuted on Cartoon Network in 1997.",

    "In Disney's Brother Bear, what is the name of Kenai's bear cub companion?":
        "Koda is an orphaned bear cub who attaches himself to bear-form Kenai, not knowing that Kenai (as a human) killed his mother. This tragic irony drives the emotional core of the film. Jeremy Suarez voiced Koda with infectious energy that makes the eventual revelation devastating.",

    "In Disney's Sleeping Beauty, what are the three fairy godmothers named?":
        "Flora (red/pink), Fauna (green), and Merryweather (blue) are the three good fairies who raise Aurora in hiding to protect her from Maleficent's curse. Their comic bickering over whether Aurora's dress should be pink or blue continues through the end credits. They were animated by some of Disney's legendary Nine Old Men.",

    "In Disney's The Little Mermaid, what is the name of Ariel's fish friend?":
        "Flounder is Ariel's loyal but easily frightened best friend who accompanies her on adventures despite his anxieties. Despite his name, he's actually a tropical fish, not a flounder. His courage at key moments, despite constant fear, makes him one of Disney's most relatable sidekicks.",

    "In Darkwing Duck, what is the name of the villain organization that opposes S.H.U.S.H.?":
        "F.O.W.L. (Fiendish Organization for World Larceny) is a criminal organization that serves as the primary antagonistic group in both Darkwing Duck and DuckTales. Their name is a deliberate bird pun to match the duck-themed universe. They're a parody of classic spy-fiction organizations like SPECTRE and HYDRA.",

    "In Disney's Hercules, what are the names of Hades' two bumbling minions?":
        "Pain and Panic are shape-shifting imps whose incompetence repeatedly foils Hades' plans, starting with their failure to make baby Hercules fully mortal. Their dynamic is a comedy duo of physical humor, with Pain being the stocky, pink one and Panic being the thin, blue one. Bobcat Goldthwait voiced Pain with his signature frantic energy.",

    "In Disney's Pinocchio, what is the name of the puppet-maker who creates Pinocchio?":
        "Geppetto is a kindly, lonely woodcarver who wishes upon a star for his puppet to become a real boy. The Blue Fairy grants his wish, bringing Pinocchio to life. Christian Rub voiced him with gentle warmth in the 1940 film, which Walt Disney considered his personal masterpiece.",

    "In Cars, what is the name of the small town where McQueen gets stranded?":
        "Radiator Springs was once a thriving stop on Route 66 but was bypassed when the interstate highway system was built, turning it into a ghost town. The town is a love letter to real Route 66 communities that suffered the same fate. McQueen's community service there teaches him that life is about the journey, not just winning.",

    "In Toy Story 2, who is the vintage toy cowgirl that Woody meets?":
        "Jessie is a yodeling cowgirl from the Woody's Roundup toy line who was abandoned by her owner Emily when she grew up. Her heartbreaking backstory, set to 'When She Loved Me' by Sarah McLachlan, is one of Pixar's most emotional sequences. Joan Cusack voiced her with both manic energy and genuine vulnerability.",

    "In Disney's Tangled, what is the name of the horse who pursues Flynn Rider?":
        "Maximus is a palace horse with the determination of a bloodhound and the personality of a strict law enforcement officer. He's the most capable character in the film, tracking Flynn Rider with more skill than any human guard. His eventual friendship with Flynn, brokered by Rapunzel, provides some of the film's best comedy.",

    "In Chip 'n Dale Rescue Rangers, what is the name of the gadget-inventing female mouse?":
        "Gadget Hackwrench is a brilliant inventor who builds incredible machines from everyday junk and serves as the team's pilot and engineer. She developed a huge cult following and even has a real-life religious following in Russia (no, really). She's one of the earliest examples of a capable female inventor in children's animation.",

    "In Ben 10, what is the name of Ben's alien form that can turn invisible?":
        "Ghostfreak (Zs'Skayr) is an Ectonurite from the planet Anur Phaetos whose abilities include invisibility, intangibility, and possession. Uniquely among Ben's aliens, Ghostfreak has its own consciousness and eventually escapes the Omnitrix to become a recurring villain. It's one of the creepiest alien designs in the series.",

    "In WALL-E, what does WALL-E collect as a hobby?":
        "WALL-E compulsively collects interesting objects from the trash he compacts, including a Rubik's Cube, a light bulb, and a spork. His most prized possession is a VHS tape of Hello, Dolly! that taught him about love and holding hands. These collections humanize him and show that curiosity and wonder persist even in a world of garbage.",

    "In The Incredibles, who is the villain who tries to eliminate superheroes?":
        "Syndrome (born Buddy Pine) was once Mr. Incredible's biggest fan who was rejected as a kid sidekick. He grew up to become a tech genius who secretly killed dozens of superheroes with his Omnidroid to eventually stage a fake heroic rescue. His line 'When everyone's super, no one will be' perfectly captures his twisted philosophy.",

    "In Disney's Snow White, what does the Evil Queen disguise herself as?":
        "The Queen transforms herself into a hideous old hag using a potion, then lures Snow White with a poisoned apple. This transformation scene was considered genuinely frightening when the film debuted in 1937, reportedly causing some children to be escorted from theaters. The disguise is so effective that even the audience barely recognizes her.",

    "In Monsters, Inc., what do monsters use as energy for their city?":
        "Monstropolis is powered by children's screams, which monsters collect through closet doors that connect to human bedrooms. The entire economy depends on scaring children, with top Scarers treated as celebrities. The film's twist reveals that laughter generates ten times more power than screams, completely transforming their society.",

    "In Up, what country does Carl travel to in his flying house?":
        "Carl's balloon-powered house drifts to the tepui plateaus of Venezuela, specifically to find Paradise Falls (inspired by the real Angel Falls). The setting was chosen because the flat-topped tepuis look otherworldly and fit the adventure's sense of discovery. Pixar's production team actually traveled to Venezuela for research.",

    "In Disney's Peter Pan, who is the villain that pursues Peter Pan?":
        "Captain Hook lost his hand to Peter Pan, who then fed it to a crocodile. The crocodile enjoyed it so much that it follows Hook everywhere, hoping for more. The ticking clock the croc swallowed serves as Hook's personal alarm system of approaching doom. Hans Conried voiced both Hook and Mr. Darling in the 1953 film.",

    "In Toy Story, what is the name of Andy's toy dinosaur?":
        "Rex is a tyrannosaurus rex toy with severe anxiety and self-esteem issues, constantly worried about being too scary or not scary enough. Wallace Shawn's nervous voice perfectly captures Rex's personality. Despite being a fearsome dinosaur toy, he's terrified of everything, especially the dark.",

    "In Disney's Snow White, what is the name of the sleeping dwarf?":
        "Sleepy is perpetually drowsy and half-asleep, often seen yawning or struggling to keep his eyes open. He's one of the seven dwarfs whose names were carefully chosen to be instantly recognizable personality descriptors. Despite his sleepiness, he rallies with the others to chase the Evil Queen off a cliff.",

    "In Disney's Sleeping Beauty, what is the name of the evil fairy?":
        "Maleficent calls herself 'the Mistress of All Evil' and is widely considered the greatest Disney villain of all time. She curses baby Aurora simply because she wasn't invited to the christening, demonstrating a terrifying sense of petty vindictiveness backed by enormous power. Her transformation into a dragon for the climax is one of Disney's most spectacular scenes.",

    "In Disney's The Princess and the Frog, what is the name of the firefly who helps Tiana?":
        "Ray is a lovesick Cajun firefly who's devoted to Evangeline, which he believes is a beautiful firefly but is actually the Evening Star. His accent and personality bring authentic Louisiana charm to the film. His fate in the climax is one of the most bittersweet moments in Disney history.",

    "In Toy Story 3, what is the name of the pink strawberry-scented bear villain?":
        "Lots-o'-Huggin' Bear (Lotso) was once a beloved toy who was accidentally left behind by his owner and replaced. The trauma of being replaced twisted him into a prison-warden-like tyrant at Sunnyside Daycare. His strawberry scent and huggable appearance mask one of Pixar's most genuinely threatening villains.",

    "In Ben 10, what is the name of Ben's alien form that shrinks him?":
        "Grey Matter is a tiny Galvan from the planet Galvan Prime whose species compensates for their 5-inch height with incredible intelligence. When Ben transforms into Grey Matter, he gains genius-level problem-solving abilities. The Galvan are the smartest species in the Ben 10 universe and actually created the Omnitrix.",

    "In Disney's The Lion King, what is the name of Simba's mother?":
        "Sarabi is the queen of Pride Rock and Mufasa's mate, whose name means 'mirage' in Swahili. After Mufasa's death, she refuses to bow to Scar's tyranny and endures his cruel leadership with dignity. Madge Sinclair voiced her in the original film with regal strength.",

    "In Disney's Aladdin, who does Aladdin disguise himself as?":
        "Aladdin uses one of his three wishes from the Genie to become 'Prince Ali Ababwa,' complete with a massive parade entrance. The elaborate disguise includes servants, riches, and exotic animals. Despite the spectacle, Jasmine sees through the facade because the person underneath remains the same street rat she was drawn to.",

    "In Disney's The Little Mermaid, what is Ariel's father's name?":
        "King Triton is the ruler of Atlantica and Ariel's overprotective father who forbids any contact with the human world. His trident is the symbol of his power over the seas. His extreme reaction to Ariel's human collection (destroying it in anger) drives her to make the desperate deal with Ursula.",

    "In Disney's Sleeping Beauty, what is the name of Aurora's kingdom?":
        "King Stefan's unnamed kingdom is where Aurora was born and cursed by Maleficent. The film never gives the kingdom a formal name, unlike later Disney films. The kingdom's medieval European aesthetic, inspired by Gothic and pre-Raphaelite art, set the visual tone for the entire film.",

    "In Disney's Peter Pan, what are the names of the three Darling children?":
        "Wendy, John, and Michael Darling are whisked away to Neverland by Peter Pan one night when their father threatens to move Wendy out of the nursery. Wendy serves as a mother figure to the Lost Boys, John plays at being a leader, and young Michael is the innocent adventurer. Their family name 'Darling' was J.M. Barrie's deliberate choice to emphasize their beloved status.",

    "In Disney's Cinderella, what object identifies Cinderella to the prince?":
        "The glass slipper is a magical creation of the Fairy Godmother that didn't revert to normal at midnight like everything else. The Prince uses it to search the kingdom for the mysterious woman from the ball. Charles Perrault's 1697 version introduced the glass slipper, though some scholars believe it was a mistranslation of 'fur' (vair vs. verre).",

    "In Disney's Hercules, what does Hercules need to do to prove himself a true hero?":
        "Despite becoming the greatest warrior in Greece and defeating countless monsters, Hercules only becomes a true hero when he willingly sacrifices his immortality to save Megara. Zeus and the gods restore his godhood as a reward, but Hercules chooses to remain mortal to be with Meg. The message is that true heroism comes from selfless love, not strength.",

    "In Disney's Mulan, what disguise does Mulan use to join the army?":
        "Mulan cuts her hair, steals her father's armor, and joins the army under the male name 'Ping' to save her elderly, injured father from conscription. Impersonating a man in the army was historically punishable by death in China. Ming-Na Wen voiced Mulan with both vulnerability and determination.",

    # ========== TIER 3 ==========
    "In DuckTales, who is Scrooge McDuck's pilot?":
        "Launchpad McQuack is an enthusiastic but spectacularly terrible pilot who crashes virtually every vehicle he operates. Despite this, he's fiercely loyal and surprisingly effective in a crisis. He later became Darkwing Duck's sidekick, making him one of the few characters to appear in both shows.",

    "In Darkwing Duck, what is Darkwing Duck's real name?":
        "Drake Mallard is a suburban dad by day and St. Canard's masked vigilante by night. The show was a loving parody of Batman, The Shadow, and other pulp heroes. Jim Cummings voiced him with perfect dramatic pomposity.",

    "In TaleSpin, what is the name of Baloo's cargo plane?":
        "The Sea Duck is a modified Conwing L-16 seaplane that serves as Baloo's beloved cargo hauler, though it technically belongs to Rebecca Cunningham's Higher for Hire business. Baloo's emotional attachment to the plane is a running theme. The show's 1930s aviation aesthetic was inspired by real-world seaplane era adventures.",

    "In Chip 'n Dale Rescue Rangers, who is the main villain?":
        "Fat Cat is a well-dressed, cigar-smoking feline crime lord who operates the animal underworld while his human owner remains oblivious. He commands a gang of animal henchmen and runs various criminal schemes. His character parodies classic mob bosses, particularly from film noir.",

    "In Goof Troop, what is the name of Goofy's neighbor?":
        "Pete (Peg-Leg Pete) has been antagonizing Disney characters since 1925, making him one of the oldest Disney characters still in use. In Goof Troop, he's reimagined as Goofy's scheming but ultimately harmless suburban neighbor. His relationship with Goofy is a classic odd-couple dynamic.",

    "In Johnny Bravo, what is Johnny Bravo's most notable personality trait?":
        "Johnny's extreme vanity is the engine of almost every episode's plot, as he constantly flexes and hits on women who invariably reject him. Despite his muscular appearance, he's actually quite weak and cowardly. The character was partly inspired by Elvis Presley's look and James Dean's confidence.",

    "In Disney's The Emperor's New Groove, who is Emperor Kuzco's loyal advisor turned villain?":
        "Yzma is an elderly, purple-clad sorceress who was Kuzco's advisor before he fired her, triggering her revenge plot. Eartha Kitt voiced her with campy, over-the-top malice that made her instantly iconic. Her repeated failures to accomplish anything, despite her intelligence, provide the film's best comedy.",

    "In Disney's The Jungle Book, what is the name of the python who hypnotizes his victims?":
        "Kaa is a massive Indian rock python whose hypnotic eyes can put victims in a trance. Sterling Holloway (who also voiced Winnie the Pooh) gave him a sinister, silky voice. In Kipling's original stories, Kaa was actually an ally who helped Mowgli, not a villain.",

    "In Disney's Peter Pan, what is the name of the island where the Lost Boys live?":
        "Neverland is a magical island where children never grow up, inhabited by Lost Boys, mermaids, pirates, and fairies. J.M. Barrie's creation has become a universal metaphor for eternal childhood and the refusal to face adult responsibilities. The island was originally called 'The Never Never Land' in Barrie's 1904 play.",

    "In Toy Story 3, where do the toys end up at the beginning of the movie?":
        "Sunnyside Daycare appears to be toy paradise but is actually controlled by the tyrannical Lotso, who assigns new toys to the toddler room where they're brutally played with. The daycare operates like a prison, complete with a guard (Big Baby) and escape-proof security measures. The toys' escape plan is a direct homage to The Great Escape.",

    "In Up, what is the name of the rare bird Carl and Russell encounter?":
        "Kevin is a 13-foot-tall flightless bird that Russell names before discovering it's female. She's the reason explorer Charles Muntz has remained in South America for decades, obsessively trying to capture her as proof of her species' existence. Kevin's colorful design was inspired by the Himalayan Monal pheasant.",

    "In Monsters, Inc., what is the name of the little girl who befriends Sully?":
        "Boo is a fearless toddler whose real name is Mary, glimpsed on her drawings. She accidentally enters the monster world through her closet door and forms a heartwarming bond with the initially terrified Sully. Her door being shredded and later rebuilt is one of Pixar's most emotionally satisfying conclusions.",

    "In Ratatouille, what is the name of the restaurant Remy dreams of cooking in?":
        "Gusteau's is a Parisian restaurant that lost one of its five stars after founder Auguste Gusteau died, reportedly of a broken heart following a harsh review by critic Anton Ego. The restaurant's motto 'Anyone Can Cook' inspires Remy's culinary dreams. Under Remy's secret guidance, the restaurant regains its reputation.",

    "In Disney's Snow White, what does the Evil Queen use to put Snow White to sleep?":
        "The poisoned apple puts Snow White into a death-like sleep that can only be broken by 'Love's First Kiss.' The Queen dips the apple in a Sleeping Death potion, making only one side poisonous. This scene was so frightening in 1937 that some theaters had to reupholster seats that young children had damaged in terror.",

    "In Marvel's Spider-Man, what gave Peter Parker his powers?":
        "A radioactive spider bit Peter during a science exhibition, granting him proportional strength and agility of a spider, plus a 'spider-sense' danger warning. In the original 1962 comic, the spider was irradiated, while later versions changed it to genetically modified. The bite scene has been reimagined in virtually every Spider-Man adaptation.",

    "In Harry Potter, what is the name of Dumbledore's phoenix?":
        "Fawkes is a phoenix whose tears have healing powers and who can carry immensely heavy loads. He rescues Harry in the Chamber of Secrets by providing the Sorting Hat (containing the sword of Gryffindor) and healing Harry's basilisk wound with his tears. Phoenixes burst into flame when they die and are reborn from the ashes.",

    "In The Legend of Zelda, what are the three pieces of the Triforce?":
        "The Triforce of Power (held by Ganondorf), Wisdom (held by Zelda), and Courage (held by Link) together form the complete Triforce created by the three Golden Goddesses. Each piece grants its holder immense power aligned with its nature. If someone with an imbalanced heart touches the complete Triforce, it splits into three pieces.",

    "In Disney's Brother Bear, what animal does Kenai get transformed into?":
        "Kenai is transformed into a bear by the Great Spirits as punishment for killing a bear in anger after his brother Sitka's death. Living as a bear forces him to understand the creatures he hated and see the world from their perspective. The transformation is a journey of empathy that changes his entire worldview.",

    "In Disney's Cinderella, what does the glass slipper identify?":
        "The glass slipper is the only clue the Prince has to find the mystery woman from the ball, and it magically fits only Cinderella's foot perfectly. Lady Tremaine tries to prevent the fitting by tripping the servant carrying the slipper, shattering it, but Cinderella produces the matching slipper. This moment is the ultimate triumph over her stepmother's control.",

    "In Disney's The Little Mermaid, what is the name of Ariel's crab guardian?":
        "Sebastian is the Jamaican-accented court composer whom King Triton tasks with keeping an eye on Ariel. Samuel E. Wright's performance of 'Under the Sea' and 'Kiss the Girl' won an Academy Award for Best Original Song. Sebastian was originally written as a stuffy British crab before the calypso approach was chosen.",

    "In Disney's Beauty and the Beast, what is the name of the enchanted teapot?":
        "Mrs. Potts is the castle's warm-hearted head housekeeper who was transformed into a teapot along with her son Chip (a teacup). Angela Lansbury's performance of 'Beauty and the Beast' was recorded in a single take. She initially resisted singing it, feeling she was too old for the role.",

    "In DuckTales, what is the name of the robot suit worn by Fenton Crackshell?":
        "The Gizmoduck armor is activated by Fenton shouting 'Blathering blatherskite!' and transforms him into a one-wheeled superhero. Fenton is Scrooge's bumbling accountant by day and Duckburg's armored protector by night. The suit was created by Gyro Gearloose and its password was accidentally set to the first thing Fenton said.",

    "In Disney's Mulan, what is the name of Mulan's horse?":
        "Khan is Mulan's loyal black horse who carries her through her entire military campaign. His name likely references Genghis Khan, fitting the film's Central Asian conflict. Khan shows remarkable courage throughout the film, including leaping across a chasm to save the army.",

    "In Disney's Pinocchio, what is the name of the villain who uses Pinocchio as a puppet attraction?":
        "Stromboli is a menacing puppeteer who imprisons Pinocchio in a birdcage after seeing his potential as a stringless marionette act. He threatens to chop Pinocchio into firewood when he's no longer useful. His rage and cruelty make him one of Disney's earliest genuinely frightening villains.",

    "In Disney's Peter Pan, who is the leader of the Lost Boys?":
        "Peter Pan is the leader of the Lost Boys, a group of children who fell out of their prams and were sent to Neverland because they weren't claimed in seven days. Peter refuses to grow up and acts as their charismatic but sometimes thoughtless leader. In Barrie's original work, Peter would 'thin out' Lost Boys who grew too old.",

    "In Disney's Robin Hood, what animal is Little John?":
        "Little John is a large, friendly bear who serves as Robin Hood's best friend and partner in crime. Phil Harris, who also voiced Baloo in The Jungle Book, gave Little John the same loveable personality. The animation for Little John was actually recycled from Baloo due to budget constraints.",

    "In Ratatouille, what is the name of the chef who inherits Gusteau's restaurant?":
        "Chef Skinner inherited Gusteau's restaurant and was secretly mass-producing frozen meals under the Gusteau brand name. He discovers that Linguini is actually Gusteau's son and the rightful owner, then tries to suppress this information. Ian Holm voiced him as a comically petty, Napoleon-complex villain.",

    "In Disney's Hercules, who is Hercules' satyr trainer?":
        "Phil (Philoctetes) is a curmudgeonly satyr who has trained heroes for centuries but was burned out after none of them achieved true greatness. Danny DeVito voiced him with perfect world-weary sarcasm. Phil's montage of failed heroes ('I trained all those would-be heroes') is a highlight.",

    "In Disney's Sleeping Beauty, what gift does the third fairy change the curse to?":
        "Merryweather couldn't undo Maleficent's death curse entirely, but she softened it so Aurora would fall into a deep sleep instead of dying, breakable only by true love's kiss. This is a clever narrative device: the good fairies are powerful but not powerful enough to directly counter Maleficent. The limitation drives the entire plot.",

    "In TaleSpin, what is the name of the company Baloo works for?":
        "Higher for Hire is a struggling cargo delivery service owned by Rebecca Cunningham, who bought the company and became Baloo's boss. The dynamic between freewheeling Baloo and business-minded Rebecca drives much of the show's humor. Rebecca's young daughter Molly also lives at the business.",

    "In DuckTales, what is the name of the ancient city of gold that the gang searches for?":
        "El Dorado, the legendary city of gold, was one of several famous treasures Scrooge pursued in the series. The five-part pilot 'Treasure of the Golden Suns' established the show's adventure-serial format. DuckTales drew heavily from Carl Barks' classic Uncle Scrooge comics, which pioneered adventure stories in the Disney Duck universe.",

    "In Disney's Robin Hood, what is the name of the sheriff who enforces Prince John's laws?":
        "The Sheriff of Nottingham is a bullying wolf who gleefully collects Prince John's oppressive taxes, even stealing from the poor. Pat Buttram voiced him with a southern drawl that made him both comical and menacing. His constant squeezing of citizens for tax money is historically accurate to medieval England.",

    "In Disney's Pinocchio, what is the name of the whale that swallows Geppetto?":
        "Monstro is a massive, terrifying whale who swallows ships whole, including the raft Geppetto set out on to find Pinocchio. The whale chase sequence features some of the most impressive animation of the 1940 film. In the original Italian novel by Collodi, the creature was a giant shark called 'The Terrible Dogfish.'",

    "In Toy Story 2, who is the prospector toy villain?":
        "Stinky Pete the Prospector has never been removed from his box and is desperate to be displayed in a Tokyo museum rather than risk being discarded by a child. Kelsey Grammer voiced him with folksy charm that masks his manipulative nature. His breakdown when his box is opened reveals years of shelf-warming bitterness.",

    "In The Incredibles, what is the name of the superhero costume designer?":
        "Edna Mode is a diminutive, no-nonsense fashion designer whose 'No capes!' monologue (illustrating cape-related superhero deaths) is one of Pixar's most quoted scenes. Director Brad Bird voiced her himself because no one else captured the character's energy. She's partially inspired by legendary costume designer Edith Head.",

    "In Up, what is the name of the talking dog who helps Carl and Russell?":
        "Dug is a Golden Retriever whose special collar translates his thoughts into speech, revealing a hilariously simple and loveable inner monologue. His 'SQUIRREL!' exclamation became an instant cultural touchstone. Despite being part of the villain's pack, his genuine sweetness makes him switch sides immediately.",

    "In Disney's Snow White, what is the name of the bashful dwarf?":
        "Bashful is the perpetually blushing, shy dwarf who can barely speak around Snow White without turning red and twisting his beard. His shy personality makes him endearing among the seven dwarfs. Walt Disney's character team carefully ensured each dwarf's name instantly communicated their defining trait.",

    "In Disney's Mulan, what is the name of Mulan's lucky cricket?":
        "Cri-Kee was given to Mulan by her grandmother as a lucky charm for the matchmaker meeting. Ironically, he causes more chaos than good luck. Real crickets are indeed considered lucky in Chinese culture, where cricket-keeping has been a tradition for thousands of years.",

    "In Disney's The Jungle Book, what is the name of the tiger villain?":
        "Shere Khan is a man-hating Bengal tiger whose menacing, sophisticated demeanor makes him the most feared creature in the jungle. George Sanders voiced him with aristocratic elegance in the 1967 film. In Kipling's stories, Shere Khan means 'Tiger King' (shere = tiger in Hindi-Urdu, khan = ruler).",

    "In Disney's The Princess and the Frog, what is the name of the Shadow Man villain?":
        "Dr. Facilier is a smooth-talking voodoo sorcerer who makes deals with dark spirits called 'Friends on the Other Side.' Keith David's deep, commanding voice performance made Facilier one of Disney's coolest villains. His powers come from serving shadow demons who will collect his soul if he fails to deliver.",

    "In Disney's Brother Bear, who are the moose duo that comedically accompany Kenai?":
        "Rutt and Tuke are a pair of Canadian moose brothers voiced by Rick Moranis and Dave Thomas, reprising their iconic Bob and Doug McKenzie characters from SCTV. Their 'hoser' humor and sibling bickering provide comic relief throughout the film. They were added to lighten the movie's heavy emotional themes.",

    "In Disney's Hercules, what are the gospel-singing Muses?":
        "The five Muses serve as a Greek chorus narrating the story through gospel-inspired musical numbers, a brilliant anachronistic choice by the filmmakers. They interrupt the traditional narrator at the film's start, declaring his version too boring. This blending of ancient Greek mythology with African American gospel music was one of the film's most creative decisions.",

    "In The Incredibles, what is Violet's superpower?":
        "Violet can turn invisible and project protective force fields, powers that perfectly reflect her shy, withdrawn teenage personality. As she gains confidence through the film, her control over both powers strengthens. Brad Bird deliberately matched each family member's power to their personality: the shy teen turns invisible, the hyperactive kid has super speed, etc.",

    "In Disney's Sleeping Beauty, what kingdom does Prince Phillip come from?":
        "Prince Phillip comes from the neighboring kingdom ruled by King Hubert, who arranged a betrothal with Aurora when both were infants. Despite the arranged marriage, Phillip and Aurora actually fall in love independently in the forest before realizing who each other is. Phillip was the first Disney prince to have a significant personality and active role in the story.",

    "In DuckTales (1987), what is the first multi-episode adventure arc called?":
        "Treasure of the Golden Suns was a five-part story that served as the series premiere, sending Scrooge around the world to find pieces of a treasure map. It established the show's globe-trotting adventure format and introduced key characters. The serial format was unusual for children's animation at the time.",

    "In Disney's Cinderella, what are the names of Cinderella's two wicked stepsisters?":
        "Anastasia and Drizella are Cinderella's clumsy, jealous stepsisters who are spoiled rotten by their mother Lady Tremaine. In the original Grimm fairy tale, the stepsisters cut off parts of their feet to fit the slipper. Disney's sequels actually gave Anastasia a redemption arc where she falls in love and reforms.",

    "In Disney's The Princess and the Frog, what is the full name of the villain?":
        "Dr. Facilier, also known as the Shadow Man, is a bokor (voodoo sorcerer) who draws power from dark spirits. His name comes from the French word 'facile' meaning 'easy,' reflecting his smooth, persuasive nature. His musical number 'Friends on the Other Side' is one of Disney's most atmospheric villain songs.",

    "In Disney's Brother Bear, what animal is Kenai's spirit animal totem associated with?":
        "Kenai's totem is the Bear of Love, which he initially sees as a cruel joke since he hates bears for causing his brother's death. His transformation into a bear forces him to literally embody what his totem represents. The irony of learning love through the creature he despised is the film's central theme.",

    "In DuckTales, what is the name of the young female pilot who works with the gang?":
        "Webby Vanderquack is actually Mrs. Beagley's granddaughter and Scrooge's honorary family member, not a pilot. She's an energetic young girl who joins the nephews' adventures. The 2017 reboot significantly expanded her character, making her a conspiracy-theorist adventurer with deep ties to Scrooge's family history.",

    "In Darkwing Duck, what is the name of the villain Darkwing battles who controls plants?":
        "Bushroot was a botanist named Reginald who experimented on himself to photosynthesize like a plant, accidentally turning himself into a plant-duck hybrid. He's the most sympathetic of the Fearsome Five villains, often just wanting companionship. His tragic origin makes him Darkwing Duck's most complex antagonist.",

    # ========== TIER 4 ==========
    "In DuckTales (1987), who is the villain known as the richest duck in the world after Scrooge?":
        "Flintheart Glomgold is Scrooge's South African rival who claims to be the world's second-richest duck, a ranking that infuriates him. Unlike Scrooge who earned his fortune honestly, Glomgold uses dirty tricks and shortcuts. Carl Barks created him in 1956 as the anti-Scrooge: equally driven but without moral principles.",

    "In Darkwing Duck, what is the name of Darkwing's sidekick who is also Scrooge's pilot?":
        "Launchpad McQuack bridges the DuckTales and Darkwing Duck universes as the only character to be a main cast member of both shows. His crash-prone flying skills somehow translate into effective crime-fighting assistance. His unwavering loyalty and optimism make him the perfect foil for Darkwing's ego.",

    "In TaleSpin, who is the main villain and leader of the air pirates?":
        "Don Karnage is a flamboyant, swashbuckling wolf who leads a gang of air pirates from their massive ship, the Iron Vulture. His theatrical personality and butchering of idioms ('I am a great pirate, am I not?') make him endlessly quotable. Jim Cummings voiced him with a gloriously hammy faux-Spanish accent.",

    "In Chip 'n Dale Rescue Rangers, what is the name of the mouse who wears a flight jacket?":
        "Monterey Jack ('Monty') is a burly, world-traveling Australian mouse whose only weakness is cheese, which sends him into an uncontrollable frenzy. His adventurous backstory gives the team a wealth of underworld contacts and knowledge. His cheese addiction is played for laughs but has derailed missions more than once.",

    "In Goof Troop, what city does the show take place in?":
        "Spoonerville is the fictional suburban town where Goofy and Pete live as neighbors. The town's ordinary setting grounds the show's comedy in relatable suburban life. It later serves as the starting point for A Goofy Movie's cross-country road trip.",

    "In the original DuckTales (1987), who is the sorceress who wants Scrooge's Number One Dime?":
        "Magica De Spell is a sorceress from Mount Vesuvius who believes Scrooge's Number One Dime, being the first coin earned by the world's richest duck, possesses immense magical power. She's been trying to steal it for decades across comics, cartoons, and the 2017 reboot. Carl Barks created her in 1961, inspired by Italian actress Sophia Loren.",

    "In Darkwing Duck, what is the name of Darkwing's adopted daughter?":
        "Gosalyn Mallard (born Gosalyn Waddlemeyer) is a spirited, tomboyish redhead whose fearlessness often gets her into trouble. Drake Mallard adopted her after saving her from villain Taurus Bulba. Her reckless energy and willingness to join fights provides both comedy and genuine stakes for Darkwing.",

    "In TaleSpin, what city serves as Baloo's home base?":
        "Cape Suzette is a cliff-enclosed harbor city accessible only through a narrow sea-cliff gap, protected by anti-aircraft guns. This natural fortress setting gave the show its unique blend of adventure and safety. The city's 1930s Art Deco aesthetic was inspired by real-world cities like Rio de Janeiro.",

    "In Disney's Robin Hood (1973), who plays the role of King Richard's brother and villain?":
        "Prince John is a scrawny, thumb-sucking lion who serves as regent while his brother King Richard is away at the Crusades. Peter Ustinov voiced him as a pompous, whiny coward. His constant cry of 'Mommy!' when threatened became one of the film's most memorable running gags.",

    "In Disney's Peter Pan (1953), what is the name of the Darling children's dog-nanny?":
        "Nana is a Saint Bernard who serves as the Darling children's nursemaid, a role she takes very seriously. Mr. Darling banishes her to the yard the night Peter Pan arrives, removing the children's last line of protection. In Barrie's original play, Nana was played by a human actor in a dog costume.",

    "In Disney's Pinocchio (1940), what is the name of Pinocchio's goldfish?":
        "Cleo is Geppetto's coquettish pet goldfish who lives in a bowl in his workshop. She's known for her flirtatious behavior toward Figaro the cat. Cleo later appeared in other Disney properties as a minor recurring character.",

    "In Johnny Bravo, what city does Johnny live in?":
        "Aron City is named after Elvis Aaron Presley, fitting Johnny's Elvis-inspired character design and personality. The town serves as a backdrop for Johnny's misadventures in hitting on women and getting into absurd situations. The show was one of Cartoon Network's earliest original productions.",

    "In Disney's Hercules, who are the Muses?":
        "The five Muses narrate Hercules' story through gospel-style musical numbers, an unexpected but brilliant fusion of Greek mythology and soul music. They are named Calliope, Clio, Melpomene, Terpsichore, and Thalia. Their spirited performances ('Zero to Hero,' 'The Gospel Truth') set the film's irreverent tone.",

    "In Disney's Brother Bear (2003), who are the comedic moose duo that Kenai encounters?":
        "Rutt and Tuke are Canadian moose brothers voiced by Rick Moranis and Dave Thomas, directly channeling their classic Bob and Doug McKenzie characters. Their 'eh' and 'hoser' filled dialogue provides lighthearted contrast to the film's heavier themes. They were specifically added to the film to balance its emotional intensity.",

    "In Cars, who is the legendary racing car that becomes McQueen's mentor?":
        "Doc Hudson is a 1951 Hudson Hornet who was once a champion racer (the 'Fabulous Hudson Hornet') before a devastating crash ended his career. Paul Newman voiced him in what became his final animated role. The real Hudson Hornet dominated NASCAR from 1951 to 1954.",

    "In Disney's Tangled, what is Flynn Rider's real name?":
        "Eugene Fitzherbert adopted the alias 'Flynn Rider' from his favorite childhood adventure book hero. He grew up in an orphanage reading tales of Flynn Rider's daring exploits. His real name reveal is a pivotal moment of vulnerability that deepens his relationship with Rapunzel.",

    "In DuckTales, what is the name of the Beagle Boy gang who always tries to rob Scrooge?":
        "The Beagle Boys are a large family of criminals identified by their prison ID numbers, led by their mother Ma Beagle. Created by Carl Barks in 1951, they're Scrooge's most persistent antagonists. Despite their numbers, they're consistently outwitted by Scrooge and his family.",

    "In Darkwing Duck, what is the name of the electric-powered villain?":
        "Megavolt was once a nerdy high school student named Elmo Sputterspark who was electrocuted during a science experiment, gaining electrical powers but losing most of his sanity. He believes electrical devices are alive and 'frees' them from their human oppressors. He's a member of the Fearsome Five and one of Darkwing's most recurring foes.",

    "In Goof Troop, what is the name of Pete's daughter?":
        "Pistol Pete is Pete's hyperactive, attention-demanding young daughter who provides additional chaos to the neighborhood dynamics. She's significantly younger than PJ and Max, creating a typical little-sister annoyance dynamic. Her energy level is somehow even higher than Goofy's.",

    "In The Powerpuff Girls (original series), what is the name of the sinister red devil villain?":
        "HIM is an effeminate, lobster-clawed devil figure whose voice shifts between sweet falsetto and terrifying bass. He's considered the most powerful and dangerous villain in the series, capable of manipulating reality itself. Creator Craig McCracken designed him to be as unsettling as possible for a children's show.",

    "In Disney's Snow White, what is the name of the grumpy dwarf?":
        "Grumpy is the most resistant to Snow White's presence, constantly complaining about having a woman in the house. His gradual softening toward Snow White provides one of the film's most satisfying character arcs. Despite his protests, he's the most visibly devastated when he believes Snow White has died.",

    "In Disney's Sleeping Beauty, what is the name of the prince who awakens Aurora?":
        "Prince Phillip was the first Disney prince to be given a proper name and personality, breaking the 'generic prince' mold of Snow White's and Cinderella's unnamed princes. He fights Maleficent in dragon form, making him Disney's first action-hero prince. He was named after Prince Philip, Duke of Edinburgh.",

    "In Ratatouille, what is the name of the junior chef who Remy controls?":
        "Alfredo Linguini is Gusteau's biological son who has zero cooking talent but becomes a puppet for Remy's culinary genius. Remy hides under Linguini's chef hat and controls his movements by pulling his hair. Lou Romano voiced him with perfect bumbling anxiety.",

    "In Monsters, Inc., what is the name of the CEO of Monsters, Inc.?":
        "Henry J. Waternoose III is a crab-like monster who runs the company and appears grandfatherly but is secretly willing to kidnap children to solve the energy crisis. James Coburn voiced him with smooth authority that masks his desperation. His 'I'll kidnap a thousand children' confession, caught on camera by Mike, leads to his downfall.",

    "In Up, what is the name of Carl's late wife?":
        "Ellie Fredricksen is shown only in the film's famous opening montage, but her presence drives Carl's entire journey. Their love story, from childhood meeting to her death, is told without dialogue and is considered one of cinema's most emotionally powerful sequences. Her Adventure Book, with the message 'Thanks for the adventure,' provides Carl's emotional resolution.",

    "In TaleSpin, what is the name of the young boy who works with Baloo?":
        "Kit Cloudkicker is a former air pirate who defected from Don Karnage's gang and became Baloo's navigator and surrogate son. His signature move is 'cloud surfing,' riding air currents on a small metal airfoil behind the Sea Duck. His backstory as a reformed child criminal gave TaleSpin surprising emotional depth.",

    "In Chip 'n Dale Rescue Rangers, what is the name of the tiny fly on the team?":
        "Zipper is a common housefly who serves as the Rescue Rangers' scout and is Monterey Jack's best friend. Despite being unable to speak English (only buzzing), the other team members understand him perfectly. His small size makes him invaluable for reconnaissance and getting into tight spaces.",

    "In Darkwing Duck, what is the name of the villain made entirely of water?":
        "Liquidator was once Bud Flood, a corrupt bottled water salesman who fell into a vat of contaminated water at his rival's plant. His water-based form makes him nearly impossible to physically harm. He speaks entirely in advertising jingles and sales pitches, parodying the advertising industry.",

    "In Goof Troop, who is Pete's best friend?":
        "Goofy is Pete's neighbor and unintentional best friend, despite Pete frequently trying to exploit their relationship. Their dynamic works because Goofy is genuinely oblivious to Pete's scheming, and Pete secretly values the friendship even when he won't admit it. This odd-couple dynamic drove the entire series.",

    "In DuckTales (1987), what is the name of the money-obsessed villain who guards an Aztec treasure?":
        "El Capitan is an immortal conquistador who has been guarding an Aztec treasure for centuries, driven mad by his obsession with gold. He appeared in the show's pilot movie 'Treasure of the Golden Suns.' His centuries of isolation left him unable to function in the modern world.",

    "In Disney's Robin Hood (1973), who voices the narrator rooster Alan-a-Dale?":
        "Roger Miller, the legendary country music singer known for 'King of the Road,' voiced and sang as Alan-a-Dale. His songs 'Whistle-Stop' and 'Oo-De-Lally' became beloved, with the hamster dance meme decades later being based on a sped-up version of 'Whistle-Stop.' Miller was already a crossover star, making his casting a perfect fit.",

    "In Disney's Snow White, what are the names of all seven dwarfs?":
        "Doc, Grumpy, Happy, Sleepy, Bashful, Sneezy, and Dopey were selected from a list of about 50 potential names during development. Rejected options included Jumpy, Deafy, Wheezy, and Baldy. Dopey was the last one finalized and became the most popular, despite never speaking a single word in the film.",

    "In Ben 10, what is the name of Ben's alien form that is a super-speedster?":
        "XLR8 (pronounced 'accelerate') is a Kineceleran from the planet Kinet who can run at speeds exceeding 500 mph. His design features a visor and wheel-like feet for maximum aerodynamics. The name is a clever play on the word 'accelerate,' fitting Ben's habit of giving his aliens punny names.",

    "In Disney's Pinocchio (1940), what is the name of the cat companion of Honest John?":
        "Gideon is Honest John's mute, dim-witted cat sidekick who communicates through pantomime and hiccups. He was originally scripted to have a speaking role, but Disney decided the silent treatment was funnier. His scenes parody classic silent film comedy duos.",

    "In Disney's Sleeping Beauty (1959), what does Maleficent curse the princess with?":
        "Maleficent's curse decrees that before sunset on Aurora's 16th birthday, she will prick her finger on the spindle of a spinning wheel and die. The specificity and inevitability of the curse is what makes it so terrifying. King Stefan's desperate response of burning every spinning wheel in the kingdom proves futile.",

    "In Disney's Peter Pan, what is Captain Hook's greatest fear?":
        "The ticking crocodile swallowed an alarm clock along with Hook's hand, so Hook can hear it approaching. This fear is both comical and symbolic: the ticking represents mortality and time catching up with someone who refuses to grow old. The crocodile patiently pursues Hook throughout the story.",

    "In Disney's Snow White, what are the names of the two most comedic dwarfs?":
        "Dopey (the youngest, mute, and most childlike) and Grumpy (the cantankerous curmudgeon) provide the most comedy through opposite approaches. Dopey's physical comedy and Grumpy's verbal complaints create a classic comic duo. Together they represent innocence and cynicism, both ultimately charmed by Snow White.",

    "In TaleSpin, what is the name of Baloo's mechanic friend?":
        "Wildcat is Higher for Hire's cheerful but absent-minded mechanic who can fix anything mechanical despite seeming completely scatterbrained. His mechanical genius contrasts hilariously with his inability to follow basic conversations. He's based on the character Flunkey from The Jungle Book.",

    "In Darkwing Duck, what is the name of the villain made of plant matter?":
        "Bushroot (Dr. Reginald Bushroot) was a timid botanist who experimented on himself to gain the ability to photosynthesize, accidentally becoming a plant-duck hybrid. He controls plants and often tries to create plant companions for himself out of loneliness. His tragic backstory makes him the most sympathetic member of the Fearsome Five.",

    "In Chip 'n Dale Rescue Rangers, what is the name of the scientist villain?":
        "Professor Norton Nimnul is a mad scientist whose outlandish inventions regularly threaten the city. He's unaware of the Rescue Rangers' existence, attributing their interference to bad luck or competing villains. His over-the-top inventions parody the mad scientist trope of 1950s B-movies.",

    "In Disney's Robin Hood (1973), what type of animal is the Sheriff of Nottingham?":
        "The Sheriff is a wolf, which perfectly captures his predatory, bullying nature as Prince John's chief tax collector and enforcer. The wolf symbolism underscores his role as a threat to the innocent townspeople (the 'sheep'). His gleeful cruelty when seizing taxes makes him one of the film's most hissable villains.",

    "In Disney's The Jungle Book (1967), what song does Baloo teach Mowgli?":
        "The Bare Necessities, performed by Phil Harris as Baloo, teaches Mowgli to relax and let life's simple pleasures sustain him. The song was nominated for the Academy Award for Best Original Song. Its carefree philosophy perfectly encapsulates Baloo's character and became one of Disney's most beloved songs.",

    "In Goof Troop, what kind of animal is PJ?":
        "PJ (Peter Pete Junior) is a dog, like all the Disney characters in the Goofy extended universe. He's Pete's overweight, insecure son who is Max's best friend. Unlike his scheming father, PJ is gentle and anxious, often caught between his father's demands and his friendship with Max.",

    "In Disney's Hercules, what is the name of the five Muses?":
        "Calliope (epic poetry), Clio (history), Melpomene (tragedy), Terpsichore (dance), and Thalia (comedy) narrate the film as a gospel choir. Only five of the nine original Greek Muses were included. Their names are historically accurate, though their gospel-singing roles are a creative invention.",

    "In Disney's The Princess and the Frog (2009), what is the name of Tiana's friend who is a prince?":
        "Prince Naveen of Maldonia is a charismatic but irresponsible prince who was cut off from his family's fortune and turned into a frog by Dr. Facilier. His journey from lazy charmer to responsible partner mirrors Tiana's learning to balance work with love. Bruno Campos voiced him with magnetic, playboy charm.",

    "In Disney's Brother Bear, what is the name of Kenai's youngest brother who befriends Koda?":
        "This is actually a trick question. Koda is not Kenai's brother; he's an orphaned bear cub Kenai meets after being transformed. Kenai's human brothers are Sitka (the eldest, who dies and becomes a spirit) and Denahi (the middle brother who hunts bear-Kenai). The question tests whether you confuse Koda's close bond with Kenai for actual kinship.",

    "In Disney's Sleeping Beauty, what are the three good fairies' colors?":
        "Flora wears pink/red, Fauna wears green, and Merryweather wears blue. Flora and Merryweather's constant bickering over whether Aurora's dress should be pink or blue provides a running gag that continues through the film's final frame. Their color-coded magic leaves telltale traces that help Maleficent's raven find Aurora.",

    "In Disney's Robin Hood, what is the name of the narrator rooster?":
        "Alan-a-Dale is a troubadour rooster who narrates the story and performs songs, voiced and sung by country legend Roger Miller. The minstrel Alan-a-Dale is a traditional character in Robin Hood legends. Using a rooster as the storytelling device gave the film a folksy, campfire-tale atmosphere.",

    "In Disney's Peter Pan, what island do the Lost Boys inhabit?":
        "Neverland is the magical realm where children never grow up, accessible by flying 'second star to the right and straight on till morning.' J.M. Barrie created it as a place that exists in every child's imagination. The island's geography conveniently contains every type of adventure setting a child could want.",

    "In Disney's Snow White, what are the names of the seven dwarfs in the classic song order?":
        "The dwarfs march home singing 'Heigh-Ho' in the order Doc, Grumpy, Happy, Sleepy, Bashful, Sneezy, and Dopey. This ordering has become the standard whenever they're listed. The 'Heigh-Ho' sequence was actually one of the first uses of multiplane camera technology in animation.",

    "In Monsters, Inc., what is the name of Sully's one-eyed best friend?":
        "Mike Wazowski is a one-eyed green sphere of a monster who works as Sully's assistant and best friend. Billy Crystal voiced him with rapid-fire wit and neurotic energy. His running gag of being obscured in photos and advertisements became a beloved meme decades later.",

    "In TaleSpin, what organization does Baloo's employer Higher for Hire belong to?":
        "Higher for Hire operates within Cape Suzette's air cargo industry, competing with other delivery services while navigating air pirates and rival businesses. The city's commerce-driven economy mirrors 1930s port cities. Rebecca Cunningham bought the struggling business and made it legitimate, much to freewheeling Baloo's chagrin.",

    "In Chip 'n Dale Rescue Rangers, what was the team's first major case?":
        "The Rescue Rangers formed when Chip and Dale helped a distraught mouse find her kidnapped husband, uncovering a cat crime ring led by Fat Cat. This inaugural case brought together all five team members (Chip, Dale, Gadget, Monterey Jack, and Zipper). The pilot movie established the team's formula of solving cases too small for human police.",

    "In Goof Troop, what type of car does Goofy drive?":
        "Goofy drives a beat-up old car that reflects his lovably ramshackle lifestyle, constantly breaking down at the worst moments. The car contrasts with Pete's flashier vehicles, mirroring their different approaches to life. Goofy's terrible driving, a trait from his classic cartoons, carries over into the series.",

    "In DuckTales (1987), what is the name of Scrooge's friendly competitor who is also a duck?":
        "Gladstone Gander is Scrooge's impossibly lucky nephew who never has to work because good fortune falls into his lap. His supernatural luck makes him a foil for Scrooge's 'earned every penny' philosophy. Carl Barks created him in 1948 to represent undeserved privilege versus hard work.",

    "In Darkwing Duck, what does Darkwing always say before appearing dramatically?":
        "The full introduction is 'I am the terror that flaps in the night,' followed by a different metaphor each time (e.g., 'I am the itch you cannot reach'). The ever-changing metaphor became one of the show's signature running gags. It parodies the dramatic introductions of classic pulp heroes like The Shadow.",

    "In The Powerpuff Girls, what substance gives the girls their powers in addition to sugar, spice, and everything nice?":
        "Chemical X was accidentally knocked into Professor Utonium's mixture by the mischievous lab monkey Jojo (later Mojo Jojo), creating both the Powerpuff Girls and their greatest enemy in the same incident. The substance's exact composition is never explained. 'Sugar, spice, and everything nice' comes from the classic nursery rhyme 'What Are Little Girls Made Of.'",

    "In Ben 10, what is the name of Ben's alien form that is made of living rock?":
        "Diamondhead is a Petrosapien from the planet Petropia whose body is made of extremely durable crystal (not technically rock). He can reshape his limbs into blades and projectiles, and he's nearly indestructible. His crystalline body also refracts energy beams, making him effective against laser-wielding enemies.",

    # ========== TIER 5 ==========
    "In the original DuckTales (1987), what is the name of the ancient sorcerer villain in the first multi-part episode?":
        "El Capitan is a centuries-old Spanish conquistador driven mad by his obsession with an Aztec treasure of gold. His immortality (or extreme longevity) keeps him alive purely through his greed for gold. He appeared in the five-part pilot 'Treasure of the Golden Suns,' setting the series' adventure tone.",

    "In TaleSpin, the character Shere Khan is a villain. What famous literary work is he originally from?":
        "Shere Khan comes from Rudyard Kipling's 'The Jungle Book,' published in 1894, where he's a Bengal tiger who claims the man-cub Mowgli as his rightful prey. TaleSpin reimagined him as a powerful, morally ambiguous business tycoon. Kipling based the stories on his childhood in British India.",

    "In Darkwing Duck, what is the name of the secret intelligence agency Darkwing works with?":
        "S.H.U.S.H. is a spy agency led by Director J. Gander Hooter, parodying real-world intelligence agencies and their fictional counterparts. Their rivalry with F.O.W.L. mirrors the classic spy-vs-spy dynamic of Cold War fiction. The name is a 'shush' pun, since intelligence agencies deal in secrets.",

    "In the original DuckTales (1987), what is the name of Gyro Gearloose's little helper robot?":
        "Little Helper (also called Little Bulb) is a tiny robot with a lightbulb for a head that assists Gyro in his lab. Created by Carl Barks in the comics, he's one of the smallest recurring characters in the Disney Duck universe. Despite his size, he often proves crucial to solving problems.",

    "In Goof Troop, what is the name of Pete's wife?":
        "Peg Pete is Pete's no-nonsense wife who keeps him somewhat in check with her assertive personality. She's one of the few characters who can make Pete back down from his schemes. She works as a real estate agent and doesn't appear in A Goofy Movie, where Pete is seemingly single.",

    "In Ben 10, what is the home planet of Ben's alien form Heatblast?":
        "Pyros is a star-like celestial body that serves as the homeworld of the Pyronites, beings made of living magma. The planet's surface is constantly erupting and shifting, with temperatures reaching solar levels. In Ben 10 lore, Pyronites are actually quite intelligent and peaceful despite their destructive appearance.",

    "In Disney's Snow White, what is the name of the dwarf who sneezes constantly?":
        "Sneezy suffers from uncontrollable, incredibly powerful sneezing fits that are strong enough to blow objects across the room. The other dwarfs have to hold his nose shut during critical moments to prevent him from giving away their location. His sneezing was used for visual comedy that pushed the boundaries of 1930s animation.",

    "In Disney's Pinocchio, what is the name of the island where boys are turned into donkeys?":
        "Pleasure Island lures boys with unlimited candy, games, and mischief, then transforms them into donkeys to be sold to salt mines and circuses. It's one of the darkest sequences in any Disney film, serving as a heavy allegory about the consequences of abandoning education and morality. The Coachman who runs it is arguably Disney's most purely evil villain.",

    "In Disney's Sleeping Beauty, what are the colors associated with Flora, Fauna, and Merryweather?":
        "Flora is associated with red/pink, Fauna with green, and Merryweather with blue. Their debate over Aurora's dress color (pink vs. blue) is a running gag that appears in the film's final frame. In the film's climax, their color-coded magic accidentally creates a trail of sparks that reveals Aurora's location to Maleficent.",

    "In Disney's Cinderella, what are the names of Cinderella's two main mouse friends?":
        "Jaq (Jacques) and Gus (Gus-Gus/Octavius) are Cinderella's most loyal allies among the mice and birds that share her attic room. Jaq is clever and brave while Gus is lovably bumbling and food-obsessed. They risk their lives to steal the key from Lady Tremaine's pocket to free Cinderella.",

    "In Disney's Peter Pan, what is the name of the tribe princess who befriends Peter Pan?":
        "Tiger Lily is the daughter of the Chief and is captured by Captain Hook as bait for Peter Pan. Peter rescues her, earning the tribe's respect. The portrayal of Tiger Lily and her people is one of the most culturally criticized aspects of the 1953 film by modern standards.",

    "In Ratatouille, what is the name of the fearsome food critic who visits Gusteau's restaurant?":
        "Anton Ego is a skeletal, coffin-shaped food critic whose devastating review contributed to Gusteau's death. His climactic taste of ratatouille triggers a Proustian flashback to his mother's home cooking, transforming his worldview. Peter O'Toole's voice performance captured both his intimidating exterior and hidden vulnerability.",

    "In Up, what was the name of the famous explorer Carl and Ellie idolized as children?":
        "Charles Muntz was a renowned explorer who was discredited when scientists doubted his discovery of a giant bird skeleton. He's spent decades in South America trying to capture a live specimen to clear his name, going mad in the process. Christopher Plummer voiced him as a charming man corrupted by obsession.",

    "In Monsters, Inc., what is the name of the villain monster with a lizard-like appearance?":
        "Randall Boggs is a chameleon-like monster who can turn invisible, and he's Sully's bitter rival as a Scarer. He's secretly building a scream-extraction machine for Waternoose that would forcibly extract screams from kidnapped children. Steve Buscemi voiced him with perfect slithery menace.",

    "In Disney's The Emperor's New Groove, what is the name of Yzma's muscular assistant?":
        "Kronk is Yzma's dim but loveable henchman whose shoulder angel and devil provide the film's most iconic comedy scenes. Patrick Warburton's deadpan delivery made Kronk so popular he got his own sequel (Kronk's New Groove). He's actually a talented chef and speaks fluent squirrel.",

    "In Disney's Brother Bear, what is the name of Kenai's oldest brother who becomes a spirit?":
        "Sitka sacrifices himself to save his brothers from a bear attack at the film's beginning, and his spirit later transforms Kenai into a bear to teach him empathy. He appears throughout the film as an eagle spirit watching over his brothers. His sacrifice establishes the film's themes of love and understanding.",

    "In Disney's The Princess and the Frog, what instrument does Louis the alligator play?":
        "Louis plays the trumpet and dreams of performing jazz with human musicians in New Orleans, despite being a terrifying alligator. His jazz performances are among the film's most energetic musical moments. He represents the film's message that dreams can come from anywhere, even the bayou.",

    "In Toy Story 2, who is the prospector toy villain who wants to go to a museum?":
        "Stinky Pete the Prospector, voiced by Kelsey Grammer, has spent his entire existence mint-in-box and wants to be preserved in a Tokyo museum rather than risk the heartbreak of being played with and eventually discarded. His fear of abandonment is tragically relatable, even though his methods are villainous.",

    "In Disney's Tangled, what is the name of the bar where the thugs have dreams?":
        "The Snuggly Duckling is a tavern filled with intimidating thugs who, during the song 'I've Got a Dream,' reveal surprisingly gentle aspirations like becoming a concert pianist, collecting ceramic unicorns, and performing mime. This scene established Tangled's irreverent humor and its theme that everyone deserves to pursue their dreams.",

    "In Darkwing Duck, what is the name of the toy-themed villain who uses giant toys as weapons?":
        "Quackerjack is a deranged former toy maker who uses weaponized toys like explosive teddy bears, killer dolls, and banana-peel grenades. He was driven insane when video games replaced traditional toys, making his business obsolete. His jester appearance and maniacal laughter make him one of Darkwing's most unhinged foes.",

    "In TaleSpin, what is the name of Kit Cloudkicker's signature move on his airfoil?":
        "Cloud surfing involves Kit riding a crescent-shaped metal airfoil while being towed behind the Sea Duck, catching air currents to perform aerial maneuvers. It's essentially wakeboarding in the sky. Kit learned the technique during his time with Don Karnage's air pirates before going straight.",

    "In Disney's Pinocchio, who is Pinocchio's insect conscience?":
        "Jiminy Cricket was appointed Pinocchio's official conscience by the Blue Fairy, tasked with guiding the wooden boy toward being 'brave, truthful, and unselfish.' Cliff Edwards voiced him with a cheerful, everyman charm. His song 'When You Wish Upon a Star' became Disney's corporate anthem and one of the most famous songs in film history.",

    "In Disney's Snow White, what is the name of the magic mirror?":
        "The Magic Mirror (sometimes called the Slave in the Magic Mirror) tells the Evil Queen that Snow White has surpassed her as the fairest in the land, triggering the entire plot. The mirror always tells the truth, which is what makes it so dangerous. Its face trapped in glass is one of Disney's most haunting images.",

    "In Disney's Peter Pan, what is the name of Captain Hook's first mate?":
        "Mr. Smee is Hook's bumbling, good-natured first mate who is somehow loyal despite Hook's constant abuse. He's the comic relief to Hook's menace, frequently getting things wrong in ways that accidentally help the heroes. In Barrie's original work, Smee is described as 'pathetically stupid.'",

    "In Cars, what is the number on Lightning McQueen's race car?":
        "Lightning McQueen's number 95 is a tribute to 1995, the year Pixar released Toy Story, their first feature film. This Easter egg connects McQueen to Pixar's own origin story. His sponsor 'Rust-eze' bumper ointment is a deliberate contrast to the flashy sponsors real racing stars typically have.",

    "In Ratatouille, what is Gusteau's famous motto?":
        "Auguste Gusteau's philosophy that 'Anyone can cook' doesn't mean everyone is a great chef, but that a great chef can come from anywhere. This motto inspires Remy and is ultimately validated when a rat produces a dish that moves the world's harshest food critic. It's also Brad Bird's metaphor for creativity in filmmaking.",

    "In Monsters, Inc., what is the name of the CDA agent who watches over the floor?":
        "Roz is the dour, slug-like administrator who constantly nags Mike about his paperwork. The twist reveals she's actually an undercover agent for the Child Detection Agency (CDA), and she's been investigating Waternoose's scheme all along. Her monotone 'I'm watching you, Wazowski' became one of the film's most quoted lines.",

    "In Ben 10, what is the name of the alien plumber organization Ben's grandfather Max belongs to?":
        "The Plumbers are a secret intergalactic law enforcement agency whose Earth name is deliberately mundane to avoid suspicion. Max Tennyson was a legendary Plumber agent before retirement. The organization deals with alien threats while maintaining the secret of extraterrestrial life from the general public.",

    "In Disney's Lilo and Stitch, what is the name of the alien agent initially pursuing Stitch?":
        "Captain Gantu is a massive, whale-like alien military officer tasked with recapturing Experiment 626. Despite his imposing appearance, he's frequently outsmarted by Stitch and Lilo. Kevin Michael Richardson's deep voice gave Gantu an intimidating presence that made his failures even funnier.",

    "In Johnny Bravo, who is Johnny Bravo's mother?":
        "Mama Bravo (Bunny Bravo) is Johnny's loving, somewhat overbearing mother who somehow raised him despite his complete lack of self-awareness. She often serves as the voice of reason, though Johnny never listens. Her character adds heart to a show that could otherwise be purely absurdist.",

    "In Disney's Tangled, what magical property does Rapunzel's hair have?":
        "Rapunzel's 70 feet of golden hair can heal injuries, cure illness, and restore youth when she sings the incantation flower song. This power comes from a magical golden flower that was used to save her mother during pregnancy. If the hair is cut, it turns brown and loses its power, which is why Gothel kept it intact.",

    "In Disney's Hercules, what is the name of Hercules' flying horse?":
        "Pegasus was created by Zeus from clouds as a gift for baby Hercules. In the film, he's fiercely loyal and somewhat jealous of Meg's relationship with Herc. In actual Greek mythology, Pegasus was born from the blood of Medusa when Perseus beheaded her, a very different origin story.",

    "In Disney's Brother Bear, what is the name of the shaman elder woman who gives Kenai his totem?":
        "Tanana is the village shaman who gives each young person their spirit totem, determining their path in life. She gives Kenai the Bear of Love, which he initially rejects. Her role represents the wisdom of Indigenous spiritual traditions that the film tries to honor.",

    "In DuckTales (1987), what is the name of the ancient sorcerer who can transform into animals?":
        "Merlock is a powerful sorcerer who appeared in the DuckTales movie 'Treasure of the Lost Lamp,' possessing a magic talisman that amplifies a genie's power. He can transform into various animals, with a griffin being his preferred flight form. His centuries of life have been sustained through the talisman's magic.",

    "In TaleSpin, what is the name of the bar and cafe where Baloo hangs out?":
        "Louie's Place is a tropical island bar and restaurant run by the orangutan Louie (King Louie from The Jungle Book, reimagined as a nightclub owner). It serves as a neutral territory where pilots, pirates, and travelers all mingle. The jazz-and-swing atmosphere echoes Louie's original 'I Wan'na Be Like You' musical personality.",

    "In Darkwing Duck, what are the initials of the villain organization F.O.W.L.?":
        "Fiendish Organization for World Larceny is a criminal syndicate that serves as the primary intelligence threat in the show's universe, opposing the spy agency S.H.U.S.H. The name is a triple pun: it's an acronym, a description of their nature (fowl/foul), and a bird reference fitting the duck universe. Their agents include some of Darkwing's most dangerous foes.",

    "In Chip 'n Dale Rescue Rangers, what does Gadget Hackwrench specialize in?":
        "Gadget builds incredible machines, vehicles, and gadgets from everyday junk and household items, making her the team's engineer, inventor, and pilot. She can build a functioning airplane from a rubber band, a soda can, and a paper clip. Her engineering genius combined with her sweet, slightly oblivious personality made her a groundbreaking female character in kids' TV.",

    "In DuckTales (1987), what is the special quality of Scrooge's Number One Dime?":
        "Scrooge's Number One Dime is the very first coin he ever earned, given to him as payment for shining a ditchdigger's boots in Glasgow, Scotland. He considers it the foundation of his entire fortune and guards it obsessively. Multiple villains, especially Magica De Spell, believe it contains the magical 'essence' of his success.",

    "In Disney's Robin Hood (1973), what is the name of the snake who serves Prince John?":
        "Sir Hiss is a snake who serves as Prince John's advisor, having originally hypnotized King Richard into going on the Crusades. His name is both a description of his sibilant speech and a pun on 'Sir.' Terry-Thomas voiced him with perfect obsequious sycophancy.",

    "In Disney's Pinocchio, what is the name of Geppetto's cat?":
        "Figaro is Geppetto's tuxedo kitten who became so popular that Walt Disney made him Minnie Mouse's cat in later cartoons. His annoyed reactions to Pinocchio's antics provide subtle comedy. Figaro was reportedly Walt Disney's personal favorite character from the film.",

    "In Disney's Snow White, what is the evil queen's unofficial name?":
        "Grimhilde is the name given to the Evil Queen in some Disney merchandise and publications, though it's never spoken in the 1937 film. The name likely derives from Germanic mythology. She was Disney's first animated villain and set the template for decades of memorable Disney antagonists.",

    "In Disney's Peter Pan, what literary work by J.M. Barrie is it based on?":
        "Disney's film is primarily based on Barrie's 1911 novel 'Peter and Wendy,' though Peter Pan first appeared in Barrie's 1904 play 'Peter Pan, or the Boy Who Wouldn't Grow Up.' Barrie gifted the rights to Great Ormond Street Hospital, which still receives royalties. Peter Pan also briefly appeared in Barrie's 1902 novel 'The Little White Bird.'",

    "In Disney's Cinderella, what is the name of the wicked stepmother?":
        "Lady Tremaine is one of Disney's most psychologically realistic villains, using emotional manipulation and cruelty without any magical powers. She was voiced by Eleanor Audley, who also voiced Maleficent. Her subtle, cold cruelty has made her one of the most studied villains in animation history.",

    "In Cars, what is the name of the race car rival who cheats to win?":
        "Chick Hicks (number 86) is a dirty racer who has always finished behind veteran champion Strip 'The King' Weathers. His desperation to win leads him to deliberately wreck The King in the final race. Michael Keaton voiced him as the perfect petty, win-at-all-costs antagonist.",

    "In Ratatouille, what is the name of the French chef who inspires Remy?":
        "Auguste Gusteau was Paris's most famous chef whose restaurant held five stars before food critic Anton Ego's harsh review cost it one star. Gusteau died shortly after, reportedly of a broken heart. His ghost appears to Remy as a manifestation of his culinary imagination and conscience.",

    "In Up, what is the name of the wilderness explorer troop Russell belongs to?":
        "The Wilderness Explorers are a boy-scout-like organization, and Russell needs his 'Assisting the Elderly' badge to become a Senior Wilderness Explorer. His earnest, chattering presence slowly breaks through Carl's grumpy shell. The badge ceremony at the end, where Carl pins Russell's badge, is a touching surrogate grandfather moment.",

    "In Disney's The Emperor's New Groove, what potion does Yzma accidentally use on Kuzco?":
        "Yzma meant to use poison but grabbed the wrong vial from her extensive potion collection, turning Kuzco into a llama instead of killing him. This mistake drives the entire plot. The scene where she and Kronk realize the mixup ('I'll turn him into a flea... or I'll put that flea in a box') is comedy gold.",

    "In Toy Story 2, what is the name of the TV show that all the Woody's Roundup toys come from?":
        "Woody's Roundup was a fictional 1950s puppet show (mirroring real shows like Howdy Doody) that made Woody, Jessie, Bullseye, and Stinky Pete valuable collector's items. The black-and-white show footage within the film was created using real puppets. The show was cancelled after the launch of Sputnik shifted children's interests to space.",

    "In Disney's Lilo and Stitch, who created Experiment 626?":
        "Dr. Jumba Jookiba is a self-described 'evil genius' who created 626 illegal genetic experiments, with Stitch (626) being his masterpiece. He was arrested by the Galactic Federation for his experiments but escapes to pursue Stitch on Earth. Despite being labeled evil, he's actually a bumbling, loveable scientist.",

    "In Disney's The Princess and the Frog, what does Dr. Facilier use to make deals with people?":
        "Dr. Facilier uses voodoo magic, tarot cards, and deals with powerful shadow spirits called 'Friends on the Other Side.' The shadow demons do the heavy lifting of his magic, and they demand payment in human souls. When Facilier fails to deliver, his 'friends' literally drag him into their dimension.",

    "In Disney's Hercules, what are the names of the three Fates?":
        "Clotho (who spins the thread of life), Lachesis (who measures it), and Atropos (who cuts it) share a single eye between them in the Disney version. In Greek mythology, these three sisters (the Moirai) control the destiny of every mortal and even the gods fear their power. Their scene with Hades is one of the film's funniest.",

    "In Disney's Brother Bear, what totem is Kenai assigned?":
        "The Bear of Love seems like the cruelest joke possible to Kenai, who blames a bear for his brother Sitka's death. His entire arc is about learning what the totem truly means by literally walking in a bear's paws. By the end, he chooses to remain a bear, embracing the love his totem represents.",

    "In Goof Troop, what is the full name of Pete's son PJ?":
        "Peter Pete Junior is often called PJ, a shy, overweight teenager who suffers under his overbearing father Pete. His friendship with Max Goof is the emotional heart of both Goof Troop and A Goofy Movie. PJ's anxiety and low self-esteem, caused by Pete's bullying, are portrayed with surprising sensitivity.",

    "In Ben 10, what is the name of Ben's alien form that is a tiny super-intelligent grey alien?":
        "Grey Matter is a five-inch-tall Galvan, the smartest species in the Ben 10 universe, who built the Omnitrix itself. When Ben transforms into Grey Matter, he gains genius-level intellect but loses all physical power. This alien teaches that intelligence can solve problems brute force cannot.",

    "In Disney's Sleeping Beauty (1959), where does Maleficent trap Prince Phillip?":
        "Maleficent imprisons Phillip in her dungeon at the Forbidden Mountain, chaining him and taunting him with visions of Aurora's sleeping form. She plans to release him only when he's an old man, too late for love to break the spell. The three good fairies rescue him and arm him with the Sword of Truth and Shield of Virtue.",

    "In Disney's Pinocchio (1940), what is the name of the Coachman who takes boys to Pleasure Island?":
        "The Coachman is a portly, sinister man who lures 'stupid little boys' to Pleasure Island where they're transformed into donkeys and sold into slavery. Unlike the other villains, he's never defeated or punished in the film, making him uniquely terrifying. His grinning face during the 'They never come back... as BOYS!' scene is nightmare fuel.",

    "In Disney's Robin Hood (1973), how does Robin Hood disguise himself at the archery tournament?":
        "Robin Hood enters Prince John's archery tournament disguised as a stork, despite being a fox, to win the golden arrow prize and impress Maid Marian. His disguise fools everyone except Marian, who recognizes him by his skill. Prince John suspects the stork is Robin Hood and uses the tournament as a trap.",

    "In Disney's The Jungle Book (1967), what human settlement does Mowgli choose at the end?":
        "Mowgli is finally drawn to the human village when he sees a girl his age fetching water. After spending the entire film resisting leaving the jungle, he follows her into the village without a backward glance. The song 'My Own Home' plays as he makes the choice that Baloo and Bagheera couldn't force him to make.",

    "In Disney's Mulan (1998), what is the name of the lucky cricket given to Mulan?":
        "Cri-Kee is presented by Grandmother Fa as a lucky cricket, but his presence actually causes a chain of disasters starting with the disastrous matchmaker visit. The irony of an 'unlucky lucky cricket' is a running joke throughout the film. Cricket-keeping for luck is an authentic Chinese cultural tradition dating back thousands of years.",

    "In DuckTales (1987), what is the name of Fenton Crackshell's alter ego?":
        "Gizmoduck is Duckburg's armored superhero, created when accountant Fenton Crackshell accidentally activated Gyro Gearloose's mechanical suit by saying 'blathering blatherskite.' The suit grants superhuman strength, flight, and an arsenal of gadgets. Fenton's dual identity as bumbling bean counter and heroic Gizmoduck parodies Superman/Clark Kent.",

    "In Darkwing Duck, what is the name of Darkwing's daughter Gosalyn's best friend?":
        "Honker Muddlefoot is the bespectacled, nerdy son of the Muddlefoot family who live next door to Drake Mallard. He knows Darkwing Duck's secret identity and helps on cases with his intelligence. His timid personality contrasts perfectly with Gosalyn's recklessness.",

    "In TaleSpin, what is the name of Baloo's young navigator protege?":
        "Kit Cloudkicker ran away from Don Karnage's air pirates and became Baloo's navigator and surrogate son at Higher for Hire. His past as a child pirate gives him skills beyond his years, and his redemption arc adds emotional depth to the show. He's one of the few Disney characters with a genuinely troubled backstory.",

    "In Chip 'n Dale Rescue Rangers, what is the name of the Australian mouse who loves cheese?":
        "Monterey Jack is a globe-trotting Australian mouse whose Achilles heel is cheese: the mere scent sends him into an uncontrollable frenzy called a 'cheese attack.' His adventurous past provides backstory and connections that help the Rangers on cases. His accent and tough-guy personality belie a soft heart.",

    # ========== HARRY POTTER ==========
    "What spell is used to disarm an opponent in Harry Potter?":
        "Expelliarmus became Harry Potter's signature spell, which he used so frequently that Death Eaters identified him by it during the Battle of the Seven Potters. It causes the target's wand to fly out of their hand. This spell ultimately defeats Voldemort when Harry's Expelliarmus overpowers Voldemort's Killing Curse.",

    "What are the four Hogwarts houses?":
        "Each house was founded by one of the four greatest witches and wizards of the age: Godric Gryffindor (bravery), Salazar Slytherin (ambition), Helga Hufflepuff (loyalty), and Rowena Ravenclaw (wisdom). The founders' increasingly bitter disagreements, especially Slytherin's insistence on blood purity, eventually led to Slytherin's departure. The Sorting Hat was created to continue sorting students after the founders were gone.",

    "What is the killing curse in Harry Potter?":
        "Avada Kedavra is one of the three Unforgivable Curses, instantly killing its target with a flash of green light. There is no known magical defense against it except physical dodging, sacrificial love protection, or the unique circumstances of Harry's wand connection to Voldemort. The incantation likely derives from the Aramaic phrase 'avra kedabra' meaning 'I will create as I speak.'",

    "What animal form does Hermione's Patronus take?":
        "Hermione's otter Patronus is fitting because otters are known for their intelligence and playfulness. J.K. Rowling has said the otter is her own favorite animal. Ron's Patronus is a Jack Russell terrier, which are known for chasing otters, a subtle hint at their romantic connection.",

    "How many Horcruxes does Voldemort create in total (including the unintentional one)?":
        "Voldemort intentionally created six Horcruxes (diary, ring, locket, cup, diadem, Nagini), plus Harry himself became an unintentional seventh when the Killing Curse backfired. He chose the number seven because it's the most powerfully magical number. Splitting his soul so many times is why he became increasingly inhuman.",

    "What is Voldemort's real name?":
        "Tom Marvolo Riddle was born to a witch mother (Merope Gaunt) who died in childbirth and a Muggle father (Tom Riddle Sr.) who abandoned them. He rearranged the letters of his birth name into 'I am Lord Voldemort.' He grew up in a Muggle orphanage, which partly fueled his hatred of non-magical people.",

    "What position does Harry play on the Gryffindor Quidditch team?":
        "Harry became the youngest Seeker in a century when Professor McGonagall spotted his natural flying ability during his first broomstick lesson. The Seeker's job is to catch the Golden Snitch, worth 150 points and ending the game. Harry's talent was inherited from his father James, who was also a gifted Quidditch player.",

    "What is the name of Harry's owl?":
        "Hedwig was a snowy owl purchased from Eeylops Owl Emporium by Hagrid as Harry's 11th birthday present. She was named after a saint Harry found in 'A History of Magic.' Her death by a stray Killing Curse during the escape from Privet Drive marked the definitive end of Harry's childhood.",

    "What is the spell that makes things levitate?":
        "Wingardium Leviosa is the first spell Hogwarts students learn to perform, and Hermione's correction of Ron's pronunciation ('It's Levi-OH-sa, not Levio-SAH') is one of the series' most quoted moments. The spell combines 'wing' (English), 'arduus' (Latin for 'high'), and 'levo' (Latin for 'to raise'). Ron later uses it to knock out a mountain troll, saving Hermione.",

    "What is the incantation to produce a Patronus charm?":
        "Expecto Patronum conjures a silvery guardian made from the caster's happiest memories, used primarily to repel Dementors. Harry's Patronus takes the form of a stag, matching his father's Animagus form. The spell is so advanced that most adult wizards can't produce a corporeal Patronus, making Harry's mastery at 13 remarkable.",

    "Which Hogwarts professor is secretly a werewolf?":
        "Remus Lupin's name itself is a double clue: 'Remus' references the Roman boy raised by wolves, and 'Lupin' derives from 'lupus' (Latin for wolf). He was bitten as a child by Fenrir Greyback and struggled with prejudice his entire life. Dumbledore was the only headmaster willing to accommodate a werewolf student.",

    "What is the name of Harry's godfather?":
        "Sirius Black spent 12 years in Azkaban for murders he didn't commit, framed by the true traitor Peter Pettigrew. As an Animagus who can transform into a large black dog, he escaped Azkaban by slipping through the bars in dog form. His name references the 'Dog Star' Sirius, the brightest star in the constellation Canis Major.",

    "Which Deathly Hallow is described as the most powerful wand ever made?":
        "The Elder Wand passes from master to master through defeat, creating a bloody trail throughout wizarding history. Dumbledore won it from Grindelwald, then Draco inadvertently became its master by disarming Dumbledore, and Harry claimed its allegiance by disarming Draco. Its power is real but its curse is that it attracts violence.",

    "What is the name of the wizarding bank in the Harry Potter world?":
        "Gringotts is run entirely by goblins and features underground vaults protected by dragons, curses, and magical security measures. The deeper the vault, the more security it has, with the oldest families' vaults deep underground. Harry, Ron, and Hermione break into Gringotts in Deathly Hallows, something that had never been accomplished before.",

    "What is the name of Draco Malfoy's father?":
        "Lucius Malfoy is a wealthy pure-blood supremacist who served Voldemort as a Death Eater while maintaining respectable appearances at the Ministry of Magic. He secretly slipped Tom Riddle's diary to Ginny Weasley, setting the events of Chamber of Secrets in motion. Jason Isaacs' film portrayal with the iconic platinum wig became definitive.",

    "What magical creature did Hagrid hatch and name Norbert?":
        "Norbert is a Norwegian Ridgeback dragon that Hagrid won as an egg in a card game (actually a setup by Quirrell to learn how to get past Fluffy). Dragons are illegal to keep as pets in the wizarding world. Norbert was later revealed to be female and renamed Norberta.",

    "What is the name of the Gryffindor house ghost?":
        "Nearly Headless Nick (Sir Nicholas de Mimsy-Porpington) was improperly executed in 1492 when the axe man's blade was dull, leaving his head attached by half an inch of skin. This technicality prevents him from joining the Headless Hunt, a source of eternal frustration. His 500th Deathday Party is a memorable scene in Chamber of Secrets.",

    "What does the spell Accio do?":
        "Accio is a summoning charm that magically pulls an object to the caster from any distance. Harry famously used it to summon his Firebolt broomstick during the first task of the Triwizard Tournament to escape a dragon. The name comes from the Latin 'accio' meaning 'I summon.'",

    "Who kills Dumbledore in Harry Potter and the Half-Blood Prince?":
        "Severus Snape killed Dumbledore with the Killing Curse atop the Astronomy Tower, but it was secretly arranged between them beforehand. Dumbledore was already dying from a cursed Horcrux ring and wanted Snape to be the one to end it, both to spare Draco from becoming a killer and to solidify Snape's position as a trusted Death Eater spy.",

    "What is the name of Ron's pet rat that is secretly Peter Pettigrew?":
        "Scabbers had been the Weasley family rat for 12 years, an unusually long life for a common rat. He was actually Peter Pettigrew in Animagus form, hiding after faking his death and framing Sirius Black for murder. His exposure by Remus Lupin and Sirius in the Shrieking Shack is one of the series' biggest reveals.",

    "What position does Ron Weasley play in Quidditch?":
        "Ron plays Keeper for the Gryffindor team, but his performance is severely affected by his confidence level. The song 'Weasley is Our King' was created by Slytherins to mock him but was later reclaimed by Gryffindor supporters after his heroic performances. His confidence issues mirror his broader struggle with feeling overshadowed.",

    "What is the spell that creates light from the tip of a wand?":
        "Lumos derives from the Latin 'lumen' meaning 'light,' and it's one of the simplest and most practical spells in the wizarding world. Its counter-spell is 'Nox' (Latin for 'night'). Google even programmed 'OK Google, Lumos' to turn on phone flashlights as an Easter egg.",

    "What is the pub that serves as the entrance to Diagon Alley?":
        "The Leaky Cauldron is a dingy pub on Charing Cross Road in London that Muggles can't see due to enchantments. Its back wall opens into Diagon Alley when the correct bricks are tapped. The pub was founded in the early 1500s and has served as the gateway to the wizarding shopping district ever since.",

    "What are Snape's last words to Harry before dying?":
        "Snape's dying request 'Look at me' was so he could see Harry's green eyes one last time, because Harry has his mother Lily's eyes. Snape's entire life was motivated by his love for Lily Potter, and his 'Always' response to Dumbledore about whether he still loved her is the series' most poignant word.",

    "What does Neville Longbottom destroy in the Battle of Hogwarts?":
        "Neville beheads Nagini with the Sword of Gryffindor, destroying Voldemort's final Horcrux and making him mortal. This moment was Neville's ultimate vindication: the boy who could have been the Chosen One (the prophecy fit him too) proves himself a true Gryffindor hero. He pulled the sword from the Sorting Hat, just as Harry did in Chamber of Secrets.",

    "What Hogwarts house does Cedric Diggory belong to?":
        "Cedric Diggory was a proud Hufflepuff and the Triwizard Tournament co-champion who proved that Hufflepuff produces heroes too. His murder by Peter Pettigrew on Voldemort's orders ('Kill the spare') was the first death Harry witnessed. Robert Pattinson played him in the films before becoming Batman and Edward Cullen.",

    # ========== STAR WARS ==========
    "What is the name of Han Solo's ship?":
        "The Millennium Falcon is a modified Corellian YT-1300 light freighter that Han Solo won from Lando Calrissian in a game of sabacc. It made the Kessel Run in less than 12 parsecs (a measurement of distance, not time, indicating the shortcut Han took). Its design was inspired by a hamburger with an olive on the side.",

    "Who says the famous line 'I am your father' in The Empire Strikes Back?":
        "Darth Vader's revelation to Luke is cinema's most famous twist. During filming, the script read 'Obi-Wan killed your father' to prevent leaks, and only Mark Hamill was told the real line moments before shooting. David Prowse (in the suit) delivered the fake line while James Earl Jones recorded the real one later.",

    "What planet is Luke Skywalker from?":
        "Tatooine is a desert planet with twin suns orbiting in the Outer Rim. It was filmed in Tunisia, and the name comes from the real Tunisian city of Tataouine. Luke was hidden there by Obi-Wan because it was the last place Vader would look, having hated the planet since childhood.",

    "What is the name of the Wookiee co-pilot of the Millennium Falcon?":
        "Chewbacca is a 200-year-old Wookiee from the planet Kashyyyk who owes Han Solo a life debt. His appearance was inspired by George Lucas's dog Indiana (who also inspired Indiana Jones's name). Peter Mayhew played Chewie in the original trilogy, standing 7'3\" tall.",

    "Which planet is destroyed by the Death Star in A New Hope?":
        "Alderaan was a peaceful, weapon-free planet and Princess Leia's adopted homeworld. Grand Moff Tarkin ordered its destruction specifically to demonstrate the Death Star's power and break Leia's will. The destruction of an entire peaceful civilization in seconds established the Empire as genuinely evil.",

    "What color is Luke Skywalker's lightsaber in Return of the Jedi?":
        "Luke's green lightsaber was actually changed from blue during post-production because the blue blade was hard to see against the bright sky of Tatooine in the Sarlacc pit scene. This happy accident created the idea that lightsaber colors have meaning. Luke built this saber himself, a Jedi rite of passage.",

    "Who was Anakin Skywalker's Jedi master?":
        "Obi-Wan Kenobi trained Anakin from boyhood to knighthood, inheriting the task when his own master Qui-Gon Jinn died in The Phantom Menace. Obi-Wan's failure to prevent Anakin's fall to the dark side haunted him for the rest of his life. Their relationship is the emotional core of the prequel trilogy.",

    "What species is Yoda?":
        "After nearly 50 years and hundreds of Star Wars stories, Yoda's species has never been named. George Lucas deliberately kept it a mystery, and Lucasfilm continues to enforce this rule. Only three members of his species have ever appeared in canon: Yoda, Yaddle, and Grogu (Baby Yoda from The Mandalorian).",

    "What is the Sith Rule of Two?":
        "The Rule of Two was established by Darth Bane approximately 1,000 years before the films, after the Sith destroyed themselves through infighting. One master holds the power, one apprentice craves it, ensuring the Sith grow stronger with each generation. Palpatine's scheme to replace Dooku with Anakin is a textbook application of this rule.",

    "Who trained Darth Maul?":
        "Darth Sidious (Palpatine) took Maul from his Nightsister mother on Dathomir and trained him from childhood as a weapon of pure hatred. Maul was meant to be expendable, a tool to draw out the Jedi while Sidious worked in the shadows. The Clone Wars animated series later gave Maul a much richer characterization.",

    "What type of fighter does Luke fly in the Battle of Yavin?":
        "The T-65B X-Wing Starfighter is the Rebel Alliance's primary space superiority fighter, named for its distinctive S-foil configuration that forms an X shape when in attack position. Luke flew Red Five in the original Death Star trench run. The X-Wing's design was inspired by the dart shape of a crossbow bolt.",

    "What is the name of the battle station the Empire builds in A New Hope?":
        "The Death Star is a moon-sized space station with a superlaser capable of destroying entire planets. Its design originated from Geonosian blueprints, and its construction took nearly 20 years. Its thermal exhaust port weakness, exploited by Luke, became one of fiction's most famous design flaws.",

    "In which film does Han Solo get frozen in carbonite?":
        "Han Solo is frozen in carbonite at Cloud City in The Empire Strikes Back, delivered to Boba Fett as payment for Jabba the Hutt's bounty. The carbonite freezing was partly a practical solution: Harrison Ford hadn't committed to a third film yet. The 'I love you' / 'I know' exchange before the freezing was improvised by Ford.",

    "What order does Palpatine issue to have all Jedi killed by clone troopers?":
        "Order 66 was a secret command embedded in the clone troopers' behavioral programming that compelled them to turn on their Jedi commanders. Nearly all Jedi across the galaxy were killed simultaneously by soldiers they trusted. The scene in Revenge of the Sith showing multiple Jedi betrayals is one of the saga's most devastating sequences.",

    "What is the name of the swampy planet where Yoda lives in exile?":
        "Dagobah is a remote, swamp-covered planet strong in the Force where Yoda hid after the fall of the Jedi Order. Its dense life readings helped mask Yoda's powerful Force presence from the Empire. Luke trained there with Yoda, learning that the Force is about more than physical power.",

    "What is the name of the bounty hunter who captures Han Solo?":
        "Boba Fett became one of Star Wars' most popular characters despite having only four lines and about six minutes of screen time in the original trilogy. He first appeared in the infamous Star Wars Holiday Special before his Empire Strikes Back debut. His Mandalorian armor and mysterious persona sparked a massive expanded universe.",

    "What weapon does General Grievous collect from fallen Jedi?":
        "General Grievous hoards lightsabers taken from Jedi he's personally killed, wielding up to four simultaneously with his cybernetic arms. He's not Force-sensitive himself but was trained in lightsaber combat by Count Dooku. His coughing and wheezing are the result of having his organic body crushed into a mostly mechanical shell.",

    "What does 'midi-chlorians' measure in Star Wars lore?":
        "Midi-chlorians are microscopic organisms that live inside all living cells and serve as conduits to the Force. A higher midi-chlorian count indicates a stronger connection to the Force. This concept, introduced in The Phantom Menace, was controversial among fans who preferred the Force's mystical, unexplained nature.",

    "Who kills Jabba the Hutt in Return of the Jedi?":
        "Princess Leia strangles Jabba with the very chain he used to enslave her, in one of the trilogy's most satisfying moments of poetic justice. She was disguised as the bounty hunter Boushh when she was captured. Carrie Fisher reportedly found the metal bikini costume extremely uncomfortable and was glad to kill the character who made her wear it.",

    "What is the moon where the Ewoks live in Return of the Jedi?":
        "The forest moon of Endor orbits a gas giant also called Endor, and its lush forests are home to the Ewoks, who help the Rebels destroy the Death Star's shield generator. The Ewok scenes were filmed in the redwood forests of Northern California. George Lucas originally planned to use Wookiees but changed to a more primitive species.",

    "Who is Luke Skywalker's twin sister?":
        "Leia Organa was hidden at birth and raised by Bail Organa on Alderaan while Luke was sent to Tatooine. Their twin connection was not part of the original plan; Lucas decided to make Leia Luke's sister while writing Return of the Jedi. This retroactively makes their kiss in Empire Strikes Back rather awkward.",

    "What planet are the Ewoks native to (or rather, what moon)?":
        "The Ewoks live on the Forest Moon of Endor, which is technically a moon orbiting a larger planet. Their primitive technology (stone and wood) is contrasted with the high-tech Imperial presence, yet they prove crucial to the Rebellion's victory. The Ewoks were controversial among fans who felt they were too cute for a war film.",

    "What color are the evil Sith lightsabers almost always?":
        "Sith lightsabers are red because the Sith use synthetic or 'bled' kyber crystals. In current canon, Sith 'bleed' natural kyber crystals by pouring their dark side rage into them, turning them red. This process is essentially torturing the crystal, reflecting the Sith's corrupting nature.",

    # ========== MCU / MARVEL ==========
    "What is the name of the villain in the first Avengers movie?":
        "Loki leads a Chitauri alien army to invade Earth through a portal opened by the Tesseract (Space Stone). Tom Hiddleston's charismatic performance made Loki one of the MCU's most popular characters, eventually getting his own Disney+ series. Despite being the main villain, Loki was actually being manipulated by Thanos behind the scenes.",

    "What is the name of the dragon in the Disney movie Mulan?":
        "Mushu is a tiny, wisecracking dragon voiced by Eddie Murphy who serves as Mulan's guardian spirit. He was demoted from his position as a family guardian after a previous failure. Mushu was originally meant to be a much larger, more serious dragon before the character was redesigned for comedy.",

    "What is Tony Stark's suit of armor powered by?":
        "The arc reactor in Tony Stark's chest was originally built in a cave to power an electromagnet keeping shrapnel from reaching his heart. He later miniaturized and improved it to power increasingly advanced Iron Man suits. The original MCU arc reactor was powered by palladium, which was slowly poisoning Tony until he synthesized a new element.",

    "What are the six Infinity Stones?":
        "Space (blue/Tesseract), Mind (yellow/Scepter), Reality (red/Aether), Power (purple/Orb), Time (green/Eye of Agamotto), and Soul (orange/Vormir) are remnants of six singularities that existed before the universe began. When united in the Infinity Gauntlet, they grant absolute control over reality. Thanos spent years tracking them all down.",

    "Who says 'I am Iron Man' before snapping in Avengers: Endgame?":
        "Tony Stark's final 'I am Iron Man' echoes his defiant declaration at the end of the first Iron Man film, bringing his character arc full circle. The snap uses all six Infinity Stones to dust Thanos and his army, but the energy kills Tony. Robert Downey Jr. improvised the line, as the original script had Tony die in silence.",

    "Which Infinity Stone is hidden on Vormir?":
        "The Soul Stone requires the sacrifice of someone you truly love to obtain it, making it the cruelest of the Infinity Stones. Red Skull, cursed to be its guardian, explains the price to both Thanos (who sacrifices Gamora) and Hawkeye/Black Widow (with Natasha sacrificing herself). The stone's location was one of the MCU's longest-running mysteries.",

    "What is Black Widow's real name?":
        "Natasha Romanoff was trained from childhood in the Red Room, a Soviet program that created elite female assassins. She defected to S.H.I.E.L.D. and became one of the founding Avengers. Her sacrifice on Vormir to obtain the Soul Stone was her way of clearing the 'red in her ledger' once and for all.",

    "What is the name of Wakanda's king in Black Panther?":
        "T'Challa inherited the Black Panther mantle and the Wakandan throne after his father T'Chaka's death. Chadwick Boseman's dignified, powerful performance defined the character and made Black Panther a cultural phenomenon. Boseman's real-life battle with cancer during filming made his portrayal even more poignant.",

    "Who is the villain of the first Iron Man film?":
        "Obadiah Stane (Iron Monger) was Tony's father's business partner who secretly arranged Tony's kidnapping and later built his own armored suit from Tony's designs. Jeff Bridges shaved his head for the role and played Stane as a smiling corporate shark. He was the MCU's first true villain.",

    "What does S.H.I.E.L.D. stand for in the MCU?":
        "The full name was retconned multiple times in the comics, but the MCU settled on Strategic Homeland Intervention, Enforcement and Logistics Division. Agent Coulson admits they're 'working on' the name. The organization was founded after WWII by Peggy Carter, Howard Stark, and others to protect against extraordinary threats.",

    "What is the name of Doctor Strange's home base?":
        "The Sanctum Sanctorum is located at 177A Bleecker Street in Greenwich Village, New York, and is one of three Sanctums (along with London and Hong Kong) that protect Earth from mystical threats. Its Seal of Vishanti window is recognizable from the comics. The building exists in real life, though it's just an ordinary building.",

    "Who is Peter Parker's best friend in Spider-Man: Homecoming?":
        "Ned Leeds, played by Jacob Batalon, is Peter's enthusiastic 'guy in the chair' who discovers Peter's secret identity and immediately wants to help. His character combines elements of several Spider-Man comic characters. His excited reaction to learning Peter is Spider-Man is one of Homecoming's funniest moments.",

    "What is the name of the organization secretly embedded inside S.H.I.E.L.D.?":
        "HYDRA infiltrated S.H.I.E.L.D. from its very founding, when Operation Paperclip recruited Arnim Zola and other former Nazi scientists. Their motto 'Cut off one head, two more shall take its place' proved literally true within the organization. Captain America: The Winter Soldier's revelation that HYDRA had been controlling S.H.I.E.L.D. for decades was the MCU's biggest conspiracy twist.",

    "What is Thanos's home planet?":
        "Titan was once a thriving civilization that collapsed due to overpopulation and resource depletion, according to Thanos. This trauma drove his obsession with 'balancing' the universe by eliminating half of all life. When the Avengers visit Titan, it's a desolate wasteland, physically representing Thanos's greatest fear.",

    "What is Thanos's goal with the completed Infinity Gauntlet?":
        "Thanos believes that randomly eliminating half of all life will save the universe from the resource collapse that destroyed his homeworld Titan. He sees himself not as a villain but as a necessary surgeon. The 'Snap' (or 'Blip') erasing half of all life is one of cinema's most shocking villain victories.",

    "Who is sacrificed to obtain the Soul Stone in Avengers: Infinity War?":
        "Thanos throws Gamora, his adopted daughter, off the cliff on Vormir because she's the person he loves most. Gamora believed Thanos was incapable of love, but the Soul Stone accepted the sacrifice. Zoe Saldana's horrified realization that Thanos genuinely loves her in his twisted way is devastating.",

    "What material is Captain America's shield made from?":
        "Vibranium is a rare metal found almost exclusively in Wakanda, brought to Earth by a meteorite millions of years ago. It absorbs kinetic energy (vibrations), making Cap's shield virtually indestructible and capable of absorbing any impact. Howard Stark used all available vibranium to create the shield, explaining why it's one of a kind.",

    "In Endgame, who besides Thor is able to lift Mjolnir?":
        "Captain America lifting Mjolnir is one of the MCU's most crowd-pleasing moments, as audiences erupted in theaters worldwide. Thor's delighted 'I knew it!' suggests Cap was always worthy but held back in Age of Ultron when he budged the hammer slightly. The enchantment states only the 'worthy' can wield it.",

    "What is the name of the Guardians of the Galaxy's ship?":
        "The Milano is Peter Quill's M-class ship named after his childhood crush, actress Alyssa Milano. Its orange-and-blue color scheme and compact design make it one of the MCU's most recognizable ships. After the Milano was destroyed, the team used the Benatar (named after Pat Benatar) in later films.",

    "Which Infinity Stone is contained in the Tesseract?":
        "The Space Stone allows instantaneous travel across the universe and was the first Infinity Stone introduced in the MCU (Captain America: The First Avenger). Red Skull used it to power HYDRA weapons, Howard Stark recovered it from the ocean, and Loki used it to open the Chitauri portal. Thanos eventually crushed the Tesseract cube to extract the stone.",

    "What is the name of Ant-Man's mentor and the original Ant-Man?":
        "Hank Pym discovered the Pym Particles that allow size manipulation and operated as the original Ant-Man alongside his wife Janet Van Dyne (the Wasp) during the Cold War. He retired after Janet was lost in the Quantum Realm and passed the mantle to Scott Lang. Michael Douglas brought gravitas to the role of the brilliant but bitter Pym.",

    "Who kills Loki in Avengers: Infinity War?":
        "Thanos snaps Loki's neck after Loki's failed assassination attempt with a concealed dagger. Thanos's cold declaration 'No resurrections this time' seemed definitive. However, the 2012 timeline Loki escapes with the Tesseract during the Avengers' time heist in Endgame, leading to the Loki TV series.",

    "What is Nick Fury's most recognizable physical feature?":
        "Nick Fury's eye patch over his left eye is his most distinctive feature, and he tells different people different stories about how he lost the eye. Captain Marvel reveals the anticlimactic truth: a Flerken (an alien cat named Goose) scratched it. Samuel L. Jackson has said the eye patch is his favorite part of the costume.",

    "What is the Power Stone originally found inside in the MCU?":
        "The Power Stone was contained inside the Orb, an artifact hidden in the Temple of Morag and sought by Star-Lord at the beginning of Guardians of the Galaxy. Direct contact with the stone unleashes energy that destroys most beings instantly. The Guardians survived wielding it together only because of their combined strength and Quill's Celestial heritage.",

    # ========== SKYRIM / ELDER SCROLLS ==========
    "What is the first shout the Dragonborn learns in Skyrim?":
        "Unrelenting Force (Fus Ro Dah) is learned at Bleak Falls Barrow and the Greybeards' High Hrothgar. The first word 'Fus' (Force) is found on a Word Wall in the barrow. 'Fus Ro Dah' became a massive internet meme, with videos of people and objects being blasted away set to the shout's sound effect.",

    "What is the name of the main antagonist dragon in Skyrim?":
        "Alduin is the World-Eater, the firstborn of the dragon god Akatosh, prophesied to devour the world and end the current era (kalpa). He was cast forward in time by ancient Nords using an Elder Scroll, emerging in Skyrim's present day. Despite being a world-ending threat, many players find him surprisingly easy compared to random high-level dragons.",

    "What is the name of the warrior faction in Skyrim associated with werewolves?":
        "The Companions are an ancient order of warriors based in Whiterun's mead hall Jorrvaskr, built around the overturned ship of the legendary Ysgramor. Their inner circle, the Circle, carries the 'beast blood' of Hircine the Daedric Prince, allowing them to transform into werewolves. The questline forces you to confront whether this gift is a blessing or a curse.",

    "Who is the true leader of the Thieves Guild (as a traitor) in Skyrim?":
        "Mercer Frey was the Thieves Guild Guildmaster who secretly stole the Skeleton Key of Nocturnal, breaking the guild's oath and causing their string of bad luck. He'd been embezzling from the Guild for years and murdered the previous Guildmaster. His betrayal and the quest to restore Nocturnal's artifact is one of Skyrim's best storylines.",

    "What is the name of the hidden assassin faction in Skyrim?":
        "The Dark Brotherhood is a family of assassins who worship Sithis and the Night Mother, accepting contracts through a ritual called the Black Sacrament. Their greeting 'What is the music of life? Silence, my brother' is one of gaming's most memorable faction passwords. Their Skyrim questline involves an assassination plot against the Emperor himself.",

    "Which Daedric Prince is associated with madness and cheese in Elder Scrolls?":
        "Sheogorath, the Daedric Prince of Madness, is one of the most beloved characters in the Elder Scrolls series. His obsession with cheese (especially cheese wheels) has become a fan-favorite running joke. In Skyrim, his quest 'The Mind of Madness' takes place inside the mind of the dead Emperor Pelagius III.",

    "What is the name of the wise old dragon who lives on the Throat of the World?":
        "Paarthurnax is the leader of the Greybeards who has spent millennia atop the Throat of the World meditating to overcome his violent dragon nature. He was once Alduin's lieutenant before betraying him to teach mortals the Thu'um. The Blades' demand that you kill him creates one of Skyrim's most debated moral choices.",

    "What is the name of the civil war leader of the Stormcloaks in Skyrim?":
        "Ulfric Stormcloak is the Jarl of Windhelm who killed High King Torygg with the Thu'um and ignited the Skyrim Civil War. His cause (Nordic independence and Talos worship) has legitimate grievances, but his methods and the racism in Windhelm complicate his heroic image. Players must choose between the Stormcloaks and the Imperial Legion.",

    "What are the words of power in Skyrim called collectively?":
        "The Thu'um (Dragon Shout) is the ancient art of using the dragon language to project power through voice. Each shout consists of three words of power, with each word increasing its potency. The Dragonborn can learn shouts instantly by absorbing dragon souls, while the Greybeards spent decades mastering even basic shouts.",

    "What is the title given to one who can absorb dragon souls in Skyrim?":
        "Dovahkiin (Dragonborn) literally means 'Dragonborn' in the dragon language: 'Dovah' (dragon) + 'kiin' (born). The Dragonborn has the body of a mortal but the soul of a dragon, allowing them to absorb the knowledge and power of slain dragons. The prophecy of the Last Dragonborn is inscribed on Alduin's Wall.",

    "Which city in Skyrim is the capital of the Stormcloak rebellion?":
        "Windhelm is the oldest city in Skyrim, founded by Ysgramor himself, and serves as Ulfric Stormcloak's seat of power. The city's Grey Quarter, where Dunmer refugees are confined to squalid conditions, reveals uncomfortable truths about the Stormcloak ideology. Its Palace of the Kings is one of the most impressive buildings in the game.",

    "Who is the Daedric Prince of Destruction associated with the planes of Oblivion?":
        "Mehrunes Dagon is the Daedric Prince of Destruction, Change, and Ambition who was the main antagonist of The Elder Scrolls IV: Oblivion. He attempted a full-scale invasion of Tamriel through Oblivion Gates. His Razor (Mehrunes' Razor) is a dagger with a small chance to instantly kill any enemy in Skyrim.",

    "What is the name of the vampire faction in the Dawnguard DLC?":
        "The Volkihar Clan is led by Lord Harkon, an ancient vampire who seeks to fulfill a prophecy to blot out the sun permanently using Auriel's Bow. Players can choose to join the vampires or the Dawnguard vampire hunters. The Volkihar castle on a frozen island is one of Skyrim's most atmospheric locations.",

    "What is the name of the ancient axe of the Companions in Skyrim?":
        "Wuuthrad was the legendary battleaxe wielded by Ysgramor during the Return, when he led 500 Companions to reclaim Skyrim from the elves. The axe was shattered and its fragments scattered over the centuries. Reassembling Wuuthrad is the key to entering Ysgramor's Tomb during the Companions questline.",

    "In Skyrim, what skill tree governs the use of one-handed weapons?":
        "The One-Handed skill tree includes swords, war axes, maces, and daggers. Its perks branch into specialized paths for different weapon types, with Armsman increasing base damage and specialized perks adding bleeding, decapitation, and paralyzing effects. Most combat-focused characters invest heavily in this tree.",

    "What is the name of the Daedric Prince who rules the Shivering Isles?":
        "Sheogorath rules the Shivering Isles, a realm of madness split between Mania (creative insanity) and Dementia (dark insanity). The Oblivion expansion of the same name is widely considered one of the best Elder Scrolls DLCs ever made. In it, the player actually becomes Sheogorath, which is why Skyrim's Sheogorath makes references to the events of Oblivion.",

    # ========== FINAL FANTASY ==========
    "Who is the main villain of Final Fantasy VII?":
        "Sephiroth is a former SOLDIER hero who went insane upon discovering he was created from cells of the alien entity Jenova. His one-winged angel form and iconic theme song 'One-Winged Angel' made him gaming's most recognizable villain. His murder of Aerith is one of the most shocking moments in video game history.",

    "What is the name of Cloud's giant sword in FF7?":
        "The Buster Sword is a massive, iconic blade originally wielded by Cloud's friend and mentor Zack Fair. Cloud inherited it after Zack's death, and it serves as a symbol of their bond and Cloud's false memories. The sword's impractical size has become a beloved trope of Japanese RPG character design.",

    "What is the name of Cloud's childhood friend in Final Fantasy VII?":
        "Tifa Lockhart grew up in Nibelheim with Cloud and runs the 7th Heaven bar that serves as AVALANCHE's secret headquarters. She's one of the few people who knows the truth about Cloud's fabricated memories. Her martial arts fighting style makes her unique among FF7's cast of sword and gun wielders.",

    "Who is Yuna's main guardian in Final Fantasy X?":
        "Tidus is a star Blitzball player from the dream city of Zanarkand who is thrown 1,000 years into the future and becomes Yuna's guardian on her pilgrimage. His cheerful personality gradually reveals deeper layers as the truth about Spira's cycle of destruction unfolds. The laugh scene between him and Yuna is intentionally awkward, not bad acting.",

    "What is the recurring fire summon in Final Fantasy?":
        "Ifrit has appeared in nearly every mainline Final Fantasy game since FFIII, typically as a horned, muscular fire demon. He's usually one of the earliest summons obtained and serves as a reliable source of fire damage. His design has evolved dramatically across the series, from a simple demon to an elaborate beast.",

    "What does a Moogle say in every Final Fantasy appearance?":
        "Moogles say 'Kupo!' as their signature expression, and it's become one of Final Fantasy's most recognizable catchphrases. These small, fluffy creatures with bat wings and a pom-pom antenna have served as save points, mail carriers, shopkeepers, and even party members across the series. They first appeared in Final Fantasy III.",

    "Who is the main villain of Final Fantasy VI?":
        "Kefka Palazzo is a nihilistic court jester who actually succeeds in destroying the world and becoming a god, making him unique among FF villains. His maniacal laugh and clown-like appearance mask genuine menace. He's often cited as one of gaming's greatest villains because he's one of the few who actually wins.",

    "What does FF6's World of Ruin refer to?":
        "Halfway through Final Fantasy VI, Kefka actually destroys the world by rearranging the Warring Triad statues, creating the World of Ruin. The second half of the game takes place a year later in this devastated landscape. The player must reassemble their party one by one, with most character reunions being optional.",

    "What is the large yellow bird creature used for transportation in Final Fantasy?":
        "Chocobos have appeared in every mainline Final Fantasy since FFII and are the series' most beloved mascot alongside Moogles. They come in various colors with different abilities (gold chocobos can fly and cross water). Their iconic 'Chocobo Theme' music is one of gaming's most recognizable tunes.",

    "What is the name of the recurring Final Fantasy character who is always an engineer or airship pilot?":
        "A character named Cid appears in every mainline Final Fantasy from FFII onward, always connected to technology, engineering, or airships in some way. Each Cid is a different character, from gruff mechanics to refined scientists to playable party members. The tradition has become one of the series' most beloved Easter eggs.",

    "In FF10, what is the name of the water sport played in Spira?":
        "Blitzball is an underwater sport played inside a massive sphere of water, where players can hold their breath for extended periods. It's a fully playable minigame in FFX with its own recruitment system, stats, and tournaments. Tidus was a star player for the Zanarkand Abes before being transported to Spira.",

    "What is Sephiroth's most powerful attack?":
        "Supernova is an absurdly cinematic attack where Sephiroth summons a meteor that destroys the entire solar system (in the international version), complete with a two-minute unskippable animation. Despite the apocalyptic visuals, it deals percentage-based damage and can't actually kill your party. The Japanese version has a shorter, different animation.",

    "What was the original Final Fantasy game released on?":
        "The original Final Fantasy (1987) was released on the Nintendo Entertainment System (Famicom in Japan). Creator Hironobu Sakaguchi named it 'Final Fantasy' because he planned to quit the industry if it failed. It became a massive hit and spawned one of gaming's most successful franchises.",

    "In Final Fantasy IX, who is the main protagonist?":
        "Zidane Tribal is a charming, monkey-tailed thief and member of the Tantalus Theater Troupe. FFIX was designed as a love letter to the classic, more fantastical style of earlier Final Fantasy games. Zidane's upbeat, flirtatious personality was a deliberate contrast to the brooding Cloud and Squall of FFVII and FFVIII.",

    "What is Terra's unique ability in Final Fantasy VI?":
        "Terra Branford is half-human, half-Esper, making her the only person in the world who can use magic naturally without magicite. She can also transform into her Esper form, dramatically boosting her power. Her identity crisis about being caught between two worlds is the emotional core of FFVI's first half.",

    "What is the name of the recurring blue dragon deity summon in Final Fantasy?":
        "Bahamut is the King of Dragons and typically the most powerful non-secret summon in each Final Fantasy game, unleashing devastating Megaflare attacks. He appears in almost every FF title and has had many forms (Bahamut ZERO, Neo Bahamut, etc.). His name comes from the mythological Bahamut of Arabian mythology.",

    "What opera is performed in Final Fantasy VI?":
        "The 'Maria and Draco' opera scene is one of the most beloved sequences in RPG history, where Celes must perform as the lead soprano to lure the opera-loving airship pilot Setzer. The scene demonstrated that video games could achieve genuine artistic beauty. The opera was fully voiced and orchestrated in the Pixel Remaster.",

    "What is the name of the mega-city built on metal plates in FF7?":
        "Midgar is a dystopian megacity built on massive plates that literally block sunlight from the slums below, creating a stark class divide. The Shinra Electric Power Company controls the city and drains the planet's Lifestream for energy. Midgar's oppressive atmosphere and environmental themes were groundbreaking for 1997.",

    # ========== SMASH BROS ==========
    "Who are the original 8 characters in Super Smash Bros. 64?":
        "The original eight were Nintendo's most iconic characters: Mario, Donkey Kong, Link, Samus, Yoshi, Kirby, Fox, and Pikachu. Luigi was notably absent from the starting roster (he was an unlockable). Creator Masahiro Sakurai developed the original prototype as 'Dragon King: The Fighting Game' with generic characters before adding Nintendo stars.",

    "What is the technique in Melee that lets characters slide on the ground after an air dodge?":
        "Wavedashing involves jumping and immediately air-dodging diagonally into the ground, causing the character to slide while retaining all ground options. It was an unintended mechanic that became central to high-level Melee play. Nintendo never patched it out and it's now considered a defining feature of Melee's competitive scene.",

    "What item in Smash Bros. activates a character's Final Smash?":
        "The Smash Ball is a floating, glowing orb that must be hit multiple times to break, granting the character who breaks it access to their unique Final Smash super move. It was introduced in Super Smash Bros. Brawl. Ultimate also added the Final Smash Meter as an alternative way to charge Final Smashes.",

    "What is Captain Falcon's most famous move?":
        "The Falcon Punch is an enormously powerful, dramatically slow fire-infused punch that has become one of gaming's most iconic attacks. It's impractical in competitive play due to its long wind-up, but landing it is immensely satisfying. Captain Falcon's 'FALCON PUNCH!' scream has been memed endlessly since 1999.",

    "Which Smash Bros. game introduced the Subspace Emissary story mode?":
        "Super Smash Bros. Brawl (2008) featured the Subspace Emissary, a full side-scrolling adventure mode with cutscenes showing Nintendo characters teaming up. It was directed by Masahiro Sakurai, who poured enormous effort into the cinematic crossover story. The leaked cutscenes online before release led Sakurai to skip story modes in later games.",

    "What game is Meta Knight from?":
        "Meta Knight is from the Kirby series, where he serves as a mysterious, honorable rival to Kirby. He always offers Kirby a sword before fighting, showing his code of fair combat. In Super Smash Bros. Brawl, he was infamously the best character in the game and was sometimes banned from tournaments.",

    "What character is widely considered the best in Melee's competitive tier list?":
        "Fox McCloud's incredible speed, combo potential, and devastating 'shine' (Reflector) make him Melee's consensus top-tier character. His technical ceiling is so high that even top players can't execute everything perfectly. The 'Fox ditto' (Fox vs. Fox) at high level is considered Melee's purest test of skill.",

    "What was the final DLC fighter added to Super Smash Bros. Ultimate?":
        "Sora from Kingdom Hearts was the final DLC fighter, revealed at a special presentation in October 2021. His inclusion was the result of years of negotiations between Nintendo, Disney, and Square Enix. Sakurai revealed that Sora was the most-requested character in the Smash Fighter Ballot.",

    "What technique in Melee involves canceling the landing lag of aerial attacks?":
        "L-canceling (also called Z-canceling in Smash 64) halves the landing lag of aerial attacks when you press L, R, or Z just before landing. It's one of the first advanced techniques competitive players learn. Nintendo removed it in later Smash games, reducing the technical barrier but also the skill expression.",

    "How many total fighters are in Super Smash Bros. Ultimate including all DLC?":
        "Super Smash Bros. Ultimate has 89 fighters (82 base plus 12 DLC, minus Pyra/Mythra counting as one slot). Its 'Everyone is Here!' tagline meant every single previous Smash character returned. Sakurai has said this roster size is unlikely to be matched in any future installment.",

    "What move does Ness use that reflects projectiles and absorbs PSI moves?":
        "PSI Magnet creates an energy field around Ness that absorbs energy-based projectiles and converts them into healing. It's essential for Ness's survival against projectile-heavy characters. The move comes from EarthBound, where PSI Magnet absorbs enemy psychic attacks.",

    "Which Smash Bros. game had the Adventure Mode called 'The Subspace Emissary'?":
        "Brawl's Subspace Emissary was a massive side-scrolling adventure featuring Nintendo characters facing an original villain, Tabuu. The mode featured gorgeous CG cutscenes showing characters from different franchises meeting for the first time. Its ambitious scope hasn't been replicated in later Smash games.",

    # ========== NINTENDO GENERAL ==========
    "What is Bowser's species?":
        "Bowser is a Koopa, specifically the King of the Koopas, a turtle-like species in the Mario universe. His Japanese name 'Kuppa' comes from the Korean word for a type of rice soup. Despite being Mario's arch-nemesis, he's also a loving father to Bowser Jr. and occasionally teams up with Mario against greater threats.",

    "What power-up lets Mario shoot fireballs?":
        "The Fire Flower transforms Mario into Fire Mario (white and red outfit), granting the ability to throw bouncing fireballs. It first appeared in Super Mario Bros. (1985) and has been in nearly every Mario game since. In multiplayer games, Luigi's fireballs are green while Mario's are red.",

    "Who holds the Triforce of Wisdom in the Legend of Zelda?":
        "Princess Zelda holds the Triforce of Wisdom, which grants her prophetic dreams, magical abilities, and deep insight. Despite the series being named after her, she's been playable in relatively few games. Each game features a different incarnation of Zelda, all descended from the goddess Hylia.",

    "What is the famous reveal about Samus Aran at the end of the original Metroid?":
        "Completing the original Metroid quickly enough reveals that the armored bounty hunter Samus is a woman, one of gaming's most groundbreaking twists in 1986. The faster you beat the game, the more of her civilian appearance you see. This reveal challenged assumptions about who video game heroes could be.",

    "What is the name of Donkey Kong's main villain?":
        "King K. Rool is a crocodile king who repeatedly steals Donkey Kong's banana hoard and kidnaps Kong family members. He's appeared as a pirate (Kaptain K. Rool), a mad scientist (Baron K. Roolenstein), and a boxer (King Krusha K. Rool). His inclusion in Smash Bros. Ultimate was one of the most celebrated character reveals.",

    "What is the name of Kirby's home world?":
        "Planet Popstar is a star-shaped planet in the Kirby universe, with Dream Land being its most famous kingdom. Kirby protects it from threats ranging from the evil King Dedede to cosmic horrors like Dark Matter. Despite its cute appearance, the Kirby series has some of gaming's most terrifyingly powerful final bosses.",

    "What is Captain Falcon's racing vehicle called?":
        "The Blue Falcon is Captain Falcon's signature F-Zero racing machine, capable of speeds exceeding 1,500 km/h. F-Zero (1990) was one of the SNES launch titles and showcased Mode 7 graphics. Despite Captain Falcon's massive popularity from Smash Bros., Nintendo hasn't released a new F-Zero game since 2004.",

    "What is the first dungeon in Ocarina of Time called?":
        "Inside the Deku Tree is the first dungeon, where young Link must clear a curse placed by Ganondorf. The Great Deku Tree serves as the guardian of Kokiri Forest and Link's initial mentor. Despite Link's success, the Deku Tree dies from the curse, giving the game an unexpectedly somber early tone.",

    "What does Ganondorf's piece of the Triforce represent?":
        "Ganondorf holds the Triforce of Power, which grants him near-invulnerability and immense dark magic. His relentless pursuit of the complete Triforce drives the conflict in most Zelda games. He's the recurring incarnation of the demon king Demise's hatred, cursed to eternally battle the hero and the goddess.",

    "What is the main lord character in Fire Emblem: Path of Radiance?":
        "Ike is the son of the mercenary Greil and leads the Greil Mercenaries into a continent-spanning war. His lack of noble birth made him unique among Fire Emblem lords and contributed to his popularity. His famous Smash Bros. line 'I fight for my friends' perfectly captures his straightforward character.",

    "What is the final boss of The Legend of Zelda: Majora's Mask?":
        "Majora's Mask goes through three forms: Majora's Mask (the possessed mask), Majora's Incarnation (a bizarre dancing creature), and Majora's Wrath (a terrifying whip-armed humanoid). The mask itself is an ancient artifact of terrible power that possessed Skull Kid. The fight takes place inside the Moon, which has been threatening to crash into Termina for three days.",

    "What does Meta Knight's mask conceal?":
        "Beneath Meta Knight's mask is a face nearly identical to Kirby's, just blue instead of pink. He hides it because he considers showing his face embarrassing, immediately fleeing when his mask breaks. This connection has led to decades of fan speculation about whether he and Kirby are the same species.",

    "What are the four Divine Beasts in Breath of the Wild named after?":
        "Vah Ruta (Ruto), Vah Medoh (Medli), Vah Rudania (Darunia), and Vah Naboris (Nabooru) are each named after sages from previous Zelda games, specifically Ocarina of Time and Wind Waker. Each was piloted by a Champion who fell to Calamity Ganon 100 years ago. Freeing the Divine Beasts provides powerful assistance in the final battle.",

    "What is the name of the Metroid homeworld where Metroids originate?":
        "SR388 is a hostile planet where the Chozo created Metroids to combat the parasitic X organisms. The entire planet was explored in Metroid II: Return of Samus and its remake Metroid: Samus Returns. Samus's mission to exterminate all Metroids on SR388 sets up the events of Super Metroid and Metroid Fusion.",

    # ========== GROUNDED ==========
    "What is the premise of the game Grounded?":
        "Grounded by Obsidian Entertainment shrinks four teenagers to the size of ants in a suburban backyard, turning ordinary grass into a jungle and garden bugs into terrifying monsters. The game draws heavy inspiration from the 1989 film 'Honey, I Shrunk the Kids.' Its survival mechanics are built around the unique perspective of being tiny.",

    "What are the names of the four playable characters in Grounded?":
        "Max, Pete, Willow, and Hoops each have distinct personalities: Max is the leader type, Pete is the nerdy one, Willow is the rebellious one, and Hoops is the athletic one. They wake up shrunk in the backyard with no memory of how it happened. Each character has the same gameplay abilities.",

    "What is the name of the robot that gives quests to players in Grounded?":
        "BURG.L (which stands for something never fully explained) is a helpful but glitchy robot who provides quests, recipes, and information about the backyard. He's missing several of his science chips, which players must recover from dangerous locations. His cheerful personality makes him the game's most endearing NPC.",

    "What device do players use to analyze items and unlock recipes in Grounded?":
        "The SCA.B (Super Chip Attached to Back) is a wrist-mounted device that serves as the player's HUD, map, and item analyzer. Analyzing new materials unlocks crafting recipes. It's a brilliantly practical plot device that explains how teenagers can build complex equipment.",

    "What corporation is responsible for the shrinking experiment in Grounded?":
        "Ominent Diversified Sciences is the shadowy corporation behind the miniaturization technology that shrunk the kids. Their experiments in the backyard lab go far beyond simple shrinking, with evidence of more sinister research. The corporate conspiracy is gradually revealed through scattered logs and documents.",

    "Who is the scientist responsible for the shrinking experiment in Grounded?":
        "Dr. Wendell Tully created the shrinking technology and built the backyard research lab, but something went wrong during his experiments. Players gradually piece together his story through audio logs and lab discoveries. His motivations become more complex as the story unfolds.",

    "What is the most feared large spider in Grounded?":
        "Wolf Spiders are nocturnal hunters that roam the backyard at night, and encountering one unprepared is often fatal for new players. They're fast, aggressive, and deal massive damage. The game actually has an arachnophobia mode that progressively reduces spiders to floating blobs to accommodate players with spider fears.",

    "What material do players collect from grass blades in Grounded?":
        "Grass Planks (chopped from full grass blades) and Grass Fiber (from loose grass) are the game's most basic building materials. They're used for everything from walls and floors to basic tools. Carrying planks is physically modeled, with the tiny character hauling enormous (relative to them) pieces of grass.",

    "What large insect in Grounded sprays a burning chemical as an attack?":
        "Bombardier Beetles spray a boiling chemical defense from their abdomen, just like their real-world counterparts, which can eject a caustic spray at 100 degrees Celsius. In the game, their acid attack deals heavy damage and can catch unprepared players off guard. Real bombardier beetles create this spray through an internal chemical reaction.",

    "What health drinks can be crafted at a smoothie station in Grounded?":
        "Smoothies are healing and buff drinks made from various backyard ingredients like berries, flowers, and bug parts at a Smoothie Station. Different recipes provide different effects: healing, stamina recovery, attack boosts, and resistance to specific damage types. The smoothie system encourages experimentation with ingredient combinations.",

    "What large red creature in Grounded is found near the oak tree and charges players?":
        "Ladybugs (called Ladybirds in some regions) are passive creatures that become aggressive when provoked or when players are carrying planks near their territory. Despite being 'cute' in real life, at the player's scale they're intimidating tanks that can kill in a few hits. They're among the first large creatures new players encounter.",

    "What material from spiders is needed to build ziplines in Grounded?":
        "Spider Silk Rope is crafted from spider web, requiring players to venture into spider dens and harvest silk from their webs. This creates a compelling risk-reward dynamic: you need to brave spider territory to build the ziplines that make future travel safer. Ziplines become essential for quickly traversing the vast backyard.",

    "What mineral resource in Grounded is mined from white rocks and used for durable tools?":
        "Quartzite is a tier-2 mineral found in caves and dark areas, used to craft repair tools and upgrade weapons. Mining it requires venturing into dangerous underground areas populated by spiders and other creatures. It's essential for maintaining equipment durability in the mid-game.",

    "What are the small round rock resources called that are used in early crafting in Grounded?":
        "Pebblets are tiny pebbles that, at the player's shrunken scale, are the size of boulders. They're used alongside plant fiber and other basic materials to craft early-game tools like axes and hammers. They're one of the first resources new players collect.",

    "What is the currency used to buy upgrades from BURG.L in Grounded?":
        "Raw Science appears as glowing blue orbs scattered throughout the backyard and earned by completing BURG.L's quests. It's spent on purchasing new crafting recipes and upgrades from BURG.L. Finding hidden Raw Science deposits rewards exploration of dangerous areas.",

    "What is the main antagonist creature type found in the Haze biome in Grounded?":
        "The Haze is a foggy area created by a leaking weed killer canister, filled with infected insects including fungal-infested gnats and mites. The toxic atmosphere requires gas masks to survive. It's one of the game's most atmospheric and unsettling biomes.",

    # ========== STARDEW / TERRARIA ==========
    "In Stardew Valley, what is the name of the town you move to?":
        "Pelican Town is a small rural community in Stardew Valley where the player inherits their grandfather's old farm. The town has about 30 residents, each with unique schedules, preferences, and storylines. Developer Eric 'ConcernedApe' Barone created the entire game solo over four years.",

    "In Stardew Valley, who gives you the farm at the start of the game?":
        "Your grandfather leaves you the farm in his will, with a letter asking you to open it when modern life becomes too much. The game begins when your corporate office job drives you to finally take up his offer. This setup reflects the game's theme of finding meaning outside the rat race.",

    "In Terraria, what is the first boss most players fight?":
        "The Eye of Cthulhu is a giant flying eyeball that spawns naturally once the player has enough health and NPCs, or can be summoned with a Suspicious Looking Eye. It starts slow, then enters a more aggressive second phase where its pupil rips out to reveal a mouth. Despite being the first boss, it can be challenging for unprepared players.",

    # ========== RESIDENT EVIL ==========
    "Who are the main protagonists of Resident Evil 2 (original and remake)?":
        "Leon S. Kennedy is a rookie cop on his first day and Claire Redfield is searching for her brother Chris. They arrive in Raccoon City during the zombie outbreak and are separated, each experiencing different parts of the same nightmare. The dual-protagonist structure was revolutionary for survival horror.",

    "What is the name of the virus used to create zombies in the original Resident Evil?":
        "The T-Virus (Tyrant Virus) was developed by the Umbrella Corporation as a biological weapon, but leaked into the Arklay Mountains and Raccoon City water supply. It reanimates dead tissue, creating zombies and various other mutations. The T-Virus was derived from the ancient Progenitor Virus found in African flowers.",

    "Who is the main antagonist Umbrella executive throughout the early Resident Evil games?":
        "Albert Wesker betrayed his S.T.A.R.S. teammates in the original Resident Evil, revealing himself as an Umbrella double agent. He injected himself with a virus that gave him superhuman abilities, including incredible speed and strength. His sunglasses-wearing, trench-coat villain persona became iconic in gaming.",

    "What is the name of the relentless pursuer in Resident Evil 3?":
        "Nemesis is a Tyrant bio-weapon programmed to hunt and kill all remaining S.T.A.R.S. members in Raccoon City. Unlike previous enemies, Nemesis can use weapons, run, and follow the player between areas. His terrifying 'STAAARS!' growl became one of gaming's most recognizable villain lines.",

    "In Resident Evil 4, what country does Leon travel to?":
        "Leon travels to rural Spain to rescue the President's daughter from the Los Illuminados cult. The game's shift from zombie horror to action-oriented gameplay against intelligent, weapon-wielding Ganados revolutionized third-person shooters. The over-the-shoulder camera angle it popularized was adopted by countless games afterward.",

    "What are the parasite-controlled villagers in RE4 called?":
        "Ganados (Spanish for 'cattle') are villagers infected with Las Plagas parasites that control their minds while maintaining their intelligence and ability to use tools and weapons. Unlike mindless zombies, they can set ambushes, use chainsaws, and coordinate attacks. The Las Plagas represented a major evolution in RE enemy design.",

    "Who is Leon Kennedy sent to rescue in Resident Evil 4?":
        "Ashley Graham is the US President's daughter, kidnapped by the Los Illuminados cult to be implanted with a Las Plagas parasite and returned as a sleeper agent. Protecting Ashley while fighting enemies became a central gameplay mechanic. Her frequent cries of 'LEON, HELP!' became a beloved meme.",

    "Who is the main villain of Resident Evil Village (RE8)?":
        "Mother Miranda is an ancient being who mastered the Megamycete (a massive mold colony) and created the four lords of the village in her experiments to resurrect her dead daughter. Lady Dimitrescu, Heisenberg, Moreau, and Beneviento are all her pawns. Miranda's centuries of manipulation make her one of RE's most dangerous villains.",

    "What is the name of the tall vampire woman in RE8 Village?":
        "Lady Alcina Dimitrescu stands 9 feet 6 inches tall and rules her castle section with her three vampire daughters. Her towering presence and elegant menace made her an instant fan sensation before the game even launched. Her mutations are caused by the Cadou parasite, not traditional vampirism.",

    "What corporation is responsible for most biological outbreaks in Resident Evil?":
        "The Umbrella Corporation was a pharmaceutical company that secretly developed biological weapons, ultimately causing the Raccoon City disaster and numerous other outbreaks. Despite being 'officially' dissolved, its research and former employees continue to cause problems throughout the series. Their red-and-white logo is one of gaming's most recognized corporate symbols.",

    "What is William Birkin's mutation in Resident Evil 2?":
        "William Birkin injected himself with his own G-Virus to survive being shot by Umbrella's USS team, triggering a series of grotesque mutations that make him increasingly monstrous. He transforms through five stages, each more horrifying than the last. His G-Virus is more powerful than the T-Virus but harder to control.",

    "What does S.T.A.R.S. stand for in Resident Evil?":
        "Special Tactics And Rescue Service is an elite law enforcement unit of the Raccoon City Police Department. Both S.T.A.R.S. Alpha and Bravo teams are sent to investigate bizarre murders in the Arklay Mountains, leading them to the Spencer Mansion. Most members are killed, with only Chris, Jill, Barry, Brad, and Rebecca surviving.",

    "What is the name of the fungal entity in RE7 that Eveline controls?":
        "The Mold (Mutamycete) is a fungal superorganism that can infect and control living beings, giving them regenerative abilities and linking their minds. Eveline, a bioweapon made from the Mold, controls the infected Baker family through it. The Mold connects to RE Village through the Megamycete, the Mold's origin.",

    "Who is Chris Redfield's partner in the original Resident Evil?":
        "Jill Valentine is a member of S.T.A.R.S. Alpha team and one of the series' two original protagonists. She and Chris can be chosen as separate playable characters in RE1, each with different gameplay experiences. Jill's lockpicking skills and access to Barry Burton's help make her campaign slightly easier.",

    # ========== MISC ==========
    "What does GG mean in gaming?":
        "GG stands for 'Good Game' and is typed in chat at the end of competitive matches as a sign of sportsmanship. It originated in early online gaming communities in the 1990s, particularly in StarCraft and other RTS games. Saying 'GG' too early (before the game is actually over) is considered disrespectful, essentially telling your opponent to give up.",

    "What does HP stand for in most video games?":
        "Hit Points originated in tabletop wargaming and was popularized by Dungeons & Dragons in 1974 before becoming universal in video games. HP represents a character's health or damage capacity before death. The concept was revolutionary because it replaced the previous binary alive/dead state with a gradient that added tactical depth.",

    "In The Legend of Zelda, what is the name of the hero you play as?":
        "Link is one of gaming's most enduring silent protagonists, with each game featuring a different incarnation of the legendary hero. Despite the series being called 'The Legend of Zelda,' you play as Link, not Zelda. His name was chosen because he serves as the 'link' between the player and the game world.",

    "In The Incredibles, what is the name of the baby who has multiple powers?":
        "Jack-Jack Parr appears powerless throughout most of the first Incredibles film, but reveals an astounding array of abilities in the climax and sequel: laser eyes, shapeshifting, teleportation, combustion, and more. His powers are unstable because he's too young to have settled on one ability. The raccoon fight scene in Incredibles 2 showcases his chaos brilliantly.",

    "What is the name of the main robot in the movie WALL-E?":
        "WALL-E (Waste Allocation Load Lifter Earth-Class) is the last functioning robot on an abandoned, garbage-covered Earth, spending 700 years compacting trash alone. His character was inspired by binoculars (his eyes) and conveyed entirely through sound design and animation, with almost no dialogue. Ben Burtt, who created R2-D2's sounds, voiced WALL-E.",

    "In Disney's Hercules, what is Hercules' love interest?":
        "Megara already appears in the Hercules T2 section. Her backstory of selling her soul to Hades for a faithless lover makes her uniquely jaded among Disney heroines. Susan Egan's world-weary delivery of 'I Won't Say I'm in Love' perfectly captures a woman afraid to be vulnerable again.",
}


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    trivia_path = os.path.join(script_dir, "questions", "trivia.json")

    with open(trivia_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Loaded {len(questions)} questions")

    matched = 0
    missing = []
    for q in questions:
        text = q["question"]
        if text in CONTEXTS:
            q["context"] = CONTEXTS[text]
            matched += 1
        else:
            missing.append(text)

    print(f"Matched: {matched}/{len(questions)}")
    if missing:
        print(f"MISSING {len(missing)} contexts:")
        for m in missing:
            print(f"  - {m}")

    with open(trivia_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(questions)} questions back to {trivia_path}")


if __name__ == "__main__":
    main()
