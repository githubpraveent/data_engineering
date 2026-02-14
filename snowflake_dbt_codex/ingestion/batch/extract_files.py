import json
import os
from pathlib import Path


DATA_DIR = Path(os.getenv("FILE_LANDING_DIR", "./data/landing"))


def extract_files():
    payloads = []
    if not DATA_DIR.exists():
        return payloads

    for path in DATA_DIR.glob("**/*"):
        if path.is_dir():
            continue
        if path.suffix.lower() == ".csv":
            payloads.append({"type": "csv", "path": str(path)})
        elif path.suffix.lower() in {".json", ".ndjson"}:
            payloads.append({"type": "json", "path": str(path)})
    return payloads
