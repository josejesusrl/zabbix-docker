"""Create or update a dashboard from a readable JSON definition (zabbix_dashboards/*.json).

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  run_remote.sh -f zabbix_dashboards/likson_noc.json zbx_dashboard_apply.py likson_noc.json [--dry-run]

Definition format: {"name", "display_period", "auto_start", "pages": [{"name", "widgets": [
  {"type", "name", "x", "y", "width", "height", "fields": {FIELD: VALUE}}]}]}
Field values are written by name instead of ids and converted to Zabbix widget fields:
  integer -> type 0 | string -> type 1 | {"group": NAME} -> type 2 | {"host": NAME} -> type 3
  {"item": [HOST, KEY]} -> type 4
A "reference" is generated for widget types that need one. The dashboard is matched by name:
updating replaces all its pages and widgets with the definition.
"""
import argparse
import json
import random
import string

from zbx_api import ZabbixError, api_from_stdin

NEEDS_REFERENCE = {"svggraph", "problems", "problemsbysv", "honeycomb", "hostnavigator", "itemnavigator", "geomap", "map", "tophosts", "topitems"}


class Resolver:
    """Translates group/host/item names to ids, caching lookups."""

    def __init__(self, api):
        self.api = api
        self.cache = {}

    def _one(self, method, params, label):
        key = (method, json.dumps(params, sort_keys=True))
        if key not in self.cache:
            found = self.api.call(method, params)
            if len(found) != 1:
                raise ZabbixError(f"{label}: {len(found)} matches")
            self.cache[key] = found[0]
        return self.cache[key]

    def group(self, name):
        return self._one("hostgroup.get", {"filter": {"name": [name]}, "output": ["groupid"]}, f"group '{name}'")["groupid"]

    def host(self, name):
        return self._one("host.get", {"filter": {"name": [name]}, "output": ["hostid"]}, f"host '{name}'")["hostid"]

    def item(self, host, key):
        return self._one("item.get", {"hostids": self.host(host), "filter": {"key_": key}, "output": ["itemid"]},
                         f"item '{host}' / '{key}'")["itemid"]


def to_fields(fields, resolver):
    result = []
    for name, value in fields.items():
        if isinstance(value, bool) or isinstance(value, int):
            result.append({"type": 0, "name": name, "value": int(value)})
        elif isinstance(value, str):
            result.append({"type": 1, "name": name, "value": value})
        elif "group" in value:
            result.append({"type": 2, "name": name, "value": resolver.group(value["group"])})
        elif "host" in value:
            result.append({"type": 3, "name": name, "value": resolver.host(value["host"])})
        elif "item" in value:
            result.append({"type": 4, "name": name, "value": resolver.item(*value["item"])})
        else:
            raise ZabbixError(f"unknown field value for {name}: {value}")
    return result


def build_pages(definition, resolver):
    used = set()
    pages = []
    for page in definition["pages"]:
        widgets = []
        for w in page["widgets"]:
            fields = to_fields(w.get("fields", {}), resolver)
            if w["type"] in NEEDS_REFERENCE and not any(f["name"] == "reference" for f in fields):
                ref = "".join(random.choices(string.ascii_uppercase, k=5))
                while ref in used:
                    ref = "".join(random.choices(string.ascii_uppercase, k=5))
                used.add(ref)
                fields.append({"type": 1, "name": "reference", "value": ref})
            widgets.append({"type": w["type"], "name": w.get("name", ""), "x": w["x"], "y": w["y"],
                            "width": w["width"], "height": w["height"], "view_mode": w.get("view_mode", 0), "fields": fields})
        pages.append({"name": page["name"], "display_period": page.get("display_period", 0), "widgets": widgets})
    return pages


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("definition")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(args.definition, encoding="utf-8") as f:
        definition = json.load(f)
    api = api_from_stdin()
    pages = build_pages(definition, Resolver(api))
    body = {"name": definition["name"], "display_period": definition.get("display_period", 30),
            "auto_start": definition.get("auto_start", 1), "pages": pages}
    summary = ", ".join(f"{p['name']} ({len(p['widgets'])} widgets)" for p in pages)
    existing = api.call("dashboard.get", {"filter": {"name": [definition["name"]]}, "output": ["dashboardid"]})
    if args.dry_run:
        print(f"{'Actualizaría' if existing else 'Crearía'} '{definition['name']}': {summary} (nombres resueltos correctamente)")
        return
    if existing:
        api.call("dashboard.update", {"dashboardid": existing[0]["dashboardid"], **body})
        print(f"Actualizado '{definition['name']}' (id {existing[0]['dashboardid']}): {summary}")
    else:
        dashboardid = api.call("dashboard.create", body)["dashboardids"][0]
        print(f"Creado '{definition['name']}' (id {dashboardid}): {summary}")


if __name__ == "__main__":
    main()
