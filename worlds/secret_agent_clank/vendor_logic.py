"""Sends the vendor locations' rules to the client in slot data, so it only shows
offers the player can logically reach, using the same rule classes as generation.

Only the rule types in RULES can be sent; a vendor rule using any other type fails
at generation.
"""
import json
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


class _RuleTable:
    def __init__(self):
        self.rules = []
        self._ids = {}

    def add(self, rule):
        if rule.rule_name not in RULES:
            raise ValueError(f"Unsupported vendor rule: {rule.rule_name}")
        args, children = {}, {}
        for field in fields(rule):
            if field.name in ("player", "caching_enabled"):
                continue
            value = getattr(rule, field.name)
            if isinstance(value, Rule.Resolved):
                children[field.name] = self.add(value)
            elif isinstance(value, tuple) and value and all(isinstance(v, Rule.Resolved) for v in value):
                children[field.name] = [self.add(v) for v in value]
            else:
                args[field.name] = _lists(value)
        node = [rule.rule_name, args, children]
        key = json.dumps(node, sort_keys=True)
        if key not in self._ids:
            self._ids[key] = len(self.rules)
            self.rules.append(node)
        return self._ids[key]


def _lists(value):
    return [_lists(item) for item in value] if isinstance(value, tuple) else value


def _tuples(value):
    return tuple(_tuples(item) for item in value) if isinstance(value, list) else value


def _decode_rules(table):
    decoded = []
    for name, args, children in table:
        kwargs = {key: _tuples(value) for key, value in args.items()}
        for key, ref in children.items():
            kwargs[key] = tuple(decoded[i] for i in ref) if isinstance(ref, list) else decoded[ref]
        decoded.append(RULES[name](**kwargs, player=1, caching_enabled=False))
    return decoded


def export_vendor_rules(world):
    """Export the actual location rules and the region graph they depend on."""
    locations = {loc.name: loc for loc in world.multiworld.get_locations(world.player)
                 if loc.name in VENDOR_CASES}
    table = _RuleTable()
    regions = {}

    def include_region(name):
        if name in regions or name == "Menu":
            return
        regions[name] = []
        region = world.multiworld.get_region(name, world.player)
        for entrance in region.entrances:
            rule = entrance.access_rule
            regions[name].append([entrance.parent_region.name, table.add(rule)])
            include_region(entrance.parent_region.name)
            for dependency in rule.region_dependencies():
                include_region(dependency)

    for loc in locations.values():
        include_region(loc.parent_region.name)
        for dependency in loc.access_rule.region_dependencies():
            include_region(dependency)
    exported = {name: [loc.parent_region.name, table.add(loc.access_rule)] for name, loc in locations.items()}
    return {"version": 2, "rules": table.rules, "regions": regions, "locations": exported}


class VendorLogic:
    def __init__(self, data):
        if data["version"] != 2:
            raise ValueError("Unsupported vendor logic version")
        rules = _decode_rules(data["rules"])
        self.regions = {name: [(parent, rules[rule]) for parent, rule in entrances]
                        for name, entrances in data["regions"].items()}
        self.locations = {name: (parent, rules[rule]) for name, (parent, rule) in data["locations"].items()}

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
