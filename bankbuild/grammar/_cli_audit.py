"""CLI-harness audit driver for the GRAMMAR bank (moral + tone + lanestrict).

Forked from bankbuild/economics/_cli_audit.py; rubrics rewritten for the grammar
voice (Comma-Saves-Lives Pattern: punchline-via-misuse, vocab-teaching T1-T3,
grade-10 hard ceiling, light moral load, kid-safe punny-dad register).

USAGE (from the CLI orchestrator):
  python -m bankbuild.grammar._cli_audit prompt <moral|tone|lanestrict> [--batch=5] [id1 id2 ...]
  python -m bankbuild.grammar._cli_audit aggregate <moral|tone|lanestrict>
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bank import paths  # noqa: E402

SUBJECT = "grammar"
P = paths(SUBJECT)
LAD = P["LAD"]
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_cli_state")
os.makedirs(STATE, exist_ok=True)


LANESTRICT_RUBRIC = """LANE-STRICT AUDIT for the GRAMMAR bank. Sole question: is this ladder actually GRAMMAR (the RULES that govern how English sentences are put together + their correct vs incorrect application), or is it VOCABULARY (word meanings / etymology as such), WRITING-COMPOSITION (essay structure / argumentation / paragraphing), or bare LITERATURE with a grammar label used as a fig leaf?

A rung is GRAMMAR if its ANSWER is one of:
  - a PUNCTUATION RULE + its correct vs incorrect application (vocative comma, Oxford comma, semicolon between independent clauses, apostrophe for possession, apostrophe for contraction, em-dash vs en-dash, comma splice, question mark inside vs outside quotes)
  - a HOMOPHONE / CONFUSABLE resolution (your vs you're, its vs it's, there/their/they're, affect vs effect, then vs than, lose vs loose, accept vs except, complement vs compliment)
  - an AGREEMENT rule (subject-verb agreement including collective nouns and measurement subjects, pronoun-antecedent, tense sequence)
  - a SENTENCE-STRUCTURE rule + violation (fragment, run-on, comma splice, parallel structure violation, misplaced modifier, dangling modifier, garden-path)
  - a USAGE / REGISTER call (literally-as-figurative-intensifier, less vs fewer, may vs might, active vs passive tradeoff, wordy vs concise revision, tense/mood consistency)
  - a WORDPLAY term named + illustrated (chiasmus, zeugma, malapropism, spoonerism, buffalo-construction, pun, palindrome)
  - a PARADIGM / INFLECTION form (who/whom, lay/lie, had run vs had ran, fewer vs less as measure, whom/whomever)
  - a part-of-speech identification tied to a QUOTED example sentence (T1-T3 vocab-teaching invariant)

A rung is NOT GRAMMAR (flag as lane-drift) if its ANSWER is:
  - a WORD MEANING with no rule component -- pure vocabulary ("what does 'ubiquitous' mean?" is vocab, not grammar; "which sentence uses 'ubiquitous' correctly?" IS grammar because it tests usage)
  - a PURE ETYMOLOGY fact ("the word 'sandwich' comes from the Earl of Sandwich" -- vocab bank if built, not grammar); etymology may appear as CONTEXT for a grammar rule (T4-T5 "why does English keep both 'ox/oxen' and 'boxes'?") but cannot be the standalone payoff
  - a WRITING-COMPOSITION fact (how to structure a five-paragraph essay; what a thesis statement is; how to write a topic sentence; how to cite MLA vs APA -- composition-bank territory, not grammar)
  - a LITERATURE fact (who wrote what; what a novel is about; a character's arc -- literature/history bank, not grammar)
  - a LINGUISTICS-ACADEMIC fact above grade-10 (Chomsky's transformational grammar, Saussure's signifier/signified, deep vs surface structure, morphosyntax, phonological theory, verb-valency taxonomy, evidentiality typology, generative syntax -- OUT per the grade-10 ceiling)
  - a SPELLING drill absent a rule ("how do you spell 'accommodate'?" is spelling drill, not grammar; "which sentence uses 'accommodate' correctly?" IS grammar as usage)

CRITICAL: The vocab-teaching invariant (T1-T3) makes SOME vocabulary appear in-lane -- when a grammar rule uses a QUOTED example sentence with a defined term ("A vocative addresses the listener -- as in 'Let's eat, Grandma!' -- what mistake breaks the second reading?"), that IS grammar. Flag when the payoff is the WORD MEANING itself with no rule application. Historical/literary examples as SETTING for a grammar rule are FINE ("Lincoln's Gettysburg Address uses parallel structure -- of the people, by the people, for the people -- what device is that?") -- the payoff is the grammar device, not the history. Flag when the answer is the historical fact ITSELF.

For each RUNG in the ladder give a per-rung verdict (grammar / not-grammar). For the LADDER give:
  - grammar_rungs = count of rungs that are legitimate grammar
  - drift_rungs = count of rungs that are lane-drift
  - verdict = 'keep' (>= 70% grammar), 'trim' (mixed - keep only grammar rungs), or 'delete' (< 30% grammar)
  - recommendation = one-line rationale
  - keep_idxs = if 'trim', the list of rung indices to KEEP

Do NOT flag a ladder just because its TOPIC crosses domains. Flag only on the SUBSTANCE of the rungs' answers."""


MORAL_RUBRIC = """THE MORAL VISION for the GRAMMAR bank (docs/quiz/moral_vision.md + bankbuild/subjects/grammar.json + feedback-grammar-voice + feedback-no-content-warping). Grammar is a LIGHT-STANCE subject: the bank leans TEACH-THE-STANDARD (prescriptive) while acknowledging real usage evolves. It has NONE of the heavy moral load of philosophy/economics/theology/science. The moral-audit's job here is to catch IDEOLOGICAL DRIFT -- politics or religion smuggled in as example-sentence fodder -- and FABRICATED FACTS about writers/etymologies/quotations. Score the ladder for VIOLATIONS of these:

1. IDEOLOGICAL DRIFT VIA EXAMPLE SENTENCES -- the #1 catch. Grammar rules illustrated with POLITICALLY-CHARGED example sentences are IDEOLOGICAL DRIFT, even if the grammar itself is correct. VIOLATION: (a) political-figure-as-subject dragging politics in ("President X lied to Congress" as a subject-verb example, "Senator Y's policies destroyed the economy" as a modifier example); (b) currently-live political/culture-war sentences ("The border crisis worsened last quarter", "Climate denial harms our planet", "Gender is fluid / Gender is binary" as example sentences -- either direction); (c) religious shibboleths as examples ("Jesus saves believers", "There is no God", "Allah is merciful" -- again, either direction). The bank teaches GRAMMAR; example sentences must be POLITICALLY + RELIGIOUSLY NEUTRAL or drawn from the SAFE historical/literary canon (Lincoln's Gettysburg parallel structure, Churchill's chiasmus, Austen quotations, everyday-life scenes: pets, food, weather, siblings, sports). FLAG HIGH on political/culture-war example sentences; MEDIUM on religious shibboleths.

2. FABRICATED FACTS about writers, styles, or etymologies. Grammar T4-T5 can reference real writers (Strunk, White, Lynne Truss, Fowler, Bryan Garner, Steven Pinker) and real works ("Eats, Shoots and Leaves" 2003, "The Elements of Style" 1918 Strunk / 1959 Strunk+White). VIOLATION: (a) fake dates ("Lynne Truss published 'Eats, Shoots and Leaves' in 2005" -- 2003); (b) misattributed quotes ("Winston Churchill: 'Never end a sentence with a preposition'" -- Churchill actually MOCKED that rule with "This is the sort of English up with which I will not put"); (c) fabricated etymology (invented origins for words -- especially in wordplay-pillar rungs about "buffalo buffalo Buffalo buffalo..." or "sandwich" or "quiz"); (d) fabricated grammatical "rules" that don't exist ("the split-infinitive rule was invented by Latin scholars" is TRUE and cite-able; "the Oxford comma was standardized in 1908" would need to be verified). Grokipedia-verify anything historical. FLAG HIGH.

3. ABOVE-GRADE-10 LINGUISTICS JARGON as content (not just as a distractor to reject). Grade-10 hard ceiling: no Chomsky/Saussure/Sapir-Whorf/Bloomfield/Panini as answer-payoff, no transformational grammar / generative syntax / deep vs surface structure / morphosyntax / phonological theory / verb-valency taxonomy / evidentiality typology / critical-period hypothesis as answers. These may appear as DISTRACTORS a T5 kid rejects ("which of these is NOT a real grammar rule for grade-10 writers?"), but never as the correct answer. FLAG MEDIUM.

4. PRESCRIPTIVIST OVERREACH stated as ABSOLUTE fact. The bank leans teach-the-standard, but some "rules" are actually zombie superstitions -- flag when a rung asserts an invented rule as absolute. VIOLATION: (a) "Never split an infinitive" stated as if it's a real rule (it's not -- split infinitives are fine); (b) "Never end a sentence with a preposition" stated as if it's a real rule (Churchill mocked this); (c) "Never begin a sentence with 'And' or 'But'" stated as absolute (both are fine when used deliberately); (d) singular-they treated as ungrammatical (used since Shakespeare). Prescriptive rules where the standard IS clear (subject-verb agreement, its/it's, "fewer" for count nouns) are fine. Flag when a rung teaches a superstition as if it were a rule. FLAG MEDIUM.

5. DESCRIPTIVIST-CAPITULATION on where the standard IS clear. The mirror of rule 4: don't flatten actual usage rules into "well, anything goes if enough people say it." VIOLATION: (a) "less" vs "fewer" collapsed as "both are fine now" (fewer for count nouns is still the standard); (b) "literally" as figurative intensifier taught as CORRECT with no register note (it's INFORMAL usage a careful writer avoids); (c) "who" vs "whom" collapsed as "whom is dead" (whom is alive in formal writing). Teach the standard, note the informal usage as informal. FLAG LOW-MEDIUM.

6. HISTORICAL / LITERARY EXAMPLE ACCURACY. When a rung cites a real quote or historical figure as an example, the quote must be REAL and correctly attributed. VIOLATION: (a) fake JFK quote for chiasmus (his real "ask not what your country" is fine); (b) misattributed Lincoln quote for parallel structure; (c) fake Shakespeare examples; (d) fake historical anecdotes about "how grammar rule X came about." Grokipedia-verify. FLAG HIGH.

7. LANE-DRIFT catch (also covered separately in lanestrict, but flag here as moral-vision failure if the rung is pure vocabulary / composition / literature with no grammar-rule payoff). FLAG MEDIUM.

CRITICAL GUARD -- DO NOT OVER-FLAG: apolitical everyday example sentences ("The dog chased the ball", "Grandma baked cookies", "The team won the game"), canonical historical wordplay examples (JFK's "ask not what your country" as chiasmus, Lincoln's "of the people, by the people, for the people" as tricolon, Churchill's up-with-which-I-will-not-put on preposition-stranding), the Grandma vocative example ("Let's eat, Grandma!"), the Oxford-comma strippers/JFK/Stalin example (canonical -- see feedback-grammar-voice), garden-path "The horse raced past the barn fell" (canonical), buffalo-construction (canonical), "Time flies like an arrow; fruit flies like a banana" (canonical), and pun-dad/eye-rolling-safe humor are ALL CORRECT and expected. Flag only genuine violations. The #1 catches: IDEOLOGICAL DRIFT (rule 1), FABRICATED FACTS (rule 2), and HISTORICAL/LITERARY ACCURACY (rule 6)."""


TONE_RUBRIC = """You are reviewing a GRAMMAR quiz bank a father built for HIS OWN KIDS (ages ~10-14), as a careful PARENT would. The bank teaches grammar via the Comma-Saves-Lives Pattern: the memorable rung QUOTES a wrong version of a sentence in the stem so a kid laughs (or winces) at the mistake and remembers the rule. The voice is PUNNY DAD -- eye-rolling, absurd, safe-for-kids humor. Canonical punchlines are IN and expected: "Let's eat, Grandma!" (vocative comma -- the "eating Grandma" reading is the whole point), "I invited the strippers, JFK, and Stalin" (Oxford comma -- without it, JFK and Stalin become the strippers), garden-path "The horse raced past the barn fell", buffalo-construction, "Time flies like an arrow; fruit flies like a banana", chiasmus, malapropism, spoonerism. These canonical examples STAY as-is -- they're the load-bearing pedagogy. Flag a rung ONLY for a genuine TONE / APPROPRIATENESS problem below:

1. FRESH VIOLENT EXAMPLE SENTENCES (the priority). The canonical Grandma vocative example is CANONICAL -- it stays. But do NOT invent NEW violent example sentences to teach grammar. VIOLATION: (a) a fresh "let's kill/hurt/torture X" sentence used to illustrate a comma or modifier rule; (b) a fresh weapon/gore/murder scenario used for a subject-verb example; (c) a fresh domestic-violence or abuse scenario. Punchlines should be ABSURD, not menacing. The "eating Grandma" gag works because it's obviously absurd; a fresh "the killer walked, into the room" example is genuinely creepy. FLAG HIGH on fresh violence; FLAG the LOW severity on the canonical Grandma if it appears (it doesn't, it's canonical) -- but a fresh sibling-example like "Let's eat, Timmy!" is FINE (still absurd, still not menacing).

2. MEAN-SPIRITED / BULLYING HUMOR. Punchlines should be PUNNY-DAD absurd, not mean. VIOLATION: (a) example sentences mocking a real named group (ethnic, religious, disability, body-type, socioeconomic); (b) example sentences that punch down at kids ("The stupid student failed his grammar test" for a modifier example); (c) sneering register toward the reader ("If you can't spot this, you're an idiot" as context/closer). Grammar humor should make kids WANT to write better, not make them feel dumb. FLAG MEDIUM-HIGH.

3. PROFANITY / CRUDE CONTENT as example sentences. VIOLATION: (a) any profanity in stems or answers (even mild -- "damn" / "hell" / "crap" as example words); (b) sexual innuendo in example sentences; (c) toilet humor; (d) drug/alcohol scenarios as example fodder ("She drank six beers and then drove home" for a compound sentence). Substitute silly-safe scenarios (pets, food, sports, homework, weather, siblings). FLAG HIGH.

4. KID-APPROPRIATENESS beyond violence/profanity. (a) Adult-life scenarios kids won't parse or shouldn't be modeling (workplace politics, dating drama, financial-instrument sentences); (b) self-harm / suicide framings unrelated to teaching grammar; (c) medical-emergency scenarios ("The paramedic couldn't revive her" as a subject-verb example); (d) horror/dread scenarios that stick after the quiz ends. Kid-life scenarios (school, family, hobbies, animals, food) are the safe defaults. FLAG MEDIUM.

5. DISTURBING-OUT-OF-CONTEXT. The deck is SHUFFLED; a stem read cold should not land as menacing, self-harm-adjacent, cultish, or creepy toward the reader in a way unrelated to teaching grammar. The Grandma canonical works because it's ABSURD-menacing (obviously a comma joke). A stem like "You will never escape" quoted for a modifier example lands as menacing out of context. FLAG.

6. TONE-DEAF PUNS on real tragedy. VIOLATION: puns invoking Holocaust / 9/11 / recent mass shootings / natural disasters / ongoing wars as vehicles for a grammar joke. Historical wordplay (Lincoln, Churchill, JFK inauguration) is FINE because the moment is closed and canonical; ongoing tragedy is off-limits. FLAG HIGH.

CRITICAL GUARD -- DO NOT OVER-FLAG: the canonical corpus ("Let's eat, Grandma!", "I invited the strippers, JFK, and Stalin", "The horse raced past the barn fell", buffalo-construction, "Eats, Shoots and Leaves" panda, "Time flies like an arrow"), pun-dad absurdism, silly-scenario examples (dog chasing ball, grandma baking cookies, kid forgetting homework), historical/literary canonical quotes (Lincoln parallel structure, Churchill chiasmus, JFK inaugural chiasmus), and eye-rolling groaner puns ARE ALL EXPECTED and must STAY. You are flagging FRESH violent examples, MEAN-SPIRITED humor, PROFANITY, and TONE-DEAF wordplay on real tragedy -- NOT the canonical pedagogy. When unsure, do NOT flag. Most ladders will be clean.

For each flagged rung give idx + rule(1-6) + severity + one concrete line + a one-line fix suggestion."""


def all_ladder_ids():
    # Skip intermediate coordinator outputs like `0182_ladder.json` — audit only
    # the canonical slug-named files that `bank.py integrate` writes.
    import re
    intermediate = re.compile(r"^\d{4}_ladder$")
    ids = []
    for f in glob.glob(os.path.join(LAD, "*.json")):
        name = os.path.splitext(os.path.basename(f))[0]
        if intermediate.match(name):
            continue
        ids.append(name)
    return sorted(ids)


def read_ladder_for_audit(lid, include_context):
    d = json.load(open(os.path.join(LAD, lid + ".json"), encoding="utf-8"))
    rungs = []
    for r in d.get("rungs", []):
        rung = {
            "tier": r.get("tier"),
            "stem": r.get("stem", ""),
            "choices": r.get("choices", []),
            "answer": r.get("answer", ""),
        }
        if include_context:
            rung["context"] = r.get("context", "")
        rungs.append(rung)
    out = {"name": d.get("name", "?"), "rungs": rungs}
    if include_context:
        out["strand"] = d.get("strand")
    return out


def cmd_prompt(rubric, batch, ids):
    if rubric not in ("moral", "tone", "lanestrict"):
        print("rubric must be moral, tone, or lanestrict")
        return
    if not ids:
        ids = all_ladder_ids()

    include_context = rubric == "moral"
    if rubric == "moral":
        rubric_text = MORAL_RUBRIC
    elif rubric == "tone":
        rubric_text = TONE_RUBRIC
    else:
        rubric_text = LANESTRICT_RUBRIC
    kind = {
        "moral": "moral-vision auditor",
        "tone": "tone/appropriateness reviewer",
        "lanestrict": "lane-strict grammar-vs-vocabulary/writing-composition auditor",
    }[rubric]
    subject_frame = (
        "GRAMMAR quiz bank a father is building for his kids"
        if rubric == "moral"
        else "kids' GRAMMAR quiz bank"
    )
    if rubric == "lanestrict":
        schema_hint = (
            '{"audits":[{"id":"...","verdict":"keep|trim|delete",'
            '"grammar_rungs":N,"drift_rungs":N,"keep_idxs":[...optional...],'
            '"recommendation":"one-line"}]}'
        )
    else:
        schema_hint = (
            '{"audits":[{"id":"...","verdict":"clean|flag","worst_severity":"none|low|medium|high",'
            '"flags":[{"idx":N,"rule":"1..7" or "1..6","severity":"low|medium|high","detail":"one line"'
        )
        if rubric == "tone":
            schema_hint += ',"fix":"one-line fix"'
        schema_hint += '}],"note":"one-line summary"}]}'

    groups = [ids[i : i + batch] for i in range(0, len(ids), batch)]

    print(f"rubric={rubric} batch={batch} ladders={len(ids)} batches={len(groups)}")
    for bidx, group in enumerate(groups):
        blocks = []
        for k, lid in enumerate(group):
            data = read_ladder_for_audit(lid, include_context)
            blocks.append(
                f'  LADDER {k + 1} (id="{lid}"):\n'
                + json.dumps(data, ensure_ascii=True, indent=1)
            )
        reads = "\n\n".join(blocks)

        prompt = (
            f"You are an INDEPENDENT {kind} for a {subject_frame}. Review {len(group)} ladders --"
            f" give EACH its own full, independent review.\n\n"
            f"STEP 1 -- LADDER DATA (already inlined below; do NOT modify):\n{reads}\n\n"
            f"{rubric_text}\n\n"
            f"Audit EVERY rung of EVERY ladder. Return one audit object PER LADDER"
            f" ({len(group)} total), each carrying its own id. worst_severity = highest among"
            f" that ladder's flags ('none' if clean); verdict = 'flag' if any high/medium else"
            f" 'clean'; note = one line. Do not skip or merge ladders.\n\n"
            f"OUTPUT: write EXACTLY this JSON to"
            f' _cli_state/audit_{rubric}_batch{bidx:03d}.json:\n'
            f"  {schema_hint}\n\n"
            f'IMPORTANT: escape embedded double-quotes as \\" or use single quotes so JSON parses.'
            f" ASCII-only."
        )

        pfile = os.path.join(STATE, f"audit_{rubric}_batch{bidx:03d}.md")
        with open(pfile, "w", encoding="utf-8") as f:
            f.write(prompt)
    print(f"wrote {len(groups)} prompt files to _cli_state/audit_{rubric}_batch*.md")
    print(
        f"outputs expected at _cli_state/audit_{rubric}_batch000.json .. batch{len(groups)-1:03d}.json"
    )


def cmd_aggregate(rubric):
    if rubric not in ("moral", "tone", "lanestrict"):
        print("rubric must be moral, tone, or lanestrict")
        return
    files = sorted(glob.glob(os.path.join(STATE, f"audit_{rubric}_batch*.json")))
    all_audits = []
    missing = 0
    for f in files:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print(f"  PARSE-FAIL {os.path.basename(f)}: {e}")
            missing += 1
            continue
        audits = d.get("audits") if isinstance(d, dict) else d
        if not audits:
            missing += 1
            continue
        all_audits.extend(audits)

    if rubric == "lanestrict":
        flagged = [a for a in all_audits if a.get("verdict") in ("trim", "delete")]
    else:
        flagged = [a for a in all_audits if a.get("verdict") == "flag"]
    outpath = os.path.join(STATE, f"audit_{rubric}_all.json")
    json.dump(
        {"rubric": rubric, "audited": len(all_audits), "flagged": len(flagged), "results": all_audits},
        open(outpath, "w", encoding="utf-8"),
        ensure_ascii=True,
        indent=1,
    )
    print(
        f"audit_{rubric}: {len(all_audits)} audited, {len(flagged)} flagged, {missing} missing/parse-fail"
    )
    print(f"wrote {outpath}")
    if flagged:
        print("\nFLAGGED LADDERS:")
        for a in flagged:
            if rubric == "lanestrict":
                sci = a.get("grammar_rungs", "?")
                drift = a.get("drift_rungs", "?")
                v = a.get("verdict", "?")
                print(
                    f"  [{v:>6}] {a.get('id','?')}  (grammar={sci} drift={drift})"
                    f"  -> {a.get('recommendation','')[:120]}"
                )
                if v == "trim":
                    print(f"      keep_idxs: {a.get('keep_idxs',[])}")
            else:
                worst = a.get("worst_severity", "?")
                n = len(a.get("flags", []))
                print(f"  [{worst:>6}] {a.get('id','?')}  ({n} flag{'s' if n != 1 else ''})")
                for fl in a.get("flags", []):
                    if fl.get("severity") in ("high", "medium"):
                        print(
                            f'      T? idx={fl.get("idx")} rule={fl.get("rule")}'
                            f' [{fl.get("severity")}]: {fl.get("detail","")[:120]}'
                        )


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "prompt":
        if len(sys.argv) < 3:
            print("usage: prompt <moral|tone|lanestrict> [--batch=5] [ids...]")
            return
        rubric = sys.argv[2]
        batch = 5
        ids = []
        for a in sys.argv[3:]:
            if a.startswith("--batch="):
                batch = int(a.split("=", 1)[1])
            else:
                ids.append(a)
        cmd_prompt(rubric, batch, ids)
    elif cmd == "aggregate":
        if len(sys.argv) < 3:
            print("usage: aggregate <moral|tone|lanestrict>")
            return
        cmd_aggregate(sys.argv[2])
    else:
        print(f"unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
