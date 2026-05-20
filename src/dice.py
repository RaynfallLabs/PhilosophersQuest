import re
import random


def roll_duration(spec) -> int:
    """Resolve an effect duration that may be either a plain int (fixed)
    or a dice-notation string like '1d4' (variable).

    Returns the rolled integer. -1 is preserved (permanent effect sentinel).
    """
    if isinstance(spec, int):
        return spec
    if isinstance(spec, str):
        return roll(spec)
    raise TypeError(f"duration must be int or dice string, got {type(spec).__name__}")


def roll(notation: str) -> int:
    """Parse and roll dice notation like '2d6+3', '1d20', 'd6'.

    Returns the integer result of the roll.
    Raises ValueError for invalid notation.
    """
    notation = notation.strip().lower().replace(' ', '')
    match = re.fullmatch(r'(\d*)d(\d+)([+-]\d+)?', notation)
    if not match:
        raise ValueError(f"Invalid dice notation: {notation!r}")

    count_str, sides_str, modifier_str = match.groups()
    count = int(count_str) if count_str else 1
    sides = int(sides_str)
    modifier = int(modifier_str) if modifier_str else 0

    if count < 1:
        raise ValueError(f"Dice count must be >= 1: {notation!r}")
    if sides < 2:
        raise ValueError(f"Dice must have >= 2 sides: {notation!r}")

    return sum(random.randint(1, sides) for _ in range(count)) + modifier
