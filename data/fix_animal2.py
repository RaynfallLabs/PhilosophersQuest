import json

data = json.load(open('data/questions/animal.json', encoding='utf-8'))

# Fix the 3 remaining dupes by changing indices 98, 110, 144 to different questions
replacements = {
    98: (1, "What is a group of kangaroos called?",
         "Mob",
         ["Mob", "Pack", "Herd", "Colony"]),

    110: (1, "Which mammal lays eggs?",
          "Platypus",
          ["Platypus", "Bat", "Shrew", "Opossum"]),

    144: (1, "What is a group of ravens called?",
          "Unkindness",
          ["Unkindness", "Murder", "Flock", "Colony"]),
}

# Verify these won't create new dupes
existing = set(q['question'].strip().lower() for i, q in enumerate(data) if i not in replacements)
for idx, (tier, question, answer, choices) in replacements.items():
    key = question.strip().lower()
    if key in existing:
        print(f'CONFLICT at idx {idx}: "{question}" already exists!')
    else:
        print(f'OK: idx {idx} -> "{question}"')

for idx, (tier, question, answer, choices) in replacements.items():
    data[idx]['tier'] = tier
    data[idx]['question'] = question
    data[idx]['answer'] = answer
    data[idx]['choices'] = choices

with open('data/questions/animal.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print('Saved')

# Verify
data2 = json.load(open('data/questions/animal.json', encoding='utf-8'))
seen2 = {}
dupes2 = []
for i, q in enumerate(data2):
    key = q['question'].strip().lower()
    if key in seen2:
        dupes2.append((seen2[key]+1, i+1, q['tier'], q['question'][:60]))
    else:
        seen2[key] = i

from collections import Counter
tiers = Counter(q['tier'] for q in data2)
print(f'Total: {len(data2)}, Tiers: {dict(sorted(tiers.items()))}')
print(f'Remaining dupes: {len(dupes2)}')
for d in dupes2:
    print(f'  {d[0]}&{d[1]} (t{d[2]}): {d[3]}')
