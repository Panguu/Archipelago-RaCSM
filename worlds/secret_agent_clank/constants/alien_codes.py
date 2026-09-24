"""27 Alien Codes: three each in nine native modules."""
from dataclasses import dataclass

from .planets import SACCases
from .types import CaseStructure, SACTags, group_by_case, with_display_names


@dataclass(frozen=True)
class SACAlienCodes:
    """String constants for each Alien Code's title (short form only -- see ALIEN_CODES below for which case/address each belongs to)."""

    THE_LEGENDS = "The Legends"
    RONNS_SECRET = "Ronn's secret"
    BENS_SECRET = "Ben's secret"
    JHAIROS_SECRET = "Jhairo's secret"
    GILBERTS_SECRET = "Gilbert's secret"
    RICARDOS_SECRET = "Ricardo's secret"
    LEVITICUS_SECRET = "Leviticus' secret"
    CARLS_SECRET = "Carl's secret"
    JESS_SECRET = "Jess' secret"
    JONS_SECRET = "Jon's secret"
    THE_3_JASONS_SECRET = "The 3 Jasons' secret"
    TRAVIS_SECRET = "Travis' secret"
    COLINS_SECRET = "Colin's secret"
    SHANES_SECRET = "Shane's secret"
    THE_PING_PONG_SECRET = "The Ping Pong Secret"
    GERARDS_SECRET = "Gerard's secret"
    ALEXS_SECRET = "Alex's secret"
    HAROONS_SECRET = "Haroon's secret"
    AVERYS_SECRET = "Avery's secret"
    LESLEYS_SECRET = "Lesley's secret"
    DAVES_SECRET = "Dave's secret"
    MATTS_SECRET = "Matt's secret"
    KENS_SECRET = "Ken's secret"
    JAREDS_SECRET = "Jared's secret"
    VESSUPS_SECRET = "Vessup's secret"
    ADAMS_SECRET = "Adam's secret"
    JEFFS_SECRET = "Jeff's secret"


_RAW_ALIEN_CODES: tuple[CaseStructure, ...] = (
    # Boltaire Museum -- confirmed case (exact name match).
    CaseStructure(SACCases.BOLTAIRE_MUSEUM, SACAlienCodes.THE_LEGENDS, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.BOLTAIRE_MUSEUM, SACAlienCodes.RONNS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.BOLTAIRE_MUSEUM, SACAlienCodes.BENS_SECRET, SACTags.ALIEN_CODE),

    # Asyanica, Skyline Rooftops -- TODO: no exact case match (closest is
    # Asyanica Rooftops, case_id 5, but the name doesn't match cleanly).
    CaseStructure(SACCases.ASYANICA_ROOFTOPS, SACAlienCodes.JHAIROS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.ASYANICA_ROOFTOPS, SACAlienCodes.GILBERTS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.ASYANICA_ROOFTOPS, SACAlienCodes.RICARDOS_SECRET, SACTags.ALIEN_CODE),

    # Rionosis, Mountainside Ascent -- TODO: no matching case at all yet.
    CaseStructure(SACCases.GONDOLA_ASCENT, SACAlienCodes.LEVITICUS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.GONDOLA_ASCENT, SACAlienCodes.CARLS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.GONDOLA_ASCENT, SACAlienCodes.JESS_SECRET, SACTags.ALIEN_CODE),

    # Rionosis, Azcotal Alley -- case exists (Azcotal Alley), but
    # planets.py currently files it under Glaciara (LOW CONFIDENCE); this
    # data implies Rionosis instead. Used as-is -- see module docstring.
    CaseStructure(SACCases.AZCOTAL_ALLEY, SACAlienCodes.JONS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.AZCOTAL_ALLEY, SACAlienCodes.THE_3_JASONS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.AZCOTAL_ALLEY, SACAlienCodes.TRAVIS_SECRET, SACTags.ALIEN_CODE),

    # Casino "Le Paradis des tricheurs" -- TODO: ambiguous between
    # High-Rollers Casino and High Stakes Room, both on this planet.
    CaseStructure(SACCases.HIGH_ROLLERS_CASINO, SACAlienCodes.COLINS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.HIGH_ROLLERS_CASINO, SACAlienCodes.SHANES_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.HIGH_ROLLERS_CASINO, SACAlienCodes.THE_PING_PONG_SECRET, SACTags.ALIEN_CODE),

    # Labos de Venantonio (= Venantonio Labs) -- confirmed case.
    CaseStructure(SACCases.VENANTONIO_LABS, SACAlienCodes.GERARDS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.VENANTONIO_LABS, SACAlienCodes.ALEXS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.VENANTONIO_LABS, SACAlienCodes.HAROONS_SECRET, SACTags.ALIEN_CODE),

    # Fort Sprocket, Galactic Bolt Reserve -- case exists (exact name
    # match), but planets.py currently files it under Venantonio (LOW
    # CONFIDENCE); this data implies Fort Sprocket instead. Used as-is --
    # see module docstring.
    CaseStructure(SACCases.GALACTIC_BOLT_RESERVE, SACAlienCodes.AVERYS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.GALACTIC_BOLT_RESERVE, SACAlienCodes.LESLEYS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.GALACTIC_BOLT_RESERVE, SACAlienCodes.DAVES_SECRET, SACTags.ALIEN_CODE),

    # Spaceship Graveyard -- confirmed case (exact name match).
    CaseStructure(SACCases.SPACESHIP_GRAVEYARD, SACAlienCodes.MATTS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.SPACESHIP_GRAVEYARD, SACAlienCodes.KENS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.SPACESHIP_GRAVEYARD, SACAlienCodes.JAREDS_SECRET, SACTags.ALIEN_CODE),

    # Hydrano, Underwater base -- TODO: closest is Underwater Bunker
    # (case_id 29), but the name doesn't match cleanly.
    CaseStructure(SACCases.UNDERWATER_BUNKER, SACAlienCodes.VESSUPS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.UNDERWATER_BUNKER, SACAlienCodes.ADAMS_SECRET, SACTags.ALIEN_CODE),
    CaseStructure(SACCases.UNDERWATER_BUNKER, SACAlienCodes.JEFFS_SECRET, SACTags.ALIEN_CODE),
)


# Native module IDs from GLOBALVARS_GetTotalAlienCodeCount, not catalog IDs.
ALIEN_CODE_MODULES = {
    SACCases.BOLTAIRE_MUSEUM: 1, SACCases.ASYANICA_ROOFTOPS: 4,
    SACCases.AZCOTAL_ALLEY: 10, SACCases.GONDOLA_ASCENT: 11,
    SACCases.HIGH_ROLLERS_CASINO: 13, SACCases.VENANTONIO_LABS: 16,
    SACCases.GALACTIC_BOLT_RESERVE: 19, SACCases.SPACESHIP_GRAVEYARD: 22,
    SACCases.UNDERWATER_BUNKER: 29,
}


@dataclass(frozen=True)
class SACAlienCodeLocations:
    BOLTAIRE_MUSEUM_THE_LEGENDS = "Boltaire (Clank) - Boltaire Museum: Alien Code: The Legends"
    BOLTAIRE_MUSEUM_RONNS_SECRET = "Boltaire (Clank) - Boltaire Museum: Alien Code: Ronn's secret"
    BOLTAIRE_MUSEUM_BENS_SECRET = "Boltaire (Clank) - Boltaire Museum: Alien Code: Ben's secret"
    ASYANICA_ROOFTOPS_JHAIROS_SECRET = "Asyanica (Clank) - Asyanica Rooftops: Alien Code: Jhairo's secret"
    ASYANICA_ROOFTOPS_GILBERTS_SECRET = "Asyanica (Clank) - Asyanica Rooftops: Alien Code: Gilbert's secret"
    ASYANICA_ROOFTOPS_RICARDOS_SECRET = "Asyanica (Clank) - Asyanica Rooftops: Alien Code: Ricardo's secret"
    GONDOLA_ASCENT_LEVITICUS_SECRET = "Rionosis (Clank) - Gondola Ascent: Alien Code: Leviticus' secret"
    GONDOLA_ASCENT_CARLS_SECRET = "Rionosis (Clank) - Gondola Ascent: Alien Code: Carl's secret"
    GONDOLA_ASCENT_JESS_SECRET = "Rionosis (Clank) - Gondola Ascent: Alien Code: Jess' secret"
    AZCOTAL_ALLEY_JONS_SECRET = "Rionosis (Clank) - Azcotal Alley: Alien Code: Jon's secret"
    AZCOTAL_ALLEY_THE_3_JASONS_SECRET = "Rionosis (Clank) - Azcotal Alley: Alien Code: The 3 Jasons' secret"
    AZCOTAL_ALLEY_TRAVIS_SECRET = "Rionosis (Clank) - Azcotal Alley: Alien Code: Travis' secret"
    HIGH_ROLLERS_CASINO_COLINS_SECRET = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Alien Code: Colin's secret"
    HIGH_ROLLERS_CASINO_SHANES_SECRET = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Alien Code: Shane's secret"
    HIGH_ROLLERS_CASINO_THE_PING_PONG_SECRET = "The Paradis Des Tricheurs Casino (Clank) - High-Rollers Casino: Alien Code: The Ping Pong Secret"
    VENANTONIO_LABS_GERARDS_SECRET = "Venantonio (Clank) - Venantonio Labs: Alien Code: Gerard's secret"
    VENANTONIO_LABS_ALEXS_SECRET = "Venantonio (Clank) - Venantonio Labs: Alien Code: Alex's secret"
    VENANTONIO_LABS_HAROONS_SECRET = "Venantonio (Clank) - Venantonio Labs: Alien Code: Haroon's secret"
    GALACTIC_BOLT_RESERVE_AVERYS_SECRET = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Alien Code: Avery's secret"
    GALACTIC_BOLT_RESERVE_LESLEYS_SECRET = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Alien Code: Lesley's secret"
    GALACTIC_BOLT_RESERVE_DAVES_SECRET = "Fort Sprocket (Clank) - Galactic Bolt Reserve: Alien Code: Dave's secret"
    SPACESHIP_GRAVEYARD_MATTS_SECRET = "Spaceship Graveyard (Clank) - Spaceship Graveyard: Alien Code: Matt's secret"
    SPACESHIP_GRAVEYARD_KENS_SECRET = "Spaceship Graveyard (Clank) - Spaceship Graveyard: Alien Code: Ken's secret"
    SPACESHIP_GRAVEYARD_JAREDS_SECRET = "Spaceship Graveyard (Clank) - Spaceship Graveyard: Alien Code: Jared's secret"
    UNDERWATER_BUNKER_VESSUPS_SECRET = "Hydrano (Clank) - Underwater Bunker: Alien Code: Vessup's secret"
    UNDERWATER_BUNKER_ADAMS_SECRET = "Hydrano (Clank) - Underwater Bunker: Alien Code: Adam's secret"
    UNDERWATER_BUNKER_JEFFS_SECRET = "Hydrano (Clank) - Underwater Bunker: Alien Code: Jeff's secret"


ALIEN_CODES: tuple[CaseStructure, ...] = with_display_names(_RAW_ALIEN_CODES, SACAlienCodeLocations)

# Every Alien Code confirmed to a real case, grouped by case name -- feeds
# locations.py's ALIEN_CODE_LOCATIONS. Excludes the still-TODO entries
# above (see module docstring).
ALIEN_CODES_BY_CASE: dict[str, tuple[str, ...]] = group_by_case(
    tuple(entry for entry in ALIEN_CODES if entry.case_name != "TODO")
)
