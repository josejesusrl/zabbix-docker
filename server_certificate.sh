#!/bin/sh
# Self-signed TLS certificate of Zabbix web interface (origin certificate).
# Usage (as root, from anywhere):
#   ./server_certificate.sh selfsigned [DAYS]   create or replace it (default 3650 days) and recreate web container
# Public access goes through Cloudflare Tunnel: browsers get the Cloudflare edge certificate and
# cloudflared connects to nginx without verifying this one (docs/despliegue/acceso-externo.md).
# This certificate is seen only on direct LAN access (https://CERT_LAN_IP/), with a browser warning.
set -eu

cd "$(dirname "$0")"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root: sudo $0 $*" >&2
    exit 1
fi

. ./server.env
# LETSENCRYPT_DOMAIN: name used by server.env files created before Cloudflare Tunnel
CERT_DOMAIN="${CERT_DOMAIN:-${LETSENCRYPT_DOMAIN:-}}"
: "${CERT_DOMAIN:?CERT_DOMAIN is not set in server.env}"

COMPOSE="docker compose --env-file .env --env-file server.env"
WEB_SERVICE=zabbix-web-nginx-pgsql
# Mounted to /etc/ssl/nginx of web container (DATA_DIRECTORY from .env)
SSL_DIR=./zbx_env/etc/ssl/nginx
# Container user of Zabbix images
ZBX_UID=1997
ZBX_GID=1995

case "${1:-}" in
    selfsigned)
        days="${2:-3650}"
        san="DNS:${CERT_DOMAIN}"
        [ -n "${CERT_LAN_IP:-}" ] && san="${san},IP:${CERT_LAN_IP}"
        mkdir -p "$SSL_DIR"
        if [ ! -f "${SSL_DIR}/dhparam.pem" ]; then
            openssl dhparam -out "${SSL_DIR}/dhparam.pem" 2048
        fi
        openssl req -x509 -newkey rsa:2048 -nodes -days "$days" \
            -subj "/CN=${CERT_DOMAIN}" \
            -addext "subjectAltName=${san}" \
            -keyout "${SSL_DIR}/ssl.key" -out "${SSL_DIR}/ssl.crt"
        chown "${ZBX_UID}:${ZBX_GID}" "${SSL_DIR}/ssl.crt" "${SSL_DIR}/ssl.key" "${SSL_DIR}/dhparam.pem"
        chmod 644 "${SSL_DIR}/ssl.crt" "${SSL_DIR}/dhparam.pem"
        chmod 600 "${SSL_DIR}/ssl.key"
        # HTTPS virtual host is enabled by container entrypoint, recreate is required
        $COMPOSE up -d --force-recreate "$WEB_SERVICE"
        echo "Self-signed certificate installed for ${san}, valid ${days} days"
        ;;
    *)
        echo "Usage: $0 selfsigned [DAYS]" >&2
        exit 1
        ;;
esac
