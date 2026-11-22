"""Forget: what a mind-eater took, pure (Brandon, 2026-11-22).

"Intellect devourer might make you Forget previously identified items or
monsters": on a failed Wisdom save it eats ONE identified kind of thing in
the pack, or ONE Bestiary page the hero earned. Kill it on that floor and
all it ate comes back; leave the floor and it is lost until learned again.

Never spells, stats, family tiers, the Philosopher's Shard, or anything a
mastered philosophy tier names again by itself. A page taken still counts
toward its family's tiers (family_lore.ever_studied).

The record is ``player._mind_eaten``, plain dicts saved with the hero. Each
copy of a forgotten thing carries what it knew of itself (``_eaten``), so
what comes back is what was taken, blessing and all.
"""
from __future__ import annotations

import uuid

import effect_rules

MARK = '_eaten'


def records(player) -> list:
    d = player.__dict__.get('_mind_eaten')
    if not isinstance(d, list):
        d = player.__dict__['_mind_eaten'] = []
    return d


def relearnable(kind: str) -> bool:
    """Others of the kind still walk the floors: a boss dies once, and a
    page of its could never be learned again."""
    import kind_data
    d = kind_data.defs().get(kind)
    return (isinstance(d, dict)
            and not any(d.get(f) for f in ('is_boss', 'is_mini_boss', 'is_seal_demon', 'quest_only'))
            and float(d.get('peak_weight', 0) or 0) > 0 and d.get('frequency', 3) != 0)


def page_candidates(player) -> list:
    """Kinds whose page he would lose: studied or opened, and not known all
    the same through the family's Lore tier (that is mastery's)."""
    import family_lore as FL
    earned = set(FL.studied(player)) | set(getattr(player, 'lore_known_monster_ids', None) or ())
    return sorted(k for k in earned
                  if relearnable(k) and FL.tier(player, FL.family_of(k)) < FL.full_lore_tier())


def item_candidates(player, forgettable) -> list:
    """One of each identified kind in the pack that he could forget."""
    import philosophy_mastery
    out = {}
    for it in getattr(player, 'inventory', None) or ():
        iid = str(getattr(it, 'id', '') or '')
        if iid and iid not in out and forgettable(it) and not philosophy_mastery.covers(it, player):
            out[iid] = it
    return list(out.values())


def eat_page(player, kind: str, by: str, name: str) -> dict:
    studied = getattr(player, 'studied_monster_ids', None)
    if not isinstance(studied, set):
        studied = player.studied_monster_ids = set(studied or ())
    opened = getattr(player, 'lore_known_monster_ids', None)
    if not isinstance(opened, set):
        opened = player.lore_known_monster_ids = set(opened or ())
    rec = {'what': 'page', 'by': by, 'id': kind, 'name': name,
           'studied': kind in studied, 'opened': kind in opened}
    studied.discard(kind)
    opened.discard(kind)
    if rec['studied']:
        player.__dict__.setdefault('forgotten_pages', set()).add(kind)
    records(player).append(rec)
    return rec


def eat_item(player, item, by: str, name: str, copies: list) -> dict:
    """Remember what the kind and every copy knew. The caller forgets the
    kind right after (Game._forget_kind)."""
    from items import form_id, type_class
    try:
        cls = type_class(item)
    except Exception:
        cls = None
    fid = form_id(item)
    iid = str(getattr(item, 'id', '') or '')
    key = uuid.uuid4().hex
    rec = {'what': 'item', 'by': by, 'id': iid, 'name': name, 'cls': cls, 'form': fid, 'key': key,
           'knew_id': iid in (getattr(player, 'known_item_ids', None) or ()),
           'knew_cls': bool(cls) and cls in (getattr(player, 'known_class_ids', None) or ()),
           'knew_form': bool(fid) and fid in (getattr(player, 'known_forms', None) or ())}
    for it in copies:
        marks = dict(it.__dict__.get(MARK) or {})
        marks[key] = (getattr(it, 'id_level', 0), getattr(it, 'buc_known', None))
        it.__dict__[MARK] = marks
    records(player).append(rec)
    return rec


def give_back(player, rec: dict, copies=()) -> None:
    if rec in records(player):
        records(player).remove(rec)
    if rec['what'] == 'page':
        if rec.get('studied'):
            player.studied_monster_ids.add(rec['id'])
            player.__dict__.setdefault('forgotten_pages', set()).discard(rec['id'])
        if rec.get('opened'):
            player.lore_known_monster_ids.add(rec['id'])
        return
    for flag, attr, field in (('knew_id', 'known_item_ids', 'id'), ('knew_cls', 'known_class_ids', 'cls'),
                              ('knew_form', 'known_forms', 'form')):
        if rec.get(flag):
            s = getattr(player, attr, None)
            if not isinstance(s, set):
                s = set(s or ())
                setattr(player, attr, s)
            s.add(rec[field])
    for it in copies:
        marks = it.__dict__.get(MARK) or {}
        if rec['key'] not in marks:
            continue
        level, buc = marks[rec['key']]
        if hasattr(it, 'id_level'):
            it.id_level = max(int(getattr(it, 'id_level', 0) or 0), int(level or 0))
        if buc and hasattr(it, 'buc_known'):
            it.buc_known = buc
        left = {k: v for k, v in marks.items() if k != rec['key']}
        if left:
            it.__dict__[MARK] = left
        else:
            it.__dict__.pop(MARK, None)


def owed_by(player, monster) -> list:
    return [r for r in records(player) if effect_rules.is_source(monster, r.get('by'))]


def lose_all(player) -> list:
    """The floor is left: what was eaten is gone until learned again.
    Returns what was lost, for the line."""
    gone = list(records(player))
    del records(player)[:]
    return gone
