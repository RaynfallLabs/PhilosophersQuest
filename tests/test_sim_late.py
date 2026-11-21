"""The late game's simulator instruments (tools/balance/sim_late.py,
tools/balance/bane_synth.py; 2026-11-20).

Each knob defaults off and a default cell is the simulator as it was. These
tests hold: the overlay reaching a generated floor's monster and the real
combat multiplier, in this process and back out again; the synthetic overlay's
determinism and its frame (holy kept on demons when asked); a coating, a
thrown flask and a smith's inlay of a new substance meeting its weakness
through the game's own code; supply at 0 being today and supply being
deterministic under a seed; the HP stand-in writing a kind once, by its
affinity and depth and never by the floor it is met on, bosses untouched; a
gaze without a mirror hurting more and with one as today; campaign memory
carrying over; and the default cell being the one before the hooks.
"""
import json
import os
import random
import subprocess
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
os.environ.setdefault('PQ_NO_BONES', '1')

import pytest  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)

NAMED = ('is_boss', 'is_mini_boss', 'is_seal_demon', 'quest_only', 'unique', 'is_allied')


def _ordinary(d):
    return not any(d.get(f) for f in NAMED) and float(d.get('peak_weight', 0) or 0) > 0


@pytest.fixture
def late():
    """sim_late with whatever a test installs taken out again afterwards."""
    import difficulty_sim as ds
    import sim_late
    ds.install_caches()
    yield sim_late
    sim_late.uninstall()


def _write(tmp_path, name, obj):
    p = tmp_path / name
    p.write_text(json.dumps(obj), encoding='utf-8')
    return str(p)


def _cell(knobs='', profile='mastery', floors=(1, 3), seed=3, engagers=2):
    import difficulty_sim as ds
    return ds.run_cell(profile=profile, accuracy=0.95, trials=1, floors=floors,
                       knobs=ds.parse_knobs(knobs), speed=1.2, engagers=engagers, seed=seed,
                       variants=1)


def _old_keys(res, keys=None):
    out = {}
    for f, fs in res['stats'].items():
        ks = keys[f] if keys else fs
        out[f] = {k: fs.get(k) for k in ks}
    return out


# ------------------------------------------------------------------ the knobs

def test_every_late_knob_is_in_the_simulator_and_off():
    import difficulty_sim as ds
    import sim_late
    for k, v in sim_late.KNOBS.items():
        assert ds.KNOB_DEFAULTS[k] == v
    assert ds.KNOB_DEFAULTS['overlay'] == '' and ds.KNOB_DEFAULTS['hp_target'] == 0
    assert ds.KNOB_DEFAULTS['supply'] == 0 and ds.KNOB_DEFAULTS['sig'] == 0
    assert ds.KNOB_DEFAULTS['campaign'] == 1


def test_a_path_knob_is_kept_as_written():
    import difficulty_sim as ds
    k = ds.parse_knobs(r'overlay=C:\some dir\banes.json,sig=1.5,supply=1')
    assert k['overlay'] == r'C:\some dir\banes.json'
    assert k['sig'] == 1.5 and k['supply'] == 1.0
    assert 'overlay=banes.json' in ds.knobs_label(k)


def test_importing_the_simulator_patches_neither_the_data_path_nor_the_blow():
    code = ("import sys; sys.path[:0] = ['src', 'tools/balance']; import paths, monster; "
            "real = paths.data_path; blow = monster.Monster._resolve_blow; "
            "import difficulty_sim, sim_late, bane_synth; "
            "assert paths.data_path is real and monster.Monster._resolve_blow is blow; print('ok')")
    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    out = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env,
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0 and 'ok' in out.stdout, out.stderr[-2000:]


def test_the_cookonly_kid_cooks_as_mastery_and_uses_no_tactics():
    import difficulty_sim as ds
    m, c = ds.PROFILES['mastery'], ds.PROFILES['cookonly']
    assert c['knobs']['tactics'] == 0 and c['knobs']['families'] == 0
    for k in ('cooks_per_floor', 'saver', 'eats_for_hp', 'rest_turns', 'stat_focus', 'pet'):
        assert c.get(k) == m.get(k)
    for k in ('practice', 'untimed', 'traders', 'altars'):
        assert c['knobs'][k] == m['knobs'][k]


# ------------------------------------------------------------------ A. the overlay

def test_the_overlay_reaches_a_generated_floor_and_the_real_multiplier(late, tmp_path):
    import combat
    import coatings
    import difficulty_sim as ds
    import dungeon
    import items
    import kind_data
    import paths
    real_dp = paths.data_path
    # every ordinary kind that can walk floor 45 is weak to a new substance only
    kinds = sorted(k for k, d in MONS.items() if _ordinary(d) and 25 <= (d.get('peak_floor') or 0) <= 65)
    ov = {k: {'weaknesses': ['bane_q'], 'resistances': [], 'shrugs_off': [], 'hp': 777} for k in kinds}
    path = _write(tmp_path, 'ov.json', ov)
    late.install(ds.parse_knobs(f'overlay={path}'))
    try:
        k0 = kinds[0]
        assert kind_data.defs()[k0]['weaknesses'] == ['bane_q']
        assert dungeon._build_spawn_pool(45)[next(k for k in kinds if k in dungeon._build_spawn_pool(45))]['hp'] == 777
        assert 'bane_q' in late.reachable()
        seen = None
        for _ in range(6):
            snap = ds.build_snapshot(45)
            seen = next((m for g in snap.groups for m in g if m.kind in ov), None)
            if seen is not None:
                break
        assert seen is not None, 'no overlay kind on six generated floor-45 maps'
        assert seen.weaknesses == ['bane_q'] and seen.max_hp == 777
        w = items.instantiate_weapon('longsword', 'steel')
        assert combat.weapon_type_multiplier(w, seen)[1] == 1.0
        p = ds.SimPlayer(ds.parse_knobs(''))
        p.weapon = w
        coatings.apply(p, late.make_coating('bane_q', 45))
        assert combat.weapon_type_multiplier(w, seen)[1] == combat.WEAK_TO
    finally:
        late.uninstall()
    assert paths.data_path is real_dp
    assert kind_data.defs()[k0]['weaknesses'] == MONS[k0].get('weaknesses', [])


def test_an_overlay_naming_an_unknown_kind_is_an_error(late, tmp_path):
    import difficulty_sim as ds
    path = _write(tmp_path, 'bad.json', {'no_such_kind_at_all': {'hp': 5}})
    with pytest.raises(ValueError):
        late.install(ds.parse_knobs(f'overlay={path}'))


def test_a_researchers_file_is_read_through_its_proposed_lists(late, tmp_path):
    import difficulty_sim as ds
    import kind_data
    k = sorted(k for k, d in MONS.items() if _ordinary(d) and (d.get('peak_floor') or 0) > 60)[0]
    path = _write(tmp_path, 'research.json', {k: {'name': 'x', 'family': 'y', 'proposed': {
        'weaknesses': ['silver'], 'resistances': ['fire'], 'shrugs_off': []}}})
    late.install(ds.parse_knobs(f'overlay={path}'))
    d = kind_data.defs()[k]
    assert d['weaknesses'] == ['silver'] and d['resistances'] == ['fire']
    assert d['name'] == MONS[k]['name']


# ------------------------------------------------------------------ B. the synthetic overlay

def test_the_synthetic_overlay_is_deterministic_and_keeps_holy_on_demons_when_asked():
    import bane_synth
    a = bane_synth.synth(MONS, pool=5, seed=7)
    b = bane_synth.synth(MONS, pool=5, seed=7)
    assert a == b and a['_meta']['kinds'] > 50
    demon = next(k for k in sorted(a) if not k.startswith('_') and MONS[k].get('family') == 'demons'
                 and 'holy' in (MONS[k].get('weaknesses') or ()))
    assert 'holy' in a[demon]['weaknesses']
    gone = bane_synth.synth(MONS, pool=5, seed=7, keep_holy=False)
    assert 'holy' not in gone[demon]['weaknesses']
    for k, v in a.items():
        if k.startswith('_'):
            continue
        assert not set(v['weaknesses']) & {'fire', 'cold', 'lightning'}
        assert (MONS[k].get('peak_floor') or 0) >= 41 and _ordinary(MONS[k])
        pool = bane_synth.domain_pool(bane_synth.domain_of(MONS[k]['peak_floor']), 5, 7)
        assert set(v['weaknesses']) & set(pool)
    assert bane_synth.synth(MONS, particular=0.0)['_meta']['kinds'] == 0
    half = {k for k in bane_synth.synth(MONS, particular=0.5) if not k.startswith('_')}
    more = {k for k in bane_synth.synth(MONS, particular=0.8) if not k.startswith('_')}
    assert half < more


def test_the_synthetic_overlay_spreads_the_answers():
    import bane_synth
    now = bane_synth.concentration(MONS, 61, 80)
    after = bane_synth.concentration(bane_synth.apply(MONS, bane_synth.synth(MONS, pool=6)), 61, 80)
    assert len(after['cover80']) > len(now['cover80'])
    assert after['top'][0][1] < now['top'][0][1]


# ------------------------------------------------------------------ C. carriers

def _proto(kind, **kw):
    from monster import Monster
    m = Monster({**MONS[kind], 'id': kind}, 0, 0)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def test_a_new_substance_meets_its_weakness_coated_thrown_and_inlaid(late):
    import combat
    import coatings
    import difficulty_sim as ds
    import items
    kind = sorted(k for k, d in MONS.items() if _ordinary(d) and (d.get('peak_floor') or 0) > 60)[0]
    m = _proto(kind, weaknesses=['bane_z'], resistances=['slash', 'pierce', 'blunt'], shrugs_off=[],
               tags=[])
    w = items.instantiate_weapon('longsword', 'steel')
    assert combat.weapon_type_multiplier(w, m) == (combat.RESISTED, 1.0)
    p = ds.SimPlayer(ds.parse_knobs(''))
    p.weapon = w
    flask = late.make_coating('bane_z', 70)
    assert coatings.coat_spec(flask)['substance'] == 'bane_z'
    assert late.carrier_blows(flask) == 20
    coatings.apply(p, flask)
    assert combat.weapon_type_multiplier(w, m) == (combat.RESISTED, combat.WEAK_TO)
    # thrown: the real Monster.take_damage takes the weak step
    t = late.make_throw('bane_z', 70)
    dmg, dtype = coatings.thrown_damage(t, m)
    assert dtype == 'bane_z' and dmg > 0
    m.hp = m.max_hp = 10 ** 7
    plain = _proto(kind, weaknesses=[], resistances=[], shrugs_off=[], tags=[])
    plain.hp = plain.max_hp = 10 ** 7
    assert m.take_damage(dmg, dtype) == 2 * plain.take_damage(dmg, dtype)
    # inlaid for good: substance, not a form
    w2 = items.instantiate_weapon('longsword', 'steel')
    assert late.bane_inlay(w2, 'bane_z')
    assert combat.weapon_type_multiplier(w2, m) == (combat.RESISTED, combat.WEAK_TO)
    assert not late.bane_inlay(w2, 'bane_y')               # one inlay a weapon (smithing's rule)
    # the game's own carriers for the game's own substances
    assert late.make_coating('holy', 70).id == 'water_of_life'
    assert late.make_throw('acid', 70).id == 'alkahest'


# ------------------------------------------------------------------ the default cell

def test_the_default_cell_is_the_one_before_the_late_hooks(monkeypatch):
    """Every late knob off: the same seeded cell, stat for stat, as with the
    late hooks taken out of the simulator (the counters left aside)."""
    import sim_late
    from monster import Monster
    a = _cell('', 'mastery', (1, 3), seed=5)
    nohook = dict(blow_pre=lambda run, t: None, blow_post=lambda run, t, pre: None,
                  on_record=lambda run, m: None, on_fight=lambda run, g: None,
                  prep=lambda run, g: None, unprep=lambda run: None,
                  floor_start=lambda run, f: None, shop=lambda *a, **k: None,
                  on_coat=lambda *a: None, after_coat=lambda *a: None, on_throw=lambda *a: None,
                  on_shed=lambda *a: None, run_end=lambda run: None, kit=lambda run: [],
                  aura_begin=lambda run: None, aura_end=lambda run: None)
    for name, fn in nohook.items():
        monkeypatch.setattr(sim_late, name, fn)
    if 'resolve' in sim_late._ORIG:
        monkeypatch.setattr(Monster, '_resolve_blow', sim_late._ORIG['resolve'])
    b = _cell('', 'mastery', (1, 3), seed=5)
    keys = {f: list(fs) for f, fs in b['stats'].items()}
    assert _old_keys(a, keys) == _old_keys(b)
    assert any(fs.get('kb_p') or fs.get('kb_a') for fs in a['stats'].values())   # it did count


# ------------------------------------------------------------------ D. supply

def test_supply_zero_is_today_and_supply_is_seeded(late):
    a = _cell('', 'mastery', (1, 4), seed=9)
    z = _cell('supply=0,supply_ahead=3', 'mastery', (1, 4), seed=9)
    assert _old_keys(a) == _old_keys(z)
    s1 = _cell('supply=3', 'mastery', (1, 4), seed=9)
    s2 = _cell('supply=3', 'mastery', (1, 4), seed=9)
    assert s1['stats'] == s2['stats']
    tot = {}
    for fs in s1['stats'].values():
        for k in ('sup_found', 'sup_offered_stall', 'sup_missed', 'sup_unsold', 'sup_bought'):
            tot[k] = tot.get(k, 0) + fs.get(k, 0)
    assert sum(tot.values()) > 0
    assert not any(fs.get('sup_found') or fs.get('sup_offered_stall') for fs in a['stats'].values())


def test_supply_follows_the_residents_ahead(late):
    w = late.window(45, 5)
    assert w['floors'] == 6 and w['demand']
    import domain_counters
    kinds = {k for f in range(45, 51) for k, _s, _d in domain_counters._floor_kinds(f)}
    for sub, ks in w['kinds'].items():
        assert ks <= kinds
        assert all(sub in late.kind_subs(k, late.active_defs()[k]) for k in ks)


# ------------------------------------------------------------------ E. the HP stand-in

def test_the_hp_stand_in_writes_a_kind_once_by_its_affinity_never_by_the_floor(late):
    import difficulty_sim as ds
    import kind_data
    from monster import Monster
    knobs = ds.parse_knobs('hp_target=1.7')
    late.install(knobs)
    rows = {r[0]: r for r in late._STATE['hp_rows']}
    deep = sorted(k for k, d in MONS.items() if _ordinary(d) and (d.get('peak_floor') or 0) >= 21)
    assert set(rows) == set(deep)
    for kind, (k, pk, how, step, old, new) in list(rows.items())[:40]:
        assert kind_data.defs()[kind]['hp'] == new
        ans, plain = late.steps(MONS[kind])
        b, st = (1.7, ans) if ans is not None else (2.0, plain)
        assert how == ('answered' if ans is not None else 'plain')
        want = max(1, int(round(late.x_for_blows(b, pk) * late.careful_blow(pk) * st)))
        assert new == want
    # bosses, seal demons and the shallow untouched
    for kind, d in MONS.items():
        if d.get('is_boss') or d.get('is_seal_demon') or (d.get('peak_floor') or 0) < 21:
            assert kind not in rows and kind_data.defs()[kind]['hp'] == d['hp']
    # the same health wherever it is met (it is the kind's, not the floor's)
    k = deep[len(deep) // 2]
    a = ds.fresh_monster(Monster({**kind_data.defs()[k], 'id': k}, 0, 0), knobs, 41)
    b = ds.fresh_monster(Monster({**kind_data.defs()[k], 'id': k}, 0, 0), knobs, 97)
    assert a.max_hp == b.max_hp == rows[k][5]
    # written from the data as it is, once: a second install is no second rewrite
    late.install(knobs)
    assert kind_data.defs()[k]['hp'] == rows[k][5]
    late.install(ds.parse_knobs('hp_target=2.5'))
    k2 = next(x for x in deep if late.steps(MONS[x])[0] is not None)
    want = int(round(late.x_for_blows(2.5, MONS[k2]['peak_floor']) * late.careful_blow(MONS[k2]['peak_floor'])
                     * late.steps(MONS[k2])[0]))
    assert kind_data.defs()[k2]['hp'] == max(1, want)


def test_the_hp_stand_in_depends_on_the_kinds_affinity(late, tmp_path):
    import difficulty_sim as ds
    import kind_data
    a, b = sorted(k for k, d in MONS.items() if _ordinary(d) and 55 <= (d.get('peak_floor') or 0) <= 65)[:2]
    pk = MONS[a]['peak_floor']
    ov = {a: {'weaknesses': ['silver'], 'resistances': [], 'shrugs_off': [], 'tags': []},
          b: {'weaknesses': [], 'resistances': ['slash', 'pierce', 'blunt'], 'shrugs_off': [],
              'peak_floor': pk, 'tags': []}}
    path = _write(tmp_path, 'aff.json', ov)
    late.install(ds.parse_knobs(f'overlay={path},hp_target=1.7,hp_plain=2.0'))
    ha, hb = kind_data.defs()[a]['hp'], kind_data.defs()[b]['hp']
    assert late.steps(kind_data.defs()[a]) == (2.0, 1.0)
    assert late.steps(kind_data.defs()[b]) == (None, 0.5)
    assert ha == int(round(late.x_for_blows(1.7, pk) * late.careful_blow(pk) * 2.0))
    assert hb == int(round(late.x_for_blows(2.0, pk) * late.careful_blow(pk) * 0.5))
    assert ha > hb


def test_more_hp_takes_more_blows():
    import sim_late
    xs = [sim_late.x_for_blows(b, 70) for b in (1.2, 1.7, 2.5, 4.0)]
    assert xs == sorted(xs) and xs[0] < xs[-1]
    for b in (1.7, 2.5, 4.0):
        assert abs(sim_late.blows_to_kill(sim_late.x_for_blows(b, 70), 70) - b) < 0.05


# ------------------------------------------------------------------ F. signature attacks

def _gazer(ds, run):
    m = _proto('ogre')
    m.attacks = [{'name': 'Withering Gaze', 'damage': '20d10', 'type': 'magic', 'delivery': 'gaze'}]
    m.multi_attack_count = 0
    m.thac0 = -40
    return ds.fresh_monster(m, run.knobs, 60)


def _gaze_total(knobs, mirror, seeds=30):
    import difficulty_sim as ds
    import items
    import sim_late
    sim_late.install_runtime()
    tot = 0
    for s in range(seeds):
        run = ds.Run(ds.FloorCache(1), 'unprepared', 0.95, 1.0, 'greedy', 1, ds.parse_knobs(knobs))
        run.fs = ds.new_floor_stats()
        run.floor = 60
        run.p.max_hp = run.p.hp = 10 ** 6
        if mirror:
            run.p.shield = items.instantiate_shield('mirror_shield', 'steel')
        m = _gazer(ds, run)
        random.seed(1000 + s)
        before = run.p.hp
        m.attack(run.p)
        tot += before - run.p.hp
    return tot, run.fs


def test_a_gaze_without_a_mirror_hurts_more_and_with_one_is_as_today():
    base, fs0 = _gaze_total('', mirror=False)
    sig, fs1 = _gaze_total('sig=1.5', mirror=False)
    assert base > 0 and 1.35 < sig / base < 1.65
    assert fs1['sig_bare'].get('gaze')
    mir0, _ = _gaze_total('', mirror=True)
    mir1, fs2 = _gaze_total('sig=1.5', mirror=True)
    assert mir1 == mir0
    assert fs2['sig_ctr'].get('gaze') and not fs2.get('sig_bare')


def test_wax_and_a_resistance_are_counters():
    import difficulty_sim as ds
    import items
    import sim_late
    run = ds.Run(ds.FloorCache(1), 'unprepared', 0.95, 1.0, 'greedy', 1, ds.parse_knobs('sig=1.5'))
    p = run.p
    voice = {'name': 'Wail', 'damage': '2d6', 'type': 'magic', 'delivery': 'voice'}
    breath = {'name': 'Fire Breath', 'damage': '6d6', 'type': 'fire', 'delivery': 'breath'}
    m = _proto('ogre')
    assert not sim_late.has_counter(p, m, voice, 'voice')
    plugs = items.make_item_by_id('accessory', 'beeswax_earplugs')
    p.inventory.append(plugs)
    p.ears_stopped = True
    assert sim_late.has_counter(p, m, voice, 'voice')
    assert not sim_late.has_counter(p, m, breath, 'breath')
    p.add_effect('fire_resist', 50)
    assert sim_late.has_counter(p, m, breath, 'breath')
    assert sim_late.sig_of({'name': 'Life Drain', 'damage': '1d6', 'type': 'drain'}) == 'drain'


# ------------------------------------------------------------------ H. campaign memory

def test_campaign_memory_carries_over(monkeypatch):
    import difficulty_sim as ds
    import sim_late
    made = []

    class Rec(ds.Run):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            made.append(self)
    monkeypatch.setattr(ds, 'Run', Rec)
    monkeypatch.setattr(sim_late, 'learned', lambda run: {'goblin', f'kind{len(made)}'})
    res = _cell('campaign=3', 'unprepared', (1, 2), seed=4, engagers=1)
    assert len(made) == 3 and res['trials'] == 3
    assert made[0].late_memory == set()
    assert made[1].late_memory == {'goblin', 'kind1'}
    assert made[2].late_memory == {'goblin', 'kind1', 'kind2'}
    assert made[2]._knows('goblin') and not made[0]._knows('goblin')
    camp = res['late']['campaign']
    assert [c['runs'] for c in camp] == [1, 1, 1]
    assert all(len(c['floors']) == 1 for c in camp)


def test_what_the_death_screen_teaches():
    import difficulty_sim as ds
    import sim_late
    run = ds.Run(ds.FloorCache(1), 'unprepared', 0.95, 1.0, 'greedy', 1, ds.parse_knobs(''))
    run.ever_died, run.last_hit_by = True, 'ogre'
    run.late['dmg_by_kind'] = {'rat': 0.1, 'wolf': 0.9, 'bat': 0.5, 'orc': 0.4, 'ogre': 0.2}
    assert sim_late.learned(run) == {'ogre', 'wolf', 'bat', 'orc'}


# ------------------------------------------------------------------ I. the report

def test_the_summary_reads_a_cell(late):
    import io
    res = _cell('supply=1,sig=1.5', 'mastery', (1, 3), seed=2)
    buf = io.StringIO()
    late.summary(res, buf, name='smoke')
    text = buf.getvalue()
    assert 'smoke' in text and '1-20' in text and 'survive' in text


def test_the_counters_weigh_and_the_spare_ones_are_left_over_his_line():
    """The kit supply gives him (counters, resistance potions) is in the load
    Run._fit_pack keeps under his line: potions go first, then the mirror."""
    import difficulty_sim as ds
    import sim_late
    run = ds.Run(ds.FloorCache(1), 'mastery', 0.95, 1.0, 'greedy', 1, ds.parse_knobs('supply=1'))
    run.fs = ds.new_floor_stats()
    mirror = sim_late._make_counter('mirror', 40)
    pots = [sim_late._make_counter('potion', 40, 'fire') for _ in range(300)]
    assert mirror is not None and all(p is not None for p in pots)
    run.late['kit'] = [mirror] + pots
    run.late['mirror'] = mirror
    run._sync_pack()
    kept = run.late['kit']
    assert mirror in kept and len(kept) < 301
    assert run.p.get_current_weight() <= run._pack_line() + 1.0
    assert run.fs.get('sup_shed_ctr', 0) == 301 - len(kept)
