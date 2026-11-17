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
| `tools/dad/` | Dad's tools: `make_key.py`, `check_code.py` (with a redeemed ledger; `--for <kid>` records under a kid), `codebook.py` (a printable page per Seeker) and the Code Validator (`code_validator.py`, rules in `validator_core.py`; see "Dad's Code Validator" below). They write to `Documents\PQ_Dad\`, outside the repo. |

## Where the profile lives

`save_dir()/seekers/`:
- Installed on Windows: `%APPDATA%\PhilosophersQuest\seekers\`. The installer's upgrade wipes only `{app}\_internal`, and uninstall removes only `{app}`, so the profile survives upgrades, reinstalls and uninstalls.
- AppImage: the XDG data dir.
- Mac app: `~/Library/Application Support/PhilosophersQuest/seekers/`.
- The release workflow proves each built Linux and Mac game writes, re-reads and seals a profile there before it ships (`src/selftest.py`, `--selftest-saves`).
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

### Dad's Code Validator

A code is made for the Seeker name the child plays under, and the kids play under names that need not be their own, on more than one computer (Brandon, 2026-11-17). So the validator never guesses a name:
- **Choose the kid profile** (Fianna, Corwin, any name added): the badge goes to that kid, recorded in the ledger under the kid's name.
- **The code screen asks for two things:** the Seeker name (the name on the kid's Seeker page) and the code. Up / Down or a click moves between them; Tab still switches the tabs. The name is filled in with the one last used for that kid, else the kid's own name, and stays editable.
- **Enter checks the code with that name only** (`seeker_codes.check_code`). Real: the badge is given and the name remembered for the kid, newest first, in `kids.json` under `seeker_names` (a file from before reads with none). The kid card shows "Plays as: ...". Not real: "That code isn't real for the Seeker name ... Check the letters and the name."
- **The same kid already holding that badge** gets the "Already Claimed" card. **This exact code already in the ledger for another kid** (compared after `seeker_codes.split_code`) lands amber with "Already Used": nothing is written unless Dad presses Enter to give it anyway; Esc goes back.
- The CLI does the same with `py tools/dad/check_code.py --for Corwin <Seeker name> <code>` (`--allow-duplicate` to record a code used before).

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

**The rare pets (2026-11-14, 6):** Dance Partner (the deed `saved.mooble`), Not a Step Missed (`dance_off`, won with no miss), First Past the Post (`race` won), Free of the Tether (the deed `saved.bococho`), Slow and Steady (`race` won with no sprint), Riding Into the Deep (`rode_down`). Their badges show the pets' own installed sprites on painted backgrounds (`badge_composite.py`), as the Emberpup's do.

**Added 2026-11-14 (23):** the lore ways (The First Labour, The Bronze Heel, In the Polished Shield, Deaf to Riddles), the named foes with no badge yet (the Bonnacon, the Calydonian Boar, the Undying Sisters, the Iron Patriarch, the Whispering Crone, the Blood Archon), the arsenal (A Silver Edge, Holy Water, Old Remedies), the kitchen and the smiths (the `feasts` ladder A Feast for Heroes and The Long Table, Five Courses, Stone Soup, Worth the Wait, Made to Order), Leaves Against the Rain (the Emberpup's cloak), the Stray Kids (Stage Fright, Encore!) and one more fourth-wall secret, Rip Van Winkle. A profile from before has none of them, and nothing in it changes: the new ladders read counters it never had, so `settle` gives nothing (`tests/test_achievements_quirks_2026_11.py`).

**The horn paths (2026-11-16, 3):** Neither Would Give Way (the deed `told.robin_in_the_stream`: Robin Hood knocked off his bridge), Not Yet the Hour (`told.arthur_woken`: the sleepers under the hill woken by the bugle) and One Who Listens (`told.heimdall_watch`: the watch kept with Heimdall), all `secrets`. Their hints point at the ballad, the Sewingshields legend and the Eddas; each lists its spoiler words. With them, Not by Strength (`told.merlin_staff`: Merlin's questions answered at his stone, the Staff of Emrys given), whose hint points at Malory.

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
| `counters.ON_COUNTER` | `'counter'` (technique, monster, family): a named counter at work. `counters.line` tells it, and so do the Aegis's and Perseus' Shield's own gaze branches in `monster.py` |

**Fields added 2026-11-14** (the winning build and the new kitchen):

| Event | Field | Set by |
|---|---|---|
| `kill` | `coat` | the coating's substance on the blow that killed (`coatings.after_blow` marks the creature `_killed_coated`) |
| `kill` | `flask` | the thrown flask's id (`game_arsenal._throw_flask` marks `_killed_by_flask`) |
| `cooked` | `tab`, `legendary`, `parts`, `carried` | `main._cook_facts`, read before the ingredients leave the pack. `carried` is the deepest floor reached now less the oldest `harvest_floor` among the dish's parts (`Game._harvest` stamps each part; a stack keeps the oldest) |
| `smith` | `service` | a smith's service done (`game_traders._trader_service_on`), or `order_collected` |
| `stray_kids` | `outcome` | `cleared` (the band's last falls) or `show` (the photo read) |
| `save_older` | `version` | a save written by an older version of the game is loaded (`game_seeker.older_version`; the save keeps `_game_version` from 3.5 on, and one with none is older) |
| `dance_off` | `won`, `misses`, `perfects`, `total`, `practised`, `dance` | a dance-off with the Mooble danced to its end (`mooble_encounter._mooble_dance_done`); `practised` is set by a practice round since the last dance-off (`game_mooble_dance._mooble_open_dance`) |
| `race` | `won`, `sprints`, `photo` | the Underway Run finished (`game_race._race_leg_done`) |
| `rode_down` | `floor` | down a staircase in the Bococho's saddle (`main._change_level`, before the rider is set down at the stair) |

**The Stray Kids (Stage Fright, Encore!)** fire on `stray_kids` with `outcome` `cleared` (`game_stray_kids._stray_kids_member_died`, when the last of the band falls and the photo drops) and `show` (`_stray_kids_summon`, the photo read). A rework of the band's fight must keep sending `cleared` at the moment the band is beaten.

A thrown weapon's kill and a thrown flask's kill are kills from afar (`ranged`). Before 2026-11-14 they counted as neither melee nor ranged.

**What counts (D4):**
- Every run except the Dad/god build (`_joke`) and the QA build (`_qa_tools`). On the QA build an
  achievement one event earns opens as a preview, once a run, with the code "QA PREVIEW" and
  nothing written (`game_seeker._qa_achievement_preview`, 3.5.2), so a test run can see it.
- Nothing is recorded with no Seeker chosen.
- Study Mode emits only `'study_answer'`.

**Popups (D7):** an unlock is logged at once (with its code) and queued. `_seeker_tick` (top of `update`) shows up to three per popup when the state is plain play: never during a quiz, a menu or another popup.

**Won as the run ended:** no popup opens over the death screen, so what a fall earns (The First Fall, Forgot to Eat...) waits in the queue. When the run is over, `main()` reads `_seeker_unshown()` (still pending, or queued and never opened) and the title screen shows their unlock cards. Leaving the Stone home opens the queue after the ending's own popup instead.

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
| `test_dad_tools.py` | checker (`--for`, duplicates), ledger, codebook, key file, release step |
| `test_dad_code_validator.py` | the validator: code entry, the Seeker name, assignment to the kid, remembered names, old `kids.json` files, duplicates, reels, library, every screen headless |
| `test_seeker_wiring.py` | the spine, plus real game paths: kills, damage, quiz answers, deeds, pets, XYZZY, run end, a copied-back save, an edited profile, the save round trip, the reward scrolls |
| `test_seeker_ui.py` | the screens |
| `test_achievements_quirks_2026_11.py` | the audit (every creature, deed, flask, technique, outcome and pet line a trigger names is real and sent), the 2026-11-14 achievements through real game paths, an old profile, and the new quirks |
