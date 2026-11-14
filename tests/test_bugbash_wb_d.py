"""Bug bash on the winning build, round 2, area D (2026-11-13): round 1's
fixes reviewed, the seams between the areas, and a visual pass.

Each test names the finding it pins (WB-Dnn in the bug bash report) and
failed on the code before its fix. Real data, and a real headless Game where
the seam runs through it. Whether any of it feels right is Brandon's
play-test: Claude cannot drive Pygame.
"""
import json
import os
import random
import sys
from types import SimpleNamespace

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

import items  # noqa: E402
from items import instantiate_weapon, make_item_by_id  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402

pygame.init()

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _mon(kind, x=0, y=0):
    return Monster({**MONS[kind], 'id': kind}, x, y)


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(11)
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1, 1)), player_name='__bugbash_wb_d__', secret_build=None)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    g.player.hp = g.player.max_hp = 500
    return g


# ------------------------------------------------- WB-D01: Kit Sense x coatings

def test_wb_d01_kit_sense_silence_on_a_coating_does_not_tell_an_unknown_blade_is_silver():
    """An unidentified longsword, the werewolf (weak to silver), silver dust
    in the pack: Kit Sense named the dust for an iron blade and fell silent
    for a silver one, so its silence said "your blade is silver"."""
    import kit_sense
    wolf = _mon('werewolf')
    said = {}
    for mat in ('iron', 'silver'):
        p = Player()
        w = instantiate_weapon('longsword', mat)
        p.weapon = w
        assert not kit_sense.knows_weapon(p, w)
        p.inventory = [make_item_by_id('flask', 'silver_dust')]
        got = kit_sense.advise(p, wolf)
        said[mat] = (got[0].kind, got[0].name) if got else None
    assert said['iron'] == said['silver'] == ('coating', 'Silver Dust'), said


def test_wb_d01_the_coating_tool_counts_only_what_he_knows_of_the_blade():
    """The coating's own value is reckoned on the blade as the hero knows it,
    so holy water on an unknown blessed... or silver blade reads as holy
    water on a plain one."""
    import coatings
    import kit_sense
    wolf = _mon('werewolf')
    vals = []
    for mat in ('iron', 'silver'):
        p = Player()
        p.weapon = instantiate_weapon('longsword', mat)
        p.inventory = [make_item_by_id('flask', 'silver_dust')]
        assert [why for _it, why in coatings.kit_sense_tools(p, wolf)] == ['coat']
        vals.append([t.mult for t in kit_sense.tools(p, wolf) if t.kind == 'coating'])
    assert vals[0] == vals[1] and vals[0], vals


def test_wb_d01_a_known_silver_blade_still_needs_no_silver_dust():
    import kit_sense
    wolf = _mon('werewolf')
    p = Player()
    w = instantiate_weapon('longsword', 'silver')
    w.id_level = 5
    p.weapon = w
    p.inventory = [make_item_by_id('flask', 'silver_dust')]
    assert kit_sense.knows_weapon(p, w)
    assert kit_sense.advise(p, wolf) is None


# ------------------------------------------------- WB-D02: the combat strip

def _strip_texts(g, monkeypatch, weapon, target):
    g.player.weapon = weapon
    g.combat_target = target
    g.quiz_engine = SimpleNamespace(chain=2)
    seen = []
    real = type(g)._fit_line

    def spy(self, text, max_w, sizes, family='body'):
        seen.append(text)
        return real(self, text, max_w, sizes, family)

    monkeypatch.setattr(type(g), '_fit_line', spy)
    g.screen = pygame.Surface((1600, 900))
    rect = pygame.Rect(110, 400, 1060, g._combat_hud_height())
    g._draw_combat_hud(rect)
    return seen


def test_wb_d02_the_strike_strip_never_names_an_unknown_blades_metal(game, monkeypatch):
    """An unidentified silver longsword against a goblin: the strip's type
    tag read "Slash / Pierce / Silver"."""
    w = instantiate_weapon('longsword', 'silver')
    assert w.id_level < 5 and 'silver' in w.damage_types
    seen = _strip_texts(game, monkeypatch, w, _mon('goblin'))
    tags = [t for t in seen if 'Slash' in t]
    assert tags, seen
    assert not any('Silver' in t for t in tags), tags


def test_wb_d02_a_known_blade_and_the_smiths_inlay_are_still_named(game, monkeypatch):
    import smithing
    w = instantiate_weapon('longsword', 'silver')
    w.id_level = 5
    seen = _strip_texts(game, monkeypatch, w, _mon('goblin'))
    assert any('Silver' in t and 'Slash' in t for t in seen), seen
    inlaid = instantiate_weapon('mace', 'iron')
    assert smithing.inlay(inlaid, 'silver')
    seen = _strip_texts(game, monkeypatch, inlaid, _mon('goblin'))
    assert any('Silver' in t and 'Blunt' in t for t in seen), seen


def test_wb_d02_a_known_kinds_tag_reads_the_blade_as_the_hero_knows_it(game, monkeypatch):
    """A studied werewolf and an unknown silver longsword: the tag said
    "Weakness: Slash / Pierce", naming a weakness the blade's form is not
    (the werewolf resists both); the hidden silver is no part of it."""
    game.player.studied_monster_ids.add('werewolf')
    w = instantiate_weapon('longsword', 'silver')
    seen = _strip_texts(game, monkeypatch, w, _mon('werewolf'))
    tags = [t for t in seen if 'Slash' in t]
    assert tags and not any(t.startswith('Weakness') for t in tags), tags
    assert any(t.startswith('Resisted') for t in tags), tags


# ------------------------------------------------- WB-D03: reforge x identify

def _reforge(g, w, tid='mace'):
    import smithing
    g.player.weapon = w
    assert tid in smithing.reforge_targets(w, False)
    assert g._render_service('reforge', tid, who='Brannoc')


def test_wb_d03_a_reforged_weapon_he_knew_by_its_kind_stays_known(game):
    """The hero knows iron longswords; Brannoc beats his blessed one into a
    mace. It came back a "Plain Mace" of unknown blessing, though the smith
    said the metal, plus and blessing all stay."""
    from items import is_fully_known, buc_known_to
    from hud_context import item_bare_name
    p = game.player
    w = instantiate_weapon('longsword', 'iron')
    w.buc = 'blessed'
    p.known_item_ids.add(w.id)
    assert is_fully_known(w, p)
    _reforge(game, w)
    assert w.id == 'iron_mace'
    assert is_fully_known(w, p) and buc_known_to(w, p)
    assert item_bare_name(p, w) == 'Blessed Iron Mace'


def test_wb_d03_an_unknown_weapon_stays_unknown_when_reforged(game):
    from items import is_fully_known
    p = game.player
    w = instantiate_weapon('longsword', 'iron')
    assert not is_fully_known(w, p)
    _reforge(game, w)
    assert not is_fully_known(w, p)


# ------------------------------------------------- WB-D04: an inlay's name on reload

def test_wb_d04_an_inlaid_weapon_keeps_its_name_through_a_save(game):
    """Every load recomposes a common weapon's name from its material and
    template, so a "Silvered Iron Longsword" came back an "Iron Longsword"
    (the silver itself stayed)."""
    import save_system
    import smithing
    from main import Game
    p = game.player
    w = instantiate_weapon('longsword', 'iron')
    w.id_level = 5
    assert smithing.inlay(w, 'silver')
    c = instantiate_weapon('mace', 'iron')
    assert smithing.inlay(c, 'cold_iron')
    p.weapon = w
    p.inventory.append(c)
    names = (w.name, w.unidentified_name, c.name, c.unidentified_name)
    assert names[0] == 'Silvered Iron Longsword' and names[2].startswith('Iron-Inlaid ')
    save_system.settle_unfinished_actions(game)
    assert save_system.save_game(game)
    g2 = Game(pygame.display.set_mode((1, 1)), player_name=game.player_name)
    g2.load_state(save_system.load_game(game.player_name))
    w2 = g2.player.weapon
    c2 = next(i for i in g2.player.inventory if getattr(i, 'id', '') == 'iron_mace')
    assert (w2.name, w2.unidentified_name, c2.name, c2.unidentified_name) == names
    assert smithing.inlay_of(w2) == 'silver' and smithing.inlay_of(c2) == 'cold_iron'


# ------------------------------------------------- WB-D05: rust x a named piece's own make

def _named(cat, iid):
    return next(i for i in items.load_items(cat) if i.id == iid)


def test_wb_d05_a_named_piece_that_is_not_metal_never_rusts():
    """A named piece whose material has no file ("legendary", "enchanted
    hide", "rubber") fell back to "it rusts", whatever it was: the rust
    monster flaked the Linothorax of Alexander (linen, metal false) and the
    Mantle of Elijah to red rust, and their cards said "rusts"."""
    import gear
    import status_effects as se
    for cat, iid in (('armor', 'linothorax_of_alexander'), ('armor', 'coat_of_cu_chulainn'),
                     ('armor', 'serpent_scale_mail'), ('armor', 'mantle_of_elijah'),
                     ('armor', 'robe_of_the_magus'), ('armor', 'duck_of_doom')):
        it = _named(cat, iid)
        assert se.material_wear(it) is None
        assert not se._can_rust(it), iid
        assert 'rusts' not in gear.wear_words(it), iid


def test_wb_d05_a_named_iron_piece_still_rusts():
    import status_effects as se
    for cat, iid in (('armor', 'breastplate_of_joan'), ('armor', 'tarnhelm'),
                     ('weapon', 'caliburn'), ('weapon', 'penitents_blade')):
        it = _named(cat, iid)
        assert se._can_rust(it), (iid, it.material, getattr(it, 'metal', None))


def test_wb_d05_the_rust_monster_passes_over_a_linen_legend(game):
    import status_effects as se
    from items import ARMOR_SLOTS
    p = game.player
    p.weapon = None
    p.shield = None
    p.ranged_weapon = None
    p.armor_slots = [None] * len(ARMOR_SLOTS)
    p.armor_slots[ARMOR_SLOTS.index('body')] = _named('armor', 'linothorax_of_alexander')
    assert se.rust_worn_gear(p, _mon('goblin'), rng=random.Random(1)) is None


# ------------------------------------------------- WB-D06: Mass Polymorph x the band

def test_wb_d06_mass_polymorph_passes_over_the_stray_kids_band_too(game):
    """WB-C06 made the band shrug off the polymorph wand and spell; the
    Mass Polymorph spell still turned every band member into "a small
    animal" (a quarter of his health, slow and easy to hit)."""
    import stray_kids as sk
    p = game.player
    m = sk.make_zombie('felix', p.x + 2, p.y, 5)
    game.monsters.append(m)
    hp, speed = m.max_hp, m.speed
    game._in_spell_sight = lambda mon: mon is m
    game._cast_spell_effect({'effect': 'mass_polymorph', 'id': 'mass_polymorph',
                             'name': 'Mass Polymorph', 'power': '', 'tier': 5})
    assert (m.max_hp, m.speed) == (hp, speed)
    # An ordinary creature still becomes a small animal.
    gob = _mon('goblin', p.x, p.y + 2)
    game.monsters.append(gob)
    game._in_spell_sight = lambda mon: mon is gob
    before = gob.max_hp
    game._cast_spell_effect({'effect': 'mass_polymorph', 'id': 'mass_polymorph',
                             'name': 'Mass Polymorph', 'power': '', 'tier': 5})
    assert gob.max_hp < before


# ------------------------------------------------- WB-D07: a special order past its floor

def test_wb_d07_an_order_whose_stall_he_passed_waits_at_the_smiths_next_one(game):
    """An order is collected "at his next stall". A hero who never met that
    stall (a trapdoor past its floor, no room for it to stand) found the
    smith deeper down with nothing for him: the order stayed open for good,
    paid for, and blocked every new order with that smith."""
    from mystery_system import build_trader
    from game_states import STATE_PLAYER
    plan = game._trader_plan()
    here = game.dungeon_level
    plan['floors'] = {here: 'armourer', here + 12: 'armourer', here + 24: 'armourer'}
    plan['orders'] = [{'kind': 'armourer', 'person': 'Brannoc', 'placed': here,
                       'collect': here + 12, 'cat': 'weapon', 'template': 'mace',
                       'material': 'iron', 'name': 'Iron Mace', 'paid': 100, 'piece': 80}]
    game.dungeon_level = here + 24                 # floor here+12 was never walked
    m = build_trader('armourer', game.dungeon_level, random.Random(11))
    m.x, m.y = game.player.x + 1, game.player.y
    game.ground_items.append(m)
    game.state = STATE_PLAYER
    game._open_shop()
    assert not plan['orders']
    assert any(getattr(i, 'id', None) == 'iron_mace' for i in game.player.inventory)


def test_wb_d07_an_order_is_not_handed_over_before_its_floor(game):
    from mystery_system import build_trader
    from game_states import STATE_PLAYER
    plan = game._trader_plan()
    here = game.dungeon_level
    plan['floors'] = {here: 'armourer', here + 12: 'armourer'}
    plan['orders'] = [{'kind': 'armourer', 'person': 'Brannoc', 'placed': here,
                       'collect': here + 12, 'cat': 'weapon', 'template': 'mace',
                       'material': 'iron', 'name': 'Iron Mace', 'paid': 100, 'piece': 80}]
    m = build_trader('armourer', here, random.Random(11))
    m.x, m.y = game.player.x + 1, game.player.y
    game.ground_items.append(m)
    game.state = STATE_PLAYER
    game._open_shop()
    assert plan['orders'] and not any(getattr(i, 'id', None) == 'iron_mace'
                                      for i in game.player.inventory)
