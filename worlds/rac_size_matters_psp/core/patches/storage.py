"""Owned PSP kernel memory for patch payloads and runtime data.

The caller supplies verified, nonblocking kernel imports and holds the guest
CPU stopped at a supported frame boundary throughout each operation.
"""
from dataclasses import dataclass
import secrets


@dataclass(frozen=True)
class Allocation:
    name: str
    address: int
    size: int


class PatchStorage:
    HEADER_SIZE = 64

    def __init__(self, memory, kernel, size=0x4000):
        if type(size) is not int or size < 128 or size > 0x100000 or size % 64:
            raise ValueError("Patch storage must be 128..1048576 bytes, aligned to 64")
        self.memory, self.kernel, self.size = memory, kernel, size
        self.block_id = None
        self.address = None
        self._cookie = None
        self._next = self.HEADER_SIZE
        self.allocations = {}
        self._users = set()
        self._failed = False

    def open(self):
        if self._failed:
            raise RuntimeError("Patch storage initialization failed; reconnect required")
        if self.block_id is not None:
            self.validate()
            return
        block = self.kernel.allocate(self.size)
        if type(block) is not int or not 0 < block < 0x80000000:
            raise RuntimeError(f"PSP allocation failed: {block!r}")
        self.block_id = block
        # Record ownership before subsequent operations so a failed write can
        # still release the known allocation, without guessing an address.
        try:
            address = self.kernel.head(block)
            if type(address) is not int or address % 64 or not 0x08800000 <= address <= 0x0A000000 - self.size:
                raise RuntimeError("PSP allocator returned an invalid block address")
            cookie = b"RACSMPSP" + secrets.token_bytes(24)
            header = cookie.ljust(self.HEADER_SIZE, b"\0")
            self.memory.write_bytes(address, header)
            if self.memory.read_bytes(address, self.HEADER_SIZE) != header:
                raise RuntimeError("Patch storage header failed readback")
        except Exception:
            # If cleanup also fails, retain the UID and prevent a second
            # allocation from silently leaking or replacing this ownership.
            self._failed = True
            if self.kernel.free(block) == 0:
                self.block_id = None
            raise
        self.block_id, self.address, self._cookie = block, address, header

    def validate(self):
        if self._failed:
            raise RuntimeError("Patch storage initialization failed; reconnect required")
        if self.block_id is None:
            raise RuntimeError("Patch storage is closed")
        self.memory.validate_session()
        # Both the kernel block and our nonce must match. A savestate or guest
        # restart can recycle a UID or preserve stale RAM from a freed block.
        if self.kernel.head(self.block_id) != self.address:
            raise RuntimeError("PSP patch allocation changed; refusing stale access")
        if self.memory.read_bytes(self.address, self.HEADER_SIZE) != self._cookie:
            raise RuntimeError("PSP patch storage changed; refusing stale access")

    def reserve(self, name, size, alignment=16):
        if not name or name in self.allocations:
            raise ValueError("Patch buffer name must be unique and nonempty")
        if type(size) is not int or size <= 0:
            raise ValueError("Patch buffer size must be positive")
        if type(alignment) is not int or alignment <= 0 or alignment > 64 or alignment & (alignment - 1):
            raise ValueError("Alignment must be a power of two, up to 64")
        self.validate()
        offset = (self._next + alignment - 1) & -alignment
        if offset + size > self.size:
            raise MemoryError("PSP patch storage exhausted")
        allocation = Allocation(name, self.address + offset, size)
        self.memory.write_bytes(allocation.address, bytes(size))
        if self.memory.read_bytes(allocation.address, size) != bytes(size):
            raise RuntimeError("Patch buffer initialization failed readback")
        self.allocations[name] = allocation
        self._next = offset + size
        return allocation

    def write(self, name, data, offset=0):
        allocation = self.allocations[name]
        data = bytes(data)
        if type(offset) is not int or offset < 0 or offset + len(data) > allocation.size:
            raise ValueError("Write exceeds owned patch buffer")
        self.validate()
        self.memory.write_bytes(allocation.address + offset, data)
        if self.memory.read_bytes(allocation.address + offset, len(data)) != data:
            raise RuntimeError("Patch buffer write failed readback")

    def retain(self, owner):
        """Mark a hook as potentially referencing this storage before install."""
        self.validate()
        self._users.add(owner)

    def release(self, owner):
        """Call only after a hook has been verified fully restored."""
        self._users.discard(owner)

    def close(self):
        if self.block_id is None:
            return
        if self._users:
            raise RuntimeError("Cannot free PSP storage while hooks reference it")
        self.validate()
        result = self.kernel.free(self.block_id)
        if result != 0:
            raise RuntimeError(f"PSP free failed: {result!r}")
        self.block_id = self.address = self._cookie = None
        self.allocations.clear()
        self._next = self.HEADER_SIZE
