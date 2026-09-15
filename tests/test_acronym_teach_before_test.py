"""Acronym teach-before-test CI gate — v2.15.2.

**Rule (CLAUDE.md §16):** any acronym used in a question stem must either be
on the common-knowledge allowlist (kid-obvious in 2026) OR expanded inline
via `Full Name (ACR)` (or `ACR (Full Name)`) on its first appearance in
the stem.

**How the gate works:**
- A snapshot of currently-failing (bank, question_index, acronyms) is
  stored at `tests/data/acronym_violations_baseline.json`. That's the
  grandfathered backlog — 2,119 questions as of v2.15.2.
- On every test run, we recompute current violations.
- Pass if current violations ⊆ baseline. New questions authored after this
  ship MUST pass the acronym rule.
- Fail if a NEW question sneaks in with unexplained acronyms (regression).
- Also fail if a grandfathered violation appears with DIFFERENT acronyms
  (partial rewrite that missed some).

**How to reduce the baseline:** after fixing a batch of questions
(expanding acronyms inline), regenerate the baseline by running
`tools/quiz_gate/rebaseline_acronyms.py`. The baseline should only ever
shrink.

**Why grandfather instead of hard-fail?** The audit found 2,119 existing
violations across 11 banks. Hard-fail would red-build the tree the day
this landed. Grandfather freezes the current mess as an accountable
backlog and blocks any NEW instance from being added.
"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

# ---------------------------------------------------------------------------
# The rule
# ---------------------------------------------------------------------------

BANKS = ['economics','history','philosophy','science','ai','animal','cooking',
         'geography','theology','trivia','grammar']

# Roman numerals through XX + common higher (kings/popes/Super Bowls).
ROMAN = {r for r in ['I','II','III','IV','V','VI','VII','VIII','IX','X',
                     'XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX',
                     'XXI','XXII','XXIII','XXIV','XXV','XXX','XL','L','LX','XC','C','D','M',
                     'XXXI','XXXV','XLII','XLV','XLVIII','LII','LV','LVI','LVIII',
                     'LX','LXX','LXXX','XC']}

# English words that show up in ALL CAPS for emphasis — safe.
# This is deliberately broad. The rule targets UNEXPLAINED ACRONYMS; any
# token that is unambiguously a common English word is not an acronym even
# if it happens to be all-caps in some stem. Add liberally when a new
# English word trips the gate — false positives here waste author effort
# on non-issues while missing no real acronyms (real acronyms don't collide
# with common English words).
EMPHASIS_OK = set("""
    NOT SEE REALLY ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN
    ELEVEN TWELVE THIRTEEN FOURTEEN FIFTEEN TWENTY THIRTY FORTY FIFTY
    HUNDRED THOUSAND MILLION BILLION HALF DOUBLE TRIPLE
    OWN ONLY YES NO OK OKAY WHY WHAT WHERE WHEN HOW WHOSE WHICH
    SECOND FIRST THIRD LAST NEXT NOW THEN HERE THERE ANY
    GOOD BAD BIG SMALL OLD NEW HIGH LOW HOT COLD OPEN SHUT REAL FAKE
    GIRL BOY MAN WOMAN SON DAUGHTER KING QUEEN GOD LOOKS TIP
    ACCEPT EXCEPT WHOM WERE MORE LESS BOTH FOR AND OR IS THE
    ALL SOME NONE FEW MANY OTHER SAME DIFFERENT LAW UP DOWN
    BEST WORST BEFORE AFTER EVER NEVER ALWAYS EVER OWN
    KNOW YOU HE SHE WE THEY MY OUR HIS HER MINE THEIRS HIM
    HEARD SEEN UNSEEN BARE FORMAL RAW HOME LORD KIN NAME
    ELODIE AA BEEN LOOK GOING NOVA DURARE
    WITH TO SHALL RE CAN WOULD COULD SHOULD MAY MIGHT MUST
    THIS THAT THESE THOSE THEM ITS OURS EVERY
    FALSE TRUE PROVE STILL FATHER MOTHER
    ENTIRE BELOW ABOVE OUT INSIDE OUTSIDE INTO ONTO UPON
    KIN NAME SONS TWICE MRT DO OF LOST USING
    DAY DAYS NIGHT WEEK MONTH YEAR HOUR MINUTE SECOND
    HUGE VAST TINY SMALLER LARGER BIGGER
    MUCH LOT LOTS PLENTY ENOUGH
    DEATH LIFE ALIVE DEAD
    KEY LOCK DOOR ROOM HOUSE HOME
    PLUS MINUS TIMES SPLIT ADD ALSO
    MOST LEAST FEW MANY EACH BOTH EITHER NEITHER
    PRICE PRICES COST COSTS PAY PAID
    AWAY BACK GONE HERE THERE
    HIDDEN SEEN UNSEEN CLEAR MURKY OBVIOUS
    USEFUL USELESS HELPFUL HELPLESS
    WANT WANTS WANTED SHARE SHARES SHARED
    LEARN LEARNS LEARNED TELLS TOLD TELL
    RIGHT WRONG SHAPE FORM KIND TYPE
    STOP GO KEEP LEAVE COME LEFT RIGHT
    READ WRITE BUY SELL TRADE
    ARE WAS WERE BE BEEN BEING AM DOES DID HAD HAS HAVE
    ON OFF IN OUT AT BY FROM WITH WITHOUT
    RED GREEN BLUE BLACK WHITE YELLOW ORANGE PURPLE GRAY GREY
    HIGHER LOWER WIDER TIGHTER LOOSER STRONGER WEAKER
    WHOLE PART PIECE SLICE PORTION
    YOUR YOURS
    FEE FEES FINE FINES
    PM AM
    STOP START END BEGIN
    IT ITS IS AS AN
    HELP HURT HEAL HARM
    JOB JOBS WORK WORKED WORKS
    SICK WELL HEALTHY HEALTHILY
    RICH POOR FAIR UNFAIR
    FOOD DRINK EAT DRANK ATE
    WIN LOSE WON LOST WINS LOSES
    PLAY PLAYS PLAYED PLAYING
    BUY BUYS BOUGHT BOUGHT
    RUN RAN RUNS RUNNING WALK WALKS WALKED
    COUNT COUNTS COUNTED COUNTING HUMAN HUMANS PERSON PEOPLE
    TOP BOTTOM MIDDLE CANNOT FRONT SIDE BACK REAR
    YEAR YEARS FREE FREES FREED BETTER WORSE BEST WORST
    MAKE MAKES MADE MAKING GIVE GIVES GIVEN GAVE GIVING
    ORDER ORDERS ORDERED ORDERING NUMBER NUMBERS NUMBERED
    AIR AIRS AIRED HEAD HEADS HEADED THEIR THEIRS
    AMONG AMIDST STRICT STRICTLY STOLEN STEAL STOLE
    SIZE SIZES SIZED MONEY HARD SOFT EVEN ODD VERY
    TITLE TITLES TITLED GOLDEN SILVER BRONZE
    ONCE TWICE THRICE ITSELF ITS THEMSELF
    FEEL FEELS FELT FEELING WILL WON WONT
    KNOW KNOWS KNEW KNOWN KNOWING WIFE HUSBAND CHILD CHILDREN
    FEWER MORE LESSER GREATER LIVE LIVES LIVED LIVING
    PASS PASSES PASSED WEST EAST NORTH SOUTH
    KILL KILLS KILLED KILLING FAST SLOW QUICKER SLOWER
    LIKE LIKES LIKED LIKING LOOSE TIGHT LOOSER TIGHTER
    MEAN MEANS MEANT MEANING TOO ALSO EITHER NEITHER
    RULE RULES RULED RULING ACTUAL ACTUALLY REAL REALLY
    CREATE CREATES CREATED CREATING DROP DROPS DROPPED
    GROW GROWS GREW GROWN GROWING LACK LACKS LACKED
    POLICE POLICING CHOSE CHOSEN CHOOSE CHOOSES CHOOSING
    OWN OWNS OWNED OWNING FAIL FAILS FAILED FAILING
    FASTER SLOWER STRONGER WEAKER LARGER SMALLER
    WORD WORDS WORDED HEART HEARTS FULL EMPTY
    JOIN JOINS JOINED JOINING OIL OILS OILED
    DRY WET WETTER DRIER VALUE VALUES VALUED BLEW BLOW BLOWN
    SCHOOL SCHOOLS SCHOOLING ISN COULDN WOULDN SHOULDN DON DOESN DIDN
    LED LIT LIGHTED DART DARTS DARTED
    NET NETS NETTED CLAP CLAPS CLAPPED
    SICK WELL BETTER STRONG WEAK POWER POWERS POWERED
    PLAY PLAYS PLAYED PLAYING PLAYER PLAYERS
    WORK WORKS WORKED WORKING WORKER WORKERS
    STORE STORES STORED STORING STOP STOPS STOPPED STOPPING
    OPEN OPENS OPENED OPENING SHUT SHUTS SHUTTING
    LEFT RIGHT CENTER MIDDLE ACROSS
    BUY BUYS BOUGHT BUYING SELL SELLS SOLD SELLING
    GIVE GIVES GAVE GIVEN GIVING TAKE TAKES TOOK TAKEN TAKING
    KIDS KID PARENT PARENTS FAMILY FAMILIES
    ONE ONES SOMEONE ANYONE EVERYONE NOBODY
    SHOP SHOPS SHOPPED SHOPPING STORE STORES
    FARM FARMS FARMED FARMING FARMER FARMERS
    FOOD FOODS EAT ATE EATEN EATING DRINK DRANK DRUNK DRINKING
    NEED NEEDS NEEDED NEEDING WANT WANTS WANTED WANTING
    LOVE LOVES LOVED LOVING HATE HATES HATED HATING
    BOOK BOOKS BOOKED BOOKING READ READS READING
    WRITE WRITES WROTE WRITTEN WRITING
    GAME GAMES GAMED GAMING PLAYER PLAYERS
    TEACH TEACHES TAUGHT TEACHING TEACHER TEACHERS
    LEARN LEARNS LEARNED LEARNING STUDENT STUDENTS
    THINK THINKS THOUGHT THINKING SAID SAY SAYS
    GONE WENT COME COMES COMING CAME
    NEW NEWER NEWEST OLD OLDER OLDEST
    NEAR FAR FARTHER FURTHER NEARER
    HAPPY SAD SADDER ANGRY MAD SORRY
    HEALTHY UNHEALTHY SICK WELL FIT UNFIT
    STOOD STOOD STAND STANDS STANDING SAT SIT SITS SITTING
    THROW THROWS THREW THROWN CATCH CATCHES CAUGHT CATCHING
    KEEP KEEPS KEPT KEEPING HOLD HOLDS HELD HOLDING
    OPEN OPENED SHUT SHUTS CLOSED CLOSE CLOSING
    START STARTS STARTED STARTING BEGIN BEGINS BEGAN BEGUN BEGINNING
    END ENDS ENDED ENDING FINISH FINISHES FINISHED FINISHING
    OFF ON UPON UNDER OVER
    RUN JUMP LEAP LEAPT LEAPED HOPS HOPPED HOP
    STAY STAYS STAYED STAYING GO GOES WENT GONE GOING
    HELP HELPS HELPED HELPING WATCH WATCHED WATCHING WATCHES
    WAR WARS PEACE FIGHT FIGHTS FOUGHT FIGHTING BATTLE BATTLES
    SAFE UNSAFE DANGER DANGERS DANGEROUS
    RICH POOR WEALTH WEALTHY POVERTY
    LOST FOUND FIND FINDS FINDING
    MISS MISSED MISSING MISSES
    HIT HITS HITTING SHOT SHOTS SHOOT SHOOTS SHOOTING
    HEAD HEADS HEADED HEADING FEET FOOT LEG LEGS ARM ARMS HAND HANDS
    HOT COLD WARM COOL CHILLY FREEZING BOILING
    HEAVY LIGHT LIGHTER HEAVIER
    LOUD QUIET LOUDER QUIETER
    DEEP SHALLOW DEEPER SHALLOWER
    HIGH LOW HIGHER LOWER
    NEXT LAST FIRST LATEST OLDEST
    THAT WHICH THOSE THESE THIS THEM WHOM
    HERSELF HIMSELF THEMSELVES OURSELVES YOURSELF
    BECAUSE SINCE UNTIL WHILE THOUGH ALTHOUGH
    ABOUT AGAINST AMONG BEHIND BETWEEN BESIDE BEYOND
    RATE RATES RATED RATING BASE BASES BASED
    FINE FINED FIGHT FIGHTING FEE FEES
    PM AM MID MIDDAY NOON MIDNIGHT
    PRINT PRINTS PRINTED PRINTING
    GOLD SILVER BRONZE COPPER STEEL IRON
    TENTH NINTH EIGHTH SEVENTH SIXTH FIFTH FOURTH THIRD SECOND FIRST
    WASTE WASTES WASTED WASTING WASTEFUL
    DO DID DONE DOING DOES
    DOLLAR DOLLARS CENT CENTS PENNY PENNIES POUND POUNDS EURO EUROS
    FORGET FORGETS FORGOT FORGOTTEN
    TODAY TODAYS TONIGHT TOMORROW YESTERDAY
    STRONGEST WEAKEST TALLEST SHORTEST OLDEST YOUNGEST
    SEND SENDS SENT SENDING MAIL MAILS MAILED MAILING
    CALL CALLS CALLED CALLING
    LIST LISTS LISTED LISTING
    FILL FILLS FILLED FILLING EMPTY EMPTIES EMPTIED
    ADD ADDS ADDED ADDING SUM SUMS SUMMED
    SUBTRACT MULTIPLY DIVIDE DIVIDED DIVIDES
    HALF HALVES QUARTER QUARTERS EIGHTH EIGHTHS
    HEAVY LIGHT MEDIUM
    RAISE RAISES RAISED RAISING LOWER LOWERS LOWERED LOWERING
    CHECK CHECKS CHECKED CHECKING TEST TESTS TESTED TESTING
    ANSWER ANSWERS ANSWERED ANSWERING ASK ASKS ASKED ASKING
    QUESTION QUESTIONS QUESTIONED QUESTIONING
""".split())

# Common-knowledge acronyms a 2026 school-age kid can be expected to
# recognize without teaching. Curated — keep tight; if in doubt, expand.
ACRONYM_ALLOW = {'US','USA','UK','EU','UN','TV','DNA','RNA','CO2','H2O',
                 'NBA','NFL','MLB','NHL','AI','AD','BC','BCE','CE',
                 'PhD','MD','MBA','BA','BS','JD','ID','GPS','CT',
                 'GPT','NASA','FBI','CIA','KGB','SS','SAS','SEAL',
                 'WWF','WWE','KFC','CEO','TSA','MRI','ATM','USB',
                 'AKA','ETA','ASAP','DIY','HBO','NBC','ABC','CBS','MTV',
                 'COVID','SARS','CDC','WHO','IQ','EQ',
                 'DC','MCU','NES','SNES','LEGO','MMO','RPG','FPS',
                 'DJ','KJV','USS','USSR','HMS','RAF','SA','UV','MIT'}


def _find_unexplained_acronyms(stem: str) -> list[str]:
    """Return the sorted deduped list of unexplained acronyms in the stem."""
    hits = set()
    for m in re.finditer(r'\b[A-Z]{2,6}\b', stem):
        ac = m.group(0)
        if ac in ACRONYM_ALLOW or ac in EMPHASIS_OK or ac in ROMAN:
            continue
        # Explained inline via parenthetical either direction.
        if re.search(r'\(\s*' + re.escape(ac) + r'\s*\)', stem):
            continue
        if re.search(re.escape(ac) + r'\s*\(', stem):
            continue
        hits.add(ac)
    return sorted(hits)


def _current_violations() -> dict[str, dict[str, list[str]]]:
    """Walk every bank; return {bank: {question_index_str: [acronym,...]}}."""
    out: dict = {}
    for bank in BANKS:
        p = ROOT / 'data' / 'questions' / f'{bank}.json'
        if not p.exists():
            continue
        qs = json.loads(p.read_text(encoding='utf-8'))
        per_bank = {}
        for i, item in enumerate(qs):
            stem = item.get('question', '')
            acr = _find_unexplained_acronyms(stem)
            if acr:
                per_bank[str(i)] = acr
        if per_bank:
            out[bank] = per_bank
    return out


def _load_baseline() -> dict[str, dict[str, list[str]]]:
    p = ROOT / 'tests' / 'data' / 'acronym_violations_baseline.json'
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding='utf-8'))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_new_acronym_violations():
    """The CORE gate. Fails if any question NOT in the grandfathered baseline
    contains unexplained acronyms. Also fails if a grandfathered question's
    violation SET grew (partial rewrite that missed some)."""
    baseline = _load_baseline()
    current = _current_violations()

    new_violations = []
    grown_violations = []

    for bank, per_bank in current.items():
        base_bank = baseline.get(bank, {})
        for qidx, acronyms in per_bank.items():
            if qidx not in base_bank:
                new_violations.append((bank, qidx, acronyms))
                continue
            baseline_set = set(base_bank[qidx])
            current_set = set(acronyms)
            new_in_this_q = current_set - baseline_set
            if new_in_this_q:
                grown_violations.append((bank, qidx, sorted(new_in_this_q)))

    msg_parts = []
    if new_violations:
        msg_parts.append(f'{len(new_violations)} NEW questions with unexplained acronyms:')
        for bank, qidx, acs in new_violations[:12]:
            msg_parts.append(f'  {bank}.{qidx}: {acs}')
        if len(new_violations) > 12:
            msg_parts.append(f'  ... and {len(new_violations) - 12} more.')
    if grown_violations:
        msg_parts.append(f'{len(grown_violations)} EXISTING questions gained new acronyms:')
        for bank, qidx, acs in grown_violations[:6]:
            msg_parts.append(f'  {bank}.{qidx}: added {acs}')
    if msg_parts:
        msg_parts.append('')
        msg_parts.append('Fix by expanding each acronym inline on first use:')
        msg_parts.append('  "LTCM used sophisticated models..."')
        msg_parts.append('  -> "Long-Term Capital Management (LTCM) used sophisticated models..."')
        msg_parts.append('OR add to ACRONYM_ALLOW if kid-obvious in 2026.')

    assert not new_violations and not grown_violations, '\n'.join(msg_parts)


def test_baseline_did_not_grow():
    """Cross-check: total flagged-question count must be <= baseline count.
    Prevents 'sneak a batch of new violations in while fixing an older batch'."""
    baseline = _load_baseline()
    current = _current_violations()

    base_total = sum(len(v) for v in baseline.values())
    curr_total = sum(len(v) for v in current.values())

    assert curr_total <= base_total, (
        f'Acronym violation count grew: baseline={base_total}, current={curr_total}. '
        f'Any fix pass must SHRINK the count, never grow it.')


def test_baseline_snapshot_is_valid_json():
    """Sanity: the baseline file exists and is well-formed."""
    p = ROOT / 'tests' / 'data' / 'acronym_violations_baseline.json'
    assert p.exists(), 'baseline snapshot missing — run tools/quiz_gate/rebaseline_acronyms.py'
    data = json.loads(p.read_text(encoding='utf-8'))
    assert isinstance(data, dict)
    for bank, per_bank in data.items():
        assert bank in BANKS
        for qidx, acronyms in per_bank.items():
            assert isinstance(qidx, str)
            assert isinstance(acronyms, list)
            assert all(isinstance(a, str) for a in acronyms)


def test_allowlists_are_disjoint():
    """The three lists (ROMAN / EMPHASIS_OK / ACRONYM_ALLOW) must be disjoint
    so an entry isn't ambiguously classified."""
    r_e = ROMAN & EMPHASIS_OK
    r_a = ROMAN & ACRONYM_ALLOW
    e_a = EMPHASIS_OK & ACRONYM_ALLOW
    assert not r_e, f'ROMAN & EMPHASIS_OK overlap: {r_e}'
    assert not r_a, f'ROMAN & ACRONYM_ALLOW overlap: {r_a}'
    assert not e_a, f'EMPHASIS_OK & ACRONYM_ALLOW overlap: {e_a}'


def test_common_ltcm_style_pattern_would_be_caught():
    """Regression pin: the LTCM-style question the audit found MUST be caught
    by the rule. If someone widens the allowlist too far, this fires."""
    stem_bad = "LTCM used sophisticated mathematical models to identify..."
    stem_good = ("Long-Term Capital Management (LTCM) used sophisticated mathematical "
                 "models to identify...")
    assert 'LTCM' in _find_unexplained_acronyms(stem_bad), \
        'gate must catch unexpanded LTCM'
    assert 'LTCM' not in _find_unexplained_acronyms(stem_good), \
        'gate must accept expanded LTCM'
