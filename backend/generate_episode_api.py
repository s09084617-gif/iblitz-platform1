from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .models import (
    Assessment,
    Episode,
    Outcome,
    Program,
    ProgramExercise,
    RecommendationRule,
    Restriction,
    User,
    Workout,
    ClassificationRule,
    ProgramRule,
)
from .schemas import (
    EpisodeResponse,
    GenerateEpisodeRequest,
    GenerateEpisodeResponse,
    GenerateWorkoutRequest,
    WorkoutResponse,
)

router = APIRouter()


def get_classification(db: Session, pbf: float, smm: str) -> str:
    smm_key = smm.lower().strip()
    rule = (
        db.query(ClassificationRule)
        .filter(ClassificationRule.active.is_(True))
        .filter(ClassificationRule.pbf_min <= pbf)
        .filter(or_(ClassificationRule.pbf_max.is_(None), pbf < ClassificationRule.pbf_max))
        .filter(or_(ClassificationRule.smm_key.is_(None), ClassificationRule.smm_key == smm_key))
        .order_by(ClassificationRule.priority.desc())
        .first()
    )
    if rule:
        return rule.classification
    return "normal"


def get_recommendation(db: Session, classification: str, goal: str) -> str:
    goal_key = goal.lower().strip()
    rule = (
        db.query(RecommendationRule)
        .filter(RecommendationRule.active.is_(True))
        .filter(RecommendationRule.classification == classification)
        .filter(or_(RecommendationRule.goal_key.is_(None), RecommendationRule.goal_key == goal_key))
        .order_by(RecommendationRule.priority.desc())
        .first()
    )
    if rule:
        return rule.recommendation
    if goal_key == "fat_loss":
        return "fat_loss"
    if goal_key == "muscle_gain":
        return "muscle_gain"
    if goal_key == "maintenance":
        return "maintenance"
    return "general_fitness"


def get_program(db: Session, classification: str, restriction: Optional[str]) -> str:
    restriction_key = restriction.upper().strip() if restriction else None
    rule = (
        db.query(ProgramRule)
        .filter(ProgramRule.active.is_(True))
        .filter(ProgramRule.classification == classification)
        .filter(or_(ProgramRule.restriction_code.is_(None), ProgramRule.restriction_code == restriction_key))
        .order_by(ProgramRule.priority.desc())
        .first()
    )
    if rule:
        return rule.program_code
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


def generate_workout_details(db: Session, program: str, goal: str, restriction: Optional[str]) -> dict:
    program_key = program.lower().strip()
    restriction_key = restriction.upper().strip() if restriction else None
    program_obj = db.query(Program).filter(Program.code == program_key).first()
    substitution_map = {}

    if restriction_key:
        restriction_obj = db.query(Restriction).filter(Restriction.code == restriction_key).first()
        if restriction_obj:
            for substitution in restriction_obj.substitutions:
                substitution_map[substitution.exercise_id] = substitution.substitute_exercise

    workouts = []
    if program_obj:
        mappings = (
            db.query(ProgramExercise)
            .options(joinedload(ProgramExercise.exercise))
            .filter(ProgramExercise.program_id == program_obj.id)
            .order_by(ProgramExercise.day, ProgramExercise.sequence)
            .all()
        )

        grouped = {}
        for mapping in mappings:
            exercise = substitution_map.get(mapping.exercise_id, mapping.exercise)
            movement = {
                "name": exercise.name,
                "sets": mapping.sets,
                "reps": mapping.reps,
            }
            if mapping.duration:
                movement["duration"] = mapping.duration
            if mapping.notes:
                movement["notes"] = mapping.notes

            if mapping.day:
                grouped.setdefault(mapping.day, []).append(movement)
            else:
                workouts.append(movement)

        if grouped:
            workouts = [{"day": day, "movements": movements} for day, movements in grouped.items()]

    if not workouts:
        workouts = [
            {"name": "Goblet Squat", "sets": 3, "reps": "10-15"},
            {"name": "Push-up", "sets": 3, "reps": "12-20"},
            {"name": "Dumbbell Row", "sets": 3, "reps": "10-15"},
            {"name": "Lunge", "sets": 3, "reps": "10-12"},
            {"name": "Plank", "sets": 3, "duration": "30s"},
        ]

    return {
        "program": program,
        "goal": goal,
        "restriction": restriction,
        "workouts": workouts,
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

    details = generate_workout_details(db, request.program, request.goal, request.restriction)
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
    classification = get_classification(db, request.pbf, request.smm)
    recommendation = get_recommendation(db, classification, request.goal)
    program = get_program(db, classification, request.restriction)

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
