# Combat (Chain v2)
**Status:** v2.18.0 (shipped 2026-10-02)
**Code:** `src/combat.py` (2186 lines), `src/game_combat.py` (CombatMixin, 2567 lines), `src/chain_passives.py`, `src/hero_specials.py`, `src/monster.py::take_damage`
**Data:** `data/items/weapon.json` (96 uniques), `data/materials/weapons/*.json` (54 materials), `data/monsters.json` (resistances / weaknesses / tags / is_boss / dragon_scales)
**Related docs:** [weapons_and_materials](weapons_and_materials.md) · [monsters](monsters.md) · [items](items.md) · [status_effects](status_effects.md) · [magic](magic.md) · [progression](progression.md) · design history: [`docs/design/chain_combat_v2.md`](../design/chain_combat_v2.md), [`docs/design/weapon_specials_v2_14.md`](../design/weapon_specials_v2_14.md), [`docs/design/uniques_v2_14.md`](../design/uniques_v2_14.md)

## Purpose

Combat is the game's primary quiz loop. Every strike runs a **chain-mode math quiz** — the player answers simple math questions in sequence, and each correct answer multiplies the per-hit damage via a polynomial curve. The player decides when the swing lands by pressing SPACE, running out of time, or missing a question. Chain-length drives damage, status procs, cleaves, and class-specific signature effects.

The chain quiz is the only mechanic the player will interact with hundreds of times per run, so its tuning (per-weapon exponent, per-class ladder, boss-tag gating) is the load-bearing combat axis of the whole game.

## Design intent

- **Chain IS the crit.** v2.14.0 retired `crit_multiplier` entirely. The polynomial `chain**exponent` ladder delivers all the "big number" reward. No flat crit chance, no crit-dice, no "next hit auto-crits" state. Harpe's petrify, Kusanagi's surround-bonus, and Soul Reaver's innocent-kill trigger were all rewired away from crit.
- **Math skill = combat skill.** WIS = quiz-timer seconds. Simple math drops the floor; stacking long chains lifts the ceiling. See `docs/design/chain_combat_v2.md` for the authoritative Timer section — `SUBJECT_TIMER['math'] = (0, 1.0)` makes WIS the sole timer source.
- **Chain 20 is reachable on floor 1.** A fast player can chain 20 on their first swing. Chain-20 effects are rewarding but not instant-kill — any instant-kill at chain 20 would be oppressive against bosses. See [`docs/design/weapon_specials_v2_14.md`](../design/weapon_specials_v2_14.md) §Core principles #5.
- **One rung fires, not all of them.** `_chain_special_tier()` returns the HIGHEST qualifying threshold; chain 20 does NOT additionally fire chain 15 / 10 / 5 effects. The chain-20 package is designed as a complete payoff for that rung.
- **No forced monster movement.** Knockback / pull / teleport are player-opt (dagger's throw, mace's `knockback` flag) — the class chain-special ladder never moves monsters, because moving them is unpredictable and often bad for the player.
- **Weapons telegraph their shape.** Each weapon class has a unique ladder (dagger stacks DoTs, 2h-warhammer area-stuns, bow goes blind-then-vitals). Uniques inherit the class ladder and layer distinctive passives (lifesteal, lightning splash, boss-doom DoT) on top.

## Data model / schema

### Weapon fields that drive combat (loaded in `items.py::Weapon.__init__`)

| Field (JSON key) | Type | Role |
|---|---|---|
| `base_damage` (`baseDamage`) | int | Flat per-hit base before multipliers |
| `chain_exponent` (`chainExponent`) | float \| None | Polynomial path: `mult = chain**exponent`. If set (>0), takes precedence over `chain_multipliers`. Common templates ship 1.15. Uniques: all 96 carry `chain_exponent: 1.15` after the v2.14.0 rebase (see `docs/design/uniques_v2_14.md`). |
| `chain_multipliers` (`chainMultipliers`) | list[float] | Legacy per-rung array (5 entries). Still read as fallback when `chain_exponent` is absent. |
| `damage_types` (`damageTypes`) | list[str] | For weakness/resistance lookup. Material is appended at use-site. |
| `material` | str | Looked up in `data/materials/weapons/<id>.json` for `damage_mult`, `effective_against`, `vulnerabilities`. |
| `enchant_bonus` | int | +N flat damage. Weapon cap 5 (`items.py::ENCHANT_CAP`); Panoply of Hephaestus raises to 6. |
| `stun_chance` / `bleed_chance` / `poison_chance` / `burn_chance` / `confuse_chance` / `freeze_chance` | float | On-hit status rolls. |
| `ignore_shield` | bool | Bypasses monster `shielded` 0.5× |
| `ignore_resistances` | bool | Clamps `dtype_mult` to 1.0 (Gram reforged) |
| `cursed_miss_backlash` | int | HP damage on chain-0 (Tyrfing) |
| `class_mechanic` | str | 22-entry template-driven ability (see §Class mechanics in [weapons_and_materials](weapons_and_materials.md)) |
| `effects` | dict | `{status, effect_chance, effect_duration}` — on-hit status (v2.17 wire-up for 4 quest mythics) |
| `effective_against` | list[str] | Unique-only anti-tag array. +50% damage to matching tags. **Compositional weapons must NOT set this** — material already carries it, see `combat.py:1068` guard. |
| 149 unique-only proc flags | mixed | Documented in [weapons_and_materials](weapons_and_materials.md) §Unique procs |

### Monster fields read during combat (`monster.py`)

| Field | Role |
|---|---|
| `hp` / `max_hp` / `alive` | HP tracking; `take_damage` writes `alive=False` at hp 0 |
| `resistances` / `weaknesses` | list[str] of damage-type strings. `_damage_multiplier` picks the best (max) across weapon's declared damage types. |
| `tags` | list[str]. `_tag_match` consults these for material.effective_against, per-weapon anti-tag arrays, and `is_boss`. |
| `is_boss` | bool. **v2.18.0 fix:** `Monster.__init__` now reads from JSON (was dropped on load, breaking boss-immunity for 10 mini-bosses). |
| `dragon_scales` | float 0..1. Multiplicative physical reduction (Fafnir). Bypassed by `ignore_resistances`, `blade_flow` stacks, or chain-special `_chain_bypass_dr`. |
| `status_effects` | dict[str,int]. Keys include `armor_crack`, `sundered`, `deep_wound`, `blade_flow`, `ruptured`, `impaled`, `bleeding`, `poisoned`, `burning`, `stunned`, `paralyzed`, `shielded`, `heal_blocked`, `doom_dot`, `petrifying`. |
| `drain_heals_self` | float 0..1 fraction. Vampire-family drain attacks heal the monster for `actual * drain_heals_self`. |

## Flow — public API

### Entry points

- **`combat.player_attack(player, monster, quiz_engine, on_complete, ammo=None)`** — starts a chain-mode math quiz. `on_complete(damage, killed, chain, **kwargs)` fires when the quiz ends. `ammo` present ⇒ ranged shot (uses `player.ranged_weapon`), absent ⇒ melee swing (`player.weapon`).
- **`combat.can_melee_attack(player, monster)`** — reach check. Ruyi Jingu Bang's `chain_modulated_reach` is read with `max(values)` for targeting (known lie at chain 0 — see audit).
- **`combat.can_ranged_attack(player, monster, dungeon)`** — ammo check + reach check (`weapon.reach + (PER-10)//3`). Line-of-sight NOT required (projectile traces at fire time).
- **`combat._line_of_sight(x0, y0, x1, y1, dungeon)`** — Bresenham with corner-cut guard.
- **`combat.get_line_tiles(...)` / `combat.get_cone_tiles(...)`** — tile walks for pierce / cleave / cone shots.
- **`game_combat.CombatMixin._start_combat(monster)`** — melee opener. Primes side-channel refs (`player._combat_monsters_ref`, `_combat_game_ref`, `_combat_pets_ref`), calls `player_attack`.
- **`game_combat.CombatMixin._fire_ranged(monster)`** — ranged opener. Pulls one ammo from inventory BEFORE the quiz (chain-0 still burns ammo — see audit P3). Calls `player_attack` with `ammo=...`.
- **`game_combat.CombatMixin._on_monster_killed(monster, *, chain_score, ranged, ...)`** — single point for boss popups, seal tracking, treasure drops, and corpse spawning.
- **`combat.apply_knockback(player, monster, dungeon, monsters)`** — pushes monster 1 tile away. No-op if blocked.

### Combat loop (one swing)

```
_start_combat(monster)                              # game_combat.py
  → player_attack(player, monster, quiz_engine, on_complete)
      → quiz_engine.start_quiz(mode='chain', subject='math', tier=weapon.quiz_tier,
                                base_seconds=player.get_quiz_timer('math'), ...)
      → _callback(result)                           # inside player_attack
          chain = result.score + chain_bonus (armor chain_bonus, Parashu carry,
                  Glamdring orc-glow, Fail-not / Gungnir / Hrunting save,
                  Harpe warmup skip, Skofnung low-HP window)
          if chain == 0:
              Tyrfing cursed_miss_backlash damage
              on_complete(0, dead, 0); return
          base = weapon.base_damage (or roll dice fallback, or fist STR scaling)
          + ranged stat bonuses (STR + PER /4 for bow/sling/dagger/spear; PER-only for crossbow)
          mult  = chain ** chain_exponent    (polynomial path — all v2.14.0+ weapons)
          mult *= _apply_chain_class_pre_damage(player, weapon, chain)
                   # may set player._chain_bypass_dr; bow C20 returns 2.0 vitals mult
          dtype_mult = _damage_multiplier(weapon.damage_types + material, monster)
                   # 0.5 resist / 1.0 neutral / 1.5 weakness, max over types
          dtype_mult += unique anti-tag (if is_unique)
                      + Anduril undead_multiplier
                      + Akinakes prophecy tag
                      + Mistilteinn resistant-at-max
                      + Robin Hood stealth bonus
                      + Oathkeeper adjacent-pet
          mult *= Kusanagi surround (3+ adj) × 1.25
          shield_bypass = ignore_shield OR blade_flow stacks OR _chain_bypass_dr
          if monster.shielded and not shield_bypass: dtype_mult *= 0.5
          _pre_mech: versatile +20% 2H, master_strike +15% at chain>=3,
                     str_bonus_range_7 (composite bow), at-max anti_heavy / armor_pierce /
                     ignores_all_armor / ignores_half_armor
          hero passives: will_to_power +30% @ <30%HP, witcher_mutations +20%, niten_ichi_ryu +15%
          buffs: crit_buff +50% (legacy, consumed one charge), berserk +30%
          BUC: +1 blessed / -1 cursed
          Chandrahasa low_hp_mult up to 2× at 0% HP
          str_factor = 1 + max(0, STR-10)*0.03   (MELEE ONLY — ranged keeps 1.0 to avoid STR+PER double-dip)
          if (blade_flow or _chain_bypass_dr) and dtype_mult < 1.0: dtype_mult = 1.0
          damage = max(1, round((base + enchant + ammo_bonus + buc) * mult * dtype_mult * str_factor * low_hp_mult))
          if monster has armor_crack / deep_wound: damage *= 1 + min(0.50, 0.25*nflags)
          empowered spell buff: damage *= 3 (consumed)
          blade_flow stack consumed; _chain_bypass_dr flag consumed
          dragon_scales reduction (unless _skip_dr): damage *= 1 - dragon_scales
                                                    OR *4 if player in_pit (underbelly strike)
          per-tag bonus damage dice (Anduril +1d8 undead, Glamdring goblin, etc.)
          _death_omen_target, Helm of Leonidas +3 @ <20% HP, Cannae Encirclement +N adj,
          Lorica Caesar et_tu +50%, Hippolyta amazon_charge +50%, Dragonslayer Ring tag bonus,
          Bracers of Arjuna gita_focus +50% (first ranged / floor)
          actual = monster.take_damage(damage)
          _apply_chain_class_post_damage(...)         # see §Class chain-specials
              applies target statuses, AoE damage/statuses, player buffs
          Harpe chain-15 petrify, Sword-of-Michael holy_smite flavor,
          Cu Chulainn riastrad every-3rd-hit bleed
          weapon procs: stun_chance / bleed_chance / poison_chance / burn_chance /
                        confuse_chance / freeze_chance / weapon.effects status
          Gae Dearg heal_blocked, Sword-of-Damocles counter tick + auto-kill,
          Penitent karma tally, Parashu chain_no_reset tag, Meleager boar-spear reveal,
          Curtana spare_kill, Mjolnir chain-lightning, Zulfiqar every-hit secondary,
          Gandiva multi-arrow, Rod of Moses plagues table, Laevateinn boss doom_dot,
          Spear of Longinus weep-heal, Sudarshana return-to-hand ward,
          Soul Reaver innocent-kill → blade_flow +1, Ring of Gyges invis-attack karma,
          Echidna random status, Cadmus / Vel / Shamshir summon ally pet,
          lifesteal_percent, kill_heal_amount, growing_power +1 base per N kills,
          Khopesh of Anubis +max_hp per kill
          class_mechanic post-hit: bleed/stun/backstab/disarm/concussion/riposte/
                                   returning_blow/parry_armed/rapid_shot
          cleave_at_max / cleave_at_max_plus_bleed → on_complete(..., cleave_dmg=...)
          sling free_stones ricochet 25% → on_complete(..., ricochet_dmg=...)
          on_complete(actual, killed, chain, stunned=.., knocked=.., crit=False,
                      poisoned=.., burned=.., confused=.., petrified=.., healed=..)
```

### `on_complete` kwargs the melee/ranged callers consume

- `stunned` / `knocked` / `poisoned` / `burned` / `confused` / `petrified` / `healed` — flavor + flag used for message formatting.
- `crit` — **always False** since v2.14.0. Kept in the signature for compat.
- `cleave_dmg` — int. Caller walks adjacent monsters and applies the AoE.
- `ricochet_dmg` — int. Sling signature; caller picks adjacent and applies.

## Peak-chain damage formula

The polynomial path is the only path for all 96 uniques (`chain_exponent = 1.15`) and every v2.14.0+ common template. The relevant block is in `combat.py:1003-1014`:

```python
_chain_exp = getattr(weapon, 'chain_exponent', None) if weapon else 1.15
if _chain_exp and _chain_exp > 0:
    mult = float(chain) ** float(_chain_exp)
    multipliers = None  # signals "polynomial path" to blocks below
else:
    multipliers = weapon.chain_multipliers if weapon else _DEFAULT_MULTIPLIERS
    mult        = multipliers[min(chain - 1, len(multipliers) - 1)]
```

The full final-damage expression at `combat.py:1272`:

```python
damage = max(1, round((base + enchant + ammo_bonus + buc_bonus)
                      * mult * dtype_mult * str_factor * low_hp_mult))
```

Reference multipliers at the default `chain_exponent = 1.15`:

| Chain | mult (polynomial) | Example: iron longsword base 5 | mithril 2h sword base 19 |
|---|---|---|---|
| 1 | 1.00 | 5 | 19 |
| 3 | 3.60 | 18 | 68 |
| 5 | 6.50 | 33 | 124 |
| 8 | 11.40 | 57 | 217 |
| 10 | 14.10 | 71 | 268 |
| 15 | 22.90 | 115 | 435 |
| 20 | 36.40 | 182 | 692 |

(Pre-material, pre-dtype_mult, pre-str_factor. Add +1.5× for each matching weakness or material.effective_against tag.)

Chain is **UNCAPPED on the polynomial path.** The chain ends when the player answers wrong, the timer expires, or SPACE is pressed. See `combat.py:1976`:

```python
if weapon and getattr(weapon, 'chain_exponent', None):
    _max_chain = None  # polynomial path: uncapped
else:
    _max_chain = weapon.max_chain_length
```

**Unarmed is also uncapped** (fixed 2026-10-03). The damage formula at line 1008 already runs the polynomial at exponent 1.15 for `weapon is None`, but the max-chain gate used to fall into the `else` branch and cap unarmed at `len(_DEFAULT_MULTIPLIERS) = 5`. That mismatch was a half-finished v2.14.0 migration — now `weapon is None` goes to the uncapped path. `_DEFAULT_MULTIPLIERS` is kept only as a safety fallback for any caller that reaches for `chain_multipliers` on an unarmed path (it has no live reader after this fix).

**Audit note (SYSTEMS_AUDIT.md P2):** `attack_chain_cap_bonus` (Ring of Gawain, Torque of Lugh) is dead on the polynomial path — the +N applies only when `_max_chain is not None`, but every weapon with `chain_exponent` sets `_max_chain = None`. Known bug, not fixed in v2.18.0.

## Strike / SPACE mechanic

Chain-mode math quiz accepts answers continuously. The strike LANDS when:

| Trigger | Chain outcome | Damage |
|---|---|---|
| Player presses **SPACE** | Lands at current rung | Full chain mult |
| Answer wrong at chain ≥ 1 | Chain shatters visually; strike lands | Full chain mult |
| Answer wrong at chain 0 (first question) | **MISS** | 0 (plus cursed-miss backlash if applicable) |
| Timer expires | Lands at current chain | Full chain mult |
| Chain reaches `_max_chain` (legacy path only) | Auto-lands | Peak mult |

Chain **resets to 0 at every new attack** — no stockpiling between attacks. Parashu's `chain_no_reset_on_tag` is the one carry-forward exception, and it only carries ONE attack and only when the previous kill matched a tag.

## UI — combat HUD inside the quiz modal

`RenderMixin._draw_combat_hud` (`src/game_render.py:2477`) paints the combat strip at the bottom of the chain-mode quiz panel. Its visual hierarchy is intentional — not every row carries the same weight.

**Primary call-outs** (bigger font, high contrast):

- **Target HP** — monster name in body-md, bar color-coded by percentage (green > 50%, warning yellow 25–50%, danger red < 25%), HP numbers printed next to the bar in the same hp color at body-md.
- **Current damage preview** — the live chain readout (`x{mult:.1f}   {dmg} dmg`) renders in heading-lg beside the HP bar, coloured by chain-rank once the player clears chain 3.

**Secondary rows** (body-sm, muted / `FP.FADED_TEXT`):

- Weapon name (parenthetical, bottom-right corner).
- Damage-type label — keeps its signal colour (`WEAKNESS!` success-green, `RESISTED` danger-red, neutral in faded) but shrinks to body-sm; sits on the same row as the projection.
- Future-chain projection (`at {milestone} ({rank}): {dmg}`).
- `SPACE strikes` / `SPACE cancels` hint — bottom-right footer, muted.

**History:** the Phase 1 UI beautification pass (v2.22.0, 2026-10-03) reordered the hierarchy. Before, every row rendered at body-sm except the chain readout at body-md — the weapon name, damage-type banner, and SPACE hint competed with the HP bar for attention. The reorder is **font-size and color only**: no mechanics, numbers, procs, or ranged-weapon branching changed.

## Hit resolution — order of operations

Melee swings resolve entirely inside `player_attack._callback`. Monster-to-player hits resolve inside `monster.attack(player)`. Both paths funnel per-hit damage through:

- **`monster.take_damage(amount, damage_type='physical', ignore_resistance=False)`** (`monster.py:310`) — resistance/weakness via `_damage_multiplier` on non-physical types, HP decrement, revive-once-on-death (Green Knight), sleeping-wakes-up on hit, `alive=False` at 0 HP. Melee callers pre-scale and pass `damage_type='physical'` to avoid double-dipping the resistance table.
- **`DeathMonster.take_damage(amount, damage_type='physical', ignore_resistance=False) -> 0`** — the Grim Reaper is invincible. **v2.18.0 fix:** signature now accepts `damage_type` and `ignore_resistance` kwargs (`monster.py:1706`) so spell/wand paths and chain-passive procs that pass them don't TypeError.
- **`player.take_damage(dmg, atk_type)`** — the mirror of monster.take_damage; applies player resistances, armor DR, Nemean-hide floor-at-1, etc.

### Dragon scales / shielded / resistances — the "DR" layer

`_skip_dr = ignore_resistances OR blade_flow_stack OR _chain_bypass_dr`. When set:

- `dragon_scales` physical reduction is skipped (Fafnir underbelly intact though — in-pit still gives ×4).
- Monster `shielded` status's 0.5× is bypassed earlier via `_shield_bypass` (same conditions + `weapon.ignore_shield`).
- `dtype_mult` is clamped UP to 1.0 — resistances stop cutting damage, weaknesses still boost.

`_chain_bypass_dr` is set per-hit by `_apply_chain_class_pre_damage` for these class × tier combos (`_BYPASS_DR_TIERS`):

```python
'sword':     {10, 15, 20}   # 1h sword: master strike at C10, blade_flow-driven C15/C20
'1h_sword':  {10, 15, 20}
'spear':     {10, 15, 20}   # pierce through armor
'bow':       {15, 20}       # piercing shot
'crossbow':  {5, 10, 15, 20} # bolts always punch through
'mace':      {20}           # shattering blow
'halberd':   set()          # halberd C20 keeps sunder, does NOT bypass DR
```

`blade_flow` is a stack-consumed player buff (max 10 stacks). Each attack consumes 1 stack. Granted by 1h sword C15 (+3), 1h sword C20 (+4), 2h sword C20 (+3), and Soul Reaver's `growth_on_innocent_kill` (+1).

### Weakness / resistance / material.effective_against

The master lookup is `combat._damage_multiplier(damage_types, monster)` at `combat.py:833`:

1. Load material tags from `data/materials/weapons/*.json` (cached in `_MATERIAL_EFFECTIVE_AGAINST`, `_MATERIAL_VULNERABILITIES` — lazy on first call).
2. Build `weaknesses = monster.weaknesses + any_damage_type_whose_material_effective_against_matches_monster_tags`.
3. Legacy fallback: adds `silver` to weaknesses for undead/demon, `iron` for fey (safety net for pre-material-system monsters).
4. For each `dt` in `damage_types`, score 1.5 (weakness) / 0.5 (resistance) / 1.0 (neutral). Return `max(scores)`.

The `effective_against` tag is a **1.5× bonus**, not a replacement. A volcanic-iron 2h sword hitting a frost giant (fire-vulnerable AND slash-vulnerable) stacks all layers:

`8 base × 0.95 material × 1.5 material_effective × 1.5 slash-weakness × chain_mult`

at chain 10 ≈ 254 damage. This stacking is **intended** — the vulnerabilities layer up for the "really weak" story.

### Reflect handling

Three reflect paths exist, all driven from `monster.attack(player)` (`monster.py:631-676`):

- **Elemental shield reflect.** If `atk_type == 'fire'` and player has `fire_shield` status AND the attack was blocked (`actual == 0`), reflect `dmg // 2` back as `self.take_damage(refl)`. Same for cold/`cold_shield`. See `monster.py:631-639`.
- **`reflect_spell` / `spell_reflect` chain passive** (Aegis of Athena, Smoking Mirror). Rolls a % chance per magical/elemental hit (`fire`, `cold`, `lightning`, `magic`, `acid`, `poison`, `force`, `necrotic`, `radiant`, `psychic`). On success, reflects FULL damage back. See `chain_passives.get_reflect_spell_chance` and `monster.py:641-654`.
- **`mirror_of_souls` chain passive** (Smoking Mirror of Tezcatlipoca). 20% chance an incoming melee attacker takes the SAME damage they dealt. Melee types only. See `chain_passives.roll_mirror_of_souls` and `monster.py:656-666`.

### Drain-heals-self

`drain_heals_self` on a monster (default 0.0; vampire family 0.5–1.0) causes a drain attack to heal the monster: `heal = max(1, int(actual * drain_heals_self))`. Fired at `monster.py:701-710`:

```python
if atk_type == 'drain' and _dhs > 0 and actual > 0 and self.alive:
    heal = max(1, int(actual * _dhs))
    self.hp = min(self.max_hp, self.hp + heal)
    msg += f" The {self.name}'s wounds close as it feeds ({heal} HP regained)."
```

The audit fix for `ancient_vampire_lord` was adding the `drain_heals_self` field to the monster JSON — the attack type and heal pipeline existed, but the data was wrong.

### Boss-immunity gating

`is_boss` is now sourced from JSON (`monster.py:104`, **v2.18.0 fix**):

```python
# Read from JSON so boss-immunity in hero_specials/game_magic actually
# applies to blood_archon, iron_patriarch, whispering_crone, and the
# 7 seal_demon_* monsters. Falls back to False if the JSON omits it;
# _DEFAULTS also carries is_boss=False for old pickles.
self.is_boss: bool = bool(defn.get('is_boss', False))
```

Combat consumers of `is_boss` / `'boss' in tags`:

- **Damocles auto-kill** (`combat.py:1629`) — `and 'boss' not in set(getattr(monster, 'tags', []))`. The sword cannot auto-kill a boss.
- **Laevateinn boss_doom_dot** (`combat.py:1740`) — fires ONLY on `'boss' in tags OR getattr(monster, 'is_boss', False)`. 5% max-HP/turn DoT with 30-turn duration.
- **Minimum hit chance** (`monster.py:402, 496, 1510`) — `min_hit_chance = 0.25 if is_boss else 0.05`. Bosses punch through player AC on a bad THAC0 roll one in four times.
- **Spell / wand immunity** — charm, paralyze, confuse, sleep, hold_monster, fear are gated via `is_boss` in `game_magic.py` (not in-scope for this doc but same flag feeds it).

### Crit model

**There is no crit model.** v2.14.0 retired all crit code. `combat.py:1152`:

```python
# Chain combat v2 (v2.14.0): crit is retired. Chain IS the crit —
# the polynomial ladder handles the "big number" reward directly.
# The `crit` boolean is kept for on_complete kwargs so callers that
# branch on it still compile; it now stays False everywhere.
crit = False
```

`Weapon.crit_multiplier` is still LOADED from JSON (`items.py:325`) for backward compat but is never consumed. Harpe's old `petrify_on_crit` was rewired to fire at chain ≥ 15 (`combat.py:1456`); Kusanagi's old force-crit became a flat ×1.25 damage when 3+ enemies are adjacent (`combat.py:1118`); Soul Reaver's "next-hit auto-crit" became `+1 blade_flow` stack (`combat.py:1779-1782`).

The `crit_buff` status (Joan of Arc / Ash's She-Bitch hero passive) still provides a +50% damage multiplier (`combat.py:1226`) and consumes one duration charge per attack. It's the only legacy crit mechanic left live.

## Class chain-specials ladder

Per-weapon-class ladder keyed on `_weapon_key(weapon)` and `_chain_special_tier(chain) ∈ {0, 5, 10, 15, 20}`. The ladder table lives in [`docs/design/weapon_specials_v2_14.md`](../design/weapon_specials_v2_14.md); the dispatch is `combat._apply_chain_class_post_damage` (`combat.py:311-735`). See [weapons_and_materials](weapons_and_materials.md) §Class ladder for the per-class short form.

**Key invariant:** only the HIGHEST-threshold rung fires. The `_apply_chain_class_post_damage` function uses `if tier == 5 / elif tier == 10 / elif tier == 15 / elif tier == 20` — never combined. Each rung's effect was designed as the full package for that chain level.

The pre-damage hook (`combat._apply_chain_class_pre_damage`) sets `player._chain_bypass_dr` (consumed in the damage block) and returns the bow-C20 vitals ×2 multiplier. All other class effects are post-damage.

### New statuses v2.14.0 added for the ladder

| Status | Target | Effect | Primary driver |
|---|---|---|---|
| `armor_crack` | Monster | +25% damage received for N turns | Mace C10+, 2h warhammer C15+ |
| `sundered` | Monster | -30% outgoing damage for N turns | Fist C10, Rapier C10+, 1h axe C10+, 2h axe C10+, halberd C10+ |
| `deep_wound` | Monster | +25% damage received AND cannot regenerate for N turns | Fist C15+, Dagger C10 |
| `blade_flow` | **Player** | Next N attacks bypass DR (stack-consumed, cap 10) | 1h sword C15 (+3) / C20 (+4), 2h sword C20 (+3), Soul Reaver innocent-kill (+1) |
| `ruptured` | Monster | 10% max HP / turn DoT; cannot be healed | Dagger C20 |
| `impaled` | Monster | Cannot move for N turns (can still attack in place) | Spear C20 |

`armor_crack` and `deep_wound` STACK additively on amplifier (`combat.py:1283-1289`): `_amp += 0.25` per flag, cap at `+0.50` combined.

## Invariants (don't break)

- **`chain_exponent` set ⇒ polynomial path ⇒ uncapped chain.** Any new field or hook that expects a finite max_chain (like `attack_chain_cap_bonus`) must handle `_max_chain is None`.
- **One class-rung fires at a time.** Never add another `elif tier == 5` in a block that already has `tier == 10` — the dispatch assumes the else-chain structure.
- **`crit=False` everywhere.** Do not resurrect `crit=True` paths. Any new "big hit" mechanic should layer on `mult`, not revive the crit boolean.
- **Weapon.effective_against on compositional weapons is dead.** The guard at `combat.py:1068` is `if is_unique:`. A compositional weapon inherits `effective_against` through its material; counting the weapon's inherited copy ALSO would double-apply. Only unique weapons' explicit anti-tag arrays live here.
- **Monster.take_damage is pre-scaled on melee callers.** `combat.player_attack` applies `_damage_multiplier` locally and passes `damage_type='physical'` so the resistance table doesn't fire twice. Any new melee pathway must do the same, OR skip the local multiplier and pass the real type.
- **DeathMonster.take_damage accepts `damage_type` and `ignore_resistance` kwargs.** v2.18.0 fix. Keep them; many wand/spell paths pass them through.
- **`_combat_monsters_ref`, `_combat_pets_ref`, `_combat_game_ref` are side channels.** `combat.py` is a leaf — it does not import `game_combat` or `main`. These attrs are set by the mixin in `_start_combat` / `_fire_ranged` immediately before calling `player_attack`. Ranged does NOT set `_combat_game_ref` as of v2.18.0 — latent bug for any weapon-side mechanic that reaches for `game` via a ranged shot (SYSTEMS_AUDIT.md P3).
- **`chain=0` is a MISS, not a landed hit.** Tyrfing's backlash fires, Damocles counter resets, callback runs with `(0, dead, 0)`. Do not add damage, status, or chain-special effects at chain 0.
- **Fist is the "you dropped your weapon" fallback.** `base = max(1, round(2 * (1 + max(0, STR-10)/10)))`. STR 10 ⇒ 2, STR 15 ⇒ 3, STR 20 ⇒ 4. Don't buff it — unarmed should feel worse than any equipped weapon, same as the original 2026-05-19 intent.

## Interactions

- **[status_effects](status_effects.md)** — the ladder depends on `bleeding`, `poisoned`, `burning`, `stunned`, `paralyzed`, `confused`, `blinded`, `slowed`, `shielded`, `heal_blocked`, `petrifying`, plus the v2.14.0 additions. Any status registered there is a candidate for weapon procs. `combat.py` writes to `monster.status_effects` directly through `_max_status` (ceiling-max, no overwrite shortening).
- **[magic](magic.md)** — spells call `monster.take_damage(dmg, damage_type)` with real types. Resistance / weakness are resolved there (not pre-scaled). `apply_spell_damage_passives` layers chain-equip multipliers / crit / anti-being charges. Reflect-spell chain passives fire on monster.attack (not spell cast).
- **[items](items.md)** — Weapon class, Ammo class, Panoply of Hephaestus `divine_smithing` cap bump, chain-equip armor `chain_bonus` adding a free chain head-start.
- **[progression](progression.md)** — WIS seconds per math question is THE combat-skill lever. Enchant caps per slot are enforced in `effective_enchant_cap`.
- **[monsters](monsters.md)** — resistances / weaknesses lists, tags for material.effective_against, `is_boss` for immunities, `dragon_scales` for the DR layer, `drain_heals_self` for vampire family. Multi-tile boss footprint uses `geom.monster_at_tile` so AoE radius checks remain correct against Fafnir's (2,2).
- **[identify_v3](identify_v3.md)** — identification does NOT gate combat. Unidentified weapons work; the player just sees "unidentified <true name>" and doesn't know the BUC/enchant. Blessed weapons gain the `holy` damage type at use-site (`combat.py:1050`).

## History of major decisions

- **2026-05-19 — Combat rebuild.** Chain-peak formula canonized. 11 materials (data/materials), 22 class mechanics (common templates), 149 unique procs. 8 invariant tests added. Base-weapon damage retuned so chain-5 under the new curve matched chain-5 on comparable old gear (protect floor, open ceiling). See `project_combat_rebuild_2026_05_18.md`.
- **2026-05-30 — Engine waves 2 / 3 / 4 (inert-flag wiring).** The audit found ~30 uniques whose JSON flags had no engine consumer. Each wave added field-load + consumer code for a batch: freeze_chance (Aiglos), weapon.effects status (vulcans_brand / wendigo_fang / echidna_fang / hunt_captains_sword), undead_multiplier (Anduril numeric), per-tag bonus damage dice (Anduril +1d8, Glamdring, Cadmus, etc.), chain_bonus_on_low_hp_window (Skofnung), skip_chain_warmup_vs_tag (Harpe), one_shot_chain_save_per_floor (Hrunting), cursed_lineage (Pelops), prophecy_blade (Akinakes), cannot_miss_before_hurt (Fail-not), chain_lightning_at_chain_n (Mjolnir), multi_arrow_at_chain_5 (Gandiva), boss_doom_dot_at_chain_5 (Laevateinn), weep_heal_on_kill_scaled (Spear of Longinus), chain_tier_status_table (Rod of Moses), return_to_hand_ward (Sudarshana), spare_kill_chance (Curtana), summon_after_kill_with_tag (Cadmus / Vel / Shamshir), damage_bonus_vs_gaze (Spear of Lugh), chain_modulated_reach (Ruyi Jingu Bang), random_status_from_pool (Echidna's Fang), apply_heal_block_chance (Gae Dearg), damoclean_counter (Sword of Damocles), kill_count_karma_adjust (Penitent's Blade), reveal_tag_on_chain_5_kill (Meleager's Boar-Spear), stealth_damage_bonus (Robin Hood), adjacent_pet_damage_bonus (Oathkeeper), extra_action_after_kill (Zireael), first_blood_bonus (Atalanta's Bow), glows_near_orcs (Glamdring).
- **2026-06-07 — Ranged double-dip fix.** Compositional ranged weapons (yew crossbow etc.) were double-counting material.effective_against: once in `_damage_multiplier`'s weakness lookup, again in the per-weapon anti-tag block. Gated the per-weapon block to `is_unique` only (`combat.py:1068`). A yew crossbow vs fey satyr was dealing 2.25× instead of the intended 1.5×.
- **2026-09-07 — Chain combat v2 design agreed.** Polynomial damage, flat WIS seconds, SPACE-to-strike, visual chain milestones, no mechanical bonuses on milestones. See `docs/design/chain_combat_v2.md`.
- **2026-09-10 — Weapon chain specials + crit removal (v2.14.0).** 6 new statuses, per-class 5/10/15/20 ladder, crit retired from engine + data. Harpe petrify-on-crit → chain 15, Kusanagi force-crit → ×1.25 surround, Soul Reaver auto-crit → `blade_flow +1`. See `docs/design/weapon_specials_v2_14.md`.
- **2026-09-11 — Uniques v2.14.** 96 uniques rebased to `chain_exponent=1.15`, iconic exceptions keep bumped base_damage (Mjolnir 32, Dawnbreaker 30, Tyrfing 26, Laevateinn 26, Ruyi Jingu Bang 24, etc.). 8 redundant `class_mechanic` values stripped where the class ladder now covers them (bleed_at_max, cleave_at_max, cleave_at_max_plus_bleed, stun_at_max, stun_knockdown_at_max, defensive_parry, quick_riposte, master_strike, armor_pierce_at_max, anti_heavy_at_max). See `docs/design/uniques_v2_14.md`.
- **2026-09-13 (v2.15.0) — `_weapon_key` normalization.** Common hafted-blunt templates (mace, warhammer, flail, club, maul, quarterstaff) all set `weapon_class='blunt'`; glaive uses `'polearm'`. The `_weapon_key` function (`combat.py:128`) was added to disambiguate these to the correct chain-special ladder entry. Without it every common blunt weapon was getting zero class chain specials.
- **2026-10-02 (v2.18.0) — Full systems audit + fix wave.** Highlights for combat:
  - `Monster.__init__` now reads `is_boss` from JSON (`monster.py:104`). 10 mini-bosses (blood_archon, iron_patriarch, whispering_crone, 7 seal_demon_*) regained boss-immunity to charm / paralyze / confuse / sleep / hold_monster / fear.
  - `DeathMonster.take_damage` signature now accepts `damage_type` and `ignore_resistance` kwargs (`monster.py:1706`).
  - `vulcans_brand` material id fixed from `"volcanic iron"` (space) to `"volcanic_iron"` (underscore). The signature volcanic-iron effective_against tags now apply.
  - `kladenets` (Samosek) — removed inert `counterAttackChance: 0.25` field; added a `_note` recording the design intent so a future passive-defense hook can wire it in.
  - Niten Ichi-Ryū (Musashi) gate rewired at `combat.py:1214-1224`. Previously the +15% required `player.weapon AND player.ranged_weapon`, but Musashi ships two melee swords (`longsword` + `shortsword`), and `ranged_weapon` only accepts ammo-requiring weapons — so the signature never fired. New gate: "a non-ammo weapon in the primary slot," which preserves the two-swords fantasy for any melee loadout.
  - 7 unreachable quest armors deleted from `data/items/armor.json` (`quest_spawn_nemean`, `quest_spawn_green_knight`, `quest_spawn_serpent`, `quest_spawn_arachne`, `quest_spawn_erlking`, `quest_spawn_anansi`, `quest_spawn_nidhoggr`). All had `min_level: 9999` and no code implementing their `quest_spawn_*` methods. ~15KB of dead stat blocks removed.

## Testing

- **`tests/test_combat_invariants.py`** — the 8 invariants from the 2026-05-18 rebuild. Peak-chain shape, class-tag presence, no-crit, dragon-scales + blade_flow bypass, etc.
- **`tests/test_engine_wave*_unique_mechanics.py`** — field-load + consumer-code presence per inert-wire-up wave.
- **Full suite** — `pytest tests/ -v`. 1570+ tests pass as of v2.18.0.
- **No play-test coverage** for randomized chain-20 outcomes, deep-floor Dragon-vs-blade_flow DR interactions, or multi-weapon unique proc combos — those are flagged "logic test only" in `feedback_play_test_limits.md`.
- **Play-test rule applies** to easy-reach changes: equipping a common weapon, chain-5 against a floor-1 orc, SPACE-to-strike cancel, cleave on adjacent kill. These must be driven by Brandon before a feature is called "done."

## Known rough edges

(Open findings from SYSTEMS_AUDIT.md — not fixed in v2.18.0.)

- `attack_chain_cap_bonus` dead on polynomial path. Ring of Gawain / Torque of Lugh effectively inert for every weapon shipping `chain_exponent`.
- `boomstick` design-notes promise a chain-5 AOE/shotgun spread, but the mechanic was never wired. `template_basis: "crossbow"` but `weapon_class: "ranged"` routes it through the BOW specials ladder.
- `game_combat._fire_ranged` doesn't set `_combat_game_ref` (unlike `_start_combat`). Any weapon-side mechanic that reaches for `game` via a ranged shot is latent-buggy.
- `game_combat._fire_ranged` consumes ammo BEFORE the quiz — chain 0 (miss) still burns ammo. Unarmed melee whiffs are free.
- `equip_threshold` field exists on 4 weapons (hunt_captains_sword, wendigo_fang, echidna_fang, vulcans_brand). Dead — there is no weapon-equip quiz path. See `_equip_item` at `main.py:5462` — Weapon equip calls `player._apply_equip` directly, no quiz.
- `Weapon.equipped_monster_aggro_radius`, `equipped_sound_radius_modifier`, `_karma_disappear_rolled_this_floor` loaded but no consumers. Dead fields.
- `Curtana._spare_kill_floor_hp` counter is never reset in `_change_level`. "Per floor" silently becomes "per run."
- `mjolnir_shard` lore claims a chain-5 lightning proc that only Mjolnir carries. Shard has the design note but not the wiring.
- 21 uniques reference material names that don't exist as material files (`"divine iron"`, `"dark iron"`, `"enchanted iron"`, `"spectral iron"`, `"legendary"`, `"bone"`, `"fang"`, `"hardwood"`, `"wood"`, `"gold"`, `"leather"`, `"dad"`). Pure lore strings; any material lookup silently returns 1.0.
- `_BYPASS_DR_TIERS` lists only 7 weapon classes. The other classes never bypass DR at any chain rung — design intent unclear (deliberate for 2h axe / glaive / dagger / fist / staff; probably accidental for the 2h variants).
