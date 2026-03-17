import json, os, re

QDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'questions')

for fname in sorted(os.listdir(QDIR)):
    if not fname.endswith('.json'): continue
    subj = fname.replace('.json','')
    path = os.path.join(QDIR, fname)
    with open(path, encoding='utf-8') as f:
        qs = json.load(f)

    issues = []
    for i, q in enumerate(qs):
        text = json.dumps(q, ensure_ascii=False)
        # Find chars outside printable ASCII and basic extended latin
        bad = [(m.start(), m.group()) for m in re.finditer(r'[^\x09\x0a\x0d\x20-\x7e]', text)]
        if bad:
            chars = list(set(c for _,c in bad))
            preview = text[:100].encode('ascii','replace').decode()
            issues.append((i, chars, preview))

    if issues:
        print(f'{subj}: {len(issues)} questions with non-ASCII chars')
        for idx, chars, preview in issues[:5]:
            hex_chars = [f'U+{ord(c):04X}={repr(c)}' for c in chars]
            print(f'  idx={idx}: {hex_chars}')
    else:
        print(f'{subj}: CLEAN')
