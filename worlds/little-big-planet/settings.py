import settings


class LBPSettings(settings.Group):
    class ScoreBubbleSanityEnabled(settings.Bool):
        """Host-level kill switch for Score Bubble Sanity: if disabled, no player's
        Score Bubble Checks option has any effect regardless of what they set in
        their own YAML. Individual pickup detection is still experimental, so this
        defaults off until a host has verified it works for their setup."""

    score_bubble_sanity: ScoreBubbleSanityEnabled | bool = False
