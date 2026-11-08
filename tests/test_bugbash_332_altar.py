"""Bug bash 3.3.2: the altar's offering (Brandon, 2026-11-07).

"When you get an item blessed at an altar, it blesses a random item in
inventory... it selects from all items, so you can get your lockpick blessed
or random food." Then the ruling: an ordinary altar takes an offering (one
price, rising with the floor) for one theology chain that lifts curses
FIRST and then blesses, one thing a link, five at most, by priority; the
same offering buys either ordinary prayer out of turn. Nothing there sets
the prayer cooldown.

Data layer (what a blessing changes), the pure rite (src/altar.py), and the
real Game flow on floor 1's altar.
"""
import copy
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import altar  # noqa: E402
import economy  # noqa: E402
import items  # noqa: E402


def _data(cat):
    with open(os.path.join(ROOT, 'data', 'items', f'{cat}.json'), encoding='utf-8') as f:
        return json.load(f)


def _one(cat, pred=lambda i: True):
    return copy.copy(next(i for i in items.load_items(cat) if pred(i)))


def _known(it):
    it.id_level = 5            # this copy identified: its kind is known
    return it


def _unknown(it):
    it.id_level = 0
    it.buc_known = False
    return it


# ---------------------------------------------------------------- data layer

@pytest.mark.parametrize('cat, helps, ignores', [
    ('potion', altar.POTION_EFFECTS_BLESSING_HELPS, altar.POTION_EFFECTS_BLESSING_IGNORES),
    ('scroll', altar.SCROLL_EFFECTS_BLESSING_HELPS, altar.SCROLL_EFFECTS_BLESSING_IGNORES),
])
def test_every_potion_and_scroll_effect_is_classified(cat, helps, ignores):
    """A new effect must be put on one list or the other: otherwise a kind
    a blessing cannot change would be blessed, or the reverse."""
    assert not (helps & ignores)
    effects = {it['effect'] for it in _data(cat).values()
               if isinstance(it, dict) and it.get('effect')}
    unclassified = effects - helps - ignores
    assert not unclassified, f"{cat} effects on neither list: {sorted(unclassified)}"


def test_the_offering_is_half_a_floor_and_rises_with_it():
    assert economy.altar_offering(1) == 105
    assert economy.altar_offering(16) == 670
    assert economy.altar_offering(46) == 1800
    prices = [economy.altar_offering(f) for f in range(1, 101)]
    assert prices == sorted(prices)


# ---------------------------------------------------------- what to bless

def test_gear_is_always_worth_blessing():
    for cat in ('weapon', 'armor', 'shield', 'accessory'):
        assert altar.blessing_helps(_one(cat)), cat


@pytest.mark.parametrize('cat', ['lockpick', 'food', 'spellbook', 'wand', 'ammo',
                                 'ingredient', 'container', 'treasure'])
def test_things_a_blessing_does_not_change_are_never_blessed(cat):
    assert not altar.blessing_helps(_one(cat)), cat


def test_a_known_potion_is_judged_by_its_kind():
    teleport = _known(_one('potion', lambda p: p.effect == 'teleport'))
    healing = _known(_one('potion', lambda p: p.effect == 'heal'))
    assert not altar.blessing_helps(teleport)
    assert altar.blessing_helps(healing)


def test_an_unknown_potion_or_scroll_is_always_eligible():
    """Leaving one off would tell the hero it is a kind a blessing cannot
    help: an identification for free."""
    assert altar.blessing_helps(_unknown(_one('potion', lambda p: p.effect == 'teleport')))
    assert altar.blessing_helps(_unknown(_one('scroll', lambda s: s.effect == 'mapping')))


# -------------------------------------------------------------- the rite

def _gear(cat, buc='uncursed'):
    it = _one(cat)
    it.buc = buc
    it.buc_known = True
    return it


def test_curses_first_worn_before_pack_then_blessings():
    worn_sword = _gear('weapon')
    worn_cursed_helm = _gear('armor', 'cursed')
    pack_cursed_ring = _gear('accessory', 'cursed')
    potion = _known(_one('potion', lambda p: p.effect == 'heal'))
    lockpick = _one('lockpick')
    acts = altar.rite(5, [worn_sword, worn_cursed_helm],
                      [lockpick, pack_cursed_ring, potion])
    assert acts[:2] == [('lift', worn_cursed_helm), ('lift', pack_cursed_ring)]
    blessed = [it for what, it in acts if what == 'bless']
    # Worn first (the sword, then the helm just cleaned), then the potion.
    assert blessed == [worn_sword, worn_cursed_helm, potion]
    assert lockpick not in [it for _, it in acts]


def test_the_chain_sets_how_many_things_and_five_is_the_most():
    worn = [_gear('weapon'), _gear('shield'), _gear('armor')]
    pack = [_gear('armor') for _ in range(6)]
    for chain in range(0, 8):
        acts = altar.rite(chain, worn, pack)
        assert len(acts) == min(chain, altar.MAX_MENDED)


def test_curses_take_every_link_before_any_blessing():
    cursed = [_gear('armor', 'cursed') for _ in range(4)]
    acts = altar.rite(3, [_gear('weapon')], cursed)
    assert [w for w, _ in acts] == ['lift', 'lift', 'lift']


def test_a_secret_blessing_is_shown_and_costs_no_link():
    secret = _gear('weapon', 'blessed')
    secret.buc_known = False
    secret.id_level = 0
    plain = _gear('shield')
    acts = altar.rite(1, [secret, plain], [])
    assert acts == [('already', secret), ('bless', plain)]
    altar.apply(acts)
    assert secret.buc_known and plain.buc == 'blessed'


def test_a_known_blessing_is_passed_over():
    known = _gear('weapon', 'blessed')
    plain = _gear('shield')
    assert altar.rite(1, [known, plain], []) == [('bless', plain)]


def test_the_duck_of_doom_keeps_its_curse():
    duck = _gear('armor', 'cursed')
    duck.id = 'duck_of_doom'
    assert altar.curse_order([duck], []) == []


# ------------------------------------------------------------ the real game

@pytest.fixture
def game(monkeypatch, tmp_path):
    import quiz_engine
    import save_system
    import bones
    import layout
    from main import Game
    from game_states import STATE_PLAYER
    from dungeon import ALTAR
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path',
                        lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    size = (1600, 900)
    screen = pygame.display.set_mode(size)
    layout.update(*size)
    random.seed(3)
    g = Game(screen, player_name='__test_bugbash_332_altar__')
    g.on_resize(*size)
    g._resize_grace = 0
    g.monsters = []
    g.state = STATE_PLAYER
    d = g.dungeon
    assert g.dungeon_level == 1
    g.player.x, g.player.y = next((x, y) for y in range(d.height)
                                  for x in range(d.width) if d.tiles[y][x] == ALTAR)
    g.player_gold = 1000
    g.player.prayer_cooldown = 60
    return g


def _press(g, key):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0,
                                      unicode=chr(92) if key == pygame.K_BACKSLASH else ''))


def _answer_chain(g, n):
    """Answer the quiz on screen: n right, then a wrong one (or stop at 5)."""
    from quiz_engine import QuizState
    qe = g.quiz_engine
    for i in range(6):
        if qe.state != QuizState.ASKING:
            break
        q = qe.current_question
        right = str(q['answer'])
        wrong = next(c for c in q['choices'] if str(c).strip() != right.strip())
        qe.answer(right if i < n else wrong)
        for _ in range(40):
            if qe.state != QuizState.RESULT:
                break
            if getattr(qe, '_result_hold', False):
                qe._result_hold_until = 0.0
                qe.release_result_hold()
            g.update(0.25)


def test_the_altar_opens_even_while_prayer_waits(game):
    from game_states import STATE_PRAYER_MENU
    _press(game, pygame.K_BACKSLASH)
    assert game.state == STATE_PRAYER_MENU
    ids = [r['id'] for r in game._prayer_choices()]
    assert ids == ['altar_rite', 'mercy', 'guide_my_hand']   # no free rows on cooldown


def test_the_rite_takes_the_offering_and_leaves_the_cooldown(game):
    p = game.player
    sword = _gear('weapon')
    helm = _gear('armor', 'cursed')
    p.weapon = sword
    p.armor_slots[0] = helm
    lockpick = next(i for i in p.inventory if str(i.item_class) == 'lockpick')
    _press(game, pygame.K_BACKSLASH)
    _press(game, pygame.K_1)
    assert game.player_gold == 1000 - economy.altar_offering(1)
    _answer_chain(game, 2)
    assert helm.buc == 'uncursed'                      # the curse first
    assert sword.buc == 'blessed'                      # then what is wielded
    assert lockpick.buc != 'blessed'
    assert p.prayer_cooldown == 60 - 1                 # one turn passed; never reset


def test_a_silent_rite_keeps_the_offering(game):
    _press(game, pygame.K_BACKSLASH)
    _press(game, pygame.K_1)
    _answer_chain(game, 0)
    assert game.player_gold == 1000 - economy.altar_offering(1)


def test_a_paid_prayer_does_not_touch_the_cooldown(game):
    p = game.player
    p.hp = 1
    _press(game, pygame.K_BACKSLASH)
    _press(game, pygame.K_2)                           # Lord, Have Mercy, paid
    _answer_chain(game, 2)
    assert p.hp > 1
    assert p.prayer_cooldown == 60 - 1


def test_the_free_prayer_is_offered_when_ready_and_sets_the_cooldown(game):
    p = game.player
    p.prayer_cooldown = 0
    _press(game, pygame.K_BACKSLASH)
    rows = game._prayer_choices()
    assert [r['offering'] for r in rows] == [True, True, True, False, False]
    _press(game, pygame.K_4)                           # Mercy, no offering
    assert game.player_gold == 1000
    _answer_chain(game, 1)
    assert p.prayer_cooldown >= 50


def test_no_offering_in_reach_takes_nothing(game):
    from game_states import STATE_PRAYER_MENU
    game.player_gold = 10
    for it in list(game.player.inventory):
        if str(getattr(it, 'item_class', '')) == 'treasure':
            game.player.inventory.remove(it)
    _press(game, pygame.K_BACKSLASH)
    assert not any(r['enabled'] for r in game._prayer_choices())
    _press(game, pygame.K_1)
    assert game.state == STATE_PRAYER_MENU and game.player_gold == 10


def test_god_refuses_the_rite_at_karma_minus_five(game):
    game.karma = -5
    _press(game, pygame.K_BACKSLASH)
    rite = game._prayer_choices()[0]
    assert rite['id'] == 'altar_rite' and not rite['enabled']
    _press(game, pygame.K_1)
    assert game.player_gold == 1000


def test_floor_100_and_the_judgment_altar_keep_their_ways(game):
    game.dungeon.judgment_altar_pos = (game.player.x, game.player.y)
    assert not game._ordinary_altar_here()
    game.dungeon.judgment_altar_pos = None
    assert game._ordinary_altar_here()
    game.dungeon_level = 100
    assert not game._ordinary_altar_here()
