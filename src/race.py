"""The Underway Run: a maths race, pure scoring (no pygame).

Brandon, 2026-11-14 (RARE_PETS_PLAN section 3): "something about racing for
the chocobo". The young Bococho races Gilt Varro's best bird, Brassbeak, on
an oval track. The quiz stays the engine:

* **Five legs.** Each leg is ONE maths chain at the hero's own maths tier
  (as in combat: the tier of the weapon in his hand). Every right answer
  lengthens her stride: the leg's distance is ``base_per_leg`` plus the
  chain times the tier's ``stride`` (a harder sum is worth more ground, so
  a hard weapon is no handicap and an easy one no trick).
* **Sprint or Pace,** chosen before each leg:
    - Sprint: ``sprint_mult`` times the distance, but it costs
      ``sprint_cost`` wind and she runs the NEXT leg winded
      (``winded_mult``). A sprint with too little wind left is a tired
      one: it gives only part of the boost.
    - Pace: steady; she gets back ``pace_recover`` wind.
  On the last leg, the home straight, the wind she has left is her kick:
  up to ``final_kick`` more. So two sprints in a row lose ground (the
  second is run winded), and the bird kept in hand finishes strongest.
* **The cheat.** On leg ``cheat_leg`` Varro has scattered caltrops on the
  inside lane: the inside costs ``caltrops_mult`` of the leg. His taunt
  before that leg is the tell. The outside lane is a little longer
  (``outside_mult``) but clean.
* **Brassbeak** runs a written pace by leg (``varro_pace``) with a little
  luck (``varro_luck``, either way), drawn from the race's own seed so a
  leg run again after a load comes out the same.

The race is a plain dict (saved with the run): see ``new_race``. Every
number is in data/bococho.json ``race``; the caller (src/game_race.py)
runs the quiz and shows the positions.
"""
from __future__ import annotations

import random

MODES = ('sprint', 'pace')
LANES = ('inside', 'outside')


def config(cfg: dict | None = None) -> dict:
    """The race block of data/bococho.json (or `cfg`, for a test)."""
    if cfg is not None:
        return cfg
    import bococho_encounter
    return bococho_encounter.data()['race']


def new_race(seed: int, tier: int, cfg: dict | None = None) -> dict:
    """A race at the line: nothing run yet."""
    c = config(cfg)
    return {
        'seed': int(seed) & 0xFFFFFFFF,
        'tier': max(1, min(5, int(tier or 1))),
        'leg': 0,                       # legs run so far
        'legs': int(c['legs']),
        'hero': 0.0,                    # lengths run by the young Bococho
        'varro': 0.0,                   # lengths run by Brassbeak
        'wind': float(c['wind_start']),
        'winded': False,                # the last leg was a sprint
        'history': [],                  # one dict per leg run (leg_result)
        'done': False,
        'forfeit': False,
    }


def is_cheat_leg(race: dict, cfg: dict | None = None) -> bool:
    """Is the NEXT leg the one Varro has salted with caltrops?"""
    return int(race['leg']) + 1 == int(config(cfg)['cheat_leg'])


def is_final_leg(race: dict) -> bool:
    """Is the NEXT leg the home straight?"""
    return int(race['leg']) + 1 == int(race['legs'])


def stride(tier: int, cfg: dict | None = None) -> float:
    s = config(cfg)['stride']
    return float(s.get(str(max(1, min(5, int(tier or 1)))), s.get('3', 2.0)))


def varro_leg(race: dict, leg_index: int, cfg: dict | None = None) -> float:
    """Brassbeak's lengths on leg ``leg_index`` (0-based): the written pace
    and a little luck from the race's own seed (the same every time that
    leg is run)."""
    c = config(cfg)
    pace = list(c['varro_pace'])
    base = float(pace[min(leg_index, len(pace) - 1)])
    luck = float(c.get('varro_luck', 0.0))
    rng = random.Random(int(race['seed']) * 7919 + leg_index * 104729)
    return max(0.0, base + rng.uniform(-luck, luck))


def hero_leg(race: dict, chain: int, mode: str, lane: str = 'inside',
             cfg: dict | None = None) -> tuple[float, list, dict]:
    """(lengths, events, new state) for the young Bococho's next leg: a
    chain of ``chain`` right answers, run as ``mode`` in ``lane``. Pure:
    `race` is not changed. ``events`` name what happened, in order, for the
    commentary ('winded', 'sprint', 'tired_sprint', 'pace', 'kick',
    'caltrops', 'outside')."""
    c = config(cfg)
    mode = mode if mode in MODES else 'pace'
    lane = lane if lane in LANES else 'inside'
    chain = max(0, int(chain or 0))
    events = []
    dist = float(c['base_per_leg']) + chain * stride(race['tier'], c)
    wind = float(race['wind'])
    if race.get('winded'):
        dist *= float(c['winded_mult'])
        events.append('winded')
    kick_wind = wind
    cost = float(c['sprint_cost'])
    if mode == 'sprint':
        boost = float(c['sprint_mult']) - 1.0
        if wind >= cost:
            dist *= 1.0 + boost
            events.append('sprint')
        else:
            dist *= 1.0 + boost * (wind / cost if cost > 0 else 1.0)
            events.append('tired_sprint')
        wind = max(0.0, wind - cost)
        kick_wind = wind
        winded = True
    else:
        wind = min(float(c['wind_max']), wind + float(c['pace_recover']))
        events.append('pace')
        winded = False
    if is_final_leg(race):
        kick = float(c['final_kick']) * max(0.0, kick_wind) / max(1.0, float(c['wind_max']))
        if kick > 0:
            dist *= 1.0 + kick
            if kick_wind >= float(c['wind_max']) * 0.5:
                events.append('kick')
    if is_cheat_leg(race, c):
        if lane == 'inside':
            dist *= float(c['caltrops_mult'])
            events.append('caltrops')
        else:
            dist *= float(c['outside_mult'])
            events.append('outside')
    return dist, events, {'wind': wind, 'winded': winded}


def run_leg(race: dict, chain: int, mode: str, lane: str = 'inside',
            cfg: dict | None = None) -> dict:
    """Run the next leg: both birds move on. Returns the leg's result
    (also kept in ``race['history']``):
    {'leg', 'chain', 'mode', 'lane', 'hero_run', 'varro_run', 'events',
     'hero', 'varro'} (the last two the totals after it)."""
    if race.get('done'):
        return race['history'][-1] if race['history'] else {}
    c = config(cfg)
    i = int(race['leg'])
    dist, events, st = hero_leg(race, chain, mode, lane, c)
    v = varro_leg(race, i, c)
    race['hero'] = float(race['hero']) + dist
    race['varro'] = float(race['varro']) + v
    race['wind'] = st['wind']
    race['winded'] = st['winded']
    race['leg'] = i + 1
    out = {'leg': i + 1, 'chain': int(chain or 0), 'mode': mode, 'lane': lane,
           'hero_run': dist, 'varro_run': v, 'events': events,
           'hero': race['hero'], 'varro': race['varro']}
    race['history'].append(out)
    if race['leg'] >= int(race['legs']):
        race['done'] = True
    return out


def gap(race: dict) -> float:
    """How far the young Bococho leads (less than 0: behind)."""
    return float(race['hero']) - float(race['varro'])


def standing(race: dict, cfg: dict | None = None) -> str:
    """'lead_big', 'lead', 'level', 'behind' or 'behind_big'."""
    c = config(cfg)
    g = gap(race)
    level = float(c.get('level_margin', 1.0))
    big = float(c.get('big_margin', 8.0))
    if abs(g) < level:
        return 'level'
    if g > 0:
        return 'lead_big' if g >= big else 'lead'
    return 'behind_big' if -g >= big else 'behind'


def lengths(value: float) -> int:
    """A gap as the commentary says it: whole lengths, at least one."""
    return max(1, int(round(abs(float(value)))))


def outcome(race: dict, cfg: dict | None = None) -> dict:
    """At the finish: {'won', 'photo', 'gap'}. A dead heat goes to her (the
    old judge has a soft spot for the underdog); within ``photo_margin``
    it is a photo finish."""
    c = config(cfg)
    g = gap(race)
    return {'won': g >= 0, 'photo': abs(g) < float(c.get('photo_margin', 1.5)),
            'gap': abs(g)}


def positions(race: dict, loop_len: int, cfg: dict | None = None) -> tuple[int, int]:
    """Where each bird stands on a loop of ``loop_len`` track tiles (0 is
    the start and finish line). The race is one lap of ``lap_lengths``;
    a bird past the finish waits on the line; at the finish the leader is
    on the line and the other behind it by the gap."""
    c = config(cfg)
    lap = max(1.0, float(c['lap_lengths']))
    n = max(1, int(loop_len))
    h, v = float(race['hero']), float(race['varro'])
    if race.get('done'):
        top = max(h, v, 1.0)
        scale = lap / top
        h, v = h * scale, v * scale

    # Before the finish nobody is on the line yet: the leader waits a few
    # tiles short of it (``short_of_line``) however far ahead he is.
    room = 1.0 if race.get('done') else 1.0 - float(c.get('short_of_line', 3)) / n

    def at(d):
        share = max(0.0, min(room, d / lap))
        return int(round(share * n)) % n
    return at(h), at(v)
