"""item_actions.py -- the item actions shared by the Kit (K) and the
character sheet (@).

Both screens act on ONE selected item with the same keys:

    E  Equip, or Unequip when the item is worn (a toggle). A floor item on
       the Kit is picked up first, then equipped.
    D  Drop. A worn item is unequipped first, then dropped.
    I  Identify (one philosophy question; needs the Philosopher's Shard,
       exactly like the I menu).
    X  Read the item's lore.

Every action goes through the game's own paths (``_equip_item``,
``_unequip_slot``, ``_pickup``, ``_do_drop_item``, ``_identify_item``), so
turn cost, quiz gating, curses, weight and messages are exactly those of the
map commands. Nothing here decides an outcome; it only routes the key and
then brings the player back.

Returning: an action remembers the screen it came from (tab, focus and the
selected item). When the action's flow is over -- at once, or after the equip
quiz, the stack-quantity prompt or the lore screen -- the player is put back
on that screen with the same item selected (or the nearest row when the item
left the list). The messages the action wrote are kept and shown on the
screen, so the quiz result is read where the player is looking.
"""

from __future__ import annotations

from game_states import (
    STATE_PLAYER, STATE_QUIZ, STATE_QUIZ_CONTEXT, STATE_LORE,
    STATE_DROP_QTY_INPUT, STATE_KIT, STATE_CHARACTER_SHEET,
)


# States an action may pass through on its way back to the screen. Any other
# state (death, a story popup, a boon menu) ends the return: the player is
# left where the game put them.
_TRANSIT_STATES = frozenset((
    STATE_PLAYER, STATE_QUIZ, STATE_QUIZ_CONTEXT, STATE_LORE,
    STATE_DROP_QTY_INPUT, STATE_KIT, STATE_CHARACTER_SHEET,
))

# Keys, in the order the screens show them.
ACTION_KEYS = (('equip', 'E'), ('drop', 'D'), ('identify', 'I'), ('lore', 'X'))


class ItemActionsMixin:
    """Mixed into Game. Pure routing over the existing item paths."""

    # ------------------------------------------------------------------
    # What can be done with an item
    # ------------------------------------------------------------------

    def _item_where(self, item) -> str:
        """'equip' when worn, 'pack' when carried, 'floor' when on this tile,
        '' otherwise."""
        if item is None:
            return ''
        if self._lore_equipped_slot(item):
            return 'equip'
        if any(i is item for i in self.player.inventory):
            return 'pack'
        px, py = self.player.x, self.player.y
        for it in getattr(self, 'ground_items', []) or []:
            if it is item and getattr(it, 'x', None) == px and getattr(it, 'y', None) == py:
                return 'floor'
        return ''

    @staticmethod
    def _item_known_unremovable(item) -> str:
        """Why a worn item visibly cannot come off, or ''. Only what the
        player can already see: an unknown curse is found by trying, exactly
        as on the map."""
        if item is None:
            return ''
        if getattr(item, 'bound_to_wielder', False):
            return "It is a part of you"
        if getattr(item, 'cursed', False) and getattr(item, 'buc_known', False):
            return "Cursed, it will not come off"
        return ''

    def _item_equip_block(self, item) -> str:
        """A reason the equip would be refused that the player can already
        see, or ''. Mirrors the checks at the top of ``_equip_item`` and
        ``_equip_accessory``; pressing E still runs the real path."""
        from items import Weapon, Armor, Shield, Accessory, ARMOR_SLOTS
        p = self.player
        if isinstance(item, Weapon):
            if getattr(item, 'two_handed', False) and p.shield is not None:
                why = self._item_known_unremovable(p.shield)
                if why:
                    return "Your shield is cursed to your arm"
            is_ranged = getattr(item, 'requires_ammo', None) is not None
            cur = p.ranged_weapon if is_ranged else p.weapon
            if cur is not None and self._item_known_unremovable(cur):
                return "Your weapon will not leave your hand"
            return ''
        if isinstance(item, Shield):
            if not p.can_equip_shield():
                return "Not with a two-handed weapon"
            if p.shield is not None and self._item_known_unremovable(p.shield):
                return "Your shield will not come off"
            return ''
        if isinstance(item, Armor):
            slot = getattr(item, 'slot', '')
            if slot in ARMOR_SLOTS:
                cur = p.armor_slots[ARMOR_SLOTS.index(slot)]
                if cur is not None and self._item_known_unremovable(cur):
                    return f"Your {slot} piece will not come off"
            return ''
        if isinstance(item, Accessory):
            slot = getattr(item, 'slot', '')
            if slot == 'amulet':
                return "You already wear an amulet" if p.amulet_slot is not None else ''
            if slot == 'belt':
                return ''
            if all(s is not None for s in p.accessory_slots):
                return "All ring slots are full"
            return ''
        return ''

    def _item_can_identify_now(self) -> bool:
        """The I menu's own gate: the Philosopher's Shard is carried (or the
        Plato passive perceives items without it)."""
        if 'plato_no_shard' in getattr(self.player, 'hero_passives', set()):
            return True
        return any(getattr(i, 'id', '') == 'philosophers_shard'
                   for i in self.player.inventory)

    def _item_actions(self, item, where: str | None = None) -> list[dict]:
        """The actions for ``item``: dicts {id, key, label, enabled, why}.

        Only actions that apply to the item are listed; one that applies but
        is blocked right now (a known curse, full ring slots, too heavy, no
        Shard) is listed with ``enabled`` False and the reason in ``why``.
        """
        from items import Weapon, Armor, Shield, Accessory, Corpse
        if item is None:
            return []
        where = where or self._item_where(item)
        if not where:
            return []
        out: list[dict] = []

        def add(aid, label, why=''):
            key = dict(ACTION_KEYS)[aid]
            out.append({'id': aid, 'key': key, 'label': label,
                        'enabled': not why, 'why': why})

        wearable = (isinstance(item, (Weapon, Armor, Shield, Accessory))
                    and not (isinstance(item, Accessory)
                             and getattr(item, 'slot', '') == 'none'))
        # E -- Equip / Unequip
        if where == 'equip':
            add('equip', 'Unequip', self._item_known_unremovable(item))
        elif wearable and where == 'pack':
            add('equip', 'Equip', self._item_equip_block(item))
        elif wearable and where == 'floor' and not getattr(item, 'not_pickable', False):
            why = self._item_equip_block(item)
            if not why:
                # Worn gear counts, so a swap adds the new piece's weight
                # (the old one goes to the pack and still weighs the same).
                weight = getattr(item, 'weight', 0) * getattr(item, 'count', 1)
                if not self.player.can_carry(weight):
                    why = f"Too heavy for your limit of {self.player.get_carry_limit()}"
            add('equip', 'Take & Equip', why)
        # D -- Drop
        if where == 'pack':
            add('drop', 'Drop')
        elif where == 'equip':
            add('drop', 'Drop', self._item_known_unremovable(item))
        # I -- Identify
        if (hasattr(item, 'id_level') and int(getattr(item, 'id_level', 5)) < 5
                and not isinstance(item, Corpse)):
            add('identify', 'Identify',
                '' if self._item_can_identify_now() else "Needs the Philosopher's Shard")
        # X -- Lore
        add('lore', 'Lore')
        return out

    # ------------------------------------------------------------------
    # Running an action
    # ------------------------------------------------------------------

    def _item_action_run(self, action_id: str, item, ctx: dict) -> bool:
        """Run ``action_id`` on ``item`` from the screen described by ``ctx``
        (see ``_kit_return_ctx`` / ``_charsheet_return_ctx``). Returns True
        when something was attempted."""
        if action_id == 'unequip':
            action_id = 'equip'          # U on the sheet: the same toggle
        where = self._item_where(item)
        actions = {a['id']: a for a in self._item_actions(item, where)}
        # Start a fresh feedback record for this action.
        self._item_feedback = []
        self._item_feedback_on = True
        act = actions.get(action_id)
        if act is None:
            self._item_feedback_on = False
            return False
        if not act['enabled']:
            why = act['why']
            self.add_message(
                f"You cannot {act['label'].lower()} it: {why[:1].lower()}{why[1:]}.",
                'warning')
            self._item_feedback_on = False
            return False

        self._item_screen_return = dict(ctx, item=item)
        if action_id == 'equip':
            self._item_do_equip_toggle(item, where)
        elif action_id == 'drop':
            self._item_do_drop(item, where)
        elif action_id == 'identify':
            self._identify_item(item)
        elif action_id == 'lore':
            self._lore_subject = item
            self.state = STATE_LORE
        self._item_hook_quiz()
        self._item_screen_resume()
        return True

    def _item_do_equip_toggle(self, item, where: str) -> None:
        if where == 'equip':
            self._unequip_slot(self._lore_equipped_slot(item), item)
            return
        if where == 'floor':
            # Pick THIS item up through the normal pickup (turn, weight,
            # pickup side effects), then equip it as from the pack.
            self._pickup(target=item)
            if self.state != self._item_screen_state() or self._item_where(item) != 'pack':
                return
        self._equip_item(item)

    def _item_do_drop(self, item, where: str) -> None:
        if where == 'equip':
            self._unequip_slot(self._lore_equipped_slot(item), item)
            # Still worn (a curse refused it) or the turn ended the run:
            # nothing more happens.
            if self._item_where(item) != 'pack' or self.state != self._item_screen_state():
                return
        self._do_drop_item(item)

    def _item_screen_state(self):
        ctx = getattr(self, '_item_screen_return', None) or {}
        return STATE_KIT if ctx.get('screen') == 'kit' else STATE_CHARACTER_SHEET

    def _item_hook_quiz(self) -> None:
        """When the action opened a quiz, chain the return onto its callback
        so the player is back on the screen the moment the quiz ends."""
        if self.state != STATE_QUIZ:
            return
        qe = getattr(self, 'quiz_engine', None)
        cb = getattr(qe, 'callback', None)
        if cb is None or getattr(cb, '_item_screen_hooked', False):
            return

        def _then_return(result, _cb=cb):
            try:
                _cb(result)
            finally:
                self._item_screen_resume()
        _then_return._item_screen_hooked = True
        qe.callback = _then_return

    # ------------------------------------------------------------------
    # Coming back
    # ------------------------------------------------------------------

    def _item_screen_resume(self) -> bool:
        """Put the player back on the screen an action came from, once the
        action's flow is over. Safe to call every frame."""
        ctx = getattr(self, '_item_screen_return', None)
        if not ctx:
            return False
        if self.state not in _TRANSIT_STATES:
            self._item_screen_return = None          # death, a popup, ...
            self._item_feedback_on = False
            return False
        if self.state not in (STATE_PLAYER, STATE_KIT, STATE_CHARACTER_SHEET):
            return False                              # still in the quiz / prompt / lore
        qe = getattr(self, 'quiz_engine', None)
        if qe is not None and self.state == STATE_PLAYER and getattr(qe, 'active', False):
            return False
        self._item_screen_return = None
        self._item_feedback_on = False
        if ctx.get('screen') == 'kit':
            self._kit_restore(ctx)
        else:
            self._charsheet_restore(ctx)
        return True

    def _item_feedback_lines(self) -> list[tuple[str, str]]:
        """The messages the last action wrote (newest last), for the screen."""
        return list(getattr(self, '_item_feedback', None) or [])[-3:]
