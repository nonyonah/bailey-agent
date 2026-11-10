import importlib.util
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from bailey.acceptance import check_database

spec = importlib.util.spec_from_file_location("backup", Path(__file__).parents[1] / "deploy/backup.py")
backup_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup_module)


class OperationsTests(unittest.TestCase):
    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.db"
            with self.assertRaises(ValueError):
                check_database(path)
            self.assertFalse(path.exists())

    def test_native_db_check_requires_wal_and_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.db"
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE fixture (value TEXT)")
                db.commit()
                with self.assertRaises(ValueError):
                    check_database(path)
                db.execute("PRAGMA journal_mode=WAL")
                self.assertTrue(check_database(path))

    def test_failed_backup_restarts_gateway_without_pruning(self):
        calls = []
        def run(args, **kwargs):
            calls.append(args)
            if args[:2] == ["restic", "backup"]:
                raise subprocess.CalledProcessError(1, args)
            return subprocess.CompletedProcess(args, 0)
        with patch.dict(os.environ, {"RESTIC_REPOSITORY": "sftp:fixture:/backup", "RESTIC_PASSWORD_FILE": "/fixture"}):
            with self.assertRaises(subprocess.CalledProcessError):
                backup_module.backup(run)
        self.assertEqual(calls[-1], ["systemctl", "start", "bailey-gateway.service"])
        self.assertNotIn(["restic", "forget"], [c[:2] for c in calls])

    def test_failed_backup_preserves_stopped_state(self):
        calls = []
        def run(args, **kwargs):
            calls.append(args)
            if args[:2] == ["restic", "backup"]:
                raise subprocess.CalledProcessError(1, args)
            return subprocess.CompletedProcess(args, 3)
        with patch.dict(os.environ, {"RESTIC_REPOSITORY": "sftp:fixture:/backup", "RESTIC_PASSWORD_FILE": "/fixture"}):
            with self.assertRaises(subprocess.CalledProcessError):
                backup_module.backup(run)
        self.assertNotIn("stop", [c[1] for c in calls])
        self.assertNotIn("start", [c[1] for c in calls])
