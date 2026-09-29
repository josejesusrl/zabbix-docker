"""Execute now the items and discovery rules of hosts, instead of waiting for their interval.

Usage (token on stdin, see README.md):
  zbx_check_now.py (--host NAME ... | --group GROUP | --tag TAG=VALUE) [--key-prefix PREFIX]

Useful right after creating a host or changing macros. Dependent items are updated when their
master item runs. Discovery rules with 'discard unchanged' preprocessing may still wait up to 1 h.
"""
import argparse

from zbx_api import api_from_stdin, check_now, find_hosts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", nargs="*", default=[])
    parser.add_argument("--group")
    parser.add_argument("--tag")
    parser.add_argument("--key-prefix", default="")
    args = parser.parse_args()
    if not (args.host or args.group or args.tag):
        parser.error("select hosts with --host, --group or --tag")

    api = api_from_stdin()
    hosts = find_hosts(api, args.host, args.group, args.tag)
    count = check_now(api, [h["hostid"] for h in hosts], args.key_prefix)
    print(f"{count} items/reglas lanzados en {len(hosts)} hosts")


if __name__ == "__main__":
    main()
