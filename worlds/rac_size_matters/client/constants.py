GAME_NAME = "Ratchet & Clank: Size Matters"
EXPECTED_GAME_ID = "SCUS-97615"
POLL_INTERVAL = 0.1

# Dynamic Pine launches PCSX2 straight into the game via `-batch <iso>`
# (skipping the BIOS/PS2 browser a manually-started PCSX2 would otherwise sit
# at), so a just-opened PINE socket doesn't mean the game itself has finished
# booting - the ISO is still loading assets into memory for a bit after PINE
# is reachable. Reading game memory in that window sees inconsistent/garbage
# values (e.g. planet id not written yet), so PINE_CONNECT_SETTLE_DELAY_S
# gives the game a moment to settle before the very first memory read.
PINE_CONNECT_SETTLE_DELAY_S = 3.0
