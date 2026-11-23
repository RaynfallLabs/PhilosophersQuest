"""Console lines are cues, not soliloquies (Brandon, 2026-11-22: "your
tactics messages are WAY too descriptive. Just saying the Goblin warband
leader will call for help is enough... Think like you're an adventurer in
the dungeon... you need a cue, not a soliloquy, especially for console
messages").

Every line the monster behaviour systems leave in the message log (the
Tactical Mind and the captains' orders, the first and third waves, the
packs, the war-bands, the senses, the floor's clock, the kinds' own lines
and the tells on first sight) is ONE short line: filled in with a long
creature name it stays under CAP, and it never tells what WILL happen
(RUNDOWN). The Bestiary, Observe (O) and the help page keep the fuller
words where they teach. Data-layer tests: they read the JSON.

The effects and statuses meet the same rule (effect_lines, at the end):
data/effects.json and data/hunger.json's lines, the expiry lines, and every
line the effect modules write in their own source.
"""
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import tells  # noqa: E402
import war_bands  # noqa: E402
from family_lore import KIN, KNOWN, UNKNOWN  # noqa: E402
from monster import Monster  # noqa: E402

CAP = 90            # the hard cap of a console line, filled in
TARGET = 70         # what a line should be with a common name
CUE_MAX = 60        # a tell's cue, unfilled

# What a line says when it is a rundown of what will happen next, the rule
# or the counter, instead of what the hero sees and hears now.
RUNDOWN = ('will not follow', 'will be waiting', 'will come', 'will run', 'will lose',
           'will fall', 'will turn', 'will follow', 'will not hide', 'will not shake',
           'will not last', 'will seek', 'will not care', 'the longer you', 'keep coming while',
           'for as long as', 'if you drop', 'if you end', 'if he falls', 'if {he} falls', 'when he falls',
           'stand still and',
           'kill the', 'kill {him}', 'strike {him}', 'drop him', 'they wait', '{he} waits for you',
           # The effects' asides: what he could do instead, the counter, the rule.
           'you can still', 'you can step', 'you can fight', 'in guard', 'would have', 'would thaw',
           'takes a turn', 'no mp is spent', 'win it back', 'you will have to', 'unless it is cured',
           'until you eat', 'will not mend', 'stops it', 'yours to take off', 'can be healed again',
           'usual pace', 'every action takes')

# A long name, so a line that fits with it fits with any.
_LONG = {'{The}': 'The hobgoblin warlord', '{the}': 'the hobgoblin warlord',
         '{A}': 'A hobgoblin warlord', '{a}': 'a hobgoblin warlord', '{name}': 'The hobgoblin warlord',
         '{He}': 'He', '{he}': 'he', '{His}': 'His', '{his}': 'his', '{him}': 'him',
         '{himself}': 'himself', '{pet}': 'Emberpup', '{hazard}': 'fire vent',
         '{potion}': 'a potion of healing', '{potion_bare}': 'potion of healing', '{damage}': '12',
         '{n}': '4', '{light}': 'torch', '{buff}': 'magic resistance', '{flask}': 'a fire pot',
         '{attack}': 'longbow', '{noun}': 'venom', '{tool}': 'silver dust', '{pack}': 'wolves',
         '{weapon}': 'longsword', '{by}': 'The hobgoblin warlord', '{item}': 'potion of healing',
         '{kind}': 'Hobgoblin Warlord', '{what}': 'potion of healing, Hobgoblin Warlord'}


def _load(name):
    with open(os.path.join(ROOT, 'data', name), encoding='utf-8') as f:
        return json.load(f)


MONS = _load('monsters.json')


def _filled(s):
    for k, v in _LONG.items():
        s = s.replace(k, v)
    return s


def _walk(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _walk(v, path + (str(k),))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _walk(v, path + (str(i),))
    elif isinstance(o, str):
        yield '.'.join(path), o


def console_lines():
    """[(where, line)] of every behaviour line the log can say."""
    out = []
    minds = _load('minds.json')
    for sec in ('lines', 'unseen', 'orders'):
        out += [(f'minds.{p}', s) for p, s in _walk(minds[sec], (sec,)) if '_doc' not in p]
    ai = _load('monster_ai.json')
    out += [(f'monster_ai.{p}', s) for p, s in _walk(ai)
            if '_doc' not in p and 'buff_words' not in p and not p.endswith('ask_line')]
    packs = _load('packs.json')
    out += [(f'packs.{p}', s) for p, s in _walk(packs['tactics'], ('tactics',)) if p.endswith('line')]
    out += [(f'packs.{p}', s) for p, s in _walk(packs['tricks'], ('tricks',))
            if p.split('.')[-1] in ('line', 'line_unseen', 'message')]
    for bid, b in war_bands.data()['bands'].items():
        out += [(f'war_bands.{bid}.{k}', b[k]) for k in ('line', 'rout_line', 'break_line')]
        biggest = {r: (b.get('counts') or {}).get(r, [0, 0])[1] for r in war_bands.ROLES}
        out.append((f'war_bands.{bid}.known_line', war_bands.arrival_line({'id': bid, 'counts': biggest}, True)))
    sen = _load('senses.json')
    out += [(f'senses.{p}', s) for p, s in _walk(sen['senses'], ('senses',)) if '.lines.' in p]
    out.append(('senses.search.lost_line', sen['search']['lost_line']))
    for key in ('warning', 'stirs'):
        out += [(f'senses.wanderers.{key}.{i}', s) for i, s in enumerate(sen['wanderers'][key])]
    ks = _load('kit_sense.json')
    for key in ('lines', 'lines_many'):
        out += [(f'kit_sense.{p}', s) for p, s in _walk(ks[key], (key,))]
    behaviours = ('alarm', 'death_throes', 'aura', 'spells', 'bargain', 'enraged_form', 'sheds_skin',
                  'summons_fall', 'countdown_voice', 'metal_eater', 'corpse_hop', 'gold_gatherer',
                  'talisman', 'on_stunned', 'appeased_by', 'weak_spot_line', 'lair_line')
    for kind, d in MONS.items():
        if not isinstance(d, dict):
            continue
        for b in behaviours:
            for p, s in _walk(d.get(b), (b,)):
                last = p.split('.')[-1]
                if 'tell' in p.split('.') or last in ('name', 'id', 'kind', 'type', 'effect', 'when', '_doc') \
                        or ' ' not in s:
                    continue
                out.append((f'monsters.{kind}.{p}', s))
    return out


def test_the_census_finds_the_lines():
    lines = console_lines()
    assert len(lines) > 400
    where = {w.split('.')[0] for w, _ in lines}
    assert where == {'minds', 'monster_ai', 'packs', 'war_bands', 'senses', 'kit_sense', 'monsters'}


def test_every_behaviour_line_is_one_short_cue():
    long = [(w, len(_filled(s)), s) for w, s in console_lines() if len(_filled(s)) > CAP]
    assert not long, long


def test_no_behaviour_line_is_a_rundown_of_what_will_happen():
    bad = [(w, s) for w, s in console_lines() for r in RUNDOWN if r in s.lower()]
    assert not bad, bad


def test_most_lines_fit_the_target_with_a_common_name():
    common = {'{The}': 'The goblin', '{the}': 'the goblin'}

    def fill(s):
        for k, v in common.items():
            s = s.replace(k, v)
        return _filled(s)
    lines = console_lines()
    over = [(w, s) for w, s in lines if len(fill(s)) > TARGET]
    assert len(over) <= len(lines) // 10, over


def test_brandons_example_the_alarm_raiser_is_one_cue():
    m = Monster({**MONS['hobgoblin'], 'id': 'hobgoblin'}, 1, 1)
    assert 'raises_alarm' in tells.abilities(m)
    assert tells.cue(m, 'raises_alarm') == 'The Hobgoblin will shout for help when he sees you.'


# ---------------------------------------------------------------- the tells

def test_every_tell_has_a_short_cue_that_names_the_creature():
    for key, e in tells.data()['effects'].items():
        for field in ('cue', 'cue_friend', 'cue_weak'):
            if field == 'cue' or field in e:
                c = e[field]
                assert c and len(c) <= CUE_MAX, (key, field, c)
                assert '{The}' in c or '{the}' in c, (key, field, c)
                assert c.count('.') + c.count('!') == 1, (key, field, 'one sentence')
                low = c.lower()
                for w in ('shift+', 'press ', 'kill ', 'carry ', 'wax ', 'mirror', 'guard (', 'strike {him}'):
                    assert w not in low, (key, field, w)


def test_first_sight_is_one_short_line_for_every_kind_at_every_level():
    seen = 0
    for kind, d in MONS.items():
        if not isinstance(d, dict) or not d.get('name'):
            continue
        m = Monster({**d, 'id': kind}, 1, 1)
        keys = tells.abilities(m)
        if not keys:
            continue
        seen += 1
        for level in (UNKNOWN, KIN, KNOWN):
            t = tells.log_line(m, keys[0], level)
            assert t and '{' not in t and t[:1].isupper(), (kind, level, t)
            assert len(t) <= CAP, (kind, level, len(t), t)
            low = t.lower()
            assert not any(r in low for r in RUNDOWN), (kind, level, t)
        # The cue is what a hero who knows it hears: never the sign again,
        # never the counter.
        known = tells.log_line(m, keys[0], KNOWN)
        assert known == tells.log_line(m, keys[0], KIN)
        sign, _does, counter = tells.parts(m, keys[0])
        assert tells.log_line(m, keys[0], UNKNOWN) == sign
        assert not counter or counter not in known
    assert seen > 200


def test_observe_keeps_the_full_tell():
    """The reading (O) still teaches: sign, what it does and the counter."""
    ghoul = Monster({**MONS['ghoul'], 'id': 'ghoul'}, 1, 1)
    full = tells.line(ghoul, 'paralyzed', KNOWN)
    sign, does, counter = tells.parts(ghoul, 'paralyzed')
    assert full == ' '.join((sign, does, counter))
    assert tells.log_line(ghoul, 'paralyzed', KNOWN) == 'The Ghoul can hold you still where you stand.'


def test_the_variants_have_their_own_cues():
    pud = Monster({**MONS['black_pudding'], 'id': 'black_pudding'}, 1, 1)
    c = tells.cue(pud, 'splits')
    assert c.startswith('The Black Pudding splits in two under ') and '{' not in c
    assert 'cutting' in c and 'lightning' in c
    blood = Monster({**MONS['tiamat_blood'], 'id': 'tiamat_blood'}, 1, 1)
    assert tells.cue(blood, 'splits').endswith('under a weak blow.')
    sphinx = Monster({**MONS['sphinx'], 'id': 'sphinx'}, 1, 1)
    assert tells.cue(sphinx, 'parley').endswith(' will ask you a riddle before you pass.')


# ---------------------------------------------------------------- the effects
#
# The same ruling, met by the effects and statuses the same night (the
# systems bug bash): a fall said "(Stand still, fight or be in Guard while
# Stunned.)", a fear "You can step away, shoot, cast or drink." Each line
# is what the hero feels or sees now; what he can do about it is the
# status's own words (status_effects.EFFECT_INFO) and the help screen's
# (data/ui/monster_ways.json, "What they lay on you").

EFFECT_MODULES = ('action_gate', 'game_effects', 'status_effects', 'knockdown', 'mind_theft',
                  'quiz_sight', 'venom', 'hunger', 'holds')
# What an f-string's value is, at its longest; anything else a long name.
_EXPR_FILL = {'loss': '(-1 enchantment)', 'left': '9', 'stat': 'STR', 'noun': 'creeping frost',
              'flavor': 'Your hardy constitution', '_what': 'strength'}


def _src_text(node):
    """A string the source writes, its f-string values filled in; None for
    anything else."""
    import ast
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out = ''
        for v in node.values:
            if isinstance(v, ast.Constant):
                out += str(v.value)
            else:
                out += _EXPR_FILL.get(ast.unparse(v.value), 'the hobgoblin warlord')
        return out
    if isinstance(node, ast.IfExp):
        return _src_text(node.body) or _src_text(node.orelse)
    return None


def _said_in(module):
    """[(where, line)] a module writes for the log in its own source: what it
    hands add_message, what it appends to ``messages`` and the line of a
    (line, kind) or (applied, line) it returns. ('_signals' are main's.)"""
    import ast
    with open(os.path.join(ROOT, 'src', module + '.py'), encoding='utf-8') as f:
        tree = ast.parse(f.read())
    found = []
    for node in ast.walk(tree):
        cands = []
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.args:
            first = node.args[0]
            if node.func.attr == 'add_message':
                cands = [first]
            elif (node.func.attr == 'append' and isinstance(node.func.value, ast.Name)
                  and node.func.value.id == 'messages'):
                cands = list(first.elts[:1]) if isinstance(first, ast.Tuple) else [first]
        elif isinstance(node, ast.Return) and isinstance(node.value, ast.Tuple):
            cands = list(node.value.elts)
        for c in cands:
            s = _src_text(c)
            if s and ' ' in s.strip() and not s.startswith('_'):
                found.append((f'{module}:{getattr(c, "lineno", 0)}', s.strip()))
    return found


def effect_lines():
    """[(where, line)] of every line the effects and statuses can say."""
    import status_effects
    fx = _load('effects.json')
    out = [(f'effects.lines.{k}', s) for k, s in fx['lines'].items()]
    poison = {k: s for k, s in fx['poison']['lines'].items() if k not in ('chip', 'bestiary')}
    out += [(f'effects.poison.{k}', s) for k, s in poison.items()]
    # A bite that would kill says so after its own line (venom.line, lands).
    out += [(f'effects.poison.{k}+deadly', f"{s} {poison['deadly']}")
            for k, s in poison.items() if k != 'deadly']
    out.append(('effects.quiz.nothing_there', fx['quiz']['nothing_there']))
    # The stone's count is said after its line: "Your limbs drag. (5)".
    out += [(f'effects.lines.{k}+count', fx['lines'][k] + ' (9)')
            for k in ('stiff', 'stiff_slow', 'rigid_lethal', 'rigid_lesser')]
    out += [(f'hunger.lines.{k}', s) for k, s in _load('hunger.json')['lines'].items()]
    out += [(f'status_effects.expire.{k}', s) for k, (s, _kind) in status_effects._EXPIRE_MSGS.items()]
    for module in EFFECT_MODULES:
        out += _said_in(module)
    return out


def test_the_effect_census_finds_the_lines():
    lines = effect_lines()
    assert len(lines) > 150
    where = {w.split('.')[0].split(':')[0] for w, _ in lines}
    assert {'effects', 'hunger', 'status_effects', 'game_effects'} <= where
    said = {s for _w, s in lines}
    assert 'You are knocked off your feet!' in said           # effects.json
    assert 'You stumble in a random direction!' in said        # game_effects.py
    assert 'The hobgoblin warlord takes hold!' not in said     # (a noun, not a name)
    assert 'The creeping frost takes hold!' in said            # status_effects.py, filled


def test_every_effect_line_is_one_short_cue():
    long = [(w, len(_filled(s)), _filled(s)) for w, s in effect_lines() if len(_filled(s)) > CAP]
    assert not long, long


def test_no_effect_line_is_a_rundown_of_what_to_do():
    bad = [(w, s) for w, s in effect_lines() for r in RUNDOWN if r in s.lower()]
    assert not bad, bad


def test_most_effect_lines_fit_the_target():
    lines = effect_lines()
    over = [(w, s) for w, s in lines if len(_filled(s)) > TARGET]
    assert len(over) <= len(lines) // 10, over


def test_no_effect_line_carries_a_counter_in_brackets():
    """"(In Guard you would have held it.)": an aside in brackets is a rule,
    never a cue. A count, a lost plus or a stat ("(5)", "(-1 level)") is
    what happened."""
    import re
    bad = [(w, s) for w, s in effect_lines()
           for inner in re.findall(r'\(([^)]*)\)', s) if re.search(r'[a-z]{3,} [a-z]{3,}', inner)]
    assert not bad, bad


# What the log no longer says, each status's own words and the help screen
# still teach: (status, a word of its counter in the status's words, its row
# in "What they lay on you", a word of it there).
TAUGHT = (('stunned', 'Guard', 'Stunned', 'Guard'),
          ('fumbling', 'Guard', None, None),
          ('knocked_down', 'standing up', 'Knocked down', 'getting up'),
          ('frozen', 'lit torch', 'Frozen', 'lit torch'),
          ('frozen', 'hands', 'Frozen', 'still strike'),
          ('immobilized', 'still fight', 'Held by the feet', 'Everything else works'),
          ('feared', 'Shoot, cast or drink', 'Afraid', 'Step away, shoot or cast'),
          ('charmed', 'cannot harm your charmer', 'Charmed', 'cannot harm your charmer'),
          ('hexed', 'will not come off', 'Hexed', 'will not come off'),
          ('petrifying', 'Oil of Rue', 'Turning to stone', 'Oil of Rue'),
          ('petrifying', 'slow', 'Turning to stone', 'slow'),
          ('forgetting', 'Kill it on this floor', 'Mind-bitten', 'Kill it before you leave the floor'),
          ('silenced', 'no spell or scroll', None, None),
          ('weak_from_hunger', 'Strength -2, wounds do not mend', None, None),
          ('starving', 'hunger wounds you until you eat', None, None),
          ('ruptured', 'cannot be healed', None, None))


def test_the_counters_left_out_of_the_log_are_taught_elsewhere():
    from status_effects import EFFECT_INFO
    rows = {}
    for sec in _load(os.path.join('ui', 'monster_ways.json'))['sections']:
        rows.update({r[0]: r[1] for r in sec.get('rows') or ()})
    for status, word, row, there in TAUGHT:
        assert word in EFFECT_INFO[status][2], (status, word)
        if row:
            assert there in rows[row], (row, there)
    # Hunger's cost is on How Quizzes Work too.
    hunger = ' '.join(p for sec in _load(os.path.join('ui', 'how_quizzes_work.json'))['sections']
                      for p in sec.get('paragraphs') or ())
    assert 'Strength -2' in hunger and 'wounds do not mend' in hunger and 'until you eat' in hunger


def test_a_frozen_refusal_is_the_cue_alone():
    """The torch is the chip's and the help's: the refusal no longer adds
    "A lit torch would thaw you."."""
    import effect_rules
    assert 'frozen_hint' not in effect_rules.data()['lines']
    assert effect_rules.line('frozen_hands') == 'Your hands are numb with ice.'
    assert effect_rules.line('fall') == 'You step, the floor tips, and you fall.'
    assert effect_rules.line('feared_strike', the='the banshee') == 'You cannot make yourself strike the banshee.'
