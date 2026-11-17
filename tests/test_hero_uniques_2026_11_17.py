"""Four Secret Builds carry their own legend's piece (Brandon, 2026-11-17:
"yes, ok to give uniques that are lore accurate to special builds").

  * Achilles: the Shield of Achilles (Iliad 18, 20, 22), for the Oak Light
    Shield: points that pierce do half damage.
  * Alexander: the Shield of Ilion (Arrian 1.11, 6.10), for the Bronze Heavy
    Shield: once a floor, Shielded when a blow leaves him at a quarter of his
    health.
  * Boudicca: Boudicca's Spear (Cassius Dio 62.2), for the iron longsword:
    each hit may frighten its target.
  * Joan of Arc: her Standard (her trial, 1431), in the off hand where she had
    nothing: a standard, not a shield (no AC); her pets and allies in sight
    hit harder. Her sword stays her weapon.

Headless Game and data tests. How the four feel in play is a play-test
question (CLAUDE.md).
"""
import json
import os
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import gear  # noqa: E402
import items  # noqa: E402
from welcome_screen import SECRET_BUILDS  # noqa: E402

ACHILLES = 'achilles son of peleus'
ALEXANDER = 'alexander the great'
BOUDICCA = 'boudicca queen of the iceni'
JOAN = 'saint joan of arc maid of orleans'

SHIELD_IDS = ('shield_of_achilles', 'shield_of_ilion', 'joans_standard')
SPEAR = 'boudicca_spear'
ALL_IDS = SHIELD_IDS + (SPEAR,)


def _raw(cat):
    with open(os.path.join(ROOT, 'data', 'items', f'{cat}.json'), encoding='utf-8') as f:
        return json.load(f)


SHIELDS, WEAPONS = _raw('shield'), _raw('weapon')


def _defn(iid):
    return SHIELDS.get(iid) or WEAPONS[iid]


def _game(key=None, name=None, build=None):
    from main import Game
    return Game(pygame.display.set_mode((1, 1)), player_name=name or key or '__test_hero_uniques__',
                secret_build=build if build is not None else (SECRET_BUILDS[key] if key else None))


def _mon(kind, hp=10 ** 6):
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        m = Monster({**json.load(f)[kind], 'id': kind}, 0, 0)
    m.hp = m.max_hp = hp
    return m


# ------------------------------------------------------------ each build's kit

@pytest.mark.parametrize('key, slot, iid', [
    (ACHILLES, 'shield', 'shield_of_achilles'),
    (ALEXANDER, 'shield', 'shield_of_ilion'),
    (BOUDICCA, 'weapon', SPEAR),
    (JOAN, 'shield', 'joans_standard'),
])
def test_each_build_starts_with_its_own_piece_in_hand_or_on_the_arm(key, slot, iid):
    field = '_start_shield' if slot == 'shield' else '_start_weapon'
    assert SECRET_BUILDS[key][field] == iid
    p = _game(key).player
    piece = getattr(p, slot)
    assert piece is not None and piece.id == iid, key
    assert not any(getattr(i, 'id', '') == iid for i in p.inventory), key   # worn, not packed
    assert piece.id_level == 5 and iid in p.known_item_ids, key            # his own kit: known
    if slot == 'shield':
        import known_by_hand
        assert known_by_hand.knows(p, piece), key                          # no quiz to put back


def test_the_plain_pieces_they_replace_are_gone():
    a = _game(ACHILLES).player
    assert a.weapon.id == 'achilles_spear'
    assert not any(getattr(i, 'id', '') == 'oak_light_wooden' for i in a.inventory)
    al = _game(ALEXANDER).player
    assert al.weapon.id == 'iron_longsword'                                 # his sword stays
    assert not any(getattr(i, 'id', '') == 'bronze_heavy_wooden' for i in al.inventory)
    b = _game(BOUDICCA).player
    assert b.shield is None and not any(getattr(i, 'id', '') == 'iron_longsword' for i in b.inventory)
    j = _game(JOAN).player
    assert j.weapon.id == 'iron_longsword'                                  # her sword stays her weapon
    assert j.readied_weapon is None
    # A Soul Sphere from the start, so her standard has someone to rally
    # (Brandon, 2026-11-17: "she needs a soul sphere, yes").
    assert any(getattr(i, 'id', '') == 'soul_sphere' for i in j.inventory)


def test_the_starting_ac_per_build():
    """No AC from Dexterity (the defence model): Achilles 9 to 5 (AC 5 for
    AC 1), Alexander 8 to 7 (AC 3 for AC 2), Boudicca and Joan 10 as before
    (a spear and a standard give none)."""
    want = {ACHILLES: 5, ALEXANDER: 7, BOUDICCA: 10, JOAN: 10}
    for key, ac in want.items():
        assert _game(key).player.get_ac() == ac, key


# ------------------------------------------------------------------- the data

@pytest.mark.parametrize('iid', ALL_IDS)
def test_each_piece_is_a_unique_that_is_never_random_loot(iid):
    d = _defn(iid)
    assert d['is_unique'] and d['min_level'] >= 9999 and d['peak_weight'] == 0
    assert not any(v for v in d['floorSpawnWeight'].values())
    assert d['peak_floor'] == 0 and not d['can_be_cursed']
    assert iid in items.scripted_only_ids()                                 # no chest, shop or floor roll
    built = items.make_item_by_id('shield' if iid in SHIELDS else 'weapon', iid)
    assert built is not None and not items.is_random_loot(built)
    assert built.name == d['name']                                          # Title Case, as written


def test_the_shield_of_achilles():
    d = SHIELDS['shield_of_achilles']
    assert d['name'] == 'Shield of Achilles'
    assert (d['tier'], d['ac_bonus'], d['enchant_bonus']) == (3, 2, 3)      # AC 5, tier 3 like his spear
    assert d['damage_resistances'] == {'pierce': 0.5}
    assert d['template_basis'] == 'heavy_wooden'
    for words in ('Hephaestus', 'Thetis', 'Ocean', 'two of bronze, two of tin and one of gold',
                  'Aeneas', 'Hector'):
        assert words in d['lore'], words


def test_the_shield_of_ilion():
    d = SHIELDS['shield_of_ilion']
    assert d['name'] == 'Shield of Ilion'
    assert (d['tier'], d['ac_bonus'], d['enchant_bonus']) == (1, 2, 1)      # AC 3
    assert d['fallen_cover_turns'] == 5 and not d['damage_resistances']
    for words in ('Troy', 'Athena', 'Peucestas', 'Malli', 'Arrian'):
        assert words in d['lore'], words


def test_boudiccas_spear_and_its_fixed_tier():
    """LORE, NOT FLOOR: a mortal queen's war spear, the peer of the Dory of
    Leonidas and the Spear of Romulus, at its own fixed maths tier."""
    d = WEAPONS[SPEAR]
    assert d['name'] == "Boudicca's Spear"
    assert d['tier'] == d['mathTier'] == d['quiz_tier'] == 2
    assert d['base_damage'] == d['baseDamage'] == 30
    assert d['base_damage'] == WEAPONS['leonidas_dory']['base_damage'] == WEAPONS['romulus_spear']['base_damage']
    assert d['twoHanded'] is False and d['reach'] == 2 and d['damage_types'] == ['pierce']
    assert d['effects'] == {'status': 'feared', 'effect_chance': 0.25, 'effect_duration': 4}
    for words in ('Iceni', 'Cassius Dio', 'spear', 'terror', 'Londinium'):
        assert words in d['lore'], words
    for bad in ('Gae', 'Bolg'):                     # named from the source: no invented Celtic name
        assert bad not in d['name']


def test_joans_standard_is_a_standard_not_a_shield():
    d = SHIELDS['joans_standard']
    assert d['name'] == "Joan of Arc's Standard"
    assert d['standard'] is True and d['ac_bonus'] == 0 and d['enchant_bonus'] == 0
    assert 'ench_level' not in d and d['rally_damage_mult'] == 1.5
    for words in ('forty times', 'kill no one', 'Jhesus Maria', 'lilies', 'Orléans'):
        assert words in d['lore'], words
    s = items.make_item_by_id('shield', 'joans_standard')
    assert gear.is_standard(s) and gear.is_shield(s) and not gear.is_core(s)
    assert gear.ac_value(s) == 0


def test_the_armour_ladder_and_threshold_passes_agree_with_the_data():
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))
    import known_by_hand_thresholds_2026_11 as kbh
    import unique_armor_ladder_2026_11 as ua
    assert ua.main(['--check']) == 0 and kbh.main(['--check']) == 0
    import hero_uniques_2026_11_17 as hu
    assert hu.main([]) == 0
    for k, e in {**hu.SHIELDS, **hu.WEAPONS}.items():
        assert _defn(k) == e, k                     # the script is the record of the data


# --------------------------------------------------------------- the powers

def test_the_shield_of_achilles_halves_what_pierces():
    g = _game(ACHILLES)
    p = g.player
    assert gear.worn_factor(p, 'pierce') == 0.5 and gear.worn_factor(p, 'slash') == 1.0
    p.hp = p.max_hp = 1000
    with_it = p.take_damage(100, 'pierce')
    sh, p.shield = p.shield, None
    p.hp = 1000
    without = p.take_damage(100, 'pierce')
    p.shield = sh
    assert with_it * 2 in (without - 1, without, without + 1)


def _hurt_to_a_fifth(p):
    """One fire blow from a third of his health down to about a fifth."""
    p.hp = int(p.max_hp * 0.30)
    return p.take_damage(max(1, int(p.max_hp * 0.12)), 'fire')


def test_the_shield_of_ilion_covers_the_fallen_once_a_floor():
    g = _game(ALEXANDER)
    p = g.player
    said = []
    g.add_message = lambda text, kind='info', *a, **k: said.append(text)
    assert not p.has_effect('shielded')
    p.hp = p.max_hp
    p.take_damage(max(1, int(p.max_hp * 0.10)), 'fire')                    # not yet a quarter
    assert not p.has_effect('shielded')
    _hurt_to_a_fifth(p)
    assert 0 < p.hp <= p.max_hp * 0.25
    assert p.has_effect('shielded') and p.status_effects['shielded'] == 5
    assert said == ['Badly hurt, you crouch under the Shield of Ilion. You are Shielded.']
    p.status_effects.pop('shielded')
    _hurt_to_a_fifth(p)
    assert not p.has_effect('shielded')                                     # once a floor
    assert '_fallen_cover_used' in type(g)._ONCE_A_FLOOR_PLAYER
    g._change_level(g.dungeon_level + 1, True)
    assert p.__dict__.get('_fallen_cover_used') is False
    _hurt_to_a_fifth(p)
    assert p.has_effect('shielded')                                         # a new floor, a new cover


def test_no_other_shield_covers_the_fallen():
    g = _game(ACHILLES)
    p = g.player
    _hurt_to_a_fifth(p)
    assert not p.has_effect('shielded')


def test_boudiccas_spear_frightens_what_has_a_mind_to_frighten():
    import combat
    g = _game(BOUDICCA)
    p = g.player
    spear = p.weapon
    spear.effects = dict(spear.effects, effect_chance=1.0)                 # every hit, to test it

    class _Quiz:
        def start_quiz(self, callback=None, **_kw):
            callback(types.SimpleNamespace(score=3, success=True, struck_early=False))

    def _strike(m):
        got = {}
        combat.player_attack(p, m, _Quiz(), lambda dmg, killed, chain, **kw: got.update(dmg=dmg))
        return got['dmg']

    orc = _mon('orc_warrior')
    assert not orc.resists_control('feared')
    assert _strike(orc) > 0 and orc.has_effect('feared')
    golem = _mon('clay_golem')                       # a thing with no mind is not frightened
    assert golem.resists_control('feared')
    _strike(golem)
    assert not golem.has_effect('feared')


def _pet_game():
    from pet_system import Pet, random_species
    g = _game(JOAN)
    p = g.player
    pet = Pet(random_species(), p.x + 1, p.y)
    g.pets = [pet]
    g.monsters = []
    return g, pet


def test_joans_standard_rallies_the_pets_she_can_see():
    g, pet = _pet_game()
    g.visible = {(pet.x, pet.y)}
    assert g._rally_mult(pet) == 1.5
    g.visible = set()
    assert g._rally_mult(pet) == 1.0                  # out of her sight, no rally
    g.visible = {(pet.x, pet.y)}
    std, g.player.shield = g.player.shield, None
    assert g._rally_mult(pet) == 1.0                  # put down, no rally
    g.player.shield = items.make_item_by_id('shield', 'shield_of_ilion')
    assert g._rally_mult(pet) == 1.0                  # a shield is no standard
    g.player.shield = std
    pet.alive = False
    assert g._rally_mult(pet) == 1.0


def _bite(g, pet, target, dmg=20):
    pet.take_turn = lambda *a, **k: ('attack', target)
    pet.get_attack_damage = lambda acc=0.5: dmg
    before = target.hp
    g._do_pet_turns()
    return before - target.hp


def test_a_rallied_pet_bites_and_strikes_harder():
    g, pet = _pet_game()
    g.visible = {(pet.x, pet.y)}
    rallied = _bite(g, pet, _mon('goblin'))
    std, g.player.shield = g.player.shield, None
    plain = _bite(g, pet, _mon('goblin'))
    assert plain > 0 and rallied == round(plain * 1.5)
    g.player.shield = std
    # A special's blow (_pet_hit) is rallied too.
    m1, m2 = _mon('goblin'), _mon('goblin')
    hit = g._pet_hit(pet, m1, 1.0)
    g.player.shield = None
    base = g._pet_hit(pet, m2, 1.0)
    assert hit == max(1, int(pet.base_damage * 1.5)) and base == max(1, int(pet.base_damage))


def test_the_standard_turns_no_blow_and_takes_no_plus():
    g = _game(JOAN)
    p = g.player
    std = p.shield
    ac = p.get_ac()
    p.shield = None
    assert p.get_ac() == ac                           # no AC
    p.shield = std
    std.buc = 'blessed'
    assert p.get_ac() == ac and p.core_ac() == 0      # no blessing's AC either
    std.buc = 'uncursed'
    import altar
    assert not altar.blessing_helps(std, p)            # an altar does not offer to bless it
    assert altar.blessing_helps(items.make_item_by_id('shield', 'shield_of_ilion'), p)
    assert items.wear_down(std) is False and std.enchant_bonus == 0     # nothing to rust or burn
    for effect in ('enchant_armor', 'enchant_item'):
        g._apply_scroll_effect(types.SimpleNamespace(
            effect=effect, buc='blessed', tier=5, quiz_tier=5, power=None, name='scroll'))
        assert std.enchant_bonus == 0, effect


def test_the_standard_is_no_mirror_for_perseus_shield():
    import family_edges
    p = _game(JOAN).player
    std = p.shield
    seen = {}

    def _mine(_player, _att, key, recognise=True):
        return [({'id': 'perseus_shield'}, {'requires': 'shield'})] if key == 'gaze_immune' else []
    real = family_edges._mine
    family_edges._mine = _mine
    try:
        seen['standard'] = family_edges.gaze_immune(p, None)
        p.shield = items.make_item_by_id('shield', 'shield_of_ilion')
        seen['shield'] = family_edges.gaze_immune(p, None)
    finally:
        family_edges._mine = real
        p.shield = std
    assert seen == {'standard': False, 'shield': True}


# ----------------------------------------------- traders, thieves, the census

@pytest.mark.parametrize('iid', ALL_IDS)
def test_traders_refuse_them_and_thieves_skip_them(iid):
    import theft
    import traders
    from main import Game
    g = _game(name='__test_hero_uniques_trade__')
    piece = items.make_item_by_id('shield' if iid in SHIELDS else 'weapon', iid)
    g.player.inventory.append(piece)                  # in the pack, not worn
    assert traders.is_quest_piece(piece, Game._QUEST_PIECE_IDS)
    assert piece not in theft.stealable(g.player)
    assert items.withheld(piece)                      # no NPC takes it as payment either


@pytest.mark.parametrize('iid', ALL_IDS)
def test_the_tier_census_does_not_count_a_starting_hero_piece(iid):
    from tools.balance import tier_census
    assert tier_census.band(tier_census.found_floor(_defn(iid))) is None


# ---------------------------------------------------------------- the cards

def test_the_cards_say_what_each_does_in_plain_words_before_the_lore():
    g = _game(JOAN)
    std = g.player.shield
    lines = g._item_power_lines(std)
    assert lines == ['No AC: it is a standard, not a shield.',
                     'Your pets and allies hit harder while they are in your sight.']
    lore = [t for t, _c, _f in g._lore_item_mechanic_lines(std, 5)]
    assert lore[0] == 'Standard' and 'No AC: a standard, not a shield' in lore
    assert 'Your pets and allies hit harder while they are in your sight.' in lore
    ilion = items.make_item_by_id('shield', 'shield_of_ilion')
    ilion.id_level = 5
    cover = ('Once a floor, when a blow leaves you at a quarter of your health, '
             'it covers you: you are Shielded.')
    assert g._item_power_lines(ilion) == ['AC +3', cover]
    achilles = items.make_item_by_id('shield', 'shield_of_achilles')
    achilles.id_level = 5
    assert g._item_power_lines(achilles) == ['AC +5', 'Resists: pierce 50%']
    spear = items.make_item_by_id('weapon', SPEAR)
    spear.id_level = 5
    sl = g._item_power_lines(spear)
    assert 'Each hit has a 25% chance to frighten its target.' in sl
    assert 'Fear 25%' in g._kit_weapon_special(spear, 5)
    for t in lines + [cover]:                         # plain: no "(double damage)" asides
        assert '(' not in t and not any(ch.isdigit() for ch in t), t
    for t in lines + sl + [cover]:
        assert ' they ' not in f' {t.lower()} ' or 'pets and allies' in t.lower(), t


def test_every_piece_has_its_painted_art():
    with open(os.path.join(ROOT, 'tools', 'content', 'genart', 'installed_items.json'),
              encoding='utf-8') as f:
        installed = set(json.load(f)['items'])
    for iid in ALL_IDS:
        path = os.path.join(ROOT, 'assets', 'tiles', 'items', iid + '.png')
        assert os.path.isfile(path), iid
        assert pygame.image.load(path).get_size() == (64, 64), iid
        assert iid in installed, iid


# ------------------------------------------------------------------ old saves

@pytest.mark.parametrize('key, old_field, old_value, slot, old_id', [
    (ACHILLES, '_start_shield', ('light_wooden', 'oak'), 'shield', 'oak_light_wooden'),
    (ALEXANDER, '_start_shield', ('heavy_wooden', 'bronze'), 'shield', 'bronze_heavy_wooden'),
    (BOUDICCA, '_start_weapon', ('longsword', 'iron'), 'weapon', 'iron_longsword'),
])
def test_an_old_save_keeps_the_kit_it_started_with_and_loads(key, old_field, old_value, slot, old_id):
    """A run begun before 2026-11-17 kept the plain piece: the build's rules
    are refreshed by name on load, its starting kit never is."""
    from main import Game
    from save_system import delete_save, load_game, save_game
    old_build = dict(SECRET_BUILDS[key], **{old_field: old_value})
    g = _game(name=key, build=old_build)
    assert getattr(g.player, slot).id == old_id
    try:
        assert save_game(g)
        g2 = Game(pygame.display.set_mode((1, 1)), player_name=g.player_name)
        g2.load_state(load_game(g.player_name))
        assert getattr(g2.player, slot).id == old_id                        # kept as it was
        assert g2.secret_build == SECRET_BUILDS[key]                        # today's rules
        assert not any(getattr(i, 'id', '') in ALL_IDS for i in g2.player.inventory)
        g2.player.get_ac()
    finally:
        delete_save(g.player_name)


def test_an_old_joan_with_an_empty_off_hand_loads_and_rallies_nothing():
    from main import Game
    from save_system import delete_save, load_game, save_game
    old_build = {k: v for k, v in SECRET_BUILDS[JOAN].items() if k != '_start_shield'}
    g = _game(name=JOAN, build=old_build)
    assert g.player.shield is None
    try:
        assert save_game(g)
        g2 = Game(pygame.display.set_mode((1, 1)), player_name=g.player_name)
        g2.load_state(load_game(g.player_name))
        assert g2.player.shield is None and g2.player.weapon.id == 'iron_longsword'
        from pet_system import Pet, random_species
        pet = Pet(random_species(), g2.player.x + 1, g2.player.y)
        g2.visible = {(pet.x, pet.y)}
        assert g2._rally_mult(pet) == 1.0
    finally:
        delete_save(g.player_name)


def test_a_shield_pickled_before_the_fields_does_nothing_new():
    import pickle
    g = _game(ALEXANDER)
    sh = pickle.loads(pickle.dumps(g.player.shield))
    for f in ('fallen_cover_turns', 'rally_damage_mult', 'standard'):
        sh.__dict__.pop(f, None)
    g.player.shield = sh
    assert gear.is_core(sh) and not gear.is_standard(sh)
    _hurt_to_a_fifth(g.player)
    assert not g.player.has_effect('shielded')
    assert g._off_hand_power_lines(sh) == []
