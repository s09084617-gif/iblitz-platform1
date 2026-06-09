import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from backend.database import SessionLocal
from backend.import_reference_data import import_restrictions


def main():
    db = SessionLocal()
    try:
        print("Importing restrictions and substitutions from Excel assets...")
        import_restrictions(db)
        print("Restrictions and substitutions import completed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
