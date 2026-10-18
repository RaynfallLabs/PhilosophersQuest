"""Encounter validator (DEEDS_KARMA_DESIGN.md section 8.3, with Brandon's
decisions in section 11).

Checks every encounter in data/npc_encounters.json and data/flavor_encounters.json,
after encounter_schema.normalise:
fields and types, the option rules (at most four visible, a free way out, no
reward beside a quiz), the karma rules P5-P12, virtue tags, the stakes table,
quizzes, references, disguises, and the road / chronicle lint.

Today's content predates the schema, so its known breaches are listed in
tests/encounter_legacy_allow.json (tag -> codes). That list must shrink to
empty by the end of Phase 3a; the test also fails on a stale entry.

    py -m tools.encounters.validate            # errors not on the allowlist
    py -m tools.encounters.validate --all      # every finding, allowlisted too
    py -m tools.encounters.validate --report   # +1 karma chances per block
    py -m tools.encounters.validate --budget   # expected +1 chances per block (Road slots)
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

ALLOWLIST_PATH = os.path.join(ROOT, 'tests', 'encounter_legacy_allow.json')
PENDING_KEY = 'pending_engine'

ENC_KEYS = {
    'tag', 'name', 'symbol', 'color', 'sprite_id', 'text', 'options', 'proper_noun',
    'block', 'trigger_item', 'trigger_level_offset', 'min_level', 'max_level',
    'chain_after', 'role', 'stakes', 'band', 'person', 'requires', 'forbids',
    'text_variants', 'contested', 'stance', 'stance_note', 'tragedy', 'disguise',
    'callback_only', 'fallback_anchor', 'chronicle_meet', 'escorts', 'road_ok',
    # J3: a scene that finds the hero on arrival and has no walk-away (C19).
    'hostile',
}
OUTCOME_KEYS = {
    'outcome', 'outcome_variants', 'karma', 'karma_kind', 'virtue', 'reward',
    'bonus_reward', 'cost', 'deeds', 'oath', 'oath_keep', 'oath_break',
    'oath_release', 'schedule', 'delayed', 'escort', 'person_status', 'thread',
    'thread_close', 'chronicle', 'fight', 'then',
    # J3 (ENCOUNTER_STORIES_DRAFT): a lapse settled in a scene, other people
    # the scene changes, the encounter person's last line, the encounter
    # room's door turning to wall, the floor giving the hero up, and the
    # per-person lines table (The Gate).
    'oath_lapse', 'people', 'last_line', 'seal_door', 'expel_up', 'people_lines',
}
OPTION_ONLY_KEYS = {
    'label', 'quiz', 'pass', 'fail', 'requires', 'forbids', 'hidden', 'hidden_group',
    'villain', 'side', 'naive', 'warning', 'road', 'fail_reward',
    # J3: consequences as each round is lost; a fail that reads by rounds won.
    'per_miss', 'fail_by_correct',
}
QUIZ_KEYS = {'subject', 'tier', 'mode', 'threshold', 'total_qs', 'timed', 'title',
             'max_chain', 'pass_at', 'play_all'}
OATH_KEYS = {'id', 'to', 'what', 'item_id', 'due_floors', 'thread', 'lapse_chronicle',
             'lapse_mode'}
PER_MISS_KEYS = {'text', 'cost', 'effect', 'deeds'}
PEOPLE_KEYS = {'id', 'name', 'status', 'deserving', 'owes', 'owed', 'last_line'}
PEOPLE_LINES_KEYS = {'table', 'max', 'after', 'none'}
COST_TYPES = {
    'food', 'healing_potion', 'potion', 'scroll', 'weapon', 'gold', 'hp_percent',
    'max_hp', 'sp', 'hp', 'mp', 'random_item', 'triggered_item', 'accept_item',
    'spawn_deadite_ambush', 'hp_pct', 'sp_pct', 'mp_pct', 'max_hp_pct', 'gold_pct',
    'triggered_item_id', 'stat', 'armor_enchant', 'multi',
}
ITEM_COSTS = {'food', 'healing_potion', 'potion', 'scroll', 'weapon'}
PCT_COSTS = {'hp_pct', 'sp_pct', 'mp_pct', 'max_hp_pct', 'gold_pct', 'hp_percent'}
REWARD_TYPES = {
    'gold', 'random_weapon', 'random_armor', 'random_shield', 'random_accessory',
    'random_potion', 'random_scroll', 'random_food', 'random_wand', 'stat',
    'specific_item', 'random_item', 'effect', 'hp_restore', 'sp_restore', 'mp_restore',
    'hp_restore_pct', 'sp_restore_pct', 'mp_restore_pct', 'enchant_weapon', 'message',
    'multi', 'gold_pct', 'gold_pct_loss', 'armor_enchant', 'random_artifact', 'service',
}
THREAD_KEYS = {'id', 'hint', 'closed_line'}
STAT_NAMES = ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')
ROAD_BANNED = ('karma', 'quiz', 'option', 'choose', 'press', 'light', 'medium', 'high',
               'stakes')
CALLBACK_KEYS = {'encounter', 'after_floors', 'requires', 'replace', 'if_missed', 'thread',
                 'lost_line', 'after_oath_due'}
DELAYED_KEYS = {'after_floors', 'reward', 'cost', 'requires', 'text', 'chronicle'}
ESCORT_KEYS = {'id', 'name', 'sprite_id', 'color', 'hp', 'ac', 'goal', 'leash', 'floors',
               'perk', 'on_arrive', 'on_fail', 'on_arrive_variants', 'on_fail_variants',
               'on_fail_trapdoor', '$ref'}
ESCORT_PERKS = (None, 'reveal_traps', 'light')


@dataclass(frozen=True)
class Issue:
    tag: str
    code: str
    msg: str

    def __str__(self):
        return f'{self.tag}: [{self.code}] {self.msg}'


# ------------------------------------------------------------------ loading

def load_all():
    """[(source, encounter)] after normalise: 'npc' or 'flavor'."""
    import flavor_encounters
    import npc_encounters
    out = [('npc', e) for e in npc_encounters.ENCOUNTERS]
    out += [('flavor', e) for e in flavor_encounters.FLAVOR_ENCOUNTERS]
    return out


def load_allowlist(path: str = ALLOWLIST_PATH) -> dict:
    """tag -> codes. The ``pending_engine`` section (tag -> codes) lists the
    breaches that exist only because a field's engine support is being built
    in parallel (ENCOUNTER_STORIES_DRAFT.md J3). It is merged in here, and it
    is emptied once that work is merged."""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    out = {k: set(v) for k, v in data.items()
           if not k.startswith('_') and k != PENDING_KEY}
    for tag, codes in (data.get(PENDING_KEY) or {}).items():
        if not tag.startswith('_'):
            out.setdefault(tag, set()).update(codes)
    return out


def load_pending(path: str = ALLOWLIST_PATH) -> dict:
    """Only the ``pending_engine`` section: tag -> codes."""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return {k: set(v) for k, v in (data.get(PENDING_KEY) or {}).items()
            if not k.startswith('_')}


def _subjects() -> set:
    qdir = os.path.join(ROOT, 'data', 'questions')
    return {n[:-5] for n in os.listdir(qdir) if n.endswith('.json')}


def _quest_piece_ids() -> set:
    with open(os.path.join(SRC, 'main.py'), encoding='utf-8') as f:
        text = f.read()
    m = re.search(r'_QUEST_PIECE_IDS = frozenset\(\((.*?)\)\)', text, re.S)
    return set(re.findall(r"'([a-z0-9_]+)'", m.group(1))) if m else set()


def _item_ids() -> set:
    ids = set()
    idir = os.path.join(ROOT, 'data', 'items')
    for n in os.listdir(idir):
        if not n.endswith('.json'):
            continue
        with open(os.path.join(idir, n), encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            ids.update(data.keys())
        elif isinstance(data, list):
            ids.update(d.get('id') for d in data if isinstance(d, dict))
    return ids


def _rules() -> dict:
    with open(os.path.join(ROOT, 'data', 'karma_rules.json'), encoding='utf-8') as f:
        return json.load(f)


def _monster_ids() -> set:
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        return set(json.load(f))


def _people_tables() -> set:
    try:
        with open(os.path.join(ROOT, 'data', 'gate_lines.json'), encoding='utf-8') as f:
            return {k for k in json.load(f) if not k.startswith('_')}
    except (OSError, ValueError):
        return set()


def _effect_ids() -> set:
    from status_effects import EFFECT_INFO
    return set(EFFECT_INFO)


# ------------------------------------------------------------------ scoring

def reward_value(reward, table: dict) -> float:
    """The P7 score of a reward under karma_rules.json 'reward_value'."""
    if not isinstance(reward, dict):
        return 0.0
    rtype = reward.get('type')
    if rtype == 'multi':
        return sum(reward_value(r, table) for r in reward.get('rewards') or ())
    spec = table.get(rtype) or {}
    v = float(spec.get('flat', 0))
    # A named item can be worth more than the flat price (the Book of Thoth
    # is the greatest prize in the game): "items": {id: value} replaces it.
    items = spec.get('items') if isinstance(spec.get('items'), dict) else {}
    if reward.get('item_id') in items:
        v = float(items[reward['item_id']])
    for field, coef in spec.items():
        if field in ('flat', 'items'):
            continue
        if field == 'amount' and 'amount' not in reward and 'min' in reward:
            val = (float(reward['min']) + float(reward.get('max', reward['min']))) / 2
        else:
            val = float(reward.get(field, 1 if field == 'count' else 0) or 0)
        v += float(coef) * val
    return v


# A cost scored as the reward it gives up. P7 compares a forgo option with
# its temptation net of what each costs: keeping the sword you would
# otherwise hand over IS the greater benefit.
COST_AS_REWARD = {
    'food': 'random_food', 'healing_potion': 'random_potion', 'potion': 'random_potion',
    'scroll': 'random_scroll', 'weapon': 'random_weapon', 'random_item': 'random_item',
    'triggered_item': 'specific_item', 'triggered_item_id': 'specific_item',
}
_PCT_COST_AS = {'hp_pct': 'hp_restore_pct', 'sp_pct': 'sp_restore_pct',
                'mp_pct': 'mp_restore_pct', 'max_hp_pct': 'hp_restore_pct',
                'hp_percent': 'hp_restore_pct', 'gold_pct': 'gold_pct'}


def cost_value(cost, table: dict) -> float:
    """What paying ``cost`` gives up, on the reward_value scale."""
    if not isinstance(cost, dict):
        return 0.0
    ctype = cost.get('type')
    if ctype == 'multi':
        return sum(cost_value(c, table) for c in cost.get('costs') or ())
    if ctype in COST_AS_REWARD:
        rw = {'type': COST_AS_REWARD[ctype]}
        if 'count' in cost:
            rw['count'] = cost['count']
        return reward_value(rw, table)
    if ctype in _PCT_COST_AS:
        return reward_value({'type': _PCT_COST_AS[ctype], 'amount': cost.get('amount', 0)}, table)
    if ctype == 'gold':
        return reward_value({'type': 'gold', 'amount': cost.get('amount', 0)}, table)
    if ctype == 'stat':
        return reward_value({'type': 'stat', 'amount': cost.get('amount', 1)}, table)
    return 0.0


def option_value(opt: dict, table: dict, enc: dict | None = None) -> float:
    """An option's material worth: the best branch it can lead to (an
    escort's arrival reward included), net of what the option costs."""
    from encounter_schema import option_branches
    vals = []
    deed_prices = table.get('deeds') if isinstance(table.get('deeds'), dict) else {}
    for b in option_branches(opt):
        v = reward_value(b.get('reward'), table) + reward_value(b.get('bonus_reward'), table)
        for d in b.get('deeds') or ():
            v += float(deed_prices.get(d if isinstance(d, str) else (d or {}).get('id'), 0))
        esc = b.get('escort')
        if isinstance(esc, dict):
            spec = (((enc or {}).get('escorts') or {}).get(esc['$ref'])
                    if '$ref' in esc else esc)
            v += reward_value(((spec or {}).get('on_arrive') or {}).get('reward'), table)
        if b is not opt and b.get('cost'):
            v -= cost_value(b['cost'], table)
        vals.append(v)
    return max(vals, default=0.0) - cost_value(opt.get('cost'), table)


def _norm(s: str) -> str:
    return re.sub(r'[^a-z0-9 ]+', '', str(s or '').lower())


def _chron_lint(line: str) -> list:
    bad = []
    if re.search(r'\bL\d+', line) or re.search(r'Level \d+', line):
        bad.append('floor number')
    if '!' in re.sub(r'"[^"]*"', '', line):
        bad.append('exclamation')
    if re.search(r'\+\d', line):
        bad.append('+N')
    if any(re.search(rf'\b{s}\b\s*[+-]?\d', line) for s in STAT_NAMES):
        bad.append('stat number')
    if re.search(r'\b(karma|quiz|tier)\b', line, re.I):
        bad.append('game term')
    if len(line) > 220:
        bad.append('too long')
    return bad


def _road_lint(road: dict, label: str) -> list:
    hint = str((road or {}).get('hint', ''))
    bad = []
    if re.search(r'\d', hint):
        bad.append('digit')
    if any(re.search(rf'\b{s}\b', hint) for s in STAT_NAMES):
        bad.append('stat name')
    if any(re.search(rf'\b{w}\b', hint, re.I) for w in ROAD_BANNED):
        bad.append('banned word')
    if len(hint) > 90:
        bad.append('too long')
    # A label of a word or two ("Refuse") may share a word with its hint.
    if label and len(_norm(label).split()) >= 3 and _norm(label) in _norm(hint):
        bad.append('quotes the label')
    return bad


# ------------------------------------------------------------------ checks

def validate_encounter(source: str, enc: dict, ctx: dict) -> list:
    import deeds
    from encounter_schema import (MAX_VISIBLE, QUIZ_MODES, ROLES, STAKES,
                                  has_naive_sibling, is_quiz, max_karma, option_branches)
    import karma
    tag = str(enc.get('tag', '?'))
    out = []

    def err(code, msg):
        out.append(Issue(tag, code, msg))

    # ---- fields
    for k in ('tag', 'name', 'symbol', 'text'):
        if not isinstance(enc.get(k), str) or not enc.get(k):
            err('field', f'missing or empty {k!r}')
    col = enc.get('color')
    if not (isinstance(col, (list, tuple)) and len(col) == 3
            and all(isinstance(c, int) and 0 <= c <= 255 for c in col)):
        err('field', 'color must be three 0-255 ints')
    if not re.fullmatch(r'[a-z0-9_]+', tag):
        err('field', 'tag must be [a-z0-9_]+ (it becomes a deed id segment)')
    if source == 'npc':
        if enc.get('block') not in range(1, 11):
            err('field', 'anchor needs block 1-10')
    else:
        lo, hi = enc.get('min_level'), enc.get('max_level')
        if not (isinstance(lo, int) and isinstance(hi, int) and 1 <= lo <= hi):
            err('field', 'flavor needs 1 <= min_level <= max_level')
    for k in enc:
        if k not in ENC_KEYS and not k.startswith('_'):
            err('unknown_key', f'encounter key {k!r}')
    if enc.get('chain_after'):
        err('chain_after', "'chain_after' is retired: schedule the follow-up from the "
                           "opener's outcome (DEEDS_KARMA_DESIGN 4.7)")
    for key, spec in (enc.get('escorts') or {}).items():
        _check_escort(err, f'escorts.{key}', spec)
    if enc.get('role') not in ROLES:
        err('field', f"role {enc.get('role')!r}")
    stakes = enc.get('stakes')
    if stakes not in STAKES:
        err('field', f'stakes {stakes!r}')
    opts = enc.get('options')
    if not isinstance(opts, list) or not opts:
        err('field', 'no options')
        return out

    # ---- conditions
    def cond_ok(cond, where):
        if cond is None:
            return
        if not isinstance(cond, dict):
            err('condition', f'{where}: not an object')
            return
        for k, v in cond.items():
            if k not in deeds.CONDITION_KEYS:
                err('condition', f'{where}: unknown key {k!r}')
            if k == 'any':
                for sub in v or ():
                    cond_ok(sub, where)

    cond_ok(enc.get('requires'), 'requires')
    cond_ok(enc.get('forbids'), 'forbids')
    for v in enc.get('text_variants') or ():
        cond_ok(v.get('when'), 'text_variants')
        if not v.get('text'):
            err('field', 'text_variant without text')

    # ---- options: shape
    unconditional = grouped = ungrouped_cond = 0
    groups = set()
    free_exit = False
    for i, o in enumerate(opts):
        where = f'option {i + 1}'
        if not isinstance(o.get('label'), str) or not o.get('label'):
            err('field', f'{where}: no label')
        for k in o:
            if k not in OUTCOME_KEYS | OPTION_ONLY_KEYS:
                err('unknown_key', f'{where}: key {k!r}')
        cond_ok(o.get('requires'), where)
        cond_ok(o.get('forbids'), where)
        conditional = bool(o.get('requires') or o.get('forbids'))
        if o.get('hidden_group') is not None:
            groups.add(o['hidden_group'])
            grouped += 1
        elif conditional:
            ungrouped_cond += 1
        else:
            unconditional += 1
        if not conditional and not o.get('cost') and not is_quiz(o) and not o.get('fight') \
                and o.get('hidden_group') is None:
            free_exit = True
        if o.get('hidden') and not conditional:
            err('hidden', f'{where}: hidden but no requires')
        if is_quiz(o):
            for k in ('reward', 'bonus_reward', 'karma', 'outcome'):
                if k in o:
                    err('quiz_shape', f'{where}: option-level {k!r} beside a quiz')
            for b in ('pass', 'fail'):
                if not isinstance(o.get(b), dict) or not isinstance(o[b].get('outcome'), str):
                    err('quiz_shape', f'{where}: {b} needs an outcome')
            _check_quiz(err, where, o['quiz'], stakes, source, ctx, QUIZ_MODES)
            _check_per_miss(err, where, o, stakes, ctx)
        elif not isinstance(o.get('outcome'), str):
            err('field', f'{where}: no outcome')
        if not is_quiz(o):
            for k in ('per_miss', 'fail_by_correct'):
                if k in o:
                    err('quiz_shape', f'{where}: {k!r} needs a quiz')
        if o.get('cost') is not None:
            _check_cost(err, where, o['cost'], stakes)
        for b in option_branches(o):
            if b is not o:
                for k in b:
                    if k not in OUTCOME_KEYS:
                        err('unknown_key', f'{where}: outcome key {k!r}')
            th = b.get('thread')
            if th is not None:
                if not (isinstance(th, dict) and re.fullmatch(r'[a-z0-9_]+', str(th.get('id', '')))):
                    err('thread', f'{where}: a thread needs an id [a-z0-9_]+')
                else:
                    for k in th:
                        if k not in THREAD_KEYS:
                            err('unknown_key', f'{where}: thread key {k!r}')
            for rk in ('reward', 'bonus_reward'):
                if b.get(rk) is not None:
                    _check_reward(err, where, b[rk])
            if b is not o and b.get('cost') is not None:
                # A fail branch (or a fail read by rounds won) may carry a loss
                # at high stakes, or where it lands the very trap a naive
                # sibling walks into (a failed look at the crying girl ends
                # where following her does).
                _fails = [o.get('fail')] + list((o.get('fail_by_correct') or {}).values())
                fail_ok = any(b is f for f in _fails) and (stakes == 'high'
                                                           or has_naive_sibling(enc, o))
                # A price paid only on success ("half fare, if he agrees").
                if not fail_ok and b is not o.get('pass') and not o.get('naive'):
                    err('stakes', f'{where}: an outcome cost only in a pass, a high-stakes '
                                  'fail, a fail beside a naive sibling, or a naive option')
                _check_cost(err, where, b['cost'], stakes)
            for d in b.get('deeds') or ():
                did = d if isinstance(d, str) else (d or {}).get('id')
                if not deeds.valid_id(did):
                    err('deed', f'{where}: bad deed id {did!r}')
                tags = [] if isinstance(d, str) else (d.get('tags') or [])
                if any(str(t).startswith('virtue:') for t in tags):
                    err('virtue', f'{where}: virtue tags are engine-only')
            for v in b.get('outcome_variants') or ():
                cond_ok(v.get('when'), where)
                for vk in v:
                    if vk not in ('when', 'outcome', 'chronicle'):
                        err('unknown_key', f'{where}: outcome_variants key {vk!r}')
                if v.get('chronicle'):
                    bad = _chron_lint(v['chronicle'])
                    if bad:
                        err('chronicle_lint', f"{where} variant: {', '.join(bad)}")
            if b.get('chronicle'):
                bad = _chron_lint(b['chronicle'])
                if bad:
                    err('chronicle_lint', f"{where}: {', '.join(bad)}")
            if b.get('then') not in (None, 'close', 'options'):
                err('field', f"{where}: then {b.get('then')!r}")
            _check_j3_outcome(err, where, b, stakes, ctx, cond_ok)
            for cb in b.get('schedule') or ():
                _check_callback(err, where, cb, cond_ok)
            for dl in b.get('delayed') or ():
                _check_delayed(err, where, dl, cond_ok)
            esc = b.get('escort')
            if esc is not None and not (isinstance(esc, dict) and '$ref' in esc):
                _check_escort(err, where, esc)
            if b.get('fight') is not None:
                _check_fight(err, where, b['fight'], ctx)
        if o.get('road') is not None:
            bad = _road_lint(o['road'], o.get('label', ''))
            if bad:
                err('road_lint', f"{where}: {', '.join(bad)}")
            if o.get('hidden') and not o['road'].get('hint'):
                err('road_lint', f'{where}: a hidden option needs an oblique hint')
        if o.get('warning') and _norm(o['warning']) not in _norm(enc.get('text', '')):
            err('naive', f'{where}: warning sentence not in the scene text')
    bound = unconditional + len(groups) + ungrouped_cond
    if bound > MAX_VISIBLE:
        err('visible', f'up to {bound} options visible at once (max {MAX_VISIBLE})')
    if enc.get('hostile') is not None and not isinstance(enc.get('hostile'), bool):
        err('field', 'hostile is true or false')
    if enc.get('hostile'):
        # The dead do not let you walk away, but they must come to fight.
        if not enc.get('callback_only'):
            err('hostile', 'a hostile scene is callback_only (it comes for the hero)')
        if not any(b.get('fight') for o in opts for b in option_branches(o)):
            err('hostile', 'a hostile scene needs at least one option that starts a fight')
    elif not free_exit and not _free_in_every_state(opts):
        err('free_exit', 'no unconditional option without a cost (a way to walk away)')

    # ---- karma rules
    table = ctx['rules'].get('reward_value', {})
    for i, o in enumerate(opts):
        where = f'option {i + 1}'
        for b in option_branches(o):
            k = int(b.get('karma', 0) or 0)
            kind = b.get('karma_kind')
            if kind == 'reckless':
                err('karma_kind', f"{where}: 'reckless' is gone; naive help costs "
                                  'material consequences, not karma')
            elif kind is not None and kind not in karma.KINDS - {karma.LEGACY}:
                err('karma_kind', f'{where}: unknown kind {kind!r}')
            if k and kind is None:
                err('karma_kind_missing', f'{where}: karma {k:+d} without karma_kind')
            # At most +1 a choice, and no choice costs more than one (Brandon,
            # 2026-10-18: "Max karma drop is -1"; karma.MAX_LOSS). Betrayal
            # costs one; handing a guilty man to lawful judgement costs none.
            if k > 1 or k < -karma.MAX_LOSS:
                err('karma_size', f'{where}: karma {k:+d} (at most +1, and a loss '
                                  f'is at most -{karma.MAX_LOSS})')
            # An oath broken here costs its own -1 betray unless this outcome
            # already pays it as betray; any other negative beside it would
            # take two in one choice.
            if b.get('oath_break') and k < 0 and kind != 'betray':
                err('karma_size', f'{where}: karma {k:+d} {kind} beside an oath_break '
                                  'would cost two; the break is the -1')
            if k > 0 and kind in ('constancy', 'recovery'):
                err('karma_kind', f'{where}: {kind} is engine-only')
            if k > 0 and kind == 'oath':
                err('karma_kind', f'{where}: an oath pays through oath_keep, not karma')
            if k < 0 and kind in karma.POSITIVE_GATED | karma.POSITIVE_UNGATED:
                err('karma_kind', f'{where}: negative karma with positive kind {kind!r}')
            if k > 0 and kind == 'forgo':
                _check_forgo(err, where, o, opts, table, enc)
            if k > 0 and kind == 'judgment':
                in_pass = b is o.get('pass') and has_naive_sibling(enc, o)
                if not in_pass and not _after_a_pass(enc, o)                         and not _unlocked_by_judged_pass(enc, o):
                    err('judgment', f'{where}: judgment +1 only in a quiz pass with a '
                                    'naive sibling, or on a follow-up only that pass reveals')
            if k > 0 and kind == 'stance':
                if not enc.get('stance') or o.get('side') != 'right':
                    err('stance', f'{where}: stance +1 needs an encounter stance and '
                                  "side 'right'")
                elif not (o.get('cost') or is_quiz(o)
                          or any(br.get('fight') for br in option_branches(o))):
                    err('stance', f'{where}: the right side must carry a visible cost')
            v = b.get('virtue')
            if v is not None:
                if v == 'forgo':
                    _check_forgo(err, where, o, opts, table, enc)
                elif v == 'judged':
                    if b is not o.get('pass') or not has_naive_sibling(enc, o):
                        err('virtue', f'{where}: judged only in a quiz pass with a naive sibling')
                else:
                    err('virtue', f'{where}: virtue {v!r} is engine-only')
            if stakes == 'light' and k != 0:
                err('light_karma', f'{where}: a light encounter gives no karma (P11)')
            if stakes == 'light' and (b.get('oath_keep') or b.get('oath_break')):
                err('stakes', f'{where}: an oath is kept or broken only at medium or higher')
            rw = b.get('reward') or {}
            if _gives_stat(rw) or _gives_stat(b.get('bonus_reward') or {}):
                if b is not o.get('pass'):
                    err('stat_reward', f'{where}: a permanent stat only inside a quiz pass (P12)')
                if stakes == 'light':
                    err('stat_reward', f'{where}: a permanent stat never at light stakes')
        if o.get('naive'):
            if any(int(b.get('karma', 0) or 0) for b in option_branches(o)):
                err('naive', f'{where}: naive kindness is never karma, either way')
            if not _has_consequence(o):
                err('naive', f'{where}: naive help must carry a real cost or consequence')
    if enc.get('contested'):
        ks = {(max_karma(o), min(int(b.get('karma', 0) or 0) for b in option_branches(o)))
              for o in opts if not o.get('villain')}
        if len(ks) > 1:
            err('contested', 'contested encounter with unequal karma (P9)')
    if enc.get('stance'):
        right = [max_karma(o) for o in opts if o.get('side') == 'right']
        wrong = [max_karma(o) for o in opts if o.get('side') == 'wrong']
        if not right or not wrong or not min(right) > max(wrong):
            err('stance', "stance: every 'right' option must outscore every 'wrong' one (P10)")
    if tag == 'deadite_woman':
        if any(max_karma(o) or min(int(b.get('karma', 0) or 0) for b in option_branches(o))
               for o in opts):
            err('deadite', 'the Deadite gives 0 karma on every option (P16)')

    # ---- references
    trig = enc.get('trigger_item')
    if trig:
        if trig not in ctx['items']:
            err('reference', f'trigger_item {trig!r} is not an item')
        if trig not in ctx['quest_pieces']:
            err('quest_piece', f'trigger_item {trig!r} is not in Game._QUEST_PIECE_IDS')
    dis = enc.get('disguise')
    if dis is not None:
        tells = (dis or {}).get('tells') or []
        if not tells:
            err('disguise', 'a disguise needs tells')
        elif not any(_norm(t) in _norm(enc.get('text', '')) for t in tells):
            err('disguise', 'no tell appears in the scene text')
    if enc.get('tragedy') == 'unsavable':
        pid = (enc.get('person') or {}).get('id')
        for o in opts:
            for b in option_branches(o):
                for d in b.get('deeds') or ():
                    did = d if isinstance(d, str) else (d or {}).get('id', '')
                    if pid and did == f'saved.{pid}':
                        err('tragedy', 'an unsavable tragedy saves its person')
    return out


def _pass_only_deeds(enc: dict) -> set:
    """Deed ids that only a quiz PASS writes in this encounter, from a quiz
    option with a naive sibling on screen (nothing else in the encounter
    writes them)."""
    from encounter_schema import has_naive_sibling, is_quiz, option_branches

    def ids(b):
        out = set()
        for d in b.get('deeds') or ():
            did = d if isinstance(d, str) else (d or {}).get('id')
            if did:
                out.add(did)
        return out
    from_pass, elsewhere = set(), set()
    for o in enc.get('options') or ():
        if is_quiz(o):
            elsewhere |= ids(o)
            for b in option_branches(o):
                if b is o.get('pass') and has_naive_sibling(enc, o):
                    from_pass |= ids(b)
                elif b is not o.get('pass'):
                    elsewhere |= ids(b)
        else:
            elsewhere |= ids(o)
        for pm in o.get('per_miss') or ():
            elsewhere |= ids(pm or {})
    return from_pass - elsewhere


def _after_a_pass(enc: dict, o: dict) -> bool:
    """Silas (A24): a judgment +1 may sit on a follow-up option that appears
    only after a passed examination: the option itself has no quiz and its
    ``requires`` names a deed that only such a pass writes."""
    from encounter_schema import is_quiz
    if is_quiz(o):
        return False
    req = o.get('requires') or {}
    named = set(req.get('deeds_all') or ())
    any_ = list(req.get('deeds_any') or ())
    gated = _pass_only_deeds(enc)
    if named & gated:
        return True
    return bool(any_) and all(d in gated for d in any_)


def _check_fight(err, where, spec, ctx):
    from encounter_schema import MAX_FIGHT_COUNT
    items = spec if isinstance(spec, list) else [spec]
    if not items:
        err('fight', f'{where}: an empty fight')
    for e in items:
        if isinstance(e, str):
            mid, n = e, 1
        elif isinstance(e, dict):
            mid, n = e.get('monster_id'), e.get('count', 1)
            for k in e:
                if k not in ('monster_id', 'count'):
                    err('unknown_key', f'{where}: fight key {k!r}')
        else:
            err('fight', f'{where}: fight entry must be an id or {{monster_id, count}}')
            continue
        if not isinstance(mid, str) or not mid:
            err('fight', f'{where}: fight needs a monster_id')
        elif mid not in ctx['monsters']:
            err('fight', f'{where}: monster {mid!r} is not in monsters.json')
        if not isinstance(n, int) or not 1 <= n <= MAX_FIGHT_COUNT:
            err('fight', f'{where}: count {n!r} (1-{MAX_FIGHT_COUNT})')


def _check_per_miss(err, where, o, stakes, ctx):
    q = o.get('quiz') or {}
    pm = o.get('per_miss')
    if pm is not None:
        if not isinstance(pm, list) or not pm:
            err('per_miss', f'{where}: per_miss is a list, one entry a lost round')
        else:
            total = int(q.get('total_qs', q.get('threshold', 1)) or 1)
            if len(pm) > total:
                err('per_miss', f'{where}: {len(pm)} per_miss entries for {total} rounds')
            if len(pm) > 1 and not q.get('play_all'):
                err('per_miss', f'{where}: a second lost round needs play_all (a miss '
                                'otherwise ends the quiz)')
            for i, e in enumerate(pm):
                if not isinstance(e, dict):
                    err('per_miss', f'{where}: per_miss {i + 1} must be an object')
                    continue
                for k in e:
                    if k not in PER_MISS_KEYS:
                        err('unknown_key', f'{where}: per_miss key {k!r}')
                if e.get('cost') is not None:
                    _check_cost(err, f'{where} per_miss {i + 1}', e['cost'], stakes)
                eff = e.get('effect')
                if eff is not None:
                    if not (isinstance(eff, dict) and eff.get('effect') in ctx['effects']):
                        err('per_miss', f'{where}: per_miss {i + 1} effect {eff!r}')
                for d in e.get('deeds') or ():
                    did = d if isinstance(d, str) else (d or {}).get('id')
                    if not __import__('deeds').valid_id(did):
                        err('deed', f'{where}: bad deed id {did!r}')
    fbc = o.get('fail_by_correct')
    if fbc is not None:
        total = int(q.get('total_qs', q.get('threshold', 1)) or 1)
        thr = int(q.get('threshold', 1) or 1)
        if not isinstance(fbc, dict) or not fbc:
            err('quiz_shape', f'{where}: fail_by_correct maps rounds won to an outcome')
        else:
            for k, b in fbc.items():
                if not (str(k).isdigit() and int(k) < min(thr, total + 1)):
                    err('quiz_shape', f'{where}: fail_by_correct key {k!r} (a fail wins '
                                      f'0 to {thr - 1})')
                if not isinstance(b, dict) or not isinstance(b.get('outcome'), str):
                    err('quiz_shape', f'{where}: fail_by_correct {k!r} needs an outcome')


def _check_j3_outcome(err, where, b, stakes, ctx, cond_ok):
    import deeds
    oath = b.get('oath')
    if oath is not None:
        if not (isinstance(oath, dict) and oath.get('id')):
            err('oath', f'{where}: an oath needs an id')
        else:
            for k in oath:
                if k not in OATH_KEYS:
                    err('unknown_key', f'{where}: oath key {k!r}')
            mode = oath.get('lapse_mode', 'silent')
            if mode not in deeds.LAPSE_MODES:
                err('oath', f'{where}: lapse_mode {mode!r}')
            if mode == 'callback':
                linked = [cb for cb in b.get('schedule') or ()
                          if isinstance(cb, dict) and cb.get('after_oath_due') == oath['id']]
                if not oath.get('due_floors') or not linked:
                    err('oath', f"{where}: lapse_mode 'callback' needs due_floors and a "
                                'schedule entry with after_oath_due naming the oath')
    for cb in b.get('schedule') or ():
        if isinstance(cb, dict) and cb.get('after_oath_due'):
            if not (isinstance(oath, dict) and oath.get('id') == cb['after_oath_due']):
                err('schedule', f"{where}: after_oath_due {cb['after_oath_due']!r} must name "
                                'the oath sworn in this same outcome')
    for pe in b.get('people') or ():
        if not isinstance(pe, dict) or not re.fullmatch(r'[a-z0-9_]+', str(pe.get('id', ''))):
            err('people', f'{where}: a people entry needs an id [a-z0-9_]+')
            continue
        for k in pe:
            if k not in PEOPLE_KEYS:
                err('unknown_key', f'{where}: people key {k!r}')
        _ll = pe.get('last_line')
        if _ll is not None and (not isinstance(_ll, str) or not _ll or len(_ll) > 220):
            err('field', f'{where}: last_line is a line of at most 220 characters')
        if pe.get('status') is not None and pe['status'] not in deeds.PERSON_STATUSES:
            err('people', f"{where}: person status {pe['status']!r}")
        if pe.get('deserving') not in (None, True, False):
            err('people', f'{where}: deserving is true, false or absent')
    if b.get('people') is not None and not isinstance(b['people'], list):
        err('people', f'{where}: people is a list')
    ps = b.get('person_status')
    if isinstance(ps, dict):
        if ps.get('status') is not None and ps['status'] not in deeds.PERSON_STATUSES:
            err('people', f"{where}: person status {ps['status']!r}")
    elif ps is not None and ps not in deeds.PERSON_STATUSES:
        err('people', f'{where}: person status {ps!r}')
    for key in ('last_line',):
        v = b.get(key)
        if v is not None and (not isinstance(v, str) or not v or len(v) > 220):
            err('field', f'{where}: {key} is a line of at most 220 characters')
    for key in ('seal_door', 'expel_up'):
        if key in b and b[key] is not True:
            err('field', f'{where}: {key} is true or absent')
    pl = b.get('people_lines')
    if pl is not None:
        if not isinstance(pl, dict):
            err('people_lines', f'{where}: people_lines is an object')
        else:
            for k in pl:
                if k not in PEOPLE_LINES_KEYS:
                    err('unknown_key', f'{where}: people_lines key {k!r}')
            if pl.get('table', 'gate') not in ctx['people_tables']:
                err('people_lines', f"{where}: no table {pl.get('table')!r} in gate_lines.json")
            if pl.get('max') is not None and not (isinstance(pl['max'], int) and 1 <= pl['max'] <= 10):
                err('people_lines', f'{where}: max 1-10')
            if stakes != 'light' and int(b.get('karma', 0) or 0):
                err('people_lines', f'{where}: the people lines never carry karma')
    for rk in ('reward', 'bonus_reward'):
        _check_effect_reward(err, where, b.get(rk), ctx)


def _check_effect_reward(err, where, rw, ctx):
    if not isinstance(rw, dict):
        return
    if rw.get('type') == 'multi':
        for sub in rw.get('rewards') or ():
            _check_effect_reward(err, where, sub, ctx)
        return
    if rw.get('type') == 'effect':
        if rw.get('effect') not in ctx['effects']:
            err('reward', f"{where}: effect {rw.get('effect')!r} is not in status_effects")
        fl = rw.get('floors')
        if fl is not None and not (isinstance(fl, int) and 1 <= fl <= 10):
            err('reward', f'{where}: effect floors 1-10')
    if rw.get('type') in ('gold_pct', 'gold_pct_loss'):
        amt = rw.get('amount')
        if not (isinstance(amt, (int, float)) and 0 < amt <= 50):
            err('reward', f"{where}: {rw['type']} amount 1-50 (a share of the hero's own purse)")


def _is_free(o: dict) -> bool:
    """A way to walk away: no cost, no quiz, and no fight it starts."""
    from encounter_schema import is_quiz
    return not o.get('cost') and not is_quiz(o) and not o.get('fight')


def _cond_atoms(cond, out):
    """The deed patterns, items, oath states and stats a condition reads."""
    if not isinstance(cond, dict):
        return
    for k, v in cond.items():
        if k in ('deeds_all', 'deeds_any', 'deeds_none'):
            out['deeds'].update(v or ())
        elif k in ('items_any', 'items_none'):
            out['items'].update(v or ())
        elif k in ('worn_any', 'worn_none'):
            out['items'].update(v or ())
            out['worn'].update(v or ())
        elif k == 'oath_status':
            for oid, want in (v or {}).items():
                out['oaths'].setdefault(oid, set()).update(
                    want if isinstance(want, (list, tuple)) else [want])
        elif k == 'stat_min':
            out['stats'].update(v or {})
        elif k == 'any':
            for sub in v or ():
                _cond_atoms(sub, out)
        else:
            out['other'] = True


def _deed_for(pattern: str) -> str:
    """A concrete deed id matching ``pattern`` (an id, or a prefix)."""
    p = pattern[:-1] if pattern.endswith('*') else pattern
    return p + 'validator_x' if p.endswith('.') else p


def _free_in_every_state(opts) -> bool:
    """Is a free option (no cost, no quiz) visible whatever the hero has
    done, holds and has sworn? A follow-up whose options split by what
    happened earlier covers every case between them. Every combination of
    the facts its conditions read is tried."""
    import itertools

    import deeds
    from encounter_schema import visible_options
    atoms = {'deeds': set(), 'items': set(), 'worn': set(), 'oaths': {}, 'stats': {},
             'other': False}
    for o in opts:
        _cond_atoms(o.get('requires'), atoms)
        _cond_atoms(o.get('forbids'), atoms)
    if atoms['other']:
        return False
    # Only the first opening needs a way out: once a choice is made, Esc
    # resolves the encounter. Deeds this encounter records itself (a
    # 'then: options' step) are therefore absent when it opens.
    from encounter_schema import option_branches
    own = set()
    for o in opts:
        for b in option_branches(o) + [o]:
            own |= _deed_ids(b)
    flags = sorted(atoms['deeds'] - own) + [f'item:{i}' for i in sorted(atoms['items'])] \
        + [f'worn:{i}' for i in sorted(atoms['worn'])]
    oath_axes = [[(oid, st) for st in [None] + sorted(states)]
                 for oid, states in sorted(atoms['oaths'].items())]
    stat_axes = [[(st, 0), (st, int(n))] for st, n in sorted(atoms['stats'].items())]
    if len(flags) + len(oath_axes) + len(stat_axes) > 14:
        return False
    enc = {'options': opts}
    for bits in itertools.product((False, True), repeat=len(flags)):
        for oath_pick in itertools.product(*oath_axes):
            for stat_pick in itertools.product(*stat_axes):
                reg = deeds.new_register()
                held, worn = set(), set()
                for on, f in zip(bits, flags):
                    if on and f.startswith('item:'):
                        held.add(f[5:])
                    elif on and f.startswith('worn:'):
                        worn.add(f[5:])
                        held.add(f[5:])
                    elif on:
                        deeds.record(reg, _deed_for(f), floor=1, block=1, turn=0,
                                     source='validator')
                for oid, st in oath_pick:
                    if st is not None:
                        reg['oaths'][oid] = {'id': oid, 'status': st}
                ctx = {'reg': reg, 'karma': 0, 'stats': dict(stat_pick), 'floor': 1,
                       'deepest': 1, 'items': held, 'worn': worn}
                if not any(_is_free(o) for _i, o in visible_options(enc, ctx)):
                    return False
    return True


def _deed_ids(branch) -> set:
    return {d if isinstance(d, str) else (d or {}).get('id')
            for d in (branch or {}).get('deeds') or ()}


def _unlocked_by_judged_pass(enc: dict, opt: dict) -> bool:
    """A judgment +1 on an option reachable only after a passed examination:
    its ``requires`` names deeds that only a quiz pass in this encounter
    records, on an option with a naive sibling (A24: leave the poisoner to
    his sentence once his wall has been read)."""
    from encounter_schema import has_naive_sibling, is_quiz, option_branches
    req = opt.get('requires') or {}
    wanted = set(req.get('deeds_all') or ()) | set(req.get('deeds_any') or ())
    if not wanted:
        return False
    for o in enc.get('options') or ():
        if not (is_quiz(o) and has_naive_sibling(enc, o) and wanted <= _deed_ids(o.get('pass'))):
            continue
        elsewhere = set()
        for x in enc.get('options') or ():
            for b in option_branches(x) + ([x] if is_quiz(x) else []):
                if b is not o.get('pass'):
                    elsewhere |= _deed_ids(b)
        if not wanted & elsewhere:
            return True
    return False


def _gives_stat(rw: dict) -> bool:
    if rw.get('type') == 'stat':
        return True
    if rw.get('type') == 'multi':
        return any(_gives_stat(r) for r in rw.get('rewards') or ())
    return False


def _has_consequence(o: dict) -> bool:
    """Brandon, decision 9: blind help must cost something real."""
    from encounter_schema import option_branches
    if o.get('cost'):
        return True
    for b in option_branches(o):
        if b.get('cost') or b.get('fight') or b.get('schedule') or b.get('expel_up'):
            return True
        if _harmful_reward(b.get('reward')):
            return True
        if any(_harmful_reward((dl or {}).get('reward')) for dl in b.get('delayed') or ()):
            return True
        for d in b.get('deeds') or ():
            did = d if isinstance(d, str) else (d or {}).get('id', '')
            if str(did).startswith(('lost.', 'wrong.')):
                return True
        ps = b.get('person_status')
        if (ps if isinstance(ps, str) else (ps or {}).get('status')) in ('lost', 'wronged'):
            return True
    return False


def _harmful_reward(rw) -> bool:
    """A 'reward' that is really a loss: a lifted purse, a fever."""
    if not isinstance(rw, dict):
        return False
    if rw.get('type') == 'multi':
        return any(_harmful_reward(r) for r in rw.get('rewards') or ())
    if rw.get('type') == 'gold_pct_loss':
        return True
    if rw.get('type') == 'effect':
        from status_effects import DEBUFFS
        return rw.get('effect') in DEBUFFS
    return False


def _check_callback(err, where, cb, cond_ok):
    if not isinstance(cb, dict) or not cb.get('encounter'):
        err('schedule', f'{where}: a callback names its encounter')
        return
    for k in cb:
        if k not in CALLBACK_KEYS:
            err('unknown_key', f'{where}: schedule key {k!r}')
    span = cb.get('after_floors')
    if not (isinstance(span, list) and len(span) == 2 and all(isinstance(x, int) for x in span)
            and 1 <= span[0] <= span[1]):
        err('schedule', f'{where}: after_floors must be [min, max] with 1 <= min <= max')
    if cb.get('replace', 'light') != 'light':
        err('schedule', f"{where}: a callback only ever replaces a light slot")
    if cb.get('if_missed', 'carry') not in ('carry', 'drop'):
        err('schedule', f"{where}: if_missed {cb.get('if_missed')!r}")
    cond_ok(cb.get('requires'), f'{where} schedule')


def _check_delayed(err, where, dl, cond_ok):
    if not isinstance(dl, dict) or not (isinstance(dl.get('reward'), dict)
                                        or isinstance(dl.get('cost'), dict)):
        err('delayed', f'{where}: a delayed entry needs a reward or a cost')
        return
    for k in dl:
        if k not in DELAYED_KEYS:
            err('unknown_key', f'{where}: delayed key {k!r}')
    if 'karma' in dl:
        err('delayed', f'{where}: delayed rewards never carry karma (P5)')
    span = dl.get('after_floors')
    # [0, n] is allowed: "by the next new floor" (a purse lifted overnight).
    if not (isinstance(span, list) and len(span) == 2 and 0 <= int(span[0]) <= int(span[1])
            and int(span[1]) >= 1):
        err('delayed', f'{where}: after_floors must be [min, max]')
    if dl.get('reward') is not None:
        _check_reward(err, where, dl['reward'])
    if dl.get('cost') is not None:
        _check_cost(err, f'{where} delayed', dl['cost'], 'medium')
    if dl.get('chronicle'):
        bad = _chron_lint(dl['chronicle'])
        if bad:
            err('chronicle_lint', f"{where} delayed: {', '.join(bad)}")
    cond_ok(dl.get('requires'), f'{where} delayed')


def _check_escort(err, where, esc):
    if not isinstance(esc, dict):
        err('escort', f'{where}: escort must be an object')
        return
    for k in esc:
        if k not in ESCORT_KEYS:
            err('unknown_key', f'{where}: escort key {k!r}')
    if not esc.get('id') or not re.fullmatch(r'[a-z0-9_]+', str(esc.get('id'))):
        err('escort', f'{where}: escort id must be [a-z0-9_]+')
    if not isinstance(esc.get('hp'), int) or esc['hp'] < 1:
        err('escort', f'{where}: escort hp is a fixed number (LORE NOT FLOOR)')
    # Escort AC is hero-style: lower is better, 10 is unarmoured, so a civilian
    # sits near 10 and a hoplite or an angel well below it (CODE-01).
    ac = esc.get('ac', 10)
    if not isinstance(ac, int) or isinstance(ac, bool) or not -10 <= ac <= 10:
        err('escort', f'{where}: ac {ac!r} must be a whole number from -10 to 10 '
                      '(hero-style: lower is better, 10 is unarmoured)')
    goal = esc.get('goal', 'stairs_down')
    if goal not in ('stairs_down', 'stairs_up') and not str(goal).startswith('tile:'):
        err('escort', f'{where}: goal {goal!r}')
    if esc.get('perk') not in ESCORT_PERKS:
        err('escort', f"{where}: perk {esc.get('perk')!r}")
    for key in ('on_arrive', 'on_fail'):
        o = esc.get(key)
        if o is not None and isinstance(o, dict):
            if int(o.get('karma', 0) or 0):
                err('escort', f'{where}: an escort never carries karma by itself')
            if o.get('reward') is not None:
                _check_reward(err, f'{where} {key}', o['reward'])
            if o.get('chronicle'):
                bad = _chron_lint(o['chronicle'])
                if bad:
                    err('chronicle_lint', f"{where} {key}: {', '.join(bad)}")


def _check_forgo(err, where, o, opts, table, enc=None):
    mine = option_value(o, table, enc)
    if not any(option_value(s, table, enc) > mine for s in opts
               if s is not o and not s.get('requires')):
        err('forgo', f'{where}: forgo needs a visible sibling with a greater reward (P7)')


def _check_cost(err, where, cost, stakes):
    if not isinstance(cost, dict) or cost.get('type') not in COST_TYPES:
        err('cost', f'{where}: unknown cost {cost!r}')
        return
    if cost['type'] == 'multi':
        subs = cost.get('costs')
        if not isinstance(subs, list) or not subs:
            err('cost', f'{where}: a multi cost lists its costs')
            return
        for sub in subs:
            if isinstance(sub, dict) and sub.get('type') == 'multi':
                err('cost', f'{where}: a multi cost inside a multi cost')
            else:
                _check_cost(err, where, sub, stakes)
        if sum(1 for sub in subs if isinstance(sub, dict) and sub.get('type') in ITEM_COSTS) > 1:
            err('cost', f'{where}: at most one part of a multi cost asks for a pick')
        return
    if cost['type'] == 'gold':
        # A vendor's goods: priced at the trader's rate on the encounter's
        # floor (economy.share_price, ECONOMY_REFACTOR_PROPOSAL S5).
        if 'service' in cost:
            import economy
            if cost['service'] not in economy.SERVICE_SHARE:
                err('cost', f"{where}: gold for unknown service {cost['service']!r}")
        elif 'share' in cost:
            import economy
            mk = cost.get('markup', 1.0)
            if cost['share'] not in economy.MERCHANT_SHARE:
                err('cost', f"{where}: gold share {cost['share']!r} is not a trader class")
            if not isinstance(mk, (int, float)) or not 0.3 <= mk <= 3.0:
                err('cost', f'{where}: gold markup {mk!r} outside 0.3-3')
        elif not any(isinstance(cost.get(k), (int, float)) for k in ('amount', 'min', 'max')):
            err('cost', f'{where}: a gold cost needs an amount or a share')
    if 'count' in cost:
        n = cost['count']
        if cost['type'] not in ITEM_COSTS or not (isinstance(n, int) and 1 <= n <= 5):
            err('cost', f"{where}: count 1-5, and only on an item cost ({cost['type']!r})")
    if cost['type'] in PCT_COSTS:
        cap = {'light': 15, 'medium': 30}.get(stakes)
        if cap is not None and float(cost.get('amount', 0)) > cap:
            err('stakes', f"{where}: {cost['type']} {cost.get('amount')}% over the "
                          f'{stakes} cap of {cap}%')


def _check_reward(err, where, rw):
    if not isinstance(rw, dict) or rw.get('type') not in REWARD_TYPES:
        err('reward', f'{where}: unknown reward {rw!r}')
        return
    if 'purse_pct' in rw:
        # D6: a deep temptation's written sum, or this share of the purse.
        pct = rw['purse_pct']
        if rw['type'] != 'gold' or not isinstance(pct, (int, float)) or not 1 <= pct <= 50:
            err('reward', f'{where}: purse_pct 1-50, and only on a gold reward ({rw!r})')
    if rw['type'] == 'service':
        import economy
        if rw.get('service') not in economy.SERVICE_SHARE:
            err('reward', f"{where}: unknown service {rw.get('service')!r}")
    if rw['type'] == 'specific_item' and rw.get('item_id') not in _items_of(rw.get('item_type')):
        # The engine looks the item up in data/items/<item_type>.json only.
        err('reference', f"{where}: no {rw.get('item_id')!r} in data/items/{rw.get('item_type')}.json")
    for sub in rw.get('rewards') or ():
        _check_reward(err, where, sub)


_ITEMS_BY_FILE: dict = {}


def _items_of(item_type) -> set:
    if item_type not in _ITEMS_BY_FILE:
        p = os.path.join(ROOT, 'data', 'items', f'{item_type}.json')
        try:
            with open(p, encoding='utf-8') as f:
                data = json.load(f)
            _ITEMS_BY_FILE[item_type] = set(data) if isinstance(data, dict) else set()
        except (OSError, ValueError, TypeError):
            _ITEMS_BY_FILE[item_type] = set()
    return _ITEMS_BY_FILE[item_type]


def _check_quiz(err, where, q, stakes, source, ctx, modes):
    for k in q:
        if k not in QUIZ_KEYS:
            err('unknown_key', f'{where}: quiz key {k!r}')
    if 'play_all' in q:
        if not isinstance(q['play_all'], bool):
            err('quiz', f'{where}: play_all is true or false')
        elif q['play_all'] and q.get('mode', 'threshold') not in ('threshold', 'escalator_threshold'):
            err('quiz', f'{where}: play_all is for threshold modes')
        elif q['play_all'] and stakes != 'high':
            err('stakes', f'{where}: every round played is for high stakes')
    if q.get('subject') not in ctx['subjects']:
        err('quiz', f"{where}: subject {q.get('subject')!r} has no bank")
    if q.get('tier') not in range(1, 6):
        err('quiz', f"{where}: tier {q.get('tier')!r}")
    mode = q.get('mode', 'threshold')
    if mode not in modes:
        err('quiz', f'{where}: mode {mode!r}')
    if mode in ('chain', 'escalator_chain') and q.get('pass_at') is None:
        err('quiz', f'{where}: a chain quiz needs pass_at')
    if q.get('timed') and not (q.get('subject') == 'math' and stakes == 'high'):
        err('quiz', f'{where}: timed only for maths at high stakes')
    thr = int(q.get('threshold', 1) or 1)
    total = int(q.get('total_qs', thr) or thr)
    if stakes == 'light' and (thr != 1 or total != 1):
        err('stakes', f'{where}: a light quiz is exactly one question')
    if stakes == 'medium':
        ok = total <= 1 or (thr <= 2 and total <= 3)
        if not ok:
            err('stakes', f'{where}: a medium quiz is one question, or two of three')
        if mode.startswith('escalator') or mode == 'chain':
            err('stakes', f'{where}: chains and escalators are for high stakes')
    if stakes == 'high' and q.get('max_chain') is not None and int(q['max_chain']) > 5:
        err('stakes', f'{where}: max_chain over 5')


def validate_all(encounters=None) -> list:
    encs = encounters if encounters is not None else load_all()
    ctx = {'subjects': _subjects(), 'quest_pieces': _quest_piece_ids(),
           'items': _item_ids(), 'rules': _rules(), 'monsters': _monster_ids(),
           'effects': _effect_ids(), 'people_tables': _people_tables()}
    out = []
    seen = {}
    for source, enc in encs:
        tag = enc.get('tag')
        if tag in seen:
            out.append(Issue(str(tag), 'duplicate', 'tag used twice'))
        seen[tag] = enc
        out.extend(validate_encounter(source, enc, ctx))
    # Cross-references across the whole set.
    made = set()
    kept = []
    threads = set()
    closes = []
    for _src, enc in encs:
        for o in enc.get('options') or ():
            for b in [o, o.get('pass') or {}, o.get('fail') or {}] + \
                    [x for x in (o.get('fail_by_correct') or {}).values() if isinstance(x, dict)]:
                if isinstance(b.get('oath'), dict):
                    made.add(b['oath'].get('id'))
                for k in ('oath_keep', 'oath_break', 'oath_release', 'oath_lapse'):
                    if b.get(k):
                        kept.append((enc['tag'], b[k]))
                if isinstance(b.get('thread'), dict):
                    threads.add(b['thread'].get('id'))
                if b.get('thread_close'):
                    closes.append((enc['tag'], b['thread_close']))
                for cb in b.get('schedule') or ():
                    tgt = seen.get(cb.get('encounter'))
                    if tgt is None:
                        out.append(Issue(enc['tag'], 'reference',
                                         f"schedule names unknown {cb.get('encounter')!r}"))
                    elif not tgt.get('callback_only'):
                        out.append(Issue(enc['tag'], 'reference',
                                         f"schedule target {cb.get('encounter')!r} is not "
                                         'callback_only (the Road could also roll it)'))
                esc = b.get('escort')
                if isinstance(esc, dict) and '$ref' in esc:
                    if esc['$ref'] not in (enc.get('escorts') or {}):
                        out.append(Issue(enc['tag'], 'reference',
                                         f"escort $ref {esc['$ref']!r} not found"))
    for tag, oid in kept:
        if oid not in made:
            out.append(Issue(tag, 'reference', f'oath {oid!r} is never sworn'))
    for tag, tid in closes:
        if tid not in threads:
            out.append(Issue(tag, 'reference', f'thread {tid!r} is never opened'))
    out.extend(_oath_due_vs_callback(encs, seen))
    if encounters is None:
        # The whole game's data and code: every deed a condition reads is
        # written somewhere (ENG-06: told.read_thoth was read, never written).
        out.extend(_deed_refs(encs))
        out.extend(_other_karma_sources(ctx['rules']))
    return out


def _other_karma_sources(rules: dict) -> list:
    """The karma written outside the encounters (the negative patterns, the
    Emberpup) keeps the same ceiling on a loss: one (karma.MAX_LOSS)."""
    import karma
    out = []
    for rule in rules.get('patterns_neg', ()):
        k = int(rule.get('karma', -1))
        if k < -karma.MAX_LOSS:
            out.append(Issue('karma_rules', 'karma_size',
                             f"pattern {rule.get('id')!r}: karma {k:+d} (a loss is at most "
                             f'-{karma.MAX_LOSS})'))
    try:
        with open(os.path.join(ROOT, 'data', 'abandoned_emberpup.json'), encoding='utf-8') as f:
            pup = json.load(f)
    except (OSError, ValueError):
        pup = {}
    k = int(pup.get('attack_karma', 0) or 0)
    if k < -karma.MAX_LOSS:
        out.append(Issue('abandoned_emberpup', 'karma_size',
                         f'attack_karma {k:+d} (a loss is at most -{karma.MAX_LOSS})'))
    return out


def _branches(o: dict) -> list:
    return [o, o.get('pass') or {}, o.get('fail') or {}] + \
        [x for x in (o.get('fail_by_correct') or {}).values() if isinstance(x, dict)]


def _oath_due_vs_callback(encs, seen) -> list:
    """An outcome that swears an oath with a due floor and schedules the
    callback that keeps it: the callback's earliest floor must not come after
    the earliest due floor, or the oath can run out first (ENG-01; the engine
    also lands the callback on or before the rolled due floor)."""
    out = []
    for _src, enc in encs:
        for o in enc.get('options') or ():
            for b in _branches(o):
                oath = b.get('oath')
                if not isinstance(oath, dict) or not oath.get('due_floors'):
                    continue
                if oath.get('lapse_mode') == 'callback':
                    continue
                due_lo = int(oath['due_floors'][0])
                for cb in b.get('schedule') or ():
                    tgt = seen.get(cb.get('encounter')) or {}
                    keeps = any(x.get('oath_keep') == oath.get('id')
                                for to in tgt.get('options') or () for x in _branches(to))
                    span = cb.get('after_floors') or [1, 10]
                    if keeps and int(span[0]) > due_lo:
                        out.append(Issue(enc['tag'], 'oath_due',
                                         f"callback {cb.get('encounter')!r} that keeps oath "
                                         f"{oath.get('id')!r} can come after its due floor "
                                         f"(after_floors {span} vs due_floors {oath['due_floors']})"))
    return out


_DEED_PREFIXES = ('met', 'aid', 'forgo', 'wrong', 'oath', 'kept', 'broke', 'lapsed', 'released',
                  'noticed', 'saved', 'lost', 'spared', 'slew', 'told', 'owe', 'flag')


def _deed_refs(encs) -> list:
    """Every deed pattern read by a requires / forbids / variant ``when``,
    against every deed id the data and the engine write (the bug bash's
    d11 cross-reference, made a gate)."""
    import glob
    import json as _json
    reads, writes = {}, set()

    def walk_cond(c, where):
        if not isinstance(c, dict):
            return
        for k, v in c.items():
            if k in ('deeds_all', 'deeds_any', 'deeds_none'):
                for p in v or ():
                    reads.setdefault(p, set()).add(where)
            elif k == 'any':
                for s in v or ():
                    walk_cond(s, where)

    def walk(o, where):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ('requires', 'forbids', 'when'):
                    walk_cond(v, where)
                elif k == 'deeds':
                    for d in v or ():
                        did = d if isinstance(d, str) else (d or {}).get('id')
                        if did:
                            writes.add(did)
                else:
                    walk(v, where)
        elif isinstance(o, list):
            for x in o:
                walk(x, where)

    for _src, e in encs:
        walk(e, e.get('tag', '?'))
        for oid in re.findall(r'"oath": \{"id": "([a-z0-9_]+)"', _json.dumps(e)):
            for p in ('oath', 'kept', 'broke', 'lapsed', 'released'):
                writes.add(f'{p}.{oid}')
    for fn in glob.glob(os.path.join(ROOT, 'data', '*.json')):
        if 'encounters' in os.path.basename(fn):
            continue
        try:
            with open(fn, encoding='utf-8') as f:
                walk(_json.load(f), os.path.basename(fn))
        except (OSError, ValueError):
            pass
    src = ''
    for fn in glob.glob(os.path.join(ROOT, 'src', '*.py')):
        with open(fn, encoding='utf-8') as f:
            src += f.read()
    alt = '|'.join(_DEED_PREFIXES)
    writes |= set(re.findall(r"""['"]((?:%s)\.[a-z0-9_.]+)['"]""" % alt, src))
    pref = set(re.findall(r"""f['"]((?:%s)\.[a-z0-9_.]*)\{""" % alt, src))

    def satisfiable(p):
        if p.endswith('*') or p.endswith('.'):
            pre = p.rstrip('*')
            return any(w.startswith(pre) for w in writes) or \
                any(pre.startswith(x) or x.startswith(pre) for x in pref)
        return p in writes or any(p.startswith(x) for x in pref)

    return [Issue(sorted(w)[0], 'deed_ref',
                  f'reads deed {p!r}, which nothing writes (also read by {sorted(w)[1:]})'
                  if len(w) > 1 else f'reads deed {p!r}, which nothing writes')
            for p, w in sorted(reads.items()) if not satisfiable(p)]


def split_by_allowlist(issues, allow: dict):
    """(errors not allowlisted, allowlisted issues, stale allowlist entries)."""
    errors, allowed = [], []
    used = set()
    for i in issues:
        if i.code in allow.get(i.tag, ()):
            allowed.append(i)
            used.add((i.tag, i.code))
        else:
            errors.append(i)
    stale = sorted((t, c) for t, codes in allow.items() for c in codes if (t, c) not in used)
    return errors, allowed, stale


def opportunities_report(encounters=None) -> dict:
    """{block: count of options with a +1 karma path}, for the content mix
    (Brandon, decision 5: roughly two or three genuine chances a block)."""
    import deeds
    from encounter_schema import option_branches
    encs = encounters if encounters is not None else load_all()
    rep = {b: 0 for b in range(1, 11)}
    for _src, enc in encs:
        band = enc.get('band') or [1, 1]
        b = deeds.karma_block(band[0])
        for o in enc.get('options') or ():
            if any(int(x.get('karma', 0) or 0) > 0 for x in option_branches(o)):
                rep[b] += 1
    return rep


def has_plus_one_path(enc: dict) -> bool:
    """A genuine +1 chance (ENCOUNTER_STORIES_DRAFT Part I): some option can
    pay +1 karma of a gated kind, or swears an oath whose keep pays later."""
    from encounter_schema import option_branches
    for o in enc.get('options') or ():
        for b in option_branches(o):
            if int(b.get('karma', 0) or 0) > 0:
                return True
            if isinstance(b.get('oath'), dict) and b['oath'].get('id'):
                return True
    return False


def _overlaps(band, lo, hi) -> bool:
    return bool(band) and int(band[0]) <= hi and int(band[1]) >= lo


def opportunity_budget(encounters=None, *, setne_floors=None, setne_tag=None) -> dict:
    """Expected genuine +1 karma chances per 10-floor block, by the Road's
    slots (Brandon, decision 5: roughly two or three a block, never one a
    floor). Per block: the share of its anchor candidates with a +1 path
    (one anchor binds), plus medium slots (two in odd bands, one in even)
    times the share of the medium pool overlapping the block with a +1 path,
    plus (even bands) the high pool's share, plus the chance the showcase
    tomb (its own roll) lands in the block. Callback-only and light content
    never takes a random slot and is not counted."""
    encs = encounters if encounters is not None else load_all()
    if setne_floors is None or setne_tag is None:
        try:
            with open(os.path.join(ROOT, 'data', 'setne_tomb.json'), encoding='utf-8') as f:
                st = json.load(f)
            lo, hi = st.get('floors', [45, 65])
            setne_floors = [x for x in range(int(lo), int(hi) + 1) if x not in (20, 40, 60, 80)]
            setne_tag = st.get('encounter')
        except (OSError, ValueError):
            setne_floors, setne_tag = [], None
    showcase = next((e for _s, e in encs if e.get('tag') == setne_tag), None)
    out = {}
    for b in range(1, 11):
        lo, hi = 10 * b - 9, 10 * b
        anchors = [e for s, e in encs if s == 'npc' and e.get('block') == b]
        story = [e for s, e in encs if s != 'npc' and not e.get('callback_only')
                 and _overlaps(e.get('band'), lo, hi)]
        med = [e for e in story if e.get('stakes') == 'medium']
        high = [e for e in story if e.get('stakes') == 'high']

        def share(pool):
            return (sum(1 for e in pool if has_plus_one_path(e)) / len(pool)) if pool else 0.0
        med_slots = 2 if b % 2 else 1
        p_show = 0.0
        if showcase is not None and has_plus_one_path(showcase) and setne_floors:
            p_show = sum(1 for f in setne_floors if lo <= f <= hi) / len(setne_floors)
        exp = share(anchors) + med_slots * share(med) + (share(high) if b % 2 == 0 else 0.0) + p_show
        out[b] = {
            'anchors': (sum(1 for e in anchors if has_plus_one_path(e)), len(anchors)),
            'medium': (sum(1 for e in med if has_plus_one_path(e)), len(med), med_slots),
            'high': (sum(1 for e in high if has_plus_one_path(e)), len(high)) if b % 2 == 0 else (0, 0),
            'showcase': round(p_show, 2),
            'expected': round(exp, 2),
        }
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    issues = validate_all()
    if '--report' in argv or '--budget' in argv:
        if '--report' in argv:
            for b, n in opportunities_report().items():
                print(f'block {b:2d}: {n} option(s) with a +1 path')
        for b, r in opportunity_budget().items():
            a, m, h = r['anchors'], r['medium'], r['high']
            print(f'block {b:2d}: anchors {a[0]}/{a[1]}, medium {m[0]}/{m[1]} x{m[2]} slot(s), '
                  f'high {h[0]}/{h[1]}, showcase {r["showcase"]:.2f} '
                  f'-> about {r["expected"]:.1f} genuine +1 chances (target 2-3)')
        return 0
    allow = load_allowlist()
    errors, allowed, stale = split_by_allowlist(issues, allow)
    shown = issues if '--all' in argv else errors
    for i in shown:
        print(i)
    for t, c in stale:
        print(f'{t}: [stale-allowlist] {c} no longer occurs; remove it')
    print(f'{len(errors)} error(s), {len(allowed)} allowlisted, {len(stale)} stale allowlist entries')
    return 1 if errors or stale else 0


if __name__ == '__main__':
    sys.exit(main())
