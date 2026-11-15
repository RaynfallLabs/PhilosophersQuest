"""Riding the Bococho: the rules, pure (no pygame).

Brandon, 2026-11-14: "We'd need to have riding code, but I like the idea."
The game's side (the keys, the step, the set-downs, the picture) is
src/game_riding.py; every word and number is in data/bococho.json
``riding``.

* **Getting on** (``mount_refusal``): a Bococho grown enough to carry a
  rider (``min_stage``: not the chick), beside the hero, no hostile in
  sight, the hero neither Overloaded, nor in a pit, nor in a state that
  unseats (``unseat_statuses``).
* **Mounted, each step covers two tiles** (``second_step``): the second
  only when the first was clear and the second is walkable and free.
  Both tiles are stepped on as tiles are (traps, hazards, items, stairs).
  One move is still one turn for the monsters: riding is speed over the
  ground, never free turns.
* **Set down at once, with a line** (``set_down_line``): a hostile coming
  into view, a blow, a trap or hazard, a quiz starting, the stairs (she
  follows), a status that unseats, being Overloaded, her being stored in
  her sphere or hurt.
* **Noise** (``step_noise``, ``sleeper_step_factor``): a galloping bird is
  loud.

The hero's ``riding`` flag lives on the Player (a class default of False,
so an old save loads unmounted) and the mount is the pet with ``ridden``
set.
"""
from __future__ import annotations


def data() -> dict:
    import bococho_encounter
    return bococho_encounter.data()['riding']


def is_bococho(pet) -> bool:
    return getattr(pet, 'species_key', None) == 'bococho'


def can_carry(pet) -> bool:
    """Is she grown enough to carry a rider (not the chick)?"""
    return is_bococho(pet) and int(getattr(pet, 'stage', 0)) >= int(data().get('min_stage', 1))


def unseats(player) -> str:
    """The status that would throw the hero from the saddle, or ''."""
    for eid in data().get('unseat_statuses', ()):
        try:
            if player.has_effect(eid):
                return eid
        except Exception:
            continue
    return ''


def overloaded(player) -> bool:
    try:
        return bool(player.is_overloaded())
    except Exception:
        return False


def mount_refusal(player, pet, *, foe_in_sight=None, side_floor=False) -> str:
    """'' when the hero may climb into her saddle now, else the key of the
    refusal line (data ``refuse``)."""
    if pet is None or not is_bococho(pet) or not getattr(pet, 'alive', False):
        return 'none'
    if side_floor:
        return 'side_floor'
    if not can_carry(pet):
        return 'small'
    if max(abs(pet.x - player.x), abs(pet.y - player.y)) > 1:
        return 'far'
    if foe_in_sight is not None:
        return 'foe'
    if overloaded(player):
        return 'overloaded'
    if unseats(player):
        return 'status'
    try:
        if player.has_effect('in_pit'):
            return 'pit'
    except Exception:
        pass
    return ''


def set_down_reason(player, *, foe=None, struck=False, pet_ok=True, pet_hurt=False) -> str:
    """Why the hero is set down after a turn, or '' (ride on). Checked in
    this order: she is gone, a blow, a status, the load, a foe in view, she
    is hurt."""
    if not pet_ok:
        return 'gone'
    if struck:
        return 'blow'
    if unseats(player):
        return 'status'
    if overloaded(player):
        return 'overloaded'
    if foe is not None:
        return 'foe'
    if pet_hurt:
        return 'hurt'
    return ''


def set_down_line(reason: str, pet_name: str, foe_name: str = 'it') -> str:
    lines = data().get('set_down') or {}
    text = lines.get(reason) or lines.get('gone') or ''
    return text.replace('{pet}', pet_name).replace('{foe}', foe_name)


def refusal_line(reason: str, pet_name: str = 'she', foe_name: str = 'it') -> str:
    lines = data().get('refuse') or {}
    return (lines.get(reason) or '').replace('{pet}', pet_name).replace('{foe}', foe_name)


def second_step(start: tuple, dx: int, dy: int, walkable, occupied) -> tuple | None:
    """The tile the second half of a mounted step lands on, or None.
    ``walkable(x, y)``: open ground she can run on (no wall, door, water or
    lava, no blocking fixture); ``occupied(x, y)``: a creature, a pet or a
    person stands there. The first tile was already stepped on cleanly
    (the caller checks that)."""
    if not (dx or dy):
        return None
    tx, ty = start[0] + dx, start[1] + dy
    if not walkable(tx, ty) or occupied(tx, ty):
        return None
    return (tx, ty)


def step_noise(player) -> int:
    """Tiles a mounted hero's steps carry further."""
    return int(data().get('step_noise', 0)) if getattr(player, 'riding', False) else 0


def sleeper_step_factor(player) -> float:
    """How much readier a deep sleeper is to stir at a mounted hero's step."""
    if not getattr(player, 'riding', False):
        return 1.0
    return float(data().get('sleeper_step_factor', 1.0))


def saddled_sprite(stage: int) -> str:
    """The saddled picture for her stage (the chick has none)."""
    sad = data().get('saddled') or {}
    return str(sad.get(str(max(1, min(2, int(stage or 1))))) or 'bococho_saddled')


def seat(sprite_id: str) -> tuple:
    """Where the rider's hips go in a saddled picture's 64 px frame."""
    s = (data().get('seat') or {}).get(sprite_id) or (32, 22)
    return int(s[0]), int(s[1])
