from ..model import Kind, LBPLocationData

LEVEL = 'g75388'

LOCATIONS = (
    LBPLocationData('Tales of the Little Big Crystal  - Score Bubble 1', LEVEL, Kind.SCORE, uid=22645),
    LBPLocationData('Tales of the Little Big Crystal  - Score Bubble 2', LEVEL, Kind.SCORE, uid=22853),
    LBPLocationData('Tales of the Little Big Crystal  - Score Bubble 3', LEVEL, Kind.SCORE, uid=22857),
    LBPLocationData('Tales of the Little Big Crystal  - Score Bubble 4', LEVEL, Kind.SCORE, uid=31588),
    LBPLocationData('Tales of the Little Big Crystal  - Score Bubble 5', LEVEL, Kind.SCORE, uid=31590),
    LBPLocationData('Tales of the Little Big Crystal  - Score Bubble 6', LEVEL, Kind.SCORE, uid=31592),
    LBPLocationData('Tales of the Little Big Crystal  - Score Bubble 7', LEVEL, Kind.SCORE, uid=1691679),
    LBPLocationData('Tales of the Little Big Crystal  - Score Bubble 8', LEVEL, Kind.SCORE, uid=2438166),
    LBPLocationData('Tales of the Little Big Crystal  - Score Bubble 9', LEVEL, Kind.SCORE, uid=2438248),
    LBPLocationData('Tales of the Little Big Crystal  - Score Bubble 10', LEVEL, Kind.SCORE, uid=2438323),
    LBPLocationData('Tales of the Little Big Crystal  - Prize Bubble 1 - Flower 3', LEVEL, Kind.PRIZE, uid=5260412, plan='g77017'),
    LBPLocationData('Tales of the Little Big Crystal  - Prize Bubble 2 - Yellow Crystal', LEVEL, Kind.PRIZE, uid=5814042, plan='g77019'),
    LBPLocationData('Tales of the Little Big Crystal  - Prize Bubble 3 - Green Crystal', LEVEL, Kind.PRIZE, uid=5894734, plan='g77021'),
    LBPLocationData('Tales of the Little Big Crystal  - Prize Bubble 4 - Blue Crystal', LEVEL, Kind.PRIZE, uid=5907608, plan='g77022'),
    LBPLocationData('Tales of the Little Big Crystal  - Prize Bubble 5 - Unresolved prize g77024', LEVEL, Kind.PRIZE, uid=5910618, plan='g77024'),
    LBPLocationData('Tales of the Little Big Crystal  - Prize Bubble 6 - Red Crystal', LEVEL, Kind.PRIZE, uid=5911247, plan='g77025'),
    LBPLocationData('Tales of the Little Big Crystal  - Prize Bubble 7 - Green Grass', LEVEL, Kind.PRIZE, uid=5920510, plan='g77026'),
    LBPLocationData('Tales of the Little Big Crystal  - Prize Bubble 8 - White Crystal', LEVEL, Kind.PRIZE, uid=5922287, plan='g77027'),
    LBPLocationData('Tales of the Little Big Crystal  - Prize Bubble 9 - Pinky Snake', LEVEL, Kind.PRIZE, uid=5922700, plan='g77028'),
    LBPLocationData('Tales of the Little Big Crystal  - Prize Bubble 10 - Purple Crystal', LEVEL, Kind.PRIZE, uid=5930441, plan='g77029'),
    LBPLocationData('Tales of the Little Big Crystal  - Prize Bubble 11 - Flower 2', LEVEL, Kind.PRIZE, uid=5931283, plan='g77030'),
    LBPLocationData('Tales of the Little Big Crystal  - Prize Bubble 12 - Flower 1', LEVEL, Kind.PRIZE, uid=5933049, plan='g77031'),
    LBPLocationData('Tales of the Little Big Crystal  - Prize Bubble 13 - Dragon Head Entrance', LEVEL, Kind.PRIZE, uid=6400701, plan='g77032'),
    LBPLocationData('Tales of the Little Big Crystal  - Level Complete', LEVEL, Kind.COMPLETE),
    LBPLocationData('Tales of the Little Big Crystal  - All Prize Bubbles', LEVEL, Kind.ALL_PRIZES),
    LBPLocationData('Tales of the Little Big Crystal  - Ace (No Deaths)', LEVEL, Kind.ACE),
    LBPLocationData('Tales of the Little Big Crystal  - Completion Reward 1 - Dragon Head ', LEVEL, Kind.REWARD, plan='g77033', condition=Kind.COMPLETE),
    LBPLocationData('Tales of the Little Big Crystal  - All Prizes Reward 1 - Dark Dragon ', LEVEL, Kind.REWARD, plan='g77034', condition=Kind.ALL_PRIZES),
)
