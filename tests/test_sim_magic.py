"""Magic written for the real hero: the simulator's measurement knobs
(tools/balance/sim_magic.py; 2026-11-21, LATE_GAME_PLAN_2026_11_21.md change 6).

Every knob's default is the game as it is, and a default cell is the one
before the hooks. These tests hold that, and that each knob does what it says
through the game's own code: INT's step (M1), the tier written against the
careful blow and by tier only (M2), the holy spells meeting the holy weakness
(M3), max MP from INT (M4), and escape and hold (M5) by the game's handlers.
"""
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
os.environ.setdefault('PQ_NO_BONES', '1')

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _run(knobs='', profile='mastery'):
    import difficulty_sim as ds
    run = ds.Run(ds.FloorCache(1), profile, 0.95, 1.0, 'greedy', 1, ds.parse_knobs(knobs))
    run.fs = ds.new_floor_stats()
    run.floor = 30
    return run


def _proto(kind, **kw):
    from monster import Monster
    m = Monster({**MONS[kind], 'id': kind}, 0, 0)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def _sure(run):
    run.quiz.one_question = lambda *a, **k: True


def test_every_magic_knob_is_in_the_simulator_and_is_the_game():
    import difficulty_sim as ds
    import game_magic
    import sim_magic
    for k, v in sim_magic.KNOBS.items():
        assert ds.KNOB_DEFAULTS[k] == v
    assert sim_magic.KNOBS['mg_int_per'] == game_magic.INT_DAMAGE_PER_POINT
    assert sim_magic.KNOBS['mg_int_cap'] == game_magic.INT_DAMAGE_CAP


def test_at_the_defaults_spells_are_the_games():
    import game_magic
    import sim_magic
    run = _run()
    for intel in (6, 10, 20, 37, 55):
        run.p.INT = intel
        assert sim_magic.int_factor(run) == game_magic.int_damage_factor(intel)
    for t in range(1, 6):
        assert sim_magic.tier_mult(run, t) == game_magic.MAGIC_TIER_MULT[t]
    assert sim_magic.element(run, 'smite', None) is None
    assert not sim_magic.ignores_resistance(run, 'smite')
    mp = run.p.max_mp
    sim_magic.sync_mp(run)
    assert run.p.max_mp == mp


def test_m1_int_feeds_a_spell_as_str_feeds_the_sword():
    import sim_magic
    run = _run('mg_int_per=0.03,mg_int_cap=99')
    run.p.INT = 30
    sword = 1.0 + (30 - 10) * 0.03            # combat.py's str_factor at STR 30
    assert abs(sim_magic.int_factor(run) / 2.0 - sword) < 1e-9
    run.p.INT = 60
    assert sim_magic.int_factor(run) == 2.0 * (1.0 + 50 * 0.03)     # no cap


def test_m2_a_tier_is_written_against_the_careful_blow_by_tier_alone():
    import game_magic
    import sim_magic
    table = sim_magic.anchor_table()
    assert sorted(table) == [1, 2, 3, 4, 5]
    assert all(v > 1.0 for v in table.values())        # the careful kid out-hits the yardstick
    run = _run('mg_anchor=0.8')
    for t in range(1, 6):
        assert abs(sim_magic.tier_mult(run, t) - game_magic.MAGIC_TIER_MULT[t] * 0.8 * table[t]) < 1e-9
    run.floor = 90                                  # the floor never enters it
    assert abs(sim_magic.tier_mult(run, 2) - game_magic.MAGIC_TIER_MULT[2] * 0.8 * table[2]) < 1e-9


def test_m3_the_holy_spells_meet_the_holy_weakness_and_ignore_resistance():
    import sim_magic
    run = _run('mg_holy=1')
    assert sim_magic.element(run, 'smite', None) == 'holy'
    assert sim_magic.element(run, 'fire_bolt', 'fire') == 'fire'
    assert sim_magic.ignores_resistance(run, 'smite')
    z = _proto('zombie')
    assert 'holy' in z.weaknesses
    z.max_hp = z.hp = 10 ** 6
    plain = _proto('zombie')
    plain.max_hp = plain.hp = 10 ** 6
    holy = z.take_damage(100, 'holy', ignore_resistance=True)
    flat = plain.take_damage(100, 'physical')
    assert holy == 2 * flat
    r = _proto('zombie', weaknesses=[], resistances=['holy'])
    r.max_hp = r.hp = 10 ** 6
    assert r.take_damage(100, 'holy', ignore_resistance=True) == flat


def test_m4_max_mp_follows_int_and_never_counts_twice():
    import sim_magic
    run = _run('mg_mp_int=2')
    p = run.p
    base = p.max_mp
    sim_magic.sync_mp(run)
    assert p.max_mp == base + p.INT
    sim_magic.sync_mp(run)
    assert p.max_mp == base + p.INT
    p.apply_stat_bonus('INT', 3)               # the game gives +3 MP; the knob adds the other 3
    sim_magic.sync_mp(run)
    assert p.max_mp == base + (p.INT - 3) + 2 * 3


def test_m5_hold_puts_a_second_foe_to_sleep_or_holds_it_through_the_games_handler():
    import difficulty_sim as ds
    import sim_magic
    run = _run('mg_hold=1')
    _sure(run)
    run.p.mp = run.p.max_mp = 100
    run._mg_book = {'hold_monster_spell': ds.SPELLS['hold_monster_spell']}
    a, b = _proto('ogre'), _proto('ogre')
    a.x, a.y, b.x, b.y = 6, 5, 5, 6
    run.p.x, run.p.y = 5, 5
    assert sim_magic.hold(run, a, [a, b], [])
    assert b.has_effect('paralyzed') and not a.has_effect('paralyzed')
    assert sim_magic.pick_target(run, [a, b], b) is a       # the awake one first
    assert not sim_magic.hold(run, a, [a, b], [])           # one awake: nothing to hold
    run2 = _run('')
    run2._mg_book = dict(run._mg_book)
    assert not sim_magic.hold(run2, a, [a, b], [])          # the knob off: never


def test_m5_escape_is_a_sure_way_out_and_none_without_a_spell():
    import difficulty_sim as ds
    import sim_magic
    run = _run('mg_escape=1')
    _sure(run)
    assert sim_magic.escape(run, slow=False) is None
    run._mg_book = {'blink_spell': ds.SPELLS['blink_spell']}
    run.p.mp = run.p.max_mp = 100
    assert sim_magic.escape(run, slow=False) is True
    run.p.mp = 0
    assert sim_magic.escape(run, slow=False) is None
    off = _run('')
    off._mg_book = {'blink_spell': ds.SPELLS['blink_spell']}
    assert sim_magic.escape(off, slow=False) is None


def test_the_default_cell_is_the_one_before_the_magic_hooks(monkeypatch):
    import difficulty_sim as ds
    import game_magic
    import sim_magic

    def cell():
        return ds.run_cell(profile='mastery', accuracy=0.95, trials=1, floors=(1, 3),
                           knobs=ds.parse_knobs(''), speed=1.2, engagers=2, seed=5, variants=1)
    a = cell()
    old = dict(int_factor=lambda run: game_magic.int_damage_factor(run.p.INT),
               tier_mult=lambda run, t: game_magic.MAGIC_TIER_MULT.get(int(t), 1.0),
               element=lambda run, fx, el: el, ignores_resistance=lambda run, fx: False,
               sync_mp=lambda run: None, learn=lambda run, item: False,
               escape=lambda run, slow: None, pick_target=lambda run, r, t: t,
               hold=lambda run, t, a, q: False, install_bigfoe=lambda knobs: None)
    for name, fn in old.items():
        monkeypatch.setattr(sim_magic, name, fn)
    b = cell()
    assert a['stats'] == b['stats']


def test_pets_and_flasks_follow_the_careful_blow_only_when_asked():
    import coatings
    import items
    import sim_magic
    run = _run()
    assert sim_magic.pet_bite_mult(run) == 1.0
    run = _run('mg_pet_anchor=1')
    run.floor = 60
    assert abs(sim_magic.pet_bite_mult(run) - sim_magic.ratio_at(60)) < 1e-9 and sim_magic.ratio_at(60) > 1
    flask = items.make_item_by_id('flask', 'flask_of_fire_oil')
    m = _proto('ogre')
    base, dtype = coatings.thrown_damage(flask, m)
    at = coatings.throw_spec(flask)['sized_at']
    try:
        sim_magic.install_flasks({'mg_flask_anchor': 1.0})
        got, dtype2 = coatings.thrown_damage(flask, m)
        assert dtype2 == dtype and got == max(1, int(round(base * sim_magic.ratio_at(float(at)))))
        sim_magic.install_flasks({'mg_flask_anchor': 0.0})
        assert coatings.thrown_damage(flask, m) == (base, dtype)
    finally:
        sim_magic.install_flasks({})
