"""The fields the client needs from each built level, saved relative to the
module base. Code is saved with its relocations so it can be checked at any base.
"""
import struct

from .snr2 import SNR2Module, word


FIELDS = {
    "hooks": ("module", "marker_address", "tables", "locations", "entitlement_table", "gadget_base"),
    "wrench": ("module", "ownership_address", "power_address"),
    "mission_travel": ("completion_mailbox",),
    "skins": ("config_address",),
    "weapon_mods": ("module", "base", "mod_list", "table"),
    "progression": ("module", "base", "save_pointer_address", "cap_address", "pickup_challenge_address", "config_address"),
    "vendor_catalog": ("case_descriptors", "location_descriptors", "challenge_descriptors"),
    "presentation": ("mailbox", "timer"),
    "connection_warning": ("heartbeat", "entry"),
    "keycard_hunt": ("table", "entry", "pointer_address", "enable_address"),
}


class BindingCompiler:
    def __init__(self, compiled, imports, base):
        self.module = SNR2Module(compiled)
        self.imports, self.base = imports, base
        self.relocations = {}
        low = None
        for relocation in reversed(self.module.local_relocations):
            offset, kind = relocation.offset, relocation.kind
            original = word(compiled, offset)
            if kind == 0:
                low = offset
                value, native = original & 65535, 6
            elif kind == 1:
                if low is None:
                    raise ValueError("Missing local low half")
                value = ((original & 65535) << 16) + struct.unpack_from("<h", compiled, low)[0]
                native = 5
            elif kind == 2:
                value, native = (original & 0x3FFFFFF) << 2, 4
            else:
                value, native = original, 2
            self.relocations[offset] = (native, True, value)
        for relocation in self.module.import_relocations:
            symbol = self.module.symbols[relocation.symbol]
            relative = symbol.kind in (0, 2, 3)
            value = imports[symbol.name] if symbol.kind == 1 else symbol.value
            self.relocations[relocation.offset] = (relocation.kind, relative, value + relocation.addend)

    def code(self, address, size):
        offset = address - self.base
        if offset % 4 or size % 4 or offset < 128 or offset + size > len(self.module.data):
            raise ValueError("Code binding outside module")
        return {"code": self.module.data[offset:offset + size].hex(),
                "fixups": [[site - offset, *recipe] for site, recipe in self.relocations.items()
                           if offset <= site < offset + size]}

    def value(self, value):
        if isinstance(value, int) and not isinstance(value, bool):
            value = int(value)
            if self.base <= value < self.base + len(self.module.data):
                return {"address": value - self.base}
            return value
        if value is None or isinstance(value, (str, bool)):
            return value
        if isinstance(value, dict):
            return {"mapping": [[self.value(k), self.value(v)] for k, v in value.items()]}
        if isinstance(value, (tuple, list, set, frozenset)):
            kind = "set" if isinstance(value, (set, frozenset)) else "tuple"
            values = sorted(value) if kind == "set" else value
            return {kind: [self.value(v) for v in values]}
        raise TypeError(f"Unsupported binding value: {type(value).__name__}")

    def objects(self, objects):
        result = {name: {field: self.value(getattr(obj, field)) for field in FIELDS[name]}
                  for name, obj in objects.items() if name in FIELDS}
        skins = objects["skins"]
        result["skins"]["pointer_address"] = self.value(skins.flags.pointer_address)
        for name in ("connection_warning", "keycard_hunt"):
            obj = objects[name]
            if obj.entry is not None:
                result[name]["code"] = self.code(obj.entry, len(obj.code))
        failure = objects["mission_failure"].binding
        if failure:
            site, replacement, entry, code, flag = failure
            result["mission_failure"] = {"binding": {"tuple": [self.value(site), self.code(site, len(replacement)),
                self.value(entry), self.code(entry, len(code)), self.value(flag)]}}
        else:
            result["mission_failure"] = {"binding": None}
        stealth = objects["stealth"].binding
        if stealth:
            case, counter, site, replacement, entry, code = stealth
            result["stealth"] = {"binding": {"tuple": [case, self.value(counter), self.value(site),
                self.code(site, len(replacement)), self.value(entry), self.code(entry, len(code))]}}
        else:
            result["stealth"] = {"binding": None}
        return result


def decode_binding(value, base):
    if not isinstance(value, dict):
        return value
    if set(value) == {"address"}:
        offset = value["address"]
        if type(offset) is not int or offset < 128 or base + offset >= 0x2000000:
            raise ValueError("Invalid binding address")
        return base + offset
    if set(value) == {"code", "fixups"}:
        data = bytearray.fromhex(value["code"])
        for offset, kind, relative, addend in value["fixups"]:
            if offset % 4 or not 0 <= offset <= len(data) - 4 or kind not in (1, 2, 4, 5, 6, 119):
                raise ValueError("Invalid code binding fixup")
            SNR2Module._write(data, offset, kind, addend + (base if relative else 0))
        return bytes(data)
    if set(value) == {"mapping"}:
        return {decode_binding(k, base): decode_binding(v, base) for k, v in value["mapping"]}
    if set(value) == {"tuple"}:
        return tuple(decode_binding(v, base) for v in value["tuple"])
    if set(value) == {"set"}:
        return set(decode_binding(v, base) for v in value["set"])
    raise ValueError("Unknown native binding recipe")
