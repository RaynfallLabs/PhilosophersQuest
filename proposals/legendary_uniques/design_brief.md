# Legendary Uniques Design Brief — 2026-05-18

## The Mandate

Commons follow templates. They are clean, predictable, capped at 5. Uniques are LEGENDARY — they break the rules. Each unique should make the player feel they have found the named item from myth, literature, or history.

**Power is optional. Flavor is mandatory.**

## What Uniques Can Do That Commons Cannot

- **Long chains** (8, 10, 15+ entries) — player chains a longer quiz for bigger reward
- **Skyrocket curves** (`[0.1, 0.1, 0.2, 0.5, 5.0]`) — terrible early, devastating finish
- **Dip curves** (`[1.0, 1.5, 0.3, 0.3, 4.0]`) — moments of vulnerability for thematic reasons (Damocles)
- **Quirky/flavor-only effects** — Glamdring glows near orcs, Bow of Apollo leaves sun-streak, Lyre of Orpheus charms instead of damaging
- **Tier-escalator equip** (armor/accessories) — bonuses scale with tier reached on equip-quiz
- **Per-monster-type triggers** — extra damage vs undead, fey, dragon, demon
- **Per-event procs** — on-kill heal, on-low-HP rage, on-floor-descent bonus
- **Failure modes** — curse if chain breaks at 1, debuff on drop, etc.

## Tier-Escalator Armor / Accessory Mechanic (NEW)

A unique armor / accessory with `"tier_escalator": true` uses escalator-tier equip:

1. Player attempts to equip → faces a Tier-1 quiz question (subject by slot: geography for armor, history for accessories)
2. Correct → gets Tier-1 bonuses, advances to Tier-2 question
3. Repeat through Tier-5 (each tier harder than the last)
4. First wrong answer ends the escalator
5. Player keeps the **highest tier reached** as the active bonus
6. Achieved tier stored on the item instance — re-equip does not re-quiz
7. Player can re-attempt at a higher tier later by **unequipping + re-equipping** (consuming a fresh quiz attempt) — but this risks losing the current tier if they fail

Tier-1 is always weakest, Tier-5 is the full legendary expression. Tier 5 unlocks the named ability (Aegis cone of awe, Robe of the Archmage's double-cast, etc.).

### JSON shape

```json
"aegis_of_athena": {
  ...
  "tier_escalator": true,
  "tier_bonuses": {
    "1": {"ac_bonus": 3},
    "2": {"ac_bonus": 4, "resistance": {"fear": 1}},
    "3": {"ac_bonus": 5, "resistance": {"fear": 2, "magic": 1}},
    "4": {"ac_bonus": 5, "resistance": {"fear": 2, "magic": 2}, "passive": "reflect_spell_10"},
    "5": {"ac_bonus": 6, "resistance": {"fear": 2, "magic": 2}, "passive": "reflect_spell_15_aura_of_awe"}
  }
}
```

Bonuses at each tier are CUMULATIVE-expressed (each tier's dict is the full set granted at that tier). Strictly improves with tier (no nerf-tiers).

## Power Guardrails

- **Damage peak**: non-mythic uniques cap at 3.0x mob_hp at peak_floor (test_no_super_weapon enforces this)
- **Mythic-tier** (god-touched: Excalibur, Mjolnir, Gungnir, Aegis): can reach 5x — these are exemptions
- **Long chains**: reward mastery. A 12-chain weapon at chain 8 should out-perform a 5-chain common at chain 5 — that's the point
- **Skyrocket weapons**: peak can be huge (5x+) ONLY if early chain values are sacrificially low (≤0.3)
- **Quirky-only**: zero power increase is fine if the effect is iconic (Sword of Damocles always crits or always misses on chain 1 — never both)

## Subject → Item-Type Quiz Mapping

(For tier-escalator and identify quizzes)

- Weapons: math (chain mode)
- Armor / shields: geography
- Accessories: history
- Wands / wand-instruments: science
- Scrolls / spellbooks: grammar
- Potions: cooking (or theology for divine ones)
- Artifacts: per item's lore — flexible

## Output Format

Each section author produces a markdown file at `proposals/legendary_uniques/{weapons|armor_shields|magic_accessories}.md`.

Use this entry shape per item (30-100 words):

```markdown
### Item Name

**Lore hook**: One sentence on what this is in myth.

**Mechanic**: New chain / new tier_bonuses / new procs. Be specific.

**Why legendary**: One line on the player's emotional payoff.

**Code needed**: (optional) List any new combat.py / equip hooks required.
```

Group entries by archetype, NOT alphabetically. Suggested groupings:
- God-Touched (Excalibur, Aegis, Mjolnir tier)
- Cursed / Ill-Omened (Tyrfing, Stormbringer, Mistilteinn)
- Royal / Inheritance (Anduril, Joyeuse, Curtana)
- Hero's Personal (Gae Bolg, Heracles' Club, David's Sling)
- Trickster / Wild (Stormbringer, Soul Reaver, Sword of Damocles)
- Quirky / Flavor-First (Lyre of Orpheus, Boomstick, Vidar's Sandal)
- Plain Elevated (good lore, clean treatment)

At the END of each doc add a section `## Code Required` listing every new mechanic that needs engine support, deduplicated, with notes on complexity.
