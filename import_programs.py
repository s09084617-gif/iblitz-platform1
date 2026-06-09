from backend.database import SessionLocal
from backend.import_reference_data import import_programs


def main() -> None:
    db = SessionLocal()
    try:
        print("Importing programs from IBLITZ_216_Program_Library.xlsx...")
        import_programs(db)
        print("Programs import completed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
