#!/usr/bin/env bash
# First-time TLS bootstrap for the nginx + certbot services.
#
#   1. puts a throw-away self-signed certificate in place so nginx can start,
#   2. starts nginx, requests the real Let's Encrypt certificate over HTTP-01 (webroot),
#   3. reloads nginx. Renewals afterwards are automatic (certbot + periodic nginx reload).
#
# Usage: ./deploy/init-letsencrypt.sh [--staging]
# Requires DOMAIN and LETSENCRYPT_EMAIL in .env, and DNS for DOMAIN pointing at this host.
set -euo pipefail
cd "$(dirname "$0")/.."

set -a; source .env; set +a
: "${DOMAIN:?set DOMAIN in .env}"
: "${LETSENCRYPT_EMAIL:?set LETSENCRYPT_EMAIL in .env}"
STAGING_ARG=""
[[ "${1:-}" == "--staging" ]] && STAGING_ARG="--staging"

live="/etc/letsencrypt/live/${DOMAIN}"

# Host directories mounted into containers must be writable by the app user (uid 1000).
mkdir -p data/socialdownload/cookies backups
chown -R 1000:1000 data 2>/dev/null || sudo chown -R 1000:1000 data

if docker compose run --rm --entrypoint sh certbot -c "test -s ${live}/fullchain.pem && ! test -e ${live}/.dummy"; then
  echo "A real certificate for ${DOMAIN} already exists; nothing to do."
  exit 0
fi

echo "### Creating a temporary self-signed certificate for ${DOMAIN}"
docker compose run --rm --entrypoint sh certbot -c "
  mkdir -p ${live} &&
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 -subj /CN=localhost \
    -keyout ${live}/privkey.pem -out ${live}/fullchain.pem &&
  touch ${live}/.dummy"

echo "### Starting nginx (and its dependencies)"
docker compose up -d nginx

echo "### Replacing it with a Let's Encrypt certificate"
docker compose run --rm --entrypoint certbot certbot certonly --webroot -w /var/www/certbot \
  ${STAGING_ARG} --email "${LETSENCRYPT_EMAIL}" --agree-tos --no-eff-email -d "${DOMAIN}" --cert-name "${DOMAIN}" --force-renewal
docker compose run --rm --entrypoint sh certbot -c "rm -f ${live}/.dummy"

echo "### Reloading nginx"
docker compose exec nginx nginx -s reload

echo "### Starting the full stack"
docker compose up -d
echo "Done. Webhooks will be served at https://${DOMAIN}/webhook/<bot-slug>"
