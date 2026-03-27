# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Philosopher's Quest.
Run from the project root:
    pyinstaller PhilosophersQuest.spec
Output: dist\PhilosophersQuest\  (portable folder — zip for distribution)

Saves, highscores, and crash reports go to %APPDATA%\PhilosophersQuest\
"""

import os

block_cipher = None

# ── Data files to bundle ────────────────────────────────────────────────────
# Format: (source_path_or_glob, dest_folder_inside_bundle)
added_files = [
    # Game data
    ('data/monsters.json',          'data'),
    ('data/hints.json',             'data'),
    ('data/items',                  'data/items'),
    ('data/questions',              'data/questions'),
    # Assets
    ('assets/fonts',                'assets/fonts'),
    ('assets/tiles',                'assets/tiles'),
    ('assets/textures',             'assets/textures'),
]

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
        'status_effects', 'paths',
        # Standard lib used in except blocks
        'pickle', 'traceback',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', '_tkinter', 'unittest', 'pytest',
        'email', 'html', 'http', 'xml', 'pydoc',
        'doctest', 'difflib', 'ftplib', 'argparse',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

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
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
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
