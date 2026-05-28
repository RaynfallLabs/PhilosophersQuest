"""Phase E cooking fixes: 8 critical truncations + 16 c[i] mid-phrase cuts + weasel closers."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/cooking.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))


def replace_closer(stem: str, new_closer: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', stem.rstrip())
    for i in range(len(sentences) - 1, -1, -1):
        if sentences[i].rstrip().endswith('?'):
            sentences[i] = new_closer
            break
    return ' '.join(sentences)


FIXES = []

# === CRITICAL TRUNCATIONS — rewrite to complete phrases that fit cap ===

# #372 T1 — distractors cut: complete them shorter
FIXES.append({
    "idx": 372,
    "patch": {
        "choices": [
            "Metal carries heat much faster along its length than wood",
            "Wood is hollow inside, so heat fills the space and dissipates",
            "Metal handles glow invisibly hot and warm your hand from afar",
            "Wood actively cools itself by releasing tiny puffs of water",
        ],
    },
    "reason": "Complete 3 truncated distractors (#372 T1).",
})

# #416 T3 — answer cut at "across the": complete + tighten distractors
FIXES.append({
    "idx": 416,
    "patch": {
        "answer": "Sous-vide gives uniform doneness with no smoke flavor; smoke brings flavor and texture variation",
        "choices": [
            "Sous-vide gives uniform doneness with no smoke flavor; smoke brings flavor and texture variation",
            "Sous-vide builds a thicker bark on the surface while smoking keeps the exterior pale and gel-like",
            "Sous-vide develops more pronounced Maillard during the bath while smoking depends on the brief sear",
            "Sous-vide reduces total cook time because the bath runs hotter than the smoker",
        ],
    },
    "reason": "Complete truncated answer #416 T3.",
})

# #447 T4 — answer cut: complete
FIXES.append({
    "idx": 447,
    "patch": {
        "answer": "Pho chars ginger and onion and uses star anise/cinnamon with obsessive fat-skimming for clarity",
        "choices": [
            "Pho chars ginger and onion and uses star anise/cinnamon with obsessive fat-skimming for clarity",
            "Pho cooks at a rolling boil for clarity while pot-au-feu uses a low simmer for depth",
            "Pho uses only oxtail and rib bones while pot-au-feu uses shank and brisket",
            "Pho adds lime juice at the table while pot-au-feu adds vinegar early in the simmer",
        ],
    },
    "reason": "Complete truncated answer + distractor #447 T4.",
})

# #450 T4 — all 4 choices cut; rewrite with compact completions
FIXES.append({
    "idx": 450,
    "patch": {
        "answer": "Tradition appeal — invoking long cultural history of fire-cooking as a legitimacy claim",
        "choices": [
            "Tradition appeal — invoking long cultural history of fire-cooking as a legitimacy claim",
            "Bastiat seen-vs-unseen — pointing to invisible smoke compounds that sous-vide silently omits",
            "Sowell compared-to-what — challenging sous-vide to specify what it improves on against fire",
            "Pollan food-like substances — relabeling sous-vide output as not actually cooking at all",
        ],
    },
    "reason": "Complete 4 truncated choices #450 T4.",
})

# #458 T4 — answer cut at "the unstable"
FIXES.append({
    "idx": 458,
    "patch": {
        "answer": "Beta-V cocoa butter crystals — stable, tightly packed; tempering selects this over unstable forms",
        "choices": [
            "Beta-V cocoa butter crystals — stable, tightly packed; tempering selects this over unstable forms",
            "Sucrose crystals fine and even — tempering controls sugar crystallization, not cocoa butter",
            "Milk-fat globules dispersed in cocoa solid — tempering breaks up globule clusters in milk chocolate",
            "Casein-bound chocolate liquor — tempering activates the protein matrix in milk chocolate only",
        ],
    },
    "reason": "Complete truncated answer #458 T4.",
})

# #477 T5 — answer cut at "salsa"
FIXES.append({
    "idx": 477,
    "patch": {
        "answer": "Dry-heat toasting of chiles, seeds, and tortillas — Maillard browning central to mole and salsa",
        "choices": [
            "Dry-heat toasting of chiles, seeds, and tortillas — Maillard browning central to mole and salsa",
            "Slow simmering of stews and pozole — the comal enabled long liquid dishes for daily Mesoamerican eating",
            "Roasting whole meats over an open surface — the comal allowed cooks to roast turkey and game directly",
            "Steaming tamales above heated water — the comal generated steam that cooked masa-wrapped fillings",
        ],
    },
    "reason": "Complete truncated answer + distractor #477 T5.",
})

# #482 T5 — all 4 choices cut; trim back
FIXES.append({
    "idx": 482,
    "patch": {
        "answer": "Higher temperature (116C) accelerates Maillard 4-8x and seals aromas; loses slow enzymatic effects",
        "choices": [
            "Higher temperature (116C) accelerates Maillard 4-8x and seals aromas; loses slow enzymatic effects",
            "Higher pressure forces water into meat and speeds collagen; loses slow-reduction flavor concentration",
            "Higher pressure tightens fibers and intensifies salt; loses the silky texture of long gentle simmering",
            "Higher boiling point sterilizes pathogens faster; loses slow aromatic development from open-air contact",
        ],
    },
    "reason": "Complete 4 truncated choices #482 T5.",
})

# #492 T5 — answer cut at "fast-grilled"
FIXES.append({
    "idx": 492,
    "patch": {
        "answer": "Category boundary defense — 'barbecue' names a technique (long slow smoke), not fast-grill meat",
        "choices": [
            "Category boundary defense — 'barbecue' names a technique (long slow smoke), not fast-grill meat",
            "Bastiat seen-vs-unseen — pointing to invisible pitmaster hours that fast-grill marketing hides",
            "Sowell compared-to-what — challenging fast-grill chains to specify what they actually improve on",
            "Pollan food-like substances — arguing fast-grill output is barbecue-like but not actually barbecue",
        ],
    },
    "reason": "Complete truncated answer #492 T5.",
})


# === DISTRACTOR-ONLY MID-PHRASE CUTS (WARN) — patch the cut c[i] ===

DISTRACTOR_FIXES = {
    # idx: dict of choice_index -> new_text
    449: {
        0: "Gluten development must be minimized; overworking builds elastic gluten that traps oil; cold and few strokes keep gluten low",
        1: "Egg yolk fat must coat each flour particle; overworking emulsifies the yolk past usefulness; cold water preserves the coat",
        2: "Oil temperature must penetrate fully; cold batter cools oil at first contact; few strokes prevent batter compacting on heat",
        3: "Egg white foam must trap air; overworking deflates the foam; cold water keeps foam structure for the airy crisp texture",
    },
    451: {
        3: "Yeast in the dough keeps rising at high heat; at lower oven heat the yeast dies too soon for the airy crust",
    },
    455: {
        1: "Whole spices are too hard to chew raw; brief hot-oil softens them so the diner doesn't bite into a hard seed",
    },
    464: {
        2: "Salt brine adds dietary minerals to the cucumber; the mineral content of a fermented pickle is higher than a fresh one",
    },
    469: {
        2: "All three are the same chemistry at progressively higher temperatures; the names just label different visible stages of browning",
    },
    471: {
        3: "Coastal access to seafood meant pork was a secondary protein; vinegar imitated the bright acid of seaside cuisine for the table",
    },
    473: {
        2: "Surface protein denaturation forms a sealing band that blocks heat penetration — the wrap conducts heat around the seal",
        3: "Maillard reaction consumes energy as it produces bark — the wrap stops further Maillard so heat goes into raising temperature",
    },
    476: {
        1: "Sugar must dissolve fully (slow churning) while fat must separate cleanly (fast freezing); both decide richness versus iciness",
    },
    478: {
        1: "Brisket: complete drying of the surface to dense bark; char siu: complete hydration through a wet glaze that prevents Maillard",
    },
    484: {
        2: "Recognize that fast-grill is a modern industrial invention while slow-smoke is the only authentic barbecue tradition that endures",
    },
    486: {
        3: "Alkaloid compounds resembling pepper-and-chile heat compounds contributing the warm character; lignin gives color but not flavor",
    },
    489: {
        1: "Claim: traditional cooking is wrong and should be replaced by laboratory methods; critique: tradition produced good food for ages",
        2: "Claim: home cooks should buy equipment to match restaurants; critique: the gear is too expensive and methods are impractical at home",
    },
    491: {
        1: "Quick fermentation of imported wheat satisfies modern needs — injera adapts older techniques into a faster preparation appearance",
        3: "Religious calendar dictates fasting days when injera replaces meat — the bread otherwise takes on religious meaning during fasts",
    },
    493: {
        2: "Wealthy diners pay premiums for rare experiences — fugu persists because affluent consumers seek novelty rather than safety",
    },
    494: {
        3: "Methyl groups dissolve in oil at 50C — chains form an oil-trapping network when heated and the gel forms because oil is held there",
    },
    731: {
        1: "Pre-industrial sausage was a luxury food limited to nobility; regional density reflects court cuisines competing for prestige at courts",
    },
}

for idx, choice_patches in DISTRACTOR_FIXES.items():
    q = bank[idx]
    new_choices = list(q["choices"])
    for ci, new_text in choice_patches.items():
        new_choices[ci] = new_text
    # If we patched the answer position, update answer
    new_answer = q["answer"]
    if q["answer"] in q["choices"]:
        ans_idx = q["choices"].index(q["answer"])
        if ans_idx in choice_patches:
            new_answer = choice_patches[ans_idx]
    FIXES.append({
        "idx": idx,
        "patch": {"choices": new_choices, "answer": new_answer},
        "reason": f"Complete {len(choice_patches)} mid-phrase distractor cut(s).",
    })


# === WEASEL CLOSERS — replace with pointed concrete questions ===
WEASEL_REWRITES = [
    (39, "What single thing is the high temperature doing differently from the lower temperature?"),
    (70, "What specifically happens to chicken muscle proteins above about 70C?"),
    (303, "What does the pinch test on the chicken thigh actually measure?"),
    (319, "What changes inside an egg between 62C and 68C that pasteurization without scrambling exploits?"),
    (321, "What does emulsification accomplish between oil droplets and yolk lecithin?"),
    (325, "What does kneading bread dough physically build up that no-knead doughs build by time alone?"),
    (334, "What does cold-water marination accomplish that hot marinades cannot?"),
    (345, "What three measurable variables does sous-vide pin down that open-flame cooking cannot?"),
    (352, "What molecular event happens when collagen passes about 60C and starts converting to gelatin?"),
    (357, "What does dry-brining a steak overnight do to surface moisture and salt distribution?"),
    (358, "What specific protein change does smoke deposition trigger on the meat surface?"),
    (562, "What does the 50C poaching temperature do to the egg white versus the yolk?"),
    (590, "What chemical change does fermentation drive that ordinary salting cannot?"),
    (598, "What does retrograded starch in cooled rice or potato do that fresh-cooked starch does not?"),
    (609, "What specific reaction does roasting coffee at about 200C trigger inside the bean?"),
    (705, "What does scoring fat-side of pork belly do that simple seasoning does not?"),
    (716, "What does aging beef for 30 days accomplish through enzymatic action?"),
    (722, "What does the maturation of a hard cheese over months do to its protein structure?"),
    (799, "What does the autolyse rest period do to flour and water before kneading begins?"),
    (826, "What does whipping cream physically do to the fat globules between the whisks?"),
    (942, "What does brining a turkey overnight change about its meat-protein structure?"),
    (948, "What specific texture change does buttermilk produce in fried chicken batter?"),
    (954, "What does deglazing the pan capture that would otherwise be lost?"),
    (965, "What single chemical advantage does cooking eggplant in salt-water brine first provide?"),
    (969, "What does blooming dry spices in hot oil release that cold-mixing cannot?"),
    (971, "What does the kombu and bonito dashi extract chemically that water alone cannot?"),
    (972, "What does the long-fermentation sourdough do to wheat that fast yeast cannot?"),
    (974, "What chemical work does fish sauce fermentation perform on anchovies over months?"),
    (978, "What does long pressure-cooking do to bone collagen that open simmering cannot match in hours?"),
    (986, "What does the careful tempering of chocolate select for at the crystal level?"),
    (988, "What does enzymatic browning on a cut apple actually do at the cell level?"),
]

for idx, new_closer in WEASEL_REWRITES:
    old_stem = bank[idx]["question"]
    new_stem = replace_closer(old_stem, new_closer)
    FIXES.append({
        "idx": idx,
        "patch": {"question": new_stem},
        "reason": f"Replace §15 weasel: {new_closer[:60]}...",
    })


# === APPLY ===
dup, ans = build_bank_indices(bank)
print(f"Applying {len(FIXES)} cooking fixes...\n")

results = {"applied": [], "failed": []}
for fix in FIXES:
    idx = fix["idx"]
    q_new = dict(bank[idx])
    for k, v in fix["patch"].items():
        q_new[k] = v
    r = validate_rewrite("cooking", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        bank[idx] = q_new
        results["applied"].append((idx, fix["reason"], r["verdict"]))
        dup, ans = build_bank_indices(bank)
    else:
        results["failed"].append((idx, [f"{g}: {reason[:200]}" for g, reason in r["hard_fails"]]))

print(f"Applied: {len(results['applied'])}")
print(f"Failed: {len(results['failed'])}")

if results["failed"]:
    print("\n=== FAILED ===")
    for idx, reasons in results["failed"]:
        print(f"  #{idx}: {reasons}")

if results["applied"]:
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {BANK_PATH}")
