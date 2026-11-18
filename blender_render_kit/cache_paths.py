"""Centralized cache directory management for inspection files."""

from pathlib import Path


CACHE_DIR_NAME = ".inspection_cache"


def get_cache_directory(working_dir):
    """
    Get the centralized cache directory for inspection files.

    Creates if doesn't exist.

    Args:
        working_dir: Working directory (where .blend files are)

    Returns:
        Path to cache directory
    """
    cache_dir = Path(working_dir) / CACHE_DIR_NAME
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def get_inspection_cache_path(blend_path, working_dir):
    """
    Get path to inspection cache metadata file in centralized cache dir.

    Args:
        blend_path: Path to .blend file
        working_dir: Working directory

    Returns:
        Path to metadata JSON file
    """
    cache_dir = get_cache_directory(working_dir)
    blend_name = Path(blend_path).stem
    return cache_dir / f".{blend_name}_inspection_cache.json"


def get_inspection_path(blend_path, working_dir):
    """
    Get path to inspection.json file in centralized cache dir.

    Args:
        blend_path: Path to .blend file
        working_dir: Working directory

    Returns:
        Path to inspection JSON file
    """
    cache_dir = get_cache_directory(working_dir)
    blend_name = Path(blend_path).stem
    return cache_dir / f"{blend_name}_inspection.json"
