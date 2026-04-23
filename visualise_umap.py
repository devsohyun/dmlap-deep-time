"""
visualise_umap.py
Reduce CLIP embeddings to 2D with UMAP and plot.

Produces two plots saved to embeddings/:
    umap_by_species.png    — each species a different colour
    umap_by_category.png   — each conceptual category a different colour

Usage:
    python3 visualise_umap.py
    python3 visualise_umap.py --n-neighbors 15   # default
    python3 visualise_umap.py --n-neighbors 5    # tighter local structure
    python3 visualise_umap.py --n-neighbors 30   # broader global structure
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from umap import UMAP

EMBEDDINGS_DIR = Path("embeddings")


def load_embeddings():
    embeddings = np.load(EMBEDDINGS_DIR / "embeddings.npy")
    with open(EMBEDDINGS_DIR / "metadata.json") as f:
        metadata = json.load(f)
    print(f"Loaded {len(metadata)} embeddings, shape {embeddings.shape}")
    return embeddings, metadata


def run_umap(embeddings: np.ndarray, n_neighbors: int = 15, min_dist: float = 0.1):
    """
    Reduce 512-dimensional CLIP embeddings to 2D.

    n_neighbors: controls local vs global structure balance.
        Low  (5)  — tight clusters, local detail, may fragment species
        Mid  (15) — good default balance
        High (30) — broader structure, categories may be more visible

    min_dist: how tightly points are packed in 2D.
        Lower = tighter clusters, higher = more spread out.
    """
    print(f"\nRunning UMAP (n_neighbors={n_neighbors}, min_dist={min_dist})...")
    reducer = UMAP(
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        n_components=2,
        metric="cosine",  # cosine distance is natural for L2-normalised CLIP embeddings
        random_state=42,  # reproducible results
    )
    coords = reducer.fit_transform(embeddings)
    print(f"UMAP complete — output shape {coords.shape}")
    return coords


def plot_by_species(coords: np.ndarray, metadata: list[dict], save_path: Path):
    """Plot UMAP coloured by species."""

    species_list = sorted(set(m["species"] for m in metadata))

    # Colour palette — enough distinct colours for 9-10 species
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
    ]
    colour_map = {s: colours[i % len(colours)] for i, s in enumerate(species_list)}

    fig, ax = plt.subplots(figsize=(12, 9))
    fig.patch.set_facecolor("#0D0D0D")
    ax.set_facecolor("#0D0D0D")

    # Plot each species
    for species in species_list:
        indices = [i for i, m in enumerate(metadata) if m["species"] == species]
        x = coords[indices, 0]
        y = coords[indices, 1]
        ax.scatter(
            x,
            y,
            c=colour_map[species],
            s=40,
            alpha=0.85,
            edgecolors="none",
            label=species.replace("_", " "),
        )

    # Legend
    legend = ax.legend(
        loc="upper left",
        framealpha=0.15,
        facecolor="#1a1a1a",
        edgecolor="#444",
        fontsize=8,
        labelcolor="white",
    )

    ax.set_title("CLIP latent space — by species", color="white", fontsize=13, pad=14)
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


def plot_by_category(coords: np.ndarray, metadata: list[dict], save_path: Path):
    """
    Plot UMAP coloured by your four conceptual categories.
    This is the artistically significant plot — does the machine's
    grouping align with your framing or cut across it?
    """

    category_colours = {
        "evolutionary_continuity": "#E63946",
        "resilience": "#2A9D8F",
        "longevity": "#E9C46A",
        "persistence": "#457B9D",
    }

    # Marker shapes per category — adds second visual channel beyond colour
    category_markers = {
        "evolutionary_continuity": "o",
        "resilience": "s",  # square
        "longevity": "^",  # triangle
        "persistence": "D",  # diamond
    }

    fig, ax = plt.subplots(figsize=(12, 9))
    fig.patch.set_facecolor("#0D0D0D")
    ax.set_facecolor("#0D0D0D")

    categories = sorted(set(m["category"] for m in metadata))

    for category in categories:
        indices = [i for i, m in enumerate(metadata) if m["category"] == category]
        x = coords[indices, 0]
        y = coords[indices, 1]
        colour = category_colours.get(category, "#888888")
        marker = category_markers.get(category, "o")

        ax.scatter(
            x,
            y,
            c=colour,
            marker=marker,
            s=50,
            alpha=0.85,
            edgecolors="none",
            label=category.replace("_", " "),
        )

    legend = ax.legend(
        loc="upper left",
        framealpha=0.15,
        facecolor="#1a1a1a",
        edgecolor="#444",
        fontsize=9,
        labelcolor="white",
    )

    ax.set_title("CLIP latent space — by category", color="white", fontsize=13, pad=14)
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


def plot_by_image_type(coords: np.ndarray, metadata: list[dict], save_path: Path):
    """
    Plot coloured by image type — specimen_photo, sem_microscopy, field_photo etc.
    Reveals whether CLIP clusters by visual register rather than biology.
    """

    type_colours = {
        "specimen_photo": "#A8DADC",
        "sem_microscopy": "#E63946",
        "field_photo": "#2A9D8F",
        "deep_sea_still": "#457B9D",
        "botanical_illustration": "#E9C46A",
        "light_microscopy": "#F4A261",
    }

    image_types = sorted(set(m["image_type"] for m in metadata))

    fig, ax = plt.subplots(figsize=(12, 9))
    fig.patch.set_facecolor("#0D0D0D")
    ax.set_facecolor("#0D0D0D")

    for image_type in image_types:
        indices = [i for i, m in enumerate(metadata) if m["image_type"] == image_type]
        x = coords[indices, 0]
        y = coords[indices, 1]
        colour = type_colours.get(image_type, "#888888")
        ax.scatter(
            x,
            y,
            c=colour,
            s=40,
            alpha=0.85,
            edgecolors="none",
            label=image_type.replace("_", " "),
        )

    ax.legend(
        loc="upper left",
        framealpha=0.15,
        facecolor="#1a1a1a",
        edgecolor="#444",
        fontsize=9,
        labelcolor="white",
    )
    ax.set_title(
        "CLIP latent space — by image type", color="white", fontsize=13, pad=14
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-neighbors", type=int, default=15)
    parser.add_argument("--min-dist", type=float, default=0.1)
    args = parser.parse_args()

    embeddings, metadata = load_embeddings()
    coords = run_umap(embeddings, n_neighbors=args.n_neighbors, min_dist=args.min_dist)

    # Save coords for later use (clustering, etc.)
    np.save(EMBEDDINGS_DIR / "umap_coords.npy", coords)
    print("Saved: embeddings/umap_coords.npy")

    # Three plots — each asks a different question
    plot_by_species(coords, metadata, EMBEDDINGS_DIR / "umap_by_species.png")
    plot_by_category(coords, metadata, EMBEDDINGS_DIR / "umap_by_category.png")
    plot_by_image_type(coords, metadata, EMBEDDINGS_DIR / "umap_by_image_type.png")

    print("\nDone. Open embeddings/ to see the three plots.")
    print("\nWhat to look for:")
    print("  umap_by_species.png   — do same-species images cluster together?")
    print("  umap_by_category.png  — do your four categories form regions?")
    print(
        "  umap_by_image_type.png — does image register drive clustering more than biology?"
    )


if __name__ == "__main__":
    main()
    main()
