"""Additional puzzle checks, allocated after existing records to preserve IDs."""

from rule_builder.options import OptionFilter
from rule_builder.rules import HasAll

from ..constants import Rac5Gadgets, Rac5Planets, Rac5ShrinkRayGrindrail
from ..options import ShrinkRayOptions
from .model import Completion, LocationOptions, Rac5CompletionSources, Rac5Locations


LOCATIONS = (
    Rac5Locations(
        Rac5ShrinkRayGrindrail.OUTPOST_OMEGA_GRINDRAIL,
        Rac5Planets.OUTPOST_OMEGA,
        lambda world: HasAll(Rac5Gadgets.SHRINK_RAY, Rac5Gadgets.HYPERSHOT, Rac5Gadgets.SPROUT_O_MATIC),
        Completion(Rac5CompletionSources.EVENTS, Rac5ShrinkRayGrindrail.OUTPOST_OMEGA_GRINDRAIL),
        options=LocationOptions(requirements=(OptionFilter(ShrinkRayOptions, (1,), "in"),)),
        categories=frozenset(("shrink_ray_skip",)),
        definition_order=371,
    ),
    Rac5Locations(
        Rac5ShrinkRayGrindrail.CHALLAX_SECOND_PUZZLE,
        Rac5Planets.CHALLAX,
        lambda world: HasAll(Rac5Gadgets.SHRINK_RAY, Rac5Gadgets.POLARIZER, Rac5Gadgets.SPROUT_O_MATIC),
        Completion(Rac5CompletionSources.EVENTS, Rac5ShrinkRayGrindrail.CHALLAX_SECOND_PUZZLE),
        options=LocationOptions(requirements=(OptionFilter(ShrinkRayOptions, (1,), "in"),)),
        categories=frozenset(("shrink_ray_skip",)),
        definition_order=372,
    ),
    Rac5Locations(
        Rac5ShrinkRayGrindrail.OUTPOST_OMEGA_SECOND_GRINDRAIL,
        Rac5Planets.OUTPOST_OMEGA,
        lambda world: HasAll(Rac5Gadgets.SHRINK_RAY, Rac5Gadgets.HYPERSHOT, Rac5Gadgets.SPROUT_O_MATIC),
        Completion(Rac5CompletionSources.EVENTS, Rac5ShrinkRayGrindrail.OUTPOST_OMEGA_SECOND_GRINDRAIL),
        options=LocationOptions(requirements=(OptionFilter(ShrinkRayOptions, (1,), "in"),)),
        categories=frozenset(("shrink_ray_skip",)),
        definition_order=373,
    ),
)
