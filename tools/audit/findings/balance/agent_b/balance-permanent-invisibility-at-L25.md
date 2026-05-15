---
id: balance-permanent-invisibility-at-L25
dimension: balance
severity: P2
title: Permanent-status rings at L25 (invisible, hasted, displacement, magic_resist, levitating) trivialize most floor 25-80 monster threats
status: open
systems: [accessories, status_effects, monsters_to_hit]
floors_affected: [25, 80]
evidence:
  - balance_curves_agent_b.json:accessories_by_min_level (30+ accessories at min_level 25)
  - data/items/accessory.json (ring_invisible, ring_hasted, ring_displace, ring_magic_res, amulet_invis, etc.)
  - src/monster.py:295-298 (displacement = 30% monster miss)
  - src/player.py:259 (invisible_bonus -2 AC)
discovered: 2026-05-15
---

## What's out of balance

The accessory pool at min_level 25 (`balance_curves_agent_b.json :: accessories_by_min_level`) includes:
- `ring_invisible` (status: invisible, duration: -1) — permanent invisibility
- `amulet_invis` (status: invisible, duration: -1)
- `ring_hasted` (permanent haste — move twice per turn)
- `amulet_hasted`
- `ring_displace` / `amulet_displace` (30% monster miss rate)
- `ring_magic_res` / `amulet_magic_res` (magic resistance permanent)
- `ring_levitate` / `amulet_levitate` (immune to floor traps)
- `ring_clairvoy` / `amulet_clairvoyant` (sees whole map)

These are PERMANENT status effects from a SINGLE ring slot. The player has 4 accessory slots + 1 amulet slot. A player who reaches L25 (the second act starts at L21) and finds 4 rings + an amulet from the permanent-status pool can equip:

- Invisible permanent → most enemies need `aggravated` or adjacency to notice you (`monster.py:441`)
- Hasted permanent → 2x movement and quiz timer (`player.py:310-311`)
- Displacement permanent → 30% miss on every incoming attack
- Magic Resist permanent → most magic damage cut
- Levitating permanent → no traps

This combo is reachable somewhere in floors 25-40 with reasonable luck (30+ permanent-status accessories at L25 means the pool is *crowded* with these). Once equipped, monsters at L40-L80 (Medusa floors, Dragon floors) can barely connect.

Compare to NetHack lineage: NetHack's ring of invisibility is uncommon, and `wand of digging` exists to balance ambush — PQ has no such wand on the offensive side that I can find.

## Curve evidence

`balance_curves_agent_b.json :: accessories_by_min_level` filtered to `status` non-null with `slot=ring|amulet` shows the cluster at min_level 25. Compare to L1 starting pool which is mostly stat-+1 rings (`ring_strength_iron` etc.). The progression is:

| min_level | accessories | notable |
|---|---|---|
| 1 | 36 | mostly +1/+2 stat rings, warning rings |
| 8 | 49 | mid-tier stat (+2/+3 mixed) |
| 25 | 30 | permanent-status spike (invisibility, haste, etc.) |
| 45 | 11 | greater-status (eg. greater rings) |
| 65 | 15 | divine-tier |

The L25 spike is unusual — it's the act-2 entry — and the *quality* of effects there (permanent invisibility for a non-quest item) is anomalously high for a 25-floor checkpoint.

## Suggested re-tuning

1. **Permanent → temporary at lower tier**: ring_invisible at L25 grants `invisible 30 turns` per equip-cycle, not `-1`. The greater amulet at L45-L65 gets permanent. Distinguishes mid-game gear from end-game gear.
2. **Curse-on-equip risk**: permanent-status rings have a 50% chance of being cursed at L25 (welded on, prevents swap). Player commits to one effect.
3. **Stack limit**: only ONE permanent-status accessory may be equipped at a time. Hardcoded slot rule rather than soft economy.

Option (1) is the cleanest curve fix.

## Notes

- Cross-system: accessories + status_effects + monster_to_hit (invisibility affects detection range at `monster.py:436-449`).
- Some of these effects DON'T affect bosses meaningfully (Medusa's gaze ignores invisibility per `monster.py:200-211`; Fenrir's smell-based AI may bypass invisibility — unverified, speculation). So the impact is *most acute* on regular L25-L80 monster ecology. Boss fights still bite.
- Single-system would be "ring_invisible too powerful." Holistic is "the L25 act-2 entry pool gives away end-game-quality permanent effects."
- This finding compounds `balance-AC-runaway-deep-monsters-cannot-hit.md` — invisibility + AC -33 = total invincibility against regular monsters.
