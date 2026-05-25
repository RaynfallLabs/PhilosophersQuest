"""Grammar bank exemplars — 35 hand-authored questions demonstrating the
voice rules from GRAMMAR_FRAMEWORK.md across all 5 tiers + 6 pillars.

Pillars (5 content pillars from docs/quiz/grammar_strategies.md +
1 voice-showcase pillar):

  1. Parts of speech + sentence structure
  2. Verb forms + tense + agreement
  3. Etymology + how English came to be
  4. Figurative language + word play
  5. Grammar history + usage rules + style
  6. Comma-Saves-Lives showcase — the controlling-voice exemplars

Each exemplar should:
  - Pass every gate in tools.quizgen.gates.grammar.PER_QUESTION_GATES
  - Pass every pipeline gate (length_budget, length_parity, etc.)
  - Land somewhere on the Comma-Saves-Lives hierarchy (§1 of framework)
  - Honor the vocab-teaching invariant at T1–T3
  - Stay under the per-tier total cap (600/700/750/950/1000)

Run validation: `py -m tools.quizgen.exemplars.grammar`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402


# ---------------------------------------------------------------------------
# PILLAR 1 — Parts of speech + sentence structure
# ---------------------------------------------------------------------------

P1_T1 = {
    "tier": 1,
    "question": "In 'The cat sat on the mat,' which word is a noun?",
    "answer": "cat",
    "choices": ["cat", "sat", "on", "the"],
    "context": "A noun names a person, place, thing, or idea. In this sentence, 'cat' is a thing — and 'mat' is too. ('Sat' is a verb; 'on' is a preposition; 'the' is an article.)",
}

P1_T2 = {
    "tier": 2,
    "question": "In 'She works for a hospital,' what part of speech is 'for'?",
    "answer": "Preposition",
    "choices": ["Preposition", "Noun", "Verb", "Adjective"],
    "context": "Prepositions show the relationship between a noun (or pronoun) and the rest of the sentence — typically location, direction, or time. Common ones include: in, on, at, by, for, under, over, between, through.",
}

P1_T3 = {
    "tier": 3,
    "question": "In 'When the rain stopped, we went outside,' which part is the dependent clause?",
    "answer": "When the rain stopped",
    "choices": [
        "When the rain stopped",
        "we went outside",
        "the rain stopped, we went",
        "When the rain",
    ],
    "context": "A dependent (or subordinate) clause cannot stand alone — it needs an independent clause to complete it. 'When' is a subordinating conjunction; 'When the rain stopped' has a subject ('the rain') and verb ('stopped') but doesn't express a complete thought on its own.",
}

P1_T4 = {
    "tier": 4,
    "question": "An appositive is a noun phrase that renames or further identifies another noun beside it. Restrictive appositives are essential to the meaning (no commas: 'my friend Sarah'); non-restrictive appositives add extra information (set off by commas). Which sentence correctly uses a non-restrictive appositive?",
    "answer": "Beethoven, the famous composer, became deaf later in life.",
    "choices": [
        "Beethoven, the famous composer, became deaf later in life.",
        "Beethoven the famous composer became deaf later in life.",
        "Beethoven, the famous composer became deaf later in life.",
        "Beethoven the famous composer, became deaf later in life.",
    ],
    "context": "Non-restrictive appositives are set off by commas on BOTH sides (or by em-dashes). Restrictive appositives ('my brother John' when you have multiple brothers) take NO commas because the identifier is essential to knowing which one. The classic test: if you can remove the appositive and the sentence still names the right person, it's non-restrictive.",
}

P1_T5 = {
    "tier": 5,
    "question": "In 'Running is good exercise,' what is the grammatical function of 'running'?",
    "answer": "Gerund — a verb form acting as a noun (subject of 'is')",
    "choices": [
        "Gerund — a verb form acting as a noun (subject of 'is')",
        "Present participle — a verb form acting as an adjective",
        "Infinitive — the base form of a verb",
        "Present-tense verb — the main action of the sentence",
    ],
    "context": "Gerunds and present participles look identical (both end in -ing) but function differently. The test: a gerund acts as a noun (subject, object, or complement); a present participle acts as an adjective ('the running water') or part of a continuous tense ('she is running'). Here, 'Running' is the subject of 'is' — a noun-role — so it's a gerund.",
}


# ---------------------------------------------------------------------------
# PILLAR 2 — Verb forms + tense + agreement
# ---------------------------------------------------------------------------

P2_T1 = {
    "tier": 1,
    "question": "Which sentence has the verb in the past tense?",
    "answer": "Yesterday I walked to school.",
    "choices": [
        "Yesterday I walked to school.",
        "Tomorrow I will walk to school.",
        "Today I am walking to school.",
        "Every day I walk to school.",
    ],
    "context": "Past tense names actions that already happened. Most English verbs add -ed for past tense (walk → walked). Some are irregular: go → went, see → saw, eat → ate, run → ran.",
}

P2_T2 = {
    "tier": 2,
    "question": "Pick the verb that agrees with the subject: 'The team ___ celebrating its win.'",
    "answer": "is",
    "choices": ["is", "are", "be", "were"],
    "context": "In American English, collective nouns like 'team', 'family', 'audience', 'jury' usually take SINGULAR verbs ('The team is celebrating'). British English often uses the plural ('The team are celebrating') when emphasizing the individual members.",
}

P2_T3 = {
    "tier": 3,
    "question": "Pick the correct form: 'The book is ___ on the table.'",
    "answer": "lying",
    "choices": ["lying", "laying", "layed", "lain"],
    "context": "Lie / lay confuses everyone. 'Lie' (recline, intransitive — no object): lie / lay / lain — 'I lie down, I lay down yesterday, I have lain there for hours.' 'Lay' (place, transitive — takes an object): lay / laid / laid — 'I lay the book down, I laid it down yesterday, I have laid it down many times.' A book LIES on a table because nobody is placing it as you speak.",
}

P2_T4 = {
    "tier": 4,
    "question": "The subjunctive mood expresses counterfactual or hypothetical situations. Which sentence uses the subjunctive correctly?",
    "answer": "If I were rich, I'd travel the world.",
    "choices": [
        "If I were rich, I'd travel the world.",
        "If I was rich, I'd travel the world.",
        "If I am rich, I'd travel the world.",
        "If I will be rich, I'd travel the world.",
    ],
    "context": "The English subjunctive is fading but persists in counterfactuals (contrary-to-fact 'if' clauses) and certain formal idioms ('Long live the king,' 'Be that as it may,' 'God save the queen'). 'If I were' is subjunctive (he/she/it normally takes 'was', but the subjunctive uses 'were' for all persons). 'If I was' is increasingly accepted in informal usage but the subjunctive 'were' remains standard in careful writing.",
}

P2_T5 = {
    "tier": 5,
    "question": "Identify the type of conditional: 'If I had studied harder, I would have passed.'",
    "answer": "Third (past counterfactual — unreal past condition with unreal past result)",
    "choices": [
        "Third (past counterfactual — unreal past condition with unreal past result)",
        "Second (present counterfactual — unreal present condition)",
        "First (real future possibility — likely outcome)",
        "Zero (general truth — always-true relationships)",
    ],
    "context": "English conditionals: Zero (general truth, 'If water reaches 100°C, it boils'); First (real future, 'If it rains, I'll stay home'); Second (present unreal, 'If I were rich, I'd travel'); Third (past unreal, 'If I had studied, I would have passed'). Mixed conditionals splice tenses between clauses. The Third conditional is purely counterfactual — both the condition AND the result are imagined alternatives to what actually happened.",
}


# ---------------------------------------------------------------------------
# PILLAR 3 — Etymology + how English came to be
# ---------------------------------------------------------------------------

P3_T1 = {
    "tier": 1,
    "question": "The word 'sandwich' is named after a person. What kind of person?",
    "answer": "An English earl (the 4th Earl of Sandwich)",
    "choices": [
        "An English earl (the 4th Earl of Sandwich)",
        "A French chef from Paris",
        "A baker from Italy",
        "A Roman general from long ago",
    ],
    "context": "John Montagu, the 4th Earl of Sandwich (1718-1792), reportedly asked his servants to bring him meat between slices of bread so he could keep gambling at the card table without dirtying his hands. The bread-and-meat order took his title as its name — and English has called it a 'sandwich' ever since.",
}

P3_T2 = {
    "tier": 2,
    "question": "Which language gave English the word 'pajamas'?",
    "answer": "Hindi-Urdu (from Persian roots)",
    "choices": [
        "Hindi-Urdu (from Persian roots)",
        "French (from Latin roots)",
        "German (from Old Saxon roots)",
        "Greek (from ancient Hellenic roots)",
    ],
    "context": "British soldiers and officials in colonial India encountered 'pāy-jāma' — Persian-rooted Hindi-Urdu for 'leg-garment.' They borrowed the loose drawstring trousers AND the word, and 'pyjamas' (British spelling) entered English in the 1800s. English picked up many words this way: shampoo, bungalow, jungle, loot, thug, guru, bandana — all from Hindi-Urdu.",
}

P3_T3 = {
    "tier": 3,
    "question": "After 1066, French became the language of English nobility while English-speaking farmers kept their Old English words. This is why we have separate words for the animal versus the meat: 'pig' (Anglo-Saxon, what farmers raised) vs 'pork' (French, what nobles ate). Which other pair shows this pattern?",
    "answer": "cow vs beef",
    "choices": [
        "cow vs beef",
        "horse vs stallion",
        "dog vs puppy",
        "chicken vs hen",
    ],
    "context": "The Norman Conquest of 1066 brought French-speaking nobility to England. For about 300 years, the upper class spoke French while commoners spoke English. This gave English the cow/beef, pig/pork, sheep/mutton, calf/veal, deer/venison split — the animal name from the field (English) and the meat name from the table (French). English roughly doubled its vocabulary during this period.",
}

P3_T4 = {
    "tier": 4,
    "question": "The word 'sincere' is sometimes claimed to come from the Latin 'sine cera' meaning 'without wax' — supposedly from sculptors hiding cracks in marble with wax. The true Latin origin is 'sincerus' meaning 'clean, pure, sound.' Which of these other popular word-origin stories is ALSO a false folk etymology?",
    "answer": "'Rule of thumb' came from a law allowing a husband to beat his wife with a stick no thicker than his thumb.",
    "choices": [
        "'Rule of thumb' came from a law allowing a husband to beat his wife with a stick no thicker than his thumb.",
        "'Chocolate' comes from Nahuatl 'xocolātl,' meaning bitter water.",
        "'Algebra' comes from Arabic 'al-jabr,' meaning the reunion of broken parts.",
        "'Coffee' comes from Arabic 'qahwa,' which originally also meant wine.",
    ],
    "context": "The 'rule of thumb' wife-beating origin is a popular but false story circulated since the 1970s — no such law ever existed in English common law. The phrase actually comes from rough-measurement tradition (carpenters, brewers, gardeners using the thumb as a quick gauge). The other three etymologies are accurate. Always check word origins — folk etymologies multiply faster than truth.",
}

P3_T5 = {
    "tier": 5,
    "question": "The Great Vowel Shift was a dramatic change in English pronunciation between roughly 1400 and 1700 — long vowels moved upward in the mouth or became diphthongs. Why does modern English spelling rarely match its pronunciation?",
    "answer": "Spelling stabilized via the 1476 printing press — then the Great Vowel Shift kept changing the sounds.",
    "choices": [
        "Spelling stabilized via the 1476 printing press — then the Great Vowel Shift kept changing the sounds.",
        "Spelling was never standardized in English — every careful speaker still spells phonetically today.",
        "The Norman Conquest of 1066 froze French spellings — they passed into English permanently then.",
        "Modern English deliberately preserves Old English spellings — purely as a cultural choice now.",
    ],
    "context": "William Caxton's introduction of the printing press to England in 1476 began standardizing spelling — but he chose London-dialect forms just BEFORE the Great Vowel Shift completed (~1700). The shift moved long vowels: Middle English 'time' (rhymed with modern 'team') became modern 'time' (rhymes with 'rhyme'). The printers kept the spelling 'time'; the speakers changed the sound. This is why English has 'name' and 'face' (long 'a' = /eɪ/) but 'cat' and 'hat' (short 'a' = /æ/) — the long-a vowels shifted; the short ones didn't.",
}


# ---------------------------------------------------------------------------
# PILLAR 3b — Etymology: word-meaning shifts + root families
# (the punchline angle of etymology — "wait, X used to mean Y?")
# ---------------------------------------------------------------------------

P3b_T1 = {
    "tier": 1,
    "question": "Long ago, the word 'awful' meant something good — full of AWE, like a beautiful sunset. Today, 'awful' means terrible. Many English words have shifted meaning over centuries. The word 'nice' is one of them. What did 'nice' originally mean in Middle English?",
    "answer": "Foolish or silly",
    "choices": [
        "Foolish or silly",
        "Polite and kind",
        "Beautiful or pretty",
        "Friendly and warm",
    ],
    "context": "'Nice' comes from Latin 'nescius' meaning 'ignorant' (literally 'not-knowing'). In Middle English (1200s-1400s), 'nice' meant foolish, simple-minded, or silly. By the 1500s the meaning shifted to 'careful' or 'precise' (as in 'a nice distinction'). By the 1800s it landed on its modern meaning: pleasant, kind, agreeable. The meaning has migrated upward across centuries — from insult to compliment. Many English words have done this: 'awful' (awe-inspiring → terrible), 'silly' (blessed → foolish), 'terrific' (terrifying → wonderful).",
}

P3b_T2 = {
    "tier": 2,
    "question": "Some English words have flipped meaning to the OPPOSITE of where they started. Which of these word-shifts is REAL?",
    "answer": "'Silly' originally meant blessed or innocent — from Old English 'sælig.'",
    "choices": [
        "'Silly' originally meant blessed or innocent — from Old English 'sælig.'",
        "'Cat' originally meant a clever person — from Old Norse 'katr' meaning wise.",
        "'Apple' originally meant any vegetable — from Old English 'æppel' meaning plant.",
        "'Run' originally meant to walk slowly — from Old English 'rinnan' meaning stroll.",
    ],
    "context": "Word-meaning shifts can flip a word's sense to its opposite over centuries. 'Silly' is the classic example — from Old English 'sælig' meaning blessed, holy, or innocent, it slid through 'helpless' and 'foolish' to land at its modern 'foolish, ridiculous.' The other claims are invented. Real flips include: 'awful' (awe-inspiring → terrible), 'terrific' (causing terror → wonderful), 'nice' (foolish → pleasant), 'fond' (foolish → loving), and the most extreme — 'literally' shifted to mean its own opposite ('figuratively'), enraging usage purists since the 1700s.",
}

P3b_T3 = {
    "tier": 3,
    "question": "The Latin word 'manus' means 'hand.' English has built a whole word-family from this root. Which of these English words does NOT come from Latin 'manus'?",
    "answer": "Magnify (which comes from Latin 'magnus' meaning great)",
    "choices": [
        "Magnify (which comes from Latin 'magnus' meaning great)",
        "Manuscript (literally: 'written by hand')",
        "Manipulate (originally: 'to handle skillfully')",
        "Manicure (literally: 'care of the hands')",
    ],
    "context": "Latin 'manus' (hand) is one of the most productive English word-roots. From it: MANUAL (done by hand), MANUSCRIPT ('written by hand' — manu + scriptus), MANIPULATE ('to handle skillfully'), MANICURE (manu + cure, 'care of hands'), MANUFACTURE (manu + factura, 'made by hand'), MANDATE ('given into the hand'), EMANCIPATE ('out of the hand of' — a master), MAINTAIN ('to hold in the hand'), and more. 'Magnify' is unrelated — it comes from Latin 'magnus' (great, large), the same root as MAGNATE, MAGNITUDE, MAGNIFICENT, and MAGNUM. Learning Latin roots multiplies your English vocabulary geometrically.",
}

P3b_T4 = {
    "tier": 4,
    "question": "The word 'decimate' originally had a very specific meaning in ancient Rome. A Roman general would discipline a mutinous legion by selecting soldiers by lot and executing them. In modern English, 'decimate' means to devastate broadly. What was the ORIGINAL Roman ratio?",
    "answer": "Kill exactly 1 in 10 (the others would carry out the execution by club or stone).",
    "choices": [
        "Kill exactly 1 in 10 (the others would carry out the execution by club or stone).",
        "Kill exactly 1 in 5 (the standard discipline rate for a defeated unit's officers).",
        "Kill exactly 1 in 100 (a rare and symbolic punishment reserved for treason).",
        "Kill exactly half of all surviving troops (a brutal but rare Roman penalty).",
    ],
    "context": "'Decimate' comes from Latin 'decimus' (tenth) — the Roman military punishment killed exactly 1 in 10 soldiers, chosen by lot, with the remaining 9 conscripted to carry out the executions (by club, stone, or sword). It was rare and reserved for grave offenses like cowardice or mutiny. The most famous historical instance: Marcus Licinius Crassus decimated his troops after their defeat by Spartacus's army (71 BC). Modern English has widened the meaning to 'destroy a large portion' — usage purists object, but the broader sense is now standard. The shift from 'exactly 10%' to 'a large amount' demonstrates how a precise technical term softens into a vague intensifier over centuries.",
}

P3b_T5 = {
    "tier": 5,
    "question": "The English past tense of 'go' is 'went' — not 'goed' or any regular form. Linguists call this 'suppletion': two unrelated verbs got grafted into a single paradigm. From which Old English verb did 'went' come?",
    "answer": "'Wend' (Old English 'wendan,' meaning to turn or wind one's way) — which still survives in 'wend my way.'",
    "choices": [
        "'Wend' (Old English 'wendan,' meaning to turn or wind one's way) — which still survives in 'wend my way.'",
        "'Wander' (Old English 'wandrian,' meaning to roam) — which donated its past tense to 'go' around 1100 AD.",
        "'Wear' (Old English 'werian,' meaning to walk worn paths) — through metaphorical extension to mean travel.",
        "'Win' (Old English 'winnan,' meaning to strive or labor) — its past 'wann' was reanalyzed as motion.",
    ],
    "context": "English 'went' is the past tense of 'wend' — a separate verb meaning 'to turn, to direct one's course' (compare modern 'wend my way home'). Around 1200-1500, English speakers stopped saying 'goed' or 'eode' (the actual Old English past of 'go') and grafted 'went' onto 'go' instead. 'Wend' kept the form 'wended' for itself. This is SUPPLETION — when two unrelated verbs share a paradigm. The most extreme case is the verb 'be': am / is / are / was / were / been / being come from THREE Proto-Indo-European roots (*es-, *bheue-, *wes-). English's most-used verbs are its most-irregular, because the patterns wore smooth before standardization caught them.",
}


# ---------------------------------------------------------------------------
# PILLAR 4 — Figurative language + word play
# ---------------------------------------------------------------------------

P4_T1 = {
    "tier": 1,
    "question": "Which sentence uses a simile (a comparison using 'like' or 'as')?",
    "answer": "Her smile was as bright as the sun.",
    "choices": [
        "Her smile was as bright as the sun.",
        "Her smile lit up the room.",
        "She smiled when she saw him.",
        "The sun was shining brightly.",
    ],
    "context": "A simile compares two unlike things using 'like' or 'as' ('cool as a cucumber,' 'fits like a glove'). A metaphor compares directly without 'like' or 'as' ('Life is a journey,' 'Her smile lit up the room' — her smile didn't literally produce photons). The first choice uses 'as bright as' — that's a simile.",
}

P4_T2 = {
    "tier": 2,
    "question": "What kind of word play is in this sentence: 'Time flies like an arrow; fruit flies like a banana'?",
    "answer": "A pun ('flies' re-reads as a noun in the second clause)",
    "choices": [
        "A pun ('flies' re-reads as a noun in the second clause)",
        "Alliteration (repeated sounds at the starts of words)",
        "Hyperbole (deliberate exaggeration for emphasis)",
        "Metaphor (direct comparison without 'like' or 'as')",
    ],
    "context": "A pun (also called paronomasia) exploits a word with two meanings or two words that sound alike. Groucho Marx's famous joke works because the first clause sets up 'flies' as a verb ('Time moves quickly, like an arrow'), then the second clause forces you to re-read 'flies' as a noun ('Fruit flies, the insect, are fond of bananas'). The double-take IS the joke.",
}

P4_T3 = {
    "tier": 3,
    "question": "Which sentence contains a dangling modifier (the opening phrase doesn't logically attach to the subject that follows)?",
    "answer": "Walking down the street, the trees were beautiful.",
    "choices": [
        "Walking down the street, the trees were beautiful.",
        "Walking down the street, I noticed the beautiful trees.",
        "The trees, beautiful in the autumn light, lined the street.",
        "I walked down the street, admiring the beautiful trees.",
    ],
    "context": "A dangling modifier is an opening phrase (usually -ing or -ed) that should describe the subject of the main clause — but doesn't, because the wrong subject follows. 'Walking down the street, the trees were beautiful' literally claims the trees were walking. The fix: change the subject so it matches what's walking ('Walking down the street, I noticed...') OR rewrite the opener entirely.",
}

P4_T4 = {
    "tier": 4,
    "question": "'I came, I saw, I conquered.' Caesar's famous Latin phrase ('Veni, vidi, vici') uses which rhetorical figure — three clauses of similar length without conjunctions?",
    "answer": "Asyndeton (omitting conjunctions for compact force)",
    "choices": [
        "Asyndeton (omitting conjunctions for compact force)",
        "Polysyndeton (using many conjunctions for rhythm)",
        "Anaphora (repeating opening words across clauses)",
        "Hyperbole (extreme exaggeration for effect)",
    ],
    "context": "Asyndeton omits conjunctions where you'd expect them ('and,' 'or') to produce punch and rapidity — Caesar's 'I came, I saw, I conquered' (no 'and'); Lincoln's 'we cannot dedicate, we cannot consecrate, we cannot hallow this ground.' The opposite figure, polysyndeton, piles ON conjunctions for rhythm and weight ('And the rain descended, and the floods came, and the winds blew' — Matthew 7:25).",
}

P4_T5 = {
    "tier": 5,
    "question": "Identify the rhetorical figure in: 'Ask not what your country can do for you — ask what you can do for your country.'",
    "answer": "Chiasmus (mirror-image inversion: A-B / B-A)",
    "choices": [
        "Chiasmus (mirror-image inversion: A-B / B-A)",
        "Anaphora (repetition at the start of successive clauses)",
        "Epistrophe (repetition at the end of successive clauses)",
        "Antithesis (contrast within a parallel structure)",
    ],
    "context": "Chiasmus reverses the order of paired elements between two clauses: A (country / you) — B (you / country) — B (you / country) — A. Kennedy's 1961 inaugural line is the most famous American example. The figure dates to Greek rhetoric (the name comes from the Greek letter χ 'chi,' shaped like an X, mapping the crossover). Related but distinct: antithesis sets up contrast in parallel form ('It was the best of times, it was the worst of times'); chiasmus inverts the elements.",
}


# ---------------------------------------------------------------------------
# PILLAR 5 — Grammar history + usage rules + style
# ---------------------------------------------------------------------------

P5_T1 = {
    "tier": 1,
    "question": "Which is correct?",
    "answer": "I'd like an apple, please.",
    "choices": [
        "I'd like an apple, please.",
        "I'd like a apple, please.",
        "I'd like an pear, please.",
        "I'd like a egg, please.",
    ],
    "context": "Use 'a' before a CONSONANT sound and 'an' before a VOWEL sound. 'Apple' starts with /æ/ (vowel sound) → 'an apple.' 'Pear' starts with /p/ (consonant) → 'a pear.' 'Egg' starts with /ɛ/ (vowel) → 'an egg.' The rule cares about sounds, not letters — 'an hour' (silent h, vowel sound) but 'a hospital' (sounded h, consonant).",
}

P5_T2 = {
    "tier": 2,
    "question": "Which is correct: 'less than ten people' or 'fewer than ten people'?",
    "answer": "'Fewer than ten people' — fewer for countable, less for non-countable",
    "choices": [
        "'Fewer than ten people' — fewer for countable, less for non-countable",
        "'Less than ten people' — less is correct for any quantity at all",
        "Both equally correct — fully interchangeable in any usage today",
        "'Less than ten people' — fewer is archaic and not used anymore",
    ],
    "context": "Use 'fewer' for things you can count (fewer apples, fewer cars, fewer people). Use 'less' for things you can't count (less water, less time, less sugar). Modern usage increasingly blurs the rule in casual speech ('10 items or less' at the grocery store), but careful writing keeps the distinction. The rule comes from Robert Baker's 1770 grammar — older than that, the words were often interchangeable.",
}

P5_T3 = {
    "tier": 3,
    "question": "'Whom did you see?' — Why 'whom' and not 'who'?",
    "answer": "Because 'whom' is the OBJECT of 'see' — 'you' is the subject, 'whom' the object.",
    "choices": [
        "Because 'whom' is the OBJECT of 'see' — 'you' is the subject, 'whom' the object.",
        "Because 'whom' is more formal-sounding — preferred in formal written English always.",
        "Because 'who' is becoming obsolete — 'whom' is the modern standard form everywhere.",
        "Because the question starts with 'whom' — every sentence-initial form uses 'whom'.",
    ],
    "context": "Use 'who' for the subject (the doer) and 'whom' for the object (the receiver). Quick test: substitute 'he/she' (subject) or 'him/her' (object) — if 'him/her' fits, use 'whom.' 'Whom did you see?' → 'You saw him' (object). 'Who saw you?' → 'He saw you' (subject). The whom/who distinction is fading in conversational English but holds in formal writing.",
}

P5_T4 = {
    "tier": 4,
    "question": "Bishop Robert Lowth's 'Short Introduction to English Grammar' (1762) imported a Latin rule into English: don't split an infinitive (don't put a word between 'to' and the verb). Latin infinitives are single words (amare = 'to love'), so they CAN'T be split. English infinitives are two words and CAN be. Which famous phrase deliberately violates Lowth's rule?",
    "answer": "Star Trek's 'to boldly go where no man has gone before'",
    "choices": [
        "Star Trek's 'to boldly go where no man has gone before'",
        "Shakespeare's 'to be or not to be, that is the question'",
        "Lincoln's 'of the people, by the people, for the people'",
        "Kennedy's 'ask not what your country can do for you'",
    ],
    "context": "Splitting an infinitive — putting 'boldly' between 'to' and 'go' — was branded improper by Lowth in 1762 and his successors. Star Trek's opening narration cheerfully ignored the rule and made it a cultural marker. Modern style guides (Garner, Chicago, even AP) accept the split when it reads naturally; Strunk & White grudgingly allow it. Most other 'rules' Lowth invented — no preposition at the end of a sentence, no double negative — share the same Latin-grafted-onto-English origin and have similarly relaxed.",
}

P5_T5 = {
    "tier": 5,
    "question": "Two famous English style guides disagree about the Oxford comma. The Associated Press Stylebook (journalism) drops it; the Chicago Manual of Style and Strunk & White keep it. Which sentence demonstrates the Chicago position — that the Oxford comma can prevent ambiguity?",
    "answer": "'I invited the strippers, JFK, and Stalin.' (Oxford comma — three separate guests at the dinner)",
    "choices": [
        "'I invited the strippers, JFK, and Stalin.' (Oxford comma — three separate guests at the dinner)",
        "'I invited the strippers and JFK and Stalin.' (no commas — polysyndeton style for rhythm)",
        "'I invited the strippers; JFK; and Stalin.' (semicolons — overformal but unambiguous)",
        "'I invited the strippers, JFK and Stalin.' (no Oxford comma — JFK and Stalin become the strippers)",
    ],
    "context": "Without the Oxford comma, 'I invited the strippers, JFK and Stalin' can be read as 'I invited the strippers — namely JFK and Stalin.' The Oxford comma (so named because the Oxford University Press style requires it) resolves the ambiguity. AP style omits it for space efficiency in newspaper columns; Chicago, MLA, and most book publishers keep it. The Oxford-comma debate is the most famous style-guide disagreement in English — both sides have legitimate cases.",
}


# ---------------------------------------------------------------------------
# PILLAR 6 — Comma-Saves-Lives showcase (the controlling voice)
# ---------------------------------------------------------------------------

P6_T1 = {
    "tier": 1,
    "question": "Which sentence means we are INVITING Grandma to dinner (not eating her)?",
    "answer": "Let's eat, Grandma!",
    "choices": [
        "Let's eat, Grandma!",
        "Let's eat Grandma!",
        "Lets eat Grandma!",
        "Let's eat grandma",
    ],
    "context": "Punctuation can change meaning entirely. 'Let's eat, Grandma!' uses a vocative comma — you're TALKING TO Grandma, inviting her to eat. 'Let's eat Grandma!' has no comma — you're proposing to eat Grandma. The little curve saves a relative. Commas can save lives.",
}

P6_T2 = {
    "tier": 2,
    "question": "Which sentence is correct: the apostrophe in 'it's' vs 'its'?",
    "answer": "The dog wagged its tail because it's happy.",
    "choices": [
        "The dog wagged its tail because it's happy.",
        "The dog wagged it's tail because its happy.",
        "The dog wagged its' tail because it's happy.",
        "The dog wagged it's tail because its' happy.",
    ],
    "context": "'Its' = possessive (belongs to it) — like 'his' or 'her,' no apostrophe. 'It's' = contraction of 'it is' (or 'it has') — the apostrophe stands in for the missing letter. The trick: if you can substitute 'it is,' use the apostrophe. 'The dog wagged it is tail' makes no sense, so → 'its.' 'It is happy' makes sense, so → 'it's.' The same trap waits in your/you're, their/there/they're, whose/who's.",
}

P6_T3 = {
    "tier": 3,
    "question": "Lynne Truss's book 'Eats, Shoots and Leaves' (2003) takes its title from a panda joke. A wildlife manual says a panda 'eats shoots and leaves' — bamboo shoots and bamboo leaves. What does adding a comma after 'eats' do to the panda?",
    "answer": "Turns it into an outlaw — eats, then shoots (fires a gun), then leaves the scene.",
    "choices": [
        "Turns it into an outlaw — eats, then shoots (fires a gun), then leaves the scene.",
        "Turns it into a vegetarian — the comma emphasizes the panda's bamboo-only diet.",
        "Turns it into an athlete — 'shoots' becomes basketball; 'leaves' means departure.",
        "Turns it into a poet — the comma creates a contemplative list of three actions.",
    ],
    "context": "Lynne Truss's bestseller 'Eats, Shoots and Leaves' (2003) made the case for better punctuation through this panda joke: a misprinted wildlife manual reads 'Eats, shoots and leaves' as a panda's description. Without the comma after 'eats,' the phrase reads as a diet description: the panda eats (bamboo) shoots and (bamboo) leaves. WITH the comma: three sequential verbs — the panda eats, then shoots (a gun), then leaves the scene. Same words; one comma turns a vegetarian bear into a hit-man.",
}

P6_T4 = {
    "tier": 4,
    "question": "A misplaced modifier is a word or phrase placed so it modifies the wrong word, creating absurd or unintended meaning. Which sentence demonstrates a misplaced modifier (note where 'with the telescope' attaches)?",
    "answer": "I saw the boy with the telescope.",
    "choices": [
        "I saw the boy with the telescope.",
        "Using the telescope, I saw the boy.",
        "I saw the boy who had a telescope.",
        "The telescope let me see the boy.",
    ],
    "context": "'I saw the boy with the telescope' is famously ambiguous: it can mean (a) I used the telescope to see the boy, OR (b) I saw the boy who had a telescope. The modifier 'with the telescope' should attach to 'saw' (case a) or to 'the boy' (case b) — and the sentence doesn't tell you which. The fix: put the modifier where it can only mean one thing. 'Using the telescope, I saw the boy' (case a only); 'I saw the boy who had a telescope' (case b only).",
}

P6_T5 = {
    "tier": 5,
    "question": "An eight-word sentence: 'Most of the time travelers worry about their luggage.' A single comma changes this into two very different sentences. Which two interpretations does the punctuation produce?",
    "answer": "WITH comma after 'time': 'Most of the time, travelers worry about their luggage.' (frequency — usually travelers worry). WITHOUT comma: 'Most of the time travelers worry...' (subject — most of these time-travelers are worriers).",
    "choices": [
        "WITH comma after 'time': 'Most of the time, travelers worry about their luggage.' (frequency — usually travelers worry). WITHOUT comma: 'Most of the time travelers worry...' (subject — most of these time-travelers are worriers).",
        "WITH comma: describes science-fiction characters worrying — they roam through history. WITHOUT comma: describes airport workers worrying — about ordinary baggage.",
        "WITH comma: an imperative command directing travelers to worry now — instructional. WITHOUT comma: a declarative statement about their habits — descriptive.",
        "Both readings are identical — 'time' modifies 'travelers' regardless of comma. The comma is purely stylistic — it does not affect meaning at all.",
    ],
    "context": "This sentence demonstrates how a single comma can change phrase-grouping and therefore meaning. WITH the comma after 'time': 'Most of the time' is a prepositional adverb phrase (frequency); 'travelers' is the subject; the sentence says travelers usually worry about luggage. WITHOUT the comma: 'time travelers' becomes a compound noun (the science-fiction characters); the sentence says most of these time-travelers worry. The comma controls whether 'time' is a noun-in-a-prepositional-phrase or a modifier-of-travelers. Same eight words, two opposite subjects, all hanging on one punctuation mark.",
}


# ---------------------------------------------------------------------------
# Assemble all exemplars + validate
# ---------------------------------------------------------------------------

EXEMPLARS = [
    ("P1_T1", P1_T1), ("P1_T2", P1_T2), ("P1_T3", P1_T3), ("P1_T4", P1_T4), ("P1_T5", P1_T5),
    ("P2_T1", P2_T1), ("P2_T2", P2_T2), ("P2_T3", P2_T3), ("P2_T4", P2_T4), ("P2_T5", P2_T5),
    # Etymology: famous-word origins + linguistic history (P3) + meaning-shifts + roots (P3b)
    ("P3_T1", P3_T1), ("P3_T2", P3_T2), ("P3_T3", P3_T3), ("P3_T4", P3_T4), ("P3_T5", P3_T5),
    ("P3b_T1", P3b_T1), ("P3b_T2", P3b_T2), ("P3b_T3", P3b_T3), ("P3b_T4", P3b_T4), ("P3b_T5", P3b_T5),
    ("P4_T1", P4_T1), ("P4_T2", P4_T2), ("P4_T3", P4_T3), ("P4_T4", P4_T4), ("P4_T5", P4_T5),
    ("P5_T1", P5_T1), ("P5_T2", P5_T2), ("P5_T3", P5_T3), ("P5_T4", P5_T4), ("P5_T5", P5_T5),
    ("P6_T1", P6_T1), ("P6_T2", P6_T2), ("P6_T3", P6_T3), ("P6_T4", P6_T4), ("P6_T5", P6_T5),
]


def validate_all() -> int:
    """Run every gate against every exemplar. Returns # of fails."""
    questions = [q for _, q in EXEMPLARS]
    dup, ans = build_bank_indices(questions)
    fail_count = 0
    for (name, q), idx in zip(EXEMPLARS, range(len(questions))):
        r = validate_rewrite(
            "grammar", q, bank=questions, dup_index=dup, answer_index=ans,
            replace_idx=idx,
        )
        total = len(q["question"]) + sum(len(c) for c in q["choices"])
        if r["verdict"] == "FAIL":
            fail_count += 1
            print(f"  FAIL {name} (T{q['tier']}, total={total}c):")
            for g, reason in r["hard_fails"]:
                print(f"    {g}: {reason[:140]}")
        elif r["verdict"] == "SOFT_WARN":
            print(f"  SOFT {name} (T{q['tier']}, total={total}c):")
            for g, reason in r["soft_warns"]:
                print(f"    {g}: {reason[:140]}")
        else:
            print(f"  PASS {name} (T{q['tier']}, total={total}c)")
    return fail_count


if __name__ == "__main__":
    fails = validate_all()
    print()
    print(f"Total: {len(EXEMPLARS)} exemplars, {fails} failures")
    sys.exit(0 if fails == 0 else 1)
