import gzip
import json
import unittest
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from pathlib import Path

from BaseClasses import MultiWorld
from rule_builder.rules import True_

from ..core.locations import (
    armour_set_locations,
    challenge_locations,
    mission_locations,
    skill_point_locations,
    titanium_bolt_locations,
)
from ..items import ALL_ITEMS
from ..locations import ALL_LOCATIONS, BASE_ID
from ..options import RACSizeMatterOptions
from ..regions import create_regions
from ..rules import set_rules
from ..world import RACSizeMatterWorld


def canonical(value):
    if isinstance(value, dict):
        return {key: canonical(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return sorted((canonical(child) for child in value), key=lambda child: json.dumps(child, sort_keys=True))
    return value


class TestRefactorParity(unittest.TestCase):
    def test_completion_tables_and_reporting_order(self):
        def normalize(value):
            if isinstance(value, Mapping):
                return sorted(
                    [[normalize(key), normalize(child)] for key, child in value.items()], key=lambda pair: repr(pair[0])
                )
            if hasattr(value, "planet_ids"):
                return [list(value.planet_ids), value.bit, value.region]
            if is_dataclass(value):
                return normalize(asdict(value))
            if isinstance(value, (list, tuple)):
                return [normalize(child) for child in value]
            if isinstance(value, (set, frozenset)):
                return sorted(normalize(child) for child in value)
            return value

        baseline = json.loads((Path(__file__).parent / "fixtures/completion_tables.json").read_text())
        modules = (
            armour_set_locations,
            challenge_locations,
            mission_locations,
            skill_point_locations,
            titanium_bolt_locations,
        )
        for name, expected in baseline.items():
            field = name.removesuffix("_order")
            module = next(module for module in modules if hasattr(module, field))
            value = getattr(module, field)
            if name.endswith("_order"):
                value = list(value)
            self.assertEqual(expected, normalize(value), name)

    def test_ids_and_classifications(self):
        baseline = json.loads((Path(__file__).parent / "fixtures/refactor_ids.json").read_text())
        self.assertEqual(
            {name: data[1] for name, data in baseline["locations"].items()},
            {name: data.region for name, data in ALL_LOCATIONS.items()},
        )
        self.assertEqual(
            baseline["items"], {name: [data.code, int(data.classification)] for name, data in ALL_ITEMS.items()}
        )

    def test_generated_location_ids_are_unique_and_sequential(self):
        self.assertEqual(
            sorted(location.code for location in ALL_LOCATIONS.values()),
            list(range(BASE_ID + 1, BASE_ID + len(ALL_LOCATIONS) + 1)),
        )

    def test_option_and_rule_parity(self):
        path = Path(__file__).parent / "fixtures/refactor_logic.json.gz"
        scenarios = json.loads(gzip.decompress(path.read_bytes()))
        for scenario in scenarios:
            with self.subTest(options=scenario["options"]):
                multiworld = MultiWorld(1)
                multiworld.set_seed(1)
                world = RACSizeMatterWorld(multiworld, 1)
                world.options = RACSizeMatterOptions(
                    **{
                        name: option.from_any(scenario["options"].get(name, option.default))
                        for name, option in RACSizeMatterOptions.type_hints.items()
                    }
                )
                create_regions(world)
                self.assertEqual(
                    scenario["location_order"], [location.name for location in multiworld.get_locations(1)]
                )
                recorded = {}
                world.set_rule = lambda spot, rule: recorded.__setitem__(spot.name, rule.to_dict())
                set_rules(world)
                truth = True_().to_dict()
                actual = {
                    location.name: [location.address, location.parent_region.name, recorded.get(location.name, truth)]
                    for location in multiworld.get_locations(1)
                }
                expected = {
                    name: [ALL_LOCATIONS[name].code if name in ALL_LOCATIONS else None, *data[1:]]
                    for name, data in scenario["locations"].items()
                }
                self.assertEqual(canonical(expected), canonical(actual))
                entrances = {
                    entrance.name: recorded.get(entrance.name, truth)
                    for region in multiworld.regions
                    for entrance in region.exits
                }
                self.assertEqual(canonical(scenario["entrances"]), canonical(entrances))
