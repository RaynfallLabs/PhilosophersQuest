---
id: voice-mystery-reward-text-stat-leak
dimension: voice
severity: P3
title: Mystery reward_text strings carry mechanical stat callouts inline with mythic flavor
status: open
systems: [mystery_system.py (MYSTERIES dict), game_render.py (loot panel)]
evidence:
  - src/mystery_system.py:27 (Sphinx) — "'reward_text': 'The Sphinx crumbles. Ancient wisdom floods your mind. WIS+2, INT+1.'"
  - src/mystery_system.py:56 (Grail) — "'reward_text': 'You are found worthy. Max HP+30, CON+2.'"
  - src/mystery_system.py:99 (Mjolnir) — "'reward_text': 'The dwarves\\' work is complete. Mjolnir reforged (+4 enchant). STR+2.'"
  - src/mystery_system.py:155 (Fisher King) — "'reward_text': 'The king heals. He blesses you: Max HP+30, prayer cooldown halved forever.'"
  - src/mystery_system.py:169 (Sisyphus) — "'reward_text': 'The boulder vanishes. Your body is transformed by the effort. STR+3, INT+1.'"
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

Each mystery altar's `reward_text` mixes two registers in the same sentence:
- Mythic: "The Sphinx crumbles. Ancient wisdom floods your mind."
- Statblock: "WIS+2, INT+1."

The format `mythic. statblock.` repeats across all 13 mysteries. The mythic half is doing the work — describing the moment, the feeling, the transformation. The statblock half is a UI confirmation appended to lore prose.

This is a register clash *within a single string*. The reward panel already displays stat changes elsewhere (sidebar updates). The reward_text doesn't need to carry the mechanical recap.

## Why it breaks the register

The dungeon_entrance popup, the boss popups, the exit_with_stone popup — none of them include statblock callouts in the prose. They describe the moment fully and let the mechanical effects land separately. Mystery rewards are tonally adjacent (rare, climactic, mythic-themed events) and should follow the same pattern.

The current format reads like a JIRA ticket: *here's what happened* (lore) | *here's the spec change* (stats). One panel away, the chronicle entry will record this in pure voice. Two writers again.

## Suggested rewrite direction

Strip the stat suffix from each reward_text. The stat changes are still displayed mechanically; the reward_text just stops competing with them.

- Sphinx: *"The Sphinx crumbles. Ancient wisdom floods your mind."*
- Grail: *"You are found worthy."*
- Mjolnir: *"The dwarves' work is complete. Mjolnir is reforged, whole at last."*
- Sisyphus: *"The boulder vanishes. Your body is transformed by the effort."*
- Fisher King: *"The king heals. He blesses you: a king's gratitude is not nothing."*

The mechanical effects can be a separate add_message in the next line, formatted plainly.

## Notes

13 strings to tune. Each fires once per mystery completion (rare per run). Modest impact individually, cumulative impact through the run.
