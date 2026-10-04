"""Pluggable visual-effects handlers.

Each file in this package implements one handler for the
``EffectsRuntime`` -- see ``src/effects_runtime.py`` for the host and
``docs/design/effects_runtime.md`` for the authoring guide.

Phase 1 ships with two handlers:

    chain_aura.py          -- ChainAuraPulse: in-quiz per-answer feedback
                              for math combat (border aura + pulse +
                              milestone bursts).
    fullscreen_takeover.py -- FullscreenTakeover: full-screen rune-circle
                              + candle-glow + headline, used by the
                              Divine Intercession and Unicorn-bond
                              celebrations.

New handlers plug in by (1) adding a config block to
``data/ui/effects_config.json``, (2) adding a handler class in a new
file here, and (3) registering it in
``effects_runtime.build_default_runtime``.
"""
