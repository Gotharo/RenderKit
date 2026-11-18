"""Update render_state.json after each segment completes to track progress."""

import json
from pathlib import Path


def save_segment_completion(working_dir, view_layer_name, segment_name, last_frame):
    """
    Save state after a segment completes to enable per-segment resumption.

    This allows PowerShell loop to detect which segment just finished
    and proceed to the next one.

    Args:
        working_dir: Working directory (where .blend file is)
        view_layer_name: Name of view layer just rendered
        segment_name: Name of segment just rendered
        last_frame: Last frame number of segment
    """
    state_path = Path(working_dir) / "render_state.json"

    state = {
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
