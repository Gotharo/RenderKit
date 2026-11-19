"""Manage segment rendering state to enable per-segment execution."""

import json
from pathlib import Path


def get_render_state_path(working_dir, blend_name):
    """
    Get path to render_state.json for a specific blend file.

    Per-file render state prevents interference between multiple files.

    Args:
        working_dir: Working directory
        blend_name: Blend file stem (without .blend extension)

    Returns:
        Path to render_state JSON file for this blend
    """
    return Path(working_dir) / f"render_state_{blend_name}.json"


def read_render_state(working_dir, blend_name):
    """
    Read render_state.json for specific blend to determine which segment was last completed.

    Args:
        working_dir: Working directory
        blend_name: Blend file stem (without .blend extension)

    Returns dict with keys:
    - blend_file: Name of .blend file
    - view_layer: Name of last rendered view layer
    - segment: Name of last rendered segment
    - frame: Last rendered frame number

    Returns None if file doesn't exist (first run for this blend).
    """
    state_path = get_render_state_path(working_dir, blend_name)
    if not state_path.exists():
        return None

    try:
        with open(state_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def find_next_segment(jobs, current_state):
    """
    Find the next segment to render based on current state.

    Args:
        jobs: List of render jobs (segments) from render_batch.py
        current_state: Current state from render_state.json (or None if first run)

    Returns:
        Index of next job to render, or None if all complete
    """
    if current_state is None:
        return 0  # First run: start with first segment

    current_view_layer = current_state.get("view_layer")
    current_segment = current_state.get("segment")

    # Find the job that matches current state
    for idx, job in enumerate(jobs):
        if (job["view_layer"].name == current_view_layer and
            job["segment_name"] == current_segment):
            # Found current job, return next one
            return idx + 1 if idx + 1 < len(jobs) else None

    return None  # All segments complete


def has_more_segments_after(jobs, working_dir, blend_name):
    """
    Check if there are MORE segments after the one just completed.

    Returns True if there's another segment to render, False if all complete.

    Args:
        jobs: All render jobs
        working_dir: Working directory
        blend_name: Blend file stem
    """
    state = read_render_state(working_dir, blend_name)
    next_idx = find_next_segment(jobs, state)
    return next_idx is not None


def get_jobs_to_render(jobs, working_dir, blend_name):
    """
    Filter jobs to render only the next segment for this blend.

    Returns list with zero or one job (the next segment).

    Args:
        jobs: All render jobs
        working_dir: Working directory
        blend_name: Blend file stem
    """
    state = read_render_state(working_dir, blend_name)
    next_idx = find_next_segment(jobs, state)

    if next_idx is None:
        return []  # All segments complete

    return [jobs[next_idx]]  # Return only the next segment
