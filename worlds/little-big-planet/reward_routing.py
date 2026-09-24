"""Reward routing contract for a future verified game hook, not a live patch.

The hook must suppress the original grant BEFORE calling native_reward, while
preserving physical collection progress independently of inventory ownership.
Only AP ReceivedItems handling may call received_item. Neither method performs
memory writes. Decisions must be acknowledged by the game/server adapters.
"""
from dataclasses import dataclass
from items import ITEM_ID_TO_DATA
from locations import LOCATIONS


@dataclass(frozen=True)
class NativeRewardDecision:
    location_id: int
    grant_original: bool = False


class RewardRouter:
    def __init__(self, enabled_location_ids, confirmed_location_ids=()):
        self.locations = {loc['id']: loc for loc in LOCATIONS.values()
                          if loc['kind'] in ('prize', 'reward')}
        self.enabled = frozenset(enabled_location_ids)
        if self.enabled - self.locations.keys():
            raise ValueError('Reward routing accepts only known prize/reward locations')
        self.confirmed = set(confirmed_location_ids) & self.enabled
        self.pending_checks = set()

    def native_reward(self, location_id):
        """Use exact bubble UID/reward index mapping, never inventory ownership.

        Disabled locations retain vanilla behavior. Repeated enabled rewards
        remain suppressed even after the server has confirmed their checks.
        """
        if location_id not in self.locations:
            raise ValueError('Unknown prize/reward location')
        if location_id not in self.enabled:
            return NativeRewardDecision(location_id, grant_original=True)
        if location_id not in self.confirmed:
            self.pending_checks.add(location_id)
        return NativeRewardDecision(location_id)

    def acknowledge_checks(self, location_ids):
        confirmed = set(location_ids) & self.enabled
        self.confirmed.update(confirmed)
        self.pending_checks.difference_update(confirmed)

    def received_item(self, item_id):
        """Resolve an AP item to a grant target without creating a location check.

        Adapter must grant idempotently, bypass native reward suppression, and
        acknowledge delivery only after verified readback. Unsupported inventory
        grants stay pending in the AP delivery layer.
        """
        import copy
        return copy.deepcopy(ITEM_ID_TO_DATA[item_id]['state'])


def require_randomizer_adapter(adapter):
    """Refuse activation until all required game-side capabilities are verified."""
    required = ('suppresses_native_rewards', 'captures_prize_identity',
                'preserves_collection_progress', 'grants_received_inventory')
    missing = [name for name in required if not getattr(adapter, name, False)]
    if missing:
        raise RuntimeError('Randomizer game adapter is not ready: ' + ', '.join(missing))
