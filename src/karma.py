"""The single karma entry point (DEEDS_KARMA_DESIGN.md section 3.1).

Karma stays one integer, -10..+10 (``Game.karma``). Every change in ``src/``
goes through :func:`adjust`; ``tests/test_single_karma_entry_point.py``
fails on any other write.

Feature flag ``data/karma_rules.json: gate_enabled`` (shipped ON since the
story content, 2026-10-17):

* **on**: at most +1 per 10-floor block from encounters, oaths and
  choices (one slot per block, first come first served); a kept oath fills
  the earliest open slot from the block it was sworn in; constancy pays at
  most ``constancy_cap`` (+2) per run, once per rule. Untyped ('legacy')
  karma is refused.
* **off** (kept only as a switch): every kind applies exactly as it did
  before the redesign, with each old site's own clamp (the Penitent's Blade
  only below zero and never above it; everything else -10..+10). Block
  slots and the ledger are still written. Nothing is absorbed.

Every block is ``karma_block(deepest_floor_reached)``: an award made after
walking back upstairs still lands in the deepest block reached.
"""
from __future__ import annotations

import json

import deeds

POSITIVE_GATED = frozenset({'forgo', 'judgment', 'oath', 'stance'})
POSITIVE_UNGATED = frozenset({'constancy', 'recovery'})
# No 'reckless': naive kindness is never negative karma (Brandon, decision 9).
# It carries material consequences authored in the outcome instead.
NEGATIVE = frozenset({'betray', 'cruelty', 'stance_wrong', 'sacrilege', 'pattern'})
LEGACY = 'legacy'      # the old untyped karma; only while the gate is off
KINDS = POSITIVE_GATED | POSITIVE_UNGATED | NEGATIVE | {LEGACY}

KARMA_MIN, KARMA_MAX = -10, 10

_RULES: dict | None = None
_EVALUATING = False


def rules() -> dict:
    global _RULES
    if _RULES is None:
        from paths import data_path
        with open(data_path('data', 'karma_rules.json'), encoding='utf-8') as f:
            _RULES = json.load(f)
    return _RULES


def gate_enabled() -> bool:
    return bool(rules().get('gate_enabled', False))


def _clamp(v: int) -> int:
    return max(KARMA_MIN, min(KARMA_MAX, v))


def _where(game):
    """(floor, deepest, block, turn) for ``game`` (duck-typed)."""
    return deeds.where(game)


def _earliest_open(slots: dict, lo: int, hi: int):
    for b in range(max(1, lo), hi + 1):
        if b not in slots:
            return b
    return None


def adjust(game, delta: int, *, kind: str, source: str,
           made_block: int | None = None) -> int:
    """Apply a karma change and return the delta actually applied."""
    if kind not in KINDS:
        raise ValueError(f'unknown karma kind: {kind!r}')
    delta = int(delta or 0)
    reg = deeds.ensure_register(game)
    kreg = reg['karma']
    slots = kreg['slots']
    floor, deepest, block, turn = _where(game)
    try:
        cur = int(getattr(game, 'karma', 0) or 0)
    except (TypeError, ValueError):
        cur = 0
    gate = gate_enabled()
    slot_block = None          # the block this award fills (or would fill)

    if kind == 'recovery':
        # The Penitent's Blade balances the ledger but cannot redeem you.
        new = min(0, cur + delta) if (cur < 0 and delta > 0) else cur
    elif delta > 0 and kind in POSITIVE_GATED | {LEGACY}:
        if kind == 'oath':
            lo = int(made_block) if made_block is not None else block
            slot_block = _earliest_open(slots, lo, block)
        else:
            slot_block = block if block not in slots else None
        if gate:
            if kind == LEGACY:
                raise ValueError('legacy karma is not allowed once the gate is on')
            new = _clamp(cur + 1) if slot_block is not None else cur
        else:
            new = _clamp(cur + delta)
    elif kind == 'constancy':
        # Engine-only: evaluate_patterns claims the rule (and enforces the
        # run cap) before it calls here.
        cap = int(rules().get('constancy_cap', 2))
        if gate and delta > 0 and len(kreg['constancy']) <= cap:
            new = _clamp(cur + 1)
        else:
            new = cur
    else:
        new = _clamp(cur + delta)

    write_failed = False
    if new != cur:
        try:
            game.karma = new
        except Exception:
            # The write failed: nothing was applied, so neither the ledger
            # nor the slot may say it was (CODE-09).
            from game_log import log_error
            log_error(f'karma.adjust: could not write karma for {source!r}')
            new = cur
            write_failed = True
    applied = new - cur
    # With the gate off the slot is recorded for every positive award, even
    # one the +10 ceiling swallowed: the block was earned all the same.
    if slot_block is not None and not write_failed and (applied > 0 or not gate):
        slots[slot_block] = source
    kreg['ledger'].append({
        'seq': deeds.next_seq(reg), 'floor': floor, 'block': block, 'kind': kind,
        'source': source, 'requested': delta, 'applied': applied,
    })
    if gate:
        evaluate_patterns(game)
    return applied


def evaluate_patterns(game) -> list:
    """Pay any constancy or negative-pattern rule that has just completed,
    once per rule, and return the ids paid. Runs only with the gate on; with
    it off no karma may change beyond what the old sites gave."""
    global _EVALUATING
    if not gate_enabled() or _EVALUATING:
        return []
    reg = deeds.ensure_register(game)
    kreg = reg['karma']
    r = rules()
    cap = int(r.get('constancy_cap', 2))
    paid = []
    _EVALUATING = True
    try:
        for rule in r.get('constancy', ()):
            rid = rule['id']
            if rid in kreg['constancy'] or len(kreg['constancy']) >= cap:
                continue
            if _rule_met(reg, rule):
                kreg['constancy'].append(rid)         # claimed before paying
                adjust(game, 1, kind='constancy', source=f'constancy:{rid}')
                paid.append(rid)
                _soul_line(game, rule)
        for rule in r.get('patterns_neg', ()):
            rid = rule['id']
            if rid in kreg['patterns_neg']:
                continue
            if _rule_met(reg, rule):
                kreg['patterns_neg'].append(rid)
                adjust(game, int(rule.get('karma', -1)), kind='pattern', source=f'pattern:{rid}')
                paid.append(rid)
                _soul_line(game, rule)
    finally:
        _EVALUATING = False
    return paid


def _rule_met(reg: dict, rule: dict) -> bool:
    tag = rule['tag']
    if deeds.count(reg, tag=tag) < int(rule.get('min', 1)):
        return False
    if len(deeds.blocks_with(reg, tag=tag)) < int(rule.get('min_blocks', 1)):
        return False
    return not any(deeds.count(reg, tag=t) for t in rule.get('none_tags', ()))


def _soul_line(game, rule: dict) -> None:
    text = rule.get('chronicle')
    if not text:
        return
    try:
        import chronicle
        chronicle.chron(game, 'soul', text, once=f"rule:{rule['id']}")
    except Exception:
        from game_log import log_error
        log_error(f"karma._soul_line: could not write the line for rule {rule.get('id')!r}")
