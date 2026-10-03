"""Create or update a trigger action from a JSON definition (e.g. zabbix_media/proveedor_coefi01.json).

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  run_remote.sh -f zabbix_media/X.json zbx_action_apply.py X.json [--dry-run]

JSON keys (names instead of ids):
  name, esc_period, pause_suppressed (default 1), notify_if_canceled (default 0)
  conditions: [{"tag": T, "value": V}] (tag value equals), [{"tag": T, "not_value": V}] (does not equal),
              [{"tag_exists": T}] (tag name equals), [{"not_suppressed": true}] (problem not in maintenance
              when it starts); all must match
  operations: [{"esc_step_from", "esc_step_to", "users": [USERNAME], "mediatype": NAME, "subject", "message"}]
  recovery: {"subject", "message"} sent to everyone notified about the problem, or with
            "users" and "mediatype" sent always to those users, also when the problem resolved before any
            operation step (short incidents) (optional)
The action is matched by name; conditions and operations are replaced on every run.
"""
import argparse
import json

from zbx_api import ZabbixError, api_from_stdin

TAG_NAME, TAG_VALUE, SUPPRESSED = 25, 26, 16
EQUAL, NOT_EQUAL, NO = 0, 1, 11


def conditions(spec):
    out = []
    for c in spec:
        if c.get("not_suppressed"):
            out.append({"conditiontype": SUPPRESSED, "operator": NO})
        elif "tag_exists" in c:
            out.append({"conditiontype": TAG_NAME, "operator": EQUAL, "value": c["tag_exists"]})
        elif "not_value" in c:
            out.append({"conditiontype": TAG_VALUE, "operator": NOT_EQUAL, "value": c["not_value"], "value2": c["tag"]})
        else:
            out.append({"conditiontype": TAG_VALUE, "operator": EQUAL, "value": c["value"], "value2": c["tag"]})
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("definition")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    with open(args.definition, encoding="utf-8") as f:
        spec = json.load(f)

    api = api_from_stdin()
    media = {m["name"]: m["mediatypeid"] for m in api.call("mediatype.get", {"output": ["mediatypeid", "name"]})}
    users = {u["username"]: u["userid"] for u in api.call("user.get", {"output": ["userid", "username"]})}
    operations = []
    for op in spec["operations"]:
        missing = [u for u in op["users"] if u not in users] + ([op["mediatype"]] if op["mediatype"] not in media else [])
        if missing:
            raise ZabbixError(f"not found: {', '.join(missing)}")
        operations.append({"operationtype": 0, "esc_step_from": op["esc_step_from"], "esc_step_to": op["esc_step_to"],
                           "opmessage": {"default_msg": 0, "mediatypeid": media[op["mediatype"]],
                                         "subject": op["subject"], "message": op["message"]},
                           "opmessage_usr": [{"userid": users[u]} for u in op["users"]]})
    body = {"name": spec["name"], "esc_period": spec.get("esc_period", "1h"),
            "pause_suppressed": spec.get("pause_suppressed", 1), "notify_if_canceled": spec.get("notify_if_canceled", 0),
            "filter": {"evaltype": 0, "conditions": conditions(spec["conditions"])}, "operations": operations}
    if "recovery" in spec:
        rec = spec["recovery"]
        message = {"default_msg": 0, "subject": rec["subject"], "message": rec["message"]}
        if "users" in rec:
            missing = [u for u in rec["users"] if u not in users] + ([rec["mediatype"]] if rec["mediatype"] not in media else [])
            if missing:
                raise ZabbixError(f"not found: {', '.join(missing)}")
            body["recovery_operations"] = [{"operationtype": 0, "opmessage": {**message, "mediatypeid": media[rec["mediatype"]]},
                                            "opmessage_usr": [{"userid": users[u]} for u in rec["users"]]}]
        else:
            body["recovery_operations"] = [{"operationtype": 11, "opmessage": message}]
    existing = api.call("action.get", {"output": ["actionid"], "filter": {"name": [spec["name"]]}})
    print(f"acción {spec['name']}: {'actualizar' if existing else 'crear'} | {len(body['filter']['conditions'])} condiciones | "
          f"{len(operations)} operaciones | escalada {body['esc_period']} | recuperación {'sí' if 'recovery' in spec else 'no'}")
    if args.dry_run:
        return
    if existing:
        api.call("action.update", {"actionid": existing[0]["actionid"], **{k: v for k, v in body.items() if k != "name"}})
    else:
        api.call("action.create", {"eventsource": 0, "status": 0, **body})
    print("aplicado")


if __name__ == "__main__":
    main()
