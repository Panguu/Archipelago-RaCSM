"""Generate locations/<base|dlc>/<level>.py and constants/data/levels.py from data/*.json.

Run from anywhere: python tools/generate_locations.py
Hand-written `players=` and `rule=` arguments are kept when a level file is regenerated.
Location ids are assigned in file order (base levels, then DLC), so append new locations at the end.
"""
import ast
import json
import re
from pathlib import Path

WORLD = Path(__file__).resolve().parents[1]
LOCATIONS_DIR = WORLD / 'locations'
LEVELS_MODULE = WORLD / 'constants' / 'data' / 'levels.py'
KEPT_ARGUMENTS = ('players', 'rule')
RULE_NAMES = ('Has', 'HasAll', 'HasAny', 'HasAnyCount', 'And', 'Or')
KINDS = {
    'score': 'SCORE', 'prize': 'PRIZE', 'key': 'KEY', 'sticker_switch': 'STICKER_SWITCH',
    'complete': 'COMPLETE', 'ace': 'ACE', 'all_prizes': 'ALL_PRIZES', 'reward': 'REWARD',
}
LEVEL_FIELDS = ('name', 'constant', 'path', 'slots')


def load(name):
    return json.loads((WORLD / 'data' / name).read_text(encoding='utf-8'))


def group(level):
    return 'base' if '/00_developer_levels_episode_1/' in level['path'] else 'dlc'


def module_names(levels):
    names, used = {}, set()
    for level in levels:
        name = re.sub(r'\W+', '_', level['constant'].lower()).strip('_')
        if name in used:
            name = f'{name}_{level["guid"]}'
        used.add(name)
        names[level['guid']] = name
    return names


def kept_arguments(path):
    """Map location name -> {argument: source} for hand-written arguments in an existing file."""
    if not path.exists():
        return {}
    source = path.read_text(encoding='utf-8')
    kept = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'LBPLocationData':
            name = ast.literal_eval(node.args[0])
            kept[name] = {kw.arg: ast.get_source_segment(source, kw.value)
                          for kw in node.keywords if kw.arg in KEPT_ARGUMENTS}
    return kept


def record(location, kept):
    arguments = [repr(location['name']), 'LEVEL', f'Kind.{KINDS[location["kind"]]}']
    if location.get('uid') is not None:
        arguments.append(f'uid={location["uid"]}')
    plan = location.get('sticker_plan') or location.get('plan')
    if plan is not None:
        arguments.append(f'plan={plan!r}')
    if location.get('target_slot'):
        arguments.append(f'target_slot={location["target_slot"]!r}')
    if location.get('condition'):
        arguments.append(f'condition=Kind.{KINDS[location["condition"]]}')
    arguments += [f'{name}={kept[name]}' for name in KEPT_ARGUMENTS if name in kept]
    return f'    LBPLocationData({", ".join(arguments)}),'


def level_module(level, locations, kept):
    lines = [record(location, kept.get(location['name'], {})) for location in locations]
    used = sorted(name for name in RULE_NAMES if any(re.search(rf'\b{name}\(', line) for line in lines))
    header = [f'from rule_builder.rules import {", ".join(used)}', ''] if used else []
    return '\n'.join([
        *header,
        'from ..model import Kind, LBPLocationData',
        '',
        f'LEVEL = {level["guid"]!r}',
        '',
        'LOCATIONS = (',
        *lines,
        ')',
        '',
    ])


def package_module(names):
    imports = [f'from .{name} import LOCATIONS as {name.upper()}' for name in names]
    return '\n'.join([*imports, '', 'LOCATIONS = (', *(f'    *{name.upper()},' for name in names), ')', ''])


def main():
    levels = load('levels.json')['levels']
    interactions = load('interactions.json')['locations']
    names = module_names(levels)
    by_group = {'base': [], 'dlc': []}
    count = 0
    for level in levels:
        folder = LOCATIONS_DIR / group(level)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f'{names[level["guid"]]}.py'
        locations = level['locations'] + [i for i in interactions if i['level_guid'] == level['guid']]
        path.write_text(level_module(level, locations, kept_arguments(path)), encoding='utf-8')
        by_group[group(level)].append(names[level['guid']])
        count += len(locations)
    for name, modules in by_group.items():
        (LOCATIONS_DIR / name / '__init__.py').write_text(package_module(modules), encoding='utf-8')
    frozen = {level['guid']: {field: level[field] for field in LEVEL_FIELDS} for level in levels}
    LEVELS_MODULE.write_text(f'LEVELS = {frozen!r}\n', encoding='utf-8')
    print(f'{len(levels)} levels, {count} locations')


if __name__ == '__main__':
    main()
