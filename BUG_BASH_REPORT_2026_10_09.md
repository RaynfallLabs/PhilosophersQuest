# Bug bash report, night of 2026-10-08 to 09

Eight reviewers each attacked a frozen copy of the game from one angle, and all eight have reported.

**Bottom line:** no reviewer found a crash in normal play, including a headless "monkey" that played about 3.1 million random actions across roughly 12,000 games as every hero on every floor. They found about 115 real faults, most of them "does the wrong thing quietly". I fixed about 80 in code and data and left the rest for you because they are design calls, balance-affecting, or large. Everything is committed locally (nine commits after `b9a07b7`, ending `48b8b469`, plus this report); nothing is pushed. The suite is at 2,166 passing. Nothing has been played by a person.

## Read these first

1. **The game has sound now.** All 14 sounds had always failed to build, silently. They build now, so you will hear the game for the first time. I have not heard it: volumes and pitch are untested, and there is no mute key.
2. **I was wrong about unidentified items.** I told you they showed stand-in pictures. They did not: an unidentified wand, potion, scroll, book, ring or amulet was drawn with its true picture, and the new art made that worse (the healing wand shows a green cross). They now show one of six neutral looks chosen by the item's unidentified name.
3. **About one run in nine could become unwinnable.** A seal keeper could spawn on ground cut off by water or lava, and its stair then stayed sealed. Fixed and re-measured: 0 of 280 seal floors, and all four Gleipnir ingredients reachable on 40 of 40 floors each.
4. **"Exit without saving" deletes the run.** That was deliberate in the code (to stop save-scumming) but the dialog said the opposite. I changed the wording to "Abandon This Run (Deletes The Save)". If you would rather N kept the save, say so.
5. **One regression was mine.** The sweep I added two days ago for unnoticed boss deaths also "slew" any NPC that simply left: helping the Lost Girl printed "The Lost Girl is slain!" and dropped her corpse. Fixed.

## What was fixed

### Could end or ruin a run
- Seal keepers, mystery shrines and their keys, the trader and quest pieces are moved within reach when floor generation strands them. A teleport only lands where the stairs can be walked to. Phasing that ends deep in rock finds the nearest open tile, however far (it searched two tiles and gave up).
- A save that exists but will not read was treated as "no save": the game started a new hero and overwrote it. It is now set aside as `save_<name>.pkl.unreadable-<time>` and you are told.
- A save that loads partly crashed at every launch under that name. It now bounces to the welcome screen with a message.
- Dying to a floor trap, or to a fall into a dug pit, skipped game over: the save stayed (reload and carry on) and no bones were left.
- A finished run could be saved again by closing the window on the ending popup, and an error on the death screen put a dead hero back in play.
- Named items stopped being once-per-run after any load (one item turned up four times in a test run).

### Exploits
- Every "once a floor" charge recharged on any staircase: death wards, absorbs, free casts, escapes, Mulan's altar heal, descent haste, Curtana's allowance. Six lethal blows in a row were survived on one charge each. They now come back only on a floor reached for the first time.
- Gold doubled each time it was dropped and picked up with a gold ring on (100 became 102,400 in ten drops).
- Excalibur and the Amulet of Life Saving gave a new life every time they were taken off and put back on.
- A heroism potion plus the Pharaoh's Crook left +2 Strength for good, once per potion.
- Enchant-ring scrolls changed a ring's number without changing the stat: cursed scrolls turned a ring's points into permanent ones. Copies of one ring also shared one set of numbers.
- An absorb that caught a lethal blow healed the wearer (5 health, 50-point blow, left at 50).
- The polymorph trap turned pack junk into named items, including the Aegis the Medusa quest is for.
- Quitting on an encounter's outcome page and reloading repeated the reward and the karma.
- Quitting mid-question gave some actions a free retry and made others lose what they had spent. A question left unanswered now counts as wrong.

### Did nothing, or did the wrong thing
- Stunned and Frozen did nothing to monsters (thirteen weapon specials and four spells apply them and announce them).
- Sleeping, held and friendly creatures bit pets; the Lost Girl could kill one. Area spells and pet specials killed flavor NPCs, the unicorn and the Heavenly Host.
- Floors began with monsters stacked on one tile (about one floor in twenty) or standing in water; loot lay under water. Two-by-two monsters walked onto other monsters, and pets could not attack them from two sides.
- Zoo, graveyard and barracks sleepers all woke 60 turns after you arrived.
- A boss kill could be handled twice (two drops, two gifts).
- Pandora's Coffer could never pay its real reward. The Fleece Altar and Mimir's Well quizzes never ended on right answers.
- The potion of restore strength never restored anything. Diogenes' Lantern could not be earned.
- Tier-1 enchant scrolls did nothing when uncursed. Remove-curse never reached a cursed belt. A belt could not be worn with four rings on.
- A weapon thrown at a wall landed inside it and was lost, the Broken Blade of Gram included. Bows fired the rarest arrows first.
- A one-point poison or bleed tick was rounded to nothing by any resistance at all.
- Tidal Crash never hit the first tile of its line. Rewired traps bypassed the cap on holding a named foe.
- Study Mode: the right answer was always choice 1.
- Two traits unlocking on one answer dropped you out of the quiz.
- Four old-save migrations skipped every floor but the current one.
- Damaged score, answer-time and bones files could stop the game opening, lose every quiz result, or put a 9,000-health ghost on floor 4.

### Content and text
- Maths: "Round 65 to nearest 10" was keyed 60 (now 70, and the generator's rounding is fixed). Three fraction questions offered a distractor equal to the answer. Three divisions were ambiguous and are now bracketed. Seven cube-root questions showed an empty box for the root sign and now read "Cube root of 27 = ?". Two history questions had the same problem with Chinese characters.
- Two hints were false (the Sphinx "forgives most wrong answers"; confusion "moves the answers"). Two mystery texts quoted gold the game no longer pays.
- The Possessed Woman's first option could kill you from dialogue at 5 health or less.
- "The The Whispering Crone summons a Adult Blue Dragon", "You equip the A Dark Curved Blade", "You ponder the A Scorched Gold Ring", "It is the The Seamless Tunic", "You feel fire_resist!", "PER +-1!", "You pick up 12 Iron Arrow x12s", Fenrir's rage line repeating every turn he is held.
- Nine whole sentences were capitalised word by word ("The Dungeon Has Taught You Something..."). That was my over-application of your Title Case rule to sentences; names and labels keep Title Case.
- The help screen silently dropped the last rows of its longest group, so R (read) was never listed.

### Pictures
- All 893 recipes have a picture. None was ever shown before: the 364 that existed were named for an older recipe set, so every recipe was a green asterisk.
- 517 gear combinations borrowed another material's picture (leather gloves drawn as teal plate) and now have their own.
- The Duck of Doom's three pet stages have sprites. A rewired trap keeps its picture in a cyan frame.
- The module that draws the dungeon tiles was hidden from git by a `.gitignore` line (`ENV/` matches a folder called `env` on Windows). It is committed now.

### Other
- The F2 debug overlay (raw ids, monster health) was live for every player, in quizzes too. It now needs `PQ_QA_MODE`.
- The window has a minimum size of 1280x720. Below about 400x300 every panel raised an error, and several screens run out of room below 1280x720.

## Left for you: decisions

These are real, verified, and not fixed, because the fix is a design or balance choice.

| # | What | Why I left it |
|---|---|---|
| 1 | **Monster resistance to slash, pierce and blunt never applies.** The weapon's material is counted as a second damage type and the best multiplier wins. 87 monsters are meant to resist one of these. | Fixing it makes those monsters tougher against the wrong weapon and makes "ignores armor" weapons matter. It changes balance, so the win table needs re-measuring. I recommend fixing it. |
| 2 | **Monsters that attack more than once a turn skip most attack rules** (41 monsters: every mini-boss, seal demon, Tiamat, Asmodeus, Abaddon). No drain heal, no pull, no charge, no pit rule, no reflection, no Nemean hide halving. | Needs the single-attack code and the multi-attack code merged into one. A real refactor; also changes how hard those fights are. |
| 3 | **Death wards only answer a monster's blow.** Poison, traps, starvation and the doom curse kill through the Amulet of Life Saving, the Jade Cicada and Joan's breastplate. The status says "Survive one killing blow". | Moving every ward into one place is a moderate change and makes characters tougher. Your call whether a ward should stop poison. |
| 4 | **Enchant caps.** A material's cap is ignored (copper reaches +5), named armor and shield caps are ignored, and a bow takes its cap from the sword in the other hand. | Which number is the authority: the slot, the material, or the item? |
| 5 | **Weapon class descriptions do not match what happens.** Rapier "uses Dexterity" (it uses Strength); glaive "reach 2 and line attack" (neither exists); dagger backstab never fires on a sleeper; mace, maul and axe texts state different chain rungs and durations from the code. | Either build the mechanics or reword the text. |
| 6 | **Statuses are capped at 60 turns, but 371 recipes and several potions promise 70 to 250.** | Raise the cap for good statuses, or print the capped number. |
| 7 | **Every "N right out of M" mystery fails on the first wrong answer** (and spends its key). I corrected the hint that said otherwise. | Is all-or-nothing what you want for once-per-run shrines? |
| 8 | **Six legendary chain items attune to tier 5 of 5 on five tier-1 questions** (Crown of Brahma, Ring of Gawain, Anklet of Atalanta, Idunn's Apple and two more). | Probably unintended, but it is a difficulty choice. |
| 9 | **`cursed: true` in item data is never read** (Necklace of Harmonia, Hand of Glory, Cursed Lodestone come out uncursed). | Which of the three are meant to be cursed? |
| 10 | **Excalibur has two life-saves** (one on equip, one "cast me away"); the second takes a point of enchantment and gives nothing. | Which one is the design? |
| 11 | **Thrown named spears hit with no question** (Gungnir thrown: 495 damage, no sum). A two-handed bow can be used with a shield. | Possibly intended. |
| 12 | **Three hero portraits are still paintings** (ranger, Robyn, wizard). The reviewer reads them as dark smudges on the map. Pixel versions are drawn and ready. | You have not said whether to replace them. I recommend it. |
| 13 | **Welcome screen: DEL erases a save with one key press and no confirmation.** Names that differ only in punctuation share a save file ("O'Brien" and "O Brien"). | Small, but a child can lose a run. |
| 14 | **Permanent levitation makes Sigurd's pit unusable** against Fafnir (you float over it). | Edge case; needs a rule. |

## Left for you: smaller and bug-adjacent

- **Question data.** About 1,400 context blurbs contain the answer to a question in their own ladder (the reviewer hand-checked 20 flagged rows: 16 real). 2,713 of 3,559 blurbs are under your 200-word rule (cooking averages 53 words). Four "Which is a factor of N?" stems appear twice in one tier with different answers; 52 maths stems appear in two tiers. The full table is in `_bugbash_2026_10_09\QUIZ_DATA_FINDINGS.md`.
- **Hard to see.** Explored-but-not-visible rooms nearly vanish on the full map with the new dark tiles; dug pits are a thin brown outline. Lowering the dimming and drawing pits with the pit picture would fix both.
- **Small layout faults** at the new minimum size or below: the spell menu footer collides once you know 7 spells; Study Mode text overflows; long names overflow the welcome name box; shop and equip lists cut long names with no ellipsis.
- **Trait popup lost** when the trait is earned by the answer that ends a quiz (the trait is granted; only the ceremony is missing).
- **Hero powers** burn their full cooldown with nobody in sight.
- **Five builds start below full health or mana** (Corwin 30 of 36, Cain 33 of 39 and three more).
- **Worn gear weighs nothing**, against its own comment; there are no encumbrance steps, only a refusal to pick up.
- **Slowed** skips moves only: waiting, drinking and casting are never slowed.
- **Stats have no floor**: Constitution drained below zero and restored returns extra health.
- **Pets** ignore "Stay" on stairs; dead pets are never removed from the list; pet special damage has no type.
- **Dead data and code**: 34 wand effects no wand has; 19 functions nothing calls; seven conditions that can never be true; recipe `flavor` lines (893) and ingredient `temp_desc` lines (530) are never shown; 791 item pictures match no item; `ancient_lich` can never spawn; eighteen monsters' health dice can roll zero.
- **Floor generation cannot be seeded**, so a bad floor cannot be replayed. That is why one test failed once last week and never again. Worth fixing for future bug hunts.
- **The test suite writes into the repository** on every run, and 177 tests only check that a line of source text exists. I added 20 more of that kind tonight where behaviour could not be reached cheaply.
- **`CLAUDE.md` lists `src/help_screens.py`**, which does not exist.

## What was covered

| Reviewer | Scale |
|---|---|
| Monsters and bosses | All 529 monsters, about 58,000 monster turns; 3,200 generated floors; 321 kill paths; every boss, seal, trap and pet |
| Save and load | About 1,900 save/load round trips; your real Cain save played forward 8,600 actions; 30 runs of the real launch path; damaged files of every kind |
| Quiz and content | 2,993 engine cases; all 32,642 questions; 2,415 maths answers recomputed; 1,239 encounter option runs; all 14 mysteries |
| Character systems | 12,000 generated floors; about 500 status cases; all 33 builds and 19 hero powers; every per-floor grant |
| Items | 64,250 weapon attacks; about 6,900 consumable uses; 164 accessories; 3,572 recipe cooks; 440,000 loot rolls |
| Screens and art | 53 game states at 10 window sizes; about 6,100 key events; all 4,943 sprite files; about 500 sprites read by eye |
| Static analysis | Every call site and import checked against the real classes; 330 fuzzed sessions with a hook counting swallowed exceptions; the suite run in four orders |

Checked and found sound: no undefined names, no missing methods, no broken imports, no dangling ids between data files, no state the game cannot leave, no double-apply on load, the CON migration, stat caps under stair dancing, every boss floor and gift menu, Death's chase, prayer, the trader, and the rock/wall drawing rule (no leak of secret doors).

## What I did not do

- **Nothing has been played by a person.** I re-ran the reviewers' own reproductions for the serious fixes and they pass; the smaller fixes are covered by tests or by reading.
- **The win table is not re-measured.** Tonight's fixes pull both ways: wards no longer recharge on stairs (harder), stunned monsters now lose turns (easier), and stat tricks are closed (harder).
- **Old saves.** Your Cain save loads and plays. One-time stat effects already banked in an old save (a doubled gold pile, a permanent +2 Strength) are not taken back.

## The eighth reviewer (crash hunting)

It drove the real game through its real input path: about 3.1 million actions, 12,000 games, 11,400 deaths, all 33 secret builds, floors 1 to 100, seven window sizes, packs of 150 items, 200-monster floors, every status at once, and six scripted runs to the ending. A hook recorded every exception raised inside the game, including swallowed ones.

- **No uncaught exception at any normal window size**, and no hidden programming error (no missing attribute, bad key or bad index swallowed anywhere). The only swallowed errors were the sound failure and the too-small-window failure, both fixed.
- **Its worst finding: the polymorph trap could turn any artifact into the Philosopher's Stone.** It won the game from floor 2. Fixed (the trap now only changes ordinary weapons, armor and shields into ordinary ones).
- It independently found the phasing entombment, the stacked spawns, loot under water and the monster on the arrival stair. All fixed, as above.
- **Also fixed from its list:** dying on the turn a gold drop was spent gave one more action and ended the game twice; stamina could sit above its maximum after losing Strength; dead monsters were never removed from a floor's list; a frame error with a question on screen dropped the question unpunished.

Two more decisions for you from this reviewer:

| # | What | Why I left it |
|---|---|---|
| 15 | **Dad's fist starts in the pack, not on his hand.** Until a child finds Equip, Dad hits for 33; after, for 1.6 million. Every build's starting weapon goes to the pack, but for Dad the weapon is his own hand. | Probably not intended. Say the word and Dad starts with it wielded. |
| 16 | **Fleeing, dying with the Stone and winning all grade A+** (scores 106,100, 151,860 and 156,130). | A scoring choice. |

Missed questions are kept without limit (2,667 after 27,000 turns in one soak run) and saved with the game; harmless at that size, worth a cap some day.
