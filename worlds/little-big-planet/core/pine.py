"""Read-only RPCS3 PINE transport. Replaced by the pypine submodule in a later pass."""
import socket
import struct


class Pine:
    def __init__(self, port=28011):
        self.sock = socket.create_connection(('127.0.0.1', port), timeout=5)
        self.sock.settimeout(10)

    def close(self):
        self.sock.close()

    def _recv(self, size):
        result = bytearray()
        while len(result) < size:
            chunk = self.sock.recv(size - len(result))
            if not chunk:
                raise ConnectionError('PINE disconnected')
            result.extend(chunk)
        return bytes(result)

    def request(self, commands):
        if not commands or len(commands) + 4 > 650000:
            raise ValueError('Invalid PINE request length')
        self.sock.sendall(struct.pack('<I', len(commands) + 4) + commands)
        size, = struct.unpack('<I', self._recv(4))
        if not 5 <= size <= 450000:
            raise ValueError(f'Invalid PINE reply length {size}')
        result = self._recv(size - 4)
        if result[0] != 0:
            raise ValueError('PINE rejected request (possibly unmapped memory)')
        return result[1:]

    def info(self):
        result = {}
        for name, opcode in [('emulator',8), ('title',11), ('id',12), ('version',14)]:
            raw = self.request(bytes([opcode]))
            if len(raw) < 4 or struct.unpack('<I', raw[:4])[0] != len(raw) - 4:
                raise ValueError('Invalid PINE string')
            result[name] = raw[4:].rstrip(b'\0').decode('utf-8', errors='replace')
        raw = self.request(bytes([15]))
        status, = struct.unpack('<I', raw)
        result['status'] = {0:'running',1:'paused',2:'shutdown'}.get(status, f'unknown:{status}')
        return result

    def read(self, address, length):
        if address < 0 or length < 0 or address + length > 2**32:
            raise ValueError('Invalid guest address range')
        result = bytearray()
        for offset in range(0, length, 60000):
            n = min(60000, length-offset)
            commands = b''.join(struct.pack('<BI',0,address+offset+i) for i in range(n))
            data = self.request(commands)
            if len(data) != n:
                raise ValueError('Unexpected read response length')
            result.extend(data)
        return bytes(result)
