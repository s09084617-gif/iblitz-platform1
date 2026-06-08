# iblitz-platform1

A backend for the iblitz recommendation and workout system.

## Backend structure

- `backend/main.py` — FastAPI application entrypoint
- `backend/generate_episode_api.py` — recommendation, episode, workout, and listing endpoints
- `backend/database.py` — SQLAlchemy database engine and session management
- `backend/models.py` — ORM schema for users, assessments, episodes, outcomes, workouts
- `backend/schemas.py` — Pydantic request/response schemas
- `backend/schema_v3.sql` — PostgreSQL schema bootstrap SQL
- `backend/setup_ec2_postgres.sh` — Docker-based PostgreSQL setup script
- `backend/seed_reference_data.sh` — seed program, exercise, restriction, and rule reference data
- `backend/reset_and_seed_canonical_assessments.sh` — reset and reseed canonical test data
- `backend/seed_canonical_assessments.sh` — create 10 test users, episodes, outcomes
- `backend/run_dev.sh` — local FastAPI startup helper

## Requirements

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Running locally

1. Start the PostgreSQL container:

```bash
cd backend
sudo chmod +x setup_ec2_postgres.sh
sudo ./setup_ec2_postgres.sh
```

2. Start the backend:

```bash
cd backend
chmod +x run_dev.sh
./run_dev.sh
```

3. Open the API docs:

```
http://127.0.0.1:8000/docs
```

4. Open the admin dashboard:

```
http://127.0.0.1:8000/admin
```

## API Endpoints

- `GET /` — root
- `GET /health` — health check
- `GET /docs` — OpenAPI docs
- `POST /engine/generate-episode` — generate a recommendation episode and persist assessment/episode/outcome
- `GET /engine/episodes` — list stored episodes with outcomes
- `POST /engine/generate-workout` — generate and persist a workout plan
- `GET /engine/workouts` — list stored workouts
- `GET /admin` — admin dashboard and counts

## Notes

- The database URL defaults to `postgresql://iblitz:iblitz123@172.17.0.2:5432/iblitz`.
- If host port forwarding is unavailable in this environment, use the Docker container directly and connect from the app inside the same host.
