---
id: beauty-missing-secret-sprites
dimension: beauty
severity: P2
title: Most secret-build player sprites are missing — silent fallback to default player.png
status: open
systems: [welcome_screen, dungeon_view, renderer]
evidence:
  - src/welcome_screen.py:34-255 — `SECRET_BUILDS` references `_sprite` for 26 characters
  - src/renderer.py:249-259 — `draw_player` calls `_get_env_sprite(sprite_name) or _get_env_sprite('player')`
  - src/game_render.py:1053-1054 — `_pspr = (self.secret_build or {}).get('_sprite', 'player')` passed to `draw_player`
  - assets/tiles/env/ listing — only `player.png`, `player_ash_ketchum.png`, `player_ash_williams.png`, `player_ciri.png`, `player_geralt.png`, `player_wizard_f.png` exist
  - beauty_screen_catalog.md#2
  - beauty_screen_catalog.md#5
discovered: 2026-05-15
---

## The visual clash or inconsistency

The Welcome screen advertises 26+ "secret build" identities — Aristotle, Socrates, Plato, Nietzsche, Pythagoras, Prometheus, Diogenes, Achilles, Leonidas, Alexander, Theseus, Hermes, Odysseus, Merlin, Corwin, Cain, Fianna, Fluffs, Dad, Robyn, Titivillus — each with a distinct `_sprite` key in `SECRET_BUILDS`. Picking one of these names is a visible meta-discovery for the player (the "[*] SECRET BUILD ACTIVE!" badge confirms it).

Out of the 26+ referenced sprite names, only **5** corresponding `.png` files exist in `assets/tiles/env/`:
- `player_ash_ketchum.png`
- `player_ash_williams.png`
- `player_ciri.png`
- `player_geralt.png`
- `player_wizard_f.png` (shared by Fianna and Fluffs)

**Missing:** `player_aristotle`, `player_socrates`, `player_plato`, `player_nietzsche`, `player_pythagoras`, `player_prometheus`, `player_diogenes`, `player_achilles`, `player_leonidas`, `player_alexander`, `player_theseus`, `player_hermes`, `player_odysseus`, `player_merlin`, `player_ranger` (referenced by Corwin and Cain), `player_dad` (referenced by Dad and Titivillus), `player_robyn`.

In `renderer.py:253`, the `_get_env_sprite(sprite_name) or _get_env_sprite('player')` pattern silently falls back to the default sprite if the named one is missing. **The player picks Aristotle and sees the default character on screen.** The secret-build feature is partially decorative — the *stats* change but the *visual identity* does not.

## Where it surfaces

- **Dungeon view** (the entire main play screen): every secret build except 5 displays as the generic player sprite. The "I am playing Aristotle" experience is purely stat-line; the on-screen character looks identical to a default-name run.
- **Welcome screen**: the "[*] SECRET BUILD ACTIVE!" badge promises a unique character. The promise is half-broken.
- **Identity discovery loop**: a player who figures out one of the secret names should be visually rewarded. Currently they're rewarded only by stats and a single greeting line.

## Suggested unification

Two options, both legitimate:

**Option A — Ship the missing sprites.** Generate or commission the 16 missing portraits. Their style needs to match the existing five (which appear to be in a unified pixel-art tile style based on the file naming and asset-tile-size architecture).

**Option B — Prune the build list.** Remove `_sprite` overrides from builds without art, or pare `SECRET_BUILDS` to only the five characters with art. Less ambitious but immediately closes the gap.

**Recommended:** Option A for the Great Philosophers (Aristotle, Socrates, Plato, Pythagoras, Nietzsche, Diogenes, Prometheus) — they're the highest-resonance picks for the game's audience and the most likely first-discoveries. The Warriors/Rogues/etc. can use shared archetype sprites (`player_warrior`, `player_rogue`, `player_mage`) as a compromise.

## Notes

This is P2 (not P1) because:
- The fallback is graceful (no crash, no broken pixels — just the default sprite).
- A player who never discovers a secret name never notices the gap.

But for the audience who *does* discover Aristotle or Achilles — the game's most engaged players, the kids' father/uncle types — this is the moment the visual identity should crystallize, and it doesn't.

Asset work, not code work. The infrastructure to use the sprites already exists.
