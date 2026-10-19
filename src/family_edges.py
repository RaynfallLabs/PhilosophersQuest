"""The abilities monster-family knowledge grants, as a registry of effect
PRIMITIVES (docs/systems/monster_families_v2_design.md section 6).

Pure module: no pygame, no Game. Every technique in
data/monster_families.json is one primitive plus its `params` (and any
`also` parts); game code asks the questions below and this module sums the
abilities the hero has earned (src/family_lore.py says which tiers he has).
Adding or tuning a technique is a data edit.

The rails, everywhere in this file:
  * A family's ability works only on that family, and only on a creature
    the hero can recognise (`_recognised`: not an invisible creature he
    cannot see, an ambusher that has not sprung or a disguised mimic).
    Hidden things stay hidden, except through the one primitive that is
    exactly that (`sense_hidden`), and then only for its own family, inside
    its radius.
  * Named foes (bosses, mini-bosses, seal demons: Monster._is_named_foe)
    are too wilful: execute, turn, calm, charm-on-hit, surrender and
    stun-on-hit never touch them, and an execute lands a blow `named_mult`
    harder instead. Wards, damage, block_regen, pierce_resist and
    sense_hidden do apply to them (ruling 3). The Black Knight is held the
    same way against execute, turn, calm, charm and surrender (`_steadfast`:
    nothing moves him off his bridge, and he never yields).
  * A technique's trigger line is said once per fight (per creature), into
    an outbox the Game drains (`drain`).
  * Nothing scales by floor.

Circle boons (family_lore circles) use the same primitives with
`scope: "any"`: they apply whoever the source is.
"""
from __future__ import annotations

import random

import family_lore

# ---------------------------------------------------------------------------
# The registry: primitive -> its params ({name: type}; a trailing '?' marks
# an optional one). tests/test_monster_families_data.py validates every
# ability in the data against this.
# ---------------------------------------------------------------------------
PRIMITIVES = {
    'recognise':       {},
    'forewarned':      {'line': str},
    'save_bonus':      {'effects': list, 'amount': int, 'scope?': str},
    'duration_mult':   {'effects': list, 'mult': float},
    'resist_damage':   {'types': list, 'mult': float, 'scope?': str},
    'damage_mult':     {'mult': float, 'chain_min?': int, 'weapons?': list, 'weapon_mult?': float,
                        'only_weapons?': list, 'big_mult?': float},
    'weakness_amp':    {'mult': float},
    'extra_seconds':   {'seconds': int, 'scope?': str, 'boss_only?': bool},
    'chain_forgive':   {'uses': int},
    'opening_chain':   {'chain': int},
    'pierce_resist':   {'chain_min': int, 'scales?': bool, 'blessed?': bool},
    'block_regen':     {'turns': int},
    'prevent_split':   {},
    'execute':         {'chain_min': int, 'hp_below': float, 'variant': str, 'named_mult': float},
    'turn':            {'trigger': str, 'turns': int, 'chain_min?': int, 'chance?': float},
    'calm_on_arrival': {'chance': float},
    'charm_on_hit':    {'chain_min': int, 'turns': int},
    'surrender':       {'chain_min': int, 'hp_below': float, 'turns': int},
    'theft_immune':    {},
    'no_ambush':       {},
    'sense_hidden':    {'kinds': list, 'radius': int},
    'gaze_immune':     {'requires': str},
    'harvest_bonus':   {'portions': int},
    'drain_heal_block': {},
    'stun_on_hit':     {'chain_min': int, 'turns': int},
    'sight_bonus':     {'amount': int},
}

# Allowed values for the enumerated params.
CHOICES = {
    ('turn', 'trigger'): {'on_hit', 'on_kill', 'on_sight'},
    ('execute', 'variant'): {'ash', 'banish', 'petrify', 'erase'},
    ('gaze_immune', 'requires'): {'shield', ''},
}
SENSE_KINDS = {'invisible', 'ambush', 'disguise'}
WEAPON_KINDS = {'iron', 'silver', 'ranged', 'thrown'}
# Ward ids that are not status effects: a life-draining blow (its CON save,
# Monster._drain_takes_hold) and a killing gaze (the gorgon gaze block).
SPECIAL_EFFECTS = {'drain', 'gaze'}

# What an execute does, said by variant when no trigger line is written.
VARIANT_WORDS = {'ash': 'crumbles to ash', 'banish': 'is cast back into the Pit',
                 'petrify': 'turns to stone', 'erase': 'falls lifeless'}


def validate(ability: dict) -> list:
    """Every problem with one ability dict (empty when it is sound)."""
    errs = []
    parts = [(ability.get('effect'), ability.get('params'))]
    parts += [(p.get('effect'), p.get('params')) for p in ability.get('also', ()) or ()]
    for eff, params in parts:
        spec = PRIMITIVES.get(eff)
        if spec is None:
            errs.append(f'unknown primitive {eff!r}')
            continue
        params = params if isinstance(params, dict) else None
        if params is None:
            errs.append(f'{eff}: params must be an object')
            continue
        known = {k.rstrip('?') for k in spec}
        for k in params:
            if k not in known:
                errs.append(f'{eff}: unknown param {k!r}')
        for k, typ in spec.items():
            name = k.rstrip('?')
            if name not in params:
                if not k.endswith('?'):
                    errs.append(f'{eff}: missing param {name!r}')
                continue
            v = params[name]
            ok = (isinstance(v, (int, float)) and not isinstance(v, bool)) if typ is float else (
                isinstance(v, int) and not isinstance(v, bool) if typ is int else isinstance(v, typ))
            if not ok:
                errs.append(f'{eff}: param {name!r} should be {typ.__name__}')
            choices = CHOICES.get((eff, name))
            if choices is not None and v not in choices:
                errs.append(f'{eff}: {name}={v!r} is not one of {sorted(choices)}')
        if eff == 'sense_hidden' and not set(params.get('kinds', ())) <= SENSE_KINDS:
            errs.append('sense_hidden: unknown kind')
        for key in ('weapons', 'only_weapons'):
            if eff == 'damage_mult' and not set(params.get(key, ()) or ()) <= WEAPON_KINDS:
                errs.append(f'damage_mult: unknown weapon kind in {key}')
        if params.get('scope') not in (None, 'any'):
            errs.append(f'{eff}: scope must be "any"')
    return errs


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------
_PART_CACHE: dict = {}


def _parts_upto(fid, t: int) -> list:
    """(ability, effect, params) for every part of every ability in tiers
    1..t of family `fid`. Pure data, cached."""
    key = (fid, t, id(family_lore.data()))
    got = _PART_CACHE.get(key)
    if got is None:
        got = []
        for a in family_lore.abilities(fid, t):
            got.append((a, a.get('effect'), a.get('params') or {}))
            for p in a.get('also', ()) or ():
                got.append((a, p.get('effect'), p.get('params') or {}))
        _PART_CACHE[key] = got
    return got


def parts(player, fid, effect) -> list:
    """The hero's (ability, params) of one primitive in one family."""
    if not fid or player is None:
        return []
    t = family_lore.tier(player, fid)
    if t <= 0:
        return []
    return [(a, p) for a, e, p in _parts_upto(fid, t) if e == effect]


def circle_parts(player, effect) -> list:
    """(boon, params) of one primitive across the circles the hero has
    completed (scope "any")."""
    out = []
    if player is None:
        return out
    for cid in family_lore.complete_circles(player):
        boon = (family_lore.circles().get(cid) or {}).get('boon') or {}
        if boon.get('effect') == effect:
            out.append((boon, boon.get('params') or {}))
    return out


def _named(m) -> bool:
    fn = getattr(m, '_is_named_foe', None)
    try:
        return bool(fn()) if callable(fn) else False
    except Exception:
        return False


def _steadfast(m) -> bool:
    """A creature no execute, turning, charm, calm or surrender may move: a
    named foe, or the Black Knight, whom the engine already holds on his
    bridge against every charm, fear and instant kill (game_magic._is_big_foe;
    he never yields: "'Tis but a scratch"). Yield! used to make him "throw
    down his purse and run" while he stood there."""
    # Proper-named story characters (Morrow, Azarael, Neferkaptah) and the
    # figures of NPC and flavor encounters are held the same way: a stake
    # or a "Yield!" must not cut across a story with its own spared deed.
    return (_named(m) or bool(getattr(m, 'is_black_knight', False))
            or bool(getattr(m, 'proper_noun', False))
            or bool(getattr(m, '_npc_encounter_tag', None))
            or bool(getattr(m, '_flavor_encounter_tag', None)))


def _recognised(player, m) -> bool:
    """The hero can see what this creature is (never a concealed one)."""
    if m is None:
        return False
    try:
        import unseen
        return not unseen.concealed(m, player)
    except Exception:
        return True


def _fam(m):
    return family_lore.family_of(m)


def _mine(player, m, effect, *, recognise=True) -> list:
    """The hero's (ability, params) of `effect` in this creature's family."""
    if m is None or (recognise and not _recognised(player, m)):
        return []
    return parts(player, _fam(m), effect)


# ---------------------------------------------------------------------------
# Trigger lines: once per fight per technique
# ---------------------------------------------------------------------------
def tell(player, m, ability) -> None:
    """Queue the ability's trigger line, once per creature it is used on."""
    msg = (ability or {}).get('trigger_msg') or ''
    if not msg or player is None:
        return
    if m is not None and hasattr(m, '__dict__'):
        told = m.__dict__.setdefault('_edges_told', set())
        if ability.get('id') in told:
            return
        told.add(ability.get('id'))
    player.__dict__.setdefault('_edge_msgs', []).append(msg)


def say(player, msg: str) -> None:
    """Queue a line that is not a once-per-fight trigger."""
    if msg and player is not None:
        player.__dict__.setdefault('_edge_msgs', []).append(msg)


def drain(player) -> list:
    """The queued lines, in order, and empty the queue (the Game prints them)."""
    if player is None:
        return []
    return player.__dict__.pop('_edge_msgs', None) or []


# ---------------------------------------------------------------------------
# Defence: saves, durations, damage taken
# ---------------------------------------------------------------------------
def save_bonus(player, attacker, effect) -> int:
    """Extra on a saving throw when `attacker` inflicts `effect` (a status id,
    or 'drain' / 'gaze'). Sits outside Player.save_bonus_for's +5 cap: it
    is earned against one family only."""
    total = 0
    for a, p in _mine(player, attacker, 'save_bonus'):
        if effect in (p.get('effects') or ()):
            total += int(p.get('amount', 0) or 0)
            tell(player, attacker, a)
    for _b, p in circle_parts(player, 'save_bonus'):
        if effect in (p.get('effects') or ()):
            total += int(p.get('amount', 0) or 0)
    return total


def no_save_ward_share(amount: int) -> float:
    """What a ward of +`amount` does to an effect with NO saving throw: the
    share of its duration left (data no_save_ward: `per_point` off a point,
    never below `floor`)."""
    rule = family_lore.data().get('no_save_ward') or {}
    per = float(rule.get('per_point', 0.1))
    floor = float(rule.get('floor', 0.5))
    return max(floor, 1.0 - per * max(0, int(amount)))


def duration_mult(player, attacker, effect) -> float:
    """How long `effect` from `attacker` lasts, as a share (0 = it never
    takes hold)."""
    mult = 1.0
    for a, p in _mine(player, attacker, 'duration_mult'):
        if effect in (p.get('effects') or ()):
            mult *= float(p.get('mult', 1.0))
            tell(player, attacker, a)
    return mult


def incoming_damage_mult(player, attacker, dtype) -> float:
    """A blow of `dtype` from `attacker`: the strongest family resist that
    covers it (an upgrade replaces, it does not stack)."""
    best = 1.0
    for a, p in _mine(player, attacker, 'resist_damage'):
        if dtype in (p.get('types') or ()) and float(p.get('mult', 1.0)) < best:
            best = float(p.get('mult', 1.0))
            tell(player, attacker, a)
    return best


def any_damage_mult(player, dtype) -> float:
    """Circle resists that hold against `dtype` from any source."""
    best = 1.0
    for _b, p in circle_parts(player, 'resist_damage'):
        if dtype in (p.get('types') or ()):
            best = min(best, float(p.get('mult', 1.0)))
    return best


def drain_heal_blocked(player, attacker) -> bool:
    got = _mine(player, attacker, 'drain_heal_block')
    if got:
        tell(player, attacker, got[0][0])
    return bool(got)


def gaze_immune(player, attacker) -> bool:
    """The gaze of this family cannot take the hero (Perseus' Shield needs a
    shield carried)."""
    for a, p in _mine(player, attacker, 'gaze_immune', recognise=False):
        if p.get('requires') == 'shield' and getattr(player, 'shield', None) is None:
            continue
        tell(player, attacker, a)
        return True
    return False


def theft_immune(player, thief) -> bool:
    got = _mine(player, thief, 'theft_immune')
    if got:
        tell(player, thief, got[0][0])
    return bool(got)


def no_ambush(player, m) -> bool:
    """Its family's ambushers never catch the hero unawares (by definition
    an ambusher is hidden, so this does not ask whether it is seen)."""
    got = _mine(player, m, 'no_ambush', recognise=False)
    return bool(got)


def sight_bonus(player) -> int:
    return sum(int(p.get('amount', 0) or 0) for _b, p in circle_parts(player, 'sight_bonus'))


# ---------------------------------------------------------------------------
# Seeing the hidden
# ---------------------------------------------------------------------------
def _hidden_kind(m, player) -> str:
    if getattr(m, 'ai_pattern', '') == 'mimic' and not getattr(m, '_aware', False):
        return 'disguise'
    if getattr(m, 'ai_pattern', '') == 'ambush' and not getattr(m, '_aware', False):
        # A plain mimic waiting as a chest is a disguise, not a lurker, so
        # Mimic-Sense finds it too (cloakers and lurkers stay ambushers).
        if 'mimic' in str(getattr(m, 'kind', '') or ''):
            return 'disguise'
        return 'ambush'
    if getattr(m, 'invisible', False):
        return 'invisible'
    return ''


def _distance(player, m) -> int:
    fw, fh = getattr(m, 'footprint', (1, 1)) or (1, 1)
    dx = max(0, m.x - player.x, player.x - (m.x + int(fw) - 1))
    dy = max(0, m.y - player.y, player.y - (m.y + int(fh) - 1))
    return max(dx, dy)


def senses(player, m) -> bool:
    """The hero's own family technique shows him this hidden creature: it
    is of that family, hidden in a way the technique covers, and inside its
    radius. Called by src/unseen.py (never calls it back)."""
    if player is None or m is None or not hasattr(player, 'x'):
        return False
    kind = _hidden_kind(m, player)
    if not kind:
        return False
    for a, p in parts(player, _fam(m), 'sense_hidden'):
        if kind in (p.get('kinds') or ()) and _distance(player, m) <= int(p.get('radius', 0) or 0):
            return True
    return False


def sense_ability(player, m):
    """The sense_hidden ability that shows `m`, for its trigger line."""
    kind = _hidden_kind(m, player)
    for a, p in parts(player, _fam(m), 'sense_hidden'):
        if kind in (p.get('kinds') or ()) and _distance(player, m) <= int(p.get('radius', 0) or 0):
            return a
    return None


# ---------------------------------------------------------------------------
# Offence: the hero's weapon blow
# ---------------------------------------------------------------------------
def _weapon_kinds(weapon, ranged: bool, thrown: bool) -> set:
    out = set()
    if ranged:
        out.add('ranged')
    if thrown:
        out.add('thrown')
    if weapon is not None:
        mat = str(getattr(weapon, 'material', '') or '').lower()
        types = {str(t).lower() for t in (getattr(weapon, 'damage_types', None) or ())}
        if 'silver' in mat or 'silver' in types:
            out.add('silver')
        if 'iron' in mat or types & {'iron', 'cold_iron'}:
            out.add('iron')
    return out


def damage_mult(player, target, chain: int, weapon=None, *, ranged: bool = False,
                thrown: bool = False, consume: bool = False) -> float:
    """The hero's weapon blow on `target` at `chain`: the product of his
    damage techniques against its family. Weapon blows only (never spells or
    pets), and only on a creature he can see."""
    mult = 1.0
    if target is None or not _recognised(player, target):
        return mult
    have = _weapon_kinds(weapon, ranged, thrown)
    for a, p in parts(player, _fam(target), 'damage_mult'):
        if chain < int(p.get('chain_min', 0) or 0):
            continue
        only = set(p.get('only_weapons') or ())
        if only and not (only & have):
            continue
        m = float(p.get('mult', 1.0))
        if p.get('weapons') and set(p['weapons']) & have:
            m = float(p.get('weapon_mult', m))
        fw, fh = getattr(target, 'footprint', (1, 1)) or (1, 1)
        if p.get('big_mult') and int(fw) * int(fh) > 1:
            m = float(p['big_mult'])
        mult *= m
        if consume:
            tell(player, target, a)
    return mult


def weakness_amp(player, target, hits_weakness: bool, consume: bool = False) -> float:
    """A blow that strikes the creature's listed weakness: the strongest
    such technique."""
    if not hits_weakness or not _recognised(player, target):
        return 1.0
    best, ab = 1.0, None
    for a, p in parts(player, _fam(target), 'weakness_amp'):
        if float(p.get('mult', 1.0)) > best:
            best, ab = float(p.get('mult', 1.0)), a
    if consume and ab is not None:
        tell(player, target, ab)
    return best


def pierce_resist(player, target, chain: int, consume: bool = False) -> dict:
    """{'pierce', 'scales', 'blessed'}: at its chain, the blow ignores the
    creature's resistances (as the chain specials' bypass does), and with
    `scales` its scales and wards too; `blessed` counts the weapon blessed."""
    out = {'pierce': False, 'scales': False, 'blessed': False}
    if target is None or not _recognised(player, target):
        return out
    for a, p in parts(player, _fam(target), 'pierce_resist'):
        if chain >= int(p.get('chain_min', 0) or 0):
            out['pierce'] = True
            out['scales'] = out['scales'] or bool(p.get('scales'))
            out['blessed'] = out['blessed'] or bool(p.get('blessed'))
            if consume:
                tell(player, target, a)
    return out


def extra_seconds(player, target) -> int:
    """More seconds on the maths clock for an attack on `target`."""
    total = 0
    if target is not None and _recognised(player, target):
        for a, p in parts(player, _fam(target), 'extra_seconds'):
            total += int(p.get('seconds', 0) or 0)
            tell(player, target, a)
    for _b, p in circle_parts(player, 'extra_seconds'):
        if p.get('boss_only') and not _named(target):
            continue
        total += int(p.get('seconds', 0) or 0)
    return total


def opening_chain(player, target, consume: bool = False) -> int:
    """Rungs added to the hero's FIRST blow of a fight on this creature
    (Mongoose: start at chain 2 is one rung more)."""
    if target is None or target.__dict__.get('_edge_opened') or not _recognised(player, target):
        return 0
    best, ab = 0, None
    for a, p in parts(player, _fam(target), 'opening_chain'):
        rungs = max(0, int(p.get('chain', 1) or 1) - 1)
        if rungs > best:
            best, ab = rungs, a
    if best and consume:
        target.__dict__['_edge_opened'] = True
        tell(player, target, ab)
    return best


def chain_forgive_ready(player, target) -> bool:
    """A wrong answer against this creature will not end the chain (once
    per fight)."""
    if target is None or not _recognised(player, target):
        return False
    uses = sum(int(p.get('uses', 1) or 1) for _a, p in parts(player, _fam(target), 'chain_forgive'))
    return uses > int(target.__dict__.get('_edge_forgiven', 0) or 0)


def spend_chain_forgive(player, target) -> None:
    target.__dict__['_edge_forgiven'] = int(target.__dict__.get('_edge_forgiven', 0) or 0) + 1
    got = parts(player, _fam(target), 'chain_forgive')
    if got:
        tell(player, target, got[0][0])


def prevents_split(player, target) -> bool:
    got = _mine(player, target, 'prevent_split')
    if got:
        tell(player, target, got[0][0])
    return bool(got)


def block_regen_turns(player, target) -> int:
    best = 0
    for _a, p in _mine(player, target, 'block_regen'):
        best = max(best, int(p.get('turns', 0) or 0))
    return best


def _execute_parts(player, target, chain):
    return [(a, p) for a, p in _mine(player, target, 'execute')
            if chain >= int(p.get('chain_min', 99) or 99)]


def execute_named_mult(player, target, chain: int, consume: bool = False) -> float:
    """Against a NAMED foe an execute lands a harder blow instead (+25%),
    when its chain is reached and the foe is below its health line."""
    if target is None or not _named(target):
        return 1.0
    best, ab = 1.0, None
    hp_share = target.hp / max(1, target.max_hp)
    for a, p in _execute_parts(player, target, chain):
        if hp_share < float(p.get('hp_below', 0)) or float(p.get('hp_below', 0)) >= 1.0:
            if float(p.get('named_mult', 1.0)) > best:
                best, ab = float(p.get('named_mult', 1.0)), a
    if consume and ab is not None:
        tell(player, target, ab)
    return best


def execute(player, target, chain: int):
    """The execute that ends this lesser creature now (after the blow
    landed), or None. Never a named foe (or the Black Knight: _steadfast)."""
    if target is None or _steadfast(target) or not getattr(target, 'alive', False):
        return None
    hp_share = target.hp / max(1, target.max_hp)
    for a, p in _execute_parts(player, target, chain):
        if hp_share < float(p.get('hp_below', 0)) or float(p.get('hp_below', 0)) >= 1.0:
            return a, p
    return None


def turn_on_hit(player, target, chain: int):
    for a, p in _mine(player, target, 'turn'):
        if p.get('trigger') == 'on_hit' and chain >= int(p.get('chain_min', 0) or 0):
            return a, p
    return None


def turn_on_kill(player, target):
    if target is None:
        return None
    for a, p in parts(player, _fam(target), 'turn'):
        if p.get('trigger') == 'on_kill':
            return a, p
    return None


def turn_on_sight(player, fid):
    for a, p in parts(player, fid, 'turn'):
        if p.get('trigger') == 'on_sight':
            return a, p
    return None


def calm_chance(player, fid) -> tuple:
    """(chance, ability) that a lesser member of `fid` arrives calm."""
    best, ab = 0.0, None
    for a, p in parts(player, fid, 'calm_on_arrival'):
        if float(p.get('chance', 0)) > best:
            best, ab = float(p.get('chance', 0)), a
    return best, ab


def charm_on_hit(player, target, chain: int):
    if _steadfast(target):
        return None
    for a, p in _mine(player, target, 'charm_on_hit'):
        if chain >= int(p.get('chain_min', 0) or 0):
            return a, p
    return None


def stun_on_hit(player, target, chain: int):
    if _named(target):
        return None
    for a, p in _mine(player, target, 'stun_on_hit'):
        if chain >= int(p.get('chain_min', 0) or 0):
            return a, p
    return None


def surrender(player, target, chain: int):
    """The surrender a lesser foe makes now (after the blow), or None."""
    if target is None or _steadfast(target) or not getattr(target, 'alive', False):
        return None
    if target.__dict__.get('_surrendered'):
        return None
    for a, p in _mine(player, target, 'surrender'):
        if (chain >= int(p.get('chain_min', 0) or 0)
                and target.hp < float(p.get('hp_below', 0)) * max(1, target.max_hp)):
            return a, p
    return None


def harvest_bonus(player, kind) -> tuple:
    """(extra portions, ability) for harvesting a corpse of `kind`."""
    best, ab = 0, None
    for a, p in parts(player, family_lore.family_of(kind), 'harvest_bonus'):
        if int(p.get('portions', 0) or 0) > best:
            best, ab = int(p.get('portions', 0) or 0), a
    return best, ab


# ---------------------------------------------------------------------------
# What a landed blow sets off (combat.player_attack calls this once)
# ---------------------------------------------------------------------------
def after_blow(player, target, chain: int, actual: int, monsters=(), visible=None,
               rng=random) -> dict:
    """Run the on-hit techniques for a weapon blow that landed and return
    what happened: {'executed': ability|None, 'surrendered': params|None,
    'gold_drop': bool}. Messages go to the outbox. Turning sends every
    lesser member of the family the hero can see fleeing; named foes are
    never turned, charmed, stunned, made to surrender or executed."""
    out = {'executed': None, 'surrendered': None}
    if target is None or actual <= 0:
        return out
    fid = _fam(target)
    turns = block_regen_turns(player, target)
    if turns and getattr(target, 'alive', False):
        target.__dict__['_regen_blocked'] = max(int(target.__dict__.get('_regen_blocked', 0) or 0), turns)
        got = _mine(player, target, 'block_regen')
        if got:
            tell(player, target, got[0][0])
    ex = execute(player, target, chain)
    if ex is not None:
        a, p = ex
        target._has_revived = True           # no mist, no rising, no second life
        target._pending_splits = 0
        target.__dict__['_no_split_blow'] = True
        try:
            target.take_damage(max(1, int(target.hp)), ignore_resistance=True)
        finally:
            target.__dict__.pop('_no_split_blow', None)
        target.alive = False
        target.hp = 0
        word = VARIANT_WORDS.get(p.get('variant'), 'falls')
        say(player, a.get('trigger_msg') or f"{a.get('name', '')}! It {word}.")
        out['executed'] = a
    if getattr(target, 'alive', False):
        th = turn_on_hit(player, target, chain)
        if th is not None:
            n = turn_members(player, fid, th[1], monsters, visible)
            if n:
                tell(player, target, th[0])
        ch = charm_on_hit(player, target, chain)
        if ch is not None and not target.resists_control('charmed'):
            target.hold('charmed', int(ch[1].get('turns', 1)))
            tell(player, target, ch[0])
        st = stun_on_hit(player, target, chain)
        if st is not None:
            target.hold('stunned', int(st[1].get('turns', 1)))
            tell(player, target, st[0])
        su = surrender(player, target, chain)
        if su is not None:
            a, p = su
            target.__dict__['_surrendered'] = True
            target.hold('feared', int(p.get('turns', 8)))
            target._flee_timer = max(int(getattr(target, '_flee_timer', 0) or 0), int(p.get('turns', 8)))
            say(player, a.get('trigger_msg') or f"{a.get('name', '')}!")
            out['surrendered'] = p
    return out


def after_kill(player, target, monsters=(), visible=None, rng=random) -> int:
    """A kill by the hero's weapon: an on-kill turn (Break Their Nerve) may
    rout the lesser members of the family in sight. Returns how many fled."""
    tk = turn_on_kill(player, target)
    if tk is None:
        return 0
    n = turn_members(player, _fam(target), tk[1], monsters, visible, rng=rng, exclude=target)
    if n:
        tell(player, None, tk[0])
    return n


def turn_members(player, fid, params, monsters, visible, rng=random, exclude=None) -> int:
    """Send the lesser members of `fid` the hero can see fleeing (the
    engine's monster fear: Monster.take_turn flees while feared, and
    Monster.resists_control keeps the mindless and named foes steady)."""
    n = 0
    chance = float(params.get('chance', 1.0) if params.get('chance') is not None else 1.0)
    for m in monsters or ():
        if m is exclude or not getattr(m, 'alive', False) or _fam(m) != fid:
            continue
        if visible is not None and (m.x, m.y) not in visible:
            continue
        if not _recognised(player, m) or _steadfast(m) or getattr(m, 'is_allied', False):
            continue
        if m.resists_control('feared') or getattr(m, 'fearless', False):
            continue
        if chance < 1.0 and rng.random() >= chance:
            continue
        m.hold('feared', int(params.get('turns', 1)))
        n += 1
    return n


def on_sight_turns(player, monsters, visible) -> list:
    """Each turn: the families the hero has a turn-on-sight technique for
    flee from him (Your Name Is Known). Returns the abilities that fired."""
    fired = []
    fams = {}
    for fid in family_lore.tiers(player):
        got = turn_on_sight(player, fid)
        if got:
            fams[fid] = got
    if not fams:
        return fired
    for fid, (a, p) in fams.items():
        if turn_members(player, fid, p, monsters, visible):
            fired.append(a)
    return fired


def calm_arrivals(player, monsters, rng=random) -> list:
    """A floor just reached: lesser members of a family with calm_on_arrival
    may arrive calm (the engine's charm, which a blow breaks: the same rule
    as Gilgamesh's Bribe). Returns the abilities that calmed anything.
    Never a concealed creature (an invisible one, an ambusher not yet
    sprung, a disguised mimic): calming it, and the line that says so,
    would give it away."""
    fired = []
    by_fid = {}
    for m in monsters or ():
        if not getattr(m, 'alive', False) or _steadfast(m) or getattr(m, 'is_allied', False):
            continue
        if not _recognised(player, m):
            continue
        fid = _fam(m)
        if fid not in by_fid:
            by_fid[fid] = calm_chance(player, fid)
        chance, ab = by_fid[fid]
        if chance <= 0 or m.resists_control('charmed'):
            continue
        if rng.random() < chance:
            m.status_effects['charmed'] = max(int(m.status_effects.get('charmed', 0) or 0), 9999)
            m.__dict__['_bribed'] = True        # a blow breaks the calm
            if ab not in fired:
                fired.append(ab)
    return fired
