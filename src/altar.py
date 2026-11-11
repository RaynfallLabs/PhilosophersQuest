"""The altar rite: an offering, one theology chain, curses lifted and then
blessings given (Brandon, 2026-11-07, bug bash 3.3.2).

On an ordinary altar the prayer key opens the altar instead of the prayer
menu. Every choice there costs one offering (``economy.altar_offering``,
the same price whatever is asked, rising with the floor) and none of them
sets the prayer cooldown:

  * The altar rite: the theology escalator chain (max 5). Each link mends
    one thing: every CURSE is lifted first (worn pieces before the pack),
    then the links left BLESS, in the order below. A chain of 0 keeps the
    offering and mends nothing.
  * Either ordinary prayer (Lord, Have Mercy / Michael, Guide My Hand),
    answered as at any altar, without the cooldown.

Before this, Mercy's fourth link blessed random pack items of any kind: a
lockpick, a ration, a spellbook, none of which a blessing changes.

Pure rules: no pygame, no Game. ``game_divine`` pays, kneels, runs the quiz
and says what happened.

What a blessing does, as the code reads it (so what may be blessed):
  * weapons: +1 damage, and the blow counts as holy (combat.py);
  * armour, shields, rings, amulets, belts: +1 AC while worn (player.py);
  * potions: healing and buffs x1.5, harm blocked (food_system.drink_potion),
    except the kinds in ``POTION_EFFECTS_BLESSING_IGNORES``;
  * scrolls: a stronger reading (game_magic._apply_scroll_effect), except
    the kinds in ``SCROLL_EFFECTS_BLESSING_IGNORES``.
Never: wands (a wand's blessing is its extra charge, given only when it is
made), food, corpses, ingredients, ammo, lockpicks, containers, spellbooks,
relics, treasure, Soul Spheres. An unidentified potion or scroll is always
eligible: leaving it out would tell the hero it is one of the kinds a
blessing cannot help.
"""
from __future__ import annotations

MAX_MENDED = 5          # the chain's cap: five links, five things mended

# Potion and scroll effects whose handler never reads the blessing. Every
# effect in data/items/potion.json and scroll.json must be in this set or
# in the matching *_BLESSING_HELPS set (tests/test_bugbash_332_altar.py).
POTION_EFFECTS_BLESSING_IGNORES = frozenset({
    'brilliance_mp', 'cure_all', 'cure_disease', 'cure_poison', 'fafnirs_blood',
    'gain_level', 'mimir_wisdom', 'restore_mp', 'restore_str', 'teleport',
})
POTION_EFFECTS_BLESSING_HELPS = frozenset({
    'blindness', 'cold_resist', 'confusion', 'drain_con', 'drain_int', 'drain_str',
    'drain_wis', 'extra_heal', 'fear', 'fire_resist', 'full_heal', 'fumbling',
    'hallucination', 'haste', 'heal', 'heroism', 'invisibility', 'levitation',
    'paralysis', 'poison', 'regeneration', 'restore_sp', 'see_invisible',
    'shock_resist', 'sickness', 'sleep', 'slow', 'weakness',
})
SCROLL_EFFECTS_BLESSING_IGNORES = frozenset({
    'annihilate', 'boss_reward', 'charging', 'confuse_monsters', 'dead_sea_map',
    'earth', 'genocide', 'great_power', 'haste_self', 'mapping', 'sleep_monsters',
    'teleport_self', 'time_stop_scroll',
})
SCROLL_EFFECTS_BLESSING_HELPS = frozenset({
    'enchant_accessory', 'enchant_armor', 'enchant_item', 'enchant_weapon',
    'full_light', 'heal', 'identify', 'protection', 'remove_curse',
})

# Gear a blessing always improves (worn or wielded).
_GEAR_CLASSES = ('weapon', 'armor', 'shield', 'accessory')

# A curse that is the point of the thing: the Duck of Doom answers to
# patience, not to a scroll (game_magic remove_curse) and not to an altar.
CURSE_KEEPS = frozenset({'duck_of_doom'})


def _kind_known(item, player) -> bool:
    try:
        from items import is_fully_known
        return bool(is_fully_known(item, player))
    except Exception:
        return False


def _buc_known(item, player) -> bool:
    try:
        from items import buc_known_to
        return bool(buc_known_to(item, player))
    except Exception:
        return bool(getattr(item, 'buc_known', False))


def blessing_helps(item, player=None) -> bool:
    """Would a blessing change anything about ``item``, as far as the hero
    can tell? (A potion or scroll of a kind he has not identified: yes.)"""
    if item is None or not hasattr(item, 'buc'):
        return False
    # (``can_be_cursed: false`` is NOT "takes no blessing": holy relics and
    # most unique armour are never found cursed, and a blessing still adds
    # its AC. Treasure takes none, and is not a kind listed below.)
    try:
        from pet_system import is_soul_sphere
        if is_soul_sphere(item):
            return False
    except Exception:
        pass
    cls = str(getattr(item, 'item_class', '') or '')
    if cls in _GEAR_CLASSES:
        return True
    if cls in ('potion', 'scroll'):
        if not _kind_known(item, player):
            return True
        effect = str(getattr(item, 'effect', '') or '')
        ignores = (POTION_EFFECTS_BLESSING_IGNORES if cls == 'potion'
                   else SCROLL_EFFECTS_BLESSING_IGNORES)
        return effect not in ignores
    return False


def _unique(seq) -> list:
    seen, out = set(), []
    for it in seq:
        if it is None or id(it) in seen:
            continue
        seen.add(id(it))
        out.append(it)
    return out


def curse_order(equipped, inventory) -> list:
    """Every cursed thing the hero has, worn first (the ones welded on),
    then the pack in its order. The Duck of Doom keeps its curse."""
    return [it for it in _unique(list(equipped) + list(inventory))
            if getattr(it, 'buc', 'uncursed') == 'cursed'
            and getattr(it, 'id', '') not in CURSE_KEEPS]


def _consumable_rank(item, player) -> float:
    """Better first among potions and scrolls: a known kind by its worth,
    an unknown one as its class's common band (1.0), so the order never
    tells the hero more than he knows."""
    if not _kind_known(item, player):
        return 1.0
    try:
        from economy import item_worth
        return float(item_worth(item))
    except Exception:
        return 1.0


def bless_order(equipped, inventory, player=None) -> list:
    """What the links left after the curses bless, best first: what the
    hero wields and wears (in slot order: weapon, ranged weapon, shield,
    armour, rings, amulet, belt), then potions and scrolls (the better
    first), then spare gear in the pack. Only things a blessing helps, and
    none the hero knows to be blessed already."""
    def wanted(it):
        if not blessing_helps(it, player):
            return False
        return not (getattr(it, 'buc', '') == 'blessed' and _buc_known(it, player))

    worn = [it for it in _unique(equipped) if wanted(it)]
    worn_ids = {id(it) for it in worn} | {id(it) for it in equipped if it is not None}
    pack = [it for it in _unique(inventory) if id(it) not in worn_ids and wanted(it)]
    consumables = [it for it in pack
                   if str(getattr(it, 'item_class', '')) in ('potion', 'scroll')]
    consumables = [it for _, _, it in sorted(
        ((-_consumable_rank(it, player), i, it) for i, it in enumerate(consumables)),
        key=lambda t: (t[0], t[1]))]
    spare = [it for it in pack
             if str(getattr(it, 'item_class', '')) in _GEAR_CLASSES]
    return worn + consumables + spare


def rite(chain: int, equipped, inventory, player=None) -> list[tuple[str, object]]:
    """What a chain of ``chain`` links does, in order, as (what, item):
    'lift' a curse, 'bless' a thing, or 'already' (a thing the hero did not
    know was blessed: it is shown so, and costs no link). Nothing is
    changed here; the caller applies it."""
    links = max(0, min(int(chain or 0), MAX_MENDED))
    out: list[tuple[str, object]] = []
    for it in curse_order(equipped, inventory):
        if links <= 0:
            return out
        out.append(('lift', it))
        links -= 1
    for it in bless_order(equipped, inventory, player):
        if links <= 0:
            break
        if getattr(it, 'buc', '') == 'blessed':
            out.append(('already', it))
            continue
        out.append(('bless', it))
        links -= 1
    return out


def apply(actions) -> None:
    """Carry out ``rite``'s actions on the items themselves."""
    for what, it in actions:
        if what == 'lift':
            it.buc = 'uncursed'
        elif what == 'bless':
            it.buc = 'blessed'
        it.buc_known = True
