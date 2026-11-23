"""Known by Hand: a kind of gear the hero has put on once goes on again with
no quiz (winning-build plan 3.4, 2026-11-13).

The first time the hero passes the equip quiz for a KIND, every copy of that
kind equips with no quiz, whatever its plus, enchantment level or blessing.
Brandon's example: a rusty iron breastplate teaches it, so the blessed iron
breastplate found later goes straight on; a mithril breastplate is a new
kind and asks its own quiz.

  * The kind is the item's id. For common gear that is exactly material +
    template ("iron_breastplate"); a named unique's id is itself, so a
    unique is one quiz.
  * A ring or amulet KIND (rings.py: "ring_of_protection" at levels 1-10)
    is known by kind AND tier (Brandon, 2026-11-16: "a deeper level of a
    known kind asks its own quiz"). The hero remembers the highest tier he
    has put on (Player.by_hand_ring_tiers): a ring of that tier or lower
    goes on with no quiz, a higher one asks its own once. The tier is the
    one its quiz is set at (gear.tier_for_level: a lesser and a greater
    form share one), so a Ring of Greater Protection V on floor 95 asks
    though a Ring of Protection I was worn on floor 2. Belts have no kinds
    today: each is a named one, one quiz.
  * A chain-equip legend (chain_equip.py) remembers the BEST chain reached
    on it. Put back on, it goes on at that tier with no quiz, and the hero
    may take the quiz again to climb (the best is kept).
  * The hero learns it, for this run (Player.known_by_hand, saved; plan
    decision 4). An old save counts what is worn as known, a ring at its
    own tier (an old save's ring kind known but not worn: its first tier,
    as it went on at least that once).
  * A cursed piece still refuses to come off: knowing how a thing goes on
    says nothing of getting it off again.

This is a skill the hero has, not a mastery system: it is one set of kinds,
and it never changes a number (docs/systems/README.md).

Pure rules over the player's two stores; no pygame, no game state.
"""
from __future__ import annotations

MARK = "Known by Hand"
FIRES_LINE = "You have worn one of these before. On it goes."
FIRES_LINE_UNIQUE = "You have worn it before. On it goes."


def kind_key(item) -> str:
    """The kind an item is for Known by Hand: its id ('' for none)."""
    return str(getattr(item, 'id', '') or '')


def _store(player) -> set:
    s = player.__dict__.get('known_by_hand')
    if not isinstance(s, set):
        s = set(s or ())
        player.__dict__['known_by_hand'] = s
    return s


def _tiers(player) -> dict:
    d = player.__dict__.get('by_hand_tiers')
    if not isinstance(d, dict):
        d = dict(d or {})
        player.__dict__['by_hand_tiers'] = d
    return d


def _ring_tiers(player) -> dict:
    d = player.__dict__.get('by_hand_ring_tiers')
    if not isinstance(d, dict):
        d = dict(d or {})
        player.__dict__['by_hand_ring_tiers'] = d
    return d


def levelled(item) -> bool:
    """A ring or amulet KIND at a level (rings.py): known by kind and tier.
    A named ring, amulet or belt is not (its id is the kind: one quiz)."""
    if item is None or not str(getattr(item, 'kind', '') or ''):
        return False
    if int(getattr(item, 'ench_level', 0) or 0) <= 0:
        return False
    if getattr(item, 'item_class', '') != 'accessory' and type(item).__name__ != 'Accessory':
        return False
    import rings
    return rings.kind_of(item) is not None


def ring_tier(item) -> int:
    """The tier of a kind ring's level, the tier its quiz is set at (a
    lesser and a greater form share one)."""
    import gear
    return gear.tier_for_level(int(getattr(item, 'ench_level', 0) or 0))


def known_ring_tier(player, item) -> int:
    """The highest tier of this ring kind the hero has put on (0: none)."""
    if player is None or item is None or kind_key(item) not in _store(player):
        return 0
    return max(0, min(5, int(_ring_tiers(player).get(kind_key(item), 0) or 0)))


def asks_quiz(item) -> bool:
    """Does putting this on ask a quiz at all? Armour, shields and worn
    rings / amulets / belts do; weapons and carried charms never did, and a
    no-quiz trap (threshold 0, the Duck of Doom) does not."""
    cls = str(getattr(item, 'item_class', '') or '')
    if not cls:
        cls = {'Armor': 'armor', 'Shield': 'shield',
               'Accessory': 'accessory'}.get(type(item).__name__, cls)
    if cls not in ('armor', 'shield', 'accessory'):
        return False
    if cls == 'accessory' and getattr(item, 'slot', '') == 'none':
        return False
    from chain_equip import is_chain_equip
    if is_chain_equip(item):
        return True
    return int(getattr(item, 'equip_threshold', 1) or 0) > 0


def knows(player, item) -> bool:
    """Has the hero put this kind on before (no quiz now)? A ring kind: at
    this tier or a higher one."""
    if player is None or item is None:
        return False
    key = kind_key(item)
    if not key:
        return False
    from chain_equip import is_chain_equip
    if is_chain_equip(item):
        return best_tier(player, item) > 0
    if levelled(item):
        return ring_tier(item) <= known_ring_tier(player, item)
    return key in _store(player)


def best_tier(player, item) -> int:
    """The best chain reached on a chain-equip legend (0: never worn)."""
    if player is None or item is None:
        return 0
    return max(0, min(5, int(_tiers(player).get(kind_key(item), 0) or 0)))


def learn(player, item, tier: int = 0) -> bool:
    """The hero has put this kind on. ``tier``: the chain reached on a
    chain-equip legend (the best is kept). True when it is newly known."""
    if player is None or item is None:
        return False
    key = kind_key(item)
    if not key:
        return False
    new = not knows(player, item)
    from chain_equip import is_chain_equip
    if is_chain_equip(item):
        t = max(0, min(5, int(tier or 0)))
        if t > 0:
            tiers = _tiers(player)
            tiers[key] = max(int(tiers.get(key, 0) or 0), t)
    elif levelled(item):
        # The highest tier of the kind he has put on (a lower one after a
        # higher keeps the higher).
        rt = _ring_tiers(player)
        rt[key] = max(int(rt.get(key, 0) or 0), ring_tier(item))
    _store(player).add(key)
    return new


def mark_for(player, item) -> str:
    """The Kit / @ / equip-menu mark for a wearable the hero knows, else ''."""
    if not asks_quiz(item) or not knows(player, item):
        return ''
    return MARK


def fires_line(item, player=None) -> str:
    """The line said when a known kind goes on with no quiz. With the hero,
    said the first time for each kind only, '' after (said_once.py; the
    equip menus show the mark every time)."""
    text = FIRES_LINE_UNIQUE if getattr(item, 'is_unique', False) else FIRES_LINE
    if player is None:
        return text
    import said_once
    return said_once.line(player, 'by_hand', kind_key(item), text)


def seed_from_worn(player) -> None:
    """An old save (from before Known by Hand): what the hero wears now, he
    has put on, so it counts as known (a worn legend at its attuned tier, a
    worn ring kind at its own tier)."""
    for it in player.worn_items():
        if asks_quiz(it):
            learn(player, it, int(getattr(it, 'achieved_tier', 0) or 0))


def _ring_kind_ids() -> dict:
    """{item id: ring kind} for every ring and amulet kind in the data
    ("ring_of_protection": "protection")."""
    import json
    from paths import data_path
    try:
        with open(data_path('data', 'items', 'accessory.json'), encoding='utf-8') as f:
            raw = json.load(f)
    except (OSError, ValueError):
        return {}
    return {k: v['kind'] for k, v in raw.items() if isinstance(v, dict) and v.get('kind')}


def migrate_ring_tiers(player) -> None:
    """A save from before ring kinds were known by tier (2026-11-16). What
    he wears counts as known at its own tier; a ring kind he knew but does
    not wear, at the kind's first tier (it went on at least once, and its
    level was never kept)."""
    import gear
    import rings
    store = _store(player)
    rt = _ring_tiers(player)
    for it in player.worn_items():
        if levelled(it) and asks_quiz(it):
            learn(player, it)
    ids = None
    for key in list(store):
        if key in rt:
            continue
        if ids is None:
            ids = _ring_kind_ids()
        kind = rings.get(ids.get(key, ''))
        if kind:
            rt[key] = gear.tier_for_level(rings.first_level(kind))
