# Legendary Uniques Proposal — Index

Three proposal docs covering all 303 uniques + 4 recommended new pieces. Authored 2026-05-18 from the design brief at `design_brief.md`.

| Doc | Items | Lines | Highlights |
|---|---|---|---|
| [weapons.md](weapons.md) | 96 | 1177 | Long chains, skyrocket curves, mythic peaks |
| [armor_shields.md](armor_shields.md) | 96 | 1530 | 20 tier-escalator pieces with named T5 abilities |
| [magic_accessories.md](magic_accessories.md) | 111 + 4 new | 1003 | Wild-magic tables, ritual escalators, quest artifacts |

---

## What "legendary" means here (the bar)

- **Power optional, flavor mandatory.** A weapon can be quirky-only with zero stat increase and still be legendary if the effect is iconic (Vidar's Sandal one-shots Fenrir but does nothing else; Lyre of Orpheus charms instead of damaging).
- **Rules are made to be broken for uniques.** Commons stay 5-cap clean. Uniques can have 10-chain skyrockets, dip curves, conditional damage tables, tier-escalator equip — anything that fits the lore.
- **Stay grounded.** Every mechanic ties back to the source material. No invented flavor without lore reason.

---

## Top highlights per section

### Weapons (full doc: weapons.md)

- **Mjolnir** — 10-chain steady ascent ending at 5.0×; chain-lightning to a second adjacent foe at chain 6+. The player feels the storm gather.
- **Sling of David** — skyrocket `[0.2, 0.5, 1.0, 2.5, 8.0]` against giants/over-leveled foes only. Picks fights it shouldn't win and wins them.
- **Sword of Michael** — 9-chain to 16.0× peak; at chain 7+, applies a **run-wide** -25% damage debuff to all demons. The Host has noticed.
- **Sword of Damocles** — dip curve `[1.0, 1.5, 0.3, 0.3, 4.0]` reflecting the falling thread; player intentionally plays the dip for the kill.
- **Tyrfing** — unsheath economy: first strike per equip is +50% damage but the wielder takes a curse stack until they kill 3 foes.
- **Stormbringer** — refuses to be unequipped while attuned; at low HP it strikes the wielder instead of the target.
- **Punch in the Face** — 1-entry chain, 1.0×, no proc. The legendary IS that it does nothing fancy.

### Armor & Shields (full doc: armor_shields.md)

- **Aegis of Athena** (tier-escalator) — T5 "Aura of Awe" makes monsters entering FOV save vs fear; failures lose their first turn.
- **Greater Aegis** (tier-escalator) — T5 "Gorgoneion" petrifies the first melee striker each floor.
- **Helm of Hades** (tier-escalator) — T5 "Unseen When Still" makes monsters lose target if you skip a turn.
- **Sandals of Hermes** (tier-escalator) — T5 "Psychopomp's Step" carries you one floor UP at death instead of dying. Once per game.
- **Crown of Brahma** (tier-escalator) — T5 360° FOV (four faces).
- **Armor of Ragnarök** (cursed tier-escalator) — T5 self-destructs on a chosen turn for massive AoE.
- **Green Knight's Plate** (tier-escalator) — T5 "Second Beheading Returns": when killed, head regrows next floor (full revive, once per run).
- **Spartan Aspis** — phalanx-adjacency: +2 AC per adjacent allied/pet square.
- **Pridwen** — Arthur's shield; reflects damage from any monster carrying a 'queen' or 'lady' tag at +100% (the Lady of the Lake's protection).

### Magic, Accessories & Artifacts (full doc: magic_accessories.md)

- **Seal of Solomon** (tier-escalator) — T5 Solomonic Key: bypass any lock, command undead/demon 1/floor.
- **Tyet of Isis** (tier-escalator) — T5 "Reassembly": death-save revives to full HP + regenerating. Once per run.
- **Kavacha and Kundala** — T5 "Cut and Given" is a VOLUNTARY SACRIFICE: surrender the armor for full HP + permanent CON +2 + karma. Only voluntary-sacrifice mechanic in the proposal.
- **Ring of Sir Gawain** — STR dip curve (peaks at noon, valleys at 3 o'clock) reflecting the Green Knight myth.
- **Pandora's Box** (NEW artifact) — single-shot 1d20 chaos table; 50/50 buffs and debuffs.
- **Wand of Wonder** (NEW wand) — chain mode where each rung rolls a FRESH escalating chaos table.
- **Necronomicon** (spellbook) — 6-chain with Klaatu-Verata-Nictu comedy backfire: miss the final word and summon a hostile.
- **Aladdin's Lamp** (NEW artifact) — 3-charge wish menu; each wish is a tier-5 theology quiz.
- **Picatrix** (spellbook) — 7-chain planetary cascade; each chain step casts in a different element (Mercury/Venus/Mars/Jupiter/Saturn/Sun/Moon).
- **Tablet of Destinies** — held passive shows next-floor spawn hint at floor descent.

---

## Engine work required

Deduplicated and split by complexity. These are the new combat.py / equip / floor-state hooks needed.

| Bucket | Weapons | Armor/Shields | Magic/Acc | Total |
|---|---|---|---|---|
| Simple (flag, reuse existing) | 13 | 28 | ~13 | ~54 |
| Moderate (new proc, modest code) | 57 | 42 | ~26 | ~125 |
| Complex (system-level work) | 17 | 6 | ~7 | ~30 |
| **Total** | **87** | **76** | **~46** | **~209** |

Significant **sharing** between weapons and armor/magic — the summon system, terrain procs, per-tag conditional bonuses, and tier-escalator infrastructure each serve many items. Realistic implementation is ~25-40 distinct engine systems, with most uniques being data-only after the engine is in place.

The **tier-escalator infrastructure** is the largest single piece of new code — quiz state machine for equip, per-tier bonus stacking, instance-stored achieved-tier, save/load support, UI for tier reveal. Once built, ~30 pieces across armor/accessories use it for free.

---

## Recommended new uniques (4 net adds)

| Item | Slot | Why add |
|---|---|---|
| Hand of Glory | amulet | Cursed-grimoire archetype is thin; this is the canonical entry |
| Pandora's Box | artifact | Brief explicitly calls it out; the chaos-table item |
| Aladdin's Lamp | artifact | Use-charged 3-wish ritual; theology tier-escalator demo |
| Wand of Wonder | wand | Brief explicitly calls it out; the wand-of-wild-magic |

---

## Suggested review path

The full proposal is ~3700 lines. Options:

1. **Read by section** in any order. Each doc is self-contained.
2. **Read the archetypes that excite you** — the section headers (God-Touched, Cursed, Quirky, etc.) let you skim to what you'd play.
3. **Triage by code complexity** — if you want to ship a smaller pass, the "complex" mechanics are listed and most can be cut without losing the legendary feel.
4. **Veto / lock items by name** — say "do not change X" or "must keep Y" and I'll honor it.

I'd recommend reading the highlights above first, then sampling sections in `weapons.md` (you've seen the most of those) before armor and magic.

---

## Open questions (would help to answer before implementation)

1. **Tier-escalator on FIRST equip only or every re-equip?** Proposal assumes first-equip stores the achieved tier; re-equip after unequipping uses the stored tier (no re-quiz). User can opt to re-attempt at higher tier via deliberate unequip → re-equip, accepting the risk.
2. **Voluntary-sacrifice mechanics** — Kavacha is the only one. Want more (Damocles's "trade armor for crit"? Excalibur's "cast me away" is a softer version)?
3. **Comedy backfires** (Necronomicon's "Klaatu Verata Nictu", Wand of Wonder's chaos) — appetite for a few more deliberately silly outcomes, or keep them rare?
4. **Quest items** (Sword of Michael, Penitent's Blade, Hunt Captain's Sword, etc.) — flavor edits proposed but their core mechanics are hand-set and preserved. OK to also tune their chains lightly, or hands-off?
5. **Implementation pacing** — phase by item type (weapons first, then armor, then magic), or phase by code complexity (build tier-escalator infra first, then port pieces)?
