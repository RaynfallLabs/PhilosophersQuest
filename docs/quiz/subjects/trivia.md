---
version: 1
date: 2026-05-14
subject: trivia
in_game_action: general / utility (deck-shuffling, study mode)
style_verdict: GEEK-DAD CANON — the deep cuts the user loves and wants to share with his kids
---

# Subject: Trivia

The trivia bank is **personal**. It's the user's way of sharing the deep-cut canon he loves — movies, anime, comics, pulp fiction, gaming, arcades, cryptids, classic D&D — with his kids. *Ready Player One* deep-lore vibe: stuff that the player NEEDS to know, and that makes them want to GO seek out the source. The bank is fun, the wonder voice carries through, and **NO MAJOR SPOILERS ever** — questions reference scenes, casts, production, real-world impact, but never ruin the first-time wonder of reading or seeing something.

## 1. Timing budget

| Stat | Value |
|---|---|
| `SUBJECT_TIMER` | `('trivia', (26, 1.2))` in src/player.py |
| Total timer at WIS 10 | **38s** |
| Total timer at WIS 25 | **56s** |

Generous mid-range timer — these questions read fast.

## 2. Per-tier char budgets (answer-outlier 1.6× rule applies)

| Tier | Hard cap | Voice |
|---|---:|---|
| T1 | ≤ 280 | The OBVIOUS stuff — name of Ash's first Pokémon, primary colors of Sonic the Hedgehog |
| T2 | ≤ 480 | Casual fan knowledge — the year Pac-Man came out (1980), Akira director (Otomo) |
| T3 | ≤ 680 | Real fan stuff — Donkey Kong kill screen at level 22, Conan author origins (Howard) |
| T4 | ≤ 900 | Deep fan stuff — Billy Mitchell vs Steve Wiebe (King of Kong 2007), Eva production troubles |
| T5 | ≤ 1100 | Ready Player One deep cuts — Easter eggs, technical achievements, obscure connections |

## 3. Tier = depth (the user's framing)

Tier in this bank is **depth of trivia**, not subject difficulty. Per the user: "high score in Pac-Man is deep; name of Ash's first Pokémon is obvious."

- **T1**: Anyone who's heard of the thing knows the answer (Bulbasaur was Ash's... wait actually Pikachu. T1.)
- **T5**: Only people who've gone deep know (the secret world warp in Super Mario Bros. via the minus-world glitch in 1-2)

## 4. Stance — what makes THIS bank different

**No spoilers, ever.** Questions reference scenes, plots, characters, and interactions — but NEVER ruin:
- The ending or twist of a film/show/book/game
- Major character deaths
- Season-finale beats
- Final boss reveals
- Mystery solutions

**Make them want to seek it out.** Every question should leave a kid thinking "I want to watch/read/play that." This is the user's explicit voice target.

### Stance table

| Topic | Stance |
|---|---|
| Classic comics (Golden through Bronze + Modern through ~2003) | CELEBRATED |
| Modern multiverse-era Marvel/DC slop (2010+, Disney+ shows, etc.) | NOT COVERED |
| Marvel cinematic universe | THROUGH ENDGAME ONLY (2008-2019) — nothing after |
| Classic D&D / AD&D / TSR-era | CELEBRATED |
| Modern D&D (5e errata, sensitivity reads, etc.) | NOT COVERED |
| Anime classics | CELEBRATED — DBZ, Eva, Berserk, MHA, Demon Slayer, Naruto, OP, Bleach, Trigun, Bebop, Akira, GitS, Ghibli, FMA |
| Pulp fiction era | CELEBRATED — Weird Tales, Howard's Conan, Lovecraft, Burroughs's Tarzan/John Carter, Clark Ashton Smith |
| Western lore | CELEBRATED — Tombstone, OK Corral 1881, Eastwood/Leone, John Wayne, Doc Holliday, Wyatt Earp |
| Saturday morning cartoons (80s/90s) | CELEBRATED — TMNT, Thundercats, Silverhawks, He-Man, GI Joe, Transformers, X-Men TAS, Batman TAS |
| Classic arcades + console era | CELEBRATED — Pac-Man, Donkey Kong, Galaga, Defender, Robotron, original Zelda, Metroid, Mario, Sonic, FF7, MGS, Goldeneye |
| WWF/WWE through Attitude Era (~2002 Hogan-Rock WM18) | CELEBRATED — Hogan, Macho, Andre, Hart Foundation, Hulkamania, Stone Cold 3:16, the Rock, Mick Foley, NWO at WCW |
| Modern wrestling (post-Attitude Era) | NOT COVERED beyond Hogan-Rock WM18 (March 17, 2002) |
| Seahawks moments | CELEBRATED — Largent, Legion of Boom, SB XLVIII, Beast Quake 2010, Russell Wilson |
| Mariners moments | CELEBRATED — Edgar's Double 1995, 2001 116-win season, Griffey, Ichiro, A-Rod, Felix's perfect game |
| Cryptids + mysteries | CELEBRATED AS STORIES — story-led, not credulous; cover the Patterson-Gimlin film, Loch Ness 1933 photo (and the 1994 hoax confession), Mothman, Roanoke, DB Cooper, Voynich |
| Magic: the Gathering through Legends (June 1994) | CELEBRATED — Alpha/Beta/Unlimited, Arabian Nights, Antiquities, Power 9, Garfield's MIT origins |
| Modern MTG (post-Legends) | NOT COVERED |
| Internet folklore (clean) | CELEBRATED — SCP Foundation, Backrooms, classic memes as cultural phenomena |

## 5. Voice rules

### Same wonder voice as other banks, lighter touch

PERSON / SCENE / DETAIL → STORY → WONDER. Lead with a named thing — a movie, a game, a character, a moment. Pay off with the deep-cut fact.

### Story beats OK, spoilers banned

- OK: *"In the opening scene of the 1987 film *The Princess Bride*, a young Fred Savage is seen playing a baseball video game on a Commodore Amiga personal computer. What game?"* (Hardball II — production trivia, scene reference, no spoiler)
- BANNED: *"At the end of *The Princess Bride*, what happens to Westley?"* (spoils the ending)

### "Make them want to seek it out"

Every question should leave the player intrigued enough to GO watch/read/play the thing. Examples:

> *"Released in 1988, an animated cyberpunk film set in 2019 Neo-Tokyo featured groundbreaking hand-drawn animation, a soundtrack of taiko drums and chanting voices, and a now-legendary motorcycle slide. Whose directorial debut was it?"* → **Katsuhiro Otomo** (this should make a kid want to watch *Akira*)

> *"On July 9, 1982, a 21-year-old construction worker named Steve Sanders played *Donkey Kong* at the Twin Galaxies arcade in Ottumwa, Iowa, achieving a score of 1,000,000 — the first publicly verified million. A pizza-parlor owner from Florida named Billy Mitchell took the record back six months later. What was Mitchell's score?"* → **1,047,200 (Mitchell's famous July 1982 score)** — this should make a kid want to watch *King of Kong*

> *"In 1932, in Cross Plains, Texas, a 26-year-old writer named Robert E. Howard sold his first story about a black-haired, blue-eyed Cimmerian barbarian to *Weird Tales* magazine. The character would become the archetype of an entire literary genre Fritz Leiber later named 'sword & sorcery.' Who?"* → **Conan the Cimmerian / Conan the Barbarian**

### Tier = depth-of-cut

- T1 obvious: "Pikachu" / "Bulbasaur" / "Mario" / "Mickey Mouse" / "Charlie Brown"
- T5 deep: "Pac-Man's kill screen at level 256" / "Minus World in SMB 1-2" / "the 2.5-frame perfect dragon punch input"

## 6. Quality gates

| Gate | Configuration |
|---|---|
| schema | required |
| length_parity | answer-outlier rule (1.6× multiplier) |
| length_budget | per-tier cap |
| anti_rote | NOT exempted |
| duplicate | 0.85 similarity threshold |

## 7. Distractor design

- **Casts / actors**: distractors are other real actors who could plausibly have been cast
- **Years / dates**: distractors are real adjacent years (the famous-year for the franchise, the actual neighboring releases)
- **Characters**: distractors are other real adjacent characters
- **Production**: distractors are other real adjacent productions of the era
- **Cryptids**: distractors are other real cryptids
- **Module names**: distractors are other real TSR modules of the era

## 8. Anti-patterns

- **Plot spoilers** — fail, automatic rejection
- **Character-death reveals** — fail
- **Mystery solutions for mystery films/games** — fail
- **Modern multiverse-era capeshit** — out of scope
- **Disney-era Star Wars** — out of scope
- **Post-Endgame MCU** — out of scope
- **Post-Attitude-Era wrestling** — out of scope (Hogan-Rock WM18 March 2002 is the boundary)
- **Modern D&D errata or sensitivity reads** — out of scope
- **Modern Magic the Gathering (post-Legends)** — out of scope
- **Joke / "obviously dumb" distractors** — fail
- **Pronoun antecedents over 8 words apart**
- **Term-before-definition** — if introducing "kill screen" or "TPK" or "Section 8," scene-set first

## 9. What success looks like

- A T1 makes a kid hear "Sonic" and remember he's blue
- A T2 makes them hear "Akira" and learn it came out in 1988
- A T3 makes them hear "Conan" and learn Robert E. Howard wrote him from a Texas farmhouse in 1932
- A T4 makes them hear "Donkey Kong kill screen" and learn it's level 22 (256)
- A T5 makes them hear "the Princess Bride opening shot" and learn the boy is playing Hardball II on an Amiga
- **Kids leave wanting to watch *Akira*, watch *King of Kong*, read Howard's Conan stories, find the original *Princess Bride*, dig up *Captain N* episodes on YouTube, and explore the deep cuts their dad loves.**
