# Overnight Bug Bash — Morning Report (2026-05-28 → 2026-05-29)

## TL;DR

- **7 opus agents** ran in parallel, surveying UI, cross-system, dead code, data integrity, attribute API, question banks, mechanics, and elegance.
- **305 raw findings** triaged into 3 tiers.
- **9 batches executed overnight** (B1, B2, B3+B4, B5, B7, B8, B9, B11) — **~70 substantive fixes** shipped.
- **665/665 tests** green after every batch.
- **Rollback tag**: `pre_bug_bash_2026_05_28` (preserved).
- 8 commits pushed to remote: `70d505e` … `5f4c23e`.

## What landed

### B1 — Save/load critical fixes (`70d505e`)
Three save-exploit / warp-on-reload bugs:
1. Per-floor charges `_first_hit_used`, `_death_save_used`, `_tarnhelm_used`, `_quiz_reroll_used` now serialized — were on Game (not Player) and never saved → save/reload refreshed them
2. `_cow_return_level` now serialized — reload on cow level → exit portal previously warped to floor 0
3. `_chronicle_abaddon_start` guard now serialized — was duplicating chronicle line on reload

### B2 — Quick wins (`ea8cb0c`)
Five surgical fixes:
1. `main.py:3774` `'good'` message-type → `'success'` (was falling back to info-grey)
2. Paracelsus quirk wire-up: `status_effects.tick_all` emits `_disease_drain:STAT:N` signal, `main.py` dispatches to `quirk_system.on_disease_drain()`. Without this the quirk could **never unlock**.
3. Four ring grammar names fixed so `mastery_class` slug matches `CLASS_MASTERY_BLESSINGS`:
   - `ring_levitate` → "ring of levitation"
   - `ring_invisible` → "ring of invisibility"
   - `ring_hasted` → "ring of haste"
   - `ring_clairvoy` → "ring of clairvoyance"
4. `tungsten` armor material can now spawn (added `exotic_metal` to plate template's `compatible_material_classes`)

### B3+B4 — Spell-MP / stacked-status / monster mastery (`6554a7b`)
1. **ESC during STATE_TARGET refunds spell MP**. _cast_spell deducts MP *before* targeting; ESC handler now refunds and clears `_pending_spell`.
2. **Stacked-status unequip preserves effect when another item still grants it**. New helper `_remove_status_if_no_other_grants(status)` walks every other slot before popping. Two Rings of Warning no longer lose 'warning' status when one is removed.
3. **Monster `int_bonus` mastery uses `apply_stat_bonus` instead of direct assignment**. Aberration family chain-5 was doing `max_mp = BASE + INT`, wiping chain-equip max_mp_bonus from Robe of the Magus etc. Now uses the helper that correctly adds to bonuses without clobbering siblings.

### B5 — Combat math edges (`ea4295f`)
1. **Quiz timer floored at 5 seconds** — at very low WIS (cursed drain + disease ticks) the formula could yield 0 or negative, making combat unwinnable
2. **`shielded` status now halves physical damage on the player too** (matches the description + Mage Armor spell). Was only wired for monsters.
3. **Stack-merge BUC now compares underlying buc values**. Previously hidden-BUC blessed + cursed stacks merged into one stack carrying only one buc — silently lost the incoming item's effect at consumption.
4. **`cursed_miss_backlash` floors HP at 0**. Was raw `player.hp -= N`; could go negative.

### B7 — UI critical fixes (`612a265`)
1. Three pet sub-menus (`_draw_pet_menu`, `_draw_pet_specials_submenu`, `_draw_pet_sub_picker`) now render ESC footer hint on empty state — was leaving user with no exit instruction
2. Combat HUD monster name + effects row truncate to `rx - lx - 16` so long uniques don't bleed into the WEAKNESS!/RESISTED label column
3. **Sidebar equipment line now truncates the BASE NAME, not the suffix**. Was composing `name +3 {C} [124 silver tipped arrowss]` then truncating the whole string, eating the gameplay-critical `+3 {C}` info. New pattern: measure suffix width first, give name only the leftover budget.
4. Drop-gold popup uses `WINDOW_H` not `GAME_H` for vertical centering (was shifted up 100px vs every other input modal)

### B8 — Duplicate-choice fixes (`5928750`)
**27 questions** had literal duplicate choices (4-choice multiple-choice was effectively 3-choice):
- 25 math T2/T3/T4 geometry questions (bulk-gen formula-collision) — regenerated via off-by-one + doubling perturbations
- AI #105 ("Stable Diffusion" x2 — my Phase E Sora swap own-goal) → replaced second dup with "Imagen"
- Grammar #514 ("afect" x2) → replaced one with "effected"

### B9 — Bank quality (`5f98c3e`)
17 substantive rewrites:
- **5 trivia stem-leaks**: Urusei Yatsura, Fullmetal Alchemist nickname, The One Piece, Mumm-Ra the Ever-Living, Donkey Kong → Pauline (pivot, "Mario" collided with #688)
- **6 history generic-labels** ("Mary Celeste pattern" — same bug class as Mary Celeste fix two days ago):
  - #101 Sobieski → "The Winged Hussars" (was "largest cavalry charge")
  - #198 Origin of Species → "1,250 copies" (was "sold out")
  - #737 Kursk → "Prokhorovka" (was "largest tank battle")
  - #829 Guernica → "Guernica" (the painting's name; was "most powerful anti-war painting")
  - #32 Thermopylae → "Thermopylae" (was "Three hundred")
  - #98 Antietam → "Special Order 191" (was "Three cigars in a field")
- **6 weasel closers** — 4 AI ("What's the move?" / "What does that mean?") + 2 economics ("What's the point?" / "What does this tell us?") rewritten to single-thing-pointed closers

### B11 — Ruff cleanup (`5f4c23e`)
24 automatic fixes:
- 11 unused imports (F401)
- 8 f-strings without placeholders (F541)
- 2 unused locals (F841)
- title_col, total_slots, etc.

## Tier 3 — DEFERRED for your review

These need design decisions or carry behavioral risk too high for overnight autonomy:

### A4 — Phantom artifacts (4 items)
- `pandoras_box`, `aladdins_lamp`, `palladium`, `tablet_of_destinies` are fully authored in JSON with rich consume mechanics but **cannot spawn**. Two have active player-code handlers (`main.py:1349`, `game_combat.py:1332`) that are effectively dead because the items never enter inventory.
- Need design decision: wire spawn pool (which floor band, which chest tier) OR remove from JSON.
- **My recommendation**: keep them — implement a `random_lore_quest_*` spawn hook in `level_manager.py`. The JSON spec is internally complete.

### A4 — 26 artifacts have no `mastery_blessing` AND no `Artifact` branch in `_default_mastery_for`
- Chain-5 identify says "You have mastered the X!" then silent no-op. Item stuck in identify menu forever.
- Options: (a) write conservative default `{'kind': 'no_effect', 'desc': 'Your understanding feels complete.'}` for Artifact, (b) author per-artifact `mastery_blessing` entries in JSON.
- **My recommendation**: (a) for safety, then (b) over time for the iconic artifacts.

### A8 — Big refactors (3 candidates)
1. **313-elif effect dispatch** in `game_magic.py` (`_apply_wand_effect`, `_apply_spell_effect`, `_apply_scroll_effect`, `drink_potion`). Multi-day handler-at-a-time work; matches the kit-menu shared-helper pattern.
2. **`load_state` migration table** (`main.py:354-540`, 187 lines, 35 `hasattr` checks). Should become a declarative `PLAYER_DEFAULTS` table.
3. **render() + handle_event() mega-dispatch** (89 states across 2 files). State→method tables would cut both 70%.

All three are high-ROI but risky overnight.

### A5 — Attribute API standardization (deferred)
- `id_level` default conflict (5 at 2 sites vs 0 at all others) — A5 said standardize on 0; but the comment at `game_menus.py:649-650` explains 5 is intentional defensive. Skipping risk; needs your call.
- `slot` default has 7 different values across sites (`''`, `'armor'`, `'body'`, `'ring'`, `'accessory'`, `itype`, `slot_type`). Each change risks behavioral surprise.
- `apply_stat_bonus(stat, amount)` does setattr with no validation — risky to add (would convert silent fails to explicit fails).

### A2 — Other integration gaps (queued)
- **`_propagate_identification` doesn't actually sync `id_level`** (doc claims it does). Only syncs `buc_known` and only walks inventory. Two identical wands → identify one to T3 → other still shows (0/5).
- **`Item.identified` is NOT a back-compat property** (my IDENTIFY_SYSTEM.md doc claims it is but the code shows it's a plain instance attribute). 40+ sites write `item.identified = True` without bumping `id_level`. Doc + code drift.
- Wand+scroll identify paths don't bump `id_level` when setting `identified = True`.

### Docs that need updating
- `proposals/v2_audit/IDENTIFY_SYSTEM.md` §2 — `Item.identified` property claim is wrong
- `proposals/v2_audit/07_systems.md` — spell-handler missing list is now stale (all are wired)
- Memory file `project_architecture.md` claims `main.py` is ~4,065 lines; actual is 5,443

### Banks — residuals (~70 minor flags)
A6 found ~70 WARN/MINOR bank quality issues across the 12 banks that I didn't get to overnight. Most are borderline (subjective tier judgments, debatable generic-label calls). Worth a follow-up sweep but not urgent.

### A3 — Dead functions (~17, ~190 LOC)
Cross-mixin grep verification needed before removal. Notable candidates:
- `Dungeon.is_altar/water/lava/fountain/grave/throne` (6 helpers, never called)
- `Room.intersects`, `_quick_buc_check` (chooser carcass from identify rebuild)
- `combat.can_melee_attack`, `_material_effective_multiplier`, `_material_wielder_vulnerable`
- `game_render._draw_page_indicator`, `_draw_tab_bar`
- `panel.outer_rect`, `draw_scrollable_lines`
- `main._examine_corpse` (orphan; `_examine_corpse_direct` is the live one)

### A1 — UI WARN list (~60)
Most are missing-truncate-call patterns in less-critical paths (XYZZY input, judgment overlay, NPC encounter text, etc.). Lower-risk than the B7 batch I shipped. Worth a clean sweep when you have time.

## Quality of finds

The 7-agent parallel survey worked extremely well — far more leverage than the recent QA audit. Each agent found things the others wouldn't have (e.g. A2 confirmed two memory-flagged "unwired" masteries are actually wired now; A5 caught the `id_level` default split that A2 missed; A6 found my own Stable Diffusion own-goal from Phase E).

## What I did NOT touch

- `data/questions/math.json` outside the dup-choice fixes (no other findings flagged)
- `tests/conftest.py` (none exists; not creating one overnight without your sign-off on the pattern)
- The 14 fake `try: from chain_passives import ...` blocks in `main.py` (A8 found them; defensive code against a guaranteed-present sibling; would prefer your sign-off before mass-removing)
- Any item balance / monster stats / floor layouts
- Anything that touches the L99 judgment / karma system

## Recommendation for morning

1. Sanity-check the game (open Kit menu, sidebar, identify menu, pet menu, hack-reality). If anything visibly broken, see commit `5f4c23e` for the most-recent state and roll back the offending batch.
2. Look at the 4 phantom artifacts — they're real money waiting on a small wiring decision.
3. Look at the 26 artifacts-no-mastery question — needs a one-line policy choice.
4. The doc drift items (IDENTIFY_SYSTEM.md, 07_systems.md, project_architecture.md memory) — happy to update if you want them brought current.

Sleep well. 🛌
