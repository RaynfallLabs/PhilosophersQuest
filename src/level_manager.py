import copy
import random

# Philosopher's Stone spawns on this level
STONE_LEVEL = 100


class LevelManager:
    def __init__(self):
        self._saved: dict = {}          # level_num -> (dungeon, monsters, items)
        self.max_level_reached: int = 1
        self.monsters_killed: int   = 0
        self._placed_mini_bosses: set = set()

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
        from boss_levels import BOSS_LEVELS, COW_LEVEL, generate_boss_level

        if level_num in BOSS_LEVELS or level_num == COW_LEVEL:
            dungeon, monsters, items = generate_boss_level(level_num)
            # Place Philosopher's Stone on level 100
            if level_num == STONE_LEVEL:
                stone = _place_stone(dungeon, items)
                if stone:
                    items.append(stone)
            self.max_level_reached = max(self.max_level_reached, level_num)
            return dungeon, monsters, items

        from dungeon import generate_dungeon, spawn_monsters, spawn_items

        dungeon = generate_dungeon(80, 50, level_num)

        # Monster count scales with depth -- matches balance targets (L1:2-3, L20:3-5, L50:5-9)
        min_m = min(2 + level_num // 15, 7)
        max_m = min(3 + level_num // 8, 11)
        monsters = spawn_monsters(dungeon.rooms, level_num, dungeon, min_m, max_m)

        items = spawn_items(dungeon.rooms, level_num, dungeon)

        # Spawn extra monsters in monster_den special rooms
        # (must run after spawn_items which creates special rooms)
        _spawn_monster_den_extras(dungeon, monsters, level_num)

        # Try to spawn a mini-boss on this level
        self._try_spawn_mini_boss(dungeon, monsters, level_num)

        # Forced seal demon spawn (Abaddon quest — guaranteed on their specific levels)
        self._try_spawn_seal_demon(dungeon, monsters, level_num)

        # Populate hidden chambers with themed monsters/items
        _populate_hidden_chambers(dungeon, monsters, items, level_num)

        # Bones: chance to spawn a ghost from a previous player's death
        from bones import load_bones, spawn_ghost
        bones = load_bones(level_num)
        if bones:
            spawn_ghost(bones, dungeon, monsters, items)

        if level_num == STONE_LEVEL:
            stone = _place_stone(dungeon, items)
            if stone:
                items.append(stone)

        self.max_level_reached = max(self.max_level_reached, level_num)
        return dungeon, monsters, items


    def _try_spawn_mini_boss(self, dungeon, monsters: list, level_num: int):
        """Attempt to spawn one mini-boss on this level (at most one per level)."""
        import json as _json
        import random as _rng

        from paths import data_path as _dp
        _monsters_path = _dp('data', 'monsters.json')
        try:
            with open(_monsters_path, encoding='utf-8') as _f:
                _all_monsters = _json.load(_f)
        except Exception:
            return

        # Filter to eligible mini-bosses for this level that haven't been placed
        eligible = [
            (mid, mdata)
            for mid, mdata in _all_monsters.items()
            if mdata.get('is_mini_boss')
            and mdata.get('min_level', 999) <= level_num <= mdata.get('max_level', 0)
            and mid not in self._placed_mini_bosses
        ]

        if not eligible:
            return

        # Shuffle so ordering in JSON doesn't bias selection
        _rng.shuffle(eligible)

        # Roll spawn chance for each, stop at first success
        chosen_id = None
        chosen_data = None
        for mid, mdata in eligible:
            if _rng.random() < mdata.get('spawn_chance', 0.0):
                chosen_id = mid
                chosen_data = mdata
                break

        if chosen_id is None:
            return

        # Pick a room that isn't rooms[0] (start) or rooms[-1] (boss/exit)
        candidate_rooms = dungeon.rooms[1:-1] if len(dungeon.rooms) > 2 else dungeon.rooms[1:]
        if not candidate_rooms:
            candidate_rooms = dungeon.rooms

        room = _rng.choice(candidate_rooms)

        # Find a free walkable tile in the room
        occupied = {(m.x, m.y) for m in monsters}
        tiles = list(room.inner_tiles())
        _rng.shuffle(tiles)
        spawn_pos = None
        for tx, ty in tiles:
            if dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                spawn_pos = (tx, ty)
                break

        if spawn_pos is None:
            return

        # Build the monster via the normal Monster class
        # Monster.__init__ expects a defn dict with an 'id' key
        try:
            from monster import Monster
            defn = dict(chosen_data)
            defn['id'] = chosen_id
            mb = Monster(defn, spawn_pos[0], spawn_pos[1])
            monsters.append(mb)
            self._placed_mini_bosses.add(chosen_id)
        except Exception:
            pass


    _SEAL_DEMON_LEVELS = {
        83: 'seal_demon_wrath',
        85: 'seal_demon_pestilence',
        87: 'seal_demon_famine',
        89: 'seal_demon_war',
        91: 'seal_demon_death',
        93: 'seal_demon_earthquake',
        97: 'seal_demon_silence',
    }

    def _try_spawn_seal_demon(self, dungeon, monsters: list, level_num: int):
        """Force-spawn a seal demon on its designated level (guaranteed, always)."""
        demon_id = self._SEAL_DEMON_LEVELS.get(level_num)
        if not demon_id:
            return
        if demon_id in self._placed_mini_bosses:
            return  # already placed on a prior visit

        import json as _json
        import random as _rng
        from paths import data_path as _dp

        try:
            with open(_dp('data', 'monsters.json'), encoding='utf-8') as f:
                all_defs = _json.load(f)
        except Exception:
            return

        demon_data = all_defs.get(demon_id)
        if not demon_data:
            return

        # Pick a room (not start room) and find a free tile
        candidate_rooms = dungeon.rooms[1:-1] if len(dungeon.rooms) > 2 else dungeon.rooms[1:]
        if not candidate_rooms:
            candidate_rooms = dungeon.rooms
        _rng.shuffle(candidate_rooms)

        occupied = {(m.x, m.y) for m in monsters}
        for room in candidate_rooms:
            tiles = list(room.inner_tiles())
            _rng.shuffle(tiles)
            for tx, ty in tiles:
                if dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                    from monster import Monster
                    defn = dict(demon_data)
                    defn['id'] = demon_id
                    mb = Monster(defn, tx, ty)
                    monsters.append(mb)
                    self._placed_mini_bosses.add(demon_id)
                    return


def _spawn_monster_den_extras(dungeon, monsters: list, level_num: int):
    """Spawn 3-5 extra monsters in each monster_den special room."""
    from dungeon import spawn_monsters

    den_centers = [
        center for center, rtype in dungeon.special_rooms.items()
        if rtype == 'monster_den'
    ]
    if not den_centers:
        return

    for cx, cy in den_centers:
        # Find the Room object whose center matches
        den_room = None
        for room in dungeon.rooms:
            if room.center == (cx, cy):
                den_room = room
                break
        if den_room is None:
            continue

        # spawn_monsters skips rooms[0], so pass [dummy, den_room]
        extras = spawn_monsters([den_room, den_room], level_num, dungeon,
                                min_count=3, max_count=5)
        monsters.extend(extras)


def _populate_hidden_chambers(dungeon, monsters: list, items: list, level: int):
    """Populate each hidden chamber with themed monsters or treasure items."""
    import random as _rng
    from dungeon import spawn_monsters, spawn_items

    # Theme keyword -> monster name/id substrings to prefer
    THEME_KEYWORDS = {
        'rat_nest':       ['rat', 'rodent'],
        'spider_den':     ['spider'],
        'bat_cave':       ['bat'],
        'goblin_camp':    ['goblin'],
        'kobold_den':     ['kobold'],
        'orc_hideout':    ['orc'],
        'troll_cave':     ['troll'],
        'bandit_hideout': ['bandit', 'human', 'brigand', 'thug'],
        'undead_crypt':   ['skeleton', 'zombie', 'ghoul', 'ghost', 'wraith',
                           'vampire', 'lich', 'undead', 'specter', 'wight'],
        'demon_shrine':   ['demon', 'devil', 'imp', 'fiend'],
        'yuan_ti_lair':   ['yuan', 'serpent', 'snake', 'naga'],
        'vampire_crypt':  ['vampire', 'bat', 'ghoul'],
        'dragon_hoard':   ['dragon', 'drake', 'wyrm'],
        'lich_sanctum':   ['lich', 'skeleton', 'zombie', 'wraith', 'ghost'],
        'chaos_shrine':   ['chaos', 'demon', 'mutant'],
        'cache':          [],  # treasure -- no monsters
    }

    for chamber in getattr(dungeon, 'hidden_chambers', []):
        room = chamber['room']
        ctype = chamber['type']
        theme = chamber['theme']

        if ctype == 'treasure':
            # Spawn 3-5 items inside the chamber
            count_target = _rng.randint(3, 5)
            placed = 0
            # Re-use spawn_items on the single chamber room, then keep only
            # items that land inside the chamber (spawn_items skips rooms[0])
            chamber_items = spawn_items([room, room], level, dungeon)
            for it in chamber_items:
                if placed >= count_target:
                    break
                items.append(it)
                placed += 1

        elif ctype == 'lair':
            keywords = THEME_KEYWORDS.get(theme, [])
            count_target = _rng.randint(3, 6)

            # Try to spawn monsters via the normal helper using only this chamber room
            # spawn_monsters skips rooms[0], so pass [dummy, chamber_room]
            lair_monsters = spawn_monsters([room, room], level, dungeon,
                                           min_count=count_target,
                                           max_count=count_target + 1)

            if keywords:
                # Re-roll monsters that don't match the theme until we get a match
                # or run out of attempts; just label existing ones as themed preference
                themed = [m for m in lair_monsters
                          if any(kw in m.kind.lower() or kw in m.name.lower()
                                 for kw in keywords)]
                non_themed = [m for m in lair_monsters if m not in themed]

                # If we found no themed monsters at all, keep whatever spawned
                # (level-appropriate fallback) -- themed monsters may not exist at this level
                if themed:
                    # Prefer themed: fill remaining slots from themed pool
                    final = themed[:count_target]
                else:
                    final = lair_monsters[:count_target]
            else:
                final = lair_monsters[:count_target]

            monsters.extend(final)


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
