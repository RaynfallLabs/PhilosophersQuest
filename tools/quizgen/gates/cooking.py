"""Cooking bank structural gates.

Reuses gates from animal_structural_gates (which itself reuses some from philosophy)
and adds cooking-specific:
  - cooking-specific toddler-banned answers (pizza, hamburger, pasta, etc.)
  - cooking-specific anti-pattern stems (fad diet moralism, recipe memorization, etc.)
  - cooking-specific wonder vocab
  - subject_named: non-D patterns must name the subject of analysis in the stem
  - no_food_moralism: stems cannot ask "is X bad/good for you?" verdict questions
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Callable, Optional

from tools.quizgen.gates.philosophy import (
    gate_choice_shape_parity,
    gate_context_no_meta_references,
    _content_tokens,
)


TIER_CAPS = {1: (200, 90, 200), 2: (240, 110, 240),
             3: (280, 130, 300), 4: (320, 160, 360),
             5: (360, 180, 420)}


# --------------------------------------------------------------------------
# Gate: schema
# --------------------------------------------------------------------------


def gate_schema(q: dict) -> Optional[str]:
    for field in ('tier', 'question', 'answer', 'choices', 'context'):
        if field not in q:
            return f'schema: missing field {field}'
    if q.get('tier') not in (1, 2, 3, 4, 5):
        return f'schema: invalid tier {q.get("tier")}'
    chs = q.get('choices', [])
    if len(chs) != 4:
        return f'schema: choices length {len(chs)}'
    if q.get('answer') not in chs:
        return 'schema: answer not in choices'
    return None


# --------------------------------------------------------------------------
# Gate: length_budget
# --------------------------------------------------------------------------


def gate_length_budget(q: dict) -> Optional[str]:
    """Stem + per-choice budgets enforced; context is UNCAPPED.

    Per SHARED_PRINCIPLES.md §9: context is teaching content shown AFTER the
    answer, read at the player's pace — not under timer pressure. Capping it
    forces shallow educational depth, which fights moral_vision.md §"Beauty
    of mechanism" + §"Curiosity over completion". Context cap removed
    2026-05-24 per cooking audit §2 (cooking templates §6 should also be
    updated to mark context uncapped). Mirrors geography 2026-05-23.
    """
    tier = q.get('tier', 3)
    sc, cc, _ctxc_legacy = TIER_CAPS[tier]
    if len(q.get('question', '')) > sc:
        return f'length_budget: stem {len(q["question"])} > {sc}'
    for i, c in enumerate(q.get('choices', [])):
        if len(c) > cc:
            return f'length_budget: choice[{i}] {len(c)} > {cc}'
    return None


# --------------------------------------------------------------------------
# Gate: length_parity
# --------------------------------------------------------------------------


def gate_length_parity(q: dict) -> Optional[str]:
    choices = q.get('choices', [])
    if len(choices) != 4:
        return f'length_parity: expected 4 choices, got {len(choices)}'
    lens = [len(c) for c in choices]
    if min(lens) == 0:
        return 'length_parity: zero-length choice'
    ratio = max(lens) / min(lens)
    if ratio > 1.30:
        return f'length_parity: max/min ratio {ratio:.2f} > 1.30'
    mean = sum(lens) / 4
    dev = max(abs(l - mean) / mean for l in lens)
    if dev > 0.15:
        return f'length_parity: max deviation {100*dev:.1f}% > 15%'
    return None


# --------------------------------------------------------------------------
# Gate: no_toddler_recall (cooking-specific)
# --------------------------------------------------------------------------

TODDLER_BANNED_ANSWERS = {
    # Foods toddlers know
    'pizza', 'hamburger', 'burger', 'french fries', 'fries', 'spaghetti',
    'pasta',  # generic; specific names like tagliatelle/orecchiette fine
    'bread',  # generic; specific names like ciabatta/naan/injera fine
    'ice cream', 'ice-cream',
    'cake',  # generic; specific cakes fine
    'cookie', 'cookies', 'sandwich', 'sandwiches',
    'hot dog', 'hotdog',
    # Toddler-trivial ingredients as answers
    'salt', 'sugar',
    # Toddler-trivial kitchen equipment
    'oven', 'stove', 'pan', 'knife', 'fork', 'spoon', 'plate', 'bowl',
    'frying pan',
    # Toddler-trivial cooking methods
    'boiling', 'frying', 'baking', 'grilling', 'steaming',
    # Toddler-trivial produce
    'carrot', 'potato', 'tomato', 'onion', 'apple', 'banana', 'lettuce',
}

TODDLER_BANNED_STEMS = [
    r"\bwhat (is|do you call) (a |an |the )?(round flat baked food|food made of dough)",
    r"\bwhat (is|do you call) (a |an |the )?(orange root vegetable|red sauce|round fruit)",
    r"\bwhat (is|do you call) (a |an |the )?(white salty crystal|sweet white crystal)",
    r"\bwhat (is|do you call) (a |an )?(cooking food on a grill|cooking with oil in a pan)",
    r"\bwhat (is|do you call) (a |an )?(baby chef|kid chef)",
    r"\bin (a |the )?(kitchen|pantry), what is (a |an |the )",
    # Pure date / year recall
    r"\bin what year did .{1,40}(open|publish|invent|create)",
    r"\bwhat year did .{1,40}(open|publish|invent|create)",
    # Pure restaurant trivia
    r"\bwhat restaurant did .{1,40}work at",
    r"\bwhat (was|is) the name of .{1,40}restaurant",
    # Recipe memorization
    r"\bhow many (cups|tablespoons|teaspoons|grams) of \w+ (in|for) (a |the )",
    # Fad diet moralism (these are food-politics verdict questions)
    r"\bis (gluten|sugar|meat|fat|carbs|dairy) (bad|unhealthy|harmful|good)",
    r"\bshould (everyone|you|we|people|kids) be (vegan|vegetarian|keto|paleo|carnivore)",
    r"\bare (processed foods|GMOs?|gmos?|fast foods?|sugary drinks?) (bad|poison|harmful|unhealthy|good)",
    r"\bis (kosher|halal|hindu vegetarian|buddhist) (right|correct|valid|wrong|true)",
    r"\bwhat does (saute|sautee|sauter|al dente|mise en place|julienne|brunoise) mean\b",
    # Kindergarten phrasings
    r"\bjust spot it\b",
    r"\bwhich one is it\b",
]
_TODDLER_STEM_RE = re.compile('|'.join(TODDLER_BANNED_STEMS), re.IGNORECASE)


def gate_no_toddler_recall(q: dict) -> Optional[str]:
    stem = q.get('question', '')
    answer = q.get('answer', '').strip().lower()
    m = _TODDLER_STEM_RE.search(stem)
    if m:
        return f'no_toddler_recall: stem matches banned phrasing "{m.group(0)}"'
    # Strip leading articles/punctuation; lower
    stripped = re.sub(r'^(a |an |the )', '', answer).strip(' .,"\'')
    # Also strip after first em-dash so "Pizza — round flat baked food" → "Pizza"
    if '—' in stripped:
        stripped = stripped.split('—')[0].strip()
    if '–' in stripped:
        stripped = stripped.split('–')[0].strip()
    if stripped in TODDLER_BANNED_ANSWERS:
        return f'no_toddler_recall: correct answer is toddler-banned "{stripped}"'
    return None


# --------------------------------------------------------------------------
# Gate: anti_pattern_clear (cooking-specific)
# --------------------------------------------------------------------------

COOKING_BANNED_STEM_PATTERNS = [
    # Already covered above but bundled here for documentation
    r"\bwhat does (the (term|word) )?['\"]?(saute|sautee|saut[éè]|al dente|mise en place|julienne|brunoise|roux|deglaze|reduce|emulsify)['\"]? mean",
    r"\bis (gluten|sugar|meat|fat|carbs|dairy) (bad|unhealthy|harmful|good)",
    r"\bare (processed foods|GMOs?|fast foods?) (bad|poison|harmful|unhealthy)",
    r"\bshould (everyone|you|we) (be vegan|stop eating)",
    r"\bin what year did .{1,40}(open|publish|invent|create)",
]
_COOKING_BANNED_RE = re.compile('|'.join(COOKING_BANNED_STEM_PATTERNS), re.IGNORECASE)


def gate_anti_pattern_clear(q: dict) -> Optional[str]:
    stem = q.get('question', '')
    m = _COOKING_BANNED_RE.search(stem)
    if m:
        return f'anti_pattern_clear: banned phrasing "{m.group(0)}"'
    return None


# --------------------------------------------------------------------------
# Gate: forcing_constraint (cooking)
# --------------------------------------------------------------------------


def gate_forcing_constraint(q: dict) -> Optional[str]:
    stem = q.get('question', '')
    tier = q.get('tier', 3)
    min_chars = {1: 50, 2: 70, 3: 90, 4: 110, 5: 130}[tier]
    if len(stem) < min_chars:
        return f'forcing_constraint: stem too short ({len(stem)} chars, need {min_chars})'
    toks = _content_tokens(stem)
    min_toks = {1: 6, 2: 8, 3: 10, 4: 12, 5: 14}[tier]
    if len(toks) < min_toks:
        return f'forcing_constraint: stem too sparse ({len(toks)} content tokens)'
    return None


# --------------------------------------------------------------------------
# Gate: wonder_bias_check (cooking)
# --------------------------------------------------------------------------

_WONDER_WORDS = {
    # Food / cooking nouns
    'food', 'cuisine', 'dish', 'meal', 'recipe', 'flavor', 'taste', 'aroma',
    'texture', 'ingredient', 'ingredients', 'spice', 'spices', 'herb', 'herbs',
    'sauce', 'sauces', 'soup', 'broth', 'stock', 'gravy', 'dressing', 'marinade',
    'bread', 'dough', 'batter', 'pastry', 'cake', 'pie', 'tart', 'cookie',
    'meat', 'fish', 'seafood', 'poultry', 'beef', 'pork', 'lamb', 'chicken',
    'cheese', 'butter', 'cream', 'milk', 'yogurt', 'egg', 'eggs', 'oil',
    'vinegar', 'salt', 'sugar', 'honey', 'syrup', 'wine', 'beer', 'tea', 'coffee',
    'vegetable', 'vegetables', 'fruit', 'fruits', 'grain', 'grains', 'rice', 'pasta',
    'noodle', 'noodles', 'pepper', 'garlic', 'onion', 'tomato', 'potato', 'carrot',
    # Cooking science
    'maillard', 'fermentation', 'ferment', 'fermented', 'emulsion', 'emulsifier',
    'gluten', 'starch', 'protein', 'enzyme', 'enzymes', 'denaturation', 'denatured',
    'gelation', 'gel', 'pectin', 'agar', 'collagen', 'gelatin', 'lecithin',
    'caramelization', 'caramelize', 'caramelized', 'oxidation', 'reduction',
    'hydrolysis', 'hydrocolloid', 'acid', 'alkaline', 'base', 'ph', 'tannin',
    'yeast', 'bacteria', 'lactobacillus', 'mold', 'koji', 'aspergillus',
    'molecule', 'molecules', 'chemistry', 'reaction', 'compound', 'compounds',
    'amino', 'sugar', 'carbohydrate', 'fat', 'fats', 'lipid', 'umami', 'glutamate',
    # Cooking verbs
    'cook', 'cooks', 'cooked', 'cooking', 'bake', 'bakes', 'baked', 'baking',
    'roast', 'roasts', 'roasted', 'roasting', 'broil', 'broils', 'broiled',
    'fry', 'fries', 'fried', 'frying', 'saute', 'saut', 'sauteed', 'sauteing',
    'boil', 'boils', 'boiled', 'boiling', 'simmer', 'simmers', 'simmered',
    'poach', 'poaches', 'poached', 'poaching', 'steam', 'steams', 'steamed',
    'grill', 'grills', 'grilled', 'grilling', 'smoke', 'smokes', 'smoked',
    'sear', 'sears', 'seared', 'searing', 'braise', 'braises', 'braised',
    'stew', 'stews', 'stewed', 'reduce', 'reduces', 'reduced', 'reducing',
    'ferment', 'cure', 'cures', 'cured', 'curing', 'pickle', 'pickles', 'pickled',
    'brine', 'brines', 'brined', 'brining', 'salt', 'salted', 'salting',
    'whisk', 'whisks', 'whisked', 'whisking', 'fold', 'folds', 'folded',
    'mix', 'mixes', 'mixed', 'mixing', 'knead', 'kneads', 'kneaded', 'kneading',
    'chop', 'chops', 'chopped', 'chopping', 'slice', 'slices', 'sliced',
    'dice', 'dices', 'diced', 'mince', 'minces', 'minced', 'julienne', 'brunoise',
    'roll', 'rolls', 'rolled', 'rolling', 'shape', 'shapes', 'shaped',
    'rise', 'rises', 'risen', 'rising', 'proof', 'proofs', 'proofed',
    'taste', 'tastes', 'tasted', 'tasting', 'smell', 'smells', 'smelled',
    'melt', 'melts', 'melted', 'melting', 'crystallize', 'crystallized',
    'pop', 'pops', 'popped', 'popping', 'rest', 'rests', 'rested', 'resting',
    'season', 'seasons', 'seasoned', 'seasoning', 'glaze', 'glazes', 'glazed',
    # Equipment / tools (named cooking implements)
    'oven', 'stove', 'pan', 'pot', 'skillet', 'kettle', 'wok', 'griddle',
    'knife', 'cleaver', 'whisk', 'spatula', 'tongs', 'ladle',
    # Cultural / traditional
    'french', 'italian', 'japanese', 'chinese', 'korean', 'indian', 'mexican',
    'thai', 'spanish', 'german', 'greek', 'turkish', 'persian', 'arab', 'arabic',
    'middle east', 'mediterranean', 'asian', 'african', 'caribbean', 'european',
    'american', 'southern', 'cajun', 'creole', 'southwestern', 'tex-mex',
    'cuisine', 'tradition', 'traditional', 'regional', 'heritage', 'ancient',
    'medieval', 'renaissance', 'roman', 'greek', 'colonial', 'modern',
    'monastic', 'monk', 'monks', 'monastery', 'crusader', 'crusades',
    'kitchen', 'restaurant', 'chef', 'cook', 'baker', 'butcher', 'charcutier',
    'brigade', 'kitchen', 'station', 'mise en place',
    # Historical/cultural anchors
    'escoffier', 'careme', 'brillat-savarin', 'beard', 'child', 'fisher',
    'columbian', 'exchange', 'spice', 'trade', 'silk', 'road',
    'aoc', 'appellation', 'terroir', 'farm', 'farming', 'agriculture',
    'preservation', 'preserve', 'preserved', 'preserves', 'preserving',
    'pollan', 'sowell', 'hayek', 'bastiat', 'friedman',
    # Etiquette
    'etiquette', 'manners', 'napkin', 'fork', 'spoon', 'plate', 'tablecloth',
    'serve', 'served', 'serving', 'course', 'courses', 'banquet', 'feast', 'dinner',
    'lunch', 'breakfast', 'supper', 'meal',
    'toast', 'toasts', 'toasting', 'host', 'guest', 'hospitality',
    # Religious dietary
    'kosher', 'halal', 'lent', 'lenten', 'fast', 'fasting', 'feast',
    'hindu', 'jain', 'buddhist', 'jewish', 'muslim', 'christian', 'orthodox',
    'catholic', 'protestant',
    # Numbers / measurement
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'dozen', 'dozens', 'hundred', 'hundreds', 'thousand', 'thousands',
    'percent', 'degree', 'degrees', 'celsius', 'fahrenheit', 'centigrade',
    'minute', 'minutes', 'hour', 'hours', 'day', 'days', 'week', 'weeks',
    'month', 'months', 'year', 'years', 'century', 'centuries',
    # Generic action / change verbs
    'use', 'uses', 'used', 'using', 'change', 'changes', 'changed', 'changing',
    'become', 'becomes', 'became', 'becoming', 'turn', 'turns', 'turned',
    'transform', 'transforms', 'transformed', 'develop', 'develops', 'developed',
    'form', 'forms', 'formed', 'forming', 'produce', 'produces', 'produced',
    'release', 'releases', 'released', 'absorb', 'absorbs', 'absorbed',
    # Comparative framing
    'only', 'unique', 'uniquely', 'unlike', 'differs', 'differ', 'difference',
    'compared', 'comparison', 'distinct', 'distinctive', 'shared', 'common',
    'surprising', 'bizarre', 'strange', 'remarkable', 'extraordinary',
    'unusual', 'striking', 'why', 'because', 'reason',
}


def gate_wonder_bias_check(q: dict) -> Optional[str]:
    stem = q.get('question', '')
    if re.search(r'\d', stem):
        return None
    stem_words = set(re.findall(r"[A-Za-z][A-Za-z'-]+", stem.lower()))
    if stem_words & _WONDER_WORDS:
        return None
    return 'wonder_bias_check: stem lacks wonder signal (no food/cooking vocab, number, or comparative framing)'


# --------------------------------------------------------------------------
# Gate: subject_named (NEW for cooking — addresses kimchi-style failure)
# --------------------------------------------------------------------------


def gate_subject_named(q: dict) -> Optional[str]:
    """Non-D patterns should NAME the subject of analysis in the stem.
    Heuristic: if stem ends with 'What is it?' / 'Which is this?' / 'Identify the X' /
    'What is the dish/technique/cuisine?' AND the pattern label isn't D, flag.

    Pattern info isn't stored in bank format (tier/question/answer/choices/context),
    so we apply this as a permissive check: only flag stems that pose a
    "what is this?" question without describing-then-identifying a clearly
    novel/non-obvious term."""
    stem = q.get('question', '').strip()
    # Identify-style questions
    identify_re = re.compile(
        r"(what is it|which (is this|is it)|identify the (dish|technique|cuisine|tradition|ingredient)|"
        r"what is the (dish|cuisine|tradition))\??\s*$",
        re.IGNORECASE,
    )
    if not identify_re.search(stem):
        return None
    # Allow if the answer text leads with a specific named term defined inline.
    # Legitimate patterns: "A roux — ...", "An emulsion — ...", "The Maillard reaction — ...",
    # "Kimchi is a fermented...", "Béchamel — French mother sauce..."
    answer = q.get('answer', '')
    # Strip leading article + lowercase, allow proper-noun + em-dash, OR
    # leading lowercase term + em-dash (e.g., "kimchi — ...")
    if re.match(r"^(A |An |The )?[A-Za-z][a-zA-Zà-ÿ'-]{2,}\s*[—–-]", answer):
        return None
    # Also allow if all 4 choices have the dash structure — that's parallel
    # name-defining shape, which by construction means the choices are teaching terms.
    choices = q.get('choices', [])
    if choices and all('—' in c or '–' in c for c in choices):
        return None
    return 'subject_named: non-identify question asks "what is it?" without naming the subject of analysis'


# --------------------------------------------------------------------------
# Gate: stem_answer_overlap
# --------------------------------------------------------------------------

# Words that are okay to repeat between stem and answer (topic anchors, not telegraphing)
_STOPLIKE = {
    'cooking', 'cuisine', 'cuisines', 'cook', 'cooks', 'food', 'foods',
    'kitchen', 'restaurant', 'chef',
    'is', 'are', 'was', 'were', 'has', 'have', 'had', 'be', 'been', 'being',
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'of', 'for',
    'with', 'by', 'as', 'that', 'this', 'it', 'its', 'they', 'their', 'them',
    'these', 'those', 'all', 'any', 'some', 'one', 'two', 'three',
    'when', 'where', 'why', 'how', 'what', 'which', 'who',
    'each', 'both', 'either', 'neither', 'same', 'different',
    'tradition', 'traditional', 'recipe', 'method', 'methods',
}


def _distinctive_tokens(text: str) -> set[str]:
    """Lowercase content tokens length>=4 not in stop-like set."""
    toks = re.findall(r"[A-Za-z][A-Za-z'-]+", text.lower())
    return {t for t in toks if len(t) >= 4 and t not in _STOPLIKE}


def gate_stem_answer_overlap(q: dict) -> Optional[str]:
    """Flag when the correct answer's distinctive content tokens are mostly
    contained in the stem — the stem is telegraphing the answer.

    EXEMPT Pattern I (Non-obvious term) and Pattern D (Identify-by-trait):
    these LEGITIMATELY have answers that name a term + describe what was set
    up in the stem. Detected by: answer leads with "[Term] —" (em-dash structure)
    AND the stem asks "What is it?" / "What is the [noun] called?" — the test
    is naming the term.

    Example failure caught: stem says "Each tradition picks a different cut
    and cure" + asks "What is the axis of difference?" → answer "Cut and cure
    differ; ..." — circular."""
    stem = q.get('question', '').strip()
    answer = q.get('answer', '')
    # Exempt Pattern I/D: answer leads with a Capitalized term (1-5 words,
    # including connectors of/and/the/the/+slash) + em-dash, OR term + comma
    # + description ("Great heron, a tall white wading bird that...").
    # These shapes legitimately restate stem content in the term-defining
    # post-em-dash/post-comma explanation.
    answer_term_dash = re.match(
        r"^(A |An |The )?[A-Za-zà-ÿ][a-zA-Zà-ÿ'-]+"
        r"(?:\s+(?:of |and |/ |the )?[A-Za-zà-ÿ][a-zA-Zà-ÿ'-]+){0,4}"
        r"\s*[—–\-/]\s*[—–]?",
        answer,
    )
    answer_term_comma = re.match(
        r"^(A |An |The )?[A-Za-zà-ÿ][a-zA-Zà-ÿ'-]+"
        r"(?:\s+[A-Za-zà-ÿ][a-zA-Zà-ÿ'-]+){0,3}"
        r",\s+(?:a |an |the )?",
        answer,
    )
    if answer_term_dash or answer_term_comma:
        return None
    # Exempt: stem contains the answer's opening 2-3 words in quotes
    # (stem is quoting the topic; answer is elaborating)
    ans_words = re.findall(r"[A-Za-z][A-Za-z'-]+", answer)
    if len(ans_words) >= 2:
        for n in (3, 2):
            if len(ans_words) >= n:
                phrase = ' '.join(ans_words[:n]).lower()
                # Search for phrase in stem within quotes
                if re.search(rf"['\"]\s*{re.escape(phrase)}.*?['\"]", stem.lower()):
                    return None
    stem_toks = _distinctive_tokens(stem)
    ans_toks = _distinctive_tokens(answer)
    if len(ans_toks) < 3:
        return None
    overlap = stem_toks & ans_toks
    overlap_pct = len(overlap) / len(ans_toks)
    if overlap_pct > 0.65:
        shared = sorted(overlap)[:8]
        return f'stem_answer_overlap: answer reuses {len(overlap)}/{len(ans_toks)} ({100*overlap_pct:.0f}%) distinctive stem tokens — telegraphing. Shared: {shared}'
    # ALSO check: does the answer's OPENING contain a 3+ word phrase that
    # appears verbatim in the stem? Catches cut/cure-style failures where the
    # answer literally re-asserts what the stem already said.
    # ("Cut and cure differ" with stem containing "different cut and cure")
    ans_words = re.findall(r"[A-Za-z][A-Za-z'-]+", answer.lower())
    stem_lower = stem.lower()
    # Try 4-word, then 3-word opening phrases (excluding leading articles)
    skip_leading = {'a', 'an', 'the'}
    start = 0
    while start < len(ans_words) and ans_words[start] in skip_leading:
        start += 1
    for n in (4, 3):
        if start + n <= len(ans_words):
            phrase = ' '.join(ans_words[start:start+n])
            # Require at least one non-stoplike word in phrase
            content_count = sum(1 for w in ans_words[start:start+n] if w not in _STOPLIKE and len(w) >= 3)
            if content_count >= 2 and phrase in stem_lower:
                return f'stem_answer_overlap: answer opens with phrase "{phrase}" appearing verbatim in stem'
    return None


# --------------------------------------------------------------------------
# Gate: comparative_completeness
# --------------------------------------------------------------------------


_CUISINE_PROPER_NOUNS = {
    'Chinese', 'Japanese', 'Korean', 'Indian', 'Italian', 'French', 'Spanish',
    'German', 'Mexican', 'Thai', 'Vietnamese', 'Mediterranean', 'Persian',
    'Turkish', 'Greek', 'Russian', 'British', 'American', 'Ethiopian', 'Moroccan',
    'Tunisian', 'Lebanese', 'Syrian', 'Iranian', 'Iraqi', 'Egyptian',
    'Sicilian', 'Tuscan', 'Roman', 'Venetian', 'Lyonnaise', 'Provençal',
    'Cantonese', 'Sichuan', 'Hunan', 'Hakka', 'Mughlai', 'Goan', 'Punjabi',
    'Oaxacan', 'Yucatecan', 'Pueblan', 'Cajun', 'Creole', 'Texan',
    'Norse', 'Scandinavian', 'Bavarian', 'Alsatian', 'Catalan', 'Basque',
    'Andalusian', 'Genovese', 'Neapolitan', 'Bolognese',
}

# Adjective-form ↔ noun-form equivalents (answer often uses the country/region
# name rather than the cuisine adjective, e.g. stem says "Sicilian" and "Spanish",
# answer says "Sicily" and "Spain" — same comparison subjects).
_CUISINE_NOUN_FORMS = {
    'Chinese': 'china', 'Japanese': 'japan', 'Korean': 'korea',
    'Indian': 'india', 'Italian': 'italy', 'French': 'france',
    'Spanish': 'spain', 'German': 'germany', 'Mexican': 'mexico',
    'Thai': 'thailand', 'Vietnamese': 'vietnam', 'Persian': 'persia',
    'Turkish': 'turkey', 'Greek': 'greece', 'Russian': 'russia',
    'British': 'britain', 'American': 'america', 'Ethiopian': 'ethiopia',
    'Moroccan': 'morocco', 'Tunisian': 'tunisia', 'Lebanese': 'lebanon',
    'Syrian': 'syria', 'Iranian': 'iran', 'Iraqi': 'iraq', 'Egyptian': 'egypt',
    'Sicilian': 'sicily', 'Tuscan': 'tuscany', 'Roman': 'rome',
    'Venetian': 'venice', 'Cantonese': 'canton',
    'Norse': 'norway', 'Bavarian': 'bavaria', 'Alsatian': 'alsace',
    'Catalan': 'catalonia', 'Basque': 'basque',
    'Andalusian': 'andalusia', 'Genovese': 'genoa',
    'Neapolitan': 'naples', 'Bolognese': 'bologna',
}

_COMPARE_MARKERS = re.compile(
    r'\b(?:both|each|either|neither|versus|vs\.?|compared|comparison|'
    r'difference between|different (?:methods|ways|approaches|techniques|cuisines|traditions)|'
    r'why do (?:the|both)|distinguish|distinct from|in contrast)\b',
    re.IGNORECASE
)


def gate_comparative_completeness(q: dict) -> Optional[str]:
    """When stem explicitly compares two+ named cuisines/traditions and uses
    an explicit comparison marker (both, vs, why do X and Y, different methods),
    the answer should address all named subjects.

    Catches the Chinese-vs-Mediterranean fish case: stem mentions both
    cuisines + "different methods" → answer must mention both."""
    stem = q.get('question', '')
    answer = q.get('answer', '')
    if not _COMPARE_MARKERS.search(stem):
        return None
    # Find cuisine proper nouns mentioned in the stem
    stem_cuisines = set()
    for cuisine in _CUISINE_PROPER_NOUNS:
        if re.search(rf'\b{cuisine}\b', stem):
            stem_cuisines.add(cuisine)
    if len(stem_cuisines) < 2:
        return None
    # Extract cuisine→dish pairings from the stem (e.g. "Japanese dashi" maps
    # Japanese → dashi; answer mentioning "dashi" counts as addressing Japanese).
    cuisine_dish = {}
    for c in stem_cuisines:
        m = re.search(rf'\b{c}\s+([a-z]{{3,}})\b', stem)
        if m:
            cuisine_dish[c] = m.group(1).lower()
    # Check all are present in answer — accept adjective form, noun form,
    # OR a uniquely-paired dish name extracted from the stem.
    ans_lower = answer.lower()
    missing = []
    for c in stem_cuisines:
        adj_present = c.lower() in ans_lower
        noun_form = _CUISINE_NOUN_FORMS.get(c)
        noun_present = noun_form and noun_form in ans_lower
        dish = cuisine_dish.get(c)
        dish_present = dish and dish in ans_lower
        if not (adj_present or noun_present or dish_present):
            missing.append(c)
    if not missing or len(missing) == len(stem_cuisines):
        return None
    # Supertype exemption: if missing items are supertypes AND ≥2 subtypes
    # of that supertype are addressed, treat the supertype as implicitly covered
    SUPERTYPES_OF = {
        'Italian': {'Sicilian', 'Tuscan', 'Roman', 'Venetian', 'Genovese',
                    'Neapolitan', 'Bolognese'},
        'Mediterranean': {'Sicilian', 'Greek', 'Spanish', 'Italian', 'Tunisian',
                          'Moroccan', 'Turkish', 'Lebanese', 'Syrian'},
        'Chinese': {'Cantonese', 'Sichuan', 'Hunan', 'Hakka'},
        'Indian': {'Mughlai', 'Goan', 'Punjabi'},
        'Mexican': {'Oaxacan', 'Yucatecan', 'Pueblan'},
        'French': {'Lyonnaise', 'Provençal', 'Alsatian'},
        'Spanish': {'Catalan', 'Basque', 'Andalusian'},
    }
    addressed = stem_cuisines - set(missing)
    real_missing = []
    for m in missing:
        subtypes = SUPERTYPES_OF.get(m, set())
        if subtypes and len(subtypes & addressed) >= 2:
            continue  # subtypes covered, treat supertype as covered
        real_missing.append(m)
    if not real_missing:
        return None
    # Tolerance: if ≥3 cuisines addressed and ≤1 missing, ignore as noisy
    if len(addressed) >= 3 and len(real_missing) <= 1:
        return None
    return f'comparative_completeness: stem compares {sorted(stem_cuisines)} but answer addresses only {sorted(addressed)} — missing {sorted(real_missing)}'


# --------------------------------------------------------------------------
# Gate: list_comma_lint
# --------------------------------------------------------------------------

# Detect missing serial commas in 3-item participial lists.
# Conservative: only fires on -ed/-ed/-ed or -ing/-ing/-ing chains where
# the first word is NOT a common preposition (during, including) or a common
# main verb (weighed, served, sold).
_ED_LIST = re.compile(r'\b([a-z]{3,}ed) ([a-z]{3,}ed) and ([a-z]{3,}ed)\b')
_ING_LIST = re.compile(r'\b([a-z]{3,}ing) ([a-z]{3,}ing) and ([a-z]{3,}ing)\b')

# Words that look participial but typically introduce a 2-item list, not lead it
_LIST_LEAD_EXCLUDED = {
    # -ing words that are prepositions/conjunctions, not list items
    'during', 'including', 'regarding', 'considering', 'concerning',
    'depending', 'following', 'owing', 'viewing', 'pending', 'excluding',
    'preceding', 'surrounding',
    # -ing nouns (time-of-day, etc.) that don't start participial lists
    'morning', 'evening', 'wedding', 'meeting', 'building', 'opening',
    'ending', 'beginning', 'spring',
    # -ed words that are commonly main verbs introducing a 2-item subject phrase
    'weighed', 'served', 'sold', 'found', 'bought', 'made', 'used',
    'called', 'watched', 'wanted', 'needed', 'asked', 'tried',
    'compared', 'tested', 'measured',
}


def gate_list_comma_lint(q: dict) -> Optional[str]:
    """Flag missing serial commas in 3-item participial lists."""
    fields = [('stem', q.get('question', ''))] + \
             [('choice', c) for c in q.get('choices', [])] + \
             [('context', q.get('context', ''))]
    for label, text in fields:
        for pattern in (_ED_LIST, _ING_LIST):
            m = pattern.search(text)
            if m and m.group(1).lower() not in _LIST_LEAD_EXCLUDED:
                return f'list_comma_lint: possible missing serial commas in "{m.group(0)}" ({label})'
    return None


# --------------------------------------------------------------------------
# Gate: duplicate
# --------------------------------------------------------------------------


def make_duplicate_gate():
    seen = set()
    def gate_duplicate(q: dict) -> Optional[str]:
        stem = q.get('question', '').strip().lower()
        fp = stem[:80]
        if fp in seen:
            return f'duplicate: stem matches earlier question'
        seen.add(fp)
        return None
    return gate_duplicate


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

PER_QUESTION_GATES: list[tuple[str, Callable[[dict], Optional[str]]]] = [
    ('schema', gate_schema),
    ('length_budget', gate_length_budget),
    ('length_parity', gate_length_parity),
    ('choice_shape_parity', gate_choice_shape_parity),
    ('anti_pattern_clear', gate_anti_pattern_clear),
    ('no_toddler_recall', gate_no_toddler_recall),
    ('forcing_constraint', gate_forcing_constraint),
    ('wonder_bias_check', gate_wonder_bias_check),
    ('context_no_meta_references', gate_context_no_meta_references),
    ('subject_named', gate_subject_named),
    ('stem_answer_overlap', gate_stem_answer_overlap),
    ('comparative_completeness', gate_comparative_completeness),
    ('list_comma_lint', gate_list_comma_lint),
]


def run_gates(q: dict) -> dict[str, Optional[str]]:
    return {name: fn(q) for name, fn in PER_QUESTION_GATES}


def run_bank(qs: list[dict]) -> dict:
    per_gate_fail = {name: 0 for name, _ in PER_QUESTION_GATES}
    fail_examples = {name: [] for name, _ in PER_QUESTION_GATES}
    fail_count = 0
    dup_gate = make_duplicate_gate()
    for q in qs:
        results = run_gates(q)
        dup_result = dup_gate(q)
        if dup_result:
            results['duplicate'] = dup_result
        failed = [(n, r) for n, r in results.items() if r is not None]
        if failed:
            fail_count += 1
        for name, reason in failed:
            if name not in per_gate_fail:
                per_gate_fail[name] = 0
                fail_examples[name] = []
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
        'per_gate': per_gate_fail,
        'examples': fail_examples,
    }


def _load_exemplars() -> list[dict]:
    here = Path(__file__).parent
    path = here / '_cooking_exemplars.py'
    if not path.exists():
        return []
    ns: dict = {}
    exec(path.read_text(encoding='utf-8'), ns)
    out = []
    for ex in ns.get('exemplars', []):
        out.append({
            'tier': ex['tier'],
            'question': ex['question'],
            'choices': ex['choices'],
            'answer': ex['choices'][ex['answer_idx']],
            'context': ex['context'],
        })
    return out


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else None
    ex_qs = _load_exemplars()
    if ex_qs:
        result = run_bank(ex_qs)
        print(f'== exemplars cross-check ({len(ex_qs)} questions) ==')
        print(f'  pass-all: {len(ex_qs) - result["fail_any"]} ({100*(len(ex_qs)-result["fail_any"])/len(ex_qs):.1f}%)')
        for name, count in sorted(result['per_gate'].items(), key=lambda kv: -kv[1]):
            if count > 0:
                print(f'  {name:30s} {count} fails')
                for ex in result['examples'].get(name, [])[:2]:
                    print(f'    T{ex["tier"]}: {ex["stem"]}')
                    print(f'      -> {ex["reason"]}')
        print()
    if target:
        with open(target, encoding='utf-8') as f:
            data = json.load(f)
        qs = data if isinstance(data, list) else data.get('questions', [])
        result = run_bank(qs)
        print(f'== {target} ({len(qs)} questions) ==')
        print(f'  pass-all: {len(qs) - result["fail_any"]} ({100*(len(qs)-result["fail_any"])/max(len(qs),1):.1f}%)')
        for name, count in sorted(result['per_gate'].items(), key=lambda kv: -kv[1]):
            if count > 0:
                print(f'  {name:30s} {count}')


if __name__ == '__main__':
    main()
