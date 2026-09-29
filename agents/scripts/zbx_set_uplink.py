"""Set the upstream (parent) device of hosts: dependencies of their availability triggers and the 'uplink' tag.

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  zbx_set_uplink.py --parent HOST (--host NAME ... | --group GROUP | --tag TAG=VALUE)
                    [--self-dependency TEXT ...] [--dry-run]

- Availability triggers (ICMP down/loss/response time, No SNMP data) will depend on the parent's
  'Unavailable by ICMP ping'. Template internal dependencies (on the host's own triggers) are kept;
  previous dependencies on other hosts are replaced. Safe to run again.
- --self-dependency TEXT: triggers containing TEXT also depend on the host's own ICMP down
  (APs: 'no connected clients').
"""
import argparse

from zbx_api import add_self_dependency, api_from_stdin, find_hosts, get_host, set_host_tag, set_upstream


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--parent", required=True)
    parser.add_argument("--host", nargs="*", default=[])
    parser.add_argument("--group")
    parser.add_argument("--tag")
    parser.add_argument("--self-dependency", nargs="*", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.host or args.group or args.tag):
        parser.error("select hosts with --host, --group or --tag")

    api = api_from_stdin()
    parent = get_host(api, args.parent)
    for host in find_hosts(api, args.host, args.group, args.tag, selectTags=["tag", "value"]):
        if host["hostid"] == parent["hostid"]:
            continue
        changed = set_upstream(api, host["hostid"], parent["hostid"], args.dry_run)
        for pattern in args.self_dependency:
            changed += add_self_dependency(api, host["hostid"], pattern, args.dry_run)
        tag_ok = any(t["tag"] == "uplink" and t["value"] == parent["name"] for t in host["tags"])
        if not tag_ok and not args.dry_run:
            set_host_tag(api, host["hostid"], "uplink", parent["name"])
        action = "cambiaría" if args.dry_run else "cambiado"
        print(f"{host['name']:24} -> {parent['name']}: {action} {changed or 'nada'}{'' if tag_ok else ', etiqueta uplink'}")


if __name__ == "__main__":
    main()
