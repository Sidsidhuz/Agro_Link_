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
    return {
        "crop": crop, "supported": True, "method": kind,
        "start": start.isoformat(), "end": end.isoformat(),
        "days_until": days, "in_window": start <= today <= end,
        "prepare_now": days <= 30,
        "note": rule["note"], "source": rule["source"],
    }
