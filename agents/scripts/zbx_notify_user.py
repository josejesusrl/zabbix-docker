"""Create or update a notification-only user (e.g. an internet provider): it receives messages but cannot
log in to the web interface or the API.

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  zbx_notify_user.py --user USERNAME --name "Full name" --group GROUP --read HOSTGROUP ... \\
                     --media MEDIATYPE --sendto ADDRESS ... [--role ROLE] [--dry-run]

- GROUP is created if missing with "Frontend access: Disabled"; it gets read permission on the --read host
  groups (Zabbix only sends notifications about hosts the user can read). Existing rights of the group are replaced.
- The user gets ROLE (default "Solo lectura": no actions, no API) and a random password that is never shown.
- --sendto replaces the addresses of that media type for the user (several addresses = several recipients).
Which problems are sent is decided by an action (zbx_action_apply.py), not here.
"""
import argparse
import secrets

from zbx_api import ZabbixError, api_from_stdin

READ = 2
FRONTEND_DISABLED = 3


def ids(api, method, key, field, names):
    found = api.call(method, {"output": [key, field], "filter": {field: names}})
    missing = set(names) - {f[field] for f in found}
    if missing:
        raise ZabbixError(f"{method}: not found {', '.join(sorted(missing))}")
    return [f[key] for f in found]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--user", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--group", required=True)
    parser.add_argument("--read", nargs="+", required=True)
    parser.add_argument("--media", required=True)
    parser.add_argument("--sendto", nargs="+", required=True)
    parser.add_argument("--role", default="Solo lectura")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api = api_from_stdin()
    hostgroups = ids(api, "hostgroup.get", "groupid", "name", args.read)
    roleid = ids(api, "role.get", "roleid", "name", [args.role])[0]
    mediatypeid = ids(api, "mediatype.get", "mediatypeid", "name", [args.media])[0]
    group = api.call("usergroup.get", {"output": ["usrgrpid"], "filter": {"name": [args.group]}})
    rights = [{"id": g, "permission": READ} for g in hostgroups]
    print(f"grupo {args.group}: {'actualizar' if group else 'crear'} (sin acceso web, lectura: {', '.join(args.read)})")
    user = api.call("user.get", {"output": ["userid"], "filter": {"username": [args.user]}, "selectMedias": "extend"})
    print(f"usuario {args.user} ({args.name}): {'actualizar' if user else 'crear'}, rol {args.role}, "
          f"{args.media} -> {len(args.sendto)} destinatario(s)")
    if args.dry_run:
        return
    if group:
        usrgrpid = group[0]["usrgrpid"]
        api.call("usergroup.update", {"usrgrpid": usrgrpid, "gui_access": FRONTEND_DISABLED, "hostgroup_rights": rights})
    else:
        usrgrpid = api.call("usergroup.create", {"name": args.group, "gui_access": FRONTEND_DISABLED,
                                                 "hostgroup_rights": rights})["usrgrpids"][0]
    media = {"mediatypeid": mediatypeid, "sendto": args.sendto, "active": 0, "severity": 63, "period": "1-7,00:00-24:00"}
    if user:
        others = [{k: m[k] for k in ("mediatypeid", "sendto", "active", "severity", "period")}
                  for m in user[0]["medias"] if m["mediatypeid"] != mediatypeid]
        api.call("user.update", {"userid": user[0]["userid"], "name": args.name, "roleid": roleid,
                                 "usrgrps": [{"usrgrpid": usrgrpid}], "medias": others + [media]})
    else:
        api.call("user.create", {"username": args.user, "name": args.name, "roleid": roleid,
                                 "passwd": secrets.token_urlsafe(24) + "aA1!", "usrgrps": [{"usrgrpid": usrgrpid}],
                                 "medias": [media]})
    print("aplicado")


if __name__ == "__main__":
    main()
