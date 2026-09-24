"""Read-only validation of v1.30 code dependencies, independent of server identity."""
import hashlib

try:
    from ..constants.data.compatibility_130 import DATA as MANIFEST
except ImportError:
    from constants.data.compatibility_130 import DATA as MANIFEST


def verify_130(pine):
    manifest = MANIFEST
    for region in manifest['ranges']:
        address, size = region['address'], region['size']
        # Keep PINE packets small; large Read8 batches can stall some builds.
        data = bytearray()
        for offset in range(0, size, 256):
            count = min(256, size-offset)
            chunk = pine.read(address+offset, count)
            if len(chunk) != count:
                raise RuntimeError('Truncated executable compatibility read')
            data.extend(chunk)
        # Accept only our exact static replacements. Never mask arbitrary bytes
        # or foreign branches. RPCS3 calloc hooks retain original PINE text.
        for site, original, replacement in manifest['replacements']:
            offset = site-address
            if 0 <= offset <= size-4 and data[offset:offset+4] == replacement.to_bytes(4, 'big'):
                data[offset:offset+4] = original.to_bytes(4, 'big')
        if hashlib.sha256(data).hexdigest() != region['sha256']:
            raise RuntimeError(
                f'Unsupported LBP code layout at {address:#x}; AP compatibility '
                'verification failed. Keep your online patch; this build needs a new AP port.')
