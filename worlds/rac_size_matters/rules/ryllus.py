from typing import TYPE_CHECKING

from rule_builder.rules import Has, HasAll, True_

from ..constants import (
    Rac5CutsceneLocations,
    Rac5Gadgets,
    Rac5Locations,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5TitanVendorLocations,
    Rac5VendorLocations,
)

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld


def set_ryllus_rules(world: "RACSizeMatterWorld") -> None:
    player = world.player
    mw = world.multiworld

    _full = HasAll(Rac5Gadgets.HYPERSHOT, Rac5Gadgets.SPROUT_O_MATIC)

    if world.options.skill_points.value >= 1:
        world.set_rule(mw.get_location(Rac5SkillPoints.RYLLUS_CAMERA, player), True_())
        world.set_rule(mw.get_location(Rac5SkillPoints.RYLLUS_SHIP_IT, player), _full)
    if world.options.skill_points.value >= 2:
        world.set_rule(mw.get_location(Rac5SkillPoints.RYLLUS_BURY, player), _full)

    if world.options.all_cutscenes:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.RYLLUS_BUZZING, player), True_())
    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.RYLLUS_ARTIFACT, player), _full)
        world.set_rule(mw.get_location(Rac5CutsceneLocations.RYLLUS_TEMPLE, player), _full)

    world.set_rule(mw.get_location(Rac5TBolts.RYLLUS_CLIFF, player), True_())
    world.set_rule(mw.get_location(Rac5TBolts.RYLLUS_WALL, player), _full)
    world.set_rule(mw.get_location(Rac5Locations.RYLLUS_HELMET, player), _full)
    world.set_rule(mw.get_location(Rac5Locations.RYLLUS_BOOTS, player), Has(Rac5Gadgets.SPROUT_O_MATIC))

    world.set_rule(mw.get_location(Rac5VendorLocations.RYLLUS_AGENTS, player), True_())

    # Challenge Mode — NG+ Items only controls the item pool, not location
    # existence (see regions.py, which both tables must agree with on
    # which of these locations actually exist).
    if world.options.challenge_mode.value >= 1:
        world.set_rule(mw.get_location(Rac5Locations.RYLLUS_HYPERBOREAN_BOOTS, player), _full)
        # Titan variant available once the base weapon is purchasable at
        # its own vendor — buying it there is what actually unlocks the
        # Titan re-purchase in-game now (see core/vendor.py), matching
        # RYLLUS_AGENTS's own rule above.
        world.set_rule(mw.get_location(Rac5TitanVendorLocations.RYLLUS_AGENTS_TITAN, player), True_())
