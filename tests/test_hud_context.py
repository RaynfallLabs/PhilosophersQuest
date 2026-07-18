from types import SimpleNamespace


def test_hud_item_name_uses_unidentified_name_until_type_known():
    from hud_context import hud_item_name

    player = SimpleNamespace(known_item_ids=set(), knows_item_type=lambda item: False)
    item = SimpleNamespace(
        id="ring_of_secret_goodness",
        name="Ring of Secret Goodness",
        unidentified_name="plain brass ring",
        identified=False,
        buc="uncursed",
        buc_known=False,
        count=1,
    )

    assert hud_item_name(player, item) == "Plain Brass Ring"


def test_hud_item_name_uses_real_name_when_class_or_type_known():
    from hud_context import hud_item_name

    player = SimpleNamespace(known_item_ids=set(), knows_item_type=lambda item: True)
    item = SimpleNamespace(
        id="ring_of_secret_goodness",
        name="Ring of Secret Goodness",
        unidentified_name="plain brass ring",
        identified=False,
        buc="blessed",
        buc_known=True,
        count=2,
    )

    assert hud_item_name(player, item, include_count=True) == "{blessed} Ring of Secret Goodness x2"


def test_spawn_fit_color_inverts_item_and_monster_meaning():
    from hud_context import spawn_fit_color

    level = 20
    strong_item = spawn_fit_color(level, peak_floor=40, spread=10, kind="item")
    stale_item = spawn_fit_color(level, peak_floor=5, spread=10, kind="item")
    dangerous_monster = spawn_fit_color(level, peak_floor=40, spread=10, kind="monster")
    weak_monster = spawn_fit_color(level, peak_floor=5, spread=10, kind="monster")

    assert strong_item[1] > strong_item[0]     # green-leaning
    assert stale_item[0] > stale_item[1]       # red-leaning
    assert dangerous_monster[0] > dangerous_monster[1]
    assert weak_monster[1] > weak_monster[0]


def test_visible_context_rows_are_sight_limited_and_sorted():
    from hud_context import visible_context_rows

    player = SimpleNamespace(x=10, y=10, knows_item_type=lambda item: False)
    monster_near = SimpleNamespace(
        x=11, y=10, alive=True, is_allied=False, name="Giant Rat",
        kind="giant_rat", peak_floor=7, spread=9, footprint=(1, 1),
    )
    monster_out = SimpleNamespace(
        x=20, y=20, alive=True, is_allied=False, name="Hydra",
        kind="hydra", peak_floor=31, spread=12, footprint=(1, 1),
    )
    item_here = SimpleNamespace(
        x=10, y=10, id="mystery_wand", name="Wand of Healing",
        unidentified_name="crooked ash wand", identified=False,
        buc="uncursed", buc_known=False, count=1,
        peak_floor=3, spread=8, min_level=1,
    )

    monsters, items = visible_context_rows(
        player, [monster_out, monster_near], [item_here],
        {(10, 10), (11, 10)}, 20,
    )

    assert [row.label for row in monsters] == ["Giant Rat"]
    assert items[0].label == "Crooked Ash Wand"
    assert items[0].meta == "here"
