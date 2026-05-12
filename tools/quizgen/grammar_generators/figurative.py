"""Figurative-language attribution: which figure of speech is this example?
Pillar 4 (figurative language + word play).
"""
from __future__ import annotations

from tools.quizgen.grammar_generators.common import make_question


# (example, type, brief_context)
FIGURES = [
    # Simile (with "like" or "as")
    ("She runs like the wind.", "Simile", "Comparison using 'like'."),
    ("His heart is as cold as ice.", "Simile", "Comparison using 'as ... as'."),
    ("Brave as a lion.", "Simile", "Direct 'as a' comparison."),
    ("Quiet like a mouse.", "Simile", "Uses 'like'."),
    ("Eyes like stars.", "Simile", "Uses 'like'."),
    # Metaphor (direct, no "like" or "as")
    ("Life is a journey.", "Metaphor", "Direct comparison without 'like' or 'as'."),
    ("Time is money.", "Metaphor", "Equates time to money."),
    ("Her laugh was music.", "Metaphor", "Direct equation."),
    ("The world is a stage.", "Metaphor", "Shakespeare's *As You Like It*."),
    ("He's a night owl.", "Metaphor", "Person = nocturnal animal."),
    # Personification
    ("The wind whispered through the trees.", "Personification", "Wind given human action (whispering)."),
    ("The sun smiled down on us.", "Personification", "Sun given human emotion."),
    ("Death came knocking at the door.", "Personification", "Death personified."),
    ("Opportunity knocks once.", "Personification", "Opportunity given action."),
    ("Time waits for no one.", "Personification", "Time given agency."),
    # Hyperbole
    ("I've told you a million times.", "Hyperbole", "Extreme exaggeration for effect."),
    ("My backpack weighs a ton.", "Hyperbole", "Obvious exaggeration."),
    ("I could eat a horse.", "Hyperbole", "Exaggeration for emphasis."),
    ("I'm dying of boredom.", "Hyperbole", "Exaggeration."),
    ("This bag weighs a ton.", "Hyperbole", "Common everyday hyperbole."),
    # Alliteration
    ("Peter Piper picked a peck of pickled peppers.", "Alliteration", "Repeated 'P' sounds at start of words."),
    ("She sells seashells by the seashore.", "Alliteration", "Repeated 'S' sounds."),
    ("Big brown bear.", "Alliteration", "Repeated 'B' sounds."),
    ("Wild and woolly.", "Alliteration", "Repeated 'W' sounds."),
    # Onomatopoeia
    ("Buzz, buzz, went the bee.", "Onomatopoeia", "Word imitates a sound."),
    ("The thunder crashed.", "Onomatopoeia", "'Crash' imitates the sound."),
    ("Hiss like a snake.", "Onomatopoeia", "'Hiss' imitates the sound."),
    ("The clock tick-tocked.", "Onomatopoeia", "'Tick-tock' imitates sound."),
    ("Pop! The balloon burst.", "Onomatopoeia", "'Pop' imitates the sound."),
    # Oxymoron
    ("Jumbo shrimp.", "Oxymoron", "Two opposite words combined."),
    ("Deafening silence.", "Oxymoron", "Two contradictory ideas."),
    ("Bittersweet memory.", "Oxymoron", "Combines opposites."),
    ("Cruel kindness.", "Oxymoron", "Contradictory pair."),
    ("Living dead.", "Oxymoron", "Apparent contradiction."),
    # Pun
    ("Time flies like an arrow; fruit flies like a banana.", "Pun", "Wordplay on multiple meanings of 'flies' and 'like'."),
    ("I'm reading a book on anti-gravity; it's impossible to put down.", "Pun", "Wordplay on 'put down'."),
    ("A bicycle can't stand on its own — it's two tired.", "Pun", "Wordplay on 'two tired' / 'too tired'."),
    # Idiom
    ("She kicked the bucket.", "Idiom", "Means 'she died' — figurative, not literal."),
    ("It's raining cats and dogs.", "Idiom", "Means heavy rain."),
    ("Break a leg!", "Idiom", "Means 'good luck!' in theater."),
    ("Bite the bullet.", "Idiom", "Means 'endure pain/difficulty'."),
    ("Spill the beans.", "Idiom", "Means 'reveal a secret'."),
    # Paradox
    ("Less is more.", "Paradox", "Apparently self-contradictory but true."),
    ("This statement is false.", "Paradox", "Liar paradox — can't be true or false."),
    ("Sometimes the only winning move is not to play.", "Paradox", "Apparent contradiction."),
    # Metonymy (substitute associated word)
    ("The pen is mightier than the sword.", "Metonymy", "'Pen' = writing/journalism; 'sword' = military force."),
    ("The crown will judge.", "Metonymy", "'Crown' = the monarchy."),
    ("Hollywood lost a star.", "Metonymy", "'Hollywood' = the film industry."),
    # Synecdoche (part-for-whole)
    ("All hands on deck!", "Synecdoche", "'Hands' = sailors (part for whole)."),
    ("Lend me your ears.", "Synecdoche", "'Ears' = attention; part for the whole."),
    ("Nice wheels.", "Synecdoche", "'Wheels' = the car."),
    # Understatement
    ("It's just a flesh wound.", "Understatement", "Saying less than the truth for effect."),
    ("Not bad.", "Understatement", "Means 'quite good'."),
    ("It's a bit warm today.", "Understatement", "When it's actually scorching."),
]


def generate_figurative_id() -> list[dict]:
    """T2-T3: identify the figure of speech."""
    out = []
    all_types = sorted({t for _, t, _ in FIGURES})

    for example, fig_type, ctx in FIGURES:
        distractors = [t for t in all_types if t != fig_type][:3]
        out.append(make_question(
            tier=2,
            topic_cell="figurative",
            strategy="identify_figure_of_speech",
            pillar="figurative",
            question=f"Which figure of speech: \"{example}\"?",
            answer=fig_type,
            distractors=distractors,
            context=ctx,
        ))
    return out


def generate_all_figurative() -> list[dict]:
    return generate_figurative_id()


if __name__ == "__main__":
    qs = generate_all_figurative()
    print(f"Generated {len(qs)} figurative-language questions")
