"""Encounter validator (DEEDS_KARMA_DESIGN.md section 8.3, with Brandon's
decisions in section 11).

Checks every encounter in data/npc_encounters.json, data/flavor_encounters.json
and the hardcoded FLAVOR_ENCOUNTERS list, after encounter_schema.normalise:
fields and types, the option rules (at most four visible, a free way out, no
reward beside a quiz), the karma rules P5-P12, virtue tags, the stakes table,
quizzes, references, disguises, and the road / chronicle lint.

Today's content predates the schema, so its known breaches are listed in
tests/encounter_legacy_allow.json (tag -> codes). That list must shrink to
empty by the end of Phase 3a; the test also fails on a stale entry.

    py -m tools.encounters.validate            # errors not on the allowlist
    py -m tools.encounters.validate --all      # every finding, allowlisted too
    py -m tools.encounters.validate --report   # +1 karma chances per block
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

ENC_KEYS = {
    'tag', 'name', 'symbol', 'color', 'sprite_id', 'text', 'options', 'proper_noun',
    'block', 'trigger_item', 'trigger_level_offset', 'min_level', 'max_level',
    'chain_after', 'role', 'stakes', 'band', 'person', 'requires', 'forbids',
    'text_variants', 'contested', 'stance', 'stance_note', 'tragedy', 'disguise',
    'callback_only', 'fallback_anchor', 'chronicle_meet', 'escorts', 'road_ok',
}
OUTCOME_KEYS = {
    'outcome', 'outcome_variants', 'karma', 'karma_kind', 'virtue', 'reward',
    'bonus_reward', 'cost', 'deeds', 'oath', 'oath_keep', 'oath_break',
    'oath_release', 'schedule', 'delayed', 'escort', 'person_status', 'thread',
    'thread_close', 'chronicle', 'fight', 'then',
}
OPTION_ONLY_KEYS = {
    'label', 'quiz', 'pass', 'fail', 'requires', 'forbids', 'hidden', 'hidden_group',
    'villain', 'side', 'naive', 'warning', 'road', 'fail_reward',
}
COST_TYPES = {
    'food', 'healing_potion', 'potion', 'scroll', 'weapon', 'gold', 'hp_percent',
    'max_hp', 'sp', 'hp', 'mp', 'random_item', 'triggered_item', 'accept_item',
    'spawn_deadite_ambush', 'hp_pct', 'sp_pct', 'mp_pct', 'max_hp_pct', 'gold_pct',
    'triggered_item_id', 'stat',
}
PCT_COSTS = {'hp_pct', 'sp_pct', 'mp_pct', 'max_hp_pct', 'gold_pct', 'hp_percent'}
REWARD_TYPES = {
    'gold', 'random_weapon', 'random_armor', 'random_shield', 'random_accessory',
    'random_potion', 'random_scroll', 'random_food', 'random_wand', 'stat',
    'specific_item', 'random_item', 'effect', 'hp_restore', 'sp_restore', 'mp_restore',
    'hp_restore_pct', 'sp_restore_pct', 'mp_restore_pct', 'enchant_weapon', 'message',
    'multi',
}
STAT_NAMES = ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')
ROAD_BANNED = ('karma', 'quiz', 'option', 'choose', 'press', 'light', 'medium', 'high',
               'stakes')


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
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return {k: set(v) for k, v in data.items() if not k.startswith('_')}


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
    for field, coef in spec.items():
        if field == 'flat':
            continue
        if field == 'amount' and 'amount' not in reward and 'min' in reward:
            val = (float(reward['min']) + float(reward.get('max', reward['min']))) / 2
        else:
            val = float(reward.get(field, 1 if field == 'count' else 0) or 0)
        v += float(coef) * val
    return v


def option_value(opt: dict, table: dict) -> float:
    """An option's material reward: the best branch it can lead to."""
    from encounter_schema import option_branches
    return max((reward_value(b.get('reward'), table) + reward_value(b.get('bonus_reward'), table)
                for b in option_branches(opt)), default=0.0)


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
    if label and _norm(label) and _norm(label) in _norm(hint):
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
        if not conditional and not o.get('cost') and not is_quiz(o) \
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
        elif not isinstance(o.get('outcome'), str):
            err('field', f'{where}: no outcome')
        if o.get('cost') is not None:
            _check_cost(err, where, o['cost'], stakes)
        for b in option_branches(o):
            for rk in ('reward', 'bonus_reward'):
                if b.get(rk) is not None:
                    _check_reward(err, where, b[rk])
            if b is not o and b.get('cost') is not None:
                if not (b is o.get('fail') and stakes == 'high') and not o.get('naive'):
                    err('stakes', f'{where}: an outcome cost only in a high-stakes fail '
                                  'or a naive option')
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
            if b.get('chronicle'):
                bad = _chron_lint(b['chronicle'])
                if bad:
                    err('chronicle_lint', f"{where}: {', '.join(bad)}")
            if b.get('then') not in (None, 'close', 'options'):
                err('field', f"{where}: then {b.get('then')!r}")
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
    if not free_exit:
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
            if abs(k) > 1:
                err('karma_size', f'{where}: karma {k:+d} (at most one point a choice)')
            if k > 0 and kind in ('constancy', 'recovery'):
                err('karma_kind', f'{where}: {kind} is engine-only')
            if k > 0 and kind == 'oath':
                err('karma_kind', f'{where}: an oath pays through oath_keep, not karma')
            if k < 0 and kind in karma.POSITIVE_GATED | karma.POSITIVE_UNGATED:
                err('karma_kind', f'{where}: negative karma with positive kind {kind!r}')
            if k > 0 and kind == 'forgo':
                _check_forgo(err, where, o, opts, table)
            if k > 0 and kind == 'judgment':
                if b is not o.get('pass') or not has_naive_sibling(enc, o):
                    err('judgment', f'{where}: judgment +1 only in a quiz pass with a '
                                    'naive sibling')
            if k > 0 and kind == 'stance':
                if not enc.get('stance') or o.get('side') != 'right':
                    err('stance', f'{where}: stance +1 needs an encounter stance and '
                                  "side 'right'")
                elif not (o.get('cost') or is_quiz(o)):
                    err('stance', f'{where}: the right side must carry a visible cost')
            v = b.get('virtue')
            if v is not None:
                if v == 'forgo':
                    _check_forgo(err, where, o, opts, table)
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
        if b.get('cost') or b.get('fight') or b.get('schedule'):
            return True
        for d in b.get('deeds') or ():
            did = d if isinstance(d, str) else (d or {}).get('id', '')
            if str(did).startswith(('lost.', 'wrong.')):
                return True
        ps = b.get('person_status')
        if (ps if isinstance(ps, str) else (ps or {}).get('status')) in ('lost', 'wronged'):
            return True
    return False


def _check_forgo(err, where, o, opts, table):
    mine = option_value(o, table)
    if not any(option_value(s, table) > mine for s in opts if s is not o and not s.get('requires')):
        err('forgo', f'{where}: forgo needs a visible sibling with a greater reward (P7)')


def _check_cost(err, where, cost, stakes):
    if not isinstance(cost, dict) or cost.get('type') not in COST_TYPES:
        err('cost', f'{where}: unknown cost {cost!r}')
        return
    if cost['type'] in PCT_COSTS:
        cap = {'light': 15, 'medium': 30}.get(stakes)
        if cap is not None and float(cost.get('amount', 0)) > cap:
            err('stakes', f"{where}: {cost['type']} {cost.get('amount')}% over the "
                          f'{stakes} cap of {cap}%')


def _check_reward(err, where, rw):
    if not isinstance(rw, dict) or rw.get('type') not in REWARD_TYPES:
        err('reward', f'{where}: unknown reward {rw!r}')
        return
    for sub in rw.get('rewards') or ():
        _check_reward(err, where, sub)


def _check_quiz(err, where, q, stakes, source, ctx, modes):
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
        ok = total <= 1 or (source == 'npc' and thr <= 2 and total <= 3)
        if not ok:
            err('stakes', f'{where}: a medium quiz is one question (anchors: 2 of 3)')
        if mode.startswith('escalator') or mode == 'chain':
            err('stakes', f'{where}: chains and escalators are for high stakes')
    if stakes == 'high' and q.get('max_chain') is not None and int(q['max_chain']) > 5:
        err('stakes', f'{where}: max_chain over 5')


def validate_all(encounters=None) -> list:
    encs = encounters if encounters is not None else load_all()
    ctx = {'subjects': _subjects(), 'quest_pieces': _quest_piece_ids(),
           'items': _item_ids(), 'rules': _rules()}
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
            for b in [o, o.get('pass') or {}, o.get('fail') or {}]:
                if isinstance(b.get('oath'), dict):
                    made.add(b['oath'].get('id'))
                for k in ('oath_keep', 'oath_break', 'oath_release'):
                    if b.get(k):
                        kept.append((enc['tag'], b[k]))
                if isinstance(b.get('thread'), dict):
                    threads.add(b['thread'].get('id'))
                if b.get('thread_close'):
                    closes.append((enc['tag'], b['thread_close']))
                for cb in b.get('schedule') or ():
                    if cb.get('encounter') not in seen:
                        out.append(Issue(enc['tag'], 'reference',
                                         f"schedule names unknown {cb.get('encounter')!r}"))
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
    return out


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


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    issues = validate_all()
    if '--report' in argv:
        for b, n in opportunities_report().items():
            print(f'block {b:2d}: {n} option(s) with a +1 path')
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
