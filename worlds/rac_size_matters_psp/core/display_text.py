from __future__ import annotations

# Colour encoding
# 0x09 = colour-change marker; the following byte selects the colour.

class TextColour:
    YELLOW  = bytes([0x90, 0x10])
    PURPLE = bytes([0x90, 0x04])
    RED = bytes([0x90, 0x03])
    ORANGE = bytes([0x90, 0x02])
    WHITE  = bytes([0x90, 0x01])


def colored_text(*parts: bytes | str) -> bytes:
    """Build a null-terminated byte string from text and TextColour constants.

    Example:
        colored_text("Received ", TextColour.PURPLE, "X", TextColour.WHITE, " from Y")
    """
    buf = bytearray()
    for part in parts:
        buf.extend(part if isinstance(part, (bytes, bytearray)) else part.encode("ascii"))
    buf.append(0x00)
    return bytes(buf)


# In-game text-box display (SmallTextBox/MultiLineTextBox, STATIC_TEXT_BUFFER)
# was removed — PSP addresses for it were never verified and won't be pursued.
# Core.notify() now just logs every message that would have gone through here
# (item received, deathlink, connection status, ...); colored_text() above is
# kept since callers still build messages with it for the log line.
