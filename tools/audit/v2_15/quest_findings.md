# v2.15.0 Quest-Chain Audit — Findings

Read-only audit of quest chains, character quirks, boss encounters, and endgame
wiring. No code changes performed. All source refs are absolute paths on
Windows; line numbers are from HEAD.

Severity rubric:
- **P0** — crash / softlock (impossible to complete).
- **P1** — quest reward never granted, character quirk silent, seal drops but
  does nothing.
- **P2** — quest works but reward is trivially weak (dead balance).
- **P3** — quest message stale / mentions removed system.
- **P4** — nit.

## Severity counts

| Severity | Count |
|----------|-------|
| P0       | 0     |
| P1       | 2     |
| P2       | 0     |
| P3       | 1     |
| P4       | 1     |

Total findings: **4**.

---

## End-to-end quest walkthroughs (confirmed)

### 1. Broken Gram → Reforged Gram — WIRED
- Broken Gram spawns on L48 (`src\dungeon.py:1799`, gate: `level == 48`).
- Odin Altar spawns on L53 (`src\dungeon.py:2057` `_create_odin_shrine`, gate
  `level == 53`, sets `dungeon.odin_altar_pos` + `odin_shrine_door`).
- **Throw-over trigger**: `src\game_combat.py:293-315` — throwing weapon
  `broken_gram` on a trajectory that crosses `odin_altar_pos` calls
  `_activate_odin_shrine(weapon, reforge=True)` which consumes the broken
  blade, spawns a full-quality `gram` on the altar, and opens the shrine
  door. Handler at `src\game_divine.py:481-531`.
- Non-secret drop path (drop broken_gram on the altar) also wired at
  `src\main.py:6624-6630` → `_activate_odin_shrine(item, reforge=False)`
  (dissolves the blade, opens the shrine, no reforge).

### 2. Judgment Altar → Sword & Scales of Michael — WIRED
- Altar spawns on L99 (`src\dungeon.py:2456-2466` `_create_judgment_altar`).
- Pressing pray on the altar tile calls `_resolve_judgment`
  (`src\game_divine.py:772-780`; handler in
  `src\game_encounters.py:956-1017`).
- Karma table drives all five outcomes
  (`src\npc_encounters.py:1989-2027` `_JUDGMENT_TIERS`, resolver
  `judge_karma()`).
- Reward branches:
  - `sword_and_scales` (karma 10) — spawns `sword_of_michael` weapon +
    `scales_of_michael` artifact in inventory + sets `player_title='Paladin'`.
  - `scales_granted` (karma +1..+9) — spawns just the scales.
  - `abaddon_empowered` (karma −6..−10) — sets `self._abaddon_empowered=True`;
    consumed on L100 first entry at `src\main.py:1554-1558` (Abaddon HP is
    boosted).
  - `locusts_strengthened` (karma −1..−5) — sets flag; consumed in
    `src\main.py:5787` for larger swarms.
- Save/load: both flags persisted (`src\save_system.py:99, 108-109`).

### 3. Punch in the Face (Dad build) — WIRED
- Build entry `src\welcome_screen.py:194-201`: name "dad" or the "god"→"Did
  you mean Dad?" prompt (`welcome_screen.py:456-459`) → maxes all stats to 20,
  sets `_immortal: True`, gives weapon `punch_in_the_face`.
- Weapon `punch_in_the_face` exists in `data\items\weapon.json` (grep-verified).
- `player.immortal` set at `src\main.py:382`; damage bypass at
  `src\player.py:81`.
- No hero_special/passive — Dad's only mechanic is immortality + the weapon.
  (Confirmed comment in `src\hero_specials.py:270`.)

### 4. Six/seven demon seals — DROPS TRACKED, ARTIFACT SPAWN ABSENT (P3)
- Seven seal demons spawn one per level on L83/85/87/89/91/93/97
  (`src\level_manager.py:233-284` `_SEAL_DEMON_LEVELS`,
  `_try_spawn_seal_demon`). Force-placed and marked `is_seal_demon=True`
  (`src\monster.py:90`).
- Kill hook (`src\game_combat.py:726-736`) adds `'seal_of_<kind>'` to a
  `self.seals_broken: set` counter. At count 7 the "the way to the Pit
  stands open" message fires.
- **Gate**: descending from L99 blocked while `len(seals_broken) < 7`
  (`src\main.py:2715-2722`).
- **P3 finding**: the seven `seal_of_*` **artifact JSON entries**
  (`data\items\artifact.json:282-449`) with
  `"effects": ["shatter_on_pickup_with_chronicle"]` and
  `"spawn_method": "seal_demon_drop"` are **completely orphaned**. No code
  in `src\` references `shatter_on_pickup`, `seal_demon_drop`, or any
  actual seal artifact spawn/pickup handler (Grep returned 0 hits).
  The design doc calls this out itself
  (`tools\balance\systems\bosses_and_quests.md:1216-1217`: *"appear to be
  lore-only — no mechanical effect I can find"*).
  **Impact**: the mechanic *works* (the counter suffices to gate L100), but
  the ceremonial pickup + chronicle line described by the JSON never fires.
  Purely a lore-payoff regression, not a quest blocker.

### 5. Abaddon → Victory — WIRED (with caveat)
- L100 arena: `src\boss_levels.py:447-526` `_level_100_abyss` places Abaddon +
  6 altars, **no STAIRS_DOWN** — L100 is terminal.
- `_place_stone` (`src\level_manager.py:388-410`) spawns the Philosopher's
  Stone in the deepest room of L100 on generation. **Placement is
  independent of Abaddon being alive** — the stone is on the floor from the
  moment the player enters L100.
- Kill Abaddon → `boss_abaddon` story popup shown
  (`src\game_combat.py:711-721`, popup content
  `src\main.py:6272-6288`), but this only returns state to STATE_PLAYER.
- Pick up Stone → chronicle line
  (`src\main.py:4266-4311`).
- Ascend from L100 → `_trigger_death_pursuit()`
  (`src\main.py:2746-2760`).
- Ascend to L1 with Stone in inventory → STAIRS_UP triggers
  `STATE_EXIT_QUEST` (`src\main.py:2731-2743`), then `_do_exit()`
  (`src\main.py:2960-2972`) checks for `philosophers_stone` or
  `complete_tablet_of_second_death` in inventory → shows `exit_with_stone`
  popup → transitions to `STATE_VICTORY`.
- Secret victory: `_trigger_abyss` (`src\main.py:2880-2917`) sets
  `_secret_victory=True` and reclaims Death; the victory screen renders the
  purple "DEATH IS DEAD" variant.
- **Confirmation**: the ending sequence Abaddon → win IS fully wired. The
  player kills Abaddon, walks to the pre-placed Stone, picks it up,
  ascends to L1 while Death chases, then a normal STAIRS_UP interaction on
  L1 with the Stone in inventory triggers the victory screen. No orphan
  half — the whole chain is connected.

### 6. Character quirks (all confirmed wired unless noted)

Trigger sites verified in `src\combat.py`, `src\game_combat.py`,
`src\status_effects.py`, and `src\quirk_system.py`.

| Quirk (spec name in brief) | Storage key | Consumer | Status |
|----------------------------|-------------|----------|--------|
| Beowulf `beowulf_unarmed_bonus` | `player.quirk_progress['beowulf_unarmed_bonus']=5` | `src\combat.py:1132` (unarmed damage adder) | WIRED |
| Coif of Beowulf armor proc `grendel_grip` | armor proc | `src\status_effects.py:454-465` (clears paralyzed/strangulation/sleeping) | WIRED |
| Musashi `musashi_active` | `player.quirk_progress['musashi_active']=True` | `src\combat.py:952-954` (chain-1 uses 2nd multiplier) | WIRED |
| Skofnung `chain_bonus_on_low_hp_window` | weapon field | `src\combat.py:876-885` reads it, `src\player.py:341-347` sets the pending flag on <50% HP damage | WIRED |
| Hrunting `one_shot_chain_save_per_floor` | weapon field | `src\combat.py:856-863` promotes chain 0 → 1; `_hrunting_save_used` reset per floor at `src\main.py:1250-1251` | WIRED |
| Green Chapel Axe `returning_blow` | class_mechanic | `src\combat.py:1856-1858` (max-chain self-backlash for half damage) | WIRED |
| Jormungandr `jormungandr_weapon_id` | `player.quirk_progress` | `src\combat.py:1908` (+1 max chain on that weapon id) | WIRED |
| Cow King's Horns `chain_bonus` | armor field | `src\combat.py:815-818` (starting chain head-start) | WIRED |
| Anansi web cloak `story_thread` | armor field | `src\game_combat.py:1914-1921` (first crit per floor charge) | WIRED |
| Cu Chulainn warp-spasm `cuchulainn_wins` | quirk progress | `src\quirk_system.py:495-500` (unlock: STR+1). No "warp-spasm active state" beyond stat bonus. | WIRED (passive stat only — see F1) |
| Bracers of Arjuna `gita_focus` | accessory field | `src\combat.py:1367-1369` (first ranged per floor bonus) | WIRED |
| Breastplate of Joan `maid_does_not_fall` | armor field | `src\game_combat.py:2138-2145` (per-floor death save) | WIRED |
| Fisher King prayer cooldown halving | `fisher_king_active` / `fisher_king_mystery_active` | `src\game_divine.py:976-982` | WIRED |
| All 100 quirk unlocks (see `src\quirk_system.py:_QUIRK_PROGRESS`) — spot check: unlock functions all bound to real hooks (`on_kill`, `on_move`, `on_prayer`, etc.). | | | WIRED |

### 7. Bones (persistent ghosts across runs) — WIRED
- Save on death: `src\bones.py:26-79` (`save_bones`) called from
  `src\main.py:2977-2982` `_on_game_over`.
- Load on level entry: `src\level_manager.py:87-90` (50% roll → `load_bones`
  → `spawn_ghost`).
- Ghost `player_ghost` monster spawned with cursed loot from the dead
  player's equipped gear (`src\bones.py:118-225`). Bones file consumed on
  load so ghost only appears once (`src\bones.py:106`).
- Cap of 3 files; eviction on 4th (`src\bones.py:81-91`).
- Kilt of the Pharaoh `royal_burial` preserves one item uncursed
  (`src\bones.py:33-54, 205-207`).

### 8. Mystery / NPC / Cow / XYZZY — WIRED
- Mystery altars: `src\mystery_system.py` + orchestration
  `src\game_divine.py:151-289`. Physical (Sisyphus) + quiz challenges both
  handled; Pandora `invert_result` respected.
- Karma NPC encounters + flavor NPC encounters — spawn
  `src\game_encounters.py:122-221`; resolve/reward
  `src\game_encounters.py:566-947` (deep switch on cost/reward types,
  Surya's Gift doubling verified).
- Secret cow: 10 pokes → cow-level portal (`src\game_input.py:849-858` +
  `src\game_encounters.py:85-116`). Cow King spawn `spawn_chance=0` (test
  `test_cow_king_spawn_chance_zero_is_portal_only` guards it). Cow King's
  Horns wired via `treasure.unique_drop_id='cow_kings_horns'`
  (`data\monsters.json:22675`, consumer
  `src\game_combat.py:772-774`).
- XYZZY: `src\main.py:4918-5063` + `player.hack_tiers_claimed`. Tier 1
  always fires; tiers 2–5 are once-per-run. Fenrir pet spawn wired at
  tier 5 via `_spawn_fenrir_pet` (referenced but not read here). Backtick
  key opens the terminal (`src\game_input.py:471`).

---

## Findings

### F1 — Cu Chulainn "warp-spasm" quirk is a plain STR+1 stat bump (P1 balance)
- **File**: `C:\Users\brand\Documents\PhilosophersQuest\src\quirk_system.py:495-500`,
  `src\quirk_system.py:1417` (flavor: *"the warp-spasm seizes me — I become
  the storm"*), `src\quirk_system.py:1525` (effect: *"STR +1"*).
- The quirk unlock condition ("5 combat wins while feared") reads as
  earning Cu Chulainn's legendary combat frenzy, but the actual effect is
  just `apply_stat_bonus('STR', 1)`. There is no active buff / no
  temporary aggro / no berserk state. The flavor text is loud, the mechanic
  is silent. Compare with Loki (`WIS +2`), Boudicca (`STR +2`), Cu Chulainn
  is `STR +1` — trivially weak for a difficult trigger.
- **Severity**: P1 (marketed effect never actually fires — the "warp-spasm"
  is nowhere). Also P2 balance (STR+1 is beneath what the flavor promises).
- **Fix hint**: give the quirk a real hook — e.g. auto-apply `berserk` or
  `hasted` for N turns when `feared` is applied, or a per-floor "warp
  session" buff. Even a fear-immunity passive would justify the flavor.

### F2 — Seal-of-* artifact JSON entries are orphaned (P3 stale)
- **Files**: `C:\Users\brand\Documents\PhilosophersQuest\data\items\artifact.json:282-449`
  (all 7 seal entries have `"effects": ["shatter_on_pickup_with_chronicle"]`
  and `"spawn_method": "seal_demon_drop"`).
- No consumer in `src\` for either token (Grep both terms → 0 hits).
- Actual gate uses the `seals_broken: set` counter incremented on demon
  death (`src\game_combat.py:726-736`), which is sufficient — but the
  ceremonial pickup + chronicle line the JSON describes never fires.
- **Severity**: P3. Not a quest blocker (L100 gate works), but the JSON is
  misleading and the "pick up the seal" moment implied by the data is
  missing.
- **Fix hint**: either delete the seven artifact entries (they're dead
  data), or wire the demon-drop path so each demon drops its seal artifact,
  the artifact triggers a chronicle line on pickup, and the seal is
  consumed. Matches the design promise in the JSON `lore` text.

### F3 — Judgment altar "silence" (karma=0) has no side effect nor stored flag (P3)
- **File**: `C:\Users\brand\Documents\PhilosophersQuest\src\npc_encounters.py:2003-2007`
  (`silence` outcome text) + `src\game_encounters.py:956-1017`
  (`_resolve_judgment` — only handles `sword_and_scales`, `scales_granted`,
  `abaddon_empowered`, `locusts_strengthened`).
- The `silence` branch (karma==0) is displayed correctly ("You receive
  nothing.") but there is no elif for it in `_resolve_judgment` — the
  function falls through with `_judgment_text` set and `state=STATE_JUDGMENT`
  but no mechanical consequence and, more importantly, no differentiation
  from the karma-plus/karma-minus branches in save state.
- **Severity**: P3. Functionally correct (silence *should* do nothing) but
  the code shape is confusing — a reader looking at the function reasonably
  wonders whether the karma-0 case is a missed branch. `_judgment_resolved`
  is set in `_start_pray` (`src\game_divine.py:778`) so re-pray is
  blocked either way. No player-facing issue.
- **Fix hint**: cosmetic — add `elif outcome == 'silence': pass  # cold
  silence: message-only, per design` for the reader.

### F4 — `_place_stone` doesn't gate on Abaddon being killed (P4 nit)
- **File**: `C:\Users\brand\Documents\PhilosophersQuest\src\level_manager.py:388-410`
  (called unconditionally when L100 is generated;
  `src\level_manager.py:51-54, 92-95`).
- The Philosopher's Stone is placed in the deepest room of L100 at
  generation time — before Abaddon dies. A brave/lucky player could
  theoretically stealth around Abaddon (or trap him with pets), grab the
  Stone, and ascend without killing him. The boss_abaddon popup would
  simply never fire.
- **Severity**: P4. Almost certainly intended (the design accepts skips as
  legitimate roguelike play), but worth flagging: the "victory sequence"
  does NOT strictly require Abaddon's death — only Stone-in-inventory +
  ascend to L1.
- **Fix hint**: none needed unless design mandates a kill-Abaddon
  gate. If it does, condition the stone's on-tile visibility on
  `abaddon_destroyer` being dead, or drop the stone from Abaddon's corpse
  instead of pre-placing it.

---

## Confirmations (no findings)

- **Ending sequence Abaddon → win**: fully wired. Kill → popup → ascend →
  Death chase → L1 STAIRS_UP with Stone → STATE_EXIT_QUEST → `_do_exit()` →
  `exit_with_stone` popup → STATE_VICTORY. Secret Abyss victory (Death
  killed via `_trigger_abyss`) also wired via `_secret_victory` flag +
  distinct victory screen.
- **Save/load quest state**: `odin_altar_pos` is a dungeon attribute
  (regenerated per floor visit, or restored from save via
  `LevelManager._saved`). `seals_broken`, `_abaddon_empowered`,
  `_locusts_strengthened`, `_l100_altars_used`, `_secret_victory`,
  `_cow_poke_count`, `_cow_level_done` all persisted in
  `src\save_system.py:99-131`. `hack_tiers_claimed` persisted on the
  Player (`src\player.py:78`). `quirk_progress` and `unlocked_quirks`
  persisted on the Player (auto via `__getstate__`).
- **Every named boss has a level generator + kill-popup**: all five
  (Asterion L20, Medusa L40, Fafnir L60, Fenrir L80, Abaddon L100) mapped
  in `_BOSS_STORY_KEYS` (`src\main.py:6338-6344`) and popup content
  (`src\main.py:6220-6288`).
- **Every unique quest artifact I inspected has both spawn AND consumption
  logic**: Bronze Bull (L12) → Ariadne's Shrine; Eye of Graeae (L29) →
  Athena Shrine; Broken Gram (L48) → Odin Shrine / reforge; 6 Gleipnir
  components (L62-77) → Dwarven Forge; 10 leather scraps → Vidar's Altar;
  scales/sword from Judgment altar; Cow King's Horns from Cow King; Sword
  of Michael from L99 pray.
- **Hero specials (V-menu)**: dispatched via
  `src\hero_specials.py:505` `resolve_active_special` invoked from
  `src\game_menus.py:1600-1602` after the chain quiz. Every entry in
  `HERO_SPECIALS` has a matching `_DISPATCH` handler (spot checked).
