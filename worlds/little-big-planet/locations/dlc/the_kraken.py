from ..model import Kind, LBPLocationData

LEVEL = 'g89123'

LOCATIONS = (
    LBPLocationData('The Kraken!!! - Prize Bubble 1 - Davy Jones', LEVEL, Kind.PRIZE, uid=328217, plan='g89068'),
    LBPLocationData('The Kraken!!! - Prize Bubble 2 - Paddle Boat', LEVEL, Kind.PRIZE, uid=331676, plan='g91957'),
    LBPLocationData('The Kraken!!! - Prize Bubble 3 - Port Royal House', LEVEL, Kind.PRIZE, uid=331677, plan='g91958'),
    LBPLocationData('The Kraken!!! - Prize Bubble 4 - Skull Chest', LEVEL, Kind.PRIZE, uid=331678, plan='g91959'),
    LBPLocationData('The Kraken!!! - Level Complete', LEVEL, Kind.COMPLETE),
    LBPLocationData('The Kraken!!! - All Prize Bubbles', LEVEL, Kind.ALL_PRIZES),
    LBPLocationData('The Kraken!!! - Ace (No Deaths)', LEVEL, Kind.ACE),
    LBPLocationData('The Kraken!!! - Completion Reward 1 - Barbossa', LEVEL, Kind.REWARD, plan='g89071', condition=Kind.COMPLETE),
    LBPLocationData('The Kraken!!! - Completion Reward 2 - Skull Chest', LEVEL, Kind.REWARD, plan='g85534', condition=Kind.COMPLETE),
    LBPLocationData("The Kraken!!! - Completion Reward 3 - Ship's Lantern", LEVEL, Kind.REWARD, plan='g85533', condition=Kind.COMPLETE),
    LBPLocationData("The Kraken!!! - All Prizes Reward 1 - Ship's Bell", LEVEL, Kind.REWARD, plan='g82184', condition=Kind.ALL_PRIZES),
    LBPLocationData('The Kraken!!! - All Prizes Reward 2 - Pirate Ship', LEVEL, Kind.REWARD, plan='g85710', condition=Kind.ALL_PRIZES),
    LBPLocationData('The Kraken!!! - All Prizes Reward 3 - Skull Flag', LEVEL, Kind.REWARD, plan='g85535', condition=Kind.ALL_PRIZES),
    LBPLocationData('The Kraken!!! - Ace Reward 1 - Sea Serpent Tail', LEVEL, Kind.REWARD, plan='g85703', condition=Kind.ACE),
    LBPLocationData('The Kraken!!! - Ace Reward 2 - Sea Serpent Body', LEVEL, Kind.REWARD, plan='g85706', condition=Kind.ACE),
    LBPLocationData('The Kraken!!! - Ace Reward 3 - Sea Serpent Head', LEVEL, Kind.REWARD, plan='g85705', condition=Kind.ACE),
)
