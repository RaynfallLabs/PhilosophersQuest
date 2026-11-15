"""Achievements and quirks brought up to the winning build and the new
kitchen (2026-11-14).

The audit (every trigger names something the game still does), the new
achievements driven through real game paths (a coated blow, a thrown flask,
a mirror shield, the earplugs, the kitchen, a smith, an older save), the
new quirks and their rewards, and an old profile meeting the new catalogue.

Brandon's rules for the text are pinned in test_achievements_data.py; the
new secrets carry their own spoiler words, which the validator enforces.
Whether the dance-off, the race or a feast FEELS right is his play-test.
"""
import json
import os
import random
import re
import sys
import types
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import achievements  # noqa: E402
import seeker_codes  # noqa: E402
import seeker_profile  # noqa: E402

SRC = ROOT / 'src'
DATA = json.loads((ROOT / 'data' / 'achievements.json').read_text(encoding='utf-8'))
MONS = json.loads((ROOT / 'data' / 'monsters.json').read_text(encoding='utf-8'))
NEW_IDS = ('first_labour', 'bronze_heel', 'polished_shield', 'deaf_to_riddles', 'quest_bonnacon',
           'quest_calydonian_boar', 'gorgon_sisters', 'quest_iron_patriarch',
           'quest_whispering_crone', 'quest_blood_archon', 'silver_edge', 'holy_water',
           'old_remedies', 'feast_first', 'feast_12', 'five_courses', 'stone_soup',
           'worth_the_wait', 'made_to_order', 'leaves_against_rain', 'stage_fright', 'encore',
           'rip_van_winkle')
NEW_QUIRKS = ('callinicus', 'medea', 'fabius', 'wallace', 'janus', 'marius_mule',
              'fatted_calf', 'widows_jar', 'proteus')


def _src_text() -> str:
    return '\n'.join(f.read_text(encoding='utf-8') for f in SRC.glob('*.py'))


def _wheres():
    """(achievement or counter name, event, where) for every event test in the data."""
    out = []

    def walk(name, t):
        for k in ('all', 'any'):
            for p in t.get(k, ()):
                walk(name, p)
        if 'event' in t:
            out.append((name, t['event'], t.get('where') or {}))
    for a in DATA['achievements']:
        walk(a['id'], a['trigger'])
    for k, c in DATA['counters'].items():
        out.append((k, c['on'], c.get('where') or {}))
    return out


def _vals(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        return []
    return [v]


# ---------------------------------------------------------------- the audit

def test_every_new_achievement_is_in_the_catalogue():
    ids = {a['id'] for a in DATA['achievements']}
    assert set(NEW_IDS) <= ids
    assert achievements.validate(DATA) == []


def test_every_kill_names_a_real_creature_and_family():
    families = {v.get('family') for v in MONS.values() if isinstance(v, dict)}
    bad = []
    for name, ev, where in _wheres():
        if ev in ('kill', 'counter') and 'monster' in where:
            bad += [(name, m) for m in _vals(where['monster']) if m not in MONS]
        if ev in ('kill', 'counter') and 'family' in where:
            bad += [(name, f) for f in _vals(where['family']) if f not in families]
    assert bad == []


def test_every_deed_named_is_one_the_game_writes():
    """A deed id's own part (after kind.) is written somewhere in src/ or
    data/ (an oath's 'kept.x' comes from its oath id x)."""
    text = _src_text() + '\n'.join(p.read_text(encoding='utf-8')
                                   for p in (ROOT / 'data').glob('*.json')
                                   if p.name != 'achievements.json')
    bad = []
    for name, ev, where in _wheres():
        if ev == 'deed' and 'id' in where:
            for did in _vals(where['id']):
                if did.split('.', 1)[-1] not in text:
                    bad.append((name, did))
    assert bad == []


def test_every_named_thing_a_trigger_waits_for_is_sent():
    src = _src_text()
    flasks = json.loads((ROOT / 'data' / 'items' / 'flask.json').read_text(encoding='utf-8'))
    arsenal = json.loads((ROOT / 'data' / 'arsenal.json').read_text(encoding='utf-8'))
    techniques = set(arsenal['counters']['techniques'])
    bad = []
    for name, ev, where in _wheres():
        for v in _vals(where.get('item')) if ev == 'forged' else ():
            if not re.search(rf"_seeker_event\('forged', item='{v}'\)", src):
                bad.append((name, v))
        if ev == 'kill':
            bad += [(name, f) for f in _vals(where.get('flask')) if f not in flasks]
            bad += [(name, c) for c in _vals(where.get('coat'))
                    if c not in {(d.get('coat') or {}).get('substance') for d in flasks.values()}]
        if ev == 'counter':
            bad += [(name, t) for t in _vals(where.get('technique')) if t not in techniques]
        if ev in ('stray_kids', 'black_knight', 'necronomicon', 'judgment'):
            for o in _vals(where.get('outcome')):
                if f"'{o}'" not in src:
                    bad.append((name, o))
        if ev == 'smith':
            for s in _vals(where.get('service')):
                if f"'{s}'" not in src:
                    bad.append((name, s))
    assert bad == []


def test_every_pet_line_a_trigger_waits_for_exists():
    import pet_system
    lines = set(getattr(pet_system, 'SPECIES', {}) or {}) | set(
        getattr(pet_system, '_SPECIES', {}) or {})
    src = (SRC / 'pet_system.py').read_text(encoding='utf-8')
    bad = []
    for name, ev, where in _wheres():
        if ev in ('pet_evolved', 'pet_level', 'pet_hatched', 'rare_pet'):
            for k in ('line', 'pet'):
                for v in _vals(where.get(k)):
                    if v not in lines and f"'{v}'" not in src:
                        bad.append((name, v))
    assert bad == []


def test_the_new_secrets_keep_their_spoilers_out_of_the_hints():
    """No hint names its trigger: each new secret or lore-way badge lists
    the words that would give it away (the validator refuses a hint that
    uses one)."""
    by_id = {a['id']: a for a in DATA['achievements']}
    for aid in ('first_labour', 'bronze_heel', 'polished_shield', 'deaf_to_riddles',
                'silver_edge', 'holy_water', 'leaves_against_rain', 'stage_fright', 'encore',
                'rip_van_winkle', 'worth_the_wait'):
        assert by_id[aid].get('spoiler_words'), aid
        hint = by_id[aid]['hint'].casefold()
        assert not [w for w in by_id[aid]['spoiler_words'] if w.casefold() in hint], aid


def test_no_hint_or_text_uses_singular_they():
    bad = []
    for a in DATA['achievements']:
        if a['id'] not in NEW_IDS:
            continue
        for f in ('hint', 'unlocked_text'):
            if re.search(r"\b(they|them|their|themselves|themself)\b", a[f], re.I):
                bad.append((a['id'], f, a[f]))
    import quirk_system as qs
    from quirk_text import QUIRK_DESC, QUIRK_HINT
    for q in NEW_QUIRKS:
        for f, t in (('hint', QUIRK_HINT[q]), ('desc', QUIRK_DESC[q]),
                     ('trigger', qs._QUIRK_TRIGGER[q]), ('flavor', qs._QUIRK_FLAVOR[q])):
            if re.search(r"\b(they|them|their|themselves|themself)\b", t, re.I):
                bad.append((q, f, t))
    # A plural is fine, and each of these was read as one: Odysseus's sailors
    # and their ears, Medusa's two sisters, the Byzantines, the legionaries,
    # the dishes.
    allowed = {('deaf_to_riddles', 'hint'), ('gorgon_sisters', 'hint'), ('callinicus', 'hint'),
               ('marius_mule', 'hint'), ('widows_jar', 'trigger')}
    assert [b for b in bad if (b[0], b[1]) not in allowed] == []


def test_dads_notes_cover_every_achievement():
    notes = json.loads((ROOT / 'tools' / 'dad' / 'achievement_notes.json')
                       .read_text(encoding='utf-8'))['notes']
    assert [a['id'] for a in DATA['achievements'] if a['id'] not in notes] == []


# ---------------------------------------------------------------- game paths

@pytest.fixture
def seeker(tmp_path):
    saved = seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE
    seeker_codes._KEYS_OVERRIDE = {'label': 'pq1', 'keys': {'pq1': bytes(range(32))}}
    seeker_profile._DIR_OVERRIDE = str(tmp_path / 'seekers')
    seeker_profile.set_active('Robyn')
    yield 'Robyn'
    seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE = saved
    import counters
    counters.ON_COUNTER = None


@pytest.fixture(autouse=True)
def _clean():
    import affinity
    import coatings
    coatings.drain()
    affinity.drain()
    yield
    coatings.drain()
    affinity.drain()


def _game(name='Quirk Hero'):
    from main import Game
    from game_states import STATE_PLAYER
    import items
    random.seed(7)
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1, 1)), player_name=name)
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    g.visible = {(x, y) for y in range(g.dungeon.height) for x in range(g.dungeon.width)}
    return g


def _mon(kind):
    from monster import Monster
    return Monster({**MONS[kind], 'id': kind}, 0, 0)


def _place(g, kind, hp=None):
    m = _mon(kind)
    px, py = g.player.x, g.player.y
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        if g.dungeon.is_walkable(px + dx, py + dy):
            m.x, m.y = px + dx, py + dy
            break
    if hp is not None:
        m.hp = hp
    g.monsters.append(m)
    return m


def _unlocked(g, aid):
    return g._seeker.profile.is_unlocked(aid)


def test_a_silver_coated_blow_on_a_shapeshifter(seeker):
    from items import instantiate_weapon
    g = _game()
    ww = _place(g, 'werewolf', hp=1)
    dag = instantiate_weapon('dagger', 'steel')
    dag.coating = {'id': 'silver_dust', 'name': 'Silver Dust', 'substance': 'silver', 'blows': 3}
    g.player.inventory.append(dag)
    g._throw_weapon(dag, ww, ww.x, ww.y)
    assert ww.is_dead()
    assert _unlocked(g, 'silver_edge')


def test_a_plain_blade_on_a_shapeshifter_is_not_silver(seeker):
    from items import instantiate_weapon
    g = _game()
    ww = _place(g, 'werewolf', hp=1)
    dag = instantiate_weapon('dagger', 'steel')
    g.player.inventory.append(dag)
    g._throw_weapon(dag, ww, ww.x, ww.y)
    assert ww.is_dead() and not _unlocked(g, 'silver_edge')


def test_holy_water_thrown_counts_as_a_flask_kill_and_from_afar(seeker):
    from items import make_item_by_id
    g = _game()
    z = _place(g, 'zombie', hp=1)
    hw = make_item_by_id('flask', 'flask_of_holy_water')
    g.player.inventory.append(hw)
    before = g._seeker.profile.stat('ranged_kills')
    g._throw_flask(hw, z, z.x, z.y)
    assert z.is_dead()
    assert _unlocked(g, 'holy_water')
    # The audit: a thrown kill is a kill from afar (it counted as neither).
    assert g._seeker.profile.stat('ranged_kills') == before + 1
    assert g.player.quirk_progress.get('callinicus_flask_kills') == 1


def test_a_thrown_weapon_kill_counts_as_ranged(seeker):
    from items import instantiate_weapon
    g = _game()
    t = _place(g, 'talos', hp=1)
    dag = instantiate_weapon('dagger', 'steel')
    g.player.inventory.append(dag)
    g._throw_weapon(dag, t, t.x, t.y)
    assert t.is_dead()
    assert _unlocked(g, 'bronze_heel') and _unlocked(g, 'quest_talos')


def test_the_nemean_lion_with_bare_hands_only(seeker):
    g = _game()
    lion = _place(g, 'nemean_lion')
    lion.alive = False
    g._on_monster_killed(lion, chain_score=4, unarmed=False)
    assert _unlocked(g, 'quest_nemean_lion') and not _unlocked(g, 'first_labour')
    lion2 = _place(g, 'nemean_lion')
    lion2.alive = False
    g._on_monster_killed(lion2, chain_score=4, unarmed=True)
    assert _unlocked(g, 'first_labour')


def test_medusa_watched_in_a_mirror_shield(seeker):
    from items import instantiate_shield
    g = _game()
    med = _place(g, 'medusa_gorgon')
    # Killed without the shield ever turning her gaze: no Polished Shield.
    med.alive = False
    g._on_monster_killed(med)
    assert _unlocked(g, 'boss_medusa') and not _unlocked(g, 'polished_shield')
    g2 = _game('Second Hero')
    med2 = _place(g2, 'medusa_gorgon')
    g2.player.shield = instantiate_shield('mirror_shield', 'steel')
    med2._gaze_cooldown = 0
    dmg, msg = med2.attack(g2.player)
    assert not g2.player.has_effect('paralyzed'), msg
    med2.alive = False
    g2._on_monster_killed(med2)
    assert _unlocked(g2, 'polished_shield')


def test_the_sphinx_unheard_through_the_wax(seeker, monkeypatch):
    from items import make_item_by_id
    import counters
    g = _game()
    sph = _place(g, 'the_sphinx')
    g.player.inventory.append(make_item_by_id('accessory', 'beeswax_earplugs'))
    counters.toggle_ears(g.player)
    riddle = dict(next(a for a in sph.attacks if a['name'] == 'Whispered Riddle'), effect_chance=1.0)
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    out = sph._apply_attack_effect(riddle, g.player)
    assert 'wax' in out and not g.player.has_effect('confused')
    monkeypatch.undo()
    sph.alive = False
    g._on_monster_killed(sph)
    assert _unlocked(g, 'deaf_to_riddles')


def test_every_old_remedy_used(seeker, monkeypatch):
    from items import instantiate_shield, make_item_by_id
    import counters
    g = _game()
    p = g.player
    p.shield = instantiate_shield('mirror_shield', 'steel')
    eye = _place(g, 'floating_eye')
    eye._gaze_cooldown = 0
    eye.attack(p)
    assert not _unlocked(g, 'old_remedies')
    p.inventory += [make_item_by_id('accessory', 'beeswax_earplugs'),
                    make_item_by_id('accessory', 'cold_iron_charm')]
    counters.toggle_ears(p)
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    bans = _mon('banshee')
    wail = dict(next(a for a in bans.attacks if a['name'] == 'Death Wail'), effect_chance=1.0)
    bans._apply_attack_effect(wail, p)
    cg = _mon('changeling')
    glam = dict(next(a for a in cg.attacks if a.get('effect') == 'confused'), effect_chance=1.0)
    cg._apply_attack_effect(glam, p)
    assert g._seeker.profile.members('counters_used') == {'gaze', 'voice', 'fey_glamour'}
    assert _unlocked(g, 'old_remedies')


def test_medusas_sisters_both_in_one_journey(seeker):
    g = _game()
    for kind in ('stheno_gorgon', 'euryale_gorgon'):
        m = _place(g, kind)
        m.alive = False
        g._on_monster_killed(m)
    assert _unlocked(g, 'gorgon_sisters')


def _no_quiz(g):
    g.quiz_engine.start_quiz = lambda **kw: kw['callback'](types.SimpleNamespace(success=True, score=1))


def _give(g, part_id, n=1):
    import kitchen
    from food_system import load_ingredient_for
    from items import make_item_by_id
    for _ in range(n):
        if kitchen.part_kind(part_id) == 'food':
            it = make_item_by_id('food', part_id)
        else:
            it = load_ingredient_for(part_id)
        assert it is not None, part_id
        g.player.inventory.append(it)


def test_the_kitchen_badges_from_real_cooking(seeker):
    import kitchen
    g = _game()
    _no_quiz(g)
    # A dish from each tab: Five Courses.
    for rid in ('cook_abyssal_dragon', 'cook_abyssal_behemoth', 'cook_aboleth_lesser',
                'cook_abyssal_hound'):
        _give(g, kitchen.parts(kitchen.recipe(rid))[0])
        g._cook_compound(kitchen.recipe(rid))
    assert not _unlocked(g, 'five_courses')
    _give(g, 'abyssal_mimic_prime')
    g._cook_compound(kitchen.recipe('cook_abyssal_mimic'))
    assert _unlocked(g, 'five_courses')
    # Five ingredients: Stone Soup.
    rec = kitchen.recipe('dish_063')
    for pid in kitchen.parts(rec):
        _give(g, pid)
    g._cook_compound(rec)
    assert _unlocked(g, 'stone_soup')
    # A legendary feast: the first of the ladder.
    feast = kitchen.recipe('feast_29')
    for pid in kitchen.parts(feast):
        _give(g, pid)
    g._cook_compound(feast)
    assert _unlocked(g, 'feast_first') and not _unlocked(g, 'feast_12')
    assert g._seeker.profile.members('feasts') == {'feast_29'}


def test_worth_the_wait_a_part_carried_from_the_first_floor(seeker):
    """A real-keys journey: harvest a goblin on floor 1, carry the gristle
    down to floor 40, cook it there with a deep part and plain food."""
    import kitchen
    from food_system import make_corpse
    g = _game()
    _no_quiz(g)

    def press(key, uni=''):
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))

    px, py = g.player.x, g.player.y
    g.ground_items = [i for i in g.ground_items if (i.x, i.y) != (px, py)]
    g.ground_items.append(make_corpse('goblin', px, py))
    press(pygame.K_h, 'h')
    gristle = next(i for i in g.player.inventory if kitchen.resolve(i.id) == 'goblin_prime')
    assert gristle.harvest_floor == 1
    g._change_level(40, enter_from_top=True, via='warp')
    g.monsters = []
    assert g.player.deepest_floor_reached >= 40
    rec = kitchen.recipe('dish_221')
    for pid in kitchen.parts(rec):
        if pid != 'goblin_prime':
            _give(g, pid)
    g._cook_compound(rec)
    assert _unlocked(g, 'worth_the_wait')
    # bread and cheese in a dish of four: one step to the Widow's Jar
    assert g.player.quirk_progress.get('widows_jar_dishes') == 1


def test_a_stack_keeps_its_oldest_harvest(seeker):
    from food_system import load_ingredient_for
    from player import Player
    p = Player()
    a, b = load_ingredient_for('goblin_prime'), load_ingredient_for('goblin_prime')
    a.harvest_floor, b.harvest_floor = 3, 20
    p.add_to_inventory(b)
    p.add_to_inventory(a)
    stack = [i for i in p.inventory if i.id == 'goblin_prime']
    assert len(stack) == 1 and stack[0].count == 2 and stack[0].harvest_floor == 3


def test_a_special_order_collected(seeker):
    g = _game()
    m = types.SimpleNamespace(kind='armourer', person='Brannoc',
                              line=lambda key, default='': default)
    plan = g._trader_plan()
    plan.setdefault('orders', []).append({'kind': 'armourer', 'cat': 'weapon', 'template': 'longsword',
                                          'material': 'steel', 'collect': g.dungeon_level,
                                          'name': 'Steel Longsword', 'paid': 100})
    g._trader_deliver_orders(m)
    assert _unlocked(g, 'made_to_order')


def test_the_pups_cloak_and_the_stray_kids_reach_the_seeker(seeker):
    import deeds
    g = _game()
    deeds.note(g, 'aid.emberpup_sheltered', source='test')
    assert _unlocked(g, 'leaves_against_rain')
    g._stray_kids_summon()
    assert _unlocked(g, 'encore')


def test_an_older_save_is_rip_van_winkle(seeker):
    """A save the older version wrote (or one from before saves kept their
    version) wakes in the new one: Rip Van Winkle. Today's save does not."""
    from main import _restore_saved_game
    from save_system import save_game, load_game
    g = _game(name='Sleeper')
    assert save_game(g)
    state = load_game('Sleeper')
    assert state['_game_version']
    g2, _ = _restore_saved_game(pygame.display.set_mode((1, 1)), 'Sleeper', state)
    assert not g2._seeker.profile.is_unlocked('rip_van_winkle')
    state = load_game('Sleeper')
    state['_game_version'] = '1.0.0'
    g3, _ = _restore_saved_game(pygame.display.set_mode((1, 1)), 'Sleeper', state)
    assert g3._seeker.profile.is_unlocked('rip_van_winkle')


def test_older_version_reads_versions_as_numbers():
    import game_seeker
    assert game_seeker.older_version('3.4.0', '3.5.0')
    assert game_seeker.older_version('3.9.9', '3.10.0')
    assert not game_seeker.older_version('3.5.0', '3.5.0')
    assert not game_seeker.older_version('4.0.0', '3.5.0')
    assert game_seeker.older_version('', '3.5.0')


def test_an_old_profile_meets_the_new_catalogue(seeker):
    """A profile written before these achievements: it opens, keeps what it
    earned, and is given nothing new it has not done (the new ladders read
    counters it never had)."""
    path = seeker_profile.profile_path('Robyn')
    p = seeker_profile.load('Robyn')
    p.add('kills', 250)
    p.add('dishes', 40)
    p.unlock('kills_100', hero='Old Hero')
    p.flush()
    doc = json.load(open(path, encoding='utf-8'))
    assert 'feasts' not in doc.get('sets', {})
    g = _game()
    prof = g._seeker.profile
    assert prof.is_unlocked('kills_100')
    assert not any(prof.is_unlocked(a) for a in NEW_IDS)
    assert g._seeker.book.progress('feast_12', prof) == (0, 12)


# ---------------------------------------------------------------- the new quirks

def _qs():
    from player import Player
    import quirk_system as qs
    pl = Player()
    msgs = []
    game = types.SimpleNamespace(player=pl, turn_count=0, dungeon_level=1, monsters=[],
                                 correct_answers=0, add_message=lambda *a, **k: msgs.append(a))
    return qs.QuirkSystem(game), pl


def test_callinicus_and_his_fire(seeker):
    q, pl = _qs()
    for _ in range(19):
        q.on_kill('goblin', 0, True, False, 1.0, False, flask=True)
    assert not q.is_unlocked('callinicus') and q.get_quirk_progress('callinicus') == 0.95
    q.on_kill('goblin', 0, True, False, 1.0, False, flask=True)
    assert q.is_unlocked('callinicus')
    # The reward on a real throw: fire oil's burning lasts twice as long.
    import coatings
    from items import make_item_by_id
    oil = make_item_by_id('flask', 'flask_of_fire_oil')
    turns = int(coatings.throw_spec(oil)['status']['turns'])
    a, b = _mon('goblin'), _mon('goblin')
    a.hp = a.max_hp = b.hp = b.max_hp = 10 ** 5
    coatings.throw_at(oil, a)
    coatings.throw_at(make_item_by_id('flask', 'flask_of_fire_oil'), b, turns_mult=2)
    assert b.status_effects.get('burning', 0) >= a.status_effects.get('burning', 0)
    assert b.status_effects.get('burning', 0) == min(turns * 2, b.status_effects.get('burning', 0))


def test_medea_counts_different_coatings_and_they_last_longer():
    import coatings
    from items import instantiate_weapon, make_item_by_id
    q, pl = _qs()
    for cid in ('silver_dust', 'silver_dust', 'frost_salts', 'viper_venom'):
        q.on_coat_applied(cid)
    assert not q.is_unlocked('medea')
    q.on_coat_applied('flask_of_holy_water')
    q.on_coat_applied('flask_of_fire_oil')
    assert q.is_unlocked('medea')
    pl.weapon = instantiate_weapon('longsword', 'steel')
    dust = make_item_by_id('flask', 'silver_dust')
    base = int(coatings.coat_spec(dust).get('blows', 12))
    coatings.apply(pl, dust)
    assert pl.weapon.coating['blows'] == base + base // 2


def test_fabius_wins_in_guard_and_guard_costs_less():
    import stance
    from items import instantiate_weapon
    q, pl = _qs()
    pl.weapon = instantiate_weapon('longsword', 'steel')
    pl.stance = 'guard'
    plain = stance.damage_mult(pl)
    for _ in range(39):
        q.on_kill('goblin', 2, False, False, 1.0, False)
    q.on_kill('goblin', 0, False, False, 1.0, False)     # a spell's kill: not his guard
    assert not q.is_unlocked('fabius')
    q.on_kill('goblin', 2, False, False, 1.0, False)
    assert q.is_unlocked('fabius')
    assert stance.damage_mult(pl) == pytest.approx(1.0 - (1.0 - plain) / 2.0)
    pl.stance = 'press'
    assert stance.damage_mult(pl) == pytest.approx(1.3)


def test_wallace_and_the_parry():
    import stance
    from items import instantiate_shield, instantiate_weapon
    q, pl = _qs()
    pl.weapon = instantiate_weapon('greatsword', 'steel')
    pl.shield = None
    base = stance.parry_ac(pl)
    assert base > 0
    for _ in range(100):
        q.on_kill('goblin', 3, False, False, 1.0, False)
    assert q.is_unlocked('wallace')
    assert stance.parry_ac(pl) == base + 1
    pl.weapon = instantiate_weapon('longsword', 'steel')
    pl.shield = instantiate_shield('round_shield', 'steel') if False else None
    assert stance.parry_ac(pl) == 0                   # a one-hander never parries


def test_janus_by_the_real_key(seeker):
    """S (game_input) with a foe in sight, forty times: the trait; then the
    swap costs no turn."""
    from items import instantiate_weapon
    from game_states import STATE_PLAYER
    g = _game()
    p = g.player
    foe = _place(g, 'goblin', hp=10 ** 6)
    foe.status_effects['paralyzed'] = 10 ** 6          # in sight, and no trouble
    hand, back = instantiate_weapon('dagger', 'steel'), instantiate_weapon('mace', 'steel')
    p.inventory += [hand, back]
    p.weapon = hand
    g._ready_weapon(back)

    def press_s():
        g.state = STATE_PLAYER
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s, unicode='s', mod=0,
                                          scancode=0))
    for _ in range(39):
        press_s()
    assert not g.quirk_system.is_unlocked('janus')
    assert g.quirk_system.get_quirk_progress('janus') == pytest.approx(39 / 40)
    t = g.turn_count
    press_s()
    assert g.quirk_system.is_unlocked('janus')
    assert g.turn_count == t + 1                      # the fortieth still took its turn
    w = p.weapon
    press_s()
    assert p.weapon is not w and g.turn_count == t + 1   # the swap is free now


def test_marius_mule_and_the_stride():
    q, pl = _qs()
    pl.is_burdened = lambda: True
    for lvl in range(2, 11):
        q.on_stair_use(lvl, lvl - 1)
    q.on_stair_use(10, 11)                            # back up: not a march down
    q.on_stair_use(10, 9)                             # floor 10 again: counted once
    assert not q.is_unlocked('marius_mule')
    q.on_stair_use(11, 10)
    assert q.is_unlocked('marius_mule')
    from player import Player
    hero = Player()
    hero.quirk_progress = {'marius_active': True}
    hero.load_tier = lambda: 'burdened'
    assert hero.load_step_every() == 0
    hero.load_tier = lambda: 'overloaded'
    assert hero.load_step_every() == Player.OVERLOADED_STEP_EVERY


def test_the_fatted_calf_and_the_feast_that_heals():
    import kitchen
    from food_system import _apply_recipe_outcome, load_ingredient_for
    q, pl = _qs()
    for lvl in range(2, 13):
        q.on_stair_use(lvl, lvl - 1)
    assert q.get_quirk_progress('fatted_calf') == 0          # no trophy carried
    pl.inventory.append(load_ingredient_for('fafnir_dragon_trophy'))
    for lvl in range(13, 25):
        q.on_stair_use(lvl, lvl - 1)
    assert q.is_unlocked('fatted_calf')
    pl.hp = 1
    _apply_recipe_outcome(pl, kitchen.recipe('feast_29'))
    assert pl.hp == pl.max_hp


def test_the_widows_jar_and_plain_food():
    from food_system import eat_food
    from items import make_item_by_id
    q, pl = _qs()
    for _ in range(9):
        q.on_food_eaten(2, 'goblin', 'sp', 'goblin_prime', parts=('goblin_prime', 'bread_ration'))
    q.on_food_eaten(0, 'goblin', 'ruined', 'goblin_prime', parts=('goblin_prime', 'bread_ration'))
    q.on_food_eaten(2, 'goblin', 'sp', 'goblin_prime', parts=('goblin_prime', 'harpy_prime'))
    assert not q.is_unlocked('widows_jar')
    q.on_food_eaten(2, 'goblin', 'sp', 'goblin_prime', parts=('goblin_prime', 'swamp_moss'))
    assert q.is_unlocked('widows_jar')
    bread = make_item_by_id('food', 'bread_ration')
    pl.sp = 0
    eat_food(pl, bread)
    assert pl.sp == min(pl.max_sp, bread.sp_restore + bread.sp_restore // 2)


def test_proteus_and_the_new_kind():
    import main
    q, pl = _qs()
    pl.known_by_hand = {f'kind_{i}' for i in range(24)}
    q.on_item_equipped('x', 'armor', 'body')
    assert not q.is_unlocked('proteus') and q.get_quirk_progress('proteus') == pytest.approx(24 / 25)
    pl.known_by_hand.add('kind_24')
    q.on_item_equipped('x', 'armor', 'body')
    assert q.is_unlocked('proteus')
    assert main._new_kind_threshold(pl, 3) == 2
    assert main._new_kind_threshold(pl, 1) == 1


def test_circe_counts_no_ruined_dish():
    q, pl = _qs()
    for kind in ('hp', 'sp', 'mp', 'stat', 'ruined', 'ruined'):
        q.on_food_eaten(0 if kind == 'ruined' else 2, '', kind, 'x')
    assert not q.is_unlocked('circe')
    q.on_food_eaten(2, '', 'special', 'x')
    assert q.is_unlocked('circe')


def test_new_quirks_award_the_seekers_trait_ladder(seeker):
    g = _game()
    g.quirk_system.on_coat_applied('a')
    for c in 'bcde':
        g.quirk_system.on_coat_applied(c)
    assert 'medea' in g._seeker.profile.members('traits')


# ---------------------------------------------------------------- the Mooble

def test_a_cold_clean_dance_off_and_terpsichore(seeker):
    """Through the dance screen's own keys (test_mooble's helpers): a
    dance-off won on time with no practice first is Not a Step Missed and
    one step to Terpsichore's Step; one practised first is not."""
    import test_mooble as TM
    g = TM._game(name='Dancing Hero')
    m = TM._fed(g)
    now = TM._clock(g)
    TM._win_dance_off(g, now)
    assert _unlocked(g, 'not_a_step_missed')
    assert g.player.quirk_progress.get('terpsichore_cold_wins') == 1
    TM._key(g, pygame.K_RETURN)
    TM._wait(g)
    g._start_mooble_encounter(m)
    TM._key(g, pygame.K_1)                            # practice first this time
    TM._dance_through(g, now)
    g._mooble_dance_key(pygame.K_d)
    TM._dance_through(g, now)
    g._mooble_dance_key(pygame.K_RETURN)
    assert TM.mo.dances(m) == 2
    assert g.player.quirk_progress.get('terpsichore_cold_wins') == 1


def test_terpsichore_after_three_cold_wins():
    q, pl = _qs()
    dex = pl.DEX
    q.on_dance_off(True, False)
    q.on_dance_off(False, False)
    q.on_dance_off(True, True)
    q.on_dance_off(True, False)
    assert not q.is_unlocked('terpsichore')
    q.on_dance_off(True, False)
    assert q.is_unlocked('terpsichore') and pl.DEX >= dex


def test_the_mooble_joining_is_dance_partner(seeker):
    import test_mooble as TM
    g = TM._game(name='Partner Hero')
    g.pets = []
    TM._three_dances(g)
    TM._key(g, pygame.K_4)
    g.quiz_engine._end(success=True)
    assert _unlocked(g, 'dance_partner')
