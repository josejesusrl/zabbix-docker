"""Users, user roles and user groups with their permissions (read only).

Usage (token on stdin, see README.md):
  zbx_users.py [--dashboards]

Shows each user role (type, denied UI sections, actions, API access), each user group
(frontend access, status, permissions per host group) and each user (role, groups, autologout).
--dashboards adds the sharing of every dashboard (owner, users and groups).
"""
import argparse

from zbx_api import api_from_stdin

ROLE_TYPES = {"1": "User", "2": "Admin", "3": "Super admin"}
PERMISSIONS = {"0": "deny", "2": "read", "3": "read-write"}
GUI_ACCESS = {"0": "default", "1": "internal", "2": "LDAP", "3": "disabled"}
SHARE = {"2": "read", "3": "read-write"}


def names(api, method, key, field, ids):
    if not ids:
        return {}
    return {o[key]: o[field] for o in api.call(method, {"output": [key, field], key + "s": list(ids)})}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dashboards", action="store_true")
    args = parser.parse_args()
    api = api_from_stdin()

    print("== Roles")
    for r in api.call("role.get", {"output": ["roleid", "name", "type", "readonly"], "selectRules": "extend"}):
        rules = r["rules"]
        denied = [u["name"] for u in rules.get("ui", []) if u["status"] == "0"]
        actions = [a["name"] for a in rules.get("actions", []) if a["status"] == "1"]
        print(f"{r['name']} ({ROLE_TYPES[r['type']]})")
        print(f"   ui default   {'allow' if rules.get('ui.default_access') == '1' else 'deny'}; denegadas: {', '.join(denied) or '—'}")
        print(f"   acciones     default {'allow' if rules.get('actions.default_access') == '1' else 'deny'}; permitidas: {', '.join(actions) or '—'}")
        print(f"   api          {'activada' if rules.get('api.access') == '1' else 'desactivada'}")

    groups = api.call("usergroup.get", {"output": ["usrgrpid", "name", "gui_access", "users_status"],
                                        "selectHostGroupRights": "extend", "selectTemplateGroupRights": "extend"})
    hostgroups = names(api, "hostgroup.get", "groupid", "name", {p["id"] for g in groups for p in g["hostgroup_rights"]})
    print("\n== Grupos de usuarios")
    for g in groups:
        rights = ", ".join(f"{hostgroups.get(p['id'], p['id'])}={PERMISSIONS[p['permission']]}" for p in g["hostgroup_rights"])
        status = "activo" if g["users_status"] == "0" else "desactivado"
        print(f"{g['name']} ({status}, frontend {GUI_ACCESS[g['gui_access']]})")
        print(f"   host groups  {rights or '—'}")

    roles = names(api, "role.get", "roleid", "name", {u["roleid"] for u in api.call("user.get", {"output": ["roleid"]})})
    print("\n== Usuarios")
    for u in api.call("user.get", {"output": ["username", "name", "surname", "roleid", "autologout"],
                                   "selectUsrgrps": ["name"], "selectMedias": ["mediatypeid"]}):
        full = " ".join(filter(None, [u["name"], u["surname"]]))
        print(f"{u['username']}{' (' + full + ')' if full else ''}: rol {roles.get(u['roleid'], '—')}; "
              f"grupos {', '.join(g['name'] for g in u['usrgrps']) or '—'}; autologout {u['autologout']}; medios {len(u['medias'])}")

    if args.dashboards:
        print("\n== Dashboards")
        dashboards = api.call("dashboard.get", {"output": ["name", "userid", "private"],
                                                "selectUsers": "extend", "selectUserGroups": "extend"})
        users = names(api, "user.get", "userid", "username",
                      {d["userid"] for d in dashboards} | {u["userid"] for d in dashboards for u in d["users"]})
        ugroups = {g["usrgrpid"]: g["name"] for g in groups}
        for d in dashboards:
            shared = [f"{users.get(u['userid'])}={SHARE[u['permission']]}" for u in d["users"]]
            shared += [f"{ugroups.get(g['usrgrpid'])}={SHARE[g['permission']]}" for g in d["userGroups"]]
            print(f"{d['name']}: propietario {users.get(d['userid'])}; {'privado' if d['private'] == '1' else 'público'}; "
                  f"compartido {', '.join(shared) or '—'}")


if __name__ == "__main__":
    main()
