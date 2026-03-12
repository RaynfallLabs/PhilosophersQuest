#!/usr/bin/env python3
"""
Step 1: Classify every monster and write data/monsters_art_brief.json.
Run: python data/gen_monster_art_brief.py
"""
import json, os

ROOT    = os.path.join(os.path.dirname(__file__), '..')
IN_PATH = os.path.join(ROOT, 'data', 'monsters.json')
OUT_PATH= os.path.join(ROOT, 'data', 'monsters_art_brief.json')

# ---------------------------------------------------------------------------
# Silhouette classifier
# ---------------------------------------------------------------------------

def classify_silhouette(mid):
    n = mid.lower()

    # Oozes / amorphous
    if any(k in n for k in ['ooze','jelly','slime','pudding','blob','cube','mold',
                              'gas_spore','gelatinous','rot_grub']):
        return 'blob_ooze'

    # Floating orbs / eyes
    if any(k in n for k in ['beholder','floating_eye']):
        return 'orb_floating'

    # Elementals — specific first
    if 'fire_elemental' in n or (('fire' in n or 'magma' in n) and 'elemental' in n):
        return 'elemental_fire'
    if any(k in n for k in ['ice_elemental','frost_elemental','cold_elemental']):
        return 'elemental_ice'
    if 'earth_elemental' in n or ('earth' in n and 'elemental' in n):
        return 'elemental_earth'
    if any(k in n for k in ['storm_elemental','air_elemental','void_elemental']):
        return 'elemental_storm'
    if 'elemental' in n:
        return 'elemental_storm'

    # Dragons — large vs small forms
    if any(k in n for k in ['ancient_dragon','elder_dragon','adult_dragon','adult_blue','adult_red',
                              'young_dragon','young_red','young_black']):
        return 'dragon_large'
    if 'dragon' in n:
        return 'dragon_large'
    if any(k in n for k in ['wyvern','lindworm','dread_wyrm','wyrm','drake']):
        return 'dragon_small'

    # Undead — specific archetypes
    if any(k in n for k in ['ancient_lich','greater_lich','lich_sovereign','lich_king',
                              'demi_lich','pale_master','bone_witch','necromancer']):
        return 'lich_caster'
    if any(k in n for k in ['skeleton','bone_archer','burning_skeleton','frost_skeleton',
                              'skeletal','bone_golem','bone_titan','ossuary']):
        return 'undead_skeleton'
    if any(k in n for k in ['ghost','wraith','shade','shadow','specter','wight','banshee',
                              'allip','poltergeist','death_echo','entropy_wraith','spectral',
                              'berserker_spirit','desert_wraith','duat_shade','ba_spirit',
                              'soul_shadow','nightmare_shade','forsaken','hollow_one',
                              'sluagh','fetch','haunt','nightshade','void_wraith',
                              'greater_shadow','vrykolakas','strigoi']):
        return 'undead_ghost'
    if any(k in n for k in ['zombie','mummy','draugr','huecuva','mohrg','gravehound',
                              'revenant','jiangshi','plague_zombie','rotting_zombie',
                              'undead_dragon']):
        return 'undead_zombie'
    if any(k in n for k in ['lich','dread_knight','death_knight','cairn_wight','tomb_guardian',
                              'grave_guardian','crypt_thing','dread_wraith']):
        return 'lich_caster'

    # Vampires
    if 'vampire' in n:
        return 'vampire_noble'

    # Lycanthropes
    if any(k in n for k in ['werewolf','werebear','wererat','weretiger','elder_werewolf',
                              'wolfman']):
        return 'werewolf'

    # Constructs / golems
    if any(k in n for k in ['golem','construct','clockwork','animated_armor','shield_guardian',
                              'wood_golem','iron_golem','clay_golem','stone_golem',
                              'thoth_construct']):
        return 'construct_golem'

    # Trolls
    if 'troll' in n:
        return 'troll'

    # Bats
    if 'bat' in n:
        return 'bat'

    # Birds / avians
    if any(k in n for k in ['bird','raven','harpy','roc','thunderbird','tengu','peryton',
                              'stymphalian','hugin','phoenix','owl']):
        return 'avian_bird'

    # Winged quadrupeds
    if any(k in n for k in ['griffin','hippogriff','pegasus','owlbear']):
        return 'winged_quadruped'

    # Demons / devils / fiends (winged humanoids)
    if any(k in n for k in ['demon','devil','balor','vrock','erinyes','pazuzu','incubus',
                              'succubus','lemure','marilith','nalfeshnee','glabrezu',
                              'hezrou','bearded_devil','abyssal','arch_demon',
                              'demon_emperor','djinn','ruinous_djinn','bone_devil',
                              'chain_devil','greater_demon','abyssal_champion',
                              'abyssal_overlord']):
        return 'demon_winged'

    # Serpents / worm-like
    if any(k in n for k in ['serpent','snake','cobra','naga','python','jormungandr',
                              'world_serpent','sea_serpent']):
        return 'serpent_snake'
    if any(k in n for k in ['worm','crawler','leviathan','void_leviathan','roper',
                              'lurker','carrion_crawler','void_crawler']):
        return 'serpent_worm'

    # Insects / arachnids
    if any(k in n for k in ['spider','beetle','bug','wasp','scarab','scorpion','mantis',
                              'centipede','web_spinner','ettercap','piercer','stirge',
                              'hook_horror','darkmantle']):
        return 'insect_spider'

    # Rodents
    if any(k in n for k in ['rat','mouse']):
        return 'rat_rodent'

    # Amphibians
    if any(k in n for k in ['frog','toad','bullywug','cave_toad']):
        return 'amphibian_frog'

    # Plants
    if any(k in n for k in ['vine','plant','yellow_musk','thorn','myconid','fungus',
                              'shroom','assassin_vine','violet_fungus','yellow_mold',
                              'brown_mold','thorn_slinger']):
        return 'plant_creature'

    # Large quadrupeds
    if any(k in n for k in ['dire_bear','cave_bear','displacer','dire_lion','manticore',
                              'cath_palug','sphinx','carbuncle','basilisk','catoblepas',
                              'behir','chimera','rust_monster','grick']):
        return 'quadruped_large'

    # Medium quadrupeds
    if any(k in n for k in ['wolf','hound','dog','fenrir','blink_dog','death_dog',
                              'hecate_hound','fionn_hound','shadow_hound','charnel_hound',
                              'each_uisce','winter_wolf','nue','peryton','hyena',
                              'komodo','phase_spider_lesser','trapper','xorn',
                              'cave_bear','rock_python','dire_rat','giant_rat',
                              'giant_frog','giant_lizard','giant_wasp','giant_eagle',
                              'giant_centipede','giant_scorpion','giant_spider',
                              'giant_mantis','giant_beetle','giant_wasp',
                              'cloaker','shambling_mound']):
        return 'quadruped_medium'

    # Humanoid — small
    if any(k in n for k in ['goblin','kobold','pixie','sprite','leprechaun','boggart',
                              'changeling','redcap','spriggan','puca','grid_bug',
                              'dretch','mane_demon','imp','quasit','homunculus',
                              'myconid_worker']):
        return 'humanoid_small'

    # Humanoid — casters
    if any(k in n for k in ['mage','shaman','witch','wizard','sorcerer','cultist',
                              'apprentice','warlock','sorceress','sage','thoth',
                              'drow_mage','drow_priestess','lich_apprentice',
                              'battle_mage','goblin_shaman','orc_shaman','skeleton_mage',
                              'necromancer_lord','necromancer_apprentice']):
        return 'humanoid_caster'

    # Humanoid — large
    if any(k in n for k in ['giant','cyclops','fomorian','titan','ettin','ogre',
                              'two_headed_ogre','undead_colossus']):
        return 'humanoid_large'

    # Humanoid — medium (default for most bipeds)
    return 'humanoid_medium'


# ---------------------------------------------------------------------------
# Feature classifier
# ---------------------------------------------------------------------------

def classify_features(mid, silhouette):
    n = mid.lower()
    f = set()

    if any(k in n for k in ['dragon','drake','wyvern','wyrm','bat','harpy','roc',
                              'griffin','hippogriff','pegasus','angel','valkyrie',
                              'thunderbird','peryton','demon','devil','balor','vrock',
                              'erinyes','pazuzu','abyssal','arch_demon','demon_emperor',
                              'djinn','ruinous_djinn']):
        f.add('wings')

    if any(k in n for k in ['demon','devil','satyr','minotaur','bull','djinn','balor',
                              'death_knight','abyssal_champion','imp','quasit','dragon',
                              'drake','chaos','redcap','death_lord','lich_sovereign',
                              'demon_emperor','ruinous_djinn','abyssal_overlord']):
        f.add('horns')

    if any(k in n for k in ['dragon','demon','devil','lizard','serpent','snake','wyvern',
                              'drake','kobold','imp','quasit','rat','wolf','cat','lion',
                              'sphinx','manticore','scorpion','scorpion','basilisk',
                              'lich_sovereign']):
        f.add('tail')

    if any(k in n for k in ['mind_flayer','aboleth','void_crawler','otyugh','void_leviathan',
                              'elder_mind_flayer','tentacle','cthulhu','crawler',
                              'gibbering','carrion']):
        f.add('tentacles')

    if any(k in n for k in ['king','lord','sovereign','emperor','prince','noble','commander',
                              'warlord','chieftain','overlord','vampire_lord','vampire_noble']):
        f.add('crown')

    if any(k in n for k in ['knight','champion','warrior','guard','soldier','death_knight',
                              'abyssal_champion','einherjar','bandit_captain','mercenary',
                              'animated_armor','shield_guardian']):
        f.add('armor')

    if any(k in n for k in ['mage','shaman','witch','wizard','sorcerer','cultist','necromancer',
                              'lich','pale_master','battle_mage','bone_witch','warlock',
                              'drow_mage','drow_priestess','goblin_shaman','skeleton_mage',
                              'orc_shaman','lich_apprentice','necromancer_lord',
                              'necromancer_apprentice','thoth']):
        f.add('staff')

    if any(k in n for k in ['fire','flame','burning','infernal','hellfire','balor',
                              'ruinous_djinn','magma','burning_skeleton','fire_gland']):
        f.add('flames')

    if any(k in n for k in ['frost','ice','frozen','cold','winter','crystal',
                              'frost_skeleton','frost_giant','drake_cold','ice_troll',
                              'ice_elemental','ancient_dragon','ancient_lich']):
        f.add('ice')

    if any(k in n for k in ['lich','demi_lich','skeleton','death_knight','pale_master',
                              'mohrg','bone_witch','undead_colossus','bone_titan',
                              'burning_skeleton','frost_skeleton','ancient_lich',
                              'lich_sovereign','greater_lich','lich_apprentice']):
        f.add('skull')

    if any(k in n for k in ['will_o_wisp','ghost','phantom','specter','wraith','shadow',
                              'ethereal','haunting','void','entropy','greater_shadow',
                              'allip','spectral','shade','banshee','soul','death_echo',
                              'ba_spirit','nightshade','nightmare']):
        f.add('glow')

    if any(k in n for k in ['hydra','chimera','two_headed','ettin','gibbering']):
        f.add('multi_head')

    if any(k in n for k in ['spider','web_spinner','ettercap']):
        f.add('web')

    if any(k in n for k in ['lightning','shock','storm','thunder','zap']):
        f.add('lightning')

    return sorted(f)


# ---------------------------------------------------------------------------
# Palette deriver
# ---------------------------------------------------------------------------

def derive_palette(primary_list):
    r, g, b = primary_list
    def darken(c, f=0.45):  return [max(0, int(x*f)) for x in c]
    def lighten(c, f=1.45): return [min(255, int(x*f)) for x in c]
    def saturate(c):
        mx = max(c); mn = min(c)
        if mx == mn: return c
        return [min(255, int(x * 1.3)) if x == mx else max(0, int(x * 0.7)) for x in c]
    return {
        'primary':   primary_list,
        'secondary': lighten(primary_list, 1.3),
        'dark':      darken(primary_list, 0.4),
        'highlight': lighten(primary_list, 1.7),
        'saturated': saturate(primary_list),
    }


# ---------------------------------------------------------------------------
# Size estimator
# ---------------------------------------------------------------------------

def estimate_size(mid, mdef):
    n = mid.lower()
    lvl = mdef.get('min_level', 1)

    if any(k in n for k in ['ancient','soul_eater','death_lord','world_serpent',
                              'entropy_wraith','void_leviathan']):
        return 1.55
    if any(k in n for k in ['elder_dragon','lich_sovereign','demon_emperor','ancient_lich',
                              'iron_golem','bone_titan','undead_colossus']):
        return 1.45
    if any(k in n for k in ['adult_dragon','greater_lich','arch_demon','abyssal_overlord',
                              'dread_wyrm','giant_spider','hill_giant','frost_giant',
                              'fire_giant','cloud_giant','storm_giant','stone_giant',
                              'beholder','elder_beholder','elder_mind_flayer']):
        return 1.35
    if any(k in n for k in ['young_dragon','dragon','hydra','wyrm','ogre','cyclops',
                              'vampire_lord','lich','beholder','troll','bone_golem',
                              'greater_demon','death_knight','wyvern','vampire','abyssal_champion',
                              'void_leviathan','spectral_lord','lich_sovereign']):
        return 1.20
    if any(k in n for k in ['giant_rat','grid_bug','bat','imp','quasit','mane','lemure',
                              'pixie','sprite','leprechaun','boggart','grid_bug',
                              'myconid_worker','grub','spore']):
        return 0.65
    if any(k in n for k in ['goblin','kobold','dretch','homunculus','redcap',
                              'dire_rat','cave_toad']):
        return 0.75
    if any(k in n for k in ['orc','hobgoblin','gnoll','brigand','troglodyte','cultist',
                              'dark_elf','drow','satyr','fetchv','kuo_toa']):
        return 0.95

    # Scale slightly by level
    base = 0.85 + min(0.4, lvl * 0.005)
    return round(base, 2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    with open(IN_PATH, encoding='utf-8') as f:
        monsters = json.load(f)

    briefs = {}
    for mid, mdef in monsters.items():
        silhouette = classify_silhouette(mid)
        features   = classify_features(mid, silhouette)
        palette    = derive_palette(mdef['color'])
        size       = estimate_size(mid, mdef)

        briefs[mid] = {
            'name':       mdef['name'],
            'silhouette': silhouette,
            'size':       size,
            'features':   features,
            'palette':    palette,
            'level':      mdef.get('min_level', 1),
            'symbol':     mdef.get('symbol', '?'),
        }

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(briefs, f, indent=2)

    # Print summary
    from collections import Counter
    counts = Counter(v['silhouette'] for v in briefs.values())
    print(f"Classified {len(briefs)} monsters:")
    for sil, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {sil:28s} {n:3d}")
    print(f"\nWrote {OUT_PATH}")

if __name__ == '__main__':
    main()
