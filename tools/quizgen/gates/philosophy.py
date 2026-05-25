"""Philosophy bank structural gates — Phase 2b.

Two layers:
  - Deterministic + heuristic gates (this file): fast, no LLM, no spend.
  - Judgment gates (separate, future): LLM-as-judge using Opus.

Each gate is a callable: question_dict -> Optional[str]
  - returns None on pass
  - returns a one-line failure reason on fail

Usage:
  py tools/quizgen/scratch/philosophy_structural_gates.py [path/to/bank.json]

  If no path given, runs against data/questions/philosophy.json AND the
  exemplar batches (which should all pass) for cross-validation.

Gate inventory (see PHILOSOPHY_TEMPLATES.md §8.1):
  - choice_shape_parity     — all 4 choices share shape
  - anti_pattern_clear      — no banned stem phrasings
  - no_verdict_on_contested — verdict-style banned on contested topics
  - stem_pattern_match      — stem matches an approved pattern for topic+tier
  - scenario_anchored_correct — correct answer uses scenario-specific tokens
  - forcing_constraint      — stem has scenario detail to force a choice
  - register_consistency    — vocab tier matches stem-to-choices
  - answer_position_bias    — bank-level: correct-index roughly uniform
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Callable, Optional


# --------------------------------------------------------------------------
# Topic inference (bank questions don't carry a topic field)
# --------------------------------------------------------------------------

TOPIC_KEYWORDS = {
    'logic_fallacy': [
        'fallacy', 'fallacious', 'reasoning move', 'argument', 'premise',
        'rhetorical', 'valid inference', 'logical', 'inference', 'reason',
    ],
    'ethics': [
        'virtue', 'duty', 'consequence', 'utilitarian', 'kantian',
        'moral', 'ethic', 'good person', 'right thing',
    ],
    'epistemology': [
        'know', 'knowledge', 'justified', 'belief', 'gettier',
        'evidence', 'doubt', 'skeptic', 'JTB',
    ],
    'metaphysics': [
        'identity', 'same person', 'same river', 'same ship', 'exists',
        'real', 'reality', 'persist', 'time', 'change',
    ],
    'mind': [
        'consciousness', 'experience', 'mind', 'qualia', 'phenomenal',
        'mary', 'zombie', 'chinese room', 'subjective',
    ],
    'political': [
        'state', 'authority', 'government', 'right', 'consent',
        'social contract', 'liberty', 'justice', 'sovereign',
    ],
    'religion': [
        'God', 'faith', 'religious', 'divine', 'theology',
        'problem of evil', 'theodicy', 'theist',
    ],
    'aesthetics': [
        'art', 'beauty', 'beautiful', 'aesthetic', 'taste',
        'sublime', 'work of art',
    ],
}

# Topics for which verdict-style stems are NOT allowed (contested)
CONTESTED_TOPICS = {'metaphysics', 'mind', 'aesthetics', 'religion'}
# Topics where yes/no IS a legitimate stem (carve-out)
VERDICT_OK_TOPICS = {'logic_fallacy', 'epistemology'}


def infer_topic(stem: str, context: str = '') -> Optional[str]:
    """Best-effort topic inference. Returns one topic or None."""
    text = (stem + ' ' + context).lower()
    scores = {}
    for topic, kws in TOPIC_KEYWORDS.items():
        scores[topic] = sum(text.count(kw.lower()) for kw in kws)
    best = max(scores.items(), key=lambda kv: kv[1])
    return best[0] if best[1] > 0 else None


# --------------------------------------------------------------------------
# Length caps (deterministic, also enforced earlier in pipeline)
# --------------------------------------------------------------------------

TIER_CAPS = {1: (220, 110, 250), 2: (250, 130, 290), 3: (290, 160, 340),
             4: (340, 190, 400), 5: (400, 230, 480)}


# --------------------------------------------------------------------------
# Gate: choice_shape_parity
# --------------------------------------------------------------------------

EM_DASH = '—'  # —
EN_DASH = '–'  # –


def _has_dash(s: str) -> bool:
    return EM_DASH in s or EN_DASH in s or ' -- ' in s


def _yes_no_prefix(s: str) -> bool:
    stripped = s.lstrip().lower()
    return stripped.startswith(('yes ', 'yes,', 'yes' + EM_DASH,
                                'no ', 'no,', 'no' + EM_DASH,
                                'yes -', 'no -'))


def _choice_shape(c: str) -> str:
    """Classify a single choice's shape — simplified to dash-vs-no-dash.
    Templates §5 requires parallel structure; the chief failure mode is
    'only correct answer has the dash structure', which is exactly what
    has_dash captures."""
    return 'dash' if _has_dash(c) else 'plain'


def gate_choice_shape_parity(q: dict) -> Optional[str]:
    choices = q.get('choices', [])
    if len(choices) != 4:
        return f'choice_shape_parity: expected 4 choices, got {len(choices)}'
    shapes = [_choice_shape(c) for c in choices]
    if len(set(shapes)) > 1:
        # The classic skim-tell case: only one choice has the dash structure
        dash_count = shapes.count('dash')
        if dash_count == 1:
            correct = q.get('answer', '')
            if correct in choices and shapes[choices.index(correct)] == 'dash':
                return 'choice_shape_parity: skim-tell (only correct answer has dash structure)'
        return f'choice_shape_parity: {dash_count}/4 choices use dash structure (must be all or none)'
    return None


# --------------------------------------------------------------------------
# Gate: anti_pattern_clear
# --------------------------------------------------------------------------

_APOS = "['’]"  # straight or curly apostrophe
BANNED_STEM_PATTERNS = [
    rf"what{_APOS}?s wrong",
    r"what is wrong",
    rf"what{_APOS}?s missed",
    r"what is missed",
    rf"where{_APOS}?s the slip",
    r"slips by",
    r"what did .{1,40} avoid",
    rf"what{_APOS}?s the trick",
    r"just spot it",
    r"\bwhich one is it\b",
    r"what is the problem",
    r"\bis (\w+ ){0,3}(really|still|even|truly) the same\b",
    r"\bare you (still |really )?the same\b",
]
_BANNED_RE = re.compile('|'.join(BANNED_STEM_PATTERNS), re.IGNORECASE)


def gate_anti_pattern_clear(q: dict) -> Optional[str]:
    stem = q.get('question', '')
    m = _BANNED_RE.search(stem)
    if m:
        return f'anti_pattern_clear: stem contains banned phrase "{m.group(0)}"'
    return None


# --------------------------------------------------------------------------
# Gate: no_verdict_on_contested
# --------------------------------------------------------------------------

_VERDICT_OPENERS = re.compile(
    r'^\s*(Is|Are|Was|Were|Do|Does|Did|Can|Could|Should|Would|Will)\b',
    re.IGNORECASE
)


def _final_clause(stem: str) -> str:
    """Return the last interrogative clause of the stem."""
    parts = re.split(r'(?<=[.!?])\s+', stem.strip())
    return parts[-1] if parts else stem


def _all_sentences(stem: str) -> list[str]:
    """Split stem into sentences for whole-stem pattern matching."""
    return [s for s in re.split(r'(?<=[.!?])\s+', stem.strip()) if s]


def _looks_verdict_style(q: dict) -> bool:
    stem = q.get('question', '')
    last = _final_clause(stem)
    if not _VERDICT_OPENERS.match(last):
        return False
    # Also check: do at least 2 choices start with Yes/No?
    choices = q.get('choices', [])
    yn = sum(1 for c in choices if _yes_no_prefix(c))
    return yn >= 2


_AMBIGUITY_MARKERS = re.compile(
    r'\b(puzzle|oldest|still (debated|contested|open)|depends|but how|never been (fully|completely) (explained|settled)|hard problem|both sides|either way)\b',
    re.IGNORECASE
)


def gate_no_verdict_on_contested(q: dict) -> Optional[str]:
    if not _looks_verdict_style(q):
        return None
    topic = infer_topic(q.get('question', ''), q.get('context', ''))
    if topic not in CONTESTED_TOPICS:
        return None
    # Carve-out: if the correct answer itself acknowledges the puzzle/ambiguity,
    # the question is not imposing a verdict — it's flagging the unresolved nature.
    correct = q.get('answer', '')
    if _AMBIGUITY_MARKERS.search(correct):
        return None
    return f'no_verdict_on_contested: verdict-style stem on contested topic ({topic})'


# --------------------------------------------------------------------------
# Gate: stem_pattern_match
# --------------------------------------------------------------------------

# Approved stem closers per topic (from PHILOSOPHY_TEMPLATES.md §4).
# Closers are matched against the LAST sentence of the stem.
APPROVED_CLOSERS = {
    'logic_fallacy': [
        r'commits which (logical )?fallacy',
        r'which (logical )?fallacy does .{1,80}commit',
        r'relies on which (logical )?fallacy',
        r'identify the (reasoning )?(rhetorical )?(maneuver|flaw|move)',
        r'diagnose the (rhetorical )?(maneuver|move)',
        r'what (logical )?fallacy does the argument commit',
        r'what is the (rhetorical |reasoning )?(maneuver|move|trick|technique)',
        r'what (rhetorical |reasoning |logical )?(maneuver|move|trick|technique)',
        r'(which|name) (rhetorical |reasoning |logical )?(maneuver|move|fallacy|trick)',
    ],
    'ethics': [
        r'which view of ethics .{1,40}defend',
        r'which (ethical )?(framework|view|position|tradition)',
        r'which (philosophical |ethical )?(response|move|principle)',
        r'which principle .{1,30}(priority|take)',
        r'why is .{1,40}not a good defense',
        r'what makes .{1,40}(right|wrong|virtuous)',
        r'what (would|should) .{1,40}do',
    ],
    'epistemology': [
        r'did .{1,40}(really |actually )?know',
        r'(what|which).{0,30}surviv.{1,20}doubt',
        r'would .{1,30}still be (certain|true|known)',
        r'(strongest|best) reason to doubt',
        r'which conception of knowledge',
        rf'what{_APOS}?s the most careful',
        r'was .{0,30}belief reasonable',
        r'does .{1,40}(really |actually )?count as knowledge',
    ],
    'metaphysics': [
        r'puzzle exposes a tension',
        r'which view (best )?captures',
        r'what makes (you|.{1,30})the same',
        r'which (view|principle) of identity',
        r'which feature settles identity',
        r'which view of (identity|time|persistence)',
    ],
    'mind': [
        r'thought experiment asks',
        r'what does (the )?.{1,40}(case|experiment) expose',
        r'(what|when) does it take .{1,30}conscious',
        r'could .{1,40}have felt',
        r'(which|what) response (best )?engages',
        r'which view of (mind|consciousness)',
        r'(why|why not)',  # tail "Why or why not?" is permitted after main question
    ],
    'political': [
        r'which view (holds|grounds|is)',
        r'where do rights come from',
        r'what (justifies|grounds) (the )?state',
        r'why is .{1,40}not the same',
        r'which (tradition|view|position) .{1,40}(defend|ground|support|hold)',
        r'which view of political authority',
        r'which (tradition|view) (most directly |best )?grounds',
    ],
    'religion': [
        r'which response (actually )?engages',
        r'which (philosophical |theological )?move',
        r'what does the .{1,40}argument claim',
        r'how does .{1,40}handle',
        r'why is .{1,40}not enough',
        r'which view of (faith|religious experience|religion)',
    ],
    'aesthetics': [
        r'which view (best )?handles',
        r'is .{1,40}(genuinely )?art',
        r'what (does|makes) .{1,40}(beautiful|valuable|art)',
        r'which view of (art|aesthetic|value) does',
    ],
}


_QUESTION_CLOSER_WORDS = re.compile(
    r'\b(which|what|how|why|where|identify|diagnose|name|did|does|do|is|are|was|were|can|could|should|would)\b',
    re.IGNORECASE
)


_IMPERATIVE_OR_DECLARATIVE_CLOSERS = re.compile(
    r'\b(identify|diagnose|name (the|which)|choose|select|state|consider|'
    r'exposes? a tension|asks: did|asks: could|the (puzzle|case|thought experiment)\b)',
    re.IGNORECASE
)


def gate_stem_pattern_match(q: dict) -> Optional[str]:
    """Sanity-check that the stem is recognizably interrogative or directive.
    Per-topic approved-closers in templates §4 are advisory but too narrow
    to enforce as a hard gate (high FP rate)."""
    stem = q.get('question', '').strip()
    if stem.endswith('?'):
        if _QUESTION_CLOSER_WORDS.search(stem):
            return None
        return 'stem_pattern_match: stem ends with ? but contains no interrogative word'
    # Non-question stems are allowed if they use an approved imperative/declarative closer
    last = _final_clause(stem)
    if _IMPERATIVE_OR_DECLARATIVE_CLOSERS.search(last):
        return None
    return 'stem_pattern_match: stem is neither a question nor an approved imperative/declarative'


# --------------------------------------------------------------------------
# Gate: scenario_anchored_correct
# --------------------------------------------------------------------------

_STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
    'in', 'on', 'at', 'to', 'of', 'for', 'with', 'by', 'as', 'that',
    'this', 'it', 'its', 'be', 'been', 'has', 'have', 'had', 'do',
    'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
    'so', 'if', 'than', 'then', 'when', 'where', 'who', 'what', 'which',
    'how', 'why', 'because', 'about', 'from', 'into', 'over', 'under',
    'one', 'two', 'three', 'all', 'any', 'some', 'no', 'not', 'yes',
    'just', 'only', 'very', 'really', 'still', 'also', 'even', 'such',
    'you', 'your', 'he', 'his', 'she', 'her', 'we', 'our', 'they', 'their',
    'i', 'my', 'me', 'us', 'him', 'them', 'said', 'says', 'say',
}


def _content_tokens(s: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z'-]+", s.lower())
    return {t for t in tokens if t not in _STOPWORDS and len(t) > 3}


def gate_scenario_anchored_correct(q: dict) -> Optional[str]:
    """Applies to FALLACY questions only (templates §5.1). For these,
    correct = '[Name] — scenario-tied explanation'; distractors =
    '[Name] — generic definition'. The correct answer must contain
    at least one distinctive scenario token. Other topics (ethics,
    metaphysics, etc.) are excluded — they use position-defended shape
    where correct = '[Position] — definition' is the right form."""
    topic = infer_topic(q.get('question', ''), q.get('context', ''))
    if topic != 'logic_fallacy':
        return None
    stem = q.get('question', '')
    correct = q.get('answer', '')
    choices = q.get('choices', [])
    if correct not in choices:
        return None
    stem_toks = _content_tokens(stem)
    if not stem_toks:
        return None
    wrong_choices = [c for c in choices if c != correct]
    wrong_tok_sets = [_content_tokens(c) for c in wrong_choices]
    distinctive = set()
    for t in stem_toks:
        hits = sum(1 for ws in wrong_tok_sets if t in ws)
        if hits <= 1:
            distinctive.add(t)
    if not distinctive:
        return None
    correct_toks = _content_tokens(correct)
    if not (distinctive & correct_toks):
        return 'scenario_anchored_correct: fallacy-question correct answer is generic (no scenario token)'
    return None


# --------------------------------------------------------------------------
# Gate: forcing_constraint
# --------------------------------------------------------------------------


def gate_forcing_constraint(q: dict) -> Optional[str]:
    """Stem must be substantive enough to force a choice. Quoted dialogue
    and named characters count toward specificity even when content
    tokens are sparse."""
    stem = q.get('question', '')
    tier = q.get('tier', 3)
    has_quote = '"' in stem or "'" in stem or '‘' in stem or '“' in stem
    has_named_person = bool(re.search(r"\b[A-Z][a-z]{2,}'?s?\b", stem))
    min_chars = {1: 60, 2: 90, 3: 110, 4: 130, 5: 150}[tier]
    if len(stem) < min_chars:
        return f'forcing_constraint: stem too short ({len(stem)} chars, need {min_chars})'
    toks = _content_tokens(stem)
    min_toks = {1: 6, 2: 8, 3: 10, 4: 12, 5: 14}[tier]
    if len(toks) < min_toks and not (has_quote or has_named_person):
        return f'forcing_constraint: stem too sparse ({len(toks)} content tokens, no quote or named character)'
    return None


# --------------------------------------------------------------------------
# Gate: register_consistency
# --------------------------------------------------------------------------

# Specialist vocabulary that should NOT appear in choices if the stem
# stayed simple. Tier of FIRST allowable use.
SPECIALIST_VOCAB = {
    # Word: minimum tier where it can appear in choices
    'physicalism': 4, 'eliminativism': 5, 'qualia': 4, 'phenomenal': 4,
    'hermeneutic': 5, 'epistemic': 4, 'dialectical': 4, 'noumenon': 5,
    'haecceity': 6, 'quiddity': 6,  # 6 = never
    'consequentialism': 3, 'deontology': 3, 'contractualism': 4,
    'intentionalism': 4, 'eternalism': 4, 'presentism': 4,
}


def gate_register_consistency(q: dict) -> Optional[str]:
    tier = q.get('tier', 3)
    stem_lower = q.get('question', '').lower()
    issues = []
    for c in q.get('choices', []):
        c_lower = c.lower()
        for word, min_tier in SPECIALIST_VOCAB.items():
            if word in c_lower and word not in stem_lower:
                if tier < min_tier:
                    issues.append(f'"{word}" too specialist for T{tier}')
    if issues:
        return f'register_consistency: {"; ".join(issues[:3])}'
    return None


# Note: an earlier draft of this module had `bank_gate_answer_position_bias`
# checking for uniform answer-index distribution. Dropped — quiz_engine.py:280-285
# shuffles choice order at presentation time, so the runtime never sees the bank's
# answer-position bias.


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Gate: context_no_meta_references
# --------------------------------------------------------------------------

_META_LEAK_PATTERNS = re.compile(
    r"§\d+(\.\d+)?[-A-Z]*"                           # §4.5-D, §5.1
    r"|\bthe §"                                       # 'the §...'
    r"|\bThis is the\b.{0,30}\bpattern\b"             # 'This is the X pattern'
    r"|\bpattern at T[12345]\b"                       # 'pattern at T2'
    r"|\b(stem |choice )?pattern (A|B|C|D|E|F)\b"     # 'pattern A' / 'stem pattern B'
    r"|'(Could-X-have-felt|Position-defended|Did-X-know|"
    r"Puzzle-exposes-tension|Which-view-captures|What-makes-X-X|"
    r"Subject-commits|Argument-relies-on|Identify-flaw|Even-if-correct|"
    r"Diagnose-maneuver|What-survives-doubt|Strongest-reason-to-doubt|"
    r"Conception-challenged|Which-question-to-ask|Best-response-holds|"
    r"Principle-priority|Why-not-defense|What-makes-X-right|"
    r"Thought-experiment-asks|What-does-X-expose|What-makes-X-conscious|"
    r"If-A-and-B-which)'",
    re.IGNORECASE,
)


def gate_context_no_meta_references(q: dict) -> Optional[str]:
    """Context field is player-facing; must not contain authoring metadata
    (template section refs, pattern names, tier labels used as labels)."""
    ctx = q.get('context', '')
    m = _META_LEAK_PATTERNS.search(ctx)
    if m:
        return f'context_no_meta_references: context contains authoring meta-reference "{m.group(0)}"'
    return None


PER_QUESTION_GATES: list[tuple[str, Callable[[dict], Optional[str]]]] = [
    ('choice_shape_parity', gate_choice_shape_parity),
    ('anti_pattern_clear', gate_anti_pattern_clear),
    ('no_verdict_on_contested', gate_no_verdict_on_contested),
    ('stem_pattern_match', gate_stem_pattern_match),
    ('scenario_anchored_correct', gate_scenario_anchored_correct),
    ('forcing_constraint', gate_forcing_constraint),
    ('register_consistency', gate_register_consistency),
    ('context_no_meta_references', gate_context_no_meta_references),
]


def run_gates(q: dict) -> dict[str, Optional[str]]:
    return {name: fn(q) for name, fn in PER_QUESTION_GATES}


def run_bank(qs: list[dict]) -> dict:
    """Returns aggregated counts and per-question failure lists."""
    per_gate_fail = {name: 0 for name, _ in PER_QUESTION_GATES}
    fail_examples = {name: [] for name, _ in PER_QUESTION_GATES}
    fail_count = 0
    triple_fail = 0  # questions failing 3+ gates (deep red)
    for q in qs:
        results = run_gates(q)
        failed = [(n, r) for n, r in results.items() if r is not None]
        if failed:
            fail_count += 1
        if len(failed) >= 3:
            triple_fail += 1
        for name, reason in failed:
            per_gate_fail[name] += 1
            if len(fail_examples[name]) < 3:
                fail_examples[name].append({
                    'tier': q.get('tier'),
                    'stem': q.get('question', '')[:120],
                    'reason': reason,
                })
    return {
        'total': len(qs),
        'fail_any': fail_count,
        'fail_3plus': triple_fail,
        'per_gate': per_gate_fail,
        'examples': fail_examples,
    }


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _load(path: Path) -> list[dict]:
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get('questions', [])


def _load_exemplar_modules() -> list[dict]:
    """Pull all batch1-4 exemplars from sibling _exemplars_batch*.py files."""
    here = Path(__file__).parent
    out = []
    for path in sorted(here.glob('_exemplars_batch*.py')):
        ns: dict = {}
        exec(path.read_text(encoding='utf-8'), ns)
        for ex in ns.get('exemplars', []):
            out.append({
                'tier': ex['tier'],
                'question': ex['question'],
                'choices': ex['choices'],
                'answer': ex['choices'][ex['answer_idx']],
                'context': ex['context'],
            })
    return out


def _report(label: str, result: dict, total_target: Optional[int] = None) -> None:
    total = result['total']
    target = total_target or total
    print(f'== {label} ({total} questions) ==')
    print(f"  pass-all-gates: {total - result['fail_any']} ({100*(total-result['fail_any'])/target:.1f}%)")
    print(f"  fail >=1 gate:  {result['fail_any']} ({100*result['fail_any']/target:.1f}%)")
    print(f"  fail >=3 gates: {result['fail_3plus']} ({100*result['fail_3plus']/target:.1f}%)")
    print('  per-gate failures:')
    for name, count in sorted(result['per_gate'].items(), key=lambda kv: -kv[1]):
        print(f'    {name:30s} {count:4d} ({100*count/target:.1f}%)')
    print()


def _print_examples(result: dict) -> None:
    print('Sample failures:')
    for gate, examples in result['examples'].items():
        if not examples:
            continue
        print(f'\n  [{gate}]')
        for ex in examples:
            print(f"    T{ex['tier']}: {ex['stem']}")
            print(f"      -> {ex['reason']}")


def main() -> None:
    if len(sys.argv) > 1:
        qs = _load(Path(sys.argv[1]))
        _report(sys.argv[1], run_bank(qs))
    else:
        # Default: validate against exemplars first (sanity), then bank
        ex_qs = _load_exemplar_modules()
        if ex_qs:
            ex_result = run_bank(ex_qs)
            print('Exemplar cross-check (these should pass cleanly):')
            _report(f'exemplars (batches 1-4)', ex_result)
            if ex_result['fail_any'] > 0:
                print('!! Some exemplars failed — gate may have false positives:')
                _print_examples(ex_result)
                print()
        bank_path = Path('data/questions/philosophy.json')
        if bank_path.exists():
            bank_qs = _load(bank_path)
            bank_result = run_bank(bank_qs)
            _report('philosophy bank', bank_result)
            _print_examples(bank_result)


if __name__ == '__main__':
    main()
