# Philosopher's Quest — Systems Reference

**v2.18.0** (shipped 2026-10-02)

The authoritative map of how Philosopher's Quest is wired. If you're changing a
system — gameplay, data, or UI — start here, read the one-paragraph summary
of the relevant doc, then open that doc.

If you are new to the codebase: read **[conventions.md](conventions.md) first**.
It is short and dense. Everything else makes more sense once you know the
cross-cutting rules.

---

## Architecture overview

**Three layers.** Philosopher's Quest is a tile-based roguelike built on
Pygame-ce where **every action is quiz-gated**. The game loop lives in
`src/main.py` as a `Game` class assembled from seven mixins
(`InputMixin`, `MenuMixin`, `RenderMixin`, `MagicMixin`, `CombatMixin`,
`DivineMixin`, `EncountersMixin`). Input routes through
`game_input.handle_event` to a state-dispatch table keyed on `Game.state`
(the `STATE_*` strings in `src/game_states.py`). Each state has a drawing
method on `RenderMixin` and an input handler on `MenuMixin` or
`InputMixin`.

Below the loop sit three parallel sublayers:

1. **Quiz-gate layer** — `quiz_engine.py` runs every player action that
   consumes a resource or applies an effect. Four modes: `threshold`,
   `chain`, `escalator_threshold`, `escalator_chain`. The engine is
   **zero-tolerance**: one wrong answer in any threshold-mode quiz ends
   that quiz. Chain v2 (combat only) lets a wrong answer close the chain
   at the achieved rank — the strike still lands.
2. **Mechanical layer** — `combat.py`, `food_system.py`,
   `container_system.py`, `game_magic.py`, `game_divine.py`,
   `status_effects.py`, `save_bonus_for`. These run after the quiz
   succeeds and own the dice.
3. **Data layer** — `data/*.json` loaded through `paths.data_path`. No
   hardcoded content in `.py`. Items, monsters, questions, recipes,
   outcomes, chest traps, and hints all live in JSON. The schema
   conventions are documented in [data_schemas.md](data_schemas.md).

Rendering is tile-based (64×64 PNGs in `assets/tiles/`, drawn on 40-px map tiles) composited by
`renderer.py` on a 1600×900 window (`layout.py`). All chrome goes through
`fantasy_ui.FP` (the single palette), `RenderMixin._ui_modal_panel` (the
modal frame), and `text_layout` (the single word-wrap / column-fit
helper). Overlay menus are drawn by `RenderMixin._draw_*` methods and
driven by `MenuMixin._*_input` + `MenuMixin._open_*` handlers.

Save/load is Pickle (per player name) via atomic temp-file replace;
dev/frozen path split through `paths.py`. Highscores and the crash
reporter are small, independent JSON/text siblings. See
[save_meta.md](save_meta.md).

---

## System docs

| Doc | What it covers | When to read |
|---|---|---|
| [conventions.md](conventions.md) | Zero-tolerance, chain v2, math-only timing, no-masteries, resource-loss-is-the-penalty, flow-over-gradient, save-bonus cap, karma clamp, SP floor, system-change-sweep rule | **Read first.** The orientation doc. |
| [quiz_engine.md](quiz_engine.md) | threshold / chain / escalator modes, zero-tolerance, per-run tier-clear auto-pass, timing | Any time you touch quiz flow |
| [combat.md](combat.md) | Chain v2 peak-chain formula, the hero's defence (AC, dodge, speed, the world's turns), hit resolution, _damage_multiplier, DR bypass tiers | Any combat change |
| [weapons_and_materials.md](weapons_and_materials.md) | 96 weapons, 11 materials, 149 uniques, chain-passive hooks | Weapon tuning |
| [monsters.md](monsters.md) | 527 monsters, AI patterns, boss / mini-boss flags, families | Monster add/edit |
| [monster_families.md](monster_families.md) | The 22 monster families, tiers earned by studying distinct kinds (keystones count two), the five tiers (Recognise, Forewarned, Lore, Hunter, Bane), technique primitives (`family_edges`), Circles, Loremaster, Bestiary gating | Family, Bestiary or technique change |
| [items.md](items.md) | Item classes, slots, equip, BUC, one identification knows every copy | Item schema change |
| [armour.md](armour.md) | AC from body armour and shield only, what armour does beyond AC (template forms, material elements, wards, light vs heavy: dodge, speed, noise, spell cost; the defence model, no Dexterity in AC; the load tiers), the minor slots' guard families and enchantments, the ring and amulet kinds, named pieces on the ladder, the 45 / 45 / 10 gear split, old saves (3.3.2) | Any AC, to-hit, armour, ring, weight or gear-loot change |
| [identify_v3.md](identify_v3.md) | One philosophy Q, derived id_tier, a known kind fully identifies every copy (2026-10-18), NO masteries | Identify flow change |
| [containers_lockpick.md](containers_lockpick.md) | Chest tiers, chest_traps.json, Lockpick v3 (1 Q, master pick, traps on fail) | Loot-gate change |
| [magic.md](magic.md) | Spells, wands, spellbooks, MP and meditation (Intelligence deepens the floor's quiet), magic as a style (the best spell of a tier is about one weapon chain; bands in `tools/balance/magic_audit.py`), MAGIC_TIER_MULT, dispatch | Spell add/edit, any spell or wand number |
| [food_system.md](food_system.md) | The kitchen (2026-11-14): kin ingredients (`harvest_map.json`), the recipe book (every ingredient in 3+ dishes), five kinds of meal (HP / SP / MP / Stat / Special) from `cooking_rules.json`, legendary feasts, the menu functions; harvest and cook (1 Q binary each), SP soft boundary | Food, ingredient, recipe or cook change |
| [status_effects.md](status_effects.md) | BUFFS / DEBUFFS / HARD_CONTROL, _RESIST_BLOCKS, SAVE_STAT, apply_debuff_with_save | Status effect add/edit |
| [save_bonus.md](save_bonus.md) | Gradient defense on CON/WIS/DEX/all, +5 cap, timed +3 cap | Save add/edit |
| [world.md](world.md) | Dungeon gen, mazes, terrain (water/ice/lava), bones, boss floors, cow level | Floor layout change |
| [pets.md](pets.md) | Species, specials, Duck transform, the six Soul Spheres (what each hatches, spawn bands, traders) | Pet add/edit |
| [progression.md](progression.md) | Quirks, hero specials, elder blood, secret builds, karma judgments | Progression add/edit |
| [quests_mysteries.md](quests_mysteries.md) | 9 quest chains + 12 mysteries + the Judgment altar | Quest add/edit |
| [economy.md](economy.md) | The income line, gold by lore (no coin in beasts), chests and coin piles, the named traders (plan, stock, worth-based prices, Buy / Sell / Services), services, purse-relative temptations, deeds pricing | Any gold, price, trader or shop change |
| [karma_prayer.md](karma_prayer.md) | Karma −10..+10 and the block cap (`karma.adjust`), 37 block anchors (at least three a block, each placed where its people could be: `reach`) + the story/flavor encounters, the Road, Setne's Tomb, prayer chain, divine intercession, judgment tiers | Karma / encounter / prayer change |
| [ui.md](ui.md) | Menus, HUD, help, bestiary, kit, discoveries, threshold copy helper | UI change |
| [save_meta.md](save_meta.md) | save_system (atomic pickle), highscore_system, crash_handler, paths.py, player.`__setstate__` migration | Save format change |
| [seeker_profile.md](seeker_profile.md) | The Seeker profile (the real player, across every run), achievements as data, reward codes for Dad and their key, the event spine, badge art | Achievement, profile or reward-code change |
| [data_schemas.md](data_schemas.md) | JSON conventions, `_meta` sub-object (v2.18), spawn tables, unidentified_name discipline | Data file edit |

---

## Quick lookup

Each row names the doc to open and the function or JSON file inside it
that answers the question. If the quick lookup disagrees with a doc,
the doc wins (and the row is a bug — please update it).

| Question | Open |
|---|---|
| "How do I add a monster?" | [monsters.md](monsters.md), `data/monsters.json` |
| "How hard is a mini-boss, and how do I retune one?" | [monsters.md](monsters.md) "Mini-boss tuning"; `tools/balance/mini_boss_bands.py` (the numbers), `tools/balance/mini_boss_fights.py` (the measuring) |
| "Where does a mini-boss live, how many does a run meet, and what does it drop?" | [monsters.md](monsters.md) "Mini-bosses by lore"; `tools/balance/mini_boss_seats.py` (the seats), `tools/content/mini_boss_drops_2026_11_17.py` (the drops), `level_manager.plan_mini_bosses` (one or two a band) |
| "How do I add a new quiz subject?" | [quiz_engine.md](quiz_engine.md), `data/questions/`, `fantasy_ui.FP.SUBJECT`, `player.SUBJECT_TIMER` |
| "What does chain-v2 do differently from v1?" | [combat.md](combat.md); peak-chain damage, miss = chain 0, wrong = strike-now |
| "How does a scroll get identified?" | [identify_v3.md](identify_v3.md); one philosophy Q at derived id_tier |
| "Where does damage math live?" | [combat.md](combat.md); `combat.player_attack`, `_damage_multiplier` |
| "How do AC, dodge, speed and the load work?" | [armour.md](armour.md) section 1c and [combat.md](combat.md) "The hero's defence"; `src/defence.py`, `data/gear_rules.json` `defence` and `load` |
| "How do coatings, thrown flasks, Press or Guard and the parry work?" | [combat.md](combat.md) "The arsenal's tools"; `coatings.py`, `stance.py`, `data/arsenal.json` |
| "What blocks a gaze, a voice or fey glamour?" | [armour.md](armour.md) 6b; `counters.py` (mirror shield, beeswax earplugs, cold-iron charm) |
| "Why does a piece I have worn before go on with no quiz? How long does plate take to put on?" | [armour.md](armour.md) 1b; `known_by_hand.py`, `game_dressing.py` (donning turns, the weapon At Your Back on S, the Loadouts on Shift+E), `busy.py`, `loadouts.py`, `data/gear_rules.json` `threshold` / `donning` |
| "What is a monster weak to, and where is it written?" | [combat.md](combat.md) "Weakness / resistance / shrugs off" and [monster_families.md](monster_families.md) "Affinity profiles"; `data/affinity_rules.json` (x2 / x0.5 / x0.25, cap x3), `data/family_affinity.json`, `affinity.py` |
| "What does the hero get told about a creature, and when?" | [monster_families.md](monster_families.md) "How knowledge is earned" and "The five tiers"; `affinity.py` (felt / habit / named lines), `enemy_lore.py` + `data/enemy_lore.json` (the Wand of Probing, which reads a creature and teaches its kind as a corpse study does, and the quests that teach the gate boss); Recall Lore is a random hint (`data/hints.json`), never about a creature, `kit_sense.py` + `data/kit_sense.json` (Hunter tier) |
| "What do the traders do for a build (stock for what is below, reforge, silvering, lining, trade-in, special orders)?" | [economy.md](economy.md) 4, 6 and "Stock that knows what's below"; `domain_counters.py`, `smithing.py`, `game_traders.py`, `data/traders.json` `counters` / `inlays` / `linings` |
| "How does an altar move a stat point?" | [karma_prayer.md](karma_prayer.md) 5.6 (Rededicate a Gift); `rededication.py`, `game_divine.py` |
| "Who is Old Nickel and why does the Emberpup want his cloak?" | [pets.md](pets.md) "The abandoned Emberpup"; `emberpup_encounter.py` (`BloomleafMixin`), `data/abandoned_emberpup.json`, `data/items/armor.json` `bloomleaf_cloak`, `data/monsters.json` `old_nickel` |
| "Who is the Mooble, and how does his dance work?" | [pets.md](pets.md) "The Mooble"; `mooble_encounter.py`, `game_mooble_dance.py`, `rhythm.py` (pure scoring), `data/mooble.json`; his tart is cooked to carry ([food_system.md](food_system.md) 5.5) |
| "How is the Bococho won, how does the race score, and how does riding work?" | [pets](pets.md) "The Bococho"; `bococho_encounter.py` (the camp, Gilt Varro), `race.py` (the scoring), `game_race.py` + `underway_run.py` (the side floor, 996), `riding.py` + `game_riding.py` (getting on, the two-tile step, set-downs, her saddlebags), `data/bococho.json` |
| "What statuses exist and how do resists apply?" | [status_effects.md](status_effects.md); `EFFECT_INFO`, `_RESIST_BLOCKS`, `apply_debuff_with_save` |
| "How do I add a save bonus from an accessory?" | [save_bonus.md](save_bonus.md); `_gear_save_bonus` + `Player.save_bonus_for` |
| "How do pets gain levels?" | [pets.md](pets.md); `Pet.gain_xp`; a pet's starting level comes from its sphere (`pet_system.hatch_level`) |
| "How does the Dreamspun Sketchbook's Manifest work?" | [pets.md](pets.md) 4.4, [ui.md](ui.md) 13b; `sketch_manifest.py` (pure rules), `game_manifest.py` (menu, quiz, spawn, QA Shift+V), `data/manifest.json`: draw any studied kind or one in view, bite typed as its first attack, INT + 5 turns a right answer |
| "What is Duck of Doom?" | [pets.md](pets.md); 10,000-turn transform in `main._duck_of_doom_transform` |
| "How does cooking work?" | [food_system.md](food_system.md); 1 Q binary at the dish's tier, numbers from `cooking_rules.json` (`kitchen.dish_outcome`) |
| "What is harvest v4?" | [food_system.md](food_system.md); 1 Q, `harvest_map.json` keyed by `monster.kind` |
| "Why did a harvest ask no question?" | [food_system.md](food_system.md) 8 (Butchered Before); `butchered.py`: a kind identified (its full Bestiary page open) and harvested right once, `Player.butchered_kinds` |
| "How does the lockpick trap fire?" | [containers_lockpick.md](containers_lockpick.md); `chest_traps.json` keyed by chest tier |
| "Where is the save file written?" | [save_meta.md](save_meta.md); `paths.save_dir()` dev vs frozen split |
| "Why isn't my old save loading?" | [save_meta.md](save_meta.md); `player.__setstate__` migration list |
| "What is the `_meta` block in JSON?" | [data_schemas.md](data_schemas.md); introduced v2.18 for `spawn_method` / `plot_locked` |
| "Why do spawn tables use peak_weight + spread?" | [data_schemas.md](data_schemas.md); Gaussian + explicit floor bands |
| "What is zero-tolerance?" | [conventions.md](conventions.md); any wrong answer ends a threshold quiz |
| "What subjects are timed?" | [conventions.md](conventions.md); math only (combat chain). Everything else untimed |
| "Which school grades is each maths tier?" | [../quiz/math_grade_curve.md](../quiz/math_grade_curve.md); `tools/balance/math_difficulty.py` scores, `py -m tools.balance.math_grade_curve` fixes |
| "What is the system-change-sweep rule?" | [conventions.md](conventions.md); grep OLD terms across all `src/` in same commit as mechanical change |
| "Where does help text live?" | [ui.md](ui.md) §17; `game_render._draw_help_screen` (page 1, the key map) and `data/ui/how_quizzes_work.json`, `data/ui/gear_and_load.json` (pages 2 and 3, `RenderMixin.HELP_PAGES`) |
| "How is the sidebar built?" | [ui.md](ui.md); `ui.Sidebar._identity/_vitals/_attributes/_derived/_effects/_powers/_in_sight` |
| "Why is a potion I never identified showing its true name and blessing?" | [identify_v3.md](identify_v3.md) §1 top: a known kind fully identifies every copy (`items.is_fully_known`) |
| "How do mystery altars gate challenges?" | [quests_mysteries.md](quests_mysteries.md); `MYSTERIES` dict in `mystery_system.py` |
| "What is the Stray Kids idol / the Zombie Stage / the dance-off?" | [monsters.md](monsters.md) (Special monster modules) and [world.md](world.md) §6.6a; `src/stray_kids.py`, `src/game_stray_kids.py`, `data/stray_kids.json`; the dance screen is the Mooble's (`game_mooble_dance.py`, `rhythm.py`) |
| "Where is karma clamped?" | [karma_prayer.md](karma_prayer.md); `karma.adjust` (`src/karma.py`), −10..+10, +1 per 10-floor block |
| "What does `plot_locked` do in item JSON?" | [data_schemas.md](data_schemas.md); documentary only — real gate is `min_level: 9999` + custom spawn code |
| "How does the welcome screen pick a build?" | [progression.md](progression.md); `welcome_screen.SECRET_BUILDS`, `_qa_tools` gated by `PQ_QA_MODE=1` or `--qa` |

---

## Audit history

The system docs are the forward-looking reference. The audits are the
snapshot of findings at a point in time — kept because they still name
every known bug and dead field.

- **[SYSTEMS_AUDIT.md](../../SYSTEMS_AUDIT.md)** — 2026-09-27 full
  systems audit (10 agents, ~330 findings, 8 P0, ~25 P1, ~40 P2, ~200
  P3–P5). Scope: every monster, item, quest, mechanic, UI element.
- **[ITEM_QUIZ_AUDIT.md](../../ITEM_QUIZ_AUDIT.md)** — 2026-09-24 item
  + quirk audit. 25 Dad-reward scrolls, 18 non-math timer quirks, 10
  container thresholds, ~166 ingredient/prime-cut `temp_desc` fields.
- **[ANSWER_CORRECTNESS_SUSPECTS.md](../../ANSWER_CORRECTNESS_SUSPECTS.md)** —
  2026-09-19 full-coverage answer-correctness audit.

Fixes from these audits ship in the version bump that mentions them in
`git log` (e.g. v2.18.0 "Full systems audit + fix wave").

---

## Where to find the code

- **Game loop + mixin assembly:** `src/main.py` (`class Game(InputMixin,
  MenuMixin, RenderMixin, MagicMixin, CombatMixin, DivineMixin,
  EncountersMixin)`).
- **State dispatch:** `src/game_input.handle_event` → per-state
  `_*_input` methods on `MenuMixin` / `InputMixin`.
- **Rendering:** `src/game_render.RenderMixin._draw_*` methods, one
  per `STATE_*`.
- **UI theme:** `src/fantasy_ui.FP` (palette), `RenderMixin._ui_modal_panel`
  in `src/game_render.py` (modal frame), `src/text_layout` (wrap / truncate / column-fit).
- **Data:** `data/` (all read-only JSON), `assets/tiles/` (PNGs).
- **Entry point:** `python src/main.py` (not the bundled exe — "run it"
  means source, per the user's memory rule).

---

## Project rules worth repeating

- Every quiz-gated action **consumes the target** when it fires. The
  resource loss **IS** the penalty. Don't stack stuns on cook / harvest
  / lockpick fails — the lost corpse / ingredient / chest tier is the
  cost. (Identify's stun exists because identify is the one action that
  doesn't consume the item.)
- **No masteries of the old kind.** All three mastery systems (class,
  family, identify) were removed on 2026-08-06; see `player.__setstate__`
  in [save_meta.md](save_meta.md) for the migration list. Three later rules
  keep what the hero has learnt this run, and are allowed because each is
  one plain rule with no ladder of growing numbers: philosophy tier
  mastery (`src/philosophy_mastery.py`: every question of a tier answered
  right names that tier's items), **Known by Hand**
  (`src/known_by_hand.py`, 2026-11-13: a kind of gear put on once goes on
  again with no quiz) and **Butchered Before** (`src/butchered.py`,
  2026-11-17: a kind identified and harvested right once is harvested
  again with no question). Any other "mastery" vocabulary in UI, log or
  JSON is a stale string: fix it.
- When a game system is renamed, redesigned, or removed, **grep the OLD
  terms across all of `src/` in the same commit as the mechanical
  change.** Pytest won't catch text-only rot. See
  [conventions.md](conventions.md) "system-change-sweep rule" for the
  file list.
