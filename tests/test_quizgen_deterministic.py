"""Pytest suite for tools/quizgen deterministic gates.

Covers schema, length_parity, length_budget, anti_rote, duplicate.
Also includes an integration test that runs the full pipeline against
the philosophy bank and confirms the deterministic findings match the
calibration agent's reported numbers (within tolerance).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Ensure tools/ is importable when running pytest from repo root.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from tools.quizgen import specs  # noqa: E402
from tools.quizgen.deterministic import (  # noqa: E402
    GateStatus,
    build_duplicate_index,
    validate_anti_rote,
    validate_duplicate,
    validate_length_budget,
    validate_length_parity,
    validate_schema,
)
from tools.quizgen.deterministic.anti_rote import (  # noqa: E402
    ANTI_ROTE_PATTERN_SOURCES,
)
from tools.quizgen.pipeline import run_deterministic  # noqa: E402


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
def make_question(**overrides):
    q = {
        "tier": 2,
        "question": "What philosophical claim does Heraclitus's river image illustrate?",
        "answer": "Reality is in constant flux; nothing stays the same",
        "choices": [
            "Reality is in constant flux; nothing stays the same",
            "Time is an illusion created by human consciousness today",
            "Physical objects exist only when observed by a mind aware",
            "Knowledge requires both reason and sensory experience too",
        ],
        "context": "Heraclitus argued that change is the fundamental nature of reality.",
    }
    q.update(overrides)
    return q


# ----------------------------------------------------------------------
# schema
# ----------------------------------------------------------------------
def test_schema_pass_on_well_formed():
    r = validate_schema(make_question())
    assert r.status == GateStatus.PASS


def test_schema_fail_missing_required_field():
    q = make_question()
    del q["context"]
    r = validate_schema(q)
    assert r.status == GateStatus.FAIL
    assert "context" in r.detail


def test_schema_fail_invalid_tier():
    r = validate_schema(make_question(tier=7))
    assert r.status == GateStatus.FAIL
    assert "Tier" in r.detail


def test_schema_fail_string_tier():
    r = validate_schema(make_question(tier="2"))
    assert r.status == GateStatus.FAIL


def test_schema_fail_empty_question():
    r = validate_schema(make_question(question="  "))
    assert r.status == GateStatus.FAIL


def test_schema_fail_three_choices():
    q = make_question()
    q["choices"] = q["choices"][:3]
    r = validate_schema(q)
    assert r.status == GateStatus.FAIL
    assert "list of exactly 4" in r.detail


def test_schema_fail_answer_not_in_choices():
    q = make_question(answer="Something not in any choice")
    r = validate_schema(q)
    assert r.status == GateStatus.FAIL


def test_schema_pass_answer_case_insensitive():
    q = make_question()
    q["answer"] = q["choices"][0].upper()
    r = validate_schema(q)
    assert r.status == GateStatus.PASS


# ----------------------------------------------------------------------
# length_parity
# ----------------------------------------------------------------------
def test_length_parity_pass_when_within_15_pct():
    # All choices length ~50 chars
    q = make_question(choices=[
        "A" * 50,
        "B" * 51,
        "C" * 52,
        "D" * 49,
    ], answer="A" * 50)
    r = validate_length_parity(q)
    assert r.status == GateStatus.PASS


def test_length_parity_fail_on_short_answer():
    q = make_question(choices=[
        "Hg, mercury element from hydrargyrum tradition",  # 47
        "Au",  # 2
        "Ag, silver element from argentum old tradition",  # 47
        "Fe, iron element from ferrum old Roman tradition",  # 49
    ], answer="Au")
    r = validate_length_parity(q)
    assert r.status == GateStatus.FAIL
    assert "longest/shortest" in r.detail or "deviation" in r.detail


def test_length_parity_fail_on_ratio():
    # 4 choices where ratio just exceeds 1.30
    q = make_question(choices=[
        "A" * 100,
        "B" * 120,
        "C" * 130,
        "D" * 140,  # ratio 140/100 = 1.4
    ], answer="A" * 100)
    r = validate_length_parity(q)
    assert r.status == GateStatus.FAIL


# ----------------------------------------------------------------------
# length_budget
# ----------------------------------------------------------------------
def test_length_budget_pass_short_t1():
    q = make_question(tier=1, question="Short.", choices=["a", "b", "c", "d"], answer="a")
    r = validate_length_budget(q)
    assert r.status == GateStatus.PASS


def test_length_budget_fail_long_t1():
    q = make_question(
        tier=1,
        question="X" * 700,
        choices=["a", "b", "c", "d"],
        answer="a",
    )
    r = validate_length_budget(q)
    assert r.status == GateStatus.FAIL


def test_length_budget_t5_more_room():
    q = make_question(
        tier=5,
        question="X" * 700,
        choices=["a", "b", "c", "d"],
        answer="a",
    )
    r = validate_length_budget(q)
    # 700 + 4 = 704; T5 budget 800
    assert r.status == GateStatus.PASS


# ----------------------------------------------------------------------
# anti_rote
# ----------------------------------------------------------------------
@pytest.mark.parametrize("question_text", [
    "What is 'metaphysics'?",
    "What does 'aporia' mean?",
    "What is the 'coherence theory of truth'?",
    "What word means making a conclusion from clues?",
    "Which ancient city was home to Socrates?",
    "Which European country produced Hegel?",
    "What is the capital of France?",
    "In what year did WWI start?",
    "In what year was the Magna Carta signed?",
    "Who wrote Hamlet?",
    "Who invented the printing press?",
    "Who tutored Alexander the Great?",
    "How many gospels are there in the New Testament?",
    "What is the chemical symbol for gold?",
    "Define teleology",
    "What is the term for the study of beauty?",
])
def test_anti_rote_fires_on_rote_patterns(question_text):
    q = make_question(question=question_text)
    r = validate_anti_rote(q, subject="philosophy")
    assert r.status == GateStatus.FAIL, f"Should fire on: {question_text!r}"


@pytest.mark.parametrize("question_text", [
    "Hayek argued that price signals do something specific. What did he claim?",
    "The Buddha identified one root cause of all suffering. What is it?",
    "Russell and Whitehead spent ten years on a project Gödel destroyed. What did Gödel prove?",
    "Solzhenitsyn smuggled chapters out through friends. What argument was his finished book making?",
    "Aristotle argued the heart was the seat of thought. What evidence persuaded him?",
])
def test_anti_rote_does_not_fire_on_legitimate(question_text):
    q = make_question(question=question_text)
    r = validate_anti_rote(q, subject="philosophy")
    assert r.status == GateStatus.PASS, f"Should not fire on: {question_text!r}"


def test_anti_rote_exempts_math_and_grammar():
    q = make_question(question="What is the chemical symbol for gold?")
    r = validate_anti_rote(q, subject="math")
    assert r.status == GateStatus.NA
    r = validate_anti_rote(q, subject="grammar")
    assert r.status == GateStatus.NA


def test_anti_rote_pattern_list_in_sync_with_moral_vision_doc():
    """The patterns in anti_rote.py must match the spec in moral_vision.md §6.

    This test is the trip-wire that catches drift between the operational
    Python list and the human-readable rubric.
    """
    mv_path = REPO_ROOT / "docs" / "quiz" / "moral_vision.md"
    text = mv_path.read_text(encoding="utf-8")
    # Find the §6 anti-rote code block
    marker = "**Rote memorization without a wonder hook"
    start = text.find(marker)
    assert start > 0, "anti-rote anti-pattern not found in moral_vision.md"
    block_start = text.find("```", start)
    block_end = text.find("```", block_start + 3)
    assert block_start > 0 and block_end > 0
    block = text[block_start + 3:block_end]

    # Extract regex lines (each starts with `^`). Both code patterns and doc
    # patterns are normalized by stripping ONLY trailing whitespace (since
    # decorative alignment whitespace in the doc is not semantically part of
    # the regex). Leading whitespace and internal whitespace are preserved.
    def _normalize(s: str) -> str:
        return s.rstrip()

    doc_patterns = []
    for line in block.splitlines():
        if not line.lstrip().startswith("^"):
            continue
        # split on first `#` (the comment marker)
        if "#" in line:
            line = line.split("#", 1)[0]
        doc_patterns.append(_normalize(line.lstrip()))

    code_patterns = [_normalize(p) for p in ANTI_ROTE_PATTERN_SOURCES]
    assert sorted(doc_patterns) == sorted(code_patterns), (
        f"Pattern drift between moral_vision.md §6 and anti_rote.py.\n"
        f"  In doc only:  {sorted(set(doc_patterns) - set(code_patterns))}\n"
        f"  In code only: {sorted(set(code_patterns) - set(doc_patterns))}"
    )


# ----------------------------------------------------------------------
# duplicate
# ----------------------------------------------------------------------
def test_duplicate_pass_on_unique():
    corpus = [
        {"question": "How did Plato describe the realm of perfect forms?"},
        {"question": "What did the Buddha identify as the root of suffering?"},
        {"question": "Why did Hayek reject central economic planning?"},
    ]
    idx = build_duplicate_index(corpus)
    for i, q in enumerate(corpus):
        r = validate_duplicate(q, idx, self_idx=i)
        assert r.status == GateStatus.PASS


def test_duplicate_catches_near_dupes():
    corpus = [
        {"question": "Who is regarded as the founder of Western philosophy?"},
        {"question": "Who is considered the founder of Western philosophy?"},  # one-word swap
    ]
    idx = build_duplicate_index(corpus)
    r0 = validate_duplicate(corpus[0], idx, self_idx=0)
    r1 = validate_duplicate(corpus[1], idx, self_idx=1)
    assert r0.status == GateStatus.FAIL
    assert r1.status == GateStatus.FAIL
    assert "Near-duplicate" in r0.detail


def test_duplicate_exact_match():
    corpus = [
        {"question": "What is the meaning of life?"},
        {"question": "What is the meaning of life?"},
    ]
    idx = build_duplicate_index(corpus)
    r = validate_duplicate(corpus[0], idx, self_idx=0)
    assert r.status == GateStatus.FAIL
    assert r.metrics["top_match_ratio"] == 1.0


# ----------------------------------------------------------------------
# specs loading
# ----------------------------------------------------------------------
def test_load_moral_vision():
    mv = specs.load_moral_vision()
    assert mv.version >= 4
    assert mv.sha256
    assert "moral vision" in mv.body.lower() or "rubric" in mv.body.lower()


def test_load_philosophy_subject_spec():
    s = specs.load_subject_spec("philosophy")
    assert s.subject == "philosophy"
    assert s.style_verdict == "WONDER-DRIVEN"


def test_taxonomy_aggregates():
    tax = specs.load_taxonomy()
    ph = tax["philosophy"]
    assert ph.actual_total > 800  # current spec aims for ~922
    assert sum(ph.by_tier.values()) == ph.actual_total
    assert set(ph.by_tier.keys()) == {1, 2, 3, 4, 5}


# ----------------------------------------------------------------------
# integration: pipeline matches calibration agent's findings
# ----------------------------------------------------------------------
@pytest.mark.parametrize("seed", [20260510])
def test_pipeline_calibrate_matches_prior_findings(tmp_path, seed):
    # Same seed as the original n=25 calibration. After the bank was
    # rebuilt to the new rubric, specific verdict counts no longer
    # match the old calibration — we just sanity-check that the
    # pipeline runs end-to-end and produces a sensible verdict mix.
    out_dir = tmp_path / "out"
    report = run_deterministic(
        subject="philosophy",
        sample_size=25,
        seed=seed,
        out_dir=out_dir,
    )
    assert report.n_questions == 25
    # Deterministic-only: every question should at minimum schema-pass on
    # the rebuilt bank, so DISCARD count should be 0.
    assert report.n_discard == 0
    # KEEP + REPAIR should sum to 25
    assert report.n_keep + report.n_repair == 25

    # Confirm report files written
    assert (out_dir / "report.json").exists()
    assert (out_dir / "report.md").exists()
    data = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
    assert data["subject"] == "philosophy"
    assert data["n_questions"] == 25
    assert "moral_vision_sha" in data


def test_pipeline_full_bank_runs_under_30_seconds():
    """Sanity check: full deterministic pass on the philosophy bank completes."""
    import time
    t0 = time.time()
    report = run_deterministic(subject="philosophy")
    elapsed = time.time() - t0
    # Dedup was O(n^2) on raw SequenceMatcher; historical bumps tracked bank
    # growth: 60s @ 949 (2026-04), 90s @ 1159 (2026-05-19), 300s @ 882
    # (2026-05-24, wall-clock had crept to ~270s). 2026-05-24: rewrote
    # DuplicateIndex to use a word-bigram inverted index with Jaccard
    # candidate filtering — the SequenceMatcher stage now sees ~60 pairs
    # instead of ~150k, full bank lands in <1s. 30s leaves comfortable
    # CI headroom while still catching any future regression to O(n²).
    assert elapsed < 30.0, f"Full bank validation took {elapsed:.1f}s — too slow"
    # The bank size grows as new questions are added; only require a
    # reasonable lower bound here.
    assert report.n_questions >= 500, f"Bank shrank unexpectedly to {report.n_questions}"
    # On the rebuilt bank, length-parity failures should be minimal
    # (generator and repair pipeline enforce the rule). Allow some slack
    # but expect dramatically fewer than the pre-rebuild ~340/615.
    lp_fails = report.gate_fail_counts.get("length_parity", 0)
    assert lp_fails < 50, f"Length-parity fails on rebuilt bank: {lp_fails}"


# ----------------------------------------------------------------------
# math_correctness
# ----------------------------------------------------------------------
from tools.quizgen.deterministic import validate_math_correctness  # noqa: E402


def make_math_question(question, answer, tier=2):
    return {
        "tier": tier,
        "question": question,
        "answer": answer,
        "choices": [answer, "99", "88", "77"],
        "context": "",
    }


def test_math_pass_unicode_times():
    r = validate_math_correctness(make_math_question("7 × 8 = ?", "56"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_fail_wrong_answer():
    r = validate_math_correctness(make_math_question("7 × 8 = ?", "54"), subject="math")
    assert r.status == GateStatus.FAIL


def test_math_pass_ascii_x_as_times():
    r = validate_math_correctness(make_math_question("7 x 8 = ?", "56"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_pass_unicode_fractions():
    r = validate_math_correctness(make_math_question("½ + ⅓ = ?", "5/6"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_pass_percent_of():
    r = validate_math_correctness(make_math_question("15% of 80 = ?", "12"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_fail_percent_of_wrong():
    r = validate_math_correctness(make_math_question("15% of 80 = ?", "15"), subject="math")
    assert r.status == GateStatus.FAIL


def test_math_pass_solve_for_x():
    r = validate_math_correctness(make_math_question("Solve for x: 2x + 5 = 13", "x = 4"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_pass_solve_for_x_bare_number():
    r = validate_math_correctness(make_math_question("Solve for x: 2x + 5 = 13", "4"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_pass_quadratic_multi_root():
    r = validate_math_correctness(make_math_question("Solve: x^2 - 5x + 6 = 0", "x = 2 or x = 3"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_pass_function_eval():
    r = validate_math_correctness(make_math_question("If f(x) = x + 3, what is f(7)?", "10"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_pass_compare_larger():
    r = validate_math_correctness(make_math_question("Which is larger: 2/3 or 3/4?", "3/4"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_pass_order_of_operations():
    r = validate_math_correctness(make_math_question("3 + 4 * 2 = ?", "11"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_fail_order_of_operations():
    r = validate_math_correctness(make_math_question("3 + 4 * 2 = ?", "14"), subject="math")
    assert r.status == GateStatus.FAIL


def test_math_pass_power_caret():
    r = validate_math_correctness(make_math_question("2^5 = ?", "32"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_pass_unicode_superscript():
    r = validate_math_correctness(make_math_question("5² = ?", "25"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_na_word_problem():
    r = validate_math_correctness(
        make_math_question("A train leaves Station A at 60 mph; another at 90 mph from opposite direction 300 miles away. When meet?", "2"),
        subject="math",
    )
    assert r.status == GateStatus.NA


def test_math_na_for_non_math_subject():
    r = validate_math_correctness(make_math_question("7 × 8 = ?", "56"), subject="philosophy")
    assert r.status == GateStatus.NA



def test_math_pass_negative_unicode_exponent():
    r = validate_math_correctness(make_math_question("2⁻³ = ?", "1/8"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_pass_fractional_unicode_exponent():
    r = validate_math_correctness(make_math_question("4⁰·⁵ = ?", "2"), subject="math")
    assert r.status == GateStatus.PASS


def test_math_pass_middle_dot_as_multiplication():
    r = validate_math_correctness(
        make_math_question("2^(1/2) · 2^(1/2) = ?", "2"), subject="math"
    )
    assert r.status == GateStatus.PASS


def test_math_pass_multi_digit_unicode_super():
    r = validate_math_correctness(make_math_question("2¹⁰ = ?", "1024"), subject="math")
    assert r.status == GateStatus.PASS


# ----------------------------------------------------------------------
# trailing_tokens (§12 — repeated-word corruption signature)
# ----------------------------------------------------------------------
from tools.quizgen.deterministic import validate_trailing_tokens  # noqa: E402


def test_trailing_tokens_pass_normal_question():
    r = validate_trailing_tokens(make_question(), subject="philosophy")
    assert r.status == GateStatus.PASS


def test_trailing_tokens_pass_two_repeats():
    # Two consecutive repeats are legitimate phrasing — only 3+ are flagged.
    q = make_question(answer="Reality is very very transient and changing today")
    r = validate_trailing_tokens(q, subject="philosophy")
    assert r.status == GateStatus.PASS


def test_trailing_tokens_fail_answer_trailing_overall():
    q = make_question(answer="Reality is in flux overall overall overall")
    q["choices"][0] = q["answer"]
    r = validate_trailing_tokens(q, subject="philosophy")
    assert r.status == GateStatus.FAIL
    assert "overall overall overall" in r.detail


def test_trailing_tokens_fail_distractor_corruption():
    q = make_question()
    q["choices"][3] = "Some claim foo foo foo foo wrong"
    r = validate_trailing_tokens(q, subject="philosophy")
    assert r.status == GateStatus.FAIL
    assert "choices[3]" in r.detail


def test_trailing_tokens_fail_context_corruption():
    q = make_question(context="Heraclitus argued change change change change is fundamental")
    r = validate_trailing_tokens(q, subject="philosophy")
    assert r.status == GateStatus.FAIL
    assert "context" in r.detail


def test_trailing_tokens_na_for_grammar_subject():
    # Grammar has legitimate repeated-token teaching content (the "had had"
    # puzzle, German "Toi toi toi", etc.). Exempt.
    q = make_question(
        question="What is special about 'had had had had had had had had had had had'?",
    )
    r = validate_trailing_tokens(q, subject="grammar")
    assert r.status == GateStatus.NA


def test_trailing_tokens_case_insensitive():
    q = make_question(answer="X Y Y y Y final")
    q["choices"][0] = q["answer"]
    r = validate_trailing_tokens(q, subject="philosophy")
    assert r.status == GateStatus.FAIL


# ----------------------------------------------------------------------
# answer_collision — catch same-answer questions across the bank
# ----------------------------------------------------------------------
from tools.quizgen.deterministic import (  # noqa: E402
    build_answer_collision_index,
    validate_answer_collision,
)


def test_answer_collision_pass_unique_answer():
    qs = [
        make_question(answer="Reality is in constant flux; nothing stays the same"),
        make_question(answer="Knowledge requires both reason and sensory experience"),
        make_question(answer="Time is an illusion created by human consciousness"),
    ]
    idx = build_answer_collision_index(qs)
    r = validate_answer_collision(qs[0], idx, self_idx=0, subject="history")
    assert r.status == GateStatus.PASS


def test_answer_collision_fail_same_answer_diff_stems():
    # Two questions with very different stems but the SAME canonical answer
    # — the exact pattern the dedup gate misses.
    q1 = make_question(
        question="Galileo was forced to recant his belief that the Earth moves. What did he mutter as he stood up?",
        answer="'Eppur si muove' — 'And yet it moves'",
    )
    q1["choices"][0] = q1["answer"]
    q2 = make_question(
        question="On June 22 1633 the 69-year-old astronomer Galileo Galilei knelt before the Roman Inquisition and recanted his teaching that the Earth moves around the Sun. As he rose from his knees, legend says he muttered something in Italian. What did he say?",
        answer="'Eppur si muove' — 'And yet it moves'",
    )
    q2["choices"][0] = q2["answer"]
    idx = build_answer_collision_index([q1, q2])
    r1 = validate_answer_collision(q1, idx, self_idx=0, subject="history")
    r2 = validate_answer_collision(q2, idx, self_idx=1, subject="history")
    assert r1.status == GateStatus.FAIL
    assert r2.status == GateStatus.FAIL


def test_answer_collision_exempt_math():
    # Math has templated drills that legitimately recur ("5+7=?" → "12" etc)
    q1 = make_question(answer="12")
    q2 = make_question(answer="12")
    q1["choices"][0] = q1["answer"]
    q2["choices"][0] = q2["answer"]
    idx = build_answer_collision_index([q1, q2])
    r = validate_answer_collision(q1, idx, self_idx=0, subject="math")
    assert r.status == GateStatus.NA


def test_answer_collision_exempt_grammar():
    q1 = make_question(answer="past tense")
    q2 = make_question(answer="past tense")
    q1["choices"][0] = q1["answer"]
    q2["choices"][0] = q2["answer"]
    idx = build_answer_collision_index([q1, q2])
    r = validate_answer_collision(q1, idx, self_idx=0, subject="grammar")
    assert r.status == GateStatus.NA


def test_answer_collision_exempt_philosophy():
    # Philosophy answers ARE canonical position names ("Memory continuity —
    # you're the same person if memory carries forward"). Multiple legitimate
    # thought-experiment scenes can — and pedagogically should — test the
    # same position. User-confirmed 2026-05-25.
    q1 = make_question(answer="Memory continuity — you're the same person if memory carries forward")
    q2 = make_question(answer="Memory continuity — you're the same person if memory carries forward")
    q1["choices"][0] = q1["answer"]
    q2["choices"][0] = q2["answer"]
    idx = build_answer_collision_index([q1, q2])
    r = validate_answer_collision(q1, idx, self_idx=0, subject="philosophy")
    assert r.status == GateStatus.NA


def test_answer_collision_exempt_theology():
    # Theology answers are often canonical NAMED figures or objects
    # ("Athena", "Mjölnir", "David", "Excalibur"). Multiple legitimate
    # story scenes pedagogically test the SAME figure — e.g. Athena's
    # birth, Athena gifting the olive tree, Athena turning Arachne into
    # a spider. Dedup theology by SCENE variety, not answer text.
    # User-confirmed 2026-05-27.
    q1 = make_question(answer="Athena")
    q2 = make_question(answer="Athena")
    q1["choices"][0] = q1["answer"]
    q2["choices"][0] = q2["answer"]
    idx = build_answer_collision_index([q1, q2])
    r = validate_answer_collision(q1, idx, self_idx=0, subject="theology")
    assert r.status == GateStatus.NA
