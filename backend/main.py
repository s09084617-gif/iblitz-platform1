from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from .auth import get_current_admin_user, router as auth_router
from .database import Base, engine, get_db
from .generate_episode_api import UnsupportedCase, router as engine_router
from .models import Assessment, Episode, EpisodeFailure, Outcome, User, Workout

try:
    Base.metadata.create_all(bind=engine)
except Exception as exc:
    print(f"Warning: could not initialize database: {exc}")

app = FastAPI()
app.include_router(auth_router)
app.include_router(engine_router, prefix="/engine", tags=["engine"])


@app.exception_handler(UnsupportedCase)
async def unsupported_case_handler(request: Request, exc: UnsupportedCase):
    return JSONResponse(
        status_code=422,
        content={
            "status": "unsupported_case",
            "stage": exc.stage,
            "reason": exc.reason,
            "details": exc.details,
        },
    )


@app.get("/")
async def read_root():
    return {"message": "Hello from iblitz backend!"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    current_user=Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    user_count = db.query(User).count()
    assessment_count = db.query(Assessment).count()
    episodes_started = db.query(Episode).filter(Episode.started_at.is_not(None)).count()
    episodes_completed = db.query(Episode).filter(Episode.completed_at.is_not(None)).count()
    outcome_count = db.query(Outcome).count()
    workout_count = db.query(Workout).count()
    unsupported_cases = db.query(EpisodeFailure).count()

    completion_rate = (
        round(100.0 * episodes_completed / episodes_started, 2)
        if episodes_started
        else 0.0
    )
    outcome_capture_rate = (
        round(
            100.0 * db.query(func.count(func.distinct(Outcome.episode_id))).scalar() / episodes_completed,
            2,
        )
        if episodes_completed
        else 0.0
    )

    top_programs = [
        f"{row[0]} ({row[1]})"
        for row in db.query(Outcome.result["program"].astext, func.count(Outcome.id))
        .group_by(Outcome.result["program"].astext)
        .order_by(func.count(Outcome.id).desc())
        .limit(5)
        .all()
    ]
    top_restrictions = [
        f"{row[0]} ({row[1]})"
        for row in db.query(Outcome.result["restriction"].astext, func.count(Outcome.id))
        .filter(Outcome.result["restriction"].astext.is_not(None))
        .group_by(Outcome.result["restriction"].astext)
        .order_by(func.count(Outcome.id).desc())
        .limit(5)
        .all()
    ]
    top_goals = [
        f"{row[0]} ({row[1]})"
        for row in db.query(Outcome.result["goal"].astext, func.count(Outcome.id))
        .filter(Outcome.result["goal"].astext.is_not(None))
        .group_by(Outcome.result["goal"].astext)
        .order_by(func.count(Outcome.id).desc())
        .limit(5)
        .all()
    ]

    html = f"""
    <html>
      <head>
        <title>iblitz Admin Dashboard</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f7f8fb; }}
          h1 {{ color: #1f2937; }}
          .card {{ background: white; border-radius: 12px; padding: 1rem 1.5rem; margin: .75rem 0; box-shadow: 0 10px 30px rgba(15,23,42,.08); }}
          .card p {{ margin: .25rem 0; color: #4b5563; }}
          .card ul {{ margin: .25rem 0 0 1rem; color: #4b5563; }}
          a {{ color: #2563eb; text-decoration: none; }}
        </style>
      </head>
      <body>
        <h1>iblitz Admin Dashboard</h1>
        <div class="card"><strong>Users</strong><p>{user_count}</p></div>
        <div class="card"><strong>Assessments</strong><p>{assessment_count}</p></div>
        <div class="card"><strong>Episodes Started</strong><p>{episodes_started}</p></div>
        <div class="card"><strong>Episodes Completed</strong><p>{episodes_completed}</p></div>
        <div class="card"><strong>Completion Rate</strong><p>{completion_rate}%</p></div>
        <div class="card"><strong>Outcomes</strong><p>{outcome_count}</p></div>
        <div class="card"><strong>Outcome Capture Rate</strong><p>{outcome_capture_rate}%</p></div>
        <div class="card"><strong>Unsupported Cases</strong><p>{unsupported_cases}</p></div>
        <div class="card"><strong>Top Programs</strong><ul>{''.join(f'<li>{item}</li>' for item in top_programs)}</ul></div>
        <div class="card"><strong>Top Restrictions</strong><ul>{''.join(f'<li>{item}</li>' for item in top_restrictions)}</ul></div>
        <div class="card"><strong>Top Goals</strong><ul>{''.join(f'<li>{item}</li>' for item in top_goals)}</ul></div>
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
