"""Bug bash 3.5.1, hunter D: tonight's fixes reviewed, their seams, the screens.

Each test pins one bug found in review (D1, D2... in the hunter's report).
"""
import json
import os
import random
import sys

import pytest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, HERE)

import pygame  # noqa: E402

pygame.init()

import affinity  # noqa: E402
from monster import Monster  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _m(kind, x=0, y=0):
    return Monster({**MONS[kind], 'id': kind}, x, y)


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(351)
    g = Game(pygame.display.set_mode((1280, 720)), player_name='__test_bugbash_351_d__')
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    log = []
    monkeypatch.setattr(g, 'add_message', lambda text, kind='info', *a, **k: log.append(text))
    g._log = log
    return g


def _page_texts(g, corpse):
    identity, mechanics, lore = g._lore_corpse_lines(corpse, 5)
    return [str(t[0]) for t in identity], [str(t[0]) for t in mechanics], lore


# ---------------------------------------------------------------------------
# D1. A studied body's page tells what its kind is made of
# ---------------------------------------------------------------------------

def test_d1_a_slain_stirge_swarms_body_says_it_shrugs_off_a_sword(game):
    """The body of a creature the hero killed carries only its weaknesses
    and resistances (Game._make_corpse), so its studied page never said what
    it shrugs off, refuses or falls to easily, nor its scales, ward or healing:
    a stirge swarm's body did not say a sword hardly touches it, the very
    thing the 3.5.1 Bestiary pass was for. The page reads its kind's own
    definition."""
    corpse = game._make_corpse(_m('stirge_swarm', 3, 3))
    _ident, mech, _lore = _page_texts(game, corpse)
    for _k, text in affinity.bestiary_rows(MONS['stirge_swarm']):
        assert text in mech, (text, mech)
    assert 'Shrugs Off: Slash, Pierce' in mech


@pytest.mark.parametrize('kind', ['troll', 'abaddon_destroyer', 'fafnir_dragon', 'skeleton'])
def test_d1_every_row_of_a_slain_kind_is_on_its_bodys_page(game, kind):
    corpse = game._make_corpse(_m(kind, 3, 3))
    _ident, mech, _lore = _page_texts(game, corpse)
    for _k, text in affinity.bestiary_rows(MONS[kind]):
        assert text in mech, (kind, text)


def test_d1_a_graveyard_skeleton_has_its_numbers_and_its_story(game):
    """A graveyard's laid-out skeleton (food_system.make_corpse) carried no
    health, THAC0, blows or lists: studied, its page said "HP: ?   THAC0: ?"
    and "No lore recorded.", and none of its weaknesses."""
    from food_system import make_corpse
    corpse = make_corpse('skeleton', 3, 3)
    _ident, mech, lore = _page_texts(game, corpse)
    stats = next(t for t in mech if t.startswith('HP: '))
    assert '?' not in stats, stats
    assert f"HP: {MONS['skeleton']['hp']}" in stats
    assert 'Weak To: Blunt, Holy' in mech
    assert any(t.startswith('Hurt Most By') and 'Silver' in t for t in mech)
    assert lore == MONS['skeleton']['lore']


def test_d1_an_old_saves_body_and_an_encounter_person_still_read(game):
    """A body from an old save (only what was copied then) reads its kind; a
    person built in code (no kind in monsters.json) keeps what the body has."""
    from items import Corpse
    old = Corpse('stirge swarm', 'stirge_swarm', 1, 1,
                 monster_def={'hp': 19, 'thac0': 20, 'resistances': ['blunt'],
                              'weaknesses': ['fire', 'cold']})
    _ident, mech, _lore = _page_texts(game, old)
    assert 'HP: 19   THAC0: 20   Speed: 12' in mech
    assert 'Shrugs Off: Slash, Pierce' in mech
    person = Corpse('pilgrim', 'pilgrim_npc_d', 1, 1,
                    monster_def={'hp': 9, 'thac0': 19, 'weaknesses': ['holy']})
    _ident, mech, _lore = _page_texts(game, person)
    assert 'HP: 9   THAC0: 19   Speed: 1' in mech
    assert 'Weak To: Holy' in mech


# ---------------------------------------------------------------------------
# D2. The simulator casts Drain Life as the game does
# ---------------------------------------------------------------------------

def _sim_table(name):
    """A literal table in tools/balance/difficulty_sim.py, read from its source."""
    import ast
    path = os.path.join(ROOT, 'tools', 'balance', 'difficulty_sim.py')
    with open(path, encoding='utf-8') as f:
        tree = ast.parse(f.read())
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and getattr(node.targets[0], 'id', None) == name):
            return ast.literal_eval(node.value)
    raise KeyError(name)


@pytest.mark.parametrize('effect', ['drain_life_spell', 'fire_bolt', 'acid_arrow',
                                    'frost_touch', 'smite', 'magic_missile'])
def test_d2_the_simulators_spell_types_are_the_games(game, monkeypatch, effect):
    """tools/balance/difficulty_sim.ATTACK_SPELLS says what each attack spell
    lands as. Drain Life lands as 'drain' since 3.5.1 (the undead resist it),
    but the simulator still cast it untyped, so its mage hit a ghoul twice as
    hard with it as the game does. (The table is read from the source:
    importing the simulator patches the game's bones for good.)"""
    from spells import LEARNABLE_SPELLS
    attack_spells = _sim_table('ATTACK_SPELLS')
    spell = next(s for s in LEARNABLE_SPELLS.values() if s.get('effect') == effect)
    target = _m('troll', game.player.x + 1, game.player.y)
    target.hp = target.max_hp = 100000
    game.monsters = [target]
    seen = []
    real = Monster.take_damage

    def spy(self, amount, damage_type='physical', *a, **k):
        seen.append(damage_type)
        return real(self, amount, damage_type, *a, **k)
    monkeypatch.setattr(Monster, 'take_damage', spy)
    game._apply_spell_effect(dict(spell), target)
    assert seen, effect
    assert set(seen) == {attack_spells[effect] or 'physical'}, (effect, seen)


# ---------------------------------------------------------------------------
# D3. Gilt Varro is a man's name
# ---------------------------------------------------------------------------

def test_d3_gilt_varro_is_said_with_no_article(game):
    """"The Gilt Varro is slain!", "The Gilt Varro: 1094/1094 HP." (the Wand
    of Probing): a man's name took the article. A 3.5.0 save's Varro is
    mended on the camp's floor."""
    import bococho_encounter as bc
    import enemy_lore
    from monster import the_name
    varro = bc.make_creature('varro', 2, 2, 55)
    assert the_name(varro) == 'Gilt Varro'
    assert enemy_lore.probe_lines(varro)[0].startswith('Gilt Varro: ')
    old = bc.make_creature('varro', 2, 2, 55)
    old.proper_noun = False                       # as a 3.5.0 save holds him
    assert the_name(old) == 'The Gilt Varro'
    game.monsters = [old]
    game._bococho_state()['floor'] = game.dungeon_level
    game._bococho_tick()
    assert the_name(old) == 'Gilt Varro'


# ---------------------------------------------------------------------------
# D4. The Wand of Probing reads one row a line
# ---------------------------------------------------------------------------

def test_d4_the_probe_reads_each_row_on_its_own_line(game):
    """3.5.1 ran every row of a creature together into one message: a
    skeleton's was ten lines in the log, and the log showed it from the
    middle of a word ("Damage): Elven Silver, Ghost Iron..."), the health and
    the weaknesses scrolled away. Each row is its own line now, as on the
    Bestiary page."""
    import copy
    from items import load_items
    skel = _m('skeleton', game.player.x + 1, game.player.y)
    game.monsters = [skel]
    wand = copy.copy(next(w for w in load_items('wand') if getattr(w, 'effect', '') == 'probing'))
    game._wand_override_target = skel
    game._apply_wand_effect(wand)
    game._wand_override_target = None
    rows = [t if t.endswith('.') else t + '.' for _k, t in affinity.bestiary_rows(skel)]
    assert len(rows) >= 4
    for text in rows:
        assert text in game._log, (text, game._log)
    assert game._log[0] == f"The Skeleton: {skel.hp}/{skel.max_hp} HP."


# ---------------------------------------------------------------------------
# D5. The race panel's choices hold their words at a small window
# D6. The two birds' names are never drawn one over the other
# ---------------------------------------------------------------------------

class _BlitLog(pygame.Surface):
    """A screen that remembers where each surface was blitted."""

    def __init__(self, size):
        super().__init__(size)
        self.blits = []

    def blit(self, source, dest, *a, **k):
        r = super().blit(source, dest, *a, **k)
        self.blits.append((source, pygame.Rect(r)))
        return r


def _small_window(game, size):
    import layout
    layout.update(*size)
    game.on_resize(*size)
    game._resize_grace = 0
    game.screen = _BlitLog(size)


@pytest.fixture
def kit_loaded():
    """The UI art kit (assets/ui/) loaded, as in the game; the kit before
    is put back afterwards."""
    import ui_theme
    saved = ui_theme.save_state()
    ui_theme.load()
    try:
        yield
    finally:
        ui_theme.restore_state(saved)


@pytest.mark.parametrize('size', [(1024, 600), (960, 540), (1093, 614), (1280, 720)])
def test_d5_the_race_choices_hold_their_words(game, kit_loaded, monkeypatch, size):
    """In the compact layout (a window under 1280x720) a row shrinks with
    the UI scale but its words never go under 16 px: "Sprint: half again as
    far, then a winded leg" wrapped, and its second line ran out through the
    row's bottom edge (1024x600, 960x540). Each row is as tall as its words."""
    from ui_scale import px as S
    from fantasy_ui import get_font
    import fantasy_ui
    _small_window(game, size)
    game._race_phase = 'choose'
    monkeypatch.setattr(game, '_race', lambda: {'leg': 2, 'legs': 5})
    monkeypatch.setattr(game, '_draw_race_runner_tags', lambda top: None)
    rows = []
    real_row = game._ui_action_row

    def spy(rect, key, label, **k):
        rows.append((pygame.Rect(rect), str(key), label))
        return real_row(rect, key, label, **k)
    monkeypatch.setattr(game, '_ui_action_row', spy)
    game._draw_race_screen()
    assert len(rows) >= 2
    assert fantasy_ui.kit_on()
    font = get_font('body', 16, bold=True)        # _ui_action_row's, with the kit
    for rect, key, label in rows:
        key_w = max(S(40), min(rect.w // 3, font.size(key)[0] + S(18)))
        n = len(game._wrap_text(label, font, rect.w - S(9) - key_w - S(22))[:2])
        need = n * (font.get_height() + S(2)) + 2 * S(6)
        assert need <= rect.h, (size, label, n, need, rect.h)


def test_d6_the_birds_names_do_not_overlap(game, monkeypatch):
    """On a small window the whole oval is small, and the two birds' name
    tags, each set over its bird, were drawn one over the other when the
    birds ran side by side."""
    from types import SimpleNamespace
    from fantasy_ui import get_font
    import bococho_encounter as bc
    _small_window(game, (960, 540))
    r = game.renderer
    T = r.map_tile_size
    hero_bird = SimpleNamespace(x=game.player.x, y=game.player.y)
    rival = SimpleNamespace(x=game.player.x + 1, y=game.player.y)
    monkeypatch.setattr(game, '_race_runner', lambda who: hero_bird if who == 'hero' else rival)
    import layout
    px, py = hero_bird.x, hero_bird.y
    monkeypatch.setattr(r, 'world_to_screen', lambda wx, wy: (layout.MAP_X + 150 + (wx - px) * T,
                                                              120 + (wy - py) * T))
    sx, sy = r.world_to_screen(hero_bird.x, hero_bird.y)
    game.screen.blits.clear()
    game._draw_race_runner_tags(sy + 6 * T)
    font = get_font('body', 16, bold=True)
    widths = {font.size(bc.data()['race'].get('tag_hero', 'Her'))[0],
              font.size(bc.data()['race'].get('rival_name', 'Brassbeak'))[0]}
    tags = [rect for surf, rect in game.screen.blits if surf.get_width() in widths]
    assert len(tags) == 2, tags
    assert not tags[0].colliderect(tags[1]), tags


# ---------------------------------------------------------------------------
# D8. The fight strip's red words can be read
# ---------------------------------------------------------------------------

def _capture_mod():
    import importlib.util
    if 'pq_ui_capture' in sys.modules:
        return sys.modules['pq_ui_capture']
    spec = importlib.util.spec_from_file_location(
        'pq_ui_capture', os.path.join(ROOT, 'tools', 'ui', 'capture.py'))
    mod = importlib.util.module_from_spec(spec)
    sys.modules['pq_ui_capture'] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize('low_hp', [False, True])
def test_d8_the_fight_strips_danger_words_reach_their_contrast(low_hp):
    """The fight strip wrote "Shrugs Off (Quarter): Pierce / Slash", "Resisted
    (Half): ...", and a target's or the hero's health under a quarter, in
    FP.DANGER_TEXT (blood red): 2.8:1 on the strip, under the 3:1 floor for
    large text and far under 4.5:1 (the UI gate found it once a capture
    scene fought a studied stirge swarm). They take the light danger red."""
    cap = _capture_mod()
    base = next(s for s in cap.SCENES if s.name == 'quiz_chain_strip_shrugs')

    def setup(g):
        base.setup(g)
        if low_hp:
            g.combat_target.hp = 1
            g.player.hp = 1
    sc = cap.Scene('d8_strip', 'Quiz', 'test', setup, 'game', 'quiz')
    with cap.harness():
        surf, _state = cap.render_scene(sc, (1280, 720), measure_contrast=True)
    blits, infos, _panels = surf.top_layer()
    seen = {}
    for (rect, text), info in zip(blits, infos):
        if text.startswith('Shrugs Off') or text.endswith(' HP'):
            seen[text] = info['contrast']
    assert any(t.startswith('Shrugs Off: ') for t in seen), seen
    for text, c in seen.items():
        assert c is not None and c >= 4.5, (text, c)


# ---------------------------------------------------------------------------
# D9. (Test helper) The Black Knight tests reach him through a crowd
# ---------------------------------------------------------------------------

def test_d9_the_knight_tests_reach_him_with_both_bridge_ends_held():
    """test_black_knight._beside skipped a tile another monster held, then
    sent every other monster away: on 3.5.1's fuller floors both ends of the
    bridge were sometimes held, and a full run failed with "list index out of
    range". The others go first now."""
    import test_black_knight as tbk
    g = tbk._game('__test_bugbash_351_d_knight__')
    k = tbk._on_his_floor(g)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x, y = k.x + dx, k.y + dy
        if g.dungeon.is_walkable(x, y):
            g.monsters.append(_m('goblin', x, y))
    dx, dy = tbk._beside(g, k)
    assert (g.player.x + dx, g.player.y + dy) == (k.x, k.y)
    assert g.monsters == [k]
