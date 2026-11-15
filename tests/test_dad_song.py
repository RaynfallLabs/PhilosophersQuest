"""Dad and his song (3.5.2): "The Greatest Trainer of All Time", Brandon's
song as A Man Before a King, the one Dad and his special attacks come from.

Thrown, the Unusual Soul Sphere brings Dad and his song plays; he stays
exactly as long as it does, then fades. The old rules hold: not on a boss
floor (the sphere is kept), and the family cats and Shep can still answer
instead. One song at a time: with another playing, the sphere is kept.
(songs.py, game_songs.py, game_combat._throw_unusual_sphere, pet_system.)
"""
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
import songs  # noqa: E402

SONG = 'greatest_trainer'
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


@pytest.fixture
def quiet_music(monkeypatch):
    import music
    calls = []
    monkeypatch.setattr(music, 'play_song', lambda path, at=0.0: calls.append(('play', path)))
    monkeypatch.setattr(music, 'end_song', lambda: calls.append(('end',)))
    monkeypatch.setattr(music, 'mute_song', lambda: calls.append(('mute',)))
    monkeypatch.setattr(music, 'is_held', lambda: False)
    monkeypatch.setattr(music, 'song_playing', lambda: False)
    return calls


@pytest.fixture
def no_rare_pet(monkeypatch):
    import pet_system
    monkeypatch.setattr(pet_system, 'roll_rare_sphere_pet', lambda present: None)


def _game(level=None):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(9)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name='__test_dad_song__')
    g.monsters = []
    g.state = STATE_PLAYER
    if level is not None:
        g.dungeon_level = level
    return g


def _sphere(g):
    s = items.make_item_by_id('artifact', 'unusual_soul_sphere')
    s.identified = True
    g.player.add_to_inventory(s)
    return s


def _open_tile(g):
    px, py = g.player.x, g.player.y
    for dx in (-2, -1, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            if g.dungeon.is_walkable(px + dx, py + dy):
                return px + dx, py + dy
    raise AssertionError('no open tile near the hero')


def _dads(g):
    return [p for p in g.pets if getattr(p, 'is_dad', False) and p.alive]


def test_the_song_ships():
    s = songs.song(SONG)
    assert s['title'] == 'The Greatest Trainer of All Time'
    assert s['artist'] == 'A Man Before a King' and s['companion'] == 'dad'
    assert songs.song_for_companion('dad') == SONG
    assert os.path.exists(songs.track_path(SONG))
    assert s['seconds'] >= 212                     # the whole song (212.6 s)


def test_dad_comes_with_his_song_and_stays_till_it_ends(quiet_music, no_rare_pet):
    g = _game()
    sphere = _sphere(g)
    g._throw_unusual_sphere(sphere, None, *_open_tile(g))
    assert sphere not in g.player.inventory
    dad = _dads(g)
    assert len(dad) == 1 and dad[0].song_id == SONG
    st = songs.active(g.player)
    assert st and st['id'] == SONG
    assert any('Dad is here! Everything will be fine now!' in str(e[0])
               for e in g.msg_log.entries[-3:])
    g._song_frame(0.0)
    assert quiet_music[0][0] == 'play' and quiet_music[0][1].endswith('greatest_trainer.ogg')
    # Turns no longer send him home: fifty pet turns and he is still here.
    for _ in range(50):
        assert dad[0].tick_duration() is False
    g._do_pet_turns()
    assert _dads(g)
    # The song ends: he smiles and fades.
    for _ in range(500):
        g._song_frame(0.5)
    assert songs.active(g.player) is None
    assert not _dads(g)
    assert any('fades away' in str(e[0]) for e in g.msg_log.entries[-3:])
    assert ('end',) in quiet_music


def test_not_on_a_boss_floor_and_the_sphere_is_kept(quiet_music, no_rare_pet):
    from boss_levels import BOSS_LEVELS
    g = _game(level=sorted(BOSS_LEVELS)[0])
    sphere = _sphere(g)
    g._throw_unusual_sphere(sphere, None, *_open_tile(g))
    assert sphere in g.player.inventory and not _dads(g)
    assert songs.active(g.player) is None
    assert "This one's yours" in str(g.msg_log.entries[-1][0])


def test_one_song_at_a_time_keeps_the_sphere(quiet_music, no_rare_pet):
    g = _game()
    songs.begin(g.player, 'caviar_and_tater_tots')
    sphere = _sphere(g)
    g._throw_unusual_sphere(sphere, None, *_open_tile(g))
    assert sphere in g.player.inventory and not _dads(g)
    assert 'One song at a time' in str(g.msg_log.entries[-1][0])


def test_a_family_pet_can_still_answer_instead(quiet_music, monkeypatch):
    import pet_system
    g = _game()
    calls = []
    monkeypatch.setattr(pet_system, 'roll_rare_sphere_pet', lambda present: 'shep')
    monkeypatch.setattr(g, '_hatch_sphere_pet', lambda *a, **k: calls.append(a))
    g._throw_unusual_sphere(_sphere(g), None, *_open_tile(g))
    assert calls and not _dads(g) and songs.active(g.player) is None


def test_a_dad_from_an_old_save_keeps_his_turns():
    from pet_system import DadPet
    dad = DadPet(1, 1, duration=2)
    del dad.song_id                                # pickled before 3.5.2
    assert dad.tick_duration() is False
    assert dad.tick_duration() is True and not dad.alive


def test_a_song_no_longer_playing_takes_him_with_it(quiet_music, no_rare_pet):
    """A save whose song has ended (or was cut) never leaves Dad behind."""
    g = _game()
    g._throw_unusual_sphere(_sphere(g), None, *_open_tile(g))
    songs.end(g.player)                            # gone without the frame seeing it
    dad = _dads(g)[0]
    dad.x, dad.y = g.player.x, g.player.y + 1
    g._do_pet_turns()
    assert not _dads(g)


def test_the_qa_key_puts_a_sphere_in_the_pack():
    g = _game()
    g._qa_unusual_sphere()
    assert any(getattr(i, 'id', '') == 'unusual_soul_sphere' for i in g.player.inventory)
