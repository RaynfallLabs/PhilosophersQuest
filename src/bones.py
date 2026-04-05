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
    # Collect up to 5 best equipped items (non-None)
    gear = []
    for slot, item in equipped.items():
        if item is None:
            continue
        gear.append({
            'id': getattr(item, 'id', 'unknown'),
            'name': getattr(item, 'name', 'unknown item'),
            'item_class': getattr(item, 'item_class', 'misc'),
            'slot': slot,
        })
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
    if random.random() > 0.50:
        return None
    path = os.path.join(_bones_dir(), f'bones_L{dungeon_level}.json')
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            bones = json.load(f)
        # Consume the bones file so this ghost only appears once
        os.remove(path)
        return bones
    except (OSError, json.JSONDecodeError):
        return None


def spawn_ghost(bones: dict, dungeon, monsters: list, ground_items: list):
    """Spawn a ghost monster and its cursed gear from a bones file."""
    from monster import Monster

    name = bones.get('player_name', 'Unknown')
    plevel = bones.get('player_level', 1)
    max_hp = bones.get('max_hp', 50)
    reason = bones.get('defeat_reason', 'died')

    # Scale ghost HP: base on dead player's max HP, capped reasonably
    ghost_hp = max(20, min(max_hp // 2, 300))

    ghost_defn = {
        'id': 'player_ghost',
        'name': f'Ghost of {name}',
        'symbol': 'G',
        'color': [180, 180, 255],
        'hp': ghost_hp,
        'ai_pattern': 'aggressive',
        'speed': 8,
        'attacks': [
            {'name': 'spectral touch', 'damage': f'{max(1, plevel // 5)}d4+{max(1, plevel // 10)}',
             'type': 'drain'},
        ],
        'resistances': ['physical', 'cold', 'poison'],
        'weaknesses': ['holy', 'fire'],
        'tags': ['undead'],
        'min_level': 1,
        'max_level': 100,
        'harvest_tier': 0,
        'harvest_threshold': 99,
        'lore': f'The restless spirit of {name}, who {reason} on this floor.',
        'treasure': {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 1},
    }

    # Place ghost in a non-start room
    rooms = dungeon.rooms
    if len(rooms) < 2:
        return
    room = random.choice(rooms[1:])
    cx, cy = room.center
    # Find a walkable tile near room center
    gx, gy = cx, cy
    for tx, ty in room.inner_tiles():
        if dungeon.is_walkable(tx, ty):
            gx, gy = tx, ty
            break

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

    for gear_entry in gear_list:
        item_id = gear_entry.get('id', '')
        item_class = gear_entry.get('item_class', '')

        # Try to find the item in our pools
        pool = item_pools.get(item_class, {})
        template = pool.get(item_id)
        if template is None:
            continue

        item = copy.copy(template)
        item.buc = 'cursed'
        item.buc_known = False

        # Place on a free tile
        placed = False
        while tile_idx < len(tiles):
            tx, ty = tiles[tile_idx]
            tile_idx += 1
            if dungeon.is_walkable(tx, ty):
                item.x, item.y = tx, ty
                ground_items.append(item)
                placed = True
                break

    # Drop gold pile if any
    if gold > 0 and tile_idx < len(tiles):
        from items import GoldPile
        tx, ty = tiles[tile_idx]
        ground_items.append(GoldPile(gold, tx, ty))
