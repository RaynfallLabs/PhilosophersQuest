"""
Remove intra-subject duplicate questions from all question files.

Strategy:
  - Same question text within the same subject = duplicate.
  - When duplicates exist: keep the one with the HIGHER tier (more precise answer),
    or the first occurrence if tiers are equal.
  - Also fix: replace Unicode multiplication sign (×, U+00D7) with ASCII 'x'
    to prevent font rendering failures.
  - Reports all changes made.
"""
import json, os, re

QDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'questions')

def fix_unicode(text: str) -> str:
    """Replace known-problematic Unicode chars with ASCII equivalents."""
    if not isinstance(text, str):
        return text
    return (text
        .replace('\u00d7', 'x')     # × (multiplication sign) -> x
        .replace('\u00f7', '/')     # ÷ (division sign) -> /
        .replace('\u2212', '-')     # − (minus sign) -> -
        .replace('\u2260', '!=')    # ≠ -> !=
        .replace('\u2264', '<=')    # ≤ -> <=
        .replace('\u2265', '>=')    # ≥ -> >=
        .replace('\u03b1', 'alpha') # α
        .replace('\u03b2', 'beta')  # β
        .replace('\u03b3', 'gamma') # γ
        .replace('\u03b4', 'delta') # δ
        .replace('\u03c0', 'pi')    # π
        .replace('\u03a9', 'Omega') # Ω
        .replace('\u221e', 'inf')   # ∞
        .replace('\u2248', '~=')    # ≈
        .replace('\u00b0', ' deg')  # ° (degree)
        .replace('\u00b2', '^2')    # ²
        .replace('\u00b3', '^3')    # ³
        .replace('\u00bd', '1/2')   # ½
        .replace('\u00bc', '1/4')   # ¼
        .replace('\u00be', '3/4')   # ¾
        .replace('\u2019', "'")     # ' (right single quote)
        .replace('\u2018', "'")     # ' (left single quote)
        .replace('\u201c', '"')     # " (left double quote)
        .replace('\u201d', '"')     # " (right double quote)
        .replace('\u2014', '--')    # — (em dash)
        .replace('\u2013', '-')     # – (en dash)
        .replace('\u00e9', 'e')     # é
        .replace('\u00e8', 'e')     # è
        .replace('\u00ea', 'e')     # ê
        .replace('\u00f3', 'o')     # ó
        .replace('\u00fa', 'u')     # ú
        .replace('\u00e1', 'a')     # á
        .replace('\u00ed', 'i')     # í
        .replace('\u00fc', 'u')     # ü
        .replace('\u00e4', 'a')     # ä
        .replace('\u00f6', 'o')     # ö
        .replace('\u00e0', 'a')     # à
        .replace('\u00e2', 'a')     # â
        .replace('\u00ee', 'i')     # î
        .replace('\u00f4', 'o')     # ô
        .replace('\u00fb', 'u')     # û
        .replace('\u00e7', 'c')     # ç
        .replace('\u00df', 'ss')    # ß
        .replace('\u00f1', 'n')     # ñ
        .replace('\u00e6', 'ae')    # æ
        .replace('\u00f8', 'o')     # ø
        .replace('\u00e5', 'a')     # å
        .replace('\u0107', 'c')     # ć
        .replace('\u015b', 's')     # ś
        .replace('\u00c9', 'E')     # É
        .replace('\u00d3', 'O')     # Ó
        .replace('\u00da', 'U')     # Ú
        .replace('\u00c1', 'A')     # Á
        .replace('\u00cd', 'I')     # Í
    )

def fix_question(q: dict) -> dict:
    """Apply unicode fixes to all string fields in a question."""
    for key, val in q.items():
        if isinstance(val, str):
            q[key] = fix_unicode(val)
        elif isinstance(val, list):
            q[key] = [fix_unicode(v) if isinstance(v, str) else v for v in val]
    return q

total_removed = 0
total_unicode_fixed = 0

for fname in sorted(os.listdir(QDIR)):
    if not fname.endswith('.json'):
        continue
    subj = fname.replace('.json', '')
    path = os.path.join(QDIR, fname)

    with open(path, encoding='utf-8') as f:
        qs = json.load(f)

    original_count = len(qs)

    # Apply unicode fixes and track changes
    unicode_fixes = 0
    fixed_qs = []
    for q in qs:
        q_str = json.dumps(q, ensure_ascii=False)
        q_fixed = fix_question(dict(q))
        if json.dumps(q_fixed, ensure_ascii=False) != q_str:
            unicode_fixes += 1
        fixed_qs.append(q_fixed)
    qs = fixed_qs

    # Deduplicate: keep highest-tier version of each question text
    seen: dict[str, int] = {}   # normalized_text -> index of kept entry
    keep_indices: set[int] = set()
    removed_info = []

    for i, q in enumerate(qs):
        text = q.get('question', '').strip().lower()
        tier = q.get('tier', 1)

        if text not in seen:
            seen[text] = i
            keep_indices.add(i)
        else:
            prev_i = seen[text]
            prev_tier = qs[prev_i].get('tier', 1)

            if tier > prev_tier:
                # New one is higher tier -- replace kept entry
                keep_indices.discard(prev_i)
                keep_indices.add(i)
                seen[text] = i
                removed_info.append((prev_i, qs[prev_i].get('tier',1), 'replaced by higher-tier version'))
            else:
                # Keep existing, discard this one
                removed_info.append((i, tier, f'dup of idx {prev_i}'))

    new_qs = [qs[i] for i in sorted(keep_indices)]
    removed = original_count - len(new_qs)
    total_removed += removed
    total_unicode_fixed += unicode_fixes

    if removed > 0 or unicode_fixes > 0:
        print(f'{subj}: {original_count} -> {len(new_qs)} q  '
              f'(-{removed} dupes, {unicode_fixes} unicode fixes)')

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(new_qs, f, indent=2, ensure_ascii=False)

print(f'\nTotal questions removed: {total_removed}')
print(f'Total unicode fixes applied: {total_unicode_fixed}')
