class VendorTextLayout:
    TITLE_CALLS = (0x3FC, 0x464, 0x4CC)
    DESCRIPTION_CALL = 0x5FC

    @staticmethod
    def _text(value, capacity, color=None):
        clean = "".join(c if 32 <= ord(c) < 127 or c == "\n" else "?" for c in value)
        prefix = bytes((0x90, color)) if color is not None else b""
        suffix = b"\x90\x01" if color is not None else b""
        content = clean.encode("ascii")[:capacity-len(prefix)-len(suffix)-1]
        return (prefix + content + suffix).ljust(capacity, b"\0")
