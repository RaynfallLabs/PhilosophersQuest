---
id: code-chronicle-first-flags-not-saved
dimension: code
severity: P3
title: `_chronicle_first_*` flags not persisted; first-time chronicle entries re-fire after save/load
status: open
systems: [save_load, chronicle]
evidence:
  - src/save_system.py:22-78 — `save_game` writes a state dict; no `_chronicle_first_*` or `_chronicle_room_*` or `_chronicle_abaddon_start` keys
  - src/main.py:276-365 — `load_state` does not restore them either
  - 12 distinct first-time chronicle flags exist:
    - src/game_combat.py:1152 `_chronicle_first_pit`
    - src/game_combat.py:1252 `_chronicle_abaddon_start`
    - src/game_divine.py:98 `_chronicle_first_mystery`
    - src/game_divine.py:313 `_chronicle_first_fountain`
    - src/game_divine.py:553 `_chronicle_first_grave`
    - src/game_divine.py:624 `_chronicle_first_throne`
    - src/game_divine.py:732 `_chronicle_first_prayer`
    - src/main.py:1140 `_chronicle_room_<rtype>` (one per room type, dynamic attr name)
    - src/main.py:1813 `_chronicle_first_trap`
    - src/main.py:1957 `_chronicle_first_disarm`
    - src/main.py:2385 `_chronicle_first_compound`
    - src/main.py:2555 `_chronicle_first_xyzzy`
verified: true
discovered: 2026-05-15

---

## What's wrong

Twelve "first time X" chronicle gates use ad-hoc `getattr(self, '_chronicle_first_xxx', False)` flags that are set on the Game object at runtime. None of them are persisted in `save_game` or restored in `load_state`. On load, all flags reset to False (via the default in `getattr`).

Consequence: after save/load, the next time the player triggers any of these events, the first-time chronicle line fires again, polluting the chronicle journal with duplicates:

- "Found a strange altar. {name}. The inscription dared me to approach." — fires again after load.
- "Abaddon. The Destroyer. He's real. He's here. This is it." — fires again if player saves & loads on L100, then engages Abaddon again.
- "Dug a pit with the shovel. Took everything I had. If something walks over this..." — fires on second dig.
- Room-discovery chronicle lines (graveyard, zoo, etc.) re-fire on revisit if the player previously visited that special room, saved, loaded.

The chronicle is meant to be a permanent narrative spine. Duplicate entries break the diary voice and are visible in the encyclopedia.

## How to reproduce / where it fires

1. Find a fountain. Interact. Chronicle entry "I found a fountain. The water glistens..." fires.
2. Save & quit.
3. Reload. `_chronicle_first_fountain` defaults to False.
4. Walk to any (same or different) fountain. Interact. The "first fountain" chronicle entry fires again.
5. Encyclopedia → Chronicle tab now shows the entry twice.

## Suggested fix

Two options.

**Option A** (minimal, preserves attr-style flags): add an explicit list of these flags to `save_game` and `load_state`. Painful — 12 names, fragile to forgetting one when a new flag is added.

**Option B** (recommended): replace the 12 ad-hoc attrs with a single set `self._chronicle_firsts: set[str]`. Each call site becomes:

```python
if 'first_pit' not in self._chronicle_firsts:
    self._chronicle_firsts.add('first_pit')
    self._log_chronicle(...)
```

Then save/load just round-trips one set. Same pattern as `_recalled_hints`, `_lore_placed`, etc.

For the dynamic `_chronicle_room_<rtype>` names at main.py:1140-1142, change to `f'room_{rtype}'` keys in the same set.

## Notes

P3 because no crash; the bug is "narrative polish" damage to the chronicle UI. Detected via grep for `_chronicle_first_` cross-referenced against save/load.
