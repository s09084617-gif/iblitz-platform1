import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from backend.database import SessionLocal
from backend.import_reference_data import import_program_exercises


def main():
    db = SessionLocal()
    try:
        print("Importing program -> exercise mappings from IBLITZ_Program_Exercises_Expanded.xlsx...")
        import_program_exercises(db)
        print("Program exercise mappings import completed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
