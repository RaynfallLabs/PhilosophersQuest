---
id: voice-cow-level-no-lore
dimension: voice
severity: P4
title: Cow level is a fully secret NetHack reference; no T2-T3 hint gestures at "things that happen when adventurers push their luck"
status: open
systems: [data/hints.json, game_encounters.py (cow level entry), boss_levels.py (COW_LEVEL)]
evidence:
  - data/hints.json (all tiers, full read) — no entries reference cows, bovine portals, or trespass-against-livestock consequences
  - src/game_encounters.py:89-90 — "self.add_message('MOO MOO MOO MOO MOO!', 'danger')" / "_log_chronicle('I poked a cow too many times. The floor opened up. Now I'm in some kind of... cow dimension. This is not in any lore I've read.')"
  - The chronicle line itself ("This is not in any lore I've read.") explicitly self-references the gap
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The cow level is a fully secret NetHack-tradition easter egg. The trigger requires the player to attack a cow some N number of times until the floor opens. The chronicle entry on triggering it is genuinely funny ("...cow dimension. This is not in any lore I've read.") — but the parenthetical self-references the absence of lore coverage *as a feature*, which is one reading of intent.

The question for this finding: should the lore *gesture* at it (T2-T3), or is it intentionally a 100%-secret easter egg with no hint?

There's a case for either. The XYZZY equivalent in the same game has *three* hint entries across T2-T5 (the "hidden inputs" T1 hint, the "secret word deep underground" T3 hint, the "First Magic Word" T5 hint). The XYZZY system is the most-covered hidden mechanic in `data/hints.json` — three tiers of escalating reveal — and it's also a NetHack reference.

By contrast, the cow level has zero coverage, which makes it the *least*-hinted hidden mechanic in the game. The chronicle line that fires on discovery is the only in-game text that even acknowledges the system exists.

## Why it breaks the register

This is borderline — the geek-dad register tolerates fully-secret jokes. But the asymmetry with XYZZY is notable: both are NetHack references, both reward exploration; one is fully veiled-and-tiered in the lore corpus, the other is completely absent.

## Suggested rewrite direction

If the intent is for the cow level to remain 100% silent in lore: leave it alone, and consider this finding closed-as-intended.

If the intent is to gesture at it the way XYZZY is gestured at: add one T2 hint:

> *"Some of the dungeon's residents are not enemies. The old adventurers warned: if you find an animal that wants only to be left alone, leave it alone. There are consequences to not doing so."*

That covers cows specifically, the Magic Carrot unicorn (also peace-affordance), and any future peaceful-creatures-with-consequences mechanics.

## Notes

P4 — interpretive call. Flagged for the auditor's record. Either resolution is defensible.
