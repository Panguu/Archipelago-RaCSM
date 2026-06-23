from __future__ import annotations

from .memory.accessor import MemoryAccessor
from .memory.base import MemoryInterface
from .memory.poller import MemoryPoller
from .memory.writer import MemoryWriter
from .state.base_state import BaseState
from .storage.local import LocalStorage
from .structs.address_map import AddressMap


class Orchestrator:

    def __init__(
        self,
        interface: MemoryInterface,
        address_map: AddressMap,
        poll_rate: float = 0.05,
        storage: LocalStorage | None = None,
    ) -> None:
        self._storage  = storage or LocalStorage()
        self._writer   = MemoryWriter(interface)
        self._accessor = MemoryAccessor(self._writer)
        self._poller   = MemoryPoller(self._writer, interval=poll_rate)
        self._states: dict[str, BaseState] = {}
        self._current_state: str | None = None

        interface.connect()
        self._register_struct_watchers(address_map)

    def register_states(self, states: dict[str, BaseState]) -> None:
        self._states = states

    def transition(self, state_name: str) -> None:
        if self._current_state and self._current_state in self._states:
            self._states[self._current_state].exit()
        if state_name not in self._states:
            raise KeyError(f"Unknown state: {state_name!r}")
        self._current_state = state_name
        self._states[state_name].enter()

    def swap_interface(self, interface: MemoryInterface, address_map: AddressMap) -> None:
        self._poller.clear()
        self._writer.swap_interface(interface)

        for state in self._states.values():
            state.set_addresses(address_map)

        self._register_struct_watchers(address_map)

    def poll(self) -> None:
        self._poller.poll_once()

    def start_polling(self) -> None:
        self._poller.start()

    def stop_polling(self) -> None:
        self._poller.stop()

    def sync_all(self) -> None:
        for state in self._states.values():
            state.sync()

    @property
    def accessor(self) -> MemoryAccessor:
        return self._accessor

    @property
    def storage(self) -> LocalStorage:
        return self._storage

    @property
    def current_state(self) -> str | None:
        return self._current_state

    def _register_struct_watchers(self, address_map: AddressMap) -> None:
        for struct_cls in address_map.structs():
            self._poller.prime(struct_cls.BASE_ADDRESS, struct_cls.size())

    def __repr__(self) -> str:
        return (
            f"Orchestrator("
            f"states={list(self._states)}, "
            f"current={self._current_state!r})"
        )
