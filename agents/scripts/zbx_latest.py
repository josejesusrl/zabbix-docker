"""Latest values of the items of hosts, like Monitoring -> Latest data (read-only).

Usage (token on stdin, see README.md):
  zbx_latest.py (--host NAME ... | --group GROUP | --tag TAG=VALUE) [--key PREFIX ...] [--name TEXT]

- --key PREFIX: only items whose key starts with one of the prefixes (e.g. mimosa. net.if.status).
- --name TEXT: only items whose name contains TEXT (case insensitive).
Unsupported items show their error; items not collected yet show '(no data)'.
"""
import argparse

from zbx_api import api_from_stdin, find_hosts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", nargs="*", default=[])
    parser.add_argument("--group")
    parser.add_argument("--tag")
    parser.add_argument("--key", nargs="*", default=[])
    parser.add_argument("--name", default="")
    args = parser.parse_args()
    if not (args.host or args.group or args.tag):
        parser.error("select hosts with --host, --group or --tag")

    api = api_from_stdin()
    for host in find_hosts(api, args.host, args.group, args.tag):
        items = api.call("item.get", {"hostids": host["hostid"], "output": ["name", "key_", "lastvalue", "units", "state", "error", "lastclock"],
                                      "selectValueMap": ["mappings"], "filter": {"status": 0}, "sortfield": "name"})
        items = [i for i in items if (not args.key or i["key_"].startswith(tuple(args.key))) and args.name.lower() in i["name"].lower()]
        print(f"== {host['name']} ({len(items)} items)")
        for i in items:
            if i["state"] == "1":
                value = "UNSUPPORTED: " + i["error"][:80]
            elif i["lastclock"] == "0":
                value = "(no data)"
            else:
                mapped = {m["value"]: m["newvalue"] for m in (i.get("valuemap") or {}).get("mappings", [])}
                value = f"{i['lastvalue'][:60]} {i['units']}".strip()
                if i["lastvalue"] in mapped:
                    value += f" ({mapped[i['lastvalue']]})"
            print(f"   {i['name'][:55]:55} {value}")


if __name__ == "__main__":
    main()
