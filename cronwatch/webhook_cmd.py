"""CLI commands for managing webhook endpoints in the registry."""

import argparse
import json
import sys

from cronwatch.webhook_registry import WebhookEndpoint, WebhookRegistry

DEFAULT_REGISTRY = "webhooks.json"


def _get_registry(args) -> WebhookRegistry:
    return WebhookRegistry(getattr(args, "registry", DEFAULT_REGISTRY))


def cmd_add(args) -> int:
    reg = _get_registry(args)
    ep = WebhookEndpoint(
        name=args.name,
        url=args.url,
        secret=args.secret,
        timeout=args.timeout,
        enabled=not args.disabled,
    )
    reg.register(ep)
    print(f"Registered webhook '{args.name}' -> {args.url}")
    return 0


def cmd_remove(args) -> int:
    reg = _get_registry(args)
    if reg.remove(args.name):
        print(f"Removed webhook '{args.name}'")
        return 0
    print(f"Webhook '{args.name}' not found", file=sys.stderr)
    return 1


def cmd_list(args) -> int:
    reg = _get_registry(args)
    endpoints = reg.all()
    if not endpoints:
        print("No webhooks registered.")
        return 0
    for ep in endpoints:
        status = "enabled" if ep.enabled else "disabled"
        print(f"  {ep.name:20s}  {ep.url}  [{status}]")
    return 0


def cmd_show(args) -> int:
    reg = _get_registry(args)
    ep = reg.get(args.name)
    if ep is None:
        print(f"Webhook '{args.name}' not found", file=sys.stderr)
        return 1
    print(json.dumps(ep.to_dict(), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Manage cronwatch webhook endpoints")
    p.add_argument("--registry", default=DEFAULT_REGISTRY)
    sub = p.add_subparsers(dest="command")

    add_p = sub.add_parser("add", help="Register a webhook")
    add_p.add_argument("name")
    add_p.add_argument("url")
    add_p.add_argument("--secret", default=None)
    add_p.add_argument("--timeout", type=int, default=10)
    add_p.add_argument("--disabled", action="store_true")

    rm_p = sub.add_parser("remove", help="Remove a webhook")
    rm_p.add_argument("name")

    sub.add_parser("list", help="List all webhooks")

    show_p = sub.add_parser("show", help="Show webhook details")
    show_p.add_argument("name")

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {"add": cmd_add, "remove": cmd_remove, "list": cmd_list, "show": cmd_show}
    fn = dispatch.get(args.command)
    if fn is None:
        parser.print_help()
        return 1
    return fn(args)


if __name__ == "__main__":
    sys.exit(main())
