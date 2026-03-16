import json

data = json.load(open('data/questions/geography.json', encoding='utf-8'))

replacements = {
    321: (2, "What is the name of the peninsula that forms most of Denmark?",
          "Jutland",
          ["Scandinavian Peninsula", "Jutland", "Kola Peninsula", "Iberian Peninsula"]),

    322: (2, "Which country has more lakes than any other in the world?",
          "Canada",
          ["Finland", "Russia", "Canada", "Sweden"]),

    327: (2, "What is the largest island in the Mediterranean Sea?",
          "Sicily",
          ["Sardinia", "Corsica", "Cyprus", "Sicily"]),

    329: (2, "What is the name of the sea between Norway, Sweden, and Finland?",
          "Baltic Sea",
          ["North Sea", "Norwegian Sea", "Barents Sea", "Baltic Sea"]),

    331: (3, "Which Central American country has no army?",
          "Costa Rica",
          ["Panama", "Belize", "Costa Rica", "Nicaragua"]),

    333: (3, "What is the largest country in Africa by area?",
          "Algeria",
          ["Sudan", "Democratic Republic of Congo", "Libya", "Algeria"]),

    334: (3, "What is the name of the body of water that separates Madagascar from Africa?",
          "Mozambique Channel",
          ["Somali Sea", "Mozambique Channel", "Zanzibar Channel", "Madagascar Strait"]),
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
for d in dupes2:
    print(f'  {d[0]}&{d[1]} (t{d[2]}): {d[3]}')
