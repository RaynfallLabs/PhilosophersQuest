import copy

# Single source of truth for boss floors — imported from dungeon.py so
# `_roll_planned_mini_bosses` and `generate_boss_level` agree on which
# floors reject mini-boss placement.
from dungeon import _BOSS_LEVELS

# Philosopher's Stone spawns on this level
STONE_LEVEL = 100


def band_candidates(all_defs: dict, lo: int, hi: int) -> list:
    """[(id, defn, peak floor)] of the mini-bosses a band's slots draw from:
    every `is_mini_boss` with a spawn_chance above 0 whose peak_floor lies in
    the band. The seven seal demons (Abaddon's arc, placed by
    LevelManager._try_spawn_seal_demon) and the hand-placed ones (the gate
    floors' Asterion and Medusa, the Cow King, Old Nickel, Euryale beside
    Stheno: spawn_chance 0 or none) are not in it."""
    out = []
    for mid, m in all_defs.items():
        if not isinstance(m, dict) or not m.get('is_mini_boss') or mid.startswith('seal_demon'):
            continue
        if float(m.get('spawn_chance', 0) or 0) <= 0:
            continue
        pf = int(m.get('peak_floor', m.get('min_level', 1)) or 1)
        if lo <= pf <= hi:
            out.append((mid, m, pf))
    return out


def _free_floor(pf: int, lo: int, hi: int, taken: set, planned: dict):
    """The floor nearest a mini-boss's peak_floor, inside its band, with no
    gate boss, seal demon or other planned mini-boss: the peak itself, then
    one below, one above, two below... (a gate floor is the band's last, so
    one on a gate's floor is met the floor before it)."""
    for d in range(0, hi - lo + 1):
        for f in ((pf - d, pf + d) if d else (pf,)):
            if lo <= f <= hi and f not in taken and f not in planned:
                return f
    return None


def plan_mini_bosses(all_defs: dict, rng, bands=((1, 20), (21, 40), (41, 60), (61, 80), (81, 100)),
                     first: float = 1.0, second: float = 0.30, taken=frozenset()) -> dict:
    """{floor: mini-boss id}: each band's FIRST slot (chance `first`) and
    SECOND (chance `second`), each a pick weighted by spawn_chance among the
    band's candidates not picked yet (band_candidates), set on the free floor
    nearest its peak (_free_floor). Never on a floor in `taken` (the gate and
    seal floors)."""
    planned: dict = {}
    for lo, hi in bands:
        cands = band_candidates(all_defs, lo, hi)
        picked: set = set()
        for chance in (first, second):
            roll = rng.random()
            pool = [c for c in cands if c[0] not in picked]
            if roll >= chance or not pool:
                continue
            weights = [float(m.get('spawn_chance', 1.0) or 0) for _, m, _ in pool]
            if sum(weights) <= 0:
                continue
            mid, _m, pf = rng.choices(pool, weights=weights, k=1)[0]
            f = _free_floor(pf, lo, hi, set(taken), planned)
            if f is not None:
                planned[f] = mid
                picked.add(mid)
    return planned


class LevelManager:
    # Mini-boss bands (Brandon's ruling 13, 2026-11-16: "mini-bosses with cool
    # unique drops are supposed to be spread through the whole game, maybe one
    # or two every 20 floors"). Each 20-floor band, one per gate boss, has a
    # FIRST slot that is always filled and a SECOND filled in about one run in
    # three, so a run meets one or two named foes in every band: 6.5 a run.
    # Guaranteed, but earned: each waits somewhere on its floor and is a
    # fight. Who may fill a band is data: every rolled mini-boss whose
    # peak_floor lies in it, its floor set by its legend (docs/systems/
    # monsters.md, "Mini-bosses by lore"). The legendary ones (Ymir's Last
    # Spawn, Hrungnir, Tiamat, Surtur, Asmodeus) ride the slots of their band
    # like the rest; until 2026-11-17 each also rolled on its own at 50%, so
    # floors 81-100 met three or four besides the seven seals and the
    # shallow bands one run in ten met none.
    _MINI_BOSS_BANDS: list[tuple[int, int]] = [
        (1, 20),
        (21, 40),
        (41, 60),
        (61, 80),
        (81, 100),
    ]
    _MINI_BOSS_FIRST_CHANCE = 1.0
    _MINI_BOSS_SECOND_CHANCE = 0.30
    # The plan's rules: 2 is the band plan above. A save made under the old
    # rules (1) is planned again for the floors still ahead when it loads.
    _PLAN_VERSION = 2

    def __init__(self):
        self._saved: dict = {}          # level_num -> (dungeon, monsters, items)
        # Named uniques already handed out this run (items.claim_unique).
        self.seen_unique_ids: set = set()
        self._bind_uniques()
        self.max_level_reached: int = 1
        self.monsters_killed: int   = 0
        self._placed_mini_bosses: set = set()
        # Mini-boss spawns are PRE-ROLLED at run start. Each band gets one or
        # two mini-bosses picked weighted by spawn_chance. Placement is each
        # chosen mini-boss's peak_floor (or the nearest free floor of its
        # band). Every band member has weighted odds every run.
        self._planned_mini_bosses: dict = self._roll_planned_mini_bosses()
        self._plan_version: int = self._PLAN_VERSION

    def save(self, level_num: int, dungeon, monsters: list, ground_items: list):
        """Persist current level state so it can be restored later."""
        self._saved[level_num] = (dungeon, list(monsters), list(ground_items))

    def load(self, level_num: int):
        """Return (dungeon, monsters, items) for a saved level, or None."""
        return self._saved.get(level_num)

    def _bind_uniques(self) -> None:
        import items
        if not hasattr(self, 'seen_unique_ids'):
            self.seen_unique_ids = set()            # a save from before the rule
        items.bind_unique_registry(self.seen_unique_ids)

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._bind_uniques()
        # A run saved under the old plan (before the mini-bosses were seated
        # by lore, 2026-11-17) meets the new bands on the floors still ahead.
        if (isinstance(self.__dict__.get('_planned_mini_bosses'), dict)
                and int(self.__dict__.get('_plan_version', 1) or 1) < self._PLAN_VERSION):
            try:
                self._replan_ahead()
            except Exception:
                from game_log import log_error
                log_error('level_manager.__setstate__: the old mini-boss plan was kept')
            self._plan_version = self._PLAN_VERSION

    def _replan_ahead(self) -> None:
        """Plan the floors not yet reached by today's bands, keeping what an
        old save already has on the floors behind (or already made). A band
        the hero is part-way through keeps its earlier mini-boss and takes
        new ones only up to the count its fresh plan has."""
        reached = int(getattr(self, 'max_level_reached', 1) or 1)
        made = set(getattr(self, '_saved', {}) or {})
        placed = set(getattr(self, '_placed_mini_bosses', set()) or set())
        old = dict(self._planned_mini_bosses)
        keep = {f: m for f, m in old.items() if f <= reached or f in made}
        fresh = self._roll_planned_mini_bosses()
        used = set(keep.values()) | placed
        for lo, hi in self._MINI_BOSS_BANDS:
            want = sorted(f for f in fresh if lo <= f <= hi)
            have = [f for f in keep if lo <= f <= hi]
            for f in want:
                if len(have) >= len(want):
                    break
                m = fresh[f]
                if f <= reached or f in made or f in keep or m in used:
                    continue
                keep[f] = m
                used.add(m)
                have.append(f)
        self._planned_mini_bosses = keep

    def _once_per_run(self, floor_items: list) -> list:
        """Drop any named unique this run has already produced, and record
        the ones that stay (on the floor or on a merchant's shelf)."""
        from items import claim_unique, unique_available
        kept = []
        for it in floor_items:
            stock = getattr(it, 'stock', None)
            if isinstance(stock, list) and hasattr(it, 'prices'):
                keep = [i for i, s in enumerate(stock) if unique_available(s)]
                it.prices = [it.prices[i] for i in keep]
                it.stock = [stock[i] for i in keep]
                for s in it.stock:
                    claim_unique(s)
                if not it.stock:
                    # Every ware was a unique this run already has: no empty
                    # shop (ECONOMY_REFACTOR_PROPOSAL S10).
                    it.sold_out = True
            if not unique_available(it):
                continue
            claim_unique(it)
            kept.append(it)
        return kept

    def generate(self, level_num: int):
        """Create a fresh level, spawn monsters/items, save, and return it."""
        from boss_levels import BOSS_LEVELS, generate_boss_level, is_side_floor

        if level_num in BOSS_LEVELS or is_side_floor(level_num):
            dungeon, monsters, items = generate_boss_level(level_num)
            # Place Philosopher's Stone on level 100
            # The Philosopher's Stone is NOT placed here any more. It used to
            # lie on the arena floor from the start, so the player could take
            # it without facing Abaddon. game_combat._on_monster_killed drops
            # it where he falls (see spawn_stone_at below).
            # A side floor (the Cow Level is numbered 999 internally, the
            # Zombie Stage 997) is a side trip, not depth: counting the farm
            # made "Deepest Level 999" and added 999,000 to the score.
            if not is_side_floor(level_num):
                self.max_level_reached = max(self.max_level_reached, level_num)
            # A character who died to a gate boss haunts that boss's floor
            # (never the Cow Level or the Stone floor).
            if level_num in (20, 40, 60, 80):
                self._maybe_spawn_bones(level_num, dungeon, monsters, items)
            import senses
            senses.assign_jobs(monsters, dungeon.rooms)
            # A gate floor wears its domain's look and is dressed for its
            # showdown (data/boss_floors.json, decor.dress_boss_floor).
            import decor
            if not is_side_floor(level_num):
                decor.dress_boss_floor(dungeon, level_num, monsters, items)
            items = self._once_per_run(items)
            return dungeon, monsters, items

        from dungeon import generate_dungeon, spawn_items, populate_floor, FLOOR_DENSITY_BASE

        dungeon = generate_dungeon(80, 50, level_num)

        # Monster spread scales with depth (2026-05-19 density rebuild;
        # 2026-06-06 per-room pass). `density` is the PER-ROOM probability of
        # a baseline monster -- populate_floor rolls every room, so the
        # population spreads across the whole floor instead of lumping in one
        # corner. Packs, bands and den/zoo extras cluster intentionally on top.
        # 3.5.1: it starts at 0.62 (was 0.50). A floor's own monsters carry the
        # fight now; newcomers come only to a hero who lingers (src/wanderers.py).
        density = min(FLOOR_DENSITY_BASE + level_num / 130, 0.95)
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

        # A war-band may have made camp in one room (src/war_bands.py).
        import war_bands
        war_bands.place_band(dungeon, monsters, level_num)

        # The clan's clue, only if the clan really holds the floor now that
        # it is peopled (audit G6: it named families with no one there). It
        # is said on arrival by FamilyMixin._family_arrival, which knows the
        # hero: never to one Forewarned of the family, whose own line names it.
        import hazards
        _clan = getattr(dungeon, 'clan', None)
        if _clan:
            _foes = [m for m in monsters if getattr(m, 'alive', True)
                     and not getattr(m, 'is_allied', False) and getattr(m, 'family', None)]
            _share = (sum(1 for m in _foes if m.family == _clan) / len(_foes)) if _foes else 0.0
            _line = hazards.clan_line(_clan)
            if _line and _share >= 0.25:
                dungeon.clan_sign = _line

        # Bones: chance to spawn a ghost from a previous player's death
        self._maybe_spawn_bones(level_num, dungeon, monsters, items)

        # A mimic posing as the down stair (the Hellmouth) lies only where
        # the real stair stays reachable (src/false_stairs.py).
        import false_stairs
        false_stairs.seat(dungeon, monsters)

        # The domain's look and its dressing (src/decor.py), once everything
        # else is down so no item or creature lands under a statue.
        import decor
        decor.dress_floor(dungeon, level_num, monsters, items)
        # A statue set down in a maze corridor or a doorway can leave the
        # Hellmouth's tile the only way through: seat it again. One that
        # still leaves a way round stays where it lies.
        false_stairs.seat(dungeon, monsters)

        # Each creature's own business until it notices the hero
        # (src/senses.py). A den is where they sleep, as its line says (G3).
        import senses
        senses.assign_jobs(monsters, dungeon.rooms, sleep_rooms=[
            room for room in dungeon.rooms
            if dungeon.special_rooms.get(tuple(room.center)) == 'monster_den'])

        self.max_level_reached = max(self.max_level_reached, level_num)
        items = self._once_per_run(items)
        return dungeon, monsters, items

    @staticmethod
    def _maybe_spawn_bones(level_num: int, dungeon, monsters: list, items: list):
        from bones import load_bones, spawn_ghost
        bones = load_bones(level_num)
        if bones:
            try:
                spawn_ghost(bones, dungeon, monsters, items)
            except Exception:
                from game_log import log_error
                log_error('level_manager._maybe_spawn_bones: recovered from an error')  # a damaged bones file costs its ghost, never the floor


    def _roll_planned_mini_bosses(self) -> dict:
        """Pre-roll which mini-bosses appear in this run and on which floors.

        Returns dict[level_num] -> mini_boss_id (plan_mini_bosses).
        """
        import json as _json
        import random as _rng
        from paths import data_path as _dp

        try:
            with open(_dp('data', 'monsters.json'), encoding='utf-8') as _f:
                _all = _json.load(_f)
        except Exception:
            return {}
        return plan_mini_bosses(
            _all, _rng, bands=self._MINI_BOSS_BANDS, first=self._MINI_BOSS_FIRST_CHANCE,
            second=self._MINI_BOSS_SECOND_CHANCE,
            taken=set(_BOSS_LEVELS) | set(self._SEAL_DEMON_LEVELS))

    def _place_escort(self, eid: str, all_defs: dict, leader, dungeon, monsters: list):
        """Set a mini-boss's companion down on the nearest free tile it fits
        (two rings out at most). Placed once per run, like the leader."""
        from monster import Monster
        from geom import all_occupied_tiles
        from dungeon import _footprint_fits
        edef = all_defs.get(eid)
        if edef is None or eid in self._placed_mini_bosses:
            return None
        taken = all_occupied_tiles(monsters)
        for r in (1, 2, 3):
            ring = [(leader.x + dx, leader.y + dy) for dx in range(-r, r + 1)
                    for dy in range(-r, r + 1) if max(abs(dx), abs(dy)) == r]
            for x, y in ring:
                if (dungeon.in_bounds(x, y) and dungeon.is_walkable(x, y)
                        and (x, y) not in taken and _footprint_fits(edef, x, y, dungeon, monsters)):
                    esc = Monster({**edef, 'id': eid}, x, y)
                    monsters.append(esc)
                    self._placed_mini_bosses.add(eid)
                    return esc
        return None

    def _carry_mini_boss(self, mid: str, level_num: int):
        """A planned mini-boss that could not be set down on ``level_num``
        is planned instead on the next floor not yet made, within five,
        that holds no gate boss, seal demon or other planned mini-boss.
        Returns that floor, or None (then he is lost, as before)."""
        taken = (set(_BOSS_LEVELS) | set(self._SEAL_DEMON_LEVELS)
                 | set(self._planned_mini_bosses) | set(self._saved))
        for target in range(level_num + 1, min(level_num + 6, 100)):
            if target not in taken:
                if self._planned_mini_bosses.get(level_num) == mid:
                    del self._planned_mini_bosses[level_num]
                self._planned_mini_bosses[target] = mid
                return target
        return None

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
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(monsters)
        spawn_pos = None
        # Check the WHOLE footprint, not just the anchor tile: the 2x2
        # mini-bosses (Tiamat, Surtur, Ymir, Hrungnir) could otherwise spawn
        # half inside a wall on a room's east or south edge. Try every
        # candidate room: this used to pick ONE room and drop the mini-boss
        # for the whole run if its footprint did not fit there.
        from dungeon import _footprint_fits
        candidate_rooms = list(candidate_rooms)
        _rng.shuffle(candidate_rooms)
        for room in candidate_rooms:
            tiles = list(room.inner_tiles())
            _rng.shuffle(tiles)
            for tx, ty in tiles:
                if (dungeon.is_walkable(tx, ty) and (tx, ty) not in occupied
                        and _footprint_fits(mdata, tx, ty, dungeon, monsters)):
                    spawn_pos = (tx, ty)
                    break
            if spawn_pos is not None:
                break
        if spawn_pos is None:
            # A maze floor has two rooms and the far one is often full: the
            # planned mini-boss (Surtur on 90 one run in three) was lost for
            # the run. Anywhere it fits that the hero can walk to will do,
            # away from the arrival room.
            from dungeon import _reach_from_stairs, FLOOR
            reach = _reach_from_stairs(dungeon)
            start = dungeon.rooms[0] if dungeon.rooms else None

            def _in_start(x, y):
                return (start is not None and start.x <= x < start.x + start.width
                        and start.y <= y < start.y + start.height)
            spots = [(x, y) for y in range(dungeon.height) for x in range(dungeon.width)
                     if dungeon.tiles[y][x] == FLOOR and (not reach or (x, y) in reach)
                     and not _in_start(x, y) and (x, y) not in occupied
                     and _footprint_fits(mdata, x, y, dungeon, monsters)]
            if spots:
                spawn_pos = _rng.choice(spots)
        if spawn_pos is None:
            # Nowhere he fits: a big body on a maze floor whose clearings the
            # floor's own monsters fill (Surtur on 90 was lost for the run in
            # about one run in fourteen). He comes a floor or two later.
            self._carry_mini_boss(mid, level_num)
            return

        try:
            from monster import Monster
            defn = dict(mdata)
            defn['id'] = mid
            mb = Monster(defn, spawn_pos[0], spawn_pos[1])
            monsters.append(mb)
            self._placed_mini_bosses.add(mid)
            # Some arrive in company (Stheno never goes anywhere without
            # Euryale): `escort` lists ids set down beside the mini-boss.
            for _eid in mdata.get('escort') or ():
                self._place_escort(_eid, _all, mb, dungeon, monsters)
            # An omen on arrival: the player learns something named is here
            # without being told what. (Mini-bosses were never announced.)
            omen = mdata.get('omen')
            if omen:
                if not hasattr(dungeon, 'omen_messages'):
                    dungeon.omen_messages = []
                dungeon.omen_messages.append(omen)
        except Exception:
            from game_log import log_error
            log_error('level_manager._try_spawn_mini_boss: recovered from an error')


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
        if demon_id not in self._placed_mini_bosses:
            if not hasattr(dungeon, 'omen_messages'):
                dungeon.omen_messages = []
            dungeon.omen_messages.append(
                "A wax-red mark is pressed into the stair. Its keeper is "
                "somewhere on this floor.")
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
                    # The stair is sealed while its keeper lives, so a seal
                    # can no longer be walked past and discovered missing at
                    # the floor-99 gate, a dozen floors of climbing later.
                    dungeon.stairs_guardian = demon_id
                    dungeon.stairs_guardian_line = (
                        "A seal of red wax as wide as a shield is set across "
                        "the stair. Its keeper is still on this floor.")
                    dungeon.stairs_guardian_open_line = (
                        "The seal across the stair cracks from edge to edge "
                        "and falls away.")
                    return


def _spawn_monster_den_extras(dungeon, monsters: list, level_num: int):
    """Spawn 3-5 extra monsters in each monster_den special room.

    NOTE: `spawn_monsters` skips its first room (the start room convention).
    Both this helper and `_populate_hidden_chambers` exploit that by passing
    the same room twice so the target room is the "second" one and gets
    populated. If `spawn_monsters` ever loses that convention, BOTH call
    sites here and in `_populate_hidden_chambers` must be updated together.
    """
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
                                min_count=3, max_count=5, existing=monsters)
        monsters.extend(extras)


def _populate_hidden_chambers(dungeon, monsters: list, items: list, level: int):
    """Populate each hidden chamber with themed monsters or treasure items."""
    import random as _rng
    from dungeon import spawn_chamber_cache

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

    # The families a lair's theme belongs to, when no kind on the floor
    # carries one of its words (G2: lairs drew from the whole pool and were
    # themed a fifth of the time; yuan-ti lairs never).
    THEME_FAMILIES = {
        'rat_nest': ['vermin'], 'spider_den': ['vermin'], 'bat_cave': ['vermin'],
        'goblin_camp': ['goblinkin'], 'kobold_den': ['goblinkin'], 'orc_hideout': ['goblinkin'],
        'troll_cave': ['giants'], 'bandit_hideout': ['mortals'],
        'undead_crypt': ['restless_dead', 'ghosts'], 'demon_shrine': ['demons'],
        'yuan_ti_lair': ['serpents'], 'vampire_crypt': ['vampires_liches'],
        'dragon_hoard': ['dragons'], 'lich_sanctum': ['vampires_liches', 'restless_dead'],
        'chaos_shrine': ['demons', 'aberrations'],
    }
    from dungeon import spawn_themed

    for chamber in getattr(dungeon, 'hidden_chambers', []):
        room = chamber['room']
        ctype = chamber['type']
        theme = chamber['theme']

        if ctype == 'treasure':
            # A cache of 3-5 things: coin, treasure, potions and scrolls
            # (dungeon.spawn_chamber_cache). It re-ran spawn_items here,
            # which handed out an armory behind every secret door.
            items.extend(spawn_chamber_cache(room, level, dungeon, _rng.Random()))

        elif ctype == 'lair':
            # The lair's own kind: its words first, then its families, then
            # (no kind of either can live this deep) the floor's own pool.
            final = spawn_themed(room, level, dungeon,
                                 words=THEME_KEYWORDS.get(theme, []),
                                 families=THEME_FAMILIES.get(theme, []),
                                 count=(3, 6), existing=monsters, rng=_rng.Random())
            monsters.extend(final)


def spawn_stone_at(x: int, y: int):
    """A Philosopher's Stone instance at (x, y), or None if the data is gone."""
    from items import load_items
    try:
        artifacts = load_items('artifact')
    except (FileNotFoundError, KeyError):
        return None
    template = next((a for a in artifacts if a.id == 'philosophers_stone'), None)
    if template is None:
        return None
    inst = copy.copy(template)
    inst.x, inst.y = x, y
    return inst
