---
id: balance-dead-band-71-80
dimension: balance
severity: P1
title: 10-floor dead band F71-F80 — no new equipment in any slot
status: open
systems: [weapons, armor, shields, accessories, dungeon_progression]
floors_affected: [71, 80]
evidence:
  - balance_curves_agent_a.json:weapons_by_min_level (no min_level 71-80 entries between Tyrfing at L70 and adamantine at L81)
  - balance_curves_agent_a.json:armor_by_min_level (no min_level 71-80 entries; L70 Panoply of Hephaestus then L81 dragonscale)
  - balance_curves_agent_a.json:shields_by_min_level (only obsidian_shield at L71 +3, otherwise gap to L81)
  - balance_curves_agent_a.json:accessories_by_min_level (only L70 Heart of Ahriman/Amulet of Merlin, then jump to L999/L9999 uniques)
  - data/items/weapon.json (min_level=70 Tyrfing; next generic tier=81 adamantine)
  - data/items/armor.json (L70 Panoply, L81 dragonscale)
discovered: 2026-05-15
---

## What's out of balance

Floors 71-80 introduce ZERO new generic equipment in any slot. The full upgrade-floor histogram across weapons + armor + shields + accessories is `[..., 70, 71, 81, ...]` — a 10-floor stretch where the only floor with a new item is F71 obsidian_shield (+3 AC, same AC as the L51 mithril shield from 20 floors prior). All other gains are unique L9999-only artifacts placed by code. By contrast every other 10-floor stretch from F1-F70 introduces multiple new tiers (L21, L41, L61 generic staircase; L11/L25/L45/L65 accessory waves; L22/L28/L40/L60 unique waves).

This is the worst dead band in the game and falls directly **before** the Abaddon push at F80-100. Players reach F70, fully gear up, then climb 10 floors against monster HP ramping from ~835 (L70) to ~1000+ (L80) with no power-budget upgrade. Monster damage in this band averages 3d8-5d10+ per hit (locust_count, Wild Hunt Captain 3d10+16). Combined with the fact that L70-100 mini-bosses all share thac0 -16 (so DEX/AC investment is capped for hit-avoidance), the band feels like a treadmill.

## Curve evidence

- `weapons_by_min_level` rows show: L65 (11 uniques), L70 (3 uniques: Tyrfing/Amenonuhoko/Longinus), then NOTHING until L81 (22 generic adamantine tier + 4 uniques)
- `armor_by_min_level` rows show: L70 (1: Panoply of Hephaestus +9 AC unique), then NOTHING until L81 (12 dragonscale tier)
- Pool size of normal monsters drops from 32 at F70 to 23 at F80 (deliverable `monsters_by_floor[69].pool_size_normal` = 32, `[79]` = 23) — variety also shrinks alongside missing gear
- Compare to F61-F70: 22 generic diamond weapons + 11 unique L65 weapons + 3 L70 uniques = 36 new weapon introductions across 10 floors
- F71-F80: 0 generic, 0 unique = 0 new introductions across 10 floors

## Suggested re-tuning

Either (a) add a generic intermediate tier at L71 (e.g. mithril or starmetal weapons baseDmg ~13-14, AC +2-3 armor) to bridge diamond and adamantine; or (b) push back the adamantine min_level from 81 to 71 and let it be the F71-100 endgame tier with rarer drop weights at the front; or (c) add a unique-artifact wave at L75 that gives a meaningful sidegrade (e.g. an L75 ring tier between Heart of Ahriman L70 and Sphinx's Crown L9999).

The mid-tier accessories also need attention: between L70 (Heart of Ahriman, Amulet of Merlin) and the L999/L9999 unique artifacts there's no ring/amulet introduction at all. A single L75 amulet wave (4-6 items at e.g. +3-4 stat) would patch this.

## Notes

The boss-level cadence (20/40/60/80/100) makes a F80 mini-boss/area boss arrive at exactly the worst gear-curve moment. Players who don't already have full L61 diamond + L65 unique loadout by F71 will struggle to cross F80 Fenrir (HP 3000, thac0 -16, 5d10+9 devouring bite). This is *too hard in the wrong place* — not the genre-appropriate Abaddon wall at F100, but an artificial wall at F80 made worse by missing gear.
