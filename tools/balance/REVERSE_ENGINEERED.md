# Reverse-Engineered Curve Intent — Philosopher's Quest

**Goal:** infer what the *designer was trying to achieve* (not just describe the data). Surface intent so we can ratify it, then build a corrected unified curve on top.

---

## 1. The cooking-as-leveling system — intent is fully legible in code

`src/food_system.py:25-46` contains the entire cooking formula in 22 lines. The math tells a clear story.

### The formula

```python
potency(min_level)         = sqrt(min_level)            # L1 → 1.0;  L100 → 10.0
SINGLE_MULT[quality 1-5]   = 0.3, 0.6, 0.9, 1.5, 2.2
COMPOUND_MULT[quality 1-5] = 0.6, 1.1, 1.8, 3.0, 4.5    # ~2× SINGLE
compound bonus             = 1.0 + 0.15 × (n_ingredients - 2)
```

Per-cook HP gain at each end of the dungeon:

| Cook type | L1 ingredient | L100 ingredient |
|---|---|---|
| Single Q1 (rough) | 1 HP | 3 HP |
| Single Q5 (masterwork) | 2 HP | 22 HP |
| Compound Q5 (2-ing) | 1 HP | 45 HP |
| Compound Q5 (3-ing) | 1 HP | 52 HP |
| Compound Q5 (4-ing) | 1 HP | 58 HP |

### Soft cap (player.py:194)

```python
cap_factor = max(0.20, 1.0 - cooking_hp_gained / 1000)
effective_gain = base_gain × cap_factor
```

Asymptotic approach to ~1000 cooking HP. Past 800 accumulated, every new cook is 0.20× value. Theoretical mathematical ceiling: ~1000 + slow ε.

### What the code says the designer intended

1. **Quality is the dominant multiplier.** Q5 vs Q1 ≈ 7×. Quiz performance is the main skill expression.
2. **Ingredient depth is the second multiplier.** L100 ingredient = 10× the HP of an L1 ingredient. Players must descend to gain access to more potent food.
3. **Compound recipes are roughly 2× single recipes.** Strong incentive to forage multiple monster types and combine.
4. **The 3-and-4-ingredient bonuses encourage discovery.** +15%/+30% over 2-ingredient base.
5. **Quizzes always start at T1.** This is critical — the cooking quiz difficulty does *not* scale with floor. A L1 5th-grader-tier question, answered five times in a chain, produces an L100 Q5 cook. Cooking rewards *speed and stamina*, not difficulty escalation. The quiz tier escalates only WITHIN the chain (escalator_chain mode).
6. **Cooking is the only source of permanent max HP growth** outside CON stat gains from accessories/scrolls.

### The breakage

**The 1000 softcap is fixed regardless of floor.** This is the single point where the design intent fights the curve.

- A patient L30 player can grind cooking to 600+ HP. They are now over-leveled for L30 monsters.
- A non-cooking L100 player has ~44 stat HP. They die in one Abaddon hit.
- The variance between "cooks every harvest" and "ignores cooking" is the design's intended skill axis, but the absolute ceiling (1000) doesn't track the monster damage curve.

**The shape is correct. The ceiling formula is missing a floor-dependence term.**

### Fixing-in-intent

The softcap should be a function of dungeon level reached. Sketch:

```
softcap(floor)  = base + slope × floor          # something like base=30, slope=10
                                                # → L1 cap ~40, L50 cap ~530, L100 cap ~1030
```

This preserves every part of the existing system (formulas, recipes, quizzes, compound bonuses, diminishing returns) and only changes the ceiling. Players still grind cooking — but the ceiling moves with them.

---

## 2. The boss + altar layered combat system — intent is *gorgeous*

`src/game_divine.py:740-829` reveals a beautifully designed layered fight at L100.

### Mechanics

- **Prayer at any altar:** theology threshold quiz, chain 0-8. The chain value (plus +1 if at_altar) determines outcome.
- **L99 altars are SPECIAL:** when prayed at with chain > 0, they strip Abaddon's resistances for `chain × 2` turns.
- **Each L99 altar is single-use** (`_l100_altars_used` set). The arena presumably has multiple altars (need to confirm from boss_levels.py).
- **Prayer cooldown:** `max(100, 80 + effective × 25)` = 105 to 280 turns base, depending on chain.
- **Fisher King quirk halves cooldown.** Fisher King mystery halves AGAIN (stacks). The audit flagged this as bug — could be intentional, very strong combo.
- **During Death chase, prayer also freezes Death** for 3-8 turns.

### The layered combat intent

This is the design:

```
LAYER 0 (gate, REQUIRED): break 7 seal demons (L83/85/87/89/91/93/97) to access Abaddon
LAYER 1 (combat, FUNCTIONALLY REQUIRED): use L99 altars during the fight to open resist-strip burst windows
LAYER 2 (max-prep, OPTIONAL): Sword of Michael (max-karma reward) bypasses resistances permanently AND
                              gets +holy weakness bonus + abaddon_bonus_damage
LAYER 3 (secret, INVOCATION-LEVEL): Stone + Tablet of Second Death + Lake of Fire scroll → kill Death entirely
```

**Without Layer 1 (altars), Abaddon's full resistance set (`poison, cold, fire, slash, blunt`) makes him a sponge.** Only "magic" / "holy" / "drain" / "lightning" / "acid" damage gets through unattenuated.

**With Layer 1 (altars used during fight),** the resist-strip window opens a burst-damage opportunity. A chain-5 prayer = 10 turns of full damage. If the arena has 4-6 altars, the player can chain multiple windows.

**With Layer 2 (Sword), the Sword's `ignore_resistances` flag means it's always-good — and the altar windows additionally amplify holy damage further.**

### The Sword of Michael analysis (correcting the audit)

The audit's "one-shot lethal vs Abaddon" calculation:
```
45 base × 16x chain × 4x crit × 1.5 holy × ignore_resist + 6d10 abaddon_bonus ≈ 5650
```

Decomposing:
- **45 base damage** is fine for an L99 max-karma reward
- **16x chain multiplier** at chain 9 (the max chain) — this is the same as other endgame weapons (Tyrfing peaks at 16x too). Not the Sword's signature.
- **4x crit multiplier** is the Sword-specific oddity. Most weapons cap crit at 2.0–2.5x. The Sword at 4x is the outlier.
- **1.5x holy weakness** is the Sword's signature — does its job
- **ignore_resistances** is what makes it work against Abaddon at all (without altar) — does its job
- **6d10 abaddon_bonus_damage** is the special-case spice — does its job

**The numerical outlier is the 4x crit multiplier stacking with the 16x max chain.** Cap crit at 2.0 or 2.5x and the Sword goes from "1-shot Abaddon at max chain+crit" to "the same Abaddon fight, but the Sword + altar combo gives a clean win that's still earned."

### Open question about boss arena altar count

I haven't confirmed how many L99 altars exist in the arena. `_l100_altars_used` is a set — if there's only 1, the Layer 1 design is single-window-only. If there are 4-6, the design supports sustained burst phases.

---

## 3. Monster scaling — curated by floor, not artificial

`src/dungeon.py:1076-1175` reveals the spawn-pool composition algorithm.

### How it works

- Each monster has fixed `hp`, `damage`, `thac0`, `attacks` in `monsters.json`. No floor-multiplier.
- Each monster has `min_level` (when it starts appearing) and optional `max_level` (when it stops).
- `frequency` is the base spawn weight (0 = bosses, won't spawn naturally).
- At L1-29: linear floor weighting, `max_level` decays gently (floors at 1).
- At L30+: **proximity-based weighting**. On-level monsters (within ±5 floors) get `freq × (2 + prox_scale)`, where `prox_scale = (level - 30) / 10`. At L100, on-level monsters get 9× weight; far-from-level decay to zero (no floor).
- Spawn count: `randint(min(4 + lvl/10, 8), min(6 + lvl/5, 14))` = 4-6 at L1, 10-15 at L50+.
- Packs spawn variable extras: 1-2 at L<30, 2-3 at L30-59, 2-4 at L60+.

### Boss progression (from monsters.json)

| Boss | Floor | HP | THAC0 | Notes |
|---|---|---|---|---|
| Asterion (Minotaur) | L20 | 800 | 4 | Hit-and-run + can_phase_walls. Thread quest defangs (currently leaks to vampires too). |
| Medusa (Gorgon) | L40 | 1500 | -3 | Quest layer TBD — to investigate |
| Fafnir (Dragon) | L60 | 2500 | -12 | Resistances + dragon_scales (0.8 physical absorb). Blood drop hints at reforge ritual. |
| Fenrir (Wolf) | L80 | 3000 | -16 | Vidar's Sandal instant-kill is one quest layer |
| Abaddon (Destroyer) | L100 | 5000 | -16 | Seal-gate, altar Layer 1, Sword Layer 2 |
| Cow King (secret) | L30-39 | 550 | 2 | Secret cow level |

### Boss HP progression and the L60→L80 anomaly

```
L20:   800  (Asterion)
L40:  1500  (Medusa)        +700  (1.9×)
L60:  2500  (Fafnir)       +1000  (1.7×)
L80:  3000  (Fenrir)        +500  (1.2×)   ← anomaly
L100: 5000  (Abaddon)      +2000  (1.7×)
```

The L60→L80 jump is suspiciously small (1.2× vs ~1.7-1.9× elsewhere). Either Fenrir is under-tuned for his floor band, or the curve intentionally dips (Fenrir's signature is his speed + Vidar quest, not raw HP).

### THAC0 ceiling

```
L20:    4
L40:   -3   (-7 jump)
L60:  -12   (-9 jump)
L80:  -16   (-4 jump — slowing)
L100: -16   (flat — at the hit-chance floor)
```

**Past L80, THAC0 is at the hardcoded floor.** Audit flagged correctly. AC investment past L40-ish has diminishing return on hit-avoidance because monster accuracy is capped.

### Normal monster pool by band (from balance_curves_agent_a.json)

| Band | Pool size (active species) | Notes |
|---|---|---|
| L1-10 | 30+ | Diverse, plays clean |
| L11-30 | 25-32 | Good variety |
| L31-50 | 27-30 | Good variety |
| L51-70 | 28-32 | Peak variety |
| L71-80 | 23-25 | Drop |
| L81-90 | 22-28 | Recovers |
| L91-99 | ~22 (reuses 81-90 pool) | **No new species** |

**The variety drops at L71-80 first, then again at L91-99 (no new species at all).**

---

## 4. Loot progression — current state from balance_curves_agent_a.json

Weapon `min_level` distribution (counting items that become available at each band):

| Band | New weapons | New armor | New shields | New accessories |
|---|---|---|---|---|
| 1-10 | 14 | many | several | several |
| 11-20 | 19 | yes | yes | yes |
| 21-30 | 12 | yes | yes | yes |
| 31-40 | 18 | yes | yes | yes |
| 41-50 | 16 | yes | yes | yes |
| 51-60 | 20 | yes | yes | yes |
| 61-70 | 36 (peak — 22 generic diamond + 11 L65 uniques + 3 L70 uniques) | yes | yes | yes |
| **71-80** | **0** (obsidian shield = +3 AC, redundant with L51 mithril) | **0** | obsidian shield | **0** |
| 81-90 | 26 (22 adamantine generic + 4 uniques) | 12 dragonscale | yes | yes |
| **91-99** | **0** | **0** | **0** | **0** |

### What the data implies about pacing intent

- The designer wanted a major *gear inflection* at L20 (Asterion era), L40 (Medusa era), L60 (Fafnir era), L80 (Fenrir era), L100 (Abaddon era).
- Mid-band gear comes in waves (e.g., L65 unique cluster between Fafnir and Fenrir).
- **L71-80 and L91-99 are genuinely empty.** These are not "by design quiet stretches" — based on the rhythm, they were probably supposed to have intermediate waves and got skipped.

### Recommendation surface (for Stage 2)

- Add a mid-tier weapon wave at L75 (between Fafnir/diamond uniques at L65-70 and adamantine at L81)
- Add an accessory wave at L75 (between L70 Heart of Ahriman and L9999 uniques)
- Add 5-8 new normal monster species in the L91-99 band (Abaddon's "elite guards" before the throne, e.g.)
- These additions are *not* about making the game easier — they're about preserving the encounter variety and decision space the rest of the dungeon has

---

## 5. Stat / AC / damage architecture

### Player base stats (from player.py)

```
BASE_HP = 20
max_hp  = BASE_HP + CON                        # CON 10 = max_hp 30; CON 20 = max_hp 40
max_sp  = (something) + STR
max_mp  = (something) + INT
```

### CON ceiling without cooking

A typical L100 player CON build: base 10 + ~14 from late accessories (Idunn's Apple +5, Heart of Ahriman +X, Amulet of Titan Constitution +5) = CON ~24 → max_hp ~44.

This is the audit's "44 HP" stat-only figure. The number is correct; the framing was wrong (cooking IS the leveling track, not a parallel one).

### Player damage output by chain

For a typical late-game weapon (`base_damage` = 30-45, chain multipliers [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, ... up to weapon's max]):

- Chain 1 (first answer wrong, or 1 correct): 0.5× base
- Chain 3: 1.5× base
- Chain 5 (median): 2.5-3× base
- Chain 8-9 (max for most weapons, requires perfect math): 5-6× base
- Chain 9+ on Sword of Michael (max chain 9, multipliers go to 16×): special endgame

**Most chains end at 3-5.** Max chain is the "lucky+skilled" tail. The variance corridor is: 1-2× (unprepared) to 5-6× (skilled+lucky), with the Sword at endgame pushing to 16×.

### AC progression

- Naked: AC 10 (worst)
- Iron armor (early): AC 5-8
- Diamond armor (L60s): AC -10 to -15
- Adamantine + uniques (L80s+): AC -20 to -28
- Best-case stack: AC ~-33 (Dexterity + Tower shield + full late armor)

Monster THAC0 needs to *match* this curve. Currently floors at -16, so any AC better than -16 is wasted past L80.

---

## 6. The seal-demon gating sub-track

Seal demons live at **L83, L85, L87, L89, L91, L93, L97** (7 floors). All have `is_seal_demon: true`, HP ~1200, THAC0 -16, very tough.

Player must kill ALL 7 to break the gate to Abaddon. There's an unlock message at game_combat.py:608:
> "ALL SEVEN SEALS ARE BROKEN. The way to the Pit stands open."

This is the L83-99 prep phase. The player's *primary work* during this stretch is hunting seal demons, not finding new gear. **This reframes the "dead band":**

- **L71-80**: genuinely under-content (no gear, no seal demons, no quest hooks I've found). This is a real gap.
- **L81-99**: seal hunt IS the content. Lack of new normal monsters is fine because the player is hunting boss-tier seal demons.

---

## 7. Internal contradictions / broken data

1. **THAC0 floor at -16 from L40+** breaks AC progression. AC investment past mid-game is largely wasted.
2. **L60→L80 boss HP jump is only 1.2× vs ~1.7× elsewhere.** Fenrir is HP-under-tuned for his floor.
3. **Cooking softcap (1000) doesn't scale with floor reached.** A patient cook can over-level at L30.
4. **Cooking variance is huge** (cooked = 1000 HP, non-cooked = 44 HP). The system requires cooking to be balanced for the monster damage curve.
5. **Variety dip L71-80** with no monster species being introduced.
6. **L91-99 reuses L81-90 monster pool entirely.** 9 floors of recycled content.
7. **Ariadne's Thread leaks past Minotaur** to defang elder_vampire and ancient_vampire_lord. Audit-confirmed, code-confirmed. Intent was Minotaur-only.
8. **monsters.json:19682 `can_phase_walls`** is only on 3 monsters (Asterion + 2 vampires) — the Thread's mechanic implementation matches the data but the data was over-broad.
9. **Spell damage was bypassing all resistances until our Phase 2C fix.** Now correctly applies.
10. **THAC0 hardcoded floor (combat.py)** at -16 — needs to extend.

---

## 8. The question matrix — what I can't infer from data alone

These need your design ratification before I draft the corrected curve.

### About cooking-as-leveling

**Q1.** The 1000 softcap — was it ever supposed to be floor-aware, or is the asymptotic ceiling the design and I should think of it as "you reach max HP late and slowly"?

**Q2.** Should max-cooked HP at floor 100 be: ~300 (the audit's "tame" suggestion), ~700-900 (current achievable), ~1500+ (full re-tune with monster damage scaled up)? Pick a ballpark — I'll calibrate everything else to it.

**Q3.** Compound recipes: should the 3-ing/4-ing bonus (+15%/+30%) be steeper to incentivize foraging more? Or current shape correct?

### About boss layers

**Q4.** Each boss should have its own quest-layer table (base × multiplier per layer). I have:
- Asterion: Thread quest (Layer 1, defang). Are there other quest layers?
- Medusa: ??? — I haven't found her quest layer yet
- Fafnir: blood drop hints at "reforge ritual" — what's the quest?
- Fenrir: Vidar's Sandal instant-kill (Layer 1)
- Abaddon: seal gate (Layer 0), altar (Layer 1), Sword (Layer 2), kill-Death secret (Layer 3)

Can you name the quest layers I'm missing for Medusa and Fafnir?

**Q5.** L99 altar count — how many altars are in the Abaddon arena? Boss_levels.py would tell me, but the user-intent question is: was the design 1 altar (one window), 3-4 altars (sustained burst phases), or more?

**Q6.** Sword of Michael — the 4× critMultiplier is the numerical outlier. Lowering it to 2.0-2.5× keeps the Sword strong but removes the 1-shot. Do you want:
- (a) Keep crit at 4× (current), and instead make Abaddon HP higher (8000-10000)
- (b) Drop Sword crit to 2.0×, keep Abaddon HP at 5000
- (c) Drop Sword crit to 2.5×, drop abaddon_bonus_damage to 3d10 (gentler nerf)
- (d) Something else

### About monsters and loot

**Q7.** The L71-80 gap. What should fill it? Options:
- A small intermediate gear wave (mithril-tier upgrade at L75 — 4-6 items)
- Quest-prep content (NPCs hinting at the upcoming seal hunt, lore drops about Abaddon)
- A "transition mini-boss" at L75 (similar to Cow King, side-content)
- All of the above

**Q8.** The L91-99 monster pool. Should we add 5-8 new "elite guard" species themed for Abaddon's approach? Or is this band intentionally about seal demons only?

**Q9.** THAC0 floor extension. Currently capped at -16. To make AC matter at L100, monsters need to push further. Should we:
- (a) Extend THAC0 to -22 for L81-100 monsters and adjust the hardcoded floor (-16) in combat.py
- (b) Keep -16 floor, accept that AC plateaus
- (c) Make THAC0 monster-class-dependent (bosses go further, regular monsters cap)

### About variance and completion targets

**Q10.** You said skilled completion rate ~10-20%. Roughly what depth do you want the *median* run to reach? (Floor 30? 60? Affects how lethal the early game should be.)

**Q11.** Lucky+skilled runs should go ~15-25 floors deeper than median. So if median = 30, lucky+skilled = 50ish. If median = 60, lucky+skilled = 85ish. What's right?

### About discoverability

**Q12.** "Figuring out you need to use the altars is part of the puzzle." The current lore (hints.json) has T2 hint mentioning altars: *"Strange altars sometimes appear in the dungeon. Those who approach and kneel before them discover ancient challenges — and ancient rewards."* But there's no T5 hint specifically about the L99 altar resist-strip mechanic. Should we add one? The voice-spoiler line is "hint, don't explain." Something like *"In the deepest places, holy fire calls. The Destroyer's defenses are not as eternal as he believes — not where the altars rise."*

**Q13.** Other quest discoveries (Vidar vs Fenrir, Thread vs Asterion, the reforge ritual hinted at by Fafnir's blood) — do you want the curve pass to also audit *lore coverage* of each quest? Or is that separate from the curve work?

---

## 9. What I propose next

When you ratify (or adjust) the answers above, I'll:

1. Build `tools/balance/curve.json` — anchor floors 1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, plus Death-chase band. Each anchor specifies player expected stats, monster threat band, loot tiers, cooking ceiling, math tier, boss multipliers.
2. Build `tools/balance/CURVE.md` — design rationale doc.
3. Build `tools/balance/validate.py` — re-runnable validator that reads current data and reports curve drift.
4. Run the validator and produce a "what needs to change" delta report.

Then we tune system by system, with you reviewing each implementation batch.
