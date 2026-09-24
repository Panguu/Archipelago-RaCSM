"""LittleBigPlanet level checks, optional sticker requirements and key checks."""
from typing import ClassVar
from BaseClasses import Item, ItemClassification, Region
from worlds.AutoWorld import World, WebWorld
from Options import OptionGroup
from .Options import Goal, LBPOptions, LEVEL_BY_LABEL, LEVEL_LABELS, DLCLevelPacks, DLCItemPacks, DLCCostumes, TrapPercentage, GoodTraps, BadTraps
from .chapters import CHAPTER_FINALE, CHAPTER_LEVELS, DLC_PACKS, LEVEL_CHAPTER, STORY_CHAPTERS
from .items import ITEM_ID_TO_DATA, ITEM_NAME_TO_ID, ITEM_NAME_GROUPS, LEVEL_GUID_TO_ITEM_ID, PRIZE_PLAN_TO_ITEM_ID
from .locations import LEVELS, LOCATIONS, LOCATION_NAME_TO_ID
from .location import LBPLocation
from .settings import LBPSettings
from .dlc import DLC_KITS, DLC_UNLOCK_NAMES, LEVEL_DLC, ADDON_PACKS, addon_for_item
from .content_packs import PACKS, PACK_BY_NAME, PACK_LOCATIONS, UNLOCK_NAMES
from .interactions import INTERACTION_LOCATIONS, INTERACTION_NAME_TO_ID, required_sticker_plans
from .rules import LOCATION_RULES

FILLER_NAME = 'Nothing'
FILLER_ID = 1_249_999_999
# Separate project-local range from item ids in items.py; coordinate before upstream registration.
PROGRESSIVE_ITEM_ID = {chapter: 1_249_900_000 + i for i, chapter in enumerate(STORY_CHAPTERS)}


def launch_client(*args):
    from worlds.LauncherComponents import launch_subprocess
    from .Client import launch
    launch_subprocess(launch, name='LittleBigPlanet Client', args=args)


from worlds.LauncherComponents import Component, components
components.append(Component('LittleBigPlanet Client', func=launch_client, game_name='LittleBigPlanet',
                            supports_uri=True, description='RPCS3 PINE client (experimental)'))


class _RuleInventory:
    """Probe the positive has() requirements used by this world's location rules."""
    def __init__(self):
        self.required_items = set()

    def has(self, name, player, count=1):
        self.required_items.add(name)
        return True

    def has_all(self, names, player):
        self.required_items.update(names)
        return True


class LBPItem(Item):
    game = 'LittleBigPlanet'


class LBPWebWorld(WebWorld):
    option_groups = [OptionGroup('DLC Packs', [DLCLevelPacks, DLCItemPacks, DLCCostumes]),
                     OptionGroup('Traps', [TrapPercentage, GoodTraps, BadTraps])]


class LittleBigPlanetWorld(World):
    """Checks require their level; Sticker Sanity also requires the named sticker."""
    game = 'LittleBigPlanet'
    web = LBPWebWorld()
    options_dataclass = LBPOptions
    settings: ClassVar[LBPSettings]
    item_name_to_id = dict(ITEM_NAME_TO_ID, **{FILLER_NAME: FILLER_ID},
                           **{f'Progressive {c}': i for c, i in PROGRESSIVE_ITEM_ID.items()})
    location_name_to_id = dict(LOCATION_NAME_TO_ID, **INTERACTION_NAME_TO_ID,
                               **{p['name']:p['id'] for p in PACK_LOCATIONS.values()})
    location_name_groups = {name:{loc['name'] for loc in LOCATIONS.values()
                                  if LEVEL_DLC.get(loc['level_guid']) == key}
                            for key,(name,_,_) in DLC_KITS.items()}
    location_name_groups['DLC Costumes'] = {loc['name'] for loc in PACK_LOCATIONS.values()}
    location_name_groups['Sticker Switches'] = {loc['name'] for loc in INTERACTION_LOCATIONS.values() if loc['kind']=='sticker_switch'}
    location_name_groups['Keys'] = {loc['name'] for loc in INTERACTION_LOCATIONS.values() if loc['kind']=='key'}
    item_name_groups = dict(ITEM_NAME_GROUPS,
                            **{'Progressive Levels': tuple(f'Progressive {c}' for c in PROGRESSIVE_ITEM_ID)})

    def _rule_permits(self, location_key):
        """Evaluate positive item requirements as satisfied to expose co-op gates.

        Rules use has() and player-count checks. Real inventory requirements still
        apply at fill time; this only removes checks impossible for these options.
        """
        rule = LOCATION_RULES.get(location_key)
        return rule is None or rule(self, _RuleInventory())

    def generate_early(self):
        self.costume_packs = {PACK_BY_NAME[name] for name in self.options.dlc_costumes.value}
        dlc = set(self.options.dlc_level_packs.value)
        self.addons = {key for key,name in ADDON_PACKS.items() if name in self.options.dlc_item_packs.value}
        universe = {guid for guid, chapter in LEVEL_CHAPTER.items()
                    if chapter in STORY_CHAPTERS or chapter == 'Introduction' or chapter in dlc}
        excluded = {LEVEL_BY_LABEL[name] for name in self.options.excluded_levels.value}
        self.levels = sorted(universe - excluded)
        if not self.levels:
            raise ValueError('No levels enabled; check Excluded Levels and DLC Level Packs')
        self.level_kits = {g:LEVEL_DLC[g] for g in self.levels if g in LEVEL_DLC}
        self.enabled_kits = set(self.level_kits.values())

        # Universal Tracker replays generation with a different RNG stream, so a
        # random starting level would drift from the server's actual choice; on
        # its regen pass it hands back the real slot data via interpret_slot_data.
        passthrough = (getattr(self.multiworld, 're_gen_passthrough', None) or {}).get(self.game)
        if passthrough:
            self.start = passthrough['starting_level']
        else:
            self.start = (self.random.choice(self.levels) if self.options.starting_level.value == 0
                          else f'g{self.options.starting_level.value}')
        if self.start not in self.levels:
            raise ValueError(f'starting level {self.start!r} must be included')

        # Progressive Chapters: chapters with more than one enabled level collapse their
        # individual "Unlock <level>" items into one counted "Progressive <chapter>" item,
        # unlocked in the game's own story order (see chapters.py). chapter_of maps each
        # such level back to its chapter for create_regions/create_items to consult.
        self.progressive = {}
        if self.options.progressive_chapters.value:
            for chapter in STORY_CHAPTERS:
                members = [g for g in CHAPTER_LEVELS[chapter] if g in self.levels]
                if len(members) > 1:
                    self.progressive[chapter] = members
        self.chapter_of = {guid: chapter for chapter, members in self.progressive.items() for guid in members}

        self.goal = self.options.goal.value
        self.goal_level = f'g{self.options.goal_level.value}'
        if self.goal == Goal.option_all_levels:
            self.goal_guids = set(self.levels)
        elif self.goal == Goal.option_chapter_completion:
            chapters_in_play = {LEVEL_CHAPTER[g] for g in self.levels}
            self.goal_guids = {CHAPTER_FINALE[c] for c in chapters_in_play if CHAPTER_FINALE[c] in self.levels}
        else:
            if self.goal_level not in self.levels:
                raise ValueError(f'Goal level {LEVEL_LABELS[self.goal_level]!r} is excluded or its DLC level pack is disabled')
            self.goal_guids = {self.goal_level}
        if not self.goal_guids:
            raise ValueError('Goal requires at least one reachable finale level; '
                             'check Excluded Levels and DLC Level Packs')

        # Individual pickup detection is still experimental; the host must opt in via
        # host.yaml regardless of what a player's own YAML requests.
        score_bubbles = bool(self.options.score_bubbles) and bool(self.settings.score_bubble_sanity)
        self.enabled = [loc for loc in LOCATIONS.values() if loc['level_guid'] in self.levels
                        and (score_bubbles or loc['kind'] != 'score')]
        self.enabled += [PACK_LOCATIONS[slot] for slot in sorted(self.costume_packs)]
        interaction_kinds = set()
        if self.options.sticker_sanity: interaction_kinds.add('sticker_switch')
        if self.options.key_sanity: interaction_kinds.add('key')
        self.enabled += [loc for loc in INTERACTION_LOCATIONS.values()
                         if loc['level_guid'] in self.levels and loc['kind'] in interaction_kinds]
        # A location with a rule that can never be satisfied under this player's own
        # options (e.g. a co-op section with too few Players) isn't offered as a check
        # at all, the same way an excluded level's locations aren't -- never included
        # as an always-present-but-sometimes-unreachable check.
        self.enabled = [loc for loc in self.enabled if self._rule_permits(loc['key'])]
        self.required_stickers = required_sticker_plans(self.enabled)
        inventory = _RuleInventory()
        for loc in self.enabled:
            rule = LOCATION_RULES.get(loc['key'])
            if rule:
                rule(self, inventory)
        self.required_stickers.update(
            ITEM_ID_TO_DATA[ITEM_NAME_TO_ID[name]]['state']['plan_guid']
            for name in inventory.required_items)


    def interpret_slot_data(self, slot_data):
        # Only the starting level is randomized outside of items; everything else
        # UT needs is already deterministic from the (required) YAML options.
        if self.options.starting_level.value == 0:
            return slot_data
        return None

    def create_regions(self):
        menu = Region('Menu', self.player, self.multiworld)
        self.multiworld.regions.append(menu)
        regions = {}
        for guid in self.levels:
            region = Region(f'{LEVELS[guid]["name"]} [{guid}]', self.player, self.multiworld)
            region.locations = [LBPLocation.create(self, loc, region)
                                for loc in self.enabled if loc.get('level_guid') == guid]
            for loc in self.enabled:
                if loc.get('level_guid') == guid and loc['kind']=='sticker_switch':
                    plan = int(loc['sticker_plan'][1:])
                    name = ITEM_ID_TO_DATA[PRIZE_PLAN_TO_ITEM_ID[plan]]['name']
                    location = next(l for l in region.locations if l.address==loc['id'])
                    previous_rule = location.access_rule
                    location.access_rule = lambda state, name=name, base=previous_rule: base(state) and state.has(name, self.player)
            self.multiworld.regions.append(region)
            regions[guid] = region
            chapter = self.chapter_of.get(guid)
            if chapter:
                count = self.progressive[chapter].index(guid) + 1
                item_name = f'Progressive {chapter}'
                rule = lambda state, name=item_name, count=count: state.has(name, self.player, count)
            else:
                unlock = ITEM_ID_TO_DATA[LEVEL_GUID_TO_ITEM_ID[guid]]['name']
                rule = lambda state, name=unlock: state.has(name, self.player)
            if guid in self.level_kits:
                kit_name = DLC_UNLOCK_NAMES[self.level_kits[guid]]
                level_rule = rule
                rule = lambda state, base=level_rule, kit=kit_name: base(state) and state.has(kit,self.player)
            menu.connect(region, rule=rule)
        for slot in sorted(self.costume_packs):
            region = Region(f'My Content: {PACKS[slot]["name"]}', self.player, self.multiworld)
            self.multiworld.regions.append(region)
            loc = PACK_LOCATIONS[slot]
            region.locations.append(LBPLocation(self.player, loc['name'], loc['id'], region))
            menu.connect(region, rule=lambda state, name=UNLOCK_NAMES[slot]: state.has(name,self.player))
        for guid in sorted(self.goal_guids):
            name = ('LittleBigPlanet Victory' if len(self.goal_guids) == 1
                    else f'LittleBigPlanet Victory: {LEVELS[guid]["name"]}')
            victory = LBPLocation(self.player, name, None, regions[guid])
            victory.place_locked_item(LBPItem('Victory', ItemClassification.progression, None, self.player))
            regions[guid].locations.append(victory)
        # AP reachability models beating the goal once accessible; the client requires
        # the actual goal-level completion check(s) before reporting CLIENT_GOAL.
        required = len(self.goal_guids)
        self.multiworld.completion_condition[self.player] = lambda state: state.has('Victory', self.player, required)

    def create_items(self):
        pool = [self.create_item(UNLOCK_NAMES[slot]) for slot in sorted(self.costume_packs)]
        start_kit = self.level_kits.get(self.start)
        if start_kit:
            self.multiworld.push_precollected(self.create_item(DLC_UNLOCK_NAMES[start_kit]))
        pool += [self.create_item(DLC_UNLOCK_NAMES[k]) for k in sorted(self.enabled_kits) if k != start_kit]
        start_chapter = self.chapter_of.get(self.start)
        if start_chapter:
            start_count = self.progressive[start_chapter].index(self.start) + 1
            for _ in range(start_count):
                self.multiworld.push_precollected(self.create_item(f'Progressive {start_chapter}'))
        else:
            start_name = ITEM_ID_TO_DATA[LEVEL_GUID_TO_ITEM_ID[self.start]]['name']
            self.multiworld.push_precollected(self.create_item(start_name))

        for chapter, members in self.progressive.items():
            already = start_count if chapter == start_chapter else 0
            pool += [self.create_item(f'Progressive {chapter}') for _ in range(len(members) - already)]

        pool += [self.create_item(ITEM_ID_TO_DATA[LEVEL_GUID_TO_ITEM_ID[g]]['name'])
                for g in self.levels if g not in self.chapter_of and g != self.start]

        plans = {int(loc['plan'][1:]) for loc in self.enabled
                 if (loc.get('plan') or '').startswith('g')}
        plans |= {item['state']['plan_guid'] for item in ITEM_ID_TO_DATA.values()
                  if item['state']['kind']=='inventory_plan' and addon_for_item(item) in self.addons
                  and item['category'] not in ('costume', 'costume_material')}
        # DLC costumes are collected in My Content, never granted as loose AP pieces.
        plans -= {item['state']['plan_guid'] for item in ITEM_ID_TO_DATA.values()
                  if item['state']['kind']=='inventory_plan' and addon_for_item(item)
                  and item['category'] in ('costume','costume_material')}
        plans |= self.required_stickers
        plans = sorted(plans)
        for plan in plans:
            pool.append(self.create_item(ITEM_ID_TO_DATA[PRIZE_PLAN_TO_ITEM_ID[plan]]['name']))
        if len(pool) > len(self.enabled):
            score_count = sum(loc['kind'] == 'score' for loc in self.enabled)
            details = (f'{len(pool)} items need locations, but only {len(self.enabled)} checks '
                       f'are enabled ({score_count} score bubbles across {len(self.levels)} levels). ')
            if bool(self.options.score_bubbles) and not bool(self.settings.score_bubble_sanity):
                details += ('Score Bubble Checks is enabled for this player, but the host overrides it: '
                            'set score_bubble_sanity: true under little-big-planet_options in host.yaml. ')
            else:
                details += ('Enable score checks or more levels, or select fewer DLC item packs. ')
            raise ValueError(details)
        filler_count = len(self.enabled)-len(pool)
        effects = sorted(self.options.good_traps.value | self.options.bad_traps.value)
        effect_count = filler_count * self.options.trap_percentage.value // 100 if effects else 0
        pool += [self.create_item(self.random.choice(effects)) for _ in range(effect_count)]
        pool += [self.create_item(FILLER_NAME) for _ in range(filler_count - effect_count)]
        self.multiworld.itempool.extend(pool)

    def create_item(self, name):
        code = self.item_name_to_id[name]
        category = ITEM_ID_TO_DATA.get(code, {}).get('category')
        required_sticker = ITEM_ID_TO_DATA.get(code, {}).get('state', {}).get('plan_guid') in getattr(self,'required_stickers',set())
        classification = (ItemClassification.trap if category == 'trap' else ItemClassification.progression if category in ('level','dlc') or name.startswith('Progressive ') or required_sticker
                          else ItemClassification.filler if name == FILLER_NAME else ItemClassification.useful)
        return LBPItem(name, classification, code, self.player)

    def get_filler_item_name(self):
        return FILLER_NAME

    def fill_slot_data(self):
        return {'schema': 1, 'game_id': 'NPEA00241', 'game_version': '01.27', 'supported_game_versions': ['01.27', '01.30'],
                'levels': self.levels, 'starting_level': self.start,
                'level_kits': self.level_kits, 'enabled_dlc_kits': sorted(self.enabled_kits),
                'addon_packs': sorted(self.addons),
                'costume_packs': sorted(self.costume_packs),
                'progressive_chapters': self.progressive,
                'goal_locations': sorted(LOCATIONS[f'{g}/complete']['id'] for g in self.goal_guids),
                'enabled_locations': sorted(loc['id'] for loc in self.enabled),
                'sticker_sanity': bool(self.options.sticker_sanity), 'key_sanity': bool(self.options.key_sanity),
                'death_link': bool(self.options.death_link), 'requires_reward_hook': True}
