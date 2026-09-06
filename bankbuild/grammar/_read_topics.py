"""Helper to dump topic specs from _queue.json for offline authoring."""
import json, sys
Q = json.load(open(r"C:\Users\brand\Documents\PhilosophersQuest\bankbuild\grammar\_queue.json", encoding="utf-8"))
if len(sys.argv) == 2:
    print(json.dumps(Q[int(sys.argv[1])], indent=1))
elif len(sys.argv) == 3:
    lo, hi = int(sys.argv[1]), int(sys.argv[2])
    for i in range(lo, hi):
        print(f"--- {i} ---")
        print(json.dumps(Q[i], indent=1))
