"""Helper script to check inspection cache status."""

import sys
from pathlib import Path

try:
    # Add kit directory to path so we can import modules
    kit_dir = Path(__file__).parent
    sys.path.insert(0, str(kit_dir))

    from inspection_cache import inspection_cache_valid_centralized

    if len(sys.argv) < 2:
        print("USAGE: check_inspection_cache.py <blend_path>")
        sys.exit(1)

    blend_path = Path(sys.argv[1]).resolve()
    working_dir = blend_path.parent

    # Use centralized cache validation
    if inspection_cache_valid_centralized(blend_path, working_dir):
        print("CACHE_VALID")
        sys.exit(0)
    else:
        print("CACHE_INVALID")
        sys.exit(0)

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
