from .patches import VendorPresentation

AP_ICON_ID = 73


class VendorRewards:
    def __init__(self, pine, vendor, log):
        self.pine, self.vendor, self.log = pine, vendor, log
        self.text = VendorPresentation(pine)
        self.scouts = None
        self.warned = False
        self.last_text = None
        self.rows = {}

    def invalidate(self):
        self.last_text = None
        self.rows.clear()
        self.warned = False

    def close(self):
        header = self.vendor._native_header()
        if header is not None:
            pointer, _, _ = header
            for row in self.vendor.read_items():
                address = pointer + row.index * 0x1C
                original = self.rows.get(address)
                if (original is not None and original[0] == (row.node_type, row.weapon_id, row.mod_id)
                        and row.icon == AP_ICON_ID):
                    self.pine.write_int32(address + 4, original[1])
        if self.last_text is not None and self.text.mailbox is not None and not self.pine.read_int32(self.text.timer):
            self.pine.write_int32(self.text.mailbox, 0)
        self.last_text = None
        self.rows.clear()

    def tick(self, symbols):
        if self.scouts is None:
            return
        try:
            if not self.vendor.active:
                self.close()
                return
            header = self.vendor._native_header()
            if header is None:
                return
            pointer, _count, selected = header
            rows = self.vendor.read_items()
            rewards = [(row, self.scouts.for_row(row)) for row in rows]
            if self.vendor._native_header() != header:
                return
            for row, reward in rewards:
                address = pointer + row.index * 0x1C
                identity = (row.node_type, row.weapon_id, row.mod_id)
                old = self.rows.get(address)
                if reward is not None:
                    if row.icon != AP_ICON_ID:
                        self.rows[address] = (identity, row.icon)
                        self.pine.write_int32(address + 4, AP_ICON_ID)
                elif old is not None and old[0] == identity and row.icon == AP_ICON_ID:
                    self.pine.write_int32(address + 4, old[1])
                    self.rows.pop(address, None)
            entry = next(((row, reward) for row, reward in rewards if row.index == selected), None)
            if entry is None:
                return
            row, reward = entry
            key = (pointer, row.index, row.node_type, row.weapon_id, row.mod_id, reward)
            if self.text.mailbox is not None and not self.pine.read_int32(self.text.timer):
                if key != self.last_text or self.pine.read_int32(self.text.mailbox) != (pointer + row.index * 0x1C if reward else 0):
                    self.text.publish(pointer + row.index * 0x1C, row, reward)
                    self.last_text = key
        except (RuntimeError, ValueError) as exc:
            if not self.warned:
                self.log(f"[SAC] Vendor reward display unavailable: {exc}")
                self.warned = True
