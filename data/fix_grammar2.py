import json

data = json.load(open('data/questions/grammar.json', encoding='utf-8'))

# Duplicates (second occurrence indices, 0-based):
# 35: sentence fragment dupe -> need non-conflicting q
# 98: "Which sentence is a fragment?" dupe (idx 67&98)
# 202: misplaced modifier dupe
# 205: dangling modifier dupe
# 216: misplaced modifier dupe (third instance)
# 233: parallel structure dupe
# 412: dependent clause dupe
# 413: dangling modifier dupe (second)
# 420: infinitive phrase dupe
# 425: participial phrase dupe
# 427: misplaced modifier dupe (in context)
# 442: oxymoron dupe
# 459: zeugma dupe
# 460: denotation/connotation dupe
# 467: phrase vs clause dupe
# 469: periodic sentence dupe
# 486: absolute phrase dupe

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

    233: (4, "Which sentence uses a subjunctive mood correctly?",
         "If I were you, I would apologize.",
         ["If I was you, I would apologize.",
          "If I were you, I would apologize.",
          "If I am you, I would apologize.",
          "If I had been you, I would apologize."]),

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

    420: (3, "What is the subjunctive mood used for?",
         "To express wishes, hypothetical situations, or conditions contrary to fact",
         ["To express wishes, hypothetical situations, or conditions contrary to fact",
          "To express commands or direct requests",
          "To describe completed past actions",
          "To express certainty about future events"]),

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

    442: (3, "What is epistrophe (also called antistrophe)?",
         "The repetition of a word or phrase at the end of successive clauses",
         ["The repetition of a word or phrase at the end of successive clauses",
          "The repetition of a word at the beginning of successive clauses",
          "The use of two contradictory terms together",
          "The deliberate omission of conjunctions between clauses"]),

    459: (4, "What is chiasmus?",
         "A rhetorical device in which words or concepts are repeated in reverse order",
         ["A rhetorical device in which words or concepts are repeated in reverse order",
          "The repetition of a word at the end of successive clauses",
          "Deliberate understatement by negating the opposite",
          "The substitution of a harsh term with a milder one"]),

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

    469: (4, "What is a loose sentence?",
         "A sentence that makes its main point first and then adds details or qualifications",
         ["A sentence that makes its main point first and then adds details or qualifications",
          "A sentence that builds to its main point at the end",
          "A sentence that uses too many adjectives and adverbs",
          "A sentence with no clear subject or predicate"]),

    486: (4, "What is polysyndeton?",
         "The deliberate use of multiple conjunctions between successive words or clauses",
         ["The deliberate use of multiple conjunctions between successive words or clauses",
          "The deliberate omission of conjunctions between clauses",
          "The repetition of a word at the start of successive clauses",
          "The use of a word in two different senses in the same sentence"]),
}

# Pre-check for conflicts
existing = set(q['question'].strip().lower() for i, q in enumerate(data) if i not in replacements)
conflicts = []
for idx, (tier, question, answer, choices) in replacements.items():
    if question.strip().lower() in existing:
        conflicts.append(f'CONFLICT idx {idx}: "{question}"')

if conflicts:
    for c in conflicts:
        print(c)
else:
    print('No conflicts — applying replacements')
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
