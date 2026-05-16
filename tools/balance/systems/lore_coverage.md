# Discovery, Lore, and Hints — Coverage Map

Scope: every player-facing hint, lore string, NPC dialog branch, mystery prompt, encounter prose, story popup, and chronicle line, indexed against the systems it references. The discoverability gap analysis (§9) is the central deliverable: for every system the developer has built, what trail (if any) does the dungeon offer the player?

Sources consulted (read-only):
- `tools/audit/CONTEXT.md`
- `tools/balance/REVERSE_ENGINEERED.md`
- `data/hints.json` (every entry, all 5 tiers)
- `src/game_magic.py:75-146` (Recall Lore mechanic)
- `src/quirk_system.py` (Norns + Nostradamus + Second Sight + Sibyl + Oracle reveal pool)
- `src/npc_encounters.py` (all 31 NPC encounters)
- `src/mystery_system.py` (all 13 mysteries)
- `src/flavor_encounters.py` + `data/flavor_encounters.json` (5 hand-coded + 92 generated flavor scenes)
- `data/monsters.json` (sampled across L1–L100 bands)
- `data/items/artifact.json`, `accessory.json`, `weapon.json`, `armor.json`, `scroll.json`, `spellbook.json` (lore fields)
- `src/main.py` (`_STORY_CONTENT`, `_MILESTONE_FLAVOR`, `_ROOM_CHRONICLE`, `_CHRONICLE_FLAVOR`, `_BOSS_STORY_KEYS`)
- `src/items.py` (Abyssal Shimmer, Tablet, Lake of Fire scroll, Wrench, Complete Tablet)
- `src/game_combat.py:608-630` (`_BOSS_CHRONICLE`)
- `src/game_divine.py`, `src/game_encounters.py`, `src/game_magic.py` (chronicle call sites)

---

## 1. Recall Lore mechanic

**Entry point:** `src/game_magic.py:75-106` — `MagicMixin._start_recall_lore`.

- Cooldown-gated; if `player.recall_lore_cooldown > 0`, blocked with `"Your mind needs rest before recalling more lore. ({N} turns remain)"` (`game_magic.py:78-82`).
- Opens an **escalator-chain trivia quiz**, `max_chain=5`, `tier=1` (`game_magic.py:96-106`). Chain mode = each correct answer scores +1; first wrong ends the chain. Tier escalates *within* the chain.
- Wisdom and timer modifiers feed the quiz (`extra_seconds=player.get_quiz_extra_seconds('trivia')`).
- `on_complete` callback (`game_magic.py:87-95`): calls `_resolve_recall_lore(chain)`, sets state to `STATE_HINT`, then `quirk_system.on_recall_lore()`.

**Cooldown formula** (`src/game_magic.py:108-122`):
```
chain == 0 → cooldown = 40 turns, message "Your thoughts scatter. Nothing surfaces.", NO hint
chain >= 1 → cooldown = 50 + chain*15  (so chain 1 → 65, 2 → 80, 3 → 95, 4 → 110, 5 → 125)
```
**Norns active** (`quirk_system.py:803-805`, `1502`): cooldown halved to `max(5, cooldown // 2)`. Triggered after 20 lifetime Recall Lore uses in a run.

**Chain → tier mapping** (`src/game_magic.py:134`):
```
tier_key = str(min(chain, 5))
```
So chain 1 → T1 hint, ... chain 5 → T5 hint. Chain 0 returns nothing. A random hint is drawn from the tier's pool. The session's recalled hints are de-duped into `self._recalled_hints` (a journal, `game_magic.py:145-146`).

**Hint pool selection logic** (`game_magic.py:124-142`): JSON loaded from `data/hints.json`; pool = `all_hints[tier_key]`; `random.choice(pool)`. No per-floor weighting, no de-duplication across runs, no requirement gating.

**Lore-related quirks** beyond Norns (`src/quirk_system.py`):
- **Nostradamus** (#70, `quirk_system.py:807-813`): 10 Recall Lore uses while confused/blinded/hallucinating/stunned/feared → +3 WIS.
- **Second Sight** (#79 power, `quirk_system.py:815-819`): 5 Recall Lore uses while blinded → power unlock.
- **Sibyl** (#36, `quirk_system.py:1001-1012`): 500 correct answers before level 20 (any subject, including trivia) → +2s all-quiz-timer.
- **Tiresias** (Oracle reveal hint): "The blind prophet answered correctly while he could not see" — points to answering quizzes while blinded.

**Open quirk question:** the cooldown text says "Your mind needs rest" but the Norns reduction is silent — no in-game callout tells the player the cooldown was halved.

---

## 2. hints.json full index

`data/hints.json` is a `{tier: [string]}` dict, tiers `"1"`–`"5"`. Counts: **T1: 16, T2: 24, T3: 47, T4: 60, T5: 56**. Total: 203 hint lines.

Voice register: third-person observational ("Some say…", "Old hunters who…", "The Romans believed…"), present-tense, mythological framing. Falls within the geek-dad spec from `CONTEXT.md §5`.

Each line is tagged below with the system(s) it points the player toward. Convention: **SYS** in bold when the hint clearly references one system; *italic* when it's general mechanic teaching with no specific system.

### 2.1 Tier 1 hints (16 entries) — basic mechanics

| # | Hint (truncated) | System reference |
|---|---|---|
| 1 | "The wise listen before they speak. Your Wisdom shapes how long…" | *WIS stat → quiz timer* (`player.py:12-27`) |
| 2 | "Your body burns through its reserves… hunger… takes something more than comfort." | *Hunger → HP drain* |
| 3 | "Scrolls crumble after a single reading… a spellbook is a patient teacher" | *Scroll vs spellbook consume rules* |
| 4 | "Fire changes everything… a wise traveler learns to cook early" | *Cooking system* (`food_system.py`) |
| 5 | "The ? key is the beginning of wisdom" | *Help screen UX* |
| 6 | "A lockpick is a delicate instrument… fragile ones break first" | *Lockpicking durability* (`container_system.py`) |
| 7 | "Not every chest a dungeon holds is left in plain sight" | *Hidden containers* |
| 8 | "Treasures rest where they fall… G or a comma" | *Pickup keybind UX* |
| 9 | "The deeper you descend, the greater the peril — but also the greater the prize." | *Floor progression / reward curve* |
| 10 | "A carved jade insect was once placed on the tongues of the dead." | **Jade Cicada** (`accessory.json:5202-5217`) — death save artifact |
| 11 | "Not every wound is made the same way. Blades that slash, points that pierce, and weights that crush…" | *Damage type system* (slash/pierce/blunt) |
| 12 | "Strength is the measure of what you can carry…" | *STR stat* |
| 13 | "A hardy constitution is the simplest armor of all" | *CON stat* |
| 14 | "Some doors in the dungeon open only when you already know where you are going." | *Maps / memory / Palladium foreshadow* |
| 15 | "The dungeon does not announce its traps. A careful eye and a slow step…" | *Trap system + PER searching* |
| 16 | "Some say the dungeon itself is a kind of program… Try the [keys] that seem to do nothing." | **Hidden debug terminal** / **XYZZY**. Backtick key. (`main.py:2571` chronicle for XYZZY) |

**T1 gaps:** No T1 hint mentions theology/prayer (despite altars being a T2 thing), no T1 hint about identification (philosophy), no T1 hint about chain mechanics in combat. The "Some say the dungeon itself is a kind of program" line is the only T1 hint pointing at a hidden system.

### 2.2 Tier 2 hints (24 entries) — deeper mechanics + nudged secrets

| # | Hint (truncated) | System reference |
|---|---|---|
| 1 | "Fire and cold are ancient enemies." | *Elemental resists/weaknesses* |
| 2 | "Keen eyes see further… Perception is the gift of the wary." | *PER → sight + ranged* |
| 3 | "Confusion is a thief that steals your time" | *Status effects → timer mod* |
| 4 | "The mind is a vessel. A keen intellect fills it with more arcane power" | *INT → MP + philosophy/science timer* |
| 5 | "Cooking the flesh of your enemies is not savagery — it is wisdom." | *Cooking → level scaling* |
| 6 | "The staircase landing is a place of quiet power… find their bodies knitting themselves back together" | **Stair-rest healing** — load-bearing mechanic (`CONTEXT.md` notes this is the real heal path) |
| 7 | "The undead are past the reach of much that wounds the living. Fire and holy power…" | *Undead resistances* |
| 8 | "A weapon with reach is worth twice its weight in a narrow corridor." | *Polearm reach mechanic* |
| 9 | "A wand holds only so much of the world's power" | *Wand charges* |
| 10 | "Some accessories are worth more than armor." | *Accessory slot value* |
| 11 | "The body's endurance is not only about surviving wounds. Stamina is the measure…" | *SP/stamina* |
| 12 | "Different corners of the dungeon test different kinds of knowledge." | *Subject diversity preparation* |
| 13 | "Items found in the dark are not always what they appear. Some are blessed… others carry a curse… Altars may reveal…" | **Altars + BUC system** |
| 14 | "Strange altars sometimes appear in the dungeon. Those who approach and kneel…" | **Altars + prayer** (`game_divine.py:734`) |
| 15 | "Polearms and staves can strike enemies beyond arm's reach." | *Reach (duplicate)* |
| 16 | "The strength of a monster's body can be drawn into your own if you know how to harvest it." | *Harvest → animal quiz* |
| 17 | "Prayer is not merely a comfort for the frightened. Those who speak to the gods at the right place and the right time…" | **Prayer mechanic** (theology) |
| 18 | "A potion does what you need when you swallow it. A spell does what you need whenever you choose." | *Potion vs spell tradeoff* |
| 19 | "Elemental resistances are the quiet armor beneath your armor." | *Resistance accessories* |
| 20 | "An Egyptian eye of blue faience mends what was torn. Patience is its method" | **Eye of Horus** (`accessory.json:5153-5168`) — passive regen amulet |
| 21 | "The Romans believed a certain shield fell from heaven and kept their city safe." | **Palladium** (`artifact.json:285-298`) — stair_reveal artifact |
| 22 | "Gold follows certain hands as though drawn by magnetism. The dwarves forged a ring…" | **Draupnir** (`accessory.json:5170-5184`) — gold_multiplier ring |
| 23 | "Philosophers speak of a reality beneath reality — a hidden terminal that accepts a spoken word. The key… sits beside the number 1, quiet and overlooked." | **Hidden debug terminal** (backtick key) |
| 24 | "Some places in the dungeon shimmer with energy that doesn't belong to this world." | **Abyssal Shimmer** (`items.py:464-478`) |

### 2.3 Tier 3 hints (47 entries) — recipes, mini-bosses, hidden characters, weapons

Compressed table (line numbers from `data/hints.json`, system tag in caps):

| # | Topic | System reference |
|---|---|---|
| 3.1 | Wolf + cave fungi → STR recipe | **COOKING-RECIPE** (`recipes.json`) |
| 3.2 | Two healing ingredients → restorative | **COOKING-RECIPE** |
| 3.3 | Dragon ingredients → CON recipe | **COOKING-RECIPE** |
| 3.4 | Flying creature + herbs → INT recipe | **COOKING-RECIPE** |
| 3.5 | Bone + cave mushrooms → endurance | **COOKING-RECIPE** |
| 3.6 | Undead ingredients → immunities | **COOKING-RECIPE** |
| 3.7 | "The deeper the dungeon, the stronger the recipe ingredients" | *Cooking scaling principle* |
| 3.8 | "Some recipes demand three or more ingredients…" | *Compound recipe bonus* |
| 3.9 | Aquatic + underground plants → confusion clear | **COOKING-RECIPE** |
| 3.10 | Fire + cold balanced → all-stats recipe | **COOKING-RECIPE** |
| 3.11 | "Fire-bringer in starlit robe, sashed in gold" | **HIDDEN-CHAR — Prometheus** |
| 3.12 | "Bald, simply robed, unfazed by hardship… questions slow down around him" | **HIDDEN-CHAR — Buddha** (WIS-build) |
| 3.13 | "Cunning wanderer in a hood, survived ten years at sea" | **HIDDEN-CHAR — Odysseus** |
| 3.14 | "Philosopher-mathematician in forest green, with a love of numbers and harmonics" | **HIDDEN-CHAR — Pythagoras** |
| 3.15 | "Rare creatures that appear in the dungeon only once" | *Mini-boss spawn* |
| 3.16 | "Diogenes carried nothing but a lantern" | **QUIRK — Diogenes' Lantern** (shard drop) (`main.py:3705`) |
| 3.17 | "A spider of unusual size and cunning lurks in the early depths. Her web holds even armored warriors in place — but webs have a well-known enemy." | **MINI-BOSS — Arachne** (fire weakness) |
| 3.18 | "Something half-woman and half-serpent has been reported… drains warmth" | **MINI-BOSS — Lamia** |
| 3.19 | "A bronze giant… curious imperfection somewhere in its construction" | **MINI-BOSS — Talos** (drain weakness, ankle ichor) |
| 3.20 | "A serpent-woman who mothers all monsters poisons with every bite" | **MINI-BOSS — Echidna** |
| 3.21 | "A forest spirit that lures wanderers… cold iron disturbs such beings" | **MINI-BOSS — Erlking** |
| 3.22 | "A bat-god from the underworld… blinding adventurers with its wings… arms pass through it like smoke" | **MINI-BOSS — Camazotz** (magic-only weakness implied) |
| 3.23 | "A lone sphinx in the depths poses riddles to those bold enough to listen." | **MYSTERY — Sphinx** (philosophy challenge, `mystery_system.py:17-30`) |
| 3.24 | "Ancient Greek smiths spoke of an unfinished hammer buried deep. Where thunder echoes, dwarven work awaits." | **MYSTERY — Mjolnir/Dwarven Forge** (`mystery_system.py:89-102`) |
| 3.25 | "Alchemists sought the power to turn lead to gold. Their crucibles still burn in the shallower depths" | **MYSTERY — Crucible** (`mystery_system.py:103-116`) |
| 3.26 | "A Celtic cauldron of transformation… demands meals as tribute" | **MYSTERY — Cauldron** (3-food requirement, `mystery_system.py:173-186`) |
| 3.27 | "A sickle-sword of black iron carried by Egyptian priests…" | **ARTIFACT — Khopesh of judgment** (in weapon.json — UNVERIFIED, found via reference) |
| 3.28 | "A green-hafted axe was once used in a deadly game of exchange." | **WEAPON — Green Knight's axe** |
| 3.29 | "Celtic warriors wore twisted gold around their necks. One queen's torc burned brightest when she was surrounded" | **Torc of Boudicca** (`accessory.json:5186-5200`, surrounded_ac_bonus) |
| 3.30 | "A Sumerian mace could speak and fly… smasher of a thousand minds." | **WEAPON — Sharur** (in weapon.json) |
| 3.31 | "A wooden idol once fell from heaven to protect a great city. Those who carried it always knew where the exit was." | **Palladium** (`artifact.json:285-298`) (duplicates T2 #21 thematically) |
| 3.32 | "Pandora's box is said to lie somewhere in the depths." | **MYSTERY — Pandora** (`mystery_system.py:31-45`) |
| 3.33 | "The Wandering Jew walked forever without rest." | **QUIRK — Ahasverus** |
| 3.34 | "Cerberus guarded the underworld's gate… earn his grudging respect." | **QUIRK — Cerberus** |
| 3.35 | "The Sphinx was defeated… answering clearly while blind" | **QUIRK — Tiresias** (Oracle reveal hint table, `mystery_system.py:421`) |
| 3.36 | "Musashi's greatest duels were won with restraint. One precise strike…" | **QUIRK — Musashi** |
| 3.37 | "Rasputin survived poison, bullet, and blade" | **QUIRK — Rasputin** (dance with death, hard-to-kill quirk) |
| 3.38 | "Cassandra's prophecies were true even when her methods seemed strange." | **QUIRK — Cassandra** (2+ wrong threshold passes) |
| 3.39 | "Tantalus was punished by eternal hunger." | **QUIRK — Tantalus** (persistence through failure) |
| 3.40 | "Orpheus walked among the dead with only his music" | **QUIRK — Orpheus** (non-combat turns) |
| 3.41 | "The Buddha sat in perfect stillness beneath the bodhi tree." | **QUIRK — Buddha** |
| 3.42 | "Hephaestus returned to his forge obsessively, perfecting the same piece" | **QUIRK — Hephaestus** |
| 3.43 | "Fountains in the dungeon offer more than a drink… those willing to answer for it." | **Fountain system** (`game_divine.py:315`) |
| 3.44 | "In 1976, a game was released that hid a secret word deep underground." | **XYZZY** (Colossal Cave Adventure reference, `main.py:2571`) |
| 3.45 | "An old alchemist's journal mentions a tool that joins rather than separates. 'The Wrench completes what is broken,' he wrote. 'Stone into Tablet, purpose into form.'" | **Philosopher's Wrench → Complete Tablet** (`items.py:525-549`) — secret victory path |
| 3.46 | "Theologians call certain ground 'thresholds' — places where the boundary between life and death grows weak. Scripture marks these places." | **Abyssal Shimmer** ("Revelation 20:14" inscription, `main.py:1156`) |
| 3.47 | (Note: hints.json has 47 lines in T3) | — |

### 2.4 Tier 4 hints (60 entries) — boss strategies, mid-tier secrets, NPC quests

Selected most-load-bearing entries:

| Hint | System reference |
|---|---|
| "The Minotaur haunts the labyrinth at the twentieth depth… an old myth tells of a thread that once tamed the labyrinth itself." | **BOSS-ASTERION + Ariadne's Thread quest** (`artifact.json:26-37`) |
| "The Gorgon waits at the fortieth depth… heroes found ways to fight without looking — or to turn her own terrible power against her." | **BOSS-MEDUSA + mirror/blindness strategy** |
| "The Grey Sisters share a single eye… Perseus once stole it — and traded it for something far more valuable than sight." | **Eye of Graeae quest** (`artifact.json:38-49`) — Perseus altar trade |
| "The dragon Fafnir guards the sixtieth depth… Sigurd struck from below, where the scales are softest." | **BOSS-FAFNIR + dig-pit strategy** (`game_combat.py:1174`) |
| "The great wolf Fenrir prowls near the eightieth depth… grew stronger with every passing moment." | **BOSS-FENRIR + rage mechanic** (monsters.json:fenrir_wolf rage_interval) |
| "The dwarves of Svartalfheim forged Gleipnir from six things that do not exist." | **GLEIPNIR-FORGE-QUEST** (Fenrir bind) — 6 impossible ingredients (`artifact.json:50-127`) |
| "A forge of dwarven make has been discovered in the deep floors before Fenrir's hall." | **Gleipnir-Forge altar** (`game_divine.py:497`) |
| "Something ancient and terrible waits at the deepest levels… Only the devout, those who have earned the right to wield sacred arms" | **BOSS-ABADDON + Sword of Michael** (`game_encounters.py:961`, `weapon.json:8591`) |
| "Bosses tend to occupy unusually large, irregular chambers" | *Boss room visual cue* |
| "Each boss guards a threshold. Defeating them may not scatter treasure at your feet" | *Boss reward = passage, not loot* |
| "What you cannot see cannot harm you… Blindness is usually a curse, but against certain foes it may be a desperate salvation." | **BOSS-MEDUSA — blindness immunity to petrify** |
| "A bronze idol of a bull has been found in the floors before the labyrinth. King Minos offended Poseidon… Sacred waters remember old debts." | **Bronze Bull → fountain ritual** (`game_divine.py:385`, drops Ariadne's Thread) |
| "The mightiest of Greek warriors, near-invulnerable… heel is his only secret." | **HIDDEN-CHAR — Achilles** |
| "A Spartan warrior who held a narrow pass…" | **HIDDEN-CHAR — Leonidas** (`quirk_system.py:1217` references) |
| "A great conqueror in golden crown and royal purple cape, who never lost a battle" | **HIDDEN-CHAR — Alexander/Caesar** |
| "The hero who once slew the Minotaur walks as a hidden character — strangely at home in labyrinths." | **HIDDEN-CHAR — Theseus** |
| "A winged divine messenger in silver-blue, gifted with unmatched speed" | **HIDDEN-CHAR — Hermes** |
| "Ancient theology speaks of a second death — one the oldest texts say even Death himself cannot escape. Revelation may be the beginning of wisdom for those patient enough to observe, gather, and understand what they face at the very bottom." | **TABLET-OF-SECOND-DEATH + Abyssal Shimmer secret-victory path** (`items.py:481-498`, `_trigger_abyss`) |
| "A riddle-asking guardian has been encountered around the thirty-fifth depth." | **MYSTERY — Sphinx** (range 22-35, `mystery_system.py:19`) |
| "A son of the forge god roams the mid-depths, breathing fire. He shares his father's weakness to the element that stands opposite his breath." | **MONSTER — Cacus** (`monsters.json:20224`, cold weakness) |
| "The invulnerable lion of ancient myth… Heracles did not use either — and he still walked away." | **MONSTER — Nemean Lion** (`monsters.json:20393`) — kill-by-strangle hint |
| "A Slavic witch with iron teeth heals as she fights… iron and flame are what she fears most." | **MONSTER — Baba Yaga** (`monsters.json:20447`) |
| "A great serpent juvenile has been reported in the deeper levels… only the sky's own fury could wound such creatures." | **MONSTER — Jormungandr** (lightning weakness) |
| "A chaos witch in the mid-depths drains magical power… devout and the fiery have fared best" | **MONSTER — Rangda** (`monsters.json:20334`) |
| "An Egyptian servant of death drains life itself and dwells in darkness." | **MONSTER — Set/Khamut** (light + faith weakness) |
| "The knights of old sought the Grail in dungeons far below." | **MYSTERY — Grail** (`mystery_system.py:46-59`) |
| "Somewhere below the thirtieth level, an Oracle offers visions for tribute. Gold opens prophetic eyes" | **MYSTERY — Oracle** (`mystery_system.py:117-130`) |
| "A sealed tribunal near the thirtieth depth judges the wise on the great deeds of history." | **MYSTERY — Solomon's Tribunal** (`mystery_system.py:131-144`) |
| "Jason brought back the Fleece by taming beasts, not slaying them." | **MYSTERY — Fleece** (`mystery_system.py:60-73`, animal chain) |
| "A well exists somewhere in the depths where wisdom can be purchased, but it demands sacrifice." | **MYSTERY — Mimir** (`mystery_system.py:74-88`, PER cost) |
| "Tiresias was blind yet saw more than any sighted prophet." | **QUIRK — Tiresias** (answer while blind) |
| "Penelope wove and unwove her tapestry to delay her suitors." | **QUIRK — Penelope** (return to equipment) |
| "The Valkyrie chose who died in battle and valued precision above all. Those who kill from afar honor her philosophy." | **QUIRK — Valkyrie** (ranged kills) |
| "Merlin learned his craft by experimenting with the unknown. The unidentified wand in your hand is already teaching you something." | **QUIRK — Merlin** (10 unidentified wands, `quirk_system.py:726-730`) |
| "Scheherazade spun tales from books she had not yet finished." | **QUIRK — Scheherazade** |
| "Crowther and Woods hid a word inside a massive cave." | **XYZZY** (duplicates T3 #44) |
| "Paracelsus, father of toxicology, believed that enduring the poison was the path to immunity." | **QUIRK — Mithridates** (poison survival) |
| "Siegfried bathed in dragon blood and became harder to wound. Those who consume what their enemies inflict may gain unexpected resilience." | **QUIRK — Siegfried** (drink Fafnir's blood, `main.py:3019`) |
| "Job endured every affliction without losing faith." | **QUIRK — Job** |
| "Asclepius learned the art of healing from serpents. Those who harvest widely from venomous creatures may discover his secret recipe." | **COOKING-RECIPE — Asclepius**  |
| "The Fisher King's wound could only be healed by the right prayer at the right moment of desperation. The dungeon has its own wounded kings." | **MYSTERY — Fisher King** (`mystery_system.py:145-158`) |
| "Dionysus saw truth in intoxication. A distorted mind may perceive things a clear one cannot — hallucination is not always the enemy" | **QUIRK — Dionysus** (operate hallucinated) |
| "Apollo's arrows never missed. Those who maintain perfect chains of correct answers" | **QUIRK — Apollo** (perfect chains) |
| "Athena's owl observed all living things with equal patience. Knowledge of many creatures is a form of worship" | **QUIRK — Athena** (lore_known_monster diversity) |
| "Loki wore curses like cloaks and changed them freely. Enduring what others discard as worthless" | **QUIRK — Loki** (curse handling) |
| "Thor never parted from his hammer and never changed its name." | **QUIRK — Thor** (single-weapon loyalty) |
| "Beowulf tore Grendel's arm off with his bare hands. Sometimes the mightiest weapon is having none at all." | **QUIRK — Beowulf** (unarmed combat) |
| "The Norns wove fate from memory and prophecy. Those who seek lore often enough learn to read the threads" | **QUIRK — Norns** (this very mechanic, `quirk_system.py:801-805`) |
| "Jormungandr encircled the world, always returning to itself. Some bonds between warrior and weapon deepen through repetition" | **QUIRK — Jormungandr** |
| "Shiva dances the dance of illusion without rest." | **QUIRK — Shiva** |
| "Enkidu was born of the wilderness and knew every creature by name. A harvester of many species earns wild wisdom." | **QUIRK — Enkidu** (harvest diversity) |
| "Circe transformed her guests through impossible cuisine." | **QUIRK — Circe** (cooking diversity) |
| "Gawain's code demanded he fight even when bleeding." | **QUIRK — Gawain** |
| "Kali's dance is patient and eternal — she returns to the same foe again and again without tiring." | **QUIRK — Kali** |
| "Persephone mastered the bounty of two worlds." | **QUIRK — Persephone** |
| "Not every encounter in the dungeon is hostile. Some of the souls you meet are simply lost…" | **NPC-MORAL-ENCOUNTER SYSTEM** (`npc_encounters.py`) |
| "Some things in this dungeon were broken on purpose. A tool exists that can undo that separation. The alchemists understood: completion is the highest act of creation." | **Philosopher's Wrench** (duplicates T3 #45 thematically) |

### 2.5 Tier 5 hints (56 entries) — deepest secrets

| Hint | System reference |
|---|---|
| "The Philosopher's Stone lies at the deepest depth. Retrieve it and ascend — that is the whole of the quest." | **MAIN-QUEST** |
| "Prayer at a sacred altar carries more weight than prayer anywhere else." | **PRAYER + altar mechanics** (extra chain bonus when `at_altar`) |
| "Abaddon resists nearly everything the dungeon can throw at him. Those who survived speak of faith as the only weapon that drew blood — a blade that was earned, not found." | **BOSS-ABADDON + Sword of Michael (high-karma reward)** |
| "Theseus survived the labyrinth because Ariadne gave him a thread. In the old stories, it all began with a sacrifice at sacred waters — and ended with a gift that revealed every hidden passage in the maze." | **Bronze Bull → fountain → Ariadne's Thread** quest chain |
| "Perseus defeated the Gorgon with a mirror and a blindfold. The Grey Sisters' Eye was the price he paid for divine aid. Altars remember what is offered to them" | **Eye of Graeae → altar → Medusa quest** (`game_divine.py:409`) |
| "Sigurd slew Fafnir by digging beneath him and striking upward through the soft belly. Before the killing blow, he carried a broken blade — and before the blade was whole, a god had to intervene. Odin's methods are not always what you'd expect." | **Fafnir quest — pit dig + broken blade reforge** (`game_combat.py:1174`, `game_divine.py:459`) |
| "Fenrir's hide turns aside most blows. Enchantment and relentless chains of correct answers are the wolf-binders' tools — the ribbon was made of impossible things, and so must your preparation be." | **Gleipnir forge → Fenrir** |
| "The deepest dungeon levels contain provisions that sharpen a warrior's reflexes to an extraordinary degree." | *Late-game cooking + Magic Dungeon Carrot* |
| "A character who masters both Wisdom and Intelligence can cast powerful spells while enjoying the most generous quiz timers" | *Stat synergy WIS+INT* |
| "Murugan's mother gave him a lance that burned with righteous fire. It never missed" | **WEAPON — Vel of Murugan** |
| "The Monkey King stole his staff from a dragon's palace." | **WEAPON — Ruyi Jingu Bang** |
| "A crescent blade laughed as it cut. The sound grew louder as its wielder weakened" | **WEAPON — Laughing Sickle** |
| "A tiger-skin coat worn through seven impossible trials remembers every blow it absorbed." | **ARMOR — Tiger-skin coat** |
| "The Nibelungs forged a helm that removed its wearer from the world's perception." | **ARMOR — Tarnhelm** |
| "A sun-shield stands before the heavens. Those who carry it find that fire bends around them" | **SHIELD — Aegis/sun-shield** |
| "Isis reassembled her beloved from scattered pieces and breathed him back to life. She left a golden key behind — it works exactly once." | **Ankh of Isis** (resurrect_on_death, `accessory.json:5234-5248`) |
| "A ring engraved with the name of God commanded demons to kneel." | **Seal of Solomon** (`accessory.json:5218-5232`, pacify_chance) |
| "A clay tablet from the oldest city in the world once controlled fate itself. Those who carry it find that a single wrong answer is not always the end of the chain." | **Tablet of Destinies** (`artifact.json:299-312`, quiz_reroll) |
| "A heavenly spear stirred the ocean and from the brine created a nation. When its wielder fells an enemy, something ancient and still ripples outward through the space around the corpse." | **WEAPON — Ame-no-Nuboko / Izanagi's spear** |
| "The Irish Hound's battle-harness awakens a primal fury when its wearer's life hangs by a thread" | **ARMOR — Cú Chulainn's harness (warp-spasm)** |
| "The divine reward the faithful with permanent wisdom. Three boons are available to those who pray at the right altars with the right knowledge — and the gods do not offer them twice." | **Prayer boon system** (3 unique permanent boons per run, `game_divine.py`) |
| "Status effects on monsters are not merely inconveniences for them — they are openings." | *Combat status synergy* |
| "The man who catalogued the natural world and tutored a great conqueror" | **HIDDEN-CHAR — Aristotle** |
| "A bald, bearded philosopher who famously claimed to know nothing" | **HIDDEN-CHAR — Socrates** (WIS specialist) |
| "A sage who wrote of caves, shadows, and ideal forms" | **HIDDEN-CHAR — Plato** |
| "A dark-robed philosopher who declared that suffering builds strength" | **HIDDEN-CHAR — Nietzsche** |
| "A legendary archmage in a star-studded dark robe carries a staff and begins already knowing two powerful spells." | **HIDDEN-CHAR — Gandalf/Merlin-archetype** |
| "The Green Knight regenerates. Wounds close as fast as you can open them — unless something stops the healing entirely." | **MONSTER — Green Knight** (regen interrupt — fire damage?) |
| "The great whirlpool beast pulls everything toward its maw… feared the storm more than any blade" | **MONSTER — Charybdis** (lightning weakness) |
| "A severed arm of a demon king strikes three times for every one of yours. It has a weakness to purifying force" | **MONSTER — Ravana** (`monsters.json:21010-ish`) |
| "The Wendigo devours stamina itself — you will starve mid-fight if you are not prepared." | **MONSTER — Wendigo** (`monsters.json:20821`) |
| "The Wild Hunt rides through the deepest corridors. Phantom things fear iron and faith" | **MONSTER — Wild Hunt** |
| "Anansi the trickster confuses and relocates his prey before they can strike back." | **MONSTER — Anansi** (`monsters.json:20947`) |
| "A fragment of the World-Serpent carries acid that eats through armor as though it were cloth." | **MONSTER — Nidhoggr** |
| "Perseus held his shield as a mirror." | **QUIRK — Perseus** (reflect-based) |
| "Theseus mapped every inch of the labyrinth before he struck." | **QUIRK — Theseus** (exploration) |
| "Hermes moved between worlds faster than thought." | **QUIRK — Hermes** (teleportation) |
| "The Sibyl spoke ten thousand prophecies from memory. Early mastery of many subjects" | **QUIRK — Sibyl** (500 correct before L20) |
| "Ahasverus walked forever and never rested." | **QUIRK — Ahasverus** (no rest) |
| "Ariadne gave her thread so the hero could escape the maze swiftly when the deed was done." | **QUIRK — Ariadne** (fast exit after boss) |
| "Morgan le Fay cast her most powerful spells from the very edge of ruin." | **QUIRK — Morgan** (low-HP spellcasting, `quirk_system.py:823-826`) |
| "Cu Chulainn's battle-fury was born from fear itself." | **QUIRK — Cú Chulainn** |
| "Sisyphus' boulder rests on a steep slope in the deep dungeon. The Fates respect those who bear burdens willingly" | **MYSTERY — Sisyphus** (`mystery_system.py:159-172`) — also a QUIRK |
| "The Fisher King waits to be healed. A rare herb grows near his resting place, and faith is the medicine that makes the herb work." | **MYSTERY — Fisher King** (duplicates T4 entry with extra specificity) |
| "Near the sixtieth depth, an ancient wounded king waits in silence." | **MYSTERY — Fisher King** (duplicate) |
| "Odin hung on the World Tree for nine days and nine nights to gain wisdom. A similar vigil is said to grant extraordinary sight" | **QUIRK — Odin** (Oracle reveal hint, `mystery_system.py:414`) |
| "The Mithridates Protocol" | **QUIRK — Mithridates** (duplicate of T4) |
| "Prometheus burned forever and yet lived. Those who endure bleeding without dying" | **QUIRK — Prometheus** |
| "A chainsaw-wielding survivor from the world above… loud, brash, and carrying a weapon that cannot be set down. His other hand holds a boomstick" | **HIDDEN-CHAR — Ash Williams** (Evil Dead character) |
| "A white-haired monster hunter walks the dungeon armed with a silver blade and five learned Signs." | **HIDDEN-CHAR — Geralt of Rivia** (Witcher) |
| "A young woman with elder blood in her veins begins the dungeon already knowing how to step sideways through space. She carries a blade called Zireael" | **HIDDEN-CHAR — Ciri** (Witcher) |
| "A young trainer in a red-and-white cap has been seen descending… carrying not weapons but soul spheres." | **HIDDEN-CHAR — Pokemon trainer** (`mystery_system.py:634-648` Soul Sphere artifact) |
| "The First Magic Word was said to tear reality apart and send the speaker elsewhere. Some say speaking it still works, if you know where to type it" | **XYZZY** (duplicate, T5 emphatic) |
| "Adventurers sometimes tell of useless scraps of leather they find discarded in corridors. Those who held onto them long enough discovered they were not useless at all." | **Leather scrap → Vidar's Sandal forge** (`game_divine.py:521`, `artifact.json:141-152`) |
| "The oldest verse speaks of endings that are also beginnings. Not all doors require keys. Some require conviction, spoken aloud, in the right place, at the right moment." | **XYZZY** / **Abyssal Shimmer secret victory** (Revelation 20:14 inscription) |

**T5 patterns:** Heavy on quirks and hidden characters; uneven on the secret-victory path (Abyssal Shimmer + Tablet + Wrench gets oblique reference only); pop-culture hidden chars (Ash, Geralt, Ciri, Pokemon trainer) are explicit; mid-game boss tactics receive specific procedural hints (dig under Fafnir, blindfold for Medusa, six impossible things for Fenrir).

---

## 3. Item lore content

### 3.1 Artifacts (`data/items/artifact.json`)

23 artifacts, ALL with substantive lore. Tagged by what they hint:

| Item | Lore tag | Hints what |
|---|---|---|
| **philosophers_stone** | `min_level: 9999` (boss drop) | Macguffin; Magnum Opus alchemy reference; carries "transmute the bearer" themes — no mechanical spoiler |
| **bronze_bull** (`artifact.json:14-25`) | min_level 9999 (spawned by lore_levels) | Minos/Poseidon/sacred-waters — TEACHES the fountain ritual (`game_divine.py:385`) |
| **ariadnes_thread** (`artifact.json:26-37`) | min_level 15 | Theseus/labyrinth — TEACHES use against Asterion (defang per audit) |
| **eye_of_graeae** | min_level 25 | Perseus stole, traded for divine aid — TEACHES altar trade for Medusa fight |
| **cats_footstep, womans_beard, mountain_root, fish_breath, bird_spittle, bear_sinew** | 6 impossible ingredients, all min_level 60 | Gleipnir forge inputs — every one identifies itself as a Gleipnir component in plain text |
| **gleipnir** | min_level 9999 (forge product) | "Held the Wolf of Ragnarok until the end of days" — TEACHES Fenrir use |
| **leather_scrap** | min_level 1 | "Useless scrap left over from leather-working" — INTENTIONALLY misleading; T5 hint contradicts ("kept long enough… not useless at all") |
| **7 seals** (wrath/pestilence/famine/war/death/earthquake/silence) | min_level 9999 | "One of seven seals that hold the Pit closed" — TEACHES seal-demon gate |
| **scales_of_michael** | (judgment-altar drop, `game_encounters.py:961`) | "Weigher of Souls… for every locust of the Abyss, an angel descends." — TEACHES anti-locust boon mid-Abaddon fight |
| **cursed_lodestone** | NPC-encounter only (Sir Aldric, block 2) | Self-narrating: "the curse binds it to whoever takes it freely" — TEACHES remove-curse scroll requirement |
| **sealed_dispatch** | NPC-encounter only (Dying Courier, block 3) | "thousands of lives depend on its delivery" — no mechanic, narrative burden item |
| **palladium** (`artifact.json:285-298`) | min_level 45 | "reveals the path forward: while carried, the stairs on every floor glow faintly in the bearer's mind" — TEACHES self mechanic explicitly |
| **tablet_of_destinies** (`artifact.json:299-312`) | min_level 70 | "Tablet allows its bearer to reject fate once per floor — when a question is answered wrongly, the Tablet cracks and offers a different question." — TEACHES mechanic explicitly |
| **tablet_of_second_death** (`items.py:481-498`) | min_level 80 | "A circular slot in its center is shaped to hold something luminous… 'Place upon the threshold where the veil is thin.'" — TEACHES secret victory path |
| **scroll_lake_of_fire** (`items.py:501-522`) | min_level 50 | "the second death, the lake of fire" — Revelation 20:14 referenced literally |
| **philosophers_wrench** (`items.py:525-549`) | min_level 21 | "It does not tighten or loosen — it joins" — TEACHES Stone + Tablet fusion |

**Verdict:** Artifact lore quality is high. Every artifact either narrates the system it belongs to, or names the mythological hero whose strategy applies to the corresponding boss. The Bronze Bull/Eye of Graeae/Leather Scrap/six-impossible-ingredients chain is consistently traceable through item lore alone (without consulting hints.json).

### 3.2 Accessories (`data/items/accessory.json`)

~290 entries with `"lore"` field. Two registers:

**(A) Generic enchanted slots** (e.g. `ring_of_warning`, `ring_searching_silver`) — short flavor text describing the mechanic without mythological framing. These teach mechanics in-line. Example: "An amber ring containing a preserved insect that has not aged for ten thousand years. The preservation field extends to the wearer's metabolism" (`ring_sustenance_amber:3049`).

**(B) Named legendary accessories** — substantial mythological essays. Sampled:
- **ring_of_gyges** (`accessory.json:3367-3392`): Plato's Republic; "would a just man behave differently from an unjust man if he could act without consequence?" — pure philosophy, mechanic = invisibility
- **ring_of_the_nibelung**: Andvari's curse, four operas — names every owner who died wearing it
- **andvaranaut**: Loki, Otr's wergild
- **draupnir**: Odin's funeral ring; round-trip from Hel
- **brisingamen**: Freya's necklace, dwarves' four-day price
- **ring_of_solomon**: built Temple, bound Asmodeus, recovered when stolen
- **eye_of_horus**: wedjat fractions sum to 63/64
- **scarab_of_khepri**: Egyptian dawn beetle, regenerates
- **necklace_of_harmonia** (CURSED): Hephaestus' wedding curse, destroyed houses
- **ouroboros_pendant**: Kekulé and benzene ring
- **tyet_of_isis**: Book of the Dead Chapter 156
- **idunn_apple_charm**: aging gods, Loki's falcon
- **caduceus_charm**: lyre exchange with Apollo
- **torque_of_lugh**: "every skill simultaneously"
- **pectoral_of_amun**: "the hidden one"
- **ring_of_gawain**: Alliterative Morte / Green Knight poem
- **ring_of_odysseus**: "had no magical ring. He needed none."
- **ring_of_scheherazade**: "1,001 stories… argument for intellectual labour"
- **amulet_of_merlin**: incubus father, Nimue's tower
- **ring_of_pythia**: "Croesus was told… he would destroy a great empire. He did."
- **anklet_of_atalanta**: golden apples, "losing was the most interesting thing"
- **crown_of_croesus**: "Croesus's error was not the Oracle. It was the interpretation."
- **collar_of_njord**: marriage counsellors origin
- **ring_of_percival**: "courtesy has limits"
- **ring_of_lancelot**: "destroyed the Round Table by being exactly that"
- **seal_of_agrippa**: 16th century occult-philosophy systematizer
- **philosophers_ring_legendary**: catalogue's last page missing
- **amulet_of_pythagoras**: Hippasus drowned for the irrational
- **ring_of_hypatia**: 415 CE Alexandria
- **jade_cicada**: "Once per floor, when a blow would kill its wearer, the cicada intervenes." — mechanic stated
- **seal_of_solomon** (2nd entry, `accessory.json:5218`): "nearby enemies may find themselves frozen in place" — mechanic stated
- **ankh_of_isis** (`accessory.json:5234`): "When the wearer dies, the ankh shatters and Isis's magic pulls them back" — mechanic stated
- **rands_heart** (`accessory.json:5090`): personal love letter ("Robyn") — emotional gift item, warning effect
- **dreamspun_sketchbook, charmander_stuffie**: children's toy items — Charmander stuffie = pet system reference
- **silverlight_pendant, saints_reliquary, officers_signet, prophets_amulet**: ALL NPC-encounter rewards — lore narrates the NPC the player met

**Set items** (3 sets, 9 pieces): dragonslayer (ring + sword + armor), shadow_walker (ring + dagger + cloak), philosophers (ring + shard + staff). All three set rings' lore explicitly names the other two pieces.

**Verdict:** Accessory lore quality is excellent. The mythological items teach by association ("this Hero used this kind of strategy"). The set items advertise their completion bonus in plain text. The NPC-reward items braid back into the karma-encounter narrative.

### 3.3 Other slots

- **Weapons** (`data/items/weapon.json`): all 130+ entries have lore. Most are sketches of historical/material context ("Hardened gold — an alchemical alloy"). The legendary tier (sword_of_michael, mjolnir, fragarach, etc.) names the wielder, the deed, and often the enemy weakness.
- **Scrolls** (`data/items/scroll.json`): mythological invocations (Morpheus for sleep, Hermes for haste, Zeno for time stop, Carthage library fire for annihilation). Reward scrolls — "Sealed with X. A reward scroll from Dad -- show him this code!" — explicit out-of-game reward economy (consistent with CONTEXT §1).
- **Spellbooks** (`data/items/spellbook.json`): Necronomicon is the standout — "Naturom Demonto — roughly translated, the Book of the Dead. Bound in human flesh and inked in blood… It is NOT to be read aloud. Seriously. Don't." — register break (modern joke voice) but it's the Necronomicon multi-step quiz (Army of Darkness reference).
- **Armor** (`data/items/armor.json`): Vidar's Sandal lore (`armor.json:3725`) — "Vidar the Silent, son of Odin, wore it when he avenged his father — planting his foot on the lower jaw of the World-Wolf and tearing the beast apart with his bare hands." — TEACHES Fenrir kill mechanic.
- **Food**: Magic Dungeon Carrot is one of the chronicled pickups; cooking recipes (`recipes.json`) are out of audit scope for lore but the input ingredient list is the implicit hint.

---

## 4. NPC dialog content (`src/npc_encounters.py`)

**31 karma encounters**, 10 level blocks × ~3 candidates per block, 1 spawn per block per run.

Each encounter: NPC name, encounter description, 3 options (good/neutral/selfish) each with karma value (-1/0/+1), cost (item-from-inventory or stat-cost), reward (item/gold/stat or none), outcome text. Karma sum (-10..+10) feeds the **Michael Judgment** at L100 altar (`npc_encounters.py:1989-2045`) — five judgment tiers from `abaddon_empowered` (-6 or worse) to `sword_and_scales` (+10).

**Quest hooks by NPC:**

| Tag | NPC | Block (lvl) | Trigger item | Reward (selfish) | System reference |
|---|---|---|---|---|---|
| elara_amulet | Lost Girl | 1 (3-9) | silverlight_pendant (-1 lvl) | elaras_silver_ring | **Karma system + accessory chain** |
| brother_aldous | Dying Monk | 1 | — | saints_reliquary | **Karma + reliquary** |
| marta_ratchatcher | Rat-Catcher | 1 | — | potions + food | **Karma** |
| sir_aldric | Burdened Knight | 2 (11-19) | — | (+1 CON if selfish) / cursed_lodestone (if good) | **Karma + Remove Curse scroll** |
| tam_thief | Young Thief | 2 | — | gold + weapon | **Karma** |
| helena_cartographer | Injured Scholar | 2 | — | scrolls + gold | **Karma** |
| marcus_sword | Grieving Father | 3 (21-29) | oathkeeper_sword (-2 lvl) | (keep weapon) | **Karma + Oathkeeper** |
| blinded_soldier | Blinded Soldier | 3 | — | armor + gold | **Karma** |
| dying_messenger | Dying Courier | 3 | — | gold + potion / sealed_dispatch | **Karma + burden item** |
| deadite_woman | Moaning Woman | 3 | — | (ambush trap) | **EASTER EGG — Evil Dead Deadites** (Ash Williams T5 hint cross-ref) |
| sister_marguerite | Starving Nun | 4 (31-39) | — | accessory + gold | **Karma** |
| chained_priest | Chained Priest | 4 | — | scroll + potion + gold | **Karma** |
| old_konstantin | Old Warrior | 4 | — | accessory + gold | **Karma** |
| apprentice_healer | Poisoned Herbalist | 5 (41-49) | — | potions + food | **Karma** |
| ghost_grave | Ghost of Edwin | 5 | — | accessory + gold (HP cost variant) | **Karma + max_hp cost mechanic** |
| deserter | Legion Deserter | 5 | — | officers_signet | **Karma** |
| blind_seer | Blind Seer | 6 (51-59) | — | scrolls + potion | **Karma — "Cassandra"** explicitly invoked in dialog |
| trapped_seraph | Caged Angel | 6 | — | +1 WIS | **Karma + scroll-overload mechanic** |
| weeping_mother | Weeping Ghost | 6 | — | accessory | **Karma + SP cost mechanic** |
| ser_brennan | Dying Knight | 7 (61-69) | — | weapon + shield | **Karma** |
| cursed_scholar | Cursed Scholar | 7 | — | +2 INT (hp_percent cost variant) | **Karma + HP-percent cost** |
| fairy_jar | Trapped Fairy | 7 | — | +1 DEX | **Karma — fairy dust** |
| penitent | The Penitent | 8 (71-79) | — | penitents_blade + gold | **Karma + named weapon** |
| roderic_shield | Young Knight | 8 | lionheart_shield (-2 lvl) | (keep shield) | **Karma + Lionheart Shield** |
| forgotten_prisoner | Forgotten Prisoner | 8 | — | gold + accessory (gold-cost variant) | **Karma — dwarven lock gold-feed mechanic** |
| fallen_paladin | Fallen Paladin | 9 (81-89) | — | gold + armor | **Karma — atonement** |
| azarael_demon | Bound Demon | 9 | — | +2 STR + gold | **Karma — heaviest dark choice; scroll-rebind option** |
| child_shrine | Small Shrine | 9 | — | accessory + gold | **Karma — ghost child** |
| dying_prophet | Dying Prophet | 10 (91-98) | — | prophets_amulet | **Karma + Abaddon foreshadow** ("SEVEN SEALS" "THE DESTROYER WAKES" inscriptions) |
| petrified_adventurer | Stone Statue | 10 | — | weapon + armor | **Karma — basilisk + Restoration scroll** |
| last_merchant | Lost Merchant | 10 | — | weapon + accessory + gold | **Karma** |

**Merchant NPC** (separate, `mystery_system.py:582-686`): Svirfneblin Trader (deep gnome). 20% spawn per floor. Stock pulled from item categories; 15% chance of carrying a Soul Sphere (`mystery_system.py:633-648`). Soul Sphere lore: "Ancient texts say these vessels were used to bind creature spirits. One wonders what might happen if it were hurled with force..." — TEACHES the Pokemon-trainer mechanic obliquely (T5 hint cross-ref).

**Flavor NPC encounters** — 5 hardcoded in `flavor_encounters.py:34-243` + 92 generated in `data/flavor_encounters.json`. ~97 total. Spawn rate ~40% per floor, one-shot per run. Stages: 1-20 (newcomers), 21-40 (adventurers/scholars), 41-60 (mystics), 61-80 (otherworldly), 81+ (existential).

Selected high-value flavor encounters:
- **flv_blind_oracle** (`flavor_encounters.py:198-242`, level 41-60): "The dragon sleeps on gold and grief. The wolf eats the sun. The destroyer waits where faith is the only weapon." — directly previews **Fafnir/Fenrir/Abaddon strategies**.
- **flv_disguised_hermes** (data/json: l1771): Hermes cameo
- **flv_disguised_dionysus**, **flv_avatar_athena**, **flv_avatar_hermes_laughing**: hidden god avatars
- **flv_prophet_of_the_abyss**: Abaddon prophecy
- **flv_dwarven_smith_marta**: weapon enchant +1 for 80g
- **flv_dwarven_smith** (hardcoded line 159): same
- **flv_singing_bones / flv_singing_bones_2**: dungeon-history monologue
- **flv_oracle_of_endings**, **flv_dying_oracle_cassandra**: prophetic flavor without quest hooks
- **flv_humorous_imp_salesman**, **flv_false_merchant_goblin**, **flv_discount_demigod_merchant**: cursed-merchant variants

**NPC dialog gap:** No NPC encounter directly references the **Abyssal Shimmer / secret-victory path**. The Dying Prophet (block 10) hints at "SEVEN SEALS" + "THE DESTROYER WAKES" but not the Tablet/Wrench/Lake of Fire chain. The flavor Blind Oracle is the most direct boss strategy advance-warning.

---

## 5. Mystery content (`src/mystery_system.py`)

13 mysteries, each one-shot per run, floor-ranged. Spawn rate 60% per eligible floor (`mystery_system.py:282-284`).

| ID | Name | Range | Key item | Challenge | Reward | Hint reference |
|---|---|---|---|---|---|---|
| **sphinx** | The Sphinx | 22-35 | none | Philosophy esc_threshold T3 | +2 WIS / +1 INT | T3 hint #23 "lone sphinx in the depths", T4 #19 |
| **pandora** | Pandora's Coffer | 20-30 | Pandora's Key | Economics threshold T2 (**INVERTED** — failure = reward) | magic_resist + displacement + 300g | T3 hint #32 "Pandora's box… opening it was a mistake — but old stories are not always right." (signals inversion) |
| **grail** | Chapel of the Grail | 45-55 | A Chalice | Theology threshold T3 | +30 max HP +2 CON | T4 hint "knights of old sought the Grail" |
| **fleece** | The Fleece Altar | 38-50 | Golden Fleece | Animal chain T3 | regenerating + poison_resist permanent | T4 hint "Jason brought back the Fleece by taming beasts, not slaying them" |
| **mimir** | Mimir's Well | 42-55 | none | Philosophy chain T4 (**PER cost paid up-front**) | +3 INT, +1s all timers | T4 hint "well exists where wisdom can be purchased, but it demands sacrifice"; T5 "Odin hung on the World Tree" |
| **mjolnir** | The Dwarven Forge | 33-45 | Mjolnir (unfinished) | Math esc_threshold T3 | Mjolnir forged + STR+2 | T3 hint #24 "unfinished hammer buried deep" |
| **crucible** | Alchemist's Crucible | 10-22 | Lead Ingot | Philosophy threshold T1 | 400g | T3 hint #25 "Alchemists sought… lead to gold" |
| **oracle** | The Oracle's Rift | 25-35 | none (50g tribute) | Theology threshold T3 | **Oracle reveal — 3 quirk hints** | T4 hint "Somewhere below the thirtieth level, an Oracle offers visions" |
| **solomon** | Solomon's Tribunal | 30-42 | Seal of Solomon | History threshold T3 | +2 WIS + Ring of Command | T4 hint "sealed tribunal near the thirtieth depth judges the wise on the great deeds of history" |
| **fisher_king** | The Fisher King's Hall | 58-72 | Healing Herb | Theology threshold T4 | +30 max HP + halved prayer cooldown forever | T4 hint "Fisher King's wound" + T5 "rare herb… faith is the medicine" |
| **sisyphus** | Sisyphus' Hill | 78-92 | The Boulder (30 weight) | **Physical** — walk 25 tiles over carry limit | +3 STR +1 INT | T5 hint "Sisyphus' boulder rests on a steep slope" |
| **cauldron** | The Black Cauldron | 14-26 | none (3 prepared meals) | Cooking esc_chain T2 | searching + warning permanent | T3 hint "Celtic cauldron of transformation… demands meals as tribute" |

**Oracle reveal hint table** (`mystery_system.py:413-426`) — 12 quirk hints distributed:
- odin, mithridates, tiresias, penelope, orpheus, hermes, atalanta, musashi, scheherazade, merlin, prometheus, ragnarok

These quirk hints duplicate / overlap heavily with the T3-T5 hints in hints.json (e.g. "She wove and unwove" appears in both Oracle output and T4 hint).

**Verdict:** Mystery hint coverage is excellent. Every mystery has at least one hint line that names the figure (Sphinx, Pandora, Grail, Fleece, Mimir, Mjolnir, Crucible, Oracle, Solomon, Fisher King, Sisyphus, Cauldron). The Pandora **inversion** (fail-quiz = reward) is signaled by T3 hint #32 (the only hint that lets the player infer the inversion is intentional). The Fisher King's **stacking with Fisher King quirk** for double-halved prayer cooldown (REVERSE_ENGINEERED §2) is **not hinted** — neither hint references the synergy.

---

## 6. Flavor encounters (compact)

97 total scenes (5 hardcoded + 92 JSON). One-shot per run, ~40% spawn per non-boss floor.

System hooks observed:
- **Merchants / trade**: ~25 (lost merchant, suspiciously cheerful goblin, herbalist, dwarven smith, alchemist apprentice, fortune-merchant, plague doctor, rust-collector, food vendor, etc.)
- **Spirits / ghosts / undead**: ~15 (weeping ghost, singing bones x2, spectral librarian, time-lost soldier, cataloguing spirit, ghost soldier post, mirror walker, echo of dead wizard, sorrow lantern, sergeant Vael)
- **Hidden god avatars**: ~5 (Hermes — 2 versions, Athena, Dionysus, "fragment of a god")
- **Cursed/trap NPCs**: ~6 (cursed mirror, false merchant goblin, shade bargainer, djinn in a bottle, smiling merchant, beyond-being)
- **Mystic / oracle**: ~10 (blind oracle, dream weaver, oracle of endings, dying oracle Cassandra, mad cartographer, abyss cartographer)
- **Mechanically rewarded**: SP/HP cost → clairvoyance, blessed, mp_restore, hp_restore, +stat, random item. Most rewards are **temporary status effects** (clairvoyant 50 turns, blessed 30 turns) — adding to the active-world feeling but not unlocking permanent systems.

The flavor system is FUN scaffolding rather than quest scaffolding. Only the Blind Oracle (boss prophecy line) and Soul Sphere merchant directly hint at a hidden system.

---

## 7. Monster lore samples

Sampled across bands (`data/monsters.json`):

| Floor band | Sample monsters | Lore tone |
|---|---|---|
| **L1-10** | giant_rat, goblin, grid_bug, stymphalian_bird, satyr_warrior, hecate_hound, arachne (mini-boss L3-15), griffin (L7+) | Concise mythological framing. Arachne names her own weakness (web → fire); Stymphalian Bird names Heracles' bronze krotala defeat. Empusa lore mentions Hecate. |
| **L11-30** | sphinx (L13-31, w/ riddle), talos (L12-30, ankle ichor), lamia, echidna (L15+), abyssal_mimic (L51+) | Sphinx lore states "she sits at crossroads… will attack any who approach without first attempting her puzzle" — mystery-system foreshadow. Talos names the ankle/ichor weakness in the lore directly. |
| **L31-60** | erlking, camazotz, cacus, rangda, nemean_lion, baba_yaga, green_knight, charybdis | Cacus lore names Hercules; Baba Yaga names iron teeth + healing; Nemean Lion describes Hercules' strangle solution (T4 hint cross-ref); Green Knight: "regenerates… unless something stops the healing entirely" |
| **L61-80** | adult_dragon, iron_golem (acid weakness in lore), greater_lich, arch_demon, wendigo (L80-100 SP-drain) | Adult dragon: "they often know exactly what every item in their hoard is and how it was taken" — flavor; iron_golem names acid weakness explicitly; greater_lich names phylactery |
| **L81-99** | death_lord, chaos_spawn, soul_eater, anansi, ravana (and seal demons) | Death Lord: "heralds of an End that has not yet come" — Abaddon foreshadow; chaos_spawn: "philosophers debate whether… have consciousness" |
| **Bosses (L20/40/60/80/100)** | asterion (Pasiphae+Cretan Bull), medusa ("Only a mirror shield can safely meet her gaze"), fafnir ("Only the hero Sigurd, who struck from below…"), fenrir ("Son of Loki… bound by Gleipnir, he tore off the hand of Tyr"), abaddon ("dominion over the locusts of the Abyss… key to the pit") | All five boss lore lines TEACH the historical hero's strategy. The defeat mechanic is encoded in plain text. |
| **Cow King (L30-39 secret)** | cow_king | "The undisputed sovereign of the Moo Moo Farm… Diablo II reference" — easter egg lore |

**Verdict:** Monster lore consistently teaches resistances/weaknesses through mythological context. Boss lore is exemplary — every boss's defeat is sketched in the lore text. The seal demon lore (sampled at the seal artifacts, not the monsters themselves) carries the seal-gate narrative.

---

## 8. Story popups + chronicle entries

### Story popups (`src/main.py:3354-3512`)

8 popups: `dungeon_entrance`, `boss_asterion`, `boss_medusa`, `boss_fafnir`, `boss_fenrir`, `boss_abaddon`, `exit_with_stone`, `exit_without_stone`.

Voice: third-person mythological recap, ending in a turn-the-page line ("The first guardian falls. The dungeon opens deeper."). Each boss popup names the hero who originally defeated this monster and the strategy they used (Asterion → Theseus + Ariadne's thread; Medusa → Perseus + mirror; Fafnir → Sigurd + pit; Fenrir → gods + Gleipnir; Abaddon → "nature of wisdom itself").

Code drop: only `exit_with_stone` carries a code (`'QUEST-COMPLETE'`). The Abyss secret-victory drops a different code in `_trigger_abyss` (per CONTEXT §1).

`exit_without_stone` is the harshest text in the game ("You ran… from the people who needed you most"). It is intentionally bleak.

**Notable absence**: there is **no story popup** for the Abyss secret-victory (Lake-of-Fire scroll triggers it via `game_magic.py:1547+`, separately).

### Chronicle entries (~30 unique lines, first-person)

Triggered at:
- Game start, descent, dungeon-level milestones (10/20/30/…/100), bones ghost encounter, special-room first-time (`main.py:423-441`, `1136-1143`)
- Pickup of canon-significant items (`main.py:2128-2150` — 18 specific items)
- Boss kills (`game_combat.py:608-630` — 5 boss lines + 7-of-7 seals line + each individual seal)
- Major encounters: judgment altar (4 karma-tier-specific lines `game_encounters.py:961-989`), unicorn (2 outcomes), bones first-trap-disarm, first compound recipe, fountain drink, Bronze Bull → fountain ritual, Eye → altar, Broken Blade → Odin's altar, Dwarven Forge feed, Leather scraps → Vidar's Sandal forge, grave robbing, throne sitting, prayer freeze (Death chase), Necronomicon learn, identification of remarkable items, Soul Sphere hatch, Fafnir's blood, Wrench fusion, Complete Tablet on Shimmer, Death-pursuit start, Death's kill, Surface exit with Stone, Surface exit without Stone, Ankh-of-Isis revival, Rand's-Heart revival, quirk unlock generic line
- XYZZY chord (`main.py:2571`)

**First-person voice samples** (drawn from code):
- "Something is following me. I felt it before I saw it. Death itself. I need to run."
- "I killed Death. The lake of fire opened beneath it and swallowed it whole. The silence afterwards was the loudest thing I've ever heard."
- "All seven seals are broken. The ground split open. Whatever is down there, it's free now. And I have to face it."
- "Prayed while Death hunted me. It froze in place. {N} turns. That's all I get."
- "I died. Then light. Isis pulled me back. The ankh is dust now."
- "I died. I felt it — the cold, the nothing. Then warmth. Rand's Heart pulled me back. The locket is dust now. I don't get a second chance."
- "Spoke an old word of power. XYZZY. Reality flickered. Something changed. I don't think I was supposed to know that word."

The chronicle voice is consistent and exemplary throughout. It is the game's de-facto narrative spine and its single largest body of first-person discoverability content. The chronicle does **not** spoil mechanics — it states what the *character* observed, not what the *system* did. This satisfies CONTEXT §6 explicitly.

---

## 9. *** Discoverability gap analysis ***

The master table: every major developer-built system × the trail (if any) that points the player toward it.

Grades:
- **WELL-hinted** — multiple lore lines + named in popup/dialog/lore. Attentive player will find it.
- **Lightly hinted** — one or two oblique references; easy to miss.
- **No hint at all** — pure code; player must read source or experiment exhaustively.

### Boss quests (Layer 1+)

| System | Trail | Grade |
|---|---|---|
| **Asterion (L20)** boss + Ariadne's Thread defang | Story popup, monster lore, T4 hint, T5 hint, Bronze Bull lore, Thread lore, Eye-of-Graeae lore, flavor Blind Oracle preview | **WELL-hinted** |
| Ariadne quest chain (Bronze Bull → fountain → Thread) | T4 hint ("bronze idol… sacred waters remember old debts"), T5 hint ("Theseus survived… sacrifice at sacred waters… gift that revealed every hidden passage"), Bronze Bull lore explicit | **WELL-hinted** |
| **Medusa (L40)** mirror + blindness strategy | Story popup, monster lore ("Only a mirror shield can safely meet her gaze"), T4 hint, T4 blindness hint, T5 Perseus hint | **WELL-hinted** |
| Grey Sisters' Eye → Perseus altar trade (Medusa quest) | T4 hint, T5 hint ("Altars remember what is offered"), Eye-of-Graeae lore | **WELL-hinted** |
| **Fafnir (L60)** dig + strike-from-below | Story popup, monster lore (Sigurd named + strategy explicit), T4 hint, T5 hint | **WELL-hinted** |
| Broken Blade of Gram → Odin altar reforge | T5 hint ("broken blade — and before the blade was whole, a god had to intervene"), `game_divine.py:459` chronicle, broken blade item lore (UNVERIFIED — read needed) | **Lightly hinted** |
| Fafnir's blood drop → Siegfried quirk | T4 hint, chronicle line | **Lightly hinted** |
| **Fenrir (L80)** rage mechanic + enchanted weapons | Story popup, monster lore (rage_interval not in lore text), T4 hints (2: grew-stronger + Gleipnir) | **WELL-hinted** |
| Gleipnir forge (6 impossible ingredients) | T4 hint ("six things that do not exist"), T4 hint ("forge of dwarven make"), every ingredient names "Gleipnir" in own lore | **WELL-hinted** |
| Vidar's Sandal (Fenrir instant-kill via leather-scrap altar) | T5 hint ("scraps of leather… not useless at all"), Vidar's Sandal armor lore (mechanic explicit), chronicle line | **WELL-hinted** |
| **Abaddon (L100)** holy weapon + faith | Story popup, monster lore ("holy" weakness), T4 hint, T5 hint, NPC Dying Prophet | **WELL-hinted** |
| **Seal demons (L83-97)** — break-7-seals gate | Each seal artifact lore ("One of seven seals that hold the Pit closed"), seal-break chronicle lines, "ALL SEVEN SEALS ARE BROKEN" message, NPC Dying Prophet shouting "SEVEN SEALS" + "THE DESTROYER WAKES" | **WELL-hinted** |
| **L99 altars resist-strip during Abaddon fight** | T2 hint #14 (altar generic), T5 hint #2 ("Prayer at a sacred altar carries more weight than prayer anywhere else") | **Lightly hinted** — REVERSE_ENGINEERED §2 Q12 confirms this is intentionally minimal; the *resist-strip* specifically has no dedicated hint |
| **Sword of Michael (max-karma path)** | T4 hint ("Only the devout… earned the right to wield sacred arms"), T5 hint ("blade earned not found"), karma-judgment popup lines (`npc_encounters.py:2016-2026`), 31 NPC karma encounters as the actual gameplay loop | **WELL-hinted** |
| **Scales of Michael (mid-karma path)** | Karma-judgment popup, scales item lore ("Weigher of Souls… for every locust… an angel descends"), Sword path strictly above it | **WELL-hinted** |
| **Cow King (L30-39 secret level)** | Cow King lore (Diablo II reference, "Moo"), Pasture scroll lore, encounter `game_encounters.py:90` chronicle line | **Lightly hinted** (player must trigger the easter egg first; no in-game hint announces the level) |

### Secret-victory layer (Act IV)

| System | Trail | Grade |
|---|---|---|
| **Tablet of Second Death** — the slot-holds-the-Stone artifact | Artifact lore (`items.py:491` — "Place upon the threshold where the veil is thin"), chronicle pickup line, T4 hint ("Ancient theology speaks of a second death — one the oldest texts say even Death himself cannot escape. Revelation may be the beginning of wisdom for those patient enough to observe, gather, and understand") | **WELL-hinted** |
| **Philosopher's Wrench** — the joining tool | Artifact lore (`items.py:545` — mechanic explicit), T3 hint #45 ("'The Wrench completes what is broken,' he wrote. 'Stone into Tablet, purpose into form.'"), T4 hint #60, chronicle line | **WELL-hinted** |
| **Abyssal Shimmer** — the threshold | T2 hint #24 ("Some places in the dungeon shimmer with energy that doesn't belong to this world"), T3 hint #46 ("Theologians call certain ground 'thresholds'… Scripture marks these places."), "Revelation 20:14" in-game inscription | **WELL-hinted** |
| **Scroll of Lake of Fire** — final-rite scroll | Scroll lore (`items.py:518` — Revelation 20:14 explicit), chronicle pickup line | **WELL-hinted** |
| **Combine Stone + Tablet via Wrench** workflow | Wrench lore states it ("joins them"), chronicle "I think I know what it's for", "The Stone fit the Tablet perfectly" pickup line | **Lightly hinted** (player must put 3 pieces together — but each piece self-narrates) |
| **Drop Complete Tablet on Abyssal Shimmer** trigger | Implicit only; no hint says "drop ON the shimmer" — chronicle line fires *after* the drop. The Shimmer's "Revelation 20:14" inscription is the only standing clue. | **Lightly hinted** |
| **Read Lake of Fire scroll to kill Death** | T5 hint #56 ("oldest verse speaks of endings that are also beginnings… require conviction, spoken aloud, in the right place, at the right moment.") | **Lightly hinted** |
| **`_trigger_abyss` reward code (Scroll of Death's Bane)** | Per CONTEXT §1: "Take this code to your father proudly — you have shown true Wisdom and Courage." Player-facing only after the full chain executes. | n/a (post-success only) |

### Hidden characters (referenced as "secret characters")

| Hidden char | Specific hint | Grade |
|---|---|---|
| Prometheus (fire-bringer, gold sash) | T3 #11 | **Lightly hinted** |
| Buddha (bald, robed, WIS specialist) | T3 #12 + T5 hint ("bald, bearded philosopher who claimed to know nothing" — Socrates duplicate?) | **Lightly hinted** |
| Odysseus (hooded wanderer, 10y at sea) | T3 #13 | **Lightly hinted** |
| Pythagoras (forest green, harmonics) | T3 #14 | **Lightly hinted** |
| Achilles (golden armor, crimson plume, heel) | T4 hint | **Lightly hinted** |
| Leonidas (Spartan, scarlet cape) | T4 hint | **Lightly hinted** |
| Alexander/Caesar (conqueror, purple cape) | T4 hint | **Lightly hinted** |
| Theseus (helmet, labyrinth) | T4 hint | **Lightly hinted** |
| Hermes (winged messenger) | T4 hint | **Lightly hinted** |
| Aristotle (catalogued nature) | T5 hint | **Lightly hinted** |
| Socrates (knew nothing) | T5 hint | **Lightly hinted** |
| Plato (caves and shadows) | T5 hint | **Lightly hinted** |
| Nietzsche (suffering builds strength) | T5 hint | **Lightly hinted** |
| Gandalf/archmage (starry robe, 2 spells) | T5 hint | **Lightly hinted** |
| Ash Williams (chainsaw + boomstick + book) | T5 hint, Deadite NPC encounter | **Lightly hinted** |
| Geralt of Rivia (white hair, silver sword, 5 Signs) | T5 hint | **Lightly hinted** |
| Ciri (elder blood, Zireael) | T5 hint | **Lightly hinted** |
| Pokemon trainer (red-white cap, soul spheres) | T5 hint, Trainer's Cap armor lore, Soul Sphere artifact lore on merchant | **Lightly hinted** |

**Hidden character gap:** All 18 hidden characters get exactly one T3-T5 hint line each. None of them appears in the main character-select flow (the player can't actively choose them — they unlock somehow). The mechanism by which hidden characters unlock is **NOT hinted at all** in any of the sampled lore (the source-of-truth for the unlock mechanism is the quirk/character-select code which I have not exhaustively read — flagging as an open question).

### Major mechanics

| Mechanic | Trail | Grade |
|---|---|---|
| WIS → quiz timer | T1 hint #1 explicit | **WELL-hinted** |
| Stair-rest heal | T2 hint #6 explicit | **WELL-hinted** |
| Hunger → HP drain | T1 hint #2 oblique | **Lightly hinted** |
| Scroll vs spellbook consume | T1 hint #3 explicit | **WELL-hinted** |
| Cooking system | T1 #4, T2 #5, T3 ×10 recipe hints, +5 quirk hints | **WELL-hinted** (over-determined) |
| Lockpick fragility | T1 hint #6 explicit | **WELL-hinted** |
| Damage types (slash/pierce/blunt) | T1 hint #11 | **WELL-hinted** |
| STR / CON / INT / WIS / DEX / PER stats | T1 hints #12-13, T2 #2, #4, #11, T5 #9 | **WELL-hinted** |
| Trap system | T1 hint #15, chronicle line | **Lightly hinted** |
| Damage-type → elemental resists | T2 hint #1, T2 #7, T2 #19 | **WELL-hinted** |
| Altar BUC reveal | T2 hint #13 | **Lightly hinted** |
| Altar prayer chain bonus (`at_altar` +1) | T5 hint #2 explicit | **WELL-hinted** |
| **3 unique prayer boons per run** | T5 hint #21 explicit ("Three boons are available to those who pray at the right altars with the right knowledge — and the gods do not offer them twice.") | **WELL-hinted** |
| Resistance accessory value | T2 hint #19 | **WELL-hinted** |
| Cursed equipment / Remove Curse scroll | NPC Sir Aldric (Cursed Lodestone), accessory cursed items lore (necklace_of_harmonia), scroll-of-remove-curse lore | **WELL-hinted** |
| Wand charges depleting | T2 hint #9 | **WELL-hinted** |
| Polearm reach | T2 hints #8 + #15 (duplicate) | **WELL-hinted** |
| Confusion → timer mod | T2 hint #3 | **WELL-hinted** |
| Fountain mechanic | T3 hint #43 + Bronze Bull narrative | **WELL-hinted** |
| **Quiz subject diversity → readiness** | T2 hint #12 | **WELL-hinted** |
| **Bones / persistent ghost** | Chronicle line on encounter (`main.py:441`), bones.py — no lore line in hints.json | **Lightly hinted** |
| **Pet system** | Charmander Stuffie lore, Trainer's Cap lore, Soul Sphere lore, Pokemon trainer hint, chronicle "I'm not alone anymore" line | **WELL-hinted** |
| **Status effect → opening for combat** | T5 hint #22 ("Status effects on monsters are not merely inconveniences for them — they are openings.") | **WELL-hinted** |
| **Lore-Identified corpses** (`main.py:_examine_corpse`) | The Athena quirk hint hints at the importance ("Knowledge of many creatures is a form of worship") but **no hint says** "examine corpses to log lore" | **No hint at all** (the menu UX is the only teacher) |
| **Death chase mechanic** (death_pursues) | Chronicle line on start, "Death quickens. The scraping is faster now." status messages, T5 #2 prayer reference indirect | **Lightly hinted** (player learns by encounter only) |
| **Save deletion on death** | Not hinted — permadeath is the lineage default | **No hint at all** |

### Major quirks (sample — full quirk lore coverage is in the §2.4-2.5 tables)

| Quirk | Hint | Grade |
|---|---|---|
| Norns (this Recall Lore mechanic) | T4 hint explicit | **WELL-hinted** (poetic, not procedural) |
| Sibyl (500 correct before L20) | T5 hint | **Lightly hinted** |
| Nostradamus (Recall Lore while debuffed) | NOT hinted in hints.json | **No hint at all** |
| Second Sight (Recall Lore while blinded) | NOT hinted | **No hint at all** |
| Ramanujan (500 math in run) | NOT hinted in hints.json (only quirk-flavor on unlock) | **No hint at all** |
| Cassandra (pass threshold with 2+ wrong) | T3 hint | **Lightly hinted** |
| Merlin (10 unidentified wands) | T4 hint explicit | **WELL-hinted** |
| Diogenes' Lantern (drop the Shard) | T3 hint #16 explicit | **WELL-hinted** |
| Fisher King (mystery + stacks with Fisher King quirk-mystery for double-halved prayer cooldown) | Mystery hint, but **the stack** is not hinted | **Lightly hinted** |
| Beowulf (unarmed combat) | T4 hint | **Lightly hinted** |

### Other developer-built systems

| System | Trail | Grade |
|---|---|---|
| **Hidden debug terminal** (backtick key) | T1 hint #16, T2 hint #23 (explicit "sits beside the number 1"), T3 #44, T4 #36, T5 #53 (5 hints!) | **WELL-hinted** |
| **XYZZY** chord | T3 #44, T5 #53 (Crowther/Woods reference) | **WELL-hinted** |
| **Trainer's Cap pet regen bonus** | Trainer's Cap lore | **WELL-hinted** |
| **NPC moral encounters** | T4 hint "Not every encounter in the dungeon is hostile" | **Lightly hinted** (player learns by encounter) |
| **31-NPC karma → Michael judgment at L100** | No hint in hints.json names the judgment specifically | **No hint at all** for the mechanism; the L100 altar arrival is its own discovery |
| **Cursed Lodestone curse-transfer mechanic** | NPC dialog + item lore explicit | **WELL-hinted** |
| **Mimics in containers** | Adult-mimic monster lore + mimic detection PER check (`main.py:1160`) | **Lightly hinted** |
| **Soul Sphere (Pokemon-trainer mechanic)** | T5 hidden-char hint, Soul Sphere artifact lore on merchant | **Lightly hinted** |
| **Necronomicon multi-step quiz / Army of Darkness summons** | Necronomicon spellbook lore explicit | **WELL-hinted** |
| **Ankh of Isis / Rand's Heart auto-revival** | Both accessory lore lines state the mechanic; chronicle lines on trigger | **WELL-hinted** |
| **Tablet of Destinies quiz-reroll** | Artifact lore explicit | **WELL-hinted** |
| **Set bonuses (dragonslayer / shadow_walker / philosophers)** | Each set ring's lore names the other two pieces and the set bonus | **WELL-hinted** |
| **Magic Dungeon Carrot (Stuffie fire breath)** | Chronicle pickup line ("Something tells me I shouldn't eat this one") + `_int_scaled_damage` references | **Lightly hinted** |
| **Flux Capacitor** | NO hint in hints.json or item lore consulted; spawned via `_spawn_flux_capacitor` (game_input.py:416) | **No hint at all** (UNVERIFIED — flagging) |
| **Diogenes' Lantern artifact mechanic** (shard drop) | T3 hint #16 names Diogenes | **Lightly hinted** |
| **High-karma Sword vs Mid-karma Scales** | Karma-judgment popup lines (5 tiers) ARE the lore; player learns mid-judgment | **Lightly hinted** as far as **planning** the karma path is concerned |

### Top 10 systems with **NO** discoverability hint trail

1. **Nostradamus quirk** (Recall Lore while mentally debuffed) — no hint
2. **Second Sight quirk** (Recall Lore while blinded) — no hint
3. **Ramanujan quirk** (500 math correct in a run) — no hint
4. **Corpse-examine philosophy quiz** → monster lore log (`_examine_corpse`) — no hint that the menu exists or that knowledge accumulates
5. **The Save-deletion-on-death rule** — no in-game lore line (lineage assumption only)
6. **Karma-NPC count → Michael Judgment threshold table** — player knows the choices feel meaningful, but the -10..+10 scale and the 5-tier judgment is not previewed
7. **Flux Capacitor wand** (special spawn) — no hint located (UNVERIFIED but I searched item-class lore and hints.json and found nothing)
8. **Fisher-King quirk + Fisher-King mystery stack** (double-halved prayer cooldown) — neither hint references the synergy
9. **The hidden-character unlock mechanism** — every hidden char has a flavor hint, but none of the hints describes HOW to unlock them
10. **Special-room (treasury/library/graveyard) loot patterns** — chronicle lines fire on first encounter, but no hint pool describes the special rooms' rules in advance

### Top 5 systems **WELL-hinted**

1. **Cooking system** — 1 T1 + 1 T2 + 10 T3 recipe hints + 5 quirk hints + monster ingredient_ids in lore. Over-determined.
2. **Boss strategies (all 5)** — story popups + monster lore + 2-3 hints per boss + mid-tier hints + flavor Blind Oracle preview
3. **Hidden debug terminal / XYZZY** — 5 hints across tiers, explicit physical key reference at T2
4. **Gleipnir 6-impossible-ingredients forge** — T4 ingredient hint + every ingredient names "Gleipnir" in own lore + Dwarven Forge altar + chronicle line
5. **Secret-victory chain (Tablet + Wrench + Shimmer + Lake of Fire)** — every artifact self-narrates, T2/T3/T4/T5 hints each touch a piece, Revelation 20:14 inscription

---

## 10. Cross-system interactions (hints that bridge multiple systems)

Particularly important: hints that connect SYSTEM A to SYSTEM B and reward the player who synthesizes.

- **T5 #4** ("Theseus survived… sacrifice at sacred waters — and ended with a gift that revealed every hidden passage") bridges **Bronze Bull artifact → fountain mechanic → Ariadne's Thread → Asterion strategy**.
- **T5 #5** ("Perseus… Altars remember what is offered") bridges **Eye of Graeae → altar interaction → Medusa strategy**.
- **T5 #6** ("Sigurd… carried a broken blade — and before the blade was whole, a god had to intervene") bridges **Broken Blade pickup → Odin altar → Fafnir strategy + the dig mechanic**.
- **T4 "Bosses tend to occupy unusually large, irregular chambers"** + **T4 "Each boss guards a threshold"** bridge **dungeon-generation visual cue → boss room awareness → "real reward is what waits further down."**
- **T5 #21** ("Three boons are available to those who pray at the right altars with the right knowledge") bridges **prayer mechanic → altar mechanic → permanent stat boons economy**.
- **T2 #13 + T2 #14** bridge **altar location → BUC reveal mechanic + prayer mechanic**.
- **Soul Sphere artifact lore on merchant** ("One wonders what might happen if it were hurled with force") + **T5 Pokemon-trainer hint** bridge **merchant system → hidden Soul Sphere mechanic → pet/companion system**.
- **T3 #45 + T4 #60 + Wrench lore** form a triple-bridge into the **Wrench → Tablet → Shimmer secret-victory chain**.
- **T5 #54 leather scraps + Vidar's Sandal armor lore + altar mechanic** bridge **leather-scrap pickup → leather-scrap altar interaction → instant-kill Fenrir**.
- **NPC karma encounters + Sword/Scales of Michael items + judgment popup** form a single multi-floor cross-system narrative.

---

## 11. Open questions / unhinted content

1. **Fisher-King-quirk + Fisher-King-mystery stack**: per REVERSE_ENGINEERED §2, prayer cooldown halves twice when both are active. Neither hint in either system mentions stacking. Is this intentional reward for the player who solves both, or a balance bug?
2. **Hidden character unlock mechanism**: there are 18+ hidden chars hinted in T3-T5, but I haven't located any hint that describes *how* the player triggers an unlock. Is unlocking deterministic (defeat X, complete Y) or random (Oracle reveal pool)? The Oracle reveal table covers 12 quirks but not characters.
3. **Flux Capacitor** wand: I searched hints, item lore JSONs, and didn't find any reference. UNVERIFIED — the spawn function exists; the lore trail does not (or I missed it).
4. **The Soul Sphere / Pokemon-trainer character** is hinted in T5; the merchant carries Soul Spheres at 15% chance — but the **pet system** mechanics (bonding, AI, regen via Trainer's Cap) are not threaded through a single discoverability chain. The pet system feels half-hinted: the pieces exist but the player has to assemble three independent T5 cues + the Trainer's Cap armor lore.
5. **Corpse philosophy-quiz examine**: this menu produces persistent `lore_known_monster_ids` per player. Nothing in hints.json describes the existence of the menu. The Athena quirk hint says knowledge of many creatures is worship; that's the closest cue.
6. **Cow King secret level**: the entry is from poking a cow at the right place. No hint warns the player. The Cow King lore + Pasture scroll are revealed *after* the encounter.
7. **`_BOSS_STORY_KEYS` only covers 5 bosses** (`main.py:3515-3521`): asterion, medusa, fafnir, fenrir, abaddon. There is **no story popup for the Cow King defeat**. The popup chain skips it deliberately or this is a gap.
8. **The `boss_levels.py` arena altar count for Abaddon** (REVERSE_ENGINEERED §2 Q5) — I did not open that file in this pass. The hint trail asserts that altars matter "where the altars rise" (T2 #14 implies plural). If the arena has only one altar the hint is misleading; if it has 4-6, the hint is honest. This is a CODE/CONTENT question rather than a lore question.
9. **REVERSE_ENGINEERED §2 Q12** asked whether a T5 hint should be added for L99 altar resist-strip. As of this index, the resist-strip specifically is **not** named in any hint — it's the strongest specific-mechanic gap among the boss layers.
10. **Voice register dip — Necronomicon lore** ("It is NOT to be read aloud. Seriously. Don't.") breaks the register vs. the rest of the spellbook lore. Intentional joke (Army of Darkness) but flagged here for VOICE consistency.
11. **Duplicate hints**: T2 #8 = T2 #15 (polearm reach twice); T3 #31 = T2 #21 thematically (Palladium / wooden idol from heaven); T3 #44 = T4 #36 = T5 #53 (Crowther/Woods/XYZZY three times across three tiers, varying voice); T5 #43 = T5 #44 (Fisher King). Some duplication is intentional graduation; some looks like overlap.

---

## Summary statistics

- **Hint count by tier**: T1: 16, T2: 24, T3: 47, T4: 60, T5: 56 — total 203.
- **NPC karma encounters**: 31 (10 blocks × ~3 candidates, 1 per block per run).
- **Flavor encounters**: 97 (5 hardcoded + 92 JSON, ~40% spawn per non-boss floor).
- **Mysteries**: 13 (60% spawn per eligible floor).
- **Boss story popups**: 5 + dungeon-entrance + 2 endings = 8 total.
- **Chronicle entry types**: ~30 distinct lines + per-item flavor for 18 canon items + room-entry + milestone-entry.
- **Items with substantive lore**: 23 artifacts, ~290 accessories, 130+ weapons, all scrolls, all spellbooks, all named armor.
- **Hidden-system lore lines bridging multiple subsystems**: at least 9 (enumerated §10).
