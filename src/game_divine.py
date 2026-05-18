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
    STATE_PLAYER, STATE_QUIZ, STATE_TARGET, STATE_MYSTERY_APPROACH, STATE_PRAY,
)


# ----------------------------------------------------------------------------
# Prayer registry: 8 named intercessions. Each has a lore-only description
# (player extrapolates intent), an optional situational `gate`, a chain-tier
# effect dispatcher in `_resolve_specific_prayer`, and an extra cooldown
# bonus when chain-7/8 fires the strongest tier of the prayer.
# `specialty` prayers refuse at karma <= -6 ("examine your conscience");
# Pater Noster + Ave Maria + Confiteor are always available regardless.
# ----------------------------------------------------------------------------

PRAYERS: list[dict] = [
    {'id': 'pater_noster', 'name': 'Pater Noster',
     'lore': 'The foundational prayer Christ taught his disciples. Universal.',
     'specialty': False, 'cooldown_bonus_full': 0},
    {'id': 'ave_maria', 'name': 'Ave Maria',
     'lore': 'Intercession of the Mother of God; tradition invokes her in moments of mortal danger.',
     'specialty': False, 'cooldown_bonus_full': 400},
    {'id': 'memorare', 'name': 'Memorare',
     'lore': 'The desperate prayer to Mary, said only when every other recourse has failed.',
     'specialty': True, 'cooldown_bonus_full': 0,
     'gate': lambda g: g.player.hp / max(1, g.player.max_hp) < 0.20,
     'gate_reason': 'Said only at the brink — wait until you are gravely wounded.'},
    {'id': 'saint_michael', 'name': 'Prayer to Saint Michael',
     'lore': 'Invocation of the warrior archangel against the powers of darkness.',
     'specialty': True, 'cooldown_bonus_full': 200,
     'gate': lambda g: any(
         m.alive and 'demon' in getattr(m, 'tags', []) and (m.x, m.y) in g.visible
         for m in g.monsters),
     'gate_reason': 'No demonic presence is in sight.'},
    {'id': 'saint_raphael', 'name': 'Litany of Saint Raphael',
     'lore': 'Invocation of the archangel of healing.',
     'specialty': True, 'cooldown_bonus_full': 150},
    {'id': 'saint_anthony', 'name': 'Litany of Saint Anthony',
     'lore': 'Patron of lost things.',
     'specialty': True, 'cooldown_bonus_full': 250,
     'gate': lambda g: any(
         not getattr(it, 'identified', True) for it in g.player.inventory),
     'gate_reason': 'You carry nothing unknown.'},
    {'id': 'anima_christi', 'name': 'Anima Christi',
     'lore': 'Eucharistic prayer of consecration — the soul made one with Christ.',
     'specialty': True, 'cooldown_bonus_full': 0,
     'gate': lambda g: any(
         m.alive and 'undead' in getattr(m, 'tags', []) and (m.x, m.y) in g.visible
         for m in g.monsters),
     'gate_reason': 'No undead are in sight.'},
    {'id': 'confiteor', 'name': 'Confiteor',
     'lore': 'The penitential rite — acknowledgment before grace.',
     'specialty': False, 'cooldown_bonus_full': 0,
     'gate': lambda g: _any_cursed_worn(g.player),
     'gate_reason': 'You wear no cursed gear.'},
]


def _any_cursed_worn(player) -> bool:
    """True if player has at least one worn/wielded cursed item."""
    if player.weapon and getattr(player.weapon, 'buc', '') == 'cursed':
        return True
    if getattr(player, 'ranged_weapon', None) and getattr(player.ranged_weapon, 'buc', '') == 'cursed':
        return True
    if getattr(player, 'shield', None) and getattr(player.shield, 'buc', '') == 'cursed':
        return True
    for slot in (player.armor_slots or []):
        if slot and getattr(slot, 'buc', '') == 'cursed':
            return True
    for acc in (getattr(player, 'accessory_slots', []) or []):
        if acc and getattr(acc, 'buc', '') == 'cursed':
            return True
    if getattr(player, 'amulet_slot', None) and getattr(player.amulet_slot, 'buc', '') == 'cursed':
        return True
    return False


# Karma-tier verses (replaces the single Christian-only chain → verse table).
# Verses shift in tone based on the player's accumulated karma at the moment
# of prayer. Same chain tier, different message.
# Verses are indexed by effective chain (0-5). The escalator quiz caps at
# tier 5 so the chain itself maxes at 5 (max_chain=5). Altar amplification
# and saintly-karma bonuses bump the EFFECTIVE used for bucket lookup but
# the verse table only needs keys 0-5.
_KARMA_VERSES: dict[str, dict[int, tuple[str, str]]] = {
    'saintly': {  # karma +6..+10
        1: ("The LORD is my shepherd; I shall not want.", "Psalm 23:1"),
        2: ("He restoreth my soul.", "Psalm 23:3"),
        3: ("Yea, though I walk through the valley of the shadow of death, I will fear no evil.", "Psalm 23:4"),
        4: ("Thou anointest my head with oil; my cup runneth over.", "Psalm 23:5"),
        5: ("Well done, good and faithful servant.", "Matthew 25:23"),
    },
    'righteous': {  # karma +1..+5
        1: ("Cast all your anxiety on him, because he cares for you.", "1 Peter 5:7"),
        2: ("He heals the brokenhearted and binds up their wounds.", "Psalm 147:3"),
        3: ("Those who hope in the LORD will renew their strength.", "Isaiah 40:31"),
        4: ("I can do all things through him who strengthens me.", "Philippians 4:13"),
        5: ("Do not be afraid, for I am with you; I will strengthen you.", "Isaiah 41:10"),
    },
    'neutral': {  # karma 0
        1: ("Ask, and it shall be given you.", "Matthew 7:7"),
        2: ("Seek, and ye shall find.", "Matthew 7:7"),
        3: ("Knock, and it shall be opened unto you.", "Matthew 7:7"),
        4: ("Trust in the LORD with all thine heart.", "Proverbs 3:5"),
        5: ("In all thy ways acknowledge him, and he shall direct thy paths.", "Proverbs 3:6"),
    },
    'slipping': {  # karma -1..-5
        1: ("Watch and pray, that ye enter not into temptation.", "Matthew 26:41"),
        2: ("The spirit indeed is willing, but the flesh is weak.", "Matthew 26:41"),
        3: ("Be sober, be vigilant; the adversary as a roaring lion walketh about.", "1 Peter 5:8"),
        4: ("Search me, O God, and know my heart.", "Psalm 139:23"),
        5: ("Create in me a clean heart, O God; renew a right spirit within me.", "Psalm 51:10"),
    },
    'fallen': {  # karma -6..-10
        0: ("The heavens are silent. Examine your conscience.", "—"),
        1: ("The wages of sin is death.", "Romans 6:23"),
        2: ("Pride goeth before destruction, and an haughty spirit before a fall.", "Proverbs 16:18"),
        3: ("There is no peace, saith the LORD, unto the wicked.", "Isaiah 48:22"),
        4: ("How art thou fallen from heaven, O Lucifer, son of the morning!", "Isaiah 14:12"),
        5: ("Have mercy upon me, O God, according to thy lovingkindness.", "Psalm 51:1"),
    },
}


def _karma_tier(karma: int) -> str:
    """Map the player's karma to a verse-tier key."""
    if karma >= 6: return 'saintly'
    if karma >= 1: return 'righteous'
    if karma == 0: return 'neutral'
    if karma >= -5: return 'slipping'
    return 'fallen'


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
            max_chain=5,
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
            max_chain=5,
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
        """Open the prayer-selection menu (named intercessions).
        Cooldown-gated; L99 judgment altar still handled directly."""
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

        # Build the prayer menu — evaluate gates and karma refusals.
        karma = getattr(self, 'karma', 0)
        is_fallen = karma <= -6
        is_damned = karma <= -10

        # Damned: only Pater Noster is available.
        # Fallen: specialty prayers refuse. Non-specialty + Confiteor stay.
        items = []
        for spec in PRAYERS:
            entry = {
                'id': spec['id'], 'name': spec['name'], 'lore': spec['lore'],
                'specialty': spec.get('specialty', False),
                'gate_reason': None,
                'available': True,
            }
            # Situational gate
            gate_fn = spec.get('gate')
            if gate_fn is not None:
                try:
                    if not gate_fn(self):
                        entry['available'] = False
                        entry['gate_reason'] = spec.get('gate_reason', 'Not the right moment.')
                except Exception:
                    entry['available'] = False
                    entry['gate_reason'] = 'Not the right moment.'
            # Karma refusals
            if entry['available']:
                if is_damned and spec['id'] != 'pater_noster':
                    entry['available'] = False
                    entry['gate_reason'] = 'The Damned may speak only the Lord’s Prayer.'
                elif is_fallen and entry['specialty']:
                    entry['available'] = False
                    entry['gate_reason'] = 'Examine your conscience.'
            items.append(entry)

        self._prayer_menu_items = items
        self._at_altar = (self.dungeon.tiles[self.player.y][self.player.x] == ALTAR)
        self.state = STATE_PRAY

    def _begin_specific_prayer(self, prayer_id: str):
        """After menu selection: start the theology escalator-chain quiz for
        the chosen prayer; on completion dispatch to that prayer's handler."""
        bonus_desc = " The altar amplifies your prayer." if self._at_altar else ""
        self.add_message(f"You kneel and pray the {prayer_id.replace('_', ' ').title()}.{bonus_desc}", 'info')
        self.quiz_title = f"PRAYER -- THEOLOGY ({prayer_id.replace('_', ' ').upper()})"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            self._resolve_specific_prayer(prayer_id, chain, self._at_altar)
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
            max_chain=5,   # escalator caps at tier 5; chain max matches
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('theology'),
            base_seconds=self.player.get_quiz_timer('theology'),
        )

    def _resolve_specific_prayer(self, prayer_id: str, chain: int, at_altar: bool = False):
        """Dispatch by prayer_id. Each prayer scales effect by chain (1-8).
        Saintly karma adds +1 effective chain (free amplification).
        Powerful chain-7/8 outcomes extend the cooldown via cooldown_bonus_full."""
        if at_altar and not getattr(self, '_chronicle_first_prayer', False):
            self._chronicle_first_prayer = True
            self._log_chronicle("Prayed at an altar. Something listened. I felt it.")

        p = self.player
        karma = getattr(self, 'karma', 0)
        karma_tier = _karma_tier(karma)
        saintly_bonus = 1 if karma_tier == 'saintly' else 0
        effective = chain + (1 if at_altar else 0) + saintly_bonus

        # L100 altar: holy fire strips Abaddon's resistances (any prayer triggers)
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
                self._show_prayer_verse(karma_tier, min(chain, 5))
                p.prayer_cooldown = max(100, 80 + effective * 25)
                return
            else:
                self.add_message("The heavens are silent.", 'info')
                self._l100_altars_used.add(pos)
                return

        # Base cooldown — scales with how loudly the prayer was answered
        p.prayer_cooldown = max(100, 80 + effective * 25)

        if effective == 0:
            # Heavens silent
            if karma_tier == 'fallen':
                self.add_message("The heavens are silent. Examine your conscience.", 'warning')
            else:
                self.add_message("The heavens are silent.", 'info')
            self._apply_prayer_cooldown_quirks()
            return

        # Prayer can freeze Death — desperate measure during the chase
        if self.death_pursues and self.death_monster is not None:
            freeze_turns = min(8, 3 + effective)
            self.death_monster._frozen_turns = freeze_turns
            self.add_message(
                f"Holy light blazes! Death recoils, frozen for {freeze_turns} turns!", 'success')
            self._log_chronicle(
                f"Prayed while Death hunted me. It froze in place. {freeze_turns} turns. That's all I get.")

        # Dispatch to per-prayer handler — each returns (messages, cooldown_bonus_full_fired)
        dispatch = {
            'pater_noster':   self._prayer_pater_noster,
            'ave_maria':      self._prayer_ave_maria,
            'memorare':       self._prayer_memorare,
            'saint_michael':  self._prayer_saint_michael,
            'saint_raphael':  self._prayer_saint_raphael,
            'saint_anthony':  self._prayer_saint_anthony,
            'anima_christi':  self._prayer_anima_christi,
            'confiteor':      self._prayer_confiteor,
        }
        handler = dispatch.get(prayer_id, self._prayer_pater_noster)
        msgs, fired_full_effect = handler(effective, chain)

        # Apply cooldown bonus if the prayer fired its strongest tier
        if fired_full_effect:
            spec = next((s for s in PRAYERS if s['id'] == prayer_id), None)
            if spec:
                p.prayer_cooldown += spec.get('cooldown_bonus_full', 0)

        self._apply_prayer_cooldown_quirks()

        for m in msgs:
            self.add_message(m, 'success')

        # Karma-tiered verse
        # Cap verse lookup at chain 5 (the table's highest key); deeper
        # effective values still grant mechanical bonuses but reuse the
        # chain-5 verse for the player-visible flavor text.
        self._show_prayer_verse(karma_tier, min(effective, 5))

    def _apply_prayer_cooldown_quirks(self):
        """Fisher King quirks halve cooldown (stacking)."""
        p = self.player
        if getattr(p, 'quirk_progress', {}).get('fisher_king_active'):
            p.prayer_cooldown = max(1, p.prayer_cooldown // 2)
        if getattr(p, 'quirk_progress', {}).get('fisher_king_mystery_active'):
            p.prayer_cooldown = max(1, p.prayer_cooldown // 2)

    def _show_prayer_verse(self, karma_tier: str, key: int):
        verse = _KARMA_VERSES.get(karma_tier, {}).get(key)
        if not verse:
            return
        text, citation = verse
        self.add_message(f'"{text}"', 'loot')
        self.add_message(f"  -- {citation}", 'info')

    # ------------------------------------------------------------------
    # Per-prayer handlers — each returns (messages, fired_full_effect)
    # ------------------------------------------------------------------

    def _prayer_pater_noster(self, effective: int, raw_chain: int) -> tuple[list, bool]:
        """The Our Father — universal workhorse. 3 tiers based on effective
        (chain + altar + saintly), with a 'perfect chain 5' extra reward."""
        p = self.player
        msgs = []
        fired_full = False
        if effective >= 5:
            # Full effect: full restoration + cleanse
            p.hp = p.max_hp
            p.sp = p.max_sp
            bad = ['poisoned', 'paralyzed', 'confused', 'bleeding', 'blinded',
                   'sleeping', 'slowed', 'weakened']
            for e in bad:
                p.status_effects.pop(e, None)
            msgs.append("A warm light washes over you. Fully healed, restored, and cleansed!")
            fired_full = True
            # Perfect chain (raw 5): the rare permanent boon, up to 3 times per run
            if raw_chain >= 5 and p.prayer_boon_count < 3:
                p.apply_stat_bonus('WIS', 1)
                p.prayer_boon_count += 1
                msgs.append("Divine light fills you. Your wisdom is permanently increased! (WIS +1)")
        elif effective >= 3:
            sp_gain = int(p.max_sp * 0.5)
            heal = p.max_hp // 3
            p.sp = min(p.max_sp, p.sp + sp_gain)
            p.hp = min(p.max_hp, p.hp + heal)
            # Try to lift a major status
            bad = ['poisoned', 'paralyzed', 'blinded']
            removed = next((e for e in bad if p.has_effect(e)), None)
            if removed:
                p.status_effects.pop(removed, None)
                msgs.append(f"Your spirit is renewed. (+{sp_gain} SP, +{heal} HP, lifted {removed})")
            else:
                msgs.append(f"Your spirit is renewed. (+{sp_gain} SP, +{heal} HP)")
        else:
            sp_gain = p.max_sp // 10
            p.sp = min(p.max_sp, p.sp + sp_gain)
            msgs.append(f"A gentle comfort washes over you. (+{sp_gain} SP)")
        return msgs, fired_full

    def _prayer_ave_maria(self, effective: int, raw_chain: int) -> tuple[list, bool]:
        """Hail Mary — Marian intercession. life_save granted at full."""
        p = self.player
        msgs = []
        fired_full = False
        if effective >= 5:
            p.add_effect('shielded', 20)
            p.add_effect('life_save', -1)   # one-shot revive
            msgs.append("The Virgin's protection settles upon you — shielded, and one death is forgiven.")
            fired_full = True
        elif effective >= 3:
            p.add_effect('shielded', 15)
            msgs.append("Mary's grace surrounds you — shielded for 15 turns.")
        else:
            p.add_effect('shielded', 5)
            msgs.append("A brief moment of protection — shielded for 5 turns.")
        return msgs, fired_full

    def _prayer_memorare(self, effective: int, raw_chain: int) -> tuple[list, bool]:
        """The desperate prayer to Mary — gated on HP < 20%.
        Full effect: full heal + paralyze adjacent. No time_freeze."""
        p = self.player
        msgs = []
        if effective >= 5:
            p.hp = p.max_hp
            paralyzed = 0
            for m in self.monsters:
                if not m.alive: continue
                if abs(m.x - p.x) <= 1 and abs(m.y - p.y) <= 1:
                    m.add_effect('paralyzed', 3)
                    paralyzed += 1
            msgs.append(f"Mary herself answers — full restoration; {paralyzed} foes paralyzed for 3 turns.")
        elif effective >= 3:
            heal = p.max_hp // 2
            p.hp = min(p.max_hp, p.hp + heal)
            slowed = 0
            for m in self.monsters:
                if not m.alive: continue
                if abs(m.x - p.x) <= 1 and abs(m.y - p.y) <= 1:
                    m.add_effect('slowed', 3)
                    slowed += 1
            msgs.append(f"A reprieve — {heal} HP restored; {slowed} adjacent foes slowed.")
        else:
            heal = p.max_hp // 4
            p.hp = min(p.max_hp, p.hp + heal)
            msgs.append(f"The Virgin grants a small breath — {heal} HP restored.")
        return msgs, False

    def _prayer_saint_michael(self, effective: int, raw_chain: int) -> tuple[list, bool]:
        """Smite visible demons — scope grows with chain."""
        p = self.player
        msgs = []
        fired_full = False
        demons = [m for m in self.monsters
                  if m.alive and 'demon' in getattr(m, 'tags', [])
                  and (m.x, m.y) in self.visible]
        if not demons:
            msgs.append("The archangel's sword finds no demon to strike.")
            return msgs, False
        damage = max(1, p.INT * max(1, effective))
        if effective >= 5:
            targets = demons
            fired_full = True
        elif effective >= 3:
            targets = sorted(demons, key=lambda m: m.hp)[:2]
        else:
            targets = [min(demons, key=lambda m: abs(m.x - p.x) + abs(m.y - p.y))]
        kills = 0
        for tgt in targets:
            tgt.take_damage(damage, 'holy')
            if not tgt.alive:
                self._on_monster_killed(tgt)
                kills += 1
        msgs.append(f"Saint Michael's sword smites {len(targets)} demon(s) for {damage} holy damage each! ({kills} slain)")
        return msgs, fired_full

    def _prayer_saint_raphael(self, effective: int, raw_chain: int) -> tuple[list, bool]:
        """Healing archangel — scope grows with chain."""
        p = self.player
        msgs = []
        fired_full = False
        cured = []
        if effective >= 5:
            for e in ['poisoned', 'paralyzed', 'confused', 'bleeding', 'blinded',
                      'sleeping', 'slowed', 'weakened', 'cursed', 'diseased', 'burning']:
                if p.has_effect(e):
                    p.status_effects.pop(e, None)
                    cured.append(e)
            p.hp = p.max_hp
            msgs.append(f"Raphael's healing flame: full restoration"
                        + (f" + cured {', '.join(cured)}." if cured else "."))
            fired_full = True
        elif effective >= 3:
            for e in ['poisoned', 'diseased', 'bleeding']:
                if p.has_effect(e):
                    p.status_effects.pop(e, None)
                    cured.append(e)
            heal = p.max_hp // 2
            p.hp = min(p.max_hp, p.hp + heal)
            msgs.append(f"Raphael steadies your wounds — {heal} HP restored"
                        + (f", cured {', '.join(cured)}." if cured else "."))
        else:
            heal = p.max_hp // 5
            p.hp = min(p.max_hp, p.hp + heal)
            if p.has_effect('poisoned'):
                p.status_effects.pop('poisoned', None)
                cured.append('poisoned')
            msgs.append(f"A small mercy — {heal} HP restored"
                        + (f", cured {cured[0]}." if cured else "."))
        return msgs, fired_full

    def _prayer_saint_anthony(self, effective: int, raw_chain: int) -> tuple[list, bool]:
        """Identify unknown items — count scales with chain."""
        p = self.player
        msgs = []
        fired_full = False
        unknown = [it for it in p.inventory if not getattr(it, 'identified', True)]
        if not unknown:
            return ["You carry nothing unknown."], False
        if effective >= 5:
            count = len(unknown)
            fired_full = True
        elif effective >= 3:
            count = min(len(unknown), 3)
        else:
            count = min(len(unknown), 1)
        for it in unknown[:count]:
            it.identified = True
            if hasattr(p, 'known_item_ids'):
                p.known_item_ids.add(getattr(it, 'id', ''))
        msgs.append(f"Saint Anthony reveals {count} hidden thing{'s' if count != 1 else ''} in your pack.")
        return msgs, fired_full

    def _prayer_anima_christi(self, effective: int, raw_chain: int) -> tuple[list, bool]:
        """Paralyze nearby undead — scope grows with chain."""
        p = self.player
        msgs = []
        fired_full = False
        undead = [m for m in self.monsters
                  if m.alive and 'undead' in getattr(m, 'tags', [])
                  and (m.x, m.y) in self.visible]
        if not undead:
            return ["No undead respond to the Soul of Christ."], False
        if effective >= 5:
            targets = [m for m in undead if abs(m.x - p.x) <= 5 and abs(m.y - p.y) <= 5]
            duration = 5
            fired_full = True
        elif effective >= 3:
            targets = sorted(undead, key=lambda m: abs(m.x - p.x) + abs(m.y - p.y))[:2]
            duration = 4
        else:
            targets = [min(undead, key=lambda m: abs(m.x - p.x) + abs(m.y - p.y))]
            duration = 3
        for tgt in targets:
            tgt.add_effect('paralyzed', duration)
        msgs.append(f"The Soul of Christ paralyzes {len(targets)} undead for {duration} turns.")
        return msgs, fired_full

    def _prayer_confiteor(self, effective: int, raw_chain: int) -> tuple[list, bool]:
        """Uncurse worn cursed items — count scales with chain.
        No karma effect (sin reduction explicitly out of scope)."""
        p = self.player
        cursed_items = []
        for slot in (p.armor_slots or []):
            if slot and getattr(slot, 'buc', '') == 'cursed':
                cursed_items.append(slot)
        if p.shield and getattr(p.shield, 'buc', '') == 'cursed':
            cursed_items.append(p.shield)
        if p.weapon and getattr(p.weapon, 'buc', '') == 'cursed':
            cursed_items.append(p.weapon)
        if getattr(p, 'ranged_weapon', None) and getattr(p.ranged_weapon, 'buc', '') == 'cursed':
            cursed_items.append(p.ranged_weapon)
        for acc in (getattr(p, 'accessory_slots', []) or []):
            if acc and getattr(acc, 'buc', '') == 'cursed':
                cursed_items.append(acc)
        if getattr(p, 'amulet_slot', None) and getattr(p.amulet_slot, 'buc', '') == 'cursed':
            cursed_items.append(p.amulet_slot)
        if not cursed_items:
            return ["You wear no cursed gear."], False
        if effective >= 5:
            n = len(cursed_items)
            for it in cursed_items:
                it.buc = 'uncursed'
                it.buc_known = True
            sp_gain = p.max_sp // 4
            p.sp = min(p.max_sp, p.sp + sp_gain)
            return [f"All {n} cursed items purified. (+{sp_gain} SP)"], True
        elif effective >= 3:
            n = min(len(cursed_items), 3)
            for it in cursed_items[:n]:
                it.buc = 'uncursed'
                it.buc_known = True
            return [f"{n} cursed item{'s' if n != 1 else ''} purified."], False
        else:
            it = cursed_items[0]
            it.buc = 'uncursed'
            it.buc_known = True
            return [f"The curse on your {it.name} is broken."], False

