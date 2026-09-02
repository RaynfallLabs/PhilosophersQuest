"""Print the next N unbuilt queue indices (not yet in the manifest as passed/needs_review).

Usage: python bankbuild/science/_next_batch.py [N]   (default N=20)
Prints a JSON array of idxs to feed the build pipeline's args.idxs, plus a human summary.
Skips topics already built (passed OR needs_review) so contiguous scaling never rebuilds done work.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from bank import paths, jload  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
P = paths("science")
queue = jload(P["QUEUE"], [])
man = jload(P["MAN"], {})
built = {v.get("idx") for v in man.values() if v.get("idx") is not None}
unbuilt = [i for i in range(len(queue)) if i not in built]
nxt = unbuilt[:N]
print(json.dumps(nxt))
done = len(queue) - len(unbuilt)
print(f"# queue={len(queue)}  built={done}  remaining={len(unbuilt)}  this batch={len(nxt)} "
      f"idxs [{nxt[0] if nxt else '-'}..{nxt[-1] if nxt else '-'}]", file=sys.stderr)
if nxt:
    for i in nxt[:24]:
        t = queue[i]
        print(f"#   {i:3d} [{t['weight']:>6}/{t['depth']:<8}] {t['name'][:48]}", file=sys.stderr)
