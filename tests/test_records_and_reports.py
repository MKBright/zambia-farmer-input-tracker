"""Saving rows and the yield maths.

The sample farmers use round numbers so the yields can be checked by hand.
Mwansa: 18 bags x 50 kg / 0.5 ha = 1,800 kg/ha.
Chongwe maize (Mwansa + Bupe): 40 bags x 50 kg / 1.0 ha = 2,000 kg/ha.
"""

import pytest

from app.records import (
    dashboard_stats,
    get_planting,
    insert_farmer,
    insert_harvest,
    insert_input,
    insert_planting,
    list_farmers,
)
from app.reports import build_report, build_text_report, farmer_summary
from app.sample_data import seed_database


def _farmer(connection, name="Test Farmer", nrc="600100/10/1"):
    farmer_id = insert_farmer(
        connection,
        {
            "full_name": name,
            "nrc": nrc,
            "camp": "Kanakantapa",
            "district": "Chongwe",
            "phone": None,
        },
    )
    return farmer_id


def test_lima_is_stored_as_hectares(connection):
    farmer_id = _farmer(connection)
    planting_id = insert_planting(
        connection,
        farmer_id,
        {
            "crop": "Maize",
            "field_size": 4,
            "size_unit": "lima",
            "planting_date": "2024-11-28",
            "notes": None,
        },
    )
    planting = get_planting(connection, planting_id)
    assert planting["field_size"] == 4
    assert planting["size_unit"] == "lima"
    assert planting["size_hectares"] == pytest.approx(1)


def test_two_partial_harvests_are_added(connection):
    farmer_id = _farmer(connection)
    planting_id = insert_planting(
        connection,
        farmer_id,
        {
            "crop": "Maize",
            "field_size": 1,
            "size_unit": "hectares",
            "planting_date": "2024-11-22",
            "notes": None,
        },
    )
    insert_harvest(
        connection,
        {
            "planting_id": planting_id,
            "bags_50kg": 10,
            "harvest_date": "2025-06-01",
            "notes": None,
        },
    )
    insert_harvest(
        connection,
        {
            "planting_id": planting_id,
            "bags_50kg": 8,
            "harvest_date": "2025-06-20",
            "notes": None,
        },
    )
    maize = farmer_summary(connection, farmer_id)["crops"][0]
    assert maize["bags"] == pytest.approx(18)
    assert maize["kg"] == pytest.approx(900)
    assert maize["yield_kg_per_ha"] == pytest.approx(900)


def test_unharvested_area_does_not_dilute_yield(connection):
    farmer_id = _farmer(connection)
    harvested = insert_planting(
        connection,
        farmer_id,
        {
            "crop": "Maize",
            "field_size": 1,
            "size_unit": "hectares",
            "planting_date": "2024-11-22",
            "notes": None,
        },
    )
    insert_planting(
        connection,
        farmer_id,
        {
            "crop": "Maize",
            "field_size": 1,
            "size_unit": "hectares",
            "planting_date": "2024-12-02",
            "notes": "Still in the field",
        },
    )
    insert_harvest(
        connection,
        {
            "planting_id": harvested,
            "bags_50kg": 20,
            "harvest_date": "2025-06-12",
            "notes": None,
        },
    )
    maize = farmer_summary(connection, farmer_id)["crops"][0]
    assert maize["planted_hectares"] == pytest.approx(2)
    assert maize["harvested_hectares"] == pytest.approx(1)
    # 20 bags is 1,000 kg from the harvested hectare, not 500 from both.
    assert maize["yield_kg_per_ha"] == pytest.approx(1000)


def test_zero_bag_harvest_counts_as_a_failed_crop(connection):
    farmer_id = _farmer(connection)
    planting_id = insert_planting(
        connection,
        farmer_id,
        {
            "crop": "Maize",
            "field_size": 1,
            "size_unit": "hectares",
            "planting_date": "2024-11-22",
            "notes": None,
        },
    )
    insert_harvest(
        connection,
        {
            "planting_id": planting_id,
            "bags_50kg": 0,
            "harvest_date": "2025-06-12",
            "notes": "Failed",
        },
    )
    maize = farmer_summary(connection, farmer_id)["crops"][0]
    assert maize["yield_kg_per_ha"] == pytest.approx(0)
    assert maize["harvested_hectares"] == pytest.approx(1)


def test_fertilizer_bags_become_kilograms(connection):
    farmer_id = _farmer(connection)
    insert_input(
        connection,
        farmer_id,
        {
            "input_type": "Urea",
            "quantity": 2,
            "unit": "bag50",
            "received_date": "2024-11-10",
            "source": "FISP",
            "notes": None,
        },
    )
    totals = farmer_summary(connection, farmer_id)["input_totals"]
    assert totals == [{"input_type": "Urea", "kg": 100}]


def test_sample_yields_for_farmers_and_chongwe(connection):
    seed_database(connection)
    farmers = {row["full_name"]: row for row in list_farmers(connection)}

    mwansa = farmer_summary(connection, farmers["Mwansa Banda"]["id"])
    maize = next(crop for crop in mwansa["crops"] if crop["crop"] == "Maize")
    assert maize["yield_kg_per_ha"] == pytest.approx(1800)
    assert "D-Compound 100 kg" in mwansa["inputs_phrase"]

    bupe = farmer_summary(connection, farmers["Bupe Mulenga"]["id"])
    bupe_maize = bupe["crops"][0]
    assert bupe_maize["planted_hectares"] == pytest.approx(0.5)
    assert bupe_maize["yield_kg_per_ha"] == pytest.approx(2200)
    assert "Urea 150 kg" in bupe["inputs_phrase"]

    mutinta = farmer_summary(connection, farmers["Mutinta Zulu"]["id"])
    by_crop = {crop["crop"]: crop for crop in mutinta["crops"]}
    assert by_crop["Maize"]["yield_kg_per_ha"] == pytest.approx(2000)
    assert by_crop["Groundnuts"]["yield_kg_per_ha"] == pytest.approx(800)
    assert by_crop["Groundnuts"]["planted_hectares"] == pytest.approx(0.25)

    joseph = farmer_summary(connection, farmers["Joseph Tembo"]["id"])
    assert joseph["crops"][0]["yield_kg_per_ha"] == pytest.approx(1000)

    chongwe = build_report(connection, "chongwe")["current"]
    assert chongwe["district"] == "Chongwe"
    assert chongwe["farmer_count"] == 2
    assert chongwe["fisp_farmer_count"] == 2
    chongwe_maize = next(crop for crop in chongwe["crops"] if crop["crop"] == "Maize")
    assert chongwe_maize["bags"] == pytest.approx(40)
    assert chongwe_maize["yield_kg_per_ha"] == pytest.approx(2000)

    everyone = build_report(connection)["current"]
    assert everyone["farmer_count"] == 5
    assert everyone["fisp_farmer_count"] == 3
    all_maize = next(crop for crop in everyone["crops"] if crop["crop"] == "Maize")
    assert all_maize["yield_kg_per_ha"] == pytest.approx(2000)
    all_nuts = next(crop for crop in everyone["crops"] if crop["crop"] == "Groundnuts")
    assert all_nuts["yield_kg_per_ha"] == pytest.approx(800)
    assert all_nuts["planted_hectares"] == pytest.approx(1.25)


def test_sample_totals_match_the_home_page(connection):
    seed_database(connection)
    stats = dashboard_stats(connection)
    assert stats["farmers"] == 5
    assert stats["inputs"] == 14
    assert stats["hectares"] == pytest.approx(4.75)
    assert stats["bags"] == pytest.approx(130)


def test_text_report_includes_the_worked_examples(connection):
    seed_database(connection)
    report = build_text_report(connection)
    assert "Mwansa Banda (Chongwe / Kanakantapa)" in report
    assert "Maize: 0.50 ha planted, 18 x 50 kg bags, yield 1800 kg/ha" in report
    assert "Maize: 0.50 ha planted, 22 x 50 kg bags, yield 2200 kg/ha" in report
    assert "Maize: 1.00 ha planted, 40 x 50 kg bags, yield 2000 kg/ha" in report
    assert "Groundnuts: 1.25 ha planted, 20 x 50 kg bags, yield 800 kg/ha" in report
    assert "Soybeans: 1.50 ha planted, 30 x 50 kg bags, yield 1000 kg/ha" in report
    assert "FISP farmers: 3" in report


def test_search_does_not_treat_percent_as_match_everything(connection):
    seed_database(connection)
    assert len(list_farmers(connection, "Chongwe")) == 2
    assert len(list_farmers(connection, "234511")) == 1
    assert list_farmers(connection, "%") == []


def test_sql_like_name_is_stored_as_text(connection):
    tricky = "Robert'); DROP TABLE farmers;--"
    _farmer(connection, name=tricky, nrc="700100/10/1")
    names = [row["full_name"] for row in list_farmers(connection)]
    assert names == [tricky]
