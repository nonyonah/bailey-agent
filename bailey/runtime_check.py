"""Installed-Hermes compatibility check, deliberately fails closed on API drift."""
import json
import argparse
import os
from pathlib import Path
from bailey.profile import validate, profile_phase

ALLOWED = {"memory", "session_search", "text_to_speech"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Check installed APIs/tools before account login; never used to activate the gateway")
    args = parser.parse_args()
    home = Path(os.environ["HERMES_HOME"])
    validate(home, require_credentials=not args.offline)
    phase = profile_phase(home)
    from hermes_cli.config import load_config
    from hermes_cli.tools_config import _get_platform_tools
    from model_tools import get_tool_definitions
    cfg = load_config()
    if not args.offline:
        from hermes_cli.runtime_provider import resolve_runtime_provider
        creds = resolve_runtime_provider(requested="openrouter", target_model="openrouter/free")
        if not creds.get("api_key"):
            raise RuntimeError("OpenRouter model credentials are unavailable")
    for platform in ("cli", "photon", "slack", "whatsapp_cloud", "cron"):
        toolsets = _get_platform_tools(cfg, platform)
        # Hermes 0.23 may replace deferred schemas with discovery/call wrappers.
        # Inspect the full scoped catalog, so those wrappers cannot hide extra tools.
        definitions = get_tool_definitions(enabled_toolsets=sorted(toolsets), quiet_mode=True,
                                           skip_tool_search_assembly=True)
        names = {item.get("function", {}).get("name", item.get("name")) for item in definitions}
        permitted = ALLOWED if platform != "cron" else ALLOWED - {"text_to_speech"}
        if phase == 2 and platform in {"cli", "photon", "slack"}:
            permitted = permitted | {"bailey_tasks", "bailey_accounts"}
        if not names or not names <= permitted:
            raise RuntimeError(f"Unsafe or incompatible resolved tools for {platform}")
        if platform in {"photon", "slack", "whatsapp_cloud"} and names != permitted:
            raise RuntimeError("Required Phase 1 tools are unavailable")
        exposed = get_tool_definitions(enabled_toolsets=sorted(toolsets), quiet_mode=True)
        exposed_names = {item.get("function", {}).get("name", item.get("name")) for item in exposed}
        if not exposed_names <= permitted | {"tool_search", "tool_describe", "tool_call"}:
            raise RuntimeError(f"Unsafe exposed tool wrappers for {platform}")
    # Verify the callable shape we depend on before registering anything.
    import inspect
    from tools.cronjob_tools import cronjob
    params = inspect.signature(cronjob).parameters
    for key in ("action", "enabled_toolsets", "timezone", "deliver", "skills"):
        if key not in params:
            raise RuntimeError("Installed Hermes cron API is incompatible")
    print(json.dumps({"phase": phase, "tool_policy": "verified", "payment_execution": "disabled",
                      "credentials_checked": not args.offline}))


if __name__ == "__main__":
    main()
