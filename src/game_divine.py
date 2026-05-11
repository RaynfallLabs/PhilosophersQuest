"""Game's religious / divine action handlers, extracted from main.py.

This module defines :class:`DivineMixin`, which the real ``Game`` class
inherits alongside the other mixins.  It owns the Game-side orchestration
of:

  * Altar BUC mechanics (``_altar_buc_upgrade``, ``_altar_buc_identify``).
  * Named-god shrines (Ariadne, Athena, Odin) and the Fenrir-quest forge
    checks (``_check_gleipnir_forge``, ``_check_vidar_altar``).
  * Prayer (``_start_pray``, ``_resolve_prayer``).
  * Fountain / grave / throne tile interactions and their resolutions.
  * Mystery-altar orchestration (``_find_adjacent_mystery_altar``,
    ``_start_observe``, ``_start_mystery``, ``_begin_mystery_challenge``).

The pre-existing ``mystery_system`` module provides the data and reward
logic for mystery altars; this mixin only drives the Game-state
transitions and quiz callbacks.  Rendering of the mystery-approach state
lives in :class:`game_render.RenderMixin`; input handling lives in
:class:`game_input.InputMixin`.  ``_resolve_judgment`` lives in
:class:`game_encounters.EncountersMixin` and is reached by ``_start_pray``
through MRO.
"""
from __future__ import annotations

import copy
import random

import sound_system as _snd
from dungeon import FLOOR, DOOR, ALTAR
from game_states import (
    STATE_PLAYER, STATE_QUIZ, STATE_TARGET, STATE_MYSTERY_APPROACH,
)


class DivineMixin:
    # ------------------------------------------------------------------
    # Mystery altars: discovery, observation, and orchestration
    # ------------------------------------------------------------------

    def _find_adjacent_mystery_altar(self):
        """Return a MysteryAltar on the player's tile or any adjacent tile, or None."""
        from mystery_system import MysteryAltar
        px, py = self.player.x, self.player.y
        for item in self.ground_items:
            if not isinstance(item, MysteryAltar):
                continue
            if item.activated:
                continue
            if abs(item.x - px) <= 1 and abs(item.y - py) <= 1:
                return item
        return None

    def _start_observe(self):
        """Press 'o' to enter observe mode — look at monsters, items, or terrain."""
        px, py = self.player.x, self.player.y
        sight = self.player.get_sight_radius()

        # Build candidate list: visible monsters
        candidates = [
            m for m in self.monsters
            if m.alive and (m.x, m.y) in self.visible
        ]
        candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))

        self._target_candidates = candidates
        self._target_idx = 0
        self._observe_targeting = True
        self._melee_targeting = False
        self._throw_targeting = False
        self._observe_reach = sight

        if candidates:
            m = candidates[0]
            self.target_cursor_x = m.x
            self.target_cursor_y = m.y
        else:
            self.target_cursor_x = px
            self.target_cursor_y = py

        self.state = STATE_TARGET
        self.add_message(
            "Observe -- arrow keys to look, TAB to cycle targets, ENTER to examine, ESC to cancel.",
            'info'
        )

    def _start_mystery(self, altar):
        """Begin a mystery encounter -- show description and ask the player to accept."""
        from mystery_system import MYSTERIES, can_activate
        m = MYSTERIES[altar.mystery_id]
        # Show description always
        self.add_message(m['description'], 'info')
        can, reason = can_activate(altar.mystery_id, self.player,
                                   getattr(self, 'player_gold', 0))
        if not can:
            self.add_message(f"{m['name']}: {reason}", 'warning')
            return
        self._active_mystery_altar = altar
        if not getattr(self, '_chronicle_first_mystery', False):
            self._chronicle_first_mystery = True
            self._log_chronicle(f"Found a strange altar. {m['name']}. The inscription dared me to approach.")
        self.state = STATE_MYSTERY_APPROACH

    def _begin_mystery_challenge(self):
        """Trigger the actual challenge for the active mystery."""
        from mystery_system import MYSTERIES, consume_key_item, get_cauldron_food_items, apply_mystery_reward
        altar = self._active_mystery_altar
        if altar is None:
            self.state = STATE_PLAYER
            return
        m  = MYSTERIES[altar.mystery_id]
        ch = m['challenge']

        # Pre-challenge costs
        if m.get('stat_cost'):
            for stat, amt in m['stat_cost'].items():
                self.player.apply_stat_bonus(stat, amt)
            self.add_message("You feel a part of yourself drain away as payment...", 'warning')

        if m.get('gold_cost', 0) > 0:
            self.player_gold = getattr(self, 'player_gold', 0) - m['gold_cost']
            self.add_message(f"You offer {m['gold_cost']} gold as tribute.", 'info')

        # Consume key item (if any; not cauldron food, not sisyphus boulder)
        if m['key_item'] is not None and altar.mystery_id not in ('cauldron', 'sisyphus'):
            consume_key_item(altar.mystery_id, self.player)

        # For cauldron: consume 3 food items
        if altar.mystery_id == 'cauldron':
            foods = get_cauldron_food_items(self.player)
            for food in foods[:3]:
                self.player.remove_from_inventory(food)
            self.add_message("Three meals are consumed by the cauldron's fire.", 'info')

        # Sisyphus: physical challenge -- start tracking tiles
        if ch['mode'] == 'physical':
            self.player.quirk_progress['sisyphus_boulder_active'] = True
            self.player.quirk_progress['sisyphus_boulder_tiles'] = 0
            self.add_message("You grasp the boulder. Begin your ascent.", 'info')
            self.state = STATE_PLAYER
            self._active_mystery_altar = None
            return

        # Quiz challenge
        def _on_mystery_complete(result):
            success = result.success
            # For chain mode, check threshold manually
            if ch['mode'] in ('chain', 'escalator_chain') and 'threshold' in ch:
                success = result.score >= ch['threshold']
            # Pandora inversion
            if m.get('invert_result'):
                success = not success
            apply_mystery_reward(altar.mystery_id, self.player, self, success)
            if not altar.activated:
                altar.activated = True
                # Remove altar from ground_items once activated
                if altar in self.ground_items:
                    self.ground_items.remove(altar)
            self._active_mystery_altar = None

        quiz_kwargs = {
            'mode':           ch['mode'],
            'subject':        ch['subject'],
            'tier':           ch['tier'],
            'callback':       _on_mystery_complete,
            'threshold':      ch.get('threshold', 3),
            'wisdom':         self.player.WIS,
            'timer_modifier': self.player.get_quiz_timer_modifier(),
            'extra_seconds':  self.player.get_quiz_extra_seconds(ch['subject']),
            'base_seconds':   self.player.get_quiz_timer(ch['subject']),
        }
        if 'total' in ch:
            quiz_kwargs['total_qs'] = ch['total']
        if 'max_chain' in ch:
            quiz_kwargs['max_chain'] = ch['max_chain']

        self.quiz_title = f"{m['name'].upper()}  --  {ch['subject'].upper()}"
        self.state = STATE_QUIZ
        self.quiz_engine.start_quiz(**quiz_kwargs)

    # ------------------------------------------------------------------
    # Altar BUC mechanics  (drop-on-altar bless / divine BUC status)
    # ------------------------------------------------------------------

    def _altar_buc_upgrade(self, item):
        """Drop an item on an altar to attempt uncurse/bless via theology quiz."""
        display = self._display_name(item)
        self.add_message(f"You place the {display} upon the altar...", 'info')
        self.quiz_title = "ALTAR BLESSING -- THEOLOGY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            chain = result.score
            if chain == 0:
                self.add_message("The altar remains cold and silent.", 'warning')
            elif item.buc == 'cursed':
                if chain >= 3:
                    item.buc = 'blessed'
                    item.buc_known = True
                    self.add_message(
                        f"Dark energy shatters — golden light suffuses the {display}! It is blessed!",
                        'success')
                else:
                    item.buc = 'uncursed'
                    item.buc_known = True
                    self.add_message(
                        f"The dark aura around the {display} dissipates! It is uncursed.",
                        'success')
            elif item.buc == 'uncursed':
                if chain >= 3:
                    item.buc = 'blessed'
                    item.buc_known = True
                    self.add_message(
                        f"Golden light suffuses the {display}! It is blessed!",
                        'success')
                else:
                    item.buc_known = True
                    self.add_message(
                        "The altar glows faintly but the blessing is insufficient.",
                        'info')
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='theology',
            tier=1,
            callback=on_complete,
            max_chain=5,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('theology'),
            base_seconds=self.player.get_quiz_timer('theology'),
        )

    def _altar_buc_identify(self):
        """Stand on an altar and attempt to divine the BUC status of an item."""
        # Gather items that have BUC but it's not yet known
        candidates = [i for i in self.player.inventory
                      if hasattr(i, 'buc') and not getattr(i, 'buc_known', False)]
        if not candidates:
            self.add_message("You kneel at the altar, but sense nothing to divine.", 'info')
            return
        # Use the first unidentified-BUC item (simple approach -- could add a menu later)
        item = candidates[0]
        display = self._display_name(item)
        self.add_message(f"You place the {display} upon the altar and pray...", 'info')
        self.quiz_title = "ALTAR DIVINATION  --  THEOLOGY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                item.buc_known = True
                _buc = item.buc
                if _buc == 'blessed':
                    self.add_message(
                        f"The {display} glows with a warm golden light. It is blessed!", 'success'
                    )
                elif _buc == 'cursed':
                    self.add_message(
                        f"The {display} exudes a dark miasma. It is cursed!", 'warning'
                    )
                else:
                    self.add_message(
                        f"The {display} shows no special aura. It is uncursed.", 'info'
                    )
            else:
                self.add_message("The altar remains silent. Your prayer goes unanswered.", 'warning')
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='theology',
            tier=1,
            callback=on_complete,
            threshold=1,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus(),
            base_seconds=self.player.get_quiz_timer('theology'),
        )

    # ------------------------------------------------------------------
    # Fountain
    # ------------------------------------------------------------------

    def _drink_fountain(self):
        """Drink from a fountain -- AI quiz determines outcome."""
        self.add_message("You cup your hands and drink from the fountain...", 'info')
        self.quiz_title = "FOUNTAIN -- AI"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            self._resolve_fountain(chain)
            self.state = STATE_PLAYER
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='ai',
            tier=1,
            callback=on_complete,
            max_chain=6,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('ai'),
            base_seconds=self.player.get_quiz_timer('ai'),
        )

    def _resolve_fountain(self, chain: int):
        """Apply fountain effects based on chain score."""
        if not getattr(self, '_chronicle_first_fountain', False):
            self._chronicle_first_fountain = True
            self._log_chronicle("Drank from a dungeon fountain. Tasted like copper and starlight. Something happened.")
        import random as _rng
        px, py = self.player.x, self.player.y

        if chain == 0:
            outcome = _rng.choice(['poison', 'monster', 'nothing'])
            if outcome == 'poison':
                self.player.add_effect('poisoned', 10)
                self.add_message("The water tastes foul! You feel poisoned!", 'danger')
            elif outcome == 'monster':
                self.add_message("Something rises from the fountain!", 'danger')
                self._spawn_at(px, py)
            else:
                self.add_message("The water tastes stale. Nothing happens.", 'info')
        elif chain == 1:
            self.add_message("The cool water refreshes you slightly.", 'info')
            self.player.restore_hp(max(5, self.player.max_hp // 20))
        elif chain == 2:
            self.add_message("The blessed water restores your health!", 'success')
            self.player.restore_hp(max(15, self.player.max_hp // 8))
        elif chain == 3:
            self.add_message("The magical water restores you fully!", 'success')
            self.player.restore_hp(self.player.max_hp)
            self.player.restore_sp(50)
        elif chain == 4:
            self.player.restore_hp(self.player.max_hp)
            self.player.restore_sp(self.player.max_sp)
            for eff in list(self.player.status_effects.keys()):
                if eff in ('poisoned', 'diseased', 'bleeding', 'burning', 'confused', 'blinded', 'corroding'):
                    del self.player.status_effects[eff]
            self.add_message("Divine water purifies you! All ailments are cured!", 'success')
        elif chain >= 5:
            stat = _rng.choice(['STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'])
            self.player.apply_stat_bonus(stat, 1)
            self.player.restore_hp(self.player.max_hp)
            self.add_message(f"The fountain glows with divine light! +1 {stat}!", 'success')

        # 33% chance fountain dries up after use
        if _rng.random() < 0.33:

            self.dungeon.tiles[py][px] = FLOOR
            self.add_message("The fountain dries up.", 'info')

    # ------------------------------------------------------------------
    # Named-god shrines: Ariadne, Athena, Odin
    # ------------------------------------------------------------------

    def _activate_ariadne_shrine(self, bull_item):
        """Player dropped the Bronze Bull into a fountain -- activate Ariadne's shrine."""
        shrine_door = getattr(self.dungeon, 'ariadne_shrine_door', None)
        if not shrine_door:
            # Wrong level — don't consume the item
            return

        # Consume the bull (remove from ground)
        if bull_item in self.ground_items:
            self.ground_items.remove(bull_item)

        self.add_message(
            "The bronze bull sinks into the fountain waters...", 'info')
        self.add_message(
            "The water shimmers gold! A voice whispers from the depths:", 'info')
        self.add_message(
            '"I wove salvation from a simple thread. Take it, and the beast '
            'shall have no walls to hide behind."', 'success')

        dx, dy = shrine_door
        self.dungeon.tiles[dy][dx] = DOOR
        self.add_message(
            "A hidden passage opens in a nearby wall!", 'success')
        self._log_chronicle("Dropped the bronze bull into a fountain. The water turned gold. A woman's voice spoke to me about thread and a beast. A passage opened in the wall.")

    def _activate_athena_shrine(self, eye_item):
        """Player dropped the Eye of the Graeae at an altar -- activate Athena's shrine."""
        shrine_door = getattr(self.dungeon, 'athena_shrine_door', None)
        if not shrine_door:
            # Wrong level — don't consume the item
            return

        if eye_item in self.ground_items:
            self.ground_items.remove(eye_item)

        self.add_message(
            "You place the milky eye upon the altar. It dissolves into pale light...", 'info')
        self.add_message(
            "A divine presence fills the room! Athena speaks:", 'info')
        self.add_message(
            '"The Grey Sisters paid for their secret. Take my shield, '
            'and let the Gorgon see what she truly is."', 'success')

        dx, dy = shrine_door
        self.dungeon.tiles[dy][dx] = DOOR
        self.add_message(
            "A hidden passage opens in a nearby wall!", 'success')
        self._log_chronicle("Placed the eye on an altar. It dissolved into light. Athena herself spoke. Told me to take her shield. A passage opened.")

    def _activate_odin_shrine(self, gram_item, reforge: bool = False):
        """Player offered the Broken Blade of Gram at Odin's Altar."""
        odin_pos = self.dungeon.odin_altar_pos
        shrine_door = getattr(self.dungeon, 'odin_shrine_door', None)
        if not shrine_door and not reforge:
            return  # wrong level, no shrine

        # Consume the broken blade
        if gram_item in self.ground_items:
            self.ground_items.remove(gram_item)

        if reforge:
            # SECRET: throw-over reforges Gram!
            self.add_message(
                "You hurl the broken blade over the altar...", 'info')
            self.add_message(
                "CRACK! A bolt of lightning strikes the altar! "
                "Thunder shakes the dungeon to its foundations!", 'danger')
            self.add_message(
                "Odin's voice booms: \"You have thrown your weapon over the enemy, "
                "as I threw Gungnir. I name you worthy.\"", 'success')
            self.add_message(
                "The shattered fragments of Gram fuse together in white-hot light. "
                "A reforged blade rests upon the altar, whole and gleaming.", 'success')
            # Spawn reforged Gram on the altar
            from items import load_items, copy_at
            weapons = load_items('weapon')
            gram_t = next((w for w in weapons if w.id == 'gram'), None)
            if gram_t:
                ax, ay = odin_pos
                gram = copy_at(gram_t, ax, ay)
                gram.identified = True
                self.ground_items.append(gram)
        else:
            # Normal path: blade dissolves, Odin speaks
            self.add_message(
                "The broken blade dissolves into the altar stone...", 'info')
            self.add_message(
                "Odin speaks: \"The blade is spent. But the earth holds secrets "
                "that steel cannot reach. Dig, as Sigurd dug.\"", 'success')

        # Always open the shrine (contains the shovel)
        if shrine_door:
            dx, dy = shrine_door
            self.dungeon.tiles[dy][dx] = DOOR
            self.add_message(
                "A hidden passage opens in a nearby wall!", 'success')
        if reforge:
            self._log_chronicle("I threw the broken blade over the altar like a madman. Lightning struck. When the light cleared, Gram lay whole on the stone, reforged. Odin called me worthy.")
        else:
            self._log_chronicle("Laid the broken blade on the altar. It dissolved. Odin spoke of digging, of secrets beneath the earth. A passage opened nearby.")

    # ------------------------------------------------------------------
    # Fenrir quest: Gleipnir forging, binding, and Vidar's Altar
    # ------------------------------------------------------------------

    _GLEIPNIR_COMPONENT_IDS = frozenset([
        'cats_footstep', 'womans_beard', 'mountain_root',
        'fish_breath', 'bird_spittle', 'bear_sinew',
    ])

    def _check_gleipnir_forge(self, fx, fy):
        """Check if all 6 Gleipnir components are at the Dwarven Forge position."""
        on_forge = [i for i in self.ground_items
                    if getattr(i, 'id', '') in self._GLEIPNIR_COMPONENT_IDS
                    and i.x == fx and i.y == fy]
        found_ids = {i.id for i in on_forge}
        if found_ids == self._GLEIPNIR_COMPONENT_IDS:
            # All 6 present — forge Gleipnir!
            for comp in on_forge:
                self.ground_items.remove(comp)
            from items import Artifact
            gleipnir = Artifact({
                'id': 'gleipnir', 'name': 'Gleipnir',
                'symbol': '&', 'color': [220, 220, 255],
                'item_class': 'artifact', 'weight': 0.1, 'min_level': 60,
            })
            gleipnir.identified = True
            gleipnir.x, gleipnir.y = fx, fy
            self.ground_items.append(gleipnir)
            self.add_message(
                "The six impossible ingredients dissolve into the forge's flames...", 'info')
            self.add_message(
                "A shimmering ribbon materializes, thin as silk but unbreakable — "
                "GLEIPNIR, the binding that held the World-Wolf!", 'success')
            _snd.play('equip')
            self._log_chronicle("Fed six impossible things to the Dwarven Forge. The flames consumed them all. What came out was a ribbon, thin as silk. Gleipnir. I can't break it. Nothing can.")

    def _check_vidar_altar(self, vx, vy):
        """Check if 10 leather scraps are at Vidar's Altar."""
        on_altar = [i for i in self.ground_items
                    if getattr(i, 'id', '') == 'leather_scrap'
                    and i.x == vx and i.y == vy]
        if len(on_altar) >= 10:
            # Consume all scraps, create Vidar's Sandal
            for scrap in on_altar[:10]:
                self.ground_items.remove(scrap)
            from items import load_items, copy_at
            armors = load_items('armor')
            sandal_t = next((a for a in armors if a.id == 'vidars_sandal'), None)
            if sandal_t:
                sandal = copy_at(sandal_t, vx, vy)
                sandal.identified = True
                self.ground_items.append(sandal)
                self.add_message(
                    "The leather scraps melt together on the ancient altar...", 'info')
                self.add_message(
                    "They reshape into a massive sandal of primordial leather — "
                    "VIDAR'S SANDAL. The Silent God's weapon against the World-Wolf.", 'success')
                _snd.play('equip')
                self._log_chronicle("Piled leather scraps on an ancient altar. They melted together into a massive sandal. Vidar's Sandal. The Silent God's secret weapon.")

    # ------------------------------------------------------------------
    # Grave
    # ------------------------------------------------------------------

    def _dig_grave(self):
        """Dig up a grave -- geography quiz determines outcome."""
        self.add_message("You begin disturbing the grave...", 'info')
        self.quiz_title = "GRAVE -- GEOGRAPHY"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            self._resolve_grave(chain)
            self.state = STATE_PLAYER
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='geography',
            tier=1,
            callback=on_complete,
            max_chain=5,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('geography'),
            base_seconds=self.player.get_quiz_timer('geography'),
        )

    def _resolve_grave(self, chain: int):
        """Apply grave-digging effects based on chain score."""
        if not getattr(self, '_chronicle_first_grave', False):
            self._chronicle_first_grave = True
            self._log_chronicle("Dug up a grave. I'm not proud of it, but the dead don't need what's buried with them.")
        import random as _rng
        px, py = self.player.x, self.player.y

        if chain == 0:
            self.add_message("A restless spirit emerges from the grave!", 'danger')
            self._spawn_at(px, py)
        elif chain == 1:
            gold = _rng.randint(5, 30)
            self.player_gold += gold
            self.add_message(f"You find {gold} gold coins buried with the dead.", 'success')
        elif chain == 2:
            self.add_message("You unearth a buried item!", 'success')
            self._spawn_grave_item(px, py)
        elif chain >= 3:
            gold = _rng.randint(20, 80)
            self.player_gold += gold
            self._spawn_grave_item(px, py)
            self.add_message(f"A rich burial! You find {gold} gold and a buried treasure!", 'success')

        # Grave is consumed
        self.dungeon.tiles[py][px] = FLOOR
        self.add_message("The grave has been disturbed.", 'info')

    def _spawn_grave_item(self, x: int, y: int):
        """Spawn a random level-appropriate item at (x, y) from the grave."""
        from items import load_items
        templates = []
        for cls_name in ('weapon', 'armor', 'shield', 'accessory', 'scroll', 'potion'):
            try:
                templates += [t for t in load_items(cls_name)
                              if getattr(t, 'min_level', 1) <= self.dungeon_level]
            except FileNotFoundError:
                pass
        if templates:
            item = copy.copy(random.choice(templates))
            item.x, item.y = x, y
            self.ground_items.append(item)

    # ------------------------------------------------------------------
    # Throne
    # ------------------------------------------------------------------

    def _sit_throne(self):
        """Sit upon the throne -- history quiz determines outcome."""
        self.add_message("You settle onto the ancient throne...", 'info')
        self.quiz_title = "THRONE -- HISTORY"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            self._resolve_throne(chain)
            self.state = STATE_PLAYER
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='history',
            tier=1,
            callback=on_complete,
            max_chain=6,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('history'),
            base_seconds=self.player.get_quiz_timer('history'),
        )

    def _resolve_throne(self, chain: int):
        """Apply throne effects based on chain score."""
        if not getattr(self, '_chronicle_first_throne', False):
            self._chronicle_first_throne = True
            self._log_chronicle("Sat on a throne in the dark. It fit perfectly. That worries me.")
        import random as _rng
        px, py = self.player.x, self.player.y

        if chain == 0:
            outcome = _rng.choice(['shock', 'curse', 'summon'])
            if outcome == 'shock':
                dmg = _rng.randint(5, 15)
                self.player.take_damage(dmg, 'lightning')
                self.add_message(f"The throne shocks you for {dmg} damage!", 'danger')
            elif outcome == 'curse':
                self.player.add_effect('weakened', 20)
                self.add_message("A curse settles over you! You feel weakened.", 'danger')
            else:
                self.add_message("Guards materialize to defend the throne!", 'danger')
                for _ in range(2):
                    self._spawn_at(px, py)
        elif chain == 1:
            gold = _rng.randint(10, 50)
            self.player_gold += gold
            self.add_message(f"You find {gold} gold wedged in the cushions.", 'success')
        elif chain == 2:
            self.player.restore_hp(max(20, self.player.max_hp // 5))
            self.add_message("The throne's enchantment heals your wounds!", 'success')
        elif chain == 3:
            count = 0
            for item in self.player.inventory:
                if not getattr(item, 'identified', True):
                    item.identified = True
                    self.player.known_item_ids.add(item.id)
                    count += 1
            if count:
                self.add_message(f"Royal insight! {count} items identified!", 'success')
            else:
                self.add_message("Royal insight fills you, but all your items are known.", 'info')
        elif chain == 4:
            bonus = _rng.randint(5, 15)
            self.player.max_hp += bonus
            self.player.hp = min(self.player.hp + bonus, self.player.max_hp)
            self.add_message(f"The throne's blessing strengthens you! +{bonus} max HP!", 'success')
        elif chain >= 5:
            stats = _rng.sample(['STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'], 2)
            for s in stats:
                self.player.apply_stat_bonus(s, 1)
            self.add_message(f"The throne crowns you worthy! +1 {stats[0]}, +1 {stats[1]}!", 'success')

        # 33% chance throne crumbles
        if _rng.random() < 0.33:

            self.dungeon.tiles[py][px] = FLOOR
            self.add_message("The ancient throne crumbles to dust.", 'info')

    # ------------------------------------------------------------------
    # Prayer  (\ key -- theology escalator_chain quiz)
    # ------------------------------------------------------------------

    def _start_pray(self):
        """Begin a prayer -- escalator chain quiz (theology). Cooldown-gated."""
        # Altar of the Last Judgment on L99: special one-time judgment
        if self.dungeon_level == 99:
            jpos = getattr(self.dungeon, 'judgment_altar_pos', None)
            if jpos and (self.player.x, self.player.y) == jpos:
                if hasattr(self, '_judgment_resolved'):
                    self.add_message("The altar is silent. It has already spoken.", 'info')
                    return
                self._judgment_resolved = True
                self._resolve_judgment()
                return

        if self.player.prayer_cooldown > 0:
            self.add_message(
                f"You cannot pray yet. ({self.player.prayer_cooldown} turns remain)",
                'warning'
            )
            return
        at_altar = self.dungeon.tiles[self.player.y][self.player.x] == ALTAR
        bonus_desc = " The altar amplifies your prayer." if at_altar else ""
        self.add_message(f"You kneel and pray...{bonus_desc}", 'info')
        self._at_altar = at_altar
        self.quiz_title = "PRAYER -- THEOLOGY"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            self._resolve_prayer(chain, self._at_altar)
            self.state = STATE_PLAYER
            _qs_pray = getattr(self, 'quirk_system', None)
            if _qs_pray and chain > 0:
                hp_pct = self.player.hp / max(1, self.player.max_hp)
                _qs_pray.on_prayer(hp_pct)
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='theology',
            tier=1,
            callback=on_complete,
            max_chain=8,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('theology'),
            base_seconds=self.player.get_quiz_timer('theology'),
        )

    def _resolve_prayer(self, chain: int, at_altar: bool = False):
        """Apply prayer blessings based on chain score. Higher chain = greater boon."""
        if at_altar and not getattr(self, '_chronicle_first_prayer', False):
            self._chronicle_first_prayer = True
            self._log_chronicle("Prayed at an altar. Something listened. I felt it.")
        _PRAYER_VERSES = {
            0: None,
            1: ("Cast all your anxiety on him, because he cares for you.", "1 Peter 5:7"),
            2: ("If we confess our sins, he is faithful and just to forgive us.", "1 John 1:9"),
            3: ("He heals the brokenhearted and binds up their wounds.", "Psalm 147:3"),
            4: ("Those who hope in the LORD will renew their strength.", "Isaiah 40:31"),
            5: ("The LORD is my shepherd; I shall not want.", "Psalm 23:1"),
            6: ("I can do all things through him who strengthens me.", "Philippians 4:13"),
            7: ("Do not be afraid, for I am with you; I will strengthen you.", "Isaiah 41:10"),
            8: ("Well done, good and faithful servant!", "Matthew 25:23"),
        }
        p = self.player
        effective = chain + (1 if at_altar else 0)

        # L100 altar: holy fire strips Abaddon's resistances
        if self.dungeon_level == 100 and at_altar:
            pos = (p.x, p.y)
            if pos in self._l100_altars_used:
                self.add_message("This altar's holy power has been spent.", 'info')
            elif chain > 0:
                turns = chain * 2
                self.abaddon_resist_removed_turns += turns
                abaddon = next((m for m in self.monsters
                                if m.alive and m.kind == 'abaddon_destroyer'), None)
                if abaddon:
                    abaddon.resistances = []
                    self.add_message(
                        f"Holy fire surges around the Destroyer! "
                        f"His defenses crumble for {turns} turns!", 'success')
                else:
                    self.add_message(
                        "Holy fire blazes forth but finds no target.", 'info')
                self._l100_altars_used.add(pos)
                # Show verse
                verse = _PRAYER_VERSES.get(min(chain, 8))
                if verse:
                    self.add_message(f'"{verse[0]}" — {verse[1]}', 'info')
                p.prayer_cooldown = max(100, 80 + effective * 25)
                return
            else:
                self.add_message("The heavens are silent.", 'info')
                self._l100_altars_used.add(pos)
                return

        # Cooldown scales with how powerful a prayer was answered
        p.prayer_cooldown = max(100, 80 + effective * 25)
        if getattr(p, 'quirk_progress', {}).get('fisher_king_active'):
            p.prayer_cooldown = max(1, p.prayer_cooldown // 2)
        # Fisher King mystery: permanently halved prayer cooldown
        if getattr(p, 'quirk_progress', {}).get('fisher_king_mystery_active'):
            p.prayer_cooldown = max(1, p.prayer_cooldown // 2)

        if effective == 0:
            self.add_message("The heavens are silent.", 'info')
            return

        # Prayer can freeze Death — desperate measure during the chase
        if self.death_pursues and self.death_monster is not None:
            freeze_turns = min(8, 3 + effective)  # 4-8 turns depending on chain
            self.death_monster._frozen_turns = freeze_turns
            self.add_message(
                f"Holy light blazes! Death recoils, frozen for {freeze_turns} turns!", 'success')
            self._log_chronicle(f"Prayed while Death hunted me. It froze in place. {freeze_turns} turns. That's all I get.")

        msgs = []

        if effective >= 8:
            # Perfect/near-perfect chain: permanent stat bonus (diminishing returns)
            if p.prayer_boon_count < 3:
                p.apply_stat_bonus('WIS', 1)
                p.prayer_boon_count += 1
                msgs.append("A divine light fills you. Your wisdom is permanently increased! (WIS +1)")
            else:
                p.hp = p.max_hp
                p.sp = p.max_sp
                msgs.append("Divine grace overflows! You are fully restored!")
            p.hp = p.max_hp
            p.sp = p.max_sp

        elif effective >= 7:
            p.hp = p.max_hp
            p.sp = p.max_sp
            msgs.append("A warm light washes over you. You are fully healed and restored!")

        elif effective >= 6:
            p.sp = p.max_sp
            heal = p.max_hp // 2
            p.hp = min(p.max_hp, p.hp + heal)
            msgs.append(f"Divine grace heals your wounds. (+{heal} HP, SP fully restored)")

        elif effective >= 5:
            sp_gain = int(p.max_sp * 0.6)
            p.sp = min(p.max_sp, p.sp + sp_gain)
            heal = p.max_hp // 5
            p.hp = min(p.max_hp, p.hp + heal)
            msgs.append(f"Your spirit is renewed. (+{sp_gain} SP, +{heal} HP)")

        elif effective >= 4:
            sp_gain = int(p.max_sp * 0.3)
            p.sp = min(p.max_sp, p.sp + sp_gain)
            msgs.append(f"Your stamina is renewed. (+{sp_gain} SP)")

        elif effective >= 3:
            # Cleanse ALL negative status effects
            bad_effects = ['poisoned', 'paralyzed', 'confused', 'bleeding', 'blinded',
                           'sleeping', 'slowed', 'weakened', 'cursed']
            cleared = [e for e in bad_effects if p.has_effect(e)]
            for e in cleared:
                p.status_effects.pop(e, None)
            if cleared:
                msgs.append(f"All afflictions lifted: {', '.join(cleared)}!")
            else:
                sp_gain = p.max_sp // 5
                p.sp = min(p.max_sp, p.sp + sp_gain)
                msgs.append(f"You feel cleansed and refreshed. (+{sp_gain} SP)")

        elif effective >= 2:
            # Remove one major negative status OR uncurse one item
            major = ['poisoned', 'paralyzed', 'blinded']
            removed = next((e for e in major if p.has_effect(e)), None)
            if removed:
                p.status_effects.pop(removed, None)
                msgs.append(f"The {removed} condition is lifted!")
            else:
                cursed_items = []
                for slot in p.armor_slots:
                    if slot and getattr(slot, 'buc', 'uncursed') == 'cursed':
                        cursed_items.append(slot)
                if p.shield and getattr(p.shield, 'buc', 'uncursed') == 'cursed':
                    cursed_items.append(p.shield)
                if p.weapon and getattr(p.weapon, 'buc', 'uncursed') == 'cursed':
                    cursed_items.append(p.weapon)
                if p.ranged_weapon and getattr(p.ranged_weapon, 'buc', 'uncursed') == 'cursed':
                    cursed_items.append(p.ranged_weapon)
                for acc in getattr(p, 'accessory_slots', []):
                    if acc and getattr(acc, 'buc', 'uncursed') == 'cursed':
                        cursed_items.append(acc)
                if cursed_items:
                    for target in cursed_items:
                        target.buc = 'uncursed'
                        target.buc_known = True
                    if len(cursed_items) == 1:
                        msgs.append(f"The curse on your {cursed_items[0].name} is broken!")
                    else:
                        msgs.append(f"Divine light purifies {len(cursed_items)} cursed items!")
                else:
                    minor = ['confused', 'bleeding', 'slowed', 'sleeping']
                    removed = next((e for e in minor if p.has_effect(e)), None)
                    if removed:
                        p.status_effects.pop(removed, None)
                        msgs.append(f"The {removed} condition is lifted!")
                    else:
                        sp_gain = p.max_sp // 10
                        p.sp = min(p.max_sp, p.sp + sp_gain)
                        msgs.append(f"A gentle comfort washes over you. (+{sp_gain} SP)")

        elif effective >= 1:
            minor = ['confused', 'bleeding', 'slowed', 'sleeping']
            removed = next((e for e in minor if p.has_effect(e)), None)
            if removed:
                p.status_effects.pop(removed, None)
                msgs.append(f"The {removed} condition fades away.")
            else:
                sp_gain = p.max_sp // 20
                p.sp = min(p.max_sp, p.sp + sp_gain)
                msgs.append(f"A faint warmth soothes your spirit. (+{sp_gain} SP)")

        for m in msgs:
            self.add_message(m, 'success')

        # Display verse
        verse_key = min(effective, 8)
        verse_data = _PRAYER_VERSES.get(verse_key)
        if verse_data:
            verse_text, citation = verse_data
            self.add_message(f'"{verse_text}"', 'loot')
            self.add_message(f"  -- {citation}", 'info')
