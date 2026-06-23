from abc import ABC, abstractmethod


class MemoryInterface(ABC):

    @abstractmethod
    def read(self, address: int, size: int) -> bytes:
        ...

    @abstractmethod
    def write(self, address: int, data: bytes) -> None:
        ...

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass
