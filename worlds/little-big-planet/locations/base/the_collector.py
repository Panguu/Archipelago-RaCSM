from ..model import Kind, LBPLocationData

LEVEL = 'g48456'

LOCATIONS = (
    LBPLocationData("The Collector - Prize Bubble 1 - 'The Battle on the Ice'", LEVEL, Kind.PRIZE, uid=536289, plan='g33156'),
    LBPLocationData('The Collector - Level Complete', LEVEL, Kind.COMPLETE),
    LBPLocationData('The Collector - All Prize Bubbles', LEVEL, Kind.ALL_PRIZES),
    LBPLocationData('The Collector - Ace (No Deaths)', LEVEL, Kind.ACE),
    LBPLocationData('The Collector - Completion Reward 1 - The Collector Boss', LEVEL, Kind.REWARD, plan='g59289', condition=Kind.COMPLETE),
    LBPLocationData("The Collector - Completion Reward 2 - The Collector's Pod", LEVEL, Kind.REWARD, plan='g52903', condition=Kind.COMPLETE),
    LBPLocationData('The Collector - Completion Reward 3 - The Collector', LEVEL, Kind.REWARD, plan='g52904', condition=Kind.COMPLETE),
    LBPLocationData('The Collector - Ace Reward 1 - Yellow Head', LEVEL, Kind.REWARD, plan='g32378', condition=Kind.ACE),
)
