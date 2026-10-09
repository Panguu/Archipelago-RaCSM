"""Return mission completion to the current level, including Ratchet movies."""
from ...constants.native_functions import NativeFunctions as Functions
from ...constants.missions import NATIVE_FINISH_CASES
from ..symbols import require
from .asm import Patch, branch, jump, packed
from .patch import PatchSet
from . import mips as m


class TravelLayout:
    HELPER_PROLOGUE = (0x27BDFFF0, 0xFFB00000, 0xFFBF0008)
    HELPER_DECISION_OFFSET = 0x14
    HELPER_DECISION = (0x0050102B, 0x14400010, 0x0200202D)
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
    def prepare(self, symbols, *, module=None):
        self.patches = []
        self.completion_mailbox = None
        helper, map_ender = require(
            symbols, Functions.UPDATE_CHANGE_TO_LEVEL_OR_MAP_IF_ALREADY_COMPLETED,
            Functions.SCRNGALACTICMAP_SET_LEVEL_ENDER)
        change = require(symbols, Functions.UPDATE_CHANGE_TO_LEVEL)
        helper_patch = self._prepare_current_level_route(helper, map_ender, change)
        arena_patches = self._prepare_arena_routes(symbols, helper)
        self.patches = [helper_patch, *arena_patches]
        self.patches.extend(self._prepare_story_routes(symbols, helper, change))
        if module in NATIVE_FINISH_CASES:
            # These task predicates are the *next* case's intro flag. Record
            # the actual finish here and let the host capture it before reload
            # can discard this DLL. Returning success leaves the game running.
            mailbox = helper + 0x70
            self._expect(helper + 0x68, (0xDFBF0008, 0x03E00008, 0x27BD0010),
                         "Mission completion mailbox")
            code = packed([*m.li32(m.T0, mailbox), m.addiu(m.T1, m.ZERO, 1),
                           m.sw(m.T1, 0, m.T0), m.jr(m.RA), m.addiu(m.V0, m.ZERO, 1)])
            self.patches[0] = Patch(helper, self.pine.read_bytes(helper, len(code)), code)
            self.patches.append(Patch(mailbox, packed([0x27BD0010]), packed([0])))
            self.completion_mailbox = mailbox
        return self.patches

    def _prepare_story_routes(self, symbols, helper, change):
        """Result-screen Continue paths bypass the shared completion helper."""
        edits = []
        highest = symbols.get("GLOBALVARS_GetHighestLevelCanGoTo__Fv")
        for name, offset in (("SCRNGADGETBOTARENA_Update__Fv", 0x124),
                             ("SCRNVEHICLECHALLENGES_Update__Fv", 0x20C)):
            address = symbols.get(name)
            if address is None:
                continue
            if highest is None:
                raise ValueError("Missing story destination export")
            site = address + offset
            self._expect(site, (jump(highest, True), 0, 0x0040202D,
                                jump(change, True), 0x24050001), "Story Continue travel")
            edits.append(Patch(site + 12, packed([jump(change, True)]),
                               packed([jump(helper, True)])))

        vehicle = symbols.get("SCRNVEHICLECHALLENGES_Exit__Fv")
        update = symbols.get("SCRNVEHICLECHALLENGES_Update__Fv")
        if vehicle is not None and update is not None:
            callback = vehicle + 0x90
            self._expect(update + 0x1E4, (0x3C060000 | ((callback + 0x8000) >> 16),
                                         0x0200202D, 0x24C60000 | (callback & 0xFFFF)),
                         "Vehicle movie callback registration")
            if highest is None:
                raise ValueError("Missing story destination export")
            self._expect(callback, (0x27BDFFF0, 0xFFBF0000, jump(highest, True), 0,
                                   0x0040202D, jump(change, True), 0x24050001,
                                   0xDFBF0000, 0x03E00008, 0x27BD0010),
                         "Vehicle movie completion travel")
            edits.append(Patch(callback + 0x14, packed([jump(change, True)]),
                               packed([jump(helper, True)])))

        movie = symbols.get("SCRNGALACTICMAP_Level5MovieHackFinishedCallback__FPv")
        if movie is not None:
            self._expect(movie, (0x27BDFFF0, 0x2404000F, 0xFFBF0000, jump(change, True),
                                 0x24050001, 0xDFBF0000, 0x03E00008, 0x27BD0010),
                         "Story movie completion travel")
            edits.append(Patch(movie + 12, packed([jump(change, True)]),
                               packed([jump(helper, True)])))
        return edits

    def _expect(self, address, instructions, label):
        expected = packed(instructions)
        if self.pine.read_bytes(address, len(expected)) != expected:
            raise RuntimeError(f"{label} layout changed at {address:#x}")

    def _prepare_current_level_route(self, helper, map_ender, change):
        layout = TravelLayout
        checks = (
            (0, layout.HELPER_PROLOGUE),
            (layout.HELPER_DECISION_OFFSET, layout.HELPER_DECISION),
            (layout.OPEN_MAP_CALL, (jump(map_ender, True),)),
            (layout.MAP_SCREEN_ARGUMENT, (layout.MAP_SCREEN_INSTRUCTION,)),
        )
        for offset, expected in checks:
            self._expect(helper + offset, expected, "Mission-end travel")
        # Tail-call the native reload with the resident current module, not the
        # story destination passed by the caller or left by SetNextLevel.
        # Do not call SetLevelEnder: its mandatory map exit can travel onward.
        # The shared-module operative flags are left intact.
        replacement = packed([0x3C040020, 0x8C846328,
                              jump(change), 0x24050001])
        return Patch(helper, self.pine.read_bytes(helper, len(replacement)), replacement)

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
