#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
