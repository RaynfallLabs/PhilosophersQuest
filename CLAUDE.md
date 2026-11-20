# Philosopher's Quest

## Core Concept
A graphical roguelike where knowledge is power. Every action requires answering quiz questions. Performance determines outcome — not random chance.

## Quiz Modes
- **threshold** — Must answer X correct to succeed (e.g., equipping armor, harvesting)
- **chain** — Build combo until wrong answer; score = chain length (e.g., combat attacks)
- **escalator_threshold** — Questions get harder each round; must hit a correct threshold
- **escalator_chain** — Questions get harder each round; chain until failure (e.g., praying)

## Subject → Action Mapping
| Subject     | Action                  |
|-------------|-------------------------|
| math        | Combat attacks (chain)  |
| geography   | Armor/shield equipping  |
| history     | Accessory equipping     |
| animal      | Harvesting corpses      |
| cooking     | Preparing food          |
| science     | Magic / wands           |
| philosophy  | Identification          |
| grammar     | Reading scrolls + spellbooks |
| economics   | Lockpicking             |
| theology    | Praying                 |

## Player Stats
- **STR** — Carry capacity, and pays back the speed medium and heavy armour cost (full speed in medium armour from STR 13, in heavy from STR 16; a STR-fit hero in plate is at speed 10)
- **CON** — Max HP (3 per point), toughness (1% less damage per point over 10, cap 40%) and a little carry (3 lb per point over 10)
- **DEX** — No armour class (AC comes from armour, shield and magic only). Dodge (1.25% per point over 10, cap 40%) and speed (+1% per point over 10, cap +20%; 10 is ordinary), both half in medium armour and none in heavy; the dodge is less under a Light, Heavy or Burdened load
- **INT** — Max MP, and the share of it meditation gives back each floor (half, +1% per point over 10, cap 80%)
- **WIS** — Quiz timer bonus (+1 second per point)
- **PER** — Sight radius

## Project Structure
Fuller per-system docs live in `docs/systems/` (start at `docs/systems/README.md`).
```
src/
  # Entry point and the Game class (main.py + its game_* mixins)
  main.py             - Entry point, game loop, Game class and state (large; split planned)
  game_states.py      - Game.state string constants
  game_input.py       - InputMixin: key handling outside menus
  game_menus.py       - MenuMixin: menu open logic and per-tab item lists
  game_render.py      - RenderMixin: render() and every _draw_* screen (help screen included)
  game_combat.py      - CombatMixin: attacks, monster turns, pet and escort swipes, kills
  game_magic.py       - MagicMixin: spells, wands, scrolls, spellbooks
  game_wards.py       - MagicWardsMixin (MagicMixin's base): the MONSTERS AND MAGIC spells, scrolls, wands, the prayer Deliver Us, the Sceptre of Agamemnon's V power
  game_divine.py      - DivineMixin: prayer, intercession, Judgment
  game_encounters.py  - EncountersMixin: NPC, flavor and special-level encounters
  game_road.py        - RoadMixin: the Road, pending queue and oath lifecycle
  game_helpers.py     - Stateless helpers once static methods on Game
  layout.py           - Live window / viewport globals (and the version string)
  display_setup.py    - First window size and Windows DPI awareness

  # Hero, monsters, world
  player.py           - Player class: stats, inventory, equipment, quiz timers
  monster.py          - Monster class with AI patterns
  monster_classes.py  - Thin reader of each monster's `family` field (get_monster_family)
  family_lore.py      - Monster families: kind-to-family map, tiers from kinds studied, circles, news
  family_edges.py     - Family technique primitives (wards, damage, executes, sense the hidden...)
  game_families.py    - FamilyMixin: study news, tier popups, arrival lines, QA family key
  dungeon.py          - Procedural BSP dungeon generation
  level_manager.py    - Floor transitions
  boss_levels.py      - Hand-crafted boss floor layouts (and COW_LEVEL)
  floor_curve.py      - Median monster HP / damage by floor (balance anchors)
  geom.py             - Multi-tile footprint geometry
  fov.py              - Shadowcasting field of view
  unseen.py           - What the hero cannot see on a visible tile (invisible, ambush, disguise)
  senses.py           - How a monster notices the hero: sight, sound, lore senses; searching; idle jobs
  wanderers.py        - The floor's clock: time to explore (a grace from its explore tour), then a trickle of newcomers
  war_bands.py        - War-bands: groups with a leader and roles, morale when he falls
  packs.py            - Packs: kin that hunt together (surround in the open, hold a corridor's mouth or go round) and each family's trick (rats swarm, wolves hamstring, goblins sling...)
  tells.py            - Tells: what a dangerous creature shows it can do, and what to do about it
  tactics.py          - The Tactical Mind, pure: a thinking creature's options scored from what it sees (data/minds.json)
  tactical_mind.py    - The Tactical Mind in play: who thinks, the View, the plan carried out, a band leader's orders, the feint, focus on a hurt pet
  lanes.py            - Archers Find a Lane: each missile's reach, a lane past its friends, a step back, no walking into melee
  habits.py           - They Learn Your Tricks: what a side SAW the hero do on this floor (corridors, blasts, kiting, resting)
<<<<<<< HEAD
  # Monster behaviour, first wave (AI-1, 2026-11-19): small pure modules, numbers and lines in data/monster_ai.json
  kind_data.py        - A kind's own fields where the Monster keeps no copy; data/monster_ai.json; the behaviours' tells
  ai_lines.py         - What a behaviour leaves for the Game to say (seen / unseen)
  faction.py          - Whose side a monster is on (band, pack, family); the healer's choice and its rest
  summoning.py        - Summoners chant (a blow breaks it), then call while few of theirs stand
  breath.py           - Draws Breath: a breath must be drawn again; tooth and claw meanwhile
  morale.py           - Morale by Nature: who breaks (never, bolt, regroup, withdraw, yield), when, and the run
  ai_blow.py          - What the behaviours add to one monster blow (to-hit shift; after the blow)
  life_drain.py       - Life Drained: a drain blow lowers max HP; half back on the stairs, all from prayer or physician
  grave_rot.py        - Grave Rot: disease lingers, stops rest mending, halves heals; ticks on a monster
  light_shy.py        - Light-Shy (flinch, a troll's wounds, stiffening) and Snuff the Light (a soaked wick)
  gone_again.py       - Gone Again: a hit-and-run creature hides out of sight (in the dark, unseen)
  alarm.py            - Raise the Alarm: a lookout's shout rouses its side, once a floor
  death_throes.py     - Death Throes: it swells, then bursts as it dies
  relurk.py           - Back to the Web: a hurt ambusher out of sight hides again
  shove.py            - Shove: a giant's blow throws the hero back, never into deadly ground
  game_behaviour.py   - BehaviourMixin: the Game's side of the behaviours (lines, the map, the kill)
=======
  wards.py            - Wards (data/wards.json): a family kept off (melee, riders, sight, damage), missiles stayed, mist, sanctuary, the Styx; what a strike breaks
  attack_gates.py     - What a monster cannot use now: silenced (no voice, cast, summon, heal), unstrung (no missile, breath, gaze), babbled (no pack ways)
>>>>>>> main
  decor.py            - The five domains (themes) and the fixture layer: what stands in a floor
  hazards.py          - Domain hazards (data), trap lean, kin weights and the floor's resident clan
  game_hazards.py     - HazardsMixin: hazards at work on the hero and the monsters; fire vents breathe
  game_lore_fixtures.py - LoreFixturesMixin: Worth a Closer Look, one question at a lore fixture (D)
  false_stairs.py     - Hellmouth mimics that pose as the down stair
  splitting.py        - Creatures that split when struck the wrong way
  lore_powers.py      - The 2026-11-19 kinds' own powers (pure): the Cu-Sith's three barks, the Bulgasari eats iron, the Mapinguari's soft spot, the Lindworm's skins, the Kappa's dish, the Roc's carry-off, what hangs overhead
  game_lore_powers.py - LorePowersMixin: their game side (a gift of food, gold for the ants, the Blue Men's verse on D, the Vetala's corpse hop, the Jiangshi's talisman, the QA key Shift+Y)
  sleepers.py         - Zoo, graveyard and barracks sleepers stir at footsteps and gold taken
  theft.py            - Thieves that really steal, and give it back on death
  black_knight.py     - The Black Knight bridge easter egg (floors 15-19)
  stray_kids.py       - The Stray Kids easter egg (floors 8-12): the zombie band's dance-off rules (Simon Says rounds, strikes, the earworm), the stage, the stars
  game_stray_kids.py  - StrayKidsMixin: the idol, the Zombie Stage trip, the dance-off (Simon Says on the shared dance screen), the photo's show
  emberpup_encounter.py - The abandoned Emberpup (floors 3-8): three feeds, the Bloomleaf Cloak won from Old Nickel; he keeps it
  old_nickel.py       - Old Nickel's voice (data/old_nickel.json): the false friend's offers, asides and rest urges, the reveal that drops the act, then the open killer's taunts; his AI is Monster._stalker_turn (ai_pattern stalker_coward)
  mooble_encounter.py - The Mooble (floors 31-45): his side cave, the Starnut Tart, three dance-offs, "I choose you"; his gifts as a pet
  game_mooble_dance.py - MoobleDanceMixin: the dance screen (practice, the dance-off, his danced special), the beat, real-time keys
  rhythm.py           - Any dance scored, pure: the beat timeline (with or without a call), Perfect / Good / Miss, pass mark, score bands
  setne_tomb.py       - Setne's Tomb and the Book of Thoth (floors 45-65)
  bococho_encounter.py - The Bococho's racing camp (floors 51-65): two Sunroots, Gilt Varro's bet, "I choose you"
  underway_run.py     - The Underway Run (side floor 996): the oval track, its two lanes, the paddock
  race.py             - The race's scoring, pure: legs as maths chains, Sprint or Pace, wind, the caltrops
  game_race.py        - RaceMixin: the trip to the Underway Run and back, the race screen, the birds on the oval
  game_bococho_render.py - BocochoRenderMixin: the camp's screen, the race panel, the hero in her saddle

  # Combat, items, magic
  combat.py           - Combat resolution
  affinity.py         - Weakness, resistance, shrugs off (data/affinity_rules.json): what a hit met, and the lines that say so
  kit_sense.py        - Kit Sense: the best tool carried for a family known to Hunter (tool providers)
  enemy_lore.py       - The Wand of Probing's reading (a probe teaches the kind, as a corpse study does), quests that teach the boss
  dice.py             - Dice notation parser ("2d6+3")
  random_streams.py   - own_stream(): a floor builder's own generator, seeded from the shared stream (same seed, same floor in every process)
  items.py            - Item classes and equipment system
  gear.py             - Armour, shield, ring and amulet rules: levels, tiers, thresholds, core AC
  defence.py          - The defence model, pure: AC from armour only, dodge and speed from DEX, armour's drag paid by STR, the load tiers
  guards.py           - What the minor armour slots guard: attack delivery, families, touch AC
  enchantments.py     - The minor-slot enchantment stable: guard, might, craft and way lanes
  rings.py            - Ring and amulet kinds: levels, ladders, names, what a worn kind does
  gear_saves.py       - Old saves meet the armour ladder: named pieces refreshed, worn grants re-synced
  item_actions.py     - Item actions shared by the Kit (K) and the character sheet (@)
  known_by_hand.py    - Known by Hand: a kind of gear put on once goes on again with no quiz
  game_dressing.py    - DressingMixin: donning time, the weapon At Your Back (S), Loadouts (Shift+E)
  busy.py             - Busy for N turns: a multi-turn action, stopped by a foe in view or a blow
  loadouts.py         - The three saved kits and the readied weapon: names, slots, defaults; a piece dropped, thrown or stolen is remembered and back in place when picked up
  coatings.py         - Coatings (silver dust, holy water, fire oil...) on the wielded weapon; thrown flasks; Kit Sense's tool hook
  stance.py           - Press or Guard (Shift+S): damage against AC; the two-hander's parry with no shield
  counters.py         - Named counters: the mirror shield turns a gaze, wax stops a voice, cold iron fey glamour
  game_arsenal.py     - ArsenalMixin: coat (Shift+C, Kit Apply), throw a flask, change stance, the earplugs, QA (Shift+T)
  lights.py           - Lights in the off hand (data/items/light.json), pure: the brightest light counts, a lit hero is seen farther, fuel, the Light spell's turns
  game_lights.py      - LightsMixin: take a light up, burn it each turn (the next torch, the next oil), Shift+O to douse, Kit Apply to fill, Hero's Lamp's way down
  chain_equip.py      - Chain-equip for lore-rich legendary uniques
  chain_passives.py   - Chain-equip passive flag lookups and wiring
  armor_procs.py      - Flat-armour proc registry and per-floor charges
  hero_specials.py    - One special ability per Secret Build
  spells.py           - Spellbook spell definitions (tiered families)
  prayers.py          - The prayer list and what each grants
  altar.py            - The altar's offering: curses lifted, then blessings; what a blessing changes
  rededication.py     - The altar's rededication: give a stat point back to take another, once per altar
  boons.py            - Gate-boss gifts (pick one of three)
  status_effects.py   - Buffs/debuffs (paralysis, poison, berserk, etc.)
  food_system.py      - Harvest and cook (the two quiz flows), eating, potions
  butchered.py        - Butchered Before: a kind identified and harvested once is harvested again with no question
  kitchen.py          - The kitchen: kin ingredients, the recipe book, what a dish gives (cooking_rules.json), the cook menu's rows; cook to carry (a recipe's `makes`)
  cook_menu.py        - The cook menu's words (why it opened where, chips, what is missing) and its list window (pure)
  container_system.py - Chests, sacks, lockable containers (lockpicking)
  economy.py          - The gold economy: what a floor earns and what things cost
  traders.py          - Named traders: who, where, their stock, prices, selling, services
  game_traders.py     - TradersMixin: placing traders and the Buy / Sell / Services screens, trade-in, orders
  domain_counters.py  - Stock that knows what's below: what walks under a stall and the counters for it
  smithing.py         - The smiths' work: reforge, silvering and cold-iron inlay, linings, special orders
  treasure.py         - Coin weight (1 gp = 0.1 oz) and treasure: gems, jewellery, art; values, payment plans
  game_purse.py       - PurseMixin: receiving gold (weight-limited), paying with coin then treasure, gold piles
  pet_system.py       - Soul Sphere pets: AI, bonding, levels
  riding.py           - Riding the Bococho, the rules: getting on, the two-tile step, what sets the rider down
  game_riding.py      - RidingMixin: mount and dismount, the mounted step, set-downs, her saddlebags
  escort_system.py    - Escorts: people the hero walks somewhere
  sketch_manifest.py  - Manifest, the Dreamspun Sketchbook's power (pure): what she can draw (studied or in view, no bosses), the bite's type, INT + 5 turns a right answer, the menu's rows and tabs
  game_manifest.py    - ManifestMixin: the Manifest menu (V, Manifest), the AI quiz, the sketch set down beside her, the QA key (Shift+V)
  horns.py            - The four horns of legend (data/horns.json): Robin Hood's Horn, Arthur's Bugle, Gjallarhorn, the Olifant; who answers a chain, once a run; CalledAlly (a helper that comes and goes, never a gate's guardian's foe)
  game_horns.py       - HornsMixin: the horn powers in V (a history escalator chain), the Olifant's host on the road, the called going home, the QA key (Shift+H: each horn's path beside the hero)

  # Quiz
  quiz_engine.py      - All quiz logic (threshold, chain, escalator modes)
  philosophy_mastery.py - Philosophy tier traits: master a tier in one run, its items name themselves
  study_mode.py       - Standalone untimed Study Mode (title screen F3): by difficulty or by topic
  topic_cards.py      - Topic cards with no quiz running: titles, the Lore Codex, topics met/read

  # Story, deeds and karma
  deeds.py            - The deeds register: what the hero has done this run
  karma.py            - The single karma entry point (adjust)
  chronicle.py        - The hero's chronicle (Journal and Your Story entries)
  road.py             - The Road: where the run's encounters stand
  encounter_schema.py - Encounter loader normalisation and shared runtime rules
  npc_encounters.py   - NPC moral encounters (one anchor per 10-floor block)
  flavor_encounters.py - Story and flavor encounters
  mystery_system.py   - Mystery altars, key items, encounter logic
  quirk_system.py     - Per-character unlockable quirks
  quirk_text.py       - Player-facing quirk and power text

  # The Seeker profile (the real player, across every run) and achievements
  seeker_profile.py   - The Seeker's sealed profile file (save_dir()/seekers): backup, merge, set-aside
  seeker_codes.py     - Reward codes for Dad and the profile seal (the key is never in the repo)
  achievements.py     - Achievement rules from data/achievements.json: counters, triggers, ladders
  seeker_session.py   - The running Seeker: emit an event, unlock, save, look up a code
  game_seeker.py      - SeekerMixin: game events reach the Seeker; achievements join the popup queue
  game_popups.py      - PopupMixin: popups from play wait for calm play and open one at a time
  seeker_screen.py    - The Seeker Profile screen (title screen, F4) and the badge gallery

  # UI and presentation
  renderer.py         - Pygame tile rendering
  ui.py / fantasy_ui.py - Sidebar, message log, menus, fantasy-themed helpers
  ui_theme.py         - The UI art kit (painted panels and pieces)
  ui_scale.py         - The one UI scale factor
  text_layout.py      - Text fitting and containment helpers
  hud_context.py      - Pure HUD row builders
  lore_art.py         - The subject's art on lore pages
  welcome_screen.py   - Title screen and Secret Build definitions
  naming.py           - Display-name capitalisation (proper_name)
  effects_runtime.py  - Pluggable visual-effects controller (effects/ holds the handlers)
  sound_system.py     - Procedural sound effects
  music.py            - The soundtrack (Brandon's PQ Main Theme): looped from the title on, F5 on / off, remembered; a dish's song takes the stream while it plays
  songs.py            - Songs the hero plays (Brandon's own, as A Man Before a King), on real seconds: Caviar and Tater Tots (a dish: half damage), Math is Cool (a power: chain x2), The Greatest Trainer of All Time (the Unusual Soul Sphere: Dad stays till it ends)
  game_songs.py       - SongsMixin: the song's clock every frame, its audio, F5 mid-song, the soundtrack back after, whoever came with it seen off

  # Persistence and plumbing
  save_system.py      - Per-name pickle saves
  bones.py            - Persistent ghost/bones across runs
  highscore_system.py - High score table
  game_log.py         - ERROR_LOG.txt logging (log_error)
  crash_handler.py    - Crash report writer
  selftest.py         - Release self-test (--selftest-saves): the built game saves, restores, seals a Seeker profile
  paths.py            - Path resolution helpers (dev and frozen)
  dev_tools/          - Developer-only previews

data/
  questions/        - Quiz question JSON files organized by subject
  monsters.json     - Monster definitions
  items/            - Item JSON files by category (weapon/armor/shield/accessory/artifact/flask...)
  hints.json        - In-game hint pool
  affinity_rules.json, family_affinity.json - The weak / resisted / shrugs-off steps; each family's lore profile
  enemy_lore.json, kit_sense.json - What Recall Lore, probing and the quests teach of a creature; Kit Sense's lines
  arsenal.json      - Coatings, thrown flasks, Press or Guard, the parry, the named counters
  lights.json       - Carried lights and the Light spell: status sight, spell turns, the oil, lines, card and HUD words
  gear_rules.json   - Armour and ring rules: thresholds, donning turns, load tiers, the light / heavy trade
  packs.json        - Packs: the hunt's numbers, the lore packs and their tricks, the herds that do not hunt as one
  monster_ai.json   - Monster behaviour (AI-1): healers, summoners, breath, morale, drain, rot, light, alarm, throes... numbers and lines
  traders.json      - The named traders: stock, services, stall counters, the smiths' inlays and linings
  stray_kids.json, abandoned_emberpup.json - Two of the run's set pieces (the Stray Kids stage; the Emberpup and Old Nickel)
  old_nickel.json   - Old Nickel's lines by phase and moment (the friend's offers and asides, the reveal, then taunts, iron, the cloak, darting in, striking, hurt, dying), their pacing and Journal lines
  mooble.json       - The Mooble: his floors, lines, the dance (windows, pass mark, phrases and tempi) and his pet species
  bococho.json      - The Bococho: the camp, Varro, the race's numbers and words, the pet, her saddlebags, riding
  songs.json        - Songs the hero plays: the track, its length, its power, its lines (from Brandon's lyrics)
  manifest.json     - Manifest: what the sketchbook can draw, the bite-type map, the quiz, INT + 5 turns a right answer, the cooldown
  (data/ holds only runtime JSON; the old generator/migration scripts were moved out)

assets/
  tiles/            - Tile graphics
  icon.ico          - Window icon
```

## Tech Stack
- Python 3.14 (Microsoft Store install on Windows)
- Pygame-ce — rendering, input, sound
- Tile-based graphics (64×64 sprite art, drawn on 40-pixel map tiles)
- JSON data files for questions, monsters, items

## Commands
- Run game: `python src/main.py`
- Run tests: `pytest tests/ -v` (parallel: `pytest tests/ -q -n auto`, about 1 minute; add `--run-slow` for the UI gates, about 6 minutes)
- Install dependencies: `pip install -r requirements.txt`

## Rebuilding a Quiz Bank
When the user says they want to build or rebuild a quiz bank for a subject — e.g. **"now we're going to do the theology bank"** — STOP and read **[`bankbuild/PIPELINE.md`](bankbuild/PIPELINE.md)** before doing anything else. It is the complete, authoritative, zero-to-shipped process: prerequisites (topic queue + subject config + the controlling voice rule), the batched build loop, the built-in prevention layers (deterministic gate + adversarial judge), the per-batch **de-tell sweep**, the pre-ship **moral-vision audit**, the **tone/kid-appropriateness audit**, the optional **deepen pass** for the tier curve, and merge → gate → promote → ship. Follow it exactly; do not improvise an ad-hoc process. The **history**, **philosophy**, **animal**, **cooking**, and **geography** banks are the reference implementations — see **PIPELINE.md §9–§12** for each build's additions (Grokipedia-first sourcing, the two-ladder-shape reframe, knowledge-subject de-tell, tone audit, the conditional deepen pass, the efficiency levers, and the multi-window wall-recovery). geography (§12) is the most recent and the closest template for another place/knowledge subject. **PIPELINE.md §13** is the subject roster — for any subject it names the KIND (knowledge / reasoning / snappy-rote), controlling voice, which de-tell rubric to fork, ladder-shape fit, and stance load; if Brandon is choosing what to build, §13 also carries the which-next recommendation (science is the current pick). Note: a subject's old `docs/quiz/subjects/<X>.md` may describe a design Brandon has since rejected (animal's did) — treat the config `voice_rule` + memory as authoritative, state your understanding back before building. **Before building any value-laden subject, read `docs/quiz/moral_vision.md` §3.10 (stance vs neutral — the no-verdict rule is NOT uniform) and bake the subject's stance into the config `framing` + topic `framing_note`s, not only the audit.** **Every topic ladder you build must ship with a TEACHING card in `data/question_contexts/<subject>.json`: WHO/WHAT/WHY orientation for a 10th-grader, then every rung's fact taught in story order, so a reader can answer the whole ladder (ruling reversed 2026-10-18; the old no-leak rule is retired). See `bankbuild/PIPELINE.md §16` and `bankbuild/cards/AUTHOR_SPEC.md`.**

## Development Rules
- **LORE, NOT FLOOR (Brandon, 2026-10-07; broken three times before it was written here).** Decide what a thing IS from its lore, then work out where in the progression that power belongs, and write it as real numbers in the base data. NEVER multiply damage or health by the dungeon floor at runtime, and never change an item's tier or base by depth. A weapon's maths tier is fixed (the material's for a common, its own for a unique). Hero weapons are unique artifacts and are meant to be unbalanced. If the early floors are too hard and the dice cannot go lower, change something else in `monsters.json` (to-hit, health, attack count). **No smoothing multipliers either (2026-11-19):** a blanket damage or health schedule written into the data (such as `tools/balance/scale_monsters.py` applying x1.85 to every ordinary monster on a band) is the same banned pattern. To fix a band, edit each monster, armour piece and drop there by its lore; simulator knob sweeps only measure where the curve is off. `tests/test_lore_not_floor.py` fails if game code multiplies by the floor or writes a weapon's tier.
- Keep code modular — one responsibility per file (main.py is a known exception, split planned)
- All questions and game data loaded from JSON files — no hardcoded content
- Commit after each working feature
- **Play-test rule**: when changing player-facing mechanics that are *easily reachable in a few minutes of play* (combat basics, equipping common gear, food prep, common UI), the user plays the game in person before the feature is "done". Claude can't drive Pygame from the harness, so unit tests and type checks do not prove the feature works — say so explicitly rather than claiming success.
- **When play-test isn't realistic**: for randomized loot, late-game content, deep-dungeon spawns, or probabilistic effects, play-testing is impractical. Write logic tests instead — at minimum a data-layer test (load the JSON and assert the mechanical fields are set correctly), and a pure-function test where the mechanic is implemented in a standalone module.
- **System-change sweep rule (added 2026-09-06)**: any time a game system is renamed, redesigned, or removed (masteries deleted, cook redesign, harvest v3→v4, lockpick v3, identify v3, etc.), do a **full-codebase grep for the OLD system's terms, symbols, field names, comment references, help text, message strings, and menu labels** — not just the direct call sites. Fix stale UI, tooltips, log messages, docstrings, and comments in the SAME commit as the mechanical change. Categories to check every time: (1) `src/game_render.py` (menus, panels, cards, lore screens), (2) `src/game_menus.py` + `src/fantasy_ui.py` (menu strings), (3) all `add_message(...)` / `_log_chronicle(...)` calls, (4) the help screen (`_draw_help_screen` in `src/game_render.py`) / help text, (5) docstrings + comments in `src/main.py` (which mixes many systems), (6) `src/mystery_system.py` challenge configs, (7) `src/quirk_system.py` descriptions, (8) any `data/*.json` schema fields. **Don't rely on tests to catch text-only regressions** — pytest won't notice a menu still says "5/5" when the system is now binary. When in doubt, ripgrep for the old term across ALL of `src/` and read every hit. Save-file compatibility with old written state is a separate concern (usually document as-is; only migrate on explicit user request).
