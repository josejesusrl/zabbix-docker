"""Set the technical Host name equal to the visible name (inventory convention).

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  zbx_align_host_name.py (--host NAME ... | --group GROUP | --tag TAG=VALUE | --all) [--dry-run]

Characters not allowed in a Host name (only letters, digits, space, '.', '_' and '-') are removed
from the visible name, e.g. 'Switch Main Site #01' -> 'Switch Main Site 01'. The visible name is not changed.
History, dependencies, triggers and SNMP traps (matched by IP) are kept. Calculated items and
dashboards that reference hosts by technical name must use the new name.
"""
import argparse
import re

from zbx_api import api_from_stdin, find_hosts


def technical_name(visible):
    return re.sub(r" {2,}", " ", re.sub(r"[^A-Za-z0-9 ._-]", "", visible)).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", nargs="*", default=[])
    parser.add_argument("--group")
    parser.add_argument("--tag")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.host or args.group or args.tag or args.all):
        parser.error("select hosts with --host, --group, --tag or --all")

    api = api_from_stdin()
    hosts = find_hosts(api, args.host, args.group, args.tag)
    taken = {h["host"] for h in api.call("host.get", {"output": ["host"]})}
    for h in hosts:
        new = technical_name(h["name"])
        if new == h["host"]:
            continue
        if new in taken:
            print(f"{h['name']}: '{new}' ya lo usa otro host, se omite")
            continue
        print(f"{h['name']}: '{h['host']}' -> '{new}'{' (dry-run)' if args.dry_run else ''}")
        if not args.dry_run:
            # Without "name", Zabbix also sets the visible name to the new technical name
            api.call("host.update", {"hostid": h["hostid"], "host": new, "name": h["name"]})
            taken.add(new)


if __name__ == "__main__":
    main()
