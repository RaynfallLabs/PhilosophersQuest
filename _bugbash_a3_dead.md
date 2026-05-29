# Agent A3 — Dead code, unused functions, unreachable branches

Sweep of `src/` (47 modules, ~43k LOC).  
Methodology: AST scan of every `def name(`, grep for `name(` across `src/` + `tests/`, ruff `F401/F841` for unused imports/locals, hand-verification of every flag.

Mixin-class methods were re-checked across all mixins because the `class Game(InputMixin, MenuMixin, …)` pattern hides cross-file `self.method()` calls from naive single-file scans.

Severities: **CRITICAL** = swallowed bug. **WARN** = clearly dead. **MINOR** = stylistic / 1-token cleanup.

---

## src/chain_equip.py

### [WARN] Unused imports of Accessory, Armor, Shield
**File**: `src/chain_equip.py:30`
**What I see**:
```python
from items import Accessory, Armor, Shield
```
**Why it's dead**: ruff F401 + `grep -n '\bAccessory\b\|\bArmor\b\|\bShield\b' src/chain_equip.py` returns only the import line. Module never references the names.
**Suggested fix**: remove the import line entirely.
**Confidence**: HIGH

---

## src/combat.py

### [WARN] `_material_effective_multiplier` — defined, never called
**File**: `src/combat.py:80`
**What I see**:
```python
def _material_effective_multiplier(weapon, monster) -> float:
    """Return 1.5 if any of weapon's material/damage types target monster tags."""
```
**Why it's dead**: `grep -n _material_effective_multiplier src/ tests/` → only the def site. Logic was inlined into `_damage_multiplier` further down.
**Suggested fix**: remove (lines 80–99).
**Confidence**: HIGH

### [WARN] `_material_wielder_vulnerable` — defined, never called
**File**: `src/combat.py:102`
**What I see**:
```python
def _material_wielder_vulnerable(player, monster_attack_tags: list) -> float:
    """Return >1.0 if the player's equipped weapon material is vulnerable…"""
```
**Why it's dead**: zero call sites anywhere (`grep` returns only line 102). Was probably planned for monster-vs-player retaliation; never wired.
**Suggested fix**: remove (lines 102–117).
**Confidence**: HIGH

### [WARN] `can_melee_attack` — top-level function, zero callers
**File**: `src/combat.py:681`
**What I see**:
```python
def can_melee_attack(player, monster) -> bool:
    """Return True if the player's equipped weapon can reach the monster."""
```
**Why it's dead**: `grep` returns only def site. Companion `can_ranged_attack` (line 692) IS used. Cleanup oversight when ranged was split out.
**Suggested fix**: remove (lines 681–689).
**Confidence**: HIGH

---

## src/container_system.py

### [MINOR] Unused local `total_slots`
**File**: `src/container_system.py:419`
**What I see**:
```python
bonus_slots = 1 if chain == 5 else 0
total_slots = n_items + bonus_slots
```
**Why it's dead**: ruff F841. Variable assigned but never read in the rest of the function.
**Suggested fix**: remove the line.
**Confidence**: HIGH

---

## src/dungeon.py

### [WARN] Six `Dungeon.is_X` methods — never called
**File**: `src/dungeon.py:165,182,186,190,194,198`
**What I see**:
```python
def is_altar(self, x, y) -> bool: …          # line 165
def is_water(self, x, y) -> bool: …          # line 182
def is_lava(self, x, y) -> bool: …           # line 186
def is_fountain(self, x, y) -> bool: …       # line 190
def is_grave(self, x, y) -> bool: …          # line 194
def is_throne(self, x, y) -> bool: …         # line 198
```
**Why it's dead**: `grep -rn '\.is_altar\|\.is_water\|\.is_lava\|\.is_fountain\|\.is_grave\|\.is_throne' src/ tests/` returns zero matches outside the def lines. Tile-type checks all happen via direct `tiles[y][x] == ALTAR` etc. (e.g. `main.py:1766` uses ` next(... ALTAR ...)` in inventory, not the helper).
**Suggested fix**: remove all six (≈25 lines). Re-introduce as needed but `is_walkable`/`is_opaque` cover all current call sites.
**Confidence**: HIGH

### [WARN] `Room.intersects` — never called
**File**: `src/dungeon.py:101`
**What I see**:
```python
def intersects(self, other: 'Room', pad: int = 1) -> bool: …
```
**Why it's dead**: BSP partitioning makes rooms non-overlapping by construction, so the collision check is unused. `grep '\.intersects(' src/` only matches inside Pygame (`pygame.Rect.colliderect` etc.).
**Suggested fix**: remove (lines 101–107).
**Confidence**: HIGH

### [WARN] Unused imports in `spawn_items` and vault block
**File**: `src/dungeon.py:1241`, `src/dungeon.py:1655`
**What I see**:
```python
# 1241
from items import (load_items, Container, Weapon, Armor, Shield,
                   pick_random_weapon_for_floor, pick_random_armor_for_floor,
                   pick_random_shield_for_floor)
# 1655
from items import GoldPile, add_gold_to_tile
```
**Why it's dead**: ruff F401 — `Weapon`, `Armor`, `Shield` (line 1241) and `GoldPile` (line 1655) are imported but never referenced.
**Suggested fix**: trim each import list.
**Confidence**: HIGH

---

## src/game_combat.py

### [WARN] Unused import of `GoldPile`
**File**: `src/game_combat.py:660`
**What I see**:
```python
from items import GoldPile, add_gold_to_tile
```
**Why it's dead**: ruff F401. Only `add_gold_to_tile` is used in the block (line 661).
**Suggested fix**: drop `GoldPile`.
**Confidence**: HIGH

---

## src/game_magic.py

### [WARN] `MagicMixin._quick_buc_check` — never invoked
**File**: `src/game_magic.py:2722`
**What I see**:
```python
def _quick_buc_check(self, item):
    """Tier-1 philosophy threshold quiz that reveals only buc_known."""
```
**Why it's dead**: `grep -n quick_buc src/ tests/` returns only the def line. Per project_identify_design.md: "ONE quiz tiered, no chooser; chooser regression removed" — this dead method is the chooser carcass.
**Suggested fix**: remove the method (≈70 lines from line 2722 until next `def`). Confirm with user since identify rebuild noted chooser was removed.
**Confidence**: HIGH

---

## src/game_menus.py

### [WARN] `MenuMixin._get_page` — defined, never called
**File**: `src/game_menus.py:147`
**What I see**:
```python
def _get_page(self, items) -> list:
    """Return items (no pagination needed with a-z + tabs)."""
    return items[:26]
```
**Why it's dead**: docstring states pagination isn't needed; `grep _get_page src/` shows only def site. Dead since the a-z + tabs refactor.
**Suggested fix**: remove.
**Confidence**: HIGH

### [WARN] Unused import `ARMOR_SLOTS`
**File**: `src/game_menus.py:375`
**What I see**:
```python
from items import ARMOR_SLOTS
```
**Why it's dead**: ruff F401. Inside `_get_equip_items`, never referenced after import.
**Suggested fix**: remove the line.
**Confidence**: HIGH

---

## src/game_render.py

### [WARN] `RenderMixin._draw_page_indicator` — never called
**File**: `src/game_render.py:112`
**What I see**:
```python
def _draw_page_indicator(self, items, bx, bw, y):
    """Show item count if list is long."""
    total = len(items)
    if total > 9: …
```
**Why it's dead**: zero call sites. Used to live in older paged menu; deprecated by tab-based menus.
**Suggested fix**: remove (lines 112–117).
**Confidence**: HIGH

### [WARN] `RenderMixin._draw_tab_bar` — never called
**File**: `src/game_render.py:159`
**What I see**:
```python
def _draw_tab_bar(self, tabs, active_idx, bx, by, bw, counts=None): …
```
**Why it's dead**: zero call sites; tabs now drawn inside `PanelBuilder._draw_tabs` (panel.py:214).
**Suggested fix**: remove (lines 159–203, ~45 lines).
**Confidence**: HIGH

### [MINOR] Unused local `title_col`
**File**: `src/game_render.py:3783`
**What I see**:
```python
title_col  = FP.LORE_BLUE_TITLE
```
**Why it's dead**: ruff F841. Computed alongside `border_col`/`stat_col`/`lore_col` but only those three are referenced below; `title_col` is assigned in both branches of the if/else and never read.
**Suggested fix**: remove from both branches (lines 3778 and 3783).
**Confidence**: HIGH

### [WARN] Unused import `MONSTER_FAMILY_BLESSINGS`
**File**: `src/game_render.py:3803`
**What I see**:
```python
from monster_classes import (get_monster_family, MONSTER_FAMILY_BLESSINGS)
```
**Why it's dead**: ruff F401; only `get_monster_family` is used below (line 3804).
**Suggested fix**: remove `MONSTER_FAMILY_BLESSINGS` from the import.
**Confidence**: HIGH

### [MINOR] Five f-strings without placeholders
**File**: `src/game_render.py:3044, 3046, 3047, 3048, 3157`
**What I see**:
```python
("P", f"Pet  (+5 XP; once per floor)"),
("R", f"Recall to Soul Sphere  (requires adjacent)"),
…
sub = f"Will you give this companion a name?"
```
**Why it's dead**: ruff F541. `f` prefix without `{}` does nothing; either drop the prefix or it's leftover from when text used variables.
**Suggested fix**: drop the `f` prefix on those literals (or restore the variable they used to interpolate).
**Confidence**: HIGH

### [MINOR] Three duplicated draw methods (`_draw_confirm_exit` / `_draw_exit_quest` / `_draw_abandon_quest`)
**File**: `src/game_render.py:3179, 3211, 3238`
**What I see**: Three 25-line draw methods, structurally identical (overlay → dark panel → header → subtitle → divider → key/desc rows). `_draw_exit_quest` and `_draw_abandon_quest` are ~95% the same code with only the title text and color differing.
**Why it's dead**: not dead but high duplication. Could collapse to one `_draw_yn_panel(title, subtitle, options)` helper.
**Suggested fix**: refactor into `_draw_yn_panel(title, subtitle, yes_label, yes_color, no_label='Keep playing')`.
**Confidence**: MEDIUM (refactor candidate, not strictly dead)

---

## src/highscore_system.py

### [WARN] `get_scores` — only used in tests, not in production
**File**: `src/highscore_system.py:82`
**What I see**:
```python
def get_scores() -> list[dict]:
    """Return the current top-score list (sorted descending by score)."""
    return _load()
```
**Why it's dead**: `grep get_scores src/` returns only the def line; only `tests/test_pets.py` calls it. Production reads scores through `get_top(n)` instead.
**Suggested fix**: remove or fold into `get_top(None)` — the function is a one-line wrapper that duplicates `_load()`.
**Confidence**: HIGH

---

## src/items.py

### [MINOR] Unused `import math` inside `instantiate_weapon`
**File**: `src/items.py:789`
**What I see**:
```python
def instantiate_weapon(...):
    """Build a Weapon by combining a template (shape) with a material (stats)…"""
    import math
    tpl = get_template('weapons', template_id)
```
**Why it's dead**: ruff F401. `math` is imported inside the function but never used. Leftover from earlier math-based damage computation.
**Suggested fix**: remove the line.
**Confidence**: HIGH

### [MEDIUM] `instantiate_armor` / `instantiate_shield` near-duplicates
**File**: `src/items.py:927, 969`
**What I see**: two 40-line functions doing the same template+material composition, differ only in `tpl = get_template('armor'|'shields', …)`, the symbol char (`[` vs `)`), the `item_class` string, and whether material is pulled from one or both pools.
**Why it's dead**: not dead, but extensive duplication (~85% line-for-line). Maintenance hazard.
**Suggested fix**: factor into a single `_instantiate_worn(category, …)` helper; the two public names can stay as thin wrappers that pass the category and the `Armor`/`Shield` class.
**Confidence**: MEDIUM (refactor candidate)

---

## src/level_manager.py

### [WARN] `LevelManager.has_visited` — never called
**File**: `src/level_manager.py:41`
**What I see**:
```python
def has_visited(self, level_num: int) -> bool:
    return level_num in self._saved
```
**Why it's dead**: `grep '\.has_visited\(' src/ tests/` returns zero results. Callers use `self.level_mgr.load(n)` (returns None if absent) instead. Only references are in `data/audit/world.json` documentation.
**Suggested fix**: remove (lines 41–42).
**Confidence**: HIGH

---

## src/main.py

### [WARN] Unused import `get_monster_family` (inside Hermes ability)
**File**: `src/main.py:885`
**What I see**:
```python
from monster_classes import get_monster_family
# Find ANY strong allied template within visible monsters; …
```
**Why it's dead**: ruff F401; the rest of the block uses literal monster lists and never calls `get_monster_family`.
**Suggested fix**: remove the import.
**Confidence**: HIGH

### [MINOR] Unused local `bname`
**File**: `src/main.py:1310`
**What I see**:
```python
bname = (self.secret_build or {}).get('_name', '') if self.secret_build else ''
# The build dict is keyed by lowercased name in SECRET_BUILDS, but
# _give_starting_kit doesn't have direct access to the key. The
# player's typed name is the source of truth.
key = (self.player_name or '').lower().strip()
```
**Why it's dead**: ruff F841; comment even explains why `bname` isn't authoritative. Replaced by `key` on the next line.
**Suggested fix**: remove the line.
**Confidence**: HIGH

### [WARN] Unused import `add_gold_to_tile` in `_pickup`
**File**: `src/main.py:3076`
**What I see**:
```python
def _pickup(self):
    from items import GoldPile, add_gold_to_tile
```
**Why it's dead**: ruff F401. `_pickup` only uses `GoldPile` (`isinstance(item, GoldPile)` later); `add_gold_to_tile` is unused here.
**Suggested fix**: drop `add_gold_to_tile` from the import.
**Confidence**: HIGH

### [WARN] `Game._examine_corpse` — defined, never bound to a key or menu
**File**: `src/main.py:5007`
**What I see**:
```python
def _examine_corpse(self):
    """Called when player presses the examine key on a corpse on their tile."""
```
**Why it's dead**: `grep _examine_corpse src/` shows only the def + the COMPLETELY DIFFERENT method `_examine_corpse_direct` (which IS called via `game_menus.py:702`). The no-suffix variant has no caller. References in `data/audit/main_b.json` are old paths (line 7151–7161 / 7204–7214) that don't match current line numbers — both methods got renamed/restructured during the identify rebuild and only `_examine_corpse_direct` survived.
**Suggested fix**: remove the method (lines 5007–5022). The docstring lies about "press the examine key" — there's no such key binding.
**Confidence**: HIGH

---

## src/panel.py

### [WARN] Unused import `truncate_label`
**File**: `src/panel.py:34`
**What I see**:
```python
from text_layout import truncate_label
```
**Why it's dead**: ruff F401. Never used.
**Suggested fix**: remove.
**Confidence**: HIGH

### [WARN] `PanelBuilder.outer_rect` — never called
**File**: `src/panel.py:155`
**What I see**:
```python
def outer_rect(self) -> pygame.Rect:
    return pygame.Rect(self.bx, self.by, self.bw, self.bh)
```
**Why it's dead**: `grep outer_rect src/ tests/` returns only the def site. Callers use `body_rect()` (for content) or compute their own outer rect inline.
**Suggested fix**: remove (lines 155–156).
**Confidence**: HIGH

### [WARN] `PanelBuilder.draw_scrollable_lines` — never called
**File**: `src/panel.py:257`
**What I see**:
```python
def draw_scrollable_lines(self, lines, scroll, line_h=22) -> int:
    """Paint a vertical list of (text, color, font_or_None) tuples into body_rect()"""
```
**Why it's dead**: zero call sites in `src/`. Every panel that scrolls (lore log, encyclopedia, missed-questions) implements its own loop instead of calling this convenience.
**Suggested fix**: either remove (~35 lines, 257–292) or migrate the scroll-using panels to call it. Removal is the lower-risk move.
**Confidence**: HIGH

### [MINOR] Three unused size constants
**File**: `src/panel.py:40,44,47`
**What I see**:
```python
SIZE_SM   = ('sm', 480)     # line 40
SIZE_FULL = ('full', 0)     # line 44
PAD_TIGHT = 4               # line 47
```
**Why it's dead**: `grep '\bSIZE_SM\b\|\bSIZE_FULL\b\|\bPAD_TIGHT\b' src/` only matches the def lines. `SIZE_MD/LG/XL` and `PAD_NORMAL/LOOSE/SECTION` ARE used.
**Suggested fix**: remove the three unused tokens.
**Confidence**: HIGH

---

## src/paths.py

### [WARN] `fmt_id` — never called
**File**: `src/paths.py:27`
**What I see**:
```python
def fmt_id(raw: str) -> str:
    """Convert a snake_case identifier to a display string: 'wild_swing' -> 'wild swing'."""
    return raw.replace('_', ' ')
```
**Why it's dead**: `grep '\bfmt_id\b' src/ tests/` returns only the def. Code that does this conversion calls `raw.replace('_', ' ')` inline or uses `fix_name_case` from `game_helpers`.
**Suggested fix**: remove (lines 27–29).
**Confidence**: HIGH

---

## src/player.py

### [WARN] `Player.spend_sp` — never called
**File**: `src/player.py:278`
**What I see**:
```python
def spend_sp(self, amount: int) -> bool:
    if self.sp < amount:
        return False
    self.sp -= amount
    return True
```
**Why it's dead**: `grep '\.spend_sp\(' src/ tests/` returns zero results. Mirrors `restore_sp` but no SP-cost mechanic ever uses it; all stamina drain happens via `self.sp -= n` inline.
**Suggested fix**: remove (lines 278–282) OR start using it consistently (sound API design but currently zero callers).
**Confidence**: HIGH

---

## src/chain_passives.py

### [WARN] `get_mp_bonus` — only tested, never used in production
**File**: `src/chain_passives.py:182`
**What I see**:
```python
def get_mp_bonus(player) -> int:
    """Total extra max_mp from chain-equip passives (mp_bonus + max_mp_bonus)."""
    return int(sum_passive_values(player, 'mp_bonus') +
               sum_passive_values(player, 'max_mp_bonus'))
```
**Why it's dead**: `grep get_mp_bonus src/` → only def site. Test `tests/test_chain_passives.py:212` exercises it. Production callers compute MP bonuses via direct `sum_passive_values('mp_bonus')` and never go through the wrapper.
**Suggested fix**: either wire the production max-MP recompute through this helper (preferred — establishes single source of truth) or remove (+ delete the test).
**Confidence**: HIGH

### [WARN] `get_death_save_bonus` — only tested, never used in production
**File**: `src/chain_passives.py:210`
**What I see**:
```python
def get_death_save_bonus(player) -> int:
    return int(sum_passive_values(player, 'death_save_bonus'))
```
**Why it's dead**: Same pattern. Tests at `tests/test_chain_passives.py:291` exercise it; no production caller. The actual death-save logic in `player.py:try_death_save` queries items directly.
**Suggested fix**: same as `get_mp_bonus` — wire it in or remove.
**Confidence**: HIGH

### [WARN] `is_run_spent` — only tested, never used in production
**File**: `src/chain_passives.py:158`
**What I see**:
```python
def is_run_spent(player, flag: str) -> bool:
    return flag in _ensure_run_set(player)
```
**Why it's dead**: `grep is_run_spent src/` → only def site. Test `tests/test_chain_passives.py:170`. Production gates the same condition through `consume_run_passive` which both checks AND marks; the standalone "did we spend it" query has no caller.
**Suggested fix**: remove (+ delete test) OR keep as documented API and add `# noqa` if intentional.
**Confidence**: HIGH

---

## src/quirk_system.py

### [CRITICAL] `QuirkSystem.on_disease_drain` — defined hook never invoked
**File**: `src/quirk_system.py:883`
**What I see**:
```python
def on_disease_drain(self, stat: str, amount: int):
    """Called when disease ticks and drains a stat."""
    # Paracelsus (#5): disease drains 5+ stat points total
    self._inc('disease_drain_total', amount)
    if self._p('disease_drain_total') >= 5 and not self.is_unlocked('paracelsus'):
        self._award('paracelsus', "Paracelsus' Doctrine", …)
```
**Why it's dead**: `grep on_disease_drain src/` → only def site. Disease drain happens in `status_effects.py:323` (`player.apply_stat_bonus(stat, -1)`) without invoking the hook. **This silently blocks unlock of the Paracelsus quirk.** Already documented in `tools/audit/findings/code/agent_a/code-quirks-on-disease-drain-dead.md` but unfixed.
**Suggested fix**: wire `qs.on_disease_drain(stat, 1)` in `status_effects.py:323` (the existing audit suggests the exact patch).
**Confidence**: HIGH

---

## src/text_layout.py

### [WARN] `text_block_height` — never called
**File**: `src/text_layout.py:164`
**What I see**:
```python
def text_block_height(lines: int, line_h: int, line_gap: int = 0) -> int:
    """Pixel height for `lines` lines of text with `line_h` line height
    and optional `line_gap` between lines."""
```
**Why it's dead**: zero call sites in `src/` or `tests/`.
**Suggested fix**: remove (lines 164–168).
**Confidence**: HIGH

### [WARN] Unused import `Iterable`
**File**: `src/text_layout.py:32`
**What I see**:
```python
from typing import Iterable, NamedTuple
```
**Why it's dead**: ruff F401. `NamedTuple` is used; `Iterable` is not.
**Suggested fix**: trim to `from typing import NamedTuple`.
**Confidence**: HIGH

---

## src/welcome_screen.py

### [WARN] Unused import `draw_divider`
**File**: `src/welcome_screen.py:17`
**What I see**:
```python
from fantasy_ui import (FP, get_font, draw_panel, draw_dark_panel,
                        draw_header_bar, draw_filigree_bar, draw_shadow_text,
                        draw_overlay, draw_rune_circle, draw_candle_glow,
                        draw_divider, centered_text)
```
**Why it's dead**: ruff F401. `draw_divider` never referenced in the file.
**Suggested fix**: remove `draw_divider` from the import tuple.
**Confidence**: HIGH

---

## src/food_system.py

### [MINOR] f-string without placeholders
**File**: `src/food_system.py:339`
**What I see**:
```python
messages.append(f"A glow spreads — most of your stats edge upward.")
```
**Why it's dead**: ruff F541. No interpolation in this string.
**Suggested fix**: drop the `f` prefix.
**Confidence**: HIGH

---

## src/game_divine.py

### [MINOR] f-string without placeholders
**File**: `src/game_divine.py:1141`
**What I see**:
```python
msgs.append(f"Raphael's healing flame: full restoration"
            + (f" + cured {', '.join(cured)}." if cured else "."))
```
**Why it's dead**: ruff F541 on the first literal (the second is a real f-string).
**Suggested fix**: drop `f` prefix on the first literal only.
**Confidence**: HIGH

---

## src/game_magic.py

### [MINOR] f-string without placeholders
**File**: `src/game_magic.py:2711`
**What I see**:
```python
'desc': f"Potions of this type are 25% more potent."}
```
**Why it's dead**: ruff F541.
**Suggested fix**: drop `f`.
**Confidence**: HIGH

---

## src/class_masteries.py

### [MINOR] f-string without placeholders
**File**: `src/class_masteries.py:372`
**What I see**:
```python
'desc': f"Potions of this class are 20% more potent in your hands."}
```
**Why it's dead**: ruff F541. Mirror of the game_magic.py:2711 case (parallel "potion class" vs "potion type" code path — yet another duplicate-logic candidate).
**Suggested fix**: drop `f`.
**Confidence**: HIGH

---

## src/renderer.py

### [MEDIUM] Three near-identical sprite-loaders (`_get_env_sprite` / `_get_item_sprite` / `_get_sprite`)
**File**: `src/renderer.py:128, 140, 154`
**What I see**: 11-line functions, structurally identical: check cache → build path from `_*_SPRITE_DIR + f"{key}.png"` → load → scale → cache. They differ only in:
- the directory constant used
- a single corpse-fallback line in `_get_item_sprite`
**Why it's dead**: not dead but ~90% line-for-line duplication; the only meaningful difference is the dir constant. Three independent caches and three near-identical methods.
**Suggested fix**: refactor into one `_get_cached_sprite(key, sprite_dir, cache, corpse_fallback=False)` and have the three named methods delegate.
**Confidence**: MEDIUM (refactor candidate)

---

## src/game_input.py

### [MINOR] Near-duplicate input handlers (`_exit_quest_input` / `_abandon_quest_input`)
**File**: `src/game_input.py:462, 469`
**What I see**: two 6-line methods, differ only by which state to set on `y` (`_do_exit()` vs `STATE_CHICKEN`). Could collapse with a target-state parameter.
**Suggested fix**: minor; refactor only if touching the file for other reasons.
**Confidence**: LOW

---

## src/game_menus.py

### [MINOR] Near-duplicate `_pet_feed_input` / `_pet_heal_input` and `_open_quaff_menu` / `_open_wand_menu`
**File**: `src/game_menus.py:1385, 1440, 155, 515`
**What I see**: pairs of menu-open + key-handle methods that share the same shape (filter inventory by type → store list+target → set state). Reasonable as separate functions for clarity but the pair-with-pair pattern adds 4× repetition.
**Suggested fix**: optional; nothing dead, just elegance.
**Confidence**: LOW

---

## Summary

**Total findings**: 41 (1 CRITICAL, 24 WARN, 16 MINOR)

| Severity | Count | LOC estimate |
|----------|------:|-------------:|
| CRITICAL — silently breaks a quirk unlock | 1 | wire-up, not deletion |
| WARN — dead methods / dead functions | 17 | ~190 LOC |
| WARN — unused imports / locals | 13 | ~15 LOC |
| MINOR — f-string prefix fixes | 7 | 7 chars |
| MEDIUM/MINOR — duplicated logic | 6 | refactor, ~150 LOC if compressed |

**Removable LOC (pure deletions, no refactor required)**: roughly **205–225 lines** across 11 files, plus 7 one-char `f"` cleanups.

**Highest-value to act on now**:
1. **Wire `on_disease_drain` in `status_effects.py:323`** — this is a real bug (Paracelsus quirk unreachable). Already audited; just needs the patch.
2. **Remove the six `Dungeon.is_X` helpers and `Room.intersects`** — clean, isolated deletes (`dungeon.py`).
3. **Remove the three Panel scaffolding helpers** (`outer_rect`, `draw_scrollable_lines`, three unused size tokens) — `panel.py` will lose ~40 lines.
4. **Remove `_quick_buc_check`** in `game_magic.py` — leftover from identify rebuild, ~70 LOC.
5. **Remove `_examine_corpse` in `main.py`** — bound to nothing; docstring lies about an "examine key".

Lowest-confidence items: `get_mp_bonus` / `get_death_save_bonus` / `is_run_spent` (chain_passives) — they have tests, so the user may want to wire them in for consistency rather than delete.
