"""Game's combat-orchestration handlers, extracted from main.py (Phase 8).

This module defines :class:`CombatMixin`, which the real ``Game`` class
inherits alongside :class:`game_render.RenderMixin`,
:class:`game_menus.MenuMixin`, :class:`game_input.InputMixin`,
:class:`game_magic.MagicMixin`, and :class:`game_encounters.EncountersMixin`.
The mixin owns:

  * Combat openers and resolvers: ``_start_combat`` (math chain melee),
    ``_fire_ranged`` (math chain ranged), and the helper
    ``_nearest_visible_monster``.
  * Targeting cursor openers and confirms: ``_open_targeting`` (ranged),
    ``_open_melee_targeting`` (melee reach), ``_open_throw_targeting``
    (potion/weapon throw), and the confirm shims
    ``_confirm_ranged_target``, ``_confirm_melee_target``,
    ``_confirm_throw_target``, ``_confirm_wand_target``,
    ``_confirm_power_target``, ``_confirm_observe``.  The confirm shims
    delegate into MagicMixin (wand zap quiz, targeted spell quiz, AI
    powers like Stuffie fire breath) -- MRO handles cross-mixin calls.
  * Throw mechanics: ``_throw_weapon``, ``_throw_soul_sphere``,
    ``_throw_unusual_sphere``, ``_apply_thrown_potion``, plus the helpers
    ``_find_first_monster_in_path`` (Bresenham line trace),
    ``_get_weapon_throw_damage``, ``_get_weapon_break_chance``,
    ``_get_throw_range``, and the ``_is_throwable_weapon`` staticmethod.
    Throw-only class constants ``_THROWABLE_CLASSES``,
    ``_THROW_BREAK_CHANCE``, ``_THROW_BREAK_LEGENDARY``,
    ``_THROW_DEBUFF_MAP``, and ``_THROW_BUFF_MAP`` move with the methods
    that consume them.  ``_throw_crosses_tile`` is the staticmethod alias
    for the throw_crosses_tile helper used by ``_throw_weapon`` for the
    Odin altar reforge check.
  * Pit mechanics: ``_dig_pit`` (shovel weapon) and ``_player_fall_in_pit``.
  * On-kill side effects: ``_on_monster_killed`` (the single point that
    handles boss popups, seal tracking, treasure drops, and corpse
    spawning), plus ``_drop_treasure``, ``_make_corpse``, and the random
    drop helper ``_spawn_treasure_item``.
  * Monster and pet turn loops: ``_do_monster_turns``, ``_do_pet_turns``
    (each ~250 lines; moved verbatim).

The corresponding draw code (``_draw_*_targeting``, ``_draw_combat_hud``,
``_draw_death_screen``, ``_draw_victory_screen``) lives in RenderMixin,
and the keyboard dispatcher (``_target_input``) lives in InputMixin.
Class-level constant ``_THROW_TABS`` stays on Game because MenuMixin
and RenderMixin read it directly through ``self.``.

``_BOSS_STORY_KEYS`` (consumed by ``_on_monster_killed``) stays on Game
because the dictionary is co-located with story-popup code that lives in
main.py.  Bound-method lookup goes through ``self.`` so MRO finds it.
"""
from __future__ import annotations
from monster import the_name

import random

import pygame  # noqa: F401  -- kept for parity with sibling mixins; no direct use

import floor_curve
import sound_system as _snd
from combat import player_attack
from game_helpers import throw_crosses_tile
from game_states import (
    STATE_PLAYER, STATE_QUIZ,
    STATE_TARGET, STATE_DEAD,
)
from geom import monster_at_tile, is_at_tile
import unseen
import theft
from items import Artifact, Weapon
from pet_system import Pet, pet_damage_type, random_species as random_pet_species


# Chance an attack passes through a displaced image. It was 0.30, and a
# permanent one is available from a quirk and a mystery: nearly a third of
# every attack in the game, for the whole run.
DISPLACEMENT_MISS = 0.15

# A monster under one of these cannot swing this turn: it does not swipe at
# pets or escorts (_monster_swipes) and does not call Shep's rescue.
_HELD_FOE_EFFECTS = ('sleeping', 'paralyzed', 'stunned', 'frozen', 'feared', 'charmed')


def _monster_level(m) -> int:
    """A monster's own level: where monsters.json places it (1 to 100)."""
    lvl = getattr(m, 'peak_floor', None) or getattr(m, 'min_level', 1) or 1
    return max(1, min(100, int(lvl)))


def _is_bystander(m) -> bool:
    """A friend standing among the monsters: an encounter NPC, the unicorn,
    an allied angel. Monster.take_damage leaves them unhurt; area blows
    (cleave, ricochet, Joyeuse, the Boots of Thor) also pass them by, so
    they print no damage they did not take."""
    return bool(getattr(m, '_npc_encounter_tag', None) or getattr(m, '_flavor_encounter_tag', None)
                or getattr(m, '_is_unicorn', False) or getattr(m, 'is_allied', False))


# Shares of the creature's own health (floor_curve.wound).
PIT_FALL_SHARE = 0.10         # a monster that blunders into a pit
SHIELD_LASH_SHARE = 0.10      # fire / cold shield, each time it is struck
DOOM_SHARE = 0.60              # Armor of Ragnarok: of each nearby monster's health (a named foe's a tenth of it)
DOOM_STAGGER = 3               # turns the survivors of that blast lie stunned


class CombatMixin:
    """Combat orchestration, targeting cursors, throw mechanics, monster/pet turns.

    Class-level constants for the throw system live here so they stay
    co-located with the throw helpers.  ``_THROW_TABS`` stays on Game
    because MenuMixin / RenderMixin read it directly.
    """

    # ------------------------------------------------------------------
    # Throw mechanics: class constants
    # ------------------------------------------------------------------

    _throw_crosses_tile = staticmethod(throw_crosses_tile)

    # Weapon classes that can be thrown, with throw damage multiplier.
    # Chain combat v2: trimmed to dagger + spear only, both at 1.0x. Other
    # classes were not designed for throwing and the mechanic was more novelty
    # than tactical option. The full former table lived here previously —
    # see git history if resurrecting an old class as throwable.
    _THROWABLE_CLASSES = {
        'dagger': 1.0,   # designed for throwing
        'spear':  1.0,   # javelin
    }

    # Break chance by material (higher = more fragile when thrown)
    _THROW_BREAK_CHANCE = {
        'bone':           0.50,
        'iron':           0.35,
        'steel':          0.25,
        'hardened_gold':  0.20,
        'diamond':        0.10,
        'adamantine':     0.05,
    }
    _THROW_BREAK_LEGENDARY = 0.05  # named/legendary weapons

    # Map potion effect names to monster status effect names (debuffs)
    _THROW_DEBUFF_MAP = {
        'poison':        'poisoned',
        'paralysis':     'paralyzed',
        'confusion':     'confused',
        'blindness':     'blinded',
        'sleep':         'sleeping',
        'weakness':      'weakened',
        'slow':          'slowed',
        'sickness':      'diseased',
        'fumbling':      'fumbling',
        'fear':          'feared',
        'hallucination': 'hallucinating',
    }

    # Map potion effect names to monster buff status effects
    _THROW_BUFF_MAP = {
        'haste':         'hasted',
        'invisibility':  'invisible',
        'regeneration':  'regenerating',
        'levitation':    'levitating',
        'fire_resist':   'fire_resist',
        'cold_resist':   'cold_resist',
        'shock_resist':  'shock_resist',
    }
    # The buffs above that a monster actually acts on (a levitating monster
    # floats over a dug pit). The rest change nothing for a monster.
    _THROW_BUFFS_MONSTERS_USE = frozenset({'levitating'})

    # ------------------------------------------------------------------
    # Targeting -- melee reach (Observe-like cursor for melee attacks)
    # ------------------------------------------------------------------

    def _reach_line_clear(self, tx, ty) -> bool:
        """True if a melee strike can reach (tx, ty): always for the adjacent
        ring, and past it only along a clear line (no wall, closed door or
        diagonal squeeze between two walls)."""
        px, py = self.player.x, self.player.y
        if max(abs(tx - px), abs(ty - py)) <= 1:
            return True
        from combat import _line_of_sight
        return _line_of_sight(px, py, tx, ty, self.dungeon)

    def _open_melee_targeting(self):
        """Press 'a' to enter melee targeting mode — attack adjacent tiles (or further with reach weapons)."""
        weapon = self.player.weapon
        reach = weapon.reach if weapon else 1

        px, py = self.player.x, self.player.y

        # Build candidate list: alive monsters within melee reach. Past the
        # adjacent ring a reach weapon needs a clear line and a seen target
        # (C05: spears struck through solid walls at unseen monsters).
        _vis = getattr(self, 'visible', None) or set()
        candidates = [
            m for m in self.monsters
            if m.alive
            and abs(m.x - px) <= reach and abs(m.y - py) <= reach
            and not (m.x == px and m.y == py)
            and (max(abs(m.x - px), abs(m.y - py)) <= 1
                 or ((m.x, m.y) in _vis and self._reach_line_clear(m.x, m.y)))
        ]
        candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))

        self._target_candidates = candidates
        self._target_idx = 0
        self._melee_targeting = True
        self._melee_reach = reach

        if candidates:
            m = candidates[0]
            self.target_cursor_x = m.x
            self.target_cursor_y = m.y
        else:
            # Default cursor one tile to the right (or clamp)
            self.target_cursor_x = min(px + 1, self.dungeon.width - 1)
            self.target_cursor_y = py

        self.state = STATE_TARGET
        weapon_name = weapon.name if weapon else "fists"
        if candidates:
            self.add_message(
                f"Melee targeting with {weapon_name} -- arrow keys to aim, TAB to cycle, ENTER to strike, ESC to cancel.",
                'info'
            )
        else:
            self.add_message(
                f"Melee targeting with {weapon_name} -- arrow keys to aim, ENTER to strike, ESC to cancel.",
                'info'
            )

    # ------------------------------------------------------------------
    # Throw mechanics: helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_throwable_weapon(weapon) -> bool:
        """Can this weapon be thrown? Must be 1h, throwable class, and not a ranged weapon."""
        if weapon.requires_ammo:
            return False
        if weapon.two_handed:
            return False
        if weapon.weight > 5.0:
            return False
        # `throwable: true` in the data opts a single weapon in regardless of
        # class. The Broken Blade of Gram needs it: the Odin reforge secret is
        # "throw it over the altar", and a sword could never be thrown.
        if getattr(weapon, 'throwable', False):
            return True
        return weapon.weapon_class in CombatMixin._THROWABLE_CLASSES

    def _get_weapon_throw_damage(self, weapon) -> int:
        """Calculate throw damage: base_damage * class_mult * STR_factor."""
        mult = self._THROWABLE_CLASSES.get(weapon.weapon_class, 0.5)
        str_factor = 1.0 + max(0, self.player.STR - 10) * 0.03
        return max(1, int(weapon.base_damage * mult * str_factor))

    def _get_weapon_break_chance(self, weapon) -> float:
        """Return probability [0-1] that this weapon breaks on throw."""
        if weapon.weapon_class == 'net':
            return 0.0  # nets are designed to be thrown and recovered
        from items import is_random_loot
        if not is_random_loot(weapon):
            # Quest pieces (the Broken Blade of Gram) do not break: a throw
            # that missed Odin's altar had a 35% chance to end the Fafnir
            # quest for the run.
            return 0.0
        material = weapon.material.lower()
        base = self._THROW_BREAK_CHANCE.get(material, self._THROW_BREAK_LEGENDARY)
        return base

    def _get_throw_range(self, weapon=None) -> int:
        """Chain combat v2: throw range = base + (STR - 10) // 2, per weapon.
        Dagger base 3 (cap 7). Spear base 4 (cap 8). Falls back to dagger
        curve for any other throwable (in case a unique flags itself
        throwable outside the standard classes)."""
        if weapon is None:
            weapon = self.player.weapon
        wc = getattr(weapon, 'weapon_class', '') if weapon else ''
        str_bonus = max(0, (self.player.STR - 10) // 2)
        if wc == 'spear':
            return max(4, min(8, 4 + str_bonus))
        # dagger + any legacy throwable
        return max(3, min(7, 3 + str_bonus))

    def _open_throw_targeting(self, potion):
        """Enter targeting mode for throwing an item (potion, weapon, artifact).
        The arg name is legacy — the item is generic. Weapon items get their
        class-specific throw range; potions/artifacts use the dagger-tier
        fallback via `_get_throw_range(None)`."""
        self._throw_targeting = True
        self._melee_targeting = False
        self._throw_potion = potion
        _thrower = potion if hasattr(potion, 'weapon_class') else None
        self._throw_reach = self._get_throw_range(_thrower)

        px, py = self.player.x, self.player.y
        reach = self._throw_reach

        # Build candidate list: visible alive monsters within throw range
        from combat import _line_of_sight
        candidates = [
            m for m in self.monsters
            if m.alive and (m.x, m.y) in self.visible
            and max(abs(m.x - px), abs(m.y - py)) <= reach
            and _line_of_sight(px, py, m.x, m.y, self.dungeon)
        ]
        candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))

        self._target_candidates = candidates
        self._target_idx = 0

        if candidates:
            m = candidates[0]
            self.target_cursor_x = m.x
            self.target_cursor_y = m.y
        else:
            self.target_cursor_x = px
            self.target_cursor_y = py

        self.state = STATE_TARGET
        display = self._display_name(potion)
        self.add_message(
            f"Throw {display} (range {reach}) -- arrows to aim, TAB to cycle, ENTER to throw, ESC to cancel.",
            'info'
        )

    def _confirm_throw_target(self):
        """Throw the selected item at cursor position."""
        item = self._throw_potion
        self._throw_targeting = False
        self._throw_potion = None
        self.state = STATE_PLAYER

        px, py = self.player.x, self.player.y
        tx, ty = self._clamp_throw_target(px, py, self.target_cursor_x, self.target_cursor_y)

        hit_monster = self._find_first_monster_in_path(px, py, tx, ty)

        if isinstance(item, Artifact) and item.id == 'unusual_soul_sphere':
            self._throw_unusual_sphere(item, hit_monster, tx, ty)
        elif isinstance(item, Artifact) and item.id == 'soul_sphere':
            self._throw_soul_sphere(item, hit_monster, tx, ty)
        elif isinstance(item, Weapon):
            self._throw_weapon(item, hit_monster, tx, ty)
        else:
            # Potion throw
            self.player.remove_from_inventory(item)
            item.identified = True
            self.player.known_item_ids.add(item.id)
            display = item.name
            _esc = None if hit_monster else self._escort_at(tx, ty)
            if hit_monster:
                self._apply_thrown_potion(item, hit_monster, display)
            elif _esc is not None:
                # An escort never heals on its own; a thrown healing potion
                # still reaches them (half their own health, LORE NOT FLOOR).
                if 'heal' in str(getattr(item, 'effect', '') or '').lower():
                    _gain = min(_esc.max_hp - _esc.hp, max(1, _esc.max_hp // 2))
                    _esc.hp += _gain
                    self.add_message(f"The {display} splashes over {_esc.name}. (+{_gain} HP)", 'success')
                else:
                    self.add_message(f"The {display} splashes over {_esc.name}. Nothing happens.", 'info')
            else:
                self.add_message(
                    f"The {display} shatters on the ground. Nothing happens.", 'info'
                )

        # Cadmus's stone: something thrown into the middle of the Sown Men
        # makes the one it hits round on the man beside him.
        _q = int(getattr(hit_monster, 'quarrels_when_struck_by_thrown', 0) or 0) if hit_monster else 0
        if _q and hit_monster.alive:
            hit_monster.add_effect('confused', _q)
            if (hit_monster.x, hit_monster.y) in self.visible:
                self.add_message(f"{the_name(hit_monster)} spins round, blaming the one beside it!",
                                 'success')

        self._advance_turn()

    def _clamp_throw_target(self, px: int, py: int, tx: int, ty: int) -> tuple:
        """Where a throw aimed at (tx, ty) can come down: the last tile of
        its flight that is within throwing range and open floor. A throw
        aimed into rock, or past a wall, or further than the hero can throw,
        stops at the last open tile before it (PET-11). With no open tile
        before it the thing lands at the hero's feet."""
        from combat import get_line_tiles
        reach = int(getattr(self, '_throw_reach', 0) or 0)
        land = (px, py)
        for lx, ly in get_line_tiles(px, py, tx, ty):
            if reach and max(abs(lx - px), abs(ly - py)) > reach:
                break
            if not self.dungeon.is_walkable(lx, ly):
                break
            land = (lx, ly)
        return land

    def _throw_weapon(self, weapon, monster, tx: int, ty: int):
        """Throw a weapon at a target. Deals damage, may break."""
        import random as _rng

        # --- Odin's Altar secret: throw Broken Gram over the altar ---
        odin_pos = getattr(self.dungeon, 'odin_altar_pos', None)
        if odin_pos:
            ax, ay = odin_pos
            px, py = self.player.x, self.player.y
            # Check if the thrown path crosses over the altar:
            # player on one side, target on the other side (altar between them)
            if weapon.id == 'broken_gram':
                crosses_altar = self._throw_crosses_tile(px, py, tx, ty, ax, ay)
                if crosses_altar:
                    self.player.remove_from_inventory(weapon)
                    self._activate_odin_shrine(weapon, reforge=True)
                    # No _advance_turn() here: the caller advances the turn
                    # after every throw, so this one made it cost two.
                    return
            elif self._throw_crosses_tile(px, py, tx, ty, ax, ay):
                self.add_message(
                    "Thunder mutters a long way off, and stops. "
                    "The altar wanted something else.", 'info')

        self.player.remove_from_inventory(weapon)
        display = weapon.name
        dmg = self._get_weapon_throw_damage(weapon)
        break_chance = self._get_weapon_break_chance(weapon)

        if monster:
            _who = the_name(monster, lower=True)      # before the blow springs a lurker
            actual = monster.take_damage(dmg)
            self.add_message(
                f"You hurl the {display} at {_who}! ({actual} damage)", 'success'
            )
            if monster.is_dead():
                self._on_monster_killed(monster)
            land_x, land_y = monster.x, monster.y
        else:
            self.add_message(
                f"The {display} clatters to the ground.", 'info'
            )
            # the last tile of its flight that can be stood on: aimed at a
            # wall it landed inside the wall and was gone (the Broken Blade of
            # Gram, which the Fafnir quest needs, among them)
            from combat import get_line_tiles
            land_x, land_y = self.player.x, self.player.y
            for _lx, _ly in get_line_tiles(self.player.x, self.player.y, tx, ty):
                if not self.dungeon.is_walkable(_lx, _ly):
                    break
                land_x, land_y = _lx, _ly

        # Break check
        if _rng.random() < break_chance:
            self.add_message(f"The {display} shatters on impact!", 'warning')
        else:
            # Weapon survives -- drop it on the ground
            weapon.x = land_x
            weapon.y = land_y
            self.ground_items.append(weapon)

    def _throw_soul_sphere(self, sphere, hit_monster, tx: int, ty: int):
        """Throw a Soul Sphere — releases a random pet creature at the landing spot."""
        self.player.remove_from_inventory(sphere)

        # Landing tile: if a monster was hit, land one tile before; else target tile
        if hit_monster:
            # Land at the monster's tile (pet spawns there, monster is not displaced)
            land_x, land_y = hit_monster.x, hit_monster.y
        else:
            land_x, land_y = tx, ty

        # Find a walkable tile near the landing spot for the pet
        spawn_x, spawn_y = land_x, land_y
        if not self.dungeon.is_walkable(spawn_x, spawn_y) or \
           monster_at_tile(self.monsters, spawn_x, spawn_y) is not None or \
           (spawn_x == self.player.x and spawn_y == self.player.y) or \
           (spawn_x, spawn_y) in self._occupants(hero=False):
            # Try adjacent tiles
            found = False
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    nx, ny = land_x + dx, land_y + dy
                    if not self.dungeon.is_walkable(nx, ny):
                        continue
                    if nx == self.player.x and ny == self.player.y:
                        continue
                    if monster_at_tile(self.monsters, nx, ny) is not None:
                        continue
                    if (nx, ny) in self._occupants(hero=False):
                        continue
                    spawn_x, spawn_y = nx, ny
                    found = True
                    break
                if found:
                    break
            if not found:
                if getattr(sphere, 'bound_pet', None) is not None:
                    # A bound sphere holds a companion already met (Shep,
                    # a nicknamed cat): it must never be lost. It comes down
                    # whole on the open tile it reached, to be picked up and
                    # thrown again somewhere with room (PET-01).
                    if self.dungeon.is_walkable(land_x, land_y):
                        sphere.x, sphere.y = land_x, land_y
                    else:
                        sphere.x, sphere.y = self.player.x, self.player.y
                    self.ground_items.append(sphere)
                    self.add_message(
                        f"The sphere bounces and rolls to a stop, unbroken: there is no room "
                        f"for {sphere.bound_pet.name} to come out.", 'warning')
                    return
                # No room — sphere is wasted
                self.add_message("The sphere shatters but there is no room for a creature!", 'warning')
                return

        # Bound sphere: spawn the previously-recalled pet with state intact.
        bound = getattr(sphere, 'bound_pet', None)
        if bound is not None:
            bound.x, bound.y = spawn_x, spawn_y
            bound.alive = True
            self.pets.append(bound)
            self.add_message(
                f"{bound.name} bursts from the sphere — welcome back!", 'success')
            _snd.play('player_healed')
            return

        from pet_system import roll_soul_sphere_species
        self._hatch_sphere_pet(roll_soul_sphere_species(self._family_cats_present()),
                               spawn_x, spawn_y)

    def _family_cats_present(self) -> set:
        """The rare family companions (the cats and Shep) met this run."""
        from pet_system import family_pets_present
        return family_pets_present(self.player, self.pets,
                                   getattr(self.player, 'inventory', None))

    def _hatch_sphere_pet(self, species: str, spawn_x: int, spawn_y: int):
        """A new companion out of a Soul Sphere, then the naming popup."""
        from pet_system import FAMILY_PETS
        pet = Pet(species, spawn_x, spawn_y)
        # Late-pickup catch-up: pets hatched deeper get an initial XP grant
        # so they're not uselessly underleveled relative to the floor's enemies.
        pet.apply_late_pickup_bonus(self.dungeon_level)
        self.pets.append(pet)
        if species in FAMILY_PETS:
            met = getattr(self.player, 'family_cats_met', None)
            if not isinstance(met, set):
                met = set()
                self.player.family_cats_met = met
            met.add(species)
        self.add_message(pet.species['stages'][0]['msg'], 'success')
        _snd.play('player_healed')
        # Open the naming popup so the player can give this companion a nickname.
        self._naming_pet = pet
        self._pet_name_input_buffer = pet.species_name   # default: species name
        # A companion with a story of its own (Shep) brings its own words
        # for the naming popup, the log and the Journal.
        story = pet.species.get('naming_story')
        self._naming_story = dict(story) if story else None
        from game_states import STATE_PET_NAME_INPUT
        self.state = STATE_PET_NAME_INPUT

    def _throw_unusual_sphere(self, sphere, hit_monster, tx: int, ty: int):
        """Throw the Unusual Soul Sphere — summons Dad for 5 turns."""
        from boss_levels import BOSS_LEVELS
        if self.dungeon_level in BOSS_LEVELS:
            self.add_message(
                "The sphere pulses warmly in your hand, then fades. "
                "You hear Dad's voice: \"I believe in you. This one's yours.\"", 'info')
            return  # sphere NOT consumed — player keeps it
        self.player.remove_from_inventory(sphere)

        land_x, land_y = (hit_monster.x, hit_monster.y) if hit_monster else (tx, ty)

        # Find a walkable spawn tile near landing
        spawn_x, spawn_y = land_x, land_y
        placed = False
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx, ny = land_x + dx, land_y + dy
                if (self.dungeon.is_walkable(nx, ny)
                        and (nx, ny) != (self.player.x, self.player.y)
                        and not monster_at_tile(self.monsters, nx, ny) is not None
                        and (nx, ny) not in self._occupants(hero=False)):
                    spawn_x, spawn_y = nx, ny
                    placed = True
                    break
            if placed:
                break
        if not placed:
            self.add_message(
                "The sphere shatters in a flash of silver light, but there is no room!", 'warning')
            return

        from pet_system import DadPet, roll_rare_sphere_pet
        rare = roll_rare_sphere_pet(self._family_cats_present())   # Shep 1%, each cat 5%
        if rare:
            self._hatch_sphere_pet(rare, spawn_x, spawn_y)
            return
        dad = DadPet(spawn_x, spawn_y, duration=5)
        self.pets.append(dad)
        self.add_message("Dad is here! Everything will be fine now!", 'success')

    def _find_first_monster_in_path(self, x0, y0, x1, y1):
        """Walk Bresenham line from (x0,y0) to (x1,y1). Return first alive monster hit, or None.
        Prevents corner-cutting through diagonal wall gaps."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x1 > x0 else -1
        sy = 1 if y1 > y0 else -1
        err = dx - dy
        cx, cy = x0, y0
        while True:
            if cx == x1 and cy == y1:
                break
            e2 = 2 * err
            step_x = e2 > -dy
            step_y = e2 < dx
            # Diagonal step: block if both corners are walls
            if step_x and step_y:
                if (not self.dungeon.is_walkable(cx + sx, cy)
                        and not self.dungeon.is_walkable(cx, cy + sy)):
                    return None  # blocked by corner
            if step_x:
                err -= dy
                cx += sx
            if step_y:
                err += dx
                cy += sy
            if (cx, cy) != (x1, y1):
                # Check for monster at this tile
                for m in self.monsters:
                    if m.alive and is_at_tile(m, cx, cy):
                        return m
                # Check for wall (projectile stops)
                if not self.dungeon.is_walkable(cx, cy):
                    return None
        # Check target tile for monster
        for m in self.monsters:
            if m.alive and is_at_tile(m, x1, y1):
                return m
        return None

    def _apply_thrown_potion(self, potion, monster, display: str):
        """Apply a thrown potion's effect to a monster."""
        if not monster.alive:
            self.add_message(f"The {display} shatters harmlessly.", 'info')
            return
        from status_effects import _RESIST_BLOCKS
        from dice import roll as roll_dice
        effect = potion.effect
        duration = potion.duration if potion.duration > 0 else 10

        # --- Debuff effects ---
        debuff = self._THROW_DEBUFF_MAP.get(effect)
        if debuff:
            # Check resistance via status effects
            for resist, blocked in _RESIST_BLOCKS.items():
                if debuff in blocked and monster.has_effect(resist):
                    self.add_message(
                        f"The {display} splashes {the_name(monster, lower=True)}, but it resists!", 'warning'
                    )
                    return
            # Check monster resistances list for thematic immunity
            mon_resists = getattr(monster, 'resistances', [])
            if ('poison' in mon_resists and debuff in ('poisoned', 'diseased')) or \
               ('magic' in mon_resists and debuff in ('confused', 'hallucinating', 'feared')):
                self.add_message(
                    f"The {display} splashes {the_name(monster, lower=True)}, but it seems immune!", 'warning'
                )
                return
            monster.add_effect(debuff, duration)
            label = debuff.replace('_', ' ').title()
            self.add_message(
                f"The {display} splashes {the_name(monster, lower=True)}! It is {label}!", 'success'
            )
            return

        # --- Buff effects (heals/buffs the monster -- bad idea!) ---
        buff = self._THROW_BUFF_MAP.get(effect)
        if buff and buff not in self._THROW_BUFFS_MONSTERS_USE:
            # Nothing a monster does reads haste, invisibility, regenerating
            # or the resist statuses: "It looks Hasted!" was untrue.
            self.add_message(
                f"The {display} splashes {the_name(monster, lower=True)} but has no effect.", 'info'
            )
            return
        if buff:
            monster.add_effect(buff, duration)
            label = buff.replace('_', ' ').title()
            self.add_message(
                f"The {display} splashes {the_name(monster, lower=True)}. It looks {label}!", 'danger'
            )
            return

        # --- Healing effects (restore monster HP) ---
        if effect in ('heal', 'extra_heal', 'full_heal'):
            if hasattr(monster, 'can_heal') and not monster.can_heal():
                healed = 0                      # C10: its wound will not close
            elif effect == 'full_heal':
                healed = monster.max_hp - monster.hp
                monster.hp = monster.max_hp
            else:
                amt = roll_dice(potion.power) if potion.power else 10
                if effect == 'extra_heal':
                    amt += 10
                healed = min(amt, monster.max_hp - monster.hp)
                monster.hp = min(monster.max_hp, monster.hp + amt)
            if healed > 0:
                self.add_message(
                    f"The {display} splashes {the_name(monster, lower=True)}. It heals {healed} HP!", 'danger'
                )
            else:
                self.add_message(
                    f"The {display} splashes {the_name(monster, lower=True)}. It looks unaffected.", 'info'
                )
            return

        # --- Teleport (relocate monster randomly) ---
        if effect == 'teleport':
            import random as _rng
            walkable = [
                (x, y)
                for y in range(self.dungeon.height)
                for x in range(self.dungeon.width)
                if self.dungeon.is_walkable(x, y)
                and not monster_at_tile(self.monsters, x, y) is not None
                and (x, y) not in self._occupants(hero=False)
                and (x, y) != (self.player.x, self.player.y)
            ]
            if walkable:
                nx, ny = _rng.choice(walkable)
                monster.x, monster.y = nx, ny
                self.add_message(
                    f"The {display} splashes {the_name(monster, lower=True)} -- it vanishes!", 'success'
                )
            else:
                self.add_message(
                    f"The {display} splashes {the_name(monster, lower=True)} but nothing happens.", 'info'
                )
            return

        # --- Stat drain (damage the monster instead) ---
        if effect in ('drain_str', 'drain_con', 'drain_int', 'drain_wis'):
            dmg = max(1, monster.max_hp // 20)
            actual = monster.take_damage(dmg)
            self.add_message(
                f"The {display} saps {the_name(monster, lower=True)}'s vitality! ({actual} damage)", 'success'
            )
            return

        # --- Everything else: no meaningful effect on monsters ---
        self.add_message(
            f"The {display} splashes {the_name(monster, lower=True)} but has no effect.", 'info'
        )

    # ------------------------------------------------------------------
    # Combat utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _confused_name(m) -> str:
        """'The confused giant rat', or the hidden name ('Something unseen')
        for a creature the hero cannot see."""
        name = the_name(m)
        if name.startswith('The ') and name[4:] == m.name:
            return f"The confused {m.name}"
        return name

    def _nearest_visible_monster(self):
        """Return the closest alive monster the hero can see, or None (an
        invisible or hidden one is not offered: src/unseen.py)."""
        px, py = self.player.x, self.player.y
        best, best_dist = None, float('inf')
        for m in self.monsters:
            if self._sees_monster(m):
                d = abs(m.x - px) + abs(m.y - py)
                if d < best_dist:
                    best, best_dist = m, d
        return best

    # ------------------------------------------------------------------
    # On-kill side effects
    # ------------------------------------------------------------------

    def _answer_a_killing_blow(self):
        """Every ward against death, tried in order, when the player has been
        brought to 0 health by anything from outside: a monster, a spell, a
        trap, poison, a curse. (Not hunger: Player.is_dead does not call this
        for starvation.)

        These lived inside the monster-attack loop, so they answered a
        monster's blow and nothing else: poison, a trap or a chest's needle
        killed straight through the Amulet of Life Saving, the Jade Cicada and
        Joan's breastplate, each of which says it stops a killing blow."""
        if self.player.hp > 0:
            return
        # Jade Cicada: death save (once per floor).
        # death_save_bonus (chain-equip) adds to the d20 roll determining
        # whether non-Cicada death-saves succeed — and `life_save_resets_per_floor`
        # refreshes the `life_save` status effect each floor.
        if self.player.hp <= 0 and not getattr(self, '_death_save_used', False):
            for _acc in self.player.equipped_accessories:
                if getattr(_acc, 'death_save', False):
                    self.player.hp = 1
                    self._death_save_used = True
                    self.add_message("The jade cicada cracks — but holds! You cling to life!", 'success')
                    _snd.play('player_healed')
                    break

        # Chain-equip passive: reassembly (Tyet of Isis T5) — once per run,
        # restore to full HP + 10 turns regen on lethal damage.
        if self.player.hp <= 0:
            try:
                from chain_passives import consume_run_passive
                if consume_run_passive(self.player, 'reassembly'):
                    self.player.hp = self.player.max_hp
                    self.player._reassembly_regen_remaining = 10
                    self.add_message(
                        "The Tyet of Isis reassembles you from death!", 'success')
            except ImportError:
                pass

        # Breastplate of Joan (maid_does_not_fall): per-floor death save —
        # first lethal hit each floor heals back to 1 HP. Joan fought
        # wounded at Orléans, Patay, Reims; "could not protect against
        # what God willed" but kept her standing through three campaigns.
        if self.player.hp <= 0:
            try:
                from armor_procs import consume_floor_charge
                if consume_floor_charge(self.player, 'maid_does_not_fall'):
                    self.player.hp = 1
                    self.add_message(
                        "BY COMMAND OF GOD — the Maid does not fall! You stand at 1 HP.",
                        'success')
                    _snd.play('player_healed')
            except ImportError:
                pass

        # Chain-equip passive: second_beheading_returns (Green Knight's Plate).
        # On death, revive at full HP next floor; armor is broken.
        if self.player.hp <= 0:
            try:
                from chain_passives import (
                    consume_run_passive, find_passive_item,
                )
                if consume_run_passive(self.player, 'second_beheading_returns'):
                    self.player.hp = self.player.max_hp
                    self.add_message(
                        "GREEN KNIGHT'S OATH: your second beheading returns!", 'success')
                    # Break the armor: clear its chain bonuses
                    _src = find_passive_item(self.player, 'second_beheading_returns')
                    if _src is not None and _src in self.player.armor_slots:
                        idx = self.player.armor_slots.index(_src)
                        self.player.armor_slots[idx] = None
                        self.player.shed_worn_grants(_src)
            except ImportError:
                pass

        # Chain-equip passive: doom_of_the_gods (Armor of Ragnarok T5).
        # On player death, fire a massive AoE blast — last stand against everyone.
        if self.player.hp <= 0:
            try:
                from chain_passives import (
                    consume_run_passive, find_passive_item,
                )
                _src = find_passive_item(self.player, 'doom_of_the_gods')
                if _src is not None and consume_run_passive(self.player, 'doom_of_the_gods'):
                    # The world burns and one walks out of it. Each foe
                    # near loses a share of ITS OWN health (a named foe
                    # a tenth of that); the wearer is left at 1; the
                    # armor is spent. It used to blast for the wearer's
                    # max health, a sixth of a deep monster's, announce
                    # them "annihilated", and leave the wearer dead.
                    from floor_curve import wound
                    px, py = self.player.x, self.player.y
                    _hits = _kills = 0
                    for mm in list(self.monsters):
                        if not mm.alive or abs(mm.x - px) + abs(mm.y - py) > 6:
                            continue
                        _named = bool(getattr(mm, 'is_boss', False)
                                      or 'legendary' in (getattr(mm, 'tags', None) or ()))
                        mm.take_damage(wound(DOOM_SHARE, mm.max_hp, named=_named))
                        _hits += 1
                        if not mm.alive:
                            _kills += 1
                            self._on_monster_killed(mm)
                        else:
                            # Whatever lives through it is thrown down
                            # for DOOM_STAGGER turns: without this the
                            # next foe in the same turn finished the
                            # wearer and the armor bought nothing.
                            mm.status_effects['paralyzed'] = max(
                                int(mm.status_effects.get('paralyzed', 0) or 0), DOOM_STAGGER)
                    self.player.hp = 1
                    if _hits:
                        self.add_message(
                            f"DOOM OF THE GODS! Your armor erupts: {_hits} "
                            f"{'foe is' if _hits == 1 else 'foes are'} burned, {_kills} destroyed, the rest thrown down. "
                            "You stand in the ash with 1 health.", 'success')
                    else:
                        self.add_message(
                            "DOOM OF THE GODS! Your armor erupts and is gone. "
                            "You stand in the ash with 1 health.", 'success')
                    if _src in self.player.armor_slots:
                        idx = self.player.armor_slots.index(_src)
                        self.player.armor_slots[idx] = None
                    self.player.shed_worn_grants(_src)
            except ImportError:
                pass

        # Chain-equip passive: psychopomp_step (Winged Sandals of Hermes T5).
        # On death, ascend one floor with 1 HP. Once per run.
        if self.player.hp <= 0 and self.dungeon_level > 1:
            try:
                from chain_passives import consume_run_passive
                if consume_run_passive(self.player, 'psychopomp_step'):
                    self.player.hp = 1
                    self.add_message(
                        "WINGED SANDALS OF HERMES: a psychopomp's step pulls you back!", 'success')
                    from boss_levels import COW_LEVEL as _COW
                    if self.dungeon_level == _COW:
                        # One floor up from the Cow Level (999) was floor
                        # 998: back to the floor the cow stood on instead.
                        self._exit_cow_level()
                    else:
                        self._change_level(self.dungeon_level - 1, enter_from_top=False, via='warp')
            except ImportError:
                pass

        # Ankh of Isis: resurrect on death (consumes the item).
        if self.player.hp <= 0:
            for _acc in self.player.equipped_accessories:
                if getattr(_acc, 'resurrect_on_death', False):
                    # C07: what the Ankh lent comes off with it, as a plain
                    # unequip does (its +2 CON stayed for ever), before the
                    # new health is measured against the true max.
                    try:
                        from chain_equip import is_chain_equip, revert_tier_bonuses
                        if is_chain_equip(_acc) and int(getattr(_acc, 'achieved_tier', 0) or 0) > 0:
                            revert_tier_bonuses(self.player, _acc)
                    except ImportError:
                        pass
                    _fx = getattr(_acc, 'effects', None) or {}
                    if 'stat' in _fx:
                        self.player.apply_stat_bonus(_fx['stat'], -_fx.get('amount', 0))
                    if 'stat2' in _fx:
                        self.player.apply_stat_bonus(_fx['stat2'], -_fx.get('amount2', 0))
                    self.player.hp = max(1, self.player.max_hp // 2)
                    # Clear the slot that held the Ankh
                    if self.player.amulet_slot is _acc:
                        self.player.amulet_slot = None
                    else:
                        for _i, _r in enumerate(self.player.accessory_slots):
                            if _r is _acc:
                                self.player.accessory_slots[_i] = None
                                break
                    if 'status' in _fx:
                        self._remove_status_if_no_other_grants(_fx['status'])
                    self.add_message(
                        "The Ankh of Isis shatters! Isis breathes life back into you!",
                        'success')
                    self._chron('loss', "I died. Then light. Isis pulled me back. The ankh is dust now.")
                    _snd.play('player_healed')
                    break

        # Life Save: if the blow was fatal, survive at 1 HP (burns the amulet)
        if self.player.hp <= 0 and self.player.has_effect('life_save'):
            self.player.hp = 1
            del self.player.status_effects['life_save']
            # The thing that gave it is spent with it. It was not, so
            # taking Excalibur or the amulet off and putting it back
            # on bought another life every time.
            _src = None
            for _it in ([self.player.weapon, getattr(self.player, 'ranged_weapon', None),
                         self.player.shield, getattr(self.player, 'amulet_slot', None),
                         getattr(self.player, 'belt_slot', None)]
                        + list(self.player.armor_slots) + list(self.player.accessory_slots)):
                if _it is None:
                    continue
                if getattr(_it, 'on_equip_status', '') == 'life_save':
                    _it.on_equip_status = ''
                    _src = _src or _it
                _fx = getattr(_it, 'effects', None)
                if isinstance(_fx, dict) and _fx.get('status') == 'life_save':
                    _it.effects = {k: v for k, v in _fx.items() if k != 'status'}
                    _src = _src or _it
            self.add_message(
                f"{'The ' + _src.name if _src is not None else 'A ward'} blazes -- death averted! "
                "Its life-saving magic is spent.", 'success'
            )
            _snd.play('player_healed')

    def _on_monster_killed(self, monster, *, chain_score: int = 0, ranged: bool = False,
                           unarmed: bool = False, hp_pct_before: float | None = None):
        """Central handler for ALL monster kills: treasure, corpse, boss popup, seal tracking,
        plus the canonical quirk on_kill hook.

        Combat callers pass chain_score/ranged/unarmed/hp_pct_before. Spell, wand, AOE, and
        trap kill paths use defaults (chain_score=0, ranged=False) and still fire the hook
        for kill-count quirks like Caesar, Kali, Boudicca, Leonidas, Battle Trance, etc.
        """
        # One death, one handling. A monster that died inside its own attack
        # with a fire shield up was handled twice: two corpses, two kills,
        # and for a boss two drops and two gifts.
        if getattr(monster, '_kill_handled', False):
            return
        # An invisible creature shows what it was as it falls: the kill and
        # its corpse are named.
        if getattr(monster, '_unseen', False):
            monster._unseen = False
        # The Black Knight is never killed: a killing blow is one more limb
        # (black_knight.BlackKnight), and at the end he is a torso calling it
        # a draw. A path that set him dead and came here finds him alive.
        if getattr(monster, 'is_black_knight', False):
            return
        _snd.play('boss_kill' if (getattr(monster, 'is_boss', False)
                                  or 'legendary' in (getattr(monster, 'tags', None) or ())
                                  or (getattr(monster, 'treasure', None) or {}).get('boss_scroll_id'))
                  else 'kill')
        self.level_mgr.monsters_killed += 1
        # Marker read by _process_collateral_kills so a monster handled here
        # is not processed a second time by the post-attack sweep.
        monster._kill_handled = True
        # Curtana's spare is announced by the melee on_complete (the spared
        # monster is alive, so this handler is never reached for it). The
        # flag used to be consumed HERE, which meant it sat armed until the
        # next real kill and swallowed that kill's loot and corpse instead.
        self.player._spared_this_attack = False
        self.add_message(f"{the_name(monster)} is slain!", 'success')
        self._drop_treasure(monster)
        # A thief gives back everything it stole (src/theft.py).
        for _tmsg in theft.give_back(self, monster):
            self.add_message(_tmsg, 'loot')

        # Cadmus / Vel of Murugan / Shamshir (engine wave 4):
        # summon_after_kill_with_tag — combat side set _pending_summon
        # with details; we spawn a temp ally Pet here.
        _ps = getattr(self.player, '_pending_summon', None)
        if _ps:
            self.player._pending_summon = None
            try:
                # (Pet and random_pet_species come from the module imports. A
                # local `from pet_system import ... random_pet_species` named a
                # function that does not exist; the except below swallowed the
                # ImportError and no kill-summon ally ever appeared.)
                _spawn_x, _spawn_y = _ps.get('spawn_at', (self.player.x, self.player.y))
                # Adjacent fallback if spawn tile occupied
                if (_spawn_x, _spawn_y) in self._occupants(hero=False) \
                        or not self.dungeon.is_walkable(_spawn_x, _spawn_y):
                    for _dx in (-1, 0, 1):
                        for _dy in (-1, 0, 1):
                            if _dx == 0 and _dy == 0:
                                continue
                            _nx, _ny = _spawn_x + _dx, _spawn_y + _dy
                            if (self.dungeon.is_walkable(_nx, _ny)
                                    and (_nx, _ny) not in self._occupants(hero=False)):
                                _spawn_x, _spawn_y = _nx, _ny
                                break
                _species = random_pet_species()
                _ally = Pet(_species, _spawn_x, _spawn_y)
                # It springs from the slain creature and is as strong as that
                # creature was (its own level, from monsters.json).
                _ally.level = _monster_level(monster)
                _ally._refresh_stats()
                # Temp pet: scale max_hp + flag duration.
                _max_pct = float(_ps.get('max_hp_pct', 0.5) or 0.5)
                _ally.max_hp = max(5, int(_ally.max_hp * _max_pct))
                _ally.hp = _ally.max_hp
                _ally._temp_duration = int(_ps.get('duration_turns', 5) or 5)
                self.pets.append(_ally)
                self.add_message(
                    f"From the slain {monster.name} {self._a_or_an(_ally.name)} springs forth — bound to your side!",
                    'success')
            except Exception:
                pass

        # Zireael (engine wave 3): extra_action_after_kill — Ciri's speed.
        # On kill, apply 1-turn haste so the player effectively gets a free
        # action. Capped at once per combat turn via _zireael_used_this_turn
        # which the turn-advance code clears.
        _w_zir = self.player.weapon
        if (_w_zir and getattr(_w_zir, 'extra_action_after_kill', False)
                and not getattr(self.player, '_zireael_used_this_turn', False)):
            self.player.add_effect('hasted', 1)
            self.player._zireael_used_this_turn = True

        # Pharaoh's Crook / Cain's Club / Oathkeeper (engine wave 3):
        # equipped_ally_aura_buff_str — pets within 5 tiles get +N STR.
        # Apply on every kill to refresh. Reverses naturally when pet
        # exits the radius or weapon is unequipped (re-checked here).
        for _slot in (self.player.weapon, getattr(self.player, 'ranged_weapon', None)):
            _bonus = int(getattr(_slot, 'equipped_ally_aura_buff_str', 0) or 0) if _slot else 0
            if _bonus > 0:
                _px, _py = self.player.x, self.player.y
                for _pet in self.pets:
                    if (getattr(_pet, 'alive', False)
                            and abs(_pet.x - _px) <= 5 and abs(_pet.y - _py) <= 5):
                        # Idempotent — only apply once per pet per equip
                        if not getattr(_pet, '_aura_str_applied_by', None):
                            cur_str = int(getattr(_pet, 'STR', 0) or 0)
                            if cur_str > 0:
                                _pet.STR = cur_str + _bonus
                                _pet._aura_str_applied_by = id(_slot)
        # Quirk on_kill hook — single canonical call site
        qs = getattr(self, 'quirk_system', None)
        if qs:
            if hp_pct_before is None:
                hp_pct_before = self.player.hp / max(1, self.player.max_hp)
            qs.on_kill(
                monster_kind=monster.kind,
                chain_score=chain_score,
                ranged=ranged,
                unarmed=unarmed,
                hp_pct_before=hp_pct_before,
                is_feared=self.player.has_effect('feared'),
            )
        # Boss narrative popup
        story_key = self._BOSS_STORY_KEYS.get(monster.kind)
        if story_key and self.player.is_dead():
            story_key = None          # a pet finished it after the player fell
        if story_key:
            self._show_story_popup(story_key, STATE_PLAYER)
            _BOSS_CHRONICLE = {
                'asterion_minotaur': "Killed the Minotaur. His name was Asterion, and he was bigger than I expected. The Labyrinth is quiet now.",
                'medusa_gorgon': "Medusa is dead. I never once looked straight at her. Even the snakes were afraid at the end.",
                'fafnir_dragon': "Fafnir fell. His scales were like iron and I still smell the smoke on my clothes.",
                'fenrir_wolf': "Fenrir is bound, or dead. I am not sure which. The wolf was vast, and the ground still shakes.",
                'abaddon_destroyer': "Abaddon is destroyed. The Pit is sealed. I can barely hold the pen.",
            }
            self._chron('boss', _BOSS_CHRONICLE.get(monster.kind, f"Killed {monster.name}. It is done."),
                        once=f'boss:{monster.kind}')
        # Mini-bosses and legends: their death is an event in the run's story.
        # (Only the five gate bosses were ever recorded.)
        if (getattr(monster, 'is_mini_boss', False) and not story_key
                and not getattr(monster, 'is_seal_demon', False)):
            self._chron(
                'boss',
                getattr(monster, 'kill_chronicle', '')
                or f"{the_name(monster)} is dead. I had not expected to be the one left standing.",
                once=f'boss:{monster.kind}')
        # A gate boss leaves three gifts; the player takes one (boons.py).
        # Only noted here: main.update opens the choice once the kill, its
        # messages and the story popup are finished.
        import boons
        if (boons.offer_for(monster.kind) and not self.player.is_dead()
                and not boons.already_taken(self.player, monster.kind)):
            self.player.pending_boon = monster.kind
        # A guardian whose death unbars the stair (the Labyrinth).
        if getattr(self.dungeon, 'stairs_guardian', None) == monster.kind:
            self.add_message(
                getattr(self.dungeon, 'stairs_guardian_open_line', '')
                or "The way down stands open.", 'success')
        # Fafnir drops a unique blood potion with a hint about the throw-over reforge
        if monster.kind == 'fafnir_dragon':
            self._spawn_fafnir_blood(monster.x, monster.y)
        # Abaddon guards the Philosopher's Stone; it falls where he does.
        if monster.kind == 'abaddon_destroyer':
            self._drop_philosophers_stone(monster.x, monster.y)
            # Every trait point still held for a deeper floor comes in now.
            for _stat, _n in self.player.pay_quirk_stats_owed(everything=True):
                self.add_message(
                    f"A trait you earned comes into its own: {_stat} +{_n}.", 'success')
        # Seal demon: track broken seal
        if getattr(monster, 'is_seal_demon', False):
            seal_id = 'seal_of_' + monster.kind.replace('seal_demon_', '')
            self.seals_broken.add(seal_id)
            count = len(self.seals_broken)
            _ORD = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh']
            _SEAL_WORDS = ['one', 'two', 'three', 'four', 'five', 'six', 'seven']
            _short = monster.name.split(',')[0]
            self.add_message(
                f"{_short} falls. The {_ORD[min(count, 7) - 1]} of seven seals is broken.",
                'success')
            self._chron('boss', f"Broke a seal. {monster.name} is gone. That makes "
                                f"{_SEAL_WORDS[min(count, 7) - 1]} of the seven. The air feels heavier.",
                        once=f'seal:{seal_id}')
            if count == 7:
                self.add_message(
                    "ALL SEVEN SEALS ARE BROKEN. The way to the Pit stands open.", 'danger')
                self._chron('boss', "All seven seals are broken. The ground split open. Whatever is down there, it's free now. And I have to face it.")
        self.ground_items.append(self._make_corpse(monster))

    def _announce_scale_hit(self, monster, damage: int):
        """Tell the player what the scales did to that blow."""
        if getattr(self.player, '_ward_blocked', False) and damage > 0:
            self.player._ward_blocked = False
            if not getattr(monster, '_ward_hint_shown', False):
                monster._ward_hint_shown = True
                self.add_message(
                    f"Your blow sinks into the dark around {the_name(monster, lower=True)} "
                    f"and half of it is lost there.", 'warning')
        if getattr(monster, '_recovered_note', False):
            monster._recovered_note = False
            if monster.alive:
                self.add_message(
                    f"{the_name(monster)} has had time to mend. Wounds you gave have closed.",
                    'warning')
        if not getattr(monster, 'dragon_scales', 0) or damage <= 0:
            return
        if getattr(self.player, '_belly_strike', False):
            self.add_message(
                f"From the pit you strike up under the scales, into "
                f"{the_name(monster, lower=True)}'s soft belly.", 'success')
        elif not getattr(self.player.weapon, 'ignore_resistances', False):
            if not getattr(monster, '_scale_hint_shown', False):
                monster._scale_hint_shown = True
                self.add_message(
                    f"Your blow skates off {the_name(monster, lower=True)}'s scales. "
                    f"Only a little of it gets through.", 'warning')
        self.player._belly_strike = False

    # The Destroyer's swarms (not the cult's soldiers, who are only men).
    _LOCUST_KINDS = frozenset({'abyssal_locust', 'locust_swarmlord'})

    def _locust_calmed(self, m) -> bool:
        """A locust leaves the wearer of the Locust Charm alone until it is
        struck (``_struck``, set by Monster.take_damage)."""
        if m.kind not in self._LOCUST_KINDS and 'locust' not in (m.tags or ()):
            return False
        if getattr(m, '_struck', False):
            return False
        p = self.player
        if not (hasattr(p, 'amulet_slot') and hasattr(p, 'accessory_slots')):
            return False
        return any(getattr(a, 'calms_locusts', False) for a in p.equipped_accessories)

    def _green_girdle_spares(self, monster) -> bool:
        """The Green Girdle (Gawain's, from Lady Bertilak): the Green Knight's
        return blow, the one he strikes after his head is back on, cannot
        kill its wearer. Called when such a blow has just brought the hero
        to 0: the hero is left at 1, and told why.

        It turns ONE blow, as the story says, then it is spent on this knight
        (`_girdle_spent`, saved with him; bug bash 5 INT-04: it used to turn
        every killing blow he struck, so he could never kill its wearer)."""
        if getattr(monster, 'kind', '') != 'green_knight' or not getattr(monster, '_has_revived', False):
            return False
        if monster.__dict__.get('_girdle_spent', False):
            return False
        p = self.player
        worn = list(getattr(p, 'armor_slots', None) or ()) + [getattr(p, 'belt_slot', None)]
        if not any(getattr(w, 'id', '') == 'green_girdle' for w in worn if w is not None):
            return False
        if p.hp > 0:
            return False
        p.hp = 1
        monster.__dict__['_girdle_spent'] = True
        self.add_message(
            'The axe stops a hair from your neck, and the Green Knight laughs. '
            '"You lacked a little loyalty," he says. "But only a little, and for love of your life."',
            'warning')
        # once=: the Journal remembers it was written, across a reload.
        self._chron(
            'deed',
            "The Green Knight's axe should have taken my head. The green girdle turned it. "
            "He laughed and called it a little disloyalty. I think he was being kind.",
            once='green_girdle')
        return True

    def _death_gives_back_a_breath(self, hp_before: int) -> bool:
        """Death's Chessboard (H07): a hero who beat Death at chess for their
        own life holds the deed ``flag.deaths_lost_turn``. Once, on the ascent,
        the blow from Death's pursuit that would have killed them misses: the
        hero's health is put back as it was before the blow. The deed
        ``flag.deaths_lost_turn_spent`` records that the breath is used."""
        import deeds
        reg = self._deeds_reg()
        if not deeds.has(reg, 'flag.deaths_lost_turn') or deeds.has(reg, 'flag.deaths_lost_turn_spent'):
            return False
        deeds.note(self, 'flag.deaths_lost_turn_spent', source='engine:death_pursuit', unique=True)
        self.player.hp = max(1, int(hp_before))
        self.add_message(
            "The scythe comes down through the place where you were a breath ago. "
            "Death looks at the blade, and then at you, and nods. One breath, as promised.",
            'warning')
        self._chron(
            'deed',
            "Death swung, and missed on purpose. He had promised me one breath back at the "
            "chessboard. He is very exact about promises.")
        return True

    def _announce_revive(self, monster):
        """The Green Knight's beheading game: say so when a foe that should
        have died stands back up. take_damage set `_just_revived` and nothing
        ever read it, so his health bar simply refilled in silence."""
        if not getattr(monster, '_just_revived', False):
            return
        monster._just_revived = False
        line = getattr(monster, 'revive_message', '') or (
            f"{the_name(monster)} should be dead, and is getting up.")
        self.add_message(line, 'danger')
        self._chron('notice',
                    f"I struck {the_name(monster, lower=True)} down and it stood back up.",
                    once=f'revive:{monster.kind}')

    def _drop_philosophers_stone(self, x: int, y: int):
        """Place the Stone at (x, y) unless one already exists in this run
        (a save made on floor 100 before this change has one on the floor)."""
        def _is_stone(it):
            return getattr(it, 'id', '') == 'philosophers_stone'
        if any(_is_stone(i) for i in self.ground_items) \
                or any(_is_stone(i) for i in self.player.inventory):
            return
        from level_manager import spawn_stone_at
        stone = spawn_stone_at(x, y)
        if stone is None:
            return
        self.ground_items.append(stone)
        self.add_message(
            "Where the Destroyer stood, something small and warm lies on the "
            "scorched stone.", 'loot')

    def _open_boon_menu(self) -> bool:
        """Show a fallen gate boss's three gifts. Returns True if it opened."""
        import boons
        from game_states import STATE_BOON_MENU
        kind = getattr(self.player, 'pending_boon', None)
        if not kind or self.state != STATE_PLAYER or self.player.is_dead():
            return False
        if boons.already_taken(self.player, kind) or not boons.offer_for(kind):
            self.player.pending_boon = None
            return False
        self._boon_kind = kind
        self.state = STATE_BOON_MENU
        _snd.play('boon')
        return True

    def _boon_pick(self, index: int):
        import boons
        kind = getattr(self, '_boon_kind', None) or getattr(self.player, 'pending_boon', None)
        got = boons.take(self.player, kind, index) if kind else None
        if got is None:
            return
        gift, amount = got
        self.player.pending_boon = None
        self._boon_kind = None
        self.state = STATE_PLAYER
        self.add_message(gift['text'], 'success')
        self.add_message(
            f"You take {gift['name']}: {boons.STAT_NAMES.get(gift['stat'], gift['stat'])} "
            f"+{amount}, for good.", 'success')
        from chronicle import in_sentence
        self._chron('discovery', f"I took {in_sentence(gift['name'])} and left the other two where they lay.")

    def _drop_treasure(self, monster):
        """Drop gold and possibly an item when a monster dies."""
        import random as _rng
        treasure = getattr(monster, 'treasure', {})
        gold_range = treasure.get('gold', [0, 0])
        gold = _rng.randint(int(gold_range[0]), max(int(gold_range[0]), int(gold_range[1])))
        if gold > 0:
            from items import add_gold_to_tile
            add_gold_to_tile(self.ground_items, gold, monster.x, monster.y)
            self.add_message(
                f"{the_name(monster)} drops {gold:,} gold coins.", 'loot'
            )
        item_chance = treasure.get('item_chance', 0.0)
        if _rng.random() < item_chance:
            item_tier = int(treasure.get('item_tier', 1))
            self._spawn_treasure_item(monster.x, monster.y, item_tier)

        # Archer ammo drop: monsters with bows/crossbows in their attack
        # profile carry their own ammo. Per-profile chance + count_range
        # tuned in data/monsters.json under treasure.ammo_drop.
        ammo_drop = treasure.get('ammo_drop')
        if ammo_drop and _rng.random() < float(ammo_drop.get('chance', 0.65)):
            cmin, cmax = ammo_drop.get('count_range', [3, 8])
            count = _rng.randint(int(cmin), int(cmax))
            self._spawn_archer_ammo(monster.x, monster.y,
                                    ammo_drop['ammo_id'], count)

        # Boss reward scroll
        boss_scroll_id = treasure.get('boss_scroll_id')
        if boss_scroll_id:
            self._spawn_boss_scroll(monster.x, monster.y, boss_scroll_id)

        # Unique mini-boss drop
        unique_drop_id = treasure.get('unique_drop_id')
        if unique_drop_id:
            self._spawn_unique_item(monster.x, monster.y, unique_drop_id)

    def _spawn_archer_ammo(self, x: int, y: int, ammo_id: str, count: int):
        """Drop a stack of `count` ammo items at (x, y). Used by archer
        monsters whose treasure profile names an ammo_id."""
        from items import load_items, copy_at
        try:
            ammos = load_items('ammo')
            template = next((a for a in ammos if a.id == ammo_id), None)
            if template:
                stack = copy_at(template, x, y)
                stack.count = count
                self.ground_items.append(stack)
        except Exception:
            pass

    def _make_corpse(self, monster):
        """Create a Corpse for a monster, auto-identifying it if the type is already known."""
        from items import Corpse
        c = Corpse(
            monster.name, monster.kind, monster.x, monster.y,
            harvest_tier=monster.harvest_tier,
            harvest_threshold=monster.harvest_threshold,
            ingredient_id=monster.ingredient_id,
            lore=getattr(monster, 'lore', ''),
            monster_def={
                'hp': monster.max_hp,
                'thac0': monster.thac0,
                'attacks': monster.attacks,
                'resistances': monster.resistances,
                'weaknesses': monster.weaknesses,
                'speed': monster.speed,
                # tags drive the bestiary family line — must be on the corpse.
                'tags': list(getattr(monster, 'tags', []) or []),
                # peak_floor drives the identify-question tier (depth-first).
                'peak_floor': int(getattr(monster, 'peak_floor', 0) or 0),
            },
        )
        # A studied monster type is known forever: its corpses spawn
        # pre-identified (one-question identify, True Name model).
        if monster.kind in getattr(self.player, 'lore_known_monster_ids', set()):
            c.id_level = 5
        return c

    def _spawn_treasure_item(self, x: int, y: int, tier: int):
        """Place a random COMMON item of up to `tier` at (x,y).

        Uniques are explicitly excluded — they come from `unique_drop_id`
        (mini-boss fixed drops) and rare chest rolls, not from regular
        monster treasure. Weapon/armor/shield commons are template-
        instantiated; the JSON files only hold uniques.
        """
        import random as _rng
        from items import (load_items, copy_at, is_random_loot,
                            pick_random_weapon_for_floor,
                            pick_random_armor_for_floor,
                            pick_random_shield_for_floor)
        # Loot is at least as deep as the floor it drops on. The old rule was
        # tier * 5 alone and tiers stop at 5, so everything past floor 25
        # (Anansi on floor 92 included) dropped floor-25 gear.
        _here = int(getattr(self, 'dungeon_level', 1) or 1)
        if not 1 <= _here <= 100:      # the Cow Level is numbered 999
            _here = max(1, min(100, int(getattr(self, '_cow_return_level', 1) or 1)))
        # ...and only a little deeper (items.loot_floor): `tier * 5` on its
        # own put floor-5 and floor-10 gear in floor-1 drops.
        from items import loot_floor
        effective_floor = max(_here, min(tier * 5, loot_floor(_here, tier * 5)))

        # 50% weapon/armor/shield (template+material common), 50% magic item pool
        roll = _rng.random()
        if roll < 0.30:
            gear = pick_random_weapon_for_floor(effective_floor, _rng)
        elif roll < 0.40:
            gear = pick_random_armor_for_floor(effective_floor, _rng)
        elif roll < 0.50:
            gear = pick_random_shield_for_floor(effective_floor, _rng)
        else:
            gear = None
            candidates = []
            for cls_name in ('accessory', 'wand', 'scroll', 'potion', 'ammo'):
                try:
                    for item in load_items(cls_name):
                        if getattr(item, 'is_unique', False):
                            continue
                        if not is_random_loot(item):     # scripted rewards
                            continue
                        if item.min_level <= effective_floor:
                            candidates.append(item)
                except Exception:
                    pass
            if candidates:
                # Weighted by each item's own floor spawn weight (a flat
                # choice made a harmful potion as likely as a healing one).
                from container_system import _weighted_common_pick
                gear = _weighted_common_pick(candidates, effective_floor, _rng)

        if gear is not None:
            chosen = copy_at(gear, x, y) if hasattr(gear, 'id') else gear
            chosen.x, chosen.y = x, y
            from dungeon import dress_spawn
            dress_spawn(chosen, effective_floor, _rng, buc=False)   # charges and counts only
            self.ground_items.append(chosen)
            self.add_message(f"It drops {self._display_name(chosen)}!", 'loot')

    # ------------------------------------------------------------------
    # Ranged targeting
    # ------------------------------------------------------------------

    def _open_targeting(self):
        """Enter targeting mode for ranged attacks (f key)."""
        weapon = self.player.ranged_weapon
        if not weapon or not weapon.requires_ammo:
            self.add_message("You have no ranged weapon equipped.", 'warning')
            return

        # Check ammo (skip for infinite ammo weapons like Sling of David)
        ammo_type = weapon.requires_ammo
        if not getattr(weapon, 'infinite_ammo', False):
            ammo_items = [i for i in self.player.inventory
                          if getattr(i, 'ammo_type', None) == ammo_type]
            if not ammo_items:
                self.add_message(
                    f"You have no {ammo_type}s! Cannot fire the {self._bare_name(weapon)}.", 'warning'
                )
                return

        # Build candidate list: alive monsters within weapon reach + ammo
        # (visibility NOT required as of 2026-05-30 — projectile traces and
        # hits first obstacle in path, so unseen monsters in corridors are
        # legitimate targets and walls absorb mis-fires).
        px, py = self.player.x, self.player.y
        from combat import can_ranged_attack
        candidates = [
            m for m in self.monsters
            if m.alive and can_ranged_attack(self.player, m, self.dungeon)
        ]
        candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))

        self._target_candidates = candidates
        self._target_idx = 0
        self._melee_targeting = False

        if candidates:
            m = candidates[0]
            self.target_cursor_x = m.x
            self.target_cursor_y = m.y
        else:
            # No valid targets -- cursor starts on player
            self.target_cursor_x = px
            self.target_cursor_y = py

        self.state = STATE_TARGET
        if candidates:
            self.add_message(
                f"Targeting with the {self._bare_name(weapon)} -- arrow keys to move, TAB to cycle, ENTER to fire, ESC to cancel.",
                'info'
            )
        else:
            self.add_message(
                f"No targets in range for the {self._bare_name(weapon)}. Move cursor with arrow keys, ENTER to fire, ESC to cancel.",
                'info'
            )

    def _confirm_wand_target(self):
        """Confirm wand target, then start the science quiz."""
        from combat import _line_of_sight
        cx, cy = self.target_cursor_x, self.target_cursor_y
        self._wand_targeting = False
        wand = self._pending_wand
        self._pending_wand = None

        target = monster_at_tile(self.monsters, cx, cy)
        if not target or (cx, cy) not in self.visible:
            self.add_message("No valid target.", 'warning')
            self.state = STATE_PLAYER
            return

        # Line of sight check
        if not _line_of_sight(self.player.x, self.player.y, cx, cy, self.dungeon):
            self.add_message("No clear line of sight!", 'warning')
            self.state = STATE_PLAYER
            return

        # Store target for the quiz callback
        self._wand_target_monster = target
        display = self._display_name(wand)
        self.quiz_title = f"INVOKING {display.upper()}  --  SCIENCE"
        self.state = STATE_QUIZ
        _was_identified = getattr(wand, 'identified', False) or wand.id in self.player.known_item_ids

        def on_complete(result):
            self.state = STATE_PLAYER
            wand.identified = True
            self.player.known_item_ids.add(wand.id)
            _qs_wand = getattr(self, 'quirk_system', None)
            if _qs_wand:
                _qs_wand.on_wand_zapped(wand.id, was_identified=_was_identified)

            # v2.11.0: charge consumed REGARDLESS of success. Fail = wasted zap.
            wand.charges -= 1

            if not result.success:
                self.add_message(
                    "The wand fizzes and fails to fire -- the charge is wasted.",
                    'warning')
                if wand.charges <= 0:
                    self.add_message(
                        "The wand crumbles to dust -- it is spent.", 'warning')
                    self.player.remove_from_inventory(wand)
                self._advance_turn()
                return

            # Cursed misfire (3% on TOP of the fail-consumes-charge rule)
            import random as _rng_wand
            if getattr(wand, 'buc', 'uncursed') == 'cursed' and _rng_wand.random() < 0.03:
                self.add_message(
                    "The cursed wand misfires! The charge is doubly wasted.",
                    'warning')
                if wand.charges <= 0:
                    self.add_message(
                        "The wand crumbles to dust -- it is spent.", 'warning')
                    self.player.remove_from_inventory(wand)
                self._advance_turn()
                return

            self._wand_chain = 0
            # Override auto-target with stored target
            self._wand_override_target = self._wand_target_monster
            self._apply_wand_effect(wand)
            self._wand_override_target = None
            if wand.charges <= 0:
                self.add_message("The wand crumbles to dust -- it is spent.", 'warning')
                self.player.remove_from_inventory(wand)
            else:
                self.add_message(f"({wand.charges} charges remain)", 'info')
            self._advance_turn()

        # v2.11.0: All wands use threshold=1 at the wand's authoritative tier.
        # Power is baked into wand.power per tier; no more chain-mode wands.
        self.quiz_engine.start_quiz(
            mode='threshold', subject='science',
            tier=getattr(wand, 'tier', wand.quiz_tier),
            callback=on_complete, threshold=1,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('science'),
            base_seconds=self.player.get_quiz_timer('science'),
        )

    def _confirm_power_target(self):
        """Confirm targeted power (e.g. Fire Breath)."""
        from combat import _line_of_sight
        cx, cy = self.target_cursor_x, self.target_cursor_y
        pid = getattr(self, '_pending_power', None)
        self._power_targeting = False
        self._pending_power = None

        target = monster_at_tile(self.monsters, cx, cy)
        if not target or (cx, cy) not in self.visible:
            self.add_message("No valid target.", 'warning')
            self._refund_pending_spell()
            self.state = STATE_PLAYER
            return
        if not _line_of_sight(self.player.x, self.player.y, cx, cy, self.dungeon):
            self.add_message("No clear line of sight!", 'warning')
            self._refund_pending_spell()
            self.state = STATE_PLAYER
            return

        if pid and pid.startswith('spell_'):
            # Targeted spell: start the quiz with this target
            spell = getattr(self, '_pending_spell', None)
            spell_id = getattr(self, '_pending_spell_id', None)
            self._pending_spell = None
            self._pending_spell_id = None
            self._pending_spell_paid = None
            self._pending_spell_free = False
            if spell:
                self._start_spell_quiz(spell, spell_id, target)
            return  # quiz handles state + advance_turn

        if pid == 'sketch_manifest':
            # Store target for quiz callback, then start AI escalator chain
            self._sketch_target_monster = target
            self.add_message(
                f"You begin sketching {the_name(target, lower=True)} with furious concentration...", 'info')
            self.quiz_title = "MANIFESTING  --  AI"
            self.state = STATE_QUIZ
            pl = self.player

            def _on_sketch_complete(result):
                chain = result.score
                monster = self._sketch_target_monster
                self._sketch_target_monster = None
                if chain == 0:
                    self.add_message(
                        "The sketch smudges and fades to nothing. The page goes blank.", 'warning')
                    self.state = STATE_PLAYER
                    self._advance_turn()
                    return
                duration = 5 * chain
                # Find a walkable tile adjacent to the player for the pet
                from pet_system import SketchedPet
                px, py = pl.x, pl.y
                placed = False
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
                    nx, ny = px + dx, py + dy
                    if (self.dungeon.is_walkable(nx, ny)
                            and not monster_at_tile(self.monsters, nx, ny) is not None
                            and (nx, ny) not in self._occupants(hero=False)):
                        pet = SketchedPet(monster, nx, ny, duration)
                        self.pets.append(pet)
                        placed = True
                        break
                if not placed:
                    # A little further out, never on the hero's own tile
                    # (MNK-07); with no room at all the sketch fades.
                    spot = self._escort_tile_near_hero()
                    if spot is None:
                        self.add_message(
                            "There is no room for the sketch to stand. It fades from the page.",
                            'warning')
                        self.state = STATE_PLAYER
                        self._advance_turn()
                        return
                    pet = SketchedPet(monster, *spot, duration)
                    self.pets.append(pet)
                self.add_message(
                    f"The sketch shimmers and peels off the page! "
                    f"A Sketched {monster.name} materializes! ({duration} turns)",
                    'success')
                pl.power_cooldowns['sketch_manifest'] = 500
                self.state = STATE_PLAYER
                self._advance_turn()

            self.quiz_engine.start_quiz(
                mode='escalator_chain',
                subject='ai',
                tier=1,
                callback=_on_sketch_complete,
                max_chain=5,
                wisdom=pl.WIS,
                timer_modifier=pl.get_quiz_timer_modifier(),
                extra_seconds=pl.get_quiz_extra_seconds('ai'),
                base_seconds=pl.get_quiz_timer('ai'),
            )
            return  # don't call _advance_turn or set STATE_PLAYER — quiz handles it

        if pid == 'stuffie_fire_breath':
            # Store cone target for quiz callback
            self._stuffie_cone_target = (cx, cy)
            self.add_message(
                "The Charmander Stuffie glows warm... focus your fire!", 'info')
            self.quiz_title = "FIRE BREATH  --  AI"
            self.state = STATE_QUIZ
            pl = self.player

            def _on_fire_breath(result):
                chain = result.score
                if chain == 0:
                    self.add_message(
                        "The Stuffie flickers and dims. The fire fizzles out.", 'warning')
                    self.state = STATE_PLAYER
                    self._advance_turn()
                    return
                from dice import roll as _fb_roll
                from combat import get_cone_tiles
                # Damage scales with chain: base 3d6, +1d6 per chain level
                dice = f'{2 + chain}d6'
                # A share of each target's own health (floor_curve.power_share).
                _share = floor_curve.power_share(_fb_roll(dice)) * self._int_share_factor()
                tcx, tcy = self._stuffie_cone_target
                px, py = pl.x, pl.y
                cone = get_cone_tiles(px, py, tcx, tcy, max_range=6)
                hits = 0
                kills = 0
                for m in list(self.monsters):
                    if m.alive and (m.x, m.y) in cone and (m.x, m.y) in self.visible:
                        m.take_damage(floor_curve.wound(_share, m.max_hp, m._is_named_foe()))
                        hits += 1
                        if not m.alive:
                            self._on_monster_killed(m)
                            kills += 1
                self.add_message(
                    "The Charmander Stuffie glows white-hot! "
                    f"You breathe a cone of fire! (chain {chain})", 'success')
                if hits:
                    self.add_message(
                        f"{hits} creatures engulfed: the fire takes {round(100 * _share)}% "
                        f"of each one's health! ({kills} slain)", 'combat')
                else:
                    self.add_message("The flames find no target.", 'info')
                pl.power_cooldowns['stuffie_fire_breath'] = 500
                self.state = STATE_PLAYER
                self._advance_turn()

            self.quiz_engine.start_quiz(
                mode='escalator_chain',
                subject='ai',
                tier=1,
                callback=_on_fire_breath,
                max_chain=5,
                wisdom=pl.WIS,
                timer_modifier=pl.get_quiz_timer_modifier(),
                extra_seconds=pl.get_quiz_extra_seconds('ai'),
                base_seconds=pl.get_quiz_timer('ai'),
            )
            return  # quiz handles state + advance_turn

        self.state = STATE_PLAYER
        self._advance_turn()

    def _confirm_observe(self):
        """Describe whatever is at the cursor position. Free action."""
        from dungeon import (STAIRS_UP, STAIRS_DOWN, ALTAR, FOUNTAIN, GRAVE,
                             THRONE, WATER, LAVA, ICE)
        cx, cy = self.target_cursor_x, self.target_cursor_y

        # Check if the tile is visible
        if (cx, cy) not in self.visible:
            self.add_message("You can't see that location.", 'info')
            self.state = STATE_PLAYER
            self._observe_targeting = False
            return

        found = False

        # Monster at cursor: only one the hero can see. A mimic still in its
        # disguise looks like the thing it imitates; an invisible creature
        # looks like nothing at all, unless he has felt it there.
        _hidden = monster_at_tile(self.monsters, cx, cy)
        monster = self._seen_monster_at(cx, cy)
        if _hidden is not None and monster is None:
            _disg = unseen.disguise(_hidden)
            if _disg:
                if _disg.get('tile'):
                    # Posing as part of the map: the same line the real
                    # feature gets, or Look tells the two apart (MON-08).
                    _feat = {'stairs_down': "Stairs leading down.",
                             'stairs_up': "Stairs leading up."}.get(_disg['tile'])
                    self.add_message(_feat or f"You see {self._a_or_an(_disg.get('name') or 'chest')}.",
                                     'info')
                else:
                    self.add_message(f"You see {self._a_or_an(_disg.get('name') or 'chest')} on the ground.",
                                     'info')
                # The same sharp-eyed check a mimic chest gets (below).
                if random.random() < min(0.85, 0.15 + self.player.PER * 0.04):
                    self.add_message("Something seems off... you could swear it just moved.",
                                     'warning')
                found = True
            elif getattr(_hidden, '_felt_at', None) == (cx, cy) and unseen.unseen(_hidden, self.player):
                self.add_message("You see nothing there, but you felt something.", 'info')
                found = True
        if monster:
            hp_pct = monster.hp / max(1, monster.max_hp)
            condition = (
                "uninjured" if hp_pct >= 1.0 else
                "lightly wounded" if hp_pct >= 0.7 else
                "wounded" if hp_pct >= 0.4 else
                "badly wounded" if hp_pct >= 0.15 else
                "near death"
            )
            self.add_message(
                f"You see {monster.name} ({condition}).", 'info'
            )
            found = True

        # Items at cursor
        from items import Container
        items_here = [i for i in self.ground_items if i.x == cx and i.y == cy]
        for item in items_here[:5]:
            dname = self._display_name(item)
            self.add_message(f"You see {dname} on the ground.", 'info')
            # Mimic detection via Observe — PER check
            if isinstance(item, Container) and getattr(item, 'is_mimic', False):
                import random as _prng
                per_chance = min(0.85, 0.15 + self.player.PER * 0.04)
                if _prng.random() < per_chance:
                    _OBSERVE_HINTS = [
                        "Something seems off… is that a tooth?",
                        "It glistens with what looks like saliva.",
                        "You could swear it just moved.",
                        "The hinges look oddly organic.",
                        "You notice a faint, predatory smell.",
                    ]
                    self.add_message(_prng.choice(_OBSERVE_HINTS), 'warning')
            found = True
        if len(items_here) > 5:
            self.add_message(f"...and {len(items_here) - 5} more items.", 'info')

        # Player's own tile
        if cx == self.player.x and cy == self.player.y and not found:
            if not items_here:
                self.add_message("You see yourself standing here.", 'info')
            found = True

        # Tile features
        tile = self.dungeon.tiles[cy][cx]
        _TILE_DESC = {
            STAIRS_UP:   "Stairs leading up.",
            STAIRS_DOWN: "Stairs leading down.",
            ALTAR:       "A sacred altar.",
            FOUNTAIN:    "A shimmering fountain.",
            GRAVE:       "A weathered gravestone.",
            THRONE:      "An ancient throne.",
            WATER:       "A pool of water.",
            LAVA:        "A pool of molten lava.",
            ICE:         "An icy floor.",
        }
        desc = _TILE_DESC.get(tile)
        if desc:
            self.add_message(desc, 'info')
            found = True

        if not found:
            self.add_message("You see nothing of interest.", 'info')

        # Return to player state — no turn cost
        self.state = STATE_PLAYER
        self._observe_targeting = False

    def _confirm_ranged_target(self):
        """Confirm a ranged shot at the cursor position.

        Per user 2026-05-30: the projectile flies along a Bresenham path from
        the player to the cursor. WHAT it hits depends on what's in the way —
        not on what the player can see.

          * First obstacle is a monster -> fire on that monster (full quiz).
          * First obstacle is a wall -> ammo is consumed, shot is wasted.
          * Path clear AND no monster at cursor -> ammo is consumed, shot
            vanishes into the darkness (the player aimed at empty space).
          * Path clear AND monster AT cursor -> fire on that monster.

        Result: a ranger with high PER (sight) can shoot down corridors with
        confidence; a ranger guessing into the dark spends ammo on hope.
        """
        self.state = STATE_PLAYER
        px, py = self.player.x, self.player.y
        cx, cy = self.target_cursor_x, self.target_cursor_y

        # Bail if cursor is on the player tile (degenerate aim)
        if (cx, cy) == (px, py):
            self.add_message("You cannot fire at yourself.", 'warning')
            return

        # Bail if no ranged weapon equipped
        weapon = self.player.ranged_weapon
        if not weapon or not weapon.requires_ammo:
            self.add_message("You have no ranged weapon equipped.", 'warning')
            return

        # Range check (matches _open_targeting / can_ranged_attack)
        reach = weapon.reach + max(0, self.player.PER - 10) // 3
        if max(abs(cx - px), abs(cy - py)) > reach:
            self.add_message("That tile is out of range.", 'warning')
            return

        # Trace projectile path. _find_first_monster_in_path returns the first
        # alive monster hit, or None if the path is blocked by wall or clear.
        # We need to distinguish wall-blocked vs clear-path, so do a parallel
        # trace here.
        first_monster, blocked_by_wall = self._trace_projectile_obstacle(px, py, cx, cy)

        if first_monster is not None:
            # Real shot — let _fire_ranged handle ammo + quiz
            self._fire_ranged(first_monster)
            return

        # Either wall-blocked or clear-no-target: consume ammo, message, advance turn.
        self._consume_ranged_ammo_for_miss(blocked_by_wall, cx, cy)

    def _trace_projectile_obstacle(self, x0, y0, x1, y1):
        """Bresenham trace from (x0,y0) to (x1,y1). Returns
        (monster_or_None, blocked_by_wall_bool). blocked_by_wall is True only
        if the path hit a wall BEFORE reaching the target tile."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x1 > x0 else -1
        sy = 1 if y1 > y0 else -1
        err = dx - dy
        cx, cy = x0, y0
        while True:
            if cx == x1 and cy == y1:
                break
            e2 = 2 * err
            step_x = e2 > -dy
            step_y = e2 < dx
            if step_x and step_y:
                if (not self.dungeon.is_walkable(cx + sx, cy)
                        and not self.dungeon.is_walkable(cx, cy + sy)):
                    return None, True  # corner blocked
            if step_x:
                err -= dy
                cx += sx
            if step_y:
                err += dx
                cy += sy
            if (cx, cy) != (x1, y1):
                for m in self.monsters:
                    if m.alive and is_at_tile(m, cx, cy):
                        return m, False
                if not self.dungeon.is_walkable(cx, cy):
                    return None, True
        # Reached target tile cleanly — check for monster on the target tile
        for m in self.monsters:
            if m.alive and is_at_tile(m, x1, y1):
                return m, False
        # Target tile itself unwalkable counts as wall hit
        if not self.dungeon.is_walkable(x1, y1):
            return None, True
        return None, False

    def _consume_ranged_ammo_for_miss(self, blocked_by_wall: bool, cx: int, cy: int):
        """Ammo cost + message for a ranged shot that didn't hit a monster.
        Either struck a wall or flew into empty space. Advances the turn."""
        weapon = self.player.ranged_weapon
        # Decrement ammo (skip for infinite-ammo weapons like Sling of David)
        if not getattr(weapon, 'infinite_ammo', False):
            ammo_type = weapon.requires_ammo
            ammo_item = min((i for i in self.player.inventory if getattr(i, 'ammo_type', None) == ammo_type),
                key=lambda i: (float(getattr(i, 'damage_bonus', 0) or 0), getattr(i, 'name', '')), default=None)
            if ammo_item is not None:
                if getattr(ammo_item, 'count', 1) > 1:
                    ammo_item.count -= 1
                else:
                    self.player.inventory.remove(ammo_item)
        if blocked_by_wall:
            self.add_message(
                f"Your {weapon.requires_ammo} strikes a wall and clatters to the floor.",
                'warning')
        else:
            self.add_message(
                f"Your {weapon.requires_ammo} flies into the darkness — no target.",
                'warning')
        self._advance_turn()

    def _confirm_melee_target(self):
        """Confirm a melee strike at the cursor position."""
        cx, cy = self.target_cursor_x, self.target_cursor_y
        self.state = STATE_PLAYER

        # 1. Monster at cursor -- melee combat
        target = monster_at_tile(self.monsters, cx, cy)
        if target:
            # C05: a reach weapon cannot strike through a wall or door.
            if not self._reach_line_clear(cx, cy):
                self.add_message("Something is in the way -- you cannot reach that far.",
                                 'warning')
                return
            self._start_combat(target)
            return

        # 2. Mystery altar at cursor
        from mystery_system import MysteryAltar
        altar = next(
            (item for item in self.ground_items
             if isinstance(item, MysteryAltar) and not item.activated
             and item.x == cx and item.y == cy),
            None
        )
        if altar is not None:
            self._start_mystery(altar)
            return

        # 3. Container at cursor -- mimic check / bash
        from items import Container
        from container_system import _spawn_mimic
        container = next(
            (item for item in self.ground_items
             if isinstance(item, Container) and not item.opened
             and item.x == cx and item.y == cy),
            None
        )
        if container is not None:
            if container.is_mimic:
                # Bash hits the mimic — player gets a free 10% HP strike
                mimic = _spawn_mimic(container, self.monsters, self.dungeon_level,
                                     dungeon=self.dungeon, avoid=(self.player.x, self.player.y))
                self.ground_items.remove(container)
                mname = mimic.name if mimic else 'mimic'
                bash_dmg = max(1, int(mimic.max_hp * 0.10))
                mimic.hp -= bash_dmg
                self.add_message(
                    f"You bash the {container.name} -- it shrieks! It's {self._a_or_an(mname)}!", 'danger'
                )
                self.add_message(
                    f"Your blow connects before it can react! ({bash_dmg} damage)", 'success'
                )
                _snd.play('monster_hit')
            else:
                # Bashing a real chest damages fragile contents
                self.add_message(
                    f"You bash the {container.name}. You hear something shatter inside.", 'warning'
                )
                container.bash_damaged = True
            self._advance_turn()
            return

        # 4. Dig pit -- shovel equipped, targeting walkable floor with no pit
        weapon = self.player.weapon
        if weapon and getattr(weapon, 'can_dig', False):
            tile = self.dungeon.tiles[cy][cx]
            from dungeon import FLOOR
            _pits = getattr(self.dungeon, 'pits', set())
            if tile == FLOOR and (cx, cy) not in _pits:
                self._dig_pit(cx, cy)
                return
            elif (cx, cy) in _pits:
                self.add_message("There's already a pit there.", 'info')
                return

        # 5. Empty tile -- swing at air (costs a turn; may reveal invisible monsters)
        self.add_message("You swing at the empty space!", 'info')
        self._advance_turn()

    # ------------------------------------------------------------------
    # Pit mechanics
    # ------------------------------------------------------------------

    def _dig_pit(self, x: int, y: int):
        """Dig a pit at (x, y). Costs 30 SP and 3 turns."""
        sp_cost = 30
        if self.player.sp < sp_cost:
            self.add_message("You're too exhausted to dig! (need 30 SP)", 'warning')
            return
        self.player.sp -= sp_cost
        if not hasattr(self.dungeon, 'pits'):
            self.dungeon.pits = set()
        self.dungeon.pits.add((x, y))
        self.add_message(
            "You dig a pit in the floor, deep enough to crouch in.", 'success')
        _snd.play('trap')
        if not getattr(self, '_chronicle_first_pit', False):
            self._chronicle_first_pit = True
            self._chron('milestone', "Dug a pit with the shovel. It took everything I had. "
                                     "Something is going to walk over it, and I want to watch.",
                        once='first_pit')
        # Costs 3 turns (advancing turn 3 times — monsters get 3 actions)
        for _ in range(3):
            self._advance_turn()
            if self.state == STATE_DEAD:
                return

    def _player_fall_in_pit(self, x: int, y: int):
        """Player walks onto a pit and falls in. Applies in_pit effect."""
        if self.player.has_effect('levitating'):
            self.add_message("You float over a pit.", 'info')
            return
        if self.player.has_effect('in_pit'):
            return  # already in a pit
        from dice import roll as _dice_roll
        dmg = floor_curve.hazard(_dice_roll('1d4'), self.player.max_hp)
        actual = self.player.take_damage(dmg, 'physical')
        # -1 = until the player climbs out (the move handler clears it). A
        # duration of 1 expired on the same turn's status tick, before any
        # monster acted, so the pit never protected or helped anyone.
        self.player.add_effect('in_pit', -1)
        self.add_message(f"You drop into the pit and crouch below the rim. ({actual} damage)", 'danger')
        if (x, y) == getattr(self.dungeon, 'old_pit', None) \
                and not getattr(self.dungeon, '_old_pit_seen', False):
            self.dungeon._old_pit_seen = True
            self.add_message(
                "This hole is old. Its rim is scorched black, and beside it "
                "the stone is scored as if by a sword's point.", 'info')

    # ------------------------------------------------------------------
    # Ranged attack resolution
    # ------------------------------------------------------------------

    def _spend_attack_reroll(self):
        """Spend the quiz reroll an attack just used (melee and ranged alike).

        Tablet of Destinies: mark the reroll used this floor. Chain-equip
        passive one_thousand_and_one consumes its per-floor charge instead.
        """
        if not getattr(self.quiz_engine, 'reroll_was_used', False):
            return
        if self._has_tablet_of_destinies() and not getattr(self, '_quiz_reroll_used', False):
            self._quiz_reroll_used = True
            self.add_message("The Tablet of Destinies cracks — fate rewritten!", 'info')
        else:
            try:
                from chain_passives import consume_passive_charge
                if consume_passive_charge(self.player, 'one_thousand_and_one'):
                    self.add_message(
                        "Scheherazade whispers another tale -- one more chance.",
                        'info')
            except ImportError:
                pass

    def _fire_ranged(self, monster):
        """Consume one ammo and launch the math chain quiz for a ranged shot."""
        # Health as the shot is loosed, for the traits that count kills made
        # while badly hurt. Only a melee attack recorded it, so an archer's
        # kills were judged on their health at their last sword swing.
        self._combat_hp_pct_before = self.player.hp / max(1, self.player.max_hp)
        weapon = self.player.ranged_weapon
        ammo_type = weapon.requires_ammo
        ammo_item = None

        # Chain combat v2: crossbow reload turn. After firing, the player is
        # locked out for one turn while cranking the string back. Bow / sling
        # have no reload cost.
        if getattr(weapon, 'weapon_class', '') == 'crossbow':
            if self.player.status_effects.get('reloading', 0) > 0:
                self.add_message(
                    "Still cranking the crossbow string -- one more turn to reload.",
                    'warning'
                )
                return

        # Consume one ammo item (skip for infinite ammo weapons)
        if not getattr(weapon, 'infinite_ammo', False):
            ammo_item = min((i for i in self.player.inventory if getattr(i, 'ammo_type', None) == ammo_type),
                key=lambda i: (float(getattr(i, 'damage_bonus', 0) or 0), getattr(i, 'name', '')), default=None)
            if not ammo_item:
                self.add_message(f"Out of {ammo_type}s!", 'warning')
                return

            # Decrement stack or remove
            if getattr(ammo_item, 'count', 1) > 1:
                ammo_item.count -= 1
            else:
                self.player.inventory.remove(ammo_item)

        self.state = STATE_QUIZ
        self.combat_target = monster
        # Short fixed title: the combat strip already names the target and
        # the weapon, so repeating them here only overflowed the header.
        self.quiz_title = "RANGED ATTACK  --  MATH"
        self._combat_is_ranged = True
        self._combat_ammo = ammo_item      # for the Strike Now preview

        def on_complete(damage: int, killed: bool, chain: int, stunned: bool = False,
                        knocked: bool = False, crit: bool = False, **kwargs):
            self.state = STATE_PLAYER
            self.combat_target = None
            self._fire_strike_finisher(monster, chain, damage, killed)
            self._announce_revive(monster)
            self._announce_scale_hit(monster, damage)
            # C01: a shot spends the Tablet / Scheherazade reroll exactly as
            # a melee swing does (it never did, so archers rerolled every shot).
            self._spend_attack_reroll()
            if chain == 0:
                self.add_message(
                    f"Your shot flies wide -- you miss {the_name(monster, lower=True)}!", 'warning'
                )
            else:
                self.add_message(
                    f"Chain x{chain}! Your {weapon.requires_ammo} strikes {the_name(monster, lower=True)} for {damage} damage!",
                    'success'
                )
                if killed:
                    self._on_monster_killed(
                        monster,
                        chain_score=chain,
                        ranged=True,
                        hp_pct_before=getattr(self, '_combat_hp_pct_before', 1.0),
                    )
            # Chain combat v2: after firing the crossbow, spin up the reload
            # cooldown. Value 2 → ticks to 1 at end-of-turn (blocks next fire),
            # then to 0 the turn after (fire again). Chain-15 crossbow special
            # sets `_crossbow_skip_reloads` to 3, letting the next 3 shots
            # skip the reload lockout ("Skip next 3 reloads" per the design).
            if getattr(weapon, 'weapon_class', '') == 'crossbow':
                skip = int(getattr(self.player, '_crossbow_skip_reloads', 0) or 0)
                if skip > 0:
                    self.player._crossbow_skip_reloads = skip - 1
                else:
                    self.player.status_effects['reloading'] = 2
            self._process_collateral_kills(monster, _alive_before, chain)
            self._advance_turn()

        # Tablet of Destinies: allow quiz reroll if not used this floor.
        # Chain-equip passive one_thousand_and_one (Ring of Scheherazade T5) also grants reroll.
        try:
            from chain_passives import is_charge_available
            _scheh_reroll = is_charge_available(self.player, 'one_thousand_and_one')
        except ImportError:
            _scheh_reroll = False
        self.quiz_engine._reroll_flag = (
            (self._has_tablet_of_destinies() and not getattr(self, '_quiz_reroll_used', False))
            or _scheh_reroll
        )
        # Engine wave 3: side-channel refs for combat-side mechanics. Ranged
        # path mirrors the melee path so flags like Kusanagi surrounded and
        # Oathkeeper adjacent-pet work on bow shots too.
        self.player._combat_monsters_ref = self.monsters
        self.player._combat_pets_ref = self.pets
        self.player._combat_game_ref = self
        self.player._combat_player_taken_damage = False
        _alive_before = {id(m) for m in self.monsters if m.alive}
        # ranged=True explicitly: slings pass ammo=None (infinite ammo), and
        # player_attack used to infer "ranged" from ammo alone, so a sling
        # shot was resolved with the MELEE weapon's stats.
        player_attack(self.player, monster, self.quiz_engine, on_complete,
                      ammo=ammo_item, ranged=True)

    def _refund_pending_spell(self) -> bool:
        """Give back what a targeted spell that was never cast had cost.

        _invoke_spell deducts MP before entering STATE_TARGET. ESC refunds it
        (game_input), as do an invalid target and quitting while aiming.
        Exactly what was paid comes back: a free cast (robe charge) paid no
        MP, so it gets the floor's free charge back instead of MP it never
        spent. Returns True if a pending spell was cancelled.
        """
        spell = getattr(self, '_pending_spell', None)
        if spell is None:
            return False
        paid = getattr(self, '_pending_spell_paid', None)
        if paid is None:
            try:
                paid = int(spell.get('mp_cost', 0))
            except (AttributeError, TypeError, ValueError):
                paid = 0
        if paid > 0:
            self.player.mp = min(self.player.max_mp, self.player.mp + paid)
        if getattr(self, '_pending_spell_free', False):
            from chain_passives import refund_passive_charge
            refund_passive_charge(self.player, 'free_cast_once_per_floor')
        self._pending_spell = None
        self._pending_spell_id = None
        self._pending_spell_paid = None
        self._pending_spell_free = False
        return True

    def _process_collateral_kills(self, primary, alive_before: set,
                                  chain: int = 0) -> None:
        """Run kill handling for monsters OTHER than the target that died
        during a player attack: chain-special AoE (glaive, axes, spear,
        halberd, ...) and unique splashes (Mjolnir, Zulfiqar, Gandiva).

        Those call take_damage() on bystanders deep inside combat.py and
        nothing reported the deaths, so they gave no message, loot, corpse,
        kill count, seal or boss story. ``alive_before`` is the set of
        id()s alive when the quiz started, which keeps long-dead monsters
        (they are never removed from self.monsters) out of the sweep.
        """
        for m in list(self.monsters):
            if (m is not primary and not m.alive and id(m) in alive_before
                    and not getattr(m, '_kill_handled', False)):
                self._on_monster_killed(m, chain_score=chain)

    def _fire_strike_finisher(self, monster, chain: int, damage: int,
                              killed: bool) -> None:
        """Kick off the end-of-attack flourish (effects/strike_finisher.py).
        Purely visual and non-blocking; never allowed to break combat."""
        rt = getattr(self, 'effects_runtime', None)
        if rt is None:
            return
        try:
            rank_name, rank_color = self._chain_rank(chain)
        except Exception:
            rank_name, rank_color = '', (230, 230, 230)
        rt.fire('strike_finisher', {
            'chain': chain,
            'damage': damage,
            'killed': killed,
            'rank_name': rank_name,
            'rank_color': rank_color,
            'target_name': getattr(monster, 'name', ''),
        })

    # ------------------------------------------------------------------
    # Melee combat
    # ------------------------------------------------------------------

    def _start_combat(self, monster):
        # Charmed: 40% chance to hesitate instead of attacking
        if self.player.has_effect('charmed') and random.random() < 0.40:
            self.add_message("You hesitate, unable to bring yourself to attack.", 'warning')
            self._advance_turn()
            return

        self.state = STATE_QUIZ
        self.combat_target = monster
        # Short fixed title: the combat strip already names the target and
        # the weapon, so repeating them here only overflowed the header.
        self.quiz_title = "MELEE ATTACK  --  MATH"
        self._combat_is_ranged = False
        self._combat_ammo = None
        if monster.kind == 'abaddon_destroyer' and not getattr(self, '_chronicle_abaddon_start', False):
            self._chronicle_abaddon_start = True
            self._chron('boss', "Abaddon. The Destroyer. He's real. He's here. This is it.")
        qs = getattr(self, 'quirk_system', None)
        if qs:
            qs.on_combat_started()
        self._combat_hp_pct_before = self.player.hp / max(1, self.player.max_hp)

        # Joyeuse (engine wave 3): combat_start_aoe_confuse_chance. Each
        # melee combat start, chance to dazzle adjacent enemies for 1 turn.
        # Lore: "Charlemagne's sword changed colour thirty times a day."
        _w_dazzle = self.player.weapon
        _dz_ch = float(getattr(_w_dazzle, 'combat_start_aoe_confuse_chance', 0.0) or 0.0) if _w_dazzle else 0.0
        if _dz_ch > 0 and random.random() < _dz_ch:
            _px, _py = self.player.x, self.player.y
            _dazzled = 0
            for _m in self.monsters:
                if (_m.alive and abs(_m.x - _px) <= 3 and abs(_m.y - _py) <= 3
                        and not (_m.x == _px and _m.y == _py)
                        and not _is_bystander(_m)):
                    _m.add_effect('confused', 1)
                    _dazzled += 1
            if _dazzled:
                self.add_message(
                    f"{_w_dazzle.name} flashes — nearby foes reel in confusion!",
                    'success')

        # Floating eye: paralyzing gaze on melee attack (the eye's signature
        # mechanic). Honor sleep_resist and blindness like monster.attack does.
        if monster.kind == 'floating_eye':
            if not self.player.has_effect('sleep_resist') and \
                    not self.player.has_effect('blinded'):
                cur = self.player.status_effects.get('paralyzed', 0)
                self.player.status_effects['paralyzed'] = max(cur, 3)
                self.add_message("The floating eye's gaze paralyzes you!", 'danger')
            else:
                self.add_message(
                    "Your gaze meets the floating eye's, but nothing happens.", 'info')

        def on_complete(damage: int, killed: bool, chain: int, stunned: bool = False,
                        knocked: bool = False, crit: bool = False, **kwargs):
            self.state = STATE_PLAYER
            self.combat_target = None
            self._fire_strike_finisher(monster, chain, damage, killed)
            self._announce_revive(monster)
            self._announce_scale_hit(monster, damage)
            # Curtana: the blow would have killed, but the Sword of Mercy
            # left the foe alive at 1 HP.
            if getattr(self.player, '_spared_this_attack', False):
                self.player._spared_this_attack = False
                self.add_message(
                    f"You spare {the_name(monster, lower=True)} — Curtana's mercy. (+1 max HP)",
                    'success')
            self._spend_attack_reroll()
            if chain == 0:
                self.add_message(
                    f"You swing wildly at {the_name(monster, lower=True)} and miss!", 'warning'
                )
            elif (chain >= 1 and monster.kind == 'fenrir_wolf' and monster.alive
                  and any(getattr(i, 'id', '') == 'vidars_sandal'
                          for i in self.player.inventory)):
                # Vidar's Sandal instant kill!
                monster.hp = 0
                monster.alive = False
                self._fire_strike_finisher(monster, chain, damage, True)
                _snd.play('monster_hit')
                self.add_message(
                    "You plant Vidar's shoe on the wolf's lower jaw and take "
                    "the upper in your hands.", 'combat')
                self.add_message(
                    "It is not your strength that does it. The wolf comes "
                    "apart as it was foretold.", 'success')
                self._on_monster_killed(
                    monster,
                    chain_score=chain,
                    hp_pct_before=getattr(self, '_combat_hp_pct_before', 1.0),
                )
                self._advance_turn()
                return
            else:
                if damage > 0:
                    _snd.play('monster_hit')
                # Stormbringer: betrays_at_low_hp. At HP <= 15%, a successful
                # hit has 25% chance to ALSO drain the nearest adjacent ally
                # (pet) for half the damage dealt to the monster. Per audit
                # 2026-05-30 — the JSON flag was inert. Lore: Elric's blade
                # eats from whatever's nearest when its bearer is dying.
                if (chain > 0 and damage > 0 and self.player.weapon
                        and getattr(self.player.weapon, 'betrays_at_low_hp', False)
                        and self.player.hp <= self.player.max_hp * 0.15):
                    if random.random() < 0.25:
                        _px, _py = self.player.x, self.player.y
                        _vic = next(
                            (p for p in self.pets
                             if p.alive
                             and abs(p.x - _px) <= 1 and abs(p.y - _py) <= 1),
                            None
                        )
                        if _vic:
                            _dr = max(1, damage // 2)
                            _vic.take_damage(_dr)
                            self.add_message(
                                f"Stormbringer twists in your hand — it drinks from {_vic.name} ({_dr} dmg)!",
                                'danger')
                            if not _vic.alive:
                                self.add_message(
                                    f"{_vic.name} crumples — the runesword has fed.",
                                    'danger')
                # Chain combat v2 (v2.14.0): crit retired. Chain IS the crit —
                # the message just calls out the chain rung and the damage.
                msg = f"Chain x{chain}! You strike {the_name(monster, lower=True)} for {damage} damage!"
                if chain >= 5:
                    _snd.play('strike_big')
                if stunned:
                    msg += f" {the_name(monster)} is stunned!"
                if monster.status_effects.get('bleeding', 0) > 0:
                    msg += f" {the_name(monster)} is bleeding!"
                if knocked and not killed:
                    from combat import apply_knockback
                    _was = (monster.x, monster.y)
                    apply_knockback(self.player, monster, self.dungeon, self.monsters,
                                    occupied=self._occupants())
                    if (monster.x, monster.y) != _was:
                        msg += f" {the_name(monster)} is knocked back!"
                if kwargs.get('poisoned'):
                    msg += f" {the_name(monster)} is poisoned!"
                if kwargs.get('burned'):
                    msg += f" {the_name(monster)} is burning!"
                if kwargs.get('confused'):
                    msg += f" {the_name(monster)} is confused!"
                if kwargs.get('petrified'):
                    msg += f" {the_name(monster)} is turning to stone!"
                if kwargs.get('healed'):
                    msg += " You absorb life energy!"
                self.add_message(msg, 'success')
                if killed:
                    self._on_monster_killed(
                        monster,
                        chain_score=chain,
                        unarmed=(self.player.weapon is None),
                        hp_pct_before=getattr(self, '_combat_hp_pct_before', 1.0),
                    )
                    # Heavy-class cleave: hits all adjacent live monsters when
                    # a MAX-CHAIN kill lands (greatsword cleave_at_max /
                    # great_axe cleave_at_max_plus_bleed). Damage = half of the
                    # killing blow. The chain-max gate lives in combat.py.
                    cleave_dmg = kwargs.get('cleave_dmg', 0)
                    if cleave_dmg:
                        _w = self.player.weapon
                        _bleed = _w and getattr(_w, 'class_mechanic', '') == 'cleave_at_max_plus_bleed'
                        _cleaved = 0
                        for _m in self.monsters:
                            if _m.alive and _m is not monster \
                                    and abs(_m.x - monster.x) <= 1 \
                                    and abs(_m.y - monster.y) <= 1 \
                                    and not _is_bystander(_m):
                                _actual = _m.take_damage(cleave_dmg)
                                _cleaved += 1
                                if _bleed and _actual > 0:
                                    _m.add_effect('bleeding', 3)
                                if not _m.alive:
                                    self._on_monster_killed(_m, chain_score=chain)
                        if _cleaved:
                            self.add_message(
                                "Your swing carries through — adjacent foes are cleaved!", 'success')
                    # Sling free_stones ricochet: bounce hit to an adjacent monster
                    ricochet_dmg = kwargs.get('ricochet_dmg', 0)
                    if ricochet_dmg:
                        for _m in self.monsters:
                            if _m.alive and _m is not monster \
                                    and abs(_m.x - monster.x) <= 1 \
                                    and abs(_m.y - monster.y) <= 1 \
                                    and not _is_bystander(_m):
                                _m.take_damage(ricochet_dmg)
                                self.add_message(
                                    f"The stone ricochets into {the_name(_m, lower=True)}!", 'success')
                                if not _m.alive:
                                    self._on_monster_killed(_m, chain_score=chain)
                                break
                    # Amenonuhoko: slow adjacent monsters on kill
                    w = self.player.weapon
                    if w and getattr(w, 'aoe_slow_on_kill', False):
                        for m in self.monsters:
                            if m.alive and abs(m.x - monster.x) <= 1 and abs(m.y - monster.y) <= 1:
                                m.add_effect('slowed', 3)
                        self.add_message("A wave of primordial stillness ripples outward.", 'info')
            self._process_collateral_kills(monster, _alive_before, chain)
            self._advance_turn()

        # Tablet of Destinies: allow quiz reroll if not used this floor.
        # Chain-equip passive one_thousand_and_one also grants reroll.
        try:
            from chain_passives import is_charge_available
            _scheh_reroll = is_charge_available(self.player, 'one_thousand_and_one')
        except ImportError:
            _scheh_reroll = False
        self.quiz_engine._reroll_flag = (
            (self._has_tablet_of_destinies() and not getattr(self, '_quiz_reroll_used', False))
            or _scheh_reroll
        )
        # Engine wave 3: side-channel refs for combat-side weapon mechanics
        # that need access to game state (Kusanagi surrounded check,
        # Oathkeeper adjacent-pet check, Penitent kill-tally karma adjust).
        # Set fresh per attack so they reflect current game state.
        self.player._combat_monsters_ref = self.monsters
        self.player._combat_pets_ref = self.pets
        self.player._combat_game_ref = self
        # Track that this combat is starting — used by cannot_miss_before_hurt
        # (Fail-not) which needs to know if the player has been hurt yet.
        # Reset to False at the START of every melee combat.
        self.player._combat_player_taken_damage = False
        _alive_before = {id(m) for m in self.monsters if m.alive}
        player_attack(self.player, monster, self.quiz_engine, on_complete)

    # ------------------------------------------------------------------
    # Monster turns
    # ------------------------------------------------------------------

    def _do_monster_turns(self):
        # Time stop: monsters are frozen this turn. Death is not: he is not
        # in time. (The return used to come first, so a scroll of time stop
        # was 25 free turns of the chase.)
        _time_stopped = self.player.has_effect('time_stopped')
        if _time_stopped and not (self.death_pursues and self.death_monster is not None):
            return
        # C06: a blow can move the player to another floor mid-loop (the
        # Winged Sandals' psychopomp step). The old floor's monsters then
        # stop: they used to keep acting on the new map, from their old
        # coordinates, and could finish the hero the Sandals had just saved.
        _floor_at_start = self.dungeon_level

        # Death acts first -- not part of self.monsters to avoid save/load issues
        if self.death_pursues and self.death_monster is not None:
            dm = self.death_monster
            all_m = self.monsters + [dm]
            _pet_occ_d = self._occupants(hero=False)      # pets and escorts
            if not self._death_steps_onto_the_floor():
                did_attack = False         # still climbing the stair
            elif (dm.x, dm.y) == (self.player.x, self.player.y):
                # Standing on his tile was total immunity: "adjacent" did not
                # include the same square, so he neither struck nor moved.
                did_attack = True
            else:
                did_attack = dm.take_turn(self.player, self.dungeon, all_m,
                                          extra_occupied=_pet_occ_d)
            if did_attack:
                _hp_before_death = self.player.hp
                dmg, msg = dm.attack(self.player)
                if self.player.hp <= 0 and self._death_gives_back_a_breath(_hp_before_death):
                    msg = None
                if msg:
                    self.add_message(msg, 'danger')
                if self.player.is_dead():
                    self.defeat_reason = 'died'
                    self._on_game_over()
                    self.state = STATE_DEAD
                    self.add_message("You have died! Press ESC to quit.", 'danger')
                    return

        # (While time is stopped, ordinary monsters stand still: see the
        # loop below. Named foes do not.)
        if self.dungeon_level != _floor_at_start:
            return

        # --- Ariadne's Thread: neutralize wall-phasing monsters ---
        has_thread = any(getattr(i, 'id', '') == 'ariadnes_thread'
                         for i in self.player.inventory)
        if not has_thread:
            # The random-loot belt of the same name counts when worn.
            has_thread = getattr(getattr(self.player, 'belt_slot', None), 'id', '') == 'ariadnes_thread'
        for m in self.monsters:
            # Asterion only: the Thread used to slow and re-pattern the two
            # phasing vampires as well, permanently.
            if getattr(m, 'can_phase_walls', False) and m.kind == 'asterion_minotaur':
                if has_thread:
                    m.can_phase_walls = False
                    m.speed = min(m.speed, 6)  # slowed by the Thread's power
                    if m.ai_pattern == 'hit_and_run':
                        m.ai_pattern = 'aggressive'  # can't hide anymore

        for m in self.monsters:
            if self.dungeon_level != _floor_at_start:
                break
            if not m.alive:
                continue
            # Time stop holds ordinary monsters only. Bosses, mini-bosses and
            # seal demons keep acting: a time-stop scroll used to be up to
            # 25 free turns on Abaddon, about three times his whole HP.
            if _time_stopped and not m._is_named_foe():
                continue
            # Allied monsters (angels): handle separately
            if getattr(m, 'is_allied', False):
                m.take_turn(self.player, self.dungeon, self.monsters,
                            extra_occupied=self._occupants(hero=False))
                _ann = getattr(m, '_annihilate_target', None)
                if _ann and _ann.alive:
                    _ann.alive = False
                    _ann.hp = 0
                    m.alive = False
                    m.hp = 0
                    if (m.x, m.y) in self.visible or (_ann.x, _ann.y) in self.visible:
                        self.add_message(
                            "An angel meets a locust in a blaze of holy fire! Both are consumed!",
                            'success')
                continue
            # Track monsters the player has seen (for encyclopedia bestiary)
            if self._sees_monster(m):
                self.player.known_monster_ids.add(m.kind)
            # "Something unseen" in its messages while the hero cannot see it.
            if getattr(m, 'invisible', False):
                m._unseen = unseen.unseen(m, self.player)
            # The Locust cult's charm: the swarms take the wearer for one of
            # their own and leave them alone until struck.
            if self._locust_calmed(m):
                continue
            _pet_occ = self._occupants(hero=False)        # pets and escorts
            _was_in_pit = m.has_effect('stuck_in_pit')
            _pos_before = (m.x, m.y)
            did_attack = m.take_turn(self.player, self.dungeon, self.monsters,
                                     extra_occupied=_pet_occ)
            # Rewired traps (player chained AI to >=3 on a trap) trigger when a
            # monster steps onto them. Only fires if the monster moved AND the
            # new tile holds a trap flagged safe_for_player.
            if m.alive and (m.x, m.y) != _pos_before:
                _new_tile_trap = self.dungeon.traps.get((m.x, m.y))
                if _new_tile_trap and _new_tile_trap.get('safe_for_player'):
                    self._fire_trap_on_monster(m, _new_tile_trap, (m.x, m.y))
            # Confused friendly fire message
            _cf_hit = getattr(m, '_confused_hit', None)
            if _cf_hit:
                victim, dmg = _cf_hit
                m._confused_hit = None
                if (m.x, m.y) in self.visible or (victim.x, victim.y) in self.visible:
                    self.add_message(
                        f"{self._confused_name(m)} attacks {the_name(victim, lower=True)} for {dmg} damage!", 'combat')
                if not victim.alive:
                    self._on_monster_killed(victim)
            # Abaddon locust swarm spawning
            if getattr(m, '_wants_locust_spawn', False) and m.kind == 'abaddon_destroyer':
                m._wants_locust_spawn = False
                self._spawn_abaddon_locusts(m)
            # Summoner AI: spawn a configured minion when flagged
            if getattr(m, '_wants_summon', False):
                m._wants_summon = False
                self._spawn_summoner_minion(m)
            # Healer AI: announce heals that occurred this turn
            heal_target = getattr(m, '_heal_target', None)
            if heal_target is not None and (m.x, m.y) in self.visible:
                amt = getattr(m, '_heal_amount', 0)
                self.add_message(
                    f"{the_name(m)} chants and heals {the_name(heal_target, lower=True)} for {amt} HP!",
                    'info')
                m._heal_target = None
                m._heal_amount = 0
            # HP-threshold phase-change announcement (boss enrage)
            enrage_msg = getattr(m, '_enrage_message', '')
            if enrage_msg and (m.x, m.y) in self.visible:
                self.add_message(enrage_msg, 'danger')
                m._enrage_message = ''
            # Fenrir rage escalation message
            rage_msg = getattr(m, '_rage_message', '')
            m._rage_message = ''        # said once, not every turn he is held
            if rage_msg and (m.x, m.y) in self.visible:
                self.add_message(rage_msg, 'danger')
            # Check if monster moved onto a dug pit
            if (not _was_in_pit and not m.has_effect('stuck_in_pit')
                    and not m.has_effect('levitating')
                    # A creature bigger than the hole steps over it (a dragon
                    # stuck in a man-sized pit was possible before).
                    and tuple(getattr(m, 'footprint', (1, 1))) == (1, 1)
                    and (m.x, m.y) != _pos_before
                    and (m.x, m.y) in getattr(self.dungeon, 'pits', set())):
                from dice import roll as _pit_roll
                _pit_roll('1d4')          # (keeps the random stream as it was)
                pit_dmg = floor_curve.wound(PIT_FALL_SHARE, m.max_hp, m._is_named_foe())
                m.hp -= pit_dmg
                m._unhurt_turns = 0
                if m.hp <= 0:
                    m.alive = False
                m.status_effects['stuck_in_pit'] = random.randint(3, 4)
                if (m.x, m.y) in self.visible:
                    self.add_message(f"{the_name(m)} falls into a pit!", 'info')
                if not m.alive:
                    self._on_monster_killed(m)
                continue  # can't attack this turn — just fell
            if did_attack:
                # Displacement: DISPLACEMENT_MISS chance that the blow lands where you are not
                if self.player.has_effect('displacement') and random.random() < DISPLACEMENT_MISS:
                    self.add_message(f"{the_name(m)}'s attack passes through your displaced image!", 'info')
                    continue

                _effects_before = set(self.player.status_effects.keys())
                if getattr(m, 'slips_on_ice', False):
                    from dungeon import ICE as _ICE
                    m._on_ice = self.dungeon.tiles[m.y][m.x] == _ICE
                m._last_attack_type = None      # set by the monster only when a blow lands
                _hp_before_blow = self.player.hp
                # The blow is reported to the traits below, once, after the
                # wards (Player.take_damage reports every other hurt).
                self.player._trait_hooks_held = True
                try:
                    dmg, msg = m.attack(self.player)
                finally:
                    self.player._trait_hooks_held = False
                if (getattr(m, '_unseen', False) is True
                        and max(abs(m.x - self.player.x), abs(m.y - self.player.y)) > 1):
                    # Unseen and not beside you: the only clue is where it came from.
                    msg += (" It came from the "
                            f"{self._compass_word(m.x - self.player.x, m.y - self.player.y)}.")
                self.add_message(msg, 'danger')
                if self.player.hp <= 0:
                    self._green_girdle_spares(m)
                # A thief's blow landed: it takes the gold or the item now
                # (src/theft.py), and runs with it.
                _steal = getattr(m, '_wants_steal', None)
                if _steal:
                    m._wants_steal = None
                    _tmsg = theft.steal(self, m, _steal)
                    if _tmsg:
                        self.add_message(_tmsg, 'danger')
                # Perseus's trait counts every gaze or effect thrown back at its
                # sender. Only the reflection aura's second chance (below) was
                # counted: the Aegis turning Medusa's gaze, the thing the trait
                # is named for, never was.
                if getattr(self.player, '_reflected_back', False):
                    self.player._reflected_back = False
                    _qs_pers = getattr(self, 'quirk_system', None)
                    if _qs_pers:
                        _qs_pers.on_status_reflected()
                _fury = m.fury_line() if m.alive else ''
                if _fury:
                    self.add_message(_fury, 'warning')
                # Reflect / thorns damage can kill the attacker inside
                # attack(); that death used to go unprocessed.
                if not m.alive and not getattr(m, '_kill_handled', False):
                    self._on_monster_killed(m)

                # Anansi web cloak (story_thread): the first crit per floor that
                # would deal >25% of max-HP is reduced to 1 damage. Threshold is
                # a stand-in for "crit" since monsters don't tag their hits as crits.
                try:
                    from armor_procs import consume_floor_charge
                    if dmg > 0 and self.player.max_hp > 0 and \
                            dmg / max(1, self.player.max_hp) >= 0.25:
                        if consume_floor_charge(self.player, 'story_thread'):
                            # Reverse the damage spike by healing back to pre-hit HP - 1.
                            self.player.hp = max(self.player.hp,
                                                 min(self.player.max_hp, max(1, _hp_before_blow - 1)))
                            self.add_message(
                                "The thread of a thousand stories catches the blow — only a scratch!",
                                'success')
                            dmg = 1
                except ImportError:
                    pass

                # Arachne silk cloak (webbed_strike): on melee hit, attacker is
                # slowed for 3 turns.
                if dmg > 0:
                    try:
                        from armor_procs import player_has_armor_proc
                        if player_has_armor_proc(self.player, 'webbed_strike'):
                            atks = getattr(m, 'attacks', []) or []
                            _is_melee = atks and not any(
                                w in (atks[0].get('name', '') or '').lower()
                                for w in ('shoot', 'arrow', 'bolt', 'dart', 'spit',
                                         'hurl', 'volley', 'ray', 'blast', 'breath',
                                         'spike', 'gaze', 'song', 'wail'))
                            if _is_melee and hasattr(m, 'add_effect'):
                                m.add_effect('slowed', 3)
                                self.add_message(
                                    f"Arachne's silk drags {the_name(m, lower=True)} — slowed!", 'info')
                    except ImportError:
                        pass

                # Sandals of Theseus (their_own_methods): on melee hit, % chance
                # to mirror one of the player's currently active statuses back
                # at the attacker. Probability stored on the field.
                if dmg > 0:
                    try:
                        from armor_procs import proc_value
                        chance = float(proc_value(self.player, 'their_own_methods') or 0.0)
                        if chance > 0 and random.random() < chance:
                            from status_effects import DEBUFFS as _DEBUFFS
                            # Not the crossbow cooldown or the pit the
                            # player stands in: neither is a tactic.
                            _candidates = [eff for eff in self.player.status_effects.keys()
                                          if eff in _DEBUFFS
                                          and eff not in ('reloading', 'in_pit')]
                            if _candidates and hasattr(m, 'add_effect'):
                                _eff = random.choice(_candidates)
                                m.add_effect(_eff, 5)
                                self.add_message(
                                    f"Theseus's sandals turn {the_name(m, lower=True)}'s tactic against it — {_eff.replace('_', ' ')}!",
                                    'info')
                    except ImportError:
                        pass

                # Carapace of the Hydra (caustic_blood): when the wearer takes
                # poison damage, the attacker also gets poisoned. Reflects the
                # "immune to its own venom" lore. Keyed on the bite landing, not on
                # damage getting through: the carapace's own poison resistance
                # turns a small bite to 0, and then nothing was answered.
                if getattr(m, '_last_attack_type', None) == 'poison':
                    try:
                        from armor_procs import proc_value
                        _refl_chance = float(proc_value(self.player, 'caustic_blood') or 0.0)
                        if _refl_chance > 0 and getattr(m, '_last_attack_type', None) == 'poison':
                            if random.random() < _refl_chance and hasattr(m, 'add_effect'):
                                m.add_effect('poisoned', 4)
                                self.add_message(
                                    f"The Hydra carapace bleeds caustic ichor — {the_name(m, lower=True)} is poisoned!",
                                    'combat')
                    except ImportError:
                        pass

                # Lorica Hamata of Caesar (et_tu_charge): the first attacker each
                # combat is marked; player will deal +50% damage to that monster
                # (consumed in combat.player_attack via _et_tu_target).
                if dmg > 0:
                    try:
                        from armor_procs import player_has_armor_proc
                        # The mark is the monster itself, and moves on when it dies.
                        _marked = getattr(self.player, '_et_tu_target', None)
                        if player_has_armor_proc(self.player, 'et_tu_charge') and \
                                (_marked is None or not getattr(_marked, 'alive', True)):
                            self.player._et_tu_target = m
                            self.add_message(
                                f"\"Et tu, {m.name if not getattr(m, '_unseen', False) else 'unseen thing'}?\" — Caesar's lorica marks the first betrayer.",
                                'info')
                    except ImportError:
                        pass

                # Piercing collateral: damage monsters in the projectile path
                _collateral = getattr(m, '_piercing_collateral', [])
                if _collateral and dmg > 0:
                    _coll_frac = random.uniform(0.75, 0.90)
                    _coll_dmg = max(1, int(dmg * _coll_frac))
                    for _cv in _collateral:
                        if not _cv.alive:
                            continue
                        _cv.hp -= _coll_dmg
                        _cv._unhurt_turns = 0
                        if (m.x, m.y) in self.visible or (_cv.x, _cv.y) in self.visible:
                            self.add_message(
                                f"{the_name(m)}'s attack tears through {the_name(_cv, lower=True)} for {_coll_dmg} collateral damage!",
                                'combat')
                        if _cv.hp <= 0:
                            _cv.alive = False
                            self._on_monster_killed(_cv)
                    m._piercing_collateral = []

                # SP drain (locusts, famine demon)
                _sp_drain = getattr(m, 'sp_drain', 0)
                if _sp_drain > 0 and dmg > 0:
                    self.player.sp = max(0, self.player.sp - _sp_drain)
                    self.add_message(
                        f"{the_name(m)}'s attack drains your stamina! (-{_sp_drain} SP)", 'danger')

                # Fire shield: reflect melee damage back
                if self.player.has_effect('fire_shield') and dmg > 0:
                    reflect_dmg = floor_curve.wound(SHIELD_LASH_SHARE, m.max_hp, m._is_named_foe())
                    m.hp -= reflect_dmg
                    m._unhurt_turns = 0
                    self.add_message(f"Flames lash back at {the_name(m, lower=True)} for {reflect_dmg}!", 'danger')
                    if m.hp <= 0:
                        m.alive = False
                        self._on_monster_killed(m)
                # Cold shield: reflect melee damage back
                if self.player.has_effect('cold_shield') and dmg > 0:
                    reflect_dmg = floor_curve.wound(SHIELD_LASH_SHARE, m.max_hp, m._is_named_foe())
                    m.hp -= reflect_dmg
                    m._unhurt_turns = 0
                    self.add_message(f"Ice shatters back at {the_name(m, lower=True)} for {reflect_dmg}!", 'danger')
                    if m.hp <= 0 and m.alive:
                        m.alive = False
                        self._on_monster_killed(m)

                # Shortsword riposte: free counter at 0.85× weapon base damage
                # (set by combat.player_attack class_mech 'quick_riposte' at max chain)
                if self.player.has_effect('riposte_armed') and dmg > 0 and m.alive:
                    _w = self.player.weapon
                    if _w and getattr(_w, 'class_mechanic', '') == 'quick_riposte':
                        _rip = max(1, int((_w.base_damage or 4) * 0.85))
                        _rip_actual = m.take_damage(_rip)
                        self.add_message(
                            f"You riposte {the_name(m, lower=True)} for {_rip_actual}!", 'success')
                        # Consume one charge
                        self.player.status_effects['riposte_armed'] = max(
                            0, self.player.status_effects.get('riposte_armed', 0) - 1)
                        if not m.alive:
                            self._on_monster_killed(m)

                # Tarnhelm: auto-invisibility when HP drops below 30%
                if dmg > 0 and not getattr(self, '_tarnhelm_used', False):
                    if self.player.hp > 0 and self.player.hp / max(1, self.player.max_hp) < 0.30:
                        for _arm_slot in self.player.armor_slots:
                            if _arm_slot and getattr(_arm_slot, 'invisibility_power', False):
                                self.player.add_effect('invisible', _arm_slot.invisibility_duration)
                                self._tarnhelm_used = True
                                self.add_message("The Tarnhelm shimmers — you vanish from sight!", 'success')
                                break

                # Green Chapel Axe: heal when hit
                _wpn = self.player.weapon
                if _wpn and getattr(_wpn, 'on_hit_regen', 0) > 0 and dmg > 0:
                    _regen_amt = _wpn.on_hit_regen
                    self.player.hp = min(self.player.max_hp, self.player.hp + _regen_amt)
                    self.add_message(f"The green axe mends your wounds. (+{_regen_amt} HP)", 'info')

                # Svalinn: reflect fire damage back at attacker
                _shld = self.player.shield
                # A share of the attacker's own roll, not of what got through:
                # Svalinn lets no fire through at all, so it reflected nothing.
                # (And it read a field no monster has, so it never fired.)
                if _shld and getattr(_shld, 'fire_reflect', 0) > 0 \
                        and getattr(m, '_last_attack_type', None) == 'fire' and m.alive:
                    _roll = int(getattr(m, '_last_attack_roll', 0) or 0)
                    if _roll > 0:
                        _fire_ref = max(1, int(_roll * _shld.fire_reflect))
                        m.hp -= _fire_ref
                        m._unhurt_turns = 0
                        self.add_message(f"The {_shld.name} throws flame back at {the_name(m, lower=True)} for {_fire_ref}!", 'combat')
                        if m.hp <= 0 and m.alive:
                            m.alive = False
                            self._on_monster_killed(m)

                # Babr-e Bayan: absorb first hit per floor.
                # Also handles chain-equip passive `first_hit_absorb` (Armor of Ragnarok).
                if dmg > 0 and not getattr(self, '_first_hit_used', False):
                    _absorbed = False
                    for _arm_slot in self.player.armor_slots:
                        if _arm_slot and getattr(_arm_slot, 'first_hit_absorb', False):
                            # back to what it was, not "plus the blow": health
                            # stops at 0, so undoing a 50-point blow on a
                            # 5-health wearer healed them to 50
                            self.player.hp = max(self.player.hp, min(self.player.max_hp, _hp_before_blow))
                            self._first_hit_used = True
                            self.add_message("The tiger-skin absorbs the blow completely!", 'success')
                            _absorbed = True
                            break
                    if not _absorbed:
                        try:
                            from chain_passives import player_has_passive
                            if player_has_passive(self.player, 'first_hit_absorb'):
                                # C02: back to what it was, as the tiger-skin
                                # above; "+ dmg" healed a lethal blow to full.
                                self.player.hp = max(self.player.hp, min(self.player.max_hp, _hp_before_blow))
                                self._first_hit_used = True
                                self.add_message(
                                    "Your armor turns aside the first blow!", 'success')
                        except ImportError:
                            pass

                # Every ward against death (see _answer_a_killing_blow).
                self._answer_a_killing_blow()

                # Reflecting: negate 50% of newly applied status effects
                _new_effects = set(self.player.status_effects.keys()) - _effects_before
                if self.player.has_effect('reflecting') and _new_effects:
                    from status_effects import DEBUFFS as _REFL_DEBUFFS
                    for _new_eff in list(_new_effects):
                        # C08: only the blow's debuffs. The diff also holds
                        # what the player's own gear switched on (life_save,
                        # berserk, the Elder Blood escape signal).
                        if _new_eff not in _REFL_DEBUFFS:
                            continue
                        if random.random() < 0.50:
                            del self.player.status_effects[_new_eff]
                            self.add_message(f"Your reflection aura deflects the {_new_eff.replace('_', ' ')}!", 'info')
                            _new_effects.discard(_new_eff)
                            _qs_refl = getattr(self, 'quirk_system', None)
                            if _qs_refl:
                                _qs_refl.on_status_reflected()

                # Spell Turning: reflect 100% of newly applied debuffs back at attacker
                if self.player.has_effect('spell_turning') and _new_effects:
                    from status_effects import DEBUFFS as _DEBUFFS
                    for _new_eff in list(_new_effects):
                        if _new_eff in _DEBUFFS:
                            del self.player.status_effects[_new_eff]
                            m.add_effect(_new_eff, 8)
                            self.add_message(
                                f"Your spell turning reflects the {_new_eff.replace('_', ' ')} "
                                f"back at {the_name(m, lower=True)}!", 'info'
                            )

                if dmg > 0:
                    _snd.play('player_hit')
                _qs_dmg = getattr(self, 'quirk_system', None)
                if _qs_dmg and self.player:
                    if dmg > 0:
                        _qs_dmg.on_take_damage(dmg, dmg / max(1, self.player.max_hp))
                    # Notify quirk system of newly applied status effects (after reflection)
                    for _new_eff in set(self.player.status_effects.keys()) - _effects_before:
                        _qs_dmg.on_status_applied(_new_eff, m.kind)
                if self.player.is_dead():
                    self.defeat_reason = 'died'
                    self._on_game_over()
                    self.state = STATE_DEAD
                    self.add_message("You have died! Press ESC to quit.", 'danger')
                    return

    # ------------------------------------------------------------------
    # Pet turns
    # ------------------------------------------------------------------

    def _begin_pet_special_targeting(self, pet, special: dict):
        """Open targeting for a player-triggered pet special.

        The cursor starts on the pet's current tile. Confirm with ENTER/SPACE/F/S.
        Targeting envelope is enforced at resolution time, not movement time
        (cursor can roam, but invalid confirms produce a warning).

        Specials with `targeting: 'self'`, `'visible_all'` or
        `'hero_adjacent'` (Shep's Sic 'Em All!) have no tile to pick:
        they resolve instantly here, no cursor.
        """
        from game_states import STATE_TARGET, STATE_PLAYER
        if special.get('targeting') in ('self', 'visible_all', 'hero_adjacent'):
            # No-target specials: resolve immediately at pet's tile and
            # spend the turn.
            self._resolve_pet_special(pet, special, pet.x, pet.y)
            pet.use_special(special['id'])
            self.state = STATE_PLAYER
            self._advance_turn()
            return
        self._pending_pet_special = special
        self._pending_pet_special_pet = pet
        self._pet_special_targeting = True
        # Clear other targeting flags
        self._throw_targeting = False
        self._observe_targeting = False
        self._wand_targeting = False
        self._melee_targeting = False
        self._power_targeting = False
        # Start cursor on the pet, then snap to nearest visible enemy within
        # the special's range to make the common case one-keystroke.
        self.target_cursor_x = pet.x
        self.target_cursor_y = pet.y
        self._target_candidates = []
        self._target_idx = 0
        rng = int(special.get('range', 5))
        for m in self.monsters:
            if not self._sees_monster(m):
                continue
            if max(abs(m.x - pet.x), abs(m.y - pet.y)) <= rng:
                self._target_candidates.append(m)
        if self._target_candidates:
            # Sort by distance from pet
            self._target_candidates.sort(
                key=lambda m: max(abs(m.x - pet.x), abs(m.y - pet.y)))
            self.target_cursor_x = self._target_candidates[0].x
            self.target_cursor_y = self._target_candidates[0].y
        self.state = STATE_TARGET
        _ = STATE_PLAYER  # silence unused-import linter; STATE_TARGET is the active one

    def _confirm_pet_special_target(self):
        """Resolve a pet special at the cursor position. Validates range."""
        from game_states import STATE_PLAYER
        pet = self._pending_pet_special_pet
        special = self._pending_pet_special
        # Clear targeting state regardless of outcome
        self._pet_special_targeting = False
        self._pending_pet_special = None
        self._pending_pet_special_pet = None
        if pet is None or special is None or not pet.alive:
            self.state = STATE_PLAYER
            return
        tx, ty = self.target_cursor_x, self.target_cursor_y
        rng = int(special.get('range', 5))
        # Targeting is centered on the PET, not the player.
        if max(abs(tx - pet.x), abs(ty - pet.y)) > rng:
            self.add_message(
                f"{pet.name} cannot reach that distance with {special['name']}.",
                'warning')
            self.state = STATE_PLAYER
            return
        # A leap (Sic 'Em!, Pounce, Seraph Dive) goes where the hero points:
        # a tile he can see, with no rock between the pet and it (PET-10).
        if special.get('leap'):
            from combat import _line_of_sight
            if ((tx, ty) not in self.visible
                    or not _line_of_sight(pet.x, pet.y, tx, ty, self.dungeon)):
                self.add_message(f"{pet.name} has no clear way to that spot.", 'warning')
                self.state = STATE_PLAYER
                return
        self._resolve_pet_special(pet, special, tx, ty)
        pet.use_special(special['id'])
        self.state = STATE_PLAYER
        self._advance_turn()

    def _resolve_pet_special(self, pet, special: dict, tx: int, ty: int):
        """Apply a pet special's effects (damage + status) per targeting mode."""
        import random as _rng
        targeting = special.get('targeting', 'single')
        base_dmg = pet.base_damage          # real numbers: data/pet_growth.json
        dmg_mult = float(special.get('damage_mult', 1.5))
        status = special.get('status')
        status_chance = float(special.get('status_chance', 0.0))
        status_duration = int(special.get('status_duration', 3))

        # ── No-target specials (Duck of Doom: Detect Monsters) ──
        if targeting == 'self':
            effect = special.get('effect')
            dur = int(special.get('effect_duration', 0))
            if effect == 'player_telepathy' and dur > 0:
                self.player.add_effect('telepathy', dur)
                self.add_message(
                    f"{pet.name}'s mind opens — every creature on the "
                    f"floor floods into your awareness ({dur} turns).",
                    'success')
            return

        # ── Sometimes Goose: hit every alive monster in FOV ──
        if targeting == 'visible_all':
            flavor = special.get('flavor_message')
            if flavor:
                self.add_message(flavor, 'success')
            else:
                self.add_message(
                    f"{pet.name} unleashes {special['name']}!", 'success')
            hit_count = 0
            for m in self.monsters:
                if not m.alive:
                    continue
                if (m.x, m.y) not in self.visible:
                    continue
                dmg = max(1, int(base_dmg * dmg_mult))
                pre_max = m.max_hp
                m.take_damage(dmg, pet_damage_type(special.get('damage_type')
                                                   or pet.species.get('damage_type')))
                if m.alive and status and _rng.random() < status_chance:
                    cur = m.status_effects.get(status, 0)
                    m.status_effects[status] = max(cur, status_duration)
                if not m.alive:
                    for k_msg in pet.gain_xp_from_kill(pre_max, _monster_level(m)):
                        self.add_message(k_msg, 'success')
                    self._on_monster_killed(m)
                hit_count += 1
            if hit_count == 0:
                self.add_message(
                    f"The {special['name']} dissipates harmlessly.", 'info')
            return

        dtype = special.get('damage_type') or pet.species.get('damage_type')
        knock = int(special.get('knockback', 0) or 0)

        def _apply_to(m):
            self._pet_hit(pet, m, dmg_mult, status, status_chance, status_duration,
                          damage_type=dtype, knockback=knock)

        def _say(key):
            text = special.get(key)
            if text:
                self.add_message(text.replace('{pet}', pet.name)
                                 .replace('{call}', getattr(pet, 'call_name', pet.name)),
                                 'success')
            return bool(text)

        # ── Shep's Sic 'Em All!: to the hero's side, then every foe there ──
        if targeting == 'hero_adjacent':
            foes = self._foes_beside_hero()
            if not foes:
                self._dash_pet_to_hero(pet)
                if not _say('miss_message'):
                    self.add_message(f"The {special['name']} finds nothing to hit.", 'info')
                return
            if not _say('flavor_message'):
                self.add_message(f"{pet.name} unleashes {special['name']}!", 'success')
            self._dash_pet_to_hero(pet, foes[0])
            for m in foes:
                _apply_to(m)
            return

        # Draw foes in first (Sherlock's Midnight Aria: everything within
        # earshot comes over to make it stop), so the blast then catches them.
        pull = int(special.get('pull_radius', 0) or 0)
        if pull:
            self._pull_foes_to_pet(pet, pull)

        affected = []
        if targeting == 'single':
            for m in self.monsters:
                # a leap goes for what the hero pointed at: a creature he
                # cannot see is not his target (PET-10; the miss line then
                # tells him nothing about the tile)
                if (special.get('leap') and hasattr(self, '_sees_monster')
                        and not self._sees_monster(m)):
                    continue
                if m.alive and is_at_tile(m, tx, ty):
                    affected.append(m)
                    break
        elif targeting == 'aoe':
            radius = int(special.get('aoe_radius', 1))
            for m in self.monsters:
                if m.alive and max(abs(m.x - tx), abs(m.y - ty)) <= radius:
                    affected.append(m)
        elif targeting == 'cone':
            # Cone from pet toward (tx, ty), max range = special's range.
            from combat import get_cone_tiles
            cone = get_cone_tiles(pet.x, pet.y, tx, ty,
                                  max_range=int(special.get('range', 3)))
            for m in self.monsters:
                if m.alive and (m.x, m.y) in cone:
                    affected.append(m)
        elif targeting == 'line':
            from combat import get_line_tiles
            line = get_line_tiles(pet.x, pet.y, tx, ty)
            # (get_line_tiles already leaves the pet's own tile out; dropping
            # one more meant the wave never touched the creature beside it)
            for (lx, ly) in line:
                for m in self.monsters:
                    if m.alive and is_at_tile(m, lx, ly) and m not in affected:
                        affected.append(m)

        # (a special with its own miss line says only that when it hits nothing)
        if affected or not special.get('miss_message'):
            if not _say('flavor_message'):
                self.add_message(
                    f"{pet.name} unleashes {special['name']}!", 'success')
        # A leaping special (Irene's Pounce and Seraph Dive) carries the pet
        # to the target: she lands on the free tile beside it nearest to her.
        if special.get('leap'):
            self._leap_pet_to(pet, tx, ty)
        if special.get('knockback'):
            # the farthest first, so the ones in front have room to go back
            affected.sort(key=lambda m: -max(abs(m.x - pet.x), abs(m.y - pet.y)))
        for m in affected:
            _apply_to(m)
        if not affected and not _say('miss_message'):
            self.add_message(
                f"The {special['name']} dissipates harmlessly.", 'info')
        heal_share = float(special.get('self_heal', 0) or 0)
        if heal_share > 0 and pet.alive and pet.hp < pet.max_hp:
            healed = min(pet.max_hp - pet.hp, max(1, int(pet.max_hp * heal_share)))
            pet.hp += healed
            self.add_message(f"{pet.name} naps it off. (+{healed} HP)", 'success')

    def _pet_tile_free(self, x: int, y: int, pet=None) -> bool:
        return (self.dungeon.is_walkable(x, y)
                and (x, y) != (self.player.x, self.player.y)
                and monster_at_tile(self.monsters, x, y) is None
                and not any(p.alive and p is not pet and p.x == x and p.y == y
                            for p in list(self.pets) + self._escorts_here()))

    def _leap_pet_to(self, pet, tx: int, ty: int):
        """Move the pet onto the free tile beside (tx, ty) nearest to it (or
        onto (tx, ty) itself when that is free). Stays put if none is free."""
        best = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = tx + dx, ty + dy
                if (nx, ny) == (pet.x, pet.y) or self._pet_tile_free(nx, ny, pet):
                    d = max(abs(nx - pet.x), abs(ny - pet.y))
                    if best is None or d < best[0]:
                        best = (d, nx, ny)
        if best:
            pet.x, pet.y = best[1], best[2]

    def _pull_foes_to_pet(self, pet, radius: int):
        """Every visible one-tile foe within `radius` of the pet is drawn to a
        free tile beside it. Bosses and multi-tile monsters hold their ground."""
        spots = [(pet.x + dx, pet.y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                 if (dx or dy)]
        foes = [m for m in self.monsters
                if m.alive and not getattr(m, 'is_allied', False)
                and not getattr(m, 'is_boss', False)
                and tuple(getattr(m, 'footprint', (1, 1))) == (1, 1)
                and (m.x, m.y) in self.visible
                and 1 < max(abs(m.x - pet.x), abs(m.y - pet.y)) <= radius]
        foes.sort(key=lambda m: max(abs(m.x - pet.x), abs(m.y - pet.y)))
        for m in foes:
            free = [s for s in spots if self._pet_tile_free(*s, pet)]
            if not free:
                break
            m.x, m.y = min(free, key=lambda s: max(abs(s[0] - m.x), abs(s[1] - m.y)))
            self._spring_lurker(m)       # dragged out of its disguise (PET-04)

    def _pet_hit(self, pet, m, mult: float, status=None, chance: float = 0.0,
                 duration: int = 0, *, damage_type=None, knockback: int = 0) -> int:
        """One special-strength blow from a pet: its bite times `mult` of its
        `damage_type` (the special's: fire, cold, holy... meet resistances
        and weaknesses, a bite can split what a bite splits), a push of
        `knockback` tiles away from the pet, then the status at `chance`,
        kill experience and the kill itself. Returns the damage dealt."""
        import random as _rng
        if not m.alive:
            return 0
        pre_max = m.max_hp
        dealt = m.take_damage(max(1, int(pet.base_damage * mult)),
                              pet_damage_type(damage_type or pet.species.get('damage_type')))
        if m.alive and dealt and knockback:
            self._pet_knockback(pet, m, knockback)
        if m.alive and status and _rng.random() < chance:
            cur = m.status_effects.get(status, 0)
            m.status_effects[status] = max(cur, duration)
        if not m.alive:
            for k_msg in pet.gain_xp_from_kill(pre_max, _monster_level(m)):
                self.add_message(k_msg, 'success')
            self._on_monster_killed(m)
        return dealt or 0

    def _pet_knockback(self, pet, m, tiles: int = 1) -> None:
        """Push `m` straight away from the pet, a tile at a time, while the
        next tile is open floor with nobody on it. Bosses, big creatures and
        things that do not move (the sessile, mimics, the Black Knight on
        his bridge) hold their ground."""
        if (getattr(m, 'is_boss', False) or getattr(m, 'stationary', False)
                or getattr(m, 'ai_pattern', '') in ('sessile', 'mimic')
                or tuple(getattr(m, 'footprint', (1, 1)) or (1, 1)) != (1, 1)):
            return
        sx = (m.x > pet.x) - (m.x < pet.x)
        sy = (m.y > pet.y) - (m.y < pet.y)
        if not (sx or sy):
            return
        for _ in range(max(0, int(tiles))):
            nx, ny = m.x + sx, m.y + sy
            if not self._pet_tile_free(nx, ny, pet) or (nx, ny) == (pet.x, pet.y):
                return
            m.x, m.y = nx, ny

    def _foes_beside_hero(self, *, threats_only: bool = False) -> list:
        """Every living foe touching the hero, the toughest first. Friends,
        the unicorn and the people of the encounters are not foes. With
        `threats_only`, a foe that cannot swing at him this turn (asleep,
        held, frozen, feared, charmed: the ones that do not swipe at pets
        either) is not counted (PET-07: Shep's rescue is for a fight)."""
        from geom import chebyshev_distance
        px, py = self.player.x, self.player.y
        foes = [m for m in self.monsters
                if m.alive and not getattr(m, 'is_allied', False)
                and not getattr(m, '_npc_encounter_tag', None)
                and not getattr(m, '_flavor_encounter_tag', None)
                and not getattr(m, '_is_unicorn', False)
                and chebyshev_distance(px, py, m) <= 1
                and not (threats_only and any(m.has_effect(e) for e in _HELD_FOE_EFFECTS))]
        foes.sort(key=lambda m: -m.hp)
        return foes

    def _dash_pet_to_hero(self, pet, foe=None) -> None:
        """Carry the pet to the hero's side from wherever it is on the floor,
        onto the free tile beside the hero that also touches `foe` when there
        is one. A pet already there stays put; with no free tile beside the
        hero it leaps in beside the foe instead."""
        from geom import chebyshev_distance
        px, py = self.player.x, self.player.y

        def touches_foe(x, y):
            return foe is None or chebyshev_distance(x, y, foe) <= 1

        if max(abs(pet.x - px), abs(pet.y - py)) <= 1 and touches_foe(pet.x, pet.y):
            return
        spots = [(px + dx, py + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                 if (dx or dy) and self._pet_tile_free(px + dx, py + dy, pet)]
        if spots:
            pet.x, pet.y = min(spots, key=lambda s: (
                not touches_foe(*s), max(abs(s[0] - pet.x), abs(s[1] - pet.y))))
        elif foe is not None:
            self._leap_pet_to(pet, foe.x, foe.y)

    def _shep_rescue(self):
        """He Always Comes: when the hero has fallen to a quarter of his
        health with a foe beside him, Shep streaks in from anywhere on the
        floor and takes the toughest one down (Shep the Legend: all of them,
        then stands guard). Once a floor, reached for the first time.
        Returns the pet that came, which has spent its turn, or None."""
        p = self.player
        if p.is_dead() or p.max_hp <= 0:
            return None
        deepest = int(getattr(p, 'deepest_floor_reached', 1) or 1)
        for pet in self.pets:
            rescue = pet.species.get('rescue') if pet.alive else None
            if not rescue or not pet.rescue_ready(deepest):
                continue
            if p.hp > p.max_hp * float(rescue.get('hp_share', 0.25)):
                return None
            foes = self._foes_beside_hero(threats_only=True)
            if not foes:
                return None
            far = ((pet.x, pet.y) not in self.visible
                   or max(abs(pet.x - p.x), abs(pet.y - p.y)) > 3)
            msg = rescue['far_message'] if far else rescue['near_message']
            self.add_message(msg.replace('{pet}', pet.name), 'success')
            self._dash_pet_to_hero(pet, foes[0])
            pet.spend_rescue(deepest)
            every = pet.stage >= int(rescue.get('all_foes_stage', 99))
            if every and len(foes) > 1:
                self.add_message(rescue['all_message'].replace('{pet}', pet.name), 'success')
            for m in (foes if every else foes[:1]):
                dmg = self._pet_hit(pet, m, float(rescue.get('damage_mult', 1.5)),
                                    rescue.get('status'), float(rescue.get('status_chance', 0)),
                                    int(rescue.get('status_duration', 0)))
                self.add_message(rescue['hit_message'].replace('{pet}', pet.name)
                                 .replace('{foe}', the_name(m, lower=True)).replace('{dmg}', str(dmg)), 'combat')
            turns = int(rescue.get('shield_turns', 0) or 0)
            if every and turns > 0:
                p.add_effect('shielded', turns)
                self.add_message(rescue['guard_message'].replace('{pet}', pet.name)
                                 .replace('{turns}', str(turns)), 'success')
            _snd.play('player_healed')
            self._chron(
                'loss',
                f"I was down and they were all around me, and then {pet.name} was there. "
                "He always comes.", once='rescue')
            return pet
        return None

    def _do_pet_turns(self):
        """Process pet AI, XP, regen, cooldowns, and monster attacks on pets."""
        if not self.pets:
            return

        # Compute quiz accuracy for pet damage scaling
        total_q = self.correct_answers + self.wrong_answers
        quiz_acc = self.correct_answers / max(1, total_q)

        # Shep's rescue comes first: the monsters have just had their turn,
        # so a hero they have knocked to a quarter of his health is saved
        # before they swing again. The rescue is that pet's turn.
        rescuer = self._shep_rescue()

        for pet in self.pets:
            if not pet.alive:
                continue

            # Pet AI turn
            # (escorts are bodies too: a pet never steps onto one, PET-05)
            result = (None if pet is rescuer else
                      pet.take_turn(self.player, self.dungeon, self.monsters,
                                    list(self.pets) + self._escorts_here(), self.ground_items))
            if result:
                action = result[0] if isinstance(result, tuple) else None
                # Unicorn pet returns ('unicorn_actions', [...]) instead of combat
                if action == 'unicorn_actions':
                    for msg in result[1]:
                        if msg[0] == 'heal':
                            self.add_message(f"The unicorn's horn glows softly — you heal {msg[1]} HP.", 'success')
                        elif msg[0] == 'cleanse':
                            self.add_message(f"The unicorn purifies you — {msg[1]} removed!", 'success')
                        elif msg[0] == 'trap':
                            self.add_message("The unicorn stamps nervously — trap sensed nearby!", 'warning')
                    continue
                target = result[1] if len(result) > 1 else None
                if action == 'attack' and target.alive:
                    dmg = pet.get_attack_damage(quiz_acc)
                    pre_max = target.max_hp
                    # Named as the hero sees it, before the bite springs a
                    # lurker (bug bash 5 MON-04, PET-03, INT-05).
                    _foe = the_name(target, lower=True)
                    actual = target.take_damage(dmg)
                    if getattr(pet, 'is_dad', False):
                        self.add_message(
                            f"Dad punched {_foe} in the face for {actual} damage!",
                            'success')
                    else:
                        self.add_message(
                            f"{pet.name} attacks {_foe}! ({actual} damage)", 'combat')
                    if not target.alive:
                        for k_msg in pet.gain_xp_from_kill(pre_max, _monster_level(target)):
                            self.add_message(k_msg, 'success')
                        self._on_monster_killed(target)

            # Passive XP (slow trickle, every 3rd turn) + regen + cooldown
            for msg in pet.gain_xp_passive():
                self.add_message(msg, 'success')
            # Trainer's Cap: pet_regen_bonus from head armor
            _prb = 0
            _head = self.player.armor_slots[0] if self.player.armor_slots else None
            if _head:
                _prb = getattr(_head, 'pet_regen_bonus', 0)
            pet.tick_regen(bonus=_prb)
            pet.tick_cooldown()

            # Temporary pet duration ticks
            if getattr(pet, 'is_dad', False) and pet.alive:
                if pet.tick_duration():
                    self.add_message(
                        "Dad smiles at you and fades away. He believes in you!", 'success')
            elif getattr(pet, 'is_sketch', False) and pet.alive:
                if pet.tick_duration():
                    self.add_message(
                        f"The Sketched {pet.monster_name} shimmers, fades, and dissolves "
                        f"back into the pages of the sketchbook.", 'info')

        # Monsters attack adjacent pets (each monster can swipe at one pet per turn)
        self._monster_swipes(self.pets)

    def _monster_swipes(self, targets, *, escorts: bool = False):
        """Each monster beside one of ``targets`` swipes at it once, for half
        its first attack's dice. Pets take this from _do_pet_turns; escorts
        (escort_system) take it in their own pass, so they are attacked even
        when the hero has no pet (DEEDS_KARMA_DESIGN 6.2). An escort's armour
        class is a to-hit roll against the monster's THAC0; a pet is always
        hit. Returns the targets slain this pass, with their killers."""
        slain = []
        # One swipe per monster per turn, shared by the pet pass and the
        # escort pass: a monster beside a pet and an escort picks one (PET-06).
        _turn = getattr(self, 'turn_count', 0)
        _done = getattr(self, '_swiped_this_turn', None)
        if not _done or _done[0] != _turn:
            _done = self._swiped_this_turn = (_turn, set())
        swiped = _done[1]
        # C13: while time is stopped, ordinary monsters are held here too (as
        # in _do_monster_turns); named foes are not.
        _ts_pets = self.player.has_effect('time_stopped')
        for m in self.monsters:
            if not m.alive or id(m) in swiped:
                continue
            if _ts_pets and not m._is_named_foe():
                continue
            # A sleeping or held monster, a friend, or something with no
            # attack does not bite: the Lost Girl could kill a pet.
            if (not getattr(m, 'attacks', None) or getattr(m, 'is_allied', False)
                    or getattr(m, '_npc_encounter_tag', None)
                    or getattr(m, '_flavor_encounter_tag', None)
                    or getattr(m, '_is_unicorn', False)
                    or any(m.has_effect(e) for e in ('sleeping', 'paralyzed', 'stunned', 'frozen',
                                                     'feared', 'charmed'))):
                continue
            for pet in targets:
                if not pet.alive:
                    continue
                # Unicorn pet design contract: enemies do not target her in melee
                # (AoE/traps can still hit, but adjacent monsters ignore her).
                if getattr(pet, 'is_unicorn', False):
                    continue
                if max(abs(m.x - pet.x), abs(m.y - pet.y)) <= 1:
                    swiped.add(id(m))
                    # A lurker that bites gives itself away (bug bash 5
                    # PET-04: any blow, either way, springs it).
                    if m.spring():
                        self._say_springs()
                    _killer = the_name(m, lower=True)
                    if escorts:
                        to_hit = int(getattr(m, 'thac0', 20)) - int(getattr(pet, 'ac', 0) or 0)
                        if random.randint(1, 20) < to_hit:
                            break         # a miss is still this monster's swipe
                    # Monster swipes at pet — use a fraction of its normal damage
                    from dice import roll as _dice_roll
                    pet_dmg = max(1, _dice_roll(m.attacks[0]['damage']) // 2) if m.attacks else 1
                    # Leggings of Enkidu (wild_friend): pets take less damage
                    # — "the wild man stands beside his friend." Mathematically
                    # equivalent to a max-HP buff without touching the curve.
                    try:
                        from armor_procs import proc_value
                        _wf = float(proc_value(self.player, 'wild_friend') or 0.0)
                        if _wf > 0 and not escorts:
                            pet_dmg = max(1, int(pet_dmg * (1.0 - _wf)))
                    except ImportError:
                        pass
                    pet.take_damage(pet_dmg)
                    if escorts and pet.alive and (pet.x, pet.y) in getattr(self, 'visible', ()):
                        self.add_message(f"{the_name(m)} strikes {pet.name}. ({pet_dmg} damage)", 'danger')
                    if not pet.alive:
                        slain.append((pet, m))
                        if escorts:
                            pass          # the escort's own ending says it
                        elif getattr(pet, 'is_sketch', False):
                            self.add_message(
                                f"The Sketched {pet.monster_name} shatters into "
                                f"fragments of ink and vanishes!", 'danger')
                        else:
                            self.add_message(f"{pet.name} has been slain by {_killer}!", 'danger')
                    break  # one pet swipe per monster per turn
        return slain
