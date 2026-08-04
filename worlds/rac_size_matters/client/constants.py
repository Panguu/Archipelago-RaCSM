GAME_NAME = "Ratchet & Clank: Size Matters"
EXPECTED_GAME_ID = "SCUS-97615"
POLL_INTERVAL = 0.1

# Dynamic Pine boots PCSX2 straight into the ISO, so a just-opened PINE
# socket doesn't mean the game has finished loading — memory reads too soon
# can see garbage (e.g. planet id not written yet). This delay lets it settle
# before the first read.
PINE_CONNECT_SETTLE_DELAY_S = 3.0
