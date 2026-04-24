# Lineage of Endurance
A Machine Interpretation of Survival. Data & Machine Learning project for the MA Computational Arts programme at Goldsmiths.
Github repository can be viewed [here](https://github.com/devsohyun/dmlap-deep-time).

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

4. Download the image dataset from [Google Drive](https://drive.google.com/drive/folders/1tvLZoxTAkMLPGaGNYZUHvmIT0Ta-KD79?usp=drive_link) and place the contents directly into the `dataset/` folder. The expected folder structure is:

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

## Usage

### Make dataset

1. Scrape from GBIF by running `python scrape_gbif.py`
2. Then manually clean and curate images.
3. Check the collection automatically by running `python manifest.py`
4. Everytime if you add/remove images, run `python clean_manifest.py`
5. Check manifest.json in `dataset/`

### UMAP Visualisation

1. With a help of [UMAP](https://umap-learn.readthedocs.io/en/latest/), CLIP latent space can be visualised in PNG files. Run:
```
python visualise_umap.py
```
2. Check png files generated in `embeddings/`


### K-means Unsupervised Clustering

By using [k-means](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html), you can cluster the CLIP embeddings and examine how species group together in latent space. The number after `--k` sets how many clusters the machine will find.

1. Run clustering with a specific k value:
```sh
python cluster_and_extract.py --k 10
```

2. Check the output in `embeddings/`:
   - `clusters_k{k}.json` — cluster assignments and species composition per cluster
   - `prompts_k{k}.json` — extracted prompts per cluster for generative synthesis
   - `umap_clusters_k{k}.png` — UMAP plot coloured by cluster

3. Recommended k values to compare:
   - `--k 4` — one cluster per conceptual category. Tests whether the machine finds your framing
   - `--k 10` — one cluster per species. Tests whether each species holds together visually
   - Higher k values reveal finer sub-structure within each world

4. Mixed clusters (where multiple species group together) are the most conceptually interesting results. These are flagged in the JSON output as `"is_mixed_cluster": true` and carry the richest prompts for the generative step.

### Generative Image Synthesis

Generated images are produced using [Stable Diffusion](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5) via HuggingFace Diffusers, using prompts extracted from the clustering step. This step runs in Google Colab due to GPU requirements.

1. Upload `prompts_k{k}.json` to your Google Drive
2. Open `diffusion_txt2img.ipynb` in [Google Colab](https://colab.research.google.com/)
3. Mount your Google Drive and set `generatingClusterType` to match your chosen k value
4. Run all cells. Generated images are saved to `DeepTime/generated/{k}/` in your Drive

More information can be view in the [Notebook](https://github.com/devsohyun/dmlap-deep-time/blob/main/diffusion_txt2img.ipynb).

## Dataset

229 images across 10 species, collected from scientific archives. Images were evaluated individually for visual register — whether they foreground morphological structure over environmental context.

| Species | Category | Source |
|---|---|---|
| Crocodylus niloticus | Evolutionary continuity | GBIF |
| Limulus polyphemus | Evolutionary continuity | GBIF |
| Nautilus pompilius | Evolutionary continuity | GBIF |
| Tardigrade | Resilience | SEM manual |
| Cyanobacteria | Resilience | SEM manual |
| Stromatolites | Resilience | SEM manual |
| Pinus longaeva | Longevity | GBIF + curated |
| Euplectella aspergillum | Longevity | SEM manual |
| Osmunda regalis | Persistence | GBIF |
| Ginkgo biloba | Persistence | GBIF + curated |

## References

- Radford, A. et al. (2021) [Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020)
- McInnes, L., Healy, J. and Melville, J. (2018) [UMAP: Uniform Manifold Approximation and Projection](https://github.com/lmcinnes/umap)
- [GBIF](https://www.gbif.org/) — Global Biodiversity Information Facility
- [iNaturalist](https://www.inaturalist.org/)
- [MBARI](https://www.mbari.org/) — Monterey Bay Aquarium Research Institute


