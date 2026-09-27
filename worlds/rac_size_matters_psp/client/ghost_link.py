"""GhostLink protocol: only in-game coordinates, enabled by the player's option."""
import asyncio
import math
import time


class GhostLinkMixin:
    def _init_ghost_link(self):
        self._ghost_link_enabled = False
        self._ghost_link_interval = 5.0
        self._ghost_link_peers = {}
        self._ghost_link_last_push = 0.0
        self._ghost_link_watched = set()

    def _ghost_link_key(self, slot):
        return f'rsm_ghost_link_{self.team}_{slot}'

    async def _set_ghost_link_enabled(self, enabled):
        self._ghost_link_enabled = bool(enabled)
        self.tags = self.tags | {'GhostLink'} if enabled else self.tags - {'GhostLink'}
        self._ghost_link_peers.clear()
        if self.slot is not None:
            await self.send_msgs([{'cmd':'ConnectUpdate','tags':sorted(self.tags)}])
            self._ghost_link_watched = {slot for slot, info in self.slot_info.items()
                if slot != self.slot and info.game == self.game}
            if enabled:
                keys = [self._ghost_link_key(slot) for slot in sorted(self._ghost_link_watched)]
                for key in keys:
                    self.set_notify(key)
                if keys:
                    await self.send_msgs([{'cmd':'Get','keys':keys}])
            else:
                await self.send_msgs([{'cmd':'Set','key':self._ghost_link_key(self.slot),
                    'default':{},'want_reply':False,
                    'operations':[{'operation':'replace','value':{}}]}])

    def _ghost_link_packet(self, cmd, args):
        if not self._ghost_link_enabled:
            return
        updates = args.get('keys', {}) if cmd == 'Retrieved' else {args.get('key'):args.get('value')}
        for slot in self._ghost_link_watched:
            key = self._ghost_link_key(slot)
            if key not in updates:
                continue
            value = updates[key]
            self._ghost_link_peers.pop(slot, None)
            if not isinstance(value, dict) or type(value.get('planet_id')) is not int:
                continue
            pos = tuple(value.get(axis) for axis in ('x','y','z'))
            if not all(type(v) in (int,float) and math.isfinite(v) and abs(v)<1e7 for v in pos):
                continue
            self._ghost_link_peers[slot] = (value['planet_id'], pos, time.monotonic())

    def _poll_ghost_link(self):
        ghost, planet = self._wiring.ghost_ratchet, self._wiring.planet
        if not planet.is_ready:
            ghost.abandon()
            return
        if not self._ghost_link_enabled or self.slot is None:
            ghost.stop_following()
            return
        now = time.monotonic()
        if now-self._ghost_link_last_push >= max(0.05,self._ghost_link_interval):
            pos = ghost.read_own_position(planet.planet_id)
            self._ghost_link_last_push = now
            if pos is not None:
                value = dict(zip(('x','y','z'),pos),planet_id=planet.planet_id)
                asyncio.create_task(self.send_msgs([{'cmd':'Set','key':self._ghost_link_key(self.slot),
                    'default':{},'want_reply':False,
                    'operations':[{'operation':'replace','value':value}]}]))
        for slot in sorted(self._ghost_link_peers):
            other, pos, received = self._ghost_link_peers[slot]
            if other == planet.planet_id and now-received <= 20:
                ghost.follow(other,*pos)
                return
        ghost.stop_following()
