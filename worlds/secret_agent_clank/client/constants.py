GAME_NAME = "Secret Agent Clank"
EXPECTED_GAME_ID = "SCUS-97623"
POLL_INTERVAL = 0.1

# Dynamic Pine / a just-opened PINE socket doesn't mean the game has
# finished loading -- memory reads too soon can see garbage. This delay
# lets it settle before the first real read.
PINE_CONNECT_SETTLE_DELAY_S = 3.0
