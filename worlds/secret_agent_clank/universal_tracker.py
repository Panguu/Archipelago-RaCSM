"""Universal Tracker support: restore options from slot_data when UT regenerates the world without a YAML."""
from typing import TYPE_CHECKING, Any

from .options import Goal, ProgressiveWeapons, SkillPoints

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

    # Options that decide which regions and locations exist.
    world.options.infobots.value = passthrough["infobots"]
    world.options.operatives.value = dict(passthrough["operatives"])
    world.options.all_missions.value = passthrough["all_missions"]
    world.options.all_cutscenes.value = bool(passthrough["all_cutscenes"])
    tier = passthrough["skill_points"]
    if passthrough.get("skill_point_tiers_version", 1) < 2 and type(tier) is int and tier == 2:
        tier = "hard"  # Older seeds used 2 for all skill points.
    world.options.skill_points.value = SkillPoints.from_any(tier).value
    world.options.random_skill_points.value = int(passthrough.get("random_skill_points", False))
    world.options.skill_point_count.value = passthrough.get("skill_point_count", 5)
    combined = passthrough.get("keycards_and_alien_codes")
    legacy = (bool(passthrough.get("all_keycards", combined)),
              bool(passthrough.get("all_alien_codes", combined)))
    world.options.keycards_and_alien_codes.value = int(any(legacy) if combined is None else combined)
    # Older seeds may have enabled just one category; preserve their exact checks.
    world.options._legacy_collectible_checks = legacy
    world.options.goal.value = (Goal.option_pick_and_mix if passthrough.get("pick_and_mix", False)
                                else passthrough["goal"])
    world.options.pick_and_mix_goals.value = set(passthrough.get("pick_and_mix_goals", ()))

    # Options that shape the item pool.
    world.options.keycard_hunt.value = bool(passthrough.get("keycard_hunt", False))
    world.options.progressive_wrench.value = bool(passthrough.get("progressive_wrench", False))
    world.options.ng_plus.value = passthrough["ng_plus"]
    world.options.progressive_challenge_mode.value = bool(passthrough.get("progressive_challenge_mode", False))
    world.options.progressive_weapons.value = ProgressiveWeapons.from_any(passthrough["progressive_weapons"]).value
    world.options.weapon_level_checks.value = passthrough.get("weapon_level_checks", 0)
    world.options.nanotech_checks.value = passthrough.get("nanotech_checks", False)
    world.options.ratchet_nanotech_checks.value = passthrough.get("ratchet_nanotech_checks", False)
    world.options.stealth_takedown_checks.value = passthrough.get("stealth_takedown_checks", 0)
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

    # Gameplay-only options, restored so the regenerated slot_data matches.
    world.options.death_link.value = bool(passthrough["death_link"])
    world.options.weapon_xp_multiplier.value = passthrough["weapon_xp_multiplier"]
    world.options.health_xp_multiplier.value = passthrough["health_xp_multiplier"]
    world.options.bolt_multiplier.value = passthrough["bolt_multiplier"]
