"""Archipelago DeathLink bridge. Requires a verified game adapter for incoming kills.

Use CommonContext.update_death_link/send_death. No network is opened by this module.
Client.py wires the verified solo PINE action; unverified adapters remain disabled.
"""
from collections import deque


class DeathLinkBridge:
    def __init__(self, context, game_adapter):
        self.context, self.game = context, game_adapter
        self.enabled = False
        self.seen = deque(maxlen=128)
        self.remote_pending = False

    async def enable(self, enabled=True):
        if enabled and not self.game.can_apply_death:
            raise RuntimeError('DeathLink unavailable: incoming game-death action is not verified')
        await self.context.update_death_link(enabled)
        self.enabled = enabled
        if not enabled: self.remote_pending = False

    async def receive(self, data):
        if not self.enabled: return False
        key = (data['source'],data['time'])
        if key in self.seen: return False
        # Retry later if in pod, loading, dead or in a cutscene. Do not kill menus.
        if not self.game.can_die_now(): return False
        self.remote_pending = True
        try:
            applied = await self.game.apply_death()
        except Exception:
            self.remote_pending = False
            raise
        if not applied:
            self.remote_pending = False
            return False
        self.seen.append(key)
        return True

    async def local_death(self, cause='Sackboy died in LittleBigPlanet.'):
        if not self.enabled: return
        if self.remote_pending:
            self.remote_pending = False  # Never echo an incoming DeathLink death.
            return
        await self.context.send_death(cause)

    def level_changed(self):
        self.remote_pending = False


class UnverifiedPineDeathAdapter:
    can_apply_death = False

    def can_die_now(self): return False

    async def apply_death(self):
        raise RuntimeError('No verified PINE kill action; refusing to write guessed memory')
