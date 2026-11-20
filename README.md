# Farm Input Tracker

A small local web app for recording farming inputs, planting dates, and harvests for small-scale farmers in Zambia.

I am Wankumbu Musunga, a second-year BSc Computer Science student studying by distance in Lusaka. I built this while looking for entry-level IT work. The job skills I practised here are careful data entry, checking that figures add up, and writing a small Python program that someone else can run.

The people in the sample data are fictional. The districts and camps are real places.

## The problem it solves in Zambia

Most small-scale farmers grow rain-fed maize, and many also grow groundnuts or soybeans. A lot of them receive subsidised seed and fertilizer through the Farmer Input Support Programme (FISP). A common maize pack has been one 10 kg bag of seed, two 50 kg bags of D-Compound (basal fertilizer, applied around planting), and two 50 kg bags of Urea (top dressing, applied later). Packs change from season to season, and many farmers also buy extra inputs themselves.

Camp extension officers often keep those records in a paper notebook: who in the camp received FISP inputs, how big the field was, and how many bags were harvested. A field is often described in **lima** rather than hectares. At a district meeting it is hard to answer a simple question from that notebook: what was the yield per hectare, and which inputs were actually used?

This tool is a record book on one computer. It does not replace the official FISP system. It helps an officer (or a farmer keeping their own notes) store the records and calculate the yield.

## Features

- Register a farmer: full name, NRC-style number (`123456/78/1`), agricultural camp, district, and an optional Zambian phone number.
- Record inputs received: type (maize seed, D-Compound, Urea, and others), quantity in kilograms or in 10 kg / 50 kg bags, date, and source (FISP, own purchase, cooperative, or an NGO / project).
- Record a planting: crop (maize, groundnuts, soybeans, and a few others), field size in hectares or lima, and the planting date. One lima is stored as 0.25 hectares. The page still shows the lima figure that was typed.
- Record a harvest in 50 kg bags, linked to the planting it came from. A second harvest can be added if the crop was taken in parts. Zero bags means the crop failed.
- Summary for one farmer and for a district: area planted, bags harvested, yield in kilograms per hectare, and inputs used (converted to kilograms).
- A comparison of districts on one page.
- CSV export of the raw records and of the farmer and district summaries, for Excel or LibreOffice.
- Sample farmers and pytest tests.

Yield uses only fields that already have a harvest. A field with no harvest yet is not treated as a zero. A written harvest of 0 bags is a failed crop and stays in the average.

```
yield (kg/ha) = (number of 50 kg bags × 50) / harvested hectares
```

Mwansa Banda in the sample harvested 18 bags from 0.5 hectares:

```
18 × 50 = 900 kg
900 / 0.5 = 1,800 kg/ha
```

## Setup and run

You need Python 3.10 or newer. These steps were run with Python 3.12.

**macOS or Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_sample_data.py
python run.py
```

**Windows**

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/seed_sample_data.py
python run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The app listens only on this computer.

If port 5000 is busy:

```bash
PORT=5001 python run.py
```

The database file is `data/farm_tracker.db`. Copy that file if you want a backup. Stop the app before you run the sample script again. The script replaces that file, including any farmers you added.

Run the tests from the project folder (the server does not need to be running):

```bash
pytest
```

## Sample output

After `python scripts/seed_sample_data.py`, the script prints the summary below. The home page then shows **5 farmers**, **14 input records**, **4.75 hectares** planted, and **130** bags of 50 kg.

On Mwansa Banda’s page the maize yield is **1,800 kg/ha**. The Chongwe district report shows both Chongwe maize farmers together: 40 bags from 1.00 hectare, which is **2,000 kg/ha**. Three of the five sample farmers received at least one FISP input.

```
Farm Input Tracker — sample summary

Farmers: 5
Districts: Chibombo, Chongwe, Kafue, Mazabuka

Bupe Mulenga (Chongwe / Chalimbana)
  NRC: 301992/11/1
  Inputs: D-Compound 100 kg; Maize seed 10 kg; Urea 150 kg
  Maize: 0.50 ha planted, 22 x 50 kg bags, yield 2200 kg/ha

Joseph Tembo (Mazabuka / Magoye)
  NRC: 512003/17/1
  Inputs: D-Compound 100 kg; Soybean seed 25 kg
  Soybeans: 1.50 ha planted, 30 x 50 kg bags, yield 1000 kg/ha

Mutinta Zulu (Chibombo / Chisamba Camp)
  NRC: 229410/43/1
  Inputs: D-Compound 100 kg; Groundnut seed 5 kg; Maize seed 10 kg; Urea 100 kg
  Groundnuts: 0.25 ha planted, 4 x 50 kg bags, yield 800 kg/ha
  Maize: 1.00 ha planted, 40 x 50 kg bags, yield 2000 kg/ha

Mwansa Banda (Chongwe / Kanakantapa)
  NRC: 234511/10/1
  Inputs: D-Compound 100 kg; Maize seed 10 kg; Urea 100 kg
  Maize: 0.50 ha planted, 18 x 50 kg bags, yield 1800 kg/ha

Natasha Phiri (Kafue / Shimabala)
  NRC: 448120/15/1
  Inputs: Groundnut seed 20 kg
  Groundnuts: 1.00 ha planted, 16 x 50 kg bags, yield 800 kg/ha

--- By district ---

All districts
  Farmers: 5
  FISP farmers: 3
  Groundnuts: 1.25 ha planted, 20 x 50 kg bags, yield 800 kg/ha
  Maize: 2.00 ha planted, 80 x 50 kg bags, yield 2000 kg/ha
  Soybeans: 1.50 ha planted, 30 x 50 kg bags, yield 1000 kg/ha
  Inputs: D-Compound 400 kg; Groundnut seed 25 kg; Maize seed 30 kg; Soybean seed 25 kg; Urea 350 kg

Chibombo
  Farmers: 1
  FISP farmers: 1
  Groundnuts: 0.25 ha planted, 4 x 50 kg bags, yield 800 kg/ha
  Maize: 1.00 ha planted, 40 x 50 kg bags, yield 2000 kg/ha
  Inputs: D-Compound 100 kg; Groundnut seed 5 kg; Maize seed 10 kg; Urea 100 kg

Chongwe
  Farmers: 2
  FISP farmers: 2
  Maize: 1.00 ha planted, 40 x 50 kg bags, yield 2000 kg/ha
  Inputs: D-Compound 200 kg; Maize seed 20 kg; Urea 250 kg

Kafue
  Farmers: 1
  FISP farmers: 0
  Groundnuts: 1.00 ha planted, 16 x 50 kg bags, yield 800 kg/ha
  Inputs: Groundnut seed 20 kg

Mazabuka
  Farmers: 1
  FISP farmers: 0
  Soybeans: 1.50 ha planted, 30 x 50 kg bags, yield 1000 kg/ha
  Inputs: D-Compound 100 kg; Soybean seed 25 kg
```

Bupe’s field was entered as **2 lima**. The report shows 0.50 ha, because 2 × 0.25 = 0.50. Bupe also bought one extra 50 kg bag of Urea, so the Urea total is 150 kg rather than the 100 kg FISP pack.

## Project structure

```
app/
  __init__.py          builds the Flask app and opens the database
  db.py                SQLite connection and the four tables
  units.py             lima, bag sizes, crops, and input types
  validation.py        checks each form before anything is saved
  records.py           saves and loads farmers, inputs, plantings, harvests
  reports.py           yield per hectare and district totals
  csv_export.py        CSV downloads
  formatting.py        dates and numbers shown on the page
  sample_data.py       the fictional farmers
  routes.py            the web pages
  templates/           HTML
  static/style.css     layout, no internet fonts
scripts/seed_sample_data.py
tests/                 pytest, using a temporary database
run.py                 starts the app on http://127.0.0.1:5000
requirements.txt
pytest.ini
LICENSE                MIT
```

SQL uses `?` placeholders, so a farmer’s name cannot change the query. Adding a crop or an input type is a one-line change in `app/units.py`.

## What I learned

- I split the work into small functions: check the form, save the row, then add up the report. The pages and the sample-data script call the same functions, so there is one place that calculates yield.
- I store the field size twice. One column is what the officer typed (for example 4 lima). The other is hectares, which the report adds up. The page can still say “4 lima” later.
- Yield is harvested kilograms divided by harvested hectares. Leaving out a field that has no harvest yet took a real decision. An empty harvest box is not the same thing as a failed crop.
- pytest can point the app at a temporary database, so the tests never touch the sample file.
- A name that looks like a SQL command is stored as ordinary text. I also prefix CSV cells that start with `=` so a spreadsheet does not treat a name as a formula.
- The NRC check only looks at the shape (`123456/78/1`). It cannot tell whether the card was issued. The two digits in the middle are the district where the card was issued, which may not be the district where the farmer grows maize.

## Future ideas

- **SMS or USSD access.** Many farmers have a basic phone rather than a smartphone or a computer. A short code could let someone send a planting date or ask what was recorded, the way other Zambian services are reached with `*123#`-style menus.
- **Offline mobile app for camp officers.** Officers travel between fields, and the network drops. An app could take records with no signal and sync when the phone next has data.
- Labels in Chichewa, Bemba, Tonga, and other languages used in the camps.
- A season filter, such as 2024/25, so last year is not mixed with this year.
- A login if several officers share one computer, and a reminder to back up the SQLite file.

## Licence

MIT. See [LICENSE](LICENSE).
