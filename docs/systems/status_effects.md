# Status Effects

**Status:** v2.18.0 (shipped 2026-10-02)
**Code:** `src/status_effects.py` (654 lines); `Player.add_effect` / `has_effect` / `tick_effects` live in `src/player.py`
**Data:** `data/effects.json` (the gate, refresh and caps, stone, the quiz effects, their lines); `data/confusion.json` (confusion's Clear-Headed recovery); chest/trap/food/monster JSON references effect ids
**Related docs:** [save_bonus](save_bonus.md), [combat](combat.md), [quiz_engine](quiz_engine.md), [magic](magic.md), [food_system](food_system.md), [monsters](monsters.md), [items](items.md), [identify_v3](identify_v3.md)

## Purpose
A single registry + tick loop drives every timed status in the game: paralysis, poison, haste, invisibility, resistance halos, cooked wards, chain-combat specials, death-countdowns. One table defines display, color, and short text; four frozensets categorize behavior; `apply_effect` + `apply_debuff_with_save` + `tick_all` form the complete API.

## Design intent
NetHack-style "turn count tells the story" statuses are the backbone of roguelike combat identity. The design decisions that shape THIS file:

**One registry, one tick loop.** `EFFECT_INFO` is the single source of truth for every effect's display name, HUD color, and short description. UI (sidebar, bestiary, expire log) reads from here. `tick_all` walks `player.status_effects` once per turn and dispatches per-effect side effects. Adding a new effect = add one row to `EFFECT_INFO`, add the id to the right frozenset(s), optionally add an `_EXPIRE_MSGS` line, optionally add a dispatch branch in `tick_all`.

**Four categories gate behavior**, and effects can be in several of them:
- `BUFFS` — stripped by `dispel_magic` / `cancellation` / `drain_magic` targeting the player's own buffs.
- `DEBUFFS` — stripped by scrolls/prayers that "cleanse" the player.
- `HARD_CONTROL` — the autokill risk (paralysis, sleep, stun, freeze, immobilize, petrifying, fear, held). D&D-save NEGATES; cannot be re-applied while active; followed by a 3-turn grace window.
- `SOFT_CONTROL` — degraded but not frozen (confuse, charm, slow, weaken, forget). A save HALVES (Forget: negates). Weakened refreshes to `max()`; the others are bouts (`SOFT_GRACE`): never refreshed while they run, followed by 3 turns Clear-Headed, Clear Sight (charm) or Footing (slow).

**Gradient defense, never immunity.** Three layers:
1. **Resist items** (`_RESIST_BLOCKS`) — hard immunity for a specific debuff class, short-circuits before the save math.
2. **Save bonuses** ([save_bonus.md](save_bonus.md)) — a +N to the d20 save roll (gradient; +5 total cap, +3 timed cap).
3. **No defense** — the save roll fires unmodified.

The important design rule: **saves + resists never overlap**. If `poison_resist` is active, the `poisoned` debuff never gets to the save roll at all — it's refused in `apply_effect`'s first branch. If `poison_resist` is absent, the save math fires (and `poisoned` has no `SAVE_STAT` so the CON-based duration-reduction branch applies — see [save_bonus.md](save_bonus.md) §apply_debuff_with_save).

**Hard-control anti-permalock guarantee.** A hard-control effect cannot be refreshed, re-applied while active, OR re-applied within the 3-turn `control_immune` grace window after it expires. This GUARANTEES free turns between every disable bout. Monsters that reliably re-cast paralysis still can't permalock.

**Confusion's recovery** (Brandon 2026-11-19, with the quiz scramble: "careful it's not an auto kill"). Confusion scrambles every quiz's words until they settle (the confusion section of `src/quiz_engine.py`; it no longer cuts the clock), so it must never chain. `SOFT_GRACE = {'confused': ('confuse_immune', 3)}` (`data/confusion.json` `recovery`; `CLEAR_HEADED_TURNS`) gives it the hard-control shape: a running confusion is not refreshed (`apply_effect` returns False), and when it ends, at its expiry in `tick_all` or by a cure anywhere (a potion, a prayer, a trader, a fixture: `_recover_cured`, at the end of every tick and before any new confusion is laid on), the hero is **Clear-Headed** (`confuse_immune`, which `_RESIST_BLOCKS` already lets block `confused`) for 3 turns. A trophy's permanent Clear-Headed is left as it is. The bouts running are kept in `player._soft_bouts` (a set, pickled; an older save's confusion is marked at the next tick). The WIS save, the head guard, magic resist, the family wards and the 6-turn cap all still come first.

**Control cap** per single application: `CONTROL_CAP` clamps individual durations so one failed save is never a death sentence even if the data file says "paralyze 20". `MAX_EFFECT_DURATION = 60` globally caps every effect (prevents infinite stacking on non-CONTROL effects which use `current + duration` additive stacking).

**Resource loss IS the penalty.** DoTs (bleed/burning/doom_dot/draining) still land even on a successful save — the save only applies a flat CON-based duration reduction, min 1 turn (§apply_debuff_with_save non-SAVE_STAT branch). This preserves "the quiz-gated action cost IS the penalty" rule without making tanks poison-immune.

## Poison (Brandon, 2026-11-22: "two damage? why have these cure poison potions"; src/venom.py)

- **Each venom has its own strength.** A monster's poison attack does its `venom` (data/monsters.json) a turn, written kind by kind from its lore in `tools/content/poison_pass_2026_11_22.py`: a mild venom costs about 12% of a typical hero's HP over one bite where the kind is most met, an ordinary one about 20%, a deadly one by lore about 30%. A kind of floors 1-5 keeps 1 a turn, and no venom is weaker than the old 2% tick where it lives. Nothing scales by the floor; Player.take_damage's toughness and the rest still apply. A poison with no venom (the potion of poison, a trap, foul water) keeps `DOT_SHARE` of max HP.
- **Doses add, a little.** A bite on a poisoned hero adds half its turns (`effects.json` `poison.add_share`), never past one and a half of the bout's longest dose (`most_doses`). The strongest venom on him sets the tick. Ten bites cost no more than two.
- **A CON save halves the dose** (d20 + CON mod + save bonus against the attack's dc). It never cancels the bite.
- **Venom Ward** (`venom_ward`, a plain meal against venom): half the venom and half the turns. Poison Resist still keeps poison off whole.
- **It shows.** `venom.to_come` (a turn's toll after the body's share, times the turns left) is drawn as the striped end of the HP bar (ui.draw_venom_due, on the sidebar and the combat strip), said on the chip ("Poisoned: 14 to come", "... Cure it!" when it would kill) and on each bite's line. The Bestiary gives each poison attack's venom and turns.
- **Cures:** the potion of cure poison (every stall of floors 2-20 keeps one, `traders.json` `always_stocked`, and the apothecary always has one), cure all, Theriac, Cleanse, a mercy prayer at a chain of four, the fountain, the apothecary's and sutler's cure, Poison Resist from meals, rings and armour.
- Six attacks were not venom by lore and lay something else now: the rotting zombie's claw nothing, the plague zombie's claw and the rot grubs disease, the green slime's, gray ooze's and ochre jelly's acid Corroding.
- An older save's monster takes its kind's venom on load (`effect_rules.refresh_monster`, `EFFECTS_PASS` 2).

## The monster effects (Brandon, 2026-11-22: "All as recommended")

**One gate.** Every action names its door (`data/effects.json` `doors`) where it is committed and asks `Game._gate`; a step asks `Game._gate_step`. `action_gate.verdict` is pure and answers open, lose (the turn is spent), refuse (no turn), stand, thaw, fall, drop or fizzle. A key that only opens a menu asks nothing: the choice does, so a menu opened before the effect landed is no way round it. `tests/test_action_doors.py` tries every effect at every door and fails when something spends a turn behind the gate's back.

| Effect | What it stops | The answer |
|---|---|---|
| Paralyzed, Sleeping | everything | saves, resists, a blow wakes a sleeper |
| Knocked Down | everything: the next action is standing up, with no dodge until then | Guard, boots, levitation, Footing |
| Frozen | step, stairs and climbing out of a pit (turn lost); swap, take off, drink, zap, shoot, throw, apply, ride (refused) | a lit light thaws in a turn; cold resistance |
| Immobilized | feet only (step, stairs, climbing out of a pit) | strike, shoot, use the hands |
| Slowed | nothing: `get_speed` halves, so every action is two of the world's turns | boots, DEX, Footing after it |
| Silenced | cast, read aloud | wax, magic resistance |
| Hexed | taking off or swapping what is worn | Cleanse, altar, any remove-curse |
| Feared | going nearer or striking its source | step away, shoot, cast; cornered, he may fight |
| Charmed | attacking the charmer, taking a stair while it is in sight; feet walk to it | its first wound or its death ends it |
| Stunned | the first step falls, the first fumble drops, the first spell fizzles, once a bout | Guard; a self-inflicted stun does none of it |
| Fumbling | the first thing handled drops, once a bout | Guard |

**Bouts** (`effect_rules`, `player._bouts`, saved): who laid it, self-inflicted, lethal, which once-a-bout price is paid, gear worn (one piece a bout of burning or corroding). A hold ends with its owner and with the floor. A bout with no end (cursed gear) starts again on each floor.

**On the quiz** (`quiz_sight`, display only): Stunned is double vision, Hallucinating a false answer in a slot of its own, Blinded a pool of light the arrows move. Confused, Stunned and Hallucinating share one settle time; the dark has none; no debuff cuts the clock. The question data, the answer check and the teaching card are never touched.

**Petrifying** (`petrify`): stiff, slow, rigid. A lethal bout (a basilisk, a gorgon, the gorgon chest) ends in stone; any other in one turn of paralysis. Oil of Rue is always stocked on floors 19-99 (`traders.json` `always_stocked`), never marked: the tell and the hint teach its look.

**Forget** (`mind_theft`): one identified kind or one Bestiary page a bout. A kill on that floor gives it back, leaving makes it permanent. Never spells, stats, family tiers, the Shard or what a mastered tier names by itself.

**Whom he spares** (`effect_rules.spares`): his charmer, by any means, aimed or not, and by a blow what frightens him. `holds.strikable` and the two reach checks of `game_magic` ask it, so every wave, sweep and nearest-foe power does.

**A price is for what could be done:** `Game._gate(..., possible=)`. A fall, a drop, a fizzle or a thaw is never charged for an action that would have refused by itself.

**A false answer is provably false:** a sum with one value borrows a number that differs however read, a which-divides sum one that does not divide, and any other question gets dream words (`effects.json` `quiz.phantom`).

**Older saves:** a monster saved before the pass takes its kind's effect fields by attack name on load (`effect_rules.refresh_monster`). A curse on the hero becomes a hex.

**A story's price** keeps its length through `price_cap`; control and Slowed keep their caps.

**Cures:** `AILMENTS` is every debuff but the crank and the pit. `ailments_on` lists those that run out, most urgent first; what gear holds on the hero (-1) goes with the gear. The fountain, Cleanse and XYZZY read it.

**On a monster:** Cursed is -2 to hit (`ai_blow`). An effect thrown back goes through `reflected`, so stone can never kill by reflection.

## Data model / schema

### `EFFECT_INFO: dict[str, (display_name, rgb, description)]`
All effect ids (debuff, buff, control, resistance, chain-combat-v2 specials, hero-special buffs) live here. The HUD color and short description are read directly for sidebar chips and expire-log entries. Example rows:
```python
'paralyzed':   ('Paralyzed',   (220,  50,  50), 'Cannot move or act'),
'poisoned':    ('Poisoned',    ( 80, 210,  60), 'Venom hurts every turn; the striped end of your health bar is what it will still take'),
'hasted':      ('Hasted',      (245, 245,  60), 'Monsters act half as often'),
'blessed':     ('Blessed',     (200, 240, 160), 'All quiz timers +25%; divine clarity'),
'petrifying':  ('Petrifying',  (205, 205, 130), 'Turning to stone: stiff, then slow, then stone. Oil of Rue cures it'),
'doom_dot':    ('Doom',        (140,  60, 200), 'Ticking damage as fraction of max HP per turn (Laevateinn)'),
'control_immune': ('Recovering', (200, 230, 255), 'Shaking it off -- briefly immune to being disabled'),
'confused':    ('Confused',    (185, 100, 230), 'Steps go astray, but blows land where aimed; quiz words swim, then settle'),
'save_guard_CON': ('Body Ward', (150, 230, 170), 'Bonus to resisting paralysis / sleep / stun'),
```

### `player.status_effects: dict[str, int]`
The one place every effect's duration lives. Values:
- `n > 0`  — active for `n` more turns.
- `-1`    — permanent (intrinsic, immutable via `apply_effect`).
- `0` / absent — not active.

Read with `player.has_effect(name)` (true for any non-zero value). Written only through `apply_effect` / `apply_debuff_with_save` / `tick_all`. Direct writes are allowed but discouraged — the `grendel_grip` tick-clear is the one in-tree exception.

### Core constants

```python
MAX_EFFECT_DURATION = 60    # Global hard cap on any effect's turn count
GRACE_TURNS         = 3     # Post-hard-control immunity window
```

### `BUFFS` (frozenset)
```python
{
  # Movement / perception / combat buffs
  'hasted', 'invisible', 'levitating', 'regenerating', 'telepathy',
  'warning', 'searching', 'clairvoyant', 'displacement', 'heroism', 'brilliance',
  'shielded', 'fire_shield', 'cold_shield', 'reflecting', 'phasing', 'time_stopped',
  'blessed', 'invulnerable',
  # Resistance effects (can be timed or permanent)
  'fire_resist', 'cold_resist', 'shock_resist', 'poison_resist',
  'sleep_resist', 'magic_resist', 'drain_resist', 'disint_resist',
  # Accessory-granted permanent buffs
  'life_save', 'sustained', 'truesight', 'dark_vision', 'identify_sight', 'spell_turning',
  'riposte_armed', 'parry_armed', 'see_invisible',
  # Hero special buffs (Phase 3B)
  'stand_ac', 'crit_buff', 'fear_immune', 'boomstick_aoe_next', 'berserk',
  # Chain combat v2 (v2.14.0) player-side buffs
  'blade_flow', 'melee_dmg_reduction',
  # Post-lock grace buff (set when a hard-control effect expires)
  'control_immune',
  # After a slowing or a knock-down
  'footing',
  # Cooked / power "ward" buffs — timed saving-throw bonuses
  'save_guard_CON', 'save_guard_WIS', 'save_guard_DEX', 'save_guard_all',
}
```
**v2.18.0 note:** `berserk` was previously double-classified (BUFFS + DEBUFFS). It grants +STR damage at the cost of HP/turn — net buff behavior — so it's a BUFF only. `abjuration` / `cancellation` / `dispel_magic` correctly strip it as an enchantment on the target now.

### `DEBUFFS` (frozenset)
```python
{
  # Classic NetHack debuffs
  'paralyzed', 'sleeping', 'stunned', 'confused', 'blinded', 'hallucinating',
  'poisoned', 'diseased', 'petrifying', 'strangulation', 'fumbling',
  'slowed', 'aggravated', 'teleportitis',
  # Mind-affecting / social
  'feared', 'charmed', 'cursed', 'weakened',
  # DoTs / curses
  'bleeding', 'doomed', 'draining', 'burning', 'frozen', 'corroding',
  # Movement locks
  'immobilized', 'in_pit', 'silenced',
  # Alternate potion label (same semantics as hallucinating)
  'hallucinating_pot',
  # The monster effects (2026-11-22)
  'hexed', 'knocked_down', 'forgetting',
  # Engine wave 3 (2026-05-30): Gae Dearg's wound-lingers
  'heal_blocked',
  # v2.18.0 audit sync: Laevateinn's doom_dot was in EFFECT_INFO but missing here
  'doom_dot',
  # Chain combat v2 (v2.14.0) weapon chain-special monster debuffs
  'armor_crack', 'sundered', 'deep_wound', 'ruptured', 'impaled',
  # v2.15.0: crossbow reload cooldown (sits here only so tick_all decrements it)
  'reloading',
}
```
**v2.18.0 note:** `doom_dot` was missing from DEBUFFS despite having an EFFECT_INFO row — status HUD and strip-debuffs paths dropped it silently. Fixed.

### `HARD_CONTROL` (frozenset)
```python
{'paralyzed', 'sleeping', 'immobilized', 'stunned', 'frozen', 'petrifying', 'feared', 'held'}
```
Zero / near-zero player actions. Save NEGATES; cannot be re-applied while active or during the 3-turn grace.

**v2.18.0 note:** `petrifying` was moved into HARD_CONTROL. Its `val==1` tick fires the `_petrify_death` signal, so a half-duration save-halve could still kill. HARD_CONTROL semantics make a successful CON save negate it outright.

**AI-3 note (2026-11-20):** `held` (Held Fast, `src/holds.py`: a coil, a gullet, a drowning grip) joins HARD_CONTROL at the end of the module (with `feared`, added in 2026-10): a DEX save slips it, `CONTROL_CAP['held']` is 4, the grace follows it. It refuses walking only (a step is a struggle; a blow on the holder is the way out), so `main._do_move` handles it after `immobilized`. It is not in DEBUFFS: no cure lifts a grip (the holder's death, a hard blow, the struggle, Loosed, the Coif of Beowulf or its running out do). The caster's ward on a monster shows as `spell_ward` ("Warded").

**v2.18.0 note:** `stunned`'s *gameplay* is soft (he still acts: see the gate), but it's deliberately kept in HARD_CONTROL so a successful save fully negates it and cannot be re-applied in the grace window. Removing it would allow a fast monster to stun-lock.

### `SOFT_CONTROL` (frozenset)
```python
{'confused', 'charmed', 'slowed', 'weakened', 'forgetting'}
```
Degraded but not frozen. A save HALVES the duration (Forget: negates, `NEGATED_BY_SAVE`, as does a knock-down). `weakened` refreshes to `max(current, new)`; the others are bouts (`SOFT_GRACE`, Design intent).

### `CONTROL`
```python
CONTROL = HARD_CONTROL | SOFT_CONTROL
```

### `SAVE_STAT: dict[effect_id -> stat]`
D&D-style saving throw category per effect:
```python
{
  'paralyzed': 'CON', 'sleeping': 'CON', 'stunned': 'CON', 'frozen': 'CON',
  'petrifying': 'CON',
  'confused':  'WIS', 'feared':   'WIS', 'charmed':  'WIS',
  'slowed':    'DEX', 'immobilized': 'DEX', 'knocked_down': 'DEX',
  'weakened':  'CON', 'forgetting': 'WIS',
}
```
- CON (body) — physical disables.
- WIS (will) — mind-affecting.
- DEX (reflex) — movement locks.
- Poison rolls its own CON save, which halves the dose (see Poison above).
- Effects **not in this map** (bleed, burning, doom_dot, …) bypass the stat-save roll but still receive a CON-based duration reduction via `save_bonus_for('CON')` (v2.18.0 fix — see [save_bonus.md](save_bonus.md)).

### `CONTROL_CAP: dict[effect_id -> max_turns]`
Hard cap on a SINGLE application's duration. Clamps egregious data values so one failed save can't exceed design headroom:
```python
{
  'paralyzed': 4, 'sleeping': 5, 'stunned': 3, 'frozen': 4, 'immobilized': 4,
  'confused':  6, 'feared':   6, 'charmed':  6,
  # from data/effects.json statuses.caps
  'slowed':    4, 'weakened': 8, 'petrifying': 10, 'forgetting': 6,
}
```

### `_RESIST_BLOCKS: dict[resist_effect -> set[blocked_effect]]`
Hard immunity table. If the resist effect is active, the listed debuffs are refused outright at `apply_effect`'s first branch (before the save math):
```python
{
  'poison_resist': {'poisoned', 'diseased'},
  'sleep_resist':  {'sleeping', 'paralyzed'},
  'drain_resist':  {'diseased', 'draining'},     # v2.18.0: draining now blocked
  'fire_resist':   {'burning'},
  'cold_resist':   {'frozen'},
  'fire_shield':   {'burning'},       # and laying a full shield ends it
  'cold_shield':   {'frozen'},        # (_QUENCHES)
  'magic_resist':  {'confused', 'charmed', 'silenced', 'feared',
                    'hallucinating', 'hallucinating_pot', 'forgetting'},
  'petrify_immune': {'petrifying'},
  'confuse_immune': {'confused', 'forgetting'},
  'footing':       {'slowed', 'knocked_down'},
}
```
**v2.18.0 note:** `drain_resist` now blocks `draining` (the ring-of-strength-drain HP tick) — the display name "Drain Resist" now matches behavior. `diseased` is retained for symmetry with poison_resist.

### `DAMAGE_IMMUNITY: dict[damage_type -> immunity_status]`
Used by `Player.take_damage` to short-circuit incoming typed damage:
```python
{'fire': 'fire_resist', 'cold': 'cold_resist',
 'lightning': 'shock_resist', 'poison': 'poison_resist',
 'drain': 'drain_resist', 'magic': 'magic_resist'}
```

### `SHIELD_IMMUNITY: dict[damage_type -> shield_status]`
Overrides `DAMAGE_IMMUNITY` when the player has a shield effect active:
```python
{'fire': 'fire_shield', 'cold': 'cold_shield'}
```

### `_EXPIRE_MSGS: dict[effect_id -> (text, message_type)]`
HUD log line fired when a timed effect expires. Message types: `'info'`, `'success'`, `'warning'`, `'danger'`. v2.18.0 audit added the previously-missing entries for: `doom_dot`, `petrifying`, `armor_crack`, `sundered`, `deep_wound`, `ruptured`, `impaled`, `heal_blocked`, `blade_flow`, `save_guard_*` (4), `fear_immune`, `control_immune`, `parry_armed`, `riposte_armed`, `see_invisible`, `warning`, `searching`, `truesight`, `dark_vision`, `identify_sight`, `life_save`, `reloading`, `boomstick_aoe_next`, `crit_buff`, `stand_ac`, `melee_dmg_reduction`.

### Material categorization (gear damage from rust, acid and fire)

What wear can touch is read from the item's **material file** (`data/materials/armor` or `weapons`, via `status_effects.material_wear`): its `material_class` and what it resists: a weapon material's `resistances` (fire, corrosion, rust), an armour material's `protection` under x1 (since slice 4, which replaced the armour files' lists: dragonhide sheds fire, so it does not scorch), `corrosion_immune` and `fire_resistant` among its `special_properties`. The wear each armour material can take was checked unchanged by that move. Winning-build slice 2 (2026-11-13); before it, hand-kept name sets were the whole rule and missed canvas, cured / boiled / studded leather, spider silk, elven silk, oak and ash (all treated as rustable metal).

| Wear | Touches | Never |
|---|---|---|
| **rust** (`_can_rust`) | classes `metal`, `rare_metal` (iron, steel and their alloys) | copper, bronze, tin, silver, gold, hematite, mithril (`_NON_FERROUS`); every leather, cloth, hide, wood and magical metal; a material whose resistances say `rust`; every unique or legendary piece, unless its lore says it rusts (below) |
| **acid** (`_can_corrode`) | everything but the classes below | `magical_metal`, `dragon_material`, `exotic_metal`; a material resisting `corrosion` or `acid` |
| **fire** (`_can_scorch`) | `leather`, `studded_leather`, `hide`, `cloth`, `wood`, `rare_wood`, `exotic_organic` | a material resisting `fire` (dragonhide, ironwood, worldtree...) |

**No legend rusts** (round 3, 2026-11-14; Brandon: "Legendary weapons don't need to rust, unless lore says so; they are magical"). Before any of the rules above, `_can_rust` asks `is_legend(item)`: a unique (`is_unique`) or a piece made of "legendary" never rusts, whatever its metal (Zireael's steel, Caliburn's enchanted iron, the Breastplate of Joan), unless its own data says `"rusts": true`, backed by its lore (`items.lore_rust_ids`, read from `data/items/*.json` by id, so an old save's piece follows today's file). The one such piece is **Achilles's Spear**, whose lore tells of the rust scraped from its point that healed King Telephus. Every rust path asks this one check: the rust trap's water, the rust monster's feelers, the Bloomleaf Cloak's ward (it speaks only when something worn could rust) and the card's "rusts" / "never rusts" (`gear.wear_words`). Tests: `tests/test_legends_do_not_rust.py`.

A named piece whose material has no file ("hardwood", "divine bronze", "legendary") falls back to the old name sets (`_RUSTPROOF`, `_ORGANIC`, `_FLAMMABLE`); for rust, then to its own `metal` word (the one `gear.is_metal` reads), then to whether the word names iron or steel. Anything else does not rust: before bug bash WB-D05 every such word rusted, the linen Linothorax of Alexander and the Mantle of Elijah among them. (Since round 3 a named piece never reaches the rust fallbacks: it is a legend.) The `corroding` / `burning` tick branches pick a random worn target and take a point off through `items.wear_down` (`_corrode_random_gear`: 25% a tick; `_scorch_random_gear`: 20%).

**Rust has one entry point:** `rust_worn_gear(player, source=None, rng=None) -> (message, kind) | None`. One worn piece that can rust (weapon, ranged weapon, shield, armour) loses a point through `items.wear_down` (-1 plus, or -1 level on a minor piece; a smith's repair gives it back), unless `Player.is_rustproof()`: any worn item whose `special_properties` has `"rustproof_wearer": true` keeps rust off everything (the line names it). The one such piece is the **Bloomleaf Cloak** (`data/items/armor.json` `bloomleaf_cloak`), worn by Old Nickel and dropped when he dies (`src/emberpup_encounter.py` (BloomleafMixin)); it is also the only thing that keeps the rain off the Emberpup, so the hero chooses between them. `None` when nothing worn can rust. Callers: the rust trap (`main.py`, water) and the rust monster's feelers (its attack's `effect: "rust"`, `Monster._apply_attack_effect`: no saving throw; the gloves' touch guard can still turn it aside).

## Flow — public API

### `apply_effect(player, effect: str, duration: int) -> bool`
The one write path for status durations. Returns True if applied; False if blocked.

Decision order:
1. **`_RESIST_BLOCKS` short-circuit**: if any resist in the table covers this effect AND the player has that resist active, return False immediately. (This is why save bonuses do not stack with immunity.)
2. **Permanent (`-1`) guard**: if the effect is already permanent, refuse any further write.
3. **`duration == -1` write**: set permanent.
4. **`effect in CONTROL`**: clamp duration by `CONTROL_CAP`. Then:
   - **HARD_CONTROL**: refuse re-apply if already active OR if `control_immune` is in the grace window. Otherwise set `min(duration, MAX_EFFECT_DURATION)`.
   - **SOFT_GRACE** (`confused`, `forgetting`, `slowed`, `charmed`): refuse while it runs (no refresh); otherwise set it and mark the bout (`_soft_bouts`). Before step 1, a bout cured since the last tick earns its recovery turns (`_recover_cured`), which then block it.
   - **SOFT_CONTROL** (the rest): refresh to `max(current, duration)`, clamped. Never stacks.
5. **Everything else**: what `statuses.refresh` names runs to the longer dose, never the sum; the rest (buffs, resistances, draining) adds, clamped to `MAX_EFFECT_DURATION`. A dose is capped by `statuses.caps` unless its caller gives a `cap` (a price the game announces).

**Call sites:** every effect-application path in the game routes through here, usually via `Player.add_effect`. Direct call sites include `food_system.py:289` (cooked wards write `save_guard_*` + magnitude), `game_magic.py` self-buff dispatchers (haste/shield/invis via `_SELF_BUFF_DURATIONS`), spell/wand effect handlers, and chain-combat weapon procs.

### `apply_debuff_with_save(player, effect, duration, dc) -> (applied: bool, message: str)`
MONSTER-inflicted debuffs route here (not through plain `apply_effect`). Two-gate model: the caller already passed the monster's `effect_chance` (skill at landing the blow). Here the player rolls `d20 + stat_mod + save_bonus` vs the DC:

```python
stat  = SAVE_STAT.get(effect)     # 'CON' / 'WIS' / 'DEX' or None
mod   = (int(getattr(player, stat, 10)) - 10) // 2
bonus = player.save_bonus_for(stat)
roll  = randint(1, 20) + mod + bonus
```

Branches:
- **Poison:** `venom.lands`: a CON save halves the dose; the bite's venom is noted. **No SAVE_STAT entry** (bleed, burning, disease, doom_dot, …): the save roll is skipped, but `save_bonus_for('CON')` reduces the applied duration by a flat amount (floor 1). `applied = player.add_effect(effect, max(1, duration - sb))`. Message: `"You are <effect>!"` on success, `""` on refuse. (v2.18.0 fix — previously bypassed `save_bonus_for` entirely, so Torque of Lugh's `{all: 3}` didn't help against DoTs despite the text.)
- **`roll >= dc` + HARD_CONTROL**: full negate. Returns `(False, "<flavor> throws off the <noun>!")`. Flavor by stat: CON → "Your hardy constitution"; WIS → "Your strong will"; DEX → "Your quick footwork".
- **`roll >= dc` + SOFT_CONTROL**: half duration (floor 1). `applied = player.add_effect(effect, max(1, duration // 2))`. Message: `"<flavor> blunts the <noun> — it barely takes hold."`.
- **`roll < dc`** (failed save): full duration. `applied = player.add_effect(effect, duration)`. Message: `"The <noun> takes hold!"`.

Flavor messages read as player-feels-stat, not dice-and-DCs. Effect nouns via `_EFFECT_NOUN` (e.g. `'stunned' → 'stun'`, `'petrifying' → 'petrification'`). The return `applied` is always `add_effect`'s result — if a resist short-circuits even after a failed save, nothing lands.

**Call sites:** `monster.py:705` (generic monster-attack path, covers all ~332 monster melee/attack debuffs — see SYSTEMS_AUDIT.md §9 VERIFIED OK). Gaze attacks also route through this.

### `tick_all(player, dungeon=None) -> list[(text, type)]`
Advance one turn for every effect in `player.status_effects`. Returns a batched list of HUD messages. May mutate `player.hp` / stats / `status_effects`. Called once per player turn from `main.py:3158` (`self.player.tick_effects()`).

Flow:
1. **Grendel-grip pre-tick** (Coif of Beowulf armor proc): clears `paralyzed` / `strangulation` / `sleeping` immediately. The grip that strangled Grendel keeps you free.
2. **Per-effect dispatch** (ordered as they appear in `player.status_effects`):
   - `poisoned` + not `poison_resist` → `venom.strength` (the venom, or `DOT_SHARE` of max HP for a poison with none; halved by Venom Ward) as poison damage; "The poison burns through you!"
   - `diseased` + not `poison_resist` AND not `drain_resist` → 8% / turn STR or CON -1 (dispatches `_disease_drain:<stat>:1` for Paracelsus quirk; UI line "The disease saps your strength! <stat> -1."). Since AI-1 (Grave Rot, `src/grave_rot.py`) it also stops natural regeneration (`main._tick_hp_regen`) and halves every heal that goes through `Player.restore_hp` (potions, spells, prayers, meals; not a drain wand's draw, a kill's heal or a worn piece's regeneration, which do not use it) while it lasts, and a monster's disease lasts its `effect_duration` times its kind's `disease_linger` (1 unless its lore makes it linger: mummy rot 10, the plague-bringers 4-8; at most `MAX_EFFECT_DURATION`, 60). The Mercy prayer at a chain of 4 cures it (`game_divine._resolve_simple_prayer`).
   - `strangulation` → 2 physical damage; "You are being strangled!"
   - `regenerating` → +1 HP if below max
   - `petrifying` → the count's line each turn by `effect_rules.stone_stage`; a LETHAL bout emits `_petrify_death` at **`val==1`**, any other expires into 1 turn of paralysis
   - `bleeding` → 1 physical damage; "You are bleeding!"
   - `doomed` → 12% / turn -1 HP; "The doom curse gnaws at your life force!"
   - `draining` → 17% / turn -1 HP (now gated by `drain_resist` via `_RESIST_BLOCKS`); "The ring drains your life force!"
   - `burning` + not fire_resist/fire_shield → 1 fire damage + `_scorch_random_gear` (20% chance of -1 enchant on a flammable equipped item, floor -3)
   - `corroding` → `_corrode_random_gear` (25% chance of -1 enchant on a non-rustproof equipped item, floor -3)
   - `teleportitis` → 4% / turn emits `_teleport` signal
   - `weakened` / `frozen` — passive flags read at combat sites, no per-turn work here
3. **Decrement + queue expiry**: `val > 0` decrements by `TICK_STEPS` (1; Slowed 2); Knocked Down waits for the hero (`UNTIL_ACTED`); expired keys go to `to_expire`.
4. **Expiry cleanup**:
   - Any HARD_CONTROL expiry grants `control_immune = GRACE_TURNS` (3 turns).
   - A `confused` expiry grants Clear-Headed (`confuse_immune = CLEAR_HEADED_TURNS`, 3); so does a confusion cured since the last tick (`_recover_cured`, after the expiry loop).
   - `save_guard_*` expiry pops the magnitude from `player._save_guard[<cat>]`.
   - `heroism` expiry: `apply_stat_bonus('STR', -2)`.
   - `brilliance` expiry: `apply_stat_bonus('INT', -1)` + `apply_stat_bonus('WIS', -1)`.
   - `stand_ac` expiry: `_stand_ac_bonus = 0` + `_stand_counter_pct = 0`.
   - `berserk` expiry: `player.STR -= _berserk_str_bonus` (direct STR write, not via `apply_stat_bonus`, because berserk is a combat damage bonus not a full stat buff).
   - Append `_EXPIRE_MSGS[effect]` to the output.

**Special signals** returned via messages (consumed by `main.py`):
- `'_teleport'` — teleport the player to a random tile.
- `'_petrify_death'` — player fully turns to stone.
- `'_disease_drain:<stat>:1'` — dispatch to Paracelsus quirk hook.

### `Player.add_effect(name, duration) -> bool`
Thin wrapper around `apply_effect` with a few additional policy gates:
- **Hermes quirk**: `hasted` duration is doubled when `quirk_progress.hermes_active`.
- **Will to Power hero passive**: `feared` / `charmed` refused when HP ≤ 30% of max.
- **Fear immunity**: `feared` refused while `fear_immune > 0` (Ash Williams' berserk chain ≥ 3).
- All other effects pass through to `apply_effect` unchanged.

(The retired Perseus "halve all debuff durations" branch previously lived here; it was converted to a `{all: +2}` save bonus and the branch deleted — see save_bonus.md history.)

### `Player.has_effect(name) -> bool`
`self.status_effects.get(name, 0) != 0`. The non-zero check means `-1` (permanent) counts.

### `Player.tick_effects() -> list[(msg, type)]`
Thin wrapper around `tick_all(self)`. Called once per player turn from `main.py:3158`.

## Invariants (don't break)

- **One-write-path:** all duration writes go through `apply_effect` (or `apply_debuff_with_save` which calls `add_effect` which calls `apply_effect`). The only in-tree exception is `grendel_grip`'s direct zeroing in `tick_all` and expiry stat-reversals.
- **`_RESIST_BLOCKS` short-circuits before saves:** full immunity never routes through the save math. If you move a check past this branch, you break the "resists + saves don't overlap" rule.
- **HARD_CONTROL anti-permalock:** cannot be refreshed, re-applied while active, or re-applied within the 3-turn grace. Monsters that reliably cast paralysis must never permalock. Grace window = `GRACE_TURNS = 3`.
- **Confusion never chains:** a running confusion is not refreshed, and every bout, however it ends, is followed by `CLEAR_HEADED_TURNS` of `confuse_immune`. The quiz scramble's whole safety rests on it.
- **Nothing a monster lays to last stacks:** a bout is not refreshed (control, confusion, slow, charm, Forget), or runs to the longer dose (`statuses.refresh`, Weakened). Only buffs and the few debuffs not named there add.
- **`MAX_EFFECT_DURATION = 60`:** every write clamps at this. CONTROL further clamps by `CONTROL_CAP`.
- **Permanent (`-1`) effects are immutable** via `apply_effect` — direct `status_effects[k] = -1` writes exist (intrinsic resistances from gear) and must be explicit.
- **`save_guard_*` is a BUFF**, not a DEBUFF — register in BUFFS, or cleanses will wipe the player's own wards.
- **`berserk` is a BUFF only (v2.18.0 fix).** It is NOT in DEBUFFS. If you double-classify, dispel_magic's dispatch becomes ambiguous.
- **`doom_dot` lives in DEBUFFS + has an `_EXPIRE_MSGS` entry.** Previously missing from both — don't re-regress.
- **`drain_resist` blocks `draining` + `diseased`.** (v2.18.0 — "Drain Resist" display name now matches behavior.)
- **`petrifying` is in HARD_CONTROL** (v2.18.0 fix). Save NEGATES; a halved duration could still kill via the val==1 death tick.
- **`stunned` stays in HARD_CONTROL** despite being semantically soft — removing it reopens the fast-monster stunlock death-spiral.
- **DoTs still land on saves** (poison: a save halves the dose; bleed/burning/doom_dot): save only reduces duration by `save_bonus_for('CON')`, min 1 turn. "Resource loss IS the penalty."
- **`control_immune` is a BUFF.** It's set BY tick_all when hard-control expires, and consumed BY apply_effect's HARD_CONTROL guard. Never set it from gameplay code directly.

## Interactions

- **[save_bonus](save_bonus.md)** — the gradient layer between "no defense" and "immunity." `apply_debuff_with_save` reads `player.save_bonus_for(stat)` as the +N on the d20 roll. Non-SAVE_STAT effects use `save_bonus_for('CON')` for duration reduction.
- **[quiz_engine](quiz_engine.md)** — identify-v3 failures apply `stunned 10t`. Timer modifier is read from `has_effect('blinded' / 'stunned' / 'hallucinating' / 'blessed')` (see quiz_engine.md "Status-effect timer modifiers"). Confusion has no clock modifier since 2026-11-19: it scrambles the quiz's words until they settle (`quiz_engine.scramble_runs`, quiz_engine.md "Confusion scrambles the words").
- **[combat](combat.md)** — chain-combat-v2 weapon procs write statuses (`armor_crack`, `sundered`, `deep_wound`, `ruptured`, `impaled`, `blade_flow`, `melee_dmg_reduction`) via `apply_effect`. `take_damage` checks `DAMAGE_IMMUNITY` / `SHIELD_IMMUNITY` short-circuits.
- **[magic](magic.md)** — self-buffs use `_SELF_BUFF_DURATIONS` (game_magic.py:1848) to scale duration by chain_scale. Chain-5 shield spell → 12 × 5 = 60t (capped at MAX_EFFECT_DURATION). `dispel_magic` / `cancellation` / `drain_magic` strip BUFFS from target; `abjuration` currently strips ALL statuses (SYSTEMS_AUDIT.md §9 P1 flagged — should match the others).
- **[monsters](monsters.md)** — monster attacks route debuffs through `apply_debuff_with_save` at `monster.py:705`. 17/17 effect ids in monster attacks map to real EFFECT_INFO entries (VERIFIED OK).
- **[items](items.md)** — permanent accessory buffs (`life_save`, `sustained`, `truesight`, `dark_vision`, `identify_sight`, `spell_turning`) are written as `-1` on equip, cleared on unequip. Resistances from gear can be timed OR permanent.
- **[food_system](food_system.md)** — cooked wards (`save_guard_CON/WIS/DEX/all`) write a BUFF status + magnitude via `_TEMP_POWER_REMAP` → `food_system.py:289`. See [save_bonus.md](save_bonus.md).
- **[karma_prayer](karma_prayer.md)** — prayer branches apply/strip statuses (Blessed, Divine Intercession = `invulnerable`, Fisher King healing, etc.).

## History of major decisions

- **Mid-2026** — `apply_debuff_with_save` added (D&D-style saves). The engine switched from flat "effect_chance" rolls to a two-gate model (monster hit chance → player save). Massive playability win.
- **2026-05-30** — Chain-combat-v2 statuses added (armor_crack / sundered / deep_wound / ruptured / impaled / blade_flow / melee_dmg_reduction). Grendel-grip tick-clear added for Coif of Beowulf.
- **2026-06-03** — Save-bonus audit (`docs/design/save_bonus_audit.md`); Option B shipped. `save_guard_*` ward family added; Perseus halve-debuffs branch retired → `{all: +2}` save bonus.
- **2026-08-06** — Identify v3 ships. Stun-on-fail becomes the ID failure cost (not a mastery hit). `stunned` kept in HARD_CONTROL for anti-stunlock despite soft semantics.
- **2026-11-19** — Confusion's quiz cost became the scramble (its ×0.55 clock cut removed), and confusion got the hard-control shape: no refresh while it runs, 3 turns Clear-Headed after (`SOFT_GRACE`, `data/confusion.json`).
- **2026-10-02 (v2.18.0 audit sync wave):**
  - `petrifying` moved into `HARD_CONTROL` (saves now negate instead of halving).
  - `berserk` removed from `DEBUFFS` (was double-classified; now BUFF-only).
  - `doom_dot` added to `DEBUFFS` + `_EXPIRE_MSGS`.
  - `drain_resist` now blocks `draining` in `_RESIST_BLOCKS` (display name matches behavior).
  - `apply_debuff_with_save` non-SAVE_STAT branch now respects `save_bonus_for('CON')` (Torque of Lugh `{all: 3}` finally helps against poison/bleed).
  - 13 spell duration descs synced to code values (stoneskin 30→25, greater_haste 25→10, phase_door 12→15, reflect 20→15, counterspell 15→12, detect_monsters 15→20, imprisonment 40→60, paralyze 10→8, hold_monster 5→8, slow 6→10, fear 8→10, magic_shield_spell distinct from mage_armor_spell at T3=20, annihilate / power_word_kill chain=5 fossil deglazed).
  - 24+ `_EXPIRE_MSGS` entries added for previously-silent expiries (armor_crack, sundered, deep_wound, ruptured, impaled, heal_blocked, blade_flow, save_guard_*, etc.).
  - `_EFFECT_NOUN['stunned']` fixed: 'daze' → 'stun' (save-flavor now matches expire-flavor).

## Testing
- `tests/test_quiz_scramble.py` — confusion's recovery: no refresh while it runs, Clear-Headed for 3 turns after expiry and after a cure, a confusing monster every turn never keeps the hero confused back to back, the trophy's permanent Clear-Headed untouched, an old save's confusion.
- `tests/test_status_lock.py` (308 lines) — pins:
  - HARD_CONTROL cannot be re-applied while active.
  - Single-application CONTROL_CAP enforcement.
  - SOFT_CONTROL refreshes (never stacks).
  - DoTs + buffs still stack additively.
  - Post-hard-control grace window blocks relock.
  - "Reapply every turn" cannot permalock.
  - Save NEGATES hard control.
  - Save messages are flavor, not math.
  - Save MINIMIZES soft control to half.
  - Failed save applies full duration but still capped.
  - `SAVE_STAT` mapping sanity.
  - `save_bonus_for` sums permanent lanes + hard-cap.
  - Timed-ward companion gated by status + capped at +3.
  - `_save_guard` cleared on ward expiry.
  - Save bonus actually improves save odds (statistical test).
  - Cooked-ward grants status + sets capped magnitude.
  - Cooked-ward amount clamped to +3.
  - Cooked-ward defaults to +2 when unspecified.
  - Control-resist remap targets are wards (not plain resists).
  - Bad-food control routes through save-failure landing.
  - Bad-food control save can negate hard control.
  - Bad-food noncontrol debuff unchanged.
- `tests/test_effect_wiring.py` — pins each effect's registration symmetry (EFFECT_INFO ↔ BUFFS/DEBUFFS presence).
- `tests/test_death_from_status_tick.py` — pins Stunned-10t-on-identify-fail still ticks + expires cleanly.
- `tests/test_effect_duration_dice.py` — pins effect duration dice parse + scale correctly.
- `tests/test_buc_effects.py` — pins BUC-driven buff/debuff application paths.

## Known rough edges

From SYSTEMS_AUDIT.md §9:
- **P1** — `game_magic.py::abjuration` (line 1065-1086) calls `target.status_effects.clear()` on the monster, stripping player-applied DoTs (poisoned/burning/petrifying/bleeding). Inconsistent with `cancellation` / `dispel_magic` / `drain_magic` which strip BUFFS only. Pre-v2-audit dispatch rot.
- **P1** — `game_magic.py::magic_missile` handler (line 1876) bypasses `_spell_damage` and `MAGIC_TIER_MULT`. Force-family spells under-scale relative to all other damage families.
- **P2 (closed 2026-11-22)** — `stunned` is a felt effect behind the gate (double vision, one fall, one drop); it stays in HARD_CONTROL against stun-locks.
- **P2** — `spells.py::elder_scream` — `mp_cost: 10` at `tier: 2`. Outside T2 5-8 MP band.
- **P3** — `MAX_EFFECT_DURATION=60` with additive stacking on non-CONTROL effects is asymmetric with CONTROL's refresh-max. Non-CONTROL stacking stays additive by design (regen + regen = longer regen), but worth noting.
- **P3** — Alternate potion label `hallucinating_pot` has identical semantics to `hallucinating`; two ids exist so UI can tell them apart in flavor text. Verify both are in all the right sets if you touch either.
- (Fixed by the kitchen rebuild, 2026-11-14: cook_outcomes.json is gone, and every dish names a canonical status id. `food_system._TEMP_POWER_REMAP` is dormant.)
