import json

with open('data/hints.json', encoding='utf-8') as f:
    hints = json.load(f)

tier3_additions = [
    "There are rare, powerful creatures that don't follow the dungeon's normal rules \u2014 they appear only once per descent, if at all. Treat their appearance as both a warning and an opportunity.",
    "A spider of unusual size and cunning lurks in the early depths. Her web immobilizes even armored warriors. Fire clears it faster than any blade.",
    "Something half-woman and half-serpent has been reported in the depths \u2014 she drains the warmth from those she embraces. She cannot abide fire or holy energy.",
    "A bronze giant walks slowly through certain levels, shrugging off every arrow and blade. Travelers who survived say only blunt weapons left any mark, and a strange ankle wound finally felled it.",
    "A serpent-woman who mothers all monsters poisons with every bite. Those who have faced her and lived wear protection against venom without exception.",
    "Reports of a forest spirit that lures wanderers to their doom \u2014 iron weapons and torches seem to disturb it. Do not follow the music.",
    "A bat-god from the underworld has been seen blinding adventurers with its wings. Holy energy or lightning seems to hurt it where conventional arms do not."
]

tier4_additions = [
    "A riddle-asking guardian has been encountered around level 35. It offers a test before combat \u2014 those who pass gain an advantage; those who fail suffer for it.",
    "A fire-breathing giant son of a forge god roams the mid-depths. Cold attacks cut through its resistance; its fire breath is devastating at close range.",
    "The invulnerable lion of ancient myth appears in the dungeon. Blades and arrows are useless \u2014 it resists both entirely. Only crushing blows can harm it.",
    "A Slavic iron-toothed witch heals as she fights and bites through armor. Iron and fire are her weaknesses \u2014 carry both if you enter her level.",
    "A great serpent juvenile has been reported near the 55th level. Its venom is the most potent in the dungeon. Lightning and fire can wound it; nothing else reaches.",
    "A chaos witch around level 40 drains magical power from those she touches. Stock up on MP before her floor. Holy and fire damage are effective.",
    "An Egyptian jackal-servant drains life with shadow attacks. It dwells in darkness and is immune to drain itself. Holy attacks and lightning are your tools."
]

tier5_additions = [
    "The Green Knight cannot be stopped by conventional means \u2014 he regenerates constantly. Fire or powerful magic are the only ways to stop his healing. Focus damage and push through.",
    "The great whirlpool beast pulls you toward it every turn. Lightning deals heavy damage to it. Do not stand still \u2014 keep moving or its maw will grind you to nothing.",
    "A severed arm of the demon king Ravana attacks three times each round. Fire and holy damage are its weaknesses. It can paralyze \u2014 carry a wand of dispel or a potion of freedom.",
    "The Wendigo drains stamina at terrifying speed \u2014 you will begin to starve mid-fight. Fire is its only true weakness. Eat before engaging and carry food.",
    "The Wild Hunt Captain leads spectral riders. Iron weapons penetrate his defenses; holy energy disrupts his phantom nature. He is fast \u2014 do not let him surround you.",
    "Anansi never fights fairly. He confuses and poisons, teleporting his prey into disorientation. Fire burns his webs. Lightning disrupts his trickery. Do not trust your footing.",
    "A fragment of N\u00ed\u00f0h\u00f6ggr carries acid that ignores most armor. Holy damage and lightning hurt it. Its poison is near-permanent without magical remedy \u2014 bring a wand of cure."
]

hints['3'].extend(tier3_additions)
hints['4'].extend(tier4_additions)
hints['5'].extend(tier5_additions)

with open('data/hints.json', 'w', encoding='utf-8') as f:
    json.dump(hints, f, indent=2, ensure_ascii=False)

print('hints.json updated')
for k in hints:
    print(f'  Tier {k}: {len(hints[k])} hints')
