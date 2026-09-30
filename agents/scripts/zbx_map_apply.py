"""Create or update network maps generated from the topology: a general map and one submap per site.

Usage (token on stdin, see README.md). Requires a recent backup (AGENTS.md, rule 1):
  run_remote.sh -f zabbix_maps/likson_red.json zbx_map_apply.py likson_red.json [--dry-run]

The parent of each host is its topological dependency (the same one shown by zbx_inventory.py), so the
maps follow the inventory without positions kept by hand. Maps are matched by name and their elements
and links are replaced on every run; sysmapids stay the same, so dashboard widgets keep working.

JSON keys:
  general       name of the general map (hosts outside the submaps, one element per submap)
  submaps       [{"root": HOST, "name": MAP}]: the root host and everything that depends on it
  exclude       hosts not drawn (hosts without interfaces are always skipped)
  icons         ordered rules {"group"|"template": NAME, "icon": IMAGE}; first match wins
  default_icon, submap_icon, back_icon   image names (Administration -> General -> Images)
  share_read    user groups with read-only access to the maps
Links turn red and bold while the child host is down ('Unavailable by ICMP ping').
"""
import argparse
import json
import math

from zbx_api import ICMP_DOWN, ZabbixError, api_from_stdin, availability_triggers, upstream_hosts

DX, DY, LEAF_DY = 120, 130, 110   # spacing between elements (pixels)
LEAVES_PER_ROW = 8                # leaf children are packed in rows under their parent
MARGIN = 70
LABEL = "{HOST.NAME}\n{HOST.CONN}"
READ = 2


def load_topology(api, spec):
    hosts = api.call("host.get", {"output": ["hostid", "name"], "selectInterfaces": ["interfaceid"],
                                  "selectHostGroups": ["name"], "selectParentTemplates": ["name"]})
    hosts = {h["name"]: h for h in hosts if h["interfaces"] and h["name"] not in spec.get("exclude", [])}
    for h in hosts.values():
        parents = [p for p in upstream_hosts(api, h["hostid"]) if p in hosts]
        if len(parents) > 1:
            print(f"aviso: {h['name']} depende de varios equipos ({', '.join(parents)}), se dibuja bajo {parents[0]}")
        h["parent"] = parents[0] if parents else None
        h["icmp"] = availability_triggers(api, h["hostid"]).get(ICMP_DOWN, {}).get("triggerid")
    children = {name: [] for name in hosts}
    for h in hosts.values():
        if h["parent"]:
            children[h["parent"]].append(h["name"])
    for names in children.values():
        names.sort()
    return hosts, children


def icon_name(spec, host):
    groups = {g["name"] for g in host["hostgroups"]}
    templates = " ".join(t["name"] for t in host["parentTemplates"])
    for rule in spec["icons"]:
        if rule.get("group") in groups or (rule.get("template") and rule["template"] in templates):
            return rule["icon"]
    return spec["default_icon"]


def layout(node, children, x, y, pos):
    """Top-down tree. Returns the width used. Leaf children go in rows of LEAVES_PER_ROW."""
    kids = children(node)
    leaves = [k for k in kids if not children(k)]
    branches = [k for k in kids if children(k)]
    cols = min(len(leaves), LEAVES_PER_ROW)
    grid_w = cols * DX
    width = grid_w
    for k in branches:
        width += layout(k, children, x + width, y + DY, pos)
    for i, k in enumerate(leaves):
        pos[k] = (x + (i % LEAVES_PER_ROW) * DX, y + DY + (i // LEAVES_PER_ROW) * LEAF_DY)
    width = max(width, DX)
    pos[node] = (x + width // 2 - DX // 2, y)
    return width


def build(roots, children):
    pos, x = {}, MARGIN
    for r in roots:
        x += layout(r, children, x, MARGIN, pos)
    return pos


def descendants(root, children):
    found = [root]
    for k in children[root]:
        found += descendants(k, children)
    return found


def map_body(spec, hosts, children, members, roots, maps, images, cut=(), back=None):
    """Elements, links and size of one map. cut: {host: submap name} drawn as submap elements."""
    def kids(n):
        return [] if n in cut else [k for k in children[n] if k in members]
    pos = build(roots, kids)
    if back:
        pos["__back__"] = (MARGIN, MARGIN)
        pos = {k: (x + (DX if k != "__back__" else 0), y) for k, (x, y) in pos.items()}
    elements, links = [], []
    for name, (x, y) in pos.items():
        if name == "__back__":
            # Image with a URL: a map element would be a circular reference (general -> submap -> general)
            elements.append({"key": name, "elementtype": 4, "iconid_off": images[spec["back_icon"]],
                             "label": f"Volver a {back}", "x": x, "y": y,
                             "urls": [{"name": back, "url": f"zabbix.php?action=map.view&sysmapid={maps[back]}"}]})
        elif name in cut:
            count = len(descendants(name, children))
            elements.append({"key": name, "elementtype": 1, "elements": [{"sysmapid": maps[cut[name]]}],
                             "iconid_off": images[spec["submap_icon"]], "label": f"{cut[name]}\n{count} equipos",
                             "x": x, "y": y})
        else:
            elements.append({"key": name, "elementtype": 0, "elements": [{"hostid": hosts[name]["hostid"]}],
                             "iconid_off": images[icon_name(spec, hosts[name])], "label": LABEL, "x": x, "y": y})
        parent = hosts.get(name, {}).get("parent")
        if name != "__back__" and parent in pos:
            link = {"from": parent, "to": name, "color": "999999", "drawtype": 0, "linktriggers": []}
            if hosts[name]["icmp"]:
                link["linktriggers"] = [{"triggerid": hosts[name]["icmp"], "color": "DD0000", "drawtype": 2}]
            links.append(link)
    width = max(x for x, _ in pos.values()) + DX + MARGIN
    height = max(y for _, y in pos.values()) + LEAF_DY + MARGIN
    return elements, links, width, height


def element_ref(elementtype, elements):
    """Identity of a map element to match it after the update: host, submap or image."""
    if elementtype == 0:
        return ("h", elements[0]["hostid"])
    if elementtype == 1:
        return ("m", elements[0]["sysmapid"])
    return ("i", elementtype)


def apply_map(api, sysmapid, elements, links, width, height, share):
    selements = [{k: v for k, v in e.items() if k != "key"} for e in elements]
    api.call("map.update", {"sysmapid": sysmapid, "width": width, "height": height, "links": [],
                               "selements": selements, "label_type": 0, "expand_macros": 1, "highlight": 1,
                               "private": 1, "userGroups": share})
    placed = api.call("map.get", {"sysmapids": sysmapid, "selectSelements": ["selementid", "elements", "elementtype"]})[0]
    ids = {element_ref(int(s["elementtype"]), s.get("elements")): s["selementid"] for s in placed["selements"]}
    key_ref = {e["key"]: element_ref(e["elementtype"], e.get("elements")) for e in elements}
    api.call("map.update", {"sysmapid": sysmapid, "links": [
        {"selementid1": ids[key_ref[l["from"]]], "selementid2": ids[key_ref[l["to"]]], "color": l["color"],
         "drawtype": l["drawtype"], "linktriggers": l["linktriggers"],
         # Zabbix 7.4: link indicators must be of trigger type (1) to accept linktriggers
         "indicator_type": 1 if l["linktriggers"] else 0} for l in links]})


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("definition")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    with open(args.definition, encoding="utf-8") as f:
        spec = json.load(f)

    api = api_from_stdin()
    hosts, children = load_topology(api, spec)
    for s in spec["submaps"]:
        if s["root"] not in hosts:
            raise ZabbixError(f"submap root not found: {s['root']}")
    wanted = [spec["general"]] + [s["name"] for s in spec["submaps"]]
    image_names = {r["icon"] for r in spec["icons"]} | {spec["default_icon"], spec["submap_icon"], spec["back_icon"]}
    images = {i["name"]: i["imageid"] for i in api.call("image.get", {"output": ["name"], "filter": {"name": list(image_names)}})}
    missing = image_names - set(images)
    if missing:
        raise ZabbixError(f"images not found: {', '.join(sorted(missing))}")
    groups = api.call("usergroup.get", {"output": ["usrgrpid", "name"], "filter": {"name": spec.get("share_read", [])}})
    share = [{"usrgrpid": g["usrgrpid"], "permission": READ} for g in groups]

    existing = {m["name"]: m["sysmapid"] for m in api.call("map.get", {"output": ["name"], "filter": {"name": wanted}})}
    maps = dict(existing)
    for name in wanted:
        if name not in maps:
            print(f"mapa {name}: crear")
            maps[name] = "0" if args.dry_run else api.call("map.create", {"name": name, "width": 800, "height": 600})["sysmapids"][0]

    cut = {s["root"]: s["name"] for s in spec["submaps"]}
    inside = {h for s in spec["submaps"] for h in descendants(s["root"], children)}
    general_members = {h for h in hosts if h not in inside} | set(cut)
    roots = sorted(h for h in general_members if not hosts[h]["parent"])
    plans = [(spec["general"], map_body(spec, hosts, children, general_members, roots, maps, images, cut=cut))]
    for s in spec["submaps"]:
        members = set(descendants(s["root"], children))
        plans.append((s["name"], map_body(spec, hosts, children, members, [s["root"]], maps, images, back=spec["general"])))

    for name, (elements, links, width, height) in plans:
        hosts_count = sum(1 for e in elements if e["elementtype"] == 0)
        print(f"mapa {name}: {hosts_count} equipos, {len(elements) - hosts_count} submapas/enlaces a mapas, "
              f"{len(links)} líneas, {width}x{height} px{' (dry-run)' if args.dry_run else ''}")
        if args.dry_run:
            for l in links:
                print(f"   {l['from']} -> {l['to']}")
        else:
            apply_map(api, maps[name], elements, links, width, height, share)


if __name__ == "__main__":
    main()
