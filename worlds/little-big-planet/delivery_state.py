"""Durable, seed/team/slot-isolated check outbox and AP delivery journal."""
import hashlib
import json
import sqlite3
from pathlib import Path


class DeliveryState:
    def __init__(self, directory, seed, team, slot):
        if not seed or slot is None or team is None:
            raise ValueError('A connected AP seed/team/slot is required')
        identity = json.dumps([seed, team, slot], separators=(',', ':'))
        key = hashlib.sha256(identity.encode()).hexdigest()
        Path(directory).mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(Path(directory)/f'{key}.sqlite3')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS checks (id INTEGER PRIMARY KEY, confirmed INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS deliveries (idx INTEGER PRIMARY KEY, item INTEGER NOT NULL,
                location INTEGER NOT NULL, sender INTEGER NOT NULL, applied INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS pickup_events (digest TEXT PRIMARY KEY, event TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS one_shots (idx INTEGER PRIMARY KEY);
        ''')

    def close(self):
        self.db.close()

    def queue_checks(self, ids, pickup_events=()):
        with self.db:
            self.db.executemany('INSERT OR IGNORE INTO checks(id) VALUES (?)', ((i,) for i in ids))
            for event in pickup_events:
                raw = json.dumps(event, sort_keys=True, separators=(',', ':'))
                self.db.execute('INSERT OR IGNORE INTO pickup_events VALUES (?,?)',
                                (hashlib.sha256(raw.encode()).hexdigest(), raw))

    def confirm_checks(self, ids):
        with self.db:
            self.db.executemany('INSERT INTO checks VALUES (?,1) ON CONFLICT(id) DO UPDATE SET confirmed=1',
                                ((i,) for i in ids))

    def pending_checks(self):
        return [r[0] for r in self.db.execute('SELECT id FROM checks WHERE confirmed=0 ORDER BY id')]

    def checked(self):
        return {r[0] for r in self.db.execute('SELECT id FROM checks')}

    def receive(self, index, items):
        if index < 0:
            raise ValueError('Negative AP item index')
        with self.db:
            for offset, item in enumerate(items):
                row = (item.item, item.location, item.player)
                old = self.db.execute('SELECT item,location,sender FROM deliveries WHERE idx=?',
                                      (index+offset,)).fetchone()
                if old is not None and old != row:
                    raise ValueError('AP item history changed for this seed/slot')
                self.db.execute('INSERT OR IGNORE INTO deliveries(idx,item,location,sender) VALUES (?,?,?,?)',
                                (index+offset, *row))

    def pending_items(self):
        return list(self.db.execute('SELECT idx,item FROM deliveries WHERE applied=0 ORDER BY idx'))

    def applied(self, index, one_shot=False):
        with self.db:
            cursor = self.db.execute('UPDATE deliveries SET applied=1 WHERE idx=?', (index,))
            if cursor.rowcount != 1:
                raise ValueError('Unknown AP delivery index')
            if one_shot:
                self.db.execute('INSERT OR IGNORE INTO one_shots VALUES (?)',(index,))

    def reconcile_game(self):
        """Reapply idempotent ownership grants after reconnect/save rollback."""
        with self.db:
            self.db.execute('UPDATE deliveries SET applied=0 WHERE idx NOT IN (SELECT idx FROM one_shots)')
