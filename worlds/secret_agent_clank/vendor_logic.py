"""Sends the vendor locations' rules to the client in slot data, so it only shows
offers the player can logically reach, using the same rule classes as generation.

Only the rule types in RULES can be sent; a vendor rule using any other type fails
at generation.
"""
from collections import Counter
from dataclasses import fields

from rule_builder.rules import (
    And, Or, Has, HasAll, HasAny, HasAllCounts, HasAnyCount,
    HasFromList, HasFromListUnique, True_, False_, CanReachRegion, Rule,
)

from .constants import PROGRESSIVE_TO_UNLOCK, VENDOR_CASES
from .rules.rule_helpers import AtLeast


RULES = {cls.Resolved.rule_name: cls.Resolved for cls in (
    And, Or, Has, HasAll, HasAny, HasAllCounts, HasAnyCount,
    HasFromList, HasFromListUnique, True_, False_, CanReachRegion, AtLeast,
)}


def logical_inventory(names):
    counts = Counter(names)
    for progressive, base in PROGRESSIVE_TO_UNLOCK.items():
        counts[base] += counts[progressive]
    return counts


def _encode(value):
    if isinstance(value, Rule.Resolved):
        if value.rule_name not in RULES:
            raise ValueError(f"Unsupported vendor rule: {value.rule_name}")
        return {"rule": value.rule_name, "args": {
            field.name: _encode(getattr(value, field.name)) for field in fields(value)
            if field.name not in ("player", "caching_enabled")}}
    if isinstance(value, tuple):
        return [_encode(child) for child in value]
    return value


def _decode(value):
    if isinstance(value, dict):
        cls = RULES[value["rule"]]
        return cls(**{name: _decode(arg) for name, arg in value["args"].items()},
                   player=1, caching_enabled=False)
    if isinstance(value, list):
        return tuple(_decode(child) for child in value)
    return value


def export_vendor_rules(world):
    """Export the actual location rules and the region graph they depend on."""
    locations = {loc.name: loc for loc in world.multiworld.get_locations(world.player)
                 if loc.name in VENDOR_CASES}
    regions = {}

    def include_region(name):
        if name in regions or name == "Menu":
            return
        regions[name] = []
        region = world.multiworld.get_region(name, world.player)
        for entrance in region.entrances:
            rule = entrance.access_rule
            regions[name].append([entrance.parent_region.name, _encode(rule)])
            include_region(entrance.parent_region.name)
            for dependency in rule.region_dependencies():
                include_region(dependency)

    for loc in locations.values():
        include_region(loc.parent_region.name)
        for dependency in loc.access_rule.region_dependencies():
            include_region(dependency)
    return {"version": 1, "regions": regions, "locations": {
        name: [loc.parent_region.name, _encode(loc.access_rule)] for name, loc in locations.items()}}


class VendorLogic:
    def __init__(self, data):
        if data["version"] != 1:
            raise ValueError("Unsupported vendor logic version")
        self.regions = {name: [(parent, _decode(rule)) for parent, rule in entrances]
                        for name, entrances in data["regions"].items()}
        self.locations = {name: (parent, _decode(rule))
                          for name, (parent, rule) in data["locations"].items()}

    def available(self, received_names):
        state = _VendorState(received_names)
        # Fixed point also handles region dependencies without recursive cycles.
        while True:
            reached = {name for name, entrances in self.regions.items()
                       if name not in state.reached and any(
                           parent in state.reached and rule(state) for parent, rule in entrances)}
            if not reached:
                break
            state.reached.update(reached)
        return frozenset(name for name, (parent, rule) in self.locations.items()
                         if parent in state.reached and rule(state))


class _VendorState:
    def __init__(self, names):
        self.prog_items = {1: logical_inventory(names)}
        self.reached = {"Menu"}

    def can_reach_region(self, name, player):
        return name in self.reached
