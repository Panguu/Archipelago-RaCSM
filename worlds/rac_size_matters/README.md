# Ratchet & Clank Size Matters Archipelago

This is an implementation for the PS2 version of the game. You can find the setup guide [here](docs/setup_en.md).

## Disclamer
This is **not** all **Human written code**, this was developed with the help of AI. This was mostly done to speed up development and to test new logical improvements from how the original version of the AP was written.

## Known Bugs and issues
- **Starting Skin can leave Ratchet invisible after a planet load.** If Starting Skin is set to anything other than Default, open the in-game Skins menu and close it again after each planet load — otherwise the chosen skin doesn't fully apply and the model can turn invisible instead.

The rest of these are open design questions we're deliberately not resolving right now — parked pending feedback or a plan that doesn't regress other logic, not active bugs blocking play.
- **Pokitaru/Ryllus starting infobot is merged, not split.** Vanilla treats Pokitaru and Ryllus as two separate starting planets, but a split into two independent infobots broke other logic when tried, so they currently share a single combined "Infobot: Pokitaru and Ryllus" item instead.
- **Nanotech (health) level check rule scaling isn't tuned.** The difficulty curve for higher Nanotech Levels is a rough cut, not a carefully considered scale — we don't yet know the right way to space it out, so it's parked until we get more playtesting feedback.
- **Skyboard Challenges has no item-only tier.** Unlike Clank Challenges (off / item rewards only / all completions), Skyboard Challenges is only off/all — no middle option for just the reward-bearing checks, and no separate "all checks" toggle for Skyboard missions specifically.

## Massive thank you's
The PCSX2 PINE interface (`pcsx2_interface/`) is adapted from [evilwb/pypine](https://github.com/evilwb/pypine), based on https://projects.govanify.com/govanify/pine. This couldn't have been done without his pcsx2 interface.

Massive inspiration from RAC2 and RAC3 AP's for how to handle Ratchet and Clank games.

Massive thanks to RAC3 dev Taoshi for letting me steal his logic and some functions to fit into size matters.

Amondo for tidying up my static strings and for testing this game ( honestly think hes played the game more than I have at this point )

Concrete for making the absolutly fantastic icon im no artist so having someone actually talanted make one is amazing!!!

ImJustATester for helping me find addresses (especially the traps) as well as load logic and other fixes theres honestly too many addresses and maps they helped find i couldnt list them all.
