"""List hosts with interfaces, groups, templates, host macros, tags and upstream dependencies (read-only).

Usage (token on stdin, see README.md):
  zbx_inventory.py [--group GROUP] [--tag TAG=VALUE] [--host NAME ...] [--markdown]

--markdown prints a table ready for the inventory of OPERACION.md.
Secret macro values are never printed.
"""
import argparse

from zbx_api import api_from_stdin, find_hosts, upstream_hosts

INTERFACE_TYPES = {"1": "agent", "2": "snmp", "3": "ipmi", "4": "jmx"}


def describe(api, host):
    interfaces = []
    for i in host["interfaces"]:
        kind = INTERFACE_TYPES.get(i["type"], i["type"])
        version = (i.get("details") or {}).get("version")
        interfaces.append(f"{kind}{'v' + version if version else ''} {i['ip']}")
    macros = [m["macro"] + ("=" + m["value"] if m["type"] == "0" else "=<secret>") for m in host["macros"]]
    return {
        "name": host["name"],
        "interfaces": ", ".join(interfaces),
        "groups": ", ".join(g["name"] for g in host["hostgroups"]),
        "templates": ", ".join(t["host"] for t in host["parentTemplates"]),
        "macros": ", ".join(macros) or "—",
        "tags": ", ".join(f"{t['tag']}={t['value']}" for t in host["tags"]) or "—",
        "upstream": ", ".join(upstream_hosts(api, host["hostid"])) or "—",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--group")
    parser.add_argument("--tag")
    parser.add_argument("--host", nargs="*", default=[])
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    api = api_from_stdin()
    hosts = find_hosts(api, args.host, args.group, args.tag, selectInterfaces=["type", "ip", "details"],
                       selectHostGroups=["name"], selectParentTemplates=["host"],
                       selectMacros=["macro", "value", "type"], selectTags=["tag", "value"])
    rows = [describe(api, h) for h in hosts]
    columns = ["name", "interfaces", "groups", "templates", "macros", "tags", "upstream"]
    if args.markdown:
        print("| " + " | ".join(columns) + " |")
        print("|" + "---|" * len(columns))
        for row in rows:
            print("| " + " | ".join(row[c].replace("|", "\\|") for c in columns) + " |")
    else:
        for row in rows:
            print(f"== {row['name']}")
            for c in columns[1:]:
                print(f"   {c:10} {row[c]}")
    print(f"\n{len(rows)} hosts")


if __name__ == "__main__":
    main()
