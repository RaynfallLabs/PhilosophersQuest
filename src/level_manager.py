import copy
import random

# Philosopher's Stone spawns on this level
STONE_LEVEL = 100


class LevelManager:
    # Mini-boss spawn bands. Each band gets ONE primary roll (90%) plus ONE
    # secondary roll (30%). Expected mini-bosses per 100-floor run: 5 × 1.2 = 6.
    _MINI_BOSS_BANDS: list[tuple[int, int]] = [
        (1, 20),
        (21, 40),
        (41, 60),
        (61, 80),
        (81, 100),
    ]
    _MINI_BOSS_PRIMARY_CHANCE = 0.90
    _MINI_BOSS_SECONDARY_CHANCE = 0.30

    def __init__(self):
        self._saved: dict = {}          # level_num -> (dungeon, monsters, items)
        self.max_level_reached: int = 1
        self.monsters_killed: int   = 0
        self._placed_mini_bosses: set = set()
        # Mini-boss spawns are PRE-ROLLED at run start. Each band gets 0-2
        # mini-bosses picked weighted by spawn_chance. Placement is locked to
        # each chosen mini-boss's peak_floor. This guarantees fair variety
        # across runs (every band member has weighted odds, not first-eligible-
        # wins).
        self._planned_mini_bosses: dict = self._roll_planned_mini_bosses()

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

        from dungeon import generate_dungeon, spawn_items, populate_floor

        dungeon = generate_dungeon(80, 50, level_num)

        # Monster spread scales with depth (2026-05-19 density rebuild;
        # 2026-06-06 per-room pass). `density` grows from 0.50 at L1 to 0.95 at
        # L75+ and is the PER-ROOM probability of a baseline monster --
        # populate_floor rolls every room, so the population spreads across the
        # whole floor instead of lumping in one corner. Packs and den/zoo extras
        # cluster intentionally on top.
        density = min(0.50 + level_num / 130, 0.95)
        monsters = populate_floor(dungeon.rooms, level_num, dungeon, occupancy=density)

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


    def _roll_planned_mini_bosses(self) -> dict:
        """Pre-roll which mini-bosses appear in this run and on which floors.

        Returns dict[level_num] -> mini_boss_id.

        Each band gets a primary slot (90%) and secondary slot (30%) chance.
        Within a slot, candidates are weighted by spawn_chance. Placement
        floor is the chosen mini-boss's peak_floor.

        Expected per run: 5 × (0.90 + 0.30) = 6.0 mini-bosses, range 4-8.
        """
        import json as _json
        import random as _rng
        from paths import data_path as _dp

        try:
            with open(_dp('data', 'monsters.json'), encoding='utf-8') as _f:
                _all = _json.load(_f)
        except Exception:
            return {}

        planned: dict = {}
        for band_lo, band_hi in self._MINI_BOSS_BANDS:
            candidates = []
            for mid, m in _all.items():
                if not m.get('is_mini_boss'):
                    continue
                # Seal demons are flagged is_mini_boss but use a separate
                # forced-spawn path (_try_spawn_seal_demon). Don't compete
                # with the random pool.
                if mid.startswith('seal_demon'):
                    continue
                if m.get('spawn_chance', 0) <= 0:
                    continue
                pf = int(m.get('peak_floor', m.get('min_level', 1)))
                if not (band_lo <= pf <= band_hi):
                    continue
                candidates.append((mid, m, pf))
            if not candidates:
                continue

            placed_ids: set = set()

            def _pick():
                pool = [(mid, m, pf) for mid, m, pf in candidates if mid not in placed_ids]
                if not pool:
                    return None
                weights = [float(m.get('spawn_chance', 1.0)) for _, m, _ in pool]
                if sum(weights) <= 0:
                    return None
                return _rng.choices(pool, weights=weights, k=1)[0]

            # Primary slot
            if _rng.random() < self._MINI_BOSS_PRIMARY_CHANCE:
                pick = _pick()
                if pick is not None:
                    mid, _, pf = pick
                    # Avoid landing on a boss floor — if peak_floor collides,
                    # shift +/- 1.
                    target = pf if pf not in (20, 40, 60, 80, 100) else pf - 1
                    planned[target] = mid
                    placed_ids.add(mid)

            # Secondary slot
            if _rng.random() < self._MINI_BOSS_SECONDARY_CHANCE:
                pick = _pick()
                if pick is not None:
                    mid, _, pf = pick
                    target = pf if pf not in (20, 40, 60, 80, 100) else pf - 1
                    # If two mini-bosses share peak_floor, offset the second
                    while target in planned:
                        target += 1
                        if target > band_hi:
                            target = pf
                            break
                    if target not in planned:
                        planned[target] = mid
                        placed_ids.add(mid)

        return planned

    def _try_spawn_mini_boss(self, dungeon, monsters: list, level_num: int):
        """Place this floor's planned mini-boss (if any). Pre-rolled at run start."""
        import random as _rng
        import json as _json
        from paths import data_path as _dp

        mid = self._planned_mini_bosses.get(level_num)
        if mid is None:
            return
        if mid in self._placed_mini_bosses:
            return

        try:
            with open(_dp('data', 'monsters.json'), encoding='utf-8') as _f:
                _all = _json.load(_f)
        except Exception:
            return

        mdata = _all.get(mid)
        if mdata is None:
            return

        candidate_rooms = dungeon.rooms[1:-1] if len(dungeon.rooms) > 2 else dungeon.rooms[1:]
        if not candidate_rooms:
            candidate_rooms = dungeon.rooms
        if not candidate_rooms:
            return
        room = _rng.choice(candidate_rooms)
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(monsters)
        tiles = list(room.inner_tiles())
        _rng.shuffle(tiles)
        spawn_pos = None
        for tx, ty in tiles:
            if dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied:
                spawn_pos = (tx, ty)
                break
        if spawn_pos is None:
            return

        try:
            from monster import Monster
            defn = dict(mdata)
            defn['id'] = mid
            mb = Monster(defn, spawn_pos[0], spawn_pos[1])
            monsters.append(mb)
            self._placed_mini_bosses.add(mid)
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

        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(monsters)
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
