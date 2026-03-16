#!/usr/bin/env python3
"""
patch_grammar.py — Append new grammar questions to bring each tier to 100.
T1: needs 3 more  (97 → 100)
T2: needs 11 more (89 → 100)
T3: needs 48 more (52 → 100)
T4: needs 49 more (51 → 100)
T5: needs 49 more (51 → 100)
"""

import json
import sys
from pathlib import Path

GRAMMAR_PATH = Path(__file__).parent / "questions" / "grammar.json"

NEW_QUESTIONS = [

    # ── TIER 1 (3 new) ──────────────────────────────────────────────────────
    {"tier": 1, "question": "Which word is a noun?",
     "choices": ["Throw", "Bright", "Book", "Quietly"],
     "answer": "Book"},

    {"tier": 1, "question": "The plural of 'bus' is ___?",
     "choices": ["Buss", "Buses", "Busies", "Buse"],
     "answer": "Buses"},

    {"tier": 1, "question": "Which sentence is a question?",
     "choices": ["Come here now.", "What time is it?", "I am hungry.", "Stop that!"],
     "answer": "What time is it?"},

    # ── TIER 2 (11 new) ─────────────────────────────────────────────────────
    {"tier": 2, "question": "The plural of 'knife' is ___?",
     "choices": ["Knifes", "Knives", "Knieves", "Knifes"],
     "answer": "Knives"},

    {"tier": 2, "question": "The plural of 'half' is ___?",
     "choices": ["Halfs", "Halfes", "Halves", "Halvs"],
     "answer": "Halves"},

    {"tier": 2, "question": "Which word is the correct homophone? 'I can ___ the sea from here.'",
     "choices": ["sea", "see", "si", "cee"],
     "answer": "see"},

    {"tier": 2, "question": "Which word is the correct homophone? 'The ___ blew hard.'",
     "choices": ["wind", "wined", "whined", "wynd"],
     "answer": "wind"},

    {"tier": 2, "question": "The possessive form of 'James' is ___?",
     "choices": ["James'", "James's", "Jamess'", "James's' "],
     "answer": "James's"},

    {"tier": 2, "question": "An apostrophe in 'can't' marks a ___?",
     "choices": ["Possession", "Plural", "Contraction", "Quotation"],
     "answer": "Contraction"},

    {"tier": 2, "question": "Past tense of 'draw'?",
     "choices": ["Drawed", "Drew", "Drawn", "Drewn"],
     "answer": "Drew"},

    {"tier": 2, "question": "Past tense of 'blow'?",
     "choices": ["Blowed", "Blown", "Blew", "Blew'd"],
     "answer": "Blew"},

    {"tier": 2, "question": "Past tense of 'pay'?",
     "choices": ["Payed", "Paied", "Paid", "Payd"],
     "answer": "Paid"},

    {"tier": 2, "question": "Past tense of 'spring'?",
     "choices": ["Springed", "Sprung", "Sprang", "Spronged"],
     "answer": "Sprang"},

    {"tier": 2, "question": "Which sentence uses the correct apostrophe?",
     "choices": ["The dog's are barking.", "The dogs' bone is missing.", "The dog's bone is missing.", "The dogs's bone is here."],
     "answer": "The dog's bone is missing."},

    # ── TIER 3 (48 new) ─────────────────────────────────────────────────────
    {"tier": 3, "question": "A clause that cannot stand alone as a sentence is a ___ clause?",
     "choices": ["Independent", "Dependent", "Relative", "Coordinate"],
     "answer": "Dependent"},

    {"tier": 3, "question": "A clause that can stand alone as a sentence is a(n) ___ clause?",
     "choices": ["Dependent", "Subordinate", "Independent", "Adverbial"],
     "answer": "Independent"},

    {"tier": 3, "question": "Which word introduces a dependent clause? 'She left ___ it started raining.'",
     "choices": ["and", "but", "because", "or"],
     "answer": "because"},

    {"tier": 3, "question": "A comma splice occurs when two independent clauses are joined with only a ___?",
     "choices": ["Semicolon", "Comma", "Colon", "Dash"],
     "answer": "Comma"},

    {"tier": 3, "question": "Which sentence contains a comma splice?",
     "choices": ["She ran fast, and she won.", "It rained, we stayed inside.", "He studied; he passed.", "Although tired, she finished."],
     "answer": "It rained, we stayed inside."},

    {"tier": 3, "question": "A semicolon can join two ___ clauses?",
     "choices": ["Dependent", "Subordinate", "Independent", "Relative"],
     "answer": "Independent"},

    {"tier": 3, "question": "Which is correct use of a semicolon?",
     "choices": ["She ran; quickly.", "She ran; and won.", "She ran fast; she won.", "She ran fast, she won."],
     "answer": "She ran fast; she won."},

    {"tier": 3, "question": "Subject-verb agreement means the subject and verb must match in ___?",
     "choices": ["Tense only", "Voice only", "Number", "Mood"],
     "answer": "Number"},

    {"tier": 3, "question": "Which sentence has correct subject-verb agreement?",
     "choices": ["The cats runs fast.", "The cat run fast.", "The cat runs fast.", "The cat running fast."],
     "answer": "The cat runs fast."},

    {"tier": 3, "question": "Which sentence has correct subject-verb agreement?",
     "choices": ["Neither he nor she are ready.", "Neither he nor she is ready.", "Neither he nor she were ready.", "Neither he nor she am ready."],
     "answer": "Neither he nor she is ready."},

    {"tier": 3, "question": "Parallel structure means items in a list must have the same ___?",
     "choices": ["Length", "Grammatical form", "Meaning", "Syllable count"],
     "answer": "Grammatical form"},

    {"tier": 3, "question": "Which sentence uses parallel structure?",
     "choices": ["She likes hiking, to swim, and runs.", "She likes hiking, swimming, and running.", "She likes to hike, swimming, and run.", "She likes hike, swim, run."],
     "answer": "She likes hiking, swimming, and running."},

    {"tier": 3, "question": "An introductory phrase is generally followed by a ___?",
     "choices": ["Semicolon", "Colon", "Comma", "Period"],
     "answer": "Comma"},

    {"tier": 3, "question": "Which correctly punctuates an introductory phrase?",
     "choices": ["After the storm the sun returned.", "After the storm; the sun returned.", "After the storm, the sun returned.", "After the storm: the sun returned."],
     "answer": "After the storm, the sun returned."},

    {"tier": 3, "question": "A non-restrictive clause adds extra information and is set off by ___?",
     "choices": ["Semicolons", "Colons", "Commas", "Dashes only"],
     "answer": "Commas"},

    {"tier": 3, "question": "Which word typically introduces a non-restrictive relative clause?",
     "choices": ["That", "Which", "Who only", "Whose only"],
     "answer": "Which"},

    {"tier": 3, "question": "Which word typically introduces a restrictive relative clause?",
     "choices": ["Which", "That", "Whom", "Whose"],
     "answer": "That"},

    {"tier": 3, "question": "A run-on sentence contains two or more independent clauses without proper ___?",
     "choices": ["Subjects", "Verbs", "Punctuation or conjunctions", "Adjectives"],
     "answer": "Punctuation or conjunctions"},

    {"tier": 3, "question": "The Oxford comma is placed before the ___ item in a list?",
     "choices": ["First", "Second", "Last", "Middle"],
     "answer": "Last"},

    {"tier": 3, "question": "Which sentence uses the Oxford comma?",
     "choices": ["I bought milk, eggs and butter.", "I bought milk, eggs, and butter.", "I bought milk eggs, and butter.", "I bought milk eggs and butter."],
     "answer": "I bought milk, eggs, and butter."},

    {"tier": 3, "question": "A dangling modifier has no clear ___ to modify?",
     "choices": ["Verb", "Subject", "Referent", "Object"],
     "answer": "Referent"},

    {"tier": 3, "question": "Which sentence contains a dangling modifier?",
     "choices": ["Running fast, she won the race.", "Running fast, the race was won.", "She won the race, running fast.", "She ran fast and won."],
     "answer": "Running fast, the race was won."},

    {"tier": 3, "question": "A misplaced modifier is a modifier placed too far from the word it ___?",
     "choices": ["Defines", "Replaces", "Modifies", "Introduces"],
     "answer": "Modifies"},

    {"tier": 3, "question": "Which verb mood expresses a command?",
     "choices": ["Indicative", "Subjunctive", "Imperative", "Conditional"],
     "answer": "Imperative"},

    {"tier": 3, "question": "Which verb mood expresses facts or opinions?",
     "choices": ["Subjunctive", "Imperative", "Indicative", "Conditional"],
     "answer": "Indicative"},

    {"tier": 3, "question": "Which verb mood expresses wishes or hypotheticals?",
     "choices": ["Indicative", "Subjunctive", "Imperative", "Interrogative"],
     "answer": "Subjunctive"},

    {"tier": 3, "question": "In 'If I were you, I would go,' 'were' is an example of ___?",
     "choices": ["Past indicative", "Subjunctive mood", "Imperative mood", "Conditional perfect"],
     "answer": "Subjunctive mood"},

    {"tier": 3, "question": "An appositive is a noun phrase that renames the ___ next to it?",
     "choices": ["Verb", "Adjective", "Noun", "Adverb"],
     "answer": "Noun"},

    {"tier": 3, "question": "Which sentence contains a correctly punctuated appositive?",
     "choices": ["My sister, Lisa, is a doctor.", "My sister Lisa, is a doctor.", "My sister Lisa is, a doctor.", "My sister, Lisa is a doctor."],
     "answer": "My sister, Lisa, is a doctor."},

    {"tier": 3, "question": "A colon is used to introduce a list after a ___?",
     "choices": ["Verb alone", "Complete independent clause", "Dependent clause", "Prepositional phrase"],
     "answer": "Complete independent clause"},

    {"tier": 3, "question": "Which correctly uses a colon?",
     "choices": ["She needs: milk and eggs.", "She needs the following: milk and eggs.", "She: needs milk and eggs.", "She needs milk: and eggs."],
     "answer": "She needs the following: milk and eggs."},

    {"tier": 3, "question": "A sentence fragment is missing a subject, a verb, or a ___?",
     "choices": ["Complete thought", "Comma", "Object", "Conjunction"],
     "answer": "Complete thought"},

    {"tier": 3, "question": "Which is a sentence fragment?",
     "choices": ["She runs daily.", "Because it was raining.", "He left early.", "They won the game."],
     "answer": "Because it was raining."},

    {"tier": 3, "question": "'Neither the students nor the teacher ___ ready.' Which verb form is correct?",
     "choices": ["are", "were", "is", "been"],
     "answer": "is"},

    {"tier": 3, "question": "A coordinating conjunction joins two elements of ___ importance?",
     "choices": ["Unequal", "Equal", "Subordinate", "Dependent"],
     "answer": "Equal"},

    {"tier": 3, "question": "The acronym FANBOYS stands for the ___ coordinating conjunctions?",
     "choices": ["Seven", "Six", "Eight", "Five"],
     "answer": "Seven"},

    {"tier": 3, "question": "Which is NOT one of the FANBOYS conjunctions?",
     "choices": ["For", "Although", "But", "So"],
     "answer": "Although"},

    {"tier": 3, "question": "A subordinating conjunction introduces a ___ clause?",
     "choices": ["Independent", "Coordinate", "Dependent", "Appositive"],
     "answer": "Dependent"},

    {"tier": 3, "question": "Which is a subordinating conjunction?",
     "choices": ["And", "But", "Although", "Or"],
     "answer": "Although"},

    {"tier": 3, "question": "The past participle of 'write' is ___?",
     "choices": ["Wrote", "Written", "Writed", "Write"],
     "answer": "Written"},

    {"tier": 3, "question": "The past participle of 'break' is ___?",
     "choices": ["Broke", "Broken", "Breaked", "Break"],
     "answer": "Broken"},

    {"tier": 3, "question": "The past participle of 'speak' is ___?",
     "choices": ["Spoke", "Spoken", "Speaked", "Speak"],
     "answer": "Spoken"},

    {"tier": 3, "question": "The past participle of 'give' is ___?",
     "choices": ["Gave", "Given", "Gived", "Give"],
     "answer": "Given"},

    {"tier": 3, "question": "The past participle of 'eat' is ___?",
     "choices": ["Ate", "Eaten", "Eated", "Eat"],
     "answer": "Eaten"},

    {"tier": 3, "question": "A gerund is a verb form ending in '-ing' that functions as a ___?",
     "choices": ["Verb", "Adjective", "Noun", "Adverb"],
     "answer": "Noun"},

    {"tier": 3, "question": "An infinitive is the base form of a verb usually preceded by ___?",
     "choices": ["A", "The", "To", "Is"],
     "answer": "To"},

    {"tier": 3, "question": "A participle is a verb form that functions as a(n) ___?",
     "choices": ["Noun", "Adjective", "Adverb", "Conjunction"],
     "answer": "Adjective"},

    {"tier": 3, "question": "In 'Swimming is fun,' 'swimming' is a ___?",
     "choices": ["Participle", "Gerund", "Infinitive", "Present tense verb"],
     "answer": "Gerund"},

    # ── TIER 4 (49 new) ─────────────────────────────────────────────────────
    {"tier": 4, "question": "A sentence in which the subject receives the action is in ___ voice?",
     "choices": ["Active", "Passive", "Indicative", "Subjunctive"],
     "answer": "Passive"},

    {"tier": 4, "question": "Which sentence is in active voice?",
     "choices": ["The cake was eaten by her.", "The window was broken.", "She ate the cake.", "Mistakes were made."],
     "answer": "She ate the cake."},

    {"tier": 4, "question": "The conditional perfect tense is formed with 'would have' + ___?",
     "choices": ["Present participle", "Past participle", "Infinitive", "Past tense"],
     "answer": "Past participle"},

    {"tier": 4, "question": "Which is a first conditional sentence (real possibility)?",
     "choices": ["If I were rich, I would travel.", "If she had studied, she would have passed.", "If it rains, I will stay home.", "If he were here, we'd celebrate."],
     "answer": "If it rains, I will stay home."},

    {"tier": 4, "question": "Which is a second conditional sentence (unreal present)?",
     "choices": ["If it rains, I will stay home.", "If I were rich, I would travel.", "If she had studied, she would have passed.", "When it rains, I stay home."],
     "answer": "If I were rich, I would travel."},

    {"tier": 4, "question": "Which is a third conditional sentence (unreal past)?",
     "choices": ["If it rains, I will stay home.", "If I were rich, I would travel.", "If she had studied, she would have passed.", "I stay home if it rains."],
     "answer": "If she had studied, she would have passed."},

    {"tier": 4, "question": "An em dash is used to indicate a(n) ___?",
     "choices": ["Hyphenated compound", "Abbreviation", "Abrupt break or emphasis", "Decimal point"],
     "answer": "Abrupt break or emphasis"},

    {"tier": 4, "question": "A hyphen is used to join words in a ___ adjective before a noun?",
     "choices": ["Predicate", "Compound", "Absolute", "Participial"],
     "answer": "Compound"},

    {"tier": 4, "question": "Which is correctly hyphenated?",
     "choices": ["A well known author", "A well-known author", "A wellknown author", "A well known-author"],
     "answer": "A well-known author"},

    {"tier": 4, "question": "Ellipsis marks (…) indicate ___?",
     "choices": ["Emphasis", "A list follows", "An omission or trailing off", "A definition"],
     "answer": "An omission or trailing off"},

    {"tier": 4, "question": "Brackets [ ] within a quotation are used to enclose ___?",
     "choices": ["The speaker's exact words", "Editor's clarifications", "Ironic comments", "Foreign phrases"],
     "answer": "Editor's clarifications"},

    {"tier": 4, "question": "A nominative absolute is a phrase consisting of a noun and a ___?",
     "choices": ["Verb in finite form", "Participle or adjective, grammatically independent", "Preposition", "Conjunction"],
     "answer": "Participle or adjective, grammatically independent"},

    {"tier": 4, "question": "The subjunctive form in 'I recommend that he ___ on time' is ___?",
     "choices": ["is", "are", "be", "was"],
     "answer": "be"},

    {"tier": 4, "question": "Polysyndeton is the use of ___ conjunctions than usual?",
     "choices": ["Fewer", "More", "No", "Inverted"],
     "answer": "More"},

    {"tier": 4, "question": "Asyndeton is the deliberate ___ of conjunctions?",
     "choices": ["Repetition", "Inversion", "Omission", "Addition"],
     "answer": "Omission"},

    {"tier": 4, "question": "Anaphora is the repetition of a word or phrase at the ___ of successive clauses?",
     "choices": ["End", "Middle", "Beginning", "Random position"],
     "answer": "Beginning"},

    {"tier": 4, "question": "Epistrophe is the repetition of a word or phrase at the ___ of successive clauses?",
     "choices": ["Beginning", "Middle", "End", "Random position"],
     "answer": "End"},

    {"tier": 4, "question": "Chiasmus reverses the order of words in ___ parallel phrases?",
     "choices": ["Three", "Four", "Two", "Five"],
     "answer": "Two"},

    {"tier": 4, "question": "Antithesis places contrasting ideas in ___ grammatical structure?",
     "choices": ["Random", "Unequal", "Parallel", "Fragmented"],
     "answer": "Parallel"},

    {"tier": 4, "question": "A syllepsis (or zeugma) uses one word to govern two others in ___ senses?",
     "choices": ["Identical", "Different", "Passive", "Active"],
     "answer": "Different"},

    {"tier": 4, "question": "Litotes is a form of understatement using ___?",
     "choices": ["Exaggeration", "Irony only", "Double negatives", "Repetition"],
     "answer": "Double negatives"},

    {"tier": 4, "question": "Which is an example of litotes?",
     "choices": ["He is a giant among men.", "She is not unkind.", "The fire burned endlessly.", "He ran like the wind."],
     "answer": "She is not unkind."},

    {"tier": 4, "question": "A split infinitive places a word between 'to' and the ___?",
     "choices": ["Subject", "Object", "Verb", "Complement"],
     "answer": "Verb"},

    {"tier": 4, "question": "Which sentence contains a split infinitive?",
     "choices": ["She wanted to run faster.", "She tried to quickly finish.", "She finished quickly.", "She ran to finish."],
     "answer": "She tried to quickly finish."},

    {"tier": 4, "question": "The pluperfect tense is also called the ___?",
     "choices": ["Present perfect", "Future perfect", "Past perfect", "Simple past"],
     "answer": "Past perfect"},

    {"tier": 4, "question": "The future perfect tense expresses an action completed ___ a future point?",
     "choices": ["After", "During", "Before", "Despite"],
     "answer": "Before"},

    {"tier": 4, "question": "Which sentence is in the future perfect tense?",
     "choices": ["She will run the race.", "She has run the race.", "By noon, she will have run the race.", "She ran the race yesterday."],
     "answer": "By noon, she will have run the race."},

    {"tier": 4, "question": "A correlative conjunction works in pairs, such as ___?",
     "choices": ["And/but", "Either/or", "Although/because", "That/which"],
     "answer": "Either/or"},

    {"tier": 4, "question": "Which is a correlative conjunction pair?",
     "choices": ["For/yet", "Neither/nor", "Since/until", "While/when"],
     "answer": "Neither/nor"},

    {"tier": 4, "question": "The case of a pronoun used as a subject is ___?",
     "choices": ["Objective", "Possessive", "Nominative", "Reflexive"],
     "answer": "Nominative"},

    {"tier": 4, "question": "The case of a pronoun used as an object is ___?",
     "choices": ["Nominative", "Possessive", "Objective", "Reflexive"],
     "answer": "Objective"},

    {"tier": 4, "question": "Which pronoun is in the nominative case?",
     "choices": ["Him", "Her", "Them", "They"],
     "answer": "They"},

    {"tier": 4, "question": "Which pronoun is in the objective case?",
     "choices": ["He", "She", "Whom", "Who"],
     "answer": "Whom"},

    {"tier": 4, "question": "'Who' is used as a ___ in a clause?",
     "choices": ["Object", "Possessive", "Subject", "Reflexive"],
     "answer": "Subject"},

    {"tier": 4, "question": "Which is correct? '___ did you speak to?'",
     "choices": ["Who", "Whom", "Whose", "Which"],
     "answer": "Whom"},

    {"tier": 4, "question": "A predicate adjective follows a linking verb and modifies the ___?",
     "choices": ["Verb", "Object", "Subject", "Adverb"],
     "answer": "Subject"},

    {"tier": 4, "question": "A predicate nominative follows a linking verb and renames the ___?",
     "choices": ["Object", "Verb", "Subject", "Adverb"],
     "answer": "Subject"},

    {"tier": 4, "question": "In 'She is a teacher,' 'a teacher' is the ___?",
     "choices": ["Direct object", "Indirect object", "Predicate nominative", "Predicate adjective"],
     "answer": "Predicate nominative"},

    {"tier": 4, "question": "In 'The soup tastes salty,' 'salty' is the ___?",
     "choices": ["Direct object", "Indirect object", "Predicate nominative", "Predicate adjective"],
     "answer": "Predicate adjective"},

    {"tier": 4, "question": "An absolute phrase modifies the entire ___ rather than a single word?",
     "choices": ["Clause", "Predicate", "Sentence", "Subject"],
     "answer": "Sentence"},

    {"tier": 4, "question": "Parenthetical expressions are set off from the rest of the sentence by ___?",
     "choices": ["Colons", "Semicolons", "Commas or parentheses", "Hyphens"],
     "answer": "Commas or parentheses"},

    {"tier": 4, "question": "When two adjectives equally modify a noun, they are separated by a ___?",
     "choices": ["Semicolon", "Colon", "Comma", "Hyphen"],
     "answer": "Comma"},

    {"tier": 4, "question": "Which is correct for cumulative adjectives?",
     "choices": ["A, large red barn", "A large, red barn", "A large red barn", "A large; red barn"],
     "answer": "A large red barn"},

    {"tier": 4, "question": "The rhetorical device of asking a question not meant to be answered is a(n) ___?",
     "choices": ["Aporia", "Rhetorical question", "Anaphora", "Antithesis"],
     "answer": "Rhetorical question"},

    {"tier": 4, "question": "A sentence where the main clause comes before subordinate details is ___?",
     "choices": ["Periodic", "Loose", "Balanced", "Inverted"],
     "answer": "Loose"},

    {"tier": 4, "question": "A periodic sentence builds toward its main clause at the ___?",
     "choices": ["Beginning", "Middle", "End", "Start of the second clause"],
     "answer": "End"},

    {"tier": 4, "question": "A balanced sentence has two parts that are ___ in structure?",
     "choices": ["Contrasting only", "Identical in length only", "Parallel", "Fragmented"],
     "answer": "Parallel"},

    {"tier": 4, "question": "Inverted syntax places the ___ before the subject?",
     "choices": ["Object", "Complement only", "Verb or complement", "Conjunction"],
     "answer": "Verb or complement"},

    {"tier": 4, "question": "A conjunctive adverb ('however,' 'therefore') joining two independent clauses requires a ___ before it?",
     "choices": ["Comma", "Colon", "Semicolon", "Period only"],
     "answer": "Semicolon"},

    # ── TIER 5 (49 new) ─────────────────────────────────────────────────────
    {"tier": 5, "question": "The grammatical term for the base form of a verb is ___?",
     "choices": ["Gerund", "Participle", "Infinitive", "Supine"],
     "answer": "Infinitive"},

    {"tier": 5, "question": "A verb form used as a noun is a ___?",
     "choices": ["Participle", "Gerund", "Infinitive", "Verbal adjective"],
     "answer": "Gerund"},

    {"tier": 5, "question": "The Latin term 'ad verbum' means ___?",
     "choices": ["To the noun", "Word for word", "To the verb", "Through speech"],
     "answer": "Word for word"},

    {"tier": 5, "question": "The Latin root 'gram' (as in 'grammar') means ___?",
     "choices": ["Speech", "Letter or writing", "Word", "Thought"],
     "answer": "Letter or writing"},

    {"tier": 5, "question": "The Greek root 'syntax' (syntassein) means ___?",
     "choices": ["To write together", "To arrange together", "To speak clearly", "To define words"],
     "answer": "To arrange together"},

    {"tier": 5, "question": "The study of meaning in language is called ___?",
     "choices": ["Syntax", "Phonology", "Semantics", "Morphology"],
     "answer": "Semantics"},

    {"tier": 5, "question": "The study of word formation and structure is called ___?",
     "choices": ["Syntax", "Semantics", "Phonology", "Morphology"],
     "answer": "Morphology"},

    {"tier": 5, "question": "The study of sound systems in language is called ___?",
     "choices": ["Morphology", "Phonology", "Semantics", "Syntax"],
     "answer": "Phonology"},

    {"tier": 5, "question": "The smallest unit of meaning in a word is a ___?",
     "choices": ["Phoneme", "Morpheme", "Syllable", "Grapheme"],
     "answer": "Morpheme"},

    {"tier": 5, "question": "A variant pronunciation of a phoneme in a specific context is a(n) ___?",
     "choices": ["Morpheme", "Grapheme", "Phoneme", "Allophone"],
     "answer": "Allophone"},

    {"tier": 5, "question": "A morpheme that can stand alone as a word is ___?",
     "choices": ["Bound", "Inflectional", "Free", "Derivational"],
     "answer": "Free"},

    {"tier": 5, "question": "A morpheme that cannot stand alone (like '-ness' or 'un-') is ___?",
     "choices": ["Free", "Lexical", "Bound", "Root"],
     "answer": "Bound"},

    {"tier": 5, "question": "The prefix 'un-' in 'unhappy' is a ___ morpheme?",
     "choices": ["Inflectional", "Derivational", "Free", "Suppletion"],
     "answer": "Derivational"},

    {"tier": 5, "question": "The suffix '-s' in 'cats' is a(n) ___ morpheme?",
     "choices": ["Derivational", "Inflectional", "Free", "Bound lexical"],
     "answer": "Inflectional"},

    {"tier": 5, "question": "Suppletion in morphology refers to an irregular root change, as in ___?",
     "choices": ["run/ran", "go/went", "walk/walked", "talk/talked"],
     "answer": "go/went"},

    {"tier": 5, "question": "The rhetorical device of deliberately using more words than necessary is ___?",
     "choices": ["Ellipsis", "Pleonasm", "Asyndeton", "Aposiopesis"],
     "answer": "Pleonasm"},

    {"tier": 5, "question": "Aposiopesis is when a speaker deliberately ___?",
     "choices": ["Repeats key words", "Breaks off mid-sentence", "Inverts word order", "Omits conjunctions"],
     "answer": "Breaks off mid-sentence"},

    {"tier": 5, "question": "Hyperbaton refers to the unusual ___ of words for rhetorical effect?",
     "choices": ["Repetition", "Omission", "Order", "Definition"],
     "answer": "Order"},

    {"tier": 5, "question": "Tmesis is the insertion of a word ___ a compound word or phrase?",
     "choices": ["After", "Before", "Inside", "Beneath"],
     "answer": "Inside"},

    {"tier": 5, "question": "The rhetorical term for a sudden, digressive address to an absent person or abstraction is ___?",
     "choices": ["Apostrophe", "Anaphora", "Antithesis", "Aporia"],
     "answer": "Apostrophe"},

    {"tier": 5, "question": "Paralipsis (or praeteritio) draws attention to something by ___?",
     "choices": ["Repeating it three times", "Claiming to pass over it", "Inverting its meaning", "Omitting all conjunctions"],
     "answer": "Claiming to pass over it"},

    {"tier": 5, "question": "Hendiadys expresses a single idea through ___ coordinated nouns or adjectives?",
     "choices": ["Three", "Two", "Four", "Five"],
     "answer": "Two"},

    {"tier": 5, "question": "The term 'cataphora' means a pronoun that refers to a noun ___?",
     "choices": ["Previously mentioned", "Not mentioned at all", "Mentioned later in the text", "In a different sentence only"],
     "answer": "Mentioned later in the text"},

    {"tier": 5, "question": "The term 'anaphora' in grammar (not rhetoric) means a pronoun that refers to a noun ___?",
     "choices": ["Mentioned later", "Never mentioned", "Previously mentioned", "In a different paragraph"],
     "answer": "Previously mentioned"},

    {"tier": 5, "question": "The Latin term 'in medias res' literally means ___?",
     "choices": ["From the beginning", "Into the middle of things", "To the end", "In the passive voice"],
     "answer": "Into the middle of things"},

    {"tier": 5, "question": "A hapax legomenon is a word that appears ___ in a corpus?",
     "choices": ["Frequently", "Never", "Only once", "Twice"],
     "answer": "Only once"},

    {"tier": 5, "question": "The genitive case primarily indicates ___?",
     "choices": ["Action", "Possession or source", "Location", "Instrument"],
     "answer": "Possession or source"},

    {"tier": 5, "question": "The dative case primarily indicates ___?",
     "choices": ["Possession", "Direct object", "Indirect object or recipient", "Location"],
     "answer": "Indirect object or recipient"},

    {"tier": 5, "question": "The accusative case primarily indicates the ___?",
     "choices": ["Subject", "Indirect object", "Direct object", "Possessor"],
     "answer": "Direct object"},

    {"tier": 5, "question": "The nominative case primarily marks the ___?",
     "choices": ["Direct object", "Subject", "Possessor", "Indirect object"],
     "answer": "Subject"},

    {"tier": 5, "question": "The vocative case is used for ___?",
     "choices": ["Possession", "Direct address", "Indirect object", "Motion toward"],
     "answer": "Direct address"},

    {"tier": 5, "question": "The ablative case in Latin expresses separation, instrument, or ___?",
     "choices": ["Possession", "Direct object", "Manner/agent", "Motion toward"],
     "answer": "Manner/agent"},

    {"tier": 5, "question": "Ergative-absolutive languages mark the subject of a transitive verb differently from ___?",
     "choices": ["The object of a transitive verb", "The subject of an intransitive verb", "All pronouns", "All nouns"],
     "answer": "The subject of an intransitive verb"},

    {"tier": 5, "question": "A cleft sentence ('It was John who left') splits a simple sentence to ___?",
     "choices": ["Make it passive", "Add negation", "Focus or emphasize an element", "Create a question"],
     "answer": "Focus or emphasize an element"},

    {"tier": 5, "question": "A pseudo-cleft sentence begins with a ___?",
     "choices": ["Relative clause", "Wh-nominal clause ('What I want is...')", "Passive construction", "Subordinating conjunction"],
     "answer": "Wh-nominal clause ('What I want is...')"},

    {"tier": 5, "question": "Extraposition moves a clause from its normal position to the ___ of the sentence?",
     "choices": ["Front", "Middle", "End", "Subject position"],
     "answer": "End"},

    {"tier": 5, "question": "In transformational grammar, deep structure represents ___?",
     "choices": ["Surface word order", "Phonological form", "Underlying meaning", "Morphological form"],
     "answer": "Underlying meaning"},

    {"tier": 5, "question": "Government and Binding theory was developed by ___?",
     "choices": ["Ferdinand de Saussure", "Noam Chomsky", "Leonard Bloomfield", "Edward Sapir"],
     "answer": "Noam Chomsky"},

    {"tier": 5, "question": "The Sapir-Whorf hypothesis proposes that language ___ thought?",
     "choices": ["Has no effect on", "Perfectly mirrors", "Influences or determines", "Contradicts"],
     "answer": "Influences or determines"},

    {"tier": 5, "question": "Synchronic linguistics studies a language ___?",
     "choices": ["Through history", "At one point in time", "Across dialects", "In writing only"],
     "answer": "At one point in time"},

    {"tier": 5, "question": "Diachronic linguistics studies a language ___?",
     "choices": ["At one point in time", "Through its historical development", "Across social classes", "In spoken form only"],
     "answer": "Through its historical development"},

    {"tier": 5, "question": "Ferdinand de Saussure distinguished between 'langue' (the system) and 'parole,' which means ___?",
     "choices": ["Written text", "Individual speech acts", "Grammar rules", "Pronunciation"],
     "answer": "Individual speech acts"},

    {"tier": 5, "question": "The term 'idiolect' refers to ___?",
     "choices": ["A regional dialect", "An individual's personal language variety", "A formal register", "A dead language"],
     "answer": "An individual's personal language variety"},

    {"tier": 5, "question": "Code-switching is the practice of alternating between two or more ___ in conversation?",
     "choices": ["Registers of one language", "Languages or dialects", "Sentence structures", "Writing systems"],
     "answer": "Languages or dialects"},

    {"tier": 5, "question": "A portmanteau word blends the sounds and meanings of ___ words?",
     "choices": ["Three or more", "Two", "Opposite", "Synonymous"],
     "answer": "Two"},

    {"tier": 5, "question": "The word 'brunch' is an example of a ___?",
     "choices": ["Compound word", "Portmanteau", "Clipping", "Blend only via suffixation"],
     "answer": "Portmanteau"},

    {"tier": 5, "question": "A back-formation creates a new word by ___ a suffix?",
     "choices": ["Adding", "Removing", "Doubling", "Replacing"],
     "answer": "Removing"},

    {"tier": 5, "question": "'Edit' was formed as a back-formation from ___?",
     "choices": ["Edition", "Editorial", "Editor", "Edited"],
     "answer": "Editor"},

    {"tier": 5, "question": "An eponym is a word derived from a ___?",
     "choices": ["Greek root", "Latin suffix", "Person's name", "Place name only"],
     "answer": "Person's name"},

]

def main():
    # Load existing data
    with open(GRAMMAR_PATH, "r", encoding="utf-8") as f:
        existing = json.load(f)

    existing_questions = {q["question"] for q in existing}

    # Check for duplicates in new batch
    dupes = []
    for q in NEW_QUESTIONS:
        if q["question"] in existing_questions:
            dupes.append(q["question"])
    if dupes:
        print(f"ERROR: {len(dupes)} duplicate(s) found in new questions:")
        for d in dupes:
            print(f"  {d!r}")
        sys.exit(1)

    # Validate answer is in choices
    errors = []
    for q in NEW_QUESTIONS:
        if q["answer"] not in q["choices"]:
            errors.append(f"Answer not in choices: {q['question']!r}")
        if len(q["choices"]) != 4:
            errors.append(f"Not exactly 4 choices: {q['question']!r}")
    if errors:
        print(f"ERROR: {len(errors)} validation error(s):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

    # Count new questions per tier
    from collections import Counter
    new_counts = Counter(q["tier"] for q in NEW_QUESTIONS)
    print("New questions per tier:", dict(sorted(new_counts.items())))

    # Combine
    combined = existing + NEW_QUESTIONS

    # Validate final counts
    final_counts = Counter(q["tier"] for q in combined)
    print("Final counts per tier:", dict(sorted(final_counts.items())))
    print("Total:", len(combined))

    ok = True
    for tier in [1, 2, 3, 4, 5]:
        count = final_counts.get(tier, 0)
        if count != 100:
            print(f"  WARNING: Tier {tier} has {count} questions (expected 100)")
            ok = False
        else:
            print(f"  Tier {tier}: {count} OK")

    # Validate all answers in choices
    val_errors = 0
    for q in combined:
        if q["answer"] not in q["choices"]:
            print(f"  ERROR answer not in choices: {q['question']!r}")
            val_errors += 1
    if val_errors:
        print(f"Total validation errors: {val_errors}")
        sys.exit(1)
    else:
        print("All answers validated in choices.")

    if not ok:
        print("Tier counts do not match expected 100 each. Aborting write.")
        sys.exit(1)

    # Write back
    with open(GRAMMAR_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print(f"\nSuccess! Wrote {len(combined)} questions to {GRAMMAR_PATH}")

if __name__ == "__main__":
    main()
