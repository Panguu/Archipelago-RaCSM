# LittleBigPlanet (NPEA00241)

Archipelago world for LittleBigPlanet on RPCS3. The client talks to the emulator over PINE.

## Layout

| Path | What it holds |
| --- | --- |
| `world.py` | `LittleBigPlanetWorld`: option handling, item pool, slot data, `level_rule()` |
| `regions.py` | Menu, one region per enabled level, My Content regions, victory events |
| `rules.py` | Applies each location's `access_rule()`, plus the completion rule |
| `locations/model.py` | `Kind`, `LBPLocationData`, `LBPLocation` |
| `locations/base/`, `locations/dlc/` | Generated, one file per level |
| `items.py`, `Options.py`, `chapters.py`, `dlc.py`, `content_packs.py` | Items, options and level groupings |
| `Client.py`, `pine_game.py`, `tracker.py`, `core/` | RPCS3 client |
| `tools/generate_locations.py` | Rebuilds `locations/**` and `constants/data/levels.py` from `data/*.json` |

## Locations

Each check is one `LBPLocationData` record in its level's file:

```python
LBPLocationData('Get a Grip - Prize Bubble 19 - Golf Club Bottom', LEVEL, Kind.PRIZE,
                uid=808453, plan='g51381', rule=Has('Tea Pot')),
```

Location ids are not written in the files. Each record takes the next id from a counter
(starting at 1,240,000,000) in load order: base levels, then DLC, top to bottom. Add new
locations at the end of the last file so existing ids don't shift.

| Field | Meaning |
| --- | --- |
| `kind` | `score`, `prize`, `key`, `sticker_switch`, `complete`, `ace`, `all_prizes` or `reward` |
| `uid` | Score/prize bubble, key or sticker switch uid in the level |
| `plan` | Prize, reward or sticker plan GUID |
| `target_slot` | Level a key unlocks |
| `condition` | For rewards: the `complete`, `ace` or `all_prizes` event that grants them |
| `players` | Co-op players needed. The location is removed when the Players option is lower |
| `rule` | Extra `rule_builder` requirement, on top of the level rule |

Every location automatically requires its level: the level's unlock item or Progressive
Curators count, and its DLC kit when it has one. A sticker switch also requires its sticker.
All Prize Bubbles and its rewards inherit the rules and players of every prize bubble in the level.

### Adding a rule

Edit the location's line in `locations/base/<level>.py` (or `dlc/`), adding `rule=` and/or `players=`:

```python
LBPLocationData('The Mines - Prize Bubble 4 - Sardine Can', LEVEL, Kind.PRIZE,
                uid=530994, plan='g34559', rule=Has('Angry Skull [plan/g31825]')),
LBPLocationData('Boom Town - Prize Bubble 8 - Powered Mine Cart', LEVEL, Kind.PRIZE,
                uid=246592, plan='g47047', players=2),
```

### Regenerating

```powershell
python tools/generate_locations.py
```

This writes a file for every level in `data/levels.json` and `data/interactions.json`. It keeps
existing `rule=` and `players=` arguments (matched by location name), so hand-written rules survive.

## Client

Launch "LittleBigPlanet Client" from the Archipelago launcher, then:

- `/patch` verifies the running game and exports the personal RPCS3 patch.
- `/pine` shows the PINE connection status.
- `/reset_progress` previews saved level counters (`/reset_progress apply` clears them).

`research/`, `output/`, `data/` and `tools/` are not packaged into the apworld (see `.apignore`).
Do not distribute game binaries or memory dumps.
