"""Build CSV downloads.

Excel on Windows often assumes a file is not Unicode unless the file
starts with a byte-order mark. The mark is invisible in the sheet and
keeps names with accents readable.

A cell that starts with =, +, -, or @ can be treated as a formula by a
spreadsheet. Farmer names are stored as text, so those cells are prefixed
with a single quote. Numbers are written as numbers and are left alone.
"""

import csv
import io

from app.formatting import format_amount
from app.records import list_all_harvests, list_all_inputs, list_all_plantings, list_farmers
from app.reports import build_report, farmer_summary
from app.units import INPUT_UNIT_LABELS

def render_export(connection, kind):
    """Return (filename, csv_text) or None if the kind is unknown."""
    # Built on each download. The functions are defined further down in
    # this file; looking them up here keeps the names in one list.
    builders = {
        "farmers": farmers_csv,
        "inputs": inputs_csv,
        "plantings": plantings_csv,
        "harvests": harvests_csv,
        "farmer-summary": farmer_summary_csv,
        "district-summary": district_summary_csv,
    }
    builder = builders.get(kind)
    if builder is None:
        return None
    return f"{kind}.csv", builder(connection)


def farmers_csv(connection):
    rows = []
    for farmer in list_farmers(connection):
        rows.append(
            [
                farmer["full_name"],
                farmer["nrc"],
                farmer["camp"],
                farmer["district"],
                farmer["phone"] or "",
            ]
        )
    return _render(
        ["full_name", "nrc", "camp", "district", "phone"],
        rows,
    )


def inputs_csv(connection):
    rows = []
    for item in list_all_inputs(connection):
        rows.append(
            [
                item["full_name"],
                item["nrc"],
                item["district"],
                item["camp"],
                item["input_type"],
                item["quantity"],
                INPUT_UNIT_LABELS.get(item["unit"], item["unit"]),
                item["kg_equivalent"],
                item["received_date"],
                item["source"],
                item["notes"] or "",
            ]
        )
    return _render(
        [
            "farmer_name",
            "nrc",
            "district",
            "camp",
            "input_type",
            "quantity",
            "unit",
            "kilograms",
            "received_date",
            "source",
            "notes",
        ],
        rows,
    )


def plantings_csv(connection):
    rows = []
    for planting in list_all_plantings(connection):
        rows.append(
            [
                planting["full_name"],
                planting["nrc"],
                planting["district"],
                planting["camp"],
                planting["crop"],
                planting["field_size"],
                planting["size_unit"],
                planting["size_hectares"],
                planting["planting_date"],
                planting["notes"] or "",
            ]
        )
    return _render(
        [
            "farmer_name",
            "nrc",
            "district",
            "camp",
            "crop",
            "field_size",
            "size_unit",
            "hectares",
            "planting_date",
            "notes",
        ],
        rows,
    )


def harvests_csv(connection):
    rows = []
    for harvest in list_all_harvests(connection):
        rows.append(
            [
                harvest["full_name"],
                harvest["nrc"],
                harvest["district"],
                harvest["camp"],
                harvest["crop"],
                harvest["planting_date"],
                harvest["bags_50kg"],
                harvest["bags_50kg"] * 50,
                harvest["harvest_date"],
                harvest["notes"] or "",
            ]
        )
    return _render(
        [
            "farmer_name",
            "nrc",
            "district",
            "camp",
            "crop",
            "planting_date",
            "bags_50kg",
            "kilograms",
            "harvest_date",
            "notes",
        ],
        rows,
    )


def farmer_summary_csv(connection):
    """One row per farmer per crop, with yield and a list of inputs used."""
    rows = []
    for farmer in list_farmers(connection):
        summary = farmer_summary(connection, farmer["id"])
        crops = summary["crops"] or [None]
        for crop in crops:
            rows.append(
                [
                    farmer["full_name"],
                    farmer["nrc"],
                    farmer["camp"],
                    farmer["district"],
                    "" if crop is None else crop["crop"],
                    "" if crop is None else _num(crop["planted_hectares"]),
                    "" if crop is None else _num(crop["harvested_hectares"]),
                    "" if crop is None else _num(crop["bags"]),
                    "" if crop is None else _num(crop["kg"]),
                    ""
                    if crop is None or crop["yield_kg_per_ha"] is None
                    else round(crop["yield_kg_per_ha"], 1),
                    summary["inputs_phrase"],
                ]
            )
    return _render(
        [
            "farmer_name",
            "nrc",
            "camp",
            "district",
            "crop",
            "planted_hectares",
            "harvested_hectares",
            "bags_50kg",
            "harvest_kg",
            "yield_kg_per_ha",
            "inputs_used",
        ],
        rows,
    )


def district_summary_csv(connection):
    """One row per district per crop. All-districts is left out so rows can be added up."""
    report = build_report(connection)
    rows = []
    for block in report["districts"]:
        crops = block["crops"] or [None]
        for crop in crops:
            rows.append(
                [
                    block["district"],
                    block["farmer_count"],
                    block["fisp_farmer_count"],
                    "" if crop is None else crop["crop"],
                    "" if crop is None else _num(crop["planted_hectares"]),
                    "" if crop is None else _num(crop["harvested_hectares"]),
                    "" if crop is None else _num(crop["bags"]),
                    "" if crop is None else _num(crop["kg"]),
                    ""
                    if crop is None or crop["yield_kg_per_ha"] is None
                    else round(crop["yield_kg_per_ha"], 1),
                    block["inputs_phrase"],
                ]
            )
    return _render(
        [
            "district",
            "farmers",
            "fisp_farmers",
            "crop",
            "planted_hectares",
            "harvested_hectares",
            "bags_50kg",
            "harvest_kg",
            "yield_kg_per_ha",
            "inputs_used",
        ],
        rows,
    )


def _num(value):
    return format_amount(value)


def _render(headers, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_csv_safe(cell) for cell in row])
    return "\ufeff" + buffer.getvalue()


def _csv_safe(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return format_amount(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    text = str(value)
    if text[:1] in ("=", "+", "-", "@"):
        return "'" + text
    return text
