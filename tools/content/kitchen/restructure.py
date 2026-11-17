"""Restructure the frozen recipe book so a run can cook it (slice K1b).

``structure.json`` was generated once (``build_kitchen.py --structure``) without
knowing how often each part turns up. The simulator says (``part_freq.json``):
many parts turn up in only some runs, so dishes mixing two or more of them, and
feasts mixing several, were luck, not effort. This script edits the frozen
structure ON PURPOSE, by the rules in ``part_rules.py``, and prints every change:

1. a feast keeps its gate (its first ingredient: the trophy or boss part) and
   its id, theme and size; each other part that turns up too rarely is swapped
   for a common part, or (in the early slot) an early part a saving hero
   reliably banks; a deep slot stays deep;
2. an ordinary multi-dish keeps ONE uncommon part (the one its name names,
   else the one with no other dish to spare) and the others are swapped for
   common partners of the same depth band, so the dish keeps its tier and
   whether it spans depths (a hand-picked stand-in in ``SWAP`` may move a
   dish's tier for its theme; a change in whether it spans depths is printed);
3. every ingredient left in fewer than two multi-dishes gets new ones: it,
   common partners close in depth (or, for some, a common part from the far
   end of the dungeon: the cross-depth dishes) and common food or forage;
4. nothing else changes. Run on a book that keeps the rules, it changes nothing.

    py tools/content/kitchen/restructure.py            # edit structure.json, print changes
    py tools/content/kitchen/restructure.py --dry-run  # print only
    py tools/content/kitchen/restructure.py --log FILE # also write a naming worksheet

Then name what changed: a dish whose name names a part it lost gets a new
name (in ``dishes_*.txt``), each new dish gets a name and a flavour line
(``dishes_3.txt``), and ``build_kitchen.py`` is run; its checks must pass.
"""
import argparse
import json
import math
import os
import random
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_kitchen as B  # noqa: E402
import part_rules as PR  # noqa: E402

STRUCTURE = os.path.join(HERE, 'structure.json')
# A dish whose name names more than one uncommon part keeps this one
# (reviewed by hand; everything else is decided by the rules below).
KEEP = {
    'dish_014': 'the_sphinx_prime',         # Riddler's Ploughman's Plate: the riddle
    'dish_041': 'charybdis_prime',          # Whirlpool Grub Boil: the whirlpool is Charybdis
    'dish_042': 'charybdis_prime',          # Bangers and Whirlpool Mash
    'dish_088': 'gibbering_mouther_prime',  # Mumbling Mushroom Dumplings
    'dish_089': 'leprechaun_prime',         # Lucky Haggis
    'dish_093': 'mimic_prime',              # Sticky Mud Pudding: the mimic's glue
    'dish_116': 'anubis_guardian_prime',    # Jackal-God's Salt Broth
    'dish_118': 'cerberus_prime',           # Gates of Hades Hotpot
    'dish_154': 'kusarikku_prime',          # Gatekeeper's Hash: the bull-man of the gate
    'dish_165': 'tengu_warrior_prime',      # Swordsman's Mixed Grill
    'dish_166': 'ethereal_filcher_prime',   # Light-Fingers Platter
    'dish_170': 'mohrg_prime',              # Snap-and-Crackle Ribs
    'dish_171': 'weretiger_prime',          # Tiger-Rib Fricassee
    'dish_181': 'hook_horror_prime',        # Echo-and-Cog Steak: the echo and the steak
    'dish_188': 'gravehound_prime',         # Lookout's Mixed Grill: the nose
    'dish_189': 'bat_prime',                # Echo-and-Wisp Pie: the echo
}
# Hand-picked stand-ins, {dish: {part out: part in}}, where the rules' pick
# would break the dish's theme (reviewed against each name and flavour line).
# A record of slice K1b (2026-11-14): its stand-ins are frozen in
# structure.json. Some name a part of a person (harrow_witch_prime,
# cult_initiate_prime...), all gone since 2026-11-16 (people.txt: people are
# never harvested); those dishes were re-sourced by hand. Before re-running
# this, drop or replace every stand-in that names a part no longer in the
# build.
# A feast's stand-in follows its lore: Norse feasts take frost giants and the
# World Serpent, Baba Yaga's hut takes a roc's drumstick.
SWAP = {
    'feast_01': {'vrykolakas_prime': 'minotaur_prime'},
    'feast_02': {'baba_yaga_prime': 'young_dragon_prime', 'scarab_swarm_prime': 'harrow_witch_prime'},
    'feast_03': {'carrion_crawler_prime': 'basilisk_prime', 'philosopher_tea': 'dried_meat'},
    'feast_04': {'anansi_prime': 'cloud_giant_prime', 'naga_guardian_prime': 'owlbear_prime'},
    'feast_06': {'ra_serpent_prime': 'drake_fire_prime'},
    'feast_07': {'ravanas_arm_prime': 'world_serpent_prime'},
    'feast_08': {'black_pudding_prime': 'troll_prime'},
    'feast_15': {'rangda_prime': 'frost_giant_prime', 'banshee_prime': 'valkyrie_shade_prime'},
    'feast_17': {'stirge_swarm_prime': 'cult_initiate_prime'},
    'feast_18': {'ravanas_arm_prime': 'death_knight_prime'},
    'feast_19': {'burning_skeleton_prime': 'magma_elemental_prime'},
    'feast_20': {'carbuncle_prime': 'sea_dragon_spawn_prime'},
    'feast_26': {'iron_patriarch_prime': 'frost_giant_prime', 'wood_golem_prime': 'hill_giant_prime'},
    'feast_27': {'jormungandr_juvenile_prime': 'world_serpent_prime',
                 'iron_patriarch_prime': 'stone_giant_prime'},
    'feast_28': {'baba_yaga_prime': 'titan_prime', 'clay_golem_prime': 'stone_golem_prime'},
    'feast_29': {'ravanas_arm_prime': 'pit_fiend_spawn_prime', 'revenant_prime': 'ugallu_demon_prime',
                 'deep_fungi': 'apple'},
    'feast_32': {'ravanas_arm_prime': 'demon_knight_prime', 'redcap_prime': 'orc_warrior_prime'},
    'feast_33': {'lesser_death_prime': 'wight_prime'},
    'feast_34': {'jormungandr_juvenile_prime': 'world_serpent_prime',
                 'iron_patriarch_prime': 'earth_elemental_prime'},
    'feast_36': {'sea_serpent_norse_prime': 'roc_chick_prime'},
    'dish_014': {'huecuva_prime': 'ossuary_horror_prime'},
    'dish_015': {'ba_spirit_prime': 'ammit_spawn_prime'},
    'dish_034': {'gravehound_prime': 'werewolf_prime'},
    'dish_042': {'bugbear_prime': 'ogre_prime', 'void_ration': 'abyssal_kelp'},
    'dish_046': {'yellow_mold_prime': 'violet_fungus_prime'},
    'dish_051': {'giant_wasp_prime': 'pegasus_prime'},
    'dish_052': {'wild_hunt_captain_prime': 'storm_giant_prime'},
    'dish_060': {'scarab_swarm_prime': 'giant_scorpion_prime'},
    'dish_064': {'werebear_prime': 'cave_bear_prime'},
    'dish_070': {'bone_witch_prime': 'death_mage_prime', 'crystal_ooze_prime': 'shade_prime'},
    'dish_071': {'homunculus_prime': 'flesh_golem_prime'},
    'dish_072': {'lahamu_prime': 'specter_prime'},
    'dish_083': {'lizardfolk_prime': 'basilisk_prime'},
    'dish_085': {'myconid_worker_prime': 'violet_fungus_prime'},
    'dish_086': {'myconid_worker_prime': 'assassin_vine_prime'},
    'dish_087': {'bugbear_prime': 'ogre_prime'},
    'dish_088': {'gas_spore_prime': 'lurker_above_prime'},
    'dish_089': {'gibbering_mouther_prime': 'gelatinous_cube_prime'},
    'dish_092': {'mimic_prime': 'roper_prime'},
    'dish_093': {'mud_crawler_prime': 'dretch_prime'},
    'dish_095': {'charybdis_spawn_prime': 'ogre_prime'},
    'dish_098': {'charybdis_spawn_prime': 'water_elemental_prime'},
    'dish_100': {'rust_monster_prime': 'xorn_prime'},
    'dish_101': {'frost_skeleton_prime': 'draugr_prime', 'winter_wolf_prime': 'wolf_pack_leader_prime'},
    'dish_103': {'winter_wolf_prime': 'wolf_pack_leader_prime'},
    'dish_104': {'shadow_demon_prime': 'sable_serpent_prime'},
    'dish_110': {'puca_prime': 'shadow_prime'},
    'dish_111': {'displacer_beast_prime': 'werewolf_prime'},
    'dish_114': {'mummy_prime': 'wight_prime'},
    'dish_115': {'mummy_prime': 'ammit_spawn_prime', 'lesser_death_prime': 'thoth_construct_prime'},
    'dish_116': {'lesser_death_prime': 'ossuary_horror_prime'},
    'dish_117': {'dullahan_spawn_prime': 'valkyrie_shade_prime'},
    'dish_118': {'dullahan_spawn_prime': 'erinyes_lesser_prime'},
    'dish_127': {'giant_centipede_prime': 'wyvern_prime'},
    'dish_130': {'giant_centipede_prime': 'snake_charmer_prime'},
    'dish_131': {'dryad_guardian_prime': 'light_elf_hostile_prime'},
    'dish_132': {'nosferatu_prime': 'cult_initiate_prime'},
    'dish_133': {'nosferatu_prime': 'vampire_prime'},
    'dish_134': {'dryad_guardian_prime': 'troll_prime'},
    'dish_135': {'dryad_guardian_prime': 'moss_sentinel_prime'},
    'dish_137': {'cockatrice_prime': 'roc_chick_prime'},
    'dish_148': {'death_dog_prime': 'wolf_pack_leader_prime'},
    'dish_154': {'otyugh_prime': 'stone_golem_prime'},
    'dish_160': {'giant_mantis_prime': 'giant_scorpion_prime'},
    'dish_161': {'jiangshi_prime': 'phase_spider_prime'},
    'dish_162': {'poltergeist_prime': 'skeleton_prime'},
    'dish_163': {'pixie_swarm_prime': 'light_elf_hostile_prime'},
    'dish_165': {'stymphalian_bird_prime': 'harpy_prime', 'blink_dog_prime': 'shadow_prime'},
    'dish_166': {'wererat_prime': 'bandit_captain_prime', 'arachne_prime': 'shadow_prime',
                 'stymphalian_bird_prime': 'kobold_prime'},
    'dish_167': {'ethereal_filcher_prime': 'dark_elf_prime'},
    'dish_168': {'blink_dog_prime': 'phase_spider_prime'},
    'dish_170': {'grell_prime': 'thunderbird_lesser_prime'},
    'dish_171': {'mohrg_prime': 'vrock_prime'},
    'dish_172': {'cath_palug_prime': 'sphinx_prime'},
    'dish_180': {'jormungandr_spawn_prime': 'nidhogg_brood_prime', 'grick_prime': 'aboleth_lesser_prime'},
    'dish_181': {'clockwork_horror_prime': 'thoth_construct_prime'},
    'dish_188': {'bat_prime': 'werewolf_prime', 'hugin_raven_prime': 'beholder_prime'},
    'dish_189': {'will_o_wisp_prime': 'light_elf_hostile_prime'},
    'dish_192': {'piercer_prime': 'lurker_above_prime'},
    'dish_193': {'strigoi_prime': 'werewolf_prime'},
    'dish_199': {'peryton_prime': 'cave_bear_prime'},
    'dish_201': {'fenrir_pup_prime': 'wolf_pack_leader_prime'},
    'dish_202': {'fenrir_pup_prime': 'wolf_pack_leader_prime'},
    'dish_204': {'revenant_prime': 'manticore_prime'},
    'dish_206': {'dire_lion_prime': 'manticore_prime'},
    'dish_217': {'banshee_prime': 'night_hag_prime'},
}


def rules_for(ings: dict) -> PR.PartRules:
    food_json = B._load(os.path.join(B.ITEMS, 'food.json'))
    freq = PR.load_freq()
    rare = PR.rare_foods({k: food_json[k] for k in B.FOOD}, freq['rules']['rare_food_weight'])

    def role_of(p):
        if p in ings:
            return ings[p]['role']
        return 'food' if p in B.FOOD else None
    return PR.PartRules(freq, role_of, rare)


# ----------------------------------------------------------------------
# Which part a dish's name (or flavour) names
# ----------------------------------------------------------------------

def _stem(tok: str) -> str:
    tok = tok.lower().strip("'")
    if tok.endswith("'s"):
        tok = tok[:-2]
    if tok.endswith('ves'):
        return tok[:-3] + 'f'
    if tok.endswith('ies'):
        return tok[:-3] + 'y'
    if tok.endswith('s') and not tok.endswith('ss') and len(tok) > 3:
        return tok[:-1]
    return tok


def _tokens(text: str) -> set:
    return {_stem(t) for t in re.findall(r"[A-Za-z']+", text.replace('-', ' ')) if len(t) > 2}


class Namer:
    """Scores how plainly a dish's name and flavour name a part: each word of
    the part's name and its creatures' names, weighted by how rare that word
    is across the whole kitchen."""

    def __init__(self, ings, monsters, names):
        self.names = names
        self.words = {}
        df = Counter()
        for iid, r in ings.items():
            words = _tokens(r['name'])
            for m in r['members']:
                words |= _tokens(monsters.get(m, {}).get('name', m.replace('_', ' ')))
            self.words[iid] = words
            df.update(words)
        food = B._load(os.path.join(B.ITEMS, 'food.json'))
        for fid in B.FOOD:
            self.words[fid] = _tokens(food[fid]['name'])
            df.update(self.words[fid])
        self.weight = {w: 1.0 / c for w, c in df.items()}

    def score(self, did: str, p: str):
        name, flavour = self.names.get(did, ('', ''))
        nt, ft = _tokens(name), _tokens(flavour)
        ws = self.words.get(p, set())
        return (round(sum(self.weight[w] for w in ws if w in nt), 3),
                round(sum(self.weight[w] for w in ws if w in ft), 3))


# ----------------------------------------------------------------------
# The restructure
# ----------------------------------------------------------------------

def restructure(S: dict, ings: dict, rules: PR.PartRules, namer: Namer, seed: int = 20261114):
    rng = random.Random(seed)
    log = {'feasts': {}, 'multis': {}, 'new': {}}

    def floor(p):
        return ings[p]['floor'] if p in ings else B.FOOD[p][1]

    def tab(p):
        return ings[p]['tab'] if p in ings else B.FOOD[p][0]

    def pool(p):
        return B._pool_key(ings[p]) if p in ings else B.FOOD[p][0]

    def is_helper(p):
        return p in B.FOOD or ings[p]['role'] == 'dungeon'

    def spans(parts):
        fl = [floor(p) for p in parts]
        return min(fl) <= 20 and max(fl) >= 40

    for did, keep in KEEP.items():
        if did in S and keep not in S[did]['parts']:
            raise SystemExit(f'KEEP {did}: {keep} is not in it')
    for did, sw in SWAP.items():
        for out, inn in sw.items():
            if did in S and inn in S[did]['parts'] and out in S[did]['parts']:
                raise SystemExit(f'SWAP {did}: {inn} is already in it')
            if inn not in ings and inn not in B.FOOD:
                raise SystemExit(f'SWAP {did}: unknown part {inn}')
            if not rules.is_common(inn) and not (S.get(did, {}).get('legendary') and rules.feast_ok(inn)):
                raise SystemExit(f'SWAP {did}: {inn} is not common')
    uses = Counter(p for d in S.values() for p in set(d['parts']))
    seen = {frozenset(d['parts']) for d in S.values()}
    # Stand-ins and partners: ordinary monster parts. Never a secret part, and
    # never a seal demon's or Baba Yaga's (one per run; each keys its own feast).
    bosses = {f'{k}_prime' for k in B.BOSS_FEASTS}
    monsters = [i for i, r in sorted(ings.items())
                if r['role'] == 'prime' and not r['secret'] and i not in bosses]
    common = [i for i in monsters if rules.is_common(i)]
    banked = [i for i in monsters if rules.is_early_saved(i) and not rules.is_common(i)]

    def closeness(c, key):
        return B._closeness(ings[c], key)

    def load(c):
        return max(0, uses[c] - 3)

    def kin(c, p):
        """0 when c is of p's monster family (the dish keeps its theme), else 1."""
        fam = ings[p].get('family') if p in ings else None
        return 0 if fam and ings[c].get('family') == fam else 1

    def score(c, key, like, floor_scale):
        """Lower is better: the nature the dish is for, then the creature's
        family, then spreading the load, then closeness in depth."""
        return (2 * closeness(c, key) + kin(c, like) + load(c)
                + abs(floor(c) - floor(like)) / floor_scale)

    paired = Counter()
    for d in S.values():
        ms = sorted(set(p for p in d['parts'] if p in ings and not is_helper(p)))
        for i, x in enumerate(ms):
            for y in ms[i + 1:]:
                paired[(x, y)] += 1

    def pair_n(a, b):
        return paired[tuple(sorted((a, b)))]

    def helpers(tab_, max_floor, k, exclude):
        """k common foods / forage suited to a dish of `tab_` (never rare food)."""
        cands = []
        for fid, (nat, fl) in sorted(B.FOOD.items()):
            if fl <= max_floor and fid not in exclude and rules.is_common(fid):
                w = 3 if nat == tab_ else 1
                cands.append((fid, w * B.FOOD_RARITY.get(fid, 1.0)))
        for fid, r in sorted(ings.items()):
            if r['role'] == 'dungeon' and r['floor'] <= max_floor and fid not in exclude:
                cands.append((fid, (3 if r['tab'] == tab_ else 0.4) + (2 if uses[fid] < 3 else 0)))
        out = []
        while len(out) < k and cands:
            x = rng.uniform(0, sum(w for _, w in cands))
            for idx, (fid, w) in enumerate(cands):
                x -= w
                if x <= 0:
                    out.append(fid)
                    cands.pop(idx)
                    break
        return out

    def swap(did, d, r, c):
        parts = [c if p == r else p for p in d['parts']]
        seen.discard(frozenset(d['parts']))
        seen.add(frozenset(parts))
        uses[r] -= 1
        uses[c] += 1
        if d.get('anchor') == r:
            d['anchor'] = c
        d['parts'] = parts

    def best(cands, key):
        cands = sorted(cands, key=key)
        return cands[0] if cands else None

    def helper_swap(d, r):
        """A rare food out: a common food or forage of its kind in."""
        rest = [p for p in d['parts'] if p != r]
        mx = max(floor(p) for p in d['parts'])
        for _ in range(20):
            got = helpers(_tab_of_benefit(d['benefit']), mx, 1, set(d['parts']))
            if got and frozenset(rest + got) not in seen:
                return got[0]
        return None

    # -- 2. Ordinary multi-dishes: at most one uncommon part ----------------
    for did, d in S.items():
        if d['legendary']:
            continue
        rare = [p for p in d['parts'] if not rules.is_common(p)]
        if len(rare) <= 1:
            continue

        def keep_key(p, did=did, d=d):
            name_s, flav_s = namer.score(did, p)
            return (ings.get(p, {}).get('secret', False), name_s, flav_s, -(uses[p] - 2),
                    p == d.get('anchor'), p)
        keep = KEEP.get(did) or max(rare, key=keep_key)
        bk = B._benefit_key(d['benefit'])
        tier = B.band_of(max(floor(p) for p in d['parts']))
        for r in [p for p in rare if p != keep]:
            if r in SWAP.get(did, {}):
                c = SWAP[did][r]
            elif is_helper(r):
                c = helper_swap(d, r)
            else:
                rest = [p for p in d['parts'] if p != r]

                def fits(c, rest=rest, d=d, tier=tier):
                    new = rest + [c]
                    return (c not in rest and B.band_of(max(floor(p) for p in new)) == tier
                            and spans(new) == bool(d['cross_depth']) and frozenset(new) not in seen)
                c = best(
                    [c for c in common if fits(c)],
                    lambda c, r=r: (min(score(c, bk, r, 10), score(c, pool(r), r, 10)), c))
            if c is None:
                raise SystemExit(f'{did}: no common stand-in for {r}')
            log['multis'].setdefault(did, []).append((r, c, namer.score(did, r)))
            swap(did, d, r, c)

    # -- 1. Feasts: the gate, then common parts or banked early ones -------
    for did, d in S.items():
        if not d['legendary']:
            continue
        bk = B._benefit_key(d['benefit'])
        for r in [p for p in d['parts'][1:] if not rules.feast_ok(p)]:
            if r in SWAP.get(did, {}):
                c = SWAP[did][r]
            elif is_helper(r):
                c = helper_swap(d, r)
            else:
                rest = [p for p in d['parts'] if p != r]
                fr = floor(r)
                if fr >= 41:
                    pool_ = [c for c in common if floor(c) >= 41]
                elif fr <= 20:
                    pool_ = [c for c in common + banked if floor(c) <= 20]
                else:
                    pool_ = [c for c in common if abs(floor(c) - fr) <= 10]

                def fkey(c, r=r):
                    needy = 0 if (c in banked and uses[c] < 2) else 1
                    return (needy, score(c, bk, r, 20), c)
                c = best([c for c in pool_ if c not in rest and frozenset(rest + [c]) not in seen], fkey)
            if c is None:
                raise SystemExit(f'{did}: no stand-in for {r}')
            log['feasts'].setdefault(did, []).append((r, c, namer.score(did, r)))
            swap(did, d, r, c)

    # A hand-picked stand-in may move a dish across the depth line: say so.
    for kind in ('feasts', 'multis'):
        for did in log[kind]:
            d = S[did]
            now = spans(d['parts'])
            if now != bool(d['cross_depth']):
                log.setdefault('cross_flips', []).append((did, now))
                d['cross_depth'] = now

    # -- 3. New dishes for every ingredient left in fewer than two ---------
    n_cross = sum(1 for d in S.values() if d['cross_depth'])
    n_multi = len(S)
    nums = [int(k.split('_')[1]) for k in S if k.startswith('dish_')]
    next_id = max(nums) + 1
    needy = sorted((i for i in ings if uses[i] < 2), key=lambda i: (floor(i), i))
    for n in needy:
        while uses[n] < 2:
            r = ings[n]
            code = r['detail'] if r['tab'] in ('stat', 'special') else r['tab']
            pk = pool(n)
            fn = floor(n)
            # About a third of the book spans depths: a deep part meets an
            # early common one, or an early part meets a deep common one.
            want_cross = (fn >= 40) or (n_cross < math.ceil(n_multi / 3) and fn <= 20
                                        and rng.random() < 0.5)
            size = rng.choice((2, 3, 3, 3, 4, 4))
            n_mon = 2 if size <= 3 else rng.choice((2, 3))
            parts = [n]
            if want_cross:
                far = [c for c in common if (floor(c) <= 20 if fn >= 40 else floor(c) >= 40)]
                c = best(far, lambda c: (2 * closeness(c, pk) + kin(c, n) + load(c)
                                         + 2 * pair_n(c, n), rng.random()))
                if c:
                    parts.append(c)
            near = [c for c in common if c not in parts and abs(floor(c) - fn) <= 15
                    and (fn <= 20 or floor(c) > 20 or not want_cross)]
            near.sort(key=lambda c: (score(c, pk, n, 15) + 2 * pair_n(c, n), rng.random()))
            for c in near:
                if len(parts) >= n_mon:
                    break
                if frozenset(parts + [c]) not in seen:
                    parts.append(c)
            mx = max(floor(p) for p in parts)
            parts += helpers(r['tab'], mx, max(0, size - len(parts)), set(parts))
            tries = 0
            while frozenset(parts) in seen and tries < 20:
                tries += 1
                parts = parts[:-1] + helpers(r['tab'], mx, 1, set(parts))
            if frozenset(parts) in seen or len(parts) < 2:
                raise SystemExit(f'could not make a new dish for {n}')
            did = f'dish_{next_id:03d}'
            next_id += 1
            cross = spans(parts)
            S[did] = {'parts': parts, 'benefit': code, 'legendary': False, 'kind': 'multi',
                      'anchor': n, 'cross_depth': cross}
            ms = sorted(set(p for p in parts if p in ings and not is_helper(p)))
            for i, x in enumerate(ms):
                for y in ms[i + 1:]:
                    paired[(x, y)] += 1
            seen.add(frozenset(parts))
            for p in parts:
                uses[p] += 1
            n_multi += 1
            n_cross += cross
            log['new'][did] = parts
    return log


def _tab_of_benefit(code):
    return B._nature_split(code)[0]


def write_worksheet(path, S, log, ings, names):
    """The naming worksheet: each changed dish (its name and flavour, what it
    holds now, what was swapped) and each new dish, with every part's nature,
    family and floor."""
    def tag(p):
        if p not in ings:
            return p
        r = ings[p]
        if r['role'] == 'dungeon':
            return r['name']
        return f"{r['name']} [{r['detail'] or r['tab']}/{r['family']}/f{r['floor']}]"

    def floor(p):
        return ings[p]['floor'] if p in ings else B.FOOD[p][1]
    with open(path, 'w', encoding='utf-8') as f:
        for kind in ('feasts', 'multis'):
            for did, swaps in log[kind].items():
                name, flav = names.get(did, ('', ''))
                f.write(f"{did} | {name} | {flav}\n   benefit {S[did]['benefit']}  now: "
                        + ' + '.join(tag(p) for p in S[did]['parts']) + '\n   swapped: '
                        + '; '.join(f'{tag(r)} {sc} -> {tag(c)}' for r, c, sc in swaps) + '\n')
        for did, parts in log['new'].items():
            d = S[did]
            tier = B.band_of(max(floor(p) for p in parts))
            f.write(f"NEW {did} | {d['benefit']} | T{tier}{' CROSS' if d['cross_depth'] else ''} | "
                    + ' + '.join(tag(p) for p in parts) + '\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--log', help='write a naming worksheet here')
    a = ap.parse_args()
    ings, _h, _a = B.build_ingredients()
    rules = rules_for(ings)
    with open(STRUCTURE, encoding='utf-8') as f:
        S = json.load(f)
    names = B._dish_names()
    monsters = B._load(os.path.join(B.DATA, 'monsters.json'))
    namer = Namer(ings, monsters, names)
    before = rules.summary(S)
    log = restructure(S, ings, rules, namer)
    problems = rules.problems(S)
    after = rules.summary(S)

    def nm(p):
        return ings[p]['name'] if p in ings else p
    print(f"feasts changed: {len(log['feasts'])}; multi-dishes changed: {len(log['multis'])}; "
          f"new multi-dishes: {len(log['new'])}")
    for kind in ('feasts', 'multis'):
        for did, swaps in log[kind].items():
            flag = ' [name names a lost part?]' if any(s[2][0] >= 0.25 for s in swaps) else ''
            print(f"  {did} {names.get(did, ('?',))[0]}{flag}: "
                  + '; '.join(f'{nm(r)} -> {nm(c)}' for r, c, _s in swaps))
    if log.get('cross_flips'):
        print('cross-depth changed:', log['cross_flips'])
    print('before:', before)
    print('after: ', after)
    multis = [d for d in S.values() if len(set(d['parts'])) > 1]
    cross = [d for d in multis if d['cross_depth']]
    early_common = [d for d in cross if any(
        (ings[p]['floor'] if p in ings else B.FOOD[p][1]) <= 20 and rules.is_common(p)
        and not (p in B.FOOD or ings[p]['role'] == 'dungeon') for p in d['parts'])]
    print(f'cross-depth: {len(cross)} of {len(multis)}; with an early common monster part: '
          f'{len(early_common)}')
    uses = Counter(p for d in multis for p in set(d['parts']))
    print('multi uses per ingredient:', sorted(Counter(uses[i] for i in ings).items()))
    if problems:
        print('\n'.join(problems[:40]))
        raise SystemExit(f'{len(problems)} rule problems remain')
    if a.log:
        write_worksheet(a.log, S, log, ings, names)
    if not a.dry_run:
        with open(STRUCTURE, 'w', encoding='utf-8') as f:
            json.dump(S, f, ensure_ascii=False, indent=1)
        print('structure.json written')


if __name__ == '__main__':
    main()
