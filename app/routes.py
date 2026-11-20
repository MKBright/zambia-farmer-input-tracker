"""Web pages.

Forms use post-then-redirect. After a successful save the browser is sent
to the farmer page with a GET. Refreshing that page does not save the same
row a second time.
"""

from datetime import date

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.csv_export import render_export
from app.db import get_db
from app.formatting import quantity_phrase
from app.records import (
    dashboard_stats,
    get_farmer,
    get_planting,
    insert_farmer,
    insert_harvest,
    insert_input,
    insert_planting,
    list_districts,
    list_farmers,
    list_plantings,
    nrc_taken,
    recent_harvests,
    recent_inputs,
)
from app.reports import build_report, farmer_summary
from app.units import CROPS, FIELD_UNITS, INPUT_TYPES, INPUT_UNITS, SOURCES
from app.validation import parse_farmer, parse_harvest, parse_input, parse_planting

bp = Blueprint("main", __name__)


@bp.context_processor
def inject_today():
    # Date inputs use this as their maximum, so a future day cannot be picked.
    return {"today": date.today().isoformat()}


@bp.route("/")
def home():
    connection = get_db()
    stats = dashboard_stats(connection)
    inputs = [_with_quantity_label(row) for row in recent_inputs(connection)]
    return render_template(
        "index.html",
        stats=stats,
        recent_inputs=inputs,
        recent_harvests=recent_harvests(connection),
        district_names=list_districts(connection),
    )


@bp.route("/farmers")
def farmers():
    search = request.args.get("q", "")
    rows = list_farmers(get_db(), search)
    return render_template(
        "farmers.html",
        farmers=rows,
        search=search.strip(),
    )


@bp.route("/farmers/new", methods=["GET", "POST"])
def new_farmer():
    if request.method == "GET":
        return render_template("farmer_form.html", form={}, errors=[])

    connection = get_db()
    data, errors = parse_farmer(request.form)
    if data and nrc_taken(connection, data["nrc"]):
        errors.append("A farmer with this NRC is already registered.")
    if errors:
        return render_template(
            "farmer_form.html", form=request.form, errors=errors
        ), 400

    farmer_id = insert_farmer(connection, data)
    flash(f"Registered {data['full_name']}.", "success")
    return redirect(url_for("main.farmer_detail", farmer_id=farmer_id))


@bp.route("/farmers/<int:farmer_id>")
def farmer_detail(farmer_id):
    summary = farmer_summary(get_db(), farmer_id)
    if summary is None:
        abort(404)
    return render_template("farmer_detail.html", summary=summary)


@bp.route("/farmers/<int:farmer_id>/inputs/new", methods=["GET", "POST"])
def new_input(farmer_id):
    farmer = _farmer_or_404(farmer_id)
    if request.method == "GET":
        return render_template(
            "input_form.html",
            farmer=farmer,
            form={},
            errors=[],
            input_types=INPUT_TYPES,
            input_units=INPUT_UNITS,
            sources=SOURCES,
        )

    data, errors = parse_input(request.form)
    if errors:
        return render_template(
            "input_form.html",
            farmer=farmer,
            form=request.form,
            errors=errors,
            input_types=INPUT_TYPES,
            input_units=INPUT_UNITS,
            sources=SOURCES,
        ), 400

    insert_input(get_db(), farmer["id"], data)
    flash(f"Saved {data['input_type']} for {farmer['full_name']}.", "success")
    return redirect(url_for("main.farmer_detail", farmer_id=farmer["id"]))


@bp.route("/farmers/<int:farmer_id>/plantings/new", methods=["GET", "POST"])
def new_planting(farmer_id):
    farmer = _farmer_or_404(farmer_id)
    if request.method == "GET":
        return render_template(
            "planting_form.html",
            farmer=farmer,
            form={},
            errors=[],
            crops=CROPS,
            field_units=FIELD_UNITS,
        )

    data, errors = parse_planting(request.form)
    if errors:
        return render_template(
            "planting_form.html",
            farmer=farmer,
            form=request.form,
            errors=errors,
            crops=CROPS,
            field_units=FIELD_UNITS,
        ), 400

    insert_planting(get_db(), farmer["id"], data)
    flash(f"Saved the {data['crop']} planting for {farmer['full_name']}.", "success")
    return redirect(url_for("main.farmer_detail", farmer_id=farmer["id"]))


@bp.route("/farmers/<int:farmer_id>/harvests/new", methods=["GET", "POST"])
def new_harvest(farmer_id):
    farmer = _farmer_or_404(farmer_id)
    connection = get_db()
    plantings = list_plantings(connection, farmer["id"])
    if request.method == "GET":
        return render_template(
            "harvest_form.html",
            farmer=farmer,
            plantings=plantings,
            form={},
            errors=[],
        )

    planting = _planting_for_farmer(connection, request.form.get("planting_id"), farmer)
    data, errors = parse_harvest(request.form, planting)
    if errors:
        return render_template(
            "harvest_form.html",
            farmer=farmer,
            plantings=plantings,
            form=request.form,
            errors=errors,
        ), 400

    insert_harvest(connection, data)
    flash(f"Saved the harvest for {farmer['full_name']}.", "success")
    return redirect(url_for("main.farmer_detail", farmer_id=farmer["id"]))


@bp.route("/reports")
def reports():
    district = request.args.get("district", "").strip() or None
    report = build_report(get_db(), district)
    return render_template("reports.html", report=report)


@bp.route("/export")
def export_page():
    stats = dashboard_stats(get_db())
    links = (
        ("farmers", "Farmers", "Name, NRC, camp, district, and phone."),
        ("inputs", "Inputs", "Every seed and fertilizer row, with kilograms."),
        ("plantings", "Plantings", "Crop, field size, unit, hectares, and date."),
        ("harvests", "Harvests", "50 kg bags, the crop, and the harvest date."),
        (
            "farmer-summary",
            "Farmer summary",
            "Yield per hectare and inputs used, one row per farmer and crop.",
        ),
        (
            "district-summary",
            "District summary",
            "Yield and inputs for each district. Rows are not double-counted.",
        ),
    )
    return render_template("export.html", stats=stats, links=links)


@bp.route("/export/<kind>.csv")
def download_csv(kind):
    exported = render_export(get_db(), kind)
    if exported is None:
        abort(404)
    filename, body = exported
    # charset=utf-8 plus the byte-order mark in the body helps Excel.
    response = Response(body, mimetype="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _farmer_or_404(farmer_id):
    farmer = get_farmer(get_db(), farmer_id)
    if farmer is None:
        abort(404)
    return farmer


def _planting_for_farmer(connection, raw_id, farmer):
    text = (raw_id or "").strip()
    if not text.isdigit():
        return None
    planting = get_planting(connection, int(text))
    if planting is None or planting["farmer_id"] != farmer["id"]:
        return None
    return planting


def _with_quantity_label(row):
    item = dict(row)
    item["quantity_label"] = quantity_phrase(item["quantity"], item["unit"])
    return item
