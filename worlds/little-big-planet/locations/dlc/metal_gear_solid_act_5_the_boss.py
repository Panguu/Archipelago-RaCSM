from ..model import Kind, LBPLocationData

LEVEL = 'g67155'

LOCATIONS = (
    LBPLocationData("METAL GEAR SOLID® Act 5: The Boss - Prize Bubble 1 - MGS1 'Encounter (LBP remix)'", LEVEL, Kind.PRIZE, uid=66501, plan='g67535'),
    LBPLocationData('METAL GEAR SOLID® Act 5: The Boss - Level Complete', LEVEL, Kind.COMPLETE),
    LBPLocationData('METAL GEAR SOLID® Act 5: The Boss - All Prize Bubbles', LEVEL, Kind.ALL_PRIZES),
    LBPLocationData('METAL GEAR SOLID® Act 5: The Boss - Ace (No Deaths)', LEVEL, Kind.ACE),
    LBPLocationData('METAL GEAR SOLID® Act 5: The Boss - Completion Reward 1 - Young Snake Body', LEVEL, Kind.REWARD, plan='g65774', condition=Kind.COMPLETE),
    LBPLocationData('METAL GEAR SOLID® Act 5: The Boss - Completion Reward 2 - Young Snake Arm', LEVEL, Kind.REWARD, plan='g65775', condition=Kind.COMPLETE),
    LBPLocationData('METAL GEAR SOLID® Act 5: The Boss - Completion Reward 3 - Big Bullet Hole', LEVEL, Kind.REWARD, plan='g66622', condition=Kind.COMPLETE),
    LBPLocationData('METAL GEAR SOLID® Act 5: The Boss - Ace Reward 1 - Metal Gear Ray Head', LEVEL, Kind.REWARD, plan='g66185', condition=Kind.ACE),
    LBPLocationData('METAL GEAR SOLID® Act 5: The Boss - Ace Reward 2 - Green Preying Mantis', LEVEL, Kind.REWARD, plan='g65704', condition=Kind.ACE),
    LBPLocationData('METAL GEAR SOLID® Act 5: The Boss - Ace Reward 3 - Liquid Snake', LEVEL, Kind.REWARD, plan='g65699', condition=Kind.ACE),
)
