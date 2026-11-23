import struct
from collections import deque


def _clean(value, limit):
    value = "".join(c if 32 <= ord(c) < 127 else "?" for c in str(value))
    return (value[:limit - 3] + "...") if len(value) > limit else value


def _item_text(verb, item, preposition, player, trap):
    color = 3 if trap else 13
    return (verb + b" " + bytes((0x90, color)) + _clean(item, 45).encode("ascii")
            + b"\x90\x01\n" + preposition + b" \x90\x0b" + _clean(player, 30).encode("ascii") + b"\x90\x01\0")


def receipt_text(item, sender, trap=False):
    return _item_text(b"Received", item, b"from", sender, trap)


def sent_text(item, receiver, trap=False):
    return _item_text(b"Sent", item, b"to", receiver, trap)


def death_text(source, cause):
    return (b"DeathLink from \x90\x0b" + _clean(source, 30).encode("ascii") + b"\x90\x01\n"
            + bytes((0x90, 3)) + _clean(cause, 45).encode("ascii") + b"\x90\x01\0")


def death_sent_text(cause):
    return b"DeathLink sent\n" + bytes((0x90, 3)) + _clean(cause, 45).encode("ascii") + b"\x90\x01\0"


class ItemNotifications:
    def __init__(self, pine):
        self.pine = pine
        self.queue = deque()
        self.binding = None

    def enqueue(self, item, sender, trap=False):
        self.queue.append(receipt_text(item, sender, trap))

    def enqueue_sent(self, item, receiver, trap=False):
        self.queue.append(sent_text(item, receiver, trap))

    def enqueue_death(self, source, cause):
        self.queue.append(death_text(source, cause))

    def enqueue_death_sent(self, cause):
        self.queue.append(death_sent_text(cause))

    def bind(self, symbols):
        self.binding = None
        show = symbols.get("HUD_ShowOneLiner__FPCcbi")
        render = symbols.get("HUD_RenderOneLiner__Fv")
        pause = symbols.get("g_PauseModeData")
        if None in (show, render, pause):
            return False
        p = self.pine
        # Once installed, the connection watchdog replaces render's prologue
        # with `j routine; nop`; the body read below is unchanged either way.
        first, second = struct.unpack("<2I", p.read_bytes(render, 8))
        hooked = first >> 26 == 2 and second == 0
        if p.read_int32(show) != 0x27BDFFE0 or (first != 0x27BDFFE0 and not hooked):
            return False
        def address(base, high, low, high_opcode, low_opcode):
            hi, lo = p.read_int32(base + high), p.read_int32(base + low)
            if hi & 0xFFFF0000 != high_opcode or lo & 0xFFFF0000 != low_opcode:
                raise ValueError("Unrecognized native one-liner layout")
            signed = lo & 65535
            result = ((hi & 65535) << 16) + (signed - 65536 if signed & 32768 else signed)
            if not 0x100000 <= result < 0x2000000 - 256:
                raise ValueError("Invalid HUD address")
            return result
        try:
            buffer = address(show, 0x30, 0x38, 0x3C040000, 0x24840000)
            timer = address(show, 0x44, 0x4C, 0x3C030000, 0xAC710000)
            cooldown = address(show, 0x1C, 0x20, 0x3C020000, 0x8C430000)
            blink = address(show, 0x2C, 0x34, 0x3C020000, 0xA0450000) # sb a1
            window = address(render, 0x28, 0x4C, 0x3C040000, 0x24840000)
            left = address(render, 0x68, 0x84, 0x3C030000, 0x8C640000)
            right = address(render, 0xAC, 0xC4, 0x3C030000, 0x8C640000)
        except ValueError:
            return False
        call = p.read_int32(render + 0x98)
        if call >> 26 != 3 or p.read_int32(render + 0xD8) != call:
            return False
        draw = (call & 0x03FFFFFF) << 2
        words = struct.unpack("<3I", p.read_bytes(draw + 0x6C, 12))
        if words[:2] != (0x3C02FFFF, 0x3442FFFF) or words[2] & 0xFFFF0000 != 0x10A20000:
            return False
        if window - buffer != 256:
            return False
        self.binding = (buffer, timer, cooldown, blink, window, left, right, pause + 12)
        return True

    def tick(self):
        if not self.queue or self.binding is None:
            return
        p = self.pine
        buffer, timer, cooldown, blink, window, left, right, screen = self.binding
        if (p.read_int32(0x206324) != 0xFFFFFFFF or p.read_int32(0x206338) != 3
                or p.read_int32(screen) != 0):
            return
        if p.read_int32(timer) or p.read_int32(cooldown):
            return
        text = self.queue[0]
        data = bytearray(0x54)
        struct.pack_into("<4i", data, 0, 24, 186, 456, 254)
        struct.pack_into("<2h", data, 0x10, 8, 8)
        struct.pack_into("<I", data, 0x14, buffer)
        struct.pack_into("<I", data, 0x20, 0xC7)
        struct.pack_into("<I", data, 0x28, 0xA0302020)
        struct.pack_into("<I", data, 0x2C, 0xFFC0C0C0)
        struct.pack_into("<I", data, 0x30, 1)
        data[0x39] = 1
        struct.pack_into("<3I", data, 0x3C, 60, 30, 4)
        data[0x48] = 1
        p.write_bytes(buffer, text.ljust(256, b"\0"))
        p.write_bytes(window, bytes(data))
        p.write_int32(left, 0xFFFFFFFF)
        p.write_int32(right, 0xFFFFFFFF)
        p.write_bytes(blink, b"\0")
        p.write_int32(timer, 240)
        self.queue.popleft()
