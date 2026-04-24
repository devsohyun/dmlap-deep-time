"""
K-means clustering on CLIP embeddings + prompt extraction per cluster.

Produces:
    embeddings/clusters_k{k}.json     — cluster assignments and metadata
    embeddings/prompts_k{k}.json      — extracted prompts per cluster
    embeddings/umap_clusters_k{k}.png — UMAP plot coloured by cluster

Usage:
    python3 cluster_and_extract.py              # runs k=4, k=9, k=12
    python3 cluster_and_extract.py --k 9        # single k value
    python3 cluster_and_extract.py --k 9 --plot # also save UMAP plot
"""

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

EMBEDDINGS_DIR = Path("embeddings")


def load_data():
    embeddings = np.load(EMBEDDINGS_DIR / "embeddings.npy")
    coords = np.load(EMBEDDINGS_DIR / "umap_coords.npy")
    with open(EMBEDDINGS_DIR / "metadata.json") as f:
        metadata = json.load(f)
    print(f"Loaded {len(metadata)} embeddings, shape {embeddings.shape}")
    return embeddings, coords, metadata


def run_kmeans(embeddings: np.ndarray, k: int) -> np.ndarray:
    """
    Run k-means on the full 512-dimensional embeddings, not the 2D UMAP coords.
    UMAP is for visualisation only — clustering in the original space is more accurate.
    """
    print(f"\nRunning k-means with k={k}...")
    kmeans = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=20,  # run 20 times with different seeds, take best
        max_iter=500,
    )
    labels = kmeans.fit_predict(embeddings)

    # Silhouette score — measures cluster quality
    # Range: -1 (bad) to 1 (perfect). Above 0.2 is reasonable for image embeddings.
    score = silhouette_score(embeddings, labels, metric="cosine")
    print(f"  Silhouette score: {score:.4f}")

    return labels, kmeans.cluster_centers_


def analyse_clusters(labels: np.ndarray, metadata: list[dict], k: int) -> list[dict]:
    """
    For each cluster, summarise what species and categories it contains.
    Returns a list of cluster dicts sorted by size.
    """
    clusters = []

    for cluster_id in range(k):
        indices = [i for i, l in enumerate(labels) if l == cluster_id]
        members = [metadata[i] for i in indices]

        species_counts = Counter(m["species"] for m in members)
        category_counts = Counter(m["category"] for m in members)
        image_type_counts = Counter(m["image_type"] for m in members)

        # Dominant species and category
        dominant_species = species_counts.most_common(1)[0][0]
        dominant_category = category_counts.most_common(1)[0][0]

        # Purity — what fraction belongs to the dominant species
        purity = species_counts.most_common(1)[0][1] / len(members)

        clusters.append(
            {
                "cluster_id": cluster_id,
                "size": len(members),
                "dominant_species": dominant_species,
                "dominant_category": dominant_category,
                "purity": round(purity, 3),
                "species_composition": dict(species_counts.most_common()),
                "category_composition": dict(category_counts.most_common()),
                "image_type_composition": dict(image_type_counts.most_common()),
                "member_paths": [m["path"] for m in members],
            }
        )

    # Sort by size descending
    clusters.sort(key=lambda x: x["size"], reverse=True)
    return clusters


def extract_prompts(clusters: list[dict]) -> list[dict]:
    """
    Extract descriptive prompts from each cluster's composition.
    These prompts reflect what CLIP grouped together — not species names,
    but visual and conceptual properties that describe the cluster.

    The prompt structure:
        - visual descriptor (from image_type)
        - biological descriptor (from species/category mix)
        - deep time descriptor (conceptual layer from your categories)
    """

    # Visual register vocabulary — maps image_type to visual language
    visual_vocab = {
        "sem_microscopy": "microscopic surface detail, scanning electron microscopy, "
        "three-dimensional textured form, greyscale scientific imaging",
        "specimen_photo": "museum specimen, isolated organism, controlled background, "
        "natural history collection, morphological clarity",
        "field_photo": "living organism in natural environment, field observation, "
        "ecological context, naturalist photography",
        "deep_sea_still": "deep ocean environment, bioluminescent darkness, "
        "ROV observation, abyssal form",
        "botanical_illustration": "scientific illustration, botanical plate, structural diagram, "
        "Haeckel aesthetic, radial symmetry",
        "light_microscopy": "optical microscopy, cellular structure, "
        "translucent form, colonial organism",
    }

    # Category vocabulary — maps conceptual category to deep time language
    category_vocab = {
        "evolutionary_continuity": "living fossil, unchanged across geological epochs, "
        "persistence through mass extinction, ancient body plan",
        "resilience": "extreme survival, cryptobiosis, indestructible at microscopic scale, "
        "survives vacuum of space, oldest living lineage",
        "longevity": "individual lifespan beyond human comprehension, "
        "ancient organism, millennia of continuous existence",
        "persistence": "morphological stasis, slow evolution, "
        "unchanged leaf form across deep time, living relic",
    }

    # Species vocabulary — specific visual/biological descriptors
    species_vocab = {
        "crocodylus_niloticus": "armoured reptile, scaled skin texture, "
        "prehistoric predator, unchanged jaw structure",
        "limulus_polyphemus": "horseshoe crab, chitinous exoskeleton, "
        "compound eyes, blue blood, ancient arthropod",
        "nautilus_pompilius": "chambered shell, logarithmic spiral, "
        "cephalopod, tentacled organism, iridescent geometry",
        "tardigrade": "water bear, eight-legged microscopic animal, "
        "barrel-shaped body, clawed limbs, cryptobiosis",
        "cyanobacteria": "filamentous colony, photosynthetic microorganism, "
        "oxygenated the ancient atmosphere, stromatolite builder",
        "stromatolites": "layered geological formation, fossilised microbial mat, "
        "3.5 billion years of biological record, ancient reef structure",
        "pinus_longaeva": "ancient twisted trunk, deadwood sculpture, "
        "sparse foliage, high altitude survivor, bristlecone form",
        "euplectella_aspergillum": "glass sponge, silica lattice skeleton, "
        "deep sea architecture, hexagonal mesh, venus flower basket",
        "osmunda_regalis": "royal fern, ancient frond, "
        "spore-bearing, Carboniferous lineage, unfurling leaf",
        "ginkgo_biloba": "fan-shaped leaf, living fossil, "
        "Jurassic survivor, ginkgolide chemistry, bilateral symmetry",
    }

    prompts = []

    for cluster in clusters:
        # Get dominant image type
        dominant_image_type = max(
            cluster["image_type_composition"], key=cluster["image_type_composition"].get
        )

        # Get dominant category
        dominant_category = cluster["dominant_category"]

        # Get top 1-2 species
        top_species = list(cluster["species_composition"].keys())[:2]

        # Build prompt layers
        visual_layer = visual_vocab.get(dominant_image_type, "scientific image")
        category_layer = category_vocab.get(dominant_category, "ancient organism")
        species_layer = ", ".join(
            species_vocab.get(s, s.replace("_", " ")) for s in top_species
        )

        # Check if cluster is mixed (purity < 0.6 means multiple species present)
        is_mixed = cluster["purity"] < 0.6
        mix_note = ""
        if is_mixed:
            all_categories = list(cluster["category_composition"].keys())
            if len(all_categories) > 1:
                mix_note = f"convergence of {' and '.join(all_categories)}, "

        # Compose full prompt
        prompt = (
            f"{species_layer}, "
            f"{mix_note}"
            f"{visual_layer}, "
            f"{category_layer}, "
            f"deep time survival, species beyond human time"
        )

        prompts.append(
            {
                "cluster_id": cluster["cluster_id"],
                "size": cluster["size"],
                "dominant_species": cluster["dominant_species"],
                "dominant_category": dominant_category,
                "purity": cluster["purity"],
                "is_mixed_cluster": is_mixed,
                "species_composition": cluster["species_composition"],
                "prompt": prompt,
                # Shorter version for direct use in image generation
                "prompt_short": (
                    f"{species_layer}, "
                    f"{visual_layer.split(',')[0]}, "
                    f"deep time, ancient survival"
                ),
            }
        )

    return prompts


def plot_clusters(
    coords: np.ndarray,
    labels: np.ndarray,
    metadata: list[dict],
    k: int,
    save_path: Path,
):
    """Plot UMAP coloured by cluster assignment."""

    colours = [
        "#E63946",
        "#457B9D",
        "#2A9D8F",
        "#E9C46A",
        "#F4A261",
        "#264653",
        "#A8DADC",
        "#6A4C93",
        "#B5838D",
        "#99C1B9",
        "#FF6B6B",
        "#4ECDC4",
        "#45B7D1",
    ]

    fig, ax = plt.subplots(figsize=(12, 9))
    fig.patch.set_facecolor("#0D0D0D")
    ax.set_facecolor("#0D0D0D")

    for cluster_id in range(k):
        indices = [i for i, l in enumerate(labels) if l == cluster_id]
        x = coords[indices, 0]
        y = coords[indices, 1]
        ax.scatter(
            x,
            y,
            c=colours[cluster_id % len(colours)],
            s=45,
            alpha=0.85,
            edgecolors="none",
            label=f"Cluster {cluster_id} (n={len(indices)})",
        )

        # Label cluster centroid
        if len(indices) > 0:
            cx, cy = np.mean(x), np.mean(y)
            ax.text(
                cx,
                cy,
                str(cluster_id),
                color="white",
                fontsize=8,
                ha="center",
                va="center",
                fontweight="bold",
            )

    ax.legend(
        loc="upper left",
        framealpha=0.15,
        facecolor="#1a1a1a",
        edgecolor="#444",
        fontsize=7,
        labelcolor="white",
    )
    ax.set_title(
        f"CLIP latent space — k-means k={k}", color="white", fontsize=13, pad=14
    )
    ax.tick_params(colors="#555")
    ax.spines["bottom"].set_color("#333")
    ax.spines["left"].set_color("#333")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlabel("UMAP 1", color="#888", fontsize=9)
    ax.set_ylabel("UMAP 2", color="#888", fontsize=9)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved: {save_path}")


def print_cluster_report(clusters: list[dict], prompts: list[dict], k: int):
    print(f"\n{'=' * 60}")
    print(f"  CLUSTER REPORT — k={k}")
    print(f"{'=' * 60}")

    for cluster, prompt_data in zip(clusters, prompts):
        print(
            f"\nCluster {cluster['cluster_id']}  "
            f"(n={cluster['size']}, purity={cluster['purity']:.2f})"
        )
        print(f"  Dominant species:  {cluster['dominant_species']}")
        print(f"  Dominant category: {cluster['dominant_category']}")
        print(f"  Species mix:       {cluster['species_composition']}")
        print(f"  Image types:       {cluster['image_type_composition']}")
        print(f"  Mixed cluster:     {prompt_data['is_mixed_cluster']}")
        print("\n  PROMPT:")
        print(f"  {prompt_data['prompt']}")
        print("\n  SHORT PROMPT:")
        print(f"  {prompt_data['prompt_short']}")


def run_for_k(k: int, embeddings, coords, metadata, plot: bool = True):
    labels, centers = run_kmeans(embeddings, k)
    clusters = analyse_clusters(labels, metadata, k)
    prompts = extract_prompts(clusters)

    # Save cluster assignments
    cluster_path = EMBEDDINGS_DIR / f"clusters_k{k}.json"
    with open(cluster_path, "w") as f:
        json.dump(clusters, f, indent=2)
    print(f"Saved: {cluster_path}")

    # Save prompts
    prompt_path = EMBEDDINGS_DIR / f"prompts_k{k}.json"
    with open(prompt_path, "w") as f:
        json.dump(prompts, f, indent=2)
    print(f"Saved: {prompt_path}")

    # Plot
    if plot:
        plot_clusters(
            coords, labels, metadata, k, EMBEDDINGS_DIR / f"umap_clusters_k{k}.png"
        )

    print_cluster_report(clusters, prompts, k)
    return clusters, prompts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, help="Single k value (default: runs 4, 9, 12)")
    parser.add_argument("--plot", action="store_true", default=True)
    args = parser.parse_args()

    embeddings, coords, metadata = load_data()

    k_values = [args.k] if args.k else [4, 9, 12]

    for k in k_values:
        run_for_k(k, embeddings, coords, metadata, plot=args.plot)

    print("\nDone. Check embeddings/ for cluster JSON files and UMAP plots.")
    print("Key files to review:")
    for k in k_values:
        print(f"  prompts_k{k}.json — extracted prompts for generative step")


if __name__ == "__main__":
    main()
    main()
