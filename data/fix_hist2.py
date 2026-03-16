import json

data = json.load(open('data/questions/history.json', encoding='utf-8'))

replacements = {
    403: (1, "What ancient civilization built the Colosseum in Rome?",
          "Ancient Rome",
          ["Ancient Greece", "Ancient Egypt", "Ancient Rome", "Byzantine Empire"]),

    397: (1, "Which ancient empire was ruled by pharaohs?",
          "Ancient Egypt",
          ["Babylon", "Persia", "Ancient Egypt", "Assyria"]),
}

for idx, (tier, question, answer, choices) in replacements.items():
    data[idx]['tier'] = tier
    data[idx]['question'] = question
    data[idx]['answer'] = answer
    data[idx]['choices'] = choices

with open('data/questions/history.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print('Saved')

# Verify
data2 = json.load(open('data/questions/history.json', encoding='utf-8'))
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
