# Ratchet & Clank: Size Matters (PSP) Archipelago Setup Guide

## Requirements

The following are required in order to play Ratchet & Clank: Size Matters (PSP) in Archipelago

- Installed the latest version of [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases)
- The latest version of the Ratchet & Clank: Size Matters (PSP) apworld
- [PPSSPP emulator](https://www.ppsspp.org/downloads) (Windows build)
- A copy of **Ratchet & Clank: Size Matters** — NTSC-U disc or ISO (`UCUS98633`)
---

## Enabling the remote debugger in PPSSPP

The remote debugger is the interface the client uses to communicate with the emulator.

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
