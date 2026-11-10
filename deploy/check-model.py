"""One real free-model tool-call probe using native Hermes credential resolution."""
import json
import sys


def main():
    from hermes_cli.runtime_provider import resolve_runtime_provider
    from openai import OpenAI
    credentials = resolve_runtime_provider(requested="openrouter", target_model="openrouter/free")
    if not credentials.get("api_key"):
        raise RuntimeError("No saved OpenRouter credential")
    client = OpenAI(api_key=credentials["api_key"], base_url=credentials["base_url"],
                    timeout=45, max_retries=0)
    response = client.chat.completions.create(
        model="openrouter/free", max_tokens=512,
        messages=[{"role": "user", "content": "Call check_ready with ready=true. This is a harmless connection test."}],
        tools=[{"type": "function", "function": {"name": "check_ready",
               "description": "Report whether this test request was understood; no action is executed.",
               "parameters": {"type": "object", "properties": {"ready": {"type": "boolean"}},
                              "required": ["ready"], "additionalProperties": False}}}],
        tool_choice={"type": "function", "function": {"name": "check_ready"}})
    calls = response.choices[0].message.tool_calls or []
    if not any(call.function.name == "check_ready" and
               json.loads(call.function.arguments).get("ready") is True for call in calls):
        raise RuntimeError("The free model did not return the required structured tool call")
    print("OpenRouter free-model inference and structured tool calling verified; no tool action executed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # No provider payload, credential, or exception text is printed.
        print(f"Free-model probe failed ({type(exc).__name__}, HTTP {getattr(exc, 'status_code', 'n/a')})", file=sys.stderr)
        sys.exit(1)
