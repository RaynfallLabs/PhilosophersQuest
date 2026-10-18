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
from geom import monster_at_tile


_NAME_TITLES = frozenset({'sir', 'brother', 'sister', 'saint', 'father', 'mother', 'prince',
                          'princess', 'king', 'queen', 'lady', 'lord', 'captain', 'corporal',
                          'sergeant', 'old', 'the', 'of', 'young', 'master', 'mistress',
                          'doctor', 'squire', 'ser'})


def _names_in(name, text) -> bool:
    """Does ``text`` say this person's name: the whole name, or one of its
    own words (not a title such as "Sir" or "Brother")? (JNL-04)"""
    import re
    name, text = str(name or ''), str(text or '')
    if not name or not text:
        return False
    if name.lower() in text.lower():
        return True
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]+", name)
             if len(w) >= 3 and w.lower() not in _NAME_TITLES]
    return any(re.search(r'\b' + re.escape(w) + r'\b', text) for w in words)


def _fate_from_deeds(entries, pid: str):
    """'saved' / 'lost' / 'spared' when an outcome's deeds record that fate
    for the person ``pid`` (the last such deed wins), else None."""
    fate = None
    for e in entries or ():
        did = e if isinstance(e, str) else (e.get('id') if isinstance(e, dict) else None)
        if not isinstance(did, str):
            continue
        for k in ('saved', 'lost', 'spared'):
            if did == f'{k}.{pid}':
                fate = k
    return fate


def _system_placed_tags() -> set:
    """Encounters a system seats itself (Setne's tomb), callback_only only so
    the Road never rolls them."""
    try:
        import setne_tomb
        return {setne_tomb.data().get('encounter', '')} - {''}
    except Exception:
        return set()


class EncountersMixin:
    def _free_spawn_tile(self, occupied):
        """A free floor tile the hero can walk to, outside the arrival room:
        the fallback for every encounter spawner when the rooms it sampled
        are full. On a maze floor the only other room is often packed with
        monsters, and the cow, the unicorn, the carrot or an NPC was lost
        for the run."""
        import random as _rng
        from dungeon import FLOOR
        d = self.dungeon
        start = d.rooms[0] if d.rooms else None
        reach = self._reachable_tiles(self.player.x, self.player.y)
        spots = [t for t in reach
                 if d.in_bounds(*t) and d.tiles[t[1]][t[0]] == FLOOR
                 and t not in occupied
                 and t != (self.player.x, self.player.y)
                 and not (start is not None and start.x <= t[0] < start.x + start.width
                          and start.y <= t[1] < start.y + start.height)]
        return _rng.choice(sorted(spots)) if spots else None

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
            'name': 'Cow',
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
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(self.monsters)
        occupied |= self._occupants()
        for room in _rng.sample(rooms, min(len(rooms), 5)):
            for tx, ty in room.inner_tiles():
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    cow = Monster(cow_def, tx, ty)
                    cow._npc_encounter_tag = '_cow_dialog'
                    self.monsters.append(cow)
                    self._cow_npc = cow
                    self._cow_spawned = True
                    return
        spot = self._free_spawn_tile(occupied)
        if spot is not None:
            cow = Monster(cow_def, *spot)
            cow._npc_encounter_tag = '_cow_dialog'
            self.monsters.append(cow)
            self._cow_npc = cow
            self._cow_spawned = True

    def _start_cow_encounter(self, cow_monster):
        """Open the cow dialog when player bumps the cow NPC."""
        if getattr(self, '_cow_level_done', False):
            # The farm is finished (a save from before the cow was removed
            # on return could still hold her): she wanders off for good.
            try:
                cow_monster.alive = False
                self.monsters.remove(cow_monster)
            except (ValueError, AttributeError):
                pass
            self.add_message("The cow gives you a long look and wanders off.", 'info')
            return
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
        self._chron('milestone', "I poked a cow one time too many and the floor opened. Now I am in some kind of cow dimension. None of my books covered this.",
                    once='cow_level')
        self._cow_return_level = self.dungeon_level
        # Remove the cow from the current level
        if self._cow_npc and self._cow_npc in self.monsters:
            self.monsters.remove(self._cow_npc)
        self._cow_npc = None
        # After a save and reload the reference above is gone, so find her
        # by her tag as well: she used to stay behind and could be poked
        # into the finished farm again.
        self.monsters[:] = [m for m in self.monsters
                            if getattr(m, '_npc_encounter_tag', None) != '_cow_dialog']
        self.state = STATE_PLAYER
        try:
            self._change_level(COW_LEVEL, enter_from_top=True, via='cow')
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
            self._change_level(self._cow_return_level, enter_from_top=False, via='cow')
        except Exception as e:
            self.add_message(f"Error exiting cow level: {e}", 'danger')
            import traceback
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Karma + flavor NPC spawn
    # ------------------------------------------------------------------

    def _encounter_allowed(self, enc) -> bool:
        """An encounter's own requires / forbids (deeds, oaths, stats) hold
        now. Content without either is always allowed."""
        if not (enc.get('requires') or enc.get('forbids')):
            return True
        from encounter_schema import encounter_allowed
        return encounter_allowed(enc, self._deed_ctx())

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
        if not self._encounter_allowed(enc):
            return
        self._spawn_encounter_npc(enc, '_npc_encounter_tag', level)

    def _maybe_spawn_flavor_npc(self, level: int):
        """Spawn a story or flavor NPC on this level if one is assigned (the
        Road fills ``_flavor_encounter_levels`` as slots bind). Light ones
        never touch karma; medium and high ones may offer a gated point."""
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
        if not self._encounter_allowed(enc):
            return
        self._spawn_encounter_npc(enc, '_flavor_encounter_tag', level)

    def _spawn_encounter_npc(self, enc: dict, tag_attr: str, level: int):
        """Place an encounter NPC: anchors, flavor encounters, callbacks and
        Road slots all come through here (DEEDS_KARMA_DESIGN 6.4). It stands
        in a room other than the arrival room, or on any free tile the hero
        can walk to; ``_settle_monsters`` (which runs after the spawners)
        brings it within four-way reach if a pool or lava cut it off, since
        ``_needed_to_finish`` counts encounter NPCs. ``tag_attr`` is
        ``_npc_encounter_tag`` or ``_flavor_encounter_tag``, which the bump
        dispatch reads. Returns the NPC or None."""
        from monster import Monster
        # A fake "monster" for the NPC so it renders and blocks tiles
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
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(self.monsters)
        occupied |= self._occupants()
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
        import random as _rng

        def _make(x, y):
            npc = Monster(npc_def, x, y)
            setattr(npc, tag_attr, enc['tag'])
            if tag_attr == '_flavor_encounter_tag':
                npc.proper_noun = bool(enc.get('proper_noun'))   # a person's name
            self.monsters.append(npc)
            return npc

        for room in _rng.sample(rooms, min(len(rooms), 5)):
            tiles = list(room.inner_tiles())
            _rng.shuffle(tiles)
            for tx, ty in tiles:
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    return _make(tx, ty)
        spot = self._free_spawn_tile(occupied)
        if spot is not None:
            return _make(*spot)
        return None

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
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(self.monsters)
        occupied |= self._occupants()
        for room in _rng.sample(rooms, min(len(rooms), 5)):
            tiles = list(room.inner_tiles())
            _rng.shuffle(tiles)
            for tx, ty in tiles:
                if self.dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    carrot.x, carrot.y = tx, ty
                    self.ground_items.append(carrot)
                    self._magic_carrot_spawned = True
                    return
        spot = self._free_spawn_tile(occupied)
        if spot is not None:
            carrot.x, carrot.y = spot
            self.ground_items.append(carrot)
            self._magic_carrot_spawned = True

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
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(self.monsters)
        occupied |= self._occupants()
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
        spot = self._free_spawn_tile(occupied)
        if spot is not None:
            npc = Monster(npc_def, *spot)
            npc._is_unicorn = True
            npc._unicorn_state = 'wary'
            npc._unicorn_wait = 0
            npc._unicorn_eat_turns = 0
            self.monsters.append(npc)
            self._unicorn_spawned = True

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
                if monster_at_tile(self.monsters, nx, ny) is not None:
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
                    # Move unicorn to the carrot, or beside it: a carrot
                    # dropped at the hero's feet put her on his tile.
                    m._unicorn_carrot_pos = (carrot.x, carrot.y)
                    if (carrot.x, carrot.y) != (self.player.x, self.player.y):
                        m.x, m.y = carrot.x, carrot.y
                    elif max(abs(m.x - carrot.x), abs(m.y - carrot.y)) > 1:
                        from geom import all_occupied_tiles
                        _busy = set(all_occupied_tiles(self.monsters, exclude=m))
                        _busy.add((self.player.x, self.player.y))
                        _near = [(carrot.x + ax, carrot.y + ay)
                                 for ax in (-1, 0, 1) for ay in (-1, 0, 1)
                                 if (ax, ay) != (0, 0)]
                        _near = [t for t in _near if self.dungeon.is_walkable(*t) and t not in _busy]
                        if _near:
                            m.x, m.y = min(_near, key=lambda t: max(abs(t[0] - m.x), abs(t[1] - m.y)))
                    self.add_message(
                        "The unicorn's ears perk up! She approaches the Magic Dungeon "
                        "Carrot and begins to eat.", 'success')

            elif state == 'eating':
                m._unicorn_eat_turns += 1
                if m._unicorn_eat_turns >= 2:
                    # Remove the carrot from ground
                    _cpos = getattr(m, '_unicorn_carrot_pos', None) or (m.x, m.y)
                    self.ground_items = [
                        gi for gi in self.ground_items
                        if not (getattr(gi, 'id', '') == 'magic_dungeon_carrot'
                                and (gi.x, gi.y) == tuple(_cpos))]
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
            # Phase 1 of CHAIN_EFFECTS_PLAN (2026-10-03): the Unicorn
            # full-screen "THE UNICORN KNEELS" takeover is a named
            # effect on the EffectsRuntime now. Fire it on any boon-
            # earning score (chain >= 1 is the first boon rung).
            if chain >= 1:
                rt = getattr(self, 'effects_runtime', None)
                if rt is not None:
                    rt.fire('unicorn_bond_takeover', {})
            self._apply_unicorn_boons(chain, unicorn)

        # Unicorn-bond takeover is driven by effects_runtime.fire()
        # in on_complete above -- no more QuizEngine.celebrating hold
        # (Phase 1, CHAIN_EFFECTS_PLAN.md, 2026-10-03).
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
        self.add_message("The unicorn's horn glows — warm healing energy fills you! (Regenerating, 30 turns)", 'success')

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
            self._chron('notice', "She stayed. The unicorn bowed her head and something passed between us. I can feel her at the edge of my thoughts now.")
            return

        # If chain < 5, unicorn departs after granting boons
        unicorn.alive = False
        unicorn._unicorn_state = 'fled'
        self.add_message("The unicorn dips her head in farewell and vanishes in a shimmer of light.", 'info')
        self._chron('notice', "The unicorn touched her horn to my hand and warmth flooded through me. Then she was gone like morning fog. I feel different.")

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
        if enc is not None and enc.get('tag') != tag:
            # The floor's own encounter belongs to another figure (the Road
            # bound a slot on the tomb's floor): never open the wrong scene.
            enc = None
        if enc is None:
            # A figure a system placed itself (Setne's tomb): its scene is in
            # the encounter data by tag, not in this run's floor views.
            from game_road import _encounter_by_tag
            _src, found = _encounter_by_tag(tag)
            if found is not None:
                import economy
                enc = economy.price_encounter(found)
        if enc is None:
            return False
        if self._npc_already_spent(enc, monster, flavor=True):
            return True

        # Reuse the NPC encounter UI with a flavor flag
        self._npc_open(enc, monster, flavor=True)
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
        if self._npc_already_spent(enc, monster, flavor=False):
            return True

        self._npc_open(enc, monster, flavor=False)
        return True

    def _hostile_encounter_arrives(self):
        """An encounter marked ``hostile`` (C19: the dead come for a book
        owed) opens as the hero arrives on its floor: its figure steps up to
        the nearest free tile the hero can walk to, and the scene begins.
        It has no walk-away option; Esc does not end it before a choice."""
        if self.state != STATE_PLAYER:
            return
        m = self._hostile_figure_here()
        if m is not None:
            px, py = self.player.x, self.player.y
            from geom import all_occupied_tiles
            busy = set(all_occupied_tiles(self.monsters)) | self._occupants()
            near = sorted((t for t in self._reachable_tiles(px, py)
                           if t not in busy and t != (px, py) and self.dungeon.is_walkable(*t)),
                          key=lambda t: (max(abs(t[0] - px), abs(t[1] - py)),
                                         abs(t[0] - px) + abs(t[1] - py), t))
            if near:
                m.x, m.y = near[0]
            if getattr(m, '_flavor_encounter_tag', None):
                self._start_flavor_encounter(m)
            else:
                self._start_npc_encounter(m)
            return

    def _hostile_figure_here(self):
        """The live figure of a ``hostile`` encounter on this floor, or None."""
        for m in self.monsters:
            ftag = getattr(m, '_flavor_encounter_tag', None)
            tag = ftag or getattr(m, '_npc_encounter_tag', None)
            if not tag or not m.alive:
                continue
            levels = (getattr(self, '_flavor_encounter_levels', None) if ftag
                      else getattr(self, '_npc_encounter_levels', None)) or {}
            if any((e or {}).get('tag') == tag and e.get('hostile') for e in levels.values()):
                return m
        return None

    def _npc_already_spent(self, enc, monster, *, flavor: bool) -> bool:
        """An encounter is spent the moment its choice is made (the cost is
        paid or its quiz starts). If the NPC is still standing after that, as
        it is when the game was closed on the outcome page or mid-quiz and
        reloaded, it has nothing more to say and leaves: a reload is not a
        second choice."""
        spent = (getattr(self, '_encountered_flavor_npcs', None) or set()) if flavor \
            else (getattr(self, '_encountered_npcs', None) or set())
        if enc.get('tag') not in spent:
            return False
        if self._npc_reopenable(enc):
            # A save from before ENG-03 marked a 'then: options' encounter
            # spent at its first talk-only step: it still has real choices.
            spent.discard(enc.get('tag'))
            return False
        from monster import the_name as _the_name
        monster.alive = False
        monster.hp = 0
        self.add_message(f"{_the_name(monster)} has nothing more to say, and goes.", 'info')
        return True

    @staticmethod
    def _npc_talk_only(opt) -> bool:
        """A 'then: options' step that commits to nothing (ENG-03): an
        option without a quiz whose outcome returns to the list, or a quiz
        option every branch of which does. Choosing one does not spend the
        encounter; a closing choice, or leaving after a step, does."""
        from encounter_schema import is_quiz
        if not isinstance(opt, dict):
            return False
        if not is_quiz(opt):
            return opt.get('then') == 'options'
        branches = [opt.get('pass'), opt.get('fail')] + list((opt.get('fail_by_correct') or {}).values())
        branches = [b for b in branches if isinstance(b, dict)]
        return bool(branches) and all(b.get('then') == 'options' for b in branches)

    def _npc_reopenable(self, enc) -> bool:
        """Every choice made in this encounter so far was a talk-only step,
        and options are left to choose from."""
        tag = (enc or {}).get('tag')
        reg = self._deeds_reg()
        picked = list((reg.get('chosen') or {}).get(tag) or ())
        opts = (enc or {}).get('options') or []
        if not picked or not all(isinstance(i, int) and 0 <= i < len(opts)
                                 and self._npc_talk_only(opts[i]) for i in picked):
            return False
        from encounter_schema import visible_options
        used = list(reg['used_options'].get(tag, []))
        for i in picked:            # a step whose page was never closed
            if i not in used:
                used.append(i)
        reg['used_options'][tag] = used
        return bool(visible_options(enc, self._deed_ctx(), used))

    def _npc_open(self, enc, monster, *, flavor: bool):
        """Open the encounter screen on its text page (or, for a 'then:
        options' encounter already part-way through, on its options)."""
        self._npc_encounter_active = enc
        self._npc_encounter_monster = monster
        self._npc_encounter_phase = 'text'
        self._npc_selected_option = None
        self._npc_selected_index = None
        self._npc_outcome_text = ''
        self._npc_outcome_chronicle = None
        self._npc_item_list = []
        self._npc_item_scroll = 0
        self._npc_visible = None
        self._npc_after = 'close'
        self._npc_pending_option = None
        if flavor:
            self._npc_is_flavor = True  # flag to skip karma processing
        # Deeds-aware scene text (text_variants) and the first meeting.
        from encounter_schema import resolve_text
        ctx = self._deed_ctx()
        self._npc_encounter_text = resolve_text(enc, ctx)
        person = enc.get('person')
        if isinstance(person, dict) and person.get('id'):
            import deeds
            floor, _deepest, _block, _turn = self._deed_where()
            # The People page shows the encounter's title ("Courteous
            # Giant") until the hero hears the name (JNL-04).
            deeds.set_person(self._deeds_reg(), person['id'],
                             name=person.get('name', ''), floor=floor,
                             title=enc.get('name', ''),
                             known=_names_in(person.get('name', ''), self._npc_encounter_text))
            if enc.get('chronicle_meet'):
                import chronicle
                chronicle.chron(self, 'person', enc['chronicle_meet'],
                                person=person['id'], once=f"meet:{enc['tag']}")
        self.state = STATE_NPC_ENCOUNTER
        if self._deeds_reg()['used_options'].get(enc.get('tag')):
            self._npc_show_options()

    # ------------------------------------------------------------------
    # Deeds helpers (thin wrappers over the pure deeds / karma modules)
    # ------------------------------------------------------------------

    def _deeds_reg(self) -> dict:
        import deeds
        return deeds.ensure_register(self)

    def _deed_where(self):
        """(floor, deepest, block, turn): the block is always the deepest
        floor's, so walking back upstairs never reopens an old block."""
        import karma
        return karma._where(self)

    def _deed_ctx(self) -> dict:
        """The context a deeds condition is checked against."""
        floor, deepest, _block, _turn = self._deed_where()
        p = self.player
        stats = {}
        for st in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'):
            try:
                stats[st] = int(getattr(p, st, 0) or 0)
            except (TypeError, ValueError):
                stats[st] = 0
        from game_divine import _iter_equipped
        worn = {getattr(i, 'id', None) for i in _iter_equipped(p)}
        items = {getattr(i, 'id', None) for i in list(getattr(p, 'inventory', []) or [])} | worn
        items.discard(None)
        worn.discard(None)
        return {'reg': self._deeds_reg(), 'karma': int(getattr(self, 'karma', 0) or 0),
                'stats': stats, 'floor': floor, 'deepest': deepest, 'items': items,
                'worn': worn}

    def _record_deeds(self, entries, source: str):
        """Record an outcome's ``deeds`` list (ids, or {id, tags, payload,
        ttl_floors, unique}). Data may never place a virtue:* tag."""
        import deeds
        reg = self._deeds_reg()
        floor, deepest, block, turn = self._deed_where()
        for e in entries or ():
            if isinstance(e, str):
                deeds.record(reg, e, floor=floor, block=block, turn=turn, source=source,
                             deepest=deepest)
            elif isinstance(e, dict) and e.get('id'):
                deeds.record(reg, e['id'], floor=floor, block=block, turn=turn,
                             source=source, tags=e.get('tags') or (),
                             payload=e.get('payload'), ttl_floors=e.get('ttl_floors'),
                             unique=bool(e.get('unique')), deepest=deepest)

    def _engine_virtue(self, virtue: str, source: str):
        """Write an engine-only virtue tag (virtue:forgo / judged / steadfast)."""
        import deeds
        reg = self._deeds_reg()
        floor, deepest, block, turn = self._deed_where()
        deeds.record(reg, f'flag.{virtue}.{deeds.slug(source)}', floor=floor, block=block,
                     turn=turn, source=source, tags=[f'virtue:{virtue}'], engine=True,
                     deepest=deepest)

    def _engine_vice(self, vice: str, source: str):
        """Write an engine-only vice tag (vice:reckless / vice:cruelty)."""
        import deeds
        reg = self._deeds_reg()
        floor, deepest, block, turn = self._deed_where()
        deeds.record(reg, f'flag.{vice}.{deeds.slug(source)}', floor=floor, block=block,
                     turn=turn, source=source, tags=[f'vice:{vice}'], engine=True,
                     deepest=deepest)
        import karma
        if karma.gate_enabled():
            karma.evaluate_patterns(self)

    def _npc_show_options(self):
        """Open (or reopen) the options page: which options are visible is
        decided here, once, from requires / forbids / hidden_group and the
        options already used in a 'then: options' encounter."""
        from encounter_schema import visible_options
        enc = self._npc_encounter_active or {}
        used = self._deeds_reg()['used_options'].get(enc.get('tag'), [])
        self._npc_visible = visible_options(enc, self._deed_ctx(), used)
        self._npc_encounter_phase = 'options'

    def _npc_visible_options(self) -> list:
        """[(raw index, option)] for the options page."""
        if getattr(self, '_npc_visible', None) is None:
            enc = self._npc_encounter_active or {}
            from encounter_schema import visible_options
            used = self._deeds_reg()['used_options'].get(enc.get('tag'), [])
            self._npc_visible = visible_options(enc, self._deed_ctx(), used)
        return self._npc_visible

    def _get_filtered_inventory(self, filter_type: str) -> list:
        """Return inventory items matching the cost filter type. Quest and
        story pieces and uniques are never offered (npc_encounters.offerable)."""
        from items import Food, Ingredient, Potion, Scroll, Weapon
        from npc_encounters import offerable
        inv = [i for i in self.player.inventory if offerable(i)]
        if filter_type == 'food':
            return [i for i in inv if isinstance(i, (Food, Ingredient))]
        if filter_type == 'healing_potion':
            # Only items the player KNOWS heal (identified copy or known
            # type): listing the true healers among unknowns leaked them.
            from npc_encounters import known_healer
            items = [i for i in inv if known_healer(self.player, i)]
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
        """Commit the chosen option (DEEDS_KARMA_DESIGN 6.1).

        The commit point: the cost is paid and the encounter is spent before
        anything else, so quitting on the outcome page or mid-quiz is never a
        second chance. An option without a quiz is its own outcome; an option
        with one starts the quiz, and its pass or fail branch is applied when
        the quiz ends (an exit mid-quiz settles it as a fail)."""
        from encounter_schema import is_quiz
        enc = getattr(self, '_npc_encounter_active', None) or {}
        self._npc_pay_cost(opt.get('cost'), selected_item)
        self._npc_mark_spent()
        import chronicle
        chronicle.record_choice(self._deeds_reg(), enc, getattr(self, '_npc_selected_index', None))
        if opt.get('naive'):
            # Blind help (decision 9): never negative karma, but it is what
            # 'discerning' looks for (ENG-09).
            self._engine_vice('reckless', enc.get('tag', ''))
        if is_quiz(opt):
            self._record_deeds(opt.get('deeds'), enc.get('tag', ''))
            self._npc_start_option_quiz(opt)
            return
        self._apply_outcome(opt, is_option=True)

    def _npc_mark_spent(self):
        # The encounter is spent the moment its choice is made, not when the
        # outcome page is dismissed: quitting on that page and reloading gave
        # the reward and the karma again, as often as wanted.
        _enc = getattr(self, '_npc_encounter_active', None)
        if _enc and _enc.get('tag'):
            if getattr(self, '_npc_is_flavor', False):
                if not hasattr(self, '_encountered_flavor_npcs') or self._encountered_flavor_npcs is None:
                    self._encountered_flavor_npcs = set()
                self._encountered_flavor_npcs.add(_enc['tag'])
            else:
                self._encountered_npcs.add(_enc['tag'])

    def _npc_start_option_quiz(self, opt: dict):
        """Run an option's quiz; its branch lands in _npc_quiz_done."""
        spec = opt['quiz']
        enc = getattr(self, '_npc_encounter_active', None) or {}
        subject = spec['subject']
        self._npc_pending_option = (getattr(self, '_npc_selected_index', None), opt)
        self.quiz_title = spec.get('title') or f"{str(enc.get('name', '')).upper()}  --  {subject.upper()}"
        self.state = STATE_QUIZ
        threshold = int(spec.get('threshold', 1))
        # Per-miss consequences (Setne's senet: ankles, then waist, then
        # neck): applied the moment each round is lost, not at the end.
        self._npc_per_miss_lines = []
        per_miss = opt.get('per_miss')
        on_each = None
        if isinstance(per_miss, list) and per_miss:
            def on_each(ok, _correct, wrong, _pm=per_miss):
                if not ok:
                    self._apply_per_miss(_pm, wrong)
        self.quiz_engine.start_quiz(
            mode=spec.get('mode', 'threshold'), subject=subject, tier=int(spec.get('tier', 1)),
            callback=self._npc_quiz_done,
            threshold=threshold,
            max_chain=spec.get('max_chain'),
            total_qs=int(spec.get('total_qs', threshold)),
            timed=bool(spec.get('timed', False)),
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds(subject),
            base_seconds=self.player.get_quiz_timer(subject),
            play_all=bool(spec.get('play_all', False)),
            on_each=on_each,
        )

    def _apply_per_miss(self, entries, misses: int):
        """The consequence of the ``misses``-th lost round: its text, a cost
        (any option cost type), an effect, deeds. A miss past the end of the
        list costs nothing more."""
        if misses < 1 or misses > len(entries):
            return
        e = entries[misses - 1] or {}
        enc = getattr(self, '_npc_encounter_active', None) or {}
        if e.get('text'):
            self.add_message(e['text'], 'danger')
            lines = getattr(self, '_npc_per_miss_lines', None)
            if lines is not None:
                lines.append(e['text'])
        if e.get('cost'):
            self._npc_pay_cost(e['cost'], None)
        eff = e.get('effect')
        if isinstance(eff, dict) and eff.get('effect'):
            self.player.add_effect(eff['effect'], int(eff.get('duration', 5)))
        if e.get('deeds'):
            self._record_deeds(e['deeds'], enc.get('tag', ''))

    def _npc_quiz_done(self, result):
        """An encounter quiz ended: apply its pass or fail branch."""
        from encounter_schema import has_naive_sibling, quiz_passed
        pending = getattr(self, '_npc_pending_option', None)
        self._npc_pending_option = None
        if not pending:
            return
        _idx, opt = pending
        enc = getattr(self, '_npc_encounter_active', None) or {}
        passed = quiz_passed(opt['quiz'], result)
        branch = opt.get('pass' if passed else 'fail') or {'outcome': ''}
        if not passed:
            # A fail can read differently by how many rounds were won
            # (senet: one round won, or none and the floor takes you).
            by = opt.get('fail_by_correct') or {}
            alt = by.get(str(int(getattr(result, 'correct', 0) or 0)))
            if isinstance(alt, dict):
                branch = alt
        if passed:
            tag = enc.get('tag', 'encounter')
            # Judgment counts only where the careless road was open, and
            # only on a pass (Brandon, decision 7).
            if has_naive_sibling(enc, opt):
                self._engine_virtue('judged', tag)
            # Holding firm under a hard test (decision 2): a high-stakes pass.
            if enc.get('stakes') == 'high':
                self._engine_virtue('steadfast', tag)
        self._apply_outcome(branch)
        if getattr(self, '_npc_encounter_active', None) is not None:
            self.state = STATE_NPC_ENCOUNTER

    def _apply_outcome(self, o: dict, *, is_option: bool = False):
        """Apply one outcome object: an option without a quiz, or a quiz
        option's pass or fail branch. Rewards, karma (through karma.adjust),
        virtue tags, deeds, oaths, people and threads; then the outcome page.

        With the karma gate on (shipped) karma is applied first and Surya
        doubles only an award that was actually applied. With it off this
        is the old order: reward, Surya's doubling (on a positive request),
        bonus reward, karma."""
        import karma
        enc = getattr(self, '_npc_encounter_active', None) or {}
        tag = enc.get('tag', '')
        reward = o.get('reward')
        karma_delta = int(o.get('karma', 0) or 0)  # flavor encounters mostly have none
        kind = o.get('karma_kind', karma.LEGACY)
        gate = karma.gate_enabled()

        # An extra loss authored in the outcome itself: a fail branch at high
        # stakes. (An option that is its own outcome paid its cost at commit.)
        if o.get('cost') and not is_option:
            self._npc_pay_cost(o['cost'], None)

        applied = 0
        if gate and karma_delta and kind == karma.LEGACY:
            # Untyped karma has no place once the gate is on; the validator
            # keeps it out of the data. Never a crash in play: log it, move
            # nothing.
            from game_log import log_error
            log_error(f'untyped karma {karma_delta:+d} on {tag!r} with the gate on: ignored',
                      exc_info=False)
            karma_delta = 0
        if gate and karma_delta:
            applied = karma.adjust(self, karma_delta, kind=kind, source=tag)

        # ── Apply reward ──────────────────────────────────────────
        if reward:
            self._apply_npc_reward(reward)
            # Chain-equip passive: suryas_gift (Kavacha-Kundala). Good-karma
            # rewards are doubled — apply the reward a second time when karma
            # delta was positive.
            try:
                from chain_passives import player_has_passive
                _good = applied > 0 if gate else karma_delta > 0
                if _good and player_has_passive(self.player, 'suryas_gift'):
                    self._apply_npc_reward(reward)
                    self.add_message(
                        "Surya's gift doubles the bounty of your good deed!", 'success')
            except ImportError:
                pass
        # Bonus reward (e.g., Cowering Goblin gives two items)
        bonus = o.get('bonus_reward')
        if bonus:
            self._apply_npc_reward(bonus)

        # ── Apply karma ───────────────────────────────────────────
        if not gate and karma_delta:
            applied = karma.adjust(self, karma_delta, kind=kind, source=tag)
        # (The "I feel clean" / "gone cold" lines are written by karma.adjust
        # itself, whatever moved the karma: ENG-12.)
        if kind == 'cruelty' and karma_delta < 0:
            # A cruelty applied (a negative is never absorbed by the gate):
            # what 'callous' counts (ENG-09).
            self._engine_vice('cruelty', tag)

        # The outcome's text and Journal line are read against the deeds as
        # they stood when the choice was made, not after this outcome's own
        # deeds (ENG-13: Edric's options write lost.edric and key a variant
        # on it, so a living courier always read as a dead one).
        from encounter_schema import resolve_outcome, resolve_chronicle
        _text = resolve_outcome(o, self._deed_ctx())
        _chron_line = resolve_chronicle(o, self._deed_ctx())

        self._apply_outcome_deeds(o, tag)

        # Show outcome
        self._npc_outcome_text = _text
        _miss = getattr(self, '_npc_per_miss_lines', None)
        if _miss:
            self._npc_outcome_text = ' '.join(list(_miss) + [self._npc_outcome_text]).strip()
            self._npc_per_miss_lines = []
        if o.get('people_lines'):
            _extra = self._people_lines_text(o['people_lines'])
            if _extra:
                self._npc_outcome_text = (self._npc_outcome_text + '\n\n' + _extra).strip()
        self._npc_outcome_chronicle = _chron_line
        _p = enc.get('person') if isinstance(enc.get('person'), dict) else None
        if _p and _p.get('id') and _names_in(_p.get('name', ''), self._npc_outcome_text):
            import deeds
            deeds.set_person(self._deeds_reg(), _p['id'], known=True)
        # The thread this outcome opened: its hint sits faint under the
        # deed's line in the Journal (section 7.4).
        th = o.get('thread')
        self._npc_outcome_thread = (th.get('id') if isinstance(th, dict)
                                    and not th.get('closed_line') else None)
        self._npc_after = o.get('then', 'close')
        self._npc_encounter_phase = 'outcome'
        if self._npc_after == 'options' and enc.get('tag'):
            # A step of a 'then: options' encounter (ENG-03, SAV-03): the
            # option is used up now (a reload never offers it twice), and
            # the encounter is not spent: it is spent when a closing choice
            # is made or the hero leaves it. A quit and reload reopens it on
            # its options.
            idx = getattr(self, '_npc_selected_index', None)
            used = self._deeds_reg()['used_options'].setdefault(enc['tag'], [])
            if idx is not None and idx not in used:
                used.append(idx)
            spent = (getattr(self, '_encountered_flavor_npcs', None)
                     if getattr(self, '_npc_is_flavor', False)
                     else getattr(self, '_encountered_npcs', None))
            if spent is not None:
                spent.discard(enc['tag'])

    def _people_lines_text(self, spec) -> str:
        """An outcome's ``people_lines``: ``{"table": "gate", "max": 6,
        "after": "closing line", "none": "line when nobody qualifies"}``.
        The table lives in data/gate_lines.json (encounter_schema.people_lines)."""
        import json
        from encounter_schema import people_lines
        from paths import data_path
        spec = spec if isinstance(spec, dict) else {'table': str(spec)}
        try:
            with open(data_path('data', 'gate_lines.json'), encoding='utf-8') as f:
                table = json.load(f).get(spec.get('table', 'gate')) or {}
        except (OSError, ValueError):
            return ''
        lines = people_lines(table, self._deed_ctx(), spec.get('max'))
        if not lines and spec.get('none'):
            lines = [spec['none']]
        if spec.get('after'):
            # The closing line is said whether or not anyone was told about.
            lines = lines + [spec['after']]
        return '\n'.join(lines)

    def _apply_outcome_deeds(self, o: dict, tag: str, *, person=None, chron_kind=None):
        """The deeds side of an outcome: engine virtue tags, the deeds list,
        oaths, the person's status, chronicle threads, callbacks
        (``schedule``), delayed rewards, an escort and a fight.

        ``person`` defaults to the open encounter's; ``chron_kind`` writes the
        outcome's ``chronicle`` line here as a structured entry (escort
        endings). An encounter's own line is written when its screen closes."""
        import deeds
        reg = self._deeds_reg()
        floor, deepest, block, turn = self._deed_where()
        if o.get('virtue') == 'forgo' or (o.get('karma_kind') == 'forgo'
                                          and int(o.get('karma', 0) or 0) > 0):
            self._engine_virtue('forgo', tag)
        self._record_deeds(o.get('deeds'), tag)
        # Old content carried its karma on the option itself (untyped,
        # 'legacy'). An outcome pays its karma once: while it does, swearing,
        # keeping or breaking an oath in that outcome moves no more karma.
        # The shipped content is all typed (the validator keeps 'legacy'
        # out), so this guard is inert for it.
        legacy_karma = (int(o.get('karma', 0) or 0)
                        and o.get('karma_kind', 'legacy') == 'legacy')
        oath = o.get('oath')
        if isinstance(oath, dict) and oath.get('id'):
            due = None
            span = oath.get('due_floors')
            if isinstance(span, (list, tuple)) and len(span) == 2:
                import road
                rng = road.rng_for(self._road_state()['seed'], f"oath:{oath['id']}")
                due = deepest + rng.randint(int(span[0]), int(span[1]))
            made = deeds.swear(reg, oath['id'], to=oath.get('to', ''), what=oath.get('what', ''),
                               item_id=oath.get('item_id'), due_floor=due, floor=floor,
                               block=block, turn=turn, source=tag,
                               lapse_mode=oath.get('lapse_mode', 'silent'))
            if legacy_karma and int(o.get('karma', 0) or 0) > 0:
                made['prepaid'] = True          # its point was paid when it was sworn
            for k in ('thread', 'lapse_chronicle'):
                if oath.get(k):
                    made[k] = oath[k] if k != 'thread' else (
                        oath[k].get('id') if isinstance(oath[k], dict) else oath[k])
            _oth = o.get('thread')
            if not made.get('thread') and isinstance(_oth, dict) and _oth.get('id') \
                    and not _oth.get('closed_line'):
                # The thread the swearing outcome opened is the oath's own:
                # keeping or breaking it closes it (JNL-01, Cuthbert's desk).
                made['thread'] = _oth['id']
        if o.get('oath_keep'):
            self._keep_oath(o['oath_keep'], paid_here=bool(legacy_karma))
        if o.get('oath_break'):
            # The break costs -1 betray once: an outcome that writes that
            # point itself ("oath_break" with karma -1, kind betray) has paid.
            _paid = bool(legacy_karma) or (int(o.get('karma', 0) or 0) < 0
                                           and o.get('karma_kind') == 'betray')
            self._break_oath(o['oath_break'], paid_here=_paid)
        if o.get('oath_release'):
            deeds.release_oath(reg, o['oath_release'], floor=floor, block=block, turn=turn)
        if o.get('oath_lapse'):
            # A lapse resolved in a scene (the dead come for a late book):
            # 0 karma, tag vice:lapsed, blocks 'faithful' (decision 3).
            deeds.lapse_oath(reg, o['oath_lapse'], floor=floor, block=block, turn=turn)
        if person is None:
            person = (getattr(self, '_npc_encounter_active', None) or {}).get('person')
        pid = person.get('id') if isinstance(person, dict) else None
        ps = o.get('person_status')
        if ps and pid:
            spec = ps if isinstance(ps, dict) else {'status': ps}
            deeds.set_person(reg, pid, name=person.get('name', ''),
                             status=spec.get('status'), owes=spec.get('owes'),
                             owed=spec.get('owed'), deserving=spec.get('deserving'),
                             last_line=spec.get('last_line', o.get('last_line', o.get('chronicle'))),
                             floor=floor)
        elif pid and _fate_from_deeds(o.get('deeds'), pid):
            # No person_status, but the outcome records this person's fate
            # (saved. / lost. / spared.): the People page agrees (CON-06).
            deeds.set_person(reg, pid, name=person.get('name', ''),
                             status=_fate_from_deeds(o.get('deeds'), pid),
                             last_line=o.get('last_line'), floor=floor)
        elif o.get('last_line') and pid:
            deeds.set_person(reg, pid, name=person.get('name', ''),
                             last_line=o['last_line'], floor=floor)
        # Other people the scene changes (Ahwere and Merib, long lost):
        # [{id, name, status, deserving, owes, owed, last_line}].
        for pe in o.get('people') or ():
            if isinstance(pe, dict) and pe.get('id'):
                deeds.set_person(reg, pe['id'], name=pe.get('name', ''),
                                 status=pe.get('status'), owes=pe.get('owes'),
                                 owed=pe.get('owed'), deserving=pe.get('deserving'),
                                 last_line=pe.get('last_line'), floor=floor)
        th = o.get('thread')
        if isinstance(th, dict) and th.get('id'):
            deeds.open_thread(reg, th['id'], hint=th.get('hint', ''), floor=floor)
            if th.get('closed_line'):
                # A thread that ends in the scene that starts it (the tomb
                # never found again): opened and closed with its last line.
                deeds.close_thread(reg, th['id'], line=th['closed_line'])
        if o.get('thread_close'):
            deeds.close_thread(reg, o['thread_close'])
        if o.get('schedule'):
            _sth = th.get('id') if isinstance(th, dict) and not th.get('closed_line') else None
            self._schedule_callbacks(o['schedule'], tag, thread=_sth)
        if o.get('delayed'):
            self._schedule_delayed(o['delayed'], tag)
        if o.get('escort'):
            from escort_system import resolve_spec
            enc = getattr(self, '_npc_encounter_active', None) or {}
            spec = resolve_spec(o['escort'], enc)
            if spec is not None:
                self._spawn_escort(spec, source=tag, person=person if pid else None)
        if o.get('fight'):
            self._spawn_outcome_fight(o['fight'])
        # Things that happen once the outcome page is closed, so the page the
        # player is reading does not change under them: the tomb door turns
        # to wall, the floor gives the hero up to the floor above.
        for key in ('seal_door', 'expel_up'):
            if o.get(key):
                self._npc_after_close = list(getattr(self, '_npc_after_close', None) or [])
                self._npc_after_close.append(key)
        if chron_kind and o.get('chronicle'):
            import chronicle
            chronicle.chron(self, chron_kind, o['chronicle'], person=pid)

    def _keep_oath(self, oath_id: str, *, paid_here: bool = False) -> bool:
        """Keep an open oath: deed ``kept.<id>`` (tag virtue:kept) and an
        'oath' karma award into the earliest open block slot since it was
        sworn. If an outcome carries the oath's point itself (``paid_here``)
        or the oath was ``prepaid`` when sworn, the award here is 0 so the
        point is never paid twice."""
        import deeds
        import karma
        reg = self._deeds_reg()
        floor, _deepest, block, turn = self._deed_where()
        o = reg['oaths'].get(oath_id) or {}
        if not deeds.keep_oath(reg, oath_id, floor=floor, block=block, turn=turn):
            return False
        delta = 0 if (paid_here or o.get('prepaid')) else 1
        karma.adjust(self, delta, kind='oath', source=oath_id, made_block=o.get('made_block'))
        if o.get('thread'):
            deeds.close_thread(reg, o['thread'])
        return True

    def _break_oath(self, oath_id: str, *, paid_here: bool = False) -> bool:
        import deeds
        import karma
        reg = self._deeds_reg()
        floor, _deepest, block, turn = self._deed_where()
        o = reg['oaths'].get(oath_id) or {}
        if not deeds.break_oath(reg, oath_id, floor=floor, block=block, turn=turn):
            return False
        karma.adjust(self, 0 if paid_here else -1, kind='betray', source=oath_id)
        if o.get('thread'):
            deeds.close_thread(reg, o['thread'])
        return True

    def _spawn_outcome_fight(self, spec):
        """An outcome's ``fight``: hostiles around the hero. Returns the
        list spawned.

        ``spec`` is a monster id, ``{monster_id, count}``, or a list of
        those (two ogres; Neferkaptah and six mummies). Each lands on the
        nearest free tile the hero can walk to by four-way steps (the
        reachability rule every encounter spawn follows, DEEDS 6.4), never
        on the hero, a monster, a pet or an escort."""
        from encounter_schema import fight_entries
        from monster import Monster
        from game_magic import _monster_defn
        from geom import all_occupied_tiles
        busy = set(all_occupied_tiles(self.monsters)) | self._occupants()
        px, py = self.player.x, self.player.y
        try:
            reach = self._reachable_tiles(px, py)
        except Exception:
            reach = None
        d = self.dungeon
        spots = [t for t in (reach or ())
                 if t != (px, py) and t not in busy and d.in_bounds(*t) and d.is_walkable(*t)]
        if not spots:
            # No flood (a test map, a pocket): the old ring search.
            spots = [(px + dx, py + dy) for r in (1, 2, 3)
                     for dx in range(-r, r + 1) for dy in range(-r, r + 1)
                     if max(abs(dx), abs(dy)) == r
                     and d.in_bounds(px + dx, py + dy) and d.is_walkable(px + dx, py + dy)
                     and (px + dx, py + dy) not in busy]
        # Nearest first: four-way neighbours, then the diagonals, then out.
        spots.sort(key=lambda t: (max(abs(t[0] - px), abs(t[1] - py)),
                                  abs(t[0] - px) + abs(t[1] - py), t))
        out = []
        for mid, n in fight_entries(spec):
            try:
                defn = _monster_defn(mid)
            except Exception:
                defn = None
            if not defn:
                continue
            for _ in range(n):
                if not spots:
                    return out
                t = spots.pop(0)
                m = Monster(defn, *t)
                m._aware = True
                self.monsters.append(m)
                out.append(m)
        return out

    def _npc_remove_item_by_id(self, item_id: str) -> bool:
        """Take the item with this id from the pack or a worn slot."""
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
        return removed

    def _npc_pay_cost(self, cost, selected_item=None):
        """Pay an option's cost (or an outcome's extra loss)."""
        # ── Apply cost ────────────────────────────────────────────
        if cost:
            ctype = cost['type']
            if ctype == 'multi':
                # Each part in turn; the picked item goes to the part that
                # asked for a pick (npc_encounters.get_inventory_filter).
                from npc_encounters import get_inventory_filter
                _given = False
                for sub in cost.get('costs') or ():
                    _mine = (not _given) and bool(get_inventory_filter(sub))
                    self._npc_pay_cost(sub, selected_item if _mine else None)
                    _given = _given or _mine
                return
            if ctype == 'armor_enchant':
                # Half the cloak cut away: the worn piece loses enchantment
                # (never below -3, the floor every enchant obeys).
                from npc_encounters import armor_enchant_target
                target = armor_enchant_target(self.player)
                if target is not None:
                    old = int(getattr(target, 'enchant_bonus', 0) or 0)
                    target.enchant_bonus = max(-3, old - int(cost.get('amount', 1)))
                    if target.enchant_bonus < old:
                        self.add_message(f"Your {self._bare_name(target)} is the poorer for it.",
                                         'warning')
                return
            if ctype in ('food', 'healing_potion', 'potion', 'scroll', 'weapon'):
                # "count": the picked item, then the rest of the count from
                # the pack in order. An outcome's item cost (no picker) takes
                # them all from the pack.
                from npc_encounters import cost_items
                _extra = int(cost.get('count', 1) or 1) - (1 if selected_item else 0)
                for _n in range(max(0, _extra)):
                    # One unit at a time (a stack gives one of its count).
                    _pool = cost_items(self.player, ctype)
                    _it = next((i for i in _pool if i is not selected_item), None)                         or next(iter(_pool), None)
                    if _it is None:
                        break
                    self.player.remove_from_inventory(_it)
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
                                f"You use the {self._bare_name(selected_item)}. ({selected_item.charges} charges left)", 'info')
                            if selected_item.charges <= 0:
                                self.player.remove_from_inventory(selected_item)
                        else:
                            self.player.remove_from_inventory(selected_item)
                    else:
                        self.player.remove_from_inventory(selected_item)
            elif ctype == 'gold':
                # A branch or per-miss cost is not checked against the purse
                # first (ENG-10): it takes what there is, never below zero.
                self.player_gold = max(0, self.player_gold - int(cost['amount']))
            elif ctype == 'hp_percent':
                loss = max(5, int(self.player.hp * cost['amount'] / 100))
                self.player.hp = max(1, self.player.hp - loss)
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
                from items import Scroll, Potion, Food, Ingredient, Weapon
                cat = cost.get('category', 'scroll')
                cat_map = {'scroll': Scroll, 'potion': Potion, 'food': (Food, Ingredient), 'weapon': Weapon}
                cls = cat_map.get(cat)
                if cls and selected_item and isinstance(selected_item, cls):
                    self.player.remove_from_inventory(selected_item)
                elif cls:
                    from npc_encounters import offerable
                    item = next((i for i in self.player.inventory
                                 if isinstance(i, cls) and offerable(i)), None)
                    if item:
                        self.player.remove_from_inventory(item)
            elif ctype == 'triggered_item':
                # Remove the trigger item from inventory OR equipment slots
                enc = self._npc_encounter_active
                self._npc_remove_item_by_id(enc.get('trigger_item', ''))
            elif ctype == 'triggered_item_id':
                # The same, for any item named in the cost (DEEDS_KARMA_DESIGN 4.3)
                self._npc_remove_item_by_id(cost.get('item_id', ''))
            elif ctype == 'accept_item':
                # Give the player a burden/cursed item
                self._grant_burden_item(cost['item_id'])
            elif ctype == 'spawn_deadite_ambush':
                # Free hit: 10% HP, then spawn a hostile Deadite
                loss = max(5, int(self.player.hp * 10 / 100))
                # never the killing blow: a talk option is not a death trap
                loss = min(loss, max(0, self.player.hp - 1))
                self.player.hp -= loss
                self.add_message(f"The Deadite rakes you for {loss} damage!", 'danger')
                self._spawn_npc_deadite()
            # A share of the player's OWN pool (LORE NOT FLOOR: never the floor).
            elif ctype == 'hp_pct':
                from npc_encounters import pct_loss
                loss = pct_loss(self.player.hp, cost['amount'])
                self.player.hp = max(1, self.player.hp - loss)
            elif ctype == 'sp_pct':
                from npc_encounters import pct_loss
                self.player.sp = max(0, self.player.sp - pct_loss(self.player.sp, cost['amount'], 0))
            elif ctype == 'mp_pct':
                from npc_encounters import pct_loss
                self.player.mp = max(0, self.player.mp - pct_loss(self.player.mp, cost['amount'], 0))
            elif ctype == 'max_hp_pct':
                from npc_encounters import pct_loss
                self.player.max_hp = max(1, self.player.max_hp - pct_loss(self.player.max_hp, cost['amount']))
                self.player.hp = min(self.player.hp, self.player.max_hp)
            elif ctype == 'gold_pct':
                from npc_encounters import pct_loss
                self.player_gold = max(0, self.player_gold - pct_loss(self.player_gold, cost['amount'], 0))
            elif ctype == 'stat':
                # Lost stat points: a real consequence of blind help.
                stat = cost['stat']
                have = int(getattr(self.player, stat, 0) or 0)
                amount = max(0, min(int(cost.get('amount', 1)), have - 3))
                if amount:
                    self.player.apply_stat_bonus(stat, -amount)
                    self.add_message(f"-{amount} {stat}.", 'danger')

    def _apply_npc_reward(self, reward: dict):
        """Grant a reward from an NPC encounter choice."""
        rtype = reward['type']

        if rtype == 'gold':
            if 'amount' in reward:
                amount = reward['amount']
            else:
                amount = random.randint(reward['min'], reward['max'])
            self.player_gold += amount
            self.add_message(f"+{amount:,} gold!", 'loot')

        elif rtype in ('random_weapon', 'random_armor', 'random_shield',
                        'random_accessory', 'random_potion', 'random_scroll',
                        'random_food', 'random_wand'):
            count = reward.get('count', 1)
            for _ in range(count):
                item = self._generate_npc_reward_item(rtype)
                if item:
                    self.add_message(f"Received: {self._display_name(item)}", 'loot')
                    self._give_item(item)

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
                self.add_message(f"Received: {self._display_name(item)}", 'loot')
                self._give_item(item)

        elif rtype == 'random_item':
            # Flavor encounter reward: random item by category name
            cat = reward.get('category', 'potion')
            item = self._generate_npc_reward_item(f'random_{cat}')
            if item:
                from items import grant_identified
                grant_identified(self, item)
                self.add_message(f"Received: {self._display_name(item)}", 'loot')
                self._give_item(item)

        elif rtype == 'gold_pct':
            # A share of the hero's own purse back (a slaver's change).
            from npc_encounters import pct_loss
            amount = pct_loss(self.player_gold, reward['amount'], 0)
            if amount:
                self.player_gold += amount
                self.add_message(f"+{amount:,} gold!", 'loot')

        elif rtype == 'gold_pct_loss':
            # A share of the hero's own purse, gone (a quick hand in the
            # night): LORE NOT FLOOR, a percentage of the player's own pool.
            from npc_encounters import pct_loss
            loss = pct_loss(self.player_gold, reward['amount'], 0)
            self.player_gold = max(0, self.player_gold - loss)
            if loss:
                self.add_message(f"Your purse is {loss:,} gold lighter.", 'danger')

        elif rtype == 'effect' and reward.get('floors'):
            # An effect that lasts whole floors (a porter for five, a
            # brighter lantern for two): held while the count runs, then
            # gone. Counted down on each new depth (Player.tick_floor_effects).
            eff = reward['effect']
            floors = max(1, int(reward['floors']))
            self.player.add_floor_effect(eff, floors)
            eff_name = eff.replace('_', ' ').title()
            self.add_message(
                f"{eff_name} for {floors} floor{'s' if floors != 1 else ''}!", 'success')

        elif rtype == 'effect':
            eff = reward['effect']
            dur = reward.get('duration', 20)
            self.player.add_effect(eff, dur)
            eff_name = eff.replace('_', ' ').title()
            # The turns it really lasts: statuses are capped (status_effects.
            # MAX_EFFECT_DURATION), and "Blessed for 150 turns!" gave 60.
            _got = self.player.status_effects.get(eff, 0)
            if isinstance(_got, int) and _got > 0:
                dur = _got
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

        # A share of the player's own maximum (LORE NOT FLOOR).
        elif rtype == 'hp_restore_pct':
            amt = max(1, int(self.player.max_hp * reward['amount'] / 100))
            self.player.restore_hp(amt)
            self.add_message(f"+{amt} HP!", 'success')

        elif rtype == 'sp_restore_pct':
            amt = max(1, int(self.player.max_sp * reward['amount'] / 100))
            self.player.sp = min(self.player.max_sp, self.player.sp + amt)
            self.add_message(f"+{amt} SP!", 'success')

        elif rtype == 'mp_restore_pct':
            amt = max(1, int(self.player.max_mp * reward['amount'] / 100))
            self.player.restore_mp(amt)
            self.add_message(f"+{amt} MP!", 'success')

        elif rtype == 'enchant_weapon':
            w = self.player.weapon
            if w:
                w.enchant_bonus += reward.get('amount', 1)
                # The number only when the weapon is identified: it named an
                # unknown blade by its true name and told its enchantment.
                if self._enchant_shown(w):
                    self.add_message(f"Your {self._bare_name(w)} is now {w.enchant_bonus:+d}!", 'success')
                else:
                    self.add_message(f"Your {self._bare_name(w)} glows!", 'success')
            else:
                self.add_message("You have no weapon equipped to enchant.", 'warning')

        elif rtype == 'armor_enchant':
            # Armour made whole and better (Saint Martin's dream): the worn
            # cloak, else body armour, else the first piece, up to its cap.
            from items import ARMOR_SLOTS, ENCHANT_CAP
            from npc_encounters import armor_enchant_target
            target = armor_enchant_target(self.player)
            if target is None:
                self.add_message("You wear no armour for it to mend.", 'info')
            else:
                slot = next((ARMOR_SLOTS[i] for i, s in enumerate(self.player.armor_slots)
                             if s is target), 'body')
                old = int(getattr(target, 'enchant_bonus', 0) or 0)
                target.enchant_bonus = max(old, min(ENCHANT_CAP.get(slot, 1),
                                                    old + int(reward.get('amount', 1))))
                if self._enchant_shown(target) and target.enchant_bonus != old:
                    self.add_message(f"Your {self._bare_name(target)} is now "
                                     f"{target.enchant_bonus:+d}!", 'success')
                else:
                    self.add_message(f"Your {self._bare_name(target)} glows!", 'success')

        elif rtype == 'random_artifact':
            # A relic from the run's unclaimed pool, set at the hero's feet
            # (the prayer gift's picker: no unique twice, no quest piece).
            name = self._spawn_intercession_artifact(self.player.x, self.player.y)
            if name:
                self.add_message(f"Received: {name} (at your feet).", 'loot')

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
        lvl = max(1, min(100, self.dungeon_level))
        try:
            # Gear comes from the floor's own generator. The item files hold
            # only named uniques, whose stats sat far under floor gear deep
            # down ("masterwork" was a fifth of a common sword at floor 95).
            from items import (is_random_loot, pick_random_weapon_for_floor,
                               pick_random_armor_for_floor, pick_random_shield_for_floor)
            _gear = {'weapon': pick_random_weapon_for_floor,
                     'armor': pick_random_armor_for_floor,
                     'shield': pick_random_shield_for_floor}.get(cls_name)
            if _gear is not None:
                result = _gear(lvl, random)
                if result is not None:
                    result.x, result.y = self.player.x, self.player.y
                    from items import grant_identified
                    grant_identified(self, result)
                    return result
            candidates = []
            for item in load_items(cls_name):
                ml = getattr(item, 'min_level', 1)
                # (Clamped: the Cow Level is numbered 999, which made every
                # min_level-999 hero keepsake eligible there.)
                _lvl = self.dungeon_level if 1 <= self.dungeon_level <= 100 else lvl
                from items import unique_available
                if (ml <= _lvl and ml < 9999 and is_random_loot(item)
                        and unique_available(item)):
                    candidates.append(item)
            if candidates:
                # Weighted by floor spawn weight, not a flat pick (on floors 3
                # to 9 most potion KINDS are harmful).
                from container_system import _weighted_common_pick
                template = _weighted_common_pick(candidates, lvl, random)
                result = copy_at(template, self.player.x, self.player.y)
                from items import grant_identified
                grant_identified(self, result)
                from items import claim_unique
                claim_unique(result)
                return result
        except Exception:
            from game_log import log_error
            log_error('game_encounters._generate_npc_reward_item: recovered from an error')
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
                        from items import grant_identified
                        grant_identified(self, result)
                    return result
        except Exception:
            from game_log import log_error
            log_error('game_encounters._create_specific_npc_item: recovered from an error')
        return None

    def _grant_burden_item(self, item_id: str):
        """Grant a cursed/burden item to the player (lodestone, dispatch, etc.)."""
        from items import load_items, copy_at
        try:
            for item in load_items('artifact'):
                if item.id == item_id:
                    result = copy_at(item, self.player.x, self.player.y)
                    from items import grant_identified
                    grant_identified(self, result)
                    # Stacked and stamped like any gift; an accepted burden
                    # is carried whatever the load (it is the cost).
                    if not self.player.add_to_inventory(result):
                        self.player.inventory.append(result)
                    return
        except Exception:
            from game_log import log_error
            log_error('game_encounters._grant_burden_item: recovered from an error')

    def _npc_committed(self) -> bool:
        """Has a choice already been made in the open encounter? (A 'then:
        options' encounter returns to its list after a choice; Esc there
        resolves it rather than leaving the NPC to be asked again.)"""
        enc = getattr(self, '_npc_encounter_active', None) or {}
        return bool(self._deeds_reg()['used_options'].get(enc.get('tag')))

    def _npc_outcome_continue(self):
        """Enter on the outcome page: back to the option list for a 'then:
        options' outcome (that option used up), otherwise close resolved."""
        enc = getattr(self, '_npc_encounter_active', None) or {}
        idx = getattr(self, '_npc_selected_index', None)
        if getattr(self, '_npc_after', 'close') == 'options' and idx is not None:
            used = self._deeds_reg()['used_options'].setdefault(enc.get('tag'), [])
            if idx not in used:
                used.append(idx)
            line = getattr(self, '_npc_outcome_chronicle', None)
            if line:
                self._npc_log_deed(enc, line)
            self._npc_outcome_chronicle = None
            self._npc_selected_option = None
            self._npc_selected_index = None
            self._npc_after = 'close'
            self._npc_show_options()
            if self._npc_visible:
                return
            # Nothing left to choose: each step's line is already in the
            # Journal, so the close adds no generic one.
            self._npc_outcome_chronicle = ''
        self._close_npc_encounter(resolved=True)

    def _npc_log_deed(self, enc: dict, line: str, *, own: bool = True):
        """The journal line of an encounter choice: a ``deed`` entry tied to
        the person (the encounter's ``person``, or the NPC itself), or a
        ``consequence`` filed under its cause when the encounter is a
        callback. The People tab keeps the person's last line."""
        import deeds
        from naming import proper_name
        enc = enc or {}
        tag = str(enc.get('tag') or '')
        reg = self._deeds_reg()
        floor, _d, _b, _t = self._deed_where()
        person = enc.get('person') if isinstance(enc.get('person'), dict) else None
        if person and person.get('id'):
            pid, pname = person['id'], person.get('name', '')
        else:
            pid = f"npc_{deeds.slug(tag)}" if tag else None
            npc = getattr(self, '_npc_encounter_monster', None)
            pname = getattr(npc, 'name', '') or enc.get('name', '')
        if pid:
            deeds.set_person(reg, pid, name=proper_name(str(pname or pid)), floor=floor,
                             last_line=line if own else None,
                             known=True if (own and person and _names_in(pname, line)) else None)
        cause = (reg.get('causes') or {}).get(tag)
        thread = getattr(self, '_npc_outcome_thread', None) if own else None
        if cause or (enc.get('callback_only') and tag not in _system_placed_tags()):
            # (A system places Setne's tomb itself; it is callback_only only
            # so nothing else rolls it, and its choices are deeds: CON-16.)
            self._chron('consequence', line, person=pid, source=cause or tag, thread=thread)
        else:
            self._chron('deed', line, person=pid, source=tag, thread=thread)
        self._npc_outcome_thread = None

    def _close_npc_encounter(self, resolved: bool):
        """Close the NPC encounter overlay."""
        _closing_npc = getattr(self, '_npc_encounter_monster', None)
        if resolved:
            # Remove the NPC
            npc = self._npc_encounter_monster
            if npc:
                npc.alive = False
                npc.hp = 0
            enc = self._npc_encounter_active
            if enc and enc.get('tag'):
                # Every figure of the scene goes with it (CON-09: Ahwere
                # used to stay behind Neferkaptah, then "go" when bumped).
                for _m in self.monsters:
                    if _m is not npc and _m.alive and (
                            getattr(_m, '_flavor_encounter_tag', None) == enc['tag']
                            or getattr(_m, '_npc_encounter_tag', None) == enc['tag']):
                        _m.alive = False
                        _m.hp = 0
            if enc:
                if getattr(self, '_npc_is_flavor', False):
                    encountered = getattr(self, '_encountered_flavor_npcs', set())
                    encountered.add(enc['tag'])
                else:
                    self._encountered_npcs.add(enc['tag'])
                # The journal line is the option's own (or the quiz branch
                # taken). The old random verbs ("Met the Rat-Catcher. Had to
                # make a hard choice.") could not tell "gave a child her
                # mother's pendant" from "kept it", so they are gone: with no
                # line of its own the encounter is only "Met the Lost Girl."
                _own = getattr(self, '_npc_outcome_chronicle', None)
                if _own is None:
                    _own = (self._npc_selected_option or {}).get('chronicle')
                if _own is None and self._deeds_reg()['used_options'].get(enc.get('tag')):
                    _own = ''   # left after 'then: options' steps, each logged (CON-15)
                if _own:
                    self._npc_log_deed(enc, _own)
                elif _own == '':
                    pass        # a 'then: options' encounter logged each step already
                else:
                    # With its article: "Met the Lost Girl.", not "Met Lost
                    # Girl." (and "Met the Penitent.", not "Met The Penitent.")
                    from monster import the_name as _the_name
                    _who = npc if npc is not None else type('N', (), {'name': enc.get('name', 'someone')})()
                    self._npc_log_deed(enc, f"Met {_the_name(_who, lower=True)}.", own=False)

        self._npc_encounter_active = None
        self._npc_encounter_monster = None
        self._npc_encounter_phase = 'text'
        self._npc_selected_option = None
        self._npc_selected_index = None
        self._npc_outcome_text = ''
        self._npc_outcome_chronicle = None
        self._npc_encounter_text = None
        self._npc_visible = None
        self._npc_after = 'close'
        self._npc_pending_option = None
        self._npc_item_list = []
        self._npc_is_flavor = False
        self.state = STATE_PLAYER
        _after = list(getattr(self, '_npc_after_close', None) or []) if resolved else []
        self._npc_after_close = []
        if resolved:
            self._advance_turn()
        if 'seal_door' in _after or 'expel_up' in _after:
            self._encounter_seal_room(_closing_npc)
        if 'expel_up' in _after:
            self._encounter_expel_up()
        if resolved and hasattr(self, '_lapse_orphan_oaths'):
            # A keeping scene closed without a keep (ENG-08).
            self._lapse_orphan_oaths()

    # ------------------------------------------------------------------
    # Encounter rooms (Setne's tomb): sealing and expulsion
    # ------------------------------------------------------------------

    def _encounter_room_of(self, npc):
        room = getattr(npc, '_encounter_room', None) if npc is not None else None
        if room is None:
            room = (getattr(self, '_setne', None) or {}).get('room') \
                if getattr(self, 'dungeon_level', None) == (getattr(self, '_setne', None) or {}).get('floor') \
                else None
        return room if isinstance(room, dict) else None

    def _encounter_seal_room(self, npc):
        """The room's door becomes wall, for good. A hero standing inside is
        put outside it first, and whoever else waits in the room goes."""
        from dungeon import WALL
        room = self._encounter_room_of(npc)
        if not room or not room.get('door'):
            return
        dx, dy = room['door']
        chamber = {tuple(t) for t in room.get('chamber') or ()}
        inside = chamber | {(dx, dy)}
        out = tuple(room.get('outside') or ())
        if self.dungeon.in_bounds(dx, dy):
            self.dungeon.tiles[dy][dx] = WALL
        # The hero, pets and escorts inside (or in the doorway) are put on
        # free tiles outside, nearest the door first (ENG-14, INT-09): the
        # hero used to land on a pet, and a pet or escort stayed walled in.
        bodies = []
        if (self.player.x, self.player.y) in inside:
            bodies.append(self.player)
        bodies += [p for p in (getattr(self, 'pets', None) or [])
                   if getattr(p, 'alive', True) and (p.x, p.y) in inside]
        if hasattr(self, '_escorts_here'):
            bodies += [e for e in self._escorts_here() if (e.x, e.y) in inside]
        if bodies and out:
            from geom import all_occupied_tiles
            busy = set(all_occupied_tiles([m for m in self.monsters if m.alive])) | \
                (self._occupants() if hasattr(self, '_occupants') else set())
            busy -= {(b.x, b.y) for b in bodies}
            try:
                reach = self._reachable_tiles(*out)
            except Exception:
                reach = {out}
            ox, oy = out
            spots = sorted((t for t in reach if t not in inside and t not in busy
                            and self.dungeon.is_walkable(*t)),
                           key=lambda t: (max(abs(t[0] - ox), abs(t[1] - oy)),
                                          abs(t[0] - ox) + abs(t[1] - oy), t))
            for b in bodies:
                if not spots:
                    break
                b.x, b.y = spots.pop(0)
        for m in list(self.monsters):
            if (m.x, m.y) in chamber and getattr(m, '_encounter_room', None) is not None:
                m.alive = False
                m.hp = 0
        self.monsters[:] = [m for m in self.monsters if m.alive or (m.x, m.y) not in chamber]
        room['sealed'] = True
        if room.get('system') == 'setne':
            st = getattr(self, '_setne', None)
            if isinstance(st, dict):
                st['sealed'] = True
        try:
            self._refresh_fov()
        except Exception:
            pass

    def _encounter_expel_up(self):
        """The floor gives the hero up to the floor above: a floor already
        visited, never the Cow Level. From floor 1 there is nowhere up, so
        nothing happens."""
        from boss_levels import COW_LEVEL
        cur = int(getattr(self, 'dungeon_level', 1) or 1)
        if cur <= 1 or cur == COW_LEVEL:
            return
        target = cur - 1
        try:
            self._change_level(target, enter_from_top=False, via='warp')
        except Exception:
            from game_log import log_error
            log_error('game_encounters._encounter_expel_up: recovered from an error')

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
                    from items import grant_identified
                    grant_identified(self, sw)
                    self._give_item(sw)
                    self.add_message("The Sword of Michael materializes in your hands!", 'success')
            except Exception:
                from game_log import log_error
                log_error('game_encounters._resolve_judgment: recovered from an error')
            try:
                artifacts = load_items('artifact')
                scales = next((a for a in artifacts if a.id == 'scales_of_michael'), None)
                if scales:
                    sc = copy_at(scales, px, py)
                    from items import grant_identified
                    grant_identified(self, sc)
                    self._give_item(sc)
                    self.add_message("The Scales of Michael float into your grasp!", 'success')
            except Exception:
                from game_log import log_error
                log_error('game_encounters._resolve_judgment: recovered from an error')
            self._chron('soul', "Stood before the altar of judgment. The scales weighed my soul. I was found worthy. A sword of white fire and the scales themselves were given to me. I've never felt so terrified.")

        elif outcome == 'scales_granted':
            from items import load_items, copy_at
            px, py = self.player.x, self.player.y
            try:
                artifacts = load_items('artifact')
                scales = next((a for a in artifacts if a.id == 'scales_of_michael'), None)
                if scales:
                    sc = copy_at(scales, px, py)
                    from items import grant_identified
                    grant_identified(self, sc)
                    self._give_item(sc)
                    self.add_message("The Scales of Michael float into your grasp!", 'success')
            except Exception:
                from game_log import log_error
                log_error('game_encounters._resolve_judgment: recovered from an error')
            self._chron('soul', "The altar weighed my deeds. Not perfect, but enough. The Scales of Michael settled into my hands. They hum with a quiet judgment.")

        elif outcome == 'abaddon_empowered':
            # Abaddon gets 50% more HP and extra attack
            self.add_message("A dark power surges into the depths below...", 'danger')
            # Store flag for when L100 is generated
            self._abaddon_empowered = True
            self._chron('soul', "The altar judged me. I was found wanting. Something below grew stronger. I can feel it.")

        elif outcome == 'locusts_strengthened':
            # Larger locust swarms
            self.add_message("The buzzing of locusts grows louder in the deep...", 'danger')
            self._locusts_strengthened = True
            self._chron('soul', "The judgment went poorly. The buzzing from below is louder now. I made things worse.")
