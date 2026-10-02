"""Replace the message operations of a trigger action from a JSON definition (zabbix_media/*.json).

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  run_remote.sh -f zabbix_media/escalation.json zbx_action_operations.py escalation.json [--dry-run]

JSON: {"action": NAME, "operations": [{"esc_step_from", "esc_step_to", "users": [USERNAME...],
"mediatype": NAME, "subject", "message"}]}. Every listed operation sends a custom message (not the
media type template) only through that media type. All existing operations of the action are replaced;
its conditions, recovery and update operations are kept.
"""
import argparse
import json

from zbx_api import ZabbixError, api_from_stdin


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("definition")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    with open(args.definition, encoding="utf-8") as f:
        spec = json.load(f)

    api = api_from_stdin()
    actions = api.call("action.get", {"output": ["actionid", "name"], "filter": {"name": [spec["action"]]}})
    if not actions:
        raise ZabbixError(f"action not found: {spec['action']}")
    media = {m["name"]: m["mediatypeid"] for m in api.call("mediatype.get", {"output": ["mediatypeid", "name"]})}
    users = {u["username"]: u["userid"] for u in api.call("user.get", {"output": ["userid", "username"]})}
    operations = []
    for op in spec["operations"]:
        missing = [u for u in op["users"] if u not in users] + ([op["mediatype"]] if op["mediatype"] not in media else [])
        if missing:
            raise ZabbixError(f"not found: {', '.join(missing)}")
        operations.append({
            "operationtype": 0, "esc_step_from": op["esc_step_from"], "esc_step_to": op["esc_step_to"],
            "opmessage": {"default_msg": 0, "mediatypeid": media[op["mediatype"]], "subject": op["subject"], "message": op["message"]},
            "opmessage_usr": [{"userid": users[u]} for u in op["users"]],
        })
        print(f"{spec['action']}: pasos {op['esc_step_from']}-{op['esc_step_to'] or '∞'} -> {', '.join(op['users'])} por {op['mediatype']} "
              f"(mensaje propio, {len(op['message'])} caracteres){' (dry-run)' if args.dry_run else ''}")
    if not args.dry_run:
        api.call("action.update", {"actionid": actions[0]["actionid"], "operations": operations})


if __name__ == "__main__":
    main()
