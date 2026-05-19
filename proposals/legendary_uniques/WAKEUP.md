# Wake-up summary — 2026-05-18 overnight push

Pushed to `RaynfallLabs/PhilosophersQuest` on `main` (HEAD `c3ebc2a`). All 388 tests pass. Audit subagent verified PASS before push.

## Triage items (the 4 from playtest)

All four fixed, committed in `933eec1`:

- **#76 ★/☆ glyphs** → ASCII `[*]/[ ]` for chain meters, `>>` `<<` for banners. Audited 5 sites in `game_render.py` + `main.py`.
- **#77 Philosophy timer** → bumped 40→50s. Audited other reading-heavy subjects: AI 40→45, history/animal 32→34, theology/economics 48→50. Math stays snappy.
- **#74 Monster AI** → audited. Perception 8/wander gating at `monster.py:587-599` is correctly wired (existing tests confirm). User-reported "they all charge me" is by design: default sight 5 (PER 10) vs monster perception 8 = monsters notice you first. Not a bug.
- **#75 Corpse identify** → full rebuild. Threshold → escalator-chain (philosophy), 5 progressive reveal tiers, 12 monster family masteries (dragon/demon/celestial/undead/fey/aberration/construct/elemental/beast/humanoid/plant/reptile). Plus fixed 31 monsters missing family tags (oozes, molds, fungi, plus blood_archon gained 'demon').

## Legendary uniques

**Proposals** (committed `5fb0044`, at `proposals/legendary_uniques/`):

- `design_brief.md` — rules of engagement
- `weapons.md` — 96 weapons in 9 archetype groups (god-touched, cursed, royal, hero's personal, trickster, bestial, quirky, quest, plain)
- `armor_shields.md` — 96 pieces; **15 chain-equip after lore-triage** (13 escalator + 2 chain mode), 5 reverted to flat passive with named procs
- `magic_accessories.md` — 111 items + 4 new uniques; **9 chain-equip accessories surviving triage**
- `README.md` — index + highlights

**Infrastructure** (committed `5dc1c36`, `c3ebc2a`):

- New `src/chain_equip.py` — apply/revert tier bonuses, subject defaulting, all bonus kinds
- New `equip_chain_mode` + `equip_chain_subject` + `tier_bonuses` JSON fields on Armor/Shield/Accessory
- `_start_chain_equip_quiz` in main.py — branches `_start_armor_quiz` and `_equip_accessory`
- `_unequip_slot` calls `revert_tier_bonuses` for round-trip cleanup
- 18 tests in `tests/test_chain_equip.py`
- Player gains `damage_resistances: dict[str, int]` and `regen_bonus: int` (audit fix)

**Data ports** (committed `4347f36`):

- 15 armor/shield pieces ported (Aegis, Greater Aegis, Helm of Hades, Morrigan, Odin, Aegishjalmr, Aragorn, Sigurd's Dragon Mail, Magus, Solomon, Smoking Mirror, Ragnarök, Green Knight, Hermes, Brahma)
- 9 accessories ported (Solomon's Seal, Tyet of Isis, Ahriman, Harmonia, Kavacha-Kundala, Gawain, Scheherazade, Atalanta, Idunn)
- 4 NEW uniques authored:
  - **Hand of Glory** (accessory.json) — cursed amulet, 3 paralyze charges then perma-cursed
  - **Pandora's Box** (artifact.json) — theology 3/4 gate, 1d20 chaos table, 50/50 buff/debuff
  - **Aladdin's Lamp** (artifact.json) — theology tier-5 4/5, ONE wish (item / power / entity), fallback table
  - **Wand of Wonder Legendary** (wand.json) — chain mode (science), 5 escalating tables (d6→d8→d10→d12→d20), ~70% positive bias

## Combat balance overhaul (earlier today)

Already committed before you went to bed: re-anchored weapon damage formula, 11 new materials, 22 class mechanics wired, 149 uniques rebuilt (12 signature + 53 archetype + 81 commons), 8 invariant tests. See memory `project_combat_rebuild_2026_05_18.md`.

## Play-test needed before claiming "done"

Per CLAUDE.md play-test rule, these are "easily reachable" and you should verify in-game:

- **Chain-equip armor**: try equipping Aegis of Athena or any of the 15 pieces — quiz fires, tier_bonuses apply at chain reached
- **Chain-equip accessories**: same for Solomon's Seal, Tyet of Isis, etc.
- **Corpse identify**: examine a corpse — escalator-chain fires, id_level advances, lore screen reveals progressively
- **Pandora's Box / Wand of Wonder / Aladdin's Lamp**: data is in place, BUT the chaos/wonder/wish DISPATCH code is not wired yet — these items will look right in inventory and tier-1 ID will reveal a name, but using them won't fire the effects. That's the next phase.
- **Philosophy timer**: feels less rushed at 50s base

## Known follow-ups (not blockers)

1. **T5 passive flags unwired** — ~60 `passive_<flag>` keys are stashed on items but use-site combat hooks aren't written yet. Aegis "Aura of Awe", Hermes "Psychopomp's Step", etc. need their effect handlers. Big future phase.
2. **Chaos/Wonder/Wish dispatchers** — Pandora, Wonder, Lamp tables are data-only. Engine needs effect dispatch for items.
3. **Family mastery use-sites** — `damage_vs_tag` and `tohit_vs_tag` are wired. `resist_charm`, `resist_elemental`, `sp_regen` aren't yet.
4. **Hand of Glory mechanics** — needs `paralyze_charges` activation + `passive_silent_walk` + `passive_dark_vision` + `expended_curse` hooks.

## Commits today

```
c3ebc2a fix(chain-equip): initialize damage_resistances + regen_bonus on Player
5fb0044 docs(proposals): legendary uniques design pass
4347f36 feat(uniques): chain-equip data for 24 pieces + 4 new uniques
a14f590 feat(corpse-id): escalator-chain corpse identify + per-family mastery
5dc1c36 feat(chain-equip): infrastructure for legendary unique tier-escalator equip
933eec1 fix(playtest): ASCII glyphs + philosophy timer +10s + audit-bumps
276334a test(combat): chain gradient + no-super-weapon invariants
04ff1e3 feat(uniques): custom-author thematic chains for 53 long-chain uniques
01e1374 feat(uniques): rebuild 81 unique baseDamage + 12 signature chains
57650cf feat(combat): wire 6 previously-unimplemented class mechanics
5abb081 feat(materials): 11 new weapon materials + magical-conductor framework
c215e9d feat(combat): re-anchor weapon damage formula on chain-5 = trash kill
```

12 commits. 388 tests. Sleep well.
