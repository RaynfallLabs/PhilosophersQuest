"""Manifest, the Dreamspun Sketchbook's power (src/sketch_manifest.py,
src/game_manifest.py, data/manifest.json).

Brandon, 2026-11-15: "she should be able to Manifest ANY monster she has
studied; needs a new menu UI so it's easy to sort by what she'd want...
probably element/attack type? then in the menu sorted by level, descending."
Then: "let's make the image last based on how many quiz questions she gets
right, with the base being her INT" (the rule: INT + 5 turns for each right
answer).

Pins: what she can draw (every studied kind and any in view, never a boss or
a named foe); the rows' order, the tabs and their counts; the "Weak!" marks
for a known foe in view and the tab the menu opens on; the duration; a
drawing's bite typed as its subject's first attack, so a weakness doubles it
through Monster.take_damage (an old pickled sketch bites as before); a
real-keys journey V, Manifest, the menu, Enter, the quiz answered right, the
sketch beside her; the QA key (Shift+V). How the menu reads to a kid is a
play-test question: Claude cannot drive Pygame.
"""
import os
import pickle
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

import sketch_manifest as manifest  # noqa: E402

pygame.init()

SKETCHBOOK = 'dreamspun_sketchbook'


def _game(size=(1280, 720), name='__test_manifest__'):
    import items
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(11)
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode(size), player_name=name)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


def _give_sketchbook(g):
    from items import make_item_by_id
    book = make_item_by_id('accessory', SKETCHBOOK)
    book.id_level = 5
    g.player.inventory.append(book)
    g.player.refresh_carry_bonuses()
    return book


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))


def _monster(kind, x=0, y=0, hp=None):
    from monster import Monster
    m = Monster(manifest.defn(kind), x, y)
    if hp is not None:
        m.hp = m.max_hp = hp
    return m


def _texts(g, n=10):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _capture():
    """tools/ui/capture.py: its real-key quiz answering (play_quiz)."""
    import importlib.util
    if 'pq_ui_capture' in sys.modules:
        return sys.modules['pq_ui_capture']
    spec = importlib.util.spec_from_file_location(
        'pq_ui_capture', os.path.join(ROOT, 'tools', 'ui', 'capture.py'))
    mod = importlib.util.module_from_spec(spec)
    sys.modules['pq_ui_capture'] = mod
    spec.loader.exec_module(mod)
    return mod


def _open_spot(g, half=3):
    from test_shep import _open_room
    return _open_room(g, half)


# ---------------------------------------------------------------------------
# The data and the pure rules
# ---------------------------------------------------------------------------

def test_the_data_file_says_the_rules():
    r = manifest.rules()
    assert r['_doc']
    assert r['base_stat'] == 'INT' and r['turns_per_right'] == 5
    assert r['quiz'] == {'subject': 'ai', 'mode': 'escalator_chain', 'tier': 1, 'max_chain': 5}
    assert r['cooldown'] == 500 and r['power_id'] == 'sketch_manifest'
    for flag in ('is_boss', 'is_mini_boss', 'proper_noun', 'quest_only', 'is_seal_demon'):
        assert flag in r['exclude_flags']
    assert {'hell_bovine', 'cow_king'} <= set(r['exclude_kinds'])


def test_duration_is_int_plus_five_a_right_answer():
    assert manifest.duration(14, 0) == 0                  # none right: it smudges
    assert manifest.duration(14, 1) == 19
    assert manifest.duration(14, 5) == 39                 # Fianna's INT 14, all five right
    assert manifest.max_duration(14) == 39
    assert manifest.duration_line(14) == \
        "Lasts INT (14) + 5 turns for each right answer: up to 39 turns."
    p = types.SimpleNamespace(INT=16)
    assert manifest.stat_value(p) == 16
    assert manifest.duration(manifest.stat_value(p), 3) == 31


def test_bosses_named_foes_the_cow_level_and_the_nameless_are_never_drawn():
    defs = manifest.defs()
    for kind, d in defs.items():
        flagged = any(d.get(f) for f in manifest.rules()['exclude_flags'])
        if flagged:
            assert not manifest.can_draw(kind), kind
    for kind in ('hell_bovine', 'cow_king', 'black_knight', 'asterion_minotaur'):
        assert not manifest.can_draw(kind), kind
    assert manifest.can_draw('goblin') and manifest.can_draw('skeleton')
    # A creature with no family (a person of an encounter) or nothing to bite with.
    assert not manifest.can_draw('x', {'name': 'traveller', 'attacks': [{'type': 'slash'}]})
    assert not manifest.can_draw('x', {'name': 'statue', 'family': 'constructs', 'attacks': []})
    assert not manifest.can_draw('not_a_kind')
    # Every kind it can draw has art: a menu row never shows a letter glyph.
    import lore_art
    assert all(lore_art.art_path('monster', k) for k in defs if manifest.can_draw(k))


def test_rows_are_the_studied_kinds_and_those_in_view_by_level_highest_first():
    studied = {'goblin', 'skeleton', 'cerberus', 'asterion_minotaur', 'cow_king'}
    rows = manifest.make_rows(studied, in_view=['wraith', 'black_knight'])
    kinds = [r['kind'] for r in rows]
    assert set(kinds) == {'goblin', 'skeleton', 'cerberus', 'wraith'}
    assert kinds[0] == 'cerberus'                         # level 77 above the rest
    levels = [r['level'] for r in rows]
    assert levels == sorted(levels, reverse=True)
    ones = [r['name'] for r in rows if r['level'] == 1]
    assert ones == sorted(ones, key=str.lower)            # then by name
    wraith = next(r for r in rows if r['kind'] == 'wraith')
    assert wraith['in_view'] and not wraith['studied']
    # (the wraith walks from floor 12 since the monster pass of 2026-11-17)
    assert manifest.row_line(wraith) == f"Level {manifest.defs()['wraith']['min_level']}, Drain, In View"
    assert manifest.defs()['wraith']['min_level'] == 12
    gob = next(r for r in rows if r['kind'] == 'goblin')
    assert gob['name'] == 'Goblin' and gob['type'] == 'pierce'
    assert manifest.row_line(gob) == "Level 1, Pierce"
    assert gob['hp'] == max(10, int(manifest.mean_hp(manifest.defs()['goblin']) * 0.4))


def test_the_bite_types_in_the_heros_words():
    assert manifest.hero_type('necrotic') == 'drain'
    assert manifest.hero_type('shadow') == 'drain'
    assert manifest.hero_type('psionic') == 'magic'
    assert manifest.hero_type('physical') == 'blunt'
    assert manifest.hero_type('fire') == 'fire'
    assert manifest.hero_type('gibberish') == 'physical'
    assert manifest.hero_type(None) == 'physical'
    assert manifest.bite_type_of([{'damage': '1d8+2'}]) == 'physical'     # the Codex helper
    assert manifest.bite_type_of([{'type': 'cold'}, {'type': 'fire'}]) == 'cold'   # the first
    assert manifest.mean_hp({'hp': '6d8+6'}) == 33
    assert manifest.mean_hp({'hp': '60'}) == 60


def test_tabs_are_all_then_each_bite_type_she_can_draw_with_counts():
    studied = {'goblin', 'giant_rat', 'skeleton', 'zombie', 'fire_beetle', 'wraith', 'acid_blob'}
    rows = manifest.make_rows(studied)
    tabs = manifest.tabs(rows)
    assert tabs[0] == ('all', 'All', 7)
    assert tabs[1:] == [('slash', 'Slash', 1), ('pierce', 'Pierce', 2), ('blunt', 'Blunt', 1),
                        ('fire', 'Fire', 1), ('acid', 'Acid', 1), ('drain', 'Drain', 1)]
    assert [r['kind'] for r in manifest.tab_rows(rows, 'pierce')] == ['giant_rat', 'goblin']
    assert manifest.tab_rows(rows, 'all') == rows


def test_a_known_foe_in_view_marks_what_it_is_weak_to_and_opens_that_tab():
    studied = {'goblin', 'giant_rat', 'skeleton', 'cave_toad', 'zombie', 'fire_beetle'}
    foe = _monster('skeleton')                     # weak to blunt and holy
    rows = manifest.make_rows(studied, foes=[('Skeleton', foe)])
    weak = {r['kind'] for r in rows if r['weak']}
    assert weak == {'skeleton', 'cave_toad'}       # the two blunt biters
    toad = next(r for r in rows if r['kind'] == 'cave_toad')
    assert toad['strong_against'] == ['Skeleton']
    assert manifest.opening_tab(rows) == 'blunt'
    assert manifest.reason_line('blunt', rows) == "Opened on Blunt: Strong against Skeleton"
    zombie = next(r for r in rows if r['kind'] == 'zombie')
    assert zombie['resisted_by'] == ['Skeleton']   # it resists a cutting blow
    # No known foe: no marks, and the menu opens on All.
    plain = manifest.make_rows(studied)
    assert not any(r['weak'] for r in plain)
    assert manifest.opening_tab(plain) == 'all'
    assert manifest.reason_line('all', plain) == ''


def test_the_qa_reach_is_max_ten_or_floor_plus_five():
    assert manifest.qa_max_level(1) == 10
    assert manifest.qa_max_level(20) == 25
    kinds = manifest.qa_kinds(1)
    assert 'goblin' in kinds and 'cerberus' not in kinds
    assert all(manifest.can_draw(k) and manifest.level_of(manifest.defs()[k]) <= 10 for k in kinds)


# ---------------------------------------------------------------------------
# The drawing's bite
# ---------------------------------------------------------------------------

def test_a_sketch_bites_as_its_subjects_first_attack():
    from pet_system import SketchedPet
    assert SketchedPet(_monster('cave_toad'), 0, 0, 10).bite_type == 'blunt'
    assert SketchedPet(_monster('wraith'), 0, 0, 10).bite_type == 'drain'
    assert SketchedPet(_monster('goblin'), 0, 0, 10).bite_type == 'pierce'


def test_a_typed_bite_meets_a_weakness_in_the_pet_turn():
    """A sketch of a blunt biter bites a skeleton (weak to blunt) for double,
    through Monster.take_damage in Game._do_pet_turns."""
    import affinity
    from pet_system import SketchedPet
    g = _game()
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    pet = SketchedPet(_monster('cave_toad'), x + 1, y, 30)
    pet.get_attack_damage = lambda *_a, **_k: 10
    bones = _monster('skeleton', x + 2, y, hp=1000)
    g.monsters, g.pets = [bones], [pet]
    g._do_pet_turns()
    assert bones.hp == 1000 - 20
    notes = affinity.drain()
    assert any(m is bones and kind == affinity.WEAK and word == 'blunt' for m, kind, word in notes)


def test_an_old_pickled_sketch_bites_as_before():
    """A sketch saved before its bite had a type bites plain physical."""
    from pet_system import SketchedPet
    old = SketchedPet(_monster('cave_toad'), 0, 0, 30)
    del old.__dict__['bite_type']
    old = pickle.loads(pickle.dumps(old))
    assert old.bite_type == 'physical'
    g = _game()
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    old.x, old.y = x + 1, y
    old.get_attack_damage = lambda *_a, **_k: 10
    bones = _monster('skeleton', x + 2, y, hp=1000)
    g.monsters, g.pets = [bones], [old]
    g._do_pet_turns()
    assert bones.hp == 1000 - 10


def test_the_codex_helper_still_bites_by_its_dice_as_plain_physical():
    import hero_specials as HS
    g = _game()
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    HS._eff_summon_sketch_helper(g, {}, {'duration': 10, 'level': 3, 'damage': '1d8+2'}, 3)
    helper = g.pets[0]
    assert helper.bite_type == 'physical'
    assert all(3 <= helper.get_attack_damage() <= 10 for _ in range(50))


# ---------------------------------------------------------------------------
# The menu and the journey, by real keys
# ---------------------------------------------------------------------------

def test_with_nothing_to_draw_it_says_so_and_spends_no_turn():
    from game_states import STATE_PLAYER
    g = _game()
    _give_sketchbook(g)
    turn = g.turn_count
    assert g._activate_power('sketch_manifest') is True
    assert g.state == STATE_PLAYER
    assert g.turn_count == turn
    assert _texts(g)[-1] == manifest.EMPTY_LINE


def test_the_v_menu_offers_manifest_with_its_short_description():
    g = _game()
    _give_sketchbook(g)
    _press(g, pygame.K_v, 'v')
    entry = next(p for p in g._power_menu_list if p[0] == 'sketch_manifest')
    assert entry[1]['label'] == 'Manifest'
    assert entry[1]['desc'] == \
        "Draw a creature you have studied, or one in view, as a short-lived ally."
    assert entry[1]['cooldown'] == 500


def _open_menu(g):
    from game_states import STATE_MANIFEST_MENU
    _press(g, pygame.K_v, 'v')
    idx = next(i for i, p in enumerate(g._power_menu_list) if p[0] == 'sketch_manifest')
    for _ in range(idx):
        _press(g, pygame.K_DOWN)
    _press(g, pygame.K_RETURN)
    assert g.state == STATE_MANIFEST_MENU


def test_tabs_and_cursor_by_real_keys_and_esc_spends_no_turn():
    from game_states import STATE_PLAYER
    g = _game()
    _give_sketchbook(g)
    g.player.studied_monster_ids = {'goblin', 'giant_rat', 'skeleton', 'zombie', 'cerberus'}
    turn = g.turn_count
    _open_menu(g)
    assert g._manifest_tab_slug() == 'all'                # no known foe in view
    assert g._manifest_tab_rows()[0]['kind'] == 'cerberus'
    g.render()
    seen = []
    for _ in range(len(g._mf_tabs)):
        seen.append(g._manifest_tab_slug())
        _press(g, pygame.K_RIGHT)
        g.render()
    assert seen == [t[0] for t in manifest.tabs(g._mf_rows)]
    assert g._manifest_tab_slug() == 'all'                # round to the start
    _press(g, pygame.K_LEFT)
    assert g._manifest_tab_slug() == seen[-1]
    _press(g, pygame.K_TAB)
    assert g._manifest_tab_slug() == 'all'
    _press(g, pygame.K_END)
    assert g._mf_sel == len(g._mf_rows) - 1
    _press(g, pygame.K_HOME)
    assert g._mf_sel == 0
    _press(g, pygame.K_ESCAPE)
    assert g.state == STATE_PLAYER
    assert g.turn_count == turn


def test_a_known_foe_in_view_opens_the_menu_on_the_tab_it_is_weak_to():
    g = _game()
    _give_sketchbook(g)
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    g.player.studied_monster_ids = {'goblin', 'giant_rat', 'skeleton', 'cave_toad', 'zombie'}
    g.monsters = [_monster('skeleton', x + 2, y)]
    g._refresh_fov()
    assert g._sees_monster(g.monsters[0])
    _open_menu(g)
    assert g._manifest_tab_slug() == 'blunt'
    rows = g._manifest_tab_rows()
    assert rows and all(r['weak'] and r['strong_against'] == ['Skeleton'] for r in rows)
    assert g._mf_open == ('blunt', "Opened on Blunt: Strong against Skeleton")
    g.render()


def test_a_creature_in_view_can_be_drawn_on_first_meeting_but_a_boss_cannot():
    g = _game()
    _give_sketchbook(g)
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    g.monsters = [_monster('harpy', x + 2, y), _monster('cow_king', x - 2, y)]
    g._refresh_fov()
    _open_menu(g)
    kinds = [r['kind'] for r in g._mf_rows]
    assert kinds == ['harpy']
    assert g._mf_rows[0]['in_view'] and not g._mf_rows[0]['studied']


def test_journey_v_manifest_enter_five_right_answers_and_the_sketch_stands_beside_her():
    from game_states import STATE_PLAYER, STATE_QUIZ
    capture = _capture()
    g = _game()
    _give_sketchbook(g)
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    g.player.studied_monster_ids = {'goblin'}
    stat = g.player.INT
    assert stat == 12                                      # 10, and the sketchbook's +2
    _open_menu(g)
    _press(g, pygame.K_RETURN)
    assert g.state == STATE_QUIZ
    assert g.quiz_engine.subject == 'ai'
    capture.play_quiz(g, 'ccccc')
    capture.settle_quiz(g)
    assert g.state == STATE_PLAYER
    sketches = [p for p in g.pets if getattr(p, 'is_sketch', False)]
    assert len(sketches) == 1
    pet = sketches[0]
    want = stat + 5 * 5
    assert pet.monster_kind == 'goblin' and pet.bite_type == 'pierce'
    assert want - 1 <= pet.turns_remaining <= want     # the turn the drawing took has ticked
    assert max(abs(pet.x - x), abs(pet.y - y)) == 1 and (pet.x, pet.y) != (x, y)
    assert pet.max_hp == max(10, int(manifest.mean_hp(manifest.defs()['goblin']) * 0.4))
    assert g.player.power_cooldowns['sketch_manifest'] == 500 or \
        g.player.power_cooldowns['sketch_manifest'] == 499
    assert any(f"A Sketched Goblin materializes! ({want} turns)" in t for t in _texts(g, 20))


def test_a_wrong_first_answer_smudges_the_page_and_the_power_stays_ready():
    from game_states import STATE_PLAYER
    capture = _capture()
    g = _game()
    _give_sketchbook(g)
    g.player.studied_monster_ids = {'goblin'}
    _open_menu(g)
    _press(g, pygame.K_RETURN)
    capture.play_quiz(g, 'w')
    capture.settle_quiz(g)
    assert g.state == STATE_PLAYER
    assert not any(getattr(p, 'is_sketch', False) for p in g.pets)
    assert not g.player.power_cooldowns.get('sketch_manifest', 0)
    assert any("The sketch smudges" in t for t in _texts(g))


def test_the_menu_draws_every_tab_at_the_smallest_and_largest_windows():
    for size in ((1093, 614), (1280, 720), (3440, 1440)):
        g = _game(size)
        _give_sketchbook(g)
        g.player.studied_monster_ids = set(manifest.qa_kinds(10))
        x, y = _open_spot(g)
        g.player.x, g.player.y = x, y
        g.monsters = [_monster('skeleton', x + 2, y)]
        g._refresh_fov()
        _open_menu(g)
        for _ in g._mf_tabs:
            for _k in range(3):
                g.render()
                _press(g, pygame.K_DOWN)
            _press(g, pygame.K_END)
            g.render()
            _press(g, pygame.K_RIGHT)


# ---------------------------------------------------------------------------
# The QA key
# ---------------------------------------------------------------------------

def test_the_qa_key_gives_the_sketchbook_studies_the_kinds_and_readies_the_power():
    import family_lore
    g = _game()
    g.player.qa_tools = True
    g.player.power_cooldowns['sketch_manifest'] = 300
    assert not any(getattr(i, 'id', '') == SKETCHBOOK for i in g.player.inventory)
    _press(g, pygame.K_v, 'V')
    assert sum(1 for i in g.player.inventory if getattr(i, 'id', '') == SKETCHBOOK) == 1
    floor = g.dungeon_level
    want = set(manifest.qa_kinds(floor))
    assert want and want <= family_lore.studied(g.player)
    assert g.player.power_cooldowns['sketch_manifest'] == 0
    _press(g, pygame.K_v, 'V')                             # again: no second sketchbook
    assert sum(1 for i in g.player.inventory if getattr(i, 'id', '') == SKETCHBOOK) == 1


def test_the_qa_key_does_nothing_without_the_qa_build():
    g = _game()
    g.player.qa_tools = False
    _press(g, pygame.K_v, 'V')
    assert not any(getattr(i, 'id', '') == SKETCHBOOK for i in g.player.inventory)
    assert not g.player.studied_monster_ids
