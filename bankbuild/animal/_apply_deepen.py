"""Append passed NEW rungs from a deepen-workflow output onto their ladder files.

Usage: python bankbuild/animal/_apply_deepen.py <deepen_task_output.json>
Only appends rungs that (a) validate, (b) are tier 4/5, (c) aren't a near-duplicate of an existing
rung (same answer, or answer text already present). Updates manifest n_rungs. Re-merge afterward.
"""
import sys, os, json, time, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from bank import paths, jload, jdump, valid_rung, extract_results  # noqa: E402

P = paths("animal")


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def main(outfile):
    wrapper = jload(outfile)
    if wrapper is None:
        print("ERROR: cannot read", outfile); return
    results = extract_results(wrapper)
    man = jload(P["MAN"], {})
    n_topics = n_rungs = n_skip = 0
    for r in results:
        if not r or "id" not in r:
            continue
        tid = r["id"]
        new = (r.get("new_rungs") or [])
        if r.get("status") != "passed" or not new:
            continue
        lp = os.path.join(P["LAD"], tid + ".json")
        d = jload(lp)
        if not d or not d.get("rungs"):
            print("  SKIP", tid, "(no ladder)"); continue
        existing_ans = {norm(x.get("answer")) for x in d["rungs"]}
        existing_stem = {norm(x.get("stem"))[:80] for x in d["rungs"]}
        added = 0
        for rg in new:
            if not valid_rung(rg):
                n_skip += 1; continue
            if int(rg.get("tier", 0)) not in (4, 5):
                n_skip += 1; continue
            if norm(rg.get("answer")) in existing_ans or norm(rg.get("stem"))[:80] in existing_stem:
                n_skip += 1; continue  # near-duplicate
            d["rungs"].append(rg)
            existing_ans.add(norm(rg.get("answer")))
            added += 1
        if added:
            d["n_rungs"] = len(d["rungs"])
            d["deepened"] = int(time.time())
            jdump(d, lp)
            if tid in man:
                man[tid]["n_rungs"] = len(d["rungs"])
            n_topics += 1; n_rungs += added
            print(f"  +{added:2d} {tid}  -> {len(d['rungs'])} rungs")
    jdump(man, P["MAN"])
    print(f"applied: {n_rungs} new rungs across {n_topics} topics ({n_skip} skipped: invalid / wrong-tier / dup).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python bankbuild/animal/_apply_deepen.py <deepen_task_output.json>")
    else:
        main(sys.argv[1])
