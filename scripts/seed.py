"""Run from project root: python scripts/seed.py"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.db.seed import run_seed
from app.db.session import SessionLocal


def main() -> None:
    run_seed(SessionLocal)


if __name__ == "__main__":
    main()
