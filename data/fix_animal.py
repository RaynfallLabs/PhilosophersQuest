import json

data = json.load(open('data/questions/animal.json', encoding='utf-8'))

# Duplicates to fix (0-based indices in second batch):
# 3&94 (t1): fastest land animal -> fix idx 93
# 22&99 (t1): group of lions -> fix idx 98
# 8&111 (t1): insect legs -> fix idx 110
# 2&112 (t1): spider legs -> fix idx 111
# 11&122 (t1): tallest animal -> fix idx 121
# 5&123 (t1): flightless bird -> fix idx 122
# 29&145 (t1): group of geese -> fix idx 144
# 28&163 (t1): group of elephants -> fix idx 162
# 31&168 (t2): longest lifespan -> fix idx 167
# 51&246 (t3): closest primate -> fix idx 245
# 21&445 (t1): group of crows -> fix idx 444

replacements = {
    93: (1, "What color is a polar bear's skin?",
         "Black",
         ["White", "Black", "Pink", "Transparent"]),

    98: (1, "What is a group of wolves called?",
         "Pack",
         ["Pack", "Pride", "Herd", "Colony"]),

    110: (1, "What is the only mammal capable of true flight?",
          "Bat",
          ["Bat", "Flying squirrel", "Flying lemur", "Sugar glider"]),

    111: (1, "How many eyes does a typical spider have?",
          "Eight",
          ["Two", "Four", "Six", "Eight"]),

    121: (1, "What is the heaviest land animal?",
          "African elephant",
          ["African elephant", "Hippopotamus", "White rhinoceros", "Giraffe"]),

    122: (1, "What is the only continent where penguins live in the wild?",
          "Antarctica",
          ["Antarctica", "Africa", "South America", "Australia"]),

    144: (1, "What is a group of fish called?",
          "School",
          ["School", "Pod", "Flock", "Colony"]),

    162: (1, "What is a group of whales called?",
          "Pod",
          ["Pod", "School", "Pride", "Pack"]),

    167: (2, "Which animal sleeps the most hours per day on average?",
          "Koala",
          ["Koala", "Cat", "Sloth", "Armadillo"]),

    245: (3, "What is the scientific name for the domestic cat?",
          "Felis catus",
          ["Felis catus", "Felis silvestris", "Panthera leo", "Lynx rufus"]),

    444: (1, "What is a group of geese in flight called?",
          "Skein",
          ["Skein", "Gaggle", "Flock", "V-formation"]),
}

for idx, (tier, question, answer, choices) in replacements.items():
    data[idx]['tier'] = tier
    data[idx]['question'] = question
    data[idx]['answer'] = answer
    data[idx]['choices'] = choices

with open('data/questions/animal.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print('Saved')

# Verify
data2 = json.load(open('data/questions/animal.json', encoding='utf-8'))
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
