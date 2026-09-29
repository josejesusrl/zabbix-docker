"""Minimal Zabbix API client and shared helpers for the agent scripts.

Every CLI script in this directory imports this module, so API access, lookups and the
dependency rules live in one place (DRY). Scripts are run on the Zabbix server through
run_remote.sh, where the API is reachable at https://localhost with a self-signed certificate.

Security: the API token is read from the first line of stdin, never from arguments,
environment or files, so it does not appear in process lists or shell history.
"""
import json
import ssl
import sys
import urllib.request

DEFAULT_URL = "https://localhost/api_jsonrpc.php"

# Availability triggers of official SNMP/agent templates, used for topological dependencies
ICMP_DOWN = "Unavailable by ICMP ping"
AVAILABILITY_TRIGGERS = (ICMP_DOWN, "High ICMP ping loss", "High ICMP ping response time", "No SNMP data collection")

SEVERITIES = ("Not classified", "Information", "Warning", "Average", "High", "Disaster")
AVAILABLE = {"0": "unknown", "1": "available", "2": "unavailable"}


class ZabbixError(RuntimeError):
    """Error returned by the Zabbix API."""


class ZabbixAPI:
    """JSON-RPC client authenticated with an API token."""

    def __init__(self, token, url=DEFAULT_URL):
        self._token = token
        self._url = url
        # The frontend uses a self-signed certificate on localhost
        self._ssl = ssl._create_unverified_context()

    def call(self, method, params):
        body = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode()
        headers = {"Content-Type": "application/json-rpc", "Authorization": "Bearer " + self._token}
        request = urllib.request.Request(self._url, body, headers)
        with urllib.request.urlopen(request, context=self._ssl) as response:
            reply = json.load(response)
        if "error" in reply:
            raise ZabbixError(f"{method}: {reply['error'].get('data') or reply['error']}")
        return reply["result"]


def api_from_stdin(url=DEFAULT_URL):
    """Build a client with the token from the first line of stdin."""
    token = sys.stdin.readline().strip()
    if not token:
        sys.exit("API token expected on the first line of stdin")
    return ZabbixAPI(token, url)


# --- Lookups -----------------------------------------------------------------------------

def short_name(description):
    """Trigger name without the template prefix: 'MikroTik: Unavailable by ICMP ping' -> 'Unavailable by ICMP ping'."""
    return description.split(": ", 1)[-1]


def get_host(api, name, **select):
    """Host by technical or visible name. Extra select* options are passed to host.get."""
    for field in ("host", "name"):
        hosts = api.call("host.get", {"filter": {field: [name]}, "output": ["hostid", "host", "name"], **select})
        if hosts:
            return hosts[0]
    raise ZabbixError(f"host not found: {name}")


def find_hosts(api, names=(), group=None, tag=None, **select):
    """Hosts selected by names, host group and/or tag ('tag=value'). With no filter, all hosts."""
    params = {"output": ["hostid", "host", "name"], **select}
    if group:
        groups = api.call("hostgroup.get", {"filter": {"name": [group]}, "output": ["groupid"]})
        if not groups:
            raise ZabbixError(f"host group not found: {group}")
        params["groupids"] = [groups[0]["groupid"]]
    if tag:
        key, _, value = tag.partition("=")
        params["tags"] = [{"tag": key, "value": value, "operator": 1}]
    hosts = api.call("host.get", params)
    if names:
        wanted = set(names)
        hosts = [h for h in hosts if h["host"] in wanted or h["name"] in wanted]
        missing = wanted - {h["host"] for h in hosts} - {h["name"] for h in hosts}
        if missing:
            raise ZabbixError(f"hosts not found: {', '.join(sorted(missing))}")
    return sorted(hosts, key=lambda h: h["name"])


def availability_triggers(api, hostid):
    """Availability triggers of a host as {short name: trigger}, with their dependencies."""
    triggers = api.call("trigger.get", {
        "hostids": hostid, "output": ["triggerid", "description"], "selectDependencies": ["triggerid"],
        "search": {"description": list(AVAILABILITY_TRIGGERS)}, "searchByAny": True,
    })
    return {short_name(t["description"]): t for t in triggers}


def icmp_down_trigger(api, hostid):
    """Trigger id of 'Unavailable by ICMP ping' of a host."""
    trigger = availability_triggers(api, hostid).get(ICMP_DOWN)
    if not trigger:
        raise ZabbixError(f"host {hostid} has no '{ICMP_DOWN}' trigger")
    return trigger["triggerid"]


def trigger_hosts(api, triggerids):
    """{triggerid: (host name, short trigger name)} for the given triggers."""
    if not triggerids:
        return {}
    triggers = api.call("trigger.get", {"triggerids": list(triggerids), "output": ["description"], "selectHosts": ["name"]})
    return {t["triggerid"]: (t["hosts"][0]["name"], short_name(t["description"])) for t in triggers}


def upstream_hosts(api, hostid):
    """Names of the hosts this host depends on (topological dependencies of its availability triggers)."""
    own = api.call("host.get", {"hostids": hostid, "output": ["name"]})[0]["name"]
    deps = {d["triggerid"] for t in availability_triggers(api, hostid).values() for d in t["dependencies"]}
    return sorted({host for host, _ in trigger_hosts(api, deps).values() if host != own})


def global_macro(api, macro):
    """Value of a global macro. Secret macros are not returned by the API."""
    macros = api.call("usermacro.get", {"globalmacro": True, "filter": {"macro": macro}, "output": ["value", "type"]})
    if not macros:
        raise ZabbixError(f"global macro not found: {macro}")
    if macros[0]["type"] != "0":
        raise ZabbixError(f"{macro} is a secret macro, its value cannot be read through the API")
    return macros[0]["value"]


# --- Changes -----------------------------------------------------------------------------

def set_host_macro(api, hostid, macro, value, description=""):
    """Create or update a host macro."""
    existing = api.call("usermacro.get", {"hostids": hostid, "filter": {"macro": macro}, "output": ["hostmacroid"]})
    if existing:
        api.call("usermacro.update", {"hostmacroid": existing[0]["hostmacroid"], "value": value})
    else:
        api.call("usermacro.create", {"hostid": hostid, "macro": macro, "value": value, "description": description})


def set_host_tag(api, hostid, tag, value):
    """Set a host tag, replacing any previous value of the same tag."""
    tags = api.call("host.get", {"hostids": hostid, "output": ["hostid"], "selectTags": ["tag", "value"]})[0]["tags"]
    tags = [t for t in tags if t["tag"] != tag] + [{"tag": tag, "value": value}]
    api.call("host.update", {"hostid": hostid, "tags": tags})


def set_upstream(api, hostid, parent_hostid, dry_run=False):
    """Make the availability triggers of a host depend on the parent's 'Unavailable by ICMP ping'.

    Dependencies on triggers of the same host (template internal ones, e.g. loss -> own ICMP down)
    are kept. Dependencies on other hosts are topological and replaced by the new parent.
    Returns the list of changed trigger names.
    """
    parent_down = icmp_down_trigger(api, parent_hostid)
    own = api.call("host.get", {"hostids": hostid, "output": ["name"]})[0]["name"]
    changed = []
    for name, trigger in availability_triggers(api, hostid).items():
        current = {d["triggerid"] for d in trigger["dependencies"]}
        owners = trigger_hosts(api, current)
        wanted = {tid for tid in current if owners[tid][0] == own} | {parent_down}
        if wanted != current:
            changed.append(name)
            if not dry_run:
                api.call("trigger.update", {"triggerid": trigger["triggerid"], "dependencies": [{"triggerid": t} for t in wanted]})
    return changed


def add_self_dependency(api, hostid, pattern, dry_run=False):
    """Make triggers whose name contains `pattern` depend on the host's own 'Unavailable by ICMP ping'.

    Example: 'no connected clients' on APs, so an unreachable AP does not also report 0 clients.
    Returns the list of changed trigger names.
    """
    own_down = icmp_down_trigger(api, hostid)
    triggers = api.call("trigger.get", {"hostids": hostid, "output": ["triggerid", "description"],
                                        "selectDependencies": ["triggerid"], "search": {"description": [pattern]}})
    changed = []
    for trigger in triggers:
        current = {d["triggerid"] for d in trigger["dependencies"]}
        if own_down not in current:
            changed.append(short_name(trigger["description"]))
            if not dry_run:
                api.call("trigger.update", {"triggerid": trigger["triggerid"],
                                            "dependencies": [{"triggerid": t} for t in current | {own_down}]})
    return changed


def find_triggers(api, hostid, text):
    """Triggers of a host whose name contains `text` (macros expanded), with their dependencies."""
    triggers = api.call("trigger.get", {"hostids": hostid, "output": ["triggerid", "description", "status"],
                                        "selectDependencies": ["triggerid"], "expandDescription": True})
    return [t for t in triggers if text.lower() in t["description"].lower()]


def add_dependency(api, trigger, parent_triggerid, dry_run=False):
    """Add a dependency keeping the existing ones. Returns True if it was missing."""
    current = {d["triggerid"] for d in trigger["dependencies"]}
    if parent_triggerid in current:
        return False
    if not dry_run:
        api.call("trigger.update", {"triggerid": trigger["triggerid"],
                                    "dependencies": [{"triggerid": t} for t in current | {parent_triggerid}]})
    return True


def check_now(api, hostids, key_prefix=""):
    """Execute now the collected items and discovery rules of hosts (dependent items follow their master)."""
    params = {"hostids": list(hostids), "output": ["itemid", "type"]}
    if key_prefix:
        params["search"] = {"key_": key_prefix}
        params["startSearch"] = True
    targets = api.call("item.get", params) + api.call("discoveryrule.get", params)
    # 18 = dependent item, 2 = trapper, 17 = SNMP trap: cannot be polled
    itemids = [t["itemid"] for t in targets if t.get("type") not in ("18", "2", "17")]
    for itemid in itemids:
        api.call("task.create", [{"type": "6", "request": {"itemid": itemid}}])
    return len(itemids)


def import_template(api, yaml_text, delete_missing=False):
    """Import a template YAML export, creating and updating objects.

    With delete_missing, items, triggers and discovery rules (including prototypes) that are no
    longer in the file are removed from the template.
    """
    update = {"createMissing": True, "updateExisting": True}
    rules = {"template_groups": {"createMissing": True}, "templates": dict(update), "valueMaps": dict(update)}
    for kind in ("items", "triggers", "discoveryRules", "graphs"):
        rules[kind] = {**update, "deleteMissing": delete_missing}
    api.call("configuration.import", {"format": "yaml", "rules": rules, "source": yaml_text})
