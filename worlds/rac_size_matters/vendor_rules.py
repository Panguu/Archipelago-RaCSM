"""Seed-specific vendor access rules shared by generation and the client.

The wire format contains only resolved item predicates, never executable code.
Unsupported rules fail generation instead of silently weakening vendor gates.
"""
from collections.abc import Mapping

from rule_builder.rules import And, Or, Has, HasAll, HasAny, HasAllCounts, HasAnyCount, Rule

from .locations import LOCATIONS, MENU_REGION

VENDOR_CATEGORIES = frozenset({
    "weapon_vendor", "gadget_vendor", "weapon_titan_vendor", "weapon_mod_vendor",
})


def encode_rule(rule):
    if not isinstance(rule, Rule.Resolved):
        raise TypeError(f"Vendor access requires a rule-builder rule, got {rule!r}")
    if rule.always_true:
        return ["true"]
    if rule.always_false:
        return ["false"]
    if type(rule) in (And.Resolved, Or.Resolved):
        return ["all" if type(rule) is And.Resolved else "any",
                [encode_rule(child) for child in rule.children]]
    if type(rule) is Has.Resolved:
        return ["has", rule.item_name, rule.count]
    if type(rule) in (HasAll.Resolved, HasAny.Resolved):
        return ["all" if type(rule) is HasAll.Resolved else "any",
                [["has", name, 1] for name in rule.item_names]]
    if type(rule) in (HasAllCounts.Resolved, HasAnyCount.Resolved):
        return ["all" if type(rule) is HasAllCounts.Resolved else "any",
                [["has", name, count] for name, count in rule.item_counts]]
    raise TypeError(f"Unsupported vendor access rule: {type(rule).__qualname__}")


def evaluate_rule(rule, items: Mapping[str, int]) -> bool:
    op = rule[0]
    if op == "true":
        return True
    if op == "false":
        return False
    if op == "has":
        return items.get(rule[1], 0) >= rule[2]
    if op == "all":
        return all(evaluate_rule(child, items) for child in rule[1])
    if op == "any":
        return any(evaluate_rule(child, items) for child in rule[1])
    raise ValueError(f"Unknown vendor rule operation: {op!r}")


def build_vendor_rules(world):
    def region_rule(region, visited=frozenset()):
        if region.name == MENU_REGION:
            return ["true"]
        if region.name in visited:
            return ["false"]
        return ["any", [
            ["all", [region_rule(entrance.parent_region, visited | {region.name}),
                     encode_rule(entrance.access_rule)]]
            for entrance in region.entrances
        ]]

    rules = {}
    for definition in LOCATIONS:
        if not definition.categories & VENDOR_CATEGORIES or not definition.available(world.options):
            continue
        location = world.multiworld.get_location(definition.name, world.player)
        rules[definition.name] = ["all", [
            region_rule(location.parent_region), encode_rule(location.access_rule),
        ]]
    return {"version": 1, "locations": rules}
