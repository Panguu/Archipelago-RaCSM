# NPEA00241 01.27 findings

These addresses are specific to the inspected executable. Function addresses are **not data addresses**. Runtime objects move; resolve pointers each time. A diagnostic boot patch is now installed but awaits its first restarted-game validation. No direct remote game-function call mechanism has been implemented.

## 2026-09-16: client and hook follow-up

Exact executable hash from PINE command 13:
`PPU-53fe207e75d7dfa26f83416f0f587bebe7005a0b`.

### Validated incoming death action

The `RequestedSuicide` serialized property at `0x6b82ac` references PYellowHead
offset `0x74`. The game's setter at `0x1caa8` zeroes its timer at `+0x70` and
sets `+0x74` to one. Update at `0x6cc20` consumes the request, calls death at
`0x6cbf8`, then clears the request at `0x6cd48`. PYellowHead is Thing `+0x24`;
its backlink `+8` points to that Thing. The world player vector contains these
parts directly. Live solo test: request byte consumed, creature state `0 -> 5`,
world death counter `0 -> 1`. Tool requires timer zero before writing only the
request byte; no creature-state write is performed.

### Prize grant call chain and diagnostic

`TriggerCollectItem` at `0x3afa4c` validates its source's egg plan, then invokes
inventory vtable `+0x4c` at `0x3afc58` and `0x3afcd8` (additional linked plans).
Current inventory vtable descriptor `0x85cd98` resolves to `0xb43c4`, TOC
`0x871498`. That routine requires an actual loaded resource handle, builds plan
metadata, handles existing entries and inserts through `0x584f8c`. A GUID alone
is insufficient to call it. Native inventory currently contains only 53 entries,
so granting all plans cannot be implemented by toggling existing ownership bits.

Diagnostic hook at `0x3afb94` replaces `lwz r18,-0x6c54(r2)` with RPCS3 `calloc`
and restores that instruction at the end of its code. It records source Thing
`r21`, collector `r22`, plan GUID and a 128-byte source-object snapshot. Buffer
`0x03000000` is separately allocated at boot; no game heap cave is borrowed.
Ring size is 128; overflow is explicit. Source, encoded bytes and independent
Capstone disassembly are available under `patches/` and `output/prize_probe/`.
Exact authored UID mapping is deliberately not assumed yet.

Correction: `TriggerCollect` -> `0x2fa18` appears to classify resource types,
not to be a proven score pickup notification. Do not hook it as a score event.

RPCS3 PINE writes call ordinary `vm::write*`; no code invalidation operation is
exposed there. This LLVM configuration therefore uses a boot patch for code
instrumentation, with PINE for data. Sources:
[IPC implementation](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Emu/IPC_socket.cpp),
[patch allocation implementation](https://github.com/RPCS3/rpcs3/blob/master/Utilities/bin_patch.cpp).

## Data validated by reads

2026-09-16 follow-up: the implemented reader passed its executable guards and returned an empty reward list initially. After the user entered The First Steps it matched only `g26374`, returned 18 source-zero prizes / 24 rewards, and passed three consecutive live samples. Full snapshot: `output/live_level.json`. This validates available-prize counting and catalogue matching, not collection state.

PINE returned RPCS3 `0.0.42-19873`, title `LittleBigPlanet™`, ID `NPEA00241`, version `01.27` and running status. The folder name contains an older RPCS3 version and is not the runtime version.

First Steps base level: GUID 26374, SHA1 `8b374ea51dc67e40bc0ce2dcc7376cdbe0bee5a1`, serialized revision 562. Object example: UID 15460, plan GUID 32150, authored position approximately `(29628.64,1760.37,0)`.

## Live prize catalogue chain

`GetNumCollectablesInLevel`: script wrapper `0x70418c` -> `0x36c368` -> thunk `0x54bb10` -> `0x85f74`.

Context getter `0x85d48`: loads a pointer from TOC - `0x60d0`, then dereferences it. Adjusted TOC is `0x871498`, hence:

```text
global_address = BE32[0x86b3c8]
context = BE32[global_address]
reward_array = BE32[context + 0x7c]
reward_count = BE32[context + 0x80]
reward_capacity = BE32[context + 0x84]
record stride = 0x2c
plan GUID = BE32[record + 0x08]  (observed GUID descriptors)
source = BE32[record + 0x28]
```

Source 0 = prize bubble, 1 = completion award, 2 = collection award, 3 = ace award. Actual live sample: 24 records, 18 source-zero entries, 2 each of sources 1, 2 and 3. Plans matched the saved per-level catalogue and all 18 authored First Steps prizes.

Observed transient context `0x390375a0`, array `0x38fe7a10`; do not hard-code either. The reader follows the static root instead.

## Collected-prize lookup: unfinished trace

`GetNumItemsCollected`: wrapper `0x7040ec` -> `0x36c294` -> `0x85fcc`.
The latter iterates the same reward array, filters source zero, and calls an inventory virtual lookup at vtable offset `0x34`. Therefore array membership alone does not mean collection.

Inventory selector `0x1d892c` gets active user through `0x37fa58`, then searches a seven-entry table through `0x1d7728`. Table root is loaded from adjusted TOC - `0xd34` (`0x870764`). Entries are 16 bytes: active byte at +0, user identifier at +4, another identifier at +8, inventory pointer at +12.

Observed table address `0x918cb0`, first inventory object `0x38dbb090`, vtable `0x8548b0`; the virtual descriptor at +0x34 points to `0xa076c` with TOC `0x871498`.

`0xa076c` branches between lookup in the local inventory (`0xa05f4`) and delegation to another inventory object, obtained by `0x879a4` from object + `0x384`. `0xa05f4` binary-searches a pointer array at inventory + `0x8c` (count + `0x90`), comparing resource descriptor words at +`0x20`, GUID at +8 and hash at +`0xc`. The descriptor-type selector at `0x551364` still needs inspection before implementing matching correctly.

## Pickup entry points: candidates, not hooks

- `TriggerCollectItem` wrapper `0x715b30` calls `0x3afa4c`.
- `TriggerCollect` wrapper `0x715148` calls `0x3aeafc`.
- Named strings also include `OnCollectFluff`, `RemovePrizeBubbleFromSceneGraph`, `UpdatePrizeBubbles`, and separate prize/points bubble statistics.

These labels and call traces locate useful code; they do not establish a safe patch site or a pickup event ABI.

## Completion, deaths and unlocks (2026-09-16)

Current slot: `context + 0x128` type, `context + 0x12c` number. Developer slots use type 0; the pod was observed as `(5,0)`. `GetDeathCount` (`0x36abb8`) follows `context+0x78 -> +0x50 -> +0x14` to the world and reads a 32-bit count at world + `0x520`. `GetNumItemsCollectedUponLevelComplete` reads context + `0x88`.

Active user: `BE32[BE32[0x881308-0x7384]]`. Select the matching active user from the seven-entry inventory table. Per-level profile records: inventory + `0x14c` pointer, +`0x150` count, stride `0x58`. Record starts with `(slot type, slot number)`; +`0x20` discovered byte, +`0x21` unlocked byte, +`0x22` play count (u16), +`0x24` completion count (u16), +`0x26` ace count (u16).

`SetLevelCompleted` calls `0xb5510`; completion updates go through `0xb3074`, which increments +`0x24`. `GetAcedCount` calls `0x36c214` and reads +`0x26` from the active player's per-slot record. One deliberate death followed by completion yielded death=1, completion=1, ace=0 and collected-at-completion=15 (of 18).

Unlock setter `0xa2660` obtains a slot record via `0xa2194`, sets +`0x21` to 1, then ORs inventory + `0x50` with 1. Discovery setter `0xa286c` similarly sets record +`0x20`. Both setters accept DLC type 8 as well as developer type 0. The grant tool reproduces these byte writes only for an existing record in the pod, with backups and readback verification. Skate to Victory (26376) was observed `00 00` and changed to `01 01`; completion/ace bytes were unchanged. The user confirmed it launched; PINE then reported `(0,26376)`. All 95 catalogue levels had an existing live profile record, including DLC. Other levels have not been individually launch-tested. No executable patches were applied.

## 2026-09-16: native inventory delivery verified

`patches/inventory_delivery.S` hooks entry `0x6cc20` (PYellowHead suicide-button
update; original `f821ff71`). RPCS3 `calloc` executes a relocated block and
returns to `0x6cc24`. In this run the block is at `0x980000`, while PINE still
reads the original instruction at `0x6cc20`. Therefore the client verifies the
complete relocated block and mailbox identity instead of assuming the original
text must contain a branch. See the RPCS3 patch implementation linked below.

Mailbox `0x03030000` has magic `APIG`, version 1, heartbeat, request state,
sequence, plan GUID, expected inventory/user, verified result pointer, error,
retained resource pointer and load timeout counter. Client payload is published
before the request state. Native result is published after `sync`. PINE never
allocates inventory nodes or inserts pointers into the game's containers.

The hook uses the active level root to find the world. Sackboy's child Thing
has a null `+0x14` world pointer, so the initial direct-child guard correctly
refused its first test before any resource load. The corrected hook verifies
the world has one player and its PYellowHead is the current update receiver.

Native calls, main TOC `0x871498`:

- `0x1d892c`: active inventory reference; dereference result and compare with
  command profile plus expected vtable `0x8548b0`.
- `0x57353c`: load/retain RPlan by GUID (`r3=&handle, r4=GUID, r5=0, r6=2`).
  Poll resource `+0x1c` until state 3; require resource `+0x34` equals GUID.
- `0xb43c4`: native AddPlan (`r3=inventory, r4=&handle, r5=0, r6=0, r7=1,
  r8=0, r9=&zero_slot`). Its native dirty marking handles save persistence.
- `0xa05f4`: exact local lookup using type `0x26`, GUID and zero hash; entry
  `+0x9a` must be zero after grant. Python independently verifies the same entry.
- `0x561648`: release retained resource handle before publishing completion.

Final installed code: 760 bytes, SHA256
`47d0137c6d3c5cb23896634bc7edba8aacc1283b96e64009627fc0dfc67879b7`.
Live grants: g31824 Apple Heart, g31842 Sombrero Hat, g32013 Zombie Boy,
g31877 Red Pattern Fabric, g31818 Snake Stone. First four confirmed visible by
the user. The fifth passed a real private AP server -> ReceivedItems -> durable
journal -> PINE -> native grant -> verified applied pipeline. Duplicate replay
did not advance mailbox sequence. All five were present in littlefart65 after
the user returned to the pod. Evidence: `output/inventory_delivery/` contains
delivery audit, AP verification, save export, save verification and backups.

This verifies representative item categories, not every catalogue plan.
Native prize suppression and exact pickup mapping remain unfinished.

### Source links

### Expanded bubble catalogue and original UID getter

The expanded BubbleCatalog export recursively inspected 381 unique emitter plan
resources with zero emitter-plan decode errors. They contain 360 score templates
and 13 prize templates across all 148 decoded level resources. There are still
95 slot-backed AP levels, 9,373 authored score locations and 1,836 authored prize
locations. These counts exclude emitted copies; they cannot simply be added.
Full emitter limits/frequencies, nested plan references and bubble provenance
are retained in `data/bubble_catalogue.json`.

Script registration at `0x4085fc` uses TOC `0x881308 - 0x3e58` for the
`GetThingUID` string and `-0x3e54` for descriptor `0x8657e8`. Wrapper `0x72959c`
calls `0x40717c`, which returns `lwz r0,0xb8(r3)` for a non-null Thing.
The diagnostic hook's 128-byte object snapshot ends at `+0x7f`, before this UID.
Reading a *surviving* recorded First Steps prize Thing at `+0xb8` yielded
1229812 (Fancy Moustache) and 1229813 (Bonnet), matching the authored catalogue.
Other recorded addresses had already been freed/reused or represented clones.
Therefore post-event pointer reads must never be used for checks; a future
hook must capture UID during the event and establish cloned/emitted provenance.
This finding does not yet enable score or prize checks.

- RPCS3 PINE implementation: https://github.com/RPCS3/rpcs3/blob/master/3rdparty/pine/pine_server.h
- Toolkit at commit `e4e8f4631624753536dd06ee37e79fdfaf18df9d`: https://github.com/ennuo/toolkit
- Relevant Toolkit classes: `Thing.isPrizeBubble`, `Thing.isScoreBubble`, `PGameplayData`, `EggLink`, `PlayedLevelData`, `CollectableData`, `CollectedBubble`, `RLocalProfile`, and `Slot`.

Toolkit's score/prize classification contains mesh-based heuristics. Exported counts should be verified against gameplay, especially when emitters or conditional objects exist.
