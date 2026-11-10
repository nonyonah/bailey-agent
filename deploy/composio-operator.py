"""Operator-only account discovery/linking; never exposes generic execution to the model."""
import asyncio
import inspect
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


def unpack(result):
    if getattr(result, 'is_error', False):
        raise RuntimeError('Composio reported an error')
    structured = getattr(result, 'structured_content', None)
    if structured is not None:
        return structured
    parts = [c.text for c in result.content if getattr(c, 'type', None) == 'text']
    return [json.loads(part) for part in parts]


def walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def save(home, name, value):
    path = home/name
    if path.is_symlink():
        raise ValueError('Refusing a symlink')
    fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream)
    path.chmod(0o600)


async def main():
    from tools.mcp_tool_discovery import _connect_server
    home = Path(os.environ['HERMES_HOME'])
    config = json.loads((home/'config.yaml').read_text())['mcp_servers']['composio']
    server = await _connect_server('composio', config)
    try:
        schemas = unpack(await server.session.call_tool('COMPOSIO_GET_TOOL_SCHEMAS', {
            'tool_slugs':['GMAIL_FETCH_EMAILS','GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID','GOOGLECALENDAR_EVENTS_LIST']}))
        save(home, 'phase2-read-schemas.json', schemas)
        print(json.dumps(schemas))

    finally:
        result = server.shutdown()
        if inspect.isawaitable(result):
            await result


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f'Composio account setup incomplete ({type(exc).__name__}); inspect privately.',file=sys.stderr)
        sys.exit(1)
