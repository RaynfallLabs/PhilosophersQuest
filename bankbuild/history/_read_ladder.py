"""Print a compact history ladder as JSON for the dedup-verify agents.
Usage: python bankbuild/history/_read_ladder.py <ladder-id>
"""
import json, sys, os

LADDIR = r"C:\Users\brand\Documents\PhilosophersQuest\bankbuild\history\ladders"
i = sys.argv[1]
d = json.load(open(os.path.join(LADDIR, i + ".json"), encoding="utf-8"))
out = {"id": i, "name": d.get("name", i),
       "rungs": [{"tier": r.get("tier"), "stem": r.get("stem"), "answer": r.get("answer")}
                 for r in d.get("rungs", [])]}
sys.stdout.write(json.dumps(out, ensure_ascii=True))
