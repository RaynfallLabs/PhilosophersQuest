# Monster Family Knowledge: Design

*Written 2026-10-18 and checked against the code at `21e39c49`. **Approved 2026-10-18:** Brandon took the recommendation on every decision in section 8 (decision 3 by default).*

Your request: study a monster's corpse and you learn about its whole FAMILY, not just that one kind. Every monster gets a family. As you study more kinds in a family you climb tiers, and each tier gives you an ability against that family: you recognise them on sight, you know when they're on the floor, you resist what they do to you, and you get extra damage or extra seconds against them.

The five decisions I need from you are in **section 8**.

---

## 0. What exists today

- **There are 574 monsters.** `src/monster_classes.py` works out a family from each monster's tags, which gives 11 broad families: undead 118, humanoid 116, beast 108, demon 69, aberration 44, dragon 30, fey 25, construct 23, elemental 19, plant 12, celestial 6. Four monsters fit none of them (ker, erinyes_greater, girtablilu, lyssa_madness).
- **That family code isn't used in the game.** Only one test calls it. Every family-targeted effect reads the raw tags instead: the Dragonslayer Ring, `bonus_damage_vs_tag`, `effective_against`, silver and cold iron.
- **Studying a corpse** (`_start_corpse_identify`) asks one philosophy question.
  - Right answer: the kind is known forever and its corpses never ask again.
  - Wrong answer: you're Stunned for 10 turns.
- **O and B open the full Bestiary page for any monster you have merely SEEN.** So today a corpse study teaches almost nothing that looking at the monster didn't already show. This matters for tier 1 (decision 1).
- **Only maths is timed.** "Extra seconds" can only mean the combat chain. The +5 s harvest bonus for a studied kind is dead code, because the animal quiz has no clock.

## 1. The families: 23 of them

Families are sorted by **what a creature is**, so each one has a single signature you can learn to resist.

There are no families by culture. A "Norse" family would hold a draugr, a frost giant and Nidhogg, which have nothing in common. The cultures live inside the families instead: jotnar in Giants, ushabti in Constructs, Greek hybrids in Monsters of Legend.

"In a run" counts how many different kinds actually appear on floors 1 to 100 in one run. It comes from floors generated with the real `LevelManager` over 6 seeds.

| Family | Who's in it | Kinds | In a run | Ladder | Tier 3 edge |
|---|---|---|---|---|---|
| The Restless Dead | skeletons, zombies, ghouls, mummies, wights, draugr, death knights | 57 | 33 | Large | Ward: paralysis, disease, life drain |
| Ghosts and Shades | wraiths, specters, shadows, banshees, wisps, Keres | 41 | 21 | Large | Ward: life drain, fear |
| Vampires and Liches | vampires, nosferatu, strigoi, jiangshi, liches | 21 | 16 | Large | Ward: life drain, paralysis |
| Demons and Devils | imps, devils, balors, seal demons, Asmodeus, Abaddon | ~68 | 51 | Large | Ward: burning, confusion |
| Dragons and Wyrms | drakes, wyverns, true dragons, dracoliches, Fafnir, Tiamat | 30 | 25 | Large | Ward: burning, freezing, poison |
| Giants and Trolls | ogres, ettins, cyclopes, trolls, Surtur, Ymir, titans | 29 | 22 | Large | Steady Hand +3 s |
| Goblins and Orcs | goblins, hobgoblins, bugbears, orcs, kobolds, gnolls | 33 | 20 | Large | Ward: fear, bleeding |
| Mortal Foes | bandits, cultists, witches, knights, assassins | 34 | 20 | Large | Steady Hand +3 s |
| The Fair Folk | pixies, redcaps, hags, satyrs, elves, the Erlking | 25 | 10 | Medium | Ward: confusion, sleep, charm |
| Great Beasts | bears, wolves, lions, boars, owlbears, Nemean lion, Fenrir | 22 | 10 | Medium | Steady Hand +3 s |
| Vermin and Swarms | rats, bats, beetles, centipedes, scorpions, wasps | 18 | 7.5 | Small | Ward: poison, disease |
| Spiders | cave, giant and phase spiders, ettercaps, Arachne | 10 | 5.5 | Small | Ward: poison, webs |
| Serpents and Swamp-Kin | snakes, nagas, frogs, lizardfolk, yuan-ti | 23 | 12 | Medium | Ward: poison, paralysis |
| Birds and Winged Hunters | eagles, rocs, harpies, griffins, Stymphalian birds | 12 | 6 | Small | Ward: blinding, confusion |
| Gorgons and Basilisks | Medusa and her sisters, basilisks, cockatrices, catoblepas | ~10 | 5 | Small | Ward: the killing gaze, poison |
| Monsters of Legend | chimera, sphinxes, hydras, manticores, minotaurs, Scylla | 27 | 17 | Large | Steady Hand +3 s |
| Werebeasts and Shapeshifters | werewolves, werebears, wererats, changelings, pucas | 9 | 5 | Small | Steady Hand +3 s |
| Golems and Constructs | golems, animated armour, Talos, ushabti | 23 | 17 | Large | Steady Hand +3 s |
| Elementals and Djinn | the elementals, xorns, djinn | 17 | 15 | Large | Ward: burning, freezing |
| Oozes and Slimes | gelatinous cube, puddings, jellies, slimes | 12 | 7 | Small | Ward: paralysis, weakness |
| Aberrations | beholders, mind flayers, every mimic, cloakers, ropers | ~33 | 21 | Large | Ward: confusion, paralysis |
| Plants and Fungi | molds, myconids, shambling mounds, vines, treants | 13 | 8 | Small | Ward: poison, sleep, hallucination |
| Celestials | pegasi, unicorns, angels, Lyssa | 7 | 6 | Small | Ward: blinding, confusion |

Undead is split three ways (57, 41 and 21) so no family is enormous. Each ward lists the effects that family's attacks actually carry in `monsters.json`.

**How every monster gets one:**
- A new `family` field goes on every monster in `monsters.json`, one primary family each.
- A new `data/monster_families.json` holds each family's name, blurb, tier 2 line, tier 3 edge and thresholds.
- **Tags stay as they are.** They still drive weapons and materials, so silver still bites a dracolich filed under Dragons.

**How the field gets filled:**
- A script proposes a family for each monster. A draft gets about 535 of 574 right on the first pass.
- About **40 borderline cases** go on a review sheet for you before anything is written. Examples: dracolich (Dragons or Liches?), Surtur and Ymir (Giants or Elementals?), basilisk (Gorgons or Serpents?), Anansi and the jorogumo (Spiders, Shapeshifters or Fair Folk?), kobolds, tengu, drow, the mimics.
- A data test fails if any monster has no valid family.

**Special cases:**
- Bosses and named monsters count as one kind each, like anything else.
- The Bones ghost is a Ghost.
- Death, the secret cow and the ethereal unicorn have no family and can't be studied.

## 2. How knowledge is earned

- **One study** is one correct corpse study, or a Scroll of Omnisight. Killing, harvesting and seeing don't count.
- **Progress counts DIFFERENT kinds studied** in the family. A known kind never asks again, so farming one kind gives nothing.
- **A new saved set, `player.studied_monster_ids`, records the kinds you studied yourself.** That keeps the Book of Thoth able to open pages without handing out tiers (decision 4).
- **There are three ladders, chosen by how many of the family's kinds a run actually meets.** The thresholds are fixed numbers in data and never change with the floor.

  | Ladder | Kinds met in a run | Studies for T1 / T2 / T3 / T4 |
  |---|---|---|
  | Large | 15 or more | 2 / 5 / 8 / 12 |
  | Medium | 8 to 14 | 2 / 3 / 5 / 7 |
  | Small | under 8 | 1 / 2 / 3 / 4 |

- **Expected pace** for a hero who studies each new kind he kills. These are estimates; the play-test tunes them, and that's a data-only change.
  - Restless Dead: T1 by floor 1 to 3, T4 around floor 20 to 25.
  - Vermin: T4 by about floor 10.
  - Demons: T4 around floor 40.
  - Gorgons: T4 by about floor 40, in time for Medusa.
  - Dragons: T4 around floor 55 to 60, in time for Fafnir.
- **Knowledge lasts one run only**, following DEEDS_KARMA_DESIGN §11 decision 4. Nothing carries over in Bones.

## 3. The four tiers

**T1: Know Them on Sight**
- Every member of the family you SEE gets its full Bestiary page, and O opens it, even for kinds you've never studied.
- The look line names the family: "You see a ghast (wounded). Restless Dead."
- T1 does NOT pre-identify corpses. If it did, studying would stop and progress would freeze.

**T2: Forewarned**
- When you arrive on a floor, you get one line for each T2 family present. Example: "The smell of the grave hangs on the stair: the restless dead walk this floor."
- It never counts invisible monsters, ambushers that haven't sprung, disguised mimics (the Hellmouth included) or allies. Shep's growl still has a job.
- At most three lines, then one combined line.

**T3: Ward** (17 families)
- This applies only when a member of that family inflicts one of its listed effects.
- Effects with a saving throw get **+4 to the save**: paralysis, sleep, freezing, petrification, fear, confusion, charm, slow, life drain and the gorgon gaze.
- Effects with no save **wear off twice as fast**: poison, disease, bleeding, burning, blinding, weakness and hallucination.
- The ward makes these effects less likely, never impossible. Full immunity stays the job of resist items.

**T3: Steady Hand** (the 6 families whose danger is their bulk, not an effect)
- **+3 seconds on the maths chain against that family.**
- It goes through the same `extra_seconds` lane as Ancile, so the clock shows it.
- It's earned by studying, it applies to one family only, and it's a fixed number. That keeps it inside the "no arbitrary seconds" rule.

**T4: Master**
- **+10% weapon damage** against members you can see, melee and ranged.
- It's applied in `combat.strike_damage` beside the Dragonslayer Ring, so the strike preview shows it.
- It doesn't apply to spells or pets.

**Why this order:**
- Information first: cheap, no balance risk, and it rewards your first studies straight away.
- Defence before offence: a teenager survives more by not being paralysed than by hitting harder.
- Damage is the capstone, because that's what you feel in boss fights.

**What the simulator says.** `difficulty_sim.py` can't model families, so I ran it with the bonus applied to EVERY monster. That makes these numbers an upper limit. The table shows the percentage of 200 runs surviving to the end, and each cell can be off by about 7 points either way.

| Player | Baseline | +10% damage to all | +15% damage to all | Clock +3 s |
|---|---|---|---|---|
| Committed, 95% right | 51.5 | 69.0 | 71.0 | 52.0 |
| Prepared, 95% right | 45.5 | 47.5 | 60.5 | 60.5 |
| Committed, 90% right | 22.0 | 19.0 | 22.5 | 22.5 |
| Prepared, 90% right | 14.0 | 19.5 | 12.0 | 19.0 |

The real system only covers families you've reached, mostly from mid-run. My estimate is **+3 to +6 points** of survival for a diligent studier, which fits the targets from your balance pass. That's why T4 is 10% and not 15%. It's one number in data if play says it feels flat. Nothing scales by floor, so `test_lore_not_floor.py` stays green.

## 4. What you see

- **Family pages.** The Bestiary gets a Tab toggle between Kinds and Families. Each family page shows:
  - the family name and current tier;
  - a two-sentence blurb;
  - "Studied 6 kinds, Seen 11";
  - a progress bar ("6 of 8 to Ward");
  - all four tiers, done or locked (locked tiers are visible, as a goal);
  - the members you've seen.

  Unseen members and the family's total size are never shown.
- **Each monster's page** gets a line: "Family: The Restless Dead (studied)" or "(known by its family, not yet studied)".
- **Reaching a tier.**
  - T1 and T2 get a gold message: "You know the restless dead now. You will recognise every one on sight."
  - T3 and T4 get a popup in the quirk popup's style: "MASTER OF THE RESTLESS DEAD".
- **Journal.** One entry per tier, for example: "Twelve kinds of the restless dead, taken apart and understood. I know where they break."
- **The @ sheet.** A "Monster Lore" block lists the active edges, for example "Spiders: Ward, Master". Your Story gets "Families known: 7, mastered: 2".
- **What O does:**

  | What you know | What O does |
  |---|---|
  | Kind unstudied, family below T1 | Plain look line plus "You don't know this creature yet. Study its corpse." |
  | Kind studied, or family at T1 or higher | Opens the full page; the look line names the family |
  | Invisible, unsprung ambusher, disguised mimic | Unchanged: never revealed |

## 5. Wiring checklist

| System | What changes |
|---|---|
| Data | `family` on all 574 monsters; new `monster_families.json`; the content generators that add monsters write the field too |
| Monster and corpse objects | `Monster.family`; old saved monsters and corpses look the family up by kind; corpses copy it |
| Study paths | Corpse study and Omnisight record the kind; Thoth opens pages only |
| Saves | New fields `studied_monster_ids`, `family_tiers_told`, `family_lore_grants`. Old saves catch up quietly, with no popup flood. **They must NOT reuse the names `family_masteries` or `family_mastery_blessings`:** `Player.__setstate__` deletes those on load |
| Bones | Nothing carries over; the ghost is a Ghost |
| Secret builds | A head start for some (decision 5) |
| Bestiary, O, corpse page | Page access, family line, "not yet studied" line |
| Arriving on a floor | T2 lines leave out concealed monsters and allies |
| Combat | `strike_damage` (T4), `player_attack` (Steady Hand), effect, drain and gaze saves (Ward) |
| Text | Help screen, 2 or 3 riddle hints, `docs/systems/`, CLAUDE.md structure lines; sweep for the old family terms |
| UI captures | Family page, monster page, tier popup, @ block, corpse page |
| QA and simulator | QA key to set a tier; simulator re-run |
| Packaging | The new data file is in the bundle (existing guard test) |

The logic lives in a new pure module, `src/family_lore.py`. `monster_classes.py` becomes a thin reader of the field. The quirk system is the wrong home: quirks are hidden discoveries, while families are visible progress. Only the popup look is borrowed.

## 6. How this differs from the masteries you removed in August

**What was removed:** a five-question chain on a single corpse, which granted a flat blessing per family ("+2 damage vs dragons", "+1 WIS"). It came with three mastery stores and 277 mastery entries. It went because the chain was a chore.

**What this does instead:**
- The study stays **one question, right or wrong**, so the flow is untouched.
- Progress comes from how many DIFFERENT kinds you've studied, so it rides on studies you already make.
- There's no new store: the counts are worked out from the studied set.
- Every edge fits its family's lore and works only against that family.

**Other risks:**
- **Grinding gives nothing.** Repeat kills don't count, and the 10-turn stun keeps study spam honest.
- **Monsters that fit several families** get one primary family, and nothing counts twice.
- **Hidden things stay hidden.** Invisible, disguised and ambushing monsters are never revealed by family knowledge: not by O, not by T2, not in Ward messages and not in Master's targeting.
- **Limiting the Bestiary page is a noticeable change.** New players lose free stat pages until they study (decision 1). T1 arriving at 1 or 2 studies makes up for it.

## 7. Build plan

1. **Data (small):** taxonomy script, review sheet, your sign-off, write the field and the families file, data tests.
2. **Core (medium):** `family_lore.py`, save fields and old-save handling, the study hook, messages and Journal, tests.
3. **T1, T2 and UI (medium to large):** Bestiary access, O, corpse page, family page, @ block, capture scenes.
4. **T3 and T4 (medium):** combat hooks, strike preview, simulator re-run.
5. **Wiring (small to medium):** secret builds, Bones, help, hints, docs, the sweep, then an independent wiring audit.

**Then ONE play-test.** Every tier can be reached on floors 1 to 10 through the small families:
- Study two skeletons or zombies and see the T1 message.
- O an unstudied ghoul: its page should open.
- Go downstairs: you should get the "smell of the grave" line.
- Study four kinds of vermin: you should get the T4 popup.
- After the Spiders ward, spider venom should wear off faster.

Deep content (dragons, demons, gorgons) gets logic tests and the QA key.

## 8. Decisions (all taken 2026-10-18: the recommended option every time)

1. **Should the full Bestiary page open only for kinds you've identified?** That means a studied kind, or a family at T1 or higher; a kind you've only seen gets a short page. **I recommend yes.** It's what you said ("O on an identified monster"), it gives studying a purpose, and without it T1 does nothing new.
2. **(Ruled 2026-10-18: no review sheet. Settle each borderline monster by its LORE, choosing the most relevant family.)** **Do you approve the 23 families**, with undead split three ways and no families by culture? **I recommend yes.** The roughly 40 borderline monsters come to you on a review sheet before anything is written.
3. **Should edges work against named monsters and gate bosses** (Abaddon, Fafnir, Medusa, Asterion, Fenrir)? **I recommend yes.** "Study the demons before the Pit" is a strategy worth rewarding, and it's at most +10%.
4. **What should the Book of Thoth's reveal do?** It reveals every kind you've ever seen. If that counted toward tiers, one read around floor 50 would push almost every family to T4. **I recommend it opens pages but gives no tiers.**
5. **Which secret builds should start with family knowledge?** I recommend a T1 or T2 head start only, never edges, and no label telling you so:
   - Geralt: T2 in Restless Dead, Ghosts, Vampires and Werebeasts (his medallion hums)
   - Aristotle: T1 in Great Beasts, Birds, Serpents and Vermin (he wrote the *History of Animals*)
   - Ash Ketchum: T1 in Great Beasts and Birds
   - Merlin: T1 in Fair Folk and Dragons
   - Theseus and Odysseus: T1 in Monsters of Legend
   - Ash Williams: T1 in Demons
   - Hildegard: T1 in Plants
   - Leonardo, Lovelace and Tesla: T1 in Constructs
   - Sherlock: T1 in Mortal Foes
   - Socrates: nothing (he knows that he knows nothing)
