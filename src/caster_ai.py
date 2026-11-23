"""The Caster's Book: a caster chooses its spell by what the fight needs
(monster behaviour, third wave: AI-3, casters_book, 2026-11-20).

Every caster used to pick one of its distance attacks at random each turn:
no ward when it was hurt, no hold on a hero who was winning, the same bolt
at a hero who had just drunk a potion against it. Now:

* A kind with a book (data/monsters.json ``spells``: 2-4 entries) casts
  from it by need. Each spell has a ``kind`` and the conditions it waits
  for (``when``); the ready spell whose conditions hold and whose weight is
  highest is cast, ties going to the first written. No dice: the same fight
  gives the same choices.

    ward      a ward rises about it: the hero's blows land at ``share`` of
              their strength for ``turns`` turns (Monster.damage_ward, the
              ward Abaddon's armour uses). Magic and missiles pass it.
    control   a curse, a hex or an evil eye on the hero: ``effect`` for
              ``duration`` turns, through the rider's whole road (wax in the
              ears, cold iron, the wards, the guards, the save, the caps
              and the grace: Monster._apply_attack_effect).
    heal      it mends a badly hurt friend of its own side (src/faction.py:
              the healer's own choice and rest).
    escape    beside the hero and hurt, it blinks four paces off
              (Monster._blink_to_standoff).
    dispel    it tears one of the hero's spells off him (a short list:
              haste, a shield, displacement, the fire and cold shields,
              reflection, magic resistance, invisibility). Never a
              permanent one, never a ward of the gods.
    darkness  it puts out the light in his hand and ends the Light spell
              (light_shy.snuff, the shadow's touch).
    hurt      which of its own attacks it uses from afar (pick_attack).

* A big spell (``wind_up``) is drawn up for a turn first, with a line the
  hero can read ("The Orc Shaman begins a chant, hands raised."); a blow
  that lands on the caster in that turn breaks it (spoil(), from
  Monster.take_damage; a wound bleeding is not a blow), and so does what
  stops it (chant_stopped: sleep, a hold, fright, charm, its nerve gone).
  The spell is spent either way: its cooldown runs.
* Every kind with a distance attack and the ``caster`` tag, book or not,
  now chooses its bolt with sense (pick_attack): not a fire bolt at a hero
  who wards off fire, not a blinding hex at a hero already blind.
* A silenced caster casts nothing (attack_gates.blocks_attack is asked for
  every spell, as for every attack); a confused one forgets its book; a
  blinded one can still ward and mend itself but aims nothing; out of sight
  it casts nothing at the hero.
* What it casts at the hero (a curse, a dispel, darkness) meets his wards
  as a ranged attack does (wards.blow_gate, asked by warded()): no ordinary
  foe casts at a hero in Sanctuary, and none farther than the Mist of
  Manannan reaches casts at a veiled one. A chant drawn up before the ward
  rose is let go when it would fire.

Named foes keep their own fights (their bosses' code is untouched); the
allied, the encounter people, the unicorn, Death and the stalker never cast
from a book. Pure module: Monster.take_turn and Monster.attack call it
through src/ai_turn.py, and the simulator runs the same choice
(tools/balance/sim_ai3.py).

For the Tactical Mind (AI-2, src/tactical_mind.py choose_cast), the two
public entry points:

    choose(m, ctx) -> dict | None
        ctx = Context(player, dungeon, monsters); the spell it casts now:
        {'id', 'kind', 'spell': its spec, 'attack': an attack dict for a
        'hurt' spell, else None}, or None (nothing in its book fits).
    pick_attack(m, player, candidates) -> dict | None
        the best of ``candidates`` (its own attack dicts) for the fight now.
    act(m, choice, player, dungeon, monsters, extra_occupied) -> bool
        does it (a wind-up spell begins its chant): True when the choice is
        a blow that Monster.attack should now resolve (``_chosen_blow``).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import ai_lines
import kind_data

ENABLED = True          # the simulator's ai3_caster knob (0 = the old random pick)

KINDS = ('ward', 'control', 'heal', 'escape', 'dispel', 'darkness', 'hurt')
# What a dispel may take off the hero: timed spells only, never a status
# his gear holds (-1), never a ward of the gods or a quest's gift.
DISPEL_ORDER = ('hasted', 'shielded', 'displacement', 'fire_shield', 'cold_shield',
                'reflecting', 'magic_resist', 'invisible', 'regenerating')
# The hero's statuses that turn a damage type aside (pick_attack avoids them).
# What the hero's statuses turn aside: a caster counts one only when it can
# SEE it on him (a glowing shield: _VISIBLE) or it, or one of its band, saw
# him shrug that kind of blow off on this floor (remember_resist). Never a
# draught it did not see him drink, never a hidden timer (the lead's ruling,
# 2026-11-20: never omniscient).
_VISIBLE = ('fire_shield', 'cold_shield')
_RESISTED_BY = {'fire': ('fire_resist', 'fire_shield'), 'cold': ('cold_resist', 'cold_shield'),
                'lightning': ('shock_resist',), 'poison': ('poison_resist',),
                'magic': ('magic_resist',), 'psionic': ('magic_resist',)}
_HARD = ('paralyzed', 'sleeping', 'immobilized', 'stunned', 'frozen', 'petrifying',
         'feared', 'held')


def rules() -> dict:
    return kind_data.rules('casters')


@dataclass
class Context:
    """What a caster weighs: the hero, the floor (None in the simulator's
    melee: every foe is beside him and in sight), and the creatures about."""
    player: object
    dungeon: object = None
    monsters: list = field(default_factory=list)


def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


def book(m) -> list:
    """Its spells (data ``spells``), each a dict with an id and a kind."""
    raw = kind_data.field(m, 'spells', None)
    if not isinstance(raw, list):
        return []
    return [s for s in raw if isinstance(s, dict) and s.get('id') and s.get('kind') in KINDS]


def ruled(m) -> bool:
    """The Caster's Book is this creature's to use."""
    return bool(ENABLED and not kind_data.named(m) and not kind_data.outside_rules(m))


def is_caster(m) -> bool:
    return 'caster' in set(getattr(m, 'tags', None) or ()) or bool(book(m))


# ---------------------------------------------------------------------------
# The gates every spell passes
# ---------------------------------------------------------------------------

def spell_attack(m, s: dict) -> dict:
    """The spell as an attack, for the gates and the rider's road: a
    spoken spell (delivery 'voice' unless the book says 'gaze' or
    'ranged'), of magic."""
    if s.get('kind') == 'hurt':
        atk = own_attack(m, s.get('attack'))
        if atk is not None:
            return atk
    return {'name': str(s.get('name') or s.get('id')), 'damage': '0',
            'type': str(s.get('type', 'magic') or 'magic'),
            'delivery': str(s.get('delivery', 'voice') or 'voice'),
            'ranged': s.get('delivery', 'voice') == 'ranged',
            'effect': s.get('effect'), 'effect_chance': 1.0,
            'effect_duration': int(s.get('duration', 3) or 3),
            'cast': True}


def own_attack(m, name) -> dict | None:
    for a in getattr(m, 'attacks', None) or ():
        if isinstance(a, dict) and a.get('name') == name:
            return a
    return None


def gated(m, atk) -> bool:
    """Silenced, unstrung (src/attack_gates.py): it may not use this now."""
    try:
        import attack_gates
        return bool(attack_gates.blocks_attack(m, atk))
    except ImportError:
        return False


def cooldown(m, sid: str) -> int:
    return int((m.__dict__.get('_spell_cd') or {}).get(sid, 0) or 0)


def _spend(m, s: dict) -> None:
    cd = dict(m.__dict__.get('_spell_cd') or {})       # a new dict: copies share none
    cd[s['id']] = int(s.get('cooldown', rules().get('cooldown', 6)) or 0)
    m._spell_cd = cd


def can_target(m, player, dungeon, reach: int) -> bool:
    """It sees the hero, in reach, with nothing between (never through a
    wall by scent or hearing)."""
    if _cheb(m.x, m.y, player.x, player.y) > reach:
        return False
    import holds
    if holds.shields(player, m):
        return False                    # he is inside another: out of every reach
    if dungeon is None:
        return True
    import senses
    if senses.perceive(m, player, dungeon) is None:
        return False
    if _cheb(m.x, m.y, player.x, player.y) <= 1:
        return True
    return senses.clear_view(m.x, m.y, player.x, player.y, dungeon)


def _mind_free(m) -> bool:
    """A confused, charmed or feared caster forgets its book (Monster.take_turn
    sends the feared and charmed off first; confusion lets it act)."""
    return not (m._under('confused') or m._under('charmed') or m._under('feared'))


# ---------------------------------------------------------------------------
# What the fight needs
# ---------------------------------------------------------------------------

def _share(x) -> float:
    return x.hp / max(1, x.max_hp)


def _allies(m, monsters) -> list:
    import faction
    return [o for o in monsters or () if faction.same_side(m, o)]


def hero_buff(player):
    """The first spell on the hero a dispel would take (DISPEL_ORDER), or None."""
    se = getattr(player, 'status_effects', None) or {}
    for k in DISPEL_ORDER:
        v = se.get(k, 0)
        if isinstance(v, int) and v > 0:
            return k
    return None


def _lit(player) -> bool:
    """A light the darkness can put out: a lit light in his hand that is not
    everlasting, or the Light spell (never the Hero's Lamp, a weapon's own
    glow or a light with a power: light_shy.snuffable)."""
    try:
        import light_shy
        import lights
    except ImportError:
        return False
    lt = lights.held(player)
    if lt is not None and light_shy.snuffable(lt):
        return True
    se = getattr(player, 'status_effects', None) or {}
    return int(se.get('light', 0) or 0) > 0


def conditions_hold(m, s: dict, ctx: Context) -> bool:
    """Every condition the spell waits for (``when``) holds now."""
    p = ctx.player
    w = s.get('when') or {}
    if 'self_hp_below' in w and not _share(m) < float(w['self_hp_below']):
        return False
    if 'self_hp_above' in w and not _share(m) > float(w['self_hp_above']):
        return False
    if 'hero_hp_above' in w and not _share(p) > float(w['hero_hp_above']):
        return False
    if 'hero_hp_below' in w and not _share(p) < float(w['hero_hp_below']):
        return False
    adj = _cheb(m.x, m.y, p.x, p.y) <= 1
    if w.get('adjacent') and not adj:
        return False
    if w.get('at_range') and adj:
        return False
    if 'ally_hp_below' in w:
        if not any(_share(o) < float(w['ally_hp_below']) for o in _allies(m, ctx.monsters)):
            return False
    if 'allies_near' in w:
        near = sum(1 for o in _allies(m, ctx.monsters) if _cheb(o.x, o.y, p.x, p.y) <= 2)
        if near < int(w['allies_near']):
            return False
    if w.get('hero_buffed') and hero_buff(p) is None:
        return False
    if w.get('hero_lit') and not _lit(p):
        return False
    return True


def _reach(s: dict) -> int:
    return int(s.get('reach', rules().get('reach', 6)) or 6)


def usable(m, s: dict, ctx: Context) -> bool:
    """Ready, allowed by its gates and its mind, and able to do something
    now (its own kind's test)."""
    if cooldown(m, s['id']) > 0:
        return False
    if gated(m, spell_attack(m, s)):
        return False
    if not conditions_hold(m, s, ctx):
        return False
    p = ctx.player
    kind = s['kind']
    blind = m._under('blinded')
    if kind == 'ward':
        return not m.has_effect('spell_ward')
    if kind == 'heal':
        import faction
        return faction.heal_choice(m, ctx.monsters, p, reach=int(s.get('reach', 4) or 4)
                                   if ctx.dungeon is not None else None) is not None
    if kind == 'escape':
        return bool(s.get('blink', True)) and _cheb(m.x, m.y, p.x, p.y) <= 1
    if blind:
        return False                    # it cannot aim at what it cannot see
    if not can_target(m, p, ctx.dungeon, _reach(s)):
        return False
    if kind in ('control', 'dispel', 'darkness') and warded(m, p, s):
        return False                    # his wards keep it off him (wards.blow_gate)
    if kind == 'control':
        eff = str(s.get('effect') or '')
        if not eff:
            return False
        se = getattr(p, 'status_effects', None) or {}
        if int(se.get(eff, 0) or 0) != 0:
            return False                # it is on him already (it can see that)
        return True
    if kind == 'dispel':
        return hero_buff(p) is not None
    if kind == 'darkness':
        return _lit(p)
    if kind == 'hurt':
        return own_attack(m, s.get('attack')) is not None
    return False


def warded(m, player, s: dict) -> bool:
    """The hero's wards keep this spell off him: asked of wards.blow_gate
    exactly as a ranged attack is (Sanctuary, the Mist past its reach, the
    family wards...). A spoken spell cast at him is a spell sent from afar
    (delivery 'ranged'); a gaze is a gaze. Only a question: the line the
    gate would say waits for the blow that meets it."""
    import wards
    atk = dict(spell_attack(m, s))
    if atk.get('delivery') not in ('gaze', 'ranged'):
        atk['delivery'], atk['ranged'] = 'ranged', True
    d = m.__dict__
    had, said = '_sanct_said' in d, d.get('_sanct_said')
    try:
        return wards.blow_gate(player, m, atk) is not None
    finally:
        if had:
            d['_sanct_said'] = said
        else:
            d.pop('_sanct_said', None)


def choose(m, ctx: Context):
    """The spell it casts now, or None (pure: no dice, the same fight gives
    the same choice). See the module docstring for the shape."""
    if not ruled(m) or not _mind_free(m):
        return None
    best = None
    for i, s in enumerate(book(m)):
        if not usable(m, s, ctx):
            continue
        key = (float(s.get('weight', 1) or 0), -i)
        if best is None or key > best[0]:
            best = (key, s)
    if best is None:
        return None
    s = best[1]
    return {'id': s['id'], 'kind': s['kind'], 'spell': s,
            'attack': own_attack(m, s.get('attack')) if s['kind'] == 'hurt' else None}


# ---------------------------------------------------------------------------
# Its bolt, chosen with sense
# ---------------------------------------------------------------------------

def _resisted(player, dtype: str, m=None) -> bool:
    """The caster knows the hero turns this kind of blow aside: a shield it
    can see glowing on him, or it (or its band) saw him shrug one off."""
    dtype = str(dtype or '')
    se = getattr(player, 'status_effects', None) or {}
    if any(int(se.get(s, 0) or 0) != 0 for s in _RESISTED_BY.get(dtype, ()) if s in _VISIBLE):
        return True
    return m is not None and dtype in (m.__dict__.get('_seen_resist') or ())


def remember_resist(m, dtype: str) -> None:
    """It saw its blow of ``dtype`` turned aside: it and its band know it
    (a new set each time: copies share none)."""
    who = [m]
    band = m.__dict__.get('_band')
    if band is not None:
        who += [o for o in (m.__dict__.get('_cached_all_monsters') or ())
                if o is not m and getattr(o, 'alive', False) and o.__dict__.get('_band') == band]
    for o in who:
        o._seen_resist = set(o.__dict__.get('_seen_resist') or ()) | {dtype}


def after_blow(m, player, atk, actual: int, msg: str) -> str:
    """ai_blow.after_blow: a typed blow of a caster's that the hero's
    resistance turned aside is seen to fizzle; it remembers."""
    dtype = str((atk or {}).get('type', '') or '')
    if dtype in _RESISTED_BY and is_caster(m):
        se = getattr(player, 'status_effects', None) or {}
        if any(int(se.get(s, 0) or 0) != 0 for s in _RESISTED_BY[dtype]):
            remember_resist(m, dtype)
    return msg


def rider_wasted(player, eff: str) -> bool:
    """The curse a bolt carries is on him already: the caster can see that.
    (A hidden grace or a draught's ward it cannot know.)"""
    se = getattr(player, 'status_effects', None) or {}
    return int(se.get(eff, 0) or 0) != 0


def _avg(atk) -> float:
    try:
        import re
        mt = re.fullmatch(r'(\d*)d(\d+)([+-]\d+)?', str(atk.get('damage', '1d4')).replace(' ', ''))
        n, s, k = int(mt.group(1) or 1), int(mt.group(2)), int(mt.group(3) or 0)
        return n * (s + 1) / 2 + k
    except (AttributeError, ValueError, TypeError):
        return 1.0


def attack_score(m, player, atk: dict, strongest: float = 0.0) -> float:
    """How well ``atk`` serves now: its book's weight for it; its curse
    when that would take (+0.5); its weight of blow (the strongest +0.5,
    twice that on a hero already badly hurt: finish him); nothing for a
    type he wards off (-3)."""
    sc = 1.0
    for s in book(m):
        if s.get('kind') == 'hurt' and s.get('attack') == atk.get('name'):
            sc = float(s.get('weight', 1) or 1)
    eff = atk.get('effect')
    if eff and not rider_wasted(player, str(eff)):
        sc += 0.5
    if strongest > 0:
        hurt = getattr(player, 'hp', 1) < 0.5 * max(1, getattr(player, 'max_hp', 1))
        sc += (1.0 if hurt else 0.5) * _avg(atk) / strongest
    if _resisted(player, atk.get('type', ''), m):
        sc -= 3.0
    return sc


def pick_attack(m, player, candidates):
    """The best of ``candidates`` for the fight now (ties: the first
    written), or None when it has no choice to make."""
    cands = [a for a in candidates or () if isinstance(a, dict) and not gated(m, a)]
    if not ENABLED or not cands or not is_caster(m) or not ruled(m):
        return None
    if len(cands) == 1:
        return cands[0]
    strongest = max(_avg(a) for a in cands) or 1.0
    best = None
    for i, a in enumerate(cands):
        key = (attack_score(m, player, a, strongest), -i)
        if best is None or key > best[0]:
            best = (key, a)
    return best[1]


# ---------------------------------------------------------------------------
# Casting
# ---------------------------------------------------------------------------

def _line(key: str, m, s: dict, **kw) -> str:
    """The spell's own line (a string under ``key``: 'cast', or 'wind_up'
    only when it is text, not the flag), else lines.<key>_<kind>, else
    lines.<key>."""
    own = s.get(key + '_line') or s.get(key)
    lines = rules().get('lines') or {}
    text = (own if isinstance(own, str) else '') or lines.get(key + '_' + s.get('kind', ''), '') \
        or lines.get(key, '')
    return ai_lines.fill(m, text, spell=str(s.get('name') or s['id']).lower(), **kw)


def _say(m, seen: str, unseen_key: str = '', colour: str = 'warning') -> None:
    unseen = (rules().get('unseen') or {}).get(unseen_key, '') if unseen_key else ''
    ai_lines.say(m, seen, unseen, colour)


def spell_by_id(m, sid):
    return next((s for s in book(m) if s.get('id') == sid), None)


def turn(m, player, dungeon, monsters, extra_occupied):
    """Its turn by the book (src/ai_turn.py, before the pattern's own move):
    True (it attacks: Monster.attack resolves ``_chosen_blow``), False (it
    cast or chanted: its turn is spent), None (nothing to cast: the pattern
    goes on, and Monster.attack chooses its bolt with pick_attack)."""
    if not ruled(m) or not book(m):
        return None
    ctx = Context(player, dungeon, list(monsters or ()))
    sid = m.__dict__.get('_casting')
    if sid:
        m._casting = None
        s = spell_by_id(m, sid)
        if s is None or not _mind_free(m) or gated(m, spell_attack(m, s)):
            return None
        if s['kind'] in ('ward', 'heal', 'escape') or usable_now(m, s, ctx):
            return _fire(m, s, ctx, extra_occupied)
        return None                       # he is gone from its sight: let go
    if not m.__dict__.get('_tracking'):
        return None                       # not in a fight
    ch = choose(m, ctx)
    if ch is None or ch['kind'] == 'hurt':
        return None
    return act(m, ch, player, dungeon, monsters, extra_occupied)


def usable_now(m, s: dict, ctx: Context) -> bool:
    """A drawn-up spell still has its mark (its cooldown is already set)."""
    cd = dict(m.__dict__.get('_spell_cd') or {})
    held = cd.pop(s['id'], None)
    m._spell_cd = cd
    try:
        return usable(m, s, ctx)
    finally:
        if held is not None:
            cd = dict(m.__dict__.get('_spell_cd') or {})
            cd[s['id']] = held
            m._spell_cd = cd


def act(m, choice, player, dungeon, monsters, extra_occupied=None):
    """Cast ``choice`` (from choose). A wind-up spell begins its chant: its
    turn is spent and it fires next turn unless a blow breaks it. None: it
    could not be cast after all (a blink with nowhere to go): its turn goes
    on."""
    s = choice['spell']
    ctx = Context(player, dungeon, list(monsters or ()))
    if s.get('wind_up') and not m.__dict__.get('_casting'):
        _spend(m, s)
        m._casting = s['id']
        _say(m, _line('wind_up', m, s), 'wind_up')
        return False
    return _fire(m, s, ctx, extra_occupied)


def _fire(m, s: dict, ctx: Context, extra_occupied=None) -> bool:
    p = ctx.player
    _spend(m, s)
    kind = s['kind']
    counts = dict(m.__dict__.get('_spells_cast') or {})
    counts[kind] = counts.get(kind, 0) + 1
    m._spells_cast = counts
    if kind == 'hurt':
        atk = own_attack(m, s.get('attack'))
        if atk is None:
            return False
        m._chosen_blow = atk
        return True
    if kind == 'ward':
        share = max(0.0, min(0.75, float(s.get('share', 0.5) or 0.5)))
        m.status_effects['spell_ward'] = int(s.get('turns', 4) or 4)
        if not m.__dict__.get('_ward_base_kept'):
            m._ward_base = float(getattr(m, 'damage_ward', 0.0) or 0.0)
            m._ward_base_kept = True
        m.damage_ward = max(float(m.__dict__.get('_ward_base', 0.0) or 0.0), share)
        _say(m, _line('cast', m, s), 'cast', 'warning')
        return False
    if kind == 'heal':
        import faction
        reach = int(s.get('reach', 4) or 4) if ctx.dungeon is not None else None
        target = faction.heal_choice(m, ctx.monsters, p, reach=reach)
        if target is not None:
            faction.heal(m, target)       # the game says who was mended (_heal_target)
        return False
    if kind == 'escape':
        if ctx.dungeon is None:
            return False                  # the simulator's melee: it blinks off (sim_ai3 counts it)
        if m._blink_to_standoff(p, ctx.dungeon, ctx.monsters, extra_occupied):
            _say(m, _line('cast', m, s), 'escape', 'warning')
            return False
        # No tile four paces off with a shot at him (a corridor, a crowd):
        # nothing was cast. It spent its turn and its blink's rest for
        # nothing, and said nothing; now the fight goes on (None).
        cd = dict(m.__dict__.get('_spell_cd') or {})
        cd.pop(s['id'], None)
        m._spell_cd = cd
        counts[kind] -= 1
        m._spells_cast = counts
        return None
    if kind == 'dispel':
        buff = hero_buff(p)
        if buff:
            p.status_effects.pop(buff, None)
            try:
                import status_effects
                status_effects.sync_timed_grants(p)
            except (ImportError, AttributeError):
                pass
            words = (rules().get('buff_words') or {}).get(buff, buff.replace('_', ' '))
            unseen = str((rules().get('unseen') or {}).get('dispel', '')).replace('{buff}', words)
            ai_lines.say(m, _line('cast', m, s, buff=words), unseen, 'danger')
        return False
    if kind == 'darkness':
        import light_shy
        got = light_shy.snuff(p, 'dark')
        _say(m, (_line('cast', m, s) + (' ' + got if got else '')).strip(), 'darkness', 'danger')
        return False
    if kind == 'control':
        atk = spell_attack(m, s)
        text = _control(m, p, atk)
        unseen = (str((rules().get('unseen') or {}).get('curse', '')) + ' ' + text).strip()
        ai_lines.say(m, (_line('cast', m, s) + ' ' + text).strip(), unseen, 'danger')
        return False
    return False


def _control(m, player, atk) -> str:
    """The curse's road: a gaze is turned by a mirror and fails on a blind
    man; the rest is the rider's own (Monster._apply_attack_effect: wax,
    cold iron, wards, guards, the save, the caps and the grace)."""
    if atk.get('delivery') == 'gaze':
        try:
            if player.get_sight_radius() == 0:
                return (rules().get('lines') or {}).get('gaze_blind', '')
        except AttributeError:
            pass
        try:
            import counters
            mirror = counters.blocks_gaze(player, m)
            if mirror is not None:
                return counters.line(player, mirror, counters.GAZE, m)
        except ImportError:
            pass
    eff = str(atk.get('effect') or '')
    se = getattr(player, 'status_effects', None) or {}
    if eff and int(se.get('spell_turning', 0) or 0) != 0:
        from status_effects import reflected
        m.add_effect(*reflected(eff, 8))  # Spell Turning: every cast curse goes back
        return ai_lines.fill(m, (rules().get('lines') or {}).get('turned', ''))
    text = m._apply_attack_effect(atk, player, gaze=atk.get('delivery') == 'gaze')
    return text.strip() or ai_lines.fill(m, (rules().get('lines') or {}).get('resisted', ''))


def take_spell(m):
    """The blow its book chose this turn (Monster.attack), or None."""
    return m.__dict__.pop('_chosen_blow', None)


def spoil(m, why: str = 'blow') -> bool:
    """A blow landed while it chants (Monster.take_damage, never a wound's
    tick), or it was put to sleep, held, stunned, frightened or charmed, or
    it broke (chant_stopped): the spell breaks. It is spent (its cooldown
    runs). True if so."""
    sid = m.__dict__.get('_casting')
    if not sid:
        return False
    m._casting = None
    s = spell_by_id(m, sid) or {'id': sid, 'kind': ''}
    counts = dict(m.__dict__.get('_spells_spoiled') or {})
    counts[s.get('kind', '')] = counts.get(s.get('kind', ''), 0) + 1
    m._spells_spoiled = counts
    key = 'spoil' if why == 'blow' else 'spoil_held'
    lines = rules().get('lines') or {}
    ai_lines.say(m, ai_lines.fill(m, lines.get(key) or lines.get('spoil', '')), '', 'success')
    return True


# A creature in one of these cannot keep a chant going (the conditions that
# stop its turn: Monster.take_turn's held gate and its mind gate, a nerve
# that has gone, a hero held fast). Pinned (immobilized) it can still speak
# (Monster._pinned_turn).
_STOPS_CHANT = ('sleeping', 'paralyzed', 'stunned', 'frozen', 'petrifying')


def broken(m) -> bool:
    """Its nerve has gone (src/morale.py): it runs, is cowed or has yielded."""
    d = getattr(m, '__dict__', {})
    return bool(int(getattr(m, '_flee_timer', 0) or 0) > 0 or d.get('_cowed') or d.get('_yielded'))


def chant_stopped(m) -> bool:
    """It cannot keep up what it had drawn up: a spell, a summoner's chant
    (src/summoning.py), an opener's wind-up."""
    return bool(any(m.has_effect(e) for e in _STOPS_CHANT)
                or m._under('feared') or m._under('charmed')
                or broken(m) or getattr(m, '__dict__', {}).get('_holding'))


def tick(m) -> None:
    """One turn of its book (Monster.tick_effects): its spells come ready
    again; a ward that has faded lets the blows through."""
    cd = m.__dict__.get('_spell_cd')
    if cd:
        m._spell_cd = {k: v - 1 for k, v in cd.items() if v - 1 > 0}
    if m.__dict__.get('_casting') and chant_stopped(m):
        spoil(m, 'held')                  # asleep, held, frightened...: the chant is lost
    if m.__dict__.get('_ward_base_kept') and not m.has_effect('spell_ward'):
        m.damage_ward = float(m.__dict__.pop('_ward_base', 0.0) or 0.0)
        m.__dict__.pop('_ward_base_kept', None)
        if m.alive:
            ai_lines.say(m, ai_lines.fill(m, (rules().get('lines') or {}).get('ward_fades', '')),
                         '', 'info')


def tell_keys(m) -> list:
    """The tells its book shows (src/tells.py)."""
    keys = []
    kinds = {s['kind'] for s in book(m)}
    if 'ward' in kinds:
        keys.append('casts_ward')
    if any(s['kind'] == 'control' and s.get('wind_up') for s in book(m)):
        keys.append('casts_curse')
    if 'dispel' in kinds:
        keys.append('casts_dispel')
    if 'darkness' in kinds:
        keys.append('casts_darkness')
    if 'escape' in kinds:
        keys.append('casts_escape')
    return keys
