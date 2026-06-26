# Ratchet & Clank Size Matters Archipelago

This is an implementation for the PS2 version of the game. You can find the setup guide [here](docs/setup_en.md).

## Disclamer
This is **not** all **Human written code**, this was developed with the help of AI. This was mostly done to speed up development and to test new logical improvements from how the original version of the AP was written.

## Known Bugs and issues
- vendor purchases currently set ratchets active weapon (change to a unlocked weapon)
- vendor purchases sometimes does not display purchasable weapons (for this issue just walk away from the vendor wait a second and open the vendor again).
- Luna if you havnt beaten her before entering clank will appear after completeing clank. if you become stuck on the luna platform at any time death abuse to get reset back to a playable area.
- Giant Clank Metalis mission is currently not a checks (do not do this mission unless you have at least outpost omega so you dont get softlocked).
- Outpost Omega 1 currently removed from game, until logic for level is completed.

## Massive thank you's
The PCSX2 PINE interface (`pcsx2_interface/`) is adapted from [evilwb/pypine](https://github.com/evilwb/pypine), based on https://projects.govanify.com/govanify/pine. This couldn't have been done without his pcsx2 interface.

Massive inspiration from RAC2 and RAC3 AP's for how to handle Ratchet and Clank games.

Massive thanks to RAC3 dev Taoshi for letting me steal his logic and some functions to fit into size matters.

Amondo for tidying up my static strings and for testing this game ( honestly think hes played the game more than I have at this point )

ImJustATester for helping me find addresses (especially the traps) as well as load logic and other fixes theres honestly too many addresses and maps they helped find i couldnt list them all.
