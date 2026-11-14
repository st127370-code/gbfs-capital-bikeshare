"""
Takes ONE snapshot of every Capital Bikeshare station and appends it to data/status_YYYY-MM-DD.csv.
GitHub Actions runs this file every 10 minutes (see .github/workflows/gbfs.yml), so no laptop is needed.
After END_DATE (UTC) it does nothing, so the collection stops by itself.
"""
import csv
import os
from datetime import datetime, timezone

import requests

END_DATE = "2026-11-23"          # last day to collect (UTC); change if you start later
BASE = "https://gbfs.lyft.com/gbfs/2.3/dca-cabi/en/"
COLUMNS = ["poll_time_utc", "station_id", "num_bikes_available", "num_ebikes_available",
           "num_docks_available", "is_installed", "is_renting", "is_returning", "last_reported"]

now = datetime.now(timezone.utc)
if now.strftime("%Y-%m-%d") > END_DATE:
    print("Collection finished; nothing to do.")
    raise SystemExit(0)

os.makedirs("data", exist_ok=True)

# station names, locations and capacity: saved once
if not os.path.exists("data/station_information.csv"):
    info = requests.get(BASE + "station_information.json", timeout=30).json()["data"]["stations"]
    with open("data/station_information.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["station_id", "name", "lat", "lon", "capacity"])
        for s in info:
            w.writerow([s.get("station_id"), s.get("name"), s.get("lat"), s.get("lon"), s.get("capacity")])

stations = requests.get(BASE + "station_status.json", timeout=30).json()["data"]["stations"]
path = f"data/status_{now.strftime('%Y-%m-%d')}.csv"          # one file per day keeps files small
new_file = not os.path.exists(path)
with open(path, "a", newline="") as f:
    w = csv.writer(f)
    if new_file:
        w.writerow(COLUMNS)
    poll_time = now.strftime("%Y-%m-%d %H:%M:%S")
    for s in stations:
        w.writerow([poll_time] + [s.get(c) for c in COLUMNS[1:]])
print(f"Saved {len(stations)} stations to {path}")
