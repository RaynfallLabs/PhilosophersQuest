"""
Apply all review2 agent changes to question files.
Order: rewrites first (on original indices), then removes (reverse order), then adds.
"""
import json, os, sys

QDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'questions')
RDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'review2_results')

SUBJECTS = [
    'animal', 'cooking', 'economics', 'geography', 'grammar',
    'history', 'math', 'philosophy', 'science', 'theology', 'trivia'
]

def fix_ascii(s):
    if not isinstance(s, str):
        return s
    replacements = {
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u2014': '--', '\u2013': '-', '\u2026': '...', '\u2022': '*',
        '\u00d7': 'x', '\u00f7': '/', '\u2212': '-', '\u00b2': '^2',
        '\u00b3': '^3', '\u00b0': ' deg', '\u00b1': '+/-',
        '\u221a': 'sqrt', '\u221e': 'inf', '\u2248': '~=',
        '\u2260': '!=', '\u2264': '<=', '\u2265': '>=',
        '\u2192': '->', '\u2190': '<-', '\u2194': '<->',
        '\u03b1': 'alpha', '\u03b2': 'beta', '\u03b3': 'gamma',
        '\u03b4': 'delta', '\u03c0': 'pi', '\u03c3': 'sigma',
        '\u03bc': 'mu', '\u03bb': 'lambda', '\u03a9': 'Omega',
        '\u00e9': 'e', '\u00e8': 'e', '\u00ea': 'e', '\u00eb': 'e',
        '\u00f3': 'o', '\u00f2': 'o', '\u00f4': 'o', '\u00f6': 'o',
        '\u00fa': 'u', '\u00f9': 'u', '\u00fb': 'u', '\u00fc': 'u',
        '\u00e1': 'a', '\u00e0': 'a', '\u00e2': 'a', '\u00e4': 'a',
        '\u00ed': 'i', '\u00ec': 'i', '\u00ee': 'i', '\u00ef': 'i',
        '\u00e7': 'c', '\u00df': 'ss', '\u00f1': 'n',
        '\u00c9': 'E', '\u00c0': 'A', '\u00c1': 'A', '\u00c7': 'C',
        '\u00d1': 'N', '\u00d6': 'O', '\u00dc': 'U',
        '\u2011': '-', '\u00a0': ' ', '\u00ab': '"', '\u00bb': '"',
        '\u2039': "'", '\u203a': "'", '\u2032': "'", '\u2033': '"',
    }
    for bad, good in replacements.items():
        s = s.replace(bad, good)
    return ''.join(c if ord(c) < 128 else '?' for c in s)

def fix_question(q):
    out = {}
    for k, v in q.items():
        if isinstance(v, str):
            out[k] = fix_ascii(v)
        elif isinstance(v, list):
            out[k] = [fix_ascii(x) if isinstance(x, str) else x for x in v]
        else:
            out[k] = v
    return out

total_removed = 0
total_rewritten = 0
total_added = 0

for subj in SUBJECTS:
    qpath = os.path.join(QDIR, f'{subj}.json')
    rpath = os.path.join(RDIR, f'{subj}.json')

    with open(qpath, encoding='utf-8') as f:
        qs = json.load(f)
    with open(rpath, encoding='utf-8') as f:
        review = json.load(f)

    orig_count = len(qs)

    # 1. Apply rewrites first (original indices still valid)
    rewrites = review.get('rewrite', [])
    rewrite_count = 0
    for r in rewrites:
        idx = r.get('index')
        field = r.get('field')
        new_val = r.get('new_value')
        if idx is None or field is None or new_val is None:
            continue
        if idx >= len(qs):
            continue
        if isinstance(new_val, str):
            new_val = fix_ascii(new_val)
        elif isinstance(new_val, list):
            new_val = [fix_ascii(x) if isinstance(x, str) else x for x in new_val]
        qs[idx][field] = new_val
        rewrite_count += 1

    # 2. Remove in reverse index order (prevents index shifting)
    removes = review.get('remove', [])
    remove_indices = sorted(set(r['index'] for r in removes if 'index' in r and r['index'] < len(qs)), reverse=True)
    for idx in remove_indices:
        qs.pop(idx)

    # 3. Add new questions at end
    adds = review.get('add', [])
    add_count = 0
    for a in adds:
        # Validate: must have question, answer, choices (4 items), tier
        q_text = a.get('question', '').strip()
        ans = a.get('answer', '').strip()
        choices = a.get('choices', [])
        tier = a.get('tier', 1)
        if not q_text or not ans or len(choices) != 4:
            continue
        if ans not in choices:
            continue
        new_q = fix_question({
            'question': q_text,
            'answer': ans,
            'choices': choices,
            'tier': tier
        })
        qs.append(new_q)
        add_count += 1

    # Fix ASCII on all existing questions
    qs = [fix_question(q) for q in qs]

    # Save
    with open(qpath, 'w', encoding='utf-8') as f:
        json.dump(qs, f, indent=2, ensure_ascii=False)

    removed = len(remove_indices)
    total_removed += removed
    total_rewritten += rewrite_count
    total_added += add_count

    print(f'{subj:15s}: {orig_count:4d} -> {len(qs):4d} '
          f'(removed {removed:3d}, rewritten {rewrite_count:3d} fields, added {add_count:3d})')

print(f'\nTotals: removed={total_removed}, rewritten={total_rewritten} fields, added={total_added}')
