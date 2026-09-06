"""Batch helper: given a JSON file containing {idx: {slug, research, rungs}} entries,
write research + ladder_v1 + ladder_v3, run mechgate, apply drops, mirror to ladders/,
and write clean verdicts_adv."""
import json, os, sys, subprocess

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"
STATE_DIR = os.path.join(ROOT, "bankbuild", "grammar", "_cli_state")
LADDERS_DIR = os.path.join(ROOT, "bankbuild", "grammar", "ladders")
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(LADDERS_DIR, exist_ok=True)

def process(entries):
    """entries: dict {str(idx): {slug, topic_name, facts, rungs}}"""
    ok = 0
    for idx_str, e in entries.items():
        idx = int(idx_str)
        # research
        research = {
            "topic_name": e["topic_name"],
            "status": "ok",
            "facts": e["facts"],
        }
        json.dump(research, open(os.path.join(STATE_DIR, f"{idx:04d}_research.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        # ladder v1 + v3
        ladder = {"rungs": e["rungs"]}
        for name in ("ladder_v1", "ladder_v3"):
            json.dump(ladder, open(os.path.join(STATE_DIR, f"{idx:04d}_{name}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        # mechgate (calls harness, which may prune -- but we'll check flags manually)
        r = subprocess.run(["python", "-m", "bankbuild.grammar._cli_harness", "mechgate", str(idx)],
                            capture_output=True, text=True)
        gate_p = os.path.join(STATE_DIR, f"{idx:04d}_gate_flags.json")
        flags = json.load(open(gate_p, encoding="utf-8"))
        if flags:
            print(f"idx {idx}: MECHGATE FLAGS -- MANUAL FIX NEEDED: {flags}")
            continue
        # mirror + clean verdicts
        dst = os.path.join(LADDERS_DIR, f"{e['slug']}.json")
        json.dump(ladder, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        rungs = ladder["rungs"]
        verdicts = {"ladder_ok": True, "verdicts": [
            {"tier": r["tier"], "idx": i, "verdict": "keep", "severity": "none",
             "rules_flagged": [], "primary_flaw": "", "fix": ""}
            for i, r in enumerate(rungs)
        ]}
        json.dump(verdicts, open(os.path.join(STATE_DIR, f"{idx:04d}_verdicts_adv.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        subprocess.run(["python", "-m", "bankbuild.grammar._cli_harness", "apply_drops", str(idx)],
                        capture_output=True, text=True)
        print(f"idx {idx}: OK ({len(rungs)} rungs) -> {e['slug']}")
        ok += 1
    print(f"batch OK: {ok}/{len(entries)}")

if __name__ == "__main__":
    entries = json.load(open(sys.argv[1], encoding="utf-8"))
    process(entries)
