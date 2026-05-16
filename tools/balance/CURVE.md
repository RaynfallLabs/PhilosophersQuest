# The Unified Balance Curve — Design Document

**Built from:** `CROSS_SYSTEM_MAP.md` + the five systems-mapper docs + the user's stated design intent. **Not yet implemented.** This document is the design proposal. Once ratified, `curve.json` becomes the machine-readable yardstick and `validate.py` reports drift against it.

---

## 0. Mission

A graphical roguelike where knowledge is power. Every step has tension. Most runs die. A motivated kid plays for many sessions, the *good* runs feel exciting because skill + luck align. The game is hard *by design* and a quest-prepared player can win — but only just.

### Completion targets

| Player profile | Expected outcome |
|---|---|
| Below T1 math (can't sustain chains) | Dies in L1-10 |
| T1 master | Past Asterion (L20). Loses before Medusa. Median completion ≈ L25-35. |
| T2 competent | Beats Medusa with gear luck. Reaches L45-55. |
| T3 competent | Reaches Fafnir. Beats him with quest layer + good chain. |
| T4 competent | Reaches Fenrir. Wins occasionally. |
| T5 master + full quest prep | Wins the game. ~1 in 5-10 dedicated runs. |
| T5 master + secret-victory chain | Kills Death entirely. ~1 in 50+ runs. |

**Skill ≫ luck in the long run.** Math tier mastery is the primary progression axis. Gear and cooking adjust the variance corridor. Quest discovery determines whether you can fight the boss meaningfully or just survive him.

---

## 1. Design principles (the 10 commandments of the curve)

1. **Tension floor never drops to zero.** Every floor presents a credible kill threat to the *most prepared* player. If max-prep feels safe, the floor is failing.
2. **Variance corridor is the design.** At every floor, gap between unprepared and skilled+lucky ≈ ±25%. Wider = swingy. Narrower = deterministic.
3. **Monster threat is curve-locked. Player capability is gated.** Monsters scale smoothly. Players jump on gear RNG, quiz performance, identification, quest completion, quirk unlocks. The asymmetry creates surprise.
4. **Damage breakpoints define encounter feel.** Median monster = 2-4 player hits. Tough monster = 5-8 hits. Boss = 20-50 hits across phases. Player HP = ~5 average monster hits at most.
5. **AC and THAC0 scale together.** The data-only THAC0 floor at -16 extends past L80 for boss-tier monsters. Investment in armor stays meaningful all the way to L100.
6. **Quest layers are multipliers, not replacements.** Each boss has a base difficulty (no quest) and quest layers that EACH reduce difficulty by ~30-50%. Stacking layers compounds — but never to trivial. A 3-layer prepped Abaddon = ~25-30% of base difficulty, "challenging but achievable."
7. **Variety budget per band.** Each 10-floor band needs ≥8 distinct active monster species. Recognition replaces surprise.
8. **Loot pacing: meaningful upgrade every 2-3 floors** within each band. Not every floor (cheapens), not every 5+ (treadmill).
9. **Cooking is THE leveling track.** Math-tier mastery + cooking diligence + ingredient depth = HP and stat progression. Cooking HP softcap is floor-derived. Lazy cooks die early; diligent cooks reach Abaddon.
10. **Skilled completion rate ≈ 10-20%.** Most runs end. The ones that win feel earned.

---

## 2. The math tier ↔ boss correspondence (the spine)

| Floor band | Math tier dominant | Pre-boss boss | Naive completion expectation |
|---|---|---|---|
| L1–19 | T1 (5th grade) | — | learn the loop |
| L20 | T1 master | **Asterion** | T1 master = possible kill |
| L21–39 | T2 (middle school) | — | gear up, cook, discover quests |
| L40 | T2 competent | **Medusa** | T2 with quest = possible kill |
| L41–59 | T3 (8th grade) | — | mid-game progression |
| L60 | T3 competent | **Fafnir** | T3 with quest = possible kill |
| L61–79 | T4 (HS freshman) | — | endgame approach |
| L80 | T4 competent | **Fenrir** | T4 with Gleipnir/Sandal = possible kill |
| L81–99 | T5 (HS soph) | Seal demons | seal hunt + quest assembly |
| L100 | T5 master | **Abaddon** | T5 + seals + altar = possible kill |
| Death-chase | T5 + theology mastery | Death | T5 + Stone + prayer = escape |
| Abyss ritual | T5 + 4-item assembly | secret Death-kill | top 5% of T5 players |

**Critical principle:** the math tier required for a band determines BOTH the difficulty of quiz-gated actions (combat, identification, cooking) AND the gear that can be USED. A player whose math tier is below the floor band cannot effectively wield floor-appropriate gear. This is the natural gate.

---

## 3. The anchor floors

Eleven anchors at floors 1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, plus the Death-chase as a separate band. Between anchors, values interpolate linearly. Boss floors are *spikes* on the smooth curve.

### Player capability axes

At each anchor, define what a "prepared player" looks like. Three profiles per anchor:

- **Unprepared (UP):** below-tier math, basic gear, no cooking, no quests found
- **Prepared (P):** at-tier math, typical gear cluster, modest cooking, basic quest awareness
- **Skilled+Lucky (SL):** above-tier math at edges of chain, best gear cluster, diligent cooking, quest layers active

### Monster threat axes

At each anchor:
- **HP_med:** median normal monster HP at this band
- **HP_tough:** 75th-percentile (the "wall" monster)
- **DMG_med:** median damage per monster hit
- **THAC0_med:** median monster THAC0 (lower = more accurate)

### Loot, cooking, and variety axes

- **Loot tiers active:** which weapon/armor/accessory tiers are spawning
- **Cooking softcap:** the new floor-derived softcap value (replaces flat 1000)
- **Min species pool:** minimum unique monster species active on this floor band
- **Quest content:** named quest items, NPCs, mysteries, lore drops scheduled in this band

---

## 4. The 11 anchors (numerical proposals)

These are first-draft numbers. Each anchor is a hypothesis; the validator will tell us how far current data has drifted from them.

### Anchor L1 (start)

| Axis | UP | P | SL |
|---|---|---|---|
| Max HP base (no cooking) | 30 | 32 | 35 |
| Cooking softcap | 4 | 4 | 4 |
| Effective max HP | 30 | 34-36 | ~39 |
| Damage per hit (chain 3) | 4 | 6 | 9 |
| AC | 10 | 7 | 4 |

Monster band: HP 4-12, damage 1d2-1d4, THAC0 18-15. ~6-8 species. Math tier T1.

### Anchor L10 (early learning)

| Axis | UP | P | SL |
|---|---|---|---|
| Max HP base | 32 | 35 | 38 |
| Cooking softcap | 40 | 40 | 40 |
| Effective max HP | 35 | 50-65 | ~78 |
| Damage per hit (chain 5) | 8 | 14 | 22 |
| AC | 8 | 4 | -2 |

Monster band: HP 12-30, damage 1d4-2d4, THAC0 14-10. ~10 species. Math tier T1.

### Anchor L20 (Asterion gate)

| Axis | UP | P | SL |
|---|---|---|---|
| Max HP base | 34 | 38 | 42 |
| Cooking softcap | 80 | 80 | 80 |
| Effective max HP | 40 | 70-95 | ~120 |
| Damage per hit (chain 5) | 14 | 26 | 42 |
| AC | 6 | 0 | -8 |

**Asterion (boss):** HP 800 → **tune to 600** (reduce by 25%). 25-turn fight for prepared T1 player at common chain 5. Quest layer (Thread): defangs to ~12 turns. Naive (no Thread): 25-35 turns, very risky.

Monster band: HP 30-80, damage 1d6-2d6, THAC0 10-6. ~12 species. Math tier T1 master / T2 entering.

### Anchor L30 (mid-game entrance)

| Axis | UP | P | SL |
|---|---|---|---|
| Max HP base | 36 | 42 | 48 |
| Cooking softcap | 120 | 120 | 120 |
| Effective max HP | 50 | 90-130 | ~170 |
| Damage per hit (chain 5) | 22 | 40 | 65 |
| AC | 4 | -4 | -12 |

Monster band: HP 60-160, damage 2d4-3d4, THAC0 8-2. ~14 species. Math tier T2 dominant. Cow Level entry randomized here (L30-39).

### Anchor L40 (Medusa gate)

| Axis | UP | P | SL |
|---|---|---|---|
| Max HP base | 38 | 46 | 52 |
| Cooking softcap | 160 | 160 | 160 |
| Effective max HP | 70 | 130-180 | ~210 |
| Damage per hit (chain 5) | 32 | 56 | 90 |
| AC | 2 | -8 | -16 |

**Medusa (boss):** HP 1500 → **tune to 1100**. Quest Layer 1 (Aegis mirror): allows mid-range engagement (~15-turn fight). Quest Layer 2 (Blindfold): allows close combat. Naive: extremely risky — petrify-on-gaze is one-shot lethal without LOS pillars or counters.

Monster band: HP 120-300, damage 2d6-3d6, THAC0 2 to -4. ~14 species. Math tier T2 master / T3 entering.

### Anchor L50 (mid late-game)

| Axis | UP | P | SL |
|---|---|---|---|
| Max HP base | 40 | 50 | 56 |
| Cooking softcap | 200 | 200 | 200 |
| Effective max HP | 90 | 170-230 | ~256 |
| Damage per hit (chain 5) | 42 | 75 | 120 |
| AC | 0 | -12 | -20 |

Monster band: HP 200-450, damage 3d6-4d6, THAC0 -2 to -8. ~14 species. Math tier T3 dominant.

### Anchor L60 (Fafnir gate)

| Axis | UP | P | SL |
|---|---|---|---|
| Max HP base | 42 | 54 | 60 |
| Cooking softcap | 240 | 240 | 240 |
| Effective max HP | 110 | 220-290 | ~300 |
| Damage per hit (chain 5) | 55 | 100 | 160 |
| AC | -2 | -16 | -24 |

**Fafnir (boss):** HP 2500 → **tune to 2000**. Dragon scales 80% physical (existing). Fire/poison resist (existing). Quest Layer 1 (Sigurd pit): in-pit 4× damage bonus → ~15-turn fight. Quest Layer 2 (Reforged Gram, secret): ignore_resistances + lightning + 9× max chain → ~8-turn fight. Naive: dragon scales make physical attacks weak; player must bring elemental damage or quest the pit.

Monster band: HP 300-700, damage 3d8-4d8, THAC0 -6 to -12. ~14 species. Math tier T3 master / T4 entering.

### Anchor L70 (peak gear band)

| Axis | UP | P | SL |
|---|---|---|---|
| Max HP base | 44 | 58 | 64 |
| Cooking softcap | 280 | 280 | 280 |
| Effective max HP | 130 | 260-340 | ~344 |
| Damage per hit (chain 5) | 70 | 130 | 210 |
| AC | -4 | -20 | -28 |

Monster band: HP 500-1000, damage 4d8-5d8, THAC0 -10 to -14. ~14 species. Math tier T4 dominant.

### Anchor L75 (the L71-80 fill — quest-prep band)

This was the "dead band" in the audit. Now: introduce a mid-tier weapon/armor wave at L75 to bridge L70 uniques and L81 adamantine. Plus this is where Dwarven Forge (Gleipnir start), Vidar's altar, and the seal-hunt prep cluster live.

| Axis | UP | P | SL |
|---|---|---|---|
| Max HP base | 45 | 60 | 66 |
| Cooking softcap | 300 | 300 | 300 |
| Effective max HP | 145 | 290-360 | ~370 |
| Damage per hit (chain 5) | 80 | 150 | 235 |
| AC | -5 | -22 | -30 |

Monster band: HP 600-1200, damage 4d8-5d8+4, THAC0 -12 to -16. **Add 3-4 new species in this band** (audit-confirmed gap).

### Anchor L80 (Fenrir gate)

| Axis | UP | P | SL |
|---|---|---|---|
| Max HP base | 46 | 62 | 68 |
| Cooking softcap | 320 | 320 | 320 |
| Effective max HP | 160 | 310-385 | ~400 |
| Damage per hit (chain 5) | 90 | 165 | 270 |
| AC | -6 | -24 | -32 |

**Fenrir (boss):** HP 3000 → **tune to 2800** (small bump from current to fit the curve — fix the 1.2× L60→L80 anomaly). Speed 12 (existing). Quest Layer 1 (Gleipnir): power-bind cuts Fenrir's speed and damage in half → manageable 20-turn fight. Quest Layer 2 (Vidar's Sandal, secret): instant kill on chain ≥ 1. Naive: Fenrir's speed advantage + 1d10+5 damage = brutal. Without Gleipnir, expect 30+ turn slog with frequent player damage spikes.

Monster band: HP 700-1500, damage 5d8-6d8, THAC0 -14 to -18. ~10 species. Math tier T4 master / T5 entering.

### Anchor L90 (seal hunt midpoint)

| Axis | UP | P | SL |
|---|---|---|---|
| Max HP base | 48 | 66 | 72 |
| Cooking softcap | 360 | 360 | 360 |
| Effective max HP | 180 | 360-430 | ~440 |
| Damage per hit (chain 5) | 105 | 195 | 320 |
| AC | -7 | -26 | -34 |

Monster band: HP 1000-1800, damage 5d10-6d10, THAC0 -16 to -20. ~10 species (regular monsters + 3 seal demons in this band). Math tier T5 dominant. **Add 4-5 new "Abaddon elite guard" species in L91-99** to fill the L91-99 monster gap.

### Anchor L100 (Abaddon)

| Axis | UP | P | SL |
|---|---|---|---|
| Max HP base | 50 | 70 | 76 |
| Cooking softcap | 400 | 400 | 400 |
| Effective max HP | 200 | 400-475 | ~480 |
| Damage per hit (chain 5) | 120 | 220 | 360 |
| AC | -8 | -28 | -36 |

**Abaddon (boss):** HP 5000 → **tune to 6000**. Resistances unchanged (5 of 6 common). Quest layers:
- Layer 0 (seals): REQUIRED to access
- Layer 1 (altar resist-strip): 10-turn burst windows × up to 6 altars = ~60 turns of high-damage windows. **Functionally required for non-Sword players.**
- Layer 2 (Sword of Michael, max karma): with **crit reduced to 2.5×** and **abaddon_bonus_damage to 3d10**, the Sword max-chain crit deals ~2700 damage = 2-3 hits to kill, but requires landing 16× chain WITH crit. Realistic mid-fight chains do ~600-800 damage per hit. Sword + altar = comfortable fight.
- Layer 2.5 (Heavenly Host): angel-per-locust counter.
- Layer 3 (Death-kill, secret): post-Abaddon.

### Death-chase band (escape phase)

| Axis | UP | P | SL |
|---|---|---|---|
| Speed escalation | 50% → 75% → 100% → 125% (existing) | same | same |
| Death immunity to time_stop | TRUE (Phase 3 fix) | same | same |
| Prayer freeze | 3-8 turns per use, 100+ turn cooldown | same | with Fisher King stack: ~25% cooldown reduction |
| Death damage per hit | 4d10+8 vs player | same | same |
| Player HP entering chase | ≥ 350 P, ≥ 460 SL | (from L100) | (from L100) |

The chase IS Act III. Tension comes from the speed escalation + the secret-victory carrot. Death is unkillable by normal means; only the Abyss ritual works.

### Abyss ritual

Death must stand on the Shimmer + Complete Tablet on Shimmer + player reads Lake of Fire scroll. Requires assembling 4 items across 4 floor bands (which now randomize ±3 per the post-curve fix list). Plus the Stone (Abaddon drop). Plus the Wrench (L21-49 random spawn ±3 from somewhere TBD).

---

## 5. The new cooking softcap formula

**Replaces the current flat 1000:**

```python
COOKING_SOFTCAP_PER_FLOOR = 4
def cooking_softcap(dungeon_level_reached: int) -> int:
    """Max cooking HP at the deepest floor the player has reached."""
    return max(20, COOKING_SOFTCAP_PER_FLOOR * dungeon_level_reached)
```

Resulting curve (matches the anchors above):
- L1: 20
- L20: 80
- L50: 200
- L100: 400

The diminishing-returns cap_factor stays:
```python
cap_factor = max(0.20, 1 - cooking_hp_gained / cooking_softcap(deepest_floor))
effective_gain = base_gain * cap_factor
```

**Behavioral consequences:**
- Patient L30 cook can reach ~120 HP cap from cooking (vs ~440 stat HP they could hit). At L30 monsters dealing 2d4-3d4 (avg 7), ~120 HP = 17 hits. Tense but survivable for prepared player.
- L100 max-cook player reaches ~400 HP cap from cooking + ~76 stat HP = ~476. Vs Abaddon's avg 41 damage per hit, that's ~11 hits. Tense fight; not numerical immortality.
- **Descent is now incentivized to unlock cooking potential.** Patient camping at low floors gets you stuck under the curve.

---

## 6. The boss layered difficulty model (post-curve)

For each boss, the **base difficulty** value (1.0 = naive prepared player at the boss's floor) and the **multipliers** for each quest layer.

| Boss | Base | Quest Layer | Multiplier | Effective fight length |
|---|---|---|---|---|
| **Asterion (L20)** | 1.0 = 25 turn | Ariadne's Thread (defang) | 0.5 | ~12 turn |
| **Medusa (L40)** | 1.0 = 25-35 turn (lethal-on-gaze) | Aegis mirror | 0.5 | ~15 turn |
| | | Blindfold | 0.6 | ~18 turn |
| | | LOS pillars (always available) | 0.85 | ~24 turn |
| **Fafnir (L60)** | 1.0 = dragon_scales + fire/poison resist = brutal | Sigurd pit (in-pit 4×) | 0.4 | ~15 turn |
| | | Reforged Gram (secret) | 0.25 | ~8 turn |
| | | Fafnir's Blood (post-kill) | n/a | n/a |
| **Fenrir (L80)** | 1.0 = speed advantage + 5d8 bite | Gleipnir power-bind | 0.5 | ~20 turn |
| | | Vidar's Sandal (secret) | instant | 1 hit |
| | | ICE arena tactic | 0.8 | ~28 turn |
| **Abaddon (L100)** | 1.0 = 5-of-6 resistances + locusts | Seal gate (REQUIRED) | gate | n/a |
| | | L100 altar resist-strip | 0.6 (per burst) | ~40 turn |
| | | Sword of Michael (max karma) | 0.4 | ~12 turn |
| | | Heavenly Host (Scales) | locust handler | ambient |
| | | + Combined Sword + altar + Heavenly Host | 0.20 | ~6-8 turn |
| **Death** | n/a (unkillable normally) | Abyss ritual | one-shot | 1 turn |

**Stacking principle:** multipliers compose. Sword (0.4) + altar (0.6) ≈ 0.25 effective difficulty. Still requires solving the math, positioning, and resource management — never trivial, just *achievable*.

---

## 7. AC + THAC0 extension past L80

Currently THAC0 floors at -16 in data (no code clamp — confirmed via systems audit). The data must extend below -16 for boss-tier and elite monsters L80+.

Proposed monster THAC0 progression:
- L80 normal: -16 to -18
- L80 elite: -18 to -20
- L90 normal: -16 to -19
- L90 elite: -19 to -22
- L100 normal: -18 to -20
- L100 elite/boss: -22 to -26 (Abaddon at -24)

This means player AC -28 to -36 (SL profile) still has meaningful hit-avoidance against L100 elites. Currently AC < -16 is wasted.

---

## 8. Variety budget per band — fill the L91-99 monster gap

Each 10-floor band needs ≥10 distinct active monster species in the regular spawn pool. Current L91-99 reuses L81-90 entirely → fix by adding 4-5 new "Abaddon elite" species (themed: locusts evolved, fallen seals' lieutenants, void-spawn, etc.) with min_level 91-95.

Same principle: L71-80 currently has thin variety (audit found ~23 species). Add 3-4 species in L71-80 themed as "approach to the seal-hunt" — corrupted versions of L40-60 monsters, hellish heralds, demonic scouts.

---

## 9. The 11 distinct quest paths — quest content schedule

Per the systems audit:

| Floor band | Quest content | Currently | Curve target |
|---|---|---|---|
| L1-19 | Ariadne fountain (L17), Bronze Bull pickup | L17 fixed | **L14-20 (±3)** |
| L20-29 | Eye of Graeae spawn (L29) | L29 fixed | **L27-31** |
| L30-39 | Cow encounter (random L30-39) | already randomized | keep |
| L30-39 | Athena shrine (L37) | L37 fixed | **L34-40** |
| L40-49 | Broken Gram spawn (L48) | L48 fixed | **L45-50** |
| L50-59 | Odin shrine (L53) | L53 fixed | **L50-55** |
| L60-79 | Gleipnir components (L62-77, fixed) | 6 fixed floors | keep fixed (recipe predictability) |
| L70-79 | Dwarven Forge (L76), Vidar altar (L79) | L76, L79 fixed | **Forge L74-78, Vidar L77-79** |
| L81-99 | Seal demons (L83-97, fixed) | fixed | keep fixed (sequence matters) |
| L99 | Judgment altar | fixed | keep fixed (day-of-reckoning) |
| L100 | Abaddon arena + 6 altars | fixed | keep fixed |
| L1-99 | 10 leather scraps (Vidar secret) | 10 fixed floors | **all 10 randomize ±2** |
| L1-99 | Abyssal Shimmer, Wrench, Lake of Fire scroll, Tablet (Death-kill ritual) | random within bands already | confirm working |

---

## 10. Implementation roadmap (post-curve ratification)

When you bless this curve, the implementation work flows:

### Tier-A (curve enforcement — needs to happen first)

1. **Cooking softcap rewrite** — `player.py:194-213` formula changes to floor-derived. Test that existing cooking gameplay still works.
2. **Boss HP retune** — Asterion 800→600, Medusa 1500→1100, Fafnir 2500→2000, Fenrir 3000→2800, Abaddon 5000→6000.
3. **Sword of Michael nerf** — `weapon.json`: crit 4.0→2.5, abaddon_bonus_damage 6d10→3d10. Keep ignore_resistances + holy + max_chain 9.
4. **Monster THAC0 extension** — add 8-12 monsters L81-100 with THAC0 in -18 to -26 range. Update existing L100 elite THAC0.
5. **L91-99 monster fill** — design 4-5 new "Abaddon elite" species. Same for L71-80 quest-prep band.
6. **Validator script** (`tools/balance/validate.py`) reads data + reports drift.

### Tier-B (quest-mechanic fixes — post-curve)

7. **Quest altar randomization** — ±3 floor windows for Ariadne, Eye of Graeae, Athena, Broken Gram, Odin, Forge, Vidar.
8. **Leather scrap randomization** — ±2 windows for all 10.
9. **Seal artifact shatter-on-kill** — replace inventory item drop with one-time flavor message per seal (7 messages).
10. **Cow King story popup + chronicle** — absurdist tone.
11. **Persephone Q6 fix** — one-shot regen power.
12. **Remove `get_int_quiz_bonus()`** — WIS handles timer alone.
13. **Remove `gain_level` potion**.

### Tier-C (content additions — once curve is enforced)

14. Mid-tier weapon/armor wave at L75.
15. New Abaddon-elite monsters at L91-99.
16. New L71-80 quest-prep monsters.

### Tier-D (deferred polish)

17. Hint bank rewrite — comprehensive pass against the new system map.
18. Hidden character builds polish.
19. Duplicate hint cleanup.
20. Achilles heel mechanic (or remove the heel-tingle line).

---

## 11. What the validator will report

After Tier-A is implemented, `validate.py` runs against current data and outputs:

```
=== Cooking softcap drift ===
✗ Current softcap formula: flat 1000 → does not match floor-derived curve
✗ Effective cap at L20: ~1000 (target: 80) — gain rate decoupled

=== Boss HP drift ===
✓ Asterion HP: 600 (target: 600)
✓ Medusa HP: 1100 (target: 1100)
...

=== Monster THAC0 by floor ===
Floor 90: median THAC0 -16, max -16  (target: median -18, max -22)
   missing: ≥4 species with THAC0 < -18

=== Monster pool variety ===
Floor band 91-99: 22 species (target: 10 NEW species at min_level 91+)
   missing: at least 4 new species

=== Loot tier coverage ===
Floor band 71-80: 0 new weapons, 0 new armor (target: mid-tier wave at L75)
   missing: 4-6 weapons, 4-6 armor at min_level 75
```

This becomes our re-runnable yardstick. When you add new content, you run it to check fit.

---

## 12. What I need from you before implementation

Per your "ratify the intent first" direction, please react to:

1. **Anchor numbers** (sections 4) — any specific anchor's player HP, monster HP, or damage range feel wrong? Cooking softcap of 4×floor is the central lever; if you want softer (3×) or harder (5×), tell me.
2. **Boss HP retunes** (section 6) — Asterion 600, Medusa 1100, Fafnir 2000, Fenrir 2800, Abaddon 6000. Feel right?
3. **Sword of Michael nerf direction** (section 6, Layer 2 Abaddon) — crit 2.5× + abaddon_bonus 3d10. Feel right?
4. **Quest-layer multipliers** (section 6) — does 0.6 for altar resist-strip + 0.4 for Sword feel right? You wanted naive Abaddon to be near-impossible.
5. **THAC0 floor extension** (section 7) — extending to -24 for Abaddon — feel right?
6. **Variety budget** (section 8) — 4-5 new species at L91-99 + 3-4 at L71-80. Right count?

Once you ratify (or adjust), I:
- Write `curve.json` from the anchor table (machine-readable yardstick)
- Write `validate.py` (the drift reporter)
- Run validate against current data and report findings
- Begin Tier-A implementation in committed batches

Nothing in code changes until you ratify the intent.
