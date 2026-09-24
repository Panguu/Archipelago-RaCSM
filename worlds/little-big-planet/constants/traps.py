class TrapItems:
    RANDOM_COSTUME_TRAP = 'Random Costume Trap'


RANDOM_COSTUME_TRAP_ID = 1249801000

# Stable IDs; helpful effects are useful items rather than AP traps.
GAMEPLAY_EFFECTS = {
    'restart_level_trap': (1249801001, 'Restart Level Trap', 'trap', 2),
    'disable_checkpoint_trap': (1249801002, 'Disable Checkpoint Trap', 'trap', 3),
    'checkpoint_refill': (1249801003, 'Checkpoint Refill', 'help', 4),
    'temporary_jetpack': (1249801004, 'Temporary Jetpack', 'help', 5),
    'temporary_paintball_gun': (1249801005, 'Temporary Paintball Gun', 'help', 6),
}
ONE_SHOT_KINDS = frozenset(GAMEPLAY_EFFECTS) | {'random_costume_trap'}

# 1249801006 / opcode 7 belonged to the removed Burn Trap; do not reuse.
RETIRED_EFFECT_IDS = frozenset({1249801006})
