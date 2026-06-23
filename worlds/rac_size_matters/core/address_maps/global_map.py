from __future__ import annotations

from ...interface_orchestrator.structs.address_map import AddressMap
from ..structs.game import (
    ControllerStruct,
    GameStatusStruct,
    MissionsStruct,
    PlanetProgressStruct,
    QuickSelectStruct,
    TransitionGateStruct,
)
from ..structs.pickups import (
    ArmourSetCollectedStruct,
    ArmourStruct,
    ClankChallengeStruct,
    SkillPointsStruct,
    SkyboardStruct,
    TitaniumBoltStruct,
)


def build_global_address_map() -> AddressMap:
    address_map = AddressMap(interface_id="global")
    address_map.register(
        QuickSelectStruct,
        ArmourStruct,
        ArmourSetCollectedStruct,
        TitaniumBoltStruct,
        SkillPointsStruct,
        GameStatusStruct,
        ControllerStruct,
        PlanetProgressStruct,
        ClankChallengeStruct,
        SkyboardStruct,
        MissionsStruct,
        TransitionGateStruct,
    )
    return address_map
