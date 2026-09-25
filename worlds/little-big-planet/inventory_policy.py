"""AP-authoritative inventory permissions, including exact native DLC membership."""
from .content_packs import PACKS, access_rows
from .items import ITEM_ID_TO_DATA
from .constants.data.dlc_inventory import DATA as DLC_PLANS


def allowed_plans(slot_data, received):
    ids = [item.item for item in received]
    states = [ITEM_ID_TO_DATA[i]['state'] for i in ids if i in ITEM_ID_TO_DATA]
    plans = {s['plan_guid'] for s in states if s['kind'] == 'inventory_plan'}
    packs = {s['slot_number'] for s in states if s['kind'] == 'content_pack_unlock'}
    for _, slot, allowed in access_rows(slot_data.get('costume_packs', ()), packs):
        if allowed:
            content = PACKS[slot]['content_id']
            if content not in DLC_PLANS:
                raise ValueError(f'No verified inventory mapping for {PACKS[slot]["name"]}')
            plans.update(DLC_PLANS[content])
    return sorted(plans)
