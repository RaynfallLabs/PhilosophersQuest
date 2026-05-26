"""Fix the 6 truncated T3 questions in data/questions/ai.json.

For each:
- Trim stem to give budget headroom
- Complete the answer (and any truncated distractor)
- Validate against AI gate suite
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK = REPO / "data" / "questions" / "ai.json"
bank = json.loads(BANK.read_text(encoding="utf-8"))

# Identify each by truncated answer fragment (unique enough)
fixes = [
    # T3#128 — AlphaFold protein database
    {
        "find_substring": "researchers design dru",
        "new": {
            "tier": 3,
            "question": "DeepMind's AlphaFold released 3D structures for about 200 million proteins in 2021 — essentially every known protein in nature. Before AlphaFold, mapping one took a PhD student years. Why is this a leap for medicine?",
            "answer": "A drug works by binding to a protein's shape, knowing the shape lets researchers design drugs that fit",
            "choices": [
                "A drug works by binding to a protein's shape, knowing the shape lets researchers design drugs that fit",
                "Every protein in the body emits a unique signal that the drug then amplifies once injected",
                "The database tells doctors which patients have which proteins, so prescriptions become custom",
                "Pharmaceutical labs can skip clinical trials once a protein's structure has been mapped by AI",
            ],
            "context": "AlphaFold 2, from DeepMind, solved a problem biologists had worked on for 50 years: predicting how a chain of amino acids folds into a 3D shape. Drug design starts from the target protein's shape — the drug must fit precisely into it. With a database of 200 million predicted shapes, researchers can screen drug candidates much faster than waiting for traditional X-ray crystallography.",
        },
    },
    # T3#130 — AlphaFold predict vs simulate
    {
        "find_substring": "chemistry of fol",
        "new": {
            "tier": 3,
            "question": "AlphaFold doesn't physically fold proteins. It predicts the final 3D shape from the amino-acid sequence using a neural network trained on known structures. Why is calling it 'protein folding' a bit misleading?",
            "answer": "It learned to predict the answer from many examples, it doesn't simulate the chemistry of folding",
            "choices": [
                "It learned to predict the answer from many examples, it doesn't simulate the chemistry of folding",
                "It physically folds the protein in a tiny lab on a chip, then photographs the result for the output",
                "It refuses to predict any protein that hasn't already been solved by traditional X-ray crystallography",
                "It performs a quantum-mechanical simulation that traces every atom's motion through the folding process",
            ],
            "context": "The Protein Data Bank holds tens of thousands of experimentally determined protein structures. AlphaFold trained on these — learning the relationship between amino-acid sequence and 3D shape. At inference time it predicts; it does not simulate the physics of folding. This is faster but means it can fail on proteins very unlike anything in its training data.",
        },
    },
    # T3#138 — Diffusion mechanism
    {
        "find_substring": "noise becomes a crea",
        "new": {
            "tier": 3,
            "question": "Modern AI image generators (DALL-E, Stable Diffusion, Midjourney) use 'diffusion.' The model starts with TV static and gradually removes the noise, step by step, until a clean image appears. Why does this work?",
            "answer": "Learning to clean up noise teaches the model what real images look like, so noise becomes a creative starting point",
            "choices": [
                "Learning to clean up noise teaches the model what real images look like, so noise becomes a creative starting point",
                "Static is actually compressed image data, and diffusion just unpacks it back into the original photo",
                "The noise is randomly chosen from real photos, and the model is just blending those photos together",
                "Diffusion models steal pixels from the training set and rearrange them into the requested image",
            ],
            "context": "Diffusion models are trained on a clever flip: take a real image, add noise to it step by step, then teach the network to reverse the process — predicting how to remove noise. After training, you start with pure noise and apply the network repeatedly, guided by a text prompt. Each step the image becomes a bit more like 'what the prompt described.'",
        },
    },
    # T3#143 — Diabetic retinopathy screening
    {
        "find_substring": "and the AI catches the ",
        "new": {
            "tier": 3,
            "question": "Google Health's AI flags retinal images that show signs of diabetic retinopathy. It's used as a screening tool in clinics in India and Thailand, where specialists are scarce. What does the AI specifically do in this deployment?",
            "answer": "Filters who needs to see a specialist next, most retinas are normal and the AI catches the high-risk ones",
            "choices": [
                "Filters who needs to see a specialist next, most retinas are normal and the AI catches the high-risk ones",
                "Treats the retinal damage directly using laser commands sent through the camera lens",
                "Replaces all eye specialists in those countries permanently, eliminating the need for any doctors",
                "Refunds the patient automatically if their eyes turn out to be healthy after the scan",
            ],
            "context": "Diabetic retinopathy is a major cause of blindness — early treatment prevents it. Screening requires an expert reading the retinal image. In countries where the ophthalmologist-to-patient ratio is too low for everyone to be screened, AI triage catches the suspicious images and sends only those to a human specialist. Most retinas come back normal; the AI's job is filtering, not treating.",
        },
    },
    # T3#150 — Satellite agriculture (also fix truncated C2 "that fi")
    {
        "find_substring": "see things at fie",
        "new": {
            "tier": 3,
            "question": "Government Landsat satellite imagery used to come monthly. Now Planet Labs's hundreds of small satellites image every spot on Earth daily, and AI processes the images to spot crop stress and deforestation. What's the recognition for modern agriculture?",
            "answer": "Daily satellite imagery + AI lets farmers see things at field scale that would have been impossible before",
            "choices": [
                "Daily satellite imagery + AI lets farmers see things at field scale that would have been impossible before",
                "Modern agriculture has completely stopped using human farmers in every country worldwide",
                "Every field in the world is watched continuously by government drones that fly overhead",
                "Satellites cannot see anything through clouds, so the new imagery only works on sunny days",
            ],
            "context": "Daily-revisit satellite imagery — combined with AI image processing — gives a farmer information her grandparents would have called miraculous: which fields are water-stressed, where pests are spreading, which patches need fertilizer. The same imagery and AI also serve conservation groups tracking deforestation, urban planners watching new construction, and journalists verifying war damage.",
        },
    },
    # T3#154 — Tesla FSD (fix only truncated C2 "for the full duration of th")
    {
        "find_substring": "for the full duration of th",
        "new": {
            "tier": 3,
            "question": "Tesla's 'Full Self-Driving' (FSD) is sold to retail buyers. The system requires the driver's hands on the wheel — it's classified as Level 2 (driver assistance, not autonomous). The marketing name suggests something stronger. Why is this a defensive recognition issue?",
            "answer": "Drivers who believe a Level 2 system is fully autonomous may stop paying attention, and crash",
            "choices": [
                "Drivers who believe a Level 2 system is fully autonomous may stop paying attention, and crash",
                "Tesla owners can legally remove all safety features if they don't like how the car drives",
                "FSD makes the car immune to all rear-end collisions for the full duration of the trip",
                "Tesla provides personal chauffeurs at no cost to anyone who buys a vehicle with FSD enabled",
            ],
            "context": "The Society of Automotive Engineers defines levels 0-5 of automation. Tesla FSD is Level 2: the driver must remain attentive. The naming creates a mismatch between what buyers expect ('full self-driving') and the system's actual capability. NHTSA investigations have documented crashes where drivers were not paying attention, trusting the marketing language over the actual operating envelope.",
        },
    },
]

print("Applying 6 truncation fixes...")
for fix in fixes:
    needle = fix["find_substring"]
    found_idx = None
    for i, q in enumerate(bank):
        if needle in q.get("answer", ""):
            found_idx = i
            break
        hit_in_choice = False
        for c in q.get("choices", []):
            if needle in c:
                hit_in_choice = True
                break
        if hit_in_choice:
            found_idx = i
            break
    if found_idx is None:
        print(f"  ?? Could not find: {needle!r}")
        continue
    print(f"  bank#{found_idx}: matched {needle!r} -> replacing")
    bank[found_idx] = fix["new"]

# Validate
print()
print("Re-validating full bank...")
dup, ans = build_bank_indices(bank)
pass_c = fail_c = soft_c = 0
fails = []
for i, q in enumerate(bank):
    r = validate_rewrite("ai", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=i)
    if r["verdict"] == "FAIL":
        fail_c += 1
        fails.append((i, q.get("question", "")[:80], r["hard_fails"]))
    else:
        pass_c += 1
        if r["verdict"] == "SOFT_WARN":
            soft_c += 1

print(f"  PASS: {pass_c} (incl. {soft_c} soft-warn)")
print(f"  FAIL: {fail_c}")
if fails:
    print("  Failure detail:")
    for i, stem, hf in fails[:10]:
        print(f"    bank#{i}: {stem!r}")
        for g, reason in hf[:3]:
            print(f"      - {g}: {reason}")

if fail_c == 0:
    BANK.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print()
    print(f"  OK Wrote {BANK} with all fixes")
else:
    print()
    print("  FAIL Validation failures - NOT writing. Investigate above.")
