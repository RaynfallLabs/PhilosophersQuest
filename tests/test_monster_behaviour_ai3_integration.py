"""Monster behaviour, third wave (AI-3): the seams the cross-slice
integration audit found (_mm_2026_11_19/INTEGRATION_AUDIT.md), each pinned
by a seeded test that failed before its fix.

  H1  a death-throes blast is no one's blow: a beetle that dies of a bleed,
      or of the hero's blade, bursts on its neighbours without ending
      Sanctuary, breaking a ward or Hoichi's sutra, breaking a fed Kappa's
      peace, teaching a habit or counting toward the hero's damage badges;
  H2  the Caster's Book meets the hero's wards as a ranged attack does: no
      curse, dispel or darkness at a hero in Sanctuary, none from beyond the
      Mist's reach, and a chant drawn up before the ward rose is let go;
  M1  the Psylli ward keeps a serpent's holds off (coil, gut and drag), and
      one read while held lets the hero go;
  M2  swallowed, the hero's area spells, wands and scrolls reach only the
      creature round him;
  L1  a silenced or babbled witness tells its band nothing;
  and the words that changed with them.
"""
import json
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))

import pygame  # noqa: E402

pygame.init()

from test_monster_behaviour_ai3_game import _hold, _messages, _scene  # noqa: E402


def _data(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# H1: a blast is no one's blow
# ---------------------------------------------------------------------------

def _blast_scene(*neighbours, seed=11):
    """The hero at the room's centre; a fire beetle three tiles east, with
    ``neighbours`` round it (inside its blast, outside the hero's)."""
    spots = [(4, 0), (3, 1), (3, -1), (2, 1)]
    placed = [('fire_beetle', 3, 0)] + [(k, dx, dy) for k, (dx, dy) in zip(neighbours, spots)]
    g = _scene(*placed, seed=seed)
    for o in g.monsters[1:]:
        o.status_effects['sleeping'] = 50        # asleep: they take no turn of their own
    return g, g.monsters[0], g.monsters[1:]


def _kill_by_hero(g, beetle):
    """The hero's blade fells the beetle: the blow is his, the burst is not."""
    g._damage_by = 'hero'
    beetle.take_damage(beetle.hp + 50)
    assert not beetle.alive
    g._on_monster_killed(beetle)
    assert g._damage_by == 'hero'                # restored after the blast


def test_a_bleed_kills_a_beetle_and_its_burst_does_not_end_sanctuary():
    import wards
    g, beetle, (gob,) = _blast_scene('goblin')
    wards.grant(g.player, 'sanctuary', 30)
    beetle.hp = 1
    beetle.status_effects['bleeding'] = 5
    beetle.status_effects['sleeping'] = 50
    hp0 = gob.hp
    g._advance_turn()
    assert not beetle.alive
    assert gob.hp < hp0                          # the blast did catch the goblin
    assert g.player.has_effect('sanctuary')
    assert not any('sanctuary is over' in t.lower() for t in _messages(g, 40))


def test_a_burst_does_not_break_the_heart_sutra_or_a_ward_against_the_dead():
    import wards
    g, beetle, (shade, zombie) = _blast_scene('shadow', 'zombie')
    wards.grant(g.player, 'ward_hoichi', 30)
    wards.grant(g.player, 'ward_lemuria', 30)
    s0, z0 = shade.hp, zombie.hp
    _kill_by_hero(g, beetle)
    assert shade.hp < s0 and zombie.hp < z0      # both were in the blast
    assert g.player.has_effect('ward_hoichi')    # the sutra holds for every ghost
    assert wards.wards_on(g.player, zombie, 'melee')   # the beans still buy it off


def test_a_burst_does_not_break_a_fed_kappas_peace():
    g, beetle, (kappa,) = _blast_scene('kappa')
    kappa._lp_calm = True
    k0 = kappa.hp
    _kill_by_hero(g, beetle)
    assert kappa.hp < k0
    assert kappa.__dict__.get('_lp_calm')
    assert not any('peace is broken' in t for t in _messages(g, 40))


def test_a_burst_teaches_no_habit_and_counts_toward_no_badge_of_the_heros():
    import monster
    g, beetle, (gob,) = _blast_scene('goblin')
    events = []
    real_observer = monster.DAMAGE_OBSERVER
    g._seeker_event = lambda kind, **kw: events.append((kind, kw))
    monster.DAMAGE_OBSERVER = g._seeker_damage
    try:
        g._damage_by = 'hero'
        beetle.take_damage(beetle.hp + 50)
        events.clear()                           # the hero's own blow on the beetle is his
        g.__dict__.pop('_tm_struck', None)
        g0 = gob.hp
        g._on_monster_killed(beetle)
    finally:
        monster.DAMAGE_OBSERVER = real_observer
    assert gob.hp < g0
    assert id(gob) not in set(g.__dict__.get('_tm_struck') or ())     # no area habit
    hero_dmg = [kw for kind, kw in events if kind == 'damage' and kw.get('by') == 'hero']
    assert hero_dmg == []
    assert any(kind == 'damage' and kw.get('by') == 'throes' for kind, kw in events)


# ---------------------------------------------------------------------------
# H2: the Book meets the hero's wards
# ---------------------------------------------------------------------------

def _caster(kind, dx, seed=5):
    import caster_ai
    g = _scene((kind, dx, 0), seed=seed)
    m = g.monsters[0]
    m._tracking = True
    ctx = caster_ai.Context(g.player, g.dungeon, list(g.monsters))
    return g, m, ctx


def _spell(m, kind):
    import caster_ai
    return next(s for s in caster_ai.book(m) if s['kind'] == kind)


def test_no_curse_dispel_or_darkness_at_a_hero_in_sanctuary():
    import caster_ai
    import wards
    for kind, sk, prep in (('night_hag', 'control', None),
                           ('cult_hierophant', 'dispel', ('hasted', 20)),
                           ('drow_priestess', 'darkness', ('light', 50))):
        g, m, ctx = _caster(kind, 3)
        if prep:
            g.player.status_effects[prep[0]] = prep[1]
        s = _spell(m, sk)
        assert caster_ai.usable(m, s, ctx), kind            # it would, unwarded
        wards.grant(g.player, 'sanctuary', 30)
        assert not caster_ai.usable(m, s, ctx), kind
        se0 = dict(g.player.status_effects)
        for _ in range(4):
            caster_ai.turn(m, g.player, g.dungeon, g.monsters, None)
        for eff in ('sleeping', 'paralyzed', 'immobilized', 'feared', 'silenced'):
            assert not g.player.has_effect(eff), (kind, eff)
        if prep:
            assert g.player.status_effects.get(prep[0]) == se0[prep[0]], kind
        # The gate's line was not spent on a question: the first blow it
        # meets still says it.
        assert m.__dict__.get('_sanct_said') is None


def test_no_cast_from_beyond_the_mists_reach():
    import caster_ai
    import wards
    for kind, sk in (('lich', 'control'), ('night_hag', 'control'), ('kobold_sorcerer', 'darkness')):
        g, m, ctx = _caster(kind, 4)
        g.player.status_effects['light'] = 50
        s = _spell(m, sk)
        m._aware = True
        g.player.add_effect('aggravated', 20)              # it knows where he is
        assert caster_ai.usable(m, s, ctx), kind
        wards.grant(g.player, 'veiled', 30)
        assert not caster_ai.usable(m, s, ctx), kind        # 4 tiles off: the mist hides him
        m.x = g.player.x + 2                                # within the veil's reach
        assert caster_ai.usable(m, s, ctx), kind


def test_a_chant_begun_before_sanctuary_is_let_go():
    import caster_ai
    import wards
    g, m, ctx = _caster('night_hag', 3)
    s = _spell(m, 'control')
    ch = {'id': s['id'], 'kind': s['kind'], 'spell': s, 'attack': None}
    assert caster_ai.act(m, ch, g.player, g.dungeon, g.monsters) is False
    assert m.__dict__.get('_casting') == s['id']             # the chant is drawn up
    wards.grant(g.player, 'sanctuary', 30)
    assert caster_ai.turn(m, g.player, g.dungeon, g.monsters, None) is None
    assert not g.player.has_effect('sleeping')
    assert not m.__dict__.get('_casting')


# ---------------------------------------------------------------------------
# M1: the Psylli ward and a serpent's holds
# ---------------------------------------------------------------------------

def _try_hold(g, m):
    import holds
    real = random.randint
    random.randint = lambda a, b: a                          # every save fails
    try:
        atk = next(a for a in m.attacks if holds.spec_of(a))
        return holds.after_blow(m, g.player, atk, 5, '')
    finally:
        random.randint = real


def test_the_psylli_ward_keeps_off_a_serpents_coils_gut_and_drag():
    import holds
    import wards
    for kind in ('rock_python', 'taniwha', 'sobek_warrior'):
        g = _scene((kind, 1, 0))
        m = g.monsters[0]
        wards.grant(g.player, 'ward_psylli', 25)
        line = _try_hold(g, m)
        assert not holds.is_held(g.player), kind
        assert 'Psylli' in line, (kind, line)
        assert not g.player.has_effect('held'), kind


def test_without_the_ward_the_serpent_still_holds():
    import holds
    g = _scene(('rock_python', 1, 0))
    _try_hold(g, g.monsters[0])
    assert holds.is_held(g.player)


def test_the_psylli_ward_does_not_keep_off_a_cube():
    import holds
    import wards
    g = _scene(('gelatinous_cube', 1, 0))
    wards.grant(g.player, 'ward_psylli', 25)
    _try_hold(g, g.monsters[0])
    assert holds.is_held(g.player)                           # an ooze is no serpent


def test_the_psylli_ward_read_while_held_lets_the_hero_go():
    import holds
    import wards
    g = _scene(('rock_python', 1, 0))
    m = g.monsters[0]
    _hold(g, m)
    wards.grant(g.player, 'ward_psylli', 25)
    line = holds.validate(g.player, g.monsters)
    assert not holds.is_held(g.player)
    assert 'ward' in line.lower() and 'Rock Python' in line


def test_the_psylli_texts_promise_what_the_game_does():
    ward = _data('wards.json')['family_wards']['ward_psylli']
    assert 'held' in ward['riders']
    assert 'hold you' in ward['desc']
    scroll = next(v for v in _data('items', 'scroll.json').values()
                  if isinstance(v, dict) and v.get('name') == 'scroll of the Psylli')
    assert 'hold you' in scroll['read_line']


# ---------------------------------------------------------------------------
# M2: swallowed, the hero reaches only the gut round him
# ---------------------------------------------------------------------------

def _inside_cube(*outside):
    spots = [(-2, 0), (0, 2), (0, -2)]
    g = _scene(('gelatinous_cube', 1, 0), *[(k, dx, dy) for k, (dx, dy) in zip(outside, spots)])
    cube = g.monsters[0]
    _hold(g, cube)
    for o in g.monsters[1:]:
        o.status_effects.pop('sleeping', None)
    return g, cube, g.monsters[1:]


def test_area_spells_from_inside_reach_only_the_holder():
    from spells import LEARNABLE_SPELLS
    for sid, eff in (('pans_panic_spell', 'feared'), ('confusion_of_tongues_spell', 'confused'),
                     ('settled_strife_spell', 'charmed')):
        g, cube, outside = _inside_cube('orc_shaman', 'goblin', 'kobold')
        g._mm_cast(LEARNABLE_SPELLS[sid], None, 1.0)
        for o in outside:
            assert not o.has_effect(eff), (sid, o.kind)
            assert not o.has_effect('babbled'), (sid, o.kind)
        assert g._mm_foes_in_sight() == [cube], sid


def test_a_wand_or_scroll_from_inside_reaches_only_the_holder():
    g, cube, outside = _inside_cube('goblin', 'kobold')
    wand = types.SimpleNamespace(effect='mass_sleep', quiz_tier=1, power='', id='wand_x',
                                 name='wand', charges=3, tier=1)
    g._apply_wand_effect(wand)
    assert not any(o.has_effect('sleeping') for o in outside)
    scroll = types.SimpleNamespace(effect='confuse_monsters', quiz_tier=1, tier=1, power='',
                                   id='scroll_x', name='scroll', buc='uncursed')
    g._apply_scroll_effect(scroll)
    assert not any(o.has_effect('confused') for o in outside)
    assert all(not g._in_hero_reach(o) for o in outside)
    assert g._in_hero_reach(cube)


def test_free_of_the_gut_the_room_is_in_reach_again():
    import holds
    g, cube, outside = _inside_cube('goblin')
    holds.release(g.player, cube, 'cut')
    assert g._in_hero_reach(outside[0])
    assert outside[0] in g._mm_foes_in_sight()


# ---------------------------------------------------------------------------
# L1: a witness with no voice tells no one
# ---------------------------------------------------------------------------

def _band_pair():
    from test_monster_behaviour_ai3_game import _monster
    a, b = _monster('goblin', 5, 5), _monster('goblin', 7, 5)
    a._band = b._band = 'band-1'
    a._tm_habits = {'choke_fighter': [10]}
    return a, b


def test_a_silenced_or_babbled_witness_tells_its_band_nothing():
    import habits
    for status in ('silenced', 'babbled'):
        witness, mate = _band_pair()
        assert habits.count(None, mate, 'choke_fighter', turn=12, monsters=[witness, mate]) == 1
        witness.status_effects[status] = 10
        assert habits.count(None, mate, 'choke_fighter', turn=12, monsters=[witness, mate]) == 0, status
        assert habits.count(None, witness, 'choke_fighter', turn=12, monsters=[witness, mate]) == 1


def test_a_babbled_listener_understands_no_one():
    import habits
    witness, mate = _band_pair()
    mate.status_effects['babbled'] = 10
    assert habits.count(None, mate, 'choke_fighter', turn=12, monsters=[witness, mate]) == 0


# ---------------------------------------------------------------------------
# The words
# ---------------------------------------------------------------------------

def test_the_tells_and_the_help_page_say_what_the_game_does():
    tells = _data('tells.json')
    flat = json.dumps(tells)
    assert 'before he can step back' not in flat
    assert 'keeps your feet on the ground' not in flat
    assert 'harder to lift' in flat
    page = _data('ui', 'monster_ways.json')
    names = [row[0] for sec in page['sections'] for row in sec.get('rows', ())]
    assert names.count('Lurkers') == 1 and 'Back to the web' in names


def test_the_soldier_tell_fits_an_it():
    import tells as tells_mod
    from test_monster_behaviour_ai3_game import _monster
    m = _monster('skeleton_warrior')
    _sign, _does, counter = tells_mod.parts(m, 'mind_soldier')
    assert 'before it can step back' in counter
