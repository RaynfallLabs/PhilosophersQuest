"""Apply the 6 moral-vision audit fixes to the cooking ladders.

DROPS (3) -- SHARED_PRINCIPLES §18 adjacency drift: the keyed answer IS a regulatory action and
every choice is a policy instrument, so the rung tests government rulemaking, not food. §18 says
that substance belongs in history/economics -> drop the rung.

EDITS (3) -- stance symmetry + reveal-staging, per moral_vision §3.10 / §6.

Usage: python bankbuild/cooking/_apply_moral_fixes.py
"""
import json, os

LAD = r"C:\Users\brand\Documents\PhilosophersQuest\bankbuild\cooking\ladders"

DROPS = [
    ("trans-fats-the-health-food-that-was-the-poison", 7),   # ans 'Banned it from the food supply'
    ("butter-margarine-and-the-fat-wars", 4),                # ans 'banned it outright'
    ("the-56-disguises-of-sugar", 9),                        # ans 'regulate it like tobacco and alcohol'
]

# (id, idx, field, find, replace)
EDITS = [
    # stance asymmetry: closed the sat-fat question as settled while leaving sugar's open
    ("sugar-vs-fat-who-was-the-real-villain", 9, "context",
     "yet saturated fat and cholesterol remain genuine cardiovascular risk factors",
     "yet both questions stay live: the mainstream still counts saturated fat and cholesterol as "
     "cardiovascular risk factors, while later meta-analyses (Siri-Tarino 2010, Chowdhury 2014) "
     "failed to confirm that link"),
    # stance: handed the baton to the next orthodoxy as flat fact
    ("cholesterol-and-the-eggs-comeback", 5, "context",
     "That shift in understanding is a big part of why the old cholesterol limit was dropped.",
     "That shift in understanding is a big part of why the old cholesterol limit was dropped. "
     "Worth knowing: that is about LDL specifically. Whether raising LDL this way actually drives "
     "heart disease is itself a live debate -- later meta-analyses (Siri-Tarino 2010, Chowdhury 2014) "
     "failed to confirm the link -- so the saturated-fat story is contested, not closed."),
    # reveal-staging ('TIL: X is secretly bad'), twice over
    ("what-organic-really-means", 4, "stem",
     "Here's what surprises people: 'organic' does not mean pesticide-free. Organic farmers do spray",
     "'Organic' does not mean pesticide-free: organic farmers do spray"),
    ("what-organic-really-means", 4, "context",
     "Surprise: 'organic' does not mean pesticide-free.",
     "'Organic' does not mean pesticide-free."),
]

ok = fail = 0

for tid, idx in DROPS:
    p = os.path.join(LAD, tid + ".json")
    d = json.load(open(p, encoding="utf-8"))
    before = len(d["rungs"])
    dropped = d["rungs"].pop(idx)
    d["n_rungs"] = len(d["rungs"])
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=True, indent=1)
    print(f"DROP  {tid}  idx{idx}  ({before} -> {len(d['rungs'])} rungs)   ans was: {dropped['answer'][:50]!r}")
    ok += 1

print()
for tid, idx, field, find, repl in EDITS:
    p = os.path.join(LAD, tid + ".json")
    d = json.load(open(p, encoding="utf-8"))
    r = d["rungs"][idx]
    if find not in r[field]:
        print(f"FAIL  {tid} idx{idx} {field}: find-string not present")
        fail += 1
        continue
    r[field] = r[field].replace(find, repl)
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=True, indent=1)
    print(f"EDIT  {tid}  idx{idx}  {field}  OK")
    ok += 1

print()
print(f"applied: {ok} ok, {fail} failed")
