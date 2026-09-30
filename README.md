<p align="center">
  <img src="static/agrolink-icon.png" alt="AgroLink logo" width="132">
</p>

<h1 align="center">AgroLink</h1>

<p align="center"><strong>A digital farm community for sharing knowledge, planning seasons, and protecting nearby crops.</strong></p>

<p align="center">
  <a href="https://www.python.org/"><img alt="Python 3.11+" src="https://img.shields.io/badge/Python-3.11%2B-285A40?style=flat-square&amp;logo=python&amp;logoColor=white"></a>
  <a href="https://fastapi.tiangolo.com/"><img alt="FastAPI async" src="https://img.shields.io/badge/FastAPI-async-285A40?style=flat-square&amp;logo=fastapi&amp;logoColor=white"></a>
  <a href="https://www.sqlalchemy.org/"><img alt="SQLAlchemy 2.x" src="https://img.shields.io/badge/SQLAlchemy-2.x-D5EAB4?style=flat-square&amp;logo=sqlalchemy&amp;logoColor=173F30"></a>
  <a href="#testing"><img alt="6 tests passing" src="https://img.shields.io/badge/tests-6%20passing-D5EAB4?style=flat-square&amp;logo=pytest&amp;logoColor=173F30"></a>
</p>

<p align="center">
  <a href="#features">Features</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#crop-diagnosis-models">ML setup</a> ·
  <a href="#privacy-and-safety">Safety</a>
</p>

---

AgroLink brings the practical parts of farm life into one calm, responsive workspace. Farmers can share field updates, follow planting windows, examine crop symptoms, receive nearby disease alerts, keep a diary, and talk directly with other growers.

The application is designed for the Kerala farming context, with a forest-inspired interface, source-linked agricultural guidance, map-based farm location selection, and weather-aware planning.

## Features

| Area | What AgroLink provides |
| --- | --- |
| **Community feed** | Photo-led farm posts, crop tags, observations, likes, comments, farmer profiles, and search. |
| **Seasonal planner** | A visual month calendar with planting windows, soil-preparation tasks, planting-material reminders, irrigation or drainage checks, and closing-window warnings. |
| **Weather-aware dates** | Up to 16 days of real rain probability, expected precipitation, and temperature data from Open-Meteo. |
| **Crop diagnosis** | Optional local PyTorch models for Banana, Corn, and Grapes, followed by clearly labelled guidance rather than an unsafe definitive diagnosis. |
| **Nearby alerts** | Farmers can report a suspected disease after analysis; signed-in farmers within 5 km receive an in-app warning without seeing the exact farm coordinates. |
| **Farm diary** | Private, dated crop notes for observations and completed field work. |
| **Messages** | Direct in-app conversations between members of the farm community. |
| **Responsive interface** | Desktop sidebar, mobile bottom navigation, accessible touch targets, reduced-motion support, and a closable post composer. |

## Product principles

- **Useful before impressive:** every screen should help a farmer make or record a decision.
- **Source-backed guidance:** unsupported crops show that guidance is unavailable instead of displaying invented dates or treatment advice.
- **Privacy by default:** phone numbers and exact farm coordinates remain private.
- **Honest predictions:** crop analysis is presented as a suggestion that should be confirmed by a local agricultural officer.
- **Resilient operation:** network-dependent information fails safely while local community and diary data remain available.

## Technology

- **Backend:** Python, FastAPI, Pydantic Settings
- **Data layer:** SQLAlchemy `AsyncSession`, SQLite for local development, PostgreSQL-ready configuration
- **Frontend:** semantic HTML, responsive CSS, and framework-free JavaScript
- **Maps:** Leaflet with OpenStreetMap tiles
- **Weather:** wttr.in for the header summary and Open-Meteo for dated planner forecasts
- **Machine learning:** optional PyTorch and torchvision crop classifiers
- **Testing:** pytest and FastAPI TestClient

## Quick start

### 1. Clone and enter the project

```powershell
git clone https://github.com/Sidsidhuz/Agro_Link_.git
cd Agro_Link_
```

### 2. Create a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux, activate it with `source .venv/bin/activate`.

### 3. Install the application

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configure the environment

```powershell
Copy-Item .env.example .env
```

The development defaults work locally. Before production, set a strong authentication secret, secure cookies, explicit CORS origins, and a production database URL.

### 5. Run AgroLink

```powershell
python -m uvicorn main:app --reload
```

Open:

- Application: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Interactive API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

The SQLite database, uploaded images, and generated session key are stored under `data/`. Preserve this directory when moving or updating an existing local installation.

## Configuration

Settings are loaded through Pydantic Settings. Nested values use a double underscore:

```dotenv
AGROLINK_ENVIRONMENT=development
AGROLINK_DATABASE__URL=sqlite+aiosqlite:///data/agrolink.db
AGROLINK_DATABASE__POOL_SIZE=5
AGROLINK_DATABASE__MAX_OVERFLOW=5
AGROLINK_DATABASE__POOL_TIMEOUT=30
AGROLINK_DATABASE__POOL_RECYCLE=1800
AGROLINK_AUTH__SECRET=replace-with-a-long-random-secret
AGROLINK_AUTH__SECURE_COOKIE=false
AGROLINK_CORS_ORIGINS=[]
```

Production mode refuses to start with a missing or short secret, insecure cookies, or wildcard credentialed CORS.

## Crop diagnosis models

Diagnosis is optional. The rest of AgroLink works without the ML dependencies.

Install the additional packages:

```powershell
python -m pip install -r requirements-ml.txt
```

Place the trained weights in `models/` using these filenames:

```text
models/
├── Banana_disease.pth
├── Corn_disease.pth
└── Grapes_disease.pth
```

The loader in `ml.py` expects state dictionaries for its defined CNN: 150 × 150 RGB inputs, convolution layers with 32, 64, and 128 channels, a 256-unit fully connected layer, and the exact output-class order in `ml.LABELS`.

If a model was trained with different preprocessing, architecture, or class ordering, update `ml.py` before using its results. Model confidence is not medical-style certainty and should not be treated as confirmation of a crop disease.

## Architecture

AgroLink separates HTTP concerns, validation, business logic, and database access:

```text
AgroLink/
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── v1/endpoints/     # HTTP route definitions
│   ├── core/                 # settings, database, errors, security foundations
│   ├── models/               # SQLAlchemy models
│   ├── repositories/         # database queries
│   ├── schemas/              # Pydantic request/response models
│   ├── services/             # application business logic
│   └── main.py               # FastAPI application factory
├── data/                     # local database and uploads; ignored by Git
├── docs/architecture.md      # migration and architecture notes
├── migrations/              # Alembic configuration
├── models/                   # optional ML weights; ignored by Git
├── static/                   # responsive web interface and brand assets
├── tests/                    # integration and foundation tests
├── main.py                   # local entry point and static mounts
├── planner.py                # source-backed crop windows and scheduled tasks
└── ml.py                     # optional model loading and inference
```

Both `/api/v1` and the compatibility alias `/api` are available. New integrations should prefer `/api/v1`.

For more detail, see [`docs/architecture.md`](docs/architecture.md).

## Planner and weather behavior

The planner currently includes verified Kerala planting-window rules for Banana and Corn. Unsupported crops, including Grapes, display an explicit unavailable state.

Each supported window generates practical calendar milestones:

1. Prepare soil.
2. Arrange planting material.
3. Inspect drainage or check irrigation.
4. Open the planting window.
5. Check soil moisture or irrigate young plants.
6. Warn when the window is closing.

Open-Meteo forecasts are limited to the dates returned by the provider—currently up to 16 days. AgroLink sends the saved **town name** for geocoding and then uses the town-centre coordinates for weather. Exact farm coordinates are never sent to the forecast provider. Forecasts are cached for 30 minutes and are never extrapolated into future months.

## Nearby disease alerts

Alerts are deliberately conservative:

1. A farmer runs a crop analysis.
2. The farmer chooses whether to report the suspected result.
3. AgroLink calculates distance using the Haversine formula.
4. Signed-in farmers within 5 km receive an in-app alert.
5. Repeat alerts for the same crop and suspected disease are suppressed for 48 hours.

Recipients see approximate distance only. They never receive the reporting farm’s coordinates.

## Privacy and safety

- Passwords are stored as hashes, not plaintext.
- Session cookies are HTTP-only and support secure production configuration.
- Phone numbers and exact farm coordinates are private.
- Uploaded files are validated and stored locally in development.
- API errors use consistent JSON responses without exposing Python or database traces.
- Diagnosis and community disease reports are suggestions, not professional confirmation.

Before deploying publicly, add HTTPS termination, database backups, durable object storage, account recovery, content moderation, CSRF protection, production rate limiting, and scheduled notification infrastructure.

## Testing

```powershell
python -m pytest -q
```

The suite covers account flows, versioned API aliases, feed interactions, upload validation, profiles, diary entries, messaging, planting rules, asynchronous session rollback, alert distance and deduplication, and safe error responses.

Actual `.pth` model quality is outside the automated test suite and must be evaluated separately against representative agricultural validation data.

## Agricultural references

- [KAU Package of Practices Recommendations: Crops (2016)](https://kau.in/sites/default/files/documents/pop2016.pdf)
- [KAU banana cultivation guidance](https://pop.kau.in/fruits.htm)
- [KAU maize cultivation guidance](https://kau.in/book/maize-zea-mays)
- [IMD district agrometeorological advisories](https://mausam.imd.gov.in/responsive/agromet_adv_ser_district_current_en.php)
- [Open-Meteo forecast API](https://open-meteo.com/en/docs)

Agricultural guidance in AgroLink is paraphrased and linked to its source. Always verify field conditions and consult a qualified local agricultural officer before applying treatment.

---

<div align="center">
  <strong>AgroLink</strong><br>
  Built for farms that grow stronger together.
</div>
