# Save / Highscore / Crash / Paths

**v2.18.0** (shipped 2026-10-02)

Covers the four small modules that persist state **outside** the main
Game loop and the one migration seam inside `Player`.

**Sources:**
- `src/save_system.py` — per-name pickle saves, atomic write
- `src/highscore_system.py` — JSON leaderboard
- `src/crash_handler.py` — crash report writer + emergency save
- `src/paths.py` — dev vs. frozen path resolution
- `src/player.py::__setstate__` — the save migration seam (v2.18 adds
  mastery-attr pop)
- `src/game_log.py` — the rolling `ERROR_LOG.txt` + log_dir helpers
  (brief overview — this doc focuses on save/meta)

---

## 1. The four files at a glance

| File | Role | Format | Writable location |
|---|---|---|---|
| `save_<name>.pkl` | per-player run state | Pickle (HIGHEST_PROTOCOL) | `save_dir()` |
| `highscores.json` | top-100 scores | JSON (indent 2) | `save_dir()` (frozen) / project root (dev) |
| `crash_YYYYMMDD_HHMMSS.txt` | one-shot crash report | plain text | `log_dir()` |
| `ERROR_LOG.txt` | rolling runtime log | plain text | `log_dir()` |

The last three live beside each other so a playtester finds them in
one place. Save files live in `save_dir()` (same base folder on
Windows when frozen).

---

## 2. `paths.py` — dev vs. frozen path split

### 2.1 `_root()`

```python
def _root() -> str:
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS          # PyInstaller onefile extract dir
    return os.path.join(os.path.dirname(__file__), '..')
```

- **Dev:** project root (one up from `src/`).
- **Frozen:** `sys._MEIPASS` — PyInstaller extracts bundled assets
  here on launch. Read-only; do NOT try to write under it.

### 2.2 `data_path(*parts)`

```python
def data_path(*parts: str) -> str:
    return os.path.normpath(os.path.join(_root(), *parts))
```

Used for every read-only asset load: `data_path('data',
'monsters.json')`, `data_path('assets', 'tiles', 'player.png')`. Never
pass a user-supplied name here — the function is strictly for
project-shipped files.

### 2.3 `save_dir()` — writable base

```python
if frozen on Windows:   %APPDATA%\PhilosophersQuest\
if frozen on macOS:     ~/Library/Application Support/PhilosophersQuest/
if frozen on Linux:     $XDG_DATA_HOME/PhilosophersQuest/
                        or ~/.local/share/PhilosophersQuest/
if dev:                 project root (unchanged)
```

`os.makedirs(base, exist_ok=True)` runs on every call so a fresh
install writes a clean folder.

**Why it matters:**
- A frozen build writing saves next to the executable fails under
  `Program Files` (ACL-denied). The APPDATA move dates from the
  first installer ship.
- A **dev session** uses the project root. "Run it" means `python
  src/main.py` (per the memory rule), NOT the dist exe — because the
  save dir differs. Loading a run under the exe can't surface changes
  made against the dev save.

### 2.4 `fmt_id`, `a_or_an`

Two string helpers that happen to live here:
- `fmt_id('wild_swing')` → `'wild swing'` — snake_case → display.
- `a_or_an('acorn')` → `'an acorn'`; handles `{blessed}` BUC tags by
  stripping leading `{` before picking the article.

---

## 3. `save_system.py`

### 3.1 Save path

```python
def _save_path(name: str) -> str:
    safe = re.sub(r'[^\w\-]', '_', name.lower())
    return os.path.join(save_dir(), f'save_{safe}.pkl')
```

Sanitizes the player name to `[A-Za-z0-9_-]`, lowercased.

**Collision note (SYSTEMS_AUDIT §10 P2):** `"Alice!"` and `"Alice?"`
both reduce to `save_alice_.pkl`. Permadeath + name collision = silent
overwrite. Not yet mitigated — adding a counter suffix on collision is
the recommended fix.

### 3.2 Save existence

```python
def save_exists(name: str) -> bool:
    path = _save_path(name)
    return os.path.exists(path) and os.path.getsize(path) > 0
```

A 0-byte file (from a pre-atomic-write failed dump) is treated as no
save — doesn't masquerade as loadable. Fail-safe.

### 3.3 `save_game(game)` — atomic write

**State dict** (`save_system.py:83-156`):

```
state = {
    'player':                 game.player,
    'player_name':            game.player_name,
    'secret_build':           game.secret_build,
    'turn_count':             game.turn_count,
    'dungeon_level':          game.dungeon_level,
    'player_gold':            game.player_gold,
    'level_mgr':              game.level_mgr,
    'dungeon':                game.dungeon,
    'monsters':               game.monsters,
    'ground_items':           game.ground_items,
    'correct_answers':        game.correct_answers,
    'wrong_answers':          game.wrong_answers,
    'missed_questions':       [...]       # post-death review
    'quiz_stats':             {...}        # per-subject per-tier
    'pets':                   game.pets,
    'seals_broken':           game.seals_broken,
    'heavenly_host_active':   bool,
    'abaddon_resist_removed_turns': int,
    '_l100_altars_used':      set,
    'karma':                  int,          # clamped -10..+10 by setters

    # NPC / flavor encounter tracking
    '_npc_encounter_levels':  dict,
    '_encountered_npcs':      set,
    '_flavor_encounter_levels': dict,
    '_encountered_flavor_npcs': set,

    # Boss / plot state
    '_abaddon_empowered':     bool,
    '_locusts_strengthened':  bool,
    '_judgment_resolved':     bool,
    '_npc_triggered_items':   set,
    '_npc_trigger_item_levels': dict,
    '_npc_trigger_items_placed': set,
    'player_title':           str,

    # Ascent / Death Pursuer
    'death_pursues':          bool,
    'death_monster':          Monster | None,
    '_secret_victory':        bool,

    # Deep-lore item spawn tracking
    '_lore_levels':           dict,
    '_lore_placed':           set,

    # One-cosmetic-per-item: per-run accessory appearance
    '_appearance_map':        dict,

    # Quirks (full object)
    'quirk_system':           QuirkSystem,

    # Secret cow level
    '_cow_poke_count':        int,
    '_cow_level_done':        bool,
    '_cow_spawned':           bool,
    '_cow_level':             int,
    '_cow_return_level':      int,

    # Per-floor charge flags
    '_first_hit_used':        bool,
    '_death_save_used':       bool,
    '_tarnhelm_used':         bool,
    '_quiz_reroll_used':      bool,

    # Chronicle guards
    '_chronicle_abaddon_start': bool,

    # Magic carrot + ethereal unicorn one-shot spawns
    '_magic_carrot_spawned':  bool,
    '_magic_carrot_target_level': int | None,
    '_unicorn_spawned':       bool,
    '_unicorn_target_level':  int | None,

    # Encyclopedia tab state
    '_chronicle':             list,
    '_recalled_hints':        list,
    '_cooked_recipes':        list,

    # Quiz deck shuffle position (anti-repeat on reload)
    'quiz_deck_state':        {...},
}
```

**Write sequence:**

```python
with open(tmp, 'wb') as f:
    pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
os.replace(tmp, path)   # atomic; never touches `path` unless dump succeeded
```

**Why atomic:** before this change (CLAUDE.md save-lifecycle rule), a
Pickle error mid-dump could leave `save_<name>.pkl` as a truncated
0-byte file — permadeath turning into instant run-death on next
reload. The temp + `os.replace` pattern means an unpicklable attribute
leaves the previous good save intact; only `<path>.tmp` is discarded.

**Common pickle hazards:**
- Pygame `Surface` objects on `player._combat_game_ref` —
  `Player.__getstate__` pops this (see §6.1).
- Bound methods set at runtime (`player._appearance_stamp`) — also
  popped in `__getstate__`.
- A quirk-system callback accidentally caching the Game — rare, but
  the `_find_unpicklable` helper (`save_system.py:25-71`) locates it.

**`_find_unpicklable(obj, path='state')`:** best-effort localizer.
Walks the state tree, honoring `__getstate__`, descending only into
subtrees pickle can't serialize. Returns up to 8 `(attribute_path,
typename)` tuples. On save failure, these are printed AND logged via
`game_log.log_error` so a tester's `ERROR_LOG.txt` names the exact
field.

**Mixed idiom caveat (SYSTEMS_AUDIT §10 P4):** some fields use bare
`game.xxx` (player_name, dungeon_level, player_gold) and others use
`getattr(game, 'xxx', default)`. The bare fields are "must exist";
getattr-with-default fields are migrations-friendly. Keep the pattern
when adding new fields — new state should use `getattr` with a safe
default so old pickles don't `AttributeError` on save.

### 3.4 `load_game(name)`

```python
try:
    with open(_save_path(name), 'rb') as f:
        return pickle.load(f)
except Exception as e:
    log_error(f"load_game failed for {name!r}: {e}")
    return None
```

Returns the state dict (not a Game instance). `main.Game` reads keys
from it in `_load_run`. No automatic migration — attributes added
after a save was written are populated via `getattr` defaults in
`main.Game.__init__` or via `Player.__setstate__` (see §6).

### 3.5 `delete_save(name)`

```python
try:
    path = _save_path(name)
    if os.path.exists(path):
        os.remove(path)
except Exception:
    pass
```

Called on **permadeath** (`_on_game_over` on death branch). Also
called from the welcome screen's Delete-key shortcut (user wipes a
run before starting). Victory does NOT delete the save by design —
the save is kept so the player can review the final state.

**Known bug (SYSTEMS_AUDIT §4 P1):** `_on_game_over` unconditionally
saves a bones file on victory and also plays the `'death'` sound.
Victory path should skip bones + skip delete + skip death sound; the
fix refactors `_on_game_over` to take explicit `reason` + `is_victory`.

### 3.6 No schema version yet

The state dict is unversioned. Adding a `schema_version: int` key +
a load-time migration hook is deferred item #5 in CLAUDE.md. Until
then, migrations happen in two places:
- `Player.__setstate__` for Player attrs (see §6).
- Lazy `getattr(game, 'xxx', default)` in `main.Game._load_run` for
  Game attrs.

If you ADD a new Game-level attribute, use the getattr-with-default
pattern on load so old saves survive.

---

## 4. `highscore_system.py`

### 4.1 File location

```python
def _score_file_path() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.join(save_dir(), 'highscores.json')
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'highscores.json'
    )
```

- **Dev:** `<project_root>/highscores.json`.
- **Frozen:** `<save_dir()>/highscores.json` — same folder as saves.

Computed once at module import; concurrent-instance writes race (no
file lock). Low risk in practice (one player per session), noted in
SYSTEMS_AUDIT §10 P4.

### 4.2 Schema

Each entry is a flat dict:

```json
{
  "name":    "Alice",
  "score":   123456,
  "grade":   "A",
  "level":   87,
  "kills":   412,
  "turns":   28391,
  "victory": true,
  "date":    "2026-10-02"
}
```

File is a JSON array sorted descending by `score`, truncated to
`MAX_ENTRIES = 100`.

### 4.3 `_load` / `_save`

- `_load` tolerates missing file, invalid JSON, OS errors — returns
  `[]`.
- `_save` writes with `indent=2`, swallows `OSError`.

Both silent on failure (SYSTEMS_AUDIT §10 P5 — a logging hook here
would catch corruption).

### 4.4 `add_score(name, score, grade, level, kills, turns, victory)`

Appends, sorts, truncates, saves. Returns 1-based rank of the new
entry (0 if it didn't make the table).

**Rank-recovery edge:** `(score, name, date)` can collide for two
same-day runs under the same name — first hit wins the rank. Minor
cosmetic issue; the entry is still saved.

### 4.5 `get_scores()` / `get_top(n=5)`

- `get_scores()` returns the full sorted list.
- `get_top(n)` returns the first `n`. Used by the welcome screen
  leaderboard panel and the death screen summary.

### 4.6 Score formula

`main._calc_score` reads only `turn_count`, `max_level_reached`,
`monsters_killed`, and the Philosopher's Stone check. **Zero**
dead mastery-XP references (SYSTEMS_AUDIT §10 VERIFIED). Grade is
computed from the score band (A/B/C/D/F).

---

## 5. `crash_handler.py`

### 5.1 Report location

```python
def _project_root() -> str:
    try:
        from game_log import log_dir
        return log_dir()        # <Documents>/PhilosophersQuest + fallbacks
    except Exception:
        pass
    if getattr(sys, 'frozen', False):
        from paths import save_dir
        return save_dir()
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
```

Priority: `game_log.log_dir()` → `save_dir()` (frozen) → project
root (dev). Playtesters find `crash_*.txt` and `ERROR_LOG.txt` in the
same folder.

### 5.2 `write_crash_report(exc_type, exc_value, exc_tb, game=None)`

Writes a plain-text file named `crash_YYYYMMDD_HHMMSS.txt`. Body:

```
======================================================================
  PHILOSOPHER'S QUEST -- CRASH REPORT
======================================================================
  Time    : 2026-10-02 15:34:11
  Platform: Windows-11-10.0.26200-SP0
  Python  : 3.14.0
  Pygame  : 2.5.2

----------------------------------------------------------------------
TRACEBACK
----------------------------------------------------------------------
Traceback (most recent call last):
  File "src/main.py", line 1234, in _advance_turn
    ...

----------------------------------------------------------------------
GAME STATE
----------------------------------------------------------------------
  Player name  : Alice
  Dungeon level: 42
  Game state   : player
  Turn         : 1337
  HP           : 78 / 120
  SP           : 55 / 100
  MP           : 20 / 50
  STR/CON/DEX  : 14 / 16 / 12
  INT/WIS/PER  : 10 / 14 / 10
  Status fx    : ['blessed', 'burning']
  Inventory    : ['scroll of healing', 'longsword', ...]
  Weapon       : longsword
  Known spells : ['fire_bolt_spell', ...]
  Quirks       : ['scheherazade', 'tesla', ...]

  Emergency save written -- your progress has been preserved.
======================================================================
  Please send this file (or ERROR_LOG.txt in the same folder)
  to the developer. Thank you!
======================================================================
```

**Emergency save order (critical):** the handler calls
`save_system.save_game(game)` **before** writing the crash file.
Reasoning: a Pickle error during the emergency save shouldn't lose
the traceback. The save's success/failure is appended to the report
("Emergency save written" or "EMERGENCY SAVE FAILED: {err}").

If the primary write fails, the handler falls back to writing in
`os.getcwd()` so the tester at least gets *something*.

**Minor hardening item (SYSTEMS_AUDIT §4 P3):** no guard if `player`
itself is `None`. Inner try/except around game-state read swallows
exceptions and logs `"(error while reading game state: <inner>)"` —
the traceback is still preserved, so the hazard is cosmetic.

### 5.3 Rolling log fold-in

The full crash report is also appended to `ERROR_LOG.txt` via
`game_log.log_crash_report`. One file is a complete record (recovered
errors AND fatal crashes), the `crash_*.txt` file is a one-shot
snapshot specifically for sharing. Both go in `log_dir()`.

---

## 6. `Player.__setstate__` — the save migration seam

Pickle's standard mechanism: `__setstate__` is called with the dict
pickled by `__getstate__` on load. This is where the Player object
accepts (or rejects) attributes from older pickles.

### 6.1 `__getstate__` — what's dropped on save

```python
def __getstate__(self):
    state = self.__dict__.copy()
    state.pop('_combat_game_ref', None)     # pygame refs
    state.pop('_appearance_stamp', None)    # bound method callback
    return state
```

Two transient attrs that cannot pickle (pygame Surface / bound
method). Re-set on next combat / on load. If you add a runtime
callback that caches `self.game`, add it here too — the save will
silently fail without this and `_find_unpicklable` will name the
field.

### 6.2 `__setstate__` — the migration list

```python
def __setstate__(self, state):
    # v2.15+ audit sync: strip retired mastery attrs BEFORE
    # __dict__.update so a stale attr can't reappear.
    for _dead in (
        'class_masteries', 'subject_mastery_xp',
        'stuffies_active', '_active_stuffies',
        'identify_masteries', 'family_mastery_blessings',
        'family_masteries', 'weapon_masteries', 'shield_masteries',
    ):
        state.pop(_dead, None)
    self.__dict__.update(state)
    if not hasattr(self, 'known_forms'):
        self.known_forms = set()
    if not hasattr(self, 'known_materials'):
        self.known_materials = set()
```

### 6.3 Why this exists

**Identify v3** (2026-08-06) removed:

- `identify_masteries` — the old per-class XP store that drove the
  3-chain identify quiz
- `class_masteries` — the per-weapon-class mastery store
- `family_mastery_blessings`, `family_masteries` — per-monster-family
  bonus pool
- `weapon_masteries`, `shield_masteries` — subclass-specific stores
- `stuffies_active`, `_active_stuffies` — Pokémon-plush buff tracker
  (collapsed into a plain `carry_bonus` field on the stuffie item)
- `subject_mastery_xp` — per-quiz-subject XP pool

Without the pop, an old pickle brings those attrs back into
`__dict__`, where they'd (a) take up memory, (b) show up in any code
that iterates attrs (sidebar passives, discoveries, debug overlay),
and (c) break the invariant "no mastery references anywhere".

**v2.6.3** also added the split-identity sets `known_forms` /
`known_materials` for the True-Name identify-v3 model. The two
`hasattr` guards fill them in as empty sets on load, so an older
save picks up True-Name discovery from the next identify.

### 6.4 Adding a new migration

If you remove or rename a Player attribute in a future version:

1. Add its name to the `_dead` tuple in `__setstate__`.
2. If the attr is renamed, set the new one from the old value **before**
   popping (do this inside `__setstate__` before `__dict__.update`).
3. If the attr is a type change (e.g. `set` → `dict`), handle the
   conversion inside `__setstate__` after `__dict__.update`.
4. **Do NOT** add a schema version here — that's the Game-level
   deferred item. `Player.__setstate__` migrates by attribute name /
   presence.

Rule of thumb: migrations are safe to accumulate. Removing an entry
from the `_dead` tuple takes an audit — if an old save still has that
attr, dropping the pop would resurrect it.

---

## 7. Game-level save migrations (via getattr default)

Not every migration is at the Player level. Game-level state uses the
`getattr(game, 'xxx', default)` idiom in `save_game` and the mirror
idiom in `_load_run` so new fields default-safe on old saves.

Examples from the state dict:

| Field | Default on load | Introduced |
|---|---|---|
| `karma` | 0 | karma system |
| `heavenly_host_active` | `False` | Michael's Scales |
| `abaddon_resist_removed_turns` | 0 | Abaddon ascent |
| `_l100_altars_used` | `set()` | L99 judgment |
| `_appearance_map` | `{}` | one-cosmetic-per-item |
| `quiz_stats` | `{}` | per-subject tracking |
| `_cow_return_level` | 0 | cow level reload fix |
| `_cow_level` | 35 | cow level random floor |
| `_magic_carrot_spawned` | `False` | unicorn quest |
| `_recalled_hints` | `[]` | Recall Lore history |
| `_cooked_recipes` | `[]` | encyclopedia recipes tab |

**Why defaults instead of `__setstate__`:** Game is composed of
seven mixins + lots of post-`__init__` setup. A proper `__setstate__`
would duplicate `__init__` logic. The flat state-dict + getattr
pattern keeps the save-roundtrip boring at the cost of a slightly
noisy save_game body.

---

## 8. `game_log.py` (brief)

Not covered in detail — small file with:

- `log_dir()` — `<Documents>/PhilosophersQuest/` with fallback chain
- `log_info(msg)`, `log_error(msg)`, `log_crash_report(text)` —
  append to `ERROR_LOG.txt`
- `log_dir()` is the single source of truth for crash/log output

Used by `save_system`, `crash_handler`, `game_input` (spurious QUIT
logging), `main` (startup banner), and any `log_error` call site.

---

## 9. End-to-end: what happens on save / load / crash

### 9.1 Save (manual or on floor change)

1. `main.Game.save_game()` → `save_system.save_game(self)`
2. State dict built from Game + Player (via `Player.__getstate__`)
3. Pickle to `<name>.pkl.tmp` with `HIGHEST_PROTOCOL`
4. `os.replace(tmp, final_path)` — atomic
5. On failure: `_find_unpicklable` walks the state tree, logs the
   culprit paths to `ERROR_LOG.txt`, keeps the old save

### 9.2 Load (welcome screen → name match)

1. `save_system.save_exists(name)` guards (0-byte files = no save)
2. `save_system.load_game(name)` returns state dict
3. `main.Game._load_run(state)` reads each key with getattr defaults
4. Each pickled Player object was already migrated via
   `Player.__setstate__` during Pickle's load phase

### 9.3 Permadeath

1. HP ≤ 0 → `_on_game_over(reason='died')`
2. Bones file written (`bones.py::save_bones`)
3. `delete_save(name)` wipes `save_<name>.pkl`
4. Highscore added via `add_score(..., victory=False)`
5. Welcome screen shows the save as gone

### 9.4 Crash

1. Unhandled exception → top-level `except Exception` in `main()`
2. `crash_handler.write_crash_report(exc_type, exc_value, exc_tb,
   game)` fires
3. **First:** `save_system.save_game(game)` — emergency save (atomic)
4. **Second:** write `crash_*.txt` with traceback + game state
5. **Third:** `log_crash_report` folds the same text into
   `ERROR_LOG.txt`
6. Process exits non-zero

Order matters: save first (preserves progress), then write the
crash file (tester-shareable), then log (archival).

---

## 10. Invariants (what not to break)

1. **Atomic save.** `tmp + os.replace` only. Never write directly to
   the save path; a mid-dump failure must not corrupt the previous
   good save.
2. **No save-on-victory bones.** (In-progress fix per
   SYSTEMS_AUDIT §4.) Bones are a death artifact; victory saves a
   file for review but should NOT drop a ghost.
3. **No `_combat_game_ref` in pickle.** Enforced in
   `Player.__getstate__`. Pygame Surfaces are not picklable; this
   was the "cannot pickle Surface" save-loss bug of record.
4. **No raw `self.karma += n`.** Use the clamp helper
   (`_award_encounter_outcome`); the Penitent weapon's bypass is the
   one documented exception and is safe only because of its triggering
   condition.
5. **Delete only on death.** `delete_save` is not called from
   victory, exit-quest, or quit-to-menu paths.
6. **Load defaults all new fields.** `getattr(game, 'xxx', default)`
   in `_load_run`; `hasattr`-guards in `Player.__setstate__`.
7. **Highscores are append-sort-truncate.** No mutation of existing
   entries; MAX_ENTRIES = 100 is the hard cap.
8. **Crash writes save first.** Order in `write_crash_report`.
9. **Frozen writes go to `save_dir()`.** Never under `sys._MEIPASS`.

---

## 11. Open items

Documented so future work has one place to find them.

- **Schema version + migration hook** in save state (deferred #5).
- **Dedupe `_save_path` collisions** — add counter suffix for
  reduced names.
- **`_on_game_over` refactor** — explicit `reason` + `is_victory`,
  skip bones on victory, played-sound honest about the outcome.
- **Bones schema stability test** — round-trip assertion so field
  renames in `save_bones` don't silently break old bones files.
- **Highscore file lock** — hold a `.lock` sentinel for the window of
  `_load`/`_save` so a second instance (e.g. two installer windows)
  can't race.
- **`_find_unpicklable` cap** — currently 8 culprits; raise if
  needed. Trade-off is log noise on genuinely broken saves.
