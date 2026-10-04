# Monster and Item Content Pass (2026-10-04)

Scope: all 527 monsters and every weapon, armor piece, shield, accessory,
artifact, wand, scroll, spellbook, potion and food, plus the template and
material text that composes common gear.

Four local commits on `main` (not pushed): `c77f657`, `cefb6ba`, `01370c8`,
`f31d379`. Test suite: 1,870 passed, 29 skipped.

**Nothing here has been play-tested.** The spawn change alters difficulty on
every floor past about 8, so it needs your hands on it before it ships. See
"What to play-test" at the bottom.

---

## 1. The big finding: monsters were spawning 10 to 15 floors too deep

The v2.14 HP rebase scaled each monster's HP to the balance-curve target for
its `min_level`. But monsters do not spawn at `min_level`; they spawn on a bell
curve around `peak_floor`, which sat 6 to 12 floors deeper with a very wide
spread. So the monsters you actually met had a fraction of the intended HP:

| Floor | Target median HP | Before | After |
|---|---|---|---|
| 10 | 21 | 9 | 16 |
| 20 | 55 | 12 | 33 |
| 30 | 110 | 21 | ~110 |
| 40 | 210 | 68 | 188 |
| 60 | 500 | 242 | 486 |
| 80 | 1,100 | 500 | 1,150 |
| 90 | 1,400 | 887 | ~1,200 |

A typical floor-20 weapon deals about 11 at chain 1, and the median floor-20
monster had 12 HP, so on floors 8 to 35 almost everything died to a one- or
two-answer chain and combos did not matter. A giant rat was still in the spawn
pool on floor 35.

**Fix (moves the RNG, not the stats):** `tools/balance/respawn_by_hp.py` sets
each random spawn's peak to the floor whose target HP matches the monster's own
HP, tightens the spread, and starts it a few floors before its peak. HP, damage
and THAC0 are untouched for 460 of the 479 random spawns. Median HP per floor
is now 0.6x to 1.07x of target on all 100 floors. `tests/test_spawn_curve.py`
guards it.

Other spawn RNG fixed in the same pass:

- **One-shot spikes early.** An air elemental (19 damage) could appear on
  floor 4, a stone giant on floor 10, a young red dragon on floor 12, where the
  median hit was 1.5. Nothing can now first appear on a floor where its hardest
  attack is over 5x that floor's normal damage.
- **Several Tiamats on one floor.** Tiamat, Surtur, Asmodeus, Ymir's Last Spawn
  and Hrungnir's Ghost were in the random pool at high weight on floors 80 to
  93. They are now placed at most once per run (each rolls 50% independently,
  never on a boss or seal-demon floor). The Iron Patriarch, Whispering Crone
  and Blood Archon join the normal mini-boss slots. The "5 to 7 mini-bosses a
  run" target is unchanged; the legends are on top of it (about 2.5 a run).

## 2. Stats changed because the lore said so

These are the only stat changes. Each was a case where the stats contradicted
the creature's own lore or its own damage.

- **Giants** had the HP of floor-15 monsters but hit like floor-70 ones. Now a
  real ladder: stone 160, frost 185, fire 210, cloud 250, storm 300 (under the
  giant kings at 344 and the elder storm giant at 546). The cloud giant's
  morningstar no longer hits for 2d4+1.
- **Air and water elementals** brought level with fire and earth (150 HP).
- **Mini-bosses and seal demons** were weaker than the ordinary monsters beside
  them (seal demons 370 to 520 HP on floors where common monsters have 1,100;
  Arachne had 7 HP). All raised to at least 2x the floor target. Fenrir was the
  one gate boss the rebase had capped (1.3x); now 2.2x (1,444 to 2,420).
- **Eleven deep monsters** left at a quarter of their band (apocalypse herald,
  wormwood blight, iron horseman, void seraph and others) brought up.
- **Master weaker than servant:** vampire vs vampire spawn, werewolf alpha vs
  werewolf. Flesh golem and zombie hulk were rat-weight.
- **Young red dragon** out-hit the adult red dragon; its breath (not its claw)
  is now the big attack, and smaller than the adult's.
- **Cath Palug** 21 to 32 HP.

The full list with before and after values prints from
`python tools/balance/respawn_by_hp.py` and is in the tool's constants.

## 3. Monster lore, resistances, tags, attacks

- **Lore:** 493 of 527 rewritten, 40 to 80 words (bosses up to 100). Named
  monsters carry a true detail from the source. Corrected errors include
  chimera anatomy, the Cyclopes' parentage, Cath Palug, Cacus, Ravana, Tiamat,
  Surtur's sword, and where Hrungnir fought Thor.
- **Resistances and weaknesses:** skeletons resist pierce and are weak to blunt
  (several had it backwards), lycanthropes are weak to silver, fey to iron,
  oozes resist acid. Lists trimmed to four. Resist-all-physical kept only on
  incorporeal things. Fafnir is weak to pierce (Sigurd's thrust from below).
- **Tags:** giants, trolls, goblins, orcs, kobolds, gnolls now carry the tags
  weapon banes look for. The classic giants were tagged only `humanoid`, so
  giant-slaying weapons did nothing to them.
- **Attacks:** names are proper labels; 65 type or effect fixes. The combat log
  lowercases them mid-sentence, per your rule.

## 4. Items

- **Lore:** about 690 entries rewritten. Wand, scroll and spellbook lore was
  mostly one terse rules sentence; now 46 to 82 words each. Invented citations
  removed ("Tesla's diary", a fake 1947 paper, fake inscriptions).
- **Appearances:** about 190 unidentified names changed. No two wands, scrolls,
  tomes or potions share a look, and looks no longer give the effect away
  ("sunlit scroll" for a light scroll). Fifteen legendary weapons were
  literally "a sword" or "a spear".
- **Armor resistances were backwards.** The engine multiplies damage by the
  stored number, but 75 entries were written as "fraction resisted". A floor-18
  shield removed 85% of pierce damage; the "immune" shields did nothing. All
  converted.
- **Powers that were authored but dead:** Sword of Michael's demon / undead /
  evil bonus, Theseus's Club's humanoid bonus, the ring of the assassin's
  silent walk, the jade cicada's poison immunity, the Girdle of Hippolyta's
  charge. All live now. Gram gets a dragon bonus; Mjolnir and the Sling of
  David hit giants; Glamdring hits orcs and goblinoids.
- **Over-strong:** haste and time-stop scrolls were scaled twice (95 turns of
  haste, 62 of time stop). Early Hermes sandals gave permanent haste on
  floor 5. Potion of sickness averaged four permanent stat points per sip.
- **Loot RNG:** harmful potions were 46% of early potion drops by weight, now
  26% and under a third everywhere. Healing had thinned to 8% deep, now 15%+.
  Chests ignored the spawn tables entirely (uniform pick among kinds); they now
  use them. Drain resistance had no source after floor 24; the five resistance
  amulets now cover the mid and deep floors.

## 5. Gaps found and NOT filled (need new content, your call)

- **Unique armor by slot:** hands has one unique in the whole game (floors 36
  to 70). Arms: none before 22. Legs: none on 91 to 100. Cloak: none on 1 to
  16. Shirt: two items total. Body and shield are crowded.
- **No identify wand exists.** No escape wand on floors 1 to 25 or 75+. No
  direct-damage scroll on floors 1 to 25.
- **Floors 91 to 100 have no potion-bearing chest template.**
- **Levitation, displacement, telepathy and sustenance** accessories have no
  deep source.
- **Monsters at the bottom:** floors 92 to 100 have 26 to 31 kinds (the curve
  doc asks for about 10 species there, so this is within design, but it is the
  thinnest stretch).

## 6. Decisions for you

Left alone because they are design or naming calls.

1. **Duplicates:** `chandrahas` / `chandrahasa` (Ravana's sword, twice);
   `andvaranaut` / `ring_of_the_nibelung` (same ring in the myth);
   `talisman_of_troy` / `palladium`; three Solomon rings; `world_serpent` vs
   `jormungandr_juvenile`; `orc_warlord` vs `orc_warchief`; three bone colossi;
   three Hermes footwear items all built on haste.
2. **Single mythic figures spawning as common monsters:** minotaur, medusa,
   cerberus, lahamu, anzu. Lore now speaks of "their kin".
3. **Other people's IP in names:** mind flayer, beholder, drow, yuan-ti,
   Yeenoghu (D&D); Hell Bovine / Cow King (Diablo II); Helm of Aragorn,
   Glamdring (Tolkien); Brisingr; the Boomstick lore is a near-verbatim film
   line; Charmander stuffie. Worth a decision before a commercial release.
4. **`naegling`** is class `axe`; it is Beowulf's sword.
5. **Three shields** (`horse_armor_of_the_norns`, `scarab_of_apophis_binding`,
   `yamas_dharma_watch`) carry a `spell_reflect` field nothing reads. Making it
   work means turning them into chain-equip items, which changes their quiz.
6. **Chain-equip accessories stack** their tier bonus on top of the base effect
   (Heart of Ahriman reaches INT +10). Intended?
7. **Permanent haste** has three generic tier-3 sources around floor 30.
8. **Potion of poison** ignores its own power and duration (hard-coded 20
   turns at 1 HP, most of a new character's HP).
9. **Elixir of Gilgamesh / potion of gain level** grant no level; they move
   you up one floor.
10. **Heal wands and scrolls do not scale; heal spells do.** The tier-5 wand
    heals about 67, the tier-4 spell about 147.
11. **Identical wand families:** cancellation / drain magic / dispel magic run
    the same code; disintegrate (85% kill) is strictly better than death ray
    (70%) at the same tier.
12. **Protection scrolls** print an AC bonus but never apply it.
    `scroll_of_sharpen` and `scroll_of_bracing` do nothing unless blessed.
13. **Ingredient metadata** (`temp_power`, `stat_grant`, `family` and three
    more fields on 538 ingredients) is never read by the game; cooking runs
    from the recipe tables. 452 of the declared powers disagree with what the
    recipe really grants. Delete the fields or wire them.
14. **Fear resistance on armor** (`resistance_fear` in 18 tier rows) reduces a
    damage type that never occurs.
15. **Mimic tiers:** the basic mimic (11 HP) is used through floor 24, where
    common monsters now have 60+.
16. **`diseased`** now lands from two early monsters (plague zombie, Pazuzu
    spawn) because it fits them. It drains STR / CON. Say if that is too harsh.

## 7. What to play-test

One sitting, from source (`python src/main.py`):

1. **Floors 1 to 15.** This is the part most changed in feel. Monsters past
   floor 8 should now take two or three good chains instead of one answer. If
   it feels like a wall, the lever is `SPIKE_MULT` / the spreads in
   `tools/balance/respawn_by_hp.py`, not monster stats.
2. **Drink unidentified potions on floors 1 to 10.** Fewer bad surprises, no
   sickness.
3. **Open a few chests.** Contents should look like floor loot.
4. **Read some dossiers:** a monster, a wand, a unique weapon. Tell me if the
   voice is right or too long.
5. **Combat log:** monster attack names should read lowercase in the sentence
   ("hits you with ice club").

Deep floors (giants, seal demons, Fenrir, the legends) are not reachable in a
quick session; those are covered by the data tests only.
