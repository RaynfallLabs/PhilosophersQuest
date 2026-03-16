import json

data = json.load(open('data/questions/economics.json', encoding='utf-8'))

# Fix remaining duplicates - replace the later-occurring ones
new_questions = {
    165: ("What is a contestable market?",
          "A market where new competitors can easily enter and exit, keeping prices competitive even with few firms",
          ["A market with fierce competition between many firms",
           "A market where new competitors can easily enter and exit, keeping prices competitive even with few firms",
           "A market contested by the government",
           "A market with high barriers to entry"]),

    201: ("What is seasonal unemployment?",
          "Unemployment that occurs at certain times of year when demand for labour drops in seasonal industries",
          ["Unemployment caused by business cycle downturns",
           "Unemployment caused by technological change",
           "Unemployment that occurs at certain times of year when demand for labour drops in seasonal industries",
           "Unemployment resulting from workers leaving voluntarily"]),

    354: ("What is a capital account surplus?",
          "When a country receives more investment from abroad than it sends overseas",
          ["When government saves more than it spends",
           "When a country receives more investment from abroad than it sends overseas",
           "When exports exceed imports",
           "When foreign reserves exceed national debt"]),

    360: ("What is comparative advantage?",
          "The ability of a country or individual to produce a good at a lower opportunity cost than others",
          ["The ability to produce more than any other country",
           "The ability of a country or individual to produce a good at a lower opportunity cost than others",
           "Having the most advanced technology in production",
           "Being the lowest-cost producer in absolute terms"]),

    361: ("What is a liquidity trap?",
          "A situation where interest rates are so low that monetary policy becomes ineffective in stimulating the economy",
          ["When a bank runs out of liquid assets",
           "A situation where interest rates are so low that monetary policy becomes ineffective in stimulating the economy",
           "When consumers hoard cash during deflation",
           "A market where assets cannot be sold quickly"]),

    363: ("What is a monopsony?",
          "A market with only one buyer, giving that buyer significant power over sellers",
          ["A market with only one seller",
           "A market with only one buyer, giving that buyer significant power over sellers",
           "A market where two buyers compete",
           "A monopoly controlled by the government"]),

    390: ("What is a negative income tax?",
          "A system where people earning below a threshold receive payments from the government rather than paying taxes",
          ["A tax credit for businesses with losses",
           "A tax on imports that harms domestic income",
           "A system where people earning below a threshold receive payments from the government rather than paying taxes",
           "A reduction in tax rates during a recession"]),

    395: ("What is a deadweight loss?",
          "The loss of economic efficiency when the equilibrium outcome is not achievable, typically due to taxes or monopoly",
          ["The cost of transporting heavy goods",
           "The loss of economic efficiency when the equilibrium outcome is not achievable, typically due to taxes or monopoly",
           "The cost of maintaining unsold inventory",
           "The reduction in profit from price competition"]),

    397: ("What is a Pigouvian tax?",
          "A tax on negative externalities designed to make producers bear the full social cost of their actions",
          ["A tax that redistributes wealth from rich to poor",
           "A tax on negative externalities designed to make producers bear the full social cost of their actions",
           "A tax that funds public goods",
           "A progressive income tax"]),

    409: ("What is a price floor's main unintended consequence?",
          "Surpluses, because producers supply more than consumers demand at the artificially high price",
          ["Shortages, because consumers want more",
           "Surpluses, because producers supply more than consumers demand at the artificially high price",
           "Black markets form because prices are too high",
           "Inflation, because the government must buy the surplus"]),

    421: ("What is the Veblen good effect?",
          "When higher prices increase demand for luxury goods because they signal status",
          ["When goods become cheaper as more people buy them",
           "When demand for a good falls as income rises",
           "When higher prices increase demand for luxury goods because they signal status",
           "When consumers prefer older goods to new versions"]),

    429: ("What does the Human Development Index (HDI) measure?",
          "A composite measure of a country's health, education, and standard of living",
          ["A country's gross domestic product per capita",
           "A composite measure of a country's health, education, and standard of living",
           "The rate of economic growth in developing nations",
           "A measure of income inequality within a country"]),
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
