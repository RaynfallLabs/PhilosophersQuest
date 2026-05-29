# A8 — Elegance / Refactor Opportunities (overnight bug-bash)

Audited:
- `src/main.py` (5,443 lines, the known god-class)
- 7 `Game` mixins: `game_render` (4,626) / `game_magic` (3,150) / `game_combat` (2,132) / `game_menus` (1,575) / `game_divine` (1,250) / `game_input` (1,090) / `game_encounters` (1,011)
- Pure helpers: `game_helpers.py` (109 lines), `chain_passives.py` (423 lines), `text_layout.py` (169 lines), `panel.py` (292 lines)
- All 35 test files in `tests/`
- Recent commit history (last 16 commits — measured-table extraction landed `3d5f78c`)

Skipped per scope:
- Stylistic nitpicks (line length, trailing whitespace) — ruff territory
- Mixin layout itself — memory file `project_architecture.md` is explicit that the 7-mixin design is a deliberate trade-off, not a refactor candidate
- Speculative big-bang redesigns

Cross-cutting numbers:
- 119 deferred `from items import X` (vs 6 top-level). Tells you what items.py couples to.
- 41 inline `import random as _rng` despite top-level `import random` already imported in 8 of those files.
- 14 `try: from chain_passives import …; except ImportError: pass` blocks in `main.py` against a guaranteed-present sibling module. Dead defensive code.
- 35 test files each duplicate the `sys.path.insert + pygame.init` boilerplate.
- 313 `if/elif effect == 'X'` branches across `_apply_wand_effect`/`_apply_spell_effect`/`_apply_scroll_effect`/`drink_potion` — the four canonical "effect dispatcher" giants.
- 6 `_draw_*` modals hand-roll `pygame.Surface((WINDOW_W, WINDOW_H), SRCALPHA) + fill((0,0,0,A)) + blit` despite `panel.PanelBuilder` existing.

---

## 1. 🟩 [HIGH] Effect-dispatch tables for wand / spell / scroll / potion / thrown

**Files affected**: `src/game_magic.py:285-1098` (`_apply_wand_effect` 740 lines, 127 branches), `src/game_magic.py:1128-1945` (`_apply_spell_effect` 814 lines, 68 branches), `src/game_magic.py:2058-2453` (`_apply_scroll_effect` 396 lines, 45 branches), `src/food_system.py:389-732` (`drink_potion` 344 lines, 73 branches).

**The pattern**: Each function is one giant `if effect == 'heal' / elif effect == 'X' / elif effect == 'Y'` ladder over string literals. `_apply_wand_effect` is the worst at 740 lines and 127 branches. The handlers mostly share a small structural shape — `dur = self._wand_tier_duration(N, tier); dur, resisted = self._boss_resist_cc(target, dur); if resisted: msg(); else: target.add_effect(EFFECT, dur); msg()` — repeated 6+ times in the wand status-effect block alone (lines 399-451).

**Concrete proposal**: Extract a `WAND_HANDLERS: dict[str, Callable[[Wand, ...], None]]` per dispatcher; each handler is a small method `_wand_heal(self, wand)`, `_wand_haste_self(self, wand)`, etc. The dispatcher becomes:
```python
handler = self._WAND_HANDLERS.get(effect)
if handler is None:
    self.add_message("The wand fizzles.", 'warning'); return
handler(self, wand)
```
For the CC-status block, factor the duration-resist-message tuple into a small helper `_apply_cc_with_resist(self, target, effect_id, base_dur, tier, win_msg, lose_msg)`.

**Cost**: ~1,000 lines moved into individual handlers; +1 dispatch table (no method count growth — same methods, shorter names). Two-week task done a handler-at-a-time, NOT a single rewrite — keeps tests green at every step.

**Payoff**: Each handler becomes individually grep-able ("what does `cleanse_self` do?" answered in one file region instead of 200-line scroll). New effects no longer need to choose where in a 740-line elif chain to slot — they declare themselves in the table. Test-writability climbs dramatically: a future T5 spell-effect test can stub a single handler.

**Risk**: Subtle — handler order matters when the same `effect` string is reachable from multiple dispatchers (heal scrolls vs heal potions vs heal wands). Mitigation: do `_apply_wand_effect` first as proof, ship, then iterate. Existing tests in `test_spell_handlers.py` are the safety net.

---

## 2. 🟩 [HIGH] Lift `_pickup`'s 80-line inline chronicle dicts to module constants

**Files affected**: `src/main.py:3169-3203` (inside `_pickup`, 166 lines).

**The pattern**: Two large literal dicts are defined INSIDE the `_pickup` method body — `_CHRONICLE_ITEMS` (18-entry set) and `_CHRONICLE_FLAVOR` (18-entry dict of multi-sentence chronicle prose). They're allocated on every pickup. They're unreadable inside an already-large method, and any other code that wants to know "is this a chronicle-worthy item?" can't reach them.

**Concrete proposal**: Move both to module-level constants at the top of `main.py` (or, better, to a new `src/chronicle_data.py`):
```python
CHRONICLE_PICKUP_FLAVOR: dict[str, str] = { ... }
CHRONICLE_PICKUP_ITEMS = frozenset(CHRONICLE_PICKUP_FLAVOR)
```
Then `_pickup` becomes a 3-line lookup. Bonus: the `_MILESTONE_FLAVOR` dict inside `_change_level` (lines 705-716) has exactly the same problem — lift it too.

**Cost**: ~80 lines moved, no behavior change. 1 file touched (or 2 if a new module).

**Payoff**: `_pickup` shrinks from 166 to ~95 lines. Chronicle prose is editable in one obvious place. Other systems (e.g. encyclopedia, save-state debug) can read the same set.

**Risk**: None — pure data move. Verify with `pytest tests/`.

---

## 3. 🟩 [HIGH] Consolidate save-migration into a declarative `MIGRATIONS` table

**Files affected**: `src/main.py:354-540` (`load_state`, 187 lines, ~50 `hasattr` checks).

**The pattern**: `load_state` is a wall of `if not hasattr(self.player, 'X'): self.player.X = DEFAULT`. The 35 `hasattr` ladders + 7 `for _attr, _default in (...)` tuple sweep at line 442 mix concerns: player-attribute defaults, dungeon-attribute defaults, level-mgr attribute defaults. Every new feature appends to the bottom; nothing is ever removed; reading the function takes 4 page-downs.

**Concrete proposal**: Move to a declarative migrations table:
```python
# src/save_migrations.py
PLAYER_DEFAULTS: list[tuple[str, Any]] = [
    ('ranged_weapon', None),
    ('hack_tiers_claimed', lambda: set()),  # callable for mutable defaults
    ('quirk_progress', dict),
    ('total_identifies', 0),
    # ... etc
]

def apply_player_defaults(player) -> None:
    for attr, default in PLAYER_DEFAULTS:
        if not hasattr(player, attr):
            value = default() if callable(default) else default
            setattr(player, attr, value)
```
`load_state` becomes a 3-line orchestrator: apply player defaults, apply dungeon defaults, copy fields from `state` dict.

**Cost**: ~180 lines compressed to ~30; 1-2 files touched.

**Payoff**: A new feature adds ONE line to the table instead of scattering its `hasattr` block among 50 siblings. The lazy-callable pattern fixes a latent bug — current code uses `set()` as a literal default IN the for-loop tuple, which is fine, but a future maintainer copy-pasting an entry that puts `dict()` in the literal position would create a shared-mutable-default bug. Centralizing makes the rule visible.

**Risk**: Low. The `_saved_lm._planned_mini_bosses` and `dungeon.pits` migrations need to stay in `load_state` (they migrate non-player objects). Keep them inline, just shrink the player block.

---

## 4. 🟨 [MEDIUM] Add `tests/conftest.py` to absorb 35 copies of `sys.path` + `pygame.init`

**Files affected**: every test file (35) does the same `sys.path.insert(0, os.path.join(...src))` + many do `pygame.init() / pygame.font.init()`.

**The pattern**: Each test file opens with:
```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import pygame
pygame.init()
pygame.font.init()
```
35 copies. Some tests omit the pygame lines, which means individual tests can fail when run in isolation depending on import order.

**Concrete proposal**: Create `tests/conftest.py`:
```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame
pygame.init()
pygame.font.init()
```
pytest auto-discovers it and applies before any test in `tests/` collects. Then bulk-delete the boilerplate from every test file.

**Cost**: 1 new file, 35 small edits (each removes 4-6 lines). ~150 lines net deleted.

**Payoff**: Test files focus on what they test. Less drift risk (some files already missing the pygame init line — a future test that needs `font` will mysteriously fail in isolation). Easier to add a global fixture (e.g. a `tmp_save_dir` for save-lifecycle tests) once a conftest exists.

**Risk**: Negligible. Verify with `pytest tests/` after.

---

## 5. 🟨 [MEDIUM] Shared `_make_armor` / `_make_shield` / `_make_accessory` factories

**Files affected**: `tests/test_chain_equip.py:21-49`, `tests/test_chain_passives.py:16-44`. Possibly more.

**The pattern**: Both files define identical `_make_shield`, `_make_armor`, `_make_accessory` factories with the same defn dict shape. Future tests adding a new mechanic will need the same factory.

**Concrete proposal**: Add to `tests/conftest.py` (or a `tests/_factories.py`):
```python
def make_armor(**overrides):
    from items import Armor
    defn = {'id': 'test_armor', 'name': 'test armor', 'symbol': '[',
            'color': [200, 200, 200], 'ac_bonus': 3, 'slot': 'body'}
    defn.update(overrides)
    return Armor(defn)
# same for make_shield, make_accessory
```
Expose as pytest fixtures or plain importable functions.

**Cost**: 1 file (or new conftest section), 2 import-site edits. ~50 lines deleted.

**Payoff**: A new test for `tier_bonuses` doesn't need to recreate the boilerplate. Item-class constructor changes propagate from one place.

**Risk**: None.

---

## 6. 🟩 [HIGH] Delete 14 fake `try: from chain_passives ... except ImportError: pass` blocks in `main.py`

**Files affected**: `src/main.py` — 14 occurrences (lines 777, 796, 816, 836, 854 in `_change_level`; lines 1543, 2657, 3285, etc.)

**The pattern**:
```python
try:
    from chain_passives import player_has_passive, consume_passive_charge
    if player_has_passive(self.player, 'X') and consume_passive_charge(self.player, 'X'):
        ...
except ImportError:
    pass
```
`chain_passives.py` is a sibling module in `src/`. The user is on Python 3.14, the module imports cleanly, and main.py already imports from sibling modules unconditionally everywhere else. These `except ImportError: pass` clauses are dead.

**Concrete proposal**: Add `from chain_passives import player_has_passive, consume_passive_charge, passive_value, sum_passive_values` at the top of `main.py` (next to the existing imports). Delete the 14 inline try/except wrappers and inline imports.

**Cost**: ~80 lines deleted, 1 file touched.

**Payoff**: Less paper-mâché. Future maintainers can grep for `player_has_passive` without sifting through `try` clutter. If `chain_passives` legitimately becomes optional one day, *that* day add ONE module-level guard, not 14 try-except blocks.

**Risk**: Effectively none — the imports are already proven by `_do_move` (line 1629) using a bare `from chain_passives import player_has_passive` without protection.

---

## 7. 🟩 [HIGH] Render/handle_event mega-dispatch → state→method table

**Files affected**: `src/game_render.py:935-1121` (`render`, 187 lines, ~52-state elif chain), `src/game_input.py:50-268` (`handle_event`, 219 lines, ~37-state elif chain).

**The pattern**: Both `render()` and `handle_event()` end with a giant `if self.state == STATE_X: foo() / elif state == STATE_Y: bar()`. Every new state requires editing both methods. The mapping is essentially a constant once written.

**Concrete proposal**: Define class-level dispatch tables on Game:
```python
class Game(...):
    _RENDER_DISPATCH: ClassVar[dict[str, str]] = {
        STATE_TARGET: '_draw_targeting',
        STATE_QUIZ: '_draw_quiz',
        STATE_EQUIP_MENU: '_draw_equip_menu',
        # ...
    }
    _INPUT_DISPATCH: ClassVar[dict[str, str]] = { ... }

def render(self):
    # ... world draw ...
    method_name = self._RENDER_DISPATCH.get(self.state)
    if method_name:
        getattr(self, method_name)()
    if self._debug_overlay:
        self._draw_debug_overlay()
    pygame.display.flip()
```
The `_camera()` setup and message-log/sidebar draw stay inline because they fire every frame. Only the post-world modal branch becomes a dispatch.

**Cost**: 2 functions shrink from 187+219 lines to ~50 each. 2 dispatch tables added. ~280 lines net deleted.

**Payoff**: Adding a new modal becomes a 2-line patch (add a state + register the draw/input method in tables) instead of editing 2 elif chains. Forgetting to register surfaces as a clear "missing key" rather than a silent "modal renders but doesn't handle input" bug — the failure mode for the `STATE_PET_FEED + STATE_PET_HEAL + STATE_PET_SPECIALS` triplet which currently each manually call `_draw_pet_menu()` before the sub-menu (line 1044-1052). With dispatch, this becomes a list-of-callables.

**Risk**: Medium. The `_PET_FEED/HEAL/SPECIALS` cases compose two draws — needs `list[str]` or callable wrapper for those keys. Manual sweep of MROs to confirm no method-name collisions across mixins (memory file confirms there are none).

---

## 8. 🟨 [MEDIUM] Extract `_give_starting_kit`'s 8 repeated load+next+try blocks

**Files affected**: `src/main.py:1033-1324` (`_give_starting_kit`, 292 lines).

**The pattern**: For weapon / ammo / melee / wand / spellbook / shield / accessory / extras, the function repeats the same skeleton:
```python
start_X = b.get('_start_X', None)
if start_X:
    try:
        items_list = load_items('X')
        item = next((x for x in items_list if x.id == start_X), None)
        if item:
            item.identified = True
            self.player.known_item_ids.add(item.id)
            self.player.inventory.append(item)
    except Exception:
        pass
```
8 copies of this shape. Bonus: tuple-vs-string dispatch (`isinstance(start_X, tuple)`) is duplicated 3 times for weapon/melee/shield.

**Concrete proposal**: Extract a single helper:
```python
def _grant_starting_item(self, key: str, item_class: str,
                        instantiate=None, on_grant=None) -> Item | None:
    """Resolve b[key] as either unique-id or (template, material) tuple,
    add to inventory + mark known. Returns the item or None."""
    ref = (self.secret_build or {}).get(key)
    if not ref:
        return None
    try:
        if isinstance(ref, tuple) and instantiate is not None:
            item = instantiate(ref[0], ref[1])
        else:
            item = next((x for x in load_items(item_class) if x.id == ref), None)
        if not item:
            return None
        item.identified = True
        self.player.known_item_ids.add(item.id)
        if on_grant: on_grant(item)
        else: self.player.inventory.append(item)
        return item
    except Exception:
        return None
```
The function body becomes 8 one-line calls.

**Cost**: ~150 lines deleted from `_give_starting_kit`, 30 lines added in helper. 1 file touched.

**Payoff**: New starting-kit slot (e.g. `_start_potion` for a healer build) is one line. The bare `except Exception: pass` becomes one swallowing point — easier to add logging later if a build silently misfires.

**Risk**: Low. The shield/melee/weapon "lock and auto-equip" logic for cursed melee (line 1104-1109) is a special case — the `on_grant` callable parameter handles it.

---

## 9. 🟨 [MEDIUM] Lift duplicated `STATS` tuple to a module constant

**Files affected**: `src/main.py:3735,3749,3763` (3x), `src/game_divine.py` (2x), `src/game_magic.py` (2x), `src/quirk_system.py`, `src/mystery_system.py`, `src/chain_equip.py`. 10 occurrences across 6 files.

**The pattern**: Every place that needs to iterate the 6 primary stats spells out `('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')`. No named constant.

**Concrete proposal**: Add to `src/player.py` (where Player owns these as attributes):
```python
PRIMARY_STATS: tuple[str, ...] = ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')
```
Replace the 10 sites.

**Cost**: 1 line added, 10 short edits.

**Payoff**: When a future stat is added or renamed (PER → PRC?), one line of churn. Also makes `cooking_stat_gained` init in Player.__init__ less hand-rolled: `{s: 0 for s in PRIMARY_STATS}`.

**Risk**: None. Verify with `pytest tests/`.

---

## 10. ⬜ [LOW] Bug: `add_message(..., 'good')` falls back to 'info'

**Files affected**: `src/main.py:3774`.

**The pattern**: A SINGLE typo — `'good'` instead of `'success'`. `MessageLog._MSG_COLORS` has only `info`/`success`/`warning`/`danger`/`loot`; `dict.get(msg_type, _MSG_COLORS['info'])` silently fall-backs to info coloring. The XYZZY tier-1 "Reality grants you Regeneration!" line displays in dull info-grey instead of celebratory green.

**Concrete proposal**: One-character fix — `'good'` → `'success'`. Also: add a guard test:
```python
# tests/test_message_types.py
def test_no_unknown_message_types():
    """ALL add_message(..., msg_type) sites use a known type."""
    import re
    from ui import _MSG_COLORS
    valid = set(_MSG_COLORS) | {'combat'}  # combat may be added in MessageLog ext
    for f in glob('src/*.py'):
        for line, m in enumerate(open(f), 1):
            mt = re.search(r"add_message\([^,]+,\s*'([a-z_]+)'\)", m)
            if mt:
                assert mt.group(1) in valid, f"{f}:{line} uses {mt.group(1)!r}"
```

**Cost**: 1 char + 15-line test = 16 lines.

**Payoff**: User sees the right color on hack-reality tier 1. Test prevents the next typo.

**Risk**: None — visual change only.

---

## 11. 🟨 [MEDIUM] Six `overlay = Surface(WINDOW_W,H); fill((0,0,0,A))` snippets → `_modal_overlay(alpha=A)` helper

**Files affected**: `src/game_render.py:208,252,310,447,1366` (5 in main render mixin) + similar copies in `study_mode.py` and `welcome_screen.py`.

**The pattern**:
```python
overlay = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
overlay.fill((0, 0, 0, 190))   # or 220
self.screen.blit(overlay, (0, 0))
```
Three lines, repeated. `fantasy_ui.draw_overlay` already exists for some panels; the hand-rolls bypass it.

**Concrete proposal**: Two paths:
1. Use the existing `fantasy_ui.draw_overlay(screen, alpha=190)` for ALL 5 sites — confirm signature matches.
2. Or, add `self._modal_overlay(alpha=190)` to a Game mixin since all 5 sites have `self.screen` handy:
```python
def _modal_overlay(self, alpha: int = 190) -> None:
    o = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H), pygame.SRCALPHA)
    o.fill((0, 0, 0, alpha))
    self.screen.blit(o, (0, 0))
```

**Cost**: ~15 lines deleted, 1 helper added. 3 files touched.

**Payoff**: A future "user wants dimmer modals" change is one line. Aligns with `PanelBuilder`'s `overlay_alpha` parameter — same vocabulary.

**Risk**: None.

---

## 12. 🟨 [MEDIUM] Inline `import random as _rng` is redundant in 41 sites

**Files affected**: `src/main.py` (13), `src/game_encounters.py` (9), `src/game_combat.py` (5), `src/game_magic.py` (4), `src/level_manager.py` (4), `src/game_divine.py` (3), `src/game_input.py` (2), `src/welcome_screen.py` (1).

**The pattern**: All 8 files have `import random` already at the top. Then inside methods they re-import `import random as _rng` and use `_rng.random()`, `_rng.choice()`. Pure cargo-cult — the top-level `random` is in scope.

**Concrete proposal**: Bulk-replace `_rng.` with `random.` after the inline imports are stripped. Use the Edit tool's `replace_all` mode or a one-off `tools/refactor_inline_random.py` script.

**Cost**: ~41 lines deleted, ~80 `_rng.X` → `random.X` substitutions. 8 files touched.

**Payoff**: Cleaner. Less noise per method. Reader is no longer confused into thinking inline import implies "this branch can be loaded without `random`".

**Risk**: Minor — check there's no shadowing by a local `random` variable. Grep confirms there isn't.

---

## 13. 🟩 [HIGH] Move ALL hand-rolled modal panels to `PanelBuilder`

**Files affected**: `src/game_render.py` has 20 `draw_dark_panel(...)` direct calls but only 7 `PanelBuilder(...)` calls. Also `study_mode.py`, `welcome_screen.py`.

**The pattern**: Despite `panel.py:1-24` docstring explicitly saying "every modal that follows the grimoire identity should be drawn through this module instead of hand-rolling", 13+ modals still hand-roll. Each defines its own `bw`, `bh`, `bx`, `by`, calls `draw_dark_panel`, then writes its own header / body / footer-hint draws. Drift risk: padding, border-radius, footer-hint font, scrollbar all subtly differ between hand-rolls.

**Concrete proposal**: Convert one hand-rolled modal per session (e.g. start with `_draw_xyzzy_input`, `_draw_xyzzy_confirm`, `_draw_qa_warp_popup` — all small). For each:
1. Replace overlay+rect+border lines with a `PanelBuilder(self.screen, size=SIZE_SM, border_color=...)`.
2. Move title text into `p.set_title()`.
3. Move footer hint into `p.set_footer_hint()`.
4. Custom body draws into `body_rect = p.body_rect(); ... `.
5. Final `p.draw()`.

**Cost**: ~30 lines per modal × 13 modals = ~400 lines saved over time. Iterative.

**Payoff**: User-visible — header/footer rhythm matches across modals. Refactor pain disappears: a "user wants header gold tone darker" request becomes a one-line fix in `panel.py` instead of grep-and-edit across 20 hand-rolls. Matches the memory `feedback_paint_order_bugs.md` lesson — `PanelBuilder.__init__` is structured so bg paints first.

**Risk**: Some hand-rolls (XYZZY green-terminal, warning amber) use NON-grimoire colors. `PanelBuilder.border_color` already covers this case — works.

---

## 14. ⬜ [LOW] Method-local `import items` in 119 sites

**Files affected**: `src/main.py` (~35 inline), `src/dungeon.py` (~20), `src/game_render.py` (~6), and more. Total 119 deferred + 6 top-level.

**The pattern**: Tons of `from items import (Weapon, Armor, Shield, ...)` inside method bodies. Originally a circular-import dodge — `items.py` may have once imported `player`/`monster` for type hints. Today most aren't justified by circular concerns; they're just inline because the top-level import line at module top got long.

**Concrete proposal**: Audit the 119 inline imports against the 6 top-level. Where the inline isn't avoiding a real circular import, lift to module top. For files with genuinely huge import surface (`main.py` already has the 18-name import at line 18), consider a `src/items_types.py` namespace export:
```python
# src/items_types.py
from items import (Weapon, Armor, Shield, Corpse, Ingredient, Artifact,
                   Container, Lockpick, Accessory, Wand, Scroll, Spellbook,
                   Ammo, Food, Potion)
__all__ = [...]
```
Then `from items_types import *` is the one import every consumer needs.

**Cost**: Larger churn (~100 edits) for modest gain. Best done opportunistically — every time you touch a method with an inline `from items import`, lift it.

**Payoff**: Module-level imports are visible to readers/IDEs without traversing into method bodies.

**Risk**: Reintroducing circular imports if any of the inlines was load-bearing. Run `pytest` after each batch of lifts.

---

## 15. 🟨 [MEDIUM] BUC delta pattern → `buc_enchant_delta(buc) -> int` helper

**Files affected**: `src/game_magic.py:2134, 2237, 2274` (3 sites in `_apply_scroll_effect`). Also similar BUC-multiplier patterns in `food_system.py:408-410`.

**The pattern**: For scroll-of-enchantment style effects:
```python
delta = 2 if _scroll_buc == 'blessed' else (-1 if _scroll_buc == 'cursed' else 1)
```
3 sites in scroll handler. Also food has:
```python
_heal_mult = 1.5 if buc == 'blessed' else (0.5 if buc == 'cursed' else 1.0)
_buff_mult = 1.5 if buc == 'blessed' else (0.5 if buc == 'cursed' else 1.0)
_harm_mult = 0.0 if buc == 'blessed' else (1.5 if buc == 'cursed' else 1.0)
```

**Concrete proposal**: Add small helpers near `game_helpers.py`:
```python
def buc_enchant_delta(buc: str) -> int:
    """Scroll-of-enchantment delta: blessed=+2, uncursed=+1, cursed=-1."""
    return {'blessed': 2, 'cursed': -1}.get(buc, 1)

def buc_heal_mult(buc: str) -> float:
    return {'blessed': 1.5, 'cursed': 0.5}.get(buc, 1.0)

def buc_harm_mult(buc: str) -> float:
    return {'blessed': 0.0, 'cursed': 1.5}.get(buc, 1.0)
```

**Cost**: ~15 lines helper, ~6 call-site fixes. 2-3 files touched.

**Payoff**: One canonical place for "what does BUC do?". Naming makes scroll-vs-food intent clearer at call-site. Easier to write `test_buc_helpers.py`.

**Risk**: None.

---

## 16. ⬜ [LOW] Stale memory document — verify against current state

**Files affected**: `~/.claude/.../memory/project_architecture.md` (cited at session start).

**The pattern**: The memory file (18 days old, flagged by the harness) claims:
- `main.py` is ~4,065 lines remaining — actual today: **5,443 lines** (grew ~34%)
- `game_render.py` is 3,590 lines — actual today: **4,626 lines**
- `game_magic.py` is 2,357 — actual today: **3,150**

**Concrete proposal**: Run a `consolidate-memory` pass to refresh module sizes. Not a code refactor but worth flagging — these are the numbers a future "should I split this further?" decision will be made against.

**Cost**: Memory edit only.

**Payoff**: Future me doesn't underestimate the god-class.

**Risk**: None.

---

## 17. 🟨 [MEDIUM] `_advance_turn` (205 lines) is a turn-orchestrator god-method

**Files affected**: `src/main.py:2287-2491` (`_advance_turn`, 205 lines).

**The pattern**: One method touches: turn counter, quirk hooks, prayer cooldown, recall lore cooldown, abaddon resistance restore, hack-reality cooldown, hero-special cooldowns, elder-blood escape, chain-escape, monster status ticks, player status ticks (with embedded death checks), wall-phasing safety net, warning/searching/secret-door/trap/ambush detection ticks, unicorn NPC tick, Eye of Horus passive regen + mastery scaling, Coat-of-Cú-Chulainn berserk trigger, Seal-of-Solomon pacify, clairvoyant reveal, Torc-of-Boudicca surrounded AC.

**Concrete proposal**: Extract focused tickers as methods on a new `PassivesTickMixin` (or just on Game, named consistently):
```python
def _advance_turn(self):
    self.turn_count += 1
    self._tick_special_cooldowns()
    self._tick_pending_escapes()
    self._tick_monster_statuses()
    if self._tick_player_statuses(): return  # death path
    self._tick_position_safety()
    self._tick_detection_passives()
    self._tick_accessory_passives()
    self._tick_environment_responses()
```
Each ticker is 10-30 lines. The orchestrator stays at ~25 lines.

**Cost**: ~205 lines redistributed into 7-8 named methods of 15-30 lines each. Net no change. 1 file touched.

**Payoff**: A new accessory passive ("ring of regen-on-low-HP") adds to ONE ticker method, not at line ~2440 of a 205-line beast. Reading `_advance_turn` becomes possible. The "death from status tick" tests are easier to localize.

**Risk**: Medium. Order of effects matters (status ticks before regen before detection — currently implicit by line order). Document the order with a docstring on `_advance_turn` after the refactor. `tests/test_death_from_status_tick.py` is the regression guard.

---

## 18. ⬜ [LOW] `name` collision: `fit_text` / `wrap_text` exist in two modules with different ellipsis

**Files affected**: `src/game_helpers.py:92,103`, `src/fantasy_ui.py` (similar functions, `...` instead of `…`).

**The pattern**: Per memory `project_architecture.md` Gotcha #2: "`fit_text` / `wrap_text` name clash. `game_helpers.py` and `fantasy_ui.py` both export functions with these names, with slightly different ellipsis behavior (`'…'` vs `'...'`). `main.py` aliases the game_helpers versions as `_gh_fit_text` / `_gh_wrap_text`."

**Concrete proposal**: Pick one. The `game_helpers` versions re-export from `text_layout` (the canonical impl). The `fantasy_ui` versions look like older, lower-quality copies that survived the extraction.

Option A: deprecate `fantasy_ui.fit_text/wrap_text`, fix the 1-2 menu-chrome callers to use `text_layout` directly.
Option B: keep both but rename the `fantasy_ui` versions to `_ftext_old` / `_wrap_old` so the name collision goes away.

**Cost**: ~5-line change in fantasy_ui + 2-3 call-site updates.

**Payoff**: Removes a memory gotcha. New code doesn't have to remember which ellipsis they're getting.

**Risk**: Low — both behave correctly, just visually different ellipsis glyph. User-visible only if both are visible side-by-side.

---

## 19. 🟨 [MEDIUM] Floor-trap dispatch (`if trap_type == 'X' / elif...`) - same pattern as effect dispatch

**Files affected**: `src/main.py:2552-2645` (`_check_floor_trap`, 128 lines, 10-branch dispatch).

**The pattern**: After deciding "trap fires", a 90-line `if trap_type == 'pit' / elif 'alarm' / elif 'acid' / elif 'teleport' / elif 'fire' / elif 'sleep_gas' / elif 'bear_trap' / elif 'squeaky_board' / elif 'rust' / elif 'polymorph'` chain. Same dispatch-by-string pattern as wand/spell effect.

**Concrete proposal**: Define a `_FLOOR_TRAP_HANDLERS` dict on Game:
```python
_FLOOR_TRAP_HANDLERS: ClassVar[dict[str, str]] = {
    'pit': '_trap_pit', 'alarm': '_trap_alarm', 'acid': '_trap_acid', ...
}
def _check_floor_trap(self, x, y):
    # ... preamble (PER avoidance, damage roll, etc.) ...
    handler = self._FLOOR_TRAP_HANDLERS.get(trap_type)
    if handler:
        getattr(self, handler)(x, y, trap)
```
Each handler 5-15 lines.

**Cost**: ~95 lines redistributed. 1 file touched.

**Payoff**: A new trap type is a one-table-entry + one-method add. Currently it's "find the right place in a 90-line chain and don't break a sibling".

**Risk**: Low.

---

## 20. ⬜ [LOW] Comment that may have lied: `_apply_thrown_potion` resistance check

**Files affected**: `src/game_combat.py:489-503`.

**The pattern**: Code says `# Check resistance via status effects` and iterates `_RESIST_BLOCKS`. The variable `blocked` is used as `if debuff in blocked`, but `_RESIST_BLOCKS.items()` returns `(resist_effect, blocked_debuffs_set)`. Confirmed the comment is accurate, this isn't a lie. False alarm — but flag noted because the inline scan saw a suspicious pattern. Documenting that I checked.

**Concrete proposal**: No change needed.

**Cost/Payoff/Risk**: N/A.

---

## TOP 5 priority refactors

1. **#1 — Effect-dispatch tables for wand / spell / scroll / potion** (🟩 HIGH)
   The single largest readability + extensibility win. 313 elif branches → small dispatch tables + named handlers. ~1,000 lines move. The Kit-table refactor that already shipped (`3d5f78c`) is the proven model: extract once, every future addition gets cheaper.

2. **#3 — Declarative `MIGRATIONS` table in `load_state`** (🟩 HIGH)
   `load_state` is the second-worst function readability after the effect dispatchers. 35 `hasattr` checks compress to a 30-line table. Direct unblock for the next time the user adds a new player attribute.

3. **#7 — Render/input mega-dispatch → state→method table** (🟩 HIGH)
   Adding a new game state currently requires touching 2 elif chains across 2 mixins, with no help if you forget one. Tables make this safe and visible.

4. **#6 — Delete the 14 fake `try: chain_passives ImportError` blocks** (🟩 HIGH)
   Pure dead-code removal, low risk, very visible cleanup. Quick win that primes the bigger refactors.

5. **#4 — `tests/conftest.py`** (🟨 MEDIUM, but very cheap)
   35 test files × 6 lines of boilerplate = ~150 lines deleted, plus catches "test passes in suite but fails in isolation" drift. Smallest cost-per-payoff ratio in the list.

---

**Count**: 20 candidates documented. 6 HIGH (🟩), 9 MEDIUM (🟨), 5 LOW (⬜).
