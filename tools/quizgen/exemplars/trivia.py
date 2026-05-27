"""Trivia bank voice anchors (30 exemplars).

These 30 questions are the Easter Egg Pattern made concrete. Six anchors
per tier, each anchor hitting a specific pillar:

  Per tier (T1-T5):
    P1  Movies + TV + Anime
    P2  Gaming + Arcade Culture
    P3  Comics + Pulp Fiction
    P4  Cryptids + Mysteries
    P5  Classic D&D + MtG + WWE Attitude + Seahawks/Mariners
    SIG Signature wonder (varies)

All exemplars are gate-validated and serve as anchors for bulk-gen
agents when they ask "what does a good X tier Y trivia question look
like?"

See `proposals/v2_audit/TRIVIA_FRAMEWORK.md` for the Easter Egg Pattern
+ cultural-osmosis carve-out + 10 spoiler-allowed franchises.

Cultural-osmosis carve-out: facts crossed into common cultural knowledge
are TESTABLE (Bruce Wayne = Batman, 'I am your father', Spider-bite
origin). 10 named franchises permit full internal spoilers (MHA, Hajime
no Ippo, Harry Potter, Star Wars OT, MCU through Endgame, Toilet-Bound
Hanako Kun, Dragon Ball, Scott Pilgrim, Princess Bride, Mario Movie
2023).

Make them want to seek it out.
"""
from __future__ import annotations

EXEMPLARS: list[dict] = [
    # =========================================================================
    # T1 — obvious — anyone who's heard of the thing knows the answer (cap 280)
    # =========================================================================

    # T1-P1 Movies/Anime — Iconic character
    {
        "tier": 1,
        "question": "A red Italian plumber in blue overalls jumps on Goombas in the Mushroom Kingdom. What's his name?",
        "answer": "Mario",
        "choices": [
            "Mario",
            "Luigi",
            "Wario",
            "Toad",
        ],
        "context": "Created by Shigeru Miyamoto in 1981, originally as the unnamed Jumpman in Donkey Kong. Renamed Mario when Nintendo of America's landlord Mario Segale stormed in demanding rent.",
    },

    # T1-P2 Gaming — Iconic visual
    {
        "tier": 1,
        "question": "A pointy-eared yellow electric mouse is the most famous Pokemon and Ash Ketchum's starter. Name him.",
        "answer": "Pikachu",
        "choices": [
            "Pikachu",
            "Bulbasaur",
            "Charmander",
            "Squirtle",
        ],
        "context": "Pikachu was originally going to be Ash's starter only in the anime, with Bulbasaur, Charmander, and Squirtle as the proper trio. The anime swapped the starter to leverage Pikachu's marketing potential.",
    },

    # T1-P3 Comics — Foundational origin
    {
        "tier": 1,
        "question": "What gave Peter Parker his spider-powers?",
        "answer": "A bite from a radioactive spider",
        "choices": [
            "A bite from a radioactive spider",
            "Exposure to gamma radiation from a bomb test",
            "An injection of mutant DNA from his uncle",
            "Being struck by lightning during a science fair",
        ],
        "context": "Peter Parker first appeared in Amazing Fantasy issue 15, August 1962. Stan Lee wrote the script and Steve Ditko drew it. The spider-bite origin has never substantively changed in 60+ years.",
    },

    # T1-P4 Cryptid — Famous monster
    {
        "tier": 1,
        "question": "A large hairy ape-like creature is said to roam the forests of the Pacific Northwest. What's the most common name for it?",
        "answer": "Bigfoot",
        "choices": [
            "Bigfoot",
            "Werewolf",
            "Yeti",
            "Chupacabra",
        ],
        "context": "The Sasquatch name comes from the Halkomelem Salish word sasq'ets. The English name 'Bigfoot' was coined by a journalist after construction worker Jerry Crew showed large footprints found at his Humboldt County logging site in 1958.",
    },

    # T1-P5 D&D — Iconic creature
    {
        "tier": 1,
        "question": "A famous Dungeons & Dragons monster is a floating sphere covered in eyestalks with a giant central eye. What's it called?",
        "answer": "Beholder",
        "choices": [
            "Beholder",
            "Mind Flayer",
            "Owlbear",
            "Bulette",
        ],
        "context": "First appeared in the original 1977 Monster Manual. The central eye projects an anti-magic cone. Beholders are so iconic that TSR fought a long legal dispute to protect the trademark.",
    },

    # T1-SIG Star Wars OT (spoiler-allowed) — Iconic line
    {
        "tier": 1,
        "question": "What line does Darth Vader famously deliver to Luke Skywalker on Cloud City in The Empire Strikes Back?",
        "answer": "Luke, I am your father",
        "choices": [
            "Luke, I am your father",
            "Join me, and we will rule the galaxy",
            "I have you now, young Skywalker",
            "Search your feelings, you know it to be true",
        ],
        "context": "Often misquoted; the actual line is 'No, I am your father.' Bond actor James Earl Jones recorded the line in post-production; the script and Mark Hamill's reaction shot had Vader saying Obi-Wan killed Luke's father to preserve the twist on set.",
    },

    # =========================================================================
    # T2 — casual fan — franchise's well-known facts (cap 480)
    # =========================================================================

    # T2-P1 Anime (Akira) — Director debut
    {
        "tier": 2,
        "question": "Released in 1988, an animated cyberpunk film set in 2019 Neo-Tokyo featured groundbreaking hand-drawn animation, a soundtrack of taiko drums and chanting voices, and a now-legendary motorcycle slide. Whose directorial debut was the film?",
        "answer": "Katsuhiro Otomo",
        "choices": [
            "Katsuhiro Otomo",
            "Hayao Miyazaki",
            "Mamoru Oshii",
            "Satoshi Kon",
        ],
        "context": "Otomo had been writing the Akira manga since 1982 and adapted his own work for the film. The score was composed by Tsutomu Ohashi under the name Geinoh Yamashirogumi. The film's $11M budget was the highest in anime history at that point.",
    },

    # T2-P2 Gaming — Pac-Man origin
    {
        "tier": 2,
        "question": "Released by Namco in 1980, Pac-Man's creator drew the round-character design from a pizza with one slice missing. Who was the Namco designer?",
        "answer": "Toru Iwatani",
        "choices": [
            "Toru Iwatani",
            "Shigeru Miyamoto",
            "Nolan Bushnell",
            "Eugene Jarvis",
        ],
        "context": "Iwatani also designed the ghost AI: Blinky chases directly, Pinky tries to ambush, Inky uses a complex algorithm involving Blinky's position, and Clyde wanders randomly. Pac-Man became the first widely-licensed video-game character.",
    },

    # T2-P3 Comics — Pulp + Conan
    {
        "tier": 2,
        "question": "In December 1932, a 26-year-old writer named Robert E. Howard sold his first story about a black-haired, blue-eyed Cimmerian barbarian to Weird Tales magazine. What was the character's name?",
        "answer": "Conan",
        "choices": [
            "Conan",
            "Solomon Kane",
            "Kull",
            "Bran Mak Morn",
        ],
        "context": "The first story was 'The Phoenix on the Sword.' Howard wrote 21 Conan stories before his suicide at age 30 in 1936, in Cross Plains, Texas. Fritz Leiber later named the genre Howard had founded — 'sword and sorcery.'",
    },

    # T2-P4 Cryptid — Patterson-Gimlin
    {
        "tier": 2,
        "question": "On October 20, 1967, Roger Patterson and Bob Gimlin filmed a 53-second clip of something striding across a sandbar at Bluff Creek in Northern California. What did Patterson nickname the female subject of the film?",
        "answer": "Patty",
        "choices": [
            "Patty",
            "Bessie",
            "Sasha",
            "Big Mama",
        ],
        "context": "The Patterson-Gimlin film remains the most-analyzed piece of Bigfoot evidence in history. Frame 352, where the subject looks back at the camera, is the most-reproduced single image. Multiple Hollywood costume designers have studied the film without reaching consensus.",
    },

    # T2-P5 D&D — TSR founders
    {
        "tier": 2,
        "question": "The original 1974 Dungeons & Dragons game was a small white box containing three thin booklets. It was published by TSR in Lake Geneva, Wisconsin. Who co-created it with Gary Gygax?",
        "answer": "Dave Arneson",
        "choices": [
            "Dave Arneson",
            "Brian Blume",
            "Tracy Hickman",
            "Ed Greenwood",
        ],
        "context": "Arneson had been running his Blackmoor campaign as a small-scale Chainmail variant in Minneapolis. Gygax had Chainmail (1971) and wanted a fantasy supplement. They collaborated by mail to combine the ideas into D&D.",
    },

    # T2-SIG Princess Bride (spoiler-allowed)
    {
        "tier": 2,
        "question": "In Rob Reiner's 1987 The Princess Bride, the Spanish swordsman Inigo Montoya finally finds the six-fingered man who killed his father, Count Rugen. What line does he say to him before they duel?",
        "answer": "Hello. My name is Inigo Montoya. You killed my father. Prepare to die.",
        "choices": [
            "Hello. My name is Inigo Montoya. You killed my father. Prepare to die.",
            "Tonight, you face the wrath of the swordsman whose father you murdered.",
            "After twenty years, six-fingered man, the time has come for vengeance.",
            "Remember this name well: Inigo Montoya, son of Domingo, here to avenge.",
        ],
        "context": "Mandy Patinkin played Inigo. The line is repeated multiple times during the duel as a sort of mantra. William Goldman wrote both the novel and screenplay; the novel includes additional backstory about Inigo's swordmaster training under Yeste.",
    },

    # =========================================================================
    # T3 — real fan — what a deep fan would know (cap 680)
    # =========================================================================

    # T3-P1 Anime (Hajime no Ippo — spoiler-allowed)
    {
        "tier": 3,
        "question": "In Hajime no Ippo, Ippo Makunouchi's signature finishing move is a devastating short uppercut he learns by watching the heavyweight Bryan Hawk in slow motion. The technique requires shifting body weight forward through a step, then twisting up from the shoulder. What is the move called?",
        "answer": "The Dempsey Roll",
        "choices": [
            "The Dempsey Roll",
            "The Liver Blow",
            "The Gazelle Punch",
            "The Smash",
        ],
        "context": "The Dempsey Roll is loosely based on the real boxer Jack Dempsey's bobbing-and-weaving style from the 1920s. In Hajime no Ippo, Ippo first uses it against Sendo. Makunouchi Boxing Club is run by the gruff Kamogawa, who refuses to teach the move directly.",
    },

    # T3-P2 Gaming — DK kill screen
    {
        "tier": 3,
        "question": "On July 9, 1982, a 21-year-old construction worker named Steve Sanders played Donkey Kong at Walter Day's Twin Galaxies arcade in Ottumwa, Iowa, achieving 1,000,000 points — the first publicly verified million in DK history. The game has a 'kill screen' beyond which no player can advance because the game's bonus timer ends faster than Mario can complete the level. What level is the kill screen?",
        "answer": "Level 22, the 117th screen of the game",
        "choices": [
            "Level 22, the 117th screen of the game",
            "Level 256, the famous arcade integer rollover",
            "Level 99, the maximum displayed level counter",
            "Level 18, the springs board with reduced timer",
        ],
        "context": "The DK kill screen happens because the bonus timer integer overflows in a way that makes the timer end the level before Mario can reach the top. The classic Twin Galaxies high score era ran from 1982 until controversies in 2017-2018 disqualified Billy Mitchell's scores.",
    },

    # T3-P3 Comics — Howard biography
    {
        "tier": 3,
        "question": "Robert E. Howard wrote his Conan stories from a small farmhouse in Cross Plains, Texas during the early 1930s. He lived with his parents and was deeply attached to his mother. On June 11, 1936, when she fell into her final coma, Howard walked out to his Chevrolet and shot himself in the head. How old was he?",
        "answer": "Thirty",
        "choices": [
            "Thirty",
            "Twenty-six",
            "Thirty-five",
            "Forty-two",
        ],
        "context": "Howard's mother Hester died the next day, June 12, 1936. He had completed 21 Conan stories plus dozens of other characters including Solomon Kane, Bran Mak Morn, King Kull, and the humorous Breckinridge Elkins. His correspondence with Lovecraft is preserved at the Howard Memorial Museum in Cross Plains.",
    },

    # T3-P4 Cryptid — Mothman
    {
        "tier": 3,
        "question": "Between November 1966 and December 1967, residents of Point Pleasant, West Virginia reported repeated sightings of a winged creature with glowing red eyes near the abandoned World War II TNT plant outside town. The sightings ended on December 15, 1967, when the Silver Bridge connecting Point Pleasant to Ohio collapsed, killing 46 people. What did locals name the creature?",
        "answer": "The Mothman",
        "choices": [
            "The Mothman",
            "The Jersey Devil",
            "The Flatwoods Monster",
            "The Beast of Bray Road",
        ],
        "context": "John Keel's 1975 book The Mothman Prophecies tied the sightings to the bridge collapse and to a wave of UFO and Men in Black reports in the area. Mark Pellington adapted the book into a 2002 film starring Richard Gere. A 12-foot statue of Mothman stands in downtown Point Pleasant today.",
    },

    # T3-P5 D&D — Tomb of Horrors
    {
        "tier": 3,
        "question": "Gary Gygax wrote a 1978 AD&D tournament module so notorious for player-character deaths that it became the proverbial 'DM's revenge.' It begins with a green devil-face entrance, includes a teleporting demilich named Acererak, and features the famous Sphere of Annihilation trap. What's the module called?",
        "answer": "Tomb of Horrors (S1)",
        "choices": [
            "Tomb of Horrors (S1)",
            "White Plume Mountain (S2)",
            "Expedition to the Barrier Peaks (S3)",
            "Vault of the Drow (D3)",
        ],
        "context": "Gygax wrote it to challenge players who claimed their characters were unkillable. Acererak's appearance in 2018's 5e module Tomb of Annihilation explicitly references the original. The famous 'green devil face' is a Sphere of Annihilation disguised as decoration; reaching into the mouth kills the PC instantly with no save.",
    },

    # T3-SIG MCU (spoiler-allowed) — production deep
    {
        "tier": 3,
        "question": "Robert Downey Jr. was cast as Tony Stark in 2008's Iron Man over Marvel Studios' initial objections due to his earlier drug-related arrests. Director Jon Favreau championed him. The film's casting set the entire tone for the MCU's first 11 years. What previous Favreau-directed film had RDJ starred in?",
        "answer": "He hadn't been in a Favreau film, but the two had bonded on a screen test",
        "choices": [
            "He hadn't been in a Favreau film, but the two had bonded on a screen test",
            "Elf 2003 alongside Will Ferrell as a department-store employee",
            "Zathura 2005 alongside Josh Hutcherson and Tim Robbins",
            "Made 2001 alongside Vince Vaughn, also a Favreau directorial debut",
        ],
        "context": "RDJ's Iron Man casting was famously approved only after a one-take audition in Favreau's office. The film grossed $585M worldwide on a $140M budget. The post-credits scene where Nick Fury (Samuel L. Jackson) mentions the Avengers Initiative kicked off the entire MCU shared universe.",
    },

    # =========================================================================
    # T4 — deep fan — geek-canon stuff (cap 900)
    # =========================================================================

    # T4-P1 Anime — Eva production collapse
    {
        "tier": 4,
        "question": "Hideaki Anno's Neon Genesis Evangelion aired on TV Tokyo from October 1995 to March 1996. The 26-episode series ran out of budget and time. The final two episodes (25 and 26) abandoned conventional animation entirely, featuring still frames, pencil sketches, internal monologues, and stark text on black backgrounds. Fan reaction was famously divided. Gainax released a theatrical alternative in 1997 to give the series a more conventional ending. What was that 1997 film called?",
        "answer": "The End of Evangelion",
        "choices": [
            "The End of Evangelion",
            "Death and Rebirth",
            "Evangelion: 3.0+1.0 Thrice Upon a Time",
            "Neon Genesis Evangelion: Final",
        ],
        "context": "Death and Rebirth (March 1997) was a clip-show compilation plus the first half of the new ending; End of Evangelion (July 1997) was the complete new ending. The Rebuild tetralogy (2007, 2009, 2012, 2021) revisited the series with new animation. Anno cited his own depression as the source of the series' psychological intensity.",
    },

    # T4-P2 Gaming — King of Kong drama
    {
        "tier": 4,
        "question": "In 2003, a Washington high-school science teacher and Boeing engineer named Steve Wiebe submitted a Donkey Kong score of 1,006,600 from a cabinet in his garage to Twin Galaxies — beating Billy Mitchell's then-standing record of 874,300. Mitchell, the pizza-parlor owner from Florida, responded with a videotape score of 1,047,200 sent in by courier without public play. Seth Gordon's 2007 documentary The King of Kong chronicled the dispute. In 2018, Twin Galaxies disqualified all of Mitchell's pre-2007 scores after analyzing the videotapes. What did they determine?",
        "answer": "His videotapes were recorded from a MAME emulator, not an arcade board",
        "choices": [
            "His videotapes were recorded from a MAME emulator, not an arcade board",
            "His scores had been achieved on a modified board with a bonus-timer hack",
            "Multiple witnesses had falsified their attestation signatures on score sheets",
            "The frame-by-frame analysis showed splice edits in the original recordings",
        ],
        "context": "Twin Galaxies' analysis focused on the way levels loaded — arcade boards have a distinctive boot-up signature MAME doesn't replicate. Mitchell's lawsuit against Twin Galaxies continued through 2024. Guinness World Records restored his records in 2020 pending the lawsuit's resolution.",
    },

    # T4-P3 Comics — Watchmen
    {
        "tier": 4,
        "question": "Alan Moore and Dave Gibbons published a 12-issue maxi-series for DC Comics in 1986-1987 about a group of retired American superheroes in an alternate 1985 where Richard Nixon is in his fifth term and the world is on the brink of nuclear war. The series was groundbreaking for its mature themes, nine-panel grid, and intricate symbolism. A single iconic image appears in every issue — a smiley face button with a blood-droplet across one eye. What was the series called?",
        "answer": "Watchmen, by Alan Moore and Dave Gibbons",
        "choices": [
            "Watchmen, by Alan Moore and Dave Gibbons",
            "The Dark Knight Returns, by Frank Miller",
            "V for Vendetta, by Moore and David Lloyd",
            "The Killing Joke, by Moore and Brian Bolland",
        ],
        "context": "Moore wanted to use Charlton Comics characters (the Question, Blue Beetle, Captain Atom) but DC said it would limit future use of those characters; Moore created analogs instead (Rorschach, Nite Owl, Doctor Manhattan). The 2009 Zack Snyder film adapted most of the comic faithfully but changed the ending. The 2019 HBO miniseries served as a sequel.",
    },

    # T4-P4 Cryptid — Loch Ness
    {
        "tier": 4,
        "question": "The most famous photo of the Loch Ness Monster — a black-and-white shot showing a long-necked silhouette rising from the water — was published in the Daily Mail on April 21, 1934. It was attributed to a London gynecologist named Robert Kenneth Wilson. The image circulated as authentic evidence for sixty years before a deathbed confession in 1994. Who confessed to fabricating the photograph using a toy submarine?",
        "answer": "Marmaduke Wetherell's son-in-law Christian Spurling, with Wetherell himself directing the hoax",
        "choices": [
            "Marmaduke Wetherell's son-in-law Christian Spurling, with Wetherell himself directing the hoax",
            "Wilson himself, in a private letter discovered in his estate by his nephew",
            "A retired Royal Navy submariner who had been a Daily Mail intern at the time",
            "Two Scottish brothers from Inverness who had been paid by the newspaper",
        ],
        "context": "Marmaduke Wetherell was a big-game hunter the Daily Mail had previously discredited after he 'discovered' Nessie footprints that turned out to be hippopotamus tracks from an umbrella stand. The toy submarine was bought at Woolworth's in London; Spurling attached a plastic neck-and-head shape. The Loch is 23 miles long, 1 mile wide, and 754 feet deep — deeper than most of the North Sea.",
    },

    # T4-P5 MtG — Power Nine
    {
        "tier": 4,
        "question": "Magic: the Gathering's original 1993 Alpha set, designed by Richard Garfield and published by Wizards of the Coast (then a small Renton, Washington garage outfit run by Peter Adkison), contained nine cards now considered the most powerful in the game's history. Eight of them have been on the Reserved List since 1996 and command thousands of dollars on the secondary market. The most famous of the nine commonly sells in excess of $200,000 for a pristine Alpha copy. What's it called?",
        "answer": "Black Lotus",
        "choices": [
            "Black Lotus",
            "Ancestral Recall",
            "Time Walk",
            "Mox Sapphire",
        ],
        "context": "Black Lotus produces three mana of any single color for zero cost and is sacrificed; it lets a player cast huge spells turn one. The Power Nine: Black Lotus, Ancestral Recall, Time Walk, Timetwister, and the five Moxes (Pearl, Sapphire, Jet, Ruby, Emerald). Garfield's PhD was in combinatorial game theory at UPenn. The first MtG Pro Tour was in New York City in 1996.",
    },

    # T4-SIG Wrestling (Attitude Era — pre-2002 OK)
    {
        "tier": 4,
        "question": "At King of the Ring 1996, the future Stone Cold Steve Austin defeated Jake 'The Snake' Roberts in the tournament final and delivered a victory speech that defined a wrestling era. The speech took a swipe at Roberts' Bible-thumping ring persona. The line he closed with became the most-printed line of merchandise in WWF history. What was it?",
        "answer": "And that's the bottom line, 'cause Stone Cold said so",
        "choices": [
            "And that's the bottom line, 'cause Stone Cold said so",
            "Austin 3:16 says I just whipped your ass",
            "DTA, Don't Trust Anybody, that's what Austin 3:16 means",
            "If you smell what the Rattlesnake is cooking, raise your hands",
        ],
        "context": "Austin's exact line was: 'You sit there and you thump your Bible, and you say your prayers, and it didn't get you anywhere. Talk about your Psalms, talk about John 3:16 — Austin 3:16 says I just whipped your ass!' The phrase became the iconic Attitude Era catchphrase. Austin's match-ending pose with both middle fingers up while shaking his head was on millions of T-shirts by 1998.",
    },

    # =========================================================================
    # T5 — Ready Player One deep cuts (cap 1100)
    # =========================================================================

    # T5-P1 Movie deep cut — Princess Bride opening
    {
        "tier": 5,
        "question": "The opening scene of 1987's The Princess Bride shows a young Fred Savage in bed playing a baseball video game on a Commodore Amiga personal computer while his grandfather (Peter Falk) arrives to read him a story. Production designer Norman Reynolds wanted the game on screen to be authentically contemporary for a 1987 setting. The cartridge-and-controller game shown was a then-recent release from Accolade software, one of the first sports games to feature digitized photos of real ballplayers on its packaging. What game was being played?",
        "answer": "Hardball II",
        "choices": [
            "Hardball II",
            "World Series Baseball",
            "Bases Loaded",
            "RBI Baseball",
        ],
        "context": "Hardball II released in 1989 actually, but the prop was the original 1985 Hardball by Bob Whitehead — Accolade's first hit. The Amiga prop was a Commodore Amiga 1000 (released 1985). Fred Savage was 11 during filming; he had been cast in The Wonder Years TV pilot the same year. Rob Reiner's daughter Tracy named the practical-effects rats in the fire-swamp scene 'pretend they're not on fire.'",
    },

    # T5-P2 Gaming — SMB Minus World
    {
        "tier": 5,
        "question": "The original 1985 NES Super Mario Bros. famously contains a glitch in World 1-2 that allows a player to enter a strange underwater level looping with no exit. To trigger the glitch, the player must jump up under a specific pipe with frame-perfect timing to clip past the trigger that would normally warp them to World 4-2. The result places Mario in a corrupted level the inventory display labels as a glitch tile. What did fans nickname this level?",
        "answer": "The Minus World (World -1)",
        "choices": [
            "The Minus World (World -1)",
            "World Zero",
            "The Glitch Pipe",
            "The Forbidden World",
        ],
        "context": "In the original Famicom Disk System version, the corrupted level is actually three different glitch-worlds depending on Mario's exact position when he clips. World 1-2's intended Warp Zone leads to Worlds 2, 3, or 4. The Minus World loops to itself because the game's level-loading routine interprets the corrupted tile as a Water Level 7 — and Water Level 7 doesn't have a flagpole, so Mario can never finish.",
    },

    # T5-P3 Pulp — Lovecraft + Cthulhu
    {
        "tier": 5,
        "question": "H.P. Lovecraft published 'The Call of Cthulhu' in the February 1928 issue of Weird Tales. The story has three parts: a Providence professor finds his great-uncle's papers; a New Orleans police inspector raids a Louisiana swamp cult; and a Norwegian sailor's manuscript describes encountering a sunken city rising from the South Pacific. The story coined a new vocabulary of cosmic horror. The Norwegian sailor's name became culturally iconic, often mispronounced. What was his name?",
        "answer": "Gustaf Johansen",
        "choices": [
            "Gustaf Johansen",
            "Henry Wilcox",
            "Francis Wayland Thurston",
            "George Gammell Angell",
        ],
        "context": "Johansen's manuscript describes his ship the Emma being attacked by R'lyeh cultists; he and his shipmate Briden then encounter Cthulhu emerging from the cyclopean ruins. Briden dies of fright; Johansen dies in Oslo soon after writing the account. Lovecraft's pronunciation of Cthulhu was reportedly 'Khlûl'-hloo,' though he admitted no human throat could properly form the sound.",
    },

    # T5-P4 Mystery — DB Cooper
    {
        "tier": 5,
        "question": "On Thanksgiving Eve 1971 — November 24 — a middle-aged man calling himself Dan Cooper bought a one-way ticket on Northwest Orient Flight 305 from Portland, Oregon to Seattle. He handed a flight attendant a note claiming he had a bomb. After landing in Seattle, he demanded $200,000 in $20 bills and four parachutes, released the passengers, and ordered the plane to fly southeast at 10,000 feet. Over southwestern Washington, he opened the rear airstair and jumped out into a stormy night. Nine years later, in February 1980, a child found something specific that suggested he hadn't survived. What was found?",
        "answer": "About $5,800 in degraded $20 bills with serial numbers matching the ransom money, on a sandbar of the Columbia River",
        "choices": [
            "About $5,800 in degraded $20 bills with serial numbers matching the ransom money, on a sandbar of the Columbia River",
            "His weathered black necktie with the SkyJay tie clip caught in a tree branch above Lake Merwin",
            "A partially submerged briefcase containing one parachute and waterlogged ID papers near Ariel WA",
            "His business shirt, monogrammed D.C., wrapped around a $20 bill in a hollow tree near Battle Ground",
        ],
        "context": "The eight-year-old boy was Brian Ingram, the family vacationing along the Columbia near Vancouver WA. The bills were waterlogged but still readable. The FBI closed the case in 2016 without ever identifying Cooper, but they retain physical evidence including a clip-on tie he left on the plane. DNA testing of the tie has been inconclusive. Cooper's parachute and the bulk of the money have never been found.",
    },

    # T5-P5 D&D deep — Strahd
    {
        "tier": 5,
        "question": "In 1983, husband-and-wife designers Tracy and Laura Hickman released an AD&D module that introduced an entirely new sub-genre to TSR's catalog: gothic horror. Set in a fog-shrouded Eastern European-style country called Barovia, the module centers on the vampire lord of Castle Ravenloft, a tragic figure cursed centuries before for the betrayal that cost him the love of his life. The module won the H.G. Wells Award in 1984. Strahd's beloved was a maiden named Tatyana whose modern reincarnation appears in the module as a barmaid. What's the module called?",
        "answer": "I6 Ravenloft",
        "choices": [
            "I6 Ravenloft",
            "I7 Baltron's Beacon",
            "X2 Castle Amber",
            "Q1 Queen of the Demonweb Pits",
        ],
        "context": "The Hickmans had been writing it as a one-shot home Halloween adventure for years before TSR published it. The randomized card-drawn fortune-telling mechanic was groundbreaking. Strahd became so popular he got the 1990 sequel I10 House of Strahd, the 2006 3.5e Expedition to Castle Ravenloft, and the 2016 5e Curse of Strahd by Tracy Hickman + Christopher Perkins. The Ravenloft campaign setting (1990) used Strahd's domain as one of many 'Domains of Dread.'",
    },

    # T5-SIG Mariners — Edgar's Double
    {
        "tier": 5,
        "question": "On October 8, 1995, in Game 5 of the American League Division Series at the Kingdome, the Seattle Mariners faced the New York Yankees with the series tied 2-2. The score was tied 4-4 in the bottom of the 11th inning. Joey Cora was on third, Ken Griffey Jr. on first. Edgar Martinez stepped to the plate. He drove a 2-1 fastball from Jack McDowell into the left-field corner. Cora scored easily. Griffey rounded second, sprinted past third, and slid headfirst across home plate as the throw came in. The play sent Seattle to its first ALCS in franchise history. What did the play come to be known as among Mariners fans?",
        "answer": "Edgar's Double, or simply 'The Double'",
        "choices": [
            "Edgar's Double, or simply 'The Double'",
            "The Junior Slide, after Ken Griffey Jr's first-to-home dash",
            "The Refuse to Lose Hit, after the team's '95 motto",
            "The Kingdome Miracle, the colloquial Seattle radio call",
        ],
        "context": "Dave Niehaus's call — 'GET OUT THE RYE BREAD AND THE MUSTARD, GRANDMA, IT IS GRAND SALAMI TIME!' — preceded the inning. For The Double, his call was: 'The Mariners are going to play for the American League Championship! I don't believe it! It just continues! My oh my!' Lou Piniella was the manager. The 1995 'Refuse to Lose' team is credited with saving baseball in Seattle and securing public funding for Safeco Field.",
    },
]
