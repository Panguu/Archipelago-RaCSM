# Generation fuzz coverage

Run commands from the Archipelago repository root, using its Python environment.

```powershell
.venv/Scripts/python.exe fuzz.py -g rac_size_matters -r 300 -n 2-4 -j 4 -t 45
.venv/Scripts/python.exe fuzz.py -g rac_size_matters -r 200 -n 2-4 -j 4 -t 45 -m worlds/rac_size_matters/tools/fuzz/common_options.yaml
```

The common-options profile exercises item links, both kinds of starting inventory,
local/non-local items, excluded/priority locations, and a single enabled projectile
weapon. Other world options remain randomized. It requires at least two slots.

Run validation hooks separately, appending one argument to either command:

```text
--hook hooks.determinism:Hook
--hook hooks.collect_accessibility_test:Hook
--hook hooks.item_location_count:Hook
--hook hooks.check_placement_item_location_references:Hook
--hook hooks.detect_rule_variable_capture_issues:Hook
--hook hooks.indirect_conditions:Hook
--hook hooks.detect_output_placement_changes:Hook
--hook hooks.deprecated_get_options:Hook
--hook hooks.deprecated_get_settings:Hook
--hook hooks.gerpocalypse:Hook
```

Some hooks reclassify unrelated failures as ignored or successful, so do not combine
them or interpret their success totals as successful generation totals. Always run
the ordinary fuzzer as well. Keep output generation enabled when testing output
mutation. The Kingdom Hearts compatibility hook (`gerpocalypse`) requires that
world to be installed. `with_empty` additionally requires an installed Empty world;
it was unavailable in this checkout. `profile` measures performance rather than
checking correctness and requires `yappi`.

The fuzzer replaces `fuzz_output` on every invocation. Preserve its report and any
failure YAMLs/logs before starting another batch. A failing YAML can be replayed
through `--sample-from` using a directory containing the relevant player YAMLs.

Deterministic single-weapon regression cases are also available as:

```powershell
.venv/Scripts/python.exe -m unittest worlds.rac_size_matters.test.test_weapon_generation
```
