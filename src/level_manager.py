import copy
import random

# Philosopher's Stone spawns on this level
STONE_LEVEL = 100


class LevelManager:
    def __init__(self):
        self._saved: dict = {}          # level_num -> (dungeon, monsters, items)
        self.max_level_reached: int = 1
        self.monsters_killed: int   = 0

    def save(self, level_num: int, dungeon, monsters: list, ground_items: list):
        """Persist current level state so it can be restored later."""
        self._saved[level_num] = (dungeon, list(monsters), list(ground_items))

    def load(self, level_num: int):
        """Return (dungeon, monsters, items) for a saved level, or None."""
        return self._saved.get(level_num)

    def has_visited(self, level_num: int) -> bool:
        return level_num in self._saved

    def generate(self, level_num: int):
        """Create a fresh level, spawn monsters/items, save, and return it."""
        from dungeon import generate_dungeon, spawn_monsters, spawn_items

        dungeon = generate_dungeon(80, 50, level_num)

        # Monster count scales with depth (higher ceiling for deep levels)
        min_m = min(3 + (level_num - 1), 12)
        max_m = min(5 + level_num, 18)
        monsters = spawn_monsters(dungeon.rooms, level_num, dungeon, min_m, max_m)

        items = spawn_items(dungeon.rooms, level_num, dungeon)

        if level_num == STONE_LEVEL:
            stone = _place_stone(dungeon, items)
            if stone:
                items.append(stone)

        self.max_level_reached = max(self.max_level_reached, level_num)
        return dungeon, monsters, items


def _place_stone(dungeon, existing_items: list):
    """Place the Philosopher's Stone in the last room of the dungeon."""
    from items import load_items
    try:
        artifacts = load_items('artifact')
    except (FileNotFoundError, KeyError):
        return None

    template = next((a for a in artifacts if a.id == 'philosophers_stone'), None)
    if template is None:
        return None

    existing_pos = {(i.x, i.y) for i in existing_items}
    # Prefer the last room (deepest), fall back to any room
    for room in reversed(dungeon.rooms):
        tiles = list(room.inner_tiles())
        random.shuffle(tiles)
        for tx, ty in tiles:
            if dungeon.is_walkable(tx, ty) and (tx, ty) not in existing_pos:
                inst = copy.copy(template)
                inst.x, inst.y = tx, ty
                return inst
    return None
