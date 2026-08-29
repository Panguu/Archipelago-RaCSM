# Star-import is deliberate here: it re-exports every public name from the
# shared registry (locations/shared.py) so the many existing
# `from ..locations import X` call sites across the world keep working
# unchanged after the split into per-planet files, with no hand-maintained
# name list that could silently drop something.
from .shared import *  # noqa: F401,F403

from . import (
    challax,
    dayni_moon,
    dreamtime,
    inside_clank,
    kalidon,
    metalis,
    outpost_omega,
    pokitaru,
    quodrona,
    ryllus,
)
