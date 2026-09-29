"""Enable or disable items or triggers of hosts by name (e.g. items unsupported by design, noisy discovered triggers).

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  zbx_set_status.py (--host NAME ... | --group GROUP | --tag TAG=VALUE) (--item TEXT ... | --trigger TEXT ...)
                    (--disable | --enable) [--dry-run]

TEXT is contained in the item or trigger name (case insensitive). Works on inherited and discovered
objects: the status set on a discovered item/trigger is kept when the discovery runs again.
Always document in docs/operacion/registro.md why an object was disabled.
"""
import argparse

from zbx_api import api_from_stdin, find_hosts, find_triggers


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", nargs="*", default=[])
    parser.add_argument("--group")
    parser.add_argument("--tag")
    parser.add_argument("--item", nargs="*", default=[])
    parser.add_argument("--trigger", nargs="*", default=[])
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--disable", action="store_true")
    action.add_argument("--enable", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.host or args.group or args.tag) or not (args.item or args.trigger):
        parser.error("select hosts (--host/--group/--tag) and objects (--item/--trigger)")

    api = api_from_stdin()
    status = "1" if args.disable else "0"
    verb = ("desactivaría" if args.disable else "activaría") if args.dry_run else ("desactivado" if args.disable else "activado")
    for host in find_hosts(api, args.host, args.group, args.tag):
        items = api.call("item.get", {"hostids": host["hostid"], "output": ["itemid", "name", "status"]})
        for text in args.item:
            for item in [i for i in items if text.lower() in i["name"].lower() and i["status"] != status]:
                if not args.dry_run:
                    api.call("item.update", {"itemid": item["itemid"], "status": status})
                print(f"{host['name']}: item '{item['name']}' {verb}")
        for text in args.trigger:
            for trigger in [t for t in find_triggers(api, host["hostid"], text) if t["status"] != status]:
                if not args.dry_run:
                    api.call("trigger.update", {"triggerid": trigger["triggerid"], "status": status})
                print(f"{host['name']}: trigger '{trigger['description']}' {verb}")


if __name__ == "__main__":
    main()
