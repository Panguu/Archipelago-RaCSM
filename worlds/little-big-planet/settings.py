import settings


class LBPSettings(settings.Group):
    class ScoreBubbleSanityEnabled(settings.Bool):
        """Host-level kill switch for Score Bubble Sanity: if disabled, no player's
        Score Bubble Checks option has any effect regardless of what they set in
        their own YAML. Individual pickup detection is still experimental, so this
        defaults off until a host has verified it works for their setup."""

    class RPCS3Directory(settings.OptionalUserFolderPath):
        """RPCS3 folder containing dev_hdd0. The client asks for it on first launch and
        /patch installs and enables the AP game patch there."""
        description = 'RPCS3 folder (contains rpcs3.exe and dev_hdd0)'

    score_bubble_sanity: ScoreBubbleSanityEnabled | bool = False
    rpcs3_directory: RPCS3Directory = RPCS3Directory('')
