import os
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Exercise, Program, ProgramExercise

BASE_DIR = Path(__file__).resolve().parent.parent
PROGRAM_FILE = BASE_DIR / "IBLITZ_216_Program_Library.xlsx"
EXERCISE_FILE = BASE_DIR / "IBLITZ_Master_Exercise_Database_vNext.xlsx"
PROGRAM_EXERCISE_FILE = BASE_DIR / "IBLITZ_Program_Exercises_Expanded.xlsx"


def normalize_code(value: str) -> str:
    return str(value).strip().lower() if value is not None else ""


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


def import_program_exercises(db: Session):
    if not PROGRAM_EXERCISE_FILE.exists():
        raise FileNotFoundError(f"Program exercises file not found: {PROGRAM_EXERCISE_FILE}")

    rows = pd.read_excel(PROGRAM_EXERCISE_FILE, sheet_name="Program_Exercises", dtype=str)
    for _, row in rows.iterrows():
        program_code = normalize_code(row.get("Program ID", ""))
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


def main():
    db = get_db()
    try:
        print("Importing programs...")
        import_programs(db)
        print("Importing exercises...")
        import_exercises(db)
        print("Importing program exercise mappings...")
        import_program_exercises(db)
        print("Program and exercise import completed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
