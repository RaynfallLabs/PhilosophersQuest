"""Consolidate the three pillar JSON files into the requested output schema."""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent


def main() -> None:
    p1 = json.loads((REPO / "_gen_science_t5_p1.json").read_text(encoding="utf-8"))["questions"]
    p2 = json.loads((REPO / "_gen_science_t5_p2.json").read_text(encoding="utf-8"))["questions"]
    p3 = json.loads((REPO / "_gen_science_t5_p3.json").read_text(encoding="utf-8"))["questions"]

    output = {
        "tier": 5,
        "summary": {
            "questions_generated": len(p1) + len(p2) + len(p3),
            "by_pillar": {
                "1": len(p1),
                "2": len(p2),
                "3": len(p3),
            },
        },
        "questions": p1 + p2 + p3,
    }

    out_path = REPO / "_gen_science_t5_p123.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Total: {output['summary']['questions_generated']}")
    print(f"P1: {output['summary']['by_pillar']['1']}")
    print(f"P2: {output['summary']['by_pillar']['2']}")
    print(f"P3: {output['summary']['by_pillar']['3']}")


if __name__ == "__main__":
    main()
