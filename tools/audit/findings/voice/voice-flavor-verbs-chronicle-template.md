---
id: voice-flavor-verbs-chronicle-template
dimension: voice
severity: P4
title: Flavor-NPC chronicle entries use string templates that flatten distinctive NPC moments
status: open
systems: [game_encounters.py (_FLAVOR_VERBS, _NPC_VERBS), flavor_encounters.json (source material)]
evidence:
  - src/game_encounters.py:897-902 — "_FLAVOR_VERBS = ['Ran into {name}. A brief exchange in the dark.', 'Met {name}. Even down here, people find a way.', 'Crossed paths with {name}. The dungeon is stranger than I thought.']"
  - src/game_encounters.py:904-909 — "_NPC_VERBS = ['Met {name}. Had to make a hard choice.', 'Encountered {name}. Did what I thought was right.', ...]"
  - data/flavor_encounters.json:3500-3535 (The General Out of Time, 96-line encounter) — "He listens. His face does the complicated thing faces do when time catches up with them all at once..."
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

When the player resolves a flavor-encounter or NPC encounter, the chronicle entry is selected randomly from a small pool of generic templates:

- `_FLAVOR_VERBS` (3 entries): "Ran into {name}. A brief exchange in the dark.", "Met {name}. Even down here, people find a way.", "Crossed paths with {name}. The dungeon is stranger than I thought."
- `_NPC_VERBS` (5 entries): "Met {name}. Had to make a hard choice.", "Encountered {name}. Did what I thought was right.", etc.

The encounter the player just experienced may have been a 96-line emotionally devastating scene (The General Out of Time invents a battle, the Final Philosopher does something permanent to the architecture of your thinking, the Star Being touches your forehead). The chronicle line summarizing it: *"Met The General Out of Time. Did what I thought was right."*

This is a tonal mismatch by an order of magnitude. The encounter itself is in pitch-perfect chronicle/mythic voice. The chronicle summary line is template prose.

## Why it breaks the register

The chronicle is the player's *record* of what happened. Reading back through it should evoke the specific moments. The current templates can't do that — they're indistinguishable from one another. A player at end-of-run reading their chronicle sees 10 NPC encounters and they all collapse to "Did what I thought was right" / "Even down here, people find a way."

This is the same surface pattern as the trap chronicle ("Stepped on a {trap_type} trap. Should have watched...") — generic wrapper around a specific event.

## Suggested rewrite direction

Two options:

(a) Author per-encounter chronicle hooks. Each `flavor_encounters.json` entry could carry a `chronicle` field that's used in place of the template:
```json
{
  "tag": "flv_final_philosopher",
  "chronicle": "Met an old man who needed nothing. His words rearranged something in my head and I do not know if I can put it back."
}
```

(b) Keep the template fallback but author chronicle lines for the highest-impact encounters (Star Being, Final Philosopher, The General Out of Time, the Time-Lost Soldier).

Option (b) is the lower-cost first pass; option (a) would require touching ~90 JSON entries but produces the best end-of-run reading experience.

## Notes

This finding is about the *chronicle*, not the encounters themselves. The encounters are 5/5; the chronicle hooks into them at 2/5.
