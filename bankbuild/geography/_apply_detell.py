"""Apply de-tell workflow output: promote passed ladders out of needs_review/ into ladders/.

Usage: python bankbuild/geography/_apply_detell.py <detell_task_output.json>

For each result {id, status, ladder:{rungs}, unresolved}:
  - reads the existing needs_review/<id>.json for its metadata (idx, name, strand, weight, depth, tier_span, sources)
  - validates the (possibly de-telled) rungs
  - status passed + valid -> write ladders/<id>.json, update manifest, DELETE needs_review/<id>.json
  - else -> rewrite needs_review/<id>.json with the new rungs + flags, update manifest
Idempotent-ish; keeps the original needs_review file if the de-tell produced nothing usable.
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from bank import paths, jload, jdump, valid_rung, extract_results  # noqa: E402

P = paths("geography")


def main(outfile):
    wrapper = jload(outfile)
    if wrapper is None:
        print("ERROR: cannot read", outfile); return
    results = extract_results(wrapper)
    man = jload(P["MAN"], {})
    n_pass = n_still = n_skip = 0
    for r in results:
        if not r or "id" not in r:
            continue
        tid = r["id"]
        nr_path = os.path.join(P["NR"], tid + ".json")
        old = jload(nr_path, {})
        if not old:
            print("  SKIP", tid, "(no needs_review file)"); n_skip += 1; continue
        rungs = (r.get("ladder") or {}).get("rungs", []) or []
        bad = [i for i, rg in enumerate(rungs) if not valid_rung(rg)]
        status = r.get("status")
        meta = {k: old.get(k) for k in ("id", "name", "strand", "idx", "weight", "depth", "tier_span", "sources")}
        if status == "passed" and rungs and not bad:
            rec = {**meta, "status": "passed", "n_rungs": len(rungs), "rounds": r.get("rounds", 0),
                   "unresolved": [], "invalid_rungs": [], "ts": int(time.time()),
                   "notes": r.get("notes", []), "rungs": rungs, "detelled": True}
            jdump(rec, os.path.join(P["LAD"], tid + ".json"))
            man[tid] = {"status": "passed", "n_rungs": len(rungs), "rounds": r.get("rounds", 0),
                        "idx": old.get("idx"), "name": old.get("name"), "strand": old.get("strand"),
                        "weight": old.get("weight"), "depth": old.get("depth"), "ts": int(time.time())}
            os.remove(nr_path)
            print(f"  PASS  {tid}  ({len(rungs)} rungs)  -> ladders/, removed from needs_review/")
            n_pass += 1
        else:
            eff_rungs = rungs if (rungs and not bad) else old.get("rungs", [])
            rec = {**meta, "status": "needs_review", "n_rungs": len(eff_rungs), "rounds": r.get("rounds", 0),
                   "unresolved": r.get("unresolved", []) or old.get("unresolved", []),
                   "invalid_rungs": bad, "ts": int(time.time()), "rungs": eff_rungs, "detelled": True}
            jdump(rec, nr_path)
            man[tid] = {"status": "needs_review", "n_rungs": len(eff_rungs), "rounds": r.get("rounds", 0),
                        "idx": old.get("idx"), "name": old.get("name"), "strand": old.get("strand"),
                        "weight": old.get("weight"), "depth": old.get("depth"),
                        "unresolved": (r.get("unresolved", []) or [])[:4], "invalid_rungs": bad, "ts": int(time.time())}
            print(f"  STILL {tid}  -> needs_review ({r.get('unresolved', [])[:1]})")
            n_still += 1
    jdump(man, P["MAN"])
    print(f"applied: {n_pass} promoted to passed, {n_still} still needs_review, {n_skip} skipped.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python bankbuild/geography/_apply_detell.py <detell_task_output.json>")
    else:
        main(sys.argv[1])
