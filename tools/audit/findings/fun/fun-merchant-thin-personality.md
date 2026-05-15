---
id: fun-merchant-thin-personality
dimension: fun
severity: P4
title: Procedural merchant is a flat shopkeeper — no haggling banter or named personality
status: open
systems: [merchants, npcs, shop_ui, chronicle]
when_it_hits: "Every merchant encounter (20% per floor) — frequent but forgettable"
evidence:
  - src/mystery_system.py:582-650
  - src/main.py:3820-3882
  - src/flavor_encounters.py:39-70
  - fun_pacing_trace.md#ambient-life-at-l10
discovered: 2026-05-15
---

## The friction or flatness
There are two merchant flavors in the game:

1. **Procedural shop merchant** (`mystery_system.py:582-650`): 20% per floor, stocks a random pool of items, opens a shop UI for buying.
2. **Flavor-encounter merchant** (`flavor_encounters.py:39-70`): the "Wandering Merchant" with named lines ("Business is slow this deep..."), a few trade options, and named-NPC weight.

The flavor-encounter merchant has *personality* — the dialog is well-pitched, the trade options have flavor. The procedural merchant is a *shop UI* with no personality. The player opens the shop with `y`, sees inventory, buys/sells, exits.

Compare: a flavor merchant fires roughly once every 10-15 floors (because each tag fires once per run). A procedural merchant fires roughly 1 in 5 floors (20%). **The forgettable one is far more frequent.**

Every player ends up viewing 8-15 procedural merchants per run as a shop UI, and 1-2 flavor merchants as actual conversations. The cumulative effect is that "merchant" reads as "menu" rather than "character."

This is *not* a P1/P2 finding — the system works. But the wonder budget for an encounter type that fires 8-15 times per run is *thin* given how rich the flavor-merchant template demonstrates is possible.

## When and how often it fires
- ~10-20 procedural merchant encounters per full run.
- The first few open the UI with curiosity. The next 10 are pure menu transactions.

## Suggested redirect
- **Procedural merchants get a randomized greeting line from a small pool** (10-20 lines, drawn from the flavor merchant register): "Anything you fancy?", "Word travels slow down here — bring news?", "I haven't seen another soul in days." Pure cosmetic, but raises the encounter from menu to scene.
- **One trade option that's a haggle**: each procedural shop has one item with a "negotiate price" interaction — economics quiz, knock 20% off if you pass. Adds a player-skill dimension to shopping.
- **Procedural merchants occasionally have a one-line story** seeded by floor depth: at L15 "I came down looking for my brother. He went deeper. I don't have the courage." Player can't follow up — it's just *texture*. But the merchant becomes a *person*.

## Notes
P4 because the system works and the cost-of-change is small relative to other findings. Spans the procedural merchant + flavor encounter pattern + chronicle integration. The point is: the **encounter type that fires most often** is the least textured. Inverting that — making the high-frequency encounters carry the same care as the rare ones — is a low-cost, high-leverage polish opportunity.
