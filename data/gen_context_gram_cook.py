#!/usr/bin/env python3
"""
Generate educational context for grammar and cooking quiz questions.
Each context is shown when the player answers incorrectly, teaching WHY the answer is correct.
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────
# GRAMMAR CONTEXTS
# ─────────────────────────────────────────────
GRAMMAR_CONTEXTS = {
    # === TIER 1 ===
    "A word that names a person, place, or thing is a ___?":
        "Nouns are the building blocks of every sentence -- they name the who, what, and where. Without nouns, you'd have nothing to talk about.",

    "Which word below is a personal pronoun?":
        "'She' stands in for a specific person's name, making it a personal pronoun. Verbs (run), adjectives (tall), and adverbs (quickly) do very different jobs.",

    "Which punctuation ends a question?":
        "The question mark has been ending questions since the 1500s. Some scholars think its shape evolved from the Latin word 'quaestio' (question) abbreviated to 'Qo' stacked vertically.",

    "Which punctuation ends a statement?":
        "The period (or full stop) signals a complete thought has ended. It's the smallest punctuation mark but does the biggest job -- ending sentences since ancient Rome.",

    "Which punctuation ends an exclamation?":
        "The exclamation point adds urgency or strong emotion to a sentence. Overusing it weakens its punch -- F. Scott Fitzgerald said using one is like laughing at your own joke.",

    "Which punctuation separates items in a list?":
        "Commas keep list items from crashing into each other. Without them, 'I love cooking my family and my pets' becomes a horror story instead of a heartwarming list.",

    "A word that replaces a noun is a ___?":
        "Pronouns like 'he,' 'she,' and 'they' are noun stand-ins that prevent tedious repetition. Without them, you'd say 'Bob told Bob that Bob's car was in Bob's driveway.'",

    "A word that shows action or state of being is a ___?":
        "Verbs are the engines of sentences -- they make things happen. Even 'is' and 'was' count as verbs because they express a state of being.",

    "A word that modifies a noun is a ___?":
        "Adjectives answer questions like 'which one?' 'how many?' and 'what kind?' They turn 'the dog' into 'the enormous, fluffy, golden dog.'",

    "A word that modifies a verb, adjective, or another adverb is a ___?":
        "Adverbs are the Swiss Army knives of grammar -- they modify verbs ('ran quickly'), adjectives ('very tall'), and even other adverbs ('extremely slowly'). Many end in '-ly,' which makes them easy to spot.",

    "A word that shows the relationship between a noun and another word is a ___?":
        "Prepositions like 'in,' 'on,' 'under,' and 'between' show spatial, temporal, or logical relationships. They're the GPS of grammar, telling you where things are in relation to each other.",

    "A word that joins words, phrases, or clauses is a ___?":
        "Conjunctions are the bridges of language. The coordinating ones (and, but, or) are easy to remember with the mnemonic FANBOYS: For, And, Nor, But, Or, Yet, So.",

    "An exclamation expressing emotion is a ___?":
        "Interjections like 'Wow!' 'Ouch!' and 'Hey!' burst into sentences uninvited. They're grammatically independent -- you can remove them without breaking the sentence.",

    "'Paris' is a ___ noun?":
        "Proper nouns name specific people, places, or things and always get capitalized. 'Paris' names one particular city, not just any city.",

    "'City' is a ___ noun?":
        "Common nouns name general categories rather than specific things. 'City' could be any city in the world, which is why it doesn't get a capital letter.",

    "The part of a sentence that tells who or what the sentence is about is the ___?":
        "The subject is the star of the sentence -- everything revolves around it. To find it, ask 'Who or what is doing (or being) something?'",

    "The part of a sentence that tells what the subject does is the ___?":
        "The predicate contains the verb and everything that follows it. If the subject is the actor, the predicate is the entire performance.",

    "The plural of 'child' is ___?":
        "'Children' is one of English's surviving Old English plurals, where '-ren' was a double plural suffix. It's the same pattern that gave us 'brethren' from 'brother.'",

    "The plural of 'mouse' is ___?":
        "'Mice' follows an ancient Germanic pattern called i-mutation, where a vowel in the root changed to signal plural. The same pattern gives us goose/geese and tooth/teeth.",

    "The plural of 'foot' is ___?":
        "'Feet' is another i-mutation plural inherited from Old English. The 'oo' sound shifted to 'ee' -- the same pattern as tooth/teeth and goose/geese.",

    "The plural of 'tooth' is ___?":
        "'Teeth' follows the same ancient vowel-shift pattern as foot/feet and goose/geese. These irregular plurals are survivors from Old English that resisted the regular '-s' ending.",

    "'He' is a ___ pronoun?":
        "Personal pronouns refer to specific people or things: I, you, he, she, it, we, they. They change form based on case -- 'he' (subject) becomes 'him' (object) and 'his' (possessive).",

    "A sentence that asks a question is ___?":
        "Interrogative sentences seek information and end with a question mark. The word 'interrogative' comes from Latin 'interrogare' meaning 'to ask.'",

    "A sentence that makes a statement is ___?":
        "Declarative sentences declare facts or opinions and end with a period. They're the most common sentence type -- you're reading several right now.",

    "A sentence that gives a command is ___?":
        "Imperative sentences give orders or make requests. Their subject ('you') is usually invisible: 'Close the door' really means 'You close the door.'",

    "A sentence that expresses strong emotion is ___?":
        "Exclamatory sentences pack an emotional punch and end with an exclamation point. They can express surprise, joy, anger, or any intense feeling.",

    "'Freedom' is a ___ noun?":
        "Abstract nouns name things you can't detect with your five senses -- ideas, qualities, and states like freedom, courage, and happiness. They exist only in the mind.",

    "'Flock' (of birds) is a ___ noun?":
        "Collective nouns name groups acting as a single unit. English has wonderfully specific ones: a murder of crows, a parliament of owls, an exaltation of larks.",

    "In the sentence 'The dog barked,' 'the dog' is the ___?":
        "The subject performs the action of the verb. Ask 'Who barked?' and the answer -- 'the dog' -- reveals the subject.",

    "In 'The dog barked,' 'barked' is the ___?":
        "The predicate tells what the subject does or is. Here, 'barked' is both the verb and the complete predicate, telling us the dog's action.",

    "Which word is a pronoun? ":
        "'They' replaces a noun (like 'the students'), making it a pronoun. 'Run' is a verb, 'blue' is an adjective, and 'slowly' is an adverb.",

    "Which word is a conjunction?":
        "'But' joins contrasting ideas, making it a conjunction. Remember FANBOYS: For, And, Nor, But, Or, Yet, So -- the seven coordinating conjunctions.",

    "Which word is a preposition?":
        "'Under' shows a spatial relationship between things, which is exactly what prepositions do. Think of prepositions as showing the position of something in relation to something else.",

    "Which word is an interjection?":
        "'Ouch!' expresses a sudden burst of emotion (pain), making it an interjection. Interjections stand grammatically alone and are often followed by exclamation points.",

    "Which word is an adjective?":
        "'Red' describes a quality of a noun (a red ball, the red car), making it an adjective. If it can fit in 'the ___ thing,' it's probably an adjective.",

    "Which word is a verb?":
        "'Jump' names an action, making it a verb. Quick test: if you can put 'I' or 'they' in front of it and it makes sense ('I jump'), it's likely a verb.",

    "The plural of 'man' is ___?":
        "'Men' is another ancient vowel-change plural from Old English. These irregular forms survive because 'man' and 'men' are among the most frequently used words in the language.",

    "The plural of 'woman' is ___?":
        "'Women' changes both its vowel sounds from 'woman' -- the 'o' shifts to short 'i' in pronunciation. It's one of the trickiest irregular plurals because the spelling barely changes.",

    "'He', 'she', and 'it' are examples of ___?":
        "These are third-person singular personal pronouns. 'He' and 'she' specify gender, while 'it' is used for things and animals (unless we know the animal personally!).",

    "A period, question mark, or exclamation point are all ___?":
        "End punctuation marks signal that a complete thought has finished. Every sentence needs exactly one of these three to close it out properly.",

    "A noun that names a specific person, place, or thing is a ___?":
        "Proper nouns get capitalized because they refer to one unique entity. 'Einstein,' 'Tokyo,' and 'the Eiffel Tower' are all proper nouns pointing to something irreplaceable.",

    "'Apple' is a ___ noun?":
        "'Apple' is common because it refers to any apple, not a specific one. If you're talking about the company Apple, though, it becomes a proper noun -- context matters!",

    "A noun you cannot see or touch, like 'love,' is a ___?":
        "Abstract nouns name invisible things: emotions (love, anger), qualities (beauty, strength), and concepts (justice, time). You can feel love, but you can't put it on a shelf.",

    "Which punctuation is used in a contraction like \"don't\"?":
        "The apostrophe marks where letters have been removed -- 'don't' is 'do not' with the 'o' deleted. Think of the apostrophe as a little tombstone for the missing letters.",

    "A sentence must contain at minimum a ___ and a ___?":
        "A subject and a verb are the bare minimum for a complete sentence. Even the shortest sentence in English -- 'Go!' -- has both: 'you' is the implied subject, and 'go' is the verb.",

    "The plural of 'ox' is ___?":
        "'Oxen' is one of only a handful of English words that still use the Old English '-en' plural. 'Children' and 'brethren' are its rare companions.",

    "The plural of 'goose' is ___?":
        "'Geese' follows the same ancient i-mutation vowel shift as mouse/mice and foot/feet. These forms have stubbornly survived over a thousand years of English evolution.",

    "The plural of 'leaf' is ___?":
        "Words ending in '-f' or '-fe' often change to '-ves' in the plural: leaf/leaves, knife/knives, wife/wives. The 'v' sound was the original pronunciation in Old English.",

    "The plural of 'wolf' is ___?":
        "'Wolves' follows the f-to-v pattern seen in leaf/leaves and knife/knives. In Old English, the 'f' between vowels was pronounced as 'v' -- the spelling just took centuries to catch up.",

    "A word used before a noun to limit or define it, like 'a' or 'the,' is a(n) ___?":
        "Articles are tiny but mighty -- 'the' is the single most used word in the English language. Together, 'a,' 'an,' and 'the' appear in virtually every sentence.",

    "'The' is a ___ article?":
        "'The' is definite because it points to a specific thing both speaker and listener know about. 'Pass me the salt' assumes there's one particular salt shaker in question.",

    "'A' and 'an' are ___ articles?":
        "'A' and 'an' are indefinite because they refer to any member of a group, not a specific one. Use 'an' before vowel sounds: 'an hour' (silent h) but 'a university' (sounds like 'yoo').",

    "A noun names a person, place, thing, or ___?":
        "Nouns also name ideas -- abstract concepts like 'democracy,' 'friendship,' and 'mathematics.' These invisible nouns are just as grammatically real as concrete ones you can touch.",

    "What part of speech connects two nouns in 'bread and butter'?":
        "'And' is a conjunction joining two equal nouns. It's the most common of the seven coordinating conjunctions (FANBOYS) and one of the most frequently used words in English.",

    "A sentence that makes a statement ends with a ___?":
        "Periods close declarative statements -- the workhorses of written communication. In British English, this punctuation mark is called a 'full stop,' which describes its job perfectly.",

    "Which part of speech does 'an adjective' modify?":
        "Adjectives always modify nouns or pronouns. If something describes a quality, size, color, or quantity of a noun, it's working as an adjective.",

    "An adverb can modify a verb, an adjective, or ___?":
        "Adverbs can even modify other adverbs, creating chains like 'very extremely slowly.' This triple-duty flexibility is what makes adverbs the most versatile modifiers in English.",

    "'Extremely' modifies what type of word?":
        "'Extremely' is an intensifier adverb that typically modifies adjectives ('extremely tall') or other adverbs ('extremely quickly'). It doesn't modify nouns -- that's an adjective's job.",

    "A proper noun is always written with a ___?":
        "Capital letters are the VIP badges of grammar -- they mark proper nouns as unique and specific. Even common nouns get capitals when they become part of a proper name ('Lake Michigan').",

    "'London' is a ___ noun?":
        "'London' names one specific city, making it a proper noun requiring capitalization. There's only one London... well, actually several worldwide, but each one is still a specific place!",

    "The word 'happiness' is a ___ noun?":
        "'Happiness' names an emotional state you can feel but can't physically touch, making it abstract. The suffix '-ness' is a common clue that a word is an abstract noun.",

    "A sentence that expresses strong emotion ends with a(n) ___?":
        "Exclamation points are the volume knobs of punctuation -- they turn up the intensity. Professional writers use them sparingly because overuse drains their power.",

    "A word that names a group acting as one, like 'team,' is a ___ noun?":
        "Collective nouns treat many individuals as one unit. 'The team wins' (singular) focuses on the group; 'the team argue' (British English) can emphasize the individuals within.",

    "The subject of a sentence performs the ___?":
        "The subject is the doer -- it performs the action expressed by the verb. In 'Lightning struck the tree,' lightning is performing the dramatic action of striking.",

    "Which word is an adverb?":
        "'Gently' modifies a verb to tell HOW something was done, making it an adverb. The '-ly' ending is the most common adverb marker, though not all adverbs have it ('fast,' 'well').",

    "Which word is a noun?":
        "'Book' names a thing, making it a noun. Quick test: can you put 'the' in front of it? 'The book' works perfectly, confirming it's a noun.",

    "The plural of 'bus' is ___?":
        "'Buses' is the standard plural. Some style guides accept 'busses,' but 'buses' is overwhelmingly preferred. Words ending in 's' typically add '-es' to form their plural.",

    "Which sentence is a question?":
        "'What time is it?' is the only interrogative sentence here -- it asks for information and ends with a question mark. Commands, statements, and exclamations serve different purposes.",

    "The expression 'beating around the bush' is an example of ___?":
        "Idioms are phrases whose meaning can't be guessed from the individual words. 'Beating around the bush' means avoiding the main point -- originally a hunting term for flushing game out of bushes.",

    "A proverb is a short traditional saying that ___?":
        "Proverbs compress generations of wisdom into pithy phrases. 'A stitch in time saves nine' has taught people about prevention for over 200 years without mentioning a single needle.",

    "The suffix '-ful' (as in 'hopeful,' 'careful') means ___?":
        "Adding '-ful' to a noun creates an adjective meaning 'full of' that quality: hope + ful = hopeful. Note it's spelled with one 'l,' not two like the word 'full' itself.",

    "The suffix '-less' (as in 'hopeless,' 'careless') means ___?":
        "'-Less' is the opposite of '-ful,' stripping away the quality: hopeful means full of hope, while hopeless means without it. Together, these suffixes create perfect antonym pairs.",

    "Which word choice is correct? 'The company will ___ its policy next month.'":
        "'Revise' is the verb form needed here after 'will.' 'Revision' is a noun, 'revised' is past tense, and 'revisory' isn't a standard English word.",

    # === TIER 2 ===
    "Which form of 'go' correctly completes: 'She ___ to the market yesterday'?":
        "'Went' is the irregular past tense of 'go.' English borrowed it from the verb 'wend' centuries ago -- one of the language's strangest substitutions.",

    "Past tense of 'bring'?":
        "'Brought' pairs with 'bring' just like 'thought' pairs with 'think' -- both follow the same Old English pattern of changing the vowel and adding '-ought.'",

    "Past tense of 'catch'?":
        "'Caught' follows the same pattern as teach/taught and buy/bought. These verbs shifted their vowels and added a '-t' ending, an ancient Germanic past-tense formation.",

    "Past tense of 'teach'?":
        "'Taught' rhymes with 'caught' and 'bought' because all three verbs underwent the same Old English sound change. Mnemonic: if you taught, you caught knowledge and bought wisdom.",

    "Past tense of 'buy'?":
        "'Bought' completes the '-ought' trio with 'brought' and 'thought.' These irregular forms are so deeply embedded in English that children learn them by age three.",

    "Past tense of 'think'?":
        "'Thought' is the irregular past tense of 'think.' Notice the pattern: think/thought, bring/brought, buy/bought -- all swap their vowels for '-ought.'",

    "Past tense of 'write'?":
        "'Wrote' is the simple past; 'written' is the past participle. Remember: 'I wrote a letter' (past) vs. 'I have written a letter' (present perfect).",

    "Past tense of 'speak'?":
        "'Spoke' is the simple past; 'spoken' is the past participle. These follow the classic 'strong verb' pattern: speak, spoke, spoken -- a vowel shift marks each tense.",

    "Past tense of 'eat'?":
        "'Ate' is the simple past tense, while 'eaten' is the past participle. Think: 'I ate lunch' vs. 'I have eaten lunch.' The vowel shifts tell the whole story.",

    "Past tense of 'swim'?":
        "'Swam' is the simple past; 'swum' is the past participle. The classic trio swim/swam/swum follows the 'i-a-u' vowel pattern, just like begin/began/begun.",

    "Past tense of 'begin'?":
        "'Began' mirrors the swim/swam/swum pattern: begin/began/begun. The 'i-a-u' vowel shift is one of English's most regular irregular verb patterns.",

    "The tense that describes an ongoing action in the past is ___?":
        "Past progressive uses 'was/were' + '-ing': 'She was running when it started raining.' It frames an action as happening at a specific moment in the past.",

    "The tense that describes a completed action before another past action is ___?":
        "Past perfect ('had' + past participle) shows which action came first: 'She had left before he arrived.' It's the flashback tense of English.",

    "A sentence with one independent clause is a ___ sentence?":
        "Simple sentences contain one complete thought. Don't confuse 'simple' with 'short' -- 'The quick brown fox jumped over the extraordinarily lazy dog' is still a simple sentence.",

    "A sentence with two independent clauses joined by 'and' is a ___ sentence?":
        "Compound sentences combine two independent clauses with a coordinating conjunction or semicolon. Both halves could stand alone as sentences -- the conjunction just links them.",

    "A sentence with one independent clause and one dependent clause is a ___ sentence?":
        "Complex sentences pair a main clause with a subordinate one: 'Although it rained, we went outside.' The dependent clause can't stand alone as a sentence.",

    "A sentence with two independent clauses and at least one dependent clause is ___?":
        "Compound-complex sentences are the most structurally rich type: 'Although it rained, we went outside, and we had a great time.' They combine the features of both compound and complex sentences.",

    "In a passive sentence, the subject ___ the action?":
        "In passive voice, the subject is acted upon: 'The ball was kicked by Tom.' The ball isn't doing anything -- it's receiving the kicking.",

    "In an active sentence, the subject ___ the action?":
        "Active voice puts the doer first: 'Tom kicked the ball.' It's more direct and vigorous than passive voice, which is why most style guides prefer it.",

    "'The ball was kicked by Tom' is ___ voice?":
        "The 'was + past participle + by' construction is the telltale sign of passive voice. The subject (ball) receives the action rather than performing it.",

    "'Tom kicked the ball' is ___ voice?":
        "The subject (Tom) performs the action directly, making this active voice. Active sentences are typically shorter, clearer, and more engaging than passive ones.",

    "The noun that receives the action of the verb is the ___ object?":
        "The direct object answers 'what?' or 'whom?' after the verb: 'She threw the ball' -- what did she throw? The ball. It directly receives the action.",

    "The noun that tells to whom the action is done is the ___ object?":
        "The indirect object is the beneficiary of the action: 'She gave him a book.' 'Him' tells us who received the book. It answers 'to/for whom?'",

    "In 'She gave him a book,' 'a book' is the ___ object?":
        "'A book' is what was given -- it directly receives the action of giving. The direct object answers 'gave what?' while the indirect object answers 'gave to whom?'",

    "In 'She gave him a book,' 'him' is the ___ object?":
        "'Him' is the recipient -- the person who indirectly benefits from the giving. Swap the word order to see it: 'She gave a book to him.'",

    "The verb tense that uses 'have' + past participle is ___?":
        "Present perfect ('have/has eaten') connects past actions to the present moment. 'I have visited Paris' implies the experience still matters now.",

    "The verb tense that uses 'had' + past participle is ___?":
        "Past perfect ('had eaten') places one past event before another: 'By the time I arrived, she had already left.' It's the time-travel tense of English.",

    "The verb tense that uses 'will have' + past participle is ___?":
        "Future perfect ('will have eaten') describes something completed before a future moment: 'By Friday, I will have finished the book.' It looks ahead to a completed action.",

    "A singular subject takes a ___ verb?":
        "Subject-verb agreement is non-negotiable: 'The dog runs' (singular) not 'The dog run.' The verb must match its subject's number, no matter what comes between them.",

    "A plural subject takes a ___ verb?":
        "'The dogs run' -- plural subjects take plural verbs. In English, oddly, plural verbs often look simpler (run) while singular verbs get the '-s' (runs).",

    "'Dogs run fast' -- 'dogs' and 'run' agree in ___?":
        "Subject-verb agreement is about number: singular subjects take singular verbs, plural subjects take plural verbs. 'Dogs' and 'run' are both plural, so they agree.",

    "Past tense of 'break'?":
        "'Broke' is the simple past; 'broken' is the past participle. The pattern break/broke/broken follows the classic strong-verb vowel shift.",

    "Past tense of 'fall'?":
        "'Fell' is the simple past, not 'fallen' (that's the past participle). Remember: 'He fell yesterday' but 'He has fallen many times.'",

    "Past tense of 'give'?":
        "'Gave' is the simple past; 'given' is the past participle. The vowel shift from 'i' to 'a' marks the past tense, while '-en' marks the participle.",

    "Past tense of 'make'?":
        "'Made' is one of the rare irregular verbs that shortens in the past tense -- dropping the 'k' sound entirely. It's been irregular since Old English 'macian/macode.'",

    "Past tense of 'come'?":
        "'Came' is the simple past; 'come' doubles as both present and past participle. 'He came yesterday' but 'He has come many times.'",

    "Past tense of 'grow'?":
        "'Grew' follows the ow/ew pattern shared with know/knew, throw/threw, and blow/blew. These verbs are all close cousins in the irregular verb family.",

    "Past tense of 'throw'?":
        "'Threw' matches the pattern of grow/grew and know/knew. The '-ow' ending shifts to '-ew' in the past tense for this whole group of irregular verbs.",

    "The helping verb used to form future tense is ___?":
        "'Will' transforms any verb into future tense: 'I will go,' 'she will eat.' In formal English, 'shall' was once preferred for first person, but 'will' has largely won out.",

    "The helping verb used to form passive voice is ___?":
        "Forms of 'be' (am, is, are, was, were, been) combine with a past participle to create passive voice: 'The cake was eaten.' No 'be,' no passive.",

    "The six main verb tenses include simple present, simple past, simple future, and three ___ tenses?":
        "The three perfect tenses (present perfect, past perfect, future perfect) all use 'have' + past participle. They describe completed actions relative to different time frames.",

    "In 'She seems tired,' 'seems' is a ___ verb?":
        "Linking verbs connect the subject to a description rather than showing action. 'Seems,' 'appears,' 'becomes,' and all forms of 'be' are common linking verbs.",

    "Past tense of 'freeze'?":
        "'Froze' is the simple past; 'frozen' is the past participle. The pattern freeze/froze/frozen mirrors speak/spoke/spoken -- a classic English strong-verb trio.",

    "Past tense of 'steal'?":
        "'Stole' is the simple past; 'stolen' is the past participle. The ea/o/o pattern mirrors the similar verb 'weave' (wove/woven).",

    "Past tense of 'hide'?":
        "'Hid' is the simple past; 'hidden' is the past participle. The vowel contracts from a long 'i' sound to a short one -- hide/hid/hidden.",

    "Past tense of 'bite'?":
        "'Bit' is the simple past; 'bitten' is the past participle. Like 'hide/hid,' the long 'i' shortens in the past tense.",

    "Past tense of 'meet'?":
        "'Met' shortens the vowel from long 'ee' to short 'e.' The same vowel-shortening pattern appears in feed/fed, bleed/bled, and read/read.",

    "Past tense of 'fight'?":
        "'Fought' follows the same pattern as think/thought and buy/bought -- the vowel changes and '-ght' appears. These are among English's most ancient irregular forms.",

    "Past tense of 'build'?":
        "'Built' swaps the 'd' ending for a 't' -- a common irregular verb pattern shared with spend/spent, send/sent, and bend/bent.",

    "The word 'read' in 'She read the book yesterday' is pronounced to rhyme with ___?":
        "'Read' is a sneaky verb -- spelled identically in present and past tense, but pronounced differently. Present 'read' rhymes with 'reed'; past 'read' rhymes with 'red.'",

    "Past tense of 'lend'?":
        "'Lent' follows the d-to-t pattern of bend/bent and send/sent. Fun fact: 'Lent' (the Christian season) is a completely different word from a different root.",

    "Past tense of 'bend'?":
        "'Bent' swaps the final 'd' for 't' in the past tense. This d-to-t shift is one of the most predictable irregular verb patterns in English: send/sent, spend/spent, lend/lent.",

    "Past tense of 'lose'?":
        "'Lost' adds a 't' while keeping the 'os' vowel. Don't confuse it with 'loose' (adjective meaning not tight) -- 'lose' and 'loose' are different words entirely.",

    "Past tense of 'cut'?":
        "'Cut' doesn't change at all in the past tense -- it's the same word. These unchanging verbs (put, shut, hit, let) are called 'zero-change' irregular verbs.",

    "Past tense of 'put'?":
        "'Put' is identical in all three forms: put/put/put. It's one of English's handful of zero-change verbs where context alone tells you the tense.",

    "Past tense of 'hit'?":
        "'Hit' stays the same across all tenses: hit/hit/hit. Like cut, put, and let, it's a zero-change verb -- wonderfully simple once you stop looking for a different form.",

    "Past tense of 'let'?":
        "'Let' never changes form: 'I let him go yesterday' and 'I let him go today' look identical. Only context reveals the tense.",

    "Past tense of 'set'?":
        "'Set' is another zero-change verb, joining cut, put, hit, and let in the club of verbs that refuse to change form for past tense.",

    "Past tense of 'read' (pronounced 'red')?":
        "The past tense of 'read' is spelled 'read' but pronounced 'red.' It's one of the few English words where the same spelling has two completely different pronunciations depending on tense.",

    "The plural of 'knife' is ___?":
        "'Knives' follows the f-to-v rule: when a word ends in '-fe,' the plural changes it to '-ves.' This ancient pattern also gives us wife/wives, life/lives, and leaf/leaves.",

    "The plural of 'half' is ___?":
        "'Halves' follows the same f-to-v plural pattern as knife/knives and calf/calves. The 'v' was actually the original Old English pronunciation -- the 'f' spelling came later.",

    "Which word is the correct homophone? 'I can ___ the sea from here.'":
        "'See' (to perceive with eyes) and 'sea' (body of water) sound identical but have completely different meanings and origins. Context is your only guide with homophones.",

    "Which word is the correct homophone? 'The ___ blew hard.'":
        "'Wind' (moving air) is the correct choice. English has many words spelled the same with different meanings -- 'wind' can also mean to turn or coil, but that's pronounced differently.",

    "The possessive form of 'James' is ___?":
        "The Chicago Manual of Style and most modern guides recommend 'James's' with the extra 's' after the apostrophe. You actually pronounce the extra 's' sound: 'JAMES-iz.'",

    "An apostrophe in 'can't' marks a ___?":
        "The apostrophe in contractions marks where letters were removed: 'can't' = 'cannot' (the 'no' disappears). This is different from possessive apostrophes, which show ownership.",

    "Past tense of 'draw'?":
        "'Drew' follows the aw/ew pattern seen in grow/grew. The past participle 'drawn' adds the '-n' suffix: 'She drew a picture' vs. 'She has drawn many pictures.'",

    "Past tense of 'blow'?":
        "'Blew' matches the pattern of grow/grew, know/knew, and throw/threw. These '-ow' verbs consistently shift to '-ew' in the past tense.",

    "Past tense of 'pay'?":
        "'Paid' is the standard past tense. 'Payed' only exists in the nautical sense of letting out rope. For money, it's always 'paid.'",

    "Past tense of 'spring'?":
        "'Sprang' is the preferred simple past; 'sprung' is the past participle. The i-a-u pattern (spring/sprang/sprung) mirrors sing/sang/sung and ring/rang/rung.",

    "Which sentence uses the correct apostrophe?":
        "'The dog's bone' correctly shows one dog owning the bone. 'Dogs'' would mean multiple dogs; 'dogs' with no apostrophe is just a plural with no possession.",

    "Which sentence corrects a comma splice?":
        "A semicolon properly joins two independent clauses without a conjunction. Comma splices illegally use just a comma where a semicolon, period, or conjunction is needed.",

    "A thesis statement in an essay should express ___?":
        "A thesis statement is your essay's compass -- it tells readers exactly what you'll argue and why it matters. Vague topics don't cut it; a thesis must be specific enough to debate.",

    "Topic sentences in body paragraphs serve to ___?":
        "Topic sentences are mini-thesis statements for individual paragraphs. They preview the paragraph's main point and create a bridge back to the overall thesis.",

    "A transition word like 'however' signals a ___?":
        "'However' pivots the argument in a new direction, signaling that what follows contradicts or qualifies what came before. It's the 'but' of formal writing.",

    "A transition word like 'therefore' signals ___?":
        "'Therefore' announces a logical conclusion drawn from the preceding evidence. It tells the reader: 'Because of everything I just said, this follows.'",

    "Which sentence uses the subjunctive mood correctly?":
        "'I wish I were taller' uses the subjunctive 'were' for an unreal condition. The subjunctive ignores normal agreement rules -- it's always 'were,' even with 'I,' 'he,' or 'she.'",

    "Which sentence demonstrates correct pronoun-antecedent agreement?":
        "Singular 'they' with 'each student' is now widely accepted in standard English. Major style guides including the APA and Chicago Manual endorse 'they' as a gender-neutral singular pronoun.",

    "Which sentence uses 'fewer' correctly?":
        "'Fewer' is for countable things (fewer students, fewer apples). 'Less' is for uncountable quantities (less water, less time). If you can count it, use 'fewer.'",

    "The phrase 'between you and I' is grammatically incorrect because 'I' should be ___?":
        "After a preposition (between, for, with), pronouns must be in the objective case: me, him, her, them. 'Between you and me' is correct because 'me' is the object of 'between.'",

    "The denotation of a word is its ___?":
        "Denotation is what the dictionary says; connotation is what the word feels like. 'Home' denotes a dwelling place but connotes warmth, safety, and belonging.",

    "When a politician uses 'passed away' instead of 'died,' this is an example of ___?":
        "Euphemisms soften harsh realities with gentler language. 'Passed away,' 'let go' (fired), and 'enhanced interrogation' (torture) all wrap uncomfortable truths in softer words.",

    "Which of the following best describes the connotation of 'stench' compared to 'smell'?":
        "Both words denote an odor detected by the nose, but 'stench' carries a powerfully negative connotation of something foul. Word choice shapes how readers feel about what you describe.",

    "Which correctly completes: 'The new law will ___ your ability to appeal.'":
        "'Affect' is the verb meaning to influence or change. 'Effect' is usually a noun meaning a result. Mnemonic: Affect is the Action (both start with A); Effect is the End result (both start with E).",

    "The prefix 'mis-' (as in 'misplace,' 'mistake') means ___?":
        "'Mis-' means wrongly or badly: misspell (spell wrongly), misunderstand (understand badly), misfire (fire incorrectly). It's been adding negativity to English verbs since Old English.",

    "Past tense of 'hang' when referring to suspending an object?":
        "'Hung' is used for objects: 'She hung the picture.' The distinction between 'hung' (objects) and 'hanged' (executions) is one of English's more morbid grammar rules.",

    "Past tense of 'hang' when referring to an execution?":
        "'Hanged' is reserved exclusively for execution by hanging. 'The outlaw was hanged at dawn.' For everything else -- pictures, curtains, heads -- use 'hung.'",

    "In 'She has been waiting for an hour,' the verb phrase is in which tense?":
        "Present perfect progressive combines 'has/have been' with '-ing' to show an action that started in the past and is still continuing. It emphasizes the ongoing duration of the action.",

    # === TIER 3 ===
    "A group of words with a subject and verb is a ___?":
        "Clauses contain a subject-verb pair, while phrases don't. 'The dog barked' is a clause; 'the big dog' is just a phrase -- no verb, no clause.",

    "A group of words without a subject and verb is a ___?":
        "Phrases are building blocks that lack a subject-verb pair. 'Under the bridge,' 'running quickly,' and 'the old house' are all phrases that need more to become sentences.",

    "A clause that can stand alone is a ___ clause?":
        "Independent clauses are self-sufficient -- they express a complete thought with a subject and verb. 'It rained' works alone. Dependent clauses like 'because it rained' cannot.",

    "A clause that cannot stand alone is a ___ clause?":
        "Dependent (or subordinate) clauses start with words like 'because,' 'although,' 'when,' or 'that.' They add information but can't stand as sentences on their own.",

    "A semicolon connects two ___?":
        "Semicolons join two independent clauses that are closely related in meaning. Think of a semicolon as a soft period -- it says 'these ideas are separate but connected.'",

    "Repeating a word or phrase at the start of successive clauses is ___?":
        "Anaphora creates rhythm and emphasis through repetition at the beginning. Martin Luther King Jr.'s 'I have a dream...' repeated eight times is perhaps the most famous anaphora in English.",

    "Repeating a word or phrase at the end of successive clauses is ___?":
        "Epistrophe is anaphora's mirror image -- repetition at the end. Lincoln's 'government of the people, by the people, for the people' is a masterful triple epistrophe.",

    "Placing contrasting ideas in parallel structure is ___?":
        "Antithesis sharpens ideas by setting opposites side by side. Neil Armstrong's 'one small step for man, one giant leap for mankind' derives its power from this contrast.",

    "Reversing the grammatical structure in successive phrases is ___?":
        "Chiasmus creates an X-shaped (chi = Greek X) pattern: AB then BA. Kennedy's 'Ask not what your country can do for you -- ask what you can do for your country' is the textbook example.",

    "Exaggeration for emphasis is ___?":
        "Hyperbole stretches truth for dramatic effect -- 'I've told you a million times!' Nobody means literally a million; the exaggeration conveys frustration more vividly than accuracy would.",

    "Understatement using negation ('not bad' for 'good') is ___?":
        "Litotes uses double negatives to create a subtle positive: 'not unkind' means kind, but with more nuance. It's a favorite device of British understatement and Old English poetry.",

    "A mild or indirect word substituted for a harsh one is a ___?":
        "Euphemisms cushion blunt realities. 'Collateral damage' for civilian deaths and 'pre-owned' for used are euphemisms that reshape how we perceive uncomfortable truths.",

    "The repetition of initial consonant sounds is ___?":
        "Alliteration has been a staple of English since before Shakespeare -- Old English poetry used it instead of rhyme. 'Peter Piper picked a peck' shows why it's so memorably musical.",

    "The repetition of vowel sounds within words is ___?":
        "Assonance creates internal music: 'The rain in Spain stays mainly in the plain' repeats the long 'a' sound throughout. It's subtler than rhyme but equally musical.",

    "A word that imitates the sound it describes is ___?":
        "Onomatopoeia makes words sound like their meaning: buzz, hiss, splash, crack. These words are rare cases where the sound-meaning connection isn't arbitrary.",

    "A phrase built around a present participle used as a noun is a ___ phrase?":
        "Gerund phrases use '-ing' verb forms as nouns: 'Running marathons requires dedication.' If you can replace the phrase with 'it' or 'something,' it's functioning as a gerund.",

    "A phrase built around 'to + verb' is a(n) ___ phrase?":
        "Infinitive phrases ('to run,' 'to boldly go') can function as nouns, adjectives, or adverbs. They're incredibly versatile -- one reason 'split infinitives' like Star Trek's famous line are so common.",

    "A phrase built around a verb form used as a modifier is a ___ phrase?":
        "Participial phrases use verb forms (-ing or -ed) as adjectives: 'Running quickly, the athlete crossed the finish line.' The phrase modifies 'athlete,' not functioning as the main verb.",

    "'Running daily is healthy' -- 'running daily' is a ___ phrase?":
        "'Running daily' is the subject of the sentence -- it names an activity. Since it's an '-ing' form used as a noun (not a modifier), it's a gerund phrase.",

    "'To win the race' is a(n) ___ phrase?":
        "This 'to + verb' construction is an infinitive phrase. Here it functions as a noun (naming a goal), but infinitives can also work as adjectives or adverbs depending on context.",

    "'Barking loudly, the dog ran away' -- 'barking loudly' is a ___ phrase?":
        "'Barking loudly' modifies 'the dog,' telling us how the dog was acting. Since this '-ing' phrase works as an adjective (not a noun), it's participial, not gerund.",

    "'My sister, a doctor, helped us' -- 'a doctor' is a(n) ___?":
        "An appositive renames the noun beside it, giving us more information. Here, 'a doctor' explains what my sister is. Remove it and the sentence still works -- that's the appositive test.",

    "A dependent clause used as a noun is a ___ clause?":
        "Noun clauses fill noun slots: 'What she said surprised me.' The clause 'what she said' works as the subject, just like a single noun would.",

    "A dependent clause used as a modifier of a noun is a(n) ___ clause?":
        "Adjective clauses modify nouns, usually introduced by 'who,' 'which,' or 'that': 'The book that I read was excellent.' The clause describes which book.",

    "A dependent clause that modifies a verb is a(n) ___ clause?":
        "Adverb clauses modify verbs, telling when, where, why, or how: 'She left because it was late.' The clause explains why she left, modifying the verb.",

    "Which device uses 'buzz' or 'crash' as words?":
        "Onomatopoeia creates words from sounds. 'Buzz,' 'crash,' 'sizzle,' and 'murmur' all echo the sounds they describe -- making language itself sound like the world.",

    "'Peter Piper picked a peck' uses ___?":
        "The repeated 'p' sound at the start of each word is alliteration. Tongue twisters rely on alliteration to create their delicious difficulty.",

    "'We shall fight on the beaches...we shall fight in the fields' uses ___?":
        "Churchill's repetition of 'we shall fight' at the beginning of each clause is anaphora. This device builds rhetorical momentum like waves crashing -- each repetition hits harder.",

    "'Ask not what your country can do for you, ask what you can do for your country' uses ___?":
        "Kennedy's line reverses the structure: 'country/you' becomes 'you/country.' This AB-BA reversal is chiasmus (from Greek 'chi,' meaning X-shaped crossing).",

    "'It was the best of times, it was the worst of times' uses ___?":
        "Dickens places 'best' against 'worst' in identical grammatical structures -- the hallmark of antithesis. The parallel structure makes the contrast razor-sharp.",

    "A colon is used to introduce a ___?":
        "Colons say 'here's what I mean' or 'here's the list.' They must follow a complete sentence: 'She bought three things: milk, eggs, and bread.' Never put a colon after a verb.",

    "A dash is used to show ___?":
        "Dashes create dramatic interruptions -- like this -- or add emphasis. They're more forceful than commas and more casual than parentheses, making them the punctuation of surprise.",

    "Parentheses are used to set off ___?":
        "Parentheses whisper supplementary details that could be removed without changing the sentence's core meaning. They're the stage whispers of punctuation -- audible but nonessential.",

    "An ellipsis (...) indicates ___?":
        "Ellipses create suspense, show trailing thoughts, or mark where text has been cut from a quotation. Those three little dots carry a surprising amount of dramatic weight...",

    "Which connects a dependent clause to an independent clause?":
        "Subordinating conjunctions (because, although, when, if, since) create a hierarchy: they make one clause dependent on another, showing cause, contrast, time, or condition.",

    "'Because,' 'although,' and 'since' are ___ conjunctions?":
        "Subordinating conjunctions turn independent clauses into dependent ones. 'It rained' is independent, but 'because it rained' can't stand alone -- 'because' subordinated it.",

    "'For, and, nor, but, or, yet, so' are ___ conjunctions?":
        "The seven coordinating conjunctions join equal elements. FANBOYS is the mnemonic: For, And, Nor, But, Or, Yet, So. They connect words, phrases, or independent clauses of equal rank.",

    "The mnemonic 'FANBOYS' stands for ___ conjunctions?":
        "FANBOYS = For, And, Nor, But, Or, Yet, So. These seven coordinating conjunctions are the only words that can join two independent clauses with just a comma before them.",

    "A word or phrase that modifies the wrong noun due to placement is a ___ modifier?":
        "'I saw the man with the telescope' -- did you use a telescope to see him, or does he have one? Misplaced modifiers create confusion by sitting next to the wrong noun.",

    "A modifier that has no logical subject in the sentence is a ___ modifier?":
        "'Walking to school, the rain started.' Who was walking? Not the rain! Dangling modifiers have no subject to attach to, creating absurd images.",

    "The repetition of consonant sounds throughout a phrase (not just at the start) is ___?":
        "Consonance repeats consonant sounds anywhere in words: 'pitter-patter' repeats the 't' sound. Unlike alliteration (initial sounds only), consonance can occur at the beginning, middle, or end.",

    "A relative clause is introduced by a ___ pronoun?":
        "Relative pronouns (who, whom, whose, which, that) introduce clauses that describe nouns. 'The student who studied passed' -- 'who' links the clause back to 'student.'",

    "'Who,' 'which,' and 'that' are ___ pronouns?":
        "Relative pronouns create relative clauses that modify nouns. 'Who' is for people, 'which' for things, and 'that' can work for both in restrictive clauses.",

    "A non-restrictive clause is set off by ___?":
        "Commas signal that the clause is bonus information: 'My brother, who lives in Paris, is visiting.' Remove the clause and the sentence still identifies which brother you mean.",

    "A restrictive clause ___ set off by commas?":
        "Restrictive clauses are essential for identification: 'Students who study hard pass.' Removing it changes the meaning entirely, so no commas are needed.",

    "'Like a ghost' is a ___?":
        "Similes compare using 'like' or 'as': 'like a ghost' explicitly flags the comparison. This distinguishes similes from metaphors, which state the comparison directly.",

    "'He is a rock' is a ___?":
        "Metaphors state that one thing IS another, without 'like' or 'as.' 'He is a rock' doesn't mean he's literally a stone -- it transfers the qualities of steadiness and strength.",

    "Giving human qualities to non-human things is ___?":
        "Personification brings non-human things to life: 'The wind whispered through the trees.' Wind can't actually whisper, but the human quality makes the image vivid and relatable.",

    "A statement that contradicts itself but reveals a truth is a ___?":
        "Paradoxes seem logically impossible yet express something true: 'The only constant is change.' The contradiction forces deeper thinking about the underlying truth.",

    "Two contradictory words placed together ('deafening silence') is a(n) ___?":
        "Oxymorons compress paradoxes into two words: 'jumbo shrimp,' 'bittersweet,' 'living dead.' The Greek roots literally mean 'sharp-dull' -- the word is itself an oxymoron!",

    "Saying the opposite of what you mean is ___?":
        "Irony creates a gap between what's said and what's meant. Saying 'What lovely weather!' during a hurricane is verbal irony. The audience must read between the lines.",

    "A clause that cannot stand alone as a sentence is a ___ clause?":
        "Dependent clauses need an independent clause to lean on. 'Because it rained' leaves you hanging -- it needs a main clause like 'we stayed inside' to complete the thought.",

    "A clause that can stand alone as a sentence is a(n) ___ clause?":
        "Independent clauses are grammatically self-sufficient. They have a subject, a verb, and express a complete thought. They're sentences waiting to happen.",

    "Which word introduces a dependent clause? 'She left ___ it started raining.'":
        "'Because' is a subordinating conjunction that turns 'it started raining' into a dependent clause explaining why she left. Coordinating conjunctions like 'and' wouldn't create that subordination.",

    "A comma splice occurs when two independent clauses are joined with only a ___?":
        "A comma alone can't join two complete sentences. You need a semicolon, a period, or a comma plus a conjunction. 'I ran, I won' is a splice; 'I ran, and I won' fixes it.",

    "Which sentence contains a comma splice?":
        "'It rained, we stayed inside' splices two independent clauses with just a comma. Fix it with a semicolon ('It rained; we stayed inside') or a conjunction ('It rained, so we stayed inside').",

    "A semicolon can join two ___ clauses?":
        "Semicolons are exclusively for independent clauses -- each side must be able to stand alone as a sentence. Think of the semicolon as a period that invites the reader to see a connection.",

    "Which is correct use of a semicolon?":
        "'She ran fast; she won' correctly joins two related independent clauses. A semicolon after a fragment ('She ran; quickly') or before a conjunction ('She ran; and won') is incorrect.",

    "Subject-verb agreement means the subject and verb must match in ___?":
        "Singular subjects need singular verbs; plural subjects need plural verbs. The tricky part is identifying the true subject when phrases intervene: 'The box of chocolates IS heavy,' not 'are.'",

    "Which sentence has correct subject-verb agreement?":
        "'The cat runs fast' correctly matches a singular subject (cat) with a singular verb (runs). In English, singular third-person verbs typically end in '-s.'",

    "Parallel structure means items in a list must have the same ___?":
        "Parallel structure keeps lists grammatically consistent. 'She likes hiking, swimming, and running' (all gerunds) flows smoothly, while mixing forms creates a jarring stumble.",

    "Which sentence uses parallel structure?":
        "'Hiking, swimming, and running' are all gerunds (-ing forms), creating clean parallel structure. Mixing 'hiking, to swim, and runs' breaks the pattern and sounds clumsy.",

    "An introductory phrase is generally followed by a ___?":
        "A comma after an introductory phrase gives the reader a breath before the main clause: 'After the storm, the sun returned.' Without it, sentences can be misread.",

    "Which correctly punctuates an introductory phrase?":
        "'After the storm, the sun returned' places a comma after the introductory prepositional phrase. This comma prevents misreading and creates a natural pause.",

    "A non-restrictive clause adds extra information and is set off by ___?":
        "Commas around non-restrictive clauses signal 'you could skip this.' In 'My car, which is red, broke down,' the color is bonus info -- the sentence works fine without it.",

    "Which word typically introduces a non-restrictive relative clause?":
        "'Which' typically introduces non-restrictive (extra information) clauses set off by commas. Mnemonic: 'which' has a comma; 'that' does not -- 'which witch has commas.'",

    "Which word typically introduces a restrictive relative clause?":
        "'That' introduces essential information without commas: 'The book that I read was great.' Remove the clause and you lose crucial meaning -- which book?",

    "A run-on sentence contains two or more independent clauses without proper ___?":
        "Run-on sentences smash clauses together without punctuation or conjunctions: 'I ran I won.' Fix them with a period, semicolon, or comma-conjunction combination.",

    "The Oxford comma is placed before the ___ item in a list?":
        "The Oxford (or serial) comma goes before the final 'and' in a list. Without it, 'I love my parents, Batman and Wonder Woman' makes your parents sound like superheroes.",

    "Which sentence uses the Oxford comma?":
        "'Milk, eggs, and butter' includes a comma before 'and' -- that's the Oxford comma. It prevents ambiguity in lists, which is why many style guides require it.",

    "A dangling modifier has no clear ___ to modify?":
        "Dangling modifiers are orphans -- they describe something that isn't actually in the sentence. 'Walking to school, the rain started' leaves us wondering who was walking.",

    "Which sentence contains a dangling modifier?":
        "'Running fast, the race was won' dangles because the race wasn't running fast -- a person was. The modifier needs a human subject: 'Running fast, she won the race.'",

    "A misplaced modifier is a modifier placed too far from the word it ___?":
        "Distance causes confusion: 'She only ate two cookies' (maybe she only ate them, didn't share?) vs. 'She ate only two cookies' (she ate just two). Placement matters enormously.",

    "Which verb mood expresses a command?":
        "Imperative mood gives direct orders: 'Close the door!' 'Be quiet!' The subject 'you' is always implied, making imperatives the only sentences with an invisible subject.",

    "Which verb mood expresses facts or opinions?":
        "Indicative is the default mood -- used for statements and questions about reality. 'The sky is blue' and 'Is the sky blue?' are both indicative.",

    "Which verb mood expresses wishes or hypotheticals?":
        "Subjunctive mood handles unreal situations: 'If I were rich' (not 'was'). It's fading from casual English but survives in phrases like 'God save the Queen' and 'come what may.'",

    "In 'If I were you, I would go,' 'were' is an example of ___?":
        "The subjunctive 'were' signals an unreal condition -- you're not actually the other person. Standard agreement would use 'was,' but the subjunctive deliberately breaks that rule.",

    "An appositive is a noun phrase that renames the ___ next to it?":
        "Appositives are renaming machines: 'My friend, a talented musician, performed.' 'A talented musician' gives us a new label for the same noun without using a separate sentence.",

    "Which sentence contains a correctly punctuated appositive?":
        "'My sister, Lisa, is a doctor' correctly wraps the appositive 'Lisa' in commas. Both commas are needed -- one opens the aside and one closes it.",

    "A colon is used to introduce a list after a ___?":
        "A colon must follow a grammatically complete sentence. 'She needs: milk and eggs' is wrong because 'She needs' isn't complete. 'She needs the following: milk and eggs' works.",

    "Which correctly uses a colon?":
        "'She needs the following: milk and eggs' places the colon after a complete independent clause. The golden rule: if the part before the colon can't stand alone, don't use a colon.",

    "A sentence fragment is missing a subject, a verb, or a ___?":
        "Fragments lack one or more essentials: a subject ('Ran quickly'), a verb ('The tall man in the hat'), or a complete thought ('Because it rained'). All three must be present.",

    "Which is a sentence fragment?":
        "'Because it was raining' has a subject and verb but doesn't express a complete thought -- 'because' makes it dependent on a main clause that never arrives.",

    "'Neither the students nor the teacher ___ ready.' Which verb form is correct?":
        "With 'neither...nor,' the verb agrees with the nearest subject. Since 'the teacher' (singular) is closest to the verb, use 'is.' If reversed, 'Neither the teacher nor the students are ready.'",

    "A coordinating conjunction joins two elements of ___ importance?":
        "Coordinating conjunctions connect equals -- two nouns, two clauses, two phrases of the same grammatical rank. Subordinating conjunctions, by contrast, create a hierarchy.",

    "The acronym FANBOYS stands for the ___ coordinating conjunctions?":
        "FANBOYS captures all seven: For, And, Nor, But, Or, Yet, So. There are only seven, no more -- making them one of the shortest complete lists in English grammar.",

    "Which is NOT one of the FANBOYS conjunctions?":
        "'Although' is a subordinating conjunction, not a coordinating one. It creates a dependent clause ('Although it rained') rather than joining equals. FANBOYS has no room for 'although.'",

    "A subordinating conjunction introduces a ___ clause?":
        "Subordinating conjunctions demote independent clauses to dependent status. 'It rained' stands alone, but 'because it rained' needs a partner clause to complete its meaning.",

    "Which is a subordinating conjunction?":
        "'Although' creates a concessive dependent clause: 'Although it rained, we went out.' Unlike coordinating conjunctions (and, but), it makes its clause subordinate.",

    "The past participle of 'write' is ___?":
        "'Written' is the past participle used with 'have': 'I have written a letter.' Don't confuse it with the simple past 'wrote': 'I wrote a letter yesterday.'",

    "The past participle of 'break' is ___?":
        "'Broken' is used with 'have' or 'be': 'The window has been broken.' The simple past 'broke' doesn't need a helper verb: 'She broke the window.'",

    "The past participle of 'speak' is ___?":
        "'Spoken' pairs with 'have' or 'be': 'She has spoken.' The pattern speak/spoke/spoken follows the classic three-form irregular verb model.",

    "The past participle of 'give' is ___?":
        "'Given' is the past participle: 'She has given generously.' Don't confuse it with the simple past 'gave': 'She gave generously last year.'",

    "The past participle of 'eat' is ___?":
        "'Eaten' requires a helper verb: 'I have eaten' or 'The cake was eaten.' The simple past 'ate' stands alone: 'I ate breakfast at eight.'",

    "A gerund is a verb form ending in '-ing' that functions as a ___?":
        "Gerunds are verbs moonlighting as nouns: 'Swimming is fun.' The '-ing' form looks like a present participle, but if it fills a noun slot (subject, object), it's a gerund.",

    "An infinitive is the base form of a verb usually preceded by ___?":
        "Infinitives use 'to' + verb: 'to run,' 'to eat,' 'to sleep.' They're the Swiss Army knives of grammar, functioning as nouns, adjectives, or adverbs depending on context.",

    "A participle is a verb form that functions as a(n) ___?":
        "Participles are verbs working as adjectives: 'the running water,' 'the broken vase.' Both present participles (-ing) and past participles (-ed/-en) can modify nouns.",

    "In 'Swimming is fun,' 'swimming' is a ___?":
        "'Swimming' is the subject of the sentence -- a noun position. Since it's a verb form filling a noun slot, it's a gerund. If it were modifying a noun ('the swimming child'), it would be a participle.",

    "Which is NOT one of the three modes of classical persuasion (the rhetorical triangle)?":
        "Aristotle's three modes are ethos (credibility), pathos (emotion), and logos (logic). Kairos (timing/context) is an important rhetorical concept but is not one of the three appeal modes.",

    "Ethos, as a rhetorical mode, persuades by appealing to the speaker's ___?":
        "Ethos builds trust through the speaker's character, expertise, and reputation. A doctor citing medical research uses ethos -- we believe them because of who they are.",

    "Pathos persuades by appealing to the audience's ___?":
        "Pathos moves hearts, not minds. A charity showing photos of hungry children uses pathos -- it bypasses logic and speaks directly to compassion and sympathy.",

    # === TIER 4 ===
    "Understatement using negation is ___?":
        "Litotes says less to mean more: 'not bad' means 'quite good.' Ancient Norse warriors loved this device -- calling a fierce battle 'no small matter' was peak Viking understatement.",

    "A figure of speech where a part represents the whole ('all hands on deck') is ___?":
        "Synecdoche uses a part (hands) to represent the whole (sailors). 'Nice wheels!' means the whole car, not just its wheels. The part becomes a vivid stand-in for the whole.",

    "Substituting a related concept for a thing ('the Crown' for the monarchy) is ___?":
        "Metonymy substitutes a related concept rather than a part. 'The White House announced' doesn't mean the building spoke -- it means the president's administration did.",

    "A single verb governing two different objects with different meanings is ___?":
        "Zeugma yokes one verb to two objects with different meanings: 'She lost her keys and her temper.' 'Lost' works literally for keys and figuratively for temper.",

    "Using one word to govern two others where it grammatically fits only one is ___?":
        "Syllepsis is zeugma's stricter cousin -- the word grammatically fits only one of its objects. 'She caught the bus and a cold' uses 'caught' in two incompatible senses.",

    "A sentence that trails off unfinished, indicated by a dash or ellipsis, is ___?":
        "Aposiopesis (from Greek 'becoming silent') creates suspense by stopping mid-thought: 'If you don't behave, I swear I'll--' The unspoken threat is often more powerful than words.",

    "A sentence that shifts grammatical construction midway is ___?":
        "Anacoluthon deliberately breaks grammatical flow: 'If you think -- well, never mind what you think.' The mid-sentence shift mirrors how people actually speak when agitated.",

    "Expressing a single idea through two nouns joined by 'and' ('nice and warm' for 'nicely warm') is ___?":
        "Hendiadys (Greek for 'one through two') splits one idea into paired nouns. Shakespeare loved it: 'sound and fury' instead of 'furious sound.'",

    "Using many conjunctions in succession ('and...and...and') is ___?":
        "Polysyndeton piles up conjunctions to create a sense of abundance or breathless accumulation. The Bible's 'and God said... and it was so... and God saw' builds majestic rhythm.",

    "Omitting conjunctions between clauses is ___?":
        "Asyndeton strips away conjunctions for speed and urgency. Caesar's 'I came, I saw, I conquered' moves at lightning pace because no 'and' slows it down.",

    "A sentence that builds to its main point at the end is a ___ sentence?":
        "Periodic sentences delay the payoff, creating suspense. The reader must hold all the subordinate details in mind until the main clause finally arrives at the end.",

    "A sentence that states its main point first and then adds details is a ___ sentence?":
        "Cumulative sentences deliver the main point upfront, then pile on supporting details. They feel natural and conversational, like adding brushstrokes to a painting.",

    "The grammatical mood used for hypotheticals and wishes is ___?":
        "The subjunctive mood expresses the unreal: wishes, demands, and hypotheticals. 'If I were a bird' (not 'was') uses subjunctive because you're imagining an impossibility.",

    "The grammatical mood used for facts and questions is ___?":
        "Indicative mood is reality mode -- it states facts ('The sun rises') and asks questions ('Does it rise?'). It's the mood of everyday communication.",

    "The grammatical mood used for commands is ___?":
        "Imperative mood turns sentences into orders: 'Run!' 'Be careful!' It's the only mood where the subject ('you') typically vanishes, leaving just the bare command.",

    "The tense expressing action completed before a past moment ('had run') is ___?":
        "The pluperfect (Latin for 'more than perfect') marks the earlier of two past events: 'She had already left when I arrived.' It's the 'flashback within a flashback' tense.",

    "'Pluperfect' is another name for ___?":
        "Pluperfect and past perfect are the same tense -- 'had' + past participle. 'Pluperfect' is the traditional Latin term; 'past perfect' is the modern English name.",

    "'Either/or' is a ___ conjunction?":
        "Correlative conjunctions work in inseparable pairs: either/or, neither/nor, both/and. They correlate two parallel elements, which is how they got their name.",

    "'Neither/nor' is a ___ conjunction?":
        "Neither/nor is a correlative pair that presents two negated options. Both elements after 'neither' and 'nor' should be grammatically parallel for proper structure.",

    "'Both/and' is a ___ conjunction?":
        "Both/and is the inclusive correlative pair -- it embraces two things simultaneously. 'Both brave and kind' is properly parallel; 'both brave and she was kind' is not.",

    "'Not only/but also' is a ___ conjunction?":
        "Not only/but also escalates from one point to a more impressive one: 'Not only did she finish, but she also won.' The 'but also' delivers the bigger surprise.",

    "A modifier placed too far from the word it modifies is ___?":
        "Distance breeds confusion: 'She served cake to the children on paper plates' -- were the children on paper plates? Moving modifiers next to their target fixes the ambiguity.",

    "A modifier that could modify either the word before or after it is a ___ modifier?":
        "Squinting modifiers look in two directions at once: 'Students who study often pass.' Does 'often' modify 'study' or 'pass'? Repositioning eliminates the ambiguity.",

    "A participial phrase whose implied subject differs from the sentence subject is a ___ modifier?":
        "Dangling modifiers create accidental comedy: 'Covered in chocolate, I ate the strawberry.' This literally says YOU were covered in chocolate. The strawberry should be the subject.",

    "An absolute phrase contains a noun and a ___?":
        "Absolute phrases pair a noun with a participle and modify the whole sentence: 'Her eyes sparkling, she accepted the award.' They're grammatically independent from the main clause.",

    "In 'If I were king,' the verb 'were' is ___?":
        "Subjunctive 'were' signals an unreal condition. Normal agreement would use 'was' with 'I,' but the subjunctive deliberately breaks this rule to flag the hypothetical nature of the statement.",

    "The rhetorical device of addressing an absent person or abstract idea is ___?":
        "Apostrophe (the rhetorical kind, not the punctuation) turns to address someone absent: 'O Death, where is thy sting?' The speaker knows Death can't answer, but the address is powerful.",

    "A question asked not for information but for effect is a ___ question?":
        "Rhetorical questions already know their answer: 'Is the sky blue?' or 'Who wouldn't want world peace?' They engage the audience's mind without expecting a verbal response.",

    "Using a specific name for a general type ('a Kleenex' for any tissue) is ___?":
        "Antonomasia replaces common nouns with brand names or proper nouns. 'Band-Aid,' 'Jacuzzi,' and 'Google it' all started as specific names that became generic terms.",

    "Describing something through a roundabout phrase is ___?":
        "Periphrasis uses more words than necessary, often for poetic or euphemistic effect. 'The Bard of Avon' instead of 'Shakespeare' is a classic example.",

    "Using words that contradict their literal meaning for humorous effect is ___?":
        "Sarcasm weaponizes irony for mockery or humor. 'Oh great, another Monday' uses words that literally mean something positive to express something entirely negative.",

    "A word formed by combining parts of two words ('brunch') is a ___?":
        "Portmanteau words blend the sounds and meanings of two sources: breakfast + lunch = brunch, smoke + fog = smog. Lewis Carroll coined the term in 'Through the Looking-Glass.'",

    "The grammatical case of a pronoun used as a subject is ___?":
        "Nominative case marks the subject: I, he, she, we, they. 'He runs' uses nominative because 'he' performs the action. Switch to 'She saw him' and 'him' becomes objective.",

    "The grammatical case of a pronoun used as an object is ___?":
        "Objective case marks pronouns receiving the action: me, him, her, us, them. After prepositions and as direct/indirect objects, always use objective case.",

    "The case of 'him' in 'She saw him' is ___?":
        "'Him' receives the action of seeing, making it the direct object in objective case. The subject 'she' is nominative; the object 'him' is objective.",

    "The case of 'he' in 'He ran' is ___?":
        "'He' performs the action, making it the subject in nominative case. If he were receiving an action instead ('She saw him'), the pronoun would shift to objective case.",

    "A clause introduced by a relative pronoun that identifies the noun is a ___ clause?":
        "Restrictive clauses are essential identifiers: 'The students who studied passed.' Remove it and you change the meaning -- which students? All of them? Only some? The clause tells us.",

    "A clause that adds extra (removable) information about the noun is a ___ clause?":
        "Non-restrictive clauses add bonus details: 'My mother, who is 60, still runs marathons.' Remove it and the sentence still makes sense -- we still know who your mother is.",

    "Grammar that describes how language is actually used is called ___?":
        "Descriptive grammar observes language like a scientist observes nature. It documents how people actually speak, without judging whether it's 'correct' by traditional standards.",

    "Grammar that prescribes how language should be used is called ___?":
        "Prescriptive grammar sets rules and standards -- it says 'don't end sentences with prepositions.' Style guides, teachers, and editors typically work in prescriptive mode.",

    "Repeating the same grammatical structure in successive phrases is ___?":
        "Parallelism creates rhythm through structural repetition: 'I came, I saw, I conquered' uses three identical subject-verb patterns. It's the backbone of powerful rhetoric.",

    "Mentioning something by saying you will not mention it is ___?":
        "Paralipsis is the art of strategic denial: 'I won't even mention his criminal record.' By claiming to skip it, you've actually highlighted it. Politicians love this trick.",

    "'Apophasis' and 'paralipsis' both refer to ___?":
        "Both terms describe the same rhetorical sleight of hand: drawing attention to something while pretending to dismiss it. 'Far be it from me to suggest...' suggests exactly that.",

    "Combining contradictory terms into a single expression is a(n) ___?":
        "Oxymorons compress contradiction into a phrase: 'bittersweet,' 'deafening silence,' 'virtual reality.' The tension between opposites creates meanings neither word could achieve alone.",

    "A correlative conjunction pair used for alternatives is ___?":
        "Either/or presents two choices: 'Either study or fail.' The pair frames a decision between alternatives, unlike both/and (inclusion) or neither/nor (double exclusion).",

    "A conjunctive adverb connects two independent clauses with a ___ before it?":
        "Conjunctive adverbs (however, therefore, moreover) need a semicolon before them, not just a comma. 'I studied hard; therefore, I passed.' A comma alone creates a comma splice.",

    "'However,' 'therefore,' and 'moreover' are ___ adverbs?":
        "Conjunctive adverbs bridge independent clauses while showing the logical relationship between them. They combine the roles of conjunctions and adverbs -- hence the double name.",

    "When a single verb applies to two objects in different senses ('She lost her keys and her temper'), this is ___?":
        "Zeugma creates wit by yoking different meanings: 'She lowered her standards and her neckline.' The verb 'lost' applies literally to keys and figuratively to temper.",

    "A word that sounds like another but differs in meaning ('to/two/too') is a ___?":
        "Homophones sound identical but have different meanings and often different spellings. English is full of them because spelling was standardized long after pronunciation shifted.",

    "A word spelled the same as another but with different meaning ('lead' the metal / 'lead' to guide) is a ___?":
        "Homographs share spelling but differ in meaning (and sometimes pronunciation). 'Lead' the metal and 'lead' the verb look identical on paper but sound completely different.",

    "A sentence in which the subject receives the action is in ___ voice?":
        "Passive voice reverses the typical actor-action order: 'The cake was eaten' hides who did the eating. It's useful when the doer is unknown or unimportant.",

    "Which sentence is in active voice?":
        "'She ate the cake' puts the subject (she) before the action (ate) -- classic active voice. Active voice is more direct, concise, and engaging for most writing.",

    "The conditional perfect tense is formed with 'would have' + ___?":
        "'Would have' + past participle expresses unrealized past possibilities: 'I would have gone if I had known.' It describes what might have happened but didn't.",

    "Which is a first conditional sentence (real possibility)?":
        "First conditionals use 'if + present, will + base verb' for real possibilities: 'If it rains, I will stay home.' The rain is genuinely possible, so we use present tense for it.",

    "Which is a second conditional sentence (unreal present)?":
        "Second conditionals use 'if + past, would + base verb' for imaginary present situations: 'If I were rich, I would travel.' The past tense signals unreality, not past time.",

    "Which is a third conditional sentence (unreal past)?":
        "Third conditionals use 'if + past perfect, would have + past participle' for unrealized past events. 'If she had studied, she would have passed' -- but she didn't study.",

    "An em dash is used to indicate a(n) ___?":
        "Em dashes create dramatic pauses or interruptions -- like this. Named for being the width of the letter 'M,' they're bolder than commas and more informal than parentheses.",

    "A hyphen is used to join words in a ___ adjective before a noun?":
        "Compound adjectives need hyphens before a noun: 'a well-known author' but 'the author is well known.' The hyphen tells readers the two words work as a single modifier.",

    "Which is correctly hyphenated?":
        "'A well-known author' correctly hyphenates the compound adjective before the noun. After the noun ('The author is well known'), no hyphen is needed.",

    "Ellipsis marks (...) indicate ___?":
        "Ellipsis points signal something is missing or trailing away. In quotations, they mark omitted words. In dialogue, they show hesitation: 'I thought maybe... never mind.'",

    "Brackets [ ] within a quotation are used to enclose ___?":
        "Brackets mark editorial insertions within quotations: 'He [the president] announced the policy.' They distinguish the editor's additions from the original speaker's words.",

    "A nominative absolute is a phrase consisting of a noun and a ___?":
        "Nominative absolutes combine a noun with a participle to modify the entire sentence: 'The sun having set, we went inside.' They're grammatically independent of the main clause.",

    "The subjunctive form in 'I recommend that he ___ on time' is ___?":
        "After verbs of recommendation, demand, or suggestion, the subjunctive uses the bare infinitive: 'that he be on time,' not 'that he is.' It's one of the subjunctive's last strongholds in English.",

    "Polysyndeton is the use of ___ conjunctions than usual?":
        "Polysyndeton piles on conjunctions for emphasis: 'We ate and drank and laughed and sang.' The extra 'ands' create a sense of abundance and breathless excitement.",

    "Asyndeton is the deliberate ___ of conjunctions?":
        "Asyndeton strips out conjunctions for speed and impact: 'I came, I saw, I conquered.' The absence of 'and' makes each clause hit like a drumbeat.",

    "Anaphora is the repetition of a word or phrase at the ___ of successive clauses?":
        "Anaphora hammers a point home through opening repetition. 'We shall fight on the beaches, we shall fight on the landing grounds' -- the repeated 'we shall fight' builds unstoppable momentum.",

    "Epistrophe is the repetition of a word or phrase at the ___ of successive clauses?":
        "Epistrophe repeats at the end for a cumulative hammering effect. 'When I was a child, I spoke as a child, I understood as a child, I thought as a child' builds through ending repetition.",

    "Chiasmus reverses the order of words in ___ parallel phrases?":
        "Chiasmus creates an AB-BA mirror: 'Never let a fool kiss you, or a kiss fool you.' The reversed structure creates a satisfying symmetry that makes the line memorable.",

    "Antithesis places contrasting ideas in ___ grammatical structure?":
        "Antithesis sharpens contrasts by putting opposites in identical structure: 'That's one small step for man, one giant leap for mankind.' The parallel framing makes the contrast razor-sharp.",

    "A syllepsis (or zeugma) uses one word to govern two others in ___ senses?":
        "The beauty of zeugma is in the double meaning: 'She broke his car and his heart.' The verb 'broke' works literally for the car and metaphorically for the heart.",

    "Litotes is a form of understatement using ___?":
        "Litotes employs double negatives to create an understated positive: 'not unhappy' means happy, but with deliberate restraint. It's the literary equivalent of a knowing nod.",

    "Which is an example of litotes?":
        "'She is not unkind' uses two negatives ('not' + 'unkind') to quietly affirm that she IS kind. The understatement suggests kindness without outright declaring it.",

    "A split infinitive places a word between 'to' and the ___?":
        "Split infinitives insert an adverb between 'to' and its verb: 'to boldly go.' Once considered incorrect, they're now widely accepted -- sometimes splitting is clearer than not.",

    "Which sentence contains a split infinitive?":
        "'To quickly finish' splits the infinitive 'to finish' with the adverb 'quickly.' Star Trek's 'to boldly go' is the most famous split infinitive in pop culture.",

    "The pluperfect tense is also called the ___?":
        "Pluperfect and past perfect are two names for the same tense -- 'had' + past participle. 'Pluperfect' comes from Latin 'plus quam perfectum' meaning 'more than completed.'",

    "The future perfect tense expresses an action completed ___ a future point?":
        "Future perfect looks forward to a completed action: 'By midnight, I will have finished.' The action will be done before the stated future moment arrives.",

    "Which sentence is in the future perfect tense?":
        "'By noon, she will have run the race' describes an action that will be completed before noon. The 'will have + past participle' construction is the future perfect signature.",

    "A correlative conjunction works in pairs, such as ___?":
        "Correlative conjunctions always travel in pairs: either/or, neither/nor, both/and, not only/but also. Using one without its partner is like wearing one shoe.",

    "Which is a correlative conjunction pair?":
        "Neither/nor is a correlative pair that negates two options: 'Neither rain nor snow will stop us.' Each pair has its own logical function -- neither/nor excludes both.",

    "Which pronoun is in the nominative case?":
        "'They' is nominative (subject) case. 'Him,' 'her,' and 'them' are all objective (object) case. Quick test: if the pronoun does the action, it should be nominative.",

    "Which pronoun is in the objective case?":
        "'Whom' is the objective form of 'who.' It's used when the pronoun receives the action: 'Whom did you call?' Substitute 'him' to test: 'You called him' works, so 'whom' is correct.",

    "'Who' is used as a ___ in a clause?":
        "'Who' is the subject form: 'Who called?' (He called.) 'Whom' is the object form: 'Whom did you call?' (You called him.) Subject = who; object = whom.",

    "Which is correct? '___ did you speak to?'":
        "'Whom' is correct because it's the object of the preposition 'to.' Test it: 'You spoke to him' (not 'he'), so 'whom' (the objective form) is right.",

    "A predicate adjective follows a linking verb and modifies the ___?":
        "Predicate adjectives describe the subject through a linking verb: 'The soup tastes salty.' 'Salty' modifies 'soup,' not the verb 'tastes.'",

    "A predicate nominative follows a linking verb and renames the ___?":
        "Predicate nominatives rename the subject: 'She is a teacher.' 'A teacher' and 'she' refer to the same person. The linking verb 'is' acts as an equals sign.",

    "In 'She is a teacher,' 'a teacher' is the ___?":
        "'A teacher' renames the subject 'she' through the linking verb 'is.' It's a predicate nominative -- a noun that equals the subject on the other side of the linking verb.",

    "In 'The soup tastes salty,' 'salty' is the ___?":
        "'Salty' describes the subject 'soup' through the linking verb 'tastes.' It's a predicate adjective -- an adjective that reaches back through a linking verb to modify the subject.",

    "An absolute phrase modifies the entire ___ rather than a single word?":
        "Absolute phrases are sentence-level modifiers: 'Weather permitting, we'll go to the beach.' The phrase doesn't modify any single word -- it sets a condition for the whole sentence.",

    "Parenthetical expressions are set off from the rest of the sentence by ___?":
        "Parenthetical expressions -- like this one -- can be removed without changing the sentence's core meaning. Commas, dashes, or parentheses all work to set them apart.",

    "When two adjectives equally modify a noun, they are separated by a ___?":
        "Coordinate adjectives get commas between them: 'a bright, cheerful day.' Test: if you can swap their order or insert 'and' between them, they're coordinate and need a comma.",

    "Which is correct for cumulative adjectives?":
        "'A large red barn' uses cumulative adjectives -- they build on each other in a fixed order and don't take commas. You wouldn't say 'a red large barn' -- that sounds wrong.",

    "The rhetorical device of asking a question not meant to be answered is a(n) ___?":
        "Rhetorical questions engage the audience's mind without expecting a reply. 'Can anyone doubt this?' isn't really asking -- it's asserting that no one can doubt it.",

    "A sentence where the main clause comes before subordinate details is ___?":
        "Loose (or cumulative) sentences deliver the main point first, then add modifying details. They feel natural and conversational, mimicking how most people actually think and speak.",

    "A periodic sentence builds toward its main clause at the ___?":
        "Periodic sentences withhold the main idea until the very end, creating suspense. All the dependent clauses and modifiers pile up before the satisfying resolution.",

    "A balanced sentence has two parts that are ___ in structure?":
        "Balanced sentences mirror their halves: 'Easy come, easy go.' The parallel structure creates symmetry and makes the sentence feel satisfying and complete.",

    "Inverted syntax places the ___ before the subject?":
        "Inverted syntax flips normal word order for emphasis: 'Dark was the night' instead of 'The night was dark.' Yoda's speech ('Powerful you have become') is famous inverted syntax.",

    "A conjunctive adverb ('however,' 'therefore') joining two independent clauses requires a ___ before it?":
        "Conjunctive adverbs require a semicolon before them: 'I studied; therefore, I passed.' Using just a comma creates a comma splice -- one of the most common punctuation errors.",

    # === TIER 5 ===
    "A morpheme that changes the grammatical form of a word (e.g., '-ed', '-s') is ___?":
        "Inflectional morphemes modify tense, number, or degree without creating new words: 'walk' + '-ed' = 'walked' (still a form of walk). English has only eight inflectional morphemes.",

    "A morpheme that creates a new word or changes word class (e.g., '-ness', '-ify') is ___?":
        "Derivational morphemes build entirely new words: 'happy' + '-ness' = 'happiness' (adjective to noun). Unlike inflectional morphemes, they can change a word's part of speech.",

    "The smallest unit of sound that distinguishes meaning is a ___?":
        "Changing one phoneme changes meaning: /b/ in 'bat' vs. /p/ in 'pat.' English has about 44 phonemes but only 26 letters -- which is why spelling is such a mess.",

    "The abstract unit representing a word across its forms is a ___?":
        "A lexeme is the abstract 'dictionary entry' behind all a word's forms. 'Run,' 'runs,' 'ran,' and 'running' are all forms of the single lexeme RUN.",

    "The study of how context shapes meaning is ___?":
        "Pragmatics explains why 'Can you pass the salt?' is a request, not a question about your abilities. Context, intention, and social norms shape meaning beyond the literal words.",

    "The study of sentence structure is ___?":
        "Syntax governs how words combine into phrases and sentences. It explains why 'The dog bit the man' and 'The man bit the dog' mean completely different things despite having the same words.",

    "Chomsky's theory of innate language ability is called ___?":
        "Universal Grammar proposes that all humans are born with a built-in language blueprint. It explains why children learn languages so quickly -- they already have the underlying framework.",

    "The underlying logical meaning of a sentence is its ___ structure?":
        "Deep structure captures what a sentence truly means, regardless of how it's worded. 'The dog was chased by the cat' and 'The cat chased the dog' share the same deep structure.",

    "The actual spoken or written form of a sentence is its ___ structure?":
        "Surface structure is what you actually see or hear -- the specific word order and form. Different surface structures can express the same deep structure through transformations.",

    "The Sapir-Whorf hypothesis holds that the language you speak ___ the way you think?":
        "The strong version says language determines thought; the weaker (more accepted) version says it influences it. Speakers of languages with many color terms do perceive color differences more quickly.",

    "The idea that grammar should describe language as used (not prescribe rules) is ___?":
        "Descriptivism treats language like a natural phenomenon to be observed. It doesn't say 'ain't' is wrong -- it notes that millions of speakers use it and describes the patterns.",

    "The idea that grammar should set rules for correct usage is ___?":
        "Prescriptivism establishes standards for 'proper' usage. Style guides and grammar textbooks are prescriptive -- they tell you how language should be used, not just how it is used.",

    "The variety of language used in a specific social situation is a ___?":
        "Register shifts depending on context: you speak differently in a job interview versus a text to a friend. Same person, same dialect, different register for different situations.",

    "A language variety associated with a geographic region or social group is a ___?":
        "Dialects are full language systems, not broken versions of a 'standard.' Every English speaker speaks a dialect -- including those who speak the prestige variety.",

    "The form that is considered the default or baseline in a language is the ___ form?":
        "Unmarked forms are the defaults: 'lion' (unmarked) vs. 'lioness' (marked). The unmarked form requires no extra morphology and is what people reach for first.",

    "The form that deviates from the default (e.g., 'actress' vs 'actor') is the ___ form?":
        "Marked forms carry extra morphology signaling deviation from the default: 'actor' is unmarked; 'actress' adds '-ess' as a gender marker. Languages differ in what they choose to mark.",

    "Using two dialects in different social situations is ___?":
        "Diglossia describes communities using a 'high' variety for formal contexts and a 'low' one for everyday speech. Arabic-speaking countries often have formal Arabic alongside regional colloquial varieties.",

    "The branch of linguistics that studies language sounds as physical phenomena is ___?":
        "Phonetics examines the physical production, transmission, and perception of speech sounds. Phonology, by contrast, studies how sounds function within a particular language's system.",

    "Chomsky's early model of grammar using phrase-structure rules is called ___?":
        "Transformational-generative grammar proposed that surface sentences are derived from deep structures through transformations. It revolutionized linguistics in 1957.",

    "Saussure argued that the connection between a word's sound and its meaning is ___?":
        "There's no natural reason 'dog' means a canine -- other languages use 'chien,' 'Hund,' or 'perro.' The sign is arbitrary, connected only by social convention.",

    "Saussure called the sound image of a word the ___?":
        "The signifier is the word's acoustic form -- the sounds of 'd-o-g.' Together with the signified (the concept of a dog), it forms a complete linguistic sign.",

    "Saussure called the concept a word represents the ___?":
        "The signified is the mental concept evoked by a word. Hearing 'tree' activates your concept of treeness -- not any particular tree, but the abstract idea.",

    "The study of signs and symbols in communication is ___?":
        "Semiotics goes beyond language to study all sign systems: road signs, body language, fashion, film. Charles Peirce and Ferdinand de Saussure independently founded the field.",

    "A language that has developed from a pidgin as a native language is a ___?":
        "Creoles are born when children grow up speaking a pidgin as their first language, expanding it into a full language with complex grammar. Haitian Creole is a well-known example.",

    "A simplified mixed language used for communication between groups is a ___?":
        "Pidgins are improvised communication bridges between groups without a shared language. They have simplified grammar and limited vocabulary, serving as nobody's native language.",

    "How many inflectional morphemes does English have (e.g., -s plural, -s possessive, -ed past, -ing, -en, -er, -est, -s third person)?":
        "English has exactly eight inflectional morphemes -- remarkably few compared to Latin (which had dozens). This is because English lost most of its inflections during the Middle English period.",

    "The inflectional suffix marking third-person singular present is ___?":
        "The '-s' in 'she runs' is the only surviving person/number inflection in English present tense. Old English had different endings for every person -- modern English kept just this one.",

    "The inflectional suffix marking past tense is ___?":
        "'-Ed' is the regular past tense marker: walk/walked, play/played. Irregular verbs like 'go/went' bypass it entirely, but '-ed' covers the vast majority of English verbs.",

    "The inflectional suffix marking progressive aspect is ___?":
        "'-Ing' marks an ongoing action: 'I am running.' Combined with forms of 'be,' it creates all progressive tenses. Without the helper verb, '-ing' forms can serve as nouns (gerunds) or adjectives (participles).",

    "A word's meaning in relation to other words in the same field is its ___ meaning?":
        "Semantic fields group related words: 'red,' 'blue,' and 'green' all belong to the color field. A word's meaning is partly defined by its neighbors -- 'hot' means more because 'cold' exists.",

    "A word's literal dictionary meaning is its ___ meaning?":
        "Denotation is the objective, agreed-upon definition. 'Home' denotes a place where someone lives. Connotation adds emotional weight -- warmth, family, safety -- that goes beyond the definition.",

    "The emotional associations of a word beyond its literal meaning are its ___?":
        "Connotations are the invisible emotional aura around words. 'Thrifty,' 'economical,' and 'cheap' denote the same thing, but their connotations range from positive to negative.",

    "Grice's cooperative principle includes four maxims: quantity, quality, relation, and ___?":
        "Grice's four conversational maxims are: Quantity (enough info), Quality (truthful), Relation (relevant), and Manner (clear and orderly). Violating them creates implicature -- meaning between the lines.",

    "The claim that all human languages share structural universals is ___?":
        "Linguistic universals include features like all languages having nouns and verbs, vowels and consonants, and ways to ask questions. These shared features suggest a common cognitive foundation.",

    "A morpheme with phonological variants depending on context (e.g., 'in-', 'im-', 'ir-') is an ___?":
        "Allomorphs are different surface forms of the same morpheme. The 'not' prefix becomes 'in-' (inactive), 'im-' (impossible), 'il-' (illegal), or 'ir-' (irregular) depending on the following sound.",

    "The subfield studying how social factors influence language use is ___?":
        "Sociolinguistics reveals that language varies by class, gender, ethnicity, and context. William Labov's famous study of New York department stores showed that even 'r' pronunciation signals social class.",

    "The study of language and the brain is ___?":
        "Neurolinguistics maps language onto brain anatomy. Broca's area handles speech production; Wernicke's area handles comprehension. Damage to either produces fascinatingly specific language deficits.",

    "The study of language processing in the mind is ___?":
        "Psycholinguistics investigates how we produce, comprehend, and acquire language in real time. It explains phenomena like 'tip of the tongue' experiences and garden-path sentence misreadings.",

    "The Latin term 'ad verbum' means ___?":
        "'Ad verbum' literally translates to 'word for word,' describing exact translation or quotation. It's the root concept behind 'verbatim,' which entered English from the same Latin source.",

    "The Latin root 'gram' (as in 'grammar') means ___?":
        "The Greek 'gramma' meant 'letter' or 'thing written.' 'Grammar' originally meant the art of letters -- the skill of reading and writing, before it narrowed to mean sentence rules.",

    "The Greek root 'syntax' (syntassein) means ___?":
        "'Syntassein' means 'to arrange together,' perfectly describing what syntax does -- it arranges words into meaningful sentences according to rules of order and hierarchy.",

    "The study of meaning in language is called ___?":
        "Semantics examines what words and sentences mean. It asks questions like: Does 'bachelor' mean the same as 'unmarried man'? How does 'not unhappy' differ from 'happy'?",

    "The study of word formation and structure is called ___?":
        "Morphology dissects words into their smallest meaningful parts. 'Unforgettable' has three morphemes: un- (not) + forget (base) + -able (capable of). Each piece contributes to meaning.",

    "The study of sound systems in language is called ___?":
        "Phonology studies how sounds function within a particular language. English treats 'p' in 'pin' and 'spin' as the same phoneme, even though they're physically different sounds.",

    "The smallest unit of meaning in a word is a ___?":
        "Morphemes are meaning atoms. 'Cats' has two: 'cat' (the animal) + '-s' (plural). Some morphemes are whole words (free); others like '-s' only exist attached to other morphemes (bound).",

    "A variant pronunciation of a phoneme in a specific context is a(n) ___?":
        "Allophones are different physical realizations of the same phoneme. The 'p' in 'pin' (aspirated) and 'spin' (unaspirated) are allophones -- different sounds that English speakers hear as identical.",

    "A morpheme that can stand alone as a word is ___?":
        "Free morphemes are independent words: 'cat,' 'run,' 'happy.' They carry meaning on their own, unlike bound morphemes (-ed, -s, un-) which must attach to something.",

    "A morpheme that cannot stand alone (like '-ness' or 'un-') is ___?":
        "Bound morphemes are parasites of meaning -- they need a host word. Prefixes (un-, re-, pre-) and suffixes (-ness, -ly, -tion) can't stand alone but fundamentally alter their hosts.",

    "The prefix 'un-' in 'unhappy' is a ___ morpheme?":
        "'Un-' creates a new word with an opposite meaning: happy becomes unhappy. Since it changes the word's meaning (not just its grammatical form), it's derivational, not inflectional.",

    "The suffix '-s' in 'cats' is a(n) ___ morpheme?":
        "The plural '-s' changes grammatical number without creating a new word -- 'cats' is still the same word as 'cat,' just plural. That's the hallmark of inflectional morphemes.",

    "Suppletion in morphology refers to an irregular root change, as in ___?":
        "'Go/went' is suppletion -- the past tense comes from a completely different root word (Old English 'wendan'). The forms are so different they couldn't have evolved from the same word.",

    "The rhetorical device of deliberately using more words than necessary is ___?":
        "Pleonasm adds redundant words for emphasis or clarity: 'I saw it with my own eyes' or 'free gift.' Sometimes it's a stylistic choice; sometimes it's just wordy writing.",

    "Aposiopesis is when a speaker deliberately ___?":
        "Aposiopesis creates dramatic tension through silence: 'If you don't stop, I'll...' The unfinished threat often speaks louder than any specific consequence could.",

    "Hyperbaton refers to the unusual ___ of words for rhetorical effect?":
        "Hyperbaton disrupts normal word order for emphasis. Yoda's 'Strong you are' is hyperbaton -- the unusual order makes 'strong' hit harder by putting it first.",

    "Tmesis is the insertion of a word ___ a compound word or phrase?":
        "Tmesis splits a word by inserting another inside it: 'abso-blooming-lutely.' It's common in informal speech and creates emphatic, playful emphasis.",

    "The rhetorical term for a sudden, digressive address to an absent person or abstraction is ___?":
        "Apostrophe (the rhetorical device) turns away from the audience to address an absent entity: 'O Romeo, Romeo, wherefore art thou Romeo?' Juliet speaks to someone who can't hear her.",

    "Paralipsis (or praeteritio) draws attention to something by ___?":
        "Paralipsis is the rhetorical 'I'm not going to mention that.' By explicitly stating what you're skipping, you ensure the audience focuses on exactly that thing.",

    "Hendiadys expresses a single idea through ___ coordinated nouns or adjectives?":
        "Hendiadys uses two words where one modified word would do: 'nice and warm' instead of 'nicely warm,' 'sound and fury' instead of 'furious sound.' Two for the price of one.",

    "The term 'cataphora' means a pronoun that refers to a noun ___?":
        "Cataphora creates forward-looking suspense: 'Before HE arrived, John called ahead.' The pronoun 'he' points forward to 'John,' building anticipation for the noun's reveal.",

    "The term 'anaphora' in grammar (not rhetoric) means a pronoun that refers to a noun ___?":
        "Grammatical anaphora points backward: 'John arrived. HE was tired.' The pronoun 'he' refers back to the already-mentioned 'John.' Don't confuse this with rhetorical anaphora (repetition).",

    "The Latin term 'in medias res' literally means ___?":
        "'In medias res' drops you into the middle of the action. Homer's 'Iliad' doesn't start with the Trojan War's beginning -- it opens in the war's ninth year.",

    "A hapax legomenon is a word that appears ___ in a corpus?":
        "Hapax legomena (Greek for 'said once') are unique occurrences in a text or language corpus. They fascinate scholars because their meaning must be deduced from a single context.",

    "The genitive case primarily indicates ___?":
        "The genitive case shows possession or origin. In English, it survives in possessive forms: 'John's book' (John possesses the book) and 'the city's mayor' (the mayor from/of the city).",

    "The dative case primarily indicates ___?":
        "The dative marks the indirect object -- the recipient of an action. In 'She gave him the book,' 'him' is dative (the receiver). English mostly uses word order and 'to' instead of case endings.",

    "The accusative case primarily indicates the ___?":
        "The accusative case marks the direct object -- what receives the action. In 'She saw him,' 'him' is accusative. English retains accusative only in pronouns (me, him, her, us, them).",

    "The nominative case primarily marks the ___?":
        "Nominative case marks the subject of a sentence. In English, it survives in pronouns: 'I/he/she/we/they' are nominative (subject) forms, versus 'me/him/her/us/them' (object forms).",

    "The vocative case is used for ___?":
        "The vocative case is for calling out to someone: 'Friends, Romans, countrymen, lend me your ears!' English doesn't have special vocative forms, but the function persists in how we use names and titles.",

    "The ablative case in Latin expresses separation, instrument, or ___?":
        "The ablative is Latin's Swiss Army case -- expressing means ('by sword'), manner ('with courage'), or agent ('by the general'). English uses prepositions where Latin used case endings.",

    "Ergative-absolutive languages mark the subject of a transitive verb differently from ___?":
        "In ergative languages (like Basque), the 'doer' of a transitive verb gets special marking, while intransitive subjects pattern with objects. It's the opposite of English's nominative-accusative system.",

    "A cleft sentence ('It was John who left') splits a simple sentence to ___?":
        "Cleft sentences spotlight one element: 'It was JOHN who left' emphasizes the person. The 'it was...who/that' frame puts any element under a grammatical magnifying glass.",

    "A pseudo-cleft sentence begins with a ___?":
        "Pseudo-clefts use a wh-clause to create focus: 'What I need is coffee.' The wh-clause sets up expectations, and the complement delivers the focused element -- like a grammatical drumroll.",

    "Extraposition moves a clause from its normal position to the ___ of the sentence?":
        "Extraposition shifts heavy clauses to the end: 'It is clear that he lied' instead of 'That he lied is clear.' This keeps subjects short and saves complex information for last.",

    "In transformational grammar, deep structure represents ___?":
        "Deep structure captures the core meaning before any surface rearrangement. 'The cat chased the mouse' and 'The mouse was chased by the cat' share the same deep structure.",

    "Chomsky's Government and Binding theory proposes that syntax is governed by universal ___ that vary by language?":
        "Principles are universal rules shared by all languages; parameters are switches set differently for each language. Children 'set the switches' by hearing their native language.",

    "The Sapir-Whorf hypothesis proposes that language ___ thought?":
        "The weak version (linguistic relativity) is widely accepted: language influences how easily we think about certain concepts. The strong version (linguistic determinism) -- that language imprisons thought -- is largely rejected.",

    "Synchronic linguistics studies a language ___?":
        "Synchronic study takes a snapshot of a language at one moment. Saussure championed this approach, arguing you can study chess by analyzing the current board position without knowing every move that led there.",

    "Diachronic linguistics studies a language ___?":
        "Diachronic study tracks how languages change over centuries. It explains why Old English ('Hwael!' = whale) looks like a foreign language and predicts how modern English might evolve.",

    "Ferdinand de Saussure distinguished between 'langue' (the system) and 'parole,' which means ___?":
        "Langue is the shared system of rules in a community's minds; parole is what individuals actually say. Every speech act (parole) draws from the shared system (langue) but never uses all of it.",

    "The term 'idiolect' refers to ___?":
        "Your idiolect is your unique linguistic fingerprint -- the specific words, pronunciations, and grammar patterns that make your speech distinctively yours. No two idiolects are identical.",

    "Code-switching is the practice of alternating between two or more ___ in conversation?":
        "Code-switching is a sign of linguistic sophistication, not confusion. Bilingual speakers seamlessly switch languages mid-conversation, often to express concepts that work better in one language.",

    "A portmanteau word blends the sounds and meanings of ___ words?":
        "Lewis Carroll coined 'portmanteau word' in 1871, comparing it to a suitcase (portmanteau) that opens into two compartments. His example 'slithy' blends 'slimy' and 'lithe.'",

    "The word 'brunch' is an example of a ___?":
        "'Brunch' (breakfast + lunch) is a classic portmanteau -- it packs two words into one bag. Other favorites include 'smog' (smoke + fog) and 'emoticon' (emotion + icon).",

    "A back-formation creates a new word by ___ a suffix?":
        "Back-formation works in reverse: 'editor' existed first, and 'edit' was created by removing '-or.' Similarly, 'televise' was back-formed from 'television.'",

    "'Edit' was formed as a back-formation from ___?":
        "'Editor' came first (from Latin), and English speakers assumed there must be a verb 'edit' behind it. Back-formation creates verbs from nouns by stripping away what looks like a suffix.",

    "An eponym is a word derived from a ___?":
        "Eponyms immortalize real people in everyday language: 'sandwich' (Earl of Sandwich), 'algorithm' (al-Khwarizmi), and 'diesel' (Rudolf Diesel). Fame through vocabulary is a unique kind of legacy.",
}

# ─────────────────────────────────────────────
# COOKING CONTEXTS
# ─────────────────────────────────────────────
COOKING_CONTEXTS = {
    # === TIER 1 ===
    "At what temperature does water boil at sea level?":
        "Water boils at 100 degC (212 degF) at sea level. At higher altitudes, lower air pressure means water boils at lower temperatures -- Denver's water boils around 95 degC, which is why high-altitude recipes need adjustments.",

    "What herb is traditionally used in pesto?":
        "Classic Genovese pesto requires fresh basil, pine nuts, garlic, Parmesan, and olive oil. The word 'pesto' comes from the Italian 'pestare' meaning to pound or crush -- originally made with a mortar and pestle.",

    "What is the main ingredient in hummus?":
        "Chickpeas (garbanzo beans) are the backbone of hummus, blended with tahini, lemon, and garlic. The full Arabic name 'hummus bi tahini' literally means 'chickpeas with tahini.'",

    "What tool is used to measure the temperature of meat?":
        "A meat thermometer takes the guesswork out of doneness. Insert it into the thickest part, avoiding bone (which conducts heat faster and gives a false reading).",

    "What is the primary leavening agent in bread?":
        "Yeast is a living fungus that eats sugar and exhales carbon dioxide, creating the bubbles that make bread rise. A single gram of fresh yeast contains about 10 billion yeast cells.",

    "What kitchen tool is used to finely chop or mince?":
        "The chef's knife is the workhorse of the kitchen. Its curved blade lets you rock it back and forth for rapid mincing -- a technique called the 'rock chop.'",

    "What is the main ingredient in guacamole?":
        "Ripe avocado is the star, mashed with lime, salt, and cilantro. The name comes from the Aztec word 'ahuacamolli' -- 'ahuacatl' (avocado) + 'molli' (sauce).",

    "What does it mean to 'dice' a vegetable?":
        "Dicing means cutting into small uniform cubes. The standard sizes are brunoise (3mm), small dice (6mm), medium dice (12mm), and large dice (20mm).",

    "What is pasta traditionally made from?":
        "Durum wheat semolina gives pasta its characteristic golden color and firm bite. The high protein content creates strong gluten networks that hold up during boiling.",

    "Which of these foods is classified as a dairy product?":
        "Parmesan cheese is made from cow's milk, making it a dairy product. It takes about 16 liters of milk to produce one kilogram of Parmesan, aged for at least 12 months.",

    "What tool do you use to measure liquid ingredients?":
        "Liquid measuring cups have a spout and are read at eye level at the bottom of the meniscus. Dry measuring cups are flat-topped for leveling -- using the wrong type throws off recipes.",

    "What do you call the outer layer of bread that is crispy and brown?":
        "The crust gets its color and crunch from the Maillard reaction -- amino acids and sugars browning at high heat. The interior (called the crumb) stays softer because its moisture prevents temperatures from rising above 100 degC.",

    "What is the main ingredient in tomato sauce?":
        "Tomatoes form the base of the sauce. San Marzano tomatoes from Italy are prized for sauces because they have fewer seeds, thicker walls, and a sweeter, less acidic flavor.",

    "Which cooking method uses hot oil to cook food quickly?":
        "Frying uses hot oil (typically 160-190 degC) to cook food fast while creating a crispy exterior. The high temperature causes moisture to escape as steam, which is what prevents the food from absorbing too much oil.",

    "What do you add to bread dough to make it rise?":
        "Yeast ferments sugars in the flour, producing CO2 gas that gets trapped in the gluten network. This is why kneading matters -- without a strong gluten mesh, the gas would just escape.",

    "What is the name for the fat that comes from a pig?":
        "Lard is rendered pig fat, prized in baking for incredibly flaky pie crusts. It has a higher smoke point than butter and was the most common cooking fat in Western kitchens before vegetable oils took over.",

    "What does 'preheat the oven' mean?":
        "Preheating ensures the oven reaches the target temperature before food goes in. Putting food in a cold oven means it heats unevenly, and baked goods need consistent heat from the start for proper rise and structure.",

    "What kitchen tool is used to beat eggs or cream?":
        "A whisk incorporates air into liquids through its multiple wire loops. Balloon whisks (with wide, round loops) are best for whipping cream; flat whisks excel at making roux and sauces.",

    "What is pasta made from?":
        "The basic recipe is just flour and water, with eggs added in many traditions for richness. Italian law actually requires that dried pasta be made only from durum wheat semolina.",

    "Which herb is most associated with Italian cooking and has a sweet, clove-like aroma?":
        "Basil is the king of Italian herbs. The name comes from Greek 'basilikon' meaning 'royal.' Fresh basil should be torn rather than cut with a knife, which bruises the leaves and turns them black.",

    "What is the purpose of salt in cooking?":
        "Salt enhances flavor by suppressing bitterness and amplifying other tastes. It also affects texture (strengthening gluten in bread, drawing moisture from vegetables) and has been used as a preservative for thousands of years.",

    "What is a 'simmer'?":
        "A simmer means small bubbles gently breaking the surface, around 85-95 degC. It's gentler than a boil and ideal for soups, stews, and sauces where a rolling boil would break food apart.",

    "Which spice is bright yellow and used in curry?":
        "Turmeric gets its vivid color from curcumin, a compound studied for anti-inflammatory properties. It's been used in Indian cooking for over 4,000 years and gives American yellow mustard its color too.",

    "What is the name for the process of browning meat or vegetables in oil?":
        "Sauteing comes from the French 'sauter' meaning 'to jump' -- food should be hot enough that it sizzles and jumps in the pan. The key is not overcrowding, which drops the temperature and causes steaming instead.",

    "What is 'flour' made from?":
        "Flour is grain ground to a fine powder, usually from wheat. Different grinds and wheat varieties produce different flours -- bread flour has more protein for chewy loaves, cake flour has less for tender crumbs.",

    "What do eggs provide in baking?":
        "Eggs are triple-threat ingredients: whites provide structure (protein coagulation), yolks add moisture and richness (fat and lecithin), and the whole egg binds ingredients together.",

    "What is the purpose of kneading bread dough?":
        "Kneading aligns the glutenin and gliadin proteins in flour into an elastic gluten network. This mesh traps CO2 from yeast, creating the airy structure of bread.",

    "Which of these is used to sweeten food?":
        "Honey is nature's sweetener, made by bees from flower nectar. It's about 25% sweeter than table sugar due to its high fructose content, meaning you can use less.",

    "What is a 'stock' in cooking?":
        "Stock is a flavorful liquid foundation simmered from bones, vegetables, and aromatics. The long cooking time extracts collagen from bones, which converts to gelatin and gives stock its body.",

    "What does 'al dente' mean for pasta?":
        "Al dente (Italian for 'to the tooth') means pasta is cooked through but still has a slight firmness when bitten. It tastes better and has a lower glycemic index than overcooked pasta.",

    "What is the most common fat used in baking cakes?":
        "Butter contributes flavor, tenderness, and moisture to cakes. When creamed with sugar, it traps air bubbles that expand during baking, helping the cake rise.",

    "What kitchen tool do you use to drain pasta?":
        "A colander's holes let water drain while keeping pasta safely inside. Pro tip: save a cup of starchy pasta water before draining -- it's liquid gold for thickening and binding sauces.",

    "What is the main flavor of vinegar?":
        "Vinegar's sourness comes from acetic acid, produced by bacteria fermenting alcohol. The name literally comes from French 'vin aigre' meaning 'sour wine.'",

    "What does 'bake' mean?":
        "Baking surrounds food with dry heat in an enclosed oven. Unlike roasting (which also uses dry oven heat), baking typically refers to bread, pastries, and casseroles rather than meat.",

    "What is the name for a sauce made from egg yolks, lemon juice, and butter?":
        "Hollandaise is one of the five French mother sauces, and it's an emulsion -- the lecithin in egg yolks holds the butter and lemon juice together. Gentle heat is crucial; too hot and the eggs scramble.",

    "Which vegetable is used to make traditional French onion soup?":
        "Onions -- lots of them, slowly caramelized until deeply golden. The long, slow cooking breaks down the onions' sugars through the Maillard reaction, transforming sharp raw onion into sweet, complex flavor.",

    "What does 'grate' mean in cooking?":
        "Grating rubs food against sharp holes to produce fine shreds or powder. A Microplane grater creates feathery wisps of cheese or zest, while a box grater offers multiple textures.",

    "What is 'batter' in cooking?":
        "Batter is a liquid mixture thin enough to pour, unlike dough which is thick enough to knead. The key difference is the ratio of liquid to flour -- more liquid makes batter, less makes dough.",

    "Which food is made by curdling and pressing milk?":
        "Cheese-making separates milk into curds (solid protein and fat) and whey (liquid). An acid or rennet triggers the curdling, and pressing removes moisture to create the final texture.",

    "What is a 'marinade'?":
        "Marinades flavor food from the outside in, but they only penetrate about 1-2mm deep. The real magic is surface flavor -- think of them as a coating that transforms when cooked.",

    "Which fruit is used to make guacamole?":
        "Avocado is technically a large berry with a single seed. The Hass variety (dark, bumpy skin) is the most popular for guacamole because of its creamy texture and rich flavor.",

    "What kind of knife has a curved blade good for chopping?":
        "A chef's knife (typically 20cm/8 inches) has a curved blade that lets you rock it for fast chopping. It's the most versatile knife in any kitchen -- many professional chefs do 90% of their cutting with one.",

    "What is the name for the thin outer covering of fruits like lemons?":
        "Zest is the colorful outer layer packed with aromatic citrus oils. Avoid the white pith beneath it, which is bitter. A Microplane grater removes zest without touching the pith.",

    "Which cooking method keeps the most nutrients in vegetables?":
        "Steaming preserves water-soluble vitamins (like C and B) because the vegetables never touch the water. Boiling leaches these vitamins into the cooking liquid.",

    "What is a 'stock cube'?":
        "Stock cubes are dehydrated, concentrated stock compressed into small blocks. They dissolve in hot water for a quick broth. While convenient, they're much saltier and less nuanced than homemade stock.",

    "What is the white part of an egg called?":
        "Albumen (egg white) is almost pure protein and water. When heated, the proteins unfold and bond together, turning from clear liquid to opaque white -- a process called denaturation.",

    "What is used to glaze pastries to give them a golden color?":
        "Egg wash creates a golden sheen through the Maillard reaction -- proteins and sugars in the egg brown under heat. Whole egg gives a balanced golden color; yolk alone gives a deeper gold.",

    "Which cooking method wraps food tightly in foil or parchment to cook in its own steam?":
        "En papillote (French for 'in parchment') creates a sealed parcel that steams food in its own juices. The dramatic puff of aromatic steam when opened at the table is part of the experience.",

    "What is a 'pinch' of spice as a measurement?":
        "A pinch is roughly 1/16 of a teaspoon -- whatever you can grab between thumb and two fingers. It's the oldest and most intuitive measurement, used long before standardized spoons.",

    "What is the difference between 'baking soda' and 'baking powder'?":
        "Baking soda (pure sodium bicarbonate) needs an acid partner (buttermilk, yogurt, lemon) to produce CO2. Baking powder contains its own acid, so it works with any liquid. Using the wrong one can leave a metallic taste.",

    "What is 'whipped cream' made from?":
        "Heavy cream (35%+ fat) whipped with air creates a stable foam. The fat globules partially coalesce around air bubbles, trapping them. Too little fat and it won't hold; too much whipping and you get butter.",

    "What is the name for a very thin crepe-like pancake from France?":
        "Crepes are paper-thin pancakes made from a simple batter of flour, eggs, milk, and butter. In Brittany, savory galettes are made with buckwheat flour while sweet crepes use white flour.",

    "What type of sugar is used to make caramel?":
        "White granulated sugar is the standard for caramel because its neutral flavor lets the caramelization shine. When heated to 160-180 degC, sugar molecules break down and recombine into hundreds of new flavor compounds.",

    "What is 'buttermilk' used for in baking?":
        "Buttermilk's acidity activates baking soda, creating CO2 for lift. It also tenderizes gluten and adds a subtle tang. In a pinch, add a tablespoon of lemon juice to regular milk as a substitute.",

    "What is a 'pinbone' in a fish fillet?":
        "Pin bones are small, flexible bones that run along the center of many fish fillets. They're removed by feeling for them with your fingers and pulling each one out at an angle with tweezers or pliers.",

    "What does 'rest' mean when applied to meat after cooking?":
        "Resting allows the muscle fibers, which contracted during cooking, to relax and reabsorb their juices. Cut too soon and those juices pour out onto your plate instead of staying in the meat.",

    "What is the main purpose of resting bread dough after kneading?":
        "During resting (fermentation), yeast produces CO2 that inflates the gluten network, while the gluten itself relaxes. This dual process creates both rise and easier handling for shaping.",

    "What is a 'brine'?":
        "Brining uses osmosis to push salt and water into meat cells, seasoning them deeply and improving moisture retention during cooking. Even a short 30-minute brine noticeably improves chicken breast.",

    "What is 'scoring' food before cooking?":
        "Scoring makes shallow cuts that help heat penetrate thick proteins, allow marinades to reach deeper, and prevent items like sausages or bread from splitting unpredictably during cooking.",

    "What does 'mince' mean when preparing garlic?":
        "Mincing garlic into tiny pieces maximizes the surface area that releases allicin -- the compound responsible for garlic's pungent flavor. The finer the mince, the more intense the garlic taste.",

    "Which country is the origin of sushi?":
        "Japan perfected sushi as we know it, though the concept of fermenting fish with rice originated in Southeast Asia. Modern nigiri sushi was invented in Tokyo in the 1820s as a fast food.",

    "What is a 'saucepan' used for?":
        "Saucepans have tall, straight sides that reduce evaporation -- ideal for liquids. They're distinct from saute pans (wider, shorter sides for browning) and skillets (sloped sides for tossing).",

    "What do you call the top thin layer of oil floating on a soup or stock?":
        "Fat rises to the surface because it's less dense than water. Skimming it off produces a cleaner, lighter stock. Chilling stock overnight solidifies the fat into a solid disc that lifts off easily.",

    "What is 'flour' made from?":
        "Flour is grain ground to a fine powder, usually from wheat. Different grinds and wheat varieties produce different flours -- bread flour has more protein for chewy loaves, cake flour has less for tender crumbs.",

    "What does it mean to 'fold' ingredients in baking?":
        "Folding gently combines a light mixture (whipped eggs) with a heavier one (batter) using a spatula in a sweeping under-and-over motion. Vigorous stirring would deflate all those precious air bubbles.",

    "What does 'season' a cast iron pan mean?":
        "Seasoning polymerizes oil into a hard, slick coating through heat. Each layer builds on the last, creating a naturally non-stick surface. Soap and scrubbing won't ruin modern seasoning -- that's an old myth.",

    "What is a 'clove' of garlic?":
        "A garlic bulb contains 10-20 individual cloves, each wrapped in its own papery skin. One clove typically yields about half a teaspoon when minced. Recipes almost always mean individual cloves, not whole bulbs!",

    "What is the purpose of letting wine breathe before serving?":
        "Exposing wine to air softens harsh tannins through oxidation and releases volatile aroma compounds. Young, tannic red wines benefit most -- decanting for 30-60 minutes can dramatically smooth the flavor.",

    "What is 'double cream' higher in than regular cream?":
        "Double cream has about 48% fat compared to heavy cream's 35%. The extra fat makes it richer, thicker, and less likely to curdle when added to hot sauces.",

    "What does it mean to 'strain' a sauce?":
        "Straining through a fine mesh sieve catches lumps, seeds, and solids, producing a silky smooth sauce. For the finest results, professional kitchens use a chinois (conical sieve) and push the liquid through with a ladle.",

    "What is 'parboiling'?":
        "Parboiling partially cooks food in boiling water before finishing with another method. Parboiling potatoes before roasting gives you a fluffy interior with a crispy exterior -- the best of both worlds.",

    "Which type of pasta is shaped like small butterflies or bow ties?":
        "Farfalle means 'butterflies' in Italian. Their pinched center stays slightly thicker than the ruffled wings, giving each piece two textures in one bite.",

    "What is a 'stock cube'?":
        "Stock cubes are dehydrated, concentrated stock compressed into small blocks. They dissolve in hot water for a quick broth. While convenient, they're much saltier and less nuanced than homemade stock.",

    # === TIER 2 ===
    "Why is wheat the primary grain for bread-making rather than rice or corn?":
        "Only wheat flour contains significant amounts of glutenin and gliadin, which hydrate and link into gluten -- an elastic protein network that traps CO2 from yeast. No gluten, no rise, no fluffy bread.",

    "What is the standard safe internal temperature for cooked chicken (Celsius)?":
        "At 74 degC (165 degF), Salmonella and other pathogens are instantly destroyed. Lower temperatures can also be safe if held longer (sous vide uses this principle), but 74 degC is the instant-kill threshold.",

    "Why is olive oil not ideal for high-heat frying?":
        "Extra virgin olive oil smokes around 190 degC, lower than refined oils like avocado (270 degC). Past its smoke point, oil breaks down into acrid compounds. Save EVOO for finishing and use refined oils for high-heat work.",

    "What cooking technique involves briefly boiling food then plunging into ice water?":
        "Blanching's thermal shock deactivates enzymes that would otherwise destroy color, texture, and nutrients. It's essential before freezing vegetables and for easy tomato peeling.",

    "What does 'al dente' mean?":
        "Italian for 'to the tooth,' al dente pasta has a slight resistance when bitten. It has a lower glycemic index than soft-cooked pasta because the compact starch is digested more slowly.",

    "What does the Maillard reaction cause in cooking?":
        "The Maillard reaction between amino acids and reducing sugars creates hundreds of new flavor and color compounds. It's responsible for the flavors of seared steak, toasted bread, roasted coffee, and dark beer.",

    "What is umami often described as?":
        "Umami is the fifth basic taste, detected by receptors that respond to glutamate. Discovered by Japanese chemist Kikunae Ikeda in 1908, it's the deep savoriness in aged Parmesan, soy sauce, and mushrooms.",

    "Why does blanching vegetables in boiling water then plunging into ice water preserve their bright color?":
        "The brief heat burst deactivates polyphenol oxidase and other enzymes that break down chlorophyll. The ice bath halts the cooking immediately, locking in that vibrant green before heat can dull it.",

    "What does the Maillard reaction require that caramelization does not?":
        "Maillard needs both amino acids (from proteins) and reducing sugars, which is why it happens on meat, bread, and cheese. Caramelization is sugar-only -- pure thermal decomposition without any protein involvement.",

    "What is 'braising'?":
        "Braising combines two methods: first a high-heat sear for flavor (Maillard reaction), then slow, moist cooking in a covered pot. This dual approach is perfect for tough, collagen-rich cuts.",

    "What is the approximate ratio of flour to fat in a standard shortcrust pastry?":
        "The 2:1 flour-to-fat ratio creates 'short' (crumbly, tender) pastry. The fat coats flour particles, preventing long gluten strands from forming -- more fat means shorter, more tender pastry.",

    "Why does braising tough cuts of meat produce tender results?":
        "Collagen in connective tissue needs sustained moist heat (around 70-80 degC over hours) to unravel and convert into gelatin. This is why braised brisket practically melts while a quick-seared one would be tough.",

    "What does 'reduce' mean in cooking?":
        "Reducing concentrates flavors by evaporating water. A sauce reduced by half has twice the flavor intensity. The French term 'reduction' is the foundation of classical sauce-making.",

    "What is a 'julienne' cut?":
        "Julienne produces matchstick strips about 3mm x 3mm x 6cm. Named after a 17th-century French chef, it's the basis for other cuts -- stack julienne strips and cross-cut for brunoise (tiny cubes).",

    "What country does 'kimchi' come from?":
        "Kimchi is Korea's national dish -- lacto-fermented vegetables (usually napa cabbage) with chili, garlic, and ginger. There are over 200 varieties, and the average Korean eats about 40 pounds per year.",

    "What kitchen technique is 'folding'?":
        "Folding preserves air in delicate mixtures. Use a spatula to cut down through the center, sweep along the bottom, and fold back over the top. Rotate the bowl and repeat -- gentle is the key word.",

    "What is the main ingredient in a traditional French onion soup?":
        "Caramelized onions take 45-60 minutes of slow cooking to develop their deep sweetness. The Maillard reaction and caramelization transform sharp, pungent raw onions into a rich, sweet base.",

    "What grain is risotto made from?":
        "Arborio rice has a high amylopectin starch content that releases into the cooking liquid, creating risotto's signature creaminess. The gradual addition of hot stock and constant stirring coaxes out the starch.",

    "Why does sourdough bread rise without commercial yeast?":
        "A sourdough starter is a living ecosystem of wild yeast and lactic acid bacteria. The wild yeast produces CO2 for leavening, while the bacteria create the tangy acids that give sourdough its distinctive flavor.",

    "What type of cuisine prominently uses 'mole' sauce?":
        "Mexican mole is a complex sauce that can contain 20+ ingredients including chilies, chocolate, spices, and nuts. Mole poblano is the most famous variety, and each region has its own signature version.",

    "What is the key ingredient that makes bread rise when using sourdough?":
        "Wild yeast and lactic acid bacteria in the starter work as a team. The yeast provides leavening (CO2 gas), while the bacteria produce acids that develop flavor and strengthen the gluten network.",

    "Why does butter burn at lower temperatures than refined vegetable oils?":
        "Butter's milk solids (proteins and sugars) char around 150 degC, well below refined oil smoke points. Clarifying butter by removing these solids raises its smoke point to about 250 degC.",

    "What does it mean to 'fold' ingredients in baking?":
        "Folding preserves air that you've worked hard to whip in. The gentle under-and-over motion incorporates ingredients without deflating the mixture -- critical for souffles, meringues, and chiffon cakes.",

    "Why does kneading develop gluten in bread dough?":
        "The physical stretching and folding aligns glutenin and gliadin proteins, then cross-links them into elastic gluten sheets. Think of it like untangling and then braiding ropes into a strong net.",

    "What is a 'roux'?":
        "A roux is the thickening backbone of many sauces and soups. Cooking the flour in fat eliminates its raw taste. White roux cooks briefly for maximum thickening; dark roux cooks longer for deeper flavor but less thickening power.",

    "What does 'caramelize' mean in cooking?":
        "Caramelization breaks sugar molecules apart at 160+ degC, then reassembles them into hundreds of new compounds producing butterscotch, nutty, and rich flavors. It's pure chemistry transforming simple sweetness into complexity.",

    "What is 'blanching'?":
        "The brief boiling followed by ice-water shock serves multiple purposes: it loosens tomato skins for easy peeling, sets the bright color of green vegetables, and deactivates enzymes before freezing.",

    "Why does caramelization require higher temperatures than the Maillard reaction?":
        "The Maillard reaction begins around 140 degC because amino acids lower the energy barrier for sugar reactions. Caramelization, with no protein assistance, needs 160 degC+ to break sugar bonds through heat alone.",

    "What type of heat cooks food from the inside in a microwave?":
        "Microwaves excite water molecules, causing them to vibrate and generate heat throughout the food. This is why dry foods don't heat well in a microwave, and why food with uneven moisture heats unevenly.",

    "What is 'searing'?":
        "Searing at high heat (over 200 degC) triggers rapid Maillard reactions, creating a flavorful brown crust in minutes. Despite the popular myth, searing does NOT 'seal in juices' -- it creates flavor.",

    "What does 'deglaze' mean in cooking?":
        "Adding liquid to a screaming-hot pan dissolves the fond (browned bits) through a combination of heat and dissolution. Wine, stock, or even water captures those concentrated flavors for an instant pan sauce.",

    "What is 'reduction' in cooking?":
        "Every cup of liquid you boil away concentrates the remaining flavors. A sauce reduced by half isn't just thicker -- it's twice as flavorful. This is why restaurant sauces taste so much more intense than home versions.",

    "Which cooking fat has the highest smoke point?":
        "Refined avocado oil can handle about 270 degC (520 degF), making it the champion for high-heat cooking. Butter bottoms out around 150 degC, and extra virgin olive oil sits around 190 degC.",

    "What does 'julienne' mean in knife skills?":
        "Julienne produces uniform matchstick strips (3mm x 3mm x 6cm). Uniformity isn't just about looks -- equally sized pieces cook at the same rate, preventing some from burning while others stay raw.",

    "What is a 'coulis'?":
        "A coulis is a smooth, vibrant sauce made by pureeing raw or cooked fruit or vegetables and straining out seeds and fiber. Raspberry coulis drizzled on a plate is both a sauce and edible art.",

    "What is the cooking purpose of egg wash on pastry before baking?":
        "Egg proteins and sugars undergo the Maillard reaction in oven heat, creating a beautiful golden-brown gloss. Yolk-only wash gives deeper color; white-only gives shine without much color.",

    "What does 'render' mean in cooking?":
        "Rendering melts fat out of meat over low heat. Think of it as gently persuading the fat to liquefy and leave. Bacon is the most familiar example -- start it in a cold pan and let the fat slowly render out.",

    "What does 'proof' mean for bread dough?":
        "Proofing is the final rise after shaping. The yeast produces its last burst of CO2, and the gluten network expands to its limit. Under-proofed bread is dense; over-proofed bread collapses.",

    "What is a 'court bouillon'?":
        "Court bouillon ('short broth') is a quick poaching liquid for delicate fish. It's typically water, white wine, vegetables, and herbs simmered for just 20 minutes -- long enough to extract flavor without turning murky.",

    "What is 'en papillote'?":
        "Cooking en papillote creates a sealed steam chamber that gently cooks food in its own moisture. The parchment puffs dramatically in the oven, and cutting it open at the table releases a fragrant burst of steam.",

    "What is 'ceviche'?":
        "Citric acid denatures fish proteins the same way heat does, turning the flesh opaque and firm. It's not technically 'raw' even though no heat is used -- the acid does the cooking chemically.",

    "What is a 'gastrique'?":
        "A gastrique bridges sweet and sour -- caramelized sugar provides depth while vinegar adds brightness. It's the secret behind classic duck a l'orange and other French dishes that balance richness with acidity.",

    "What is 'spatchcocking' a bird?":
        "Removing the backbone and flattening the bird dramatically increases the surface area exposed to heat. A spatchcocked chicken roasts in about 45 minutes instead of 90, with crispier skin and juicier meat.",

    "What is 'basting'?":
        "Spooning pan drippings over roasting meat adds flavor and keeps the surface moist. However, each time you open the oven to baste, you lose heat -- so baste quickly and confidently.",

    "Why does salt suppress bitterness and enhance perceived sweetness in food?":
        "Sodium ions interact directly with taste receptors, blocking bitter signals while amplifying sweet and umami perception. This is why a pinch of salt in chocolate chip cookies makes them taste sweeter.",

    "What is 'ganache' in pastry?":
        "Ganache is simply chocolate and hot cream emulsified together. The ratio determines its use: equal parts for frosting, more cream for pouring glaze, more chocolate for truffle centers.",

    "What does 'poach' mean in cooking?":
        "Poaching uses liquid at 70-85 degC -- below a simmer, with barely a bubble. This gentle heat is perfect for delicate foods like eggs, fish, and fruit that would fall apart at higher temperatures.",

    "What is a 'bain-marie' (water bath)?":
        "The surrounding water can never exceed 100 degC, creating a gentle, even heat buffer. This protects custards from curdling, chocolate from seizing, and cheesecakes from cracking.",

    "What is 'fondant' used for?":
        "Fondant is a sugar paste rolled flat and draped over cakes for a smooth, pristine finish. While beautiful, many bakers prefer buttercream for taste -- fondant is more about visual perfection.",

    "What is 'larding' a roast?":
        "Larding inserts strips of fat into lean meat using a larding needle. Before modern breeding produced marbled meat, larding was essential for making lean game and beef moist and flavorful.",

    "What is 'mirepoix'?":
        "The classic French flavor base of onion, carrot, and celery (2:1:1 ratio) appears in stocks, soups, and braises worldwide. The Italian version (soffritto) and Cajun version (holy trinity with bell pepper) are close cousins.",

    "What is a 'bouquet garni'?":
        "Tying herbs in a bundle (or cheesecloth sachet) makes them easy to fish out after cooking. The classic combination is thyme, bay leaf, and parsley stems -- robust herbs that hold up to long simmering.",

    "What is 'creme fraiche'?":
        "Creme fraiche is cream cultured with bacteria, similar to sour cream but richer (about 30% fat). Its higher fat content means it won't curdle when stirred into hot sauces -- a major advantage over sour cream.",

    "What is the main difference between 'roasting' and 'baking'?":
        "Both use the same dry oven heat. The distinction is mostly tradition: we 'roast' a chicken or vegetables (foods with existing structure) and 'bake' bread, cakes, or casseroles (which transform during cooking).",

    "What is 'mise en place'?":
        "French for 'everything in its place,' mise en place means measuring, cutting, and organizing all ingredients before cooking begins. Professional chefs consider it non-negotiable -- it prevents mistakes and reduces stress.",

    "What is the 'Maillard reaction'?":
        "Named after French chemist Louis-Camille Maillard (1912), this reaction between amino acids and sugars creates the flavors we associate with seared meat, toasted bread, and roasted coffee. It's arguably the most important flavor reaction in cooking.",

    "What is 'emulsification' in cooking?":
        "Oil and water naturally separate, but emulsifiers (like lecithin in egg yolks or mustard) create a bridge. Each emulsifier molecule has one end that loves water and another that loves oil, holding them together.",

    "What is a 'liaison' in French cooking?":
        "A liaison of egg yolks and cream adds silky richness to soups and sauces. It must be added off the heat or tempered carefully -- otherwise the yolks will scramble instead of thickening smoothly.",

    "What is 'gelatin' derived from in cooking?":
        "Gelatin comes from collagen -- the protein in animal connective tissue. When bones and joints simmer for hours, their collagen dissolves into the stock. That's why homemade stock jiggles when cold.",

    "What is the difference between 'stock' and 'broth'?":
        "Stock relies on bones for gelatin body, while broth uses meat for flavor. Stock sets like Jell-O when cold (from dissolved collagen); broth stays liquid. Stock is the professional chef's foundation.",

    "What is a 'beurre blanc'?":
        "This classic Loire Valley sauce emulsifies cold butter into a wine-shallot reduction. The key is adding butter piece by piece over gentle heat -- too hot and the emulsion breaks into an oily mess.",

    "What is 'curing' food?":
        "Curing preserves food by reducing water activity below levels that bacteria need to thrive. Salt draws out moisture through osmosis, while smoke adds antimicrobial compounds and flavor.",

    "Why does the Maillard reaction not occur when boiling meat in water?":
        "Water can never exceed 100 degC at normal pressure, but the Maillard reaction needs at least 140 degC. This is why boiled meat is grey and bland, while seared meat is brown and flavorful -- it's all about surface temperature.",

    "What is 'ghee'?":
        "Ghee is butter taken one step beyond clarification -- the milk solids are allowed to brown slightly before straining, adding a nutty flavor. It's a staple of Indian cooking with a smoke point around 250 degC.",

    "What is 'tempering' an egg in cooking?":
        "Gradually whisking hot liquid into eggs raises their temperature slowly. Dumping eggs into hot liquid would instantly coagulate (scramble) them. Tempering is basically giving eggs a warm-up before the heat.",

    "What is a 'fond' in cooking?":
        "Fond means 'bottom' or 'base' in French -- it's the foundation of flavor stuck to your pan. Those browned bits are packed with Maillard reaction products. Deglazing captures them for sauces.",

    "What is 'buttercream' made from?":
        "The simplest American buttercream is just butter beaten with powdered sugar. Swiss and Italian meringue buttercreams add whipped egg whites for a lighter, silkier texture that's less sweet.",

    "What is 'en croute' in French cooking?":
        "En croute ('in a crust') wraps food in pastry before baking. Beef Wellington -- fillet wrapped in mushroom duxelles and puff pastry -- is the most famous example of this elegant technique.",

    "What is 'deglazing' primarily used to make?":
        "Pan sauces are built on fond -- those caramelized bits contain concentrated Maillard flavor. A splash of wine or stock dissolves them in seconds, creating the base of a sauce that tastes like you cooked for hours.",

    "What does 'proof' mean for bread dough?":
        "Proofing is the final rise after shaping. The yeast produces its last burst of CO2, and the gluten network expands to its limit. Under-proofed bread is dense; over-proofed bread collapses.",

    "What are the five French mother sauces? One is Bechamel. Name another.":
        "The five mothers are Bechamel (milk-based), Veloute (light stock), Espagnole (brown stock), Hollandaise (butter-egg emulsion), and Tomato. Every French sauce descends from one of these five foundations.",

    "What does 'mise en place' mean?":
        "This principle is so fundamental that culinary schools test students on it before they ever turn on a stove. Having everything prepped and organized means you can focus entirely on cooking when the heat is on.",

    "What is a roux?":
        "Equal parts fat and flour, cooked to different stages: white roux (1-2 min) for bechamel, blond roux (3-5 min) for veloute, brown roux (15+ min) for gumbo. Longer cooking develops nuttier flavor but reduces thickening power.",

    "What is tempering chocolate?":
        "Tempering creates stable Form V cocoa butter crystals through precise heating and cooling (typically melt to 50 degC, cool to 27 degC, reheat to 31 degC). The result is chocolate that snaps cleanly, has a glossy sheen, and melts smoothly.",

    "What is emulsification in cooking?":
        "An emulsion suspends tiny droplets of one liquid within another that wouldn't normally mix. Mayonnaise is oil droplets suspended in water (from lemon juice), held stable by lecithin from egg yolks.",

    "What is the French term for cooking vegetables until soft and translucent without browning?":
        "Sweating uses low heat with a lid to draw moisture from vegetables without triggering browning reactions. The vegetables 'sweat' out their liquid, becoming soft and sweet while staying pale.",

    "Which spice comes from the stigma of the Crocus sativus flower?":
        "Saffron is the world's most expensive spice by weight because each flower produces only three tiny stigmas, hand-picked during a brief two-week harvest. It takes about 75,000 flowers to produce one pound.",

    "What is 'deglazing' a pan?":
        "When liquid hits a scorching-hot pan, it flash-boils and dissolves the fond (browned bits) in seconds. That concentrated flavor is the secret behind restaurant-quality pan sauces.",

    "What is the fermentation process that makes yogurt?":
        "Lactic acid bacteria (Lactobacillus and Streptococcus) convert milk sugar (lactose) into lactic acid, which thickens the milk and creates yogurt's characteristic tang. The acid also acts as a natural preservative.",

    "What is 'clarified butter'?":
        "Removing milk solids and water from butter yields pure butterfat with a much higher smoke point (around 250 degC vs. 150 degC). This makes it perfect for high-heat searing and sauteing.",

    "What spice originates from the Moluccas (Spice Islands) and is the dried seed of Myristica fragrans?":
        "Nutmeg and its lacy outer covering (mace) come from the same fruit. The Spice Islands' nutmeg monopoly was so valuable that the Dutch traded Manhattan to England for control of a nutmeg-producing island.",

    "What is 'chiffonade'?":
        "Stack the leaves, roll them into a tight cigar, and slice across to produce delicate ribbons. This technique works beautifully with basil, mint, and spinach for elegant garnishes.",

    "What are the five French mother sauces? One is Espagnole. What is it based on?":
        "Espagnole is built on brown veal or beef stock, thickened with brown roux and tomato puree. When combined with additional brown stock and reduced by half, it becomes demi-glace -- a cornerstone of French cuisine.",

    "What is miso made from?":
        "Miso is soybeans fermented with koji mold (Aspergillus oryzae) and salt. White miso ferments for weeks (mild, sweet); red miso for months or years (intense, complex). It's a umami powerhouse.",

    "What does 'en papillote' mean?":
        "The sealed parchment packet traps steam, gently cooking the food in its own juices. When the packet puffs up in the oven and you cut it open at the table, the aromatic steam is part of the dining experience.",

    "What acid is responsible for the sour taste in sourdough bread?":
        "The bacteria in sourdough starter produce both lactic acid (mild, yogurty tang) and acetic acid (sharp, vinegary bite). Warmer fermentation favors lactic acid; cooler favors acetic -- giving bakers control over flavor.",

    "What temperature is used for sous vide cooking of chicken breast?":
        "At 63 degC, chicken breast remains juicy and tender because the proteins don't fully contract. Traditional cooking at 74 degC is safe because it kills bacteria instantly; at 63 degC, holding for 75+ minutes achieves the same safety.",

    "What cooking method uses vacuum-sealed bags in a water bath?":
        "Sous vide ('under vacuum') gives unprecedented temperature control -- the water bath never exceeds the target temp. This means a steak cooked to 55 degC is 55 degC edge-to-edge, with no gray band.",

    "What is the role of the 'garde manger' in a professional kitchen?":
        "The garde manger station handles all cold preparations: salads, cold appetizers, charcuterie, and terrines. In the classical brigade system, it's one of the most versatile and demanding positions.",

    "In the classical brigade system, what is the 'saucier' responsible for?":
        "The saucier is traditionally the most prestigious position after the head chef. Sauces are considered the ultimate test of culinary skill -- they require mastering stocks, reductions, emulsions, and flavor balance.",

    "What is the purpose of 'tempering' eggs when adding them to a hot liquid?":
        "Eggs coagulate (scramble) at around 62-70 degC. Gradually raising their temperature by whisking in small amounts of hot liquid prevents the shock of sudden heat that would turn them into scrambled bits.",

    "What is 'nappe' consistency in a sauce?":
        "Run your finger across the coated spoon -- if the line holds without the sauce running back together, you've hit nappe. It's the classic test for custards, creme anglaise, and many cream sauces.",

    "What does 'blooming' gelatin mean?":
        "Soaking gelatin in cold water hydrates and softens it, ensuring it dissolves evenly when heated. Skipping this step results in lumpy, unevenly set gels -- a frustrating mistake that's easily avoided.",

    "What is 'transglutaminase' sometimes called in professional cooking?":
        "Meat glue bonds proteins together so seamlessly that you can combine scraps into a single, uniform piece or create impossible combinations like shrimp-wrapped-in-chicken. It's an enzyme, not a chemical additive.",

    "What role does a 'poissonnier' play in a professional kitchen brigade?":
        "The poissonnier (from French 'poisson' = fish) is dedicated to fish and seafood preparation. This specialist position reflects how delicate and skill-intensive seafood cooking is compared to meat.",

    "What is 'carryover cooking'?":
        "Residual heat in the outer layers continues migrating inward after food leaves the heat source. A roast can rise 5-10 degC during resting, so pull it off heat before your target temperature.",

    "What is the 'Maillard reaction' temperature threshold approximately?":
        "Below 140 degC, the reaction barely happens. This explains why boiled food (max 100 degC) never browns, while grilled, roasted, or seared food (well above 140 degC) develops rich brown crusts.",

    "What is 'fond' in French cooking terminology?":
        "Those caramelized bits stuck to your pan are concentrated flavor -- Maillard reaction products and caramelized sugars. The word 'fond' means 'bottom' or 'base' in French, because great sauces start here.",

    "What is the purpose of 'resting' meat after cooking?":
        "During cooking, heat drives moisture toward the center. Resting allows the temperature to equalize and fibers to relax, letting juice redistribute throughout. Cut too soon and you'll lose up to 40% of the juices.",

    "Which chemical reaction causes bread crust to brown?":
        "The Maillard reaction between amino acids and sugars in the dough surface creates the brown crust and its complex flavor. Steam in the early baking phase keeps the crust soft long enough for maximum oven spring before browning begins.",

    "What compound in chili peppers causes the burning sensation?":
        "Capsaicin binds to TRPV1 pain receptors, tricking your brain into feeling heat. It's fat-soluble (drink milk, not water, to cool the burn) and concentrated in the white pith, not the seeds as commonly believed.",

    "What is 'agar-agar' derived from?":
        "Extracted from red algae, agar sets firmer than gelatin, gels at a higher temperature, and is vegetarian. Unlike gelatin, agar gels don't melt in your mouth -- they break cleanly, giving a different textural experience.",

    "What is the historical origin of 'haute cuisine'?":
        "French haute cuisine emerged in the 17th-century royal courts, formalized by chefs like La Varenne and later Careme and Escoffier. It established the mother sauces, brigade system, and plating techniques still used today.",

    "What is 'transglutaminase' and what does it do chemically?":
        "This enzyme catalyzes covalent bonds between lysine and glutamine amino acids in proteins, essentially gluing protein strands together. Chefs use it to bind meat pieces, create novel textures, and make seamless protein combinations.",

    "What is the Scoville scale used to measure?":
        "Wilbur Scoville developed his scale in 1912 using taste panels to determine how much sugar water was needed to neutralize the heat. Modern testing uses HPLC chromatography for precision, but the scale name endures.",

    "What is 'pectin' and what is its culinary role?":
        "Pectin is a structural carbohydrate in fruit cell walls. When heated with sugar and acid, it forms the gel that makes jam set. Apples and citrus peels are loaded with pectin; strawberries have very little.",

    "What ancient civilization first cultivated chocolate from cacao?":
        "The Olmec civilization (1500 BCE) of modern-day Mexico first cultivated cacao, long before the Maya and Aztec empires. They drank it as a bitter, spiced beverage -- sugar wasn't added until Europeans got involved.",

    "What causes the 'tearing eyes' reaction when cutting onions?":
        "When onion cells are damaged, an enzyme converts amino acid sulfoxides into syn-propanethial-S-oxide gas. This volatile compound irritates your eyes' nerve endings. Chilling onions before cutting slows the reaction.",

    "In molecular gastronomy, what gas is commonly used for flash-freezing tableside?":
        "Liquid nitrogen boils at -196 degC, freezing food almost instantly. The rapid freezing creates tiny ice crystals that preserve smooth texture -- unlike slow freezing, which creates large crystals that damage cell walls.",

    "What is 'hydrocolloid' in the context of modern cooking?":
        "Hydrocolloids include xanthan gum, agar, gellan, methylcellulose, and many others. Each behaves differently with heat, acid, and salt, giving modernist chefs a toolkit for creating precise textures.",

    "What ancient Roman fermented fish sauce is considered a precursor to Worcestershire sauce?":
        "Garum was made by fermenting fish entrails in salt for months under the Mediterranean sun. Romans used it like we use soy sauce -- as a universal flavor enhancer. Worcestershire sauce uses anchovy ferment similarly.",

    "What is the chemical compound responsible for the distinctive flavor of truffles?":
        "2,4-dithiapentane (also called bis(methylthio)methane) is the key aroma compound, along with dimethyl sulfide. These sulfur compounds produce the musky, earthy aroma that makes truffles one of the world's most prized ingredients.",

    "What is 'MSG' (monosodium glutamate)?":
        "MSG is the sodium salt of glutamic acid -- a naturally occurring amino acid found in tomatoes, Parmesan, and mushrooms. It activates umami taste receptors, and extensive research has found no evidence it causes the symptoms attributed to it.",

    "What is 'konjac' used for in cooking?":
        "Konjac (from the Amorphophallus konjac plant) produces glucomannan fiber that creates extremely low-calorie noodles (shirataki). It's also used as a thickener and is popular in Japanese cuisine.",

    "What is 'caramelization temperature' for sugar?":
        "Sucrose begins decomposing around 160 degC, breaking into hundreds of new compounds that create butterscotch, toffee, and bitter notes depending on how far you push it. Above 180 degC, it quickly turns bitter and burns.",

    "What is a 'veloute'?":
        "Veloute is one of the five French mother sauces -- a light stock (chicken, fish, or veal) thickened with a blond roux. Its name means 'velvety,' describing the smooth, elegant texture it should have.",

    "What is 'deglazing' a pan most useful for?":
        "Those browned bits (fond) are concentrated Maillard flavor. Deglazing with wine, stock, or vinegar dissolves them instantly, giving you the foundation of a rich pan sauce in under a minute.",

    "What is 'dry brine' versus 'wet brine'?":
        "Dry brining is simpler and more forgiving: salt draws out moisture through osmosis, then the dissolved salt gets reabsorbed, seasoning deeply. Wet brining works faster but can waterlog delicate proteins.",

    "What is a 'liaison' used to prevent in a cream sauce?":
        "Adding raw egg yolks and cream to a boiling sauce would scramble the proteins. A liaison -- tempered off the heat -- provides silky thickening without the risk of curdling.",

    "What is 'osmosis' relevant to in cooking?":
        "When salt sits on the surface of food, water moves through cell membranes toward the higher salt concentration outside. This is why salting eggplant draws out moisture and why brined meat stays juicier.",

    "What is 'torchon' in charcuterie?":
        "The cloth ('torchon' means towel in French) creates a smooth, cylindrical shape as the terrine or foie gras sets. Poaching the wrapped roll in court bouillon cooks it gently and evenly.",

    "What is 'praline'?":
        "European praline is caramelized sugar and nuts ground into a paste. Belgian pralines are filled chocolates. Both descend from a 17th-century French confection created by the cook of the Duke of Praslin.",

    "What is 'choux pastry' used for?":
        "Choux is unique because it's cooked twice -- first on the stovetop (which gelatinizes the starch), then baked. Steam trapped inside creates hollow shells perfect for filling with cream, custard, or ice cream.",

    "What is 'pate brisee'?":
        "Pate brisee ('broken dough') gets its name from how the butter is 'broken' into the flour. Keeping the butter cold during mixing creates pockets that produce a tender, crumbly texture after baking.",

    "What is 'umami' most associated with in ingredient terms?":
        "Free glutamate is the umami trigger, and it's concentrated in aged, fermented, and dried foods. Parmesan has more glutamate per gram than almost any other food -- which is why it makes everything taste better.",

    "What is 'crouton'?":
        "Croutons (from French 'croute' meaning crust) transform stale bread into crispy, golden cubes. Tossing them in garlic butter before toasting maximizes flavor -- and is a classic way to avoid wasting bread.",

    "What is 'miso' made from?":
        "Soybeans are fermented with koji mold (Aspergillus oryzae), salt, and sometimes rice or barley. The fermentation breaks proteins into amino acids, creating intense umami. Some misos age for years.",

    "What is 'fish sauce' used for in Southeast Asian cooking?":
        "Fish sauce is liquid umami -- fermented anchovies and salt aged for months. It plays the same role in Thai and Vietnamese cooking that soy sauce does in Chinese and Japanese cuisine.",

    "What is 'fond' de veau in French cooking?":
        "Fond de veau (veal stock) is the foundation of classical French sauce-making. Veal bones contain more collagen than beef bones, producing a stock with superior body and a neutral flavor that supports rather than dominates.",

    "What is 'creaming' butter and sugar in baking?":
        "Beating traps millions of tiny air bubbles in the butter-sugar matrix. These bubbles expand during baking, providing much of a cake's lift. This is why properly creamed butter looks light and fluffy.",

    "What does the Scoville scale actually measure, and what is its unit?":
        "Modern Scoville testing uses HPLC chromatography to precisely measure capsaicinoid concentration in parts per million, then converts to SHU. A habanero measures 100,000-350,000 SHU; a Carolina Reaper exceeds 2,000,000.",

    "What is 'shortcrust pastry' made shorter by?":
        "Fat coats flour particles, blocking water from reaching gluten-forming proteins. More fat = less gluten = shorter, more crumbly pastry. This is the opposite of bread, where you WANT strong gluten.",

    "What is 'the window pane test' for bread dough?":
        "Stretch a small piece thin enough to see light through without tearing. If the gluten is developed enough to form this translucent membrane, the dough is ready. Tearing means it needs more kneading.",

    "What is 'clarifying' a stock?":
        "Egg white proteins coagulate and form a 'raft' that attracts and traps tiny particles, leaving crystal-clear liquid beneath. The result -- consomme -- is one of the most technically demanding preparations in classical cooking.",

    "What is 'tartare' when referring to beef?":
        "Steak tartare uses the finest quality raw beef, typically tenderloin, hand-chopped (never ground). It's traditionally served with capers, shallots, Dijon mustard, and a raw egg yolk on top.",

    "What does 'nappe' mean in sauce consistency?":
        "The nappe test is the chef's gold standard for sauce thickness: coat a spoon, draw a line with your finger, and watch. If the line holds clean, the sauce is ready to serve.",

    "What is a 'mandoline' in cooking?":
        "A mandoline slices faster and more uniformly than even the best knife skills. Professional kitchens use them for paper-thin potato chips, uniform vegetable slices, and precise julienne cuts. Always use the hand guard!",

    "What is 'pate' made from?":
        "Pate ranges from rustic country-style (coarsely ground) to silky-smooth liver mousse. The fat content (often pork back fat) is crucial for moisture and mouthfeel -- lean pate tends to be dry and crumbly.",

    "What is 'tagine' in Moroccan cooking?":
        "The conical clay lid of a tagine condenses steam and returns it to the dish, creating a self-basting cycle. The slow cooking at low temperatures produces incredibly tender meat with concentrated, aromatic sauces.",

    "What is 'tahini'?":
        "Ground sesame seeds produce a paste rich in healthy fats, calcium, and iron. Middle Eastern tahini is a cornerstone ingredient in hummus, baba ganoush, and halva. Quality varies enormously -- good tahini should be smooth and pourable.",

    "What is 'zesting' a citrus fruit?":
        "The zest contains aromatic oil glands packed with flavor. A Microplane grater is the ideal tool -- it removes only the colorful outer layer, leaving the bitter white pith behind.",

    "What is the purpose of 'proofing' yeast before using it?":
        "Dissolving yeast in warm water (about 38 degC) with a pinch of sugar lets you verify it's alive. If it foams within 10 minutes, the yeast is active. Dead yeast means flat bread -- better to find out before mixing the whole recipe.",

    "What is 'clarified stock' called when fully clarified and perfectly clear?":
        "Consomme is stock clarified using a 'raft' of ground meat, egg whites, and aromatics. The result is a crystal-clear, deeply flavored liquid that's considered one of the ultimate tests of a chef's skill.",

    "What is the key technique for making puff pastry flaky?":
        "Each fold creates layers: 3 folds of a single turn = 3 layers, but after 6 turns you have 729 layers! Each thin butter layer creates steam during baking, puffing the dough apart into flaky sheets.",

    "What is 'chorizo'?":
        "Spanish chorizo is a cured, fermented sausage flavored with smoked paprika. Mexican chorizo is fresh and uncured, made with chili peppers. Despite sharing a name, they're quite different products.",

    "What is 'pesto'?":
        "Traditional Genovese pesto is pounded (not blended) in a marble mortar with a wooden pestle. The slow crushing releases basil oils without the heat that a food processor generates, which can oxidize and darken the leaves.",

    "What is 'prosciutto'?":
        "Prosciutto di Parma is salt-cured for 60 days, then air-dried for at least 12 months (often 24-36). The Parma region's specific humidity and breezes contribute to its distinctive sweet, nutty flavor.",

    "What is 'spherification' in modern cooking?":
        "Sodium alginate mixed into a flavorful liquid reacts with calcium chloride on contact, forming a gel membrane around a liquid center. The result is a burst-in-your-mouth sphere that looks like caviar.",

    # === TIER 3+ (selected important ones - the script handles the rest) ===
    "What is 'sous vide' cooking?":
        "Sous vide eliminates guesswork by cooking food in a water bath at the exact final temperature you want. A steak held at 55 degC for two hours will be 55 degC from edge to edge -- perfectly medium-rare throughout.",

    "What does 'denaturation' mean in protein cooking?":
        "Heat or acid unravels a protein's 3D structure, exposing hidden bonds that then reconnect in new ways. This is why a raw egg transforms from clear liquid to opaque solid -- same molecules, totally different arrangement.",

    "What is 'food pairing' theory?":
        "This theory explains surprising combinations like chocolate and blue cheese -- they share key volatile compounds. Heston Blumenthal's famous white chocolate and caviar pairing was discovered this way.",

    "What is 'koji' in Japanese fermentation?":
        "Aspergillus oryzae mold produces enzymes that break proteins into amino acids (umami) and starches into sugars. It's the secret behind soy sauce, sake, miso, and mirin -- the foundations of Japanese flavor.",

    "What is 'molecular gastronomy'?":
        "Coined by physicist Nicholas Kurti and chemist Herve This in 1988, it applies scientific methods to understand why cooking works. It gave us sous vide, spherification, and foam -- techniques now used worldwide.",

    "What is 'the danger zone' in food safety?":
        "Between 4-60 degC, bacteria can double every 20 minutes. Food should never spend more than 2 hours total in this range. The phrase 'when in doubt, throw it out' exists because food poisoning is no joke.",

    "What is 'FIFO' in kitchen stock management?":
        "First In, First Out is the golden rule of kitchen inventory. Newer deliveries go to the back of the shelf; older items move to the front. It minimizes waste and ensures food is used at peak freshness.",
}


def main():
    for filename, contexts in [
        ("grammar.json", GRAMMAR_CONTEXTS),
        ("cooking.json", COOKING_CONTEXTS),
    ]:
        filepath = os.path.join(SCRIPT_DIR, "questions", filename)
        print(f"Reading {filepath}...")
        with open(filepath, "r", encoding="utf-8") as f:
            questions = json.load(f)

        added = 0
        missing = 0
        for q in questions:
            qtext = q["question"].strip()
            if "context" not in q:
                if qtext in contexts:
                    q["context"] = contexts[qtext]
                    added += 1
                else:
                    missing += 1

        print(f"  {filename}: {added} contexts added, {missing} questions without context mapping")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)

        print(f"  Wrote {filepath}")

    print("Done!")


if __name__ == "__main__":
    main()
