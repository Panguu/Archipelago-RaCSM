# Dynamic Pine

Shared PCSX2/PINE infrastructure for Archipelago PS2 game worlds. Like Universal
Tracker, this is not a playable game — it's an extension apworld that gets copied
into the `worlds/` folder, and other apworlds build on top of it.

Dynamic Pine owns everything PCSX2 so game worlds don't have to:

- Per-instance **portable PCSX2 configs** under one data root, grouped by game
  serial and then slot name, so multiple games and slots run at once without
  sharing an ini, memcard, or port.
- **PINE enabled** on a free port per instance (reusing the instance's previous
  port when it's not taken).
- A per-instance **memcard** and a **shared BIOS folder** (BIOS setup happens
  once, not once per instance).
- **RetroAchievements disabled** on every instance it builds.
- **Launching PCSX2** with the user's ISO, tracked by pid file so re-launches
  attach to the running instance instead of spawning a duplicate.
- A **hub client** ("Dynamic Pine" in the AP Launcher) with a tab per supported
  game: launch PCSX2 instances, launch the game's own client, see every
  instance that's been configured (running or stopped), and clear out unused
  ones. Also usable headless via `/games`, `/launch`, `/launch_pcsx2`, and
  `/clear`.

The `pypine` folder is a git submodule of <https://github.com/evilwb/pypine>
(same pin as rac_size_matters), which provides the PINE protocol implementation
and the base `PineConfig` ini builder.

## User setup (host.yaml)

```yaml
dynamic_pine_options:
  pcsx2_path: "C:/Program Files/PCSX2/pcsx2-qt.exe"
  pcsx2_data_path: "dynamic_pine_pcsx2_data"
  bios_path: "C:/Users/you/Documents/PCSX2/bios"
  game_files:
    SCUS-97615: "C:/isos/Ratchet and Clank Size Matters.iso"
```

`game_files` is keyed by each game's PS2 serial. A game with no entry can still
be played — Dynamic Pine just can't auto-launch PCSX2 for it.

## Adding Dynamic Pine support to your apworld

Two touch points, both optional-dependency safe.

**1. Declare support on your World** (this is how the hub discovers your game):

```python
try:
    from worlds.dynamicpine import DynamicPineGame
except ImportError:
    DynamicPineGame = None


class MyPS2World(World):
    game = "My PS2 Game"
    ...
    if DynamicPineGame:
        dynamic_pine = DynamicPineGame(
            game_id="SCUS-97615",              # serial as PCSX2/PINE reports it
            client_component="My Game Client", # your Component's display_name
            # memcard_name="memcard.ps2",      # optional
            # ini_overrides={"EmuCore": {"EnableCheats": "true"}},  # optional
        )
```

**2. Get your PINE port from Dynamic Pine in your client**, typically in your
`Connected` package handler once the slot name is known:

```python
try:
    from worlds.dynamicpine import launch_pcsx2
except ImportError:
    launch_pcsx2 = None

if launch_pcsx2:
    port = launch_pcsx2("My PS2 Game", self.auth)
    if port is not None:
        self.pine.port = port  # or however your client sets its PINE port
```

That's the whole integration: Dynamic Pine builds/repairs the ini, picks the
port, disables achievements, launches PCSX2 with the user's ISO, and hands you
the port. If this exact game+slot instance is already running, `launch_pcsx2`
raises `InstanceAlreadyRunningError` instead of launching a duplicate - catch
it and fall back to `get_pine_port(game, slot_name)` to reuse the existing
port (this is exactly what re-asking on reconnect should do):

```python
from worlds.dynamicpine import InstanceAlreadyRunningError, get_pine_port, launch_pcsx2

try:
    port = launch_pcsx2("My PS2 Game", self.auth)
except InstanceAlreadyRunningError:
    port = get_pine_port("My PS2 Game", self.auth)
if port is not None:
    self.pine.port = port
```

`get_pine_port(game, slot_name)` is also available on its own if you only want
to look up a port without launching anything.

Your client's logic is untouched from there onwards — Dynamic Pine never wraps
or modifies game clients, it only starts them.

## PCSX2.ini settings Dynamic Pine manages

Dynamic Pine only ever touches these keys, re-applying all of them on every
(re)build of an instance's ini so manual edits self-correct on the next
launch. Anything else in `PCSX2.ini` is left as PCSX2's own defaults / the
user's own settings:

| Section        | Key                | Value                          | Set by |
|----------------|---------------------|--------------------------------|--------|
| `EmuCore`      | `EnablePINE`        | `true`                          | `pypine`'s `PineConfig` |
| `EmuCore`      | `PINESlot`          | the instance's resolved port    | `pypine`'s `PineConfig` |
| `Memcard`      | `Slot1_Enable`      | `true`                          | `pypine`'s `PineConfig` |
| `Memcard`      | `Slot2_Enable`      | `false`                         | `pypine`'s `PineConfig` |
| `Memcard`      | `Slot1_Filename`    | the game's `memcard_name`       | `pypine`'s `PineConfig` |
| `Folders`      | `Bios`              | the shared `bios_path`, if set  | `DynamicPineConfig` |
| `Achievements` | `Enabled`           | `false`                         | `DynamicPineConfig` (`BASE_INI_SETTINGS`) |
| `Achievements` | `ChallengeMode`     | `false`                         | `DynamicPineConfig` (`BASE_INI_SETTINGS`) |
| `UI`           | `SetupWizardIncomplete` | `false`                     | `DynamicPineConfig` (`BASE_INI_SETTINGS`) |
| `UI`           | `SettingsVersion`   | `1`                             | `DynamicPineConfig` (`BASE_INI_SETTINGS`) |
| *(any)*        | *(any)*             | per-game `ini_overrides`        | the game's `DynamicPineGame` declaration |

The `UI` keys exist purely to skip two blocking PCSX2 dialogs a brand-new,
blank ini otherwise pops on its very first `-batch` launch - PCSX2's
first-run setup wizard, and a "Settings failed to load, or are the incorrect
version - reset to defaults?" confirmation. Without them, Dynamic Pine's
headless launch just hangs waiting for someone to click through a dialog on
an emulator window it never expects anyone to look at.

A game adds to this list, rather than Dynamic Pine growing more hardcoded
settings, via `ini_overrides` on its `DynamicPineGame` declaration - see
`ini_overrides={"EmuCore": {"EnableCheats": "true"}}` in the example above.
Overrides are applied last, after the base settings, so a game can override
anything above except `EnablePINE`/`PINESlot` (re-applied last of all by
`pypine` itself, so PINE can never accidentally be disabled).

## Environment variable: picking up the PINE port without a round trip

`launch_pcsx2` and `ensure_instance_config` both set
`ARCHIPELAGO_DYNAMIC_PINE_PORT` in the hub process's own environment every
time either one resolves an instance's port. Because game clients are spawned
from the hub via `multiprocessing.Process`, they inherit the hub's
environment at spawn time - the same mechanism `ARCHIPELAGO_DYNAMIC_PINE_HUB`
already relies on (see `launched_via_hub()`).

This means: clicking "Launch Client" for a game prepares that instance's
config (via `ensure_instance_config`, even if its PCSX2 isn't started yet)
before the client process is spawned, so the client comes up with
`ARCHIPELAGO_DYNAMIC_PINE_PORT` already set to the right port - it can read it
immediately with `get_pine_port_from_env()`, before it's even connected to an
AP server or knows its slot name:

```python
from worlds.dynamicpine import get_pine_port_from_env

env_port = get_pine_port_from_env()
if env_port is not None:
    self.pine.port = env_port  # point at it immediately, no need to wait
```

**This is a fast-path only, not a replacement for calling
`launch_pcsx2`.** A client must still call it (typically from its
`Connected` handler, once the slot name is known) to actually get PCSX2
launched in the first place, and to get the correct port if this particular
instance wasn't already running when the client process was spawned (in
which case the env var wasn't set yet, or belongs to a different instance
that resolved a port more recently).

Because the env var is a single fixed name (not keyed by game), it only ever
reflects the *most recently resolved* instance's port in that process - never
rely on it once more than one Dynamic Pine instance may have been resolved in
the same process (the hub itself, mid-session, launching several games).

## Managing instances

- `list_instances(spec)` returns every instance that's ever been configured
  for a game (running or stopped), each with its `instance_id`, `port`, and
  `running` flag - what the hub's per-game "Instances:" line and `/games`
  are built from. `list_running_instances(spec)` is just the running subset.
- `remove_instance(spec, instance_id)` deletes one stopped instance's whole
  datapath (ini, memcard, pid file, save states). It refuses (raising
  `InstanceAlreadyRunningError`) if that instance's PCSX2 is still running -
  stop it first.
- `clear_unused_instances(spec)` removes every stopped instance for a game in
  one call, leaving running ones alone, and returns the instance IDs it
  removed. This is what the hub's "Clear Unused" button and the `/clear`
  command use, for cleaning up old/one-off slot names without hunting down
  their data folders by hand.
