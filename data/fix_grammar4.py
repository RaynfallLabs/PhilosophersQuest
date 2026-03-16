import json

data = json.load(open('data/questions/grammar.json', encoding='utf-8'))
existing = set(q['question'].strip().lower() for q in data)

# All second-occurrence indices to fix
replacements = {
    35: (1, "Which of these is an example of a run-on sentence?",
         "I love pizza it is my favorite food",
         ["I love pizza, and it is my favorite food.",
          "I love pizza it is my favorite food",
          "I love pizza; it is my favorite food.",
          "I love pizza."]),

    98: (1, "Which of these words is a conjunction?",
         "But",
         ["But", "Quickly", "Beautiful", "Happiness"]),

    202: (3, "Which sentence uses passive voice correctly?",
         "The cake was baked by the chef.",
         ["The chef baked the cake.",
          "The cake was baked by the chef.",
          "The chef is baking the cake.",
          "The cake baked itself."]),

    205: (3, "Which sentence is correctly punctuated with a semicolon?",
         "She studied hard; she passed the exam.",
         ["She studied hard, she passed the exam.",
          "She studied hard; she passed the exam.",
          "She studied hard; and she passed the exam.",
          "She studied hard: she passed the exam."]),

    216: (3, "Which of the following best defines 'syntax'?",
         "The arrangement of words and phrases to form well-structured sentences",
         ["The study of word meanings and their changes over time",
          "The arrangement of words and phrases to form well-structured sentences",
          "The system of sounds used in a language",
          "The rules for spelling words correctly"]),

    233: (4, "Which sentence uses a correlative conjunction correctly?",
         "Neither the teacher nor the students were prepared.",
         ["Neither the teacher or the students were prepared.",
          "Neither the teacher nor the students were prepared.",
          "Either the teacher nor the students were prepared.",
          "Both the teacher or the students were prepared."]),

    412: (3, "Which sentence uses a relative clause correctly?",
         "The book that she recommended was excellent.",
         ["The book, that she recommended, was excellent.",
          "The book that she recommended was excellent.",
          "The book which she recommended, was excellent.",
          "The book whom she recommended was excellent."]),

    413: (3, "What is an adverbial clause?",
         "A dependent clause that modifies a verb, adjective, or adverb",
         ["A dependent clause that modifies a verb, adjective, or adverb",
          "A clause that acts as the subject of a sentence",
          "A clause that renames or describes a noun",
          "An independent clause joined by a coordinating conjunction"]),

    416: (3, "What is a present participle?",
         "The -ing form of a verb used as an adjective or in progressive tenses",
         ["The -ing form of a verb used as an adjective or in progressive tenses",
          "A verb form ending in -ed showing completed action",
          "The base form of a verb preceded by 'to'",
          "A verbal noun derived from a verb by adding -ing"]),

    425: (3, "What is an adjective clause?",
         "A dependent clause that modifies a noun or pronoun",
         ["A dependent clause that modifies a noun or pronoun",
          "A clause that functions as the subject of a sentence",
          "An independent clause describing an action",
          "A phrase using an adjective to modify a verb"]),

    427: (3, "Which of the following is an example of anaphora?",
         "We shall fight on the beaches, we shall fight on the landing grounds, we shall fight in the fields.",
         ["We shall fight on the beaches, we shall fight on the landing grounds, we shall fight in the fields.",
          "It was the best of times, it was the worst of times.",
          "To be or not to be, that is the question.",
          "All the world's a stage, and all the men and women merely players."]),

    442: (3, "What is litotes?",
         "A figure of speech using understatement by negating the opposite",
         ["A figure of speech using understatement by negating the opposite",
          "The use of two contradictory terms together for effect",
          "The repetition of a word at the start of successive clauses",
          "Deliberate exaggeration to emphasize a point"]),

    460: (4, "What is the difference between syntax and morphology?",
         "Syntax deals with sentence structure; morphology deals with word structure",
         ["Syntax deals with word structure; morphology deals with sentence structure",
          "Syntax deals with sentence structure; morphology deals with word structure",
          "Both deal with the rules governing sentence formation",
          "Syntax concerns meaning; morphology concerns sound"]),

    467: (4, "What is the difference between a coordinating and a subordinating conjunction?",
         "Coordinating conjunctions join equal elements; subordinating conjunctions introduce dependent clauses",
         ["Coordinating conjunctions join equal elements; subordinating conjunctions introduce dependent clauses",
          "Subordinating conjunctions join equal elements; coordinating conjunctions introduce dependent clauses",
          "Both types join independent clauses of equal importance",
          "Coordinating conjunctions begin sentences; subordinating conjunctions end them"]),

    469: (4, "What is a loose (cumulative) sentence?",
         "A sentence that states its main point first and then adds modifying details",
         ["A sentence that states its main point first and then adds modifying details",
          "A sentence that builds to its main idea at the end",
          "A sentence with too many adjectives and adverbs",
          "A sentence with no clear subject or predicate"]),
}

# Verify no conflicts with questions NOT being replaced
keep_set = set(i for i in range(len(data)) if i not in replacements)
existing_keep = set(data[i]['question'].strip().lower() for i in keep_set)

conflicts = []
for idx, (tier, question, answer, choices) in replacements.items():
    if question.strip().lower() in existing_keep:
        conflicts.append(f'CONFLICT idx {idx}: "{question}"')

if conflicts:
    for c in conflicts:
        print(c)
else:
    print('No conflicts — applying all replacements')
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
