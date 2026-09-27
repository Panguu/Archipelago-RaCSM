"""AP-controlled PSP Challenge Mode counter (retail save offset 0x1C38)."""
from .address_maps import CURRENT_PLANET_ADDRESS, MENU_ADDR_BY_PLANET_ID
from .structs.game import TransitionGateStruct, TRANSITION_GATE_IDLE
from .menu import MenuStateValue

# UCUS98633 resident save base 0x088C0B00. Retail uses lw/sw, not a byte.
# Save current-planet offset is 0x1C2C; Challenge Mode counter is +0x0C.
CHALLENGE_MODE_ADDRESS = 0x088C2738


class ChallengeModeState:
    def __init__(self, memory):
        self.memory = memory
        self.ceiling = 0
        self.progressive = False
        self.received = 0
        self.tier = 0
        self.configured = False

    def configure(self, ceiling, progressive=False):
        if type(ceiling) is not int or not 0 <= ceiling <= 2:
            raise ValueError('Challenge Mode ceiling must be 0, 1 or 2')
        self.ceiling, self.progressive = ceiling, bool(progressive)
        self.received = 0
        self.tier = 0
        self.configured = True

    def set_received(self, count):
        if type(count) is not int or count < 0:
            raise ValueError('Invalid Progressive Challenge Mode receipt count')
        self.received = count

    @property
    def desired(self):
        return min(self.ceiling, self.received) if self.progressive else self.ceiling

    def apply(self, planet, ready):
        if not self.configured or not ready or planet not in MENU_ADDR_BY_PLANET_ID:
            return False
        m = self.memory
        if (m.read_int32(TransitionGateStruct.BASE_ADDRESS) != TRANSITION_GATE_IDLE
                or m.read_int8(CURRENT_PLANET_ADDRESS) != planet):
            return False
        if m.read_int8(MENU_ADDR_BY_PLANET_ID[planet]) in (MenuStateValue.WEAPONS_VENDOR, MenuStateValue.MOD_VENDOR):
            return False
        if m.read_int32(CHALLENGE_MODE_ADDRESS) != self.desired:
            m.write_int32(CHALLENGE_MODE_ADDRESS, self.desired)
            if m.read_int32(CHALLENGE_MODE_ADDRESS) != self.desired:
                raise RuntimeError('Challenge Mode counter failed readback')
        self.tier = self.desired
        return True
