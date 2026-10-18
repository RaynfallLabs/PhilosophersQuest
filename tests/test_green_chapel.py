"""Brandon's encounter decisions of 2026-10-18 (ENCOUNTER_STORIES_DRAFT.md
Part J11, DEEDS_KARMA_DESIGN.md section 11.16):

1. Oswin: urging him to go back and face the families of Thale and the
   king's court, and to tell the truth about Bishop Ranulf, pays +1. It is a
   stance (moral_vision section 1), not 'owning': owning is the hero's own
   confession of his own recorded wrong, and an NPC's confession pays no
   owning karma (J10). The point asks the hero to say why (one passed
   question); Oswin goes back either way. "Fight on" stays at 0.
2. Creon's edict is an unjust authority: informing is the one submit (-1
   betray), nothing rewards submitting, resisting never costs.
3. Socrates stays contested and the "I lost it" admissions stay at 0.
4. The Green Chapel (C24): Gawain's own owning-up story, for a hero who took
   Lady Bertilak's girdle and lied to her husband about it. The Knight's three
   swings, the nick that shows he knows, and the choice: own it (+1 owning, the
   girdle given back), bluster or say nothing (0), draw on him or walk away
   (0: resisting his game is never penalised).

Data tests plus behaviour tests on a real headless Game. The chapel is a
floor-67-to-73 callback after a medium-stakes story, so it is proven here,
not by play-test (CLAUDE.md).
"""
import copy
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402

import deeds  # noqa: E402
import encounter_schema as ES  # noqa: E402
from tools.encounters import validate as V  # noqa: E402

ALL = V.load_all()
BY_TAG = {e['tag']: e for _s, e in ALL}
TAG = 'flv_green_chapel'
GIRDLE = 'green_girdle'
BLOW = 'told.green_chapel_blow'

KNEEL = 'Kneel, and bare your neck'
FIRST = 'Tell him about the girdle before he swings'
FIGHT = 'Refuse his game, and draw on him'
LEAVE = 'Walk away from the chapel'
TRUTH = 'Tell him the truth about the girdle, and give it back'
BLUSTER = "Call it a fair blow, and say you're quits"
SILENT = 'Say nothing, and go'
OSWIN_BACK = '"Go back up. Face the families of Thale, and tell the king\'s court about Ranulf."'
OSWIN_FIGHT = '"Fight on down here. Spend it against what lies below."'

with open(os.path.join(ROOT, 'data', 'gate_lines.json'), encoding='utf-8') as _f:
    GATE_ROWS = json.load(_f)['gate']['lines']


def _opt(tag, label):
    return next(o for o in BY_TAG[tag]['options'] if o['label'] == label)


def _ctx(deed_ids=(), items=(), worn=()):
    reg = deeds.new_register()
    for d in deed_ids:
        deeds.record(reg, d, floor=66, block=7, turn=0, source='test')
    return {'reg': reg, 'karma': 0, 'stats': {}, 'floor': 70, 'deepest': 70,
            'items': set(items) | set(worn), 'worn': set(worn)}


def _labels(ctx, used=()):
    return [o['label'] for _i, o in ES.visible_options(BY_TAG[TAG], ctx, used)]


# ================================================================== data: Oswin

def test_oswin_going_back_pays_a_stance_when_the_hero_can_say_why():
    e = BY_TAG['fallen_paladin']
    back = _opt('fallen_paladin', OSWIN_BACK)
    assert not e.get('contested')                       # no longer contested on this option
    assert e['stance'] == '1' and 'Steel-man' in e['stance_note']
    assert back['side'] == 'right' and back['submit'] is True
    assert e['authority']['just'] is True               # an honest court
    assert ES.is_quiz(back)                             # the visible price: saying why
    assert (back['pass']['karma'], back['pass']['karma_kind']) == (1, 'stance')
    assert int(back['fail'].get('karma', 0) or 0) == 0  # never a loss
    for b in ('pass', 'fail'):                          # he goes back either way
        assert 'told.oswin_go_back' in back[b]['deeds']
        assert back[b]['schedule'][0]['encounter'] == 'flv_paladin_end'
        assert 'Ranulf' in back[b]['outcome']
    # Not 'owning': that is the hero's own wrong; an NPC's confession pays none.
    assert all(b.get('karma_kind') != 'owning' for o in e['options']
               for b in ES.option_branches(o))


def test_oswin_fighting_on_stays_at_nothing_and_only_robbing_him_costs():
    fight = _opt('fallen_paladin', OSWIN_FIGHT)
    assert ES.max_karma(fight) == 0 and not fight.get('side')
    rob = _opt('fallen_paladin', "Take the armour he offered, and the pack he didn't")
    assert rob['side'] == 'wrong' and rob['villain'] and rob['karma'] == -1


def test_the_block_budget_stays_two_to_three():
    for b, r in V.opportunity_budget().items():
        assert 2.0 <= r['expected'] <= 3.0, (b, r)
    assert V.opportunity_budget()[9]['anchors'] == (3, 3)      # Oswin now has a +1 path


# ================================================================== data: Antigone

def test_creons_edict_is_unjust_and_nothing_rewards_submitting():
    e = BY_TAG['flv_antigone']
    assert e['authority']['just'] is False and 'Creon' in e['authority']['who']
    submits = [o for o in e['options'] if o.get('submit')]
    assert [o['label'] for o in submits] == ["Tell Creon's men where she is"]
    assert submits[0]['karma'] == -1 and submits[0]['karma_kind'] == 'betray'
    for o in e['options']:
        if not o.get('submit'):                          # resisting it never costs
            assert min(int(b.get('karma', 0) or 0) for b in ES.option_branches(o)) == 0
    assert e['contested']                                # the defensible answers stay equal


# ================================================================== data: decision 3

LOST_IT = {('flv_seventh_lamp', '"I lost Wat\'s oil."'),
           ('flv_reliquary_chapel', '"I lost him on the way."'),
           ('flv_squire_tobyn', "Give him Ser Brennan's message, without the sword"),
           ('flv_rolands_horn_gate', '"I lost Roland\'s horn."')}


def test_i_lost_it_admissions_stay_at_nothing():
    for tag, label in LOST_IT:
        o = _opt(tag, label)
        assert all(int(b.get('karma', 0) or 0) == 0 and b.get('karma_kind') != 'owning'
                   for b in ES.option_branches(o)), (tag, label)


def test_socrates_stays_contested():
    e = BY_TAG['flv_socrates_cell']
    assert e['contested'] and e['authority']['just'] is False
    assert {ES.max_karma(o) for o in e['options']} == {0}


# ================================================================== data: the chapel

def test_the_chapel_is_a_high_stakes_callback_after_the_girdle():
    e, s20 = BY_TAG[TAG], BY_TAG['flv_green_girdle']
    assert e['callback_only'] and e['stakes'] == 'high' and e['role'] == 'story'
    assert e['band'] == [67, 73]
    # Inside the floors the girdle's callback can reach, and below the girdle.
    keep = _opt('flv_green_girdle', 'Take it and keep it secret')
    (cb,) = keep['schedule']
    lo, hi = s20['band'][0] + cb['after_floors'][0], s20['band'][1] + cb['after_floors'][1]
    assert lo <= e['band'][0] and e['band'][1] <= hi and e['band'][0] > s20['band'][0]
    # Before the Green Knight's own peak floor (74), so the chapel comes first.
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        gk = json.load(f)['green_knight']
    assert e['band'][1] < gk['peak_floor']
    assert e['sprite_id'] == 'green_knight' and e['person'] == {'id': 'bertilak', 'name': 'Sir Bertilak'}
    assert e['authority']['just'] is True               # his judgement is honest: the point of the poem


def test_only_the_lie_schedules_the_chapel():
    keep = _opt('flv_green_girdle', 'Take it and keep it secret')
    assert keep['schedule'][0]['encounter'] == TAG and keep['schedule'][0]['lost_line']
    assert keep['thread']['id'] == 'green_chapel' and keep['thread']['hint']
    assert 'wrong.kept_girdle' in keep['deeds']
    for label in ('Take it, and give it to your host at the door, as agreed', 'Refuse it'):
        o = _opt('flv_green_girdle', label)
        assert not o.get('schedule'), label
    scheduled_by = {e['tag'] for _s, e in ALL for o in e['options']
                    for b in ES.option_branches(o) for c in b.get('schedule') or ()
                    if c.get('encounter') == TAG}
    assert scheduled_by == {'flv_green_girdle'}


def test_the_chapel_needs_the_lie_and_the_girdle():
    e = BY_TAG[TAG]
    assert ES.encounter_allowed(e, _ctx(['wrong.kept_girdle'], [GIRDLE]))
    assert ES.encounter_allowed(e, _ctx(['wrong.kept_girdle'], worn=[GIRDLE]))
    assert not ES.encounter_allowed(e, _ctx(['wrong.kept_girdle']))             # sold or lost it
    assert not ES.encounter_allowed(e, _ctx(['forgo.green_girdle'], [GIRDLE]))  # gave it back
    assert not ES.encounter_allowed(e, _ctx([], [GIRDLE]))                      # won it off his corpse
    assert not ES.encounter_allowed(e, _ctx(['wrong.kept_girdle', 'slew.green_knight'], [GIRDLE]))
    assert not ES.encounter_allowed(
        e, _ctx(['wrong.kept_girdle', 'flag.green_girdle_turned'], [GIRDLE]))


def test_karma_follows_owning_up_and_resisting_is_never_penalised():
    e = BY_TAG[TAG]
    for o in e['options']:
        brs = ES.option_branches(o)
        assert min(int(b.get('karma', 0) or 0) for b in brs) >= 0, o['label']   # no loss anywhere
        if o['label'] in (FIRST, TRUTH):
            assert (o['karma'], o['karma_kind']) == (1, 'owning')
            assert o['cost'] == {'type': 'triggered_item_id', 'item_id': GIRDLE}  # the girdle itself
            assert o['requires']['items_any'] == [GIRDLE]
            assert 'told.owned_up_to_green_knight' in o['deeds']
        else:
            assert ES.max_karma(o) == 0, o['label']
    assert _opt(TAG, KNEEL)['cost'] == {'type': 'hp_pct', 'amount': 15}         # the nick
    assert _opt(TAG, FIGHT)['fight'] == {'monster_id': 'green_knight'}
    assert V._is_free(_opt(TAG, LEAVE))


def test_the_scene_steps_from_the_swings_to_the_choice():
    worn = _ctx(['wrong.kept_girdle'], worn=[GIRDLE])
    assert _labels(worn) == [KNEEL, FIRST, FIGHT, LEAVE]
    # After kneeling (that option is used up, as the engine records it).
    after = _labels(_ctx(['wrong.kept_girdle', BLOW], worn=[GIRDLE]), used=[0])
    assert after == [TRUTH, BLUSTER, SILENT]
    # Put down before he was bumped: no confession can be paid for.
    assert _labels(_ctx(['wrong.kept_girdle'])) == [KNEEL, FIGHT, LEAVE]
    assert _labels(_ctx(['wrong.kept_girdle', BLOW]), used=[0]) == [BLUSTER, SILENT]
    e = BY_TAG[TAG]
    assert 'his eyes stop at your waist' in ES.resolve_text(e, worn)
    assert 'waist' not in ES.resolve_text(e, _ctx(['wrong.kept_girdle'], [GIRDLE]))
    kneel = _opt(TAG, KNEEL)
    assert kneel['then'] == 'options' and BLOW in kneel['deeds'] and kneel['submit']
    assert 'Bertilak' in kneel['outcome'] and 'called nothing' in kneel['outcome']


def test_every_ending_has_a_journal_line_a_road_hint_and_a_gate_line():
    e = BY_TAG[TAG]
    assert e['chronicle_meet'] and not V._chron_lint(e['chronicle_meet'])
    endings = {FIRST: ['told.owned_up_to_green_knight', 'flag.green_chapel_first'],
               TRUTH: ['told.owned_up_to_green_knight'],
               BLUSTER: ['told.green_chapel_blustered'], SILENT: ['told.green_chapel_silent'],
               FIGHT: ['told.green_chapel_fought'], LEAVE: ['told.green_chapel_left']}
    lines = set()
    for label, ids in endings.items():
        o = _opt(TAG, label)
        assert set(ids) <= set(o['deeds']), label
        assert o['chronicle'] and not V._chron_lint(o['chronicle']), label
        assert o['road']['hint'] and not V._road_lint(o['road'], label), label
        c = _ctx(['wrong.kept_girdle', BLOW] + list(o['deeds']))
        mine = [r for r in GATE_ROWS if r['person'] == 'bertilak' and deeds.check(r['when'], c)]
        assert mine, label
        lines.add(mine[0]['line'])
        assert mine[0]['name'] == 'Sir Bertilak'
    assert len(lines) == len(endings)                   # every ending its own line


def test_the_validator_lists_both_confessions():
    assert V.validate_all() == []
    own = {(t, lbl) for t, lbl, _w, _b, _cb in V.owning_report() if t == TAG}
    assert own == {(TAG, FIRST), (TAG, TRUTH)}


# ================================================================== behaviour

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(seed=71, name='__test_green_chapel__'):
    import items
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(seed)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.state = STATE_PLAYER
    g._npc_encounter_levels = {}
    g._flavor_encounter_levels = {}
    return g


def _def(tag):
    import economy
    from game_road import _encounter_by_tag
    _src, e = _encounter_by_tag(tag)
    return economy.price_encounter(copy.deepcopy(e))


def _go(g, floor):
    g._change_level(floor, enter_from_top=floor >= g.dungeon_level, via='stairs')
    g.monsters[:] = [m for m in g.monsters
                     if getattr(m, '_flavor_encounter_tag', None) or getattr(m, '_npc_encounter_tag', None)]
    g.dungeon.traps = {}
    from game_states import STATE_PLAYER
    g.state = STATE_PLAYER


def _npc(g, tag):
    return next((m for m in g.monsters if m.alive and tag in (
        getattr(m, '_flavor_encounter_tag', None), getattr(m, '_npc_encounter_tag', None))), None)


def _meet(g, floor, tag, flavor=True):
    (g._flavor_encounter_levels if flavor else g._npc_encounter_levels)[floor] = _def(tag)
    _go(g, floor)
    npc = _npc(g, tag)
    assert npc is not None, tag
    return npc


def _open(g, npc):
    from game_states import STATE_NPC_ENCOUNTER
    if getattr(npc, '_flavor_encounter_tag', None):
        assert g._start_flavor_encounter(npc)
    else:
        assert g._start_npc_encounter(npc)
    assert g.state == STATE_NPC_ENCOUNTER
    if g._npc_encounter_phase == 'text':
        g._npc_encounter_input(pygame.K_RETURN)


def _pick(g, label):
    """On the options page, pick the option shown with this label and land on
    its outcome page (any item pick takes the first)."""
    labels = [o['label'] for _i, o in g._npc_visible_options()]
    assert label in labels, labels
    g._npc_encounter_input(pygame.K_1 + labels.index(label))
    if g._npc_encounter_phase == 'select_item':
        g._npc_encounter_input(pygame.K_a)
    assert g._npc_encounter_phase == 'outcome', g._npc_encounter_phase
    return labels


def _continue(g):
    g._npc_encounter_input(pygame.K_RETURN)


def _hero_who_lied(g, *, worn=True):
    """As the Green Girdle's secret leaves him: the deed, the open thread, the
    girdle worn (or carried)."""
    from items import make_item_by_id
    reg = deeds.ensure_register(g)
    deeds.record(reg, 'wrong.kept_girdle', floor=66, block=7, turn=0, source='flv_green_girdle')
    keep = _opt('flv_green_girdle', 'Take it and keep it secret')
    deeds.open_thread(reg, 'green_chapel', hint=keep['thread']['hint'], floor=66)
    girdle = make_item_by_id('armor', GIRDLE)
    if worn:
        g.player.armor_slots[4] = girdle                # legs
    else:
        g.player.inventory.append(girdle)
    return girdle


def _holds_girdle(g):
    return GIRDLE in g._deed_ctx()['items']


def _pending(g):
    return [p for p in g._deeds['pending'] if p['kind'] == 'encounter'
            and p.get('source') != 'engine:run_start']


def _texts(g):
    return [e.get('text', '') if isinstance(e, dict) else str(e) for e in g._chronicle]


def test_keeping_the_girdle_secret_sends_the_hero_to_the_chapel():
    g = _game()
    lady = _meet(g, 66, 'flv_green_girdle')
    _open(g, lady)
    _pick(g, 'Take it and keep it secret')
    _continue(g)
    assert _holds_girdle(g) and deeds.has(g._deeds, 'wrong.kept_girdle')
    (cb,) = _pending(g)
    assert cb['spec']['encounter'] == TAG and 68 <= cb['target'] <= 72
    assert g._deeds['threads']['green_chapel']['status'] == 'open'
    # On its floor the Green Knight stands at his chapel, in his own art.
    _go(g, cb['target'])
    knight = _npc(g, TAG)
    assert knight is not None and knight.kind == 'green_knight'
    assert g.renderer._get_sprite(getattr(knight, 'sprite_id', None) or knight.kind) is not None


def test_an_honest_guest_never_meets_the_chapel():
    for label in ('Take it, and give it to your host at the door, as agreed', 'Refuse it'):
        g = _game(name='__test_green_chapel_honest__')
        lady = _meet(g, 66, 'flv_green_girdle')
        _open(g, lady)
        _pick(g, label)
        _continue(g)
        assert not _pending(g), label


def test_the_chapel_is_lost_if_the_girdle_is_gone_by_then():
    g = _game(name='__test_green_chapel_sold__')
    lady = _meet(g, 66, 'flv_green_girdle')
    _open(g, lady)
    _pick(g, 'Take it and keep it secret')
    _continue(g)
    (cb,) = _pending(g)
    g.player.inventory[:] = [i for i in g.player.inventory if getattr(i, 'id', '') != GIRDLE]
    _go(g, cb['target'])
    assert _npc(g, TAG) is None
    assert deeds.has(g._deeds, 'flag.thread_lost.flv_green_chapel')
    assert g._deeds['threads']['green_chapel']['status'] != 'open'
    assert any('never did find the Green Chapel' in t for t in _texts(g))


def test_kneel_take_the_nick_then_own_it_with_the_girdle_worn():
    import karma
    g = _game(name='__test_green_chapel_truth__')
    g.player.hp = g.player.max_hp = 200
    _hero_who_lied(g, worn=True)
    k0 = g.karma
    knight = _meet(g, 70, TAG)
    _open(g, knight)
    assert 'his eyes stop at your waist' in g._npc_encounter_text
    assert g._deeds['people']['bertilak']['known'] is False       # "The Green Knight" until named
    labels = _pick(g, KNEEL)
    assert labels == [KNEEL, FIRST, FIGHT, LEAVE]
    assert g.player.hp == 200 - 30                                # the nick: a sixth-ish of it
    assert 'a nick' in g._npc_outcome_text and g.karma == k0
    _continue(g)                                                  # back to the choice
    assert g._npc_encounter_phase == 'options'
    labels = _pick(g, TRUTH)
    assert labels == [TRUTH, BLUSTER, SILENT]
    assert not _holds_girdle(g) and g.player.armor_slots[4] is None   # handed over from the body
    assert g.karma == k0 + 1 and karma.gate_enabled()
    led = [e for e in g._deeds['karma']['ledger'] if e['kind'] == 'owning']
    assert len(led) == 1 and led[0]['applied'] == 1
    assert deeds.count(g._deeds, tag='virtue:owned') == 1
    assert g.player.has_effect('blessed')
    _continue(g)
    from game_states import STATE_PLAYER
    assert g.state == STATE_PLAYER
    # People: named now; Journal: both steps, filed under the girdle.
    row = g._deeds['people']['bertilak']
    assert row['known'] is True and row['name'] == 'Sir Bertilak'
    texts = _texts(g)
    assert any('Knelt at the Green Chapel' in t for t in texts)
    assert any('gave it back' in t and 'clean' in t for t in texts)
    assert g._deeds['threads']['green_chapel']['status'] != 'open'
    # The Green Knight has had his blow: he never comes again as a mini-boss.
    assert 'green_knight' in g.level_mgr._placed_mini_bosses
    # And the Gate tells his line.
    rows = [r for r in GATE_ROWS if r['person'] == 'bertilak' and deeds.check(r['when'], g._deed_ctx())]
    assert rows and 'blood running into your collar' in rows[0]['line']


def test_owning_up_before_the_axe_costs_no_nick():
    g = _game(name='__test_green_chapel_first__')
    g.player.hp = g.player.max_hp = 200
    _hero_who_lied(g, worn=False)
    k0 = g.karma
    knight = _meet(g, 70, TAG)
    _open(g, knight)
    _pick(g, FIRST)
    assert g.player.hp == 200 and not _holds_girdle(g)
    assert g.karma == k0 + 1 and deeds.has(g._deeds, 'flag.green_chapel_first')
    assert 'You said it first' in g._npc_outcome_text
    _continue(g)
    assert 'green_knight' in g.level_mgr._placed_mini_bosses
    rows = [r for r in GATE_ROWS if r['person'] == 'bertilak' and deeds.check(r['when'], g._deed_ctx())]
    assert 'before he had even lifted the axe' in rows[0]['line']


def test_bluster_or_silence_keeps_the_girdle_and_pays_nothing():
    for label, deed in ((BLUSTER, 'told.green_chapel_blustered'),
                        (SILENT, 'told.green_chapel_silent')):
        g = _game(name='__test_green_chapel_quiet__')
        g.player.hp = g.player.max_hp = 200
        _hero_who_lied(g)
        k0 = g.karma
        knight = _meet(g, 70, TAG)
        _open(g, knight)
        _pick(g, KNEEL)
        _continue(g)
        _pick(g, label)
        _continue(g)
        assert _holds_girdle(g) and g.karma == k0 and deeds.has(g._deeds, deed), label
        assert deeds.count(g._deeds, tag='virtue:owned') == 0
        assert 'green_knight' in g.level_mgr._placed_mini_bosses


def test_walking_away_pays_nothing_and_leaves_him_free_to_come():
    g = _game(name='__test_green_chapel_leave__')
    g.player.hp = g.player.max_hp = 200
    _hero_who_lied(g)
    k0 = g.karma
    knight = _meet(g, 70, TAG)
    _open(g, knight)
    _pick(g, LEAVE)
    _continue(g)
    assert g.karma == k0 and g.player.hp == 200 and _holds_girdle(g)
    assert 'green_knight' not in g.level_mgr._placed_mini_bosses
    assert deeds.has(g._deeds, 'told.green_chapel_left')


def test_drawing_on_him_calls_up_the_green_knight_and_the_girdle_answers():
    g = _game(name='__test_green_chapel_fight__')
    g.player.hp = g.player.max_hp = 200
    _hero_who_lied(g, worn=True)
    k0 = g.karma
    knight = _meet(g, 70, TAG)
    _open(g, knight)
    _pick(g, FIGHT)
    _continue(g)
    gks = [m for m in g.monsters if m.alive and m.kind == 'green_knight'
           and not getattr(m, '_flavor_encounter_tag', None)]
    assert len(gks) == 1 and gks[0].is_mini_boss
    assert 'green_knight' in g.level_mgr._placed_mini_bosses    # never a second one later
    assert g.karma == k0                                        # resisting is never penalised
    # His return blow, with his head back on: the girdle turns it, and he
    # remembers the chapel.
    gk = gks[0]
    gk._has_revived = True
    g.player.hp = 0
    assert g._green_girdle_spares(gk) and g.player.hp == 1
    assert 'You would not kneel at my chapel' in str(g.msg_log.entries[-1][0])
    assert deeds.has(g._deeds, 'flag.green_girdle_turned')
    # Dead, he drops no second girdle while the hero holds his.
    n_ground = len(g.ground_items)
    g._spawn_unique_item(gk.x, gk.y, GIRDLE)
    assert len(g.ground_items) == n_ground
    g._green_knight_slain(gk)
    assert deeds.has(g._deeds, 'slew.green_knight')


def test_the_girdle_drops_from_the_knight_when_the_hero_has_none():
    g = _game(name='__test_green_chapel_drop__')
    n_ground = len(g.ground_items)
    g._spawn_unique_item(g.player.x, g.player.y, GIRDLE)
    assert len(g.ground_items) == n_ground + 1


def test_a_girdle_that_already_turned_his_axe_or_a_dead_knight_keeps_no_appointment():
    g = _game(name='__test_green_chapel_gone__')
    _hero_who_lied(g)
    assert g._encounter_allowed(BY_TAG[TAG])
    from game_magic import _monster_defn
    from monster import Monster
    gk = Monster(_monster_defn('green_knight'), g.player.x + 1, g.player.y)
    g._green_knight_slain(gk)
    assert not g._encounter_allowed(BY_TAG[TAG])


def test_the_wandering_knight_gives_way_to_his_chapel():
    """A carried callback can land on the floor rolled for the Green Knight
    as a mini-boss: he is at his chapel instead, not wandering beside it."""
    from game_magic import _monster_defn
    from monster import Monster
    g = _game(name='__test_green_chapel_one_knight__')
    _hero_who_lied(g)
    _go(g, 72)
    x, y = next((x, y) for y in range(g.dungeon.height) for x in range(g.dungeon.width)
                if g.dungeon.is_walkable(x, y) and (x, y) != (g.player.x, g.player.y))
    g.monsters.append(Monster(_monster_defn('green_knight'), x, y))
    assert g._place_callback(72, TAG)
    assert not [m for m in g.monsters if m.kind == 'green_knight' and getattr(m, 'is_mini_boss', False)
                and not getattr(m, '_flavor_encounter_tag', None)]


def test_save_and_load_mid_scene_reopens_on_the_choice():
    import main
    import save_system
    from game_states import STATE_NPC_ENCOUNTER, STATE_PLAYER
    g = _game(name='__test_green_chapel_reload__')
    g.player.hp = g.player.max_hp = 200
    _hero_who_lied(g)
    knight = _meet(g, 70, TAG)
    _open(g, knight)
    _pick(g, KNEEL)                       # the nick paid; quit on the outcome page
    save_system.settle_unfinished_actions(g)
    assert save_system.save_game(g)
    st = save_system.load_game(g.player_name)
    g2, notice = main._restore_saved_game(_screen(), g.player_name, st)
    assert g2 is not None, notice
    g2.state = STATE_PLAYER
    assert g2.player.hp == 170            # paid once, not again
    k0 = g2.karma
    knight2 = _npc(g2, TAG)
    assert knight2 is not None and knight2.kind == 'green_knight'
    assert g2._start_flavor_encounter(knight2)
    assert g2.state == STATE_NPC_ENCOUNTER and g2._npc_encounter_phase == 'options'
    assert [o['label'] for _i, o in g2._npc_visible_options()] == [TRUTH, BLUSTER, SILENT]
    _pick(g2, TRUTH)
    assert g2.karma == k0 + 1 and not _holds_girdle(g2)
    assert g2.player.hp == 170


def test_the_encounter_screen_shows_the_knight():
    import lore_art
    g = _game(name='__test_green_chapel_art__')
    _hero_who_lied(g)
    knight = _meet(g, 70, TAG)
    lore_art.clear_cache()
    assert g._start_flavor_encounter(knight)
    g.render()
    assert lore_art.cached('monster', 'green_knight')


def test_the_old_girdle_line_still_reads_for_a_hero_never_at_the_chapel():
    from game_magic import _monster_defn
    from monster import Monster
    g = _game(name='__test_green_chapel_plain__')
    gk = Monster(_monster_defn('green_knight'), g.player.x + 1, g.player.y)
    g.monsters.append(gk)
    _hero_who_lied(g)
    gk._has_revived = True
    g.player.hp = 0
    assert g._green_girdle_spares(gk)
    assert '"You lacked a little loyalty," he says.' in str(g.msg_log.entries[-1][0])


def test_oswin_urged_home_pays_on_a_pass_and_goes_either_way():
    import karma
    for passed, gain in ((True, 1), (False, 0)):
        g = _game(name='__test_oswin_home__')
        k0 = g.karma
        oswin = _meet(g, 84, 'fallen_paladin', flavor=False)
        _open(g, oswin)
        labels = [o['label'] for _i, o in g._npc_visible_options()]
        g._npc_encounter_input(pygame.K_1 + labels.index(OSWIN_BACK))
        g.quiz_engine._end(success=passed)
        assert g._npc_encounter_phase == 'outcome'
        assert 'Ranulf' in g._npc_outcome_text
        _continue(g)
        assert g.karma == k0 + gain and karma.gate_enabled()
        assert deeds.has(g._deeds, 'told.oswin_go_back')
        assert [p['spec']['encounter'] for p in _pending(g)] == ['flv_paladin_end']
        kinds = {e['kind'] for e in g._deeds['karma']['ledger'] if e['applied']}
        assert kinds == ({'stance'} if passed else set())
