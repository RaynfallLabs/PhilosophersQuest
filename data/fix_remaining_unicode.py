"""Find and fix any remaining non-ASCII characters in question files."""
import json, os, re

QDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'questions')

# Extended unicode replacement table
EXTRA_REPLACEMENTS = {
    '\u2192': '->',    # →
    '\u2190': '<-',    # ←
    '\u2194': '<->',   # ↔
    '\u2191': '^',     # ↑
    '\u2193': 'v',     # ↓
    '\u00b1': '+/-',   # ±
    '\u00b5': 'u',     # µ (micro)
    '\u03b1': 'alpha',
    '\u03b2': 'beta',
    '\u03b3': 'gamma',
    '\u03b4': 'delta',
    '\u03b5': 'epsilon',
    '\u03b8': 'theta',
    '\u03bb': 'lambda',
    '\u03bc': 'mu',
    '\u03c0': 'pi',
    '\u03c3': 'sigma',
    '\u03c9': 'omega',
    '\u03a3': 'Sigma',
    '\u03a9': 'Omega',
    '\u03a6': 'Phi',
    '\u03a8': 'Psi',
    '\u221a': 'sqrt',  # √
    '\u221e': 'inf',   # ∞
    '\u2248': '~=',    # ≈
    '\u2260': '!=',    # ≠
    '\u2264': '<=',    # ≤
    '\u2265': '>=',    # ≥
    '\u2282': 'subset',# ⊂
    '\u2229': 'intersect', # ∩
    '\u222a': 'union', # ∪
    '\u2211': 'sum',   # ∑
    '\u222b': 'integral', # ∫
    '\u00d7': 'x',     # ×
    '\u00f7': '/',     # ÷
    '\u2212': '-',     # −
    '\u00b2': '^2',    # ²
    '\u00b3': '^3',    # ³
    '\u00b0': ' deg',  # °
    '\u00bd': '1/2',   # ½
    '\u00bc': '1/4',   # ¼
    '\u00be': '3/4',   # ¾
    '\u2019': "'",     # '
    '\u2018': "'",     # '
    '\u201c': '"',     # "
    '\u201d': '"',     # "
    '\u2014': '--',    # —
    '\u2013': '-',     # –
    '\u2026': '...',   # …
    '\u00e9': 'e', '\u00e8': 'e', '\u00ea': 'e', '\u00eb': 'e',
    '\u00f3': 'o', '\u00f2': 'o', '\u00f4': 'o', '\u00f6': 'o',
    '\u00fa': 'u', '\u00f9': 'u', '\u00fb': 'u', '\u00fc': 'u',
    '\u00e1': 'a', '\u00e0': 'a', '\u00e2': 'a', '\u00e4': 'a', '\u00e5': 'a',
    '\u00ed': 'i', '\u00ec': 'i', '\u00ee': 'i', '\u00ef': 'i',
    '\u00e7': 'c', '\u00df': 'ss', '\u00f1': 'n', '\u00f8': 'o',
    '\u00e6': 'ae', '\u0107': 'c', '\u015b': 's', '\u017a': 'z',
    '\u00c9': 'E', '\u00c0': 'A', '\u00c1': 'A', '\u00c2': 'A',
    '\u00c4': 'A', '\u00c5': 'A', '\u00c7': 'C', '\u00c8': 'E',
    '\u00ca': 'E', '\u00cd': 'I', '\u00ce': 'I', '\u00d3': 'O',
    '\u00d4': 'O', '\u00d6': 'O', '\u00da': 'U', '\u00db': 'U',
    '\u00dc': 'U', '\u00d1': 'N', '\u00d8': 'O',
    '\u0141': 'L', '\u0142': 'l', '\u017c': 'z', '\u017b': 'Z',
    '\u0160': 'S', '\u0161': 's', '\u017e': 'z', '\u017d': 'Z',
}

def fix_str(s):
    if not isinstance(s, str):
        return s
    for bad, good in EXTRA_REPLACEMENTS.items():
        s = s.replace(bad, good)
    # catch-all: replace remaining non-ASCII with '?'
    return ''.join(c if ord(c) < 128 else '?' for c in s)

total_fixed = 0
for fname in sorted(os.listdir(QDIR)):
    if not fname.endswith('.json'): continue
    path = os.path.join(QDIR, fname)
    with open(path, encoding='utf-8') as f:
        qs = json.load(f)

    fixed = 0
    for q in qs:
        for key, val in q.items():
            if isinstance(val, str):
                new = fix_str(val)
                if new != val:
                    q[key] = new
                    fixed += 1
            elif isinstance(val, list):
                new_list = [fix_str(v) for v in val]
                if new_list != val:
                    q[key] = new_list
                    fixed += new_list.count(val) + 1

    if fixed:
        print(f'{fname}: {fixed} fields fixed')
        total_fixed += fixed
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(qs, f, indent=2, ensure_ascii=False)

# Final check: any remaining?
remaining = 0
for fname in sorted(os.listdir(QDIR)):
    if not fname.endswith('.json'): continue
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    count = sum(1 for c in raw if ord(c) > 127)
    remaining += count

print(f'\nTotal fields fixed: {total_fixed}')
print(f'Remaining non-ASCII chars (should be 0): {remaining}')
