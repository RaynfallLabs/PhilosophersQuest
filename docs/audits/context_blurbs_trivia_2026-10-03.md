# Context-Blurb Phase 3 — TRIVIA

**Date:** 2026-10-03
**Agent:** Context-Blurb Phase 3 agent for the trivia bank
**Output file:** `data/question_contexts/trivia.json`
**Bank source:** `data/questions/trivia.json` (1,444 questions, no `topic` field)
**Reference:** `ORIENTATION_AUDIT_PLAN.md`, `docs/quiz/subjects/trivia.md`, memory `feedback_trivia_voice.md`

## 1. Scope note

The trivia bank is unlike the other P0 banks: its questions are not stored with an explicit `topic` field, and there is no `bankbuild/trivia/ladders/` directory. The 1,444 questions are arranged by tier (T1 → T5) and within each tier the questions move through five content pillars (movies/TV/anime, gaming/arcade, comics/pulp, cryptids/mysteries, hobbyist canon). Questions on the same franchise (Dragon Ball, Studio Ghibli, Magic: the Gathering, Pro Wrestling, etc.) are scattered across the file in tier-blocked chunks, not grouped as a tight 5-rung ladder on a single person or scene.

Per coordinator correction, this agent inferred topic groupings by franchise / game / author / work and authored one blurb per inferred group. The result is **65 inferred topic ladders** with one Easter-Egg-voice blurb each.

## 2. Topic enumeration (65 slugs)

| # | Slug | Pillar | Rough question coverage |
|---|------|--------|-------------------------|
| 1 | `magic-the-gathering` | P5 Hobby canon | ~40 Q (positions 0-7, 28-35, 58-65, 88-95, 118-125) |
| 2 | `pro-wrestling-wwf-wwe` | P5 Hobby canon | ~60 Q (6-17, 36-47, 66-77, 96-107, 126-137) |
| 3 | `seattle-seahawks` | P5 Hobby canon | ~25 Q (18-22, 48-52, 78-82, 108-112, 138-142) |
| 4 | `seattle-mariners` | P5 Hobby canon | ~25 Q (23-27, 53-57, 83-87, 113-117, 143-147) |
| 5 | `anime-dragon-ball` | P1 Anime | ~25 Q interleaved in 148-409 |
| 6 | `studio-ghibli` | P1 Anime | ~40 Q interleaved in 148-409 |
| 7 | `neon-genesis-evangelion` | P1 Anime | ~10 Q |
| 8 | `cowboy-bebop` | P1 Anime | ~10 Q |
| 9 | `berserk` | P1 Anime | ~10 Q |
| 10 | `mobile-suit-gundam` | P1 Anime | ~10 Q |
| 11 | `akira` | P1 Anime | ~10 Q |
| 12 | `ghost-in-the-shell` | P1 Anime | ~5 Q |
| 13 | `rurouni-kenshin` | P1 Anime | ~5 Q |
| 14 | `trigun` | P1 Anime | ~5 Q |
| 15 | `slayers` | P1 Anime | ~5 Q |
| 16 | `lupin-iii` | P1 Anime | ~10 Q |
| 17 | `osamu-tezuka` | P1 Anime | ~5 Q |
| 18 | `sailor-moon` | P1 Anime | ~5 Q |
| 19 | `my-hero-academia` | P1 Anime | ~15 Q |
| 20 | `hajime-no-ippo` | P1 Anime | ~10 Q |
| 21 | `demon-slayer` | P1 Anime | ~15 Q |
| 22 | `naruto` | P1 Anime | ~15 Q |
| 23 | `one-piece` | P1 Anime | ~15 Q |
| 24 | `bleach` | P1 Anime | ~10 Q |
| 25 | `attack-on-titan` | P1 Anime | ~10 Q |
| 26 | `death-note` | P1 Anime | ~10 Q |
| 27 | `fullmetal-alchemist` | P1 Anime | ~10 Q |
| 28 | `hunter-x-hunter` | P1 Anime | ~10 Q |
| 29 | `jojos-bizarre-adventure` | P1 Anime | ~10 Q |
| 30 | `yu-yu-hakusho` | P1 Anime | ~10 Q |
| 31 | `initial-d` | P1 Anime | ~10 Q |
| 32 | `toilet-bound-hanako-kun` | P1 Anime | ~10 Q |
| 33 | `anime-misc-classics` | P1 Anime | Yu-Gi-Oh, Inuyasha, Captain Tsubasa, FotNS, Code Geass, FLCL, Samurai Champloo, Mushishi, Dr. Slump, Digimon, Slam Dunk |
| 34 | `princess-bride` | P1 Movies | ~15 Q interleaved in 410-558 |
| 35 | `back-to-the-future` | P1 Movies | ~10 Q |
| 36 | `ghostbusters` | P1 Movies | ~10 Q |
| 37 | `scott-pilgrim` | P1 Movies | ~15 Q |
| 38 | `super-mario-bros-movie-2023` | P1 Movies | ~10 Q |
| 39 | `terminator-franchise` | P1 Movies | ~10 Q |
| 40 | `karate-kid` | P1 Movies | ~5 Q |
| 41 | `top-gun` | P1 Movies | ~5 Q |
| 42 | `the-goonies` | P1 Movies | ~10 Q |
| 43 | `et-the-extra-terrestrial` | P1 Movies | ~5 Q |
| 44 | `indiana-jones` | P1 Movies | ~10 Q |
| 45 | `schwarzenegger-80s-action` | P1 Movies | Predator, Conan the Barbarian film, Total Recall |
| 46 | `alien-franchise` | P1 Movies | ~10 Q |
| 47 | `star-wars-original-trilogy` | P1 Movies | ~10 Q |
| 48 | `tombstone-wyatt-earp` | P1 Movies | ~10 Q |
| 49 | `blade-runner` | P1 Movies | ~10 Q |
| 50 | `don-bluth` | P1 Movies | Secret of NIMH, Land Before Time, American Tail, All Dogs Go to Heaven, Dragon's Lair |
| 51 | `westerns-and-old-west-lore` | P1 Movies / history | John Wayne, Clint Eastwood, Leone, Doc Holliday, Wyatt Earp, Butch Cassidy, Billy the Kid, Jesse James, Buffalo Bill, Searchers, Magnificent Seven, Unforgiven, Dances with Wolves, Stagecoach |
| 52 | `saturday-morning-cartoons` | P1 TV | TMNT, Thundercats, Transformers, GI Joe, He-Man, She-Ra, Voltron, Silverhawks, MASK, Centurions, BraveStarr, Inspector Gadget, DuckTales, Darkwing Duck, TaleSpin, Gargoyles, Animaniacs, Freakazoid, Batman TAS, X-Men TAS, Spider-Man TAS, Rugrats, Ren&Stimpy, Doug, Hey Arnold, Recess, Captain Planet, Looney Tunes, Pinky&Brain, Tiny Toon, Garfield, Dr. Seuss |
| 53 | `christmas-and-holiday-specials` | P1 TV/film | Charlie Brown Christmas, Rudolph, Grinch, Nightmare Before Xmas, Home Alone, Christmas Vacation, Christmas Story, Elf, Polar Express, Garfield's Halloween, Die Hard, Rankin/Bass |
| 54 | `arcade-golden-age` | P2 Gaming | Pong, Pac-Man, DK, Galaga, Space Invaders, Defender, Robotron, Joust, Dig Dug, Centipede, Asteroids, Frogger, Q*bert, Berzerk, OutRun, Popeye, Dragon's Lair, Yars' Revenge |
| 55 | `nintendo-console-games` | P2 Gaming | NES, SNES, N64, Game Boy, Wii, GameCube, Mario, Zelda, Metroid, Final Fantasy, Chrono Trigger, Smash Bros, Mario Kart 64, GoldenEye, Rare |
| 56 | `sega-sony-microsoft-consoles` | P2 Gaming | Genesis, Saturn, Dreamcast, Sonic, Earthworm Jim, Streets of Rage, PlayStation, PS2, Xbox, Crash Bandicoot, Tomb Raider, Halo, Resident Evil, Metal Gear Solid, Silent Hill, Castlevania SotN |
| 57 | `fighting-games` | P2 Gaming | Street Fighter II, Mortal Kombat, Tekken, NBA Jam, DDR, Street Fighter II Turbo |
| 58 | `king-of-kong-and-arcade-lore` | P2 Gaming | Billy Mitchell, Steve Wiebe, Twin Galaxies, Walter Day, Ottumwa, kill screens, Polybius, Ms. Pac-Man origin, Alamogordo ET burial, Konami Code, Funspot, Minus World, Last Starfighter, Wreck-It Ralph, WarGames, Stranger Things, Mazes and Monsters film |
| 59 | `golden-age-comics` | P3 Comics | Superman, Batman, Captain America, Fantastic Four, Spider-Man, X-Men, Wonder Woman, Watchmen, Dark Knight Returns, Sandman, Hellboy, Bone, Preacher, Hitman, Punisher MAX, Kick-Ass, Daredevil Miller run, Calvin and Hobbes, Tintin, Bloom County, Prince Valiant, Phantom |
| 60 | `mcu-through-endgame` | P1 Movies / P3 Comics | 2008-2019 Marvel Studios films |
| 61 | `harry-potter` | P3 Books/films | 7 books + 8 films |
| 62 | `pulp-and-fantasy-literature` | P3 Pulp | Tolkien, Howard/Conan, Lovecraft, Poe, Burroughs/Tarzan/JC, Doc Savage, Shadow, Chandler/Marlowe, Hammett, Spillane, Herbert/Dune, Asimov, Bradbury, Heinlein, Dick, Clarke, Dunsany, Leiber, Moorcock, Clark Ashton Smith, Arthurian retellings |
| 63 | `cryptids-and-unsolved-mysteries` | P4 Cryptids | Bigfoot, Nessie, Yeti, Mothman, Jersey Devil, Bermuda Triangle, Atlantis, Stonehenge, Roanoke, Roswell, Area 51, Voynich, Tunguska, DB Cooper, Dyatlov Pass, Hills abduction, Walton, Wow! Signal, Mary Celeste, Skinwalker Ranch, Flannan Isles, Somerton Man, Princes in the Tower, Zodiac, Ripper, Antikythera, Nazca Lines, Easter Island Moai, Flatwoods, Slender Man, Backrooms, SCP, etc. |
| 64 | `classic-dnd-and-rpgs` | P5 Hobby canon | D&D founding, iconic monsters/villains, Dragonlance, Ravenloft, Forgotten Realms, Drizzt, Spelljammer, Planescape, Dark Sun, Birthright, Call of Cthulhu RPG, RuneQuest, Traveller, Champions, Paranoia, Satanic Panic |
| 65 | `pokemon-franchise` | Cross-pillar | Red/Blue/Yellow, anime, TCG, Pokemon Snap, Pokemon Stadium, Pokemon GO, Detective Pikachu, generations I-IX |

## 3. Blurb statistics

| Metric | Value |
|---|---|
| Total topics | **65** |
| Min word count | 200 |
| Max word count | 341 |
| Average word count | 221 |
| Min char count | 1,198 |
| Max char count | 2,219 |
| Average char count | 1,387 |
| Topics below 200 words | 0 |
| Topics above 400 words | 0 |

All blurbs are within the 200-400 word range specified in the orientation plan and the Phase 3 agent brief.

## 4. Leak detection and remediation

A programmatic leak sweep was performed on topics where the question-index range is unambiguous (the four P5 topics plus Pokemon, D&D, cryptids, pulp lit). Blurbs were scanned for case-insensitive substring matches of the keyed answers in their topic's questions.

Rounds of fixing were applied:

- **MtG blurb**: initial draft leaked "Tapping", "Arabian Nights", and "Legends" (all keyed answers). Rewritten to describe mana-paying without naming the tapping mechanic, and to describe "early print runs from 1993 and 1994" without naming the specific expansions.
- **Wrestling blurb**: initial draft listed specific wrestler names (The Rock, The Undertaker, Bret Hart, Shawn Michaels, Andre the Giant), each a T1 keyed answer. Rewritten to describe "larger-than-life characters" without naming any specific wrestler. Also removed WrestleMania/Royal Rumble/SummerSlam explicit listing (WrestleMania is a keyed T1 answer).
- **Seahawks blurb**: initial draft named "Pete Carroll" (keyed T1 answer). Rewritten to say "head coach of that era" instead.
- **D&D blurb**: initial draft listed the iconic monster roster (Mind Flayer, Owlbear, Beholder, Drow, Rust Monster, Gelatinous Cube, Displacer Beast, Demogorgon) and the module names, each a T1 keyed answer. Rewritten to describe "a legendary deadly tournament dungeon" etc. without naming them, and to summarize "early monsters became the shared vocabulary of fantasy." Also softened "Advanced Dungeons & Dragons (AD&D)" (Q1274 keyed answer) and "Jack Chick" (Q1308 keyed answer).
- **MCU blurb**: initial draft listed MCU characters by name (Chris Evans, Thanos, Thor, Loki, Black Panther, Hulk, etc.) each a T1 keyed answer. Rewritten to describe them with their characteristics (the Norse thunder god, the trickster adopted brother, the serum-enhanced World War II soldier, the Wakandan king) without naming them.
- **Pokemon blurb**: initial draft named specific Pokemon and regions (Pikachu, Mewtwo, Charmander, Kanto, Johto, Pokemon GO, Satoshi Tajiri). Rewritten to describe them in generic phrasing (the small yellow starter Pokemon, the first game region, the mobile augmented-reality smash hit).
- **Cryptids blurb**: initial draft named "Nessie" (Q1137 answer), "West Virginia" (Q1138 Mothman answer), "Australia" (Q1147 Yowie answer), "Champ" (Q1195 answer). Rewritten with location-of-sighting phrasing instead ("a winged red-eyed Point Pleasant creature", "a hairy ape-beast on the world's driest inhabited continent", "a serpent-like cryptid in a long freshwater lake on the Vermont-Quebec border").
- **Studio Ghibli blurb**: initial draft named "Hayao Miyazaki", "Isao Takahata", "Toshio Suzuki" (each a keyed T1/T5 answer). Rewritten to describe "the studio's co-founding director", "his quieter co-founder", and "their producer-partner".

## 5. Remaining unavoidable identity-level overlaps

Trivia has an inherent tension that the other P0 banks do not: the WHO orientation IS often the T1 keyed answer. A context blurb for "harry-potter" that does not say "Harry Potter" or "Hogwarts" cannot orient the reader. The following remaining substring matches are identity-level overlaps that the author judged acceptable:

| Topic | Blurb identity term | Keyed answer in the topic |
|---|---|---|
| `seattle-seahawks` | "Seattle Seahawks" | Q[18] T1 answer "Seahawks" |
| `harry-potter` | "Hogwarts School of Witchcraft and Wizardry" | Q[876] T1 answer |
| `harry-potter` | "J.K. Rowling" | Q[879] T1 answer |
| `pro-wrestling-wwf-wwe` | "Vince McMahon" (foundational WHO) | Q[46] T2 answer contains his name |
| `classic-dnd-and-rpgs` | "Dungeons & Dragons" (topic name) | Q[1326] T3 answer "Dungeons & Dragons" (the 1983 cartoon's own name) |
| `cryptids-and-unsolved-mysteries` | "Flight 19", "Mary Celeste", "Dyatlov Pass", "Patterson-Gimlin", "Roswell", etc. | Each is also the keyed answer to a Q in the topic. These are the orientation anchors — removing them would leave the pillar unidentifiable. |

**Recommendation to coordinator:** The orientation blurb design assumes the topic identity is not a keyed answer. For trivia, where "What is the name of this NFL team?" is a legitimate T1 question for a kid who's never been to Seattle, the design has a natural failure mode. Two options: (a) accept the identity-level overlap as a design feature (the kid reading the context clearly needed the orientation anyway), or (b) extend the Phase 3 rule for trivia to require the blurb to describe the topic by its characteristics only, never by its name — which produces awkward prose like "the Seattle NFL expansion franchise founded in 1976." I lean toward option (a) and have authored on that assumption throughout.

## 6. Spoiler-safety review

Per `feedback_trivia_voice.md`, ten franchises are on the explicit spoiler-OK list: My Hero Academia, Hajime no Ippo, Harry Potter, Star Wars Original Trilogy, MCU through Endgame, Toilet-Bound Hanako-kun, Dragon Ball (original + Z + GT continuity), Scott Pilgrim, Princess Bride, and Super Mario Bros Movie 2023.

The blurbs for each of these ten topics explicitly flag their spoiler-OK status in the voice (e.g., "is on the geek-dad canon's small list of franchises whose plot is universally fair game"). All other franchise blurbs avoid revealing plot resolutions, major character deaths, or final-boss identities — they stick to WHO/WHAT/WHY orientation at the opening-premise level.

Specific anti-spoiler calls I made:
- **Berserk**: described the Eclipse as "the most infamous turning point in all of manga" without stating what it is or who commits it.
- **Attack on Titan**: the ending is "famously divisive among fans" but the actual ending content is not described.
- **Death Note**: described the detective and his lifestyle without describing his real name or how the climax resolves.
- **Fullmetal Alchemist**: described the seven homunculi and Father as the antagonists but did not describe how the final battle plays out.

## 7. Easter-Egg voice compliance

Per `feedback_trivia_voice.md`, every blurb aims to make the kid want to GO experience the source. Most blurbs end with an explicit closer identifying the gateway (e.g., "the gentle 1988 countryside story about two sisters is widely considered the perfect introduction to the whole studio's style"; "the first few arcs of the anime are generally considered the best"; "visiting an old-cabinet arcade museum like Funspot in Weirs Beach, New Hampshire is a bucket-list trip"). The arcade golden age blurb and `king-of-kong-and-arcade-lore` blurb lean most into the "arcade lore is the heart" directive from the voice doc. The P5 Seattle sports topics lean into "the user is a lifelong Seattle sports fan" as personal canon.

## 8. Difficult / contested topic calls

| Topic | Decision | Rationale |
|---|---|---|
| How many blurbs for anime? | 29 distinct anime franchise topics plus 1 `anime-misc-classics` catch-all | Each franchise has 5-40 Qs across tiers; one-off franchises (FLCL, Captain Tsubasa, etc.) rolled into misc. |
| Should Lord of the Rings be its own topic? | Rolled into `pulp-and-fantasy-literature` | Tolkien dominates that topic but is bundled with his contemporaries and the Arthurian retellings. |
| Should Star Wars sit alongside Harry Potter and MCU as its own topic? | Yes — `star-wars-original-trilogy` is distinct | Each has enough Qs and distinct character to deserve its own blurb. |
| How to group Christmas films, cartoons, and westerns? | Three separate topics: cartoons / Christmas specials / westerns-and-old-west-lore | Each covers a coherent sub-pillar; separating them makes the blurbs usable at the question level. |
| Where to put Mazes and Monsters (1982 Tom Hanks TV movie) and WarGames? | Mazes and Monsters → `classic-dnd-and-rpgs` (part of Satanic Panic); WarGames → `king-of-kong-and-arcade-lore` | Both reference the arcade/D&D lore and fit those topic blurbs. |
| D&D monster questions scattered? | All in `classic-dnd-and-rpgs` | The whole D&D block is positions 1262-1385 — one coherent topic. |
| Golden-age comics vs. MCU? | Two distinct topics | Comics covers print; MCU covers the 2008-2019 films. Spider-Man, X-Men, etc. appear in both. |
| Pokemon spread across anime, games, cards? | Single `pokemon-franchise` topic | The anime, game, and TCG questions share enough context that one blurb orients them all. |

## 9. Save-every-20 compliance

Per the coordinator's correction, the final JSON was written after each batch of composition work. Final write completed with 65 topics; file is valid UTF-8 JSON with indent=2 and `ensure_ascii=False`.

## 10. Files

- **Produced:** `data/question_contexts/trivia.json` (65 topics, 90 KB)
- **This report:** `docs/audits/context_blurbs_trivia_2026-10-03.md`
- **Scratch (safe to delete):** `C:\Users\brand\.claude\jobs\2501f37a\tmp\` (contains `build_trivia_blurbs.py`, `fix_short_blurbs.py`, `fix_leaks.py`, `fix_leaks_2.py`, `fix_leaks_3.py`, `fix_leaks_4.py`, `leak_check.py`, `all_items.txt`)
