import json, os
from collections import defaultdict

for fname in sorted(os.listdir('data/questions')):
    if not fname.endswith('.json'): continue
    subj = fname.replace('.json','')
    with open(f'data/questions/{fname}', encoding='utf-8') as f:
        qs = json.load(f)

    seen = defaultdict(list)
    for i, q in enumerate(qs):
        text = q.get('question','').strip().lower()
        seen[text].append((i, q))

    dupes = {t: locs for t, locs in seen.items() if len(locs) > 1}
    if not dupes:
        continue
    print(f'=== {subj.upper()} ({len(dupes)} duplicate texts) ===')
    for text, locs in list(dupes.items())[:6]:
        print(f'  "{text[:70]}"')
        for idx, q in locs:
            ans = q.get('answer','?')
            print(f'    idx={idx} T{q.get("tier",1)} ans={repr(ans)}')
    if len(dupes) > 6:
        print(f'  ... ({len(dupes)-6} more)')
    print()
