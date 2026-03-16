"""
Comprehensive item overhaul:
- Adds new weapon classes: mace, warhammer, morningstar, flail, rapier, scimitar, zweihander
- Adds named historical weapon variants
- Adds more armor items per slot/tier
- Fixes accessory min_level values and adds floorSpawnWeight tables
"""

import json, copy

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def spawn(t1, t2, t3, t4, t5):
    """Return a standard floorSpawnWeight table across 5 tier bands."""
    return {"1-20": t1, "21-40": t2, "41-60": t3, "61-80": t4, "81-100": t5}

def chain_mults(n=6):
    return [1.0, 2.0, 4.0, 6.0, 8.0, 10.0][:n]

# ─── BASE WEAPON TEMPLATE ─────────────────────────────────────────────────────

def weapon(id_, name, cls, mat, tier, dmg, min_lvl, dmg_types, two_handed=False,
           stun=0.0, bleed=0.0, knockback=False, ignore_shield=False, crit_mult=1.0,
           reach=1, requires_ammo=None, unid_name=None, lore="", value=None,
           spawn_w=None, quiz_tier=None, color=None, variant=None):
    """Return a single weapon definition dict."""
    if value is None:
        value = tier * 60 + dmg * 5
    if spawn_w is None:
        # Sparse at low levels for high-tier, fades at high for low-tier
        bands = [0]*5
        bands[tier-1] = 100
        if tier > 1: bands[tier-2] = 30
        if tier < 5: bands[tier] = 20
        spawn_w = {f"{i*20+1}-{i*20+20}": bands[i] for i in range(5)}
    if quiz_tier is None:
        quiz_tier = tier
    if color is None:
        palettes = {
            "iron":         [200, 210, 230],
            "bronze":       [205, 160, 90],
            "steel":        [160, 185, 215],
            "hardened gold":[220, 190, 60],
            "diamond":      [180, 240, 255],
            "adamantine":   [90,  60, 180],
            "wood":         [160, 120, 80],
            "hardwood":     [130, 95, 60],
            "ironwood":     [100, 75, 50],
            "dragonbone":   [210, 200, 180],
            "mithril":      [160, 200, 255],
            "obsidian":     [60,  40, 90],
            "bone":         [220, 215, 195],
            "stone":        [150, 145, 140],
        }
        color = palettes.get(mat, [180, 180, 180])
    if unid_name is None:
        unid_name = f"a {mat} {cls}"
    if variant is None:
        variant = "2h" if two_handed else "1h"

    d = {
        "name": name,
        "class": cls,
        "variant": variant,
        "tier": tier,
        "material": mat,
        "mathTier": quiz_tier,
        "baseDamage": dmg,
        "chainMultipliers": chain_mults(),
        "maxChainLength": 6,
        "damageTypes": dmg_types,
        "symbol": ")",
        "color": color,
        "weight": 5 if two_handed else 3,
        "twoHanded": two_handed,
        "reach": reach,
        "stunChance": stun,
        "bleedChance": bleed,
        "knockback": knockback,
        "ignoreShield": ignore_shield,
        "critMultiplier": crit_mult,
        "requiresAmmo": requires_ammo,
        "floorSpawnWeight": spawn_w,
        "containerLootTier": "common" if tier <= 2 else ("uncommon" if tier <= 3 else "rare"),
        "value": value,
        "min_level": min_lvl,
        "unidentified_name": unid_name,
        "lore": lore,
        "quiz_tier": quiz_tier,
        "identified": False,
    }
    return id_, d

# ─── NEW WEAPONS ──────────────────────────────────────────────────────────────

NEW_WEAPONS = dict([

  # ── MACE (crush damage, stun) ─────────────────────────────────────────────
  weapon("bone_mace","bone mace","mace","bone",1,5,1,["crush"],
    stun=0.15, unid_name="a crude bone club",
    lore="Fashioned from the femur of some large beast, this mace is little more than a heavy stick. Primitive but effective — the skull gives way just as readily to bone as to iron.",
    value=20),
  weapon("iron_mace","iron mace","mace","iron",1,7,1,["crush"],
    stun=0.22, unid_name="a heavy flanged club",
    lore="The flanged mace was a revelation in medieval warfare — its protruding ridges could deform plate armor and transmit fatal force even through thick padding. This iron version is the workhorse of dungeon brawlers who prefer certainty over finesse."),
  weapon("steel_mace","steel mace","mace","steel",2,10,21,["crush"],
    stun=0.26, unid_name="a heavy ridged bludgeon",
    lore="A well-tempered steel mace carries authority that few swords can match against heavily armored foes. Crusader knights favored such weapons when their blades proved useless against Saracen mail."),
  weapon("hardened_gold_mace","hardened gold mace","mace","hardened gold",3,13,41,["crush"],
    stun=0.30, unid_name="a gleaming weighted club",
    lore="Hardened gold is denser than steel and far more resistant to corrosion. The weight distribution of a gold mace is subtly different — the swing carries longer, the impact more decisive. Bishops of old carried such weapons, claiming they shed no blood while still crushing skulls."),
  weapon("diamond_mace","diamond mace","mace","diamond",4,16,61,["crush"],
    stun=0.33, unid_name="a brilliantly faceted bludgeon",
    lore="Diamond-tipped flanges can shatter the finest plate as if it were terracotta. The mage-smiths who craft these tools embed the gem-work into channels of enchanted iron, ensuring the diamonds survive the brutal stresses of combat."),
  weapon("adamantine_mace","adamantine mace","mace","adamantine",5,20,81,["crush"],
    stun=0.36, unid_name="an unnaturally heavy flanged mace",
    lore="Adamantine absorbs kinetic energy like a dark sponge and releases it concentrated at the point of impact. Wielding this mace feels like striking with a piece of a collapsed star."),

  # ── WAR HAMMER (2h crush, massive stun) ───────────────────────────────────
  weapon("iron_warhammer","iron war hammer","warhammer","iron",1,11,1,["crush"],
    two_handed=True, stun=0.28, unid_name="a two-handed iron hammer",
    lore="The war hammer's long haft provides leverage that no one-handed weapon can match. Used to drive tent stakes by day and skulls by night, this iron model has seen both purposes."),
  weapon("steel_warhammer","steel war hammer","warhammer","steel",2,15,21,["crush"],
    two_handed=True, stun=0.32, unid_name="a heavy two-handed steel hammer",
    lore="The Swiss and German infantry of the late medieval period elevated the war hammer into a specialized anti-armor tool. The poll spike could punch through visors; the hammerhead deformed pauldrons. This steel version carries that lethal legacy."),
  weapon("hardened_gold_warhammer","hardened gold war hammer","warhammer","hardened gold",3,19,41,["crush"],
    two_handed=True, stun=0.35, unid_name="a gleaming two-handed maul",
    lore="A maul of hardened gold is almost offensively heavy — until the first blow lands. Then the weight becomes a virtue. Dwarven artificers claim that gold hardened with their secret alloys is twice as effective as steel at transmitting force through enchanted armor."),
  weapon("diamond_warhammer","diamond war hammer","warhammer","diamond",4,23,61,["crush"],
    two_handed=True, stun=0.38, unid_name="a brutally heavy gem-faced hammer",
    lore="The impact of a diamond war hammer sends cracks propagating through stone floors. Its face is set with a flat diamond matrix that shatters on contact with metal — but regrows with each blow, a peculiarity no sage has fully explained."),
  weapon("adamantine_warhammer","adamantine war hammer","warhammer","adamantine",5,28,81,["crush"],
    two_handed=True, stun=0.40, unid_name="an impossibly heavy two-handed hammer",
    lore="Adamantine war hammers are not swung — they are guided. The weapon's own momentum does the work; the wielder merely steers. Legends say this weapon once belonged to a giant."),

  # ── MORNINGSTAR (crush + pierce, bleed) ───────────────────────────────────
  weapon("iron_morningstar","iron morningstar","morningstar","iron",1,8,1,["crush","pierce"],
    bleed=0.15, unid_name="a spiked iron ball on a shaft",
    lore="The morningstar — a spiked ball atop a stout shaft — was feared more for the wounds it left than the force it delivered. The iron spikes punch through ring mail and leave jagged tears that refuse to clot."),
  weapon("steel_morningstar","steel morningstar","morningstar","steel",2,11,21,["crush","pierce"],
    bleed=0.18, unid_name="a steel spiked bludgeon",
    lore="Steel-tipped spikes on a forged shaft represent a step up in brutality. The morningstar was commonplace in 13th-century European warfare, valued because soldiers could learn its use in days rather than years."),
  weapon("hardened_gold_morningstar","hardened gold morningstar","morningstar","hardened gold",3,14,41,["crush","pierce"],
    bleed=0.20, unid_name="a gleaming spiked golden ball",
    lore="A morningstar of hardened gold carries almost ceremonial menace. Each spike is etched with serpentine scrollwork. The wounds it leaves are ragged things that bleed for hours, as if cursed by the ornate craftsmanship itself."),
  weapon("diamond_morningstar","diamond morningstar","morningstar","diamond",4,17,61,["crush","pierce"],
    bleed=0.22, unid_name="a spiked gem-encrusted weapon",
    lore="Diamond spikes slice as cleanly as blades while the iron core delivers concussive force. Victims of this weapon face two problems simultaneously: hemorrhage and shock. The combination is usually fatal."),
  weapon("adamantine_morningstar","adamantine morningstar","morningstar","adamantine",5,22,81,["crush","pierce"],
    bleed=0.25, unid_name="a terrifyingly spiked iron ball",
    lore="An adamantine morningstar is the last word in martial brutality. The spikes are capable of piercing dragon hide, and the weight behind each blow is staggering. Wounds from this weapon are catastrophic and invariably begin to bleed."),

  # ── FLAIL (crush, ignore shield) ──────────────────────────────────────────
  weapon("iron_flail","iron flail","flail","iron",1,7,1,["crush"],
    ignore_shield=True, unid_name="a chained iron ball",
    lore="The flail's flexible chain allows its head to arc around a shield's edge, delivering force to spots the wielder could not otherwise reach. This iron model is a peasant's weapon — cheap, effective, and deeply resented by knights who spent fortunes on shields."),
  weapon("steel_flail","steel flail","flail","steel",2,10,21,["crush"],
    ignore_shield=True, unid_name="a heavy chained steel ball",
    lore="A steel flail in trained hands renders a shield almost irrelevant. The head snaps around guards with contemptuous ease. European foot soldiers adopted the flail specifically to counter the proliferation of large tower shields in 12th-century warfare."),
  weapon("hardened_gold_flail","hardened gold flail","flail","hardened gold",3,13,41,["crush"],
    ignore_shield=True, unid_name="a weighted golden flail",
    lore="The weight of hardened gold makes this flail's head swing with almost predatory momentum. The chain is enchanted with flexibility wards that prevent kinking even at full extension. No shield yet made has stopped it."),
  weapon("diamond_flail","diamond flail","flail","diamond",4,16,61,["crush"],
    ignore_shield=True, unid_name="a gem-headed chained weapon",
    lore="The diamond head of this flail shatters against armor but reforms in an instant — an enchantment that bewilders anyone trying to block it. The chain whispers as it moves, a sound that experienced warriors have learned to dread."),
  weapon("adamantine_flail","adamantine flail","flail","adamantine",5,20,81,["crush"],
    ignore_shield=True, unid_name="an incredibly dense chained weapon",
    lore="Adamantine flails are weapons of last resort even among elite warriors. The chain never tangles; the head never shatters; the force is absolute. The only reliable response to being struck is to fall."),

  # ── RAPIER (1h pierce, crit multiplier) ───────────────────────────────────
  weapon("iron_rapier","iron rapier","rapier","iron",1,5,1,["pierce"],
    crit_mult=1.5, unid_name="a thin thrusting blade",
    lore="A slender iron blade ground to a needle point, the rapier was the duelist's weapon of choice throughout Renaissance Europe. What it lacks in raw power it compensates with speed and precision. A perfect thrust through the visor slot ends fights instantly."),
  weapon("steel_rapier","steel rapier","rapier","steel",2,7,21,["pierce"],
    crit_mult=1.5, unid_name="a slim steel thrusting sword",
    lore="The Spanish pappenheimer rapier refined the form: a flexible blade tapering to a wicked point, balanced for the thrust rather than the cut. Steel allows the blade to be made longer and more whippy. Masters of the form could place their point anywhere within their opponent's guard."),
  weapon("hardened_gold_rapier","hardened gold rapier","rapier","hardened gold",3,9,41,["pierce"],
    crit_mult=1.5, unid_name="a gleaming thin thrusting blade",
    lore="A rapier of hardened gold is paradoxically both a status symbol and a lethal weapon. The gold alloy allows unusual flexibility — the blade bends in a full arc without breaking, storing energy that snaps it straight on release and drives the point home with devastating authority."),
  weapon("diamond_rapier","diamond rapier","rapier","diamond",4,12,61,["pierce"],
    crit_mult=1.5, unid_name="a crystalline needle-pointed blade",
    lore="Diamond ground to a blade that can pierce plate armor as if it were wood. The weapon's lightness belies its devastation. A diamond rapier's perfect chain strike has been compared to a lightning bolt finding the shortest path to ground."),
  weapon("adamantine_rapier","adamantine rapier","rapier","adamantine",5,15,81,["pierce"],
    crit_mult=1.6, unid_name="a dark slender thrusting sword",
    lore="The last word in precision killing. An adamantine rapier can pierce any known protection. Its perfect chain strike channels all the wielder's skill into one catastrophic thrust that bypasses the body's defenses entirely."),

  # ── SCIMITAR (1h slash, crit bonus) ───────────────────────────────────────
  weapon("iron_scimitar","iron scimitar","scimitar","iron",1,7,1,["slash"],
    crit_mult=1.3, unid_name="a curved iron slashing blade",
    lore="The scimitar's curved blade is designed for cavalry — the drawing cut that slices as the horseman rides past. On foot it is equally fearsome: the curved edge travels a longer path through flesh than a straight blade of identical length."),
  weapon("steel_scimitar","steel scimitar","scimitar","steel",2,9,21,["slash"],
    crit_mult=1.3, unid_name="a curved steel slashing sword",
    lore="Saracen smiths developed steel scimitars to a fine art. A well-tempered curve blade combines the edge geometry that maximizes cutting with the structural rigidity needed to survive combat. Crusader accounts describe these blades as 'cutting like scissors through silk.'"),
  weapon("hardened_gold_scimitar","hardened gold scimitar","scimitar","hardened gold",3,12,41,["slash"],
    crit_mult=1.3, unid_name="a curved gleaming slasher",
    lore="The curved lines of a hardened gold scimitar make it as aesthetically striking as it is dangerous. The curve amplifies the cutting motion; the gold's density adds momentum at the tip where it matters most. Several legendary blades of this type are named in Islamic chronicles."),
  weapon("diamond_scimitar","diamond scimitar","scimitar","diamond",4,15,61,["slash"],
    crit_mult=1.4, unid_name="a curved crystal-edged blade",
    lore="A diamond-edged curve blade divides flesh so cleanly that wounds seem to seal before bleeding — then open catastrophically a second later. The perfect chain strike with this weapon is a blur that leaves opponents confused about when and how badly they were cut."),
  weapon("adamantine_scimitar","adamantine scimitar","scimitar","adamantine",5,18,81,["slash"],
    crit_mult=1.4, unid_name="a dark sweeping curved blade",
    lore="An adamantine scimitar completes its arc so quickly that it seems to disappear between one heartbeat and the next. The critical momentum of a flawless chain attack through the curved edge geometry is catastrophic."),

  # ── ZWEIHANDER (2h slash+pierce, massive damage) ──────────────────────────
  weapon("iron_zweihander","iron zweihander","zweihander","iron",1,13,1,["slash","pierce"],
    two_handed=True, unid_name="a massive two-handed iron sword",
    lore="The zweihander — literally 'two-hander' — was the weapon of Doppelsöldner, German mercenaries paid double wages to stand in the front rank and shatter enemy pike formations. An iron zweihander is crude but the physics are simple: mass times velocity."),
  weapon("steel_zweihander","steel zweihander","zweihander","steel",2,17,21,["slash","pierce"],
    two_handed=True, unid_name="a long steel two-handed sword",
    lore="The 16th-century zweihander reached up to 6 feet in length and weighed 5 to 7 pounds. This steel version is at the lower end of that spectrum but fully battle-ready. The flamboyant (flame-shaped) blade was designed to disrupt pole formations with vibration on contact."),
  weapon("hardened_gold_zweihander","hardened gold zweihander","zweihander","hardened gold",3,21,41,["slash","pierce"],
    two_handed=True, unid_name="a massive gleaming two-handed blade",
    lore="A zweihander of hardened gold is an absurdity in steel workshops but a masterwork in magical ones. The weight is borne by enchantments; the edge is keener than any steel. Those few who have wielded it describe the experience as 'conducting a symphony of carnage.'"),
  weapon("diamond_zweihander","diamond zweihander","zweihander","diamond",4,26,61,["slash","pierce"],
    two_handed=True, unid_name="a crystalline two-handed giant blade",
    lore="This weapon is slightly taller than the average dwarf and carries enough kinetic energy to cleave through a door. The diamond matrix edge stays forever sharp. Each blow is accompanied by a high-pitched tone from the crystal's vibration."),
  weapon("adamantine_zweihander","adamantine zweihander","zweihander","adamantine",5,32,81,["slash","pierce"],
    two_handed=True, unid_name="a devastatingly heavy two-handed sword",
    lore="The adamantine zweihander is a weapon of legend. Very few can lift it without magical assistance. Those who can wield it effectively leave nothing standing. The blade's black surface absorbs light even as it cuts through armor."),

  # ── NAMED HISTORICAL WEAPONS ──────────────────────────────────────────────

  # Gladius — Roman short sword
  weapon("gladius","gladius","sword","iron",1,7,1,["slash","pierce"],
    crit_mult=1.2, unid_name="a short leaf-shaped sword",
    value=120,
    spawn_w=spawn(20,10,5,2,1),
    lore="The gladius Hispaniensis was the standard sidearm of the Roman legionary from the 2nd century BC. Its 50-60cm leaf-shaped blade excelled in close formation fighting — the legionary crouched behind his scutum and thrust upward at an exposed abdomen. It won an empire.",
    color=[210, 220, 235]),

  # Pugio — Roman military dagger
  weapon("pugio","pugio","dagger","iron",1,4,1,["pierce","slash"],
    crit_mult=1.3, unid_name="a wide-bladed Roman knife",
    value=80,
    spawn_w=spawn(20,10,5,2,1),
    lore="The pugio was the personal sidearm of Roman soldiers and officers from the 1st century BC. Worn on the left hip as a counterweight to the gladius, it served as a last resort in close combat and a tool for camp life. Julius Caesar was allegedly stabbed with a pugio — or many of them.",
    color=[200, 210, 220]),

  # Kopis — Greek/Persian curved blade
  weapon("kopis","kopis","scimitar","iron",1,8,1,["slash"],
    crit_mult=1.25, unid_name="a heavy curved slashing blade",
    value=110,
    spawn_w=spawn(20,10,5,2,1),
    lore="The kopis was favored by Greek cavalry and Persian infantry alike. Unlike the straight xiphos, its forward-curving blade was optimized for chopping downward strokes — ideal from horseback. Alexander's Macedonian cavalry carried kopis as secondary weapons alongside their sarissas.",
    color=[195, 175, 130]),

  # Francisca — Frankish throwing axe
  weapon("francisca","francisca","axe","iron",1,9,1,["slash"],
    knockback=True, unid_name="a strangely curved single-edged hatchet",
    value=130,
    spawn_w=spawn(20,10,5,2,1),
    lore="The francisca was the signature weapon of the Frankish warriors, used from the 5th to 8th centuries. Thrown just before contact, it caromed unpredictably along the ground and knocked down shields, disrupting formations. The 'knockback' effect was literal — it knocked shields away before the charge.",
    color=[180, 170, 150]),

  # Sica — Dacian curved dagger
  weapon("sica","sica","dagger","iron",1,4,1,["slash","pierce"],
    bleed=0.20, unid_name="a curved single-edged knife",
    value=100,
    spawn_w=spawn(20,10,5,2,1),
    lore="The sica was the weapon of Dacian warriors and Roman gladiators. Its inward-curved blade was designed to reach behind an opponent's shield and hook around armor. Roman writers noted that wounds from the sica had an unusual tendency to reopen — a phenomenon this blade replicates.",
    color=[195, 185, 160]),

  # Falchion — medieval single-edge curved sword
  weapon("falchion","falchion","sword","steel",2,11,21,["slash"],
    crit_mult=1.25, unid_name="a heavy curved single-edged sword",
    value=250,
    spawn_w=spawn(5,40,20,8,3),
    lore="The falchion was a weapon of the common soldier: cheaper to produce than a knightly sword, requiring less skill to use effectively, and brutally efficient against lightly armored opponents. The wide blade stored more momentum than a narrower sword. Medieval chroniclers described its users as 'indifferent to finesse but devoted to results.'",
    color=[170, 185, 210]),

  # Cinquedea — Italian broad dagger
  weapon("cinquedea","cinquedea","dagger","steel",2,7,21,["slash","pierce"],
    crit_mult=1.2, unid_name="a very wide short blade",
    value=220,
    spawn_w=spawn(5,35,15,5,2),
    lore="Named for its width of 'five fingers' at the ricasso, the cinquedea was a Renaissance Italian status weapon that doubled as a serious fighting tool. Its five ridges gave structural rigidity to an unusually wide blade. Wealthy citizens of 15th-century Ferrara wore these at the hip as a statement of intent.",
    color=[175, 190, 215]),

  # Estoc — anti-armor thrusting sword
  weapon("estoc","estoc","sword","steel",2,9,21,["pierce"],
    ignore_shield=True, crit_mult=1.3, unid_name="a long stiff thrusting sword",
    value=280,
    spawn_w=spawn(5,40,20,8,3),
    lore="The estoc — from Old French 'estocade,' to thrust — was developed specifically to defeat plate armor. Its stiff, unsharpened blade was designed to be driven through mail rings and into gaps in plate. In the hands of an expert it bypasses all surface defenses.",
    color=[180, 200, 225]),

  # Kukri — Nepalese forward-curved blade
  weapon("kukri","kukri","dagger","steel",2,8,21,["slash"],
    bleed=0.22, unid_name="a forward-curved heavy blade",
    value=200,
    spawn_w=spawn(5,35,18,7,2),
    lore="The kukri is the national weapon of Nepal and the combat knife of the Gurkha soldiers who have earned fear and respect in every army that has faced them. The forward curve concentrates force at the tip of the blade; the narrow notch near the guard prevents blood from running onto the handle. The Gurkha saying goes: 'Never draw it without drawing blood.'",
    color=[165, 175, 185]),

  # War Scythe — peasant uprising polearm
  weapon("war_scythe","war scythe","polearm","steel",2,13,21,["slash","pierce"],
    two_handed=True, unid_name="a repurposed agricultural polearm",
    value=240,
    spawn_w=spawn(5,35,15,5,2),
    lore="The war scythe was the weapon of desperate men — peasant armies during the Hussite Wars, Polish nobility uprisings, and countless smaller rebellions. A blacksmith would rotate the blade 90 degrees on a long haft, transforming a harvest tool into a weapon capable of unhorsing cavalry. Inelegant but terrifyingly effective.",
    color=[170, 180, 190]),

  # Bastard sword — versatile 1h or 2h
  weapon("bastard_sword","bastard sword","sword","steel",2,14,21,["slash","pierce"],
    two_handed=True, crit_mult=1.15, unid_name="a versatile long-gripped sword",
    value=300,
    spawn_w=spawn(5,40,25,10,4),
    lore="The 'bastard sword' or hand-and-a-half sword occupied the gap between a standard longsword and a full two-hander. It could be wielded one-handed from horseback or two-handed on foot. Its length gave reach; its grip options gave versatility. The name comes from its ambiguous classification in medieval catalogs.",
    color=[175, 195, 220]),

  # Katana — Japanese curved longsword
  weapon("katana","katana","sword","hardened gold",3,13,41,["slash"],
    crit_mult=1.4, unid_name="a gracefully curved eastern longsword",
    value=600,
    spawn_w=spawn(0,5,50,25,10),
    lore="The katana represents centuries of Japanese metallurgical art. The differential hardening process — clay-coating the spine before quenching — creates a blade with a hard edge and tough back. The characteristic curve (sori) develops during the quench. A perfect kata produces a strike that opponents frequently describe as not feeling until seconds after.",
    color=[220, 215, 190]),

  # Dao — Chinese broadsword
  weapon("dao","dao","scimitar","hardened gold",3,12,41,["slash"],
    crit_mult=1.35, unid_name="a curved eastern broadsword",
    value=580,
    spawn_w=spawn(0,5,45,22,8),
    lore="The dao is one of the four traditional weapons of Chinese martial arts. Its single-edged curved blade was the standard weapon of Chinese cavalry and infantry through multiple dynasties. Masters of the dao are said to achieve a state of 'no-mind' in which the blade becomes an extension of intent rather than arm.",
    color=[215, 185, 60]),

  # Naginata — Japanese pole blade
  weapon("naginata","naginata","polearm","ironwood",3,15,41,["slash","pierce"],
    two_handed=True, reach=2, crit_mult=1.2, unid_name="a long polearm with a curved blade",
    value=620,
    spawn_w=spawn(0,5,45,22,8),
    lore="The naginata was the weapon of the onna-bugeisha, Japanese female warriors, and later of Buddhist warrior monks. Its long shaft and curved blade combined the reach of a spear with the cutting ability of a sword. Naginata schools still exist in Japan; the weapon is considered more difficult to master than the katana.",
    color=[130, 110, 80]),

  # Claymore — Scottish great sword
  weapon("claymore","claymore","zweihander","hardened gold",3,21,41,["slash","pierce"],
    two_handed=True, unid_name="a massive highland two-handed sword",
    value=700,
    spawn_w=spawn(0,5,45,20,8),
    lore="The Scottish claymore (claidheamh mòr, 'great sword') was the signature weapon of Highland warriors from the 15th century. Its distinctive downward-angling quillons with trefoil finials made it instantly recognizable. Swung by a Highland warrior in full charge, the claymore could cleave through leather, mail, and occasionally the man wearing it.",
    color=[200, 195, 175]),

  # Partisan — winged spear head
  weapon("partisan","partisan","polearm","hardened gold",3,14,41,["pierce","slash"],
    two_handed=True, reach=2, unid_name="a long spear with side blades",
    value=580,
    spawn_w=spawn(0,5,40,18,6),
    lore="The partisan was a ceremonial and combat polearm of the Renaissance, featuring a main spike with two smaller side blades at the base. The side blades could catch and bind an opponent's weapon, or be used for slashing after the main thrust. Papal Swiss Guards carried partisans as marks of office.",
    color=[210, 180, 60]),

  # Mameluke saber — Ottoman cavalry saber
  weapon("mameluke_saber","mameluke saber","scimitar","diamond",4,16,61,["slash"],
    crit_mult=1.45, unid_name="an exquisitely curved cavalry saber",
    value=1200,
    spawn_w=spawn(0,0,5,50,20),
    lore="The mameluke saber was the weapon of the warrior-slave elite of the Islamic world. Its distinctive T-shaped cross-section and radical curve made it the deadliest cavalry saber of its era. Napoleon's guard officers adopted the style after Egypt; US Marine officers still carry a version of this blade today.",
    color=[190, 245, 255]),

  # Flamberge — wavy two-handed sword
  weapon("flamberge","flamberge","zweihander","diamond",4,25,61,["slash","pierce"],
    two_handed=True, bleed=0.18, unid_name="a two-handed undulating blade",
    value=1400,
    spawn_w=spawn(0,0,5,45,18),
    lore="The flamberge's wave-shaped blade was not merely aesthetic. The undulations created additional cutting edges along the blade's length and disrupted opponents' parries by vibrating their weapons uncomfortably. Opponents who blocked a flamberge often found their hands numbed; those it touched bore wounds that festered unusually.",
    color=[185, 245, 255]),

  # Executioner's sword
  weapon("executioners_sword","executioner's sword","sword","diamond",4,18,61,["slash"],
    bleed=0.25, crit_mult=1.3, two_handed=True, unid_name="a massive blunt-tipped slashing blade",
    value=1350,
    spawn_w=spawn(0,0,5,40,15),
    lore="The headsman's sword had no point — a stabbing weapon is useless when your target is kneeling. Instead, the blade was ground to extraordinary sharpness along its length for a clean single-stroke execution. A skilled executioner was expected to sever the head in one blow; a second stroke was considered a failure and the victim's family was entitled to demand compensation.",
    color=[180, 240, 255]),

  # Soul Reaver — legendary end-game weapon
  weapon("soul_reaver","Soul Reaver","scimitar","adamantine",5,20,81,["slash","pierce"],
    bleed=0.30, crit_mult=1.5, unid_name="a dark whispering curved blade",
    value=5000,
    spawn_w=spawn(0,0,0,0,8),
    lore="Few who have held the Soul Reaver remember doing so willingly. The blade selects its wielders, and the criteria are opaque. What is known: wounds it inflicts do not heal without magic; the blade whispers between kills; and it grows heavier if used against the innocent. Its origin is attributed variously to a dying god, a betrayed archmage, and a particularly vengeful plague.",
    color=[80, 50, 180]),

  # Dawnbreaker — legendary warhammer
  weapon("dawnbreaker","Dawnbreaker","warhammer","adamantine",5,30,81,["crush"],
    two_handed=True, stun=0.45, crit_mult=1.4, unid_name="a radiant two-handed hammer",
    value=5000,
    spawn_w=spawn(0,0,0,0,6),
    lore="Dawnbreaker is the weapon that ended the First Darkness — at least, that is the oldest story. The hammer's adamantine head contains a shard of preserved dawn light, visible as a faint golden gleam even in pitch darkness. Undead creatures struck by it take triple damage from the light component, in addition to the physical devastation.",
    color=[200, 180, 80]),

  # Venomfang — legendary morningstar
  weapon("venomfang","Venomfang","morningstar","adamantine",5,23,81,["crush","pierce"],
    bleed=0.35, unid_name="a darkly gleaming spiked weapon",
    value=4800,
    spawn_w=spawn(0,0,0,0,7),
    lore="A master poisoner's commission from an earlier age. The spikes of Venomfang are hollow, filled with a venom that was synthesized from the distilled suffering of a hundred different creatures. The weapon weeps a thin dark ichor when hungry, which is often. The bleed it inflicts does not merely cut — it corrupts.",
    color=[90, 130, 70]),

])

# ─── NEW ARMOR ────────────────────────────────────────────────────────────────

def armor(id_, name, slot, mat, tier, ac, min_lvl,
          quiz_tier=None, equip_thresh=2, can_curse=False,
          dmg_res=None, unid_name=None, lore="",
          color=None, enchant_bonus=0, value=None):
    if quiz_tier is None:
        quiz_tier = tier
    if dmg_res is None:
        dmg_res = {}
    if unid_name is None:
        unid_name = f"some {mat} {slot} armor"
    if value is None:
        value = tier * 80 + ac * 30
    mat_colors = {
        "cloth":      [180, 175, 165],
        "padded":     [190, 180, 160],
        "leather":    [140, 110, 75],
        "hide":       [160, 130, 95],
        "fur":        [175, 145, 100],
        "wool":       [200, 190, 175],
        "silk":       [220, 200, 230],
        "linen":      [215, 205, 190],
        "bronze":     [200, 155, 85],
        "iron":       [180, 190, 205],
        "chain":      [175, 185, 200],
        "scale":      [170, 185, 195],
        "steel":      [160, 175, 200],
        "banded":     [155, 170, 195],
        "splint":     [150, 165, 190],
        "plate":      [200, 205, 220],
        "mithril":    [160, 200, 255],
        "crystal":    [200, 240, 255],
        "dragonscale":[140, 200, 160],
        "adamantine": [80,  60, 170],
    }
    if color is None:
        color = mat_colors.get(mat, [170, 170, 170])
    return id_, {
        "name": name,
        "symbol": "[",
        "color": color,
        "weight": max(0.5, ac * 1.5),
        "min_level": min_lvl,
        "slot": slot,
        "tier": tier,
        "material": mat,
        "ac_bonus": ac,
        "equip_threshold": equip_thresh,
        "quiz_tier": quiz_tier,
        "damage_resistances": dmg_res,
        "can_be_cursed": can_curse,
        "enchant_bonus": enchant_bonus,
        "unidentified_name": unid_name,
        "lore": lore,
        "identified": False,
    }

NEW_ARMOR = dict([

  # ── HEAD ──────────────────────────────────────────────────────────────────
  armor("cloth_hood","cloth hood","head","cloth",1,0,1,
    unid_name="a plain fabric hood",
    lore="A simple hood of rough-woven cloth. It keeps the dust out of your eyes and little else. Every adventurer starts somewhere."),
  armor("bronze_helm","bronze helm","head","bronze",1,2,11,
    unid_name="an old-looking metal helmet",
    lore="Bronze predates iron in human warfare by millennia. A well-cast bronze helmet provides surprising protection; Corinthian bronze helms offered full-face coverage and were worn by Greek hoplites for three centuries."),
  armor("sallet","sallet","head","steel",3,3,41,
    unid_name="an open-faced sweep-brimmed helm",
    lore="The sallet was the standard helmet of 15th-century European infantry and cavalry. Its swept-back brim deflected downward sword cuts; its open face allowed clear vision. English archers at Agincourt wore sallets. It represents the high point of practical medieval helmet design."),
  armor("bascinet","bascinet","head","steel",3,3,41,
    unid_name="a pointed visor helmet",
    lore="The bascinet evolved from the simple iron skullcap into a sophisticated piece of armor with an articulated visor. Knights of the 14th century attached chain aventails to the bascinet's edges, protecting the neck and cheeks. The pointed top deflects downward blows laterally."),
  armor("armet","armet","head","plate",4,4,61,
    unid_name="a fully enclosing tournament helm",
    lore="The armet was the pinnacle of 15th and 16th-century helmet craft: a fully enclosing helm that locked around the wearer's head for tournament and field use alike. The hinged cheekpieces created a sealed environment that was both uncomfortably warm and extraordinarily protective."),
  armor("mithril_helm","mithril helm","head","mithril",4,4,61,
    dmg_res={"magic":0.10}, equip_thresh=3,
    unid_name="a shimmering lightweight helm",
    lore="Mithril, the moonmetal, weighs a third of steel yet provides equivalent protection through an enchantment woven into its crystalline structure. A mithril helm offers a subtle resistance to magical attacks — the metal refracts hostile spells the same way it refracts light."),

  # ── BODY ──────────────────────────────────────────────────────────────────
  armor("brigandine","brigandine","body","steel",2,4,21,
    unid_name="a cloth coat with metal rivets",
    lore="The brigandine was the armor of choice for 14th-century mercenary companies: small iron or steel plates riveted to a fabric outer coat, usually velvet or canvas. It combined the flexibility of cloth with reasonable protection and was far cheaper than a full coat of mail."),
  armor("hauberk","hauberk","body","chain",2,4,21,
    unid_name="a long-skirted chain coat",
    lore="The hauberk was the primary body defense of Norman and crusading knights. A full hauberk extended to mid-thigh with skirts split for riding, long sleeves ending in mail mittens, and an attached coif. William the Conqueror's knights wore hauberks at Hastings in 1066."),
  armor("coat_of_plates","coat of plates","body","plate",3,6,41,
    unid_name="a heavy riveted plate coat",
    lore="Transitional armor of the early 14th century: large overlapping iron plates riveted to a heavy fabric foundation. The Black Prince wore a coat of plates over his mail at Crécy. It represents the step between chain and full plate — more protection but heavier and less mobile than later plate armor."),
  armor("mithril_plate","mithril plate","body","mithril",4,7,61,
    dmg_res={"magic":0.15}, equip_thresh=4,
    unid_name="a shimmering full-body suit",
    lore="Mithril plate is the culmination of elven craft and dwarven metallurgy. It weighs half what steel plate does and deflects magical energies with unusual efficiency. A mithril plate suit was reportedly worn by a human wizard who survived a dragon's full breath weapon — though he described the experience as 'thoroughly unpleasant.'"),

  # ── ARMS ──────────────────────────────────────────────────────────────────
  armor("cloth_wraps","cloth arm wraps","arms","cloth",1,0,1,
    unid_name="plain wrapped cloth",
    lore="Simple strips of linen wrapped around the forearms. They protect against minor abrasions and cold rather than serious weapons."),
  armor("padded_bracers","padded bracers","arms","padded",1,0,1,
    unid_name="thick padded forearm wraps",
    lore="Quilted linen bracers filled with wool provided the common soldier's minimal forearm protection. More importantly, they prevented the abrasion from a mail coat's interior surface."),
  armor("bronze_bracers","bronze bracers","arms","bronze",1,1,11,
    unid_name="old bronze arm guards",
    lore="Bronze greaves and bracers preceded iron equivalents in Greek and Roman armies. A pair of Mycenaean bronze bracers found at Dendra represents over 3,000 years of continuous use of this design."),
  armor("chain_bracers","chain bracers","arms","chain",2,1,21,
    unid_name="linked metal forearm guards",
    lore="Chain mail bracers protect the forearms while allowing the hand full articulation. They are heavier than leather but significantly better at deflecting cuts."),
  armor("scale_bracers","scale bracers","arms","scale",2,1,21,
    unid_name="overlapping plate forearm guards",
    lore="Overlapping scales of metal riveted to leather backing create excellent glancing resistance. Scale armor was standard issue in the armies of ancient Egypt and Persia."),
  armor("crystal_bracers","crystal bracers","arms","crystal",4,2,61,
    dmg_res={"magic":0.12},
    unid_name="glowing forearm guards",
    lore="Crystal bracers are grown rather than forged — mage-cultivated mineral formations shaped into armor. They resonate with defensive wards that reflect minor magical attacks harmlessly."),
  armor("dragonscale_bracers","dragonscale bracers","arms","dragonscale",5,2,81,
    dmg_res={"fire":0.15},
    unid_name="scaled exotic forearm guards",
    lore="Dragonscale bracers require scales from the foreleg — the most densely armored section of any dragon. The fire resistance they provide is inherent to the scale's structure, not an enchantment."),

  # ── HANDS ─────────────────────────────────────────────────────────────────
  armor("iron_gauntlets","iron gauntlets","hands","iron",2,1,21,
    unid_name="heavy fingered iron gloves",
    lore="Early iron gauntlets were crude affairs: mitten-shaped iron coverings attached to mail sleeves. By the 13th century, articulated fingers had been developed. These iron examples represent the transitional form."),
  armor("bronze_gauntlets","bronze gauntlets","hands","bronze",1,0,11,
    unid_name="old metal hand covers",
    lore="Bronze gauntlets were worn by Macedonian cavalry to protect sword hands. Their archaeological record dates to 700 BC. These examples follow the simple mitten form that was practical for three millennia."),
  armor("mithril_gauntlets","mithril gauntlets","hands","mithril",4,2,61,
    dmg_res={"magic":0.08},
    unid_name="shimmering lightweight metal gloves",
    lore="Mithril gauntlets are fully articulated at every finger joint and provide complete protection without any loss of weapon control. Master craftspeople take six months to produce a single pair."),

  # ── LEGS ──────────────────────────────────────────────────────────────────
  armor("cloth_leggings","cloth leggings","legs","cloth",1,0,1,
    unid_name="plain fabric leg covers",
    lore="Simple cloth leggings provide no real protection but at least insulate against cold stone floors."),
  armor("padded_leggings","padded leggings","legs","padded",1,0,1,
    unid_name="thick padded leg protection",
    lore="Padded leggings were worn under heavier armor throughout the medieval period. They also served as the standalone leg protection of poorer soldiers who could not afford mail."),
  armor("iron_leggings","iron leggings","legs","iron",2,2,21,
    unid_name="solid iron leg plates",
    lore="Iron plate leg armor protected the vulnerable femoral artery from cutting weapons. Medieval surgeons noted that wounds to the upper leg were among the most dangerous — which explains why legionnaires spent so much on this protection."),
  armor("scale_greaves","scale greaves","legs","scale",3,2,41,
    unid_name="overlapping scaled leg guards",
    lore="Scale greaves represent the Eastern approach to leg protection: flexible scales that move with the leg while providing good overall coverage. Byzantine cavalry used this pattern throughout the eastern empire."),
  armor("crystal_greaves","crystal greaves","legs","crystal",4,3,61,
    dmg_res={"magic":0.10},
    unid_name="shimmering crystal leg armor",
    lore="Crystal greaves hum faintly when approached by hostile magic, providing both warning and protection. The resonance crystals in the knee joints can detect arcane energies up to 10 feet away."),

  # ── FEET ──────────────────────────────────────────────────────────────────
  armor("cloth_sandals","cloth sandals","feet","cloth",1,0,1,
    unid_name="simple wrapped sandals",
    lore="The simplest footwear imaginable — straps of cloth wrapped around the foot and ankle. Offers no real protection but allows silent movement and is better than going barefoot on dungeon stone."),
  armor("padded_boots","padded boots","feet","padded",1,0,1,
    unid_name="thick-soled cloth boots",
    lore="Padded boots filled with wool provide warmth and limited protection. They are the everyday footwear of merchants, farmers, and beginning adventurers."),
  armor("bronze_boots","bronze boots","feet","bronze",1,0,11,
    unid_name="old bronze foot guards",
    lore="Bronze greaves covered the shins and were held in place by the metal's natural spring. Greek hoplites wore bronze greaves without straps; the metal gripped the leg by itself. These boots extend the protection to the foot."),
  armor("chain_boots","chain boots","feet","chain",2,1,21,
    unid_name="linked metal boots",
    lore="Chain mail feet protection is more common than it might seem — crusading knights wore chain chaussures covering the entire foot in linked rings. They provided excellent protection against slashing while maintaining reasonable flexibility."),
  armor("crystal_boots","crystal boots","feet","crystal",4,2,61,
    dmg_res={"magic":0.10},
    unid_name="glowing crystalline boots",
    lore="Crystal boots grip the floor with surprising stability — the crystalline structure creates a natural adhesion that prevents slipping on wet stone. The magical resistance embedded in each facet extends from toe to calf."),
  armor("mithril_boots","mithril boots","feet","mithril",4,2,61,
    dmg_res={"magic":0.08},
    unid_name="shimmering lightweight boots",
    lore="Mithril boots are so light that wearers report feeling faster — a subjective effect that tests have confirmed is objectively true. The metal's enchantments reduce impact, allowing quieter movement than any other protective footwear."),

  # ── CLOAK ─────────────────────────────────────────────────────────────────
  armor("fur_cloak","fur cloak","cloak","fur",1,1,1,
    unid_name="a thick animal-fur cloak",
    lore="A bearskin or wolf-pelt cloak was the mark of a northern warrior — practical insulation against the cold and an intimidating appearance in southern eyes. Several Viking chieftains were described wearing such cloaks over their mail."),
  armor("wool_cloak","wool cloak","cloak","wool",1,0,1,
    unid_name="a heavy grey cloak",
    lore="Undyed wool cloaks were the standard traveling garment across the medieval world. The natural lanolin in wool provides mild water resistance; the thickness provides warmth. Not impressive, but reliable."),
  armor("silk_cloak","silk cloak","cloak","silk",3,1,41,
    dmg_res={"pierce":0.05}, equip_thresh=3,
    unid_name="a lustrous smooth cloak",
    lore="Silk is surprisingly effective at stopping arrows — the fiber wraps around arrowheads and prevents penetration. Mongol warriors wore silk undergarments precisely because removal of the garment could draw out arrowheads without surgery. A silk cloak extends this protection."),
  armor("mithril_cloak","mithril cloak","cloak","mithril",4,2,61,
    dmg_res={"magic":0.15}, equip_thresh=3,
    unid_name="a faintly shimmering cloak",
    lore="A mithril-woven cloak is the ultimate magical protection garment. The metal threads form an interference pattern that disrupts incoming spells. Arch-mages who have studied this effect describe it as 'the magic equivalent of signal jamming.'"),
  armor("shadowweave_cloak","shadowweave cloak","cloak","adamantine",5,3,81,
    dmg_res={"magic":0.20,"pierce":0.10},
    equip_thresh=4, can_curse=True,
    unid_name="a cloak that seems to absorb light",
    lore="Woven from adamantine threads thinner than silk, the shadowweave cloak is barely visible in dim light — it bends shadows around the wearer. Assassins covet these garments; rulers fear them. The cursed variants permanently darken the wearer's reputation in ways that are difficult to explain to historians."),

  # ── SHIRT ─────────────────────────────────────────────────────────────────
  armor("linen_shirt","linen shirt","shirt","linen",1,0,1,
    unid_name="a plain off-white undershirt",
    lore="Worn against the skin beneath any other armor. Keeps sweat from rusting the mail and distributes the weight more comfortably. Everyone wears one."),
  armor("wool_shirt","wool shirt","shirt","wool",1,0,1,
    unid_name="a thick undershirt",
    lore="Thick wool against the skin in cold dungeons is not luxury — it is survival. Medieval knights wore wool garments under their mail in winter. The padding also reduces the transfer of impact forces from the outer armor."),
  armor("silk_shirt","silk shirt","shirt","silk",3,1,41,
    dmg_res={"pierce":0.08}, equip_thresh=3,
    unid_name="an unexpectedly protective undershirt",
    lore="Silk's arrow-stopping properties were well known in the medieval east. A tight-woven silk undergarment catches and wraps arrowheads, preventing deeper penetration. Temur's cavalry reportedly wore silk shirts under their armor for exactly this reason."),
  armor("scale_shirt","scale shirt","shirt","scale",3,2,41,
    unid_name="a short-sleeved scale coat",
    lore="A scale shirt worn beneath outer armor is an old layering technique. The scales provide a rigid base that distributes the force of impacts, while the outer layer provides coverage. Egyptian and Mesopotamian warriors wore this combination for centuries."),
  armor("elven_shirt","elven shirt","shirt","mithril",4,2,61,
    dmg_res={"magic":0.20}, equip_thresh=3, can_curse=False,
    unid_name="an impossibly fine mail garment",
    lore="Elven craftspeople weave mithril into garments so fine they appear to be fabric rather than armor. An elven shirt can be folded into a package the size of a handkerchief. It weighs nothing and stops almost everything. Those few who have worn one describe feeling simultaneously naked and invincible.",
    color=[170, 210, 255]),

])

# ─── FIX ACCESSORIES (proper min_level and floorSpawnWeight) ──────────────────

def accessory_floor_spawn(min_l, peak_lo, peak_hi):
    """Build a floorSpawnWeight table for accessories."""
    sw = {}
    for lo in range(1, 101, 20):
        hi = lo + 19
        lvl = (lo + hi) // 2
        if hi < min_l:
            sw[f"{lo}-{hi}"] = 0
        elif lo <= peak_hi and hi >= peak_lo:
            sw[f"{lo}-{hi}"] = 80
        elif lo < peak_lo:
            sw[f"{lo}-{hi}"] = 30
        else:
            sw[f"{lo}-{hi}"] = 40
    return sw

# Map old quiz_tier -> new min_level and level bands
ACC_TIER_MAP = {
    1: (1,  1,  60),   # early game — spawns 1-60
    2: (8,  10, 70),   # early-mid game
    3: (25, 30, 90),   # mid game
    4: (45, 50, 100),  # late game
    5: (65, 70, 100),  # end game
}

# ─── NEW ACCESSORIES ──────────────────────────────────────────────────────────

NEW_ACCESSORIES = {
  # Rings of Protection (+AC)
  "ring_protection_silver": {
    "name": "ring of protection +1",
    "symbol": "=", "color": [220, 220, 240], "weight": 0.1,
    "min_level": 10, "slot": "ring", "equip_threshold": 2, "quiz_tier": 2,
    "effects": {"stat": "AC", "amount": 1},
    "unidentified_name": "a smooth silver ring",
    "lore": "A silver ring engraved with overlapping ward-circles. The protection it offers is modest but reliable — every experienced adventurer keeps at least one.",
    "identified": False,
  },
  "ring_protection_gold": {
    "name": "ring of protection +2",
    "symbol": "=", "color": [220, 200, 80], "weight": 0.1,
    "min_level": 35, "slot": "ring", "equip_threshold": 3, "quiz_tier": 3,
    "effects": {"stat": "AC", "amount": 2},
    "unidentified_name": "a polished gold band",
    "lore": "A finely wrought golden ring set with nested protection glyphs. The field it generates slightly deflects incoming attacks, as if the air itself becomes briefly solid around the wearer.",
    "identified": False,
  },
  "ring_protection_adamantine": {
    "name": "ring of protection +3",
    "symbol": "=", "color": [80, 60, 170], "weight": 0.1,
    "min_level": 61, "slot": "ring", "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"stat": "AC", "amount": 3},
    "unidentified_name": "a dark heavy ring",
    "lore": "A dense band of adamantine inscribed with protection formulae so complex that identifying the ring correctly requires advanced philosophical training. The field it generates is nearly impenetrable.",
    "identified": False,
  },

  # Rings of Speed
  "ring_speed_quicksilver": {
    "name": "ring of speed",
    "symbol": "=", "color": [210, 230, 240], "weight": 0.1,
    "min_level": 30, "slot": "ring", "equip_threshold": 3, "quiz_tier": 3,
    "effects": {"status": "hasted", "duration": -1},
    "unidentified_name": "a vibrating quicksilver ring",
    "lore": "Quicksilver rings that vibrate at a specific resonance can entrain the wearer's nervous system to fire slightly faster. The effect is subtle but cumulative — the ring's owner moves, thinks, and reacts just quickly enough to survive situations that would kill others.",
    "identified": False,
  },

  # Rings of Sustenance
  "ring_sustenance_amber": {
    "name": "ring of sustenance",
    "symbol": "=", "color": [210, 170, 80], "weight": 0.1,
    "min_level": 15, "slot": "ring", "equip_threshold": 2, "quiz_tier": 2,
    "effects": {"status": "sustained", "duration": -1},
    "unidentified_name": "a warm amber ring",
    "lore": "An amber ring containing a preserved insect that has not aged for ten thousand years. The preservation field extends to the wearer's metabolism, slowing hunger and reducing the need for rest. Useful in deep dungeons where food is scarce.",
    "identified": False,
  },

  # High stat bonus accessories
  "ring_strength_dragonbone": {
    "name": "ring of giant strength",
    "symbol": "=", "color": [210, 200, 175], "weight": 0.1,
    "min_level": 61, "slot": "ring", "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"stat": "STR", "amount": 4},
    "unidentified_name": "a massive carved bone ring",
    "lore": "Carved from the finger-knuckle of a fire giant, this ring channels a fraction of the creature's legendary strength into the wearer. The inscription reads: 'Take from strength; do not merely borrow it.'",
    "identified": False,
  },
  "ring_constitution_diamond": {
    "name": "ring of endurance",
    "symbol": "=", "color": [200, 245, 255], "weight": 0.1,
    "min_level": 61, "slot": "ring", "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"stat": "CON", "amount": 4},
    "unidentified_name": "a faceted crystal ring",
    "lore": "A diamond ring that channels the stone's indomitable hardness into the wearer's constitution. Those who have worn it for long periods report an unusual inability to tire, a reduced need for sleep, and a strange clarity of purpose.",
    "identified": False,
  },
  "ring_intellect_prismatic_deep": {
    "name": "ring of brilliance",
    "symbol": "=", "color": [200, 180, 255], "weight": 0.1,
    "min_level": 61, "slot": "ring", "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"stat": "INT", "amount": 4},
    "unidentified_name": "a shifting prismatic ring",
    "lore": "The prismatic ring contains a miniature aurora borealis in its setting — an observable phenomenon with no satisfactory mundane explanation. Wearers report accelerated thought, improved memory consolidation, and an occasional overwhelming sense of suddenly understanding something they cannot articulate.",
    "identified": False,
  },

  # Amulet of Life Saving
  "amulet_life_saving": {
    "name": "amulet of life saving",
    "symbol": '"', "color": [255, 230, 80], "weight": 0.2,
    "min_level": 50, "slot": "amulet", "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"status": "life_save", "duration": -1},
    "unidentified_name": "a warm golden medallion",
    "lore": "A single-use death ward forged from the solidified moment of a healer's last breath. The amulet cannot be refilled — when it triggers, it is spent. But the one time it matters, no price seems too high. Necromancers have offered fortunes to study how this effect works; none have succeeded.",
    "identified": False,
  },

  # Amulet of Spell Turning
  "amulet_spell_turning": {
    "name": "amulet of spell turning",
    "symbol": '"', "color": [180, 160, 255], "weight": 0.2,
    "min_level": 55, "slot": "amulet", "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"status": "spell_turning", "duration": -1},
    "unidentified_name": "a spiral-engraved medallion",
    "lore": "A medallion inscribed with a möbius-strip ward that sends certain spells back to their casters. The effect is imperfect — complex magics may partially deflect, partially turn, or simply fail. But the look on an enemy wizard's face when their own fireball returns is considered adequate compensation.",
    "identified": False,
  },

  # Amulet of True Sight
  "amulet_truesight": {
    "name": "amulet of true sight",
    "symbol": '"', "color": [200, 245, 200], "weight": 0.2,
    "min_level": 45, "slot": "amulet", "equip_threshold": 3, "quiz_tier": 3,
    "effects": {"status": "truesight", "duration": -1},
    "unidentified_name": "a clear gem pendant",
    "lore": "A lens of perfectly clear crystal that has been inscribed with wards against illusion, displacement, and invisibility. Looking through it reveals the world as it actually is. The feeling of wearing it has been compared to taking off glasses you did not know you were wearing.",
    "identified": False,
  },

  # Amulet of Reflection
  "amulet_reflection": {
    "name": "amulet of reflection",
    "symbol": '"', "color": [220, 235, 255], "weight": 0.2,
    "min_level": 60, "slot": "amulet", "equip_threshold": 4, "quiz_tier": 4,
    "effects": {"status": "reflecting", "duration": -1},
    "unidentified_name": "a mirror-faced medallion",
    "lore": "The face of this medallion is a perfect silver mirror. When hostile magic contacts it, the amulet reflects a portion of the effect back at its source. Powerful spellcasters who encounter this amulet for the first time sometimes cast their second spell into their own reflection.",
    "identified": False,
  },

  # High-tier stat amulets
  "amulet_titan_constitution": {
    "name": "amulet of titan constitution",
    "symbol": '"', "color": [220, 60, 60], "weight": 0.2,
    "min_level": 71, "slot": "amulet", "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "CON", "amount": 5},
    "unidentified_name": "a heavy blood-red gem pendant",
    "lore": "Forged in the crater where a titan fell, this amulet radiates a palpable sense of physical authority. The CON bonus it provides is extraordinary — those who wear it describe simultaneously feeling that their body could survive almost anything and that it probably will have to.",
    "identified": False,
  },
  "amulet_archmage_intellect": {
    "name": "amulet of archmage intellect",
    "symbol": '"', "color": [180, 140, 255], "weight": 0.2,
    "min_level": 71, "slot": "amulet", "equip_threshold": 5, "quiz_tier": 5,
    "effects": {"stat": "INT", "amount": 5},
    "unidentified_name": "a violet crystalline pendant",
    "lore": "This amulet was reportedly the property of a council of arch-mages who each contributed one year of their own intelligence to its enchantment. The cumulative effect of several lifetimes of accumulated intellect is significant.",
    "identified": False,
  },

  # Cursed accessories (interesting gameplay)
  "ring_curse_drain": {
    "name": "ring of life drain",
    "symbol": "=", "color": [80, 40, 120], "weight": 0.1,
    "min_level": 1, "slot": "ring", "equip_threshold": 2, "quiz_tier": 1,
    "effects": {"status": "draining", "duration": -1},
    "unidentified_name": "a cold purple ring",
    "lore": "This ring appears valuable and may even feel empowering when first worn. The draining effect is subtle at first — a slight weariness after long use. By the time the wearer notices the full extent of the damage, they have usually worn it for some time.",
    "identified": False,
  },
  "amulet_curse_drain": {
    "name": "amulet of doom",
    "symbol": '"', "color": [60, 20, 80], "weight": 0.2,
    "min_level": 1, "slot": "amulet", "equip_threshold": 2, "quiz_tier": 1,
    "effects": {"status": "doomed", "duration": -1},
    "unidentified_name": "an ominous dark pendant",
    "lore": "The amulet of doom does not harm the wearer directly. Instead, it makes the universe slightly more hostile — doors that would close slowly now close quickly; enemies that might have hesitated now strike immediately; saving throws always seem to land on the worst possible number. It has no off switch.",
    "identified": False,
  },
}

# ─── WRITE ────────────────────────────────────────────────────────────────────

def add_items(filepath, new_items, item_type="items"):
    with open(filepath, encoding='utf-8') as f:
        existing = json.load(f)
    before = len(existing)
    skipped = []
    for k, v in new_items.items():
        if k in existing:
            skipped.append(k)
        else:
            existing[k] = v
    after = len(existing)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"{item_type}: {before} -> {after} ({after-before} added, {len(skipped)} skipped)")
    return existing

def fix_accessory_levels(filepath):
    """Update all accessory min_level and add floorSpawnWeight."""
    with open(filepath, encoding='utf-8') as f:
        acc = json.load(f)

    curse_ids = {k for k, v in acc.items() if 'curse' in k or 'doom' in k or 'drain' in k}

    for k, v in acc.items():
        qt = v.get('quiz_tier', 1)
        if k in curse_ids:
            # Cursed items spawn anywhere
            v['min_level'] = 1
            v['floorSpawnWeight'] = {"1-20":60, "21-40":60, "41-60":40, "61-80":30, "81-100":20}
        else:
            min_l, peak_lo, peak_hi = ACC_TIER_MAP.get(qt, (1, 1, 60))
            v['min_level'] = min_l
            v['floorSpawnWeight'] = accessory_floor_spawn(min_l, peak_lo, peak_hi)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(acc, f, ensure_ascii=False, indent=2)

    # Report distribution
    by_tier = {}
    for v in acc.values():
        qt = v.get('quiz_tier', 1)
        by_tier[qt] = by_tier.get(qt, 0) + 1
    print(f"Accessories fixed: {len(acc)} total, tier distribution: {dict(sorted(by_tier.items()))}")

# Run everything
print("=== Item Overhaul ===")
add_items('items/weapon.json', NEW_WEAPONS, "Weapons")
add_items('items/armor.json',  NEW_ARMOR,   "Armor")
add_items('items/accessory.json', NEW_ACCESSORIES, "Accessories")
fix_accessory_levels('items/accessory.json')

# Final counts
for fname in ['weapon.json', 'armor.json', 'accessory.json', 'shield.json']:
    with open(f'items/{fname}', encoding='utf-8') as f:
        d = json.load(f)
    print(f"  {fname}: {len(d)} items")
