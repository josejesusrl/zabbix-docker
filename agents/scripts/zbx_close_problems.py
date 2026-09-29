"""Close open problems by name with a comment (false positives, stale problems of disabled triggers).

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  zbx_close_problems.py (--host NAME ... | --group GROUP | --tag TAG=VALUE) --name TEXT --message TEXT [--dry-run]

--name: text contained in the problem name (case insensitive). The trigger must allow manual close;
problems that cannot be closed are listed. The comment is notified like any acknowledgement.
Zabbix does not close problems of triggers disabled by discovery or of disabled items: close them here.
"""
import argparse

from zbx_api import api_from_stdin, find_hosts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", nargs="*", default=[])
    parser.add_argument("--group")
    parser.add_argument("--tag")
    parser.add_argument("--name", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.host or args.group or args.tag):
        parser.error("select hosts with --host, --group or --tag")

    api = api_from_stdin()
    hostids = [h["hostid"] for h in find_hosts(api, args.host, args.group, args.tag)]
    problems = [p for p in api.call("problem.get", {"hostids": hostids, "output": ["eventid", "name", "objectid"]})
                if args.name.lower() in p["name"].lower()]
    triggers = {t["triggerid"]: t for t in api.call("trigger.get", {"triggerids": [p["objectid"] for p in problems], "output": ["manual_close"]})} if problems else {}
    closable = [p for p in problems if triggers.get(p["objectid"], {}).get("manual_close") == "1"]
    for p in problems:
        state = "se cerraría" if args.dry_run else "cerrado"
        print(f"{p['name'][:100]} -> {state if p in closable else 'NO se puede cerrar a mano (trigger sin manual close)'}")
    if closable and not args.dry_run:
        # 1 = close problem, 4 = add message
        api.call("event.acknowledge", {"eventids": [p["eventid"] for p in closable], "action": 1 | 4, "message": args.message})
    print(f"{len(closable)} de {len(problems)} problemas")


if __name__ == "__main__":
    main()
