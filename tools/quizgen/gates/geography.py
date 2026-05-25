"""Geography bank structural gates.

Imports subject-agnostic gates from cooking_structural_gates (which itself
imports choice_shape_parity, context_no_meta_references, and _content_tokens
from philosophy_structural_gates). Adds geography-specific:
  - geography TODDLER_BANNED_ANSWERS (capitals, Everest, Nile, Russia, etc.)
  - geography BANNED_STEM_PATTERNS (climate-policy verdicts, capital recall, etc.)
  - geography WONDER vocab (geographic features, civilizations, exploration)
  - geography gate_subject_named (geography-specific identify-style tokens)
  - NEW: no_capital_recall (hard-reject: "What is the capital of X" stems)
  - NEW: no_climate_policy_verdict (hard-reject: climate-policy verdict stems)
  - NEW: place_anchor_check (soft-warn: place name without geographic anchor)
  - NEW: no_theory_stacking_check (soft-warn: 2+ theory tokens without concrete anchor)
  - NEW: wonder_in_stem_check (soft-warn: rote-proportion stem may have wonder deferred to context)
  - NEW: register_consistency (closes geography gap per SHARED_PRINCIPLES §3)

Per docs/quiz/moral_vision.md (SUPREME), SHARED_PRINCIPLES.md, GEOGRAPHY_FRAMEWORK.md,
GEOGRAPHY_TEMPLATES.md, and feedback_lift_discovered_rules.md.

Soft-warn gates return strings prefixed with 'soft-warn:'. They flag candidates
for human review without hard-rejecting (recognition-type questions and legitimate
stylistic choices may trigger them).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Callable, Optional

# Subject-agnostic gates imported from cooking (which imports from philosophy).
# NOTE: gate_length_budget is NOT imported — geography overrides it locally to
# remove the context cap (context is teaching content shown AFTER the answer;
# capping it forces shallow depth — see user directive 2026-05-23).
from tools.quizgen.gates.cooking import (
    gate_schema,
    gate_length_parity,
    gate_forcing_constraint,
    gate_stem_answer_overlap,
    gate_comparative_completeness,
    gate_list_comma_lint,
    make_duplicate_gate,
)
from tools.quizgen.gates.philosophy import (
    gate_choice_shape_parity,
    gate_context_no_meta_references,
    _content_tokens,
)


# Total-char budget per tier (stem + 4 choices). Context is uncapped.
# Recalibrated 2026-05-23: aligned with the canonical length_budget.py geography
# override AND with exemplar density (user-approved). Old per-field caps (200/90,
# 240/110, etc.) are dropped in favor of total budget — total is what governs
# reading time during play, which is the actual playability gate.
# See SHARED_PRINCIPLES.md §10 and tools/quizgen/llm_jobs/validate_gameplay.md.
TOTAL_BUDGET = {1: 500, 2: 620, 3: 770, 4: 900, 5: 1000}
BUDGET_GRACE = 1.05  # +5% per validate_gameplay.md §"Primary gate"

# Per-field caps retained as legacy/advisory for exemplar self-validation.
# Not enforced by the gate; total budget is authoritative.
TIER_CAPS = {1: (200, 90, 200), 2: (240, 110, 240),
             3: (280, 130, 300), 4: (320, 160, 360),
             5: (360, 180, 420)}


# --------------------------------------------------------------------------
# Gate: length_budget (geography — TOTAL char budget, canonical)
# --------------------------------------------------------------------------


def gate_length_budget(q: dict) -> Optional[str]:
    """Total chars (stem + 4 choices) must fit per-tier budget. Context uncapped.

    Recalibrated 2026-05-23: budgets {500, 620, 770, 900, 1000} match exemplar
    density (which the user reviewed and approved). Old per-field caps weren't
    aligned with canonical length_budget.py — this is now consistent. Per-field
    caps would have allowed up to 2x the canonical total in some tiers, masking
    real playability issues.

    Rationale: total reading time governs playability; per-field is supplementary.
    See SHARED_PRINCIPLES.md §10 and validate_gameplay.md.
    """
    tier = q.get('tier', 3)
    budget = TOTAL_BUDGET[tier]
    hard_cap = int(budget * BUDGET_GRACE)
    total = len(q.get('question', '')) + sum(len(c) for c in q.get('choices', []))
    if total > hard_cap:
        return f'length_budget: T{tier} total {total} > hard_cap {hard_cap} (budget {budget} + 5% grace)'
    return None


# --------------------------------------------------------------------------
# Gate: no_toddler_recall (geography-specific)
# --------------------------------------------------------------------------

TODDLER_BANNED_ANSWERS = {
    # Capital-name recall (per moral_vision.md and GEOGRAPHY_FRAMEWORK §forbids)
    'paris', 'london', 'tokyo', 'beijing', 'washington', 'washington dc',
    'washington d.c.', 'moscow', 'rome', 'berlin', 'madrid', 'cairo',
    'athens', 'delhi', 'new delhi', 'brasilia', 'canberra', 'ottawa',
    'wellington', 'mexico city', 'buenos aires', 'lima', 'bogota',
    'santiago', 'caracas', 'havana', 'kingston', 'reykjavik', 'oslo',
    'stockholm', 'helsinki', 'copenhagen', 'amsterdam', 'brussels',
    'vienna', 'prague', 'warsaw', 'budapest', 'bucharest', 'sofia',
    'ankara', 'tehran', 'baghdad', 'riyadh', 'jerusalem', 'damascus',
    'beirut', 'amman', 'islamabad', 'kabul', 'dhaka', 'colombo',
    'jakarta', 'bangkok', 'hanoi', 'manila', 'seoul', 'pyongyang',
    'taipei', 'singapore', 'kuala lumpur', 'nairobi', 'addis ababa',
    'lagos', 'abuja', 'kinshasa', 'pretoria', 'cape town', 'rabat',
    'tunis', 'algiers', 'tripoli', 'khartoum',
    # Toddler-trivial superlative answers
    'mount everest', 'everest', 'mt everest', 'nile', 'amazon',
    'russia', 'china', 'india', 'pacific ocean', 'pacific',
    'asia', 'sahara', 'antarctica', 'atlantic', 'atlantic ocean',
    'mississippi', 'mississippi river', 'andes',
}

GEOGRAPHY_TODDLER_STEMS = [
    # Capital-recall (also caught by no_capital_recall; defense in depth)
    r"^\s*what is the capital of\b",
    r"^\s*which (city|town) is the capital of\b",
    # Basic continent identification
    r"^\s*which continent is \w+ on\?",
    r"^\s*on which continent is\b",
    # Basic counting
    r"^\s*how many (oceans|continents) (are there|exist)",
    # Toddler superlatives
    r"^\s*what is the (tallest|highest) mountain\?",
    r"^\s*what is the (longest|biggest) river\?",
    r"^\s*what is the (biggest|largest) country\?",
    r"^\s*what is the most populous (country|nation)\?",
    r"^\s*what is the (largest|biggest) ocean\?",
    r"^\s*what is the (biggest|largest) continent\?",
    r"^\s*what is the (biggest|largest) desert\?",
    r"^\s*what is the coldest continent\?",
    # Pure date recall
    r"\bin what year did .{1,40}(reach|discover|explore|chart|map)\b",
    r"\bwhat year did .{1,40}(reach|discover|explore|chart|map)\b",
    # Pure explorer-name recall
    r"^\s*who (discovered|charted|mapped|first reached) \b",
    # Definition lookup
    r"^\s*what does ['\"]?(latitude|longitude|altitude|biome|ecosystem|tectonic|GPS)['\"]?\s+mean\b",
    # Kindergarten phrasings
    r"\bjust spot it\b",
    r"\bwhich one is it\b",
]
_GEOGRAPHY_TODDLER_STEM_RE = re.compile('|'.join(GEOGRAPHY_TODDLER_STEMS), re.IGNORECASE)


def gate_no_toddler_recall(q: dict) -> Optional[str]:
    stem = q.get('question', '')
    answer = q.get('answer', '').strip().lower()
    m = _GEOGRAPHY_TODDLER_STEM_RE.search(stem)
    if m:
        return f'no_toddler_recall: stem matches banned phrasing "{m.group(0).strip()}"'
    # Strip leading articles/punctuation; lower
    stripped = re.sub(r'^(a |an |the )', '', answer).strip(' .,"\'')
    # Also strip after first em-dash so "Paris — capital of France" → "paris"
    if '—' in stripped:
        stripped = stripped.split('—')[0].strip()
    if '–' in stripped:
        stripped = stripped.split('–')[0].strip()
    if stripped in TODDLER_BANNED_ANSWERS:
        return f'no_toddler_recall: correct answer is toddler-banned "{stripped}"'
    return None


# --------------------------------------------------------------------------
# Gate: anti_pattern_clear (geography-specific)
# --------------------------------------------------------------------------

GEOGRAPHY_BANNED_STEM_PATTERNS = [
    # Climate-policy verdict (also caught by no_climate_policy_verdict; defense in depth)
    r"\bis climate change (real|happening|true|caused)\b",
    r"\bare humans (causing|responsible for) (climate change|global warming)\b",
    # Anti-anti-white framing (per FRAMEWORK §forbids #6)
    r"\bis (colonialism|imperialism|western civilization|whiteness) (evil|bad|inherently|morally wrong)\b",
    r"\bwas the (european|western) colonization of \w+ (genocide|inherently evil)\b",
    # Definition lookup
    r"\bwhat does ['\"]?(latitude|longitude|altitude|biome|ecosystem|tectonic|continental drift|GPS)['\"]?\s+mean",
    # Toddler trivia patterns
    r"\bwhat is the (tallest|highest) mountain\b(?! in)",
    r"\bwhat is the (longest|biggest) river\b(?! in)",
    r"\bwhat is the (biggest|largest) country\b(?! in)",
    r"\bwhat is the most populous (country|nation)\b(?! in)",
    # Kindergarten phrasings
    r"\bjust spot it\b",
    r"\bwhich one is it\b",
    # Pure year-of-discovery recall (geography-specific)
    r"\bin what year did (columbus|magellan|cook|lewis and clark|amundsen|shackleton) ",
]
_GEOGRAPHY_BANNED_RE = re.compile('|'.join(GEOGRAPHY_BANNED_STEM_PATTERNS), re.IGNORECASE)


def gate_anti_pattern_clear(q: dict) -> Optional[str]:
    stem = q.get('question', '')
    m = _GEOGRAPHY_BANNED_RE.search(stem)
    if m:
        return f'anti_pattern_clear: banned phrasing "{m.group(0)}"'
    return None


# --------------------------------------------------------------------------
# Gate: wonder_bias_check (geography-specific)
# --------------------------------------------------------------------------

_GEOGRAPHY_WONDER_WORDS = {
    # Geographic features
    'mountain', 'mountains', 'peak', 'peaks', 'summit', 'ridge', 'range',
    'volcano', 'volcanoes', 'volcanic', 'caldera', 'crater', 'hotspot',
    'plateau', 'plain', 'plains', 'valley', 'valleys', 'canyon', 'gorge',
    'river', 'rivers', 'tributary', 'delta', 'estuary', 'waterfall',
    'lake', 'lakes', 'sea', 'seas', 'ocean', 'oceans', 'gulf', 'bay',
    'strait', 'straits', 'channel', 'sound', 'fjord', 'fjords',
    'island', 'islands', 'archipelago', 'peninsula', 'isthmus', 'cape',
    'desert', 'deserts', 'oasis', 'dune', 'dunes', 'savanna', 'tundra',
    'taiga', 'steppe', 'jungle', 'rainforest', 'forest', 'forests',
    'glacier', 'glaciers', 'iceberg', 'permafrost', 'tropics', 'arctic',
    'antarctic', 'equator', 'tropic',
    # Tectonics / geology
    'plate', 'plates', 'tectonic', 'subduction', 'rift', 'mantle',
    'magma', 'lava', 'erupt', 'erupts', 'erupted', 'erupting', 'eruption',
    'earthquake', 'earthquakes', 'fault', 'faults', 'seismic',
    'sandstone', 'limestone', 'granite', 'basalt', 'tepui', 'karst',
    'plume', 'sediment', 'loess', 'silt',
    # Atmosphere / climate / sky
    'climate', 'weather', 'monsoon', 'monsoons', 'hurricane', 'typhoon',
    'cyclone', 'tornado', 'storm', 'storms', 'wind', 'winds', 'jet',
    'hadley', 'cell', 'cells', 'pressure', 'humidity', 'precipitation',
    'rainfall', 'snowfall', 'temperature', 'celsius', 'fahrenheit',
    'milankovitch', 'paleoclimate', 'glacial', 'interglacial',
    'thermohaline', 'circulation', 'current', 'currents', 'gulf stream',
    'cloud', 'clouds', 'cumulus', 'cumulonimbus', 'stratus', 'cirrus',
    'thunderstorm', 'thunder', 'lightning', 'thunderhead', 'anvil',
    'snow', 'snowstorm', 'snowflake', 'snowflakes', 'snowfield', 'snowy',
    'hail', 'hailstone', 'hailstones', 'sleet', 'rain', 'drizzle', 'mist',
    'fog', 'foggy', 'haze', 'hazy', 'frost', 'ice', 'icicle', 'icicles',
    'sunburn', 'sunlight', 'sunrise', 'sunset', 'shadow', 'shadows',
    'halo', 'halos', 'aurora', 'auroras', 'rainbow', 'rainbows',
    'sundog', 'sundogs', 'glory', 'glow', 'glowing', 'flame', 'flames',
    'ozone', 'stratosphere', 'troposphere', 'mesosphere', 'ionosphere',
    'atmosphere', 'atmospheric', 'altitude', 'elevation', 'sky', 'skies',
    'arctic', 'antarctic', 'polar', 'tropical', 'temperate', 'equatorial',
    'season', 'seasons', 'seasonal', 'summer', 'winter', 'spring', 'autumn',
    'frozen', 'freezing', 'thaw', 'thawing', 'melt', 'melting', 'melted',
    'borehole', 'core', 'cores', 'icecore', 'isotope', 'isotopes',
    'el nino', 'la nina', 'jet stream', 'foehn', 'katabatic', 'chinook',
    # Cultural / civilizational anchors (people/peoples, traditions)
    'tribe', 'tribes', 'tribal', 'nation', 'nations', 'people', 'peoples',
    'confederacy', 'confederation', 'league', 'council', 'councils',
    'indigenous', 'native', 'aboriginal', 'longhouse', 'longhouses',
    'iroquois', 'haudenosaunee', 'mohawk', 'oneida', 'onondaga',
    'cayuga', 'seneca', 'tuscarora', 'cherokee', 'navajo', 'sioux',
    'apache', 'aztec', 'maya', 'inca', 'mongol', 'mongols', 'turk', 'turks',
    'mali', 'songhai', 'ottoman', 'persian', 'arab', 'arabs', 'arabic',
    'sami', 'inuit', 'bedouin', 'tuareg', 'maasai', 'zulu', 'bantu',
    'polynesian', 'maori', 'aborigine', 'aboriginal', 'baka', 'san',
    'wayfinding', 'navigation', 'tradition', 'traditions', 'traditional',
    'heritage', 'culture', 'cultural', 'cultures', 'civilization',
    'civilizations', 'civilizational', 'kingdom', 'kingdoms', 'empire',
    'empires', 'imperial', 'dynasty', 'dynasties', 'medieval', 'modern',
    # Wonder-evoking sensory / observation
    'huge', 'tiny', 'vast', 'massive', 'enormous', 'gigantic',
    'mysterious', 'unique', 'rare', 'common', 'sudden', 'suddenly',
    'glowing', 'flashing', 'sparkling', 'shimmering', 'shining',
    'painted', 'paintings', 'carved', 'carvings', 'engraving',
    'discovery', 'discovered', 'discoveries', 'breakthrough',
    'exploration', 'expedition', 'expeditions', 'explorer', 'explorers',
    # Water systems
    'watershed', 'divide', 'basin', 'aquifer', 'qanat', 'aqueduct',
    'irrigation', 'dam', 'reservoir', 'flood', 'flooding', 'drought',
    'salinity', 'freshwater', 'brackish', 'saltwater',
    # Biomes / wonder
    'endemic', 'endemism', 'biodiversity', 'ecosystem', 'biome',
    'evolution', 'evolved', 'isolation', 'isolated', 'species',
    # Civilizations / cultural anchors
    'roman', 'romans', 'greek', 'greeks', 'persian', 'persians',
    'egyptian', 'egyptians', 'mesopotamian', 'sumerian', 'akkadian',
    'byzantine', 'ottoman', 'crusader', 'crusades', 'viking', 'vikings',
    'norse', 'inca', 'incas', 'maya', 'mayan', 'aztec', 'aztecs',
    'mongol', 'mongols', 'chinese', 'japanese', 'korean', 'indian',
    'mughal', 'mughals', 'khmer', 'mali', 'songhai', 'ethiopian',
    'ancient', 'medieval', 'renaissance', 'colonial', 'imperial',
    # Religious geographic anchors
    'christian', 'christianity', 'church', 'cathedral', 'basilica',
    'monastery', 'monasteries', 'monastic', 'monk', 'monks',
    'jerusalem', 'holy land', 'mecca', 'medina', 'rome', 'constantinople',
    'pilgrimage', 'pilgrim', 'pilgrims', 'crusade',
    'mosque', 'temple', 'synagogue', 'pagoda',
    'islam', 'islamic', 'muslim', 'jewish', 'judaism', 'hindu',
    'hinduism', 'buddhist', 'buddhism',
    # Exploration / cartography
    'voyage', 'voyages', 'expedition', 'explorer', 'navigator',
    'cartography', 'cartographer', 'map', 'maps', 'mapping', 'chart',
    'charts', 'longitude', 'latitude', 'compass', 'sextant', 'chronometer',
    'astrolabe', 'meridian', 'GPS', 'satellite', 'satellites',
    'circumnavigation', 'circumnavigate',
    'eratosthenes', 'columbus', 'magellan', 'cook', 'lewis', 'clark',
    'amundsen', 'shackleton', 'cabot', 'da gama', 'drake', 'vespucci',
    # Adaptation
    'igloo', 'sod', 'tent', 'yurt', 'kibbutz', 'terraces', 'terrace',
    'terracing', 'chinampas', 'mound', 'mounds',
    'inuit', 'bedouin', 'tuareg', 'maasai', 'sami', 'polynesian',
    'navigator', 'navigation', 'wayfinding',
    # American achievement geography
    'american', 'louisiana', 'erie', 'transcontinental', 'panama',
    'apollo', 'hoover', 'tva', 'manhattan', 'mississippi',
    # Communist-regime geography
    'kolyma', 'gulag', 'aral', 'soviet', 'collectivization', 'famine',
    'iron curtain', 'berlin wall', 'siberia',
    # Comparative / wonder framing
    'only', 'unique', 'uniquely', 'unlike', 'differs', 'differ',
    'difference', 'compared', 'comparison', 'distinct', 'distinctive',
    'surprising', 'bizarre', 'strange', 'remarkable', 'extraordinary',
    'unusual', 'striking', 'why', 'because', 'reason', 'mechanism',
    'discover', 'discovery', 'wonder', 'wondrous',
    # Superlatives (geographic facts often use these)
    'largest', 'biggest', 'smallest', 'oldest', 'youngest', 'deepest',
    'shallowest', 'highest', 'tallest', 'longest', 'shortest', 'widest',
    'narrowest', 'fastest', 'slowest', 'driest', 'wettest', 'hottest',
    'coldest', 'most', 'first', 'last', 'world', 'worlds', 'earth',
    'earths', 'planet', 'planets',
    # Geological / mineral / resource vocab
    'salt', 'mirror', 'metal', 'metals', 'mineral', 'minerals', 'ore',
    'gold', 'silver', 'copper', 'iron', 'lithium', 'platinum', 'gem',
    'gems', 'diamond', 'diamonds', 'crystal', 'crystals',
    'valuable', 'precious', 'rare', 'abundant', 'reserves',
    'rock', 'rocks', 'stone', 'stones', 'soil', 'soils', 'sand', 'sands',
    # Numbers (geographic facts often have them)
    'thousand', 'thousands', 'million', 'millions', 'billion',
    'percent', 'fraction', 'half', 'third', 'quarter',
    # Movement / change verbs
    'flow', 'flows', 'flowed', 'flowing', 'drain', 'drains', 'drained',
    'rise', 'rises', 'rose', 'rising', 'risen', 'sink', 'sinks',
    'collide', 'collides', 'spread', 'spreads', 'spreading',
    'becomes', 'become', 'became', 'becoming',
}


def gate_wonder_bias_check(q: dict) -> Optional[str]:
    stem = q.get('question', '')
    if re.search(r'\d', stem):
        return None  # Any digit signals factual anchoring
    stem_words = set(re.findall(r"[A-Za-z][A-Za-z'-]+", stem.lower()))
    if stem_words & _GEOGRAPHY_WONDER_WORDS:
        return None
    return 'wonder_bias_check: stem lacks wonder signal (no geographic vocab, number, or comparative framing)'


# --------------------------------------------------------------------------
# Gate: subject_named (geography-specific)
# --------------------------------------------------------------------------


def gate_subject_named(q: dict) -> Optional[str]:
    """Non-D patterns should NAME the subject of analysis in the stem.

    Geography-specific identify tokens: feature, place, region, range, mountain,
    river, lake, ocean, term, system, phenomenon, process.

    Permissive: only fires on stems ending in "what is this?" / "what is the X?"
    that aren't followed by an answer that defines a named term inline.
    """
    stem = q.get('question', '').strip()
    identify_re = re.compile(
        r"(what is it|which (is this|is it)|"
        r"identify the (feature|place|region|range|term|system|phenomenon|process|mountain|river|lake)|"
        r"what is the (feature|place|region|range|term|system|phenomenon|process|mountain|river|lake))\??\s*$",
        re.IGNORECASE,
    )
    if not identify_re.search(stem):
        return None
    # Allow if answer leads with named term + em-dash (inline-teaching shape)
    answer = q.get('answer', '')
    if re.match(r"^(A |An |The )?[A-Za-z][a-zA-Zà-ÿ'-]{2,}\s*[—–-]", answer):
        return None
    # Allow if all 4 choices have dash structure (parallel name-defining)
    choices = q.get('choices', [])
    if choices and all('—' in c or '–' in c for c in choices):
        return None
    return 'subject_named: non-identify question asks "what is it?" without naming the subject of analysis'


# --------------------------------------------------------------------------
# NEW Gate: no_capital_recall (hard-reject)
# --------------------------------------------------------------------------

CAPITAL_RECALL_PATTERNS = [
    r"^\s*what is the capital of\s+",
    r"^\s*which (city|town) is the capital of\s+",
    r"^\s*what city is the capital of\s+",
    r"^\s*name the capital of\s+",
]
_CAPITAL_RECALL_RE = re.compile('|'.join(CAPITAL_RECALL_PATTERNS), re.IGNORECASE)


def gate_no_capital_recall(q: dict) -> Optional[str]:
    """Per moral_vision.md and GEOGRAPHY_FRAMEWORK §forbids #1: capital-name
    recall is BANNED full stop. Capital names live in context, never as the test.
    """
    stem = q.get('question', '')
    if _CAPITAL_RECALL_RE.search(stem):
        return f'no_capital_recall: stem uses banned "capital of" recall pattern'
    return None


# --------------------------------------------------------------------------
# NEW Gate: no_climate_policy_verdict (hard-reject)
# --------------------------------------------------------------------------

CLIMATE_POLICY_PATTERNS = [
    r"\bis climate change (real|happening|true|caused by|man-made|man made)\b",
    r"\bare humans (causing|responsible for) (climate change|global warming)\b",
    r"\bshould (we|the (world|us|government|un)) (adopt|impose|enact|sign|implement)\s+",
    r"\bwhy (should|must) (we|the world|the us|the government) (reduce|cut|limit|ban|tax)\s+(carbon|co2|emissions|fossil)\b",
    r"\bis (the )?paris (agreement|accord|climate accord) (good|necessary|effective)\b",
    r"\bshould (oil|gas|coal|fossil fuel) (companies|industry) (be banned|be taxed|pay reparations)\b",
]
_CLIMATE_POLICY_RE = re.compile('|'.join(CLIMATE_POLICY_PATTERNS), re.IGNORECASE)


def gate_no_climate_policy_verdict(q: dict) -> Optional[str]:
    """Per GEOGRAPHY_FRAMEWORK §forbids #7: climate-change-as-policy only as
    T5 recognize-the-move (Pattern J), never as a yes/no verdict question.
    """
    stem = q.get('question', '')
    m = _CLIMATE_POLICY_RE.search(stem)
    if m:
        return f'no_climate_policy_verdict: stem matches climate-policy verdict pattern "{m.group(0)}"'
    return None


# --------------------------------------------------------------------------
# NEW Gate: place_anchor_check (soft-warn)
# --------------------------------------------------------------------------

# Specific-place patterns that often appear without geographic anchor.
# Conservative: matches K-style abbreviations, Mt./Lake/River name patterns.
SPECIFIC_PLACE_RE = re.compile(
    r'\b('
    r'K\d|K-\d|'                          # K2, K-2
    r'Mt\.?\s+[A-Z][a-zA-Z]+|'            # Mt Everest, Mt. Roraima
    r'Mount\s+[A-Z][a-zA-Z]+|'            # Mount Olympus
    r'Lake\s+[A-Z][a-zA-Z]+|'             # Lake Baikal
    r'River\s+[A-Z][a-zA-Z]+|'            # River Thames
    r'[A-Z][a-z]+\s+(?:River|Mountains?|Range|Desert|Sea|Ocean|Strait|Plateau|Bay|Gulf)'
    r')\b'
)

# Geographic anchor tokens (substring match, case-insensitive).
# Any of these appearing in a stem grounds it geographically.
GEOGRAPHIC_ANCHOR_TOKENS = {
    # Continents
    'africa', 'asia', 'europe', 'antarctica', 'australia', 'oceania',
    'north america', 'south america',
    # Major countries (sampling — covers most-cited)
    'united states', 'usa', 'canada', 'mexico', 'brazil', 'argentina',
    'chile', 'peru', 'bolivia', 'colombia', 'venezuela', 'cuba',
    'uk', 'britain', 'england', 'scotland', 'wales', 'ireland', 'france',
    'germany', 'spain', 'italy', 'portugal', 'netherlands', 'belgium',
    'switzerland', 'austria', 'poland', 'czech', 'hungary', 'romania',
    'russia', 'ukraine', 'belarus', 'greece', 'turkey', 'cyprus',
    'egypt', 'morocco', 'algeria', 'tunisia', 'libya', 'sudan',
    'ethiopia', 'kenya', 'tanzania', 'uganda', 'somalia', 'nigeria',
    'ghana', 'mali', 'senegal', 'south africa', 'zimbabwe', 'angola',
    'china', 'india', 'japan', 'korea', 'taiwan', 'vietnam', 'thailand',
    'indonesia', 'philippines', 'malaysia', 'singapore', 'burma',
    'myanmar', 'cambodia', 'laos', 'bangladesh', 'sri lanka', 'nepal',
    'tibet', 'mongolia', 'kazakhstan', 'uzbekistan', 'turkmenistan',
    'tajikistan', 'kyrgyzstan', 'afghanistan',
    'pakistan', 'iran', 'iraq', 'syria', 'lebanon', 'jordan', 'israel',
    'palestine', 'saudi arabia', 'yemen', 'oman', 'uae', 'kuwait',
    'qatar', 'bahrain',
    'norway', 'sweden', 'denmark', 'finland', 'iceland', 'greenland',
    'new zealand', 'madagascar', 'fiji', 'samoa',
    # Oceans, seas, gulfs
    'pacific', 'atlantic', 'indian ocean', 'arctic ocean', 'southern ocean',
    'mediterranean', 'caribbean', 'baltic', 'aegean', 'adriatic',
    'caspian', 'black sea', 'red sea', 'persian gulf', 'gulf of mexico',
    'north sea', 'bering', 'sea of japan', 'arabian sea',
    # Deserts
    'sahara', 'gobi', 'kalahari', 'atacama', 'mojave', 'karakum',
    'namib', 'arabian desert', 'thar',
    # Mountain ranges
    'andes', 'rockies', 'rocky mountains', 'alps', 'himalaya', 'himalayas',
    'karakoram', 'pyrenees', 'urals', 'caucasus', 'appalachian',
    'atlas mountains', 'pamir', 'tian shan', 'altai',
    # Major rivers
    'amazon', 'nile', 'mississippi', 'yangtze', 'yellow river', 'ganges',
    'danube', 'volga', 'mekong', 'columbia river', 'missouri river',
    'ohio river', 'rhine', 'rhone', 'thames', 'seine', 'tigris',
    'euphrates', 'indus', 'congo river', 'niger river', 'zambezi',
    # Major regions / features
    'great lakes', 'great plains', 'holy land', 'levant', 'patagonia',
    'siberia', 'altiplano', 'tibetan plateau', 'mongolian steppe',
    'iberian peninsula', 'arabian peninsula', 'horn of africa',
    'fertile crescent', 'mesopotamia',
    # Geographic context tokens
    'continent', 'country', 'countries', 'peninsula', 'archipelago',
    'hemisphere', 'coast', 'coastal', 'border', 'borders', 'frontier',
    'territory', 'range', 'mountains', 'mountain', 'valley', 'basin',
    'plateau', 'desert', 'tundra', 'savanna', 'rainforest',
}


def _has_geographic_anchor(stem: str) -> bool:
    stem_lower = stem.lower()
    return any(token in stem_lower for token in GEOGRAPHIC_ANCHOR_TOKENS)


def gate_place_anchor_check(q: dict) -> Optional[str]:
    """Soft-warn: when stem names a specific place (mountain, river, lake, etc.)
    but lacks a geographic anchor (continent/country/region/range), flag for review.

    Recognition-type questions where the place IS the answer are legitimately
    exempt — they'll still trigger this gate, but as soft-warn, human reviews.
    """
    stem = q.get('question', '')
    if SPECIFIC_PLACE_RE.search(stem) and not _has_geographic_anchor(stem):
        m = SPECIFIC_PLACE_RE.search(stem)
        return f'soft-warn: place_anchor_check: stem names "{m.group(0)}" without geographic anchor'
    return None


# --------------------------------------------------------------------------
# NEW Gate: no_theory_stacking_check (soft-warn)
# --------------------------------------------------------------------------

THEORY_TOKEN_RE = re.compile(
    r'\b(epistemic|epistemology|framing|thesis|doctrine|paradigm|ontology|'
    r'hermeneutic|hermeneutics|hypothesis|critique|metaphysical|'
    r'phenomenology|dialectic|teleological|deontological|consequentialist|'
    r'modernism|postmodernism|structuralism|poststructuralism|essentialism|'
    r'liberalism|conservatism|socialism|capitalism|marxism|nihilism|'
    r'pleistocene|holocene|paleoclimate|milankovitch)\b',
    re.IGNORECASE
)

CONCRETE_ANCHOR_RE = re.compile(
    r'(\b\d{4}\b|'                                            # specific year
    r'\b\d+\s+(?:years|million|billion|mya|kya)\b|'           # specific timespan
    r'\bin\s+(?:18|19|20)\d{2}\b|'                            # year in 18xx-20xx
    r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b|'                         # named figure (Capitalized First Last)
    r"'[^']{15,}'|"                                           # quoted statement 15+ chars
    r'"[^"]{15,}"|'                                           # double-quoted statement
    r'\b(said|argued|wrote|claimed|argues|writes)\b)'         # speech verb
)


def gate_no_theory_stacking_check(q: dict) -> Optional[str]:
    """Soft-warn: stem contains 2+ theory-laden tokens without concrete-scenario
    anchor (named person, specific event, quoted argument).

    Pattern J questions must demonstrate the analytical move concretely, not as
    abstract framing-vs-framing.
    """
    stem = q.get('question', '')
    theory_matches = THEORY_TOKEN_RE.findall(stem)
    if len(theory_matches) >= 2 and not CONCRETE_ANCHOR_RE.search(stem):
        return f'soft-warn: no_theory_stacking_check: stem has {len(theory_matches)} theory tokens {sorted(set(theory_matches))} without concrete anchor'
    return None


# --------------------------------------------------------------------------
# NEW Gate: wonder_in_stem_check (soft-warn)
# --------------------------------------------------------------------------

ROTE_PROPORTION_RE = re.compile(
    r'\b(what\s+fraction|about\s+what\s+(?:percent|percentage|fraction)|'
    r'roughly\s+how\s+(?:many|much|big|large|long|tall|deep|high)|'
    r'approximately\s+what\s+(?:percent|fraction|number|size)|'
    r'what\s+percent(?:age)?\s+of)\b',
    re.IGNORECASE
)


def gate_wonder_in_stem_check(q: dict) -> Optional[str]:
    """Soft-warn: stem asks for a rote proportion/quantity that may indicate
    wonder is deferred to context (the Socotra failure pattern).

    Per SHARED_PRINCIPLES.md §8: wonder lives in the stem, not deferred to context.
    """
    stem = q.get('question', '')
    if ROTE_PROPORTION_RE.search(stem):
        return f'soft-warn: wonder_in_stem_check: stem asks rote proportion/quantity — verify wonder is in stem, not deferred to context'
    return None


# --------------------------------------------------------------------------
# NEW Gate: register_consistency (closes geography gap per SHARED_PRINCIPLES §3)
# --------------------------------------------------------------------------

# Specialist-word threshold: very long words (>=13 chars) tolerated above stem level.
# 13 is the cutoff so common words like "electronics" (11), "thermohaline" (12),
# "central-bank" (12) don't trigger; truly specialist terms like "circumnavigation"
# (16), "subduction" (10 — under threshold), "endemism" (8), "biogeography" (12)
# rarely fire false positives.
SPECIALIST_TOLERANCE_BY_TIER = {1: 2, 2: 3, 3: 4, 4: 5, 5: 7}


def _specialist_word_count(text: str) -> int:
    """Words of length >= 13 (proxy for specialist vocabulary)."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]+", text)
    return sum(1 for w in words if len(w) >= 13)


def gate_register_consistency(q: dict) -> Optional[str]:
    """Stem vocabulary tier ≈ choice vocabulary tier. No choice should introduce
    specialist vocabulary far beyond what the stem stayed at.

    Heuristic: count words of length >= 11 in stem vs each choice. If a choice
    exceeds stem count by more than tier-tolerance, flag.
    """
    tier = q.get('tier', 3)
    tolerance = SPECIALIST_TOLERANCE_BY_TIER[tier]
    stem_count = _specialist_word_count(q.get('question', ''))
    for i, c in enumerate(q.get('choices', [])):
        choice_count = _specialist_word_count(c)
        if choice_count > stem_count + tolerance:
            return f'register_consistency: choice[{i}] has {choice_count} specialist words vs stem {stem_count} (tier {tier} tolerance +{tolerance})'
    return None


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

# Soft-warn gates flag candidates for human review without hard-rejecting.
SOFT_WARN_GATES = {
    'place_anchor_check',
    'no_theory_stacking_check',
    'wonder_in_stem_check',
}

PER_QUESTION_GATES: list[tuple[str, Callable[[dict], Optional[str]]]] = [
    # Hard-reject gates
    ('schema', gate_schema),
    ('length_budget', gate_length_budget),
    ('length_parity', gate_length_parity),
    ('choice_shape_parity', gate_choice_shape_parity),
    ('anti_pattern_clear', gate_anti_pattern_clear),
    ('no_toddler_recall', gate_no_toddler_recall),
    ('no_capital_recall', gate_no_capital_recall),
    ('no_climate_policy_verdict', gate_no_climate_policy_verdict),
    ('forcing_constraint', gate_forcing_constraint),
    ('wonder_bias_check', gate_wonder_bias_check),
    ('context_no_meta_references', gate_context_no_meta_references),
    ('subject_named', gate_subject_named),
    ('stem_answer_overlap', gate_stem_answer_overlap),
    ('comparative_completeness', gate_comparative_completeness),
    ('list_comma_lint', gate_list_comma_lint),
    ('register_consistency', gate_register_consistency),
    # Soft-warn gates (return strings prefixed with 'soft-warn:')
    ('place_anchor_check', gate_place_anchor_check),
    ('no_theory_stacking_check', gate_no_theory_stacking_check),
    ('wonder_in_stem_check', gate_wonder_in_stem_check),
]


def run_gates(q: dict) -> dict[str, Optional[str]]:
    return {name: fn(q) for name, fn in PER_QUESTION_GATES}


def run_bank(qs: list[dict]) -> dict:
    per_gate_fail = {name: 0 for name, _ in PER_QUESTION_GATES}
    fail_examples = {name: [] for name, _ in PER_QUESTION_GATES}
    hard_fail_count = 0
    soft_warn_count = 0
    dup_gate = make_duplicate_gate()
    for q in qs:
        results = run_gates(q)
        dup_result = dup_gate(q)
        if dup_result:
            results['duplicate'] = dup_result
        hard_failed = [(n, r) for n, r in results.items()
                       if r is not None and n not in SOFT_WARN_GATES]
        soft_warned = [(n, r) for n, r in results.items()
                       if r is not None and n in SOFT_WARN_GATES]
        if hard_failed:
            hard_fail_count += 1
        if soft_warned:
            soft_warn_count += 1
        for name, reason in hard_failed + soft_warned:
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
        'hard_fail': hard_fail_count,
        'soft_warn': soft_warn_count,
        'per_gate': per_gate_fail,
        'examples': fail_examples,
    }


def _load_exemplars() -> list[dict]:
    here = Path(__file__).parent
    path = here / '_geography_exemplars.py'
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
        n = len(ex_qs)
        hard_pass = n - result['hard_fail']
        soft_clean = n - result['soft_warn']
        print(f'== exemplars cross-check ({n} questions) ==')
        print(f'  hard-reject pass: {hard_pass}/{n} ({100*hard_pass/n:.1f}%)')
        print(f'  soft-warn clean : {soft_clean}/{n} ({100*soft_clean/n:.1f}%)')
        print()
        for name, count in sorted(result['per_gate'].items(), key=lambda kv: -kv[1]):
            if count > 0:
                tag = '[SOFT-WARN]' if name in SOFT_WARN_GATES else '[HARD-FAIL]'
                print(f'  {tag} {name:30s} {count}')
                for ex in result['examples'].get(name, [])[:3]:
                    print(f'    T{ex["tier"]}: {ex["stem"]}')
                    print(f'      -> {ex["reason"]}')
                print()
    if target:
        with open(target, encoding='utf-8') as f:
            data = json.load(f)
        qs = data if isinstance(data, list) else data.get('questions', [])
        result = run_bank(qs)
        n = len(qs)
        hard_pass = n - result['hard_fail']
        print(f'== {target} ({n} questions) ==')
        print(f'  hard-reject pass: {hard_pass}/{n} ({100*hard_pass/max(n,1):.1f}%)')
        print(f'  soft-warn clean : {n - result["soft_warn"]}/{n} ({100*(n-result["soft_warn"])/max(n,1):.1f}%)')
        for name, count in sorted(result['per_gate'].items(), key=lambda kv: -kv[1]):
            if count > 0:
                tag = '[SOFT-WARN]' if name in SOFT_WARN_GATES else '[HARD-FAIL]'
                print(f'  {tag} {name:30s} {count}')


if __name__ == '__main__':
    main()
