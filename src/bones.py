"""
Bones file system -- when a player dies, their ghost and cursed gear
can appear on that dungeon level in a future run.

At most 3 bones files are kept (oldest evicted when a 4th is saved).
On level generation, there is a 50% chance to check for a matching
bones file; if found, a ghost + cursed loot are spawned.
"""
import json
import os
import random
import copy

from paths import save_dir

_BONES_DIR_NAME = 'bones'
_MAX_BONES = 3


def _bones_dir() -> str:
    d = os.path.join(save_dir(), _BONES_DIR_NAME)
    os.makedirs(d, exist_ok=True)
    return d


def save_bones(player_name: str, dungeon_level: int, defeat_reason: str,
               player, player_gold: int):
    """Save a bones file when the player dies.  Keeps at most _MAX_BONES files."""
    equipped = player.get_equipped_items()
    # Kilt of the Pharaoh (royal_burial): preserve ONE possession on death.
    # Mark the first equipped item as 'preserved'; load_bones-side spawning
    # leaves preserved items uncursed.
    has_royal_burial = any(
        getattr(it, 'royal_burial', False)
        for it in (equipped.values() if isinstance(equipped, dict) else [])
        if it is not None
    )
    # Collect up to 5 best equipped items (non-None)
    gear = []
    preserved_marked = False
    for slot, item in equipped.items():
        if item is None:
            continue
        entry = {
            'id': getattr(item, 'id', 'unknown'),
            'name': getattr(item, 'name', 'unknown item'),
            'item_class': getattr(item, 'item_class', 'misc'),
            'slot': slot,
        }
        # Preserve the first non-kilt item (so the kilt itself doesn't always win).
        if has_royal_burial and not preserved_marked and \
                getattr(item, 'id', '') != 'kilt_of_the_pharaoh':
            entry['preserved'] = True
            preserved_marked = True
        gear.append(entry)
        if len(gear) >= 5:
            break

    bones = {
        'player_name': player_name,
        'dungeon_level': dungeon_level,
        'defeat_reason': defeat_reason,
        'player_level': getattr(player, 'level', 1),
        'max_hp': player.max_hp,
        'gear': gear,
        'gold': min(player_gold, 500),  # cap ghost gold to avoid windfalls
    }

    bd = _bones_dir()
    path = os.path.join(bd, f'bones_L{dungeon_level}.json')
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(bones, f, indent=2)
    except OSError:
        return  # silently fail if can't write

    # Evict oldest if over cap
    _evict_oldest(bd)


def _evict_oldest(bd: str):
    files = sorted(
        [f for f in os.listdir(bd) if f.startswith('bones_') and f.endswith('.json')],
        key=lambda f: os.path.getmtime(os.path.join(bd, f))
    )
    while len(files) > _MAX_BONES:
        oldest = files.pop(0)
        try:
            os.remove(os.path.join(bd, oldest))
        except OSError:
            pass


def load_bones(dungeon_level: int):
    """Check for bones on this level.  50% chance to even look.
    Returns the bones dict if found, else None."""
    # Check file existence FIRST — no point burning a 50% roll on a level
    # that has no bones file at all. Only levels with real bones need the
    # rarity gate to prevent the ghost from feeling routine.
    # Offline tooling and tests generate floors by the thousand; they must
    # never consume a real ghost (set PQ_NO_BONES=1).
    if os.environ.get('PQ_NO_BONES'):
        return None
    path = os.path.join(_bones_dir(), f'bones_L{dungeon_level}.json')
    if not os.path.exists(path):
        return None
    if random.random() > 0.50:
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            bones = json.load(f)
        # Consume the bones file so this ghost only appears once
        os.remove(path)
        return bones
    except (OSError, json.JSONDecodeError):
        # Corrupt bones file -- remove so it doesn't permanently occupy a slot
        # under the _MAX_BONES cap.
        try:
            os.remove(path)
        except OSError:
            pass
        return None


def spawn_ghost(bones: dict, dungeon, monsters: list, ground_items: list):
    """Spawn a ghost monster and its cursed gear from a bones file."""
    from monster import Monster

    name = bones.get('player_name', 'Unknown')

    # The ghost is as strong as the floor it died on. It used to scale on a
    # player "level" that does not exist, so it was 1d4+1 at every depth.
    from floor_curve import target_hp, target_dmg, dice_for_average
    floor = int(bones.get('dungeon_level', 1) or 1)
    ghost_hp = max(20, int(round(1.5 * target_hp(floor))))
    ghost_dmg = dice_for_average(1.2 * target_dmg(floor))

    ghost_defn = {
        'id': 'player_ghost',
        'name': f'Ghost of {name}',
        'symbol': 'G',
        'color': [180, 180, 255],
        'hp': ghost_hp,
        'ai_pattern': 'aggressive',
        'speed': 8,
        'attacks': [
            {'name': 'Spectral Touch', 'damage': ghost_dmg, 'type': 'drain'},
        ],
        'resistances': ['pierce', 'cold', 'poison'],
        'weaknesses': ['holy', 'fire'],
        'tags': ['undead'],
        'min_level': floor,
        'peak_floor': floor,
        'max_level': 100,
        'harvest_tier': 0,
        'harvest_threshold': 99,
        'lore': (f'{name} carried the same errand down these stairs and did '
                 f'not carry it back.'),
        'treasure': {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 1},
    }

    # Place ghost in a non-start room. Must not co-locate with a monster
    # already placed this turn (mini-boss, seal demon, den extras, etc.);
    # ghost is spawned AFTER those paths from level_manager.generate.
    rooms = dungeon.rooms
    if len(rooms) < 2:
        return
    occupied = {(m.x, m.y) for m in monsters if m.alive}
    ghost_pos = None
    # Try up to a few random non-start rooms before giving up.
    room = None
    for _ in range(min(5, len(rooms) - 1)):
        candidate_room = random.choice(rooms[1:])
        for tx, ty in candidate_room.inner_tiles():
            if dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                ghost_pos = (tx, ty)
                room = candidate_room
                break
        if ghost_pos is not None:
            break
    if ghost_pos is None:
        # Every candidate tile was occupied — silently skip this ghost
        # rather than overwrite another monster on the same tile.
        return
    gx, gy = ghost_pos

    ghost = Monster(ghost_defn, gx, gy)
    monsters.append(ghost)
    dungeon.bones_ghost_name = f'Ghost of {name}'

    # Place cursed gear around the ghost
    gear_items = bones.get('gear', [])
    gold = bones.get('gold', 0)

    _place_cursed_gear(gear_items, gold, room, dungeon, ground_items)


def _place_cursed_gear(gear_list: list, gold: int, room, dungeon, ground_items: list):
    """Place the dead player's gear as cursed items on the ground near the ghost."""
    from items import load_items

    # Load all item pools once
    item_pools = {}
    for cls in ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll', 'potion'):
        try:
            item_pools[cls] = {i.id: i for i in load_items(cls)}
        except Exception:
            pass

    tiles = list(room.inner_tiles())
    random.shuffle(tiles)
    tile_idx = 0
    # Track tiles that already carry a ground item so cursed gear doesn't
    # spawn on top of existing loot from `spawn_items` (or a prior bones drop).
    used_tiles = {(gi.x, gi.y) for gi in ground_items}

    for gear_entry in gear_list:
        item_id = gear_entry.get('id', '')
        item_class = gear_entry.get('item_class', '')

        # Try to find the item in our pools
        pool = item_pools.get(item_class, {})
        template = pool.get(item_id)
        if template is None:
            # Ordinary gear is composed ("iron_longsword" = material +
            # template) and is not in the item files, which now hold only
            # named uniques. Without this the ghost's ordinary weapon,
            # armor and shield all vanished from the bones pile.
            template = _recompose_gear(item_id, item_class)
        if template is None:
            continue

        item = copy.copy(template)
        # Royal Burial (Kilt of the Pharaoh): preserved items stay uncursed.
        if gear_entry.get('preserved'):
            item.buc = 'uncursed'
            item.buc_known = True  # the inscription is visible — "preserved by the Pharaoh"
        else:
            item.buc = 'cursed'
            item.buc_known = False

        # Place on a free tile
        while tile_idx < len(tiles):
            tx, ty = tiles[tile_idx]
            tile_idx += 1
            if dungeon.is_walkable(tx, ty) and (tx, ty) not in used_tiles:
                item.x, item.y = tx, ty
                ground_items.append(item)
                used_tiles.add((tx, ty))
                break

    # Drop gold pile if any — advance past any already-used tiles so the pile
    # doesn't land on the last-placed cursed item.
    if gold > 0:
        while tile_idx < len(tiles):
            tx, ty = tiles[tile_idx]
            tile_idx += 1
            if dungeon.is_walkable(tx, ty) and (tx, ty) not in used_tiles:
                from items import GoldPile
                ground_items.append(GoldPile(gold, tx, ty))
                break


def _recompose_gear(item_id: str, item_class: str):
    """Rebuild a composed weapon / armor / shield from its id
    ("<material>_<template>"), or return None if it does not parse."""
    try:
        from items import (load_materials, load_templates, instantiate_weapon,
                           instantiate_armor, instantiate_shield)
        spec = {
            'weapon': ('weapons', 'weapons', instantiate_weapon),
            'armor':  ('armor', 'armor', instantiate_armor),
            'shield': ('armor', 'shields', instantiate_shield),
        }.get(item_class)
        if spec is None:
            return None
        mat_cat, tpl_cat, build = spec
        templates = load_templates(tpl_cat)
        # Longest material id first: "cold_iron" must win over "cold".
        for mat_id in sorted(load_materials(mat_cat), key=len, reverse=True):
            prefix = mat_id + '_'
            if item_id.startswith(prefix) and item_id[len(prefix):] in templates:
                return build(item_id[len(prefix):], mat_id)
    except Exception:
        return None
    return None
