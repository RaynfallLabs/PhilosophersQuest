"""
Story and flavor encounters (data/flavor_encounters.json): everything that is
not a block anchor. Light ones (vendors, moments, jokes) never touch karma;
medium and high story encounters may offer one gated point (DEEDS_KARMA_DESIGN
section 3, ENCOUNTER_STORIES_DRAFT.md). The block anchors are npc_encounters.py.

Spawn rate (the legacy roll, while the Road is off): ~40% per floor,
independent of the anchors.
One-shot: each encounter can only be triggered once per run.
Follow-ups (``callback_only``) are never rolled here: the deed that opens
them schedules them (an outcome's ``schedule``; game_road.py). With the
Road on (``karma_rules.json: road_enabled``) road.py replaces this roll.
"""
import json
import os
import random

from paths import data_path

# ---------------------------------------------------------------------------
# Encounter definitions
# ---------------------------------------------------------------------------
# Every flavor and story encounter lives in data/flavor_encounters.json (the
# rule: all game data is loaded from JSON). The fields are described in
# encounter_schema.py and DEEDS_KARMA_DESIGN.md section 4; the content is
# ENCOUNTER_STORIES_DRAFT.md. The five that were a Python literal here (the
# Wandering Merchant, the Old Traveler, Gikk, the Dwarven Smith and the Blind
# Oracle) moved to the JSON or were merged in 2026-10.

_GEN_PATH = os.path.join(data_path('data'), 'flavor_encounters.json')


def _load_encounters() -> list:
    with open(_GEN_PATH, encoding='utf-8') as f:
        return json.load(f)


FLAVOR_ENCOUNTERS: list[dict] = _load_encounters()

# Schema defaults (role 'story', stakes 'light', band = [min_level,
# max_level]) for any entry that leaves them out; see encounter_schema.py.
from encounter_schema import normalise_all as _normalise_all  # noqa: E402
_normalise_all(FLAVOR_ENCOUNTERS, source='flavor')


# ---------------------------------------------------------------------------
# Spawn logic
# ---------------------------------------------------------------------------

def select_flavor_encounters(level_count: int = 100) -> dict[int, dict]:
    """Select which floors get flavor encounters for this run.
    Returns {level: encounter_dict} for ~40% of floors.
    """
    BOSS_LEVELS = {20, 40, 60, 80, 100}
    eligible_by_level = {}
    for level in range(1, level_count + 1):
        if level in BOSS_LEVELS:
            continue  # no flavor NPCs on boss floors
        # A callback-only encounter (a follow-up such as the Great Lion, the
        # Relic Broker, Brother Sacristan's chapel or the Watch Post) is never
        # rolled: a deed schedules it (an outcome's 'schedule', game_road.py).
        pool = [e for e in FLAVOR_ENCOUNTERS
                if e['min_level'] <= level <= e['max_level']
                and not e.get('callback_only')]
        if pool:
            eligible_by_level[level] = pool

    selected = {}
    used_tags = set()
    levels = list(eligible_by_level.keys())
    random.shuffle(levels)

    for level in levels:
        if random.random() > 0.40:
            continue  # ~40% spawn rate
        pool = [e for e in eligible_by_level[level] if e['tag'] not in used_tags]
        if not pool:
            continue
        enc = random.choice(pool)
        selected[level] = enc
        used_tags.add(enc['tag'])

    # Gold costs and rewards at today's scale (economy.py), once, here.
    import economy
    return {lvl: economy.price_encounter(enc) for lvl, enc in selected.items()}
