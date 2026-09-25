from ..model import Kind, LBPLocationData

LEVEL = 'g101477'

LOCATIONS = (
    LBPLocationData('Marvel™ Issue 4 - Rocket Rampage - Level Complete', LEVEL, Kind.COMPLETE),
    LBPLocationData('Marvel™ Issue 4 - Rocket Rampage - Ace (No Deaths)', LEVEL, Kind.ACE),
    LBPLocationData('Marvel™ Issue 4 - Rocket Rampage - Completion Reward 1 - Marvel™ Montage', LEVEL, Kind.REWARD, plan='g89783', condition=Kind.COMPLETE),
    LBPLocationData('Marvel™ Issue 4 - Rocket Rampage - Completion Reward 2 - Bam!', LEVEL, Kind.REWARD, plan='g100644', condition=Kind.COMPLETE),
    LBPLocationData('Marvel™ Issue 4 - Rocket Rampage - Completion Reward 3 - Explosion', LEVEL, Kind.REWARD, plan='g93300', condition=Kind.COMPLETE),
    LBPLocationData('Marvel™ Issue 4 - Rocket Rampage - All Prizes Reward 1 - Unimpressed Daredevil', LEVEL, Kind.REWARD, plan='g93268', condition=Kind.ALL_PRIZES),
    LBPLocationData('Marvel™ Issue 4 - Rocket Rampage - All Prizes Reward 2 - Spider-Man', LEVEL, Kind.REWARD, plan='g93286', condition=Kind.ALL_PRIZES),
    LBPLocationData('Marvel™ Issue 4 - Rocket Rampage - All Prizes Reward 3 - Ghost Rider', LEVEL, Kind.REWARD, plan='g93203', condition=Kind.ALL_PRIZES),
    LBPLocationData('Marvel™ Issue 4 - Rocket Rampage - Ace Reward 1 - Spider-Man Arm', LEVEL, Kind.REWARD, plan='g93234', condition=Kind.ACE),
    LBPLocationData('Marvel™ Issue 4 - Rocket Rampage - Ace Reward 2 - Spider-Man Leg', LEVEL, Kind.REWARD, plan='g93235', condition=Kind.ACE),
    LBPLocationData('Marvel™ Issue 4 - Rocket Rampage - Ace Reward 3 - Spider-Man Torso', LEVEL, Kind.REWARD, plan='g93236', condition=Kind.ACE),
)
