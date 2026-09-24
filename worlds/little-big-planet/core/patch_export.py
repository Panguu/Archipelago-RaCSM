"""Generate a personal RPCS3 patch after checking the running game, without writes to it."""
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


def export_patch(directory, port=28011, pine=None):
    # The caller must serialize access when supplying the gameplay connection.
    owned = pine is None
    if owned:
        pine = Pine(port)
    try:
        executable, document = patch_document(pine)
    finally:
        if owned:
            pine.close()
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
