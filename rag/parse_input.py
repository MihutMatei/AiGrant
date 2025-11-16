# rag/parse_input.py

from pathlib import Path
import json
from typing import List, Any


# Base paths (aligned with your existing project structure)
BASE_DIR = Path(__file__).resolve().parents[1]
SCRAPER_OUTPUT_DIR = BASE_DIR / "scraper" / "output"
DATA_DIR = BASE_DIR / "data" / "opportunities"

# Combined output for RAG
OUTPUT_FILE = DATA_DIR / "sources.json"


def load_json_file(path: Path) -> Any:
    """Load a JSON file and return its parsed content."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def collect_objects_from_dir(dir_path: Path) -> List[dict]:
    """
    Collect JSON objects from all .json files in a directory.

    Supports:
    - Files that contain a single JSON object (dict)
    - Files that contain a list of JSON objects
    """
    objects: List[dict] = []

    if not dir_path.exists():
        print(f"[WARN] Directory not found: {dir_path}")
        return objects

    for json_file in dir_path.glob("*.json"):
        try:
            data = load_json_file(json_file)
        except Exception as e:
            print(f"[ERROR] Failed to load {json_file}: {e}")
            continue

        if isinstance(data, list):
            objects.extend(data)
        elif isinstance(data, dict):
            objects.append(data)
        else:
            print(f"[WARN] Unexpected JSON structure in {json_file}: {type(data)}")

    return objects


def build_combined_sources() -> dict:
    """
    Read all scraper outputs and build a combined structure:

    {
        "grants": [...],
        "vcs": [...],
        "accelerators": [...]
    }
    """
    grants_dir = SCRAPER_OUTPUT_DIR / "grants"
    vcs_dir = SCRAPER_OUTPUT_DIR / "vcs"
    acc_dir = SCRAPER_OUTPUT_DIR / "accelerators"

    print(f"[INFO] Reading grants from: {grants_dir}")
    grants = collect_objects_from_dir(grants_dir)

    print(f"[INFO] Reading VCs from: {vcs_dir}")
    vcs = collect_objects_from_dir(vcs_dir)

    print(f"[INFO] Reading accelerators from: {acc_dir}")
    accelerators = collect_objects_from_dir(acc_dir)

    combined = {
        "grants": grants,
        "vcs": vcs,
        "accelerators": accelerators,
    }

    print(
        f"[INFO] Collected {len(grants)} grants, "
        f"{len(vcs)} VCs, {len(accelerators)} accelerators."
    )

    return combined


def save_combined_sources(data: dict, output_path: Path) -> None:
    """Save the combined data to a single JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Combined sources written to: {output_path}")


def main():
    combined = build_combined_sources()
    save_combined_sources(combined, OUTPUT_FILE)


if __name__ == "__main__":
    main()
