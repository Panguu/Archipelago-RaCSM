from ..model import Kind, LBPLocationData

LEVEL = 'g89109'

LOCATIONS = (
    LBPLocationData('Global Water Object - Prize Bubble 1 - Global Water Object', LEVEL, Kind.PRIZE, uid=32534761, plan='g71977'),
    LBPLocationData('Global Water Object - Level Complete', LEVEL, Kind.COMPLETE),
    LBPLocationData('Global Water Object - All Prize Bubbles', LEVEL, Kind.ALL_PRIZES),
    LBPLocationData('Global Water Object - Ace (No Deaths)', LEVEL, Kind.ACE),
)
