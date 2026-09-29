"""Run net-snmp commands on the Zabbix server with the community of a Zabbix macro, without printing it.

Shared by snmp_probe.py and snmp_walk.py. The commands run in a temporary Alpine container
(net-snmp-tools, fping), so nothing is installed on the host. The community is passed through the
environment variable COMM; shell snippets reference it as "$COMM".
"""
import os
import subprocess

from zbx_api import global_macro

IMAGE = "alpine:3.22"
SETUP = "apk add -q --no-cache net-snmp-tools fping >/dev/null 2>&1\n"


def community_from_zabbix(api, macro="{$SNMP_COMMUNITY}"):
    """Community stored in a global Zabbix macro (text type)."""
    return global_macro(api, macro)


def run_netsnmp(script, community, env=None):
    """Run a shell snippet with net-snmp tools. Returns (returncode, stdout, stderr)."""
    variables = {"COMM": community, **(env or {})}
    process_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), **variables}
    env_args = [arg for name in variables for arg in ("-e", name)]
    result = subprocess.run(["docker", "run", "--rm", *env_args, IMAGE, "sh", "-c", SETUP + script],
                            capture_output=True, text=True, env=process_env, check=False)
    return result.returncode, result.stdout, result.stderr
