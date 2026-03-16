import json

data = json.load(open('data/questions/philosophy.json', encoding='utf-8'))

# Current dupe second-occurrence indices (0-based):
# 346, 355, 359, 368, 369, 370, 372, 374, 376, 383, 386, 387, 389
# 398, 399, 402, 405, 413, 420, 423, 427, 433, 437, 441, 447, 449, 450

replacements = {
    346: (2, "What is 'a priori' knowledge?",
          "Knowledge independent of experience, knowable through reason alone",
          ["Knowledge independent of experience, knowable through reason alone",
           "Knowledge derived from sense experience",
           "Knowledge based on empirical observation",
           "Knowledge that requires both reason and experience"]),

    355: (2, "What is 'a posteriori' knowledge?",
          "Knowledge derived from sense experience and empirical observation",
          ["Knowledge derived from sense experience and empirical observation",
           "Knowledge independent of experience",
           "Knowledge known through pure reason alone",
           "Knowledge that is necessarily true in all possible worlds"]),

    359: (2, "What is 'relativism'?",
          "The view that knowledge, truth, or morality exists only relative to a framework",
          ["The view that knowledge, truth, or morality exists only relative to a framework",
           "The belief that moral rules are absolute and universal",
           "The doctrine that all possible perspectives have equal validity",
           "The view that there are no objective standards of any kind"]),

    368: (2, "What is 'fallibilism'?",
          "The view that our beliefs or knowledge claims might always be mistaken",
          ["The view that our beliefs or knowledge claims might always be mistaken",
           "The position that genuine knowledge is impossible",
           "The belief that logical proofs can always be refuted",
           "The doctrine that moral judgments are always subjective"]),

    369: (2, "What is Plato's 'Theory of Forms'?",
          "The view that abstract Forms are more real than the physical things that exemplify them",
          ["The view that abstract Forms are more real than the physical things that exemplify them",
           "The theory that knowledge is acquired through the senses",
           "The belief that the soul is made up of reason, spirit, and appetite",
           "The doctrine that virtue is identical to knowledge"]),

    370: (2, "What is 'naive realism'?",
          "The common-sense view that the world is as we perceive it to be",
          ["The common-sense view that the world is as we perceive it to be",
           "The view that physical objects exist independently of perception",
           "The belief that only ideas exist in the mind",
           "The theory that perception is always theory-laden"]),

    372: (2, "What is 'the veil of ignorance'?",
          "John Rawls' device for choosing fair social principles without knowing one's social position",
          ["John Rawls' device for choosing fair social principles without knowing one's social position",
           "The Kantian view that we cannot know things-in-themselves",
           "Descartes' method of doubting all beliefs that might be false",
           "The view that our moral intuitions are systematically unreliable"]),

    374: (2, "What is 'antirealism' in philosophy?",
          "The view that entities in some domain do not exist independently of our minds",
          ["The view that entities in some domain do not exist independently of our minds",
           "The view that the external world exists and is knowable",
           "The belief that science gives us accurate descriptions of unobservable entities",
           "The doctrine that abstract objects exist independently"]),

    376: (2, "What is 'instrumentalism' in philosophy of science?",
          "The view that scientific theories are tools for making predictions, not literal truths",
          ["The view that scientific theories are tools for making predictions, not literal truths",
           "The belief that science reveals the true nature of unobservable reality",
           "The doctrine that observation is theory-free",
           "The view that only observable entities are real"]),

    383: (2, "What is 'the problem of induction'?",
          "The challenge of justifying generalizations from past observations to future cases",
          ["The challenge of justifying generalizations from past observations to future cases",
           "The difficulty of deriving moral conclusions from factual premises",
           "The impossibility of proving a universal negative",
           "The challenge of explaining how we come to know a priori truths"]),

    386: (2, "What is 'the Chinese Room argument'?",
          "Searle's thought experiment arguing syntax alone cannot produce genuine understanding",
          ["Searle's thought experiment arguing syntax alone cannot produce genuine understanding",
           "An argument that translation between languages is impossible in principle",
           "A thought experiment about multiple realizability of mental states",
           "An argument against behaviorist theories of the mind"]),

    387: (2, "What is the 'paradox of the heap' (sorites)?",
          "The puzzle about how many grains make a heap, arising from vague predicates",
          ["The puzzle about how many grains make a heap, arising from vague predicates",
           "A paradox about self-referential statements",
           "A puzzle about whether future contingents can be true or false",
           "The paradox of a set containing all sets that don't contain themselves"]),

    389: (2, "What is 'contractualism'?",
          "The moral theory that principles are justified if no one could reasonably reject them",
          ["The moral theory that principles are justified if no one could reasonably reject them",
           "The view that moral rules are based on a social contract for mutual benefit",
           "The theory that moral obligations derive from actual agreements people make",
           "The doctrine that justice requires maximizing the minimum share"]),

    398: (3, "What is 'occasionalism'?",
          "The view that God mediates all causal interactions between mind and body",
          ["The view that God mediates all causal interactions between mind and body",
           "The theory that mind and body run in parallel without interacting",
           "The doctrine that mental events cause physical events directly",
           "The view that causal relations are regularities without necessary connection"]),

    399: (3, "What is 'falsificationism' in philosophy of science?",
          "The view that scientific theories must be testable and capable of being proved false",
          ["The view that scientific theories must be testable and capable of being proved false",
           "The doctrine that only verifiable statements are meaningful",
           "The belief that science proceeds by accumulation of facts",
           "The theory that all knowledge is derived from sense experience"]),

    402: (3, "Who wrote 'Being and Time'?",
          "Martin Heidegger",
          ["Martin Heidegger", "Jean-Paul Sartre", "Edmund Husserl", "Albert Camus"]),

    405: (3, "What is 'trope theory'?",
          "The view that particulars are bundles of abstract particular properties (tropes)",
          ["The view that particulars are bundles of abstract particular properties (tropes)",
           "The philosophical study of figures of speech in argumentation",
           "The doctrine that universals exist independently of particulars",
           "The belief that all properties are reducible to physical properties"]),

    413: (3, "What is 'structural realism'?",
          "The view that what science reveals is the structure of reality, not its intrinsic nature",
          ["The view that what science reveals is the structure of reality, not its intrinsic nature",
           "The belief that theoretical entities in science are literally real",
           "The doctrine that only directly observable entities exist",
           "The view that science is only a useful tool for prediction"]),

    420: (3, "What is 'four-dimensionalism' (perdurantism)?",
          "The view that objects persist through time by having temporal parts",
          ["The view that objects persist through time by having temporal parts",
           "The view that an object is wholly present at each moment it exists",
           "The doctrine that time is an illusion created by the mind",
           "The belief that past, present, and future are equally real"]),

    423: (3, "What is 'supervenience'?",
          "A relation where A-properties supervene on B-properties if any A-difference requires a B-difference",
          ["A relation where A-properties supervene on B-properties if any A-difference requires a B-difference",
           "The view that mental properties are identical to physical properties",
           "The doctrine that all properties reduce to fundamental physical properties",
           "The theory that higher-level properties cause lower-level events"]),

    427: (3, "What is a 'philosophical zombie' (p-zombie)?",
          "A hypothetical being physically identical to a human but lacking consciousness",
          ["A hypothetical being physically identical to a human but lacking consciousness",
           "A thought experiment about machine intelligence",
           "A concept used to argue that mental states are purely behavioral",
           "A being that lacks free will but otherwise behaves normally"]),

    433: (3, "What is 'property dualism'?",
          "The view that mental properties are distinct from physical properties but arise from the brain",
          ["The view that mental properties are distinct from physical properties but arise from the brain",
           "The view that mind and body are entirely separate substances",
           "The theory that mental states are reducible to physical states",
           "The belief that consciousness cannot be explained by physical processes"]),

    437: (3, "What is 'libertarianism' in philosophy of free will?",
          "The view that free will is real and incompatible with determinism, and determinism is false",
          ["The view that free will is real and incompatible with determinism, and determinism is false",
           "The view that free will and determinism are compatible",
           "The view that free will is an illusion because all events are determined",
           "The view that free will requires determinism to be coherent"]),

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
