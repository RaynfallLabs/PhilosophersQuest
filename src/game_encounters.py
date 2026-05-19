"""Game's NPC and special-level encounter handlers, extracted from main.py.

This module defines :class:`EncountersMixin`, which the real ``Game`` class
inherits alongside :class:`game_render.RenderMixin`,
:class:`game_menus.MenuMixin`, and :class:`game_input.InputMixin`.  The mixin
owns:

  * Karma NPC + flavor NPC spawn/open/close/reward logic.
  * Altar of the Last Judgment resolution.
  * Special-level encounter handlers: secret cow, ethereal unicorn (full
    state machine), and Magic Dungeon Carrot spawn.

The corresponding render code lives in :class:`game_render.RenderMixin`
(``_draw_npc_encounter``, ``_draw_judgment``, ``_draw_cow_encounter``) and
input code in :class:`game_input.InputMixin` (``_npc_encounter_input``,
``_judgment_input``, ``_cow_encounter_input``).  MRO dispatches all
cross-mixin ``self._foo()`` calls.

Class-level constants (``_COW_MOO_MESSAGES``, ``_COW_POKE_MESSAGES``) stay
on ``Game`` so they remain co-located with related cow-encounter code — the
mixin's methods reach them through ``self.`` and MRO.
"""
from __future__ import annotations

import random

from game_states import (
    STATE_PLAYER, STATE_QUIZ,
    STATE_NPC_ENCOUNTER, STATE_COW_ENCOUNTER, STATE_JUDGMENT,
)


class EncountersMixin:
    # ------------------------------------------------------------------
    # Secret cow encounter
    # ------------------------------------------------------------------

    def _maybe_spawn_cow(self, level: int):
        """Spawn the secret cow NPC on its designated level (once per run)."""
        if self._cow_spawned or self._cow_level_done:
            return
        if level != self._cow_level:
            return
        from monster import Monster
        cow_def = {
            'id': 'secret_cow',
            'name': 'a cow',
            'symbol': 'C',
            'color': [180, 140, 80],
            'hp': 1,
            'thac0': 20,
            'speed': 0,
            'attacks': [],
            'ai_pattern': 'sessile',
            'resistances': [],
            'weaknesses': [],
            'min_level': level,
            'is_allied': True,
            'harvest_tier': 0,
            'harvest_threshold': 99,
            'ingredient_id': None,
        }
        import random as _rng
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
        occupied = {(m.x, m.y) for m in self.monsters}
        occupied.add((self.player.x, self.player.y))
        for room in _rng.sample(rooms, min(len(rooms), 5)):
            for tx, ty in room.inner_tiles():
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    cow = Monster(cow_def, tx, ty)
                    cow._npc_encounter_tag = '_cow_dialog'
                    self.monsters.append(cow)
                    self._cow_npc = cow
                    self._cow_spawned = True
                    return

    def _start_cow_encounter(self, cow_monster):
        """Open the cow dialog when player bumps the cow NPC."""
        self._active_cow = cow_monster
        self._cow_dialog_phase = 'options'
        self.state = STATE_COW_ENCOUNTER

    def _enter_cow_level(self):
        """Teleport the player to the Moo Moo Farm."""
        from boss_levels import COW_LEVEL
        self.add_message(
            "The cow's eyes glow red. The ground splits open beneath you!", 'danger'
        )
        self.add_message("MOO MOO MOO MOO MOO!", 'danger')
        self._log_chronicle("I poked a cow too many times. The floor opened up. Now I'm in some kind of... cow dimension. This is not in any lore I've read.")
        self._cow_return_level = self.dungeon_level
        # Remove the cow from the current level
        if self._cow_npc and self._cow_npc in self.monsters:
            self.monsters.remove(self._cow_npc)
        self._cow_npc = None
        self.state = STATE_PLAYER
        try:
            self._change_level(COW_LEVEL, enter_from_top=True)
        except Exception as e:
            self.add_message(f"Error entering cow level: {e}", 'danger')
            import traceback
            traceback.print_exc()

    def _exit_cow_level(self):
        """Return from Moo Moo Farm to the level where the cow was."""
        self._cow_level_done = True
        self.add_message("You step through the portal. The pasture fades behind you.", 'info')
        self.add_message("The cow is gone. The portal closes. Moo.", 'info')
        try:
            self._change_level(self._cow_return_level, enter_from_top=False)
        except Exception as e:
            self.add_message(f"Error exiting cow level: {e}", 'danger')
            import traceback
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Karma + flavor NPC spawn
    # ------------------------------------------------------------------

    def _maybe_spawn_npc(self, level: int):
        """Spawn an NPC on this level if one is assigned and hasn't been encountered."""
        enc = self._npc_encounter_levels.get(level)
        if enc is None:
            return
        if enc['tag'] in self._encountered_npcs:
            return
        # Don't double-spawn if the NPC is already on the floor (e.g., the
        # player descended past it without bumping, then returned — the saved
        # floor still has the NPC, and we'd otherwise add a duplicate).
        for _m in self.monsters:
            if getattr(_m, '_npc_encounter_tag', None) == enc['tag']:
                return
        # For triggered encounters, only spawn if the player has the trigger item
        if enc.get('trigger_item'):
            if enc['trigger_item'] not in self._npc_triggered_items:
                return

        from monster import Monster
        # Create a fake "monster" for the NPC so it renders and blocks tiles
        npc_def = {
            'id': enc.get('sprite_id', 'npc_traveler'),
            'name': enc['name'],
            'symbol': enc['symbol'],
            'color': list(enc['color']),
            'hp': 1,
            'thac0': 20,
            'speed': 0,
            'attacks': [],
            'ai_pattern': 'sessile',
            'resistances': [],
            'weaknesses': [],
            'min_level': level,
            'is_allied': True,
            'harvest_tier': 0,
            'harvest_threshold': 99,
            'ingredient_id': None,
        }
        # Place in a non-start room
        occupied = {(m.x, m.y) for m in self.monsters}
        occupied.add((self.player.x, self.player.y))
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
        import random as _rng
        for room in _rng.sample(rooms, min(len(rooms), 5)):
            tiles = list(room.inner_tiles())
            _rng.shuffle(tiles)
            for tx, ty in tiles:
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    npc = Monster(npc_def, tx, ty)
                    npc._npc_encounter_tag = enc['tag']
                    self.monsters.append(npc)
                    return

    def _maybe_spawn_flavor_npc(self, level: int):
        """Spawn a flavor (non-karmic) NPC on this level if one is assigned."""
        enc = getattr(self, '_flavor_encounter_levels', {}).get(level)
        if enc is None:
            return
        encountered = getattr(self, '_encountered_flavor_npcs', set())
        if enc['tag'] in encountered:
            return
        # Don't double-spawn — match the moral-NPC guard above.
        for _m in self.monsters:
            if getattr(_m, '_flavor_encounter_tag', None) == enc['tag']:
                return

        from monster import Monster
        npc_def = {
            'id': enc.get('sprite_id', 'npc_traveler'),
            'name': enc['name'],
            'symbol': enc['symbol'],
            'color': list(enc['color']),
            'hp': 1,
            'thac0': 20,
            'speed': 0,
            'attacks': [],
            'ai_pattern': 'sessile',
            'resistances': [],
            'weaknesses': [],
            'min_level': level,
            'is_allied': True,
            'harvest_tier': 0,
            'harvest_threshold': 99,
            'ingredient_id': None,
        }
        occupied = {(m.x, m.y) for m in self.monsters}
        occupied.add((self.player.x, self.player.y))
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
        import random as _rng
        for room in _rng.sample(rooms, min(len(rooms), 5)):
            tiles = list(room.inner_tiles())
            _rng.shuffle(tiles)
            for tx, ty in tiles:
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    npc = Monster(npc_def, tx, ty)
                    npc._flavor_encounter_tag = enc['tag']
                    self.monsters.append(npc)
                    return

    # ------------------------------------------------------------------
    # Magic Dungeon Carrot  (guaranteed spawn L1-19, once per run)
    # ------------------------------------------------------------------

    def _maybe_spawn_magic_carrot(self, level: int):
        """Place one Magic Dungeon Carrot on a random level between 1-19."""
        if getattr(self, '_magic_carrot_spawned', False):
            return
        if level < 1 or level > 19:
            return
        if not hasattr(self, '_magic_carrot_target_level'):
            import random as _rng
            self._magic_carrot_target_level = _rng.randint(1, 19)
        if level != self._magic_carrot_target_level:
            return

        from items import load_items
        import random as _rng
        foods = load_items('food')
        carrot_template = next((f for f in foods if f.id == 'magic_dungeon_carrot'), None)
        if carrot_template is None:
            return
        import copy
        carrot = copy.copy(carrot_template)
        # Place in a random room
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
        occupied = {(m.x, m.y) for m in self.monsters}
        occupied.add((self.player.x, self.player.y))
        for room in _rng.sample(rooms, min(len(rooms), 5)):
            tiles = list(room.inner_tiles())
            _rng.shuffle(tiles)
            for tx, ty in tiles:
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    carrot.x, carrot.y = tx, ty
                    self.ground_items.append(carrot)
                    self._magic_carrot_spawned = True
                    return

    # ------------------------------------------------------------------
    # Unicorn encounter  (L21-39, spawns once per run)
    # ------------------------------------------------------------------

    def _maybe_spawn_unicorn(self, level: int):
        """Spawn the ethereal unicorn on one random level between 21-39."""
        if getattr(self, '_unicorn_spawned', False):
            return
        if level < 21 or level > 39:
            return
        # Pick a random level in 21-39 on first eligible entry; spawn on that level
        if not hasattr(self, '_unicorn_target_level'):
            import random as _rng
            self._unicorn_target_level = _rng.randint(21, 39)
        if level != self._unicorn_target_level:
            return

        from monster import Monster
        npc_def = {
            'id': 'ethereal_unicorn',
            'name': 'Ethereal Unicorn',
            'symbol': 'u',
            'color': [255, 255, 240],
            'hp': 200,
            'thac0': 20,
            'speed': 10,
            'attacks': [],
            'ai_pattern': 'sessile',
            'resistances': ['magic', 'holy'],
            'weaknesses': [],
            'min_level': level,
            'is_allied': True,
            'harvest_tier': 0,
            'harvest_threshold': 99,
            'ingredient_id': None,
        }
        occupied = {(m.x, m.y) for m in self.monsters}
        occupied.add((self.player.x, self.player.y))
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
        import random as _rng
        for room in _rng.sample(rooms, min(len(rooms), 5)):
            tiles = list(room.inner_tiles())
            _rng.shuffle(tiles)
            for tx, ty in tiles:
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    npc = Monster(npc_def, tx, ty)
                    npc._is_unicorn = True
                    npc._unicorn_state = 'wary'  # wary → relaxing → offered → eating → trusting
                    npc._unicorn_wait = 0
                    npc._unicorn_eat_turns = 0
                    self.monsters.append(npc)
                    self._unicorn_spawned = True
                    return

    def _handle_unicorn_bump(self, unicorn):
        """Handle player bumping the unicorn at various states."""
        state = getattr(unicorn, '_unicorn_state', 'wary')

        if state == 'wary':
            # Unicorn startles and moves away
            self.add_message("The unicorn startles and leaps away from you!", 'info')
            self._unicorn_flee(unicorn)
            unicorn._unicorn_wait = 0
            return True

        if state == 'relaxing':
            self.add_message("The unicorn watches you nervously. Perhaps an offering would help...", 'info')
            unicorn._unicorn_state = 'wary'
            unicorn._unicorn_wait = 0
            self._unicorn_flee(unicorn)
            return True

        if state in ('offered', 'eating'):
            self.add_message("The unicorn is eating! Don't disturb her!", 'info')
            unicorn._unicorn_state = 'wary'
            unicorn._unicorn_wait = 0
            self._unicorn_flee(unicorn)
            return True

        if state == 'trusting':
            # Karma check
            karma = getattr(self, 'karma', 0)
            if karma < 0:
                self.add_message(
                    "The unicorn gazes into your eyes... and recoils. She senses "
                    "darkness in your heart and gallops away!", 'danger')
                unicorn._unicorn_state = 'fled'
                unicorn.alive = False
                return True

            # Start the AI escalator quiz
            self.add_message(
                "The unicorn lowers her head and nuzzles your hand. "
                "A warm light envelops you both...", 'success')
            self._start_unicorn_quiz(unicorn)
            return True

        if state == 'fled':
            return True
        return False

    def _unicorn_flee(self, unicorn):
        """Move unicorn to a distant walkable tile in the same room or nearby."""
        import random as _rng
        px, py = self.player.x, self.player.y
        candidates = []
        for dy in range(-8, 9):
            for dx in range(-8, 9):
                nx, ny = unicorn.x + dx, unicorn.y + dy
                if not self.dungeon.in_bounds(nx, ny):
                    continue
                if not self.dungeon.is_walkable(nx, ny):
                    continue
                dist_from_player = abs(nx - px) + abs(ny - py)
                if dist_from_player < 4:
                    continue
                if any(m.alive and m.x == nx and m.y == ny for m in self.monsters):
                    continue
                candidates.append((nx, ny))
        if candidates:
            unicorn.x, unicorn.y = _rng.choice(candidates)

    def _tick_unicorn(self):
        """Called each turn to update unicorn state machine."""
        for m in self.monsters:
            if not getattr(m, '_is_unicorn', False) or not m.alive:
                continue
            state = getattr(m, '_unicorn_state', 'wary')
            px, py = self.player.x, self.player.y
            dist = max(abs(m.x - px), abs(m.y - py))

            if state == 'wary':
                # Player visible and within 8 tiles? Start watching
                if (m.x, m.y) in self.visible and dist <= 8:
                    m._unicorn_wait += 1
                    if m._unicorn_wait == 1:
                        self.add_message(
                            "A beautiful white unicorn stands nearby. She watches you warily.",
                            'info')
                    # If player stays still (or moves slowly) for 3 turns
                    if m._unicorn_wait >= 3:
                        m._unicorn_state = 'relaxing'
                        self.add_message(
                            "The unicorn seems to relax slightly. She sniffs the air...",
                            'info')
                else:
                    m._unicorn_wait = 0

            elif state == 'relaxing':
                # Check if player dropped a magic carrot adjacent to the unicorn
                carrot = None
                for item in self.ground_items:
                    if getattr(item, 'id', '') == 'magic_dungeon_carrot':
                        cdist = max(abs(item.x - m.x), abs(item.y - m.y))
                        if cdist <= 2:
                            carrot = item
                            break
                if carrot:
                    m._unicorn_state = 'eating'
                    m._unicorn_eat_turns = 0
                    # Move unicorn to the carrot
                    m.x, m.y = carrot.x, carrot.y
                    self.add_message(
                        "The unicorn's ears perk up! She approaches the Magic Dungeon "
                        "Carrot and begins to eat.", 'success')

            elif state == 'eating':
                m._unicorn_eat_turns += 1
                if m._unicorn_eat_turns >= 2:
                    # Remove the carrot from ground
                    self.ground_items = [
                        gi for gi in self.ground_items
                        if not (getattr(gi, 'id', '') == 'magic_dungeon_carrot'
                                and gi.x == m.x and gi.y == m.y)]
                    m._unicorn_state = 'trusting'
                    self.add_message(
                        "The unicorn finishes the carrot and looks at you with gentle "
                        "eyes. You may approach her now.", 'success')

    def _start_unicorn_quiz(self, unicorn):
        """Start the AI escalator_chain quiz for the unicorn encounter."""
        self._pending_unicorn = unicorn
        self.quiz_title = "THE UNICORN'S BLESSING  --  AI"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            chain = result.score  # 0-5
            self._apply_unicorn_boons(chain, unicorn)

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='ai',
            tier=1,
            callback=on_complete,
            max_chain=5,    # cap chain at 5 — matches the 0-5 chain comment in _apply_unicorn_boons
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('ai'),
            base_seconds=self.player.get_quiz_timer('ai'),
        )

    def _apply_unicorn_boons(self, chain: int, unicorn):
        """Apply tiered boons based on quiz chain score."""
        if chain == 0:
            self.add_message(
                "The unicorn nuzzles your hand gently, then trots away. "
                "Perhaps next time...", 'info')
            unicorn._unicorn_state = 'fled'
            unicorn.alive = False
            return

        # Chain 1+: Regenerating status
        self.player.add_effect('regenerating', 30)
        self.add_message("The unicorn's horn glows — warm healing energy fills you! (regenerating 30 turns)", 'success')

        if chain >= 2:
            # Full HP/SP/MP restore
            self.player.hp = self.player.max_hp
            self.player.sp = self.player.max_sp
            self.player.mp = self.player.max_mp
            self.add_message("A radiant pulse fully restores your body, stamina, and magic!", 'success')

        if chain >= 3:
            # Remove curse from all equipped items
            uncursed = 0
            for item in self.player.get_equipped_items().values():
                if item and getattr(item, 'buc', 'uncursed') == 'cursed':
                    item.buc = 'uncursed'
                    item.buc_known = True
                    uncursed += 1
            # Also check inventory
            for item in self.player.inventory:
                if getattr(item, 'buc', 'uncursed') == 'cursed':
                    item.buc = 'uncursed'
                    item.buc_known = True
                    uncursed += 1
            if uncursed:
                self.add_message(f"Holy light purifies your belongings — {uncursed} item{'s' if uncursed != 1 else ''} uncursed!", 'success')
            else:
                self.add_message("Holy light sweeps through your belongings — all is pure.", 'success')

        if chain >= 4:
            # Permanent bonus: magic resistance
            import random as _rng
            bonus = _rng.choice(['magic_resist', 'poison_resist'])
            self.player.add_effect(bonus, -1)  # -1 = permanent
            nice = bonus.replace('_', ' ').title()
            self.add_message(f"The unicorn bestows a permanent blessing: {nice}!", 'success')

        if chain >= 5:
            # Unicorn joins as a pet!
            from pet_system import UnicornPet
            pet = UnicornPet(unicorn.x, unicorn.y)
            self.pets.append(pet)
            unicorn.alive = False  # remove the NPC monster
            self.add_message(
                "The unicorn bows her head to you. A bond forms between your souls — "
                "the Ethereal Unicorn joins you as a companion!", 'success')
            self.add_message(
                "She will heal you, cleanse afflictions, and sense hidden traps.",
                'info')
            self._log_chronicle("She stayed. The unicorn bowed her head and something passed between us. I can feel her presence at the edge of my thoughts. We're connected now.")
            return

        # If chain < 5, unicorn departs after granting boons
        unicorn.alive = False
        unicorn._unicorn_state = 'fled'
        self.add_message("The unicorn dips her head in farewell and vanishes in a shimmer of light.", 'info')
        self._log_chronicle("The unicorn touched her horn to my hand. Warmth flooded through me. Then she was gone, vanished like morning fog. I feel... different.")

    # ------------------------------------------------------------------
    # NPC encounter open / resolve / close
    # ------------------------------------------------------------------

    def _start_flavor_encounter(self, monster):
        """Begin a flavor encounter when the player bumps a flavor NPC."""
        tag = getattr(monster, '_flavor_encounter_tag', None)
        if tag is None:
            return False

        enc = getattr(self, '_flavor_encounter_levels', {}).get(self.dungeon_level)
        if enc is None or enc['tag'] != tag:
            # Search all levels for this tag
            for lvl_enc in getattr(self, '_flavor_encounter_levels', {}).values():
                if lvl_enc['tag'] == tag:
                    enc = lvl_enc
                    break
        if enc is None:
            return False

        # Reuse the NPC encounter UI with a flavor flag
        self._npc_encounter_active = enc
        self._npc_encounter_monster = monster
        self._npc_encounter_phase = 'text'
        self._npc_selected_option = None
        self._npc_outcome_text = ''
        self._npc_item_list = []
        self._npc_item_scroll = 0
        self._npc_is_flavor = True  # flag to skip karma processing
        self.state = STATE_NPC_ENCOUNTER
        return True

    def _start_npc_encounter(self, monster):
        """Begin a moral encounter when the player bumps an NPC."""
        tag = getattr(monster, '_npc_encounter_tag', None)
        if tag is None:
            return False

        # Find the encounter definition
        enc = None
        for lvl_enc in self._npc_encounter_levels.values():
            if lvl_enc['tag'] == tag:
                enc = lvl_enc
                break
        if enc is None:
            return False

        self._npc_encounter_active = enc
        self._npc_encounter_monster = monster
        self._npc_encounter_phase = 'text'
        self._npc_selected_option = None
        self._npc_outcome_text = ''
        self._npc_item_list = []
        self._npc_item_scroll = 0
        self.state = STATE_NPC_ENCOUNTER
        return True

    def _get_filtered_inventory(self, filter_type: str) -> list:
        """Return inventory items matching the cost filter type."""
        from items import Food, Ingredient, Potion, Scroll, Weapon, Wand
        inv = self.player.inventory
        if filter_type == 'food':
            return [i for i in inv if isinstance(i, (Food, Ingredient))]
        if filter_type == 'healing_potion':
            items = []
            # Healing potions
            items.extend(i for i in inv if isinstance(i, Potion)
                         and getattr(i, 'effect', '') in ('heal', 'extra_heal', 'full_heal'))
            # Healing scrolls
            items.extend(i for i in inv if isinstance(i, Scroll)
                         and 'heal' in getattr(i, 'effect', '').lower())
            # Healing wands with charges
            items.extend(i for i in inv if isinstance(i, Wand)
                         and 'heal' in getattr(i, 'effect', '').lower()
                         and getattr(i, 'charges', 0) > 0)
            # Heal spell (virtual entry — show as a selectable option)
            if 'heal_spell' in getattr(self.player, 'known_spells', {}):
                mp_cost = self.player.known_spells.get('heal_spell', 99)
                if self.player.mp >= mp_cost:
                    # Create a placeholder for the spell choice
                    class _SpellChoice:
                        name = f'Cast Heal ({mp_cost} MP)'
                        id = '_heal_spell_choice'
                        item_class = 'spell'
                    items.append(_SpellChoice())
            return items
        if filter_type == 'potion':
            return [i for i in inv if isinstance(i, Potion)]
        if filter_type == 'scroll':
            return [i for i in inv if isinstance(i, Scroll)]
        if filter_type == 'weapon':
            return [i for i in inv if isinstance(i, Weapon)]
        return []

    def _apply_npc_choice(self, opt: dict, selected_item=None):
        """Apply the cost, reward, and karma for the chosen option."""
        cost = opt.get('cost')
        reward = opt.get('reward')
        karma_delta = opt.get('karma', 0)  # flavor encounters have no karma

        # ── Apply cost ────────────────────────────────────────────
        if cost:
            ctype = cost['type']
            if ctype in ('food', 'healing_potion', 'potion', 'scroll', 'weapon'):
                if selected_item:
                    if getattr(selected_item, 'id', '') == '_heal_spell_choice':
                        # Spell: spend MP instead of removing an item
                        mp_cost = self.player.known_spells.get('heal_spell', 8)
                        self.player.mp -= mp_cost
                        self.add_message(f"You cast Heal. (-{mp_cost} MP)", 'info')
                    elif hasattr(selected_item, 'charges'):
                        # Wand: spend a charge
                        from items import Wand
                        if isinstance(selected_item, Wand):
                            selected_item.charges -= 1
                            self.add_message(
                                f"You use the {selected_item.name}. ({selected_item.charges} charges left)", 'info')
                            if selected_item.charges <= 0:
                                self.player.remove_from_inventory(selected_item)
                        else:
                            self.player.remove_from_inventory(selected_item)
                    else:
                        self.player.remove_from_inventory(selected_item)
            elif ctype == 'gold':
                self.player_gold -= cost['amount']
            elif ctype == 'hp_percent':
                loss = max(5, int(self.player.hp * cost['amount'] / 100))
                self.player.hp -= loss
            elif ctype == 'max_hp':
                self.player.max_hp -= cost['amount']
                self.player.hp = min(self.player.hp, self.player.max_hp)
            elif ctype == 'sp':
                self.player.sp = max(0, self.player.sp - cost['amount'])
            elif ctype == 'hp':
                self.player.hp = max(1, self.player.hp - cost['amount'])
            elif ctype == 'mp':
                self.player.mp = max(0, self.player.mp - cost['amount'])
            elif ctype == 'random_item':
                # Cost is an item from a category (e.g., scroll sacrifice)
                from items import Scroll, Potion, Food, Weapon
                cat = cost.get('category', 'scroll')
                cat_map = {'scroll': Scroll, 'potion': Potion, 'food': Food, 'weapon': Weapon}
                cls = cat_map.get(cat)
                if cls and selected_item and isinstance(selected_item, cls):
                    self.player.remove_from_inventory(selected_item)
                elif cls:
                    item = next((i for i in self.player.inventory if isinstance(i, cls)), None)
                    if item:
                        self.player.remove_from_inventory(item)
            elif ctype == 'triggered_item':
                # Remove the trigger item from inventory OR equipment slots
                enc = self._npc_encounter_active
                item_id = enc.get('trigger_item', '')
                removed = False
                # Check inventory first
                for it in self.player.inventory:
                    if getattr(it, 'id', '') == item_id:
                        self.player.remove_from_inventory(it)
                        removed = True
                        break
                # Check equipment slots if not found in inventory
                if not removed:
                    p = self.player
                    if p.weapon and getattr(p.weapon, 'id', '') == item_id:
                        p.weapon = None
                        removed = True
                    elif p.shield and getattr(p.shield, 'id', '') == item_id:
                        p.shield = None
                        removed = True
                    elif p.amulet_slot and getattr(p.amulet_slot, 'id', '') == item_id:
                        # Reverse accessory stat bonuses
                        fx = p.amulet_slot.effects
                        if 'stat' in fx:
                            p.apply_stat_bonus(fx['stat'], -fx.get('amount', 0))
                        if 'stat2' in fx:
                            p.apply_stat_bonus(fx['stat2'], -fx.get('amount2', 0))
                        if 'status' in fx:
                            p.status_effects.pop(fx['status'], None)
                        p.amulet_slot = None
                        removed = True
                    else:
                        for i, slot in enumerate(p.accessory_slots):
                            if slot and getattr(slot, 'id', '') == item_id:
                                fx = slot.effects
                                if 'stat' in fx:
                                    p.apply_stat_bonus(fx['stat'], -fx.get('amount', 0))
                                if 'stat2' in fx:
                                    p.apply_stat_bonus(fx['stat2'], -fx.get('amount2', 0))
                                if 'status' in fx:
                                    p.status_effects.pop(fx['status'], None)
                                p.accessory_slots[i] = None
                                removed = True
                                break
            elif ctype == 'accept_item':
                # Give the player a burden/cursed item
                self._grant_burden_item(cost['item_id'])
            elif ctype == 'spawn_deadite_ambush':
                # Free hit: 10% HP, then spawn a hostile Deadite
                loss = max(5, int(self.player.hp * 10 / 100))
                self.player.hp -= loss
                self.add_message(f"The Deadite rakes you for {loss} damage!", 'danger')
                self._spawn_npc_deadite()

        # ── Apply reward ──────────────────────────────────────────
        if reward:
            self._apply_npc_reward(reward)
            # Chain-equip passive: suryas_gift (Kavacha-Kundala). Good-karma
            # rewards are doubled — apply the reward a second time when karma
            # delta was positive.
            try:
                from chain_passives import player_has_passive
                if karma_delta > 0 and player_has_passive(self.player, 'suryas_gift'):
                    self._apply_npc_reward(reward)
                    self.add_message(
                        "Surya's gift doubles the bounty of your good deed!", 'success')
            except ImportError:
                pass
        # Bonus reward (e.g., Cowering Goblin gives two items)
        bonus = opt.get('bonus_reward')
        if bonus:
            self._apply_npc_reward(bonus)

        # ── Apply karma ───────────────────────────────────────────
        old_karma = self.karma
        self.karma = max(-10, min(10, self.karma + karma_delta))
        if self.karma == 10 and old_karma < 10:
            self._log_chronicle("I feel... clean. Like everything I've done down here has mattered. The dungeon feels lighter.")
        elif self.karma == -10 and old_karma > -10:
            self._log_chronicle("Something inside me has gone cold. The dungeon doesn't frighten me anymore. That frightens me.")

        # Show outcome
        self._npc_outcome_text = opt['outcome']
        self._npc_encounter_phase = 'outcome'

    def _apply_npc_reward(self, reward: dict):
        """Grant a reward from an NPC encounter choice."""
        rtype = reward['type']

        if rtype == 'gold':
            if 'amount' in reward:
                amount = reward['amount']
            else:
                amount = random.randint(reward['min'], reward['max'])
            self.player_gold += amount
            self.add_message(f"+{amount} gold!", 'loot')

        elif rtype in ('random_weapon', 'random_armor', 'random_shield',
                        'random_accessory', 'random_potion', 'random_scroll',
                        'random_food', 'random_wand'):
            count = reward.get('count', 1)
            for _ in range(count):
                item = self._generate_npc_reward_item(rtype)
                if item:
                    self.player.inventory.append(item)
                    self.add_message(f"Received: {self._display_name(item)}", 'loot')

        elif rtype == 'stat':
            stat = reward['stat']
            amount = reward['amount']
            self.player.apply_stat_bonus(stat, amount)
            self.add_message(f"+{amount} {stat}!", 'success')

        elif rtype == 'specific_item':
            item = self._create_specific_npc_item(
                reward['item_type'], reward['item_id'],
                no_auto_identify=reward.get('no_auto_identify', False))
            if item:
                self.player.inventory.append(item)
                self.add_message(f"Received: {self._display_name(item)}", 'loot')

        elif rtype == 'random_item':
            # Flavor encounter reward: random item by category name
            cat = reward.get('category', 'potion')
            item = self._generate_npc_reward_item(f'random_{cat}')
            if item:
                item.identified = True
                self.player.inventory.append(item)
                self.add_message(f"Received: {self._display_name(item)}", 'loot')

        elif rtype == 'effect':
            eff = reward['effect']
            dur = reward.get('duration', 20)
            self.player.add_effect(eff, dur)
            eff_name = eff.replace('_', ' ').title()
            self.add_message(f"{eff_name} for {dur} turns!", 'success')

        elif rtype == 'hp_restore':
            self.player.restore_hp(reward['amount'])
            self.add_message(f"+{reward['amount']} HP!", 'success')

        elif rtype == 'sp_restore':
            self.player.sp = min(self.player.max_sp, self.player.sp + reward['amount'])
            self.add_message(f"+{reward['amount']} SP!", 'success')

        elif rtype == 'mp_restore':
            self.player.restore_mp(reward['amount'])
            self.add_message(f"+{reward['amount']} MP!", 'success')

        elif rtype == 'enchant_weapon':
            w = self.player.weapon
            if w:
                w.enchant_bonus += reward.get('amount', 1)
                self.add_message(f"{w.name} is now +{w.enchant_bonus}!", 'success')
            else:
                self.add_message("You have no weapon equipped to enchant.", 'warning')

        elif rtype == 'message':
            pass  # No mechanical reward, just the outcome text

        elif rtype == 'multi':
            for sub_reward in reward['rewards']:
                self._apply_npc_reward(sub_reward)

    def _generate_npc_reward_item(self, rtype: str):
        """Generate a random item of the given reward type at current level."""
        from items import load_items, copy_at
        type_map = {
            'random_weapon': 'weapon',
            'random_armor': 'armor',
            'random_shield': 'shield',
            'random_accessory': 'accessory',
            'random_potion': 'potion',
            'random_scroll': 'scroll',
            'random_food': 'food',
            'random_wand': 'wand',
        }
        cls_name = type_map.get(rtype)
        if not cls_name:
            return None
        try:
            candidates = []
            for item in load_items(cls_name):
                ml = getattr(item, 'min_level', 1)
                if ml <= self.dungeon_level and ml < 9999:
                    candidates.append(item)
            if candidates:
                template = random.choice(candidates)
                result = copy_at(template, self.player.x, self.player.y)
                result.identified = True
                return result
        except Exception:
            pass
        return None

    def _create_specific_npc_item(self, item_type: str, item_id: str,
                                   no_auto_identify: bool = False):
        """Create a specific named item for an NPC reward."""
        from items import load_items, copy_at
        try:
            for item in load_items(item_type):
                if item.id == item_id:
                    result = copy_at(item, self.player.x, self.player.y)
                    if not no_auto_identify:
                        result.identified = True
                    return result
        except Exception:
            pass
        return None

    def _grant_burden_item(self, item_id: str):
        """Grant a cursed/burden item to the player (lodestone, dispatch, etc.)."""
        from items import load_items, copy_at
        try:
            for item in load_items('artifact'):
                if item.id == item_id:
                    result = copy_at(item, self.player.x, self.player.y)
                    result.identified = True
                    self.player.inventory.append(result)
                    return
        except Exception:
            pass

    def _close_npc_encounter(self, resolved: bool):
        """Close the NPC encounter overlay."""
        if resolved:
            # Remove the NPC
            npc = self._npc_encounter_monster
            if npc:
                npc.alive = False
                npc.hp = 0
            enc = self._npc_encounter_active
            if enc:
                if getattr(self, '_npc_is_flavor', False):
                    encountered = getattr(self, '_encountered_flavor_npcs', set())
                    encountered.add(enc['tag'])
                else:
                    self._encountered_npcs.add(enc['tag'])
                # Log to chronicle
                name = enc.get('name', 'someone')
                import random as _chr_rng
                if getattr(self, '_npc_is_flavor', False):
                    _FLAVOR_VERBS = [
                        "Ran into {name}. A brief exchange in the dark.",
                        "Met {name}. Even down here, people find a way.",
                        "Crossed paths with {name}. The dungeon is stranger than I thought.",
                    ]
                    self._log_chronicle(_chr_rng.choice(_FLAVOR_VERBS).format(name=name))
                else:
                    _NPC_VERBS = [
                        "Met {name}. Had to make a hard choice.",
                        "Encountered {name}. Did what I thought was right.",
                        "Came across {name}. This dungeon tests more than combat skill.",
                        "Found {name}. Every choice down here has weight.",
                        "{name} needed something from me. I gave my answer.",
                    ]
                    self._log_chronicle(_chr_rng.choice(_NPC_VERBS).format(name=name))

        self._npc_encounter_active = None
        self._npc_encounter_monster = None
        self._npc_encounter_phase = 'text'
        self._npc_selected_option = None
        self._npc_outcome_text = ''
        self._npc_item_list = []
        self._npc_is_flavor = False
        self.state = STATE_PLAYER
        if resolved:
            self._advance_turn()

    # ------------------------------------------------------------------
    # Altar of the Last Judgment  (L99)
    # ------------------------------------------------------------------

    def _resolve_judgment(self):
        """Resolve the Altar of the Last Judgment on L99."""
        from npc_encounters import judge_karma
        outcome, text = judge_karma(self.karma)

        self._judgment_text = text
        self.state = STATE_JUDGMENT

        if outcome == 'sword_and_scales':
            # Grant both Sword and Scales of Michael + Paladin title
            self.player_title = 'Paladin'
            from items import load_items, copy_at
            px, py = self.player.x, self.player.y
            try:
                weapons = load_items('weapon')
                sword = next((w for w in weapons if w.id == 'sword_of_michael'), None)
                if sword:
                    sw = copy_at(sword, px, py)
                    sw.identified = True
                    self.player.inventory.append(sw)
                    self.add_message("The Sword of Michael materializes in your hands!", 'success')
            except Exception:
                pass
            try:
                artifacts = load_items('artifact')
                scales = next((a for a in artifacts if a.id == 'scales_of_michael'), None)
                if scales:
                    sc = copy_at(scales, px, py)
                    sc.identified = True
                    self.player.inventory.append(sc)
                    self.add_message("The Scales of Michael float into your grasp!", 'success')
            except Exception:
                pass
            self._log_chronicle("Stood before the altar of judgment. The scales weighed my soul. I was found worthy. A sword of white fire and the scales themselves were given to me. I've never felt so terrified.")

        elif outcome == 'scales_granted':
            from items import load_items, copy_at
            px, py = self.player.x, self.player.y
            try:
                artifacts = load_items('artifact')
                scales = next((a for a in artifacts if a.id == 'scales_of_michael'), None)
                if scales:
                    sc = copy_at(scales, px, py)
                    sc.identified = True
                    self.player.inventory.append(sc)
                    self.add_message("The Scales of Michael float into your grasp!", 'success')
            except Exception:
                pass
            self._log_chronicle("The altar weighed my deeds. Not perfect, but enough. The Scales of Michael settled into my hands. They hum with a quiet judgment.")

        elif outcome == 'abaddon_empowered':
            # Abaddon gets 50% more HP and extra attack
            self.add_message("A dark power surges into the depths below...", 'danger')
            # Store flag for when L100 is generated
            self._abaddon_empowered = True
            self._log_chronicle("The altar judged me. I was found wanting. Something below grew stronger. I can feel it.")

        elif outcome == 'locusts_strengthened':
            # Larger locust swarms
            self.add_message("The buzzing of locusts grows louder in the deep...", 'danger')
            self._locusts_strengthened = True
            self._log_chronicle("The judgment went poorly. The buzzing from below is louder now. I made things worse.")
