"""Swapping without the chore (winning-build plan 3.4, 2026-11-13).

  * Known by Hand (src/known_by_hand.py): the first equip quiz passed for a
    KIND (its id: material + template for commons) lets every copy of it go
    on with no quiz, whatever its plus or blessing; another material is a
    new kind; a unique is one quiz; a chain-equip legend keeps its best
    tier and may be attuned again to climb.
  * Donning time (gear.don_turns, data/gear_rules.json `donning`): light
    body armour 1 turn, medium 3, heavy 5, full plate 6, the rest 1; off in
    half, rounded up. The turns pass through the normal turn advance; a
    hostile coming into view or a blow stops it (busy.py); the piece counts
    only once fully on.
  * The weapon At Your Back: S swaps it in one turn; a cursed blade in the
    hand and a cursed shield before a two-hander refuse.
  * Loadouts (src/loadouts.py): a saved kit skips what is not in the pack
    and refuses what is not known by hand.
  * Old saves: what is worn counts as known.

Real headless Game: the quiz callbacks, the turn advance, the Kit actions
and the save are the game's own. Unit tests cannot say whether any of it
feels right: that is Brandon's play-test (plan section 6).
"""
import os
import pickle
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

import gear  # noqa: E402
import items  # noqa: E402
import known_by_hand as kbh  # noqa: E402
from busy import BusyAction, Step, interrupt_reason  # noqa: E402
from game_states import STATE_PLAYER, STATE_QUIZ, STATE_ASK, STATE_LOADOUTS  # noqa: E402
from quiz_engine import QuizResult  # noqa: E402

pygame.init()


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__swap_chore__', secret_build=None)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    p = g.player
    # A bare hero: nothing worn, nothing known by hand.
    from items import ARMOR_SLOTS
    p.shield = None
    p.armor_slots = [None] * len(ARMOR_SLOTS)
    p.accessory_slots = [None] * 4
    p.amulet_slot = None
    p.belt_slot = None
    p.known_by_hand = set()
    p.by_hand_tiers = {}
    p.hp = p.max_hp = 500
    return g


def _said(g, n=40):
    """The last lines of the message log."""
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _pass_quiz(g, score=5):
    """Answer the open equip quiz: passed."""
    assert g.state == STATE_QUIZ
    cb, g.quiz_engine.callback = g.quiz_engine.callback, None
    g.state = STATE_PLAYER
    cb(QuizResult(success=True, score=score, correct=score, asked=score))


def _carry(g, item):
    g.player.inventory.append(item)
    return item


def _breastplate(material='chain_steel', level=0, buc='uncursed'):
    return items.instantiate_armor('breastplate', material, level=level, buc=buc)


def _body(g):
    from items import ARMOR_SLOTS
    return g.player.armor_slots[ARMOR_SLOTS.index('body')]


def _wear(g, item):
    """Equip through the game's own path, passing a quiz if one is asked."""
    _carry(g, item)
    g._equip_item(item)
    if g.state == STATE_QUIZ:
        _pass_quiz(g)


# ---------------------------------------------------------------- Known by Hand

def test_a_known_kind_goes_on_with_no_quiz(game):
    p = game.player
    first = _breastplate()
    _wear(game, first)
    assert _body(game) is first
    assert kbh.knows(p, first)
    game._unequip_slot('body', first)
    assert _body(game) is None
    # Another copy of the kind: no quiz, it just goes on (after its turns).
    second = _breastplate()
    _carry(game, second)
    game._equip_item(second)
    assert game.state == STATE_PLAYER
    assert _body(game) is second
    assert any(kbh.FIRES_LINE in t for t in _said(game))
    # Said the first time for the kind only (said_once.py, 2026-11-22).
    game._unequip_slot('body', second)
    n = len(game.msg_log.entries)
    game._equip_item(first)
    assert game.state == STATE_PLAYER and _body(game) is first
    assert not any(kbh.FIRES_LINE in str(e[0]) for e in game.msg_log.entries[n:])


def test_a_new_material_is_a_new_kind(game):
    _wear(game, _breastplate('chain_steel'))
    mithril = _carry(game, _breastplate('mithril'))
    assert not kbh.knows(game.player, mithril)
    game._equip_item(mithril)
    assert game.state == STATE_QUIZ                     # its own quiz
    game.quiz_engine.callback = None
    game.state = STATE_PLAYER


def test_the_plus_and_the_blessing_do_not_matter(game):
    p = game.player
    _wear(game, _breastplate(level=0))
    for level, buc in ((5, 'blessed'), (10, 'uncursed'), (2, 'blessed')):
        copy_ = _breastplate(level=level, buc=buc)
        assert kbh.knows(p, copy_), (level, buc)
        assert kbh.mark_for(p, copy_) == kbh.MARK


def test_a_cursed_known_piece_still_will_not_come_off(game):
    _wear(game, _breastplate())
    game._unequip_slot('body', _body(game))
    cursed = _carry(game, _breastplate(buc='cursed'))
    game._equip_item(cursed)
    assert _body(game) is cursed                        # known: no quiz
    game._unequip_slot('body', cursed)
    assert _body(game) is cursed                        # welded on, as ever
    assert cursed.buc_known


def test_a_unique_asks_once(game):
    p = game.player
    helm = items.make_item_by_id('armor', 'helm_of_achilles')
    _carry(game, helm)
    game._equip_item(helm)
    assert game.state == STATE_QUIZ
    _pass_quiz(game)
    from items import ARMOR_SLOTS
    assert p.armor_slots[ARMOR_SLOTS.index('head')] is helm
    game._unequip_slot('head', helm)
    game._equip_item(helm)
    assert game.state == STATE_PLAYER                   # no second quiz
    assert p.armor_slots[ARMOR_SLOTS.index('head')] is helm


def test_rings_are_known_by_kind_and_tier(game):
    """Brandon, 2026-11-16: a deeper level of a known kind asks its own
    quiz (it used to be the kind at every level, so a Ring of Greater
    Protection V asked nothing once any Protection ring was worn). A lower
    or same-tier one goes on freely."""
    import rings
    p = game.player
    r1 = items.make_item_by_id('accessory', 'ring_of_protection')
    rings.relevel(r1, 1)
    _carry(game, r1)
    game._equip_accessory(r1)
    _pass_quiz(game)
    assert r1 in p.accessory_slots
    r2 = items.make_item_by_id('accessory', 'ring_of_protection')
    rings.relevel(r2, 2)                                # Greater I: the same tier
    assert kbh.knows(p, r2)
    r9 = items.make_item_by_id('accessory', 'ring_of_protection')
    rings.relevel(r9, 9)
    assert not kbh.knows(p, r9)                         # tier V asks its own
    _carry(game, r9)
    game._equip_accessory(r9)
    assert game.state == STATE_QUIZ
    _pass_quiz(game)
    assert r9 in p.accessory_slots and kbh.knows(p, r9)
    r5 = items.make_item_by_id('accessory', 'ring_of_protection')
    rings.relevel(r5, 5)                                # lower than V: free
    assert kbh.knows(p, r5)
    other = items.make_item_by_id('accessory', 'ring_of_regeneration')
    assert not kbh.knows(p, other)


def test_a_chain_legend_keeps_its_best_tier(game):
    p = game.player
    aegis = items.make_item_by_id('shield', 'aegis_of_athena')
    _carry(game, aegis)
    game._equip_item(aegis)
    _pass_quiz(game, score=3)
    assert p.shield is aegis and aegis.achieved_tier == 3
    assert kbh.best_tier(p, aegis) == 3
    game._unequip_slot('shield', aegis)
    # Back on: the game asks; N wears it at tier 3 with no quiz.
    game._equip_item(aegis)
    assert game.state == STATE_ASK
    game._ask_input(pygame.K_n)
    assert game.state == STATE_PLAYER
    assert p.shield is aegis and aegis.achieved_tier == 3
    game._unequip_slot('shield', aegis)
    # Y attunes again: a worse chain keeps the best...
    game._equip_item(aegis)
    game._ask_input(pygame.K_y)
    _pass_quiz(game, score=1)
    assert p.shield is aegis and aegis.achieved_tier == 3
    game._unequip_slot('shield', aegis)
    # ...a better one climbs.
    game._equip_item(aegis)
    game._ask_input(pygame.K_y)
    _pass_quiz(game, score=5)
    assert aegis.achieved_tier == 5 and kbh.best_tier(p, aegis) == 5
    game._unequip_slot('shield', aegis)
    # At tier 5 there is nothing to climb: straight on.
    game._equip_item(aegis)
    assert game.state == STATE_PLAYER and p.shield is aegis and aegis.achieved_tier == 5


def test_the_starting_kit_is_known_by_hand(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    from welcome_screen import SECRET_BUILDS
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    name, build = next((k, b) for k, b in SECRET_BUILDS.items()
                       if b.get('_start_armor') or b.get('_start_shield'))
    g = Game(pygame.display.set_mode((1, 1)), player_name=name, secret_build=build)
    kit = [i for i in g.player.inventory + g.player.worn_items() if kbh.asks_quiz(i)]
    assert kit and all(kbh.knows(g.player, i) for i in kit)


# ----------------------------------------------------------------- donning time

def test_the_donning_table():
    d = gear.rules()['donning']
    assert d['body'] == {'light': 1, 'medium': 3, 'heavy': 5}
    assert d['templates'] == {'full_plate': 6}
    assert d['shield'] == d['minor'] == d['accessory'] == 1
    assert gear.don_turns(items.instantiate_armor('leather', 'leather')) == 1
    assert gear.don_turns(items.instantiate_armor('scale', 'chain_steel')) == 3
    plate = items.instantiate_armor('plate', 'chain_steel')
    assert gear.don_turns(plate) == 5 and gear.doff_turns(plate) == 3
    full = items.instantiate_armor('full_plate', 'chain_steel')
    assert gear.don_turns(full) == 6 and gear.doff_turns(full) == 3
    assert gear.don_turns(items.instantiate_armor('plate_helm', 'chain_steel')) == 1
    assert gear.don_turns(items.instantiate_shield('tower_shield', 'oak')) == 1
    assert gear.don_turns(items.make_item_by_id('accessory', 'ring_of_protection')) == 1
    # Hephaestus: half, rounded up.
    assert gear.don_turns(plate, fast=True) == 3 and gear.doff_turns(plate, fast=True) == 2
    # A named piece goes by its template (the Panoply is full plate).
    assert gear.don_turns(items.make_item_by_id('armor', 'panoply_of_hephaestus')) == 6
    # An old save's common piece (no template_basis) is read from its id.
    full.template_basis = ''
    assert gear.don_turns(full) == 6


def test_plate_takes_five_turns_and_counts_only_once_on(game):
    p = game.player
    plate = items.instantiate_armor('plate', 'chain_steel')
    kbh.learn(p, plate)
    _carry(game, plate)
    ac_bare = p.get_ac()
    seen = []
    real = game._advance_turn

    def _turn():
        seen.append((_body(game) is plate, p.get_ac()))
        real()
    game._advance_turn = _turn
    t0 = game.turn_count
    game._equip_item(plate)
    assert game.turn_count - t0 == 5
    # Four turns with the slot empty, then the plate is on for the fifth.
    assert [on for on, _ac in seen] == [False, False, False, False, True]
    assert all(ac == ac_bare for on, ac in seen if not on)
    assert seen[-1][1] < ac_bare
    assert _body(game) is plate
    # Taking it off is half, rounded up: three turns.
    t0 = game.turn_count
    game._unequip_slot('body', plate)
    assert game.turn_count - t0 == 3 and _body(game) is None


def test_a_swap_is_the_old_piece_off_then_the_new_on(game):
    p = game.player
    old = items.instantiate_armor('plate', 'chain_steel')
    new = items.instantiate_armor('scale', 'chain_steel')
    for it in (old, new):
        kbh.learn(p, it)
    _carry(game, old)
    game._equip_item(old)
    t0 = game.turn_count
    _carry(game, new)
    game._equip_item(new)
    assert game.turn_count - t0 == 3 + 3                # plate off 3, scale on 3
    assert _body(game) is new and old in p.inventory


def test_hephaestus_halves_donning(game):
    p = game.player
    plate = items.instantiate_armor('plate', 'chain_steel')
    kbh.learn(p, plate)
    _carry(game, plate)
    p.unlocked_quirks = set(getattr(p, 'unlocked_quirks', set()) or ()) | {'hephaestus'}
    t0 = game.turn_count
    game._equip_item(plate)
    assert game.turn_count - t0 == 3


def _monster(game, dx=6):
    import json
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        defs = json.load(f)
    m = Monster(dict(defs['goblin'], id='goblin'), game.player.x + dx, game.player.y)
    game.monsters = [m]
    return m


def test_a_foe_coming_into_view_stops_the_dressing(game, monkeypatch):
    p = game.player
    plate = items.instantiate_armor('plate', 'chain_steel')
    kbh.learn(p, plate)
    _carry(game, plate)
    m = _monster(game)
    t0 = game.turn_count
    # The goblin steps into sight after the second turn.
    monkeypatch.setattr(game, '_sees_monster', lambda mon: game.turn_count - t0 >= 2)
    monkeypatch.setattr(game, '_do_monster_turns', lambda: None)
    game._equip_item(plate)
    assert game.state == STATE_ASK
    assert game.turn_count - t0 == 2
    assert _body(game) is None and plate in p.inventory  # not on yet: the slot is empty
    assert any('You stop, half into the' in t and 'comes into view' in t for t in _said(game))
    assert any('Keep dressing? (Y/N)' in t for t in _said(game))
    # Y: the dressing goes on where it stopped.
    game._ask_input(pygame.K_y)
    assert game.turn_count - t0 == 5 and _body(game) is plate
    assert m.alive


def test_stopping_leaves_the_piece_in_the_pack(game, monkeypatch):
    p = game.player
    plate = items.instantiate_armor('plate', 'chain_steel')
    kbh.learn(p, plate)
    _carry(game, plate)
    _monster(game)
    t0 = game.turn_count
    monkeypatch.setattr(game, '_sees_monster', lambda mon: game.turn_count - t0 >= 1)
    monkeypatch.setattr(game, '_do_monster_turns', lambda: None)
    game._equip_item(plate)
    assert game.state == STATE_ASK
    game._ask_input(pygame.K_n)
    assert game.state == STATE_PLAYER
    assert _body(game) is None and plate in p.inventory
    assert game._busy is None


def test_a_blow_stops_the_dressing(game, monkeypatch):
    p = game.player
    plate = items.instantiate_armor('plate', 'chain_steel')
    kbh.learn(p, plate)
    _carry(game, plate)
    m = _monster(game, dx=1)
    t0 = game.turn_count
    monkeypatch.setattr(game, '_sees_monster', lambda mon: True)     # seen from the start

    def _blow():
        if game.turn_count - t0 == 3:
            game._blows_on_hero = game._hero_blows() + 1
            game._last_striker = m
    monkeypatch.setattr(game, '_do_monster_turns', _blow)
    game._equip_item(plate)
    assert game.state == STATE_ASK
    assert any('strikes you' in t for t in _said(game))
    game._ask_input(pygame.K_ESCAPE)                    # Esc stops
    assert _body(game) is None and plate in p.inventory


def test_the_busy_action_bookkeeping():
    act = BusyAction([Step('off', 'old', 3), Step('ready', 'r', 0), Step('on', 'new', 2)])
    assert act.total_turns == 5 and act.turns_left == 5
    assert not act.step_due()
    act.advance()
    act.advance()
    assert act.step_due()                               # the third turn finishes it
    act.finish_step()
    assert act.current.kind == 'ready' and act.step_due()
    act.finish_step()
    assert act.turns_left == 2
    act.seen = {1, 2}
    act.struck = 4
    assert interrupt_reason(act, {1, 2}, 4) == ''
    assert interrupt_reason(act, {1, 2, 3}, 4) == 'seen'
    assert interrupt_reason(act, {1}, 5) == 'struck'


# ------------------------------------------------------------ At Your Back (S)

def _weapon(template='shortsword', material='iron'):
    return items.instantiate_weapon(template, material)


def test_s_swaps_the_weapon_at_your_back_in_one_turn(game):
    p = game.player
    sword = _weapon()
    mace = _weapon('mace', 'iron')
    _carry(game, sword)
    game._equip_item(sword)
    _carry(game, mace)
    game._ready_weapon(mace)
    assert p.readied_weapon is mace
    t0 = game.turn_count
    assert game._swap_weapons()
    assert game.turn_count - t0 == 1
    assert p.weapon is mace and p.readied_weapon is sword and sword in p.inventory
    assert game._swap_weapons()
    assert p.weapon is sword and p.readied_weapon is mace


def test_the_swap_key_is_s(game):
    p = game.player
    sword, mace = _weapon(), _weapon('mace', 'iron')
    _carry(game, sword)
    game._equip_item(sword)
    _carry(game, mace)
    game._ready_weapon(mace)
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s, unicode='s', mod=0))
    assert p.weapon is mace


def test_a_cursed_blade_in_hand_will_not_be_swapped_away(game):
    p = game.player
    sword, mace = _weapon(), _weapon('mace', 'iron')
    sword.buc = 'cursed'
    _carry(game, sword)
    game._equip_item(sword)
    _carry(game, mace)
    game._ready_weapon(mace)
    t0 = game.turn_count
    assert not game._swap_weapons()
    assert p.weapon is sword and p.readied_weapon is mace and game.turn_count == t0


def test_a_two_hander_and_the_shield(game):
    p = game.player
    sword = _weapon()
    great = _weapon('greatsword', 'iron')
    assert great.two_handed
    _carry(game, sword)
    game._equip_item(sword)
    shield = items.instantiate_shield('buckler', 'oak')
    kbh.learn(p, shield)
    _carry(game, shield)
    game._equip_item(shield)
    assert p.shield is shield
    _carry(game, great)
    game._ready_weapon(great)
    # A cursed shield will not come off for it.
    shield.buc = 'cursed'
    assert not game._swap_weapons()
    assert p.weapon is sword and p.shield is shield
    # An ordinary shield goes to the pack, as for any two-handed equip.
    shield.buc = 'uncursed'
    assert game._swap_weapons()
    assert p.weapon is great and p.shield is None and shield in p.inventory


def _sword_and_shield(game):
    """A hero with a shortsword and a buckler on, a greatsword at his back."""
    p = game.player
    sword, great = _weapon(), _weapon('greatsword', 'iron')
    _carry(game, sword)
    game._equip_item(sword)
    shield = items.instantiate_shield('buckler', 'oak')
    kbh.learn(p, shield)
    _carry(game, shield)
    game._equip_item(shield)
    _carry(game, great)
    game._ready_weapon(great)
    assert p.weapon is sword and p.shield is shield and p.readied_weapon is great
    return sword, shield, great


def test_the_shield_goes_back_on_when_the_one_hander_is_drawn(game):
    """Brandon's play-test (2026-11-16): swapping to the two-hander and back
    left the shield in the pack. Now it goes back on the arm, and the whole
    change is one turn ("ready swapping weapon set should only take 1 turn,
    even if you equip a shield as well")."""
    p = game.player
    sword, shield, great = _sword_and_shield(game)
    t0 = game.turn_count
    assert game._swap_weapons()
    assert game.turn_count - t0 == 1
    assert p.weapon is great and p.shield is None and shield in p.inventory
    assert any('goes back on your arm' in t for t in _said(game, 6))
    t0 = game.turn_count
    assert game._swap_weapons()
    assert p.weapon is sword and p.readied_weapon is great
    assert p.shield is shield and shield not in p.inventory
    assert game.turn_count - t0 == 1                 # the swap, shield and all
    assert any('take up your' in t for t in _said(game, 6))
    # Round and round: it keeps working.
    assert game._swap_weapons() and p.shield is None
    assert game._swap_weapons() and p.shield is shield


def test_the_kit_equip_puts_the_shield_back_too(game):
    p = game.player
    sword, shield, great = _sword_and_shield(game)
    game._equip_item(great)                          # from the Kit, not S
    assert p.weapon is great and p.shield is None
    assert any('goes back on your arm' in t for t in _said(game, 6))
    t0 = game.turn_count
    game._equip_item(sword)
    assert p.weapon is sword and p.shield is shield
    assert game.turn_count - t0 == 1


def test_a_shield_dropped_or_replaced_is_not_brought_back(game):
    p = game.player
    sword, shield, great = _sword_and_shield(game)
    assert game._swap_weapons()
    game._do_drop_item(shield)
    assert game._swap_weapons()
    assert p.weapon is sword and p.shield is None
    assert p.__dict__.get('_shield_slung') is None
    # Another shield on while the two-hander is at the back: that one stays.
    other = items.instantiate_shield('buckler', 'oak')
    kbh.learn(p, other)
    _carry(game, other)
    game._equip_item(other)
    assert p.shield is other
    assert game._swap_weapons() and p.shield is None   # the greatsword sets it aside
    assert game._swap_weapons() and p.shield is other


def test_a_shield_from_an_old_save_has_nothing_to_bring_back(game):
    p = game.player
    p.__dict__.pop('_shield_slung', None)            # pickled before 2026-11-16
    assert game._slung_shield() is None


def test_the_readied_weapon_is_carried_and_not_drawn_once_dropped(game):
    import loadouts
    p = game.player
    mace = _carry(game, _weapon('mace', 'iron'))
    w0 = p.get_current_weight()
    game._ready_weapon(mace)
    assert p.get_current_weight() == w0                 # its weight counts, in the pack
    assert game._item_where(mace) == 'back'
    acts = {a['id']: a for a in game._item_actions(mace)}
    assert acts['ready']['label'] == 'Unready' and 'drop' in acts
    game._do_drop_item(mace)
    assert p.readied_weapon is None
    # Remembered while it lies there (round 3, Brandon's Q10): picked up,
    # it is at his back again (tests/test_remembered_sets.py).
    assert loadouts.readied_memory(p) is mace
    # A bow has its own slot: it is never readied.
    bow = next(w for w in items.load_items('weapon') if getattr(w, 'requires_ammo', None))
    _carry(game, bow)
    p.readied_weapon = bow
    assert p.readied_weapon is None


def test_the_kit_shows_the_weapon_at_your_back(game):
    mace = _carry(game, _weapon('mace', 'iron'))
    game._ready_weapon(mace)
    rows = game._kit_collect_items()
    assert ('back', mace) in rows
    assert game._kit_source_label('back') == 'Readied'
    sheet = game._charsheet_loadout_entries()
    assert any(e['slot'] == 'readied' and e['item'] is mace for e in sheet)


# -------------------------------------------------------------------- Loadouts

def test_a_saved_kit_goes_back_on_at_the_sum_of_its_turns(game):
    p = game.player
    plate = items.instantiate_armor('plate', 'chain_steel')
    helm = items.instantiate_armor('plate_helm', 'chain_steel')
    sword = _weapon()
    for it in (plate, helm):
        kbh.learn(p, it)
        _carry(game, it)
        game._equip_item(it)
    _carry(game, sword)
    game._equip_item(sword)
    game._kit_save(0)
    assert game._kits()[0]['name'] == 'Kit One'
    # Into leather, then back into Kit One.
    leather = items.instantiate_armor('leather', 'leather')
    kbh.learn(p, leather)
    _carry(game, leather)
    game._equip_item(leather)
    assert _body(game) is leather
    plan = game._kit_plan(0)
    assert plan['turns'] == 1 + 5                       # leather off 1, plate on 5
    t0 = game.turn_count
    game._kit_wear(0)
    assert game.turn_count - t0 == 6
    assert _body(game) is plate and p.weapon is sword
    assert game._kit_plan(0)['already']


def test_the_loadouts_screen_says_what_each_piece_takes(game):
    """Brandon's play-test (2026-11-16): make it clear how long a change
    takes, piece by piece: each piece that changes shows its turns (the
    piece in its way coming off counted in), the rest show On Now."""
    p = game.player
    plate = items.instantiate_armor('plate', 'chain_steel')
    sword = _weapon()
    kbh.learn(p, plate)
    _carry(game, plate)
    game._equip_item(plate)
    _carry(game, sword)
    game._equip_item(sword)
    game._kit_save(0)
    leather = items.instantiate_armor('leather', 'leather')
    kbh.learn(p, leather)
    _carry(game, leather)
    game._equip_item(leather)
    rows = game._kit_rows(0)
    assert ('Body', game._bare_name(plate), '6 turns') in rows    # leather off 1, plate on 5
    assert ('Weapon', game._bare_name(sword), 'On now') in rows
    plan = game._kit_plan(0)
    assert game._kit_change_text(plan) == '1 piece changes: 6 turns in all.'
    game._kit_confirm(0)
    assert game.state == STATE_ASK
    lines = game._ask_data['lines']
    assert lines[0] == 'Changes: Body 6 turns.'
    assert game._ask_data['options'][0][2] == 'Takes 6 turns in all.'
    # Dropped: the screen says so in the piece's own row.
    game.state = STATE_PLAYER
    game._equip_item(_carry(game, _weapon('mace', 'iron')))     # the sword to the pack
    assert ('Weapon', game._bare_name(sword), '1 turn') in game._kit_rows(0)
    game._do_drop_item(sword)
    assert ('Weapon', game._bare_name(sword), 'Not carried') in game._kit_rows(0)


def test_a_kit_skips_what_is_missing_and_refuses_what_is_unknown(game):
    p = game.player
    plate = items.instantiate_armor('plate', 'chain_steel')
    boots = items.instantiate_armor('plate_boots', 'chain_steel')
    ring = items.make_item_by_id('accessory', 'ring_of_regeneration')
    for it in (plate, boots, ring):
        kbh.learn(p, it)
        _carry(game, it)
        if it is ring:
            game._equip_accessory(it)
        else:
            game._equip_item(it)
    game._kit_save(1)
    from items import ARMOR_SLOTS
    for slot, it in (('body', plate), ('feet', boots)):
        game._unequip_slot(slot, it)
    game._unequip_slot(f'accessory_{p.accessory_slots.index(ring)}', ring)
    # The boots are gone; the ring's kind is forgotten (as if never worn).
    game._do_drop_item(boots)
    p.known_by_hand.discard(ring.id)
    plan = game._kit_plan(1)
    assert boots in plan['missing']
    assert any(it is ring and 'known by hand' in why for it, why in plan['refused'])
    game._kit_wear(1)
    assert _body(game) is plate
    assert p.armor_slots[ARMOR_SLOTS.index('feet')] is None
    assert ring not in p.accessory_slots
    assert any('put it on once first' in t for t in _said(game))


def test_the_loadouts_screen(game):
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e, unicode='E',
                                         mod=pygame.KMOD_SHIFT))
    assert game.state == STATE_LOADOUTS
    game._loadouts_input(pygame.K_2, '2')
    assert game._loadout_sel == 1
    game._loadouts_input(pygame.K_n, 'n')
    for ch in 'quiet':
        game._loadouts_input(getattr(pygame, f'K_{ch}'), ch)
    game._loadouts_input(pygame.K_RETURN, '')
    assert game._kits()[1]['name'] == 'Quiet'
    game._loadouts_input(pygame.K_ESCAPE, '')
    assert game.state == STATE_PLAYER


# ------------------------------------------------------------- save and load

def test_known_by_hand_kits_and_the_back_survive_a_save(game):
    p = game.player
    plate = items.instantiate_armor('plate', 'chain_steel')
    kbh.learn(p, plate)
    _carry(game, plate)
    game._equip_item(plate)
    mace = _carry(game, _weapon('mace', 'iron'))
    game._ready_weapon(mace)
    game._kit_save(2)
    game._kit_rename(2, 'iron')
    p.by_hand_tiers['aegis_of_athena'] = 4
    q = pickle.loads(pickle.dumps(p))
    assert plate.id in q.known_by_hand and q.by_hand_tiers['aegis_of_athena'] == 4
    assert q.readied_weapon is not None and q.readied_weapon.id == mace.id
    assert q.readied_weapon in q.inventory
    kit = q.loadouts[2]
    assert kit['name'] == 'Iron'
    from items import ARMOR_SLOTS
    assert kit['pieces']['body'] is q.armor_slots[ARMOR_SLOTS.index('body')]


def test_an_old_save_counts_what_is_worn_as_known(game):
    p = game.player
    plate = items.instantiate_armor('plate', 'chain_steel')
    _carry(game, plate)
    p._apply_equip(plate)
    p.remove_from_inventory(plate)
    state = p.__getstate__()
    for k in ('known_by_hand', 'by_hand_tiers', 'loadouts', '_readied_weapon'):
        state.pop(k, None)
    from player import Player
    q = Player.__new__(Player)
    q.__setstate__(state)
    assert plate.id in q.known_by_hand
    assert q.readied_weapon is None
    assert [k['name'] for k in q.loadouts] == ['Kit One', 'Kit Two', 'Kit Three']


def test_the_hephaestus_text_names_the_new_reward():
    import quirk_system
    from quirk_text import QUIRK_DESC
    assert 'half the time' in QUIRK_DESC['hephaestus']
    assert 'threshold' not in quirk_system._QUIRK_EFFECTS['hephaestus'].lower()
