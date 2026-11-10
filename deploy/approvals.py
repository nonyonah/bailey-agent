"""Operator-only approval CLI for Bailey external write proposals."""
import argparse
import getpass
import importlib.util
import json
import os
from pathlib import Path
import sys


def load(home):
    plugin = Path(__file__).resolve().parents[1] / "plugins/bailey_productivity"
    sys.path.insert(0, str(plugin))
    spec = importlib.util.spec_from_file_location("bailey_writes", plugin / "writes.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, module.Writes(home)


def print_proposal(item):
    print(f"Proposal: {item['proposal_id']}")
    print(f"Action: {item['action']}")
    print(f"Status: {item['status']}")
    print(f"Summary: {item['summary']}")
    print(f"Approval code: {item['approval_code']}")
    print(f"Created: {item['created_at']}")
    print(f"Expires: {item['expires_at']}")
    if item.get("approved_at"):
        print(f"Approved: {item['approved_at']}")
    if item.get("executed_at"):
        print(f"Executed: {item['executed_at']}")
    if item.get("result_summary"):
        print(f"Result: {item['result_summary']}")
    if item.get("error"):
        print(f"Error: {item['error']}")


def main(argv=None):
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        print("Run as the bailey service user: sudo -iu bailey ...", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description="Review and approve Bailey external write proposals")
    parser.add_argument("--home", type=Path, default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    listing = sub.add_parser("list")
    listing.add_argument("--status", default="pending",
                         choices=["pending", "proposed", "approved", "executing", "executed",
                                  "failed", "uncertain", "rejected", "cancelled", "expired", "all"])
    listing.add_argument("--limit", type=int, default=20)

    show = sub.add_parser("show")
    show.add_argument("proposal_id")

    approve = sub.add_parser("approve")
    approve.add_argument("proposal_id")
    approve.add_argument("--confirm", required=True)
    approve.add_argument("--note", default="")
    approve.add_argument("--execute", action="store_true")

    execute = sub.add_parser("execute")
    execute.add_argument("proposal_id")
    execute.add_argument("--confirm", required=True)

    reject = sub.add_parser("reject")
    reject.add_argument("proposal_id")
    reject.add_argument("--note", default="")

    events = sub.add_parser("events")
    events.add_argument("proposal_id")

    args = parser.parse_args(argv)
    home = args.home or Path(os.environ.get("HERMES_HOME") or (Path.home() / "data"))
    actor = f"operator:{getpass.getuser()}"
    try:
        _, store = load(home)
        if args.command == "list":
            items = store.list(status=args.status, limit=args.limit)
            if not items:
                print("No proposals.")
                return 0
            for item in items:
                print_proposal(item)
                print()
            return 0
        if args.command == "show":
            data = store.full(args.proposal_id)
            print_proposal(data)
            print("Payload:")
            print(json.dumps(data["preview"], indent=2, ensure_ascii=False))
            print("Events:")
            for item in data["events"]:
                print(f"  {item['at']} {item['action']} by {item['actor']} {item['details']}")
            return 0
        if args.command == "events":
            data = store.full(args.proposal_id)
            for item in data["events"]:
                print(f"{item['at']} {item['action']} by {item['actor']} {item['details']}")
            return 0
        if args.command == "approve":
            result = store.approve(args.proposal_id, args.confirm, actor=actor, note=args.note)
            print_proposal(result)
            if args.execute:
                result = store.execute(args.proposal_id, args.confirm, actor=actor)
                print()
                print_proposal(result)
            else:
                print()
                print("Approved but not executed. Nothing has been sent or changed.")
            return 0
        if args.command == "execute":
            result = store.execute(args.proposal_id, args.confirm, actor=actor)
            print_proposal(result)
            return 0
        if args.command == "reject":
            result = store.reject(args.proposal_id, actor=actor, note=args.note)
            print_proposal(result)
            return 0
        raise ValueError("Unknown command")
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception:
        print("Error: operator command failed; no further action was taken", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
