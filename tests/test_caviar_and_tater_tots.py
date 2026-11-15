"""Caviar and Tater Tots (3.5.2): Brandon's song as A Man Before a King.

Two rare plain foods, good to eat as they are; cooked together they make the
dish that plays the song, and while it plays every blow and spell on the hero
does half damage. Robyn starts with one of each; cooking it earns a secret
achievement. (songs.py, game_songs.py, music.py, kitchen.py.)
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import items  # noqa: E402
import kitchen  # noqa: E402
import songs  # noqa: E402

DISH = 'dish_caviar_and_tater_tots'
SONG = 'caviar_and_tater_tots'


def _load(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return json.load(f)


def _player():
    from player import Player
    p = Player()
    return p


def _food(fid):
    f = items.make_item_by_id('food', fid)
    assert f is not None, fid
    f.count = 1
    return f


_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(build=None):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(5)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name='__test_caviar__', secret_build=build)
    g.monsters = []
    g.state = STATE_PLAYER
    return g


# ---------------------------------------------------------------- the data

def test_two_rare_plain_foods_good_to_eat_as_they_are():
    food = _load('data', 'items', 'food.json')
    for fid in ('caviar', 'tater_tots'):
        f = food[fid]
        assert f['sp_restore'] > 0 and f['eat_line'] and f['lore']
        # Rare in every band: under 2.5% of the band's food finds.
        for band, w in f['floor_spawn_weight'].items():
            total = 0
            lo = int(band.split('-')[0])
            for other in food.values():
                for b2, w2 in (other.get('floor_spawn_weight') or {}).items():
                    a, z = (int(x) for x in b2.split('-'))
                    if a <= lo <= z:
                        total += w2
                        break
            assert 0 < w <= 0.025 * total, (fid, band, w, total)


def test_eating_one_says_its_own_line():
    from food_system import eat_food
    p = _player()
    p.sp = 1
    msgs = eat_food(p, _food('caviar'))
    assert msgs[0].startswith('You eat the Caviar')
    assert 'Unexpected, but so right.' in ' '.join(msgs)


def test_high_and_low_on_different_plates_at_the_trader():
    import economy
    caviar, tots, bread = _food('caviar'), _food('tater_tots'), _food('bread_ration')
    assert economy.item_worth(caviar) > 5 * economy.item_worth(bread)
    assert economy.item_worth(tots) < economy.item_worth(bread)


def test_the_art_and_the_song_ship():
    for rel in (('assets', 'tiles', 'items', 'caviar.png'),
                ('assets', 'tiles', 'items', 'tater_tots.png'),
                ('assets', 'tiles', 'items', 'song_caviar_and_tater_tots.png'),
                ('assets', 'achievements', 'caviar_and_tater_tots.png'),
                ('assets', 'music', 'caviar_and_tater_tots.ogg')):
        assert os.path.exists(os.path.join(ROOT, *rel)), rel
    assert os.path.exists(songs.track_path(SONG))
    spec = open(os.path.join(ROOT, 'PhilosophersQuest.spec'), encoding='utf-8').read()
    assert "'assets/music'" in spec


# ---------------------------------------------------------------- the dish

def test_the_dish_is_on_the_special_tab_once_both_are_held():
    rec = kitchen.recipe(DISH) if hasattr(kitchen, 'recipe') else next(
        r for r in kitchen.book() if r['id'] == DISH)
    assert kitchen.song_of(rec) == SONG and kitchen.dish_tab(rec) == 'special'
    p = _player()
    inv = [_food('caviar')]
    rows = kitchen.menu_rows(p, inv, 'special')
    assert not any(r['id'] == DISH for r in rows)      # a secret until both are held
    inv.append(_food('tater_tots'))
    rows = kitchen.menu_rows(p, inv, 'special')
    row = next(r for r in rows if r['id'] == DISH)
    assert row['ready']
    import cook_menu
    assert cook_menu.main_effect(row) == 'Half Damage'
    assert any('2:44' in line and 'while the song plays' in line for line in row['effects'])


def test_cooked_right_it_starts_the_song():
    rec = next(r for r in kitchen.book() if r['id'] == DISH)
    p = _player()
    msgs = kitchen.apply_dish(p, rec)
    assert msgs[0] == 'You prepare Caviar and Tater Tots.'
    assert any('high and low on different plates' in m for m in msgs)
    st = songs.active(p)
    assert st and st['id'] == SONG and st['left'] == pytest.approx(164)
    assert songs.effect_label(p) == "Everything's Right 2:44"


def test_half_damage_while_the_song_plays_and_not_after():
    p = _player()
    p.hp = p.max_hp = 500
    full = p.take_damage(40, 'physical')
    p.hp = 500
    songs.begin(p, SONG)
    half = p.take_damage(40, 'physical')
    assert half == pytest.approx(full / 2, abs=1)
    p.hp = 500
    fire_full_song = p.take_damage(40, 'fire')
    assert fire_full_song <= full // 2 + 1                 # a spell too
    # Hunger is not a blow.
    p.hp = 500
    assert p.take_damage(10, 'starvation') == 10
    closing = songs.tick(p, 200)
    assert 'Nobody saw this coming' in closing[0]
    assert songs.active(p) is None
    p.hp = 500
    assert p.take_damage(40, 'physical') == full


def test_the_song_runs_on_real_seconds():
    p = _player()
    songs.begin(p, SONG)
    assert songs.tick(p, 60) == []
    assert songs.elapsed(p) == pytest.approx(60)
    assert songs.effect_label(p) == "Everything's Right 1:44"
    assert songs.tick(p, 103.9) == []
    assert songs.tick(p, 0.2)
    assert p.song_playing is None


def test_the_builder_keeps_the_song_dish_and_its_two_foods_to_it():
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'content', 'kitchen'))
    import build_kitchen as B
    assert set(B.SONG_FOOD) == {'caviar', 'tater_tots'}
    row = _load('tools', 'content', 'kitchen', 'structure.json')[DISH]
    assert row['song'] == SONG
    rec = next(r for r in kitchen.book() if r['id'] == DISH)
    assert rec['art'] == 'song_' + SONG
    # No other dish uses them.
    for r in kitchen.book():
        if r['id'] != DISH:
            assert not set(r['ingredients']) & {'caviar', 'tater_tots'}, r['id']


# ---------------------------------------------------------------- the music

class _FakeMusic:
    def __init__(self, monkeypatch):
        import music
        self.calls = []
        self.held = False
        self.on = True
        monkeypatch.setattr(music, 'play_song', lambda path, at=0.0: self.calls.append(('play', round(at))))
        monkeypatch.setattr(music, 'end_song', lambda: self.calls.append(('end',)))
        monkeypatch.setattr(music, 'mute_song', lambda: self.calls.append(('mute',)))
        monkeypatch.setattr(music, 'is_held', lambda: self.held)
        monkeypatch.setattr(music, 'song_playing', lambda: any(c[0] == 'play' for c in self.calls))

        def set_on(v):
            self.on = bool(v)
            self.calls.append(('set_on', self.on))
            return self.on
        monkeypatch.setattr(music, 'set_on', set_on)


def test_the_game_plays_it_pauses_it_with_a_dance_and_brings_the_theme_back(monkeypatch):
    fake = _FakeMusic(monkeypatch)
    g = _game()
    songs.begin(g.player, SONG)
    g._song_frame(0.1)
    assert fake.calls[0] == ('play', 0)
    g._song_frame(0.4)
    left = g.player.song_playing['left']
    fake.held = True                          # a dance's beat: the song and its clock wait
    g._song_frame(0.4)
    assert g.player.song_playing['left'] == left
    fake.held = False
    for _ in range(400):
        g._song_frame(0.5)
    assert songs.active(g.player) is None
    assert ('end',) in fake.calls
    assert any('Nobody saw this coming' in str(e[0]) for e in g.msg_log.entries[-4:])


def test_f5_mutes_the_song_but_not_its_power(monkeypatch):
    fake = _FakeMusic(monkeypatch)
    g = _game()
    songs.begin(g.player, SONG)
    g._song_frame(0.1)
    assert g._song_f5() is False              # muted: music off
    assert ('mute',) in fake.calls and fake.on is False
    left = g.player.song_playing['left']
    g._song_frame(0.5)
    assert g.player.song_playing['left'] < left        # its time still runs
    assert songs.damage_mult(g.player) == 0.5
    assert g._song_f5() is True               # back: it plays on from where it is
    g._song_frame(0.0)
    assert fake.calls[-1][0] == 'play' and fake.calls[-1][1] >= 0
    # With no song playing, F5 is the music's usual switch.
    songs.end(g.player)
    assert g._song_f5() is None


def test_a_save_made_mid_song_plays_on_from_there(monkeypatch):
    import pickle
    fake = _FakeMusic(monkeypatch)
    p = _player()
    songs.begin(p, SONG)
    songs.tick(p, 100)
    p2 = pickle.loads(pickle.dumps(p))
    g = _game()
    g.player = p2
    g._song_frame(0.0)
    assert fake.calls[0] == ('play', 100)


def test_the_music_stream_is_the_songs_while_it_plays(monkeypatch):
    import music
    monkeypatch.setattr(music, '_song', 'x.ogg')
    monkeypatch.setattr(music, '_on', True)
    assert music.start() is False             # the theme waits
    assert music.song_playing()


def test_a_fall_ends_the_song(monkeypatch):
    fake = _FakeMusic(monkeypatch)
    g = _game()
    songs.begin(g.player, SONG)
    g._song_frame(0.1)
    g.player.hp = 0
    g._song_frame(0.1)
    assert songs.active(g.player) is None and ('end',) in fake.calls


# ---------------------------------------------------------------- Robyn, the badge

def test_robyn_starts_with_both():
    from welcome_screen import SECRET_BUILDS
    g = _game(SECRET_BUILDS['robyn'])
    ids = [getattr(i, 'id', '') for i in g.player.inventory]
    assert ids.count('caviar') == 1 and ids.count('tater_tots') == 1


def test_the_secret_achievement_for_cooking_it():
    import achievements
    a = next(x for x in _load('data', 'achievements.json')['achievements']
             if x['id'] == 'caviar_and_tater_tots')
    assert a['category'] == 'secrets'
    assert 'A Man Before a King' in a['hint']
    for w in a['spoiler_words']:
        assert w.lower() not in a['hint'].lower()
    rules = achievements.load_rules() if hasattr(achievements, 'load_rules') else None
    trig = a['trigger']
    assert trig == {'event': 'cooked', 'where': {'recipe': DISH}}
    assert achievements._matches(trig['where'], {'recipe': DISH, 'tab': 'special'})
    assert not achievements._matches(trig['where'], {'recipe': 'dish_starnut_tart'})
    del rules
