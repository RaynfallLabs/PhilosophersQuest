import json

data = json.load(open('data/questions/economics.json', encoding='utf-8'))

new_questions = {
    424: ("What is factor price equalization?",
          "The theorem that free trade will equalize the prices of production factors (like wages) across countries",
          ["The idea that prices of goods converge globally",
           "The theorem that free trade will equalize the prices of production factors (like wages) across countries",
           "The process by which currency exchange rates equalize",
           "The tendency for capital to flow to high-wage countries"]),

    429: ("What is the Lorenz curve?",
          "A graphical representation of income distribution showing cumulative income vs. cumulative population",
          ["A curve showing the relationship between inflation and unemployment",
           "A graphical representation of income distribution showing cumulative income vs. cumulative population",
           "A curve showing consumer demand at different price levels",
           "A representation of the business cycle over time"]),
}

changed = 0
for idx, (q, a, c) in new_questions.items():
    data[idx]['question'] = q
    data[idx]['answer'] = a
    data[idx]['choices'] = c
    changed += 1

print(f'Changed {changed} questions')

with open('data/questions/economics.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print('Saved')

# Verify
data2 = json.load(open('data/questions/economics.json', encoding='utf-8'))
seen = {}
dupes = []
for i, q in enumerate(data2):
    key = q['question'].strip().lower()
    if key in seen:
        dupes.append((seen[key]+1, i+1, q['tier'], q['question'][:60]))
    else:
        seen[key] = i

from collections import Counter
tiers = Counter(q['tier'] for q in data2)
print(f'Total: {len(data2)}, Tiers: {dict(sorted(tiers.items()))}')
print(f'Remaining dupes: {len(dupes)}')
for d in dupes:
    print(f'  {d[0]}&{d[1]}: {d[3]}')
