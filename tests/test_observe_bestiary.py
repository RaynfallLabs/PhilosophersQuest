"""O on a creature the hero has IDENTIFIED opens its Bestiary page (Brandon,
2026-10-18: "when using O on an identified monster, it should bring up the
monster's bestiary page.")

Identified (MONSTER_FAMILIES_DESIGN ruling 1) = the kind is in
studied_monster_ids, or in lore_known_monster_ids (the Book of Thoth,
Omnisight), or its monster family is at tier 1 or more. That opens the page
B -> Bestiary -> Enter shows; Esc returns to play. A kind only SEEN keeps
the plain look ("You don't know this creature yet") and has a short page in
B (name, art, family, "Not yet studied", the family's progress line). An
invisible creature the hero cannot see, or a mimic still in disguise, never
opens its page (unseen.py: never reveal hidden things).

These drive a real headless Game through the real keys.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(name='__test_observe_bestiary__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(11)
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _open_spot(g, half=3):
    from dungeon import FLOOR
    x = min(max(g.player.x, half + 1), g.dungeon.width - half - 2)
    y = min(max(g.player.y, half + 1), g.dungeon.height - half - 2)
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            g.dungeon.tiles[y + j][x + i] = FLOOR
    return x, y


def _scene(mid, dx=2, dy=0, known=True):
    from monster import Monster
    g = _game()
    x, y = _open_spot(g)
    g.player.x, g.player.y = x, y
    g.ground_items = [i for i in g.ground_items
                      if abs(i.x - x) > 3 or abs(i.y - y) > 3]
    m = Monster({**MONS[mid], 'id': mid}, x + dx, y + dy)
    g.monsters = [m]
    g._refresh_fov()
    g.visible |= {(x + i, y + j) for i in range(-3, 4) for j in range(-3, 4)}
    g.player.known_monster_ids.discard(mid)
    g.player.studied_monster_ids.discard(mid)
    if known:
        # Seen AND studied: an identified kind.
        g.player.known_monster_ids.add(mid)
        g.player.studied_monster_ids.add(mid)
    return g, m


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))


def _observe(g, m):
    """O, put the cursor on the creature, Enter: the real keys."""
    _press(g, pygame.K_o, 'o')
    g.target_cursor_x, g.target_cursor_y = m.x, m.y
    _press(g, pygame.K_RETURN)


def _plain_kind():
    for k in ('goblin', 'kobold', 'giant_rat', 'jackal'):
        if k in MONS:
            return k
    raise AssertionError('no plain monster')


def test_o_on_a_known_monster_opens_its_bestiary_page():
    from game_states import STATE_ENCYCLOPEDIA, STATE_PLAYER
    kind = _plain_kind()
    g, m = _scene(kind)
    _observe(g, m)
    assert g.state == STATE_ENCYCLOPEDIA
    assert g.encyclopedia_category == 'bestiary'
    assert g._encyclopedia_entry is not None and g._encyclopedia_entry['_id'] == kind
    # The very page the B -> Bestiary list opens.
    g2 = _game('__test_observe_bestiary_b__')
    g2.player.known_monster_ids.add(kind)
    g2.player.studied_monster_ids.add(kind)
    g2._open_encyclopedia()
    g2._encyclopedia_load_entries('bestiary')
    listed = next(e for e in g2.encyclopedia_entries if e['_id'] == kind)
    assert g._encyclopedia_entry == listed
    lines = [str(t[0]) for t in g._encyclopedia_article_lines('bestiary', g._encyclopedia_entry)]
    assert lines[0] == g._fix_name_case(MONS[kind]['name'])
    assert lines[1].startswith('Family: ') and lines[1].endswith('(studied)')
    # The look still says what it saw, and costs no turn.
    turn = g.turn_count
    assert any(MONS[kind]['name'].lower() in str(e[0]).lower() for e in g.msg_log.entries[-4:])
    assert g.turn_count == turn
    # Esc returns to play.
    _press(g, pygame.K_ESCAPE)
    assert g.state == STATE_PLAYER


def test_o_on_an_unknown_monster_keeps_the_plain_look():
    from game_states import STATE_PLAYER
    g, m = _scene(_plain_kind(), known=False)
    _observe(g, m)
    assert g.state == STATE_PLAYER
    assert any('You see' in str(e[0]) for e in g.msg_log.entries[-4:])


def test_o_on_a_seen_but_unstudied_monster_does_not_open_its_page():
    """Ruling 1: seeing is not knowing. A kind seen many times still keeps
    the plain look until it is identified."""
    from game_states import STATE_PLAYER
    g, m = _scene(_plain_kind(), known=False)
    g.player.known_monster_ids.add(m.kind)            # seen, not studied
    _observe(g, m)
    assert g.state == STATE_PLAYER
    recent = [str(e[0]) for e in g.msg_log.entries[-4:]]
    assert any("You don't know this creature yet" in t for t in recent)
    assert not g._open_bestiary_page(m.kind)


def test_o_on_a_kind_whose_family_is_at_tier_one_opens_its_page():
    """Tier 1 of a family (Recognise): every member seen gets its full page,
    and the look names the family, even a kind never studied."""
    import family_lore
    from game_states import STATE_ENCYCLOPEDIA
    g, m = _scene('ghoul', known=False)
    g.player.known_monster_ids.add('ghoul')
    need = family_lore.thresholds('restless_dead')[0]
    others = [k for k in family_lore.members('restless_dead')
              if k != 'ghoul' and not family_lore.is_keystone(k)][:need]
    g.player.studied_monster_ids.update(others)
    assert family_lore.tier(g.player, 'restless_dead') == 1
    _observe(g, m)
    assert g.state == STATE_ENCYCLOPEDIA and g._encyclopedia_entry['_id'] == 'ghoul'
    assert any('Restless Dead.' in str(e[0]) for e in g.msg_log.entries[-4:])
    lines = [str(t[0]) for t in g._encyclopedia_article_lines('bestiary', g._encyclopedia_entry)]
    assert 'known by its family, not yet studied' in lines[1]


def test_the_book_of_thoth_opens_pages_but_teaches_no_tiers():
    import family_lore
    from game_states import STATE_ENCYCLOPEDIA
    g, m = _scene('ghoul', known=False)
    g.player.known_monster_ids.add('ghoul')
    g.player.lore_known_monster_ids.add('ghoul')      # what the Thoth reveal writes
    assert family_lore.tiers(g.player) == {}
    _observe(g, m)
    assert g.state == STATE_ENCYCLOPEDIA and g._encyclopedia_entry['_id'] == 'ghoul'


def test_a_kind_only_seen_has_a_short_page_in_the_bestiary():
    g = _game()
    kind = _plain_kind()
    g.player.known_monster_ids.add(kind)
    g._open_encyclopedia()
    g._encyclopedia_load_entries('bestiary')
    entry = next(e for e in g.encyclopedia_entries if e['_id'] == kind)
    assert entry['_known'] is False
    lines = [str(t[0]) for t in g._encyclopedia_article_lines('bestiary', entry)]
    assert lines[0] == g._fix_name_case(MONS[kind]['name'])
    assert lines[1].startswith('Family: ')
    assert any(t.startswith('Not yet studied') for t in lines)
    assert any(' of ' in t and ' to Recognise' in t for t in lines)     # the progress line
    joined = ' '.join(lines)
    assert 'HP' not in joined and 'Lore' not in joined and 'Bite' not in joined
    assert g._encyclopedia_entry_brief('bestiary', entry).startswith('Unstudied')


def test_o_on_an_unseen_invisible_monster_never_opens_its_page():
    from game_states import STATE_PLAYER
    g, m = _scene('dread_wraith')                  # known, but he cannot see it
    _observe(g, m)
    assert g.state == STATE_PLAYER
    assert not any('Dread Wraith' in str(e[0]) for e in g.msg_log.entries[-6:])


def test_o_on_a_seen_invisible_monster_opens_it():
    from game_states import STATE_ENCYCLOPEDIA
    g, m = _scene('dread_wraith')
    g.player.add_effect('see_invisible', 30)
    _observe(g, m)
    assert g.state == STATE_ENCYCLOPEDIA and g._encyclopedia_entry['_id'] == 'dread_wraith'


def test_o_on_a_disguised_mimic_never_opens_its_page():
    from game_states import STATE_PLAYER
    for mid in ('lurking_horror', 'gilded_mimic'):
        g, m = _scene(mid, dx=3)
        _observe(g, m)
        assert g.state == STATE_PLAYER, mid
        assert g.__dict__.get('_encyclopedia_entry') is None, mid


def test_esc_in_the_encyclopedia_steps_back_as_its_footer_says():
    """B -> Bestiary -> an article: Esc goes back to the list, then to the
    categories, then to play ("ESC: list" closed the whole book before)."""
    from game_states import STATE_ENCYCLOPEDIA, STATE_PLAYER
    g = _game()
    g.player.known_monster_ids.add(_plain_kind())
    g.player.studied_monster_ids.add(_plain_kind())
    _press(g, pygame.K_b, 'b')
    _press(g, pygame.K_RETURN)
    _press(g, pygame.K_RETURN)
    assert g.state == STATE_ENCYCLOPEDIA and g._encyclopedia_entry is not None
    _press(g, pygame.K_ESCAPE)
    assert g.state == STATE_ENCYCLOPEDIA and g._encyclopedia_entry is None
    assert g.encyclopedia_category == 'bestiary'
    _press(g, pygame.K_ESCAPE)
    assert g.state == STATE_ENCYCLOPEDIA and g.encyclopedia_category == ''
    _press(g, pygame.K_ESCAPE)
    assert g.state == STATE_PLAYER
    # Opened again with B after an O page, Esc steps back normally.
    g2, m = _scene(_plain_kind())
    _observe(g2, m)
    _press(g2, pygame.K_ESCAPE)
    assert g2.state == STATE_PLAYER
    _press(g2, pygame.K_b, 'b')
    _press(g2, pygame.K_RETURN)
    _press(g2, pygame.K_RETURN)
    _press(g2, pygame.K_ESCAPE)
    assert g2.state == STATE_ENCYCLOPEDIA


def test_the_help_line_for_o_mentions_the_bestiary():
    import inspect
    import game_render
    src = inspect.getsource(game_render.RenderMixin._draw_help_screen)
    assert '("O", "Look / Bestiary"' in src
