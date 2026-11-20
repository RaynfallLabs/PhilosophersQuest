"""Draws Breath, retuned by lore (AI-1, 2026-11-20).

A dragon in reach makes its full routine of claw and bite while its breath is
drawn up again, and the ready breath is a turn of its own: never both in one
turn (src/breath.py routine(), hooked in Monster.attack). The breathers whose
lore makes a routine (true dragons and drakes, the chimera's heads, a behir's
bite and coils...) carry multi_attack_count, each routine inside a quarter of
the health of the hero of its peak floor (the lore pass's rubric,
docs/design/MONSTER_LORE_PASS_2026_11_19.md).
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import breath  # noqa: E402
import monster_bands as mb  # noqa: E402
import senses  # noqa: E402
import tells  # noqa: E402
from monster import Monster  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))

# The breathers that make a full routine in reach, and its length.
ROUTINES = {
    'young_red_dragon': 2, 'young_black_dragon': 2, 'undead_dragon_lesser': 2,
    'adult_blue_dragon': 2, 'adult_red_dragon': 2, 'young_dragon': 2, 'lich_dragon_spawn': 2,
    'adult_dragon': 2, 'elder_dragon': 2, 'ancient_dragon': 2, 'dread_wyrm': 2,
    'elder_dracolich': 2, 'abyssal_dragon': 2, 'wyrm': 2, 'spectral_dragon': 2, 'dracolich': 2,
    'drake_fire': 2, 'drake_cold': 2, 'chimera': 3, 'chimera_alpha': 2, 'pit_fiend_spawn': 2,
    'behir_lesser': 2, 'naga_guardian': 2, 'nuckelavee': 2, 'yacumama': 2,
}
# The bites the lore gave them (Beowulf's wyrm, "wings and jaws", the drakes...).
NEW_BITES = {'wyrm': 'Bite', 'spectral_dragon': 'Spectral Jaws', 'dracolich': 'Bone Jaws',
             'drake_fire': 'Bite', 'drake_cold': 'Bite'}


class Hero:
    def __init__(self, x=10, y=10, hp=100000):
        self.x, self.y = x, y
        self.hp = self.max_hp = hp
        self.status_effects = {}
        self.equipped_accessories = []
        self.boons_taken = {}
        self.STR = self.CON = self.DEX = self.INT = self.WIS = self.PER = 10
        self.shield = None
        self.weapon = None
        self.armor_slots = []

    def has_effect(self, name):
        return self.status_effects.get(name, 0) > 0

    def add_effect(self, name, turns):
        self.status_effects[name] = max(self.status_effects.get(name, 0), int(turns))
        return True

    def is_burdened(self):
        return False

    def get_ac(self):
        return 10

    def get_sight_radius(self):
        return 8

    def take_damage(self, amount, damage_type='physical'):
        self.hp = max(0, self.hp - max(0, int(amount)))
        return max(0, int(amount))

    def save_bonus_for(self, _stat):
        return 0


def make(kind, x=5, y=5):
    m = Monster({**MONS[kind], 'id': kind}, x, y)
    m._aware = True
    m._opened = True
    return m


def stub(**over):
    base = {'id': 'test_mob', 'name': 'test mob', 'symbol': 'M', 'color': [200, 200, 200],
            'ai_pattern': 'aggressive', 'hp': '40', 'speed': 10, 'thac0': 1,
            'attacks': [{'name': 'Bite', 'damage': '1d4', 'type': 'pierce', 'delivery': 'bite'}],
            'tags': ['beast']}
    base.update(over)
    m = Monster(base, 5, 5)
    m._aware = True
    return m


def setup_function(_):
    random.seed(5)
    senses.begin_turn(moved=True, guilty=False, floor=40)
    breath.ENABLED = True


def _blows_each_turn(m, hero, turns):
    """The attacks each of m's turns resolved (Monster.attack, as a turn:
    tick_effects first)."""
    seen = []
    real = m._resolve_blow

    def record(atk, player, in_flurry=False):
        seen[-1].append(atk['name'])
        return real(atk, player, in_flurry)
    m._resolve_blow = record
    for _ in range(turns):
        m.tick_effects()
        seen.append([])
        m.attack(hero)
    return seen


def _breaths(m):
    return {a['name'] for a in m.attacks if a.get('delivery') == 'breath'}


# ---------------------------------------------------------------- the engine
def test_a_dragon_in_reach_breathes_when_ready_and_rakes_and_bites_meanwhile():
    d = make('adult_red_dragon')
    hero = Hero(6, 5)
    turns = _blows_each_turn(d, hero, 9)
    fire = _breaths(d)
    assert turns[0] == ['Inferno Breath']                  # ready: the breath is the turn
    assert turns[1] == ['Claw', 'Bite'] and turns[2] == ['Claw', 'Bite']
    assert turns[3] == ['Inferno Breath']                  # drawn up again after 3 turns
    for t in turns:                                        # never a breath and a routine at once
        assert not (fire & set(t)) or t in (['Inferno Breath'],), t
    assert sum(1 for t in turns if t == ['Inferno Breath']) == 3


def test_a_dragon_drawing_breath_never_rakes_from_afar():
    d = make('elder_dragon')
    hero = Hero(9, 5)
    breath.spend(d, next(a for a in d.attacks if a['delivery'] == 'breath'))
    turns = _blows_each_turn(d, hero, 2)
    assert turns == [[], []]                               # it spends the turn coming in


def test_a_ready_dragon_at_range_breathes_alone():
    d = make('ancient_dragon')
    assert _blows_each_turn(d, Hero(8, 5), 1) == [['Frost Breath']]


def test_the_elder_seizes_and_bites_its_tail_after():
    d = make('elder_dragon')
    assert d.attacks[0]['name'] == 'Crushing Claw'         # the first attack never moved
    turns = _blows_each_turn(d, Hero(6, 5), 2)
    assert turns[1] == ['Crushing Claw', 'Bite']


def test_the_chimeras_three_heads():
    c = make('chimera')
    turns = _blows_each_turn(c, Hero(6, 5), 2)
    assert turns[0] == ['Fire Breath']
    assert turns[1] == ['Claw', 'Bite', 'Goat Gore']


def test_a_hydra_spits_alone_and_bites_and_sweeps_between():
    h = make('mythic_hydra')                               # its routine was already two
    turns = _blows_each_turn(h, Hero(6, 5), 3)
    assert turns[0] == ['Acid Spray']                      # it was bite and spray at once
    assert turns[1] == turns[2] == ['Multi Bite', 'Tail Sweep']


def test_a_breather_with_one_blow_makes_it_alone():
    a = make('azarael')                                     # fist and furnace breath
    turns = _blows_each_turn(a, Hero(6, 5), 2)
    assert turns == [['Furnace Breath'], ['Bronze Fist']]


def test_a_creature_with_no_breath_keeps_its_routine():
    s = stub(multi_attack_count=2, attacks=[
        {'name': 'Claw', 'damage': '1d4', 'type': 'slash', 'delivery': 'blow'},
        {'name': 'Bite', 'damage': '1d4', 'type': 'pierce', 'delivery': 'bite'},
        {'name': 'Hug', 'damage': '1d4', 'type': 'blunt', 'delivery': 'grapple'}])
    assert breath.routine(s, Hero(6, 5), 2) is None
    assert _blows_each_turn(s, Hero(6, 5), 1) == [['Claw', 'Bite']]


def test_named_foes_keep_their_flurry():
    t = make('tiamat')
    assert breath.routine(t, Hero(6, 5), 3) is None


def test_with_the_knob_off_the_routine_is_the_old_rule():
    d = make('adult_red_dragon')
    breath.ENABLED = False
    try:
        assert breath.routine(d, Hero(6, 5), 2) is None
    finally:
        breath.ENABLED = True


def test_the_simulator_meets_the_same_routine():
    """The simulator calls the real Monster.attack for a monster beside the
    hero; a breather drawing breath comes in, so its hero does not spend the
    turn closing on it (sim_ai1.kite_prob)."""
    import sim_ai1
    d = make('young_dragon')
    assert sim_ai1.kite_prob(d, 0.45) == 0.45              # ready: it may back off to breathe
    breath.spend(d, next(a for a in d.attacks if a['delivery'] == 'breath'))
    assert sim_ai1.kite_prob(d, 0.45) == 0.0
    breath.ENABLED = False
    try:
        assert sim_ai1.kite_prob(d, 0.45) == 0.45          # ai_breath=0: the old rule
    finally:
        breath.ENABLED = True


def test_the_tell_says_it_fights_in_full_fury_meanwhile():
    d = make('adult_dragon')
    assert 'breath_recharge' in tells.abilities(d)
    t = json.load(open(os.path.join(ROOT, 'data', 'tells.json'), encoding='utf-8'))
    text = json.dumps(t).lower()
    assert 'full fury' in text
    assert 'only tooth and claw' not in text


# ---------------------------------------------------------------- the data
def test_each_routine_breather_has_its_routine_by_lore():
    for kind, n in ROUTINES.items():
        m = MONS[kind]
        assert m.get('multi_attack_count') == n, kind
        blows = [a for a in m['attacks'] if a.get('delivery') != 'breath' and not mb._distance(a)]
        assert len(blows) >= n, kind
        assert any(a.get('delivery') == 'breath' for a in m['attacks']), kind


def test_each_routine_stays_inside_a_quarter_of_the_heros_health():
    for kind in ROUTINES:
        m = MONS[kind]
        _one, turn = mb.turn_damage(m)
        blows = [mb.dice_mean(a['damage']) for a in m['attacks']
                 if a.get('delivery') != 'breath' and not mb._distance(a)][:m['multi_attack_count']]
        assert turn >= sum(blows) > 0, kind                 # the bands tool counts the routine
        assert turn <= 0.25 * mb.hero_at(m['peak_floor'])[1], kind
        assert turn <= 0.35 * mb.hero_at(m['min_level'])[1], kind


def test_the_lore_bites_and_the_claws_cut_by_lore():
    for kind, name in NEW_BITES.items():
        a = next(a for a in MONS[kind]['attacks'] if a['name'] == name)
        assert a['delivery'] == 'bite' and a['type'] and a['damage'], kind
    atk = {k: {a['name']: a['damage'] for a in MONS[k]['attacks']}
           for k in ('adult_dragon', 'elder_dragon', 'ancient_dragon', 'chimera')}
    assert atk['adult_dragon']['Claw'] == '4d8+14'          # an adult's claw is less than its bite
    assert atk['elder_dragon']['Crushing Claw'] == '3d10+18'
    assert atk['elder_dragon']['Bite'] == '5d10+27'
    assert atk['ancient_dragon']['Claw'] == '5d10+18'
    assert atk['chimera']['Claw'] == '2d6+4' and atk['chimera']['Goat Gore'] == '2d8+5'
    for k in ('adult_dragon', 'elder_dragon', 'ancient_dragon'):
        a = {x['name']: mb.dice_mean(x['damage']) for x in MONS[k]['attacks']}
        claw = a.get('Claw', a.get('Crushing Claw'))
        assert claw < a['Bite'], k


def test_the_breathers_that_keep_one_blow():
    """A giant's one weapon, a wolf's bite, a hydra's heads already rolled as
    one bite: no routine."""
    for kind in ('frost_giant', 'fire_giant_king', 'frostfang_giant', 'rime_thurs',
                 'winter_wolf', 'hydra', 'iron_golem', 'lava_elemental', 'magma_elemental',
                 'sekhmet_lioness', 'nidhogg_brood', 'dahaka_wyrm', 'cave_toad'):
        assert not MONS[kind].get('multi_attack_count'), kind
