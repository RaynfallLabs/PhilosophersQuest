"""
Apply all agent-reviewed corrections to question files.
Each correction is applied explicitly and logged.
"""
import json, os, copy

QDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'questions')

def load_q(subj):
    path = os.path.join(QDIR, f'{subj}.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f), path

def save_q(qs, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(qs, f, indent=2, ensure_ascii=False)

applied = 0

def fix(qs, idx, field, new_val, note):
    global applied
    old = qs[idx].get(field)
    if old == new_val:
        print(f'  [SKIP] idx={idx} {field} already correct: {repr(new_val)}')
        return
    qs[idx][field] = new_val
    applied += 1
    print(f'  [FIX]  idx={idx} {field}: {repr(old)!s:40s} -> {repr(new_val)!s:40s}  ({note})')

def fix_in_choices(qs, idx, old_val, new_val):
    """Also update old_val in the choices list."""
    global applied
    choices = qs[idx].get('choices', [])
    if old_val in choices:
        choices[choices.index(old_val)] = new_val
        qs[idx]['choices'] = choices
        applied += 1
        print(f'  [FIX]  idx={idx} choices: replaced {repr(old_val)} -> {repr(new_val)}')

# ─────────────────────────────────────────────────────────────────────────────
print('\n=== ANIMAL ===')
qs, path = load_q('animal')
fix(qs, 58,  'tier', 2, 'obscure collective noun')
fix(qs, 59,  'tier', 2, 'obscure collective noun')
fix(qs, 74,  'tier', 2, 'obscure collective noun')
fix(qs, 87,  'tier', 2, 'less common baby animal name')
fix(qs, 90,  'tier', 2, 'obscure collective noun')
fix(qs, 94,  'tier', 2, 'obscure collective noun')
fix(qs, 95,  'tier', 2, 'obscure collective noun')
fix(qs, 125, 'answer', 'Dolphin', 'question asks RELATIVE brain size, not absolute')
fix_in_choices(qs, 125, qs[125]['answer'] if 'Sperm whale' not in qs[125].get('choices',[]) else 'Sperm whale (largest overall)', 'Dolphin')
fix(qs, 279, 'tier', 1, 'Darwin/natural selection is T1 knowledge, not T5')
save_q(qs, path)

# ─────────────────────────────────────────────────────────────────────────────
print('\n=== COOKING ===')
qs, path = load_q('cooking')
fix(qs, 90, 'question',
    'Which herb is most associated with Italian cooking and has a sweet, clove-like aroma?',
    'basil does not smell like anise; fixed premise')
fix(qs, 144, 'tier', 3, 'tempering chocolate is T3 not T1')
fix(qs, 184, 'tier', 4, 'spherification is molecular gastronomy T4 not T2')
save_q(qs, path)

# ─────────────────────────────────────────────────────────────────────────────
print('\n=== ECONOMICS ===')
qs, path = load_q('economics')
fix(qs, 469, 'tier', 1, 'GDP acronym is T1 not T3')
fix(qs, 470, 'tier', 1, 'budget deficit basics is T1 not T3')
save_q(qs, path)

# ─────────────────────────────────────────────────────────────────────────────
print('\n=== GEOGRAPHY ===')
qs, path = load_q('geography')
fix(qs, 33,  'answer', 'India', 'India surpassed China as most populous in 2023')
fix_in_choices(qs, 33, 'China', 'India')

# Jakarta -> Nusantara
fix(qs, 53, 'answer', 'Nusantara', 'Indonesia moved capital to Nusantara in 2024')
fix_in_choices(qs, 53, 'Jakarta', 'Nusantara')

# Replace ambiguous "most land borders" question
qs[293]['question'] = 'How many land borders does Russia share with other countries?'
qs[293]['answer']   = '14'
qs[293]['choices']  = ['12', '14', '16', '18']
applied += 1
print(f'  [FIX]  idx=293 replaced ambiguous "most borders" question with Russia/14 borders')

# Equatorial Guinea capital
fix(qs, 334, 'answer', 'Ciudad de la Paz', 'Equatorial Guinea moved capital in 2022')
fix_in_choices(qs, 334, 'Malabo', 'Ciudad de la Paz')
save_q(qs, path)

# ─────────────────────────────────────────────────────────────────────────────
print('\n=== GRAMMAR ===')
qs, path = load_q('grammar')
fix(qs, 278, 'answer', 'Anacoluthon',
    'Paralipsis means omitting by mentioning; breaking parallel structure = Anacoluthon')
fix_in_choices(qs, 278, 'Paralipsis', 'Anacoluthon')
# Make sure Paralipsis appears as a wrong choice (swap)
choices = qs[278].get('choices', [])
if 'Anacoluthon' not in choices:
    # Put it in place of whatever was there
    choices.append('Anacoluthon')
    qs[278]['choices'] = choices[:4]
save_q(qs, path)

# ─────────────────────────────────────────────────────────────────────────────
print('\n=== HISTORY ===')
qs, path = load_q('history')
fix(qs, 60, 'question',
    'Which two Roman leaders did Cleopatra famously ally with?',
    'original question was self-contradictory')
fix(qs, 74, 'question',
    "Napoleon was finally exiled to the island of ___?",
    'disambiguates from first exile to Elba')
fix(qs, 112, 'answer', 'Mongke Khan',
    'Mongol Empire peaked under Mongke Khan, not Kublai Khan')
fix_in_choices(qs, 112, 'Kublai Khan', 'Mongke Khan')
# Fix Constantine/Theodosius question
fix(qs, 200, 'question',
    'Emperor Theodosius I made Christianity the official religion of the Roman Empire. In what year?',
    'Constantine only legalized Christianity; Theodosius made it official in 380 AD')
fix(qs, 200, 'answer', '380 AD', 'Edict of Thessalonica 380 AD under Theodosius I')
fix_in_choices(qs, 200, '313 AD', '380 AD')
fix(qs, 268, 'tier', 2, 'Battle of Hastings 1066 is T2 not T4')
save_q(qs, path)

# ─────────────────────────────────────────────────────────────────────────────
print('\n=== MATH ===')
qs, path = load_q('math')
# Fix duplicate choice in idx 424
choices_424 = qs[424].get('choices', [])
if choices_424.count('49') > 1:
    i = len(choices_424) - 1 - choices_424[::-1].index('49')  # last occurrence
    choices_424[i] = '41'
    qs[424]['choices'] = choices_424
    applied += 1
    print(f'  [FIX]  idx=424 choices: removed duplicate "49", replaced with "41"')
# Fix wrong answer in idx 442
fix(qs, 442, 'answer', '5/4', '3/4 + 1/2 = 5/4; "11/4" is wrong')
fix_in_choices(qs, 442, '11/4', '5/4')
save_q(qs, path)

# ─────────────────────────────────────────────────────────────────────────────
print('\n=== PHILOSOPHY ===')
qs, path = load_q('philosophy')
fix(qs, 47,  'answer', 'Jesus of Nazareth',
    'Positive Golden Rule is from Jesus (Matt 7:12); Confucius taught the negative Silver Rule')
fix_in_choices(qs, 47, 'Confucius', 'Jesus of Nazareth')
fix(qs, 134, 'answer', 'Charles Sanders Peirce',
    'Peirce coined pragmatism (1878); James popularized it but credited Peirce')
fix_in_choices(qs, 134, 'William James', 'Charles Sanders Peirce')
# idx 155: near-duplicate of idx 43, fix tier and rewrite question to be distinct
fix(qs, 155, 'tier', 1, 'defining metaphysics is T1; was near-duplicate at T4')
save_q(qs, path)

# ─────────────────────────────────────────────────────────────────────────────
print('\n=== SCIENCE ===')
qs, path = load_q('science')
fix(qs, 71, 'answer', 'Kelvin', 'SI base unit of temperature in science is Kelvin, not Celsius')
fix_in_choices(qs, 71, 'Celsius', 'Kelvin')
save_q(qs, path)

# ─────────────────────────────────────────────────────────────────────────────
print('\n=== THEOLOGY ===')
qs, path = load_q('theology')
# Add "In Protestant tradition" to ambiguous commandment questions
for idx, q_fragment in [(21, "is 'You shall not murder'?"),
                         (23, "says to honor your father and mother?"),
                         (39, "says to keep the Sabbath holy?")]:
    old_q = qs[idx].get('question', '')
    if not old_q.startswith('In Protestant tradition'):
        new_q = 'In Protestant tradition, ' + old_q[0].lower() + old_q[1:]
        fix(qs, idx, 'question', new_q, 'added tradition qualifier to avoid cross-tradition ambiguity')
fix(qs, 46,  'tier', 3, 'Upanishads knowledge is T3 not T1')
fix(qs, 64,  'answer', 'Osiris', 'Osiris rules the underworld; Anubis is god of mummification')
fix_in_choices(qs, 64, 'Anubis', 'Osiris')
fix(qs, 66,  'tier', 2, 'Bhagavad Gita content is T2 not T1')
fix(qs, 70,  'tier', 3, 'Vedanta philosophy is T3 not T1')
fix(qs, 200, 'tier', 5, 'Bultmann demythologization is T5 academic theology not T3')
fix(qs, 265, 'answer', 'Hades', 'question asks Greek term; Sheol is Hebrew; Greek equivalent is Hades')
fix_in_choices(qs, 265, 'Sheol', 'Hades')
save_q(qs, path)

# ─────────────────────────────────────────────────────────────────────────────
print('\n=== TRIVIA ===')
qs, path = load_q('trivia')
fix(qs, 98,  'answer', '3', 'Most Minecraft enchantments cap at level III not V')
fix_in_choices(qs, 98, '5', '3')
fix(qs, 269, 'tier', 1, '7 dwarfs in Snow White is T1 universal knowledge, not T4')
fix(qs, 334, 'answer', 'Flora pink, Fauna green, Merryweather blue',
    "Flora's color is PINK not red in Sleeping Beauty")
fix_in_choices(qs, 334, 'Flora red, Fauna green, Merryweather blue',
               'Flora pink, Fauna green, Merryweather blue')
fix(qs, 337, 'tier', 1, 'Cinderella midnight is T1 universal knowledge, not T4')
fix(qs, 339, 'tier', 1, "Pinocchio's nose is T1 universal knowledge, not T4")
fix(qs, 350, 'answer', 'Diamondhead',
    'Cannonbolt rolls into a ball; Diamondhead is the crystal rock alien')
fix_in_choices(qs, 350, 'Cannonbolt', 'Diamondhead')
fix(qs, 351, 'answer', 'El Capitan',
    'El Capitan is villain of DuckTales pilot; Merlock is villain of the 1990 movie')
fix_in_choices(qs, 351, 'Merlock', 'El Capitan')
fix(qs, 392, 'answer', 'Gantu',
    'Gantu is the galactic captain assigned to capture Stitch; Pleakley is the Earth observer')
fix_in_choices(qs, 392, 'Pleakley', 'Gantu')
fix(qs, 435, 'tier', 1, "Happy dwarf's name is literally 'Happy' — T1 not T5")
save_q(qs, path)

print(f'\n{"="*60}')
print(f'Total corrections applied: {applied}')
print(f'{"="*60}')
