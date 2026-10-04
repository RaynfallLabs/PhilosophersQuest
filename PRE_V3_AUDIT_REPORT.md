# Pre-v3.0 audit report

Started 2026-10-04 on v2.23.0 (`1809db7`). Five read-only reviews (UI dead code, stale text, core-system bugs, world-system bugs and data, context blurbs), then fixes. Status column: **FIXED** (in the commit named), **OPEN** (not yet done), **DECIDE** (needs Brandon's call), **KEEP** (reviewed, left on purpose).

Line numbers are as of `1809db7` unless a fix moved them.

---

## 1. Bugs in core systems

| # | Problem | Where | Status |
|---|---|---|---|
| B1 | Window-X (or a stray QUIT from monitor sleep / focus loss) during a quiz goes to confirm-exit; cancelling returns to STATE_PLAYER, so the quiz callback never fires. Escapes a failed identify stun, a combat miss, a failed scroll or prayer; can also strand `combat_target` and spent ammo. | `game_input.py` QUIT handling + confirm-exit cancel | OPEN |
| B2 | ESC during the Necronomicon quiz calls `quiz_engine._end`, which re-fires the PREVIOUS quiz's callback (e.g. a second `_on_monster_killed`: duplicate loot/corpse) and leaves `_necro_qs` live so the next real quiz is routed to the Necronomicon handlers. `_end` has no already-ended guard. | `game_input.py` ESC branch; `game_magic.py` Necronomicon flow; `quiz_engine._end` | OPEN |
| B3 | Equipping a weapon while the wielded one is cursed (or Stormbringer) silently fails inside `_apply_equip`, but the caller still removes the new weapon from the pack and prints "You equip…". The new weapon is destroyed. | `main.py` `_equip_item` weapon branch; `player.py` `_apply_equip` | OPEN |
| B4 | Monsters killed by chain-special AoE / splash (glaive, 2H sword, axes, spear, halberd, crossbow, sling, 2H warhammer, Mjolnir, Zulfiqar, Gandiva) are never passed to `_on_monster_killed`: no message, loot, corpse, kill count, seal or boss story. | `combat.py` AoE blocks; `game_combat.py` on_complete | OPEN |
| B5 | Curtana's spare leaves `_spared_this_attack` set, so the NEXT real kill prints the mercy line and skips loot/corpse/boss handling while the monster is dead. `_spare_kill_floor_hp` is never reset, so the "per floor" +5 max HP cap is lifetime. | `combat.py` Curtana block; `game_combat.py` `_on_monster_killed` | OPEN |
| B6 | Slings (and any `infinite_ammo` ranged weapon) fire using the MELEE weapon's stats, because `player_attack` picks the weapon from `ammo` and slings pass `ammo=None`. HUD previews the sling, result uses the sword. `free_stones` ricochet is dead on the ranged path. | `combat.py` `player_attack`; `game_combat.py` `_fire_ranged` | OPEN |
| B7 | Tablet of Destinies reroll flag is sticky: set by combat, read by EVERY quiz, consumed only by melee. While unspent, every identify/lockpick/equip/prayer/scroll quiz gets a free mulligan; a ranged-only player keeps it forever. Also `self.chain = max(self.chain, 1)` gives a free chain 1 after a wrong first answer. | `quiz_engine.py` `_reroll_flag`; `game_combat.py` | OPEN |
| B8 | Unequipping a weapon never reverses its passives or on-equip status. Equip/unequip Hofud for +2 PER each cycle; Pelops Sword +2 max HP each cycle; Curtana's `blessed` survives unequip. | `main.py` `_unequip_slot`; `player.py` `_remove_weapon_passives` | OPEN |
| B9 | C (context) pauses the math combat timer: a free pause to work the sum. | `game_input.py` | KEEP: Brandon chose "pause, like other subjects" on 2026-10-04 knowing the trade-off. |
| B10 | ESC during the result flash turns a PASSED quiz into a failure (correct identify then impatient ESC = stunned). | `game_input.py` ESC branch | OPEN |
| B11 | `weakened` quarters damage (halved twice) instead of halving. | `combat.py` two weakened checks | OPEN |
| B12 | Chain-equip "permanent" statuses are written as 999 turns and tick down while still worn (Winged Sandals haste, Tyet of Isis life_save, Sigurd's Mail fire_resist, 9 items). Gone after 3-4 floors. | `chain_equip.py`; item data | OPEN |
| B13 | `tick_all` re-adds an effect removed mid-tick (poison damage wakes you, then the loop writes `sleeping` back). | `status_effects.py` `tick_all` | OPEN |
| B14 | Confirming a targeted spell on an invalid tile loses the MP (the ESC path refunds, this path does not) and leaves `_pending_spell` set. | `game_combat.py` target confirm | OPEN |
| B15 | Duplicate dict keys in `_EXPIRE_MSGS` (`warning`, `searching`, `truesight`, `dark_vision`): the earlier messages are dead. | `status_effects.py` | OPEN |
| B16 | `proper_name` capitalises small words inside hyphenated names ("Will-O'-The-Wisp"). (Leading-article capitalisation of unidentified descriptions is intended: Brandon chose to keep descriptions capitalised.) | `naming.py` | OPEN (hyphen part only) |
| B17 | Armor `chain_bonus`, `_chain_carry` and Glamdring's bonus are added before the chain-0 miss check, so a miss can become a hit; Parashu's carry stores the already-carried total and compounds. Intent unclear. | `combat.py` ~883-902, ~1600 | DECIDE |
| B18 | Throwing Broken Gram over Odin's altar advances the turn twice. | `game_combat.py` ~291/309 | OPEN |
| B19 | Quiz scroll offset resets per quiz, not per question: a scrolled long question leaves the next one starting scrolled. | `quiz_engine.py` | OPEN |
| B20 | `id()`-keyed marks (`_death_omen_target`, `_et_tu_target`, `_revealed_tag_ids`) are pickled with the Player; after reload the ids are stale and can match an unrelated monster for +25%/+50% damage. | `combat.py`; `player.py` `__getstate__` | OPEN |
| B21 | Identify Sight sets `id_level` 4, not 5: the item shows as "Unidentified <name>", stays in the Identify menu, and the dossier says Unidentified, though the status says "auto-identified". | `main.py` ~4237 | OPEN |
| B22 | HUD and menus disagree on names for `id_level` 4 items (HUD tests `item.identified`, menus test `>= 5`). Any `x.identified = True` lands on 4 (wand zap, potion quaff, Ariadne special). | `hud_context.py`; `items.py` identified setter | OPEN |
| B23 | Item dossier ignores type knowledge: a known-type copy shows "Mechanics unrevealed" and hidden lore, while the Kit panel shows its stats. | `game_render.py` `_lore_direct_id_level` | OPEN |
| B24 | Harpe's petrify at chain 15+ has no log line: `petrified = crit and …` is always False since crits were retired. | `combat.py`; `game_combat.py` | OPEN |
| B25 | Apollo quirk "perfect max chain 10 times" checks `score >= len(chain_multipliers)` (3-6 on uncapped weapons), so it unlocks far too easily. Musashi and Jormungandr quirks are no-ops on polynomial-chain weapons. | `quirk_system.py` | DECIDE (needs a design answer for the two no-op quirks) |

World-system bugs and data cross-checks: see section 5 (review still running when this was written).

## 2. Dead code

| # | What | Size | Status |
|---|---|---|---|
| D1 | 31 unreachable legacy bodies after an unconditional `return` in `game_render.py`. | 2,064 lines | FIXED `43f9aee` |
| D2 | `src/panel.py` (PanelBuilder): only callers were in D1. Kept alive by tests only. | 335 lines + tests | OPEN |
| D3 | `fantasy_ui.draw_menu`, `draw_tab_bar`, `wrap_text` ("UNIVERSAL MENU RENDERER"): only callers were in D1. Tests: `test_menu_scroll.py`, `test_menu_detail_wrap.py`. | ~380 lines + tests | OPEN |
| D4 | Old Kit table renderer: `_draw_measured_table`, `_kit_draw_items`, `_kit_draw_spells`; `text_layout.fit_columns` then has no production caller. Test: `test_menu_column_render.py`. | ~190 lines + test | OPEN |
| D5 | `_draw_npc_encounter` legacy tail + `_draw_npc_wordwrap` + `_wordwrap_text`. | ~125 lines | OPEN |
| D6 | `context_lines` param of `_draw_decision_menu_variant_a` is ignored; 8 callers build it every frame; `_menu_base_context`, `_menu_tile_label` die with it. | ~80 lines | OPEN |
| D7 | Menu builders still carry A/B-experiment names (`_draw_decision_menu_variant_a` documented as "Variant B", `_draw_fast_picker_variant_b`). | rename | OPEN |
| D8 | `scroll_attr` param is write-only; 7 `_*_scroll` attributes never read. | small | OPEN |
| D9 | Cook "single" tab leftovers: `is_compound` always True; dead else-branch, `_cook_tab_has_items`, no-op tab cycling, `cook_menu_items`, `main._cook_item`. | ~100 lines | OPEN |
| D10 | `_fit_text`, `game_helpers.fit_text`: users were all in D1. | small | OPEN |
| D11 | Zero-caller methods: `_draw_tab_bar`, `_ui_row`, `_menu_draw_resource_bars`, `_draw_page_indicator`. | ~105 lines | OPEN |
| D12 | Vestigial camera plumbing: `_camera()` always (0,0); `cam_x`/`cam_y` accepted and ignored in ~15 places. | refactor | DECIDE (not a pure delete) |
| D13 | Unused palette constants in `fantasy_ui.FP` (9 zero-ref, 5 dead-tail-only, 3 test-only). | small | OPEN |
| D14 | `_menu_item_detail_lines(action=...)` param ignored. | small | OPEN |
| D15 | Stale `_draw_shop` and `fantasy_ui` module docstrings. | text | OPEN |
| D16 | `_menu_recipe_preview` legacy `tier_outcomes` fallback (no recipe carries the key). | ~20 lines | OPEN |
| D17 | Unused imports / locals across `src/` (ruff F401, F841, F541). | ~35 sites | OPEN |
| D18 | `hud_context.item_known_to_player`, `text_layout.text_block_height`: zero references. | small | OPEN |
| D19 | `Renderer._player_sprite`, `vw`, `vh` written and never read. | small | OPEN |
| D20 | `_scroll_identify_blessed` write-only (identify-v3 leftover). | 4 lines | OPEN |
| D21 | Auto-open context plumbing (`_check_context_auto_open`, `pending_context_auto_open`, `_quiz_context_seen`): set then discarded every frame. | ~40 lines + tests | OPEN |
| D22 | `special_blessing` read in a kit panel; exists nowhere else. `Weapon.crit_multiplier`, `monster.harvest_threshold`: inert fields. | small | OPEN |

## 3. Stale or unpolished player-facing text

| # | Problem | Where | Status |
|---|---|---|---|
| T1 | Dossier text still describes multi-level identify ("Identify this item further…", "to lore tier", "Study further", "Reach full identification"). | `game_render.py` lore/kit panels | OPEN |
| T2 | Equip menu shows `chain x{max_chain_length}`, a cap that no longer exists; weapon class raw lowercase. | `game_render.py` | OPEN |
| T3 | "Crit" wording after crits were retired: Rally special, hint 163, status "Critical Resolve", prime-cut and ingredient descriptions. Real effect is +50% on the next attack. | `hero_specials.py`, `status_effects.py`, `data/hints.json`, `data/items/prime_cuts.json`, `ingredient.json` | OPEN |
| T4 | Cook buff message prints raw status ids ("A short crit buff lingers."), and the menu preview names the same buff differently. | `food_system.py`, `game_render.py` | OPEN |
| T5 | Mystery altar card and attunement panels show engine mode names ("Escalator Threshold", "Escalator Chain") and a lowercase subject. | `game_render.py` | OPEN |
| T6 | Hints describing removed mechanics: 200 (career arc order), 77 (solo vs compound cook), 51 (graded cooking), 105 (study bonus), 36/73/123 (identify tier rule), duplicates 104=122 and 107~173, 134 vs 206 ("a god's sandal"). | `data/hints.json` | OPEN |
| T7 | Quirk text uses old cook "quality-0 / quality-5". | `quirk_system.py` | OPEN |
| T8 | Combat log says "Chain xN!" while the header says "xN". | `game_combat.py` | DECIDE (log wording may be meant to differ) |
| T9 | Study mode still shows "CORRECT!" / "INCORRECT". | `study_mode.py` | DECIDE (study mode may be exempt) |
| T10 | Quiz title separators inconsistent (single vs double space around `--`); "ANIMAL LORE"; "COOKING X  --  COOKING". | 13 title sites | OPEN |
| T11 | Key-hint formats differ between combat and non-combat quizzes and across screens. | `game_render.py` and others | OPEN (quiz); DECIDE (game-wide convention) |
| T12 | Help screen omits the quiz keys C (context) and PgUp/PgDn (scroll). | `game_render.py` help | OPEN |
| T13 | Raw or lowercase ids still shown in panels ("grants fire_resist", raw BUC, slot, item_class, tags, resists, ammo type). | ~15 sites in `game_render.py` | OPEN |
| T14 | "Odin's sacrifice: 1 HP for 1 WIS." (it costs 1 MAX HP; "sacrifice" brushes the no-sacrifice rule). | `main.py` | OPEN |
| T15 | Harvest success says "(T{tier}/5)", which reads like a graded score. | `food_system.py` | OPEN |
| T16 | Comments/docstrings describing auto-open, old identify levels, mastery thresholds, escalator lockpick, crits. | several files | OPEN |

## 4. Context ladders

Deterministic checks ran over all 3,543 ladder blurbs; 60 topics were read in full; all 27 math cards were recomputed.

**Clean:** every topic with questions has a blurb; formatting is clean in all ten subjects; no math card has an arithmetic error.

| # | Problem | Scale | Status |
|---|---|---|---|
| C1 | **Answer leaks, economics.** Blurbs are ladder summaries with keyed answers pasted in. | 688 rungs (21%) across 256 of 345 topics; 34 topics leak half or more of their ladder | DECIDE (content rebuild) |
| C2 | **Answer leaks, theology.** Blurbs retell the story including the beats the rungs ask about. | 263 rungs across 171 topics | DECIDE (content rebuild) |
| C3 | Answer leaks, geography and animal: the first sentence states the T1 answer (the superlative, or the animal's name). | 174 and 105 rungs, mostly T1 | DECIDE |
| C4 | Answer leaks, trivia (mega-topics up to 125 questions under one blurb), history (90), science (58), cooking (52), ai (7), philosophy (5). | see counts | DECIDE |
| C5 | **ai `topic` tags are wrong at scale**: about 40% of ai questions sit under an unrelated topic, so C shows an irrelevant blurb (`yoshua-bengio`, `data-brokers-location`, `claude-and-anthropic`, `snowden-and-surveillance`, `rag-retrieval`). Smaller version in trivia (`akira`, `osamu-tezuka`, `mcu-through-endgame`). | ~40% of ai | DECIDE (re-tag pass) |
| C6 | 35 history questions (three ladders: 1991 Soviet collapse, Berlin Wall, Gorbachev) and 3 trivia questions have no `topic`, so no blurb can show. | 38 questions | OPEN |
| C7 | Blurb length: all of theology, geography, animal and cooking are under 120 words (cooking median 53) against a 200-400 spec; PIPELINE §16 says both "3-5 sentences" and "200-400 words". | 1,486 blurbs | DECIDE (pick the spec first) |
| C8 | Author-facing language in player text: "This ladder passes through…" (economics, 330 blurbs), "the ladder / rungs / sub-strand / the bank" (science), "the kid" (ai 40), "geek-dad canon / spoiler-OK / stance docs / the user's kids" (trivia), "no verdict crowned" (philosophy 42). | ~900 blurbs | DECIDE (rewrite pass) |
| C9 | No blurb gate exists: `bankbuild/bank.py` has no blurb check, and only math has a data test. | — | OPEN (add coverage test; leak test as a ratchet) |
| C10 | Orphan blurbs: 9 in ai, 2 in philosophy. | 11 | OPEN |
| C11 | Factual: `battle-of-okinawa` ("last land battle of the Second World War"; "home-island"); `the-hockey-stick-fight` calls McIntyre a "statistician" against its own keyed answer. | 2 blurbs | OPEN |
| C12 | Math cards: "Sum of 1 to N" says n/2 pairs (fails for odd n); "Negative Numbers" "two minus signs make a plus" invites misuse; Rounding rollover; three-decimal rounding; Exponent Rules example stops unevaluated; "Simplifying Fractions" is all ratios. | 6 cards | OPEN |
| C13 | History: 35 blurbs use killed/assassinated/executed with no actor named (active-voice rule). Three theology phrasings read as insider language. | ~38 blurbs | DECIDE |

## 5. World systems and data

Confidence note from the reviewer: W1-W8, W12-W15, W21 (spawn half), W24, W25 were verified against code or by simulation; W9-W11, W16-W20, W22, W23 rest on a second-level read and are one step less certain.

| # | Problem | Where | Status |
|---|---|---|---|
| W1 | **Crash:** `grave_knight.rage_damage_bonus` is the int `4`; `dice.roll` needs a string. Game crashes when an enraged grave knight (peak floor 55) lands a hit. | `data/monsters.json`; `monster.py` ~552, ~1528 | OPEN |
| W2 | **Softlock + repeatable reward:** mystery-altar quiz callback never sets `STATE_PLAYER`; ESC then re-fires the callback (Pandora pays out each time). | `game_divine.py` `_on_mystery_complete` | OPEN |
| W3 | **Quest-breaking:** hidden treasure chambers call the whole of `spawn_items` a second time, which re-carves shrines/altars and overwrites the dungeon's quest pointers. In simulation ~50% of floors at L17 (Ariadne), L37 (Athena), L53 (Odin), L76 (forge), L79 (Vidar), L99 (judgment) end up pointing at an empty or secret-chamber structure. | `level_manager.py` ~361; `dungeon.py` `spawn_items` | OPEN |
| W4 | Quest altars overwrite the down stairs (~5% each on L74/76/79/99); Gleipnir lava/water rings and swamp rooms can cut the stairs off (13-14% on L68/L71). | `dungeon.py` ~2500-2576, ~1803 | OPEN |
| W5 | Vidar's Altar removes 10 leather scraps, then looks for `vidars_sandal` in `armor.json` (it is in `artifact.json`): scraps destroyed, nothing given. | `game_divine.py` ~575 | OPEN |
| W6 | Level 100 has no altars (the room carve overwrites all six), so the Abaddon holy-fire prayer cannot be used. | `boss_levels.py` ~497-520 | OPEN |
| W7 | Quest/story items leak from random pools because they have `min_level` 0/1: chests can give the Philosopher's Stone, Gleipnir, demon seals, Scales of Michael; Divine Intercession picks uniformly from all artifacts (~1 in 28 the Stone); NPC rewards and merchant use the same filter; nine story accessories can drop on the floor from L1. | `container_system.py`, `game_divine.py`, `game_encounters.py`, `mystery_system.py`, `dungeon.py`; item data | OPEN |
| W8 | Most trophy "permanent powers" do nothing: they add statuses nothing reads (`petrify_immune`, `fire_immune`, `cold_immune`, `poison_immune`, `confuse_immune`, `auto_reveal_secret_3`, `acid_resist`, `_blood_archon_lifesteal`). Messages still claim the power. | `food_system.py` ~349-399 | DECIDE (map to live effects vs add readers) |
| W9 | Pets attack and kill allied NPCs (the cow, unicorn, moral-encounter NPCs, Heavenly Host). | `pet_system.py` ~465; `game_combat.py` swipe loop | OPEN |
| W10 | Monsters killed by reflect damage skip kill processing (no loot, count, boss/seal tracking). | `monster.py` attack; `game_combat.py` ~1938 | OPEN |
| W11 | Fear/confusion/blind are ignored by every special AI pattern (~136 monsters); `charmed` and `immobilized` have no monster-side reader at all; flee-when-hurt uses `max_hp > 500` instead of `is_boss`. | `monster.py` ~821-965 | DECIDE (behaviour change across many monsters) |
| W12 | Travelling merchant only spawns on the DOWN STAIRS tile (`== 3` where FLOOR is 1): ~1.7% of floors instead of 20%. | `mystery_system.py` ~662 | OPEN |
| W13 | Barracks rooms draw uniformly from weapon/armor files that are now all uniques, handing out named uniques (including quest rewards). | `dungeon.py` ~1790 | OPEN |
| W14 | Boss-drop uniques (`ruby_rod`, `scroll_of_nine_hells`, `scroll_of_chromatic_doom`) are common floor loot at F85+; uniques are 39% of magic drops at L90. | `dungeon.py` ~1464; item data | OPEN (the three boss drops); DECIDE (unique accessories generally) |
| W15 | Bones files lose almost all gear: composed ids (`iron_longsword`) are not in the item files, so the ghost's ordinary gear vanishes. | `bones.py` ~211 | OPEN |
| W16 | Multi-attack bosses never apply on-hit effects (Asmodeus, Surtur, Ymir, Hrungnir). | `monster.py` `_fenrir_multi_attack` | OPEN |
| W17 | Mysteries repeat within a run (no once-per-run tracking, though the docstring promises it): the Sphinx averages ~2.5 completions. | `mystery_system.py` ~270 | OPEN |
| W18 | Recalling a pet while over carry capacity deletes the pet. | `game_menus.py` ~1898 | OPEN |
| W19 | Hero specials: Theseus chains 2-5 call nonexistent `dungeon.is_door` / `game.explored` (caught; burns the cooldown); Ash Ketchum chain 5 reads `pet.status_effects`; Ash Williams chain 5 adds permanent +2 STR every cast. | `hero_specials.py` | OPEN |
| W20 | Quirks: permanent quirk status popped when a matching accessory is unequipped; Cu Chulainn fear immunity never applies (`> 0` vs stored -1); Zeus' Bolt and Gorgon Ward unreachable; Eye of the Storm unlocks for everyone on the 6th stair; `wanderlust_active` unread; Fisher King measures HP after the heal. | `main.py`, `player.py`, `quirk_system.py`, `game_divine.py` | OPEN (first two); DECIDE (rest) |
| W21 | 2x2 monsters are checked only at their anchor tile: mini-bosses can spawn half in a wall and walk onto pets/monsters. | `level_manager.py`, `monster.py` | OPEN |
| W22 | NPC "return the item" options never check the player still holds the item. | `npc_encounters.py`, `game_encounters.py` | OPEN |
| W23 | Displacement is rolled twice per monster attack (51% miss instead of 30%). | `game_combat.py` ~1933; `monster.py` ~521 | OPEN |
| W24 | 108 composed gear names collide ("Adamantine Shirt" is both a chain shirt and a padded shirt, different slots and AC), because `compose_item_name` strips generic words. | `items.py` `compose_item_name` | DECIDE (naming) |
| W25 | Three ingredients (`asterion_minotaur_prime`, `fenrir_wolf_prime`, `blood_archon_prime`) and the eight recipes that need them can never be obtained; `ancient_lich` never spawns. | data | DECIDE |
| W26 | Smaller items: Black Cauldron counts stacks not meals; `enchant_weapon` rewards charge with no weapon equipped; "Fifty gold" text charges 80; Sisyphus 15 vs 25 tiles; special-room atmosphere messages never show; 14 armor-only materials roll as shields; duplicate unidentified names (wand, three scroll pairs, a spellbook); two spellbook `mp_cost` mismatches; `MAX_EFFECT_DURATION` 60 clips two prayer outcomes; Army of Darkness deadites lose their HP override; Abaddon stops spawning locusts at 40% HP; `min_hit_chance` never loaded; dead `summon_kind` on four monsters. | various | OPEN / DECIDE per item |

**Cross-checks that came back clean:** all 527 monsters resolve to a prime cut or trophy; 893 recipes / 1,421 ingredient refs resolve; all starting kits instantiate; all monster drop and summon ids exist; every wand, scroll, potion and spell effect has a handler; no duplicate ids or negative weights; 1,299 template/material combinations compose; all boss levels have reachable stairs and boss; 102 quirks of which 98 have reachable triggers.

## 6. Housekeeping

- Repo root holds ~15 finished plan/audit documents, two save files and log files. Candidates for `_archive/`: DECIDE.
- `docs/systems/*` still describe v2.22.0: a docs-sync task is queued separately.
