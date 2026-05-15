# BALANCE — progression curves and difficulty integrity

**Read `tools/audit/CONTEXT.md` first.**

## Mission
This game must be **HARD by design**. Tier 1 questions are 5th-grade material; Tier 5 is 9th–10th grade. The kids playing are younger than that. Real-world reward codes are gated on the player actually reaching above their current learning. **If the game is beatable without learning, the entire reward economy collapses.** "Too easy" is a P1 finding — same severity as a game-breaker.

You are not just looking at items in isolation. You are auditing the **whole power curve** across:
- Monster stats by floor (HP, damage, AC, special abilities, AI pattern)
- Item power by `min_level` (weapons, armor, shields, accessories, artifacts)
- Spells, wands, scrolls by tier
- Quirks (~80 of them — many materially shift power)
- Status effects (offensive and defensive)
- Food/cooking bonuses
- Boss difficulty at L100 (Abaddon) and during the Death-chase escape
- Score economy and how it ties to milestones

Single-item observations are out of scope unless they sit inside a curve-level finding. **Every BALANCE finding must span ≥2 systems** (e.g., "weapon X at min_level 10 trivializes monsters floors 15–40" spans items + monsters; "spell Y plus quirk Z renders Death chase trivial" spans spells + quirks + escape phase).

## Required deliverable
`tools/audit/deliverables/balance_curves.json` — a numeric progression table, JSON. Structure:

```json
{
  "monsters_by_floor": [
    {"floor": 1, "monsters": [{"id": "rat", "hp": 5, "dmg": "1d2", "ac": 10, "ai": "aggressive", "min": 1, "max": 4}, ...]},
    ...
  ],
  "weapons_by_min_level": [
    {"id": "dagger", "min_level": 1, "damage": "1d4", "speed": 1.0, "special": null}, ...
  ],
  "armor_by_min_level": [...],
  "shields_by_min_level": [...],
  "accessories_by_min_level": [...],
  "spells_by_tier": [...],
  "wands_by_tier": [...],
  "boss_stats": {"abaddon": {...}, "minibosses": [...]},
  "death_chase_difficulty": {"speeds": [50, 75, 100, 125], "freezable": true, "freeze_method": "prayer"},
  "score_economy": {"per_turn": 10, "per_max_floor": 1000, "per_kill": 100, "stone_bonus": 50000}
}
```

Build this table by reading `data/monsters.json`, `data/items/*.json`, `src/spells.py`, `src/boss_levels.py`, `src/main.py`. If a field is genuinely absent or unparseable, note it in `balance_curves.json` under `"_data_gaps": [...]`.

The table is *evidence for your findings*. You then write the findings as separate files grounded in the table's numbers.

## Seed threads (investigate at minimum)
1. **Dead bands** — any 5+ consecutive floors with no meaningful loot upgrade in any slot (weapon/armor/shield/accessory)?
2. **Power spikes** — any item whose damage/AC/effect dominates a 5+ floor band? Specifically: can a floor-10 weapon carry to floor 60? Can a floor-30 accessory still be best-in-slot at 90?
3. **Monster gaps** — `tests/test_balance.py` already checks for monster gaps. Verify the curve is smooth in HP, damage, AC, and *encounter variety* (not just one monster per band).
4. **Boss difficulty** — Abaddon at L100. Cross-reference Abaddon's stats with player builds at floor 100 (max HP, best weapon, typical loadout). Is Abaddon a real wall? Or trivial with the right pre-stack?
5. **Death-chase curve** — Death starts at 50% speed and escalates 50→75→100→125. Player ascends 100 floors. Is the chase actually scary? Or is it ignorable? Does prayer-freeze trivialize it (especially with high WIS / theology investment)? Are there obvious cheese strategies?
6. **The secret victory** — combining Stone + Tablet + Abyssal Shimmer to defeat Death. Is the path discoverable but hard? Or trivial once you know it? Is the Tablet's drop rate / location consistent with its narrative weight?
7. **Quirk power** — ~80 quirks. Are any obviously dominant? Are any vestigial? Do they break key curves (e.g., a quirk that makes Death-chase trivial, a quirk that lets you skip the food economy)? The Power-quirk set (`philosophers_stone`, `atlas_burden`, `zeus_bolt`, `gorgon_ward`, `phoenix_rising`, `eye_storm`, `iron_will`, `battle_trance`, `second_sight`, `iron_ration`, `shadow_step`, `focused_scholar`) deserves close scrutiny.
8. **Stat scaling** — at floor 100 a player has typically X HP, Y SP, Z MP. Does damage scaling on monsters keep pace? Or does CON investment trivialize HP threat? Does INT make magic dominant over melee?
9. **Quiz timer × action frequency** — math 16s × constant combat vs. theology 46s × rare prayer. Is the timer budget appropriate given how often the action fires under pressure? If math feels survivable for a 5th grader on T1 but unsurvivable on T4, where does that wall fall and is it placed correctly?
10. **The status effects that don't tick** — `Monster.tick_effects` is known-broken (per `data/audit/consensus.json`). Assume it gets fixed: would the existing balance still hold, or does that fix introduce new imbalance (DOT-stacking monsters becoming murderous)?
11. **Permadeath × difficulty** — is the death curve such that most kids will reach floor 20–40 reliably, 60 with effort, 100 only with mastery? Or does the wall fall at the wrong place?

## Finding file schema
Filename: `tools/audit/findings/balance/<id>.md` where `<id>` is `balance-<short-kebab-slug>`.

```markdown
---
id: balance-<slug>
dimension: balance
severity: P1 | P2 | P3 | P4
title: <one-line>
status: open
systems: [<system1>, <system2>, ...]   # MUST be ≥2 for BALANCE
floors_affected: [<low>, <high>]
evidence:
  - balance_curves.json:<path-to-the-relevant-row>
  - <file>:<line>
discovered: 2026-05-15
---

## What's out of balance
<2–6 sentences, with numbers>

## Curve evidence
<reference the deliverable; show before/after, dominant strategy, dead band, etc.>

## Suggested re-tuning
<concrete numbers or design direction>

## Notes
<optional caveats — including whether this depends on a pending CODE fix>
```

## Severity guide (BALANCE-specific)
- **P1** — Breaks the difficulty contract: game beatable without learning above grade level; dominant strategy that trivializes Act II or Act III; dead band ≥10 floors; boss trivial with no setup; Death-chase ignorable.
- **P2** — Significant: dominant strategy across 5–10 floors; over/under-tuned item that materially shifts a major decision; quirk that makes a whole subsystem skippable.
- **P3** — Mild dip, niche imbalance, single-tier oddity.
- **P4** — Cosmetic value drift (a +1 vs +2 that doesn't materially matter).

## Hard rules
- Two of you are running this dimension in consensus. Do not coordinate.
- Every finding references rows in `balance_curves.json` and cites `file:line` for the source data.
- The deliverable comes *first*; then findings. Do not write findings without the curves built.
- Question banks are out of scope — but the **tier-difficulty assumption** (T1≈5th grade, T5≈HS) is in scope as a BALANCE input you reason about.
- Pacing of *play hours* is a FUN concern, not BALANCE. BALANCE owns *numerical progression*.
