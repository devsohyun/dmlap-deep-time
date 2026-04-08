"""
manifest.py
Shared utility for reading/writing manifest.json.
All scrapers import from here — never write manifest.json directly.

manifest.json is a JSON lines file (one record per line) for safe concurrent appends.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from config import DATASET_ROOT

MANIFEST_PATH = Path(DATASET_ROOT) / "manifest.json"


def load_manifest() -> list[dict]:
    """Load all entries from manifest.json. Returns empty list if file doesn't exist."""
    if not MANIFEST_PATH.exists():
        return []
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)


def save_manifest(entries: list[dict]):
    """Write full manifest back to disk."""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(entries, f, indent=2)


def add_to_manifest(entry: dict):
    """Append a single entry to the manifest. Skips if path already registered."""
    entries = load_manifest()
    existing_paths = {e["path"] for e in entries}

    if entry["path"] in existing_paths:
        return  # already registered

    entry["registered_at"] = datetime.now(timezone.utc).isoformat()
    entries.append(entry)
    save_manifest(entries)


def already_downloaded(filepath: Path) -> bool:
    """Check if a file path is already in manifest AND exists on disk."""
    if not filepath.exists():
        return False
    entries = load_manifest()
    return str(filepath) in {e["path"] for e in entries}


def get_by_species(species_key: str) -> list[dict]:
    """Return all manifest entries for a given species."""
    return [e for e in load_manifest() if e["species"] == species_key]


def get_by_category(category: str) -> list[dict]:
    """Return all entries for a conceptual category (e.g. 'resilience')."""
    return [e for e in load_manifest() if e["category"] == category]


def summary() -> dict:
    """Return counts by species and category — useful for quick checks."""
    entries = load_manifest()
    by_species: dict[str, int] = {}
    by_category: dict[str, int] = {}
    by_source: dict[str, int] = {}
    by_image_type: dict[str, int] = {}

    for e in entries:
        by_species[e["species"]] = by_species.get(e["species"], 0) + 1
        by_category[e["category"]] = by_category.get(e["category"], 0) + 1
        by_source[e["source"]] = by_source.get(e["source"], 0) + 1
        by_image_type[e["image_type"]] = by_image_type.get(e["image_type"], 0) + 1

    return {
        "total": len(entries),
        "by_species": by_species,
        "by_category": by_category,
        "by_source": by_source,
        "by_image_type": by_image_type,
    }


if __name__ == "__main__":
    # Run directly to inspect manifest state
    s = summary()
    print(f"\nTotal images: {s['total']}\n")
    print("By species:")
    for k, v in sorted(s["by_species"].items()):
        print(f"  {k:40s} {v}")
    print("\nBy category:")
    for k, v in sorted(s["by_category"].items()):
        print(f"  {k:40s} {v}")
    print("\nBy image type:")
    for k, v in sorted(s["by_image_type"].items()):
        print(f"  {k:40s} {v}")
    print("\nBy source:")
    for k, v in sorted(s["by_source"].items()):
        print(f"  {k:40s} {v}")
