"""What a scroll, potion, wand or spellbook does, in plain words
(src/item_words.py, data/ui/item_effects.json).

Brandon's play-test, 2026-11-22: "for scrolls and spells, I can't tell what
they actually do... Effects lists the cost, and lore hints, but nothing is
actually printed there." The Kit card said "Nothing beyond its stats." for
every consumable, the menus a code name ("Effect: Heal  tier 1").

The gates: every kind in the data is worded, every effect id has words, no
code id or 'tier' reaches the player. The pins: the numbers in the words are
the ones the handlers lay (a drink's turns on the hero, a scroll's and a
wand's turns on a monster, a heal's least share, a wand's damage and
charges, a book's spell). The cards: an identified scroll's Kit and menu
cards print the line; an unidentified one still says to identify it.

Headless: how the cards read at the keys is Brandon's play-test.
"""
import json
import os
import random
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import items  # noqa: E402
import item_words  # noqa: E402
from game_states import STATE_PLAYER  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402
from spells import LEARNABLE_SPELLS  # noqa: E402

CLASSES = ('scroll', 'potion', 'wand', 'spellbook')


def _data(cls):
    with open(os.path.join(ROOT, 'data', 'items', f'{cls}.json'), encoding='utf-8') as f:
        return json.load(f)


with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    KINDS = json.load(_f)

ALL_KINDS = [(cls, iid) for cls in CLASSES for iid in sorted(_data(cls))]


def _item(cls, iid, buc='uncursed'):
    it = items.make_item_by_id(cls, iid)
    it.buc = buc
    return it


def _n(text, after):
    """The number after ``after`` in ``text`` ("for 6 turns" -> 6)."""
    m = re.search(re.escape(after) + r'\s*(\d+)', text, re.I)
    assert m, (after, text)
    return int(m.group(1))


# ------------------------------------------------------------------ the gates

@pytest.mark.parametrize('cls,iid', ALL_KINDS)
def test_every_kind_in_the_data_is_worded(cls, iid):
    it = _item(cls, iid)
    lines = item_words.what_it_does(it, Player(), buc_known=False)
    fallback = item_words.data()['fallback']
    assert lines and lines[0].strip() and lines[0] != fallback, (iid, lines)
    short = item_words.short_line(it, Player(), buc_known=False)
    assert short.strip(), iid
    for text in lines + [short]:
        assert '{' not in text and '}' not in text and '?' not in text, (iid, text)


def test_every_effect_id_in_the_data_has_words():
    for cls in ('scroll', 'potion', 'wand'):
        used = {v.get('effect') for v in _data(cls).values() if v.get('effect')}
        missing = used - item_words.effect_ids(cls)
        assert not missing, (cls, sorted(missing))


def test_an_unknown_effect_says_the_fallback():
    it = _item('scroll', 'scroll_of_cure_wounds')
    it.effect = 'no_such_effect'
    assert item_words.what_it_does(it, buc_known=False) == [item_words.data()['fallback']]
    assert item_words.what_it_does(object()) == []          # not one of the four


# (The old labels were the effect id title-cased: "Effect: Heal  tier 1".)
_BANNED = (re.compile(r'\btier\b', re.I), re.compile(r'_'), re.compile(r'Effect:'),
           re.compile(r'\bHeal\b'), re.compile(r'\bExtra Heal\b|\bDrain Con\b|\bStyx Dipped\b'))


@pytest.mark.parametrize('buc', ['uncursed', 'blessed', 'cursed'])
def test_no_code_id_or_tier_reaches_the_player(buc):
    p = Player()
    for cls, iid in ALL_KINDS:
        it = _item(cls, iid, buc)
        for text in item_words.what_it_does(it, p, buc_known=True) + \
                [item_words.short_line(it, p, buc_known=True)]:
            if cls == 'spellbook':
                # A book names its spell ("Teaches Greater Heal: ..."): the
                # spell's own name, not a code id.
                text = text.replace(LEARNABLE_SPELLS.get(it.spell_id, {}).get('name', '~'), '')
            for bad in _BANNED:
                assert not bad.search(text), (iid, buc, text)
            assert not re.search(r'\bthey\b.*\b(is|has|was)\b', text), (iid, text)


def test_the_words_are_data_not_code():
    src = open(os.path.join(ROOT, 'src', 'item_words.py'), encoding='utf-8').read()
    # (The module holds only its fallback; every line is in the JSON.)
    for phrase in ('Heals', 'Confuses', 'Hastes', 'charges left', 'Teaches'):
        assert phrase not in src.split('"""', 2)[-1], phrase


# ------------------------------------------------------- the ladders and shares

def test_the_heal_shares_are_the_handlers():
    import food_system
    from game_magic import SCROLL_HEAL_SHARE, WAND_HEAL_SHARE
    for iid, t in (('scroll_of_cure_wounds', 0), ('scroll_of_full_restoration', 4)):
        line = item_words.what_it_does(_item('scroll', iid), buc_known=False)[0]
        assert f"{round(SCROLL_HEAL_SHARE[t] * 100)}% of your health" in line, line
    line = item_words.what_it_does(_item('wand', 'wand_of_healing'), buc_known=False)[0]
    assert f"{round(WAND_HEAL_SHARE * 100)}%" in line and '7d6' in line
    line = item_words.what_it_does(_item('potion', 'potion_of_extra_healing'), buc_known=False)[0]
    assert f"{round(food_system.POTION_EXTRA_HEAL_SHARE * 100)}%" in line and '4d8+10' in line


def test_a_heal_scroll_names_its_dice_and_the_least_it_heals_this_hero():
    p = Player()
    p.max_hp = 200
    line = item_words.what_it_does(_item('scroll', 'scroll_of_cure_wounds'), p, buc_known=False)[0]
    assert line == "Heals 2d4 health, or 12% of your health (24) if that is more.", line
    blessed = item_words.what_it_does(_item('scroll', 'scroll_of_cure_wounds', 'blessed'), p,
                                      buc_known=True)[0]
    assert 'twice as much' in blessed


def test_a_wands_damage_is_its_handlers_dice_tier_and_intelligence(monkeypatch):
    """game_magic._wand_tier_damage: dice x WAND_TIER_MULT x int_damage_factor."""
    from game_magic import WAND_TIER_MULT, int_damage_factor
    p = Player()
    for iid in ('wand_of_fire_spark', 'wand_of_frost', 'wand_of_devastation'):
        w = _item('wand', iid)
        lo, hi = item_words.dice_range(w.power)
        for intel in (10, 30):
            p.INT = intel
            mult = WAND_TIER_MULT[w.quiz_tier] * int_damage_factor(intel)
            want = f"{max(1, int(lo * mult))} to {max(1, int(hi * mult))} damage"
            line = item_words.what_it_does(w, p, buc_known=False)[0]
            assert want in line and 'Intelligence' not in line, (iid, intel, line)
    # With no hero: Intelligence 10, and the line says it grows with it.
    assert '(more with Intelligence)' in item_words.what_it_does(
        _item('wand', 'wand_of_fire_spark'), buc_known=False)[0]


def test_a_wand_shows_its_charges():
    w = _item('wand', 'wand_of_sleep')
    w.charges, w.max_charges = 3, 4
    lines = item_words.what_it_does(w, buc_known=False)
    assert lines[-1] == "3 of 4 charges left."
    entry = {'_id': 'wand_of_sleep', **_data('wand')['wand_of_sleep']}
    page = item_words.what_it_does(entry, buc_known=False, item_class='wand')
    assert page[-1] == "Found with 3 to 4 charges."


def test_a_spellbook_gives_its_spells_own_words_cost_and_reach():
    p = Player()
    book = _item('spellbook', 'spellbook_fire_spark')
    spell = LEARNABLE_SPELLS[book.spell_id]
    lines = item_words.what_it_does(book, p, buc_known=False)
    assert lines[0] == f"Teaches {spell['name']}: {spell['desc']}"
    assert f"{spell['mp_cost']} MP" in lines[1] and 'Aimed' in lines[1]
    touch = item_words.what_it_does(_item('spellbook', 'spellbook_frost_touch'), p, buc_known=False)
    assert 'you must touch the foe' in touch[1]
    spark = item_words.what_it_does(_item('spellbook', 'spellbook_spark'), p, buc_known=False)
    assert 'reaches 3 tiles' in spark[1]
    p.known_spells = {book.spell_id: spell['mp_cost']}
    assert item_words.what_it_does(book, p, buc_known=False)[-1] == "You know this spell already."
    assert item_words.short_line(book, p) == f"Teaches {spell['name']} ({spell['mp_cost']} MP)"


# ------------------------------------------------- a drink's turns on the hero

def _status_spec(eff):
    return (item_words.data()['potion'].get(eff) or {})


TIMED_POTIONS = sorted(iid for iid, v in _data('potion').items()
                       if _status_spec(v['effect']).get('status')
                       or _status_spec(v['effect']).get('buc') == 'ward')


@pytest.mark.parametrize('iid', TIMED_POTIONS)
@pytest.mark.parametrize('buc', ['uncursed', 'blessed', 'cursed'])
def test_a_drinks_turns_are_the_turns_it_lays(iid, buc, monkeypatch):
    """food_system.drink_potion on a fresh hero, every save failed: the
    status it lays lasts the turns its line says."""
    import food_system
    pot = _item('potion', iid, buc)
    spec = _status_spec(pot.effect)
    if spec.get('buc') == 'harm' and buc == 'blessed':
        return                                   # blessed, it does no harm (said by its note)
    monkeypatch.setattr(random, 'randint', lambda a, b: a)     # every save fails
    p = Player()
    p.status_effects.clear()
    line = item_words.what_it_does(pot, p, buc_known=True)[0]
    food_system.drink_potion(p, pot)
    laid = max(int(v) for k, v in p.status_effects.items()
               if k not in ('control_immune', 'footing'))
    assert _n(line, 'for') == laid, (iid, buc, line, p.status_effects)


def test_a_blessed_harmful_drink_says_it_does_no_harm():
    line = item_words.what_it_does(_item('potion', 'potion_of_paralysis', 'blessed'),
                                   buc_known=True)[0]
    assert line.endswith("Blessed, it does you no harm."), line
    # Its blessing unknown, the kind's words: no note.
    line = item_words.what_it_does(_item('potion', 'potion_of_paralysis', 'blessed'),
                                   buc_known=False)[0]
    assert 'Blessed' not in line


def test_a_drain_says_what_it_takes():
    pot = _item('potion', 'potion_of_drain_wisdom', 'cursed')
    line = item_words.what_it_does(pot, buc_known=True)[0]
    p = Player()
    wis = p.WIS
    import food_system
    food_system.drink_potion(p, pot)
    assert f"takes {wis - p.WIS} points of your WIS" in line, line


# --------------------------------------------- the handlers, in a real game

@pytest.fixture
def g(monkeypatch, tmp_path):
    import main
    import paths
    import seeker_profile
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(paths, '_DEV_SAVE_DIR_OVERRIDE', str(tmp_path), raising=False)
    monkeypatch.setattr(seeker_profile, '_DIR_OVERRIDE', str(tmp_path / 'seekers'), raising=False)
    random.seed(7)
    items.bind_unique_registry(set())
    game = main.Game(pygame.display.set_mode((1280, 720)), player_name='__item_words__')
    from dungeon import FLOOR
    game.monsters[:] = []
    game.pets = []
    game.ground_items[:] = []
    game._maybe_wander_spawn = lambda: None
    game._popup_queue_list().clear()
    game.state = STATE_PLAYER
    d, p = game.dungeon, game.player
    x = min(max(p.x, 9), d.width - 10)
    y = min(max(p.y, 9), d.height - 10)
    for i in range(-8, 9):
        for j in range(-8, 9):
            d.tiles[y + j][x + i] = FLOOR
            d.traps.pop((x + i, y + j), None)
            (d.__dict__.get('fixtures') or {}).pop((x + i, y + j), None)
    p.x, p.y = x, y
    p.inventory = []
    p.status_effects.clear()
    p.max_hp = p.hp = 500
    game._refresh_fov()
    game.said = []
    game.add_message = lambda text, *a, **k: game.said.append(str(text))
    return game


def _mon(game, kind='kobold', dx=2):
    m = Monster({**KINDS[kind], 'id': kind}, game.player.x + dx, game.player.y)
    m._aware = True
    m.status_weak = []
    game.monsters.append(m)
    game._refresh_fov()
    return m


@pytest.mark.parametrize('sid,status', [
    ('scroll_of_bewilderment', 'confused'), ('scroll_of_confusion', 'confused'),
    ('scroll_of_madness', 'confused'), ('scroll_of_drowsing', 'sleeping'),
    ('scroll_of_sleep', 'sleeping'), ('scroll_of_deep_slumber', 'sleeping')])
def test_an_area_scroll_lays_the_turns_its_line_says(g, sid, status):
    m = _mon(g)
    sc = _item('scroll', sid)
    g._apply_scroll_effect(sc)
    line = item_words.what_it_does(sc, g.player, buc_known=False)[0]
    assert m.status_effects.get(status) == _n(line, 'for'), (sid, line, m.status_effects)


@pytest.mark.parametrize('sid,status', [
    ('scroll_of_quickness', 'hasted'), ('scroll_of_alacrity', 'hasted'),
    ('scroll_of_slow_time', 'time_stopped'), ('scroll_of_timeless', 'time_stopped'),
    ('scroll_of_ward', 'shielded'), ('scroll_of_absolute_ward', 'shielded'),
    ('scroll_of_the_lemuria', 'ward_lemuria'), ('scroll_of_the_udug_hul', 'ward_udug_hul')])
def test_a_scroll_on_the_hero_lays_the_turns_its_line_says(g, sid, status):
    sc = _item('scroll', sid)
    g._apply_scroll_effect(sc)
    line = item_words.what_it_does(sc, g.player, buc_known=False)[0]
    assert g.player.status_effects.get(status) == _n(line, 'for'), (sid, line)


@pytest.mark.parametrize('sid,buc,status', [
    ('scroll_of_absolute_ward', 'cursed', 'shielded'),       # a cursed rite keeps the 60 limit
    ('scroll_of_the_lemuria', 'blessed', 'ward_lemuria'),
    ('scroll_of_the_udug_hul', 'cursed', 'ward_udug_hul'),
    # (The light scrolls lay a light that goes with the hero, 2026-11-22:
    # they mapped the floor and gave clairvoyance before.)
    ('scroll_of_light', 'blessed', 'light'),
    ('scroll_of_illumination', 'blessed', 'light'),
    ('scroll_of_revelation', 'uncursed', 'light'),
    ('scroll_of_absolute_ward', 'blessed', 'shielded')])
def test_a_known_blessing_or_curse_changes_the_number_as_the_handler_does(g, sid, buc, status):
    sc = _item('scroll', sid, buc)
    g._apply_scroll_effect(sc)
    line = item_words.what_it_does(sc, g.player, buc_known=True)[0]
    assert g.player.status_effects.get(status) == _n(line, 'for'), (sid, buc, line)


@pytest.mark.parametrize('sid,buc', [('scroll_of_sharpen', 'uncursed'),
                                     ('scroll_of_sharpen', 'blessed'),
                                     ('scroll_of_weaponsmith', 'uncursed')])
def test_an_enchant_scroll_adds_what_its_line_says(g, sid, buc):
    w = items.instantiate_weapon('longsword', 'iron')
    w.enchant_bonus = 0
    g.player.weapon = w
    sc = _item('scroll', sid, buc)
    g._apply_scroll_effect(sc)
    line = item_words.what_it_does(sc, g.player, buc_known=True)[0]
    assert w.enchant_bonus == _n(line, 'Adds +'), (sid, buc, line, w.enchant_bonus)


def test_a_protection_rite_says_what_it_also_keeps_off(g):
    sc = _item('scroll', 'scroll_of_greater_protection')
    g._apply_scroll_effect(sc)
    line = item_words.what_it_does(sc, g.player, buc_known=False)[0]
    p = g.player
    assert p.status_effects.get('missile_ward') == 30 and p.status_effects.get('fear_immune') == 30
    assert "For 30 turns, also: no arrow, stone or spear reaches you and nothing can frighten you." \
        in line, line


@pytest.mark.parametrize('intel', [10, 30])
def test_the_earth_scroll_takes_the_share_its_line_says(g, intel):
    from game_magic import _is_big_foe
    g.player.INT = intel
    m = _mon(g, 'kobold')
    m.max_hp = m.hp = 50                     # an ordinary foe (the mightiest take a tenth)
    m.resistances = []
    assert not _is_big_foe(m)
    sc = _item('scroll', 'scroll_of_cataclysm')
    g._apply_scroll_effect(sc)
    line = item_words.what_it_does(sc, g.player, buc_known=False)[0]
    said = _n(line, 'loses')
    assert abs(said - 100 * (50 - m.hp) / 50) <= 1, (line, m.hp)      # (whole hit points)


@pytest.mark.parametrize('wid,status', [
    ('wand_of_drowsing', 'sleeping'), ('wand_of_deep_slumber', 'sleeping'),
    ('wand_of_slow', 'slowed'), ('wand_of_madness', 'confused'), ('wand_of_hold', 'paralyzed'),
    ('wand_of_dark_curse', 'blinded'), ('wand_of_fear', 'feared'), ('wand_of_charm', 'charmed'),
    ('wand_of_poison_monster', 'poisoned'), ('wand_of_weaken_monster', 'weakened'),
    ('wand_of_unstringing', 'unstrung'), ('wand_of_curse_monster', 'cursed')])
def test_a_wand_lays_the_turns_its_line_says(g, wid, status):
    m = _mon(g, 'goblin')
    w = _item('wand', wid)
    g._wand_override_target = m
    g._apply_wand_effect(w)
    g._wand_override_target = None
    line = item_words.what_it_does(w, g.player, buc_known=False)[0]
    assert m.status_effects.get(status) == _n(line, 'for'), (wid, line, m.status_effects)


@pytest.mark.parametrize('wid,status,key', [('wand_of_blizzard', 'slowed', 'slows it for'),
                                            ('wand_of_curse_monster', 'slowed', 'slows it for')])
def test_a_wands_second_status_lasts_what_its_line_says(g, monkeypatch, wid, status, key):
    m = _mon(g, 'goblin')
    monkeypatch.setattr(g, '_wand_tier_damage', lambda base, tier: 1)    # it lives to be slowed
    w = _item('wand', wid)
    g._wand_override_target = m
    g._apply_wand_effect(w)
    g._wand_override_target = None
    line = item_words.what_it_does(w, g.player, buc_known=False)[0]
    assert m.status_effects.get(status) == _n(line, key), (wid, line, m.status_effects)


def test_a_thrown_potion_says_what_it_does_to_the_foe(g):
    m = _mon(g, 'goblin')
    pot = _item('potion', 'potion_of_sleep')
    words = item_words.thrown_line(pot, g._THROW_DEBUFF_MAP, g._THROW_BUFF_MAP,
                                   g._THROW_BUFFS_MONSTERS_USE)
    g._apply_thrown_potion(pot, m, 'potion')
    assert words == f"Thrown, it leaves a foe Sleeping for {m.status_effects['sleeping']} turns"
    assert item_words.thrown_line(_item('potion', 'potion_of_haste'), g._THROW_DEBUFF_MAP,
                                  g._THROW_BUFF_MAP, g._THROW_BUFFS_MONSTERS_USE) == \
        "Thrown, it does nothing to a foe"


# ------------------------------------------------------------------ the cards

def _known(g, it):
    it.id_level = 5
    it.identified = True
    g.player.known_item_ids.add(it.id)
    g.player.inventory.append(it)
    return it


def test_the_kit_card_of_an_identified_scroll_says_what_it_does(g):
    sc = _known(g, _item('scroll', 'scroll_of_cure_wounds'))
    card = [str(t[0]) for t in g._kit_detail_lines_for_item('consumables', 'pack', sc)]
    assert "Nothing beyond its stats." not in card
    assert "What It Does" in card
    assert any(t.startswith("Heals 2d4 health, or 12% of your health") for t in card), card
    assert g._kit_consumable_effect(sc) == "Heals 2d4 or more"


def test_the_menu_card_of_an_identified_scroll_says_what_it_does(g):
    sc = _known(g, _item('scroll', 'scroll_of_sleep'))
    card = [str(t[0]) for t in g._menu_item_detail_lines(sc, 'Read')]
    assert not any('Effect:' in t or 'tier' in t.lower() for t in card), card
    assert "Sleeps all in sight, 10 turns" in card, card
    assert any(t.startswith("Puts every monster in sight to sleep for 10 turns") for t in card)
    lore = [str(t[0]) for t in g._lore_item_mechanic_lines(sc, g._kit_visible_level(sc))]
    assert any(t.startswith("Puts every monster in sight to sleep") for t in lore), lore
    assert not any(t.startswith('Effect:') for t in lore)


def test_the_menu_card_of_a_wand_keeps_its_charges(g):
    w = _known(g, _item('wand', 'wand_of_fire_bolt'))
    w.charges, w.max_charges = 2, 5
    summary = g._get_item_stats_brief(w)
    assert summary.startswith("Fire, ") and summary.endswith("Charges: 2/5"), summary
    card = [str(t[0]) for t in g._menu_item_detail_lines(w, 'Zap')]
    assert "2 of 5 charges left." in card, card


def test_an_unidentified_scroll_still_says_to_identify_it(g):
    sc = _item('scroll', 'scroll_of_cure_wounds')
    sc.id_level = 0
    g.player.known_item_ids.discard(sc.id)
    g.player.inventory.append(sc)
    card = [str(t[0]) for t in g._kit_detail_lines_for_item('consumables', 'pack', sc)]
    assert any(t.startswith("Not identified yet") for t in card)
    assert not any('Heals' in t for t in card), card
    menu = [str(t[0]) for t in g._menu_item_detail_lines(sc, 'Read')]
    assert not any('Heals' in t for t in menu), menu


def test_the_encyclopedia_pages_say_what_the_kind_does(g):
    for cat, iid in (('scroll', 'scroll_of_sleep'), ('wand', 'wand_of_sleep'),
                     ('spellbook', 'spellbook_fire_spark')):
        entry = {'_id': iid, **_data(cat)[iid]}
        page = [str(t[0]) for t in g._encyclopedia_article_lines(cat, entry)]
        want = item_words.what_it_does(entry, g.player, buc_known=False, item_class=cat)
        assert "What It Does" in page and all(w in page for w in want), (iid, page)
        assert not any(t.startswith('Effect:') or t.startswith('Charges: ?') for t in page)
        assert g._encyclopedia_entry_brief(cat, entry) == item_words.short_line(
            entry, g.player, buc_known=False, item_class=cat)
