from ..model import Kind, LBPLocationData

LEVEL = 'g89110'

LOCATIONS = (
    LBPLocationData('Water Switch - Prize Bubble 1 - Water Switch', LEVEL, Kind.PRIZE, uid=32535396, plan='g75694'),
    LBPLocationData('Water Switch - Prize Bubble 2 - Scuba Gear', LEVEL, Kind.PRIZE, uid=32537191, plan='g74458'),
    LBPLocationData('Water Switch - Level Complete', LEVEL, Kind.COMPLETE),
    LBPLocationData('Water Switch - All Prize Bubbles', LEVEL, Kind.ALL_PRIZES),
    LBPLocationData('Water Switch - Ace (No Deaths)', LEVEL, Kind.ACE),
)
