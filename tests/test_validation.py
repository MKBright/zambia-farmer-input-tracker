"""Form checks, without going through the browser."""

from datetime import date

from app.validation import parse_farmer, parse_harvest, parse_input, parse_planting


def test_farmer_accepts_a_normal_nrc_and_phone():
    data, errors = parse_farmer(
        {
            "full_name": "Mwansa Banda",
            "nrc": "234511 / 10 / 1",
            "camp": "Kanakantapa",
            "district": "Chongwe",
            "phone": "0971 001 001",
        }
    )
    assert errors == []
    assert data["nrc"] == "234511/10/1"
    assert data["phone"] == "0971001001"


def test_farmer_accepts_an_international_phone():
    data, errors = parse_farmer(
        {
            "full_name": "Bupe Mulenga",
            "nrc": "301992/11/1",
            "camp": "Chalimbana",
            "district": "Chongwe",
            "phone": "260961001002",
        }
    )
    assert errors == []
    assert data["phone"] == "+260961001002"


def test_farmer_rejects_a_bad_nrc_and_a_short_phone():
    data, errors = parse_farmer(
        {
            "full_name": "A",
            "nrc": "12345/78/1",
            "camp": "",
            "district": "Chongwe",
            "phone": "097",
        }
    )
    assert data is None
    assert any("NRC" in error for error in errors)
    assert any("phone" in error for error in errors)
    assert any("full name" in error for error in errors)
    assert any("camp" in error for error in errors)


def test_phone_can_be_left_blank():
    data, errors = parse_farmer(
        {
            "full_name": "Natasha Phiri",
            "nrc": "448120/15/1",
            "camp": "Shimabala",
            "district": "Kafue",
            "phone": "   ",
        }
    )
    assert errors == []
    assert data["phone"] is None


def test_other_input_needs_notes():
    data, errors = parse_input(
        {
            "input_type": "Other",
            "quantity": "1",
            "unit": "kg",
            "received_date": "2025-01-10",
            "source": "Own purchase",
            "notes": "",
        }
    )
    assert data is None
    assert any("Other" in error for error in errors)


def test_input_converts_a_fertilizer_bag_quantity():
    data, errors = parse_input(
        {
            "input_type": "D-Compound",
            "quantity": "2",
            "unit": "bag50",
            "received_date": "2024-11-10",
            "source": "FISP",
            "notes": "",
        }
    )
    assert errors == []
    assert data["quantity"] == 2


def test_planting_rejects_a_field_over_100_hectares():
    data, errors = parse_planting(
        {
            "crop": "Maize",
            "field_size": "500",
            "size_unit": "lima",
            "planting_date": "2024-11-22",
            "notes": "",
        }
    )
    assert data is None
    assert any("100 hectares" in error for error in errors)


def test_planting_rejects_a_future_date():
    data, errors = parse_planting(
        {
            "crop": "Maize",
            "field_size": "1",
            "size_unit": "hectares",
            "planting_date": "2099-01-01",
            "notes": "",
        }
    )
    assert data is None
    assert any("future" in error for error in errors)


def test_harvest_cannot_be_before_planting():
    planting = {"id": 1, "planting_date": "2024-12-02"}
    data, errors = parse_harvest(
        {"bags_50kg": "10", "harvest_date": "2024-11-01", "notes": ""},
        planting,
    )
    assert data is None
    assert any("before the planting date" in error for error in errors)


def test_zero_bags_is_allowed_for_a_failed_crop():
    planting = {"id": 4, "planting_date": "2024-12-02"}
    data, errors = parse_harvest(
        {"bags_50kg": "0", "harvest_date": "2025-06-01", "notes": "Crop failed"},
        planting,
    )
    assert errors == []
    assert data["bags_50kg"] == 0
    assert data["planting_id"] == 4


def test_dates_use_the_computer_clock():
    """A planting dated today is accepted. This guards the future-date rule."""
    today = date.today().isoformat()
    data, errors = parse_planting(
        {
            "crop": "Soybeans",
            "field_size": "1",
            "size_unit": "hectares",
            "planting_date": today,
            "notes": "",
        }
    )
    assert errors == []
    assert data["planting_date"] == today
