"""Escorts: people the hero walks somewhere (DEEDS_KARMA_DESIGN.md sections 4.9
and 6.2, with Brandon's decision 11).

An escort follows the hero, never attacks, and is lost if it dies, is left
behind (more than ``leash`` tiles away when the hero takes a stair) or is
parted from the hero by anything that is not a stair (a level warp, a
potion, a trapdoor). A trapdoor loss is the floor's fault and gets its own
journal line, but it is still a loss: 0 karma either way, as for any escort.

* ``Game.escorts`` is its own list, never ``Game.pets``: the pet menus, Soul
  Sphere logic, pet XP and quiz-accuracy damage never see an escort.
* ``_do_escort_turns`` runs right after ``_do_pet_turns`` whether or not the
  hero has a pet, and monsters swipe at escorts in their own pass
  (``_monster_swipes``).
* ``_occupants()`` is the one occupancy helper: the hero, live pets and live
  escorts on this floor. Every spawn landing, teleport landing, monster move
  and settle check that must count bodies uses it.
* Only a stair descent counts down ``floors_left``. An up stair carries the
  escort without counting. The Cow Level suspends every escort where it
  stands; coming back unsuspends it in place.
* HP never regenerates (a frightened person does not heal mid-dungeon); a
  thrown potion can still reach them.

LORE NOT FLOOR: an escort's HP and AC are fixed numbers in its data.
"""
from __future__ import annotations

import copy

from pet_system import Pet

from boss_levels import COW_LEVEL
STRAGGLE_EXTRA = 6         # beyond the leash
STRAGGLE_TURNS = 10        # this long, and they stop and wait


class Escort(Pet):
    """A person following the hero. Built from an escort spec; reuses the
    pet follow routine and nothing else of a pet."""

    is_escort = True

    def __init__(self, spec: dict, x: int, y: int, *, source: str = '', floor: int = 1,
                 person: dict | None = None):
        from naming import proper_name
        name = proper_name(spec.get('name') or spec.get('id') or 'Stranger')
        color = tuple(spec.get('color') or (200, 180, 140))
        self.species_key = 'escort'
        self.species = {
            'element': 'none', 'damage_type': 'physical', 'color': color,
            'stages': [{'name': name, 'symbol': '@', 'msg': ''}] * 3, 'specials': [],
        }
        self.level = 1
        self.xp = 0
        self.x, self.y = int(x), int(y)
        self.alive = True
        self._regen_timer = 0
        self._passive_xp_timer = 0
        self.nickname = ''
        self.kills_count = 0
        self._special_cooldowns = {}
        self.command = 'return'
        self.last_pet_floor = -1
        self.rescue_spent_at = 0
        self.escort_id = str(spec.get('id') or 'escort')
        self.display_name = name
        self.sprite_id = spec.get('sprite_id', 'npc_traveler')
        self.max_hp = self.hp = max(1, int(spec.get('hp', 20)))
        # Hero-style armour class: lower is better, 10 is unarmoured (CODE-01).
        ac = spec.get('ac')
        self.ac = 10 if ac is None else int(ac)
        self.base_damage = 0
        self.goal = str(spec.get('goal', 'stairs_down'))
        self.leash = max(1, int(spec.get('leash', 2)))
        self.floors_left = max(1, int(spec.get('floors', 1)))
        self.perk = spec.get('perk')
        self.spec = copy.deepcopy(spec)
        self.source = source
        self.person = dict(person) if isinstance(person, dict) else {
            'id': self.escort_id, 'name': name}
        self.floor = int(floor)
        self.suspended = False
        self.waiting = False
        self._straggle = 0
        self._warned = False

    # A person, not a species.
    @property
    def name(self) -> str:
        return self.display_name

    @property
    def species_name(self) -> str:
        return self.display_name

    @property
    def symbol(self) -> str:
        return '@'

    def gain_xp(self, amount: int = 1) -> list:
        return []

    def gain_xp_passive(self) -> list:
        return []

    def tick_regen(self, bonus: int = 0):
        return None                         # never heals on its own

    def take_turn(self, player, dungeon, monsters, pets, ground_items=None):
        """Follow the hero; never attack. A straggler stops and waits."""
        if not self.alive or self.suspended:
            return None
        dist = max(abs(self.x - player.x), abs(self.y - player.y))
        if self.waiting:
            if dist <= self.leash:
                self.waiting = False
                self._straggle = 0
            return None
        if dist > self.leash + STRAGGLE_EXTRA:
            self._straggle += 1
            if self._straggle >= STRAGGLE_TURNS:
                self.waiting = True
                return None
        else:
            self._straggle = 0
        if dist > 1:
            self._move_toward(player.x, player.y, dungeon, monsters, pets, player, ground_items)
        return None


def resolve_spec(spec, enc: dict | None):
    """An outcome's ``escort``: inline, or ``{"$ref": key}`` into the
    encounter's ``escorts`` map. None when the reference is missing."""
    if not isinstance(spec, dict):
        return None
    if '$ref' in spec:
        ref = ((enc or {}).get('escorts') or {}).get(spec['$ref'])
        if not isinstance(ref, dict):
            return None
        out = copy.deepcopy(ref)
        out.update({k: v for k, v in spec.items() if k != '$ref'})
        return out
    return copy.deepcopy(spec)


def apply_variants(base: dict, variants, check) -> dict:
    """``base`` with the keys of the first variant whose ``when`` holds."""
    out = dict(base or {})
    for v in variants or ():
        if check(v.get('when')):
            out.update({k: val for k, val in v.items() if k != 'when'})
            break
    return out


def occupants(game, *, hero: bool = True) -> set:
    """Tiles a body stands on: the hero, live pets and live escorts on this
    floor. Duck-typed (any object with player / pets / escorts will do)."""
    out = set()
    player = getattr(game, 'player', None)
    if hero and player is not None:
        out.add((player.x, player.y))
    out |= {(p.x, p.y) for p in getattr(game, 'pets', ()) or () if getattr(p, 'alive', False)}
    lvl = getattr(game, 'dungeon_level', None)
    out |= {(e.x, e.y) for e in getattr(game, 'escorts', ()) or ()
            if getattr(e, 'alive', False) and not getattr(e, 'suspended', False)
            and getattr(e, 'floor', None) == lvl}
    return out


class EscortMixin:
    # ------------------------------------------------------------------
    # Bodies
    # ------------------------------------------------------------------

    def _escort_list(self) -> list:
        lst = getattr(self, 'escorts', None)
        if not isinstance(lst, list):
            lst = self.escorts = []
        return lst

    def _escorts_here(self) -> list:
        """Live, unsuspended escorts on this floor."""
        lvl = getattr(self, 'dungeon_level', None)
        return [e for e in self._escort_list()
                if e.alive and not e.suspended and e.floor == lvl]

    def _occupants(self, *, hero: bool = True) -> set:
        """Tiles a body stands on: the hero, live pets and live escorts."""
        return occupants(self, hero=hero)

    def _escort_at(self, x: int, y: int):
        return next((e for e in self._escorts_here() if e.x == x and e.y == y), None)

    def _escort_tile_near_hero(self, taken=()):
        """A free tile beside the hero, four-way neighbours first."""
        from geom import all_occupied_tiles
        px, py = self.player.x, self.player.y
        busy = set(all_occupied_tiles(self.monsters)) | self._occupants() | set(taken)
        rings = [[(px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)],
                 [(px + 1, py + 1), (px - 1, py - 1), (px + 1, py - 1), (px - 1, py + 1)]]
        for r in (2, 3):
            rings.append([(px + dx, py + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)
                          if max(abs(dx), abs(dy)) == r])
        pits = getattr(self.dungeon, 'pits', None) or set()
        for ring in rings:
            for t in ring:
                if (self.dungeon.in_bounds(*t) and self.dungeon.is_walkable(*t)
                        and t not in busy and t not in pits):
                    return t
        return None

    def _escort_tile_reachable(self):
        """The nearest free tile the hero can walk to, or None."""
        from geom import all_occupied_tiles
        px, py = self.player.x, self.player.y
        busy = set(all_occupied_tiles(self.monsters)) | self._occupants()
        pits = getattr(self.dungeon, 'pits', None) or set()
        try:
            reach = self._reachable_tiles(px, py)
        except Exception:
            return None
        near = [t for t in reach if t not in busy and t not in pits
                and self.dungeon.is_walkable(*t)]
        if not near:
            return None
        return min(near, key=lambda t: (max(abs(t[0] - px), abs(t[1] - py)),
                                        abs(t[0] - px) + abs(t[1] - py), t))

    # ------------------------------------------------------------------
    # Starting and ending
    # ------------------------------------------------------------------

    def _spawn_escort(self, spec: dict, *, source: str = '', person=None):
        """Start an escort beside the hero. Returns the Escort or None."""
        if not isinstance(spec, dict):
            return None
        spot = self._escort_tile_near_hero()
        if spot is None:
            # Nothing free within 3: the nearest free tile the hero can walk
            # to, never the hero's own tile (MNK-09).
            spot = self._escort_tile_reachable()
        if spot is None:
            return None
        esc = Escort(spec, *spot, source=source, floor=self.dungeon_level, person=person)
        self._escort_list().append(esc)
        import deeds
        deeds.note(self, f'flag.escorting.{deeds.slug(esc.escort_id)}', source=source)
        self._escort_perk(esc)
        return esc

    def _escort_ctx_check(self, cond) -> bool:
        if not cond:
            return True
        import deeds
        return deeds.check(cond, self._deed_ctx())

    def _escort_end(self, esc, outcome_key: str, *, chron_kind: str, default_line=None):
        """Run ``on_arrive`` or ``on_fail`` (with its variants) and remove the
        escort. An escort never carries karma by itself."""
        if esc in self._escort_list():
            self._escort_list().remove(esc)
        esc.alive = False
        spec = esc.spec or {}
        o = apply_variants(spec.get(outcome_key) or {}, spec.get(f'{outcome_key}_variants'),
                           self._escort_ctx_check)
        if default_line:
            o['chronicle'] = default_line
        o = {k: v for k, v in o.items() if k not in ('karma', 'karma_kind')}
        if o.get('reward'):
            self._apply_npc_reward(o['reward'])
        if o.get('bonus_reward'):
            self._apply_npc_reward(o['bonus_reward'])
        self._apply_outcome_deeds(o, esc.source or f'escort:{esc.escort_id}',
                                  person=esc.person, chron_kind=chron_kind)
        text = o.get('outcome') or ''
        if text:
            self.add_message(text, 'success' if outcome_key == 'on_arrive' else 'danger')
            self._escort_card(esc.name, text)

    def _escort_card(self, title: str, text: str):
        """The outcome card: a story popup, shown only over plain play."""
        from game_states import STATE_PLAYER, STATE_STORY_POPUP
        if getattr(self, 'state', None) != STATE_PLAYER:
            return
        self.popup_data = {'title': str(title).upper(), 'accent': (200, 180, 140),
                           'lines': [text], 'code': None}
        self.popup_next_state = STATE_PLAYER
        self.state = STATE_STORY_POPUP

    def _escort_failed(self, esc, why: str):
        """``why``: 'died', 'left_behind' or 'trapdoor'."""
        import deeds
        slug = deeds.slug(esc.escort_id)
        default = None
        if why in ('left_behind', 'trapdoor'):
            deeds.note(self, f'flag.escort_left_behind.{slug}', source=esc.source)
        if why == 'trapdoor':
            # Brandon, decision 11: still a loss, with its own line that
            # says it was the floor's fault.
            deeds.note(self, f'flag.escort_trapdoor.{slug}', source=esc.source)
            default = (esc.spec or {}).get('on_fail_trapdoor') or (
                f"The floor gave way and dropped me a level, and {esc.name} was left "
                "above. That was the floor's doing, not mine. It does not feel that way.")
        elif why == 'left_behind':
            self.add_message(f"You have left {esc.name} behind.", 'danger')
        else:
            self.add_message(f"{esc.name} falls and does not get up.", 'danger')
        self._escort_end(esc, 'on_fail', chron_kind='loss', default_line=default)

    def _escort_arrived(self, esc):
        self._escort_end(esc, 'on_arrive', chron_kind='consequence')

    # ------------------------------------------------------------------
    # Turns
    # ------------------------------------------------------------------

    def _do_escort_turns(self):
        """Move, perk and goal for each escort here, then the monsters'
        swipes at them (their own pass: escorts are attacked with no pet)."""
        here = self._escorts_here()
        if not here:
            return
        bodies = list(getattr(self, 'pets', []) or []) + here
        for esc in here:
            was_waiting = esc.waiting
            esc.take_turn(self.player, self.dungeon, self.monsters, bodies, self.ground_items)
            if esc.waiting and not was_waiting and not esc._warned:
                esc._warned = True
                self.add_message(f"{esc.name} has fallen behind and stopped to wait for you.",
                                 'warning')
            self._escort_perk(esc)
        for esc, _m in self._monster_swipes(here, escorts=True):
            self._escort_failed(esc, 'died')
        for esc in self._escorts_here():
            if self._escort_goal_reached(esc):
                self._escort_arrived(esc)

    def _escort_goal_reached(self, esc) -> bool:
        goal = esc.goal or ''
        if not goal.startswith('tile:'):
            return False
        kind = goal.split(':', 1)[1]
        near = max(abs(esc.x - self.player.x), abs(esc.y - self.player.y)) <= esc.leash
        if not near:
            return False
        if kind == 'altar':
            return bool(self.dungeon.is_altar(self.player.x, self.player.y)
                        or self.dungeon.is_altar(esc.x, esc.y))
        import dungeon as _dg
        want = getattr(_dg, kind.upper(), None)
        if want is None:
            return False
        return want in (self.dungeon.tiles[self.player.y][self.player.x],
                        self.dungeon.tiles[esc.y][esc.x])

    def _escort_perk(self, esc):
        if esc.perk == 'reveal_traps' and esc.alive and not esc.suspended:
            r = max(1, int(getattr(self.player, 'PER', 10) or 10))
            for (tx, ty), trap in (getattr(self.dungeon, 'traps', None) or {}).items():
                if max(abs(tx - esc.x), abs(ty - esc.y)) <= r and isinstance(trap, dict):
                    trap['revealed'] = True

    def _escort_sight_bonus(self) -> int:
        """The 'light' perk: +2 sight while the escort is here."""
        return 2 if any(e.perk == 'light' for e in self._escorts_here()) else 0

    # ------------------------------------------------------------------
    # Floor changes (called from _change_level)
    # ------------------------------------------------------------------

    def _escorts_leaving(self, old_level: int, new_level: int, via: str):
        """Before the old floor is torn down. Returns (carried, arrived):
        escorts that come along, and escorts whose last stair this was
        (their on_arrive fires after arrival)."""
        carried, arrived = [], []
        if new_level == COW_LEVEL:
            for e in self._escort_list():
                if e.alive and e.floor == old_level:
                    e.suspended = True          # they wait in the pasture's shadow
            return carried, arrived
        if old_level == COW_LEVEL:
            for e in self._escort_list():
                if e.alive and e.suspended and e.floor == new_level:
                    e.suspended = False
                    # Seated beside the hero at the stair (SAV-06): left
                    # where she stood, she was far behind the first step
                    # and lost as "left behind".
                    carried.append(e)
            return carried, arrived
        stairs = via == 'stairs' and abs(new_level - old_level) == 1
        for e in list(self._escort_list()):
            if not e.alive or e.suspended or e.floor != old_level:
                continue
            near = max(abs(e.x - self.player.x), abs(e.y - self.player.y)) <= e.leash
            if not stairs:
                self._escort_failed(e, 'trapdoor' if via == 'trapdoor' else 'left_behind')
                continue
            if not near:
                self._escort_failed(e, 'left_behind')
                continue
            # 'stairs_down' counts stairs taken down; 'stairs_up' counts
            # stairs taken up (a civilian walked back toward the surface).
            step = {'stairs_down': 1, 'stairs_up': -1}.get(e.goal)
            if step is not None and new_level == old_level + step:
                e.floors_left -= 1
                if e.floors_left <= 0:
                    arrived.append(e)
                    e.floor = new_level
                    continue
            e.floor = new_level
            carried.append(e)
        return carried, arrived

    def _escorts_place(self, carried):
        """After the hero stands on the new floor: set each escort that came
        along beside him (before the spawners, so _occupants() counts them)."""
        taken = set()
        for e in carried:
            spot = self._escort_tile_near_hero(taken)
            if spot is None:
                spot = (self.player.x, self.player.y)
            e.x, e.y = spot
            e.waiting = False
            e._straggle = 0
            taken.add(spot)

    def _escorts_finish(self, arrived):
        for e in arrived:
            if e in self._escort_list():
                self._escort_arrived(e)
