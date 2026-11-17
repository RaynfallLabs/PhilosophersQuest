"""Armour you choose, not just wear: the protection pass (2026-11-13).

Winning-build plan 3.3, slice 4 (decision 3, approved by Brandon: "Ensure
that kit armor defenses are IMPORTANT beyond AC; materials can change weight
and resistances, block certain monster attacks and status effects... there
should be a REAL choice to kit and armor, not just what has the best AC").
It reverses the 3.3.2 rule that the material "gives the weight and the wear,
never protection". Every gift carries a price, so no material simply wins.

What this writes (src/gear.py reads it, section "What armour does beyond
AC"):

- the body-armour templates (and the tower shield) get the physical FORMS
  their build turns or lets through, data/templates/armor/*.json and
  shields/*.json: `forms` {slash|pierce|blunt: multiplier}, `forms_words`
  (the card's words for each) and `forms_note` (the lore);
- the 45 armour materials get the ELEMENTS and specials, replacing the
  `resistances` / `weaknesses` lists nothing read for damage
  (data/materials/armor/*.json): `protection` {damage type: multiplier},
  `protection_words`, `metal` (clanks and taxes a spell), and where the lore
  says so `quiet` (no clank), `casting_free` (no spell tax) and `wards`
  (riders it stops: data/gear_rules.json `wards`); `protection_note` says
  why, `protection_price` what it costs;
- the named body armours (data/items/armor.json) get `metal`, by their lore.
  A named piece keeps its own `damage_resistances`: its JSON wins.

The material's elements apply to BODY armour only (a whole kit of leather
would otherwise take the fire x1.25 eight times); a shield is held, not
worn, so its material gives its weight and its wear and nothing more.

Formats are kept (jsonfmt, or the inline-list style of most material files).
Idempotent: a second run changes nothing.

    py tools/content/armour_profiles_2026_11.py [--check]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jsonfmt  # noqa: E402

TEMPLATES = os.path.join(ROOT, 'data', 'templates')
MATERIALS = os.path.join(ROOT, 'data', 'materials', 'armor')
NAMED = os.path.join(ROOT, 'data', 'items', 'armor.json')

# ---------------------------------------------------------------- templates
# (forms, words, note). The plan's table (section 3.3).
_PLATE = ({'slash': 0.75, 'pierce': 0.85},
          {'slash': 'turns an edge', 'pierce': 'skids a point aside'},
          "A plate turns an edge and skids a point aside; a hammer still rings it.")
_MAIL = ({'slash': 0.75, 'pierce': 1.15},
         {'slash': 'turns an edge', 'pierce': 'parts under a point'},
         "Rings stop a cut but part under a point: a spear or a bodkin arrow finds the gaps.")
_SCALE = ({'slash': 0.8, 'pierce': 0.9},
          {'slash': 'sheds a cut', 'pierce': 'turns most points'},
          "Overlapping metal sheds a cut and turns most points; a hammer still bruises through.")
_LEATHER = ({'slash': 0.9, 'blunt': 0.85},
            {'slash': 'slows an edge', 'blunt': 'takes the sting from a blow'},
            "Thick leather slows an edge and takes the sting from a blow; a point goes straight in.")
FORMS = {
    ('armor', 'padded'): ({'slash': 0.9, 'blunt': 0.75},
                          {'slash': 'dulls a cut', 'blunt': 'soaks a blow'},
                          "Quilted layers soak a club the way a mattress takes a punch, and dull an edge a little."),
    ('armor', 'leather'): _LEATHER,
    ('armor', 'studded_leather'): (_LEATHER[0], _LEATHER[1],
                                   "Leather set with rivets: it slows an edge and takes the sting from a blow."),
    ('armor', 'hide'): (_LEATHER[0], {'slash': 'slows an edge', 'blunt': 'blunts a blow'},
                        "A beast's hide, hair and all, slows an edge and blunts a blow."),
    ('armor', 'chain_shirt'): _MAIL,
    ('armor', 'ringmail'): (_MAIL[0], _MAIL[1],
                            "Iron rings sewn on leather stop a cut but part under a point."),
    ('armor', 'chainmail'): _MAIL,
    ('armor', 'scale'): _SCALE,
    ('armor', 'banded'): (_SCALE[0], _SCALE[1],
                          "Bands of metal laced over mail shed a cut and turn most points."),
    ('armor', 'splint'): (_SCALE[0], _SCALE[1],
                          "Strips of metal riveted on leather shed a cut and turn most points."),
    ('armor', 'breastplate'): (_PLATE[0], _PLATE[1],
                               "The curve of the chest plate turns an edge and skids a point aside; a hammer still rings it."),
    ('armor', 'plate'): _PLATE,
    ('armor', 'full_plate'): _PLATE,
    # A shield is held, so only the one that is a wall gets a form.
    ('shields', 'tower_shield'): ({'pierce': 0.9}, {'pierce': 'a wall to hide behind'},
                                  "A shield as tall as a man: the Roman tortoise walked under a hail of arrows."),
}

# ---------------------------------------------------------------- materials
# id -> dict(p=protection, w=words, metal, quiet, casting_free, wards, note, price).
_FIRE = {'fire': 'catches fire'}
_SPARK = {'lightning': 'conducts lightning'}
_SCORCH = "Catches fire, and fire scorches it."
_WOOD_NOTE = "A shield's {name}: held, not worn, so it guards with its AC alone."
_WOOD_PRICE = "Wood burns: fire scorches it."

MATS = {
    # --- cloth: light and quiet; it burns (plan: cloth and leather fire x1.25)
    'linen': dict(p={'fire': 1.25}, w=_FIRE, note="Linen is cool and light, and it goes up like a wick.",
                  price=_SCORCH),
    'canvas': dict(p={'fire': 1.25}, w=_FIRE, note="Canvas is sailcloth: tough, light and cheap.",
                   price=_SCORCH),
    'silk': dict(p={'pierce': 0.9, 'fire': 1.25},
                 w={'pierce': 'catches an arrowhead', **_FIRE},
                 note="Silk does not part under an arrowhead: it wraps the point and draws out clean, which is why the Mongol riders wore it under their coats.",
                 price=_SCORCH),
    'spider_silk': dict(p={'pierce': 0.85, 'fire': 1.25},
                        w={'pierce': 'grips a point', **_FIRE},
                        note="Spider silk is stronger than steel for its weight and grips a point before it bites.",
                        price=_SCORCH),
    'elven_silk': dict(p={'slash': 0.9, 'pierce': 0.9, 'fire': 1.25},
                       w={'slash': 'slows an edge', 'pierce': 'catches a point', **_FIRE},
                       note="Woven in the golden wood, light as a leaf: it slows an edge and catches a point.",
                       price=_SCORCH),
    # --- leather
    'leather': dict(p={'fire': 1.25}, w=_FIRE,
                    note="Plain oiled leather: cheap, quiet and kind to a nimble wearer.", price=_SCORCH),
    'rawhide': dict(p={'fire': 1.25}, w=_FIRE,
                    note="Untanned hide dried hard: what you can get on the first floors.", price=_SCORCH),
    'cured_leather_armor': dict(p={'fire': 1.25}, w=_FIRE,
                                note="Smoke-cured leather, lighter than plain.", price=_SCORCH),
    'boiled_leather_armor': dict(p={'slash': 0.9, 'fire': 1.25},
                                 w={'slash': 'boiled hard against an edge', **_FIRE},
                                 note="Cuir bouilli: leather boiled in wax and shaped hard, so an edge skids on it.",
                                 price=_SCORCH),
    'drakeskin_armor': dict(p={'fire': 0.85, 'cold': 0.9, 'acid': 1.15},
                            w={'fire': 'sheds flame', 'cold': 'keeps out the cold', 'acid': 'acid eats a hide'},
                            note="A lesser drake's skin keeps some of its owner's scorn for fire and frost.",
                            price="Acid eats a hide."),
    'dragonhide_armor': dict(p={'fire': 0.7, 'cold': 1.15},
                             w={'fire': 'sheds flame', 'cold': 'stiffens in the cold'},
                             wards=['flame'],
                             note="A true dragon's hide, tanned: flame runs off it and it will not catch.",
                             price="It stiffens in the cold, as a dragon slows in winter."),
    'studded_leather': dict(p={'fire': 1.25}, w=_FIRE,
                            note="Leather set with rivets, a little more for an edge to catch on.",
                            price=_SCORCH),
    'hide': dict(p={'cold': 0.85, 'fire': 1.25}, w={'cold': 'keeps out the cold', **_FIRE},
                 note="A beast's pelt with the hair on: warm, coarse and quick to singe.", price=_SCORCH),
    # --- iron and steel: metal conducts (lightning x1.25) and iron rusts
    'ring_iron': dict(p={'lightning': 1.25}, w=_SPARK, metal=True, wards=['fey_glamour'],
                      note="Plain wrought iron, the cold iron of the old stories: the fair folk will not touch it.",
                      price="It conducts lightning, and it rusts."),
    'chain_steel': dict(p={'slash': 0.95, 'lightning': 1.25},
                        w={'slash': 'good steel holds against an edge', **_SPARK}, metal=True,
                        note="Good steel rings, and is a little harder to cut than iron.",
                        price="It conducts lightning, and it rusts."),
    'tempered_bronze': dict(p={'lightning': 1.25}, w=_SPARK, metal=True,
                            note="Bronze, the heroes' metal of the old songs: it never rusts.",
                            price="It conducts lightning."),
    'damascus_steel': dict(p={'slash': 0.9, 'lightning': 1.25},
                           w={'slash': 'an edge skids along the grain', **_SPARK}, metal=True,
                           note="Pattern-welded steel, folded and folded again.",
                           price="It conducts lightning, and it rusts."),
    'cobalt_steel': dict(p={'cold': 0.75, 'fire': 1.15, 'lightning': 1.25},
                         w={'cold': 'keeps out the cold', 'fire': 'softens in fire', **_SPARK}, metal=True,
                         note="Frost-blue steel forged cold and staying cold: frost cannot bite through it (the plan's frost iron).",
                         price="It softens in fire, conducts lightning, and rusts."),
    'hematite': dict(p={'drain': 0.8, 'necrotic': 0.85, 'blunt': 1.1},
                     w={'drain': 'holds the life in', 'necrotic': 'holds the life in',
                        'blunt': 'cracks under a hammer'}, metal=True,
                     note="Bloodstone: the old surgeons pressed it to a wound to stop the bleeding. It is iron that has already rusted, so it neither rusts nor carries a spark.",
                     price="Stone cracks under a hammer."),
    'mithril': dict(p={'lightning': 1.25}, w=_SPARK, metal=True, quiet=True, casting_free=True,
                    note="Mithril is light as cloth, makes no sound and never tarnishes: an elf can sing a spell in it.",
                    price="It is still metal: it conducts lightning."),
    # --- the magical and exotic metals (deep)
    'adamantine': dict(p={'slash': 0.85, 'pierce': 0.85, 'lightning': 1.25},
                       w={'slash': 'hard to cut', 'pierce': 'hard to pierce', **_SPARK}, metal=True,
                       note="Adamant, the unbreakable: the hardest thing the gods ever forged.",
                       price="It is half as heavy again as steel, and it conducts lightning."),
    'dwarven_plate': dict(p={'blunt': 0.85, 'fire': 0.85, 'lightning': 1.25},
                          w={'blunt': 'takes a hammer', 'fire': 'forged in the deep fire', **_SPARK},
                          metal=True,
                          note="Rune-worked steel from the forges under the mountain: it takes a hammer's ring and the forge's heat.",
                          price="It is heavier than steel, and it conducts lightning."),
    'glassteel': dict(p={'fire': 0.9, 'cold': 0.9, 'lightning': 0.9, 'blunt': 1.2},
                      w={'fire': 'turns the elements', 'cold': 'turns the elements',
                         'lightning': 'turns the elements', 'blunt': 'shatters under a hammer'},
                      metal=True,
                      note="A crystal alloy, clear as ice: fire, frost and lightning slide off it.",
                      price="A hammer cracks it."),
    'godweave_armor': dict(p={'magic': 0.85, 'shadow': 0.85, 'fire': 1.15},
                           w={'magic': 'turns a spell', 'shadow': 'starlight against the dark',
                              'fire': 'thread burns'},
                           metal=False, quiet=True, casting_free=True,
                           note="Woven from starlight thread, not forged: it turns a spell and the dark, and makes no sound.",
                           price="Thread burns, and it is found only at the very bottom of the world."),
    'orichalcum_armor': dict(p={'magic': 0.8, 'lightning': 1.25},
                             w={'magic': 'turns a spell', **_SPARK}, metal=True, casting_free=True,
                             note="Atlantis' red metal, said to hum with magic: a caster can work in it.",
                             price="It conducts lightning, and it is found only near the bottom."),
    'quicksilver_armor': dict(p={'slash': 0.9, 'pierce': 0.9, 'fire': 1.25, 'lightning': 1.25},
                              w={'slash': 'flows round an edge', 'pierce': 'flows round a point',
                                 'fire': 'boils in fire', **_SPARK}, metal=True,
                              note="Living metal that flows like water: an edge or a point slides in and out again.",
                              price="It boils in fire, and it conducts lightning."),
    'shadowiron_armor': dict(p={'shadow': 0.75, 'necrotic': 0.75, 'holy': 1.25, 'lightning': 1.25},
                             w={'shadow': 'drinks the dark', 'necrotic': 'drinks the dark',
                                'holy': 'holy light burns through it', **_SPARK}, metal=True,
                             note="Iron from the void: the dark is at home in it.",
                             price="Holy light burns through it, it conducts lightning, and it can never be blessed."),
    'soulsteel': dict(p={'drain': 0.75, 'necrotic': 0.75, 'lightning': 1.25},
                      w={'drain': 'holds the soul in', 'necrotic': 'holds the soul in', **_SPARK}, metal=True,
                      note="Spirit-forged steel, the plan's silver mail: what would drink your life finds a soul already bound in the metal.",
                      price="It conducts lightning."),
    'starmetal_armor': dict(p={'magic': 0.85, 'shadow': 0.85, 'lightning': 1.25},
                            w={'magic': 'turns a spell', 'shadow': 'glows against the dark', **_SPARK},
                            metal=True,
                            note="Iron that fell from the sky: it glows faintly, and the dark gives it room.",
                            price="It conducts lightning."),
    'sunsteel_armor': dict(p={'fire': 0.75, 'cold': 1.15, 'lightning': 1.25},
                           w={'fire': 'sheds flame', 'cold': 'turns brittle in the cold', **_SPARK},
                           metal=True,
                           note="Steel that keeps the sun's warmth (the plan's volcanic iron): fire is at home in it, frost is not.",
                           price="It turns brittle in the cold, and it conducts lightning."),
    'titanforged_armor': dict(p={'blunt': 0.8, 'lightning': 1.25},
                              w={'blunt': "takes a giant's blow", **_SPARK}, metal=True,
                              note="Forged by the Titans for their own war: it takes a blow that would fell an ox.",
                              price="It is nearly twice as heavy as steel, and it conducts lightning."),
    'tungsten': dict(p={'blunt': 0.85, 'magic': 0.9, 'lightning': 1.25},
                     w={'blunt': 'takes a hammer', 'magic': 'dulls a spell', **_SPARK}, metal=True,
                     note="The densest metal there is: a hammer barely dents it.",
                     price="It is half again as heavy as steel, and it conducts lightning."),
    'primordial_stone_armor': dict(p={'magic': 0.75, 'slash': 0.9, 'pierce': 0.9},
                                   w={'magic': 'older than magic', 'slash': 'stone turns an edge',
                                      'pierce': 'stone turns a point'},
                                   metal=False,
                                   note="Stone from before the world was made: magic is younger than it.",
                                   price="It weighs twice as much as steel."),
    # --- dragon
    'dragonscale': dict(p={'fire': 0.5, 'cold': 1.15},
                        w={'fire': 'fire runs off it', 'cold': 'stiffens in the cold'}, metal=False,
                        wards=['flame'],
                        note="A dragon's scales, still warm: fire runs off them like water and they will not catch.",
                        price="It stiffens in the cold."),
    'petrified_dragon': dict(p={'fire': 0.65, 'blunt': 1.1},
                             w={'fire': 'still remembers the fire', 'blunt': 'cracks under a hammer'},
                             metal=False,
                             note="Dragon scale turned to stone with age: it still remembers the fire.",
                             price="Stone cracks under a hammer, and it is heavier than scale."),
}
# The shield woods and bones: a shield is held, not worn.
for _wid in ('ash', 'oak', 'yew', 'dragonwood', 'ironwood', 'petrified_wood', 'silverbark',
             'leviathan_rib_armor', 'treant_heart_armor', 'worldtree'):
    MATS[_wid] = dict(p={}, w={}, metal=False, note=None, price=None)
# Their old `resistances` lists were read only by the wear rule: a wood that
# would not burn keeps that as a special property (status_effects reads
# `fire_resistant`), so no shield scorches that did not before. Ironwood and
# dragonwood say so already.
MATS['petrified_wood']['sp_add'] = ['fire_resistant']      # stone does not burn
MATS['worldtree']['sp_add'] = ['fire_resistant']           # Yggdrasil outlasts the fire

# Named body armour: is it metal? (its lore; everything else about it is its own)
NAMED_METAL = {
    'hide_of_nemean_lion': False,        # the lion's own hide
    'calydonian_boar_hide': False,       # the boar's own bristled hide (2026-11-17)
    'carapace_of_the_hydra': False,      # a monster's shell
    'panoply_of_hephaestus': True,       # the smith god's bronze and gold
    'dragon_mail_of_sigurd': False,      # dragon's scale, not forged
    'breastplate_of_joan': True,         # "white" harness of plain polished steel
    'lorica_hamata_of_caesar': True,     # the legions' ringed iron mail
    'orichalcum_breastplate': True,      # Atlantis' brass
    'brigandine_of_william_wallace': True,   # steel plates riveted in cloth
    'cuirass_of_hannibal': True,
    'cloth_of_penelope': False,
    'coat_of_cu_chulainn': False,        # a war coat of hide
    'babr_e_bayan': False,               # a tiger skin, worn over the mail
    'linothorax_of_alexander': False,    # layered linen
    'scale_of_dilmun': True,             # "this bronze shirt"
    'haramaki_of_yoshitsune': True,      # lacquered iron lamellae
    'armor_of_ragnarok': True,
    'serpent_scale_mail': False,         # the World Serpent's scales
}


def _inline(d: dict, nl: str, tail: str) -> str:
    t = "{\n" + ",\n".join(f"  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}"
                          for k, v in d.items()) + "\n}" + tail
    return t.replace('\n', nl)


def _read(path):
    """(data, writer): writer(data) -> the file's text in its own style."""
    raw = open(path, 'rb').read().decode('utf-8')
    data = json.loads(raw)
    for nl in ('\r\n', '\n'):
        for tail in ('', '\n'):
            if _inline(data, nl, tail) == raw:
                return data, (lambda d, nl=nl, tail=tail: _inline(d, nl, tail))
    _d, fmt = jsonfmt.load(path)
    indent, ascii_, seps, nl, tail, _bom = fmt

    def write(d):
        text = json.dumps(d, indent=indent, ensure_ascii=ascii_, separators=seps)
        return text.replace('\n', nl) + tail.replace('\n', nl)
    return data, write


def _material_entry(mid: str, old: dict) -> dict:
    spec = MATS[mid]
    out = {}
    for k, v in old.items():
        if k in ('resistances', 'weaknesses', 'protection'):
            # Where the old lists stood (or, on a second run, the profile).
            if 'protection' not in out:
                out.update(_protection_fields(mid, spec, old))
            continue
        if k in _NEW_MAT_KEYS:
            continue
        if k == 'special_properties' and spec.get('sp_add'):
            v = list(v) + [s for s in spec['sp_add'] if s not in v]
        out[k] = v
    if 'protection' not in out:
        out.update(_protection_fields(mid, spec, old))
    return out


_NEW_MAT_KEYS = ('protection', 'protection_words', 'metal', 'quiet', 'casting_free', 'wards',
                 'protection_note', 'protection_price')


def _protection_fields(mid, spec, old) -> dict:
    metal = spec.get('metal')
    if metal is None:
        metal = old.get('material_class') in ('metal', 'rare_metal', 'magical_metal', 'exotic_metal')
    f = {'protection': dict(spec['p']), 'protection_words': dict(spec['w']), 'metal': bool(metal)}
    for flag in ('quiet', 'casting_free'):
        if spec.get(flag):
            f[flag] = True
    if spec.get('wards'):
        f['wards'] = list(spec['wards'])
    note = spec.get('note') or _WOOD_NOTE.format(name=old.get('name', mid))
    price = spec.get('price') or _WOOD_PRICE
    f['protection_note'] = note
    f['protection_price'] = price
    return f


def plan() -> list:
    """[(path, new text)] for every file whose text this pass changes."""
    out = []
    for (cat, tid), (forms, words, note) in FORMS.items():
        path = os.path.join(TEMPLATES, cat, f'{tid}.json')
        data, write = _read(path)
        new = {k: v for k, v in data.items() if k not in ('forms', 'forms_words', 'forms_note')}
        new['forms'] = dict(forms)
        new['forms_words'] = dict(words)
        new['forms_note'] = note
        text = write(new)
        if text != open(path, 'rb').read().decode('utf-8'):
            out.append((path, text))
    for fn in sorted(os.listdir(MATERIALS)):
        if not fn.endswith('.json'):
            continue
        path = os.path.join(MATERIALS, fn)
        data, write = _read(path)
        mid = data.get('id') or fn[:-5]
        if mid not in MATS:
            raise SystemExit(f"no protection written for armour material {mid}")
        text = write(_material_entry(mid, data))
        if text != open(path, 'rb').read().decode('utf-8'):
            out.append((path, text))
    data, write = _read(NAMED)
    for iid, metal in NAMED_METAL.items():
        e = data[iid]
        assert e.get('slot') == 'body', iid
        e['metal'] = bool(metal)
    missing = [k for k, v in data.items() if isinstance(v, dict) and v.get('slot') == 'body'
               and k not in NAMED_METAL]
    if missing:
        raise SystemExit(f"named body armour with no metal decision: {missing}")
    text = write(data)
    if text != open(NAMED, 'rb').read().decode('utf-8'):
        out.append((NAMED, text))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='report what would change, write nothing')
    args = ap.parse_args()
    changes = plan()
    for path, text in changes:
        rel = os.path.relpath(path, ROOT)
        if args.check:
            print(f"would write {rel}")
        else:
            with open(path, 'wb') as f:
                f.write(text.encode('utf-8'))
            print(f"wrote {rel}")
    if not changes:
        print("nothing to change")
    return 1 if (args.check and changes) else 0


if __name__ == '__main__':
    sys.exit(main())
