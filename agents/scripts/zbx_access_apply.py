"""Create or update an access profile: user role, user group with host group permissions
and dashboards shared with that group, from zabbix_access/*.json.

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  run_remote.sh -f zabbix_access/X.json zbx_access_apply.py X.json [--dry-run]

JSON keys:
  role        name; ui_deny (UI sections denied, e.g. "services.sla_report"); actions (allowed
              actions, e.g. "acknowledge_problems", everything else denied); api (true/false).
              The role type is always "User": it cannot open configuration sections.
  user_group  name; read (host groups with read permission). Host groups not listed get no
              permission, so hosts of a new host group stay hidden until it is added here.
  dashboards  dashboards shared read-only with the user group (other sharing is kept).
Users are assigned with zbx_user_set.py.
"""
import argparse
import json

from zbx_api import ZabbixError, api_from_stdin

USER_TYPE = 1
READ = 2


def user_actions(api):
    """Names of all actions available to User type roles."""
    role = api.call("role.get", {"output": ["roleid"], "selectRules": "extend", "filter": {"type": USER_TYPE}, "limit": 1})
    return [a["name"] for a in role[0]["rules"]["actions"]] if role else []


def role_rules(spec, action_names):
    """Zabbix enables every action that is not listed, actions.default_access only applies to
    actions added in future versions. So every known action is listed with its status."""
    allowed = set(spec.get("actions", []))
    unknown = allowed - set(action_names)
    if unknown:
        raise ZabbixError(f"unknown actions: {', '.join(sorted(unknown))}")
    return {
        "ui.default_access": 1,
        "ui": [{"name": name, "status": 0} for name in spec.get("ui_deny", [])],
        "modules.default_access": 1,
        "actions.default_access": 0,
        "actions": [{"name": name, "status": 1 if name in allowed else 0} for name in action_names],
        "api.access": 1 if spec.get("api") else 0,
    }


def apply_role(api, spec, dry_run):
    found = api.call("role.get", {"output": ["roleid"], "filter": {"name": [spec["name"]]}})
    params = {"name": spec["name"], "type": USER_TYPE, "rules": role_rules(spec, user_actions(api))}
    verb = "actualizar" if found else "crear"
    print(f"rol {spec['name']}: {verb} (UI denegada: {spec.get('ui_deny') or '—'}; "
          f"acciones: {spec.get('actions') or 'ninguna'}; API: {'sí' if spec.get('api') else 'no'})")
    if dry_run:
        return
    if found:
        api.call("role.update", {"roleid": found[0]["roleid"], **params})
    else:
        api.call("role.create", params)


def apply_user_group(api, spec, dry_run):
    groups = api.call("hostgroup.get", {"output": ["groupid", "name"], "filter": {"name": spec["read"]}})
    missing = set(spec["read"]) - {g["name"] for g in groups}
    if missing:
        raise ZabbixError(f"host groups not found: {', '.join(sorted(missing))}")
    found = api.call("usergroup.get", {"output": ["usrgrpid"], "filter": {"name": [spec["name"]]}})
    params = {"name": spec["name"], "hostgroup_rights": [{"id": g["groupid"], "permission": READ} for g in groups]}
    print(f"grupo {spec['name']}: {'actualizar' if found else 'crear'} (lectura: {', '.join(sorted(spec['read']))})")
    if dry_run:
        return found[0]["usrgrpid"] if found else None
    if found:
        api.call("usergroup.update", {"usrgrpid": found[0]["usrgrpid"], **params})
        return found[0]["usrgrpid"]
    return api.call("usergroup.create", params)["usrgrpids"][0]


def share_dashboards(api, names, usrgrpid, group_name, dry_run):
    dashboards = api.call("dashboard.get", {"output": ["dashboardid", "name"], "selectUserGroups": "extend",
                                            "filter": {"name": names}})
    missing = set(names) - {d["name"] for d in dashboards}
    if missing:
        raise ZabbixError(f"dashboards not found: {', '.join(sorted(missing))}")
    for d in dashboards:
        shared = [g for g in d["userGroups"] if g["usrgrpid"] != usrgrpid]
        print(f"dashboard {d['name']}: compartir con {group_name} (lectura)")
        if dry_run or usrgrpid is None:
            continue
        api.call("dashboard.update", {"dashboardid": d["dashboardid"],
                                      "userGroups": shared + [{"usrgrpid": usrgrpid, "permission": READ}]})


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    with open(args.file, encoding="utf-8") as f:
        spec = json.load(f)

    api = api_from_stdin()
    apply_role(api, spec["role"], args.dry_run)
    usrgrpid = apply_user_group(api, spec["user_group"], args.dry_run)
    share_dashboards(api, spec.get("dashboards", []), usrgrpid, spec["user_group"]["name"], args.dry_run)


if __name__ == "__main__":
    main()
