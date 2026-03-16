import json

data = json.load(open('data/questions/geography.json', encoding='utf-8'))

replacements = {
    327: (2, "What is the name of the large bay that indents the coast of northern Canada?",
          "Hudson Bay",
          ["Baffin Bay", "James Bay", "Hudson Bay", "Foxe Basin"]),

    333: (3, "What is the term for the boundary between fresh water and salt water in an estuary?",
          "Halocline",
          ["Thermocline", "Halocline", "Pycnocline", "Estuarine front"]),
}

for idx, (tier, question, answer, choices) in replacements.items():
    data[idx]['tier'] = tier
    data[idx]['question'] = question
    data[idx]['answer'] = answer
    data[idx]['choices'] = choices

with open('data/questions/geography.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print('Saved')

# Verify
data2 = json.load(open('data/questions/geography.json', encoding='utf-8'))
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
