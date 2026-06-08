from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .models import Assessment, Episode, Outcome, User, Workout
from .schemas import (
    EpisodeResponse,
    GenerateEpisodeRequest,
    GenerateEpisodeResponse,
    GenerateWorkoutRequest,
    WorkoutResponse,
)

router = APIRouter()


def determine_classification(pbf: float, smm: str) -> str:
    smm_key = smm.lower().strip()
    if pbf >= 30 and smm_key == "low":
        return "obese_low_muscle"
    if pbf >= 30:
        return "obese"
    if pbf >= 25 and smm_key == "low":
        return "overweight_low_muscle"
    if pbf >= 25:
        return "overweight"
    if smm_key == "low":
        return "normal_low_muscle"
    return "normal"


def determine_recommendation(classification: str, goal: str) -> str:
    goal_key = goal.lower().strip()
    if goal_key == "fat_loss":
        if "low_muscle" in classification:
            return "fat_loss_muscle_preservation"
        return "fat_loss"
    if goal_key == "muscle_gain":
        return "muscle_gain"
    if goal_key == "maintenance":
        return "maintenance"
    return "general_fitness"


def determine_program(classification: str, restriction: Optional[str]) -> str:
    restriction_key = restriction.upper().strip() if restriction else ""
    if restriction_key == "KNEE_PAIN":
        return "3_day_full_body"
    if "low_muscle" in classification:
        return "3_day_full_body"
    return "4_day_split"


def get_or_create_user(db: Session, user_id: Optional[int], username: Optional[str]) -> User:
    if user_id is not None:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    if username:
        username_key = username.strip()
        user = db.query(User).filter(User.username == username_key).first()
        if user:
            return user

        user = User(
            username=username_key,
            email=f"{username_key}@example.com",
            hashed_password="default_password",
            is_active=True,
        )
        db.add(user)
        db.flush()
        return user

    user = db.query(User).filter(User.username == "anonymous").first()
    if user:
        return user

    user = User(
        username="anonymous",
        email="anonymous@example.com",
        hashed_password="default_password",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def create_assessment(db: Session, user: User, title: str, description: str) -> Assessment:
    assessment = Assessment(
        user_id=user.id,
        title=title,
        description=description,
        status="completed",
    )
    db.add(assessment)
    db.flush()
    return assessment


def create_episode(db: Session, assessment: Assessment, program: str) -> Episode:
    episode = Episode(
        assessment_id=assessment.id,
        name=f"{program} Episode",
        sequence=1,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    db.add(episode)
    db.flush()
    return episode


def create_outcome(db: Session, episode: Episode, classification: str, recommendation: str, program: str) -> Outcome:
    outcome = Outcome(
        episode_id=episode.id,
        name="generated_episode",
        result={
            "classification": classification,
            "recommendation": recommendation,
            "program": program,
        },
        score=1.0,
    )
    db.add(outcome)
    return outcome


def generate_workout_details(program: str, goal: str, restriction: Optional[str]) -> dict:
    program_key = program.lower().strip()
    restriction_key = restriction.upper().strip() if restriction else ""

    if "3_day_full_body" in program_key:
        exercises = [
            {"name": "Squat", "sets": 3, "reps": "8-12"},
            {"name": "Bench Press", "sets": 3, "reps": "8-12"},
            {"name": "Bent-over Row", "sets": 3, "reps": "8-12"},
            {"name": "Shoulder Press", "sets": 3, "reps": "8-12"},
            {"name": "Plank", "sets": 3, "duration": "30s"},
        ]
    elif "4_day_split" in program_key:
        exercises = [
            {"day": "Push", "movements": [
                {"name": "Bench Press", "sets": 4, "reps": "6-10"},
                {"name": "Overhead Press", "sets": 3, "reps": "8-12"},
                {"name": "Triceps Dip", "sets": 3, "reps": "10-15"},
            ]},
            {"day": "Pull", "movements": [
                {"name": "Deadlift", "sets": 3, "reps": "5-8"},
                {"name": "Pull-up", "sets": 3, "reps": "6-12"},
                {"name": "Face Pull", "sets": 3, "reps": "12-15"},
            ]},
            {"day": "Legs", "movements": [
                {"name": "Front Squat", "sets": 3, "reps": "6-10"},
                {"name": "Romanian Deadlift", "sets": 3, "reps": "8-12"},
                {"name": "Lunges", "sets": 3, "reps": "10-12"},
            ]},
            {"day": "Upper", "movements": [
                {"name": "Incline Bench Press", "sets": 3, "reps": "8-12"},
                {"name": "Barbell Row", "sets": 3, "reps": "8-12"},
                {"name": "Lat Pulldown", "sets": 3, "reps": "10-15"},
            ]},
        ]
    else:
        exercises = [
            {"name": "Goblet Squat", "sets": 3, "reps": "10-15"},
            {"name": "Push-up", "sets": 3, "reps": "12-20"},
            {"name": "Dumbbell Row", "sets": 3, "reps": "10-15"},
            {"name": "Lunge", "sets": 3, "reps": "10-12"},
            {"name": "Plank", "sets": 3, "duration": "30s"},
        ]

    if restriction_key == "KNEE_PAIN":
        exercises.append({"name": "Glute Bridge", "sets": 3, "reps": "12-15"})
        exercises = [e for e in exercises if e["name"] not in ["Lunge", "Squat", "Front Squat"]]

    return {
        "program": program,
        "goal": goal,
        "restriction": restriction,
        "workouts": exercises,
    }


def create_workout(db: Session, user: Optional[User], episode: Optional[Episode], program: str, details: dict) -> Workout:
    workout = Workout(
        user_id=user.id if user else None,
        episode_id=episode.id if episode else None,
        program=program,
        details=details,
    )
    db.add(workout)
    db.flush()
    return workout


@router.post(
    "/generate-workout",
    response_model=WorkoutResponse,
    summary="Generate a workout plan",
)
async def generate_workout(request: GenerateWorkoutRequest, db: Session = Depends(get_db)):
    user = None
    episode = None

    if request.user_id is not None or request.username is not None:
        user = get_or_create_user(db, request.user_id, request.username)

    if request.episode_id is not None:
        episode = db.get(Episode, request.episode_id)
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

    details = generate_workout_details(request.program, request.goal, request.restriction)
    workout = create_workout(db, user, episode, request.program, details)

    db.commit()
    db.refresh(workout)

    return WorkoutResponse(
        workout_id=workout.id,
        user_id=workout.user_id,
        episode_id=workout.episode_id,
        program=workout.program,
        details=workout.details,
    )


@router.post(
    "/generate-episode",
    response_model=GenerateEpisodeResponse,
    summary="Generate an episode recommendation",
)
async def generate_episode(request: GenerateEpisodeRequest, db: Session = Depends(get_db)):
    classification = determine_classification(request.pbf, request.smm)
    recommendation = determine_recommendation(classification, request.goal)
    program = determine_program(classification, request.restriction)

    user = get_or_create_user(db, request.user_id, request.username)
    assessment_title = request.assessment_title or f"{request.goal.capitalize()} Assessment"
    assessment_description = f"Generated assessment for {user.username}"
    assessment = create_assessment(db, user, assessment_title, assessment_description)
    episode = create_episode(db, assessment, program)
    create_outcome(db, episode, classification, recommendation, program)

    db.commit()
    db.refresh(episode)
    db.refresh(assessment)

    return GenerateEpisodeResponse(
        classification=classification,
        recommendation=recommendation,
        program=program,
        episode_id=episode.id,
        assessment_id=assessment.id,
    )


@router.get(
    "/workouts",
    response_model=list[WorkoutResponse],
    summary="List stored workouts",
)
async def list_workouts(
    user_id: Optional[int] = None,
    episode_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Workout)

    if user_id is not None:
        query = query.filter(Workout.user_id == user_id)
    if episode_id is not None:
        query = query.filter(Workout.episode_id == episode_id)

    workouts = query.order_by(Workout.created_at.desc()).limit(limit).all()
    return workouts


@router.get(
    "/episodes",
    response_model=list[EpisodeResponse],
    summary="List stored episodes with outcomes",
)
async def list_episodes(
    user_id: Optional[int] = None,
    completed: Optional[bool] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Episode).options(joinedload(Episode.outcomes))

    if user_id is not None:
        query = query.join(Assessment).filter(Assessment.user_id == user_id)

    if completed is True:
        query = query.filter(Episode.completed_at.is_not(None))
    elif completed is False:
        query = query.filter(Episode.completed_at.is_(None))

    episodes = query.order_by(Episode.created_at.desc()).limit(limit).all()
    return episodes
