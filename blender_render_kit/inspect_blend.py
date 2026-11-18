"""Inspect a .blend and write a detailed View Layer and collection report."""

import json
import sys
import traceback
from pathlib import Path

import bpy

# Add kit directory to Python path so we can import local modules
sys.path.insert(0, str(Path(__file__).parent))

from inspection_cache import save_cache_metadata


def get_script_arguments():
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def collect_layer_collections(layer_collection, parent_path="", parent_excluded=False):
    collection = layer_collection.collection
    path = f"{parent_path}/{collection.name}" if parent_path else collection.name
    excluded = layer_collection.exclude
    effectively_excluded = parent_excluded or excluded

    result = {
        "name": collection.name,
        "path": path,
        "exclude": excluded,
        "effectively_excluded": effectively_excluded,
        "state": "excluded" if effectively_excluded else "included",
        "children": [],
    }

    for child in layer_collection.children:
        result["children"].append(
            collect_layer_collections(
                child,
                parent_path=path,
                parent_excluded=effectively_excluded,
            )
        )

    return result


def get_render_scene(kit_directory):
    master_path = kit_directory / "render_master.json"
    if not master_path.is_file():
        raise FileNotFoundError(f"Master JSON not found: {master_path}")

    master = json.loads(master_path.read_text(encoding="utf-8"))
    scene_name = master.get("scene")
    scene = bpy.data.scenes.get(scene_name) if scene_name else bpy.context.scene
    if scene is None:
        raise ValueError(f"Scene not found in .blend: {scene_name!r}")
    return scene


def build_render_config(scene):
    return {
        "schema_version": 1,
        "view_layers": [
            {
                "name": view_layer.name,
                "segments": [
                    {
                        "name": "segment_01",
                        "start": scene.frame_start,
                        "end": scene.frame_end,
                        "renderizar": True,
                    }
                ],
            }
            for view_layer in scene.view_layers
        ],
    }


def main():
    if not bpy.data.filepath:
        raise RuntimeError("Save the .blend file before exporting the inspection report.")

    arguments = get_script_arguments()
    unknown_arguments = [argument for argument in arguments if argument != "--config-only"]
    if unknown_arguments:
        raise ValueError(f"Unknown script arguments: {', '.join(unknown_arguments)}")

    blend_path = Path(bpy.data.filepath).resolve()
    kit_directory = Path(__file__).resolve().parent
    if kit_directory.parent != blend_path.parent:
        raise RuntimeError(
            "Copy the complete blender_render_kit folder next to the .blend file "
            "and run the inspector from that copy."
        )

    output_path = kit_directory / f"{blend_path.stem}_inspection.json"
    render_config_path = blend_path.parent / f"{blend_path.stem}_render_user.json"
    render_scene = get_render_scene(kit_directory)

    # Always generate inspection report (needed for caching and rendering)
    report = {
        "schema_version": 1,
        "blend_file": str(blend_path),
        "scenes": [],
    }

    for scene in bpy.data.scenes:
        scene_report = {
            "name": scene.name,
            "frame_range": {
                "start": scene.frame_start,
                "end": scene.frame_end,
            },
            "view_layers": [],
        }

        for view_layer in scene.view_layers:
            scene_report["view_layers"].append(
                {
                    "name": view_layer.name,
                    "collections": collect_layer_collections(
                        view_layer.layer_collection
                    ),
                }
            )

        report["scenes"].append(scene_report)

    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"INFORME: {output_path}")

    # Generate or preserve config
    if render_config_path.exists():
        print(
            "CONFIGURACION: existente; no se sobrescribio: "
            f"{render_config_path}"
        )
    else:
        render_config_path.write_text(
            json.dumps(build_render_config(render_scene), indent=2, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )
        print(f"CONFIGURACION: plantilla creada: {render_config_path}")

    # Save cache after inspection completes
    save_cache_metadata(blend_path, output_path)

    if "--config-only" in arguments:
        print("RESULTADO: OK - configuracion preparada; inspeccion guardada en cache.")
    else:
        print("RESULTADO: OK - inspeccion completada.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"RESULTADO: ERROR - {error}", file=sys.stderr, flush=True)
        traceback.print_exc()
        sys.exit(1)
