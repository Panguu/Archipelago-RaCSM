"""Known executable layouts and fingerprint-verified v1.30 online variants."""
import re

from .compatibility import verify_130
HASH_127 = 'PPU-53fe207e75d7dfa26f83416f0f587bebe7005a0b'
HASH_130 = 'PPU-545c1abbf1c562d60fca7435401f020beab76b53'
HASH_130_UNION = 'PPU-54d7031c59958d5fd278e696b07001fe44376ada'
HASHES_130 = (HASH_130, HASH_130_UNION)
BUILDS = {
    HASH_127: dict(version='01.27', root=0x86b3c8, user=0x879f84, table=0x870764,
                   slot=0x128, reward_size=44, prize_count=0x88,
                   signatures={0x85d48: '81229f30806900004e800020',
                               0x85f74: '8523007c800300047d2b4b78'},
                   death={0x1caa8: '380000003920000190030070992300744e800020',
                          0x6cc3c: '88030074', 0x6cd40: '4bfffeb938000000981f0074'}),
    HASH_130: dict(version='01.30', root=0x86b3d8, user=0x879f90, table=0x87076c,
                   slot=0x120, reward_size=36, prize_count=0x88,
                   signatures={0x85dc8: '81229f38806900004e800020',
                               0x85ff4: '8563007c800300047d6a5b78'},
                   death={0x1ca78: '380000003920000190030070992300744e800020',
                          0x68cc8: '88030074', 0x68dcc: '4bfffeb938000000981f0074'}),
}

# Union-patched executable verified through PINE: reader/death signatures and
# every AP hook/replacement site match the original v1.30 layout.
BUILDS[HASH_130_UNION] = BUILDS[HASH_130]


def identify(pine, info=None):
    info = info or pine.info()
    executable = pine.request(bytes([13]))[4:].rstrip(b'\0').decode()
    build = BUILDS.get(executable)
    if build and (info['id'], info['version']) == ('NPEA00241', build['version']):
        pine._lbp_verified_variant = None
        return executable, build
    if (build is not None or (info['id'], info['version']) != ('NPEA00241', '01.30')
            or not re.fullmatch(r'PPU-[0-9a-f]{40}', executable)):
        raise RuntimeError(f'Unsupported LBP executable: {info["id"]} {info["version"]} {executable}')
    if info['status'] not in ('running', 'paused'):
        pine._lbp_verified_variant = None
        raise RuntimeError('Boot the Union-patched game before AP compatibility verification')
    # Cache on this transport only, never globally or as a user-editable hash allowlist.
    # Reconnecting or changing the executable triggers a fresh read-only check.
    if getattr(pine, '_lbp_verified_variant', None) != executable:
        verify_130(pine)
        after = pine.info()
        after_hash = pine.request(bytes([13]))[4:].rstrip(b'\0').decode()
        if after != info or after_hash != executable:
            raise RuntimeError('Game changed during AP compatibility verification; retry')
        pine._lbp_verified_variant = executable
    return executable, BUILDS[HASH_130]
