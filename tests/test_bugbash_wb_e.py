"""Bug bash on the winning build, area E (2026-11-13): player journeys.

Each test plays one new feature from start to finish the way a player
would, on a real headless Game: every step is a key event through
``Game.handle_event``, then ``update()`` and ``render()``, as the game loop
does. Quizzes are answered by pressing the number of the right (or a wrong)
choice. The messages the game printed are read back at each step.

A test that pins a bug names it (WB-Enn in the bug bash report). Unit tests
cannot say whether any of it feels right: that is Brandon's play-test.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

SIZE = (1600, 900)


# ---------------------------------------------------------------------------
# The driver: a player at the keyboard
# ---------------------------------------------------------------------------

class Hero:
    """Drives a real Game through its key handler, a frame at a time."""

    def __init__(self, g):
        self.g = g
        self._mark = len(g.msg_log.entries)
        self.errors = []

    # -- frames and keys ----------------------------------------------------
    def frame(self, dt=1 / 30):
        self.g.update(dt)
        self.g.render()

    def key(self, k, uni='', mod=0, frames=1):
        if isinstance(k, str):
            uni = uni or k
            k = getattr(pygame, f'K_{k.lower()}') if len(k) == 1 and k.isalnum() else k
        if uni and uni.isalpha() and uni.isupper():
            mod |= pygame.KMOD_SHIFT
        self.g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=k, unicode=uni,
                                               mod=mod, scancode=0))
        for _ in range(frames):
            self.frame()

    def shift(self, letter):
        """Shift+<letter>, as the keyboard sends it."""
        self.key(getattr(pygame, f'K_{letter.lower()}'), uni=letter.upper(),
                 mod=pygame.KMOD_SHIFT)

    def wait(self, n=1):
        for _ in range(n):
            self.key(pygame.K_PERIOD, '.')

    def move(self, dx, dy):
        k = {(1, 0): pygame.K_RIGHT, (-1, 0): pygame.K_LEFT,
             (0, 1): pygame.K_DOWN, (0, -1): pygame.K_UP}[(dx, dy)]
        self.key(k)

    # -- the quiz -------------------------------------------------------------
    def in_quiz(self):
        from game_states import STATE_QUIZ, STATE_QUIZ_CONTEXT
        return self.g.state in (STATE_QUIZ, STATE_QUIZ_CONTEXT)

    def _settle_quiz(self):
        from quiz_engine import QuizState
        qe = self.g.quiz_engine
        for _ in range(400):
            if not self.in_quiz():
                return
            if qe.state == QuizState.ASKING and not qe.celebrating:
                return
            if qe.state == QuizState.RESULT and getattr(qe, '_result_hold', False):
                qe._result_hold_until = 0.0
                self.key(pygame.K_RETURN)
                continue
            self.frame(0.1)

    def answer(self, right=True):
        """Press the number of the right (or a wrong) choice on screen."""
        from quiz_engine import QuizState
        qe = self.g.quiz_engine
        assert self.in_quiz() and qe.state == QuizState.ASKING, (self.g.state, qe.state)
        q = qe.current_question
        choices = q.get('choices', [])
        want = str(q['answer']).strip()
        order = qe.confused_order if (qe.confused_order and
                                      len(qe.confused_order) == len(choices)) else \
            list(range(len(choices)))
        shown = [choices[i] for i in order]
        if right:
            pos = next(i for i, c in enumerate(shown) if str(c).strip() == want)
        else:
            pos = next(i for i, c in enumerate(shown) if str(c).strip() != want)
        self.key(getattr(pygame, f'K_{pos + 1}'))
        self._settle_quiz()

    def quiz(self, right, wrong=0, limit=30):
        """Answer ``right`` correctly, then ``wrong`` wrongly, as long as the
        quiz keeps asking. Returns how many were asked."""
        asked = 0
        for _ in range(limit):
            if not self.in_quiz():
                break
            if asked < right:
                self.answer(True)
            elif asked < right + wrong:
                self.answer(False)
            else:
                break
            asked += 1
        return asked

    # -- what the player read -------------------------------------------------
    def said(self):
        """Every line since the last call (and marks the place)."""
        out = [str(e[0]) for e in self.g.msg_log.entries[self._mark:]]
        self._mark = len(self.g.msg_log.entries)
        return out

    def peek(self):
        return [str(e[0]) for e in self.g.msg_log.entries[self._mark:]]


@pytest.fixture
def make_game(monkeypatch, tmp_path):
    import bones
    import layout
    import save_system
    import game_log
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    logged = []
    _orig = game_log.log_error

    def _log_error(msg, exc_info=True):
        import traceback
        logged.append((msg, traceback.format_exc() if exc_info else ''))
        return _orig(msg, exc_info)
    monkeypatch.setattr(game_log, 'log_error', _log_error)
    # Every floor the journey walks is the same every run (3.5.1). The game
    # makes each floor's random streams fresh (random.Random() with no
    # seed, from the OS), so a journey met a new map each time and failed on
    # about one in fifty ("never got there", "no room beside it" when the
    # fuller floors crowded a door). A stream made with no seed now takes
    # one from the global stream, which _make seeds: same seed, same floors,
    # whatever ran before. (random.getrandbits is the module's own
    # instance, made at import, so it is not the patched class.)
    _RealRandom = random.Random

    class _SeededRandom(_RealRandom):
        def __init__(self, x=None):
            super().__init__(random.getrandbits(64) if x is None else x)
    monkeypatch.setattr(random, 'Random', _SeededRandom)

    def _make(build=None, name='__bugbash_wb_e__', seed=7, clear=True):
        import items
        from main import Game
        from game_states import STATE_PLAYER
        from welcome_screen import SECRET_BUILDS
        if build:
            monkeypatch.setenv('PQ_QA_MODE', '1')
        random.seed(seed)
        items.bind_unique_registry(set())
        screen = pygame.display.set_mode(SIZE)
        layout.update(*SIZE)
        g = Game(screen, player_name=name,
                 secret_build=SECRET_BUILDS[build] if build else None)
        g.on_resize(*SIZE)
        g._resize_grace = 0
        if clear:
            g.monsters = []
        g.state = STATE_PLAYER
        h = Hero(g)
        h.errors = logged
        h.frame()
        h.said()
        return g, h
    return _make


# ---------------------------------------------------------------------------
# Small world helpers (they set the scene; the player's actions are keys)
# ---------------------------------------------------------------------------

_DEFS = None


def monster_def(mid):
    global _DEFS
    if _DEFS is None:
        with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
            _DEFS = json.load(f)
    return dict(_DEFS[mid], id=mid)


def open_floor(g, x, y, r=3):
    """Make the tiles round (x, y) plain floor, so a scene can be set."""
    from dungeon import FLOOR
    d = g.dungeon
    for yy in range(y - r, y + r + 1):
        for xx in range(x - r, x + r + 1):
            if 0 < xx < d.width - 1 and 0 < yy < d.height - 1:
                d.tiles[yy][xx] = FLOOR
    g._refresh_fov()


def place_monster(g, mid, dx, dy=0):
    from monster import Monster
    m = Monster(monster_def(mid), g.player.x + dx, g.player.y + dy)
    g.monsters.append(m)
    return m


def drop_here(g, item, dx=0, dy=0):
    item.x, item.y = g.player.x + dx, g.player.y + dy
    g.ground_items.append(item)
    return item


def pick(h, item, getter):
    """On a tabbed item menu: Right until the item's tab, then its letter."""
    for _ in range(10):
        lst = getter()
        if lst is not None and any(i is item for i in lst):
            break
        h.key(pygame.K_RIGHT)
    lst = getter()
    idx = next(i for i, it in enumerate(lst) if it is item)
    h.key(getattr(pygame, f'K_{chr(97 + idx)}'))


def the_sword_in_hand(h, part=''):
    """The hero's starting sword, in his hand: since 2026-11-16 he starts
    holding it (UI-1). One still in the pack is wielded through the E menu,
    as a player would."""
    import items
    g = h.g
    p = g.player
    if isinstance(p.weapon, items.Weapon) and part in (p.weapon.name or ''):
        return p.weapon
    sword = next(i for i in p.inventory if isinstance(i, items.Weapon) and part in i.name)
    h.key('e')
    pick(h, sword, g._get_equip_tab_items)
    assert p.weapon is sword
    return sword


def unequip(h, item):
    """E, Right to the Unequip tab, the worn item's letter."""
    g = h.g
    h.key('e')
    for _ in range(10):
        if g._get_equip_tab_items() is None:
            break
        h.key(pygame.K_RIGHT)
    idx = next(i for i, (_s, it) in enumerate(g.equip_menu_equipped) if it is item)
    h.key(getattr(pygame, f'K_{chr(97 + idx)}'))


def kit_select(h, item):
    """K is open: Right to the item's tab, Down to its row."""
    g = h.g
    for _ in range(8):
        slug = g._KIT_TABS[g._kit_tab][1]
        rows = g._kit_rows_for_slug(slug) if slug != 'spells' else []
        if any(it is item for _s, it in rows):
            break
        h.key(pygame.K_RIGHT)
    rows = g._kit_rows_for_slug(g._KIT_TABS[g._kit_tab][1])
    want = next(i for i, (_s, it) in enumerate(rows) if it is item)
    while g._kit_sel < want:
        h.key(pygame.K_DOWN)


def blow(h, m, right=1):
    """Walk into ``m`` (beside the hero) and answer ``right`` sums, then a
    wrong one. The lines the blow printed."""
    g = h.g
    dx = (m.x > g.player.x) - (m.x < g.player.x)
    dy = (m.y > g.player.y) - (m.y < g.player.y)
    if dx:
        h.move(dx, 0)
    else:
        h.move(0, dy)
    if h.in_quiz():
        h.quiz(right, 1)
    return h.said()


def arrive_after(g, n, mid, dx, dy=0):
    """A creature walks into view on the hero's ``n``-th turn from now
    (the scene: the turns are the game's own)."""
    real = g._advance_turn
    box = {'n': 0, 'm': None}

    def _adv(*a, **k):
        box['n'] += 1
        r = real(*a, **k)
        if box['n'] == n:
            box['m'] = place_monster(g, mid, dx, dy)
            g._refresh_fov()
        return r
    g._advance_turn = _adv
    return box


def warp(h, floor):
    """The QA build's floor warp (Shift+W, the number, Enter)."""
    g = h.g
    h.shift('W')
    for ch in str(floor):
        h.key(getattr(pygame, f'K_{ch}'), uni=ch)
    h.key(pygame.K_RETURN)
    for _ in range(6):
        if g.state != 'player':
            h.key(pygame.K_RETURN)


def stand_beside(g, m):
    occ = {(o.x, o.y) for o in g.monsters}
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        x, y = m.x + dx, m.y + dy
        if g.dungeon.is_walkable(x, y) and (x, y) not in occ:
            g.player.x, g.player.y = x, y
            g._refresh_fov()
            return
    raise AssertionError('no room beside it')


def reload(h):
    """Save, load the save as the title screen does, and play on."""
    import main
    import save_system
    g = h.g
    assert save_system.save_game(g)
    g2, note = main._restore_saved_game(g.screen, g.player_name,
                                        save_system.load_game(g.player_name))
    assert g2 is not None, note
    h.g = g2
    for _ in range(4):
        if g2.state != 'player':
            h.key(pygame.K_RETURN)
    h.said()
    return g2


def no_errors(h):
    assert not h.errors, h.errors


# ---------------------------------------------------------------------------
# The bugs this bash found (each failed before its fix)
# ---------------------------------------------------------------------------

def test_wb_e01_stopping_a_swap_says_the_old_piece_is_off(make_game):
    """A jerkin swapped for plate is off before the plate goes on. Stopped
    by a goblin, the hero stands in nothing, and the prompt and the line
    said only that the plate went back in the pack."""
    import items
    import known_by_hand as kbh
    from items import ARMOR_SLOTS
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 4)
    jerkin = items.instantiate_armor('leather', 'leather')
    plate = items.instantiate_armor('plate', 'chain_steel')
    for it in (jerkin, plate):
        kbh.learn(p, it)
        p.inventory.append(it)
    h.key('e')
    pick(h, jerkin, g._get_equip_tab_items)
    arrive_after(g, 2, 'goblin', 4)
    h.key('e')
    pick(h, plate, g._get_equip_tab_items)
    assert g.state == 'ask'
    stop = next(o for o in g._ask_data['options'] if o[0] == 'N')
    assert 'Worn Leather Jerkin' in stop[2] and 'off' in stop[2], stop
    h.said()
    h.key('n')
    said = ' '.join(h.said())
    assert p.armor_slots[ARMOR_SLOTS.index('body')] is None
    assert 'Worn Leather Jerkin is already off' in said, said
    no_errors(h)


def test_wb_e02_a_known_kind_with_no_tell_is_named_before_its_lore(make_game):
    """A studied skeleton (no tell) came into view as three lines about
    "it" with no creature named: which "it", with two in sight?"""
    import tells
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 5)
    p.studied_monster_ids.add('skeleton')
    sk = place_monster(g, 'skeleton', 3, 0)
    assert not tells.abilities(sk)
    g._refresh_fov()
    h.wait()
    said = h.said()
    lore = tells.lore_lines(sk)
    # One line that names it itself (2026-11-16: no "You know what the
    # Skeleton is made of." before it).
    assert len(lore) == 1 and lore[0] in said and lore[0].startswith('The Skeleton: '), said
    no_errors(h)


def test_wb_e03_the_emberpup_eats_one_ration_not_the_stack(make_game):
    """"The Emberpup eats your Bread Ration x4." He eats one."""
    import emberpup_encounter as E
    g, h = make_game(build='titivillus', name='Titivillus')
    warp(h, g._emberpup_state()['floor'])
    g = h.g
    bread = next(i for i in g.player.inventory if 'Bread' in i.name)
    bread.count = 4
    pup = next(m for m in g.monsters if E.is_emberpup(m))
    stand_beside(g, pup)
    h.said()
    h.move(pup.x - g.player.x, pup.y - g.player.y)
    h.key(pygame.K_RETURN)                         # his story
    h.key('1')                                     # leave him something to eat
    h.key('a')
    text = g._emberpup_text
    said = ' '.join(h.said())
    assert bread.count == 3
    assert 'x4' not in text and 'x4' not in said, (text, said)
    assert 'The Emberpup eats your Bread Ration.' in said
    no_errors(h)


def test_wb_e04_the_cloaked_emberpup_is_he_when_he_evolves():
    """"...it has become Infernodrake! The leaf cloak still hangs round his
    shoulders." The pup in the cloak is "he" throughout."""
    from pet_system import Pet
    pet = Pet('fire', 0, 0)
    pet.bloomleaf = True
    msgs = []
    while pet.stage < 2 and pet.level < 100:
        msgs += pet.gain_xp(pet._xp_to_next())
    evolved = [m for m in msgs if 'cloak' in m]
    assert len(evolved) == 2, msgs
    assert not any(' it has ' in m for m in evolved), evolved
    plain = Pet('fire', 0, 0)
    plain_msgs = []
    while plain.stage < 2 and plain.level < 100:
        plain_msgs += plain.gain_xp(plain._xp_to_next())
    assert any(' it has ' in m for m in plain_msgs)        # a Soul Sphere pet stays "it"


def test_wb_e06_a_ware_too_heavy_to_carry_is_bought_before_it_is_set_down(make_game):
    """"It is too heavy to carry with everything else, so Brannoc sets it
    down at your feet." came before "You buy the maul": set down before it
    was bought."""
    import items
    from mystery_system import build_trader
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 3)
    g.player_gold = 5000
    rock = items.instantiate_armor('plate', 'chain_steel')       # a load to carry
    rock.weight = p.get_carry_limit() - p.get_current_weight() - 1
    p.inventory.append(rock)
    import random as _r
    smith = build_trader('armourer', 10, _r.Random(5))
    smith.x, smith.y = p.x + 1, p.y
    g.ground_items.append(smith)
    h.key('y')
    assert g.state == 'shop'
    h.said()
    i = max(range(len(smith.stock)), key=lambda k: getattr(smith.stock[k], 'weight', 0)
            if getattr(smith.stock[k], 'item_class', '') != 'treasure' else -1)
    ware = smith.stock[i]
    while g._shop_selection < i:
        h.key(pygame.K_DOWN)
    h.key(pygame.K_RETURN)
    said = h.said()
    heavy = next(n for n, s in enumerate(said) if 'too heavy' in s)
    bought = next(n for n, s in enumerate(said) if s.startswith('You buy'))
    assert bought < heavy, said
    assert ware in g.ground_items
    no_errors(h)


def test_wb_e05_a_song_title_in_a_shout_is_not_a_second_quote():
    """Zombie Bang Chan: ""Thunderous"! Stop nagging me..." read as an
    empty quote and then a stray one."""
    from game_stray_kids import StrayKidsMixin
    from monster import Monster

    class _G:
        _stray_kids_say = StrayKidsMixin._stray_kids_say
        _stray_kids_line = staticmethod(StrayKidsMixin._stray_kids_line)

        def __init__(self):
            self.lines = []

        def add_message(self, text, kind='info'):
            self.lines.append(text)
    g = _G()
    m = Monster(monster_def('sk_zombie_bang_chan'), 0, 0)
    g._stray_kids_say(m, '"Thunderous"! Stop nagging me to go to bed!')
    line = g.lines[-1]
    assert line.count('"') == 2 and '""' not in line, line
    assert "'Thunderous'" in line


# ---------------------------------------------------------------------------
# The journeys
# ---------------------------------------------------------------------------

def path_step(h, tx, ty):
    """One step along the shortest walkable path toward a tile beside
    (tx, ty), round the creatures in the way. False when there is none."""
    from collections import deque
    g = h.g
    p = g.player
    d = g.dungeon
    blocked = {(m.x, m.y) for m in g.monsters if getattr(m, 'alive', False)}
    goal = {(tx + dx, ty + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
    start = (p.x, p.y)
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur in goal:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt in prev or nxt in blocked or not d.is_walkable(*nxt):
                continue
            prev[nxt] = cur
            q.append(nxt)
    else:
        return False
    step = cur
    while prev[step] != start and prev[step] is not None:
        step = prev[step]
    if step == start:
        return True
    h.move(step[0] - p.x, step[1] - p.y)
    return True


def shop_tab(h, idx):
    for _ in range(4):
        if h.g._shop_tab == idx:
            return
        h.key(pygame.K_RIGHT)


def shop_pick(h, pred):
    """Down / Up to the first row that ``pred`` accepts, then Enter."""
    g = h.g
    rows = g._trader_rows()
    want = next(i for i, r in enumerate(rows) if pred(r))
    while g._shop_selection < want:
        h.key(pygame.K_DOWN)
    while g._shop_selection > want:
        h.key(pygame.K_UP)
    h.key(pygame.K_RETURN)


def walk_beside(h, x, y):
    """Walk to (x, y); a spot the opened floor does not reach, the hero is
    set beside (the walk is not what is being tested)."""
    g = h.g
    for _ in range(80):
        p = g.player
        if max(abs(x - p.x), abs(y - p.y)) <= 1:
            return
        if not path_step(h, x, y):
            open_floor(g, x, y, 1)
            p.x, p.y = x + (1 if g.dungeon.is_walkable(x + 1, y) else -1), y
            g._refresh_fov()
            return
    raise AssertionError('never got there')


def body(g):
    from items import ARMOR_SLOTS
    return g.player.armor_slots[ARMOR_SLOTS.index('body')]


def test_journey_01_the_first_armour(make_game):
    """Floor 1: leather armour from the floor through the E menu and its
    geography quiz; dropped; a second leather goes on with no quiz; plate
    takes its turns, a goblin walks in, and the prompt is answered both
    ways."""
    import items
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 4)
    jerkin = drop_here(g, items.instantiate_armor('leather', 'leather'))
    h.key('g')
    assert h.said() == ['You pick up the Worn Leather Jerkin.']
    h.key('e')
    assert g.state == 'equip_menu'
    pick(h, jerkin, g._get_equip_tab_items)              # Right to Armor, its letter
    assert h.in_quiz() and 'GEOGRAPHY' in g.quiz_title
    assert h.quiz(2) == 2                               # light armour: two right answers
    assert body(g) is jerkin
    assert h.said()[-1] == 'You equip the Worn Leather Jerkin. AC is now 8.'
    unequip(h, jerkin)
    h.key('d')
    pick(h, jerkin, g._get_drop_tab_items)
    assert h.said() == ['You remove the Worn Leather Jerkin.', 'You drop the Worn Leather Jerkin.']
    assert jerkin in g.ground_items and body(g) is None

    second = drop_here(g, items.instantiate_armor('leather', 'leather', enchant=1, buc='blessed'), 1)
    h.move(1, 0)
    h.key('g')
    assert second in p.inventory
    h.said()
    h.key('e')
    assert g._known_by_hand_mark(second) == 'Known by Hand'
    pick(h, second, g._get_equip_tab_items)
    assert not h.in_quiz()                              # Known by Hand: no quiz
    assert h.said() == ['You have worn one of these before. On it goes.',
                        'You equip the Worn Leather Jerkin. AC is now 6.']

    plate = drop_here(g, items.instantiate_armor('plate', 'chain_steel'))
    h.key('g')
    h.said()
    h.key('e')
    pick(h, plate, g._get_equip_tab_items)
    arrive_after(g, 2, 'goblin', 3)                     # a goblin walks in mid-dressing
    assert h.quiz(4) == 4                               # heavy: four right answers
    said = h.said()
    assert said[0] == ('You start changing the Worn Leather Jerkin for the Well-Forged Steel '
                       'Plate Armor (6 turns).')
    assert 'as the Goblin comes into view' in said[-2] and said[-1] == 'Keep dressing? (Y/N)'
    assert g.state == 'ask' and body(g) is None         # the slot is empty until it is on
    assert g._ask_data['lines'][-1] == '4 turns left.'
    h.key('y')                                          # yes: keep going
    while g.state == 'ask':                              # the goblin's blow asks again
        h.key('y')
    assert body(g) is plate and g.state == 'player'
    assert any(s.startswith('The Well-Forged Steel Plate Armor is on. AC is now') for s in h.said())

    g.monsters = []
    h.key('e')
    pick(h, second, g._get_equip_tab_items)             # back to the jerkin: plate off first
    assert g.state == 'player' and body(g) is second
    h.said()
    arrive_after(g, 1, 'goblin', 3)                     # the jerkin off, then a goblin
    h.key('e')
    pick(h, plate, g._get_equip_tab_items)              # known by hand now: no quiz
    assert g.state == 'ask'
    h.said()
    h.key('n')                                          # no: stop where you are
    said = ' '.join(h.said())
    assert 'You leave the Well-Forged Steel Plate Armor in your pack.' in said
    assert 'Your Worn Leather Jerkin is already off.' in said
    assert body(g) is None and plate in p.inventory and second in p.inventory
    no_errors(h)


def test_journey_02_swaps_and_kits(make_game):
    """A mace readied with R in the Kit, S in a fight, a kit saved with
    Shift+E, changed into and renamed."""
    import items
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 4)
    sword = the_sword_in_hand(h)
    mace = items.instantiate_weapon('mace', 'iron')
    p.inventory.append(mace)
    h.key('s')
    assert 'Ready a weapon from the Kit (K, then R)' in h.said()[-1]
    h.key('k')
    kit_select(h, mace)
    assert ('R', 'Ready') in [(a['key'], a['label']) for a in g._kit_actions()]
    h.key('r')
    assert p.readied_weapon is mace and g.state == 'kit'
    assert h.said()[-1] == 'You sling the Plain Mace at your back. S swaps it into your hand.'
    h.key(pygame.K_ESCAPE)
    place_monster(g, 'goblin', 1)
    g._refresh_fov()
    h.key('s')
    assert p.weapon is mace and p.readied_weapon is sword
    assert h.said()[0] == 'You sling the Iron Shortsword at your back and draw the Plain Mace.'
    h.key('s')
    assert p.weapon is sword and p.readied_weapon is mace
    g.monsters = []

    jerkin = items.instantiate_armor('leather', 'leather')
    p.inventory.append(jerkin)
    h.key('e')
    pick(h, jerkin, g._get_equip_tab_items)
    h.quiz(2)
    h.said()
    h.shift('E')
    assert g.state == 'loadouts'
    h.key(pygame.K_RETURN)
    assert h.said() == ['Kit One is empty. Dress as you like, then S saves it.']
    h.key('s')
    assert h.said() == ['Kit One saved: 3 pieces.']
    h.key('n')
    for ch in 'Iron':
        h.key(getattr(pygame, f'K_{ch.lower()}'), uni=ch)
    h.key(pygame.K_RETURN)
    assert g._kits()[0]['name'] == 'Iron'
    assert g._kit_lines(0) == [('Weapon', 'Iron Shortsword'), ('Readied', 'Plain Mace'),
                               ('Body', 'Worn Leather Jerkin')]
    h.key(pygame.K_ESCAPE)
    unequip(h, jerkin)
    h.key('s')
    h.said()
    h.shift('E')
    h.key('1')
    h.key(pygame.K_RETURN)
    assert g.state == 'ask' and g._ask_data['title'] == 'Change Into Iron?'
    assert g._ask_data['lines'] == ['Changes: Weapon 1 turn, Body 1 turn.',
                                    'Every piece is in your pack and known by hand: no quizzes.']
    h.key('y')
    said = h.said()
    assert said[0] == 'You start changing into Iron (2 turns).' and said[-1] == 'You are dressed in Iron.'
    assert p.weapon is sword and p.readied_weapon is mace and body(g) is jerkin
    no_errors(h)


def test_journey_03_the_arsenal(make_game):
    """QA Shift+T: silver dust worked into a sword with Shift+C and worn
    off in a fight; fire oil thrown at a troll; Press set with Shift+S;
    the earplugs put in from the Kit."""
    import counters
    import items
    import stance
    g, h = make_game(build='titivillus', name='Titivillus')
    p = g.player
    open_floor(g, p.x, p.y, 5)
    h.shift('T')
    assert h.said()[-1].startswith('[QA] The arsenal:')
    h.shift('I')
    sword = the_sword_in_hand(h, 'ongsword')
    h.said()
    h.shift('C')
    assert g.state == 'quaff_menu'
    dust = next(i for i in g.quaff_menu_items if i.name == 'Silver Dust')
    h.key(getattr(pygame, f'K_{chr(97 + g.quaff_menu_items.index(dust))}'))
    assert h.said()[0] == ('You work the Silver Dust into your Iron Longsword. It is silvered '
                           'for the next 12 blows that land.')
    wolf = place_monster(g, 'werewolf', 1)
    wolf.hp = wolf.max_hp = 99999
    g._refresh_fov()
    worn_off = None
    for n in range(30):
        if any('wears off' in s for s in blow(h, wolf, 1)):
            worn_off = n
            break
    assert worn_off is not None and getattr(sword, 'coating', None) is None
    g.monsters = []

    troll = place_monster(g, 'troll', 3)
    troll.hp = troll.max_hp = 500
    g._refresh_fov()
    h.said()
    h.key('t')
    oil = next(i for i in p.inventory if 'Fire Oil' in i.name)
    pick(h, oil, g._get_throw_tab_items)
    assert g.state == 'target' and (g.target_cursor_x, g.target_cursor_y) == (troll.x, troll.y)
    assert h.said()[-1].startswith('Throw Flask of Fire Oil')
    h.key(pygame.K_RETURN)
    said = h.said()
    assert said[0].startswith('The Flask of Fire Oil bursts over the Troll!')
    assert troll.has_effect('burning') and troll.hp < 500

    h.shift('S')
    assert stance.of(p) == 'press' and '+30% damage' in h.said()[0]
    troll.x, troll.y = p.x + 1, p.y
    assert any(s.startswith('Chain x') for s in blow(h, troll, 2))
    h.shift('S')
    assert stance.of(p) == 'guard'
    h.shift('S')
    assert stance.of(p) == 'neutral'
    g.monsters = []

    plugs = next(i for i in p.inventory if i.name == 'Beeswax Earplugs')
    h.key('k')
    kit_select(h, plugs)
    assert ('A', 'Put In') in [(a['key'], a['label']) for a in g._kit_actions()]
    h.said()
    h.key('a')
    assert counters.ears_stopped(p)
    assert 'press it into your ears' in h.said()[0]
    no_errors(h)


def test_journey_04_knowing_a_monster(make_game):
    """An unstudied skeleton hit with a sword (felt lines only), killed,
    its corpse studied; the next one is named, told on sight and opens its
    Bestiary page."""
    import items
    import tells
    g, h = make_game()
    p = g.player
    p.hp = p.max_hp = 400
    open_floor(g, p.x, p.y, 5)
    sword = the_sword_in_hand(h)
    sk = place_monster(g, 'skeleton', 1)
    g._refresh_fov()
    h.said()
    causes = ('a cutting blow', 'a point', 'a crushing blow', 'holy power', 'resists')
    felt = []
    for _ in range(40):
        if not sk.alive:
            break
        felt += blow(h, sk, 2)
    assert not sk.alive
    assert not any(c in s for s in felt for c in causes), felt
    assert any(s in felt for s in ("It's not very effective...", 'The Skeleton barely notices.',
                                   'Barely a mark on the Skeleton.', 'The Skeleton takes little of it.',
                                   'The Skeleton hardly flinches.',
                                   'That did less to the Skeleton than it should have.'))
    corpse = next(i for i in g.ground_items if isinstance(i, items.Corpse))
    h.move(corpse.x - p.x, corpse.y - p.y)
    h.said()
    h.key('i')
    entry = next(n for n, e in enumerate(g.identify_menu_items) if e[0] is corpse)
    h.key(getattr(pygame, f'K_{chr(97 + entry)}'))
    assert h.in_quiz() and g.quiz_title == 'STUDYING SKELETON CORPSE  --  PHILOSOPHY'
    h.quiz(3)
    assert 'You understand the Skeleton now.' in h.said()
    while g.state != 'player':
        h.key(pygame.K_ESCAPE)

    sk2 = place_monster(g, 'skeleton', 3)
    g._refresh_fov()
    h.wait()
    said = h.said()
    assert said[1:] == tells.lore_lines(sk2) and said[1].startswith('The Skeleton: ')
    sk2.x, sk2.y = p.x + 1, p.y
    named = blow(h, sk2, 2)
    assert any(('a point' in s.lower() or 'a cutting blow' in s.lower()) for s in named), named
    h.key('o')
    assert g.state == 'target'
    h.key(pygame.K_RETURN)
    assert g.state == 'encyclopedia'
    no_errors(h)


def test_journey_04b_recall_lore_is_a_random_hint(make_game):
    """Recall Lore (N) with a zombie in view (Brandon, 2026-11-14: "a Trivia
    quiz that gives a random hint, doesn't do anything with monsters you can
    see and is not targeted"): each chain brings a hint of its own tier, kept
    in the Lore Hints journal, and the zombie is no better known for it."""
    import family_lore
    g, h = make_game(build='titivillus', name='Titivillus')
    p = g.player
    open_floor(g, p.x, p.y, 5)
    zombie = place_monster(g, 'zombie', 3)
    zombie.add_effect('paralyzed', 200)
    g._refresh_fov()
    with open(os.path.join(ROOT, 'data', 'hints.json'), encoding='utf-8') as f:
        pool = json.load(f)
    before = family_lore.knowledge(p, 'zombie')
    for chain in (1, 2, 3, 4, 5):
        p.recall_lore_cooldown = 0
        h.key('n')
        assert h.said()[-1] == 'You close your eyes and search your memory...'
        h.quiz(chain, 1)
        assert g.state == 'hint'
        assert g._lore_hint_chain == chain
        assert g._lore_hint_text in pool[str(chain)]
        assert g._lore_hint_text in g._recalled_hints
        h.key(pygame.K_SPACE)
    assert family_lore.knowledge(p, 'zombie') == before
    assert 'zombie' not in p.studied_monster_ids
    assert 'zombie' not in p.lore_known_monster_ids
    no_errors(h)


def test_journey_04c_the_wand_of_probing_teaches_the_kind(make_game):
    """Z, the Wand of Probing on a zombie (Brandon, 2026-11-14: probing
    counts as studying the kind): the read-out, then "You learn the ways of
    the Zombie.", and the kind is KNOWN and counts once for the restless
    dead. A second probe reads it again and teaches nothing more."""
    import family_lore
    import items
    g, h = make_game(name='__wb_e_probe__')
    p = g.player
    open_floor(g, p.x, p.y, 5)
    zombie = place_monster(g, 'zombie', 3)
    zombie.add_effect('paralyzed', 200)
    g._refresh_fov()
    wand = items.make_item_by_id('wand', 'wand_of_probing')
    wand.charges = wand.max_charges = 5
    p.inventory = [i for i in p.inventory if not isinstance(i, items.Wand)] + [wand]
    assert family_lore.knowledge(p, 'zombie') == family_lore.UNKNOWN
    score = family_lore.score(p, 'restless_dead')
    for probe in (1, 2):
        h.key('z')
        h.key(pygame.K_RETURN)
        assert h.in_quiz(), g.state
        h.quiz(1)
        said = h.said()
        assert any(f'The Zombie: {zombie.hp}/{zombie.max_hp} HP.' == s for s in said), said
        assert any(s.startswith('Weak To: ') for s in said), said
        assert ('You learn the ways of the Zombie.' in said) == (probe == 1), said
        assert family_lore.knowledge(p, 'zombie') == family_lore.KNOWN
        assert family_lore.score(p, 'restless_dead') == score + 1
        assert 'zombie' in p.studied_monster_ids and 'zombie' in p.lore_known_monster_ids
        while g.state != 'player':
            h.key(pygame.K_ESCAPE)
    no_errors(h)


def test_journey_05_the_smith(make_game):
    """Brannoc (QA $): his counter bought, the sword reforged into a mace
    and silvered, a cloak lined, a special order placed and collected at
    his next stall, and a sale on the buying visit at the trade-in rate."""
    import items
    import traders
    from mystery_system import MerchantNPC
    g, h = make_game(build='titivillus', name='Titivillus')
    p = g.player
    open_floor(g, p.x, p.y, 6)
    g.player_gold = 6000
    h.shift('I')
    sword = the_sword_in_hand(h, 'ongsword')
    cloak = items.instantiate_armor('cloak', 'linen')
    p.inventory.append(cloak)
    h.key('e')
    pick(h, cloak, g._get_equip_tab_items)
    h.quiz(2)
    h.key('$')
    assert 'Brannoc the armourer' in h.said()[-1]
    smith = next(m for m in g.ground_items if isinstance(m, MerchantNPC) and m.kind == 'armourer')
    walk_beside(h, smith.x, smith.y)
    h.said()
    h.key('y')
    assert g.state == 'shop' and g._shop_merchant is smith
    said = h.said()
    assert any(s.startswith('Brannoc: "Where you\'re going') for s in said), said
    counter = next(i for i, it in enumerate(smith.stock) if getattr(it, '_counter', None))
    ware = smith.stock[counter]
    shop_pick(h, lambda r: r == counter)
    assert any(s.startswith('You buy ') for s in h.said())
    assert ware in p.inventory or ware in g.ground_items

    shop_tab(h, 2)
    shop_pick(h, lambda r: r == 'reforge')
    shop_pick(h, lambda r: getattr(r, 'name', '') == 'Iron Mace')
    assert p.weapon is sword and sword.id == 'iron_mace'
    assert h.said()[0].startswith('Brannoc heats your Iron Longsword white and beats it into an Iron Mace.')
    shop_pick(h, lambda r: r == 'silvering')
    assert g._display_name(sword) == 'Silvered Iron Mace'
    h.said()
    shop_pick(h, lambda r: r == 'lining')
    shop_pick(h, lambda r: isinstance(r, tuple) and r[1] == 'fire')
    assert 'lines your Rough Cloth Cloak' in h.said()[0]     # linen's disguise (round 3)

    plan = g._trader_plan()
    nxt = traders.next_stall(plan, 'armourer', g.dungeon_level)
    shop_pick(h, lambda r: r == 'special_order')
    shop_pick(h, lambda r: True)                         # the first metal
    shop_pick(h, lambda r: True)                         # the first shape
    order = plan['orders'][0]
    assert order['collect'] == nxt
    assert f"floor {nxt}" in h.said()[0]
    h.key(pygame.K_ESCAPE)

    warp(h, nxt)
    g = h.g
    p = g.player
    assert any('Your ' + order['name'] + ' is waiting for you there.' in s for s in h.said())
    stall = next(m for m in g.ground_items if isinstance(m, MerchantNPC))
    assert stall.person == 'Brannoc'
    walk_beside(h, stall.x, stall.y)
    h.said()
    h.key('y')
    assert any(order['name'] in s and 'Made as you asked' in s for s in h.said())
    got = next(i for i in p.inventory + g.ground_items if g._bare_name(i) == order['name'])
    assert not plan['orders']
    cheap = min((i for i, it in enumerate(stall.stock) if getattr(it, 'item_class', '') != 'treasure'),
                key=lambda i: stall.prices[i])
    shop_tab(h, 0)
    shop_pick(h, lambda r: r == cheap)
    h.said()
    shop_tab(h, 1)
    shield = next(i for i in p.inventory if isinstance(i, items.Shield))
    plain, _why = g._trader_offer(shield)
    extra = g._trade_in_extra(shield, plain)
    assert extra > 0
    shop_pick(h, lambda r: r is shield)
    assert h.said()[0].endswith(f"for {plain + extra:,} gold, {extra:,} of it as a trade-in.")
    assert got is not None
    no_errors(h)


def test_journey_06_the_altar(make_game):
    """Rededicate a Gift at three altars: chain 2 moves nothing, chain 3
    one point, chain 5 two; the altar heard once."""
    from dungeon import ALTAR
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 5)
    g.player_gold = 2000
    p.apply_stat_bonus('STR', 4)                         # what a gate gift and meals gave him
    moved = []
    for n, chain in enumerate((2, 3, 5)):
        ax = p.x + (2 if n else 0)
        g.dungeon.tiles[p.y][ax] = ALTAR
        while p.x != ax:
            h.move(1, 0)
        h.said()
        h.key(pygame.K_BACKSLASH, '\\')
        assert g.state == 'prayer_menu'
        row = next(i for i, c in enumerate(g._prayer_choices()) if c['id'] == 'rededicate')
        assert g._prayer_choices()[row]['enabled']
        h.key(getattr(pygame, f'K_{row + 1}'))
        assert g._ask_data['title'] == 'Rededication: Give Back'
        h.key('s')                                       # Strength
        assert g._ask_data['title'] == 'Rededication: Take for Strength'
        h.key('d')                                       # Dexterity
        assert h.in_quiz() and g.quiz_title == 'THE ALTAR  --  REDEDICATION'
        before = (p.STR, p.DEX)
        h.quiz(chain, 1)
        moved.append((before[0] - p.STR, p.DEX - before[1]))
        assert g.state == 'player'
    assert moved == [(0, 0), (1, 1), (2, 2)]
    h.key(pygame.K_BACKSLASH, '\\')
    row = next(c for c in g._prayer_choices() if c['id'] == 'rededicate')
    assert not row['enabled'] and 'heard your rededication' in row['asks']
    no_errors(h)


def test_journey_07_the_emberpup(make_game):
    """Old Nickel (QA Shift+L) watched, warned, fought, his cloak taken;
    the pup fed, too soon, fed twice more, another cloak tried, the
    Bloomleaf Cloak given, "I choose you!", named, evolved; saved and
    loaded on the way."""
    import emberpup_encounter as E
    import items
    g, h = make_game(build='titivillus', name='Titivillus')
    p = g.player
    open_floor(g, p.x, p.y, 6)
    h.shift('I')
    sword = the_sword_in_hand(h, 'ongsword')
    h.said()
    h.shift('L')
    nickel = next(m for m in g.monsters if E.is_wearer(m))
    h.wait(2)
    said = ' '.join(h.said())
    assert 'Old Nickel wears a cloak of broad green leaves' in said
    assert '"Mine," he hisses.' in said
    for _ in range(80):
        if not nickel.alive:
            break
        if max(abs(nickel.x - p.x), abs(nickel.y - p.y)) > 1 or (nickel.x != p.x and nickel.y != p.y):
            path_step(h, nickel.x, nickel.y)
        else:
            blow(h, nickel, 3)
    assert not nickel.alive
    cloak = next(i for i in g.ground_items if E.is_cloak(i))
    h.move(cloak.x - p.x, 0) if cloak.x != p.x else None
    h.move(0, cloak.y - p.y) if cloak.y != p.y else None
    for _ in range(4):
        if cloak in p.inventory:
            break
        h.key('g')
    assert cloak in p.inventory and g._display_name(cloak) == 'Bloomleaf Cloak'
    h.key('e')
    pick(h, cloak, g._get_equip_tab_items)               # it keeps his iron from rust
    h.quiz(9)
    assert cloak in p.worn_items() and p.is_rustproof()

    warp(h, g._emberpup_state()['floor'])
    g = h.g
    p = g.player
    bread = next(i for i in p.inventory if 'Bread' in i.name)
    bread.count = 5
    p.inventory.append(items.instantiate_armor('cloak', 'linen'))
    pup = next(m for m in g.monsters if E.is_emberpup(m))
    g.monsters = [pup]                                    # a quiet floor: only he is here

    def bump():
        stand_beside(g, pup)
        h.move(pup.x - g.player.x, pup.y - g.player.y)
    bump()
    assert g.state == 'emberpup' and g._emberpup_phase == 'story'
    h.key(pygame.K_RETURN)
    h.key('5')                                            # the cloak on his own back
    assert g._emberpup_text.startswith('The leaf cloak is on your own back. Take it off first')
    h.key(pygame.K_RETURN)
    h.key('1')
    h.key('a')
    assert g._emberpup_text.startswith('You set the Bread Ration down at the foot of his rock')
    h.key(pygame.K_RETURN)
    h.key('1')
    assert g._emberpup_text == ('The Emberpup, still eating the treat you provided, '
                                'growls and backs away as you approach.')
    h.key(pygame.K_RETURN)
    h.key('2')
    g = reload(h)                                         # saved and loaded mid-way
    p = g.player
    pup = next(m for m in g.monsters if E.is_emberpup(m))
    cloak = next(i for i in p.worn_items() if E.is_cloak(i))
    assert E.feeds(pup) == 1
    h.wait(26)
    for n, start in ((2, 'You set down the Bread Ration and step back again.'),
                     (3, 'This time he does not run.')):
        bump()
        h.key('1')
        h.key('a')
        assert g._emberpup_text.startswith(start), g._emberpup_text
        h.key(pygame.K_RETURN)
        if n == 2:
            h.key('2')
            h.wait(26)
    h.key('4')
    assert g._emberpup_text.startswith('He wants to come. But the rain is still on him')
    h.key(pygame.K_RETURN)
    h.key('2')
    h.key('k')                                           # off his back, and set down (the
    kit_select(h, cloak)                                 # Kit's D: a lore fixture beside
    h.key('d')                                           # him may take the map's D)
    h.key(pygame.K_ESCAPE)
    assert cloak in g.ground_items
    bump()
    h.key('5')                                            # any other cloak: no good
    shield = next(i for i in p.inventory if isinstance(i, items.Shield))
    assert g._emberpup_text.startswith(f'You hold your {g._bare_name(shield)} over his rock')
    assert g._emberpup_text.endswith('A cloak of leaves would turn this rain.')
    h.key(pygame.K_RETURN)
    h.key('2')
    p.x, p.y = cloak.x, cloak.y
    for _ in range(6):                                    # one thing a press: what lay there first
        if cloak in p.inventory:
            break
        h.key('g')
    assert cloak in p.inventory
    bump()
    h.key('5')
    assert g._emberpup_text.startswith("You spread the Bloomleaf Cloak over the Emberpup's rock.")
    assert E.sheltered(pup) and pup.sprite_id == 'npc_abandoned_emberpup_sheltered'
    h.key(pygame.K_RETURN)
    h.key('2')
    g = reload(h)
    pup = next(m for m in g.monsters if E.is_emberpup(m))
    assert E.sheltered(pup)
    bump()
    h.key('4')
    assert h.in_quiz() and 'ANIMAL' in g.quiz_title
    h.quiz(2)
    assert g._emberpup_text.startswith('The Emberpup looks at you for a long moment.')
    h.key(pygame.K_RETURN)
    assert g.state == 'pet_name_input'
    for _ in range(len('Emberpup')):
        h.key(pygame.K_BACKSPACE)
    for ch in 'Ember':
        h.key(getattr(pygame, f'K_{ch.lower()}'), uni=ch)
    h.key(pygame.K_RETURN)
    assert 'Ember the Emberpup will not be left behind again.' in h.said()
    pet = g.pets[-1]
    assert pet.bloomleaf and pet.sprite_id == 'emberpup_cloaked' and pet.weak_to() == ()
    msgs = []
    while pet.stage < 1:
        msgs += pet.gain_xp(pet._xp_to_next())
    assert pet.sprite_id == 'flamescale_cloaked'
    assert any('The leaf cloak still hangs round his shoulders.' in m for m in msgs)
    g = reload(h)
    pet = g.pets[-1]
    assert pet.bloomleaf and pet.sprite_id == 'flamescale_cloaked'
    h.shift('P')
    assert g.state == 'pet_menu' and g._pet_cloak_lines(pet)
    no_errors(h)


def test_journey_08_fenrirs_scraps(make_game):
    """The floor-5 scrap: 5 lb, no hint; on an ordinary altar it is only
    dropped; ten on Vidar's altar on floor 79 make the Sandal."""
    import copy
    from dungeon import ALTAR
    g, h = make_game(build='titivillus', name='Titivillus')
    h.shift('I')
    warp(h, 5)
    g = h.g
    p = g.player
    g.monsters = []                                       # a quiet floor
    scrap = next(i for i in g.ground_items if getattr(i, 'id', '') == 'leather_scrap')
    assert scrap.weight == 5.0 and scrap.buc != 'cursed'
    p.x, p.y = scrap.x, scrap.y
    g._refresh_fov()
    h.said()
    h.key('g')
    assert h.said() == ['You pick up the Leather Scrap.']
    for word in ('shoe ', 'collect', 'Vidar', 'ten', 'north'):
        assert word not in scrap.lore.replace('shoe leather', ''), word
    g.dungeon.tiles[p.y][p.x] = ALTAR
    h.key('d')
    assert g.state == 'drop_menu'
    pick(h, scrap, g._get_drop_tab_items)
    assert h.said() == ['You drop the Leather Scrap.'] and scrap in g.ground_items
    h.key('g')
    for _ in range(9):
        p.inventory.append(copy.copy(scrap))
    warp(h, 79)
    g = h.g
    p = g.player
    g.monsters = []
    p.x, p.y = g.dungeon.vidar_altar_pos
    g._refresh_fov()
    h.said()
    h.key('d')
    assert g.state == 'drop_menu'
    one = next(i for i in p.inventory if getattr(i, 'id', '') == 'leather_scrap')
    pick(h, one, g._get_drop_tab_items)
    said = h.said()
    assert 'You empty your pack of every scrap you have carried down.' in said
    assert any(i.name == "Vidar's Sandal" for i in g.ground_items)
    assert not any(getattr(i, 'id', '') == 'leather_scrap' for i in p.inventory)
    no_errors(h)


def test_journey_09_a_caster(make_game):
    """A bolt learnt from a spellbook (R), cast in steel plate (twice the
    MP) and in leather, then a rest that meditates MP back."""
    import items
    import known_by_hand as kbh
    g, h = make_game()
    p = g.player
    open_floor(g, p.x, p.y, 6)
    book = items.make_item_by_id('spellbook', 'spellbook_fire_bolt')
    p.inventory.append(book)
    h.key('r')
    pick(h, book, g._get_scroll_tab_items)
    assert h.in_quiz() and 'GRAMMAR' in g.quiz_title
    h.quiz(5)
    assert h.said()[-1] == 'You master the arcane text! Fire Bolt learned! (costs 6 MP)'
    plate = items.instantiate_armor('plate', 'chain_steel')
    jerkin = items.instantiate_armor('leather', 'leather')
    for it in (plate, jerkin):
        kbh.learn(p, it)
        p.inventory.append(it)
    h.key('e')
    pick(h, plate, g._get_equip_tab_items)
    troll = place_monster(g, 'troll', 3)
    troll.hp = troll.max_hp = 5000
    g._refresh_fov()
    costs = []
    for wear in (None, jerkin):
        if wear is not None:
            h.key('e')
            pick(h, wear, g._get_equip_tab_items)
        p.mp = p.max_mp
        h.key('m')
        assert g.state == 'spell_menu'
        h.key('a')
        assert g.state == 'target'
        h.key(pygame.K_RETURN)
        h.quiz(3, 1)
        assert any('A bolt of fire strikes the Troll' in s for s in h.said())
        costs.append(p.max_mp - p.mp)
    assert costs == [12, 6]
    g.monsters = []
    p.mp = 0
    for _ in range(20):
        h.wait()
    assert p.mp >= 1 and 'You meditate. (+1 MP)' in h.said()
    no_errors(h)


def test_journey_10_the_stray_kids_stage(make_game):
    """QA Shift+K: the idol touched, the band beaten to the last in the
    dance-off (2026-11-14: it replaced the fight), the photo taken, read in
    a fight on the way back."""
    import items
    import stray_kids
    g, h = make_game(build='titivillus', name='Titivillus')
    h.shift('I')
    warp(h, 9)
    g = h.g
    p = g.player
    g.monsters = [m for m in g.monsters if getattr(m, 'is_allied', False)]
    sword = the_sword_in_hand(h, 'ongsword')
    h.shift('K')
    ix, iy = g._stray_kids_state()['pos']
    if ix != p.x and iy != p.y:
        p.x = ix                                          # stand in line with it
        g._refresh_fov()
    h.said()
    h.move((ix > p.x) - (ix < p.x), (iy > p.y) - (iy < p.y))
    assert 'walk into it again' in h.said()[-1]
    h.move((ix > p.x) - (ix < p.x), (iy > p.y) - (iy < p.y))
    assert g._on_stray_kids_stage()
    assert h.said()[-1] == 'The stage door is the way out (> on it).'
    # The dance-off, every round on time (the driver of the Stray Kids'
    # own journey: tests/test_stray_kids_journey.py).
    from test_stray_kids_journey import fake_clock, to_the_stage, win_the_dance_off
    heard = to_the_stage(h)
    heard += win_the_dance_off(h, fake_clock(g))
    assert not stray_kids.the_band(g.monsters)
    said = ' '.join(heard)
    assert '""' not in said                               # WB-E05
    assert 'An Autographed Stray Kids Photo lies where the band last stood.' in said
    photo = next(i for i in g.ground_items if getattr(i, 'id', '') == stray_kids.photo_id())
    while (p.x, p.y) != (photo.x, photo.y):
        path_step(h, photo.x, photo.y)
        if abs(photo.x - p.x) + abs(photo.y - p.y) == 1:
            h.move(photo.x - p.x, photo.y - p.y)
    h.key('g')
    assert any(getattr(i, 'id', '') == stray_kids.photo_id() for i in p.inventory)
    from dungeon import STAIRS_DOWN
    d = g.dungeon
    door = next((x, y) for y in range(d.height) for x in range(d.width) if d.tiles[y][x] == STAIRS_DOWN)
    p.x, p.y = door
    g._refresh_fov()
    h.said()
    h.key(pygame.K_PERIOD, '>')
    g = h.g
    p = g.player
    assert g.dungeon_level == 9
    assert h.said()[0].startswith('You slip out through the stage door.')
    open_floor(g, p.x, p.y, 3)
    g.monsters = [m for m in g.monsters if getattr(m, 'is_allied', False)]
    import decor
    # In plain sight: a dark corridor shows only the tiles beside the hero,
    # and a pillar may block one side.
    spot = next(((dx, dy) for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 0), (-1, 0), (0, 1), (0, -1))
                 if (p.x + dx, p.y + dy) in g.visible and g.dungeon.is_walkable(p.x + dx, p.y + dy)
                 and not decor.fixture_at(g.dungeon, p.x + dx, p.y + dy)), None)
    assert spot is not None
    gob = place_monster(g, 'goblin', *spot)
    g._refresh_fov()
    h.key('r')
    photo = next(i for i in g.scroll_menu_items if getattr(i, 'id', '') == stray_kids.photo_id())
    pick(h, photo, g._get_scroll_tab_items)
    h.quiz(3)
    said = h.said()
    assert 'The Goblin stops to watch the show.' in said, said
    assert gob.has_effect('stunned')
    h.wait(10)
    assert not any(stray_kids.is_star(m) for m in g.monsters)
    no_errors(h)
