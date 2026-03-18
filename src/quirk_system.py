"""
quirk_system.py -- 50 Bofuri-style traits earned through counterintuitive play.
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
        self.game.add_message(f"  Reward: {_QUIRK_EFFECTS.get(qid, '')}", 'success')
        trigger = _QUIRK_TRIGGER.get(qid, '')
        flavor  = _QUIRK_FLAVOR.get(qid, '')
        if trigger:
            self.game.add_message(f"  {trigger}", 'info')
        if flavor:
            self.game.add_message(f'  "{flavor}"', 'info')

    def _timer_bonus(self, subject: str, amount: int):
        def _apply(pl):
            b = getattr(pl, 'quiz_timer_bonuses', None)
            if b is None:
                pl.quiz_timer_bonuses = {}
                b = pl.quiz_timer_bonuses
            b[subject] = b.get(subject, 0) + amount
        return _apply

    def _all_timer_bonus(self, amount: int):
        def _apply(pl):
            b = getattr(pl, 'quiz_timer_bonuses', None)
            if b is None:
                pl.quiz_timer_bonuses = {}
                b = pl.quiz_timer_bonuses
            for subj in _ALL_SUBJECTS:
                b[subj] = b.get(subj, 0) + amount
        return _apply

    def _award_power(self, qid: str, name: str, apply_fn):
        """Award a power-based quirk and initialise power_uses / power_cooldowns."""
        if self.is_unlocked(qid):
            return
        u = getattr(self._pl, 'unlocked_quirks', None)
        if u is None:
            self._pl.unlocked_quirks = set()
        self._pl.unlocked_quirks.add(qid)
        apply_fn(self._pl)
        # Initialise tracking from definition
        pdef = _ACTIVE_POWER_DEFS.get(qid, {})
        pl = self._pl
        if not hasattr(pl, 'power_uses') or pl.power_uses is None:
            pl.power_uses = {}
        if not hasattr(pl, 'power_cooldowns') or pl.power_cooldowns is None:
            pl.power_cooldowns = {}
        if pdef.get('uses', 0) > 0:
            pl.power_uses[qid] = pdef['uses']
        if pdef.get('cooldown', 0) > 0:
            pl.power_cooldowns[qid] = 0  # ready immediately
        self.game.add_message(f"POWER UNLOCKED: {name}", 'loot')
        self.game.add_message(f"  Effect: {_QUIRK_EFFECTS.get(qid, '')}", 'success')
        trigger = _QUIRK_TRIGGER.get(qid, '')
        flavor  = _QUIRK_FLAVOR.get(qid, '')
        if trigger:
            self.game.add_message(f"  {trigger}", 'info')
        if flavor:
            self.game.add_message(f'  "{flavor}"', 'info')

    def tick_powers(self):
        """Decrement all active power cooldowns by 1 each turn."""
        pl = self._pl
        cds = getattr(pl, 'power_cooldowns', None)
        if not cds:
            return
        for pid in list(cds.keys()):
            if cds[pid] > 0:
                cds[pid] -= 1

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
        # Wanderlust (#69): 20000 moves -> SP drain halved
        if self._p('tile_moves') >= 20000 and not self.is_unlocked('wanderlust_q'):
            self._award('wanderlust_q', "The Endless Wanderer",
                        lambda pl: pl.quirk_progress.update({'wanderlust_active': True}))
        # Metabolic (#88 power): 5000 moves
        if self._p('tile_moves') >= 5000 and not self.is_unlocked('metabolic'):
            self._award_power('metabolic', "Metabolic Surge", lambda pl: None)
        # Iron Ration (#80 power): 15000 moves
        if self._p('tile_moves') >= 15000 and not self.is_unlocked('iron_ration'):
            self._award_power('iron_ration', "Iron Ration", lambda pl: None)
        # Shadow Step (#81 power): 2500 moves while invisible
        if self._pl.has_effect('invisible'):
            self._inc('invisible_moves')
            if self._p('invisible_moves') >= 2500 and not self.is_unlocked('shadow_step'):
                self._award_power('shadow_step', "Shadow Step", lambda pl: None)

    def on_stair_use(self, new_level: int):
        """Called when player uses stairs (any direction)."""
        # Cerberus (#49): 300 stair uses -> warning permanent
        self._inc('stair_uses')
        if self._p('stair_uses') >= 300 and not self.is_unlocked('cerberus'):
            self._award('cerberus', "Cerberus",
                        lambda pl: pl.add_effect('warning', -1))

        # Ragnarok (#50): descend to level 100 at <=10 HP
        if new_level == 100 and self._pl.hp <= 10 and not self.is_unlocked('ragnarok'):
            self._award('ragnarok', "Ragnarok's Survivor",
                        lambda pl: pl.apply_stat_bonus('CON', 5))

        # Atalanta (#65): escape 10 floors within 25 turns
        entry = self._p('ariadne_entry_turn', -9999)
        if self.game.turn_count - entry <= 25:
            self._inc('atalanta_fast25')
            if self._p('atalanta_fast25') >= 10 and not self.is_unlocked('atalanta'):
                self._award('atalanta', "Winged Feet",
                            lambda pl: pl.apply_stat_bonus('DEX', 2))

        # Reset eye-of-storm damage flag on every floor change
        self._sp('eye_storm_damage_this_floor', False)
        # Reset guardian session hits on floor change
        self._sp('guardian_session_hits', 0)

    def on_floor_entered(self, dungeon_level: int):
        """Called after arriving on a new floor."""
        self._sp('ariadne_entry_turn', self.game.turn_count)
        self._sp('eye_storm_damage_this_floor', False)
        self._sp('guardian_session_hits', 0)
        # Eye of Storm: check if previous floor was completed damage-free
        if self._p('eye_storm_no_damage_prev', False):
            self._inc('eye_storm_clean_floors')
            if self._p('eye_storm_clean_floors') >= 5 and not self.is_unlocked('eye_storm'):
                self._award_power('eye_storm', "Eye of the Storm", lambda pl: None)
        self._sp('eye_storm_no_damage_prev', True)  # assume clean until damage taken

        # Mystic Eye (#94 power): use telepathy on 10 distinct floors
        if self._pl.has_effect('telepathy'):
            self._set_add('mystic_eye_floors', dungeon_level)
            if self._set_len('mystic_eye_floors') >= 10 and not self.is_unlocked('mystic_eye'):
                self._award_power('mystic_eye', "Mystic Eye", lambda pl: None)

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
            # Only count each dungeon level once -- not every FOV refresh
            floor = self.game.dungeon_level
            explored_set = self._p('theseus_explored_floors', None)
            if not isinstance(explored_set, set):
                explored_set = set()
            if floor not in explored_set:
                explored_set.add(floor)
                self._sp('theseus_explored_floors', explored_set)
                self._sp('fully_explored_floors', len(explored_set))
                if len(explored_set) >= 5 and not self.is_unlocked('theseus'):
                    self._award('theseus', "Theseus in the Labyrinth",
                                lambda pl: pl.apply_stat_bonus('PER', 1))
                # Ancestral Memory (#93 power): fully explore 10 floors
                if len(explored_set) >= 10 and not self.is_unlocked('ancestral_q'):
                    self._award_power('ancestral_q', "Ancestral Memory", lambda pl: None)
                # Ibn Battuta (#57): fully explore 30 distinct floors
                if len(explored_set) >= 30 and not self.is_unlocked('ibn_battuta'):
                    self._award('ibn_battuta', "Ibn Battuta's Road",
                                self._timer_bonus('geography', 4))

    def on_quiz_answer(self, subject: str, correct: bool, chain: int,
                       while_blinded: bool, while_confused: bool,
                       while_hallucinating: bool, while_feared: bool,
                       wrong_this_session: int, score_this_session: int):
        """Called after every individual quiz answer."""
        # Time Dilation (#86 power): 25 consecutive correct answers
        if correct:
            self._inc('consecutive_correct')
            if self._p('consecutive_correct') >= 25 and not self.is_unlocked('time_dilation'):
                self._award_power('time_dilation', "Time Dilation", lambda pl: None)
        else:
            self._sp('consecutive_correct', 0)

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

            # Ramanujan (#56): 500 correct math answers in one run
            if subject == 'math':
                self._inc('math_correct_run')
                if self._p('math_correct_run') >= 500 and not self.is_unlocked('ramanujan'):
                    self._award('ramanujan', "The Infinite Sum",
                                self._timer_bonus('math', 5))

            # Solomon (#64): 100 correct philosophy answers
            if subject == 'philosophy':
                self._inc('philosophy_correct_total')
                if self._p('philosophy_correct_total') >= 100 and not self.is_unlocked('solomon_q'):
                    self._award('solomon_q', "Wisdom of Solomon",
                                lambda pl: pl.apply_stat_bonus('WIS', 2))

            # Sage's Counsel (#99 power): 50 correct history answers
            if subject == 'history':
                self._inc('history_correct_total')
                if self._p('history_correct_total') >= 50 and not self.is_unlocked('sage_counsel'):
                    self._award_power('sage_counsel', "Sage's Counsel", lambda pl: None)

            # Scholar's Focus (#82 power): 500 total correct answers
            self._inc('total_correct_answers')
            if self._p('total_correct_answers') >= 500 and not self.is_unlocked('focused_scholar'):
                self._award_power('focused_scholar', "Scholar's Focus", lambda pl: None)

            # Mind Fortress (#91 power): 30 correct while mentally debuffed
            _mental = {'confused', 'blinded', 'hallucinating', 'hallucinating_pot', 'stunned', 'feared'}
            if any(self._pl.has_effect(e) for e in _mental):
                self._inc('mental_debuff_correct')
                if self._p('mental_debuff_correct') >= 30 and not self.is_unlocked('mind_fortress'):
                    self._award_power('mind_fortress', "Mind Fortress", lambda pl: None)

            # Galileo (#66): 100 correct science
            if subject == 'science':
                self._inc('science_correct_total')
                if self._p('science_correct_total') >= 100 and not self.is_unlocked('galileo'):
                    self._award('galileo', "Galileo's Heresy", self._timer_bonus('science', 3))

            # Confucius (#61): 50 philosophy correct while blessed
            if subject == 'philosophy' and self._pl.has_effect('blessed'):
                self._inc('confucius_blessed_philosophy')
                if self._p('confucius_blessed_philosophy') >= 50 and not self.is_unlocked('confucius'):
                    self._award('confucius', "The Analects", self._timer_bonus('philosophy', 4))

            # Machiavelli (#72): 500 correct answers in one run
            self._inc('machiavelli_run_correct')
            if self._p('machiavelli_run_correct') >= 500 and not self.is_unlocked('machiavelli'):
                self._award('machiavelli', "The Prince", self._all_timer_bonus(1))

            # Ouroboros (#100 power): 1000 correct answers in one run
            if self._p('total_correct_answers') >= 1000 and not self.is_unlocked('ouroboros'):
                self._award_power('ouroboros', "The Infinite Circle", lambda pl: None)

            # Archimedes (#71): 50 correct science AND 50 correct economics
            if subject == 'economics':
                self._inc('economics_correct_total')
            sci_ok = self._p('science_correct_total', 0) >= 50
            eco_ok = self._p('economics_correct_total', 0) >= 50
            if sci_ok and eco_ok and not self.is_unlocked('archimedes'):
                self._award('archimedes', "Give Me a Lever",
                            lambda pl: pl.apply_stat_bonus('INT', 1))

            # Hypatia (#74): 50 correct math AND 50 correct science
            math_ok = self._p('math_correct_run', 0) >= 50
            sci50   = self._p('science_correct_total', 0) >= 50
            if math_ok and sci50 and not self.is_unlocked('hypatia'):
                self._award('hypatia', "Hypatia's Legacy",
                            lambda pl: pl.apply_stat_bonus('INT', 2))

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

        # Caesar (#67): 300 kills in one run
        self._inc('caesar_kills')
        if self._p('caesar_kills') >= 300 and not self.is_unlocked('caesar'):
            def _apply_caesar(pl):
                for _s in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'):
                    pl.apply_stat_bonus(_s, 1)
            self._award('caesar', "Veni Vidi Vici", _apply_caesar)

        # Boudicca (#63): 50 kills while missing >60% HP
        if hp_pct_before < 0.40:
            self._inc('boudicca_kills')
            if self._p('boudicca_kills') >= 50 and not self.is_unlocked('boudicca'):
                self._award('boudicca', "Boudicca's Fury",
                            lambda pl: pl.apply_stat_bonus('STR', 2))

        # Spartacus (#55): 20 kills while any debuff is active
        if any(self._pl.has_effect(e) for e in _DEBUFF_EFFECTS):
            self._inc('spartacus_kills')
            if self._p('spartacus_kills') >= 20 and not self.is_unlocked('spartacus'):
                def _apply_spartacus(pl):
                    pl.apply_stat_bonus('STR', 1)
                    pl.apply_stat_bonus('CON', 1)
                self._award('spartacus', "The Gladiator's Defiance", _apply_spartacus)

        # Leonidas (#60): kill enemies on 30 distinct dungeon floors
        self._set_add('leonidas_kill_floors', self.game.dungeon_level)
        if self._set_len('leonidas_kill_floors') >= 30 and not self.is_unlocked('leonidas'):
            self._award('leonidas', "The Last Stand",
                        lambda pl: pl.apply_stat_bonus('CON', 2))

        # Battle Trance (#78 power): 200 total kills
        self._inc('battle_trance_kills')
        if self._p('battle_trance_kills') >= 200 and not self.is_unlocked('battle_trance'):
            self._award_power('battle_trance', "Battle Trance", lambda pl: None)

        # Death Wish (#84 power): win 10 combats at <=10% HP
        if hp_pct_before <= 0.10:
            self._inc('death_wish_kills')
            if self._p('death_wish_kills') >= 10 and not self.is_unlocked('death_wish'):
                self._award_power('death_wish', "Death Wish", lambda pl: None)

        # Life Drain (#95 power): 25 kills at <=15% HP
        if hp_pct_before <= 0.15:
            self._inc('life_drain_kills')
            if self._p('life_drain_kills') >= 25 and not self.is_unlocked('life_drain'):
                self._award_power('life_drain', "Life Drain", lambda pl: None)

        # War Cry (#90 power): 15 kills while feared
        if is_feared:
            self._inc('war_cry_kills')
            if self._p('war_cry_kills') >= 15 and not self.is_unlocked('war_cry'):
                self._award_power('war_cry', "War Cry", lambda pl: None)

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

        # Phoenix Rising (#75 power): survive at <=5% HP 10 times
        if self._pl.hp > 0 and (self._pl.hp / max(1, self._pl.max_hp)) <= 0.05:
            if not self._p('phoenix_was_low', False):
                self._sp('phoenix_was_low', True)
                self._inc('phoenix_survivals')
                if self._p('phoenix_survivals') >= 10 and not self.is_unlocked('phoenix_rising'):
                    self._award_power('phoenix_rising', "Phoenix Rising", lambda pl: None)
        else:
            self._sp('phoenix_was_low', False)

        # Temporal Shield (#92 power): take 50 total hits
        self._inc('temporal_shield_hits')
        if self._p('temporal_shield_hits') >= 50 and not self.is_unlocked('temporal_shield'):
            self._award_power('temporal_shield', "Temporal Shield", lambda pl: None)

        # Iron Will (#77 power): take damage 10 times while paralyzed
        if self._pl.has_effect('paralyzed'):
            self._inc('iron_will_paralyzed_hits')
            if self._p('iron_will_paralyzed_hits') >= 10 and not self.is_unlocked('iron_will'):
                self._award_power('iron_will', "Iron Will", lambda pl: None)

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

        # Mithridates (#1): cross-ref -- monster both poisoned you AND you ate it
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

        # Hermes (#35): tracked via on_teleport() to avoid double-counting scroll + teleport hooks

        # Shakespeare (#68): read 50 scrolls successfully
        self._inc('shakespeare_scrolls')
        if self._p('shakespeare_scrolls') >= 50 and not self.is_unlocked('shakespeare'):
            self._award('shakespeare', "The Bard's Tongue", self._timer_bonus('grammar', 5))

    def on_wand_zapped(self, wand_id: str, was_identified: bool):
        """Called when a wand is zapped."""
        # Merlin (#9): 10 unique wand types zapped unidentified
        if not was_identified:
            self._set_add('merlin_wands', wand_id)
            if self._set_len('merlin_wands') >= 10 and not self.is_unlocked('merlin'):
                self._award('merlin', "Merlin's Apprenticeship",
                            self._timer_bonus('science', 4))

        # Tesla (#58): zap 50 wands total
        self._inc('tesla_zaps')
        if self._p('tesla_zaps') >= 50 and not self.is_unlocked('tesla'):
            self._award('tesla', "Tesla's Circuit", self._timer_bonus('science', 5))

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

        # Zoroaster (#62): pray successfully on 15 distinct dungeon floors
        self._set_add('zoroaster_pray_floors', self.game.dungeon_level)
        if self._set_len('zoroaster_pray_floors') >= 15 and not self.is_unlocked('zoroaster'):
            self._award('zoroaster', "The Prophet's Vigil", self._all_timer_bonus(1))

    def on_recall_lore(self):
        """Called when recall lore is used."""
        # Norns (#28): use recall lore 20 times in a run
        self._inc('recall_lore_uses')
        if self._p('recall_lore_uses') >= 20 and not self.is_unlocked('norns'):
            self._award('norns', "The Norns' Thread",
                        lambda pl: pl.quirk_progress.update({'norns_active': True}))

        # Nostradamus (#70): recall lore 10 times while mentally debuffed
        _mental = {'confused', 'blinded', 'hallucinating', 'hallucinating_pot', 'stunned', 'feared'}
        if any(self._pl.has_effect(e) for e in _mental):
            self._inc('nostradamus_lore')
            if self._p('nostradamus_lore') >= 10 and not self.is_unlocked('nostradamus'):
                self._award('nostradamus', "The Prophet's Eye",
                            lambda pl: pl.apply_stat_bonus('WIS', 3))

        # Second Sight (#79 power): recall lore 5 times while blinded
        if self._pl.has_effect('blinded'):
            self._inc('second_sight_blind_lore')
            if self._p('second_sight_blind_lore') >= 5 and not self.is_unlocked('second_sight'):
                self._award_power('second_sight', "Second Sight", lambda pl: None)

    def on_spell_cast(self, hp_pct: float):
        """Called when a spell is successfully cast."""
        # Morgan le Fay (#42): cast spell at <=20% HP 6 times
        if hp_pct <= 0.20:
            self._inc('morgan_spells')
            if self._p('morgan_spells') >= 6 and not self.is_unlocked('morgan'):
                self._award('morgan', "Morgan le Fay",
                            lambda pl: pl.apply_stat_bonus('INT', 2))

        # Arcane Surge (#83 power): cast 20 spells in a run
        self._inc('arcane_surge_casts')
        if self._p('arcane_surge_casts') >= 20 and not self.is_unlocked('arcane_surge'):
            self._award_power('arcane_surge', "Arcane Surge", lambda pl: None)

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

        # Darwin (#73): acquire 8 distinct debuff types (passive)
        if effect_id in _DEBUFF_EFFECTS:
            self._set_add('darwin_debuff_types', effect_id)
            if self._set_len('darwin_debuff_types') >= 8 and not self.is_unlocked('darwin'):
                self._award('darwin', "Survival of the Fittest",
                            lambda pl: pl.apply_stat_bonus('CON', 3))

        # Gorgon Ward (#54 power): petrifying applied 3 times
        if effect_id == 'petrifying':
            self._inc('gorgon_ward_petrify')
            if self._p('gorgon_ward_petrify') >= 3 and not self.is_unlocked('gorgon_ward'):
                self._award_power('gorgon_ward', "Gorgon Ward", lambda pl: None)

        # Zeus Bolt (#53 power): hasted 15 times in a run
        if effect_id == 'hasted':
            self._inc('zeus_bolt_hasted')
            if self._p('zeus_bolt_hasted') >= 15 and not self.is_unlocked('zeus_bolt'):
                self._award_power('zeus_bolt', "Zeus' Bolt", lambda pl: None)

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

        # Venom Lore (#89 power): poisoned AND diseased simultaneously for 5 turns
        if pl.has_effect('poisoned') and pl.has_effect('diseased'):
            self._inc('venom_lore_turns')
            if self._p('venom_lore_turns') >= 5 and not self.is_unlocked('venom_lore'):
                self._award_power('venom_lore', "Venom Lore", lambda pl2: None)

        # Reality Anchor (#96 power): confused AND hallucinating simultaneously for 5 turns
        if (pl.has_effect('confused') and
                (pl.has_effect('hallucinating') or pl.has_effect('hallucinating_pot'))):
            self._inc('reality_anchor_turns')
            if self._p('reality_anchor_turns') >= 5 and not self.is_unlocked('reality_anchor'):
                self._award_power('reality_anchor', "Reality Anchor", lambda pl2: None)

        # Runic Armor (#97 power): have fire_resist + cold_resist + shock_resist active simultaneously 10 turns
        if pl.has_effect('fire_resist') and pl.has_effect('cold_resist') and pl.has_effect('shock_resist'):
            self._inc('runic_armor_turns')
            if self._p('runic_armor_turns') >= 10 and not self.is_unlocked('runic_armor'):
                self._award_power('runic_armor', "Runic Armor", lambda pl2: None)

        # Astral Form (#98 power): spend 100 turns invisible
        if pl.has_effect('invisible'):
            self._inc('astral_form_invisible_turns')
            if self._p('astral_form_invisible_turns') >= 100 and not self.is_unlocked('astral_form'):
                self._award_power('astral_form', "Astral Form", lambda pl2: None)

        # Atlas Burden (#52 power): carry 90%+ weight for 100 turns
        if pl.get_current_weight() >= 0.90 * pl.get_carry_limit():
            self._inc('atlas_burden_turns')
            if self._p('atlas_burden_turns') >= 100 and not self.is_unlocked('atlas_burden'):
                self._award_power('atlas_burden', "Atlas' Burden", lambda pl2: None)

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

    def on_item_identified(self, item_id: str):
        """Called whenever an item is successfully identified."""
        self._inc('items_identified')
        # Mirror Mind (#87 power): identify 100 items
        if self._p('items_identified') >= 100 and not self.is_unlocked('mirror_mind'):
            self._award_power('mirror_mind', "Mirror Mind", lambda pl: None)
        # Philosopher's Stone (#51 power): identify 200 items
        if self._p('items_identified') >= 200 and not self.is_unlocked('philosophers_stone'):
            self._award_power('philosophers_stone', "Philosopher's Stone", lambda pl: None)

    def on_lockpick_success(self):
        """Called when lockpick quiz succeeds and a chest is opened."""
        # De Medici (#59): 20 successful lockpicks
        self._inc('de_medici_picks')
        if self._p('de_medici_picks') >= 20 and not self.is_unlocked('de_medici'):
            self._award('de_medici', "De Medici's Treasury", self._timer_bonus('economics', 4))

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
        # Wandering Star (#85 power): teleport 15 times
        if self._p('hermes_teleports') >= 15 and not self.is_unlocked('wandering_star'):
            self._award_power('wandering_star', "Wandering Star", lambda pl: None)


# ---------------------------------------------------------------------------
# Active power definitions  (power_id -> config dict)
# uses > 0  = uses-based (no cooldown)
# cooldown > 0 = cooldown-based (unlimited use if ready)
# ---------------------------------------------------------------------------
_ACTIVE_POWER_DEFS: dict[str, dict] = {
    'metabolic':          {'uses': 3,  'cooldown': 0,  'label': 'Metabolic Surge',       'desc': 'Restore 100 SP instantly.'},
    'time_dilation':      {'uses': 1,  'cooldown': 0,  'label': 'Time Dilation',          'desc': 'Freeze time for 10 turns.'},
    'ouroboros':          {'uses': 1,  'cooldown': 0,  'label': "The Infinite Circle",     'desc': 'Haste + Shield + Regen for 20 turns.'},
    'eye_storm':          {'uses': 3,  'cooldown': 0,  'label': 'Eye of the Storm',       'desc': 'Invisible + Blessed for 10 turns.'},
    'ancestral_q':        {'uses': 2,  'cooldown': 0,  'label': 'Ancestral Memory',       'desc': 'Clairvoyance for 20 turns.'},
    'sage_counsel':       {'uses': 3,  'cooldown': 0,  'label': "Sage's Counsel",         'desc': 'Blessed for 15 turns (+25% quiz timer).'},
    'focused_scholar':    {'uses': 2,  'cooldown': 0,  'label': "Scholar's Focus",        'desc': 'Brilliance for 10 turns (INT+1, WIS+1).'},
    'mind_fortress':      {'uses': 3,  'cooldown': 0,  'label': 'Mind Fortress',          'desc': 'Clears all mental debuffs instantly.'},
    'philosophers_stone': {'uses': 1,  'cooldown': 0,  'label': "Philosopher's Stone",    'desc': 'Blessed + Brilliance for 10 turns.'},
    'atlas_burden':       {'uses': 2,  'cooldown': 0,  'label': "Atlas' Burden",          'desc': 'Heroism for 20 turns.'},
    'zeus_bolt':          {'uses': 3,  'cooldown': 0,  'label': "Zeus' Bolt",             'desc': 'Shock Resist + Hasted for 15 turns.'},
    'gorgon_ward':        {'uses': 2,  'cooldown': 0,  'label': 'Gorgon Ward',            'desc': 'Sleep Resist + Displacement for 15 turns.'},
    'phoenix_rising':     {'uses': 1,  'cooldown': 0,  'label': 'Phoenix Rising',         'desc': 'Fully restore HP.'},
    'iron_will':          {'uses': 2,  'cooldown': 0,  'label': 'Iron Will',              'desc': 'Shielded + Reflecting for 10 turns.'},
    'battle_trance':      {'uses': 3,  'cooldown': 0,  'label': 'Battle Trance',          'desc': 'Heroism for 15 turns.'},
    'second_sight':       {'uses': 3,  'cooldown': 0,  'label': 'Second Sight',           'desc': 'Telepathy + Clairvoyance for 15 turns.'},
    'iron_ration':        {'uses': 5,  'cooldown': 0,  'label': 'Iron Ration',            'desc': 'Restore 100 SP.'},
    'shadow_step':        {'uses': 3,  'cooldown': 0,  'label': 'Shadow Step',            'desc': 'Invisible + Phasing for 5 turns.'},
    'arcane_surge':       {'uses': 2,  'cooldown': 0,  'label': 'Arcane Surge',           'desc': 'Brilliance for 10 turns + restore all MP.'},
    'death_wish':         {'uses': 3,  'cooldown': 0,  'label': 'Death Wish',             'desc': 'Heroism + Hasted for 10 turns.'},
    'wandering_star':     {'uses': 0,  'cooldown': 50, 'label': 'Wandering Star',         'desc': 'Teleport to a random location (50t cooldown).'},
    'mirror_mind':        {'uses': 2,  'cooldown': 0,  'label': 'Mirror Mind',            'desc': 'Reflecting + Magic Resist for 10 turns.'},
    'venom_lore':         {'uses': 3,  'cooldown': 0,  'label': 'Venom Lore',             'desc': 'Poison Resist for 20 turns; cures poison.'},
    'war_cry':            {'uses': 3,  'cooldown': 0,  'label': 'War Cry',                'desc': 'Hasted for 8 turns.'},
    'temporal_shield':    {'uses': 2,  'cooldown': 0,  'label': 'Temporal Shield',        'desc': 'Shielded for 25 turns.'},
    'mystic_eye':         {'uses': 3,  'cooldown': 0,  'label': 'Mystic Eye',             'desc': 'Telepathy + Clairvoyance + Warning for 15 turns.'},
    'life_drain':         {'uses': 3,  'cooldown': 0,  'label': 'Life Drain',             'desc': 'Restore 25% of max HP.'},
    'reality_anchor':     {'uses': 2,  'cooldown': 0,  'label': 'Reality Anchor',         'desc': 'Clear all debuffs instantly.'},
    'runic_armor':        {'uses': 2,  'cooldown': 0,  'label': 'Runic Armor',            'desc': 'Fire Shield + Cold Shield + Shock Resist 10t.'},
    'astral_form':        {'uses': 2,  'cooldown': 0,  'label': 'Astral Form',            'desc': 'Levitate + Invisible + Phase for 8 turns.'},
}


# What the player did to earn this trait
_QUIRK_TRIGGER = {
    'mithridates':   "You ate 5 monster types that had previously poisoned you.",
    'tiresias':      "You answered 25 questions correctly while blinded.",
    'odin':          "You waited 12,960 turns -- half a day of mortal time.",
    'scheherazade':  "You read 12 distinct scrolls before identifying them.",
    'paracelsus':    "Disease drained 5 total stat points from you.",
    'siegfried':     "You ate ingredients from monsters with 5 distinct attack effects.",
    'musashi':       "You killed 30 enemies with a chain of exactly 1.",
    'rasputin':      "You survived 5 separate times at 5% HP or below.",
    'merlin':        "You zapped 10 distinct unidentified wands.",
    'buddha':        "You waited 500 times while hostile monsters were nearby.",
    'hephaestus':    "You equipped the same armor piece 15 times.",
    'cassandra':     "You passed 10 threshold quizzes despite getting 2+ wrong.",
    'sisyphus':      "You failed the lockpick quiz on 10 distinct trapped chests.",
    'job':           "You triggered 5 distinct trap types.",
    'orpheus':       "You stood beside monsters for 10 turns without fighting, 5 times.",
    'tantalus':      "You ate 15 ruined quality-0 meals.",
    'asclepius':     "You harvested 15 distinct poisonous monster species.",
    'fisher_king':   "You prayed 6 times at 15% HP or below.",
    'anansi':        "You answered 20 questions correctly while confused.",
    'prometheus':    "You bled for 5+ turns across 10 separate episodes.",
    'penelope':      "You equipped or unequipped armor 100 times.",
    'dionysus':      "You drank 10 potions while hallucinating.",
    'apollo':        "You achieved a perfect max chain 10 times.",
    'athena':        "You encountered 50 distinct monster species.",
    'loki':          "You wore 5 cursed items for 10+ turns each.",
    'thor':          "You fought 30 combats with the same weapon.",
    'beowulf':       "You won 10 unarmed combats.",
    'norns':         "You used Recall Lore 20 times.",
    'jormungandr':   "You equipped and unequipped the same weapon 20 times.",
    'shiva':         "You spent 100 turns under hallucination.",
    'enkidu':        "You harvested 20 distinct monster species.",
    'perseus':       "You reflected 5 status effects back at monsters.",
    'theseus':       "You fully explored 5 dungeon floors.",
    'persephone':    "You cooked quality-5 meals from 5 distinct ingredients.",
    'hermes':        "You teleported 8 or more times.",
    'sibyl':         "You answered 500 questions correctly before level 20.",
    'valkyrie':      "You made 25 ranged kills.",
    'ahasverus':     "You moved 15,000 tiles -- a wanderer without equal.",
    'circe':         "You cooked meals from 5 distinct bonus-type categories.",
    'gawain':        "You won 6 combats starting at 40% HP or below.",
    'ariadne':       "You escaped 10 floors within 30 turns of arriving.",
    'morgan':        "You cast 6 spells at 20% HP or below.",
    'cuchulainn':    "You killed 5 enemies while feared.",
    'fenrir':        "You endured 150 turns under debuffs.",
    'kali':          "You killed 100 of the same monster type.",
    'medusa':        "You answered correctly while blinded in 5 separate blinded episodes.",
    'green_knight':  "You survived 5 single hits dealing 30%+ of your max HP.",
    'narcissus':     "You examined your inventory 30 times.",
    'cerberus':      "You used the stairs 300 times.",
    'ragnarok':      "You descended to level 100 with 10 HP or less.",
    # --- New passive quirks ---
    'spartacus':     "You killed 20 enemies while at least one debuff was active.",
    'ramanujan':     "You answered 500 math questions correctly in one run.",
    'ibn_battuta':   "You fully explored 30 distinct dungeon floors.",
    'tesla':         "You zapped 50 wands.",
    'de_medici':     "You successfully picked 20 locks.",
    'leonidas':      "You killed enemies on 30 distinct dungeon floors.",
    'confucius':     "You answered 50 philosophy questions correctly while Blessed.",
    'zoroaster':     "You prayed successfully on 15 distinct dungeon floors.",
    'boudicca':      "You killed 50 enemies while missing more than 60% of your HP.",
    'solomon_q':     "You answered 100 philosophy questions correctly.",
    'atalanta':      "You escaped 10 floors within 25 turns of arriving.",
    'galileo':       "You answered 100 science questions correctly.",
    'caesar':        "You killed 300 monsters in one run.",
    'shakespeare':   "You successfully read 50 scrolls.",
    'wanderlust_q':  "You moved 20,000 tiles -- the road is your home.",
    'nostradamus':   "You used Recall Lore 10 times while mentally debuffed.",
    'archimedes':    "You answered 50 science AND 50 economics questions correctly.",
    'machiavelli':   "You answered 500 questions correctly in one run.",
    'darwin':        "You survived 8 distinct types of debuffs in one run.",
    'hypatia':       "You answered 50 math AND 50 science questions correctly.",
    # --- New power quirks ---
    'philosophers_stone': "You identified 200 items.",
    'atlas_burden':  "You carried 90%+ of your weight limit for 100 turns.",
    'zeus_bolt':     "You were Hasted 15 times in a single run.",
    'gorgon_ward':   "You survived the petrifying effect 3 times.",
    'phoenix_rising': "You survived at 5% HP or below 10 separate times.",
    'eye_storm':     "You completed 5 floors without taking any damage.",
    'iron_will':     "You took damage 10 times while paralyzed.",
    'battle_trance': "You killed 200 monsters.",
    'second_sight':  "You used Recall Lore 5 times while blinded.",
    'iron_ration':   "You moved 15,000 tiles on foot.",
    'shadow_step':   "You moved 2,500 tiles while invisible.",
    'focused_scholar': "You answered 500 questions correctly.",
    'arcane_surge':  "You cast 20 spells in one run.",
    'death_wish':    "You won 10 combats while at 10% HP or below.",
    'wandering_star': "You teleported 15 times.",
    'time_dilation': "You answered 25 questions correctly in a row.",
    'mirror_mind':   "You identified 100 items.",
    'metabolic':     "You moved 5,000 tiles.",
    'venom_lore':    "You endured 5 turns with both poison and disease simultaneously.",
    'war_cry':       "You killed 15 enemies while feared.",
    'mind_fortress': "You answered 30 questions correctly while mentally debuffed.",
    'temporal_shield': "You took 50 hits in a single run.",
    'ancestral_q':   "You fully explored 10 dungeon floors.",
    'mystic_eye':    "You had Telepathy active upon entering 10 distinct floors.",
    'life_drain':    "You killed 25 enemies while at 15% HP or below.",
    'reality_anchor': "You endured 5 turns confused AND hallucinating simultaneously.",
    'runic_armor':   "You had fire, cold, AND shock resistance all active for 10 turns.",
    'astral_form':   "You spent 100 turns invisible.",
    'sage_counsel':  "You answered 50 history questions correctly.",
    'ouroboros':     "You answered 1,000 questions correctly in one run.",
}

# Flavor quote shown on unlock -- captures the spirit of the achievement
_QUIRK_FLAVOR = {
    'mithridates':   "What does not kill me makes me immune. -- Mithridates VI",
    'tiresias':      "Sight is not needed to know the truth. -- Tiresias",
    'odin':          "I know that I hung on a windy tree, nine long nights. -- Havamal",
    'scheherazade':  "A story told at the right moment can stop a sword. -- Scheherazade",
    'paracelsus':    "The dose makes the poison -- and the cure. -- Paracelsus",
    'siegfried':     "I bathed in dragon blood. Let them try to harm me now.",
    'musashi':       "The Way of the sword does not require two strikes. -- Miyamoto Musashi",
    'rasputin':      "I was difficult to kill. I remained curious about whether you could.",
    'merlin':        "Magic is only science the scholar has not yet categorised. -- Merlin",
    'buddha':        "Peace is not the absence of danger -- it is the mastery of reaction.",
    'hephaestus':    "The forge rewards obsession. Every hammer blow matters. -- Hephaestus",
    'cassandra':     "It was always true. You simply refused to hear it. -- Cassandra",
    'sisyphus':      "One must imagine Sisyphus happy -- and with a better lockpick.",
    'job':           "Though He slay me, yet will I trust in Him. -- Job 13:15",
    'orpheus':       "Music can charm even death -- but you must not look back. -- Orpheus",
    'tantalus':      "Even the worst meal nourishes the will to eat better next time.",
    'asclepius':     "The serpent that poisons can also heal, if you learn its nature.",
    'fisher_king':   "Ask the right question -- the wasteland cannot persist. -- The Grail Legend",
    'anansi':        "I am confused? I simply chose the most interesting path. -- Anansi",
    'prometheus':    "They chained me to the rock. I am still here. -- Prometheus",
    'penelope':      "What is woven by day can be unwoven -- and rewoven stronger. -- Penelope",
    'dionysus':      "I have seen things sober men will never see. I prefer it. -- Dionysus",
    'apollo':        "The arrow does not miss if the archer does not waver. -- Apollo",
    'athena':        "Wisdom begins with knowing your enemy -- all of them. -- Athena",
    'loki':          "Constraints are merely invitations to be creative. -- Loki",
    'thor':          "Mjolnir always returns. Loyalty in battle is its own reward. -- Thor",
    'beowulf':       "I will not use a sword -- it would be beneath us both. -- Beowulf",
    'norns':         "Past, present, future -- the thread runs through all three. -- The Norns",
    'jormungandr':   "The serpent holds its own tail -- neither end willing to let go.",
    'shiva':         "To destroy the illusion you must first live inside it completely.",
    'enkidu':        "I walked with beasts and men alike. Both taught me survival. -- Enkidu",
    'perseus':       "Look not at the Gorgon directly -- use the shield. -- Perseus",
    'theseus':       "The labyrinth is only dangerous to those who do not map it. -- Theseus",
    'persephone':    "To descend is not defeat -- some seeds only bloom in the dark.",
    'hermes':        "Distance is a habit of mind, not a fact of space. -- Hermes",
    'sibyl':         "I asked for immortality. I should have asked for wisdom to use it.",
    'valkyrie':      "The battlefield is wider than the blade's reach. Learn to see it.",
    'ahasverus':     "I walk because I must -- but I have learned every road in doing so.",
    'circe':         "I transform nothing arbitrarily. Each change reveals what was inside.",
    'gawain':        "The truest courage is not in starting strong, but in finishing. -- Gawain",
    'ariadne':       "I gave him the thread -- knowing he would use it to leave. -- Ariadne",
    'morgan':        "Power does not leave when the body is weak. If anything, it sharpens.",
    'cuchulainn':    "The warp-spasm seizes me -- I become the storm. -- Cu Chulainn",
    'fenrir':        "Even bound, I have broken things. Even chained, I grow. -- Fenrir",
    'kali':          "I do not hate what I destroy. I simply am what I am. -- Kali",
    'medusa':        "She turned those who stared to stone -- but not those who studied.",
    'green_knight':  "My head falls -- I only laugh. -- The Green Knight",
    'narcissus':     "Self-knowledge is not vanity. Narcissus drowned in ignorance, not love.",
    'cerberus':      "Three heads -- one for what lies behind, one ahead, one for the passage.",
    'ragnarok':      "The end of the world is not an obstacle. It is merely the next floor.",
    # --- New passive quirks ---
    'spartacus':     "They gave me chains. I learned to fight in them. -- Spartacus",
    'ramanujan':     "An equation for me has no meaning unless it represents a thought of God. -- Ramanujan",
    'ibn_battuta':   "I have surveyed every hall, every passage, every hidden alcove. -- Ibn Battuta",
    'tesla':         "The day science begins to study non-physical phenomena, it will make more progress. -- Tesla",
    'de_medici':     "Every lock is merely a price. Some pay in gold. I pay in knowledge.",
    'leonidas':      "Come back with your shield -- or on it. Fight on every field. -- Leonidas",
    'confucius':     "The superior man thinks always of virtue; the small man thinks of comfort. -- Confucius",
    'zoroaster':     "Through prayer on every threshold I have walked, truth crystallised. -- Zarathustra",
    'boudicca':      "They drew first blood. I returned the debt with interest. -- Boudicca",
    'solomon_q':     "Wisdom begins in wonder. It ends in certainty. -- Solomon",
    'atalanta':      "She asked for a race -- they gave her a myth.",
    'galileo':       "And yet it moves. -- Galileo Galilei",
    'caesar':        "I came, I saw, I conquered. -- Julius Caesar",
    'shakespeare':   "All the world's a stage -- and every scroll holds a new act. -- Shakespeare",
    'wanderlust_q':  "The road teaches what rooms cannot. Stay on it long enough.",
    'nostradamus':   "The future belongs to those who can read it through the fog of the present.",
    'archimedes':    "Give me a lever long enough and a fulcrum -- I will move the world. -- Archimedes",
    'machiavelli':   "The end justifies the means -- and the means is relentless preparation. -- Machiavelli",
    'darwin':        "It is not the strongest that survive, but those most adaptable to change. -- Darwin",
    'hypatia':       "Reserve your right to think -- even to think wrong is better than not thinking. -- Hypatia",
    # --- New power quirks ---
    'philosophers_stone': "Matter and spirit are one substance wearing different faces.",
    'atlas_burden':  "I carry the weight of the world not because I must -- but because no one else can. -- Atlas",
    'zeus_bolt':     "The bolt does not ask permission. It simply arrives. -- Zeus",
    'gorgon_ward':   "Stone gazes back. The ward is in the eye that refuses to flinch.",
    'phoenix_rising': "I have been ash before. I know the way back.",
    'eye_storm':     "Five floors untouched. The calm at the centre is not absence -- it is mastery.",
    'iron_will':     "They paralysed the body. The will simply waited. -- Epictetus",
    'battle_trance': "The warrior and the weapon become one. The trance is the point of union.",
    'second_sight':  "Blindness is not darkness -- it is seeing with a different sense. -- Tiresias",
    'iron_ration':   "The soldier who knows his own feet can march forever. -- Napoleon",
    'shadow_step':   "The shadow moves without the body noticing. Learn to be the shadow.",
    'focused_scholar': "Volume is not mastery. Mastery is knowing which question to ask next.",
    'arcane_surge':  "Magic does not tire the soul -- it feeds it.",
    'death_wish':    "The greatest victories taste best at the edge of defeat.",
    'wandering_star': "Even stars do not stay fixed -- they travel across the night unmoored.",
    'time_dilation': "Twenty-five correct in a row. Not luck. Architecture.",
    'mirror_mind':   "A mind that reflects does not absorb lies.",
    'metabolic':     "The body is a furnace -- learn to stoke it at will.",
    'venom_lore':    "To name the poison is to begin its cure. -- Mithridates",
    'war_cry':       "Fear amplifies courage -- if you let it scream through you instead of at you.",
    'mind_fortress': "The walls you build inside cannot be breached from outside. -- Marcus Aurelius",
    'temporal_shield': "Every blow teaches the body a new rhythm -- until surprise becomes impossible.",
    'ancestral_q':   "Memory is not the past. It is the past made present. -- Ancestral spirits",
    'mystic_eye':    "To see all monsters is not paranoia. It is completion.",
    'life_drain':    "At the edge of death, vitality becomes a reflex.",
    'reality_anchor': "When the world bends, remain the fixed point. -- Stoic maxim",
    'runic_armor':   "Fire, frost, lightning -- all weather to those dressed in elder runes.",
    'astral_form':   "The body is a guest. The self is the host. Invisibility is the host stepping outside.",
    'sage_counsel':  "History is not what happened. It is what we learned from what happened.",
    'ouroboros':     "The serpent swallows its own tail and is never diminished. -- Hermetic Corpus",
}

# Map quirk IDs to short effect descriptions shown on unlock
_QUIRK_EFFECTS = {
    'mithridates':   "Permanent poison & disease immunity.",
    'tiresias':      "PER +2",
    'odin':          "Permanent telepathy -- all monsters visible.",
    'scheherazade':  "Grammar quiz timer +5 seconds.",
    'paracelsus':    "Permanent drain & disease resistance.",
    'siegfried':     "Permanent magic resistance.",
    'musashi':       "Chain-1 damage uses 2nd multiplier instead of weakest.",
    'rasputin':      "CON +2",
    'merlin':        "Science quiz timer +4 seconds.",
    'buddha':        "Permanent displacement -- monsters may miss.",
    'hephaestus':    "Equip threshold -1 for that armor slot.",
    'cassandra':     "WIS +1",
    'sisyphus':      "Economics quiz timer +5 seconds.",
    'job':           "Permanent levitation -- immune to floor traps.",
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
    'ahasverus':     "Permanent searching -- auto-reveal adjacent tiles.",
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
    'cerberus':      "Permanent warning -- sense monsters through walls.",
    'ragnarok':      "CON +5",
    # --- New passive quirks ---
    'spartacus':     "STR +1, CON +1",
    'ramanujan':     "Math quiz timer +5 seconds.",
    'ibn_battuta':   "Geography quiz timer +4 seconds.",
    'tesla':         "Science quiz timer +5 seconds.",
    'de_medici':     "Economics quiz timer +4 seconds.",
    'leonidas':      "CON +2",
    'confucius':     "Philosophy quiz timer +4 seconds.",
    'zoroaster':     "All quiz timers +1 second.",
    'boudicca':      "STR +2",
    'solomon_q':     "WIS +2",
    'atalanta':      "DEX +2",
    'galileo':       "Science quiz timer +3 seconds.",
    'caesar':        "All stats +1",
    'shakespeare':   "Grammar quiz timer +5 seconds.",
    'wanderlust_q':  "SP drain from movement is halved.",
    'nostradamus':   "WIS +3",
    'archimedes':    "INT +1",
    'machiavelli':   "All quiz timers +1 second.",
    'darwin':        "CON +3",
    'hypatia':       "INT +2",
    # --- New power quirks ---
    'philosophers_stone': "[POWER x1] Blessed + Brilliance for 10 turns.",
    'atlas_burden':  "[POWER x2] Heroism for 20 turns.",
    'zeus_bolt':     "[POWER x3] Shock Resist + Hasted for 15 turns.",
    'gorgon_ward':   "[POWER x2] Sleep Resist + Displacement for 15 turns.",
    'phoenix_rising': "[POWER x1] Fully restore HP.",
    'eye_storm':     "[POWER x3] Invisible + Blessed for 10 turns.",
    'iron_will':     "[POWER x2] Shielded + Reflecting for 10 turns.",
    'battle_trance': "[POWER x3] Heroism for 15 turns.",
    'second_sight':  "[POWER x3] Telepathy + Clairvoyance for 15 turns.",
    'iron_ration':   "[POWER x5] Restore 100 SP.",
    'shadow_step':   "[POWER x3] Invisible + Phasing for 5 turns.",
    'focused_scholar': "[POWER x2] Brilliance for 10 turns.",
    'arcane_surge':  "[POWER x2] Brilliance for 10 turns + restore all MP.",
    'death_wish':    "[POWER x3] Heroism + Hasted for 10 turns.",
    'wandering_star': "[POWER CD:50] Teleport to a random location.",
    'time_dilation': "[POWER x1] Time Stop for 10 turns.",
    'mirror_mind':   "[POWER x2] Reflecting + Magic Resist for 10 turns.",
    'metabolic':     "[POWER x3] Restore 100 SP.",
    'venom_lore':    "[POWER x3] Poison Resist for 20 turns; cures poison.",
    'war_cry':       "[POWER x3] Hasted for 8 turns.",
    'mind_fortress': "[POWER x3] Clear all mental debuffs instantly.",
    'temporal_shield': "[POWER x2] Shielded for 25 turns.",
    'ancestral_q':   "[POWER x2] Clairvoyance for 20 turns.",
    'mystic_eye':    "[POWER x3] Telepathy + Clairvoyance + Warning for 15 turns.",
    'life_drain':    "[POWER x3] Restore 25% of max HP.",
    'reality_anchor': "[POWER x2] Clear all debuffs instantly.",
    'runic_armor':   "[POWER x2] Fire Shield + Cold Shield + Shock Resist for 10 turns.",
    'astral_form':   "[POWER x2] Levitate + Invisible + Phase for 8 turns.",
    'sage_counsel':  "[POWER x3] Blessed for 15 turns (+25% quiz timer).",
    'ouroboros':     "[POWER x1] Hasted + Shielded + Regenerating for 20 turns.",
}
