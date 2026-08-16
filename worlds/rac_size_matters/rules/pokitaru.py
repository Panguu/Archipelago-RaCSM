from typing import TYPE_CHECKING

from rule_builder.rules import Has, True_

from ..constants import (
    Rac5CutsceneLocations,
    Rac5Locations,
    Rac5SkillPoints,
    Rac5TBolts,
    Rac5TitanVendorLocations,
    Rac5VendorLocations,
    Rac5Weapons,
)
from ..items import GLITCHES_ITEM_NAME
from ._helpers import HasProjectileWeapon, HasWeapon

if TYPE_CHECKING:
    from ..world import RACSizeMatterWorld

# Universal Tracker glitched-logic only (see world.glitches_item_name) — every
# check on Pokitaru is reachable via glitches EXCEPT the Mootator skill point
# (POKITARU_COWS below, deliberately left without this OR'd in). Never
# actually creatable during real generation, so this has no effect there.
_GLITCH = Has(GLITCHES_ITEM_NAME)


def set_pokitaru_rules(world: "RACSizeMatterWorld") -> None:
    player = world.player
    mw = world.multiworld

    if world.options.skill_points.value >= 1:
        world.set_rule(mw.get_location(Rac5SkillPoints.POKITARU_TRAIN, player), HasProjectileWeapon() | _GLITCH)
        world.set_rule(mw.get_location(Rac5SkillPoints.POKITARU_BOAT, player), True_())
    if world.options.skill_points.value >= 2:
        # Deliberately no glitch route — see _GLITCH's comment above.
        world.set_rule(mw.get_location(Rac5SkillPoints.POKITARU_COWS, player), HasWeapon(Rac5Weapons.MOOTATOR))

    if world.options.all_missions:
        world.set_rule(mw.get_location(Rac5CutsceneLocations.POKITARU_RESCUE, player), True_())
        world.set_rule(mw.get_location(Rac5CutsceneLocations.POKITARU_FIGHT, player), True_())

    world.set_rule(mw.get_location(Rac5TBolts.POKITARU_ZIPLINE, player), True_())
    world.set_rule(mw.get_location(Rac5TBolts.POKITARU_HUT, player), True_())

    world.set_rule(mw.get_location(Rac5Locations.POKITARU_CHESTPLATE, player), HasProjectileWeapon() | _GLITCH)
    world.set_rule(mw.get_location(Rac5Locations.POKITARU_GLOVES, player), HasProjectileWeapon() | _GLITCH)

    # Weapons and gadgets freely accessible on arrival.
    world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_LACERATOR, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_ACID, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_CONCUSSION, player), True_())
    world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_HYPERSHOT, player), True_())

    # Challenge Mode — NG+ Items only controls the item pool, not location
    # existence (see regions.py, which both tables must agree with on
    # which of these locations actually exist).
    if world.options.challenge_mode.value >= 1:
        world.set_rule(
            mw.get_location(Rac5Locations.POKITARU_HYPERBOREAN_GLOVES, player), HasProjectileWeapon() | _GLITCH
        )
        world.set_rule(mw.get_location(Rac5VendorLocations.POKITARU_RYNO, player), True_())
        # Titan variants become available the moment the base weapon is
        # purchasable at its own vendor — buying it there is now what
        # actually unlocks the Titan re-purchase in-game (see
        # core/vendor.py), no separate progression requirement — so these
        # match the base weapon's own vendor-location rule exactly.
        world.set_rule(mw.get_location(Rac5TitanVendorLocations.POKITARU_LACERATOR_TITAN, player), True_())
        world.set_rule(mw.get_location(Rac5TitanVendorLocations.POKITARU_ACID_TITAN, player), True_())
        world.set_rule(mw.get_location(Rac5TitanVendorLocations.POKITARU_CONCUSSION_TITAN, player), True_())
    if world.options.challenge_mode.value >= 2:
        world.set_rule(mw.get_location(Rac5Locations.POKITARU_CHAMELEON_BOOTS, player), True_())
