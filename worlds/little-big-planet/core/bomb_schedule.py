"""Bomb Trap timing prototype; native prefab spawning is not enabled yet.

Offsets use the game's 30 Hz simulation clock, so pausing does not consume the
effect. The first drop also waits 3–10 seconds. No new bomb is due at or after
30 seconds; bombs already emitted keep their own prefab fuse.
"""

TIMED_EXPLOSIVE_PLAN = 55804
BOMB_TRAP_DURATION_TICKS = 900


def bomb_drop_ticks(rng):
    """Precompute bounded random delays for a future native command payload."""
    ticks = 0
    result = []
    while True:
        delay = rng.randint(3, 10)
        if not isinstance(delay, int) or not 3 <= delay <= 10:
            raise ValueError('Bomb interval must be an integer from 3 to 10 seconds')
        ticks += delay * 30
        if ticks >= BOMB_TRAP_DURATION_TICKS:
            return tuple(result)
        result.append(ticks)
