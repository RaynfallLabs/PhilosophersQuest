#!/usr/bin/env python3
"""Add art briefs for the 24 missing monsters."""
import json, os

ROOT = os.path.join(os.path.dirname(__file__), '..')
BRIEF_PATH = os.path.join(ROOT, 'data', 'monsters_art_brief.json')
MONSTERS_PATH = os.path.join(ROOT, 'data', 'monsters.json')


def derive_palette(primary):
    r, g, b = primary
    def darken(c, f=0.45):  return [max(0, int(x*f)) for x in c]
    def lighten(c, f=1.45): return [min(255, int(x*f)) for x in c]
    def saturate(c):
        mx = max(c); mn = min(c)
        if mx == mn: return c
        return [min(255, int(x * 1.3)) if x == mx else max(0, int(x * 0.7)) for x in c]
    return {
        'primary':   primary,
        'secondary': lighten(primary, 1.3),
        'dark':      darken(primary, 0.4),
        'highlight': lighten(primary, 1.7),
        'saturated': saturate(primary),
    }


# Define the 24 missing monsters with their art brief properties
MISSING_MONSTERS = {
    # === 5 Main Bosses ===
    'asterion_minotaur': {
        'silhouette': 'humanoid_large',
        'features': ['horns', 'tail'],
        'size': 1.4,
    },
    'medusa_gorgon': {
        'silhouette': 'humanoid_caster',
        'features': ['tail'],
        'size': 1.3,
    },
    'fafnir_dragon': {
        'silhouette': 'dragon_large',
        'features': ['wings', 'flames', 'horns', 'tail'],
        'size': 1.5,
    },
    'fenrir_wolf': {
        'silhouette': 'quadruped_large',
        'features': ['tail'],
        'size': 1.45,
    },
    'abaddon_destroyer': {
        'silhouette': 'demon_winged',
        'features': ['wings', 'horns', 'flames', 'glow', 'tail'],
        'size': 1.5,
    },

    # === 19 Mini-bosses ===
    'arachne': {
        'silhouette': 'insect_spider',
        'features': ['web'],
        'size': 1.0,
    },
    'talos': {
        'silhouette': 'construct_golem',
        'features': ['glow'],
        'size': 1.2,
    },
    'echidna': {
        'silhouette': 'serpent_snake',
        'features': ['tail'],
        'size': 1.1,
    },
    'erlking': {
        'silhouette': 'humanoid_caster',
        'features': ['crown', 'staff'],
        'size': 1.1,
    },
    'camazotz': {
        'silhouette': 'bat',
        'features': ['wings'],
        'size': 1.15,
    },
    'cacus': {
        'silhouette': 'humanoid_large',
        'features': ['flames'],
        'size': 1.3,
    },
    'the_sphinx': {
        'silhouette': 'quadruped_large',
        'features': ['wings', 'crown', 'tail'],
        'size': 1.25,
    },
    'rangda': {
        'silhouette': 'humanoid_caster',
        'features': ['flames', 'skull', 'staff'],
        'size': 1.15,
    },
    'nemean_lion': {
        'silhouette': 'quadruped_large',
        'features': ['glow', 'tail'],
        'size': 1.25,
    },
    'baba_yaga': {
        'silhouette': 'humanoid_caster',
        'features': ['staff'],
        'size': 1.05,
    },
    'jormungandr_juvenile': {
        'silhouette': 'serpent_worm',
        'features': ['glow'],
        'size': 1.2,
    },
    'sets_jackal': {
        'silhouette': 'humanoid_medium',
        'features': ['staff'],
        'size': 1.1,
    },
    'green_knight': {
        'silhouette': 'humanoid_large',
        'features': ['armor', 'glow'],
        'size': 1.25,
    },
    'charybdis': {
        'silhouette': 'blob_ooze',
        'features': ['tentacles'],
        'size': 1.2,
    },
    'ravanas_arm': {
        'silhouette': 'humanoid_medium',
        'features': ['flames'],
        'size': 1.1,
    },
    'wendigo': {
        'silhouette': 'undead_zombie',
        'features': ['ice', 'horns'],
        'size': 1.2,
    },
    'wild_hunt_captain': {
        'silhouette': 'humanoid_medium',
        'features': ['armor', 'glow'],
        'size': 1.15,
    },
    'anansi': {
        'silhouette': 'insect_spider',
        'features': ['glow', 'web'],
        'size': 1.15,
    },
    'nidhoggr_fragment': {
        'silhouette': 'dragon_small',
        'features': ['glow', 'tail'],
        'size': 1.1,
    },
}


def main():
    with open(MONSTERS_PATH, encoding='utf-8') as f:
        monsters = json.load(f)

    with open(BRIEF_PATH, encoding='utf-8') as f:
        briefs = json.load(f)

    added = 0
    for mid, spec in MISSING_MONSTERS.items():
        if mid in briefs:
            print(f"  SKIP (already exists): {mid}")
            continue

        mdef = monsters[mid]
        palette = derive_palette(mdef['color'])

        briefs[mid] = {
            'name': mdef['name'],
            'silhouette': spec['silhouette'],
            'size': spec['size'],
            'features': sorted(spec['features']),
            'palette': palette,
            'level': mdef.get('min_level', 1),
            'symbol': mdef.get('symbol', '?'),
        }
        added += 1
        print(f"  ADDED: {mid} ({spec['silhouette']}, size={spec['size']})")

    with open(BRIEF_PATH, 'w', encoding='utf-8') as f:
        json.dump(briefs, f, indent=2)

    print(f"\nAdded {added} briefs. Total now: {len(briefs)}")


if __name__ == '__main__':
    main()
