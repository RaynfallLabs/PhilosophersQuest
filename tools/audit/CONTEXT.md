# Philosopher's Quest — Audit Context Briefing

**Read this before doing anything.** This document is the shared briefing for every audit agent (CODE, BALANCE, FUN, BEAUTY, VOICE). Do not skim. The game's design intent — and the real-world stakes attached to it — are not derivable from filenames.

---

## 1. What this game actually is

Philosopher's Quest is a **graphical roguelike where knowledge is power**. Every meaningful action (swinging a weapon, equipping armor, reading a scroll, praying, picking a lock, casting a spell, harvesting a corpse, cooking food, identifying an item) routes through a **timed quiz**. The player's actual recall and reading speed — not RNG — determine the outcome.

**Lineage:** NetHack. Use NetHack as your soft external benchmark for depth, brutality, secret density, emergent behavior, and the principle that the game does not hold the player's hand.

**Audience:** The game is being built for the developer's kids. Question tiers map to school grades:
- **Tier 1 ≈ 5th grade**
- **Tier 2–3 ≈ middle school**
- **Tier 4 ≈ 8th grade**
- **Tier 5 ≈ high school (9th–10th)**

The kids playing are *younger* than these tiers. **Winning requires reaching above their current grade level.** This is the point.

**Real-world reward economy.** Major in-game milestones drop *codes* the player gives their father for real-world rewards. The code drop in `_trigger_abyss()` reads: *"Take this code to your father proudly — you have shown true Wisdom and Courage."* This means **difficulty is load-bearing**. If the game is beatable without genuine learning, the reward economy collapses. **"Too easy" is a P1 BALANCE finding, not a polish note.**

---

## 2. Subject → Action mapping (the spine)

| Subject | Action | Quiz mode | Frequency |
|---|---|---|---|
| math | Combat attacks | chain | Constant |
| geography | Equip armor/shield | threshold | Occasional |
| history | Equip accessory | threshold | Occasional |
| animal | Harvest corpses | threshold | Common |
| cooking | Prepare food | escalator_chain | Common |
| science | Magic / wands | escalator_chain (spells) / threshold (wands) | Occasional |
| philosophy | Identify items | threshold | Common |
| grammar | Read scrolls / spellbooks | threshold | Common |
| economics | Lockpicking | threshold | Occasional |
| theology | Praying | threshold | Rare but high-stakes |
| trivia | **Recall Lore** | escalator_chain | Player-initiated |

**Per-subject quiz timer** (`player.py:12-27`, `SUBJECT_TIMER`): math 16s ↔ theology 46s @ WIS 10. **These differences are intentional.** Math is the high-frequency combat tempo; theology is the slow contemplative pause. Treat the asymmetry as a feature.

WIS adds **+1 second per point above 10** to every quiz timer. Status effects modify the timer multiplicatively (`get_quiz_timer_modifier`), floored at 0.40x.

---

## 3. The three acts (and the secret fourth)

**Act I — Descent (Floors 1–99).** Procedurally generated. Player learns the loop, gathers gear, identifies items, builds out their character. Most runs die here. Floors 1–20 = learning; 20–60 = the main game where most runs live and die; 60–100 = endgame.

**Act II — The Boss (Floor 100).** **Abaddon.** Hand-crafted level (see `boss_levels.py`). Defeating Abaddon yields the **Philosopher's Stone** — the macguffin.

**Act III — The Escape.** The moment the player ascends from L100 carrying the Stone, `death_pursues = True` and a `DeathMonster` instance spawns. Death persists across floors (special-cased to survive save/load). Its speed escalates as the player climbs:
- 50% speed (initial) → 75% → 100% → 125% (faster than the player)
- Atmospheric messages at each tier ("Death quickens. The scraping is faster now.")
- **Prayer can freeze Death** for a number of turns (theology threshold quiz — a desperate measure during the chase, `game_divine.py:791`)
- Reaching floor 1 and exiting with Stone → `STATE_VICTORY` and a 50,000-point score bonus

**Act IV — The Secret Victory.** Combine **Philosopher's Stone + Tablet of Second Death** → **Complete Tablet of Second Death**. Standing on an Abyssal Shimmer with this artifact triggers `_trigger_abyss()`: the Abyss opens, Death is consumed, the player receives the **Scroll of Death's Bane** (sixth boss reward). Quote: *"Then Death and Hades were thrown into the lake of fire."* This is the maximum-difficulty ending and unlocks the most prestigious reward code.

---

## 4. Hidden systems are features, not bugs

The game has an enormous secret surface area. Examples already in code:
- **~80 named mythological/historical quirks** (`quirk_system.py:1097-1180`+) — each unlocks via a specific behavior. Examples: Prometheus, Odysseus, Buddha, Hypatia, Sisyphus, Norns, Ragnarok, Hermes, Cassandra, Persephone, Tantalus, Anansi, Penelope, Dionysus, Apollo, Athena, Loki, Thor, Beowulf, Jormungandr, Shiva, Enkidu, Perseus, Theseus, Sibyl, Valkyrie, Ahasverus, Circe, Gawain, Ariadne, Morgan, Cú Chulainn, Fenrir, Kali, Medusa, Green Knight, Narcissus, Cerberus, Spartacus, Ramanujan, Ibn Battuta, Tesla, De Medici, Leonidas, Confucius, Zoroaster, Boudicca, Solomon, Atalanta, Galileo, Caesar, Shakespeare, Nostradamus, Archimedes, Machiavelli, Darwin, Hypatia.
- **Power quirks**: philosophers_stone, atlas_burden, zeus_bolt, gorgon_ward, phoenix_rising, eye_storm, iron_will, battle_trance, second_sight, iron_ration, shadow_step, focused_scholar.
- **Hidden characters** (referenced in Tier 3 hints): a fire-bringer in a starlit robe sashed in gold; a bald simply-robed monk unfazed by hardship; a cunning wanderer in a hood who survived ten years at sea; a philosopher-mathematician in forest green with a love of numbers and harmonics.
- **A hidden debug terminal** referenced obliquely in a Tier 2 hint: *"Philosophers speak of a reality beneath reality — a hidden terminal that accepts a spoken word. The key to reach it is not listed in any help screen. It sits beside the number 1, quiet and overlooked."* (The backtick key.)
- **The Abyssal Shimmer** and the secret victory ritual.
- Hidden item interactions, altar mechanics, mystery encounters, easter eggs.

**The rule: hidden systems are HINTED at by Recall Lore, never directly explained.** Comments in code, UI tooltips, menu text, NPC dialog, and lore hints must preserve the mystery. **Direct spoilers in player-facing text are a P1 VOICE finding.** Hints should graduate in specificity by tier — T1 hints teach the basics, T5 hints reveal deep secrets.

---

## 5. Recall Lore — the in-game discovery vehicle

**Mechanic** (`game_magic.py:75-140`): trivia escalator-chain quiz, max chain 5. The chain score determines which hint tier the player receives (chain 0 = nothing; chain 5 = T5 hint). Cooldown scales with chain quality (longer cooldown for better hints — knowledge takes time to absorb). The **Norns quirk** halves cooldown after 20 lore uses.

**Hints** live in `data/hints.json`, keyed by tier "1"–"5". Current voice is exemplary geek-dad register:

> *"An Egyptian eye of blue faience mends what was torn. Patience is its method — the old gods do not hurry."*
> *"The Romans believed a certain shield fell from heaven and kept their city safe. Those who carried it thought more clearly under pressure."*
> *"Strange altars sometimes appear in the dungeon. Those who approach and kneel before them discover ancient challenges — and ancient rewards."*

**Required: every major strategic system or quest should have at least one lore entry at the appropriate tier.** Auditors should call out systems with no lore coverage as gaps.

---

## 6. The chronicle voice (the narrative spine)

`_log_chronicle()` writes first-person diary entries throughout the run. Tone samples already in the code:

> *"Something is following me. I felt it before I saw it. Death itself. I need to run."*
> *"I killed Death. The lake of fire opened beneath it and swallowed it whole. The silence afterwards was the loudest thing I've ever heard."*
> *"I made it. I climbed back out with the Stone. The sunlight hurt my eyes. I'd forgotten what it looked like."*
> *"Prayed while Death hunted me. It froze in place. {N} turns. That's all I get."*

This voice is **the game's voice**. Short sentences. Frank. Slightly Cormac-McCarthy without the violence pornography. Awe without bombast. Defeat without self-pity. Victory without triumphalism. **Every piece of player-facing text in the game should be evaluable against this register.**

---

## 7. Player stats and mechanical levers

- **STR** — Carry capacity
- **CON** — Max HP and SP (stamina)
- **DEX** — Armor class bonus
- **INT** — Max MP (mana)
- **WIS** — Quiz timer bonus (+1 second per point above 10)
- **PER** — Sight radius

**HP economics.** Food's `hp_restore` values are tiny (2–10) versus late-game player HP (500–800). The real heal path is **stair-rest** — resting on a stair tile heals over time. This is *intentional design*. Food's purpose is SP (stamina) and stat bonuses, not HP.

**Permadeath.** On any game-ending event, the save file is deleted (`save_system.delete_save`) and bones are written (ghost haunts future runs via `bones.py`). Save violations (load-then-crash exploits) are P2 CODE findings. **The existing `data/audit/consensus.json` already lists a known violation at main.py:8337** where `load_save()` does not delete the save immediately — this is a known issue but verify it remains.

**Quiz failure modes.** Threshold = must reach N correct or fail entirely. Chain = score is your chain length until first wrong (a chain of 0 is a "success with score 0"). Escalator versions ramp difficulty per round.

---

## 8. Enemy AI and dungeon "life"

The dungeon is meant to feel **alive**. Auditors must internalize the AI patterns:

- **aggressive** — moves toward player
- **sessile** — stationary (e.g., fungi, statues), can be alerted by noise
- **patrol** — moves on routes
- **ambush** — invisible until player gets close (`_aware` flag); see `main.py:1891`, `main.py:2004`, `game_render.py:1010`
- **hit_and_run** — engages then retreats (`game_combat.py:1381`)
- Container lockpicking alerts adjacent sessile monsters (`container_system.py:135` — narrow alerting is a known finding)

Beyond monsters, "dungeon life" includes:
- **NPCs** (`npc_encounters.py`) — dialog-driven, often quest-bearing or merchant
- **Flavor encounters** (`flavor_encounters.py`, `data/flavor_encounters.json`) — ambient scenes
- **Mystery system** (`mystery_system.py`) — random investigable events
- **Altars** — referenced in T2 hints, grant boons or curses
- **Containers** with locked loot (`container_system.py`)
- **Pet system** (`pet_system.py`) — bondable companion AI

**The world feeling alive is a FUN concern.** Findings on monotony, samey rooms, or absent ambient life are FUN-domain.

---

## 9. Existing prior audit work

`data/audit/` contains a previous single-dimension (CODE-only) consensus audit:
- `consensus.json` — P1–P4 confirmed findings (timer == 0.0 bug, heroism stacking, Monster.tick_effects never called, save-not-deleted-on-load, etc.)
- `systems.json`, `main_a.json`, `main_b.json`, `player_combat.json`, `world.json`, `content_systems.json` — per-agent raw outputs

**Treat these as a known baseline.** New CODE findings should not re-litigate items already in `consensus.json` unless the auditor is correcting them (false-positive flag) or extending them with new evidence. **Genuinely new bugs — single-system or cross-system — should be reported.**

---

## 10. Your hard rules

1. **Every claim must cite `file:line` evidence.** No hand-waving.
2. **Speculation is fine but must be flagged.** Mark unverified suspicions clearly so the consensus pass can resolve them.
3. **For BALANCE, FUN, BEAUTY, VOICE: findings must span ≥2 systems** (the holistic rule). Single-system polish belongs elsewhere.
4. **CODE is exempt from the holistic rule** — single-system bugs are in scope and must be reported.
5. **Severity bands** (shared, P1 = highest):
   - **P1** — Crash, data loss, game-breaker, savefile exploit, spoils a hidden system, breaks the difficulty contract, breaks the voice contract egregiously.
   - **P2** — Significant: silent feature failure, obvious imbalance, repeated UX friction, voice register drift in major text.
   - **P3** — Real but minor: edge-case bug, minor balance dip, polish issue.
   - **P4** — Nit.
6. **You write to disk.** Each finding goes in its own markdown file under `tools/audit/findings/<dim>/<id>.md` using the schema in your rubric. Required deliverables (BALANCE table, etc.) go in `tools/audit/deliverables/`.
7. **You are an Opus subagent.** Use Read, Glob, Grep liberally. Do not Edit or Write code — only audit findings and deliverables.
8. **Question banks are out of scope.** `data/questions/*.json` is NOT to be audited. VOICE looks at flavor text, NPC dialog, monster descriptions, hints, UI copy, encounter prose, status/combat/death messages — never bank questions.

---

## 11. Major files map (your starting points)

- **Game loop & state:** `src/main.py`, `src/game_states.py`
- **The 7 mixins (post-refactor):** `src/game_input.py`, `src/game_menus.py`, `src/game_render.py`, `src/game_magic.py`, `src/game_combat.py`, `src/game_divine.py`, `src/game_encounters.py`
- **Quiz engine:** `src/quiz_engine.py`
- **Player:** `src/player.py`
- **Combat:** `src/combat.py`, `src/game_combat.py`
- **Items:** `src/items.py`, `data/items/*.json`
- **Monsters:** `src/monster.py`, `data/monsters.json`
- **Magic/spells/wands:** `src/spells.py`, `src/game_magic.py`
- **Food/cooking:** `src/food_system.py`
- **Status effects:** `src/status_effects.py`
- **Dungeon gen:** `src/dungeon.py`, `src/level_manager.py`
- **Boss levels:** `src/boss_levels.py` (includes Abaddon at L100)
- **UI:** `src/ui.py`, `src/fantasy_ui.py`, `src/renderer.py`, `src/welcome_screen.py`
- **Quirks:** `src/quirk_system.py` (~80 quirks, ~1100 lines)
- **Hidden / scripted:** `src/npc_encounters.py`, `src/flavor_encounters.py`, `src/mystery_system.py`, `src/bones.py`, `src/pet_system.py`, `src/container_system.py`
- **Lore content:** `data/hints.json` (tiered 1–5)
- **Save/score:** `src/save_system.py`, `src/highscore_system.py`
- **Death chase mechanics:** search `death_pursues` across `src/`
- **Project rules:** `CLAUDE.md` (root)
