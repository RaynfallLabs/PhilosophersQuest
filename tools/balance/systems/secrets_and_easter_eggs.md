# Hidden Systems, Secrets, and Easter Eggs — Reference

This is the spoiler-bible for Philosopher's Quest. **Hidden systems are FEATURES, not bugs.**
Every secret here is intentional. Many are richly hinted in `data/hints.json` and rewarded with permanent power, rare items, or unique quest endings.

---

## Hierarchy of secrets

| Tier | Examples | Discovery cost |
|---|---|---|
| **easy** | XYZZY terminal (T2 hint, T3 hint, T5 hint), Magic Carrot → Unicorn, Mystery altars, Cow level (poke 10x) | Read a few lore hints, experiment |
| **moderate** | Bronze Bull → Ariadne, Eye of the Graeae → Athena's Aegis, Broken Gram → Odin shrine (normal path), 7 Seal Demons, Last Judgment altar, blindfold vs Medusa, Aegis-mirror vs Medusa | Mid-tier lore hints, careful reading of T4 |
| **mega** | Vidar's Sandal (10 leather scraps over 10 floors → L79 altar), Gleipnir forge (6 impossible ingredients on L62-77 → L76 dwarven forge), **Gram REFORGE** (throw broken_gram OVER Odin's altar — not drop), Tablet of Destinies (quiz-reroll artifact), Palladium (stair-reveal) | Deep lore reading, lateral thinking |
| **invocation** | Stone + Tablet + Shimmer + Lake-of-Fire scroll → **KILL DEATH** (sixth boss reward) | T5 lore + every other secret combined |
| **easter egg / nod** | Charmander Stuffie, Dreamspun Sketchbook, Rand's Heart, Flux Capacitor (McFly), Dad / "God"-typo prompt, Ash Williams, Geralt, Ciri, Ash Ketchum builds | Type the right name |

---

# 1. Hidden levels

## 1.1 The Secret Cow Level — "Moo Moo Farm" (L999)

**File evidence:**
- Constant + map: `src/boss_levels.py:16` (`COW_LEVEL = 999`), `src/boss_levels.py:533-615` (`_level_999_moo_moo_farm`).
- Cow NPC spawn: `src/game_encounters.py:38-75` (`_maybe_spawn_cow`).
- Cow dialog input: `src/game_input.py:512-554` (`_cow_encounter_input`).
- Trigger: `src/game_input.py:541-545` (poke 10 times to enter).
- Cow lore msg: `src/game_render.py:763` ("large brown eyes, chewing slowly. This is deeply unusual. Moo.")
- Run-state: `src/main.py:123-129` (`_cow_level: int = _lore_rng.randint(30, 39)` — cow appears on a random floor in 30-39).
- Save: `src/main.py:352-354`, `src/save_system.py:66-68`.

**Hinted by:** No direct hint trail. T3 hint about "rare creatures that appear in the dungeon only once" (`data/hints.json:61`) is the closest. **Discoverability: blind. Player will only find this by poking a cow repeatedly.**

**Trigger:** Bump-interact a Cow NPC (sessile, allied, symbol `C`) that spawns once per run on a randomly-chosen floor in 30-39. Dialog offers three options:
1. Feed an Ingredient — flavor message, no reward.
2. Walk away — flavor message.
3. **Poke (key `3`)** — counter increments. After **10 pokes** the floor opens (`game_input.py:544`).

**Mechanic:** Player teleported to `COW_LEVEL`. The arena is a single 35×20 pasture with **40-50 Hell Bovines** plus the **Cow King** (HP ~550, THAC0 2, boss) in a walled pen. Atmosphere messages: "The air smells of hay and brimstone." / "You hear an ominous chorus of mooing." / "Welcome to the Moo Moo Farm." (`boss_levels.py:609-613`).

**Exit:** Step onto the `STAIRS_DOWN` portal — returns to `_cow_return_level`. Sets `_cow_level_done=True`, can't re-enter.

**Reward:** Whatever bovines drop (corpses are good ingredient sources at mid-floors) plus the Cow King's drops. The chronicle is the real reward: *"I poked a cow too many times. The floor opened up. Now I'm in some kind of... cow dimension."* (`game_encounters.py:90`).

**Cross-system:** Touches PROGRESSION (secret floor bypass) and LORE (Diablo II reference).

---

## 1.2 Hidden chambers (per-floor, behind secret doors)

**File evidence:** `src/dungeon.py:124, 310-339, 949+` (`_place_hidden_chambers`); `src/level_manager.py:62, 232+` (`_populate_hidden_chambers`).

**Hinted by:** `hints.json` T1: *"Try the ones [keys] that seem to do nothing"* (s key/search), T2: *"Some places in the dungeon shimmer with energy that doesn't belong to this world."*

**Mechanic:** Each regular floor may carve a hidden chamber adjacent to a corridor, connected by a **SECRET_DOOR** (tile constant `5` — looks like WALL until searched or bumped, `dungeon.py:30`). Themes drive what spawns:
- `rat_nest` — rats/rodents
- (other themes — see `level_manager.py:238-256`)

**Trigger:** Bump the SECRET_DOOR tile, or have `searching` status active (Ahasverus quirk, Cauldron mystery reward, Cerberus quirk's "warning", and Trinkets of Searching from Recall-Lore mention).

**Discoverability:** PER stat passively detects nearby secret doors via `_do_passive_search` (`main.py:1586`).

---

## 1.3 Vaults (4×4 sealed treasure rooms)

**File evidence:** `src/dungeon.py:618-694` (`_try_place_vault`). Surrounded by walls with optional locked door candidates.

Not strictly "hidden" — they appear on the map but are sealed. They are NetHack-style.

---

# 2. Hidden boss-quest paths (MEGA SECRETS)

These are quest LAYERS on top of the core boss quests. The basic kill is always possible; these layers reward investigation.

## 2.1 Asterion (L20 Minotaur) — Ariadne's Thread

**Layer 0 (gate):** Reach L20.
**Layer 1 (defang):** Drop Bronze Bull Idol into a fountain → activates Ariadne's shrine → grants Ariadne's Thread → reveals every hidden passage, prevents Asterion's wall-phasing escapes.

**File evidence:**
- Bronze Bull spawns guaranteed on a pre-Asterion floor; trigger in `src/main.py:3730-3734` (`_drop_item` → `_activate_ariadne_shrine`).
- Shrine activation: `src/game_divine.py:362-385` (`_activate_ariadne_shrine`).
- The shrine door is the key — opens a hidden passage to Ariadne's Thread.

**Hinted by:**
- T5: *"Theseus survived the labyrinth because Ariadne gave him a thread. In the old stories, it all began with a sacrifice at sacred waters — and ended with a gift that revealed every hidden passage in the maze."* (hints.json:158)
- T3: *"A bronze idol of a bull has been found in the floors before the labyrinth. King Minos offended Poseidon by refusing to sacrifice such a bull. Sacred waters remember old debts."* (hints.json:107)

**Reward:** Ariadne's Thread artifact — see `data/items/artifact.json` `ariadnes_thread`. (NOTE: the audit elsewhere has flagged that the Thread leak-affects ancient vampires too via `can_phase_walls` — a known gap.)

---

## 2.2 Medusa (L40 Gorgon) — TWO independent counter-paths

The Medusa gaze petrifies for 8 turns (`monster.py:209-224`). Two ways around it:

### Path A — Mirror Shield (Perseus path)

**Trigger:** Equip `aegis_of_athena` or `greater_aegis_of_athena` as your shield.
**Mechanic:** `monster.py:215-219` — Medusa's gaze REFLECTS, petrifying HER for 1 turn instead.
**File evidence:** `monster.py:216` `getattr(player.shield, 'id', '') in ('aegis_of_athena', 'greater_aegis_of_athena')`.

**Hinted by:**
- T5: *"Perseus defeated the Gorgon with a mirror and a blindfold. The Grey Sisters' Eye was the price he paid for divine aid."* (hints.json:159)
- T5: *"Perseus held his shield as a mirror. Turning an enemy's power against them is a feat the dungeon rewards more than once."* (hints.json:189)

**How to acquire Aegis:**
1. Pick up **Eye of the Graeae** (guaranteed spawn on L29, `dungeon.py:1505-1520`).
2. Drop it on any altar → triggers `_activate_athena_shrine` (`game_divine.py:387-409`).
3. The shrine room opens; the **Aegis of Athena** is inside (`dungeon.py:1770-1784`).
4. The Aegis is `min_level: 9999` (`data/items/shield.json`) — NEVER spawns as random loot. The Athena shrine is the ONLY way to get it.

### Path B — Blindfold

**Trigger:** Equip the `blindfold` armor in the head slot.
**Mechanic:** `player.py:285-290` — `get_sight_radius()` returns 0 if blindfold equipped. `monster.py:200-201, 213-214` — Medusa's gaze checks sight radius; with 0, gaze does nothing. Player still cannot SEE (the standard cost of blindness).
**File evidence:** `data/items/armor.json:3699` `blindfold` (min_level varies, `floorSpawnWeight: 30-38 = 8, 39-100 = 3`).

**Hinted by:**
- T4: *"What you cannot see cannot harm you — or so the legend goes. Blindness is usually a curse, but against certain foes it may be a desperate salvation."* (hints.json:106)
- The Tiresias quirk (`tiresias` — 25 correct answers while blinded → PER+2) shadows this path mechanically.

**Cross-system:** Touches **BOSS QUEST** and **PROGRESSION** (the blindfold path is fascinatingly cheap; the Aegis path requires the Eye + altar + shrine ritual).

---

## 2.3 Fafnir (L60 Dragon) — Broken Gram → Odin → "Reforge by Throwing"

This is a TWO-PATH secret:

### Path A (moderate) — Drop the Broken Blade

**Trigger:** Pick up `broken_gram` (guaranteed L48 spawn, `dungeon.py:1527-1536`). Stand on Odin's Altar (guaranteed L53, `dungeon.py:1538-1540` `_create_odin_shrine`). DROP the blade onto the altar.
**Mechanic:** `game_divine.py:411-462` — non-reforge path: blade dissolves, Odin opens the shrine door, which contains the SHOVEL ("Dig, as Sigurd dug").

**Hinted by:**
- T5: *"Sigurd slew Fafnir by digging beneath him and striking upward through the soft belly. Before the killing blow, he carried a broken blade — and before the blade was whole, a god had to intervene. Odin's methods are not always what you'd expect."* (hints.json:160)

**Reward:** The shovel, which can dig pits beneath Fafnir for the "soft-belly" strike (combat.py contains `can_dig` weapon flag).

### Path B (MEGA SECRET) — THROW the Broken Blade OVER the altar

**Trigger:** Stand on one side of Odin's altar. Throw the `broken_gram` weapon at a target on the OTHER side. The thrown path must cross the altar tile.
**Mechanic:** `src/game_combat.py:286-303` — `_throw_weapon` detects altar-crossing throw of `broken_gram`. Calls `_activate_odin_shrine(weapon, reforge=True)`.
**File evidence:** `game_divine.py:422-443`. Result: lightning strikes the altar, Odin proclaims the player worthy ("You have thrown your weapon over the enemy, as I threw Gungnir. I name you worthy."), **Gram appears reforged on the altar** — a tier-5 adamantine blade with `ignore_resistances: true`, 9-stage chain multipliers maxing at **9× damage**, and 24 base damage. (`data/items/weapon.json` `gram`.)

**Hinted by:**
- T3: *"Gungnir, when its wielder fells an enemy, something ancient and still ripples outward through the space around the corpse."* (hints.json:173 — Odin's spear) — this is the GUNGNIR throw archetype the player must imitate.
- The Lyre/Orpheus chronicle pattern and Fafnir's blood drop (`game_combat.py:617` — drops "fafnir_blood" potion with the reforge hint) point at it.
- The chronicle entry `"I threw the broken blade over the altar like a madman. Lightning struck."` (`game_divine.py:459`) confirms the throw-over mechanic on success.

**Discoverability assessment:** The throw-over mechanic is **not directly hinted** in any T1-T5 lore. Only the Fafnir's blood drop and the Gungnir hint nudge at it. **A serious gap in discovery scaffolding** for the dungeon's most spectacular reward path.

**Cross-system:** Touches **DIVINE** (Odin shrine), **BOSS QUEST** (Fafnir kill route), **PROGRESSION** (Gram is one of two endgame "ignore_resistance" weapons).

---

## 2.4 Fenrir (L80 Wolf) — TWO mega-secret paths

### Path A — Gleipnir Forge (build the unbreakable ribbon)

**Trigger:** Collect all six Gleipnir components and drop them on the Dwarven Forge tile.
**Six components, one per floor:**
| Floor | ID | Name | Theme/Guard |
|---|---|---|---|
| 62 | `cats_footstep` | Sound of a Cat's Footstep | Surrounded by alarm traps (`dungeon.py:2058-2070`) |
| 65 | `womans_beard` | Roots of a Woman's Beard | Behind a SECRET_DOOR alcove (`2071-2089`) |
| 68 | `mountain_root` | Root of a Mountain | Surrounded by lava (`2090-2098`) |
| 71 | `fish_breath` | Breath of a Fish | Surrounded by water (`2099-2107`) |
| 74 | `bird_spittle` | Spittle of a Bird | Sits ON an altar tile (`2108-2110`) |
| 77 | `bear_sinew` | Sinew of a Bear's Sensitivity | Adjacent bear-traps (`2111-2120`) |

Each is a guaranteed single spawn (`dungeon.py:1558-1570`).

**Trigger:** Step on Dwarven Forge tile (guaranteed L76, `dungeon.py:1572-1574` `_create_dwarven_forge`). Drop all six components on it.
**Mechanic:** `game_divine.py:472-497` — `_check_gleipnir_forge`. The six dissolve and **Gleipnir** materializes (artifact, `min_level: 9999`).

**Hinted by:**
- T4: *"The dwarves of Svartalfheim forged Gleipnir from six things that do not exist. Adventurers have found strange objects in unusual rooms between the dragon's lair and the wolf's den — things that by all rights should not be real."* (hints.json:101)
- T4: *"A forge of dwarven make has been discovered in the deep floors before Fenrir's hall."* (hints.json:102)
- T3: *"Ancient Greek smiths spoke of an unfinished hammer buried deep. Where thunder echoes, dwarven work awaits."* (hints.json:70 — Mjolnir, also at the forge)

**Reward:** Gleipnir grants the **"Bind Odinkiller"** active power (`game_menus.py:665-672, 980-1008`):
- Resets Fenrir's rage-stacks (his attacks escalate per turn — `monster.py:_fenrir_multi_attack`).
- Paralyzes Fenrir for 2 turns.
- COST: -1 permanent stat (rotating STR→DEX→CON cycle, `game_menus.py:996-1007`).

### Path B — Vidar's Sandal (instant kill)

**Trigger:** Pick up TEN leather scraps from levels [5, 13, 21, 28, 35, 42, 50, 58, 66, 73] (`dungeon.py:1542-1556` — each guaranteed). Stand on Vidar's Altar (guaranteed L79, `dungeon.py:1576-1578`, `_create_vidar_altar`). Drop scraps one by one on the altar.
**Mechanic:** `game_divine.py:499-521` — `_check_vidar_altar`. When 10 are present, they fuse into Vidar's Sandal.
**Combat trigger:** During the Fenrir fight, when chain >= 1 AND Vidar's Sandal is in inventory → **instant kill** (`game_combat.py:1292-1311`):
> "You plant Vidar's Sandal against Fenrir's lower jaw!"
> "With impossible strength, you wrench the great wolf's mouth apart!"
> "FENRIR, THE WORLD-WOLF, IS TORN ASUNDER!"

**Hinted by:**
- T5: *"Adventurers sometimes tell of useless scraps of leather they find discarded in corridors. Those who held onto them long enough discovered they were not useless at all."* (hints.json:208)
- The Sandal-vs-Fenrir mechanic itself is not hinted directly — the player must know Norse myth (Vidar killed Fenrir at Ragnarok by stomping his jaw open).

**Discoverability assessment:** The leather scraps are described as worthless in their item lore ("Useless scrap left over from leather-working", `dungeon.py:1551`) — the T5 hint is the ONLY trail for a player not steeped in Norse myth. Very deep secret.

**Cross-system:** Touches **DIVINE** (altar), **BOSS QUEST** (alternative to combat), **PROGRESSION** (mega-secret reward path).

---

## 2.5 Abaddon (L100 Destroyer) — FOUR LAYERS (Layers 0-3)

### Layer 0 — The Seven Seals (gate, REQUIRED)

**File evidence:** `level_manager.py:152-202` (`_try_spawn_seal_demon`), `game_combat.py:619-630` (seal tracking), `main.py:1210-1216` (L99 stair gate).

Seven seal demons spawn guaranteed on floors **83, 85, 87, 89, 91, 93, 97**:
- `seal_demon_wrath`, `seal_demon_pestilence`, `seal_demon_famine`, `seal_demon_war`, `seal_demon_death`, `seal_demon_earthquake`, `seal_demon_silence`.

Killing each adds a seal artifact to `seals_broken`. Player **CANNOT descend from L99 to L100** until all 7 broken.

**Hinted by:**
- T5: *"Abaddon resists nearly everything the dungeon can throw at him. Those who survived speak of faith as the only weapon that drew blood — a blade that was earned, not found."* (hints.json:157)
- T4: *"Theologians call certain ground 'thresholds' — places where the boundary between life and death grows weak. Scripture marks these places."* (hints.json:92)

### Layer 1 — Altar Resist-Strip (combat, FUNCTIONALLY REQUIRED without Sword)

**File evidence:** `game_divine.py:749-777`. The L100 arena has **SIX altars** in a hex ring (`boss_levels.py:469-478`).

**Trigger:** Pray (`\` key) while standing on an L100 altar.
**Mechanic:** Each altar is single-use (`_l100_altars_used: set`). Chain score × 2 = turns of Abaddon's resistance-strip. Abaddon normally has `poison, cold, fire, slash, blunt` resistances; for the window, ALL are removed.

**Hinted by:**
- T5: *"Prayer at a sacred altar carries more weight than prayer anywhere else."* (hints.json:156)
- T2: *"Prayer is not merely a comfort for the frightened."* (hints.json:37)

### Layer 2 — Last Judgment / Sword of Michael (max-karma reward)

**File evidence:** `dungeon.py:1580-1582, 2157-2167` (`_create_judgment_altar` on L99), `game_divine.py:684-693` (judgment trigger from `_start_pray`), `game_encounters.py:928-989` (`_resolve_judgment`), `npc_encounters.py` (judge_karma).

**Trigger:** Stand on the Altar of the Last Judgment (L99) and pray.
**Mechanic:** Player's accumulated karma (from 30 moral NPC encounters across the run) is weighed:
- **`sword_and_scales`** outcome: Player gets **Sword of Michael** (45 base damage, 16× max chain, `ignore_resistances`, `abaddon_bonus_damage`) + **Scales of Michael** + `player_title = 'Paladin'`.
- **`scales_granted`**: Scales of Michael only.
- **`abaddon_empowered`** (negative karma): Abaddon gets +50% HP and an extra attack.
- **`locusts_strengthened`** (low karma): Abyssal locust swarms are bigger.

**Hinted by:**
- T5: *"The divine reward the faithful with permanent wisdom. Three boons are available to those who pray at the right altars with the right knowledge — and the gods do not offer them twice."* (hints.json:175)
- T4: *"The knights of old sought the Grail in dungeons far below. The worthy must know the ways of faith before the cup reveals itself."* (hints.json:121)

### Layer 2.5 — Heavenly Host (active power)

**Trigger:** Use `V` menu → **Summon the Heavenly Host** (requires Scales of Michael in inventory).
**Mechanic:** `game_menus.py:697-705, 1010-1016`, `main.py:3079-3094`. While `heavenly_host_active=True`, every locust Abaddon summons triggers a counter-spawn of a `heavenly_angel` near the player.

**Hinted by:** T5 (`Scales of Michael` lore line — *"For every locust of the Abyss, an angel descends."*) — but only AFTER acquiring the artifact.

### Layer 3 — KILL DEATH (INVOCATION TIER, sixth boss reward)

**Trigger sequence:**
1. **Defeat Abaddon at L100** → drops Philosopher's Stone.
2. **Carry the Stone**, climb. `death_pursues = True` spawns the `DeathMonster` (`main.py:1240-1265`).
3. Locate the **Abyssal Shimmer** (random floor 1-20, `main.py:117`, item id `abyssal_shimmer`).
4. Locate the **Tablet of Second Death** (random floor 80-99, `main.py:120`, item id `tablet_of_second_death`).
5. Locate the **Philosopher's Wrench** (random floor 21-49, `main.py:118`, item id `philosophers_wrench`).
6. Locate the **Scroll of the Lake of Fire** (random floor 50-79, `main.py:119`, item id `scroll_lake_of_fire`).
7. **Use the Wrench** (`_use_philosophers_wrench`, `main.py:1318-1344`) to fuse Stone + Tablet → **Complete Tablet of Second Death**.
8. **Drop the Complete Tablet on the Abyssal Shimmer** (`main.py:3713-3728`) → Shimmer activates.
9. **Lead Death onto the Shimmer**, then **read the Scroll of the Lake of Fire** while Death is standing on it.
10. **Result** (`game_magic.py:1953-1979` → `main.py:1374-1407` `_trigger_abyss`):
    - Quote: *"Then Death and Hades were thrown into the lake of fire."*
    - Death is consumed, `death_pursues=False`.
    - **Scroll of Death's Bane** (`scroll_deaths_bane`, sixth boss reward) materializes.
    - Chronicle: *"I killed Death. The lake of fire opened beneath it and swallowed it whole. The silence afterwards was the loudest thing I've ever heard."*
    - The Stone is consumed.
    - This is the maximum-difficulty ending; the reward code given is the most prestigious.

**Hinted by:**
- T2: *"Some places in the dungeon shimmer with energy that doesn't belong to this world. The veil between realms is thin there."* (hints.json:44)
- T4: *"Ancient theology speaks of a second death — one the oldest texts say even Death himself cannot escape. Revelation may be the beginning of wisdom..."* (hints.json:113)
- T3: *"An old alchemist's journal mentions a tool that joins rather than separates. 'The Wrench completes what is broken,' he wrote. 'Stone into Tablet, purpose into form.'"* (hints.json:91)
- T4: *"Some things in this dungeon were broken on purpose. A tool exists that can undo that separation."* (hints.json:152)
- T5: *"The oldest verse speaks of endings that are also beginnings. Not all doors require keys. Some require conviction, spoken aloud, in the right place, at the right moment."* (hints.json:209)
- The Shimmer's on-step message reveals "Revelation 20:14" (`main.py:1156`).

**Cross-system:** Touches **EVERY** system: BOSS QUEST, DIVINE (Death), LORE (4 items + 1 scroll), PROGRESSION (must climb back up with Stone + survive Death + assemble the kit).

---

# 3. Hidden items / artifacts

## 3.1 Spawned by lore-quest mechanic (random floor per run)

| Item | Spawn range | Code | Notes |
|---|---|---|---|
| **Abyssal Shimmer** (terrain) | L1-20 | `items.py:464-478` | Tile-like, weight 9999, has `activated` flag |
| **Philosopher's Wrench** | L21-49 | `items.py:525-549` | Wand — `effect: 'philosophers_wrench'`; combines Stone + Tablet |
| **Scroll of the Lake of Fire** | L50-79 | `items.py:501-522`; `single_copy: True` (re-spawns if read once and failed) | Effect `lake_of_fire`; kills Death on Shimmer |
| **Tablet of Second Death** | L80-99 | `items.py:481-498` | Artifact; unidentified name "plain tablet" |

## 3.2 Quest-chain items (guaranteed spawns)

| Item | Spawn | Purpose |
|---|---|---|
| Bronze Bull Idol | Pre-L20 floor | Ariadne quest (drop in fountain) |
| Eye of the Graeae | L29 guaranteed (`dungeon.py:1507`) | Athena quest (drop on altar) |
| Broken Blade of Gram | L48 guaranteed (`dungeon.py:1527`) | Odin quest |
| Leather Scrap × 10 | L5, 13, 21, 28, 35, 42, 50, 58, 66, 73 | Vidar's Sandal recipe |
| 6 Gleipnir components | L62, 65, 68, 71, 74, 77 | Gleipnir recipe |
| Magic Dungeon Carrot | L1-19 random | Unicorn feed (`game_encounters.py:213-245`) |
| Sword of Michael | L99 reward (Last Judgment) | Holy-fire weapon for Abaddon |
| Scales of Michael | L99 reward (Last Judgment) | Active power "Summon Heavenly Host" |

## 3.3 Mid-tier hidden artifacts

### Tablet of Destinies (`data/items/artifact.json` `tablet_of_destinies`, min_level 70)
- **Effect:** `quiz_reroll: true`. Once per floor, if a quiz question is answered wrongly, the Tablet cracks and offers a different question.
- **File evidence:** `game_combat.py:1250, 1284-1287`; `main.py:2457-2459` (`_has_tablet_of_destinies`); `main.py:460` (resets each floor).
- **Hinted by:** T5 *"A clay tablet from the oldest city in the world once controlled fate itself."* (hints.json:172)

### Palladium (`data/items/artifact.json` `palladium`, min_level 45)
- **Effect:** `stair_reveal: true`. While in inventory, stairs glow on every floor (`main.py:826-827`).
- **Hinted by:** T3 *"A wooden idol once fell from heaven to protect a great city. Those who carried it always knew where the exit was."* (hints.json:77)

### Cursed Lodestone (`data/items/artifact.json` `cursed_lodestone`, min_level 9999)
- **Acquired:** Knight encounter at L11-19, accepting the +1 karma option (`npc_encounters.py:270`).
- **Effect:** Permanent inventory burden — 20 lb of useless cursed weight that cannot be dropped easily (curse).

### Sealed Dispatch (`data/items/artifact.json` `sealed_dispatch`, min_level 9999)
- **Acquired:** A karma encounter offering to "deliver this letter" (`npc_encounters.py:546`).

## 3.4 Build-only / character-only items

| Item | Granted by | Effect |
|---|---|---|
| **Charmander Stuffie** (accessory) | Corwin, Cain builds (`welcome_screen.py:151, 163`) | 50% fire damage reduction passive (`player.py:130-133`); grants "Fire Breath" V-power (`game_menus.py:646-653`) — cone of fire at all visible enemies, 500-turn CD |
| **Dreamspun Sketchbook** (accessory) | Fianna, Fluffs builds (`welcome_screen.py:173, 183`) | Grants "Manifest" V-power (`game_menus.py:655-663`) — sketch a visible creature and bring it to life as a temporary ally (`pet_system.py:333+` `SketchedPet` at 40% monster stats) |
| **Rand's Heart** (amulet) | Robyn build (`welcome_screen.py:202`) | Prevents one death: restores full HP/MP/SP, clears all debuffs, then consumes (`player.py:147-165`); dramatic message in `main.py:1517-1527` |
| **Unusual Soul Sphere** (artifact) | Family builds (Corwin, Cain, Fianna, Fluffs — `_start_unusual_sphere: True`) | Throwing it summons **Dad** for 5 turns (`game_combat.py:380-415`); on boss floors it does NOT consume — Dad whispers "I believe in you. This one's yours." |
| **Charmander Stuffie + Dreamspun + Rand's Heart** | Family builds set | Curated emotional payload for the user's kids (note: Robyn build references "rands_heart") |
| **Boomstick + Chainsaw Prosthetic + Necronomicon** | Ash Williams build | Cult Evil Dead reference set |
| **Witcher Silver Blade + Signs** | Geralt build | Five sign spells preloaded (`welcome_screen.py:222`) |
| **Zireael** + Elder Blood teleport | Ciri build | Blink/Charge/Scream V-powers (`game_menus.py:674-695`) |
| **Trainer's Cap + 4 Soul Spheres** | Ash Ketchum build | `pet_regen_bonus: 2` to pets; starts with 4 sphere captures |
| **Punch In The Face** weapon | Dad build (typed `god`, confirmed Y to "Did you mean Dad?") | 9999 base damage; immortal player |

## 3.5 Flux Capacitor (McFly easter egg)

**Trigger:** Stand on L1 stairs UP without the Stone. State transitions to `STATE_ABANDON_QUEST` → confirm "Yes, I'm leaving" → `STATE_CHICKEN` popup → press `2` "Nobody calls me chicken!" → `_spawn_flux_capacitor` (`game_input.py:406-416`, `main.py:1422-1448`).
**Effect:** Wand, single charge, `effect: time_stop`, freezes time for 10 turns. `min_level: 9999`.

## 3.6 The "missing" artifacts from CONTEXT.md

The audit-context mentioned "Black Stone, Palladium" as spoiler artifacts:
- **Palladium** — confirmed in artifact.json (above).
- **Black Stone** — NOT present in `data/items/artifact.json`. The `cursed_lodestone` is described as "A massive black stone" (`npc_encounters.py:253-269`) — that may be what the audit was thinking of. **Flag: INCOMPLETE — no separately-named Black Stone item.**

## 3.7 Special weapons with unique mechanics

- **Excalibur / Achilles's Spear**: `kill_heal_amount` heals on kill (`combat.py:209`).
- **Khopesh of Anubis**: `kill_max_hp_bonus` / `kill_max_hp_cap` — gain max HP per kill up to cap (`items.py:93-94`).
- **Chandrahasa**: `low_hp_damage_bonus` — bonus damage when player HP is low (`items.py:95-96, combat.py:135`).
- **Amenonuhoko (Japanese spear)**: `aoe_slow_on_kill` — slow adjacent monsters on kill (`items.py:97-98`).
- **Green Chapel Axe**: `on_hit_regen` — heal when hit by enemy (`items.py:99-100`).

---

# 4. Hidden characters (Secret Builds)

26 secret builds in `src/welcome_screen.py:34-255` (`SECRET_BUILDS`). Type the exact name (case-insensitive) at the welcome screen.

| Name typed | File line | Hint tier | Notes |
|---|---|---|---|
| `aristotle of stagira` | 36 | T5 | "Catalogued the natural world and tutored a great conqueror" |
| `socrates of athens` | 43 | T5 | "Bald, bearded philosopher who famously claimed to know nothing" — extraordinary WIS for the most generous quiz timers |
| `plato of athens` | 50 | T5 | "Sage who wrote of caves, shadows, and ideal forms" |
| `friedrich nietzsche` | 57 | T5 | "Dark-robed philosopher who declared that suffering builds strength" |
| `pythagoras of samos` | 64 | T3 | "Philosopher-mathematician in forest green, with a love of numbers and harmonics" |
| `prometheus the firebearer` | 70 | T3 | "Fire-bringer in a starlit robe, sashed in gold" |
| `diogenes of sinope` | 76 | T3 | "Bald simply-robed monk unfazed by hardship" (game treats Diogenes as the wise-ascetic) — starts WITHOUT a dagger, no clothing |
| `achilles son of peleus` | 84 | T4 | "Mightiest of Greek warriors, near-invulnerable — golden armor and crimson plume" — heel quirk implied but not implemented as a vulnerability |
| `leonidas of sparta` | 92 | T4 | "Spartan warrior who held a narrow pass" |
| `alexander the great` | 99 | T4 | "Great conqueror in golden crown and royal purple cape" |
| `theseus of athens` | 106 | T4 | "Hero who once slew the Minotaur" |
| `hermes trismegistus` | 115 | T4 | "Winged divine messenger in silver-blue" — starts with Hermes's Sandals (early version, hasted-on-equip) |
| `odysseus of ithaca` | 124 | T3 | "Cunning wanderer in a hood, said to have survived ten years of misadventure at sea" |
| `merlin ambrosius` | 134 | T5 | "Legendary archmage in a star-studded dark robe" — starts with two spells already known |
| `corwin` | 144 | none | Family build (Charmander Stuffie + Unusual Sphere) — ranger archetype |
| `cain` | 155 | none | Family build (variant of Corwin) |
| `fianna` | 167 | none | Family build (Dreamspun Sketchbook + Unusual Sphere) — wizard archetype |
| `fluffs` | 177 | none | Family build (variant of Fianna) |
| `dad` | 187 | none | **All stats 20, immortal, 9999-damage weapon.** Triggered by typing `god` (case-insensitive) — popup asks "Did you mean, 'Dad'?" Y → spawns Dad. (`welcome_screen.py:355-366, 405-426`) |
| `robyn` | 195 | none | Family build (Rand's Heart amulet) |
| `ash williams` | 206 | T5 | Evil Dead — "chainsaw-wielding survivor... boomstick... book that should not be opened." Lock-melee flag. |
| `geralt of rivia` | 217 | T5 | "White-haired monster hunter armed with a silver blade and five learned Signs" |
| `ciri riannon` | 226 | T5 | "Young woman with elder blood in her veins... blade called Zireael" — elder_blood flag → Blink/Charge/Scream powers |
| `ash ketchum` | 234 | T5 | "Young trainer in a red-and-white cap... soul spheres" — starts with 4 Soul Spheres |
| `titivillus` | 244 | none | QA test build — "Scribe of Errors" |

**Hidden character lore-tier hint summary:**
- T3 has 4 hidden characters mentioned (fire-bringer, bald monk, hooded sea-wanderer, forest-green mathematician).
- T4 adds 5 (Achilles, Leonidas, Alexander, Theseus, Hermes).
- T5 adds 8 (Aristotle, Socrates, Plato, Nietzsche, Merlin, Ash Williams, Geralt, Ciri, Ash Ketchum).

**Discoverability assessment:** T5 entries are reasonably hinted. Family builds (Corwin/Cain/Fianna/Fluffs/Robyn/Dad) have NO in-game hints — they're personal Easter eggs for the developer's family. The "God → Dad" prompt is a perfect kid-discovery moment.

---

# 5. Debug terminal (XYZZY)

**Hinted by:**
- T1: *"Some say the dungeon itself is a kind of program — and all programs have hidden inputs. Not every key on your keyboard does what you'd expect. Try the ones that seem to do nothing."* (hints.json:18)
- T2: *"Philosophers speak of a reality beneath reality — a hidden terminal that accepts a spoken word. The key to reach it is not listed in any help screen. It sits beside the number 1, quiet and overlooked."* (hints.json:43)
- T3: *"In 1976, a game was released that hid a secret word deep underground. Those who found it could bend the rules of the world."* (hints.json:90) — Colossal Cave Adventure reference.
- T4: *"Crowther and Woods hid a word inside a massive cave. It made no sense to the uninitiated — but it changed everything for those who spoke it aloud in the right place."* (hints.json:131)
- T5: *"The First Magic Word was said to tear reality apart and send the speaker elsewhere. Some say speaking it still works, if you know where to type it — the dungeon has a memory older than its stones."* (hints.json:207)

**Trigger:** Press the **backtick key** (` / K_BACKQUOTE) during normal play (`game_input.py:343-344`). Opens green terminal (`STATE_XYZZY_INPUT`, `game_render.py:234-274`).

**Mechanic:**
1. Type `xyzzy` (case-insensitive) + Enter.
2. Confirm "Hack reality?" Y/N prompt (`STATE_XYZZY_CONFIRM`).
3. `_start_hack_reality` (`main.py:2527-2553`) launches an **AI subject** escalator-chain quiz, max chain 5.
4. The "ai" subject is one of two subjects with no normal action (besides Trivia — recall lore is the other) — it ONLY exists for the XYZZY terminal and the fountain/throne/grave AI-quiz events.

---

# 6. Hack Reality system (tier breakdown)

**File:** `main.py:2555-2710` (`_resolve_hack_reality`).

| Chain | Label | Effect | Once-only? |
|---|---|---|---|
| 0 | "XYZZY FAILED" | SEGFAULT. 100-turn cooldown. Nothing. | n/a |
| 1 | "ECHO" | Full HP/SP/MP restore + clears 15 negative status effects | **Repeatable** |
| 2 | "RESONANCE" | + random PERMANENT positive effect (regenerating, hasted, see_invisible, fire_shield, cold_shield, reflecting, displacement, drain_resist) | Once only (`hack_tiers_claimed`) |
| 3 | "CONVERGENCE" | + all 6 stats **permanently +5** | Once only |
| 4 | "TRANSCENDENCE" | + random **legendary item** at player feet (`_hack_reality_spawn_legendary` — pulls from any item-class with `container_loot_tier: 'legendary'`, excludes generic material-prefixed weapons) | Once only |
| 5 | "SINGULARITY" | + **Fenrir wolf pet summoned** (`pet_system.py:286+` `FenrirPet` — 500 HP, 45 damage, 3 HP/turn regen, double-speed, max-level immediately) | Once only |

**Cooldown:** `150 + chain × 30` = 180-300 turns (chain 5 = 300 turns).
**Chronicle on first use:** `"Spoke an old word of power. XYZZY. Reality flickered. Something changed. I don't think I was supposed to know that word."`

The cooldown is intentionally HIDDEN from the UI (`game_render.py:673` — "Hack Reality cooldown is intentionally hidden from the UI").

**Tier 1 alone is enormously valuable** (full restore + status purge, repeatable) — a serious mid-fight panic button if the player knows about XYZZY.

---

# 7. Hidden quirks (selected — the ones requiring obscure play)

The full list (~80 quirks) is in `src/quirk_system.py:1097-1199`. Most appear in the F1-style quirks screen as locked entries with progress bars. The truly **hidden / counter-intuitive** ones:

| Quirk | Trigger | Reward |
|---|---|---|
| **Odin's Vigil** | Wait 12,960 turns (half a day of mortal time) | Permanent telepathy |
| **The Mithridates Protocol** | Eat ingredients from 5 monster types that poisoned you | Permanent poison & disease immunity |
| **Tantalus' Resolve** | Eat 15 ruined Q0 meals | STR +1 |
| **Job's Endurance** | Trigger 5 distinct trap types | Permanent levitation (immune to floor traps) |
| **Sisyphus' Mastery** | Fail lockpick on 10 distinct trapped chests | Economics timer +5s |
| **Buddha's Stillness** | Wait 500 times near hostile monsters | Permanent displacement |
| **Beowulf's Vow** | Win 10 unarmed combats | Unarmed +5 base damage |
| **Loki's Gambit** | Wear 5 cursed items for 10+ turns each | WIS +2 |
| **Diogenes' Lantern** | DROP your Philosopher's Shard and survive 10 levels without it | WIS +2 |
| **Ragnarok's Survivor** | Descend to L100 with ≤10 HP | CON +5 |
| **Cassandra's Persistence** | Pass 10 threshold quizzes despite ≥2 wrong | WIS +1 |
| **Musashi's Empty Strike** | 30 kills at chain exactly 1 | Chain-1 uses 2nd multiplier (not weakest) |
| **Anansi's Clarity** | 20 correct while confused | INT +1 |
| **Tiresias' Gift** | 25 correct while blinded | PER +2 |
| **Medusa's Gaze** | Answer correctly while blinded across 5 separate episodes | DEX +2 |
| **Orpheus' Lyre** | Stand beside monsters 10 turns without fighting, 5 times | Monsters start slowed 5 turns on each new floor |
| **Hephaestus' Obsession** | Same armor piece equipped 15 times | Equip threshold -1 for that slot |
| **Jormungandr's Cycle** | Same weapon equip/unequip 20 times | That weapon's max chain +1 |
| **Persephone's Descent** | Q5 meals from 5 distinct ingredients | Cooking max chain becomes 6 (not 5) |
| **Sibyl of Cumae** | 500 correct answers before level 20 | All quiz timers +2s |

**Hidden power quirks** (30 of them, unlock via play): `_ACTIVE_POWER_DEFS` in `quirk_system.py:1058-1089`. Each grants a 1-5 use **active** power (V key menu). Examples:
- Philosopher's Stone power: identify 200 items → 1-use [Blessed + Brilliance 10t]
- Phoenix Rising: survive at ≤5% HP 10 times → 1-use [fully restore HP]
- Ouroboros: 1000 correct answers in one run → 1-use [Haste+Shield+Regen 20t]
- Wandering Star: teleport 15 times → unlimited use with 50t cooldown

**Hinted by:** T2-T5 hints scatter many quirk names obliquely (Mithridates, Odin, Penelope, etc.). The Oracle's Rift mystery (`mystery_system.py:117-128`) explicitly reveals 3 locked quirk hints on success (`_oracle_reveal_quirks`, `mystery_system.py:397-431`).

---

# 8. Hidden item interactions

| Combination | Trigger | Result |
|---|---|---|
| **Stone + Tablet of Second Death (via Wrench)** | Hold both, use Wrench (zap it from wand menu) | Fuse into Complete Tablet of Second Death (`main.py:1318-1344`) |
| **Complete Tablet + Abyssal Shimmer** | Drop Complete Tablet on Shimmer tile | Shimmer activates (turns crimson, ready to consume Death) |
| **Read Scroll of Lake of Fire while Death is on activated Shimmer** | Read scroll with positioning | KILL DEATH → drops Scroll of Death's Bane |
| **Bronze Bull Idol → fountain** | Drop on fountain tile | Activates Ariadne shrine → opens hidden passage to Ariadne's Thread |
| **Eye of the Graeae → altar** | Drop on any altar | Activates Athena shrine → opens passage to Aegis of Athena |
| **Broken Gram → drop on Odin's Altar** | Drop ON the Odin altar tile | Opens shrine; Odin gives spade-quest dialog ("dig as Sigurd dug") |
| **Broken Gram → THROW over Odin's Altar** | Throw weapon, path crosses altar tile | **Lightning! Gram is REFORGED on the altar** (`game_combat.py:286-299`) |
| **6 Gleipnir components → Dwarven Forge tile** | Drop all 6 on the forge | Components dissolve, Gleipnir materializes |
| **10 Leather Scraps → Vidar's Altar** | Drop 10 scraps on the altar tile | Scraps fuse into Vidar's Sandal |
| **Magic Carrot → ground near Unicorn** | Drop carrot within 2 tiles of "relaxing" unicorn | Unicorn approaches and eats; later allows interaction (AI quiz → boons) |
| **Soul Sphere → THROW at monster (or empty tile)** | Throw using `t` key | Releases a random elemental pet (electric/water/plant/fire) at landing spot (`game_combat.py:333-378`) |
| **Unusual Soul Sphere → THROW** | Throw on non-boss floor | Summons Dad for 5 turns (boss floors: NOT consumed, Dad encourages you) |
| **Item on altar** | Drop any item with BUC on altar | Altar BUC upgrade quiz (theology chain → uncurse or bless) (`game_divine.py:184-233`) |
| **Pray on altar** | `\` key while standing on ALTAR tile | Effective chain +1, higher prayer tier outcomes |
| **L100 altars + prayer** | Pray on any L100 altar | Strip Abaddon's resistances for `chain × 2` turns; each altar single-use |

---

# 9. Mystery system encounters (13 mystery altars)

**File:** `src/mystery_system.py:16-187`. Each spawns at 60% chance per eligible level (after the floor's altar/altar room generation). One mystery per floor max.

| ID | Name | Floor range | Trigger | Reward |
|---|---|---|---|---|
| **sphinx** | The Sphinx | 22-35 | Philosophy T3 escalator_threshold 4/6 | WIS+2, INT+1 |
| **pandora** | Pandora's Coffer | 20-30 | Economics T2 threshold 4/5 — **INVERTED** (fail = success) | Permanent magic_resist + displacement + 300 gold (success-via-fail); 100 gold on "success" |
| **grail** | Chapel of the Grail | 45-55 | Theology T3 threshold 5/7 | Max HP +30, CON+2 |
| **fleece** | The Fleece Altar | 38-50 | Animal T3 chain (threshold 5) | Permanent regenerating + poison_resist |
| **mimir** | Mimir's Well | 42-55 | Philosophy T4 chain (threshold 6) — PRE-COST: PER-1 | INT+3, all quiz timers +1s |
| **mjolnir** | The Dwarven Forge | 33-45 | Math T3 escalator_threshold 4/6 | **Mjolnir (full)** + STR+2 |
| **crucible** | Alchemist's Crucible | 10-22 | Philosophy T1 threshold 3/4 | 400 gold |
| **oracle** | The Oracle's Rift | 25-35 | Theology T3 threshold 5/7 — COST: 50 gold | Reveals 3 hidden quirks via cryptic hints (`mystery_system.py:397-431`) |
| **solomon** | Solomon's Tribunal | 30-42 | History T3 threshold 6/8 | WIS+2 + **Ring of Command** (WIS+1) |
| **fisher_king** | The Fisher King's Hall | 58-72 | Theology T4 threshold 5/7 | Max HP+30 + **prayer cooldown permanently halved** (`fisher_king_mystery_active`) |
| **sisyphus** | Sisyphus' Hill | 78-92 | Physical: walk 25 tiles over carry limit holding 30-lb Boulder | STR+3, INT+1 |
| **cauldron** | The Black Cauldron | 14-26 | Cooking T2 escalator_chain (threshold 5) — COST: 3 cooked Food items | Permanent searching + warning |

**Pandora's Coffer twist** (`mystery_system.py:31-45`): It is the ONLY mystery with `invert_result: True`. Passing the quiz "well" gives just 100 gold; FAILING the quiz triggers the "true" reward (chaos floods out + Hope). The T3 hint says *"Pandora's box is said to lie somewhere in the depths. The old stories say opening it was a mistake — but old stories are not always right."* (hints.json:78) — the inversion is hinted by the "not always right" line.

**Hinted by:** T2 *"Strange altars sometimes appear in the dungeon. Those who approach and kneel before them discover ancient challenges — and ancient rewards."* (hints.json:34). Individual mysteries hinted in T3-T4 (Sphinx, Pandora's box, Grail, Cauldron, Mjolnir's reforge, Sisyphus' boulder, Fisher King, Mimir's well, Oracle).

---

# 10. Pet capture / bonding

## 10.1 Soul Sphere — the Pokeball mechanic

**File:** `game_combat.py:333-378` (`_throw_soul_sphere`), `pet_system.py:1-268` (`Pet` class with 4 species × 3 evolution stages).

**Trigger:** Throw a Soul Sphere (`t` key, select sphere, target a monster or empty tile).
**Mechanic:** A random species (electric/water/plant/fire) Pet is released at the landing tile. The pet starts at L1 (Zappik/Shellkit/Seedling/Emberpup), gains XP from monster kills, evolves at L33 and L66.

**Hinted by:** T5 *"A young trainer in a red-and-white cap has been seen descending into the dungeon, carrying not weapons but soul spheres."* (hints.json:206)

## 10.2 Ethereal Unicorn (L21-39 one-time encounter)

**File:** `game_encounters.py:251-516` (`_maybe_spawn_unicorn`, state machine, `_apply_unicorn_boons`).

**State machine:**
1. `wary` — Unicorn watches. Wait 3 turns near her → 'relaxing'.
2. `relaxing` — Drop Magic Carrot within 2 tiles → 'eating'.
3. `eating` — 2 turns → 'trusting'.
4. `trusting` — Bump for AI escalator-chain quiz. **Karma < 0 → unicorn flees in disgust** (`game_encounters.py:328-334`).

**Boons by chain:**
- 1: Regenerating 30 turns
- 2: + full HP/SP/MP restore
- 3: + uncurse ALL equipped/inventory cursed items
- 4: + permanent magic_resist OR poison_resist
- 5: + **Unicorn joins as a PET** (`pet_system.py:UnicornPet`)

**Hinted by:** No direct T1-T5 hint for the unicorn ritual itself. The Magic Carrot's lore mentions "favorite food of a certain magical beast" — only trail.

## 10.3 Sketched Pet (Dreamspun Sketchbook)

**File:** `game_menus.py:655-663`, `pet_system.py:333+` `SketchedPet`. Manifest a visible monster as a 40%-stat temporary ally.

## 10.4 Fenrir pet (XYZZY tier 5)

See Hack Reality / XYZZY (section 6).

---

# 11. Easter eggs and nods

| Easter egg | File | Reference |
|---|---|---|
| **XYZZY** | `game_input.py:431+` | Colossal Cave Adventure (1976) — explicitly cited in T3/T4 hints |
| **Secret Cow Level** | `boss_levels.py:533+` | Diablo II "Moo Moo Farm" |
| **Soul Spheres = Pokeballs** | `game_combat.py:333+` | Pokémon |
| **Ash Ketchum build** | `welcome_screen.py:234+` | Pokémon (Trainer's Cap, "Gotta catch 'em all") |
| **Charmander Stuffie** | family builds | Pokémon (Charmander) |
| **Flux Capacitor** | `main.py:1422+`, "Nobody calls me chicken" popup | Back to the Future ("McFly!") |
| **Ash Williams** | `welcome_screen.py:206+` | Evil Dead — "Boomstick", "Necronomicon", greeting *"Good. Bad. I'm the guy with the gun."* |
| **Geralt of Rivia** | `welcome_screen.py:217+` | Witcher 3 — five Signs, three potions, *"Wind's howling."* |
| **Ciri (Cirilla Fiona Elen Riannon)** | `welcome_screen.py:226+` | Witcher 3 — Zireael blade, Elder Blood powers |
| **Merlin** | `welcome_screen.py:134+` | Arthurian / Disney |
| **Dad** | `welcome_screen.py:187+` | Personal: God→Dad popup is a kid moment |
| **Robyn / Rand's Heart** | `welcome_screen.py:195+` | Personal: Robyn is presumably the developer's child; Rand's Heart prevents death |
| **Corwin / Cain / Fianna / Fluffs** | `welcome_screen.py:144+` | Personal: family character builds (Corwin Amber-style ranger, Cain Hunter, Fianna wizard, Fluffs variant) |
| **Titivillus** | `welcome_screen.py:244+` | Medieval folklore: "Scribe of Errors" — QA test build |
| **Sphinx riddles** | `mystery_system.py:17-30` | Oedipus mythology |
| **Mjolnir reforge** | `mystery_system.py:89-102` | Norse — note Mjolnir is also a mystery reward (unfinished hammer to be reforged at the forge) |
| **Gleipnir + 6 impossible ingredients** | `dungeon.py:1558-1570` | Norse — the original recipe is sound of cat's footstep, beard of woman, root of mountain, fish breath, bird spittle, bear sinew |
| **Bronze Bull Idol** | `npc_encounters.py` references + Ariadne | Greek — Minos and the Cretan Bull |
| **Wandering Jew / Ahasverus quirk** | `quirk_system.py:236+` | Medieval Christian legend |
| **The Wendigo / Wild Hunt monsters** | T5 hints | Various folklore — these are normal monster spawns, not secrets |
| **The Sphinx in mid-floors** | mystery + T3 hint *"A lone sphinx in the depths poses riddles..."* (hints.json:69) | Egyptian/Greek |

---

# 12. Bones interactions with secret content

**File:** `src/bones.py:79-153`. 50% chance to load a bones file on any matching dungeon level. The dead player becomes a **Ghost** monster (player_ghost, `bones.py:97-147`), with drain damage and physical/cold/poison resistance + holy/fire weakness.

**Hidden interaction:** The dead player's equipped gear is dropped near the ghost as **cursed** items (`_place_cursed_gear`, `bones.py:156-199`). The Loki quirk explicitly rewards wearing 5 cursed items for 10+ turns each (`quirk_system.py:924-946`) — so bones content can BE a quirk farm.

**Not currently hidden, but worth noting:** No T1-T5 hint references the bones system explicitly. Players will encounter ghosts on the same dungeon level on subsequent runs.

---

# 13. Cross-system interactions

| Secret | Touches |
|---|---|
| Death-kill ritual (Stone + Tablet + Shimmer + Scroll) | BOSS, DIVINE (Death), PROGRESSION (full ascent), LORE (5 items) |
| Vidar's Sandal | DIVINE (altar), BOSS (Fenrir alt-kill), PROGRESSION (10-floor scrap collection) |
| Gleipnir | DIVINE (altar in component room 5), BOSS (Fenrir binding), PROGRESSION (6-floor recipe) |
| Gram reforge (throw-over) | DIVINE (Odin), BOSS (Fafnir), PROGRESSION (L48-53 setup) |
| Last Judgment | DIVINE (L99 altar), BOSS (Abaddon empowerment OR Sword), PROGRESSION (karma accumulation), LORE (Sword/Scales/title) |
| Medusa mirror path | DIVINE (Athena altar), BOSS (Medusa), LORE (Eye + Aegis) |
| Medusa blindfold path | Standalone; no DIVINE involvement |
| Ariadne thread | DIVINE (fountain), BOSS (Asterion), LORE (Bronze Bull) |
| Hack Reality (XYZZY) | LORE (T1-T5 hint chain), PROGRESSION (in-game powerup, Fenrir-pet endgame) |
| Mystery altars | DIVINE (kneel/pray), PROGRESSION (per-floor power spikes) |
| Cow level | PROGRESSION (side-floor with high-density bovines for cooking) |
| Sketched pet | LORE (Dreamspun book), pet system, family builds |
| Unicorn | LORE (Magic Carrot), KARMA (karma <0 → flees), pet system, encounter system |
| Pet companion (Soul Sphere) | Character creation (Ash Ketchum), throw mechanic, pet AI |
| Rand's Heart | Robyn build only, death-prevention layer |
| Dad / Unusual Sphere | Build-only (5 family builds + "God" typo), CHRONICLE |
| Bones / cursed gear | PROGRESSION, Loki quirk farm |

---

# 14. Discoverability map

| Secret | Hint trail quality | Risk: undiscoverable? |
|---|---|---|
| XYZZY | **Excellent** — 5 hints across T1-T5 | Low. Easily findable. |
| Cow level (10 pokes) | **None** | **HIGH.** A player without genre knowledge will never know to poke a cow 10 times. |
| Ariadne thread (Bronze Bull) | **Excellent** — T3 + T5 explicit | Low. |
| Athena Aegis (Eye of Graeae) | **Good** — T4 *"Grey Sisters share a single eye between three bodies"* + T5 Perseus | Moderate. Requires knowing to drop on altar. |
| Medusa via Mirror | **Excellent** — T4 + T5 explicit | Low. |
| Medusa via Blindfold | **Excellent** — T4 explicit *"What you cannot see cannot harm you"* | Low. |
| Odin shrine (Broken Gram drop) | **Good** — T5 Sigurd hint | Low-moderate. |
| **Gram REFORGE (throw-over)** | **Weak** — only Gungnir T5 hint nods at the throw archetype; no direct hint | **HIGH.** The dungeon's most spectacular weapon reward is gated behind a mechanic almost no player will attempt. |
| Gleipnir (6 components + forge) | **Excellent** — T4 explicit | Low. Six themed rooms + forge prompt. |
| **Vidar's Sandal (10 scraps + L79 altar)** | **Weak** — only T5 *"useless scraps... not useless at all"* | **HIGH.** The scrap lore SAYS they're useless. The Vidar altar isn't hinted at all. |
| Seven Seals gate | **Implicit** — must encounter seal demons; "ALL SEVEN SEALS BROKEN" message is clear once 7th falls | Low. |
| L100 altar resist-strip | **Moderate** — T5 mentions prayer/altars + Abaddon weakness | Moderate. |
| Last Judgment / Sword | **Good** — T4 Grail + T5 "three boons" | Moderate. Requires karma accumulation across whole run. |
| **Kill Death ritual** | **Excellent** — 5+ hints across T2-T5 | Moderate. The hint chain is there but assembling 4 items from 4 different floor ranges + executing the sequence is the hardest discovery in the game. |
| Tablet of Destinies | **Good** — T5 explicit "single wrong answer is not always the end" | Low. |
| Palladium | **Excellent** — T3 explicit | Low. |
| Mysteries (Sphinx, Mjolnir, etc.) | **Excellent** — most have T3/T4 hints + altar tile detection | Low. |
| Magic Carrot → Unicorn | **Moderate** — Carrot's lore + magical-beast hint | Moderate. |
| Soul Sphere throw | **Moderate** — Ash Ketchum hint mentions soul spheres | Moderate. |
| Hidden characters (T3-T5 hinted) | **Excellent** | Low. |
| Family builds (Corwin/Cain/Fianna/Fluffs/Robyn/Dad) | **None** | Intentional — these are personal Easter eggs. |
| Flux Capacitor | **None** — discovered only by abandoning quest then refusing | **HIGH** for non-McFly-knowing players. |
| Bones ghosts | **None** | Acceptable — emerges naturally on repeat runs. |

---

# 15. Incomplete / orphaned references (flag)

1. **"Black Stone"** referenced in audit context but not present in `data/items/artifact.json` — likely confused with `cursed_lodestone` ("massive black stone"). Flag: **possibly missing item**.
2. **Achilles's heel** — Achilles secret build's greeting says *"His heel tingles ominously"* but no mechanical heel-vulnerability exists. The build just has high stats. Flag: **lore promises a vulnerability that isn't implemented**.
3. **Cow King "boss reward"** — Cow King has `is_boss=True` but no special drop chain confirmed. Hell Bovines are the main attraction. Flag: **Cow King's drop table not separately verified**.
4. **Aristotle's "ring and a lantern"** — T5 hint says Aristotle starts with both; the build (`welcome_screen.py:38-41`) has the ring + Lantern of Diogenes. Confirmed.
5. **Diogenes' Lantern quirk** rewards dropping the Philosopher's Shard for 10 levels — the **Shard** is a never-explained starting item. Searching `philosophers_shard` confirms it's spawned at start (`main.py:3705+`). Flag: **the Shard mechanic itself is a hidden quirk-trigger but not hinted in lore at all**.
6. **No T-tier hint for the Cow level** — the only hint is the T3 line about "rare creatures that appear in the dungeon only once" — generic and ambiguous.

---

# 16. Summary count by category

| Category | Count |
|---|---|
| Hidden levels (Cow + hidden chambers) | **2 systems**, ~5+ chambers per floor possible |
| Boss quest layers (Asterion, Medusa×2, Fafnir×2, Fenrir×2, Abaddon×4) | **11 distinct paths** |
| Hidden artifacts (lore items + mystery rewards + named) | **~30 unique items** (4 lore-quest + 24 artifact.json + Mjolnir + Aegis + Vidar's Sandal + Sword of Michael + Death's Bane + 5 family-build) |
| Hidden characters (secret builds) | **26 builds** |
| Mystery altars | **13** |
| Hidden quirks (passive) | **~70 quirks** |
| Hidden powers (active V-menu) | **30 power quirks** + 4 item-granted (Fire Breath, Manifest, Bind Odinkiller, Heavenly Host) + 3 Elder Blood (Ciri only) |
| Easter eggs / pop-culture nods | **~15** (XYZZY, Cow, Pokemon, BTTF, Evil Dead, Witcher, etc.) |
| Cross-item combinations | **11** documented |

**Grand total of distinct secrets/easter eggs:** ~200+ discrete pieces of hidden content.

---
