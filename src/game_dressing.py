"""DressingMixin: swapping gear without the chore (winning-build plan 3.4,
2026-11-13).

  * Known by Hand (known_by_hand.py): a kind the hero has put on once goes
    on again with no quiz. The quiz paths in main.py (_start_armor_quiz,
    _equip_accessory, _start_chain_equip_quiz) ask it first.
  * Donning time (gear.don_turns): body armour takes 1 / 3 / 5 turns by
    weight class, full plate 6, everything else 1; taking a piece off half
    that, rounded up. A swap is the old piece off, then the new one on. The
    turns pass one at a time through the normal turn advance (busy.py); a
    hostile coming into view or a blow landing stops it and asks "Keep
    dressing?". Until a piece is fully on, its slot is empty.
  * The weapon At Your Back (Player.readied_weapon): readied from the Kit
    (R), swapped into the hand with S in one turn. A two-hander sends the
    shield to the pack (remembered: Player._shield_slung); a one-hander
    taken up again, by S or the Kit, puts it back on in the same one turn.
  * Loadouts: three saved kits (Shift+E). Putting one on takes the sum of
    its pieces' turns; a piece not in the pack is skipped, a piece not
    known by hand is refused (it must be put on once first).
  * Remembered pieces (loadouts.py): the back and the kits keep a piece
    dropped, thrown or stolen, show it "(not carried)" while it is away and
    have it in its place again when it is picked up (one line says so); a
    piece sold, destroyed or used up is let go (_sets_prune, _sets_let_go).

A light goes on as one (never a stack), and what it took the place of is
remembered by one rule (lights.off_hand_takes, lights.two_hands).

Every piece goes on and comes off through one pair of helpers
(_put_on_now / _take_off_now), so the messages, curses, chain tiers,
grants and quirk counters are the same whichever way it happens.
"""
from __future__ import annotations

from naming import quantity
import pygame

import gear
import known_by_hand as kbh
from busy import BusyAction, Step, interrupt_reason
from game_states import STATE_PLAYER, STATE_ASK, STATE_LOADOUTS
import loadouts as sets
from loadouts import (KIT_COUNT, KIT_NAME_MAX, KIT_ARMOR_SLOTS, KIT_SLOT_LABELS,
                      KIT_SLOTS, default_kits, valid as kits_valid, clean_name)


def _immovable(item) -> bool:
    """Would this worn piece refuse to come off (cursed, part of the hero,
    a blade that chose its wielder)? Asked without trying, so nothing is
    revealed by a plan."""
    return bool(getattr(item, 'cursed', False) or getattr(item, 'bound_to_wielder', False)
                or getattr(item, 'selects_wielder', False))


class DressingMixin:
    """Mixed into Game."""

    _busy = None                # the multi-turn action under way (busy.BusyAction), never saved
    _ask_data = None            # the yes / no prompt's title, lines and options
    _loadout_sel = 0            # the kit selected on the Loadouts screen
    _loadout_naming = None      # a kit name being typed, or None

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------

    def _dress_fast(self) -> bool:
        """The Hephaestus quirk: donning and taking off take half as long."""
        return 'hephaestus' in (getattr(self.player, 'unlocked_quirks', None) or ())

    def _don_turns(self, item) -> int:
        from items import Weapon
        if isinstance(item, Weapon):
            return 1
        return gear.don_turns(item, self._dress_fast())

    def _doff_turns(self, item) -> int:
        from items import Weapon
        if isinstance(item, Weapon):
            return 1
        return gear.doff_turns(item, self._dress_fast())

    def _hero_blows(self) -> int:
        """Blows that have landed on the hero this run (game_combat counts)."""
        return int(self.__dict__.get('_blows_on_hero', 0) or 0)

    def _busy_watch(self, m) -> bool:
        """A creature whose coming into view stops the dressing: a hostile
        the hero can see. A friend (an encounter's person, the unicorn, an
        allied angel, the Emberpup, Old Nickel while the act holds) is no
        reason to stop (bug bash WB-A03)."""
        from game_combat import _is_bystander
        from old_nickel import is_friend
        return not _is_bystander(m) and not is_friend(m) and self._sees_monster(m)

    def _busy_seen(self) -> set:
        return {id(m) for m in (getattr(self, 'monsters', None) or ()) if self._busy_watch(m)}

    def _occupant_for(self, item):
        """(slot name, the piece worn where ``item`` goes) or ('', None). A
        ring has none: it goes in a free ring slot."""
        from items import Armor, Shield, Accessory, ARMOR_SLOTS
        p = self.player
        if isinstance(item, Shield):
            return 'shield', p.shield
        if isinstance(item, Armor):
            slot = getattr(item, 'slot', '')
            if slot in ARMOR_SLOTS:
                return slot, p.armor_slots[ARMOR_SLOTS.index(slot)]
            return '', None
        if isinstance(item, Accessory):
            slot = getattr(item, 'slot', '')
            if slot == 'amulet':
                return 'amulet', p.amulet_slot
            if slot == 'belt':
                return 'belt', getattr(p, 'belt_slot', None)
        return '', None

    def _takes_off_to_wear(self, item) -> bool:
        """Equipping ``item`` would take something off him (the hex's
        question: action_gate 'refuse_worn')."""
        from items import Weapon
        p = self.player
        if isinstance(item, Weapon):
            cur = p.ranged_weapon if getattr(item, 'requires_ammo', None) is not None else p.weapon
            return cur is not None or bool(getattr(item, 'two_handed', False) and p.shield is not None)
        return self._occupant_for(item)[1] is not None

    def _known_by_hand_mark(self, item) -> str:
        """'Known by Hand' for a wearable the hero knows, else ''."""
        return kbh.mark_for(getattr(self, 'player', None), item)

    def _dress_time_text(self, item) -> str:
        """'Takes 5 turns to put on.' for a piece that takes more than one."""
        from items import Weapon
        if isinstance(item, Weapon) or not kbh.asks_quiz(item):
            return ''
        n = self._don_turns(item)
        if n <= 1:
            return ''
        return f"Takes {quantity(n, 'turn')} to put on, {self._doff_turns(item)} to take off."

    # ------------------------------------------------------------------
    # One piece on, one piece off (instant: the turn is the caller's)
    # ------------------------------------------------------------------

    def _put_on_now(self, item, tier: int = 0, done_line: bool = False) -> bool:
        """Put ``item`` (from the pack) on at once. ``tier``: a chain-equip
        legend's tier. ``done_line``: it took several turns, so say
        "The X is on." True when it is worn."""
        from chain_equip import is_chain_equip, apply_tier_bonuses, revert_tier_bonuses
        from items import Shield, Accessory
        p = self.player
        name = self._bare_name(item)
        chain = is_chain_equip(item)
        if chain:
            tier = max(1, min(5, int(tier or 1)))
            apply_tier_bonuses(p, item, tier)
        p._apply_equip(item)
        if not self._is_worn(item):
            # Refused (the piece in that slot would not come off): the new
            # one stays in the pack, never lost.
            if chain:
                revert_tier_bonuses(p, item)
            self.add_message(f"You cannot put on the {name}.", 'warning')
            return False
        p.remove_from_inventory(item)
        kbh.learn(p, item, tier if chain else 0)
        if chain:
            self.add_message(f"You attune to the {name} at tier {tier}/5." + self._ac_now_note(item),
                             'success')
            self._note_worn_curse(item)
            self._chain_equip_passives_fire(item)
            _qs = getattr(self, 'quirk_system', None)
            if _qs:
                if isinstance(item, Accessory):
                    _qs.on_item_equipped(item.id, 'accessory', getattr(item, 'slot', 'accessory'))
                else:
                    slot_type = 'shield' if isinstance(item, Shield) else 'armor'
                    _qs.on_item_equipped(item.id, slot_type, getattr(item, 'slot', slot_type))
            return True
        if isinstance(item, Accessory):
            self._say_accessory_on(item, name)
            self._note_worn_curse(item)
            # The traits hear of a ring or an amulet put on too: Proteus'
            # Many Shapes counts the kinds Known by Hand, and a ring that was
            # the 25th kind earned nothing until the next armour or weapon.
            _qs_acc = getattr(self, 'quirk_system', None)
            if _qs_acc:
                _qs_acc.on_item_equipped(item.id, 'accessory', getattr(item, 'slot', 'accessory'))
            return True
        if gear.is_light(item):
            # A torch or a lantern, taken up and lit (game_lights.py): what
            # it lights is the line, it moves no AC. The FOV widens now.
            self.add_message(self._light_on_line(item), 'success')
            self._refresh_fov()
            return True
        # Armour or a shield. Its curse, if any, is now known and named once.
        # Only body armour and a shield move AC (bug bash 3.3.2): a helm or
        # boots say only that they are on.
        if done_line:
            self.add_message(f"The {name} is on." + self._ac_now_note(item), 'success')
        else:
            self.add_message(f"You equip the {name}." + self._ac_now_note(item), 'success')
        self._note_worn_curse(item)
        # Great Helm of Galahad (purity): announce the cleansing when items
        # were freed of curses by the helm going on.
        _cleansed = int(getattr(p, '_galahad_cleansed_count', 0) or 0)
        if _cleansed > 0:
            self.add_message(
                f"The Grail's light flows from the helm. "
                f"{_cleansed} cursed item{'s' if _cleansed != 1 else ''} "
                f"on your person {'are' if _cleansed != 1 else 'is'} purified.",
                'success')
            p._galahad_cleansed_count = 0
        _qs_arm = getattr(self, 'quirk_system', None)
        if _qs_arm:
            itype = 'shield' if isinstance(item, Shield) else 'armor'
            _qs_arm.on_item_equipped(item.id, itype, getattr(item, 'slot', itype))
        return True

    def _say_accessory_on(self, item, name: str) -> None:
        p = self.player
        fx = item.effects
        if 'status' in fx:
            # the status by its name, not its id ("You feel fire_resist!")
            from status_effects import EFFECT_INFO as _EI
            _label = (_EI.get(fx['status']) or (str(fx['status']).replace('_', ' ').title(),))[0]
            self.add_message(f"You slip on the {name}. You feel {_label}!", 'success')
        elif fx.get('stat') and fx.get('amount'):
            _st, _amt = fx['stat'], int(fx['amount'])
            # Only the strongest bonus to a stat counts (Player.sync_worn_stats):
            # say what this one adds over the others worn.
            _got = p.worn_stat_gain(item, _st) if _st in p.WORN_STATS else _amt
            if _amt < 0 or _got >= _amt:
                self.add_message(f"You slip on the {name}. {_st} {_amt:+d}!", 'success')
            elif _got > 0:
                self.add_message(
                    f"You slip on the {name}. {_st} {_got:+d}: of rings and amulets "
                    f"of one stat, only the strongest counts.", 'success')
            else:
                self.add_message(
                    f"You slip on the {name}, but you already wear a {_st} charm at "
                    f"least as strong: of rings and amulets of one stat, only the "
                    f"strongest counts.", 'info')
        else:
            self.add_message(f"You slip on the {name}.", 'success')

    def _chain_equip_passives_fire(self, item) -> None:
        """Chain-equip passives that fire as the legend goes on:
        dragon_blood_bath (permanent elemental resist statuses, listed on the
        item so they come off with it) and aesir_young (5 turns shielded)."""
        p = self.player
        _passives = getattr(item, '_chain_passives', {}) or {}
        if 'dragon_blood_bath' in _passives:
            _held = list(getattr(item, '_chain_statuses', None) or [])
            for _stat in ('fire_resist', 'cold_resist', 'shock_resist'):
                p.add_effect(_stat, -1)
                if _stat not in _held:
                    _held.append(_stat)
            item._chain_statuses = _held
            self.add_message("You bathe in the dragon's blood. Elements turn aside!", 'success')
        if 'aesir_young' in _passives:
            p.add_effect('shielded', 5)
            self.add_message("Idunn's apples wash years away. You are young again.", 'info')

    def _take_off_now(self, slot_name: str, item) -> bool:
        """Take a worn ``item`` off its slot into the pack at once (the turn
        is the caller's). True when it came off."""
        from items import ARMOR_SLOTS
        from chain_equip import is_chain_equip, revert_tier_bonuses
        p = self.player
        ok, msg = p.try_unequip_slot(item)
        if not ok:
            self.add_message(msg, 'warning')
            return False
        # Revert chain-equip tier bonuses BEFORE slot bookkeeping so player
        # state reflects baseline by the time the item returns to inventory.
        if is_chain_equip(item) and getattr(item, 'achieved_tier', 0) > 0:
            revert_tier_bonuses(p, item)
        if slot_name in ('weapon', 'ranged_weapon'):
            if slot_name == 'weapon':
                p.weapon = None
            else:
                p.ranged_weapon = None
            # Take the weapon's while-equipped effects off with it. Only the
            # swap path inside _apply_equip did this, so a plain unequip left
            # them behind and equip/unequip cycles stacked them (Hofud +2
            # PER per cycle; Curtana's blessing surviving removal).
            p._remove_weapon_passives(item)
            _w_status = getattr(item, 'on_equip_status', '')
            if _w_status:
                self._remove_status_if_no_other_grants(_w_status)
        elif slot_name == 'shield':
            p.shield = None
            p.shed_worn_grants(item)
        elif slot_name in ARMOR_SLOTS:
            idx = ARMOR_SLOTS.index(slot_name)
            p.armor_slots[idx] = None
            # Its status and anything else it lent come off with it (only the
            # swap path did this: the Blindfold left its wearer blind).
            p.shed_worn_grants(item)
        elif slot_name.startswith('accessory_') or slot_name in ('amulet', 'belt'):
            if slot_name == 'amulet':
                p.amulet_slot = None
            elif slot_name == 'belt':
                p.belt_slot = None
            else:
                p.accessory_slots[int(slot_name.split('_')[1])] = None
            from items import Accessory as _Acc
            if isinstance(item, _Acc):
                # Its AC, and its stats by the strongest-counts rule (a
                # weaker ring of the same stat takes over).
                p.accessory_off(item)
                fx = item.effects
                if 'status' in fx:
                    self._remove_status_if_no_other_grants(fx['status'])
        else:
            return False
        p.inventory.append(item)
        if gear.is_light(item):
            # It goes out as it leaves the hand (Player.shed_worn_grants).
            self.add_message(f"You put out the {self._bare_name(item)} and stow it.", 'info')
            self._refresh_fov()
        else:
            self.add_message(f"You remove the {self._bare_name(item)}.", 'info')
        _qs_uneq = getattr(self, 'quirk_system', None)
        if _qs_uneq:
            # A light is taken up and put away, never worn: no armour changed
            # (Penelope's count), as the equip side says nothing of one.
            itype = 'weapon' if slot_name in ('weapon', 'ranged_weapon') else \
                    'light' if gear.is_light(item) else \
                    'shield' if slot_name == 'shield' else \
                    'armor' if slot_name not in ('amulet', 'belt') and not slot_name.startswith('accessory_') else \
                    'accessory'
            _qs_uneq.on_item_unequipped(item.id, itype, slot_name)
        return True

    def _wield_now(self, item) -> bool:
        """Take a weapon from the pack into the hand at once (the old one
        goes to the pack; a two-hander sends an unbound shield there too).
        True when it is wielded."""
        p = self.player
        shield_before = p.shield
        p._apply_equip(item)
        if p.weapon is not item:
            return False
        p.remove_from_inventory(item)
        if shield_before is not None and p.shield is None:
            self._say_shield_slung(shield_before, item)
        _qs_eq = getattr(self, 'quirk_system', None)
        if _qs_eq:
            _qs_eq.on_item_equipped(item.id, 'weapon', 'weapon')
        self._note_worn_curse(item)
        return True

    # ------------------------------------------------------------------
    # The shield a two-hander set aside (Brandon's play-test, 2026-11-16:
    # "If I swap between my one handed weapon and 2 handed, it doesn't
    # automatically swap BACK my shield")
    # ------------------------------------------------------------------

    def _say_shield_slung(self, shield, weapon) -> None:
        # A torch or a lantern goes out and back in the hand, not on the arm.
        back = "it is lit in your hand again" if gear.is_light(shield) else "it goes back on your arm"
        self.add_message(f"Your {self._bare_name(shield)} goes to your pack: the "
                         f"{self._bare_name(weapon)} takes both hands. Take up a "
                         f"one-handed weapon and {back}.", 'info')

    def _slung_shield(self):
        """The shield a two-hander sent to the pack (Player._shield_slung),
        when the weapon in the hand now leaves an arm free for it: not worn,
        still in the pack, its kind known by hand. The memory is let go when
        it can never come back (another shield is on, it left the pack)."""
        p = self.player
        sh = p.__dict__.get('_shield_slung')
        if sh is None:
            return None
        if p.shield is not None or not any(i is sh for i in p.inventory) \
                or (kbh.asks_quiz(sh) and not kbh.knows(p, sh)):
            p.__dict__['_shield_slung'] = None
            return None
        if not p.can_equip_shield():
            return None                 # a two-hander is still in the hand
        if gear.is_light(sh):
            import lights
            lights.leave_rest(p.inventory, sh)  # it may have taken in a bundle: one goes back
        return sh

    def _shield_back_on(self, sh) -> None:
        """The remembered shield goes back on the arm as part of the weapon
        change itself: no turn of its own (Brandon 2026-11-16: "ready
        swapping weapon set should only take 1 turn, even if you equip a
        shield as well"). The caller spends the change's one turn."""
        p = self.player
        p.__dict__['_shield_slung'] = None
        self._put_on_now(sh, tier=kbh.best_tier(p, sh))

    # ------------------------------------------------------------------
    # Putting a piece on / taking it off, with the time it takes
    # ------------------------------------------------------------------

    def _dress_known(self, item, tier: int = 0) -> None:
        """A kind known by hand: no quiz. Say so, then put it on."""
        self.add_message(kbh.fires_line(item), 'info')
        self._dress_begin_on(item, tier=tier)

    def _dress_begin_on(self, item, tier: int = 0) -> None:
        """Put ``item`` on, taking the time it takes: the piece in its slot
        comes off first (half its own time), then the new one goes on. A
        one-turn piece into an empty slot is what equipping always was."""
        slot, old = self._occupant_for(item)
        steps = []
        if old is not None and old is not item:
            steps.append(Step('off', old, self._doff_turns(old), slot=slot))
        steps.append(Step('on', item, self._don_turns(item), tier=tier))
        total = sum(s.turns for s in steps)
        if total <= 1:
            self._put_on_now(item, tier=tier)
            self._advance_turn()
            return
        name = self._bare_name(item)
        if old is not None:
            line = (f"You start changing the {self._bare_name(old)} for the {name} "
                    f"({quantity(total, 'turn')}).")
        else:
            from items import Armor
            verb = 'buckling on' if isinstance(item, Armor) and gear.is_core(item) else 'putting on'
            line = f"You start {verb} the {name} ({quantity(total, 'turn')})."
        self._busy_start(BusyAction(steps, label=name), line)

    def _equip_failed(self, item, struggle: str) -> int:
        """A failed equip quiz costs the piece's donning time (Brandon,
        2026-11-16: "If there is no penalty for missing putting on armor,
        then use the equip length as 'lost' turns on a failure"). The hero
        spent that long at it: the turns pass through the normal turn
        advance, one at a time, so the monsters act on every one, and a
        blow does not stop them (they are already spent). Only death, a
        change of floor or of screen ends them early. ``struggle`` is the
        line's opening ("You struggle with the Iron Full Plate"). Returns the
        turns that passed."""
        n = max(1, int(self._don_turns(item)))
        self.add_message(f"{struggle} for {quantity(n, 'turn')} and give up.", 'warning')
        start_state = self.state
        floor = self.dungeon_level
        spent = 0
        for _ in range(n):
            self._advance_turn()
            spent += 1
            if (self.player.is_dead() or self.state != start_state
                    or self.dungeon_level != floor):
                break
        return spent

    def _dress_start_off(self, slot_name: str, item) -> None:
        """Take a worn piece off, taking the time it takes."""
        n = self._doff_turns(item)
        if n <= 1:
            if self._take_off_now(slot_name, item):
                self._advance_turn()
            return
        self._busy_start(BusyAction([Step('off', item, n, slot=slot_name)],
                                    label=self._bare_name(item)),
                         f"You start unbuckling the {self._bare_name(item)} ({quantity(n, 'turn')}).")

    # ------------------------------------------------------------------
    # The busy runner
    # ------------------------------------------------------------------

    def _busy_start(self, action: BusyAction, line: str = '') -> None:
        action.seen = self._busy_seen()
        action.struck = self._hero_blows()
        self._busy = action
        if line:
            self.add_message(line, 'info')
        self._busy_run()

    def _busy_do(self, step: Step) -> None:
        if step.kind == 'off':
            act = getattr(self, '_busy', None)
            # A shield coming off for a light (E, the Kit, a saved kit) is
            # what that light takes the place of (lights.set_aside).
            for_light = (step.slot == 'shield' and not gear.is_light(step.item) and act is not None
                         and any(s.kind == 'on' and gear.is_light(s.item) for s in act.steps))
            tier = int(getattr(step.item, 'achieved_tier', 0) or 0)
            if self._take_off_now(step.slot, step.item) and for_light:
                self._light_takes_place(step.item, tier)
        elif step.kind == 'on':
            if any(i is step.item for i in self.player.inventory):
                self._put_on_now(step.item, tier=step.tier, done_line=step.turns > 1)
        elif step.kind == 'wield':
            if any(i is step.item for i in self.player.inventory):
                if not self._wield_now(step.item):
                    self.add_message(f"You cannot take up the {self._bare_name(step.item)}.",
                                     'warning')
        elif step.kind == 'ready':
            if any(i is step.item for i in self.player.inventory):
                self.player.readied_weapon = step.item

    def _busy_step_possible(self, step: Step) -> bool:
        """Can the step under way still be done? A piece to go on, into the
        hand or at the back must still be in the pack (a thief's blow may
        have taken it); a piece to come off must still be worn."""
        if step.item is None:
            return True
        if step.kind in ('on', 'wield', 'ready'):
            return any(i is step.item for i in self.player.inventory)
        if step.kind == 'off':
            return self._is_worn(step.item)
        return True

    def _busy_helpless(self) -> str:
        """Why the hero cannot go on working at all ('' when he can): asleep
        or paralysed, as _helpless_turn reads it (bug bash WB-A02), off his
        feet, numb with ice, or hexed with a piece still to come off."""
        p = self.player
        if p.has_effect('paralyzed'):
            return 'you cannot move'
        if p.has_effect('sleeping'):
            return 'you have fallen asleep'
        if p.has_effect('knocked_down'):
            return 'you are off your feet'
        if p.has_effect('frozen'):
            return 'your hands are numb with ice'
        if p.has_effect('hexed'):
            act = getattr(self, '_busy', None)
            if act is not None and not act.done and act.current.kind == 'off':
                return 'the hex holds it to you'
        return ''

    def _busy_run(self) -> None:
        """Run the action's turns until it is done or something stops it.
        Before each turn: a step whose piece is gone is dropped and spends
        no turn (bug bash WB-A04); a hero asleep or paralysed stops
        (WB-A02); a hostile newly in view or a blow asks "Keep dressing?"."""
        act = getattr(self, '_busy', None)
        start_state = self.state
        floor = self.dungeon_level
        while act is not None and not act.done:
            s = act.current
            if not self._busy_step_possible(s):
                if (s.kind in ('on', 'wield', 'ready') and s.item is not None
                        and not self._is_worn(s.item)):
                    self.add_message(f"The {self._bare_name(s.item)} is gone from your pack.",
                                     'warning')
                act.finish_step()
                continue
            helpless = self._busy_helpless()
            if helpless:
                self._busy_halt(helpless)
                return
            why = interrupt_reason(act, self._busy_seen(), self._hero_blows())
            if why:
                self._busy_pause(why)
                return
            if int(s.turns) <= 0:
                self._busy_do(s)
                act.finish_step()
                continue
            if act.step_due():
                # The step is done on its last turn: the piece counts on it.
                self._busy_do(s)
                act.finish_step()
            else:
                act.advance()
            self._advance_turn()
            if (self.player.is_dead() or self.state != start_state
                    or self.dungeon_level != floor):
                self._busy_abort()
                return
        self._busy = None
        if act is not None and act.done_line:
            self.add_message(act.done_line, 'success')

    def _busy_who(self, why: str, act: BusyAction):
        """The monster that stopped it: the one that struck, or the first
        one newly in view."""
        if why == 'struck':
            m = self.__dict__.get('_last_striker')
            if m is not None:
                return m
        for m in getattr(self, 'monsters', None) or ():
            if id(m) not in act.seen and self._busy_watch(m):
                return m
        return None

    def _busy_already_off(self, act: BusyAction) -> str:
        """The pieces this action has taken off already that nothing has
        replaced, as a sentence ("Your Worn Leather Jerkin is already
        off."), or ''. A swap takes the old piece off first: stopped on the
        new one, the hero stands in neither (bug bash WB-E01)."""
        names = []
        for st in act.steps[:act.index]:
            if st.kind != 'off' or st.item is None or self._is_worn(st.item):
                continue
            if self._occupant_for(st.item)[1] is not None:
                continue                      # something else is on there now
            names.append(self._bare_name(st.item))
        if not names:
            return ''
        both = names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]
        return f"Your {both} {'is' if len(names) == 1 else 'are'} already off."

    def _busy_pause(self, why: str) -> None:
        from monster import the_name
        act = self._busy
        s = act.current
        m = self._busy_who(why, act)
        who = the_name(m, lower=True) if m is not None else 'something'
        what = (f"as {who} strikes you" if why == 'struck'
                else f"as {who} comes into view")
        piece = self._bare_name(s.item) if s.item is not None else act.label
        if s.kind == 'on':
            line = f"You stop, half into the {piece}, {what}."
        elif s.kind == 'off':
            line = f"You stop, half out of the {piece}, {what}."
        else:
            line = f"You stop changing into {act.label}, {what}."
        self.add_message(line, 'warning')
        left = act.turns_left
        self.add_message(f"{act.prompt} (Y/N)", 'warning')
        if s.kind == 'off':
            stop_text = f"The {piece} stays on."
        elif s.kind == 'on':
            stop_text = f"The {piece} goes back in your pack."
            off = self._busy_already_off(act)
            if off:
                stop_text = f"{stop_text} {off}"
        else:
            stop_text = "What is on stays on; the rest stays in your pack."
        self._ask(act.prompt.rstrip('?').title() + '?', [line, f"{left} turn{'s' if left != 1 else ''} left."],
                  [('Y', 'Keep Going', f"{left} more turn{'s' if left != 1 else ''}.", self._busy_resume),
                   ('N', 'Stop', stop_text, self._busy_stop)],
                  on_cancel=self._busy_stop, esc='stop')

    def _busy_halt(self, why: str) -> None:
        """The hero cannot go on (asleep, paralysed): he stops where he is,
        as if he had said no. What is on stays on; the rest stays in the
        pack."""
        act = getattr(self, '_busy', None)
        if act is None or act.done:
            self._busy = None
            return
        s = act.current
        piece = self._bare_name(s.item) if s.item is not None else act.label
        if s.kind == 'on':
            line = f"You stop, half into the {piece}: {why}."
        elif s.kind == 'off':
            line = f"You stop, half out of the {piece}: {why}."
        else:
            line = f"You stop changing into {act.label}: {why}."
        self.add_message(line, 'warning')
        self._busy_stop()

    def _busy_resume(self) -> None:
        act = getattr(self, '_busy', None)
        if act is None:
            return
        act.seen = self._busy_seen()
        act.struck = self._hero_blows()
        self._busy_run()

    def _busy_stop(self) -> None:
        act = getattr(self, '_busy', None)
        self._busy = None
        if act is None or act.done:
            return
        s = act.current
        piece = self._bare_name(s.item) if s.item is not None else act.label
        if s.kind == 'on':
            off = self._busy_already_off(act)
            self.add_message(f"You leave the {piece} in your pack." + (f" {off}" if off else ''),
                             'info')
        elif s.kind == 'off':
            self.add_message(f"You leave the {piece} on.", 'info')
        else:
            self.add_message(f"You stop changing into {act.label}.", 'info')

    def _busy_abort(self) -> None:
        act = getattr(self, '_busy', None)
        self._busy = None
        if act is None or act.done or self.player.is_dead():
            return
        s = act.current
        piece = self._bare_name(s.item) if s.item is not None else act.label
        self.add_message(f"You never finished with the {piece}.", 'info')

    # ------------------------------------------------------------------
    # A small yes / no prompt (Keep dressing?, attune again?, a kit)
    # ------------------------------------------------------------------

    def _ask(self, title: str, lines: list, options: list, on_cancel=None,
             esc: str = 'close') -> None:
        """Open the prompt. ``options``: (key, name, text, callback); the
        first is what Enter picks. Escape runs ``on_cancel`` (or nothing);
        ``esc`` is what the footer calls it."""
        self._ask_data = {'title': title, 'lines': list(lines or ()),
                          'options': list(options), 'on_cancel': on_cancel, 'esc': esc}
        self.state = STATE_ASK

    def _ask_input(self, key: int) -> None:
        data = getattr(self, '_ask_data', None) or {}
        options = data.get('options') or []
        pick = None
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER) and options:
            pick = options[0][3]
        elif key == pygame.K_ESCAPE:
            self._ask_data = None
            self.state = STATE_PLAYER
            cb = data.get('on_cancel')
            if cb:
                cb()
            return
        else:
            for k, _name, _text, cb in options:
                if key == getattr(pygame, f'K_{k.lower()}', None):
                    pick = cb
                    break
        if pick is None:
            return
        self._ask_data = None
        self.state = STATE_PLAYER
        pick()

    # ------------------------------------------------------------------
    # The weapon At Your Back
    # ------------------------------------------------------------------

    def _ready_weapon(self, item) -> None:
        """Sling a weapon from the pack at your back (no turn: it is only
        which one S draws)."""
        p = self.player
        p.readied_weapon = item
        if p.readied_weapon is item:
            self.add_message(f"You sling the {self._bare_name(item)} at your back. "
                             f"S swaps it into your hand.", 'info')

    def _readied_mark(self, item) -> bool:
        """Is this what a swap key draws: the weapon At Your Back (S), or a
        light of the readied kind (Shift+L, game_lights.py)?"""
        p = getattr(self, 'player', None)
        if p is None or item is None:
            return False
        import lights
        return item is getattr(p, 'readied_weapon', None) or lights.is_readied(p, item)

    def _unready_weapon(self) -> None:
        p = self.player
        item = p.readied_weapon
        p.readied_weapon = None
        if item is not None:
            self.add_message(f"You put the {self._bare_name(item)} away in your pack.", 'info')

    def _swap_weapons(self) -> bool:
        """S: the weapon in your hand and the one at your back change places,
        in one turn. A cursed blade in the hand will not let go; a two-hander
        cannot come out past a shield that will not come off. A two-hander
        sends the shield to the pack, and drawing a one-hander again puts it
        back on the arm in the same one turn. True when the swap happened."""
        p = self.player
        back = p.readied_weapon
        hand = p.weapon
        if back is None:
            gone = self._readied_away()
            if gone is not None:
                # Dropped, thrown or stolen: remembered, not with him.
                self.add_message(f"Your {self._bare_name(gone)} is not with you. Pick it up "
                                 f"again and S draws it.", 'info')
                return False
            self.add_message("Nothing is at your back. Ready a weapon from the Kit "
                             "(K, then R).", 'info')
            return False
        if not self._gate('swap', item=back, worn=hand is not None, possible=lambda: (
                (hand is None or p.try_unequip_slot(hand)[0])
                and (not getattr(back, 'two_handed', False) or p.shield is None
                     or p.try_unequip_slot(p.shield)[0]))):
            return False
        if hand is not None:
            ok, msg = p.try_unequip_slot(hand)
            if not ok:
                self.add_message(f"{msg} The {self._bare_name(back)} stays at your back.",
                                 'warning')
                return False
        if getattr(back, 'two_handed', False) and p.shield is not None:
            ok, msg = p.try_unequip_slot(p.shield)
            if not ok:
                self.add_message(f"{msg} The two-handed {self._bare_name(back)} stays at "
                                 f"your back.", 'warning')
                return False
        if not self._wield_now(back):
            self.add_message(f"You cannot take up the {self._bare_name(back)}.", 'warning')
            return False
        # The Two Faces of Janus: drawn with a foe in sight, counted; once
        # earned, the swap costs no turn (the swap that earns it still does).
        _free = bool((getattr(p, 'quirk_progress', None) or {}).get('janus_active'))
        # A one-hander drawn: the shield the two-hander set aside goes back
        # on the arm in the same turn (Brandon 2026-11-16: one turn).
        sh = None if getattr(back, 'two_handed', False) else self._slung_shield()
        tail = f" and take up your {self._bare_name(sh)}" if sh is not None else ''
        if hand is not None and any(i is hand for i in p.inventory):
            p.readied_weapon = hand
            self.add_message(f"You sling the {self._bare_name(hand)} at your back and draw "
                             f"the {self._bare_name(back)}{tail}.", 'success')
        else:
            self.add_message(f"You draw the {self._bare_name(back)} from your back{tail}.",
                             'success')
        if sh is not None:
            self._shield_back_on(sh)
            if _free:
                import lights
                if lights.is_lit(p.shield):
                    lights.kindled(p, p.shield)     # lit in no time: this turn pays for it
        _qs = getattr(self, 'quirk_system', None)
        if _qs is not None:
            try:
                _foe = bool(self._busy_seen())
            except Exception:
                _foe = False
            _qs.on_weapon_swap(_foe)
        if not _free:
            self._advance_turn()
        return True

    # ------------------------------------------------------------------
    # Remembered pieces: the back and the kits keep what was dropped,
    # thrown or stolen, and let go of what is gone for good (loadouts.py)
    # ------------------------------------------------------------------

    def _sets_let_go(self, item) -> bool:
        """``item`` is gone for good (sold, destroyed, used up, made into
        another thing): off the back and out of every kit."""
        return sets.let_go(getattr(self, 'player', None), item)

    def _sets_lost(self, pieces) -> list:
        """Those of ``pieces`` (away from the hero) found nowhere in the
        world: not on any floor's ground or in a chest there, not in a
        thief's hands. What is left of them was destroyed, used up, given
        away or remade."""
        want = {id(it): it for it in pieces if it is not None}

        def scan(things):
            for it in things or ():
                if not want:
                    return
                want.pop(id(it), None)
                inner = getattr(it, 'contents', None)
                if inner:
                    scan(inner)

        def scan_floor(ground, monsters):
            scan(ground)
            for m in monsters or ():
                if not want:
                    return
                scan(getattr(m, '__dict__', {}).get('stolen_items'))

        scan_floor(getattr(self, 'ground_items', None), getattr(self, 'monsters', None))
        saved = getattr(getattr(self, 'level_mgr', None), '_saved', None) or {}
        for val in list(saved.values()):
            if not want:
                break
            if isinstance(val, dict):
                scan_floor(val.get('ground_items') or val.get('items'), val.get('monsters'))
            elif isinstance(val, (tuple, list)) and len(val) >= 3:
                scan_floor(val[2], val[1])
        return list(want.values())

    def _sets_prune(self, force: bool = False) -> None:
        """Let go of every remembered piece that is gone for good. Cheap when
        everything is with the hero; the world is searched only for a piece
        that is away, and at most once a turn (or when the pack or the floor
        changes) unless ``force`` (a save)."""
        p = getattr(self, 'player', None)
        if p is None:
            return
        key = (getattr(self, 'turn_count', 0), len(getattr(p, 'inventory', None) or ()),
               len(getattr(self, 'ground_items', None) or ()))
        if not force and self.__dict__.get('_sets_pruned_at') == key:
            return
        self.__dict__['_sets_pruned_at'] = key
        away = sets.away_pieces(p)
        if not away:
            return
        for it in self._sets_lost(away):
            sets.let_go(p, it)

    def _readied_away(self):
        """The weapon At Your Back while it is away (dropped, thrown,
        stolen), else None. In the hand it is not away."""
        self._sets_prune()
        p = self.player
        mem = sets.readied_memory(p)
        return mem if mem is not None and sets.away(p, mem) else None

    def _sets_note_back(self, item) -> None:
        """A remembered piece is back in the pack: one line says it is in
        its place again (after "You pick up ...")."""
        p = self.player
        if item is None or not sets.holds(p, item) \
                or not any(i is item for i in p.inventory):
            return
        line = sets.back_line(self._bare_name(item), sets.readied_memory(p) is item,
                              sets.kit_names_holding(p, item))
        if line:
            self.add_message(line, 'info')

    # ------------------------------------------------------------------
    # Loadouts: three saved kits
    # ------------------------------------------------------------------

    def _kits(self) -> list:
        p = self.player
        kits = p.__dict__.get('loadouts')
        if not kits_valid(kits):
            kits = default_kits()
            p.__dict__['loadouts'] = kits
        return kits

    def _kit_snapshot(self) -> dict:
        """What is worn now, by kit slot."""
        from items import ARMOR_SLOTS
        p = self.player
        out = {'weapon': p.weapon, 'readied': p.readied_weapon, 'shield': p.shield,
               'amulet': p.amulet_slot, 'belt': getattr(p, 'belt_slot', None)}
        for slot in KIT_ARMOR_SLOTS:
            out[slot] = p.armor_slots[ARMOR_SLOTS.index(slot)]
        for i, r in enumerate(p.accessory_slots):
            out[f'ring_{i}'] = r
        return {k: v for k, v in out.items() if v is not None}

    def _kit_save(self, idx: int) -> None:
        kit = self._kits()[idx]
        kit['pieces'] = self._kit_snapshot()
        n = len(kit['pieces'])
        self.add_message(f"{kit['name']} saved: {n} piece{'s' if n != 1 else ''}.", 'success')

    def _kit_rename(self, idx: int, name: str) -> None:
        self._kits()[idx]['name'] = clean_name(name, idx)

    def _worn_in(self, slot: str):
        from items import ARMOR_SLOTS
        p = self.player
        if slot == 'weapon':
            return p.weapon
        if slot == 'readied':
            return p.readied_weapon
        if slot == 'shield':
            return p.shield
        if slot == 'amulet':
            return p.amulet_slot
        if slot == 'belt':
            return getattr(p, 'belt_slot', None)
        if slot in KIT_ARMOR_SLOTS:
            return p.armor_slots[ARMOR_SLOTS.index(slot)]
        return None


    def _kit_plan(self, idx: int) -> dict:
        """What putting kit ``idx`` on would do: {'steps', 'turns', 'missing',
        'refused' (piece, why), 'already'}. Nothing is changed but what is
        gone for good leaving the kit (_sets_prune). A piece that is away
        (dropped, thrown, stolen) is 'missing': skipped, at no cost."""
        self._sets_prune()
        p = self.player
        kit = self._kits()[idx]
        pieces = dict(kit.get('pieces') or {})
        inv = {id(i) for i in p.inventory}
        missing, refused = [], []
        offs, wields, readies, ons = [], [], [], []
        # What each piece of the kit costs (id -> turns): its own turns on,
        # with the piece in its way coming off counted in (the Loadouts
        # screen shows it per piece: Brandon's play-test 2026-11-16).
        cost = {}

        def carried(it):
            return id(it) in inv

        def known_ok(it):
            if kbh.asks_quiz(it) and not kbh.knows(p, it):
                refused.append((it, "not known by hand: put it on once first"))
                return False
            return True

        # Weapons first: what goes in the hand decides the shield.
        new_hand = p.weapon
        w = pieces.get('weapon')
        if w is not None and w is not p.weapon:
            if not carried(w):
                missing.append(w)
            elif p.weapon is not None and _immovable(p.weapon):
                refused.append((w, f"your {self._bare_name(p.weapon)} will not leave your hand"))
            elif getattr(w, 'two_handed', False) and p.shield is not None \
                    and _immovable(p.shield) and pieces.get('shield') is not p.shield:
                refused.append((w, "your shield will not come off for a two-hander"))
            else:
                wields.append(Step('wield', w, 1))
                cost[id(w)] = 1
                new_hand = w
        r = pieces.get('readied')
        if r is not None and r is not p.readied_weapon:
            if r is new_hand:
                pass                          # it is going in the hand
            elif carried(r) or (r is p.weapon and new_hand is not p.weapon):
                readies.append(Step('ready', r, 0))
                cost[id(r)] = 0
            elif r is p.weapon:
                refused.append((r, "it is in your hand"))
            else:
                missing.append(r)
        two_hander = bool(getattr(new_hand, 'two_handed', False))

        for slot in ('shield', 'amulet', 'belt') + KIT_ARMOR_SLOTS:
            want = pieces.get(slot)
            if want is None:
                continue
            cur = self._worn_in(slot)
            if want is cur:
                continue
            if not carried(want):
                missing.append(want)
                continue
            if slot == 'shield' and two_hander:
                refused.append((want, "not with a two-handed weapon"))
                continue
            if not known_ok(want):
                continue
            off_turns = 0
            if cur is not None:
                if _immovable(cur):
                    refused.append((want, f"your {self._bare_name(cur)} will not come off"))
                    continue
                off_turns = self._doff_turns(cur)
                offs.append(Step('off', cur, off_turns, slot=slot))
            ons.append(Step('on', want, self._don_turns(want),
                            tier=kbh.best_tier(p, want)))
            cost[id(want)] = off_turns + self._don_turns(want)

        # Rings: the kit's rings on, worn rings not in the kit off to make room.
        kit_rings = [v for k, v in sorted(pieces.items()) if k.startswith('ring_')]
        worn_rings = [x for x in p.accessory_slots if x is not None]
        to_put = []
        for ring in kit_rings:
            if any(ring is x for x in worn_rings):
                continue
            if not carried(ring):
                missing.append(ring)
                continue
            if not known_ok(ring):
                continue
            to_put.append(ring)
        free = sum(1 for x in p.accessory_slots if x is None)
        spare = [x for x in worn_rings
                 if not any(x is k for k in kit_rings) and not _immovable(x)]
        for ring in to_put:
            off_turns = 0
            if free <= 0 and spare:
                old = spare.pop(0)
                slot = f'accessory_{next(i for i, x in enumerate(p.accessory_slots) if x is old)}'
                off_turns = self._doff_turns(old)
                offs.append(Step('off', old, off_turns, slot=slot))
                free += 1
            if free <= 0:
                refused.append((ring, "no free ring finger"))
                continue
            free -= 1
            ons.append(Step('on', ring, self._don_turns(ring), tier=kbh.best_tier(p, ring)))
            cost[id(ring)] = off_turns + self._don_turns(ring)

        steps = offs + wields + readies + ons
        return {'steps': steps, 'turns': sum(s.turns for s in steps),
                'missing': missing, 'refused': refused, 'cost': cost,
                'empty': not pieces,
                'already': bool(pieces) and not steps and not missing and not refused}

    def _kit_rows(self, idx: int, plan: dict | None = None) -> list:
        """(label, name, what changing into the kit does to the piece) for
        each piece of kit ``idx``, in slot order. The third is 'On now',
        'At your back', '3 turns' (the piece in its way coming off counted
        in), 'No time' (slung at the back), 'Not carried' or 'Stays off'."""
        plan = plan if plan is not None else self._kit_plan(idx)
        p = self.player
        pieces = self._kits()[idx].get('pieces') or {}
        cost = plan.get('cost') or {}
        missing = {id(i) for i in plan['missing']}
        refused = {id(i) for i, _why in plan['refused']}
        worn_rings = [x for x in p.accessory_slots if x is not None]
        out = []
        for s in KIT_SLOTS:
            if s not in pieces:
                continue
            it = pieces[s]
            name = self._bare_name(it)
            if id(it) in missing or not sets.carried_or_worn(p, it):
                out.append((KIT_SLOT_LABELS[s], name, 'Not carried'))
                continue
            if id(it) in refused:
                out.append((KIT_SLOT_LABELS[s], name, 'Stays off'))
                continue
            if id(it) in cost:
                n = int(cost[id(it)])
                out.append((KIT_SLOT_LABELS[s], name, quantity(n, 'turn') if n else 'No time'))
                continue
            if s == 'readied':
                out.append((KIT_SLOT_LABELS[s], name, 'At your back'))
            elif s.startswith('ring_') and not any(it is x for x in worn_rings):
                out.append((KIT_SLOT_LABELS[s], name, 'Stays off'))
            else:
                out.append((KIT_SLOT_LABELS[s], name, 'On now'))
        return out

    def _kit_change_text(self, plan: dict) -> str:
        """One line for what changing into a kit takes: "3 pieces change:
        7 turns in all." ('' when nothing changes)."""
        n = len(plan.get('cost') or {})
        if not plan['steps'] or not n:
            return ''
        t = plan['turns']
        return (f"{quantity(n, 'piece')} change{'s' if n == 1 else ''}: "
                f"{quantity(t, 'turn')} in all.")

    def _kit_wear(self, idx: int) -> None:
        """Put kit ``idx`` on now (after the confirmation)."""
        kit = self._kits()[idx]
        plan = self._kit_plan(idx)
        for it in plan['missing']:
            self.add_message(f"{kit['name']}: the {self._bare_name(it)} is not with you, so "
                             f"it is skipped.", 'warning')
        for it, why in plan['refused']:
            self.add_message(f"{kit['name']}: the {self._bare_name(it)} stays off ({why}).",
                             'warning')
        steps = plan['steps']
        if not steps:
            self.add_message(f"You are already dressed in {kit['name']}." if plan['already']
                             else f"Nothing of {kit['name']} can be put on.", 'info')
            return
        if not self._gate('swap', worn=any(s.kind == 'off' for s in steps)):
            return
        act = BusyAction(steps, label=kit['name'], prompt='Keep dressing?',
                         done_line=f"You are dressed in {kit['name']}.")
        turns = plan['turns']
        line = (f"You start changing into {kit['name']} ({turns} turn{'s' if turns != 1 else ''})."
                if turns > 0 else '')
        self._busy_start(act, line)

    # -- the Loadouts screen (Shift+E) --------------------------------------

    def _open_loadouts(self) -> None:
        self._kits()
        self._loadout_sel = max(0, min(getattr(self, '_loadout_sel', 0), KIT_COUNT - 1))
        self._loadout_naming = None
        self.state = STATE_LOADOUTS

    def _kit_lines(self, idx: int) -> list:
        """(label, name) of each piece in a kit, in slot order; a piece that
        is away is "(not carried)"."""
        self._sets_prune()
        p = self.player
        pieces = self._kits()[idx].get('pieces') or {}
        out = []
        for s in KIT_SLOTS:
            if s not in pieces:
                continue
            name = self._bare_name(pieces[s])
            if not sets.carried_or_worn(p, pieces[s]):
                name = sets.not_carried(name)
            out.append((KIT_SLOT_LABELS[s], name))
        return out

    def _loadouts_input(self, key: int, unicode_char: str = '') -> None:
        naming = getattr(self, '_loadout_naming', None)
        if naming is not None:
            if key == pygame.K_ESCAPE:
                self._loadout_naming = None
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._kit_rename(self._loadout_sel, naming)
                self._loadout_naming = None
            elif key == pygame.K_BACKSPACE:
                self._loadout_naming = naming[:-1]
            elif unicode_char and (unicode_char.isalnum() or unicode_char in " '-") \
                    and len(naming) < KIT_NAME_MAX:
                self._loadout_naming = naming + unicode_char
            return
        if key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER
            return
        if key in (pygame.K_1, pygame.K_2, pygame.K_3):
            self._loadout_sel = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}[key]
            return
        if key == pygame.K_UP:
            self._loadout_sel = (self._loadout_sel - 1) % KIT_COUNT
            return
        if key == pygame.K_DOWN:
            self._loadout_sel = (self._loadout_sel + 1) % KIT_COUNT
            return
        if key == pygame.K_s:
            self._kit_save(self._loadout_sel)
            return
        if key == pygame.K_n:
            self._loadout_naming = ''
            return
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_w):
            self._kit_confirm(self._loadout_sel)

    def _kit_confirm(self, idx: int) -> None:
        kit = self._kits()[idx]
        plan = self._kit_plan(idx)
        if plan['empty']:
            self.add_message(f"{kit['name']} is empty. Dress as you like, then S saves it.",
                             'info')
            return
        if not plan['steps']:
            # Already worn, or nothing of it can go on now: say why, no prompt.
            self._kit_wear(idx)
            return
        turns = plan['turns']
        lines = []
        # What changes, piece by piece, and what it all takes.
        changing = [(lab, c) for lab, _nm, c in self._kit_rows(idx, plan)
                    if c.endswith(('turn', 'turns'))]
        if changing:
            shown = ', '.join(f"{lab} {c}" for lab, c in changing[:4])
            more = f", and {len(changing) - 4} more" if len(changing) > 4 else ''
            lines.append(f"Changes: {shown}{more}.")
        if plan['missing']:
            lines.append("Not with you, so skipped: " + ', '.join(
                self._bare_name(i) for i in plan['missing'][:3])
                + (' ...' if len(plan['missing']) > 3 else '') + '.')
        for it, why in plan['refused'][:2]:
            lines.append(f"Stays off: {self._bare_name(it)} ({why}).")
        if not plan['missing'] and not plan['refused']:
            lines.append("Every piece is in your pack and known by hand: no quizzes.")

        def _wear(i=idx):
            self._kit_wear(i)
        self._ask(f"Change Into {kit['name']}?", lines,
                  [('Y', f"Put On {kit['name']}",
                    f"Takes {quantity(turns, 'turn')} in all.", _wear),
                   ('N', 'Not Now', 'Back to the game.', lambda: None)],
                  on_cancel=None)
