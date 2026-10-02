"""Create, list or end one-time maintenance periods (problems are suppressed: no notifications).

Usage (token on stdin, see README.md). Creating or ending requires a recent backup (AGENTS.md, rule 1):
  zbx_maintenance.py --list
  zbx_maintenance.py --create NAME (--host NAME ... | --group GROUP) --minutes N
                     [--start "YYYY-MM-DD HH:MM"] [--tag TAG=VALUE ...] [--description TEXT] [--dry-run]
  zbx_maintenance.py --end NAME [--dry-run]

- With data collection: Zabbix keeps collecting, only notifications pause. Starts now by default; Zabbix
  applies it within about 1 minute, so create it a few minutes before the work.
- --tag limits the suppression to problems with those tags (e.g. --tag proveedor=Coefi01: only the provider
  notices; the rest of the problems of those hosts still notify).
- --end deletes the maintenance: if a problem is still open, its notifications resume at that moment
  (the provider notice is sent at once if 5 minutes have passed). End it only when everything is OK.
- --start and the printed times use --tz (default America/Mexico_City, the time zone of the Zabbix frontend),
  not the clock of the host where the script runs (UTC on the server).
"""
import argparse
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from zbx_api import ZabbixError, api_from_stdin, find_hosts

WITH_DATA, ONE_TIME, EQUALS = 0, 0, 0
TZ = ZoneInfo("America/Mexico_City")


def fmt(ts, pattern="%Y-%m-%d %H:%M"):
    return datetime.fromtimestamp(int(ts), TZ).strftime(pattern)


def show(api):
    now = time.time()
    for m in api.call("maintenance.get", {"output": ["name", "active_since", "active_till", "description"],
                                          "selectHosts": ["name"], "selectHostGroups": ["name"], "selectTags": "extend"}):
        state = "activo" if int(m["active_since"]) <= now <= int(m["active_till"]) else (
            "programado" if now < int(m["active_since"]) else "caducado")
        targets = [h["name"] for h in m["hosts"]] + [g["name"] for g in m.get("hostgroups", [])]
        tags = ", ".join(f"{t['tag']}={t['value']}" for t in m["tags"]) or "todos los problemas"
        print(f"{m['name']}: {state} {fmt(m['active_since'])} → {fmt(m['active_till'], '%H:%M')} | {', '.join(targets)} | {tags}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--list", action="store_true")
    action.add_argument("--create", metavar="NAME")
    action.add_argument("--end", metavar="NAME")
    parser.add_argument("--host", nargs="*", default=[])
    parser.add_argument("--group")
    parser.add_argument("--minutes", type=int)
    parser.add_argument("--start", help='"YYYY-MM-DD HH:MM" (default: now)')
    parser.add_argument("--tag", nargs="*", default=[])
    parser.add_argument("--description", default="")
    parser.add_argument("--tz", default="America/Mexico_City", help="time zone of --start and of the output")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    global TZ
    TZ = ZoneInfo(args.tz)
    api = api_from_stdin()

    if args.list:
        show(api)
        return
    if args.end:
        found = api.call("maintenance.get", {"output": ["maintenanceid"], "filter": {"name": [args.end]}})
        if not found:
            raise ZabbixError(f"maintenance not found: {args.end}")
        print(f"terminar (borrar) mantenimiento {args.end}{' (dry-run)' if args.dry_run else ''}")
        if not args.dry_run:
            api.call("maintenance.delete", [found[0]["maintenanceid"]])
        return
    if not args.minutes or not (args.host or args.group):
        parser.error("--create needs --minutes and --host or --group")
    start = (int(datetime.strptime(args.start, "%Y-%m-%d %H:%M").replace(tzinfo=TZ).timestamp()) if args.start
             else int(time.time()) // 60 * 60)
    end = start + args.minutes * 60
    body = {"name": args.create, "maintenance_type": WITH_DATA, "active_since": start, "active_till": end,
            "description": args.description,
            "timeperiods": [{"timeperiod_type": ONE_TIME, "start_date": start, "period": args.minutes * 60}]}
    if args.group:
        body["groups"] = [{"groupid": g["groupid"]} for g in api.call("hostgroup.get", {"output": ["groupid"], "filter": {"name": [args.group]}})]
    if args.host:
        body["hosts"] = [{"hostid": h["hostid"]} for h in find_hosts(api, args.host)]
    if args.tag:
        body["tags_evaltype"] = 0
        body["tags"] = [{"tag": t.split("=", 1)[0], "operator": EQUALS, "value": t.split("=", 1)[1]} for t in args.tag]
    print(f"mantenimiento {args.create}: {fmt(start)} → {fmt(end, '%H:%M')} ({args.minutes} min, {args.tz}) | "
          f"{', '.join(args.host) or args.group} | "
          f"{', '.join(args.tag) or 'todos los problemas'}{' (dry-run)' if args.dry_run else ''}")
    if not args.dry_run:
        api.call("maintenance.create", body)
        print("creado")


if __name__ == "__main__":
    main()
