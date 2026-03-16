import json

data = json.load(open('data/questions/history.json', encoding='utf-8'))

replacements = {
    394: (1, "In what year did the Berlin Wall fall?",
          "1989",
          ["1985", "1989", "1991", "1993"]),

    395: (1, "Which country first granted women the right to vote nationally?",
          "New Zealand",
          ["Australia", "United Kingdom", "United States", "New Zealand"]),

    396: (1, "What was the name of the ship that carried the Pilgrims to America in 1620?",
          "Mayflower",
          ["Santa Maria", "Pinta", "Mayflower", "Victory"]),

    397: (1, "Who was the first Emperor of China?",
          "Qin Shi Huang",
          ["Liu Bang", "Qin Shi Huang", "Sun Yat-sen", "Kublai Khan"]),

    403: (1, "In what year did the French Revolution begin?",
          "1789",
          ["1776", "1789", "1804", "1815"]),

    404: (1, "What was the name of the ancient Egyptian writing system using pictorial symbols?",
          "Hieroglyphics",
          ["Cuneiform", "Linear A", "Hieroglyphics", "Demotic"]),

    413: (2, "Which country was the first to abolish slavery nationally?",
          "Haiti",
          ["United Kingdom", "France", "United States", "Haiti"]),
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
