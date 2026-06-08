#!/usr/bin/env bash
set -euo pipefail

CONTAINER=iblitz-postgres
DB_USER=iblitz
DB_NAME=iblitz

cat <<'SQL' | sudo docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME"
BEGIN;

WITH new_users AS (
  INSERT INTO users (username, email, hashed_password)
  SELECT 'testuser' || i, 'testuser' || i || '@example.com', 'password'
  FROM generate_series(1, 10) AS s(i)
  RETURNING id, username
),
new_assessments AS (
  INSERT INTO assessments (user_id, title, description, status)
  SELECT id,
         'Canonical Assessment for ' || username,
         'Canonical assessment flow for ' || username,
         'completed'
  FROM new_users
  RETURNING id AS assessment_id, user_id
),
episodes_insert AS (
  SELECT assessment_id, 1 AS sequence, 'Onboarding' AS name,
         now() - interval '30 minutes' AS started_at,
         now() - interval '20 minutes' AS completed_at
  FROM new_assessments
  UNION ALL
  SELECT assessment_id, 2 AS sequence, 'Core Flow' AS name,
         now() - interval '19 minutes' AS started_at,
         now() - interval '10 minutes' AS completed_at
  FROM new_assessments
  UNION ALL
  SELECT assessment_id, 3 AS sequence, 'Wrap-up' AS name,
         now() - interval '9 minutes' AS started_at,
         NULL AS completed_at
  FROM new_assessments
)
INSERT INTO episodes (assessment_id, name, sequence, started_at, completed_at)
SELECT assessment_id, name, sequence, started_at, completed_at
FROM episodes_insert;

INSERT INTO outcomes (episode_id, name, result, score)
SELECT e.id,
       'Outcome for ' || e.name,
       jsonb_build_object('status', 'captured', 'episode', e.name),
       1.0
FROM episodes e
WHERE e.completed_at IS NOT NULL;

COMMIT;
SQL

sudo docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" <<'SQL'
SELECT
  COUNT(*) FILTER (WHERE started_at IS NOT NULL) AS episodes_started,
  COUNT(*) FILTER (WHERE completed_at IS NOT NULL) AS episodes_completed,
  ROUND(100.0 * COUNT(*) FILTER (WHERE completed_at IS NOT NULL) / NULLIF(COUNT(*) FILTER (WHERE started_at IS NOT NULL), 0), 2) AS completion_rate_pct,
  COUNT(DISTINCT o.episode_id) AS episodes_with_outcome,
  ROUND(100.0 * COUNT(DISTINCT o.episode_id) / NULLIF(COUNT(*) FILTER (WHERE completed_at IS NOT NULL), 0), 2) AS outcome_capture_rate_pct
FROM episodes e
LEFT JOIN outcomes o ON o.episode_id = e.id;
SQL