# Bug bash report, 2026-10-16 (after v3.1.0)

Eight reviewers each attacked a frozen copy of v3.1.0 from one angle:

- combat and monsters;
- items, identify and weight;
- the quiz engine and question banks;
- saves;
- UI and art;
- world, quests and encounters;
- a monkey fuzzer;
- code quality and the release pipeline.

## Bottom line

**Nothing crashed in normal play.** The fuzzer ran about 5.3 million random actions across 3,246 games: every hero, floors 1 to 100, 12 window sizes and 11,160 save-and-reload checks. It found no crash and no softlock. One error does escape: F11 on a display that cannot go fullscreen, now fixed.

**About 211 real faults were found.** Most are the quiet "does the wrong thing" kind, and about 27 are serious (exploits, lost items, broken quest steps).

**About 165 are fixed, in five fix batches.**
- Every fix has a test that fails on v3.1.0 and passes now: 168 new tests.
- The suite is at **2,631 passing**, up from 2,413.
- The work is 45 commits on top of v3.1.0, committed locally on `main`. **Nothing is pushed.**

**About 45 are your call** (listed below with my recommendation for each). They change design, balance or content.

**The fuzzer was re-run on the fixed code:** 400 games, 507,000 actions, all 34 heroes, 1,001 save reloads.

- No crash, no softlock and no new failure.
- The only things it flagged were two already known:
  - pets stacking with you (your call #18);
  - going over the weight limit for a moment when a Strength potion wears off on the same turn as a pickup, which is harmless.

**Not played.** All of this is tested and simulated, not played. The play-test list is at the end.

## The serious ones, all fixed

### Exploits
- **Ring enchanting:** two rings of the same kind on one floor shared their stats, so cursed enchant scrolls could raise a stat permanently. This is last bash's exploit coming back by a different route.
- **Free archer rerolls:** archers never used up the Tablet of Destinies or Scheherazade reroll, so every shot got one.
- **Lethal blow that heals:** the Armor of Ragnarok and Crown of Brahma's first-hit protection healed a nearly dead hero to full from a blow that should have killed them.
- **Harpe and the Sword of Damocles killed any boss.** Harpe's chain-15 petrify and Damocles' auto-kill both worked on gate bosses, seal demons and mini-bosses. Both now spare the foes the wand of stoning spares.
- **Reach weapons through walls:** spears and staves hit through solid walls at monsters you could not see.
- **Paralysis bypass:** while paralysed or asleep, the @ screen still let you equip or drop, and the stairs still let you escape a fight.
- **Endings:**
  - A gain-level potion on floor 100 with the Stone skipped Death's chase and still gave a full victory. Death now comes whenever the Stone leaves floor 100, by any route.
  - Abaddon could lose his guard for good with one prayer and a step upstairs.
  - The Last Judgment's +50% to Abaddon could be dodged by visiting floor 100 first.
  - The chicken popup gave unlimited Flux Capacitors.
- **Free identifies:**
  - Esc on the Scroll of Identify picker saved a free identify for later.
  - The true name or hidden enchant of unidentified items leaked in about 15 places: "welded to you", the combat panel, the shop, the floor comparison line, the "Journey Restored" popup, the equip menu, Kit materials and more.
  - All item names now go through one display-name path.

### Lost items and broken quests
- **Belt over a cursed belt destroyed the new belt.** The quiz passed and the message printed, then the belt vanished.
- **Drop while phasing:** an item dropped while phasing through rock was lost in the wall (the fuzzer lost Chrysaor this way).
- **The Woman's Beard** (a Gleipnir ingredient) could not be reached on foot in 81% of runs, because its secret door was cut into a room corner. It is now reachable in 200 of 200.
- **The reachability check was eight-way but the hero walks four-way.** So:
  - quest pieces were left behind diagonal gaps;
  - teleports could strand you: 86 of 400 on one test floor, now 0.
- **Quest altars, the forge and fountains were cut off by later lava or water,** costing a quest step in about 1 run in 10. Now 0.
- **Ariadne's Thread** was pulled out of its sealed shrine in every run, skipping that quest step.
- **NPCs took your scrolls and potions.** They silently took the first scroll or potion in your pack, which could be the Lake of Fire scroll for the secret ending. They now ask, and never take quest pieces or uniques.
- **Divine Intercession** could hand you a unique you had already found, or a quest-only item.

### Saves and quitting
- **Crash after a finished run:** a crash right after a hero died, won or fled wrote the finished run back as a resumable save.
- **The Delete key on the title screen** erased a save with no "are you sure?" It now asks.
- **A save that loads but will not restore** used to loop on "please try again" forever. It is now set aside with a notice.
- **Spell refunds:** quitting while aiming a spell lost its MP, and cancelling a free cast refunded MP never paid.
- **Necronomicon:** quitting mid-recital dodged the failure.

## Medium and small fixes

- **Combat:**
  - Healer and summoner monsters no longer club you from across the room.
  - Heal-block (Gae Dearg, rupture) now stops monster healing.
  - Magic missiles and Smite no longer kill friendly NPCs.
  - Time-stopped monsters no longer bite pets.
  - The Ankh's bonus no longer stays after it shatters.
  - The reflecting aura no longer strips your good effects.
  - Fafnir no longer steps half into walls.
- **World:**
  - Floor 1 no longer starts with stacked monsters (1 game in 37).
  - Mini-bosses are no longer lost on maze floors.
  - Mimics no longer spawn on your tile.
  - Alarm traps wake monsters instead of turning rooted ones hostile.
  - Every hero starts at full HP and MP.
  - The Sibyl and Eye of the Storm traits unlock correctly.
- **Interface:**
  - The character sheet lists every item, not just the first 26.
  - The Kit shows real weights (food no longer reads "Weight 0").
  - The weight readout never contradicts Burdened.
  - "Cursed A Rough Pelt" now reads "Cursed Rough Pelt".
  - Popups no longer close when you press Alt.
  - Numpad Enter and numpad 8/2/4/6 work everywhere.
  - F11 works on the title and in Study Mode, and is listed in help.
  - The quiz footers only show keys that work. "Space Cancel" used to waste your swing.
  - Clicking the window X after death quits properly.
  - Resizing no longer stalls, the map draws only what is on screen, and image caches no longer grow forever.
- **Quiz:**
  - Study Mode now checks capital letters (all four grammar choices used to count as correct).
  - A long frame such as an autosave can take at most 0.25 s off the combat clock.
  - About 560 explanations no longer show web addresses or wiki citations.
  - Two AI questions with cut-off choices, and some garbled text in trivia, are fixed.
- **Release:**
  - The release now runs the whole test suite first.
  - It builds on the same Python you develop on, with pinned library versions.
  - It checks that the tag matches the version number.
  - It is ready for the Ubuntu 26 switch on October 19 and the Node 20 deprecation.
  - Installer upgrades now remove old files.
- **Housekeeping:**
  - Tests no longer write into your real save folder.
  - Dead code is removed.
  - About 25 error handlers that failed silently now log.
  - Empty tests are rewritten.
  - Stale docs are corrected.

## One content change to check

To stop healer and summoner casters clubbing you from range, the combat fix gave **8 casters a proper ranged spell** in `monsters.json` instead of leaving them to walk up and melee: Bone Shard, Ice Wave, Litany of Pain, Void Invocation, Summoner's Gesture, Snake-Pipe Drone, Miasma and Tide Invocation. If you would rather they close to melee, I will revert the data part.

## Your calls (my recommendation in brackets)

**A rule breach first.** The Deadite is built from the floor number at runtime (`game_magic.py` ~3962). That breaks LORE NOT FLOOR. [Fix it: give it fixed stats from its lore in `monsters.json`.]

### Quiz and timer
1. **The C context card pauses the combat clock** for as long as it is open, on every question, so maths attacks can be untimed. [Let it pause once per question, and keep it open only as long as needed to read.]
2. **19 questions contain their own one-word answer** in the stem (Esther, Sinai, Totoro and others). [Rewrite them, and add a one-word check to the leak test.]
3. **The 5 s minimum timer** is applied before the status penalties, so a confused and blinded child gets 2 s. [Apply the minimum after the penalties.]
4. **208 explanations use builder jargon** ("the three distractors", "keyed answer"). [Reword them.]
5. **The Mjolnir forge mystery runs on the combat clock.** [Untime it like the other mysteries.]
6. **One economics answer is "wtfhappenedin1971.com".** [Replace it in a kids' game.]

### Items
7. **About 40 scripted rewards** (NPC gifts, the Sword of Michael and others) set "identified" but no longer actually identify. [Fully identify quest and divine gifts.]
8. **Picking up a potion can reveal its blessing,** because unknown copies only merge with a matching stack. [Merge only when the blessing is known.]
9. **Unopened chests, even mimics, can be carried** (30 lb), and a floor-1 chest opened deep pays deep loot. [Make chests not pickable.]
10. **Every corpse weighs 5 lb,** rat or dragon. [Weight by monster size.]
11. **Knock and the Wand of Opening never open chests.** [Make them open locked chests.]

### Combat
12. **Chain stuns can lock a boss** for the whole fight. [Cap stuns on named foes, with a short immunity afterwards.]
13. **"Strike now N damage" in the combat strip** leaves out STR, blessings and shields, so it differs from the real hit. [One shared damage calculation; a moderate refactor.]
14. **Weapon materials' vulnerabilities do nothing** (cold iron against demons and so on). [Wire them in; they are written in the lore.]

### Interface
15. **Below 1280×720, or on a laptop at 125% scaling, screens break,** and the game ignores Windows display scaling. [Support 1280×720 as the floor with a compact layout below it, and turn on DPI awareness.]
16. **No message history.** [Add a scroll-back log on a key.]
17. **193 items borrow another item's picture,** some with the opposite meaning (the weaken wand shows the empowerment wand). [Fix the opposite ones first, then add art.]
18. **Walking into your pet stacks you on its tile.** [Swap places, like most roguelikes.]
19. **Portrait monitors** lay out badly. [Low priority.]

### Saves
20. **Save and Exit during a fight's quiz can kill the hero** with no death screen and no high score. The high score is written from inside the drawing code. [Record the score at game over, not in the drawing code.]
21. **Two copies of the game under one name fight over one save.** [Single-instance lock.]
22. **Names differing only in case or punctuation share a save file** ("Bob!" and "bob"). [Make save names unique.]
23. **Old saves keep old hero-build flags,** so an old Dad save still earns boss scrolls. [Refresh the flags from the current builds on load.]

### World
24. **Ordinary loot behind water or lava** sits on 14% of floors. [Leave it: levitation is the answer, and that is a reward.]
25. **The floor-100 altar can be retried until you get it right.** [One attempt per visit.]
26. **Sisyphus' Boulder** does not overload an ordinary hero, so the trial counts nothing. [Make the trial count distance carried rather than being over the limit.]
27. **Two Mjolnirs share one id.** [One Mjolnir.]
28. **Only melee damage feeds the trait counters** (traps, poison and falls do not). [Count all damage.]
29. **Cerberus can be farmed on a staircase.** [Spawn it once per floor.]
30. **The Codex helper ignores its damage table** (254 damage on floor 1). [Use the table.]
31. **Hero powers waste their cooldown,** still open from last bash. [Refund the cooldown when a power does nothing.]
32. **The healing picker lists exactly your unidentified healers,** which leaks what they are. [List every potion.]
33. **Encounter effects print 80 to 200 turns but are capped at 60.** [Print the real number.]

### Code and process
34. **About 400 tests check source text** instead of behaviour. [Replace them as each area is touched.]
35. **The suite takes about 6 minutes.** [Mark the slow UI gates and run them in CI.]
36. **Saves are pickles,** so a save file shared by someone else could run code. [Fine for a family game; revisit if saves are ever shared online.]

### Still open from last bash
- Same-question maths pairs.
- Maths stems repeated across tiers.
- The blurb answer-leak ratchet.

## Please play-test these

They are easy to reach in a few minutes:

- **The title screen:** Delete now asks Y/N.
- **A fight:** the quiz footer now reads "Esc Give Up" or "Space Stop Here", and your HP is shown.
- **Equip:** put on a cursed item and you should see the new "It feels wrong" message; wearing it now marks the curse known.
- **Paralysed or asleep:** the @ screen and the stairs do nothing.
- **The Kit and equip menu:** unidentified gear hides its stats and material, weights show decimals, and labels are capitalised.
- **Numpad and F11:** play with the numpad (Enter and 8/2/4/6), and press F11 on the title screen.
- **P next to a chest and a trap:** P now opens the chest first. To disarm a trap beside a chest, step to another side.
- **Floor 1:** you start at full HP and MP.

## Evidence

All findings, drivers and reproductions are in `_bugbash_2026_10_16/<angle>/FINDINGS.md`. The angles are combat, items, quiz, saves, ui, world (with four sub-reports), code and monkey.

---

## Your rulings of 2026-10-17, applied

Every numbered call is implemented, each with behaviour tests. All six batches are merged and the suite is green at **2,777 passing**, slow UI gates included. Nothing is pushed.

| # | What was done |
|---|---|
| 1 | The context card stops the combat clock **once per question**. Opened again on the same question, the clock runs, and the card says so. This metahack is kept on purpose (saved as a standing rule). |
| 2 | The 19 give-away stems are rewritten in each subject's voice. The leak test now catches one-word answers. It also found 10 older cases, held in a shrink-only list for the question-bank bash. |
| 3 | The 5 s minimum is applied after status penalties. |
| 4 | About 460 explanations (not 208) are cleaned of builder jargon, and the author-notes test now covers them. |
| 5 | The Mjolnir forge quiz is untimed. Combat is now the only timed quiz. |
| 6 | The "wtf" answer is replaced: the 1971 productivity-vs-pay chart. |
| 7 | Quest and divine gifts are fully identified, and their type becomes known. |
| 8 | Unknown copies only stack once their blessing is known. |
| 9 | Chests cannot be picked up; you open them in place. A chest carried in an old save is set down on load. |
| 10 | Corpses weigh by lore size: tiny 2, small 10, medium 40, large 150, huge 400 lb (`data/monster_sizes.json`). |
| 11 | Knock and the Wand of Opening open chests. Every chest is locked by default. |
| 12 | Boss stuns last at most 2 turns, then 3 turns of immunity. Asterion was stunned 30 turns of 30; now 6–8. |
| 13 | One damage calculation for the hit and the "Strike Now" preview, checked across 22 weapons × 8 materials × 8 targets × 6 chain lengths. Side effect: the dagger's Backstab now works on sleeping targets. |
| 14 | Material weaknesses take effect: +25% when, for example, cold iron meets a demon or wood meets fire, with a message saying why. |
| 15 | 1280×720 is the floor. Below it the UI compacts down to 0.75 scale (never under the 16 px text floor). The game is per-monitor DPI aware, and the window opens inside the taskbar edge. The UI gates now also run at 1093×614 and 1080×1920. |
| 16 | Message history on **L**: the log keeps 500 lines, and the history scrolls. |
| 17 | All 193 borrowed item pictures now have their own art: 143 newly drawn, 50 reclaimed. No picture contradicts its item. See `ITEM_ART_GAPS_BEFORE_AFTER.png`. |
| 18 | Walking into your pet swaps places with it. |
| 19 | Portrait monitors: the title wheel is centred with Top Runs below it, and the character sheet is two rows of two panels. |
| 20 | The high score is written at game over. A Save & Exit that kills the hero shows the death screen. |
| 21 | Two copies of the game never clobber a newer save. A manually copied save still loads (metahack kept). |
| 22 | Every name gets its own save file. Old saves are still found. |
| 23 | Hero-build rule flags are refreshed on load. |
| 25 | The floor-100 altar takes one prayer per visit. |
| 26 | Sisyphus counts steps carried with the Boulder. |
| 27 | One Mjolnir: the anvil gives the real unique and claims it. |
| 28 | All damage and statuses feed the trait counters. |
| 29 | Cerberus counts each staircase once. |
| 30 | The Codex helper uses its damage table. |
| 31 | A hero power that does nothing refunds its cooldown. |
| 32 | The healing picker shows only identified healers. |
| 33 | Encounter effects print their real turns. |
| 35 | Slow UI gates are marked `slow` and run in CI. Run them locally with `--run-slow`. |
| Deadite | Fixed floor-25 stats from its lore. The Necronomicon's horde is a weaker "risen deadite". The LORE NOT FLOOR test now catches any monster stat built from the floor number. |

### Needs your eyes

- **Codex helper (#30): it is much weaker.** Its chain-5 bite drops from about 289 to about 20. If that's too weak, the dice in its table are the place to tune.
- **Mjolnir (#27):** Brokkr's Anvil (floors 33–45) now gives the real unique hammer (base 515, tier-5 maths every swing).
- **Sisyphus (#26):** counting carried steps makes the 15-step trial easy. Raise the number if you like.
- **Eye of the Storm (#28):** now that traps and poison count as damage, it is harder to earn.
- **The Deadite** is a real floor-25 fight now if you help the Moaning Woman. The new risen deadite reuses the Deadite's art.
- **Item art:**
  - the rainbow master-intellect ring is the most cartoony of the set;
  - the chain-lightning book looks a lot like the plain lightning book;
  - the soul-drain wand's wisp is faint.
- **Small screens:** if you have a laptop at 125–150% scaling, check how sharp the text looks.
