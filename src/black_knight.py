"""The Black Knight: an easter egg, about one run in four.

On one floor from 15 to 19 a knight in black armour stands on a short stone
bridge over a strip of water across a corridor, and says that none shall
pass. There is always another way round (the bridge is only ever built where
the floor stays joined up with him standing on it), so he never blocks the run.

He never moves. He loses a limb at 75, 50 and 25 per cent of his health, and
any single hit (melee, ranged, spell, wand, special or instant kill) takes him
down to the next of those marks and no further. On his last leg a hit leaves
him teetering on 1, and only the next blow takes the leg: so he takes at least
five hits, the last of them the blow that leaves the torso. His attack changes with each stage
(sword and shield, sword, kick, hop). When his sword arm goes, his sword falls
onto the bridge beside him: that is the reward. At 0 he is not killed: he is a
torso on the bridge that calls it a draw, bites at your boots for nothing,
shouts after you, and swaps places with you when you walk into him.

"One hit" is one action: once he loses a limb, he loses nothing more until
the turn is over (Game._advance_turn calls ``_black_knight_tick`` before and
after the world moves). A blow that lands twice in one action (the Sword of
Damocles' second strike, a weapon proc) cannot take two limbs.

Run state: ``game._black_knight`` (saved): {'floor', 'spawned', 'outcome',
'sword_dropped'}. The knight himself, his stage and what he has said live on
the creature, which is saved with its floor. Text and numbers are in
data/black_knight.json; his fighting numbers in data/monsters.json; his sword
is ``flesh_wound`` in data/items/weapon.json.
"""
from __future__ import annotations

import json
import random

from monster import Monster

_DATA: dict | None = None

TORSO = 4


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'black_knight.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def monster_defn() -> dict:
    from paths import data_path
    with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
        d = json.load(f)[data()['monster_id']]
    return {**d, 'id': data()['monster_id']}


# ---------------------------------------------------------------------------
# The roll: which floor this run, if any
# ---------------------------------------------------------------------------

def roll_floor(rng) -> int | None:
    d = data()
    if rng.random() >= float(d['chance_per_run']):
        return None
    return rng.randint(int(d['first_floor']), int(d['last_floor']))


def roll_for_new_run() -> int | None:
    """roll_floor from its own generator, seeded from the shared stream without
    disturbing it, so seeded floors and captures are unchanged."""
    saved = random.getstate()
    try:
        seed = random.getrandbits(64)
    finally:
        random.setstate(saved)
    return roll_floor(random.Random(seed ^ 0xB1AC4))


def new_run_state() -> dict:
    return {'floor': roll_for_new_run(), 'spawned': False, 'outcome': None, 'sword_dropped': False}


def is_black_knight(thing) -> bool:
    return bool(getattr(thing, 'is_black_knight', False))


# ---------------------------------------------------------------------------
# The knight
# ---------------------------------------------------------------------------

class BlackKnight(Monster):
    """A Monster whose health falls one stage per action and never reaches 0,
    who never moves once set on his bridge, and whose attacks and picture
    follow his stage."""

    is_black_knight = True
    stationary = True

    def __init__(self, defn: dict, x: int, y: int):
        self.__dict__['_bk_ready'] = False
        super().__init__(defn, x, y)
        self._bk_events = []          # ('hit', stage) / ('stage', new stage), drained by the game
        self._bk_locked = False       # a limb went this action: no more until the turn is over
        self._bk_defeated = False
        self._bk_rooted = False       # set once he is on his bridge
        self._bk_greeted = False
        self._bk_engaged = False      # came within reach since the last parting shout
        self._bk_said = {}            # line pool -> how many used (lines cycle in order)
        self.__dict__['_bk_ready'] = True

    # --- health: stages -------------------------------------------------

    def threshold(self, i: int) -> int:
        """Health at which limb i (1-3) is lost: 75, 50, 25 per cent."""
        return self.max_hp * (4 - i) // 4

    @property
    def stage(self) -> int:
        """0 whole, 1 no left arm, 2 no arms, 3 one leg, 4 torso."""
        d = self.__dict__
        if d.get('_bk_defeated'):
            return TORSO
        hp = d.get('_bk_hp', 0)
        for i in (1, 2, 3):
            if hp > self.threshold(i):
                return i - 1
        return 3

    @property
    def defeated(self) -> bool:
        return bool(self.__dict__.get('_bk_defeated'))

    @property
    def hp(self) -> int:
        return self.__dict__.get('_bk_hp', 0)

    @hp.setter
    def hp(self, value):
        d = self.__dict__
        value = int(value)
        if not d.get('_bk_ready'):
            d['_bk_hp'] = value
            return
        if d.get('_bk_defeated'):
            d['_bk_hp'] = 1
            return
        cur = d.get('_bk_hp', 0)
        st = self.stage
        if value >= cur:
            # Healing never grows a limb back.
            d['_bk_hp'] = min(value, self.max_hp if st == 0 else self.threshold(st))
            return
        if d.get('_bk_locked'):
            return
        if st < 3:
            floor = self.threshold(st + 1)
        else:
            # On his last leg the last blow is its own blow: a hit stops at 1
            # (he teeters), and only a blow from 1 takes the leg. So he takes
            # at least five hits: three limbs, the teeter, the last leg.
            floor = 1 if cur > 1 else 0
        if value > floor or (floor == 1 and value <= 1):
            d['_bk_hp'] = max(value, floor)
            d['_bk_events'].append(('teeter' if d['_bk_hp'] == 1 else 'hit', st))
            if d['_bk_hp'] == 1:
                d['_bk_locked'] = True
            return
        d['_bk_locked'] = True
        if floor <= 0:
            d['_bk_hp'] = 1
            d['_bk_defeated'] = True
            self.is_allied = True            # harmless now: not a target, not a threat
            self.status_effects = {}
            d['_bk_events'].append(('stage', TORSO))
        else:
            d['_bk_hp'] = floor
            d['_bk_events'].append(('stage', st + 1))

    @property
    def alive(self) -> bool:
        return self.__dict__.get('_bk_alive', True)

    @alive.setter
    def alive(self, value):
        d = self.__dict__
        if not d.get('_bk_ready') or value:
            d['_bk_alive'] = True
            return
        # Something tried to kill him outright: it is one more hit.
        if not d.get('_bk_defeated'):
            self.hp = 0

    # --- he stays on his bridge --------------------------------------------

    @property
    def x(self) -> int:
        return self.__dict__.get('_bk_x', 0)

    @x.setter
    def x(self, value):
        if not self.__dict__.get('_bk_rooted'):
            self.__dict__['_bk_x'] = value

    @property
    def y(self) -> int:
        return self.__dict__.get('_bk_y', 0)

    @y.setter
    def y(self, value):
        if not self.__dict__.get('_bk_rooted'):
            self.__dict__['_bk_y'] = value

    def place(self, x: int, y: int) -> None:
        """Move him (only the game's own step-past swap does)."""
        self.__dict__['_bk_x'], self.__dict__['_bk_y'] = x, y

    def root(self) -> None:
        self.__dict__['_bk_rooted'] = True

    # --- what he fights with and looks like -------------------------------

    @property
    def attacks(self) -> list:
        st = self.stage
        if st == 0:
            return self.__dict__.get('_bk_base_attacks', [])
        if st == TORSO:
            return []
        key = {1: 'one_arm', 2: 'no_arms', 3: 'one_leg'}[st]
        return data()['stage_attacks'][key]

    @attacks.setter
    def attacks(self, value):
        self.__dict__['_bk_base_attacks'] = list(value or [])

    @property
    def sprite_id(self) -> str:
        return data()['stage_sprites'][self.stage]

    def take_turn(self, player, dungeon, all_monsters, extra_occupied=None) -> bool:
        """He never moves, flees or wanders: he strikes whoever stands next
        to him. The torso only bites (Game._black_knight_tick says so)."""
        self._cached_all_monsters = all_monsters
        if not self.alive or self.defeated:
            return False
        if any(self.has_effect(e) for e in ('sleeping', 'paralyzed', 'stunned', 'frozen')):
            return False
        self._aware = True
        return self._adjacent_to(player)


# ---------------------------------------------------------------------------
# Where he stands: a bridge with a way round
# ---------------------------------------------------------------------------

def _room_cells(dungeon) -> set:
    cells = set()
    for r in dungeon.rooms:
        for x in range(r.x, r.x + r.width):
            for y in range(r.y, r.y + r.height):
                cells.add((x, y))
    return cells


def _passable(dungeon, x, y) -> bool:
    """A tile the hero can walk onto: floor-like, or a door he can open.
    Secret doors do not count: a way round must be one he can see."""
    from dungeon import DOOR
    return dungeon.is_walkable(x, y) or (dungeon.in_bounds(x, y) and dungeon.tiles[y][x] == DOOR)


def flood(dungeon, start, blocked=None) -> set:
    """Tiles the hero can walk to from `start`, four ways, never through `blocked`."""
    seen = {start}
    stack = [start]
    while stack:
        x, y = stack.pop()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if n in seen or n == blocked or not _passable(dungeon, *n):
                continue
            seen.add(n)
            stack.append(n)
    return seen


def has_way_round(dungeon, start, spot) -> bool:
    """True if every tile reachable from `start` is still reachable with the
    knight standing on `spot` (he never moves): he cuts nothing off."""
    whole = flood(dungeon, start)
    if spot not in whole:
        return False
    return flood(dungeon, start, blocked=spot) == whole - {spot}


def _bridge_candidates(dungeon, rooms: set, length: int):
    """(axis, tiles) for every straight run of corridor where a bridge fits:
    `length` corridor tiles with one more corridor tile at each end, solid
    wall on both sides all along, nothing of a room."""
    from dungeon import FLOOR, WALL
    t = dungeon.tiles
    w, h = dungeon.width, dungeon.height
    half = length // 2 + 1
    out = []
    for y in range(3, h - 3):
        for x in range(3, w - 3):
            for axis, (ax, ay), (px, py) in (('h', (1, 0), (0, 1)), ('v', (0, 1), (1, 0))):
                run = [(x + ax * k, y + ay * k) for k in range(-half, half + 1)]
                if not all(0 < cx < w - 1 and 0 < cy < h - 1 for cx, cy in run):
                    continue
                if any(t[cy][cx] != FLOOR or (cx, cy) in rooms for cx, cy in run):
                    continue
                sides = [(cx + px * s, cy + py * s) for cx, cy in run for s in (-1, 1)]
                if any(not dungeon.in_bounds(*c) or t[c[1]][c[0]] != WALL or c in rooms for c in sides):
                    continue
                out.append((axis, run[1:-1]))
    return out


def find_site(dungeon, start, rng, taken=(), length: int = 3) -> dict | None:
    """Where the knight goes on this floor:
    {'kind': 'bridge'|'doorway'|'corridor', 'knight': (x, y), 'bridge': [...], 'axis': 'h'|'v'|None}.
    Every answer leaves a way round (has_way_round). None when nothing fits."""
    rooms = _room_cells(dungeon)
    taken = set(taken)
    traps = getattr(dungeon, 'traps', {}) or {}
    cands = _bridge_candidates(dungeon, rooms, length)
    rng.shuffle(cands)
    for axis, tiles in cands:
        mid = tiles[len(tiles) // 2]
        if mid in taken or any(tt in traps for tt in tiles):
            continue
        if has_way_round(dungeon, start, mid):
            return {'kind': 'bridge', 'knight': mid, 'bridge': list(tiles), 'axis': axis}
    # No corridor suits: a doorway with a way round.
    from dungeon import FLOOR, DOOR
    doorways = []
    for r in dungeon.rooms:
        for cx, cy in r.wall_tiles():
            if dungeon.in_bounds(cx, cy) and dungeon.tiles[cy][cx] in (FLOOR, DOOR):
                doorways.append((cx, cy))
    rng.shuffle(doorways)
    for spot in doorways:
        if spot in taken or spot in traps:
            continue
        if has_way_round(dungeon, start, spot):
            return {'kind': 'doorway', 'knight': spot, 'bridge': [], 'axis': None}
    return None


def build_bridge(dungeon, site: dict) -> None:
    """Carve the strip of water across the corridor and mark the bridge.
    Only solid wall beside the corridor turns to water, so nothing that
    could be walked on before is lost and nothing new can be walked on."""
    from dungeon import WALL, WATER, DOOR, FLOOR
    if site['kind'] == 'doorway':
        x, y = site['knight']
        if dungeon.tiles[y][x] == DOOR:
            dungeon.tiles[y][x] = FLOOR          # he stands in the open door
        return
    rooms = _room_cells(dungeon)
    px, py = (0, 1) if site['axis'] == 'h' else (1, 0)
    for bx, by in site['bridge']:
        for s in (-2, -1, 1, 2):
            cx, cy = bx + px * s, by + py * s
            if (0 < cx < dungeon.width - 1 and 0 < cy < dungeon.height - 1
                    and dungeon.tiles[cy][cx] == WALL and (cx, cy) not in rooms):
                if abs(s) == 2:
                    # the outer row only where the inner one is water already
                    ix, iy = bx + px * (s // 2), by + py * (s // 2)
                    if dungeon.tiles[iy][ix] != WATER:
                        continue
                dungeon.tiles[cy][cx] = WATER
    bt = dict(getattr(dungeon, 'bridge_tiles', None) or {})
    for t in site['bridge']:
        bt[tuple(t)] = site['axis']
        (getattr(dungeon, 'traps', {}) or {}).pop(tuple(t), None)
    dungeon.bridge_tiles = bt


# ---------------------------------------------------------------------------
# The game's side
# ---------------------------------------------------------------------------

SPEECH_MS = 3200


class BlackKnightMixin:
    """Spawn, the per-turn tick (lines, the sword, the torso), the step-past
    swap and the floating line over him."""

    def _black_knight_state(self) -> dict:
        st = getattr(self, '_black_knight', None)
        if not isinstance(st, dict):
            st = {'floor': None, 'spawned': False, 'outcome': None, 'sword_dropped': False}
            self._black_knight = st
        return st

    def _black_knight_rng(self) -> random.Random:
        r = getattr(self, '_bk_rng', None)
        if r is None:
            r = self._bk_rng = random.Random()      # its own stream: lines never shift the game's dice
        return r

    def _black_knights(self) -> list:
        return [m for m in self.monsters if is_black_knight(m) and m.alive]

    def _maybe_spawn_black_knight(self, level: int):
        st = self._black_knight_state()
        if st.get('spawned') or st.get('floor') != level:
            return
        if self._black_knights():
            return
        from geom import all_occupied_tiles
        taken = set(all_occupied_tiles(self.monsters))
        taken |= self._occupants()        # the hero, pets and escorts
        site = find_site(self.dungeon, (self.player.x, self.player.y), random,
                         taken=taken, length=int(data()['bridge_length']))
        if site is not None:
            build_bridge(self.dungeon, site)
            spot = site['knight']
        else:
            spot = self._free_spawn_tile(taken)
            if spot is None:
                return
        k = BlackKnight(monster_defn(), *spot)
        k.root()
        self.monsters.append(k)
        st['spawned'] = True
        st['site'] = site['kind'] if site else 'room'

    # ---- lines ------------------------------------------------------------

    def _black_knight_say(self, k, text: str, kind: str = 'warning'):
        self.add_message(f'The Black Knight: "{text}"', kind)
        try:
            import pygame
            now = pygame.time.get_ticks()
        except Exception:
            now = 0
        self._bk_speech = {'text': text, 'knight': k, 'until': now + SPEECH_MS,
                           'turn': getattr(self, 'turn_count', 0)}

    def _black_knight_next(self, k, pool: str) -> str:
        """Lines from a pool in order, round and round."""
        d = data()
        lines = d[pool]
        said = k.__dict__.setdefault('_bk_said', {})
        i = said.get(pool, 0)
        said[pool] = i + 1
        return lines[i % len(lines)]

    # ---- the tick -----------------------------------------------------------

    def _black_knight_tick(self, end: bool = False):
        """Before the world moves: what the player's action did to him.
        After: what the world did, his parting shouts, the torso's bite, and
        the end of the one-limb-per-action lock."""
        for k in self._black_knights():
            self._black_knight_events(k)
            if end:
                self._black_knight_presence(k)
                k._bk_locked = False

    def _black_knight_events(self, k):
        d = data()
        events, k._bk_events = list(k._bk_events), []
        if not events:
            return
        stages = [s for kind, s in events if kind == 'stage']
        for s in stages:
            self.add_message(d['stage_messages'][str(s)], 'combat')
            if s == 2:
                self._black_knight_drop_sword(k)
            if s == TORSO:
                self._black_knight_state()['outcome'] = 'draw'
                import deeds
                deeds.note(self, 'flag.black_knight_draw', source='black_knight', unique=True)
                self._log_chronicle(d['draw_chronicle'])
        if stages:
            self._black_knight_say(k, d['stage_lines'][str(stages[-1])])
            return
        if any(kind == 'teeter' for kind, _ in events):
            self.add_message(d['teeter'], 'combat')
            self._black_knight_say(k, self._black_knight_next(k, 'teeter_lines'))
            return
        hits = [s for kind, s in events if kind == 'hit']
        if hits and self._black_knight_rng().random() < float(d['line_chance_on_hit']):
            pool = d['hit_lines'][str(hits[-1])]
            self._black_knight_say(k, self._black_knight_rng().choice(pool))

    def _black_knight_presence(self, k):
        """First sight, parting shouts, the torso's bite."""
        d = data()
        p = self.player
        dist = max(abs(k.x - p.x), abs(k.y - p.y))
        seen = (k.x, k.y) in getattr(self, 'visible', set())
        if not k._bk_greeted:
            if seen:
                k._bk_greeted = True
                try:
                    p.known_monster_ids.add(k.kind)
                except AttributeError:
                    pass
                self._black_knight_say(k, d['greet'])
                import deeds
                deeds.note(self, 'met.black_knight', source='black_knight', unique=True)
                self._log_chronicle(d['greet_chronicle'])
            return
        if dist <= 2:
            k._bk_engaged = True
            if (k.defeated and dist == 1
                    and self._black_knight_rng().random() < float(d['torso_bite_chance'])):
                self.add_message(d['torso_bite'], 'info')
            return
        if k._bk_engaged and dist >= 4 and dist <= 12:
            k._bk_engaged = False
            pool = 'torso_leave_lines' if k.defeated else 'walk_away_lines'
            self._black_knight_say(k, self._black_knight_next(k, pool))

    # ---- the sword ------------------------------------------------------------

    def _black_knight_drop_sword(self, k):
        st = self._black_knight_state()
        if st.get('sword_dropped'):
            return
        from items import load_items, copy_at
        tpl = next((i for i in load_items('weapon') if i.id == data()['sword_id']), None)
        if tpl is None:
            return
        spot = self._black_knight_sword_tile(k)
        sword = copy_at(tpl, *spot)
        sword.identified = False
        self.ground_items.append(sword)
        st['sword_dropped'] = True
        self.add_message(data()['sword_drop'], 'loot')

    def _black_knight_sword_tile(self, k) -> tuple:
        """A bridge tile beside him, the one the hero is not on if it can be,
        else any open tile beside him."""
        bt = getattr(self.dungeon, 'bridge_tiles', None) or {}
        near = [(k.x + dx, k.y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                                    (1, 1), (1, -1), (-1, 1), (-1, -1))]
        me = (self.player.x, self.player.y)
        occupied = {(m.x, m.y) for m in self.monsters if m.alive and m is not k}
        for pool in ([t for t in near if t in bt and t != me],
                     [t for t in near if t in bt],
                     [t for t in near if self.dungeon.is_walkable(*t) and t != me and t not in occupied],
                     [t for t in near if self.dungeon.is_walkable(*t)]):
            if pool:
                return pool[0]
        return me

    # ---- the torso: walk round him -----------------------------------------------

    def _black_knight_step_past(self, k) -> None:
        """Walking into the torso swaps places with it: he never blocks."""
        ox, oy = self.player.x, self.player.y
        self.player.x, self.player.y = k.x, k.y
        k.place(ox, oy)
        self.add_message("You step around the Black Knight.", 'info')
        self._black_knight_say(k, self._black_knight_next(k, 'torso_pass_lines'))
        k._bk_engaged = True
        self._refresh_fov()
        self._advance_turn()

    # ---- the floating line -------------------------------------------------------

    def _draw_black_knight_speech(self):
        sp = getattr(self, '_bk_speech', None)
        if not sp:
            return
        import pygame
        if pygame.time.get_ticks() > sp['until'] and getattr(self, 'turn_count', 0) > sp['turn']:
            self._bk_speech = None
            return
        k = sp['knight']
        if k not in self.monsters or (k.x, k.y) not in self.visible:
            return
        from fantasy_ui import get_font
        font = get_font('body', 16, bold=True)
        sx, sy = self.renderer.world_to_screen(k.x, k.y)
        T = self.renderer.map_tile_size
        surf = font.render(sp['text'], True, (255, 236, 170))
        pad = 4
        w, h = surf.get_width() + pad * 2, surf.get_height() + pad * 2
        x = sx + T // 2 - w // 2
        y = sy - h - 2
        clip = self.screen.get_clip() or self.screen.get_rect()
        x = max(clip.left + 2, min(x, clip.right - w - 2))
        y = max(clip.top + 2, y)
        box = pygame.Surface((w, h), pygame.SRCALPHA)
        box.fill((12, 10, 16, 215))
        self.screen.blit(box, (x, y))
        pygame.draw.rect(self.screen, (150, 120, 60), (x, y, w, h), 1)
        self.screen.blit(surf, (x + pad, y + pad))
