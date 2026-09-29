# AgroLink 2

A local-first farmer community app built with FastAPI, SQLite, and a responsive HTML/CSS/JavaScript frontend. It has a recent-photo feed, likes and comments, farmer profiles, direct messages, a planting planner, crop diagnosis, confirmed nearby disease alerts, and a farm diary.

## Set up on a Windows G: drive

1. Extract the project ZIP to `G:\AgroLink_v2`.
2. Open PowerShell in that folder.
3. Run:

```powershell
cd G:\AgroLink_v2
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Open **http://127.0.0.1:8000**. API documentation is at **http://127.0.0.1:8000/docs**. The SQLite database, uploads, and session key are created under `G:\AgroLink_v2\data`. Keep that folder when updating the app.

For disease classification, first add your trained model files to `G:\AgroLink_v2\models`:

- `Banana_disease.pth`
- `Corn_disease.pth`
- `Grapes_disease.pth`

Then install the optional ML packages:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
```

The loader expects state dictionaries for the CNN defined in `ml.py`: 150 × 150 RGB inputs, three convolution layers (32/64/128 channels), a 256-unit fully connected layer, and four output classes. It uses the exact class order shown in `ml.LABELS`. If your models were saved with another architecture, preprocessing, or class order, update `ml.py` before trusting results. No weights are included in this ZIP.

## How the features work

- **Feed:** newest posts first. Signed-in farmers can share images, captions, crop tags, likes, and comments. The feed is limited to the latest 100 posts in this local version.
- **Planting planner:** choose crops and irrigation status in Profile. KAU-based month windows are included for banana and maize (shown as Corn in the app). A preparation reminder appears in the app during the 30 days before the next window. Grapes show “not verified” rather than an invented date. These are Kerala baseline windows, not a field-specific weather forecast.
- **Disease alerts:** first run a model prediction, then tap **Report suspected disease**. The backend checks farm-to-farm distance with the Haversine formula and creates in-app alerts for other farmers within 5 km. It suppresses repeat alerts for the same crop and disease to a recipient for 48 hours. Set farm coordinates in Profile; a device location can fill them only when you are physically at the farm. Recipients see approximate distance, never exact coordinates. The app must be running and opened to view alerts; browser push and SMS are not implemented.
- **KAU guidance:** a specifically sourced entry is included for banana Sigatoka. Other labels show a clearly marked unverified-guidance state; a prediction alone must not be used to choose treatment. The original model's `Black_Root` grape label is preserved pending verification of its actual meaning.
- **Diary and messages:** each farmer can record dated crop notes and exchange private in-app messages with another signed-in farmer.

## Sources and boundaries

- KAU 2016 *Package of Practices Recommendations: Crops*, Banana/Sigatoka section: https://kau.in/sites/default/files/documents/pop2016.pdf
- KAU banana season: https://pop.kau.in/fruits.htm
- KAU maize season: https://kau.in/book/maize-zea-mays
- IMD district agromet bulletins for current local conditions: https://mausam.imd.gov.in/responsive/agromet_adv_ser_district_current_en.php

KAU guidance is paraphrased and linked, not copied into a full reference book. Consult a local agricultural officer before applying treatments. Weather on the top bar uses wttr.in when network access is available; planting dates do not automatically shift based on that weather string.

This version is suitable for local development and demonstrations. Before public deployment, add HTTPS, stronger account recovery, production session settings, content moderation, scheduled notifications, database backups, and deployment-specific storage. Do not expose the local server to the public internet as-is.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install pytest httpx
.\.venv\Scripts\python.exe -m pytest -q
```

The tests cover registration, login, feed, likes, comments, profiles, planner, diary, messages, upload validation, and alert radius/deduplication with a mocked model result. They do not validate your actual `.pth` weights.
