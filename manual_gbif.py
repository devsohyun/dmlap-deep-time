# Run this code to add a manually selected image from GBIF to the manifest, e.g. as a replacement for a bad image that was removed.
from manifest import add_to_manifest

add_to_manifest(
    {
        "species": "crocodylus_niloticus",
        "common_name": "Nile Crocodile",
        "category": "evolutionary_continuity",
        "source": "gbif_manual",  # distinguish from auto-scraped
        "image_type": "specimen_photo",
        "path": "dataset/gbif/crocodylus_niloticus/crocodylus_niloticus_manual_001.jpg",
        "url": "https://www.gbif.org/species/XXXXXXX",  # paste the GBIF occurrence URL
        "notes": "manually selected replacement — cleaner specimen photo",
    }
)
