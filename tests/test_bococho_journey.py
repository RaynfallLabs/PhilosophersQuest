"""The Bococho, the whole way through, as a player would (RARE_PETS_PLAN 3).

One run on a real headless Game, every step a key through the game's own
handler (the driver of tests/test_bugbash_wb_e.py):

1. the camp stands on its floor (51 to 65), set up by the game;
2. the young Bococho shies; a Sunroot, too soon, a second Sunroot after
   the gap, and she trusts the hero (a save and load on the way);
3. Varro takes the fee and the trip goes to the Underway Run;
4. the race: five legs, each a maths chain answered through the keys,
   Sprint or Pace and the outside lane on the cheat leg; a save and load
   mid-race resumes at the next leg; the birds move round the oval;
5. the win: back at the camp Varro storms off and his birds run free;
6. "I choose you!", the animal quiz, the naming popup;
7. into her saddle (Shift+R): two tiles a step, one turn for the world;
   a monster comes into view and the hero is set down with a line;
8. saved and loaded while mounted.

The race's pace and riding's feel are Brandon's play-test.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

from test_bugbash_wb_e import (  # noqa: E402,F401  (make_game is a fixture)
    make_game, no_errors, open_floor, path_step, place_monster, reload, stand_beside, warp)


def _bump(h, m):
    g = h.g
    stand_beside(g, m)
    h.move(m.x - g.player.x, m.y - g.player.y)


def _sunroots(g, n=3):
    import bococho_encounter as bc
    from items import load_items, copy_at, grant_identified
    tpl = next(i for i in load_items('ingredient') if i.id == bc.data()['food_id'])
    r = copy_at(tpl, g.player.x, g.player.y)
    r.count = n
    grant_identified(g, r)
    g.player.inventory.append(r)
    return r


def _run_leg(h, mode_key, right):
    """From the choose phase: pick the mode, answer ``right`` sums and then
    a wrong one (the chain), and land on the leg's result."""
    g = h.g
    h.key(mode_key)
    assert h.in_quiz(), g.state
    h.quiz(right, 1)
    for _ in range(20):
        if g.state == 'race':
            break
        h.frame(0.2)
    assert g.state == 'race', g.state


def test_the_bococho_from_the_camp_to_the_saddle(make_game):  # noqa: F811
    import bococho_encounter as bc
    import race as R
    from boss_levels import UNDERWAY_RUN
    g, h = make_game(build='titivillus', name='Titivillus')
    st = g._bococho_state()
    floor = st['floor']
    assert 51 <= floor <= 65                       # every run, one floor of 51-65
    h.shift('I')                                   # (the QA build's sturdy hero)
    warp(h, floor)
    g = h.g
    st = g._bococho_state()
    assert st['spawned']
    young = next(m for m in g.monsters if bc.is_young(m))
    varro = next(m for m in g.monsters if bc.is_varro(m))
    birds = [m for m in g.monsters if bc.is_bird(m)]
    assert len(birds) == 2 and young.is_allied and varro.is_allied
    import decor
    fx = decor.fixtures_of(g.dungeon)
    assert sum(1 for f in fx.values() if f == 'race_tether_post') == 3
    assert 'race_betting_board' in fx.values()
    g.monsters = [m for m in g.monsters if bc.role(m)]     # a quiet floor: only the camp
    g.pets = []
    g.player_gold = 5000
    # 2. She shies, and only Sunroot will do.
    _bump(h, young)
    assert g.state == 'bococho' and g._bc_phase == 'story'
    h.key(pygame.K_RETURN)
    h.key('3')
    assert g._bc_text == bc.data()['refused']
    h.key(pygame.K_RETURN)
    h.key('1')
    assert g._bc_text.startswith('You hold out your')          # bread, not a Sunroot
    assert 'Sunroot' in g._bc_text
    h.key(pygame.K_RETURN)
    _sunroots(g)
    h.key('1')
    assert g._bc_text == bc.data()['fed'][0] and bc.feeds(st) == 1
    h.key(pygame.K_RETURN)
    h.key('1')
    assert g._bc_text == bc.data()['too_soon'][0]              # still crunching
    assert bc.feeds(st) == 1
    h.key(pygame.K_RETURN)
    h.key('2')
    assert g.state == 'player'
    # Varro will not race yet.
    _bump(h, varro)
    assert g._bc_phase == 'story'
    h.key(pygame.K_RETURN)
    h.key('1')
    assert g._bc_text == bc.data()['challenge_untrusted']
    h.key(pygame.K_RETURN)
    h.key('2')
    g = reload(h)                                               # saved and loaded mid-way
    st = g._bococho_state()
    young = next(m for m in g.monsters if bc.is_young(m))
    varro = next(m for m in g.monsters if bc.is_varro(m))
    assert bc.feeds(st) == 1
    _bump(h, young)
    assert g._bc_text == bc.data()['too_soon'][0]              # still too soon after the load
    h.key(pygame.K_RETURN)
    h.wait(26)
    _bump(h, young)
    assert g._bc_phase == 'options'
    h.key('1')
    assert g._bc_text == bc.data()['fed'][1] and bc.trusts(st)
    h.key(pygame.K_RETURN)
    h.key('3')
    assert g._bc_text == bc.data()['refused_tethered']        # Varro's bird first
    h.key(pygame.K_RETURN)
    h.key('2')
    # 3. The challenge: the fee, and the trip.
    gold = g.player_gold
    fee = bc.fee(floor)
    _bump(h, varro)
    h.key('1')
    assert g._bc_text.startswith('Varro takes your')
    assert g.player_gold == gold - fee
    h.key(pygame.K_RETURN)
    assert g.dungeon_level == UNDERWAY_RUN
    assert g.state == 'race' and g._race_phase == 'intro'
    said = ' '.join(h.said())
    assert 'The Underway Run is a great oval' in said
    racer = g._race_runner('hero')
    rival = g._race_runner('rival')
    assert racer is not None and rival is not None
    line = (racer.x, racer.y)
    assert line in g.visible                                     # the cavern is lit
    h.key(pygame.K_RETURN)
    assert g._race_phase == 'choose'
    # 4. The race. Leg 1: pace.
    _run_leg(h, '2', 10)
    r = g._race()
    assert r['leg'] == 1 and r['history'][0]['chain'] == 10
    assert (racer.x, racer.y) != line                            # she has moved round the oval
    said = ' '.join(h.said())
    assert bc.data()['race']['events']['pace'] in said
    h.key(pygame.K_RETURN)
    _run_leg(h, '2', 10)
    h.key(pygame.K_RETURN)
    # Leg 3, the cheat leg: the taunt is the tell; take the outside lane.
    assert R.is_cheat_leg(g._race())
    info = g._race_panel()
    assert any('Hug the inside rail' in t for t in info['lines'])
    h.key('3')
    assert g._race_lane == 'outside'
    g = reload(h)                                                # saved and loaded mid-race
    h.frame()
    assert g.dungeon_level == UNDERWAY_RUN and g.state == 'race'
    assert g._race()['leg'] == 2 and g._race_phase == 'choose'
    h.key('3')                                                   # (the lane is chosen again)
    _run_leg(h, '2', 10)
    leg3 = g._race()['history'][2]
    assert leg3['lane'] == 'outside' and 'outside' in leg3['events']
    h.key(pygame.K_RETURN)
    _run_leg(h, '2', 10)
    h.key(pygame.K_RETURN)
    _run_leg(h, '1', 10)                                          # the home straight: sprint
    assert g._race_phase == 'finish' and g._race()['done']
    assert R.outcome(g._race())['won'], g._race()
    said = ' '.join(h.said())
    assert 'Your Bococho wins' in said
    h.key(pygame.K_RETURN)
    # 5. Back at the camp: Varro storms off, his birds run free.
    assert g.dungeon_level == floor and g.state == 'player'
    st = g._bococho_state()
    assert st['won'] and st['race'] is None
    assert not any(bc.is_varro(m) or bc.is_bird(m) for m in g.monsters)
    said = ' '.join(h.said())
    assert 'storms off' in said
    # 6. "I choose you!"
    young = next(m for m in g.monsters if bc.is_young(m))
    _bump(h, young)
    assert bc.data()['waiting_won'] in g._bococho_waiting_text()
    h.key('3')
    assert h.in_quiz() and 'ANIMAL' in g.quiz_title
    h.quiz(2)
    assert g._bc_text == bc.data()['pass']
    h.key(pygame.K_RETURN)
    assert g.state == 'pet_name_input'
    for _ in range(len('Bococho')):
        h.key(pygame.K_BACKSPACE)
    for ch in 'Goldie':
        h.key(getattr(pygame, f'K_{ch.lower()}'), uni=ch)
    h.key(pygame.K_RETURN)
    assert 'Goldie the Bococho runs for you now, and for nobody else.' in h.said()
    pet = g.pets[-1]
    assert pet.species_key == 'bococho' and pet.stage == 1 and pet.pronouns()[0] == 'she'
    assert g._bococho_state()['outcome'] == 'adopted'
    # Her saddlebags.
    h.wait()
    assert g.player.saddlebag_lb == 20
    # 7. Into the saddle, and off at the first foe.
    open_floor(g, g.player.x, g.player.y, 7)
    for pos in list(decor.fixtures_of(g.dungeon)):             # (the camp's posts: an open field)
        decor.remove(g.dungeon, pos)
    g.monsters = []
    g.dungeon.dark_rooms = set()                                # (a lit field: the foe is seen)
    g.dungeon.traps = {}
    pet.x, pet.y = g.player.x + 1, g.player.y
    h.shift('R')
    assert g.player.riding and pet.ridden
    assert (pet.x, pet.y) == (g.player.x, g.player.y)
    turns = g.turn_count
    x0 = g.player.x
    h.key(pygame.K_LEFT)
    assert g.player.x == x0 - 2 and g.turn_count == turns + 1   # two tiles, one turn
    assert (pet.x, pet.y) == (g.player.x, g.player.y), h.said()
    g = reload(h)                                               # 8. a save while mounted loads mounted
    pet = next(p for p in g.pets if p.species_key == 'bococho')
    assert g.player.riding and pet.ridden
    h.said()
    g.dungeon.dark_rooms = set()
    place_monster(g, 'goblin', -3, 0)
    g._refresh_fov()
    h.wait()
    assert not g.player.riding and not pet.ridden, h.peek()
    said = ' '.join(h.said())
    assert 'you slide down from the saddle' in said
    assert (pet.x, pet.y) != (g.player.x, g.player.y)
    no_errors(h)
