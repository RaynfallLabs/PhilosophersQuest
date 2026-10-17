"""The fourth bug bash (2026-10-16), combat angle (fix batch F1). Each test
names what was wrong and the finding ID from
_bugbash_2026_10_16/combat/FINDINGS.md.

Behaviour tests on a real headless Game wherever the bug lives in the game
loop. The feel of these fixes in play is a play-test question: Claude cannot
drive Pygame.
"""
import copy
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import items  # noqa: E402

_SCREEN = None
_DEFS = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=5, name='__test_bug_bash_4_combat__', build=None):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    g = Game(_screen(), player_name=name, secret_build=build)
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER          # past any opening story popup
    return g


def _mdef(kind):
    global _DEFS
    if _DEFS is None:
        with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
            _DEFS = json.load(f)
    d = dict(_DEFS[kind])
    d.setdefault('id', kind)
    return d


def _open_floor(g, r=4):
    from dungeon import FLOOR
    for yy in range(g.player.y - r, g.player.y + r + 1):
        for xx in range(g.player.x - r, g.player.x + r + 1):
            if g.dungeon.in_bounds(xx, yy):
                g.dungeon.tiles[yy][xx] = FLOOR


def _spawn(g, kind, dx=1, dy=0, **attrs):
    from monster import Monster
    from dungeon import FLOOR
    x, y = g.player.x + dx, g.player.y + dy
    g.dungeon.tiles[y][x] = FLOOR
    m = Monster(_mdef(kind), x, y)
    for k, v in attrs.items():
        setattr(m, k, v)
    m._aware = True
    g.monsters.append(m)
    return m


def _plain(it):
    it = copy.copy(it)
    it.cursed = False
    it.buc = 'uncursed'
    it.buc_known = True
    it.id_level = 5
    return it


def _texts(g, n=20):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _right(g):
    return str(g.quiz_engine.current_question['answer']).strip()


def _wrong(g):
    q = g.quiz_engine.current_question
    ans = str(q['answer']).strip()
    for c in q.get('choices', []) or q.get('options', []) or []:
        if str(c).strip() != ans:
            return str(c)
    return ans + 'XXX'


def _answer(g, seq, max_steps=200):
    """Answer right/wrong per seq, then wrong until the quiz ends."""
    from quiz_engine import QuizState
    qe = g.quiz_engine
    it = iter(seq)
    steps = 0
    while qe.active and steps < max_steps:
        steps += 1
        if qe.state == QuizState.ASKING:
            qe.answer(_right(g) if next(it, False) else _wrong(g))
        qe.update(5.0)


# ---------------------------------------------------------------- C01
def test_c01_a_ranged_shot_spends_the_tablet_reroll():
    """A bow shot never spent the Tablet of Destinies' once-a-floor reroll,
    so an archer rerolled a wrong answer on every shot."""
    g = _game()
    p = g.player
    _open_floor(g)
    bow = _plain(items.instantiate_weapon('longbow', 'ash'))
    arrows = items.make_item_by_id('ammo', 'iron_arrow')
    arrows.count = 50
    p.inventory += [bow, arrows, items.make_item_by_id('artifact', 'tablet_of_destinies')]
    p.ranged_weapon = bow
    used = 0
    for _ in range(4):
        m = _spawn(g, 'giant_rat', dx=3, hp=10_000, max_hp=10_000)
        g._fire_ranged(m)
        _answer(g, [False, True, True])
        used += int(g.quiz_engine.reroll_was_used)
        p.status_effects.pop('reloading', None)
        g.monsters.remove(m)
    assert used == 1
    assert g._quiz_reroll_used is True


# ---------------------------------------------------------------- C02
def test_c02_first_hit_absorb_does_not_heal_a_lethal_blow():
    """The chain passive first_hit_absorb set hp = hp + dmg with the blow's
    full size, so a 60-point bite on a 5-health wearer healed them to full."""
    g = _game(seed=7)
    p = g.player
    _open_floor(g, 3)
    armor = _plain(items.instantiate_armor('leather', 'cured_leather_armor'))
    armor._chain_passives = {'first_hit_absorb': True}
    p.armor_slots[1] = armor
    p.hp = 5
    m = _spawn(g, 'giant_rat')
    m.thac0 = -99
    m.min_hit_chance = 1.0
    m.attacks = [{'name': 'Bite', 'damage': '1d2+58', 'type': 'physical'}]
    random.seed(1)
    g._do_monster_turns()
    assert any('turns aside the first blow' in t for t in _texts(g))
    assert p.hp == 5


# ---------------------------------------------------------------- C08
def test_c08_reflecting_aura_keeps_the_players_own_new_buffs():
    """The reflecting aura deleted half of EVERY status new after a blow,
    including Excalibur's life_save that the blow itself had just granted."""
    lost = hits = 0
    for i in range(30):
        g = _game(seed=100 + i)
        _open_floor(g, 3)
        p = g.player
        p.status_effects['reflecting'] = -1
        w = _plain(items.make_item_by_id('weapon', 'excalibur'))
        p.inventory.append(w)
        p.weapon = w
        p.hp = p.max_hp = 100
        m = _spawn(g, 'giant_rat')
        m.thac0 = -99
        m.min_hit_chance = 1.0
        m.attacks = [{'name': 'Bite', 'damage': '1d2+79', 'type': 'physical'}]
        random.seed(i)
        g._do_monster_turns()
        assert p.hp > 0
        if p.hp == 100:
            continue                # the bite missed (dodge)
        hits += 1
        if 'life_save' not in p.status_effects:
            lost += 1
    assert hits >= 10 and lost == 0


def _strike(g, n):
    """Answer n right, then lock in with SPACE (cancel_and_strike)."""
    from quiz_engine import QuizState
    qe = g.quiz_engine
    for _ in range(n):
        while qe.active and qe.state != QuizState.ASKING:
            qe.update(5.0)
        if not qe.active:
            break
        qe.answer(_right(g))
        qe.update(5.0)
    while qe.active and qe.state != QuizState.ASKING:
        qe.update(5.0)
    if qe.active:
        qe.cancel_and_strike()


# ---------------------------------------------------------------- C03
def test_c03_harpe_cannot_petrify_a_boss_but_still_stones_a_rat():
    """Harpe's chain-15 petrify wrote the status directly, and petrifying
    running out kills: any boss died two turns after one chain of 15."""
    for kind, stoned in (('asterion_minotaur', False), ('giant_rat', True)):
        g = _game(seed=21)
        _open_floor(g)
        p = g.player
        p.hp = p.max_hp = 1_000_000
        harpe = _plain(items.make_item_by_id('weapon', 'harpe'))
        p.inventory.append(harpe)
        p.weapon = harpe
        b = _spawn(g, kind)
        if kind == 'giant_rat':
            b.max_hp = 50              # an ordinary foe, but alive through the blow
            b.hp = 10 ** 6
        g._start_combat(b)
        _strike(g, 15)
        assert ('petrifying' in b.status_effects) is stoned, kind
        if not stoned:
            for _ in range(4):
                b.x, b.y = p.x + 1, p.y
                g._advance_turn()
            assert b.alive, kind


# ---------------------------------------------------------------- C04
def test_c04_sword_of_damocles_does_not_one_shot_a_gate_boss():
    """The Damocles auto-kill excluded only monsters TAGGED 'boss'; the gate
    bosses, seal demons and mini-bosses are flagged, so Abaddon died."""
    g = _game(seed=81)
    _open_floor(g, 3)
    p = g.player
    p.hp = p.max_hp = 10 ** 7
    w = _plain(items.make_item_by_id('weapon', 'sword_of_damocles'))
    p.inventory.append(w)
    p.weapon = w
    b = _spawn(g, 'abaddon_destroyer')
    b.thac0 = 99
    assert b._is_named_foe() and 'boss' not in b.tags
    for _ in range(10):
        g._start_combat(b)
        _strike(g, 1)
    assert b.alive and b.hp > b.max_hp // 2


# ---------------------------------------------------------------- C05
def test_c05_a_reach_weapon_does_not_strike_through_a_wall():
    """Reach was checked by distance alone: Gungnir struck a rat on the far
    side of a solid wall the player could not see through."""
    from dungeon import WALL, FLOOR
    from game_states import STATE_QUIZ
    g = _game(seed=61)
    _open_floor(g)
    p = g.player
    spear = _plain(items.make_item_by_id('weapon', 'gungnir'))
    p.inventory.append(spear)
    p.weapon = spear
    assert spear.reach >= 2
    for dy in (-1, 0, 1):
        g.dungeon.tiles[p.y + dy][p.x + 1] = WALL
    rat = _spawn(g, 'giant_rat', dx=2, hp=500, max_hp=500)
    g.dungeon.tiles[rat.y][rat.x] = FLOOR
    g._refresh_fov()
    g._open_melee_targeting()
    assert rat not in g._target_candidates
    g.target_cursor_x, g.target_cursor_y = rat.x, rat.y
    g._confirm_melee_target()
    assert g.state != STATE_QUIZ and rat.hp == 500
    # with the wall gone the same strike is offered and starts
    for dy in (-1, 0, 1):
        g.dungeon.tiles[p.y + dy][p.x + 1] = FLOOR
    g._refresh_fov()
    g._open_melee_targeting()
    assert rat in g._target_candidates
    g.target_cursor_x, g.target_cursor_y = rat.x, rat.y
    g._confirm_melee_target()
    assert g.state == STATE_QUIZ


# ---------------------------------------------------------------- C07
def test_c07_the_shattered_ankh_takes_its_constitution_with_it():
    """The Ankh of Isis (+2 CON while worn) shattered to save a life and the
    slot was simply emptied: the +2 CON and its health stayed for good."""
    g = _game(seed=41)
    p = g.player
    ankh = _plain(items.make_item_by_id('accessory', 'ankh_of_isis'))
    assert ankh.effects.get('stat') == 'CON'
    con0, mhp0 = p.CON, p.max_hp
    p.inventory.append(ankh)
    p._apply_equip(ankh)
    p.remove_from_inventory(ankh)
    assert p.CON == con0 + ankh.effects['amount']
    p.hp = 0
    g._answer_a_killing_blow()
    assert p.hp > 0 and p.amulet_slot is None
    assert any('Ankh of Isis shatters' in t for t in _texts(g))
    assert (p.CON, p.max_hp) == (con0, mhp0)
    assert p.hp == max(1, mhp0 // 2)


# ---------------------------------------------------------------- C06
def test_c06_old_floor_monsters_stop_when_the_sandals_lift_the_hero(monkeypatch):
    """The Winged Sandals' psychopomp step changed floor inside the monster
    loop; the old floor's rats kept acting on the new map, against the
    hero's new position."""
    from game_states import STATE_PLAYER
    g = _game(seed=31)
    p = g.player
    g._change_level(2, enter_from_top=True)
    g.state = STATE_PLAYER
    g.monsters = []
    g.pets = []
    _open_floor(g, 3)
    boots = _plain(items.instantiate_armor('leather_boots', 'cured_leather_armor'))
    boots._chain_passives = {'psychopomp_step': True}
    p.armor_slots[5] = boots
    p.hp = 3
    p.max_hp = max(p.max_hp, 30)
    killer = _spawn(g, 'giant_rat')
    killer.thac0 = -99
    killer.min_hit_chance = 1.0
    killer.attacks = [{'name': 'Bite', 'damage': '1d2+40', 'type': 'physical'}]
    others = []
    for dx, dy in ((-1, 0), (0, 1), (0, -1)):
        o = _spawn(g, 'giant_rat', dx=dx, dy=dy)
        o.thac0 = -99
        o.min_hit_chance = 1.0
        o.attacks = [{'name': 'Claw', 'damage': '1d2+2', 'type': 'physical'}]
        others.append(o)
    from monster import Monster
    acted = []
    real_turn = Monster.take_turn

    def spy(self, *a, **kw):
        acted.append((self, g.dungeon_level))
        return real_turn(self, *a, **kw)

    monkeypatch.setattr(Monster, 'take_turn', spy)
    random.seed(2)
    g._do_monster_turns()
    assert g.dungeon_level == 1
    assert any('psychopomp' in t for t in _texts(g))
    assert p.hp == 1
    assert acted and acted[0][0] is killer
    assert not [m for m, lvl in acted if lvl == 1], 'an old-floor monster acted on the new floor'


def test_burdened_extra_turn_is_not_spent_on_a_new_floor_or_under_a_popup(monkeypatch):
    """A Burdened step's extra dungeon turn fired after the step's own turn
    had moved the hero to another floor (the Winged Sandals) or opened a
    popup, so the new floor's monsters got a free turn."""
    from game_states import STATE_PLAYER, STATE_STORY_POPUP
    from player import Player
    monkeypatch.setattr(Player, 'is_burdened', lambda self: True)
    monkeypatch.setattr(Player, 'burden_step', lambda self: True)
    g = _game(seed=31)
    g._change_level(2, enter_from_top=True)
    g.state = STATE_PLAYER
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    _open_floor(g, 3)
    levels = []
    real = type(g)._advance_turn

    def spy(self, *a, **kw):
        levels.append(self.dungeon_level)
        return real(self, *a, **kw)

    monkeypatch.setattr(type(g), '_advance_turn', spy)
    # The step's own turn moves the hero up a floor; the extra one must not run.
    real_tick = type(g)._do_monster_turns

    def lift(self):
        if self.dungeon_level == 2:
            self._change_level(1, enter_from_top=False)
            self.state = STATE_PLAYER
            return
        return real_tick(self)

    monkeypatch.setattr(type(g), '_do_monster_turns', lift)
    g._do_move(1, 0)
    assert g.dungeon_level == 1
    assert levels == [2], levels
    # A popup opened by the step's turn: no extra turn behind it either.
    levels.clear()
    _open_floor(g, 3)
    g.monsters = []

    def popup(self):
        self.state = STATE_STORY_POPUP

    monkeypatch.setattr(type(g), '_do_monster_turns', popup)
    g._do_move(1, 0)
    assert levels == [1], levels


# ---------------------------------------------------------------- C09
def _reaching(attacks):
    from monster import _RANGED_WORDS
    return [a for a in attacks
            if a.get('ranged') or any(w in a.get('name', '').lower() for w in _RANGED_WORDS)]


def test_c09_healer_and_summoner_casters_do_not_swing_melee_from_range():
    """Healers and summoners with two attacks stood off at 2-6 tiles and
    then picked ANY attack, so the orc priest clubbed from across the room."""
    import collections
    for kind in ('orc_priest', 'cult_priest', 'imp_lord'):
        g = _game(seed=11)
        _open_floor(g, 6)
        p = g.player
        p.hp = p.max_hp = 100000
        m = _spawn(g, kind, dx=4)
        m.summon_kind = ''
        m.thac0 = -99
        c = collections.Counter()
        for _ in range(60):
            m.x, m.y = p.x + 4, p.y
            m.status_effects.clear()
            before = len(g.msg_log.entries)
            g._do_monster_turns()
            for e in g.msg_log.entries[before:]:
                for a in m.attacks:
                    if a['name'].lower() in str(e[0]).lower():
                        c[a['name']] += 1
            p.hp = p.max_hp
        distance = {a['name'] for a in _reaching(m.attacks)}
        assert distance and c, kind
        assert set(c) <= distance, (kind, dict(c))


def test_c09_every_two_attack_caster_has_an_attack_that_reaches():
    """Eight such casters had no ranged attack at all; their spells are now
    flagged ranged in monsters.json, so they cast from where they stand."""
    from monster import Monster
    bad = []
    for kind in _DEFS or json.load(open(os.path.join(ROOT, 'data', 'monsters.json'),
                                        encoding='utf-8')):
        d = _mdef(kind)
        if d.get('ai_pattern') in ('healer', 'summoner') and len(d.get('attacks') or []) > 1:
            if not _reaching(Monster(d, 0, 0).attacks):
                bad.append(kind)
    assert not bad


# ---------------------------------------------------------------- C10
def test_c10_heal_blocked_and_ruptured_monsters_do_not_heal():
    """Gae Dearg's heal_blocked was read by no monster healing path, and the
    dagger's ruptured only by regeneration: trolls regenerated, priests mended
    ruptured allies, vampires fed through both."""
    g = _game(seed=3)
    _open_floor(g, 5)
    p = g.player
    p.hp = p.max_hp = 10_000
    t = _spawn(g, 'troll', dx=3)
    assert t.regeneration > 0
    t.hp = t.max_hp // 2
    t.status_effects['heal_blocked'] = 10
    h0 = t.hp
    t.tick_effects()
    assert t.hp <= h0

    g.monsters.clear()
    pr = _spawn(g, 'orc_priest', dx=4)
    ally = _spawn(g, 'orc_priest', dx=4, dy=1)
    ally.hp = ally.max_hp // 3
    ally.status_effects['ruptured'] = 5
    a0 = ally.hp
    pr._healer_turn(p, g.dungeon, g.monsters, set())
    assert ally.hp == a0

    g.monsters.clear()
    v = _spawn(g, 'vampire')
    assert v.drain_heals_self > 0
    v.hp = v.max_hp // 2
    v.status_effects['heal_blocked'] = 50
    v.thac0 = -99
    v.min_hit_chance = 1.0
    v.attacks = [a for a in v.attacks if a.get('type') == 'drain']
    assert v.attacks
    v0 = v.hp
    random.seed(4)
    for _ in range(5):
        v.attack(p)
    assert v.hp <= v0


# ---------------------------------------------------------------- C11
def test_c11_missiles_and_smite_go_through_take_damage():
    """Magic-missile wands, the force missiles spell and Smite cut hp
    directly: they killed encounter NPCs, the Green Knight's beheading-game
    revive never fired, and a sleeper stayed asleep."""
    from monster import Monster

    def zap(g, target):
        w = items.make_item_by_id('wand', 'wand_of_magic_missile')
        w.charges = 5
        g._wand_override_target = target
        g._apply_wand_effect(w)
        g._wand_override_target = None

    g = _game(seed=93)
    p = g.player
    _open_floor(g)
    npc = Monster({'id': 'npc_traveler', 'name': 'Lost Girl', 'symbol': '@',
                   'color': [200, 200, 200], 'hp': 1, 'thac0': 20, 'speed': 0,
                   'attacks': [], 'ai_pattern': 'sessile', 'resistances': [],
                   'weaknesses': [], 'min_level': 1, 'harvest_tier': 0,
                   'harvest_threshold': 99, 'ingredient_id': None}, p.x + 2, p.y)
    npc._npc_encounter_tag = 'lost_girl'
    g.monsters.append(npc)
    zap(g, npc)
    assert npc.alive and npc.hp == 1

    g = _game(seed=94)
    _open_floor(g)
    gk = _spawn(g, 'green_knight', dx=2)
    assert gk.revive_once_on_death
    gk.hp = 3
    g._apply_spell_effect({'effect': 'smite', 'power': '6d6', 'tier': 3, 'name': 'Smite'}, gk)
    assert gk.alive and gk.hp > 3
    assert any('getting up' in t or t == getattr(gk, 'revive_message', None) for t in _texts(g))

    g = _game(seed=95)
    _open_floor(g)
    rat = _spawn(g, 'giant_rat', dx=2, hp=500, max_hp=500)
    rat.status_effects['sleeping'] = 50
    g._apply_spell_effect({'effect': 'magic_missile', 'power': '2d4', 'tier': 2,
                           'name': 'Force Missiles'}, rat)
    assert rat.hp < 500 and not rat.has_effect('sleeping')


# ---------------------------------------------------------------- C13
def test_c13_time_stopped_monsters_do_not_bite_pets():
    """Ordinary monsters stand still under time stop, but the 'monsters
    attack adjacent pets' pass ignored it and frozen rats killed pets."""
    from pet_system import Pet, random_species
    g = _game(seed=71)
    p = g.player
    _open_floor(g)
    random.seed(71)
    pet = Pet(random_species(), p.x + 1, p.y)
    pet.command = 'stay'
    g.pets.append(pet)
    m = _spawn(g, 'giant_rat', dx=2, hp=10 ** 6, max_hp=10 ** 6)
    m.attacks = [{'name': 'Bite', 'damage': '1d2+20', 'type': 'physical'}]
    m.thac0 = -99
    p.status_effects['time_stopped'] = 10
    hp0 = pet.hp
    for _ in range(3):
        g._advance_turn()
    assert pet.alive and pet.hp >= hp0


# ---------------------------------------------------------------- C15
def test_c15_target_status_row_shows_plus_n_instead_of_a_cut_word(monkeypatch):
    """The status row was measured at 14 px but _fit_line draws at 16 px at
    least, so a row that 'fit' was cut mid-word and '+N' never showed."""
    from types import SimpleNamespace
    from test_ui_measured_rows import _combat_render_stub, _reset_layout
    _reset_layout(1280, 720)
    g = _combat_render_stub()
    g.screen = pygame.Surface((1280, 720))
    g.quiz_title = 'ATTACK'
    weapon = SimpleNamespace(name='Iron Longsword', base_damage=10, enchant_bonus=0,
                             damage_types=['slash'], chain_exponent=1.15,
                             chain_multipliers=[1.0])
    g.player = SimpleNamespace(weapon=weapon, ranged_weapon=weapon, hp=20, max_hp=30)
    from fantasy_ui import get_font
    rect = pygame.Rect(110, 400, 1060, g._combat_hud_height())
    slot_w = g._combat_hud_slots(rect.x, rect.y, rect.w)['target']['sub2'].w
    pool = ['poisoned', 'slowed', 'burning', 'blinded', 'stunned', 'weakened',
            'confused', 'bleeding', 'armor_crack', 'sundered', 'deep_wound',
            'heal_blocked', 'feared', 'silenced', 'immobilized', 'diseased']

    def row(effs):
        return "  ".join(f"[{e.replace('_', ' ').title()}]" for e in effs)

    # the worst case: a row that fits at 14 px but not at the 16 px it is drawn at
    effects = next(pool[:n] for n in range(1, len(pool) + 1)
                   if get_font('body', 16).size(row(pool[:n]))[0] > slot_w)
    assert get_font('body', 14).size(row(effects))[0] <= slot_w
    g.combat_target = SimpleNamespace(
        name='Giant Rat', hp=10, max_hp=20, resistances=[], weaknesses=[], tags=[],
        status_effects={e: 3 for e in effects})
    g.quiz_engine = SimpleNamespace(chain=3)
    seen = []
    real = type(g)._fit_line

    def spy(self, text, max_w, sizes, family='body'):
        font, fitted = real(self, text, max_w, sizes, family)
        if text.startswith('[Poisoned]'):
            seen.append((text, fitted))
        return font, fitted

    monkeypatch.setattr(type(g), '_fit_line', spy)
    g._draw_combat_hud(rect)
    assert seen
    text, fitted = seen[-1]
    assert fitted == text, 'status row was truncated mid-word'
    assert text.split()[-1].startswith('+')


# ---------------------------------------------------------------- MK-03
def test_mk03_a_two_by_two_monster_does_not_squeeze_through_a_one_tile_door():
    """A monster opening a door moved onto it at once; only the anchor was
    checked, so Fafnir (2x2) stood half inside the wall."""
    import dungeon as D
    from monster import Monster
    from player import Player
    from geom import occupied_tiles
    W, H = 12, 8
    tiles = [[D.FLOOR] * W for _ in range(H)]
    for x in range(W):
        tiles[3][x] = D.WALL
    tiles[3][5] = D.DOOR
    dn = D.Dungeon(tiles, [], W, H, 60)
    m = Monster(_mdef('fafnir_dragon'), 5, 4)
    assert tuple(m.footprint) == (2, 2)
    p = Player()
    p.x, p.y = 5, 0
    m._turn_occupied = {(p.x, p.y)}
    m._standard_move(p, dn, [m], set(), 'aggressive')
    assert not any(dn.tiles[ty][tx] == D.WALL for tx, ty in occupied_tiles(m))
    assert dn.tiles[3][5] == D.DOOR            # it could not pass: the door stays shut
    # a one-tile creature still opens the door and steps through
    r = Monster(_mdef('giant_rat'), 5, 4)
    r._standard_move(p, dn, [r], set(), 'aggressive')
    assert (r.x, r.y) == (5, 3) and dn.tiles[3][5] != D.DOOR


# ---------------------------------------------------------------- MK-10
def test_mk10_self_buff_spell_message_names_the_status_not_its_id():
    """Casting Counterspell printed 'Counterspell -- magic_resist for 12 turns!'."""
    g = _game(seed=12)
    g._apply_spell_effect({'effect': 'counterspell_self', 'tier': 3, 'name': 'Counterspell'})
    line = next(t for t in _texts(g) if t.startswith('Counterspell --'))
    assert 'magic_resist' not in line and 'Magic Resist' in line


def test_a_thrown_buff_potion_does_not_claim_an_effect_monsters_ignore():
    """A thrown potion of haste said 'It looks Hasted!', but no monster code
    reads hasted (or invisible, regenerating, the resists)."""
    from types import SimpleNamespace
    g = _game(seed=13)
    _open_floor(g)
    m = _spawn(g, 'giant_rat', dx=2)
    g._apply_thrown_potion(SimpleNamespace(effect='haste', duration=5, power=''), m, 'Potion')
    assert 'hasted' not in m.status_effects
    assert not any('It looks' in t for t in _texts(g))
    assert any('no effect' in t for t in _texts(g, 1))
    # the one a monster does use still lands, and says so
    g._apply_thrown_potion(SimpleNamespace(effect='levitation', duration=5, power=''), m, 'Potion')
    assert m.has_effect('levitating')
    assert 'It looks Levitating!' in _texts(g, 1)[0]


def test_sandals_of_theseus_do_not_mirror_reloading_or_the_pit(monkeypatch):
    """The Sandals of Theseus mirror one of the wearer's debuffs onto the
    attacker; the crossbow cooldown and standing in a pit counted, so a rat
    was told it was 'reloading'."""
    import armor_procs
    monkeypatch.setattr(armor_procs, 'proc_value',
                        lambda p, k: 1.0 if k == 'their_own_methods' else 0)
    g = _game(seed=9)
    _open_floor(g, 3)
    p = g.player
    p.hp = p.max_hp = 500
    m = _spawn(g, 'giant_rat')
    m.thac0 = -99
    m.min_hit_chance = 1.0
    m.attacks = [{'name': 'Bite', 'damage': '1d2+5', 'type': 'physical'}]
    for s in range(8):
        p.status_effects['reloading'] = 50
        p.status_effects['in_pit'] = 50
        random.seed(s)
        g._do_monster_turns()
    assert p.hp < 500
    assert 'reloading' not in m.status_effects and 'in_pit' not in m.status_effects
    assert not any("Theseus's sandals" in t for t in _texts(g, 60))
