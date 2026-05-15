---
id: code-identify-sight-pickup-no-quirk-notify
dimension: code
severity: P3
title: Identify-sight passive auto-identify on pickup does not notify quirk system
status: open
systems: [quirks, identification, philosophers_stone]
evidence:
  - src/main.py:2113-2115 — `if self.player.has_effect('identify_sight'): item.identified = True; self.player.known_item_ids.add(item.id)` — no `qs.on_item_identified(item.id)` call
  - src/game_magic.py:1989 — the philosophy-quiz identify path DOES call `_qs_id.on_item_identified(item.id)`
  - src/quirk_system.py:1014-1019 — `on_item_identified` is the only place `items_identified` is incremented (Mirror Mind quirk #87)
verified: true
discovered: 2026-05-15

---

## What's wrong

Once the player picks up the Philosopher's Stone, they gain the permanent `identify_sight` status effect (main.py:2161). After that, every item pickup at main.py:2113-2115 auto-identifies the item without calling the quirk system's `on_item_identified` hook.

`Mirror Mind` (#87 quirk power) requires 100 items identified in one run to unlock. The counter `items_identified` (quirk_system.py:1016) only increments in `on_item_identified`. So after the player acquires the Philosopher's Stone, every item they pick up adds to known_item_ids but does NOT advance Mirror Mind progress.

The philosophy-quiz identify path at game_magic.py:1989 correctly notifies the quirk system. The asymmetry is:
- Manual identify via philosophy quiz → counts toward Mirror Mind.
- Auto-identify via identify_sight (Stone passive) → does NOT count.

A player who reaches L100 and gets the Stone has just gained access to dozens of unidentified items still in play — but none of them now contribute to Mirror Mind progress.

## How to reproduce / where it fires

1. Play through to L100, pick up the Philosopher's Stone.
2. Walk back through the dungeon. Pick up any unidentified item.
3. Item is marked identified.
4. Check Quirks screen → Mirror Mind progress: unchanged.

## Suggested fix

```python
if self.player.has_effect('identify_sight'):
    # Only newly-identified items count for quirks (avoid double-counting if
    # the type was already known)
    if not item.identified:
        item.identified = True
        self.player.known_item_ids.add(item.id)
        qs = getattr(self, 'quirk_system', None)
        if qs:
            qs.on_item_identified(item.id)
    else:
        # already known type, but the specific instance's BUC may be hidden
        item.identified = True
```

The guard `if not item.identified` ensures the notify fires once per type, matching the philosophy-quiz path.

## Notes

P3 because the Stone is acquired late-game (L100) so few items remain to pick up before exit. But the Death-chase path back through 100 levels of saved-state monsters might surface dozens of unidentified items the player ignored earlier; this fix lets the auto-identify do its job for Mirror Mind too.

Consensus had an item flagged about main.py:2120 with on_item_identified() — they may have been looking at a now-shifted line number. The actual current bug is the absence of the call, not a zero-arg crash.
