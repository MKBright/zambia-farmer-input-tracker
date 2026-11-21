"""Fictional farmers used by scripts/seed_sample_data.py.

The people, NRC numbers, and phone numbers are made up. The districts
and camps are real places, so the sample looks like a notebook from
farms around Lusaka and the maize belt.

The harvest numbers are round on purpose. A reader can check the yield
by hand: bags × 50 kg, divided by the hectares.

FISP maize packs in recent seasons have often been one 10 kg bag of seed,
two 50 kg bags of D-Compound, and two 50 kg bags of Urea, aimed at about
half a hectare. Packs change, so these rows are only an example.
"""

from app.records import insert_farmer, insert_harvest, insert_input, insert_planting

SAMPLE_FARMERS = (
    {
        "full_name": "Mwansa Banda",
        "nrc": "234511/10/1",
        "camp": "Kanakantapa",
        "district": "Chongwe",
        "phone": "0971001001",
        "inputs": (
            {
                "input_type": "Maize seed",
                "quantity": 10,
                "unit": "kg",
                "received_date": "2024-11-10",
                "source": "FISP",
                "notes": "Variety note: MRI 634",
            },
            {
                "input_type": "D-Compound",
                "quantity": 2,
                "unit": "bag50",
                "received_date": "2024-11-10",
                "source": "FISP",
                "notes": None,
            },
            {
                "input_type": "Urea",
                "quantity": 2,
                "unit": "bag50",
                "received_date": "2024-11-10",
                "source": "FISP",
                "notes": None,
            },
        ),
        "plantings": (
            {
                "crop": "Maize",
                "field_size": 0.5,
                "size_unit": "hectares",
                "planting_date": "2024-11-22",
                "notes": None,
                "harvests": (
                    {"bags_50kg": 18, "harvest_date": "2025-06-12", "notes": None},
                ),
            },
        ),
    },
    {
        "full_name": "Bupe Mulenga",
        "nrc": "301992/11/1",
        "camp": "Chalimbana",
        "district": "Chongwe",
        "phone": "0961001002",
        "inputs": (
            {
                "input_type": "Maize seed",
                "quantity": 10,
                "unit": "kg",
                "received_date": "2024-11-18",
                "source": "FISP",
                "notes": None,
            },
            {
                "input_type": "D-Compound",
                "quantity": 2,
                "unit": "bag50",
                "received_date": "2024-11-18",
                "source": "FISP",
                "notes": None,
            },
            {
                "input_type": "Urea",
                "quantity": 2,
                "unit": "bag50",
                "received_date": "2024-11-18",
                "source": "FISP",
                "notes": None,
            },
            {
                "input_type": "Urea",
                "quantity": 1,
                "unit": "bag50",
                "received_date": "2024-12-20",
                "source": "Own purchase",
                "notes": "Extra top dressing, not part of the FISP pack",
            },
        ),
        "plantings": (
            {
                # 2 lima is 0.5 hectares. The report should show 0.50 ha.
                "crop": "Maize",
                "field_size": 2,
                "size_unit": "lima",
                "planting_date": "2024-12-02",
                "notes": None,
                "harvests": (
                    {"bags_50kg": 22, "harvest_date": "2025-06-20", "notes": None},
                ),
            },
        ),
    },
    {
        "full_name": "Natasha Phiri",
        "nrc": "448120/15/1",
        "camp": "Shimabala",
        "district": "Kafue",
        "phone": "0951001003",
        "inputs": (
            {
                "input_type": "Groundnut seed",
                "quantity": 20,
                "unit": "kg",
                "received_date": "2024-11-28",
                "source": "Own purchase",
                "notes": None,
            },
        ),
        "plantings": (
            {
                "crop": "Groundnuts",
                "field_size": 1,
                "size_unit": "hectares",
                "planting_date": "2024-12-05",
                "notes": None,
                "harvests": (
                    {"bags_50kg": 16, "harvest_date": "2025-05-28", "notes": None},
                ),
            },
        ),
    },
    {
        "full_name": "Joseph Tembo",
        "nrc": "512003/17/1",
        "camp": "Magoye",
        "district": "Mazabuka",
        "phone": "0971001004",
        "inputs": (
            {
                "input_type": "Soybean seed",
                "quantity": 25,
                "unit": "kg",
                "received_date": "2024-12-01",
                "source": "Own purchase",
                "notes": None,
            },
            {
                "input_type": "D-Compound",
                "quantity": 2,
                "unit": "bag50",
                "received_date": "2024-12-01",
                "source": "Own purchase",
                "notes": None,
            },
        ),
        "plantings": (
            {
                "crop": "Soybeans",
                "field_size": 1.5,
                "size_unit": "hectares",
                "planting_date": "2024-12-10",
                "notes": None,
                "harvests": (
                    {"bags_50kg": 30, "harvest_date": "2025-06-05", "notes": None},
                ),
            },
        ),
    },
    {
        "full_name": "Mutinta Zulu",
        "nrc": "229410/43/1",
        "camp": "Chisamba Camp",
        "district": "Chibombo",
        "phone": "0761001005",
        "inputs": (
            {
                "input_type": "Maize seed",
                "quantity": 10,
                "unit": "kg",
                "received_date": "2024-11-15",
                "source": "FISP",
                "notes": None,
            },
            {
                "input_type": "D-Compound",
                "quantity": 2,
                "unit": "bag50",
                "received_date": "2024-11-15",
                "source": "FISP",
                "notes": None,
            },
            {
                "input_type": "Urea",
                "quantity": 2,
                "unit": "bag50",
                "received_date": "2024-11-15",
                "source": "FISP",
                "notes": None,
            },
            {
                "input_type": "Groundnut seed",
                "quantity": 5,
                "unit": "kg",
                "received_date": "2024-12-01",
                "source": "Own purchase",
                "notes": "Seed for 1 lima",
            },
        ),
        "plantings": (
            {
                "crop": "Maize",
                "field_size": 4,
                "size_unit": "lima",
                "planting_date": "2024-11-28",
                "notes": None,
                "harvests": (
                    {"bags_50kg": 40, "harvest_date": "2025-06-18", "notes": None},
                ),
            },
            {
                "crop": "Groundnuts",
                "field_size": 1,
                "size_unit": "lima",
                "planting_date": "2024-12-08",
                "notes": None,
                "harvests": (
                    {"bags_50kg": 4, "harvest_date": "2025-05-30", "notes": None},
                ),
            },
        ),
    },
)


def seed_database(connection):
    """Insert every sample farmer. Returns how many rows were written."""
    counts = {"farmers": 0, "inputs": 0, "plantings": 0, "harvests": 0}
    for entry in SAMPLE_FARMERS:
        farmer_id = insert_farmer(
            connection,
            {
                "full_name": entry["full_name"],
                "nrc": entry["nrc"],
                "camp": entry["camp"],
                "district": entry["district"],
                "phone": entry["phone"],
            },
        )
        counts["farmers"] += 1
        for item in entry["inputs"]:
            insert_input(connection, farmer_id, item)
            counts["inputs"] += 1
        for planting in entry["plantings"]:
            planting_id = insert_planting(
                connection,
                farmer_id,
                {
                    "crop": planting["crop"],
                    "field_size": planting["field_size"],
                    "size_unit": planting["size_unit"],
                    "planting_date": planting["planting_date"],
                    "notes": planting["notes"],
                },
            )
            counts["plantings"] += 1
            for harvest in planting["harvests"]:
                insert_harvest(
                    connection,
                    {
                        "planting_id": planting_id,
                        "bags_50kg": harvest["bags_50kg"],
                        "harvest_date": harvest["harvest_date"],
                        "notes": harvest["notes"],
                    },
                )
                counts["harvests"] += 1
    return counts
