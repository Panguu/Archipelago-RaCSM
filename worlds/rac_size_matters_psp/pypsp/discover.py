"""Discovery of running PPSSPP instances via report.ppsspp.org.

PPSSPP periodically reports its local IP and remote-debugger port to
report.ppsspp.org (see Core/WebServer.cpp's RegisterServer(), which hits
"/match/update?local=<ip>&port=<port>") so that a mobile device on the same
network can find it for Remote ISO Sharing. The same list is what we use
here to find the debugger WebSocket endpoint automatically, since PPSSPP
picks a fresh port on every restart (there's no stable, well-known port).

Selecting an instance:
  - PYPSP_HOST / PYPSP_PORT: if both are set, discovery is skipped entirely
    and this host/port is used as-is. Useful for a pinned/known instance,
    or when the machine running PPSSPP can't reach report.ppsspp.org.
  - PYPSP_MATCH_INDEX: 1-based index into the discovered instance list,
    ordered most-recently-seen first. Defaults to "1" (the freshest
    instance). Set this when more than one PPSSPP instance is reporting
    on the network and you need a specific one.
  - PYPSP_MATCH_API_URL: override the match-list URL (mainly for testing).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

MATCH_API_URL = "https://report.ppsspp.org/match/list"

_ENV_HOST = "PYPSP_HOST"
_ENV_PORT = "PYPSP_PORT"
_ENV_MATCH_INDEX = "PYPSP_MATCH_INDEX"
_ENV_MATCH_API_URL = "PYPSP_MATCH_API_URL"

_DEFAULT_TIMEOUT = 5.0

# report.ppsspp.org 403s requests without a recognizable User-Agent (urllib's
# default "Python-urllib/x.y" gets rejected outright).
_REQUEST_HEADERS = {"User-Agent": "pypsp (Archipelago RAC Size Matters client)"}


@dataclass(frozen=True)
class DiscoveredInstance:
    """One entry from report.ppsspp.org/match/list."""
    ip: str
    port: int
    last_seen: int  # Unix timestamp of the instance's last check-in.


class DiscoveryError(Exception):
    """Raised when discovery can't produce a usable (host, port)."""


def discover_instances(*, timeout: float = _DEFAULT_TIMEOUT) -> list[DiscoveredInstance]:
    """Fetch the current list of PPSSPP instances reporting to
    report.ppsspp.org, most-recently-seen first.

    Raises DiscoveryError if the request fails or the response is malformed.
    """
    url = os.environ.get(_ENV_MATCH_API_URL, MATCH_API_URL)
    request = urllib.request.Request(url, headers=_REQUEST_HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:  # noqa: S310 (fixed https host)
            raw = resp.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise DiscoveryError(f"Could not reach {url}: {exc}") from exc

    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DiscoveryError(f"Bad response from {url}: not JSON") from exc

    if not isinstance(entries, list):
        raise DiscoveryError(f"Bad response from {url}: expected a list")

    instances = []
    for entry in entries:
        try:
            instances.append(DiscoveredInstance(
                ip=str(entry["ip"]),
                port=int(entry["p"]),
                last_seen=int(entry["t"]),
            ))
        except (KeyError, TypeError, ValueError):
            continue  # Skip malformed entries rather than failing the whole list.

    instances.sort(key=lambda i: i.last_seen, reverse=True)
    return instances


def _env_int(name: str) -> int | None:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        raise DiscoveryError(f"{name}={raw!r} is not a valid integer") from None


def resolve_target(*, timeout: float = _DEFAULT_TIMEOUT) -> tuple[str, int]:
    """Figure out which PPSSPP instance to connect to.

    If PYPSP_HOST and PYPSP_PORT are both set, uses those directly (no
    network call). Otherwise, calls discover_instances() and picks the
    entry at PYPSP_MATCH_INDEX (1-based, default 1 = most recently seen).
    """
    env_host = os.environ.get(_ENV_HOST)
    env_port = _env_int(_ENV_PORT)
    if env_host and env_port is not None:
        return env_host, env_port

    instances = discover_instances(timeout=timeout)
    if not instances:
        raise DiscoveryError(
            "No PPSSPP instances found at report.ppsspp.org/match/list. "
            "Make sure PPSSPP is running with 'Allow remote debugger' enabled, "
            "or set PYPSP_HOST / PYPSP_PORT to connect directly."
        )

    index_raw = os.environ.get(_ENV_MATCH_INDEX, "1")
    try:
        index = int(index_raw)
    except ValueError:
        raise DiscoveryError(f"{_ENV_MATCH_INDEX}={index_raw!r} is not a valid integer") from None
    if index < 1 or index > len(instances):
        raise DiscoveryError(
            f"{_ENV_MATCH_INDEX}={index} is out of range: "
            f"only {len(instances)} instance(s) reporting right now."
        )

    chosen = instances[index - 1]
    return chosen.ip, chosen.port
