# Run this after moving bad images out of their species folders into _rejected/

from pathlib import Path

from manifest import load_manifest, save_manifest

entries = load_manifest()
before = len(entries)

# Keep only entries where the file still exists on disk
clean = [e for e in entries if Path(e["path"]).exists()]
after = len(clean)

save_manifest(clean)
print(f"Removed {before - after} entries")
print(f"Manifest now has {after} images")
