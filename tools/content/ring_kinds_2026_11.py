"""Rings and amulets after the armour redesign (bug bash 3.3.2, plan section 8).

Offline content pass over data/items/accessory.json. Idempotent: run it
again and nothing changes.

1. The 89 common rings and amulets become ten KINDS (data/ring_kinds.json,
   src/rings.py), each tiered I-V by the level it is found at: Protection
   (saving throws), Spell Turning, Regeneration, Invisibility, Sustenance,
   Wizardry; amulets of Life Saving, Wisdom, Intellect, Constitution. The
   powers armour now owns leave (data/enchantments.json): telepathy, sight,
   haste, levitation, displacement, warning, searching, STR / DEX / PER,
   the elements; and every AC ring (no ring gives AC).
   The cursed kinds stay as they are (traps, tier I), found at every depth.
2. The named rings and amulets (UNIQUE_REVIEW below): a moved power stays
   only where the item's lore makes it its own; AC goes from all of them.
   Their tier is their power and depth (more powerful, higher tier): a tier
   above the commons found where they are found, and never under their own
   stat; their threshold the slot's complexity and that tier's benefit, plus
   one for a unique (gear.accessory_threshold).

    python tools/content/ring_kinds_2026_11.py [--check]
"""
from __future__ import annotations

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))

import jsonfmt  # noqa: E402

PATH = os.path.join(ROOT, 'data', 'items', 'accessory.json')

# The ten kinds: (id, kind, the entry it takes the place of, its own fields).
# Weights are flat through the dungeon: a ring found deep is the same kind,
# stronger (its level comes from the armour bells, not its kind).
KINDS = [
    ('ring_of_protection', 'protection', 'ring_protection_iron', {
        'name': 'ring of protection', 'symbol': '=', 'color': [200, 200, 200],
        'weight': 0.1, 'slot': 'ring', 'min_level': 1, 'weight_by_floor': 12,
        'effects': {},
        'unidentified_name': 'a ring',
        'lore': ("Saint Dunstan was a blacksmith before he was Archbishop of Canterbury. "
                 "The story goes that the Devil came to have a hoof shod, and Dunstan nailed "
                 "the shoe on so painfully that the Devil swore never to enter a door with iron "
                 "over it. Rings like this one trade on that promise: what is aimed at the "
                 "wearer's body may land, but the venom, the spell or the fear it carries often "
                 "does not.")}),
    ('ring_of_spell_turning', 'spell_turning', 'amulet_spell_turning', {
        'name': 'ring of spell turning', 'symbol': '=', 'color': [180, 160, 255],
        'weight': 0.1, 'slot': 'ring', 'min_level': 1, 'weight_by_floor': 8,
        'effects': {},
        'unidentified_name': 'a ring',
        'lore': ("King Balak of Moab hired the seer Balaam to curse Israel and took him up "
                 "three mountains to do it. Three times Balaam opened his mouth and a blessing "
                 "came out, and the curse fell back on the man who paid for it. The spiral cut "
                 "in this ring turns ill words the same way: magic, shadow and the mind's "
                 "blows glance off.")}),
    ('ring_of_regeneration', 'regeneration', 'ring_of_regeneration', {
        'name': 'ring of regeneration', 'min_level': 1, 'weight_by_floor': 8,
        'effects': {'status': 'regenerating', 'duration': -1}}),
    ('ring_of_invisibility', 'invisibility', 'ring_invisible', {
        'name': 'ring of invisibility', 'min_level': 8, 'weight_by_floor': 4,
        'effects': {}, 'unidentified_name': 'a ring'}),
    ('ring_of_sustenance', 'sustenance', 'ring_sustenance_amber', {
        'name': 'ring of sustenance', 'min_level': 1, 'weight_by_floor': 8,
        'effects': {'status': 'sustained', 'duration': -1}, 'unidentified_name': 'a ring'}),
    ('ring_of_wizardry', 'wizardry', None, {
        'name': 'ring of wizardry', 'symbol': '=', 'color': [150, 120, 230],
        'weight': 0.1, 'slot': 'ring', 'min_level': 1, 'weight_by_floor': 8,
        'effects': {},
        'unidentified_name': 'a ring',
        'lore': ("The Greek Magical Papyri, found in a single cache at Thebes, are working "
                 "books: recipes for summoning, binding and foretelling, with notes in the "
                 "margins where a spell went wrong. Their writers wanted what every working "
                 "magician wants, a spell that costs less than the last one. This ring was cut "
                 "to that wish.")}),
    ('amulet_life_saving', 'life_saving', 'amulet_life_saving', {
        'name': 'amulet of life saving', 'min_level': 35, 'weight_by_floor': 4,
        'effects': {'status': 'life_save', 'duration': -1}}),
    ('amulet_of_wisdom', 'wisdom', 'amulet_of_wisdom', {
        'name': 'amulet of wisdom', 'min_level': 1, 'weight_by_floor': 8, 'effects': {}}),
    ('amulet_of_intellect', 'intellect', 'amulet_of_intellect', {
        'name': 'amulet of intellect', 'min_level': 1, 'weight_by_floor': 8, 'effects': {}}),
    ('amulet_of_constitution', 'constitution', 'amulet_of_constitution', {
        'name': 'amulet of constitution', 'min_level': 1, 'weight_by_floor': 8, 'effects': {}}),
]

# Common entries that leave: their power moved to armour (enchantments.json),
# was folded into a kind, or was an AC ring.
REMOVED = [
    'ring_magic_res_a', 'ring_drain_res_a', 'ring_levitate', 'ring_hasted', 'ring_clairvoy',
    'ring_displace', 'amulet_regen_jade', 'amulet_hasted', 'amulet_invis', 'amulet_levitate',
    'amulet_clairvoyant', 'amulet_displace', 'amulet_fire_res', 'amulet_cold_res',
    'amulet_shock_res', 'amulet_poison_res', 'amulet_sleep_res', 'amulet_magic_res',
    'amulet_drain_res', 'ring_protection_silver', 'ring_protection_gold',
    'ring_protection_adamantine', 'ring_speed_quicksilver', 'ring_strength_dragonbone',
    'ring_constitution_diamond', 'ring_intellect_prismatic_deep', 'amulet_truesight',
    'amulet_reflection', 'amulet_titan_constitution', 'amulet_archmage_intellect',
    'ring_of_warning', 'ring_of_searching', 'ring_of_telepathy', 'ring_of_fire_resist',
    'ring_of_cold_resist', 'ring_of_shock_resist', 'ring_of_poison_resist',
    'ring_of_sleep_resist', 'amulet_of_warning', 'amulet_of_searching', 'amulet_of_telepathy',
    'amulet_of_strength', 'amulet_of_greater_strength', 'amulet_of_greater_constitution',
    'amulet_of_dexterity', 'amulet_of_greater_dexterity', 'amulet_of_greater_intellect',
    'amulet_of_greater_wisdom', 'amulet_of_perception', 'amulet_of_greater_perception',
] + [f'ring_of_{p}{w}' for w in ('strength', 'constitution', 'dexterity', 'intellect',
                                    'wisdom', 'perception')
     for p in ('', 'greater_', 'master_')]

CURSED = ['ring_curse_teleport', 'ring_curse_aggravate', 'ring_curse_fumble',
          'ring_curse_slow', 'ring_curse_drain', 'amulet_curse_teleport',
          'amulet_curse_slow', 'amulet_curse_drain']
CURSED_WEIGHT = 2


def _kind_entry(old: dict | None, kind: str, fields: dict) -> dict:
    import gear
    e = dict(old or {})
    for k in ('value', 'tier', 'peak_floor', 'peak_weight', 'spread', 'floorSpawnWeight',
              'identified', 'floor_spawn_weight'):
        e.pop(k, None)
    w = fields.pop('weight_by_floor')
    e.update(fields)
    slot = e['slot']
    e['kind'] = kind
    # A kind is made at a level when it is found (rings.dress); these are
    # its level-1 figures, for anything that reads the template itself.
    e['equip_threshold'] = gear.accessory_threshold(slot, 1)
    e['quiz_tier'] = 1
    e['is_unique'] = False
    e['peak_floor'] = 0
    e['peak_weight'] = 0.0
    e['floorSpawnWeight'] = {'1-100': w}
    return e


def commons(d: dict) -> dict:
    kinds = {kid: (kind, src, dict(f)) for kid, kind, src, f in KINDS}
    at = {src: kid for kid, (kind, src, f) in kinds.items() if src}
    out, done = {}, set()
    for k, v in d.items():
        if k in kinds and k not in done:
            kind, src, f = kinds[k]
            out[k] = _kind_entry(v if (src == k or src not in d) else d[src], kind, f)
            done.add(k)
        elif k in at and at[k] not in done:
            kid = at[k]
            kind, src, f = kinds[kid]
            out[kid] = _kind_entry(v, kind, f)
            done.add(kid)
        elif k in REMOVED or k in at:
            continue
        elif k in CURSED:
            v = dict(v)
            v['floorSpawnWeight'] = {'1-100': CURSED_WEIGHT}
            v['peak_floor'], v['peak_weight'] = 0, 0.0
            out[k] = v
        else:
            out[k] = v
    for kid, (kind, src, f) in kinds.items():
        if kid not in done:
            out[kid] = _kind_entry(None, kind, f)
    return out


# --------------------------------------------------------------- uniques

def _power_tier(e: dict) -> int:
    fx = e.get('effects') or {}
    amt = 0
    for sk, ak in (('stat', 'amount'), ('stat2', 'amount2')):
        if fx.get(sk):
            amt = max(amt, abs(int(fx.get(ak, 0) or 0)))
    return max(1, min(5, amt))


def _depth_tier(e: dict) -> int:
    """The tier a common piece found where this item is found would most
    often have (the level bells at its peak floor)."""
    import gear
    pf = int(e.get('peak_floor', 0) or 0)
    if pf <= 0 or pf >= 999:
        return 1
    w = gear.level_weights(pf)
    lv = max(range(1, gear.MAX_LEVEL + 1), key=lambda L: w[L - 1])
    return gear.tier_for_level(lv)


def uniques(d: dict, review: dict) -> dict:
    import gear
    for k, e in d.items():
        named = e.get('is_unique') or e.get('plot_locked') or k in review or k in NAMED_COMMONS
        if not named or e.get('slot') == 'none' or e.get('kind'):
            continue
        r = review.get(k) or {}
        fx = dict(e.get('effects') or {})
        for p in list(r.get('strip') or ()) + ['AC']:      # no ring or amulet gives AC
            _strip(e, fx, p)
        rep = r.get('replace') or {}
        if rep.get('effects'):
            fx.update(rep['effects'])
        for f, v in rep.items():
            if f not in ('effects', 'lore_end'):
                e[f] = v
        if 'status' not in fx:
            fx.pop('duration', None)
        e['effects'] = fx
        if rep.get('lore_end') and not e.get('lore', '').endswith(rep['lore_end']):
            e['lore'] = e['lore'].rsplit('. ', 1)[0] + '. ' + rep['lore_end']
        e.pop('lore_end', None)
        authored = int(e.get('tier', 0) or 0)
        # A unique outranks the commons of its depth by a tier, and is never
        # under its own stat (a +4 is tier IV); a plot gift keeps its own.
        depth = _depth_tier(e) + 1 if int(e.get('peak_floor', 0) or 0) > 0 else 1
        t = max(depth, _power_tier(e), authored if e.get('plot_locked') else 0)
        t = max(1, min(5, t))
        e['quiz_tier'] = t
        if 'tier' in e or e.get('plot_locked'):
            e['tier'] = t
        e['equip_threshold'] = gear.accessory_threshold(
            e.get('slot', 'ring'), gear.level_for_tier(t), unique=True)
    return d


_STAT_POWERS = ('STR', 'DEX', 'PER', 'AC')
# Named pieces found as rare loot (not flagged unique): reviewed as uniques.
NAMED_COMMONS = ('ouroboros_pendant', 'ankh_of_ra')


def _strip(e: dict, fx: dict, p: str) -> None:
    if p in _STAT_POWERS:
        for sk, ak in (('stat', 'amount'), ('stat2', 'amount2')):
            if fx.get(sk) == p:
                fx.pop(sk, None)
                fx.pop(ak, None)
        if fx.get('stat2') and not fx.get('stat'):
            fx['stat'], fx['amount'] = fx.pop('stat2'), fx.pop('amount2', 0)
        if p == 'AC':
            e.pop('ac_bonus', None)
            e.pop('surrounded_ac_bonus', None)
        _strip_tiers(e, p)
        return
    if fx.get('status') == p:
        fx.pop('status', None)
        if not any(x in fx for x in ('stat', 'stat2')):
            fx.pop('duration', None)
    if e.get('on_equip_status') == p:
        e.pop('on_equip_status', None)
    _strip_tiers(e, p)


_RESIST_KEYS = {'fire_resist': 'resistance_fire', 'cold_resist': 'resistance_cold',
                'shock_resist': 'resistance_lightning', 'poison_resist': 'resistance_poison'}


def _strip_tiers(e: dict, p: str) -> None:
    """A chain-equip item's tier ladder loses the power too (Gawain's haste,
    Kavacha's fire, Solomon's telepathy)."""
    for tb in (e.get('tier_bonuses') or {}).values():
        if not isinstance(tb, dict):
            continue
        for key in (f'status_{p}', f'stat_bonus_{p}', _RESIST_KEYS.get(p, '')):
            tb.pop(key, None)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='report only; exit 1 if it would change')
    a = ap.parse_args(argv)
    d, fmt = jsonfmt.load(PATH)
    new = uniques(commons(d), UNIQUE_REVIEW)
    if a.check:
        return 0 if new == d else 1
    jsonfmt.save(PATH, new, fmt)
    n_k = sum(1 for v in new.values() if v.get('kind'))
    print(f"accessory.json: {len(d)} -> {len(new)} entries; {n_k} kinds")
    return 0


# The named rings and amulets (review 2026-11-07, every one of the 79 read
# against its lore): a moved power is stripped unless the lore makes it the
# item's own; four get a replacement (AC, or nothing left). Items not listed
# had no moved power. 'keep' records the lore calls the other way.
UNIQUE_REVIEW: dict = {
    'dragonslayer_ring': {"keep": ["fire_resist"], "strip": ["STR"], "why": "The lore is the stand in the dragon's fire (Wiglaf alone stood in the fire; a scorched ring that remembers who stayed), so fire resistance is its own. Nothing in the lore gives the ring strength; it keeps the dragon chain bonus."},
    'shadow_walker_ring': {"keep": ["poison_resist"], "strip": ["DEX"], "why": "The lore says it outright: 'The wearer's blood stops noticing poison' (venom glands, nightshade). The DEX is a generic thief's bump that the lore never names."},
    'ring_of_the_nibelung': {"strip": ["STR"], "why": "Andvari's cursed ring is about gold and the death of every owner (Volsunga saga); nothing gives it strength. It keeps gold_multiplier and its curse."},
    'andvaranaut': {"strip": ["PER", "searching"], "why": "Its lore is the ring that makes wealth grow again; nothing in it finds hidden doors or sharpens the eye. It keeps gold_multiplier and can_be_cursed."},
    'draupnir': {"strip": ["STR"], "why": "Draupnir drips eight rings every ninth night: its power is gold, which gold_multiplier carries. No source gives it strength. The effects block becomes empty ({})."},
    'ring_of_eluned': {"strip": ["DEX"], "why": "Luned's ring in the Lady of the Fountain does one thing, hides Owain; invisibility and the low-HP veil stay. The DEX has no tie."},
    'talisman_of_troy': {"strip": ["AC"], "replace": {"save_bonus": {"cat": "all", "amount": 2}}, "why": "AC always goes (both effects stat2 'AC' 2 and ac_bonus 2). Troy could not be taken while the Palladium was inside its walls, so a flat saving throw against every rider is the ward that fits. It keeps reflecting and WIS 2, the same shape as the Hand of Fatima."},
    'eye_of_horus': {"keep": ["PER"], "why": "The wedjat is an eye, the falcon god's sound eye, painted on coffins and on boat prows so the dead and the boat could see their way. Sight is its own. It keeps passive_regen."},
    'torque_of_lugh': {"strip": ["STR"], "why": "Lugh won his seat at Tara as master of every art at once (smith, champion, harper, poet, physician); the all-round save and the extra attack chain carry that. A plain strength bump is not his."},
    'ring_of_gawain': {"keep": ["STR"], "strip": ["hasted"], "why": "Malory's Gawain gains strength from nine until noon, the might of three men, so STR is his own, with the three_oclock surge. Nothing makes Gawain swift. Strip hasted from effects and status_hasted from tier_bonuses 3, 4 and 5; the ladder keeps STR, the chain-cap bonus and three_oclock."},
    'ring_of_odysseus': {"keep": ["PER", "searching"], "why": "The lore is that Odysseus came home because he noticed things (PER), and 'Nothing hidden stays hidden from this ring for long' (searching). Both are named."},
    'ring_of_pythia': {"strip": ["PER"], "why": "The Pythia's gift is prophecy, which clairvoyant and the cheaper identifying carry; keen eyes are not part of it."},
    'anklet_of_atalanta': {"keep": ["DEX"], "why": "Atalanta could outrun any man alive; her fleetness is the anklet's whole story, and DEX (dodge) with the free moves is how the game tells it. Keep DEX in effects and in every tier."},
    'crown_of_croesus': {"strip": ["searching"], "why": "Croesus's story is wealth and a misread oracle; nothing in it uncovers hidden things. INT stays."},
    'collar_of_njord': {"strip": ["warning"], "why": "The lore is Njord's sea and his marriage to Skadi; no foreknowledge of danger is told of him. CON stays."},
    'ring_of_lancelot': {"strip": ["STR", "hasted"], "replace": {"effects": {"stat": "CON", "amount": 4, "status": "magic_resist", "duration": -1}}, "why": "Neither strength nor speed is in the lore (the Lady of the Lake, his name under the slab at Dolorous Gard), so both go and nothing is left. In the Vulgate the Lady of the Lake gave Lancelot a ring that breaks enchantments, and he ended the enchantments of Dolorous Gard: magic_resist, with CON 4 for the knight who outlasted every wound, the same size as Percival's ring. The lore could add a line on her ring."},
    'philosophers_ring_legendary': {"strip": ["Truesight"], "why": "Socrates' daimonion was a voice that stopped him before a wrong act. It never showed him the invisible, so Truesight goes. WIS 3 stays, which leaves it at or below the plain Philosopher's Ring (WIS 3, INT 1); the tier pass can weigh that."},
    'amulet_of_pythagoras': {"strip": ["searching"], "why": "The tetractys, the musical ratios and Hippasus are about number, not finding hidden doors. INT stays."},
    'ring_of_hypatia': {"strip": ["Truesight"], "why": "Hypatia was a mathematician and astronomer; nothing in her story sees the invisible. INT and the once-a-floor mob shield stay. Note: protected_when_surrounded is not an AC field, but it grants the 'shielded' status (+2 AC, half physical damage, 3 turns). Kept as a timed status proc; if 'no AC' is to cover granted statuses too, swap it for reflecting."},
    'ring_of_thunder': {"keep": ["shock_resist"], "why": "A thunderstone was kept under the eaves because lightning does not strike the same place twice. Warding off lightning is the whole lore. INT stays."},
    'amulet_of_the_titan': {"keep": ["STR"], "why": "Ore from the bottom of Tartarus that 'makes its wearer equal to the weight': that is strength, and STR is carry capacity in the game. CON 1 stays."},
    'ring_of_the_deep': {"keep": ["cold_resist"], "why": "Scyllias's ring: 'its wearer does not feel the cold', named in the lore. CON stays."},
    'ring_of_the_assassin': {"strip": ["DEX"], "why": "Alamut's signet 'walks very quietly', which passive_silent_walk carries. A dexterity bump is not in the lore."},
    'ring_of_far_sight': {"keep": ["PER", "warning"], "why": "Lynceus, the Argo's lookout, could see through an oak and spotted two men hiding in a hollow tree: keen sight (PER), and the lookout's job of seeing what is coming before it strikes (warning)."},
    'amulet_of_the_archmage': {"keep": ["fire_resist"], "why": "Cast from the bronze of the sandal Etna threw back from Empedocles: 'Fire has already had its turn with it.' INT stays."},
    'ring_of_displacement': {"keep": ["DEX", "displacement"], "why": "Fata Morgana's air: 'Its wearer is quick on his feet and never quite where he appears to be'. The lore names both the quickness (DEX) and the displacement."},
    'sailors_amulet': {"keep": ["cold_resist"], "strip": ["PER"], "why": "'Does not mind the cold' is named, so cold resistance stays. 'Feels trouble coming the way a sailor feels weather' describes a sense for danger (the helm's Alertness), not keener eyes. PER is sight radius, so it goes."},
    'ring_of_iron_grip': {"keep": ["STR"], "why": "Beaten from the armour of Ravana, who tried to tear Mount Kailash out of the ground: 'Its grip does not loosen.' Strength is the lore."},
    'obsidian_talisman': {"keep": ["dark_vision"], "why": "A shard of the Hero Twins' trial-houses (the Dark House first among them): 'Darkness does not hide much from its wearer.' Dark vision is its only power and is named."},
    'ariadnes_thread': {"strip": ["searching"], "why": "The thread remembers the way it has run ('not forgotten a single turning'). It does not uncover hidden doors or traps, and its real power is the quest code that lays out the Labyrinth route and holds Asterion. WIS 2 stays."},
    'eponas_charm': {"keep": ["searching"], "strip": ["PER"], "why": "Epona 'keeps a traveller off the bad road and out of the blind alley': steering clear of traps and finding the way out of dead ends is what Searching does. The PER bump is not in the lore."},
    'rope_of_izanagi': {"keep": ["searching"], "why": "The boundary rope of Yomi 'hums near anything hidden', so searching is named. CON stays."},
    'silverlight_pendant': {"strip": ["PER"], "why": "Elara's pendant is a keepsake, a child's name on the back; nothing ties it to sight. WIS 2 stays."},
    'officers_signet': {"keep": ["STR", "DEX"], "why": "The lore names both: 'It makes the hand that wears it stronger and surer.' A commander's ring that steadies the hand."},
    'prophets_amulet': {"strip": ["PER"], "why": "What the prophet saw was foresight (the Destroyer, the Seals), not keener eyes; the 'clarity' is of the mind and WIS carries it. Same call as the Ring of the Oracle."},
    'lyre_of_orpheus': {"keep": ["sleep_resist"], "why": "Orpheus sang Cerberus to sleep, and 'no spell of sleep can close the eyes of anyone who hears it'. Sleep resistance is named, and it is the lyre's only status."},
    'scales_of_maat': {"strip": ["PER"], "why": "Ma'at's scales 'help their wearer weigh things as they are'. That is judgement (WIS, which stays), not eyesight."},
    'torc_of_boudicca': {"strip": ["STR", "AC"], "replace": {"effects": {"stat": "CON", "amount": 3}, "save_bonus": {"cat": "WIS", "amount": 2}, "lore_end": "The torc lends its wearer her temper: a body that will not break and a mind that will not bend, however many crowd in."}, "why": "AC always goes (surrounded_ac_bonus 2), and the lore gives Boudicca her temper, not strength, so nothing is left. Flogged by Rome and still rising: CON 3 for STR 3. Her temper becomes a will no fear, charm or confusion can bend: a WIS save of +2 for the AC-when-mobbed. The lore's last sentence ('the harder they are to hit') must be rewritten to match."},
    'rands_heart': {"keep": ["warning"], "why": "The lore is Rand's promise: he could not always be at Robyn's side, so he swore to protect her always. The locket keeps his watch while he is away (warning) and keeps the promise at the last (the death ward). Both are that promise."},
    'jade_cicada': {"strip": ["poison_resist"], "why": "Han mourners laid the jade cicada on the tongue for rebirth, and its lore power is the crack that holds against a killing blow (death_save). Poison plays no part in it."},
    'megingjord': {"keep": ["STR"], "strip": ["hasted"], "why": "Snorri's belt doubles Thor's strength, so STR stays. Thor is never told as swift (he wades the rivers while the others ride), so hasted goes."},
    'kavacha_kundala': {"strip": ["fire_resist"], "why": "Surya's armour made Karna proof against weapons, and first_hit_absorb and the death save carry that. No telling makes it proof against fire, so fire resistance goes: effects status fire_resist, status_fire_resist in tiers 1-5 and resistance_fire in tiers 3-5. CON, suryas_gift, first_hit_absorb and the death save stay; every tier stays non-empty."},
    'hand_of_glory': {"keep": ["dark_vision"], "strip": ["PER"], "why": "Its fingers burn as candles in a sleeping house, a light (in the old tales seen only by its holder) for the thief to work by, so passive_dark_vision stays. The PER -1 is a malus with no lore tie, and rings and amulets no longer touch PER; its drawback stays the curse when the last finger burns."},
    'ring_of_solomons_authority': {"strip": ["telepathy"], "why": "Solomon's ring commands demons and djinn (Asmodeus at the Temple). pacify_demon and weaken_summoned carry that; it is not told as reading minds. Strip telepathy from effects and status_telepathy from tiers 4 and 5. WIS/INT, detect_magic and the Solomonic key stay."},
    'amulet_of_hippolyta': {"strip": ["STR"], "replace": {"effects": {"stat": "CON", "amount": 3}}, "why": "In the Greek sources Ares's war-belt is the sign of Hippolyta's rule, not a source of strength (that is a modern comic-book addition), so STR goes and nothing is left. The war god's belt girds his warrior daughter's body: CON 3, the same size."},
    'azaraels_brand': {"keep": ["STR"], "why": "'The strength in it is real': Azarael pays his debt in strength, so STR is named."},
}


if __name__ == '__main__':
    sys.exit(main())
