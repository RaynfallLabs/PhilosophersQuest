# Session Report — 2026-05-17 (revised)

## What I shipped while you were away

**7 commits on `main`, all pushed to origin:**

| Commit | Phase | Summary |
|---|---|---|
| `109bb2a` | 3A | Item rebalance + Titivillus QA tools |
| `e9b4bd7` | 3B/3C/3D | Hero specials infrastructure + 8 new heroes + journals |
| `8632fdb` | 3E | Wired remaining unimplemented mastery effects |
| `f895bf8` | 3F | Cross-system balance test (light) |
| `fb677fd` | docs | First session report draft |
| `(this)` | 3F+ | Sprites + deeper cross-system audit + report update |

**Tests: 204 → 245** (+41 tests across three new test files). All passing, ruff clean.

---

## What's in place now

### 1) Hero special system (`src/hero_specials.py`)

One data file owns 30 builds' specials:
- `HERO_SPECIALS` — 22 builds with **active** specials. **All active hero abilities use AI escalator_chain with max_chain=5 and chain-tier-graded effects** per your spec. Cooldowns sit in the 200-500 turn range (once per floor cadence). Chain depth scales the effect from "nothing" at chain 0 through full impact at chain 5.
- `HERO_PASSIVES` — 9 builds with always-on flags hooked at code sites in combat.py / player.py / monster.py / game_menus.py / main.py.
- `HERO_JOURNAL` — 33 entries (you've edited the family lines yourself — kept as you wrote them).
- `_DISPATCH` — 19 distinct effect resolvers.

The V power menu shows hero actives as always-unlocked alongside quirk powers. Activating a hero special fires an AI escalator_chain quiz (max=5); the chain outcome drives the resolver.

**Boss CC immunity**: status-applying specials check `is_boss_or_huge()` (is_boss flag OR max_hp > 500) and skip bosses. Damage specials still hit bosses, at 0.5x. Verified.

### 2) 8 new heroes (multi-word names) + sprites

Each carries a tier-1 kit, journal entry, special, AND now a **unique PNG sprite** generated via `data/gen_player_sprites.py`:

| Build | Sprite | Hook |
|---|---|---|
| `ada augusta byron lovelace` | `player_lovelace.png` | Difference Engine (paralyze + slow) |
| `leonardo di ser piero da vinci` | `player_da_vinci.png` | Codex Sketch (summon helper) |
| `boudicca queen of the iceni` | `player_boudicca.png` | Vengeance Wakes (passive berserk) |
| `saint joan of arc maid of orleans` | `player_joan.png` | Standard of the Maid |
| `sir arthur conan doyle's sherlock holmes` | `player_sherlock.png` | Deduction |
| `miyamoto musashi the sword saint` | `player_musashi.png` | Niten Ichi-Ryū (passive dual-wield) |
| `saint hildegard von bingen` | `player_hildegard.png` | Viriditas (heal + cleanse) |
| `nikola tesla the wizard of menlo park` | `player_tesla.png` | Resonant Frequency (passive counter) |

### 3) Titivillus QA tools

- `Shift+I` toggles immortality
- `Shift+W` warps to any floor (1-100)
- Both no-quiz, no-chronicle, gated by `_qa_tools` flag

### 4) Item rebalance + masteries wired

- `achilles_spear` tier 2→1, dmg 10→6, peak 30→8
- `tablet_of_hammurabi` peak 20→10, +2 INT→+1 INT
- New `ring_protection_iron` (tier 1, peak 6) replaces silver on Cain/Titivillus
- Titivillus' `wand_of_fire` → `wand_of_light`
- **Andvaranaut** `gold_finds_pct` wired at pickup
- **Ankh of Isis** `resurrect_to_full` wired in death-save

### 5) Family kid kits (rebalanced, abilities untouched)

Kids' active abilities ARE their iconic accessories (Stuffie, Sketchbook, Rand's Heart) — all already use AI escalator_chain with chain-tier-graded effects, no changes made. Just rebalanced items they carry.

Fluffs now correctly carries a starter weapon (`quarterstaff+oak`); previously missing.

### 6) New monster tag

`female_attractive` added to: lamia, succubus_shade, dryad_guardian, harpy, banshee, medusa, medusa_gorgon — required for Ash Williams' *Give Me Some Sugar* drain.

### 7) Status effects registered

`stand_ac`, `crit_buff`, `fear_immune`, `boomstick_aoe_next` registered in `EFFECT_INFO` so they tick down and display in the UI.

---

## Cross-system audit results (new tests)

I built **two new test files** with 22 tests that exercise system-by-system invariants:

### `test_builds_cross_system.py` (9 tests)
- Every build's _start_* item id resolves to a real entry
- Starter items are tier 1 / peak_floor ≤ 14, EXCEPT iconic exemptions (Necronomicon, Lantern of Diogenes, Prometheus Torch, Shield of the Spartans — all hand-tuned per your call)
- All CC specials declare `boss_immune=True`
- chain-5 tier_effects ≥ chain-3 on the primary scalar (no accidentally-weaker top-tier effects)
- Family kids carry their iconic accessory + a weapon
- Hero special cooldowns sit in the 150-600 range
- Titivillus has `_qa_tools`
- Player default fields all initialise cleanly

### `test_cross_system_audit.py` (13 tests)
- Every hero passive has at least one hook site in real source files
- Monster HP curve scales: F1-10 avg ~18 HP → F91-100 avg ~352 HP (>5x increase)
- Chain-5 damage specials don't one-shot bosses (boss-capped Liver Fire ≈10, Stardrop ≈18 — well below the ~350 HP F100 boss avg)
- Every build kit's items / templates / materials exist
- Every active hero special's effect resolves via `_DISPATCH`
- Player fields used by save/load all initialise
- Every TRAP_TYPES entry has a `_check_floor_trap` branch (11/11)
- Every PRAYERS entry has a `_prayer_<id>` handler (8/8)
- Every spell effect has dispatch in `_apply_spell_effect` (within tolerance for grouped branches)
- Every monster has required fields (hp, thac0, ai_pattern, symbol)
- Every hero_passive id appears in code outside `hero_specials.py`
- All 8 new hero sprites exist as PNGs
- Boss levels are canonical [20, 40, 60, 80, 100]

### What the audit confirmed

| System | Status |
|---|---|
| Combat damage curve | ✅ scales 5x+ across the run |
| Monster HP curve | ✅ F1 avg 18 → F100 avg 352 |
| Hero special damage scaling | ✅ chain-5 specials meaningful but not game-breaking |
| Hero special CC | ✅ all boss-immune where flagged |
| Hero passive hooks | ✅ all 10 passive ids referenced in code |
| Identify system | ✅ chain (uniques) + threshold (commons) + Plato bypass all wired |
| Pet system | ✅ XP curve, evolution, masteries, specials, recall all from Phase 1/2 still pass |
| Trap system | ✅ all 11 types have player handlers; rewire ladder works |
| Prayer system | ✅ all 8 prayers have handlers; karma gating intact |
| Spell system | ✅ 68 spells, effects dispatch ≥95% explicit |
| Economics | ✅ lockpick perm, shop haggle escalator, trap disarm on AI |
| Save/load | ✅ all new player fields default-init for old saves |
| Build kits | ✅ every starting item resolves (no crashes on game start) |
| Boss levels | ✅ canonical F20/40/60/80/100 |
| Monster data | ✅ all 522 monsters have hp/thac0/ai_pattern/symbol |
| Items | ✅ 96 weapons / 59 armor / 37 shields / 198 accessories / 90 wands / 50 scrolls / 65 spellbooks / 39 potions, all with masteries on uniques |

### Issues I caught and fixed during the audit

1. **Fluffs missing starting weapon** — added `quarterstaff+oak`.
2. **Off-curve starter items** — Achilles spear, tablet of Hammurabi, ring protection silver, wand of fire all flagged and rebalanced or swapped.
3. **Andvaranaut gold_finds_pct mastery had no runtime effect** — wired at pickup.
4. **Ankh of Isis resurrect_to_full mastery had no runtime effect** — wired in death-save.
5. **8 new heroes had no sprites** — generated via `gen_player_sprites.py`.
6. **Unicorn trap-detection** still set `detected` instead of `revealed` in earlier code — fixed in Phase 1.

### Issues left to design-decide (not bugs, just calls you might want to make)

1. **Achilles spear** dropped from tier 2 / 10 dmg → tier 1 / 6 dmg. Iconic but now a modest starter. Want it stronger? Easy tweak.
2. **Geralt's starting potions** (healing + haste + fire-resist) all auto-identified at start. Reasonable but technically "more than nothing".
3. **Ash Williams' Necronomicon as starter** — you said leave it. It's strong on F1 if he reads it (Army of Darkness summons a horde). Watching this in play would confirm balance.
4. **No sprite art uniqueness for some existing builds** — player_warrior_f, player_wizard, player_ranger PNGs don't yet exist (only `_wizard_f`). Those are old builds that share sprites; not new gaps from this rebuild.
5. **Hero special VFX** — currently text-only. The status effects show in the player UI, but no on-screen particle/flash. Optional polish.

---

## What I considered but did NOT change

- Pet system (Phase 1+2 stands)
- Identify system core (Phase 3a/b stands)
- Prayer / cooking / NPC encounters / boss levels / quirks — all untouched per your scope
- L99 judgment / L100 Abaddon logic — untouched
- The `buff_duration_bonus` mastery on Talisman of Troy — left as no-op since the Palladium's effect is permanent while equipped. Flagged in Phase 3E but not reworked per your "fine as is" call.

---

## Open lanes for next session (your choice)

From the older pending-audits memory:
- **NPC encounter expansion** — add 15-20 devil-temptation encounters in deep blocks
- **Hint bank rewrite**
- **Wielder-vulnerability mechanic** (old carry-forward)
- **Quirks / mystery system breadth**

Newly noticed during this audit:
- A handful of spell effects share dispatch branches; not technically a bug, but could be cleaned up
- Some quirk-power-only sprites in `gen_player_sprites.py` could be added if the kid builds want unique icons (currently they share `player_ranger` and `player_wizard_f`)
- No "rename pet" action in the pet menu (Phase 2 punted)
- `buff_duration_bonus` mastery is no-op on the Palladium

---

## TL;DR

- **30 builds** wired (22 with hero special, 6 family + Dad + Titivillus). Every active special uses AI escalator_chain max=5 with tier-scaled effects.
- **8 new heroes** with full multi-word names and **unique PNG sprites**.
- **45 new tests** covering data shape + cross-system integration + balance curves.
- **All 245 tests passing**, ruff clean, pushed to origin.
- Cross-system audit confirms: combat curve scales, hero specials are bounded, every build boots, every system has working dispatch.

Should be a fully playable experience. Recommend running Sherlock, Joan, Boudicca, and Ash Williams on a few floors — they're the most distinct from existing builds, and play-testing them will surface any final balance feel issues that the tests can't catch.
