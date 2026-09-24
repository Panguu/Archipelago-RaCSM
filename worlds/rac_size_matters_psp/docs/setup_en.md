# Ratchet & Clank: Size Matters (PSP) Archipelago Setup Guide

This is an experimental PSP port. Read [runtime parity status](runtime-parity.md) before generating a seed with newly added options.

## First playtest

Use `examples/PSPPlayer.yaml` for the initial playtest. It starts on Pokitaru and disables the runtime features that are still being ported. The generation rules remain shared with the PS2 version.

For this checkout, `build/rac_size_matters_psp.apworld` is the installable package and `build/playtest/AP_63004146548060263751.zip` is a generated solo seed for slot **PSPPlayer**. Install the apworld in Archipelago, host the seed ZIP, launch **Ratchet & Clank: Size Matters PSP Client**, and connect as PSPPlayer. Load a new UCUS98633 game in PPSSPP with its remote debugger enabled. The startup grant is 45,000 bolts, two random weapons, and the Hypershot.

The standard client runs without Universal Tracker. To opt into an installed and configured tracker, set `RACSM_PSP_TRACKER=1` before launching. In-game notification rendering and the newer native gameplay patches are not yet active; notifications appear in the client log.

Validation includes a real local Archipelago server and the actual PSP client using synthetic PSP RAM: authentication, starting inventory, starting-bolt checkpoints, mission reporting, and reward delivery passed. This is not a completed live-emulator playthrough.

## Requirements

The following are required in order to play Ratchet & Clank: Size Matters (PSP) in Archipelago

- Installed the latest version of [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases)
- The latest version of the Ratchet & Clank: Size Matters (PSP) apworld
- [PPSSPP emulator](https://www.ppsspp.org/downloads) (Windows build)
- Install `requirements.txt` using the Python environment that runs the Archipelago client (`python -m pip install -r requirements.txt`).
- A copy of **Ratchet & Clank: Size Matters** — NTSC-U disc or ISO (`UCUS98633`)
---

## Enabling the remote debugger in PPSSPP

Gameplay RAM reads and writes use pymem in the local PPSSPP process. The remote debugger supplies metadata and CPU/cache control; it does not read or write gameplay memory. Only one PPSSPP process may be running. The client discovers its local debugger port automatically, without the public discovery service.

1. Open PPSSPP.
2. Go to **Settings → Tools → Developer tools**.
3. Enable **Allow remote debugger**.
4. Restart PPSSPP sometimes allowing debugger bugs out if this doesnt work then close ppsspp in task manager and restart.

---
## Configuring your YAML file

### What is a YAML file and why do I need one?

Your YAML file contains a set of configuration options which provide the generator with information about how it should
generate your game. Each player of a multiworld will provide their own YAML file. This setup allows each player to enjoy
an experience customized for their taste, and different players in the same multiworld can all have different options.

### Where do I get a YAML file?


You can use the "Options Creator" (a GUI tool in the Archipelago Launcher) to customize your options and export your YAML file. You can also use the "Generate Template Options" feature if you prefer editing your YAML in a text editor. Both tools are available in the Archipelago Launcher.

---
## Setting up your Multiworld
### Hosting your MultiWorld

This section is for players who want to host a solo or multiplayer game.

1. Collect YAML files from all participating players.
    - In the Archipelago Launcher, select "Browse Files" and open the `Players` folder.
    - Place each player's YAML file into the `Players` folder.

2. In the Archipelago Launcher, select "Generate" to create your multiworld.
    - The generated zip file will appear in the `output` folder.

3. To host online, upload the zip file from the `output` folder to the [Archipelago Website](https://archipelago.gg/uploads).
    - To host locally, select "Host" in the Archipelago Launcher and choose the zip file from the `output` folder.

### Starting a Game

1. Launch the **R&C: Size Matters (PSP) Client** from the Archipelago launcher.
2. Connect to your Archipelago server with your slot name.
3. Connect client to ppsspp in **main menu**
4. In PPSSPP, load `UCUS98633` and start a **New Game**.


> **Important:** Always start from a New Game at the beginning of a seed. Loading a save from a previous run will cause inventory and location state to be out of sync. To continue an ongoing session, simply reconnect to the same Archipelago connection address and load the save file you used for that session.

---

## Weapons and Gadgets

If weapons or gadgets are not being applied correctly, use the following commands in the client console:

| Command | Description |
|---------|-------------|
| `/reconnect` | Disconnect and reconnect to PPSSPP, then re-apply all received items. Use this if the client loses sync with the emulator. |
| `/disconnect_game` | Disconnect from PPSSPP without closing the client. |

---

## Troubleshooting

**Client says "Wrong game in PPSSPP"**
Make sure you are running `UCUS98633` (NTSC-U). PAL and other regional versions are not supported.

**Vendor purchases are not registering**
Make sure you are standing at a vendor on a planet that has vendor locations. Purchases are detected when you buy from the vendor menu — the client needs to be connected before you open the menu.

**If you need further help**, join the [Archipelago Discord](https://discord.gg/archipelago) and visit the `[PSP/PS2] Ratchet & Clank Size Matters` thread in the `future-game-design` forum channel (located at the bottom).
