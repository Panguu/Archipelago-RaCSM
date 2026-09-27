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

The newer generation options exist for rule/schema parity, but the legacy PSP runtime does not yet fully implement Challenge Mode vendor content (Titan purchases and the deferred mod-vendor work), Giant Clank integration, the nanotech experience multiplier, Shrink Ray skip checks, Ghost Link, or multiplayer skins. Seeds using those features are not supported for gameplay yet. In-game notifications now have an independent top-left drawing hook and owned text/countdown storage, while retaining client-log output. Visual confirmation alongside native prompts is pending. Other PSP addresses retain their existing verification notes in `core/address_maps/psp.py`.

The location completion records use the existing PSP mission/challenge/skyboard save-table layouts. That mapping is not evidence of live validation of every event bit or newly added location. The current client still uses its existing PSP completion trackers.

## Validation

Planet receipts now share generation's infobot mapping. Current split-infobot
seeds require separate Pokitaru and Ryllus receipts, matching PS2; neither planet
is automatically regranted by save restoration. Legacy combined receipts remain
supported, and the legacy temporary Ryllus exception is disabled for split seeds
and random-start slots. The frontend random-start patch is now implemented; live New Game validation is deferred.
Synthetic-memory tests cover both ship/unlock bytes, stale saves, session resets,
each individual infobot, and preservation of the game-managed Inside Clank entry.
The full PSP suite passes 284 tests as of 2026-09-26; a full live multiworld playthrough remains pending.
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
Retail signatures now cover eleven main-planet presentation profiles. Pokitaru and Kalidon icon/text presentation have been confirmed live; the remaining profiles have static and synthetic-memory validation only. Mod-vendor work remains deferred. The user confirmed the
latest first-selected preview icon and AP
item/recipient text work in the live Pokitaru vendor on 2026-09-22.

Run from the Archipelago root with its supported Python environment:

```
worlds/rac_size_matters_psp/build/runtime/Scripts/python.exe -B -m unittest discover -s worlds/rac_size_matters_psp/test -t .
```

The suite covers generation, item/location ID parity, PSP completion address ranges, pymem calls, address bounds, game-swap cleanup, patch transactions, overlap rejection, readiness gating, resource links, nanotech levels, and debugger response matching.

`tools/smoke_client.py` hosts the generated playtest seed on an ephemeral localhost port and connects the actual PSP client against synthetic RAM. It verifies starting inventory/bolts, reports a mission through the real Core polling path, and waits for the server to acknowledge the location and deliver its randomized reward. It does not touch PPSSPP or the user's live save. Development client state is isolated under `build/smoke-state`.

Live UCUS98633/Pokitaru validation on PPSSPP v1.20.4 includes attachment, JIT clearing, owned-buffer pymem write/readback, a native frame-counter hook, register/prologue verification, original-code restoration, and a 16 KiB kernel allocation/free round trip with identical free memory before/after. `tools/probe_allocator.py` is a development probe, not automatic gameplay setup. Native gameplay features and a full multiworld playthrough remain unvalidated.

## Independent notification validation (2026-09-26)

The top-left overlay uses its own allocated text and frame countdown. It does not
write the interaction prompt pointer, timer, dimensions, or panel drawing calls.
Synthetic MIPS execution checks placement, delay slots, countdown expiry,
callee-saved registers, stack restoration, and restoration of both font colours.
Lifecycle tests cover simultaneous native prompt data, queued notifications,
loading, departure from an overlay, hook restoration, and allocation release.
Vendor resolution accepts the exact registered notification jump while continuing
to reject unknown or modified jumps.

A 30-second live Pokitaru test executed the independent hook and restored the
original instructions afterward. Maximum free memory was 241664 bytes before
and after allocation/free. The user has not yet confirmed its visual position or
simultaneous display with a native interaction prompt. This is not full PS2 parity.

## Cross-planet vendor validation (2026-09-26)

Synthetic RAM tests now install and restore the list icon, separate selected
preview icon, and scouted item/recipient text on all eleven presentation profiles.
They compare the entire RAM image after returning to the ammo view. A missed
loading poll now discards the previous planet's presentation snapshot, cached
profile results, and failure state before processing the new planet.

Native travel from Pokitaru to Ryllus was confirmed with destination 2 through
the previously verified travel routine; all CPU register categories were restored.
Ryllus vendor visual confirmation is pending. These automated checks do not
replace live validation of the remaining planets.

The first Ryllus live test exposed an incorrect weapon-array base: the list icon
worked, but the selected preview did not. The retail reference at module offset
0x1FACC and live specification pointers establish the correct level-byte base as
0x093FD2FB, replacing 0x0940F60F. This shared address correction also applies to
Ryllus weapon inventory access. A second reversible presentation test completed
and restored successfully; user confirmation of preview/text remains pending.
The corresponding reference was audited in all eleven local retail captures;
the other ten mapped weapon-array bases matched (assuming the captured module
load base). This does not establish visual validation on those other planets.

On 2026-09-26 the user confirmed the repeated corrected Ryllus presentation test
works: selected AP preview icon and AP item/recipient text. The temporary test
restored the original presentation. Pokitaru, Ryllus, and Kalidon now have live
presentation confirmation; a full connected-seed purchase test on Ryllus remains
separate from this presentation-only diagnostic.

## Random starting planets (2026-09-26)

The PSP client now configures a reversible FRONTEND.PRX New Game patch from
`starting_planet_id` when random starts are enabled. Eligible IDs match PS2:
1, 2, 3, 4, 7, 8, 23. The default/off setting preserves retail behavior.
It changes the new-save destination and two New Game intro destinations, leaving
existing-save load calls unchanged. It does not teleport an existing save.

Retail FRONTEND.PRX SHA-256:
`dd60d18acf4130cb6eaaeaa54eaf53257ee0c71f3cf91797228902f3b02d271b`.
The initializer begins at module offset 0x19F4; its destination rewrite is at
0x1AAC. New Game travel argument sequences are at 0x198B4 and 0x19E34 and call
0xF38. The original paths request intro overlay 20. Initializer save offset
0x1C2C holds the destination. The rewrite preserves a1=1 for unrelated defaults
and restores a2=0x50000 before continuing. All edits require exact retail bytes,
UCUS98633, an idle transition gate and a uniquely identified frontend (planet 0).

Eight offline tests cover every eligible destination, instruction semantics,
option changes, restoration, departed overlays, loading/gameplay refusal,
savestate-reset recovery and mismatched-instruction rejection. No live frontend
or connected-seed test was performed: frontend detection, first spawn, intro
bypass and all seven destinations remain on the final validation checklist.
The user requested that connected AP tests be deferred until the end.

## Challenge Mode tier progression (2026-09-26)

Fixed tiers 0/1/2 and Progressive Challenge Mode receipts are now wired from
slot data and the complete received-item snapshot into the PSP runtime. The
receipt count is rebuilt rather than incremented on network retries, capped at
the configured tier, and cleared on a new connection. No writes occur until the
existing server handshake and loaded-game gates allow gameplay polling.

The PSP counter is a 32-bit word at resident save offset 0x1C38
(0x088C2738), rather than the PS2 accessor's byte. Evidence from retail captures:
FRONTEND.PRX initializer store at 0x1ADC; LEVEL_10.PRX completion increment reads
at 0x224A0 and stores at 0x224AC; LEVEL_01.PRX tests at 0x22A44 and 0x22AA0.
The save's current-planet field is offset 0x1C2C (0x088C272C).
The client writes only changed values and verifies readback. Unknown overlays,
loading, mismatched planet state, and open weapon/mod vendors defer writes.
The missing RYNO vendor entry is now offered on Pokitaru at applied tier 1+.

Nine new offline tests cover fixed/progressive tiers, receipt replay, ceilings,
reconnection, word-size writes with adjacent-field preservation, transition and
vendor deferral, reapplication after load, RYNO visibility and input validation.
No live counter writes or connected AP tests were performed, as requested.
This completes tier synchronization, not every Challenge Mode feature: Titan
purchase tracking/level behavior remains unfinished. Challenge Mode mod-vendor
routing was subsequently implemented as described below. Those gaps must not be described as full Challenge Mode parity.


## Challenge Mode mod vendors (2026-09-26)

All ten Challenge Mode mod locations now have runtime planet routes matching
PS2. Hints and native purchasable flags require applied tier 1 or 2; tier 0
clears those flags. Planet accessibility and Challax gadget requirements still
apply. Existing mod purchase detection handles these locations as well.

An offline repeated-tick test exposed a temporary display ownership leak:
WeaponInventory.check() reasserts observed ownership every tick, but the vendor
previously corrected only newly changed weapons. The vendor now corrects all
non-AP-owned weapon tracking each tick while preserving native display bytes
until close. Closing removes temporary weapon/mod display grants.

Four new tests cover all generated mod routes, tier changes, hints, native
purchase flags, planet/gadget gating, purchase deduplication, repeated-tick
ownership and close cleanup. Full PSP suite: 288 tests passed. Live/AP tests
remain deferred. Titan purchase tracking and Titan level behavior are still
unfinished; this change does not establish full Challenge Mode parity.


## Titan vendor and level runtime (2026-09-26)

The PSP runtime now shares its local generation weapon definitions: twelve
Titan-capable weapons have eight levels and the complete XP curves; RYNO stays
at four. Level observations clamp to the maximum zero-based index, and XP
multipliers operate above level four. Applied Challenge Mode tier reaches both
the vendor and weapon inventory. Vanilla/manual/automatic Titan level bounds
follow the PS2 runtime; automatic progression remains driven by item counts.
Checked Titan locations restore purchase bookkeeping without granting a weapon
or levels. Buying a Titan check removes the vanilla ceiling rather than raising
the player's real level.

A base weapon's slot becomes its Titan offer after the base check is purchased
at tier 1+. Mootator requires real level four and Dayni Moon access. The PSP
buy-new path uses a temporary level index 4 and cleared unlocked byte for Titan
offers, versus index 0 for base offers. Purchase detection reports the selected
base or Titan check once. Hints and scouted item/recipient text use that same
location. Display writes rebaseline observations, and real levels/XP are restored
for ammo view and on close. Periodic AP weapon-state persistence is blocked
while vendors are active so temporary display levels cannot enter storage.

Eleven new offline tests cover every Titan route, base-to-Titan purchase flow,
no fake level checks or item grants, replay, ammo toggles, XP restoration,
Mootator/RYNO exceptions, tier gating, progressive bounds, upper-level XP,
maximum-level clamping, scouted text and persistence blocking. Full suite:
299 tests passed. Package rebuilt; no commits or pushes.

Live/AP testing remains deferred. In particular, the native PSP level-index-4
buy-new path still needs in-game confirmation of Titan naming, prices, bolt
charges and native unlock transitions. Synthetic purchase tests simulate the
unlock transition; they do not prove the emulator's purchase routine. Reconnect,
savestate/planet transitions and all progressive modes are on the final live
checklist. This is an offline-tested implementation, not full live parity proof.

## Remaining PSP gameplay features (2026-09-27)

Multiplayer skins are excluded from PSP scope at the user's request. No new
multiplayer skin runtime or skin profile is included.

Giant Clank stages now track their armour rewards, mission checks and skill
points without binding Ratchet-only overlay addresses. AP armour unlocks are
restored on return. When enabled, the Metalis stage's verified native travel
routine redirects the destination to Metalis. The patch validates the retail
instruction sequence and relocated calls, coordinates CPU pause/JIT invalidation,
restores when disabled, and drops stale state during loading.

Nanotech XP applies the configured multiplier to positive earned deltas at
resident save offset 0x1C34 (0x088C2734), with transition baselines and overflow
clamping. The offset is backed by retail LEVEL_01 XP addition and health-level
threshold routines, rather than PS2 address translation.

Shrink Ray checks read the PSP resident puzzle flags at 0x088C13CE. Skip mode
changes only validated, idle GrindrailLock interlocks, without fabricating earned
completion flags. Restoration respects puzzles completed while skip was active.
Object signatures, reciprocal pointers, payload size, puzzle index and transition
state are checked before mutation; native layout evidence comes from LEVEL_03.

GhostLink implements opt-in AP position sharing, same-game peer subscriptions,
finite-coordinate validation, stale-peer expiry, and native decoy display with
validated scene object links. Disabling or disconnecting stops the local display;
loading abandons stale pointers. Position sharing was explicitly authorized by
the user. All guest RAM access continues through pymem; no live network exchange
or emulator mutation was performed during this implementation pass.

Validation: 312 offline tests pass, including thirteen new cases for XP,
puzzle checks and skip restoration, GhostLink protocol/display guards, Giant
Clank rewards and native return patch rejection/restoration/reload. Package rebuilt.
No commits or pushes were made.

Live validation remains deferred: Giant Clank entry/rewards/return, native
Nanotech level thresholds, Shrink Ray doors and puzzles, and GhostLink decoy
rendering/lifecycle must still be tested in PPSSPP. Synthetic tests verify the
client's behavior against captured layouts; they do not establish full gameplay
parity. Earlier pending AP/vendor/Titan/notification checks above also remain.
