from backend.database import SessionLocal
from backend.import_reference_data import import_program_exercises


def main() -> None:
    db = SessionLocal()
    try:
        print("Importing program exercise mappings from IBLITZ_Program_Exercises_Expanded.xlsx...")
        import_program_exercises(db)
        print("Program exercise mappings import completed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
