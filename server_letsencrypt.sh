#!/bin/sh
# Let's Encrypt certificate for Zabbix web interface (HTTP-01 webroot challenge).
# Usage (as root, from anywhere):
#   ./server_letsencrypt.sh issue   first certificate, web stack must be running
#   ./server_letsencrypt.sh renew   renewal, run daily from cron
# Certbot runs from certbot/certbot image, challenges are served by
# zabbix-web-nginx-pgsql from ./letsencrypt/webroot (nginx/zabbix_http.conf).
set -eu

cd "$(dirname "$0")"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root: sudo $0 ${1:-}" >&2
    exit 1
fi

. ./server.env
: "${LETSENCRYPT_DOMAIN:?LETSENCRYPT_DOMAIN is not set in server.env}"
: "${LETSENCRYPT_EMAIL:?LETSENCRYPT_EMAIL is not set in server.env, run server_setup.sh}"

COMPOSE="docker compose --env-file .env --env-file server.env"
WEB_SERVICE=zabbix-web-nginx-pgsql
LE_DIR="$(pwd)/letsencrypt"
# Mounted to /etc/ssl/nginx of web container (DATA_DIRECTORY from .env)
SSL_DIR=./zbx_env/etc/ssl/nginx
# Container user of Zabbix images
ZBX_UID=1997
ZBX_GID=1995

certbot() {
    docker run --rm \
        -v "${LE_DIR}/etc:/etc/letsencrypt" \
        -v "${LE_DIR}/lib:/var/lib/letsencrypt" \
        -v "${LE_DIR}/webroot:/var/www/acme" \
        certbot/certbot "$@"
}

# Copies certificate to nginx SSL directory, returns 1 if it is unchanged
install_certs() {
    live="${LE_DIR}/etc/live/${LETSENCRYPT_DOMAIN}"

    mkdir -p "$SSL_DIR"
    if [ ! -f "${SSL_DIR}/dhparam.pem" ]; then
        openssl dhparam -out "${SSL_DIR}/dhparam.pem" 2048
    fi

    if cmp -s "${live}/fullchain.pem" "${SSL_DIR}/ssl.crt"; then
        return 1
    fi

    cp -L "${live}/fullchain.pem" "${SSL_DIR}/ssl.crt"
    cp -L "${live}/privkey.pem" "${SSL_DIR}/ssl.key"
    chown "${ZBX_UID}:${ZBX_GID}" "${SSL_DIR}/ssl.crt" "${SSL_DIR}/ssl.key" "${SSL_DIR}/dhparam.pem"
    chmod 644 "${SSL_DIR}/ssl.crt" "${SSL_DIR}/dhparam.pem"
    chmod 600 "${SSL_DIR}/ssl.key"
    return 0
}

case "${1:-}" in
    issue)
        mkdir -p "${LE_DIR}/webroot"
        certbot certonly --webroot -w /var/www/acme \
            -d "$LETSENCRYPT_DOMAIN" \
            --email "$LETSENCRYPT_EMAIL" --agree-tos --no-eff-email \
            --non-interactive --keep-until-expiring
        install_certs || true
        # HTTPS virtual host is enabled by container entrypoint, recreate is required
        $COMPOSE up -d --force-recreate "$WEB_SERVICE"
        echo "HTTPS enabled: https://${LETSENCRYPT_DOMAIN}/"
        ;;
    renew)
        certbot renew --webroot -w /var/www/acme --quiet
        if install_certs; then
            $COMPOSE exec -T "$WEB_SERVICE" nginx -s reload
            echo "Certificate renewed and nginx reloaded"
        fi
        ;;
    *)
        echo "Usage: $0 issue|renew" >&2
        exit 1
        ;;
esac
