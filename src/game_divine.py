"""Game's religious / divine action handlers, extracted from main.py.

This module defines :class:`DivineMixin`, which the real ``Game`` class
inherits alongside the other mixins.  It owns the Game-side orchestration
of:

  * Simple prayer (``_start_pray``) -- one theology escalator_chain quiz,
    stacking bonuses at chain 1..5, karma modifies magnitudes,
    altar doubles them.
  * Divine Intercession (``_start_divine_intercession``) -- once per game,
    the "big ask": on-altar = escalator_chain(1); off-altar = threshold(5)
    at T5. Success = full heal + invulnerable + random artifact. Failure =
    all-worn cursed + blinded 100t.
  * Altar drop-reveal (``_altar_drop_reveal``) -- karma-gated BUC reveal
    with truthful positive-karma and deceptive negative-karma messages.
  * Named-god shrines (Ariadne, Athena, Odin) and the Fenrir-quest forge
    checks (``_check_gleipnir_forge``, ``_check_vidar_altar``).
  * Fountain / grave / throne tile interactions and their resolutions.
  * Mystery-altar orchestration (``_find_adjacent_mystery_altar``,
    ``_start_observe``, ``_start_mystery``, ``_begin_mystery_challenge``).

v2.13.0 (2026-09-06) SIMPLIFICATION:
  - Removed: PRAYERS registry (9 named intercessions), 9 per-prayer
    handlers, ``_begin_specific_prayer``, ``_resolve_specific_prayer``,
    ``_altar_buc_upgrade``, ``_altar_buc_identify``, STATE_PRAY,
    the prayer-picker menu.
  - The "big ask" (BUC identify at altar) is now Divine Intercession,
    bound to Shift+\\, one attempt per run.

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
    STATE_INTERCESSION_PROMPT,
)


# ----------------------------------------------------------------------------
# Module-level helpers for altar / equipped-item introspection.
# `_on_altar` is used by the drop-reveal + Divine-Intercession paths.
# `_iter_equipped` centralises the "for every worn item, do X" loop that
# both drop-reveal (locating cursed) and Divine Intercession failure
# (smite: curse every worn item) need.
# ----------------------------------------------------------------------------


def _on_altar(g) -> bool:
    """True iff the player is standing on an ALTAR tile."""
    try:
        return g.dungeon.tiles[g.player.y][g.player.x] == ALTAR
    except Exception:
        return False


def _iter_equipped(player):
    """Yield every currently-equipped item (weapon, ranged, shield, armor
    slots, accessory slots, amulet, belt). Used by Divine Intercession
    (smite path) and by simple-prayer chain-4 (find first worn cursed)."""
    if getattr(player, 'weapon', None):
        yield player.weapon
    if getattr(player, 'ranged_weapon', None):
        yield player.ranged_weapon
    if getattr(player, 'shield', None):
        yield player.shield
    for slot in (getattr(player, 'armor_slots', None) or []):
        if slot:
            yield slot
    for acc in (getattr(player, 'accessory_slots', None) or []):
        if acc:
            yield acc
    if getattr(player, 'amulet_slot', None):
        yield player.amulet_slot
    if getattr(player, 'belt_slot', None):
        yield player.belt_slot


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
    # Altar drop-reveal (v2.13.0)  — dropping an item on an ALTAR now
    # REVEALS its BUC based on karma, with the reveal being TRUTHFUL at
    # positive karma and DECEPTIVE at negative karma. Uncursed items
    # produce no message either way. There is no quiz — the reveal is a
    # passive divine action, not an intercession the player asks for.
    # Positive-karma cursed items are also CONSUMED (the altar destroys
    # the item and its curse). Called from ``_finish_drop`` in main.py.
    # ------------------------------------------------------------------

    def _altar_drop_reveal(self, item):
        """Handle the divine-reveal side effect of dropping ``item`` on an
        ALTAR tile. Returns True if the item was CONSUMED by the altar
        (positive-karma cursed → destroyed) so the caller can remove it
        from ``ground_items``. Item mutation (buc_known) happens here.
        """
        # Items without a BUC field (quest items, gold, etc.) are silent.
        if not hasattr(item, 'buc'):
            return False
        karma = int(getattr(self, 'karma', 0) or 0)
        buc = getattr(item, 'buc', 'uncursed')
        display = self._display_name(item)

        if karma == 0:
            # Neutral: God gives no sign either way.
            return False

        if karma > 0:
            # Truthful reveal. Cursed items are consumed by the altar; the
            # curse is lifted from the world. Blessed items have their BUC
            # revealed and stay on the ground. Uncursed items are silent.
            if buc == 'cursed':
                self.add_message(
                    f"The {display} is drawn into a black aura — the altar consumes it. "
                    "The curse is lifted from the world.",
                    'success')
                return True   # caller removes from ground_items
            if buc == 'blessed':
                item.buc_known = True
                self.add_message(
                    f"The {display} glows with a holy light — it is truly blessed.",
                    'success')
                return False
            # uncursed → silent
            return False

        # karma < 0: deceptive reveal — God does not help the wicked. The
        # messages LIE. Real buc/buc_known are UNCHANGED so the player is
        # tempted to trust a bad signal.
        if buc == 'cursed':
            self.add_message(
                f"The {display} glows with a holy light — it must be blessed.",
                'success')
            return False
        if buc == 'blessed':
            self.add_message(
                f"The {display} is drawn into a black aura — the altar consumes it.",
                'warning')
            return False
        # uncursed → silent
        return False

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
    # Simple Prayer  (\ key -- theology escalator_chain quiz, one call)
    # ------------------------------------------------------------------
    #
    # v2.13.0 SIMPLIFICATION: the multi-prayer picker is gone. Pressing \\
    # directly launches a theology escalator_chain quiz (max 5). Bonuses
    # STACK at each chain tier:
    #
    #   chain >= 1 : restore SP  (~25% max)
    #   chain >= 2 : + restore HP (~25% max)
    #   chain >= 3 : + restore MP (~25% max)
    #   chain >= 4 : + uncurse ONE worn cursed item, OR (if none worn cursed)
    #                bless one random unblessed inventory item
    #   chain >= 5 : + grant 'shielded' status for 20 turns (+3 AC)
    #
    # Karma modifies MAGNITUDES (not access) and is DOUBLED at altars.
    # L100 holy fire is preserved (chain >= 1 at L100 altar still strips
    # Abaddon's resistances for chain*2 turns).
    # Karma-tiered verse still shows.

    def _start_pray(self):
        """Launch simple prayer directly — theology escalator_chain, no menu.
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

        at_altar = _on_altar(self)
        bonus_desc = " The altar amplifies your prayer." if at_altar else ""
        self.add_message(f"You kneel and pray.{bonus_desc}", 'info')
        self.quiz_title = "PRAYER -- THEOLOGY"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            self._resolve_simple_prayer(chain, at_altar)
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

    def _resolve_simple_prayer(self, chain: int, at_altar: bool = False):
        """Apply the stacking simple-prayer bonuses.

        - Each chain tier ADDS its bonus (they do not replace each other).
        - Karma scales magnitudes; altar DOUBLES the karma delta (positive
          AND negative). Chain-0 (or worse) plays the karma-tier silent-
          heavens message.
        - Cooldown = max(100, 100 + 25 * effective) where effective is
          chain + (1 if at_altar else 0). Fisher King quirks halve.
        - L100 altar preserves the holy-fire Abaddon-resist strip.
        """
        if at_altar and not getattr(self, '_chronicle_first_prayer', False):
            self._chronicle_first_prayer = True
            self._log_chronicle("Prayed at an altar. Something listened. I felt it.")

        p = self.player
        karma = int(getattr(self, 'karma', 0) or 0)
        karma_tier = _karma_tier(karma)
        effective = chain + (1 if at_altar else 0)

        # L100 altar holy-fire strip — preserved from v2.12 behaviour.
        if self.dungeon_level == 100 and at_altar:
            pos = (p.x, p.y)
            if pos in self._l100_altars_used:
                self.add_message("This altar's holy power has been spent.", 'info')
                # Still show a verse + set cooldown so the turn doesn't feel wasted.
                self._show_prayer_verse(karma_tier, min(chain, 5))
                p.prayer_cooldown = max(100, 100 + 25 * effective)
                self._apply_prayer_cooldown_quirks()
                return
            if chain > 0:
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
                # Fall through so the stacking bonuses ALSO apply.

        # Cooldown baseline — set once, quirks halve at the end.
        p.prayer_cooldown = max(100, 100 + 25 * effective)

        if chain <= 0:
            if karma_tier == 'fallen':
                self.add_message("The heavens are silent. Examine your conscience.", 'warning')
            else:
                self.add_message("The heavens are silent.", 'info')
            self._apply_prayer_cooldown_quirks()
            self._show_prayer_verse(karma_tier, 0 if karma_tier == 'fallen' else 1)
            return

        # Karma bonuses (base). At altar we DOUBLE the raw karma before applying.
        karma_for_bonuses = karma * 2 if at_altar else karma
        karma_bonus_sp   = max(-15, karma_for_bonuses)
        karma_bonus_hp   = max(-15, karma_for_bonuses)
        karma_bonus_mp   = max(-5,  karma_for_bonuses // 2)
        karma_bonus_buff = max(-15, karma_for_bonuses * 3)

        msgs: list[tuple[str, str]] = []

        # ---- chain >= 1: SP restore ----
        sp_amt = max(15, p.max_sp // 4) + karma_bonus_sp
        if sp_amt > 0:
            p.restore_sp(sp_amt)
            msgs.append((f"Strength floods back into your limbs. (+{sp_amt} SP)", 'success'))
        elif sp_amt < 0:
            # Rare: negative karma so severe the "restore" nets a loss. Guard
            # the SP floor at 0 and describe the failure honestly.
            drain = min(p.sp, -sp_amt)
            p.sp = max(0, p.sp - drain)
            msgs.append((f"Your prayer is answered coldly — strength drains from you. (-{drain} SP)", 'warning'))

        # ---- chain >= 2: HP restore ----
        if chain >= 2:
            hp_amt = max(15, p.max_hp // 4) + karma_bonus_hp
            if hp_amt > 0:
                gained = p.restore_hp(hp_amt)
                if gained > 0:
                    msgs.append((f"Warmth washes over your wounds. (+{gained} HP)", 'success'))
                else:
                    msgs.append(("Warmth washes over you, but your wounds refuse to close.", 'info'))
            elif hp_amt < 0:
                dmg = min(p.hp - 1, -hp_amt) if p.hp > 1 else 0
                if dmg > 0:
                    p.hp = max(1, p.hp - dmg)
                    msgs.append((f"Divine coldness bites at you. (-{dmg} HP)", 'warning'))

        # ---- chain >= 3: MP restore ----
        if chain >= 3:
            mp_amt = max(5, p.max_mp // 4) + karma_bonus_mp
            if mp_amt > 0:
                p.restore_mp(mp_amt)
                msgs.append((f"Arcane wells refill within you. (+{mp_amt} MP)", 'success'))
            elif mp_amt < 0:
                drain = min(p.mp, -mp_amt)
                p.mp = max(0, p.mp - drain)
                msgs.append((f"The magic ebbs from you. (-{drain} MP)", 'warning'))

        # ---- chain >= 4: uncurse OR bless ----
        if chain >= 4:
            # At karma <= -5 the gift is refused outright.
            if karma <= -5:
                msgs.append(("You offer a gift, but God turns away from it.", 'warning'))
            else:
                bless_count = 1 + max(0, karma // 3)
                first_cursed = next(
                    (it for it in _iter_equipped(p)
                     if getattr(it, 'buc', '') == 'cursed'),
                    None,
                )
                if first_cursed is not None:
                    first_cursed.buc = 'uncursed'
                    first_cursed.buc_known = True
                    msgs.append(
                        (f"The curse on your {getattr(first_cursed, 'name', 'gear')} is broken.",
                         'success'))
                else:
                    candidates = [it for it in (p.inventory or [])
                                  if hasattr(it, 'buc') and getattr(it, 'buc', '') != 'blessed']
                    if candidates:
                        chosen = random.sample(
                            candidates, k=min(bless_count, len(candidates)))
                        for it in chosen:
                            it.buc = 'blessed'
                            it.buc_known = True
                        if len(chosen) == 1:
                            msgs.append(
                                (f"A holy light suffuses the {getattr(chosen[0], 'name', 'item')} in your pack.",
                                 'success'))
                        else:
                            msgs.append(
                                (f"A holy light suffuses {len(chosen)} items in your pack.",
                                 'success'))
                    else:
                        msgs.append(("Every item you carry already bears a blessing.", 'info'))

        # ---- chain >= 5: shielded buff ----
        if chain >= 5:
            duration = max(1, 20 + karma_bonus_buff)
            p.add_effect('shielded', duration)
            msgs.append(
                (f"A translucent barrier settles around you. (shielded {duration}t)",
                 'success'))

        self._apply_prayer_cooldown_quirks()

        for text, kind in msgs:
            self.add_message(text, kind)

        # Karma-tiered verse. The table peaks at chain 5 (its highest key).
        self._show_prayer_verse(karma_tier, min(chain, 5))

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
    # Divine Intercession  (Shift+\ -- once per game, the "big ask")
    # ------------------------------------------------------------------
    #
    # NOT gated by prayer_cooldown. Gated by ``player.divine_intercession_used``
    # — one attempt per RUN, success or failure. The Y/N prompt asks the
    # player to confirm they want to spend their one intercession before
    # any quiz launches. On confirmation:
    #
    #   On altar : escalator_chain theology tier 1 (max 5). Success needs
    #              chain >= 1. Easier by design — the altar carries the
    #              weight.
    #   Off altar: threshold theology tier 5, threshold=5, total_qs=5 —
    #              five T5 theology questions in a row, all must be right.
    #
    # Success -> full HP/MP/SP restore, all non-item debuffs cleared,
    # ``invulnerable`` 10t, random unspawned Artifact placed at feet.
    # Failure -> every equipped item cursed + buc_known True, ``blinded``
    # 100t.

    def _start_divine_intercession(self):
        """Kick off the Y/N confirmation for Divine Intercession. Once-per-run
        gate is checked HERE so a second press wastes no state."""
        if getattr(self.player, 'divine_intercession_used', False):
            self.add_message(
                "You have already sought intercession this run. God's ear is not for spam.",
                'warning')
            return
        # Enter the confirm-prompt state; rendering + input live in
        # game_render / game_input.
        self.state = STATE_INTERCESSION_PROMPT

    def _confirm_divine_intercession(self, accept: bool):
        """Y/N handler for Divine Intercession. ``accept`` False -> silent
        cancel. ``accept`` True -> mark the run used and launch the quiz
        (altar-easy or off-altar-hard). Called from game_input."""
        if not accept:
            self.state = STATE_PLAYER
            self.add_message("You step back from the altar's edge.", 'info')
            return
        # Belt-and-braces: recheck the once-per-run gate.
        if getattr(self.player, 'divine_intercession_used', False):
            self.state = STATE_PLAYER
            self.add_message(
                "You have already sought intercession this run. God's ear is not for spam.",
                'warning')
            return
        # LOCK the attempt now — even a bail-out via failed quiz counts.
        self.player.divine_intercession_used = True

        at_altar = _on_altar(self)
        self.add_message(
            "You raise your voice to Heaven and beg for intercession...",
            'info')
        self.quiz_title = "DIVINE INTERCESSION -- THEOLOGY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            # For altar path (escalator_chain), success = chain >= 1.
            # For off-altar (threshold=5), success = result.success.
            if at_altar:
                success = getattr(result, 'score', 0) >= 1
            else:
                success = bool(getattr(result, 'success', False))
            if success:
                self._resolve_intercession_success()
            else:
                self._resolve_intercession_failure()
            self._advance_turn()

        if at_altar:
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
        else:
            self.quiz_engine.start_quiz(
                mode='threshold',
                subject='theology',
                tier=5,
                callback=on_complete,
                threshold=5,
                total_qs=5,
                wisdom=self.player.WIS,
                timer_modifier=self.player.get_quiz_timer_modifier(),
                extra_seconds=self.player.get_quiz_extra_seconds('theology'),
                base_seconds=self.player.get_quiz_timer('theology'),
            )

    # Non-item debuffs cleared on successful intercession. In practice this
    # is EVERY known debuff — the intent is "poisons flee, wounds close",
    # not "except this cursed ring". Item-bound curse effects are on the
    # ITEM, not in status_effects, so this iterates ALL active statuses in
    # DEBUFFS.
    def _resolve_intercession_success(self):
        """Full-restore + invulnerable 10t + spawn random artifact at feet."""
        p = self.player
        p.hp = p.max_hp
        p.mp = p.max_mp
        p.sp = p.max_sp
        # Clear every DEBUFF-registered status effect. Item-bound curse
        # slots (if any exist) are stored on the item itself, not in
        # status_effects, so this is safe.
        try:
            from status_effects import DEBUFFS
            for eff in list(p.status_effects.keys()):
                if eff in DEBUFFS:
                    p.status_effects.pop(eff, None)
        except ImportError:
            pass
        # Grant invulnerable for 10 turns.
        p.add_effect('invulnerable', 10)
        # Spawn artifact at player feet.
        art_name = self._spawn_intercession_artifact(p.x, p.y)
        if art_name:
            self.add_message(
                f"THE HEAVENS OPEN. God's grace pours over you — wounds close, "
                f"poisons flee, and a {art_name} materializes at your feet, "
                "gift from the Most High.",
                'loot')
            self._log_chronicle(
                f"Sought divine intercession and was answered. Fully restored. "
                f"God set a {art_name} at my feet."
            )
        else:
            # No artifact could be found even from unique pool — should be
            # extremely rare. Still announce the heal.
            self.add_message(
                "THE HEAVENS OPEN. God's grace pours over you — wounds close, "
                "poisons flee, and a divine calm settles on you.",
                'loot')
            self._log_chronicle(
                "Sought divine intercession and was answered. Fully restored. "
                "No relic came — the Most High set peace at my feet instead."
            )

    def _resolve_intercession_failure(self):
        """SMITE: curse every equipped item + blinded 100t."""
        p = self.player
        for it in _iter_equipped(p):
            if hasattr(it, 'buc'):
                it.buc = 'cursed'
                it.buc_known = True
        p.add_effect('blinded', 100)
        self.add_message(
            "THE HEAVENS DARKEN. God strikes you for your arrogance — "
            "your gear reeks of curse and your eyes go dark.",
            'danger')
        self._log_chronicle(
            "Sought intercession without the merit. God smote me. "
            "Everything I wore turned cursed. I could not see for a hundred turns."
        )

    def _spawn_intercession_artifact(self, px: int, py: int) -> str:
        """Place a random UNSPAWNED Artifact at (px, py) and return its name.

        Prefers artifacts not currently on the map or in the player's
        inventory (avoids duplicating a unique already in play). Falls back
        to any is_unique item if the artifact pool is exhausted. Returns
        the item name (for the announce/chronicle message) or '' on total
        failure."""
        from items import Artifact, load_items, copy_at

        def _in_play(item_id: str) -> bool:
            for g in getattr(self, 'ground_items', []) or []:
                if getattr(g, 'id', '') == item_id:
                    return True
            for it in getattr(self.player, 'inventory', []) or []:
                if getattr(it, 'id', '') == item_id:
                    return True
            for it in _iter_equipped(self.player):
                if getattr(it, 'id', '') == item_id:
                    return True
            return False

        # Primary pool: artifact.json entries not already in play.
        try:
            templates = load_items('artifact')
        except (FileNotFoundError, Exception):
            templates = []
        pool = [t for t in templates if not _in_play(getattr(t, 'id', ''))]
        if pool:
            tpl = random.choice(pool)
            inst = copy_at(tpl, px, py)
            inst.identified = True
            if hasattr(inst, 'buc'):
                inst.buc = 'blessed'
                inst.buc_known = True
            self.ground_items.append(inst)
            return getattr(inst, 'name', 'divine artifact')

        # Fallback: any is_unique item across the main equippable classes.
        fallback_pool: list = []
        for cls in ('weapon', 'armor', 'shield', 'accessory'):
            try:
                fallback_pool.extend(
                    t for t in load_items(cls)
                    if getattr(t, 'is_unique', False)
                    and not _in_play(getattr(t, 'id', ''))
                )
            except (FileNotFoundError, Exception):
                pass
        if fallback_pool:
            tpl = random.choice(fallback_pool)
            inst = copy_at(tpl, px, py)
            inst.identified = True
            if hasattr(inst, 'buc'):
                inst.buc = 'blessed'
                inst.buc_known = True
            self.ground_items.append(inst)
            return getattr(inst, 'name', 'divine relic')
        return ''
