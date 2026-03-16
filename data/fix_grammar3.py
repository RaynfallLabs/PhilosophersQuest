import json

data = json.load(open('data/questions/grammar.json', encoding='utf-8'))

# Check current state of dupes
seen = {}
dupes = []
for i, q in enumerate(data):
    key = q['question'].strip().lower()
    if key in seen:
        dupes.append((seen[key], i, q['tier'], q['question'][:70]))
    else:
        seen[key] = i
print('Current dupes:')
for d in dupes:
    print(f'  idx {d[0]}&{d[1]} (t{d[2]}): {d[3]}')
print()
