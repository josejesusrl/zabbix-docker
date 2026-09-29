"""Add a dependency on any trigger of another host, keeping existing dependencies.

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  zbx_add_dependency.py --host NAME ... --trigger TEXT --parent-host NAME --parent-trigger TEXT [--dry-run]

--trigger / --parent-trigger: text contained in the trigger name (case insensitive, macros expanded).
The parent text must match exactly one trigger of the parent host.
Example: roots of the topology depend on the Zabbix server own network link, so an outage of the
monitoring server does not report every device as unavailable.
For topological ICMP dependencies between devices use zbx_set_uplink.py.
"""
import argparse

from zbx_api import ZabbixError, add_dependency, api_from_stdin, find_hosts, find_triggers, get_host


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", nargs="+", required=True)
    parser.add_argument("--trigger", required=True)
    parser.add_argument("--parent-host", required=True)
    parser.add_argument("--parent-trigger", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api = api_from_stdin()
    parent_host = get_host(api, args.parent_host)
    parents = find_triggers(api, parent_host["hostid"], args.parent_trigger)
    if len(parents) != 1:
        raise ZabbixError(f"'{args.parent_trigger}' matches {len(parents)} triggers of {parent_host['name']}: {[p['description'] for p in parents]}")
    parent = parents[0]
    for host in find_hosts(api, args.host):
        for trigger in find_triggers(api, host["hostid"], args.trigger):
            added = add_dependency(api, trigger, parent["triggerid"], args.dry_run)
            state = ("se añadiría" if args.dry_run else "añadida") if added else "ya existía"
            print(f"{host['name']}: '{trigger['description']}' -> '{parent_host['name']}: {parent['description']}' ({state})")


if __name__ == "__main__":
    main()
