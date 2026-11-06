"""Bug bash 3.3.1, B7: a pet effect reaches the pet it is meant for.

Ash Ketchum's "I Choose You!" ("Heal your active pet") healed pets[0], the
first living pet in the list, whatever state it was in: with two pets, a
full-health first pet took the heal and the dying second one got nothing.
It now heals the pet that needs it most.

Behaviour test through the real hero-power menu path on a headless Game.
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()


def _game(build='ash ketchum'):
    from main import Game
    from game_states import STATE_PLAYER
    from welcome_screen import SECRET_BUILDS
    import items
    items.bind_unique_registry(set())
    screen = pygame.display.set_mode((1, 1))
    g = Game(screen, player_name=build, secret_build=SECRET_BUILDS[build])
    g.state = STATE_PLAYER
    g.monsters = []
    return g


def _use_power(g, pid, chain):
    from game_states import STATE_QUIZ
    assert g._activate_hero_special(pid) is True
    assert g.state == STATE_QUIZ
    cb = g.quiz_engine.callback
    g.quiz_engine.callback = None
    cb(type('R', (), {'score': chain, 'success': chain > 0})())


def _pet(x, y):
    from pet_system import Pet, random_species
    p = Pet(random_species(), x, y)
    p._refresh_stats()
    p.hp = p.max_hp
    return p


def test_b7_i_choose_you_heals_the_pet_that_is_hurt_not_the_first_one():
    g = _game()
    whole = _pet(g.player.x + 1, g.player.y)
    hurt = _pet(g.player.x - 1, g.player.y)
    hurt.hp = 1
    g.pets = [whole, hurt]
    pid = g.player.hero_specials[0]['id']
    _use_power(g, pid, 3)
    assert whole.hp == whole.max_hp
    assert hurt.hp > 1, "the wounded pet got nothing; the full-health first pet took the heal"


def test_b7_with_one_pet_it_heals_that_pet():
    g = _game()
    only = _pet(g.player.x + 1, g.player.y)
    only.hp = 1
    g.pets = [only]
    _use_power(g, g.player.hero_specials[0]['id'], 3)
    assert only.hp > 1
