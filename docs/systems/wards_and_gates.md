# Wards and monster gates (MONSTERS AND MAGIC, 2026-11-19)

The magic of the MONSTERS AND MAGIC pass answers the dungeon's threats with the
systems the hero already has: a scroll (grammar), a spell (science), a wand
(science), a prayer (theology), a potion or oil (no question). Every number is
fixed by the item's tier in its data (LORE, NOT FLOOR); a spell's turns grow only
with the hero's Intelligence (`game_magic.int_reach`), as every spell's do.

| Module | What it is |
|---|---|
| `src/wards.py` + `data/wards.json` | The hero's wards: pure rules, one hook each |
| `src/attack_gates.py` (rules in `data/wards.json` `gates`) | What a monster cannot use now |
| `src/game_wards.py` (`MagicWardsMixin`, the base of `MagicMixin`) | Casting, reading, zapping, the prayer, the Sceptre's power |
| `food_system._WARD_POTIONS` | The ward potions and oils |
| `decor.place_for` / `decor.expire` | A fixture that lasts a while (the conjured vine) |
| `kitchen.makes_ref` | A carry recipe that makes a potion (`"makes": "potion:theriac"`) |
| `tools/content/add_mm_magic_2026_11.py` | Writes every item entry (safe to run again) |

## The wards (hero statuses)

Each ward is an ordinary status: it shows on the HUD, ticks down, is dispelled and
is saved with the hero.

**Family wards** (`ward_*`, `data/wards.json` `family_wards`) keep one or more
monster families (`family_lore.family_of`) off. `holds`:

* `melee`: no blow, bite, touch, grapple, sting or trample from the family lands.
  Striking one of them ends the ward against that one (`breaks: creature`; the
  memory is per rite, so a ward read again is a new one). A named foe (boss,
  mini-boss, seal demon) is too strong: its first blow lands at half and the ward
  breaks against it.
* `riders`: the family's blows carry none of the listed riders (the Psylli). The
  rider `held` is the family's holds (`src/holds.py`): no coil, gut or drag
  takes the hero, and a ward read while held lets him go (`holds.ward_line`).
* `sight`: the family cannot notice the hero (`senses._hidden`); striking any one
  ends it for all (`breaks: all`: Hoichi's ears). A named foe is not fooled.
* `damage`: the family's damage times `mult`, named foes too (Saint Martha).

| Ward | From | Keeps off |
|---|---|---|
| `ward_lemuria` | Scroll of the Lemuria (T1, 15 turns) | the restless dead's melee |
| `ward_daniel` | Scroll of Daniel (T2, 20) | great beasts' melee |
| `ward_psylli` | Scroll of the Psylli (T2, 25) | serpents' poison, holds and paralysis |
| `ward_hoichi` | Scroll of the Heart Sutra (T3, 20) | ghosts' sight of the hero |
| `ward_martha` | Scroll of Saint Martha's Hymn (T4, 25) | half of every dragon's damage |
| `ward_udug_hul` | Scroll of the Udug Hul (T5, 30) | demons' melee, and their fear, curse and confusion |
| `ward_deliver_us` | the prayer Deliver Us From Evil (karma 3+, 4 turns a link, 24 at most) | demons', ghosts', vampires' and the walking dead's melee |

A blessed scroll holds half again as long, a cursed one half.

**The hero's own wards** (`data/wards.json` `statuses`):

| Status | From | What it does |
|---|---|---|
| `missile_ward` (Arrow-Ward) | Scroll of greater protection (Psalm 91, 30 turns) | every missile fails, seen or unseen |
| `stayed_spear` | Galdr of the Stayed Spear (T2 spell) | missiles from a foe the hero can see fail |
| `veiled` (Mist-Veiled) | Mist of Manannan (T4 spell) | no foe farther than 2 tiles sees him (`senses.sees`), shoots him, casts at him or meets his eyes (a Caster's Book curse, dispel or darkness too: `caster_ai.warded` asks `wards.blow_gate`) |
| `all_round_ward` | Scroll of protection (the Breastplate, 20 turns) | a pack round him gains nothing: no swarm bonus, no hamstring (`packs.py`) |
| `sanctuary` | Sanctuary (T1 spell) | ordinary foes will not strike or cast at him (`caster_ai.warded`); ends when the hero strikes, zaps or casts at a foe, or does anything to a creature with an area spell, a scroll or a wand (`_mm_acting`: hurt it, laid a status on it); a foe he hurt in the last 20 turns is not held back |
| `styx_dipped` | Water of the Styx (T5 potion, 6 turns) | no blow, bite or claw wounds him; an unseen blow lands at half (the heel) |
| `free_action` (Loosed) | Galdr of Loosing (T1 spell) | immobilized, impaled and strangling cannot take hold; no hold takes him (`holds.loosed_line`); a monster's pull fails |
| `wakeful` | Goatherd's Coffee (T1 potion) | sleep cannot take hold (paralysis still can) |
| `clear_sight` | Moly (T3 potion, with `confuse_immune`) | hallucination and charm cannot take hold |

A **missile** (`wards.is_missile`) is a physical thing shot or thrown: an arrow,
a stone, a spear, a dart, a hurled boulder (delivery `ranged`, and a physical
damage type or a name in `missile_words`). A bolt of fire, a death ray or a
curse is a **cast** (`wards.is_cast`: any other `ranged` attack except a spit,
a spray or a swoop, `not_cast_words`), whatever its damage type: the arrow-wards
do not stop it, Silence does.

The four warding rites keep their Shielded and add what their own story names
(`ward_also` in `data/items/scroll.json`; a cursed scroll gives the Shielded only):
the Breastplate `all_round_ward`, Psalm 91 `missile_ward` and `fear_immune`, the
Aegis `petrify_immune`, the furnace `fire_shield`.

Hooks: `Monster._resolve_blow` asks `wards.blow_gate` (through `monster._ward_gate`)
first thing; `Monster._apply_attack_effect` asks `wards.rider_line`;
`monster._edge_incoming` multiplies `wards.damage_mult`; `senses._hidden` asks
`wards.hidden_from` and `senses.sees` `wards.veil_hides`; `Monster.take_damage`
calls `monster.HERO_STRUCK` (the game sets it to `_ward_hero_struck`, which acts
only on the hero's own blows: `Game._damage_by == 'hero'`, and never for a wound
ticking: `Monster.tick_effects` sets `_dot_tick`); `_ring_veil_slips` (every
strike) and `_mm_acting` (every spell, wand or scroll that did something to a
creature) end sanctuary.

## The monster gates

`attack_gates.inflict(m, status, turns)` (also what `Monster.add_effect` does for
these statuses):

* `silenced`: no voice attack and no cast (`wards.is_cast`: every bolt, ray, curse
  or prayer shot from afar, whatever its damage type), no summoning (a boss's
  summons and Abaddon's locusts too), no healing. A silenced summoner or healer
  comes and fights, and so does a caster with nothing left to use from afar
  (`attack_gates.must_close` / `close_in`, from `Monster.take_turn`). The
  mouthless (oozes, plants, constructs, or a kind's own `status_immune`) cannot be
  silenced. From Tacita's Seal (T2), the Hush of the Feralia (T4), and the Sceptre
  of Agamemnon's blow on a man or a goblin.
* `unstrung`: no missile (a bow, a sling, a thrown thing: `wards.is_missile`), its
  opener from range too; a gaze or a breath is not strung. An archer with nothing
  else to use from afar has to come to the hero, and an unstrung slinger in a pack
  slings nothing (`packs._ranged_attacks`). From the Wand of Unstringing (T3).
* `babbled`: its pack forgets its ways (`packs.in_pack` and `packs.tricks_of`
  read it), and a war-band follower cannot hear his leader (no nerve held,
  `war_bands.holds_nerve` and the take_turn flee rule; no alarm called or heard,
  `war_bands.alarm`). From the Confusion of Tongues (T3), with Confused.

A gated monster never strikes with a melee attack from range (`attack_gates.blow_gate`):
beside the hero it takes any attack it may still use; at range only one that reaches.

A named foe holds silenced or unstrung 3 turns at most, then shakes off the next
for 3 turns (`gate_grace`). Beside the hero a gated monster fights with an attack
it may still use; at range it loses the turn, with a line.

## The spells

| Spell | Tier | Effect |
|---|---|---|
| Galdr of Loosing | 1 | frees the hero from holds; Loosed 6 turns |
| Cockcrow | 1 | the turn-undead ladder's first rung: 1d8 holy, fear 4 turns |
| Sanctuary | 1 | Sanctuary 8 turns |
| Elf-Shot | 1 | paralyses one foe 3 turns (the paralyse ladder's first rung) |
| Galdr of the Stayed Spear | 2 | Stayed Spear 12 turns |
| Tacita's Seal | 2 | one foe Silenced 10 turns |
| Dionysus's Vine | 2 | the target's 3x3 held 4 turns; conjured vines there 12 turns |
| Shrink the Earth | 2 | an aimed step to a seen, empty tile within 6, over a clear line of walkable ground (never through a wall the Crown of Brahma shows; a tile spell: `needs_tile`) |
| Bough of Somnus | 2 | the target and all beside it asleep 8 turns |
| Galdr of Dulled Blades | 3 | everything in sight Weakened 8 turns |
| Confusion of Tongues | 3 | every foe that speaks Confused 6 turns, babbling 12 |
| Darkness of Egypt | 3 | everything in sight Blinded 6 turns |
| Pan's Panic | 3 | everything within 4 tiles Feared 8 turns |
| Galdr of Settled Strife | 4 | every man, goblin and giant in sight Charmed 12 turns; a blow ends it for that one |
| Mist of Manannan | 4 | Mist-Veiled 20 turns |
| Hush of the Feralia | 4 | everything in sight Silenced 8 turns |

Paralyze (T4) now holds 12 turns (its own `duration`), above Hold Monster's 8:
the flat ladder fixed by lore. Shrink the Earth's source: Ge Hong's *Shenxian
zhuan*, Fei Changfang shrinking the veins of the earth (Grokipedia, "Shukuchi").

## Potions and oils

No question to drink. Each has a real `tier` (the census checks it against where
it is found) and a `drink_line` for the cook menu.

| Item | Tier | Effect |
|---|---|---|
| Goatherd's Coffee | 1 | Wakeful 60 |
| Nepenthe | 2 | clears fear; Fearless (`fear_immune`) 50 |
| Oil of rue | 2 | clears petrifying; Stoneproof 40 |
| Fern-Flower Tincture | 2 | every treasure, coin and chest on the floor marked on the map, and drawn dim where it lies out of sight until taken (`dungeon.treasure_seen`, `Renderer.draw_item_remembered`) |
| Moly | 3 | clears confusion, charm, visions; Clear-Headed and Clear Sight 60 |
| Theriac of Andromachus | 3 | clears poison and disease; Poison Resist 80. Also brewed to carry (`brew_theriac`) |
| Water of Epidaurus | 4 | every drained stat point back (`status_effects.restore_drained`, the physician's own work) |
| Charm of Prometheus | 4 | Fire Shield and Shielded 30 |
| Water of the Styx | 5, rare | Styx-Dipped 6 |

## Wands and the Sceptre

* Wand of Unstringing (T3): Unstrung, its `power` in turns.
* Krotala of Athena (T2, wand class): every bird in sight Feared; the clash wakes
  sleepers (`_make_noise('shout')`).
* Sceptre of Agamemnon (unique 1h mace, maths tier 3): a man or goblin it strikes is
  Silenced 2 turns (its `effects.families`, read in `combat.py`; through
  `Monster.hold`, so a named foe keeps the gate's 3-turn cap and grace); V: Call
  the Assembly, once a floor visited (by depth: `_sceptre_floors`), a history
  escalator chain: every man and goblin in sight Feared 2 turns a link (12 at
  most, `gates.assembly_families`), and a war band in sight loses its leader's
  hold (`war_bands.break_hold`). Its card says both (`effects.target_words`,
  `power_line`).

## Saves

New state is created per instance and read with getattr defaults: the player's
`_ward_gen` and `_sceptre_floors`; a monster's `_wards_broken`, `_ward_half`,
`_strife_peace`, `_hurt_by_hero_turn`; the dungeon's `fixture_expiry` and
`treasure_seen`. An old save has none and reads as nothing warded.

## The simulator

`tools/balance/difficulty_sim.py`, the `_MMMagicSim` block: knobs `mm_wards`,
`mm_spells`, `mm_potions`, `mm_wands` (default 1; 0 is the ablation). The hero
uses the game's own handlers before a fight worth it. What it cannot value:
Sanctuary, Shrink the Earth, Dionysus's Vine, Bough of Somnus, the Fern-Flower
Tincture, the sutra's hiding, Deliver Us From Evil and the Sceptre's assembly.

Tests: `tests/test_mm_magic_2026_11.py`; each defect the audit of 2026-11-20 found
(`_mm_2026_11_19/G/AUDIT.md`), `tests/test_mm_magic_audit_2026_11_20.py`.
