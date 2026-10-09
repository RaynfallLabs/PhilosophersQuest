"""Safety net: a body-plan drawing for any record without its own entry."""
from rig import *  # noqa


def pick(rec):
    col = tuple(rec.get('color') or (150, 120, 160))
    body = rec.get('body', '')

    def f(s, i, r):
        eye = s.lit((255, 230, 120))
        if body == 'undead':
            import undead
            undead.skel(s, mix(BONE, col, 0.3), eye)
        elif body == 'demon':
            bat_wings(s, mul(col, 0.7))
            man(s, col, mul(col, 0.8)); horns(s, BONE, 'up'); face(s, eye)
        elif body == 'construct':
            brute(s, col, eye)
        else:
            s.e(6, 10, 25, 28, col); s.e(11, 13, 20, 20, WHITE); s.e(14, 15, 17, 18, DARK)
    return f
