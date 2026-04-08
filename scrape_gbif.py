"""
Downloads specimen/field images from GBIF for species with "gbif" in their sources list.

Usage:
    python scrape_gbif.py
    python scrape_gbif.py --species ginkgo_biloba  # single species
    python scrape_gbif.py --dry-run                # check counts without downloading
"""

import argparse
import time
from pathlib import Path

import requests

from config import DATASET_ROOT, SPECIES_CONFIG
from manifest import add_to_manifest, already_downloaded


def get_gbif_images(taxon_key: int, limit: int = 50) -> list[dict]:
    """
    Query GBIF occurrence API for images of a taxon.
    Returns list of dicts with {url, license, publisher}.
    """
    # Request occurrences that have still images attached; fetch 2x target to allow for skips
    params = {
        "taxonKey": taxon_key,
        "mediaType": "StillImage",
        "limit": limit,
        "hasCoordinate": False,  # Don't restrict to georeferenced — gets more images
    }
    resp = requests.get(
        "https://api.gbif.org/v1/occurrence/search", params=params, timeout=15
    )
    resp.raise_for_status()

    # Each occurrence can have multiple media items; flatten to a single list of images
    results = []
    for occ in resp.json().get("results", []):
        for media in occ.get("media", []):
            if media.get("type") == "StillImage" and media.get("identifier"):
                results.append(
                    {
                        "url": media["identifier"],
                        "license": media.get("license", "unknown"),
                        "publisher": occ.get("institutionCode", "unknown"),
                        "occurrence_id": occ.get("gbifID"),
                    }
                )
    return results


def download_gbif_species(species_key: str, dry_run: bool = False):
    cfg = SPECIES_CONFIG[species_key]

    # Skip species that are not configured to use GBIF as a source
    if "gbif" not in cfg["sources"]:
        return
    if cfg["gbif_taxon_key"] is None:
        print(f"  [skip] {species_key} — no GBIF taxon key")
        return

    # Output goes to <DATASET_ROOT>/gbif/<species_key>/
    out_dir = Path(DATASET_ROOT) / "gbif" / species_key
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    target = cfg["target_count"]
    print(f"\n{cfg['common_name']} ({species_key})")
    print(f"  Querying GBIF taxon key {cfg['gbif_taxon_key']} — target {target} images")

    # Request 2x the target count so we have headroom to skip bad images
    image_records = get_gbif_images(cfg["gbif_taxon_key"], limit=target * 2)
    print(f"  Found {len(image_records)} candidate images")

    if dry_run:
        print(f"  [dry-run] Would attempt up to {target} downloads")
        return

    downloaded = 0
    for i, record in enumerate(image_records):
        if downloaded >= target:
            break

        url = record["url"]
        filename = f"{species_key}_{i:03d}.jpg"
        filepath = out_dir / filename

        # Check manifest and disk before attempting download
        if already_downloaded(filepath):
            print(f"  [exists] {filename}")
            downloaded += 1
            continue

        try:
            img_resp = requests.get(url, timeout=12, stream=True)
            img_resp.raise_for_status()

            # Basic sanity check — skip tiny thumbnails
            content_len = int(img_resp.headers.get("content-length", 999999))
            if content_len < 10_000:
                print(f"  [skip] {filename} — too small ({content_len} bytes)")
                continue

            # Stream to disk in chunks to avoid loading large images into memory
            with open(filepath, "wb") as f:
                for chunk in img_resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Record the download in the manifest for deduplication and provenance tracking
            add_to_manifest(
                {
                    "species": species_key,
                    "common_name": cfg["common_name"],
                    "category": cfg["category"],
                    "source": "gbif",
                    "image_type": "specimen_photo",
                    "path": str(filepath),
                    "url": url,
                    "license": record["license"],
                    "publisher": record["publisher"],
                    "gbif_occurrence_id": record["occurrence_id"],
                }
            )

            print(f"  [ok] {filename}")
            downloaded += 1
            time.sleep(0.3)  # polite rate limiting

        except Exception as e:
            print(f"  [fail] {url} — {e}")

    print(f"  Done: {downloaded}/{target} downloaded")


def main():
    # Command-line arguments for flexibility in targeting specific species or doing dry runs
    parser = argparse.ArgumentParser()
    parser.add_argument("--species", help="Single species key to download")  #
    parser.add_argument(
        "--dry-run", action="store_true"
    )  # If --dry-run is set, will print counts and skip actual downloads
    args = parser.parse_args()

    # If no species is specified, run for all species configured with GBIF as a source
    targets = (
        [args.species]
        if args.species
        else [k for k, v in SPECIES_CONFIG.items() if "gbif" in v["sources"]]
    )

    for species_key in targets:
        download_gbif_species(species_key, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
