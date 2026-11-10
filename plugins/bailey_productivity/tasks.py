"""Owner's personal task records, separate from Hermes' agent-worker Kanban."""
import calendar
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
import uuid
from zoneinfo import ZoneInfo

LAGOS = ZoneInfo('Africa/Lagos')
PRIORITIES = {'low', 'normal', 'high', 'urgent'}
STATES = {'tentative', 'open', 'completed', 'cancelled'}


def now():
    return datetime.now(timezone.utc)


def instant(value):
    if not isinstance(value, str):
        raise ValueError('Use an ISO date/time with a timezone offset')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Due dates need a timezone offset; Africa/Lagos is +01:00')
    return result.astimezone(timezone.utc)


def due_value(value):
    return instant(value).isoformat() if value else None


def text(value, label, maximum=4000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f'{label} must be nonempty text, at most {maximum} characters')
    return value.strip()


class Tasks:
    def __init__(self, home):
        home = Path(home)
        if home.is_symlink() or not home.is_dir() or home.stat().st_mode & 0o077:
            raise ValueError('Task storage requires a private Hermes home')
        self.path = home / 'bailey-tasks.db'
        if self.path.is_symlink():
            raise ValueError('Refusing a symlinked task database')
        if not self.path.exists():
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        if self.path.stat().st_mode & 0o077:
            raise ValueError('Task database must be private')
        with self.connection() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1):
                raise ValueError('Unsupported task schema version')
            if version == 0:
                db.executescript('''
                BEGIN IMMEDIATE;
                CREATE TABLE tasks (
                  id TEXT PRIMARY KEY, title TEXT NOT NULL, notes TEXT NOT NULL,
                  status TEXT NOT NULL CHECK(status IN ('tentative','open','completed','cancelled')),
                  priority TEXT NOT NULL CHECK(priority IN ('low','normal','high','urgent')),
                  due_at TEXT, recurrence TEXT, series_id TEXT NOT NULL,
                  created_at TEXT NOT NULL, updated_at TEXT NOT NULL, completed_at TEXT,
                  request_key TEXT UNIQUE);
                CREATE INDEX tasks_due ON tasks(status,due_at);
                CREATE TABLE task_events (
                  id INTEGER PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
                  action TEXT NOT NULL, at TEXT NOT NULL, details TEXT NOT NULL);
                PRAGMA user_version=1;
                COMMIT;
                ''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('PRAGMA busy_timeout=10000')
            db.execute('PRAGMA journal_mode=WAL')
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def event(db, task_id, action, details):
        db.execute('INSERT INTO task_events(task_id,action,at,details) VALUES(?,?,?,?)',
                   (task_id, action, now().isoformat(), json.dumps(details)))

    def create(self, title, notes='', due_at=None, priority='normal', recurrence=None,
               confirmed=False, request_key=None):
        title = text(title, 'Title', 300)
        if not isinstance(notes, str) or len(notes) > 4000:
            raise ValueError('Notes must be at most 4000 characters')
        if priority not in PRIORITIES:
            raise ValueError('Unknown priority')
        if type(confirmed) is not bool:
            raise ValueError('confirmed must be a boolean')
        due = due_value(due_at)
        if recurrence not in (None, 'daily', 'weekly', 'monthly'):
            raise ValueError('Recurrence must be daily, weekly or monthly')
        if recurrence and not due:
            raise ValueError('Recurring tasks need a due date')
        if request_key is not None:
            request_key = text(request_key, 'Request key', 200)
        rule = {'frequency': recurrence, 'day': instant(due).astimezone(LAGOS).day} if recurrence else None
        task_id, stamp = str(uuid.uuid4()), now().isoformat()
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if request_key:
                existing = db.execute('SELECT * FROM tasks WHERE request_key=?', (request_key,)).fetchone()
                if existing:
                    proposed = (title, notes, due, priority, json.dumps(rule) if rule else None)
                    if tuple(existing[k] for k in ('title','notes','due_at','priority','recurrence')) != proposed:
                        raise ValueError('Request key already belongs to a different task')
                    return dict(existing)
            db.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                       (task_id, title, notes, 'open' if confirmed else 'tentative', priority,
                        due, json.dumps(rule) if rule else None, task_id, stamp, stamp, None, request_key))
            self.event(db, task_id, 'created', {'confirmed': confirmed})
            return dict(db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone())

    def list(self, status='open', today=False, overdue=False, limit=50):
        if status not in STATES | {'all'} or type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('Invalid task filter or limit')
        clauses, args = [], []
        if status != 'all':
            clauses.append('status=?')
            args.append(status)
        if today:
            start = now().astimezone(LAGOS).replace(hour=0, minute=0, second=0, microsecond=0)
            clauses += ['due_at>=?', 'due_at<?']
            args += [start.astimezone(timezone.utc).isoformat(), (start+timedelta(days=1)).astimezone(timezone.utc).isoformat()]
        if overdue:
            clauses.append('due_at<?')
            args.append(now().isoformat())
        where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
        with self.connection() as db:
            rows = db.execute('SELECT * FROM tasks'+where+''' ORDER BY
              CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END,
              due_at IS NULL,due_at,created_at LIMIT ?''', [*args, limit]).fetchall()
            return [dict(row) for row in rows]

    def update(self, task_id, **changes):
        allowed = {'title', 'notes', 'due_at', 'priority', 'status'}
        if not changes or set(changes)-allowed:
            raise ValueError('Unsupported task update')
        if 'title' in changes:
            changes['title'] = text(changes['title'], 'Title', 300)
        if 'notes' in changes and (not isinstance(changes['notes'], str) or len(changes['notes'])>4000):
            raise ValueError('Invalid notes')
        if 'due_at' in changes:
            changes['due_at'] = due_value(changes['due_at'])
        if 'priority' in changes and changes['priority'] not in PRIORITIES:
            raise ValueError('Unknown priority')
        if 'status' in changes and changes['status'] not in {'open', 'tentative', 'cancelled'}:
            raise ValueError('Use complete to complete a task')
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
            if row is None:
                raise ValueError('Task not found')
            if row['status'] in {'completed', 'cancelled'}:
                raise ValueError('Closed tasks cannot be edited')
            if row['recurrence'] and 'due_at' in changes and not changes['due_at']:
                raise ValueError('Recurring tasks need a due date')
            fields = list(changes)
            db.execute('UPDATE tasks SET '+','.join(k+'=?' for k in fields)+',updated_at=? WHERE id=?',
                       [*(changes[k] for k in fields), now().isoformat(), task_id])
            self.event(db, task_id, 'updated', changes)
            return dict(db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone())

    def complete(self, task_id):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
            if row is None:
                raise ValueError('Task not found')
            if row['status'] == 'completed':
                return {'task': dict(row), 'already_completed': True}
            if row['status'] != 'open':
                raise ValueError('Only a confirmed open task can be completed')
            stamp = now().isoformat()
            db.execute("UPDATE tasks SET status='completed',completed_at=?,updated_at=? WHERE id=?", (stamp, stamp, task_id))
            self.event(db, task_id, 'completed', {})
            next_id = None
            if row['recurrence']:
                rule = json.loads(row['recurrence'])
                due = instant(row['due_at']).astimezone(LAGOS)
                if rule['frequency'] == 'monthly':
                    year, month = due.year + (due.month == 12), due.month % 12 + 1
                    due = due.replace(year=year, month=month, day=min(rule['day'], calendar.monthrange(year, month)[1]))
                else:
                    due += timedelta(days=1 if rule['frequency'] == 'daily' else 7)
                next_id = str(uuid.uuid4())
                db.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                    (next_id,row['title'],row['notes'],'open',row['priority'],due.astimezone(timezone.utc).isoformat(),
                     row['recurrence'],row['series_id'],stamp,stamp,None,None))
                self.event(db,next_id,'recurrence_created',{'previous_task':task_id})
            return {'task':dict(db.execute('SELECT * FROM tasks WHERE id=?',(task_id,)).fetchone()),'next_task_id':next_id}
