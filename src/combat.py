from dice import roll

# Damage multipliers indexed by chain length - 1.
# Chain 1 = 0.5×, Chain 2 = 1.0× (full base), Chain 3 = 1.5×, etc.
CHAIN_MULTIPLIERS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]


def player_attack(player, monster, quiz_engine, on_complete):
    """
    Start a math chain quiz for the player attacking a monster.

    on_complete(damage: int, killed: bool, chain: int) is called when the quiz ends.
    Chain 0 = miss (no correct answers before first wrong).
    """
    def _callback(result):
        chain = result.score

        if chain == 0 or monster.is_dead():
            on_complete(0, monster.is_dead(), chain)
            return

        weapon_damage = getattr(player.weapon, 'damage', None) if player.weapon else None
        base = roll(weapon_damage if weapon_damage else '1d4')
        mult = CHAIN_MULTIPLIERS[min(chain - 1, len(CHAIN_MULTIPLIERS) - 1)]
        damage = max(1, int(base * mult))
        actual = monster.take_damage(damage)
        on_complete(actual, monster.is_dead(), chain)

    quiz_engine.start_quiz(
        mode='chain',
        subject='math',
        tier=1,
        callback=_callback,
        wisdom=player.WIS,
    )
