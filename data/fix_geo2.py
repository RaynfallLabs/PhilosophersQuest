import json

data = json.load(open('data/questions/geography.json', encoding='utf-8'))

# Replace all duplicate second-batch questions with non-capital geography questions
# Items (0-indexed): 407, 408, 409, 410, 413, 420, 423, 427, 428, 433, 436, 439, 440, 445, 448, 449, 451, 455, 457, 460, 470, 472, 479, 486

# Indices that need replacement (0-based = item_num - 1)
replace_indices = [407, 408, 409, 410, 413, 420, 423, 427, 428, 433, 436, 439, 440, 445, 448, 449, 451, 455, 457, 460, 470, 472, 479, 486]

replacement_questions = [
    # Tier 3 geography questions (non-capital)
    (3, "Which river is the longest in South America?",
     "Amazon River",
     ["Orinoco River", "Parana River", "Amazon River", "Sao Francisco River"]),

    (3, "What is the name of the narrow strip of land connecting North and South America?",
     "Isthmus of Panama",
     ["Isthmus of Suez", "Isthmus of Panama", "Strait of Magellan", "Drake Passage"]),

    (3, "Which African country has the highest population?",
     "Nigeria",
     ["Ethiopia", "Egypt", "Nigeria", "South Africa"]),

    (3, "What is the name of the large desert in southern Africa?",
     "Kalahari Desert",
     ["Namib Desert", "Sahara Desert", "Kalahari Desert", "Danakil Desert"]),

    (3, "Which South American country is landlocked?",
     "Bolivia",
     ["Peru", "Colombia", "Bolivia", "Venezuela"]),

    (3, "What is the largest lake in Africa?",
     "Lake Victoria",
     ["Lake Tanganyika", "Lake Victoria", "Lake Malawi", "Lake Chad"]),

    (3, "Which country lies to the north of South Africa?",
     "Botswana",
     ["Mozambique", "Zimbabwe", "Botswana", "Namibia"]),

    (3, "What is the name of the sea between Italy and the Balkan Peninsula?",
     "Adriatic Sea",
     ["Tyrrhenian Sea", "Ionian Sea", "Adriatic Sea", "Aegean Sea"]),

    (3, "Which country is separated from Europe by the Strait of Gibraltar?",
     "Morocco",
     ["Tunisia", "Algeria", "Libya", "Morocco"]),

    # Tier 4 geography questions
    (4, "Which river forms much of the border between the United States and Mexico?",
     "Rio Grande",
     ["Colorado River", "Rio Grande", "Mississippi River", "Pecos River"]),

    (4, "What is the name of the large plateau region that covers much of central Africa?",
     "Congo Basin",
     ["Ethiopian Highlands", "East African Plateau", "Congo Basin", "Saharan Massif"]),

    (4, "Which African country is entirely surrounded by South Africa?",
     "Lesotho",
     ["Eswatini", "Lesotho", "Botswana", "Malawi"]),

    (4, "What is the name of the longest river in Russia?",
     "Ob River",
     ["Yenisei River", "Lena River", "Ob River", "Volga River"]),

    (4, "Which country claims the Falkland Islands (Islas Malvinas)?",
     "Argentina",
     ["Chile", "Argentina", "United Kingdom", "Uruguay"]),

    (4, "What is the name of the large archipelago nation northeast of mainland Asia?",
     "Japan",
     ["Philippines", "Indonesia", "Japan", "Taiwan"]),

    # Tier 5 geography questions
    (5, "What is the name of the exclaves that make up the Kaliningrad region?",
     "Russia (separated from mainland by Lithuania and Belarus)",
     ["Germany", "Poland", "Russia (separated from mainland by Lithuania and Belarus)", "Belarus"]),

    (5, "Which country has the most UNESCO World Heritage Sites?",
     "Italy",
     ["China", "Spain", "France", "Italy"]),

    (5, "What is the term for the boundary between two tectonic plates moving apart?",
     "Divergent plate boundary",
     ["Convergent plate boundary", "Transform plate boundary", "Divergent plate boundary", "Subduction zone"]),

    (5, "What is the name of the sea that borders Libya, Tunisia, and Algeria to the north?",
     "Mediterranean Sea",
     ["Red Sea", "Ionian Sea", "Tyrrhenian Sea", "Mediterranean Sea"]),

    (5, "Which country is home to the world's largest salt flat, the Salar de Uyuni?",
     "Bolivia",
     ["Argentina", "Chile", "Peru", "Bolivia"]),

    (5, "What is the name of the island group that includes Majorca and Ibiza?",
     "Balearic Islands",
     ["Canary Islands", "Azores", "Balearic Islands", "Faroe Islands"]),

    (5, "Which ocean current is responsible for moderating the climate of Western Europe?",
     "North Atlantic Drift (Gulf Stream extension)",
     ["Labrador Current", "North Atlantic Drift (Gulf Stream extension)", "Humboldt Current", "Benguela Current"]),

    (5, "What is the name of the boundary between the humid tropics and the Sahara, marked by shrubland?",
     "Sahel",
     ["Savanna belt", "Sahel", "Sub-Saharan transition zone", "African Green Belt"]),

    (5, "What is the name of the chain of islands that stretches from Alaska toward Russia?",
     "Aleutian Islands",
     ["Kuril Islands", "Aleutian Islands", "Commander Islands", "Pribilof Islands"]),
]

for idx, replacement in zip(replace_indices, replacement_questions):
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
