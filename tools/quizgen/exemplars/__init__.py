"""Per-subject hand-authored exemplars.

Each module exports an ``EXEMPLARS`` list of ``(name, question_dict)``
tuples, plus a ``validate_all()`` function that runs the full gate suite
against every exemplar. Exemplars are voice-anchoring questions — the
agent reads them to learn the subject's voice before producing rewrites
at scale.

Modules:
    grammar — 35 exemplars, 5 content pillars + voice showcase +
              etymology-meaning-shift extension × 5 tiers
"""
