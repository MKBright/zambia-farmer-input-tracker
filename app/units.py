"""Units and fixed choices used on Zambian smallholder farms.

A lima is the field measure many farmers use when they talk to a camp
officer. This tool treats 1 lima as 0.25 hectares, which is the same as
a 50 metre by 50 metre plot. Four lima is one hectare.

Fertilizer is sold in 50 kg bags. A Farmer Input Support Programme (FISP)
maize seed pack is often 10 kg, so seed can be entered in kilograms or
as a 10 kg bag. The program pack changes from season to season, which is
why this tool stores whatever was actually received instead of assuming
one fixed pack.

D-Compound is a basal fertilizer (it contains phosphorus) applied around
planting. Urea is a nitrogen fertilizer, usually applied later as a top
dressing.
"""

# Internal code, then the words shown on the form.
INPUT_UNITS = (
    ("kg", "kilograms (kg)"),
    ("bag10", "10 kg bag"),
    ("bag50", "50 kg bag"),
)

FIELD_UNITS = (
    ("hectares", "hectares"),
    ("lima", "lima (1 lima = 0.25 ha)"),
)

# Add a crop here and it shows up on the planting form.
CROPS = (
    "Maize",
    "Groundnuts",
    "Soybeans",
    "Mixed beans",
    "Sunflower",
)

# Add an input here and it shows up on the input form.
INPUT_TYPES = (
    "Maize seed",
    "Groundnut seed",
    "Soybean seed",
    "D-Compound",
    "Urea",
    "Lime",
    "Other",
)

SOURCES = (
    "FISP",
    "Own purchase",
    "Cooperative",
    "NGO / project",
)

# How many kilograms one entered unit represents.
KG_PER_UNIT = {
    "kg": 1,
    "bag10": 10,
    "bag50": 50,
}

# Multiply a field size by this to store hectares.
HECTARES_PER_UNIT = {
    "hectares": 1,
    "lima": 0.25,
}

# Harvests are always counted in the usual grain bag.
BAG_WEIGHT_KG = 50

INPUT_UNIT_LABELS = dict(INPUT_UNITS)
FIELD_UNIT_LABELS = dict(FIELD_UNITS)


def kilograms_for(quantity, unit):
    """Convert an entered quantity to kilograms.

    Two 50 kg bags become 100. Ten kilograms stay 10.
    """
    if unit not in KG_PER_UNIT:
        raise ValueError(f"Unknown input unit: {unit}")
    return round(float(quantity) * KG_PER_UNIT[unit], 2)


def to_hectares(size, unit):
    """Convert a field size to hectares.

    The original number and unit are stored as well, so the page can still
    say "4 lima" after the report has used 1.00 hectare.
    """
    if unit not in HECTARES_PER_UNIT:
        raise ValueError(f"Unknown field unit: {unit}")
    return round(float(size) * HECTARES_PER_UNIT[unit], 4)
