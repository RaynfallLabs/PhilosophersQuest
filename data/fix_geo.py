import json

data = json.load(open('data/questions/geography.json', encoding='utf-8'))

# Find all duplicate pairs and collect which indices (later ones) need replacing
seen = {}
to_replace = []
for i, q in enumerate(data):
    key = q['question'].strip().lower()
    if key in seen:
        to_replace.append(i)  # replace this later occurrence
    else:
        seen[key] = i

print(f'Indices to replace: {[x+1 for x in to_replace]}')

# Create replacement questions - geography questions that don't duplicate existing ones
# All existing questions in the file
existing = set(q['question'].strip().lower() for q in data)

new_qs = [
    # Tier 2 replacements (items 185, 254->wrong tier, 408, 409, 410, 411, 414, 421->wrong tier)
    (1, "What is the capital of Denmark?", "Copenhagen",
     ["Oslo", "Stockholm", "Copenhagen", "Helsinki"]),
    (2, "What is the capital of Portugal?", "Lisbon",
     ["Madrid", "Porto", "Lisbon", "Faro"]),
    (2, "What is the capital of Hungary?", "Budapest",
     ["Vienna", "Warsaw", "Budapest", "Prague"]),
    (2, "What is the capital of the Czech Republic?", "Prague",
     ["Budapest", "Warsaw", "Bratislava", "Prague"]),
    (2, "What is the capital of Finland?", "Helsinki",
     ["Stockholm", "Oslo", "Copenhagen", "Helsinki"]),
    (2, "What is the capital of Austria?", "Vienna",
     ["Bern", "Zurich", "Vienna", "Munich"]),
    (2, "Which country has the highest population in South America?", "Brazil",
     ["Argentina", "Colombia", "Brazil", "Peru"]),
    (2, "What is the capital of Chile?", "Santiago",
     ["Buenos Aires", "Lima", "Bogota", "Santiago"]),
    # Tier 3 replacements
    (3, "What is the capital of Guatemala?", "Guatemala City",
     ["San Jose", "Panama City", "Guatemala City", "Tegucigalpa"]),
    (3, "What is the capital of Cuba?", "Havana",
     ["Kingston", "Port-au-Prince", "Santo Domingo", "Havana"]),
    (3, "What is the capital of Zimbabwe?", "Harare",
     ["Lusaka", "Nairobi", "Harare", "Maputo"]),
    (3, "What is the capital of Mozambique?", "Maputo",
     ["Harare", "Luanda", "Nairobi", "Maputo"]),
    (3, "What is the capital of Senegal?", "Dakar",
     ["Conakry", "Abidjan", "Dakar", "Bamako"]),
    (3, "What is the capital of Tanzania?", "Dodoma",
     ["Nairobi", "Kampala", "Dar es Salaam", "Dodoma"]),
    (3, "What is the capital of Sudan?", "Khartoum",
     ["Addis Ababa", "Khartoum", "Nairobi", "Cairo"]),
    (3, "What is the capital of Bolivia?", "Sucre (constitutional) / La Paz (seat of government)",
     ["Lima", "Quito", "Sucre (constitutional) / La Paz (seat of government)", "Asuncion"]),
    (3, "What is the capital of Peru?", "Lima",
     ["Quito", "Lima", "Bogota", "Santiago"]),
    (3, "What is the capital of Venezuela?", "Caracas",
     ["Bogota", "Lima", "Quito", "Caracas"]),
    (3, "What is the capital of Paraguay?", "Asuncion",
     ["Montevideo", "La Paz", "Asuncion", "Buenos Aires"]),
    (3, "What is the capital of Uruguay?", "Montevideo",
     ["Buenos Aires", "Asuncion", "Montevideo", "Santiago"]),
    # Tier 4 replacements
    (4, "What is the capital of Laos?", "Vientiane",
     ["Phnom Penh", "Yangon", "Vientiane", "Naypyidaw"]),
    (4, "What is the capital of Timor-Leste?", "Dili",
     ["Suva", "Port Moresby", "Dili", "Honiara"]),
    (4, "What is the capital of Benin?", "Porto-Novo",
     ["Lomé", "Abidjan", "Accra", "Porto-Novo"]),
    (4, "What is the capital of Burundi?", "Gitega",
     ["Kigali", "Bujumbura", "Gitega", "Kampala"]),
    (4, "What is the capital of Mali?", "Bamako",
     ["Niamey", "Ouagadougou", "Dakar", "Bamako"]),
    (4, "What is the capital of Mauritania?", "Nouakchott",
     ["Dakar", "Bamako", "Nouakchott", "Conakry"]),
    (4, "What is the capital of the Central African Republic?", "Bangui",
     ["Yaounde", "Libreville", "Brazzaville", "Bangui"]),
    (4, "What is the capital of Gabon?", "Libreville",
     ["Brazzaville", "Yaounde", "Libreville", "Malabo"]),
    (4, "What is the capital of Djibouti?", "Djibouti City",
     ["Mogadishu", "Asmara", "Djibouti City", "Addis Ababa"]),
    # Tier 5 replacements
    (5, "What is the capital of Liechtenstein?", "Vaduz",
     ["Bern", "Luxembourg City", "Vaduz", "Monaco"]),
    (5, "What is the capital of Nauru?", "Yaren (de facto)",
     ["Suva", "Funafuti", "Yaren (de facto)", "Honiara"]),
    (5, "What is the capital of Palau?", "Ngerulmud",
     ["Koror", "Palikir", "Yaren", "Ngerulmud"]),
    (5, "What is the capital of San Marino?", "San Marino City",
     ["Vaduz", "Andorra la Vella", "Monaco", "San Marino City"]),
    (5, "What is the capital of Kosovo?", "Pristina",
     ["Skopje", "Tirana", "Pristina", "Sarajevo"]),
    (5, "What is the capital of the Federated States of Micronesia?", "Palikir",
     ["Koror", "Honiara", "Suva", "Palikir"]),
    (5, "What is the capital of Tonga?", "Nuku'alofa",
     ["Apia", "Suva", "Port Vila", "Nuku'alofa"]),
    (5, "What is the capital of Samoa?", "Apia",
     ["Suva", "Nuku'alofa", "Honiara", "Apia"]),
    (5, "What is the capital of Kiribati?", "South Tarawa",
     ["Funafuti", "Majuro", "Honiara", "South Tarawa"]),
    (5, "What is the capital of the Marshall Islands?", "Majuro",
     ["Funafuti", "South Tarawa", "Palikir", "Majuro"]),
]

# Apply replacements
for idx, replacement in zip(to_replace, new_qs):
    tier, question, answer, choices = replacement
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
