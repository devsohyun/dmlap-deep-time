"""
Register hand-curated images (SEM microscopy, MBARI stills) into the manifest.

For automated scraping doesn't work well for certain species/sources.
Then drop them into the appropriate folder and run this script to register them.

Usage:
    python ingest_manual.py                          # register everything in sem_manual/ and mbari/
    python ingest_manual.py --species ramazzottius_sp
    python ingest_manual.py --report                 # just show what's registered vs on disk
"""

import argparse
from pathlib import Path

from config import DATASET_ROOT, SPECIES_CONFIG
from manifest import add_to_manifest, load_manifest

# Map folder names to metadata defaults
MANUAL_SOURCE_DEFAULTS = {
    "sem_manual": {
        "source": "sem_manual",
        "image_type": "sem_microscopy",
    },
    "mbari": {
        "source": "mbari",
        "image_type": "deep_sea_still",
    },
}

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def infer_species_from_path(filepath: Path) -> str | None:
    """Infer species key from folder name — assumes dataset/source/species_key/image.jpg"""
    parts = filepath.parts
    if len(parts) >= 3:
        return parts[-2]  # parent folder = species key
    return None


def register_manual_images(source_folder: str, species_filter: str | None = None):
    """
    Walk a manual source folder and register any untracked images into the manifest.
    """
    source_dir = Path(DATASET_ROOT) / source_folder
    if not source_dir.exists():
        print(
            f"  [skip] {source_dir} does not exist yet — create it and drop images in"
        )
        return

    defaults = MANUAL_SOURCE_DEFAULTS[source_folder]
    manifest = load_manifest()
    already_registered = {entry["path"] for entry in manifest}

    new_count = 0
    for img_path in sorted(source_dir.rglob("*")):
        if img_path.suffix.lower() not in VALID_EXTENSIONS:
            continue

        species_key = infer_species_from_path(img_path)
        if species_filter and species_key != species_filter:
            continue
        if species_key not in SPECIES_CONFIG:
            print(
                f"  [warn] unknown species folder: {species_key} — skipping {img_path.name}"
            )
            continue

        path_str = str(img_path)
        if path_str in already_registered:
            continue

        cfg = SPECIES_CONFIG[species_key]

        # Try to infer image type from filename hints
        name_lower = img_path.stem.lower()
        if "sem" in name_lower or "electron" in name_lower:
            image_type = "sem_microscopy"
        elif "light" in name_lower or "optical" in name_lower:
            image_type = "light_microscopy"
        elif "cross" in name_lower or "section" in name_lower:
            image_type = "cross_section"
        else:
            image_type = defaults["image_type"]

        add_to_manifest(
            {
                "species": species_key,
                "common_name": cfg["common_name"],
                "category": cfg["category"],
                "source": defaults["source"],
                "image_type": image_type,
                "path": path_str,
                "url": None,  # no source URL tracked automatically. Could be added manually if desired.
                "notes": "manually ingested",
            }
        )

        print(f"  [registered] {img_path.name} → {species_key} ({image_type})")
        new_count += 1

    print(f"  Registered {new_count} new images from {source_folder}/")


def report():
    """Compare what's in manifest vs what's on disk."""
    manifest = load_manifest()
    registered_paths = {entry["path"] for entry in manifest}

    print("\n=== Manifest vs disk report ===\n")

    for source_folder in ["sem_manual", "mbari"]:
        source_dir = Path(DATASET_ROOT) / source_folder
        if not source_dir.exists():
            print(f"{source_folder}/  [directory not found]")
            continue

        on_disk = {
            str(p)
            for p in source_dir.rglob("*")
            if p.suffix.lower() in VALID_EXTENSIONS
        }
        registered = on_disk & registered_paths
        unregistered = on_disk - registered_paths

        print(f"{source_folder}/")
        print(f"  on disk:      {len(on_disk)}")
        print(f"  registered:   {len(registered)}")
        if unregistered:
            print(f"  unregistered: {len(unregistered)}")
            for p in sorted(unregistered):
                print(f"    - {Path(p).name}")
        print()

    # Overall manifest summary
    print("=== Manifest summary by species ===\n")
    by_species: dict[str, list] = {}
    for entry in manifest:
        by_species.setdefault(entry["species"], []).append(entry)

    for species_key, cfg in SPECIES_CONFIG.items():
        entries = by_species.get(species_key, [])
        target = cfg["target_count"]
        status = (
            "OK" if len(entries) >= target else f"need {target - len(entries)} more"
        )
        print(f"  {cfg['common_name']:35s} {len(entries):3d}/{target}  {status}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--species", help="Filter to a single species key")
    parser.add_argument(
        "--report", action="store_true", help="Show manifest vs disk report"
    )
    args = parser.parse_args()

    if args.report:
        report()
        return

    for source_folder in ["sem_manual", "mbari"]:
        register_manual_images(source_folder, species_filter=args.species)


if __name__ == "__main__":
    main()
