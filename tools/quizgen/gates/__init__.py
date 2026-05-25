"""Per-subject structural gates.

Each module exposes:

    PER_QUESTION_GATES: list[tuple[str, Callable[[dict], Optional[str]]]]
        — ordered list of (gate_name, gate_function) pairs. Each gate
          function takes a question dict and returns None on PASS or a
          short string reason on FAIL.

    SOFT_WARN_GATES: frozenset[str]
        — optional. Gates listed here flag rather than fail; rewrites
          with only soft-warn flags still apply.

Subject-agnostic gates are defined once (in philosophy.py / cooking.py /
geography.py) and reused across subjects via direct imports.
"""
