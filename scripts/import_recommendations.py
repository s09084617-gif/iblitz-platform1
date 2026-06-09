import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from backend.database import SessionLocal
from backend.import_reference_data import import_recommendation_rules


def main():
    db = SessionLocal()
    try:
        print("Importing recommendation rules from IBLITZ_Decision_Engine_V15.xlsx...")
        import_recommendation_rules(db)
        print("Recommendation rules import completed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
