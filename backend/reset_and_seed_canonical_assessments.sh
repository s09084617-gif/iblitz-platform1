#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONTAINER=iblitz-postgres
DB_USER=iblitz
DB_NAME=iblitz

cat <<'SQL' | sudo docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME"
BEGIN;
TRUNCATE TABLE outcomes, episodes, assessments, users RESTART IDENTITY CASCADE;
COMMIT;
SQL

echo "Database reset complete. Reseeding canonical assessments..."
./seed_canonical_assessments.sh

echo "Reset and reseed complete."

echo "\nSummary report:"
sudo docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" <<'SQL'
SELECT
  (SELECT count(*) FROM users) AS users,
  (SELECT count(*) FROM assessments) AS assessments,
  (SELECT count(*) FROM episodes WHERE started_at IS NOT NULL) AS episodes_started,
  (SELECT count(*) FROM episodes WHERE completed_at IS NOT NULL) AS episodes_completed,
  ROUND(100.0 * (SELECT count(*) FROM episodes WHERE completed_at IS NOT NULL) / NULLIF((SELECT count(*) FROM episodes WHERE started_at IS NOT NULL), 0), 2) AS completion_rate_pct,
  (SELECT count(*) FROM outcomes) AS outcomes,
  ROUND(100.0 * (SELECT count(DISTINCT episode_id) FROM outcomes) / NULLIF((SELECT count(*) FROM episodes WHERE completed_at IS NOT NULL), 0), 2) AS outcome_capture_rate_pct;
SQL
