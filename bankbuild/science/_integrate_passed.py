"""Wall-recovery salvage: from a (possibly WALLED) build output, integrate ONLY the topics that
FULLY passed the in-build pipeline (status=='passed' with valid, non-empty rungs) into ladders/.

Everything else -- needs_review, status 'error' (walled mid-pipeline), empty/invalid ladders -- is
LEFT UN-INTEGRATED, so `_next_batch.py` returns those idxs for a clean fresh rebuild. This avoids the
§8 trap (integrating a walled 'error' topic with a partial/empty ladder orphans it in the manifest)
while salvaging the fully-completed topics' work, which is otherwise discarded on every wall.

A 'passed' topic completed research -> author -> craft-judge -> adversarial-judge -> gate at 0 high +
0 medium; the wall did not touch it, so keeping it is 100% safe. needs_review topics are deliberately
NOT salvaged here (a wall-during-adversarial topic also reports needs_review, per §8), so they rebuild.

Usage: python bankbuild/science/_integrate_passed.py <walled_build_output.json>
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from bank import paths, jload, jdump, valid_rung, extract_results  # noqa: E402

P = paths("science")


def main(outfile):
    wrapper = jload(outfile)
    if wrapper is None:
        print("ERROR: cannot read", outfile); return
    results = extract_results(wrapper)
    queue = jload(P["QUEUE"], [])
    man = jload(P["MAN"], {})
    n_pass = n_skip = 0
    skipped = []
    for r in results:
        if not r or "idx" not in r:
            continue
        idx = r["idx"]
        meta = queue[idx] if 0 <= idx < len(queue) else {}
        tid = meta.get("id", f"idx-{idx}")
        name = r.get("name") or meta.get("name", tid)
        rungs = (r.get("ladder") or {}).get("rungs", []) or []
        bad = [i for i, rg in enumerate(rungs) if not valid_rung(rg)]
        status = r.get("status")
        # ONLY salvage a genuinely-complete clean pass (bank.py's exact ladders/ criterion)
        if status == "passed" and rungs and not bad:
            # do not clobber a topic already banked as passed
            if tid in man and man[tid].get("status") == "passed":
                continue
            rec = {"id": tid, "name": name, "strand": meta.get("strand"), "idx": idx,
                   "status": "passed", "n_rungs": len(rungs), "rounds": r.get("rounds", 0),
                   "weight": meta.get("weight"), "depth": meta.get("depth"),
                   "tier_span": meta.get("tier_span"), "sources": r.get("sources", []),
                   "unresolved": [], "invalid_rungs": [], "ts": int(time.time()), "rungs": rungs}
            jdump(rec, os.path.join(P["LAD"], tid + ".json"))
            man[tid] = {k: rec[k] for k in ("status", "n_rungs", "rounds", "idx", "name",
                                            "strand", "weight", "depth", "ts")}
            n_pass += 1
        else:
            n_skip += 1
            skipped.append((idx, status or "?", len(rungs), tid))
    jdump(man, P["MAN"])
    print(f"salvaged: {n_pass} fully-passed topics -> ladders/ ; {n_skip} left un-integrated for rebuild.")
    for idx, st, nr, tid in sorted(skipped):
        print(f"   rebuild idx {idx:3d}  [{st}, {nr} rungs]  {tid}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python bankbuild/science/_integrate_passed.py <walled_build_output.json>")
    else:
        main(sys.argv[1])
