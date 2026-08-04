GAME_NAME = "Ratchet & Clank: Size Matters PSP"
# PSP disc id (game.status's "id"), not the PS2 SCUS id this was copied from.
# Update if targeting a different region's disc.
EXPECTED_GAME_ID = "UCUS98633"

# PPSSPP's debugger WebSocket is only opened once, at connect(), to fetch
# Memory::base and confirm the game id; every actual read/write afterward is a
# raw ReadProcessMemory/WriteProcessMemory call (see procmem/winmem.py), so
# POLL_INTERVAL can be as tight as the PS2/PINE original without stuttering
# the emulator.
POLL_INTERVAL = 0.1

# Windows executable names tried when locating the PPSSPP process live in
# procmem/winmem.py (PPSSPP_PROCESS_NAMES), not here.
