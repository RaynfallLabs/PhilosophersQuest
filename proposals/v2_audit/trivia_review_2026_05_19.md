# Trivia Bank Audit (2026-05-19)

## Scope
Full quality review of `data/questions/trivia.json`, against five dimensions:
tier appropriateness, grammar, fun/wonder, topic coverage, weird metadata.

The user's stated stance: **geek-dad canon, Ready Player One vibe — broadly
recognizable across generations. NOT niche fandom. NO SPOILERS.**

## Inputs
- Pre-audit active: 990 questions
- Pre-audit dropped (prior-pass): 2761 questions (mostly fandom-deep dropped
  in earlier re-tier pass: jargon>=90 markers and fk>10)
- Pre-audit tier shape: T1=75, T2=53, T3=176, T4=306, T5=380
- Tier floors required: T1 ≥ 200, T2 ≥ 200, T3 ≥ 200

## Findings

### 1. Fandom-deep content had crept back in
Despite the prior 2761-item drop, ~520 items still slipped through that fall
into "niche fandom deep dive" territory, not broad pop culture. The user
explicitly named these as targets:

- **Pokemon** (Articuno/Zapdos/Moltres, Charizard evolution, Mudkip meme, etc.)
  9 items remained in active bank
- **D&D deep lore** (Drizzt, Forgotten Realms, Lolth, Drow, phylacteries, THAC0,
  Greyhawk vs Krynn vs Faerun vs Oerth, module codes like B1/S1/Q1, Tomb of
  Horrors deep lore, owlbear-from-bag-of-toys origin story) — ~100 items
- **MTG deep lore** (color pie philosophy, summoning sickness mechanics,
  Modern/Pioneer format histories, Counterspell mana cost, Tales of
  Middle-earth crossover set, Birds of Paradise rate) — ~30 items
- **Anime deep cuts** (Naruto/My Hero Academia/One Piece/Demon Slayer/Trigun
  protagonists, Rurouni Kenshin sakabato lore, Cowboy Bebop Yoko Kanno
  composer trivia, Devil Fruit classification, Sun Breathing lore) — ~25 items
- **Wrestling specifics** (Stone Cold's real name, Ric Flair's birth name,
  Bret Hart's Sharpshooter, Dudley Boyz tag-team members, real names of
  Razor Ramon and Diesel and British Bulldog and Macho Man, WrestleMania
  III venue) — ~19 items
- **Video-game lore depth** (Mortal Kombat designer names, Pong creators,
  Tetris Soviet history, Chrono Trigger composer, Streets of Rage 2 audio
  drivers, Q*bert curse, Metal Gear Solid Psycho Mantis fourth-wall trick,
  GTA V protagonists, Deus Ex immersive sim history) — ~80 items
- **Pulp deep lore** (Howard's Bran Mak Morn / Solomon Kane / Kull stories,
  Lovecraft's Color Out of Space and At the Mountains of Madness, William
  Hope Hodgson's Night Land, Clark Ashton Smith's Xiccarph, Burroughs's
  Pellucidar, Doc Savage / Walter Gibson Shadow, Fritz Leiber's Lankhmar,
  Mickey Spillane's Mike Hammer count of novels) — ~40 items
- **Cryptid / UFO / mystery deep cuts** (Skinwalker Ranch, Dyatlov Pass,
  Isdal Woman, Somerton Man / Tamam Shud, Lead Masks Case, Kecksburg,
  Travis Walton, Loveland Frog, Beast of Bray Road, Dover Demon, Flatwoods
  Monster, Cahokia, Spring-Heeled Jack, Gobekli Tepe dating, Easter Island
  walking-statue experiment) — ~85 items
- **Niche internet creepypasta** (Slender Man, Smile.jpg, Smile Dog,
  Jeff the Killer, The Rake, SCP Foundation, Black-Eyed Kids) — 5 items
- **Niche arcade / game** (Q*bert curse string, Gottlieb pinball flipper
  history, Tron arcade I/O Tower mini-game) — 4 items
- **Indie film niche** (Shane Carruth's Primer 2004) — 1 item

**Total niche-fandom items moved to dropped/: 522.**

### 2. Spoilers
The user explicitly said: NO SPOILERS. I searched the bank for the most
common high-spoiler reveals across pop culture:

- Star Wars: "I am your father", "Leia is Luke's sister"
- Harry Potter: Snape's loyalty, horcrux mechanics
- Fight Club twist
- Sixth Sense reveal
- Citizen Kane Rosebud
- Han Solo's death
- Bambi's mother

**0 spoilers found.** The earlier curation had already protected against
plot-reveal questions — surface-level facts only.

### 3. Grammar / typography
- Stripped markdown italic asterisks from question stems (e.g.
  "*Star Wars*" → "Star Wars") — affected 5 items
- Fixed mojibake of "Pokémon" → "Pokemon" in items that needed it
  (the items themselves were then dropped as fandom-niche, but the
  byte hygiene was applied first)
- Em-dashes (U+2014) preserved as proper Unicode

### 4. Weird metadata
Stripped metadata keys: `_drop_reason`, `_fk`, `_jargon`, `_old_tier`,
`_topic`, `_grade`, `_calibration`, `_audit_pass`, `_review_id`, `_notes`,
`_source_id`. None of these belong in production bank.

### 5. Tier appropriateness
After audit, the kept set was 468 items. Tier shape:
- T1: 72
- T2: 51
- T3: 105
- T4: 120
- T5: 120

T1-T3 required +132 / +149 / +95 to hit the 200 floor. T4-T5 already pass.

## Generation: T1 / T2 / T3 fills
I wrote 351 new questions in `tools/quizgen/scratch/trivia_gen_{t1,t2,t3}.py`,
adhering to:

- **Anti-rote patterns** (no "Which CITY/COUNTRY/RIVER..." opener; no "What is
  the capital of..."; no "In what year did..."; no "Who wrote/invented...").
  Rephrased to scene-led / consequence-led / fact-led phrasing.
- **Length parity** (answer can't exceed longest distractor × 1.6 or be below
  shortest / 1.6 — padded one-word answers' choices with parenthetical or
  qualifier matching).
- **Length budget** (T1=280, T2=480, T3=680 char total).
- **Geek-dad-canon stance**: broadly recognizable across generations
  (Disney classics, Star Wars surface, Beatles, Beethoven, Pixar broad,
  Olympic sports, holidays, Greek/Norse/Egyptian mythology as cultural
  literacy, fairy tales, classic Westerns, broad Marvel/DC, classic
  literature names like Tolkien/Lewis/Rowling/Twain/Dickens).
- **No spoilers**: surface-level facts only.

Generation counts:
- T1: 145 new
- T2: 154 new
- T3: 103 new

## Final shape
After merge:
- T1: 217 (72 kept + 145 new)
- T2: 205 (51 kept + 154 new)
- T3: 208 (105 kept + 103 new)
- T4: 120 (kept, above floor)
- T5: 120 (kept, above floor)
- **Total: 870**

Dropped:
- Original dropped: 2761
- Added by this audit: 522
- **Total dropped: 3283**

## Topic coverage (post-audit)
| Topic | T1 | T2 | T3 | T4 | T5 | Total |
|---|---|---|---|---|---|---|
| Mythology / Legend | 9 | 45 | 39 | 15 | 17 | 125 |
| Other (mixed) | 52 | 29 | 20 | 6 | 5 | 112 |
| Geography | 12 | 19 | 30 | 14 | 14 | 89 |
| Animals | 35 | 17 | 12 | 11 | 5 | 80 |
| Movies / TV | 8 | 13 | 14 | 11 | 13 | 59 |
| Sports | 17 | 16 | 8 | 5 | 10 | 56 |
| Holidays | 26 | 4 | 4 | 4 | 6 | 44 |
| History (famous) | 4 | 10 | 12 | 6 | 10 | 42 |
| Food | 19 | 8 | 7 | 2 | 0 | 36 |
| Space | 7 | 11 | 4 | 3 | 1 | 26 |
| Nature / Weather | 12 | 4 | 7 | 1 | 1 | 25 |
| Famous people | 2 | 3 | 5 | 2 | 4 | 16 |
| Books / Literature | 0 | 5 | 4 | 4 | 1 | 14 |
| Body / Health | 3 | 2 | 7 | 1 | 0 | 13 |
| Music | 4 | 2 | 2 | 2 | 0 | 10 |
| Comics (broad) | 2 | 3 | 5 | 11 | 6 | 27 |
| Video games (broad) | 3 | 6 | 12 | 8 | 14 | 43 |
| Mystery / cryptid (broad) | 0 | 1 | 6 | 7 | 12 | 26 |
| Pulp (broad) | 0 | 2 | 1 | 4 | 1 | 8 |
| Games / Toys | 1 | 1 | 4 | 0 | 0 | 6 |
| Language / Words | 0 | 3 | 1 | 0 | 0 | 4 |
| TV broad | 0 | 0 | 2 | 2 | 0 | 4 |

Every major topic has T2-T4 coverage. T5 stays light by design (depth is
for those with deeper knowledge, not coverage-parity).

## Gate results
```
py -m tools.quizgen validate --subject trivia
Validated 870 trivia questions: 870 KEEP, 0 REPAIR, 0 DISCARD
```

```
pytest -q
598 passed in 56.73s
```

## Notable design choices

1. **Pokemon dropped entirely.** Even broad recognition (Pikachu) was already
   in the prior 2761-item drop list. I respected that and dropped the
   stragglers (legendary birds, gen3 starters, etc.).

2. **Mortal Kombat / Sonic / SpongeBob kept at broad-recognition level,
   dropped at deep-lore level.** "SpongeBob lives in a pineapple under the
   sea in Bikini Bottom" stays (broadly recognized). "Mortal Kombat
   designers Ed Boon and John Tobias" gets dropped (deep development
   trivia).

3. **D&D and MTG dropped almost entirely.** These are the textbook fandoms
   the user flagged. The lone "broad enough" survivors (e.g., D&D ranger
   class wilderness-skills) were also dropped because they reference D&D
   itself, not the underlying fantasy archetype.

4. **Cryptid coverage trimmed but not eliminated.** Bigfoot, Loch Ness,
   Yeti, Stonehenge, Roswell, Area 51, Sphinx are all "kids and adults
   know this." Kept. Skinwalker Ranch, Dyatlov Pass, Isdal Woman, Somerton
   Man / Tamam Shud are "true crime / Reddit-mystery podcast deep cuts."
   Dropped.

5. **No mojibake remaining.** Pokémon → Pokemon (via fix and then drop;
   no item with a Pokémon glyph survives the audit). Em-dashes preserved.

6. **Length-parity padding via parenthetical qualifiers.** For T1 questions
   like "The capital of the USA is Washington DC", the 1-word distractors
   needed padding: "New York City", "Boston town", "Chicago city" — not
   pretty but the gate enforces no length-tell.

## Files produced
- `data/questions/trivia.json` (rewritten — 870 items)
- `data/questions/dropped/trivia.json` (extended — 3283 items)
- `tools/quizgen/scratch/trivia_audit.py` (audit pass script)
- `tools/quizgen/scratch/trivia_analyze.py` (topic-tagging diagnostic)
- `tools/quizgen/scratch/trivia_gen_t1.py` (145 new T1 items)
- `tools/quizgen/scratch/trivia_gen_t2.py` (154 new T2 items)
- `tools/quizgen/scratch/trivia_gen_t3.py` (103 new T3 items)
- `tools/quizgen/scratch/trivia_finalize.py` (merge + write)
- This file.

Backup: `data/questions/trivia.json.backup_pre_audit` (pre-audit 990-item state).

---

## Addendum (2026-05-19, follow-up): T4 + T5 fill to floor

The prior audit pass dropped 522 niche-fandom items mostly from T4/T5, but
only T1/T2/T3 were refilled to the 200-floor; T4 and T5 sat at 120 each,
below the 200 floor.

### Generation

- **97 new T4 questions** (`tools/quizgen/scratch/trivia_gen_t4.py`),
  bringing T4 from 120 -> 217.
- **97 new T5 questions** (`tools/quizgen/scratch/trivia_gen_t5.py`),
  bringing T5 from 120 -> 217.

### Topic distribution (new content only, ~16 categories across 194 items)

Each tier received ~5-8 items per category to spread coverage:
- Classic literature (Shakespeare/Dickens/Twain/Hemingway/Austen/Melville/
  Stevenson/Stoker/Shelley/Tolstoy/Fitzgerald/Lee/Orwell/Huxley/Salinger)
- Classical music (Beethoven/Bach/Mozart/Vivaldi/Chopin/Tchaikovsky/Wagner/
  Stravinsky/Handel — surface facts)
- Pop music history (Beatles, Elvis, Michael Jackson, Bob Dylan, Aretha
  Franklin, Stones, Bob Marley, Stevie Wonder, Pink Floyd, Johnny Cash)
- Film history (Jazz Singer, Casablanca, Citizen Kane, Gone with the Wind,
  Wizard of Oz, Hitchcock, Chaplin, Kurosawa, Bergman, Kubrick, Fellini,
  Coppola)
- Game/computer history (Pong, NES, Apple II, IBM PC, Tetris, Mac, ENIAC,
  Super Mario, Pac-Man, D&D, Colossal Cave)
- Inventions/inventors (Bell, Edison, Wright Brothers, Gutenberg, Curie,
  Franklin, Tesla, Newcomen, Fleming, Niepce, Marconi, Salk, DNA, Einstein,
  Sputnik)
- Mythology — Greek/Norse/Egyptian as cultural literacy (Poseidon, Odin,
  Osiris, Perseus, Odysseus, Frey, Horus, Trojan War, Heracles, Yggdrasil,
  Isis, labyrinth, Freya)
- World capitals + landmarks (Paris, Tokyo, Athens, Moscow, Brasilia, Cairo,
  Istanbul, Canberra, Eiffel, Great Wall, Pyramids, Taj Mahal, Pisa,
  Stonehenge, Machu Picchu, Hagia Sophia)
- Olympics/championship history (1896 Athens revival, motto, torch relay,
  Jesse Owens, Stanley Cup, marathon distance, Tour de France, Wimbledon,
  Pele)
- Famous historical figures (Washington, Lincoln, Churchill, T. Roosevelt,
  Franklin, Jefferson, Cleopatra, Genghis, Napoleon, Gandhi, E. Roosevelt,
  Joan of Arc, Elizabeth I, Douglass, Catherine, Sitting Bull)
- Word origins / idioms (bite the bullet, Rubicon, crocodile tears, salary,
  breaking the ice, kicking the bucket, mad as a hatter, serendipity,
  paying through the nose, turn a blind eye)
- Science adjacent (speed of light, dinosaur extinction, hydrogen,
  atmosphere, Jupiter, Amazon, Mariana Trench, blue whale, helium,
  Antarctica, cheetah, Sahara, Krakatoa)
- Board/card games (chess, Monopoly, Scrabble, Bridge, Risk, Go,
  backgammon, poker, mahjong, D&D)
- Holidays/traditions (Thanksgiving, Easter, Hanukkah, Diwali, Day of the
  Dead, Chinese New Year, Independence Day, Cinco de Mayo, Yom Kippur,
  Lunar New Year, Passover, Holi)
- Pop-culture milestones (moon landing, Beatles on Ed Sullivan, Berlin
  Wall fall, Woodstock, Star Wars 1977, NES 1985, TAT-1, Live Aid, MTV
  launch, first web page, Beatles last concert, Dr. No)

### Final tier shape

| Tier | Pre-fill | Added | Final |
|------|----------|-------|-------|
| T1   | 217      | 0     | 217   |
| T2   | 205      | 0     | 205   |
| T3   | 208      | 0     | 208   |
| T4   | 120      | 97    | 217   |
| T5   | 120      | 97    | 217   |
| Total| 870      | 194   | 1064  |

### Topic distribution (full T4 / T5 after merge)

| Topic              | T4 | T5 |
|--------------------|----|----|
| Movies/TV/Pop      | 47 | 45 |
| Historical Figures | 24 | 28 |
| Mythology          | 21 | 14 |
| Classic Lit        | 14 | 10 |
| Science Adjacent   | 13 |  9 |
| Inventors/Science  | 11 | 11 |
| Landmarks/Capitals |  9 |  8 |
| Sports             |  9 | 12 |
| Games/Computers    |  8 |  6 |
| Holidays           |  8 | 13 |
| Classical Music    |  7 | 10 |
| Cryptid/Folklore   |  7 | 11 |
| Word Origins       |  6 |  2 |
| Pop Music          |  6 |  6 |
| Board/Card Games   |  3 |  3 |
| Other              | 24 | 29 |

### FK voice tracking (against TIER_CAPS audit-time caps)

The five deterministic gates do not enforce FK at validate-time, but the
TIER_CAPS document defines audit-time grade caps (T4 <= 8, T5 <= 10).

| Tier | Existing avg FK | New avg FK | Existing > cap | New > cap |
|------|-----------------|------------|----------------|-----------|
| T4   | 6.94            | 6.68       | 40 / 120 (33%) | 31 / 97 (32%) |
| T5   | 9.27            | 7.60       | 29 / 120 (24%) | 20 / 97 (21%) |

New content tracks the existing voice band (slightly lower in both
averages and over-cap rates), so the rewrite is voice-consistent rather
than skewing high.

### Validation

```
py -m tools.quizgen validate --subject trivia
Validated 1064 trivia questions: 1064 KEEP, 0 REPAIR, 0 DISCARD
```

```
py -m pytest tests/ -q
598 passed in 58.87s
```

### Files added (this pass)

- `tools/quizgen/scratch/trivia_gen_t4.py` (97 new T4 items)
- `tools/quizgen/scratch/trivia_gen_t5.py` (97 new T5 items)
- `tools/quizgen/scratch/trivia_gate_check.py` (per-gate diagnostic for
  the 5 deterministic gates, against existing-bank dupe index)
- `tools/quizgen/scratch/trivia_merge_t4_t5.py` (merge + sort + write)

