"""Save and load farmers, inputs, plantings, and harvests.

The SQL uses ? placeholders. The values are passed separately, so a name
cannot change the meaning of the query. A test covers this with a name
that looks like a SQL command.
"""

from datetime import datetime, timezone

from app.db import execute, query_all, query_one
from app.units import kilograms_for, to_hectares


def now_stamp():
    """UTC time the row was saved, for example 2026-11-20T19:40:00+00:00."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def insert_farmer(connection, data):
    return execute(
        connection,
        """
        INSERT INTO farmers (full_name, nrc, camp, district, phone, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data["full_name"],
            data["nrc"],
            data["camp"],
            data["district"],
            data.get("phone"),
            now_stamp(),
        ),
    )


def get_farmer(connection, farmer_id):
    return query_one(connection, "SELECT * FROM farmers WHERE id = ?", (farmer_id,))


def nrc_taken(connection, nrc):
    row = query_one(connection, "SELECT id FROM farmers WHERE nrc = ?", (nrc,))
    return row is not None


def list_farmers(connection, search=""):
    """List farmers, optionally matching a name, NRC, camp, district, or phone."""
    sql = "SELECT * FROM farmers"
    params = []
    term = (search or "").strip()
    if term:
        pattern = _like_pattern(term)
        sql += """
            WHERE full_name LIKE ? ESCAPE '\\'
               OR nrc LIKE ? ESCAPE '\\'
               OR camp LIKE ? ESCAPE '\\'
               OR district LIKE ? ESCAPE '\\'
               OR IFNULL(phone, '') LIKE ? ESCAPE '\\'
        """
        params.extend([pattern, pattern, pattern, pattern, pattern])
    sql += " ORDER BY full_name COLLATE NOCASE, id"
    return query_all(connection, sql, params)


def list_districts(connection):
    rows = query_all(
        connection,
        "SELECT DISTINCT district FROM farmers ORDER BY district COLLATE NOCASE",
    )
    return [row["district"] for row in rows]


def insert_input(connection, farmer_id, data):
    kilograms = kilograms_for(data["quantity"], data["unit"])
    return execute(
        connection,
        """
        INSERT INTO inputs (
            farmer_id, input_type, quantity, unit, kg_equivalent,
            received_date, source, notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            farmer_id,
            data["input_type"],
            data["quantity"],
            data["unit"],
            kilograms,
            data["received_date"],
            data["source"],
            data.get("notes"),
            now_stamp(),
        ),
    )


def list_inputs(connection, farmer_id):
    return query_all(
        connection,
        """
        SELECT * FROM inputs
        WHERE farmer_id = ?
        ORDER BY received_date, id
        """,
        (farmer_id,),
    )


def list_all_inputs(connection):
    return query_all(
        connection,
        """
        SELECT inputs.*, farmers.full_name, farmers.nrc, farmers.camp, farmers.district
        FROM inputs
        JOIN farmers ON farmers.id = inputs.farmer_id
        ORDER BY inputs.received_date, inputs.id
        """,
    )


def recent_inputs(connection, limit=5):
    return query_all(
        connection,
        """
        SELECT inputs.*, farmers.full_name, farmers.district
        FROM inputs
        JOIN farmers ON farmers.id = inputs.farmer_id
        ORDER BY inputs.received_date DESC, inputs.id DESC
        LIMIT ?
        """,
        (limit,),
    )


def insert_planting(connection, farmer_id, data):
    hectares = to_hectares(data["field_size"], data["size_unit"])
    return execute(
        connection,
        """
        INSERT INTO plantings (
            farmer_id, crop, field_size, size_unit, size_hectares,
            planting_date, notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            farmer_id,
            data["crop"],
            data["field_size"],
            data["size_unit"],
            hectares,
            data["planting_date"],
            data.get("notes"),
            now_stamp(),
        ),
    )


def get_planting(connection, planting_id):
    return query_one(
        connection, "SELECT * FROM plantings WHERE id = ?", (planting_id,)
    )


def list_plantings(connection, farmer_id):
    return query_all(
        connection,
        """
        SELECT * FROM plantings
        WHERE farmer_id = ?
        ORDER BY planting_date, id
        """,
        (farmer_id,),
    )


def list_all_plantings(connection):
    return query_all(
        connection,
        """
        SELECT plantings.*, farmers.full_name, farmers.nrc, farmers.camp, farmers.district
        FROM plantings
        JOIN farmers ON farmers.id = plantings.farmer_id
        ORDER BY plantings.planting_date, plantings.id
        """,
    )


def insert_harvest(connection, data):
    return execute(
        connection,
        """
        INSERT INTO harvests (planting_id, bags_50kg, harvest_date, notes, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data["planting_id"],
            data["bags_50kg"],
            data["harvest_date"],
            data.get("notes"),
            now_stamp(),
        ),
    )


# Shared SELECT for harvest lists. The crop and the farmer come from the
# planting, then the farmer row adds the name shown on screen.
HARVEST_SELECT = """
SELECT
    harvests.id AS id,
    harvests.planting_id AS planting_id,
    harvests.bags_50kg AS bags_50kg,
    harvests.harvest_date AS harvest_date,
    harvests.notes AS notes,
    harvests.created_at AS created_at,
    plantings.farmer_id AS farmer_id,
    plantings.crop AS crop,
    plantings.planting_date AS planting_date,
    plantings.size_hectares AS size_hectares,
    farmers.full_name AS full_name,
    farmers.nrc AS nrc,
    farmers.district AS district,
    farmers.camp AS camp
FROM harvests
JOIN plantings ON plantings.id = harvests.planting_id
JOIN farmers ON farmers.id = plantings.farmer_id
"""


def list_harvests(connection, farmer_id):
    return query_all(
        connection,
        HARVEST_SELECT
        + " WHERE plantings.farmer_id = ? ORDER BY harvests.harvest_date, harvests.id",
        (farmer_id,),
    )


def list_all_harvests(connection):
    return query_all(
        connection,
        HARVEST_SELECT + " ORDER BY harvests.harvest_date, harvests.id",
    )


def recent_harvests(connection, limit=5):
    return query_all(
        connection,
        HARVEST_SELECT
        + " ORDER BY harvests.harvest_date DESC, harvests.id DESC LIMIT ?",
        (limit,),
    )


def dashboard_stats(connection):
    """Counts for the home page. COALESCE turns a sum of no rows into 0."""
    farmers = query_one(connection, "SELECT COUNT(*) AS n FROM farmers")["n"]
    inputs = query_one(connection, "SELECT COUNT(*) AS n FROM inputs")["n"]
    hectares = query_one(
        connection, "SELECT COALESCE(SUM(size_hectares), 0) AS n FROM plantings"
    )["n"]
    bags = query_one(
        connection, "SELECT COALESCE(SUM(bags_50kg), 0) AS n FROM harvests"
    )["n"]
    return {
        "farmers": farmers,
        "inputs": inputs,
        "hectares": hectares,
        "bags": bags,
    }


def _like_pattern(term):
    """Build a LIKE pattern where % and _ typed by the user stay literal.

    Without this, a search for "%" would match every farmer.
    """
    escaped = (
        term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )
    return f"%{escaped}%"
