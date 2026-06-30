from __future__ import annotations

import asyncio
import logging

from CommonClient import ClientCommandProcessor, CommonContext
from NetUtils import ClientStatus

from ..locations import INTRO_LOCATION, location_table
from .backend import ALL_SCENES, OddCoupleServer

logger = logging.getLogger("OddCoupleClient")

# Which scene the SWF reports maps to which AP item that must be held to enable it.
SCENE_TO_ITEM = {
    "stereo": "Stereo",
    "taxiDriver": "Taxi Driver",
    "gimp": "Gimp",
    "phonecall1": "Phonecall",
    "scissors": "Scissors",
    "tv": "TV",
}

# Which location(s) get checked off when a scene is reported. "gimp" can be
# replayed, and each playthrough fills the next not-yet-checked Gimp location.
# Derived from location_table (keyed by item, via SCENE_TO_ITEM) rather than
# hardcoded, so renaming locations in locations.py doesn't require a matching
# edit here. "The Odd Couple Intro" has no item requirement (data.item is
# None) and isn't tied to any scene - it's checked directly on connect, below.
_ITEM_TO_SCENE = {item: scene for scene, item in SCENE_TO_ITEM.items()}
SCENE_TO_LOCATIONS: dict[str, list[str]] = {}
for _location_name, _location_data in location_table.items():
    if _location_data.item is None:
        continue
    SCENE_TO_LOCATIONS.setdefault(_ITEM_TO_SCENE[_location_data.item], []).append(_location_name)


class OddCoupleCommandProcessor(ClientCommandProcessor):
    ctx: "OddCoupleContext"


class OddCoupleContext(CommonContext):
    game = "Ratchet & Clank: The Odd Couple"
    items_handling = 0b111
    command_processor = OddCoupleCommandProcessor

    def __init__(self, server_address: str | None, password: str | None) -> None:
        super().__init__(server_address, password)
        # NOT "self.server" - CommonContext reserves that name for the actual
        # AP multiserver connection (server_loop overwrites it with an
        # Endpoint once connected), which would silently clobber this.
        self.local_server = OddCoupleServer(self.on_scene_initiated)
        self.received_item_names: set[str] = set()

    def run_gui(self):
        from kvui import GameManager

        class OddCoupleManager(GameManager):
            logging_pairs = [("Client", "Archipelago")]
            base_title = "The Odd Couple Archipelago Client"

        self.ui = OddCoupleManager(self)
        self.ui_task = asyncio.create_task(self.ui.async_run(), name="UI")

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        self.tags = set()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict) -> None:
        if cmd == "Connected":
            self.received_item_names = set()
            self.local_server.set_suppressed(set(ALL_SCENES))
            intro_id = location_table[INTRO_LOCATION].code
            if intro_id not in self.checked_locations:
                asyncio.create_task(self.check_locations([intro_id]))
            # Covers reconnecting after every location was already checked in
            # a previous session, where no further check is sent to trigger this.
            asyncio.create_task(self.maybe_send_goal())

        if cmd == "ReceivedItems":
            new_names = [self.item_names.lookup_in_slot(item.item) for item in args["items"]]
            self.received_item_names.update(new_names)
            scenes_to_enable = [scene for scene, item in SCENE_TO_ITEM.items() if item in self.received_item_names]
            self.local_server.enable(scenes_to_enable)

        if cmd == "RoomUpdate" and "checked_locations" in args:
            asyncio.create_task(self.maybe_send_goal())

    async def on_scene_initiated(self, scene: str) -> None:
        location_names = SCENE_TO_LOCATIONS.get(scene)
        if not location_names:
            return
        for location_name in location_names:
            location_id = location_table[location_name].code
            if location_id not in self.checked_locations and location_id not in self.locations_checked:
                self.locations_checked.add(location_id)
                await self.check_locations([location_id])
                break

    async def maybe_send_goal(self) -> None:
        """The goal is 100% - every one of this slot's locations checked. missing_locations
        is server-confirmed (updated on Connected/RoomUpdate), so it's only accurate to check
        here rather than right after our own check_locations call, which hasn't round-tripped yet."""
        if self.finished_game or self.missing_locations:
            return
        self.finished_game = True
        await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])

    async def disconnect(self, allow_autoreconnect: bool = False):
        self.locations_checked = set()
        await super().disconnect(allow_autoreconnect)
