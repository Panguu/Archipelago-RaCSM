# Sticker and key sanity (NPEA00241 v1.30)

`sticker_sanity: true` adds 162 authored sticker-switch locations across enabled
levels. Each needs its level unlock and exact sticker item. Required stickers are
progression items and enter the pool even if their original reward level is excluded.
`key_sanity: true` adds 27 authored collectible-key locations. Both default off.
Generate a new seed to add these locations; restarting an existing seed cannot add them.

Extraction decoded all 99 catalogued levels without errors. Seven sensors with no
sticker descriptor are recorded as excluded, rather than guessed. Authored sensors
are not a guarantee that every sensor is reachable: all-level physical validation
is still outstanding. Emitted instances are not inferred as extra checks.

The read-only sticker detector validates level, profile, native switch type, exact
Thing UID, owner pointers and sticker GUID before accepting activation. Get a Grip's
Tea Pot sensor (UID 824392) was live-tested changing from 0 to 1 while the other seven
sensors stayed inactive. A sensor destroyed before polling may be missed; a native
activation event hook remains a possible improvement if such a case is found.

Keys use an added native CollectKey hook and the existing durable pickup ring. A
check needs exact source level, key UID and target SlotID. An unlocked level or a
disappearing key alone never creates a check. AP level-access overrides continue
to control the key's original bonus-level destination. The key hook needs a full
RPCS3 restart. Live-tested Get a Grip's key UID 7714 targeting slot 26368:
the hook produced exactly location 1241000052. The client tests verify seed filtering,
durable recording before acknowledgement, and outgoing AP LocationChecks packets.

The installed GOTY bonus levels use local developer slots from `goty_levels.slt`.
The new patch makes the native IsGOTYVersion query true to expose their menu. It does
not connect to an online community server. The player confirmed that the bonus
levels now appear and can be selected; full playthroughs remain untested.
Kit and individual AP level locks remain separate.

Regenerate with `tools/build_catalogs.ps1`; interaction IDs persist in
`data/interaction_ids.json`. Constants are generated per level (sticker switches and
keys together) under `constants/interactions/base/` and `constants/interactions/dlc/<kit>/`,
mirroring `constants/levels/`. Game assets are read only; the native changes are RPCS3 boot
patches. Installation backs up patches, config and the active save.
