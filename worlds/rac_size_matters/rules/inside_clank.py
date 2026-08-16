from typing import TYPE_CHECKING

from rule_builder.rules import HasAll, True_

from ..constants import (
    Rac5CutsceneLocations,
    Rac5Gadgets,
    Rac5Locations,
    Rac5ShrinkRayGrindrail,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5TitanVendorLocations,
    Rac5VendorLocations,
)

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_inside_clank_rules(world: "RACSizeMatterWorld") -> None:
    player = world.player
    mw = world.multiworld

    _base = HasAll(Rac5Gadgets.HYPERSHOT, Rac5Gadgets.POLARIZER, Rac5Gadgets.SHRINK_RAY)
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.INSIDE_CLANK_SHOCK, player), _base)
        world.set_rule(mw.get_location(Rac5SkillPoints.INSIDE_CLANK_RATCHET, player), _base)

    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.INSIDE_CLANK_ESCAPE, player), _base)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.INSIDE_CLANK_TECHNOMITES, player), _base)

    world.set_rule(mw.get_location(Rac5TBolts.INSIDE_CLANK_LADDER, player), True_())
    world.set_rule(mw.get_location(Rac5TBolts.INSIDE_CLANK_WALL, player), True_())

    world.set_rule(mw.get_location(Rac5Locations.INSIDE_CLANK_CHESTPLATE, player), _base)

    # Static Barrier vendor — freely accessible on arrival.
    world.set_rule(mw.get_location(Rac5VendorLocations.INSIDE_CLANK_STATIC, player), _base)

    if world.options.shrink_ray_locations:
        world.set_rule(
            mw.get_location(Rac5ShrinkRayGrindrail.INSIDE_CLANK_GRINDRAIL, player),
                HasAll(Rac5Gadgets.SHRINK_RAY, Rac5Gadgets.HYPERSHOT)
                )

    # Challenge Mode — NG+ Items only controls the item pool, not location
    # existence (see regions.py, which both tables must agree with on
    # which of these locations actually exist).
    if world.options.challenge_mode.value >= 1:
        # Titan variant available once the base weapon is purchasable at
        # its own vendor — buying it there is what actually unlocks the
        # Titan re-purchase in-game now (see core/vendor.py), matching
        # INSIDE_CLANK_STATIC's own rule above.
        world.set_rule(mw.get_location(Rac5TitanVendorLocations.INSIDE_CLANK_STATIC_TITAN, player), _base)
    if world.options.challenge_mode.value >= 2:
        world.set_rule(mw.get_location(Rac5Locations.INSIDE_CLANK_CHAMELEON_HELMET, player), True_())
