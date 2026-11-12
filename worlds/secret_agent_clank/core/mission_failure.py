from .patches import Patch, jump, mips as m, packed


class MissionFailure:
    def __init__(self, pine):
        self.pine = pine
        self.binding = None

    def prepare(self, symbols, allocate):
        self.binding = None
        render = symbols.get("CLANK_MissionFailedText__FPv")
        entries = []
        # Verified entry instructions, replayed after setting the shared latch.
        # Do not hook individual Gadgetbot deaths: only mission/player failure.
        for name, words in (
            ("PLAYER_PlayerIsDeadRequestLevelRestart__FP6PLAYER", [0x27BDFFF0, 0xFFB00000]),
            ("Begin__11MissionFail", [0x27BDFFE0, 0x240300A1]),
            ("Begin__15MissionFailFall", [0x27BDFFF0, 0xFFB00000]),
            ("Begin__10QwarkDeath", [0x27BDFFE0, 0xFFB10008]),
            ("Begin__16QwarkFallToDeath", [0x27BDFFF0, 0x24030004]),
            ("Arena_FailChallenge__FP4Moby", [0x24020008, 0x03E00008, 0xA0820045]),
        ):
            address = symbols.get(name)
            if address is not None:
                original = packed(words)
                if self.pine.read_bytes(address, len(original)) != original:
                    raise RuntimeError(f"Native failure entry changed: {name}")
                entries.append((address, original))
        giant = symbols.get("Enter__14GCP_DeathStateP16GiantClankPlayer")
        if giant is not None:
            original = self.pine.read_bytes(giant, 8)
            if (original[:4] != packed([0x27BDFFF0])
                    or int.from_bytes(original[4:], "little") & 0xFFFF0000 != 0x3C020000):
                raise RuntimeError("Native giant Qwark death entry changed")
            entries.append((giant, original))
        if render is None and not entries:
            return []
        flag = allocate(packed([0]))
        edits = self._prepare_text(symbols, allocate, render, flag) if render is not None else []
        token = self.binding[0] + 8 if self.binding else entries[0][0] + 8
        for site, original in entries:
            code = packed([*m.li32(m.T1, token),
                           m.lui(m.T0, (flag + 0x8000) >> 16),
                           m.sw(m.T1, flag & 0xFFFF, m.T0)]) + original
            if len(original) == 8:
                code += packed([jump(site + 8), m.NOP])
            entry = allocate(code)
            replacement = packed([jump(entry), m.NOP])
            edits.append(Patch(site, original[:8], replacement))
            if self.binding is None:
                self.binding = site, replacement, entry, code, flag
        bots = symbols.get("GadgetBot_UpdateType__FP8MobyType")
        if bots is not None:
            # The native loop counts bots that are alive OR still playing
            # their death animation in s2. Only zero reaches this fade call.
            # Hook here, before the fade finishes and requests a reload, never
            # GadgetBotDeath (which runs for each individual bot).
            fade = symbols.get("FADEOVERLAY_Refresh__FUiUcUcUcb")
            site = bots + 0x180
            original = packed([jump(fade, True), m.dmove(m.T0, m.ZERO)]) if fade else b""
            if (not fade or self.pine.read_int32(bots + 0x168) != 0x1640000E
                    or self.pine.read_bytes(site, 8) != original):
                raise RuntimeError("Native Gadgetbot squad failure changed")
            # t0 is the fifth fade argument; preserve it and the original RA.
            code = packed([*m.li32(m.T1, token),
                           m.lui(m.T2, (flag + 0x8000) >> 16),
                           jump(fade), m.sw(m.T1, flag & 0xFFFF, m.T2)])
            entry = allocate(code)
            edits.append(Patch(site, original[:4], packed([jump(entry, True)])))
        edits.extend(self._prepare_vehicle(symbols, allocate, flag, token))
        return edits

    def _prepare_vehicle(self, symbols, allocate, flag, token):
        finish = symbols.get("VehicleChallengeController_ChallengeFinished__FUiUi")
        if finish is None:
            return []
        if self.pine.read_bytes(finish, 8) == packed([m.jr(m.RA), m.NOP]):
            return []  # Non-vehicle modules export an unused-operative stub.
        if self.pine.read_bytes(finish, 8) != packed([0x27BDFFE0, 0x24020002]):
            raise RuntimeError("Native vehicle challenge finish changed")
        update = symbols.get("VehicleChallengeController_Update__FP4Mobyf")
        reset = symbols.get("VehicleSectionStarter_Reset__Fv")
        start = symbols.get("VehicleChallengeController_StartChallenge__FUiUi")
        if None in (update, reset, start):
            raise RuntimeError("Native vehicle challenge exports missing")
        edits = []
        # Only the insufficient-ring and expired-timer branches set the
        # failure flag before Reset. Successful finishes call it elsewhere.
        for site, store in ((finish + 0x44, 0xA0620000), (update + 0x138, 0xA0500000)):
            original = self.pine.read_bytes(site, 8)
            if (original[:4] != packed([jump(reset, True)])
                    or int.from_bytes(original[4:], "little") & 0xFFFF0000 != store):
                raise RuntimeError("Native vehicle challenge failure branch changed")
            code = packed([*m.li32(m.T1, token), m.lui(m.T2, (flag + 0x8000) >> 16),
                           jump(reset), m.sw(m.T1, flag & 0xFFFF, m.T2)])
            entry = allocate(code)
            edits.append(Patch(site, original[:4], packed([jump(entry, True)])))
        # Vehicle challenges can restart without reloading the module.
        original = self.pine.read_bytes(start, 8)
        if (original[:4] != packed([0x27BDFFE0])
                or int.from_bytes(original[4:], "little") & 0xFFFF0000 != 0x3C020000):
            raise RuntimeError("Native vehicle challenge start changed")
        code = packed([m.lui(m.T0, (flag + 0x8000) >> 16),
                       m.sw(m.ZERO, flag & 0xFFFF, m.T0)]) + original + packed([jump(start + 8), m.NOP])
        entry = allocate(code)
        edits.append(Patch(start, original, packed([jump(entry), m.NOP])))
        return edits

    def _prepare_text(self, symbols, allocate, render, flag):
        get_string = symbols.get("GetStr__Fi")
        site = render + 0x14
        if (get_string is None or self.pine.read_bytes(site, 8)
                != packed([jump(get_string, True), m.addiu(m.A0, m.ZERO, 934)])):
            raise RuntimeError("Native Mission Failed renderer changed")
        original = packed([jump(get_string, True)])
        # Record this call's return address as the latch, then tail-call
        # GetStr with its original arguments/RA. Only caller-saved t0 changes.
        code = packed([m.lui(m.T0, (flag + 0x8000) >> 16),
                       jump(get_string), m.sw(m.RA, flag & 0xFFFF, m.T0)])
        entry = allocate(code)
        replacement = packed([jump(entry, True)])
        self.binding = site, replacement, entry, code, flag
        return [Patch(site, original, replacement)]

    def active(self):
        if self.binding is None:
            return False
        site, replacement, entry, code, flag = self.binding
        if (self.pine.read_bytes(site, len(replacement)) != replacement
                or self.pine.read_bytes(entry, len(code)) != code):
            return False
        return self.pine.read_int32(flag) == site + 8
