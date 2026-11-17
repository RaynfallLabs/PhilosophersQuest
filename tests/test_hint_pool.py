"""The Recall Lore hint pool (data/hints.json), redone 2026-11-14.

Brandon: "We need to entirely refresh Recall Lore, there's so much in here to
understand now. Redo the hint list, follow all my rules about not directly
giving something away." And: "Recall lore is a Trivia quiz that gives a
random hint, doesn't do anything with monsters you can see and is not
targeted."

His rules for a hint (RECALL_LORE_HINTS_2026_11_14.md has the whole reading):
point at the source (a myth, a story, nature or craft), never the mechanic;
never a number, a percentage, a key, a menu name or the rule outright; never
demystify a secret (the secret builds, the cow, the duck past his own two
lines, the carrot, the unicorn's secret, the 4th-wall tricks); Fenrir's
scraps get one oblique tier-4 or tier-5 hint at most. Only what a machine can
see is pinned here; the rest is the review file and Brandon's read.
"""
import json
import os
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

with open(os.path.join(ROOT, 'data', 'hints.json'), encoding='utf-8') as _f:
    POOL = json.load(_f)
ALL = [(t, h) for t, lst in POOL.items() for h in lst]

# The pool before the redo had 76 / 85 / 86 / 84 / 47; "keep about the same
# count per tier". Its longest hint was 217 characters: none may be longer.
OLD_COUNTS = {'1': 76, '2': 85, '3': 86, '4': 84, '5': 47}
LONGEST = 217


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------
def test_the_pool_is_five_tiers_of_sentences():
    assert sorted(POOL) == ['1', '2', '3', '4', '5']
    for tier, lst in POOL.items():
        assert isinstance(lst, list) and lst, tier
        for h in lst:
            assert isinstance(h, str) and h.strip() == h and h, (tier, h)
    texts = [h for _t, h in ALL]
    assert len(texts) == len(set(texts)), 'a hint appears twice'


def test_each_tier_keeps_about_its_old_count():
    for tier, n in OLD_COUNTS.items():
        assert abs(len(POOL[tier]) - n) <= 10, (tier, len(POOL[tier]), n)
    assert 360 <= len(ALL) <= 400


def test_no_hint_is_longer_than_the_old_longest():
    for tier, h in ALL:
        assert len(h) <= LONGEST, (tier, len(h), h)


def test_every_hint_is_a_proper_sentence():
    for tier, h in ALL:
        assert h[0].isupper() or h[0] == "'", h
        assert h.endswith(('.', '!', '?', "'", '"')) or h.split()[-1].isupper(), h
        assert not re.search('[–—]', h), h                     # no long dashes
        assert '  ' not in h, h


# ---------------------------------------------------------------------------
# The giveaways a machine can see
# ---------------------------------------------------------------------------
LABELS_ANY_CASE = ('Kit Sense', 'Known by Hand', 'Loadout', 'Burdened', 'Overloaded',
                   'Recall Lore', 'Bestiary', 'Encyclopedia', 'Lore Hints', 'Rededicat',
                   'Forewarned', 'Field Notes', 'trade-in', 'karma')
LABELS_AS_WRITTEN = ('Readied', 'At Your Back', 'Trade In', 'Kit', 'Press', 'Guard')


@pytest.mark.parametrize('tier,hint', ALL)
def test_no_hint_gives_a_number_a_key_or_a_menu_name(tier, hint):
    assert not re.search(r'\d', hint), 'a digit'
    assert '%' not in hint
    assert not re.search(r'\b(press|presses|pressed|pressing)\b', hint, re.I), 'press'
    assert not re.search(r'\b(Shift|Ctrl|Alt|Tab|Esc|Enter|Space)\b', hint), 'a key'
    assert not re.search(r'\bF\d', hint) and not re.search(r'\([A-Z]\)|\+[A-Z]\b', hint), 'a key'
    for lab in LABELS_ANY_CASE:
        assert lab.lower() not in hint.lower(), lab
    for lab in LABELS_AS_WRITTEN:
        assert not re.search(r'\b' + lab + r'\b', hint), lab


@pytest.mark.parametrize('tier,hint', ALL)
def test_no_hint_touches_the_cow_or_the_scraps_too_early(tier, hint):
    assert not re.search(r'\bcows?\b', hint, re.I), 'the cow: no hint at all'
    if re.search(r'scrap', hint, re.I) or 'Fenrir' in hint:
        assert tier in ('4', '5'), 'scraps or Fenrir outside tiers 4 and 5'


def test_the_secrets_stay_secret():
    """The old giveaways are gone: the door that knows a great name, the hero's
    own power in a small menu, the carrot, the cow, the unicorn coming along,
    the family's gold-trimmed sphere, the hidden word's gifts."""
    low = ' '.join(h for _t, h in ALL).lower()
    for phrase in ('under his name', 'the door', 'famous visitors', 'whole name',
                   'small menu', "hero's own power", 'carrot', 'no cow level',
                   'she comes along', 'trimmed with gold', 'it still works',
                   'thinking machines', 'unusual', 'come to heel', 'keep counting',
                   'it can count'):
        assert phrase not in low, phrase


# ---------------------------------------------------------------------------
# Every new or changed system is taught somewhere
# ---------------------------------------------------------------------------
TAUGHT = {
    'donning time': r'buckle on',
    'a kind once worn goes on again': r'remember its buckles|hands that know every buckle',
    'the weapon at your back': r'at your back',
    'saved kits': r'harness for the tourney|one harness for fire',
    'armour: edges and points': r'parts under a point',
    'armour: elements': r'carries the lightning|forged against the frost',
    'Dexterity in light armour': r'tumble in a breastplate',
    'noise': r'hears him coming|ring or clank',
    'casting in metal': r'true-silver.*orichalcum',
    'weight': r'full pack|pack mule|heavy pack',
    'felt lines before study, named after': r'teaches why|blow that is understood',
    'what a kind shrugs off': r'only tickle',
    'studying corpses': r'corpse',
    'family tiers': r'first you know a family|know enough of a family',
    'the Wand of Probing teaches a kind': r'wand that reads|can still be read|be read before',
    'the best tool for a family': r'reaches for its old trick|hand has already chosen',
    'coatings': r'silver dust|fire oil|viper venom',
    'thrown flasks': r'greek fire|aqua regia|siloam|medea|alkahest',
    'Press and Guard': r'lunges|careful guard',
    "the two-hander's parry": r'both hands turns blows|worse it parries',
    'mirror and gaze': r'mirror',
    'wax and voice': r'wax',
    'cold iron and glamour': r'cold iron',
    "traders' stock for what lies below": r'set out for it|oddly particular',
    'reforging': r'sword into a mace',
    'silvering and cold-iron inlay': r'silver worked into a blade',
    'linings': r'line your cloak|line a cloak',
    'special orders': r'make what he does not have|order the armour',
    'a smith works only a blade you can name': r'metal he cannot name',
    'the trade-in': r'just made a sale|sells and never buys',
    "the altar's Rededication": r'jacob',
    'meditation and Intelligence': r'stillness refills|quiet of a floor|mind refills',
    'the quests that teach a gate boss': r'how the beast at the end|not making conversation',
    "the unicorn's trust": r'unicorn',
    'escorts': r'the ones you lead',
    'oaths': r'promise',
    'the Emberpup': r'fire lizard',
    'Old Nickel': r'old nickel',
    # The horns of legend's paths (Brandon, 2026-11-16), each at its depth's
    # tier and pointing at its source: the ballad, the legend, the Eddas,
    # the Song of Roland.
    "Robin Hood's bridge": r'quarterstaff on a narrow bridge',
    'the sleepers under the hill': r'never blew the bugle-horn',
    "Heimdall's watch": r'hears the grass grow',
    "the Olifant's lesson": r'call for help early',
    # Merlin's stone (the path to the Staff of Emrys, floors 6-11): Malory's
    # stone a hundred men could not lift, and Geoffrey's art over strength.
    "Merlin's stone": r'art, not by strength',
    # Brandon, 2026-11-16: people are searched, never harvested; a special
    # find has a dish of its own.
    "a person's body is searched": r'what a fallen man carried',
    'a rare find cooks into its own dish': r'more in a pot than in a pocket',
}


def test_each_horn_path_hint_sits_at_its_depths_tier():
    """Tier = depth / 20: the bridge (floors 12-18) at 1, the sleepers
    (45-55) at 3, Heimdall (70-78) at 4, Roland (86-92) at 5."""
    for tier, pat in (('1', TAUGHT["Robin Hood's bridge"]),
                      ('1', TAUGHT["Merlin's stone"]),
                      ('3', TAUGHT['the sleepers under the hill']),
                      ('4', TAUGHT["Heimdall's watch"]),
                      ('5', TAUGHT["the Olifant's lesson"])):
        assert any(re.search(pat, h, re.I) for h in POOL[tier]), (tier, pat)


@pytest.mark.parametrize('system', sorted(TAUGHT))
def test_each_new_system_has_a_hint(system):
    pat = re.compile(TAUGHT[system], re.I)
    assert any(pat.search(h) for _t, h in ALL), system


def test_the_emberpup_and_old_nickel_get_story_not_steps():
    for _t, h in ALL:
        low = h.lower()
        if 'fire lizard' in low or 'old nickel' in low or 'emberpup' in low:
            for step in ('leave him food', 'come back', 'give', 'feed', 'three', 'twice'):
                assert step not in low, (step, h)


# ---------------------------------------------------------------------------
# Where the pool is read: the Recall Lore card, the trap's chain 5, the
# Lore Hints journal
# ---------------------------------------------------------------------------
SIZES = [(1093, 614), (1280, 720), (1080, 1920), (3440, 1440)]


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import layout
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    screen = pygame.display.set_mode((1280, 720))
    layout.update(1280, 720)
    g = Game(screen, player_name='__test_hint_pool__')
    g.on_resize(1280, 720)
    g._resize_grace = 0
    g.monsters = []
    g.state = STATE_PLAYER
    return g


def _resize(g, w, h):
    import layout
    g.screen = pygame.display.set_mode((w, h))
    layout.update(w, h)
    g.on_resize(w, h)
    g._resize_grace = 0


@pytest.mark.parametrize('size', SIZES)
def test_every_hint_fits_the_recall_lore_card(game, size):
    """The card wraps the hint into its text box and silently drops a line
    that does not fit (_ui_wrap_text): every hint, at every gate size, must
    fit whole."""
    import game_render
    from game_states import STATE_HINT
    _resize(game, *size)
    seen = {}
    real = game._ui_wrap_text

    def spy(text, font, color, rect, *, line_gap=3, max_lines=None):
        y = real(text, font, color, rect, line_gap=line_gap, max_lines=max_lines)
        seen[text] = (font, rect, line_gap, y)
        return y
    game._ui_wrap_text = spy
    for tier, hint in ALL:
        game.state = STATE_HINT
        game._lore_hint_text = hint
        game._lore_hint_chain = int(tier)
        game._draw_recall_lore_card()
        font, rect, gap, y = seen[hint]
        lines = game._wrap_text(hint, font, rect.w)
        whole = rect.y + len(lines) * (font.get_height() + game_render.S(gap))
        assert y == whole, (size, tier, len(lines), hint)


def test_recall_lore_draws_from_the_chains_tier(game):
    for chain in (1, 2, 3, 4, 5):
        game._resolve_recall_lore(chain)
        assert game._lore_hint_text in POOL[str(chain)]
        assert game._lore_hint_chain == chain
    n = len(game._recalled_hints)
    assert len(set(game._recalled_hints)) == n


def test_the_trap_hint_joins_the_journal_once(game, monkeypatch):
    """A chain-5 disarm draws from every tier (main._random_hint_for_disarm)
    and used to append the hint to the journal again each time it came up."""
    hint = POOL['3'][0]
    monkeypatch.setattr(game, '_random_hint_for_disarm', lambda: hint)
    game._recalled_hints = []
    for _ in range(2):
        pos = (game.player.x + 1, game.player.y)
        game.dungeon.traps[pos] = {'type': 'bear_trap', 'damage': '1d4',
                                   'damage_type': 'physical', 'message': '!', 'revealed': True}
        game._resolve_trap_disarm(pos, 'bear trap', 5)
    assert game._recalled_hints == [hint]


def test_the_journal_shows_a_hint_in_its_own_case_and_whole(game):
    """The Lore Hints page title-cased every hint into its heading ("Wisdom
    Is Time. Every Point of It..."). Now it heads the page plainly and gives
    the hint as written."""
    hint = max((h for _t, h in ALL), key=len)
    game._recalled_hints = [hint]
    game._encyclopedia_load_entries('lore_hints')
    entry = game.encyclopedia_entries[0]
    lines = [str(t[0]) for t in game._encyclopedia_article_lines('lore_hints', entry)]
    assert lines[0] == 'Lore Hint'
    assert hint in lines
    game.encyclopedia_category = 'lore_hints'
    game.state = 'encyclopedia'
    drawn = []
    real = game._ui_wrap_text

    def spy(text, *a, **k):
        drawn.append(str(text))
        return real(text, *a, **k)
    game._ui_wrap_text = spy
    game._draw_encyclopedia_browser()
    assert hint in drawn                                                 # the list row, own case
