"""Negative-rights correction for the philosophy bank (2026-06-07).

User flagged a moral error: a T1 question made "feeding a hungry child is a
natural right" the CORRECT answer, with context calling feeding the hungry /
sheltering the homeless 'unalienable' rights. That teaches kids a POSITIVE
right (a claim on another's labor or goods) as if it were a NEGATIVE right
(life, liberty, property -- which only ask others to leave you alone). The
Declaration's unalienable rights are the negative kind.

User's principle (verbatim): "Food is not a right; anything that costs labor or
work (service or product) is not a right ... people are NEVER entitled to the
labor or services of another." Confirmed framing: NEGATIVE RIGHTS ONLY --
relational duties (a parent to a child, a promise, charity) are real moral
obligations but NOT the recipient's enforceable 'right'. The positive-rights
view (FDR's 1944 economic bill of rights) is steel-manned, not flame-baited,
and the bank's existing "parental partiality is just" content is preserved.

This script:
  1. RECASTS the lunch-ticket question (found by the unique substring
     'forgotten ticket') so the correct answer teaches the negative-vs-positive
     distinction, keeping the vivid scene + tier.
  2. APPENDS 7 reinforcing questions across T2-T4 (fallacy-collapse, the clean
     diagnostic, charity-as-virtue, parental-duty-not-universal-right, plus
     steel-manned Nozick + FDR + Bastiat legal-plunder).

Gated exactly like _manual_theology.py: answer-in-choices, parity <= 1.30,
total length budget, round-trip guard before any write.
"""
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[3] / 'data' / 'questions' / 'philosophy.json'
CAP = {1: 660, 2: 770, 3: 930, 4: 1100, 5: 1200}

# --- 1. The corrected lunch-ticket question (replaces the bad one in place) ---
FIX = {
    'tier': 1,
    'question': (
        "A monitor denies a hungry boy lunch over a lost ticket. Theo: 'Food's "
        "a basic right!' Mara: 'Feeding him is decent -- but call it his *right* "
        "and you've drafted the cook to work for free.' What distinction is Mara "
        "drawing?"
    ),
    'answer': "A liberty asks others to leave you be; a food right makes someone serve you.",
    'choices': [
        "A liberty asks others to leave you be; a food right makes someone serve you.",
        "A custom outranks a fresh rule whenever the two happen to collide.",
        "A kind act and a cruel act get judged by one and the same standard.",
        "A wise expert, not the hungry boy, should decide who gets to eat.",
    ],
    'context': (
        "Negative rights -- speech, conscience, property, moving freely -- only ask "
        "others to LEAVE YOU ALONE. A positive 'right' to a good like food, housing, "
        "or care requires others to PROVIDE it: the cook's labor, the farmer's grain, "
        "the taxpayer's money. Locke, Bastiat, and Nozick held only the first kind are "
        "truly natural, since no one is born owing you their work; the Declaration's "
        "'unalienable rights' are life, liberty, and the pursuit of happiness, not a "
        "claim on the baker. Feeding the child may still be a real duty of charity -- "
        "but that is the giver's virtue, not the boy's enforceable claim. (FDR's 1944 "
        "'economic bill of rights' argued the other way; it is steel-manned in its own "
        "question.)"
    ),
}

# --- 2. Reinforcing questions (appended) -------------------------------------
NEW = [
    {  # A -- housing-as-right soundbite collapse (fallacy ladder)
        'tier': 2,
        'question': (
            "A pamphlet declares: 'Housing is a human right -- so the city MUST hand "
            "every comer an apartment.' Devin nods. Pria stops him: 'A home is bricks "
            "someone laid on land someone owns. Whose labor and property does this "
            "*right* quietly command?'"
        ),
        'answer': "A 'right' to a thing someone must build or own is a claim on that someone.",
        'choices': [
            "A 'right' to a thing someone must build or own is a claim on that someone.",
            "Slogans printed on a pamphlet are never true, however well they're argued.",
            "The city always has the funds, so in truth no one is forced to provide it.",
            "Housing matters less than speech, so it cannot count as any right at all.",
        ],
        'context': (
            "Negative rights require only that others refrain -- leave you alone. A "
            "positive 'right' to a good like housing, food, or healthcare requires others "
            "to PROVIDE it: the builder's labor, the owner's land, the taxpayer's money. "
            "Locke, Bastiat, and Nozick argued only the first kind are natural, since no "
            "one is born owing you their work. One may still owe charity or rescue as a "
            "DUTY -- but that is the giver's virtue, not the recipient's enforceable "
            "claim. The strongest case on the other side, FDR's 1944 'economic bill of "
            "rights,' is treated in its own question."
        ),
    },
    {  # B -- charity is a free virtue, not an enforceable claim
        'tier': 2,
        'question': (
            "Old Hessa leaves bread on her sill each night for whoever's hungry. A "
            "traveler demands tomorrow's loaf as his due. Hessa: 'The gift is good "
            "BECAUSE I'm free to give it -- demand it as owed, and you've turned a "
            "kindness into a leash on me.' Why won't Hessa call the bread his due?"
        ),
        'answer': "Charity is a free virtue; made an enforceable claim, it would enslave the giver.",
        'choices': [
            "Charity is a free virtue; made an enforceable claim, it would enslave the giver.",
            "Whoever happens to need a loaf the most is the one who truly owns it.",
            "A gift once given twice becomes a contract the giver can never escape.",
            "Generosity is for fools, so the truly wise give nothing at all away.",
        ],
        'context': (
            "A duty of charity is real -- many hold we OUGHT to feed the hungry. But a "
            "duty on the giver is not a RIGHT in the receiver: if the loaf were the "
            "traveler's enforceable claim, Hessa would be conscripted to bake on command, "
            "and the act would no longer be generous at all. Thinkers in the Lockean line "
            "distinguish what is virtuous to give from what others may compel. Parents are "
            "the exception people raise -- but a parent's duty flows from a freely-taken "
            "bond to THIS child, not from every stranger's standing claim (see the "
            "partiality questions)."
        ),
    },
    {  # C -- the clean negative/positive diagnostic
        'tier': 3,
        'question': (
            "A debate coach writes four 'rights' on the board and asks for the odd one "
            "out: the one that, unlike the rest, can't be honored just by everyone "
            "leaving you alone -- it needs someone else's labor handed over. Which is it?"
        ),
        'answer': "A right to be given medical care whenever you fall ill.",
        'choices': [
            "A right to be given medical care whenever you fall ill.",
            "A right to speak against the mayor without being jailed.",
            "A right to worship, or not, as your own conscience directs.",
            "A right to keep the wages that you have honestly earned.",
        ],
        'context': (
            "The clean diagnostic for a negative vs positive right: can it be satisfied by "
            "mere non-interference? Speech, worship, and keeping your wages impose only "
            "'leave me alone' on everyone else -- classic negative rights in the Lockean "
            "tradition. A right to be GIVEN care is different in kind: it requires a "
            "specific person (a doctor, a taxpayer) to provide labor or goods, which is "
            "why Bastiat and Nozick denied such claims the name of natural rights. People "
            "may still owe care through charity or contract -- a separate question from "
            "whether it is anyone's enforceable claim."
        ),
    },
    {  # D -- Nozick "taxation on a par with forced labor" (steel-manned)
        'tier': 3,
        'question': (
            "A philosopher presses a thought: 'Tax an hour of your wages to fund "
            "another's benefit, and for that hour you worked not for yourself but for "
            "them. How is being made to labor for another's ends -- even by a vote -- "
            "different in kind from a slice of forced labor?' Which claim is he pressing?"
        ),
        'answer': "Taking earnings to fund others is, in form, conscripting the hours behind them.",
        'choices': [
            "Taking earnings to fund others is, in form, conscripting the hours behind them.",
            "All taxation is theft, so no government may collect a single coin ever.",
            "A majority vote can make any burden just, however heavy it may fall.",
            "Work carries no real value, so losing its wages costs a person nothing.",
        ],
        'context': (
            "Robert Nozick (Anarchy, State, and Utopia, 1974) argued that 'taxation of "
            "earnings from labor is on a par with forced labor': redistribute the fruits "
            "of your hours and you have, in form, commandeered those hours. It is a "
            "deliberately provocative framing, and serious critics answer it -- we accept "
            "shared rules, and owe for the roads and order we use. The skill is "
            "recognizing the argument's exact structure, not setting a tax rate: the "
            "precise claim differs from the slogan 'all taxation is theft,' which "
            "overshoots what Nozick himself defended."
        ),
    },
    {  # E -- FDR's economic bill of rights (the steel-man of positive rights)
        'tier': 4,
        'question': (
            "In 1944 a president told a war-weary nation: 'True individual freedom "
            "cannot exist without economic security. A hungry, jobless man is not free "
            "-- he is the stuff of which dictatorships are made. So a second bill of "
            "rights should guarantee a job, a home, care, and schooling.' What principle "
            "grounds his case?"
        ),
        'answer': "Real freedom is hollow without the means to use it, so security itself is a right.",
        'choices': [
            "Real freedom is hollow without the means to use it, so security itself is a right.",
            "Freedom means only that no law forbids you; means and money never matter here.",
            "The strong are meant to rule the weak, so rights are whatever the leaders grant.",
            "Tradition alone may settle rights, so no genuinely new right can be declared.",
        ],
        'context': (
            "Franklin Roosevelt's 1944 'Second Bill of Rights' is the serious case FOR "
            "positive rights: liberty on paper is empty, he argued, if hunger or "
            "joblessness leaves you unable to act on it, so a decent society should "
            "guarantee the material floor that freedom requires. Critics in the Lockean-"
            "Austrian line (Hayek, Nozick, Bastiat) reply that a 'right' to a job or a "
            "home is a claim on other people's labor and property, colliding with their "
            "liberty -- and that what government guarantees, it can ration and control. "
            "The bank's own line falls with the critics; but FDR's argument is a real and "
            "powerful one, worth stating at its strongest before answering it."
        ),
    },
    {  # F -- Bastiat legal plunder
        'tier': 3,
        'question': (
            "A merchant lobbies the council to outlaw his cheaper rival, 'for the public "
            "good.' A clerk objects: 'When one man takes another's goods we call it "
            "robbery and stop it. You've just asked the law to do the taking for you, and "
            "call it lawful.' What has the merchant turned the law into?"
        ),
        'answer': "A tool for taking what its users could never have taken by themselves.",
        'choices': [
            "A tool for taking what its users could never have taken by themselves.",
            "A fair rule that shields buyers from a dangerous, low-quality product.",
            "An honest contract that the merchant and his rival both freely agreed to.",
            "A custom so old that its plain rightness no longer needs any defending.",
        ],
        'context': (
            "Frederic Bastiat called this 'legal plunder' (The Law, 1850): using the "
            "machinery of law to do what would be robbery if a private person did it -- "
            "here, destroying a competitor instead of out-serving him. His test was "
            "simple: does the law take from some to give to others what they have not "
            "earned? Recognizing the move matters because legal plunder always arrives "
            "dressed as 'the public good' -- exactly the costume that makes it hard to "
            "see."
        ),
    },
    {  # G -- a parent's duty is real but does not generalize into a universal right
        'tier': 2,
        'question': (
            "Bea insists: 'If a father must feed his own child, then food is a universal "
            "right -- every hungry person may demand it of anyone.' Her uncle: 'Watch the "
            "leap. A father's duty flows from being THIS child's father, a bond he took "
            "on. It hands no stranger a claim on the baker.' Where is Bea's mistake?"
        ),
        'answer': "She stretched a specific, taken-on bond into everyone's claim on everyone.",
        'choices': [
            "She stretched a specific, taken-on bond into everyone's claim on everyone.",
            "She forgot that parents in truth owe their own children nothing at all.",
            "She assumed that hunger is real, when most need is merely imagined.",
            "She trusted a warm feeling instead of counting the costs and benefits.",
        ],
        'context': (
            "The bank holds that parents genuinely owe their children -- a real duty (see "
            "the partiality questions, where favoring your own child is just). But that "
            "duty is grounded in a particular relationship the parent entered, not in a "
            "universal right the child shares with every stranger against every baker. "
            "Bea's slip is the common one: sliding from 'A owes B because of their bond' "
            "to 'everyone owes everyone.' A real obligation to the near and chosen does "
            "not generalize into an enforceable claim by all upon all."
        ),
    },
]


def _gate(q, tag):
    assert q['answer'] in q['choices'], (tag, 'answer-not-in-choices')
    L = [len(c) for c in q['choices']]
    ratio = max(L) / min(L)
    tot = len(q['question']) + sum(L)
    assert ratio <= 1.30, (tag, 'parity', round(ratio, 3))
    assert tot <= CAP[q['tier']], (tag, 'budget', tot, '>', CAP[q['tier']])
    assert len(q['choices']) == 4, (tag, 'need 4 choices')
    return ratio, tot


print("gating...")
r, t = _gate(FIX, 'FIX/lunch')
print(f"  FIX  T{FIX['tier']}  parity {r:.2f}  total {t}")
for i, q in enumerate(NEW):
    r, t = _gate(q, f'NEW[{i}]')
    print(f"  NEW{i} T{q['tier']}  parity {r:.2f}  total {t}")

orig = BANK.read_text(encoding='utf-8')
bank = json.loads(orig)
assert json.dumps(bank, indent=2, ensure_ascii=False) + '\n' == orig, 'round-trip mismatch -- aborting'

# locate the bad lunch question by a unique substring
matches = [i for i, q in enumerate(bank) if 'forgotten ticket' in q.get('question', '')]
assert len(matches) == 1, f'expected exactly 1 lunch question, found {len(matches)}: {matches}'
lunch_idx = matches[0]
print(f"\nreplacing lunch question at bank index {lunch_idx}")
print(f"  OLD answer: {bank[lunch_idx]['answer']!r}")
bank[lunch_idx] = {k: FIX[k] for k in ('tier', 'question', 'answer', 'choices', 'context')}
print(f"  NEW answer: {bank[lunch_idx]['answer']!r}")

before = len(bank)
for q in NEW:
    bank.append({k: q[k] for k in ('tier', 'question', 'answer', 'choices', 'context')})
print(f"\nappended {len(NEW)} reinforcing questions ({before} -> {len(bank)})")

BANK.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print("WROTE philosophy.json")
