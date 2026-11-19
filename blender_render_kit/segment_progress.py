"""Update render_state.json after each segment completes to track progress."""

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


def save_segment_completion(working_dir, blend_name, view_layer_name, segment_name, last_frame):
    """
    Save state after a segment completes to enable per-segment resumption.

    Uses per-file render_state so multiple files don't interfere.

    Args:
        working_dir: Working directory (where .blend file is)
        blend_name: Blend file stem (without .blend extension)
        view_layer_name: Name of view layer just rendered
        segment_name: Name of segment just rendered
        last_frame: Last frame number of segment
    """
    state_path = get_render_state_path(working_dir, blend_name)

    state = {
        "blend_file": blend_name,
        "view_layer": view_layer_name,
        "segment": segment_name,
        "frame": last_frame,
    }

    try:
        state_path.write_text(
            json.dumps(state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except IOError as e:
        print(f"Warning: Could not save segment progress: {e}", flush=True)
