"""
scrape_inaturalist.py
Downloads verified observation photos from iNaturalist.
No API key required for read-only access.

Usage:
    python scrape_inaturalist.py
    python scrape_inaturalist.py --species crocodylus_niloticus
    python scrape_inaturalist.py --dry-run
"""

import argparse
import time
from pathlib import Path

import requests

from config import DATASET_ROOT, SPECIES_CONFIG
from manifest import add_to_manifest, already_downloaded

INAT_API = "https://api.inaturalist.org/v1/observations"

# Map your species keys to iNaturalist taxon names
# iNaturalist uses scientific names directly
INAT_TAXON_NAMES = {
    "crocodylus_niloticus": "Crocodylus niloticus",
    "limulus_polyphemus": "Limulus polyphemus",
    "nautilus_pompilius": "Nautilus pompilius",
    "pinus_longaeva": "Pinus longaeva",
    "osmunda_regalis": "Osmunda regalis",
    "ginkgo_biloba": "Ginkgo biloba",
}


def get_inat_photos(taxon_name: str, limit: int = 50) -> list[dict]:
    """
    Fetch verified observation photos from iNaturalist.
    Returns list of dicts with url and metadata.
    """
    photos = []
    per_page = min(limit, 50)  # iNaturalist max per page is 200 but 50 is safe
    page = 1

    while len(photos) < limit:
        resp = requests.get(
            INAT_API,
            params={
                "taxon_name": taxon_name,
                "photos": True,
                "quality_grade": "research",
                "per_page": per_page,
                "page": page,
                "order": "votes",  # highest quality observations first
                "order_by": "votes",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            break

        for obs in results:
            for photo in obs.get("photos", []):
                url = photo.get("url", "")
                if not url:
                    continue

                # iNaturalist URL sizes:
                # square (75px), small (240px), medium (500px), large (1024px), original
                large_url = url.replace("square", "large")

                photos.append(
                    {
                        "url": large_url,
                        "observation_id": obs.get("id"),
                        "license": photo.get("license_code", "unknown"),
                        "attribution": photo.get("attribution", ""),
                        "quality_grade": obs.get("quality_grade"),
                        "observed_on": obs.get("observed_on", ""),
                    }
                )

                if len(photos) >= limit:
                    break
            if len(photos) >= limit:
                break

        page += 1
        time.sleep(0.5)

    return photos


def download_inat_species(species_key: str, dry_run: bool = False):
    if species_key not in INAT_TAXON_NAMES:
        print(f"  [skip] {species_key} — not in iNaturalist source list")
        return

    cfg = SPECIES_CONFIG[species_key]
    taxon_name = INAT_TAXON_NAMES[species_key]
    target = cfg["target_count"]

    out_dir = Path(DATASET_ROOT) / "inaturalist" / species_key
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{cfg['common_name']} ({taxon_name})")
    print(f"  Querying iNaturalist — target {target} images")

    photos = get_inat_photos(taxon_name, limit=target * 2)
    print(f"  Found {len(photos)} candidate photos")

    if dry_run:
        print(f"  [dry-run] Would attempt up to {target} downloads")
        return

    downloaded = 0
    for i, photo in enumerate(photos):
        if downloaded >= target:
            break

        filename = f"{species_key}_{i:03d}.jpg"
        filepath = out_dir / filename

        if already_downloaded(filepath):
            print(f"  [exists] {filename}")
            downloaded += 1
            continue

        try:
            img_resp = requests.get(photo["url"], timeout=15, stream=True)
            img_resp.raise_for_status()

            content_len = int(img_resp.headers.get("content-length", 999999))
            if content_len < 20_000:
                print(f"  [skip] {filename} — too small ({content_len} bytes)")
                continue

            with open(filepath, "wb") as f:
                for chunk in img_resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            add_to_manifest(
                {
                    "species": species_key,
                    "common_name": cfg["common_name"],
                    "category": cfg["category"],
                    "source": "inaturalist",
                    "image_type": "field_photo",
                    "path": str(filepath),
                    "url": photo["url"],
                    "license": photo["license"],
                    "attribution": photo["attribution"],
                    "inat_observation_id": photo["observation_id"],
                    "quality_grade": photo["quality_grade"],
                }
            )

            print(f"  [ok] {filename}")
            downloaded += 1
            time.sleep(0.3)

        except Exception as e:
            print(f"  [fail] {photo['url']} — {e}")

    print(f"  Done: {downloaded}/{target}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--species", help="Single species key")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    targets = [args.species] if args.species else list(INAT_TAXON_NAMES.keys())

    for species_key in targets:
        download_inat_species(species_key, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
