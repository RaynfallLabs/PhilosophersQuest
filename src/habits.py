"""They Learn Your Tricks (AI-2, reads_your_habits, 2026-11-20).

Odysseus's tricks worked once on each foe. A clever creature remembers what
it SAW the hero do on this floor, and its side plays against it:

  choke_fighter     he fights from corridors and doorways: at 2, its side
                    holds its room harder (tactics: hold_choke)
  opens_with_area   he blasts several at once: at 1, its side spreads out
                    round him (flank)
  kiter             he shoots and steps back: at 2, its side no longer
                    waits to be shot (no hold, no waiting for friends)
  rester_near_foes  he rests with foes about: at 2, its side rushes him
                    while he rests (pressing)

No omniscience (Brandon's ruling): only a witness learns, a creature with
a mind that learns (cunning, soldier, trickster) that can SEE the hero when
he does it (senses.sees), and it tells its own side (its band, its pack,
its family: faction.ai_faction). An invisible hero teaches nothing; a pet's
deed is not the hero's. A sighting counts once a fight (`apart` turns), and
only the last `memory` turns are remembered. The record lives on the floor
(dungeon.habits: {side: {habit: [turns]}}), so a new floor starts fresh and
an old save has none.

The Game's hooks (one line each): the hero's melee attack (choke_fighter),
a ranged shot at four tiles or more (kiter), a rest (rester_near_foes), and
the hero's blows on two or more creatures in one turn (opens_with_area).
Pure module.
"""
from __future__ import annotations

HABITS = ('choke_fighter', 'opens_with_area', 'kiter', 'rester_near_foes')


def rules() -> dict:
    import tactics
    return tactics.data().get('habits') or {}


def side_of(m) -> str:
    import faction
    f = faction.ai_faction(m)
    return f'{f[0]}:{f[1]}'


def learner(m) -> bool:
    """A creature whose side learns from what it sees."""
    import tactical_mind
    import tactics
    mind = tactical_mind.mind_of(m)
    return bool(mind and tactics.spec(mind).get('learns') and not tactical_mind.excluded(m))


def witnesses(monsters, player, dungeon) -> list:
    """The learners that can see the hero now."""
    import senses
    if player is None or player.has_effect('invisible'):
        return []
    out = []
    for m in monsters or ():
        if not getattr(m, 'alive', False) or not learner(m):
            continue
        if any(int((m.status_effects or {}).get(e, 0) or 0) > 0
               for e in ('sleeping', 'paralyzed', 'blinded')):
            continue
        if senses.sees(m, player, dungeon):
            out.append(m)
    return out


def note(dungeon, habit: str, seen_by, turn: int) -> list:
    """The witnesses ``seen_by`` saw the hero do ``habit`` on game turn
    ``turn``: each of their sides counts it once (not again within `apart`
    turns). Returns the sides that counted it."""
    if dungeon is None or habit not in HABITS:
        return []
    r = rules()
    apart = int(r.get('apart', 30))
    book = {k: {h: list(v) for h, v in (hv or {}).items()}
            for k, hv in (dungeon.__dict__.get('habits') or {}).items()}
    counted = []
    for side in sorted({side_of(m) for m in seen_by or ()}):
        turns = book.setdefault(side, {}).setdefault(habit, [])
        if turns and int(turn) - int(turns[-1]) < apart:
            continue
        turns.append(int(turn))
        counted.append(side)
    if counted:
        dungeon.__dict__['habits'] = book
    return counted


def count(dungeon, m, habit: str, turn: int | None = None) -> int:
    """How many times ``m``'s side has seen ``habit`` within `memory` turns."""
    if dungeon is None:
        return 0
    book = dungeon.__dict__.get('habits') or {}
    turns = (book.get(side_of(m)) or {}).get(habit) or ()
    if not turns:
        return 0
    if turn is None:
        import tactical_mind
        turn = tactical_mind.TURN.n
    memory = int(rules().get('memory', 300))
    if not turn:
        return len(turns)
    return sum(1 for t in turns if int(turn) - int(t) <= memory)


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


def hero_shot(game, target) -> list:
    """The hero shoots from four tiles or more: the kiter's way."""
    p = getattr(game, 'player', None)
    if p is None or target is None:
        return []
    if max(abs(target.x - p.x), abs(target.y - p.y)) < 4:
        return []
    return _game_note(game, 'kiter')


def hero_rest(game) -> list:
    """The hero rests while a foe can see him."""
    return _game_note(game, 'rester_near_foes')


def hero_struck(game, m) -> list:
    """One of the hero's blows landed on ``m`` (monster.HERO_STRUCK): two or
    more creatures struck in one turn is an area blast. A damage-over-time
    tick is never a blow."""
    if m is None or getattr(m, '__dict__', {}).get('_dot_tick'):
        return []
    if getattr(game, '_damage_by', 'hero') != 'hero':
        return []
    turn = int(getattr(game, 'turn_count', 0) or 0)
    was = game.__dict__.get('_tm_struck')
    hit = set(was[1]) if isinstance(was, tuple) and was[0] == turn else set()
    hit.add(id(m))
    game.__dict__['_tm_struck'] = (turn, frozenset(hit))
    if len(hit) == 2:
        return _game_note(game, 'opens_with_area')
    return []
