"""Read-only checks for DLC installation required by this player's slot options.

Checks NPDRM content identities in installed EDAT headers, not AP unlocks or
the shared asset catalogue. This does not decrypt files or validate licences.
"""
import json
from pathlib import Path
import re
import time

if __package__:
    from .content_packs import PACKS
    from .dlc import DLC_KITS, LEVEL_DLC, ADDON_PACKS, addon_for_item
    from .items import ITEM_ID_TO_DATA
    from .constants.data.dlc_inventory import DATA as PLAN_CONTENT
else:
    from content_packs import PACKS
    from dlc import DLC_KITS, LEVEL_DLC, ADDON_PACKS, addon_for_item
    from items import ITEM_ID_TO_DATA
    from constants.data.dlc_inventory import DATA as PLAN_CONTENT

ROOT = Path(__file__).resolve().parent
KIT_CONTENT = {
    'creator_pack': 'LBPDLCORIGCP0001', 'history_kit': 'LBPDLCORIGLK0004',
    'incredibles_kit': 'LBPDLCDSINLK0001', 'metal_gear_solid_kit': 'PLITTLEBIG000034',
    'monster_kit': 'LBPDLCORIGLK0003', 'pirates_of_the_caribbean_kit': 'LBPDLCDSPCLK0001',
    'marvel_kit': 'LBPDLCMARVLK0001',
}
# GOTY community levels are bundled in the supported digital game, not an EDAT SKU.
PLAN_OWNERS = {}
for _content, _plans in PLAN_CONTENT.items():
    for _plan in _plans:
        PLAN_OWNERS.setdefault(_plan, set()).add(_content)
# These pack assets are absent from the native inventory membership lists.
EXTRA_PLAN_OWNERS = {75761: {'LBPDLCSNYPCK0001'}, 75762: {'LBPDLCSNYPCK0001'},
                     95284: {'LBPDLCSEGACK0001'}}


class ContentOptionsError(ValueError):
    """The local installation cannot satisfy the connected slot's options."""


def requirements(slot_data):
    """Return named AND requirements; each row accepts any of its content IDs."""
    result = []
    kits = set(slot_data.get('enabled_dlc_kits', ()))
    kits.update(LEVEL_DLC[g] for g in slot_data.get('levels', ()) if g in LEVEL_DLC)
    for key in sorted(kits):
        if key not in DLC_KITS:
            raise ContentOptionsError(f'Options error: unknown DLC level pack {key!r}. Update the client.')
        if key in KIT_CONTENT:
            result.append((DLC_KITS[key][0], frozenset({KIT_CONTENT[key]})))
    for value in slot_data.get('costume_packs', ()):
        try:
            slot = int(value)
            pack = PACKS[slot]
        except (ValueError, TypeError, KeyError):
            raise ContentOptionsError(f'Options error: unknown costume pack {value!r}. Update the client.')
        ids, seen = set(), set()
        while slot in PACKS and slot not in seen:
            seen.add(slot)
            ids.add(PACKS[slot]['content_id'])
            slot = PACKS[slot]['parent_slot']
        result.append((pack['name'], frozenset(ids)))
    for key in sorted(set(slot_data.get('addon_packs', ()))):
        if key not in ADDON_PACKS:
            raise ContentOptionsError(f'Options error: unknown DLC item pack {key!r}. Update the client.')
        # Match generation: costume-only assets are not put in the item pool.
        for item in ITEM_ID_TO_DATA.values():
            if (item['state']['kind'] != 'inventory_plan' or addon_for_item(item) != key
                    or item['category'] in ('costume', 'costume_material')):
                continue
            plan = item['state']['plan_guid']
            ids = PLAN_OWNERS.get(plan) or EXTRA_PLAN_OWNERS.get(plan)
            if not ids:
                raise ContentOptionsError(f'Options error: cannot verify required DLC item pack {ADDON_PACKS[key]}. Update the client.')
            result.append((ADDON_PACKS[key], frozenset(ids)))
    return tuple(sorted(set(result), key=lambda row: (row[0], sorted(row[1]))))


def installed_content(game_directory):
    """Read only the European DLC mount used by supported NPEA00241 builds.

    US DLC installed alongside it must not accidentally satisfy the check.
    Names alone, empty files and shared assets do not establish installation.
    """
    directory = Path(game_directory)/'BCES00141DLC0'/'USRDIR'
    installed = set()
    if not directory.exists():
        return installed
    for path in directory.rglob('*'):
        if not path.is_file() or path.suffix.lower() != '.edat':
            continue
        with path.open('rb') as stream:
            header = stream.read(0x100)
        if len(header) != 0x100 or header[:4] != b'NPD\0' or path.stat().st_size <= 0x100:
            continue
        content = header[0x10:0x40].split(b'\0', 1)[0].decode('ascii', errors='replace')
        match = re.fullmatch(r'EP\d{4}-BCES00141_00-([A-Z0-9]{16})', content)
        if match:
            installed.add(match[1])
    return installed


class ContentPackValidator:
    def __init__(self, rpcs3_directory=None, save_directory=None):
        self.rpcs3_directory = Path(rpcs3_directory) if rpcs3_directory else None
        self.save_directory = Path(save_directory) if save_directory else None
        self.cached_key = None
        self.next_check = 0
        self.error = None

    def game_directory(self):
        if self.rpcs3_directory:
            path = self.rpcs3_directory/'dev_hdd0'/'game'
        elif self.save_directory and self.save_directory.parent.parent.name == 'game':
            path = self.save_directory.parent.parent
        else:
            # Avoid silently picking one installation when multiple emulators run.
            candidates = set()
            try:
                import psutil
            except ImportError:
                psutil = None
            if psutil:
                for process in psutil.process_iter(['name', 'exe']):
                    try:
                        if (process.info['name'] or '').lower() in ('rpcs3', 'rpcs3.exe') and process.info['exe']:
                            candidate = Path(process.info['exe']).parent/'dev_hdd0'/'game'
                            if candidate.is_dir():
                                candidates.add(candidate)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            if len(candidates) == 1:
                return candidates.pop()
            if len(candidates) > 1:
                raise ContentOptionsError('Options error: multiple RPCS3 installations are running. '
                                          'Select the active one with --rpcs3-dir.')
            # Local installer configuration is the same source used for save backups.
            config = ROOT/'output/port_130/installation.json'
            if config.is_file():
                path = Path(json.loads(config.read_text(encoding='utf-8'))['save']).parent.parent
            else:
                raise ContentOptionsError('Options error: cannot locate installed DLC. Start the client with '
                                          '--rpcs3-dir pointing to your active RPCS3 folder (or --save-dir).')
        if not path.is_dir():
            raise ContentOptionsError(f'Options error: RPCS3 game directory does not exist: {path}')
        return path

    def validate(self, slot_data):
        required = requirements(slot_data)
        if not required:
            return
        directory = self.game_directory()
        key = (str(directory), required)
        if key != self.cached_key or time.monotonic() >= self.next_check:
            try:
                installed = installed_content(directory)
            except OSError as exc:
                raise ContentOptionsError(f'Options error: cannot read installed DLC: {exc}') from exc
            missing = sorted({name for name, alternatives in required if not alternatives & installed})
            self.error = ('Options error: required DLC is not installed: ' + '; '.join(missing)
                          + '. Install the packs required by this slot, or regenerate with those options disabled. '
                          'Restart RPCS3 after installing DLC.') if missing else None
            self.cached_key, self.next_check = key, time.monotonic() + 5
        if self.error:
            raise ContentOptionsError(self.error)
