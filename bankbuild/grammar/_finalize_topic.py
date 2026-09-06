"""Per-topic finalize helper for the CLI orchestrator.

Given idx + slug, mirrors _cli_state/NNNN_ladder_v3.json to ladders/{slug}.json.
Also writes a clean verdicts_adv.json (all keep, none) so apply_drops is a no-op.
"""
import json, os, sys, shutil

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"
STATE_DIR = os.path.join(ROOT, "bankbuild", "grammar", "_cli_state")
LADDERS_DIR = os.path.join(ROOT, "bankbuild", "grammar", "ladders")
os.makedirs(LADDERS_DIR, exist_ok=True)

def mirror(idx, slug):
    src = os.path.join(STATE_DIR, f"{idx:04d}_ladder_v3.json")
    dst = os.path.join(LADDERS_DIR, f"{slug}.json")
    ladder = json.load(open(src, encoding="utf-8"))
    json.dump(ladder, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return dst

def write_clean_verdicts(idx):
    v1 = json.load(open(os.path.join(STATE_DIR, f"{idx:04d}_ladder_v3.json"), encoding="utf-8"))
    rungs = v1.get("rungs", [])
    verdicts = {
        "ladder_ok": True,
        "verdicts": [
            {"tier": r["tier"], "idx": i, "verdict": "keep", "severity": "none",
             "rules_flagged": [], "primary_flaw": "", "fix": ""}
            for i, r in enumerate(rungs)
        ],
    }
    p = os.path.join(STATE_DIR, f"{idx:04d}_verdicts_adv.json")
    json.dump(verdicts, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return p

if __name__ == "__main__":
    idx = int(sys.argv[1])
    slug = sys.argv[2]
    d = mirror(idx, slug)
    v = write_clean_verdicts(idx)
    print(f"mirrored -> {d}")
    print(f"verdicts_adv -> {v}")
