---
id: voice-power-quirks-no-lore-coverage
dimension: voice
severity: P2
title: Power quirks (zeus_bolt, atlas_burden, phoenix_rising, etc.) have no hint coverage at any tier
status: open
systems: [data/hints.json, quirk_system.py (_ACTIVE_POWER_DEFS)]
evidence:
  - data/hints.json (all 5 tiers, full read) — no entries reference "power" mechanics, named power quirks, or active-cooldown abilities by concept
  - src/quirk_system.py:1332-1364 — _QUIRK_TRIGGER block: philosophers_stone, atlas_burden, zeus_bolt, gorgon_ward, phoenix_rising, eye_storm, iron_will, battle_trance, second_sight, iron_ration, shadow_step, focused_scholar, arcane_surge, death_wish, wandering_star, time_dilation, mirror_mind, metabolic, venom_lore, war_cry, mind_fortress, temporal_shield, ancestral_q, mystic_eye, life_drain, reality_anchor, runic_armor, astral_form, sage_counsel, ouroboros — none referenced in hints.json
  - CONTEXT.md §4 — "Power quirks: philosophers_stone, atlas_burden, zeus_bolt, gorgon_ward, phoenix_rising, eye_storm, iron_will, battle_trance, second_sight, iron_ration, shadow_step, focused_scholar"
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The game ships with ~30 active-power quirks — distinct from passive trait quirks in that the player must invoke them (cooldown-gated). Examples: Zeus Bolt, Atlas Burden, Phoenix Rising, Eye of the Storm, Shadow Step. These represent significant strategic depth — they reward specific play patterns and give late-game characters distinct identities.

`data/hints.json` (108 entries across 5 tiers) has zero coverage of this category. The player can experience a 100-floor run, unlock several power-quirks, and never read a single in-game lore entry that gestures at the existence of "powers" as a class — let alone hints at how to find specific ones.

Recall Lore is the game's discovery vehicle (CONTEXT.md §5). The whole point of the trivia → tiered hint loop is that the player is rewarded with mythic gestures toward what's possible. A player who has unlocked Zeus Bolt and is dying to know how it differs from the bolt-themed wand they're carrying has nowhere to go for in-fiction context.

## Why it breaks the register

This is a coverage gap, not a register violation per se — but it matters because the hint corpus is otherwise dense and well-tiered. The absence is conspicuous: T4 hints mention dozens of named heroes' techniques as gestures toward quirk triggers (Sigurd's belly-strike → fafnir killcue, Penelope's weaving → equip/unequip armor); T5 hints describe major late-game items (Murugan's lance, the Monkey King's staff). But the entire active-power category is missing.

Compare to how *passive* quirks are referenced: the T4 entry *"Asclepius learned the art of healing from serpents. Those who harvest widely from venomous creatures may discover his secret recipe."* gestures at the asclepius quirk's trigger condition. The pattern exists; it just hasn't been applied to powers.

## Suggested rewrite direction

Add ~6–12 entries to `data/hints.json` covering the power-quirk class. Distribute across tiers:
- **T3:** Generic gesture that some who endure unusual conditions are gifted with on-call abilities. ("Some who have suffered the right things long enough find they can call upon what wounded them.")
- **T4:** Named gestures for specific powers — Atlas, Zeus, Phoenix, etc. ("Atlas carried the world. Those who carry weight long enough learn that the weight changes them in ways that can be called upon.")
- **T5:** Reveals for the rarer powers like Eye of Storm, Shadow Step. ("Five floors untouched by harm is not luck. It is a kind of stillness the world recognizes — and after the fifth, it offers something.")

This closes the gap without spoiling any specific trigger numbers.

## Notes

This is the largest single coverage gap in `data/hints.json`. The active-power quirk system is significant strategic depth that the discovery vehicle doesn't acknowledge.
