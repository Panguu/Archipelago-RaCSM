from rule_builder.options import OptionFilter
from rule_builder.rules import Has, True_

from ..constants import Rac5ClankChallenges, Rac5Locations as Names, Rac5Planets, Rac5Gadgets, Rac5ShrinkRayGrindrail
from ..data.challenges import CHALLENGE_GROUP_GADGETBOT
from ..options import ClankChallenges, EnableHIGTreehouse, ShrinkRayOptions
from .model import BASE_ID, Completion, LocationOptions, Rac5Locations


CHALLENGE_NAMES = (
    Rac5ClankChallenges.HIG_TREEHOUSE_1,
    Rac5ClankChallenges.HIG_TREEHOUSE_2,
    Rac5ClankChallenges.HIG_TREEHOUSE_3,
    Rac5ClankChallenges.HIG_TREEHOUSE_4,
)

# The arena table selects save-byte IDs 148 onward for Treehouse's Gadgetbot
# section. Save byte IDs are relative to the canonical save block + 0x8C0.
LOCATIONS = tuple(
    Rac5Locations(
        name, Rac5Planets.HIG_TREEHOUSE, lambda world: True_(),
        Completion("challenges", 0x1F4B454 + index, increasing=True),
        code=BASE_ID + 375 + index,
        options=LocationOptions(
            requirements=(OptionFilter(EnableHIGTreehouse, 1), OptionFilter(ClankChallenges, (1, 2), "in")),
            challenge_group=CHALLENGE_GROUP_GADGETBOT,
        ),
        categories=frozenset(("challenge",)),
        check_order=30 + index, definition_order=375 + index,
    )
    for index, name in enumerate(CHALLENGE_NAMES)
) + (
    Rac5Locations(
        Names.HIG_TREEHOUSE_TURRET, Rac5Planets.HIG_TREEHOUSE, lambda world: True_(),
        Completion("events", Names.HIG_TREEHOUSE_TURRET),
        code=BASE_ID + 379,
        options=LocationOptions(requirements=(OptionFilter(EnableHIGTreehouse, 1),)),
        categories=frozenset(("gadget_pickup",)),
        native_planets=(24,), definition_order=379,
    ),
    Rac5Locations(
        Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL, Rac5Planets.HIG_TREEHOUSE,
        lambda world: Has(Rac5Gadgets.SHRINK_RAY),
        Completion("events", Rac5ShrinkRayGrindrail.HIG_TREEHOUSE_GRINDRAIL),
        code=BASE_ID + 380,
        options=LocationOptions(requirements=(OptionFilter(EnableHIGTreehouse, 1),
                                             OptionFilter(ShrinkRayOptions, 1))),
        categories=frozenset(("shrink_ray_skip",)),
        native_planets=(24,), definition_order=380,
    ),
)

