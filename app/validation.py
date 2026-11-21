"""Check form answers before anything is saved.

Each function returns (cleaned_values, errors). cleaned_values is None
when errors is not empty. The web pages show the error strings as they are,
so they are written for a camp officer, not for a programmer.
"""

import math
from datetime import date

from app.formatting import format_amount
from app.units import CROPS, FIELD_UNITS, INPUT_TYPES, INPUT_UNITS, SOURCES, to_hectares

# The written shape of a Zambian National Registration Card number.
# This checks the shape only. It cannot tell whether the number was issued.
NRC_EXAMPLE = "123456/78/1"

# A local number is 10 digits starting with 0. +260 and then 9 digits
# is the same phone written for international use.
PHONE_EXAMPLE = "0971234567"


def parse_farmer(form):
    """Check the register-farmer form."""
    errors = []
    full_name = _text(form.get("full_name"), "farmer's full name", 80, errors)
    nrc = _nrc(form.get("nrc"), errors)
    camp = _text(form.get("camp"), "camp", 60, errors)
    district = _text(form.get("district"), "district", 60, errors)
    phone = _phone(form.get("phone"), errors)
    if errors:
        return None, errors
    return {
        "full_name": full_name,
        "nrc": nrc,
        "camp": camp,
        "district": district,
        "phone": phone,
    }, []


def parse_input(form):
    """Check the record-input form."""
    errors = []
    input_type = _choice(form.get("input_type"), INPUT_TYPES, "type of input", errors)
    quantity = _number(form.get("quantity"), "quantity", 0.01, 100000, errors)
    unit = _choice(form.get("unit"), _values(INPUT_UNITS), "unit", errors)
    received_date = _date(form.get("received_date"), "date received", errors)
    source = _choice(form.get("source"), SOURCES, "source", errors)
    notes = _notes(form.get("notes"), errors)
    if input_type == "Other" and not notes:
        errors.append("Describe the input in the notes when you choose Other.")
    if errors:
        return None, errors
    return {
        "input_type": input_type,
        "quantity": quantity,
        "unit": unit,
        "received_date": received_date,
        "source": source,
        "notes": notes,
    }, []


def parse_planting(form):
    """Check the record-planting form."""
    errors = []
    crop = _choice(form.get("crop"), CROPS, "crop", errors)
    field_size = _number(form.get("field_size"), "field size", 0.01, 100000, errors)
    size_unit = _choice(form.get("size_unit"), _values(FIELD_UNITS), "field unit", errors)
    planting_date = _date(form.get("planting_date"), "planting date", errors)
    notes = _notes(form.get("notes"), errors)

    # Reject a lima entry that would be more than 100 hectares (400 lima).
    # A typo like an extra zero is easy when someone is in a hurry.
    if field_size is not None and size_unit in _values(FIELD_UNITS):
        hectares = to_hectares(field_size, size_unit)
        if hectares > 100:
            errors.append(
                "That field is larger than 100 hectares. Check the size and the unit."
            )
    if errors:
        return None, errors
    return {
        "crop": crop,
        "field_size": field_size,
        "size_unit": size_unit,
        "planting_date": planting_date,
        "notes": notes,
    }, []


def parse_harvest(form, planting):
    """Check the record-harvest form.

    planting is the row the officer selected, or None if it is missing
    or belongs to a different farmer.
    """
    errors = []
    if planting is None:
        errors.append("Choose the planting this harvest came from.")
    bags = _number(form.get("bags_50kg"), "number of 50 kg bags", 0, 10000, errors)
    harvest_date = _date(form.get("harvest_date"), "harvest date", errors)
    notes = _notes(form.get("notes"), errors)
    if planting is not None and harvest_date is not None:
        # ISO dates sort correctly as text, so "2025-06-12" is after "2024-11-22".
        if harvest_date < planting["planting_date"]:
            errors.append("The harvest date cannot be before the planting date.")
    if errors:
        return None, errors
    return {
        "planting_id": planting["id"],
        "bags_50kg": bags,
        "harvest_date": harvest_date,
        "notes": notes,
    }, []


def _text(raw, label, max_len, errors):
    text = " ".join((raw or "").split())
    # One letter is not enough for a name, camp, or district.
    if len(text) < 2:
        errors.append(f"Enter the {label}.")
        return None
    if len(text) > max_len:
        errors.append(f"The {label} is too long.")
        return None
    if _has_control_character(text):
        errors.append(f"The {label} contains a character this form cannot store.")
        return None
    return text


def _notes(raw, errors):
    text = " ".join((raw or "").split())
    if not text:
        return None
    if len(text) > 200:
        errors.append("Keep the notes under 200 characters.")
        return None
    if _has_control_character(text):
        errors.append("The notes contain a character this form cannot store.")
        return None
    return text


def _nrc(raw, errors):
    """Accept 123456/78/1, including spaces around the slashes."""
    text = "".join((raw or "").split())
    parts = text.split("/")
    if len(parts) != 3 or not (
        len(parts[0]) == 6
        and len(parts[1]) == 2
        and len(parts[2]) == 1
        and all(part.isdigit() for part in parts)
    ):
        errors.append(f"Enter the NRC like {NRC_EXAMPLE}.")
        return None
    return text


def _phone(raw, errors):
    """Phone is optional. Stored without spaces, starting with 0 or +260."""
    text = "".join((raw or "").split()).replace("-", "")
    if not text:
        return None
    if text.startswith("260") and not text.startswith("+"):
        text = "+" + text
    local = text.startswith("0") and len(text) == 10 and text[1:].isdigit()
    international = (
        text.startswith("+260") and len(text) == 13 and text[1:].isdigit()
    )
    if not (local or international):
        errors.append(
            f"Enter a Zambian phone number like {PHONE_EXAMPLE} or +260971234567."
        )
        return None
    return text


def _choice(raw, allowed, label, errors):
    value = (raw or "").strip()
    if value not in allowed:
        errors.append(f"Choose the {label}.")
        return None
    return value


def _number(raw, label, minimum, maximum, errors):
    text = (raw or "").strip()
    if not text:
        errors.append(f"Enter the {label}.")
        return None
    try:
        value = float(text)
    except ValueError:
        errors.append(
            f"Enter the {label} as a number, using a dot for decimals (for example 2.5)."
        )
        return None
    if math.isnan(value) or math.isinf(value):
        errors.append(f"Enter a real number for the {label}.")
        return None
    if value < minimum:
        errors.append(f"The {label} cannot be less than {format_amount(minimum)}.")
        return None
    if value > maximum:
        errors.append(f"The {label} looks too large. Check the amount.")
        return None
    return round(value, 2)


def _date(raw, label, errors):
    text = (raw or "").strip()
    if not text:
        errors.append(f"Enter the {label}.")
        return None
    try:
        day = date.fromisoformat(text)
    except ValueError:
        errors.append(f"Enter the {label} as a full date.")
        return None
    if day.year < 1990:
        errors.append(f"The {label} is too far in the past.")
        return None
    # date.today() follows the clock on the computer running the app.
    if day > date.today():
        errors.append(f"The {label} cannot be in the future.")
        return None
    return day.isoformat()


def _values(pairs):
    return tuple(value for value, _label in pairs)


def _has_control_character(text):
    return any(ord(character) < 32 for character in text)
