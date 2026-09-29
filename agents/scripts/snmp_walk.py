"""SNMP walk of a device to discover which OIDs it publishes before writing a template (read-only).

Usage (token on stdin, see README.md; runs on the Zabbix server, needs Docker there):
  snmp_walk.py IP OID [OID ...] [--version 1|2c] [--max-lines N] [--hide REGEX ...]

- OIDs are walked with numeric output (-On) and values as the device returns them.
- --hide REGEX: replaces values of matching OIDs with <hidden> (e.g. client names or MACs).
- The community comes from {$SNMP_COMMUNITY} and is never printed.
Only walk devices given by the owner (AGENTS.md, rule 5).
"""
import argparse
import re

from zbx_api import api_from_stdin
from snmp_tools import community_from_zabbix, run_netsnmp


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ip")
    parser.add_argument("oids", nargs="+")
    parser.add_argument("--version", choices=["1", "2c"], default="2c")
    parser.add_argument("--max-lines", type=int, default=400)
    parser.add_argument("--hide", nargs="*", default=[])
    args = parser.parse_args()

    community = community_from_zabbix(api_from_stdin())
    script = 'for oid in $OIDS; do snmpwalk -v "$VER" -c "$COMM" -t 3 -r 1 -On "$IP" "$oid"; done'
    code, out, err = run_netsnmp(script, community, {"IP": args.ip, "OIDS": " ".join(args.oids), "VER": args.version})
    hidden = [re.compile(h) for h in args.hide]
    lines = out.splitlines()
    for line in lines[:args.max_lines]:
        oid, sep, value = line.partition(" = ")
        print(f"{oid} = <hidden>" if sep and any(h.search(oid) for h in hidden) else line)
    if len(lines) > args.max_lines:
        print(f"... {len(lines) - args.max_lines} more lines (--max-lines)")
    if code or err.strip():
        print("stderr:", err.strip()[:300])


if __name__ == "__main__":
    main()
