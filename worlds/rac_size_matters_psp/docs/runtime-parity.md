# PSP runtime parity status

## Implemented

- Independent PSP world, launcher component, client, and game identity (`Ratchet & Clank: Size Matters PSP`).
- PS2 generation definitions copied into PSP-local `data/`, `locations/`, `rules/`, and options. Item and location IDs match PS2; no dependency on the PS2 apworld is needed at runtime.
- Existing PSP inventory, location polling, vendors, traps, and DeathLink retained.
- DeathLink now uses PSP float32 health and byte-sized movement writes, waits for loaded gameplay and vendor closure, and suppresses echoes through the resulting death animation. Unsupported overlays never fall back to Pokitaru addresses.
- Supported cheat traps use the shared PS2 duration defaults. Their per-connection deadlines are serviced by the locked gameplay poll rather than asynchronous memory-writing timers; loading defers writes, reconnect reapplies remaining effects, and clean disconnect clears them. These lifecycle changes have automated coverage but await a live PSP test.
- Ammo Link and Bolt Link use the PS2 storage keys and absolute-value sharing protocol, with readiness gates, input validation, and suppression of echoed updates.
- Nanotech level checks read maximum health, respect the configured interval/maximum, and reject invalid readings. The field offset was identified in the Pokitaru HUD; other mapped planets use the same player layout.
- Unified progressive armour receipt decoding added.
- Gameplay synchronization waits for the full initial item history and fresh replies for all five client storage keys. Either packet order is supported; stale cached values and unrelated storage replies cannot trigger inventory replacement or replay old bolt/trap rewards. Disconnect resets the handshake.
- Saved quick-select, equipped armour, and weapon XP restore under the PSP lock after gameplay is ready and the vendor is closed. Persistence waits for restoration; manual resync preserves earned weapon XP. Raw transition checks also gate receipt writes between gameplay polls.
- Local PPSSPP discovery by process ID; multiple instances are rejected instead of mixing a debugger base with another process.
- pymem reads/writes, guest RAM bounds checking, single-call 64-bit accesses, and cleanup on failed attachment.
- Debugger connection for game ID, RAM-base metadata, and CPU/cache control. No debugger memory reads/writes or PINE connection.
- Checked data patch plans: preflight, readback verification, rollback, restoration, overlap rejection, and gameplay lifecycle integration.
- Executable patch plans stop the CPU, request JIT invalidation, and preflight retail instruction bytes before writing through pymem. They remain unregistered until individual hooks and their storage lifetime are verified.
- Owned patch storage supports aligned buffers, readback verification, stale-allocation detection, and reference-gated release. A reversible diagnostic frame hook has executed successfully on Pokitaru; it is excluded from automatic gameplay installation.
- Client shutdown cancels its watcher and releases emulator resources.
- Starting rewards wait for server checkpoints and a loaded planet. Filler items use an ordered retryable cursor and remain pending on failed writes or during loading.
- The previously omitted Rescue the girl, Search the factory, and Explore the miniature city mission checks are tracked instead of treated as preset bits.
- Mission/cutscene polling now observes the location definitions' planet gates, matching PS2. Flags from other planets remain pending instead of reporting immediately from an old save. Both Outpost Omega overlays use its shared mission word; shared words are read once per poll. Goal reporting also waits for loaded Quodrona gameplay.
- A first-playtest YAML and reproducible apworld builder are included. The standard client does not require Universal Tracker; its integration is opt-in.

## Not yet at PS2 gameplay parity

The PSP native patch registry is empty. The PS2 instruction addresses and retail captures are not valid PSP hooks. The new data-patch infrastructure does not install the PS2 vendor, ship-menu, loader, pickup, toast, connection-warning, or multiplayer-skin patches.

Before shipping those features, capture the remaining PSP retail instructions and overlay identities and implement the hook plans. External process writes do not automatically invalidate PPSSPP JIT translations. `CodePlan` clears translations using a temporary disabled memory breakpoint while stopped; preflight rejects any remaining JIT markers. Do not register executable edits as data patches.

The newer generation options exist for rule/schema parity, but the legacy PSP runtime does not yet implement random starting planets, Challenge Mode progression, Giant Clank integration, the nanotech experience multiplier, Shrink Ray skip checks, Ghost Link, or multiplayer skins. Seeds using those features are not supported for gameplay yet. In-game notifications currently go to the client log. Other PSP addresses retain their existing verification notes in `core/address_maps/psp.py`.

The location completion records use the existing PSP mission/challenge/skyboard save-table layouts. That mapping is not evidence of live validation of every event bit or newly added location. The current client still uses its existing PSP completion trackers.

## Validation

Planet receipts now share generation's infobot mapping. Current split-infobot
seeds require separate Pokitaru and Ryllus receipts, matching PS2; neither planet
is automatically regranted by save restoration. Legacy combined receipts remain
supported, and the legacy temporary Ryllus exception is disabled for split seeds
and random-start slots. This does not implement the native random-start hook.
Synthetic-memory tests cover both ship/unlock bytes, stale saves, session resets,
each individual infobot, and preservation of the game-managed Inside Clank entry.
The full PSP suite passes 243 tests; live validation of these changes is pending.
Handshake tests cover partial/out-of-order replies, stale storage, disconnects,
and transition gating. An actual RACContext with synthetic PSP RAM verifies
inventory, saved weapon XP, quick-select restoration, and no repeated bolt grant.
Mission tests exercise every tracked flag's planet gate, both Outpost Omega
variants, AP-checked suppression, and the real Core goal callback across loading
and planet transitions. These use synthetic RAM rather than a live playthrough.

Pokitaru's weapon vendor was tested live: a selected purchase reported its AP
location and delivered the server reward. The user also confirmed the converted
32x32, 16-colour AP emblem renders correctly in PPSSPP. Automatic texture handling
now follows the purchase/ammo view and restores original textures on vendor close
or clean disconnect. Inactive placeholder rows no longer block visible icons.
The user confirmed automatic list icons; a separate weapon-specification preview
texture has now also been included to address the initially selected item.
Scouted AP item names and recipients replace vendor title/description strings
using the existing bounded description storage and reversible table pointers.
It rejects mismatched rows/formats and discards departed overlay snapshots.
Only Pokitaru has a verified presentation address profile so far; other planets
and the mod vendor still use their original presentation. The user confirmed the
latest first-selected preview icon and AP
item/recipient text work in the live Pokitaru vendor on 2026-09-22.

Run from the Archipelago root with its supported Python environment:

```
worlds/rac_size_matters_psp/build/runtime/Scripts/python.exe -B -m unittest discover -s worlds/rac_size_matters_psp/test -t .
```

The suite covers generation, item/location ID parity, PSP completion address ranges, pymem calls, address bounds, game-swap cleanup, patch transactions, overlap rejection, readiness gating, resource links, nanotech levels, and debugger response matching.

`tools/smoke_client.py` hosts the generated playtest seed on an ephemeral localhost port and connects the actual PSP client against synthetic RAM. It verifies starting inventory/bolts, reports a mission through the real Core polling path, and waits for the server to acknowledge the location and deliver its randomized reward. It does not touch PPSSPP or the user's live save. Development client state is isolated under `build/smoke-state`.

Live UCUS98633/Pokitaru validation on PPSSPP v1.20.4 includes attachment, JIT clearing, owned-buffer pymem write/readback, a native frame-counter hook, register/prologue verification, original-code restoration, and a 16 KiB kernel allocation/free round trip with identical free memory before/after. `tools/probe_allocator.py` is a development probe, not automatic gameplay setup. Native gameplay features and a full multiworld playthrough remain unvalidated.
