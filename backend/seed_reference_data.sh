#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

python3 scripts/import_programs.py
python3 scripts/import_exercises.py
python3 scripts/import_program_mappings.py
python3 scripts/import_recommendations.py
python3 scripts/import_restrictions.py

echo "Reference data import completed."
