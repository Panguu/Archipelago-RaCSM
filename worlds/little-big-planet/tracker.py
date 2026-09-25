"""Turn level completion/ace/all-prize counter changes into location ids."""
from dataclasses import dataclass, field

from .locations import LOCATIONS_BY_LEVEL, Kind

CONDITIONS = (Kind.COMPLETE, Kind.ALL_PRIZES, Kind.ACE)


@dataclass
class CheckTracker:
    checked: set = field(default_factory=set)
    counters: dict = field(default_factory=dict)
    run: tuple | None = None
    deaths: int | None = None
    progress_initialized: bool = False
    awaiting_collection: dict = field(default_factory=dict)

    def condition(self, level, condition):
        """The condition's own check plus every reward granted for it."""
        ids = [location.code for location in LOCATIONS_BY_LEVEL.get(level, ())
               if condition in (location.kind, location.condition) and location.code not in self.checked]
        self.checked.update(ids)
        return ids

    def observe_run(self, level, run_token, death_count):
        token = (level, run_token) if level is not None else None
        died = (self.run == token and token is not None and self.deaths is not None
                and death_count is not None and death_count > self.deaths)
        if self.run != token:
            self.awaiting_collection.clear()
        self.run, self.deaths = token, death_count
        return died

    def observe_counts(self, level, completion_count, ace_count,
                       prizes_at_completion=None, prize_total=None, active=False):
        ids = []
        old = self.counters.get(level)
        self.counters[level] = (completion_count, ace_count)
        if old is not None:
            if completion_count > old[0]:
                ids += self.condition(level, Kind.COMPLETE)
                if active:
                    self.awaiting_collection[level] = completion_count
            elif completion_count < old[0]:
                self.awaiting_collection.pop(level, None)
            if ace_count > old[1]:
                ids += self.condition(level, Kind.ACE)
        if (active and self.awaiting_collection.get(level) == completion_count
                and prize_total and prizes_at_completion == prize_total):
            ids += self.condition(level, Kind.ALL_PRIZES)
            self.awaiting_collection.pop(level, None)
        return ids

    def update_progress(self, records, slots, current_level=None, run_token=None,
                        death_count=None, prizes_at_completion=None, prize_total=None):
        """Observe every profile record so a finish during return-to-pod is not lost.

        The first observation only sets baselines: a save still loading must not look like new progress.
        """
        totals = {}
        for record in records:
            levels = slots.get((record['slot_type'], record['slot_number']), set())
            if len(levels) == 1:
                values = totals.setdefault(next(iter(levels)), [0, 0])
                values[0] += record['completion_count']
                values[1] += record['ace_count']
        died = self.observe_run(current_level, run_token, death_count)
        if not self.progress_initialized:
            self.counters = {level: tuple(values) for level, values in totals.items()}
            self.progress_initialized = True
            return {'location_ids': [], 'local_death': False}
        ids = []
        for level, (completions, aces) in totals.items():
            ids += self.observe_counts(level, completions, aces, prizes_at_completion, prize_total,
                                       active=level == current_level)
        return {'location_ids': ids, 'local_death': died}
