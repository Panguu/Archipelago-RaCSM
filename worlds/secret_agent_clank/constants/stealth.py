from .planets import SACCases

STEALTH_MAX_PER_CASE = 10


class SACStealth:
    BOLTAIRE_MUSEUM = "Boltaire (Clank) - Boltaire Museum: Stealth Takedown {count}"
    ASYANICA_ROOFTOPS = "Asyanica (Clank) - Asyanica Rooftops: Stealth Takedown {count}"
    AZCOTAL_ALLEY = "Rionosis (Clank) - Azcotal Alley: Stealth Takedown {count}"
    HIGH_ROLLERS_CASINO = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Stealth Takedown {count}"
    VENANTONIO_LABS = "Venantonio (Clank) - Venantonio Labs: Stealth Takedown {count}"
    GALACTIC_BOLT_RESERVE = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Stealth Takedown {count}"
    SPACESHIP_GRAVEYARD = "Spaceship Graveyard (Clank) - Spaceship Graveyard: Stealth Takedown {count}"
    UNDERWATER_BUNKER = "Hydrano (Clank) - Underwater Bunker: Stealth Takedown {count}"


STEALTH_CASES: dict[str, str] = {
    SACCases.BOLTAIRE_MUSEUM: SACStealth.BOLTAIRE_MUSEUM,
    SACCases.ASYANICA_ROOFTOPS: SACStealth.ASYANICA_ROOFTOPS,
    SACCases.AZCOTAL_ALLEY: SACStealth.AZCOTAL_ALLEY,
    SACCases.HIGH_ROLLERS_CASINO: SACStealth.HIGH_ROLLERS_CASINO,
    SACCases.VENANTONIO_LABS: SACStealth.VENANTONIO_LABS,
    SACCases.GALACTIC_BOLT_RESERVE: SACStealth.GALACTIC_BOLT_RESERVE,
    SACCases.SPACESHIP_GRAVEYARD: SACStealth.SPACESHIP_GRAVEYARD,
    SACCases.UNDERWATER_BUNKER: SACStealth.UNDERWATER_BUNKER,
}


def stealth_check_count(case, setting):
    return min(setting, STEALTH_MAX_PER_CASE) if case in STEALTH_CASES else 0


def stealth_location_name(case, count):
    return STEALTH_CASES[case].format(count=count)
