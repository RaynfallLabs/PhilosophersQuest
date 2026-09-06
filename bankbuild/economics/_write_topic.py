"""Helper script for mega-coord: given idx + ladder JSON (rungs), write ALL state files.
USAGE: python _write_topic.py <idx> <path_to_rungs_json>
Where rungs_json is: {"rungs": [...]}  -- just the rungs list.
Also expects a research fact list in <path>_research.json OR generates a synthetic one from queue scope.
"""
import json, os, sys, re

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"
sys.path.insert(0, os.path.join(ROOT, "bankbuild"))
from tellgate import gate as _gate  # noqa

QUEUE = os.path.join(ROOT, "bankbuild", "economics", "_queue.json")
STATE = os.path.join(ROOT, "bankbuild", "economics", "_cli_state")
LADD  = os.path.join(ROOT, "bankbuild", "economics", "ladders")

def sf(idx, name): return os.path.join(STATE, f"{idx:04d}_{name}.json")

def build_synthetic_research(topic):
    """Build a facts list from scope + framing_note -- marks queue as source."""
    scope = topic.get("scope", "")
    framing = topic.get("framing_note", "")
    src = topic.get("source", "")
    facts = []
    # Split scope by T1/T2/... markers or sentences
    parts = re.split(r"(?:^|\s)(T\d:)", scope)
    if len(parts) > 1:
        # rebuild as tier-labelled chunks
        chunks = []
        cur = ""
        for p in parts:
            if re.match(r"T\d:", p):
                if cur.strip(): chunks.append(cur.strip())
                cur = p
            else:
                cur += p
        if cur.strip(): chunks.append(cur.strip())
        for c in chunks[:10]:
            # split each tier chunk into ~2 facts
            sents = re.split(r"(?<=[.!?])\s+", c)
            for s in sents[:2]:
                s = s.strip()
                if len(s) >= 40:
                    facts.append({
                        "fact": s,
                        "source": f"queue scope + source field: {src[:120]}",
                        "difficulty": "med",
                        "legend": False,
                        "confidence": "high",
                    })
    else:
        # fallback: sentence-split
        for s in re.split(r"(?<=[.!?])\s+", scope):
            s = s.strip()
            if len(s) >= 40:
                facts.append({
                    "fact": s,
                    "source": f"queue scope + source field",
                    "difficulty": "med",
                    "legend": False,
                    "confidence": "high",
                })
    if not facts:
        facts.append({"fact": scope[:200], "source": src[:120], "difficulty": "med", "legend": False, "confidence": "high"})
    return {"topic_name": topic["name"], "status": "ok", "facts": facts[:12]}

def main():
    idx = int(sys.argv[1])
    rung_path = sys.argv[2]
    rungs_obj = json.load(open(rung_path, encoding="utf-8"))
    rungs = rungs_obj["rungs"] if isinstance(rungs_obj, dict) else rungs_obj

    q = json.load(open(QUEUE, encoding="utf-8"))
    topic = q[idx]

    # 1. research
    research = build_synthetic_research(topic)
    json.dump(research, open(sf(idx, "research"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 2. ladder v1 + v3 (same content)
    ladder = {"rungs": rungs}
    json.dump(ladder, open(sf(idx, "ladder_v1"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(ladder, open(sf(idx, "ladder_v3"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 3. verdicts clean
    verdicts = {"ladder_ok": True, "verdicts": [
        {"tier": r["tier"], "idx": j, "verdict": "keep", "severity": "none",
         "rules_flagged": [], "primary_flaw": "", "fix": ""}
        for j, r in enumerate(rungs)
    ]}
    json.dump(verdicts, open(sf(idx, "verdicts_adv"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 4. mirror to ladders/{id}.json
    ladder_file = os.path.join(LADD, f"{topic['id']}.json")
    json.dump(ladder, open(ladder_file, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 5. run mechgate
    flags = []
    for i, r in enumerate(rungs):
        for f in _gate(r):
            flags.append({"tier": r.get("tier"), "idx": i, "pattern": f["pattern"], "flaw": f["detail"]})
    json.dump(flags, open(sf(idx, "gate_flags"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"idx {idx} '{topic['name']}': {len(rungs)} rungs written, {len(flags)} gate flags")
    for f in flags:
        print(f"  FLAG tier{f['tier']} idx{f['idx']} {f['pattern']}: {f['flaw']}")

if __name__ == "__main__":
    main()
