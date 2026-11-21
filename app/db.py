"""SQLite helpers.

All of the records live in one file on this computer. Copy that file
if you want a backup. There is no separate database server to install.
"""

import sqlite3
from pathlib import Path

from flask import current_app, g

# The tables are created with "IF NOT EXISTS", so starting the app again
# does not wipe any records. The sample-data script is what replaces them.
SCHEMA = """
-- A farmer supported by one agricultural camp.
-- NRC is the National Registration Card number, stored as text so the
-- slashes in a number such as 123456/78/1 are kept.
CREATE TABLE IF NOT EXISTS farmers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    nrc TEXT NOT NULL UNIQUE,
    camp TEXT NOT NULL,
    district TEXT NOT NULL,
    phone TEXT,
    created_at TEXT NOT NULL
);

-- Seed, fertilizer, and other inputs the farmer received.
-- kg_equivalent lets reports add kilograms even when one row was entered
-- as bags and another was entered as kilograms.
CREATE TABLE IF NOT EXISTS inputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id INTEGER NOT NULL,
    input_type TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    kg_equivalent REAL NOT NULL,
    received_date TEXT NOT NULL,
    source TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id)
);

-- A crop planted in one field. size_hectares is always filled in, even
-- when the officer typed the field size in lima.
CREATE TABLE IF NOT EXISTS plantings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id INTEGER NOT NULL,
    crop TEXT NOT NULL,
    field_size REAL NOT NULL,
    size_unit TEXT NOT NULL,
    size_hectares REAL NOT NULL,
    planting_date TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id)
);

-- Grain or nuts collected from one planting, counted in 50 kg bags.
-- The crop and the farmer come from the planting row, so a harvest cannot
-- point at the wrong person.
CREATE TABLE IF NOT EXISTS harvests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    planting_id INTEGER NOT NULL,
    bags_50kg REAL NOT NULL,
    harvest_date TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (planting_id) REFERENCES plantings(id)
);

CREATE INDEX IF NOT EXISTS idx_inputs_farmer ON inputs(farmer_id);
CREATE INDEX IF NOT EXISTS idx_plantings_farmer ON plantings(farmer_id);
CREATE INDEX IF NOT EXISTS idx_harvests_planting ON harvests(planting_id);
CREATE INDEX IF NOT EXISTS idx_farmers_district ON farmers(district);
"""


def connect(db_path):
    """Open the database file and turn on foreign keys.

    SQLite does not enforce foreign keys unless this pragma is set on
    every new connection. The row factory lets us read columns by name.
    """
    path = Path(db_path)
    if path.parent and str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(connection):
    """Create tables that are not there yet."""
    connection.executescript(SCHEMA)
    connection.commit()


def query_all(connection, sql, params=()):
    """Run a SELECT and return a list of plain dictionaries."""
    rows = connection.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def query_one(connection, sql, params=()):
    """Run a SELECT that should return one row, or None."""
    row = connection.execute(sql, params).fetchone()
    if row is None:
        return None
    return dict(row)


def execute(connection, sql, params=()):
    """Run an INSERT or UPDATE and save it. Returns the new row id."""
    cursor = connection.execute(sql, params)
    connection.commit()
    return cursor.lastrowid


def get_db():
    """Reuse one connection for the current web request."""
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_exc=None):
    """Close the request connection. Flask calls this automatically."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()
