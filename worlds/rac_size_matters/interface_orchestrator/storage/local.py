from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


class LocalStorage:

    def __init__(self, persist_path: Path | str | None = None) -> None:
        self._store: dict[str, Any] = {}
        self._lock = threading.Lock()
        self._path = Path(persist_path) if persist_path else None

        if self._path and self._path.exists():
            self._load()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._store.get(key, default)

    def get_all(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._store)

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._store

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = value

    def set_many(self, data: dict[str, Any]) -> None:
        with self._lock:
            self._store.update(data)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def save(self) -> None:
        if not self._path:
            return
        with self._lock:
            self._path.write_text(json.dumps(self._store, indent=2))

    def _load(self) -> None:
        try:
            data = json.loads(self._path.read_text())
            if isinstance(data, dict):
                self._store = data
        except (json.JSONDecodeError, OSError):
            self._store = {}

    def __repr__(self) -> str:
        return f"LocalStorage(keys={list(self._store.keys())})"
