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

import random

import pygame  # noqa: F401  -- kept for parity with sibling mixins; no direct use

import sound_system as _snd
from combat import player_attack
from game_helpers import throw_crosses_tile
from game_states import (
    STATE_PLAYER, STATE_QUIZ,
    STATE_TARGET, STATE_DEAD,
)
from items import Artifact, Weapon
from pet_system import Pet, random_species as random_pet_species


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

    # Weapon classes that can be thrown, with throw damage multiplier
    _THROWABLE_CLASSES = {
        'dagger':      1.0,    # designed for throwing
        'axe':         0.75,   # franciscas, hand axes
        'spear':       0.9,    # javelin-like
        'mace':        0.6,    # heavy but compact
        'flail':       0.5,    # awkward spin
        'net':         0.3,    # entangle, not damage
        'morningstar': 0.5,    # awkward but heavy impact
        'rapier':      0.4,    # fragile, not designed for it
        'scimitar':    0.5,    # curved blade, poor aerodynamics
        'sword':       0.4,    # not designed for throwing
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

    # ------------------------------------------------------------------
    # Targeting -- melee reach (Observe-like cursor for melee attacks)
    # ------------------------------------------------------------------

    def _open_melee_targeting(self):
        """Press 'a' to enter melee targeting mode — attack adjacent tiles (or further with reach weapons)."""
        weapon = self.player.weapon
        reach = weapon.reach if weapon else 1

        px, py = self.player.x, self.player.y

        # Build candidate list: alive monsters within melee reach
        candidates = [
            m for m in self.monsters
            if m.alive
            and abs(m.x - px) <= reach and abs(m.y - py) <= reach
            and not (m.x == px and m.y == py)
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
        material = weapon.material.lower()
        base = self._THROW_BREAK_CHANCE.get(material, self._THROW_BREAK_LEGENDARY)
        return base

    def _get_throw_range(self) -> int:
        """Throw range: 3 + (STR - 10) // 2, clamped to [3, 8]."""
        return max(3, min(8, 3 + (self.player.STR - 10) // 2))

    def _open_throw_targeting(self, potion):
        """Enter targeting mode for throwing a potion."""
        self._throw_targeting = True
        self._melee_targeting = False
        self._throw_potion = potion
        self._throw_reach = self._get_throw_range()

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
        tx, ty = self.target_cursor_x, self.target_cursor_y

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
            if hit_monster:
                self._apply_thrown_potion(item, hit_monster, display)
            else:
                self.add_message(
                    f"The {display} shatters on the ground. Nothing happens.", 'info'
                )

        self._advance_turn()

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
                    self._advance_turn()
                    return
            elif self._throw_crosses_tile(px, py, tx, ty, ax, ay):
                self.add_message(
                    "A rumble of distant thunder... but nothing happens. "
                    "Odin will not reforge this.", 'info')

        self.player.remove_from_inventory(weapon)
        display = weapon.name
        dmg = self._get_weapon_throw_damage(weapon)
        break_chance = self._get_weapon_break_chance(weapon)

        if monster:
            actual = monster.take_damage(dmg)
            self.add_message(
                f"You hurl the {display} at {monster.name}! ({actual} damage)", 'success'
            )
            if monster.is_dead():
                self._on_monster_killed(monster)
            land_x, land_y = monster.x, monster.y
        else:
            self.add_message(
                f"The {display} clatters to the ground.", 'info'
            )
            land_x, land_y = tx, ty

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
           any(m.alive and m.x == spawn_x and m.y == spawn_y for m in self.monsters) or \
           (spawn_x == self.player.x and spawn_y == self.player.y) or \
           any(p.alive and p.x == spawn_x and p.y == spawn_y for p in self.pets):
            # Try adjacent tiles
            found = False
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    nx, ny = land_x + dx, land_y + dy
                    if not self.dungeon.is_walkable(nx, ny):
                        continue
                    if nx == self.player.x and ny == self.player.y:
                        continue
                    if any(m.alive and m.x == nx and m.y == ny for m in self.monsters):
                        continue
                    if any(p.alive and p.x == nx and p.y == ny for p in self.pets):
                        continue
                    spawn_x, spawn_y = nx, ny
                    found = True
                    break
                if found:
                    break
            if not found:
                # No room — sphere is wasted
                self.add_message("The sphere shatters but there is no room for a creature!", 'warning')
                return

        species = random_pet_species()
        pet = Pet(species, spawn_x, spawn_y)
        self.pets.append(pet)
        self.add_message(pet.species['stages'][0]['msg'], 'success')
        _snd.play('player_healed')
        self._log_chronicle(f"A soul sphere hatched. {pet.name} emerged. I'm not alone anymore.")

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
                        and not any(m.alive and m.x == nx and m.y == ny for m in self.monsters)
                        and not any(p.alive and p.x == nx and p.y == ny for p in self.pets)):
                    spawn_x, spawn_y = nx, ny
                    placed = True
                    break
            if placed:
                break
        if not placed:
            self.add_message(
                "The sphere shatters in a flash of silver light, but there is no room!", 'warning')
            return

        from pet_system import DadPet
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
                    if m.alive and m.x == cx and m.y == cy:
                        return m
                # Check for wall (projectile stops)
                if not self.dungeon.is_walkable(cx, cy):
                    return None
        # Check target tile for monster
        for m in self.monsters:
            if m.alive and m.x == x1 and m.y == y1:
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
                        f"The {display} splashes {monster.name}, but it resists!", 'warning'
                    )
                    return
            # Check monster resistances list for thematic immunity
            mon_resists = getattr(monster, 'resistances', [])
            if ('poison' in mon_resists and debuff in ('poisoned', 'diseased')) or \
               ('magic' in mon_resists and debuff in ('confused', 'hallucinating', 'feared')):
                self.add_message(
                    f"The {display} splashes {monster.name}, but it seems immune!", 'warning'
                )
                return
            monster.add_effect(debuff, duration)
            label = debuff.replace('_', ' ').title()
            self.add_message(
                f"The {display} splashes {monster.name}! It is {label}!", 'success'
            )
            return

        # --- Buff effects (heals/buffs the monster -- bad idea!) ---
        buff = self._THROW_BUFF_MAP.get(effect)
        if buff:
            monster.add_effect(buff, duration)
            label = buff.replace('_', ' ').title()
            self.add_message(
                f"The {display} splashes {monster.name}. It looks {label}!", 'danger'
            )
            return

        # --- Healing effects (restore monster HP) ---
        if effect in ('heal', 'extra_heal', 'full_heal'):
            if effect == 'full_heal':
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
                    f"The {display} splashes {monster.name}. It heals {healed} HP!", 'danger'
                )
            else:
                self.add_message(
                    f"The {display} splashes {monster.name}. It looks unaffected.", 'info'
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
                and not any(m.alive and m.x == x and m.y == y for m in self.monsters)
                and not any(p.alive and p.x == x and p.y == y for p in self.pets)
                and (x, y) != (self.player.x, self.player.y)
            ]
            if walkable:
                nx, ny = _rng.choice(walkable)
                monster.x, monster.y = nx, ny
                self.add_message(
                    f"The {display} splashes {monster.name} -- it vanishes!", 'success'
                )
            else:
                self.add_message(
                    f"The {display} splashes {monster.name} but nothing happens.", 'info'
                )
            return

        # --- Stat drain (damage the monster instead) ---
        if effect in ('drain_str', 'drain_con', 'drain_int', 'drain_wis'):
            dmg = max(1, monster.max_hp // 20)
            actual = monster.take_damage(dmg)
            self.add_message(
                f"The {display} saps {monster.name}'s vitality! ({actual} damage)", 'success'
            )
            return

        # --- Everything else: no meaningful effect on monsters ---
        self.add_message(
            f"The {display} splashes {monster.name} but has no effect.", 'info'
        )

    # ------------------------------------------------------------------
    # Combat utilities
    # ------------------------------------------------------------------

    def _nearest_visible_monster(self):
        """Return the closest alive monster currently in FOV, or None."""
        px, py = self.player.x, self.player.y
        best, best_dist = None, float('inf')
        for m in self.monsters:
            if m.alive and (m.x, m.y) in self.visible:
                d = abs(m.x - px) + abs(m.y - py)
                if d < best_dist:
                    best, best_dist = m, d
        return best

    # ------------------------------------------------------------------
    # On-kill side effects
    # ------------------------------------------------------------------

    def _on_monster_killed(self, monster, *, chain_score: int = 0, ranged: bool = False,
                           unarmed: bool = False, hp_pct_before: float | None = None):
        """Central handler for ALL monster kills: treasure, corpse, boss popup, seal tracking,
        plus the canonical quirk on_kill hook.

        Combat callers pass chain_score/ranged/unarmed/hp_pct_before. Spell, wand, AOE, and
        trap kill paths use defaults (chain_score=0, ranged=False) and still fire the hook
        for kill-count quirks like Caesar, Kali, Boudicca, Leonidas, Battle Trance, etc.
        """
        self.level_mgr.monsters_killed += 1
        self.add_message(f"The {monster.name} is slain!", 'success')
        self._drop_treasure(monster)
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
        if story_key:
            self._show_story_popup(story_key, STATE_PLAYER)
            _BOSS_CHRONICLE = {
                'asterion_minotaur': "Killed the Minotaur. Asterion. He was bigger than I expected. The labyrinth is quiet now.",
                'medusa_gorgon': "Medusa is dead. I couldn't look at her directly. Even the snakes were afraid at the end.",
                'fafnir_dragon': "Fafnir fell. The dragon's scales were like iron. I still smell the smoke.",
                'fenrir_wolf': "Fenrir is bound. Or dead. I'm not sure which. The wolf was... vast. The ground still shakes.",
                'abaddon_destroyer': "Abaddon is destroyed. The Pit is sealed. I can barely hold the pen.",
            }
            self._log_chronicle(_BOSS_CHRONICLE.get(monster.kind, f"Slew {monster.name}. It's done."))
        # Fafnir drops a unique blood potion with a hint about the throw-over reforge
        if monster.kind == 'fafnir_dragon':
            self._spawn_fafnir_blood(monster.x, monster.y)
        # Seal demon: track broken seal
        if getattr(monster, 'is_seal_demon', False):
            seal_id = 'seal_of_' + monster.kind.replace('seal_demon_', '')
            self.seals_broken.add(seal_id)
            count = len(self.seals_broken)
            self.add_message(
                f"The {monster.name} falls! A seal is broken! ({count}/7)", 'success')
            self._log_chronicle(f"Broke a seal. {monster.name} is gone. {count} of 7 seals now shattered. The air feels heavier.")
            if count == 7:
                self.add_message(
                    "ALL SEVEN SEALS ARE BROKEN. The way to the Pit stands open.", 'danger')
                self._log_chronicle("All seven seals are broken. The ground split open. Whatever is down there, it's free now. And I have to face it.")
        self.ground_items.append(self._make_corpse(monster))

    def _drop_treasure(self, monster):
        """Drop gold and possibly an item when a monster dies."""
        import random as _rng
        treasure = getattr(monster, 'treasure', {})
        gold_range = treasure.get('gold', [0, 0])
        gold = _rng.randint(int(gold_range[0]), max(int(gold_range[0]), int(gold_range[1])))
        if gold > 0:
            from items import GoldPile
            self.ground_items.append(GoldPile(gold, monster.x, monster.y))
            self.add_message(
                f"The {monster.name} drops {gold} gold coins.", 'loot'
            )
        item_chance = treasure.get('item_chance', 0.0)
        if _rng.random() < item_chance:
            item_tier = int(treasure.get('item_tier', 1))
            self._spawn_treasure_item(monster.x, monster.y, item_tier)

        # Boss reward scroll
        boss_scroll_id = treasure.get('boss_scroll_id')
        if boss_scroll_id:
            self._spawn_boss_scroll(monster.x, monster.y, boss_scroll_id)

        # Unique mini-boss drop
        unique_drop_id = treasure.get('unique_drop_id')
        if unique_drop_id:
            self._spawn_unique_item(monster.x, monster.y, unique_drop_id)

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
            },
        )
        if monster.kind in getattr(self.player, 'lore_known_monster_ids', set()):
            c.lore_identified = True
        return c

    def _spawn_treasure_item(self, x: int, y: int, tier: int):
        """Place a random item of up to `tier` at (x,y)."""
        import random as _rng
        from items import load_items, copy_at
        candidates = []
        for cls_name in ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll'):
            try:
                for item in load_items(cls_name):
                    if item.min_level <= tier * 5:
                        candidates.append(item)
            except Exception:
                pass
        if candidates:
            chosen = copy_at(_rng.choice(candidates), x, y)
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
                    f"You have no {ammo_type}s! Cannot fire the {weapon.name}.", 'warning'
                )
                return

        # Build candidate list: visible alive monsters sorted by distance
        px, py = self.player.x, self.player.y
        from combat import can_ranged_attack
        candidates = [
            m for m in self.monsters
            if m.alive and (m.x, m.y) in self.visible
            and can_ranged_attack(self.player, m, self.dungeon)
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
                f"Targeting with {weapon.name} -- arrow keys to move, TAB to cycle, ENTER to fire, ESC to cancel.",
                'info'
            )
        else:
            self.add_message(
                f"No targets in range for {weapon.name}. Move cursor with arrow keys, ENTER to fire, ESC to cancel.",
                'info'
            )

    def _confirm_wand_target(self):
        """Confirm wand target, then start the science quiz."""
        from combat import _line_of_sight
        cx, cy = self.target_cursor_x, self.target_cursor_y
        self._wand_targeting = False
        wand = self._pending_wand
        self._pending_wand = None

        target = next(
            (m for m in self.monsters if m.alive and m.x == cx and m.y == cy), None
        )
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

            if not result.success:
                self.add_message("The wand fizzes and fails to fire.", 'warning')
                self._advance_turn()
                return

            wand.charges -= 1
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

        # All wands use threshold quiz — power is baked into the wand's tier
        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='science',
            tier=wand.quiz_tier,
            callback=on_complete,
            threshold=getattr(wand, 'quiz_threshold', 2),
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

        target = next(
            (m for m in self.monsters if m.alive and m.x == cx and m.y == cy), None
        )
        if not target or (cx, cy) not in self.visible:
            self.add_message("No valid target.", 'warning')
            self.state = STATE_PLAYER
            return
        if not _line_of_sight(self.player.x, self.player.y, cx, cy, self.dungeon):
            self.add_message("No clear line of sight!", 'warning')
            self.state = STATE_PLAYER
            return

        if pid and pid.startswith('spell_'):
            # Targeted spell: start the quiz with this target
            spell = getattr(self, '_pending_spell', None)
            spell_id = getattr(self, '_pending_spell_id', None)
            self._pending_spell = None
            self._pending_spell_id = None
            if spell:
                self._start_spell_quiz(spell, spell_id, target)
            return  # quiz handles state + advance_turn

        if pid == 'sketch_manifest':
            # Store target for quiz callback, then start AI escalator chain
            self._sketch_target_monster = target
            self.add_message(
                f"You begin sketching the {target.name} with furious concentration...", 'info')
            self.quiz_title = "MANIFESTING -- AI"
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
                            and not any(m.alive and m.x == nx and m.y == ny for m in self.monsters)
                            and not any(p.alive and p.x == nx and p.y == ny for p in self.pets)):
                        pet = SketchedPet(monster, nx, ny, duration)
                        self.pets.append(pet)
                        placed = True
                        break
                if not placed:
                    # Fallback: place on player tile
                    pet = SketchedPet(monster, px, py, duration)
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
            self.quiz_title = "FIRE BREATH -- AI"
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
                base = _fb_roll(dice)
                scaled = self._int_scaled_damage(base)
                tcx, tcy = self._stuffie_cone_target
                px, py = pl.x, pl.y
                cone = get_cone_tiles(px, py, tcx, tcy, max_range=6)
                hits = 0
                kills = 0
                for m in list(self.monsters):
                    if m.alive and (m.x, m.y) in cone and (m.x, m.y) in self.visible:
                        m.take_damage(scaled)
                        hits += 1
                        if not m.alive:
                            self._on_monster_killed(m)
                            kills += 1
                self.add_message(
                    "The Charmander Stuffie glows white-hot! "
                    f"You breathe a cone of fire! ({dice} damage, chain {chain})", 'success')
                if hits:
                    self.add_message(
                        f"{hits} creatures engulfed for {scaled} fire damage! ({kills} slain)", 'combat')
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

        # Monster at cursor
        monster = next(
            (m for m in self.monsters if m.alive and m.x == cx and m.y == cy), None
        )
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
        """Confirm a ranged shot at the cursor position."""
        target = next(
            (m for m in self.monsters
             if m.alive and m.x == self.target_cursor_x and m.y == self.target_cursor_y),
            None
        )
        self.state = STATE_PLAYER
        if target:
            from combat import can_ranged_attack
            if can_ranged_attack(self.player, target, self.dungeon):
                self._fire_ranged(target)
            else:
                self.add_message("No clear line of sight to that target.", 'warning')
        else:
            self.add_message("No target there -- shot cancelled.", 'warning')

    def _confirm_melee_target(self):
        """Confirm a melee strike at the cursor position."""
        cx, cy = self.target_cursor_x, self.target_cursor_y
        self.state = STATE_PLAYER

        # 1. Monster at cursor -- melee combat
        target = next(
            (m for m in self.monsters
             if m.alive and m.x == cx and m.y == cy),
            None
        )
        if target:
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
                mimic = _spawn_mimic(container, self.monsters, self.dungeon_level)
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
        self.add_message("You dig a pit in the floor!", 'success')
        _snd.play('trap')
        if not getattr(self, '_chronicle_first_pit', False):
            self._chronicle_first_pit = True
            self._log_chronicle("Dug a pit with the shovel. Took everything I had. If something walks over this...")
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
        dmg = _dice_roll('1d4')
        actual = self.player.take_damage(dmg, 'physical')
        self.player.add_effect('in_pit', 1)  # duration 1 = cleared on next move
        self.add_message(f"You fall into a pit! ({actual} damage)", 'danger')

    # ------------------------------------------------------------------
    # Ranged attack resolution
    # ------------------------------------------------------------------

    def _fire_ranged(self, monster):
        """Consume one ammo and launch the math chain quiz for a ranged shot."""
        weapon = self.player.ranged_weapon
        ammo_type = weapon.requires_ammo
        ammo_item = None

        # Consume one ammo item (skip for infinite ammo weapons)
        if not getattr(weapon, 'infinite_ammo', False):
            ammo_item = next(
                (i for i in self.player.inventory
                 if getattr(i, 'ammo_type', None) == ammo_type),
                None
            )
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
        self.quiz_title = (
            f"FIRE {weapon.name.upper()} at {monster.name.upper()}  --  MATH CHAIN"
        )

        def on_complete(damage: int, killed: bool, chain: int, stunned: bool = False,
                        knocked: bool = False, crit: bool = False, **kwargs):
            self.state = STATE_PLAYER
            self.combat_target = None
            if chain == 0:
                self.add_message(
                    f"Your shot flies wide -- you miss the {monster.name}!", 'warning'
                )
            else:
                self.add_message(
                    f"Chain x{chain}! Your {weapon.requires_ammo} strikes the {monster.name} for {damage} damage!",
                    'success'
                )
                if killed:
                    self._on_monster_killed(
                        monster,
                        chain_score=chain,
                        ranged=True,
                        hp_pct_before=getattr(self, '_combat_hp_pct_before', 1.0),
                    )
            self._advance_turn()

        # Tablet of Destinies: allow quiz reroll if not used this floor
        self.quiz_engine._reroll_flag = self._has_tablet_of_destinies() and not getattr(self, '_quiz_reroll_used', False)
        player_attack(self.player, monster, self.quiz_engine, on_complete, ammo=ammo_item)

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
        self.quiz_title = f"COMBAT vs {monster.name.upper()}  --  MATH CHAIN"
        if monster.kind == 'abaddon_destroyer' and not getattr(self, '_chronicle_abaddon_start', False):
            self._chronicle_abaddon_start = True
            self._log_chronicle("Abaddon. The Destroyer. He's real. He's here. This is it.")
        qs = getattr(self, 'quirk_system', None)
        if qs:
            qs.on_combat_started()
        self._combat_hp_pct_before = self.player.hp / max(1, self.player.max_hp)

        if monster.kind == 'floating_eye':
            cur = self.player.status_effects.get('paralyzed', 0)
            self.player.status_effects['paralyzed'] = max(cur, 3)
            self.add_message("The floating eye's gaze paralyzes you!", 'danger')

        def on_complete(damage: int, killed: bool, chain: int, stunned: bool = False,
                        knocked: bool = False, crit: bool = False, **kwargs):
            self.state = STATE_PLAYER
            self.combat_target = None
            # Tablet of Destinies: mark reroll as used this floor
            if getattr(self.quiz_engine, 'reroll_was_used', False):
                self._quiz_reroll_used = True
                self.add_message("The Tablet of Destinies cracks — fate rewritten!", 'info')
            if chain == 0:
                self.add_message(
                    f"You swing wildly at the {monster.name} and miss!", 'warning'
                )
            elif (chain >= 1 and monster.kind == 'fenrir_wolf' and monster.alive
                  and any(getattr(i, 'id', '') == 'vidars_sandal'
                          for i in self.player.inventory)):
                # Vidar's Sandal instant kill!
                monster.hp = 0
                monster.alive = False
                _snd.play('monster_hit')
                self.add_message(
                    "You plant Vidar's Sandal against Fenrir's lower jaw!", 'combat')
                self.add_message(
                    "With impossible strength, you wrench the great wolf's mouth apart!", 'combat')
                self.add_message(
                    "FENRIR, THE WORLD-WOLF, IS TORN ASUNDER!", 'success')
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
                if crit:
                    msg = f"CRITICAL! Chain x{chain}! You strike the {monster.name} for {damage} damage!"
                else:
                    msg = f"Chain x{chain}! You strike the {monster.name} for {damage} damage!"
                if stunned:
                    msg += f" The {monster.name} is stunned!"
                if monster.status_effects.get('bleeding', 0) > 0:
                    msg += f" The {monster.name} is bleeding!"
                if knocked and not killed:
                    from combat import apply_knockback
                    apply_knockback(self.player, monster, self.dungeon, self.monsters)
                    msg += f" The {monster.name} is knocked back!"
                if kwargs.get('poisoned'):
                    msg += f" The {monster.name} is poisoned!"
                if kwargs.get('burned'):
                    msg += f" The {monster.name} is burning!"
                if kwargs.get('confused'):
                    msg += f" The {monster.name} is confused!"
                if kwargs.get('petrified'):
                    msg += f" The {monster.name} is turning to stone!"
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
                    # the kill happens (greatsword cleave_on_kill / great_axe
                    # cleave_plus_bleed). Damage is half of the killing blow.
                    cleave_dmg = kwargs.get('cleave_dmg', 0)
                    if cleave_dmg:
                        _w = self.player.weapon
                        _bleed = _w and getattr(_w, 'class_mechanic', '') == 'cleave_plus_bleed'
                        for _m in self.monsters:
                            if _m.alive and _m is not monster \
                                    and abs(_m.x - monster.x) <= 1 \
                                    and abs(_m.y - monster.y) <= 1:
                                _actual = _m.take_damage(cleave_dmg)
                                if _bleed and _actual > 0:
                                    _m.add_effect('bleeding', 3)
                                if not _m.alive:
                                    self._on_monster_killed(_m, chain_score=chain)
                        self.add_message(
                            "Your swing carries through — adjacent foes are cleaved!", 'success')
                    # Amenonuhoko: slow adjacent monsters on kill
                    w = self.player.weapon
                    if w and getattr(w, 'aoe_slow_on_kill', False):
                        for m in self.monsters:
                            if m.alive and abs(m.x - monster.x) <= 1 and abs(m.y - monster.y) <= 1:
                                m.add_effect('slowed', 3)
                        self.add_message("A wave of primordial stillness ripples outward.", 'info')
            self._advance_turn()

        # Tablet of Destinies: allow quiz reroll if not used this floor
        self.quiz_engine._reroll_flag = self._has_tablet_of_destinies() and not getattr(self, '_quiz_reroll_used', False)
        player_attack(self.player, monster, self.quiz_engine, on_complete)

    # ------------------------------------------------------------------
    # Monster turns
    # ------------------------------------------------------------------

    def _do_monster_turns(self):
        # Time stop: monsters are frozen this turn
        if self.player.has_effect('time_stopped'):
            return

        # Death acts first -- not part of self.monsters to avoid save/load issues
        if self.death_pursues and self.death_monster is not None:
            dm = self.death_monster
            all_m = self.monsters + [dm]
            _pet_occ_d = {(p.x, p.y) for p in self.pets if p.alive}
            did_attack = dm.take_turn(self.player, self.dungeon, all_m,
                                      extra_occupied=_pet_occ_d)
            if did_attack:
                dmg, msg = dm.attack(self.player)
                self.add_message(msg, 'danger')
                if self.player.is_dead():
                    self.defeat_reason = 'died'
                    self._on_game_over()
                    self.state = STATE_DEAD
                    self.add_message("You have died! Press ESC to quit.", 'danger')
                    return

        # --- Ariadne's Thread: neutralize wall-phasing monsters ---
        has_thread = any(getattr(i, 'id', '') == 'ariadnes_thread'
                         for i in self.player.inventory)
        for m in self.monsters:
            if getattr(m, 'can_phase_walls', False):
                if has_thread:
                    m.can_phase_walls = False
                    m.speed = min(m.speed, 6)  # slowed by the Thread's power
                    if m.ai_pattern == 'hit_and_run':
                        m.ai_pattern = 'aggressive'  # can't hide anymore

        for m in self.monsters:
            if not m.alive:
                continue
            # Allied monsters (angels): handle separately
            if getattr(m, 'is_allied', False):
                m.take_turn(self.player, self.dungeon, self.monsters,
                            extra_occupied={(_p.x, _p.y) for _p in self.pets if _p.alive})
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
            if (m.x, m.y) in self.visible:
                self.player.known_monster_ids.add(m.kind)
            _pet_occ = {(p.x, p.y) for p in self.pets if p.alive}
            _was_in_pit = m.has_effect('stuck_in_pit')
            _pos_before = (m.x, m.y)
            did_attack = m.take_turn(self.player, self.dungeon, self.monsters,
                                     extra_occupied=_pet_occ)
            # Confused friendly fire message
            _cf_hit = getattr(m, '_confused_hit', None)
            if _cf_hit:
                victim, dmg = _cf_hit
                m._confused_hit = None
                if (m.x, m.y) in self.visible or (victim.x, victim.y) in self.visible:
                    self.add_message(
                        f"The confused {m.name} attacks the {victim.name} for {dmg} damage!", 'combat')
                if not victim.alive:
                    self._on_monster_killed(victim)
            # Abaddon locust swarm spawning
            if getattr(m, '_wants_locust_spawn', False) and m.kind == 'abaddon_destroyer':
                m._wants_locust_spawn = False
                self._spawn_abaddon_locusts(m)
            # Fenrir rage escalation message
            rage_msg = getattr(m, '_rage_message', '')
            if rage_msg and (m.x, m.y) in self.visible:
                self.add_message(rage_msg, 'danger')
            # Check if monster moved onto a dug pit
            if (not _was_in_pit and not m.has_effect('stuck_in_pit')
                    and not m.has_effect('levitating')
                    and (m.x, m.y) != _pos_before
                    and (m.x, m.y) in getattr(self.dungeon, 'pits', set())):
                from dice import roll as _pit_roll
                pit_dmg = _pit_roll('1d4')
                m.hp -= pit_dmg
                if m.hp <= 0:
                    m.alive = False
                m.status_effects['stuck_in_pit'] = random.randint(3, 4)
                if (m.x, m.y) in self.visible:
                    self.add_message(f"The {m.name} falls into a pit!", 'info')
                if not m.alive:
                    self._on_monster_killed(m)
                continue  # can't attack this turn — just fell
            if did_attack:
                # Displacement: 30% miss chance
                if self.player.has_effect('displacement') and random.random() < 0.30:
                    self.add_message(f"The {m.name}'s attack passes through your displaced image!", 'info')
                    continue

                _effects_before = set(self.player.status_effects.keys())
                dmg, msg = m.attack(self.player)
                self.add_message(msg, 'danger')

                # Piercing collateral: damage monsters in the projectile path
                _collateral = getattr(m, '_piercing_collateral', [])
                if _collateral and dmg > 0:
                    _coll_frac = random.uniform(0.75, 0.90)
                    _coll_dmg = max(1, int(dmg * _coll_frac))
                    for _cv in _collateral:
                        if not _cv.alive:
                            continue
                        _cv.hp -= _coll_dmg
                        if (m.x, m.y) in self.visible or (_cv.x, _cv.y) in self.visible:
                            self.add_message(
                                f"The {m.name}'s attack tears through the {_cv.name} for {_coll_dmg} collateral damage!",
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
                        f"The {m.name}'s attack drains your stamina! (-{_sp_drain} SP)", 'danger')

                # Fire shield: reflect melee damage back
                if self.player.has_effect('fire_shield') and dmg > 0:
                    reflect_dmg = random.randint(2, 9)
                    m.hp -= reflect_dmg
                    self.add_message(f"Flames lash back at the {m.name} for {reflect_dmg}!", 'danger')
                    if m.hp <= 0:
                        m.alive = False
                        self._on_monster_killed(m)
                # Cold shield: reflect melee damage back
                if self.player.has_effect('cold_shield') and dmg > 0:
                    reflect_dmg = random.randint(2, 9)
                    m.hp -= reflect_dmg
                    self.add_message(f"Ice shatters back at the {m.name} for {reflect_dmg}!", 'danger')
                    if m.hp <= 0 and m.alive:
                        m.alive = False
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
                if _shld and getattr(_shld, 'fire_reflect', 0) > 0 and dmg > 0:
                    _atk_types = getattr(m, 'damage_types', getattr(m, 'attack_types', []))
                    if 'fire' in _atk_types:
                        _fire_ref = max(1, int(dmg * _shld.fire_reflect))
                        m.hp -= _fire_ref
                        self.add_message(f"Svalinn reflects flame back at the {m.name} for {_fire_ref}!", 'combat')
                        if m.hp <= 0 and m.alive:
                            m.alive = False
                            self._on_monster_killed(m)

                # Babr-e Bayan: absorb first hit per floor
                if dmg > 0 and not getattr(self, '_first_hit_used', False):
                    for _arm_slot in self.player.armor_slots:
                        if _arm_slot and getattr(_arm_slot, 'first_hit_absorb', False):
                            self.player.hp = min(self.player.max_hp, self.player.hp + dmg)
                            self._first_hit_used = True
                            self.add_message("The tiger-skin absorbs the blow completely!", 'success')
                            break

                # Jade Cicada: death save (once per floor)
                if self.player.hp <= 0 and not getattr(self, '_death_save_used', False):
                    for _acc in self.player.equipped_accessories:
                        if getattr(_acc, 'death_save', False):
                            self.player.hp = 1
                            self._death_save_used = True
                            self.add_message("The jade cicada cracks — but holds! You cling to life!", 'success')
                            _snd.play('player_healed')
                            break

                # Ankh of Isis: resurrect on death (consumes the item)
                if self.player.hp <= 0:
                    for _acc in self.player.equipped_accessories:
                        if getattr(_acc, 'resurrect_on_death', False):
                            self.player.hp = max(1, self.player.max_hp // 2)
                            # Clear the slot that held the Ankh
                            if self.player.amulet_slot is _acc:
                                self.player.amulet_slot = None
                            else:
                                for _i, _r in enumerate(self.player.accessory_slots):
                                    if _r is _acc:
                                        self.player.accessory_slots[_i] = None
                                        break
                            self.add_message("The Ankh of Isis shatters! Isis breathes life back into you!", 'success')
                            self._log_chronicle("I died. Then light. Isis pulled me back. The ankh is dust now.")
                            _snd.play('player_healed')
                            break

                # Life Save: if the blow was fatal, survive at 1 HP (burns the amulet)
                if self.player.hp <= 0 and self.player.has_effect('life_save'):
                    self.player.hp = 1
                    del self.player.status_effects['life_save']
                    self.add_message(
                        "The amulet blazes -- death averted! Its life-saving magic is spent.", 'success'
                    )
                    _snd.play('player_healed')

                # Reflecting: negate 50% of newly applied status effects
                _new_effects = set(self.player.status_effects.keys()) - _effects_before
                if self.player.has_effect('reflecting') and _new_effects:
                    for _new_eff in list(_new_effects):
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
                                f"back at the {m.name}!", 'info'
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

    def _do_pet_turns(self):
        """Process pet AI, XP, regen, cooldowns, and monster attacks on pets."""
        if not self.pets:
            return

        # Compute quiz accuracy for pet damage scaling
        total_q = self.correct_answers + self.wrong_answers
        quiz_acc = self.correct_answers / max(1, total_q)

        for pet in self.pets:
            if not pet.alive:
                continue

            # Pet AI turn
            result = pet.take_turn(self.player, self.dungeon, self.monsters, self.pets, self.ground_items)
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
                if action == 'special' and target and target.alive:
                    dmg = pet.get_special_damage(quiz_acc)
                    actual = target.take_damage(dmg)
                    pet.use_special()
                    sp = pet.species
                    self.add_message(
                        f"{pet.name} uses {sp['special_name']} on {target.name}! ({actual} damage)",
                        'combat'
                    )
                    # Apply special status effect
                    if random.random() < sp['special_status_chance'] and target.alive:
                        target.status_effects[sp['special_status']] = \
                            max(target.status_effects.get(sp['special_status'], 0), 4)
                    if not target.alive:
                        self._on_monster_killed(target)
                elif action == 'attack' and target.alive:
                    dmg = pet.get_attack_damage(quiz_acc)
                    actual = target.take_damage(dmg)
                    if getattr(pet, 'is_dad', False):
                        self.add_message(
                            f"Dad punched {target.name} in the face for {actual} damage!",
                            'success')
                    else:
                        self.add_message(
                            f"{pet.name} attacks {target.name}! ({actual} damage)", 'combat')
                    if not target.alive:
                        self._on_monster_killed(target)

            # XP, regen, cooldown
            msgs = pet.gain_xp(1)
            for msg in msgs:
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
        for m in self.monsters:
            if not m.alive:
                continue
            for pet in self.pets:
                if not pet.alive:
                    continue
                if max(abs(m.x - pet.x), abs(m.y - pet.y)) <= 1:
                    # Monster swipes at pet — use a fraction of its normal damage
                    from dice import roll as _dice_roll
                    pet_dmg = max(1, _dice_roll(m.attacks[0]['damage']) // 2) if m.attacks else 1
                    pet.take_damage(pet_dmg)
                    if not pet.alive:
                        if getattr(pet, 'is_sketch', False):
                            self.add_message(
                                f"The Sketched {pet.monster_name} shatters into "
                                f"fragments of ink and vanishes!", 'danger')
                        else:
                            self.add_message(f"{pet.name} has been slain by {m.name}!", 'danger')
                    break  # one pet swipe per monster per turn
