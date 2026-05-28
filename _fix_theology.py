"""Phase E theology fixes: criticals + factuals + Christian-doctrinal stance + parens skim-tells."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/theology.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))


# --- Define each fix as a dict of patches applied directly to question ---

FIXES = []

# === CRITICAL #4: Noah dove second trip not third ===
FIXES.append({
    "idx": 4,
    "patch": {
        "question": "After the flood, Noah sent a bird out from the ark three times to see if dry land had appeared. The second time the bird returned with an olive leaf in its beak; the third time it did not return at all. What kind of bird was it?",
    },
    "reason": "Fix factual error: dove returned with olive leaf on SECOND trip, not third (Genesis 8).",
})

# === CRITICAL #27: Drop 'fulfilling the prophecy of Micah' + parens gloss ===
FIXES.append({
    "idx": 27,
    "patch": {
        "answer": "A manger",
        "choices": [
            "A manger",
            "A cradle in the innkeeper's loft",
            "A wooden basket beside the door",
            "A bed of straw on the temple floor",
        ],
        "context": "The story is in Luke 2. A manger is a feeding trough where animals are kept. The Gospels do not specify a stable. The town was Bethlehem, where King David had also been born — Matthew's Gospel notes the connection to Micah 5:2.",
    },
    "reason": "Drop 'fulfilling the prophecy' Christian-doctrinal framing + drop parens-skim-tell gloss.",
})

# === FACTUAL #16: Delilah was lover, not wife ===
FIXES.append({
    "idx": 16,
    "patch": {
        "question": bank[16]["question"].replace("His Philistine wife Delilah", "His Philistine lover Delilah"),
    },
    "reason": "Fix factual: Delilah was Samson's lover (Judges 16:4), not his wife.",
})

# === FACTUAL #21: Bathsheba bathing — David on the roof, not Bathsheba ===
FIXES.append({
    "idx": 21,
    "patch": {
        "question": "King David, from the roof of his palace, saw a beautiful woman bathing below. He arranged for her husband to be killed in battle so he could marry her. What was the woman's name?",
    },
    "reason": "Fix factual: David was on the rooftop (2 Sam 11:2), not Bathsheba.",
})

# === FACTUAL #765: Same Bathsheba-rooftop fix ===
FIXES.append({
    "idx": 765,
    "patch": {
        "question": bank[765]["question"].replace("a beautiful woman bathing on a rooftop", "from his palace roof a beautiful woman bathing below"),
    },
    "reason": "Fix factual: David on roof, not Bathsheba.",
})

# === FACTUAL #495: Frigg golden tears → attributed correctly ===
FIXES.append({
    "idx": 495,
    "patch": {
        "question": "Odin's wife was the queen of Asgard and the goddess of marriage. She traveled the nine worlds extracting promises that nothing would harm her beloved son Balder. Who was she?",
        "context": "Frigg lived in Fensalir, the marsh-hall. She knew the fate of all things but rarely spoke of what she knew. The 'tears of red gold' detail in the Eddas actually belongs to Freyja (weeping gold for her absent husband Od), not Frigg.",
    },
    "reason": "Fix factual: 'golden tears' is Freyja's trademark, not Frigg's.",
})

# === STANCE #29: myrrh foreshadowing — strip or attribute ===
FIXES.append({
    "idx": 29,
    "patch": {
        "context": "The story is in Matthew 2. The wise men (or Magi) are traditionally named Caspar, Melchior, and Balthazar. Gold honored a king, frankincense honored a priest, and myrrh was a burial spice — a detail Christian tradition later read as pointing to his death.",
    },
    "reason": "Attribute the myrrh-foreshadowing reading to 'Christian tradition' (not unattributed).",
})

# === STANCE #65: Akedah foreshadowing — attribute ===
FIXES.append({
    "idx": 65,
    "patch": {
        "context": "God provided the ram caught in a thicket as the substitute sacrifice. Christian readers have long interpreted Isaac on the wood as a parallel to Jesus carrying the cross. The same hill in Jerusalem is traditionally identified as both Moriah and Golgotha.",
    },
    "reason": "Strip devotional capitalization + parens; attribute to Christian readers.",
})

# === STANCE #71: lamb's blood foreshadowing — attribute ===
FIXES.append({
    "idx": 71,
    "patch": {
        "context": bank[71].get("context", "").replace(
            "Christians see the lamb's blood as a foreshadowing of Christ, 'the Lamb of God.'",
            "Christian tradition later read the Passover lamb's blood as pointing to Jesus, called 'the Lamb of God' in the Gospel of John."
        ),
    },
    "reason": "Attribute to 'Christian tradition' + reframe as parallel reading, not doctrinal foreshadowing.",
})

# === STANCE #91: myrrh foreshadowing — drop or attribute ===
FIXES.append({
    "idx": 91,
    "patch": {
        "context": bank[91].get("context", "").replace(
            "myrrh — a burial spice — foreshadowed Jesus's death.",
            "myrrh was a burial spice — a detail Christian tradition later read as pointing to his death."
        ),
    },
    "reason": "Attribute the myrrh-foreshadowing to Christian tradition.",
})

# === STANCE #131: Isaac wood foreshadowing — attribute ===
FIXES.append({
    "idx": 131,
    "patch": {
        "context": bank[131].get("context", "").replace(
            "Christians from the earliest centuries read Isaac carrying the wood up the mountain as a foreshadowing of Christ carrying the cross.",
            "Christian readers from early centuries drew a parallel between Isaac carrying the wood and Jesus carrying the cross — one of Christianity's oldest typological readings."
        ),
    },
    "reason": "Reframe foreshadowing as Christian-typological reading.",
})

# === STANCE #799: myrrh foreshadowing — attribute ===
FIXES.append({
    "idx": 799,
    "patch": {
        "context": bank[799].get("context", "").replace(
            "myrrh (used to embalm) foreshadowing his death.",
            "myrrh was used to embalm — a detail Christian tradition later read as pointing to his death."
        ),
    },
    "reason": "Attribute myrrh-foreshadowing to Christian tradition.",
})

# === STANCE #721: Isaac wood vs cross — attribute ===
FIXES.append({
    "idx": 721,
    "patch": {
        "context": bank[721].get("context", "").replace(
            "has been read across Christian centuries as the figure of Jesus carrying his cross up Golgotha",
            "has been read for centuries by Christian commentators as a parallel to Jesus carrying his cross up Golgotha"
        ),
    },
    "reason": "Tighten attribution phrasing.",
})

# === STANCE #538: Friday Frigg/Freyja ambiguity — tighten ===
FIXES.append({
    "idx": 538,
    "patch": {
        "context": "Wednesday is Wodan's day (Odin's). Friday derives from Old English Frigedæg, named for Frigg. (Some later Germanic sources confused Frigg with Freyja, but the English day-name traces specifically to Frigg.)",
    },
    "reason": "Tighten Frigg/Freyja ambiguity to scholarly consensus.",
})

# === PARENS-DECO #32: 'Men (people, souls)' → 'Fishers of men' ===
FIXES.append({
    "idx": 32,
    "patch": {
        "answer": "Fishers of men",
        "choices": [
            "Fishers of men",
            "Birds in nets of light",
            "The kingdoms of the world",
            "Sins from human hearts",
        ],
    },
    "reason": "Strip parens-decoration; use 'Fishers of men' as the iconic answer.",
})

# === PARENS-DECO #46: Golgotha + parallel parens on distractors ===
FIXES.append({
    "idx": 46,
    "patch": {
        "choices": [
            "Golgotha (the Place of the Skull)",
            "Mount Sinai (the desert mount)",
            "Mount Carmel (Elijah's mount)",
            "Mount of Olives (the Garden mount)",
        ],
    },
    "reason": "Add parallel parens to distractors for shape parity.",
})

# === PARENS-DECO #449: drop (krotala) gloss ===
FIXES.append({
    "idx": 449,
    "patch": {
        "answer": "A bronze rattle that made an unbearable clattering noise",
        "choices": [
            "A bronze rattle that made an unbearable clattering noise",
            "A silver hunting horn whose blast deafened all within a mile",
            "A wooden flute that played a tune the birds could not bear",
            "A polished mirror that blinded the birds with sunlight",
        ],
        "context": (bank[449].get("context", "") + " The Greek krotala (rattles) were forged for him by Hephaestus, the smith-god."),
    },
    "reason": "Drop (krotala) parens; move Greek term to context.",
})

# === PARENS-DECO #452: drop hedge ===
FIXES.append({
    "idx": 452,
    "patch": {
        "answer": "Six pomegranate seeds, one for each winter month",
        "choices": [
            "Six pomegranate seeds, one for each winter month",
            "Twelve seeds, one for each month of the year",
            "Three seeds, matching the three Fates of myth",
            "Nine seeds, matching the nine Muses of Helicon",
        ],
    },
    "reason": "Drop hedge; commit to six (the most common version) with month-link context.",
})

# === PARENS-DECO #567: drop (same as goddess's name) ===
FIXES.append({
    "idx": 567,
    "patch": {
        "answer": "Hel, sharing the name of its goddess",
        "choices": [
            "Hel, sharing the name of its goddess",
            "Niflheim, the world of mist and ice",
            "Muspelheim, the realm of primal fire",
            "Svartalfheim, the deep mines of the dwarfs",
        ],
    },
    "reason": "Replace parens-hedge with parallel descriptive shape.",
})

# === PARENS-DECO #581: drop (with their father Njord) ===
FIXES.append({
    "idx": 581,
    "patch": {
        "answer": "Freyja, her brother Freyr, and their father Njord",
        "choices": [
            "Freyja, her brother Freyr, and their father Njord",
            "Loki, his mother Laufey, and the giantess line",
            "Hel, her brother Fenrir, and the wolf Garm",
            "Heimdall, his nine giantess mothers, and the shore",
        ],
    },
    "reason": "Strip parens; rewrite to parallel triple-name shape.",
})

# === PARENS-DECO #761: drop (a gentle whisper) ===
FIXES.append({
    "idx": 761,
    "patch": {
        "answer": "A still small voice",
        "choices": [
            "A still small voice",
            "A blinding light brighter than the noon sun",
            "A great voice like the roar of many waters",
            "A clap of thunder that shook the mountain",
        ],
    },
    "reason": "Drop parens gloss; iconic phrase stands alone.",
})

# === PARENS-DECO #763: commit to one weapon ===
FIXES.append({
    "idx": 763,
    "patch": {
        "answer": "Held a sword in the other",
        "choices": [
            "Held a sword in the other",
            "Carried a torch to light the work after dark",
            "Held a water-jar to wet the mortar quickly",
            "Held a horn ready to sound the alarm",
        ],
    },
    "reason": "Commit to sword (the canonical Nehemiah 4:17-18 image).",
})

# === PARENS-DECO #755: drop (the Law) (the Prophets) ===
FIXES.append({
    "idx": 755,
    "patch": {
        "answer": "Moses and Elijah — and the voice said: This is my beloved Son, listen to him",
        "choices": [
            "Moses and Elijah — and the voice said: This is my beloved Son, listen to him",
            "Abraham and David — and the voice said: Behold my chosen, in whom I delight",
            "Adam and Noah — and the voice said: This is the second Adam, the heir of all",
            "Isaiah and Jeremiah — and the voice said: Hear the prophet I have raised up",
        ],
        "context": "Moses (representing the Law) and Elijah (representing the Prophets) appeared with Jesus on the mountain — the canonical visual of all three Hebrew Bible categories converging on him. The mountain is traditionally identified with Mount Tabor in Galilee or sometimes Mount Hermon. Both Moses and Elijah had unusual departures (Moses buried by God, Elijah taken up in a chariot of fire). Jesus told the three disciples not to tell anyone of the vision until after his resurrection.",
    },
    "reason": "Drop in-answer parens; move Law/Prophets explanation to context.",
})

# === PARENS-DECO #978: drop (chessmen) ===
FIXES.append({
    "idx": 978,
    "patch": {
        "answer": "The golden gaming pieces the Aesir had owned before Ragnarok",
        "choices": [
            "The golden gaming pieces the Aesir had owned before Ragnarok",
            "Mimir's severed head, still whispering wisdom from the earth",
            "Odin's eye, returned from the bottom of Mimir's well",
            "Bragi's harp, untouched by the flames of Surt's burning sword",
        ],
    },
    "reason": "Drop (chessmen) parens; clean parallel shape.",
})


# --- Apply ---
dup, ans = build_bank_indices(bank)
print(f"Applying {len(FIXES)} theology fixes...\n")

results = {"applied": [], "failed": []}
for fix in FIXES:
    idx = fix["idx"]
    q_new = dict(bank[idx])
    for k, v in fix["patch"].items():
        q_new[k] = v
    r = validate_rewrite("theology", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        bank[idx] = q_new
        results["applied"].append((idx, fix["reason"], r["verdict"]))
        dup, ans = build_bank_indices(bank)
    else:
        results["failed"].append((idx, [f"{g}: {reason[:200]}" for g, reason in r["hard_fails"]]))

print(f"Applied: {len(results['applied'])}")
print(f"Failed: {len(results['failed'])}")

print("\n=== APPLIED ===")
for idx, reason, verdict in results["applied"]:
    print(f"  #{idx} [{verdict}]: {reason}")

if results["failed"]:
    print("\n=== FAILED ===")
    for idx, reasons in results["failed"]:
        print(f"  #{idx}: {reasons}")

if results["applied"]:
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {BANK_PATH}")
