"""The audit of slice G (2026-11-20, _mm_2026_11_19/G/AUDIT.md): one seeded
test for each defect it found, each failing on 459bfabe and passing after.

H1 a wound ticking broke the wards; H2 silence let most casters cast; H3 an
unstrung gorgon bit from five tiles; M1 the Fern-Flower showed nothing; M2
Shrink the Earth crossed walls; M3 area acts kept Sanctuary; M4 the arrow
wards stopped death rays; M5 babbling did nothing to war bands; M6 the
Sceptre's card and its silence; and the Low rows.
"""
import json
import os
import random
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import attack_gates  # noqa: E402
import monster as monster_mod  # noqa: E402
import wards  # noqa: E402
from game_magic import MagicMixin  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402
from spells import LEARNABLE_SPELLS  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)
KINDS = sorted(k for k, v in MONS.items() if isinstance(v, dict) and v.get('attacks'))


def mon(kind, x=5, y=5, hits=True):
    m = Monster({**MONS[kind], 'id': kind}, x, y)
    if hits:
        m.thac0 = -100
        m._slipped = lambda player, atk: False
    return m


def hero(x=4, y=5):
    p = Player()
    p.x, p.y = x, y
    p.status_effects = {}
    return p


class _D:
    def __init__(self, w=20, h=20, walls=()):
        self.width, self.height = w, h
        self.tiles = [[1] * w for _ in range(h)]
        self.walls = set(walls)
        for (x, y) in self.walls:
            self.tiles[y][x] = 0
        self.explored = set()

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and (x, y) not in self.walls


class _G(MagicMixin):
    def __init__(self, walls=()):
        self.player = hero()
        self.player.INT = 10
        self.dungeon = _D(walls=walls)
        self.monsters, self.pets, self.ground_items = [], [], []
        self.visible = {(x, y) for x in range(20) for y in range(20)}
        self.dungeon_level, self.turn_count = 5, 100
        self.messages = []
        self._wand_override_target = None
        self._last_spell_crit = self._last_spell_anti_being = False
        self._damage_by = 'hero'

    def add_message(self, text, kind='info'):
        self.messages.append(text)

    def _on_monster_killed(self, m, **kw):
        pass

    def _refresh_fov(self):
        pass

    def _occupants(self, hero=True):
        return set()

    def _make_noise(self, *a, **kw):
        pass


def _new_game(name='__test_mm_audit__'):
    import pygame
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    pygame.init()
    import items as items_mod
    from game_states import STATE_PLAYER
    from main import Game
    random.seed(5)
    items_mod.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1280, 720)), player_name=name)
    g.monsters = []
    g.state = STATE_PLAYER
    return g


@pytest.fixture
def struck_hook():
    old = monster_mod.HERO_STRUCK
    yield
    monster_mod.HERO_STRUCK = old


# ---------------------------------------------------------------------------
# H1: a wound ticking is not the hero's blow
# ---------------------------------------------------------------------------

def test_a_wound_ticking_breaks_no_ward(struck_hook):
    random.seed(1)
    g = _G()
    monster_mod.HERO_STRUCK = g._ward_hero_struck
    far = mon('goblin', 18, 18)
    ghost = mon(next(k for k in KINDS if MONS[k].get('family') == 'ghosts'
                     and not MONS[k].get('is_boss')), 17, 17)
    dead = mon(next(k for k in KINDS if MONS[k].get('family') == 'restless_dead'
                    and not MONS[k].get('is_boss')), 16, 16)
    man = mon(next(k for k in KINDS if MONS[k].get('family') == 'mortals'
                   and not MONS[k].get('is_boss') and not MONS[k].get('is_mini_boss')), 15, 15)
    g.monsters = [far, ghost, dead, man]
    for st in ('sanctuary', 'ward_hoichi', 'ward_lemuria'):
        wards.grant(g.player, st, 20)
    man.status_effects['charmed'] = 10
    man._strife_peace = True
    for m in g.monsters:
        m.status_effects['bleeding'] = 3
        m.hp = m.max_hp = max(m.max_hp, 200)
    for m in g.monsters:
        m.tick_effects()
    p = g.player
    assert p.has_effect('sanctuary') and p.has_effect('ward_hoichi') and p.has_effect('ward_lemuria')
    assert man.has_effect('charmed')
    atk = next(a for a in dead.attacks if wards.is_melee(a))
    assert wards.blow_gate(p, dead, atk)[0] == 0          # Lemuria still holds it
    assert not far.__dict__.get('_hurt_by_hero_turn')
    # The hero's own blow still breaks them.
    far.take_damage(1)
    assert not p.has_effect('sanctuary')


# ---------------------------------------------------------------------------
# H2: silence stops every spoken or cast attack, whatever its damage type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('kind, attack', [
    ('lich', 'Cold Bolt'), ('death_mage', 'Necrotic Bolt'), ('battle_mage', 'Fire Bolt'),
    ('battle_mage', 'Frost Bolt'), ('kobold_sorcerer', 'Fire Bolt'),
    ('necromancer_apprentice', 'Death Bolt'), ('drow_mage', 'Shadow Bolt')])
def test_silence_stops_the_bolts_of_every_element(kind, attack):
    m = mon(kind)
    atk = next(a for a in m.attacks if a['name'] == attack)
    assert attack_gates.blocks_attack(m, atk) == ''
    attack_gates.inflict(m, 'silenced', 10)
    assert attack_gates.blocks_attack(m, atk) == 'silenced_cast'


def test_silence_stops_every_cast_in_the_data_and_no_arrow():
    for k in KINDS:
        m = mon(k, hits=False)
        attack_gates.inflict(m, 'silenced', 10)
        if not m.has_effect('silenced'):
            continue                                     # the mouthless
        for a in m.attacks:
            if wards.is_cast(a) or wards.delivery(a) == 'voice':
                assert attack_gates.blocks_attack(m, a), (k, a['name'])
            if wards.is_missile(a):
                assert not attack_gates.blocks_attack(m, a), (k, a['name'])


def test_a_silenced_caster_with_only_spells_walks_up():
    for kind in ('kobold_sorcerer', 'death_mage', 'battle_mage', 'drow_mage'):
        m = mon(kind)
        assert not attack_gates.must_close(m)
        attack_gates.inflict(m, 'silenced', 10)
        assert attack_gates.must_close(m), kind
    archer = mon('skeleton_archer')
    attack_gates.inflict(archer, 'silenced', 10)
    assert not attack_gates.must_close(archer)           # his bow is no spell


# ---------------------------------------------------------------------------
# H3: no gated monster strikes with a melee attack from range
# ---------------------------------------------------------------------------

def test_no_gated_kind_lands_a_melee_blow_from_five_tiles(monkeypatch):
    seen = []
    real = wards.blow_gate

    def spy(player, m, atk):
        seen.append((m.kind, atk.get('name'), wards.is_melee(atk), m._adjacent_to(player)))
        return real(player, m, atk)
    monkeypatch.setattr(wards, 'blow_gate', spy)
    random.seed(7)
    for k in KINDS:
        for gate in ('silenced', 'unstrung'):
            p = hero(4, 5)
            m = mon(k, 9, 5)
            m.add_effect(gate, 6)
            if not m.has_effect(gate):
                continue
            hp0 = p.hp
            for _ in range(4):
                m._gaze_cooldown = 0
                try:
                    m.attack(p)
                except Exception as e:                   # (no kind may crash on it either)
                    raise AssertionError(f'{k} {gate}: {e!r}')
            bad = [s for s in seen if s[2] and not s[3]]
            assert not bad, (k, gate, bad[:2])
            seen.clear()
            del hp0


def test_an_unstrung_gorgon_still_gazes_and_never_bites_from_range():
    random.seed(3)
    p = hero(4, 5)
    m = mon('medusa_gorgon', 9, 5)
    attack_gates.inflict(m, 'unstrung', 8)
    for _ in range(6):
        m._gaze_cooldown = 0
        before = p.hp
        dmg, msg = m.attack(p)
        assert dmg == 0 and p.hp == before, msg


def test_an_unstrung_slinger_does_not_sling_with_his_pack():
    import packs
    k = next((k for k in KINDS if packs.pack_of(k) and any(a.get('ranged') for a in MONS[k]['attacks'])),
             None)
    if k is None:
        pytest.skip('no pack kind with a ranged attack')
    m = mon(k)
    assert packs._ranged_attacks(m)
    attack_gates.inflict(m, 'unstrung', 8)
    assert not [a for a in packs._ranged_attacks(m) if wards.is_missile(a)]


# ---------------------------------------------------------------------------
# M1: the treasure sight is drawn
# ---------------------------------------------------------------------------

def test_the_fern_flower_draws_the_treasure_out_of_sight(struck_hook):
    from items import GoldPile
    g = _new_game()
    spot = next((x, y) for y in range(g.dungeon.height) for x in range(g.dungeon.width)
                if g.dungeon.is_walkable(x, y) and (x, y) not in g.visible
                and max(abs(x - g.player.x), abs(y - g.player.y)) > 12)
    gold = GoldPile(50, *spot)
    g.ground_items.append(gold)
    drawn = []
    g.renderer.draw_item_remembered = lambda item, cx, cy: drawn.append(item)
    g.render()
    assert gold not in drawn
    g._treasure_sight()
    assert spot in g.dungeon.__dict__['treasure_seen'] and spot in g.dungeon.explored
    g.render()
    assert gold in drawn


# ---------------------------------------------------------------------------
# M2: Shrink the Earth needs clear ground
# ---------------------------------------------------------------------------

def test_shrink_the_earth_does_not_cross_a_wall_it_can_see_through():
    # A wall across x=7 (the Crown of Brahma shows the far side: it is in
    # `visible`), and the hero at (4, 5).
    g = _G(walls=[(7, y) for y in range(20)])
    assert (9, 5) in g.visible
    assert g._aimed_step_refused(9, 5)
    assert g._aimed_step_refused(6, 5) == ''


# ---------------------------------------------------------------------------
# M3: an act with no single target ends Sanctuary
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('sid', ['pans_panic_spell', 'darkness_of_egypt_spell',
                                 'hush_of_the_feralia_spell', 'dulled_blades_spell',
                                 'confusion_of_tongues_spell', 'settled_strife_spell',
                                 'mass_slow_spell'])
def test_an_area_spell_ends_sanctuary(sid):
    random.seed(2)
    g = _G()
    g.monsters = [mon('goblin', 6, 5), mon('goblin', 6, 6)]
    wards.grant(g.player, 'sanctuary', 8)
    g._apply_spell_effect(LEARNABLE_SPELLS[sid], None)
    assert not g.player.has_effect('sanctuary'), sid


def test_the_piper_and_the_krotala_end_sanctuary_and_a_self_ward_does_not():
    from items import make_item_by_id
    g = _G()
    g.monsters = [mon('goblin', 6, 5)]
    wards.grant(g.player, 'sanctuary', 8)
    g._apply_spell_effect(LEARNABLE_SPELLS['stayed_spear_spell'], None)
    assert g.player.has_effect('sanctuary')
    g._apply_scroll_effect(make_item_by_id('scroll', 'scroll_of_the_hamelin_piper'))
    assert not g.player.has_effect('sanctuary')
    wards.grant(g.player, 'sanctuary', 8)
    g._apply_wand_effect(make_item_by_id('wand', 'krotala_of_athena'))
    assert not g.player.has_effect('sanctuary')


# ---------------------------------------------------------------------------
# M4: the arrow wards stop missiles, not spells
# ---------------------------------------------------------------------------

def test_the_arrow_wards_stop_an_arrow_and_not_a_death_ray():
    p = hero()
    archer = mon('skeleton_archer', 9, 5)
    mage = mon('death_mage', 9, 5)
    arrow = archer.attacks[0]
    bolt = next(a for a in mage.attacks if a['name'] == 'Necrotic Bolt')
    for st in ('missile_ward', 'stayed_spear'):
        p.status_effects = {}
        wards.grant(p, st, 10)
        assert wards.blow_gate(p, archer, arrow)[0] == 0, st
        assert wards.blow_gate(p, mage, bolt) is None, st


# ---------------------------------------------------------------------------
# M5: a babbling war band cannot hear its leader
# ---------------------------------------------------------------------------

def test_a_babbling_follower_loses_his_leaders_hold_and_his_call():
    import war_bands
    leader, a, b = mon('goblin', 5, 5), mon('goblin', 6, 6), mon('goblin', 7, 7)
    for m in (leader, a, b):
        m._band = 'band1'
    leader._band_role = 'leader'
    a._band_leader = b._band_leader = leader
    assert war_bands.holds_nerve(a)
    attack_gates.inflict(a, 'babbled', 12)
    assert not war_bands.holds_nerve(a)
    assert war_bands.alarm(a, [leader, a, b], 1, 1) == 0     # his call means nothing
    assert war_bands.alarm(b, [leader, a, b], 1, 1) == 1     # and he hears no call



def test_a_babbling_follower_runs_when_hurt_in_his_own_turn(struck_hook):
    g = _new_game('__test_mm_audit3__')
    px, py = g.player.x, g.player.y
    leader, a = mon('goblin', px + 1, py, hits=False), mon('goblin', px, py + 1, hits=False)
    for m in (leader, a):
        m._band = 'band1'
    leader._band_role = 'leader'
    a._band_leader = leader
    a.ai_pattern = 'aggressive'
    a.hp = 1
    a.take_turn(g.player, g.dungeon, [leader, a])
    assert a._flee_timer == 0                            # his leader's hold keeps him
    attack_gates.inflict(a, 'babbled', 12)
    a.take_turn(g.player, g.dungeon, [leader, a])
    assert a._flee_timer > 0


# ---------------------------------------------------------------------------
# M6: the Sceptre's card and its silence
# ---------------------------------------------------------------------------

def test_the_sceptres_card_names_who_it_silences_and_its_power(struck_hook):
    from game_render import RenderMixin
    from items import make_item_by_id
    w = make_item_by_id('weapon', 'sceptre_of_agamemnon')
    w.identified = True
    words = RenderMixin._weapon_hit_effect(w)[0]
    assert 'a man or a goblin' in words
    g = _new_game('__test_mm_audit4__')
    g.player.known_item_ids.add(w.id)
    lines = ' '.join(str(t) for t in g._item_power_lines(w))
    assert 'a man or a goblin' in lines and 'Call the Assembly' in lines


def test_the_sceptres_silence_keeps_the_named_foes_window():
    m = mon('iron_patriarch')
    assert m._is_named_foe()
    m.hold('silenced', 2)
    assert m.status_effects['silenced'] == 2
    m.status_effects['silenced'] = 0                      # it wore off...
    m.hold('silenced', 2)
    assert not m.has_effect('silenced')                   # ...and he is steadying


# ---------------------------------------------------------------------------
# Low rows
# ---------------------------------------------------------------------------

def test_a_held_named_foe_is_not_said_to_shake_it_off():
    m = mon('iron_patriarch')
    assert attack_gates.inflict(m, 'silenced', 10) == 3
    assert attack_gates.inflict(m, 'silenced', 10) == 3     # still held: not 0


def test_the_assembly_is_once_a_floor_visited_and_men_and_goblins_only():
    from items import make_item_by_id
    import types
    g = _G()
    g._advance_turn = lambda: None
    g.player.weapon = make_item_by_id('weapon', 'sceptre_of_agamemnon')
    g.dungeon_level = 42
    assert g._sceptre_ready()
    g.player._sceptre_floors = {42}
    g.dungeon_level = 41
    assert g._sceptre_ready()
    g.dungeon_level = 42
    assert not g._sceptre_ready()
    man = mon('brigand', 6, 5)
    giant = mon(next(k for k in KINDS if MONS[k].get('family') == 'giants' and not
                     (MONS[k].get('is_boss') or MONS[k].get('is_mini_boss'))
                     and not Monster({**MONS[k], 'id': k}, 0, 0).resists_control('feared')), 7, 5)
    g.monsters = [man, giant]
    random.seed(1)
    g._sceptre_quiz_done(types.SimpleNamespace(score=3))
    assert not giant.has_effect('feared')
    assert man.has_effect('feared')
    assert any('1 foe turns and runs' in t for t in g.messages), g.messages


def test_a_gated_monster_steps_or_strikes_not_both():
    calls = {'moved': 0}

    class M:
        def _spots_player(self, *a):
            return True

        def _adjacent_to(self, p):
            return calls['moved'] > 0

        def _standard_move(self, *a):
            calls['moved'] += 1
            return False
    assert attack_gates.close_in(M(), None, None, [], ()) is False


def test_a_named_foe_gets_one_half_blow_however_many_wards():
    p = hero()
    m = mon(next(k for k in KINDS if MONS[k].get('family') == 'demons'))
    m.is_mini_boss = True
    wards.grant(p, 'ward_udug_hul', 20)
    wards.grant(p, 'ward_deliver_us', 20)
    atk = next(a for a in m.attacks if wards.is_melee(a))
    if not atk:
        pytest.skip('no melee')
    assert monster_mod._ward_gate(p, m, atk)[1] is None
    assert not wards.wards_on(p, m, 'melee')              # both broken against it
    # The half is for that blow only: the next gate call clears it.
    monster_mod._ward_gate(p, m, atk)
    assert wards.damage_mult(p, m) == 1.0


def test_sanctuary_speaks_again_under_a_new_sanctuary_and_loosed_says_why():
    p = hero()
    m = mon('goblin')
    atk = next(a for a in m.attacks if wards.is_melee(a))
    wards.grant(p, 'sanctuary', 8)
    assert wards.blow_gate(p, m, atk)[1]
    assert wards.blow_gate(p, m, atk)[1] == ''
    p.status_effects.pop('sanctuary')
    wards.grant(p, 'sanctuary', 8)
    assert wards.blow_gate(p, m, atk)[1]
    assert monster_mod._loosed_line(m)


def test_the_lines_agree_with_one():
    random.seed(4)
    g = _G()
    a = mon('goblin', 6, 5)
    g.monsters = [a]
    g._apply_spell_effect(LEARNABLE_SPELLS['bough_of_somnus_spell'], a)
    assert any('falls asleep' in t for t in g.messages), g.messages


def test_a_silenced_abaddon_calls_no_locusts():
    p = hero(4, 5)
    ab = mon('abaddon_destroyer', 5, 5, hits=False)
    ab._aware = True
    ab.locust_interval = 1
    assert ab._adjacent_to(p)
    ab.status_effects['silenced'] = 5
    ab._abaddon_turn(p, _D(), [ab], ())
    assert not ab._wants_locust_spawn
    ab.status_effects.pop('silenced')
    ab._abaddon_turn(p, _D(), [ab], ())
    assert ab._wants_locust_spawn
