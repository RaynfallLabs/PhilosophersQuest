"""POST-SHIP dedup candidate finder (subject-generic). Scan a subject's BUILT ladders for
same-fact twins by ANSWER-SET overlap, and print candidate {keep_id, drop_ids} clusters to feed
`dedup_verify.wf.js`.

WHY this and not a queue_dedup re-run (PIPELINE §11.3 / §12.2): the pre-build `queue_dedup` reads
topic SCOPES and often judges two same-place topics as "different angles" -- but once BUILT, their
ladders can converge onto the same facts (geography: two Yellowstone ladders, 8/11 rungs identical,
that the scope pass had spared). A local answer-set overlap over the built ladders catches that
convergence cheaply (no agents). `dedup_verify` then confirms/spares each candidate against the full
ladders (biased-to-keep); `dedup_prune_apply.py` reversibly prunes the confirmed set.

Usage: python bankbuild/dedup_overlap_scan.py --subject=X [--min-shared=2] [--json]
  default prints a human table; --json prints a clusters array ready for dedup_verify args.clusters
  (keep = the richer/longer ladder of each pair; verify decides the actual drop).
"""
import sys, os, re, json, itertools

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bank import paths, jload  # noqa: E402

subject, min_shared, as_json = "geography", 2, False
for a in sys.argv[1:]:
    if a.startswith("--subject="):
        subject = a.split("=", 1)[1]
    elif a.startswith("--min-shared="):
        min_shared = int(a.split("=", 1)[1])
    elif a == "--json":
        as_json = True

P = paths(subject)
LAD = P["LAD"]


def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()


lads = {}
for fn in os.listdir(LAD):
    if not fn.endswith(".json"):
        continue
    d = jload(os.path.join(LAD, fn), {})
    rungs = d.get("rungs", [])
    lads[fn[:-5]] = {"ans": set(norm(r.get("answer", "")) for r in rungs), "n": len(rungs)}

cands = []
for a, b in itertools.combinations(sorted(lads), 2):
    la, lb = lads[a], lads[b]
    shared = la["ans"] & lb["ans"]
    if len(shared) >= min_shared:
        frac = len(shared) / max(1, min(len(la["ans"]), len(lb["ans"])))
        # keep the richer/longer ladder; verify will decide the real drop
        keep, drop = (a, b) if la["n"] >= lb["n"] else (b, a)
        cands.append({"frac": round(frac, 2), "shared": len(shared), "keep_id": keep,
                      "drop_ids": [drop], "shared_answers": sorted(shared),
                      "reason": f"share {len(shared)} answers ({round(frac,2)} of smaller): {', '.join(sorted(shared))[:80]}"})
cands.sort(key=lambda c: (-c["frac"], -c["shared"]))

if as_json:
    print(json.dumps([{k: c[k] for k in ("keep_id", "drop_ids", "reason")} for c in cands],
                     ensure_ascii=False))
else:
    print(f"[{subject}] {len(lads)} ladders scanned; {len(cands)} candidate pairs share >= {min_shared} answers.")
    print("(These are CANDIDATES only -- most are legit theme-uses-place-as-example cross-links.")
    print(" Send the real same-place/same-topic twins to dedup_verify.wf.js, which is biased-to-keep.)\n")
    for c in cands:
        print(f"  frac={c['frac']:.2f} shared={c['shared']}  KEEP {c['keep_id']}  ||  drop? {c['drop_ids'][0]}")
        print(f"      shared: {c['shared_answers']}")
    if cands:
        print("\nTo verify (edit the clusters down to real twins first):")
        print(f"  python bankbuild/dedup_overlap_scan.py --subject={subject} --json   # clusters for dedup_verify args")
