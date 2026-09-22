"""Lifecycle for verified PSP data patches during gameplay.

The retail PSP executable hooks have not yet been mapped. The registry is
intentionally empty until PSP-specific captures and cache handling exist.
"""

class NativeRuntime:
    def __init__(self, memory):
        self.memory = memory
        self.plans = []

    def register(self, plan):
        if plan.memory is not self.memory:
            raise ValueError("Patch belongs to another memory session")
        if any(existing.name == plan.name for existing in self.plans):
            raise ValueError("Duplicate patch name")
        for existing in self.plans:
            if existing.planet_id is not None and plan.planet_id is not None and existing.planet_id != plan.planet_id:
                continue
            for a in existing.edits:
                for b in plan.edits:
                    if max(a.address, b.address) < min(a.address + len(a.original), b.address + len(b.original)):
                        raise ValueError("Overlapping runtime plans")
        self.plans.append(plan)

    def tick(self, planet_id, ready):
        for plan in self.plans:
            active = ready and (plan.planet_id is None or plan.planet_id == planet_id)
            if active:
                plan.install()
            elif plan.installed:
                plan.restore()

    def restore(self):
        for plan in reversed(self.plans):
            plan.restore()
