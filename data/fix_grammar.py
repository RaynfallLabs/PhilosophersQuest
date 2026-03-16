import json

data = json.load(open('data/questions/grammar.json', encoding='utf-8'))

# Fix duplicates — replace the SECOND occurrence (higher index) in each pair
# All second occurrences are in the latter portion of the file

replacements = {
    35: (1, "Which of these is an example of a run-on sentence?",
         "I love pizza it is my favorite food",
         ["I love pizza, it is my favorite food.",
          "I love pizza it is my favorite food",
          "I love pizza, and it is my favorite food.",
          "I love pizza; it is my favorite food."]),

    98: (1, "Which of these is a complete sentence?",
         "She ran to the store quickly.",
         ["Running to the store.",
          "She ran to the store quickly.",
          "When she ran.",
          "Because she needed milk."]),

    202: (3, "Which sentence uses a split infinitive?",
          "She decided to quickly finish her homework.",
          ["She decided to finish her homework quickly.",
           "She decided to quickly finish her homework.",
           "She quickly decided to finish her homework.",
           "Quickly, she decided to finish her homework."]),

    205: (3, "Which sentence is correctly punctuated?",
         "Although it was raining, we decided to go.",
         ["Although it was raining we decided to go.",
          "Although it was raining, we decided to go.",
          "Although, it was raining we decided to go.",
          "Although it was raining; we decided to go."]),

    216: (3, "Which sentence uses passive voice?",
         "The report was written by the manager.",
         ["The manager wrote the report.",
          "The report was written by the manager.",
          "The manager is writing the report.",
          "The manager had written the report."]),

    233: (4, "Which sentence uses a correlative conjunction correctly?",
          "Neither the teacher nor the students were prepared.",
          ["Neither the teacher or the students were prepared.",
           "Neither the teacher nor the students were prepared.",
           "Either the teacher nor the students were prepared.",
           "Both the teacher or the students were prepared."]),

    412: (3, "What is an independent clause?",
         "A group of words with a subject and predicate that expresses a complete thought",
         ["A group of words with a subject and predicate that expresses a complete thought",
          "A clause that cannot stand alone as a sentence",
          "A phrase that modifies a noun",
          "A clause beginning with a subordinating conjunction"]),

    413: (3, "Which sentence correctly uses a comma with a nonrestrictive clause?",
          "My sister, who lives in Paris, is visiting next week.",
          ["My sister who lives in Paris, is visiting next week.",
           "My sister, who lives in Paris, is visiting next week.",
           "My sister who lives in Paris is visiting next week.",
           "My sister, who lives in Paris is visiting next week."]),

    420: (3, "What is a prepositional phrase?",
         "A phrase beginning with a preposition that modifies a noun or verb",
         ["A phrase beginning with a preposition that modifies a noun or verb",
          "A phrase that acts as the subject of a sentence",
          "A verbal phrase using the base form of a verb",
          "A phrase that describes the action of the main verb"]),

    425: (3, "What is a present participle?",
         "The -ing form of a verb used as an adjective or in progressive tenses",
         ["The -ing form of a verb used as an adjective or in progressive tenses",
          "The past form of a verb",
          "A verb form ending in -ed",
          "An infinitive phrase acting as a noun"]),

    427: (3, "Which sentence has a dangling participle?",
         "Walking down the street, the trees looked beautiful.",
         ["Walking down the street, she noticed the trees.",
          "Walking down the street, the trees looked beautiful.",
          "She noticed the trees while walking down the street.",
          "The trees, looking beautiful, lined the street."]),

    442: (3, "What is a malapropism?",
         "Using an incorrect word that sounds similar to the correct one",
         ["Using an incorrect word that sounds similar to the correct one",
          "Using two opposite words together for effect",
          "Intentional understatement to emphasize a point",
          "Repeating the same word at the end of successive clauses"]),

    459: (4, "What is an anacoluthon?",
         "A grammatical construction in which the expected syntax is abandoned mid-sentence",
         ["A grammatical construction in which the expected syntax is abandoned mid-sentence",
          "The repetition of a word at the beginning of successive clauses",
          "A figure of speech using two contradictory terms",
          "The deliberate omission of conjunctions between clauses"]),

    460: (4, "What is the difference between a simile and a metaphor?",
         "A simile uses 'like' or 'as'; a metaphor states the comparison directly",
         ["A simile states the comparison directly; a metaphor uses 'like' or 'as'",
          "A simile uses 'like' or 'as'; a metaphor states the comparison directly",
          "Both use 'like' or 'as' to draw comparisons",
          "A metaphor is longer; a simile is shorter"]),

    467: (4, "What is an appositive phrase?",
         "A noun phrase that renames or describes the noun beside it",
         ["A noun phrase that renames or describes the noun beside it",
          "A phrase that modifies the verb of the sentence",
          "A clause that introduces a condition",
          "A phrase using a participle to modify a noun"]),

    469: (4, "What is a cumulative sentence?",
         "A sentence that begins with the main clause and adds modifiers after it",
         ["A sentence that begins with the main clause and adds modifiers after it",
          "A sentence that ends with the main idea after a series of subordinate clauses",
          "A sentence with two independent clauses joined by a semicolon",
          "A sentence using a series of parallel phrases"]),

    486: (4, "What is a nominative absolute?",
         "A phrase consisting of a noun and a participle that modifies the entire sentence",
         ["A phrase consisting of a noun and a participle that modifies the entire sentence",
          "A noun used as a predicate complement",
          "A pronoun in the subjective case",
          "A noun that renames the subject after a linking verb"]),
}

# Check for conflicts
existing = set(q['question'].strip().lower() for i, q in enumerate(data) if i not in replacements)
conflicts = []
for idx, (tier, question, answer, choices) in replacements.items():
    if question.strip().lower() in existing:
        conflicts.append(f'CONFLICT idx {idx}: "{question}"')

if conflicts:
    for c in conflicts:
        print(c)
else:
    print('No conflicts detected')
    for idx, (tier, question, answer, choices) in replacements.items():
        data[idx]['tier'] = tier
        data[idx]['question'] = question
        data[idx]['answer'] = answer
        data[idx]['choices'] = choices

    with open('data/questions/grammar.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print('Saved')

# Verify
data2 = json.load(open('data/questions/grammar.json', encoding='utf-8'))
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
