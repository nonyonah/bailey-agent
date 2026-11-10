"""Verify current Composio write schemas without executing any external writes."""
import asyncio
import importlib.util
import inspect
import json
from pathlib import Path
import sys

plugin=Path(__file__).resolve().parents[1]/'plugins/bailey_productivity'
sys.path.insert(0,str(plugin))
from accounts import CONFIG, unpack
from writes import ACTIONS, normalize, build_execution_request


def schemas_in(value):
    if isinstance(value,dict):
        if 'tool_slug' in value and 'input_schema' in value:
            yield value['tool_slug'],value['input_schema']
        for child in value.values(): yield from schemas_in(child)
    elif isinstance(value,list):
        for child in value: yield from schemas_in(child)


async def main():
    from tools.mcp_tool_discovery import _connect_server
    requests=[]
    for action in sorted(ACTIONS):
        if action.startswith('email.'):
            fields={'to':['owner@example.com'],'subject':'Contract check only','body':'Not sent'}
        elif action=='calendar.delete':
            fields={'event_id':'contractcheck123','title':'Contract check only'}
        else:
            fields={'title':'Contract check only','start':'2026-11-12T10:00:00+01:00',
                    'end':'2026-11-12T11:00:00+01:00'}
            if action=='calendar.update': fields['event_id']='contractcheck123'
        requests.append(build_execution_request(action,normalize(action,fields))['tools'][0])
    server=await _connect_server('composio',CONFIG)
    try:
        result=unpack(await server.session.call_tool('COMPOSIO_GET_TOOL_SCHEMAS',{
            'tool_slugs':sorted({r['tool_slug'] for r in requests})+['GOOGLECALENDAR_EVENTS_GET']}))
        schemas=dict(schemas_in(result))
        for request in requests:
            schema=schemas[request['tool_slug']]
            supplied=set(request['arguments'])
            if supplied-set(schema.get('properties',{})) or set(schema.get('required',[]))-supplied:
                raise RuntimeError('Composio write contract changed; do not activate')
        if not schemas.get('GOOGLECALENDAR_EVENTS_GET'):
            raise RuntimeError('Calendar preflight read contract unavailable')
        print(json.dumps({'write_contracts':'verified','tool_count':len(requests),
                          'external_writes_executed':0}))
    finally:
        closing=server.shutdown()
        if inspect.isawaitable(closing): await closing


if __name__=='__main__': asyncio.run(main())
