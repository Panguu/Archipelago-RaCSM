# Size Matters: standalone skins for PCSX2

Adds all seven single-player skins (including Trash Ratchet) and all 13 red
multiplayer skins to the single-player Skins menu. No Archipelago client,
server, Python, or PINE connection is needed to use these files.

| Disc | Patch file |
| --- | --- |
| US — SCUS-97615 | `SCUS-97615_8661F7BA.pnach` |
| Europe/Australia — SCES-55019 | `SCES-55019_FCB981D5.pnach` |
| Japan — SCPS-15120 | `SCPS-15120_9ADCF7AF.pnach` |

## Install

1. Copy the file matching your disc into PCSX2's **patches** folder. PCSX2's
   **Tools → Edit Patches** command can locate/create the patch file for your
   currently running game. If you already have a file with the same name,
   append this patch's `[All single-player and multiplayer skins]` section to
   it instead of replacing your other patches.
2. In the game's **Properties → Patches**, enable **All single-player and
   multiplayer skins**.
3. Fully restart the game, then load your normal save. Select a skin in the
   in-game Skins menu and close the menu to apply it.

Use a current PCSX2 build. These patches use the documented grouped PNACH
format and extended conditional writes:
https://pcsx2.net/docs/advanced/writing-patches/

## Use and limitations

- These are standalone single-player patches. Do not run them together with
  the Archipelago client, which installs its own skin loader.
- Enable before a cold boot. A save state created before enabling the patch
  can bypass the level-loading step where it installs. Use a normal memory-card
  save instead.
- Select Default Ratchet and save before removing the patch. Fully restart
  PCSX2 after disabling it; disabling a PNACH does not undo injected code.
- This adds the red multiplayer variants; blue team variants are not included.
- Multiplayer mode and alternate executable revisions are not supported.
- The three executable CRCs were checked against the local retail disc images.
  Automated tests execute the installer against bounded retail loader fixtures
  and compare its output with the existing skin loader. The PNACHs have **not
  yet been playtested from a clean PCSX2 boot**. Treat this initial release as
  experimental until menu selection and planet travel are tested in-game.

## Development

From the repository root, rebuild with:

```text
python -m worlds.rac_size_matters.tools.build_skin_pnach
```

The generated EE installer locates the relocated module's skin menu and loader
before level startup, resolves their native calls, initializes the extended
menu/model tables, and publishes the code hooks last. It uses reserved space
inside the existing hero buffer, checks the regional buffer pointer and loader
instructions, and preserves the original loader registers and instructions.
It never installs Archipelago vendor, inventory, notification, or item hooks.
