# Voice Content Catalog — Philosopher's Quest

**Auditor:** VOICE (single agent)
**Date:** 2026-05-15
**Scope:** Player-facing prose only. Question banks (`data/questions/*.json`) excluded per rubric.

The catalog enumerates every prose surface the player reads, scores it 1–5 against the chronicle voice / geek-dad mythic register from `CONTEXT.md`, and notes drift, clashes, and surface-specific issues. After the catalog, a **secret-spoilage scan** and a **lore-coverage gap analysis** follow.

Voice scoring rubric:
- **5** — Pitch-perfect chronicle/mythic register. First-person, short sentences, awe without bombast, geek-dad mythic vocabulary.
- **4** — Substantively in voice, with isolated drifts.
- **3** — Functional but inconsistent; mixes mythic and statblock-flat.
- **2** — Predominantly mechanical/dry; only occasional voice notes.
- **1** — Pure RPG-statblock / corporate / generic. No voice.

---

## Surface 1: `_log_chronicle()` calls (first-person diary)

**File/range:** 52 calls across `src/main.py`, `src/game_combat.py`, `src/game_divine.py`, `src/game_magic.py`, `src/game_encounters.py`, `src/quirk_system.py`

**Sample quotes:**
- `main.py:274` — *"Descended into the dungeon. The air smells like dust and old stone. The Stone is somewhere below. I need to find it and get back out."*
- `main.py:1264` — *"Something is following me. I felt it before I saw it. Death itself. I need to run."*
- `main.py:1399` — *"I killed Death. The lake of fire opened beneath it and swallowed it whole. The silence afterwards was the loudest thing I've ever heard."*
- `main.py:1457` — *"I made it. I climbed back out with the Stone. The sunlight hurt my eyes. I'd forgotten what it looked like."*
- `game_divine.py:626` — *"Sat on a throne in the dark. It fit perfectly. That worries me."*
- `game_combat.py:592` — *"Fenrir is bound. Or dead. I'm not sure which. The wolf was... vast. The ground still shakes."*
- `game_encounters.py:90` — *"I poked a cow too many times. The floor opened up. Now I'm in some kind of... cow dimension. This is not in any lore I've read."*

**Score: 5/5 (north-star surface).** The chronicle voice is uniformly excellent and is the literal benchmark referenced in CONTEXT.md. Cormac-McCarthy-adjacent terseness, frank, awe-soaked. Some calls (`main.py:1815` — `"Stepped on a {trap_type.replace('_',' ')} trap. Should have watched..."`) use string interpolation that produces slightly generic results ("Stepped on a dart trap..."), but the wrapper voice still reads.

**Drift notes:** A handful of fully procedural chronicle entries (`game_encounters.py:902,911` flavor verbs like `"Ran into {name}. A brief exchange in the dark."`) are still in voice but blander than the hand-written ones. The randomized template approach is a tradeoff.

---

## Surface 2: Combat log via `add_message()` — player attacks

**File/range:** `src/game_combat.py` ~1100–1330, `src/combat.py` (helpers)

**Sample quotes:**
- `game_combat.py:1300` — *"CRITICAL! Chain x{chain}! You strike the {monster.name} for {damage} damage!"*
- `game_combat.py:1302` — *"Chain x{chain}! You strike the {monster.name} for {damage} damage!"*
- `game_combat.py:582` — *"The {monster.name} is slain!"*
- `game_combat.py:312` — *"You hurl the {display} at {monster.name}! ({actual} damage)"*
- `game_combat.py:486` — *"The {display} splashes {monster.name}! It is {label}!"*

**Score: 1/5.** Pure RPG-statblock. Combat happens constantly — by far the **highest-frequency player-facing surface in the game** — and it's the flattest. Compare to chronicle's "Fenrir is bound. Or dead. I'm not sure which." There is no register continuity between combat log and chronicle. The `Chain x{chain}!` prefix is functional; the verb ("strike") is generic; the damage parenthetical is statblock.

**Drift notes:** This is the single largest voice gap in the game. Findings: P2 register flatness, holistic clash with chronicle.

---

## Surface 3: Combat log — monster attacks

**File/range:** `src/monster.py:270-348`

**Sample quotes:**
- `monster.py:279` — *"The {self.name} swings at you and misses!"*
- `monster.py:285` — *"The {self.name} swings at you and misses! (AC {player_ac} deflects)"*
- `monster.py:289` — *"The {self.name} swings wildly in confusion and misses!"*
- `monster.py:293` — *"The {self.name} flails blindly and misses!"*
- `monster.py:297` — *"The {self.name} strikes at your displaced image and misses!"*
- `monster.py:314` — *"The {self.name} hits you with {atk['name'].replace('_', ' ')} for {actual} damage!"*

**Score: 2/5.** Slightly better than player attacks — "swings wildly in confusion" and "flails blindly" do glance at mythic register. But the hit message is pure damage-printout. The `(AC X deflects)` parenthetical is a tooltip leak into the combat log.

---

## Surface 4: `data/hints.json` — Recall Lore content (T1–T5)

**File/range:** `data/hints.json` — 5 tiers, ~108 hints total

**Sample quotes (T1):**
- *"The wise listen before they speak. Your Wisdom shapes how long you have to answer the dungeon's questions — every point of it above the common measure buys you another breath of time."*
- *"Some say the dungeon itself is a kind of program — and all programs have hidden inputs. Not every key on your keyboard does what you'd expect. Try the ones that seem to do nothing."*

**Sample quotes (T3):**
- *"A fire-bringer in a starlit robe, sashed in gold, is said to walk as a hidden character. His endurance is remarkable and his legacy burns eternal."*
- *"In 1976, a game was released that hid a secret word deep underground. Those who found it could bend the rules of the world. The dungeon remembers old games."*

**Sample quotes (T5):**
- *"Murugan's mother gave him a lance that burned with righteous fire. It never missed, and what it struck did not stop burning."*
- *"The oldest verse speaks of endings that are also beginnings. Not all doors require keys. Some require conviction, spoken aloud, in the right place, at the right moment."*

**Score: 5/5.** Exemplary geek-dad mythic register. Tier discipline holds well — T1 hints teach basics, T5 hints reveal deep secrets with appropriate veil. The corpus is dense, well-varied, and uniformly mythic.

**Drift notes:** A few T2 entries are arguably basics-level and could go T1 (e.g., the `?` key hint sits in T1 properly; the polearm-reach hint at T2 is also basics-ish). Within tolerance.

---

## Surface 5: `data/monsters.json` — `lore` fields

**File/range:** ~458 `lore` fields across 24,446 lines

**Sample quotes:**
- *"Floating eyes drift silently through dungeon corridors, their massive unblinking gaze capable of locking a creature in paralytic terror. They have no limbs or mouth, existing solely to observe. Sages believe they are the discarded sensors of some greater, unseen entity."*
- *"Zombies are the crudest form of undead — corpses reanimated by ambient necromantic energy or a careless spell. They shuffle toward the living with single-minded hunger, spreading disease through festering wounds. The disease they carry is believed to originate from the Plane of Rot."*
- *"Wraiths are the spirits of the deeply corrupt, those whose evil was so profound that death could not contain them. They drain life force with a touch, leaving victims pale and weakened. Unlike ghosts, wraiths have no memory of their former lives — only an insatiable hunger for vitality."*

**Score: 5/5.** Encyclopedic geek-dad voice. Each entry locates the monster in myth/legend, hints at mechanics without spoiling them, and reads like an old D&D bestiary written by a thoughtful uncle.

---

## Surface 6: `data/flavor_encounters.json` — ambient NPC scenes

**File/range:** 4080 lines, ~90 encounters across all levels

**Sample quotes:**
- (early) *"A small, wiry woman moves along the wall with a lantern, peering at patches of fungus with a jeweler's loupe. She barely glances at you. 'I'm cataloguing. Don't touch the blue ones, they'll numb your tongue for a week.'"*
- (mid) *"She makes you drink something purple. You feel briefly like you are standing at the bottom of the ocean, then briefly like you are the ocean, then fine, actually."*
- (deep) *"He listens. His face does the complicated thing faces do when time catches up with them all at once. Then he straightens his shoulders. 'I see. Then I have been standing guard over nothing.' A pause. 'No. Not nothing. I have been standing.'"*
- (deep) *"It reaches out with a hand made of light and distance and touches your forehead. For a moment you are not in the dungeon. You are somewhere enormous and cold and breathtaking..."*

**Score: 5/5.** Possibly the single best-written surface in the game. Each NPC has a distinct voice. The tonal range is wide (comic goblin merchants → trapped god fragments → time-displaced soldiers) and uniformly excellent. Emotional weight scales with depth.

---

## Surface 7: `src/npc_encounters.py` — moral encounters (3-option karma)

**File/range:** 30 encounters across 10 level blocks

**Sample quotes:**
- (Lost Girl, level 3-9) *"\"That's my mama's. She gave it to me before she went away. I dropped it when the rats came.\""*
- (Dying Monk) *"He weeps as he eats, making the sign of the cross over and over. He cannot speak, but he grips your hand with both of his and will not let go for a long time."*
- (Rat-Catcher) *"\"My daughter's name is Lena,\" she says quietly. \"In case you ever develop a conscience.\""*
- (Lost Soldier-out-of-time, level 91-98) — *"He nods. He understands. He keeps crawling toward the stairs, one hand over the other, impossibly slow."*

**Score: 5/5.** Pitch-perfect moral weight. Distinct voices per NPC. The "even selfish options are framed as pragmatic necessity" rule (file docstring) holds throughout. Real emotional stakes; never punishes the player textually for choosing wrong — leaves the choice to land of its own weight.

---

## Surface 8: `src/mystery_system.py` — mystery descriptions, reward/fail text

**File/range:** 13 mysteries, lines 16-187

**Sample quotes:**
- (Sphinx) *"A towering stone sphinx fixes you with ancient eyes. 'Answer my riddles or perish.'"*
- (Pandora) *"A sealed obsidian coffer. A warning is etched: 'Do not open.' The keyhole glows red."*
- (Mimir) *"A dark well with runes carved around its rim. The water below holds all wisdom. A price is implied."*
- (Pandora fail_text) — *"You open it 'correctly' -- but nothing is inside. Only gold."*

**Score: 4/5.** Descriptions are appropriately mysterious and mythic. Reward/fail text is mostly good but a few lines edge into mechanical exposition (`"WIS+2, INT+1"` inline in reward_text). The Pandora fail_text is fine prose but its scare-quotes around "correctly" telegraph that the player did it wrong intentionally — a soft spoiler of the `invert_result` mechanic.

The Soul Sphere merchant lore at `mystery_system.py:644` — *"Ancient texts say these vessels were used to bind creature spirits. One wonders what might happen if it were hurled with force..."* — is borderline. The ellipsis-suggestion is technically a hint, but it's almost a direct instruction.

The Oracle's `_HINTS` dict (lines 413-425) is shown to the player when they succeed at the Oracle mystery. Most are appropriately cryptic ("Some wait long enough to perceive all things." for Odin), but a few are too explicit ("She wove and unwove, ever patient. Armor is her art." practically names the equip/unequip-armor mechanic for Penelope).

---

## Surface 9: `src/welcome_screen.py` — secret-build greetings and intro

**File/range:** `SECRET_BUILDS` dict ~lines 34-255

**Sample quotes:**
- *"Diogenes enters the dungeon. He needs nothing. He wants nothing. He is still going to die."*
- *"Achilles charges in. His heel tingles ominously."*
- *"Nietzsche stares into the dungeon. The dungeon stares back."*
- *"Dad has arrived. Everything will be fine."*
- *"The Witcher unsheathes his silver blade. Wind's howling."*

**Score: 5/5.** Each greeting is a punchline-as-character-portrait. Geek-dad voice at its tightest. Reads like a Discworld chapter heading.

---

## Surface 10: Story popups — entrance + boss + endings

**File/range:** `src/main.py:3340-3497` (`_STORY_CONTENT`)

**Sample quotes:**
- (dungeon_entrance) *"Your village of Amber is dying... The Philosopher's Stone... Descend. Claim the Stone. Return it to the light. The people who love you are counting on you."*
- (boss_abaddon) *"Abaddon is named in Revelation as the angel of the bottomless pit -- the Destroyer, king of the locust army that rises at the fifth trumpet."*
- (exit_with_stone) *"You are a Philosopher in the truest sense: one who loves wisdom enough to seek it at the cost of everything, and wise enough to bring it home. Well done."*
- (exit_without_stone) *"You ran. Not from monsters. Not from darkness. Not even from death. You ran from the people who needed you most."*

**Score: 5/5.** Pitch-perfect mythic register. Real-world cultural literacy laced into every entry. The exit_without_stone text is a master class in moral seriousness without contempt — it states the consequence rather than name-calling the player.

---

## Surface 11: `src/status_effects.py` — `_EXPIRE_MSGS` and per-turn DOT messages

**File/range:** `status_effects.py:222-272` (_EXPIRE_MSGS), 318-368 (per-turn DOT)

**Sample quotes:**
- (expire) *"Your vision returns!"*
- (expire) *"Your mind sharpens. Confusion gone."*
- (expire) *"You wrench free!"*
- (DOT) *"The poison burns through you!"*
- (DOT) *"You feel yourself stiffening..."* (petrify warning)
- (DOT) *"Your limbs are rigid -- death is moments away!"* (petrify warning)
- (DOT) *"The doom curse gnaws at your life force!"*

**Score: 3/5.** Functional with occasional bright spots. The petrify progression ("...stiffening" → "...skin is hardening into stone" → "...limbs are rigid -- death is moments away") is excellent staged messaging. Most expire messages are dry-functional ("Your telepathy fades.", "Your danger sense fades."). The poison/bleeding/burning DOT lines are appropriately visceral ("burns through you", "You are bleeding!") but vary in register.

**Drift notes:** Heavy contrast with chronicle's body-aware language. Status messages could carry far more mythic weight without becoming purple.

---

## Surface 12: `src/quirk_system.py` — unlock messages, TRIGGER, FLAVOR

**File/range:** unlock at line 145-154, `_QUIRK_FLAVOR` 1367-1471, `_QUIRK_TRIGGER` 1260-1364

**Sample quotes:**
- (toast on unlock, `quirk_system.py:145`) — *"TRAIT UNLOCKED: {name}"*
- (chronicle on unlock, `quirk_system.py:148`) — *"Something changed in me. Unlocked a new trait: {name}. I'm becoming something more."*
- (flavor on unlock) — *"What does not kill me makes me immune. -- Mithridates VI"*
- (flavor) — *"They chained me to the rock. I am still here. -- Prometheus"*
- (flavor) — *"One must imagine Sisyphus happy -- and with a better lockpick."*
- (trigger, shown after unlock) — *"You waited 12,960 turns -- half a day of mortal time."*

**Score: 3/5 overall.** Flavor lines (5/5) are mythic and beautiful. The chronicle line (5/5) is in voice. But the **first thing the player sees** on unlock is `"TRAIT UNLOCKED: {name}"` — a SaaS-style caps-lock toast that breaks the mythic moment.

The TRIGGER strings are only shown after unlock (verified at `quirk_system.py:133`), so their explanatory tone ("You waited 12,960 turns...") is acceptable — they're an after-the-fact reveal of "how you got it."

---

## Surface 13: Item `lore` fields

**File/range:** `data/items/*.json` (potion, scroll, wand, armor, weapon, accessory, artifact, etc.) + inline lore (e.g., `main.py:1440` Flux Capacitor)

**Sample quotes:**
- (potion of healing) *"Brewed from cave moss and blessed spring water by wandering hedge-witches, this potion knits torn flesh with a gentle warmth..."*
- (potion of speed) *"Time does not slow — the drinker simply moves faster through it, heartbeat hammering, thoughts sparking. The crash afterward is legendary: users sleep for twelve hours and wake starving."*
- (Gleipnir artifact) *"A ribbon as thin as silk and as light as nothing. It cannot be broken by any force in the Nine Realms. The dwarves of Svartalfheim forged it from six impossible things..."*
- (Bronze Bull Idol) *"...King Minos was given such a bull by Poseidon — and his refusal to sacrifice it at the sacred waters cursed his bloodline forever. The idol still smells faintly of sea-foam."*

**Score: 5/5 for most surfaces.** Item lore is uniformly geek-dad mythic. However: a small set of artifact lore strings explain mechanics directly (see Spoiler Scan below).

---

## Surface 14: Death/Victory screen subtitles

**File/range:** `src/game_render.py:2562-2573` (death subtitle); story popups handle "exit_without_stone" and "exit_with_stone"

**Sample quotes:**
- *"YOU FLED THE DUNGEON"* / *"Your quest ends in cowardice."*
- *"YOU HAVE STARVED"* / *"Hunger claimed you on level {level}."*
- *"YOU HAVE DIED"* / *"Slain on dungeon level {level}."*

**Score: 2/5.** The "starved" and "died" subtitles are restrained statements of fact — appropriate. The "fled" subtitle — *"Your quest ends in cowardice."* — directly contradicts the encouraging-on-failure rule. The story popup that precedes this (`exit_without_stone`) already does the moral work *beautifully* ("You ran. Not from monsters. Not from darkness... from the people who needed you most"). Following that earned seriousness with the cheap "cowardice" label punches down on the player.

---

## Surface 15: Default welcome messages / hint messages

**File/range:** `src/main.py:271-272` (default greeting), `main.py:1100-1119` (special room enter messages)

**Sample quotes:**
- *"Welcome, {self.player_name}!"*
- *"Find the Philosopher's Stone and escape!"*
- *"You enter a treasure vault -- riches gleam in the darkness!"*
- *"Welcome to the treasure zoo! Sleeping creatures surround you!"*

**Score: 2/5.** When the player picks a known build, the greeting is chronicle-voice ("Diogenes enters the dungeon..."); when they don't, they get "Welcome, Brandon!" — a complete tonal collapse to dial-up-era videogame default. The follow-up imperative ("Find the Philosopher's Stone and escape!") with its exclamation point reads like a tooltip, not the narration that just told you Amber is dying.

Special-room enter messages mostly work — "An aura of ancient authority radiates from a throne" is in voice. But "Welcome to the treasure zoo!" with its exclamation point is RPG-pastiche.

---

## Surface 16: UI prompts/menu labels (`ui.py`, `fantasy_ui.py`)

**File/range:** primarily sidebar formatting

**Sample quotes:**
- *"AC     {ac}"*, *"Level  {dungeon_level}"*, *"Turns  {turn_count}"*, *"Gold   {gold:,}"*

**Score: N/A (functional).** Sidebar/menu labels are deliberately terse. No drift, no expectation of voice — these are HUD.

---

## SECRET-SPOILAGE SCAN

Per CONTEXT.md §4: *Hidden systems are HINTED at by Recall Lore, never directly explained. Direct spoilers in player-facing text are P1.*

The following surfaces **explicitly explain a mechanic** rather than hinting at it:

### CONFIRMED P1 SPOILERS

1. **Flux Capacitor `lore`** — `src/main.py:1440-1441`
   > *"A device of impossible origin. Its single charge can freeze time itself for 10 turns. Use it wisely -- there are no second chances."*

   Explicitly states the time-stop mechanic, charge count, and duration. The artifact is `identified: true` at spawn — the player sees this lore as soon as they pick it up. The matching `add_message` at `game_magic.py:165` (*"The Flux Capacitor ignites! Time freezes around you -- 10 turns!"*) re-confirms.

2. **Palladium `lore`** — `data/items/artifact.json:297`
   > *"A small wooden statue of Athena... It reveals the path forward: while carried, the stairs on every floor glow faintly in the bearer's mind, visible even through walls and darkness."*

   Spells out the `stair_reveal` mechanic verbatim, including the visual rendering ("glow faintly"). Becomes visible on identification.

3. **Tablet of Destinies `lore`** — `data/items/artifact.json:311`
   > *"...The Tablet allows its bearer to reject fate once per floor — when a question is answered wrongly, the Tablet cracks and offers a different question. A second chance, drawn from the well of all possible futures."*

   Verbatim mechanical description: "once per floor", "answered wrongly", "different question." Shown on identification.

4. **Black Stone of Sir Gareth `lore`** — `data/items/artifact.json:270`
   > *"...It weighs twenty pounds and cannot be put down — the curse binds it to whoever takes it freely. Only a scroll of Remove Curse can break the bond."*

   Explicit weight, explicit "cannot be put down" rule, explicit cure path.

### BORDERLINE / CONSIDER-DOWNGRADING

5. **Soul Sphere merchant lore** — `src/mystery_system.py:644-646`
   > *"A sphere of crimson and ivory that hums with trapped souls. Ancient texts say these vessels were used to bind creature spirits. One wonders what might happen if it were hurled with force..."*

   The ellipsis-and-suggestion ("hurled with force...") is technically hinting, but reads as direct instruction. Compare to a fully veiled version ("legends say these spheres do not stay closed when struck"). Subtle but the *throw it* mechanic is a hidden ritual.

6. **Ariadne's Thread `lore`** — `data/items/artifact.json:36`
   > *"...It reveals all hidden paths."*

   Single-sentence mechanic reveal. Slightly softened by the myth wrapper but still a direct statement. Lower-severity than the others because the mechanic is well-foreshadowed in hints (T5: *"Theseus survived the labyrinth because Ariadne gave him a thread..."*).

7. **Pandora's Coffer fail_text** — `src/mystery_system.py:42`
   > *"You open it 'correctly' -- but nothing is inside. Only gold."*

   Scare-quotes around "correctly" telegraph that the player did the wrong-correct thing. Combined with `invert_result: True`, this softly spoils the inverted-quiz mechanic.

8. **Oracle's quirk hints** — `src/mystery_system.py:413-425`
   Most are properly cryptic. A handful name the mechanic too directly:
   - `'penelope': "She wove and unwove, ever patient. Armor is her art."` (the "armor is her art" reduces it to the equip/unequip trigger)
   - `'merlin':   "Wands were used before they were understood."` (close to "zap unidentified wands")
   - `'tiresias': "The blind prophet answered correctly while he could not see."` (essentially names the trigger condition)

### CLEAN (verified)

- All TIER-graduated `data/hints.json` entries are appropriately veiled.
- All flavor encounter outcomes are hints, not mechanical exposition.
- Boss story popups describe myth, not mechanics.
- NPC encounter outcomes describe consequence-in-fiction, not mechanical bookkeeping.

---

## LORE-COVERAGE GAP ANALYSIS

For each major strategic system or hidden mechanic in the game (drawn from `CONTEXT.md` §3, §4), I checked whether `data/hints.json` has appropriately tiered coverage. The hints corpus is dense and well-tiered.

| System / Mechanic | Lore coverage? | Tier | Notes |
|---|---|---|---|
| Wisdom → quiz timer | YES | T1 | *"every point of it above the common measure buys you another breath of time"* |
| Hunger system | YES | T1 | *"When the hunger gnaws deep enough, it begins to take something more than comfort."* |
| Scrolls vs spellbooks | YES | T1 | *"Scrolls crumble after a single reading... a spellbook is a patient teacher"* |
| Cooking basics | YES | T1 | *"a wise traveler learns to cook early"* |
| Stair-rest healing | YES | T2 | *"The staircase landing is a place of quiet power..."* |
| Altars (boon/curse) | YES | T2 | *"Strange altars sometimes appear in the dungeon..."* |
| Backtick debug terminal | YES | T2 | *"a hidden terminal that accepts a spoken word. The key to reach it... sits beside the number 1"* |
| Recall Lore loop | PARTIAL | (meta) | The mechanic is self-revealing once tried; hints don't explicitly explain how the cooldown scales with chain. |
| Abyssal Shimmer / secret victory | YES | T2, T4 | *"Some places in the dungeon shimmer with energy that doesn't belong..."*, T4 *"Ancient theology speaks of a second death..."* |
| Boss myths (Minotaur, Gorgon, etc.) | YES | T4 | All 5 named bosses have lore entries with strategy hints. |
| Gleipnir / 6 impossible things | YES | T4 | *"The dwarves of Svartalfheim forged Gleipnir from six things that do not exist..."* |
| Dwarven Forge | YES | T4 | *"A forge of dwarven make has been discovered..."* |
| Sphinx / mystery altars | YES | T3, T4 | *"A lone sphinx in the depths poses riddles..."*, *"A sealed tribunal near the thirtieth depth..."* |
| XYZZY / Crowther & Woods | YES | T3, T5 | *"In 1976, a game was released that hid a secret word..."* |
| Pandora's Box | YES | T3 | *"Pandora's box is said to lie somewhere..."* |
| Bronze Bull (fountain trigger) | YES | T3 | *"A bronze idol of a bull has been found... King Minos offended Poseidon..."* |
| Secret-character builds (philosophers) | YES | T3-T5 | Multiple entries for fire-bringer (Prometheus), bald monk (Buddha/Diogenes), hooded wanderer (Odysseus), forest-green philosopher (Pythagoras), winged messenger (Hermes), white-haired hunter (Geralt), young woman with elder blood (Ciri), red-and-white cap (Ash Ketchum). |
| Death Bane / sixth boss reward | YES | T4 | *"Ancient theology speaks of a second death..."* |
| Quirks (Mithridates, Buddha, Prometheus, etc.) | PARTIAL | T3-T5 | Most major quirks have at least one hint that names the figure and gestures at the trigger, but the **specific trigger condition** is intentionally not in hints — discoverable only via the Oracle reveal or experimentation. This is intentional non-coverage. |
| Power quirks (philosophers_stone, atlas_burden, zeus_bolt, etc.) | NO | — | **GAP**: Active power quirks have no hint coverage at any tier. A player who unlocks Zeus Bolt or Atlas Burden has no in-game lore that even mentions these as a concept. |
| Pet / Soul Sphere capture mechanic | PARTIAL | (item lore) | The Soul Sphere lore at `mystery_system.py:644` hints (too directly — see spoiler scan). No `data/hints.json` entry exists. |
| Karma system | PARTIAL | (chronicle only) | The chronicle entries at `game_encounters.py:732,734` describe the feeling of karma = 10 and karma = -10. No hints.json entry explains there is a moral track at all. **GAP**: a T3 or T4 hint that gestures at "the dungeon weighs the deeds of those who walk it" would close this. |
| Container alerting (sessile monsters) | NO | — | **GAP**: the rule that lockpicking alerts adjacent sessile monsters (per `CONTEXT.md`) has no lore coverage. |
| Bones / ghost system | PARTIAL | (in-game message) | Only the in-game "you sense a restless presence" message exists; no T2 or T3 hint discusses how prior runs leave ghosts behind. |
| Fafnir's blood / throw-over reforge | PARTIAL | T5 | *"Sigurd slew Fafnir by digging beneath him... a god had to intervene. Odin's methods are not always what you'd expect."* — properly veiled; gap is in the dragon-blood reveal flavor, but that's a player-discovery surface, not hint surface. |
| Cow level | NO | — | The cow level is a NetHack-style hidden joke. No lore coverage at any tier. Borderline — the discovery moment depends on accident, but a single mischievous T2-T3 hint about "what happens when adventurers refuse to leave well enough alone" would be in spirit. |

**Summary of meaningful gaps:**
1. **Power quirks** — zero coverage in `data/hints.json` for a whole class of unlockables.
2. **Karma system** — no hint that the dungeon is morally tracking the player.
3. **Container alert mechanic** — no hint that breaking locks attracts attention.
4. **Pet/Soul Sphere mechanic** — only spoilery item-lore coverage; no veiled hint.
5. **Cow level** — no hint (defensible as full secret).
6. **Bones / ghosts** — minimal coverage beyond the in-game encounter message.

These are findings-grade gaps. Most other major systems are well-covered or appropriately fully-hidden.
