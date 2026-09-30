"""Source-backed Kerala planting windows. Unsupported crops show no invented dates."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

# Month ranges are inclusive. Regional weather and field conditions can shift dates.
WINDOWS = {
    "Banana": {
        "rainfed": [(4, 5)],
        "irrigated": [(8, 9)],
        "source": "https://pop.kau.in/fruits.htm",
        "note": "Avoid heavy monsoon and severe summer; adjust to local conditions.",
    },
    "Corn": {
        "rainfed": [(6, 7), (8, 9)],
        "irrigated": [(1, 2)],
        "source": "https://kau.in/book/maize-zea-mays",
        "note": "Maize guidance is listed as rainfed and irrigated sowing seasons.",
    },
}


def next_window(crop: str, irrigated: bool, today: date | None = None):
    today = today or datetime.now(ZoneInfo("Asia/Kolkata")).date()
    rule = WINDOWS.get(crop)
    if not rule:
        return {"crop": crop, "supported": False, "message": "No verified KAU planting window in this version."}
    kind = "irrigated" if irrigated else "rainfed"
    options = []
    for year in (today.year, today.year + 1):
        for first, last in rule[kind]:
            start = date(year, first, 1)
            end = date(year + (last == 12), last % 12 + 1, 1) - timedelta(days=1)
            if end >= today:
                options.append((start, end))
    start, end = min(options)
    days = max(0, (start - today).days)
    task_specs = [
        (start - timedelta(days=21), "Prepare soil", "Loosen the soil, add organic matter, and clear weeds.", "soil"),
        (start - timedelta(days=14), "Arrange planting material", f"Confirm healthy {crop.lower()} planting material is ready.", "materials"),
        (start - timedelta(days=7), "Check irrigation" if irrigated else "Inspect field drainage", "Test the irrigation route before planting." if irrigated else "Clear drainage channels before seasonal rain.", "water"),
        (start, "Planting window opens", f"Begin {crop.lower()} planting when local field conditions are suitable.", "plant"),
        (start + timedelta(days=7), "Irrigation reminder" if irrigated else "Check soil moisture", "Water young plants according to soil moisture." if irrigated else "Inspect moisture around new plants after the first week.", "water"),
        (end - timedelta(days=7), "Planting window closing", "Complete planting soon or confirm updated local guidance.", "warning"),
    ]
    tasks = [
        {"date": task_date.isoformat(), "title": title, "details": details, "kind": task_kind}
        for task_date, title, details, task_kind in task_specs
    ]
    return {
        "crop": crop, "supported": True, "method": kind,
        "start": start.isoformat(), "end": end.isoformat(),
        "days_until": days, "in_window": start <= today <= end,
        "prepare_now": days <= 30,
        "note": rule["note"], "source": rule["source"], "tasks": tasks,
    }
