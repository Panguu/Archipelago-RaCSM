"""Route completed missions to Case Files, including Ratchet's movie exit."""
from ...constants.native_functions import NativeFunctions as Functions
from ..symbols import require
from .asm import Patch, branch, jump, packed
from .patch import PatchSet


class TravelLayout:
    HELPER_PROLOGUE = (0x27BDFFF0, 0xFFB00000, 0xFFBF0008)
    HELPER_DECISION_OFFSET = 0x14
    HELPER_DECISION = (0x0050102B, 0x14400010, 0x0200202D)
    FORCED_TRAVEL_BRANCH = 0x18
    OPEN_MAP_CALL = 0x20
    MAP_SCREEN_ARGUMENT = 0x34
    MAP_SCREEN_INSTRUCTION = 0x2404000E

    CONTINUE = 0x188
    CONTINUE_END = 0x228
    CONTINUE_END_INSTRUCTION = 0x1240000B
    CALLBACK = 0x38
    CALLBACK_HIGH = 0x158
    CALLBACK_LOW = 0x160
    CALLBACK_TRAVEL_CALL = 0x20
    CALLBACK_RETURN = 0x28
    CALLBACK_EPILOGUE = (0xDFBF0000, 0x03E00008, 0x27BD0010)


class MissionTravel(PatchSet):
    def prepare(self, symbols):
        self.patches = []
        helper, map_ender = require(
            symbols, Functions.UPDATE_CHANGE_TO_LEVEL_OR_MAP_IF_ALREADY_COMPLETED,
            Functions.SCRNGALACTICMAP_SET_LEVEL_ENDER)
        helper_patch = self._prepare_map_route(helper, map_ender)
        arena_patches = self._prepare_arena_routes(symbols, helper)
        self.patches = [helper_patch, *arena_patches]
        return self.patches

    def _expect(self, address, instructions, label):
        expected = packed(instructions)
        if self.pine.read_bytes(address, len(expected)) != expected:
            raise RuntimeError(f"{label} layout changed at {address:#x}")

    def _prepare_map_route(self, helper, map_ender):
        layout = TravelLayout
        checks = (
            (0, layout.HELPER_PROLOGUE),
            (layout.HELPER_DECISION_OFFSET, layout.HELPER_DECISION),
            (layout.OPEN_MAP_CALL, (jump(map_ender, True),)),
            (layout.MAP_SCREEN_ARGUMENT, (layout.MAP_SCREEN_INSTRUCTION,)),
        )
        for offset, expected in checks:
            self._expect(helper + offset, expected, "Mission-end travel")
        return Patch(helper + layout.FORCED_TRAVEL_BRANCH,
                     packed([layout.HELPER_DECISION[1]]), packed([0]))

    def _prepare_arena_routes(self, symbols, helper):
        update, exit_screen, next_level, set_next, change = require(
            symbols, Functions.SCRNRATCHETARENA_UPDATE, Functions.SCRNRATCHETARENA_EXIT,
            Functions.ARENA_GET_LEVEL_TO_LOAD, Functions.SET_NEXT_LEVEL,
            Functions.UPDATE_CHANGE_TO_LEVEL)
        layout = TravelLayout
        direct = update + layout.CONTINUE
        callback = exit_screen + layout.CALLBACK
        original_direct = (jump(next_level, True), 0, 0x10000014, 0x0040202D)
        checks = (
            (direct, original_direct),
            (update + layout.CONTINUE_END, (layout.CONTINUE_END_INSTRUCTION,)),
            (callback, (0x27BDFFF0, 0xFFBF0000, jump(next_level, True), 0,
                        jump(set_next, True), 0x0040202D)),
            (callback + layout.CALLBACK_TRAVEL_CALL, (jump(change, True),)),
            (callback + layout.CALLBACK_RETURN, layout.CALLBACK_EPILOGUE),
        )
        for address, expected in checks:
            self._expect(address, expected, "Ratchet completion travel")
        self._validate_registered_callback(update, callback)
        return [
            Patch(direct, packed(original_direct), packed([
                jump(helper, True), 0, branch(direct + 8, update + layout.CONTINUE_END), 0])),
            Patch(callback + layout.CALLBACK_TRAVEL_CALL,
                  packed([jump(change, True)]), packed([jump(helper, True)])),
        ]

    def _validate_registered_callback(self, update, callback):
        """Check the signed LUI/ADDIU pair points to the validated movie callback."""
        high = (callback + 0x8000) >> 16
        self._expect(update + TravelLayout.CALLBACK_HIGH,
                     (0x3C060000 | high,), "Ratchet movie callback")
        self._expect(update + TravelLayout.CALLBACK_LOW,
                     (0x24C60000 | (callback & 0xFFFF),), "Ratchet movie callback")
