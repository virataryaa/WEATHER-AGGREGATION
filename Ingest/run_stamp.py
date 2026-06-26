"""Shared helper — writes source timestamps to Database/last_run.json."""
import json
import os
from datetime import datetime

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP_FILE = os.path.join(BASE, "Database", "last_run.json")


def stamp(source: str):
    data = {}
    if os.path.exists(STAMP_FILE):
        try:
            with open(STAMP_FILE) as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[source] = datetime.now().strftime("%d %b  %H:%M")
    with open(STAMP_FILE, "w") as f:
        json.dump(data, f, indent=2)
