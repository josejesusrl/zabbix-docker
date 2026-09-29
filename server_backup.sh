#!/bin/sh
# Backup of Zabbix database and deployment configuration to ./backups.
# Usage (as root, from anywhere): ./server_backup.sh
#   zabbix-db-<date>.dump        PostgreSQL custom format dump (consistent, taken while running)
#   zabbix-config-<date>.tar.gz  secrets, server.env, certificates, traps and agent configuration
# Backups older than BACKUP_RETENTION_DAYS (server.env) are removed.
# Copy ./backups to another machine, local copies do not protect against disk loss.
#
# Restore: server_restore.sh --config backups/zabbix-config-<date>.tar.gz --db backups/zabbix-db-<date>.dump
# (see SERVER_DEPLOY.md, "Restauración").
set -eu

cd "$(dirname "$0")"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root: sudo $0" >&2
    exit 1
fi

. ./server.env

COMPOSE="docker compose --env-file .env --env-file server.env"
DEST=./backups
STAMP=$(date +%F_%H%M%S)
DB_FILE="${DEST}/zabbix-db-${STAMP}.dump"
CONFIG_FILE="${DEST}/zabbix-config-${STAMP}.tar.gz"

umask 077
mkdir -p "$DEST"
trap 'rm -f "$DB_FILE.tmp" "$CONFIG_FILE.tmp"' EXIT

# Local socket connections are trusted inside postgres container
$COMPOSE exec -T postgres-server \
    sh -c 'pg_dump -U "$(cat /run/secrets/POSTGRES_USER)" -d "$POSTGRES_DB" -Fc' > "$DB_FILE.tmp"
mv "$DB_FILE.tmp" "$DB_FILE"

config_paths=""
for p in env_vars server.env zbx_env letsencrypt snmptraps nginx zabbix_agentd.d alertscripts externalscripts; do
    [ -e "$p" ] && config_paths="$config_paths $p"
done
# shellcheck disable=SC2086
tar -czf "$CONFIG_FILE.tmp" $config_paths
mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"

find "$DEST" -maxdepth 1 -name 'zabbix-*' -type f -mtime +"${BACKUP_RETENTION_DAYS:-7}" -delete

echo "Backup created: $DB_FILE $CONFIG_FILE"
