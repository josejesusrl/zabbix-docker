"""Set host macros (text values) on selected hosts, creating or updating them.

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  zbx_set_macro.py (--host NAME ... | --group GROUP | --tag TAG=VALUE) --macro '{$M}=VALUE' ... [--dry-run]

Only for non-secret values: passwords and other secrets are entered by a person in the web interface
as "Secret text" (AGENTS.md, rule 4), so this script refuses macros named like a secret.
"""
import argparse
import re

from zbx_api import api_from_stdin, find_hosts, set_host_macro

SECRET_NAME = re.compile(r"PASS|SECRET|TOKEN|KEY|COMMUNITY|PSK", re.I)


def macro_value(text):
    macro, sep, value = text.partition("=")
    if not sep or not re.fullmatch(r"\{\$[A-Z0-9_.]+(:.+)?\}", macro):
        raise argparse.ArgumentTypeError(f"expected '{{$MACRO}}=VALUE': {text}")
    if SECRET_NAME.search(macro):
        raise argparse.ArgumentTypeError(f"{macro} looks like a secret: set it in the web interface as Secret text")
    return macro, value


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", nargs="*", default=[])
    parser.add_argument("--group")
    parser.add_argument("--tag")
    parser.add_argument("--macro", nargs="+", type=macro_value, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.host or args.group or args.tag):
        parser.error("select hosts with --host, --group or --tag")

    api = api_from_stdin()
    for host in find_hosts(api, args.host, args.group, args.tag, selectMacros=["macro", "value"]):
        current = {m["macro"]: m.get("value") for m in host["macros"]}
        for macro, value in args.macro:
            if current.get(macro) == value:
                print(f"{host['name']}: {macro} ya es {value}")
                continue
            print(f"{host['name']}: {macro} {current.get(macro, '(no existe)')} -> {value}{' (dry-run)' if args.dry_run else ''}")
            if not args.dry_run:
                set_host_macro(api, host["hostid"], macro, value)


if __name__ == "__main__":
    main()
