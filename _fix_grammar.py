"""Phase E grammar fixes — applies the 22 flagged-question fixes.

Validates every change through validate_rewrite. Only applies PASS/SOFT_WARN.
Tracks what was applied vs rejected vs deferred.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/grammar.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))

# Fix definitions: idx → patch dict
# Each patch may have: question (new stem), answer (new answer), choices (new list), context (new context)
FIXES = []

# === CRITICAL #1095: typo "hyhpen" → "hyphen" ===
FIXES.append({
    "idx": 1095,
    "patch": {"question": bank[1095]["question"].replace("hyhpen", "hyphen")},
    "reason": "Fix typo in stem (hyhpen → hyphen).",
})

# === CRITICAL #399: replace 'Apricot' with true non-Arabic word ===
# All four current choices were claimed Arabic. Replace Apricot with Asparagus (Greek).
FIXES.append({
    "idx": 399,
    "patch": {
        "answer": "Asparagus (from Greek 'asparagos' meaning sprout/shoot)",
        "choices": [
            "Asparagus (from Greek 'asparagos' meaning sprout/shoot)",
            "Algebra (from 'al-jabr' meaning 'reunion of parts')",
            "Alcohol (from 'al-kuhl' meaning 'a powder')",
            "Algorithm (from 'al-Khwarizmi' the mathematician)",
        ],
        "context": "Three of these came through medieval Spain when Arabic learning was at its peak. ALGEBRA was named in the title of al-Khwarizmi's 820 AD book. ALCOHOL originally meant a fine powder used for makeup. ALGORITHM is from the same al-Khwarizmi whose Latin name 'Algoritmi' became the term for step-by-step procedures. ASPARAGUS is the outsider — it came through Latin from Greek, not Arabic, and its name has nothing to do with the al- prefix that signals Arabic origin.",
    },
    "reason": "Replace broken 'Apricot is not Arabic' (it actually IS Arabic) with Asparagus, which is genuinely Greek not Arabic.",
})

# === CRITICAL #978: replace 'Spectrum' with true non-spect- word ===
FIXES.append({
    "idx": 978,
    "patch": {
        "answer": "Speech",
        "choices": [
            "Speech",
            "Speculum",
            "Aspect",
            "Inspect",
        ],
        "context": "Three of these come from Latin specere (to look). SPECULUM is a Latin mirror, literally a 'looking-glass.' ASPECT is 'ad-spect' (look-toward). INSPECT is 'in-spect' (look-into). SPEECH is the outsider — it comes from Old English 'spæc,' a Germanic word about speaking, not from the Latin 'spect-' family. The visual-Latin family also gave us prospect (look-forward), retrospect (look-back), respect (look-again), spectacle, spectator, spectrum (Newton's coinage for the rainbow of light), and circumspect (look-around).",
    },
    "reason": "Replace broken 'Spectrum is not spect-' (it IS spect-) with Speech, which is genuinely Germanic not Latin.",
})

# === CRITICAL #980: replace 'Scribble' with true non-scribere word ===
FIXES.append({
    "idx": 980,
    "patch": {
        "answer": "Letter",
        "choices": [
            "Letter",
            "Scripture",
            "Subscribe",
            "Manuscript",
        ],
        "context": "Three of these come from Latin scribere (to write). SCRIPTURE is from 'scriptura' (writing). SUBSCRIBE is 'sub-scribere' (write underneath, the original sense of signing one's name). MANUSCRIPT is 'manu' (by hand) + 'scriptus' (written). LETTER is the outsider — it comes from Latin 'littera' (an alphabet letter), an entirely different Latin root from scribere. The scribere family also gives us scribe, describe, prescribe, transcribe, scribble (yes, even scribble is from scribillare, a diminutive of scribere), inscription, and postscript.",
    },
    "reason": "Replace broken 'Scribble is not scribere' (it IS scribere) with Letter (from littera, different Latin root).",
})

# === CRITICAL #981: replace 'Facade' with true non-facere word ===
FIXES.append({
    "idx": 981,
    "patch": {
        "answer": "Federal",
        "choices": [
            "Federal",
            "Manufacture",
            "Factory",
            "Beneficial",
        ],
        "context": "Three of these come from Latin facere (to make, to do). MANUFACTURE is 'manu' (by hand) + 'facere' (to make). FACTORY is 'factoria' (a place where things are made). BENEFICIAL is 'bene' (well) + 'ficio' (a form of facere). FEDERAL is the outsider — it comes from Latin 'foedus' (a treaty or league), an entirely different Latin root. The facere family is one of the most productive in English: it gives us fact, factor, fashion, feature, defect, affect, effect, perfect (made-through), confection, infection, fiction, suffice, magnify, terrify, satisfy, and even hundreds of words ending -ify, -fect, or -fact.",
    },
    "reason": "Replace broken 'Facade is not facere' (it IS facere via Italian) with Federal (from foedus, different Latin root).",
})

# === WARN #718: replace meta-answer with real misnamed -ology ===
FIXES.append({
    "idx": 718,
    "patch": {
        "answer": "Anthology — literally 'flower-gathering,' but it means a collection of writings",
        "choices": [
            "Anthology — literally 'flower-gathering,' but it means a collection of writings",
            "Biology — the study of life (from 'bios')",
            "Psychology — the study of mind (from 'psyche')",
            "Geology — the study of the earth (from 'gē')",
        ],
        "context": "The Greek '-logia' usually means 'the study of': BIOLOGY (life-study), PSYCHOLOGY (mind-study), GEOLOGY (earth-study). But ANTHOLOGY is the odd one — anthos means 'flower' + logia means 'collection' (a different use of logia), so the literal sense is 'flower-gathering.' Ancient Greeks called their best-poems collections 'anthologies' as if gathering the most beautiful flowers from a garden. Today the word means any collection of poems, stories, or songs — but its root sense isn't 'study' at all.",
    },
    "reason": "Replace meta-answer 'Trick choice — all four correctly named' with Anthology, which truly is misnamed by its root.",
})

# === MINOR decoration parity fixes — strip parens from answer, equalize length ===

# #117 Sandwich
FIXES.append({
    "idx": 117,
    "patch": {
        "answer": "An English earl named John Montagu",
        "choices": [
            "An English earl named John Montagu",
            "A French chef from Paris long ago",
            "A baker who worked for the Roman army",
            "A king of England in the Middle Ages",
        ],
    },
    "reason": "Strip parens decoration-skim-tell; name the earl directly.",
})

# #119 Cardigan
FIXES.append({
    "idx": 119,
    "patch": {
        "answer": "An English earl named James Brudenell",
        "choices": [
            "An English earl named James Brudenell",
            "A French knitter who lived in Lyon",
            "A Scottish wool-trader from Edinburgh",
            "An American clothing-maker from Boston",
        ],
    },
    "reason": "Strip parens decoration-skim-tell; name the earl directly.",
})

# #171 alliteration
FIXES.append({
    "idx": 171,
    "patch": {
        "answer": "They use alliteration with the same sound repeated.",
        "choices": [
            "They use alliteration with the same sound repeated.",
            "They use only long and complicated old words.",
            "They contain hidden secret meanings to puzzle out.",
            "They use only rare words that are hard to know.",
        ],
    },
    "reason": "Move parens definition into the answer flow.",
})

# #174 palindrome
FIXES.append({
    "idx": 174,
    "patch": {
        "answer": "It is a palindrome, spelled the same backward and forward.",
        "choices": [
            "It is a palindrome, spelled the same backward and forward.",
            "It is the oldest word in the English language by far.",
            "It is the longest word in the English language overall.",
            "It is the only English word with no vowels at all.",
        ],
    },
    "reason": "Replace parens with a comma-clause; same content, even shape.",
})

# #188 Hold your horses
FIXES.append({
    "idx": 188,
    "patch": {
        "answer": "Hold your horses, please wait just a moment.",
        "choices": [
            "Hold your horses, please wait just a moment.",
            "The horse galloped across the open field.",
            "She fed her horse oats and fresh hay.",
            "There are five horses in the stable today.",
        ],
    },
    "reason": "Replace parens with a comma-clause.",
})

# #193 hyperbole
FIXES.append({
    "idx": 193,
    "patch": {
        "answer": "An exaggeration for effect, not really a million times",
        "choices": [
            "An exaggeration for effect, not really a million times",
            "A very precise count of all the past warnings",
            "A simile comparing two unrelated daily things",
            "A pun playing on the word 'million' twice",
        ],
    },
    "reason": "Replace parens with comma.",
})

# #234 capital-I — surface the medieval-scribe punchline as answer
FIXES.append({
    "idx": 234,
    "patch": {
        "question": bank[234]["question"],
        "answer": "A lone lowercase i looked too small, so medieval scribes wrote it tall",
        "choices": [
            "A lone lowercase i looked too small, so medieval scribes wrote it tall",
            "Because I is the first letter of the alphabet, naturally",
            "Because all pronouns are always capitalized always",
            "Because vowels are always capitalized in writing",
        ],
        "context": "The pronoun I was originally lowercase, but in medieval manuscripts a single lowercase i floated alone on the page and was easy to miss. Scribes started making it tall (capital I) so readers wouldn't lose it. The convention stuck. English is unusual in capitalizing its first-person pronoun — German capitalizes 'Sie' (formal you), but most languages don't capitalize any pronoun. The capital-I habit moved from manuscripts to print and is now a permanent English-spelling rule.",
    },
    "reason": "Surface the medieval-scribe punchline as answer instead of burying in context.",
})

# #425 gymnasium
FIXES.append({
    "idx": 425,
    "patch": {
        "answer": "A place to exercise NAKED, from Greek 'gymnos' meaning naked",
        "choices": [
            "A place to exercise NAKED, from Greek 'gymnos' meaning naked",
            "A place to wrestle with oil and sand",
            "A place to train for combat with weapons",
            "A place to study sports philosophy",
        ],
    },
    "reason": "Replace parens with comma.",
})

# #490 pun
FIXES.append({
    "idx": 490,
    "patch": {
        "answer": "A pun on 'interest' meaning both money and curiosity",
        "choices": [
            "A pun on 'interest' meaning both money and curiosity",
            "Alliteration on the letter B sounds",
            "Hyperbole exaggerating the banker's career",
            "Metaphor comparing banking to losing things",
        ],
    },
    "reason": "Replace parens with prepositional phrase.",
})

# #700 naughty — strip the parens-and-em-dash etymology gloss
FIXES.append({
    "idx": 700,
    "patch": {
        "answer": "Having nothing, so morally worthless or wicked",
        "choices": [
            "Having nothing, so morally worthless or wicked",
            "Showing off — wearing fancy clothes meant to draw stares",
            "Eating too quickly — gobbling food rapidly with no manners",
            "Skipping religious observance — refusing to attend services",
        ],
    },
    "reason": "Strip parens AND the etymology em-dash; clean answer matching distractor em-dash shape.",
})

# Hmm — Issue: distractors have em-dashes; the answer above doesn't. Let me add em-dash to answer:
FIXES[-1]["patch"]["answer"] = "Having nothing — morally worthless, wicked, from 'naught'"
FIXES[-1]["patch"]["choices"][0] = "Having nothing — morally worthless, wicked, from 'naught'"

# #730 stars-with-al  — trim correct answer to similar shape as distractors (drop parens, drop "with 'al-,' meaning 'the'")
FIXES.append({
    "idx": 730,
    "patch": {
        "answer": "Medieval Arab astronomers cataloged the stars; their Arabic names entered Europe via Latin translations.",
        "choices": [
            "Medieval Arab astronomers cataloged the stars; their Arabic names entered Europe via Latin translations.",
            "Galileo named most stars himself in the 1600s using Arabic-sounding phonetics to suggest mystery.",
            "Modern astronomy chose Arabic-style names in the 1900s when older systems became politically complicated.",
            "Persian poets invented these names in the 1300s and they spread through European folklore literature.",
        ],
    },
    "reason": "Strip the parens; preserves length parity (still longest but tightened).",
})

# #1610 Cry havoc — replace with non-Antony Caesar line
FIXES.append({
    "idx": 1610,
    "patch": None,  # Need to read first
})
q1610 = bank[1610]
# Find which choice is "Cry havoc"
new_choices = []
for c in q1610["choices"]:
    if "Cry havoc" in c:
        new_choices.append("Et tu, Brute? Then fall, Caesar — Caesar's last words to Brutus")
    else:
        new_choices.append(c)
FIXES[-1]["patch"] = {"choices": new_choices}
FIXES[-1]["reason"] = "Replace Antony's 'Cry havoc' (different scene) with Caesar's own line, avoiding multi-Antony confusion."

# #1247 Buffalo redundancy with #1849 — soften by rephrasing 1849 to different angle
# Per judge: ask about William Rapaport (the linguist who popularized) or the broader homograph phenomenon
# Need to read 1849 first
q1849 = bank[1849]
# We'll change 1849 to ask about William Rapaport
FIXES.append({
    "idx": 1849,
    "patch": {
        "question": "The 'Buffalo buffalo Buffalo buffalo buffalo buffalo Buffalo buffalo' sentence is the most famous English-grammatical curiosity — eight identical words forming a valid sentence. It was popularized in 1972 by William Rapaport, a SUNY Buffalo computer scientist. What enables the trick?",
        "answer": "Three different lexical uses of 'buffalo': the city, the animal, and the verb (to bully)",
        "choices": [
            "Three different lexical uses of 'buffalo': the city, the animal, and the verb (to bully)",
            "Two homophones of 'buffalo' (the animal and the river) plus a punctuation trick on capitalization",
            "Buffalo is an abbreviation for four longer English words that share its spelling exactly",
            "The sentence is actually grammatically broken; native speakers refuse to accept it as English",
        ],
        "context": "William Rapaport, the computer-science professor at SUNY Buffalo, popularized the sentence in a 1972 paper. The trick relies on three distinct lexical entries for 'buffalo': (1) Buffalo the city in New York; (2) buffalo, the animal (plural same as singular); (3) buffalo, the verb meaning 'to bully or confuse.' Parsing: '[Buffalo buffalo] [Buffalo buffalo buffalo] buffalo [Buffalo buffalo]' = 'Buffalo bison whom other Buffalo bison bully, themselves bully [other] Buffalo bison.' Other identical-word constructions exist: 'James, while John had had had had had had had had had had had a better effect on the teacher,' though Buffalo's eight-word run is the cleanest.",
    },
    "reason": "Reframe 1849 to ask about Rapaport's role rather than duplicate 1247's content.",
})

# #76 conjunctions — improve scene anchoring
# Need to read first
q76 = bank[76]
FIXES.append({
    "idx": 76,
    "patch": {
        "question": "In the sentence 'I wanted ice cream, ___ the store was closed,' which word fits the blank to mark the contrast between what was wanted and what happened?",
        "answer": "but",
        "choices": [
            "but",
            "and",
            "so",
            "because",
        ],
        "context": "The conjunction BUT marks contrast or opposition between two clauses: what was wanted (ice cream) versus what happened (the store was closed). AND would suggest both things happened in sequence without contrast. SO would suggest the second clause caused the first. BECAUSE would reverse the cause-effect entirely. The contrast conjunctions in English are BUT, YET, and HOWEVER — each signaling that what follows is unexpected given what came before.",
    },
    "reason": "Reframe as identify-in-example with concrete scene per judge suggestion.",
})

# #802 bullet — soften historical claim
q802 = bank[802]
FIXES.append({
    "idx": 802,
    "patch": {
        "answer": q802["answer"] if "uncertain" in q802["answer"].lower() else q802["answer"],
    },
    "reason": "Skip — judge confidence MEDIUM and the bullet-biting origin claim, while folk-etymology, is also the standard answer given in OED context; the bank's framework warns against fake etymology but this one is actually historically argued. Defer for human review.",
})
# Actually let me just remove this fix; the judge's confidence was medium and the etymology is ambiguous
FIXES.pop()  # remove the no-op

# #770 metonymy — replace literal-crown distractors with figurative options
q770 = bank[770]
FIXES.append({
    "idx": 770,
    "patch": {
        "choices": [
            q770["answer"],  # keep answer
            "The royal household staff who serve the monarch personally",
            "The British government's ministers and civil service as a whole",
            "The constitution and the body of unwritten laws of England",
        ],
    },
    "reason": "Replace literal-crown distractors with strong metonymy-confusion options that genuinely contest the answer.",
})

# Validate every fix
dup, ans = build_bank_indices(bank)
print(f"Applying {len(FIXES)} grammar fixes...\n")

results = {"applied": [], "failed": [], "deferred": []}

for fix in FIXES:
    idx = fix["idx"]
    patch = fix["patch"]
    if patch is None:
        results["deferred"].append((idx, fix["reason"]))
        continue

    q_new = dict(bank[idx])
    for k, v in patch.items():
        q_new[k] = v

    # If choices changed and answer is now first item, sync
    if "choices" in patch and "answer" not in patch:
        # Keep existing answer text; verify it's in the new choices
        if q_new["answer"] not in q_new["choices"]:
            results["failed"].append((idx, f"answer not in new choices: {q_new['answer']}"))
            continue

    r = validate_rewrite("grammar", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        bank[idx] = q_new
        results["applied"].append((idx, fix["reason"], r["verdict"]))
        # Rebuild indices after each apply
        dup, ans = build_bank_indices(bank)
    else:
        results["failed"].append((idx, [f"{g}: {r[:200]}" for g, r in r["hard_fails"]]))

print(f"Applied: {len(results['applied'])}")
print(f"Failed: {len(results['failed'])}")
print(f"Deferred: {len(results['deferred'])}")

print("\n=== APPLIED ===")
for idx, reason, verdict in results["applied"]:
    print(f"  #{idx} [{verdict}]: {reason}")

if results["failed"]:
    print("\n=== FAILED ===")
    for idx, reasons in results["failed"]:
        print(f"  #{idx}: {reasons}")

if results["deferred"]:
    print("\n=== DEFERRED ===")
    for idx, reason in results["deferred"]:
        print(f"  #{idx}: {reason}")

# Write bank only if any applied
if results["applied"]:
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {BANK_PATH}")
else:
    print("\nNo changes applied; bank not written")
