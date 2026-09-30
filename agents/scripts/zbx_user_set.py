"""Set the role of a user and add it to user groups (existing groups are kept).

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  zbx_user_set.py --user USERNAME [--role ROLE] [--group GROUP ...] [--autologout 15m] [--dry-run]

The user must exist; it is created in the web interface, where the person sets the password
(Users -> Users -> Create user). This script never sets passwords.
"""
import argparse

from zbx_api import ZabbixError, api_from_stdin


def lookup(api, method, key, field, value):
    found = api.call(method, {"output": [key], "filter": {field: [value]}})
    if not found:
        raise ZabbixError(f"{method.split('.')[0]} not found: {value}")
    return found[0][key]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--user", required=True)
    parser.add_argument("--role")
    parser.add_argument("--group", nargs="*", default=[])
    parser.add_argument("--autologout")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api = api_from_stdin()
    users = api.call("user.get", {"output": ["userid"], "filter": {"username": [args.user]}, "selectUsrgrps": ["usrgrpid", "name"]})
    if not users:
        raise ZabbixError(f"user not found: {args.user}")
    user = users[0]
    params = {"userid": user["userid"]}
    if args.role:
        params["roleid"] = lookup(api, "role.get", "roleid", "name", args.role)
    current = {g["usrgrpid"] for g in user["usrgrps"]}
    new = {lookup(api, "usergroup.get", "usrgrpid", "name", g) for g in args.group}
    if new - current:
        params["usrgrps"] = [{"usrgrpid": g} for g in sorted(current | new)]
    if args.autologout:
        params["autologout"] = args.autologout

    groups = sorted({g["name"] for g in user["usrgrps"]} | set(args.group))
    print(f"{args.user}: rol {args.role or '(sin cambio)'}; grupos {', '.join(groups) or '—'}; "
          f"autologout {args.autologout or '(sin cambio)'}")
    if len(params) > 1 and not args.dry_run:
        api.call("user.update", params)
        print("aplicado")


if __name__ == "__main__":
    main()
