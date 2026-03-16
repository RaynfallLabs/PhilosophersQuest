import json

data = json.load(open('data/questions/economics.json', encoding='utf-8'))

new_questions = {
    363: ("What is a bilateral trade agreement?",
          "A trade deal between two countries that reduces tariffs and other trade barriers between them",
          ["A trade agreement involving more than two countries",
           "A trade deal between two countries that reduces tariffs and other trade barriers between them",
           "A deal that fixes exchange rates between two nations",
           "An agreement to use the same currency"]),

    389: ("What is the Heckscher-Ohlin theorem?",
          "Countries export goods that use their abundant factors of production and import goods requiring scarce factors",
          ["Countries always export manufactured goods and import raw materials",
           "Countries export goods that use their abundant factors of production and import goods requiring scarce factors",
           "Free trade leads to equal factor prices across all countries",
           "Small countries specialize in services; large countries in goods"]),

    429: ("What is the Gini coefficient?",
          "A measure of income inequality ranging from 0 (perfect equality) to 1 (complete inequality)",
          ["A measure of a country's total economic output",
           "A measure of income inequality ranging from 0 (perfect equality) to 1 (complete inequality)",
           "The ratio of private to public sector employment",
           "An index measuring inflation over time"]),

    440: ("What is the zero lower bound in monetary policy?",
          "The constraint that nominal interest rates cannot fall below zero, limiting central bank stimulus",
          ["The point where government spending must stop",
           "The minimum inflation rate a central bank targets",
           "The constraint that nominal interest rates cannot fall below zero, limiting central bank stimulus",
           "The level at which economic growth slows to zero"]),
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
    print(f'  {d[0]}&{d[1]} (t{d[2]}): {d[3]}')
