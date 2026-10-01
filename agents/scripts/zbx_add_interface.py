"""Add a main interface to a host that has none of that type (read the IP from the device, never scan).

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  zbx_add_interface.py --host NAME --ip IP [--type ping|snmp] [--snmp-version 1|2] [--dry-run]

--type ping adds an agent-type interface used only by the "ICMP Ping" template (devices monitored by
HTTP or other item types, e.g. Hikvision cameras). --type snmp uses the community {$SNMP_COMMUNITY}.
"""
import argparse

from zbx_api import ZabbixError, api_from_stdin, get_host

TYPES = {"ping": 1, "snmp": 2}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", required=True)
    parser.add_argument("--ip", required=True)
    parser.add_argument("--type", choices=TYPES, default="ping")
    parser.add_argument("--snmp-version", choices=["1", "2"], default="2")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api = api_from_stdin()
    host = get_host(api, args.host, selectInterfaces=["type", "ip"])
    if any(int(i["type"]) == TYPES[args.type] for i in host["interfaces"]):
        raise ZabbixError(f"{host['name']} already has an interface of type {args.type}")
    interface = {"hostid": host["hostid"], "type": TYPES[args.type], "main": 1, "useip": 1, "ip": args.ip, "dns": "",
                 "port": "10050" if args.type == "ping" else "161"}
    if args.type == "snmp":
        interface["details"] = {"version": int(args.snmp_version), "community": "{$SNMP_COMMUNITY}", "bulk": 1}
    print(f"{host['name']}: interfaz {args.type} {args.ip}{' (dry-run)' if args.dry_run else ''}")
    if not args.dry_run:
        api.call("hostinterface.create", interface)


if __name__ == "__main__":
    main()
