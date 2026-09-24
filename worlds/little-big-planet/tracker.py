"""Translate validated events/counter changes into location IDs, independent of transport.

Physical pickups must come from an exact-ID pickup hook. A missing object, score change,
or newly owned inventory item must not be submitted as a physical pickup.
"""
from dataclasses import dataclass, field


@dataclass
class CheckTracker:
    locations: dict
    checked: set = field(default_factory=set)
    counters: dict = field(default_factory=dict)
    run: tuple | None = None
    deaths: int | None = None
    progress_initialized: bool = False
    awaiting_collection: dict = field(default_factory=dict)

    def _checks(self, keys):
        result = []
        for key in keys:
            if key in self.locations and key not in self.checked:
                result.append(self.locations[key]['id']); self.checked.add(key)
        return result

    def pickup(self, level_guid, kind, uid):
        """Call only with a verified pickup event and original authored UID."""
        if kind not in ('score','prize'): raise ValueError('Invalid bubble kind')
        return self._checks([f'{level_guid}/{kind}/{uid}'])

    def condition(self, level_guid, condition, include_rewards=True):
        if condition not in ('complete','all_prizes','ace'): raise ValueError('Invalid condition')
        keys = [f'{level_guid}/{condition}']
        if include_rewards:
            keys += [key for key,loc in self.locations.items()
                     if key.startswith(level_guid+'/reward/') and loc.get('condition')==condition]
        return self._checks(keys)

    def observe_run(self, level_guid, run_token, death_count):
        token = (level_guid, run_token) if level_guid is not None else None
        died = (self.run == token and token is not None and self.deaths is not None
                and death_count is not None and death_count > self.deaths)
        if self.run != token:
            self.awaiting_collection.clear()
        self.run, self.deaths = token, death_count
        return died

    def observe_counts(self, level_guid, completion_count, ace_count,
                       prizes_at_completion=None, prize_total=None, active=False):
        keys = []
        old = self.counters.get(level_guid)
        self.counters[level_guid] = (completion_count, ace_count)
        if old is not None:
            if completion_count > old[0]:
                keys += self.condition(level_guid, 'complete')
                if active:
                    self.awaiting_collection[level_guid] = completion_count
            elif completion_count < old[0]:
                self.awaiting_collection.pop(level_guid, None)
            if ace_count > old[1]:
                keys += self.condition(level_guid, 'ace')
        if (active and self.awaiting_collection.get(level_guid) == completion_count
                and prize_total is not None and prize_total > 0
                and prizes_at_completion == prize_total):
            keys += self.condition(level_guid, 'all_prizes')
            self.awaiting_collection.pop(level_guid, None)
        return keys

    def update_progress(self, records, slots, current_guid=None, run_token=None,
                        death_count=None, prizes_at_completion=None, prize_total=None):
        """Observe the whole profile so a finish during return-to-pod is not lost.

        First observations establish baselines, including records that appear
        after loading. Missing records are not zero counters; that could mistake
        an old save finishing its load for newly earned progress.
        """
        totals = {}
        for record in records:
            guids = slots.get((record['slot_type'], record['slot_number']), set())
            if len(guids) == 1:
                values = totals.setdefault(next(iter(guids)), [0, 0])
                values[0] += record['completion_count']
                values[1] += record['ace_count']
        died = self.observe_run(current_guid, run_token, death_count)
        if not self.progress_initialized:
            self.counters = {guid: tuple(values) for guid, values in totals.items()}
            self.progress_initialized = True
            return {'location_ids': [], 'local_death': False}
        checks = []
        for guid, (completions, aces) in totals.items():
            checks += self.observe_counts(guid, completions, aces,
                                         prizes_at_completion, prize_total,
                                         active=guid == current_guid)
        return {'location_ids': checks, 'local_death': died}

    def update(self, level_guid, run_token, completion_count, ace_count,
               death_count, prizes_at_completion=None, prize_total=None):
        """Single-level diagnostic entry point; the client uses update_progress."""
        died = self.observe_run(level_guid, run_token, death_count)
        checks = self.observe_counts(level_guid, completion_count, ace_count,
                                     prizes_at_completion, prize_total, active=True)
        return {'location_ids': checks, 'local_death': died}
