# -*- mode: python ; coding: utf-8 -*-
r"""
PyInstaller spec for Philosopher's Quest.
Run from the project root:
    pyinstaller PhilosophersQuest.spec
Output: dist\PhilosophersQuest\  (portable folder — zip for distribution)
On macOS also dist/PhilosophersQuest.app (the BUNDLE at the end).

Saves, highscores and settings go to paths.save_dir():
    Windows  %APPDATA%\PhilosophersQuest\
    Linux    $XDG_DATA_HOME/PhilosophersQuest/ (default ~/.local/share/...)
    macOS    ~/Library/Application Support/PhilosophersQuest/
ERROR_LOG.txt and crash_*.txt go to game_log.log_dir():
    <home>/Documents/PhilosophersQuest/ (falls back to the save dir)
    macOS: ~/Library/Logs/PhilosophersQuest/ (no Documents permission prompt)
"""

import os
import re
import sys

block_cipher = None

# ── Data files to bundle ────────────────────────────────────────────────────
# Format: (source_path_or_glob, dest_folder_inside_bundle)
#
# IMPORTANT: tests/test_packaging.py verifies that EVERY data_path(...)
# call site in src/ resolves to a path covered by this list. If you add
# a `data_path('data', 'foo.json')` to game code, add ('data/foo.json',
# 'data') here OR the bundled exe will FileNotFoundError on load.
added_files = [
    # Game data — top-level JSONs
    ('data/monsters.json',          'data'),
    ('data/monster_sizes.json',     'data'),
    ('data/monster_families.json',  'data'),   # monster family knowledge (family_lore.py)
    ('data/hints.json',             'data'),
    ('data/question_twins.json',    'data'),   # same-fact twins the quiz holds back (quiz_engine)
    ('data/philosophy_mastery.json', 'data'),  # philosophy tier traits (philosophy_mastery.py)
    ('data/boss_boons.json',        'data'),
    ('data/pet_growth.json',        'data'),
    ('data/chest_templates.json',   'data'),
    ('data/chest_traps.json',       'data'),
    ('data/flavor_encounters.json', 'data'),
    ('data/npc_encounters.json',    'data'),
    ('data/abandoned_emberpup.json', 'data'),
    ('data/black_knight.json',      'data'),
    ('data/karma_rules.json',       'data'),
    ('data/setne_tomb.json',        'data'),
    ('data/gate_lines.json',        'data'),
    ('data/traders.json',           'data'),
    ('data/item_worth.json',        'data'),
    ('data/achievements.json',      'data'),   # the Seeker's achievements (achievements.py)
    ('data/gear_rules.json',        'data'),   # armour, shield, ring and amulet rules (gear.py)
    ('data/armor_guards.json',      'data'),   # what each minor armour slot guards (guards.py)
    ('data/enchantments.json',      'data'),   # the minor-slot enchantments (enchantments.py)
    ('data/ring_kinds.json',        'data'),   # the ring and amulet kinds (rings.py)
    ('data/affinity_lines.json',    'data'),   # weakness / resistance hit lines (affinity.py)
    ('data/monster_blood.json',     'data'),   # which creatures can bleed (monster.kind_can_bleed)
    # Game data — directories
    ('data/items',                  'data/items'),
    ('data/materials',              'data/materials'),
    ('data/questions',              'data/questions'),
    ('data/question_contexts',      'data/question_contexts'),
    ('data/templates',              'data/templates'),
    ('data/ui',                     'data/ui'),
    # Assets — window icon + sprites/fonts
    ('assets/icon.ico',             'assets'),
    ('assets/fonts',                'assets/fonts'),
    ('assets/tiles',                'assets/tiles'),
    ('assets/achievements',         'assets/achievements'),   # badge art (seeker_screen.py)
    # UI art kit (optional painted panels/frames; see assets/ui/README.md).
    # Loaded by src/ui_theme.py at startup; missing art = procedural UI.
    ('assets/ui',                   'assets/ui'),
]

# Paths INSIDE the whole-directory entries above that must not ship: the
# reversible prune archive of removed questions, and the UI kit's authoring
# notes. Filtered out of a.datas below; tests/test_packaging.py checks that
# every other file in those directories is runtime data.
bundle_excludes = [
    'data/questions/_pruned',
    'assets/ui/README.md',
    'assets/achievements/README.md',
]


def _is_excluded(dest):
    d = dest.replace(os.sep, '/')
    return any(d == x or d.startswith(x + '/') for x in bundle_excludes)


a = Analysis(
    ['src/main.py'],
    pathex=['src'],          # so all src/ modules are on the path
    binaries=[],
    datas=added_files,
    hiddenimports=[
        # Pygame subsystems
        'pygame', 'pygame.font', 'pygame.mixer', 'pygame.image',
        # Numpy (used by sound_system.py via __import__)
        'numpy', 'numpy.core', 'numpy.core.multiarray',
        # Game modules imported dynamically inside functions/methods
        'crash_handler', 'highscore_system', 'save_system',
        'boss_levels', 'pet_system', 'mystery_system',
        'npc_encounters', 'quirk_system', 'container_system',
        'fantasy_ui', 'sound_system', 'level_manager',
        'status_effects', 'paths', 'game_log',
        # The Seeker profile. _dad_key is written by the release build from
        # the PQ_DAD_KEY secret (tools/release/write_dad_key.py); it is never
        # in the repo, and is imported only inside seeker_codes.
        'seeker_codes', 'seeker_profile', 'seeker_session', 'achievements',
        'game_seeker', 'seeker_screen', '_dad_key',
        # The release self-test (main.py --selftest-saves; release.yml).
        'selftest',
        # Standard lib used in except blocks / logging
        'pickle', 'traceback', 'logging', 'logging.handlers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # NOTE: do NOT exclude `difflib` — pygame.font imports it
        # internally and the exe crashes on startup if it's missing.
        'tkinter', '_tkinter', 'unittest', 'pytest',
        'email', 'html', 'http', 'xml', 'pydoc',
        'doctest', 'ftplib',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.datas = [d for d in a.datas if not _is_excluded(d[0])]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PhilosophersQuest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # windowed mode (no console)
    disable_windowed_traceback=False,
    icon=('assets/icon.ico' if sys.platform == 'win32' and os.path.exists('assets/icon.ico') else None),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PhilosophersQuest',
)

# ── macOS: the .app ─────────────────────────────────────────────────────────
# Built on Apple Silicon by the release workflow (build-macos). Not signed
# with a Developer ID (no Apple Developer account yet): PyInstaller signs it
# ad hoc, which arm64 macOS requires to run at all, and the player clears
# Gatekeeper once with System Settings > Privacy & Security > Open Anyway.
# The icon is converted from the .ico by Pillow (requirements.txt).
if sys.platform == 'darwin':
    with open(os.path.join('src', 'layout.py'), encoding='utf-8') as _f:
        _VERSION = re.search(r'^VERSION\s*=\s*"([^"]+)"', _f.read(), re.M).group(1)
    app = BUNDLE(
        coll,
        name='PhilosophersQuest.app',
        icon='assets/icon.ico',
        bundle_identifier='com.raynfalllabs.philosophersquest',
        version=_VERSION,
        info_plist={
            'CFBundleName': "Philosopher's Quest",
            'CFBundleDisplayName': "Philosopher's Quest",
            'CFBundleShortVersionString': _VERSION,
            'CFBundleVersion': _VERSION,
            'LSMinimumSystemVersion': '11.0',     # every Apple Silicon Mac
            'LSApplicationCategoryType': 'public.app-category.role-playing-games',
            'NSHighResolutionCapable': True,
        },
    )
