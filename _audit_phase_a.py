"""Phase A — Deterministic + heuristic sweep across all 12 banks.

Runs every existing audit tool against every question in every bank
and produces _audit_phase_a.json with flag list keyed by (bank, idx).

NO bank modifications — read-only audit.
"""
import json
import re
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

REPO = Path(__file__).resolve().parent
BANK_DIR = REPO / "data" / "questions"

BANKS = [
    "math", "grammar", "history", "philosophy", "geography",
    "animal", "cooking", "science", "economics", "ai",
    "theology", "trivia",
]

# Weasel-closer regex (composite of v1/v2/v3)
WEASEL_RE = re.compile(
    r"(?:[Ww]hat'?s the (?:recognition(?:\s+skill)?|takeaway|substance|lesson|pattern|"
    r"connection|moral|broader|deeper|honest|key|tell|catch|giveaway|smart move|"
    r"right move|structural \w+|underlying \w+|kid'?s? takeaway|kid'?s? recognition|"
    r"\w+ tell|\w+ skill|\w+ red flag|\w+ check|\w+ move|\w+ insight|\w+ problem|"
    r"\w+ pattern|\w+ recognition)\??\s*$"
    r"|[Ww]hat does this (?:illustrate|case illustrate|show|prove|reveal|teach|"
    r"demonstrate|suggest|tell us|expose)\??\s*$"
    r"|[Ww]hat does (?:the case|the episode|the story|the incident|the timing|it|that) "
    r"(?:illustrate|show|reveal|teach|prove|demonstrate|suggest|tell us|expose)[^?]*\??\s*$"
    r"|[Ww]hy does this matter\??\s*$"
    r"|[Ww]hat does that suggest\??\s*$"
    r")"
)

# Buried-story heuristic (stem ends in generic prompt + rich context)
BURIED_STEM_RE = re.compile(
    r"(?:what happened|what was the|describe|explain|what does this illustrate|"
    r"what was published|what's the recognition)\s*\??\s*$",
    re.IGNORECASE,
)

# Trailing-token corruption (3+ repeated words)
TRAILING_TOKEN_RE = re.compile(r"\b(\w+)(\s+\1){2,}\b")

# Mid-word truncation (ellipsis or cut-off at end of stem/answer)
TRUNCATION_RE = re.compile(r"(?:\.\.\.|…|[a-z][a-z])\s*$")  # stem ends with truncation marker
TRUNCATION_BAD = re.compile(r"(?<![.!?'\"])\b(?:th|wh|ent|tion|ing|ess|ess|ly|ed)\s*$")

# Christian-doctrinal drift (theology specific)
CHRISTIAN_DRIFT_RE = re.compile(
    r"\b(?:fulfilled (?:the )?prophecy|fulfilled Zechariah|fulfilled Isaiah|"
    r"Our Lord|the Savior|the true God|the risen Christ|the resurrected (?:Lord|Christ)|"
    r"as Scripture teaches|Scripture reveals|the real (?:account|truth|story))\b",
    re.IGNORECASE,
)

# Trivia spoiler patterns (outside allowed)
SPOILER_ALLOWED = re.compile(
    r"\b(?:My Hero Academia|MHA|Hajime no Ippo|Harry Potter|Hogwarts|Voldemort|Dumbledore|Sirius|"
    r"Star Wars\s*(?:Episode\s*[IV-VI]|original trilogy|A New Hope|Empire Strikes Back|Return of the Jedi|1977|1980|1983)|"
    r"Marvel Cinematic Universe|MCU|Avengers|Endgame|Infinity War|Iron Man|Thanos|"
    r"Toilet[- ]?Bound Hanako|Dragon Ball|DBZ|Goku|Vegeta|Frieza|Saiyan|"
    r"Scott Pilgrim|Ramona|Princess Bride|Westley|Inigo|"
    r"Mario.*Movie.*2023)\b", re.IGNORECASE)

SPOILER_PAT_RE = re.compile(
    r"(?:\bWho (?:kills?|killed|murders?|murdered)\b|"
    r"\bWhat happens (?:at the end|in the climax|in the (?:final|last))\b|"
    r"\bdies at the (?:end|hands of)\b|"
    r"\bWho is the (?:true|real|secret) (?:villain|killer|murderer|traitor|father)\b|"
    r"\bSephiroth\s+(?:kills?|killed)\b|\bAerith\s+(?:dies?|killed?)\b)",
    re.IGNORECASE,
)

# Trivia stance bans
STANCE_BANS = {
    "post-Endgame MCU": re.compile(
        r"\b(?:WandaVision|Falcon and Winter Soldier|Loki series|Moon Knight|Ms\.?\s*Marvel|"
        r"She[- ]?Hulk Attorney|Multiverse of Madness|Love and Thunder|Wakanda Forever|Quantumania|"
        r"Deadpool.*Wolverine|Phase 4|Phase 5|Phase 6|TVA agents|Time Variance Authority)\b", re.IGNORECASE),
    "Disney SW": re.compile(
        r"\b(?:Force Awakens|Last Jedi|Rise of Skywalker|Episode VII|Episode VIII|Episode IX|"
        r"Rey Skywalker|Kylo Ren|Mandalorian|Grogu|Baby Yoda|Andor series|Ahsoka series|Acolyte|"
        r"Rogue One|Solo:?\s*A Star Wars)\b", re.IGNORECASE),
    "post-Attitude wrestling": re.compile(
        r"\b(?:Ruthless Aggression|PG Era|John Cena|CM Punk|Daniel Bryan|Roman Reigns WWE|"
        r"Seth Rollins|Dean Ambrose|The Shield WWE|Becky Lynch|AEW|All Elite|MJF)\b",
        re.IGNORECASE),
}


def scan_bank(name: str) -> dict:
    """Run all heuristics on a single bank."""
    path = BANK_DIR / f"{name}.json"
    if not path.exists():
        return {"missing": True, "path": str(path)}
    bank = json.loads(path.read_text(encoding="utf-8"))
    result: dict = {
        "name": name,
        "count": len(bank),
        "gate_fails": [],
        "weasel_closers": [],
        "buried_story": [],
        "trailing_tokens": [],
        "truncation": [],
        "christian_drift": [],
        "spoiler_outside_allowed": [],
        "stance_violations": {k: [] for k in STANCE_BANS},
    }
    dup, ans = build_bank_indices(bank)
    for i, q in enumerate(bank):
        # 1. Full gate validation
        r = validate_rewrite(name, q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=i)
        if r["verdict"] == "FAIL":
            result["gate_fails"].append({
                "idx": i,
                "tier": q.get("tier"),
                "stem_preview": q.get("question", "")[:80],
                "hard_fails": r["hard_fails"][:3],
            })
        # Build text-haystacks
        stem = q.get("question", "") or ""
        answer = q.get("answer", "") or ""
        context = q.get("context", "") or ""
        choices_text = " ".join(c if isinstance(c, str) else "" for c in q.get("choices", []) or [])
        full_text = stem + " " + answer + " " + context + " " + choices_text
        # 2. Weasel closers
        if WEASEL_RE.search(stem):
            result["weasel_closers"].append({"idx": i, "tier": q.get("tier"), "stem_preview": stem[-100:]})
        # 3. Buried story (stem ends in generic prompt + context > 2x stem)
        if BURIED_STEM_RE.search(stem) and len(context) > len(stem) * 1.5:
            result["buried_story"].append({"idx": i, "tier": q.get("tier"), "stem_preview": stem[:80], "ctx_len": len(context)})
        # 4. Trailing token corruption
        if TRAILING_TOKEN_RE.search(full_text):
            m = TRAILING_TOKEN_RE.search(full_text)
            result["trailing_tokens"].append({"idx": i, "tier": q.get("tier"), "matched": m.group(0)[:50]})
        # 5. Mid-word truncation
        for field_name, field_text in [("stem", stem), ("answer", answer)]:
            if TRUNCATION_BAD.search(field_text) and not field_text.rstrip().endswith((".", "!", "?", '"', "'")):
                result["truncation"].append({"idx": i, "tier": q.get("tier"), "field": field_name, "tail": field_text[-40:]})
        # 6. Theology-specific Christian drift
        if name == "theology" and CHRISTIAN_DRIFT_RE.search(full_text):
            m = CHRISTIAN_DRIFT_RE.search(full_text)
            result["christian_drift"].append({"idx": i, "tier": q.get("tier"), "matched": m.group(0)})
        # 7. Trivia-specific spoiler scan
        if name == "trivia":
            if SPOILER_PAT_RE.search(full_text) and not SPOILER_ALLOWED.search(full_text):
                m = SPOILER_PAT_RE.search(full_text)
                result["spoiler_outside_allowed"].append({"idx": i, "tier": q.get("tier"), "matched": m.group(0)})
            for stance, pat in STANCE_BANS.items():
                if pat.search(full_text):
                    result["stance_violations"][stance].append({"idx": i, "tier": q.get("tier"), "matched": pat.search(full_text).group(0)})
    return result


def cross_bank_dup_check(all_banks: dict) -> list:
    """Check for stem-near-duplicates ACROSS banks."""
    # Simple normalization
    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower())).strip()[:80]
    seen: dict[str, list[tuple[str, int]]] = {}
    for bank_name, qs in all_banks.items():
        for i, q in enumerate(qs):
            stem_norm = norm(q.get("question", ""))
            if not stem_norm:
                continue
            seen.setdefault(stem_norm, []).append((bank_name, i))
    return [{"stem_norm": k, "occurrences": v} for k, v in seen.items() if len(v) > 1]


def main():
    print("=" * 70)
    print("PHASE A — Deterministic + heuristic sweep across 12 banks")
    print("=" * 70)
    print()
    all_results = {}
    all_banks_qs = {}
    for name in BANKS:
        print(f"Scanning {name}...", end=" ", flush=True)
        r = scan_bank(name)
        all_results[name] = r
        if not r.get("missing"):
            path = BANK_DIR / f"{name}.json"
            all_banks_qs[name] = json.loads(path.read_text(encoding="utf-8"))
        # Quick summary
        total_flags = (
            len(r.get("gate_fails", [])) + len(r.get("weasel_closers", [])) +
            len(r.get("buried_story", [])) + len(r.get("trailing_tokens", [])) +
            len(r.get("truncation", [])) + len(r.get("christian_drift", [])) +
            len(r.get("spoiler_outside_allowed", [])) +
            sum(len(v) for v in r.get("stance_violations", {}).values())
        )
        print(f"{r.get('count', 0)} questions, {total_flags} flags")

    print()
    print("Cross-bank stem-duplicate check...")
    cross_dups = cross_bank_dup_check(all_banks_qs)
    print(f"  {len(cross_dups)} cross-bank stem-near-duplicates")

    out = {
        "baseline_tag": "audit_baseline_2026_05_27",
        "phase": "A",
        "banks": all_results,
        "cross_bank_dups": cross_dups,
    }
    Path("_audit_phase_a.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    # Console summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    total_qs = sum(r.get("count", 0) for r in all_results.values())
    print(f"Total questions audited: {total_qs}")
    print()
    print(f"{'Bank':<12} {'Count':>6} {'GateF':>6} {'Wsl':>5} {'Bury':>5} {'Trail':>6} {'Trunc':>6} {'Chr':>4} {'Spoil':>6} {'Stance':>7}")
    for name in BANKS:
        r = all_results.get(name, {})
        stance_total = sum(len(v) for v in r.get("stance_violations", {}).values())
        print(f"{name:<12} {r.get('count',0):>6} "
              f"{len(r.get('gate_fails',[])):>6} "
              f"{len(r.get('weasel_closers',[])):>5} "
              f"{len(r.get('buried_story',[])):>5} "
              f"{len(r.get('trailing_tokens',[])):>6} "
              f"{len(r.get('truncation',[])):>6} "
              f"{len(r.get('christian_drift',[])):>4} "
              f"{len(r.get('spoiler_outside_allowed',[])):>6} "
              f"{stance_total:>7}")
    print()
    print(f"Cross-bank stem dups: {len(cross_dups)}")
    print()
    print("Wrote _audit_phase_a.json")


if __name__ == "__main__":
    main()
