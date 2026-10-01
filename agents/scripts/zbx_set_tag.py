"""Set or remove a host tag on selected hosts (other tags are kept).

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  zbx_set_tag.py (--host NAME ... | --group GROUP | --tag-filter TAG=VALUE) --set TAG=VALUE [--dry-run]
  zbx_set_tag.py (--host NAME ... | --group GROUP | --tag-filter TAG=VALUE) --remove TAG [--dry-run]

Tags with a meaning in this deployment (docs/operacion/alertas.md): uplink=PARENT (use zbx_set_uplink.py),
escalation=off (no escalation), notificar=no (problems only in the dashboard, no messages).
"""
import argparse

from zbx_api import api_from_stdin, find_hosts, set_host_tag


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", nargs="*", default=[])
    parser.add_argument("--group")
    parser.add_argument("--tag-filter")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--set", metavar="TAG=VALUE")
    action.add_argument("--remove", metavar="TAG")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.host or args.group or args.tag_filter):
        parser.error("select hosts with --host, --group or --tag-filter")

    api = api_from_stdin()
    for host in find_hosts(api, args.host, args.group, args.tag_filter, selectTags=["tag", "value"]):
        if args.set:
            tag, _, value = args.set.partition("=")
            if any(t["tag"] == tag and t["value"] == value for t in host["tags"]):
                print(f"{host['name']}: ya tiene {tag}={value}")
                continue
            print(f"{host['name']}: {tag}={value}{' (dry-run)' if args.dry_run else ''}")
            if not args.dry_run:
                set_host_tag(api, host["hostid"], tag, value)
        else:
            if not any(t["tag"] == args.remove for t in host["tags"]):
                continue
            print(f"{host['name']}: quitar {args.remove}{' (dry-run)' if args.dry_run else ''}")
            if not args.dry_run:
                api.call("host.update", {"hostid": host["hostid"], "tags": [t for t in host["tags"] if t["tag"] != args.remove]})


if __name__ == "__main__":
    main()
