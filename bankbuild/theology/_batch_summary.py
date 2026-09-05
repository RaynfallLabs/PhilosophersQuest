"""Summarize a build-batch task output: per-topic status, rung count, unresolved flags.

Usage: python bankbuild/science/_batch_summary.py "<task output file>"
"""
import json, sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

o = json.load(open(sys.argv[1], encoding="utf-8"))


def find(x):
    if isinstance(x, dict):
        if isinstance(x.get("results"), list) and x.get("subject"):
            return x
        for v in x.values():
            r = find(v)
            if r:
                return r
    if isinstance(x, str) and x.lstrip()[:1] in "{[":
        try:
            return find(json.loads(x))
        except Exception:
            return None
    return None


res = find(o)
if not res:
    print("ERROR: no results object found")
    sys.exit(1)
print("keys:", sorted(res.keys()), "| start:", res.get("start"), "count:", res.get("count"),
      "| results:", len(res["results"]))
for t in res["results"]:
    rungs = len((t.get("ladder") or {}).get("rungs") or [])
    unres = t.get("unresolved") or []
    print(f"  idx {t['idx']}: {t['status']:14s} rungs={rungs:2d} unresolved={len(unres)}  {t['name'][:58]}")
    for u in unres[:4]:
        print(f"        - {str(u)[:150]}")
