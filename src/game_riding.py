"""RidingMixin: riding the Bococho, the game's side (the rules are
src/riding.py; the words and numbers data/bococho.json ``riding``).

* **Mount / dismount** (``_toggle_ride``): Shift+R on the map, or M on her
  card in the pet menu. Getting on needs her beside the hero, grown enough
  to carry him (not the chick), no hostile in sight, no Overload, no state
  that unseats, no pit. Either way costs one turn.
* **The step** (``_riding_second_step``, from Game._do_move): mounted, a
  step covers two tiles; the second only when the first was clean (no trap
  or hazard, no foe come into view, no slide on ice) and the second is open
  ground with nobody on it. Both tiles are stepped on as tiles are: traps
  and hazards (``_check_floor_trap``), pits, what lies there and the
  stairs. One move is one turn for the world: riding is speed over the
  ground, never free turns.
* **Set down at once, with a line** (``_riding_set_down``): a hostile in
  view, a blow (theft is a blow), a trap or hazard, any quiz starting
  (``_riding_quiz_starts``, the quiz engine's start hook: an attack, a
  spell, a wand, any quiz action), the stairs and every other way off the
  floor (she follows, as every companion does), a status that unseats,
  being Overloaded, her being stored in her sphere (the one-companion rule,
  Recall) or hurt, her special, the hero's death.
* **She is under him** (``_mount``): the pet with ``ridden`` set. She takes
  no turn of her own (game_combat._do_pet_turns), stands on his tile, and is
  not drawn apart: the map draws her saddled picture with the hero on it
  (game_bococho_render ``_draw_rider``).
* **Saddlebags** (``_sync_saddlebags``): while the Bococho is out with the
  hero, ``Player.saddlebag_lb`` holds her carry (data ``pet.saddlebags_lb``)
  and Player.get_carry_limit adds it, so every load line (Light, Heavy,
  Burdened, Overloaded) moves up with it. Synced every turn and when she joins,
  leaves, is stored or falls.

The hero's ``riding`` flag is on the Player (class default False: an old
save loads unmounted); a save while mounted loads mounted.
"""
from __future__ import annotations

import riding
from game_states import STATE_PLAYER, STATE_DEAD
from geom import monster_at_tile


class RidingMixin:

    # ---- who ---------------------------------------------------------------

    def _mount(self):
        """The Bococho the hero is riding, or None."""
        for p in getattr(self, 'pets', None) or ():
            if getattr(p, 'ridden', False) and getattr(p, 'alive', False):
                return p
        return None

    def _bococho_companion(self):
        """The hero's Bococho, out with him on this floor, or None."""
        for p in getattr(self, 'pets', None) or ():
            if riding.is_bococho(p) and getattr(p, 'alive', False):
                return p
        return None

    def _riding_foe(self):
        """A hostile the hero can see (the first), or None."""
        from game_combat import _is_bystander
        for m in getattr(self, 'monsters', None) or ():
            if getattr(m, 'alive', False) and not _is_bystander(m) and self._sees_monster(m):
                return m
        return None

    # ---- saddlebags --------------------------------------------------------

    def _sync_saddlebags(self) -> int:
        """Her saddlebags count while she is out with the hero."""
        import bococho_encounter
        pet = self._bococho_companion()
        lb = int(bococho_encounter.data()['pet'].get('saddlebags_lb', 0)) if pet is not None else 0
        if int(getattr(self.player, 'saddlebag_lb', 0) or 0) != lb:
            self.player.saddlebag_lb = lb
        return lb

    # ---- on and off --------------------------------------------------------

    def _toggle_ride(self, pet=None) -> bool:
        """Mount (or dismount) the Bococho: one turn. True when it happened."""
        p = self.player
        if getattr(p, 'riding', False):
            mount = self._mount()
            self._riding_set_down('dismount' if mount is not None else 'gone')
            self.state = STATE_PLAYER
            self._advance_turn()
            return True
        pet = pet or self._bococho_companion()
        from boss_levels import is_side_floor
        foe = self._riding_foe()
        reason = riding.mount_refusal(p, pet, foe_in_sight=foe,
                                      side_floor=is_side_floor(getattr(self, 'dungeon_level', 1)))
        if reason:
            from monster import the_name
            self.add_message(riding.refusal_line(
                reason, getattr(pet, 'name', 'she') if pet is not None else 'she',
                the_name(foe, lower=True) if foe is not None else 'it'), 'warning')
            return False
        p.riding = True
        pet.ridden = True
        pet.x, pet.y = p.x, p.y
        self._ride_blows = self._hero_blows()
        self._ride_hp = int(pet.hp)
        self.add_message(riding.data()['mount'].replace('{pet}', pet.name), 'success')
        self.state = STATE_PLAYER
        self._advance_turn()
        return True

    def _riding_set_down(self, reason: str, foe=None, quiet: bool = False) -> bool:
        """Off the saddle at once, with the reason's line (data
        ``set_down``; 'dismount' is the hero's own choice). True when he was
        riding."""
        p = getattr(self, 'player', None)
        if p is None or not getattr(p, 'riding', False):
            return False
        mount = None
        for pet in getattr(self, 'pets', None) or ():
            if getattr(pet, 'ridden', False):
                mount = pet
                pet.ridden = False
        p.riding = False
        if mount is not None and getattr(mount, 'alive', False):
            self._riding_place_beside(mount)
        if quiet:
            return True
        name = getattr(mount, 'name', None) or 'your Bococho'
        if reason == 'dismount':
            text = riding.data()['dismount'].replace('{pet}', name)
        else:
            from monster import the_name
            text = riding.set_down_line(reason, name,
                                        the_name(foe, lower=True) if foe is not None else 'it')
        if text:
            self.add_message(text, 'info' if reason in ('dismount', 'quiz', 'stairs', 'stored',
                                                        'special', 'gone') else 'warning')
        return True

    def _riding_place_beside(self, pet):
        """Set her down on a free tile beside the hero (behind him first)."""
        p = self.player
        fx = -int(getattr(p, '_facing_dx', 0) or 0)
        fy = -int(getattr(p, '_facing_dy', 0) or 0)
        order = [(fx, fy)] if (fx or fy) else []
        order += [(dx, dy) for r in (1, 2) for dx in range(-r, r + 1) for dy in range(-r, r + 1)
                  if max(abs(dx), abs(dy)) == r and (dx, dy) != (fx, fy)]
        for dx, dy in order:
            t = (p.x + dx, p.y + dy)
            if (self.dungeon.is_walkable(*t) and monster_at_tile(self.monsters, *t) is None
                    and not any(o is not pet and getattr(o, 'alive', False) and (o.x, o.y) == t
                                for o in list(self.pets) + self._escorts_here())
                    and t not in getattr(self.dungeon, 'pits', set())):
                pet.x, pet.y = t
                return
        pet.x, pet.y = p.x, p.y

    # ---- the hooks ---------------------------------------------------------

    def _riding_quiz_starts(self, subject=None) -> None:
        """Any quiz starting (an attack, a spell, a wand, a scroll...): on
        his own feet first (the quiz engine's start hook)."""
        self._riding_set_down('quiz')

    def _riding_level_change(self, via: str = 'stairs') -> None:
        """Off any floor: down from the saddle at the stair; she follows."""
        if via == 'stairs':
            self._riding_set_down('stairs')
        elif via == 'trapdoor':
            self._riding_set_down('trap')
        else:
            self._riding_set_down('gone')

    def _riding_sync(self) -> None:
        mount = self._mount()
        if mount is not None:
            mount.x, mount.y = self.player.x, self.player.y

    def _riding_tick(self) -> None:
        """Once a turn, after the world has moved (Game._advance_turn): the
        saddlebags, and whatever sets the hero down."""
        self._sync_saddlebags()
        p = self.player
        if not getattr(p, 'riding', False):
            for pet in getattr(self, 'pets', None) or ():
                if getattr(pet, 'ridden', False):
                    pet.ridden = False             # (an old or odd state: nobody up)
            return
        if p.is_dead() or self.state == STATE_DEAD:
            self._riding_set_down('gone', quiet=True)
            return
        mount = self._mount()
        ok = mount is not None and mount in self.pets
        struck = self._hero_blows() > int(self.__dict__.get('_ride_blows', 0) or 0)
        foe = self._riding_foe()
        hurt = ok and int(mount.hp) < int(self.__dict__.get('_ride_hp', mount.hp) or mount.hp)
        reason = riding.set_down_reason(p, foe=foe, struck=struck, pet_ok=ok, pet_hurt=hurt)
        if reason:
            self._riding_set_down(reason, foe)
            return
        self._riding_sync()
        self._ride_blows = self._hero_blows()
        self._ride_hp = int(mount.hp)

    def _riding_second_step(self, dx: int, dy: int, first_tile_ice: bool = False) -> bool:
        """The second tile of a mounted step (Game._do_move, after the first
        landed cleanly). True when he ran on to it. No turn is spent here:
        the move's one turn is the caller's."""
        p = self.player
        if not getattr(p, 'riding', False) or first_tile_ice:
            self._riding_sync()
            return False
        if self.state != STATE_PLAYER or p.is_dead():
            return False
        if p.has_effect('in_pit'):
            self._riding_set_down('trap')
            return False
        foe = self._riding_foe()
        if foe is not None:
            self._riding_set_down('foe', foe)
            return False
        mount = self._mount()

        def walkable(x, y):
            return self.dungeon.is_walkable(x, y)

        def occupied(x, y):
            if monster_at_tile(self.monsters, x, y) is not None:
                return True
            return any(o is not mount and getattr(o, 'alive', False) and (o.x, o.y) == (x, y)
                       for o in list(self.pets) + self._escorts_here())
        nxt = riding.second_step((p.x, p.y), dx, dy, walkable, occupied)
        if nxt is None:
            self._riding_sync()
            return False
        # The tile run over is stepped on: what lies there, and the stair.
        self._notify_ground(p.x, p.y)
        p.x, p.y = nxt
        self._riding_sync()
        self._check_floor_trap(p.x, p.y)
        if p.is_dead():
            return True
        if (p.x, p.y) in getattr(self.dungeon, 'pits', set()):
            self._riding_set_down('trap')
            self._player_fall_in_pit(p.x, p.y)
        self._refresh_fov()
        if getattr(p, 'riding', False):
            foe = self._riding_foe()
            if foe is not None:
                self._riding_set_down('foe', foe)
        return True
