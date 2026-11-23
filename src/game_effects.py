"""EffectsMixin: the debuffs at work in the Game (Brandon, 2026-11-22).

The rules are pure: action_gate.py (may he do it), effect_rules.py (the
bouts), mind_theft.py (Forget), data/effects.json (the numbers and lines).
Here the Game asks and carries the answers out.

EVERY action of the hero's calls ``_gate`` where it is committed, with its
door; a step calls ``_gate_step``. A key that only opens a menu is not an
action: the menu's choice is. tests/test_action_doors.py fails when a
function that spends a turn has no door.
"""
from __future__ import annotations

import random

import action_gate
import effect_rules
import mind_theft
from geom import monster_at_tile
from game_states import (STATE_CHARACTER_SHEET, STATE_DEAD, STATE_KIT, STATE_PET_MENU,
                         STATE_PLAYER)

_STEPS = ((0, -1), (0, 1), (-1, 0), (1, 0))
# Screens an action returns to by itself.
_STAYS = (STATE_PLAYER, STATE_KIT, STATE_CHARACTER_SHEET, STATE_PET_MENU, STATE_DEAD)


def _apart(ax: int, ay: int, bx: int, by: int) -> int:
    return (ax - bx) ** 2 + (ay - by) ** 2


class EffectsMixin:
    # ------------------------------------------------------------------
    # The gate
    # ------------------------------------------------------------------

    def _gate(self, door: str, *, target=None, item=None, worn: bool = False,
              toward: bool = False, possible=None) -> bool:
        """The one check every action passes. True: go on. False: the gate
        has said why and spent whatever the try costs; the caller returns.
        ``possible`` (a callable) says whether it could otherwise be done: a
        price (a fall, a drop, a fizzle, the thaw's turn) is never charged
        for what could not, which goes on to its own free refusal."""
        p = self.player
        if not getattr(p, 'status_effects', None):
            return True
        v = action_gate.verdict(
            p, door, target=target, worn=worn, toward=toward,
            cornered=self._fear_cornered(target) if door == 'strike' else False,
            source_here=self._effect_source('charmed') is not None,
            flame=self._flame_in_hand())
        if v.open:
            return True
        if (possible is not None and not possible()
                and v.what in (action_gate.FALL, action_gate.DROP, action_gate.FIZZLE, action_gate.THAW)):
            return True
        self._gate_closed(v, target=target, item=item)
        return False

    def _gate_closed(self, v, *, target=None, item=None) -> None:
        """Carry out what the gate answered."""
        p = self.player
        if self.state not in _STAYS:
            self.state = STATE_PLAYER
        words = {}
        if v.key.startswith(('feared_', 'charmed_')):
            words['the'] = self._effect_name(v.effect, target)
        # The line is the cue alone (Brandon 2026-11-22: "a cue, not a
        # soliloquy"): what the hero could do instead, and the counter (a
        # lit torch thaws ice, Guard keeps him steady), are the status's own
        # words and the help screen's (Monsters and Their Ways).
        if v.what == action_gate.REFUSE:
            self.add_message(effect_rules.line(v.key, **words), 'warning')
            return
        if v.what == action_gate.LOSE:
            self.add_message(effect_rules.line(v.key, **words),
                             'danger' if v.effect == 'paralyzed' else 'warning')
        elif v.what == action_gate.STAND:
            self._stand_up(advance=False)
        elif v.what == action_gate.THAW:
            from status_effects import GRACE_TURNS
            p.status_effects.pop('frozen', None)
            p.status_effects['control_immune'] = GRACE_TURNS + 1
            self.add_message(effect_rules.line('thaw'), 'success')
        elif v.what == action_gate.FALL:
            action_gate.paid(p, v)
            p.status_effects['knocked_down'] = 1
            self.add_message(effect_rules.line('fall'), 'danger')
        elif v.what == action_gate.DROP:
            action_gate.paid(p, v)
            self._fumble_drop(item)
        elif v.what == action_gate.FIZZLE:
            action_gate.paid(p, v)
            self.add_message(effect_rules.line('fizzle'), 'warning')
        self._advance_turn()

    def _stand_up(self, advance: bool = True) -> None:
        from status_effects import FOOTING_TURNS
        self.player.status_effects.pop('knocked_down', None)
        # (One more: the turn he stands in ticks it, as it does the thaw's.)
        self.player.status_effects['footing'] = FOOTING_TURNS + 1
        self.add_message(effect_rules.line('stand'), 'info')
        if advance:
            self._advance_turn()

    def _fumble_drop(self, item) -> None:
        """One of ``item`` falls underfoot, unbroken. Picking it up is the
        usual turn; a remembered piece goes back where it was (loadouts)."""
        p = self.player
        held = item is not None and any(i is item for i in p.inventory)
        if not held or self._inside_rock():
            self.add_message(effect_rules.line('drop_plain'), 'warning')
            return
        name = self._bare_name(item)
        down = p.drop_stack(item, 1)
        if down is None:
            self.add_message(effect_rules.line('drop_plain'), 'warning')
            return
        down.x, down.y = p.x, p.y
        self.ground_items.append(down)
        self.add_message(effect_rules.line('drop', item=name), 'warning')

    def _flame_in_hand(self) -> bool:
        import lights
        lt = lights.held(self.player)
        return lt is not None and lights.is_lit(lt)

    # ------------------------------------------------------------------
    # Who laid it
    # ------------------------------------------------------------------

    def _effect_source(self, effect: str, seen: bool = True):
        """The creature whose ``effect`` is on the hero: here, living and
        (``seen``) in his sight."""
        if not effect_rules.running(self.player, effect):
            return None
        m = effect_rules.source_in(self.monsters, effect_rules.bout(self.player, effect).get('by'))
        if m is None or (seen and not self._sees_monster(m)):
            return None
        return m

    def _effect_name(self, effect: str, target=None) -> str:
        from monster import the_name
        m = self._effect_source(effect) or target
        return the_name(m, lower=True) if m is not None else 'it'

    def _fears(self):
        """What he will not go nearer: what frightened him, or with no one
        to name (a bad meal, an older save) the nearest foe in sight."""
        p = self.player
        if not p.has_effect('feared'):
            return None
        if effect_rules.bout(p, 'feared').get('by'):
            return self._effect_source('feared')
        from game_combat import _is_bystander
        foes = [m for m in self.monsters
                if m.alive and not getattr(m, 'is_allied', False) and not _is_bystander(m)
                and self._sees_monster(m)]
        return min(foes, key=lambda m: _apart(m.x, m.y, p.x, p.y), default=None)

    # ------------------------------------------------------------------
    # A step
    # ------------------------------------------------------------------

    def _tile_open_to_hero(self, x: int, y: int) -> bool:
        """He could step there: ground (or what phasing or levitation makes
        ground), no creature on it, nothing standing in it."""
        from dungeon import DOOR, LAVA, WATER
        d, p = self.dungeon, self.player
        if not d.in_bounds(x, y) or monster_at_tile(self.monsters, x, y) is not None:
            return False
        through = p.has_effect('phasing')
        if (x, y) in d.fixture_blocks and not through:
            return False
        t = d.tiles[y][x]
        if t == DOOR or d.is_walkable(x, y):
            return True
        if t in (WATER, LAVA):
            return p.has_effect('levitating')
        return through

    def _fear_cornered(self, target=None) -> bool:
        """No step takes him away from what frightens him."""
        if not self.player.has_effect('feared'):
            return False
        foe = self._fears() or target
        if foe is None:
            return False
        p = self.player
        if any(p.has_effect(e) for e in ('held', 'immobilized', 'frozen', 'in_pit', 'impaled')):
            return True                      # no feet to run on
        px, py = p.x, p.y
        here = _apart(px, py, foe.x, foe.y)
        return not any(_apart(px + dx, py + dy, foe.x, foe.y) > here
                       and self._tile_open_to_hero(px + dx, py + dy)
                       for dx, dy in _STEPS)

    def _gate_bump_dir(self, dx: int, dy: int) -> tuple:
        """Where the hero's key really takes him. Confused, a key at a foe
        still strikes it (Brandon, 2026-11-22: a bump hits like A); any
        other key goes astray. Charmed, a key at no one walks him to the
        charmer."""
        p = self.player
        at = monster_at_tile(self.monsters, p.x + dx, p.y + dy)
        if at is not None and self._sees_monster(at):
            return dx, dy
        if p.has_effect('confused'):
            dx, dy = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)])
            self.add_message("You stumble in a random direction!", 'warning')
        charmer = self._effect_source('charmed')
        if charmer is None:
            return dx, dy
        here = _apart(p.x, p.y, charmer.x, charmer.y)
        ways = [(sx, sy) for sx, sy in _STEPS
                if _apart(p.x + sx, p.y + sy, charmer.x, charmer.y) < here
                and self._tile_open_to_hero(p.x + sx, p.y + sy)]
        from monster import the_name
        if max(abs(charmer.x - p.x), abs(charmer.y - p.y)) <= 1 or not ways:
            self.add_message(effect_rules.line('charmed_near', the=the_name(charmer, lower=True)), 'warning')
            return 0, 0
        step = min(ways, key=lambda w: (_apart(p.x + w[0], p.y + w[1], charmer.x, charmer.y),
                                        w != (dx, dy)))
        if step != (dx, dy):
            self.add_message(effect_rules.line('charmed_step', the=the_name(charmer, lower=True)), 'warning')
        return step

    def _gate_step(self, nx: int, ny: int) -> bool:
        """The step door, for a step onto (nx, ny). A key at a wall is no
        step: nobody falls over for it."""
        p = self.player
        if not p.status_effects:
            return True
        can = self._tile_open_to_hero(nx, ny)
        foe = self._fears()
        toward = bool(foe is not None and can
                      and _apart(nx, ny, foe.x, foe.y) < _apart(p.x, p.y, foe.x, foe.y))
        v = action_gate.verdict(p, 'step', toward=toward,
                                cornered=toward and self._fear_cornered(),
                                flame=self._flame_in_hand())
        if v.open:
            return True
        if not can and v.what == action_gate.FALL:
            return True
        self._gate_closed(v, target=foe)
        if v.what == action_gate.REFUSE and p.has_effect('confused'):
            self._advance_turn()             # a step gone astray is spent
        return False

    def _fled_a_step(self, was: tuple) -> None:
        """He stepped away from what frightens him (Atalanta's three apples
        answer a flight)."""
        p = self.player
        foe = self._fears()
        if foe is None or _apart(p.x, p.y, foe.x, foe.y) <= _apart(was[0], was[1], foe.x, foe.y):
            return
        try:
            from chain_passives import consume_passive_charge
        except ImportError:
            return
        if not getattr(p, '_three_apples_remaining', 0) and consume_passive_charge(p, 'three_apples'):
            p._three_apples_remaining = 3
            self.add_message("Atalanta's three apples scatter behind you!", 'success')

    # ------------------------------------------------------------------
    # The turn, the kill, the floor
    # ------------------------------------------------------------------

    def _effects_after_world(self) -> None:
        """What the world's turn left to the Game: a memory eaten, a hold
        whose owner is dead."""
        p = self.player
        self._effects_dead_eaters()
        for tok in p.__dict__.pop('_pending_forget', None) or ():
            if not effect_rules.running(p, 'forgetting'):
                break                        # deflected, or turned back on it
            m = effect_rules.source_in(self.monsters, tok)
            if m is not None:
                self._mind_eaten_by(m)
        for effect in ('feared', 'charmed'):
            if not effect_rules.running(p, effect):
                continue
            by = effect_rules.bout(p, effect).get('by')
            if by and effect_rules.source_in(self.monsters, by) is None:
                self._bout_over(effect)

    def _bout_over(self, effect: str) -> None:
        p = self.player
        b = effect_rules.bout(p, effect)
        the = b.get('by_the') or b.get('by_name') or 'it'
        from status_effects import end_bout
        end_bout(p, effect)
        self.add_message(effect_rules.line('bout_source_gone', the=the), 'success')

    def _effects_killed(self, monster) -> None:
        """A creature died: what it ate of his mind comes back, and its hold
        on him ends."""
        p = self.player
        owed = mind_theft.owed_by(p, monster)
        for rec in owed:
            copies = self._kind_copies(rec['id'], rec.get('cls')) if rec['what'] == 'item' else ()
            mind_theft.give_back(p, rec, copies)
        if owed:
            self.add_message(effect_rules.line('remembered', what=', '.join(r['name'] for r in owed)), 'success')
            self._merge_newly_known_stacks(force=True)
        for effect in ('feared', 'charmed'):
            if (effect_rules.running(p, effect)
                    and effect_rules.is_source(monster, effect_rules.bout(p, effect).get('by'))):
                self._bout_over(effect)

    def _effects_dead_eaters(self) -> None:
        """An eater a pet, a poison or the world killed gives back now: the
        kill may not have been handled yet (main._reap_unnoticed_kills runs
        as the next action begins, and a stair is taken before that)."""
        p = self.player
        if not mind_theft.records(p):
            return
        for m in list(self.monsters):
            if (not getattr(m, 'alive', True) and getattr(m, 'hp', 1) <= 0
                    and mind_theft.owed_by(p, m)):
                self._effects_killed(m)

    def _effects_left_floor(self) -> None:
        """The floor is left: its creatures' holds end and what they ate is
        lost until learned again."""
        p = self.player
        self._effects_dead_eaters()
        for effect in ('stunned', 'fumbling'):
            if p.status_effects.get(effect, 0) < 0:
                effect_rules.ended(p, effect)     # no end (worn gear): a new bout each floor
        p.__dict__.pop('_pending_forget', None)
        p.status_effects.pop('knocked_down', None)
        from status_effects import end_bout
        for effect in ('feared', 'charmed'):
            if effect_rules.running(p, effect) and effect_rules.bout(p, effect).get('by'):
                end_bout(p, effect)
        gone = mind_theft.lose_all(p)
        if gone:
            self.add_message(effect_rules.line('lost_for_good', what=', '.join(r['name'] for r in gone)), 'danger')

    def _forget_corpses(self, kind: str) -> None:
        """A page gone, its kind's corpses ask again: studying one teaches
        it back. (Given back, the kind knows them all: items.corpse_is_known.)"""
        from items import Corpse
        from main import _all_items_in_save
        state = {'ground_items': list(getattr(self, 'ground_items', []) or []),
                 'level_mgr': getattr(self, 'level_mgr', None)}
        for it in _all_items_in_save(self.player, state):
            if isinstance(it, Corpse) and getattr(it, 'monster_id', None) == kind:
                it.id_level = 0

    def _mind_eaten_by(self, monster) -> None:
        """It eats one identified kind from the pack, or one earned page."""
        from monster import the_name
        from naming import proper_name
        p = self.player
        words = {'The': the_name(monster)}
        meals = ([('item', it) for it in mind_theft.item_candidates(p, self._forgettable)]
                 + [('page', k) for k in mind_theft.page_candidates(p)])
        if not meals:
            self.add_message(effect_rules.line('forgot_nothing', **words), 'warning')
            return
        what, thing = random.choice(meals)
        tok = effect_rules.token(monster)
        if what == 'item':
            # (Its name while he still knows it.)
            name = self._bare_name(thing)
            from items import type_class
            try:
                cls = type_class(thing)
            except Exception:
                cls = None
            mind_theft.eat_item(p, thing, tok, name, self._kind_copies(thing.id, cls))
            self._forget_kind(thing)
            self.add_message(effect_rules.line('forgot_item', item=name, **words), 'danger')
            return
        import kind_data
        kind_name = proper_name((kind_data.defs().get(thing) or {}).get('name') or thing.replace('_', ' '))
        mind_theft.eat_page(p, thing, tok, kind_name)
        self._forget_corpses(thing)
        self.add_message(effect_rules.line('forgot_page', kind=kind_name, **words), 'danger')
