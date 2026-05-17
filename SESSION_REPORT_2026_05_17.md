# Session Report — 2026-05-17

## What I shipped while you were away

Four commits on `main`, pushed to origin:

| Commit | Phase | Summary |
|---|---|---|
| `109bb2a` | 3A | Item rebalance + Titivillus debug tools |
| `e9b4bd7` | 3B/3C/3D | Hero specials infrastructure + 8 new heroes + journal entries |
| `8632fdb` | 3E | Wired remaining unimplemented mastery effects |
| `f895bf8` | 3F | Cross-system balance check (tests) |

Test count: **204 → 232** (+28 across two new test files).

---

## What's in place now

### 1) Hero special system (new module: `src/hero_specials.py`)

A single data file owns every hero's flavor + mechanics:

- `HERO_SPECIALS` — active abilities (chain-escalator AI quiz, tier-graded effects)
- `HERO_PASSIVES` — always-on flags checked at code hook sites
- `HERO_JOURNAL` — opening chronicle entry per build
- `_DISPATCH` — effect resolver table (19 distinct effect kinds)

The V power menu shows hero actives as always-unlocked entries alongside quirk powers. Activating a hero special opens an AI escalator_chain quiz (max=5); chain depth feeds the resolver. Cooldowns tick down each turn.

**Boss immunity**: CC effects (charm, fear, confuse, paralyze) skip bosses (`is_boss=True OR max_hp > 500`). Damage specials hit bosses at 0.5x. Verified by `test_cc_specials_are_boss_immune`.

### 2) Builds wired (22 existing + 8 new = 30 total)

**Existing — with active special**: Aristotle, Socrates, Pythagoras, Prometheus, Leonidas, Alexander, Theseus, Hermes, Odysseus, Merlin, Ash Williams (×3 — Give Me Some Sugar / Yo She-Bitch Let's Go / This Is My BOOMSTICK), Ash Ketchum.

**Existing — passive**: Plato (no-shard identify), Nietzsche (Will to Power at <30% HP), Diogenes (Cynic's Detachment), Achilles (Demigod Hide -25% physical), Geralt (Witcher Mutations + Resists), Ciri (Elder Blood escape teleport).

**Family kids** — already use chain-escalator AI through Stuffie / Sketchbook / Rand's Heart; no changes to their abilities, just rebalanced their items.

**Dad** — `_immortal` flag preserved as designed.

**New builds** (multi-word names so they can't be spam-typed):
- `ada augusta byron lovelace` — Difference Engine (paralyze + slow)
- `leonardo di ser piero da vinci` — Codex Sketch (summon mechanical helper)
- `boudicca queen of the iceni` — Vengeance Wakes (passive berserk at <50% HP)
- `saint joan of arc maid of orleans` — Standard of the Maid (heal + crit-buff)
- `sir arthur conan doyle's sherlock holmes` — Deduction (reveal radius)
- `miyamoto musashi the sword saint` — Niten Ichi-Ryū (passive dual-wield +15%)
- `saint hildegard von bingen` — Viriditas (self-heal + cleanse)
- `nikola tesla the wizard of menlo park` — Resonant Frequency (passive shock counter on melee hits)

### 3) Titivillus QA tools

- `Shift+I` → toggle player immortality (no quiz, no chronicle)
- `Shift+W` → open floor-number prompt; ENTER warps via `_change_level`
- Gated by `_qa_tools` flag in the build definition; works only for Titivillus.

### 4) Item rebalance (Phase 3A)

Off-curve starter items downgraded to tier-1 stats:
- `achilles_spear`: tier 2 → 1, peak 30 → 8, damage 10 → 6
- `tablet_of_hammurabi`: peak 20 → 10, +2 INT → +1 INT
- New `ring_protection_iron` (tier 1, peak 6, +1 AC) — replaces `ring_protection_silver` on Cain & Titivillus
- `wand_of_fire` (tier 2 peak 28) on Titivillus → swapped to `wand_of_light`

Iconic items intentionally exempt (hand-tuned, build-defining): Necronomicon (Ash Williams), Lantern of Diogenes (Aristotle/Diogenes), Prometheus Torch, Shield of the Spartans. These have peak_floor > 14 but are essential to their build's identity.

### 5) Per-build journal entries

Every hero (existing + new) plus every family kid logs a themed opening chronicle line on game start. The line describes who they are and what they bring to the run. Stored in `HERO_JOURNAL`; `_give_starting_kit` calls `_log_chronicle` with the entry.

### 6) Unimplemented mastery effects wired (Phase 3E)

- **Andvaranaut** `gold_finds_pct` — at gold pickup, additive % bonus to amount (stacks alongside Draupnir's `gold_multiplier`).
- **Ankh of Isis** `resurrect_to_full` — chain-5 mastery causes the resurrection to restore FULL HP instead of half.
- **Talisman of Troy** `buff_duration_bonus` — noted as no-op (Palladium's effect is permanent while worn). Left as flavor; could be reworked if the item becomes timed-buff later.

### 7) New monster tag

`female_attractive` added to: lamia, succubus_shade, dryad_guardian, harpy, banshee, medusa, medusa_gorgon. Used by Ash Williams' *Give Me Some Sugar* — drains HP only from monsters with this tag.

### 8) New status effects registered

`stand_ac`, `crit_buff`, `fear_immune`, `boomstick_aoe_next` registered in `EFFECT_INFO` so they tick down and display in the player UI.

---

## What might need a design decision when you're back

### 1) Ash Williams' Necronomicon as starter

Ash starts with the Necronomicon, which teaches *Army of Darkness* (summons a permanent zombie horde). This is mechanically very strong at F1. Two options:
- Leave it (matches his Evil Dead identity; high-power-but-rare niche build is okay)
- Lock the Necronomicon to require a successful grammar quiz to read (already the case) and accept that he may dominate early floors if he learns it

I left it as-is. Flag if you want it scaled down.

### 2) Ciri's Elder Blood escape

I implemented as auto-teleport when HP drops below 25%, once per floor. The current `_elder_blood` build flag also grants three V-menu powers (Blink, Charge, Scream). These overlap thematically. The passive runs IN ADDITION to the existing powers. Consider: is this too much survivability? The passive is once-per-floor, so probably fine, but worth a play-test.

### 3) Sherlock's Deduction radius gets very large

At chain 5, *Deduction* reveals everything within a radius of 99 (effectively the whole floor). This is similar to Theseus' *Labyrinth Sense* at chain 5. The two builds have similar floor-reveal effects. I kept Sherlock's narrower at lower chain (3/5/7/10 vs. 99 only at max). Reconsider differentiation if it feels redundant during play.

### 4) Buff_duration_bonus mastery (Talisman of Troy)

Currently a no-op since the Palladium's `reflecting` status is permanent. Two paths:
- (a) Switch the Palladium to a timed buff and have the mastery extend it
- (b) Swap the mastery to a different `accessory_passive_strength` sub-kind that's mechanically active (e.g., `passive_regen_bonus`)

I left it alone. The Palladium is rare enough that the mastery being flavor-only isn't a big issue, but it's an outlier.

### 5) Tittivillus warp during quizzes

`Shift+W` is gated to the player turn state — pressing it during a quiz or menu does nothing. Want it to also work mid-quiz / mid-menu as a hard-debug bail-out? I'd add it if asked, but right now you can only warp from the open dungeon view.

### 6) Hero-special XP / progression

Hero specials use AI quiz, which means:
- Player performance during the quiz affects chain depth
- More AI knowledge = stronger special
- But the special itself doesn't level up or improve with floor depth

This is intentional per your design but means deep-floor heroes get the same special as F1 heroes. If you want late-game scaling, we could add a `scale_with_floor` flag to specials in a follow-up.

### 7) Family-kid journal entries

I wrote first-person entries for Corwin, Cain, Fianna, Fluffs, Robyn, Dad. They're light and kid-friendly — assume the children's voice. You may want to rewrite them in tone or content; very easy edit in `src/hero_specials.py::HERO_JOURNAL`.

### 8) No sprite for new heroes

The 8 new builds reference sprite IDs like `player_warrior_f`, `player_wizard_f`, `player_diogenes` — most of which don't have actual PNG files in `assets/tiles/`. The renderer falls back to a default. If you want each new hero to have a unique sprite, that's an art ask.

---

## What I considered but didn't change

- **Lantern of Diogenes peak_floor**: kept at 16 (in the iconic-exemption list)
- **shield_of_the_spartans peak_floor**: kept at 18 (iconic-exemption)
- **Geralt's `_start_potions`** (potion_of_healing, potion_of_haste, potion_of_fire_resistance): all auto-identified at start, all reasonable for F1, left alone
- **Existing quirk system**: untouched; hero passives live in a separate `hero_passives` set on the player
- **Pet system**: untouched (Phase 1+2 from earlier still stands)
- **Identify system**: untouched (Phase 3a/b from earlier still stands)
- **Prayer / trap / shop systems**: untouched

---

## Test coverage added

- `tests/test_hero_specials.py` (+19) — data shape, effect-resolver coverage, boss-immunity helper, item rebalance smoke, monster-tag presence
- `tests/test_builds_cross_system.py` (+9) — cross-system invariants (every linked item exists, starter curve compliance with exemption list, CC boss-immune, chain-5 ≥ chain-3, family kids have gear, Titivillus QA flag, cooldown range, player defaults)

Total: **232 tests passing, ruff clean** on all changed files (pre-existing E701/F401 issues in unrelated code untouched).

---

## Open lanes for next session (your choice)

Per the older pending-audits memory, still untouched:
- **NPC encounter expansion** — add 15-20 devil-temptation encounters in deep blocks; wire merchant attack/theft to karma penalties
- **Hint bank rewrite** — flagged in earlier sessions
- **Wielder-vulnerability mechanic** — old carry-forward, detail unclear
- **Quirks / mystery system breadth** — flavor systems for run variety

Plus newly-discovered:
- **Phase 2 mastery hooks left as "noted no-op"**: Talisman of Troy buff_duration_bonus
- **No "rename pet" action** in the pet menu (Phase 2 punted on it)
- **No sprite art for the 8 new heroes**

---

That's everything. Run a few of the new builds when you get a chance — Sherlock and Joan in particular feel like fun new variety, and Ash Williams with three signature lines should be a riot.
