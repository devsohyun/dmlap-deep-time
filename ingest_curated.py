# ingest_curated.py
# Register manually curated images into manifest.
# Run after dropping images into dataset/curated/species_key/

from pathlib import Path

from config import DATASET_ROOT, SPECIES_CONFIG
from manifest import add_to_manifest, already_downloaded

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def ingest_curated():
    curated_dir = Path(DATASET_ROOT) / "curated"
    if not curated_dir.exists():
        print("dataset/curated/ not found — create it and add species subfolders")
        return

    registered = 0
    for species_dir in sorted(curated_dir.iterdir()):
        if not species_dir.is_dir() or species_dir.name.startswith("_"):
            continue

        species_key = species_dir.name
        if species_key not in SPECIES_CONFIG:
            print(f"  [warn] unknown species folder: {species_key}")
            continue

        cfg = SPECIES_CONFIG[species_key]

        for img_path in sorted(species_dir.iterdir()):
            if img_path.suffix.lower() not in VALID_EXTENSIONS:
                continue
            if already_downloaded(img_path):
                print(f"  [exists] {img_path.name}")
                continue

            add_to_manifest(
                {
                    "species": species_key,
                    "common_name": cfg["common_name"],
                    "category": cfg["category"],
                    "source": "curated",
                    "image_type": "field_photo",
                    "path": str(img_path),
                    "url": None,
                    "notes": "manually curated image",
                }
            )
            print(f"  [registered] {img_path.name} → {species_key}")
            registered += 1

    print(f"\nDone — {registered} new images registered")


if __name__ == "__main__":
    ingest_curated()
