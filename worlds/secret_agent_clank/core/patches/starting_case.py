from ...constants import ALL_CASES


class StartingCase:
    INIT = 0x331700
    CALLS = (0x365F58, 0x3660C4)
    TRAVEL_CALLS = (0x349774, 0x349A30, 0x349E3C)
    CHANGE_LEVEL = 0x330388

    def __init__(self):
        self.case_name = None

    def configure(self, slot_data):
        name = slot_data.get("starting_case")
        if name is not None:
            case = next((case for case in ALL_CASES if case.name == name), None)
            if case is None or not slot_data.get("operatives", {}).get(case.operative, 0):
                raise ValueError(f"Invalid or disabled starting case: {name!r}")
        self.case_name = name
