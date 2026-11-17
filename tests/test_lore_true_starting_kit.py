"""Lore-true starting kit (Brandon's rulings, 2026-11-16).

Shields only where the figure's lore has one ("Geralt no, Leonidas yes...
Corwin is a ranger, not a warrior"), and on the arm from the first turn, not
in the pack:

  * kept, now on the arm: Achilles (the shield Hephaestus made, Iliad 18-22)
    and Leonidas (the hoplite's aspis);
  * put on: Alexander (Arrian 1.11 and 6.10: the sacred shield from Athena's
    temple at Troy, held over him among the Malli);
  * taken off: Theseus (sword and sandals, the club of Periphetes, bare
    hands: no shield in his myths), Boudicca (Dio gives her a spear and a
    chariot, no source a shield), Joan of Arc (her banner in her other hand)
    and Titivillus (the demon of the scribes' slips carries a quill).

Merlin's greeting says he "descends with staff in hand", and he started with
none: he now holds his own unique staff, the Staff of Emrys, a mage's staff
whose power is in his casting and his ward, not his blows. Any other hero can
earn it at Merlin's stone (test_merlins_stone.py).

Headless Game and data tests: how the kit feels in play is a play-test
question (CLAUDE.md).
"""
import json
import os
import pickle
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

from welcome_screen import SECRET_BUILDS  # noqa: E402

SHIELD_LORE = {'achilles son of peleus', 'leonidas of sparta', 'alexander the great'}
NO_SHIELD = ('theseus of athens', 'boudicca queen of the iceni',
             'saint joan of arc maid of orleans', 'titivillus', 'geralt of rivia', 'corwin',
             'miyamoto musashi the sword saint', 'merlin ambrosius')
STAFF = 'staff_of_emrys'
MERLIN = 'merlin ambrosius'


def _game(key=None, name=None):
    from main import Game
    return Game(pygame.display.set_mode((1, 1)), player_name=name or key or '__test_kit__',
                secret_build=SECRET_BUILDS[key] if key else None)


def _packed_shields(p):
    return [i for i in p.inventory if type(i).__name__ == 'Shield']


# ---------------------------------------------------------------- shields

def test_only_the_figures_whose_lore_has_a_shield_start_with_one():
    with_shield = {k for k, b in SECRET_BUILDS.items() if b.get('_start_shield')}
    assert with_shield == SHIELD_LORE
    for key in NO_SHIELD:
        assert not SECRET_BUILDS[key].get('_start_shield'), key


@pytest.mark.parametrize('key', sorted(SHIELD_LORE))
def test_a_lore_shield_is_on_the_arm_from_the_first_turn(key):
    g = _game(key)
    p = g.player
    assert p.shield is not None, key
    assert not _packed_shields(p), key                     # on the arm, not in the pack
    assert p.weapon is not None and not p.weapon.two_handed, key
    import known_by_hand
    assert known_by_hand.knows(p, p.shield), key            # his own kit: no quiz to put back
    # It is worth its AC: the same hero without it is easier to hit.
    worn = p.get_ac()
    sh, p.shield = p.shield, None
    assert p.get_ac() > worn, key
    p.shield = sh


def test_the_shields_themselves():
    assert SECRET_BUILDS['leonidas of sparta']['_start_shield'] == 'shield_of_the_spartans'
    assert SECRET_BUILDS['achilles son of peleus']['_start_shield'] == ('light_wooden', 'oak')
    assert SECRET_BUILDS['alexander the great']['_start_shield'] == ('heavy_wooden', 'bronze')
    g = _game('alexander the great')
    assert g.player.shield.id == 'bronze_heavy_wooden' and g.player.weapon.id == 'iron_longsword'


@pytest.mark.parametrize('key', ('theseus of athens', 'boudicca queen of the iceni',
                                 'saint joan of arc maid of orleans'))
def test_a_figure_with_no_shield_in_the_lore_starts_with_none(key):
    g = _game(key)
    assert g.player.shield is None and not _packed_shields(g.player), key


def test_a_shield_that_meets_a_two_hander_waits_in_the_pack():
    """The rule is the hand's, not the build's: a starting shield beside a
    two-handed weapon goes to the pack (none does today)."""
    b = dict(SECRET_BUILDS[MERLIN], _start_shield=('light_wooden', 'oak'))
    from main import Game
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_kit_2h__', secret_build=b)
    assert g.player.weapon.two_handed and g.player.shield is None
    assert len(_packed_shields(g.player)) == 1


# ---------------------------------------------------------------- Merlin's staff

def _staff_defn():
    with open(os.path.join(ROOT, 'data', 'items', 'weapon.json'), encoding='utf-8') as f:
        return json.load(f)[STAFF]


def test_merlin_starts_with_his_staff_in_his_hand():
    assert SECRET_BUILDS[MERLIN]['_start_weapon'] == STAFF
    assert 'staff in hand' in SECRET_BUILDS[MERLIN]['_greeting']
    g = _game(MERLIN)
    p = g.player
    assert p.weapon is not None and p.weapon.id == STAFF and p.weapon.name == 'Staff of Emrys'
    assert not any(getattr(i, 'id', '') == STAFF for i in p.inventory)
    assert getattr(p.weapon, 'id_level', 0) == 5            # his own kit: known
    assert p.has_effect('magic_resist')                      # his ward, in hand


def test_the_staff_is_a_unique_that_is_never_random_loot():
    import items
    d = _staff_defn()
    assert d['is_unique'] and d['min_level'] >= 9999 and d['peak_weight'] == 0
    assert not any(v for v in d['floorSpawnWeight'].values())
    assert STAFF in items.scripted_only_ids()                # no chest, shop or floor roll
    assert not d['can_be_cursed']


def test_the_staff_is_a_mages_staff_by_its_lore_and_its_tier_is_its_own():
    """LORE, NOT FLOOR: a walking staff, not a war staff (its blows are under
    every other hero weapon's and fade with depth); its power is the art."""
    with open(os.path.join(ROOT, 'data', 'items', 'weapon.json'), encoding='utf-8') as f:
        w = json.load(f)
    d = w[STAFF]
    assert d['quiz_tier'] == d['tier'] == d['mathTier'] == 1
    assert d['two_handed' if 'two_handed' in d else 'twoHanded'] is True
    assert d['base_damage'] < min(w[k]['base_damage'] for k in
                                  ('leonidas_dory', 'witcher_silver_blade', 'zireael'))
    assert d['spell_tier_ease'] == 1 and d['on_equip_status'] == 'magic_resist'
    for words in ('Vortigern', 'red dragon', 'Giants\' Dance', 'Stonehenge', 'Nimue'):
        assert words in d['lore'], words


def _cast(g, spell_id):
    """Cast through the real path, the science quiz's tier caught."""
    seen = {}

    def start_quiz(**kw):
        seen.update(kw)
    g.quiz_engine.start_quiz = start_quiz
    from spells import LEARNABLE_SPELLS
    g.player.mp = g.player.max_mp = 99
    g._invoke_spell(spell_id)
    assert LEARNABLE_SPELLS[spell_id].get('needs_target') is not True
    return seen


def test_spells_cast_with_the_staff_in_hand_ask_an_easier_question():
    """Art over strength: Merlin moved the Giants' Dance by art where no army
    could. Heal is a tier-three spell; with the staff in hand its question is
    tier two, and it heals as a tier-three spell still."""
    from spells import LEARNABLE_SPELLS
    assert LEARNABLE_SPELLS['heal_spell']['tier'] == 3
    g = _game(MERLIN)
    assert _cast(g, 'heal_spell')['tier'] == 2
    staff = g.player.weapon
    g.player.weapon = None                                   # put down: the plain question
    g.state = 'player'
    assert _cast(g, 'heal_spell')['tier'] == 3
    g.player.weapon = staff
    assert _cast(g, 'magic_dart_spell' if False else 'heal_spell')['tier'] == 2
    # never below tier one
    g.state = 'player'
    g.player.known_spells['light_spell'] = 1
    if 'light_spell' in LEARNABLE_SPELLS and LEARNABLE_SPELLS['light_spell'].get('tier') == 1 \
            and not LEARNABLE_SPELLS['light_spell'].get('needs_target'):
        assert _cast(g, 'light_spell')['tier'] == 1


def test_the_ward_goes_with_the_staff():
    g = _game(MERLIN)
    p = g.player
    staff = p.weapon
    assert p.has_effect('magic_resist')
    from items import instantiate_weapon
    p._apply_equip(instantiate_weapon('quarterstaff', 'oak'))
    assert not p.has_effect('magic_resist') and staff in p.inventory
    p._apply_equip(staff)
    assert p.has_effect('magic_resist')


def test_the_staff_works_in_any_hand_so_a_path_could_give_it_later():
    """Another hero earns it at Merlin's stone (test_merlins_stone.py), so
    its powers are the staff's, not Merlin's."""
    from items import make_item_by_id
    g = _game(name='__test_kit_any_hand__')
    staff = make_item_by_id('weapon', STAFF)
    assert staff is not None
    g.player.inventory.append(staff)
    g.player._apply_equip(staff)
    assert g.player.has_effect('magic_resist') and g._staff_spell_ease() == 1


def test_thieves_skip_it_and_traders_refuse_it_like_the_other_hero_artifacts():
    import theft
    import traders
    from main import Game
    g = _game(MERLIN)
    staff = g.player.weapon
    g.player.weapon = None
    g.player.inventory.append(staff)
    assert staff not in theft.stealable(g.player)
    assert traders.is_quest_piece(staff, Game._QUEST_PIECE_IDS)
    import items
    zir = next(x for x in items.load_items('weapon') if x.id == 'zireael')
    assert traders.is_quest_piece(zir, Game._QUEST_PIECE_IDS)          # the same rule


def test_the_card_says_what_it_does_in_plain_words():
    g = _game(MERLIN)
    staff = g.player.weapon
    powers = g._item_power_lines(staff)
    assert "Spells you cast with it in hand ask an easier science question." in powers
    assert any(t.startswith('In hand: Magic Resist') for t in powers)
    words = [t for t, _c, _f in g._lore_item_mechanic_lines(staff, 5)]
    assert 'Spells you cast with it in hand ask an easier science question' in words
    assert any(w.startswith('In hand: Magic Resist') for w in words)
    for t in powers + words:                                  # the staff's own lines:
        if 'spells' in t.lower() or t.startswith('In hand'):  # no "(double damage)" asides
            assert '(' not in t and not any(ch.isdigit() for ch in t), t


def test_the_staff_has_its_painted_art():
    p = os.path.join(ROOT, 'assets', 'tiles', 'items', STAFF + '.png')
    assert os.path.isfile(p)
    assert pygame.image.load(p).get_size() == (64, 64)
    with open(os.path.join(ROOT, 'tools', 'content', 'genart', 'installed_items.json'),
              encoding='utf-8') as f:
        assert STAFF in json.load(f)['items']


def test_the_tier_census_does_not_count_a_starting_hero_staff():
    from tools.balance import tier_census
    assert tier_census.band(tier_census.found_floor(_staff_defn())) is None


def test_an_old_merlin_save_loads_and_a_staff_pickled_before_the_field_eases_nothing():
    g = _game(MERLIN)
    back = pickle.loads(pickle.dumps(g.player))
    assert back.weapon.id == STAFF and back.weapon.spell_tier_ease == 1
    # A weapon pickled before spell_tier_ease: no ease, no error.
    w = back.weapon
    w.__dict__.pop('spell_tier_ease', None)
    g.player.weapon = w
    assert g._staff_spell_ease() == 0
    # An old Merlin (no staff at all) loads and casts as before.
    g.player.weapon = None
    assert g._staff_spell_ease() == 0
