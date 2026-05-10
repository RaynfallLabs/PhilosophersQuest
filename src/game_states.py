"""Game-state string constants.

Each constant is the string stored on Game.state to indicate which mode the
game loop is in (player turn, quiz, a specific menu, etc.). Extracted from
main.py so that render and input modules can import the same names without
creating a circular dependency with main.
"""
STATE_PLAYER         = 'player'
STATE_QUIZ           = 'quiz'
STATE_EQUIP_MENU     = 'equip_menu'
STATE_ACCESSORY_MENU = 'accessory_menu'
STATE_WAND_MENU      = 'wand_menu'
STATE_SCROLL_MENU    = 'scroll_menu'
STATE_IDENTIFY_MENU  = 'identify_menu'
STATE_COOK_MENU      = 'cook_menu'
STATE_CONFIRM_EXIT   = 'confirm_exit'
STATE_EXIT_QUEST     = 'exit_quest'      # "Complete your quest?" (has Stone)
STATE_ABANDON_QUEST  = 'abandon_quest'   # "Abandon your quest?" (no Stone)
STATE_CHICKEN        = 'chicken'         # McFly popup
STATE_VICTORY        = 'victory'
STATE_DEAD           = 'dead'
STATE_REVIEW_MISSED  = 'review_missed'   # post-death missed question review
STATE_LOCKPICK       = 'lockpick'
STATE_TARGET         = 'target'          # ranged targeting cursor
STATE_EAT_MENU       = 'eat_menu'        # eat food / raw ingredient
STATE_QUAFF_MENU     = 'quaff_menu'      # quaff a potion
STATE_HELP           = 'help'
STATE_LORE           = 'lore'
STATE_PRAY           = 'pray'
STATE_SPELL_MENU     = 'spell_menu'
STATE_HINT           = 'hint'            # Recall Lore result display
STATE_EXAMINE        = 'examine'         # Examine identified inventory item
STATE_ENCYCLOPEDIA   = 'encyclopedia'    # Encyclopedia browser
STATE_DROP_MENU      = 'drop_menu'       # Drop an item from inventory
STATE_DROP_GOLD_INPUT = 'drop_gold_input' # Numeric prompt: how much gold to drop
STATE_STORY_POPUP    = 'story_popup'     # Narrative popup (quest intro, boss defeat, ending)
STATE_MYSTERY_APPROACH = 'mystery_approach'  # Player is approaching a mystery altar
STATE_SHOP             = 'shop'              # Merchant shop overlay
STATE_POWER_MENU       = 'power_menu'        # Active powers menu (V key)
STATE_HACK_REALITY     = 'hack_reality'      # Hack Reality result display
STATE_XYZZY_INPUT      = 'xyzzy_input'       # Hidden green terminal text input
STATE_XYZZY_CONFIRM    = 'xyzzy_confirm'     # "Hack reality?" Yes/No warning
STATE_THROW_MENU       = 'throw_menu'        # Select potion to throw
STATE_QUIRKS           = 'quirks'            # Quirks progress browser
STATE_CHARACTER_SHEET  = 'character_sheet'   # Detailed character info
STATE_NPC_ENCOUNTER    = 'npc_encounter'     # Moral choice encounter with NPC
STATE_COW_ENCOUNTER    = 'cow_encounter'     # Secret cow dialog
STATE_JUDGMENT         = 'judgment'          # Altar of Last Judgment result
STATE_STUDY            = 'study'             # In-game missed question review
