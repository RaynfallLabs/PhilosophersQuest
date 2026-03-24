"""
gen_context_gaps.py
Adds missing 'context' fields to grammar.json, philosophy.json, and economics.json.
Each context is factually accurate, explains WHY the answer is correct, max 3 sentences,
and aims to be fun, clever, and memorable.
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Maps: question text → context string ─────────────────────────────────

GRAMMAR_CONTEXTS = {
    "Which word is a pronoun? ":
        "Pronouns are stand-ins that replace nouns so you don't have to keep repeating them like a broken record. "
        "'They' is a third-person plural pronoun, doing the heavy lifting so 'the students' can take a break. "
        "Other pronoun families include I/me, he/him, she/her, and the ever-controversial singular 'they.'",

    "A noun phrase that renames the noun beside it is a(n) ___?":
        "An appositive sits right next to a noun and essentially says 'let me introduce myself' by restating it in different words. "
        "For example, in 'My brother, a doctor, lives in Boston,' the phrase 'a doctor' is the appositive. "
        "Appositives are usually set off by commas, dashes, or parentheses.",

    "Logos persuades by appealing to ___?":
        "In Aristotle's rhetorical triangle, logos is the brainy corner — it wins arguments with facts, data, and airtight reasoning. "
        "While ethos appeals to the speaker's credibility and pathos tugs at emotions, logos lets the evidence do the talking. "
        "The word itself shares a root with 'logic,' which is a handy mnemonic.",

    "A straw man fallacy means the speaker ___?":
        "The straw man fallacy is like building a scarecrow version of your opponent's argument and then triumphantly knocking it down. "
        "Instead of addressing what someone actually said, the speaker distorts it into something weaker and easier to attack. "
        "It's named for the military practice of training on straw dummies rather than real opponents.",

    "An ad hominem argument attacks the ___?":
        "Ad hominem is Latin for 'to the person,' and that's exactly what this fallacy does — it goes after the messenger instead of the message. "
        "Saying 'you can't trust his climate data because he's a bad driver' is a classic example. "
        "A person's character flaws don't automatically invalidate their arguments.",

    "A false dichotomy presents a situation as having only ___?":
        "A false dichotomy, also called a false dilemma, squeezes a complex issue into an either/or box when a whole spectrum of options exists. "
        "'You're either with us or against us' ignores the perfectly reasonable middle ground. "
        "Reality rarely comes in just two flavors.",

    "A red herring in an argument is ___?":
        "Named after the smoked fish that was supposedly dragged across trails to throw hunting dogs off the scent, a red herring derails a debate with an irrelevant tangent. "
        "When someone changes the subject to avoid addressing the actual point, that's the red herring at work. "
        "It's one of the most common — and most effective — diversionary tactics in rhetoric.",

    "The Greek prefix 'poly-' (as in 'polysyndeton') means ___?":
        "'Poly-' comes from Greek 'polus' meaning 'many,' which is why a polygon has many sides, a polyglot speaks many languages, and polysyndeton uses many conjunctions. "
        "It shows up everywhere from 'polymath' (many learnings) to 'Polynesia' (many islands). "
        "If you see 'poly-' at the start of a word, think abundance.",

    "The Greek root 'logos' (as in 'dialogue,' 'monologue') primarily means ___?":
        "Logos is one of the most prolific Greek roots in English, meaning 'word,' 'reason,' or 'discourse.' "
        "A 'dialogue' is literally words between two people, a 'monologue' is one person's words, and 'biology' is the discourse of life. "
        "The ancient Greeks also used logos to mean rational principle, which is why it became central to philosophy and theology.",

    "Which suffix changes a verb into a noun meaning 'the act of' or 'the state of,' as in 'satisfaction'?":
        "The suffix -tion (and its variant -ation) is a Latin-derived workhorse that transforms verbs into nouns: 'satisfy' becomes 'satisfaction,' 'create' becomes 'creation.' "
        "It's one of the most common suffixes in English, appearing in thousands of everyday words. "
        "When you see -tion at the end of a word, you're almost always looking at a noun describing a process or result.",

    "Which prefix means 'not' or 'opposite,' as in 'illogical,' 'immoral,' and 'impossible'?":
        "The Latin prefix in- means 'not,' but it's a shapeshifter: it becomes il- before 'l,' im- before 'b,' 'm,' and 'p,' and ir- before 'r.' "
        "This assimilation happens because saying 'inlogical' or 'inpossible' is a tongue-twister — the sounds naturally blend for easier pronunciation. "
        "Despite looking like four different prefixes, they're all the same morpheme in disguise.",

    "Which sentence avoids a dangling modifier?":
        "A dangling modifier is a phrase that modifies a word not clearly stated in the sentence, creating absurd readings. "
        "'Having studied all night, she passed the exam' correctly attaches the modifier to 'she' — the person who actually studied. "
        "A dangling version like 'Having studied all night, the exam was easy' implies the exam did the studying.",

    "Which sentence demonstrates a misplaced modifier?":
        "'She almost drove her children to school every day' misplaces 'almost' so it modifies 'drove' instead of 'every day,' implying she nearly drove but never actually did. "
        "The intended meaning — that she drove most days but not all — requires 'She drove her children to school almost every day.' "
        "Modifier placement in English can completely change meaning, which is why word order matters so much.",

    "An active voice sentence is preferred over passive voice because it is ___?":
        "Active voice puts the doer front and center ('The cat ate the fish'), making sentences more direct and vigorous than passive constructions ('The fish was eaten by the cat'). "
        "Strunk and White's famous advice to 'use the active voice' has shaped a century of English writing instruction. "
        "Passive voice isn't grammatically wrong, but it often hides responsibility and adds unnecessary words.",

    "Which sentence uses 'imply' and 'infer' correctly?":
        "Imply and infer are two sides of the same communicative coin: the speaker implies (sends a hint), and the listener infers (picks up the hint). "
        "Saying 'The speaker implied guilt; the jury inferred it from the evidence' keeps each verb with its proper actor. "
        "A good mnemonic: the Implier is the Inside source, the Inferrer is the Interpreter.",

    "Which is the correct punctuation for a conjunctive adverb joining two independent clauses?":
        "When a conjunctive adverb like 'however,' 'therefore,' or 'moreover' joins two independent clauses, you need a semicolon before it and a comma after it. "
        "'She was tired; however, she finished the work' follows this rule perfectly. "
        "Using just a comma creates a comma splice, which is one of the most common punctuation errors in English.",

    "Which sentence uses a colon incorrectly?":
        "'She wants: to travel the world' is incorrect because a colon should not separate a verb from its object — the sentence is grammatically complete without the colon. "
        "Colons introduce lists, explanations, or elaborations only after a complete independent clause. "
        "A corrected version would be 'She wants one thing: to travel the world,' where 'She wants one thing' can stand alone.",

    "Which sentence correctly uses a restrictive clause without commas?":
        "'Students who study regularly tend to succeed' uses a restrictive (essential) clause that identifies which students — only those who study regularly. "
        "Restrictive clauses narrow down the noun they modify and are never set off by commas because removing them would change the sentence's meaning. "
        "Compare the nonrestrictive version: 'Students, who study regularly, tend to succeed' — which implies all students study regularly.",

    "Which rhetorical device is used in: 'Government of the people, by the people, for the people'?":
        "Lincoln's famous phrase repeats 'the people' at the end of each phrase (epistrophe) and a preposition pattern at the beginning (anaphora). "
        "When both devices combine, the technical term is symploce — a rhetorical sandwich that hammers the point from both ends. "
        "This triple construction from the Gettysburg Address is one of the most quoted examples of symploce in English.",

    "Which is an example of an oxymoron?":
        "'Living death' smashes two contradictory words together, which is exactly what an oxymoron does — the term itself is an oxymoron, from Greek 'oxus' (sharp) and 'moros' (dull). "
        "Other famous oxymora include 'jumbo shrimp,' 'deafening silence,' and 'cruel kindness.' "
        "The literary power of oxymorons lies in forcing readers to hold two opposing ideas simultaneously.",

    "Which type of irony occurs when the audience knows something the character does not?":
        "Dramatic irony creates tension and suspense by letting the audience in on a secret the character doesn't know. "
        "The classic example is Romeo drinking poison at Juliet's side — the audience knows she's merely asleep, but he doesn't. "
        "Shakespeare and horror movies both rely heavily on this gap between audience knowledge and character ignorance.",

    "Situational irony occurs when ___?":
        "Situational irony is when reality pulls the rug out from under expectations — a fire station burns down, or a traffic safety officer gets a speeding ticket. "
        "It differs from dramatic irony (audience knows more than characters) and verbal irony (saying the opposite of what you mean). "
        "O. Henry built an entire career on situational irony, with 'The Gift of the Magi' being the quintessential example.",

    "The logical fallacy of concluding that because A preceded B, A caused B is called ___?":
        "Post hoc ergo propter hoc — Latin for 'after this, therefore because of this' — is the fallacy of confusing sequence with causation. "
        "Just because the rooster crows before sunrise doesn't mean the rooster causes the sun to rise. "
        "This fallacy is the engine behind most superstitions: you wore lucky socks, your team won, therefore the socks caused the victory.",

    "Circular reasoning (begging the question) occurs when the conclusion ___?":
        "Circular reasoning sneaks the conclusion into the premise, creating an argument that proves itself with itself — a logical ouroboros. "
        "'The Bible is true because it's the word of God, and we know it's the word of God because the Bible says so' is a textbook example. "
        "The Latin name 'petitio principii' literally means 'assuming the starting point.'",

    "A slippery slope argument claims that one step will inevitably lead to ___?":
        "The slippery slope fallacy imagines a chain of increasingly dire consequences tumbling from a single action, like dominoes of doom. "
        "It becomes fallacious when the causal links between steps are asserted without evidence — 'If we allow X, then Y, then Z, then total chaos!' "
        "Not all slope arguments are fallacious, though; some genuinely demonstrate a well-evidenced causal chain.",

    "Etymology is the study of ___?":
        "Etymology traces words back through time to their earliest known origins, revealing surprising family connections — like how 'salary' comes from Latin 'salarium' (salt money). "
        "The word 'etymology' itself comes from Greek 'etymon' (true sense) + 'logos' (study). "
        "It's the linguistic equivalent of ancestry research, but for words instead of people.",

    "The Latin prefix 'bene-' (as in 'benefit,' 'benevolent') means ___?":
        "'Bene-' is Latin for 'well' or 'good,' making a 'benefit' literally a 'good deed' and a 'benevolent' person one who wishes well. "
        "Its evil twin is 'male-' (bad), which gives us 'malevolent,' 'malice,' and 'malfunction.' "
        "Even 'benediction' is just 'bene' + 'dictio' — a 'good saying,' or blessing.",

    "The Latin root 'dict-' (as in 'dictate,' 'predict,' 'verdict') means ___?":
        "'Dict-' comes from Latin 'dicere,' meaning 'to say or speak.' A 'dictator' originally was one who 'spoke' commands, a 'verdict' is a 'true saying,' and to 'predict' is to 'say before.' "
        "This root appears in over 50 common English words, making it one of the most productive Latin roots. "
        "Even 'dictionary' is literally a 'book of sayings.'",

    "In 'Caesar came, saw, and conquered' (veni, vidi, vici), the lack of conjunctions is ___?":
        "Asyndeton is the deliberate omission of conjunctions between words or phrases, creating a rapid-fire, punchy rhythm. "
        "Caesar's 'veni, vidi, vici' is the most famous example — no 'and' needed when you're flexing that hard. "
        "The technique conveys speed and decisiveness, which is exactly the image Caesar wanted to project.",

    "In 'I am tired and hungry and cold and wet,' the repeated 'and' is ___?":
        "Polysyndeton is asyndeton's chatty opposite — it piles on conjunctions to create a sense of accumulation, exhaustion, or overwhelming abundance. "
        "Each repeated 'and' forces the reader to pause, making the list feel heavier and more relentless. "
        "Hemingway and the King James Bible both use polysyndeton extensively to build rhythmic, rolling prose.",

    "Prolepsis as a rhetorical device anticipates and answers a potential ___?":
        "Prolepsis is the rhetorical equivalent of saying 'I know what you're thinking, and here's my answer' — it neutralizes objections before they're even raised. "
        "By addressing counterarguments preemptively, a speaker shows confidence and prevents the audience from mentally checking out. "
        "The term comes from Greek 'prolambanein,' meaning 'to anticipate.'",

    "Aporia is a rhetorical device in which a speaker expresses ___?":
        "Aporia is the art of strategic uncertainty — a speaker pretends to be at a loss about how to proceed, which paradoxically draws the audience in. "
        "When Hamlet asks 'To be or not to be,' he's performing aporia, expressing genuine-seeming doubt about which path to choose. "
        "The Greek word means 'without passage,' suggesting a mental roadblock.",

    "The word 'literally' used as an intensifier ('I literally died laughing') is an example of ___?":
        "Semantic bleaching occurs when a word loses its original meaning through overuse, becoming just a generic intensifier. "
        "'Literally' once meant 'in a literal sense,' but centuries of hyperbolic use have bleached it to mean simply 'really, very much.' "
        "The same fate befell 'really' (once meaning 'in reality'), 'truly,' and 'very' (originally meaning 'truthfully').",

    "Which sentence best demonstrates kairos (the rhetorical principle of timeliness)?":
        "Kairos is the Greek concept of the 'right moment' — the idea that the same argument can be powerful or pointless depending on when it's delivered. "
        "Speaking about disaster preparedness on the anniversary of a disaster leverages kairos because the audience is already emotionally primed. "
        "Unlike chronos (sequential time), kairos is about seizing the opportune moment for maximum rhetorical impact.",

    "Which is an example of a portmanteau formed from 'smoke' and 'fog'?":
        "Lewis Carroll coined the term 'portmanteau word' in 'Through the Looking-Glass,' comparing it to a suitcase with two compartments. "
        "'Smog' blends 'smoke' and 'fog' — it was coined in 1905 London, where coal smoke and fog were a deadly daily reality. "
        "Other famous portmanteaux include 'brunch' (breakfast + lunch) and 'motel' (motor + hotel).",

    "A hasty generalization fallacy occurs when a conclusion is drawn from ___?":
        "Hasty generalization leaps from a tiny sample to a sweeping conclusion — like visiting one restaurant in Paris and declaring all French food terrible. "
        "It's the logical foundation of most stereotypes and prejudices. "
        "The antidote is a sufficiently large, representative sample — which is why statistics exists as a discipline.",

    "An appeal to authority fallacy occurs when someone argues a claim is true because ___?":
        "Citing a relevant expert is perfectly valid reasoning, but the appeal to authority becomes fallacious when the 'expert' has no expertise in the topic at hand. "
        "A celebrity endorsing a medical treatment or a physicist opining on economics are classic examples. "
        "The Latin name 'argumentum ad verecundiam' literally means 'argument from respect.'",

    "In classical rhetoric, 'dispositio' refers to ___?":
        "Dispositio is the second of the five classical canons of rhetoric, covering how to arrange your arguments for maximum effect. "
        "Even the most brilliant ideas (inventio) fall flat without good organization — dispositio is the blueprint that structures a speech from introduction to conclusion. "
        "The standard classical arrangement was: exordium, narratio, confirmatio, refutatio, and peroratio.",

    "Which is NOT one of the five classical canons of rhetoric?":
        "The five classical canons are inventio (invention), dispositio (arrangement), elocutio (style), memoria (memory), and actio (delivery). "
        "Dialectica — the art of logical reasoning and debate — was considered a separate discipline in the trivium alongside grammar and rhetoric. "
        "While rhetoric and dialectic are close cousins, the Greeks and Romans treated them as distinct arts.",

    "Zeugma is rhetorically effective because it ___?":
        "Zeugma yokes two unlike things under a single verb, forcing the reader to do a double-take — as in Dickens' 'She lowered her standards and her neckline.' "
        "The humor comes from the unexpected shift between literal and figurative meanings sharing the same grammatical structure. "
        "The word comes from Greek 'zeugma' meaning 'yoke,' the same device that harnesses two oxen together.",

    "The term 'hapax legomenon' refers to a word that ___?":
        "Hapax legomenon is Greek for 'said once' — these are words that appear exactly once in an entire text or body of work. "
        "The Bible and Shakespeare's works are full of them, and they're a nightmare for translators who have zero context for the word's meaning. "
        "Some hapax legomena, like Shakespeare's 'honorificabilitudinitatibus,' were probably coined just for fun.",
}

PHILOSOPHY_CONTEXTS = {
    "What is the 'hard problem of consciousness' as framed by David Chalmers?":
        "Chalmers distinguished the 'easy problems' (how the brain processes information, controls behavior) from the 'hard problem': why any of it feels like something from the inside. "
        "You could theoretically explain every neuron firing in a brain experiencing the color red, and still not explain why there's a subjective 'redness' to the experience. "
        "This explanatory gap between physical processes and subjective qualia has made the hard problem one of philosophy's most debated questions since Chalmers named it in 1995.",
}

ECONOMICS_CONTEXTS = {
    "Sound money advocates argue gold or commodity-backed currency is superior to fiat money. What is their main argument?":
        "Sound money theory holds that when currency is tied to a physical commodity like gold, governments can't simply print more of it — the supply is constrained by nature. "
        "This constraint prevents the 'hidden tax' of inflation, where governments effectively reduce everyone's purchasing power by expanding the money supply. "
        "The gold standard era (roughly 1870-1971) saw much lower long-term inflation rates than the fiat era that followed.",

    "What does the 'debasement' of currency mean historically?":
        "Roman emperors were masters of debasement — Nero reduced the silver content of the denarius from 98% to 93%, and by the crisis of the third century it was practically bronze. "
        "The trick was sneaky: coins looked the same and had the same face value, but contained less precious metal, letting rulers mint more coins from the same amount of silver. "
        "This ancient inflation hack consistently led to price increases, economic instability, and loss of public trust in the currency.",

    "What did Adam Smith argue about the division of labor in 'The Wealth of Nations'?":
        "Smith's pin factory example is economics' most famous thought experiment: one worker making pins alone might produce 20 a day, but ten workers each performing one step could produce 48,000. "
        "Specialization increases productivity because workers develop expertise, save time by not switching tasks, and can use specialized tools. "
        "Published in 1776, this insight became the foundational argument for why trade and specialization make everyone richer.",

    "What economic argument explains why the Soviet Union eventually collapsed despite apparent full employment?":
        "Without market prices to signal scarcity and value, Soviet planners had to guess what millions of people needed — and they consistently guessed wrong. "
        "The economist Ludwig von Mises predicted this 'calculation problem' in 1920, arguing that socialist economies couldn't rationally allocate resources without price signals. "
        "Full employment meant nothing when workers were producing goods nobody wanted, using resources that could have been better used elsewhere.",

    "What did Hong Kong's laissez-faire economic policy under John Cowperthwaite demonstrate between 1950 and 1997?":
        "Cowperthwaite, Hong Kong's Financial Secretary from 1961-1971, famously refused to collect GDP statistics because he feared officials would use them to justify intervention. "
        "Under his policies of minimal regulation, low flat taxes (around 15%), and free trade, Hong Kong's per-capita GDP rose from about 28% of Britain's in 1960 to surpassing it by the 1990s. "
        "Milton Friedman called Hong Kong the best example of free market economics in action.",
}

# ── Main logic ────────────────────────────────────────────────────────────

def patch_file(filename: str, context_map: dict[str, str]) -> int:
    """Add missing context fields to questions in a JSON file. Returns count of patches."""
    path = os.path.join(SCRIPT_DIR, "questions", filename)
    with open(path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    patched = 0
    for q in questions:
        if "context" not in q or not q.get("context", "").strip():
            key = q["question"]
            if key in context_map:
                q["context"] = context_map[key]
                patched += 1
            else:
                print(f"  WARNING: no context mapping for: {key[:80]}...")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    return patched


def main():
    files = [
        ("grammar.json", GRAMMAR_CONTEXTS),
        ("philosophy.json", PHILOSOPHY_CONTEXTS),
        ("economics.json", ECONOMICS_CONTEXTS),
    ]

    total = 0
    for filename, ctx_map in files:
        count = patch_file(filename, ctx_map)
        print(f"{filename}: patched {count} questions (expected {len(ctx_map)})")
        total += count

    print(f"\nTotal patched: {total}")

    # Verify no gaps remain
    print("\n--- Verification ---")
    all_good = True
    for filename, _ in files:
        path = os.path.join(SCRIPT_DIR, "questions", filename)
        with open(path, "r", encoding="utf-8") as f:
            questions = json.load(f)
        missing = [q["question"][:60] for q in questions
                   if "context" not in q or not q.get("context", "").strip()]
        if missing:
            all_good = False
            print(f"{filename}: STILL MISSING {len(missing)} contexts:")
            for m in missing:
                print(f"  - {m}")
        else:
            print(f"{filename}: OK (all {len(questions)} questions have context)")

    if all_good:
        print("\nAll context gaps filled successfully!")
    else:
        print("\nSome gaps remain — check the warnings above.")


if __name__ == "__main__":
    main()
