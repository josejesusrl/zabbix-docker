#!/bin/sh
# Run an agent script on the Zabbix server, from the local copy of this directory.
# The API token is read from stdin and forwarded to the script stdin: it never appears in
# arguments, environment or files. The scripts are copied to a private temporary directory
# on the server that is removed at the end.
#
# Usage:
#   printf '%s\n' "$TOKEN" | agents/scripts/run_remote.sh [-f FILE]... SCRIPT [ARGS...]
#     -f FILE   also upload FILE (e.g. a template YAML), referenced by its base name in ARGS
#   ZBX_SSH=user@host overrides the server (default jjrl@192.168.0.191)
set -eu

SERVER="${ZBX_SSH:-jjrl@192.168.0.191}"
DIR="$(cd "$(dirname "$0")" && pwd)"
SSH="ssh -o BatchMode=yes"

uploads=""
while [ "${1:-}" = "-f" ]; do
    [ -f "$2" ] || { echo "File not found: $2" >&2; exit 1; }
    uploads="$uploads $2"
    shift 2
done
[ $# -ge 1 ] || { sed -n '2,12p' "$0" >&2; exit 1; }
script="$1"
shift

# Quote arguments for the remote shell
quote() { printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"; }
args=""
for a in "$@"; do args="$args $(quote "$a")"; done

remote=$($SSH "$SERVER" 'mktemp -d /tmp/zbx-agent.XXXXXX' </dev/null)
trap '$SSH "$SERVER" "rm -rf $remote" </dev/null' EXIT
# shellcheck disable=SC2086
scp -q -o BatchMode=yes "$DIR"/*.py $uploads "$SERVER:$remote/" </dev/null
# stdin (token) goes only to this ssh call
$SSH "$SERVER" "cd $remote && python3 $(quote "$script")$args"
