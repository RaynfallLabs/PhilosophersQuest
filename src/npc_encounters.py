"""
NPC moral encounter system — 30 encounters across 10 level blocks.

Flow: bump NPC → encounter text (ENTER) → 3 options (1-3) → outcome (ENTER).
Options show action + justification only — no outcomes, no karma labels.
The player is never cruel; even selfish options are framed as pragmatic necessity.
One encounter guaranteed per 10-level block, chosen from 3 candidates.
"""
import random

# Boss levels where NPCs cannot spawn
_BOSS_LEVELS = frozenset({20, 40, 60, 80, 100})

# Level blocks: (block_number, min_level, max_level)
_BLOCKS = [
    (1,  3,  9),
    (2,  11, 19),
    (3,  21, 29),
    (4,  31, 39),
    (5,  41, 49),
    (6,  51, 59),
    (7,  61, 69),
    (8,  71, 79),
    (9,  81, 89),
    (10, 91, 98),
]

# ── Encounter definitions ──────────────────────────────────────────────
#
# Each encounter has:
#   tag         - unique id (prevents duplicates per run)
#   name        - NPC display name
#   symbol      - tile character
#   color       - RGB tuple
#   block       - which 10-level block (1-10)
#   trigger_item - (optional) item_id that spawns 1-3 levels before NPC
#   trigger_level_offset - (optional) how many levels before NPC the item spawns
#   text        - encounter description (screen 1)
#   options     - list of dicts:
#       label   - what the player sees (screen 2), NO outcomes
#       karma   - -1, 0, or +1
#       outcome - shown after selection (screen 3)
#       cost    - dict or None  (what the good/neutral deed costs)
#       reward  - dict or None  (what the selfish choice gains)
#
# Cost types:
#   {'type': 'food'}              - give 1 Food (inventory selection)
#   {'type': 'healing_potion'}    - give 1 healing potion (inventory selection)
#   {'type': 'potion'}            - give 1 potion, any kind (inventory selection)
#   {'type': 'scroll'}            - give 1 scroll (inventory selection)
#   {'type': 'weapon'}            - give 1 weapon (inventory selection)
#   {'type': 'gold', 'amount': N} - pay N gold
#   {'type': 'hp_percent', 'amount': N}   - lose N% of current HP
#   {'type': 'max_hp', 'amount': N}       - lose N max HP permanently
#   {'type': 'sp', 'amount': N}           - lose N stamina
#   {'type': 'triggered_item'}            - return the trigger item
#   {'type': 'accept_item', 'item_id': X} - receive a cursed/burden item
#
# Reward types:
#   {'type': 'gold', 'min': A, 'max': B}
#   {'type': 'random_weapon'}
#   {'type': 'random_armor'}
#   {'type': 'random_shield'}
#   {'type': 'random_accessory'}
#   {'type': 'random_potion', 'count': N}
#   {'type': 'random_scroll', 'count': N}
#   {'type': 'random_food', 'count': N}
#   {'type': 'stat', 'stat': 'CON', 'amount': N}
#   {'type': 'specific_item', 'item_type': 'weapon', 'item_id': X}
#   {'type': 'multi', 'rewards': [...]}

ENCOUNTERS = [

    # ── BLOCK 1: Levels 3-9 ──────────────────────────────────────────

    {
        'tag': 'elara_amulet',
        'name': 'Lost Girl',
        'symbol': '@',
        'color': (200, 180, 220),
        'block': 1,
        'trigger_item': 'silverlight_pendant',
        'trigger_level_offset': 1,
        'text': (
            "A girl no older than seven sits against the wall, hugging her "
            "knees. She sees the pendant around your neck and her whole body "
            "goes rigid. \"That's my mama's. She gave it to me before she "
            "went away. I dropped it when the rats came.\" She pulls a "
            "burnished silver ring from her finger and holds it out with "
            "trembling hands. \"You can have this. Please. It's all I have "
            "left of her.\""
        ),
        'options': [
            {
                'label': "Give her the pendant — it belongs to her",
                'karma': +1,
                'outcome': (
                    "She presses the pendant to her chest and squeezes her "
                    "eyes shut. She doesn't say thank you. She doesn't need "
                    "to. She runs for the stairs clutching it in both hands, "
                    "and you can hear her sobbing with relief long after "
                    "she's gone."
                ),
                'cost': {'type': 'triggered_item'},
                'reward': None,
            },
            {
                'label': "Return it, but accept her ring — she offered",
                'karma': 0,
                'outcome': (
                    "\"Thank you, mister. Thank you.\" She tugs the ring "
                    "from her finger and presses it into your hand with "
                    "fierce insistence, then clutches the pendant and runs. "
                    "The ring is warm from her hand."
                ),
                'cost': {'type': 'triggered_item'},
                'reward': {'type': 'specific_item', 'item_type': 'accessory',
                           'item_id': 'elaras_silver_ring',
                           'no_auto_identify': True},
            },
            {
                'label': "Keep it — you need every advantage to survive",
                'karma': -1,
                'outcome': (
                    "\"I'm sorry, little one. I need this or I will die "
                    "down here.\" She doesn't argue. She doesn't cry. She "
                    "just watches you walk away, her empty hands still "
                    "outstretched."
                ),
                'cost': None,
                'reward': None,
            },
        ],
    },

    {
        'tag': 'brother_aldous',
        'name': 'Dying Monk',
        'symbol': '@',
        'color': (160, 130, 90),
        'block': 1,
        'text': (
            "A monk in a filthy brown robe crawls on his hands and knees. "
            "His tonsured head is covered in sores and his eyes are so "
            "sunken they seem to belong to a skull. He points to his "
            "mouth, then clasps his hands in prayer. He is too weak to "
            "speak. A silver reliquary hangs from his neck — a saint's "
            "fingerbone set in gold."
        ),
        'options': [
            {
                'label': "Give him food from your pack",
                'karma': +1,
                'outcome': (
                    "He weeps as he eats, making the sign of the cross "
                    "over and over. He cannot speak, but he grips your "
                    "hand with both of his and will not let go for a "
                    "long time."
                ),
                'cost': {'type': 'food'},
                'reward': None,
            },
            {
                'label': "You have nothing to spare — you are sorry",
                'karma': 0,
                'outcome': (
                    "He nods. He understands. He keeps crawling toward "
                    "the stairs, one hand over the other, impossibly slow."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take the reliquary — you need it more right now",
                'karma': -1,
                'outcome': (
                    "He clutches at it, but his fingers have no strength. "
                    "He doesn't cry — he's past crying. He just lets his "
                    "hands fall and stares at the floor."
                ),
                'cost': None,
                'reward': {'type': 'specific_item', 'item_type': 'accessory',
                           'item_id': 'saints_reliquary'},
            },
        ],
    },

    {
        'tag': 'marta_ratchatcher',
        'name': 'Rat-Catcher',
        'symbol': '@',
        'color': (140, 130, 110),
        'block': 1,
        'text': (
            "A wiry woman sits with her leg splinted between two torches. "
            "\"Compound fracture,\" she says through gritted teeth. \"Set "
            "it myself, but the bleeding won't stop. I've got a daughter "
            "up top who thinks I'm indestructible.\" She looks at you. "
            "\"I'm not.\" Her satchel holds vials of rare alchemical "
            "compounds."
        ),
        'options': [
            {
                'label': "Give her a healing potion to stop the bleeding",
                'karma': +1,
                'outcome': (
                    "She drinks, and color slowly returns to her face. "
                    "\"I owe you a life. My daughter's name is Lena. If "
                    "you ever make it out, find her. Tell her Marta's "
                    "coming home.\""
                ),
                'cost': {'type': 'healing_potion'},
                'reward': None,
            },
            {
                'label': "You can't spare your supplies — hold pressure",
                'karma': 0,
                'outcome': (
                    "\"Maybe someone else will come.\" She presses harder "
                    "on the wound. You both know no one else is coming."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take her satchel — those compounds could save you",
                'karma': -1,
                'outcome': (
                    "\"My daughter's name is Lena,\" she says quietly. "
                    "\"In case you ever develop a conscience.\" The "
                    "compounds are professional-grade."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'random_potion', 'count': 2},
                    {'type': 'random_food', 'count': 1},
                ]},
            },
        ],
    },

    # ── BLOCK 2: Levels 11-19 ────────────────────────────────────────

    {
        'tag': 'sir_aldric',
        'name': 'Burdened Knight',
        'symbol': '@',
        'color': (160, 160, 180),
        'block': 2,
        'text': (
            "A knight kneels in the corridor, crushed under a massive "
            "black stone lashed to his pack — a Cursed Lodestone. In his "
            "hands he cradles a crystal vial of shimmering liquid. \"My "
            "wife Elspeth is dying. This cordial is her only hope. But "
            "this stone — I cannot put it down. It grows heavier with "
            "every step.\" He looks up, red-eyed. \"If you take the stone "
            "willingly, the curse transfers. I know what I'm asking.\""
        ),
        'options': [
            {
                'label': "Take the lodestone — his wife deserves to live",
                'karma': +1,
                'outcome': (
                    "The stone settles into your pack like a dead thing. "
                    "Twenty pounds of useless, cursed rock. Sir Aldric "
                    "rises, tears streaming, and runs for the stairs "
                    "without looking back. You can feel the curse settling "
                    "in. It isn't going anywhere."
                ),
                'cost': {'type': 'accept_item', 'item_id': 'cursed_lodestone'},
                'reward': None,
            },
            {
                'label': "You cannot carry that burden — you are sorry",
                'karma': 0,
                'outcome': (
                    "\"I know. God forgive me, I know.\" He stays on his "
                    "knees. You can still hear the stone grinding against "
                    "his armor as you walk away."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take the cordial — you need it more",
                'karma': -1,
                'outcome': (
                    "\"I'm sorry, Sir Knight. I wish there were another "
                    "way.\" He stares at you. He knows there is another "
                    "way. He just watched you choose not to take it. "
                    "Warmth floods your body as you drink."
                ),
                'cost': None,
                'reward': {'type': 'stat', 'stat': 'CON', 'amount': 1},
            },
        ],
    },

    {
        'tag': 'tam_thief',
        'name': 'Young Thief',
        'symbol': '@',
        'color': (180, 160, 130),
        'block': 2,
        'text': (
            "A boy — fourteen at most — is backed against a dead end, "
            "shaking so hard the stolen coins in his arms clink together. "
            "One eye is swollen shut and his ribs show through a torn "
            "shirt. \"Don't hit me. I know I stole. But Rosie hasn't "
            "eaten in four days. She's eight. She doesn't understand "
            "why her stomach hurts.\""
        ),
        'options': [
            {
                'label': "Give him food for his sister",
                'karma': +1,
                'outcome': (
                    "He stares at the food like he's never seen such a "
                    "thing. \"For Rosie?\" he asks. Then, quieter: "
                    "\"Can I have some too?\" You tell him yes."
                ),
                'cost': {'type': 'food'},
                'reward': None,
            },
            {
                'label': "Let him go — you have nothing to spare",
                'karma': 0,
                'outcome': (
                    "\"Go. Quickly.\" He scrambles away, dropping coins "
                    "as he runs. Whether Rosie eats tonight is beyond "
                    "your control."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "He stole those from someone — take them",
                'karma': -1,
                'outcome': (
                    "He doesn't fight. He just sets everything down, "
                    "carefully, and backs away. \"Tell Rosie I tried,\" "
                    "he whispers. Among the stolen goods is a surprisingly "
                    "fine piece of equipment."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'gold', 'min': 60, 'max': 100},
                    {'type': 'random_weapon'},
                ]},
            },
        ],
    },

    {
        'tag': 'helena_cartographer',
        'name': 'Injured Scholar',
        'symbol': '@',
        'color': (160, 140, 180),
        'block': 2,
        'text': (
            "A young woman in spectacles sits surrounded by meticulous "
            "dungeon maps. Her left arm hangs at a wrong angle and the "
            "side of her face is purple from a fall. \"Twelve years I've "
            "been mapping this place. The Academy said a woman couldn't "
            "survive down here alone.\" She winces. \"I need something "
            "for the pain or I can't hold the pen. The pen is all I have.\""
        ),
        'options': [
            {
                'label': "Give her a healing potion for the arm",
                'karma': +1,
                'outcome': (
                    "She drinks and flexes her drawing hand with a gasp "
                    "of relief. \"I will put your name on the map. Right "
                    "here. 'A good person stood here.'\""
                ),
                'cost': {'type': 'healing_potion'},
                'reward': None,
            },
            {
                'label': "You need your supplies — you are sorry, Helena",
                'karma': 0,
                'outcome': (
                    "She nods sharply. \"Then go. I've survived worse.\" "
                    "She picks up the pen with her good hand and keeps "
                    "drawing, teeth clenched."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take the maps — they're worth a fortune",
                'karma': -1,
                'outcome': (
                    "\"No — that's my life's work! TWELVE YEARS!\" She "
                    "grabs at them with her one good arm, but you're "
                    "stronger. Among the scrolls are some with arcane "
                    "markings."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'random_scroll', 'count': 1},
                    {'type': 'gold', 'min': 150, 'max': 200},
                ]},
            },
        ],
    },

    # ── BLOCK 3: Levels 21-29 ────────────────────────────────────────

    {
        'tag': 'marcus_sword',
        'name': 'Grieving Father',
        'symbol': '@',
        'color': (140, 130, 120),
        'block': 3,
        'trigger_item': 'oathkeeper_sword',
        'trigger_level_offset': 2,
        'text': (
            "An old soldier sits on a fallen pillar, holding a child's "
            "blanket faded almost white. He sees the sword on your hip "
            "and stands so fast his knees crack. \"That's my boy's sword. "
            "Vale. He came down here six months ago to prove himself.\" "
            "His hands shake. \"He didn't come back. Did you find him? "
            "Was there a body?\" There wasn't."
        ),
        'options': [
            {
                'label': "Give him the sword — it belongs to his son",
                'karma': +1,
                'outcome': (
                    "Marcus holds the sword against his chest and closes "
                    "his eyes. \"He was a good boy. He was such a good "
                    "boy.\" He walks toward the stairs, clutching the "
                    "sword and the blanket. He doesn't look back."
                ),
                'cost': {'type': 'triggered_item'},
                'reward': None,
            },
            {
                'label': "Return it, but accept his coin — for your trouble",
                'karma': 0,
                'outcome': (
                    "\"Take this. For bringing me closure.\" He presses "
                    "coins into your hand and holds the sword to his "
                    "chest. \"I'll bring him home now. Both pieces of him.\""
                ),
                'cost': {'type': 'triggered_item'},
                'reward': {'type': 'gold', 'min': 50, 'max': 80},
            },
            {
                'label': "Keep it — you need this weapon to survive",
                'karma': -1,
                'outcome': (
                    "\"I found no such blade, old man.\" Marcus looks at "
                    "the sword on your hip. He reads the name VALE on "
                    "the crossguard. He knows you're lying. He sits back "
                    "down and stares at the blanket in his hands."
                ),
                'cost': None,
                'reward': None,
            },
        ],
    },

    {
        'tag': 'blinded_soldier',
        'name': 'Blinded Soldier',
        'symbol': '@',
        'color': (160, 150, 140),
        'block': 3,
        'text': (
            "A soldier in Legion armor sits with both hands clamped over "
            "his eyes. Blood seeps between his fingers. An acid trap. "
            "\"I can't see,\" he says flatly. \"Both eyes. If I had "
            "something to flush them — a healing potion, anything — I "
            "might save one. I have a wife. She has green eyes. I would "
            "like to see green eyes again.\""
        ),
        'options': [
            {
                'label': "Give him a healing potion for his eyes",
                'karma': +1,
                'outcome': (
                    "He pours it over his ruined eyes, screaming through "
                    "clenched teeth. When it's over, one eye opens. "
                    "Milky, damaged — but open. \"Green,\" he whispers. "
                    "\"I can still see green.\""
                ),
                'cost': {'type': 'healing_potion'},
                'reward': None,
            },
            {
                'label': "You can't spare it — you are sorry, soldier",
                'karma': 0,
                'outcome': (
                    "\"Understood. Move along.\" His jaw is clenched so "
                    "hard the muscles stand out like cords. He sits in "
                    "the dark and waits for no one."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take his gear — he can't use it now",
                'karma': -1,
                'outcome': (
                    "He hears you unbuckling his pack. He doesn't resist. "
                    "\"I hope you needed it, friend,\" he says. The word "
                    "'friend' cuts deeper than it should. His Legion plate "
                    "is well-maintained."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'random_armor'},
                    {'type': 'gold', 'min': 100, 'max': 150},
                ]},
            },
        ],
    },

    {
        'tag': 'dying_messenger',
        'name': 'Dying Courier',
        'symbol': '@',
        'color': (150, 130, 110),
        'block': 3,
        'text': (
            "A young man in a courier's jerkin lies on his side, a "
            "crossbow bolt in his back. One hand reaches for a sealed "
            "iron scroll case just out of reach. \"The Captain needs "
            "this. Troop positions. For the siege. Thousands will die "
            "if it doesn't get there.\" His fingers scrape the stone. "
            "\"Please. Take it up. Swear to me.\""
        ),
        'options': [
            {
                'label': "Take the dispatch — you swear to deliver it",
                'karma': +1,
                'outcome': (
                    "The iron case settles into your pack like a promise. "
                    "It's heavy and useless to you, but the courier smiles "
                    "and closes his eyes. \"Thank you. Tell them Edric "
                    "made it almost all the way.\""
                ),
                'cost': {'type': 'accept_item', 'item_id': 'sealed_dispatch'},
                'reward': None,
            },
            {
                'label': "You can't take that weight — you are sorry",
                'karma': 0,
                'outcome': (
                    "\"I understand. Just — if you see anyone else...\" "
                    "He trails off. The scroll case lies on the floor "
                    "between you. You step around it."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take his supplies — he won't need them now",
                'karma': -1,
                'outcome': (
                    "His healing draught was pinned under his body — he "
                    "never even knew it was there. His coin pouch is "
                    "heavy with hazard pay. He watches you step over the "
                    "scroll case. \"Thousands,\" he whispers."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'gold', 'min': 80, 'max': 120},
                    {'type': 'random_potion', 'count': 1},
                ]},
            },
        ],
    },

    {
        'tag': 'deadite_woman',
        'name': 'Moaning Woman',
        'symbol': '@',
        'color': (160, 160, 210),
        'block': 3,
        'text': (
            "A woman is slumped against the wall, moaning in pain. Her "
            "long dark hair hangs over her face, and her body shudders "
            "with each ragged breath. One hand clutches her stomach. "
            "She doesn't look up as you approach."
        ),
        'options': [
            {
                'label': "Kneel down and try to help her",
                'karma': +1,
                'outcome': (
                    "You reach out to move her hair aside — and her head "
                    "snaps up. The face underneath is grey and rotting, the "
                    "eyes pure white. \"I'LL SWALLOW YOUR SOUL!\" she "
                    "shrieks, and rakes you across the chest before you "
                    "can react. You stumble back, bleeding. She was dead "
                    "the whole time."
                ),
                'cost': {'type': 'spawn_deadite_ambush'},
                'reward': None,
            },
            {
                'label': "Walk away — you can't help this woman",
                'karma': 0,
                'outcome': (
                    "You give the moaning figure a wide berth. Something "
                    "about the way she moves doesn't sit right. As you "
                    "round the corner, the moaning stops. When you glance "
                    "back, she's gone."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "\"It's a trick. Get an ax.\"",
                'karma': +1,
                'outcome': (
                    "You draw your weapon and approach carefully. The "
                    "\"woman\" springs up with inhuman speed, grey flesh "
                    "splitting into a horrible grin — but you were ready. "
                    "One clean strike and it's over. The Deadite crumples "
                    "to the floor, truly dead this time. You wipe your "
                    "blade clean. Sometimes paranoia pays off."
                ),
                'cost': None,
                'reward': {'type': 'gold', 'min': 30, 'max': 60},
            },
        ],
    },

    # ── BLOCK 4: Levels 31-39 ────────────────────────────────────────

    {
        'tag': 'sister_marguerite',
        'name': 'Starving Nun',
        'symbol': '@',
        'color': (200, 200, 210),
        'block': 4,
        'text': (
            "A nun in a white habit kneels before a makeshift altar of "
            "dungeon stones. She is skeletal — her habit hangs off her "
            "like a tent. \"I was called here to minister to the lost "
            "souls of this dungeon. I have given away everything I "
            "carried. Every scrap, every coin.\" She smiles. \"But now "
            "there is no one left to minister to me.\" The altar is "
            "decorated with offerings — coins, trinkets, a golden ring."
        ),
        'options': [
            {
                'label': "Give her food — she has given enough already",
                'karma': +1,
                'outcome': (
                    "She eats slowly, savoring each bite as though it "
                    "were communion. \"You have fed Christ's servant. "
                    "He will remember.\" Her eyes are bright with "
                    "gratitude and something that might be hope."
                ),
                'cost': {'type': 'food'},
                'reward': None,
            },
            {
                'label': "You will pray for her, but cannot spare food",
                'karma': 0,
                'outcome': (
                    "\"Then we will pray for each other.\" She bows her "
                    "head. Her lips move silently. You move on."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take the altar offerings — she won't miss them",
                'karma': -1,
                'outcome': (
                    "\"Those were given in love,\" she says quietly. You "
                    "take them anyway. Among the trinkets is a finely "
                    "crafted ring that someone once treasured."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'random_accessory'},
                    {'type': 'gold', 'min': 80, 'max': 120},
                ]},
            },
        ],
    },

    {
        'tag': 'chained_priest',
        'name': 'Chained Priest',
        'symbol': '@',
        'color': (180, 170, 140),
        'block': 4,
        'text': (
            "A priest hangs from manacles bolted to the wall, his robes "
            "torn, his body covered in ritual cuts. \"Cultists. They "
            "needed a consecrated soul for their ritual.\" He manages a "
            "ghastly smile. \"The manacles are arcane — a scroll's "
            "magic can overload the binding. Any scroll. Please. I have "
            "a parish. People depend on me.\" Behind him, the cultists "
            "left a chest of ritual components."
        ),
        'options': [
            {
                'label': "Use a scroll to break the binding",
                'karma': +1,
                'outcome': (
                    "The manacles flash and fall open. The priest drops "
                    "to his knees, then to his face. \"Thank God. Thank "
                    "God and thank you.\" He rises slowly and walks "
                    "toward the stairs."
                ),
                'cost': {'type': 'scroll'},
                'reward': None,
            },
            {
                'label': "You have no scrolls to spare — you are sorry",
                'karma': 0,
                'outcome': (
                    "\"Hurry, then. The cultists return at dark.\" He "
                    "closes his eyes. You hope someone else comes."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Open the ritual chest — the cultists won't return",
                'karma': -1,
                'outcome': (
                    "\"You would leave a man in chains to rob his "
                    "jailers?\" Yes. The chest holds dark things, but "
                    "valuable ones."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'random_scroll', 'count': 1},
                    {'type': 'random_potion', 'count': 1},
                    {'type': 'gold', 'min': 100, 'max': 150},
                ]},
            },
        ],
    },

    {
        'tag': 'old_konstantin',
        'name': 'Old Warrior',
        'symbol': '@',
        'color': (150, 140, 130),
        'block': 4,
        'text': (
            "An ancient warrior sits sharpening a broken sword. Around "
            "the corner, something large growls. \"They'll be here in "
            "ten minutes. I've been holding this corridor for three days. "
            "There are people behind me — mushroom farmers. Good people.\" "
            "He tests the broken blade and shakes his head. \"My sword "
            "broke this morning. Without a weapon...\" He shrugs. "
            "\"The math gets unfavorable.\""
        ),
        'options': [
            {
                'label': "Give him a weapon — those people need him",
                'karma': +1,
                'outcome': (
                    "He takes it, tests the weight, nods once. \"This'll "
                    "do. Go on, now. I've got work.\" You hear the first "
                    "clash of steel before you reach the next corridor. "
                    "He's holding."
                ),
                'cost': {'type': 'weapon'},
                'reward': None,
            },
            {
                'label': "You can't give up your weapon — you are sorry",
                'karma': 0,
                'outcome': (
                    "\"Understood. No hard feelings.\" He picks up the "
                    "broken sword and faces the corridor. \"I'll manage.\""
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take his pack — he's focused on the fight ahead",
                'karma': -1,
                'outcome': (
                    "He doesn't notice — his eyes are on the darkness. "
                    "His pack holds his life savings from forty years "
                    "of dungeon work. He'll find out after the fight. "
                    "If he survives it."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'gold', 'min': 150, 'max': 200},
                    {'type': 'random_accessory'},
                ]},
            },
        ],
    },

    # ── BLOCK 5: Levels 41-49 ────────────────────────────────────────

    {
        'tag': 'apprentice_healer',
        'name': 'Poisoned Herbalist',
        'symbol': '@',
        'color': (120, 180, 120),
        'block': 5,
        'text': (
            "A young woman in an herbalist's apron sits surrounded by "
            "labeled jars of dried herbs. Her hands shake and black "
            "veins creep up her neck. \"Thornwick Blossom. Cures "
            "infections surface medicine can't touch. For the children's "
            "ward.\" She steadies her hand. \"One pricked me. The toxin "
            "reaches my brain in six hours. Any potion — the liquid "
            "medium can dilute it.\""
        ),
        'options': [
            {
                'label': "Give her a potion — the children need her",
                'karma': +1,
                'outcome': (
                    "She mixes it with something from her kit and drinks. "
                    "The shaking stops almost immediately. \"The children "
                    "at Saint Elara's will never know your name. But I "
                    "will.\""
                ),
                'cost': {'type': 'potion'},
                'reward': None,
            },
            {
                'label': "You need your supplies — is there another way?",
                'karma': 0,
                'outcome': (
                    "\"It has to be an alchemical base. Water won't bind "
                    "the toxin.\" She looks at her shaking hands. \"I "
                    "have about five hours to find something else.\""
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take the herb collection — it's priceless",
                'karma': -1,
                'outcome': (
                    "\"Those are for sick children!\" She's too weak to "
                    "stop you. The jars clink in your pack. They contain "
                    "compounds any alchemist would kill for."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'random_potion', 'count': 2},
                    {'type': 'random_food', 'count': 1},
                ]},
            },
        ],
    },

    {
        'tag': 'ghost_grave',
        'name': 'Ghost of Edwin',
        'symbol': '@',
        'color': (160, 180, 200),
        'block': 5,
        'text': (
            "A cairn of stacked stones marks a grave. Above it, "
            "scratched into the wall: \"HERE LIES EDWIN. HE DESERVED "
            "BETTER.\" A ghost stands before it — broad-shouldered, "
            "still wearing the wounds that killed him. \"My partner. "
            "We fought together seven years. He pushed me behind him.\" "
            "He looks at you. \"A living offering on his grave will let "
            "me rest. It hurts. I won't lie.\""
        ),
        'options': [
            {
                'label': "Bleed for him — a proper burial rite",
                'karma': +1,
                'outcome': (
                    "You cut your palm and let the blood fall on the "
                    "cairn. Pain lances through you, far worse than a "
                    "cut should feel. The cairn glows warm. The ghost "
                    "smiles. \"Thank you. We'll be together now.\" He "
                    "dissolves into gentle light."
                ),
                'cost': {'type': 'max_hp', 'amount': 15},
                'reward': None,
            },
            {
                'label': "You honor his memory, but you cannot bleed",
                'karma': 0,
                'outcome': (
                    "\"Not everyone can.\" The ghost looks at the cairn. "
                    "\"I'll stand here. I don't mind. He's worth standing "
                    "for.\""
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take the stash hidden in the cairn",
                'karma': -1,
                'outcome': (
                    "You pull the stones apart. The ghost screams — not "
                    "anger, heartbreak. \"HIS GRAVE! YOU'VE BROKEN HIS "
                    "GRAVE!\" He sinks to his knees over the scattered "
                    "stones. Edwin's stash was meant for no one."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'gold', 'min': 150, 'max': 200},
                    {'type': 'random_accessory'},
                ]},
            },
        ],
    },

    {
        'tag': 'deserter',
        'name': 'Legion Deserter',
        'symbol': '@',
        'color': (140, 140, 130),
        'block': 5,
        'text': (
            "A young soldier sits in the dark, knees drawn up, still "
            "wearing his torn Legion tabard. His hands won't stop "
            "shaking. \"Something came out of the dark. A hundred of us. "
            "I was the only one who ran.\" He stares at his hands. "
            "\"I just need food. Enough to reach the surface. I'll "
            "disappear.\" A gold officer's signet ring gleams on his "
            "finger — he couldn't bring himself to remove it."
        ),
        'options': [
            {
                'label': "Give him food — everyone deserves to eat",
                'karma': +1,
                'outcome': (
                    "He eats like an animal, then stops, ashamed. \"I "
                    "don't deserve this kindness.\" You tell him Rosie "
                    "— whoever Rosie is — would want him to eat. He "
                    "doesn't understand. He cries anyway."
                ),
                'cost': {'type': 'food'},
                'reward': None,
            },
            {
                'label': "You have nothing to spare — the stairs are east",
                'karma': 0,
                'outcome': (
                    "\"Yes sir.\" He stands mechanically and walks the "
                    "direction you pointed. He doesn't ask again."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take the signet — that's worth a year's wages",
                'karma': -1,
                'outcome': (
                    "He stares at the ring. Pulls it off. \"Take it. "
                    "Take everything. I don't deserve any of it.\" The "
                    "ring is solid gold, officer-grade, finely crafted."
                ),
                'cost': None,
                'reward': {'type': 'specific_item', 'item_type': 'accessory',
                           'item_id': 'officers_signet'},
            },
        ],
    },

    # ── BLOCK 6: Levels 51-59 ────────────────────────────────────────

    {
        'tag': 'blind_seer',
        'name': 'Blind Seer',
        'symbol': '@',
        'color': (180, 170, 200),
        'block': 6,
        'text': (
            "An ancient woman sits before candles that never burn down, "
            "surrounded by scrolls and clay jars arranged with obsessive "
            "precision. A silk blindfold covers empty sockets. She turns "
            "toward you before you make a sound. \"I know your heartbeat. "
            "You carry weight.\" She extends a paper-thin hand. \"I have "
            "not eaten in... I forget how long. Will you share a meal? "
            "I am so tired of being alone.\""
        ),
        'options': [
            {
                'label': "Share food with her — no one should be alone",
                'karma': +1,
                'outcome': (
                    "She eats slowly, telling stories from before you "
                    "were born. For a few minutes the darkness feels "
                    "warm. \"You have a good heart,\" she says. \"I "
                    "can hear it.\""
                ),
                'cost': {'type': 'food'},
                'reward': None,
            },
            {
                'label': "You cannot stay — you are sorry, Cassandra",
                'karma': 0,
                'outcome': (
                    "\"Everyone says that.\" She lowers her hand. \"Go. "
                    "I will be here when the next one comes. And the "
                    "next.\""
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take her scrolls — she can't see them anyway",
                'karma': -1,
                'outcome': (
                    "She feels the empty spaces where her things were. "
                    "Her mouth opens. Closes. She folds both hands in "
                    "her lap. The silence is worse than screaming."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'random_scroll', 'count': 2},
                    {'type': 'random_potion', 'count': 1},
                ]},
            },
        ],
    },

    {
        'tag': 'trapped_seraph',
        'name': 'Caged Angel',
        'symbol': '@',
        'color': (220, 210, 170),
        'block': 6,
        'text': (
            "A winged figure kneels inside a cage of black iron, six "
            "wings folded against a frame too large for its prison. The "
            "air smells of ozone and wildflowers. \"I was sent to guard "
            "this passage. They trapped me instead.\" Its voice resonates "
            "in your chest. \"A scroll's arcane energy will overload the "
            "binding. I have been here two hundred years. The darkness "
            "grows stronger every day I am caged.\""
        ),
        'options': [
            {
                'label': "Use a scroll to shatter the cage",
                'karma': +1,
                'outcome': (
                    "The bars explode in light. The seraph rises to its "
                    "full height — nine feet of wings and terrible grace. "
                    "\"I will not forget,\" it says, and is gone in a "
                    "flash that leaves spots in your vision."
                ),
                'cost': {'type': 'scroll'},
                'reward': None,
            },
            {
                'label': "You have no scrolls to spare",
                'karma': 0,
                'outcome': (
                    "\"Then I wait. As I have waited.\" The seraph bows "
                    "its head. Its wings fold tighter."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take its feathers — divine power, just lying there",
                'karma': -1,
                'outcome': (
                    "You reach through the bars and tear out a handful "
                    "of feathers. The seraph shrieks — a sound like a "
                    "cathedral organ screaming. Divine energy floods your "
                    "body, burning through your veins. The seraph huddles "
                    "in the corner, trembling."
                ),
                'cost': None,
                'reward': {'type': 'stat', 'stat': 'WIS', 'amount': 1},
            },
        ],
    },

    {
        'tag': 'weeping_mother',
        'name': 'Weeping Ghost',
        'symbol': '@',
        'color': (170, 190, 210),
        'block': 6,
        'text': (
            "She materializes slowly — first the outline, then the "
            "tears that fall like silver and vanish before hitting "
            "stone. A glowing locket orbits her like a small moon. "
            "\"My son wandered in twelve years ago. He was nine. The "
            "dog came back without him.\" Her voice fractures. \"Will "
            "you pray with me? Not for him — for me. I am so tired. "
            "I just want to stop.\""
        ),
        'options': [
            {
                'label': "Kneel and pray with her — she deserves peace",
                'karma': +1,
                'outcome': (
                    "The prayer stretches on and on. Her exhaustion "
                    "presses down on you like stone — twelve years of "
                    "walking. When you finish, her tears slow. \"Thank "
                    "you,\" she breathes. \"I can feel peace. After so "
                    "long.\" She fades into warm light, smiling."
                ),
                'cost': {'type': 'sp', 'amount': 60},
                'reward': None,
            },
            {
                'label': "Your love endures beyond death — that matters",
                'karma': 0,
                'outcome': (
                    "She flickers. \"Thank you for seeing me. Most walk "
                    "right through.\" She keeps searching. She will "
                    "always keep searching."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take the locket — it radiates power",
                'karma': -1,
                'outcome': (
                    "Her scream is not anger — it is heartbreak. \"That "
                    "is all I have of him! ALL I HAVE!\" Her hands pass "
                    "through yours. She crumples, fading into shadow, "
                    "not into light."
                ),
                'cost': None,
                'reward': {'type': 'random_accessory'},
            },
        ],
    },

    # ── BLOCK 7: Levels 61-69 ────────────────────────────────────────

    {
        'tag': 'ser_brennan',
        'name': 'Dying Knight',
        'symbol': '@',
        'color': (160, 155, 170),
        'block': 7,
        'text': (
            "The knight's breastplate is split open and the wound beneath "
            "is mortal. He sits with the careful dignity of a man who "
            "knows how he will spend his last minutes. A fine sword and "
            "shield rest beside him. \"My daughter Annalise drew me a "
            "picture before I left. A horse, I think. She said it was a "
            "dragon.\" He almost laughs. \"If you have a healing potion "
            "— not to save me. Just the pain.\""
        ),
        'options': [
            {
                'label': "Give him a healing potion for the pain",
                'karma': +1,
                'outcome': (
                    "He drinks, and the tension drains from his face. He "
                    "pulls a folded parchment from his breastplate — a "
                    "child's drawing. He looks at it and smiles. \"It's "
                    "a beautiful dragon, Annalise.\""
                ),
                'cost': {'type': 'healing_potion'},
                'reward': None,
            },
            {
                'label': "You need everything you have — you are sorry",
                'karma': 0,
                'outcome': (
                    "\"Then sit with me a moment. Just a moment. I don't "
                    "want to be alone at the end.\" You sit. It is the "
                    "longest minute of your life."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take his equipment — he won't need it now",
                'karma': -1,
                'outcome': (
                    "He watches you lift the sword from beside him, then "
                    "unbuckle the shield. \"She drew me a dragon,\" he "
                    "says to no one. You're already walking away. The "
                    "equipment is masterwork."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'random_weapon'},
                    {'type': 'random_shield'},
                ]},
            },
        ],
    },

    {
        'tag': 'cursed_scholar',
        'name': 'Cursed Scholar',
        'symbol': '@',
        'color': (140, 110, 170),
        'block': 7,
        'text': (
            "His hands are fused to the book. Veins of black light crawl "
            "up his arms and his eyes are pure void. His mouth whispers "
            "in a language that makes your teeth ache. Something human "
            "surfaces for a moment. \"Kill the book. Not me — THE BOOK. "
            "I was a teacher. I had a wife named Clara.\" His voice "
            "breaks. \"I can't remember her face anymore. It took that "
            "from me.\""
        ),
        'options': [
            {
                'label': "Tear the book apart — free him",
                'karma': +1,
                'outcome': (
                    "Dark energy explodes outward, searing your skin and "
                    "burning something deeper. The black veins recede. "
                    "He opens his eyes. They're blue. Human. \"Clara,\" "
                    "he says. \"Her eyes are brown. I remember.\" He "
                    "weeps."
                ),
                'cost': {'type': 'hp_percent', 'amount': 20},
                'reward': None,
            },
            {
                'label': "You can't risk it — you are sorry",
                'karma': 0,
                'outcome': (
                    "The human moment passes. His eyes go black again. "
                    "The whispering resumes. He is gone."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take the book — that knowledge could save you",
                'karma': -1,
                'outcome': (
                    "Forbidden knowledge floods your mind — centuries of "
                    "dark scholarship, the true names of things that "
                    "should not be named. The scholar is a hollow shell "
                    "on the floor, still breathing. Empty."
                ),
                'cost': None,
                'reward': {'type': 'stat', 'stat': 'INT', 'amount': 2},
            },
        ],
    },

    {
        'tag': 'fairy_jar',
        'name': 'Trapped Fairy',
        'symbol': '@',
        'color': (180, 220, 200),
        'block': 7,
        'text': (
            "A tiny winged woman is trapped inside a thick glass jar "
            "sealed with wax and iron wire. Shimmering fairy dust coats "
            "the inside — shed from her broken wings over months. She "
            "presses both hands against the glass. You lean close. "
            "\"Please! A collector caught me. Eight months ago. My wings "
            "— I can't feel them anymore. If you have a potion, I think "
            "they can still heal.\""
        ),
        'options': [
            {
                'label': "Break the jar carefully and heal her wings",
                'karma': +1,
                'outcome': (
                    "She drinks a single drop — the rest is enormous to "
                    "her — and flexes her wings. They straighten. She "
                    "loops around your head and kisses your cheek — a "
                    "warm spot no bigger than a pinprick. \"You are the "
                    "kindest giant in the world.\" The fairy dust "
                    "scattered when the jar broke. You don't care."
                ),
                'cost': {'type': 'potion'},
                'reward': None,
            },
            {
                'label': "Smash the jar — the dust will scatter, but she's free",
                'karma': 0,
                'outcome': (
                    "She tumbles out, gasping. The fairy dust scatters "
                    "across the floor, lost. Her wings are still bent. "
                    "\"Thank you. I think.\" She limps into the dark on "
                    "foot."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Keep the jar sealed — the dust is priceless",
                'karma': -1,
                'outcome': (
                    "You tilt the jar, working dust through the wax seal. "
                    "She hammers on the glass, screaming — the vibration "
                    "helps shake the dust loose. When you're done, you "
                    "pocket the jar. Her tiny fists keep pounding."
                ),
                'cost': None,
                'reward': {'type': 'stat', 'stat': 'DEX', 'amount': 1},
            },
        ],
    },

    # ── BLOCK 8: Levels 71-79 ────────────────────────────────────────

    {
        'tag': 'penitent',
        'name': 'The Penitent',
        'symbol': '@',
        'color': (150, 140, 130),
        'block': 8,
        'text': (
            "A man kneels in a pool of his own blood, a dagger beside "
            "him. He has carved the word MURDERER into his own forearm. "
            "\"I killed a man. Twenty years ago. Over money. I came here "
            "to die where no one would find the body.\" He looks at you. "
            "\"I've been kneeling here three hours and I find I am "
            "afraid. Isn't that pathetic?\" His purse is thick with "
            "gold. The dagger is dark iron, wickedly sharp."
        ),
        'options': [
            {
                'label': "Give him a healing potion — dying won't undo it",
                'karma': +1,
                'outcome': (
                    "\"Twenty years,\" he whispers. \"That's a lot of "
                    "atoning.\" He drinks. He bandages his arm. He takes "
                    "the stairs. You wonder if he'll make it. You think "
                    "he will."
                ),
                'cost': {'type': 'healing_potion'},
                'reward': None,
            },
            {
                'label': "That choice is his, not yours — you cannot judge",
                'karma': 0,
                'outcome': (
                    "\"Fair enough. Go on, then. I need to think.\" He "
                    "stares at the dagger. You don't look back."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take the gold and the dagger — he's done with both",
                'karma': -1,
                'outcome': (
                    "He watches you pick up the murder weapon and laughs "
                    "— a horrible, cracked sound. \"It suits you better "
                    "than it suited me.\" The dagger is finely made and "
                    "the gold is heavy."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'gold', 'min': 200, 'max': 300},
                    {'type': 'specific_item', 'item_type': 'weapon',
                     'item_id': 'penitents_blade'},
                ]},
            },
        ],
    },

    {
        'tag': 'roderic_shield',
        'name': 'Young Knight',
        'symbol': '@',
        'color': (170, 160, 150),
        'block': 8,
        'trigger_item': 'lionheart_shield',
        'trigger_level_offset': 2,
        'text': (
            "A young knight — barely twenty — searches the rooms "
            "frantically. His armor is freshly polished, his face clean. "
            "He sees the shield on your arm and goes white. \"That's my "
            "father's shield. Ser Marten of the Iron Vale. He came down "
            "four months ago to clear a basilisk nest. He told my mother "
            "he'd be back for supper.\" His composure breaks. \"He "
            "promised. He doesn't break promises.\""
        ),
        'options': [
            {
                'label': "Give him the shield — it belongs to his family",
                'karma': +1,
                'outcome': (
                    "Roderic holds the shield to his chest. He can barely "
                    "lift it — he's not strong enough yet. He carries it "
                    "anyway. \"I'll bring him home,\" he says. \"Both "
                    "pieces of him.\""
                ),
                'cost': {'type': 'triggered_item'},
                'reward': None,
            },
            {
                'label': "Return it, but accept his coin for your trouble",
                'karma': 0,
                'outcome': (
                    "\"For bringing me this. Thank you.\" He presses his "
                    "savings into your hand and clutches the shield like "
                    "a lifeline."
                ),
                'cost': {'type': 'triggered_item'},
                'reward': {'type': 'gold', 'min': 60, 'max': 100},
            },
            {
                'label': "Keep it — you need this shield to survive",
                'karma': -1,
                'outcome': (
                    "\"I found this on a merchant's stall.\" Roderic "
                    "reads MARTEN OF THE IRON VALE on the inside rim. "
                    "He knows. But he's too young and too scared to call "
                    "a grown adventurer a liar. He walks away, shoulders "
                    "hunched."
                ),
                'cost': None,
                'reward': None,
            },
        ],
    },

    {
        'tag': 'forgotten_prisoner',
        'name': 'Forgotten Prisoner',
        'symbol': '@',
        'color': (130, 130, 140),
        'block': 8,
        'text': (
            "The cell is ancient, the iron bars more rust than metal. "
            "Inside, a white-haired man sits with the posture of someone "
            "who stopped expecting rescue long ago. \"Forty-three years,\" "
            "he says pleasantly. \"The lock is dwarven — gold coins in "
            "the mechanism will trip the tumblers.\" Behind a loose stone "
            "in his cell, you glimpse a hidden cache. He sees you "
            "looking. \"That is all I have.\""
        ),
        'options': [
            {
                'label': "Feed gold into the lock — forty-three years is enough",
                'karma': +1,
                'outcome': (
                    "The lock groans, clicks, and swings open. He stands "
                    "for the first time in forty-three years. His knees "
                    "buckle. You catch him. \"I forgot what it feels "
                    "like,\" he says, \"to be touched by another person.\""
                ),
                'cost': {'type': 'gold', 'amount': 150},
                'reward': None,
            },
            {
                'label': "You can't afford that — you are sorry, old man",
                'karma': 0,
                'outcome': (
                    "\"No one can. Forty-three years of no one being able "
                    "to afford it.\" He folds his hands. \"Perhaps the "
                    "next one.\""
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Reach through the bars for the cache",
                'karma': -1,
                'outcome': (
                    "\"No. Please. That's all I have. Forty-three years "
                    "and that is ALL I HAVE.\" You pry the stone out. "
                    "He turns away."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'gold', 'min': 200, 'max': 300},
                    {'type': 'random_accessory'},
                ]},
            },
        ],
    },

    # ── BLOCK 9: Levels 81-89 ────────────────────────────────────────

    {
        'tag': 'fallen_paladin',
        'name': 'Fallen Paladin',
        'symbol': '@',
        'color': (140, 140, 160),
        'block': 9,
        'text': (
            "He is enormous and he is on his knees in the dirt, weeping "
            "without sound. His armor is blackened and cracked. \"I "
            "killed innocents. Forty-six people. I was told they were "
            "heretics. I believed it.\" His hands tremble. \"I came here "
            "to die. But my armor — it is still blessed. I cannot wear "
            "it. Not after what I did. If you can use it...\" His pack "
            "holds everything the church paid him."
        ),
        'options': [
            {
                'label': "Give him gold for passage — penance requires living",
                'karma': +1,
                'outcome': (
                    "\"You would send me back? To face them? To face "
                    "their families?\" Yes. He picks up the broken holy "
                    "symbol. Puts it around his neck again. Walks toward "
                    "the stairs."
                ),
                'cost': {'type': 'gold', 'amount': 200},
                'reward': None,
            },
            {
                'label': "You cannot tell him to live or die — that weight is his",
                'karma': 0,
                'outcome': (
                    "\"You are right. It is mine.\" He stays on his "
                    "knees. The decision waits."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take his pack and armor — he offered it",
                'karma': -1,
                'outcome': (
                    "The blessed metal resists your hands for a moment "
                    "— then gives in. He doesn't resist. He doesn't even "
                    "notice. What's one more betrayal to a man who "
                    "betrayed forty-six?"
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'gold', 'min': 200, 'max': 300},
                    {'type': 'random_armor'},
                ]},
            },
        ],
    },

    {
        'tag': 'azarael_demon',
        'name': 'Bound Demon',
        'symbol': '&',
        'color': (200, 80, 60),
        'block': 9,
        'text': (
            "Eight feet tall on its knees, skin like heated bronze. "
            "Glowing chains bite into its flesh. Its voice is warm, "
            "reasonable, almost kind. \"Look at me. Centuries in chains "
            "for a war I did not start. I am a soldier — same as you. "
            "Free me and I will give you strength. True strength.\" It "
            "leans forward. \"Refuse, and you face the Pit alone. We "
            "both know what waits in the Pit.\""
        ),
        'options': [
            {
                'label': "Reinforce the binding with a scroll",
                'karma': +1,
                'outcome': (
                    "The sigils blaze and the demon screams — dropping "
                    "the kind mask, showing the furnace beneath. \"FOOL! "
                    "You will BEG for what I offered!\" The chains "
                    "tighten. The world is safer."
                ),
                'cost': {'type': 'scroll'},
                'reward': None,
            },
            {
                'label': "Walk away — this is not your concern",
                'karma': 0,
                'outcome': (
                    "Its copper eyes follow you until you turn the "
                    "corner. \"You'll be back,\" it says softly. \"They "
                    "always come back.\""
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Shatter the chains — you need that strength",
                'karma': -1,
                'outcome': (
                    "The demon rises to its full height and smiles with "
                    "far too many teeth. Something cold and vast settles "
                    "into your bones. \"A pleasure doing business,\" it "
                    "says, and vanishes in sulfur and distant screaming."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'stat', 'stat': 'STR', 'amount': 2},
                    {'type': 'gold', 'min': 200, 'max': 200},
                ]},
            },
        ],
    },

    {
        'tag': 'child_shrine',
        'name': 'Small Shrine',
        'symbol': '@',
        'color': (200, 190, 160),
        'block': 9,
        'text': (
            "In a small alcove, someone has built a shrine. A cairn of "
            "pebbles, a toy wooden sword, and a child's drawing of a "
            "family. Four words scratched into the wall: \"WE WILL FIND "
            "YOU.\" A faint light glows from the shrine — grief and love "
            "given weight. Coins and small treasures have been left by "
            "those who passed before you."
        ),
        'options': [
            {
                'label': "Leave food at the shrine — for whoever lingers",
                'karma': +1,
                'outcome': (
                    "As you set it down, the light brightens. For just "
                    "a moment you feel small arms around your waist — a "
                    "hug from someone who isn't there. Then it's gone."
                ),
                'cost': {'type': 'food'},
                'reward': None,
            },
            {
                'label': "Bow your head in respect and move on",
                'karma': 0,
                'outcome': (
                    "The light flickers. Acknowledgment. Then it dims "
                    "back to its quiet glow."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take the offerings — the dead have no use for gold",
                'karma': -1,
                'outcome': (
                    "As you fill your pockets, the light dims. The "
                    "drawing curls and crumbles to dust. The toy sword "
                    "cracks down the middle. Something leaves this "
                    "place. Among the offerings is a finely crafted ring."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'random_accessory'},
                    {'type': 'gold', 'min': 150, 'max': 200},
                ]},
            },
        ],
    },

    # ── BLOCK 10: Levels 91-98 ───────────────────────────────────────

    {
        'tag': 'dying_prophet',
        'name': 'Dying Prophet',
        'symbol': '@',
        'color': (200, 200, 210),
        'block': 10,
        'text': (
            "An old man in blood-stained white robes lies against an "
            "altar, his eyes terrifyingly clear. Stone tablets surround "
            "him, fragments carved over years: \"THE DESTROYER WAKES\" "
            "and \"SEVEN SEALS.\" \"I need to finish the warning. One "
            "more tablet. A healing potion — not to save me — but to "
            "give me one more hour.\" Around his neck hangs an amulet "
            "that pulses with gathered visions."
        ),
        'options': [
            {
                'label': "Give him a healing potion — the warning matters",
                'karma': +1,
                'outcome': (
                    "He drinks, and light returns to his eyes. He takes "
                    "up his chisel with renewed purpose. The sound of "
                    "stone being carved follows you down the corridor. "
                    "He will finish."
                ),
                'cost': {'type': 'healing_potion'},
                'reward': None,
            },
            {
                'label': "You need everything for what lies below",
                'karma': 0,
                'outcome': (
                    "\"Then you will face it without knowing. Go. Go "
                    "quickly.\" His clear eyes follow you until you "
                    "turn the corner."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Take the amulet — those visions could save you",
                'karma': -1,
                'outcome': (
                    "His hand clutches at it but he's too weak. \"The "
                    "prophecy dies with me if...\" His eyes lose their "
                    "clarity. Just an old man now. Dying in the dark."
                ),
                'cost': None,
                'reward': {'type': 'specific_item', 'item_type': 'accessory',
                           'item_id': 'prophets_amulet'},
            },
        ],
    },

    {
        'tag': 'petrified_adventurer',
        'name': 'Stone Statue',
        'symbol': '@',
        'color': (160, 160, 160),
        'block': 10,
        'text': (
            "A statue stands mid-corridor — but the pose is wrong. One "
            "arm raised, mouth open in a scream turned to stone. "
            "Basilisk work. Scratched into the wall: \"CELESTE — STONE "
            "BUT ALIVE. SCROLL OF RESTORATION WILL REVERSE. I WILL "
            "COME BACK FOR YOU.\" Whoever wrote it never came back. You "
            "press your ear to the stone. Faintly, impossibly — a "
            "heartbeat. Her armor and sword are masterwork."
        ),
        'options': [
            {
                'label': "Use a scroll to restore her — she's still alive",
                'karma': +1,
                'outcome': (
                    "Stone cracks, flakes, falls. Celeste gasps — the "
                    "scream finishes, then stops. She looks at her hands. "
                    "She sees the scratched message and her eyes fill. "
                    "\"Maren. She tried.\" Celeste takes her gear and "
                    "walks toward the stairs."
                ),
                'cost': {'type': 'scroll'},
                'reward': None,
            },
            {
                'label': "You have no scrolls — you are sorry, Celeste",
                'karma': 0,
                'outcome': (
                    "You leave her there. The heartbeat continues behind "
                    "you, fainter and fainter, as you walk away."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "Break the statue — the gear returns to normal",
                'karma': -1,
                'outcome': (
                    "The stone shatters. Whatever was alive ceases. The "
                    "armor and sword clatter free, undamaged. You try "
                    "not to look at the fragments that might have been "
                    "a face."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'random_weapon'},
                    {'type': 'random_armor'},
                ]},
            },
        ],
    },

    {
        'tag': 'last_merchant',
        'name': 'Lost Merchant',
        'symbol': '@',
        'color': (200, 180, 120),
        'block': 10,
        'text': (
            "A small, fat man in an absurdly fine coat sits on a trunk, "
            "looking terrified. His moustache is immaculate. \"I followed "
            "the adventurers. I thought there would be profit.\" He pats "
            "the trunk. \"Artifacts, enchanted rings, a shimmering cloak. "
            "Ten years of collecting. But I cannot carry it back alone. "
            "Not through what is up there. I have been here three days, "
            "too afraid to move.\""
        ),
        'options': [
            {
                'label': "Give him food for the journey home",
                'karma': +1,
                'outcome': (
                    "He clutches the food to his chest. \"You are a "
                    "saint. An absolute saint. If I survive this I will "
                    "name my next shop after you.\" He straightens his "
                    "lapels and begins the long walk up."
                ),
                'cost': {'type': 'food'},
                'reward': None,
            },
            {
                'label': "The stairs are that direction — keep to the walls",
                'karma': 0,
                'outcome': (
                    "He nods frantically, smoothing his lapels. \"Walls. "
                    "No running. Right.\" He hoists the trunk onto his "
                    "back with surprising strength and shuffles away."
                ),
                'cost': None,
                'reward': None,
            },
            {
                'label': "The trunk stays — consider it a toll",
                'karma': -1,
                'outcome': (
                    "\"But that's everything. Ten years of...\" He sees "
                    "your expression. He lets go of the trunk. Inside: "
                    "enchanted equipment and a small fortune in gold."
                ),
                'cost': None,
                'reward': {'type': 'multi', 'rewards': [
                    {'type': 'random_weapon'},
                    {'type': 'random_accessory'},
                    {'type': 'gold', 'min': 200, 'max': 300},
                ]},
            },
        ],
    },
]


# ── Spawn level selection ────────────────────────────────────────────

def select_encounter_levels(seed: int | None = None) -> dict:
    """Return {level_num: encounter_dict} for a game run.

    One encounter guaranteed per 10-level block, chosen from 3 candidates.
    Never spawns on boss levels (20, 40, 60, 80, 100).
    """
    rng = random.Random(seed)
    placements: dict[int, dict] = {}

    for block_num, block_lo, block_hi in _BLOCKS:
        candidates = [e for e in ENCOUNTERS if e['block'] == block_num
                       and not e.get('trigger_item')]
        triggered  = [e for e in ENCOUNTERS if e['block'] == block_num
                       and e.get('trigger_item')]

        # Pool: all non-triggered + up to 1 triggered
        pool = list(candidates)
        if triggered:
            pool.append(rng.choice(triggered))
        if not pool:
            continue
        rng.shuffle(pool)

        enc = pool[0]

        # Pick a level within the block, excluding boss levels
        valid_levels = [lv for lv in range(block_lo, block_hi + 1)
                        if lv not in _BOSS_LEVELS]
        if not valid_levels:
            continue
        level = rng.choice(valid_levels)
        placements[level] = enc

    return placements


def get_trigger_item_levels(placements: dict) -> dict:
    """Return {item_id: spawn_level} for triggered encounters.

    The trigger item spawns `trigger_level_offset` levels before the NPC.
    """
    triggers: dict[str, int] = {}
    for level, enc in placements.items():
        item_id = enc.get('trigger_item')
        if item_id:
            offset = enc.get('trigger_level_offset', 1)
            spawn_level = max(1, level - offset)
            triggers[item_id] = spawn_level
    return triggers


# ── Cost / reward checking ───────────────────────────────────────────

def can_pay_cost(player, cost: dict | None, player_gold: int) -> tuple[bool, str]:
    """Check if the player can afford a cost. Returns (can_pay, fail_message)."""
    if cost is None:
        return True, ''

    ctype = cost['type']

    if ctype == 'food':
        from items import Food, Ingredient
        has = any(isinstance(i, (Food, Ingredient)) for i in player.inventory)
        return (True, '') if has else (False, "You have no food to give.")

    if ctype == 'healing_potion':
        from items import Potion, Scroll, Wand
        # Accept: healing potions, heal spell (costs MP), healing scrolls, healing wands
        has_potion = any(isinstance(i, Potion) and getattr(i, 'effect', '') in ('heal', 'extra_heal', 'full_heal')
                         for i in player.inventory)
        has_spell = 'heal_spell' in getattr(player, 'known_spells', {}) and player.mp >= player.known_spells.get('heal_spell', 99)
        has_scroll = any(isinstance(i, Scroll) and 'heal' in getattr(i, 'effect', '').lower()
                         for i in player.inventory)
        has_wand = any(isinstance(i, Wand) and 'heal' in getattr(i, 'effect', '').lower()
                       and getattr(i, 'charges', 0) > 0
                       for i in player.inventory)
        has = has_potion or has_spell or has_scroll or has_wand
        return (True, '') if has else (False, "You have no way to heal them.")

    if ctype == 'potion':
        from items import Potion
        has = any(isinstance(i, Potion) for i in player.inventory)
        return (True, '') if has else (False, "You have no potions to give.")

    if ctype == 'scroll':
        from items import Scroll
        has = any(isinstance(i, Scroll) for i in player.inventory)
        return (True, '') if has else (False, "You have no scrolls to spare.")

    if ctype == 'weapon':
        from items import Weapon
        has = any(isinstance(i, Weapon) for i in player.inventory)
        return (True, '') if has else (False, "You have no weapon to give.")

    if ctype == 'gold':
        amt = cost['amount']
        return (True, '') if player_gold >= amt else (False, f"You need {amt} gold.")

    if ctype == 'hp_percent':
        pct = cost['amount']
        cost_hp = max(5, int(player.hp * pct / 100))
        if player.hp > cost_hp + 5:
            return True, ''
        return False, "You are too injured to survive that."

    if ctype == 'max_hp':
        if player.max_hp > cost['amount'] + 10:
            return True, ''
        return False, "You are too frail to survive that."

    if ctype == 'sp':
        if player.sp >= cost['amount']:
            return True, ''
        return False, "You are too exhausted."

    if ctype == 'random_item':
        # Used as a cost — check if player has an item of the requested category
        from items import Scroll, Potion, Food, Weapon
        cat = cost.get('category', 'scroll')
        cat_map = {'scroll': Scroll, 'potion': Potion, 'food': Food, 'weapon': Weapon}
        cls = cat_map.get(cat)
        if cls and any(isinstance(i, cls) for i in player.inventory):
            return True, ''
        return False, f"You have no {cat} to offer."

    if ctype == 'hp':
        if player.hp > cost['amount'] + 5:
            return True, ''
        return False, "You are too injured to afford that."

    if ctype == 'mp':
        if player.mp >= cost['amount']:
            return True, ''
        return False, "You don't have enough mana."

    if ctype == 'triggered_item':
        # The trigger item should be in inventory — checked by caller
        return True, ''

    if ctype == 'accept_item':
        # Accepting a burden always possible
        return True, ''

    if ctype == 'spawn_deadite_ambush':
        # Always possible — the Deadite attacks you
        return True, ''

    return True, ''


def get_inventory_filter(cost: dict | None) -> str | None:
    """Return the inventory filter type for costs that need item selection.

    Returns None if no inventory selection is needed.
    """
    if cost is None:
        return None
    ctype = cost['type']
    if ctype in ('food', 'healing_potion', 'potion', 'scroll', 'weapon'):
        return ctype
    return None


# ── Judgment ─────────────────────────────────────────────────────────

_JUDGMENT_TIERS = [
    (-10, -6, 'abaddon_empowered',
     "Michael weighs your soul and recoils.\n"
     "\"You have walked in darkness.\"\n"
     "The scales crash to the ground. A terrible power surges\n"
     "toward the Pit below.\n\n"
     "ABADDON IS EMPOWERED BY YOUR SINS."),

    (-5, -1, 'locusts_strengthened',
     "Michael weighs your soul and frowns.\n"
     "\"Your deeds are wanting.\"\n"
     "The scales tip toward shadow. A buzzing fills the air.\n\n"
     "THE LOCUST SWARMS GROW LARGER AND MORE NUMEROUS."),

    (0, 0, 'silence',
     "Michael weighs your soul.\n"
     "The scales balance perfectly — and remain cold.\n"
     "\"You have done nothing worthy of praise or condemnation.\"\n\n"
     "The altar falls silent. You receive nothing."),

    (1, 9, 'scales_granted',
     "Michael weighs your soul and nods.\n"
     "\"You have walked in light.\"\n"
     "The scales glow with golden fire. They lift from the altar\n"
     "and float into your hands.\n\n"
     "YOU RECEIVE THE SCALES OF MICHAEL."),

    (10, 10, 'sword_and_scales',
     "Michael descends in a pillar of white fire. He kneels.\n"
     "\"In all the ages of this world, few mortals have walked\n"
     "as you have walked. You gave when you had nothing.\n"
     "You sacrificed when it would have been easier to take.\"\n"
     "He places a flaming sword in your hands and anoints\n"
     "your brow with light.\n"
     "\"Rise, Paladin. Chosen of God.\n"
     "The Destroyer will know your name.\"\n\n"
     "YOU RECEIVE THE SWORD AND SCALES OF MICHAEL.\n"
     "YOU ARE ANOINTED PALADIN AND CHOSEN OF GOD."),
]


def judge_karma(karma: int) -> tuple[str, str]:
    """Return (outcome_key, narrative_text) for the given karma score."""
    karma = max(-10, min(10, karma))
    for lo, hi, key, text in _JUDGMENT_TIERS:
        if lo <= karma <= hi:
            return key, text
    # Fallback (should be unreachable since loop covers clamped range)
    if karma >= 10:
        return _JUDGMENT_TIERS[4][2], _JUDGMENT_TIERS[4][3]
    if karma > 0:
        return _JUDGMENT_TIERS[3][2], _JUDGMENT_TIERS[3][3]
    if karma < -5:
        return _JUDGMENT_TIERS[0][2], _JUDGMENT_TIERS[0][3]
    if karma < 0:
        return _JUDGMENT_TIERS[1][2], _JUDGMENT_TIERS[1][3]
    return _JUDGMENT_TIERS[2][2], _JUDGMENT_TIERS[2][3]
