"""Probe devices by SNMP before adding them to Zabbix (read-only): ping, SNMPv1/v2c answer, sysName,
airOS 6 model and firmware, wireless clients and GPS satellites (Ubiquiti).

Usage (token on stdin, see README.md; runs on the Zabbix server, needs Docker there):
  snmp_probe.py IP [IP ...] [--community-macro '{$SNMP_COMMUNITY}']

The community is read from the Zabbix global macro and passed to a temporary net-snmp container
through the environment: it is never printed. Only probe the IPs given by the owner (AGENTS.md, rule 5).
A secret-type macro cannot be read through the API; then the probe is not possible.
"""
import argparse

from zbx_api import api_from_stdin
from snmp_tools import community_from_zabbix, run_netsnmp

OIDS = {
    "sysname": "1.3.6.1.2.1.1.5.0",
    "model": "1.2.840.10036.3.1.2.1.3.5",        # IEEE 802.11 MIB, present on airOS 6 only
    "firmware": "1.2.840.10036.3.1.2.1.4.5",
    "clients": "1.3.6.1.4.1.41112.1.4.5.1.15.1",  # UBNT-AirMAX-MIB station count
    "gps_sats": "1.3.6.1.4.1.41112.1.4.9.8.0",
}
# One value per column printed by PROBE; sysName is the v1 or v2c answer
FIELDS = ["ip", "ping_loss", "v1", "v2c", "model", "firmware", "clients", "gps_sats"]

PROBE = r'''
get() { snmpget -v "$1" -c "$COMM" -t 2 -r 0 -Ovq "$2" "$3" 2>/dev/null | head -1 | tr -d '"|'; }
for ip in $IPS; do
  loss=$(fping -q -c2 -t500 "$ip" 2>&1 | sed -nE 's/.*loss = [0-9]+\/[0-9]+\/([0-9]+)%.*/\1/p')
  v1=$(get 1 "$ip" $OID_SYSNAME); v2=$(get 2c "$ip" $OID_SYSNAME)
  echo "$ip|$loss|$v1|$v2|$(get 1 "$ip" $OID_MODEL)|$(get 1 "$ip" $OID_FIRMWARE)|$(get 1 "$ip" $OID_CLIENTS)|$(get 1 "$ip" $OID_GPS_SATS)"
done
'''


def valid(value):
    return bool(value) and "No Such" not in value and "Timeout" not in value


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ips", nargs="+")
    parser.add_argument("--community-macro", default="{$SNMP_COMMUNITY}")
    args = parser.parse_args()

    community = community_from_zabbix(api_from_stdin(), args.community_macro)
    env = {"IPS": " ".join(args.ips), **{f"OID_{k.upper()}": v for k, v in OIDS.items()}}
    code, out, err = run_netsnmp(PROBE, community, env)
    print(f"{'IP':15} {'ping%':5} {'v1':3} {'v2c':3} {'sysName':26} {'modelo (airOS6)':18} {'firmware':20} {'cli':4} gps")
    for line in out.strip().splitlines():
        row = dict(zip(FIELDS, (line.split("|") + [""] * len(FIELDS))[:len(FIELDS)]))
        yes = lambda k: "sí" if valid(row[k]) else "-"
        val = lambda k: row[k] if valid(row[k]) else ""
        print(f"{row['ip']:15} {row['ping_loss'] or '100':5} {yes('v1'):3} {yes('v2c'):3} {(val('v1') or val('v2c'))[:26]:26} "
              f"{val('model')[:18]:18} {val('firmware')[:20]:20} {val('clients'):4} {val('gps_sats')}")
    if code:
        print("docker:", err.strip()[:300])


if __name__ == "__main__":
    main()
