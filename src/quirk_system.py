"""
quirk_system.py — 50 Bofuri-style traits earned through counterintuitive play.
Progress stored in player.quirk_progress (dict).
Unlocked quirks in player.unlocked_quirks (set).
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import Game

# Debuff effect IDs used for Fenrir tracking
_DEBUFF_EFFECTS = frozenset({
    'paralyzed','sleeping','stunned','confused','blinded','hallucinating',
    'poisoned','diseased','petrifying','strangulation','fumbling','slowed',
    'aggravated','teleportitis','feared','charmed','cursed','weakened','bleeding',
})

# All quiz subjects for Sibyl's all-timer bonus
_ALL_SUBJECTS = ('math','geography','history','animal','cooking','science',
                 'philosophy','grammar','economics','theology')


class QuirkSystem:
    def __init__(self, game: 'Game'):
        self.game = game

    # ------------------------------------------------------------------ helpers
    @property
    def _pl(self):
        return self.game.player

    def _p(self, key, default=0):
        return getattr(self._pl, 'quirk_progress', {}).get(key, default)

    def _sp(self, key, value):
        prog = getattr(self._pl, 'quirk_progress', None)
        if prog is None:
            self._pl.quirk_progress = {}
            prog = self._pl.quirk_progress
        prog[key] = value

    def _inc(self, key, amount=1):
        self._sp(key, self._p(key, 0) + amount)

    def _set_add(self, key, value):
        s = self._p(key, None)
        if not isinstance(s, set):
            s = set()
        s.add(value)
        self._sp(key, s)

    def _set_has(self, key, value):
        return value in self._p(key, set())

    def _set_len(self, key):
        return len(self._p(key, set()))

    def _dict_inc(self, key, sub_key, amount=1):
        d = self._p(key, None)
        if not isinstance(d, dict):
            d = {}
        d[sub_key] = d.get(sub_key, 0) + amount
        self._sp(key, d)

    def _dict_get(self, key, sub_key, default=0):
        d = self._p(key, {})
        if not isinstance(d, dict):
            return default
        return d.get(sub_key, default)

    def is_unlocked(self, qid: str) -> bool:
        return qid in getattr(self._pl, 'unlocked_quirks', set())

    def _award(self, qid: str, name: str, apply_fn):
        if self.is_unlocked(qid):
            return
        u = getattr(self._pl, 'unlocked_quirks', None)
        if u is None:
            self._pl.unlocked_quirks = set()
        self._pl.unlocked_quirks.add(qid)
        apply_fn(self._pl)
        self.game.add_message(f"TRAIT UNLOCKED: {name}", 'loot')
        self.game.add_message(
            f"  >> {_QUIRK_EFFECTS.get(qid, '')}",
            'info'
        )

    def _timer_bonus(self, subject: str, amount: int):
        def _apply(pl):
            b = getattr(pl, 'quiz_timer_bonuses', None)
            if b is None:
                pl.quiz_timer_bonuses = {}
                b = pl.quiz_timer_bonuses
            b[subject] = b.get(subject, 0) + amount
        return _apply

    # ================================================================ NOTIFY API
    # All hooks funnel through these methods called from main.py / food_system.py

    def on_wait(self, near_monsters: bool):
        """Called when player presses '.' wait command."""
        # Odin (#3): 12960 total waits
        self._inc('wait_total')
        if self._p('wait_total') >= 12960 and not self.is_unlocked('odin'):
            self._award('odin', "Odin's Vigil",
                        lambda pl: pl.add_effect('telepathy', -1))

        # Buddha (#10): 500 waits near hostile monsters
        if near_monsters:
            self._inc('wait_near_monsters')
            if self._p('wait_near_monsters') >= 500 and not self.is_unlocked('buddha'):
                self._award('buddha', "The Buddha's Stillness",
                            lambda pl: pl.add_effect('displacement', -1))

    def on_move(self):
        """Called whenever player moves to a new tile."""
        # Ahasverus (#38): 15000 tile moves -> permanent searching
        self._inc('tile_moves')
        if self._p('tile_moves') >= 15000 and not self.is_unlocked('ahasverus'):
            self._award('ahasverus', "Ahasverus",
                        lambda pl: pl.add_effect('searching', -1))

    def on_stair_use(self, new_level: int):
        """Called when player uses stairs (any direction)."""
        # Cerberus (#49): 50 stair uses -> warning permanent
        self._inc('stair_uses')
        if self._p('stair_uses') >= 300 and not self.is_unlocked('cerberus'):
            self._award('cerberus', "Cerberus",
                        lambda pl: pl.add_effect('warning', -1))

        # Ragnarök (#50): descend to level 100 at <=10 HP
        if new_level == 100 and self._pl.hp <= 10 and not self.is_unlocked('ragnarok'):
            self._award('ragnarok', "Ragnarök's Survivor",
                        lambda pl: pl.apply_stat_bonus('CON', 5))

        # Ariadne (#41): fast floor exits — record entry turn each floor change
        self._sp('ariadne_entry_turn', self.game.turn_count)

    def on_floor_entered(self, dungeon_level: int):
        """Called after arriving on a new floor."""
        self._sp('ariadne_entry_turn', self.game.turn_count)

    def on_stairs_taken_fast(self):
        """Call this when stairs are used AND we were within 30 turns of floor entry."""
        entry = self._p('ariadne_entry_turn', -9999)
        if self.game.turn_count - entry <= 30:
            self._inc('ariadne_fast_exits')
            if self._p('ariadne_fast_exits') >= 10 and not self.is_unlocked('ariadne'):
                self._award('ariadne', "Ariadne's Thread",
                            lambda pl: pl.apply_stat_bonus('INT', 1))

    def on_floor_explored(self, explored_pct: float):
        """Called when FOV is refreshed. explored_pct = explored/total walkable tiles."""
        if explored_pct >= 0.99:
            self._inc('fully_explored_floors')
            if self._p('fully_explored_floors') >= 5 and not self.is_unlocked('theseus'):
                self._award('theseus', "Theseus in the Labyrinth",
                            lambda pl: pl.apply_stat_bonus('PER', 1))

    def on_quiz_answer(self, subject: str, correct: bool, chain: int,
                       while_blinded: bool, while_confused: bool,
                       while_hallucinating: bool, while_feared: bool,
                       wrong_this_session: int, score_this_session: int):
        """Called after every individual quiz answer."""
        if correct:
            # Tiresias (#2): 25 correct while blinded
            if while_blinded:
                self._inc('correct_while_blinded')
                if self._p('correct_while_blinded') >= 25 and not self.is_unlocked('tiresias'):
                    self._award('tiresias', "Tiresias' Gift",
                                lambda pl: pl.apply_stat_bonus('PER', 2))

            # Anansi (#19): 20 correct while confused
            if while_confused:
                self._inc('correct_while_confused')
                if self._p('correct_while_confused') >= 20 and not self.is_unlocked('anansi'):
                    self._award('anansi', "Anansi's Clarity",
                                lambda pl: pl.apply_stat_bonus('INT', 1))

            # Medusa (#46): blinded episode with correct answer
            if while_blinded and not self._p('medusa_episode_answered', False):
                self._sp('medusa_episode_answered', True)
                self._inc('medusa_episodes_answered')
                if self._p('medusa_episodes_answered') >= 5 and not self.is_unlocked('medusa'):
                    self._award('medusa', "Medusa's Gaze",
                                lambda pl: pl.apply_stat_bonus('DEX', 2))

    def on_quiz_complete(self, mode: str, subject: str, score: int,
                         correct_count: int, wrong_count: int, success: bool,
                         while_blinded: bool, while_confused: bool,
                         while_hallucinating: bool):
        """Called when a full quiz session ends."""
        # Apollo (#23): 10 max-chain hits
        if subject == 'math' and mode == 'chain':
            weapon = self._pl.weapon
            if weapon and score >= weapon.max_chain_length:
                self._inc('max_chain_hits')
                if self._p('max_chain_hits') >= 10 and not self.is_unlocked('apollo'):
                    self._award('apollo', "Apollo's Perfection",
                                self._timer_bonus('math', 3))

        # Cassandra (#12): pass threshold quiz with >=2 wrong answers
        if mode == 'threshold' and success and wrong_count >= 2:
            self._inc('cassandra_scrapes')
            if self._p('cassandra_scrapes') >= 10 and not self.is_unlocked('cassandra'):
                self._award('cassandra', "Cassandra's Persistence",
                            lambda pl: pl.apply_stat_bonus('WIS', 1))

    def on_kill(self, monster_kind: str, chain_score: int, ranged: bool,
                unarmed: bool, hp_pct_before: float, is_feared: bool):
        """Called whenever player kills a monster."""
        # Musashi (#7): 30 kills at chain exactly 1
        if chain_score == 1:
            self._inc('chain1_kills')
            if self._p('chain1_kills') >= 30 and not self.is_unlocked('musashi'):
                self._award('musashi', "Musashi's Empty Strike",
                            lambda pl: pl.quirk_progress.update({'musashi_active': True}))

        # Valkyrie (#37): 25 ranged kills
        if ranged:
            self._inc('ranged_kills')
            if self._p('ranged_kills') >= 25 and not self.is_unlocked('valkyrie'):
                self._award('valkyrie', "The Valkyrie's Eye",
                            lambda pl: pl.apply_stat_bonus('DEX', 1))

        # Beowulf (#27): 10 unarmed wins
        if unarmed:
            self._inc('unarmed_wins')
            if self._p('unarmed_wins') >= 10 and not self.is_unlocked('beowulf'):
                self._award('beowulf', "Beowulf's Vow",
                            lambda pl: pl.quirk_progress.update({'beowulf_unarmed_bonus': 5}))

        # Gawain (#40): 6 wins starting at <=40% HP
        if hp_pct_before <= 0.40:
            self._inc('gawain_wins')
            if self._p('gawain_wins') >= 6 and not self.is_unlocked('gawain'):
                self._award('gawain', "Gawain's Bargain",
                            lambda pl: pl.apply_stat_bonus('CON', 1))

        # Cu Chulainn (#43): 5 combat wins while feared
        if is_feared:
            self._inc('cuchulainn_wins')
            if self._p('cuchulainn_wins') >= 5 and not self.is_unlocked('cuchulainn'):
                self._award('cuchulainn', "Cu Chulainn's Riastrad",
                            lambda pl: pl.apply_stat_bonus('STR', 1))

        # Kali (#45): 100 kills of same monster type
        self._dict_inc('kali_kills', monster_kind)
        if self._dict_get('kali_kills', monster_kind) >= 100 and not self.is_unlocked('kali'):
            self._award('kali', "Kali's Dance",
                        self._timer_bonus('theology', 3))

        # Thor (#26): 30 combats with same weapon
        weapon = self._pl.weapon
        if weapon and not ranged:
            wid = weapon.id
            self._dict_inc('thor_weapon_combats', wid)
            if self._dict_get('thor_weapon_combats', wid) >= 30 and not self.is_unlocked('thor'):
                self._sp('thor_qualifying_weapon', wid)
                def _apply_thor(pl, _wid=wid):
                    if pl.weapon and pl.weapon.id == _wid:
                        pl.weapon.enchant_bonus = getattr(pl.weapon, 'enchant_bonus', 0) + 2
                    pl.quirk_progress['thor_weapon_id'] = _wid
                    pl.quirk_progress['thor_enchant_pending'] = True
                self._award('thor', "Thor's Oath", _apply_thor)

        # Athena (#24): see 50 distinct monster types
        if len(getattr(self._pl, 'known_monster_ids', set())) >= 50 and not self.is_unlocked('athena'):
            self._award('athena', "Athena's Owl",
                        self._timer_bonus('history', 4))

    def on_take_damage(self, amount: int, pct_of_max: float):
        """Called whenever player takes any damage."""
        # Rasputin (#8): survive at <=5% HP 5 times
        if self._pl.hp > 0 and (self._pl.hp / max(1, self._pl.max_hp)) <= 0.05:
            if not self._p('rasputin_was_low', False):
                self._sp('rasputin_was_low', True)
                self._inc('rasputin_survivals')
                if self._p('rasputin_survivals') >= 5 and not self.is_unlocked('rasputin'):
                    self._award('rasputin', "Rasputin's Constitution",
                                lambda pl: pl.apply_stat_bonus('CON', 2))
        else:
            self._sp('rasputin_was_low', False)

        # Green Knight (#47): single hit >=30% max_hp, survive
        if pct_of_max >= 0.30 and self._pl.hp > 0:
            self._inc('green_knight_survivals')
            if self._p('green_knight_survivals') >= 5 and not self.is_unlocked('green_knight'):
                self._award('green_knight', "The Green Knight",
                            lambda pl: pl.apply_stat_bonus('CON', 1))

    def on_trap_triggered(self, trap_type: str):
        """Called when a container trap fires."""
        self._set_add('job_trap_types', trap_type)
        if self._set_len('job_trap_types') >= 5 and not self.is_unlocked('job'):
            self._award('job', "Job's Endurance",
                        lambda pl: pl.add_effect('levitating', -1))

    def on_lockpick_fail(self, container_id: str, dungeon_level: int):
        """Called when lockpick quiz fails on a trapped chest."""
        key = f"{container_id}_{dungeon_level}"
        self._set_add('sisyphus_chests', key)
        if self._set_len('sisyphus_chests') >= 10 and not self.is_unlocked('sisyphus'):
            self._award('sisyphus', "Sisyphus' Mastery",
                        self._timer_bonus('economics', 5))

    def on_harvest(self, monster_kind: str, success: bool,
                   monster_applies_poisoned: bool):
        """Called after a harvest attempt (success or fail)."""
        if not success:
            return

        # Enkidu (#31): harvest 20 distinct species
        self._set_add('enkidu_harvested', monster_kind)
        if self._set_len('enkidu_harvested') >= 20 and not self.is_unlocked('enkidu'):
            self._award('enkidu', "Enkidu's Wildness",
                        lambda pl: pl.apply_stat_bonus('STR', 1))

        # Asclepius (#17): 15 distinct poison-monster species
        if monster_applies_poisoned:
            self._set_add('asclepius_species', monster_kind)
            if self._set_len('asclepius_species') >= 15 and not self.is_unlocked('asclepius'):
                self._award('asclepius', "Asclepius' Serpent",
                            self._timer_bonus('animal', 4))

        # Mithridates (#1): cross-ref — monster both poisoned you AND you ate it
        if monster_applies_poisoned and self._set_has('mithridates_poisoned_by', monster_kind):
            self._set_add('mithridates_eaten', monster_kind)
            if self._set_len('mithridates_eaten') >= 5 and not self.is_unlocked('mithridates'):
                self._award('mithridates', "The Mithridates Protocol",
                            lambda pl: pl.add_effect('poison_resist', -1))

    def on_food_eaten(self, quality: int, source_monster: str, bonus_type: str,
                      ingredient_id: str):
        """Called when cooked food is eaten."""
        # Tantalus (#16): 15 quality-0 ruined meals
        if quality == 0:
            self._inc('ruined_meals')
            if self._p('ruined_meals') >= 15 and not self.is_unlocked('tantalus'):
                self._award('tantalus', "Tantalus' Resolve",
                            lambda pl: pl.apply_stat_bonus('STR', 1))

        # Persephone (#34): quality-5 meals from 5 distinct ingredient sources
        if quality == 5 and ingredient_id:
            self._set_add('persephone_quality5', ingredient_id)
            if self._set_len('persephone_quality5') >= 5 and not self.is_unlocked('persephone'):
                self._award('persephone', "Persephone's Descent",
                            lambda pl: pl.quirk_progress.update({'persephone_active': True}))

        # Circe (#39): cook from each distinct bonus_type category
        if bonus_type:
            self._set_add('circe_bonus_types', bonus_type)
            if self._set_len('circe_bonus_types') >= 5 and not self.is_unlocked('circe'):
                self._award('circe', "Circe's Cauldron",
                            self._timer_bonus('cooking', 4))

        # Siegfried (#6): eat ingredients from monsters with 5 distinct status-effect attack types
        mith_src = source_monster or ''
        if mith_src:
            sig_types = self._p('siegfried_effect_types_eaten', None)
            if not isinstance(sig_types, set):
                sig_types = set()
            src_effects = self._p('siegfried_monster_effects', {})
            if isinstance(src_effects, dict) and mith_src in src_effects:
                for eff in src_effects[mith_src]:
                    sig_types.add(eff)
            self._sp('siegfried_effect_types_eaten', sig_types)
            if len(sig_types) >= 5 and not self.is_unlocked('siegfried'):
                self._award('siegfried', "Siegfried's Bath",
                            lambda pl: pl.add_effect('magic_resist', -1))

    def on_potion_drunk(self):
        """Called when a potion is consumed."""
        if self._pl.has_effect('hallucinating') or self._pl.has_effect('hallucinating_pot'):
            self._inc('potions_while_hallucinating')
            if self._p('potions_while_hallucinating') >= 10 and not self.is_unlocked('dionysus'):
                self._award('dionysus', "Dionysus' Vision",
                            self._timer_bonus('philosophy', 3))

    def on_scroll_read(self, scroll_id: str, was_identified: bool):
        """Called when a scroll is successfully read."""
        # Scheherazade (#4): 12 unique scroll types read unidentified
        if not was_identified:
            self._set_add('scheherazade_scrolls', scroll_id)
            if self._set_len('scheherazade_scrolls') >= 12 and not self.is_unlocked('scheherazade'):
                self._award('scheherazade', "Scheherazade's Tongue",
                            self._timer_bonus('grammar', 5))

        # Hermes (#35): use scroll_of_teleportation 8 times
        if scroll_id == 'scroll_of_teleportation':
            self._inc('hermes_teleports')
            if self._p('hermes_teleports') >= 8 and not self.is_unlocked('hermes'):
                self._award('hermes', "Hermes' Wings",
                            lambda pl: pl.quirk_progress.update({'hermes_active': True}))

    def on_wand_zapped(self, wand_id: str, was_identified: bool):
        """Called when a wand is zapped."""
        # Merlin (#9): 10 unique wand types zapped unidentified
        if not was_identified:
            self._set_add('merlin_wands', wand_id)
            if self._set_len('merlin_wands') >= 10 and not self.is_unlocked('merlin'):
                self._award('merlin', "Merlin's Apprenticeship",
                            self._timer_bonus('science', 4))

    def on_item_equipped(self, item_id: str, item_type: str, slot: str):
        """Called when any item is equipped (weapon, armor, shield, accessory)."""
        # Penelope (#21): 100 total armor equip/unequip actions
        if item_type in ('armor', 'shield'):
            self._inc('penelope_count')
            if self._p('penelope_count') >= 100 and not self.is_unlocked('penelope'):
                self._award('penelope', "Penelope's Mastery",
                            self._timer_bonus('geography', 3))

        # Hephaestus (#11): same armor piece equipped 15 times
        if item_type == 'armor':
            self._dict_inc('hephaestus_counts', item_id)
            cnt = self._dict_get('hephaestus_counts', item_id)
            if cnt >= 15 and not self.is_unlocked('hephaestus'):
                def _apply_heph(pl, _slot=slot):
                    pl.quirk_progress['hephaestus_slot'] = _slot
                self._award('hephaestus', "Hephaestus' Obsession", _apply_heph)

        # Jormungandr (#29): same weapon equip/unequip 20 times
        if item_type == 'weapon':
            self._dict_inc('jormungandr_counts', item_id)
            if self._dict_get('jormungandr_counts', item_id) >= 20 and not self.is_unlocked('jormungandr'):
                def _apply_jorm(pl, _id=item_id):
                    pl.quirk_progress['jormungandr_weapon_id'] = _id
                self._award('jormungandr', "Jormungandr's Cycle", _apply_jorm)

    def on_item_unequipped(self, item_id: str, item_type: str, slot: str):
        """Called when any item is unequipped."""
        # Penelope count
        if item_type in ('armor', 'shield'):
            self._inc('penelope_count')
            if self._p('penelope_count') >= 100 and not self.is_unlocked('penelope'):
                self._award('penelope', "Penelope's Mastery",
                            self._timer_bonus('geography', 3))

        # Hephaestus count (unequip also counts)
        if item_type == 'armor':
            self._dict_inc('hephaestus_counts', item_id)

        # Jormungandr count (unequip also counts)
        if item_type == 'weapon':
            self._dict_inc('jormungandr_counts', item_id)
            if self._dict_get('jormungandr_counts', item_id) >= 20 and not self.is_unlocked('jormungandr'):
                def _apply_jorm(pl, _id=item_id):
                    pl.quirk_progress['jormungandr_weapon_id'] = _id
                self._award('jormungandr', "Jormungandr's Cycle", _apply_jorm)

    def on_prayer(self, hp_pct: float):
        """Called when prayer succeeds."""
        # Fisher King (#18): pray at <=15% HP 6 times
        if hp_pct <= 0.15:
            self._inc('fisher_king_prayers')
            if self._p('fisher_king_prayers') >= 6 and not self.is_unlocked('fisher_king'):
                self._award('fisher_king', "The Fisher King's Vigil",
                            lambda pl: pl.quirk_progress.update({'fisher_king_active': True}))

    def on_recall_lore(self):
        """Called when recall lore is used."""
        # Norns (#28): use recall lore 20 times in a run
        self._inc('recall_lore_uses')
        if self._p('recall_lore_uses') >= 20 and not self.is_unlocked('norns'):
            self._award('norns', "The Norns' Thread",
                        lambda pl: pl.quirk_progress.update({'norns_active': True}))

    def on_spell_cast(self, hp_pct: float):
        """Called when a spell is successfully cast."""
        # Morgan le Fay (#42): cast spell at <=20% HP 6 times
        if hp_pct <= 0.20:
            self._inc('morgan_spells')
            if self._p('morgan_spells') >= 6 and not self.is_unlocked('morgan'):
                self._award('morgan', "Morgan le Fay",
                            lambda pl: pl.apply_stat_bonus('INT', 2))

    def on_examine_used(self):
        """Called when the examine menu is opened."""
        # Narcissus (#48): examine 30 times
        self._inc('narcissus_examines')
        if self._p('narcissus_examines') >= 30 and not self.is_unlocked('narcissus'):
            self._award('narcissus', "Narcissus",
                        lambda pl: pl.apply_stat_bonus('PER', 1))

    def on_status_applied(self, effect_id: str, source_monster_kind):
        """Called when a status effect is applied to the player."""
        # Mithridates: track which monster types have poisoned you
        if effect_id == 'poisoned' and source_monster_kind:
            self._set_add('mithridates_poisoned_by', source_monster_kind)

        # Siegfried: track monster -> effect type mapping
        if source_monster_kind and effect_id in ('poisoned','blinded','paralyzed','feared','stunned'):
            src_effects = self._p('siegfried_monster_effects', {})
            if not isinstance(src_effects, dict):
                src_effects = {}
            if source_monster_kind not in src_effects:
                src_effects[source_monster_kind] = set()
            src_effects[source_monster_kind].add(effect_id)
            self._sp('siegfried_monster_effects', src_effects)

        # Medusa: reset "answered this episode" flag when newly blinded
        if effect_id == 'blinded':
            self._sp('medusa_episode_answered', False)

    def on_disease_drain(self, stat: str, amount: int):
        """Called when disease ticks and drains a stat."""
        # Paracelsus (#5): disease drains 5+ stat points total
        self._inc('disease_drain_total', amount)
        if self._p('disease_drain_total') >= 5 and not self.is_unlocked('paracelsus'):
            self._award('paracelsus', "Paracelsus' Doctrine",
                        lambda pl: pl.add_effect('drain_resist', -1))

    def on_turn(self):
        """Called every advance_turn. Tracks per-turn things."""
        pl = self._pl

        # Shiva (#30): 100 turns under hallucinating
        if pl.has_effect('hallucinating') or pl.has_effect('hallucinating_pot'):
            self._inc('hallucinating_turns')
            if self._p('hallucinating_turns') >= 100 and not self.is_unlocked('shiva'):
                self._award('shiva', "Shiva's Third Eye",
                            self._timer_bonus('philosophy', 5))

        # Fenrir (#44): 150 debuff turns total
        for eff in _DEBUFF_EFFECTS:
            if pl.has_effect(eff):
                self._inc('fenrir_debuff_turns')
                if self._p('fenrir_debuff_turns') >= 150 and not self.is_unlocked('fenrir'):
                    self._award('fenrir', "Fenrir's Chains",
                                lambda p: p.apply_stat_bonus('CON', 1))
                break

        # Prometheus (#20): bleeding episodes of >=5 turns
        if pl.has_effect('bleeding'):
            self._inc('prometheus_current_bleed')
            if self._p('prometheus_current_bleed') >= 5:
                if not self._p('prometheus_episode_counted', False):
                    self._sp('prometheus_episode_counted', True)
                    self._inc('prometheus_episodes')
                    if self._p('prometheus_episodes') >= 10 and not self.is_unlocked('prometheus'):
                        self._award('prometheus', "Prometheus Unbound",
                                    lambda pl2: pl2.add_effect('regenerating', -1))
        else:
            self._sp('prometheus_current_bleed', 0)
            self._sp('prometheus_episode_counted', False)

        # Loki (#25): track turns worn for each cursed item
        loki_worn = self._p('loki_worn_turns', None)
        if not isinstance(loki_worn, dict):
            loki_worn = {}
        loki_done = self._p('loki_done_items', None)
        if not isinstance(loki_done, set):
            loki_done = set()
        for slot_item in (
            [pl.weapon, pl.shield] +
            list(pl.armor_slots) +
            list(pl.accessory_slots) +
            [pl.amulet_slot]
        ):
            if slot_item and getattr(slot_item, 'cursed', False):
                sid = slot_item.id
                loki_worn[sid] = loki_worn.get(sid, 0) + 1
                if loki_worn[sid] >= 10:
                    loki_done.add(sid)
        self._sp('loki_worn_turns', loki_worn)
        self._sp('loki_done_items', loki_done)
        if len(loki_done) >= 5 and not self.is_unlocked('loki'):
            self._award('loki', "Loki's Gambit",
                        lambda p: p.apply_stat_bonus('WIS', 2))

        # Orpheus (#15): track consecutive non-combat turns
        if self._p('orpheus_combat_this_turn', False):
            self._sp('orpheus_no_combat_streak', 0)
            self._sp('orpheus_combat_this_turn', False)
        else:
            # check if there's a monster adjacent
            any_adj = any(
                m.alive and abs(m.x - pl.x) <= 1 and abs(m.y - pl.y) <= 1
                for m in self.game.monsters
            )
            if any_adj:
                self._inc('orpheus_no_combat_streak')
                streak = self._p('orpheus_no_combat_streak')
                if streak >= 10:
                    self._sp('orpheus_no_combat_streak', 0)
                    self._inc('orpheus_sessions')
                    if self._p('orpheus_sessions') >= 5 and not self.is_unlocked('orpheus'):
                        self._award('orpheus', "Orpheus' Lyre",
                                    lambda p: p.quirk_progress.update({'orpheus_active': True}))
            else:
                self._sp('orpheus_no_combat_streak', 0)

        # Sibyl (#36): 500 correct answers before level 20
        if (not self.is_unlocked('sibyl') and
                getattr(self.game, 'correct_answers', 0) >= 500 and
                self.game.dungeon_level < 20):
            def _apply_sibyl(pl2):
                b = getattr(pl2, 'quiz_timer_bonuses', None)
                if b is None:
                    pl2.quiz_timer_bonuses = {}
                    b = pl2.quiz_timer_bonuses
                for subj in _ALL_SUBJECTS:
                    b[subj] = b.get(subj, 0) + 2
            self._award('sibyl', "The Sibyl of Cumae", _apply_sibyl)

    def on_combat_started(self):
        """Called when player initiates or is involved in combat."""
        self._sp('orpheus_combat_this_turn', True)

    def on_status_reflected(self):
        """Called when reflecting status blocks a monster status attack."""
        self._inc('perseus_blocks')
        if self._p('perseus_blocks') >= 5 and not self.is_unlocked('perseus'):
            self._award('perseus', "Perseus' Reflection",
                        lambda pl: pl.quirk_progress.update({'perseus_active': True}))

    def on_teleport(self):
        """Called for any teleport (wand or teleportitis tick)."""
        self._inc('hermes_teleports')
        if self._p('hermes_teleports') >= 8 and not self.is_unlocked('hermes'):
            self._award('hermes', "Hermes' Wings",
                        lambda pl: pl.quirk_progress.update({'hermes_active': True}))


# Map quirk IDs to short effect descriptions shown on unlock
_QUIRK_EFFECTS = {
    'mithridates':   "Permanent poison & disease immunity.",
    'tiresias':      "PER +2",
    'odin':          "Permanent telepathy — all monsters visible.",
    'scheherazade':  "Grammar quiz timer +5 seconds.",
    'paracelsus':    "Permanent drain & disease resistance.",
    'siegfried':     "Permanent magic resistance.",
    'musashi':       "Chain-1 damage uses 2nd multiplier instead of weakest.",
    'rasputin':      "CON +2",
    'merlin':        "Science quiz timer +4 seconds.",
    'buddha':        "Permanent displacement — monsters may miss.",
    'hephaestus':    "Equip threshold -1 for that armor slot.",
    'cassandra':     "WIS +1",
    'sisyphus':      "Economics quiz timer +5 seconds.",
    'job':           "Permanent levitation — immune to floor traps.",
    'orpheus':       "Monsters start slowed 5 turns on every floor you enter.",
    'tantalus':      "STR +1",
    'asclepius':     "Animal quiz timer +4 seconds.",
    'fisher_king':   "Prayer cooldown permanently halved.",
    'anansi':        "INT +1",
    'prometheus':    "Permanent regeneration (1 HP/turn).",
    'penelope':      "Geography quiz timer +3 seconds.",
    'dionysus':      "Philosophy quiz timer +3 seconds.",
    'apollo':        "Math quiz timer +3 seconds.",
    'athena':        "History quiz timer +4 seconds.",
    'loki':          "WIS +2",
    'thor':          "That weapon gains +2 enchant bonus permanently.",
    'beowulf':       "Unarmed attacks deal +5 base damage.",
    'norns':         "Recall lore cooldown reduced by 50%.",
    'jormungandr':   "That weapon's max chain length +1.",
    'shiva':         "Philosophy quiz timer +5 seconds.",
    'enkidu':        "STR +1",
    'perseus':       "Enemy status effects last 50% fewer turns on you.",
    'theseus':       "PER +1",
    'persephone':    "Cooking max chain becomes 6 instead of 5.",
    'hermes':        "Hasted duration permanently doubled.",
    'sibyl':         "All quiz timers +2 seconds.",
    'valkyrie':      "DEX +1",
    'ahasverus':     "Permanent searching — auto-reveal adjacent tiles.",
    'circe':         "Cooking quiz timer +4 seconds.",
    'gawain':        "CON +1",
    'ariadne':       "INT +1",
    'morgan':        "INT +2",
    'cuchulainn':    "STR +1",
    'fenrir':        "CON +1",
    'kali':          "Theology quiz timer +3 seconds.",
    'medusa':        "DEX +2",
    'green_knight':  "CON +1",
    'narcissus':     "PER +1",
    'cerberus':      "Permanent warning — sense monsters through walls.",
    'ragnarok':      "CON +5",
}
