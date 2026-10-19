# Monster Families v2: The Hunter's Ladders

*2026-10-18. This replaces the generic tiers 3 and 4 in `MONSTER_FAMILIES_DESIGN.md`. Everything else in that doc stands: the 23 families, studying distinct kinds, full pages only for identified kinds, Thoth giving no tiers, and the secret-build head starts.*

> **As built (read [monster_families.md](monster_families.md) for the live system).** This is the design as proposed; the build changed it the same day, and the simulator then tuned every number. Where this page and the code disagree, the code and `data/monster_families.json` are right:
> - **22 families, not 23.** Spiders merged into Vermin ("Vermin, Spiders and Swarms"): Web-Walker and Plague-Wise became one tier 3, Web and Plague; Tremor-Sense is the Vermin tier 4; the Piper's Tune covers spiders too; Arachne's Bane was dropped. The Wild Road circle lists five families.
> - **Thresholds are per family** (at least 2 for tier 1, never 1), set from real floor generation, and **a keystone counts 2 kinds**, not 3.
> - **Every number below is a first draft.** As tuned: wards +1 (not +4), a no-save effect a tenth shorter (not half), damage edges 3 to 10%, weakness 6 to 10%, executes at chain 18, extra seconds 1, the circles' boons halved (Vigil 5%, Unbent Mind +1, Hero's Nerve 1 second). See the Balance section of monster_families.md.

## The idea in one paragraph

Every family has its own ladder, written from its folklore. Vampires fall to the stake, trolls stop healing under fire, golems die when you erase the letter on their brow, and the Fair Folk lose their glamour when you know their name. You learn each technique by studying that family's corpses. The strongest ones only fire when your maths chain is long enough: **knowledge unlocks the technique, and performance lands it.** That is the game's core idea (knowledge is power, and outcome comes from how well you answer) applied to monster hunting.

## 1. What makes this better than a flat ladder

1. **Each family plays differently.** The fight with a vampire changes once you know the stake. Undead start running from you, and you stop a hydra's heads regrowing. A flat +10% changes nothing you can see.
2. **Quiz-native power.** The capstones are chain-gated: "at chain 10 or more, a vampire below 30% health dies outright". A kid who studies AND answers well gets the payoff. The chain already works as the crit (crits were retired), so this rides on the existing rung system that Harpe and the plague rungs use.
3. **Real folklore, taught.** Each tier unlocks a one-sentence Field Note on the family page, a real piece of folklore ("Salt across a threshold keeps the dead outside, or so the grandmothers of Bohemia said."). The game teaches while it rewards.
4. **Legible in the moment.** Every technique has a name and a line when it fires, such as "Stake Through the Heart! The vampire crumbles to ash." Complexity you can see is fun; hidden maths is not.
5. **Mid-run and long-run goals.** The Circles (section 5) give a reason to round out related families, with the Loremaster title for the dedicated.

## 2. The rhythm: five tiers with the same names everywhere

Kids learn the rhythm once; the content changes per family.

| Tier | Name | What it is |
|---|---|---|
| 1 | **Recognise** | Every member gets its full Bestiary page, and O opens it. The look line names the family. *(Same for all families.)* |
| 2 | **Forewarned** | A themed line when you arrive on a floor where they are. It never counts concealed members or allies. *(Same mechanic, a different line per family.)* |
| 3 | **Lore** | The family's folk defence: how ordinary people survived them. |
| 4 | **Hunter** | How a hunter takes them: offence or tactics. |
| 5 | **Bane** | The signature capstone, often one that breaks a rule (stops regeneration, ends a split, banishes, sees the hidden, breaks morale). |

Every tier also unlocks one **Field Note** on the family page, so the page fills up as a real monster hunter's journal.

**Thresholds** (counts of distinct kinds studied, fixed in data):

| Ladder | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|
| Large | 1 | 3 | 6 | 9 | 13 |
| Medium | 1 | 2 | 4 | 6 | 8 |
| Small | 1 | 2 | 3 | 4 | 5 |

- **T1 at one study everywhere.** Your first skeleton opens every Restless Dead page: an immediate, visible reward for the first study.
- **Keystones.** Each family's legends (its bosses, mini-bosses and proper-named members: Medusa, Arachne, Fafnir, Asterion, Fenrir, the Erlking, and so on) count as **3 kinds** when studied. "Study the legend to understand the family." This also smooths the small families, where a run might only meet 4 of 5 kinds.

## 3. The safety rails

- **Named foes are too wilful** (the engine's existing rule in `Monster.resists_control`). Executes, banishments, turning, calming and surrender never work on bosses, mini-bosses or seal demons. Against them, an execute technique instead lands a **+25% blow**. Wards, damage, stopping regeneration and seeing the hidden DO work on them (your ruling 3).
- **Hidden things stay hidden** except where a family's own technique is exactly that (Spiders' Tremor-Sense, Aberrations' Mimic-Sense, Ghosts' Second Sight, Fair Folk's True Name). Even then it works only on that family, at short range, and only after earning it. Shep's floor-wide growl keeps its job.
- **Lore not floor.** Every number is fixed data. Nothing scales by depth.
- **Calmed creatures** use the engine's existing charm status: a calm creature won't raise a hand, and striking it breaks the calm (the Gilgamesh bribe rule).

## 4. The 23 ladders

Notation: "+4 saves vs X" applies when a member of this family inflicts X. "Chain N+" means the blow lands at chain N or more. "Lesser" means not a named foe.

### The Restless Dead (Large)
- **T2:** "The smell of the grave hangs on the stair: the restless dead walk this floor."
- **T3 Grave-Salt:** +4 saves vs their paralysis, disease and draining. Disease wears off twice as fast.
- **T4 Bonebreaker:** your blows hit 25% harder when they strike what the dead fear (their listed weaknesses: holy, fire, blunt).
- **T5 Turn the Dead:** a chain-8+ blow against one sends every lesser undead in sight fleeing for 6 turns.

### Ghosts and Shades (Large)
- **T2:** "The candle-flames lean the wrong way: ghosts drift on this floor."
- **T3 Iron and Salt:** +4 saves vs their fear and draining, and their draining no longer heals them.
- **T4 Second Sight:** invisible ghosts within 3 tiles show to you as a faint shimmer you can strike.
- **T5 Lay the Ghost:** at chain 5+, your blows ignore their resistances, as if your weapon were blessed.

### Vampires and Liches (Large)
- **T2:** "The stair smells of iron and old roses: a vampire or a lich keeps court here."
- **T3 Garlic and Ash:** +4 saves vs their drain and paralysis, and their bite no longer heals them.
- **T4 Hunter's Patience:** +3 seconds on the maths chain against them.
- **T5 Stake Through the Heart:** at chain 10+, a lesser vampire or lich below 30% health dies outright: no mist, no rising.

### Demons and Devils (Large)
- **T2:** "Brimstone on the stair: something from the Pit has climbed this far."
- **T3 Circle of Salt:** +4 saves vs their burning and confusion. Burning wears off twice as fast.
- **T4 True Names:** +15% weapon damage against them.
- **T5 Banishment:** at chain 10+, a lesser demon below 35% health is cast back into the Pit.

### Dragons and Wyrms (Large)
- **T2:** "Gold-smell and scorch-marks on the stair: a wyrm lairs on this floor."
- **T3 Dragon-Ward:** 20% less fire, cold and poison damage from their attacks, and +4 saves vs burning, freezing and poison.
- **T4 The Soft Belly:** +15% weapon damage against them (Sigurd struck Fafnir from below).
- **T5 The Missing Scale:** at chain 10+, your blow ignores a dragon's scales and resistances, Fafnir's included.

### Giants and Trolls (Large)
- **T2:** "The stair shakes underfoot: giants walk this floor."
- **T3 Steady Hand:** +3 seconds on the maths chain against them.
- **T4 Fire and Dawn:** your blows stop a troll's or a giant's regeneration for 5 turns.
- **T5 The Bigger They Are:** at chain 5+, +20% damage against them, and +30% against giants that fill more than one tile.

### Goblins and Orcs (Large)
- **T2:** "Crude marks scratched on the stair: a goblin warband holds this floor."
- **T3 Break Their Nerve:** when you kill one, every lesser goblin or orc that saw it may lose its nerve and flee for 4 turns.
- **T4 Trap-Wise:** +4 saves vs their fear and bleeding, and their ambushers never catch you unawares.
- **T5 Your Name Is Known:** lesser goblins and orcs flee from you on sight. By the time you earn this they are no threat, so it removes the tedium.

### Mortal Foes (Large)
- **T2:** "Bootprints and a cold campfire on the stair: armed men and women walk this floor."
- **T3 Read Their Hands:** the thieves among them can never steal from you.
- **T4 Steady Hand:** +3 seconds on the maths chain against them.
- **T5 Yield!:** at chain 8+, a lesser foe below half health surrenders, throws down his purse and runs.

### The Fair Folk (Medium)
- **T2:** "A ring of mushrooms on the stair: the Fair Folk are abroad on this floor."
- **T3 Coat Turned Inside Out:** +4 saves vs their confusion, sleep and charm.
- **T4 Cold Iron:** +15% weapon damage against them, doubled with an iron or cold-iron weapon.
- **T5 Their True Name:** invisible or disguised fey within 4 tiles show to you, and their charm can never take you.

### Great Beasts (Medium)
- **T2:** "Fresh tracks and torn bark on the stair: great beasts hunt this floor."
- **T3 Hunter's Harvest:** harvesting their corpses gives one extra portion.
- **T4 Steady Hand:** +3 seconds on the maths chain against them.
- **T5 Beast-Friend:** half of all lesser beasts arrive calm and leave you be unless you strike first.

### Vermin and Swarms (Small)
- **T2:** "Droppings and gnawed bones on the stair: vermin swarm this floor."
- **T3 Plague-Wise:** +4 saves vs their poison and disease, and both wear off twice as fast.
- **T4 Ratcatcher:** +20% weapon damage against them.
- **T5 The Piper's Tune:** a chain-5+ blow sends every lesser vermin in sight fleeing for 5 turns.

### Spiders (Small)
- **T2:** "Webs thick across the stair: spiders lurk on this floor."
- **T3 Web-Walker:** +6 saves vs being slowed or held by spiders, and their poison wears off twice as fast.
- **T4 Tremor-Sense:** spiders waiting in ambush within 4 tiles are revealed.
- **T5 Arachne's Bane:** +20% damage against spiders, and their venom can no longer poison you.

### Serpents and Swamp-Kin (Medium)
- **T2:** "A shed skin on the stair: serpents coil on this floor."
- **T3 Antivenom:** +4 saves vs their poison and paralysis, and poison wears off twice as fast.
- **T4 Mongoose:** your first blow in a fight against a serpent starts at chain 2.
- **T5 Snake-Charmer:** at chain 8+, a lesser serpent you strike is charmed calm for 8 turns.

### Birds and Winged Hunters (Small)
- **T2:** "Feathers drift down the stair: winged hunters nest on this floor."
- **T3 Hooded:** +4 saves vs their blinding and confusion (the falconer's hood).
- **T4 Falconer's Eye:** +20% damage with bows and thrown weapons against them.
- **T5 Heracles' Rattle:** at chain 8+, the din sends every lesser bird in sight scattering for 6 turns.

### Gorgons and Basilisks (Small)
- **T2:** "Stone figures stand on the stair, their faces frozen in fear: a gorgon's gaze haunts this floor."
- **T3 Averted Eyes:** +4 saves vs the killing gaze and their poison.
- **T4 Perseus' Shield:** while you carry a shield, their gaze cannot take you at all.
- **T5 Harpe:** +20% damage against them, and at chain 10+ a lesser one meets its own stare and turns to stone.

### Monsters of Legend (Large)
- **T2:** "The stair is carved with an old story: a monster of legend waits on this floor."
- **T3 Steady Hand:** +3 seconds on the maths chain against them.
- **T4 Iolaus' Torch:** your blows stop their regeneration for 5 turns, so the hydra's heads stay down.
- **T5 Know the Story:** once per fight, your first wrong answer against one does not end your chain. You know how the story ends.

### Werebeasts and Shapeshifters (Small)
- **T2:** "Claw-marks and a torn cloak on the stair: a shapeshifter hunts this floor."
- **T3 Wolfsbane:** +4 saves vs their bleeding and disease, and bleeding wears off twice as fast.
- **T4 Silvered:** +10% damage against them, and +30% with a silver weapon.
- **T5 Forced Shape:** at chain 8+, a lesser shapeshifter is stunned for 3 turns as its shape tears.

### Golems and Constructs (Large)
- **T2:** "Grinding stone and ticking brass on the stair: something made, not born, guards this floor."
- **T3 Steady Hand:** +3 seconds on the maths chain against them.
- **T4 Find the Seam:** at chain 5+, your blows ignore their resistances (Medea pulled the nail from Talos's ankle).
- **T5 Erase the Letter:** at chain 10+, a lesser construct below 35% health falls lifeless (*emet*, truth, becomes *met*, dead).

### Elementals and Djinn (Large)
- **T2:** "The air on the stair tastes of lightning and ash: elementals stir on this floor."
- **T3 Ward of the Elements:** 20% less fire, cold, lightning and acid damage from them.
- **T4 Opposing Element:** your blows hit 25% harder when they strike what the elemental is weak to.
- **T5 Solomon's Seal:** their burning and freezing can never take you, and their elemental damage is halved.

### Oozes and Slimes (Small)
- **T2:** "The stair is slick and smells of acid: oozes creep on this floor."
- **T3 Clean Blade:** +4 saves vs their paralysis and weakness, and weakness wears off twice as fast.
- **T4 Strike True:** your blows never split them, and +15% weapon damage against them.
- **T5 Fire and Frost:** your blows hit 40% harder when they strike what an ooze is weak to.

### Aberrations (Large)
- **T2:** "The stair feels wrong, as if it bends: aberrations lurk on this floor."
- **T3 Steel Mind:** +4 saves vs their confusion and paralysis, and hallucination wears off twice as fast.
- **T4 Mimic-Sense:** a disguised mimic within 2 tiles gives itself away to you.
- **T5 The Unblinking:** +20% damage against them, and their ambushers never catch you unawares.

### Plants and Fungi (Small)
- **T2:** "Spores drift on the stair like dust: something green and hungry grows on this floor."
- **T3 Herbalist's Mask:** +4 saves vs their poison, sleep and hallucination, and poison wears off twice as fast.
- **T4 Herbalist:** harvesting them gives one extra portion.
- **T5 Woodsman's Axe:** +20% damage against them, and their ambushers never catch you unawares.

### Celestials (Small)
- **T2:** "A clean light falls on the stair: a celestial creature walks this floor."
- **T3 Shaded Eyes:** +4 saves vs their blinding and confusion.
- **T4 Angel's Due:** their holy damage hurts you 25% less.
- **T5 Entertaining Angels:** lesser celestials arrive calm and leave you be unless you strike first.

## 5. Circles: rounding out related families

Reaching **T3 in every family of a Circle** (or in any three of a larger Circle) grants one small cross-family boon, a gold popup and a Journal line.

| Circle | Families | Boon |
|---|---|---|
| **The Grave Watch** | Restless Dead, Ghosts, Vampires and Liches (all three) | **Vigil:** necrotic and drain damage hurt you 20% less, from any source |
| **The Wild Road** | any 3 of Great Beasts, Birds, Serpents, Vermin, Spiders, Plants | **Ranger's Instinct:** +1 sight radius |
| **The Hellward Gate** | Demons, Fair Folk, Aberrations (all three) | **Unbent Mind:** +2 to every save vs confusion, charm and fear, from anything |
| **The Hero's Road** | any 3 of Monsters of Legend, Gorgons, Giants, Dragons | **Hero's Nerve:** +2 seconds on the maths chain against any boss |

**Loremaster:** T5 in any five families. A title on Your Story, the high-score table and the Journal; no mechanics, just honour.

## 6. How it is built: one engine, data for the rest

- **`src/family_edges.py`** is a registry of about 20 effect PRIMITIVES. Every technique above is one primitive plus parameters in `data/monster_families.json`, with its name, plain text, trigger line and Field Note. Adding or tuning a technique is a data edit.
- Primitives: `save_bonus`, `duration_mult`, `resist_damage`, `damage_mult` (optional chain minimum, weapon condition: bow, thrown, iron, silver, shield), `weakness_amp`, `extra_seconds`, `chain_forgive`, `opening_chain`, `pierce_resist`, `block_regen`, `prevent_split`, `execute` (petrify, banish and ash variants, with the named-foe +25% fallback), `turn` (on-hit or on-kill, radius), `calm_on_arrival`, `charm_on_hit`, `surrender`, `theft_immune`, `no_ambush`, `sense_hidden` (invisible, ambush or disguise, with a radius), `gaze_immune` (shield condition), `harvest_bonus`, `drain_heal_block`, `stun_on_hit`.
- Every one hooks into a mechanic the engine already has: charm and fear on monsters, `resists_control` for named foes, the regeneration-burning check, `splitting.blow_splits`, `theft.py`, ambusher `spring()`, `unseen.concealed`, Ancile's `extra_seconds` lane, `_skip_warmup`, and the max-chain resistance pierce. **No new monster behaviour is invented.**
- Each fired technique prints its trigger line once per fight (not every blow), so the log stays readable.

## 7. Balance

- This is stronger than v1. Damage edges run 15 to 30% (conditional), and there are executes, turning and calming. The rails keep bosses fair: executes become +25% blows, and nothing routs or calms a named foe.
- **The simulator decides.** After the build, `difficulty_sim.py` runs with a player who studies every new kind. If the committed player climbs past your 40 to 50% target, the data numbers come down (damage first, then execute thresholds) until it lands. Every number is in one JSON file.
- Most techniques make fights *different* rather than just shorter: a fleeing pack, a calm beast, a hydra that stays down. That is the kind of power that feels good without flattening the curve.

## 8. What I need from you

Nothing, unless you want something changed. I'm building this as written and tuning by simulator. Tell me if any technique, name or Circle should go, or if you want more tiers on the big families.
