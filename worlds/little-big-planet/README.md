# LittleBigPlanet tracking research

## Sticker Sanity, Key Sanity and GOTY access (v1.30)

All current v1.30 runtime changes are bundled in **Archipelago LittleBigPlanet v1.30**
in `patches/NPEA00241_130.yml`: one RPCS3 patch entry and one checkbox. The installer
replaces the previous separate entries and removes their obsolete enable settings.
Restart RPCS3 after installing. This bundle targets **NPEA00241 version 01.30**.

### LBP Union and personal online patches

Apply Union's online patch **first**. Keep that EBOOT: AP adds an RPCS3 runtime
patch and does not rewrite server settings or account data.

1. Install the updated APWorld and boot your Union-patched **NPEA00241 v1.30**.
2. In the LittleBigPlanet AP client, enter `/patch` (an AP server connection is not required).
3. Import the generated YAML using RPCS3's game patch manager and enable
   **Archipelago LittleBigPlanet v1.30** for your game.
4. Restart the game. Repeat `/patch` whenever changing online settings changes the executable.

Each export uses the player's actual executable hash. Unknown hashes must pass
read-only SHA-256 checks over 20 code pages covering AP hooks, reader/DeathLink
routines and native calls, plus the randomiser descriptor. The client recognizes
the same verified layout automatically. Exact AP static replacements are allowed
so verification still works after installation. Results are cached only on the
current PINE connection; a new connection or hash requires verification again.
Server/account data is not included in the generated patch.

This supports personalized online executables **whose checked AP code dependencies
still match v1.30**, not arbitrary regions, updates or mods. A changed dependency
is rejected with its address and requires a new AP port. The checks do not prove
all possible mods compatible, and online multiplayer gameplay with AP remains
untested. Existing solo restrictions still apply.

For source users, `python tools/export_patch.py --output "C:\patches"` exports the
same personal patch. Close the AP client before using this standalone tool.
Alternatively, with the game running, `python tools/install_patches_130.py "C:\path\to\RPCS3"`
verifies and installs the matching entry directly, backs up the save/configuration,
and preserves unrelated patch entries. Restart RPCS3 afterward.

Optional `sticker_sanity` adds 162 named-sticker switch checks and their sticker
requirements. `key_sanity` adds 27 physical key checks. Both default off and require
a new seed to enable. Tea Pot activation and Get a Grip's key have been live-tested;
all-level reachability validation is still outstanding. The native GOTY menu patch
now exposes the installed bonus community levels (player confirmed selectable).
See [interaction checks](INTERACTION_CHECKS.md) for scope, regeneration and details.

## Level-end rewards and old-save progress

The AP client now watches completion and ace counters for every catalogued level,
including while returning to the pod. It emits their individual reward checks
along with the completion/ace check. All-prize rewards require a new completion
and a verified live prize total matching that level's authored prize plans.
If the collection data arrives one poll late on the same run, the client retries.
Old save progress establishes a baseline and never automatically checks a new seed.

LBP's saved completion/ace badges persist across AP seeds. To clear the native
play/completion/ace counters for **this seed's enabled levels** on v1.30:

1. Connect the updated AP client to your seed, return to the pod, then pause
   emulation in RPCS3.
2. Enter `/reset_progress` to preview how many level records have saved progress.
3. Enter `/reset_progress apply "C:\path\to\active\USRDIR"`, supplying the active
   LBP save directory containing `littlefart`. The path can be omitted if the
   client was launched with `--save-dir`.
4. Resume RPCS3 and reopen the level menu.

The command backs up the save and original memory records before writing, verifies
native counter/dirty-flag instructions, then clears only the six play/completion/ace
counter bytes per selected level. It marks the profile dirty, so the change can
persist when LBP saves. It does not reset inventory, prize collection metadata,
high scores, other levels, other players' profiles, or AP checks. It is an explicit
command, never an automatic reset on connecting to a seed. The backup path is
printed after the operation; close RPCS3 before restoring its saved files.

Counter tracking and bounded reset behavior have automated coverage. The reset's
badge display and persistence still require a live gameplay test.

## Gameplay traps and help items (v1.30)

The gameplay patch adds these optional filler replacements:

Use **Trap Percentage** (`trap_percentage`, 0�100, default 10) for the combined
percentage of Nothing filler replaced by effects. **Good Traps** (`good_traps`)
and **Bad Traps** (`bad_traps`) are multi-select lists. Each selected effect is
equally likely. Empty lists disable that category; both empty disable all effects.

| Selection | Effects |
| --- | --- |
| Good Traps | Checkpoint Refill, Temporary Jetpack, Temporary Paintball Gun |
| Bad Traps | Random Costume Trap, Restart Level Trap, Disable Checkpoint Trap |

By default only Random Costume Trap is selected. Helpful effects retain AP's useful
classification. This replaces the six individual percentage options; regenerate
saved player options and generate a new seed to use the new settings.

```yaml
trap_percentage: 20
good_traps:
  - Checkpoint Refill
  - Temporary Jetpack
bad_traps:
  - Random Costume Trap
  - Restart Level Trap
```

Checkpoint Refill restores the current checkpoint; Disable Checkpoint Trap empties
it. Temporary equipment lasts 900 gameplay updates (30 seconds at 30 Hz).

Effects currently queue for **solo play outside the pod**. Equipment
wait until the player has no active ability or death/stun state. The hook runs
the effects on the game thread, owns equipment expiry even if the AP client
disconnects, and cancels expiry if the creature, world or native state changes.
Completed deliveries are recorded as consumables and do not replay on reconnect.
The current lease cannot distinguish another pickup of the same ability during
the timer; that case still needs live validation.

Update both the APWorld and RPCS3 patch and restart RPCS3. Live Get a Grip testing verified native restart, checkpoint disable/refill,
and 30-second equipment expiry on the Union build.
Burn Trap was removed after its visual behavior failed player testing.
The player confirmed that the jetpack worked, the gun fired, and restart returned
the level to the start. Multiplayer effect execution is not enabled. `tools/gameplay_effect.py` provides an explicit
single-effect test command through the verified mailbox with the AP client closed.

## AP inventory policy and Random Costume Trap (v1.30)

The client publishes an AP inventory allowlist through PINE. With no received
items the list is empty. Popit's native category builder rejects unreceived
plans, including entries already present in an old save. Receiving a plan adds
permission and uses the existing native delivery queue. DLC costume unlocks use
exact content-ID membership from `data/dlc_inventory.json`; they do not grant
missing pieces automatically. Already-owned pieces become visible when their
pack is unlocked. Saved inventory entries and category metadata are preserved.

This requires the **Archipelago LittleBigPlanet v1.30** bundle, which includes the
inventory policy and command hooks. Restart RPCS3 after installation. Policy lasts
until RPCS3 restarts, or an explicit diagnostic disables it. The client refuses
to publish ownership permissions against an unverified hook. v1.27 does not
support this policy. Vanilla insertion into the saved inventory is still active;
this policy controls availability rather than deleting those entries.

**Random Costume Trap Percentage** replaces that percentage of Nothing filler
(default 10%, range 0–100). `Random Costume Trap` calls Popit's native randomiser
during solo gameplay and waits when another Popit action is active. The native
candidate loop uses the same AP allowlist. Completed trap deliveries are kept
out of ownership replay after reconnect or save reconciliation.

The original Apple Heart category-mask diagnostic was confirmed in game. The
new native policy and trap integration still require the restart/live validation
currently in progress. Existing equipped outfits and cached selections require
separate validation; hiding an entry alone does not prove those paths are gated.

## DLC ownership options and access items

All base-game levels are enabled by default. There is no Included Levels option.
**Excluded Levels** lists readable names for all base-game and DLC levels.
**Goal Level** is a dropdown of level names, defaulting to **The Collector**;
choosing an excluded level or a level in a disabled pack gives a generation error.

**DLC Level Packs** selects owned level kits and GOTY content.
**DLC Item Packs** selects standalone sticker/material/object asset families.
Costume pieces from those DLC families are no longer delivered as loose AP items.
**DLC Costumes** selects 150 actual My Content entries: 118 individual costumes
and 32 collections/minipacks. It appears alongside the other selectors under
**DLC Packs**, with all entries selected by default. Each enabled entry adds one
`Unlock <pack name>` item and one `My Content: <pack name> Unlocked` location.
The client checks that location after it receives the item and verifies the PINE
menu unlock. The player must still collect the contents in **My Content**; this
item does not grant inventory plans. A collection opens its included characters.
Disabled entries add no items or checks and remain locked unless included in an
unlocked collection. Existing costumes already owned in a save are not removed.

Animal Costumes was live-tested on v1.30: locking blocked collection and
unlocking permitted it again. Other entries use the same native slot mechanism;
individual costume navigation has not yet been separately play-tested.
New seeds and a restarted AP client/options host are required. No new boot hook
is needed. Old seeds without `costume_packs` retain their previous behavior.
Constants: `constants/dlc_costumes.py` (`DLCCostumeItems`,
`DLCCostumeLocations`). Regenerate from `tools/PackCatalog.java`, then
`tools/generate_content_packs.py` and `tools/generate_content_constants.py`.

Both pack selectors default to all catalogued entries, including Marvel Level Kit
and Marvel Costumes. Remove packs you do not own before generating. The individual kit
checkboxes, legacy DLC Packs whitelist, and separate addon exclusion list have
been removed. Remove a pack from its selector to disable it.

Each enabled kit adds an `Unlock <kit>` progression item. Its levels require
both that kit item and their individual level items. A random DLC starting
level precollects both items. Disabled kits add no levels, locations, kit items,
or exclusive rewards. Shared reward plans remain included when another enabled
location awards them. New seeds are required for these rules and options.

DLC Item Packs currently enumerates 27 extracted asset families, using readable
names such as Sonic and Watchmen. These are not verified mappings of every
separately sold Store SKU. Standalone packs add inventory items to existing
locations without invented pickup checks. Generation reports an error if there
are more items than enabled checks. These options do not install DLC or detect
ownership.

Generated per-level location constants for DLC levels live under
`constants/levels/dlc/<kit>/`, one module per level, for example:

```python
from .constants.levels.dlc.monster_kit import GhostTrainLocations
```

Existing item and location IDs are unchanged. Regenerate with
`python tools/generate_locations.py` (calls `tools/generate_level_constants.py`).

PINE publishes a complete table for all catalogued level slots. Unreceived and
excluded levels get lock state zero even when an existing save marks them
completed. Kit ownership is applied before publication. The table is rebuilt
from AP slot data and received items after reconnect; it does not edit save
unlock flags. This requires the AP client and a verified runtime access patch.
Menu-level enforcement is undergoing a live test; opening a kit's preview is
separate from being allowed to launch its levels.

## NPEA00241 v1.30 port (2026-09-17)

The client selects memory layouts by both version and executable hash. v1.27
support remains available. v1.30 uses hash
`PPU-545c1abbf1c562d60fca7435401f020beab76b53` and the distributable boot patches
in `patches/NPEA00241_130.yml`. Do not copy v1.27 addresses into a v1.30 patch.

The v1.30 reader, pod boot, inventory/access hook bytes and writable access
buffer have been verified live. Get a Grip yielded ten exact score-bubble
locations and three exact prize locations (Tudor View, Tea Pot, Leaf Doodle).
Replaying these records through a private AP server confirmed all thirteen
checks and durable recording before acknowledgement. The optional Universal
Tracker superclass was disabled for that headless test because its initialization
failed; this does not verify the tracker UI. Three score callbacks without a
source UID remain preserved and unchecked.

Angry Skull (g31825) was absent before a native PINE grant and present afterward;
the user also confirmed it in Popit. The initial allocation-permission crash is
fixed. A requested DeathLink action was also verified live: Sackboy entered
the dead state, the world death counter increased from 1 to 2, and the request
flag cleared. Completing Get a Grip increased its completion counter from 0
to 1 and produced Level Complete, Pink Cat Nose and Happy Eyes completion
checks. Its ace counter stayed zero after the test deaths. Seed-controlled
level access and DLC menu selection still need v1.30 gameplay verification. Vanilla reward
suppression remains unfinished on both versions.

To install the supplied v1.30 patches with the supported game running:

```powershell
& ../../.venv/Scripts/python.exe tools/install_patches_130.py 'C:\path\to\RPCS3'
```

The installer verifies original instructions, backs up the active save and
patch configuration, and preserves the v1.27 patches. Restart RPCS3 and the
AP client after installation. These are RPCS3 boot-time memory patches;
the installer does not modify the game's executable or archives.

## Complete extracted bubble catalogue

See [BUBBLE_CATALOGUE.md](BUBBLE_CATALOGUE.md) for per-level coverage and
`data/bubble_catalogue.json` for every authored score/prize location, original
UID, stable AP ID, name, position, classification evidence and emitter data.
The expanded extractor recursively decoded 381 emitted plans, including 360
score and 13 prize bubble templates that were absent from the authored-only
scan. Template counts do not represent spawn counts or additional AP checks;
repeated/cloned bubble identities still need a finite check policy and live
validation. All 9,373 authored score and 1,836 authored prize definitions retain
their existing constants, numbering and AP IDs. No decoded slot root is missing
from the level export. The sole resource decode failure is scratch/testrnp.slt.

**Authored score and prize pickup checks are now wired through PINE to the AP client.**
The shared mapper covers all 11,660 authored bubble identities across 99 levels.
Live validation covers King Stamp and Score Bubbles 24–29 in Skate to Victory;
it does not constitute a playthrough of every level. Emitted/cloned objects whose
IDs do not match authored locations remain unmatched and are never guessed.

## Current client status (2026-09-16)

The source world now registers as **LittleBigPlanet** in Archipelago and generates
real seeds. All checks require only their respective level's unlock item. There
are no sticker, movement, multiplayer or other access rules. The starting level
is **random by default**, chosen deterministically from the included levels; its
unlock is precollected. `goal_level` defaults to The Collector and can be changed.

`Client.py` now connects to RPCS3 automatically via **PINE port 28011**, including
before joining an AP server. It displays the live level, deaths and completion
counter and retries dropped game connections. `/pine` shows its status. The GUI
Connect field and `/connect` are for the **Archipelago server**, not the PINE port.
Restart an already-open client to load these changes. A LittleBigPlanet Client
entry is also registered in the source checkout's launcher.

From this directory, using the checkout's existing Python environment:

```powershell
& ../../.venv/Scripts/python.exe Client.py --name Sackboy
# With an AP room:
& ../../.venv/Scripts/python.exe Client.py --name Sackboy --connect HOST:PORT
# Generate a seed from examples/LittleBigPlanet.yaml:
& ../../.venv/Scripts/python.exe tools/generate_seed.py --seed 1241
```

**This is still not a playable complete randomizer.** The client connects and
durably receives items and delivers inventory plans through PINE. Exact
prize/score checks now use physical pickup events; native reward suppression remains
unfinished. Inventory deliveries run independently. The runtime level-access
patch lets the client publish the seed's starting level and received unlocks
without rewriting saved level flags. Live menu/launch validation is pending.

Validation: a full 11,764-location seed filled and passed AP's beatability check.
A real local AP server confirmed login, starting-item receipt, a synthetic test
location acknowledgement and reward receipt, without game writes. The actual
client entry point connected live to Get a Grip. The SQLite journal isolates
seed/team/slot, retains checks until server acknowledgement, and marks deliveries
applied only after adapter confirmation. The network verification server is
temporary and has been closed.

### Intro skip, planet menus and AP level access

`Archipelago intro skip and level access v1` is an executable-hash-locked RPCS3
boot patch for NPEA00241 01.27. It redirects mandatory intro startup to the pod,
returns true from the intro-completed access query, and returns the first-group
progression value to the planet-menu query. It does not increment completion
counters, award tutorial checks, modify game files, or supply missing DLC content.

The GetLockState hook reads an AP-owned table at `0x03040000`. Once connected,
the client unlocks only the seed's starting level and received level unlocks;
excluded/unreceived catalogue levels return locked even if vanilla progress
unlocked them. Real played/completed badge states are preserved for received
levels. Unknown slots retain native behavior. Table updates use two banks and
publish only after readback, using one aligned PINE Write32. This also supports
profiles that do not yet have a saved PlayedLevelData record for a received level.

Without an AP table, native level locks remain in effect. No profile lock flags
are rewritten; after an RPCS3 restart the client rebuilds access from the AP seed
and received-item history. Connect the AP client before selecting a level.

Build and install from this directory:

```powershell
python tools/build_level_access.py
& ../../.venv/Scripts/python.exe tools/install_level_access.py "PATH_TO_RPCS3"
```

The builder checks original instructions when a local research dump is present. The
legacy `output/legacy_patches/level_access.yml` is hash-locked; players do
not need to generate a new executable dump. The installer preserves existing
patches and creates patch/config/save backups. Fully restart RPCS3 and the LBP
client after installation. Disable this named patch and restart RPCS3 to restore
normal intro/menu/level-access behavior. Current status: assembled instructions
and client table protocol tested; fresh-profile intro skip and DLC launch await
live validation.

### Physical pickup hooks

An executable-hash-locked pickup patch is installed in the user's RPCS3
`patches/NPEA00241_patch.yml`, enabled in `config/patch_config.yml`, with backups
under `output/prize_probe/backups/`. Its legacy patch-manager name remains
`Archipelago prize diagnostic v1`, but it now contains both pickup hooks and uses
the LBP2 event protocol. The prize hook captures Thing UID at +0xb8 before grant.
The score callback hook captures the current frame's cached source Thing UID
before resolving the recipient overwrites it. No score-total inference is used.
**The AP client submits exact mapped pickups; vanilla grants are not suppressed.**
The patch preserves the original instruction and used registers and reports
overflow instead of silently overwriting unread events.

The initial installation was rejected because YAML reserialization converted
hexadecimal address scalars to decimal. The installer now preserves the required
`0x` strings and validates them after writing. The corrected patch was installed
and subsequently loaded successfully after restarting. `/pine` now
distinguishes a connected game from a loaded diagnostic hook.

To inspect subsequent prize events:

```powershell
python tools/read_prize_probe.py --seconds 2
```

Build sources: `patches/prize_probe.S`, `patches/score_pickup.S`;
generator: `tools/build_prize_probe.py`.

`tools/pine_pickups.py` maps the event's captured level slot, kind and UID to its
stable AP location ID. Prize events must also match their plan GUID when the
catalogue supplies one; the single unnamed prize still requires its exact UID.
`Client.py` intersects checks with the connected seed's enabled locations and
commits checks plus raw evidence to the seed/team/slot SQLite journal before
acknowledging the game ring. Repeated pickups are idempotent, server-unconfirmed
checks are resent after reconnect, and ring overflow is reported explicitly.
The diagnostic reader does not consume events unless explicitly requested.

Restart the AP client after updating and connect it to your AP room before
playing. The ring holds 256 unacknowledged events; PINE connects automatically,
but game events cannot be acknowledged until a seed-specific journal is open.

Validation: the user's King Stamp pickup (1240003561) and six score pickups
(1240003466–1240003471) were captured live. Replaying each captured batch through
`tools/verify_pickup_connection.py` produced confirmed checks on a private real
AP server, with durable journalling before acknowledgement. This verification
does not alter the user's AP room or consume the live PINE events.

### Inventory item constants

`constants/item_names.py` provides `ItemName` constants for 4,208 inventory
plans and 95 level unlocks. Examples: `ItemName.HENRY_FACE`,
`ItemName.TUDOR_VIEW`, `ItemName.BUNNY_EARS`, and `ItemName.BASIC_RUBBER`.
`items.py` links every constant to its existing AP ID and game plan identity.
The AP world exposes category groups such as `sticker`, `costume`,
`costume_material` (skins), `material`, `decoration`, `object`, and `music`.

The installed catalogue includes 1,745 stickers, 660 costume pieces, 105 costume
materials, 194 building materials, 202 decorations, and 1,069 objects, plus
music, sounds, backgrounds, colours, tools and other assets. Of the inventory
plans, 2,102 are referenced by extracted prize/reward locations; seed generation
adds each distinct reward from enabled levels once. Other plans include starter
and internal assets and are registered without automatically entering the pool.
425 inventory names remain unresolved and retain explicit GUID placeholders.

Regenerate with `python tools/generate_item_constants.py`; rebuilding with
`tools/generate_items.py` also updates the constants. AP item definitions and
durable receipt tracking now use a verified native PINE delivery hook. Native
reward suppression remains unfinished.

### PINE inventory delivery

The installed `Archipelago inventory delivery v1` patch accepts one command at
a time in a dedicated mailbox. The game's update thread loads the requested
plan, calls its native inventory grant function, verifies the collected entry,
marks the profile through the native save path and releases its resource handle.
The client verifies ownership again before marking an AP delivery applied.
Replay checks existing ownership and avoids duplicate grants. Reconnecting to
the game or changing the active inventory requeues receipts for reconciliation.

Validated live on NPEA00241 01.27 in solo gameplay:

- Apple Heart (sticker), Sombrero Hat (costume), Zombie Boy (skin), and
  Red Pattern Fabric (material), all confirmed visible by the player.
- Snake Stone (decoration), sent by a private AP test server through the actual
  client, native grant and delivery journal, with no synthetic location checks.
- Duplicate receipt/reconciliation without another native grant.
- All five plans present in the saved profile after returning to the pod.

Restart an already-open **AP client** to load the delivery code. The corrected
RPCS3 hook is already running in this session. For a new installation:

```powershell
python tools/build_inventory_delivery.py
& ../../.venv/Scripts/python.exe tools/install_inventory_delivery.py "PATH_TO_RPCS3"
# Fully restart RPCS3 and enter solo gameplay after installing the boot patch.
python tools/grant_inventory.py
```

The installer backs up patches and the known active save. Before first delivery
to a profile, the client also backs up its save using the installation record,
or an explicit `Client.py --save-dir PATH_TO_ACTIVE_USRDIR` argument. Command
audits and live validation results are under `output/inventory_delivery/`.
Failed or unverified requests retain the AP item as pending. This hook supports
the exact executable hash in its builder; multiplayer and every individual
catalogue asset have not been play-tested. Level-unlock delivery remains separate.

### Level and location constants

`constants/` contains generated AP display-name classes for all 99 catalogued
levels and 11,764 authored location definitions:

- `level_names.py`: `LevelName.FIRST_STEPS`.
- `levels/`: one generated module per level, holding every kind of check for that
  level together (prize/score bubbles, completion, all-prizes, ace, rewards), split
  into `levels/base/` for base-game levels and `levels/dlc/<kit>/` for each DLC
  kit's levels. For example, `levels/base/first_steps.py` has:

  ```python
  class FirstStepsLocations:
      PRIZE_BUBBLE_1 = 'First Steps - Prize Bubble 1 - Henry Face'
      SCORE_BUBBLE_1 = 'First Steps - Score Bubble 1'
      COMPLETE = 'First Steps - Level Complete'
      ALL_PRIZES = 'First Steps - All Prize Bubbles'
      ACE = 'First Steps - Ace (No Deaths)'
      COMPLETE_REWARD_1 = 'First Steps - Completion Reward 1 - Bunny Ears'
  ```

  Each `base/` and `dlc/<kit>/` package has an `__init__.py` re-exporting its level
  classes for direct import; `constants/levels/__init__.py` also exports the full
  `LEVEL_LOCATIONS = {guid: (Class, LOCATION_KEYS)}` registry used by `locations.py`.

Each level module maps constant attributes to stable catalogue keys through
`LOCATION_KEYS`. `locations.py` builds the world's `LOCATION_NAME_TO_ID` from
these constants and checks that every catalogue location is covered. Existing
numeric AP IDs are unchanged. The six First Steps reward checks are separate
from its three completion-condition checks. Bubble numbering is stable authored
object numbering, not the order encountered while playing.

Run `python tools/generate_level_constants.py` after catalogue edits; the full
`tools/generate_locations.py` rebuild also regenerates constants automatically.
Names use the extracted game translations. There are still 37 unresolved name
entries (including custom unnamed plans and one missing plan reference), clearly
marked in the catalogue. Static definitions do not establish reachability;
exact pickup hooks now drive checks, while reward suppression remains pending.
Disable `Archipelago prize diagnostic v1` in RPCS3's patch manager and reboot to
remove the hook. Existing unrelated patches were preserved. The pickup hook does
not edit the game executable or save archives.

Target: **NPEA00241, game version 01.27**, RPCS3 PINE at `127.0.0.1:28011`.
The readers are read-only. `tools/unlock_levels.py --apply` deliberately writes selected level-unlock flags and marks the profile for saving, after backing up the save archives. No level-destination shuffle has been applied.

## Randomizer location tables and unlock items

`data/levels.json`, `data/location_registry.json`, and `level_names.py` are generated from the installed game. Current coverage: **99 slot-backed levels, 12,263 location definitions** (including creation tutorials, challenges and installed DLC). The exporter also lists 53 non-slot-backed resources separately; these include pods/palettes and are not silently treated as playable levels. One source slot resource remains undecoded.

```python
from level_names import LevelName
from locations import locations_for_level, LOCATION_NAME_TO_ID

for location in locations_for_level(LevelName.FIRST_STEPS, "score"):
    print(location["name"], location["id"])
for location in locations_for_level(LevelName.FIRST_STEPS, "prize"):
    print(location["name"], location["prize_name"], location["uid"])
```

Examples: `First Steps - Score Bubble 1`, `First Steps - Prize Bubble 1 - Henry Face`. One constant names each level; loops construct all locations. Numbering follows initial ascending object UID, not walking order. **Keep the registry**: it preserves IDs and assigned numbers when regenerating. IDs are project-local allocations, not an upstream-approved range. The location list includes candidates that may be conditional or unreachable; reachability logic is still required before enabling every check in a seed.

Regenerate with `python tools/generate_locations.py` after rebuilding the catalogue. There are 37 unresolved names, mainly creator-made GOTY prizes; these are explicitly labelled unresolved and retain their plan IDs. All 18 First Steps prize names and its six award names resolved.

### End-of-level checks

Each level has `Level Complete`, `All Prize Bubbles`, and `Ace (No Deaths)` location definitions, plus separate locations for its actual rewards. Do not assume every level awards six items. For First Steps:

| Condition | Rewards |
|---|---|
| Completion | Bunny Ears; Big Kiss |
| All prizes | The Gardens Concept; The Gardens Concept with Frame |
| Ace | Pirate Hook; Pirate Eye Patch |

`tracker.py` awards completion on a rising completion counter, ace on a rising ace counter, and all-prizes on completion with a known positive prize total matched by the completion-time collected count. It does not award ace merely because the player is alive. It establishes a baseline on startup so pre-existing save progress does not generate new checks. Reward checks accompany their achievement; future AP options should decide whether both sets are enabled.

Live test on 2026-09-16: user deliberately died once and finished First Steps. Reads showed death count 1, completion count 1, ace count 0, collected-at-completion 15/18. This validates that case only; positive ace/all-prize cases and cross-level behavior still need play tests.

```powershell
python tools/lbp_reader.py --progress --output output/live_progress.json
python tools/monitor_checks.py
```

The monitor prints candidate location IDs and death events locally. It is not yet an AP client. Physical pickup checks are handled by the PINE/AP client, independently of this read-only monitor. World death counts may include other players; restrict eventual DeathLink use to single-player until local-player death handling is verified. A world pointer is currently the run token; replay/pointer reuse needs further validation.

### Level unlocks

`level_unlocks.py` defines one `Unlock <level name>` item per level and maps received item IDs to explicit `(slot type, slot number)` states: type 0 for story levels, type 8 for DLC levels. All 95 installed levels have a mapped record in the current live profile. Grants are idempotent, so the full received-item list can be replayed on reconnect. Only Skate to Victory has been individually launch-tested; DLC access may also depend on installed pack availability.

```powershell
# Inspect without changing anything:
python tools/unlock_levels.py --level "Skate to Victory"
# From the pod, grant one item-equivalent unlock (backs up save files first):
python tools/unlock_levels.py --level "Skate to Victory" --apply --save-dir "C:\Emulators\rpcs3-v0.0.38-18509-2b045652_win64_msvc\dev_hdd0\game\BCES00141_USER1\USRDIR"
# Apply an array of received numeric item IDs:
python tools/unlock_levels.py --received-items received_items.json --apply --save-dir "PATH_TO_ACTIVE_LBP_SAVE_USRDIR"
```

The tool verifies the executable, active user, existing slot records and pod state before setting only discovered/unlocked bytes plus the profile dirty bit. Missing records are rejected; allocation for a fresh profile is not implemented. The first live test changed Skate to Victory from locked to unlocked with successful readback; the user confirmed it launched and PINE subsequently reported slot `(0,26376)`. Reopen the story planet to refresh its badges. Backups and before/after memory records are under `output/unlock_backups/`.

This implements **granting level access**, not a complete randomized progression system. Vanilla completion/key unlocks remain active. A randomizer still needs a new-save policy, suppression of vanilla unlocks, seed-specific starting levels, dependency rules, and AP item delivery integration. The tool does not relock the user's existing levels.

### Stickers, materials, costumes and other item definitions

### Native rewards versus Archipelago deliveries

Required randomizer behavior: collecting an enabled prize bubble or earning an
enabled completion/collection/ace reward checks that location and suppresses its
original inventory grant. Receiving an item from Archipelago grants its mapped
inventory plan or level access, without checking any source location. This also
applies when the randomized item returns to the same player: delivery must come
through the AP received-item path. Repeated pickups remain suppressed after a
location is checked. Seed-disabled reward locations retain vanilla behavior.

`reward_routing.py` implements and tests this routing contract, including pending
checks until server acknowledgement. **It is not connected to a live game hook or
an AP client; vanilla prize grants currently still occur.** The activation guard
requires verified suppression, exact pickup identity, independent collection
progress, and incoming inventory grants. Do not enable randomized play by merely
running the read-only monitor.

The game integration must intercept rewards before the inventory insertion and
record the authored bubble UID or exact end-reward location. Removing items after
pickup is unsuitable: an item may already be legitimately owned through AP.
Physical bubble collection and all-prizes progress must remain independent of
inventory ownership; AP deliveries must not count as collecting their source
bubbles. Grant and check queues need seed/slot-scoped persistence and reconnect
reconciliation in the eventual client. These live integration steps remain open.

### Inventory catalogue

`items.py` loads **4,688 definitions** from `data/items.json`: 99 level-unlock items and 4,589 plan resources from the installed base and update maps/FARCs. One Sonic plan resource is absent from the archives and remains explicitly recorded as an extraction error. Marvel adds four levels with 499 checks; their pickup mappings are catalogue-tested but have not yet been play-tested.

Each level item has a `level_unlock` state mapping containing its slot type, slot number, discovered/unlocked offsets and expected value. Other items have an `inventory_plan` state mapping with the plan GUID and SHA1. **Inventory items do not use level-unlock flags**: giving a sticker requires registering its plan in the inventory. That grant operation is not implemented yet. Received inventory items are returned as pending, never falsely marked delivered.

```python
from items import LEVEL_GUID_TO_ITEM_ID, PRIZE_PLAN_TO_ITEM_ID, state_for_item

state_for_item(LEVEL_GUID_TO_ITEM_ID['g26376'])  # Skate to Victory unlock flags
state_for_item(PRIZE_PLAN_TO_ITEM_ID[32150])    # Henry Face inventory-plan identity
```

Every prize/award plan referenced by the location catalogue maps to an item. Each item records its source locations where known. The broad plan scan includes starter, internal, unused and creator-made assets: `pool_status=observed_reward` marks plans seen as rewards; `unreviewed_plan` entries need review before becoming randomized items. 425 plans lack a verified name and use explicit `Unnamed ... [GUID]` labels. These are not invented display names. Duplicate real names are disambiguated with stable resource keys.

Rebuild both catalogues and mappings with:

```powershell
./tools/build_catalogs.ps1
```

This requires the already-built cwlib dependency and Java/Python from the earlier setup. The generators read the installed game and preserve the location registry. `tools/generate_items.py` alone rebuilds item definitions from `output/item_catalog.json`.

### DeathLink status

`deathlink.py` provides a transport bridge using `CommonContext.update_death_link`
and `send_death`, with duplicate and echo suppression. The client now connects it
to `tools/pine_death.py` when the seed enables `death_link`. Incoming deaths use
the traced `RequestedSuicide` flag, only with a stable solo player in a story/DLC
level and matching executable signatures. A live request in Skate to Victory
was consumed by the game, moved the player to dead state 5, and increased the
world death count from 0 to 1 (`output/deathlink_live_test.json`). Pod/loading/dead
states are refused, and uncertain acknowledgement disables further requests.
Network bridge behavior is unit-tested; a full two-client DeathLink play test is
still outstanding. The example YAML keeps DeathLink off by default.

## Working now

- `tools/BubbleCatalog.java` reads the installed GUID map and base FARC. The tested installation produced **148 level resources and 246 slot/pack entries** after adding DLC-pack parsing. One additional slot resource failed to decode and is recorded under `errors` in the output.
- Each authored bubble has a level GUID, object UID, type, position and, for prizes, a prize-plan reference. `level GUID + object UID` is a candidate persistent location key for this exact asset version.
- The First Steps (`g26374`) contains **138 authored score-bubble objects and 18 authored prize-bubble objects**. These are authored-object counts, not guaranteed reachable totals. Emitters, conditional objects, duplicate rewards and revisions need separate handling. This level has 3 emitters.
- PINE connected successfully to the running game during investigation. A traced live array contained the same **18 prize plans**, plus **6 end-of-level rewards**. Its entries are available rewards, not collected flags.
- `tools/lbp_reader.py` implements the traced live prize-total read. It checks title ID, game version and code signatures, bounds array reads and rejects a changed array header. On 2026-09-16 the complete reader connected successfully, observed an empty reward array before the level was ready, then matched The First Steps and returned 18 prizes / 24 total rewards. Three subsequent live samples agreed. Pickup detection and other levels remain unverified.

## Run

With the game running in a story level:

```powershell
python tools/pine_probe.py info
python tools/lbp_reader.py --output output/live_level.json
python tools/lbp_reader.py --watch
python -m unittest discover -s tools -p "test_*.py"
```

The reader identifies a candidate level by matching its full prize-plan multiset against the catalogue. This is not yet a direct current-level-ID read. It reports ambiguity and does not identify prize-free levels this way. `collected_prizes` and `collected_score_bubbles` deliberately remain `null` until validated.

### Rebuild the authored catalogue

The local research checkout is Craftworld Toolkit commit `e4e8f4631624753536dd06ee37e79fdfaf18df9d`, with its MIT license retained in `research/toolkit/LICENSE`. Java 17+ and Maven are required to build its library; Python tooling uses the standard library except the optional disassembler.

```powershell
git clone https://github.com/ennuo/toolkit.git research/toolkit
git -C research/toolkit checkout e4e8f4631624753536dd06ee37e79fdfaf18df9d
mvn -f research/toolkit/pom.xml -pl lib/cwlib -am package -DskipTests
java -cp research/toolkit/lib/cwlib/target/cwlib-0.1.jar tools/BubbleCatalog.java "C:\Emulators\rpcs3-v0.0.38-18509-2b045652_win64_msvc\dev_hdd0\game\NPEA00241\USRDIR" output/bubble_catalog.json
```

`research/` and `output/` are ignored by Git: they contain downloaded dependencies and locally extracted information. Do not distribute game binaries or memory dumps with an Archipelago world.

## Which specific bubble was collected?

**Not yet validated.** Static object IDs are available, but identifying an object is separate from observing its pickup.

- Prize ownership can be correlated with a level's prize plans. Duplicate prize contents, items already owned before entering, rewards granted by other means, and multiplayer make ownership insufficient to prove a particular physical bubble was picked up.
- LBP1's `PlayedLevelData.collectables` is reward metadata. Treating every entry as collected would produce false checks. `tools/PrizeProgress.java` exports this metadata and saved inventory separately; its name does not imply validated pickup tracking.
- The newer `CollectedBubble(level, thingUID, plan)` profile format starts at revision `0x2d2`; the inspected LBP1 save is `0x272` with branch `4C44:0017`, so that field cannot be assumed here.
- Ordinary score bubbles need object-level pickup observation. Score alone cannot recover exact bubble identity or reliable counts because of multipliers and other score sources.
- The installed pickup hooks now record object IDs in a committed event ring, read through PINE and acknowledged after durable AP journalling. Polling missing objects alone is never used as proof of pickup.

## Level randomization

The decoded `gamedata/data/developer_slots.slt` contains distinct slot IDs, level-root descriptors, initial-lock flags and primary progression links. This provides a concrete route to shuffle **which level a story slot loads**.

Proposed experiment: preserve slot identity and progression links, swap two compatible level-root references in a backed-up copy, then verify launch, completion, prize accounting and next-level unlocks. The current tools export these fields but do not modify them. A PINE-only implementation would need the live slot/load-request structures or a load hook; serialized file layouts are not runtime offsets.

Do not claim a working randomizer yet. Tutorials, level keys, completion rewards, dependencies and save accounting must be tested before broad shuffling. Randomizing level geometry is a separate task.

## Required DLC installation check

The client checks the connected slot's DLC level packs, item packs and costume
packs before processing checks or deliveries. Missing packs produce an
`Options error` naming the packs. Install the required DLC and restart RPCS3,
or regenerate the seed with those options disabled. The client retries the
file check automatically; AP unlock items do not satisfy it.

The client detects a single running RPCS3 installation automatically. Use
`--rpcs3-dir "C:\path\to\RPCS3"` to select the active installation explicitly. An explicit
`--save-dir` or the local patch installer's configuration also supplies the game
directory. Costume collections cover their included characters. Item-pack
requirements match the actual non-costume items added by generation; selecting
a family with no such items adds no installation requirement.

This read-only check inspects DLC EDAT content headers in the supported European
game's DLC directory. It checks installation, not cryptographic licence validity.
GOTY community levels are bundled rather than a separate DLC licence package.

## Next live validation

1. Completed 2026-09-16: run the reader in The First Steps and verify the 18-prize total.
2. Locate the active player's inventory lookup and compare before/after a previously unowned prize pickup.
3. Observe a score-bubble pickup and map its runtime object to the authored UID; repeat across death and replay.
4. Test a second level and a full RPCS3 restart to reject accidental pointer stability.
5. Test a reversible two-level destination swap separately from progression randomization.

See `RESEARCH.md` for addresses and evidence.
