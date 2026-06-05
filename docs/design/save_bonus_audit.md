# Save-Bonus System — Design Audit & Proposal

*Status: design report (no code changes). Audited 2026-06-03. Owner decisions baked in:
**framework + best opportunities** (not exhaustive), **replacements-focused** (convert
samey/overlapping bonuses first), **gradient not immunity** (capped; full immunity stays
the rare resist items' job).*

---

## 1. Executive summary

The new saving-throw system (`status_effects.py`: `apply_debuff_with_save`) gives us a
clean third defensive tier between "no defense" and "full immunity":

```
  no defense  →  SAVE BONUSES (the gradient)  →  full immunity (resist items)
                 ← this audit ←
```

A **save bonus** = a flat `+N` to the player's d20 save roll for a category (CON/WIS/DEX).
It is the single highest-leverage fix for the game's biggest content-overlap problem:
**hundreds of bonuses across items, masteries, quirks, and recipes are interchangeable
"+X to a number."** Save bonuses let a thematic slice of them become distinct, memorable,
defensive identities — *without* inventing new subsystems, because every source can feed
one tiny new function.

**Recommendation: Option B ("Full gradient + recipe fix").** It delivers the whole
permanent+timed gradient, fixes a live recipe bug affecting ~110 dishes, and lands the
variety win, at moderate, well-contained effort. Details in §6.

**Two real bugs surfaced incidentally** (worth fixing regardless of which option):
the recipe `_TEMP_POWER_REMAP` silently rewrites ~110 control-resist dishes into the
wrong effect, and the `undead` mastery's "immune to fear" is unimplemented dead code (§4).

---

## 2. The framework (one mechanic, one insertion point)

All four audits converged on the same minimal design:

**Value shape.** A save bonus is `{cat: 'CON'|'WIS'|'DEX'|'all', amount: N}` — mirrors the
existing `{stat, amount}` and `{type, amount}` (resist) shapes, so it reads as native.

**Single consumer.** `apply_debuff_with_save` (`status_effects.py:404`) already computes:
```python
mod  = (int(getattr(player, stat, 10)) - 10) // 2
roll = randint(1, 20) + mod                 # <- the only change:
                                            #    + player.save_bonus_for(stat)
```
Add **`Player.save_bonus_for(cat)`** — a capped aggregator that sums every source. This is
the *entire* engine change. Everything else is content feeding it.

**The gradient guardrail (owner requirement).** `save_bonus_for` clamps the total with
diminishing returns: **+5 hard ceiling overall, +3 from any single lane (food/timed).**
Because the monster DC is capped at 18 and a save is `d20 + mod + bonus`, a +5 ceiling
still leaves a real failure chance at depth — so stacking never reaches immunity. Full
immunity remains exclusively the job of `_RESIST_BLOCKS` resist items
(`status_effects.py:157`), which short-circuit *before* the save math.

**Two lanes (no overlap between them):**
| Lane | Sources | Lifetime | Cap |
|---|---|---|---|
| **Permanent** | equipment, masteries, quirk-passives, build affinity | while equipped/owned | +5 total |
| **Timed** | cooked "ward" food, active powers, hero specials | N turns (chain-scaled) | +3 |

**Reuse, don't reinvent — the precedents to copy:**
- `chain_passives.sum_passive_values` / `get_death_save_bonus` (`chain_passives.py:63,210`) —
  the exact "sum a typed value across all sources, capped by caller" idiom for `save_bonus_for`.
- `chain_equip.apply_tier_bonuses` key-prefix dispatch (`chain_equip.py:85-207`) — add a
  `save_bonus_<CAT>` prefix exactly like the existing `resistance_<type>` / `stat_bonus_<STAT>`.
- `_stand_ac_bonus` companion-field pattern (status flag for duration + `player._x` field for
  magnitude + `max()` refresh + expiry cleanup; `hero_specials.py:628`, `status_effects.py:546`)
  — the template for a **tiered timed** ward.
- `cooking_stat_gained` softcap (`player.py:496`) — the diminishing-returns philosophy.

---

## 3. Findings by system (the overlap pools + best opportunities)

### 3.1 Items  (199 accessories, 96 weapons, 59 armor, 37 shields, 26 artifacts)
**Overlap pool:** **114 flat single-`+stat` accessories** + 8 dual-stat; the six stat-rings
exist in ~4 material reskins *each*, and the amulet line duplicates all six again — ~80+
near-identical commons differing only by a gem name and a number. Plus **23 named uniques
whose ONLY effect is a flat `+stat`** despite having full legendary lore.
**Doubly redundant:** flat `+CON/+WIS/+DEX` items already feed the save roll implicitly — making
that defensive identity explicit and category-scoped is pure upside.
**Best conversions** (theme already written): `amulet_of_fortitude` (CON+3)→CON saves;
`amulet_of_insight` (WIS+3)→WIS saves; `anklet_of_atalanta`→DEX saves folded into its
chain-equip ladder (shows the gradient on a unique); `kavacha_kundala`/`menat_of_hathor`→CON.
**Net-new:** Ring of Iron Will (WIS), Boots of the Cat (DEX — the thinnest-covered category).
*Wiring:* `effects` channel in `_apply_equip` (`player.py:1418`) + `tier_bonuses` prefix; store
a running `player._save_bonus={'CON':n,'WIS':n,'DEX':n}` like `_accessory_ac_bonus`.

### 3.2 Masteries  (277 unique + ~50 class + 12 family blessings — the #1 overlap)
**Overlap pool:** **60 `accessory_stat_bonus`** (worst offender — identical `{stat,amount:1-2}`),
12 `class_acc_stat_bonus`, 32 `armor_ac_bonus`, 29 `armor_hp_bonus`. All undifferentiated.
**Highest leverage = the 12 monster-family blessings:** mastering a family should teach you to
resist *that family's* control style. fey→WIS (charm), aberration→WIS (confusion),
undead→WIS (fear — *finishes the dead-code promise*), dragon→CON (freeze/frightful), demon→WIS.
This converts low-variety `+damage vs tag` into defensive identities **and retires two
special-case branches** (the fey charm-halve at `player.py:638` and aberration duration-subtract
at `:640`) into one uniform mechanism.
**Also:** re-theme the defensively-named class rings (`ring_of_constitution`→CON saves,
`ring_of_wisdom`→WIS, `ring_of_dexterity`→DEX); leave STR/INT/PER as true stats (no save axis).
*Wiring:* lazy/passive kind — no `_apply_mastery_once` change; `save_bonus_for` walks all three
mastery stores (the multi-store walk already exists at `combat.py:581`, `player.py:259/652`).

### 3.3 Quirks / Powers / Hero specials  (100 quirks, 31 powers, 19 hero actives)
**Headline conversion — PERSEUS.** The Perseus quirk currently *halves all incoming debuff
durations* (`player.py:623`) — an opaque, multiplicative lever that double-dips with the new
save's negate/halve and silently nerfs even poison/bleed. **Convert it to a clean `{all,+2}`
save bonus** (its Gorgon-shield "turn the attack aside" theme is perfect), make it legible,
fold it into the capped gradient, and delete a branch from the hot `add_effect` path.
**Overlap pool:** ~40 flat `+stat` quirks; the CON cluster (8: Darwin, Fenrir, Leonidas, Ragnarök…)
is over-served, WIS/DEX under-served. Convert the ones whose *trigger theme already screams the
category*: Darwin ("survive 8 debuff types")→`{all,+2}`, Fenrir ("endure 150 debuff turns")→CON,
Nostradamus ("recall while mind-debuffed")→WIS, Atalanta ("Winged Feet")→DEX.
**Net-new timed (the brief's ask):** an active **"Steel Yourself"** power granting a timed
`save_warded` buff (proactive — distinct from the existing *reactive* mind_fortress/reality_anchor
cleanses), and a **tier-scaled save grant on Leonidas's Spartan Stand** (the `tier_effects`
gradient is already there).
*Gotcha:* quirks have **no machine-readable effect table** (effects are lambdas), so quirk work
must be in-place `apply_fn` edits — which is exactly the replacements-focused directive. Net-new
grants belong in powers/hero-specials, which *are* data-driven.

### 3.4 Recipes / Cooking + Builds  (620 recipes, ~38 builds) — the marquee opportunity
**THE biggest single win.** Cooking is an escalator_chain quiz whose chain depth already scales
the outcome (a built-in gradient), and T5 dishes grant **timed buffs** — the natural home for
*tactical, pre-fight* save bonuses ("eat the Aspic before the cockatrice room").
**But there's a bug** (see §4): `_TEMP_POWER_REMAP` (`food_system.py:186`) silently collapses 35
authored `temp_power` names into 23, **mis-firing ~110 control-resist dishes** — a "Floating-Eye
Aspic: immune to paralysis" actually fires `sleep_resist`; Gorgon's Antitoxin's `petrify_resist`
→ `sleep_resist`. These ~110 dishes' lore *already* describes resisting paralysis/stun/
petrify/charm — they map **perfectly** onto a new **timed "ward" family**:
- `save_guard_CON` ← the ~40 paralyze/stun/petrify-resist dishes
- `save_guard_WIS` ← the ~64 confuse/charm/fear/hallucinate-resist dishes
- `save_guard_DEX` ← a fresh slice for slow/immobilize (fast/slippery monster primes)

Chain length scales magnitude (`{3:+1, 4:+2, 5:+3}`), capped +3 (temporary). This restores the
authors' original intent *and* creates the tactical timed lane in one move.
**Builds:** defensive identity is currently thin (only ~3 of 38 have any CC defense, all bespoke).
Add an optional `_save_bonus` build-metadata key: Stalwart/CON builds (Leonidas, Boudicca,
Achilles)→CON; Sage/WIS (Socrates, Joan, Hildegard)→WIS; Scout/DEX (Hermes, Ciri, Musashi)→DEX;
leave frail mages save-free (their fragility is the point — makes affinity a real trade-off).
*Wiring:* pure data for builds (`_save_bonus` in `SECRET_BUILDS`, consumed in the `main.py:316`
stat loop); register `save_guard_*` in `BUFFS`/`EFFECT_INFO` (NOT `DEBUFFS`, or cleanses wipe them).

---

## 4. Incidental bugs found (fix regardless of option)

1. **Recipe `_TEMP_POWER_REMAP` mis-fires ~110 dishes** (`food_system.py:186-213`). Authored
   `paralyze_resist`/`stunned_resist`/`petrify_resist` all silently become `sleep_resist`;
   `confused_resist`/`charm_resist`/`hallucinate_resist`/`silenced_resist` all become
   `magic_resist`. The dishes' descriptions promise specific protections the game doesn't deliver.
   (The ward-family conversion fixes this by design — remove the remap entries so they pass through.)
2. **`undead` family mastery "immune to fear from undead" is dead code** (`monster_classes.py:66`
   desc only; no implementation). The family→WIS-save conversion realizes this existing promise.

---

## 5. The coverage caveat (read before scoping)

Save bonuses only bite where `apply_debuff_with_save` is used. Today that's the **generic
monster-attack path** (`monster.py:705` — covers all ~332 monster melee/attack debuffs ✓) plus
the two gaze attacks. **Debuffs from other sources still route through plain `player.add_effect`**
and are NOT save-gated: traps, some monster spell/ability effects, environmental hazards. For the
save system (and thus save bonuses) to feel *consistent*, those sources should also be routed
through `apply_debuff_with_save`. This is the main argument for the coverage-expansion work in
Option C — without it, a player with big WIS-save gear still gets confused with no save by a trap.

---

## 6. Three options (scope ladder) — recommend **B**

### Option A — "Foundation + Family"  *(lowest risk, proves the system)*
- Build the core: `save_bonus_for` + `{cat,amount}` + the capped gradient + the one-line
  `status_effects.py:404` insertion.
- Convert the **12 monster-family masteries** (highest theme-per-edit; retires 2 special-case
  branches; finishes the undead dead-code promise).
- Convert **Perseus** → `{all,+2}` (the headline proto-save cleanup).
- Add **build save-affinity** (pure data) for ~10 archetype builds.
- *Fun:* "master a family / pick a build → resist its control." *Effort:* small, ~2-3 files +
  data. *Risk:* very low (additive + a few conversions). *Gap:* no timed lane, items untouched.

### Option B — "Full gradient + recipe fix"  ✅ RECOMMENDED
- Everything in A, **plus:**
- The **recipe "ward" family** — convert the ~110 mis-remapped control-resist dishes into
  `save_guard_CON/WIS/DEX` timed buffs (chain-scaled, +3 cap). **Fixes bug #1.** Creates the
  tactical timed lane.
- Convert a **curated set of equipment** (the named uniques whose lore already fits +
  retheme a slice of the duplicate stat-rings) + a slice of the **60 `accessory_stat_bonus`
  masteries**.
- *Fun:* the complete gradient across both lanes — permanent build/gear identity AND tactical
  "eat-before-the-fight" prep; fixes dishes that currently lie to the player. *Effort:* moderate,
  well-contained (mostly data + the one engine function + the food remap cleanup). *Risk:*
  moderate, all gated by the +5/+3 caps; immunity tier untouched. **Best balance of impact, fun,
  and effort.**

### Option C — "Full system + coverage expansion"  *(maximal)*
- Everything in B, **plus:**
- **Coverage expansion** — route traps + non-attack debuff sources through
  `apply_debuff_with_save` so saves (and bonuses) apply consistently everywhere (§5).
- Active **"Steel Yourself" powers** + **hero-special tier-scaled** save grants.
- Broader conversions across all overlap pools (the full 114 stat-rings / 60 masteries / etc.).
- *Fun:* the most variety + a consistent save everywhere. *Effort:* large; biggest balance
  surface to playtest. *Risk:* higher — coverage expansion changes how many debuffs are
  resistable, which shifts overall difficulty and needs real play-testing.

---

## 7. If you pick B — concrete phase-1 order

1. **Engine (once):** `Player.save_bonus_for(cat)` (capped-sum, reads gear/mastery/quirk/
   timed-buff/build sources) + the `status_effects.py:404` insertion + register `save_guard_*`
   in `BUFFS`/`EFFECT_INFO`. Tests: save-bonus shifts roll; cap holds; immunity unaffected.
2. **Masteries:** the 12 family blessings + retire the fey/aberration special cases. (Highest
   leverage; tests already exist for the family-mastery round-trip.)
3. **Perseus** conversion + delete the `add_effect` halving branch.
4. **Builds:** `_save_bonus` data on ~10 archetype builds.
5. **Recipes:** the ward family + strip the offending `_TEMP_POWER_REMAP` rows (fixes bug #1);
   chain-scaled magnitude via the existing `tier_outcomes` shape.
6. **Equipment:** the curated unique/ring conversions + `tier_bonuses` `save_bonus_<CAT>` prefix.
7. **Play-test** (CLAUDE.md): floor-1 sea snake with/without a CON build/ring/ward to feel the
   gradient; confirm late-game monsters still land control on an invested build (cap working).

---

## 8. Open questions for the owner
- **Stack model:** hard cap (+5, simple) vs diminishing sum (+2,+1,+1…). Recommend hard cap.
- **Should saves cover traps/non-attack debuffs now (Option C §5), or stay attack-only for now?**
  This is the single biggest "does it feel consistent" decision.
- **Food ward duration:** fixed (~150t) vs chain-scaled (80/150/250). Recommend chain-scaled
  (uses the existing gradient, rewards better cooking).
- **STR/INT/PER:** confirmed they get NO save category (only CON/WIS/DEX map to saves). This
  keeps those three as pure stat bumps so not *everything* becomes a save — intended contrast.
