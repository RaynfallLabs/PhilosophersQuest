"""Enrich item JSON files with unidentified_name, lore, set data, and Philosopher's Amulet."""
import json

# ── Weapon unidentified names ──────────────────────────────────────────────
WEAPON_UNID = {
    # Swords
    'iron_sword':               'a dull-edged short blade',
    'iron_longsword':           'a heavy notched blade',
    'steel_sword':              'a polished short blade',
    'steel_longsword':          'a polished long blade',
    'hardened_gold_sword':      'a gleaming short blade',
    'hardened_gold_longsword':  'a gleaming long blade',
    'diamond_sword':            'a crystalline short blade',
    'diamond_longsword':        'a crystalline long blade',
    'adamantine_sword':         'an obsidian-dark short blade',
    'adamantine_longsword':     'an obsidian-dark long blade',
    # Daggers
    'iron_dagger':              'a rough-edged knife',
    'steel_dagger':             'a narrow stiletto',
    'hardened_gold_dagger':     'a gleaming narrow blade',
    'diamond_dagger':           'a crystalline dirk',
    'adamantine_dagger':        'a jet-dark needle blade',
    # Axes
    'iron_axe':                 'a pitted single-bit axe',
    'iron_greataxe':            'a heavy double-bit axe',
    'steel_axe':                'a smooth-helved war axe',
    'steel_greataxe':           'a balanced greataxe',
    'hardened_gold_axe':        'a gleaming single-bit axe',
    'hardened_gold_greataxe':   'a gleaming double-bit axe',
    'diamond_axe':              'a crystalline axe head',
    'diamond_greataxe':         'a massive crystalline axe',
    'adamantine_axe':           'a dark ore single-bit axe',
    'adamantine_greataxe':      'a dark ore greataxe',
    # Clubs / Hammers
    'wood_club':                'a rough wooden bludgeon',
    'wood_hammer':              'a crude wooden mallet',
    'hardwood_club':            'a dense dark-grained club',
    'hardwood_hammer':          'a dense dark-grained hammer',
    'ironwood_club':            'an iron-banded cudgel',
    'ironwood_hammer':          'an iron-banded maul',
    'diamond_club':             'a crystalline bludgeon',
    'diamond_hammer':           'a crystalline warhammer',
    'dragonbone_club':          'a pale ivory bludgeon',
    'dragonbone_hammer':        'a pale ivory warhammer',
    # Staves
    'wood_staff':               'a smooth wooden staff',
    'hardwood_staff':           'a dark-grained quarterstaff',
    'ironwood_staff':           'an iron-shod staff',
    'diamond_staff':            'a crystalline staff of inquiry',
    'dragonbone_staff':         'a pale ivory staff',
    # Spears / Polearms
    'iron_spear':               'a rough-shafted spear',
    'steel_spear':              'a balanced spear',
    'steel_glaive':             'a curved pole-blade',
    'hardened_gold_glaive':     'a gleaming pole-blade',
    'hardened_gold_halberd':    'a gleaming halberd',
    'diamond_halberd':          'a crystalline halberd',
    'adamantine_halberd':       'a dark ore halberd',
    'adamantine_glaive':        'a dark ore glaive',
    # Bows
    'wood_shortbow':            'a simple short bow',
    'wood_longbow':             'a simple long bow',
    'hardwood_shortbow':        'a dark-grained short bow',
    'hardwood_longbow':         'a dark-grained long bow',
    'ironwood_shortbow':        'an iron-tipped short bow',
    'ironwood_longbow':         'an iron-reinforced long bow',
    'diamond_shortbow':         'a crystalline short bow',
    'diamond_longbow':          'a crystalline long bow',
    'dragonbone_longbow':       'a pale ivory war bow',
    # Crossbows
    'iron_crossbow':            'a crude iron-framed crossbow',
    'steel_crossbow':           'a polished steel crossbow',
    'hardened_gold_crossbow':   'a gleaming crossbow',
    'diamond_crossbow':         'a crystalline crossbow',
    'adamantine_crossbow':      'a dark ore crossbow',
}

WEAPON_LORE = {
    'iron_sword': "The standard iron sword has been the companion of dungeon-delvers for centuries. Its modest weight and straightforward balance make it the weapon most beginners train with. There is no shame in iron — it has ended more monsters than all other metals combined.",
    'iron_longsword': "The iron longsword sacrifices speed for reach and leverage, allowing the wielder to deliver devastating cuts from a safer distance. Its fuller — the groove down the center — reduces weight while preserving structural integrity, a compromise that defines the blade's character.",
    'steel_sword': "Forged by a smith who understood the relationship between carbon content and edge retention, this steel sword holds its sharpness through extended combat. The quenching process leaves a faint wave pattern in the metal, visible in certain light.",
    'steel_longsword': "Steel longswords are the mark of the trained warrior — expensive to produce, requiring significant skill to wield effectively, but rewarding mastery with exceptional cutting power and durability. Armies that equip their veterans in steel are armies to be feared.",
    'hardened_gold_sword': "Hardened gold — an alchemical alloy developed by wizard-smiths — is denser than steel and holds enchantments more readily. The sword has a warm golden sheen that many describe as beautiful, which has led to the somewhat unfair reputation of 'decorative' weapons that are in fact highly lethal.",
    'hardened_gold_longsword': "A hardened gold longsword is the sign of serious investment in one's equipment. The alchemical alloy takes enchantments more readily than any mundane metal, and several famous enchanted swords were originally hardened gold longswords before their final treatment.",
    'diamond_sword': "Diamond weapons are not true gemstone — they are an artificially grown lattice of carbon, magically stabilized into metal-like properties. The edge is supernaturally sharp and difficult to damage. A diamond sword will outlast its wielder by generations.",
    'diamond_longsword': "Diamond longswords represent the pinnacle of non-magical weapon crafting. The growing process takes years and significant arcane investment. Warriors who carry diamond longswords are either very wealthy, very lucky, or both.",
    'adamantine_sword': "Adamantine — dark, dense, and supernaturally tough — was first discovered in meteorite craters. Weapons made from it resist magical damage and their edges self-heal minor nicks. An adamantine sword carries a quiet gravity that even non-magical beings can sense.",
    'adamantine_longsword': "The obsidian darkness of adamantine longswords is legendary. They do not merely cut — they consume. Scholars theorize that adamantine has properties aligned with the void between stars, giving it an almost supernatural ability to find weaknesses in armor and magical defenses.",
    'iron_dagger': "The iron dagger is the backup weapon of backup weapons — cheap, easy to conceal, and fast. Most adventurers carry at least one. Their small size means they can reach places larger weapons cannot, penetrating gaps in armor that would turn a sword.",
    'steel_dagger': "A well-made steel dagger is a precision instrument for close work. The narrow blade can slip between scale plates, pierce chain links, or find the gap beneath a helmet. Assassins prize the steel dagger for its balance of durability and discretion.",
    'hardened_gold_dagger': "A hardened gold dagger is a rarity — the alloy is expensive, and most smiths consider daggers too small to justify the cost. Those that exist are typically special commissions: assassination tools or dueling pieces where appearance matters as much as function.",
    'diamond_dagger': "Diamond daggers are made by artificially growing the blade around a microscopic structural crystal. The result is a blade of terrifying sharpness that can pierce materials that would blunt steel. They are also nearly impossible to detect with magical means — diamond is largely transparent to divination.",
    'adamantine_dagger': "An adamantine dagger is a fearsome thing to face in darkness. The blade absorbs ambient light, making it nearly invisible. It was from such a dagger that the legend of the 'shadow blade' originated — warriors who carried them appeared to strike with darkness itself.",
    'iron_axe': "The iron war axe is a practical weapon for practical people. It needs no precision — the weight and edge of the head do the work. Its single-bitted design allows the smith to concentrate the metal where it counts, producing a weapon of significant force.",
    'iron_greataxe': "The iron greataxe requires both hands and significant strength, but delivers blows capable of cleaving through light armor. It is the weapon of the unsubtle — there is no technique to speak of, only application of force, but applied correctly, force is enough.",
    'steel_axe': "A steel war axe has the reliability of iron with improved edge retention. The blade can be sharpened to a finer edge, improving its cutting depth significantly. Woodcutters sometimes mistake war axes for tools — an error they do not make twice.",
    'steel_greataxe': "The steel greataxe is balanced differently from its iron cousin — the longer handle and heavier head are carefully weighted to make the weapon feel lighter than it is. Experienced users generate tremendous momentum with relatively little effort.",
    'hardened_gold_axe': "A hardened gold war axe glows with warm light in dark places, a property of the alchemical alloy. Dungeon explorers find this either useful or dangerous depending on whether they prefer to see or be unseen.",
    'hardened_gold_greataxe': "The hardened gold greataxe is a statement of power, financial and otherwise. Its dense head concentrates force into the cutting edge with greater efficiency than iron or steel. Axe-fighters who can afford gold alloy rarely go back.",
    'diamond_axe': "Diamond axes grow along crystalline fracture lines, giving their edges a microscopic serration invisible to the naked eye. This gives them exceptional bite in any material, including stone and magical constructs.",
    'diamond_greataxe': "A diamond greataxe is a weapon of tremendous destructive potential. The self-sharpening nature of diamond crystal means this weapon never dulls, regardless of what it strikes. Museum curators who have examined recovered specimens cannot find a single flaw in the edge.",
    'adamantine_axe': "Adamantine holds an edge that resists all known means of dulling. An adamantine war axe used for a decade in constant combat will be as sharp as the day it was forged. The dark metal also resonates oddly with magic — enchantments applied to it are amplified.",
    'adamantine_greataxe': "The adamantine greataxe is a weapon that dungeons are built to stop. Its weight is extraordinary, requiring prodigious strength, but its ability to cleave through magical and physical barriers alike makes it the preferred instrument for demolishing doors, walls, and the creatures behind them.",
    'wood_club': "The humble wooden club has defended lives since before metallurgy. There is something philosophically satisfying about a weapon so ancient and so immediate. Its effectiveness is primitive and unsubtle, which makes it no less effective.",
    'wood_hammer': "A wooden hammer transmits force differently from a metal one — the grain absorbs some energy, then releases it in a slightly delayed pulse that can crack bone without necessarily breaking skin. Some fighters find this effect particularly useful against armored opponents.",
    'hardwood_club': "Dense hardwood clubs cut from the heartwood of iron-oak trees are nearly as heavy as iron while remaining organic. They flex slightly on impact, adding a whip-snap to blows that catches opponents off-guard.",
    'hardwood_hammer': "The iron-oak hardwood hammer was the weapon of choice for dwarven forge-workers before they adopted metal tools. The dense grain transmits vibrations in unusual ways — strikes feel dull but the force penetrates shields with remarkable efficiency.",
    'ironwood_club': "Ironwood clubs are reinforced at striking surfaces with iron bands, converting the organic impact of wood into something approaching a metal bludgeon. The hybrid nature makes them resist the rust and enchantment-stripping properties of some dungeon environments.",
    'ironwood_hammer': "The iron-banded ironwood maul combines the best properties of both materials. The wooden haft absorbs hand-shock on impact; the iron cap focuses force on a small point. Smiths and warriors alike respect its thoughtful engineering.",
    'diamond_club': "A crystalline bludgeon of diamond-lattice construction transmits force with almost no energy loss. The material does not compress — every joule of swing energy reaches the target. This makes diamond clubs disproportionately damaging for their apparent weight.",
    'diamond_hammer': "Diamond warhammers are forged by growing crystal around a weighted core. They can shatter stone, crack enchanted materials, and stun targets through heavy armor. Several dungeon bosses have met their end from the stunning blows of a diamond warhammer.",
    'dragonbone_club': "Dragonbone clubs are carved from the arm-bones of dragons — nearly as strong as metal, lighter, and warm to the touch. They retain a trace of the dragon's elemental nature; those made from fire dragon bones occasionally spark on heavy impact.",
    'dragonbone_hammer': "A dragonbone warhammer carries the dragon's weight in every sense. The density of dragon bone, combined with the immense striking surface of the hammer head, creates a weapon capable of physically stunning creatures far larger than its wielder.",
    'wood_staff': "The wooden staff is the first weapon of scholars and the last weapon of the old. Its length compensates for reach, its structure doubles as walking support, and its material accepts magical inscriptions readily. A wizard's staff is never merely a staff.",
    'hardwood_staff': "The dark-grained hardwood quarterstaff is heavier and more rigid than its plain-wood cousin, turning it from a walking aid into a genuine fighting weapon. Temple guards throughout history have preferred staves to swords for their versatility and the unmistakable authority they project.",
    'ironwood_staff': "An iron-shod staff bridges the gap between weapon and tool. The iron ends can be used as hooks, probes, or striking points, while the staff's length allows its user to check for traps before committing weight. It is the explorer's weapon.",
    'diamond_staff': "The Diamond Staff of Inquiry is said to have been first carried by a philosopher who descended into the dungeon seeking ultimate truth. The crystalline shaft channels magical understanding, granting its bearer enhanced insight. It is the first piece of the Philosopher's Set — the other pieces are the Philosopher's Ring and the Philosopher's Amulet. When all three are carried together, the wielder can identify items by touch alone, requiring no quiz.",
    'dragonbone_staff': "A dragonbone staff carries the spiritual residue of its origin. Dragons are ancient creatures with accumulated wisdom, and their bones retain this quality after death. Scholars believe dragonbone staves enhance concentration in ways no other material can match.",
    'iron_spear': "The iron spear is humanity's oldest dungeon weapon. Its reach keeps enemies at distance, and its point requires less precision than a sword edge. Iron spears break more often than steel, but iron is abundant and spear-making requires no great craft.",
    'steel_spear': "A balanced steel spear is a precision instrument when wielded by a trained user. The point penetrates where edges cannot, and the shaft can be used to parry or sweep. Spear-fighters can hold corridors against multiple opponents — the dungeon's geography rewards their reach.",
    'steel_glaive': "The glaive's curved blade at the end of a long pole allows for sweeping cuts as well as thrusting attacks. It requires more training than a spear and rewards the investment — a skilled glaive-user can attack in arcs that close the space between themselves and enemies.",
    'hardened_gold_glaive': "A hardened gold glaive glows faintly in darkness, a consequence of the alchemical alloy. This is both advantage and disadvantage — enemies can see it coming, but so can allies in urgent situations.",
    'hardened_gold_halberd': "The halberd combines axe, spear, and hook into a single weapon — versatile, intimidating, and effective against mounted and armored opponents. A hardened gold halberd adds the enchantment-readiness of the alloy to this already formidable package.",
    'diamond_halberd': "A diamond halberd's axe-blade grows along a crystalline structure that gives it a microscopically serrated edge invisible to the naked eye. This makes it exceptional against armor — the edge finds cracks and gaps that a smooth blade would slide over.",
    'adamantine_halberd': "An adamantine halberd is a weapon of war, not adventure. Its weight demands dedication to wield, but its ability to crack magical defenses and pierce any known armor makes it the choice of dungeon raiders who expect to face the hardest targets.",
    'adamantine_glaive': "The dark ore glaive sheds ambient light rather than reflecting it — a disconcerting visual effect that unnerves opponents. Its edge is self-maintaining; the adamantine structure realigns on a molecular level after each impact, keeping the blade perpetually sharp.",
    'wood_shortbow': "The simple short bow is the everyman's ranged weapon. Easily made, easily repaired, and capable of putting an arrow through a monster at forty feet — all the range most dungeon encounters require.",
    'wood_longbow': "A long bow's draw requires greater strength than a short bow, but delivers proportionally greater force at distance. Skilled long-bow archers can launch arrows that punch through light armor at range, and at close quarters the long bow is also an effective improvised club.",
    'hardwood_shortbow': "A dark-grained short bow holds its shape longer than plain wood, resisting the warping effects of dungeon humidity. Its draw weight is slightly higher, producing better arrow penetration than comparable lighter bows.",
    'hardwood_longbow': "Dense wood long bows are the choice of dungeon archers who expect extended use in varying conditions. The denser grain holds string tension more consistently, producing better accuracy over time.",
    'ironwood_shortbow': "The iron-reinforced short bow has metal tips at the limb ends to prevent stress fractures. This seemingly small improvement dramatically extends the bow's lifespan under hard use — an important consideration for explorers who can't easily replace equipment.",
    'ironwood_longbow': "Iron-reinforced long bows produce extraordinary arrow velocity for their draw weight. The metal tips act as counterweights, changing the bow's flex dynamics in ways that experienced archers learn to exploit for longer range and better precision.",
    'diamond_shortbow': "A crystalline short bow is an engineering marvel — the crystal lattice is flexible along one axis and rigid along another, allowing it to act as a perfect spring. Every joule of draw energy transfers cleanly to the arrow, with no vibration loss in the limbs.",
    'diamond_longbow': "A crystalline long bow can produce arrow velocities approaching the theoretical maximum for unpowered projectile weapons. The arrows whistle audibly in flight — a distinctive sound that some dungeon monsters have learned to fear.",
    'dragonbone_longbow': "A dragonbone war bow is reserved for elite archers — its draw weight exceeds what most humans can sustain for more than a few shots, but the arrows it launches strike with force approaching a crossbow. It is said to have been the weapon of choice of the legendary dragon-hunter Mira the Accurate.",
    'iron_crossbow': "The iron-framed crossbow is the entry point for projectile weapons — simple to use, requiring no archery training, and capable of significant damage at range. Its slow reload time is its primary weakness in fast-moving dungeon encounters.",
    'steel_crossbow': "A steel crossbow is a significant upgrade from iron — more durable, with a smoother action that reduces reload time. The precision of its parts allows for a heavier prod, producing greater arrow velocity.",
    'hardened_gold_crossbow': "A hardened gold crossbow incorporates the alchemical alloy's enchantment-affinity into its mechanism. Bolts fired from it carry magical charge slightly more efficiently than from standard crossbows, amplifying any enchantments on the ammunition.",
    'diamond_crossbow': "The mechanism of a diamond crossbow is a masterpiece of magical engineering — crystalline gears and cams that self-align after each shot, maintaining consistent draw force without adjustment. The bolts it fires can crack stone.",
    'adamantine_crossbow': "An adamantine crossbow fires its bolts with supernatural force. The dark metal mechanism stores more energy than any mundane material could, then releases it in a single explosive motion. Bolts from this weapon can punch through armor that would stop a ballistae bolt.",
}

ARMOR_UNID = {
    # Head
    'padded_coif':     'a rough-sewn coif',
    'leather_cap':     'a supple leather cap',
    'iron_helm':       'a dented iron helm',
    'chain_coif':      'a linked-ring coif',
    'steel_helm':      'a polished steel helm',
    'great_helm':      'a heavy full-face helm',
    'plate_helm':      'a heavy plate helm',
    'crystal_helm':    'a translucent helm',
    'dragonscale_helm':'an iridescent scale helm',
    'adamantine_helm': 'a jet-dark helm',
    # Body
    'cloth_armor':     'a rough-sewn tunic',
    'padded_armor':    'a quilted gambeson',
    'leather_armor':   'a supple leather coat',
    'ring_mail':       'a linked-ring coat',
    'scale_mail':      'an overlapping plate coat',
    'chain_mail':      'an interlocked ring hauberк',
    'banded_mail':     'a banded plate hauberk',
    'splint_mail':     'a splinted plate hauberk',
    'half_plate':      'a heavy plate breastplate',
    'full_plate':      'a full heavy plate suit',
    'crystal_plate':   'a translucent plate suit',
    'dragonscale_armor':'an iridescent scale suit',
    'adamantine_armor':'a jet-dark plate suit',
    # Arms
    'leather_bracers': 'supple leather arm guards',
    'iron_bracers':    'dented iron bracers',
    'steel_bracers':   'polished steel bracers',
    'plate_bracers':   'heavy plate bracers',
    'adamantine_bracers':'jet-dark bracers',
    # Hands
    'cloth_gloves':    'thin cloth gloves',
    'leather_gloves':  'supple leather gloves',
    'chain_gauntlets': 'linked-ring gauntlets',
    'steel_gauntlets': 'polished steel gauntlets',
    'plate_gauntlets': 'heavy plate gauntlets',
    'adamantine_gauntlets':'jet-dark gauntlets',
    # Legs
    'leather_leggings':'supple leather leggings',
    'chain_leggings':  'linked-ring leggings',
    'steel_greaves':   'polished steel greaves',
    'plate_greaves':   'heavy plate greaves',
    'adamantine_greaves':'jet-dark greaves',
    # Feet
    'leather_boots':   'supple leather boots',
    'iron_boots':      'heavy iron boots',
    'steel_boots':     'polished steel boots',
    'plate_boots':     'heavy plate boots',
    'adamantine_boots':'jet-dark armored boots',
    # Cloak
    'cloth_cloak':     'a tattered cloth cloak',
    'leather_cloak':   'a supple leather cloak',
    'ring_cloak':      'a weighted ring-mail cloak',
    'crystal_cloak':   'a translucent crystal cloak',
    'dragonscale_cloak':'an iridescent scale cloak',
    # Shirt (undershirt/base layer)
    'cloth_shirt':     'a rough-sewn base layer',
    'padded_shirt':    'a quilted base layer',
    'chain_shirt':     'a short linked-ring shirt',
    'mithril_shirt':   'a silvery light shirt',
    'adamantine_shirt':'a jet-dark base layer',
}

ARMOR_LORE = {
    'padded_coif': "A padded coif — a hood of thick quilted cloth — offers minimal protection but weighs almost nothing. Early dungeon explorers often wore these before they could afford metal, and the tradition persists in communities that value speed over defense.",
    'leather_cap': "A simple leather cap provides impact protection better than its humble appearance suggests. Tanned from bovine hide, it can deflect glancing blows from small creatures. Guards who need to move quickly prefer leather caps to heavier helms.",
    'iron_helm':   "The iron helm is the workhorse of dungeon headgear. Dented from use, still functional — it has absorbed blows that would have ended careers, and its wearer usually respects it for that. The neck guard protects the most vulnerable access point to the skull.",
    'chain_coif':  "A chain mail coif protects the head and neck in a way that solid helms cannot — the interlocking rings distribute impact across a wider area. It requires geography quiz mastery to equip properly, as fitting it correctly depends on understanding how its structure works.",
    'steel_helm':  "A polished steel helm is a significant upgrade in both protection and signaling — enemies who see it know they face a prepared opponent. The face guard can be raised or lowered, a flexibility that solid helms lack.",
    'great_helm':  "The great helm — a full-face cylinder of steel — is the heaviest head protection available. Visibility is limited to a narrow slit, which demands positional discipline from the wearer. In open dungeon corridors, its protection is worth the limitation.",
    'plate_helm':  "Plate helms represent the pinnacle of articulated steel head protection. Each curve and angle is calculated to deflect strikes away from critical structures. A good plate helm can protect against blows that would kill an unarmored person outright.",
    'crystal_helm': "Crystal plate helms grow from magically cultivated mineral matrices. The resulting material is transparent — the wearer sees normally — while providing physical protection approaching steel. They are disconcerting to face: the head of the wearer appears to float above an empty armor.",
    'dragonscale_helm': "Dragonscale helms are constructed from overlapping scales harvested carefully from dragon corpses. The iridescent surface shifts color in light, and the scales retain trace elemental resistances from the dragon's nature. Each helm takes months of skilled labor to assemble.",
    'adamantine_helm': "An adamantine helm absorbs even magical impact. The dark metal resists force at a level that baffles physicists — more energy goes into it than should be possible to store. The wearer of an adamantine helm can survive blows that would shatter plate steel.",
    'cloth_armor': "Cloth armor — a thick gambeson without quilting — offers the minimum viable protection. It cannot stop blades, but it absorbs impact and provides insulation against cold environments. Most serious adventurers wear it only as a base layer under heavier protection.",
    'padded_armor': "A quilted gambeson is a genuine armor used by experienced warriors — not merely a base layer. Its layered construction absorbs piercing attacks by catching weapon points between the quilted channels. Against blunt weapons it provides significant cushioning.",
    'leather_armor': "Leather armor, hardened by oil and heat treatment, is the adventurer's first real armor investment. Flexible enough for agile movement, protective enough for the first dungeon levels, and repairable with basic tools. Most experienced delvers remember their first leather coat with affection.",
    'ring_mail': "Ring mail — large rings sewn to a leather backing — was a transitional step between leather and chain. It is heavier than leather and lighter than chain, falling awkwardly between the two in protective value. Its primary advantage is that damaged rings can be individually replaced.",
    'scale_mail': "Scale mail mimics the armor of fish and dragon alike — overlapping plates that move with the body while presenting a deflecting surface. The scales must be worn in the right direction; reversed, they catch weapon strikes instead of deflecting them, a geography lesson about surface properties.",
    'chain_mail': "Chain mail has protected warriors for millennia. The interlocking rings distribute impact across the entire suit, converting cutting blows into bruising ones. Against piercing weapons it is less reliable — a focused point can slide between rings — but against slashing it is exceptional.",
    'banded_mail': "Banded mail augments chain with horizontal strips of metal that resist cutting. The bands are attached over the chain at the torso, protecting the most critical region. A compromise between the flexibility of chain and the rigidity of plate.",
    'splint_mail': "Splint mail replaces chain with vertical metal strips riveted to a leather backing. The result is heavier than chain but more resistant to the direct impacts common in dungeon combat. The strips flex slightly on movement, unlike full plate.",
    'half_plate': "Half plate armor covers the torso in solid steel plate while leaving the arms and legs in chain or leather. The coverage where it matters most, the mobility where it helps most. Warriors who have mastered geography can equip half plate efficiently.",
    'full_plate': "Full plate armor is the apex of mundane protection — every surface covered in articulated steel, crafted to the exact dimensions of the wearer's body. A fully armored knight in full plate is a walking fortress. The dungeon presents this armor its sternest test.",
    'crystal_plate': "Crystal plate grown by magical cultivation provides extraordinary protection in a material that appears fragile. The lattice structure distributes force across three-dimensional planes, making it more resistant to impact than its transparency suggests. Looking into crystal plate is looking into the future of armor.",
    'dragonscale_armor': "Dragonscale armor is the pride piece of any dungeon explorer's collection. The iridescent scales retain the elemental resistance of the dragon they came from — fire dragon scales resist fire, cold dragon scales resist cold. This suit is part of the Dragonslayer's Set. When worn alongside the Dragonbone Longsword and Dragonslayer's Ring, the wearer gains enhanced resistance to all elemental attacks.",
    'adamantine_armor': "Adamantine plate armor is the pinnacle of material protection. The dark metal resists magical and physical damage equally. Enchanters who have tried to curse adamantine armor report the enchantment simply does not stick — the metal rejects binding magic. The wearer of adamantine moves with the confidence of someone who knows the dungeon cannot hurt them.",
    'leather_bracers': "Leather bracers protect the forearm and wrist — essential for weapon users who don't want their striking arm nicked by deflected attacks. Simple, light, and effective, they're often the first armor piece a beginning delver adds to their outfit.",
    'iron_bracers': "Iron bracers were the warriors' choice before steel became common. Heavy on the forearm, but capable of blocking blade strikes in a way leather cannot match. Some fighters use their bracer-arm to actively block rather than dodge.",
    'steel_bracers': "Steel bracers offer real protection with manageable weight. Polished examples have a mirror finish that, in tight corridors, can reflect enough light to reveal approaching enemies — an accidental surveillance tool.",
    'plate_bracers': "Plate bracers cover the entire forearm in articulated steel. Combined with plate gauntlets, they form an arm that can absorb direct weapon strikes — fighters trained in active defense treat their armored forearm as a secondary shield.",
    'adamantine_bracers': "Adamantine bracers make the forearm nearly invulnerable. Fighters who specialize in parrying find that an adamantine bracer-block can damage the attacking weapon — a psychological advantage as much as a physical one.",
    'cloth_gloves': "Cloth gloves protect from friction and minor abrasion. They are not battle gloves, but in environments where bare hands would become raw quickly — rough stone walls, rope climbing — they are essential practical equipment.",
    'leather_gloves': "Leather gloves are a fighter's second skin. They improve grip in wet conditions, protect against blisters in extended combat, and provide minimal cut protection. Most serious dungeon fighters consider them part of the uniform rather than optional equipment.",
    'chain_gauntlets': "Chain gauntlets protect the hand while maintaining finger articulation. The linked rings allow full grip and weapon manipulation. Against bladed attacks, chain is superior to leather; against crushing attacks, less so.",
    'steel_gauntlets': "Steel gauntlets are the serious fighter's hand protection. The articulated knuckles allow full fist clenching, and the back of the hand is protected by curved plate. Warriors trained in grappling use their gauntlets as impact weapons in close quarters.",
    'plate_gauntlets': "Full plate gauntlets articulate at every finger joint, maintaining dexterity while providing maximum protection. The crafting precision required is extraordinary — each joint must be perfectly sized to the wearer's hand.",
    'adamantine_gauntlets': "Adamantine gauntlets make the wearer's hands nearly indestructible. A punch from an adamantine gauntlet is nearly as damaging as a weapon strike — the density of the metal concentrates impact into a small, devastating point.",
    'leather_leggings': "Leather leggings protect the leg in a way that allows full movement. The construction allows the fighter to kick without restriction while keeping the primary leg muscles safe from slashing attacks.",
    'chain_leggings': "Chain leggings add significant weight to the lower body but the protection they afford is substantial. Against weapons that tend to target the legs — low cuts, sweeps — chain is notably superior to leather.",
    'steel_greaves': "Steel greaves — leg armor in articulated plate — protect the shin, knee, and upper leg. Armor smiths pay particular attention to the knee guard, as knee injuries end careers. Properly fitted steel greaves distribute their weight well enough for extended dungeon exploration.",
    'plate_greaves': "Full plate leg armor is an engineering achievement. The articulated knee and ankle joints must allow full movement while protecting every surface. Warriors in plate greaves can march all day — the weight distribution compensates for the total mass.",
    'adamantine_greaves': "Adamantine leg armor is extraordinarily rare. The dark metal's weight on the legs would be prohibitive if not offset by its supernatural density properties, which produce greater protection than the volume would suggest. An enemy targeting the legs of an adamantine-clad warrior is wasting their time.",
    'leather_boots': "Leather boots are the dungeon explorer's most important mundane equipment. Quality boots mean the difference between a productive delving session and feet too painful to continue. These boots are well-constructed, their soles reinforced for rough terrain.",
    'iron_boots': "Iron boots are heavy, loud, and terrible for prolonged walking — but they protect the foot completely from the floor-based hazards common in the deeper dungeon. Rolling rocks, acidic puddles, and blade traps are equally irrelevant to the wearer of iron boots.",
    'steel_boots': "Steel boots represent the balance point in foot protection — heavy enough for real protection, light enough for extended wear. The articulated toe allows a natural step, preventing the shuffling gait of iron boot wearers.",
    'plate_boots': "Plate armor boots make the foot effectively invulnerable to floor-based damage. The articulated sole flexes naturally with each step. Veterans who have worn plate boots say returning to leather feels like walking without shoes.",
    'adamantine_boots': "Adamantine boots provide protection that borders on the metaphysical. The dark metal literally repels certain forms of magical damage that would penetrate even plate. Dungeon floors that activate under weight may simply not activate under the weight of adamantine.",
    'cloth_cloak': "A cloth cloak offers minimal physical protection but significant social and environmental utility — it can be used as a blanket, a signal flag, a stretcher, or a disguise. In the dungeon, its primary value is hiding armor from creatures that target heavily-armored opponents.",
    'leather_cloak': "A leather cloak has been treated to resist water and minor cuts. Dungeon explorers who spend time near underground lakes favor leather cloaks — they repel water indefinitely and dry without stiffening. Some fighters wear leather cloaks specifically to make grappling attacks slippery.",
    'ring_cloak': "A ring-mail weighted cloak is a fighting garment — the weighted hem can be used as a weapon to entangle opponents, and the metal rings provide meaningful cut resistance. It is heavier than a cloth cloak but far more useful in direct confrontations.",
    'crystal_cloak': "Crystal cloaks are woven from crystalline fibers, producing a garment that shimmers and refracts light. Beyond their beauty, they deflect low-energy magic — minor cantrips and weak wand blasts are scattered by the crystalline matrix before reaching the wearer.",
    'dragonscale_cloak': "A dragonscale cloak is an exceptional garment — flexible, protective, and striking in appearance. The iridescent scales shift color with movement, and their elemental properties make the wearer notably harder to harm with energy attacks. This is part of the Shadow Walker's Set. When paired with the Adamantine Dagger and Shadow Walker's Ring, the wearer gains exceptional stealth and resistance to poison damage.",
    'cloth_shirt': "A cloth undershirt provides friction reduction beneath armor — an often-overlooked comfort that affects combat endurance. Armor chafes without a proper base layer, and a fighter distracted by discomfort is a fighter making mistakes.",
    'padded_shirt': "A quilted undershirt provides more than comfort — the quilted channels absorb the shock transmitted through armor, reducing bruising from powerful blows. Experienced fighters who've worn padded shirts won't return to cloth.",
    'chain_shirt': "A chain shirt is a vest of interlocked rings, shorter than full chain mail, protecting the torso and upper arms. As a base layer under other armor, it adds meaningful protection; worn alone, it is suitable for the early dungeon levels.",
    'mithril_shirt': "Mithril — a legendary metal lighter than steel and nearly as hard as adamantine — produces shirts of remarkable protective value with minimal weight impact. The wearer often forgets it is there until the moment it saves their life. Its silvery appearance has led some to call it 'moonweave.'",
    'adamantine_shirt': "An adamantine base layer is a serious investment — the dark metal is expensive and difficult to work thin enough for a shirt. The result is protection that reduces damage even when other armor is bypassed. Wise fighters layer their defenses, and adamantine starts at the innermost layer.",
}

SHIELD_LORE = {
    'wooden_shield': "The wooden shield is the simplest barrier between a dungeon explorer and the things trying to hurt them. Reinforced with metal rim and boss, it is more durable than it appears. Shield fighters learn early that a parried blow is better than an armored one.",
    'iron_shield': "An iron shield is a genuine weapon-stopper. Its weight allows the fighter to lean into parries, using mass to redirect rather than deflect attacks. Iron is heavy enough that some fighters choose lighter shields for longer dungeon excursions.",
    'steel_shield': "A steel shield is the serious shield-fighter's tool of choice — light enough to maneuver aggressively, heavy enough to block effectively. The polished face can be angled to reflect torchlight, temporarily blinding opponents who charge from a distance.",
    'crystal_shield': "A crystal shield grows from a cultivated mineral matrix, producing a transparent barrier that provides protection while allowing the fighter to see through it. Opponents who cannot assess what is behind the shield must guess at exposed body sections, a significant tactical disadvantage.",
    'dragonscale_shield': "A shield assembled from overlapping dragon scales combines the flexibility of scale armor with the defensive properties of a rigid shield. The elemental resistance of the scales extends to the shield — attacks of the dragon's element glance off rather than strike home.",
    'adamantine_shield': "An adamantine shield is the definitive defensive tool. Its surface resists not just physical attacks but magical ones — enchanted blades find no purchase, elemental attacks dissipate on contact. Warriors who carry adamantine shields are not hoping to survive encounters; they are certain they will.",
}

SHIELD_UNID = {
    'wooden_shield':     'a scarred wooden shield',
    'iron_shield':       'a dented iron shield',
    'steel_shield':      'a polished round shield',
    'crystal_shield':    'a translucent shield',
    'dragonscale_shield':'an iridescent scale shield',
    'adamantine_shield': 'a jet-dark kite shield',
}

WAND_LORE = {
    'wand_of_healing': "Carved by forest druids from living oak, these wands channel healing energy from natural sources into the wielder's body. The green tinge to the wood fades with use, suggesting the stored energy is slowly depleted.",
    'wand_of_extra_healing': "A more potent healing wand, its bark stripped to reveal glowing grain beneath. Alchemists believe the additional power comes from treating the wood with concentrated restoration potions during the carving process.",
    'wand_of_restore_body': "The most powerful healing wand known, this object can reverse even severe physical trauma. It is said to have been developed by healer-mages studying the regenerative properties of troll tissue.",
    'wand_of_sleep': "A pale ash wand inscribed with spiraling somnolent runes. The sleep it induces is dreamless and complete — targets drop where they stand. First developed to manage dangerous dungeon creatures for study rather than combat.",
    'wand_of_deep_sleep': "An intensified sleep wand whose charges produce slumber that resists even physical stimulus to wake. Only magic can break the sleep it induces, making it invaluable when monsters need to be contained rather than killed.",
    'wand_of_slumber': "The most powerful sleep wand, capable of dropping even creatures resistant to mind effects. The runes inscribed on it directly target the autonomic nervous system rather than the conscious mind — even creatures with no mind to speak of are affected.",
    'wand_of_slow': "A leaden wand inscribed with temporal retardation sigils. Its effect subjectively passes normally for the target while objective time races by — the creature experiences normal thinking speed while its body operates at half-pace.",
    'wand_of_torpor': "A deep slowing effect that reduces targets to barely functional movement. The lethargic state feels like moving through thick oil — exhausting and dispiriting as well as physically limiting.",
    'wand_of_lethargy': "The most extreme slowing wand, reducing targets to near-immobility. Those affected describe it as a waking nightmare — fully conscious but incapable of meaningful physical action.",
    'wand_of_confusion': "A bent wand whose crooked shape reflects the disorientation it induces. Targets lose directional sense and spatial coherence, stumbling in random directions until the effect fades.",
    'wand_of_bewilderment': "An intensified confusion wand that produces deeper disorientation — targets may not recognize allies or even their own bodies. The runes on this wand are written in the same script used by certain ancient dream-priests.",
    'wand_of_madness': "The extreme end of confusion effects: targets enter a state of total cognitive collapse. Whether this is true madness or a temporary psychic displacement, the practical effect is identical — total combat ineffectiveness.",
    'wand_of_paralysis': "A rigid black wand that seizes voluntary muscle control in its targets. The effect is terrifying for the target, who remains fully conscious but physically locked in place. Paralysis wands are controversial for this reason.",
    'wand_of_petrification': "A stone-gray wand that induces progressive calcification in its target. Full petrification produces a perfect statue — the target is preserved exactly as they were, which some philosophers find disturbing to contemplate.",
    'wand_of_blindness': "A dark wand inscribed with eclipse symbols that temporarily suppresses the target's visual processing. The effect is not physical — the eyes are unharmed — but the optic processing is disrupted, producing total darkness for the target.",
    'wand_of_darkness': "A larger-effect version of the blindness wand, this object creates a zone of magical darkness around a target area that blocks all light including magical illumination. Dungeon fighters learned quickly not to use this in unfamiliar territory.",
    'wand_of_fear': "A trembling wand that transmits existential terror to its targets, triggering fight-or-flight response in favor of flight. The fear is not hallucination — it is a direct emotional state induced into the target's nervous system.",
    'wand_of_dread': "An intensified fear wand that produces deeper psychological distress. Targets affected by dread often flee in directions that take them further into danger, making this wand occasionally counterproductive.",
    'wand_of_terror': "The extreme fear wand — targets enter a state of panicked rout. The psychological signature this produces can linger as trauma even after the magical effect fades. Some dungeon scholars consider this one of the more ethically concerning wands.",
    'wand_of_charm_monster': "A softly glowing wand that projects a field of magical sympathy. Charmed monsters do not become allies exactly — they become convinced that the caster is a friend, which limits their hostility but does not guarantee cooperation.",
    'wand_of_domination': "An authoritative wand that imposes direct will on its target. Unlike charm, domination allows the caster to issue commands that will be followed. The subjugation is temporary, and targets remember the experience afterward with considerable resentment.",
    'wand_of_fire': "A heat-scarred wand that projects bolts of magical flame. The fire it produces burns hotter than natural fire and ignores moisture, making it effective even in the damp lower dungeon levels.",
    'wand_of_flame': "A wand producing sustained flame rather than single bolts — the fire stream can be swept across multiple targets. The design emerged from alchemists who studied the continuous fire production of fire-breathing creatures.",
    'wand_of_inferno': "The most devastating fire wand produces explosions of concentrated flame. The blast radius means users must maintain significant distance. Particularly effective against undead and creatures resistant to physical damage.",
    'wand_of_embers': "An unusual fire wand that produces slow-burning coals rather than active flame. The embers deal ongoing fire damage and are difficult to extinguish. Originally developed to mark positions in smoke-filled environments.",
    'wand_of_cold': "An ice-white wand that projects blasts of supercooled air, rapidly lowering the temperature of its target. Particularly effective against fire-based creatures and in reducing the effectiveness of poison in a target's system.",
    'wand_of_frost': "An extended-range cold wand that coats targets in frost, slowing them through temperature reduction as well as magical effect. Frost damage accumulates differently from fire damage — slower to appear, but longer-lasting.",
    'wand_of_ice': "This wand encases targets in ice, both damaging them and physically restraining them. The ice is magical and resists normal heat to melt it. Particularly brutal against creatures with fire-based biology.",
    'wand_of_glaciation': "The extreme cold wand can reduce temperatures in an area to levels that damage even cold-resistant targets. Its side effect — flash-freezing ambient moisture — creates icy floors that cause movement problems.",
    'wand_of_lightning': "A crackling wand that delivers lightning bolts with the force of a direct strike. Lightning wands are particularly dangerous to use in metal-reinforced dungeon sections, where the current chains unpredictably.",
    'wand_of_thunder': "A concussive lightning wand that produces thunderclaps alongside its electrical discharge. The sonic component stuns targets independently of the lightning — double threat from a single wand use.",
    'wand_of_storm': "A storm wand produces a localized electrical tempest — multiple lightning strikes in a small area. Extraordinarily effective against clustered targets. The electromagnetic disruption also interferes with certain magical effects.",
    'wand_of_acid': "A corrosive green wand that projects streams of magical acid. Particularly effective against armored targets — the acid dissolves metal and degrades magical enchantments on armor before beginning to damage the wearer.",
    'wand_of_corrosion': "An intensified acid wand that produces acid specifically designed to attack magical bindings as well as physical material. Enchanted items struck by corrosion wand effects often lose their enchantment entirely.",
    'wand_of_dissolution': "The extreme acid wand produces a substance that dissolves virtually any material. Particularly effective against constructs and golems, whose magical bodies have no special resistance to chemical attack.",
    'wand_of_magic_missile': "A simple but reliable wand projecting bolts of pure magical force. Unlike elemental wands, magic missiles are not resisted by elemental resistances — what they lack in spectacular effect they compensate with universal applicability.",
    'wand_of_force': "Larger magic missiles that produce visible impact waves on contact. Against physically resistant targets — stone golems, iron constructs — force wands are significantly more effective than elemental alternatives.",
    'wand_of_annihilation': "The extreme force wand produces blasts of pure destructive energy. Targets are not burned, frozen, or shocked — they are simply reduced. The precision of the effect means it works equally against any physical target.",
    'wand_of_striking': "A physical impact wand that projects kinetic force rather than magical energy. Particularly effective against magically resistant targets that shrug off enchantment-based damage.",
    'wand_of_crushing': "An intensified striking wand that produces enough force to break bones through armor. The impact wave can knock targets back, potentially off edges or into other hazards.",
    'wand_of_smiting': "The extreme striking wand produces impacts approaching those of boulders. Used by some dungeon explorers as a structural demolition tool as well as a weapon.",
    'wand_of_drain_life': "A black wand that extracts life force from targets and transfers some of it to the wielder. The drain causes weakness and exhaustion in targets; the return provides the wielder with temporary vitality.",
    'wand_of_vampirism': "An intensified life drain wand that extracts vitality more efficiently. Wielders report feeling temporarily invigorated after use — the feeling passes, but it makes this wand popular despite the ethical concerns it raises.",
    'wand_of_death': "The extreme drain wand can strip vitality entirely from a target. Against powerful undead — which have no natural vitality — this effect is limited, but against living targets it is one of the most feared wand effects in existence.",
    'wand_of_stoning': "A wand specialized for inducing petrification in a targeted manner. Unlike the more general petrification wand, this focuses the effect for more rapid transformation.",
    'wand_of_disintegration': "The most destructive targeted wand — its discharge unravels the molecular structure of the target. The process is not gradual; disintegration occurs in a fraction of a second. What remains is dust.",
    'wand_of_speed': "A quickening wand that accelerates the target's nervous system and muscle response. The wielder acts and reacts faster while the wand's effect lasts. The energy cost to the body is significant — hunger follows.",
    'wand_of_swiftness': "An intensified speed wand that produces near-precognitive reaction speed. Targets of this wand appear to others as moving in short bursts — there are gaps in their movement that the eye cannot follow.",
    'wand_of_invisibility': "A translucent wand that bends light around the target, rendering them optically invisible. It does not suppress sound or scent, leaving the invisible user detectable through other means to creatures that rely on them.",
    'wand_of_concealment': "An intensified invisibility wand that additionally suppresses sound and reduces scent, making the user genuinely difficult to detect through most mundane means.",
    'wand_of_levitation': "A feather-light wand that counters gravity on the target. Levitation is controlled by thought but requires practice — untrained users often find themselves drifting rather than navigating purposefully.",
    'wand_of_flight': "An intensified levitation wand that provides true directed flight. Users report that the sensation differs from levitation — there is a sense of push behind the movement rather than absence of weight.",
    'wand_of_teleport': "A wand that folds space around the wielder, moving them instantly to a random nearby location. The destination is not fully controlled, making this a wand of last resort rather than tactical transport.",
    'wand_of_shielding': "A protective wand that generates a brief field of force around the wielder, deflecting incoming attacks. The field is stronger against fast-moving projectiles than slow-moving melee weapons.",
    'wand_of_stoneskin': "A hardening wand that temporarily increases the density of the target's skin to stone-like properties. The effect reduces damage from all physical attacks while active.",
    'wand_of_fire_shield': "A wand that wraps the wielder in a thin layer of protective flame. Melee attackers take fire damage when they strike the shielded target. The heat makes this wand inadvisable in environments with flammable materials.",
    'wand_of_cold_shield': "A wand that envelops the wielder in a shell of cold air. Melee attackers take cold damage; the chill also slightly slows the nervous conduction of attackers, making their strikes marginally less effective.",
    'wand_of_empowerment': "A wand that temporarily amplifies the wielder's physical capabilities, providing a surge of strength and endurance. The effect is popular with warriors who encounter unexpected challenges.",
    'wand_of_fortitude': "An intensified empowerment wand that provides greater physical enhancement. The physiological stress it places on the body means it should not be used frequently.",
    'wand_of_acuity': "A wand that temporarily sharpens mental processing, improving focus and reaction time. Quiz timers feel extended to wielders — not because time slows, but because the mind moves faster.",
    'wand_of_digging': "A useful exploration wand that disintegrates stone. Dungeon explorers use digging wands to open new passages, bypass locked doors, and escape enclosed spaces.",
    'wand_of_tunneling': "An intensified digging wand that moves more material per charge. Skilled users can carve entire room outlines in a few uses.",
    'wand_of_light': "A wand that produces bright illumination, revealing hidden features of dungeon walls and floors. Useful for detecting traps and secret passages. The light has a pinkish quality that some find soothing.",
    'wand_of_illumination': "An intensified light wand that produces sunlight-equivalent illumination. Effective against creatures that avoid or are damaged by sunlight.",
    'wand_of_cancellation': "A null-field wand that temporarily suppresses magical effects on its target. Useful for dispelling ongoing enchantments or neutralizing magically protected creatures.",
    'wand_of_negation': "An intensified cancellation wand that can suppress even deeply rooted magical effects, including permanent enchantments for a brief period.",
    'wand_of_create_monster': "A chaotic wand that draws creatures from elsewhere — monsters appear from thin air near the target area. The type of monster summoned is somewhat random, making this wand dangerous to use in small spaces.",
    'wand_of_summoning': "An intensified create monster wand that draws more powerful creatures. The summoned monsters are not under the wand user's control.",
    'wand_of_detect_monster': "A sensing wand that reveals the position of nearby monsters as a psychic impression. The range and precision of detection improves with quiz performance.",
    'wand_of_detect_treasure': "A sensing wand that locates valuable objects in the surrounding area. Some treasure is magically shielded and not detectable; this wand finds mundane valuables and many magical ones.",
    'wand_of_mapping': "A wand that produces a psychic map impression of the current dungeon level. The detail level depends on quiz performance — full success reveals the complete layout.",
    'wand_of_clairvoyance': "An intensified mapping wand that reveals not just the layout but the contents of nearby areas — monsters, items, and hazards visible as psychic impressions.",
    'wand_of_polymorph': "A wand of radical transformation that changes the physical form of its target. The new form is random. Polymorphed creatures retain their original intellect but have the physical capabilities of their new form.",
    'wand_of_transmutation': "A focused polymorph wand that transforms targets into specific categories of creature. The caster has more influence over the outcome with this wand than with the basic polymorph.",
    'wand_of_identify': "A wand that reveals the true nature of unknown items. Unlike the Philosopher's Amulet method, this wand requires no quiz — it simply reveals. Charges are limited, making the amulet superior for regular identification.",
    'wand_of_enchantment': "A wand that adds a magical bonus to any item it strikes. The enchantment is additive with existing magical properties. Artificers prize these wands for equipment improvement.",
    'wand_of_curse': "A wand that binds a malefic enchantment to a targeted item or creature. Cursed items cannot be removed by normal means; cursed creatures suffer ongoing penalties.",
    'wand_of_teleport_monster': "A repositioning wand that moves a targeted monster to a random location. Useful for separating grouped enemies or removing a specific threat from immediate range.",
    'wand_of_poison': "A toxin wand that injects magical poison into its target, causing ongoing damage. The poison bypasses physical armor entirely — it must be resisted biochemically.",
    'wand_of_venom': "An intensified poison wand producing more virulent toxins. Targets that resist normal poison sometimes succumb to venom wand effects.",
    'wand_of_plague': "The extreme poison wand introduces a magically-induced disease state rather than simple toxin. The disease progresses over multiple turns.",
    'wand_of_disease': "A wand that induces specific disease states rather than simple poison. Different disease effects target different biological systems.",
    'wand_of_rot': "A wand that accelerates biological decay in living targets. Against undead this effect is irrelevant; against living creatures it is deeply unpleasant.",
    'wand_of_regeneration': "A healing wand that operates continuously over time rather than instantly, allowing the body to rebuild at an accelerated rate. The regeneration can close wounds faster than combat opens them.",
    'wand_of_vitality': "An intensified regeneration wand that produces faster healing and also counteracts ongoing negative effects like poison and disease.",
    'wand_of_earthquake': "A devastating environmental wand that induces ground tremors in the target area. In dungeon environments this can cause structural collapse, making it extremely dangerous to use.",
    'wand_of_explosion': "An area-effect force wand that produces a small explosion centered on the target point. The blast affects everything in range regardless of allegiance.",
    'wand_of_drain_magic': "A wand that absorbs magical energy from targets, depleting wands, scrolls, and enchantments they carry. Against magically-sustained creatures it deals direct damage.",
    'wand_of_dispelling': "An intensified magic drain that completely removes ongoing enchantments from targets. Useful for dispelling beneficial effects on enemies or removing curses.",
    'wand_of_aging': "A disturbing wand that accelerates the aging process in living targets. Aging effects manifest as progressive weakening.",
    'wand_of_withering': "An intensified aging wand that produces rapid physical deterioration. The effect is reversible with restoration magic but terrifying to experience.",
    'wand_of_time_stop': "One of the rarest wands, capable of briefly halting time for everything except the wielder. In that frozen moment, the wielder can act freely. The temporal stress costs charges rapidly.",
    'wand_of_wishing': "The legendary wand — able to grant a genuine wish to the wielder. The scope of the wish is limited by the wand's power level, and overreaching causes the wand to produce unintended results. Experienced users ask for specific, modest things.",
    'wand_of_reflection': "A mirrored wand that creates a barrier that reflects magical attacks back at their source. Particularly effective against wand-wielding monsters.",
    'wand_of_mirroring': "An intensified reflection wand that reflects both magical and physical projectiles. The barrier is visible as a shimmer, allowing tactical use as a partial shield.",
    'wand_of_phasing': "A wand that temporarily makes the wielder partially non-physical, allowing them to pass through solid objects. The phased state is unstable — extended use is dangerous.",
    'wand_of_ethereality': "An intensified phasing wand that produces complete non-physical state, allowing passage through any material and immunity to physical attacks during the effect.",
    'wand_of_mass_confusion': "An area effect confusion wand affecting all targets in range simultaneously. Useful for escaping surrounded situations.",
    'wand_of_mass_sleep': "An area effect sleep wand that can drop entire groups of opponents simultaneously. One of the most tactically useful wands for non-combat exploration.",
    'wand_of_mass_slow': "An area effect slowing wand that significantly reduces the speed of all targets in range. Creates windows of safety for a group.",
}

# Accessory lore (for items that don't have it already)
# Only the ones without lore in existing JSON
ACCESSORY_LORE_ADDITIONS = {
    # Ring of warning variants (same lore for all)
    'ring_warning_oak': "The ring of warning was developed by scouts who needed advance notice of ambushes. The enchantment creates a persistent field of spatial awareness — the wearer never loses the sense of being watched that heralds a monster's presence. Different material variants hold the same enchantment.",
    # Philosopher's Set pieces
    'philosophers_ring': "Forged by a philosopher-king who spent a decade in the dungeon, this ring sharpens perceptual acuity to the point where the true nature of objects becomes apparent through mere sustained observation. It is the second piece of the Philosopher's Set. When combined with the Philosopher's Amulet and the Diamond Staff of Inquiry, all items become immediately identifiable by touch.",
    'dragonslayer_ring': "This ring was designed as a companion to the Dragonslayer's armor and blade, providing elemental resistance to complete the set. It resonates with draconic energy, and dragons — who can sense magical objects — react to its wearer with a mixture of recognition and hostility. It is the third piece of the Dragonslayer's Set.",
    'shadow_walker_ring': "A ring favored by those who move in darkness — it suppresses the wearer's presence in ways beyond mere invisibility. The ring is the third piece of the Shadow Walker's Set; when combined with the Adamantine Dagger and Dragonscale Cloak, the wearer becomes effectively undetectable in shadows.",
}

PHILOSOPHERS_AMULET = {
    "name": "Philosopher's Amulet",
    "symbol": "\"",
    "color": [220, 180, 40],
    "weight": 0.1,
    "min_level": 1,
    "slot": "amulet",
    "equip_threshold": 1,
    "quiz_tier": 1,
    "effects": {"status": "identify_sight", "duration": -1},
    "unidentified_name": "Philosopher's Amulet",
    "identified": True,
    "set_id": "philosophers",
    "set_name": "The Philosopher's Set",
    "lore": "This golden amulet is engraved with the ouroboros — the serpent devouring its own tail, symbol of eternal knowledge. It is said to have belonged to the first philosopher who descended into the dungeon seeking ultimate truth. The amulet resonates with philosophical understanding, allowing its wearer to identify the true nature of unknown items through rigorous examination. As one of three pieces of the Philosopher's Set, wearing it alongside the Philosopher's Ring and the Diamond Staff of Inquiry grants the ability to identify items simply by touching them.",
    "item_class": "accessory",
    "id": "philosophers_amulet"
}

PHILOSOPHERS_RING = {
    "name": "Philosopher's Ring",
    "symbol": "=",
    "color": [200, 170, 40],
    "weight": 0.1,
    "min_level": 6,
    "slot": "ring",
    "equip_threshold": 3,
    "quiz_tier": 3,
    "effects": {"bonus": "quiz_time", "amount": 5, "duration": -1},
    "unidentified_name": "a golden engraved ring",
    "identified": False,
    "set_id": "philosophers",
    "set_name": "The Philosopher's Set",
    "lore": "Forged by a philosopher-king who spent a decade in the dungeon, this ring sharpens perceptual acuity to the point where the true nature of objects becomes apparent through mere sustained observation. The wearer gains 5 additional seconds on all quiz timers — time spent in genuine contemplation. It is the second piece of the Philosopher's Set. When combined with the Philosopher's Amulet and the Diamond Staff of Inquiry, all items become immediately identifiable by touch."
}

DRAGONSLAYER_RING = {
    "name": "Dragonslayer's Ring",
    "symbol": "=",
    "color": [220, 80, 30],
    "weight": 0.1,
    "min_level": 12,
    "slot": "ring",
    "equip_threshold": 4,
    "quiz_tier": 4,
    "effects": {"resistance": "fire", "amount": 0.5, "duration": -1},
    "unidentified_name": "a fire-warmed iron ring",
    "identified": False,
    "set_id": "dragonslayer",
    "set_name": "The Dragonslayer's Set",
    "lore": "This ring was designed as a companion to the Dragonslayer's armor and blade, providing elemental resistance to complete the set. It resonates with draconic energy, and dragons react to its wearer with recognition and hostility. It is the third piece of the Dragonslayer's Set — when combined with the Dragonbone Longsword and Dragonscale Armor, the wearer gains exceptional resistance to all elemental attacks and enhanced damage against dragons."
}

SHADOW_WALKER_RING = {
    "name": "Shadow Walker's Ring",
    "symbol": "=",
    "color": [60, 40, 80],
    "weight": 0.1,
    "min_level": 10,
    "slot": "ring",
    "equip_threshold": 4,
    "quiz_tier": 4,
    "effects": {"status": "invisible", "duration": -1},
    "unidentified_name": "a dark obsidian band",
    "identified": False,
    "set_id": "shadow_walker",
    "set_name": "The Shadow Walker's Set",
    "lore": "A ring favored by those who move in darkness — it suppresses the wearer's presence in ways beyond mere invisibility. The ring naturally warms in the presence of poison, a property its original owner used to detect assassination attempts. It is the third piece of the Shadow Walker's Set; combined with the Adamantine Dagger and Dragonscale Cloak, the wearer becomes effectively undetectable in shadows and gains immunity to poison."
}

# Set data for existing items
SET_ADDITIONS = {
    'dragonbone_longsword': {'set_id': 'dragonslayer', 'set_name': 'The Dragonslayer\'s Set'},
    'dragonscale_armor': {'set_id': 'dragonslayer', 'set_name': 'The Dragonslayer\'s Set'},
    'adamantine_dagger': {'set_id': 'shadow_walker', 'set_name': 'The Shadow Walker\'s Set'},
    'dragonscale_cloak': {'set_id': 'shadow_walker', 'set_name': 'The Shadow Walker\'s Set'},
    'diamond_staff': {'set_id': 'philosophers', 'set_name': 'The Philosopher\'s Set'},
}

def patch_file(path, unid_map=None, lore_map=None, set_map=None, quiz_tier_map=None, extra_items=None):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    changed = 0
    for item_id, item in data.items():
        # unidentified_name
        if unid_map and item_id in unid_map and 'unidentified_name' not in item:
            item['unidentified_name'] = unid_map[item_id]
            changed += 1
        # lore
        if lore_map and item_id in lore_map and 'lore' not in item:
            item['lore'] = lore_map[item_id]
            changed += 1
        # set data
        if set_map and item_id in set_map:
            for k, v in set_map[item_id].items():
                if k not in item:
                    item[k] = v
                    changed += 1
        # quiz_tier
        if quiz_tier_map and item_id in quiz_tier_map and 'quiz_tier' not in item:
            item['quiz_tier'] = quiz_tier_map[item_id]
            changed += 1

    if extra_items:
        for item_id, item_data in extra_items.items():
            if item_id not in data:
                data[item_id] = item_data
                changed += 1

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  {path}: +{changed} changes")
    return changed


def main():
    base = 'data/items/'
    total = 0

    # Weapons
    wqtier = {
        'iron_sword': 1, 'iron_longsword': 1, 'iron_dagger': 1, 'iron_axe': 1, 'iron_greataxe': 1,
        'iron_spear': 1, 'iron_crossbow': 1, 'wood_club': 1, 'wood_hammer': 1, 'wood_staff': 1,
        'wood_shortbow': 1, 'wood_longbow': 1,
        'steel_sword': 2, 'steel_longsword': 2, 'steel_dagger': 2, 'steel_axe': 2, 'steel_greataxe': 2,
        'steel_spear': 2, 'steel_glaive': 2, 'steel_crossbow': 2, 'hardwood_club': 2, 'hardwood_hammer': 2,
        'hardwood_staff': 2, 'hardwood_shortbow': 2, 'hardwood_longbow': 2,
        'hardened_gold_sword': 3, 'hardened_gold_longsword': 3, 'hardened_gold_dagger': 3,
        'hardened_gold_axe': 3, 'hardened_gold_greataxe': 3, 'hardened_gold_glaive': 3,
        'hardened_gold_halberd': 3, 'hardened_gold_crossbow': 3, 'ironwood_club': 3, 'ironwood_hammer': 3,
        'ironwood_staff': 3, 'ironwood_shortbow': 3, 'ironwood_longbow': 3,
        'diamond_sword': 4, 'diamond_longsword': 4, 'diamond_dagger': 4, 'diamond_axe': 4,
        'diamond_greataxe': 4, 'diamond_halberd': 4, 'diamond_crossbow': 4, 'diamond_club': 4,
        'diamond_hammer': 4, 'diamond_staff': 4, 'diamond_shortbow': 4, 'diamond_longbow': 4,
        'adamantine_sword': 5, 'adamantine_longsword': 5, 'adamantine_dagger': 5, 'adamantine_axe': 5,
        'adamantine_greataxe': 5, 'adamantine_halberd': 5, 'adamantine_glaive': 5, 'adamantine_crossbow': 5,
        'dragonbone_club': 5, 'dragonbone_hammer': 5, 'dragonbone_staff': 5, 'dragonbone_longbow': 5,
    }
    total += patch_file(base+'weapon.json', WEAPON_UNID, WEAPON_LORE, SET_ADDITIONS, wqtier)

    # Armor
    aqtier = {
        'cloth_armor': 1, 'padded_coif': 1, 'cloth_gloves': 1, 'cloth_cloak': 1, 'cloth_shirt': 1,
        'padded_armor': 1, 'padded_shirt': 1, 'leather_cap': 1, 'leather_armor': 1,
        'leather_bracers': 1, 'leather_gloves': 1, 'leather_leggings': 1, 'leather_boots': 1, 'leather_cloak': 1,
        'ring_mail': 2, 'iron_helm': 2, 'iron_bracers': 2, 'iron_boots': 2, 'ring_cloak': 2,
        'scale_mail': 2, 'chain_coif': 2, 'chain_gauntlets': 2, 'chain_leggings': 2, 'chain_shirt': 2,
        'steel_helm': 3, 'steel_bracers': 3, 'steel_boots': 3, 'steel_gauntlets': 3, 'steel_greaves': 3,
        'chain_mail': 3, 'banded_mail': 3, 'splint_mail': 3,
        'half_plate': 4, 'full_plate': 4, 'plate_helm': 4, 'plate_bracers': 4, 'plate_gauntlets': 4,
        'plate_greaves': 4, 'plate_boots': 4, 'mithril_shirt': 4, 'crystal_cloak': 4,
        'great_helm': 4,
        'crystal_helm': 5, 'crystal_plate': 5, 'dragonscale_helm': 5, 'dragonscale_armor': 5,
        'dragonscale_cloak': 5, 'adamantine_helm': 5, 'adamantine_armor': 5, 'adamantine_bracers': 5,
        'adamantine_gauntlets': 5, 'adamantine_greaves': 5, 'adamantine_boots': 5, 'adamantine_shirt': 5,
    }
    total += patch_file(base+'armor.json', ARMOR_UNID, ARMOR_LORE, SET_ADDITIONS, aqtier)

    # Shields
    sqtier = {
        'wooden_shield': 1, 'iron_shield': 2, 'steel_shield': 3,
        'crystal_shield': 4, 'dragonscale_shield': 5, 'adamantine_shield': 5,
    }
    total += patch_file(base+'shield.json', SHIELD_UNID, SHIELD_LORE, None, sqtier)

    # Wands (already have unidentified_name, add lore)
    total += patch_file(base+'wand.json', None, WAND_LORE)

    # Accessories: add Philosopher's Amulet + new rings + lore additions
    acc_extra = {
        'philosophers_amulet': PHILOSOPHERS_AMULET,
        'philosophers_ring': PHILOSOPHERS_RING,
        'dragonslayer_ring': DRAGONSLAYER_RING,
        'shadow_walker_ring': SHADOW_WALKER_RING,
    }
    # Add lore to all accessories that have effects but no lore
    # (accessory lore is optional; the effect description serves)
    total += patch_file(base+'accessory.json', None, ACCESSORY_LORE_ADDITIONS,
                        None, None, acc_extra)

    print(f"\nTotal changes: {total}")


if __name__ == '__main__':
    main()
