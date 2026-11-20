"""CSV files and the web pages an officer would click through."""

import csv
import io
import subprocess
import sys
from pathlib import Path

from app.db import get_db
from app.sample_data import seed_database

ROOT = Path(__file__).resolve().parent.parent


def _read_csv(response):
    assert response.status_code == 200
    assert "text/csv" in response.content_type
    text = response.data.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def test_home_explains_the_empty_book(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"No farmers yet" in response.data
    assert b"Farmer Input Support Programme" in response.data


def test_officer_records_a_season_and_sees_the_yield(client):
    created = client.post(
        "/farmers/new",
        data={
            "full_name": "Lweendo Hamweene",
            "nrc": "600100/10/1",
            "camp": "Kanakantapa",
            "district": "Chongwe",
            "phone": "0971 002 003",
        },
    )
    assert created.status_code == 302
    farmer_path = created.headers["Location"]
    assert farmer_path.startswith("/farmers/")

    page = client.get(farmer_path)
    assert b"Registered Lweendo Hamweene." in page.data
    assert b"0971002003" in page.data

    saved_input = client.post(
        farmer_path + "/inputs/new",
        data={
            "input_type": "D-Compound",
            "quantity": "2",
            "unit": "bag50",
            "received_date": "2025-11-10",
            "source": "FISP",
            "notes": "",
        },
        follow_redirects=True,
    )
    assert b"2" in saved_input.data
    assert b"50 kg bag" in saved_input.data
    assert b"100" in saved_input.data

    saved_planting = client.post(
        farmer_path + "/plantings/new",
        data={
            "crop": "Maize",
            "field_size": "4",
            "size_unit": "lima",
            "planting_date": "2025-11-20",
            "notes": "",
        },
        follow_redirects=True,
    )
    assert b"4 lima (1.00 ha)" in saved_planting.data

    harvest_form = client.get(farmer_path + "/harvests/new")
    assert b'value="1"' in harvest_form.data

    saved_harvest = client.post(
        farmer_path + "/harvests/new",
        data={
            "planting_id": "1",
            "bags_50kg": "20",
            "harvest_date": "2026-06-01",
            "notes": "",
        },
        follow_redirects=True,
    )
    # 20 bags x 50 kg / 1.00 ha = 1,000 kg/ha.
    assert b"1,000 kg/ha" in saved_harvest.data

    report = client.get("/reports?district=Chongwe")
    assert report.status_code == 200
    assert b"Lweendo Hamweene" in report.data
    assert b"1,000" in report.data

    rows = _read_csv(client.get("/export/farmer-summary.csv"))
    assert rows[0]["farmer_name"] == "Lweendo Hamweene"
    assert rows[0]["crop"] == "Maize"
    assert float(rows[0]["yield_kg_per_ha"]) == 1000
    assert "D-Compound 100 kg" in rows[0]["inputs_used"]


def test_duplicate_nrc_and_bad_nrc_stay_on_the_form(client):
    payload = {
        "full_name": "Mwansa Banda",
        "nrc": "234511/10/1",
        "camp": "Kanakantapa",
        "district": "Chongwe",
        "phone": "",
    }
    assert client.post("/farmers/new", data=payload).status_code == 302
    duplicate = client.post("/farmers/new", data=payload)
    assert duplicate.status_code == 400
    assert b"already registered" in duplicate.data

    bad = client.post(
        "/farmers/new",
        data={**payload, "full_name": "Someone Else", "nrc": "not-an-nrc"},
    )
    assert bad.status_code == 400
    assert b"Enter the NRC like 123456/78/1." in bad.data


def test_harvest_for_another_farmers_planting_is_rejected(client):
    first = client.post(
        "/farmers/new",
        data={
            "full_name": "First Farmer",
            "nrc": "111111/10/1",
            "camp": "Kanakantapa",
            "district": "Chongwe",
            "phone": "",
        },
    )
    first_path = first.headers["Location"]
    client.post(
        first_path + "/plantings/new",
        data={
            "crop": "Maize",
            "field_size": "1",
            "size_unit": "hectares",
            "planting_date": "2025-11-20",
            "notes": "",
        },
    )
    second = client.post(
        "/farmers/new",
        data={
            "full_name": "Second Farmer",
            "nrc": "222222/10/1",
            "camp": "Kanakantapa",
            "district": "Chongwe",
            "phone": "",
        },
    )
    second_path = second.headers["Location"]
    client.post(
        second_path + "/plantings/new",
        data={
            "crop": "Maize",
            "field_size": "1",
            "size_unit": "hectares",
            "planting_date": "2025-11-21",
            "notes": "",
        },
    )
    # Planting 1 belongs to the first farmer. The second farmer must not use it.
    rejected = client.post(
        second_path + "/harvests/new",
        data={
            "planting_id": "1",
            "bags_50kg": "5",
            "harvest_date": "2026-06-01",
            "notes": "",
        },
    )
    assert rejected.status_code == 400
    assert b"Choose the planting" in rejected.data


def test_formula_like_name_is_neutralised_in_csv(client):
    client.post(
        "/farmers/new",
        data={
            "full_name": "=1+1",
            "nrc": "333333/10/1",
            "camp": "Kanakantapa",
            "district": "Chongwe",
            "phone": "",
        },
    )
    rows = _read_csv(client.get("/export/farmers.csv"))
    assert rows[0]["full_name"] == "'=1+1"


def test_sample_pages_and_district_csv(client, app):
    with app.app_context():
        seed_database(get_db())

    home = client.get("/")
    assert b"Mwansa Banda" in home.data

    farmers = client.get("/farmers?q=Chongwe")
    assert b"Mwansa Banda" in farmers.data
    assert b"Bupe Mulenga" in farmers.data
    assert b"Joseph Tembo" not in farmers.data

    detail = client.get("/farmers/1")
    # Farmer 1 is the first inserted sample farmer, Mwansa Banda.
    assert b"Mwansa Banda" in detail.data
    assert b"1,800 kg/ha" in detail.data
    assert b"MRI 634" in detail.data

    report = client.get("/reports?district=Chongwe")
    assert b"2,000 kg/ha" in report.data
    assert b"Joseph Tembo" not in report.data

    missing = client.get("/farmers/999")
    assert missing.status_code == 404
    assert b"not in the tracker" in missing.data

    unknown_csv = client.get("/export/nope.csv")
    assert unknown_csv.status_code == 404

    district_rows = _read_csv(client.get("/export/district-summary.csv"))
    chongwe = [
        row
        for row in district_rows
        if row["district"] == "Chongwe" and row["crop"] == "Maize"
    ]
    assert len(chongwe) == 1
    assert float(chongwe[0]["yield_kg_per_ha"]) == 2000
    assert chongwe[0]["fisp_farmers"] == "2"
    assert all(row["district"] != "All districts" for row in district_rows)


def test_seed_script_prints_the_summary(tmp_path):
    database = tmp_path / "sample.db"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seed_sample_data.py"), str(database)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "yield 1800 kg/ha" in result.stdout
    assert "Saved 5 farmers, 14 inputs, 6 plantings, and 6 harvests." in result.stdout
    assert database.exists()
