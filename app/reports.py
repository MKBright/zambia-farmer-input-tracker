"""Add up inputs and work out yield per hectare.

Yield uses only fields that already have a harvest. A planting with no
harvest yet is still in the ground (or the book was not updated). It is
not treated as a zero, because that would drag the average down.

A recorded harvest of 0 bags is different: the officer wrote that the
crop failed, so those hectares stay in the yield figure.

    yield (kg/ha) = (50 kg bags × 50) / harvested hectares
"""

from app.formatting import area_phrase, format_amount, format_hectares, quantity_phrase
from app.records import (
    get_farmer,
    list_all_harvests,
    list_all_inputs,
    list_all_plantings,
    list_farmers,
    list_harvests,
    list_inputs,
    list_plantings,
)
from app.units import BAG_WEIGHT_KG


def farmer_summary(connection, farmer_id):
    """Everything the farmer page and the farmer CSV need."""
    farmer = get_farmer(connection, farmer_id)
    if farmer is None:
        return None
    inputs = [_decorate_input(row) for row in list_inputs(connection, farmer_id)]
    plantings = list_plantings(connection, farmer_id)
    harvests = list_harvests(connection, farmer_id)
    harvests_by_planting = _group_by(harvests, "planting_id")
    return {
        "farmer": farmer,
        "inputs": inputs,
        "input_totals": summarise_inputs(inputs),
        "inputs_phrase": inputs_phrase(summarise_inputs(inputs)),
        "plantings": [
            _decorate_planting(row, harvests_by_planting.get(row["id"], []))
            for row in plantings
        ],
        "harvests": harvests,
        "crops": summarise_crops(plantings, harvests_by_planting),
    }


def build_report(connection, district=None):
    """District report.

    district=None means the combined "All districts" view, plus a
    comparison row for each district. A district name filters to one camp area.
    """
    farmers = list_farmers(connection)
    inputs = list_all_inputs(connection)
    plantings = list_all_plantings(connection)
    harvests = list_all_harvests(connection)

    district_names = []
    for farmer in farmers:
        if farmer["district"] not in district_names:
            district_names.append(farmer["district"])
    district_names.sort(key=str.casefold)

    def farmers_named(name):
        return [farmer for farmer in farmers if farmer["district"] == name]

    districts = [
        _build_block(name, farmers_named(name), inputs, plantings, harvests)
        for name in district_names
    ]
    combined = _build_block("All districts", farmers, inputs, plantings, harvests)

    selected = None
    current = combined
    unknown = False
    if district:
        match = next(
            (
                block
                for block in districts
                if block["district"].casefold() == district.casefold()
            ),
            None,
        )
        if match is None:
            current = _build_block(district, [], inputs, plantings, harvests)
            selected = district
            unknown = True
        else:
            current = match
            selected = match["district"]

    crop_names = sorted(
        {crop["crop"] for block in districts for crop in block["crops"]}
    )
    return {
        "current": current,
        "districts": districts,
        "district_names": district_names,
        "selected": selected,
        "unknown_district": unknown,
        "show_comparison": selected is None and bool(districts),
        "crop_names": crop_names,
    }


def build_text_report(connection):
    """Plain-text summary printed by the sample-data script."""
    report = build_report(connection)
    lines = [
        "Farm Input Tracker — sample summary",
        "",
        f"Farmers: {report['current']['farmer_count']}",
        "Districts: " + (", ".join(report["district_names"]) or "none"),
        "",
    ]
    for farmer in list_farmers(connection):
        summary = farmer_summary(connection, farmer["id"])
        lines.append(
            f"{farmer['full_name']} ({farmer['district']} / {farmer['camp']})"
        )
        lines.append(f"  NRC: {farmer['nrc']}")
        if summary["inputs_phrase"]:
            lines.append(f"  Inputs: {summary['inputs_phrase']}")
        else:
            lines.append("  Inputs: none recorded")
        if summary["crops"]:
            for crop in summary["crops"]:
                lines.append("  " + _crop_line(crop))
        else:
            lines.append("  No planting recorded")
        lines.append("")

    lines.append("--- By district ---")
    lines.append("")
    lines.extend(_block_lines(report["current"]))
    lines.append("")
    for block in report["districts"]:
        lines.extend(_block_lines(block))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def summarise_crops(plantings, harvests_by_planting):
    """One row per crop, with planted area, harvested area, and yield."""
    buckets = {}
    for planting in plantings:
        bucket = buckets.setdefault(
            planting["crop"],
            {
                "crop": planting["crop"],
                "planted_hectares": 0.0,
                "harvested_hectares": 0.0,
                "bags": 0.0,
            },
        )
        bucket["planted_hectares"] += planting["size_hectares"]
        related = harvests_by_planting.get(planting["id"], [])
        if related:
            bucket["harvested_hectares"] += planting["size_hectares"]
            bucket["bags"] += sum(row["bags_50kg"] for row in related)

    rows = []
    for bucket in buckets.values():
        kilograms = bucket["bags"] * BAG_WEIGHT_KG
        if bucket["harvested_hectares"] > 0:
            yield_kg = kilograms / bucket["harvested_hectares"]
        else:
            yield_kg = None
        rows.append(
            {
                "crop": bucket["crop"],
                "planted_hectares": bucket["planted_hectares"],
                "harvested_hectares": bucket["harvested_hectares"],
                "unharvested_hectares": (
                    bucket["planted_hectares"] - bucket["harvested_hectares"]
                ),
                "bags": bucket["bags"],
                "kg": kilograms,
                "yield_kg_per_ha": yield_kg,
            }
        )
    rows.sort(key=lambda row: row["crop"])
    return rows


def summarise_inputs(inputs):
    """Total kilograms of each input type."""
    totals = {}
    for item in inputs:
        totals[item["input_type"]] = totals.get(item["input_type"], 0.0) + item[
            "kg_equivalent"
        ]
    rows = [
        {"input_type": name, "kg": kilograms}
        for name, kilograms in totals.items()
    ]
    rows.sort(key=lambda row: row["input_type"])
    return rows


def inputs_phrase(totals):
    """Short list such as 'D-Compound 100 kg; Urea 150 kg'."""
    parts = [
        f"{row['input_type']} {format_amount(row['kg'])} kg" for row in totals
    ]
    return "; ".join(parts)


def _build_block(title, farmers, inputs, plantings, harvests):
    ids = {farmer["id"] for farmer in farmers}
    block_inputs = [row for row in inputs if row["farmer_id"] in ids]
    block_plantings = [row for row in plantings if row["farmer_id"] in ids]
    block_harvests = [row for row in harvests if row["farmer_id"] in ids]
    harvests_by_planting = _group_by(block_harvests, "planting_id")
    crops = summarise_crops(block_plantings, harvests_by_planting)
    totals = summarise_inputs(block_inputs)

    plantings_by_farmer = _group_by(block_plantings, "farmer_id")
    farmer_rows = []
    for farmer in farmers:
        farmer_crops = summarise_crops(
            plantings_by_farmer.get(farmer["id"], []), harvests_by_planting
        )
        if not farmer_crops:
            farmer_rows.append({"farmer": farmer, "crop": None})
        else:
            for crop in farmer_crops:
                farmer_rows.append({"farmer": farmer, "crop": crop})

    fisp_ids = {
        row["farmer_id"] for row in block_inputs if row["source"] == "FISP"
    }
    return {
        "district": title,
        "farmer_count": len(farmers),
        "fisp_farmer_count": len(fisp_ids & ids),
        "crops": crops,
        "input_totals": totals,
        "inputs_phrase": inputs_phrase(totals),
        "farmer_rows": farmer_rows,
        "yield_by_crop": {crop["crop"]: crop["yield_kg_per_ha"] for crop in crops},
    }


def _decorate_input(row):
    item = dict(row)
    item["quantity_label"] = quantity_phrase(item["quantity"], item["unit"])
    return item


def _decorate_planting(row, harvest_rows):
    item = dict(row)
    item["area_label"] = area_phrase(
        item["field_size"], item["size_unit"], item["size_hectares"]
    )
    item["bags_harvested"] = sum(harvest["bags_50kg"] for harvest in harvest_rows)
    item["has_harvest"] = bool(harvest_rows)
    return item


def _group_by(rows, key):
    grouped = {}
    for row in rows:
        grouped.setdefault(row[key], []).append(row)
    return grouped


def _crop_line(crop):
    planted = format_hectares(crop["planted_hectares"])
    if crop["yield_kg_per_ha"] is None:
        return f"{crop['crop']}: {planted} ha planted, no harvest yet"
    bags = format_amount(crop["bags"])
    yield_kg = format_amount(round(crop["yield_kg_per_ha"]))
    return (
        f"{crop['crop']}: {planted} ha planted, "
        f"{bags} x 50 kg bags, yield {yield_kg} kg/ha"
    )


def _block_lines(block):
    lines = [
        block["district"],
        f"  Farmers: {block['farmer_count']}",
        f"  FISP farmers: {block['fisp_farmer_count']}",
    ]
    if block["crops"]:
        for crop in block["crops"]:
            lines.append("  " + _crop_line(crop))
    else:
        lines.append("  No planting recorded")
    if block["inputs_phrase"]:
        lines.append(f"  Inputs: {block['inputs_phrase']}")
    else:
        lines.append("  Inputs: none recorded")
    return lines
