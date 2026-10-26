# The Seeker Profile and Achievements

**Built 2026-10-25.** The plan, Brandon's rulings (D1 to D11) and the full catalogue with how every secret is found are in `PLAN_SEEKER_PROFILE_ACHIEVEMENTS_2026_10_25.md` in the project root. That file is deliberately untracked, because the repo is public.

A **Seeker** is the real child playing. A **hero** is who he or she plays in one run. The Seeker's profile outlives every run, death and new version. It holds achievements with their badge art, the lifetime counters behind the ladders, and a **reward code** per achievement to show Dad.

## Modules

| Module | Role |
|---|---|
| `seeker_codes.py` | Codes and the profile seal (pure). |
| `seeker_profile.py` | The profile file (pure): read, write, backup, merge, set aside, the index of Seekers. |
| `achievements.py` | The rules from `data/achievements.json` (pure): counters, triggers, ladders, the validator, `KNOWN_EVENTS`. |
| `seeker_session.py` | A profile + the rules + this run's counters behind one call, `emit(event, **fields)`. Used by the title screen, Study Mode and the Game. |
| `game_seeker.py` | `SeekerMixin`: the Game's side. Opens the active Seeker per run, `_seeker_event`, the unlock popup queue, flushes, run end. |
| `seeker_screen.py` | The Seeker Profile screen (title screen, F4), the badge cache (greyscale until earned), the gallery and the unlock card. |
| `tools/dad/` | Dad's tools: `make_key.py`, `check_code.py` (with a redeemed ledger), `codebook.py` (a printable page per Seeker). They write to `Documents\PQ_Dad\`, outside the repo. |

## Where the profile lives

`save_dir()/seekers/`:
- Installed on Windows: `%APPDATA%\PhilosophersQuest\seekers\`. The installer's upgrade wipes only `{app}\_internal`, and uninstall removes only `{app}`, so the profile survives upgrades, reinstalls and uninstalls.
- AppImage: the XDG data dir.
- From source: the project root (gitignored).
- Tests: the conftest temp dir, or `seeker_profile._DIR_OVERRIDE`.

Files:
- `index.json`: the active Seeker, who stays active until changed on purpose (D1), and the list of Seekers.
- `seeker_<encoded normalised name>.json`: one profile per Seeker. "Robyn" and "robyn" are one Seeker.
- `.bak`: the last good copy, kept on every write.
- `.unreadable-<stamp>`, `.edited-<stamp>`: files set aside. Nothing is ever deleted.

## The profile file

JSON with schema 1: `stats` (sums), `best` (maxima), `sets` (distinct values), `live` (a running streak), `unlocked` (id → at, version, hero), `seen`, plus `seal_key` and `seal`.

- Unknown keys are kept.
- A newer schema is read-only.
- Counters only go up.
- Two copies of the game merge: each keeps only what changed since it last read the file, and a write re-reads the file and adds to it.
- Writes are atomic (temp file, fsync, `os.replace`), with the old file copied to `.bak` first.
- **When it is written:** at once on every unlock; on every autosave (every 50 turns and floor changes); at run end; on quit; from the crash handler; when Study Mode closes.

**The seal** is an HMAC of the canonical JSON.
- An edited file is set aside silently and the backup restored. That unlocks the hidden *Behind the Curtain* (D2) and says nothing.
- A file that will not parse is "corrupt": restored from `.bak`, with a notice.
- Copying **saves** stays free (the metahack ruling); only the profile is sealed, because it holds the codes.

## Codes

- A code reads `WORD-XXXX-XXXX`: the achievement's `code_word`, then 40 bits of HMAC-SHA256(code key, `"<label>|<id>|<normalised Seeker name>"`) in Crockford base32 (no I, L, O or U).
- `check_code` forgives case, spaces, dashes and O/I/L typed in the code part.
- The game has no code-entry box, so there is nothing to test guesses against.
- **The key is never in the repo.**
  - Locally it is `src/_dad_key.py` (gitignored, made by `tools/dad/make_key.py`).
  - The release build writes it from the `PQ_DAD_KEY` Actions secret (`tools/release/write_dad_key.py`) and fails without it.
  - With no key, the game uses a public dev key and every code starts `DEV-`; no checker accepts those.
  - Rotating adds a key (`--rotate`). Old keys must be kept: they still check old codes and verify old seals.
- **One system for every code (D3).** The 26 reward scrolls carry `"achievement"` in `data/items/scroll.json`, the Scroll of Death's Bane names `lake_of_fire`, and the victory popup's story entry names `stone_home`. Each shows the Seeker's own code, or a line saying to choose a Seeker.

## Achievements data

`data/achievements.json` holds `categories`, `counters` and `achievements`. The validator (`achievements.validate`) refuses any unknown event, field, counter, key or category, duplicate ids, names or code words, a code word starting `DEV`, a ladder whose thresholds do not rise, and a hint containing its own `spoiler_words`.

**Counters**, defined by an `on` event plus an optional `where`:

| Kind | Meaning |
|---|---|
| (none) | +1 per event |
| `add: field` | sum of a field |
| `best: field` | maximum of a field |
| `streak: {...}` | longest run of matching events |
| `collect: field` | distinct values |

A counter's `scope` is `life` (the profile, the default) or `run` (`RunTally`, saved in the run's save as `_seeker_run`).

**Triggers:** `{"stat"|"run": counter, "at_least": n}`, `{"event": name, "where": {...}}`, `{"all"|"any": [...]}`. A `where` value is matched exactly, by list membership, or with `{"at_least": n}`, `{"not": v}` or `{"present": bool}`.

**Rules for the text (Brandon, 2026-10-25):**
- Names are always shown, so a name must never spoil.
- Hints are very light and point at the source material (the myth, the film, the game an egg comes from), never at the mechanic.
- The deepest fourth-wall ones show only `???`.
- No achievement for being a bad guy.
- `tests/test_achievements_data.py` enforces what it can. How each one really unlocks is Dad's: `tools/dad/achievement_notes.json`, which is not shipped.

**Ids are forever.** Codes are made from them. `tests/data/achievement_ids_shipped.txt` fails if one disappears.

## The event spine

The game emits events with one line at the place each happens: `self._seeker_event('kill', monster=..., ...)`. Every name is in `achievements.KNOWN_EVENTS`, and `tests/test_seeker_wiring.py` checks that each is emitted somewhere in `src/`.

Some engine modules have no game reference, so they tell a listener, and `SeekerMixin._seeker_init` binds each listener for the run:

| Listener | Feeds |
|---|---|
| `deeds.ON_RECORD` | every deed as `'deed'` (kind, id, late): oaths kept, people saved, the Black Knight's draw, Setne's senet, Death's chessboard |
| `monster.DAMAGE_OBSERVER` | `'damage'` (amount, dealt, by). `Game._damage_by` is `hero`, except in the monster, pet and escort passes of `_advance_turn` |
| `pet_system.ON_GROWTH` | `'pet_level'` and `'pet_evolved'` (the form counted from 1) |
| `topic_cards.ON_READ` | `'topic_read'` |
| `QuizEngine.on_card` | `'card_opened'` |

**What counts (D4):**
- Every run except the Dad/god build (`_joke`) and the QA build (`_qa_tools`).
- Nothing is recorded with no Seeker chosen.
- Study Mode emits only `'study_answer'`.

**Popups (D7):** an unlock is logged at once (with its code) and queued. `_seeker_tick` (top of `update`) shows up to three per popup when the state is plain play: never during a quiz, a menu or another popup.

## Badge art

`assets/achievements/<art>.png`, 128 x 128.
- Painted as small vignettes in the owner's style by the local pipeline (`tools/content/genart/`, "Badges").
- The game draws the rarity ring: bronze, silver, gold, violet (`FP.RARITY_*`).
- It also makes the greyscale "not yet earned" version.
- A missing PNG draws a plain medallion.
- Protected art (the duck line, Dad, the family cats, Shep, the Emberpup) is the game's own sprite set on a painted background, never redrawn.

## Tests

| File | Covers |
|---|---|
| `test_seeker_codes.py` | known-answer vector, normalising, typos, rotation, dev codes, seal |
| `test_seeker_profile.py` | round trip, merge, backup, damaged and edited files, newer schema, failed write, index |
| `test_achievements_engine.py` | every counter and trigger kind, ladders, validator |
| `test_achievements_data.py` | the catalogue: validity, shipped ids, Title Case, hint rules |
| `test_dad_tools.py` | checker, ledger, codebook, key file, release step |
| `test_seeker_wiring.py` | the spine, plus real game paths: kills, damage, quiz answers, deeds, pets, XYZZY, run end, a copied-back save, an edited profile, the save round trip, the reward scrolls |
| `test_seeker_ui.py` | the screens |
