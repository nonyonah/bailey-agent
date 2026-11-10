"""Bounded native Hermes plugin; no terminal or worker execution."""
import json
from .tasks import Tasks

SCHEMA = {
    'name': 'bailey_tasks',
    'description': 'Manage the owner\'s persistent personal tasks. Only explicit owner commitments are confirmed. Tentative statements stay tentative. Completion requires the owner to say it is done. Recurrence creates the next occurrence only on completion. This tool schedules no push notifications.',
    'parameters': {'type': 'object', 'additionalProperties': False,
        'properties': {
            'action': {'type': 'string', 'enum': ['create','list','update','complete','confirm','cancel','today']},
            'task_id': {'type': 'string'},
            'title': {'type': 'string', 'maxLength': 300},
            'notes': {'type': 'string', 'maxLength': 4000},
            'due_at': {'type': ['string','null'], 'description': 'ISO datetime with timezone offset. Africa/Lagos is +01:00. Ask if ambiguous.'},
            'priority': {'type': 'string', 'enum': ['low','normal','high','urgent']},
            'recurrence': {'type': ['string','null'], 'enum': ['daily','weekly','monthly',None]},
            'confirmed': {'type': 'boolean', 'description': 'True only for an explicit owner instruction or confirmed commitment; default false.'},
            'status': {'type': 'string', 'enum': ['tentative','open','completed','cancelled','all']},
            'request_key': {'type': 'string', 'description': 'Reuse this key for a retry of the same create request; never reuse it for a different request.'},
            'limit': {'type': 'integer', 'minimum': 1, 'maximum': 100}},
        'required': ['action']}}


def handle(args, **kwargs):
    try:
        from hermes_constants import get_hermes_home
        store = Tasks(get_hermes_home())
        action = args.get('action')
        if action == 'create':
            result = store.create(**{k:v for k,v in args.items() if k in {
                'title','notes','due_at','priority','recurrence','confirmed','request_key'}})
        elif action == 'list':
            result = store.list(status=args.get('status','open'), limit=args.get('limit',50))
        elif action == 'today':
            result = {'today':store.list(today=True), 'overdue':store.list(overdue=True),
                      'undated': [t for t in store.list() if not t['due_at']],
                      'timezone':'Africa/Lagos', 'push_reminders_enabled':False}
        elif action == 'complete':
            result = store.complete(args.get('task_id'))
        elif action in {'confirm','cancel'}:
            result = store.update(args.get('task_id'),status='open' if action=='confirm' else 'cancelled')
        elif action == 'update':
            result = store.update(args.get('task_id'),**{k:v for k,v in args.items() if k in {'title','notes','due_at','priority'}})
        else:
            raise ValueError('Unknown task action')
        return json.dumps({'success':True,'result':result},ensure_ascii=False)
    except (ValueError,TypeError) as exc:
        return json.dumps({'success':False,'error':str(exc)})
    except Exception:
        return json.dumps({'success':False,'error':'Task storage unavailable; no completion is confirmed'})


def register(ctx):
    ctx.register_tool(name='bailey_tasks',toolset='bailey_tasks',schema=SCHEMA,handler=handle)

    from .accounts import SCHEMA as account_schema, handle as account_handler
    ctx.register_tool(name="bailey_accounts",toolset="bailey_accounts",schema=account_schema,handler=account_handler)
