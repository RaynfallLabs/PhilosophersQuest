# Monster Families

## Status
Built 2026-10-18 (MONSTER_FAMILIES_DESIGN.md as approved, the v2 ability ladders in
[monster_families_v2_design.md](monster_families_v2_design.md), and the coordinator's
rulings of the same day: distinct kinds only, keystones count two, Spiders merged into
Vermin, thresholds per family). Logic-tested; not yet play-tested (see the play-test list
in the build report). Field Notes are empty slots, to be filled by their own writer.

## In one paragraph
Every monster belongs to ONE of 22 families, chosen by what the creature IS in its lore.
Studying a corpse (one philosophy question; right = the kind is known) counts that KIND
for its family. A known kind's corpse never asks again, so two skeletons teach no more
than one: progress is the number of DIFFERENT kinds studied, a keystone counting two.
Each family has five tiers with the same names everywhere (Recognise, Forewarned, Lore,
Hunter, Bane); each tier grants one technique written from the family's folklore. The
first two are information (full Bestiary pages; a warning when you reach a floor). The
last three change how the fight goes, and the strongest fire only when the maths chain is
long enough: knowledge unlocks the technique, performance lands it.

## Code
- `src/family_lore.py` (pure): the kind-to-family table (from `monsters.json`, built once;
  the Bones ghost is a Ghost, Death / the secret cow / the ethereal unicorn have none),
  `family_of`, keystones, `tiers(player)` (cached on the player), `progress`, `has_page`
  (ruling 1), `record_study`, `news` (each tier, circle and the title once), circles,
  Loremaster, secret-build head starts, old-save migration, the text built from data.
- `src/family_edges.py` (pure): the registry of technique PRIMITIVES and the questions the
  engine asks (`save_bonus`, `duration_mult`, `damage_mult`, `extra_seconds`, ...). Every
  rail lives here (family only, never a concealed creature, the named-foe rail, the
  once-per-fight trigger line).
- `src/game_families.py` (`FamilyMixin`): announcing news (gold lines, popups in the quirk
  popup's style, Journal lines), the arrival lines, calm arrivals, the per-turn checks
  (flee on sight, a sensed hidden creature), draining the technique lines, Yield!'s purse,
  the QA key.
- `src/monster_classes.py`: a thin reader (`get_monster_family`, `get_family_name`).
- `tools/content/assign_monster_families.py`: proposes, writes and re-checks the `family`
  field (`--write`, `--check`, `--sheet` for the decision record of the 138 lore-settled
  borderline creatures, `--rates` for what a run meets and the ladder rule).

## Data
- `data/monsters.json` `family`: one of the 22 ids on every monster.
- `data/monster_families.json`: per family `name`, `short`, `kin` (the phrase the text uses:
  "the restless dead"), `blurb` (two sentences, no member named), `thresholds` (five
  numbers of distinct kinds), `keystones` (extra legends beyond the flagged ones), and
  `tiers` (exactly five: `name`, `field_note` (empty = hidden), `abilities`). An ability is
  `{id, name, text, trigger_msg, effect, params, also?}`: `effect` is a primitive, `also`
  adds more parts to the same technique. Top level: `tier_names`, `keystone_weight` (2),
  `no_save_ward`, `tier_messages`, `popup_titles`, `popup_leads`, `tier_chronicle`
  (Journal templates, linted), `circles`, `loremaster`. Every number is here; nothing scales by floor.

## How knowledge is earned
- One study = a correct corpse study (`_start_corpse_identify`) or a Scroll of Omnisight
  (`_omnisight_corpse_reveal`). Killing, harvesting and seeing never count. A wrong answer
  is the usual 10-turn Stun.
- The Book of Thoth fills `lore_known_monster_ids`: it opens Bestiary pages and teaches no
  tier (decision 4). A kind it only opened can still be studied from its corpse (corpses
  pre-identify for `studied_monster_ids`, the hero's own studies).
- Keystones: `is_boss`, `is_mini_boss`, `is_seal_demon`, `proper_noun`, or listed in the
  family's `keystones` (the spider queen). A keystone counts `keystone_weight` = 2 kinds.
- Tier N needs `thresholds[N-1]` (weighted) kinds. The numbers were set from real floor
  generation: kinds a run meets x (12, 25, 40, 55, 70)%, at least 2, 3, 4, 5, 6.
- The 22 families as written (kinds in `monsters.json`; kinds a run meets, from 12 seeds of
  real floor generation, `assign_monster_families.py --rates 12`; the five thresholds):

  | id | Family | Kinds | Met a run | Tiers 1-5 |
  |---|---|---|---|---|
  | demons | Demons and Devils | 68 | 50.4 | 6, 13, 20, 28, 35 |
  | restless_dead | The Restless Dead | 49 | 29.9 | 4, 9, 14, 19, 24 |
  | ghosts | Ghosts and Shades | 38 | 19.8 | 3, 6, 9, 12, 15 |
  | mortals | Mortal Foes | 34 | 18.9 | 2, 5, 8, 11, 13 |
  | goblinkin | Goblins and Orcs | 33 | 19.4 | 2, 4, 7, 10, 13 |
  | giants | Giants and Trolls | 31 | 23.0 | 3, 6, 9, 12, 16 |
  | vermin | Vermin, Spiders and Swarms | 31 | 15.5 | 2, 3, 5, 6, 8 |
  | aberrations | Aberrations | 29 | 21.3 | 2, 5, 8, 11, 14 |
  | dragons | Dragons and Wyrms | 28 | 23.1 | 3, 6, 10, 13, 17 |
  | fair_folk | The Fair Folk | 28 | 11.8 | 2, 3, 5, 6, 8 |
  | vampires_liches | Vampires and Liches | 28 | 19.0 | 2, 5, 8, 10, 13 (re-derived: the membership grew by a third) |
  | legend | Monsters of Legend | 27 | 17.8 | 2, 4, 7, 9, 12 |
  | serpents | Serpents and Swamp-Kin | 25 | 12.8 | 2, 3, 5, 7, 9 |
  | constructs | Golems and Constructs | 21 | 14.4 | 2, 4, 7, 10, 12 |
  | great_beasts | Great Beasts | 21 | 10.2 | 2, 3, 5, 7, 8 |
  | elementals | Elementals and Djinn | 18 | 16.0 | 2, 4, 6, 8, 10 |
  | plants | Plants and Fungi | 15 | 9.2 | 2, 3, 4, 5, 6 |
  | oozes | Oozes and Slimes | 13 | 6.8 | 2, 3, 4, 5, 6 |
  | birds | Birds and Winged Hunters | 12 | 5.4 | 2, 3, 4, 5, 6 |
  | gorgons | Gorgons and Basilisks | 9 | 4.9 | 2, 3, 4, 5, 6 |
  | shapeshifters | Werebeasts and Shapeshifters | 9 | 5.3 | 2, 3, 4, 5, 6 |
  | celestials | Celestials | 7 | 4.9 | 2, 3, 4, 5, 6 |

  (Wandering monsters add more kinds than generation alone, so a diligent hunter climbs
  faster than these counts suggest.)
- Secret builds: `_start_family_lore` in `SECRET_BUILDS` gives tier 1 or 2 only, never a
  technique, and nothing says so (Geralt, Aristotle, Ash Ketchum, Merlin, Theseus,
  Odysseus, Ash Williams, Hildegard, Leonardo, Lovelace, Tesla, Sherlock; Socrates none).
- Knowledge lasts one run. Bones carries none of it.

## The five tiers
| Tier | Name | What it does |
|---|---|---|
| 1 | Recognise | Every member of the family the hero sees gets its full Bestiary page, O opens it, and the look line names the family. Does NOT pre-identify corpses. |
| 2 | Forewarned | On reaching a floor, the family's line, if a member the hero could see is here (never an invisible creature, an un-sprung ambusher, a disguised mimic or the Hellmouth's stair, or an ally). At most three lines; past that two and one combined line. |
| 3 | Lore | The folk defence (wards, mostly). |
| 4 | Hunter | How a hunter takes them. |
| 5 | Bane | The signature capstone. |

The per-family techniques are in `data/monster_families.json` and the v2 design (section 4).

## Primitives (`family_edges.PRIMITIVES`) and where each is hooked
| Primitive | Params | Engine hook |
|---|---|---|
| `recognise` | | `family_lore.has_page` -> `Game._open_bestiary_page`, `_confirm_observe`, the Bestiary list |
| `forewarned` | `line` | `FamilyMixin._family_arrival` (end of `_change_level`) |
| `save_bonus` | `effects` (status ids, `drain`, `gaze`), `amount`, `scope?` | `status_effects.apply_debuff_with_save(source=)` from `Monster._apply_attack_effect` and the gaze blocks; `Monster._drain_takes_hold`. Outside the +5 cap of `Player.save_bonus_for`. Against an effect with NO save (poison, burning, blinding) the ward shortens it instead (`no_save_ward` in the data: a share off a point, at most half), and a `duration_mult` for the same effect does not stack with it: the stronger counts. |
| `duration_mult` | `effects`, `mult` (0 = never takes hold) | `apply_debuff_with_save` |
| `resist_damage` | `types`, `mult`, `scope?` | `Monster._resolve_blow` and the gaze path before `player.take_damage` (family; the strongest one wins); `Player.take_damage` (circle, any source) |
| `damage_mult` | `mult`, `chain_min?`, `weapons?` + `weapon_mult?`, `only_weapons?`, `big_mult?` | `combat.strike_damage` beside the Dragonslayer Ring (so `strike_preview` shows it); thrown weapons in `_throw_weapon`. Weapon blows on a SEEN creature only; never spells or pets. |
| `weakness_amp` | `mult` | `combat.strike_damage` (the blow's form or substance hits a listed weakness) |
| `extra_seconds` | `seconds`, `scope?`, `boss_only?` | `combat.player_attack`, the Ancile's `extra_seconds` lane (the clock shows it) |
| `chain_forgive` | `uses` | `combat.player_attack` sets `QuizEngine._forgive_flag`; `QuizEngine._advance` lets one wrong answer through; spent per creature (once per fight) |
| `opening_chain` | `chain` | `combat.effective_chain`, beside Harpe's `skip_chain_warmup_vs_tag`; first blow on a creature only |
| `pierce_resist` | `chain_min`, `scales?`, `blessed?` | `combat.strike_damage`: the resistance undone as the chain specials' bypass does; `scales` also skips dragon scales and damage wards |
| `block_regen` | `turns` | `family_edges.after_blow` sets `_regen_blocked`; `Monster.tick_effects` regeneration check |
| `prevent_split` | | `combat.player_attack` marks the blow; `splitting.blow_splits` |
| `execute` | `chain_min`, `hp_below`, `variant`, `named_mult` | `family_edges.after_blow` (lesser foes, no revive or split); a named foe takes `named_mult` in `strike_damage` instead |
| `turn` | `trigger` (on_hit / on_kill / on_sight), `turns`, `chain_min?`, `chance?` | `after_blow`, `after_kill` (from `player_attack`), `FamilyMixin._family_turn`; the monster's own fear (`Monster.hold('feared')`, `resists_control`) |
| `calm_on_arrival` | `chance` | `FamilyMixin._family_arrival` (first visit): charmed + `_bribed`, so a blow breaks it (the Gilgamesh's Bribe rule) |
| `charm_on_hit` | `chain_min`, `turns` | `after_blow` |
| `surrender` | `chain_min`, `hp_below`, `turns` | `after_blow` + `FamilyMixin._family_surrender` (a gold pile via `items.add_gold_to_tile`, picked up by the coin-weight rules) |
| `theft_immune` | | `theft.steal` |
| `no_ambush` | | `Game._do_passive_ambush_detection` (sure detection), `Monster._resolve_blow` (no mimic surprise blow) |
| `sense_hidden` | `kinds` (invisible / ambush / disguise), `radius` | `unseen.unseen` / `unseen.lurking(m, player)` / `unseen.concealed` via `unseen.senses`: drawn, targetable and O-able; family only, inside the radius |
| `gaze_immune` | `requires` (`shield`) | the floating-eye gaze and Medusa's gaze in `Monster.attack`; the gaze check in `Monster._resolve_blow` |
| `harvest_bonus` | `portions` | `food_system.harvest_corpse` |
| `drain_heal_block` | | `Monster._resolve_blow` (`drain_heals_self`) |
| `stun_on_hit` | `chain_min`, `turns` | `after_blow` |
| `sight_bonus` | `amount` | `Player.get_sight_radius` (circle) |

The rails: a technique works only on its own family and only on a creature the hero can
recognise (not concealed). Named foes (bosses, mini-bosses, seal demons) are never
executed, turned, calmed, charmed, stunned or made to yield; wards, damage, block_regen,
pierce_resist and sense_hidden do apply to them. A trigger line prints once per creature
per technique (`family_edges.tell`, the outbox drained by `FamilyMixin._family_drain`).

## Circles and the Loremaster title
Worked out from the tiers every time (never stored); told once (`family_tiers_told`
markers `circle:<id>`, `loremaster`), each with a popup and a Journal line.
(The boons' numbers are the tuned ones, in `data/monster_families.json`.)

| Circle | Families | Needs | Boon |
|---|---|---|---|
| The Grave Watch | Restless Dead, Ghosts, Vampires and Liches | all three at tier 3 | Vigil: necrotic and drain damage 10% less, any source |
| The Wild Road | Great Beasts, Birds, Serpents, Vermin, Plants | any three at tier 3 | Ranger's Instinct: +1 sight |
| The Hellward Gate | Demons, Fair Folk, Aberrations | all three at tier 3 | Unbent Mind: +1 on saves vs confusion, charm, fear, any source |
| The Hero's Road | Monsters of Legend, Gorgons, Giants, Dragons | any three at tier 3 | Hero's Nerve: +1 second against any boss |

Loremaster: tier 5 in any five families. Your Story, the Discoveries page, the @ sheet,
the Journal and the high-score table (`title`) show it.

## What the player sees
- O on a creature: an identified kind opens its full page and the look names the family
  ("You see Ghast (wounded). Restless Dead."); a kind only seen keeps the plain look and
  "You don't know this creature yet. Study its corpse."
- B, Bestiary: every kind met is listed; an unidentified one has a short page (name, art,
  family, "Not yet studied", the progress line) and no stats, attacks or lore. A full page
  carries "Family: ... (studied)" or "(known by its family, not yet studied)". Tab switches
  to Families: tier, blurb, kinds studied and seen, progress ("6 of 9 to Hunter"), all five
  tiers (learned, or their kinds needed as a goal), written Field Notes of learned tiers,
  members seen. Unseen members and a family's size are never shown.
- Corpse page: "Family: ... (studied)" with the progress line, or "Not yet studied: Restless
  Dead 2 of 4 to Recognise".
- News: tiers 1 and 2 a gold line; tiers 3 to 5 a popup ("LORE OF THE RESTLESS DEAD") with
  the technique and its Field Note; a Journal line per tier (`once` key `family:<id>:<tier>`).
- @ sheet: a Monster Lore block (title, circles, then each family with its tier and
  techniques), "+N more".
- Help: "I: Identify or study" (corpses are studied from the identify menu), "B, Tab: Monster families".
- QA: Shift+F with the Titivillus build (PQ_QA_MODE) raises the nearest creature's family
  a tier, or every family when none is in sight.

## Saves
New `Player` fields: `studied_monster_ids`, `family_tiers_told`, `family_lore_grants`.
`Player.__setstate__` -> `family_lore.migrate_old_save`: an old save's studied set is its
`lore_known_monster_ids`, and every tier it gives is marked told (no popup flood). The
retired names `family_masteries` / `family_mastery_blessings` are still deleted on load.
Transient `_family_tier_cache` and `_edge_msgs` are dropped from pickles. Monsters and
corpses saved before families look their family up by kind.

## Testing
`tests/test_monster_families_data.py` (the data: 22 families, five tiers and thresholds,
primitives and params, Title Case, no singular they, blurbs name no member, keystones,
the assignment tool agrees with the file) and `tests/test_monster_families.py` (one logic
test per primitive, the named-foe rail, sense_hidden radius and family, a disguised mimic
seen only by Mimic-Sense at two tiles, chain_forgive once per fight, keystones count two,
circles, old saves, Thoth, the study hook, news, arrival lines, head starts, Yield!, the
QA key). `tests/test_observe_bestiary.py` covers ruling 1. UI capture scenes:
`menu_bestiary_family_page`, `menu_bestiary_short_page`, `menu_bestiary_family_line`,
`popup_family_tier`, `menu_charsheet_monster_lore`.

## Balance
`tools/balance/difficulty_sim.py --knobs families=1,study_rate=0.85` plays a hero who
studies the corpse of each new kind he kills (85% of the time, one question at the
corpse's tier) and earns the tiers; every technique then runs through the real game code.
The v2 design's first-draft numbers (wards +4, damage 15-30%, executes at chain 10,
+3 seconds) put the committed 95% hero about 25 points above baseline; the target was
about 10. The simulator then cut them, data only, in passes measured on that cell
(survival to the end, `committed` 95%, baseline about 58%):

| Pass | Change | Families |
|---|---|---|
| 0 | as designed | +29 |
| 1 | damage edges roughly halved | +25 |
| 2 | executes at chain 12, lower health lines | no change |
| 3 | wards +2, no-save effects a third shorter | +25 |
| 4 | damage, executes (chain 15), calm, seconds (2), resists cut again | +20 |
| 5 | circles halved, turning at longer chains, regeneration stop 3 turns | +16 to +19 |
| 6 | seconds 1, calm and resists cut, pierce at longer chains | +11 (390 runs: a lucky low) |
| 7 | damage and weakness a little lower | +16.7 (810 runs from here on) |
| 8 | a ward against a no-save effect shortens it instead of stacking | +14 |
| 9 | wards +1 | +13.5 |
| 10 | durations a tenth shorter, resists 5%, calm one in ten / five, executes at chain 18 | +12.8 |
| 11 | Solomon's Seal: burning and freezing wear off twice as fast (they were blocked outright) | +11.2 |

Attribution at the last passes (each group switched off, 810 runs): the Steady Hand
seconds and the Hero's Nerve were worth about 5 points even at one second, the wards
about 7 (mostly the outright blocks), turning and calm about 2 each, damage about 2.
Final (200 runs a cell, 10 chunks, PYTHONHASHSEED=0): committed 95% 57.5 -> 69.0;
prepared 95% 57.5 -> 59.5; committed 90% 22.5 -> 26.0; prepared 90% 15.0 -> 17.0. Every
number is one edit in `data/monster_families.json` if play says a technique feels flat.
