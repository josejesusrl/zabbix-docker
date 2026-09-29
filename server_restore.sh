#!/bin/sh
# Restore Zabbix from server_backup.sh files, or migrate the database of a previous deployment.
# Usage (as root, from anywhere):
#   ./server_restore.sh [--replace-db] [--config zabbix-config-<date>.tar.gz] [--db zabbix-db-<date>.dump]
#
#   --config  restores secrets and local data not stored in git: PostgreSQL credentials, server.env,
#             Cloudflare Tunnel token, TLS certificate, MIBs, trap community (snmptrapd.conf).
#             Versioned files (nginx/, zabbix_agentd.d/, env_vars/.env_*) come from git, not from the archive.
#   --db      restores a PostgreSQL custom format dump (pg_dump -Fc) and starts the whole stack.
#             Zabbix server upgrades the schema on start if the dump comes from an older Zabbix version.
#   --replace-db  allow restoring over an existing database in ./zabbix-db-data (current data is lost,
#             take a backup first).
#
# Order on a new server: git clone -> sudo ./server_restore.sh --config ... --db ... -> ./server_setup.sh
set -eu

cd "$(dirname "$0")"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root: sudo $0 $*" >&2
    exit 1
fi

REPLACE_DB=0
CONFIG=""
DUMP=""
while [ $# -gt 0 ]; do
    case "$1" in
        --replace-db) REPLACE_DB=1 ;;
        --config) CONFIG="$2"; shift ;;
        --db) DUMP="$2"; shift ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
    shift
done
if [ -z "$CONFIG" ] && [ -z "$DUMP" ]; then
    echo "Usage: $0 [--replace-db] [--config ARCHIVE] [--db DUMP]" >&2
    exit 1
fi
for f in $CONFIG $DUMP; do
    [ -f "$f" ] || { echo "File not found: $f" >&2; exit 1; }
done

# Repository owner, git metadata must not become owned by root
OWNER=$(stat -c %U .git)

if [ -n "$CONFIG" ]; then
    # Only non-versioned paths are restored from the archive
    wanted="env_vars/.POSTGRES_USER env_vars/.POSTGRES_PASSWORD env_vars/.CLOUDFLARE_TUNNEL_TOKEN server.env zbx_env snmptraps/snmptrapd.conf"
    members=""
    for p in $wanted; do
        if tar -tzf "$CONFIG" | grep -q "^${p}\(/\|$\)"; then
            members="$members $p"
        fi
    done
    echo "Restoring from $CONFIG:$members"
    # shellcheck disable=SC2086
    tar -xzpf "$CONFIG" $members
    sudo -u "$OWNER" git update-index --skip-worktree env_vars/.POSTGRES_PASSWORD
    for p in /zabbix-db-data/ /server.env /backups/ /snmptraps/snmptrapd.conf /env_vars/.CLOUDFLARE_TUNNEL_TOKEN; do
        grep -qxF "$p" .git/info/exclude 2>/dev/null || echo "$p" >> .git/info/exclude
    done
fi

if [ -n "$DUMP" ]; then
    [ -f server.env ] || { echo "server.env is missing: restore --config first or copy server.env.example" >&2; exit 1; }
    COMPOSE="docker compose --env-file .env --env-file server.env"
    mkdir -p zabbix-db-data

    if [ -n "$(ls -A zabbix-db-data)" ] && [ "$REPLACE_DB" -ne 1 ]; then
        echo "./zabbix-db-data already contains a database. Take a backup and use --replace-db to overwrite it." >&2
        exit 1
    fi

    # Nothing may write to the database while it is restored
    $COMPOSE stop zabbix-server zabbix-web-nginx-pgsql zabbix-web-service 2>/dev/null || true
    $COMPOSE up -d postgres-server
    echo "Waiting for PostgreSQL..."
    i=0
    until [ "$(docker inspect --format '{{.State.Health.Status}}' "$($COMPOSE ps -q postgres-server)")" = "healthy" ]; do
        i=$((i + 1))
        [ "$i" -gt 60 ] && { echo "PostgreSQL is not healthy after 5 minutes" >&2; exit 1; }
        sleep 5
    done

    echo "Restoring database from $DUMP"
    # --clean drops objects of the same name first; owner and grants are skipped (single Zabbix user,
    # a dump from another deployment may reference roles that do not exist here)
    $COMPOSE exec -T postgres-server \
        sh -c 'pg_restore -U "$(cat /run/secrets/POSTGRES_USER)" -d "$POSTGRES_DB" --clean --if-exists --no-owner --no-privileges --exit-on-error' \
        < "$DUMP"

    $COMPOSE up -d
    echo "Stack started. Check: $COMPOSE ps ; $COMPOSE logs -f zabbix-server"
fi
