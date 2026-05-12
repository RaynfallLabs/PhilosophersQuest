"""Parts of speech generators: identify the part of speech of a word
within a real sentence.
"""
from __future__ import annotations

from tools.quizgen.grammar_generators.common import make_question


# (sentence, target_word, part_of_speech)
POS_EXAMPLES = [
    # Nouns
    ("The cat sat on the mat.", "cat", "Noun"),
    ("She read a book in the garden.", "garden", "Noun"),
    ("The teacher praised the student.", "teacher", "Noun"),
    ("Hope is a powerful thing.", "Hope", "Noun"),
    ("Freedom is precious.", "Freedom", "Noun"),
    ("The dog barked loudly.", "dog", "Noun"),
    ("Children love ice cream.", "Children", "Noun"),
    ("Mountains rise above the clouds.", "Mountains", "Noun"),
    ("Honesty is the best policy.", "Honesty", "Noun"),
    ("She wore a red dress to the party.", "dress", "Noun"),
    # Verbs
    ("The cat sat on the mat.", "sat", "Verb"),
    ("Birds fly south for winter.", "fly", "Verb"),
    ("She runs every morning.", "runs", "Verb"),
    ("They sing beautifully.", "sing", "Verb"),
    ("The bell rang at noon.", "rang", "Verb"),
    ("Tom is reading a book.", "is", "Verb"),
    ("We danced all night.", "danced", "Verb"),
    ("He built a treehouse.", "built", "Verb"),
    ("The leaves fell from the tree.", "fell", "Verb"),
    ("She painted a beautiful landscape.", "painted", "Verb"),
    # Adjectives
    ("The red ball bounced high.", "red", "Adjective"),
    ("She wore a beautiful dress.", "beautiful", "Adjective"),
    ("The old man walked slowly.", "old", "Adjective"),
    ("A tall tree shaded the yard.", "tall", "Adjective"),
    ("The dog has soft fur.", "soft", "Adjective"),
    ("She gave a brilliant answer.", "brilliant", "Adjective"),
    ("The cold wind blew.", "cold", "Adjective"),
    ("They climbed the steep hill.", "steep", "Adjective"),
    ("She drew a perfect circle.", "perfect", "Adjective"),
    ("Three friends sat together.", "Three", "Adjective"),
    # Adverbs
    ("She sings beautifully.", "beautifully", "Adverb"),
    ("He runs quickly.", "quickly", "Adverb"),
    ("They walked slowly home.", "slowly", "Adverb"),
    ("She arrived early.", "early", "Adverb"),
    ("The team played well.", "well", "Adverb"),
    ("He spoke quietly to her.", "quietly", "Adverb"),
    ("She always smiles.", "always", "Adverb"),
    ("They never argue.", "never", "Adverb"),
    ("He laughed loudly.", "loudly", "Adverb"),
    ("She drives carefully.", "carefully", "Adverb"),
    # Prepositions
    ("The cat sat on the mat.", "on", "Preposition"),
    ("The book is under the table.", "under", "Preposition"),
    ("She walked into the room.", "into", "Preposition"),
    ("The cat ran across the road.", "across", "Preposition"),
    ("He sat beside the fire.", "beside", "Preposition"),
    ("She lives near the park.", "near", "Preposition"),
    ("The bird flew over the trees.", "over", "Preposition"),
    ("Don't speak during the movie.", "during", "Preposition"),
    ("The light came through the window.", "through", "Preposition"),
    ("She works for a hospital.", "for", "Preposition"),
    # Pronouns
    ("He went to the store.", "He", "Pronoun"),
    ("She loves chocolate.", "She", "Pronoun"),
    ("They will arrive soon.", "They", "Pronoun"),
    ("This is my favorite book.", "This", "Pronoun"),
    ("Whoever finds it gets the prize.", "Whoever", "Pronoun"),
    ("She gave it to him.", "him", "Pronoun"),
    ("We invited them yesterday.", "We", "Pronoun"),
    ("Everyone laughed at the joke.", "Everyone", "Pronoun"),
    ("Nobody knows the answer.", "Nobody", "Pronoun"),
    ("Who is at the door?", "Who", "Pronoun"),
    # Conjunctions
    ("Bread and butter.", "and", "Conjunction"),
    ("She studied hard but failed the test.", "but", "Conjunction"),
    ("Stay home or come with us.", "or", "Conjunction"),
    ("He didn't go because he was tired.", "because", "Conjunction"),
    ("Although it rained, we went out.", "Although", "Conjunction"),
    ("If you study, you will pass.", "If", "Conjunction"),
    ("Wait until I arrive.", "until", "Conjunction"),
    ("She'll come unless it snows.", "unless", "Conjunction"),
    ("I read while he cooked.", "while", "Conjunction"),
    ("Tea or coffee?", "or", "Conjunction"),
    # Interjections
    ("Wow! That's amazing.", "Wow", "Interjection"),
    ("Ouch! That hurt!", "Ouch", "Interjection"),
    ("Hooray! We won!", "Hooray", "Interjection"),
    ("Oh, I didn't see you.", "Oh", "Interjection"),
    ("Hey! Wait for me!", "Hey", "Interjection"),
    ("Yikes! That's scary.", "Yikes", "Interjection"),
    ("Alas, the dream is over.", "Alas", "Interjection"),
    ("Hurrah for the victors!", "Hurrah", "Interjection"),
    # Articles
    ("The cat sat down.", "The", "Article"),
    ("A bird flew by.", "A", "Article"),
    ("She bought an apple.", "an", "Article"),
    ("The teacher arrived early.", "The", "Article"),
    ("A man walked in.", "A", "Article"),
    ("I saw an eagle today.", "an", "Article"),
]

ALL_POS = ["Noun", "Verb", "Adjective", "Adverb", "Preposition", "Pronoun", "Conjunction", "Interjection", "Article"]


def generate_pos_in_sentence() -> list[dict]:
    """T1: identify part of speech of a word in a real sentence."""
    out = []
    for sentence, word, pos in POS_EXAMPLES:
        distractors = [p for p in ALL_POS if p != pos][:3]
        out.append(make_question(
            tier=1,
            topic_cell="parts_of_speech",
            strategy="pos_in_sentence",
            pillar="parts_of_speech",
            question=f"In '{sentence}' — what part of speech is '{word}'?",
            answer=pos,
            distractors=distractors,
            context=f"'{word}' is a {pos.lower()} in this sentence.",
        ))
    return out


# Part-of-speech definitions
POS_DEFINITIONS = [
    ("Noun", "Names a person, place, thing, or idea"),
    ("Verb", "Expresses an action or state of being"),
    ("Adjective", "Modifies a noun, telling which one, what kind, or how many"),
    ("Adverb", "Modifies a verb, adjective, or another adverb"),
    ("Preposition", "Shows a relationship between a noun and another word"),
    ("Pronoun", "Replaces a noun (he, she, it, they, we, etc.)"),
    ("Conjunction", "Joins words, phrases, or clauses (and, but, or, because)"),
    ("Interjection", "Expresses emotion or sudden feeling (Wow! Ouch!)"),
    ("Article", "Indicates a noun's specificity (a, an, the)"),
]


def generate_pos_definitions() -> list[dict]:
    """T1: definition → part of speech."""
    out = []
    for pos, defn in POS_DEFINITIONS:
        distractors = [p for p, _ in POS_DEFINITIONS if p != pos][:3]
        out.append(make_question(
            tier=1,
            topic_cell="parts_of_speech",
            strategy="pos_definition_to_name",
            pillar="parts_of_speech",
            question=f"Which part of speech: {defn}?",
            answer=pos,
            distractors=distractors,
            context=f"{pos}: {defn}.",
        ))
    return out


def generate_all_parts_of_speech() -> list[dict]:
    out = []
    out.extend(generate_pos_in_sentence())
    out.extend(generate_pos_definitions())
    return out


if __name__ == "__main__":
    qs = generate_all_parts_of_speech()
    print(f"Generated {len(qs)} parts-of-speech questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
