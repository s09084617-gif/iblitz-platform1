from backend.database import SessionLocal
from backend.import_reference_data import import_programs, import_exercises, import_program_exercises


def main() -> None:
    db = SessionLocal()
    try:
        print("Importing programs...")
        import_programs(db)
        print("Importing exercises...")
        import_exercises(db)
        print("Importing program exercise mappings...")
        import_program_exercises(db)
        print("All imports completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
