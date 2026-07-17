"""Dedupe the cooking queue: drop redundant cross-strand twins, keeping the best-placed version.
Match rules are (section, must_include_substr, must_exclude_substr_or_None) on the lowercased name.
Prints every match per rule (warns if a rule hits != 1 topic), then removes matches from the spec
files and logs to _dedupe_log.txt. Re-runnable-ish (already-dropped rules just match 0).

Usage: python bankbuild/cooking/_dedupe.py [--apply]
"""
import json, os, glob, sys

SD = r"C:\Users\brand\Documents\PhilosophersQuest\bankbuild\cooking\_strands"
LOG = r"C:\Users\brand\Documents\PhilosophersQuest\bankbuild\cooking\_dedupe_log.txt"
APPLY = "--apply" in sys.argv

# (section, include_substr, exclude_substr) -> drop. Keep-decision noted in the comment.
DROP_RULES = [
    ("ingredient", "nuts that aren", None),          # keep wonder "Nuts that aren't nuts"
    ("wonder", "vanilla is an orchid", None),        # keep ingredient vanilla (provenance)
    ("history", "orchid that needed", None),         # keep ingredient vanilla
    ("history", "pinch of pepper cost", None),       # keep history king-of-spices + da-gama; myth owned by feast
    ("ingredient", "sichuan pepper", None),          # tingle -> wonder senses; cuisine -> recipe ma-la
    ("wonder", "stale bread", None),                 # keep kitchen "why stale bread revives"
    ("history", "spice-rack", None),                 # keep ingredient "every spice is a plant part"
    ("nutrition", "fiber: the carb", None),          # keep the richer fiber ladder (q11)
    ("nutrition", "two kinds", None),                # keep vitamin-A flagship (carrot myth)
    ("nutrition", "where it really comes from", None),
    ("nutrition", "where vitamin a really lives", None),
    ("history", "family tree", None),                # keep recipe "the five mother sauces"
    ("kitchen", "five bases", None),                 # keep recipe mother sauces (also resolves escoffier dup)
    ("ingredient", "heat alone does to sugar", None),# caramelization -> kitchen flagship
    ("kitchen", "own browning", None),               # keep the-sear...maillard-vs-caramelization
    ("wonder", "own browning", None),
    ("kitchen", "browning itself", None),
    ("history", "hide", None),                        # keep feast "medieval spice flex + rotten-meat myth"
    ("ingredient", "crocus stigma", None),           # keep wonder "saffron worth more than gold"
    ("history", "worth its weight", None),           # keep wonder saffron
    ("kitchen", "braising", None),                    # collagen->gelatin owned by ingredient cuts
    ("recipe", "turning collagen", None),
    ("wonder", "turn silky", None),
    ("ingredient", "stems that creep", None),        # keep ingredient "underground rhizomes"
    ("history", "sandwich", "earl"),                 # keep recipe "sandwich and the Earl"
    ("history", "modern kitchen", None),             # keep chefs "escoffier and the kitchen brigade"
    ("history", "beans that fed", None),             # keep ingredient "the three sisters"
    ("nutrition", "three sisters", None),            # complete-protein stays in macros protein topic
    ("recipe", "corn, beans, squash", None),
]

files = {fn: json.load(open(fn, encoding="utf-8")) for fn in sorted(glob.glob(os.path.join(SD, "spec_*.json")))}
log_lines = []
drop_ids = []  # (fn, idx)

for sec, inc, exc in DROP_RULES:
    matches = []
    for fn, arr in files.items():
        for i, t in enumerate(arr):
            nm = (t.get("name") or "").lower()
            if t.get("section") == sec and inc in nm and (exc is None or exc not in nm):
                matches.append((fn, i, t.get("name")))
    tag = f"[{sec} | '{inc}'{' !'+exc if exc else ''}]"
    if len(matches) != 1:
        print(f"WARN {tag}: matched {len(matches)} (expected 1)")
    for fn, i, nm in matches:
        print(f"  DROP {tag}: {nm}   ({os.path.basename(fn)})")
        drop_ids.append((fn, i))
        log_lines.append(f"{tag}  ->  {nm}  [{os.path.basename(fn)}]")

print(f"\nTOTAL to drop: {len(drop_ids)}")

if APPLY:
    # remove by index (descending per file) so indices stay valid
    byfile = {}
    for fn, i in drop_ids:
        byfile.setdefault(fn, []).append(i)
    for fn, idxs in byfile.items():
        arr = files[fn]
        for i in sorted(set(idxs), reverse=True):
            del arr[i]
        json.dump(arr, open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(LOG, "w", encoding="utf-8").write("COOKING QUEUE DEDUPE LOG\n" + "\n".join(log_lines) + "\n")
    print(f"APPLIED. dropped {len(drop_ids)} topics across {len(byfile)} files. log -> {LOG}")
else:
    print("(dry run -- pass --apply to remove)")
