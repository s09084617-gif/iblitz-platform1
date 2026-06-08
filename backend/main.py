from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .generate_episode_api import router as engine_router
from .models import Assessment, Episode, Outcome, User, Workout

try:
    Base.metadata.create_all(bind=engine)
except Exception as exc:
    print(f"Warning: could not initialize database: {exc}")

app = FastAPI()
app.include_router(engine_router, prefix="/engine", tags=["engine"])


@app.get("/")
async def read_root():
    return {"message": "Hello from iblitz backend!"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(db: Session = Depends(get_db)):
    user_count = db.query(User).count()
    assessment_count = db.query(Assessment).count()
    episode_count = db.query(Episode).count()
    outcome_count = db.query(Outcome).count()
    workout_count = db.query(Workout).count()

    html = f"""
    <html>
      <head>
        <title>iblitz Admin Dashboard</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f7f8fb; }}
          h1 {{ color: #1f2937; }}
          .card {{ background: white; border-radius: 12px; padding: 1rem 1.5rem; margin: .75rem 0; box-shadow: 0 10px 30px rgba(15,23,42,.08); }}
          .card p {{ margin: .25rem 0; color: #4b5563; }}
          a {{ color: #2563eb; text-decoration: none; }}
        </style>
      </head>
      <body>
        <h1>iblitz Admin Dashboard</h1>
        <div class="card"><strong>Users</strong><p>{user_count}</p></div>
        <div class="card"><strong>Assessments</strong><p>{assessment_count}</p></div>
        <div class="card"><strong>Episodes</strong><p>{episode_count}</p></div>
        <div class="card"><strong>Outcomes</strong><p>{outcome_count}</p></div>
        <div class="card"><strong>Workouts</strong><p>{workout_count}</p></div>
        <div class="card">
          <strong>Useful API links</strong>
          <p><a href="/engine/episodes">/engine/episodes</a></p>
          <p><a href="/engine/workouts">/engine/workouts</a></p>
          <p><a href="/docs">/docs</a></p>
        </div>
      </body>
    </html>
    """
    return html
