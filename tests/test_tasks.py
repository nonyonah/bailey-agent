import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('bailey_personal_tasks', Path(__file__).parents[1]/'plugins/bailey_productivity/tasks.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TaskTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.home.chmod(0o700)
        self.tasks = module.Tasks(self.home)

    def test_tentative_commitment_does_not_appear_as_confirmed(self):
        task = self.tasks.create('Maybe finish a report')
        self.assertEqual(task['status'], 'tentative')
        self.assertEqual(self.tasks.list(), [])
        with self.assertRaises(ValueError):
            self.tasks.complete(task['id'])
        self.tasks.update(task['id'], status='open')
        self.assertEqual(len(self.tasks.list()), 1)

    def test_records_survive_reopen_and_use_private_wal_database(self):
        self.tasks.create('Confirmed work', confirmed=True)
        reopened = module.Tasks(self.home)
        self.assertEqual(reopened.list()[0]['title'], 'Confirmed work')
        with reopened.connection() as db:
            self.assertEqual(db.execute('PRAGMA journal_mode').fetchone()[0], 'wal')
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
        self.assertEqual(self.tasks.path.stat().st_mode & 0o777, 0o600)

    def test_monthly_recurrence_preserves_original_day_and_completes_once(self):
        task = self.tasks.create('Month end', due_at='2027-01-31T09:00:00+01:00', recurrence='monthly', confirmed=True)
        first = self.tasks.complete(task['id'])
        again = self.tasks.complete(task['id'])
        self.assertTrue(again['already_completed'])
        next_task = self.tasks.list()[0]
        self.assertIn('2027-02-28', next_task['due_at'])
        self.tasks.complete(next_task['id'])
        self.assertIn('2027-03-31', self.tasks.list()[0]['due_at'])
        self.assertEqual(len(self.tasks.list()), 1)
        self.assertIsNotNone(first['next_task_id'])

    def test_retry_key_cannot_duplicate_or_substitute_task(self):
        first = self.tasks.create('One task', request_key='test-request', confirmed=True)
        again = self.tasks.create('One task', request_key='test-request', confirmed=True)
        self.assertEqual(first['id'], again['id'])
        with self.assertRaises(ValueError):
            self.tasks.create('Different task', request_key='test-request', confirmed=True)
        self.assertEqual(len(self.tasks.list()), 1)

    def test_sql_content_is_data_and_ambiguous_dates_are_rejected(self):
        title = "finish report'); DROP TABLE tasks; --"
        self.tasks.create(title, confirmed=True)
        self.assertEqual(self.tasks.list()[0]['title'], title)
        with self.assertRaises(ValueError):
            self.tasks.create('Ambiguous time', due_at='2027-01-01T10:00:00')
        with self.assertRaises(ValueError):
            self.tasks.create('No date', recurrence='weekly')

    def test_symlinks_and_unreviewed_schema_fail_closed(self):
        p = self.tasks.path
        target = self.home/'elsewhere'
        p.rename(target)
        p.symlink_to(target)
        with self.assertRaises(ValueError):
            module.Tasks(self.home)
