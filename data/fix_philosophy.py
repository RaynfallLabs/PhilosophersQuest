import json

data = json.load(open('data/questions/philosophy.json', encoding='utf-8'))

# Replace all second occurrences (higher index) with unique questions
replacements = {
    346: (2, "What is a 'thought experiment' in philosophy?",
          "A hypothetical scenario used to explore philosophical implications",
          ["A hypothetical scenario used to explore philosophical implications",
           "An experiment conducted purely in the mind without empirical data",
           "A logical argument that proves a theorem",
           "A form of meditative reasoning used in Eastern philosophy"]),

    355: (2, "What is 'compatibilism' in philosophy?",
          "The view that free will and determinism are compatible",
          ["The view that free will and determinism are compatible",
           "The belief that free will is an illusion",
           "The doctrine that moral rules are absolute",
           "The theory that consciousness emerges from physical processes"]),

    359: (2, "What is 'moral relativism'?",
          "The view that moral judgments are not universally valid but relative to culture or individual",
          ["The view that moral judgments are not universally valid but relative to culture or individual",
           "The belief that moral rules are absolute and universal",
           "The doctrine that morality is determined by consequences",
           "The view that moral facts are objective and mind-independent"]),

    368: (2, "What is the 'trolley problem'?",
          "A thought experiment about diverting a runaway trolley to save more lives",
          ["A thought experiment about diverting a runaway trolley to save more lives",
           "A scenario used to test utilitarian vs. deontological ethics",
           "Both A and B",
           "A problem in logic involving categorical reasoning"]),

    369: (2, "What is 'ontology'?",
          "The branch of philosophy concerned with the nature of existence and being",
          ["The branch of philosophy concerned with the nature of existence and being",
           "The study of knowledge and justified belief",
           "The philosophical study of moral values",
           "The analysis of language and meaning"]),

    370: (2, "What is 'deontological ethics'?",
          "An ethical theory that judges the morality of actions based on rules or duties",
          ["An ethical theory that judges the morality of actions based on rules or duties",
           "An ethical theory focused on the character of the moral agent",
           "An ethical theory that judges actions solely by their consequences",
           "An ethical theory based on social contracts"]),

    372: (2, "What is 'aesthetics' in philosophy?",
          "The branch of philosophy concerned with beauty, art, and taste",
          ["The branch of philosophy concerned with beauty, art, and taste",
           "The study of the nature of knowledge",
           "The philosophical investigation of moral principles",
           "The study of the nature of being and existence"]),

    374: (2, "What is 'Hegel's dialectic'?",
          "The process of thesis, antithesis, and synthesis driving historical change",
          ["The process of thesis, antithesis, and synthesis driving historical change",
           "A principle of economy stating simpler explanations are preferable",
           "The view that reality is fundamentally mental in nature",
           "The theory that knowledge comes from sense experience"]),

    376: (2, "What is 'skepticism' in philosophy?",
          "The position of doubting claims that lack sufficient evidence or certainty",
          ["The position of doubting claims that lack sufficient evidence or certainty",
           "The belief that the self is the only thing that can be known to exist",
           "The view that knowledge is impossible to attain",
           "A rejection of metaphysical claims about reality"]),

    383: (2, "What is 'cultural relativism'?",
          "The view that moral and social standards are relative to the culture that holds them",
          ["The view that moral and social standards are relative to the culture that holds them",
           "The doctrine that moral truths are objective and universal",
           "The belief that culture is determined by geography",
           "The theory that all cultures evolve toward the same endpoint"]),

    386: (2, "What is 'utilitarianism'?",
          "The ethical theory that the best action maximizes overall happiness or utility",
          ["The ethical theory that the best action maximizes overall happiness or utility",
           "The ethical theory that actions are right if they fulfill one's duty",
           "The ethical theory that virtue is the foundation of good character",
           "The ethical theory that moral facts are constructed by social agreement"]),

    387: (2, "What is 'substance dualism'?",
          "The view that mind and body are two distinct kinds of substance",
          ["The view that mind and body are two distinct kinds of substance",
           "The view that only physical matter exists",
           "The theory that mental states are identical to brain states",
           "The belief that consciousness is an emergent property of matter"]),

    389: (2, "What is 'existentialism'?",
          "A philosophical movement emphasizing individual freedom, responsibility, and authentic existence",
          ["A philosophical movement emphasizing individual freedom, responsibility, and authentic existence",
           "The philosophical view that life has no inherent meaning or value",
           "The belief that existence is fundamentally absurd",
           "A doctrine holding that society determines individual identity"]),

    398: (3, "What is 'panpsychism'?",
          "The view that consciousness or mind is a fundamental feature of all matter",
          ["The view that consciousness or mind is a fundamental feature of all matter",
           "The philosophical position that only minds exist",
           "The theory that God is identical with nature",
           "The doctrine that the self is an illusion"]),

    399: (3, "What is 'falsificationism' in philosophy of science?",
          "The view that scientific theories must be testable and capable of being proved false",
          ["The view that scientific theories must be testable and capable of being proved false",
           "The doctrine that only verifiable statements are meaningful",
           "The belief that science proceeds by accumulation of facts",
           "The theory that all knowledge is derived from sense experience"]),

    402: (3, "Who wrote 'Being and Time'?",
          "Martin Heidegger",
          ["Martin Heidegger", "Jean-Paul Sartre", "Edmund Husserl", "Albert Camus"]),

    405: (3, "What is 'phenomenalism'?",
          "The view that physical objects exist only as collections of perceptions",
          ["The view that physical objects exist only as collections of perceptions",
           "The philosophical study of structures of consciousness and experience",
           "The doctrine that only mental substances exist",
           "The belief that reality consists of both mental and physical substance"]),

    413: (3, "What is 'instrumentalism' in philosophy of science?",
          "The view that scientific theories are tools for prediction rather than literal truths",
          ["The view that scientific theories are tools for prediction rather than literal truths",
           "The theory that truth is what works in practice",
           "The belief that scientific knowledge is cumulative and progressive",
           "The doctrine that only observable entities should be admitted in science"]),

    420: (3, "What is 'Kant's categorical imperative'?",
          "Act only according to maxims you could will to be universal laws",
          ["Act only according to maxims you could will to be universal laws",
           "Act to maximize the greatest happiness for the greatest number",
           "Act in accordance with your virtuous character",
           "Act as you wish, provided you do not harm others"]),

    423: (3, "What is the 'coherence theory of truth'?",
          "The view that a proposition is true if it coheres with a set of other accepted propositions",
          ["The view that a proposition is true if it coheres with a set of other accepted propositions",
           "The view that truth consists in a correspondence between propositions and facts",
           "The view that truth is what works or proves useful",
           "The view that truth is determined by social consensus"]),

    427: (3, "What is 'intersubjectivity'?",
          "The shared understanding or agreement between different subjects or persons",
          ["The shared understanding or agreement between different subjects or persons",
           "The study of consciousness from a first-person perspective",
           "The philosophical view that only one's own mind is known to exist",
           "The belief that subjective experience cannot be communicated"]),

    433: (3, "What is 'property dualism'?",
          "The view that mental properties are distinct from physical properties but arise from the brain",
          ["The view that mental properties are distinct from physical properties but arise from the brain",
           "The view that mind and body are entirely separate substances",
           "The theory that mental states are reducible to physical states",
           "The belief that consciousness cannot be explained by physical processes"]),

    437: (3, "What is 'positive liberty'?",
          "Freedom as the capacity to act and fulfill one's potential",
          ["Freedom as the capacity to act and fulfill one's potential",
           "Freedom defined as absence of external constraints",
           "Freedom from government interference in private life",
           "Freedom granted by a sovereign power to its citizens"]),

    441: (4, "What is 'transcendental idealism'?",
          "Kant's doctrine that space, time, and categories are conditions imposed by the mind on experience",
          ["Kant's doctrine that space, time, and categories are conditions imposed by the mind on experience",
           "The view that all reality consists of ideas in the mind of God",
           "The belief that consciousness transcends physical reality",
           "The theory that knowledge of things-in-themselves is possible"]),

    447: (4, "What is 'realism' in metaphysics?",
          "The view that entities exist independently of our perception or thought of them",
          ["The view that entities exist independently of our perception or thought of them",
           "The view that only particulars exist and universals are mere names",
           "The belief that abstract objects such as numbers do not really exist",
           "The doctrine that reality is fundamentally mental in nature"]),

    449: (4, "What is 'epiphenomenalism'?",
          "The view that mental events are caused by physical events but have no causal power themselves",
          ["The view that mental events are caused by physical events but have no causal power themselves",
           "The theory that mental and physical processes run in parallel without interacting",
           "The view that consciousness is identical to brain states",
           "The doctrine that mind and body are two distinct substances"]),

    450: (4, "What is 'moral constructivism'?",
          "The view that moral truths are constructed through rational agreement or procedure",
          ["The view that moral truths are constructed through rational agreement or procedure",
           "The view that moral judgments are responses to particular situations",
           "The belief that moral facts are objective features of the natural world",
           "The theory that moral rules are based on divine command"]),
}

# Verify no conflicts with kept questions
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

    with open('data/questions/philosophy.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print('Saved')

# Verify
data2 = json.load(open('data/questions/philosophy.json', encoding='utf-8'))
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
