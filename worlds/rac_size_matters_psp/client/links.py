"""Ammo/Bolt Link with the Size Matters PS2 storage protocol."""
import asyncio
import time

from ..core.player_bolts import MAX_PLAYER_BOLTS


class ResourceLinkMixin:
    def _init_resource_links(self):
        self._resource_links = {"ammo": False, "bolt": False}
        self._link_ready = set()
        self._link_remote = {}
        self._link_pushed = {}
        self._link_last_push = {"ammo": 0.0, "bolt": 0.0}

    def _resource_link_key(self, kind):
        return f"rsm_{kind}_link_{self.team}"

    async def _set_resource_link(self, kind, enabled):
        if kind not in self._resource_links:
            raise ValueError("Unknown resource link")
        self._resource_links[kind] = bool(enabled)
        tag = kind.title() + "Link"
        self.tags = self.tags | {tag} if enabled else self.tags - {tag}
        if self.slot is not None:
            await self.send_msgs([{"cmd": "ConnectUpdate", "tags": sorted(self.tags)}])
            if enabled:
                key = self._resource_link_key(kind)
                self._link_ready.discard(key)
                self._link_remote.pop(kind, None)
                self._link_pushed.pop(kind, None)
                self.set_notify(key)
                await self.send_msgs([{"cmd": "Get", "keys": [key]}])

    def _resource_link_packet(self, cmd, args):
        if cmd == "Connected":
            self._init_resource_links()
            for kind in self._resource_links:
                asyncio.create_task(self._set_resource_link(kind, bool(self.slot_data.get(kind + "_link", False))))
        elif cmd == "Retrieved":
            self._link_ready.update(args.get("keys", {}))
        elif cmd == "SetReply":
            key = args.get("key")
            if key:
                self._link_ready.add(key)

    def _poll_resource_links(self):
        # Called under the emulator lock, after session validation.
        if self.slot is None or not self.psp_connected or not self._wiring.planet.is_ready:
            return
        for kind, enabled in self._resource_links.items():
            key = self._resource_link_key(kind)
            if not enabled or key not in self._link_ready:
                continue
            if kind == "ammo" and self._wiring.vendor_active:
                continue
            remote = self.stored_data.get(key)
            if kind == "bolt":
                if (type(remote) is int and 0 <= remote <= MAX_PLAYER_BOLTS
                        and remote != self._link_remote.get(kind)
                        and remote != self._link_pushed.get(kind)):
                    self._wiring.player_bolts.set(remote)
                    self._wiring.player_bolts.rebaseline(remote)
                    self._link_pushed[kind] = remote
                current = self._wiring.player_bolts.get()
            else:
                weapons = self._wiring.planet.weapons
                if isinstance(remote, dict) and remote != self._link_remote.get(kind):
                    for name, value in remote.items():
                        pushed = self._link_pushed.get(kind, {})
                        if (weapons.weapons.get(name) and type(value) is int and 0 <= value <= 9999
                                and value != pushed.get(name)):
                            weapons.set_ammo(name, value)
                            # Suppress echo only for fields actually received;
                            # don't swallow a local change to another weapon.
                            self._link_pushed.setdefault(kind, {})[name] = value
                current = {name: weapons.get_ammo(name) for name, owned in weapons.weapons.items() if owned}
            self._link_remote[kind] = dict(remote) if isinstance(remote, dict) else remote
            now = time.monotonic()
            if current == self._link_pushed.get(kind) or now - self._link_last_push[kind] < 0.5:
                continue
            self._link_last_push[kind] = now
            self._link_pushed[kind] = current
            asyncio.create_task(self.send_msgs([{
                "cmd": "Set", "key": key, "default": {} if kind == "ammo" else 0,
                "want_reply": True,
                "operations": [{"operation": "update" if kind == "ammo" else "replace", "value": current}],
            }]))
