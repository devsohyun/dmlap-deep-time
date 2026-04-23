"""
Encode all images in manifest.json through CLIP and save embeddings.

Produces:
    embeddings/embeddings.npy      — shape (N, 512) float32 array of CLIP vectors
    embeddings/metadata.json       — parallel list of metadata dicts for each embedding

The index in embeddings.npy corresponds to the same index in metadata.json,
so embeddings[i] belongs to metadata[i].

Usage:
    python3 embed_images.py
    python3 embed_images.py --model ViT-B-32          # default
    python3 embed_images.py --model ViT-L-14          # larger, slower, richer
    python3 embed_images.py --species tardigrada       # test single species first
    python3 embed_images.py --dry-run                  # check what would be encoded
"""

import argparse
import json
from pathlib import Path

import numpy as np
import open_clip
import torch
from PIL import Image

from manifest import load_manifest

EMBEDDINGS_DIR = Path("embeddings")


def get_device() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    elif torch.cuda.is_available():
        return "cuda"
    else:
        return "cpu"


def load_clip_model(model_name: str, device: str):
    """
    Load CLIP model and preprocessing transform.
    ViT-B-32 is the default — fast, good quality, 512-dimensional embeddings.
    ViT-L-14 produces 768-dimensional embeddings, richer but slower.
    """
    print(f"Loading CLIP model {model_name} on {device}...")
    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name, pretrained="openai"
    )
    model = model.to(device)
    model.eval()  # disable dropout, set to inference mode
    return model, preprocess


def encode_images(
    entries: list[dict], model, preprocess, device: str, batch_size: int = 16
) -> tuple[np.ndarray, list[dict]]:
    """
    Encode a list of manifest entries through CLIP.
    Returns (embeddings array, metadata list) — parallel by index.
    Skips unreadable images and logs them.
    """
    embeddings = []
    metadata = []
    skipped = []

    total = len(entries)
    print(f"\nEncoding {total} images...\n")

    # Process in batches for efficiency
    for batch_start in range(0, total, batch_size):
        batch_entries = entries[batch_start : batch_start + batch_size]
        batch_tensors = []
        batch_meta = []

        for entry in batch_entries:
            path = Path(entry["path"])
            if not path.exists():
                print(f"  [skip] {path.name} — file not found")
                skipped.append(entry["path"])
                continue

            try:
                # Load and preprocess
                # .convert("RGB") handles:
                #   - greyscale SEM images (single channel → 3 channel)
                #   - PNG with alpha channel (4 channel → 3 channel)
                #   - any other format PIL can read
                image = Image.open(path).convert("RGB")
                tensor = preprocess(image)  # resize, normalise to CLIP's expected input
                batch_tensors.append(tensor)
                batch_meta.append(entry)

            except Exception as e:
                print(f"  [skip] {path.name} — {e}")
                skipped.append(entry["path"])

        if not batch_tensors:
            continue

        # Stack into batch tensor and encode
        batch = torch.stack(batch_tensors).to(device)

        with torch.no_grad():  # no gradients needed — inference only
            features = model.encode_image(batch)
            # L2 normalise — makes cosine similarity equivalent to dot product
            # standard practice for CLIP embeddings
            features = features / features.norm(dim=-1, keepdim=True)

        # Move back to CPU and convert to numpy
        batch_embeddings = features.cpu().numpy().astype(np.float32)

        embeddings.append(batch_embeddings)
        metadata.extend(batch_meta)

        # Progress
        done = min(batch_start + batch_size, total)
        print(f"  {done}/{total} encoded", end="\r")

    print(f"\n\nDone — {len(metadata)} encoded, {len(skipped)} skipped")
    if skipped:
        print("\nSkipped:")
        for p in skipped:
            print(f"  {p}")

    embeddings_array = np.vstack(embeddings) if embeddings else np.array([])
    return embeddings_array, metadata


def save_embeddings(embeddings: np.ndarray, metadata: list[dict]):
    """Save embeddings and metadata to disk."""
    EMBEDDINGS_DIR.mkdir(exist_ok=True)

    embeddings_path = EMBEDDINGS_DIR / "embeddings.npy"
    metadata_path = EMBEDDINGS_DIR / "metadata.json"

    np.save(embeddings_path, embeddings)
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print("\nSaved:")
    print(f"  {embeddings_path}  — shape {embeddings.shape}")
    print(f"  {metadata_path}   — {len(metadata)} entries")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", default="ViT-B-32", help="CLIP model name (default: ViT-B-32)"
    )
    parser.add_argument("--species", help="Encode single species only (for testing)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be encoded without running",
    )
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    # Load manifest
    entries = load_manifest()
    if args.species:
        entries = [e for e in entries if e["species"] == args.species]
        print(f"Filtered to {args.species}: {len(entries)} images")

    if not entries:
        print("No images found — check manifest.py")
        return

    if args.dry_run:
        print(f"\nWould encode {len(entries)} images using {args.model}")
        print("\nBreakdown by species:")
        by_species: dict[str, int] = {}
        for e in entries:
            by_species[e["species"]] = by_species.get(e["species"], 0) + 1
        for k, v in sorted(by_species.items()):
            print(f"  {k:40s} {v}")
        return

    device = get_device()
    print(f"Device: {device}")

    model, preprocess = load_clip_model(args.model, device)
    embeddings, metadata = encode_images(
        entries, model, preprocess, device, batch_size=args.batch_size
    )

    if len(embeddings) == 0:
        print("No embeddings produced — check image paths")
        return

    save_embeddings(embeddings, metadata)

    # Quick sanity check
    print("\nSanity check:")
    print(f"  Embedding dimensions: {embeddings.shape[1]}")
    print(
        f"  First embedding norm: {np.linalg.norm(embeddings[0]):.4f} (should be ~1.0)"
    )
    print("  Species in embeddings:")
    by_species = {}
    for m in metadata:
        by_species[m["species"]] = by_species.get(m["species"], 0) + 1
    for k, v in sorted(by_species.items()):
        print(f"    {k:40s} {v}")


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
