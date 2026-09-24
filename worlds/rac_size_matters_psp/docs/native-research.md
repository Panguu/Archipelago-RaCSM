# PSP native patch research

Verified September 22, 2026 against UCUS98633 version 1.01 in PPSSPP v1.20.4, on Pokitaru. Addresses below are research evidence for this overlay, not a cross-planet hook profile.

| Component | Guest address | Evidence |
| --- | --- | --- |
| Pokitaru module base | `0x09138D00` | Matched relocated module instructions |
| Native transient-message renderer | `0x091DD638` | Original module offset `0xA4938`; 0x178-byte function |
| Text colour function | `0x091D1D2C` | Renderer call at `0x091DD6F0` |
| Centred text function | `0x091D31E0` | Renderer call at `0x091DD71C` |
| Message timer | `0x093F8434` | Renderer load |
| Message pointer | `0x093F8448` | Renderer load |
| Message width | `0x093F8450` | Renderer load |
| Player maximum health | `0x09473BA8` | HUD reads player+0x968; current health is +0x964 |

The message renderer's entry is a verified non-delay-slot boundary. Its original first instructions are `addiu sp,sp,-0x60; lui a0,0x0940`. A live allocator probe runs to that boundary before redirecting the CPU and restores all GPRs, PC, HI, and LO afterwards.

Resident `SysMemUserForUser` imports:

| Function | NID | Stub |
| --- | --- | --- |
| AllocPartitionMemory | `0x237DBD4F` | `0x0883BC08` |
| GetBlockHeadAddr | `0x9D9A5BA1` | `0x0883BC18` |
| MaxFreeMemSize | `0xA291F107` | `0x0883BC20` |
| FreePartitionMemory | `0xB6D61D02` | `0x0883BC28` |

The probe allocated 0x4000 bytes from partition 2 using high allocation, obtained guest address `0x09FA4C00`, freed the block, and confirmed maximum free memory remained 0x3B000. That allocation address is transient and must never be hardcoded as a code cave.

`PatchStorage` now manages a kernel allocation with a random ownership header, named aligned buffers, bounded writes, and readback checks. It checks both the kernel UID's current address and the ownership header before access or release. Failed initialization retains the UID if cleanup fails. Hook references prevent free until restoration succeeds. A stale header or remapped UID causes refusal, not automatic adoption of the new memory. Save-state recovery and per-overlay runtime orchestration are still pending.

The live probe also executed `CounterHook` once. It redirected the renderer entry to code in owned memory, preserved t0/t1, incremented a separate counter, replayed the two displaced prologue instructions, and returned to `0x091DD640`. All GPRs, PC, HI, and LO matched the expected post-prologue state. Original code was restored before freeing storage; maximum free memory again remained 0x3B000. The probe writes and reads payloads through pymem. This is a diagnostic execution hook, not an in-game notification implementation.

Restoration refuses to proceed if the stopped CPU is inside the payload or the overlay instructions no longer match. The probe explicitly stops at the return boundary before restoring. No diagnostic hook is installed by the gameplay client.

`cpu.runUntil` successfully executes the nonblocking HLE import and returns to the boundary. `cpu.stepInto` did not advance this live probe. All RAM captures use pymem. Debugger requests only control execution or obtain metadata/registers.

PPSSPP's breakpoint manager defers cache updates to its frame loop. Adding/removing a temporary disabled memory breakpoint while stopped cleared JIT emuhack words back to retail instructions. `CodePlan` waits for that update and then validates exact expected bytes; a delayed update fails preflight without patch writes.

Reference implementation: [PPSSPP stepping subscriber](https://github.com/hrydgard/ppsspp/blob/v1.20.4/Core/Debugger/WebSocket/SteppingSubscriber.cpp), [kernel allocator](https://github.com/hrydgard/ppsspp/blob/v1.20.4/Core/HLE/sceKernelMemory.cpp). Local raw captures stay in the excluded `.research/` directory.

## One-time Kalidon travel test (2026-09-22)

`tools/force_kalidon.py` successfully requested travel from loaded Pokitaru to
Kalidon through the native routine at `0x0914D8F4`, with arguments `(3, 0)`.
The routine queued state 7 and destination 3 at `0x094A0FCC/0x094A0FD0`.
Execution started at the verified `0x091DD638` frame boundary and returned there;
GPR, FPU, and VFPU registers were restored before resuming. The game then loaded
Kalidon, and the running client reported Kalidon ready with its connection intact.
This is a Pokitaru-specific diagnostic, not a general warp command. RAM reads
and signature checks use pymem; debugger commands only control the CPU.
