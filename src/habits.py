"""They Learn Your Tricks (AI-2, reads_your_habits, 2026-11-20).

Odysseus's tricks worked once on each foe. A clever creature remembers what
it SAW the hero do on this floor, and plays against it:

  choke_fighter     he fights from corridors and doorways: at 2, it holds
                    its room harder (tactics: hold_choke)
  opens_with_area   he blasts several at once: at 1, it spreads out round
                    him (flank)
  kiter             he shoots from afar and steps back: at 2, it no longer
                    waits to be shot (no hold, no waiting for friends)
  rester_near_foes  he rests with foes about: at 2, it rushes him while he
                    rests (pressing)

No omniscience (Brandon's ruling; the audit of 2026-11-20). The lesson lives
on the witness itself: a creature with a mind that learns (cunning,
soldier, trickster) that SAW the hero do it (senses.sees). It knows what it
saw, and it tells its own band or pack while they can hear it: a mate of the
same war-band or pack, awake, within share_reach tiles of the witness. A
creature of the same family elsewhere on the floor learns nothing. When the
witness dies, what it saw dies with it ("leave no one to tell"). An
invisible hero teaches nothing; a pet's deed is not the hero's. A sighting
counts once a fight (`apart` turns), and only the last `memory` turns are
remembered. The record is the creature's own (``_tm_habits``), so it is
saved with it and an old save has none.

The Game's hooks (one line each): the hero's melee attack (choke_fighter),
a ranged shot at four tiles or more (kiter, counted only when his next
action takes him farther from the one he shot), a rest (rester_near_foes),
the hero's blows (opens_with_area: two or more creatures struck by one
action of his; ``close_action`` at the start of Game._advance_turn and
``world_over`` at its end draw the line between his action and the
world's turn, so a worn item's blow in the world's turn, the Boots of
Thor's arc, never joins his next action's). Pure module.
"""
from __future__ import annotations

HABITS = ('choke_fighter', 'opens_with_area', 'kiter', 'rester_near_foes')
SHARE_REACH = 12          # a band's or a pack's shout carries this far in its camp


def rules() -> dict:
    import tactics
    return tactics.data().get('habits') or {}


def learner(m) -> bool:
    """A creature that learns from what it sees."""
    import tactical_mind
    import tactics
    mind = tactical_mind.mind_of(m)
    return bool(mind and tactics.spec(mind).get('learns') and not tactical_mind.excluded(m))


def _awake(m) -> bool:
    return not any(int(((getattr(m, 'status_effects', None) or {}).get(e, 0)) or 0) > 0
                   for e in ('sleeping', 'paralyzed', 'stunned', 'frozen'))


def witnesses(monsters, player, dungeon) -> list:
    """The learners that can see the hero now."""
    import senses
    if player is None or player.has_effect('invisible'):
        return []
    out = []
    for m in monsters or ():
        if not getattr(m, 'alive', False) or not learner(m) or not _awake(m):
            continue
        if int((m.status_effects or {}).get('blinded', 0) or 0) > 0:
            continue
        if senses.sees(m, player, dungeon):
            out.append(m)
    return out


def note(dungeon, habit: str, seen_by, turn: int) -> list:
    """The witnesses ``seen_by`` saw the hero do ``habit`` on game turn
    ``turn``: each counts it once a fight (not again within `apart` turns).
    Returns those that counted it. (``dungeon`` is kept for the callers; the
    record is each witness's own.)"""
    if habit not in HABITS:
        return []
    apart = int(rules().get('apart', 30))
    counted = []
    for m in seen_by or ():
        book = {h: list(v) for h, v in (m.__dict__.get('_tm_habits') or {}).items()}
        turns = book.setdefault(habit, [])
        if turns and int(turn) - int(turns[-1]) < apart:
            continue
        turns.append(int(turn))
        m._tm_habits = book
        counted.append(m)
    return counted


def _shares_with(m, o) -> bool:
    """``o`` has told ``m`` what it saw: the same war-band or pack, both
    alive and awake, within shout reach, and ``o`` with a voice to tell it
    in. A silenced witness has none; a babbled one speaks a tongue its own
    no longer understand, and a babbled listener understands no one
    (attack_gates.py: Tacita's Seal, the Confusion of Tongues)."""
    if o is m or not getattr(o, 'alive', False) or not _awake(o) or not _awake(m):
        return False
    try:
        import attack_gates
        if attack_gates.has(o, 'silenced') or attack_gates.babbled(o) or attack_gates.babbled(m):
            return False
    except ImportError:
        pass
    dm, do = m.__dict__, o.__dict__
    same = ((dm.get('_band') and dm.get('_band') == do.get('_band'))
            or (dm.get('_pack') and dm.get('_pack') == do.get('_pack')))
    if not same:
        return False
    return max(abs(m.x - o.x), abs(m.y - o.y)) <= SHARE_REACH


def count(dungeon, m, habit: str, turn: int | None = None, monsters=None) -> int:
    """How many times ``m`` knows of ``habit`` within `memory` turns: what it
    saw itself, and what a living band- or packmate within shout reach saw
    (the most either knows: one sighting is not two because two heard it)."""
    if turn is None:
        import tactical_mind
        turn = tactical_mind.TURN.n
    memory = int(rules().get('memory', 300))

    def recent(o) -> int:
        turns = ((o.__dict__.get('_tm_habits') or {}).get(habit)) or ()
        if not turn:
            return len(turns)
        return sum(1 for t in turns if int(turn) - int(t) <= memory)
    best = recent(m) if getattr(m, 'alive', True) else 0
    for o in monsters or ():
        if _shares_with(m, o):
            best = max(best, recent(o))
    return best


# ---------------------------------------------------------------------------
# The Game's hooks (duck-typed: anything with player, dungeon, monsters,
# turn_count)
# ---------------------------------------------------------------------------

def _game_note(game, habit: str) -> list:
    p = getattr(game, 'player', None)
    d = getattr(game, 'dungeon', None)
    if p is None or d is None:
        return []
    seen = witnesses(getattr(game, 'monsters', None) or (), p, d)
    if not seen:
        return []
    return note(d, habit, seen, int(getattr(game, 'turn_count', 0) or 0))


def hero_melee(game, target=None) -> list:
    """The hero strikes in melee: fighting from a narrow way is the
    corridor trick."""
    import tactical_mind
    p = getattr(game, 'player', None)
    d = getattr(game, 'dungeon', None)
    if p is None or d is None or not tactical_mind.narrow(d, p.x, p.y):
        return []
    return _game_note(game, 'choke_fighter')


def hero_shot(game, target) -> None:
    """The hero shoots from four tiles or more: it is the kiter's way only if
    his next action takes him farther from the one he shot (close_action
    judges it)."""
    p = getattr(game, 'player', None)
    if p is None or target is None:
        return
    dist = max(abs(target.x - p.x), abs(target.y - p.y))
    if dist < 4:
        return
    game.__dict__['_tm_shot'] = {'at': (int(target.x), int(target.y)), 'dist': dist, 'stage': 'shot'}


def hero_rest(game) -> list:
    """The hero rests while a foe can see him."""
    return _game_note(game, 'rester_near_foes')


def hero_struck(game, m) -> None:
    """One of the hero's blows landed on ``m`` (monster.HERO_STRUCK), in
    the action now open. A damage-over-time tick is never a blow, and only
    the hero's own blows count."""
    if m is None or getattr(m, '__dict__', {}).get('_dot_tick'):
        return
    if getattr(game, '_damage_by', 'hero') != 'hero':
        return
    if game.__dict__.get('_tm_in_world'):
        return                       # the world's turn (a worn item's arc): not his action
    hit = set(game.__dict__.get('_tm_struck') or ())
    hit.add(id(m))
    game.__dict__['_tm_struck'] = frozenset(hit)


def close_action(game) -> list:
    """The hero's action is over (the start of Game._advance_turn): two or
    more struck by it is an area blast; a shot, then a step back, is the
    kiter's way. The world's turn begins: nothing struck in it is his
    action (world_over ends it). Returns the witnesses that counted."""
    hit = game.__dict__.pop('_tm_struck', None) or ()
    game.__dict__['_tm_in_world'] = True
    out = []
    if len(hit) >= 2:
        out += _game_note(game, 'opens_with_area')
    shot = game.__dict__.get('_tm_shot')
    if isinstance(shot, dict):
        p = getattr(game, 'player', None)
        tx, ty = shot.get('at') or (0, 0)
        if shot.get('stage') == 'shot':
            game.__dict__['_tm_shot'] = dict(shot, stage='after')   # the next action decides
        else:
            game.__dict__.pop('_tm_shot', None)
            # He stepped back: farther from where the one he shot stood.
            if p is not None and max(abs(tx - p.x), abs(ty - p.y)) > int(shot.get('dist', 0)):
                out += _game_note(game, 'kiter')
    return out


def world_over(game) -> None:
    """The world's turn is over (the end of Game._advance_turn): the hero's
    next action begins. (A turn cut short, by a death or a stair, leaves
    the world's mark on: his next blows are then not counted, never wrongly
    counted.)"""
    game.__dict__.pop('_tm_in_world', None)
    game.__dict__.pop('_tm_struck', None)
