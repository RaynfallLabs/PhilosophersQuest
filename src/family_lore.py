"""Monster family knowledge: who belongs to which family, and how far the
hero has climbed each family's ladder (MONSTER_FAMILIES_DESIGN.md and
docs/systems/monster_families_v2_design.md).

Pure module: no pygame, no Game. Every number lives in
data/monster_families.json; every monster's family is the `family` field of
data/monsters.json (tools/content/assign_monster_families.py writes it).

How knowledge is earned
  * ONE study is a correct corpse study or a Scroll of Omnisight
    (`record_study`). Killing, harvesting and seeing do not count, and the
    Book of Thoth opens Bestiary pages (Player.lore_known_monster_ids) but
    gives no tiers (decision 4).
  * Progress counts DIFFERENT kinds studied in the family
    (Player.studied_monster_ids): a known kind's corpse never asks again,
    so two skeletons teach no more than one. A keystone (a boss, a
    mini-boss, a seal demon, a monster with `proper_noun`, or one in its
    family's `keystones` list) counts `keystone_weight` (2) kinds.
  * A family's tier is the highest threshold that count reaches, or a secret
    build's head start (Player.family_lore_grants), whichever is higher.
    Nothing is computed from the floor.

What the game asks here
  * `family_of(kind)`, `family_name(fid)`, `members_seen(player, fid)`;
  * `tier(player, fid)`, `tiers(player)`, `progress(player, fid)`;
  * `has_page(player, kind)`: may the full Bestiary page open (ruling 1);
  * `record_study(player, kind)` then `news(player)`: the tiers, circles and
    title newly reached, once each (Player.family_tiers_told);
  * `arrival_lines(...)`: the Forewarned lines when the hero reaches a floor.

The abilities a tier grants are read by src/family_edges.py.
"""
from __future__ import annotations

import json

# Kinds built in code (not in monsters.json) that still have a family.
# The Bones ghost is a Ghost. Death, the secret cow and the ethereal unicorn
# have none (they are absent from both tables, so family_of gives None).
SPECIAL_KINDS = {'player_ghost': 'ghosts'}

_KINDS = None        # kind -> (family, is_keystone)
_DATA = None         # data/monster_families.json


def _load_json(*parts):
    from paths import data_path
    with open(data_path(*parts), encoding='utf-8') as fh:
        return json.load(fh)


def data() -> dict:
    """data/monster_families.json, loaded once."""
    global _DATA
    if _DATA is None:
        _DATA = _load_json('data', 'monster_families.json')
    return _DATA


def families() -> dict:
    return data().get('families', {})


def family(fid) -> dict:
    return families().get(fid) or {}


def _kinds() -> dict:
    global _KINDS
    if _KINDS is None:
        table = {}
        mons = _load_json('data', 'monsters.json')
        extra = {}
        for fid, f in families().items():
            for k in f.get('keystones', ()) or ():
                extra[k] = fid
        for kind, d in mons.items():
            fid = d.get('family')
            if not fid:
                continue
            key = bool(d.get('is_boss') or d.get('is_mini_boss') or d.get('is_seal_demon')
                       or d.get('proper_noun') or extra.get(kind) == fid)
            table[kind] = (fid, key)
        for kind, fid in SPECIAL_KINDS.items():
            table.setdefault(kind, (fid, False))
        _KINDS = table
    return _KINDS


def reload() -> None:
    """Forget the cached tables (tests, QA)."""
    global _KINDS, _DATA
    _KINDS = None
    _DATA = None


def _kind(obj) -> str:
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return obj.get('_id') or obj.get('id') or ''
    return (getattr(obj, 'monster_id', None) or getattr(obj, 'kind', None) or '') or ''


def family_of(obj) -> str | None:
    """The family id of a kind, a Monster, a Corpse or a monster dict."""
    if obj is None:
        return None
    if not isinstance(obj, (str, dict)):
        fam = obj.__dict__.get('family') if hasattr(obj, '__dict__') else None
        if fam:
            return fam
    elif isinstance(obj, dict) and obj.get('family'):
        return obj['family']
    rec = _kinds().get(_kind(obj))
    return rec[0] if rec else None


def is_keystone(kind) -> bool:
    rec = _kinds().get(_kind(kind))
    return bool(rec and rec[1])


def weight(kind) -> int:
    return int(data().get('keystone_weight', 2)) if is_keystone(kind) else 1


def members(fid) -> list:
    """Every kind in a family (for tools and tests; never shown whole)."""
    return sorted(k for k, (f, _key) in _kinds().items() if f == fid)


def family_name(fid) -> str:
    return family(fid).get('name', '') or str(fid or '').replace('_', ' ').title()


def short_name(fid) -> str:
    return family(fid).get('short', '') or family_name(fid)


def kin(fid) -> str:
    return family(fid).get('kin', '') or family_name(fid).lower()


def tier_names() -> list:
    return list(data().get('tier_names', ()))


def thresholds(fid) -> list:
    return [int(x) for x in family(fid).get('thresholds', ())]


def max_tier(fid) -> int:
    return len(thresholds(fid))


def tier_name(fid, t: int) -> str:
    tiers = family(fid).get('tiers', ())
    if 1 <= t <= len(tiers):
        return tiers[t - 1].get('name', '') or ''
    return ''


# ---------------------------------------------------------------------------
# The hero's knowledge
# ---------------------------------------------------------------------------
def studied(player) -> set:
    s = getattr(player, 'studied_monster_ids', None)
    return s if isinstance(s, set) else set(s or ())


def grants(player) -> dict:
    g = getattr(player, 'family_lore_grants', None)
    return g if isinstance(g, dict) else {}


def score(player, fid) -> int:
    """Kinds studied in the family, a keystone counting keystone_weight."""
    total = 0
    table = _kinds()
    for kind in studied(player):
        rec = table.get(kind)
        if rec and rec[0] == fid:
            total += int(data().get('keystone_weight', 2)) if rec[1] else 1
    return total


def tier_for_score(fid, n: int) -> int:
    t = 0
    for i, need in enumerate(thresholds(fid), start=1):
        if n >= need:
            t = i
    return t


def tiers(player) -> dict:
    """{family id: tier} for every family above tier 0. Cached on the
    player while the studied set and grants are unchanged."""
    if player is None:
        return {}
    s = studied(player)
    g = grants(player)
    key = (id(s), len(s), id(g), tuple(sorted(g.items())), id(_DATA))
    cache = player.__dict__.get('_family_tier_cache')
    if cache and cache[0] == key:
        return cache[1]
    counts = {}
    table = _kinds()
    w = int(data().get('keystone_weight', 2))
    for kind in s:
        rec = table.get(kind)
        if rec:
            counts[rec[0]] = counts.get(rec[0], 0) + (w if rec[1] else 1)
    out = {}
    for fid in families():
        t = max(tier_for_score(fid, counts.get(fid, 0)), int(g.get(fid, 0) or 0))
        t = min(t, max_tier(fid))
        if t > 0:
            out[fid] = t
    player.__dict__['_family_tier_cache'] = (key, out)
    return out


def tier(player, fid) -> int:
    return tiers(player).get(fid, 0) if fid else 0


def progress(player, fid) -> dict:
    """{'score', 'tier', 'next', 'next_name', 'line'}: the progress line
    "4 of 6 to Hunter", or "Every tier learned" at the top."""
    n = score(player, fid)
    t = tier(player, fid)
    th = thresholds(fid)
    if t >= len(th):
        return {'score': n, 'tier': t, 'next': None, 'next_name': '',
                'line': 'Every tier learned'}
    need = th[t]
    name = tier_name(fid, t + 1)
    return {'score': n, 'tier': t, 'next': need, 'next_name': name,
            'line': f"{min(n, need)} of {need} to {name}"}


def studied_count(player, fid) -> int:
    """Distinct kinds studied (keystones counted once: this is a count of
    kinds, the progress line counts their weight)."""
    table = _kinds()
    return sum(1 for k in studied(player) if (table.get(k) or (None,))[0] == fid)


def members_seen(player, fid) -> list:
    """The kinds of a family the hero has seen (never the unseen ones)."""
    seen = set(getattr(player, 'known_monster_ids', ()) or ())
    seen |= studied(player)
    table = _kinds()
    return sorted(k for k in seen if (table.get(k) or (None,))[0] == fid)


def recognised(player, kind) -> bool:
    """The hero knows this kind: studied, its page opened by the Book of
    Thoth or the Scroll of Omnisight, or its family at tier 1 or more."""
    k = _kind(kind)
    if not k:
        return False
    if k in studied(player) or k in set(getattr(player, 'lore_known_monster_ids', ()) or ()):
        return True
    return tier(player, family_of(k)) >= 1


def has_page(player, kind) -> bool:
    """Ruling 1: the full Bestiary page opens only for an identified kind."""
    return recognised(player, kind)


# ---------------------------------------------------------------------------
# Studying and the news it brings
# ---------------------------------------------------------------------------
def record_study(player, kind) -> bool:
    """One study of `kind` (a correct corpse study or Omnisight). Returns
    True when the kind is new to the hero. A kind with no family (Death,
    the cow, the unicorn) is never studied."""
    k = _kind(kind)
    if not k or family_of(k) is None:
        return False
    s = getattr(player, 'studied_monster_ids', None)
    if not isinstance(s, set):
        s = set(s or ())
        player.studied_monster_ids = s
    if k in s:
        return False
    s.add(k)
    return True


def _told(player) -> dict:
    t = getattr(player, 'family_tiers_told', None)
    if not isinstance(t, dict):
        t = {}
        player.family_tiers_told = t
    return t


def circles() -> dict:
    return data().get('circles', {}) or {}


def circle_complete(player, cid) -> bool:
    """Calculated from the tiers, never stored: `need` of the circle's
    families at `tier` or more."""
    c = circles().get(cid) or {}
    t = tiers(player)
    need_tier = int(c.get('tier', 3))
    got = sum(1 for f in c.get('families', ()) if t.get(f, 0) >= need_tier)
    return got >= int(c.get('need', len(c.get('families', ()))))


def complete_circles(player) -> list:
    return [cid for cid in circles() if circle_complete(player, cid)]


def is_loremaster(player) -> bool:
    lm = data().get('loremaster') or {}
    need_tier = int(lm.get('tier', 5))
    t = tiers(player)
    return sum(1 for v in t.values() if v >= need_tier) >= int(lm.get('families_at_tier', 5))


def news(player) -> list:
    """What the hero has newly reached since he was last told, in order,
    each only once: ('tier', fid, t) for every tier passed, then
    ('circle', cid, None), then ('loremaster', None, None). Marks them told
    in Player.family_tiers_told."""
    told = _told(player)
    out = []
    for fid, t in sorted(tiers(player).items()):
        was = int(told.get(fid, 0) or 0)
        for step in range(was + 1, t + 1):
            out.append(('tier', fid, step))
        if t > was:
            told[fid] = t
    for cid in complete_circles(player):
        key = f'circle:{cid}'
        if not told.get(key):
            told[key] = 1
            out.append(('circle', cid, None))
    if is_loremaster(player) and not told.get('loremaster'):
        told['loremaster'] = 1
        out.append(('loremaster', None, None))
    return out


def mark_all_told(player) -> None:
    """Everything reached so far counts as told (old saves, head starts),
    so loading a game never floods the screen with popups."""
    told = _told(player)
    for fid, t in tiers(player).items():
        told[fid] = max(int(told.get(fid, 0) or 0), t)
    for cid in complete_circles(player):
        told[f'circle:{cid}'] = 1
    if is_loremaster(player):
        told['loremaster'] = 1


def grant_head_start(player, mapping) -> None:
    """A secret build's unlabelled head start: {family id: tier}, tiers 1
    and 2 only (Recognise, Forewarned), never an edge. Told at once, so no
    message announces it."""
    if not mapping:
        return
    g = getattr(player, 'family_lore_grants', None)
    if not isinstance(g, dict):
        g = {}
        player.family_lore_grants = g
    for fid, t in dict(mapping).items():
        if fid in families():
            g[fid] = max(int(g.get(fid, 0) or 0), min(2, int(t)))
    mark_all_told(player)


def migrate_old_save(player) -> None:
    """Player.__setstate__: a save from before families. Every kind whose
    corpse it studied counts as studied (lore_known held exactly that,
    plus Thoth reveals, which the old game could not tell apart), and every
    tier reached is told at once (no popup flood)."""
    d = player.__dict__
    if not isinstance(d.get('studied_monster_ids'), set):
        d['studied_monster_ids'] = set(d.get('studied_monster_ids') or
                                       d.get('lore_known_monster_ids') or ())
        fresh = True
    else:
        fresh = False
    if not isinstance(d.get('family_lore_grants'), dict):
        d['family_lore_grants'] = {}
    if not isinstance(d.get('family_tiers_told'), dict):
        d['family_tiers_told'] = {}
        fresh = True
    if fresh:
        try:
            mark_all_told(player)
        except (OSError, ValueError):
            pass


# ---------------------------------------------------------------------------
# Text built from data
# ---------------------------------------------------------------------------
def _fmt(template: str, fid) -> str:
    k = kin(fid)
    return (template or '').replace('{kin}', k).replace('{KIN}', k.upper())


def tier_message(fid, t: int) -> str:
    msgs = data().get('tier_messages', ()) or ()
    return _fmt(msgs[t - 1], fid) if 1 <= t <= len(msgs) else ''


def popup_title(fid, t: int) -> str:
    titles = data().get('popup_titles', ()) or ()
    return _fmt(titles[t - 1], fid) if 1 <= t <= len(titles) else ''


def tier_chronicle(fid, t: int) -> str:
    lines = data().get('tier_chronicle', ()) or ()
    return _fmt(lines[t - 1], fid) if 1 <= t <= len(lines) else ''


def tier_entry(fid, t: int) -> dict:
    tiers_ = family(fid).get('tiers', ())
    return tiers_[t - 1] if 1 <= t <= len(tiers_) else {}


def abilities(fid, upto: int) -> list:
    """The ability dicts of tiers 1..upto, in order."""
    out = []
    for i, entry in enumerate(family(fid).get('tiers', ()), start=1):
        if i > upto:
            break
        out.extend(entry.get('abilities', ()) or ())
    return out


def field_notes(fid, upto: int) -> list:
    """(tier, note) for every unlocked tier with a written note (an empty
    note, the placeholder, is hidden)."""
    out = []
    for i, entry in enumerate(family(fid).get('tiers', ()), start=1):
        if i > upto:
            break
        note = str(entry.get('field_note', '') or '').strip()
        if note:
            out.append((i, note))
    return out


def forewarned_line(fid) -> str:
    for a in abilities(fid, max_tier(fid)):
        if a.get('effect') == 'forewarned':
            return str((a.get('params') or {}).get('line', '') or '')
    return ''


def arrival_lines(player, monsters, *, concealed, is_ally, limit: int = 3) -> list:
    """The Forewarned lines for a floor just reached: one per family at tier
    2 or more with a member here, never counting a concealed member (an
    invisible one, an ambusher not yet sprung, a disguised mimic or the
    Hellmouth) or an ally. At most `limit` lines; past that, the first
    `limit - 1` and one combined line."""
    t = tiers(player)
    present = []
    for m in monsters or ():
        if not getattr(m, 'alive', False):
            continue
        fid = family_of(m)
        if not fid or t.get(fid, 0) < 2 or fid in present:
            continue
        try:
            if concealed(m) or is_ally(m):
                continue
        except Exception:
            continue
        present.append(fid)
    lines = [forewarned_line(f) for f in present if forewarned_line(f)]
    if len(lines) <= limit:
        return lines
    rest = [short_name(f) for f in present[limit - 1:]]
    combined = ("You sense more on this floor: "
                + (', '.join(rest[:-1]) + ' and ' + rest[-1] if len(rest) > 1 else rest[0]) + '.')
    return lines[:limit - 1] + [combined]


def lore_rows(player) -> list:
    """The @ sheet's Monster Lore rows: (family short name, tier name,
    [technique names past Forewarned]) for every family at tier 1 or more,
    the highest tiers first."""
    rows = []
    for fid, t in sorted(tiers(player).items(), key=lambda kv: (-kv[1], short_name(kv[0]))):
        names = [a.get('name', '') for a in abilities(fid, t)
                 if a.get('effect') not in ('recognise', 'forewarned')]
        rows.append((short_name(fid), tier_name(fid, t), names))
    return rows


def summary(player) -> dict:
    """Counts for Your Story and the Discoveries page."""
    t = tiers(player)
    top = {fid: v for fid, v in t.items() if v >= max_tier(fid)}
    return {'known': len(t), 'mastered': len(top), 'circles': complete_circles(player),
            'loremaster': is_loremaster(player)}
