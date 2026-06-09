import os
import re
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import (
    Exercise,
    ExerciseSubstitution,
    Program,
    ProgramExercise,
    RecommendationRule,
    Restriction,
)

BASE_DIR = Path(__file__).resolve().parent.parent
PROGRAM_FILE = BASE_DIR / "IBLITZ_216_Program_Library.xlsx"
EXERCISE_FILE = BASE_DIR / "IBLITZ_Master_Exercise_Database_vNext.xlsx"
PROGRAM_EXERCISE_FILE = BASE_DIR / "IBLITZ_Program_Exercises_Expanded.xlsx"
DECISION_ENGINE_FILE = BASE_DIR / "IBLITZ_Decision_Engine_V15.xlsx"
INTELLIGENCE_FILE = BASE_DIR / "IBLITZ_Priority9_Intelligence_Layer.xlsx"


def normalize_code(value: str) -> str:
    return str(value).strip().lower() if value is not None else ""


def normalize_text(value: str) -> str:
    normalized = str(value or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def normalize_key(value: str) -> str:
    normalized = str(value or "").lower()
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")


def get_db() -> Session:
    return SessionLocal()


def import_programs(db: Session):
    if not PROGRAM_FILE.exists():
        raise FileNotFoundError(f"Program file not found: {PROGRAM_FILE}")

    programs = pd.read_excel(PROGRAM_FILE, sheet_name="Programs", dtype=str)
    for _, row in programs.iterrows():
        program_id = normalize_code(row.get("Program ID", ""))
        if not program_id:
            continue
        program_name = str(row.get("Program Name", "")).strip()
        goal = str(row.get("Goal", "")).strip()
        muscle = str(row.get("Muscle", "")).strip()
        level = str(row.get("Level", "")).strip()
        description = ", ".join(filter(None, [goal, muscle, level])) or None

        existing = db.query(Program).filter(Program.code == program_id).first()
        if existing:
            existing.name = program_name or existing.name
            existing.description = description or existing.description
        else:
            db.add(Program(code=program_id, name=program_name or program_id, description=description))
    db.commit()


def import_exercises(db: Session):
    if not EXERCISE_FILE.exists():
        raise FileNotFoundError(f"Exercise file not found: {EXERCISE_FILE}")

    exercises = pd.read_excel(EXERCISE_FILE, sheet_name="IBLITZ_Master_DB_vNext", dtype=str)
    for _, row in exercises.iterrows():
        exercise_id = normalize_code(row.get("Exercise ID", ""))
        if not exercise_id:
            continue
        name = str(row.get("Exercise Name", "")).strip()
        category = str(row.get("Category", "")).strip() or None
        equipment = str(row.get("Equipment", "")).strip() or None
        primary_muscle = str(row.get("Primary Muscle", "")).strip() or None
        secondary_muscle = str(row.get("Secondary Muscle", "")).strip() or None

        existing = db.query(Exercise).filter(Exercise.code == exercise_id).first()
        if existing:
            existing.name = name or existing.name
            existing.category = category or existing.category
            existing.equipment = equipment or existing.equipment
            existing.primary_muscle = primary_muscle or existing.primary_muscle
            existing.secondary_muscle = secondary_muscle or existing.secondary_muscle
        else:
            db.add(
                Exercise(
                    code=exercise_id,
                    name=name or exercise_id,
                    category=category,
                    equipment=equipment,
                    primary_muscle=primary_muscle,
                    secondary_muscle=secondary_muscle,
                )
            )
    db.commit()


PROGRAM_CODE_OFFSETS = {
    "end-ar": 132,
    "end-bk": 60,
    "end-ch": 24,
    "end-cr": 204,
    "end-lg": 168,
    "end-sh": 96,
    "hyp-ar": 120,
    "hyp-bk": 48,
    "hyp-ch": 12,
    "hyp-cr": 192,
    "hyp-lg": 156,
    "hyp-sh": 84,
    "str-ar": 108,
    "str-bk": 36,
    "str-ch": 0,
    "str-cr": 180,
    "str-lg": 144,
    "str-sh": 72,
}


def translate_program_code(program_code: str) -> str:
    if not program_code:
        return ""
    program_code = normalize_code(program_code)
    if not program_code:
        return ""

    parts = program_code.rsplit("-", 1)
    if len(parts) != 2:
        return program_code

    prefix, suffix = parts
    if prefix not in PROGRAM_CODE_OFFSETS:
        return program_code

    try:
        value = int(suffix)
    except ValueError:
        return program_code

    offset = PROGRAM_CODE_OFFSETS[prefix]
    translated_code = f"{prefix}-{value + offset:03d}"
    return translated_code


def import_program_exercises(db: Session):
    if not PROGRAM_EXERCISE_FILE.exists():
        raise FileNotFoundError(f"Program exercises file not found: {PROGRAM_EXERCISE_FILE}")

    rows = pd.read_excel(PROGRAM_EXERCISE_FILE, sheet_name="Program_Exercises", dtype=str)
    for _, row in rows.iterrows():
        program_code = translate_program_code(normalize_code(row.get("Program ID", "")))
        exercise_code = normalize_code(row.get("Exercise ID", ""))
        if not program_code or not exercise_code:
            continue
        program = db.query(Program).filter(Program.code == program_code).first()
        exercise = db.query(Exercise).filter(Exercise.code == exercise_code).first()
        if not program or not exercise:
            continue
        sequence = int(row.get("Order") or 0) if str(row.get("Order") or "").isdigit() else 0
        sets = int(row.get("Sets") or 0) if str(row.get("Sets") or "").isdigit() else None
        reps = str(row.get("Reps") or "").strip() or None
        rest = str(row.get("Rest") or "").strip() or None
        notes = {"rest": rest} if rest else None

        existing_mapping = (
            db.query(ProgramExercise)
            .filter(ProgramExercise.program_id == program.id)
            .filter(ProgramExercise.exercise_id == exercise.id)
            .filter(ProgramExercise.sequence == sequence)
            .first()
        )
        if existing_mapping:
            existing_mapping.sets = sets or existing_mapping.sets
            existing_mapping.reps = reps or existing_mapping.reps
            existing_mapping.notes = notes or existing_mapping.notes
            continue

        db.add(
            ProgramExercise(
                program_id=program.id,
                exercise_id=exercise.id,
                day=None,
                sequence=sequence,
                sets=sets,
                reps=reps,
                notes=notes,
            )
        )
    db.commit()


def find_exercise(db: Session, identifier: str) -> Optional[Exercise]:
    if not identifier:
        return None

    code_key = normalize_code(identifier)
    if code_key:
        exercise = db.query(Exercise).filter(func.lower(Exercise.code) == code_key).first()
        if exercise:
            return exercise

    name_key = normalize_text(identifier)
    if name_key:
        exercise = db.query(Exercise).filter(func.lower(Exercise.name) == name_key).first()
        if exercise:
            return exercise

        tokens = [token for token in name_key.split() if len(token) > 2]
        for token in reversed(tokens):
            exercise = (
                db.query(Exercise)
                .filter(func.lower(Exercise.name).like(f"%{token}%"))
                .order_by(Exercise.name)
                .first()
            )
            if exercise:
                return exercise

    return None


def get_or_create_restriction(db: Session, condition: str) -> Optional[Restriction]:
    name = str(condition or "").strip()
    if not name:
        return None

    restriction_code = normalize_key(name).upper()
    if not restriction_code:
        return None

    restriction = db.query(Restriction).filter(Restriction.code == restriction_code).first()
    if restriction:
        return restriction

    restriction = Restriction(
        code=restriction_code,
        name=name,
        description=f"Restriction for {name}",
    )
    db.add(restriction)
    db.flush()
    return restriction


def import_restrictions(db: Session):
    if not INTELLIGENCE_FILE.exists():
        raise FileNotFoundError(f"Intelligence file not found: {INTELLIGENCE_FILE}")

    restrictions_df = pd.read_excel(INTELLIGENCE_FILE, sheet_name="Injury_Restriction_Matrix", dtype=str)
    for _, row in restrictions_df.iterrows():
        condition = str(row.get("Condition", "")).strip()
        blocked = str(row.get("Blocked Exercise", "")).strip()
        alternative = str(row.get("Alternative", "")).strip()
        if not condition or not blocked or not alternative:
            continue

        restriction = get_or_create_restriction(db, condition)
        if not restriction:
            continue

        exercise = find_exercise(db, blocked)
        substitute = find_exercise(db, alternative)
        if not exercise or not substitute:
            continue

        existing = (
            db.query(ExerciseSubstitution)
            .filter(ExerciseSubstitution.restriction_id == restriction.id)
            .filter(ExerciseSubstitution.exercise_id == exercise.id)
            .filter(ExerciseSubstitution.substitute_exercise_id == substitute.id)
            .first()
        )
        if existing:
            continue

        db.add(
            ExerciseSubstitution(
                restriction_id=restriction.id,
                exercise_id=exercise.id,
                substitute_exercise_id=substitute.id,
                reason=f"Alternative for {condition}",
            )
        )

    substitution_file = DECISION_ENGINE_FILE
    if substitution_file.exists():
        substitutions_df = pd.read_excel(substitution_file, sheet_name="Exercise_Substitution", dtype=str)
        for _, row in substitutions_df.iterrows():
            condition = str(row.get("Condition", "")).strip()
            original = str(row.get("Original Exercise", "")).strip()
            substitute_text = str(row.get("Substitute", "")).strip()
            if not condition or not original or not substitute_text:
                continue

            restriction = get_or_create_restriction(db, condition)
            if not restriction:
                continue

            exercise = find_exercise(db, original)
            substitute = find_exercise(db, substitute_text)
            if not exercise or not substitute:
                continue

            existing = (
                db.query(ExerciseSubstitution)
                .filter(ExerciseSubstitution.restriction_id == restriction.id)
                .filter(ExerciseSubstitution.exercise_id == exercise.id)
                .filter(ExerciseSubstitution.substitute_exercise_id == substitute.id)
                .first()
            )
            if existing:
                continue

            db.add(
                ExerciseSubstitution(
                    restriction_id=restriction.id,
                    exercise_id=exercise.id,
                    substitute_exercise_id=substitute.id,
                    reason=f"Alternative for {condition}",
                )
            )

    db.commit()


def main():
    db = get_db()
    try:
        print("Importing programs...")
        import_programs(db)
        print("Importing exercises...")
        import_exercises(db)
        print("Importing program exercise mappings...")
        import_program_exercises(db)
        print("Importing restrictions and substitutions...")
        import_restrictions(db)
        print("Program, exercise, restriction, and substitution import completed.")
    finally:
        db.close()


def import_recommendation_rules(db: Session):
    if not DECISION_ENGINE_FILE.exists():
        raise FileNotFoundError(f"Decision engine file not found: {DECISION_ENGINE_FILE}")

    for sheet_name, goal_col, route_col in [
        ("Recommendation_Routing_Matrix", "Goal", "Route"),
        ("Recommendation_Rule_Library", None, "Pathway"),
    ]:
        rows = pd.read_excel(DECISION_ENGINE_FILE, sheet_name=sheet_name, dtype=str)
        for _, row in rows.iterrows():
            classification = str(row.get("Classification", "")).strip()
            recommendation = str(row.get(route_col, "")).strip()
            if not classification or not recommendation:
                continue
            goal_key = None
            if goal_col:
                goal_key = str(row.get(goal_col, "")).strip() or None

            existing = (
                db.query(RecommendationRule)
                .filter(RecommendationRule.classification == classification)
                .filter(RecommendationRule.goal_key == goal_key)
                .filter(RecommendationRule.recommendation == recommendation)
                .first()
            )
            if existing:
                continue

            db.add(
                RecommendationRule(
                    classification=classification,
                    goal_key=goal_key,
                    recommendation=recommendation,
                    priority=100,
                    active=True,
                )
            )
    db.commit()


if __name__ == "__main__":
    main()
