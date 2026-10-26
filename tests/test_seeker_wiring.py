"""The Seeker's achievements wired into the game (game_seeker.py): the event
spine, and real game paths reaching the profile.

Every event achievements.json can name must be emitted somewhere in src/ (a
trigger can never wait on an event nothing sends), and a few of the real
paths are driven end to end on a headless Game.
"""
import json
import os
import re
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import achievements  # noqa: E402
import seeker_codes  # noqa: E402
import seeker_profile  # noqa: E402

SRC = Path(__file__).resolve().parent.parent / 'src'


def _emitted() -> set:
    names = set()
    pat = re.compile(r"""(?:_seeker_event|\.emit)\(\s*['"]([a-z_]+)['"]""")
    for f in SRC.glob('*.py'):
        names |= set(pat.findall(f.read_text(encoding='utf-8')))
    return names


def test_every_known_event_is_emitted_somewhere():
    missing = set(achievements.KNOWN_EVENTS) - _emitted()
    assert missing == set()


def test_every_emitted_event_is_known():
    assert _emitted() - set(achievements.KNOWN_EVENTS) == set()


def test_every_event_the_data_uses_is_emitted():
    data = json.loads((SRC.parent / 'data' / 'achievements.json').read_text(encoding='utf-8'))
    used = {c['on'] for c in data['counters'].values()}

    def walk(t):
        for k in ('all', 'any'):
            for p in t.get(k, ()):
                walk(p)
        if 'event' in t:
            used.add(t['event'])
    for a in data['achievements']:
        walk(a['trigger'])
    assert used - _emitted() == set()


# ---------------------------------------------------------------- game paths

@pytest.fixture
def seeker(tmp_path):
    saved = seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE
    seeker_codes._KEYS_OVERRIDE = {'label': 'pq1', 'keys': {'pq1': bytes(range(32))}}
    seeker_profile._DIR_OVERRIDE = str(tmp_path / 'seekers')
    seeker_profile.set_active('Robyn')
    yield 'Robyn'
    seeker_codes._KEYS_OVERRIDE, seeker_profile._DIR_OVERRIDE = saved


def _game(build=None, name='Wiring Hero'):
    from main import Game
    import items
    items.bind_unique_registry(set())
    screen = pygame.display.set_mode((1, 1))
    if isinstance(build, str):
        from welcome_screen import SECRET_BUILDS
        name, build = build, SECRET_BUILDS[build]
    return Game(screen, player_name=name, secret_build=build)


def _monster(kind):
    from monster import Monster
    defs = json.loads((SRC.parent / 'data' / 'monsters.json').read_text(encoding='utf-8'))
    return Monster(dict(defs[kind], id=kind), 1, 1)


def test_a_new_run_counts_and_remembers_the_hero(seeker):
    g = _game()
    p = g._seeker.profile
    assert p.stat('journeys') == 1
    assert seeker_codes.normalise_name('Wiring Hero') in p.members('heroes')


def test_dad_and_qa_builds_record_nothing(seeker):
    assert _game('dad')._seeker is None
    assert _game('titivillus')._seeker is None


def test_nothing_is_recorded_without_a_seeker(tmp_path):
    saved = seeker_profile._DIR_OVERRIDE
    seeker_profile._DIR_OVERRIDE = str(tmp_path / 'none')
    try:
        g = _game()
        assert g._seeker is None
        assert g._seeker_event('duck_hatched') == []
    finally:
        seeker_profile._DIR_OVERRIDE = saved


def test_a_boss_kill_unlocks_and_the_popup_waits_for_calm_play(seeker):
    from game_states import STATE_PLAYER, STATE_QUIZ, STATE_STORY_POPUP
    g = _game()
    g._seeker_pending.clear()
    m = _monster('asterion_minotaur')
    g.monsters.append(m)
    m.alive = False
    g._on_monster_killed(m)
    assert g._seeker.profile.is_unlocked('boss_asterion')
    assert 'boss_asterion' in g._seeker_pending
    g.state = STATE_QUIZ                             # (the boss's own story popup aside)
    g._seeker_tick()
    assert g.state == STATE_QUIZ                     # never over a quiz
    g.state = STATE_PLAYER
    g._seeker_tick()
    assert g.state == STATE_STORY_POPUP
    shown = g.popup_data['achievements']
    assert shown[0]['id'] == 'boss_asterion'
    assert shown[0]['code'] == seeker_codes.make_code('boss_asterion', 'LABYRINTH', 'Robyn')


def test_damage_counts_only_the_heros_blows(seeker):
    g = _game()
    p = g._seeker.profile
    m = _monster('asterion_minotaur')
    before = p.stat('damage_dealt')
    g._damage_by = 'pet'
    m.take_damage(40)
    assert p.stat('damage_dealt') == before
    g._damage_by = 'hero'
    m.take_damage(40)
    assert p.stat('damage_dealt') == before + 40 and p.best('biggest_blow') >= 40


def test_quiz_answers_count(seeker):
    g = _game()
    p = g._seeker.profile
    qe = g.quiz_engine
    qe.subject, qe.tier = 'math', 1
    qe.current_question = {'question': 'x', 'answer': '1'}
    g._on_quiz_answer(True)
    g._on_quiz_answer(False)
    assert p.stat('questions_answered') == 2 and p.stat('right_math') == 1


def test_deeds_reach_the_seeker(seeker):
    import deeds
    g = _game()
    deeds.note(g, 'saved.emberpup', source='test')
    assert g._seeker.profile.is_unlocked('i_choose_you')


def test_pet_growth_reaches_the_seeker(seeker):
    from pet_system import Pet
    g = _game()
    pet = Pet('electric')
    pet.gain_xp(10 ** 7)
    assert g._seeker.profile.is_unlocked('evolving')
    assert g._seeker.profile.is_unlocked('fully_grown')


def test_xyzzy_and_the_run_end(seeker):
    g = _game()
    g._resolve_hack_reality(0)
    assert g._seeker.profile.is_unlocked('segfault')
    g.defeat_reason = 'starved'
    g._seeker_run_end(False)
    p = seeker_profile.load('Robyn')
    assert p.is_unlocked('forgot_to_eat') and p.stat('falls') == 1


def test_a_copied_back_save_of_an_ended_run_is_noticed(seeker):
    from save_system import run_id_of
    g = _game()
    rid = run_id_of(g)
    g.defeat_reason = 'died'
    g._seeker_run_end(False)
    g2 = _game()
    g2._run_id = rid
    g2._seeker_init(new_run=False)
    assert g2._seeker.profile.is_unlocked('not_dead_yet')


def test_an_edited_profile_unlocks_the_hidden_one(seeker):
    g = _game()
    g._seeker.flush()
    path = seeker_profile.profile_path('Robyn')
    doc = json.load(open(path, encoding='utf-8'))
    doc['stats']['kills'] = 10 ** 6
    json.dump(doc, open(path, 'w', encoding='utf-8'))
    g2 = _game()
    assert g2._seeker.profile.is_unlocked('behind_curtain')
    assert g2._seeker.profile.stat('kills') < 10 ** 6


def test_the_run_counters_ride_in_the_save(seeker):
    from save_system import save_game, load_game
    g = _game()
    for _ in range(3):
        g._seeker_event('kill', monster='rat')
    assert save_game(g)
    state = load_game(g.player_name)
    assert achievements.RunTally(state['_seeker_run']).stat('kills_run') == 3


def test_reward_scrolls_and_the_victory_show_the_seekers_own_code(seeker):
    """Brandon's D3: one system for every code. The old fixed codes are gone."""
    data = json.loads((SRC.parent / 'data' / 'items' / 'scroll.json').read_text(encoding='utf-8'))
    ids = {a['id'] for a in json.loads((SRC.parent / 'data' / 'achievements.json')
                                       .read_text(encoding='utf-8'))['achievements']}
    rewards = {k: v for k, v in data.items() if isinstance(v, dict) and v.get('effect') == 'boss_reward'}
    assert len(rewards) == 26
    for k, v in rewards.items():
        assert v.get('achievement') in ids and 'power' not in v, k
    g = _game()
    from items import load_items, make_death_bane_scroll
    scroll = next(s for s in load_items('scroll') if s.id == 'scroll_of_the_gorgon')
    g._seeker_event('kill', monster='medusa_gorgon')
    g.msg_log.clear()
    g._apply_scroll_effect(scroll)
    code = seeker_codes.make_code('boss_medusa', 'GORGON', 'Robyn')
    log = ' '.join(text for text, _kind in g.msg_log.entries)
    assert code in log
    bane = make_death_bane_scroll(0, 0)
    assert bane.achievement == 'lake_of_fire'
    g._seeker_event('run_end', reason='victory', victory=True, floor=1, grade='', build=None,
                    killer=None, cow_level=False)
    g._show_story_popup('exit_with_stone')
    assert g.popup_data['code'] == seeker_codes.make_code('stone_home', 'STONE', 'Robyn')


def test_loading_a_save_is_not_a_new_journey(seeker):
    """_restore_saved_game builds a shell Game before load_state: the shell
    must not count a journey (or every load would add one)."""
    from main import _restore_saved_game
    from save_system import save_game, load_game
    g = _game(name='Loaded Hero')
    assert save_game(g)
    assert g._seeker.profile.stat('journeys') == 1
    g._seeker.flush()
    state = load_game('Loaded Hero')
    g2, notice = _restore_saved_game(pygame.display.set_mode((1, 1)), 'Loaded Hero', state)
    assert g2 is not None and notice is None
    assert seeker_profile.load('Robyn').stat('journeys') == 1
    assert g2._seeker is not None and g2._seeker.profile.stat('journeys') == 1


# ---- regressions from the independent wiring audit (_seeker/WIRING_AUDIT.md)

def test_standing_on_the_shimmer_finds_it(seeker):
    """B1: the Shimmer is fixed terrain, never picked up: finding it is
    standing on it."""
    from items import make_abyssal_shimmer
    g = _game()
    sh = make_abyssal_shimmer(g.player.x, g.player.y)
    g.ground_items.append(sh)
    g._notify_ground(g.player.x, g.player.y)
    assert g._seeker.profile.is_unlocked('shimmer')


def test_powers_count_as_traits(seeker):
    """B2: the 30 powers come through _award_power and count too."""
    g = _game()
    g.quirk_system._award_power('ancestral_q', 'Ancestral', lambda pl: None)
    assert 'ancestral_q' in g._seeker.profile.members('traits')


def test_checkmate_is_the_win_for_the_family(seeker):
    """B3 (and D9, no achievement for being a bad guy)."""
    import deeds
    g = _game()
    deeds.note(g, 'flag.deaths_lost_turn', source='test')
    assert not g._seeker.profile.is_unlocked('checkmate')
    deeds.note(g, 'saved.bartolo_family', source='test')
    assert g._seeker.profile.is_unlocked('checkmate')


def test_a_hellmouth_springing_on_its_own_turn_counts(seeker):
    """R1: the usual reveal (the hero walks up; it springs on its turn)."""
    g = _game()
    g.monsters = [m for m in g.monsters if m.kind == 'nothing']
    hm = _monster('hellmouth')
    hm.x, hm.y = g.player.x + 1, g.player.y
    hm.speed = 999                       # it always gets its turn here
    g.monsters.append(hm)
    for _ in range(5):
        if g._seeker.profile.is_unlocked('not_a_stair'):
            break
        g._do_monster_turns()
        g.player.hp = g.player.max_hp
    assert g._seeker.profile.is_unlocked('not_a_stair')


def test_a_run_ends_once(seeker):
    """R3: a second game-over in the same action is not another fall."""
    g = _game()
    g.defeat_reason = 'died'
    g._seeker_run_end(False)
    g.defeat_reason = 'starved'
    g._seeker_run_end(False)
    p = seeker_profile.load('Robyn')
    assert p.stat('falls') == 1 and not p.is_unlocked('forgot_to_eat')


def test_a_ghost_on_floor_one_is_told(seeker):
    """R5: floor 1 is built before the Seeker opens; its ghost still counts."""
    g = _game(name='Wiring Hero')
    g.dungeon.bones_ghost_name = 'Ghost of Wiring Hero'
    g._bones_ghost_notice(g.dungeon)
    assert g._seeker.profile.is_unlocked('haunted')
    assert g.dungeon.bones_ghost_name is None


def test_a_pet_hatched_past_its_first_form_counts_that_form(seeker):
    """R6: a Master sphere's pet hatches in its final form."""
    g = _game()
    g._hatch_sphere_pet('water', g.player.x, g.player.y, level=55)
    p = g._seeker.profile
    assert p.is_unlocked('fully_grown') and p.stat('grown_water') == 1


def test_a_chain_of_ten_counts_from_any_weapon(seeker):
    """R7: chains have no cap since combat v2; ten in one attack is the bar,
    with a sword, a bow or bare hands alike."""
    g = _game()
    g.player.weapon = None
    m = _monster('asterion_minotaur')
    g._fire_strike_finisher(m, 9, 10, False)
    assert not g._seeker.profile.is_unlocked('chain_10')
    g._fire_strike_finisher(m, 10, 10, False)
    assert g._seeker.profile.is_unlocked('chain_10')


def test_polymath_progress_counts_every_subject(seeker):
    """N7: the bar fills with every subject's share, not maths alone."""
    g = _game()
    s = g._seeker
    s.profile.add('right_math', 100)
    s.profile.add('right_history', 50)
    have, need = s.book.progress('polymath', s.profile)
    assert have == 150 and need > 150
