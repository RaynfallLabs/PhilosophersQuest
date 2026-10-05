# Quest Pass (2026-10-04)

Scope: every quest, chain, scripted encounter and secret in the game, traced
end to end in the code by six auditors, then fixed, rebalanced, rewritten and
extended.

Five local commits on `main` (not pushed): `d382976`, `ab61458`, `b74bdff`,
`8fc52d6`, `c1cce9d`. Test suite: 1,920 passed, 29 skipped.

**Nothing here has been play-tested.** Most of it is deep-dungeon content that
cannot be reached in a sitting, so it is covered by tests that generate the
real quest floors and run the real code. The short list of things you can
check in ten minutes is at the bottom.

---

## 1. The headline: most quest chains did not work

The existing quest tests only checked that a function name appeared in the
source. Every item below passed them.

| Quest | What was wrong | Now |
|---|---|---|
| Ariadne's Thread, Aegis of Athena, Sigurd's Shovel | The three "sealed" shrines stood open on about 98% of floors. The Bronze Bull, the Eye of the Graeae and the offering at Odin's altar were never needed. | Sealed; one door, opened by the quest. |
| Reforged Gram | Unobtainable. The secret is "throw the broken blade over Odin's altar" and a sword could not be thrown. | Throwable. Never cursed (altars eat cursed items). |
| Sigurd's pit | Did nothing. The pit status lasted one turn and expired before any monster acted. | Lasts until you climb out. From the pit Fafnir's scales do not apply. |
| Aegis reflection | Set a one-turn paralysis that was removed before Medusa lost an action; she then attacked anyway. | Costs her the turn and two more. |
| Medusa's trophy, Greater Aegis | "Immune to petrification" protected against nothing; every gaze paralyses. | Stops the gaze. |
| Gleipnir | Two of the six ingredients sat in rings of lava and water the player can never enter. Unobtainable in about 19 runs of 20. | One stepping stone in each ring; levitation crosses water and lava. |
| Fenrir | His rage built from the moment you arrived on floor 80, uncapped: about nine stacks before the fight, forty if you explored first. | Starts when he notices you; caps at 8. |
| Philosopher's Stone | Lay on the arena floor. Could be taken without facing Abaddon. | Drops where he falls. |
| Leather scraps | Live text was "Useless scrap", which tells the player to throw away the key to the best secret in the game. | Uses the lore written for it. All quest artifacts now show their lore. |
| Sword of Michael | Needed karma of exactly 10, and a run offers exactly ten chances at +1. | Karma 8 or more. |
| Death chase | The chronicle says "I need to pray"; prayer did nothing. Death arrived adjacent to you on every floor. | Prayer holds him for a few turns; he arrives a few tiles off. |
| NPC encounters | Esc on the outcome screen left the NPC in place after the reward and karma were applied. Every encounter was repeatable: free karma to +10, INT +2 a loop. | Closed properly. |
| Cursed Lodestone | Could be dropped the turn after accepting it, keeping the karma. | Stays until laid on an altar, where it breaks. |
| Cow Level | Set "deepest floor" to 999: +999,000 score and both cooking caps at floor-100 values from floor 35. | Not counted as depth. |
| Bones | Walking out alive wrote a floor-1 bones file holding your whole kit. The ghost was 1d4+1 at every depth. | Only the dead leave bones; the ghost matches its floor. |
| Zoo, graveyard, barracks | Never got their sleeping monsters. The zoo was free gold. | Populated. |
| Mystery altars | No way in except the look cursor, which nothing mentions. Read "You see a The Sphinx lying here." | Stepping onto one offers it. |
| Merchant | Haggling reset each time the shop reopened (anything down to 1 gold). A full pack took the gold and the item. | Fixed. |
| Mini-bosses | Never announced. The early ones could be deleted with one death ray. Tried one room and vanished for the run if they did not fit. | Omen on arrival, immune like bosses, try every room. |
| Loot | NPC gear rewards, grave loot and monster treasure drew from the raw item files: named uniques and scripted quest rewards (the Aegis, the Ring of Command, the Duck of Doom) came out of graves. Monster treasure was capped at floor-25 gear. | Floor-appropriate. |

## 2. A second large balance finding: legendary weapons were weak

Past floor 20 a named unique weapon did a half to a **fifth** of the damage of
an ordinary weapon from the same floor (Excalibur base 16 against a floor-80
common median of 72; the Sword of Michael 18 on floor 100). Reforged Gram, the
Sword of Michael and every mini-boss and NPC weapon reward were worthless.

`tools/balance/rebase_unique_weapons.py` raises each unique to at least 1.25x
the median of common weapons of its own class on its floor (1.5x for Gram and
the Sword of Michael). 82 of 96 rose; none fell. I missed this in the item
pass because the weapons reviewer was told the damage numbers were settled.
**Unique armor likely has the same problem** (one auditor measured AC 3
against 6 at floor 85); I have not touched it.

## 3. Other balance changes

All in `tools/balance/respawn_by_hp.py`, each with its reason.

- **Asterion 184 to 450 HP, Medusa 647 to 1,100.** These are the figures the
  design doc was written around. They were dying in 2.6 and 4.4 attacks
  against a design of 12 to 35 turns, so the Thread and the Aegis had nothing
  to shorten.
- **Named foes hit like it.** Mini-bosses and seal demons hit like ordinary
  monsters of their floor while carrying two to three times the HP. Their
  hardest attack is now at least 1.4x the floor's damage, and seal demons
  attack twice a turn. Mini-bosses before floor 40 have 3x floor HP.
- **Fafnir from the pit:** scales ignored and x1.5 (it was x4 against x0.2,
  which would have ended him in one or two hits had the pit ever worked).
  With reforged Gram he is about four attacks; from the pit about three.

## 4. Writing

- **NPC encounters** moved out of a 1,750-line Python literal into
  `data/npc_encounters.json`. 137 rewrites: every option label now says what
  the player does ("Tell him you found no such blade", not "Keep it"), no
  dashes, and lines that had been copied between NPCs are distinct.
- **Shrines, forge, altars, mysteries:** Ariadne, Athena and Odin speak in
  character and true to the myth. Mystery altar descriptions and outcomes
  rewritten (Mimir is a severed head in a well; the Fisher King waits for
  you to ask what ails him).
- **Combat text:** "Arachne is slain", not "The Arachne"; "The Sphinx", not
  "The The Sphinx". The three mini-bosses that borrow Fenrir's rage no longer
  announce "Fenrir snarls". The Green Knight picks up his head.
- Dashes removed from all flavor encounters and hints.

## 5. Hints

The rule followed: say what a thing is, never what to do with it.

- **Seven NPCs carry one sentence of rumour** each, in character, mostly as
  the reward for the kind choice: the thread, the mirror, the pit, the
  reforged sword, the seven seals, Gleipnir and the scraps, the four things
  that end Death.
- **Quest places describe themselves** when stepped on: six cups cut into an
  anvil; a cobbler's last far too large for any man; three old women passing
  something small from hand to hand.
- **Omens:** each mini-boss and legend's floor shows one line on arrival
  ("Holly grows from the bare stone here, in full berry."). The three shrine
  floors and each seal demon's floor have one too.
- **hints.json:** 14 wrong hints fixed (it described the wrong bosses on
  floors 60 and 80, said six seals, and referred to saints and theft
  mechanics that no longer exist) and 58 breadcrumbs added.
- Reaching karma 8 writes the chronicle line that tells you where you stand.

## 6. New side quests

Ten, none part of the story line, all built from machinery that already
exists. Odds are per run.

| Quest | Floors | What it is |
|---|---|---|
| The Navigator's Boat (St Brendan) | 5 to 9 | Geography altar. Almost every run. |
| The Translator's Desk (St Jerome) | 73 to 77 | Grammar altar. |
| The Old Couple's Table (Baucis and Philemon) | 2 to 9 | Eat their supper, or put your own food on the table. |
| The Three Purses (St Nicholas) | 11 to 19 | Give in secret for karma, or openly for a gift. |
| Three Small Contests (Utgard) | 28 to 39 | The horn, the cat and the old nurse: three stats, three prices. |
| The Bonnacon | 6 | Comic mini-boss; a singed squire warns of it above. |
| The Calydonian Boar | 27 | Mini-boss; an old spearman tells the hunt. Drops Meleager's Spear. |
| The Lion's Thorn (Androcles) | 8 to 18, then 22 to 34 | Draw the thorn; the lion remembers. |
| Saint Cuthbert's Gospel | 41 to 59 | Accept the book, refuse the relic broker, deliver it. |
| The Watch Post | 31 to 45 | A recipient for the Sealed Dispatch, which had none. |

Two more are designed and ready but not added, because they need a new
"quiz inside an encounter option" path I would not ship unplayed: Samson's
Riddle and the Sword in the Anvil. Designs are in the session scratchpad.

## 7. Decisions for you

1. **Should gate bosses block the stairs?** Only floor 99 is gated. Asterion,
   Medusa, Fafnir and Fenrir can all be walked past, which makes their quest
   layers optional twice over.
2. **The reward scrolls** print a code "to show Dad" and do nothing in-game.
   That is yours to keep; if the game goes public, 27 scrolls tell a stranger
   to show a code to Dad. Easy to give each one small in-game effect as well.
3. **Medusa's pillars do nothing.** Her gaze only fires when she is adjacent,
   so there is no line of sight to block. A ranged gaze would make pillars,
   Aegis and blindfold three different answers.
4. **Fafnir never closes.** His AI stands off and breathes, so the pit only
   helps if dug next to him or used with a bow (which is then completely
   safe).
5. **Boss floors are empty of loot.** Fafnir's "gold-littered hoard" and the
   Labyrinth's alcoves hold nothing. Two thirds of the Labyrinth cannot be
   reached by the player at all.
6. **About 32 dead mystery altars a run.** A mystery already faced can still
   spawn on later floors, silent. Consider excluding them or lowering the 60%
   spawn chance.
7. **Gold has no sink.** Merchants sell potions for about 10 gold and named
   unique weapons for 200 to 500, against 200+ gold per kill deep down.
8. **Fountains and thrones are a stat farm:** a perfect chain gives +1 or +2
   permanent stats with no limit but a 33% chance to break.
9. **Ring of Command** (Solomon's Tribunal reward) does nothing.
10. **Tiamat and Asmodeus never summon;** their authored minions never
    appear.
11. **Area spells hit allies.** A fireball can kill the 1 HP cow or a quest
    NPC. Not traced to the end.
12. **Eleven flavor encounters** still have a label that disagrees with what
    the option does ("Give her a scroll" charges 250 gold).
13. **Sealed Dispatch** now has an underground recipient; its lore still says
    "the surface". Pick one.
14. **Cooking named people:** the game offers "Smoked Arachne Liver" and
    "Whispering Crone's Tongue". The Green Knight's "Honor-Bound Sash" is the
    better pattern.
15. **Old saves** keep the old NPC text and the old mini-boss plan. Fine for
    a new run.

## 8. What to play-test

From source (`python src/main.py`), a fresh character:

1. **Floors 5 to 9: the Navigator's Boat.** It is in nearly every run. Walk
   onto the altar; it should offer itself and ask geography questions.
2. **Any karma NPC (floors 3 to 9).** Make a choice, press Esc on the outcome
   screen. The NPC should be gone and should not be repeatable. Read the
   option labels: do they say what you do?
3. **Floor 6 or 9, if an omen line appears on arrival,** find what it warned
   of. On the kill it should read "Arachne is slain", and the chronicle
   should record it.
4. **A merchant.** Haggle, close, reopen: the discount should hold and not
   be repeatable.
5. **Floor 5: the leather scrap.** Read its lore. Does it make you keep it
   without telling you why?
6. **Recall Lore (N)** a few times and read the hints. Tone right?

Everything past floor 12 (the shrines, Gram, the pit, Gleipnir, Fenrir, the
seals, the Stone, Death) is covered by `tests/test_quest_wiring.py` and
`tests/test_side_quests.py` only.
