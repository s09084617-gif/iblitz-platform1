#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ $(id -u) -ne 0 ]]; then
  echo "This script must be run as root or with sudo."
  exit 1
fi

echo "Installing Docker..."
apt-get update
apt-get install -y docker.io

if command -v systemctl >/dev/null 2>&1; then
  systemctl enable --now docker
fi

echo "Pulling PostgreSQL image..."
docker pull postgres:16

echo "Removing existing container if present..."
docker rm -f iblitz-postgres 2>/dev/null || true

echo "Starting PostgreSQL container..."
if [[ ! -x /usr/libexec/docker/docker-proxy ]]; then
  echo "docker-proxy not available; using host networking for PostgreSQL"
  NETWORK_ARGS="--network host"
else
  NETWORK_ARGS="-p 5432:5432"
fi

docker run -d \
  --name iblitz-postgres \
  --restart unless-stopped \
  -e POSTGRES_USER=iblitz \
  -e POSTGRES_PASSWORD=iblitz123 \
  -e POSTGRES_DB=iblitz \
  $NETWORK_ARGS \
  postgres:16

echo "Waiting for PostgreSQL to become ready..."
for i in {1..30}; do
  if docker exec iblitz-postgres pg_isready -U iblitz >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "Copying schema file into container..."
docker cp schema_v3.sql iblitz-postgres:/tmp/schema_v3.sql

echo "Applying database schema..."
docker exec -i iblitz-postgres psql -U iblitz -d iblitz -f /tmp/schema_v3.sql

echo "PostgreSQL setup complete."

echo "Database summary:"
docker exec -i iblitz-postgres psql -U iblitz -d iblitz <<'SQL'
SELECT
  (SELECT count(*) FROM users) AS users,
  (SELECT count(*) FROM assessments) AS assessments,
  (SELECT count(*) FROM episodes) AS episodes,
  (SELECT count(*) FROM outcomes) AS outcomes;
SQL
