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

## Docs

- **[Setup guide](docs/setup_en.md)** — for players: configuring
  `dynamic_pine_options` in host.yaml.
- **[Adding Dynamic Pine to your apworld](docs/adding_to_apworld.md)** — for
  world authors: declaring support, wiring up your client, patched-ISO
  launches, the `DynamicPineCommandMixin` shortcut.
- **[API reference](docs/api.md)** — every public function/exception.
- **[Client commands](docs/commands.md)** — `/games`, `/launch`,
  `/launch_pcsx2`, `/clear`, `/bios`.
- **[PCSX2.ini settings](docs/ini_settings.md)** — exactly which ini keys
  Dynamic Pine manages and why.

## why start at version 99.0.0
archiepalgo sorts and loads by the version number setting to 99 just ensures its loaded before the other apworlds so it can detect them.

## This is not my idea
The original implementation of dynamic pine came from a PR adding dynamic pine to rac2 apworld by jacobmix all credit for the idea belongs to him as he discovered how to create ini files for dynamic pine usage, the setup and requirements for it. I just took it from him and generalized it as a wrapper for multiple apworlds to utulize. 

## Disclamer
This was made with the help of AI docs and comments aswel as some of the complicated logic, that I was not able to figure out on my own.
