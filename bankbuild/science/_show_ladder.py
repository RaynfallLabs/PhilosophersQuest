"""Print a ladder's rungs (stem/choices/answer) for eyeball review.

Usage: python bankbuild/science/_show_ladder.py <id> [needs_review|ladders] [start] [count]
"""
import json, os, sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest\bankbuild\science"
lid = sys.argv[1]
sub = sys.argv[2] if len(sys.argv) > 2 else "needs_review"
start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
count = int(sys.argv[4]) if len(sys.argv) > 4 else 99

d = json.load(open(os.path.join(ROOT, sub, lid + ".json"), encoding="utf-8"))
rungs = d["rungs"]
print(f"{lid}  [{sub}]  {len(rungs)} rungs\n")
for r in rungs[start:start + count]:
    total = len(r["stem"]) + sum(len(c) for c in r["choices"])
    print(f"=== T{r['tier']}  ({total} chars stem+choices) ===")
    print(r["stem"])
    for c in r["choices"]:
        mark = " *" if c == r["answer"] else "  "
        print(f" {mark} {c}")
    print()
