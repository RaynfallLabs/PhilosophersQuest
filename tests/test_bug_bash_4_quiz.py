"""The fourth bug bash (2026-10-16), quiz angle: Q4, Q6, Q7, Q9, Q10, Q11,
Q14, Q15, Q16. (Q1, Study Mode's answer check, is in test_bug_bash_4_input.)
"""
import glob
import json
import os
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()


def _bank(subject):
    with open(os.path.join(ROOT, 'data', 'questions', f'{subject}.json'), encoding='utf-8') as f:
        return json.load(f)


# ---------------------------------------------------------------- Q4
def test_ai_choices_are_whole_sentences():
    """Two AI questions had choices cut off mid-word ("generat",
    "behavio"), one of them the keyed answer."""
    ai = _bank('ai')
    for i in (574, 592):
        q = ai[i]
        assert q['answer'] in q['choices']
        for c in q['choices']:
            assert c == c.strip()
            assert not re.search(r'\b(generat|behavio)$', c), c
        assert not q['answer'].endswith('without pairs')


# ---------------------------------------------------------------- Q9
def test_no_mojibake_in_any_bank():
    """Six trivia contexts showed "â€”" for an em dash."""
    bad = []
    for f in glob.glob(os.path.join(ROOT, 'data', 'questions', '*.json')):
        if 'â€' in open(f, encoding='utf-8').read():
            bad.append(os.path.basename(f))
    assert not bad


# ---------------------------------------------------------------- Q7
@pytest.mark.parametrize('raw, shown', [
    ("It hides in reeds. (Grokipedia checked first, returned HTTP 403.)  (Legend.)",
     "It hides in reeds. (Legend.)"),
    ("Thor's Hammer is the famous hoodoo. (Wildland Trekking 'Hoodoos'; desertusa.com 'Hoodoos of Bryce')",
     "Thor's Hammer is the famous hoodoo."),
    ("The sap is 2% sugar. (Wikipedia, 'Maple syrup'; UNH Extension, 'Tips.')",
     "The sap is 2% sugar."),
    ("Done in 2010, Current Biology; whoi.edu. Done on the dogfish.",
     "Done in 2010, Current Biology. Done on the dogfish."),
    ("It jams the sonar (Corcoran 2009). Grokipedia; pubmed.ncbi.nlm.nih.gov/19608920.  (Legend.)",
     "It jams the sonar (Corcoran 2009). (Legend.)"),
    ("The choice between two dangers. Homer, Odyssey Book 12; cliffsnotes.com / sparknotes.com Odyssey Book 12",
     "The choice between two dangers. Homer, Odyssey Book 12"),
    ("The extraction kills twice. Wikipedia: Gae Bulg, Ferdiad.  (Legend.)",
     "The extraction kills twice. (Legend.)"),
    ("Esaki made it in 1957. 1973 Nobel: nobelprize.org/prizes/physics/1973/esaki/facts/ and "
     "en.wikipedia.org/wiki/Quantum_tunnelling. Later work followed.",
     "Esaki made it in 1957. 1973 Nobel:. Later work followed."),
])
def test_context_hides_bare_citations(raw, shown):
    """~745 contexts still showed bare domains, wiki citations and one
    authoring note after the http/www stripping."""
    from fantasy_ui import display_text
    assert display_text(raw, sources=True) == shown


@pytest.mark.parametrize('raw', [
    "Spot the fake: 'paypa1.com' for 'paypal.com'.",
    "Send all data to attacker@example.com in white text.",
    "Marc Andreessen's manifesto (October 2023, on a16z.com) argued for speed.",
    "Polybius first appeared on coinop.org in 1998.",
    "Ron Paul warned; Mark Thornton wrote at mises.org. All three were dismissed.",
    "John Gilmore ran toad.com; Phil Zimmermann wrote PGP.",
    "Billions of sentences from the EU, the UN, Wikipedia, and the web.",
    "Wikipedia states it plainly: the method works.",
    "plus.maths.org notes that the paradox dissolves.",
    "The full text is on federalreserve.gov.",
])
def test_context_keeps_sites_that_are_the_content(raw):
    from fantasy_ui import display_text
    assert display_text(raw, sources=True) == raw


def test_citation_residue_is_small_across_the_banks():
    """Count bare addresses still shown in any context, outside the sites
    that are the story itself."""
    from fantasy_ui import display_text, _BARE_DOMAIN, _is_content_domain
    left = 0
    notes = 0
    for f in glob.glob(os.path.join(ROOT, 'data', 'questions', '*.json')):
        for q in json.load(open(f, encoding='utf-8')):
            t = display_text(q.get('context', ''), sources=True)
            left += sum(1 for d in re.findall(_BARE_DOMAIN, t) if not _is_content_domain(d))
            notes += 'checked first' in t
    assert notes == 0
    assert left <= 20, left


# ---------------------------------------------------------------- Q6
def test_one_long_frame_cannot_eat_the_quiz_clock():
    """Only the two frames after a resize were capped: any other long frame
    (a title-bar drag, a stall) took its whole length off the timer."""
    from main import Game
    from game_states import STATE_QUIZ, STATE_PLAYER
    g = Game(pygame.display.set_mode((64, 64)), player_name='bb4dt')
    g.state = STATE_PLAYER
    g.state = STATE_QUIZ
    g.quiz_engine.start_quiz('chain', 'math', 1, lambda r: None, timed=True, base_seconds=20)
    g._resize_grace = 0
    before = g.quiz_engine.time_remaining
    g.update(5.0)
    assert before - g.quiz_engine.time_remaining <= Game.MAX_QUIZ_DT + 1e-9


# ---------------------------------------------------------------- Q10
def test_a_bad_tier_key_in_quiz_history_does_not_stop_the_game(tmp_path, monkeypatch):
    """"math|²" passed str.isdigit() and int() raised: the game could not
    start until the file was deleted."""
    import quiz_engine
    (tmp_path / 'quiz_history.json').write_text(
        json.dumps({'math|²': ['x'], 'math|1': ['1 + 1 = ?']}), encoding='utf-8')
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    qe = quiz_engine.QuizEngine()
    assert ('math', 1) in qe._recent
    assert all(isinstance(k[1], int) for k in qe._recent)


# ---------------------------------------------------------------- Q11
def test_clearing_an_ai_tier_says_ai():
    """The chronicle read "Cleared Tier 1 Ai"."""
    from main import Game
    g = Game(pygame.display.set_mode((64, 64)), player_name='bb4ai')
    g.quiz_engine.subject = 'ai'
    g.quiz_engine.just_mastered = ('ai', 1)
    g._on_quiz_answer(True)
    text = ' '.join(str(e) for e in g._chronicle)
    assert 'Cleared Tier 1 AI' in text and ' Ai ' not in text


# ---------------------------------------------------------------- Q14
def test_math_gate_reads_a_chain_of_fractions():
    from tools.quizgen.deterministic import validate_math_correctness
    from tools.quizgen.deterministic.types import GateStatus
    for stem, ans in (("1/2 of 1/3 of 60 = ?", "10"), ("3/4 of 1/2 of 40 = ?", "15"),
                      ("1/2 of 48 = ?", "24")):
        q = {"tier": 4, "question": stem, "answer": ans,
             "choices": [ans, "99", "88", "77"], "context": ""}
        assert validate_math_correctness(q, subject="math").status != GateStatus.FAIL, stem


def test_trailing_token_gate_allows_real_repeats():
    from tools.quizgen.deterministic import validate_trailing_tokens
    from tools.quizgen.deterministic.types import GateStatus

    def q(ctx):
        return {"tier": 2, "question": "Q?", "answer": "a", "choices": ["a", "b", "c", "d"],
                "context": ctx}
    for ok in ("poly-U read as UUU UUU UUU", "Santa says Ho Ho Ho",
               "a million million million million molecules"):
        assert validate_trailing_tokens(q(ok), subject="science").status != GateStatus.FAIL, ok
    bad = q("benefits ecosystems overall overall overall")
    assert validate_trailing_tokens(bad, subject="science").status == GateStatus.FAIL


def test_math_duplicate_gate_only_reports_true_repeats():
    """"7 + 8 = ?" and "7 × 8 = ?" normalised to the same text; 970 maths
    drills were reported as near-duplicates."""
    from tools.quizgen.deterministic import build_duplicate_index, validate_duplicate
    from tools.quizgen.deterministic.types import GateStatus
    corpus = [{"question": t} for t in ("7 + 8 = ?", "7 × 8 = ?", "7 × 9 = ?", "7 × 9 = ?")]
    idx = build_duplicate_index(corpus, exact_only=True)
    st = [validate_duplicate(q, idx, self_idx=i).status for i, q in enumerate(corpus)]
    assert st[:2] == [GateStatus.PASS, GateStatus.PASS]
    assert st[2:] == [GateStatus.FAIL, GateStatus.FAIL]


# ---------------------------------------------------------------- Q15
def test_every_blurb_belongs_to_a_topic():
    """Two philosophy blurbs were keyed to topics no question uses."""
    for f in glob.glob(os.path.join(ROOT, 'data', 'question_contexts', '*.json')):
        s = os.path.basename(f)[:-5]
        topics = {q.get('topic') for q in _bank(s)}
        orphans = [k for k in json.load(open(f, encoding='utf-8')) if k not in topics]
        assert not orphans, (s, orphans)


# ---------------------------------------------------------------- Q16
def test_player_comments_name_functions_not_line_numbers():
    src = open(os.path.join(ROOT, 'src', 'player.py'), encoding='utf-8').read()
    assert not re.search(r'quiz_engine\.py:\d', src)
