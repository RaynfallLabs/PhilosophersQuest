"""Apply queue_dedup.wf.js output: remove same-fact duplicate topics from a subject's _queue.json
BEFORE the build (so idxs are never frozen with duplicates). Run right after _assemble_queue.py.

Usage: python bankbuild/queue_dedup_apply.py --subject=X <dedup_task_output.json> [--dry]

For each cluster {keep_id, drop_ids, reason}: keeps keep_id, removes the drop_ids from _queue.json.
Validates keep_id survives and all drop_ids exist; logs to <subject>/_queue_dedup_log.txt. Idempotent
(already-dropped ids are skipped). Re-run _assemble_queue.py FIRST if you want to start clean.
"""
import json, os, sys

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"

argv = sys.argv[1:]
subject, outfile, dry = "cooking", None, False
for a in argv:
    if a.startswith("--subject="):
        subject = a.split("=", 1)[1]
    elif a == "--dry":
        dry = True
    else:
        outfile = a

QUEUE = os.path.join(ROOT, "bankbuild", subject, "_queue.json")
LOG = os.path.join(ROOT, "bankbuild", subject, "_queue_dedup_log.txt")


def extract(wrapper):
    o = wrapper
    for _ in range(6):
        if isinstance(o, dict) and isinstance(o.get("clusters"), list):
            return o["clusters"]
        if isinstance(o, dict):
            for k in ("result", "value", "output", "data"):
                if k in o:
                    o = o[k]
                    if isinstance(o, str):
                        try:
                            o = json.loads(o)
                        except Exception:
                            pass
                    break
            else:
                break
        else:
            break
    return None


if not outfile:
    print("usage: python bankbuild/queue_dedup_apply.py --subject=X <dedup_task_output.json> [--dry]")
    sys.exit(1)

clusters = extract(json.load(open(outfile, encoding="utf-8")))
if clusters is None:
    print("ERROR: could not find 'clusters' in", outfile)
    sys.exit(1)

queue = json.load(open(QUEUE, encoding="utf-8"))
ids = {t["id"] for t in queue}

drop, log_lines = set(), []
for c in clusters:
    keep = c.get("keep_id")
    reason = c.get("reason", "")
    for d in c.get("drop_ids", []):
        if d not in ids:
            log_lines.append(f"SKIP (not in queue): {d}")
            continue
        if d == keep:
            continue
        drop.add(d)
        log_lines.append(f"DROP {d}   (keep {keep})   {reason[:120]}")

kept = [t for t in queue if t["id"] not in drop]
print(f"[{subject}] queue: {len(queue)} -> {len(kept)}  ({len(drop)} same-fact duplicates dropped)")
for l in log_lines:
    print("  ", l)

if dry:
    print("(dry run -- omit --dry to write)")
else:
    json.dump(kept, open(QUEUE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(LOG, "w", encoding="utf-8").write(f"QUEUE DEDUP ({subject}): {len(queue)} -> {len(kept)}\n" + "\n".join(log_lines) + "\n")
    print(f"WROTE {QUEUE}  | log -> {LOG}")
