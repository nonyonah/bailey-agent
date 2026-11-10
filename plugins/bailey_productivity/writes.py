"""Approval-gated external writes; the model can only create proposals."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
import uuid
from zoneinfo import ZoneInfo
try:
    from .responses import check_result, resource_id, ProviderFailure
except ImportError:
    from responses import check_result, resource_id, ProviderFailure

LAGOS = ZoneInfo("Africa/Lagos")
ACTIONS = {"email.send", "email.draft", "calendar.create", "calendar.update", "calendar.delete"}
STATES = {"proposed", "approved", "executing", "executed", "failed", "uncertain", "rejected", "cancelled", "expired"}
PROPOSAL_TTL = timedelta(hours=24)
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
EVENT_ID = re.compile(r"[A-Za-z0-9_+/-]{1,1024}")


def now():
    return datetime.now(timezone.utc)


def canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def instant(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be an ISO date/time with a timezone offset")
    try:
        result = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO date/time with a timezone offset") from exc
    if result.tzinfo is None:
        raise ValueError(f"{label} needs a timezone offset; Africa/Lagos is +01:00")
    return result.astimezone(LAGOS)


def text(value, label, maximum, strip=True):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")
    if strip:
        value = value.strip()
    if not value.strip() or len(value) > maximum or "\x00" in value:
        raise ValueError(f"{label} must be nonempty text, at most {maximum} characters")
    return value


def optional_text(value, label, maximum):
    if value is None or value == "":
        return ""
    return text(value, label, maximum)


def email_list(value, label, required=False, maximum=10):
    if value is None:
        value = []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError(f"{label} must be a list of at most {maximum} addresses")
    result = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{label} must contain email addresses")
        item = item.strip()
        if len(item) > 320 or not EMAIL.fullmatch(item):
            raise ValueError(f"{label} contains an invalid email address")
        result.append(item)
    if required and not result:
        raise ValueError(f"{label} needs at least one recipient")
    return result


def event_id(value):
    value = text(value, "Event ID", 1024)
    if not EVENT_ID.fullmatch(value):
        raise ValueError("Use the event ID returned by calendar search")
    return value


def window(payload):
    start = datetime.fromisoformat(payload["start"])
    end = datetime.fromisoformat(payload["end"])
    return f"{start:%Y-%m-%d %H:%M}-{end:%H:%M} Africa/Lagos"


def describe(action, payload):
    if action == "email.send":
        to = ", ".join(payload["to"]) or "no recipient"
        return f"Send email to {to} with subject {payload['subject'] or '(none)'!r}"
    if action == "email.draft":
        to = ", ".join(payload["to"]) or "no recipient"
        return f"Create email draft to {to} with subject {payload['subject'] or '(none)'!r}"
    if action == "calendar.create":
        return f"Create calendar event {payload['title']!r} on {window(payload)}"
    if action == "calendar.update":
        return f"Update calendar event {payload['event_id']} to {payload['title']!r} on {window(payload)}"
    if action == "calendar.delete":
        return f"Delete calendar event {payload['title']!r} ({payload['event_id']})"
    raise ValueError("Unsupported write action")


def normalize(action, fields):
    if action == "email.send" or action == "email.draft":
        allowed = {"to", "cc", "bcc", "subject", "body"}
        extra = set(fields) - allowed
        if extra:
            raise ValueError(f"Unsupported email field: {sorted(extra)[0]}")
        to = email_list(fields.get("to"), "To", required=action == "email.send")
        cc = email_list(fields.get("cc"), "Cc")
        bcc = email_list(fields.get("bcc"), "Bcc")
        subject = fields.get("subject")
        body = fields.get("body")
        if subject is None and body is None:
            raise ValueError("An email needs a subject or body")
        subject = text(subject, "Subject", 200).replace("\r", " ").replace("\n", " ") if subject is not None else ""
        body = text(body, "Body", 20000, strip=False) if body is not None else ""
        return {"to": to, "cc": cc, "bcc": bcc, "subject": subject, "body": body}

    if action == "calendar.create" or action == "calendar.update":
        allowed = {"title", "start", "end", "description", "location"}
        if action == "calendar.update":
            allowed.add("event_id")
        extra = set(fields) - allowed
        if extra:
            raise ValueError(f"Unsupported calendar field: {sorted(extra)[0]}")
        if action == "calendar.update" and not fields.get("event_id"):
            raise ValueError("Event ID is required")
        title = text(fields.get("title"), "Title", 300)
        start = instant(fields.get("start"), "Start")
        end = instant(fields.get("end"), "End")
        if not timedelta(minutes=1) <= end - start <= timedelta(days=30):
            raise ValueError("Calendar events must last between 1 minute and 30 days")
        payload = {"title": title, "start": start.isoformat(), "end": end.isoformat(),
                   "description": optional_text(fields.get("description"), "Description", 8000),
                   "location": optional_text(fields.get("location"), "Location", 500)}
        if action == "calendar.update":
            payload["event_id"] = event_id(fields.get("event_id"))
        return payload

    if action == "calendar.delete":
        extra = set(fields) - {"event_id", "title"}
        if extra:
            raise ValueError(f"Unsupported calendar field: {sorted(extra)[0]}")
        return {"event_id": event_id(fields.get("event_id")),
                "title": text(fields.get("title"), "Title", 300)}

    raise ValueError("Unsupported write action")


def build_execution_request(action, payload):
    if action == "email.send" or action == "email.draft":
        arguments = {"user_id": "me", "cc": payload["cc"], "bcc": payload["bcc"],
                     "subject": payload["subject"], "body": payload["body"],
                     "is_html": False, "include_signature": False}
        if payload["to"]:
            arguments["recipient_email"] = payload["to"][0]
            arguments["extra_recipients"] = payload["to"][1:]
        slug = "GMAIL_SEND_EMAIL" if action == "email.send" else "GMAIL_CREATE_EMAIL_DRAFT"
        account = "Bailey Gmail"
    elif action == "calendar.create" or action == "calendar.update":
        slug = "GOOGLECALENDAR_CREATE_EVENT" if action == "calendar.create" else "GOOGLECALENDAR_PATCH_EVENT"
        account = "Bailey Calendar"
        arguments = {"calendar_id": "primary", "summary": payload["title"],
                     "start_datetime": payload["start"], "end_datetime": payload["end"],
                     "timezone": "Africa/Lagos", "description": payload["description"],
                     "location": payload["location"], "send_updates": "none",
                     "create_meeting_room": False}
        if action == "calendar.create":
            arguments["exclude_organizer"] = True
        else:
            # PATCH preserves attendees, reminders, recurrence and conference details.
            arguments.pop('create_meeting_room')
            arguments['start_time'] = arguments.pop('start_datetime')
            arguments['end_time'] = arguments.pop('end_datetime')
            arguments["event_id"] = payload["event_id"]
    elif action == "calendar.delete":
        slug, account = "GOOGLECALENDAR_DELETE_EVENT", "Bailey Calendar"
        arguments = {"calendar_id": "primary", "event_id": payload["event_id"], "send_updates": "none"}
    else:
        raise ValueError("Unsupported write action")
    return {"tools": [{"tool_slug": slug, "account": account, "arguments": arguments}],
            "sync_response_to_workbench": False}



def proposal_hash(action, payload):
    # Approval binds the action, content, account and exact provider operation.
    bound = {'action':action,'payload':payload,'request':build_execution_request(action,payload)}
    return hashlib.sha256(canonical(bound).encode('utf-8')).hexdigest()


def calendar_snapshot(event, identifier):
    if not isinstance(event,dict) or event.get('id') != identifier or not event.get('etag'):
        raise ValueError('Cannot verify the current calendar event')
    if (event.get('status') == 'cancelled' or event.get('attendees') or event.get('attendeesOmitted')
            or event.get('recurrence') or event.get('recurringEventId')
            or event.get('eventType','default') != 'default'
            or event.get('organizer',{}).get('self') is not True):
        raise ValueError('Only standalone, owner-organized events without guests can be changed')
    return {'event_id':identifier,'etag':event['etag'],'title':event.get('summary',''),
            'start':event.get('start'), 'end':event.get('end')}


def read_calendar_event(identifier):
    request={'tools':[{'tool_slug':'GOOGLECALENDAR_EVENTS_GET','account':'Bailey Calendar',
                      'arguments':{'calendar_id':'primary','event_id':identifier}}],
             'sync_response_to_workbench':False}
    from tools.mcp_tool_loop import _ensure_mcp_loop, _run_on_mcp_loop
    try:
        from .accounts import execute
    except ImportError:
        from accounts import execute
    _ensure_mcp_loop()
    result=_run_on_mcp_loop(lambda:execute(request),timeout=90)
    check_result(result)
    def find(value):
        if isinstance(value,dict):
            if value.get('id') == identifier and 'etag' in value:
                return value
            for key in ('data','result','results','response','response_data'):
                found=find(value.get(key))
                if found is not None: return found
        elif isinstance(value,list):
            for child in value:
                found=find(child)
                if found is not None: return found
    event=find(result)
    if event is None: raise ValueError('Provider returned no matching event')
    return event


def execute_composio(action, payload):
    from tools.mcp_tool_loop import _ensure_mcp_loop, _run_on_mcp_loop
    request = build_execution_request(action, payload)

    async def run():
        try:
            from .accounts import execute as account_execute
        except ImportError:
            from accounts import execute as account_execute
        return await account_execute(request)

    _ensure_mcp_loop()
    return _run_on_mcp_loop(run, timeout=90)


class Writes:
    def __init__(self, home, executor=None, reader=None):
        home = Path(home)
        if home.is_symlink() or not home.is_dir() or home.stat().st_mode & 0o077:
            raise ValueError("Write storage requires a private Hermes home")
        self.path = home / "bailey-writes.db"
        if self.path.is_symlink():
            raise ValueError("Refusing a symlinked write database")
        if not self.path.exists():
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        if self.path.stat().st_mode & 0o077:
            raise ValueError("Write database must be private")
        self.executor = executor or execute_composio
        self.reader = reader or read_calendar_event
        with self.connection() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("Unsupported write schema version")
            if version == 0:
                db.executescript("""
                BEGIN IMMEDIATE;
                CREATE TABLE proposals (
                  id TEXT PRIMARY KEY,
                  action TEXT NOT NULL CHECK(action IN (
                    'email.send','email.draft','calendar.create','calendar.update','calendar.delete')),
                  summary TEXT NOT NULL,
                  payload TEXT NOT NULL,
                  payload_hash TEXT NOT NULL,
                  status TEXT NOT NULL CHECK(status IN (
                    'proposed','approved','executing','executed','failed','uncertain','rejected','cancelled','expired')),
                  created_at TEXT NOT NULL,
                  expires_at TEXT NOT NULL,
                  approved_at TEXT,
                  approved_by TEXT,
                  executed_at TEXT,
                  result_summary TEXT,
                  error TEXT,
                  request_key TEXT UNIQUE);
                CREATE INDEX proposals_status ON proposals(status,expires_at);
                CREATE TABLE proposal_events (
                  id INTEGER PRIMARY KEY,
                  proposal_id TEXT NOT NULL REFERENCES proposals(id),
                  action TEXT NOT NULL,
                  actor TEXT NOT NULL,
                  at TEXT NOT NULL,
                  details TEXT NOT NULL);
                PRAGMA user_version=1;
                COMMIT;
                """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA busy_timeout=10000")
            db.execute("PRAGMA journal_mode=WAL")
            with db:
                yield db
        finally:
            db.close()

    def event(self, db, proposal_id, action, actor, details):
        db.execute("INSERT INTO proposal_events(proposal_id,action,actor,at,details) VALUES(?,?,?,?,?)",
                   (proposal_id, action, actor, now().isoformat(), canonical(details)))

    def row(self, db, proposal_id):
        proposal_id = text(proposal_id, "Proposal ID", 100)
        row = db.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if row is None:
            raise ValueError("Proposal not found")
        return row

    def summary(self, row, preview=False):
        status = row["status"]
        if status in {"proposed", "approved"} and row["expires_at"] <= now().isoformat():
            status = "expired"
        result = {"proposal_id": row["id"], "action": row["action"], "summary": row["summary"],
                  "status": status, "approval_code": row["payload_hash"][:12],
                  "created_at": row["created_at"], "expires_at": row["expires_at"],
                  "approved_at": row["approved_at"], "executed_at": row["executed_at"],
                  "result_summary": row["result_summary"], "error": row["error"]}
        if preview:
            result["preview"] = json.loads(row["payload"])
        return result

    def propose(self, action, request_key=None, actor="model", **fields):
        if action not in ACTIONS:
            raise ValueError("Unsupported write action")
        actor = text(actor, 'Actor', 100)
        if request_key is not None:
            request_key = text(request_key, "Request key", 200)
        payload = normalize(action, fields)
        if action in {"calendar.update", "calendar.delete"}:
            event = self.reader(payload['event_id'])
            payload['before'] = calendar_snapshot(event, payload['event_id'])
            if action == 'calendar.delete' and payload['title'] != payload['before']['title']:
                raise ValueError('Delete title does not match the current event; read it again')
        payload_text = canonical(payload)
        payload_hash = proposal_hash(action, payload)
        stamp = now()
        proposal_id = str(uuid.uuid4())
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if request_key:
                existing = db.execute("SELECT * FROM proposals WHERE request_key=?", (request_key,)).fetchone()
                if existing:
                    if existing["action"] != action or existing["payload_hash"] != payload_hash:
                        raise ValueError("Request key already belongs to a different proposal")
                    return self.summary(existing, preview=True)
            db.execute("""INSERT INTO proposals
                (id,action,summary,payload,payload_hash,status,created_at,expires_at,request_key)
                VALUES(?,?,?,?,?,'proposed',?,?,?)""",
                       (proposal_id, action, describe(action, payload), payload_text, payload_hash,
                        stamp.isoformat(), (stamp + PROPOSAL_TTL).isoformat(), request_key))
            self.event(db, proposal_id, "proposed", actor, {"action": action})
            return self.summary(self.row(db, proposal_id), preview=True)

    def list(self, status="pending", limit=20):
        if status not in STATES | {"pending", "all"} or type(limit) is not int or not 1 <= limit <= 50:
            raise ValueError("Invalid proposal filter or limit")
        clauses, args = [], []
        if status == "pending":
            clauses.append("status IN ('proposed','approved')")
            clauses.append("expires_at>?")
            args.append(now().isoformat())
        elif status == 'expired':
            clauses.append("status IN ('proposed','approved') AND expires_at<=?")
            args.append(now().isoformat())
        elif status != "all":
            clauses.append("status=?")
            args.append(status)
            if status in {'proposed','approved'}:
                clauses.append('expires_at>?')
                args.append(now().isoformat())
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.connection() as db:
            rows = db.execute("SELECT * FROM proposals" + where +
                              " ORDER BY created_at DESC LIMIT ?", [*args, limit]).fetchall()
            return [self.summary(row) for row in rows]

    def get(self, proposal_id, preview=False):
        with self.connection() as db:
            return self.summary(self.row(db, proposal_id), preview=preview)

    def full(self, proposal_id):
        with self.connection() as db:
            row = self.row(db, proposal_id)
            result = self.summary(row, preview=True)
            result["payload_hash"] = row["payload_hash"]
            result["events"] = [dict(item) for item in db.execute(
                "SELECT action,actor,at,details FROM proposal_events WHERE proposal_id=? ORDER BY id",
                (row["id"],)).fetchall()]
            return result

    def approve(self, proposal_id, code, actor="operator", note=""):
        code = text(code, "Approval code", 100).lower()
        actor = text(actor, "Actor", 100)
        note = optional_text(note, "Note", 1000)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self.row(db, proposal_id)
            if row["status"] != "proposed":
                raise ValueError("Only a proposed write can be approved")
            if row["expires_at"] <= now().isoformat():
                raise ValueError("Proposal expired; create a new proposal")
            if not hmac.compare_digest(code, row["payload_hash"][:12]):
                raise ValueError("Approval code does not match")
            db.execute("UPDATE proposals SET status='approved',approved_at=?,approved_by=? WHERE id=?",
                       (now().isoformat(), actor, row["id"]))
            self.event(db, row["id"], "approved", actor, {"note": note})
            return self.summary(self.row(db, row["id"]))

    def reject(self, proposal_id, actor="operator", note=""):
        actor = text(actor, "Actor", 100)
        note = optional_text(note, "Note", 1000)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self.row(db, proposal_id)
            if row["status"] not in {"proposed", "approved"}:
                raise ValueError("Only a pending write can be rejected")
            db.execute("UPDATE proposals SET status='rejected' WHERE id=?", (row["id"],))
            self.event(db, row["id"], "rejected", actor, {"note": note})
            return self.summary(self.row(db, row["id"]))

    def cancel(self, proposal_id, actor="model", note=""):
        actor = text(actor, "Actor", 100)
        note = optional_text(note, "Note", 1000)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self.row(db, proposal_id)
            if row["status"] != "proposed":
                raise ValueError("Only a proposed write can be cancelled by the model")
            db.execute("UPDATE proposals SET status='cancelled' WHERE id=?", (row["id"],))
            self.event(db, row["id"], "cancelled", actor, {"note": note})
            return self.summary(self.row(db, row["id"]))

    def execute(self, proposal_id, code, actor="operator"):
        code = text(code, "Approval code", 100).lower()
        actor = text(actor, "Actor", 100)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self.row(db, proposal_id)
            if row["status"] != "approved":
                raise ValueError("Only an approved write can execute")
            if row["expires_at"] <= now().isoformat():
                raise ValueError("Proposal expired; create a new proposal")
            if not hmac.compare_digest(code, row["payload_hash"][:12]):
                raise ValueError("Approval code does not match")
            if proposal_hash(row["action"], json.loads(row["payload"])) != row["payload_hash"]:
                raise ValueError("Proposal payload integrity check failed")
            db.execute("UPDATE proposals SET status='executing' WHERE id=?", (row["id"],))
            self.event(db, row["id"], "executing", actor, {})
            action, payload = row["action"], json.loads(row["payload"])
        try:
            if action in {"calendar.update", "calendar.delete"}:
                current = calendar_snapshot(self.reader(payload['event_id']), payload['event_id'])
                if current != payload['before']:
                    raise ProviderFailure('Calendar event changed after proposal; create a new proposal')
            result = self.executor(action, payload)
            if result is None:
                raise RuntimeError("Provider returned no result")
            check_result(result)
            identifier = resource_id(result)
            if action != 'calendar.delete' and not identifier:
                raise RuntimeError('Provider result has no resource receipt; verify externally before doing anything else')
            summary = canonical({'provider':'Composio / Google','resource_id':identifier,
                                 'action':action,'confirmed':True})
        except Exception as exc:
            with self.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                row = self.row(db, proposal_id)
                if row["status"] == "executing":
                    status = 'failed' if isinstance(exc, ProviderFailure) else 'uncertain'
                    error = ('Provider rejected the operation or preflight failed; review before creating a new proposal'
                             if status == 'failed' else
                             'Outcome unknown; check Gmail/Calendar before any new attempt. Automatic retry is blocked.')
                    db.execute("UPDATE proposals SET status=?,error=? WHERE id=?", (status,error,row['id']))
                    self.event(db,row['id'],status,actor,{'error':error})
            raise RuntimeError(error) from exc
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self.row(db, proposal_id)
            if row["status"] != "executing":
                raise ValueError("Proposal state changed during execution")
            db.execute("UPDATE proposals SET status='executed',executed_at=?,result_summary=?,error=NULL WHERE id=?",
                       (now().isoformat(), summary, row["id"]))
            self.event(db, row["id"], "executed", actor, {"result": summary[:500]})
            return self.summary(self.row(db, row["id"]))


SCHEMA = {
    "name": "bailey_writes",
    "description": (
        "Prepare an external write for explicit owner approval. This tool never sends email, "
        "creates/updates/deletes a calendar event, or executes anything; it only records a proposal. "
        "Use propose only when the owner explicitly asks to send, create, update, or delete. "
        "For calendar updates/deletes, first read the event with bailey_accounts and use its event_id. "
        "Calendar changes are limited to standalone, owner-organized events without guests; preflight verifies this in code. "
        "After proposing, tell the owner the proposal ID and approval code. Never claim the action "
        "happened until bailey_writes status says executed. The owner approves through the operator CLI; "
        "chat messages cannot approve or execute."
    ),
    "parameters": {"type": "object", "additionalProperties": False, "required": ["action"],
                   "properties": {
                       "action": {"type": "string", "enum": ["propose", "list", "status", "cancel"]},
                       "write_action": {"type": "string", "enum": sorted(ACTIONS)},
                       "proposal_id": {"type": "string", "maxLength": 100},
                       "request_key": {"type": "string", "maxLength": 200},
                       "to": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
                       "cc": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
                       "bcc": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
                       "subject": {"type": "string", "maxLength": 200},
                       "body": {"type": "string", "maxLength": 20000},
                       "event_id": {"type": "string", "maxLength": 1024},
                       "title": {"type": "string", "maxLength": 300},
                       "start": {"type": "string", "description": "ISO datetime with timezone offset. Africa/Lagos is +01:00. Ask if ambiguous."},
                       "end": {"type": "string", "description": "ISO datetime with timezone offset. Africa/Lagos is +01:00. Ask if ambiguous."},
                       "description": {"type": "string", "maxLength": 8000},
                       "location": {"type": "string", "maxLength": 500},
                       "status": {"type": "string", "enum": ["pending", "proposed", "approved", "executing",
                                                             "executed", "failed", "uncertain", "rejected", "cancelled",
                                                             "expired", "all"]},
                       "limit": {"type": "integer", "minimum": 1, "maximum": 50}}}}

FIELDS = {"to", "cc", "bcc", "subject", "body", "event_id", "title", "start", "end", "description", "location"}
ALLOWED = {
    "email.send": {"to", "cc", "bcc", "subject", "body"},
    "email.draft": {"to", "cc", "bcc", "subject", "body"},
    "calendar.create": {"title", "start", "end", "description", "location"},
    "calendar.update": {"event_id", "title", "start", "end", "description", "location"},
    "calendar.delete": {"event_id", "title"},
}


def handle(args, **kwargs):
    try:
        from hermes_constants import get_hermes_home
        store = Writes(get_hermes_home())
        action = args.get("action")
        if action == "propose":
            write_action = args.get("write_action")
            if write_action not in ACTIONS:
                raise ValueError("write_action is required")
            fields = {}
            for key in FIELDS:
                value = args.get(key)
                if value is None or value == "" or value == []:
                    continue
                if key not in ALLOWED[write_action]:
                    raise ValueError(f"{key} is not valid for {write_action}")
                fields[key] = value
            result = store.propose(write_action, request_key=args.get("request_key"), **fields)
            result["approval_instructions"] = (
                "Nothing was sent or changed. The owner must review this proposal and approve it "
                "with the operator CLI, then execute it separately."
            )
        elif action == "list":
            result = store.list(status=args.get("status", "pending"), limit=args.get("limit", 20))
        elif action == "status":
            result = store.get(args.get("proposal_id"))
        elif action == "cancel":
            result = store.cancel(args.get("proposal_id"), actor="model")
        else:
            raise ValueError("Unknown write action")
        return json.dumps({"success": True, "result": result}, ensure_ascii=False)
    except (ValueError, TypeError) as exc:
        return json.dumps({"success": False, "error": str(exc)})
    except Exception:
        return json.dumps({"success": False,
                           "error": "Write proposal storage unavailable; no external action was taken"})
