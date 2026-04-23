"""
Downloads botanical illustration plates from the Biodiversity Heritage Library.
Targets: ginkgo, ferns, and the Haeckel reference archive.

Set BHL_API_KEY in config.py that you get from the BHL website.

Usage:
    python scrape_bhl.py
    python scrape_bhl.py --haeckel-only   # just pull the Haeckel plates
"""

import argparse
import time
from pathlib import Path

import requests

from config import BHL_API_KEY, BHL_HAECKEL_TITLE_IDS, DATASET_ROOT, SPECIES_CONFIG
from manifest import add_to_manifest, already_downloaded

BHL_BASE = "https://www.biodiversitylibrary.org/api3"


def bhl_get(op: str, **params) -> dict:
    """Thin wrapper around the BHL API."""
    resp = requests.get(
        BHL_BASE,
        params={"op": op, "apikey": BHL_API_KEY, "format": "json", **params},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("Status") != "ok":
        raise ValueError(f"BHL API error: {data.get('ErrorMessage')}")
    return data.get("Result", [])


def get_pages_for_title(title_id: int) -> list[dict]:
    """Get all pages in a BHL title, filtering to those that have images."""
    items = bhl_get("GetTitleItems", titleid=title_id)
    pages = []
    for item in items:
        item_pages = bhl_get("GetItemPages", itemid=item["ItemID"], ocr=False)
        for page in item_pages:
            if page.get("HasIllustration") == "True" or page.get("FileUrl"):
                pages.append(
                    {
                        "page_id": page["PageID"],
                        "url": page.get("FileUrl"),
                        "title_id": title_id,
                        "item_id": item["ItemID"],
                    }
                )
    return pages


def download_page_image(page: dict, out_path: Path, metadata: dict):
    """Download a single BHL page image."""
    if already_downloaded(out_path):
        print(f"  [exists] {out_path.name}")
        return True

    url = page["url"]
    if not url:
        return False

    # BHL serves images at different resolutions — request large version
    url_large = url.replace("thumb", "large") if "thumb" in url else url

    try:
        resp = requests.get(url_large, timeout=20, stream=True)
        if resp.status_code == 404:
            resp = requests.get(url, timeout=20, stream=True)
        resp.raise_for_status()

        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        add_to_manifest(metadata)
        print(f"  [ok] {out_path.name}")
        time.sleep(0.5)  # BHL rate limit is gentle but real
        return True

    except Exception as e:
        print(f"  [fail] {url} — {e}")
        return False


def download_haeckel(dry_run: bool = False):
    """Pull illustrated plates from Haeckel's Kunstformen der Natur."""
    print("\nHaeckel plates (reference archive)")
    out_dir = Path(DATASET_ROOT) / "bhl" / "haeckel_plates"
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    for title_id in BHL_HAECKEL_TITLE_IDS:
        print(f"  Fetching title {title_id}...")
        try:
            pages = get_pages_for_title(title_id)
            print(f"  Found {len(pages)} illustrated pages")

            if dry_run:
                print(f"  [dry-run] Would download up to {len(pages)} images")
                continue

            for i, page in enumerate(pages[:50]):  # cap at 50 plates
                out_path = out_dir / f"haeckel_{title_id}_{i:03d}.jpg"
                download_page_image(
                    page,
                    out_path,
                    {
                        "species": "haeckel_reference",
                        "common_name": "Haeckel Art Forms in Nature",
                        "category": "reference_archive",
                        "source": "bhl",
                        "image_type": "historical_illustration",
                        "path": str(out_path),
                        "url": page["url"],
                        "bhl_title_id": title_id,
                        "bhl_page_id": page["page_id"],
                    },
                )
        except Exception as e:
            print(f"  [error] title {title_id}: {e}")


def download_bhl_species(species_key: str, dry_run: bool = False):
    """Download BHL botanical illustrations for a species."""
    cfg = SPECIES_CONFIG[species_key]
    if "bhl" not in cfg["sources"]:
        return

    out_dir = Path(DATASET_ROOT) / "bhl" / species_key
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    target = cfg["target_count"] // 2  # BHL supplements GBIF, doesn't replace it
    print(f"\n{cfg['common_name']} — BHL illustrations (target: {target})")

    # Search BHL for the species
    try:
        results = bhl_get("GetTitleSearchSimple", title=cfg["common_name"])
        print(f"  Found {len(results)} BHL titles")
    except Exception as e:
        print(f"  [error] BHL search failed: {e}")
        return

    downloaded = 0
    for title in results[:5]:  # check first 5 matching titles
        if downloaded >= target:
            break
        try:
            pages = get_pages_for_title(title["TitleID"])
            for i, page in enumerate(pages):
                if downloaded >= target:
                    break
                if dry_run:
                    downloaded += 1
                    continue
                out_path = out_dir / f"{species_key}_bhl_{downloaded:03d}.jpg"
                success = download_page_image(
                    page,
                    out_path,
                    {
                        "species": species_key,
                        "common_name": cfg["common_name"],
                        "category": cfg["category"],
                        "source": "bhl",
                        "image_type": "botanical_illustration",
                        "path": str(out_path),
                        "url": page["url"],
                        "bhl_title_id": title["TitleID"],
                        "bhl_page_id": page["page_id"],
                    },
                )
                if success:
                    downloaded += 1
        except Exception as e:
            print(f"  [error] title {title.get('TitleID')}: {e}")

    print(f"  Done: {downloaded}/{target}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--haeckel-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    download_haeckel(dry_run=args.dry_run)

    if not args.haeckel_only:
        bhl_species = [k for k, v in SPECIES_CONFIG.items() if "bhl" in v["sources"]]
        for species_key in bhl_species:
            download_bhl_species(species_key, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
