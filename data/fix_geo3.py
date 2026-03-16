import json

data = json.load(open('data/questions/geography.json', encoding='utf-8'))

# Get all existing questions to avoid creating more duplicates
existing = set(q['question'].strip().lower() for q in data)

replacements = {
    184: (1, "What is the name of the tallest mountain in the Alps?",
          "Mont Blanc",
          ["Matterhorn", "Mont Blanc", "Eiger", "Jungfrau"]),

    253: (2, "Which country contains the ruins of Machu Picchu?",
          "Peru",
          ["Bolivia", "Ecuador", "Peru", "Colombia"]),

    315: (2, "What is the name of the body of water between Greenland and Iceland?",
          "Denmark Strait",
          ["Labrador Sea", "Denmark Strait", "Davis Strait", "Greenland Sea"]),

    321: (2, "What is the capital of Romania?",
          "Bucharest",
          ["Sofia", "Belgrade", "Budapest", "Bucharest"]),

    322: (2, "What is the capital of Slovakia?",
          "Bratislava",
          ["Prague", "Warsaw", "Bratislava", "Budapest"]),

    327: (2, "What is the capital of Croatia?",
          "Zagreb",
          ["Ljubljana", "Sarajevo", "Zagreb", "Belgrade"]),

    329: (2, "What is the capital of Lithuania?",
          "Vilnius",
          ["Riga", "Tallinn", "Minsk", "Vilnius"]),

    331: (3, "What is the capital of Honduras?",
          "Tegucigalpa",
          ["Guatemala City", "Managua", "San Salvador", "Tegucigalpa"]),

    333: (3, "What is the capital of Zambia?",
          "Lusaka",
          ["Harare", "Nairobi", "Lusaka", "Windhoek"]),

    334: (3, "What is the capital of Uganda?",
          "Kampala",
          ["Kigali", "Nairobi", "Addis Ababa", "Kampala"]),

    407: (3, "What is the name of the world's largest hot desert?",
          "Sahara Desert",
          ["Arabian Desert", "Sahara Desert", "Gobi Desert", "Great Victoria Desert"]),

    451: (5, "What is the name of the deepest trench in the Pacific Ocean?",
          "Mariana Trench",
          ["Puerto Rico Trench", "Tonga Trench", "Mariana Trench", "Philippine Trench"]),

    453: (4, "Which country is home to the Serengeti National Park?",
          "Tanzania",
          ["Kenya", "Tanzania", "Uganda", "Botswana"]),

    495: (5, "What is the name of the point where three or more tectonic plates meet?",
          "Triple junction",
          ["Convergence zone", "Subduction point", "Triple junction", "Plate nexus"]),
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
