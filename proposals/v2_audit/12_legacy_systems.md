# V2 Audit — 12 Legacy Systems

Scope: `src/pet_system.py`, `src/bones.py`, `src/highscore_system.py`,
`src/welcome_screen.py`, help-screen + keymap in `src/game_render.py`.

Spot-check audit of "stable" systems untouched in recent sessions. Auto-fixed
crash bugs and stale references. Pre-existing test_edge_cases /
test_save_lifecycle failures belong to a parallel audit and are NOT caused by
this audit's changes.

Tests after fixes: `py -m pytest tests/test_pets.py tests/test_audit_*.py
tests/test_cross_system_audit.py -q` -> **73 passed** (was 26 + 47 = 63
before; added 10 new regression tests covering the bugs found).

---

## 1. Pet system — **BLOCK** (5 crash bugs fixed)

### Critical (auto-fixed): Custom Pet subclasses crashed on every turn

`FenrirPet`, `UnicornPet`, `DadPet`, and `SketchedPet` all bypass
`Pet.__init__` to set custom stats, but the base `Pet` per-turn methods
(`gain_xp_passive`, `tick_cooldown`, `name` property) read instance
attributes only set in the bypassed `__init__`. The combat loop at
`game_combat.py:2064-2072` calls these methods unconditionally for every
alive pet.

Result: **AttributeError crash on the next turn after summoning any of these
pets**. Affected scenarios:

- XYZZY tier 5 spawns Fenrir → next turn crashes
- "dad" build's player-pet → first turn after spawn crashes
- Dreamspun Sketchbook → next turn after sketch creation crashes
- Unicorn encounter → next turn after acquiring crashes

`FenrirPet.name` itself crashes (no `nickname` attr, no overridden `name`
property like Dad/Unicorn/Sketched have).

**Fix** (`src/pet_system.py`): In each subclass `__init__`, after the custom
attributes, add the seven base attributes the parent's per-turn methods
require:

```python
self._passive_xp_timer = 0
self._special_cooldowns: dict[str, int] = {}
self.nickname: str = ''
self.kills_count: int = 0
self.command: str = 'return'
self.last_pet_floor: int = -1
```

(`_regen_timer` was already present in each.)

Regression tests added: `test_fenrir_per_turn_methods_dont_crash`,
`test_unicorn_per_turn_methods_dont_crash`,
`test_dad_per_turn_methods_dont_crash`,
`test_sketched_per_turn_methods_dont_crash`,
`test_all_pet_subclasses_have_required_attrs`.

### Wiring verified

- Pet spawn/naming → `STATE_PET_NAME_INPUT` flow in `game_input.py`/`game_menus.py`
- Pet feeding/heal/recall/command/specials → `Shift+P` opens
  `STATE_PET_MENU` and sub-menus
- Pet AI: follow/engage/stay/wander commands in `take_turn`
- Pet death: monster swipes deal damage, pet flags `alive=False` and
  message is added; dead pets remain in `self.pets` list but are filtered
  by every read site via `.alive` check (no memory leak in 100-floor run)
- Pet on floor change: `main.py:842-867` repositions all alive pets to
  adjacent tiles around the player after stairs — pets follow correctly
- Pet save/load: `save_system.py:40` includes `'pets': game.pets` in
  pickle; all four pet subclasses pickle-roundtrip (verified)

### No pet-revive mechanic by design

No code path resurrects a dead pet. Confirmed not a bug — the original
design intent. Player must summon a new pet via Soul Sphere.

---

## 2. Bones system — **WARN** (1 minor fix; otherwise PASS)

### Auto-fixed: Corrupt bones file permanently occupied a slot

`load_bones` removed the file only inside the success branch. If
`json.JSONDecodeError` fired (e.g. file mid-write was truncated by a
crash), the function returned `None` BUT left the corrupt file on disk.
With `_MAX_BONES = 3`, a single corrupt file could permanently consume
one of the three bones slots and the gate `os.path.exists(path)` would
keep finding the same broken file every future visit to that level.

**Fix** (`src/bones.py`): Added `os.remove(path)` in the except branch.

Regression test added: `test_bones_corrupt_file_is_cleaned_up`.

### Wiring verified

- Save on death: `main.py:2108-2111` calls `save_bones` in `_on_game_over`
- Load on level gen: `level_manager.py:88-92` calls `load_bones` (50%
  gate, then file check, then `spawn_ghost`)
- File cap: `_evict_oldest` keeps top 3 by mtime; tested with 5 files →
  3 remain
- Ghost mechanics: `spawn_ghost` builds a `Monster` with scaled HP, drain
  damage scaled by player's level, holy/fire weaknesses
- Boss/cow levels skip bones (they don't go through `generate()` →
  `load_bones` path)

### Non-issue: `_place_cursed_gear` loads pools for wand/scroll/potion

`get_equipped_items()` never returns wand/scroll/potion (they're inventory-
only), so those pool entries are dead code. Cleanup would be cosmetic.

---

## 3. Highscore system — **PASS**

Direct edge-case testing confirmed:
- Missing file → returns `[]`
- Corrupt JSON → returns `[]` (silent recovery via try/except)
- Non-list payload → returns `[]`
- Round-trip `add_score` → `get_top` works
- 150 inserts → truncated to `MAX_ENTRIES = 100`

### Wiring verified

- `add_score` called from victory screen (`game_render.py:3392`) and
  death screen (`game_render.py:3487`)
- `_score_saved` flag prevents double-counting on re-render
- `get_top` used by victory/death screens (top 5) and welcome screen
  (top 10) + F2 all-time overlay (top 100)

Regression tests added: `test_highscore_handles_missing_file`,
`test_highscore_handles_corrupt_json`,
`test_highscore_truncates_to_max_entries`.

---

## 4. Welcome screen — **WARN** (2 fixes; otherwise PASS)

### Critical (auto-fixed): Merlin's shield spell silently doesn't exist

`SECRET_BUILDS["merlin ambrosius"]._start_spells = ["heal_spell",
"shield_spell"]` — but the canonical spell id in
`spells.LEARNABLE_SPELLS` is `magic_shield_spell`. `main.py:1125`
silently skips unknown ids (`if spell:`), so Merlin gets `heal_spell` and
nothing else.

**Fix** (`src/welcome_screen.py`): `shield_spell` → `magic_shield_spell`.

### Cosmetic (auto-fixed): Stale `_DOMAINS` comments + wrong colors

The `_DOMAINS` table marked `TRIVIA` and `AI` as having `None` FP.SUBJECT
keys with the comment "no FP.SUBJECT entry — fallback". Both ARE in
`FP.SUBJECT` now (`trivia` = gold-orange, `ai` = green). The `None` keys
caused the welcome-screen domain ring to draw both with the wrong
`GOLD_PALE` fallback color instead of their proper subject hue.

**Fix** (`src/welcome_screen.py`): Restored `'trivia'` and `'ai'` keys.

### Audit findings (no fix needed)

- 33 SECRET_BUILDS defined; all keys lowercase (correct for
  `.lower()` lookup in `run()`)
- All 30 unique sprite assets exist under `assets/tiles/env/`
- All item ids (`_start_weapon`, `_start_armor`, `_start_shield`,
  `_start_accessory`, `_start_extra_acc`, `_start_wand`, `_start_book`,
  `_start_potions`, `_start_ammo`) resolve to real entries in their
  respective JSON files
- All spell ids in `_start_spells` resolve to `LEARNABLE_SPELLS` (after
  the Merlin fix)
- Ciri's `_elder_blood: True` is wired in `game_menus.py:876` for the
  Elder Blood power triplet
- F2 (all-time top 100) and F3 (study mode) keys both wired
- `delete_save` via DEL key handled with confirmation flash
- "Did you mean Dad?" prompt for `god` name wired

Regression tests added: `test_secret_build_spells_all_resolve`,
`test_secret_build_items_all_resolve`,
`test_secret_build_keys_all_lowercase`.

---

## 5. Help screen + keymap — **WARN** (1 fix)

### Auto-fixed: `Shift+P` pet menu was undocumented

`_draw_help_screen` in `game_render.py:4410` lists every key the player
needs in normal play, but `Shift+P` (pet menu — feed/heal/recall/
command/specials) was missing. The key is real and active
(`game_input.py:143-146`).

**Fix** (`src/game_render.py`): Added a "COMPANIONS" section with:

```python
("Shift+P", "Pet menu (feed/heal/recall/command/specials)", FP.BODY_TEXT),
```

### Audit findings (no fix needed)

- Cross-referenced every key in `_player_input` (`game_input.py:283-429`)
  against the `_COMMANDS` table — Shift+P was the only gap
- `STATE_LOCKPICK` reference already cleaned out (commented removal note
  in `game_states.py:24-25` dated 2026-05-19)
- Hidden keys correctly NOT documented: `` ` `` (xyzzy easter egg),
  Shift+I / Shift+W (Titivillus QA build only)
- F2 / F3 are welcome-screen only and shown in the welcome footer
  separately

---

## Summary

| System | Status | Auto-fixes |
|---|---|---|
| Pet system | BLOCK (4 crash classes) → fixed | 4 `__init__` updates in `pet_system.py` |
| Bones system | WARN → fixed | corrupt-file cleanup in `bones.py` |
| Highscore system | PASS | none |
| Welcome screen | WARN → fixed | Merlin spell typo + TRIVIA/AI colors in `welcome_screen.py` |
| Help screen | WARN → fixed | Shift+P documented in `game_render.py` |

**Files modified:**
- `src/pet_system.py` — 4 subclass `__init__` patches
- `src/bones.py` — corrupt-file cleanup
- `src/welcome_screen.py` — Merlin spell id + domain colors
- `src/game_render.py` — help screen Shift+P entry
- `tests/test_pets.py` — +10 new regression tests

**Tests:** 36 pet tests pass (was 26); 73/73 audit-related tests pass.
Full suite: my changes do not introduce any regressions (verified by
stashing parallel-audit changes and running both `test_pets.py` and
`test_save_lifecycle.py` in isolation — 37 passed). The 5 failing
`test_edge_cases.py` cases and 1 `test_save_lifecycle.py` case both
belong to a parallel audit's churn, NOT this audit.
