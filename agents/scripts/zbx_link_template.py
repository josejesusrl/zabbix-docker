"""Link templates to hosts, keeping the templates already linked.

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  zbx_link_template.py (--host NAME ... | --group GROUP | --tag TAG=VALUE) --template NAME ... [--dry-run]

Uses host.massadd: existing templates, macros and dependencies are not touched.
Hosts that already have a template are skipped for it.
"""
import argparse

from zbx_api import ZabbixError, api_from_stdin, find_hosts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", nargs="*", default=[])
    parser.add_argument("--group")
    parser.add_argument("--tag")
    parser.add_argument("--template", nargs="+", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.host or args.group or args.tag):
        parser.error("select hosts with --host, --group or --tag")

    api = api_from_stdin()
    templates = api.call("template.get", {"filter": {"host": args.template}, "output": ["templateid", "host"]})
    missing = set(args.template) - {t["host"] for t in templates}
    if missing:
        raise ZabbixError(f"templates not found: {', '.join(sorted(missing))}")

    hosts = find_hosts(api, args.host, args.group, args.tag, selectParentTemplates=["templateid"])
    for t in templates:
        pending = [h for h in hosts if t["templateid"] not in {p["templateid"] for p in h["parentTemplates"]}]
        for h in hosts:
            state = "se enlazaría" if h in pending and args.dry_run else "enlazada" if h in pending else "ya enlazada"
            print(f"{h['name']}: {t['host']} {state}")
        if pending and not args.dry_run:
            api.call("host.massadd", {"hosts": [{"hostid": h["hostid"]} for h in pending],
                                      "templates": [{"templateid": t["templateid"]}]})


if __name__ == "__main__":
    main()
