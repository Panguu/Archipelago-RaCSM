from typing import TYPE_CHECKING, Any

from .constants import SACOperatives
from .options import SLOT_DATA_OPTIONS

if TYPE_CHECKING:
    from .world import SecretAgentClankWorld


def setup_options_from_slot_data(world: "SecretAgentClankWorld") -> None:
    passthrough: dict[str, Any] | None = getattr(world.multiworld, "re_gen_passthrough", {}).get(world.game)
    world.using_ut = passthrough is not None
    if passthrough is None:
        return
    world.passthrough = passthrough
    for name in SLOT_DATA_OPTIONS:
        value = passthrough[name]
        if isinstance(value, dict):
            value = dict(value)  # option dicts only take a plain dict, not the Counter as_dict gives
        setattr(world.options, name, type(getattr(world.options, name)).from_any(value))
    # slot_data lists every playable operative; the option only holds the optional ones.
    world.options.operatives.value = {name: amount for name, amount in passthrough["operatives"].items()
                                      if name != SACOperatives.CLANK}
