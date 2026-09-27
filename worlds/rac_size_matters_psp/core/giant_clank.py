"""Giant Clank stages use resident checks, never Ratchet overlay addresses."""
from ..constants import Rac5Locations, Rac5CutsceneLocations
from .armour import ArmourPiece, ArmourUnlocks
from .address_maps import CURRENT_PLANET_ADDRESS
from .structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE

STAGES = {
    15: (ArmourPiece.GLOVES, (Rac5Locations.METALIS_GLOVES,)),
    21: (ArmourPiece.CHESTPLATE, (Rac5Locations.CHALLAX_CHESTPLATE,
                               Rac5CutsceneLocations.CHALLAX_CLANK)),
}


class GiantClank:
    def __init__(self, memory, planet):
        self.memory, self.planet = memory, planet
        self.active = None
        self.sent = set()

    def tick(self):
        p = self.memory
        current = p.read_int8(CURRENT_PLANET_ADDRESS)
        if p.read_int32(TransitionGateStruct.BASE_ADDRESS) != TRANSITION_GATE_IDLE:
            return []
        if current not in STAGES:
            if self.active is not None:
                self.planet.armour.sync_unlocked(self.planet.unlock_armour)
                self.active = None
            return []
        if not self.planet.giant_clank_allowed:
            return []
        if self.active != current:
            self.active = current
            self.planet.armour.sync_unlocked(dict.fromkeys(ArmourUnlocks._OFFSETS, 0))
            return []
        piece, locations = STAGES[current]
        if not int(self.planet.armour.UnlockedArmour.electroshock) & int(piece):
            return []
        fresh = [loc for loc in locations if loc not in self.sent]
        self.sent.update(fresh)
        return fresh

    def sync_from_ap(self, locations):
        self.sent.update(locations)
