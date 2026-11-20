"""Named counters: a thing that blocks one technique outright (winning-build
plan 2026-11-13, section 3.3; slice 5).

A piece's ``counters`` (its own data, or its shield template's) names the
techniques it stops while worn, or while carried where the technique says
so (data/arsenal.json ``counters``):

* **gaze** -- the mirror shield (data/templates/shields/mirror_shield.json;
  the Aegis of Athena too). Perseus watched Medusa in his polished shield.
  A gaze attack does nothing at all: no damage, no rider. Every gaze: the
  gorgons' and basilisks', the floating eye's.
* **voice** -- beeswax earplugs, put in or taken out with the Kit's Apply
  (one turn). Odysseus stopped his crew's ears against the Sirens. The rider
  of a voice attack never takes hold (a wail's fear, a song's sleep, a
  scream's confusion). The price: while the wax is in he hears nothing
  (``deafened``): no war-band heard on arriving, and no warning
  growl from a pet that smells what he cannot see.
* **fey_glamour** -- the cold-iron charm, carried. The Fair Folk cannot
  abide cold iron: their charm, confusion, sleep and visions slide off, by
  the same rule a cold-iron body armour's ward follows (data/gear_rules.json
  ``wards``).

The tells' counter lines name them (data/tells.json), so a kid who studies a
kind knows what to look for. ``names_for`` gives the counters that would
answer one creature's technique, for a tell or Kit Sense to name.

Pure: no pygame, no Game. monster.py asks ``blocks_gaze`` and
``blocks_rider``.
"""
from __future__ import annotations

GAZE, VOICE, FEY = 'gaze', 'voice', 'fey_glamour'

# Told each time a counter does its work (a gaze turned, a voice unheard, a
# glamour broken): fn(technique id, the creature). The Game binds it for the
# run (game_seeker.SeekerMixin._seeker_init) so the Seeker hears of it: the
# Polished Shield, Deaf to Riddles, Old Remedies. None: nobody listens.
ON_COUNTER = None


def fired(tid: str, source) -> None:
    """A counter just did its work against ``source``."""
    fn = ON_COUNTER
    if fn is None:
        return
    try:
        fn(str(tid), source)
    except Exception:
        pass


def rules() -> dict:
    import coatings
    return coatings.data().get('counters') or {}


def technique(tid: str) -> dict:
    return (rules().get('techniques') or {}).get(tid) or {}


def item_counters(item) -> list:
    """The techniques ``item`` blocks: its own ``counters`` and, for a
    shield or armour piece, its template's."""
    if item is None:
        return []
    out = list(getattr(item, 'counters', None) or ())
    if getattr(item, 'item_class', '') in ('shield', 'armor'):
        try:
            import gear
            out += list(gear.piece_template(item).get('counters') or ())
        except Exception:
            pass
    return list(dict.fromkeys(str(t) for t in out if t))


def _worn(player) -> list:
    out = [a for a in (getattr(player, 'armor_slots', None) or ()) if a is not None]
    for it in (getattr(player, 'shield', None), getattr(player, 'amulet_slot', None),
               getattr(player, 'belt_slot', None)):
        if it is not None:
            out.append(it)
    out += [a for a in (getattr(player, 'accessory_slots', None) or ()) if a is not None]
    return out


def ears_stopped(player) -> bool:
    """The earplugs are in: the flag is set and the plugs are still in the
    pack (sold, dropped or stolen, they are not in his ears either). Once
    they are gone the flag goes with them, so another pair picked up later
    is not in his ears by itself (bug bash WB-A05)."""
    if not getattr(player, 'ears_stopped', False):
        return False
    if any(technique(t).get('apply') == 'stop_ears'
           for it in (getattr(player, 'inventory', None) or ())
           for t in item_counters(it)):
        return True
    try:
        player.ears_stopped = False
    except Exception:
        pass
    return False


def deafened(player) -> bool:
    """He hears nothing: a counter that deafens is in."""
    return ears_stopped(player)


def active(player) -> list:
    """[(item, technique id)] the hero has working now: worn pieces, carried
    charms, and the earplugs while they are in."""
    out = []
    seen = set()
    for it in _worn(player):
        for t in item_counters(it):
            if technique(t).get('apply'):
                continue                # put in, not worn (the earplugs)
            out.append((it, t))
            seen.add(id(it))
    for it in getattr(player, 'inventory', None) or ():
        if id(it) in seen:
            continue
        for t in item_counters(it):
            d = technique(t)
            if d.get('carried'):
                out.append((it, t))
            elif d.get('apply') == 'stop_ears' and ears_stopped(player):
                out.append((it, t))
    return out


def _first(player, tid: str):
    for it, t in active(player):
        if t == tid:
            return it
    return None


def blocks_gaze(player, source=None):
    """The piece that turns a gaze from ``source`` aside, or None."""
    return _first(player, GAZE)


def _is_fey(source, ward: dict) -> bool:
    fams, tags = set(ward.get('families') or ()), set(ward.get('tags') or ())
    if not fams and not tags:
        return True
    fam = str(getattr(source, 'family', '') or '')
    return fam in fams or bool(set(getattr(source, 'tags', None) or ()) & tags)


def blocks_rider(player, source, atk: dict, effect_id: str):
    """(piece, technique id) when a named counter stops this attack's rider
    outright, else None: wax against a voice, cold iron against the Fair
    Folk's glamour (a gaze is turned before it lands: ``blocks_gaze``)."""
    if not effect_id:
        return None
    import guards
    d = guards.delivery(atk or {})
    for it, t in active(player):
        tech = technique(t)
        if tech.get('riders_of') and tech['riders_of'] == d:
            return it, t
        if tech.get('delivery') == d == GAZE:
            return it, t
        ward_id = tech.get('ward')
        if ward_id:
            try:
                import gear
                ward = gear.ward_rules().get(ward_id) or {}
            except Exception:
                ward = {}
            if effect_id in (ward.get('effects') or ()) and _is_fey(source, ward):
                return it, t
    return None


def line(player, piece, tid: str, source) -> str:
    """What the log says when a counter fires (and the listener told)."""
    from monster import the_name
    fired(tid, source)
    try:
        from hud_context import item_bare_name
        iname = item_bare_name(player, piece)
    except Exception:
        iname = str(getattr(piece, 'name', 'shield'))
    text = str(technique(tid).get('line', 'Your {item} turns it aside.'))
    return text.format(item=iname, the=the_name(source, lower=True), The=the_name(source))


def card_lines(item) -> list:
    """What a counter piece blocks, for its card."""
    return [str(technique(t).get('card')) for t in item_counters(item) if technique(t).get('card')]


def is_applied(item) -> bool:
    """A counter put in or taken out with the Kit's Apply (the earplugs)."""
    return any(technique(t).get('apply') == 'stop_ears' for t in item_counters(item))


def crows(item) -> bool:
    """A counter let loose with the Kit's Apply (the caged cockerel's crow:
    game_lore_powers.py)."""
    return any(technique(t).get('apply') == 'crow' for t in item_counters(item))


def shuns(player, source):
    """(piece, technique id) when a carried counter keeps this kind of
    creature from striking at all (the whitethorn and the strix), else None."""
    kind = str(getattr(source, 'kind', '') or '')
    if not kind or not any(kind in (d.get('kinds') or ()) for d in (rules().get('techniques') or {}).values()):
        return None
    for it, t in active(player):
        if kind and kind in (technique(t).get('kinds') or ()):
            return it, t
    return None


def toggle_ears(player) -> str:
    """Put the earplugs in or take them out; the line."""
    st = rules().get('stop_ears') or {}
    now = not bool(getattr(player, 'ears_stopped', False))
    player.ears_stopped = now
    return str(st.get('in' if now else 'out', ''))


def hud_rows(player) -> list:
    """[(label, kind)] for the sidebar: the stopped ears."""
    if ears_stopped(player):
        return [(str((rules().get('stop_ears') or {}).get('chip', 'Ears Stopped')), 'ears')]
    return []


def names_for(m, key: str) -> list:
    """The counter technique ids that answer creature ``m``'s tell ``key``
    (an effect id or a flag): for a tell or Kit Sense to name the piece.
    'gaze' for a gaze, 'voice' for a voice's rider, 'fey_glamour' for a
    fairy's charm, confusion, sleep or visions."""
    import guards
    out = []
    if key == 'gaze_paralyze' and getattr(m, 'gaze_paralyze', 0):
        out.append(GAZE)
    for atk in getattr(m, 'attacks', None) or ():
        if not isinstance(atk, dict) or atk.get('effect') != key:
            continue
        d = guards.delivery(atk)
        if d == 'gaze':
            out.append(GAZE)
        elif d == 'voice':
            out.append(VOICE)
    try:
        import gear
        ward = gear.ward_rules().get('fey_glamour') or {}
        if key in (ward.get('effects') or ()) and _is_fey(m, ward):
            out.append(FEY)
    except Exception:
        pass
    return list(dict.fromkeys(out))
