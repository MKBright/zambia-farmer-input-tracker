"""Turn stored values into short text for pages, CSV files, and the terminal."""

from datetime import date

from app.units import INPUT_UNIT_LABELS

MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def format_amount(value):
    """Show 2 as 2, and 0.5 as 0.5, without a long tail of zeros."""
    number = round(float(value), 2)
    if number == int(number):
        return str(int(number))
    text = f"{number:.2f}"
    return text.rstrip("0").rstrip(".")


def format_kg(value):
    """Whole kilograms with a thousands separator, for example 1,800."""
    return f"{int(round(float(value))):,}"


def format_hectares(value):
    """Always two decimal places so 0.5 ha and 1 ha line up as 0.50 and 1.00."""
    return f"{float(value):.2f}"


def human_date(value):
    """Show an ISO date as 22 Nov 2024.

    The month names are written out here so the page does not change
    when the computer's language setting changes.
    """
    if not value:
        return "—"
    try:
        day = date.fromisoformat(str(value)[:10])
    except ValueError:
        return str(value)
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def quantity_phrase(quantity, unit):
    """Describe one input row, for example '2 × 50 kg bag' or '10 kg'."""
    amount = format_amount(quantity)
    if unit == "kg":
        return f"{amount} kg"
    label = INPUT_UNIT_LABELS.get(unit, unit)
    return f"{amount} × {label}"


def area_phrase(field_size, size_unit, size_hectares):
    """Describe a field, keeping the unit the officer originally typed."""
    hectares = format_hectares(size_hectares)
    if size_unit == "lima":
        return f"{format_amount(field_size)} lima ({hectares} ha)"
    return f"{hectares} ha"
