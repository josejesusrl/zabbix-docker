"""End-to-end test of notifications: fires a real problem, acknowledges it and resolves it.

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  zbx_test_notification.py [--severity 0-5] [--group GROUP] [--tag TAG=VALUE ...] [--hold SECONDS] [--keep]

Steps: creates a temporary host "ZZ-TEST mensajes" with a trapper item and a trigger, pushes a value
(history.push) to open a PROBLEM, acknowledges it with a comment (UPDATE), pushes the recovery value
(RESOLVED), prints the delivery status of every notification (sent / failed + error) and deletes the host
(unless --keep). The actions of the server decide who receives what (default severity High: Telegram + Gmail).
--tag adds host tags so that tag-filtered actions match (e.g. the provider notice: --group "Proveedores de internet"
--tag proveedor=Coefi01 "aviso_proveedor=Prueba"). --hold keeps the problem open longer before it is acknowledged
and resolved, to reach delayed escalation steps (the provider notice is sent after 5 min: --hold 330).
"""
import argparse
import time

from zbx_api import SEVERITIES, api_from_stdin

HOST = "ZZ-TEST mensajes"
KEY = "test.alert"
STATUS = {"0": "pendiente", "1": "enviado", "2": "FALLÓ", "3": "en cola"}


def wait_for(fetch, timeout=90, step=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = fetch()
        if result:
            return result
        time.sleep(step)
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--severity", type=int, default=4, choices=range(6))
    parser.add_argument("--group", default="Zabbix servers")
    parser.add_argument("--tag", nargs="*", default=[], help="extra host tags TAG=VALUE")
    parser.add_argument("--hold", type=int, default=20, help="seconds the problem stays open before the acknowledgement")
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()

    api = api_from_stdin()
    if api.call("host.get", {"filter": {"host": [HOST]}}):
        raise SystemExit(f"'{HOST}' already exists: delete it first")
    group = api.call("hostgroup.get", {"filter": {"name": [args.group]}, "output": ["groupid"]})[0]["groupid"]
    # Interface, tags and trigger description so that every macro of the message templates is filled
    # ({HOST.IP}, {EVENT.TAGS.uplink}, {TRIGGER.DESCRIPTION}); the interface is never polled (trapper item).
    hostid = api.call("host.create", {"host": HOST, "groups": [{"groupid": group}],
                                      "interfaces": [{"type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": "10050"}],
                                      "tags": [{"tag": "uplink", "value": "ZZ-TEST padre"}, {"tag": "scope", "value": "test"}]
                                              + [dict(zip(("tag", "value"), t.split("=", 1))) for t in args.tag],
                                      "description": "Temporary host of agents/scripts/zbx_test_notification.py"})["hostids"][0]
    try:
        itemid = api.call("item.create", {"hostid": hostid, "name": "Test alert", "key_": KEY, "type": 2, "value_type": 3})["itemids"][0]
        api.call("trigger.create", {"description": "Prueba de notificaciones <test> & formato", "priority": args.severity,
                                    "expression": f"last(/{HOST}/{KEY})=1", "manual_close": 1,
                                    "opdata": "Valor: {ITEM.LASTVALUE1}",
                                    "comments": "Mensaje de prueba de zbx_test_notification.py.\nSegunda línea: <b>no</b> debe verse en negrita."})
        time.sleep(15)  # configuration cache sync
        api.call("history.push", [{"itemid": itemid, "value": "1"}])
        event = wait_for(lambda: api.call("problem.get", {"hostids": hostid, "output": ["eventid", "name"]}))
        if not event:
            raise SystemExit("the problem was not created")
        eventid = event[0]["eventid"]
        print(f"PROBLEMA abierto: evento {eventid} ({SEVERITIES[args.severity]}), abierto {args.hold} s", flush=True)
        time.sleep(args.hold)
        api.call("event.acknowledge", {"eventids": [eventid], "action": 2 | 4, "message": "Prueba de actualización: comentario con <símbolos> & acentos"})
        print("ACTUALIZACIÓN: reconocido con comentario")
        time.sleep(20)
        api.call("history.push", [{"itemid": itemid, "value": "0"}])
        wait_for(lambda: not api.call("problem.get", {"hostids": hostid, "output": ["eventid"]}))
        print("RESUELTO")
        time.sleep(30)
        # Recovery notifications belong to the recovery event (r_eventid of the problem event)
        r_eventid = api.call("event.get", {"eventids": [eventid], "output": ["r_eventid"]})[0]["r_eventid"]
        alerts = api.call("alert.get", {"eventids": [eventid, r_eventid], "output": ["clock", "status", "error", "subject"],
                                        "selectMediatypes": ["name"], "sortfield": "clock"})
        print(f"\nNotificaciones ({len(alerts)}):")
        for a in alerts:
            media = a["mediatypes"][0]["name"] if a["mediatypes"] else "?"
            print(f"  {time.strftime('%H:%M:%S', time.gmtime(int(a['clock'])))} {media:9} {STATUS.get(a['status'], a['status']):9} "
                  f"{a['subject'][:45]!r} {('error: ' + a['error']) if a['error'] else ''}")
    finally:
        if not args.keep:
            api.call("host.delete", [hostid])
            print(f"\nHost '{HOST}' eliminado")


if __name__ == "__main__":
    main()
