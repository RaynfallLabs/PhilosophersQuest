from dice import roll

# Fallback multipliers used when the player has no weapon equipped.
_DEFAULT_MULTIPLIERS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]


def player_attack(player, monster, quiz_engine, on_complete):
    """
    Start a math chain quiz for the player attacking a monster.

    on_complete(damage: int, killed: bool, chain: int) is called when the quiz ends.
    Chain 0 = miss (no correct answers before first wrong).
    Weapon's own chain_multipliers, max_chain_length, and quiz_tier are used if equipped.
    """
    weapon = player.weapon

    def _callback(result):
        chain = result.score
        if chain == 0 or monster.is_dead():
            on_complete(0, monster.is_dead(), chain)
            return

        base        = roll(weapon.damage if weapon else '1d4')
        enchant     = weapon.enchant_bonus if weapon else 0
        multipliers = weapon.chain_multipliers if weapon else _DEFAULT_MULTIPLIERS
        mult        = multipliers[min(chain - 1, len(multipliers) - 1)]
        damage      = max(1, int((base + enchant) * mult))
        actual      = monster.take_damage(damage)
        on_complete(actual, monster.is_dead(), chain)

    quiz_engine.start_quiz(
        mode='chain',
        subject='math',
        tier=weapon.quiz_tier if weapon else 1,
        callback=_callback,
        max_chain=weapon.max_chain_length if weapon else None,
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
    )
