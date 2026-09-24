"""No The Mess Hall-specific items yet -- see items/__init__.py's ALL_ITEMS for what's actually in the pool today (built from flat category tables, not per-case)."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import SACItemData

THE_MESS_HALL_ITEMS: dict[str, "SACItemData"] = {}
