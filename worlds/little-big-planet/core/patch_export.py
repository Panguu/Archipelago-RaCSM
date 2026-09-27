"""Generate and install a personal RPCS3 patch after checking the running game, without writes to it."""
from pathlib import Path

import yaml

from .compatibility import verify_130
from .game_versions import identify
from .pine import Pine
try:
    from ..constants.data.patch_template_130 import DATA as PATCH_TEMPLATE
except ImportError:
    from constants.data.patch_template_130 import DATA as PATCH_TEMPLATE


def patch_document(pine):
    executable, build = identify(pine)
    if build['version'] != '01.30':
        raise RuntimeError('Personal patch export requires NPEA00241 v1.30')
    # Also check known hashes: another enabled runtime patch may alter AP dependencies.
    verify_130(pine)
    if pine.request(bytes([13]))[4:].rstrip(b'\0').decode() != executable:
        raise RuntimeError('Game changed during patch export; retry')
    return executable, {'Version': 1.2, executable: PATCH_TEMPLATE}


def read_document(port=28011, pine=None):
    # The caller must serialize access when supplying the gameplay connection.
    owned = pine is None
    if owned:
        pine = Pine(port)
    try:
        return patch_document(pine)
    finally:
        if owned:
            pine.close()


def _load_yaml(path):
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    if data is not None and not isinstance(data, dict):
        raise RuntimeError(f'Unexpected RPCS3 patch file layout: {path}')
    return data or {}


def _replace(path, data):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(yaml.safe_dump(data, sort_keys=False), encoding='utf-8')
    temporary.replace(path)


def install_patch(rpcs3_root, port=28011, pine=None):
    """Write this executable's AP patch into RPCS3 and enable it; takes effect on next game boot.

    Every verified executable hash (original v1.30 or any Union variant) gets its own
    entry in one shared file, so switching EBOOTs only needs another /patch."""
    executable, document = read_document(port, pine)
    root = Path(rpcs3_root)
    patches = root/'patches'
    patches.mkdir(exist_ok=True)
    (description, entry), = PATCH_TEMPLATE.items()
    # A manual import of the same patch would apply the hooks twice.
    if description in (_load_yaml(patches/'imported_patch.yml').get(executable) or {}):
        raise RuntimeError(f'{patches/"imported_patch.yml"} already has "{description}" for this game. '
                           'Remove it in RPCS3 Manage > Game Patches, then run /patch again.')
    path = patches/'Archipelago-LBP_patch.yml'
    current = _load_yaml(path)
    current['Version'] = document['Version']
    current[executable] = document[executable]
    _replace(path, current)

    # Newer RPCS3 keeps patch_config.yml in config/; older builds kept it in patches/.
    config_path = (root/'config' if (root/'config').is_dir() else patches)/'patch_config.yml'
    config = _load_yaml(config_path)
    node = config.setdefault(executable, {}).setdefault(description, {})
    for title, serials in entry['Games'].items():
        for serial, versions in serials.items():
            for version in versions:
                node.setdefault(title, {}).setdefault(serial, {}).setdefault(version, {})['Enabled'] = True
    _replace(config_path, config)
    return executable, path


def export_patch(directory, port=28011, pine=None):
    executable, document = read_document(port, pine)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'Archipelago-LBP-{executable}.yml'
    text = yaml.safe_dump(document, sort_keys=False)
    if path.exists():
        if path.read_text(encoding='utf-8') != text:
            raise RuntimeError(f'Existing patch differs; move it before exporting again: {path}')
    else:
        with path.open('x', encoding='utf-8') as stream:
            stream.write(text)
    return path
