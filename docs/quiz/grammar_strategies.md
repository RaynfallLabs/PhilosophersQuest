---
version: 1
date: 2026-05-12
subject: grammar
---

# Grammar strategy taxonomy

Grammar is the daily-language wonder subject — kids see commas and capital letters every day and have no idea where they came from. The bank teaches: (1) what words *do* in sentences, (2) how English came to be what it is, (3) the historical traditions that gave us our rules, (4) the playful corners of language. Voice is **playful with discipline** — every giggle teaches something.

Five pillars:

1. **Parts of speech + sentence structure** — what words *do*
2. **Verb forms + tense + agreement** — verbs deserve their own pillar
3. **Etymology + how English came to be** — the wonder axis (Latin, Greek, Old English, Old French roots; loanwords; word-meaning flips)
4. **Figurative language + word play** — the giggle axis (pun-and-pedagogy)
5. **Grammar history + usage rules + style** — Panini → Webster → Strunk; common confusables; descriptive vs. prescriptive

Every question carries `_meta.strategy` (the named move) and `_meta.strategy_pillar`. Target ≥100 questions per tier (firm floor); aim for comprehensive coverage; total bank ~3000-3500.

## Non-English content: as lens, not as subject

The bank is **English-focused**. Other languages appear ONLY when they illuminate English:
- Latin + Greek roots → English vocabulary
- Old French (1066 Norman conquest) → why English doubled its vocabulary
- Old English → the irregular verbs we still use ("go/went", "is/was")
- Mandarin tones → contrast showing English is stress-timed
- German noun-capitalization → contrast showing English doesn't
- Sanskrit (Panini) → root of grammar tradition

We do NOT study Latin grammar for its own sake. Latin appears WHEN it explains English.

## Voice + char budgets

| Tier | Hard cap | Voice |
|---|---:|---|
| T1 | ≤ 600 | Symbol-led recognition. "What part of speech is 'quickly'?" |
| T2 | ≤ 700 | One-line sentence + question. "In 'The quick brown fox jumps over the lazy dog,' identify the direct object." |
| T3 | ≤ 750 | Scene + analysis. Brief setup permitted. |
| T4 | ≤ 950 | Multi-sentence setup + etymology/history/grammarian-context. |
| T5 | ≤ 1000 | Deep history + grammatical paradox + linguistic terminology. |

Grammar timer = 26s at WIS 10 (allows scene-led questions with substantive content).

## Quality gates

| Gate | Configuration for grammar |
|---|---|
| schema | required |
| **length_parity** | **EXEMPT** (grammar is parallel-form, not parallel-length — short single-word answers like "Noun" are legitimate) |
| length_budget | per-tier cap above |
| **anti_rote** | **EXEMPT** (grammar IS rote by design — definitions matter for parts of speech, terminology) |
| duplicate | 0.85 similarity (standard) |
| **NEW** `validate_grammar_facts` | LLM fact-check for etymology + grammarian-attribution accuracy |

Two exemptions: grammar's voice allows "What part of speech is X?" definitionally AND allows varied-length distractor sets. This is the math/grammar pairing already in the codebase.

---

## Pillar 1 — Parts of speech + sentence structure

### Parts of speech basics (T1-T2)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `pos_noun_basic` | T1 | Noun = person, place, thing, idea; proper vs. common; concrete vs. abstract |
| `pos_verb_basic` | T1 | Verb = action or state of being; "be" verbs as linking verbs |
| `pos_adjective_basic` | T1 | Adjective modifies a noun; answers which/what kind/how many |
| `pos_adverb_basic` | T1 | Adverb modifies verb/adjective/another adverb; often (but not always) ends in -ly |
| `pos_pronoun_basic` | T1 | Pronoun replaces a noun (he, she, it, they, we, you, I) |
| `pos_preposition_basic` | T2 | Preposition shows relationship (in, on, at, under, beside, between, through, despite) |
| `pos_conjunction_basic` | T2 | Conjunction joins (FANBOYS: For And Nor But Or Yet So) |
| `pos_interjection_basic` | T1 | Interjection expresses emotion ("Wow!", "Ouch!", "Hooray!") |
| `pos_eight_traditional` | T2 | The eight traditional parts of speech — Dionysius Thrax codified ~100 BC |
| `pos_article_definite_indefinite` | T2 | "The" = definite; "a"/"an" = indefinite; "an" before vowel sounds (an hour) |

### Sentence structure (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `sentence_subject_predicate` | T2 | Every complete sentence needs a subject and a predicate |
| `direct_object` | T2 | Direct object receives action of transitive verb |
| `indirect_object` | T3 | Indirect object receives the direct object ("Give Mary the book" — Mary is indirect) |
| `transitive_vs_intransitive` | T3 | Transitive needs an object; intransitive doesn't ("She sleeps" vs "She reads books") |
| `independent_clause` | T2 | Stands alone as a sentence — has subject + verb + complete thought |
| `dependent_clause` | T2 | Doesn't stand alone — starts with subordinating conjunction (because, although, since, when) |
| `relative_clause` | T3 | Begins with relative pronoun (who, whom, whose, which, that) |
| `phrase_vs_clause` | T3 | Phrase = group of words, no subject+verb; clause = has subject+verb |
| `prepositional_phrase` | T2 | Begins with preposition, ends with noun ("under the table") |
| `noun_phrase` | T3 | Noun + modifiers ("the very tall building") |
| `appositive` | T3 | Noun that renames another ("My brother, an engineer, lives in Seattle") |

### Sentence types (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `sentence_simple` | T2 | One independent clause |
| `sentence_compound` | T2 | Two or more independent clauses joined by coordinating conjunction or semicolon |
| `sentence_complex` | T2 | One independent + one or more dependent clauses |
| `sentence_compound_complex` | T3 | Multiple independents + at least one dependent |
| `sentence_declarative` | T1 | Makes a statement; ends with period |
| `sentence_interrogative` | T1 | Asks a question; ends with question mark |
| `sentence_imperative` | T1 | Gives a command ("Sit down."); subject "you" usually implied |
| `sentence_exclamatory` | T1 | Expresses strong feeling; ends with exclamation point |

### Punctuation (T1-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `punct_period` | T1 | Ends a sentence; from Greek *periodos* "circuit" |
| `punct_comma` | T2 | Separates items in list, before coordinating conjunction in compound sentence, around appositives, after intro clauses |
| `punct_semicolon` | T3 | Joins related independent clauses; separates list items with internal commas; Aldus Manutius introduced it 1494 |
| `punct_colon` | T3 | Introduces list or quotation or explanation; "The recipe needs three things: flour, water, salt" |
| `punct_em_dash` | T3 | Strong interruption — like this; longer than en dash (which connects ranges 1995–2025) |
| `punct_apostrophe` | T2 | Possession + contraction; tricky cases (its vs. it's) |
| `punct_quotation` | T2 | Direct speech; American puts comma INSIDE; British puts outside |
| `punct_oxford_comma` | T3 | Comma before final "and" in list; AP says no, Chicago + Strunk say yes; "We invited the strippers, JFK, and Stalin" (Oxford comma matters) |
| `punct_ellipsis` | T3 | Three dots indicating omission... or trailing-off |
| `punct_hyphen_vs_dash` | T3 | Hyphen joins words (well-known); en dash for ranges; em dash for breaks |

### Capitalization (T1-T2)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `cap_sentence_start` | T1 | First word of every sentence |
| `cap_proper_nouns` | T1 | Names of specific people, places, things |
| `cap_titles_books_etc` | T2 | Title-case rules; which words DON'T get capitalized (short prepositions, articles, conjunctions) |
| `cap_pronoun_I` | T1 | English uniquely capitalizes "I" (other languages don't) |
| `cap_german_nouns` | T3 | German capitalizes ALL nouns — contrast with English |

---

## Pillar 2 — Verb forms + tense + agreement

### Tenses + aspects (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `tense_simple_three` | T1 | Past / Present / Future — the simple tenses |
| `tense_perfect_aspect` | T2 | Have/has/had + past participle ("I have walked") |
| `tense_progressive_aspect` | T2 | Be + present participle ("I am walking") |
| `tense_perfect_progressive` | T3 | Combines both ("I have been walking") |
| `tense_12_combinations` | T4 | 3 times × 4 aspects (simple, perfect, progressive, perfect progressive) = 12 |
| `tense_present_three_meanings` | T3 | "I walk" can mean: habitual / scheduled future / instructional |

### Agreement (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `subject_verb_agreement` | T2 | Verb matches subject in number — singular subject, singular verb |
| `compound_subject_agreement` | T3 | "Bread and butter is" (single dish) vs. "Bread and butter are" (two items) |
| `collective_noun_agreement` | T3 | "The team is" (US) vs. "The team are" (UK collective) |
| `there_is_there_are` | T2 | "There is" with singular subject following; "there are" with plural |
| `neither_nor_agreement` | T3 | Verb agrees with subject closest to it ("Neither the boys nor the girl is...") |

### Irregular verbs (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `irregular_be_was_were` | T2 | Most-irregular verb in English — 8 forms |
| `irregular_go_went` | T2 | "Went" comes from a different Old English verb ("wendan") — suppletion |
| `english_irregular_count` | T4 | About 200 irregular verbs in English; nearly all from Old English |
| `irregular_lie_lay_distinction` | T3 | "Lie" (recline, intransitive: lie/lay/lain) vs. "Lay" (place, transitive: lay/laid/laid) |
| `bring_brought_not_brang` | T3 | "Brought" is irregular; "brang" isn't standard (despite past-tense regularization pressure) |
| `swim_swam_swum` | T2 | Strong verbs with vowel-change pattern from Old English |

### Voice + mood (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `active_vs_passive_voice` | T3 | Active: subject does action; passive: subject receives action — "The cat chased the mouse" vs. "The mouse was chased" |
| `passive_when_to_use` | T4 | Passive OK when actor unknown/unimportant — "The window was broken" if you don't know who |
| `mood_indicative` | T3 | States fact or asks question — the default mood |
| `mood_imperative` | T3 | Commands — subject "you" usually implied |
| `mood_subjunctive_if_i_were` | T3 | Hypothetical/counterfactual — "If I were rich..." (not "was"); also after "wish" + "demand" verbs |
| `mood_subjunctive_dying_form` | T4 | English subjunctive is fading; preserved in idioms ("Long live the king", "Be that as it may") |

### Other verb topics (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `gerund_vs_infinitive` | T3 | "I like swimming" (gerund) vs. "I like to swim" (infinitive) — distinction nuanced |
| `participle_present_past` | T3 | Present participle = -ing form; past participle = -ed (regular) or various (irregular) |
| `dangling_participle` | T3 | "Walking down the street, the trees looked beautiful" — trees aren't walking |
| `split_infinitive_history` | T4 | "To boldly go" — Star Trek's defiance; 1762 Lowth declared it improper; modern style accepts it |
| `phrasal_verbs` | T3 | Verb + particle changes meaning ("look up" ≠ "look") — English has thousands |
| `modal_verbs` | T3 | Can, could, may, might, shall, should, will, would, must, ought — express possibility/necessity/permission |

---

## Pillar 3 — Etymology + how English came to be

### English language history (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `old_english_anglo_saxon` | T3 | 5th-11th century — Germanic base of English; *Beowulf* in Old English unreadable to modern eyes |
| `1066_norman_conquest` | T3 | William the Conqueror — French became language of nobility, English became commoner tongue, English vocabulary doubled |
| `middle_english_chaucer` | T3 | 1066-1500 — Chaucer's *Canterbury Tales* readable with effort; Norman-French heavy |
| `great_vowel_shift` | T4 | ~1400-1700 — long vowels shifted dramatically; cause why English spelling doesn't match pronunciation |
| `early_modern_english_shakespeare` | T3 | 1500-1700 — Shakespeare wrote in Early Modern English; "thou" still in use |
| `kjv_bible_1611_english` | T4 | King James Bible 1611 shaped English idiom dramatically — "salt of the earth", "fly in the ointment", "scapegoat" |
| `english_vocabulary_size` | T4 | English has ~600,000 words in OED; ~170,000 in current use; more than any other language (debated metric) |
| `printing_press_caxton_1476` | T4 | William Caxton 1476 — first English printer; standardized spelling unevenly (he chose London dialect) |

### Word origins (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `latin_roots_english` | T2 | ~30% of English vocab from Latin (often via French) — including most science/legal terms |
| `greek_roots_english` | T2 | Science + medicine + technology mostly Greek (telephone, philosophy, microscope) |
| `germanic_core_words` | T3 | Everyday short words from Germanic root (man, woman, house, water, food, eat, drink) |
| `french_loan_words_food` | T3 | Pork/beef/mutton (French from Norman cooks) vs. pig/cow/sheep (Anglo-Saxon for farmers) |
| `loanwords_from_arabic` | T3 | Algebra, alcohol, coffee, sugar, magazine, alchemy, zenith, nadir, zero |
| `loanwords_from_dutch` | T3 | Boss, cookie, deck, dock, sketch, yacht, brandy |
| `loanwords_from_native_american` | T3 | Tomato, chocolate, coyote, hurricane, hammock, barbecue, canoe, raccoon, moose, skunk |
| `loanwords_from_indian_subcontinent` | T3 | Pajamas, shampoo, bungalow, jungle, loot, thug, guru, bandana, dungaree |
| `loanwords_from_chinese` | T3 | Ketchup, tea, kung fu, typhoon, tofu, gung-ho |
| `loanwords_from_japanese` | T3 | Tsunami, karaoke, sushi, tycoon, honcho, emoji |
| `loanwords_from_persian` | T3 | Pajamas, paradise, lemon, magic, bazaar, caravan, julep |
| `loanwords_from_czech` | T3 | Robot (Karel Čapek's *R.U.R.* 1920), pistol, polka, bohemian |

### Affixes (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `prefix_un_re_pre` | T2 | Un- = negation; re- = again; pre- = before |
| `prefix_dis_mis_non` | T2 | Dis- = opposite; mis- = wrongly; non- = not |
| `suffix_able_ible` | T2 | -able generally for English roots; -ible for Latin roots (predictable, edible) |
| `suffix_er_or` | T2 | Both make noun from verb (teacher, actor); -er usually Germanic, -or usually Latin |
| `suffix_tion_sion` | T3 | Forms abstract noun from verb (creation, decision) — Latin-derived |
| `prefix_inter_intra_intro` | T3 | Inter- = between (international); intra- = within (intravenous); intro- = inward (introvert) |
| `combining_form_greek` | T3 | -ology (study of), -graph (writing), -phobia (fear), -philia (love), -archy (rule) |

### Word meaning shifts (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `meaning_shift_nice` | T3 | "Nice" meant *foolish* in Middle English (from Latin *nescius* "ignorant") |
| `meaning_shift_awful` | T3 | "Awful" meant *inspiring awe* — God was awful in older Bible translations |
| `meaning_shift_silly` | T3 | "Silly" meant *blessed* or *innocent* (from Old English *sælig*) |
| `meaning_shift_literally` | T3 | "Literally" originally meant "to the letter"; now also used for emphasis |
| `meaning_shift_terrific` | T3 | "Terrific" meant *causing terror* before becoming positive |
| `meaning_shift_gay` | T3 | "Gay" meant *cheerful* through early 20th c; now primarily *homosexual* |
| `meaning_shift_decimate` | T4 | "Decimate" from Roman punishment killing 1 in 10 (decimus); now means devastate broadly |
| `pejoration_amelioration` | T4 | Word meanings drift negative (pejoration) or positive (amelioration) over centuries |
| `semantic_narrowing_widening` | T4 | "Deer" once meant *any wild animal*; "girl" once meant *child of either sex* |

---

## Pillar 4 — Figurative language + word play

### Figures of speech (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `metaphor_basic` | T2 | Direct comparison without "like" or "as" — "Life is a journey" |
| `simile_basic` | T2 | Comparison with "like" or "as" — "Cool as a cucumber" |
| `personification` | T2 | Giving human qualities to non-human — "The wind whispered" |
| `hyperbole` | T2 | Extreme exaggeration — "I've told you a million times" |
| `understatement` | T3 | Saying less than is true for effect — "It's just a flesh wound" (limb falling off) |
| `litotes` | T4 | Affirmation by denying the contrary — "Not bad" = good; "no small feat" = big achievement |
| `metonymy` | T3 | Substitute associated word — "The crown" for monarchy; "the White House" for executive |
| `synecdoche` | T3 | Part for whole — "All hands on deck"; or whole for part — "Australia won" |
| `oxymoron` | T2 | Apparently contradictory paired — "jumbo shrimp", "bittersweet", "deafening silence" |
| `paradox` | T3 | Apparently self-contradictory but illuminating — "Less is more"; "I am lying" |
| `analogy_basic` | T3 | Extended comparison showing structural similarity |
| `allegory` | T4 | Extended metaphor where elements represent moral/political ideas — *Animal Farm*, *Pilgrim's Progress* |
| `irony_basic` | T3 | Verbal: opposite meaning; situational: opposite outcome; dramatic: audience knows what character doesn't |
| `sarcasm_definition` | T3 | Verbal irony intended to mock |
| `apostrophe_rhetorical` | T4 | Direct address to absent/abstract — "Death, where is thy sting?" |

### Sound devices (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `alliteration` | T2 | Repeated initial consonant — "Peter Piper picked a peck of pickled peppers" |
| `assonance` | T3 | Repeated vowel sounds — "How now, brown cow" |
| `consonance` | T3 | Repeated consonant sounds (not just initial) — "pitter-patter" |
| `onomatopoeia` | T2 | Word imitates sound — buzz, hiss, crash, sizzle |
| `rhyme_internal_end` | T3 | End-rhyme (line endings) vs. internal rhyme (within a line) |

### Word play (T2-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `pun_homophone` | T2 | Play on words exploiting similar sound/spelling — "Time flies like an arrow; fruit flies like a banana" |
| `palindrome` | T2 | Reads same forward + backward — "A man, a plan, a canal: Panama"; "Madam, I'm Adam"; "Was it a car or a cat I saw?" |
| `spoonerism` | T3 | Swapped initial sounds — "I have in my bosom a half-warmed fish" (Rev. Spooner allegedly) |
| `eggcorn` | T3 | Mishearing creating new plausible word — "for all intensive purposes" (for all intents and purposes) |
| `malapropism` | T3 | Wrong word for similar-sounding one — Mrs. Malaprop in Sheridan's *The Rivals* 1775 |
| `garden_path_sentence` | T4 | Sentence with misleading parse — "The horse raced past the barn fell" (means *fell* after being *raced*) |
| `crash_blossom` | T4 | Ambiguous headline — "Eighth Army Push Bottles Up Germans" |
| `buffalo_sentence` | T4 | "Buffalo buffalo Buffalo buffalo buffalo buffalo Buffalo buffalo" — grammatically valid |
| `tongue_twister_basic` | T2 | Phrases hard to say fast — "She sells seashells by the seashore" |
| `lipogram` | T4 | Composition omitting a letter — Ernest Wright's *Gadsby* (1939) without the letter 'e' |
| `pangram` | T2 | Uses every letter — "The quick brown fox jumps over the lazy dog" |
| `anagram` | T3 | Rearrange letters — "listen" → "silent"; "astronomer" → "moon starer" |

### Idioms (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `idiom_kick_bucket` | T2 | "Kick the bucket" = die; possible origin from suicide via standing on a bucket |
| `idiom_break_leg` | T2 | "Break a leg" = good luck (theater); origin debated (avoid jinx by saying opposite) |
| `idiom_red_herring` | T3 | Distracting clue; from training hunting dogs by dragging strong-smelling herring |
| `idiom_bite_bullet` | T3 | Endure painful situation; from soldiers biting bullets during surgery before anesthesia |
| `idiom_throw_in_towel` | T3 | Give up; from boxing — corner throws towel to stop fight |
| `idiom_let_cat_out_bag` | T3 | Reveal secret; possibly from market scam selling cat as suckling pig in sealed bag |
| `idiom_bell_the_cat` | T3 | Take risk for common good; mice in Aesop's fable can't agree on belling the cat |
| `idiom_dont_count_chickens` | T2 | Don't count chickens before they hatch — Aesop |
| `idiom_eat_humble_pie` | T4 | Apologize; "umble pie" was deer-organ pie eaten by servants while lords ate venison |

### Specific funny constructions (T3-T4)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `dangling_modifier_funny` | T3 | "Walking down the street, the trees were beautiful" — trees aren't walking |
| `squinting_modifier` | T3 | Ambiguous what it modifies — "Students who study often get better grades" (study often, or often get?) |
| `comma_changes_meaning` | T2 | "Let's eat, Grandma" vs. "Let's eat Grandma" — punctuation saves lives |
| `apostrophe_changes_meaning` | T2 | "Its" vs "It's"; "Your" vs "You're"; "Were" vs "We're" |
| `oxford_comma_funny` | T3 | "I invited the strippers, JFK, and Stalin" (with vs. without Oxford comma) |

---

## Pillar 5 — Grammar history + usage rules + style

### Grammar tradition figures (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `panini_sanskrit_4thc_bc` | T4 | Pāṇini's *Aṣṭādhyāyī* — Sanskrit grammar in 8 chapters, ~4th century BC, 3,959 sutras; more rigorous than any Western grammar until 19th-20th century |
| `dionysius_thrax_greek` | T4 | ~100 BC — *Téchnē grammatikē* established the 8 parts of speech for Greek; foundation for Latin + later European grammars |
| `donatus_latin_grammar` | T4 | 4th century AD — *Ars Minor* and *Ars Maior* — standard Latin grammar text for ~1,000 years; "Donat" became synonym for "primer" |
| `priscian_latin_6thc` | T4 | 6th century AD — *Institutiones Grammaticae* — 18 volumes; standard Latin grammar of medieval Europe |
| `lowth_1762_prescriptive` | T4 | Bishop Robert Lowth — *A Short Introduction to English Grammar* — many "rules" (don't end sentence with preposition, don't split infinitives) come from him imposing Latin rules on English |
| `webster_american_1828` | T4 | Noah Webster — *American Dictionary of the English Language* — established American spelling (color not colour, center not centre, behavior not behaviour) deliberately diverging from British |
| `reed_kellogg_diagram_1877` | T4 | Alonzo Reed + Brainerd Kellogg — *Higher Lessons in English* — invented the sentence diagram still taught (or recently dropped) in US schools |
| `oxford_english_dictionary_history` | T4 | OED — begun 1857, first complete edition 1928 — took 71 years; Murray's "Scriptorium" + thousands of volunteer readers |
| `noah_webster_simplifying` | T4 | Webster intentionally simplified: dropped "u" in colour/honour, swapped "re" to "er" in centre, dropped doubled "l" in traveller |

### Style guide tradition (T4-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `strunk_white_elements_1918` | T4 | William Strunk + E.B. White — *The Elements of Style* — published 1918, White revised 1959; "Omit needless words" |
| `fowler_modern_usage_1926` | T5 | Henry Fowler — *A Dictionary of Modern English Usage* — wittier and more nuanced than Strunk |
| `chicago_manual_of_style` | T5 | First published 1906 by University of Chicago Press — preferred in book publishing + many academic fields |
| `ap_stylebook` | T5 | Associated Press Stylebook — preferred for journalism — concise, no Oxford comma |
| `mla_handbook` | T5 | Modern Language Association — preferred for humanities |
| `apa_style` | T5 | American Psychological Association — preferred for sciences + social sciences |
| `garner_modern_english_usage` | T5 | Bryan Garner — modern descendant of Fowler; influential American usage authority |
| `style_guides_disagree` | T5 | Different style guides actively disagree (Oxford comma is most famous example) |

### Common confusables (T2-T3)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `your_youre` | T2 | Your = possessive; you're = contraction of "you are" |
| `its_its` | T2 | Its = possessive (NO apostrophe); it's = contraction of "it is" |
| `their_there_theyre` | T2 | Their = possessive; there = location; they're = "they are" |
| `affect_effect` | T2 | Affect (usually verb) = to influence; effect (usually noun) = result; both have noun + verb uses though |
| `lay_lie` | T3 | Lay (transitive) takes object: lay/laid/laid; Lie (intransitive): lie/lay/lain |
| `less_fewer` | T2 | Fewer for countable (fewer apples); less for non-countable (less water) |
| `who_whom` | T3 | Who = subject; whom = object; "Whom did you see?" (you = subject; whom = object) |
| `whose_whos` | T2 | Whose = possessive; who's = "who is" |
| `then_than` | T2 | Then = time/sequence; than = comparison |
| `accept_except` | T2 | Accept = receive; except = exclude |
| `complement_compliment` | T3 | Complement = completes; compliment = praise |
| `principle_principal` | T3 | Principle = rule; principal = chief person or amount |
| `stationary_stationery` | T3 | Stationary = not moving; stationery = paper goods |

### Descriptive vs. prescriptive (T4-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `prescriptive_definition` | T4 | Tells how language SHOULD be used — rules-based — Lowth + Strunk are prescriptive |
| `descriptive_definition` | T4 | Describes how language IS used — modern linguistic approach — observed not legislated |
| `grammar_rules_origin` | T4 | Many "rules" (no split infinitive, no preposition at end, no double negative) come from Lowth's attempt to impose Latin patterns on English |
| `descriptivist_dictionary_storm` | T5 | Webster's Third (1961) — included "ain't"; descriptivist reception triggered prescriptivist backlash |
| `language_change_inevitable` | T4 | Languages change continuously — descriptive view says you cannot stop it; prescriptive says rules slow degradation |

### Linguistics terms (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `morpheme_definition` | T3 | Smallest meaning-carrying unit — "cats" = "cat" + "-s" (two morphemes) |
| `phoneme_definition` | T3 | Smallest sound unit that distinguishes meaning — pat vs. bat differ in one phoneme |
| `syntax_definition` | T3 | Rules for combining words into phrases + sentences |
| `semantics_definition` | T3 | Study of meaning in language |
| `pragmatics_definition` | T4 | How context affects meaning — "Can you pass the salt?" is a request, not a question about ability |
| `etymology_definition` | T3 | Study of word origins + history |
| `lexicon_definition` | T3 | Vocabulary of a language or speaker; mental dictionary |
| `phonology_phonetics` | T4 | Phonology = sound patterns of language; phonetics = physical production + perception of speech sounds |
| `syntactic_tree_diagram` | T4 | Chomsky-era constituency tree — shows hierarchical structure |
| `transformational_grammar` | T5 | Noam Chomsky 1957 *Syntactic Structures* — deep vs. surface structure |
| `universal_grammar_chomsky` | T5 | Chomsky's claim that humans have innate language-acquisition capacity |

### Foreign-grammar contrasts illuminating English (T3-T5)

| Strategy ID | Tier | Teaches |
|---|---|---|
| `mandarin_tones_contrast` | T3 | Mandarin uses tone to distinguish meaning (mā mother / má hemp / mǎ horse / mà scold); English uses tone for emphasis/emotion, NOT lexical distinction |
| `german_capitalize_nouns` | T3 | German capitalizes ALL nouns; English only proper nouns |
| `spanish_french_gendered_nouns` | T3 | Romance languages assign gender to all nouns (la mesa, le pain); English doesn't (mostly) |
| `latin_declension_basics` | T4 | Latin nouns change form based on case (nominative/accusative/genitive/etc.); English mostly lost this (kept it in pronouns: he/him/his) |
| `japanese_word_order_sov` | T4 | Japanese is SOV (Subject-Object-Verb); English is SVO |
| `english_no_grammatical_gender` | T4 | English mostly lost grammatical gender by Middle English (kept biological for he/she); contrast with German + Romance |
| `arabic_root_system` | T5 | Arabic words built on 3-consonant roots (k-t-b: kitab=book, katib=writer, maktab=office); English uses concatenative morphology mostly |

## Per-tier totals (target)

| Tier | Pillar 1 | Pillar 2 | Pillar 3 | Pillar 4 | Pillar 5 | **Total** |
|---|---:|---:|---:|---:|---:|---:|
| T1 | 100 | 50 | 60 | 60 | 50 | **320** |
| T2 | 150 | 100 | 150 | 150 | 100 | **650** |
| T3 | 150 | 150 | 200 | 150 | 200 | **850** |
| T4 | 100 | 100 | 150 | 100 | 200 | **650** |
| T5 | 30 | 50 | 100 | 60 | 150 | **390** |
| **Total** | **530** | **450** | **660** | **520** | **700** | **~2860** |

Every tier well above 100 floor. Pillar 5 heaviest at T5 (deep grammar history). Pillar 4 distributed across all tiers (the giggles).

## Generation approach

1. **Deterministic Python generators (~25%)**: parts-of-speech identification, common confusables (your/you're, etc.), basic punctuation, sentence-type identification, common loanword attribution. ~700 questions.
2. **LLM agents (~75%)**: etymology, grammar-history, figurative language, foreign-grammar contrast, style-guide history. ~2100 questions.
3. **Fact-check gate**: `validate_grammar_facts.md` LLM job — etymology accuracy + grammarian attribution + style guide history.

## What success looks like

- A T1 question helps a kid identify parts of speech and basic punctuation
- A T2 question reveals the magic — "nice" used to mean foolish; "robot" comes from a 1920 Czech play
- A T3 question makes the player respect language — Norman conquest doubled English vocabulary; Hindi gave us "pajamas" and "shampoo"
- A T4 question shows the chemistry — Pāṇini's 4th-c BC Sanskrit grammar was more rigorous than anything in the West until Chomsky; Webster deliberately diverged American spelling for nationalism
- A T5 question makes the player want to read Fowler, or argue about the Oxford comma, or learn one more thing about Reed-Kellogg diagrams
- Every joke and pun **teaches something** — playful with discipline

## Anti-patterns specific to grammar

- **No "What is a noun?"** as standalone — already exempt from anti-rote, but should still scene-led: "In 'The cat sat on the mat,' identify the noun(s)"
- **No fake etymologies** — every word origin must be verifiable; the "rule of thumb" wife-beating story is a popular myth — DON'T propagate it
- **No prescriptivism without acknowledgment** — when teaching a rule, acknowledge it's a *rule* (Strunk says X, Fowler disagrees); the bank shows the debate
- **No silly for its own sake** — every giggle teaches; gratuitous joke questions banned
