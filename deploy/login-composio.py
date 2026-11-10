"""Operator-only OAuth staging; live assistant tools remain unchanged."""
from types import SimpleNamespace
from hermes_cli.mcp_config import cmd_mcp_login

cmd_mcp_login(SimpleNamespace(name="composio", flow="browser"))
