"""
Monster behaviour, first wave (AI-1, 2026-11-19): the data the behaviours
read, written onto EXISTING kinds by their lore, and their tells.

Offline tooling (not loaded at runtime). Idempotent: every run sets the same
values; nothing is appended twice.

    py tools/content/monster_ai_pass_2026_11.py            # report
    py tools/content/monster_ai_pass_2026_11.py --write    # write the data

data/monsters.json keeps its layout (json indent 2, CRLF: the dump below
reproduces the file byte for byte); data/tells.json is edited as text, so its
compact lists stay as they are. New kinds are never added here (slice M adds
those at the end of monsters.json).

What each block is for, and the lore behind every choice, is in the comments
by it and in docs/systems/monsters.md, 'Monster behaviour, first wave'.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MONSTERS = ROOT / 'data' / 'monsters.json'
TELLS = ROOT / 'data' / 'tells.json'

# ---------------------------------------------------------------------------
# Kind fields: {kind: {field: value}} (a value None removes the field)
# ---------------------------------------------------------------------------
KIND_FIELDS: dict = {}

# Attack fields: {(kind, attack name): {field: value}}
ATTACK_FIELDS: dict = {}

# ---------------------------------------------------------------------------
# Tells (data/tells.json): key -> (after which key in 'order', entry)
# ---------------------------------------------------------------------------
TELLS_NEW = {
    'breath_recharge': ('pull_chance', {
        'sign': "{The}'s chest heaves like a bellows.",
        'does': "{He} breathes, then must draw breath again: for a few turns {he} has only tooth and claw.",
        'counter': "Close in while {he} draws breath, or keep stone between you until {he} has spent it.",
    }),
    'heals_allies': ('summon_kind', {
        'sign': "{The} stays close behind the others, eyeing every wound.",
        'does': "{He} mends a badly hurt friend, then must rest {his} voice a few turns before the next.",
        'counter': "Kill {him} first, or finish the friend {he} has just mended before {he} can mend again.",
    }),
}
# Tells whose words change (a rule changed): key -> {part: text}
TELLS_CHANGED = {
    'summon_kind': {
        'does': "{He} can call others to {him}, a few at a time.",
        'counter': "Strike {him} while {he} chants: a blow breaks the call. Kill what {he} calls, and {he} must call again.",
    },
}


def _dump_monsters(d) -> str:
    return (json.dumps(d, indent=2, ensure_ascii=False) + '\n').replace('\n', '\r\n')


def apply_monsters(d: dict) -> list:
    changes = []
    for kind, fields in KIND_FIELDS.items():
        m = d.get(kind)
        if not isinstance(m, dict):
            raise SystemExit(f"no kind {kind!r} in monsters.json")
        for k, v in fields.items():
            if v is None:
                if k in m:
                    del m[k]
                    changes.append(f"{kind}: -{k}")
            elif m.get(k) != v:
                m[k] = v
                changes.append(f"{kind}: {k}={v!r}")
    for (kind, aname), fields in ATTACK_FIELDS.items():
        m = d.get(kind)
        if not isinstance(m, dict):
            raise SystemExit(f"no kind {kind!r} in monsters.json")
        atk = next((a for a in m.get('attacks') or () if a.get('name') == aname), None)
        if atk is None:
            raise SystemExit(f"{kind} has no attack {aname!r}")
        for k, v in fields.items():
            if v is None:
                if k in atk:
                    del atk[k]
                    changes.append(f"{kind}/{aname}: -{k}")
            elif atk.get(k) != v:
                atk[k] = v
                changes.append(f"{kind}/{aname}: {k}={v!r}")
    return changes


def _entry_text(key: str, e: dict) -> str:
    body = ',\r\n'.join(f'      {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}'
                        for k, v in e.items())
    return f'    {json.dumps(key)}: {{\r\n{body}\r\n    }}'


def apply_tells(raw: str) -> tuple:
    """(new text, changes). Text edits keep the file's own layout."""
    d = json.loads(raw)
    changes = []
    for key, (after, e) in TELLS_NEW.items():
        if key in d['order']:
            continue
        if after not in d['order']:
            raise SystemExit(f"tells order has no {after!r}")
        old = f'"{after}",'
        if raw.count(old) != 1:
            raise SystemExit(f"tells order: {old} found {raw.count(old)} times")
        raw = raw.replace(old, f'"{after}", "{key}",', 1)
        # the entry goes last in 'effects'
        tail = raw.rstrip()
        assert tail.endswith('}\r\n}') or tail.endswith('}\n}') or tail.endswith('}')
        i = raw.rindex('    }\r\n  }')
        raw = raw[:i] + '    },\r\n' + _entry_text(key, e) + raw[i + len('    }'):]
        changes.append(f"tell {key}")
    d = json.loads(raw)
    for key, parts in TELLS_CHANGED.items():
        for part, text in parts.items():
            cur = d['effects'][key].get(part)
            if cur == text:
                continue
            old = f'"{part}": {json.dumps(cur, ensure_ascii=False)}'
            seg_start = raw.index(f'    "{key}": {{')
            seg_end = raw.index('    }', seg_start)
            seg = raw[seg_start:seg_end]
            if seg.count(old) != 1:
                raise SystemExit(f"tell {key}.{part}: old text not found once")
            seg = seg.replace(old, f'"{part}": {json.dumps(text, ensure_ascii=False)}')
            raw = raw[:seg_start] + seg + raw[seg_end:]
            changes.append(f"tell {key}.{part}")
    json.loads(raw)
    return raw, changes


def main(argv) -> int:
    write = '--write' in argv
    raw_m = MONSTERS.read_text(encoding='utf-8')
    d = json.loads(raw_m)
    ch_m = apply_monsters(d)
    raw_t = TELLS.read_bytes().decode('utf-8')
    new_t, ch_t = apply_tells(raw_t)
    for c in ch_m + ch_t:
        print(c)
    print(f"{len(ch_m)} monster changes, {len(ch_t)} tell changes")
    if write:
        if ch_m:
            with open(MONSTERS, 'w', encoding='utf-8', newline='') as f:
                f.write(_dump_monsters(d))
        if ch_t:
            with open(TELLS, 'w', encoding='utf-8', newline='') as f:
                f.write(new_t)
        print("written")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
