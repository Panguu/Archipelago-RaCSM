from typing import ClassVar

from BaseClasses import ItemClassification
from Options import OptionGroup
from rule_builder.rules import Has
from worlds.AutoWorld import WebWorld, World

from .chapters import CHAPTER_FINALE, CHAPTER_LEVELS, LEVEL_CHAPTER, STORY_CHAPTERS
from .content_packs import PACK_BY_NAME, PACK_LOCATIONS, UNLOCK_NAMES
from .dlc import ADDON_PACKS, DLC_KITS, DLC_UNLOCK_NAMES, LEVEL_DLC, addon_for_item
from .items import (FILLER_ID, FILLER_NAME, ITEM_ID_TO_DATA, ITEM_NAME_GROUPS, ITEM_NAME_TO_ID,
                    LEVEL_GUID_TO_ITEM_ID, PRIZE_PLAN_TO_ITEM_ID, LBPItem)
from .locations import LOCATIONS, LOCATION_NAME_TO_ID, LOCATIONS_BY_LEVEL, Kind
from .Options import (BadTraps, DLCCostumes, DLCItemPacks, DLCLevelPacks, Goal, GoodTraps, LBPOptions,
                      LEVEL_BY_LABEL, LEVEL_LABELS, TrapPercentage)
from .regions import create_regions
from .rules import rule_items, set_rules
from .settings import LBPSettings

ALWAYS_ON = {Kind.PRIZE, Kind.COMPLETE, Kind.ACE, Kind.ALL_PRIZES, Kind.REWARD}


class LBPWebWorld(WebWorld):
    option_groups = [OptionGroup('DLC Packs', [DLCLevelPacks, DLCItemPacks, DLCCostumes]),
                     OptionGroup('Traps', [TrapPercentage, GoodTraps, BadTraps])]


def _location_groups():
    groups = {name: {loc.name for loc in LOCATIONS if LEVEL_DLC.get(loc.level) == kit}
              for kit, (name, _, _) in DLC_KITS.items()}
    groups['DLC Costumes'] = {pack['name'] for pack in PACK_LOCATIONS.values()}
    groups['Sticker Switches'] = {loc.name for loc in LOCATIONS if loc.kind == Kind.STICKER_SWITCH}
    groups['Keys'] = {loc.name for loc in LOCATIONS if loc.kind == Kind.KEY}
    return groups


class LittleBigPlanetWorld(World):
    """Collect score and prize bubbles, keys and sticker switches across LittleBigPlanet's levels."""
    game = 'LittleBigPlanet'
    web = LBPWebWorld()
    options_dataclass = LBPOptions
    options: LBPOptions
    settings: ClassVar[LBPSettings]
    settings_key = 'little-big-planet_options'
    item_name_to_id = {**ITEM_NAME_TO_ID, FILLER_NAME: FILLER_ID}
    location_name_to_id = {**LOCATION_NAME_TO_ID, **{pack['name']: pack['id'] for pack in PACK_LOCATIONS.values()}}
    item_name_groups = ITEM_NAME_GROUPS
    location_name_groups = _location_groups()

    def generate_early(self):
        options = self.options
        self.costume_packs = {PACK_BY_NAME[name] for name in options.dlc_costumes.value}
        self.addons = {key for key, name in ADDON_PACKS.items() if name in options.dlc_item_packs.value}
        dlc = set(options.dlc_level_packs.value)
        available = {guid for guid, chapter in LEVEL_CHAPTER.items()
                     if chapter in STORY_CHAPTERS or chapter == 'Introduction' or chapter in dlc}
        self.levels = sorted(available - {LEVEL_BY_LABEL[name] for name in options.excluded_levels.value})
        if not self.levels:
            raise ValueError('No levels enabled; check Excluded Levels and DLC Level Packs')
        self.level_kits = {guid: LEVEL_DLC[guid] for guid in self.levels if guid in LEVEL_DLC}
        self.enabled_kits = set(self.level_kits.values())

        # Universal Tracker regenerates with a different RNG, so it passes the real starting level back.
        passthrough = (getattr(self.multiworld, 're_gen_passthrough', None) or {}).get(self.game)
        if passthrough:
            self.start = passthrough['starting_level']
        elif options.starting_level.value == 0:
            self.start = self.random.choice(self.levels)
        else:
            self.start = f'g{options.starting_level.value}'
        if self.start not in self.levels:
            raise ValueError(f'Starting level {self.start!r} must be included')

        self.progressive = {}
        if options.progressive_curators:
            for chapter in STORY_CHAPTERS:
                members = [guid for guid in CHAPTER_LEVELS[chapter] if guid in self.levels]
                if len(members) > 1:
                    self.progressive[chapter] = members
        self.chapter_of = {guid: chapter for chapter, members in self.progressive.items() for guid in members}

        self.goal_level = f'g{options.goal_level.value}'
        if options.goal == Goal.option_all_levels:
            self.goal_guids = set(self.levels)
        elif options.goal == Goal.option_chapter_completion:
            chapters = {LEVEL_CHAPTER[guid] for guid in self.levels}
            self.goal_guids = {CHAPTER_FINALE[c] for c in chapters if CHAPTER_FINALE[c] in self.levels}
        else:
            if self.goal_level not in self.levels:
                raise ValueError(f'Goal level {LEVEL_LABELS[self.goal_level]!r} is excluded '
                                 'or its DLC level pack is disabled')
            self.goal_guids = {self.goal_level}
        if not self.goal_guids:
            raise ValueError('Goal requires at least one reachable finale level; '
                             'check Excluded Levels and DLC Level Packs')

        kinds = set(ALWAYS_ON)
        # Score pickup detection is experimental, so the host must also opt in through host.yaml.
        if options.score_bubbles and self.settings.score_bubble_sanity:
            kinds.add(Kind.SCORE)
        if options.sticker_sanity:
            kinds.add(Kind.STICKER_SWITCH)
        if options.key_sanity:
            kinds.add(Kind.KEY)
        self.enabled = [loc for guid in self.levels for loc in LOCATIONS_BY_LEVEL[guid]
                        if loc.kind in kinds and loc.players <= options.players.value]
        self.required_plans = {int(loc.plan[1:]) for loc in self.enabled if loc.kind == Kind.STICKER_SWITCH}
        for loc in self.enabled:
            for name in rule_items(loc.rule):
                self.required_plans.add(ITEM_ID_TO_DATA[ITEM_NAME_TO_ID[name]]['state']['plan_guid'])

    def interpret_slot_data(self, slot_data):
        return slot_data if self.options.starting_level.value == 0 else None

    def level_rule(self, guid):
        chapter = self.chapter_of.get(guid)
        if chapter:
            rule = Has(f'Progressive {chapter}', self.progressive[chapter].index(guid) + 1)
        else:
            rule = Has(ITEM_ID_TO_DATA[LEVEL_GUID_TO_ITEM_ID[guid]]['name'])
        if guid in self.level_kits:
            rule = rule & Has(DLC_UNLOCK_NAMES[self.level_kits[guid]])
        return rule

    def plan_item_name(self, plan):
        return ITEM_ID_TO_DATA[PRIZE_PLAN_TO_ITEM_ID[int(plan[1:])]]['name']

    def create_regions(self):
        create_regions(self)

    def set_rules(self):
        set_rules(self)

    def create_items(self):
        pool = [self.create_item(UNLOCK_NAMES[slot]) for slot in sorted(self.costume_packs)]
        start_kit = self.level_kits.get(self.start)
        if start_kit:
            self.push_precollected(self.create_item(DLC_UNLOCK_NAMES[start_kit]))
        pool += [self.create_item(DLC_UNLOCK_NAMES[kit]) for kit in sorted(self.enabled_kits) if kit != start_kit]

        start_chapter = self.chapter_of.get(self.start)
        start_count = self.progressive[start_chapter].index(self.start) + 1 if start_chapter else 0
        if start_chapter:
            for _ in range(start_count):
                self.push_precollected(self.create_item(f'Progressive {start_chapter}'))
        else:
            self.push_precollected(self.create_item(ITEM_ID_TO_DATA[LEVEL_GUID_TO_ITEM_ID[self.start]]['name']))
        for chapter, members in self.progressive.items():
            already = start_count if chapter == start_chapter else 0
            pool += [self.create_item(f'Progressive {chapter}') for _ in range(len(members) - already)]
        pool += [self.create_item(ITEM_ID_TO_DATA[LEVEL_GUID_TO_ITEM_ID[guid]]['name'])
                 for guid in self.levels if guid not in self.chapter_of and guid != self.start]

        plans = {int(loc.plan[1:]) for loc in self.enabled
                 if loc.kind in (Kind.PRIZE, Kind.REWARD) and (loc.plan or '').startswith('g')}
        for item in ITEM_ID_TO_DATA.values():
            if item['state']['kind'] != 'inventory_plan' or not addon_for_item(item):
                continue
            # DLC costumes are collected in My Content, never granted as loose pieces.
            if item['category'] in ('costume', 'costume_material'):
                plans.discard(item['state']['plan_guid'])
            elif addon_for_item(item) in self.addons:
                plans.add(item['state']['plan_guid'])
        plans |= self.required_plans
        pool += [self.create_item(ITEM_ID_TO_DATA[PRIZE_PLAN_TO_ITEM_ID[plan]]['name']) for plan in sorted(plans)]

        checks = len(self.enabled) + len(self.costume_packs)
        if len(pool) > checks:
            scores = sum(loc.kind == Kind.SCORE for loc in self.enabled)
            details = (f'{len(pool)} items need locations, but only {checks} checks are enabled '
                       f'({scores} score bubbles across {len(self.levels)} levels). ')
            if self.options.score_bubbles and not self.settings.score_bubble_sanity:
                details += ('Score Bubble Checks is enabled for this player, but the host overrides it: '
                            'set score_bubble_sanity: true under little-big-planet_options in host.yaml.')
            else:
                details += 'Enable score checks or more levels, or select fewer DLC item packs.'
            raise ValueError(details)

        filler = checks - len(pool)
        effects = sorted(self.options.good_traps.value | self.options.bad_traps.value)
        effect_count = filler * self.options.trap_percentage.value // 100 if effects else 0
        pool += [self.create_item(self.random.choice(effects)) for _ in range(effect_count)]
        pool += [self.create_item(FILLER_NAME) for _ in range(filler - effect_count)]
        self.multiworld.itempool += pool

    def create_item(self, name):
        code = self.item_name_to_id[name]
        data = ITEM_ID_TO_DATA.get(code, {})
        category = data.get('category')
        if category == 'trap':
            classification = ItemClassification.trap
        elif (category in ('level', 'dlc') or name.startswith('Progressive ')
              or data.get('state', {}).get('plan_guid') in getattr(self, 'required_plans', ())):
            classification = ItemClassification.progression
        elif name == FILLER_NAME:
            classification = ItemClassification.filler
        else:
            classification = ItemClassification.useful
        return LBPItem(name, classification, code, self.player)

    def get_filler_item_name(self):
        return FILLER_NAME

    def fill_slot_data(self):
        goal_locations = [loc.code for guid in self.goal_guids for loc in LOCATIONS_BY_LEVEL[guid]
                          if loc.kind == Kind.COMPLETE]
        enabled = [loc.code for loc in self.enabled] + [PACK_LOCATIONS[slot]['id'] for slot in self.costume_packs]
        return {'schema': 1, 'game_id': 'NPEA00241', 'game_version': '01.27',
                'supported_game_versions': ['01.27', '01.30'],
                'levels': self.levels, 'starting_level': self.start,
                'level_kits': self.level_kits, 'enabled_dlc_kits': sorted(self.enabled_kits),
                'addon_packs': sorted(self.addons),
                'costume_packs': sorted(self.costume_packs),
                'progressive_chapters': self.progressive,
                'goal_locations': sorted(goal_locations),
                'enabled_locations': sorted(enabled),
                'sticker_sanity': bool(self.options.sticker_sanity),
                'key_sanity': bool(self.options.key_sanity),
                'death_link': bool(self.options.death_link), 'requires_reward_hook': True}
