import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"plugins/bailey_productivity"))
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from contextlib import closing
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "bailey_writes_test", Path(__file__).parents[1] / "plugins/bailey_productivity/writes.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WriteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.home.chmod(0o700)
        self.calls = []

    def executor(self, action, payload):
        self.calls.append((action, payload))
        return {"successful": True, "data": {"success": True,"id":"receipt-123"}}

    def store(self, executor=None):
        return module.Writes(self.home, executor=executor or self.executor, reader=self.read_event)

    def read_event(self, identifier):
        return {'id':identifier,'etag':'version-1','summary':'Old event','organizer':{'self':True},
                'start':{'dateTime':'2026-11-12T15:00:00+01:00'},
                'end':{'dateTime':'2026-11-12T16:00:00+01:00'}}

    def email(self, **overrides):
        fields = {"to": ["owner@example.com"], "subject": "Hello", "body": "Body"}
        fields.update(overrides)
        return fields

    def test_proposal_never_executes_and_code_is_required(self):
        store = self.store()
        proposal = store.propose("email.send", **self.email())
        self.assertEqual(proposal["status"], "proposed")
        self.assertEqual(self.calls, [])
        with self.assertRaises(ValueError):
            store.approve(proposal["proposal_id"], "not-the-code")
        approved = store.approve(proposal["proposal_id"], proposal["approval_code"])
        self.assertEqual(approved["status"], "approved")
        with self.assertRaises(ValueError):
            store.execute(proposal["proposal_id"], "not-the-code")
        result = store.execute(proposal["proposal_id"], proposal["approval_code"])
        self.assertEqual(result["status"], "executed")
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][0], "email.send")
        with self.assertRaises(ValueError):
            store.execute(proposal["proposal_id"], proposal["approval_code"])

    def test_request_key_is_idempotent_and_cannot_substitute_content(self):
        store = self.store()
        first = store.propose("email.send", request_key="same-request", **self.email())
        again = store.propose("email.send", request_key="same-request", **self.email())
        self.assertEqual(first["proposal_id"], again["proposal_id"])
        with self.assertRaises(ValueError):
            store.propose("email.send", request_key="same-request",
                          **self.email(body="Different body"))
        with self.assertRaises(ValueError):
            store.propose("email.draft", request_key="same-request", **self.email())
        self.assertEqual(len(store.list()), 1)

    def test_expired_proposal_cannot_be_approved_or_executed(self):
        store = self.store()
        with patch.object(module, "now", return_value=datetime(2026, 1, 1, tzinfo=timezone.utc)):
            proposal = store.propose("email.send", **self.email())
        with patch.object(module, "now", return_value=datetime(2026, 1, 3, tzinfo=timezone.utc)):
            with self.assertRaises(ValueError):
                store.approve(proposal["proposal_id"], proposal["approval_code"])
            self.assertEqual(store.get(proposal["proposal_id"])["status"], "expired")
            self.assertEqual(store.list(status="pending"), [])
        self.assertEqual(self.calls, [])

    def test_calendar_create_builds_pinned_fixed_write(self):
        store = self.store()
        proposal = store.propose(
            "calendar.create", title="Lunch", start="2026-11-12T15:00:00+01:00",
            end="2026-11-12T16:00:00+01:00", description="", location="")
        store.approve(proposal["proposal_id"], proposal["approval_code"])
        store.execute(proposal["proposal_id"], proposal["approval_code"])
        action, payload = self.calls[0]
        request = module.build_execution_request(action, payload)
        tool = request["tools"][0]
        self.assertEqual(tool["tool_slug"], "GOOGLECALENDAR_CREATE_EVENT")
        self.assertEqual(tool["account"], "Bailey Calendar")
        self.assertEqual(tool["arguments"]["start_datetime"], "2026-11-12T15:00:00+01:00")
        self.assertEqual(tool["arguments"]["send_updates"], "none")
        self.assertFalse(tool["arguments"]["create_meeting_room"])
        self.assertTrue(tool["arguments"]["exclude_organizer"])
        self.assertFalse(request["sync_response_to_workbench"])

    def test_email_execution_uses_plain_text_and_no_signature(self):
        store = self.store()
        proposal = store.propose(
            "email.send", to=["a@example.com", "b@example.com"], cc=["c@example.com"],
            subject="Subject", body="Line one\nLine two")
        store.approve(proposal["proposal_id"], proposal["approval_code"])
        store.execute(proposal["proposal_id"], proposal["approval_code"])
        action, payload = self.calls[0]
        tool = module.build_execution_request(action, payload)["tools"][0]
        self.assertEqual(tool["tool_slug"], "GMAIL_SEND_EMAIL")
        self.assertEqual(tool["arguments"]["recipient_email"], "a@example.com")
        self.assertEqual(tool["arguments"]["extra_recipients"], ["b@example.com"])
        self.assertFalse(tool["arguments"]["is_html"])
        self.assertFalse(tool["arguments"]["include_signature"])

    def test_calendar_validation_and_delete_requires_visible_title(self):
        store = self.store()
        with self.assertRaises(ValueError):
            store.propose("calendar.create", title="No zone",
                          start="2026-11-12T15:00:00", end="2026-11-12T16:00:00")
        with self.assertRaises(ValueError):
            store.propose("calendar.create", title="Backwards",
                          start="2026-11-12T16:00:00+01:00", end="2026-11-12T15:00:00+01:00")
        with self.assertRaises(ValueError):
            store.propose("calendar.delete", event_id="not a real id", title="Event")
        with self.assertRaises(ValueError):
            store.propose("calendar.delete", event_id="abc123")
        delete = store.propose("calendar.delete", event_id="abc123", title="Old event")
        self.assertEqual(delete["preview"]["event_id"], "abc123")
        self.assertEqual(delete["preview"]["before"]["etag"], "version-1")

    def test_email_validation(self):
        store = self.store()
        with self.assertRaises(ValueError):
            store.propose("email.send", to=[], subject="Hi", body="Body")
        with self.assertRaises(ValueError):
            store.propose("email.send", to=["not-an-email"], subject="Hi", body="Body")
        with self.assertRaises(ValueError):
            store.propose("email.send", to=["a@example.com"])
        with self.assertRaises(ValueError):
            store.propose("email.send", to=["a@example.com"], subject="Hi", body="x",
                          event_id="not-an-email-field")
        draft = store.propose("email.draft", subject="Draft", body="Body")
        self.assertEqual(draft["preview"]["to"], [])

    def test_failed_execution_is_terminal_and_never_retries(self):
        calls = []
        def fail(action, payload):
            calls.append((action, payload))
            raise RuntimeError("provider down")
        store = self.store(fail)
        proposal = store.propose("email.send", **self.email())
        store.approve(proposal["proposal_id"], proposal["approval_code"])
        with self.assertRaises(RuntimeError):
            store.execute(proposal["proposal_id"], proposal["approval_code"])
        self.assertEqual(store.get(proposal["proposal_id"])["status"], "uncertain")
        with self.assertRaises(ValueError):
            store.execute(proposal["proposal_id"], proposal["approval_code"])
        self.assertEqual(len(calls), 1)

    def test_payload_tampering_fails_closed(self):
        store = self.store()
        proposal = store.propose("email.send", **self.email())
        store.approve(proposal["proposal_id"], proposal["approval_code"])
        with closing(sqlite3.connect(store.path)) as db:
            db.execute("UPDATE proposals SET payload=? WHERE id=?",
                       (json.dumps({"to": ["attacker@example.com"], "cc": [], "bcc": [],
                                    "subject": "Changed", "body": "Changed"}, separators=(",", ":")),
                        proposal["proposal_id"]))
            db.commit()
        with self.assertRaises(ValueError):
            store.execute(proposal["proposal_id"], proposal["approval_code"])
        self.assertEqual(self.calls, [])

    def test_private_database_wal_and_symlink_fail_closed(self):
        store = self.store()
        self.assertEqual(store.path.stat().st_mode & 0o777, 0o600)
        with store.connection() as db:
            self.assertEqual(db.execute("PRAGMA journal_mode").fetchone()[0], "wal")
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        target = self.home / "elsewhere"
        store.path.rename(target)
        store.path.symlink_to(target)
        with self.assertRaises(ValueError):
            module.Writes(self.home)

    def test_model_can_cancel_only_unapproved_proposal(self):
        store = self.store()
        proposal = store.propose("email.send", **self.email())
        self.assertEqual(store.cancel(proposal["proposal_id"])["status"], "cancelled")
        with self.assertRaises(ValueError):
            store.approve(proposal["proposal_id"], proposal["approval_code"])
        approved = store.propose("email.send", **self.email())
        store.approve(approved["proposal_id"], approved["approval_code"])
        with self.assertRaises(ValueError):
            store.cancel(approved["proposal_id"])

    def test_tool_surface_has_no_approve_or_execute_action(self):
        actions = module.SCHEMA["parameters"]["properties"]["action"]["enum"]
        self.assertEqual(actions, ["propose", "list", "status", "cancel"])
        self.assertNotIn("approve", actions)
        self.assertNotIn("execute", actions)

    def test_nested_provider_errors_and_empty_results_never_mark_sent(self):
        samples = [
            {'successful':True,'data':{'results':[{'response':{'successful':False,'error':'denied'}}]}},
            {'successful':True,'data':{'results':[]}},
            {'successful':True,'data':{'results':[{}]}},
            {'successful':True,'data':{'results':[{'response':{'error':'denied'}}]}},
            {},
        ]
        for response in samples:
            with self.subTest(response=response):
                store=self.store(lambda action,payload:response)
                proposal=store.propose('email.send',**self.email())
                store.approve(proposal['proposal_id'],proposal['approval_code'])
                with self.assertRaises(RuntimeError):
                    store.execute(proposal['proposal_id'],proposal['approval_code'])
                self.assertEqual(store.get(proposal['proposal_id'])['status'],'failed')

    def test_success_without_receipt_is_uncertain_and_cannot_retry(self):
        store=self.store(lambda action,payload:{'successful':True,'data':{}})
        proposal=store.propose('email.send',**self.email())
        store.approve(proposal['proposal_id'],proposal['approval_code'])
        with self.assertRaises(RuntimeError): store.execute(proposal['proposal_id'],proposal['approval_code'])
        self.assertEqual(store.get(proposal['proposal_id'])['status'],'uncertain')
        with self.assertRaises(ValueError): store.execute(proposal['proposal_id'],proposal['approval_code'])

    def test_approval_binds_action_as_well_as_body(self):
        store=self.store()
        proposal=store.propose('email.draft',**self.email())
        store.approve(proposal['proposal_id'],proposal['approval_code'])
        with closing(sqlite3.connect(store.path)) as db:
            db.execute("UPDATE proposals SET action='email.send' WHERE id=?",(proposal['proposal_id'],))
            db.commit()
        with self.assertRaises(ValueError): store.execute(proposal['proposal_id'],proposal['approval_code'])
        self.assertEqual(self.calls,[])

    def test_calendar_guest_and_recurring_events_are_rejected_in_code(self):
        store=self.store()
        for extra in ({'attendees':[{'email':'guest@example.com'}]}, {'attendeesOmitted':True},
                      {'recurrence':['RRULE:FREQ=DAILY']}, {'recurringEventId':'series'},
                      {'organizer':{'self':False}}, {'eventType':'birthday'}):
            with self.subTest(extra=extra):
                store.reader=lambda identifier:dict(self.read_event(identifier),**extra)
                with self.assertRaises(ValueError):
                    store.propose('calendar.delete',event_id='abc123',title='Old event')
        self.assertEqual(self.calls,[])

    def test_calendar_change_after_review_blocks_execution(self):
        store=self.store()
        proposal=store.propose('calendar.delete',event_id='abc123',title='Old event')
        store.approve(proposal['proposal_id'],proposal['approval_code'])
        store.reader=lambda identifier:dict(self.read_event(identifier),etag='changed-version')
        with self.assertRaises(RuntimeError): store.execute(proposal['proposal_id'],proposal['approval_code'])
        self.assertEqual(self.calls,[])
        self.assertEqual(store.get(proposal['proposal_id'])['status'],'failed')

    def test_calendar_update_uses_patch_without_touching_other_fields(self):
        store=self.store()
        proposal=store.propose('calendar.update',event_id='abc123',title='New title',
                               start='2026-11-12T16:00:00+01:00',end='2026-11-12T17:00:00+01:00')
        request=module.build_execution_request('calendar.update',proposal['preview'])['tools'][0]
        self.assertEqual(request['tool_slug'],'GOOGLECALENDAR_PATCH_EVENT')
        fields=request['arguments']
        self.assertIn('start_time',fields)
        self.assertNotIn('start_datetime',fields)
        for untouched in ('attendees','recurrence','reminders','conference_data','create_meeting_room'):
            self.assertNotIn(untouched,fields)

    def test_concurrent_execution_only_calls_provider_once(self):
        from concurrent.futures import ThreadPoolExecutor
        import threading
        entered,release=threading.Event(),threading.Event()
        def blocked(action,payload):
            self.calls.append((action,payload))
            entered.set()
            release.wait(5)
            return {'successful':True,'data':{'id':'receipt-123'}}
        store=self.store(blocked)
        proposal=store.propose('email.send',**self.email())
        store.approve(proposal['proposal_id'],proposal['approval_code'])
        with ThreadPoolExecutor(max_workers=2) as pool:
            first=pool.submit(store.execute,proposal['proposal_id'],proposal['approval_code'])
            self.assertTrue(entered.wait(5))
            try:
                with self.assertRaises(ValueError): store.execute(proposal['proposal_id'],proposal['approval_code'])
            finally:
                release.set()
            self.assertEqual(first.result(timeout=5)['status'],'executed')
        self.assertEqual(len(self.calls),1)

    def test_expired_filter_matches_effective_status(self):
        store=self.store()
        with patch.object(module,'now',return_value=datetime(2026,1,1,tzinfo=timezone.utc)):
            proposal=store.propose('email.send',**self.email())
        with patch.object(module,'now',return_value=datetime(2026,1,3,tzinfo=timezone.utc)):
            self.assertEqual([p['proposal_id'] for p in store.list(status='expired')],[proposal['proposal_id']])
            self.assertEqual(store.list(status='proposed'),[])


    def test_operator_proposal_records_actual_actor(self):
        store=self.store()
        proposal=store.propose('email.draft',actor='operator:owner-approved-test',**self.email())
        self.assertEqual(store.full(proposal['proposal_id'])['events'][0]['actor'],'operator:owner-approved-test')
