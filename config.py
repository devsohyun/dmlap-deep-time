"""
Central configuration for all species, sources, categories, and image targets.
Edit target counts or add species here — everything else reads from this file.
Specimen and field photos from GBIF are collected with 'scrape_gbif.py', and SEM microscopy images are collected manually.
"""

DATASET_ROOT = "dataset"

# This is what gets written into manifest.json
# can check taxon key manually with the url https://www.gbif.org/species/YOUR_TAXON_KEY
SPECIES_CONFIG = {
    # --- Evolutionary continuity (living fossils) ---
    "crocodylus_niloticus": {
        "common_name": "Nile Crocodile",
        "category": "evolutionary_continuity",
        "sources": ["gbif"],
        "gbif_taxon_key": 2441341,
        "target_count": 270,
        "preferred_image_types": ["specimen_photo", "field_photo"],
    },
    "limulus_polyphemus": {
        "common_name": "Horseshoe Crab",
        "category": "evolutionary_continuity",
        "sources": ["gbif"],
        "gbif_taxon_key": 1010610,
        "target_count": 72,
        "preferred_image_types": ["specimen_photo"],
    },
    "nautilus_pompilius": {
        "common_name": "Nautilus",
        "category": "evolutionary_continuity",
        # Both GBIF (specimen) and sem_manual (shell cross-section) — intentional dual register
        "sources": ["gbif", "sem_manual"],
        "gbif_taxon_key": 2289060,
        "target_count": 100,
        "preferred_image_types": ["specimen_photo", "sem_microscopy"],
    },
    # --- Extreme resilience ---
    "tardigrade": {
        "common_name": "Tardigrade",
        "category": "resilience",
        "sources": ["sem_manual"],  # SEM only — no usable GBIF imagery
        "gbif_taxon_key": 14,
        "target_count": 20,
        "preferred_image_types": ["sem_microscopy"],
    },
    "cyanobacteria": {
        "common_name": "Cyanobacteria",
        "category": "resilience",
        "sources": ["sem_manual"],
        "gbif_taxon_key": 68,
        "target_count": 20,
        "preferred_image_types": ["sem_microscopy", "light_microscopy"],
    },
    "stromatolites": {
        "common_name": "Stromatolites",
        "category": "resilience",
        "sources": ["sem_manual"],
        "gbif_taxon_key": 68,
        "target_count": 20,
        "preferred_image_types": ["sem_microscopy", "light_microscopy"],
    },
    # --- Individual longevity ---
    "pinus_longaeva": {
        "common_name": "Great Basin Bristlecone Pine",
        "category": "longevity",
        "sources": ["gbif"],
        "gbif_taxon_key": 5285258,
        "target_count": 72,
        "preferred_image_types": ["field_photo", "specimen_photo"],
    },
    "euplectella_aspergillum": {
        "common_name": "Glass Sponge",
        "category": "longevity",
        "sources": ["mbari"],  # MBARI deep-sea stills
        "gbif_taxon_key": 5180237,
        "target_count": 20,
        "preferred_image_types": ["deep_sea_still"],
    },
    # --- Slow evolution / persistence ---
    "osmunda_regalis": {
        "common_name": "Royal Fern",
        "category": "persistence",
        "sources": ["gbif"],
        "gbif_taxon_key": 8049341,
        "target_count": 66,
        "preferred_image_types": ["specimen_photo", "field_photo"],
    },
    "ginkgo_biloba": {
        "common_name": "Ginkgo",
        "category": "persistence",
        "sources": ["gbif", "bhl"],
        "gbif_taxon_key": 2687885,
        "target_count": 52,
        "preferred_image_types": ["specimen_photo", "botanical_illustration"],
    },
}

# BHL items worth pulling for the Haeckel reference archive
# These are BHL title IDs for Haeckel's Kunstformen der Natur
BHL_HAECKEL_TITLE_IDS = [49157, 49158]  # Verify these against BHL API

BHL_API_KEY = (
    "45b71991-ad6b-421d-a85b-b5783145d382"  # Register free at biodiversitylibrary.org
)
