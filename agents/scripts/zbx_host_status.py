"""Health check of hosts after a change (read-only): interface availability, items without data,
unsupported items and active problems.

Usage (token on stdin, see README.md):
  zbx_host_status.py [--group GROUP] [--tag TAG=VALUE] [--host NAME ...] [--ignore TEXT ...] [--details]

Unsupported items whose name starts with an --ignore text are counted apart (known limitations,
e.g. 'Firmware version' on airOS 8). --details lists every unexpected unsupported item.
"""
import argparse

from zbx_api import AVAILABLE, SEVERITIES, api_from_stdin, find_hosts

KNOWN_LIMITATIONS = ("Firmware version", "Hardware model name")


def status(api, host, ignore):
    items = api.call("item.get", {"hostids": host["hostid"], "output": ["name", "state", "error", "lastclock", "status"],
                                  "filter": {"status": 0}})
    unsupported = [i for i in items if i["state"] == "1"]
    unexpected = [i for i in unsupported if not i["name"].startswith(ignore)]
    problems = api.call("problem.get", {"hostids": host["hostid"], "output": ["name", "severity"]})
    return {
        "interfaces": ", ".join(f"{i['ip']} {AVAILABLE[i['available']]}{' (' + i['error'] + ')' if i['error'] else ''}"
                                for i in host["interfaces"]),
        "items": len(items),
        "no_data": sum(1 for i in items if i["lastclock"] == "0" and i["state"] == "0"),
        "unsupported": len(unsupported),
        "unexpected": unexpected,
        "problems": [f"{SEVERITIES[int(p['severity'])]}: {p['name']}" for p in problems],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--group")
    parser.add_argument("--tag")
    parser.add_argument("--host", nargs="*", default=[])
    parser.add_argument("--ignore", nargs="*", default=list(KNOWN_LIMITATIONS))
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()

    api = api_from_stdin()
    hosts = find_hosts(api, args.host, args.group, args.tag, selectInterfaces=["ip", "available", "error"])
    ignore = tuple(args.ignore)
    total_unexpected = 0
    for host in hosts:
        s = status(api, host, ignore)
        total_unexpected += len(s["unexpected"])
        print(f"{host['name']:24} {s['interfaces']:32} items={s['items']:<5} sin_datos={s['no_data']:<4} "
              f"no_soportados={s['unsupported']} (inesperados={len(s['unexpected'])}) problemas={len(s['problems'])}")
        if args.details:
            for item in s["unexpected"]:
                print(f"    ! {item['name']}: {item['error'][:120]}")
        for problem in s["problems"]:
            print(f"    - {problem}")
    print(f"\n{len(hosts)} hosts, {total_unexpected} items no soportados inesperados")


if __name__ == "__main__":
    main()
