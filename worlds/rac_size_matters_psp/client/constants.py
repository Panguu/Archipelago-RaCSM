GAME_NAME = "Ratchet & Clank: Size Matters PSP"
# PSP disc id (game.status's "id", e.g. UCUS98633 for the US release) — not
# the PS2 SCUS id this was copied from. Confirmed live against a running
# PPSSPP instance; update if you're targeting a different region's disc.
EXPECTED_GAME_ID = "UCUS98633"

# This variant doesn't route per-tick reads/writes through PPSSPP's debugger
# WebSocket at all — see procmem/transport.py. The WebSocket is only opened
# once, briefly, at connect() to fetch Memory::base and confirm the game id;
# every actual memory access afterward is a raw ReadProcessMemory/
# WriteProcessMemory call straight into PPSSPP's own address space (see
# procmem/winmem.py). That's an ordinary host-OS memory copy with nothing to
# do with PPSSPP's emulation loop — there's no Core_Break()/
# Core_WaitInactive() pause-resume per call the way the debugger-WebSocket
# variants have (Core/Debugger/WebSocket/MemorySubscriber.cpp's
# LockMemoryAndCPU()) — so POLL_INTERVAL can be as tight as the PS2/PINE
# original without stuttering the emulator.
POLL_INTERVAL = 0.1

# The list of Windows executable names tried when locating the running
# PPSSPP process lives in procmem/winmem.py (PPSSPP_PROCESS_NAMES) — it's
# ctypes/Win32 plumbing specific to that module, not general client config,
# so it stays there rather than being duplicated here.
