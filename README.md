# Lineage of Endurance
A Machine Interpretation of Survival. Data & Machine Learning project for the MA Computational Arts programme at Goldsmiths.

## About

This project investigates whether machine learning can detect patterns of deep-time survival across nine species, organised into four categories: evolutionary continuity, extreme resilience, longevity, and persistence. Images are collected from scientific archives (GBIF, iNaturalist, MBARI, and curated SEM microscopy), encoded using CLIP embeddings, and explored through unsupervised clustering to find groupings that cut across biological classification.

## Getting Started

### Prerequisites

- Python 3.11 or above: Install from [python.org](https://www.python.org/downloads/) or via Homebrew ([instructions](https://docs.brew.sh/Homebrew-and-Python))
- conda (recommended): This project uses a conda environment called `deep-time`

### Installation

### Installation

1. Clone the repository
```sh
   git clone https://github.com/devsohyun/dmlap-deep-time.git
```

2. Create and activate the conda environment
```sh
   conda create -n deep-time python=3.11
   conda activate deep-time
```

3. Install required packages
```sh
   pip install requests Pillow tqdm openai torch torchvision clip
```
   > Note: CLIP installation may require an additional step — see [OpenAI CLIP](https://github.com/openai/CLIP) for details.

4. Download the image dataset from [SharePoint](https://goldsmithscollege-my.sharepoint.com/:f:/g/personal/sjun002_campus_goldsmiths_ac_uk/IgAtbNCp7uZ6Tr9rvG2sQPP8AaFdfZDH9V-ipMl7s4cijjI?e=t4oEPg) and place the contents directly into the `dataset/` folder. The expected folder structure is:

```
   dataset/
   ├── gbif/
   ├── sem_manual/
   ├── mbari/
   └── curated/
```

4. Download the image dataset from [SharePoint](https://goldsmithscollege-my.sharepoint.com/:f:/g/personal/sjun002_campus_goldsmiths_ac_uk/IgAtbNCp7uZ6Tr9rvG2sQPP8AaFdfZDH9V-ipMl7s4cijjI?e=t4oEPg) and place the contents directly into the `dataset/` folder. The expected folder structure is:

## Scripts

| Script | What it does |
|---|---|
| `config.py` | Central configuration. Species list, taxon keys, target image counts, source assignments, conceptual categories |
| `manifest.py` | Shared utility for reading and writing manifest.json. All scrapers import from here. Also runs directly to print dataset summary by species, category, source, and image type |
| `clean_manifest.py` | Removes entries from `manifest.json` where the file no longer exists on disk. Run after manually rejecting/moving bad images |
| `scrape_gbif.py` | Downloads occurrence images from [GBIF](https://www.gbif.org/) API filtered by taxon key and image availability |
| `scrape_inaturalist.py` | Downloads research-grade observation images from [iNaturalist](https://www.inaturalist.org/); used as a fallback where GBIF returns limited or poor-quality results |
| `manual_gbif.py` | *(please confirm)* Handles manual or targeted GBIF downloads outside the main scraper — possibly for specific taxon keys or one-off corrections? |
| `ingest_curated.py` | Registers hand-picked images dropped into `dataset/curated/`. Used for species where scraped images were insufficient (mainly bristlecone pine, ginkgo) |
| `embed_images.py` | Encodes all images in the dataset using CLIP, generating vector embeddings saved to the `embeddings/` folder |
| `visualise_umap.py` | Loads embeddings, runs UMAP reduction to 2D, produces three plots — by species, by category, by image type |
