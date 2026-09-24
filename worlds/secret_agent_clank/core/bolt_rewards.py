"""Deliver AP currency once per received item."""
from .address_maps import BOLTS_ADDRESS


def reward_balance(balance, count):
    for _ in range(count):
        updated = min(0x7FFFFFFF, balance + balance // 5)
        if updated == balance:
            break
        balance = updated
    return balance


class BoltRewards:
    def __init__(self, pine, log, *, on_state_changed=None):
        self.pine = pine
        self.log = log
        self.on_state_changed = on_state_changed or (lambda delivered, pending: None)
        self.enabled = False
        self.received = 0
        self.starting_bolts = 0
        self.delivered = 0
        self.starting_delivered = False
        self.pending = None

    def configure(self, *, starting_bolts=0, delivered=0, starting_delivered=False, pending=None):
        """Called once the AP data-storage read for this slot's "delivered_bolts"/"pending_bolts" keys has actually come back (see client/context.py) -- delivered/starting_delivered are "delivered_bolts"'s two fields, pending is "pending_bolts" as-is."""
        if type(starting_bolts) is not int or not 0 <= starting_bolts <= 100_000:
            raise ValueError("Starting bolts must be between 0 and 100000")
        if type(delivered) is not int or delivered < 0:
            raise ValueError("Invalid bolt reward state")
        self.starting_bolts = starting_bolts
        self.delivered = delivered
        self.starting_delivered = starting_delivered
        self.pending = pending
        self.received = 0
        self.enabled = True

    def _save(self):
        self.on_state_changed(
            {"count": self.delivered, "starting_delivered": self.starting_delivered}, self.pending,
        )

    def deliver(self):
        # Called only after the native runtime and current level are ready,
        # and only once AP's stored delivered/pending state has arrived.
        if not self.enabled:
            return
        pending = self.pending
        if pending:
            current = self.pine.read_int32(BOLTS_ADDRESS)
            if current == pending["before"]:
                self.pine.write_int32(BOLTS_ADDRESS, pending["after"])
            elif current != pending["after"]:
                raise RuntimeError("An interrupted bolt reward has an uncertain balance; "
                                   "delivery is paused to avoid duplicating or overwriting bolts.")
            if pending.get("kind") == "starting":
                self.starting_delivered = True
            else:
                self.delivered = pending["count"]
            self.pending = None
            self._save()
        if not self.starting_delivered:
            before = self.pine.read_int32(BOLTS_ADDRESS)
            after = min(0x7FFFFFFF, before + self.starting_bolts)
            # Award once, preserving bolts already earned while connecting.
            # Use the same write-ahead recovery as received percentage items.
            self.pending = {"kind": "starting", "before": before, "after": after}
            self._save()
            if after != before:
                self.pine.write_int32(BOLTS_ADDRESS, after)
            self.starting_delivered, self.pending = True, None
            self._save()
            if self.starting_bolts:
                self.log(f"[SAC] Granted {after - before:,} starting bolts.")
        count = self.received - self.delivered
        if count <= 0:
            return
        before = self.pine.read_int32(BOLTS_ADDRESS)
        after = reward_balance(before, count)
        self.pending = {"before": before, "after": after, "count": self.received}
        self._save()
        self.pine.write_int32(BOLTS_ADDRESS, after)
        self.delivered, self.pending = self.received, None
        self._save()
        self.log(f"[SAC] Received {after - before:,} bolts from {count} AP bolt item(s).")
