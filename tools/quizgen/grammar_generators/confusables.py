"""Common confusables: your/you're, its/it's, etc.
Pillar 5 (grammar history + usage rules).
"""
from __future__ import annotations

from tools.quizgen.grammar_generators.common import make_question


# (sentence with blank, correct, distractors, explanation)
CONFUSABLES = [
    # your/you're
    ("___ going to love this movie.", "You're", ["Your", "Yore", "You-are"],
     "'You're' = contraction of 'you are'. 'Your' shows possession."),
    ("Is this ___ bag?", "your", ["you're", "yore", "you'r"],
     "'Your' shows possession. 'You're' = 'you are'."),
    ("___ shoes are untied.", "Your", ["You're", "Yore", "Yors"],
     "'Your' shows possession (the shoes belonging to you)."),
    ("___ the best!", "You're", ["Your", "Yore", "Yur"],
     "Contraction of 'you are'."),
    # its/it's
    ("The dog wagged ___ tail.", "its", ["it's", "its'", "it is"],
     "'Its' (no apostrophe) = possessive. 'It's' = 'it is' or 'it has'."),
    ("___ raining outside.", "It's", ["Its", "Its'", "It is"],
     "Contraction of 'it is'."),
    ("The cat licked ___ paws.", "its", ["it's", "its'", "it is"],
     "Possessive — no apostrophe."),
    ("___ been a long day.", "It's", ["Its", "Its'", "Its'"],
     "Contraction of 'it has'."),
    # their/there/they're
    ("___ going to the park.", "They're", ["Their", "There", "Thier"],
     "'They're' = 'they are'. 'Their' = possessive. 'There' = location."),
    ("That is ___ house.", "their", ["there", "they're", "thier"],
     "'Their' shows possession."),
    ("Look over ___.", "there", ["their", "they're", "thair"],
     "'There' indicates location."),
    ("___ books are on the shelf.", "Their", ["There", "They're", "Thier"],
     "Possessive — the books belonging to them."),
    # less/fewer
    ("There are ___ apples in the bowl than yesterday.", "fewer",
     ["less", "lesser", "more less"],
     "'Fewer' for countable nouns; 'less' for non-countable (mass nouns)."),
    ("I have ___ water than I thought.", "less", ["fewer", "lesser", "more less"],
     "'Less' for non-countable. Water = mass noun."),
    ("She has ___ friends than her brother.", "fewer", ["less", "lesser", "more less"],
     "Friends are countable — use 'fewer'."),
    ("This recipe needs ___ sugar.", "less", ["fewer", "lesser", "much less of"],
     "Sugar is non-countable — 'less'."),
    # who/whom
    ("___ is at the door?", "Who", ["Whom", "Whose", "Who's"],
     "'Who' = subject (doing the action of being at the door)."),
    ("To ___ should I address this letter?", "whom", ["who", "whose", "who's"],
     "'Whom' = object of preposition 'to'."),
    ("___ ate the last cookie?", "Who", ["Whom", "Whose", "Who's"],
     "'Who' = subject of the verb 'ate'."),
    ("___ gift is this?", "Whose", ["Who's", "Whom", "Who"],
     "'Whose' = possessive. 'Who's' = 'who is'."),
    # then/than
    ("This book is better ___ that one.", "than", ["then", "thann", "thann"],
     "'Than' = comparison. 'Then' = time/sequence."),
    ("First we'll eat; ___ we'll watch a movie.", "then", ["than", "thann", "than"],
     "'Then' = sequence in time."),
    ("She's taller ___ her brother.", "than", ["then", "thann", "thann"],
     "Comparison."),
    # affect/effect
    ("The storm will ___ traffic tomorrow.", "affect", ["effect", "afect", "effekt"],
     "'Affect' = verb (to influence). 'Effect' = noun (result)."),
    ("The ___ of the medicine was immediate.", "effect", ["affect", "efect", "afect"],
     "Noun — the result."),
    ("Her speech had a powerful ___.", "effect", ["affect", "efect", "afect"],
     "Noun = result."),
    ("Don't let it ___ your mood.", "affect", ["effect", "afect", "afekt"],
     "Verb = to influence."),
    # lay/lie
    ("Please ___ the book on the table.", "lay", ["lie", "laid", "lain"],
     "'Lay' is transitive — takes an object (book). 'Lie' is intransitive."),
    ("I'm going to ___ down for a nap.", "lie", ["lay", "laid", "lying"],
     "'Lie' (intransitive) when the subject reclines."),
    ("Yesterday I ___ in bed all morning.", "lay", ["laid", "lie", "lain"],
     "Past tense of 'lie' (to recline) — confusingly identical to present tense of 'lay'."),
    # accept/except
    ("I ___ your apology.", "accept", ["except", "expect", "exept"],
     "'Accept' = receive willingly. 'Except' = exclude."),
    ("Everyone came ___ Mark.", "except", ["accept", "expect", "exept"],
     "'Except' = excluding."),
    # whose/who's
    ("___ going to the concert?", "Who's", ["Whose", "Whom", "Whomst"],
     "'Who's' = 'who is'. 'Whose' = possessive."),
    ("___ jacket is this?", "Whose", ["Who's", "Whom", "Whomst"],
     "'Whose' = possessive."),
    # complement/compliment
    ("Red wine ___s steak nicely.", "complement", ["compliment", "complament", "compleement"],
     "'Complement' = completes/pairs well with. 'Compliment' = praise."),
    ("She gave me a nice ___.", "compliment", ["complement", "complament", "compliement"],
     "'Compliment' = expression of praise."),
    # principal/principle
    ("The school ___ called us in.", "principal", ["principle", "principel", "prinsipal"],
     "'Principal' = head person OR primary. 'Principle' = rule/belief."),
    ("Honesty is a basic ___.", "principle", ["principal", "principel", "principal"],
     "'Principle' = rule, belief."),
    # stationary/stationery
    ("She bought new ___ for letter-writing.", "stationery", ["stationary", "stationarie", "stationary"],
     "'Stationery' (with 'e') = paper goods. 'Stationary' (with 'a') = not moving."),
    ("The car remained ___ at the light.", "stationary", ["stationery", "stationarie", "stationarie"],
     "'Stationary' = not moving."),
]


def generate_confusables() -> list[dict]:
    """T2: pick the correct confusable in a sentence."""
    out = []
    for blank_sentence, correct, distractors, explanation in CONFUSABLES:
        out.append(make_question(
            tier=2,
            topic_cell="confusables",
            strategy="common_confusables",
            pillar="history",
            question=f"Fill the blank correctly: {blank_sentence}",
            answer=correct,
            distractors=distractors,
            context=explanation,
        ))
    return out


def generate_all_confusables() -> list[dict]:
    return generate_confusables()


if __name__ == "__main__":
    qs = generate_all_confusables()
    print(f"Generated {len(qs)} confusables questions")
