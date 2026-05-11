"""Game's menu-system methods, extracted from main.py.

This module defines :class:`MenuMixin`, which the real ``Game`` class inherits
alongside :class:`game_render.RenderMixin`.  The mixin owns ONLY menu open
logic, per-tab item collection, and key-input dispatch for the various item
menus (equip, eat, quaff, throw, wand, spell, scroll, identify, cook, drop,
examine, power).

Every helper a menu method calls that touches game state or rendering
(``self._display_name()``, ``self._cycle_tab``, ``self._advance_turn()``,
``self._equip_item()``, ``self._AZ_KEYS``, ``self._EQUIP_TABS``, etc.) is
resolved through Python's MRO on the concrete ``Game`` subclass.  Class-level
constants (``_EQUIP_TABS``, ``_COOK_TABS``, ``_AZ_KEYS``, ``_GoldDropEntry``,
``_DROP_MAX_VISIBLE``, ``_BENEFICIAL_EFFECTS``) remain on Game so they can be
co-located with related action code.
"""
from __future__ import annotations

import pygame

from food_system import (eat_food, eat_raw, get_available_compound_recipes)
from items import (Weapon, Armor, Shield, Corpse, Ingredient, Artifact,
                   Accessory, Wand, Scroll, Spellbook, Food, Potion)
from game_states import (
    STATE_PLAYER, STATE_EQUIP_MENU, STATE_ACCESSORY_MENU,
    STATE_WAND_MENU, STATE_SCROLL_MENU, STATE_IDENTIFY_MENU, STATE_COOK_MENU,
    STATE_TARGET, STATE_EAT_MENU, STATE_QUAFF_MENU,
    STATE_SPELL_MENU, STATE_LORE, STATE_EXAMINE,
    STATE_DROP_MENU, STATE_DROP_GOLD_INPUT,
    STATE_POWER_MENU, STATE_THROW_MENU,
)


class MenuMixin:
    # ------------------------------------------------------------------
    # Cook menu  (C key)
    # ------------------------------------------------------------------

    def _open_cook_menu(self):
        self.cook_menu_items = [
            i for i in self.player.inventory if isinstance(i, Ingredient)
        ]
        self.cook_compound_recipes = get_available_compound_recipes(self.player.inventory)
        if not self.cook_menu_items and not self.cook_compound_recipes:
            self.add_message("You have no ingredients to cook.", 'info')
            return
        # Auto-select first tab that has items
        if self.cook_menu_items:
            self._cook_tab = 0
        else:
            self._cook_tab = 1
        self.state = STATE_COOK_MENU

    def _get_cook_tab_items(self):
        """Return list for current cook tab."""
        if self._COOK_TABS[self._cook_tab][1] == 'single':
            return self.cook_menu_items
        return self.cook_compound_recipes

    def _cook_tab_has_items(self, idx):
        return (self.cook_menu_items if self._COOK_TABS[idx][1] == 'single'
                else self.cook_compound_recipes)

    def _cook_menu_input(self, key: int):
        if key == pygame.K_LEFT:
            self._cook_tab = self._cycle_tab(self._cook_tab, -1, len(self._COOK_TABS), self._cook_tab_has_items)
            return
        if key == pygame.K_RIGHT:
            self._cook_tab = self._cycle_tab(self._cook_tab, 1, len(self._COOK_TABS), self._cook_tab_has_items)
            return
        idx = self._AZ_KEYS.get(key)
        if idx is None:
            return
        tab_items = self._get_cook_tab_items()
        if idx >= len(tab_items):
            return
        self.state = STATE_PLAYER
        if self._COOK_TABS[self._cook_tab][1] == 'single':
            self._cook_item(tab_items[idx])
        else:
            self._cook_compound(tab_items[idx])

    # ------------------------------------------------------------------
    # Eat menu  (z key)
    # ------------------------------------------------------------------

    def _open_eat_menu(self):
        """Collect Food items and Ingredients for eating."""
        self.eat_menu_items = [
            i for i in self.player.inventory
            if isinstance(i, (Food, Ingredient))
        ]
        if not self.eat_menu_items:
            self.add_message("You have nothing to eat.", 'info')
            return
        self._eat_tab = 0
        for i, (_, filt) in enumerate(self._EAT_TABS):
            if any(filt(item) for item in self.eat_menu_items):
                self._eat_tab = i
                break
        self.state = STATE_EAT_MENU

    def _get_eat_tab_items(self):
        _, filt = self._EAT_TABS[self._eat_tab]
        return [i for i in self.eat_menu_items if filt(i)]

    def _eat_menu_input(self, key: int):
        if key == pygame.K_LEFT:
            self._eat_tab = self._cycle_tab(self._eat_tab, -1, len(self._EAT_TABS),
                lambda t: any(self._EAT_TABS[t][1](i) for i in self.eat_menu_items))
            return
        if key == pygame.K_RIGHT:
            self._eat_tab = self._cycle_tab(self._eat_tab, 1, len(self._EAT_TABS),
                lambda t: any(self._EAT_TABS[t][1](i) for i in self.eat_menu_items))
            return
        tab_items = self._get_eat_tab_items()
        idx = self._AZ_KEYS.get(key)
        if idx is None or idx >= len(tab_items):
            return
        self.state = STATE_PLAYER
        item = tab_items[idx]
        self.player.remove_from_inventory(item)
        if isinstance(item, Food):
            messages = eat_food(self.player, item)
            mtype = 'success' if self.player.sp > 0 else 'warning'
            for msg in messages:
                self.add_message(msg, mtype)
        else:
            messages = eat_raw(self.player, item)
            mtype = 'success' if self.player.sp > 0 else 'warning'
            for msg in messages:
                self.add_message(msg, mtype)
        self._advance_turn()

    # ------------------------------------------------------------------
    # Generic paged menu helpers
    # ------------------------------------------------------------------

    def _paged_menu_input(self, key, items) -> int | None:
        """Handle a-z selection within items. Returns index or None."""
        idx = self._AZ_KEYS.get(key)
        if idx is not None and idx < len(items):
            return idx
        return None

    def _get_page(self, items) -> list:
        """Return items (no pagination needed with a-z + tabs)."""
        return items[:26]

    # ------------------------------------------------------------------
    # Quaff menu  (Q key)
    # ------------------------------------------------------------------

    def _open_quaff_menu(self):
        self.quaff_menu_items = [
            i for i in self.player.inventory if isinstance(i, Potion)
        ]
        if not self.quaff_menu_items:
            self.add_message("You have no potions to quaff.", 'info')
            return
        self._menu_page = 0
        self.state = STATE_QUAFF_MENU

    def _quaff_menu_input(self, key: int):
        idx = self._paged_menu_input(key, self.quaff_menu_items)
        if idx is None:
            return
        self.state = STATE_PLAYER
        item = self.quaff_menu_items[idx]
        self.player.remove_from_inventory(item)

        from food_system import drink_potion
        item.identified = True
        self.player.known_item_ids.add(item.id)
        messages = drink_potion(self.player, item)
        _qs_pot = getattr(self, 'quirk_system', None)
        if _qs_pot:
            _qs_pot.on_potion_drunk()

        # Handle special signal: gain_level
        if '_gain_level' in messages:
            messages.remove('_gain_level')
            if self.dungeon_level > 1:
                self._change_level(self.dungeon_level - 1, enter_from_top=False)
                self.add_message("The potion propels you upward!", 'success')
            else:
                self.add_message("The potion shimmers -- but you're already on the first floor.", 'info')
        # Handle teleport signal
        if '_teleport' in messages:
            messages.remove('_teleport')
            self._teleport_player()
            self.add_message("The world lurches -- you're somewhere else!", 'warning')

        is_good = item.effect in self._BENEFICIAL_EFFECTS
        for msg in messages:
            self.add_message(msg, 'success' if is_good else 'danger')
        self._advance_turn()

    # ------------------------------------------------------------------
    # Throw menu  (T key)
    # ------------------------------------------------------------------

    def _open_throw_menu(self):
        """Open menu to select a potion, throwable weapon, or Soul Sphere."""
        potions = [i for i in self.player.inventory if isinstance(i, Potion)]
        weapons = [
            i for i in self.player.inventory
            if isinstance(i, Weapon) and self._is_throwable_weapon(i)
            and i is not self.player.weapon and i is not self.player.ranged_weapon
        ]
        spheres = [i for i in self.player.inventory
                   if isinstance(i, Artifact) and i.id in ('soul_sphere', 'unusual_soul_sphere')]
        self.throw_menu_items = potions + weapons + spheres
        if not self.throw_menu_items:
            self.add_message("You have nothing to throw.", 'info')
            return
        self._throw_tab = 0
        for i, (_, filt) in enumerate(self._THROW_TABS):
            if any(filt(item) for item in self.throw_menu_items):
                self._throw_tab = i
                break
        self.state = STATE_THROW_MENU

    def _get_throw_tab_items(self):
        _, filt = self._THROW_TABS[self._throw_tab]
        return [i for i in self.throw_menu_items if filt(i)]

    def _throw_menu_input(self, key: int):
        if key == pygame.K_LEFT:
            self._throw_tab = self._cycle_tab(self._throw_tab, -1, len(self._THROW_TABS),
                lambda t: any(self._THROW_TABS[t][1](i) for i in self.throw_menu_items))
            return
        if key == pygame.K_RIGHT:
            self._throw_tab = self._cycle_tab(self._throw_tab, 1, len(self._THROW_TABS),
                lambda t: any(self._THROW_TABS[t][1](i) for i in self.throw_menu_items))
            return
        tab_items = self._get_throw_tab_items()
        idx = self._AZ_KEYS.get(key)
        if idx is None or idx >= len(tab_items):
            return
        potion = tab_items[idx]
        self.state = STATE_PLAYER
        self._open_throw_targeting(potion)

    # ------------------------------------------------------------------
    # Equip menu  (w/W key -- geography quiz)
    # ------------------------------------------------------------------

    def _open_equip_menu(self):
        from items import ARMOR_SLOTS
        self.equip_menu_items = [
            i for i in self.player.inventory
            if isinstance(i, (Weapon, Armor, Shield, Accessory))
            and getattr(i, 'slot', '') != 'none'  # exclude carry-only items
        ]
        # Collect currently equipped items for the unequip section
        self.equip_menu_equipped = []
        if self.player.weapon:
            self.equip_menu_equipped.append(('weapon', self.player.weapon))
        if self.player.ranged_weapon:
            self.equip_menu_equipped.append(('ranged_weapon', self.player.ranged_weapon))
        if self.player.shield:
            self.equip_menu_equipped.append(('shield', self.player.shield))
        for slot_name, slot_item in zip(ARMOR_SLOTS, self.player.armor_slots):
            if slot_item:
                self.equip_menu_equipped.append((slot_name, slot_item))
        for idx, acc_item in enumerate(self.player.accessory_slots):
            if acc_item is not None:
                self.equip_menu_equipped.append((f'accessory_{idx}', acc_item))
        if self.player.amulet_slot:
            self.equip_menu_equipped.append(('amulet', self.player.amulet_slot))
        if not self.equip_menu_items and not self.equip_menu_equipped:
            self.add_message("Nothing to equip or unequip.", 'info')
            return
        self._menu_tab = 0
        # Auto-select first tab with items
        for i, (_, filt) in enumerate(self._EQUIP_TABS):
            if filt is None:
                if self.equip_menu_equipped:
                    self._menu_tab = i
                    break
            elif any(filt(item) for item in self.equip_menu_items):
                self._menu_tab = i
                break
        self.state = STATE_EQUIP_MENU

    def _get_equip_tab_items(self):
        """Return items for the current equip tab."""
        label, filt = self._EQUIP_TABS[self._menu_tab]
        if filt is None:
            return None  # unequip tab
        return [i for i in self.equip_menu_items if filt(i)]

    def _equip_menu_input(self, key: int):
        # Left/Right: switch tabs
        if key == pygame.K_LEFT:
            def _eq_has(t):
                _, filt = self._EQUIP_TABS[t]
                if filt is None:
                    return bool(self.equip_menu_equipped)
                return any(filt(i) for i in self.equip_menu_items)
            self._menu_tab = self._cycle_tab(self._menu_tab, -1, len(self._EQUIP_TABS), _eq_has)
            return
        if key == pygame.K_RIGHT:
            def _eq_has(t):
                _, filt = self._EQUIP_TABS[t]
                if filt is None:
                    return bool(self.equip_menu_equipped)
                return any(filt(i) for i in self.equip_menu_items)
            self._menu_tab = self._cycle_tab(self._menu_tab, 1, len(self._EQUIP_TABS), _eq_has)
            return

        # a-z keys: select from current tab
        idx = self._AZ_KEYS.get(key)
        if idx is None:
            return

        tab_items = self._get_equip_tab_items()
        if tab_items is not None:
            if idx < len(tab_items):
                self.state = STATE_PLAYER
                self._equip_item(tab_items[idx])
        else:
            if idx < len(self.equip_menu_equipped):
                self.state = STATE_PLAYER
                slot_name, slot_item = self.equip_menu_equipped[idx]
                self._unequip_slot(slot_name, slot_item)

    # ------------------------------------------------------------------
    # Accessory menu  (r key -- history quiz)
    # ------------------------------------------------------------------

    def _open_accessory_menu(self):
        self.accessory_menu_items = [
            i for i in self.player.inventory
            if isinstance(i, Accessory)
        ]
        if not self.accessory_menu_items:
            self.add_message("You have no rings or amulets to equip.", 'info')
            return
        self.state = STATE_ACCESSORY_MENU

    def _accessory_menu_input(self, key: int):
        idx = self._AZ_KEYS.get(key)
        if idx is None or idx >= len(self.accessory_menu_items):
            return
        self.state = STATE_PLAYER
        self._equip_accessory(self.accessory_menu_items[idx])

    # ------------------------------------------------------------------
    # Wand menu  (u key -- science quiz)
    # ------------------------------------------------------------------

    def _open_wand_menu(self):
        self.wand_menu_items = [
            i for i in self.player.inventory if isinstance(i, Wand)
        ]
        if not self.wand_menu_items:
            self.add_message("You have no wands to use.", 'info')
            return
        self._menu_page = 0
        self.state = STATE_WAND_MENU

    def _wand_menu_input(self, key: int):
        idx = self._paged_menu_input(key, self.wand_menu_items)
        if idx is None or idx >= len(self.wand_menu_items):
            return
        self.state = STATE_PLAYER
        self._invoke_wand(self.wand_menu_items[idx])

    # ------------------------------------------------------------------
    # Spell menu  (Z key)
    # ------------------------------------------------------------------

    def _open_spell_menu(self):
        if self.player.has_effect('silenced'):
            self.add_message("You are silenced and cannot cast spells!", 'warning')
            return
        if not self.player.known_spells:
            self.add_message("You have not learned any spells.", 'warning')
            return
        self.spell_menu_items = list(self.player.known_spells.keys())
        self.state = STATE_SPELL_MENU

    def _spell_menu_input(self, key: int):
        if key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER
            return
        idx = None
        if pygame.K_a <= key <= pygame.K_z:
            idx = key - pygame.K_a
        if idx is None or idx >= len(self.spell_menu_items):
            return
        self._invoke_spell(self.spell_menu_items[idx])

    # ------------------------------------------------------------------
    # Scroll/Spellbook menu  (r key -- grammar quiz)
    # ------------------------------------------------------------------

    def _open_scroll_menu(self):
        if self.player.has_effect('silenced'):
            self.add_message("You are silenced and cannot read!", 'warning')
            return
        self.scroll_menu_items = [
            i for i in self.player.inventory if isinstance(i, (Scroll, Spellbook))
        ]
        if not self.scroll_menu_items:
            self.add_message("You have no scrolls or spellbooks to read.", 'info')
            return
        self._scroll_tab = 0
        for i, (_, filt) in enumerate(self._SCROLL_TABS):
            if any(filt(item) for item in self.scroll_menu_items):
                self._scroll_tab = i
                break
        self.state = STATE_SCROLL_MENU

    def _get_scroll_tab_items(self):
        _, filt = self._SCROLL_TABS[self._scroll_tab]
        return [i for i in self.scroll_menu_items if filt(i)]

    def _scroll_menu_input(self, key: int):
        if key == pygame.K_LEFT:
            self._scroll_tab = self._cycle_tab(self._scroll_tab, -1, len(self._SCROLL_TABS),
                lambda t: any(self._SCROLL_TABS[t][1](i) for i in self.scroll_menu_items))
            return
        if key == pygame.K_RIGHT:
            self._scroll_tab = self._cycle_tab(self._scroll_tab, 1, len(self._SCROLL_TABS),
                lambda t: any(self._SCROLL_TABS[t][1](i) for i in self.scroll_menu_items))
            return
        tab_items = self._get_scroll_tab_items()
        idx = self._AZ_KEYS.get(key)
        if idx is None or idx >= len(tab_items):
            return
        self.state = STATE_PLAYER
        item = tab_items[idx]
        if isinstance(item, Spellbook):
            self._learn_from_spellbook(item)
        else:
            self._read_scroll(item)

    # ------------------------------------------------------------------
    # Identify menu  (I key -- philosophy quiz)
    # ------------------------------------------------------------------

    def _open_identify_menu(self):
        # Require the Philosopher's Shard in inventory
        has_shard = any(
            getattr(i, 'id', '') == 'philosophers_shard'
            for i in self.player.inventory
        )
        if not has_shard:
            self.add_message("You need the Philosopher's Shard to identify items.", 'warning')
            return
        inv_items = [
            i for i in self.player.inventory
            if hasattr(i, 'identified') and not i.identified
               and i.id not in self.player.known_item_ids
        ]
        ground_items = [
            i for i in self.ground_items
            if i.x == self.player.x and i.y == self.player.y
               and hasattr(i, 'identified') and not i.identified
               and i.id not in self.player.known_item_ids
        ]
        # Corpses on the current tile that haven't been lore-identified yet
        _lore_known = getattr(self.player, 'lore_known_monster_ids', set())
        corpses = [
            i for i in self.ground_items
            if i.x == self.player.x and i.y == self.player.y
               and isinstance(i, Corpse)
               and not i.lore_identified
               and getattr(i, 'monster_id', '') not in _lore_known
        ]
        # Store as (item, is_ground, is_corpse) tuples
        self.identify_menu_items = (
            [(i, False, False) for i in inv_items]
            + [(i, True,  False) for i in ground_items]
            + [(i, True,  True)  for i in corpses]
        )
        if not self.identify_menu_items:
            self.add_message("Nothing here to identify or examine.", 'info')
            return
        self._menu_page = 0
        self.state = STATE_IDENTIFY_MENU

    def _identify_menu_input(self, key: int):
        idx = self._paged_menu_input(key, self.identify_menu_items)
        if idx is None:
            return
        self.state = STATE_PLAYER
        item, is_ground, is_corpse = self.identify_menu_items[idx]
        if is_corpse:
            self._examine_corpse_direct(item)
        else:
            self._identify_item(item)

    # ------------------------------------------------------------------
    # Drop menu  (d key)
    # ------------------------------------------------------------------

    def _open_drop_menu(self):
        items = []
        if getattr(self, 'player_gold', 0) > 0:
            items.append(self._GoldDropEntry())
        items += self.player.inventory[:]
        if not items:
            self.add_message("You have nothing to drop.", 'info')
            return
        self.drop_menu_items = items
        self._menu_tab = 0
        self._drop_scroll = 0
        self.state = STATE_DROP_MENU

    def _get_drop_tab_items(self):
        _, filt = self._DROP_TABS[self._menu_tab]
        if filt is None:
            return self.drop_menu_items
        return [i for i in self.drop_menu_items if filt(i)]

    def _drop_menu_input(self, key: int):
        if key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER
            return
        if key == pygame.K_LEFT:
            def _dr_has(t):
                _, filt = self._DROP_TABS[t]
                return bool(self.drop_menu_items) if filt is None else any(filt(i) for i in self.drop_menu_items)
            self._menu_tab = self._cycle_tab(self._menu_tab, -1, len(self._DROP_TABS), _dr_has)
            return
        if key == pygame.K_RIGHT:
            def _dr_has(t):
                _, filt = self._DROP_TABS[t]
                return bool(self.drop_menu_items) if filt is None else any(filt(i) for i in self.drop_menu_items)
            self._menu_tab = self._cycle_tab(self._menu_tab, 1, len(self._DROP_TABS), _dr_has)
            return
        # Up/Down: scroll within the current tab
        if key == pygame.K_UP:
            self._drop_scroll = max(0, getattr(self, '_drop_scroll', 0) - 1)
            return
        if key == pygame.K_DOWN:
            tab_items = self._get_drop_tab_items()
            max_scroll = max(0, len(tab_items) - self._DROP_MAX_VISIBLE)
            self._drop_scroll = min(getattr(self, '_drop_scroll', 0) + 1, max_scroll)
            return
        tab_items = self._get_drop_tab_items()
        idx = self._AZ_KEYS.get(key)
        if idx is None or idx >= len(tab_items):
            return
        item = tab_items[idx]
        if isinstance(item, self._GoldDropEntry):
            self.drop_gold_input = ''
            self.state = STATE_DROP_GOLD_INPUT
            return
        self.state = STATE_PLAYER
        self._do_drop_item(item)

    # ------------------------------------------------------------------
    # Examine menu  (E key -- inspect identified item)
    # ------------------------------------------------------------------

    def _open_examine_menu(self):
        """Open a list of all identified items in player inventory (and equipment)."""
        qs = getattr(self, 'quirk_system', None)
        if qs:
            qs.on_examine_used()
        items = []
        for item in self.player.inventory:
            if self._item_is_known(item):
                items.append(item)
        if self.player.weapon and self._item_is_known(self.player.weapon):
            if self.player.weapon not in items:
                items.append(self.player.weapon)
        if self.player.ranged_weapon and self._item_is_known(self.player.ranged_weapon):
            if self.player.ranged_weapon not in items:
                items.append(self.player.ranged_weapon)
        if self.player.shield and self._item_is_known(self.player.shield):
            if self.player.shield not in items:
                items.append(self.player.shield)
        for slot_item in self.player.armor_slots:
            if slot_item and self._item_is_known(slot_item):
                if slot_item not in items:
                    items.append(slot_item)
        for acc in self.player.accessory_slots:
            if acc and self._item_is_known(acc):
                if acc not in items:
                    items.append(acc)

        if not items:
            self.add_message("You have no identified items to examine.", 'info')
            return
        self.examine_menu_items = items
        self._examine_tab = 0
        # Auto-select first tab with items
        for i, (_, filt) in enumerate(self._EXAMINE_TABS):
            if any(filt(item) for item in items):
                self._examine_tab = i
                break
        self.state = STATE_EXAMINE

    def _get_examine_tab_items(self):
        _, filt = self._EXAMINE_TABS[self._examine_tab]
        return [i for i in self.examine_menu_items if filt(i)]

    def _examine_menu_input(self, key: int):
        if key == pygame.K_ESCAPE:
            self.state = STATE_PLAYER
            return
        if key == pygame.K_LEFT:
            self._examine_tab = self._cycle_tab(self._examine_tab, -1, len(self._EXAMINE_TABS),
                lambda t: any(self._EXAMINE_TABS[t][1](i) for i in self.examine_menu_items))
            return
        if key == pygame.K_RIGHT:
            self._examine_tab = self._cycle_tab(self._examine_tab, 1, len(self._EXAMINE_TABS),
                lambda t: any(self._EXAMINE_TABS[t][1](i) for i in self.examine_menu_items))
            return
        tab_items = self._get_examine_tab_items()
        idx = self._AZ_KEYS.get(key)
        if idx is None or idx >= len(tab_items):
            return
        self._lore_subject = tab_items[idx]
        self.state = STATE_LORE

    # ------------------------------------------------------------------
    # Power menu  (V key -- active quirk powers)
    # ------------------------------------------------------------------

    def _open_power_menu(self):
        from quirk_system import _ACTIVE_POWER_DEFS
        pl = self.player
        unlocked = getattr(pl, 'unlocked_quirks', set())
        power_uses = getattr(pl, 'power_uses', {})
        power_cds  = getattr(pl, 'power_cooldowns', {})
        powers = []
        for pid, pdef in _ACTIVE_POWER_DEFS.items():
            if pid not in unlocked:
                continue
            if pdef.get('uses', 0) > 0:
                remaining = power_uses.get(pid, 0)
                if remaining > 0:
                    powers.append((pid, pdef, remaining, 0))
            else:
                cd = power_cds.get(pid, 0)
                powers.append((pid, pdef, 0, cd))

        # Charmander Stuffie grants "Fire Breath" when carried
        if any(getattr(i, 'id', '') == 'charmander_stuffie' for i in pl.inventory):
            _fb_cd = power_cds.get('stuffie_fire_breath', 0)
            _fb_def = {
                'label': 'Fire Breath',
                'desc': 'The Stuffie glows and you breathe a cone of fire at all visible enemies.',
                'cooldown': 500, 'uses': 0,
            }
            powers.append(('stuffie_fire_breath', _fb_def, 0, _fb_cd))

        # Dreamspun Sketchbook grants "Manifest" when carried
        if any(getattr(i, 'id', '') == 'dreamspun_sketchbook' for i in pl.inventory):
            _sk_cd = power_cds.get('sketch_manifest', 0)
            _sk_def = {
                'label': 'Manifest',
                'desc': 'Sketch a visible creature and bring it to life as a temporary ally.',
                'cooldown': 500, 'uses': 0,
            }
            powers.append(('sketch_manifest', _sk_def, 0, _sk_cd))

        # Gleipnir grants "Bind Odinkiller" when carried
        if any(getattr(i, 'id', '') == 'gleipnir' for i in pl.inventory):
            _bind_def = {
                'label': 'Bind Odinkiller',
                'desc': 'Reset Fenrir\'s rage and paralyze him briefly. Costs 1 permanent stat point.',
                'cooldown': 0, 'uses': 0,
            }
            powers.append(('bind_odinkiller', _bind_def, 0, 0))

        # Elder Blood powers (Ciri build)
        if (self.secret_build or {}).get('_elder_blood'):
            _ELDER_POWERS = [
                ('elder_blink', {
                    'label': 'Blink',
                    'desc': 'Teleport to safety. The Elder Blood bends space.',
                    'cooldown': 8, 'uses': 0,
                }),
                ('elder_charge', {
                    'label': 'Charge',
                    'desc': 'Channel Elder Blood — next melee attack deals 3x damage.',
                    'cooldown': 12, 'uses': 0,
                }),
                ('elder_scream', {
                    'label': 'Scream',
                    'desc': 'Unleash the Elder Blood — cold damage to all visible enemies.',
                    'cooldown': 20, 'uses': 0,
                }),
            ]
            for epid, epdef in _ELDER_POWERS:
                cd = power_cds.get(epid, 0)
                powers.append((epid, epdef, 0, cd))

        # Scales of Michael grants "Summon the Heavenly Host"
        if (any(getattr(i, 'id', '') == 'scales_of_michael' for i in pl.inventory)
                and not getattr(self, 'heavenly_host_active', False)):
            _scales_def = {
                'label': 'Summon the Heavenly Host',
                'desc': 'While active, for every locust Abaddon summons, an angel descends to oppose it.',
                'cooldown': 0, 'uses': 1,
            }
            powers.append(('summon_heavenly_host', _scales_def, 1, 0))

        if not powers:
            self.add_message("You have no active powers. Earn quirks to unlock them!", 'info')
            return
        self._power_menu_list = powers
        self.state = STATE_POWER_MENU

    def _power_menu_input(self, key: int):
        idx = self._AZ_KEYS.get(key)
        if idx is None or idx >= len(self._power_menu_list):
            return
        self.state = STATE_PLAYER
        pid, pdef, uses_remaining, cooldown = self._power_menu_list[idx]
        if cooldown > 0:
            self.add_message(f"{pdef['label']} is cooling down ({cooldown} turns).", 'warning')
            return
        if pdef.get('uses', 0) > 0 and uses_remaining <= 0:
            self.add_message(f"{pdef['label']} has no uses remaining.", 'warning')
            return
        if not self._activate_power(pid):
            self._advance_turn()

    def _activate_power(self, pid: str) -> bool:
        """Activate a power. Returns True if it defers turn advance (e.g. targeting)."""
        from quirk_system import _ACTIVE_POWER_DEFS
        from status_effects import DEBUFFS
        pdef = _ACTIVE_POWER_DEFS.get(pid, {})
        pl = self.player
        label = pdef.get('label', pid)
        # Consume uses or set cooldown
        if pdef.get('uses', 0) > 0:
            pl.power_uses[pid] = max(0, pl.power_uses.get(pid, 1) - 1)
        elif pdef.get('cooldown', 0) > 0:
            pl.power_cooldowns[pid] = pdef['cooldown']

        # --- Effect dispatch ---
        if pid == 'metabolic' or pid == 'iron_ration':
            pl.restore_sp(100)
            self.add_message(f"{label}: You surge with renewed stamina! (+100 SP)", 'success')

        elif pid == 'time_dilation':
            pl.add_effect('time_stopped', 10)
            self.add_message(f"{label}: Time crystallises around you -- 10 turns of stillness!", 'success')

        elif pid == 'ouroboros':
            pl.add_effect('hasted', 20)
            pl.add_effect('shielded', 20)
            pl.add_effect('regenerating', 20)
            self.add_message(f"{label}: The circle completes -- Haste, Shield, and Regen surge through you!", 'success')

        elif pid == 'eye_storm':
            pl.add_effect('invisible', 10)
            pl.add_effect('blessed', 10)
            self.add_message(f"{label}: You become one with the calm at the eye of the storm.", 'success')

        elif pid == 'ancestral_q':
            pl.add_effect('clairvoyant', 20)
            self.add_message(f"{label}: Ancestral visions flood your mind -- the dungeon unfolds!", 'success')

        elif pid == 'sage_counsel':
            pl.add_effect('blessed', 15)
            self.add_message(f"{label}: A sage's wisdom descends -- all quiz timers extended.", 'success')

        elif pid == 'focused_scholar' or pid == 'arcane_surge':
            pl.add_effect('brilliance', 10)
            if pid == 'arcane_surge':
                pl.restore_mp(pl.max_mp)
                self.add_message(f"{label}: Arcane energy floods your mind! (MP fully restored, Brilliance 10t)", 'success')
            else:
                self.add_message(f"{label}: Your mind reaches a razor edge. (Brilliance 10t)", 'success')

        elif pid == 'mind_fortress':
            cleared = []
            mental = {'confused', 'blinded', 'hallucinating', 'hallucinating_pot', 'stunned', 'feared'}
            for eff in mental:
                if pl.has_effect(eff):
                    pl.status_effects.pop(eff, None)
                    cleared.append(eff.replace('_', ' '))
            if cleared:
                self.add_message(f"{label}: Mental walls slam shut -- {', '.join(cleared)} cleared!", 'success')
            else:
                self.add_message(f"{label}: Your mind is already fortress-clear.", 'info')

        elif pid == 'philosophers_stone':
            pl.add_effect('blessed', 10)
            pl.add_effect('brilliance', 10)
            self.add_message(f"{label}: Gold-bright wisdom suffuses your thoughts.", 'success')

        elif pid == 'atlas_burden':
            pl.add_effect('heroism', 20)
            self.add_message(f"{label}: You bear the weight of the world -- Heroism for 20 turns!", 'success')

        elif pid == 'zeus_bolt':
            pl.add_effect('shock_resist', 15)
            pl.add_effect('hasted', 15)
            self.add_message(f"{label}: Lightning courses through you -- Shock Resist + Hasted 15t!", 'success')

        elif pid == 'gorgon_ward':
            pl.add_effect('sleep_resist', 15)
            pl.add_effect('displacement', 15)
            self.add_message(f"{label}: The gorgon's ward wraps around you -- Sleep Resist + Displacement 15t.", 'success')

        elif pid == 'phoenix_rising':
            pl.hp = pl.max_hp
            self.add_message(f"{label}: You rise from the ashes -- HP fully restored!", 'success')

        elif pid == 'iron_will':
            pl.add_effect('shielded', 10)
            pl.add_effect('reflecting', 10)
            self.add_message(f"{label}: Iron will takes hold -- Shielded + Reflecting for 10 turns.", 'success')

        elif pid == 'battle_trance':
            pl.add_effect('heroism', 15)
            self.add_message(f"{label}: Battle trance descends -- Heroism for 15 turns!", 'success')

        elif pid == 'second_sight':
            pl.add_effect('telepathy', 15)
            pl.add_effect('clairvoyant', 15)
            self.add_message(f"{label}: The second sight opens -- Telepathy + Clairvoyance for 15 turns.", 'success')

        elif pid == 'shadow_step':
            pl.add_effect('invisible', 5)
            pl.add_effect('phasing', 5)
            self.add_message(f"{label}: You slip between shadows -- Invisible + Phasing for 5 turns.", 'success')

        elif pid == 'death_wish':
            pl.add_effect('heroism', 10)
            pl.add_effect('hasted', 10)
            self.add_message(f"{label}: You embrace the edge -- Heroism + Hasted for 10 turns!", 'success')

        elif pid == 'wandering_star':
            self._teleport_player()
            self.add_message(f"{label}: You vanish and reappear elsewhere!", 'success')

        elif pid == 'mirror_mind':
            pl.add_effect('reflecting', 10)
            pl.add_effect('magic_resist', 10)
            self.add_message(f"{label}: Your mind becomes a mirror -- Reflecting + Magic Resist 10t.", 'success')

        elif pid == 'venom_lore':
            pl.add_effect('poison_resist', 20)
            if pl.has_effect('poisoned'):
                pl.status_effects.pop('poisoned', None)
                self.add_message(f"{label}: Poison cured. Poison Resist for 20 turns.", 'success')
            else:
                self.add_message(f"{label}: Venom knowledge shields you -- Poison Resist for 20 turns.", 'success')

        elif pid == 'war_cry':
            pl.add_effect('hasted', 8)
            self.add_message(f"{label}: A battle cry erupts -- Hasted for 8 turns!", 'success')

        elif pid == 'temporal_shield':
            pl.add_effect('shielded', 25)
            self.add_message(f"{label}: A temporal barrier slows all impacts -- Shielded for 25 turns.", 'success')

        elif pid == 'mystic_eye':
            pl.add_effect('telepathy', 15)
            pl.add_effect('clairvoyant', 15)
            pl.add_effect('warning', 15)
            self.add_message(f"{label}: The mystic eye opens wide -- Telepathy + Clairvoyance + Warning 15t.", 'success')

        elif pid == 'life_drain':
            restored = max(1, pl.max_hp // 4)
            pl.restore_hp(restored)
            self.add_message(f"{label}: Vital energy flows back -- +{restored} HP!", 'success')

        elif pid == 'reality_anchor':
            cleared = [e for e in list(pl.status_effects.keys()) if e in DEBUFFS]
            for e in cleared:
                pl.status_effects.pop(e, None)
            if cleared:
                self.add_message(f"{label}: Reality snaps into place -- all debuffs cleared!", 'success')
            else:
                self.add_message(f"{label}: Nothing to anchor. You are clear.", 'info')

        elif pid == 'runic_armor':
            pl.add_effect('fire_shield', 10)
            pl.add_effect('cold_shield', 10)
            pl.add_effect('shock_resist', 10)
            self.add_message(f"{label}: Runes blaze -- Fire Shield + Cold Shield + Shock Resist 10t!", 'success')

        elif pid == 'astral_form':
            pl.add_effect('levitating', 8)
            pl.add_effect('invisible', 8)
            pl.add_effect('phasing', 8)
            self.add_message(f"{label}: You transcend the physical -- Levitate + Invisible + Phase 8t.", 'success')

        # --- Elder Blood powers (Ciri) ---
        elif pid == 'elder_blink':
            self._teleport_player()
            self.add_message("The Elder Blood bends space — you vanish and reappear!", 'success')
            pl.power_cooldowns['elder_blink'] = 8

        elif pid == 'elder_charge':
            pl.status_effects['empowered'] = 1
            self.add_message("Elder Blood surges through your blade — next strike deals 3x damage!", 'success')
            pl.power_cooldowns['elder_charge'] = 12

        elif pid == 'elder_scream':
            from dice import roll as _es_roll
            base = _es_roll('4d8')
            scaled = self._int_scaled_damage(base)
            visible = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            kills = 0
            for m in visible:
                m.take_damage(scaled)
                if not m.alive:
                    self._on_monster_killed(m)
                    kills += 1
            self.add_message(
                f"The Elder Blood SCREAMS! {len(visible)} creatures take {scaled} cold damage! ({kills} slain)",
                'success')
            pl.power_cooldowns['elder_scream'] = 20

        elif pid == 'sketch_manifest':
            # Enter targeting mode — quiz + pet spawn on confirm
            px, py = pl.x, pl.y
            candidates = [
                m for m in self.monsters
                if m.alive and (m.x, m.y) in self.visible
            ]
            candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))
            if not candidates:
                self.add_message("You open the sketchbook, but there is nothing to draw.", 'warning')
                return False
            self._target_candidates = candidates
            self._target_idx = 0
            self._power_targeting = True
            self._pending_power = 'sketch_manifest'
            self.target_cursor_x = candidates[0].x
            self.target_cursor_y = candidates[0].y
            self.state = STATE_TARGET
            self.add_message(
                "You flip open the Dreamspun Sketchbook... select a creature to sketch! "
                "Arrow keys to aim, TAB to cycle, ENTER to begin drawing.",
                'info')
            return True  # defer _advance_turn()

        elif pid == 'stuffie_fire_breath':
            # Enter targeting mode — damage applied on confirm
            px, py = pl.x, pl.y
            candidates = [
                m for m in self.monsters
                if m.alive and (m.x, m.y) in self.visible
            ]
            candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))
            self._target_candidates = candidates
            self._target_idx = 0
            self._power_targeting = True
            self._pending_power = 'stuffie_fire_breath'
            if candidates:
                self.target_cursor_x = candidates[0].x
                self.target_cursor_y = candidates[0].y
            else:
                self.target_cursor_x = px
                self.target_cursor_y = py
            self.state = STATE_TARGET
            self.add_message(
                "The Charmander Stuffie glows warm... aim your fire breath! "
                "Arrow keys to move, TAB to cycle, ENTER to fire, ESC to cancel.",
                'info')
            return True  # defer _advance_turn()

        elif pid == 'bind_odinkiller':
            fenrir = next((m for m in self.monsters
                           if m.alive and m.kind == 'fenrir_wolf'), None)
            if not fenrir:
                self.add_message("Bind Odinkiller: Fenrir is not here.", 'warning')
                return
            fenrir.reset_rage()
            fenrir.status_effects['paralyzed'] = 2
            self.add_message(
                "You hurl the shimmering ribbon at Fenrir!", 'info')
            self.add_message(
                "Gleipnir wraps around the World-Wolf's massive jaws! "
                "He strains, but the binding holds!", 'success')
            self.add_message(
                "Fenrir's rage subsides -- for now.", 'success')
            # Rotating stat cost: STR -> DEX -> CON
            _stat_cycle = ['STR', 'DEX', 'CON']
            _stat_names = {'STR': 'strength', 'DEX': 'agility', 'CON': 'vitality'}
            bind_count = getattr(self, '_gleipnir_bind_count', 0)
            stat = _stat_cycle[bind_count % 3]
            current = getattr(pl, stat)
            if current > 1:
                setattr(pl, stat, current - 1)
                self.add_message(
                    f"The binding tears something from you... "
                    f"your {_stat_names[stat]} diminishes permanently. ({stat} -1)",
                    'danger')
            self._gleipnir_bind_count = bind_count + 1

        elif pid == 'summon_heavenly_host':
            self.heavenly_host_active = True
            self.add_message(
                "You raise the Scales of Michael toward the heavens!", 'info')
            self.add_message(
                "A choir of light answers! The Heavenly Host will counter "
                "the Destroyer's locusts!", 'success')

        else:
            self.add_message(f"Used {label}.", 'info')

        return False  # turn consumed immediately
