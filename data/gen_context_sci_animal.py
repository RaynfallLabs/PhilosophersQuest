#!/usr/bin/env python3
"""
Generate educational context paragraphs for science and animal quiz questions.
Reads contexts from the embedded CONTEXTS dict, patches them into the question JSONs.

Usage: python data/gen_context_sci_animal.py
"""
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load contexts from the companion JSON file
def load_contexts():
    ctx_path = os.path.join(SCRIPT_DIR, "contexts_sci_animal.json")
    with open(ctx_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    contexts = load_contexts()

    for filename in ["science.json", "animal.json"]:
        filepath = os.path.join(SCRIPT_DIR, "questions", filename)
        print(f"Processing {filepath}...")

        with open(filepath, "r", encoding="utf-8") as f:
            questions = json.load(f)

        added = 0
        missing = 0
        for q in questions:
            if "context" not in q:
                key = q["question"]
                if key in contexts:
                    q["context"] = contexts[key]
                    added += 1
                else:
                    missing += 1
                    print(f"  WARNING: No context for: {key[:80]}...")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)

        total = sum(1 for q in questions if "context" in q)
        print(f"  {filename}: {added} added, {missing} missing, {total}/{len(questions)} total with context")


if __name__ == "__main__":
    main()
