from __future__ import annotations

from typing import TYPE_CHECKING

from ..constants import Rac5Planets
from .locations.challenge_locations import (
    ALL_CLANK_ADDRESS_MAP,
    CHALLENGE_ADDRESS_MAP,
    CLANK_SECTION_UNLOCK_ADDRESSES,
    COUNT_BASED_CHALLENGE_ADDRS,
    DAYNI_MOON_CHALLENGE_NAMES,
    GLADIATOR_FAILSAFE,
    METALIS_CHALLENGE_NAMES,
    SKYBOARD_ADDRESS_MASK_MAP,
    ChallengeSection,
    SkyboardBit,
)

if TYPE_CHECKING:
    from pypine import Pine


class ChallengeSlot:
    """Pine-backed accessor for a single challenge-completion byte at a fixed
    absolute address (addresses are scattered per-planet, not a common
    base+offset struct, so this binds directly to an address)."""

    def __init__(self, address: int) -> None:
        self.address = address

    def __get__(self, instance, owner) -> int | None:
        if instance is None:
            return None
        return instance.pine.read_int8(self.address)

    def __set__(self, instance, value) -> None:
        if instance is None:
            return
        instance.pine.write_int8(self.address, value)

    def __delete__(self, instance) -> None:
        if instance is None:
            return
        instance.pine.write_int8(self.address, 0)


class ChallengeInventory:
    """Pine-backed live accessor for every clank-challenge completion byte.

    One ChallengeSlot per AP location name, built dynamically from
    ALL_CLANK_ADDRESS_MAP. Also owns completion tracking: check() is a pull —
    call it whenever the caller decides to poll — and reports newly-completed
    AP location names, including the Ultimate Gladiator failsafe.
    """

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        self._slots: dict[str, ChallengeSlot] = {
            name: ChallengeSlot(address) for address, name in ALL_CLANK_ADDRESS_MAP.items()
        }
        self._counts: dict[str, int] = dict.fromkeys(self._slots, 0)
        self.completed: set[str] = set()
        self.gladiator_sent: set[str] = set()

    def get(self, name: str) -> int:
        return self._slots[name].__get__(self, type(self))

    def set(self, name: str, value: int) -> None:
        self._slots[name].__set__(self, value)

    def delete(self, name: str) -> None:
        self._slots[name].__delete__(self)

    def unlock_section(self, planet: str, section: ChallengeSection, value: int = 0x0F) -> None:
        """Unlock a single challenge section (Derby / Gadgetbot Toss / Gadgetbot) on a planet."""
        self.pine.write_int8(CLANK_SECTION_UNLOCK_ADDRESSES[planet][section], value)

    def setup(self, all_challenges: bool = False) -> None:
        """Unlock every section on every tracked planet and, unless every
        individual challenge is tracked, preset the non-count-based (reward)
        bytes so undetected challenges don't block sync."""
        for planet, sections in CLANK_SECTION_UNLOCK_ADDRESSES.items():
            for section in sections:
                self.unlock_section(planet, section)
        if all_challenges:
            return  # don't preset values — every completion is a check
        for slot in self._slots.values():
            if slot.address not in COUNT_BASED_CHALLENGE_ADDRS and slot.__get__(self, type(self)) == 0:
                slot.__set__(self, 1)

    def check(self, all_challenges: bool = False) -> list[str]:
        """Read every tracked byte and return newly completed AP location
        names for this call, including any gladiator failsafe locations."""
        newly: list[str] = []
        addr_map = ALL_CLANK_ADDRESS_MAP if all_challenges else CHALLENGE_ADDRESS_MAP
        for address, name in addr_map.items():
            if name in self.completed:
                continue
            count = self._slots[name].__get__(self, type(self))
            if address in COUNT_BASED_CHALLENGE_ADDRS:
                done = count > self._counts.get(name, 0)
                self._counts[name] = count
            else:
                done = count >= 2
            if done:
                self.completed.add(name)
                newly.append(name)
        newly.extend(self._check_gladiator_failsafe())
        return newly

    def _check_gladiator_failsafe(self) -> list[str]:
        """Report a planet's Ultimate Gladiator skill point once every
        individual challenge on it is complete, even if its own in-game
        detection never fired."""
        newly: list[str] = []
        if Rac5Planets.METALIS not in self.gladiator_sent and METALIS_CHALLENGE_NAMES <= self.completed:
            self.gladiator_sent.add(Rac5Planets.METALIS)
            newly.append(GLADIATOR_FAILSAFE[Rac5Planets.METALIS])
        if Rac5Planets.DAYNI_MOON not in self.gladiator_sent and DAYNI_MOON_CHALLENGE_NAMES <= self.completed:
            self.gladiator_sent.add(Rac5Planets.DAYNI_MOON)
            newly.append(GLADIATOR_FAILSAFE[Rac5Planets.DAYNI_MOON])
        return newly

    def sync(self) -> None:
        """Baseline read: populate completed/_counts without reporting anything as newly completed."""
        for address, name in ALL_CLANK_ADDRESS_MAP.items():
            count = self._slots[name].__get__(self, type(self))
            if address in COUNT_BASED_CHALLENGE_ADDRS:
                self._counts[name] = count
                if count > 0:
                    self.completed.add(name)
            elif count >= 2:
                self.completed.add(name)

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self.completed.update(name for name in checked_locations if name in ALL_CLANK_ADDRESS_MAP.values())

    def __repr__(self) -> str:
        return f"ChallengeInventory(completed={len(self.completed)}/{len(ALL_CLANK_ADDRESS_MAP)})"


class SkyboardSlot:
    """Pine-backed accessor for a single skyboard race's completion bit.

    Unlike ChallengeSlot, all four races on a planet share one completion
    byte, each owning one SkyboardBit — reads/writes mask/preserve the
    other three races' bits.
    """

    def __init__(self, address: int, mask: SkyboardBit) -> None:
        self.address = address
        self.mask = mask

    def __get__(self, instance, owner) -> bool | None:
        if instance is None:
            return None
        raw = instance.pine.read_int8(self.address)
        return bool(raw & self.mask)

    def __set__(self, instance, value: bool) -> None:
        if instance is None:
            return
        raw = instance.pine.read_int8(self.address)
        raw = (raw | self.mask) if value else (raw & ~self.mask)
        instance.pine.write_int8(self.address, raw)

    def __delete__(self, instance) -> None:
        if instance is None:
            return
        raw = instance.pine.read_int8(self.address)
        instance.pine.write_int8(self.address, raw & ~self.mask)


class SkyboardInventory:
    """Pine-backed live accessor + completion tracking for every skyboard
    race's completion bit. One SkyboardSlot per AP location name, built
    dynamically from SKYBOARD_ADDRESS_MASK_MAP."""

    def __init__(self, pine: Pine) -> None:
        self.pine = pine
        self._slots: dict[str, SkyboardSlot] = {
            name: SkyboardSlot(address, SkyboardBit(mask))
            for (address, mask), name in SKYBOARD_ADDRESS_MASK_MAP.items()
        }
        self.completed: set[str] = set()

    def get(self, name: str) -> bool:
        return bool(self._slots[name].__get__(self, type(self)))

    def set(self, name: str, value: bool) -> None:
        self._slots[name].__set__(self, value)

    def delete(self, name: str) -> None:
        self._slots[name].__delete__(self)

    def check(self) -> list[str]:
        """Read every tracked bit and return newly completed AP location names for this call."""
        newly: list[str] = []
        for name, slot in self._slots.items():
            if name in self.completed:
                continue
            if slot.__get__(self, type(self)):
                self.completed.add(name)
                newly.append(name)
        return newly

    def sync(self) -> None:
        """Baseline read: populate completed without reporting anything as newly completed."""
        for name, slot in self._slots.items():
            if slot.__get__(self, type(self)):
                self.completed.add(name)

    def sync_from_ap(self, checked_locations: set[str]) -> None:
        self.completed.update(name for name in checked_locations if name in SKYBOARD_ADDRESS_MASK_MAP.values())

    def __repr__(self) -> str:
        return f"SkyboardInventory(completed={len(self.completed)}/{len(SKYBOARD_ADDRESS_MASK_MAP)})"
