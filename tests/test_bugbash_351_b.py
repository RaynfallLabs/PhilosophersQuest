"""Bug bash 3.5.1, hunter B: the quest pets, the dance-offs, riding, the race
and the soundtrack (all new in 3.5.0, none of it play-tested yet).

Each test pins one bug a player would have met, on a real headless Game
driven through the same keys and frames the game loop uses (the dance's
clock is a fake one, as in tests/test_mooble.py). The rhythm's feel and the
race's pace stay Brandon's play-test.
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import mooble_encounter as mo  # noqa: E402
import test_mooble as TM  # noqa: E402

pygame.init()


# ---------------------------------------------------------------------------
# The Mooble's dance
# ---------------------------------------------------------------------------

def test_a_flopped_dance_of_the_dark_holds_them_for_1_turn_not_1_turns():
    """B-01. The Dance of the Dark's result card said "stand staring for 1
    turns" after a flop (the Flop band holds them 1 turn)."""
    bands = {b['name']: b for b in mo.special_spec()['bands']}
    flop = mo.special_result_line(bands['flop'])
    assert 'for 1 turn,' in flop and '1 turns' not in flop, flop
    assert 'for 3 turns,' in mo.special_result_line(bands['great'])
    # Danced through the menu with real keys (no step hit: a flop), the
    # result card draws that line.
    from pet_system import Pet
    g = TM._game('__test_351b_flop__')
    TM._hall(g)
    pet = Pet('mooble', 11, 10, level=20)
    g.pets = [pet]
    now = TM._clock(g)
    md = TM._special_through_the_menu(g, now, lambda resp: [])
    assert md['band']['name'] == 'flop'
    drawn = []
    real_wrap = g._ui_wrap_text

    def wrap(text, *a, **k):
        drawn.append(str(text))
        return real_wrap(text, *a, **k)
    g._ui_wrap_text = wrap
    g.screen = pygame.Surface((1600, 900))
    g._draw_mooble_dance()
    assert any('for 1 turn,' in t for t in drawn), drawn
    assert not any('1 turns' in t for t in drawn)


def test_the_count_in_starts_after_the_soundtrack_steps_aside(monkeypatch):
    """B-02. Holding the soundtrack waits for the sound effects still playing
    (music._effects_done, up to a second), and the dance's clock started
    before that wait: Enter to practise again during the result's fanfare
    lost the first beats of the count-in ("5, 6") to the wait."""
    import music
    g = TM._game('__test_351b_count_in__')
    TM._fed(g)
    now = TM._clock(g)

    def slow_hold():
        now[0] += 700                     # the result's fanfare still ringing
    monkeypatch.setattr(music, 'hold', slow_hold)
    monkeypatch.setattr(music, 'release', lambda: None)
    TM._key(g, pygame.K_1)
    before = now[0]
    g._mooble_dance_key(pygame.K_SPACE)
    md = g._mdance
    assert now[0] == before + 700
    assert md['t0'] == now[0]             # the clock starts once the music is quiet
    import game_mooble_dance as gmd
    played = []
    monkeypatch.setattr(gmd, '_play', lambda name: played.append(name))
    g._mooble_dance_tick()
    assert played == ['dance_bar']        # the count-in's first beat, "5", sounds


def test_opening_the_practice_card_and_backing_out_is_not_practising():
    """B-03. Choosing Practise and pressing Esc on its card, without dancing
    a step, counted as practising before the dance-off: that dance-off won
    no step toward Terpsichore's Step ("won with no practice round first")
    and the Seeker's dance_off event said practised."""
    g = TM._game('__test_351b_practised__')
    m = TM._fed(g)
    now = TM._clock(g)
    TM._key(g, pygame.K_1)                       # the practice card
    g._mooble_dance_key(pygame.K_ESCAPE)         # not now
    assert not g._mooble.get('practised')
    TM._win_dance_off(g, now)
    assert g.player.quirk_progress.get('terpsichore_cold_wins') == 1
    TM._key(g, pygame.K_RETURN)
    # A practice round really danced still counts.
    TM._wait(g)
    g._start_mooble_encounter(m)
    TM._key(g, pygame.K_1)
    TM._dance_through(g, now)
    assert g._mooble.get('practised') is True
    g._mooble_dance_key(pygame.K_d)
    TM._dance_through(g, now)
    g._mooble_dance_key(pygame.K_RETURN)
    assert mo.dances(m) == 2
    assert g.player.quirk_progress.get('terpsichore_cold_wins') == 1


def test_a_special_one_turn_from_ready_says_1_turn():
    """B-07. Choosing a pet's special with one turn of its cooldown left
    said "Dance of the Dark is on cooldown (1 turns)." (every pet's special,
    the Mooble's dance among them)."""
    from pet_system import Pet
    from game_states import STATE_PET_SPECIALS
    g = TM._game('__test_351b_cooldown__')
    pet = Pet('mooble', g.player.x + 1, g.player.y, level=20)
    g.pets = [pet]
    sp = pet.available_specials()[0]
    pet._special_cooldowns[sp['id']] = 1
    g._pet_open_specials(pet)
    assert g.state == STATE_PET_SPECIALS
    g._pet_specials_input(pygame.K_RETURN)
    said = ' '.join(TM._texts(g, 3))
    assert 'Dance of the Dark is on cooldown (1 turn).' in said, said
    assert g._mdance is None                     # nothing danced
    pet._special_cooldowns[sp['id']] = 7
    g._pet_specials_input(pygame.K_RETURN)
    assert '(7 turns).' in ' '.join(TM._texts(g, 2))


def test_a_grown_bococho_with_no_special_keeps_her_rider_in_the_saddle():
    """B-08. She joins as a Bococho (stage 1) and has no special until she
    is a Champion. In her saddle, S on her card set the rider down "to let
    her run", then said she had no specials (and "Evolve it": she is she)."""
    from pet_system import Pet
    from game_states import STATE_PLAYER
    g = TM._game('__test_351b_no_special__')
    p = g.player
    pet = Pet('bococho', p.x, p.y, level=25)
    assert pet.stage == 1 and pet.available_specials() == []
    g.pets = [pet]
    p.riding, pet.ridden = True, True
    g.state = STATE_PLAYER
    g._pet_open_specials(pet)
    assert p.riding and pet.ridden
    said = ' '.join(TM._texts(g, 3))
    assert 'to let her run' not in said
    assert 'has no specials yet. Evolve her to unlock them.' in said, said
    # A Champion's Charge still sets him down first, as before.
    champ = Pet('bococho', p.x, p.y, level=55)
    g.pets = [champ]
    pet.ridden = False
    champ.ridden = True
    g._pet_open_specials(champ)
    assert not p.riding and not champ.ridden


# ---------------------------------------------------------------------------
# The Bococho's camp
# ---------------------------------------------------------------------------

def test_the_racing_camp_is_never_rolled_onto_a_gate_bosss_floor():
    """B-05. The camp's floor was any of 51-65, so about one run in fifteen
    set Gilt Varro's tether posts, his birds and the betting board down in
    Fafnir's hand-built hoard chamber on floor 60 (the Mooble's floor has
    always left gate boss floors out)."""
    import random
    import bococho_encounter as bc
    from boss_levels import BOSS_LEVELS
    d = bc.data()
    floors = {bc.roll_floor(random.Random(i)) for i in range(3000)}
    want = set(range(int(d['first_floor']), int(d['last_floor']) + 1)) - set(BOSS_LEVELS)
    assert floors == want and 60 not in floors
    assert set(bc.candidate_floors()) == want
    # A new game's roll still leaves the shared random stream alone.
    state = random.getstate()
    st = bc.new_run_state()
    assert random.getstate() == state and st['floor'] in want


def test_the_bococho_is_a_bird_with_feet_not_hooves():
    """B-06. The help page's riding section said "Her hooves are loud": the
    Bococho is a running bird."""
    import json
    with open(os.path.join(ROOT, 'data', 'ui', 'gear_and_load.json'), encoding='utf-8') as f:
        page = json.load(f)
    sec = next(s for s in page['sections'] if 'Bococho' in s['heading'])
    text = ' '.join(sec['paragraphs']).lower()
    assert 'hoof' not in text and 'hooves' not in text
    assert 'things hear you coming' in text
    with open(os.path.join(ROOT, 'data', 'bococho.json'), encoding='utf-8') as f:
        assert 'hoove' not in f.read().lower()


# ---------------------------------------------------------------------------
# The Stray Kids: the test helper that walks the hero to the idol
# ---------------------------------------------------------------------------

def test_the_idol_can_be_touched_when_monsters_crowd_round_it():
    """B-10 (a test, the lead's find). test_stray_kids's save-mid-dance-off
    test failed once in a full parallel run: its floor comes from the
    dungeon's own unseeded generator, and on 3.5.1's fuller floors monsters
    sometimes stood on all four square tiles beside the idol, so the helper
    raised "no tile beside it". It now takes any of the eight tiles round
    it and, failing a free one, lifts an ordinary monster off one (never the
    band or a friend). In the game itself the idol always stands where it
    cuts nothing off, with open floor beside it (decor.place_event_stand);
    a crowd only waits to move."""
    import json
    import stray_kids as sk
    import test_stray_kids as TS
    from boss_levels import STRAY_KIDS_STAGE
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        gob = dict(json.load(f)['goblin'], id='goblin')
    g = TS._game('__test_351b_crowd__')
    x, y = TS._idol_floor(g, 9)
    around = [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
              if (dx or dy) and g.dungeon.is_walkable(x + dx, y + dy)]
    assert around                                   # the idol has open floor beside it
    g.monsters = [m for m in g.monsters if (m.x, m.y) not in set(around)]
    for t in around:
        g.monsters.append(Monster(gob, *t))
    dx, dy = TS._beside(g, (x, y))
    assert (g.player.x + dx, g.player.y + dy) == (x, y)
    assert not any(m.alive and (m.x, m.y) == (g.player.x, g.player.y) for m in g.monsters)
    assert len([m for m in g.monsters if (m.x, m.y) in set(around)]) == len(around) - 1
    g.pets = []
    g._do_move(dx, dy)
    g._do_move(dx, dy)
    assert g.dungeon_level == STRAY_KIDS_STAGE
    assert len(sk.the_band(g.monsters)) == 8


# ---------------------------------------------------------------------------
# The race
# ---------------------------------------------------------------------------

def test_a_one_length_leg_is_said_a_length_not_1_lengths():
    """B-04. Sprint on leg 2, keep the inside on leg 3 (Varro's caltrops)
    and miss the first sum: she runs a single length, and the commentary
    said "she runs 1 lengths"."""
    import race as R
    from game_states import STATE_RACE
    g = TM._game('__test_351b_race_words__')
    st = g._bococho_state()
    r = R.new_race(5, 1)
    st['race'] = r
    R.run_leg(r, 3, 'pace')
    R.run_leg(r, 3, 'sprint')                     # leg 3 runs winded
    g._race_leg_done(0, 'pace', 'inside')         # no sum right, through the caltrops
    assert R.lengths(r['history'][-1]['hero_run']) == 1
    import re
    said = ' '.join(g._race_lines)
    assert not re.search(r'\b1 lengths', said), said
    assert 'she runs a length.' in said, said
    assert 'Brassbeak runs ' in said and ' lengths.' in said.split('Brassbeak runs ')[1]
    assert g.state == STATE_RACE
