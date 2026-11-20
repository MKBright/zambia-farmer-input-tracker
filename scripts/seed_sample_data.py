#!/usr/bin/env python3
"""Load the fictional sample farmers into the local database.

Running this replaces that database file so the sample can be repeated
from a clean start. Your own records in that file are removed.

    python scripts/seed_sample_data.py
    python scripts/seed_sample_data.py /tmp/practice.db

The path line below lets this file import the app package when you run
it directly. Python would otherwise look only inside the scripts folder.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import connect, init_db
from app.reports import build_text_report
from app.sample_data import seed_database


def main():
    if len(sys.argv) > 2:
        print("Usage: python scripts/seed_sample_data.py [database-file]")
        return 1

    if len(sys.argv) == 2:
        db_path = Path(sys.argv[1])
    else:
        db_path = ROOT / "data" / "farm_tracker.db"

    if db_path.exists():
        db_path.unlink()

    connection = connect(db_path)
    try:
        init_db(connection)
        counts = seed_database(connection)
        print(build_text_report(connection), end="")
        print()
        print(
            "Saved {farmers} farmers, {inputs} inputs, "
            "{plantings} plantings, and {harvests} harvests.".format(**counts)
        )
        print(f"Database file: {db_path}")
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
