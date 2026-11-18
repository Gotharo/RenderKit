"""Manage inspection caching to avoid redundant .blend file inspection."""

import hashlib
import json
from pathlib import Path

try:
    from cache_paths import get_cache_directory, get_inspection_cache_path, get_inspection_path
    USE_CENTRALIZED_CACHE = True
except ImportError:
    USE_CENTRALIZED_CACHE = False


def compute_blend_hash(blend_path):
    """
    Compute SHA256 hash of .blend file for change detection.

    Args:
        blend_path: Path to .blend file

    Returns:
        Hex digest of SHA256 hash
    """
    sha256 = hashlib.sha256()
    with open(blend_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_cache_metadata_path(blend_path):
    """
    Get path where inspection cache metadata is stored.

    Args:
        blend_path: Path to .blend file

    Returns:
        Path to metadata JSON file (same directory as .blend)
    """
    blend_path = Path(blend_path)
    return blend_path.parent / f".{blend_path.stem}_inspection_cache.json"


def load_cache_metadata(metadata_path):
    """
    Load cache metadata if it exists.

    Args:
        metadata_path: Path to metadata JSON file

    Returns:
        Dict with 'blend_hash' and 'inspection_path', or None if not found
    """
    if not metadata_path.is_file():
        return None

    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def inspection_cache_valid(blend_path, inspection_path):
    """
    Check if cached inspection is valid (blend hasn't changed).

    Args:
        blend_path: Path to .blend file
        inspection_path: Path to _inspection.json file

    Returns:
        True if cache is valid and both files exist, False otherwise
    """
    blend_path = Path(blend_path)
    inspection_path = Path(inspection_path)

    if not inspection_path.is_file():
        return False

    metadata_path = get_cache_metadata_path(blend_path)
    metadata = load_cache_metadata(metadata_path)

    if metadata is None:
        return False

    current_hash = compute_blend_hash(blend_path)
    cached_hash = metadata.get("blend_hash")

    return current_hash == cached_hash


def save_cache_metadata(blend_path, inspection_path):
    """
    Save cache metadata after successful inspection.

    Args:
        blend_path: Path to .blend file
        inspection_path: Path to _inspection.json file
    """
    blend_path = Path(blend_path)
    metadata_path = get_cache_metadata_path(blend_path)

    metadata = {
        "blend_hash": compute_blend_hash(blend_path),
        "inspection_path": str(inspection_path),
    }

    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# === Centralized Cache Functions (Optional) ===
# Use these if cache_paths module is available

if USE_CENTRALIZED_CACHE:

    def inspection_cache_valid_centralized(blend_path, working_dir):
        """
        Check if cached inspection is valid using centralized cache directory.

        Args:
            blend_path: Path to .blend file
            working_dir: Working directory (where .blend files are)

        Returns:
            True if cache is valid and both files exist, False otherwise
        """
        blend_path = Path(blend_path)
        inspection_path = get_inspection_path(blend_path, working_dir)

        if not inspection_path.is_file():
            return False

        metadata_path = get_inspection_cache_path(blend_path, working_dir)
        metadata = load_cache_metadata(metadata_path)

        if metadata is None:
            return False

        current_hash = compute_blend_hash(blend_path)
        cached_hash = metadata.get("blend_hash")

        return current_hash == cached_hash

    def save_cache_metadata_centralized(blend_path, inspection_path, working_dir):
        """
        Save cache metadata to centralized cache directory.

        Args:
            blend_path: Path to .blend file
            inspection_path: Path to _inspection.json file
            working_dir: Working directory
        """
        blend_path = Path(blend_path)
        metadata_path = get_inspection_cache_path(blend_path, working_dir)

        metadata = {
            "blend_hash": compute_blend_hash(blend_path),
            "inspection_path": str(inspection_path),
        }

        metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
