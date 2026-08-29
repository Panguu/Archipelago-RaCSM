GAME_NAME = "Ratchet & Clank: Size Matters"
EXPECTED_GAME_ID = "SCUS-97615"
POLL_INTERVAL = 0.1

# A just-opened PINE socket doesn't mean the game has finished loading — reads too soon can
# see garbage (e.g. planet id not written yet), so this delay lets it settle first.
PINE_CONNECT_SETTLE_DELAY_S = 3.0
