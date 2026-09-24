"""Universal Tracker integration for Secret Agent Clank -- mirrors worlds/rac_size_matters/universal_tracker.py's pattern: UT regenerates this world from a finished multiworld's slot_data (via multiworld.re_gen_passthrough), without the player's original YAML, so its options must be restored from fill_slot_data()'s payload (world.py) rather than re-rolled."""
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .world import SecretAgentClankWorld


def setup_options_from_slot_data(world: "SecretAgentClankWorld") -> None:
    """Set options from passthrough slot data when re-generating for Universal Tracker."""
    if not hasattr(world.multiworld, "re_gen_passthrough") or world.game not in world.multiworld.re_gen_passthrough:
        world.using_ut = False
        return
    world.using_ut = True
    passthrough: dict[str, Any] = world.multiworld.re_gen_passthrough[world.game]
    world.passthrough = passthrough

    # Region/location existence -- must match exactly, or UT's regenerated
    # region graph disagrees with the real one's location IDs.
    world.options.infobots.value = passthrough["infobots"]
    world.options.operatives.value = dict(passthrough["operatives"])
    world.options.all_missions.value = passthrough["all_missions"]
    world.options.all_cutscenes.value = bool(passthrough["all_cutscenes"])
    world.options.skill_points.value = bool(passthrough["skill_points"])
    world.options.all_keycards.value = bool(passthrough["all_keycards"])
    world.options.all_alien_codes.value = bool(passthrough["all_alien_codes"])
    world.options.goal.value = passthrough["goal"]

    # Item pool composition -- affects create_items()'s pool exactly like
    # the real generation, so a re_gen'd world's item IDs/counts still match.
    world.options.ng_plus.value = passthrough["ng_plus"]
    world.options.progressive_weapons.value = bool(passthrough["progressive_weapons"])
    world.options.starting_weapons.value = passthrough["starting_weapons"]
    world.options.starting_gadgets.value = passthrough["starting_gadgets"]
    world.options.starting_bolts.value = passthrough["starting_bolts"]
    world.options.death_amnesty.value = passthrough["death_amnesty"]
    world.options.trap_chance.value = passthrough.get("trap_chance", 0)
    world.options.trap_weight.value = dict(
        passthrough.get("trap_weight", world.options.trap_weight.default)
    )
    world.options.trap_duration.value = dict(
        passthrough.get("trap_duration", world.options.trap_duration.default)
    )

    # Gameplay-only multipliers -- don't affect regions/items/logic, but
    # round-tripped anyway so a re_gen'd world's slot_data matches the real
    # one exactly (some tracker/tooling code diffs the two).
    world.options.death_link.value = bool(passthrough["death_link"])
    world.options.weapon_xp_multiplier.value = passthrough["weapon_xp_multiplier"]
    world.options.health_xp_multiplier.value = passthrough["health_xp_multiplier"]
    world.options.bolt_multiplier.value = passthrough["bolt_multiplier"]
