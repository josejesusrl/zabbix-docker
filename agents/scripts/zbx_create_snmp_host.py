"""Create an SNMP host with templates, macros, tags and its upstream dependency.

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  zbx_create_snmp_host.py --name NAME --ip IP --group GROUP --template TPL [TPL ...]
                          [--visible-name TEXT] [--snmp-version 1|2] [--macro '{$M}=VALUE' ...] [--tag TAG=VALUE ...]
                          [--uplink PARENT] [--self-dependency TEXT ...] [--dry-run]

--name is the technical name (letters, digits, spaces, '.', '-', '_'); use --visible-name when the
device name has other characters (e.g. '[AP]-Link'). The SNMP community is always {$SNMP_COMMUNITY}. Ubiquiti airOS answers SNMPv1 only (--snmp-version 1).
Examples in README.md and docs/operacion/procedimientos/.
"""
import argparse

from zbx_api import ZabbixError, add_self_dependency, api_from_stdin, get_host, set_host_tag, set_upstream


def key_value(text):
    key, sep, value = text.partition("=")
    if not sep:
        raise argparse.ArgumentTypeError(f"expected KEY=VALUE: {text}")
    return key, value


def lookup_ids(api, method, field, names, id_field):
    found = api.call(method, {"filter": {field: names}, "output": [field, id_field]})
    missing = set(names) - {f[field] for f in found}
    if missing:
        raise ZabbixError(f"{method}: not found {', '.join(sorted(missing))}")
    return [{id_field: f[id_field]} for f in found]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", required=True, help="Host name (sysName / device name)")
    parser.add_argument("--visible-name", help="Visible name, defaults to --name")
    parser.add_argument("--ip", required=True)
    parser.add_argument("--group", required=True)
    parser.add_argument("--template", nargs="+", required=True)
    parser.add_argument("--snmp-version", choices=["1", "2"], default="2")
    parser.add_argument("--macro", nargs="*", type=key_value, default=[])
    parser.add_argument("--tag", nargs="*", type=key_value, default=[])
    parser.add_argument("--uplink", help="Parent host for dependencies and 'uplink' tag")
    parser.add_argument("--self-dependency", nargs="*", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api = api_from_stdin()
    if api.call("host.get", {"filter": {"host": [args.name]}, "output": ["hostid"]}):
        raise SystemExit(f"host already exists: {args.name}")
    groups = lookup_ids(api, "hostgroup.get", "name", [args.group], "groupid")
    templates = lookup_ids(api, "template.get", "host", args.template, "templateid")
    parent = get_host(api, args.uplink) if args.uplink else None
    if args.dry_run:
        print(f"Se crearía {args.name} [{args.visible_name or args.name}] ({args.ip}, SNMPv{args.snmp_version}) en {args.group} con {args.template}, "
              f"macros {dict(args.macro)}, tags {dict(args.tag)}, uplink {args.uplink or '—'}")
        return

    hostid = api.call("host.create", {
        "host": args.name, "name": args.visible_name or args.name, "groups": groups, "templates": templates,
        "interfaces": [{"type": 2, "main": 1, "useip": 1, "ip": args.ip, "dns": "", "port": "161",
                        "details": {"version": int(args.snmp_version), "community": "{$SNMP_COMMUNITY}", "bulk": 1}}],
        "macros": [{"macro": m, "value": v} for m, v in args.macro],
        "tags": [{"tag": t, "value": v} for t, v in args.tag],
    })["hostids"][0]
    print(f"Creado {args.name} (hostid {hostid})")
    if parent:
        print("  dependencias:", set_upstream(api, hostid, parent["hostid"]))
        set_host_tag(api, hostid, "uplink", parent["name"])
    for pattern in args.self_dependency:
        print(f"  dependencia propia '{pattern}':", add_self_dependency(api, hostid, pattern))


if __name__ == "__main__":
    main()
