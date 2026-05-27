# trivia bank assembly log

- Pool: 1410 questions across 10 source files
- After intra-bank dedup: 1410
- After gate validation: 1386 pass (0 soft-warn), 24 fail
- Final bank size: **1386**

## Sources

- `A10_mtg_wwe_seattle.json` — 150 questions
- `A1_anime_classics.json` — 120 questions
- `A2_modern_anime.json` — 150 questions
- `A3_movies_80s90s.json` — 150 questions
- `A4_cartoons_westerns_holidays.json` — 130 questions
- `A5_arcade_console_lore.json` — 180 questions
- `A6_comics_hp_mcu.json` — 150 questions
- `A7_pulp_tolkien_scifi.json` — 120 questions
- `A8_cryptids_mysteries.json` — 130 questions
- `A9_classic_dnd.json` — 130 questions

## Tier distribution

- T1: 272
- T2: 274
- T3: 279
- T4: 279
- T5: 282

## Gate failures (dropped)

- `answer_collision`: 24

## Fail samples (first 20)

### #2 T1
- Stem: What is the famous black-bordered MtG card whose Alpha printings now sell for over $200,000?...
- Answer: Black Lotus
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=1355 jaccard=1.00

### #4 T1
- Stem: MtG's iconic five-headed dragon-goddess card, queen of evil dragons, is named what?...
- Answer: Tiamat
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=1282 jaccard=1.00

### #151 T1
- Stem: In Dragon Ball Z, Goku's signature blue energy attack — fired with cupped hands and a long shouted n...
- Answer: Kamehameha
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=280 jaccard=1.00

### #171 T2
- Stem: In Dragon Ball Z, the muscular green-skinned alien warrior who arrives on Earth at the start of the ...
- Answer: Raditz
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=321 jaccard=1.00

### #174 T1
- Stem: In Studio Ghibli's 1986 film about a girl named Sheeta who falls from the sky into the arms of a you...
- Answer: Laputa
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=345 jaccard=1.00

### #191 T2
- Stem: Studio Ghibli's 2013 film, which Miyazaki initially said would be his last theatrical feature, was a...
- Answer: The Wind Rises
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=226 jaccard=1.00

### #226 T4
- Stem: Hayao Miyazaki had publicly retired from feature direction at least seven times before his 2023 retu...
- Answer: The Wind Rises
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=191 jaccard=1.00

### #280 T1
- Stem: In Dragon Ball, Goku's signature blue energy-beam attack — formed by cupping the hands at the hip be...
- Answer: Kamehameha
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=151 jaccard=1.00

### #321 T2
- Stem: Dragon Ball Z's Saiyan arc introduced Goku's older brother — a long-haired warrior who arrives on Ea...
- Answer: Raditz
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=171 jaccard=1.00

### #345 T3
- Stem: Hayao Miyazaki's Castle in the Sky (1986) — Studio Ghibli's first official film — features two child...
- Answer: Laputa
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=174 jaccard=1.00

### #433 T1
- Stem: In 1993's Tombstone, Val Kilmer's tubercular Doc Holliday delivers one famous catchphrase before eac...
- Answer: I'm your huckleberry
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=629 jaccard=1.00

### #586 T1
- Stem: In the 1995 spinoff cartoon Pinky and the Brain, what do the two lab mice attempt to do every single...
- Answer: Try to take over the world
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=599 jaccard=1.00

### #599 T2
- Stem: In the 1993 Warner Bros. cartoon Animaniacs, two lab mice were a recurring segment featuring a tall ...
- Answer: Try to take over the world
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=586 jaccard=1.00

### #620 T2
- Stem: A persistent rumor about 1985's Garfield's Halloween Adventure claims a legendary actor — the man be...
- Answer: Orson Welles
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=653 jaccard=1.00

### #629 T3
- Stem: In the 1993 Western Tombstone, Val Kilmer played the tuberculosis-stricken dentist and gambler Doc H...
- Answer: I'm your huckleberry
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=433 jaccard=1.00

### #653 T4
- Stem: In Animaniacs's spinoff Pinky and the Brain, the actor Maurice LaMarche voiced Brain. LaMarche has b...
- Answer: Orson Welles
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=620 jaccard=1.00

### #1195 T2
- Stem: The unsolved 1947 murder of 22-year-old Elizabeth Short, whose body was found posed in a vacant lot ...
- Answer: The Black Dahlia
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=1239 jaccard=1.00

### #1239 T4
- Stem: Twenty-two-year-old Elizabeth Short was found bisected at the waist and posed in a vacant lot in Lei...
- Answer: The Black Dahlia
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=1195 jaccard=1.00

### #1282 T1
- Stem: The five-headed evil dragon queen of the chromatic dragons in D&D, each head a different color, is n...
- Answer: Tiamat
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=4 jaccard=1.00

### #1294 T1
- Stem: The author of the fantasy setting Dragonlance, co-creator of the Dragonlance Chronicles trilogy with...
- Answer: Margaret Weis
  - HARD `answer_collision`: Answer collides with 1 other question(s); top match idx=1314 jaccard=1.00

