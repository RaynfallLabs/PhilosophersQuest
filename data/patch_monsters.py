"""Patch existing monsters.json to add max_level, treasure, and lore fields."""
import json

PATCHES = {
    "giant_rat": {
        "max_level": 4,
        "treasure": {"gold": [0, 3], "item_chance": 0.05, "item_tier": 1},
        "lore": "Giant rats infest the upper warrens of every dungeon, drawn by the smell of refuse and carrion. Their teeth can gnaw through wood and soft metals. While individually weak, they often swarm in packs and their bites can carry a mild fever."
    },
    "goblin": {
        "max_level": 5,
        "treasure": {"gold": [1, 6], "item_chance": 0.10, "item_tier": 1},
        "lore": "Goblins are small, cunning humanoids who lurk in the shallow tunnels near the dungeon's surface. They raid in packs, using numbers and traps to compensate for their lack of individual strength. Adventurers often find crude coins and stolen trinkets among their remains."
    },
    "grid_bug": {
        "max_level": 3,
        "treasure": {"gold": [0, 0], "item_chance": 0.0, "item_tier": 1},
        "lore": "Grid bugs are bizarre insectoid creatures that can only move in straight lines along invisible magical lattices. Their origin is unknown — some sages believe they are fragments of a broken spell matrix given physical form. They carry nothing of value."
    },
    "floating_eye": {
        "max_level": 6,
        "treasure": {"gold": [0, 5], "item_chance": 0.05, "item_tier": 1},
        "lore": "Floating eyes drift silently through dungeon corridors, their massive unblinking gaze capable of locking a creature in paralytic terror. They have no limbs or mouth, existing solely to observe. Sages believe they are the discarded sensors of some greater, unseen entity."
    },
    "bat": {
        "max_level": 4,
        "treasure": {"gold": [0, 2], "item_chance": 0.0, "item_tier": 1},
        "lore": "The giant bats of the deep cave networks are far more aggressive than their surface cousins. Their echolocation has evolved into a disorienting sonic pulse that scrambles the inner ear. Colonies roost in cavern ceilings, dropping on prey from above."
    },
    "cobra": {
        "max_level": 5,
        "treasure": {"gold": [0, 4], "item_chance": 0.05, "item_tier": 1},
        "lore": "Cave cobras have adapted to total darkness, developing pale scales and heat-sensing pits along their jawline. Their venom is more potent than their surface-dwelling kin. Alchemists prize cobra venom glands for antidote research."
    },
    "zombie": {
        "max_level": 6,
        "treasure": {"gold": [0, 5], "item_chance": 0.05, "item_tier": 1},
        "lore": "Zombies are the crudest form of undead — corpses reanimated by ambient necromantic energy or a careless spell. They shuffle toward the living with single-minded hunger, spreading disease through festering wounds. The disease they carry is believed to originate from the Plane of Rot."
    },
    "gelatinous_cube": {
        "max_level": 7,
        "treasure": {"gold": [5, 20], "item_chance": 0.30, "item_tier": 2},
        "lore": "Gelatinous cubes are semi-transparent oozes perfectly sized to fill dungeon corridors, acting as natural cleaning agents. They engulf and dissolve all organic matter, while indigestible items — coins, gems, weapons — remain suspended within their bodies. They are nearly invisible until they have already engulfed you."
    },
    "wraith": {
        "max_level": 9,
        "treasure": {"gold": [5, 15], "item_chance": 0.10, "item_tier": 2},
        "lore": "Wraiths are the spirits of the deeply corrupt, those whose evil was so profound that death could not contain them. They drain life force with a touch, leaving victims pale and weakened. Unlike ghosts, wraiths have no memory of their former lives — only an insatiable hunger for vitality."
    },
    "mimic": {
        "max_level": None,
        "treasure": {"gold": [10, 40], "item_chance": 0.50, "item_tier": 3},
        "lore": "Mimics are shapeshifting predators that disguise themselves as treasure chests, doors, or dungeon furnishings. Their digestive acid can dissolve iron. The oldest mimics have survived for centuries by perfecting their camouflage, accumulating wealth from victims who mistook them for a lucky find."
    },
    "leprechaun": {
        "max_level": 8,
        "treasure": {"gold": [20, 80], "item_chance": 0.60, "item_tier": 2},
        "lore": "Leprechauns are trickster fey who wander dungeons collecting gold. Their hexes scramble spatial perception, sending pursuers stumbling in random directions. They carry considerable wealth but spend more energy protecting it with illusions and curses than an honest warrior might spend on a sword."
    },
    "kobold": {
        "max_level": 4,
        "treasure": {"gold": [1, 5], "item_chance": 0.08, "item_tier": 1},
        "lore": "Kobolds are small draconic humanoids who worship dragons and mine the deep earth. What they lack in strength they compensate with elaborate traps and ambushes. Kobold warrens are riddled with pit traps, tripwires, and poisoned darts. Their obsession with dragon hoards makes them surprisingly good miners."
    },
    "cave_spider": {
        "max_level": 5,
        "treasure": {"gold": [0, 3], "item_chance": 0.05, "item_tier": 1},
        "lore": "Cave spiders spin invisible webs across dungeon passages, waiting motionless for days until prey stumbles through. Their venom causes progressive paralysis rather than immediate death — they prefer to consume prey alive. The silk they produce is of remarkable tensile strength."
    },
    "skeleton": {
        "max_level": 6,
        "treasure": {"gold": [1, 6], "item_chance": 0.08, "item_tier": 1},
        "lore": "Animated by residual necromantic magic, skeletons are the most common undead in the shallow dungeon levels. They retain no memory or personality, fighting until destroyed. Piercing weapons slip between their ribs, but slashing blows can shatter their bones."
    },
    "fire_beetle": {
        "max_level": 5,
        "treasure": {"gold": [0, 5], "item_chance": 0.10, "item_tier": 1},
        "lore": "Fire beetles store bioluminescent fuel in special glands behind their eyes and at their abdomen. In the wild, this light attracts mates; in the dungeon, they have evolved to project it defensively as a short-range ignition burst. Their glands remain potent for days after death."
    },
    "orc_scout": {
        "max_level": 5,
        "treasure": {"gold": [2, 10], "item_chance": 0.12, "item_tier": 1},
        "lore": "Orc scouts are the vanguard of larger warbands, sent ahead to map territory and eliminate weak prey. They travel light, relying on speed and surprise rather than heavy armor. Their tribal tattoos record their kills — a scout with many markings is especially dangerous."
    },
    "gnoll": {
        "max_level": 6,
        "treasure": {"gold": [3, 12], "item_chance": 0.15, "item_tier": 1},
        "lore": "Gnolls are hyena-headed humanoids who live to hunt and kill. Unlike orcs, they do not build settlements — they follow prey until it collapses, consuming everything including bone. Their laughter-like vocalizations signal a pack closing in for the kill."
    },
    "hobgoblin": {
        "max_level": 8,
        "treasure": {"gold": [5, 20], "item_chance": 0.20, "item_tier": 2},
        "lore": "Hobgoblins are the military aristocracy of the goblinoid races, disciplined and organized where their lesser kin are chaotic. They train in formation tactics and maintain strict hierarchies. A hobgoblin warband is a genuine military threat, capable of holding dungeon territory against much larger monsters."
    },
    "ghoul": {
        "max_level": 8,
        "treasure": {"gold": [2, 10], "item_chance": 0.10, "item_tier": 2},
        "lore": "Ghouls were once people — usually those who resorted to cannibalism in extremity. The curse of the ghoul transforms them fully, leaving them with an insatiable appetite for humanoid flesh. Their claws secrete a paralytic enzyme, allowing them to feed at leisure. They hoard the jewelry of victims in their lairs."
    },
    "dire_rat": {
        "max_level": 5,
        "treasure": {"gold": [0, 4], "item_chance": 0.05, "item_tier": 1},
        "lore": "Dire rats are the size of large dogs and far more aggressive than ordinary rats. Pack hunters, they coordinate attacks to overwhelm larger prey. Their teeth can sever fingers, and their bites often fester due to their filthy habits."
    },
    "acid_blob": {
        "max_level": 7,
        "treasure": {"gold": [3, 12], "item_chance": 0.20, "item_tier": 2},
        "lore": "Acid blobs are semi-intelligent oozes that secrete a powerful corrosive that dissolves metal and bone with equal efficiency. They leave trails of etched stone wherever they travel. Items found within a dead acid blob's mass are typically damaged but still recoverable."
    },
    "troll": {
        "max_level": 10,
        "treasure": {"gold": [10, 35], "item_chance": 0.25, "item_tier": 2},
        "lore": "Trolls are enormously resilient creatures whose flesh regenerates wounds almost as fast as they are inflicted. Only fire and acid can prevent regrowth. Dungeon trolls are larger and more aggressive than their surface kin, evolved in a world of constant violent competition. They hoard shiny objects without understanding their value."
    },
    "orc_warrior": {
        "max_level": 8,
        "treasure": {"gold": [5, 18], "item_chance": 0.18, "item_tier": 2},
        "lore": "Orc warriors are the backbone of orcish warbands, equipped with salvaged armor and brutal weapons. They fight with reckless aggression, bolstered by a cultural belief that dying in battle earns favor with their war-god. A cornered orc warrior fights with increased ferocity."
    },
    "dark_elf": {
        "max_level": None,
        "treasure": {"gold": [15, 50], "item_chance": 0.35, "item_tier": 3},
        "lore": "Dark elves — drow — are exiles from the surface world who have built a civilization in the deepest tunnels. Their magic is potent but their iron corrodes rapidly in surface air. Drow who venture into the upper dungeon are typically scouts, assassins, or outcasts from even their own cruel society."
    },
    "wight": {
        "max_level": 10,
        "treasure": {"gold": [8, 25], "item_chance": 0.15, "item_tier": 2},
        "lore": "Wights are powerful undead who retain some semblance of their former intelligence, making them more dangerous than mindless skeletons. They dwell in ancient burial mounds and ruined fortresses, commanding lesser undead. Their touch drains life force, and those slain by a wight often rise as undead themselves."
    },
    "rust_monster": {
        "max_level": 8,
        "treasure": {"gold": [0, 8], "item_chance": 0.05, "item_tier": 1},
        "lore": "Rust monsters are the terror of armored adventurers — their antenna touch causes ferrous metal to instantly corrode into worthless flakes. They are not aggressive by nature, seeking metal to consume rather than flesh. A dungeon where rust monsters dwell is stripped of iron fixtures."
    },
    "cave_bear": {
        "max_level": 7,
        "treasure": {"gold": [0, 8], "item_chance": 0.08, "item_tier": 1},
        "lore": "Cave bears are massive omnivores that dominate middle dungeon levels the way brown bears dominate forests. Enormously strong and highly territorial, they attack with a devastating combination of claws and bite. Their hides are prized by tanners for exceptional thickness and warmth."
    },
    "ogre": {
        "max_level": 9,
        "treasure": {"gold": [10, 40], "item_chance": 0.25, "item_tier": 2},
        "lore": "Ogres are brutish giants standing eight feet tall, motivated primarily by hunger and the desire to smash things. Despite their dim intellect, they are cunning enough to set ambushes and use improvised weapons effectively. Ogre warrens are identified by the smell — they hoard food alongside stolen goods."
    },
    "shadow": {
        "max_level": 9,
        "treasure": {"gold": [3, 12], "item_chance": 0.08, "item_tier": 2},
        "lore": "Shadows are incorporeal undead that drain strength from living creatures, growing more solid with each point of ability they steal. They lurk in dark corners and beneath furniture, indistinguishable from ordinary shadows until they move. A person drained to zero Strength by a shadow rises as a shadow themselves."
    },
    "mummy": {
        "max_level": 11,
        "treasure": {"gold": [15, 60], "item_chance": 0.40, "item_tier": 3},
        "lore": "Mummies are the preserved dead of ancient kings and priests, animated to guard tomb treasures for eternity. Their rotted bandages carry a supernatural disease — mummy rot — that resists natural healing. The curse they carry is linked to the original embalming rites; defeating the mummy that placed it can lift the curse."
    },
    "giant_spider": {
        "max_level": 8,
        "treasure": {"gold": [0, 10], "item_chance": 0.12, "item_tier": 2},
        "lore": "Giant spiders of the deep dungeon grow to the size of horses, spinning massive orb webs that span entire corridors. Their venom is fast-acting and powerful. Victims they do not immediately consume are wrapped in silk and stored for later — the cocoons often contain items from previous adventurers."
    },
    "ettin": {
        "max_level": 12,
        "treasure": {"gold": [15, 50], "item_chance": 0.25, "item_tier": 3},
        "lore": "Ettins are two-headed giants whose dual consciousnesses argue constantly about everything — including combat tactics. This gives them the ability to attack and defend simultaneously, never truly caught off-guard. Their lairs are littered with the remains of meals and the occasional intact trophy from a memorable fight."
    },
    "manticore": {
        "max_level": 12,
        "treasure": {"gold": [20, 70], "item_chance": 0.30, "item_tier": 3},
        "lore": "Manticores have the body of a lion, the wings of a dragon, and a barbed tail that launches volleys of spikes with deadly precision. Persian scholars describe them as the perfect predator, a creature that can fight at range or close quarters equally well. They relish the taste of human flesh above all other prey."
    },
    "specter": {
        "max_level": 12,
        "treasure": {"gold": [5, 20], "item_chance": 0.08, "item_tier": 3},
        "lore": "Specters are more powerful than wraiths, incorporeal undead who have burned away all remnants of their former personality in their hunger for life force. They can pass through solid stone. The dread cold that precedes a specter's arrival lowers ambient temperature by several degrees — a useful warning sign."
    },
    "basilisk": {
        "max_level": 12,
        "treasure": {"gold": [10, 35], "item_chance": 0.20, "item_tier": 3},
        "lore": "The basilisk's eight-eyed gaze carries petrification magic — sustained eye contact will turn flesh to stone within seconds. The dungeon basilisk is smaller than the legendary surface variety but equally deadly. Their stone-form victims litter their lairs, sometimes still in postures of final surprise."
    },
    "chimera": {
        "max_level": None,
        "treasure": {"gold": [30, 100], "item_chance": 0.40, "item_tier": 4},
        "lore": "The chimera is a magical aberration with the body of a lion, the head of a goat, and a serpentine tail. Its goat head breathes fire, its lion head bites, and its tail delivers venomous strikes. Ancient texts describe chimeras as failed divine experiments — amalgams of multiple beasts fused by careless magic."
    },
    "minotaur": {
        "max_level": 13,
        "treasure": {"gold": [20, 70], "item_chance": 0.35, "item_tier": 3},
        "lore": "Minotaurs are the cursed offspring of divine punishment, possessing a bull's head and enormous strength in a humanoid body. They possess perfect spatial memory, never becoming lost in labyrinths they know. Dungeon minotaurs are often solitary, claiming entire sections of dungeon as their territory and marking passages with the remains of intruders."
    },
    "frost_crawler": {
        "max_level": 9,
        "treasure": {"gold": [5, 20], "item_chance": 0.12, "item_tier": 2},
        "lore": "Frost crawlers are centipede-like creatures from the frozen sub-levels, their exoskeleton covered in natural ice crystals. They secrete a supercooled slime that flash-freezes flesh on contact. Their lair temperatures drop noticeably below ambient — dungeon explorers use this cold draft as a warning."
    },
    "medusa": {
        "max_level": None,
        "treasure": {"gold": [40, 130], "item_chance": 0.55, "item_tier": 4},
        "lore": "The medusa is a serpent-haired horror whose gaze turns flesh to stone. Greek myth held that only one existed, but dungeon scholars have catalogued several varieties. They are cunning and use their collection of stone victims as both decoration and tactical concealment. Blind adventurers are immune to their primary ability."
    },
    "vampire_spawn": {
        "max_level": 12,
        "treasure": {"gold": [15, 50], "item_chance": 0.25, "item_tier": 3},
        "lore": "Vampire spawn are newly turned vampires who have not yet mastered their powers. They serve their sire as thralls, hunting on command. Unlike true vampires they cannot transform into mist or animals. Their drain attack is weaker than a full vampire's but they are more numerous and easier to encounter."
    },
    "fire_elemental": {
        "max_level": 13,
        "treasure": {"gold": [10, 40], "item_chance": 0.15, "item_tier": 3},
        "lore": "Fire elementals are fragments of the Elemental Plane of Fire summoned or drawn through planar weak points in volcanic dungeon sections. They burn with intense heat that ignites everything they touch. They cannot enter water and are confused by cold spells that partially extinguish their flames."
    },
    "earth_elemental": {
        "max_level": 13,
        "treasure": {"gold": [10, 40], "item_chance": 0.15, "item_tier": 3},
        "lore": "Earth elementals rise from dungeon floors as walking masses of stone and compressed soil. They move through rock as easily as a fish through water, ambushing from below. Their immense weight makes them devastating in close combat but slow to pursue a fleeing target across open ground."
    },
    "storm_elemental": {
        "max_level": 14,
        "treasure": {"gold": [15, 50], "item_chance": 0.20, "item_tier": 3},
        "lore": "Storm elementals crackle with contained lightning and howling winds, drawn to the deep dungeon by resonant geomantic currents. Their strikes discharge static electricity that chains between metal objects. Metal armor actually increases one's vulnerability to their attacks — a fact armored adventurers learn painfully."
    },
    "lich_apprentice": {
        "max_level": 14,
        "treasure": {"gold": [25, 80], "item_chance": 0.40, "item_tier": 3},
        "lore": "A lich apprentice is a mage who has begun the terrible transformation into lichdom but has not completed the phylactery ritual. They retain enough life to feel pain but enough undeath to ignore most of it. They serve more powerful liches in exchange for the secret of immortality, a secret their master has no intention of sharing."
    },
    "mind_flayer": {
        "max_level": None,
        "treasure": {"gold": [40, 130], "item_chance": 0.50, "item_tier": 4},
        "lore": "Mind flayers are tentacled horror from the deep places, sustained entirely by consuming the brains of sentient beings. Their psychic blast can scramble thought itself. An ancient mind flayer city is said to exist in the deepest dungeon levels, its architecture built from the calcified remains of thousands of victims."
    },
    "vampire": {
        "max_level": None,
        "treasure": {"gold": [50, 180], "item_chance": 0.60, "item_tier": 4},
        "lore": "True vampires are among the most dangerous undead — immortal predators who have refined their hunting over centuries. They can transform into mist, command wolves and bats, and regenerate damage rapidly outside of sunlight. Each vampire has a personality and agenda; most are collecting power as obsessively as they once collected gold."
    },
    "death_knight": {
        "max_level": None,
        "treasure": {"gold": [60, 200], "item_chance": 0.65, "item_tier": 4},
        "lore": "Death knights are the accursed remains of paladins who fell from grace so completely that even death rejected them. They retain their martial skill and gain dark magic, forced to serve whatever dark power claimed their soul. Their hellfire swords are a mark of their eternal damnation — they cannot remove them."
    },
    "bone_golem": {
        "max_level": 14,
        "treasure": {"gold": [10, 35], "item_chance": 0.20, "item_tier": 3},
        "lore": "Bone golems are constructs assembled from the skeletons of multiple creatures, held together by necromantic binding. Unlike undead, they have no animus of their own — they execute commands mechanically. Their disjointed anatomy makes them eerily resistant to cutting weapons; the bones simply separate and reconnect."
    },
    "greater_demon": {
        "max_level": None,
        "treasure": {"gold": [50, 160], "item_chance": 0.55, "item_tier": 4},
        "lore": "Greater demons are powerful entities of the Abyss, drawn to the material plane by large-scale evil or summoning rituals. They are not merely powerful — they are willfully cruel, seeking to corrupt and destroy with equal enthusiasm. Their very presence twists reality; flowers wilt and children cry at their passing."
    },
    "young_dragon": {
        "max_level": 15,
        "treasure": {"gold": [40, 150], "item_chance": 0.55, "item_tier": 3},
        "lore": "Young dragons are already more dangerous than most dungeon denizens despite not yet reaching their full potential. They collect treasure obsessively, a drive that begins in youth and never diminishes. A young dragon's hoard is modest compared to an adult's but still represents considerable wealth accumulated through violence."
    },
    "beholder": {
        "max_level": None,
        "treasure": {"gold": [60, 200], "item_chance": 0.65, "item_tier": 4},
        "lore": "Beholders are aberrations of alien intelligence, their spherical bodies covered in eyestalks each projecting a different magical ray. They are deeply paranoid, trusting no one — not even others of their own kind. Beholder lairs contain the petrified, charmed, or disintegrated remains of everyone they have ever met."
    },
    "vampire_lord": {
        "max_level": None,
        "treasure": {"gold": [100, 400], "item_chance": 0.80, "item_tier": 5},
        "lore": "A vampire lord has survived for a millennium or more, accumulating power, wealth, and influence across the mortal world. They control vast networks of thralls and spawn, and their castle or lair typically occupies an entire dungeon level. They regard adventurers as momentary amusements or potential additions to their collection."
    },
    "lich": {
        "max_level": None,
        "treasure": {"gold": [80, 280], "item_chance": 0.70, "item_tier": 5},
        "lore": "A lich is a wizard who achieved immortality through a dark ritual, binding their soul to a phylactery. They cannot be permanently destroyed while the phylactery survives. Centuries of study have made liches extraordinarily powerful; decades of undeath have stripped away their humanity, leaving only intellect and ambition."
    },
    "adult_dragon": {
        "max_level": None,
        "treasure": {"gold": [150, 500], "item_chance": 0.75, "item_tier": 4},
        "lore": "Adult dragons are calculating predators who have lived long enough to understand strategy, politics, and the value of reputation. Their hoard is not merely accumulated wealth but a carefully curated collection representing centuries of domination. They often know exactly what every item in their hoard is and how it was taken."
    },
    "iron_golem": {
        "max_level": None,
        "treasure": {"gold": [20, 60], "item_chance": 0.25, "item_tier": 4},
        "lore": "Iron golems are the masterwork of the golem-maker's art — eight feet of animated metal, immune to fire, magic, and most physical harm. They breathe toxic gas from their forge-heated interiors. Built to guard powerful mages' vaults, they continue their work long after their creators have died of old age."
    },
    "greater_lich": {
        "max_level": None,
        "treasure": {"gold": [150, 500], "item_chance": 0.80, "item_tier": 5},
        "lore": "A greater lich has transcended even the elevated power of standard liches, their magical ability grown so immense that reality bends in their presence. They have had centuries to perfect their phylactery's hiding place. Many have become interested in philosophical or arcane problems too abstract for mortal minds to comprehend."
    },
    "arch_demon": {
        "max_level": None,
        "treasure": {"gold": [100, 350], "item_chance": 0.75, "item_tier": 5},
        "lore": "An arch-demon rules a layer of the Abyss, commanding millions of lesser demons. When one descends to the material plane, it is fulfilling a plan centuries in the making. They are nearly impossible to banish without knowledge of their true name, which they guard with obsessive care."
    },
    "ancient_dragon": {
        "max_level": None,
        "treasure": {"gold": [300, 1000], "item_chance": 0.90, "item_tier": 5},
        "lore": "Ancient dragons are among the oldest intelligent beings on the material plane. They have watched kingdoms rise and fall, and their accumulated knowledge rivals any library. Their hoard contains items of historical significance as much as monetary value. Meeting one is either the greatest opportunity or greatest danger an adventurer will ever face."
    },
    "ancient_lich": {
        "max_level": None,
        "treasure": {"gold": [200, 700], "item_chance": 0.85, "item_tier": 5},
        "lore": "An ancient lich has persisted for thousands of years, their original mortal identity long since dissolved in millennia of undead existence. They have achieved magical understanding that makes even other liches look like apprentices. Their phylactery is typically hidden in a demiplane of their own creation."
    },
    "death_lord": {
        "max_level": None,
        "treasure": {"gold": [200, 800], "item_chance": 0.90, "item_tier": 5},
        "lore": "Death lords are the apex of the undead hierarchy — beings who have transcended individual undeath to embody the concept of death itself. They command the obedience of all lesser undead within miles of their presence. Ancient texts describe them as heralds of an End that has not yet come."
    },
    "chaos_spawn": {
        "max_level": None,
        "treasure": {"gold": [50, 150], "item_chance": 0.45, "item_tier": 4},
        "lore": "Chaos spawns are the physical manifestation of raw entropic energy, their form shifting constantly between states. No two look alike and they change even as you fight them. Philosophers debate whether chaos spawns have consciousness or are simply self-organizing patterns of disorder given temporary solidity."
    },
    "soul_eater": {
        "max_level": None,
        "treasure": {"gold": [40, 120], "item_chance": 0.35, "item_tier": 4},
        "lore": "Soul eaters are entities from a plane adjacent to death, sustained by consuming the animating essence of living beings. A creature whose soul is devoured cannot be resurrected by ordinary means. They are drawn to high concentrations of life force — adventurers deep in dungeons represent exceptionally attractive prey."
    },
    "orc_shaman": {
        "max_level": 10,
        "treasure": {"gold": [15, 45], "item_chance": 0.35, "item_tier": 2},
        "lore": "Orc shamans channel the dark blessings of their tribal deity, bolstering warband members and hurling curses at enemies. They are respected and feared within orcish society — only the warchief has more authority. Their ritual tattoos glow with eldritch energy during combat."
    },
    "giant_centipede": {
        "max_level": 8,
        "treasure": {"gold": [0, 5], "item_chance": 0.05, "item_tier": 1},
        "lore": "Giant centipedes are common throughout the dungeon's middle levels, their hundreds of legs moving with disturbing speed. Their venom causes intense burning pain that disrupts concentration. Alchemists use centipede venom in paralytic preparations, but extracting it from a living specimen is extremely dangerous."
    },
    "skeletal_archer": {
        "max_level": 8,
        "treasure": {"gold": [2, 10], "item_chance": 0.10, "item_tier": 2},
        "lore": "Skeletal archers are the reanimated remains of warriors who were skilled with the bow in life. The necromantic animation preserves their martial memory, allowing them to draw and fire with mechanical precision. They prefer to maintain distance, riddling targets with arrows before retreating behind their melee companions."
    },
    "cave_toad": {
        "max_level": 7,
        "treasure": {"gold": [0, 5], "item_chance": 0.05, "item_tier": 1},
        "lore": "Cave toads have evolved in the absolute darkness of underground lakes and flooded passages. Their swollen glands secrete a powerful hallucinogen as a defensive measure. Dungeon explorers who mistake them for food sources experience vivid, sometimes permanent, sensory alterations."
    },
    "brigand": {
        "max_level": 8,
        "treasure": {"gold": [8, 30], "item_chance": 0.25, "item_tier": 2},
        "lore": "Brigands are former soldiers, escaped criminals, or simply desperate people who have turned to dungeon raiding and banditry. Unlike monsters, they have actual combat training and equipment. Some brigand bands have claimed entire dungeon sections as territory, extorting passing adventurers or simply killing them."
    },
    "shadow_hound": {
        "max_level": 10,
        "treasure": {"gold": [0, 8], "item_chance": 0.05, "item_tier": 2},
        "lore": "Shadow hounds are canine predators partially displaced into the Shadow Plane, their bodies semi-transparent and cold to the touch. They can step through solid objects briefly to bypass obstacles or flank prey. Their howl causes existential dread — adventurers who hear it often report feeling suddenly alone in all the universe."
    },
    "flesh_golem": {
        "max_level": 12,
        "treasure": {"gold": [10, 30], "item_chance": 0.20, "item_tier": 3},
        "lore": "Flesh golems are patchwork constructs assembled from the bodies of multiple humanoids, animated by lightning and necromantic science. The creator's manual warns that a flesh golem occasionally rebels if its animating intelligence coalesces into something resembling grief. Their berserk episodes are legendary among golem artificers."
    },
    "harpy": {
        "max_level": 9,
        "treasure": {"gold": [10, 35], "item_chance": 0.25, "item_tier": 2},
        "lore": "Harpies are winged women-creatures from Greek myth, their lower bodies those of great birds of prey. Their enchanting song lures victims to walk heedlessly toward danger. Despite their magical ability, they are filthy and cruel by nature — their nesting sites are identifiable by smell alone."
    },
    "necromancer_apprentice": {
        "max_level": 11,
        "treasure": {"gold": [20, 60], "item_chance": 0.40, "item_tier": 3},
        "lore": "A necromancer's apprentice has learned enough dark magic to animate lesser undead and hurl bolts of necrotic energy, but has not yet achieved the mastery to safely attempt lichdom. They typically follow a senior necromancer, performing the gruesome preparatory work their master finds beneath their dignity."
    }
}

def main():
    with open('data/monsters.json', encoding='utf-8') as f:
        data = json.load(f)

    updated = 0
    for monster_id, patch in PATCHES.items():
        if monster_id not in data:
            print(f"WARNING: {monster_id} not found in monsters.json")
            continue
        for key, value in patch.items():
            if key not in data[monster_id]:
                data[monster_id][key] = value
                updated += 1
            # Only add if missing — don't overwrite existing values

    with open('data/monsters.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Patched {len(PATCHES)} monsters, added {updated} new fields.")

if __name__ == '__main__':
    main()
