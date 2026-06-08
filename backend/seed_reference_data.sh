#!/usr/bin/env bash
set -euo pipefail

CONTAINER=iblitz-postgres
DB_USER=iblitz
DB_NAME=iblitz

cat <<'SQL' | sudo docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME"
BEGIN;

INSERT INTO programs (code, name, description)
VALUES
  ('3_day_full_body', '3 Day Full Body', 'Balanced full-body program for lower muscle mass or restriction adaptation'),
  ('4_day_split', '4 Day Split', 'Traditional 4-day upper/lower split');

INSERT INTO exercises (code, name, category, equipment, primary_muscle, secondary_muscle)
VALUES
  ('squat', 'Squat', 'Strength', 'Barbell', 'Quadriceps', 'Glutes'),
  ('bench_press', 'Bench Press', 'Strength', 'Barbell', 'Chest', 'Triceps'),
  ('bent_over_row', 'Bent-over Row', 'Strength', 'Barbell', 'Back', 'Biceps'),
  ('shoulder_press', 'Shoulder Press', 'Strength', 'Barbell', 'Shoulders', 'Triceps'),
  ('plank', 'Plank', 'Core', 'Bodyweight', 'Core', NULL),
  ('deadlift', 'Deadlift', 'Strength', 'Barbell', 'Back', 'Hamstrings'),
  ('pull_up', 'Pull-up', 'Strength', 'Bodyweight', 'Back', 'Biceps'),
  ('face_pull', 'Face Pull', 'Strength', 'Cable', 'Shoulders', 'Upper Back'),
  ('front_squat', 'Front Squat', 'Strength', 'Barbell', 'Quadriceps', 'Core'),
  ('romanian_deadlift', 'Romanian Deadlift', 'Strength', 'Barbell', 'Hamstrings', 'Glutes'),
  ('lunges', 'Lunges', 'Strength', 'Bodyweight', 'Quadriceps', 'Glutes'),
  ('incline_bench_press', 'Incline Bench Press', 'Strength', 'Barbell', 'Chest', 'Shoulders'),
  ('barbell_row', 'Barbell Row', 'Strength', 'Barbell', 'Back', 'Biceps'),
  ('lat_pulldown', 'Lat Pulldown', 'Strength', 'Cable', 'Back', 'Biceps'),
  ('glute_bridge', 'Glute Bridge', 'Strength', 'Bodyweight', 'Glutes', 'Hamstrings');

INSERT INTO restrictions (code, name, description)
VALUES
  ('KNEE_PAIN', 'Knee Pain', 'Exercise substitutions and adaptations for knee discomfort');

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Full Body', 1, 3, '8-12', NULL
FROM programs p, exercises e
WHERE p.code = '3_day_full_body' AND e.code = 'squat';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Full Body', 2, 3, '8-12', NULL
FROM programs p, exercises e
WHERE p.code = '3_day_full_body' AND e.code = 'bench_press';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Full Body', 3, 3, '8-12', NULL
FROM programs p, exercises e
WHERE p.code = '3_day_full_body' AND e.code = 'bent_over_row';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Full Body', 4, 3, '8-12', NULL
FROM programs p, exercises e
WHERE p.code = '3_day_full_body' AND e.code = 'shoulder_press';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Full Body', 5, 3, NULL, jsonb_build_object('duration', '30s')
FROM programs p, exercises e
WHERE p.code = '3_day_full_body' AND e.code = 'plank';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Push', 1, 4, '6-10', NULL
FROM programs p, exercises e
WHERE p.code = '4_day_split' AND e.code = 'bench_press';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Push', 2, 3, '8-12', NULL
FROM programs p, exercises e
WHERE p.code = '4_day_split' AND e.code = 'shoulder_press';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Push', 3, 3, '10-15', NULL
FROM programs p, exercises e
WHERE p.code = '4_day_split' AND e.code = 'face_pull';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Pull', 1, 3, '5-8', NULL
FROM programs p, exercises e
WHERE p.code = '4_day_split' AND e.code = 'deadlift';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Pull', 2, 3, '6-12', NULL
FROM programs p, exercises e
WHERE p.code = '4_day_split' AND e.code = 'pull_up';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Pull', 3, 3, '12-15', NULL
FROM programs p, exercises e
WHERE p.code = '4_day_split' AND e.code = 'lat_pulldown';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Legs', 1, 3, '6-10', NULL
FROM programs p, exercises e
WHERE p.code = '4_day_split' AND e.code = 'front_squat';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Legs', 2, 3, '8-12', NULL
FROM programs p, exercises e
WHERE p.code = '4_day_split' AND e.code = 'romanian_deadlift';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Legs', 3, 3, '10-12', NULL
FROM programs p, exercises e
WHERE p.code = '4_day_split' AND e.code = 'lunges';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Upper', 1, 3, '8-12', NULL
FROM programs p, exercises e
WHERE p.code = '4_day_split' AND e.code = 'incline_bench_press';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Upper', 2, 3, '8-12', NULL
FROM programs p, exercises e
WHERE p.code = '4_day_split' AND e.code = 'barbell_row';

INSERT INTO program_exercise_mappings (program_id, exercise_id, day, sequence, sets, reps, notes)
SELECT p.id, e.id, 'Upper', 3, 3, '10-15', NULL
FROM programs p, exercises e
WHERE p.code = '4_day_split' AND e.code = 'lat_pulldown';

INSERT INTO exercise_substitutions (restriction_id, exercise_id, substitute_exercise_id, reason)
SELECT r.id, e.id, s.id, 'Avoid deep knee flexion'
FROM restrictions r,
     exercises e,
     exercises s
WHERE r.code = 'KNEE_PAIN'
  AND e.code = 'squat'
  AND s.code = 'glute_bridge';

INSERT INTO exercise_substitutions (restriction_id, exercise_id, substitute_exercise_id, reason)
SELECT r.id, e.id, s.id, 'Avoid deep knee flexion'
FROM restrictions r,
     exercises e,
     exercises s
WHERE r.code = 'KNEE_PAIN'
  AND e.code = 'lunges'
  AND s.code = 'glute_bridge';

INSERT INTO classification_rules (pbf_min, pbf_max, smm_key, classification, priority, active)
VALUES
  (30, NULL, 'low', 'obese_low_muscle', 100, TRUE),
  (30, NULL, NULL, 'obese', 90, TRUE),
  (25, 30, 'low', 'overweight_low_muscle', 80, TRUE),
  (25, 30, NULL, 'overweight', 70, TRUE),
  (0, 25, 'low', 'normal_low_muscle', 60, TRUE),
  (0, 25, NULL, 'normal', 50, TRUE);

INSERT INTO recommendation_rules (classification, goal_key, recommendation, priority, active)
VALUES
  ('obese_low_muscle', 'fat_loss', 'fat_loss_muscle_preservation', 100, TRUE),
  ('obese_low_muscle', NULL, 'fat_loss_muscle_preservation', 90, TRUE),
  ('obese', 'fat_loss', 'fat_loss', 100, TRUE),
  ('overweight', 'fat_loss', 'fat_loss', 90, TRUE),
  ('normal', 'muscle_gain', 'muscle_gain', 90, TRUE),
  ('normal', 'maintenance', 'maintenance', 80, TRUE),
  ('normal', NULL, 'general_fitness', 50, TRUE);

INSERT INTO program_rules (classification, restriction_code, program_code, priority, active)
VALUES
  ('obese_low_muscle', 'KNEE_PAIN', '3_day_full_body', 100, TRUE),
  ('obese_low_muscle', NULL, '3_day_full_body', 90, TRUE),
  ('overweight_low_muscle', NULL, '3_day_full_body', 80, TRUE),
  ('obese', NULL, '4_day_split', 70, TRUE),
  ('normal', NULL, '4_day_split', 60, TRUE);

COMMIT;
SQL

echo "Reference data seeded into $DB_NAME."
