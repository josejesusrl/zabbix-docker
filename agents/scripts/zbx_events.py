"""Problem events of the last hours grouped by host and trigger, to spot false positives and flapping (read-only).

Usage (token on stdin, see README.md):
  zbx_events.py [--hours N] [--group GROUP] [--host NAME ...] [--min-severity 0-5]

For each trigger: how many times it opened, how many are still open, first/last time (UTC),
how many notifications were sent and whether problems were closed manually. Triggers that open
several times in the period are candidates for flapping or wrong thresholds.
"""
import argparse
import collections
import time

from zbx_api import SEVERITIES, api_from_stdin, find_hosts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hours", type=float, default=24)
    parser.add_argument("--group")
    parser.add_argument("--host", nargs="*", default=[])
    parser.add_argument("--min-severity", type=int, default=0)
    args = parser.parse_args()

    api = api_from_stdin()
    params = {"source": 0, "object": 0, "value": 1, "time_from": int(time.time() - args.hours * 3600),
              "severities": list(range(args.min_severity, 6)), "output": ["eventid", "name", "severity", "clock", "r_eventid"],
              "selectHosts": ["name"], "selectAcknowledges": ["action"], "sortfield": ["clock"], "sortorder": "ASC"}
    if args.group or args.host:
        params["hostids"] = [h["hostid"] for h in find_hosts(api, args.host, args.group)]
    events = api.call("event.get", params)
    alerts = collections.Counter()
    if events:
        # Only messages (alerttype 0), not remote commands
        for alert in api.call("alert.get", {"eventids": [e["eventid"] for e in events], "output": ["eventid", "alerttype"]}):
            if alert["alerttype"] != "0":
                continue
            alerts[alert["eventid"]] += 1

    groups = collections.defaultdict(list)
    for e in events:
        host = e["hosts"][0]["name"] if e["hosts"] else "?"
        groups[(host, e["name"], e["severity"])].append(e)
    fmt = lambda t: time.strftime("%m-%d %H:%M", time.gmtime(int(t)))
    print(f"{len(events)} problem events in {args.hours:g} h, {len(groups)} distinct triggers\n")
    for (host, name, sev), evs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        open_now = sum(1 for e in evs if e["r_eventid"] == "0")
        closed_manually = sum(1 for e in evs if any(int(a["action"]) & 1 for a in e["acknowledges"]))
        notified = sum(alerts[e["eventid"]] for e in evs)
        print(f"{len(evs):3}x {SEVERITIES[int(sev)]:11} {host:28} {name[:90]}")
        print(f"      {fmt(evs[0]['clock'])} -> {fmt(evs[-1]['clock'])} UTC | abiertos: {open_now} | cerrados a mano: {closed_manually} | notificaciones: {notified}")


if __name__ == "__main__":
    main()
