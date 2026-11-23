"""What a scroll, potion, wand or spellbook does, in plain words.

Brandon's play-test, 2026-11-22: "for scrolls and spells, I can't tell what
they actually do... Effects lists the cost, and lore hints, but nothing is
actually printed there." The Kit card said "Nothing beyond its stats." for
every consumable, the menus showed a code name ("Effect: Heal  tier 1").

The words are data (data/ui/item_effects.json), one line per effect id; this
module fills them from the item's own fields (its dice, its tier, its turns,
its charges, the ward or the family it names) and, when a hero is given, from
him (his health for a heal's least share, his Intelligence for a wand's
damage, his sight, his armour's tax on a spell). The numbers are the ones the
handlers use: a scroll kind keeps its own in its data entry (an entry's
``fields``: map_radius, light_turns, delta..., read by wards.field_of as its
handler reads them), the rest are read from the handlers' own modules
(game_magic, food_system, status_effects, lights, wards), and
tests/test_item_words.py pins both.

Pure: no Game. It never asks whether the item is identified; the callers
gate that as before (unidentified still says to identify it).

    what_it_does(item, player=None, buc_known=None, item_class=None) -> [str]
    short_line(item, player=None, buc_known=None, item_class=None) -> str

``item`` is an item object or a data entry (a dict: the Encyclopedia's pages,
with ``item_class`` given).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

CLASSES = ('scroll', 'potion', 'wand', 'spellbook')
FALLBACK = "What it does is not written down."
_DICE = re.compile(r'^(\d*)d(\d+)([+-]\d+)?$')
_MONSTER_MAX_TURNS = 60            # monster.add_effect's cap (status_effects.MAX_EFFECT_DURATION)


@lru_cache(maxsize=1)
def data() -> dict:
    """data/ui/item_effects.json, read once ({} when it cannot be read)."""
    try:
        from paths import data_path
        with open(data_path('data', 'ui', 'item_effects.json'), encoding='utf-8') as f:
            got = json.load(f)
        return got if isinstance(got, dict) else {}
    except (OSError, ValueError, ImportError):
        return {}


def _get(item, key: str, default=None):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def item_class_of(item, item_class: str | None = None) -> str:
    """'scroll', 'potion', 'wand', 'spellbook' or ''."""
    if item_class in CLASSES:
        return item_class
    ic = str(_get(item, 'item_class', '') or '')
    if ic in CLASSES:
        return ic
    name = type(item).__name__.lower()
    if name in CLASSES:
        return name
    if _get(item, 'spell_id', None) is not None and not _get(item, 'effect', ''):
        return 'spellbook'
    return ''


def covers(item, item_class: str | None = None) -> bool:
    """Is this one of the items these words are for?"""
    return item_class_of(item, item_class) in CLASSES


def entry(item_class: str, effect: str, item_id: str = '') -> dict:
    """The words for one kind: its own (``by_id``) or its effect's. {} if none."""
    d = data()
    own = ((d.get('by_id') or {}).get(item_class) or {}).get(str(item_id or ''))
    if own:
        return dict(own)
    if item_class == 'spellbook':
        return dict(d.get('spellbook') or {})
    return dict((d.get(item_class) or {}).get(str(effect or '')) or {})


def effect_ids(item_class: str) -> set:
    """Every effect id the words cover for a class."""
    return {k for k in (data().get(item_class) or {}) if not k.startswith('_')}


# ---------------------------------------------------------------- the numbers

def _tstep(item, cls: str) -> int:
    """0..4: a scroll's own tier (its quiz tier when it has none), a wand's
    quiz tier, a potion's tier. The ladders' index."""
    if cls == 'wand':
        t = _get(item, 'quiz_tier', None) or _get(item, 'tier', 1)
    else:
        t = _get(item, 'tier', None) or _get(item, 'quiz_tier', 1)
    try:
        t = int(t)
    except (TypeError, ValueError):
        t = 1
    return min(max(0, t - 1), 4)


def _int_of(v):
    try:
        s = str(v).strip()
        if not s or 'd' in s.lower():
            return None
        return int(s)
    except (TypeError, ValueError):
        return None


def dice_range(power) -> tuple | None:
    """(least, most) a dice string rolls, or None."""
    s = str(power or '').strip().lower().replace(' ', '')
    m = _DICE.fullmatch(s)
    if not m:
        n = _int_of(s)
        return (n, n) if n is not None else None
    count = int(m.group(1) or 1)
    sides = int(m.group(2))
    mod = int(m.group(3) or 0)
    return count + mod, count * sides + mod


def _hero_int(player) -> int:
    try:
        return int(getattr(player, 'INT', 10) or 10)
    except (TypeError, ValueError):
        return 10


def _wand_damage(item, player) -> str:
    """A wand's damage as its handler rolls it: the dice x the wand tier's
    multiplier x the Intelligence factor (game_magic._wand_tier_damage)."""
    rng = dice_range(_get(item, 'power', ''))
    if rng is None:
        return '?'
    from game_magic import WAND_TIER_MULT, int_damage_factor
    tier = int(_get(item, 'quiz_tier', None) or _get(item, 'tier', 1) or 1)
    mult = WAND_TIER_MULT.get(tier, 1.5) * int_damage_factor(_hero_int(player))
    lo, hi = (max(1, int(v * mult)) for v in rng)
    return f"{lo}" if lo == hi else f"{lo} to {hi}"


def wand_turns(item, base: int, tier_only: bool = False) -> int:
    """game_magic._wand_effect_duration: the wand's power when it is a plain
    number, else its tier's share of ``base`` (game_helpers.wand_tier_duration).
    A monster holds a status 60 turns at most."""
    from game_helpers import wand_tier_duration
    n = None if tier_only else _int_of(_get(item, 'power', ''))
    if n is not None:
        turns = max(1, n)
    else:
        turns = wand_tier_duration(int(base), int(_get(item, 'quiz_tier', None) or 1))
    return min(turns, _MONSTER_MAX_TURNS)


def hero_turns(status: str, duration: int, ward: bool = False) -> int:
    """The turns a dose lays on the hero, as status_effects.apply_effect cuts
    them: a control effect to its cap, a capped status to its cap, the rest
    to 60. A ward potion carries a cap of its own (food_system._ward_potion)."""
    duration = max(1, int(duration))
    if ward:
        return duration
    from status_effects import CONTROL, CONTROL_CAP, STATUS_CAP, MAX_EFFECT_DURATION
    if status in CONTROL:
        most = CONTROL_CAP.get(status)
        if most is not None:
            duration = min(duration, most)
        return min(duration, MAX_EFFECT_DURATION)
    if status in STATUS_CAP:
        return min(duration, STATUS_CAP[status])
    return min(duration, MAX_EFFECT_DURATION)


def _buc(item, buc_known) -> str:
    """The copy's blessing as the hero knows it: 'uncursed' while unknown."""
    if not buc_known:
        return 'uncursed'
    b = str(_get(item, 'buc', 'uncursed') or 'uncursed')
    return b if b in ('blessed', 'cursed') else 'uncursed'


def _pick(value, t: int):
    """A template or a list of five by tier."""
    if isinstance(value, list):
        return value[min(t, len(value) - 1)] if value else ''
    return value


def _points(n: int) -> str:
    return f"{n} point" if n == 1 else f"{n} points"


class _Fields(dict):
    """The placeholders, filled on demand from the item, its entry and the hero."""

    def __init__(self, item, cls: str, spec: dict, player, buc: str):
        super().__init__()
        self.item, self.cls, self.spec, self.player, self.buc = item, cls, spec, player, buc
        self.t = _tstep(item, cls)

    def __missing__(self, key):
        val = self._compute(key)
        self[key] = val
        return val

    def _ladder(self, key):
        # A number the kind keeps in its own data entry (``fields``: a
        # scroll's map_radius, light_turns, delta...), by the blessing the
        # hero knows: the very lookup its handler makes (wards.field_of).
        if key in (self.spec.get('fields') or ()):
            import wards
            got = wards.field_of(self._own_def(), key, self.buc)
            if got is not None:
                return got
        tiers = self.spec.get('tiers') or {}
        if self.buc != 'uncursed' and f"{key}_{self.buc}" in tiers:
            return tiers[f"{key}_{self.buc}"][self.t]
        if key in tiers:
            return tiers[key][self.t]
        return None

    def _compute(self, key):
        it, spec, p = self.item, self.spec, self.player
        lad = self._ladder(key)
        if lad is not None:
            return lad
        d = data()
        if key == 'power':
            return str(_get(it, 'power', '') or '?')
        if key == 'int_note':
            return '' if p is not None else d.get('int_note', '')
        if key == 'boss_cap':
            return d.get('boss_cap', '')
        if key == 'damage':
            return _wand_damage(it, p)
        if key == 'least':
            return self._least()
        if key == 'turns':
            return self._turns()
        if key in (spec.get('tier_turns') or {}):
            from game_helpers import wand_tier_duration
            n = wand_tier_duration(int(spec['tier_turns'][key]),
                                   int(_get(it, 'quiz_tier', None) or 1))
            return min(n, _MONSTER_MAX_TURNS)
        if key == 'share':
            from game_magic import EARTH_SHARE, int_damage_factor
            share = EARTH_SHARE[self.t] * (int_damage_factor(_hero_int(p)) / 2.0)
            return f"{round(100 * share)}%"
        if key == 'also':
            return self._also()
        if key == 'ward':
            return self._ward()
        if key == 'family':
            fam = str(self._own_def().get('family') or _get(it, 'family', '') or '')
            return (d.get('family_words') or {}).get(fam, fam.replace('_', ' ') or 'creature')
        if key == 'sight':
            import lights
            return lights.status_sight()
        if key == 'radius':
            # The wand of secret door detection: as far as he sees, 4 at least.
            if p is not None and hasattr(p, 'get_sight_radius'):
                try:
                    return d.get('radius_hero', 'within {n} tiles of you').format(
                        n=max(4, int(p.get_sight_radius())))
                except Exception:
                    pass
            return d.get('radius_words', 'as far as you can see')
        if key == 'dance_turns':
            try:
                import stray_kids
                return int(stray_kids.data()['stars']['dance_turns'])
            except Exception:
                return 'a few'
        if key == 'per_turn':
            from status_effects import DOT_SHARE, dot_tick
            pct = f"{round(DOT_SHARE * 100)}% of your health"
            if p is None:
                return pct
            # What a turn of it takes from this hero (his toughness, what
            # resists poison: Player.damage_after), as the tick will.
            n = dot_tick(p)
            if callable(getattr(p, 'damage_after', None)):
                n = p.damage_after(n, 'poison')
            return f"{pct} ({n})"
        if key == 'amount':
            return _points(2 if self.buc == 'cursed' else 1)
        if key.startswith('quiz_'):
            q = dict(_get(it, 'quiz', None) or {})
            if key == 'quiz_subjects':
                return ' or '.join(str(s).title() for s in (q.get('subjects') or ['philosophy']))
            if key == 'quiz_stat':
                return str(q.get('stat', 'WIS'))
            if key == 'quiz_amount':
                return int(q.get('amount', 1) or 1)
        return '?'

    def _own_def(self) -> dict:
        """The kind's data entry for the fields the item objects do not copy
        (a scroll's ``turns``, ``ward``, ``family``; wards.item_def)."""
        it = self.item
        if isinstance(it, dict):
            return it
        try:
            import wards
            return wards.item_def(self.cls, str(_get(it, 'id', '') or ''))
        except Exception:
            return {}

    def _least(self) -> str:
        """A heal's least share of the hero's health, as its handler mends."""
        cls, eff = self.cls, str(_get(self.item, 'effect', '') or '')
        if cls == 'scroll':
            from game_magic import SCROLL_HEAL_SHARE
            share = SCROLL_HEAL_SHARE[self.t]
        elif cls == 'wand':
            from game_magic import WAND_HEAL_SHARE
            share = WAND_HEAL_SHARE
        else:
            from food_system import POTION_HEAL_SHARE, POTION_EXTRA_HEAL_SHARE
            share = POTION_EXTRA_HEAL_SHARE if eff == 'extra_heal' else POTION_HEAL_SHARE
        d = data()
        pct = round(share * 100)
        p = self.player
        if p is not None:
            try:
                n = int(round(share * max(1, int(p.max_hp))))
                return d.get('least_words_hero', '{pct}%').format(pct=pct, n=n)
            except (TypeError, ValueError, AttributeError):
                pass
        return d.get('least_words', '{pct}%').format(pct=pct)

    def _turns(self):
        it, cls, spec, buc = self.item, self.cls, self.spec, self.buc
        if cls == 'wand':
            if str(_get(it, 'effect', '')) == 'light':
                import lights
                return lights.wand_light(it)[0] if not isinstance(it, dict) else \
                    lights.wand_turns(it.get('power', ''))
            return wand_turns(it, int(spec.get('base_turns', 8)), bool(spec.get('tier_only')))
        if cls == 'scroll':
            pt = spec.get('power_turns')
            if pt:
                # The kind's power is its turns (today's data, as its handler
                # reads it; a tier's share of it when the data gives 'mult').
                base = (_int_of(self._own_def().get('power', '')) or _int_of(_get(it, 'power', ''))
                        or int(pt.get('default', 10)))
                mult = pt.get('mult')
                turns = max(int(pt.get('least', 1)),
                            int(base * mult[self.t]) if mult else base)
                from status_effects import MAX_EFFECT_DURATION
                return min(turns, MAX_EFFECT_DURATION)
            # The family wards and the Piper's tune: the kind's own turns,
            # a blessed scroll half again, a cursed one half (_mm_scroll).
            mult = 1.5 if buc == 'blessed' else (0.5 if buc == 'cursed' else 1.0)
            return max(1, int(int(self._own_def().get('turns', 10) or 10) * mult))
        if cls == 'potion':
            kind = spec.get('buc', '')
            dur = int(spec.get('base_turns', 0) or _get(it, 'duration', 0) or 0)
            if kind in ('buff', 'ward'):
                mult = 1.5 if buc == 'blessed' else (0.5 if buc == 'cursed' else 1.0)
            elif kind == 'harm':
                mult = 1.5 if buc == 'cursed' else 1.0
            else:
                mult = 1.0
            dur = max(1, int(dur * mult))
            if kind == 'ward':
                return dur
            return hero_turns(str(spec.get('status', '')), dur)
        return '?'

    def _also(self) -> str:
        """What a protection rite also keeps off (data 'ward_also'); a cursed
        scroll gives only its shield (game_wards._protection_also)."""
        if self.buc == 'cursed':
            return ''
        also = self._own_def().get('ward_also') or _get(self.item, 'ward_also', None) or []
        if not also:
            return ''
        d = data()
        words = d.get('protection_also') or {}
        from status_effects import EFFECT_INFO
        by_turns: dict = {}
        for st, n in also:
            w = words.get(st) or (EFFECT_INFO.get(st) or ('', '', st.replace('_', ' ')))[2].lower()
            by_turns.setdefault(int(n), []).append(w)
        out = ''
        for n, ws in by_turns.items():
            out += d.get('protection_also_line', ' For {n} turns, also: {words}.').format(
                n=n, words=' and '.join(ws))
        return out

    def _ward(self) -> str:
        try:
            import wards
            desc = str(wards.ward_spec(self._own_def().get('ward', '')).get('desc', '') or '')
        except Exception:
            desc = ''
        return (desc[:1].lower() + desc[1:]) if desc else 'a ward keeps you'


def _fill(template, fields: _Fields) -> str:
    if not template:
        return ''
    try:
        return str(template).format_map(fields)
    except (KeyError, ValueError, IndexError, AttributeError):
        return str(template)


def _notes(cls: str, spec: dict, buc: str) -> list:
    """The blessing's or the curse's note after the line (known copies only)."""
    if buc == 'uncursed':
        return []
    out = []
    if spec.get(buc):
        out.append(spec[buc])
    d = data()
    if cls == 'potion':
        kind = spec.get('buc', '')
        note = (d.get('potion_notes') or {}).get(f"{kind}_{buc}")
        if note:
            out.append(note)
    if cls == 'wand':
        note = (d.get('wand_notes') or {}).get(buc)
        if note:
            out.append(note)
    return out


def _spellbook_lines(item, player, short: bool) -> list:
    from spells import LEARNABLE_SPELLS, reach_words, spell_reach
    d = data().get('spellbook') or {}
    sid = str(_get(item, 'spell_id', '') or '')
    spell = LEARNABLE_SPELLS.get(sid) or {}
    name = spell.get('name') or _get(item, 'spell_name', '') or ''
    desc = str(spell.get('desc', '') or '').strip()
    if not name or not desc:
        return []
    try:
        base_mp = int(spell.get('mp_cost', _get(item, 'mp_cost', 0)) or 0)
    except (TypeError, ValueError):
        base_mp = 0
    mp = base_mp
    if player is not None and hasattr(player, 'spell_mp_cost'):
        try:
            mp = int(player.spell_mp_cost(base_mp))
        except Exception:
            mp = base_mp
    if short:
        return [str(d.get('short', '{spell}')).format(spell=name, mp=mp)]
    lines = [str(d.get('line', '{spell}: {desc}')).format(spell=name, desc=desc)]
    cost = (d.get('cost_taxed') if mp > base_mp else d.get('cost')) or ''
    tail = cost.format(mp=mp, base_mp=base_mp) if cost else ''
    if spell.get('needs_target'):
        reach = spell_reach(spell)
        rw = d.get('reach') or {}
        words = reach_words(reach)
        key = 'sight' if words == 'sight' else ('touch' if words == 'touch' else 'tiles')
        if rw.get(key):
            tail = (tail + ' ' if tail else '') + rw[key].format(reach=words)
    if tail:
        lines.append(tail)
    known = getattr(player, 'known_spells', None) if player is not None else None
    if known and sid in known and d.get('known'):
        lines.append(d['known'])
    return lines


def _charges_line(item) -> str:
    d = data()
    if isinstance(item, dict):
        lo, hi = item.get('charges_min'), item.get('charges_max')
        if lo is not None and hi is not None and int(lo) != int(hi):
            return d.get('charges_found', '').format(charges_min=lo, charges_max=hi)
        n = item.get('charges', hi if hi is not None else lo)
        return d.get('charges_fixed', '').format(charges=n) if n is not None else ''
    if _get(item, 'charges', None) is None:
        return ''
    return d.get('charges', '').format(charges=_get(item, 'charges', 0),
                                       max_charges=_get(item, 'max_charges', 0))


def _lines(item, player, buc_known, item_class, short: bool) -> list:
    cls = item_class_of(item, item_class)
    if cls not in CLASSES:
        return []
    if buc_known is None:
        try:
            from items import buc_known_to
            buc_known = (not isinstance(item, dict)) and buc_known_to(item, player)
        except Exception:
            buc_known = False
    buc = _buc(item, buc_known)
    iid = str(_get(item, 'id', '') or _get(item, '_id', '') or '')
    effect = str(_get(item, 'effect', '') or '')
    spec = entry(cls, effect, iid)
    if cls == 'spellbook' and iid not in ((data().get('by_id') or {}).get('spellbook') or {}):
        # A book teaches its spell: the spell's own words, cost and reach.
        got = _spellbook_lines(item, player, short)
        return got or ([] if short else [data().get('fallback', FALLBACK)])
    if not spec:
        return [] if short else [data().get('fallback', FALLBACK)]
    fields = _Fields(item, cls, spec, player, buc)
    t = fields.t
    key = 'short' if short else 'line'
    template = spec.get(f"{key}_{buc}") if buc != 'uncursed' else None
    replaced = template is not None
    if template is None:
        template = spec.get(key) or (spec.get('line') if short else '')
    text = _fill(_pick(template, t), fields)
    if short:
        return [text] if text else []
    if not replaced:
        notes = [_fill(n, fields) for n in _notes(cls, spec, buc)]
        text = ' '.join([text] + [n for n in notes if n])
    out = [text] if text else [data().get('fallback', FALLBACK)]
    if cls == 'wand':
        ch = _charges_line(item)
        if ch:
            out.append(ch)
    return out


def what_it_does(item, player=None, buc_known=None, item_class: str | None = None) -> list:
    """The plain lines for a scroll, potion, wand (its charges too) or
    spellbook (its spell, cost and reach): [] for anything else, the
    fallback line for a kind the data does not word."""
    return _lines(item, player, buc_known, item_class, short=False)


def short_line(item, player=None, buc_known=None, item_class: str | None = None) -> str:
    """One short phrase for a list row ('' for anything else)."""
    got = _lines(item, player, buc_known, item_class, short=True)
    return got[0] if got else ''


def thrown_line(potion, debuff_map: dict, buff_map: dict, buffs_used=()) -> str:
    """What a potion does thrown at a foe, by the thrower's own maps
    (CombatMixin._THROW_DEBUFF_MAP, _THROW_BUFF_MAP, _THROW_BUFFS_MONSTERS_USE):
    a debuff for its turns (10 when it lasts none), a heal, a teleport, a
    drain's twentieth of its health; a buff a monster does not use, nothing."""
    words = data().get('thrown') or {}
    eff = str(_get(potion, 'effect', '') or '')
    if eff in debuff_map:
        from status_effects import EFFECT_INFO
        st = debuff_map[eff]
        name = (EFFECT_INFO.get(st) or (st.replace('_', ' ').title(),))[0]
        dur = int(_get(potion, 'duration', 0) or 0)
        turns = min(dur if dur > 0 else 10, _MONSTER_MAX_TURNS)
        return str(words.get('debuff', '')).format(status=name, turns=turns)
    if eff in buff_map:
        st = buff_map[eff]
        used = words.get('buff_used') or {}
        if st in buffs_used and used.get(st):
            return str(used[st])
        return str(words.get('none', ''))
    if eff in ('heal', 'extra_heal', 'full_heal'):
        return str(words.get('heal', ''))
    if eff == 'teleport':
        return str(words.get('teleport', ''))
    if eff in ('drain_str', 'drain_con', 'drain_int', 'drain_wis'):
        return str(words.get('drain', ''))
    return str(words.get('none', ''))
