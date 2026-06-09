from backend.database import SessionLocal
from backend.import_reference_data import import_exercises


def main() -> None:
    db = SessionLocal()
    try:
        print("Importing exercises from IBLITZ_Master_Exercise_Database_vNext.xlsx...")
        import_exercises(db)
        print("Exercises import completed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
