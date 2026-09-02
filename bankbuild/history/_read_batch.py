"""Dump a batch of history dedup clusters WITH their full ladders, for the
verify agents. One command gives an agent everything it needs for its batch.

Usage: python bankbuild/history/_read_batch.py <start> <count>
"""
import json, sys, os

BASE = r"C:\Users\brand\Documents\PhilosophersQuest\bankbuild\history"
LAD = os.path.join(BASE, "ladders")


def lad(i):
    d = json.load(open(os.path.join(LAD, i + ".json"), encoding="utf-8"))
    return {"id": i, "name": d.get("name", i),
            "rungs": [{"tier": r.get("tier"), "stem": r.get("stem"), "answer": r.get("answer")}
                      for r in d.get("rungs", [])]}


clusters = json.load(open(os.path.join(BASE, "_dedup_clusters.json"), encoding="utf-8"))
start, count = int(sys.argv[1]), int(sys.argv[2])
out = []
for cl in clusters[start:start + count]:
    entry = {"keep": lad(cl["keep_id"]), "reason": cl.get("reason", ""), "drops": []}
    for d in cl.get("drop_ids", []):
        try:
            entry["drops"].append(lad(d))
        except Exception:
            entry["drops"].append({"id": d, "MISSING": True})
    out.append(entry)
sys.stdout.write(json.dumps(out, ensure_ascii=True))
