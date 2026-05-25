"""Animal bank structural gates.

Reuses several gates from philosophy_structural_gates and adds animal-specific:
  - no_toddler_recall: stem doesn't ask for an answer in the toddler-banned list
  - wonder_bias_check: T1-T3 stems must include behavior verb, adaptation cue,
    specific number, or non-obvious feature
  - context_no_meta_references: reused from philosophy module unchanged

Skips philosophy gates that don't fit animal questions:
  - no_verdict_on_contested (philosophy-specific)
  - scenario_anchored_correct (fallacy-specific)
  - stem_pattern_match (philosophy-specific closers)
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
    EM_DASH,
    _has_dash,
    _content_tokens,
)


TIER_CAPS = {1: (200, 90, 200), 2: (240, 110, 240),
             3: (280, 130, 300), 4: (320, 160, 360),
             5: (360, 180, 420)}


# --------------------------------------------------------------------------
# Gate: length_budget
# --------------------------------------------------------------------------


def gate_length_budget(q: dict) -> Optional[str]:
    """Stem + per-choice budgets enforced; context is UNCAPPED.

    Per SHARED_PRINCIPLES.md §9: context is teaching content shown AFTER the
    answer, read at the player's pace — not under timer pressure. Capping it
    forces shallow educational depth, which fights moral_vision.md §"Beauty
    of mechanism" + §"Curiosity over completion". Context cap removed
    2026-05-24 per animal audit §2 (animal templates should also be updated
    to mark context uncapped). Mirrors geography 2026-05-23 + cooking same-day.
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
# Gate: no_toddler_recall
# --------------------------------------------------------------------------

# Toddler-banned answers — questions where the correct answer is one of these
# are not real philosophical/biological questions, they're toddler trivia.
TODDLER_BANNED_ANSWERS = {
    'zebra', 'zebras',
    'giraffe', 'giraffes',
    'lion', 'lions',
    'elephant', 'elephants',
    'kangaroo', 'kangaroos',
    'penguin', 'penguins',
    # Group names everyone knows
    'pack', 'a pack', 'pack of wolves',
    'herd', 'a herd', 'herd of cattle', 'herd of cows', 'herd of sheep',
    'school', 'a school', 'school of fish',
    'flock', 'a flock',
    'swarm', 'a swarm', 'swarm of bees',
    'colony', 'a colony', 'colony of ants',
    # Baby names everyone knows
    'calf', 'a calf',
    'kitten', 'a kitten',
    'puppy', 'a puppy',
    'foal', 'a foal',
    'lamb', 'a lamb',
    'kid', 'a kid',
    'chick', 'a chick',
    'duckling', 'a duckling',
    'gosling', 'a gosling',
    'piglet', 'a piglet',
}

# Toddler-banned stem patterns — phrasings that telegraph trivial fact-lookup
TODDLER_BANNED_STEMS = [
    r'\b(a\s+|the\s+)?(black-?and-?white\s+)?(striped\s+)?african horse',
    r'long[- ]necked african mammal',
    r'\bking of the jungle',
    r'\bpouched australian (hopper|mammal|animal)',
    r"\bbaby (cat|dog|cow|horse|sheep|chicken|duck|goose|pig|goat) is (called|named) (a |an )?",
    r"\bgroup of (cats|dogs|wolves|cows|sheep|horses|fish|birds|bees|ants) is (called|named) (a |an )?",
    r"what is (a |an )?(baby|young) (cat|dog|cow|horse|sheep|pig|goat) called",
    r"what is a group of (cats|dogs|wolves|cows|sheep|fish|bees|ants) called",
]
_TODDLER_STEM_RE = re.compile('|'.join(TODDLER_BANNED_STEMS), re.IGNORECASE)


def gate_no_toddler_recall(q: dict) -> Optional[str]:
    stem = q.get('question', '')
    answer = q.get('answer', '').strip().lower()
    # 1) Banned stem phrasings
    m = _TODDLER_STEM_RE.search(stem)
    if m:
        return f'no_toddler_recall: stem matches banned phrasing "{m.group(0)}"'
    # 2) Banned answer is the entire correct answer (or only with article)
    # Strip leading articles and punctuation, lowercase
    stripped = re.sub(r'^(a |an |the )', '', answer).strip(' .,"\'')
    if stripped in TODDLER_BANNED_ANSWERS:
        return f'no_toddler_recall: correct answer is toddler-banned "{stripped}"'
    return None


# --------------------------------------------------------------------------
# Gate: anti_pattern_clear (animal-specific)
# --------------------------------------------------------------------------

ANIMAL_BANNED_STEM_PATTERNS = [
    # Pure date recall (May-19 audit cleared these but enforce)
    r"in what year did .{1,40}go extinct",
    r"what year did .{1,40}(go extinct|first appear|become extinct)",
    # Latin-name-as-test
    r"what is the latin name for",
    r"what is the binomial (name )?for",
    # AKC kennel-club categorization
    r"\bAKC group\b",
    r"is classified in which (AKC|kennel club) group",
    # Definition lookup
    r"what does (the (term|word) )?['\"]?(biome|predator|prey|niche|habitat|species|genus|phylum|kingdom)['\"]? mean",
    # Pure name-lookup of famous animals
    r"^(Cher Ami|Sergeant Stubby|Mister Ed|Wojtek) was (the )?animal of",
    r"^(Cher Ami|Sergeant Stubby|Mister Ed|Wojtek) was famously",
    # Yes/no with obvious answer
    r"^do (bats|birds|fish) (fly|swim|breathe)\??$",
    # Animal-rights moralizing
    r"is it (wrong|cruel|unethical) to (eat meat|hunt|farm animals|wear (fur|leather))",
    # Kindergarten phrasings
    r"\bjust spot it\b",
    r"\bwhich one is it\b",
]
_ANIMAL_BANNED_RE = re.compile('|'.join(ANIMAL_BANNED_STEM_PATTERNS), re.IGNORECASE)


def gate_anti_pattern_clear(q: dict) -> Optional[str]:
    stem = q.get('question', '')
    m = _ANIMAL_BANNED_RE.search(stem)
    if m:
        return f'anti_pattern_clear: banned phrasing "{m.group(0)}"'
    return None


# --------------------------------------------------------------------------
# Gate: forcing_constraint (animal-adapted)
# --------------------------------------------------------------------------


def gate_forcing_constraint(q: dict) -> Optional[str]:
    """Stem must be substantive enough to single out one answer."""
    stem = q.get('question', '')
    tier = q.get('tier', 3)
    min_chars = {1: 50, 2: 70, 3: 90, 4: 110, 5: 130}[tier]
    if len(stem) < min_chars:
        return f'forcing_constraint: stem too short ({len(stem)} chars, need {min_chars})'
    # Must have enough content tokens to set up a real scenario
    toks = _content_tokens(stem)
    min_toks = {1: 6, 2: 8, 3: 10, 4: 12, 5: 14}[tier]
    if len(toks) < min_toks:
        return f'forcing_constraint: stem too sparse ({len(toks)} content tokens)'
    return None


# --------------------------------------------------------------------------
# Gate: wonder_bias_check
# --------------------------------------------------------------------------

# Wonder signals — broad word list. Any match passes the gate.
_WONDER_WORDS = {
    # Animal / biology nouns
    'animal', 'animals', 'mammal', 'mammals', 'bird', 'birds', 'fish', 'fishes',
    'reptile', 'reptiles', 'amphibian', 'amphibians', 'insect', 'insects',
    'spider', 'spiders', 'crab', 'crabs', 'worm', 'worms', 'snake', 'snakes',
    'dinosaur', 'dinosaurs', 'fossil', 'fossils', 'species', 'breed', 'breeds',
    'predator', 'predators', 'prey', 'herd', 'pack', 'flock', 'school', 'colony',
    # Behavior verbs (all forms)
    'hunt', 'hunts', 'hunted', 'hunting', 'kill', 'kills', 'killed', 'killing',
    'eat', 'eats', 'eaten', 'eating', 'ate', 'feed', 'feeds', 'fed', 'feeding',
    'food', 'diet', 'carnivore', 'herbivore', 'omnivore', 'scavenger',
    'migrate', 'migrates', 'migrated', 'migrating', 'migration',
    'navigate', 'navigates', 'navigated', 'navigation',
    'sleep', 'sleeps', 'slept', 'sleeping', 'hibernate', 'hibernates', 'hibernation',
    'see', 'saw', 'sees', 'seen', 'seeing', 'vision', 'eye', 'eyes', 'sight',
    'smell', 'smells', 'smelled', 'smelling', 'hear', 'heard', 'hearing',
    'sound', 'sounds', 'sense', 'senses', 'sensed', 'taste', 'tastes', 'tasted',
    'detect', 'detects', 'detected', 'detection',
    'signal', 'signals', 'signalled', 'display', 'displays', 'displayed',
    'mate', 'mates', 'mated', 'mating', 'court', 'courts', 'courted', 'courtship',
    'protect', 'protects', 'protected', 'defend', 'defends', 'defended', 'defense',
    'attack', 'attacks', 'attacked', 'attacking',
    'strike', 'strikes', 'struck', 'striking', 'bite', 'bites', 'bit', 'biting',
    'sting', 'stings', 'stung', 'stinging',
    'swarm', 'swarms', 'swarmed', 'nest', 'nests', 'nested', 'nesting',
    'burrow', 'burrows', 'burrowed', 'burrowing',
    'build', 'builds', 'built', 'building', 'spin', 'spins', 'spun', 'spinning',
    'web', 'webs', 'spray', 'sprays', 'sprayed', 'spraying',
    'inject', 'injects', 'injected', 'injecting', 'venom', 'venoms', 'venomous',
    'poison', 'poisons', 'poisonous', 'toxin', 'toxins', 'toxic',
    'shed', 'sheds', 'shedding', 'moult', 'moults', 'molted', 'molting',
    'hatch', 'hatches', 'hatched', 'hatching', 'egg', 'eggs',
    'crawl', 'crawls', 'crawled', 'crawling', 'climb', 'climbs', 'climbed', 'climbing',
    'swim', 'swims', 'swam', 'swimming', 'fly', 'flies', 'flew', 'flown', 'flying',
    'flight', 'jump', 'jumps', 'jumped', 'jumping', 'leap', 'leaps', 'leaped', 'leaping',
    'dive', 'dives', 'dived', 'dove', 'diving',
    'pump', 'pumps', 'pumped', 'pumping', 'heart', 'hearts', 'blood',
    'circulate', 'circulates', 'circulated', 'camouflage', 'camouflaged',
    'mimic', 'mimics', 'mimicked', 'mimicry',
    'glow', 'glows', 'glowed', 'glowing', 'bioluminesce', 'bioluminescent', 'bioluminescence',
    'echolocate', 'echolocates', 'echolocation',
    'warn', 'warns', 'warned', 'warning',
    'track', 'tracks', 'tracked', 'tracking', 'stalk', 'stalks', 'stalked', 'stalking',
    'punch', 'punches', 'punched', 'punching',
    'fight', 'fights', 'fought', 'fighting',
    'cooperate', 'cooperates', 'cooperated', 'cooperation',
    'farm', 'farms', 'farmed', 'farming', 'cultivate', 'cultivates', 'cultivated',
    # Adaptations / systems
    'adapt', 'adapts', 'adapted', 'adaptation', 'adaptations',
    'evolve', 'evolves', 'evolved', 'evolution', 'evolutionary',
    'survive', 'survives', 'survived', 'survival', 'specialized', 'specialization',
    'niche', 'ecosystem', 'ecosystems', 'habitat', 'habitats', 'biome', 'biomes',
    'community', 'population', 'populations',
    'pressure', 'selection', 'fitness', 'symbiosis', 'symbiotic',
    'mutualism', 'parasitism', 'parasite', 'parasites', 'commensalism',
    'host', 'hosts', 'trophic', 'cascade', 'keystone', 'exaptation',
    'silk', 'claw', 'claws', 'fang', 'fangs', 'beak', 'beaks', 'antenna', 'antennae',
    'fur', 'feather', 'feathers', 'scale', 'scales', 'shell', 'shells',
    'exoskeleton', 'wing', 'wings', 'fin', 'fins', 'tail', 'tails',
    'tongue', 'tongues', 'electroreception', 'magnetoreception',
    'metamorphosis', 'metamorphose', 'metamorphoses',
    # Cultural / historical anchors (T4-T5)
    'roosevelt', 'leopold', 'pittman', 'dingell', 'stewardship',
    'conservation', 'conservationist', 'domestication', 'domesticated',
    'darwin', 'wallace', 'mendel', 'aristotle', 'aquinas', 'pliny', 'linnaeus',
    # Comparative framing
    'only', 'unique', 'uniquely', 'unlike', 'differs', 'differ',
    'compared', 'comparison', 'distinct', 'distinctive',
    'surprising', 'bizarre', 'strange', 'remarkable', 'extraordinary',
    'unusual', 'striking',
    # Number words
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'dozen', 'dozens', 'hundred', 'hundreds', 'thousand', 'thousands',
    'million', 'millions', 'billion', 'billions', 'pair', 'pairs',
    # Generic action / movement / use verbs
    'use', 'uses', 'used', 'using', 'move', 'moves', 'moved', 'moving',
    'find', 'finds', 'found', 'finding', 'learn', 'learns', 'learned', 'learning',
    'show', 'shows', 'showed', 'shown', 'showing', 'know', 'knows', 'knew', 'known',
    'live', 'lives', 'lived', 'living', 'grow', 'grows', 'grew', 'grown', 'growing',
    'change', 'changes', 'changed', 'changing',
    # More animal common names (broad)
    'starling', 'starlings', 'sparrow', 'robin', 'finch', 'finches', 'jay', 'cardinal',
    'magpie', 'raven', 'ravens', 'crow', 'crows', 'owl', 'owls', 'hawk', 'hawks',
    'eagle', 'eagles', 'falcon', 'falcons', 'vulture', 'condor', 'parrot', 'parakeet',
    'hummingbird', 'hummingbirds', 'woodpecker', 'kingfisher', 'heron', 'egret',
    'crane', 'cranes', 'stork', 'pelican', 'tern', 'terns', 'puffin', 'albatross',
    'swan', 'swans', 'pigeon', 'pigeons', 'dove', 'swift', 'swallow', 'gull', 'gulls',
    'bear', 'bears', 'fox', 'foxes', 'wolf', 'wolves', 'rabbit', 'rabbits',
    'mouse', 'mice', 'rat', 'rats', 'deer', 'elk', 'moose', 'beaver', 'beavers',
    'otter', 'otters', 'weasel', 'badger', 'raccoon', 'skunk', 'possum', 'opossum',
    'squirrel', 'squirrels', 'chipmunk', 'hedgehog', 'mole', 'moles', 'bat', 'bats',
    'koala', 'sloth', 'sloths', 'anteater', 'armadillo', 'pangolin', 'pangolins',
    'platypus', 'echidna', 'dolphin', 'dolphins', 'whale', 'whales', 'porpoise',
    'orca', 'orcas', 'seal', 'seals', 'walrus', 'manatee', 'dugong',
    'lizard', 'lizards', 'gecko', 'geckos', 'iguana', 'chameleon', 'chameleons',
    'komodo', 'turtle', 'turtles', 'tortoise', 'tortoises',
    'alligator', 'alligators', 'crocodile', 'crocodiles',
    'salamander', 'newt', 'frog', 'frogs', 'toad', 'toads', 'axolotl',
    'shark', 'sharks', 'ray', 'rays', 'tuna', 'salmon', 'trout', 'bass', 'catfish',
    'eel', 'eels', 'seahorse', 'anglerfish', 'swordfish', 'marlin',
    'bee', 'bees', 'honeybee', 'honeybees', 'ant', 'ants', 'wasp', 'wasps',
    'hornet', 'beetle', 'beetles', 'butterfly', 'butterflies', 'moth', 'moths',
    'dragonfly', 'grasshopper', 'cricket', 'mantis', 'scorpion',
    'octopus', 'octopuses', 'squid', 'cuttlefish', 'nautilus',
    'jellyfish', 'starfish', 'urchin', 'lobster', 'shrimp', 'prawn',
    'slug', 'slugs', 'snail', 'snails',
    'tyrannosaurus', 'triceratops', 'stegosaurus', 'brontosaurus', 'velociraptor',
    'pterodactyl', 'pteranodon', 'sauropod', 'sauropods', 'theropod', 'theropods',
    # Behavior / communication
    'dance', 'dances', 'danced', 'dancing', 'song', 'songs', 'sing', 'sings', 'sang', 'sung',
    'call', 'calls', 'called', 'calling', 'chirp', 'chirps', 'chirped',
    'roar', 'roars', 'roared', 'howl', 'howls', 'howled', 'bark', 'barks',
    'nectar', 'pollen', 'pollinate', 'pollinates', 'pollinated', 'pollinator',
    'nestmate', 'nestmates', 'colonies', 'hive', 'hives',
    'waggle', 'forage', 'forages', 'foraged', 'foraging',
    # Habitats / biomes (these are wonder material at every tier)
    'desert', 'deserts', 'rainforest', 'rainforests', 'forest', 'forests',
    'jungle', 'jungles', 'tundra', 'savanna', 'savannah', 'grassland', 'grasslands',
    'ocean', 'oceans', 'sea', 'seas', 'river', 'rivers', 'lake', 'lakes',
    'pond', 'ponds', 'mountain', 'mountains', 'cave', 'caves',
    'polar', 'tropical', 'arctic', 'antarctic', 'temperate', 'reef', 'reefs',
    'coral', 'corals', 'tide', 'tidepool', 'mangrove', 'mangroves',
    'wetland', 'wetlands', 'marsh', 'swamp', 'estuary',
    # More biology + measurement context
    'wet', 'dry', 'cold', 'hot', 'warm', 'snow', 'snowy', 'ice', 'icy',
    'water', 'air', 'sun', 'sunlight', 'rain', 'rainfall', 'climate',
    'temperature', 'pressure', 'humidity', 'darkness', 'light',
    'sized', 'size', 'big', 'small', 'large', 'tiny', 'huge', 'giant',
    'massive', 'minute', 'enormous',
}


def gate_wonder_bias_check(q: dict) -> Optional[str]:
    """Stems should include any wonder signal — a behavior verb, adaptation cue,
    specific number, biology vocabulary, or comparative framing. Pure
    definition-lookup stems fail. (Permissive — designed to catch only truly
    empty 'What does X mean?'-style stems.)"""
    stem = q.get('question', '')
    # Any digit in the stem passes (numbers are strong wonder signals)
    if re.search(r'\d', stem):
        return None
    # Any wonder word present passes
    stem_words = set(re.findall(r"[A-Za-z][A-Za-z'-]+", stem.lower()))
    if stem_words & _WONDER_WORDS:
        return None
    return 'wonder_bias_check: stem lacks any wonder signal (no behavior, biology vocab, number, or comparative framing)'


# --------------------------------------------------------------------------
# Gate: duplicate
# --------------------------------------------------------------------------


def make_duplicate_gate():
    """Return a gate function that closes over a seen-set, tracking duplicates
    across a single batch."""
    seen = set()
    def gate_duplicate(q: dict) -> Optional[str]:
        stem = q.get('question', '').strip().lower()
        # First 80 chars as fingerprint
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
]


def run_gates(q: dict) -> dict[str, Optional[str]]:
    return {name: fn(q) for name, fn in PER_QUESTION_GATES}


def run_bank(qs: list[dict]) -> dict:
    per_gate_fail = {name: 0 for name, _ in PER_QUESTION_GATES}
    fail_examples = {name: [] for name, _ in PER_QUESTION_GATES}
    fail_count = 0
    dup_gate = make_duplicate_gate()
    for q in qs:
        # Per-question gates
        results = run_gates(q)
        # Plus duplicate (stateful across batch)
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
    """Pull exemplars from _animal_exemplars.py for cross-validation."""
    here = Path(__file__).parent
    path = here / '_animal_exemplars.py'
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
                print(f'  {name:30s} {count} fails')


if __name__ == '__main__':
    main()
