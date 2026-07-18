"""Apply dedup_verify output (subject-generic): move CONFIRMED same-fact duplicate ladders out of
<subject>/ladders/ into <subject>/_pruned/ (reversible -- never deletes), drop them from the manifest.

Usage: python bankbuild/dedup_prune_apply.py --subject=X <dedup_verify_task_output.json> [--dry]

SAFETY: only run after confirming a fresh `bank.py merge --subject=X` reproduces the LIVE bank count
(else ladders/ are stale and re-merging would regress the bank). After applying:
  bank.py merge --subject=X  ->  bank.py gate --subject=X  ->  bank.py promote --subject=X
"""
import json, os, sys, shutil

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"

argv = sys.argv[1:]
subject, outfile, dry = None, None, False
for a in argv:
    if a.startswith("--subject="):
        subject = a.split("=", 1)[1]
    elif a == "--dry":
        dry = True
    elif not a.startswith("--"):
        outfile = a
if not subject or not outfile:
    print("usage: python bankbuild/dedup_prune_apply.py --subject=X <dedup_verify_output.json> [--dry]")
    sys.exit(1)

LAD = os.path.join(ROOT, "bankbuild", subject, "ladders")
PRUNED = os.path.join(ROOT, "bankbuild", subject, "_pruned")
MAN = os.path.join(ROOT, "bankbuild", subject, "manifest.json")
LOG = os.path.join(ROOT, "bankbuild", subject, "_dedup_prune_log.txt")


def extract(w):
    o = w
    for _ in range(6):
        if isinstance(o, dict) and isinstance(o.get("verdicts"), list):
            return o["verdicts"]
        if isinstance(o, dict):
            for k in ("result", "value", "output", "data"):
                if k in o:
                    o = o[k]
                    if isinstance(o, str):
                        try: o = json.loads(o)
                        except Exception: pass
                    break
            else:
                break
        else:
            break
    return None


verdicts = extract(json.load(open(outfile, encoding="utf-8")))
if verdicts is None:
    print("ERROR: no 'verdicts' in", outfile); sys.exit(1)

os.makedirs(PRUNED, exist_ok=True)
man = json.load(open(MAN, encoding="utf-8")) if os.path.exists(MAN) else {}

drop_ids, spared, log_lines = [], 0, []
for v in verdicts:
    keep = v.get("keep_id")
    spared += len(v.get("kept_distinct_ids", []))
    for d in v.get("confirmed_drop_ids", []):
        if not os.path.exists(os.path.join(LAD, d + ".json")):
            log_lines.append(f"SKIP (already gone): {d}"); continue
        drop_ids.append(d)
        log_lines.append(f"PRUNE {d}   (dup of {keep})")

print(f"[{subject}] dedup prune: {len(drop_ids)} confirmed duplicate ladders -> _pruned/  ({spared} spared as distinct)")
for l in log_lines:
    print("  ", l)

if dry:
    print("\n(dry run -- omit --dry to move)"); sys.exit(0)

for d in drop_ids:
    shutil.move(os.path.join(LAD, d + ".json"), os.path.join(PRUNED, d + ".json"))
    man.pop(d, None)
json.dump(man, open(MAN, "w", encoding="utf-8"), ensure_ascii=True, indent=1)
open(LOG, "w", encoding="utf-8").write(f"DEDUP PRUNE ({subject}): moved {len(drop_ids)} ladders to _pruned/\n" + "\n".join(log_lines) + "\n")
remaining = len([f for f in os.listdir(LAD) if f.endswith(".json") and not f.startswith("_")])
print(f"\nMOVED {len(drop_ids)} ladders to _pruned/. ladders/ now holds {remaining}. log -> {LOG}")
print(f"NEXT: bank.py merge --subject={subject}  ->  bank.py gate --subject={subject}  ->  bank.py promote --subject={subject}")
