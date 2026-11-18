"""Render Blender View Layers using the master and per-project JSON files."""

import json
import re
import sys
import time
import traceback
from pathlib import Path

import bpy


OPTIONS = {"--dry-run", "--overwrite-existing"}


def get_script_arguments():
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def get_config_path(arguments, filename):
    config_arguments = [argument for argument in arguments if argument not in OPTIONS]
    if config_arguments:
        if len(config_arguments) > 1:
            raise ValueError("Provide at most one user JSON path.")
        return Path(config_arguments[0]).resolve()

    return Path(__file__).resolve().with_name(filename)


def collect_layer_collections(
    layer_collection,
    parent_path="",
    result=None,
    parents=None,
    children=None,
):
    if result is None:
        result = {}
    if parents is None:
        parents = {}
    if children is None:
        children = {}
    collection_name = layer_collection.collection.name
    path = f"{parent_path}/{collection_name}" if parent_path else collection_name
    if path in result:
        raise ValueError(f"Duplicate collection path in Blender: {path}")
    result[path] = layer_collection
    parents[path] = parent_path or None
    children[path] = []
    if parent_path:
        children[parent_path].append(path)

    for child in layer_collection.children:
        collect_layer_collections(child, path, result, parents, children)
    return result, parents, children


def safe_path_token(value):
    token = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value.strip())
    token = re.sub(r"\s+", "_", token)
    return token or "unnamed"


def resolve_included_collections(view_layer, configured_names):
    if not isinstance(configured_names, list) or not configured_names:
        raise ValueError(
            f"View Layer {view_layer.name!r} needs at least one included collection."
        )
    if any(not isinstance(name, str) or not name.strip() for name in configured_names):
        raise ValueError(
            f"Collection selectors for View Layer {view_layer.name!r} "
            "must be non-empty strings."
        )

    layer_nodes, parents, children = collect_layer_collections(
        view_layer.layer_collection
    )
    selected_paths = set()
    for selector in configured_names:
        if selector in layer_nodes:
            matches = [selector]
        else:
            matches = [
                path
                for path, layer_collection in layer_nodes.items()
                if layer_collection.collection.name == selector
            ]
        if not matches:
            raise ValueError(
                f"Collection {selector!r} not found in View Layer "
                f"{view_layer.name!r}."
            )
        if len(matches) > 1:
            raise ValueError(
                f"Collection name {selector!r} is ambiguous in "
                f"{view_layer.name!r}; use its full collection path."
            )

        path = matches[0]
        pending = [path]
        while pending:
            current = pending.pop()
            selected_paths.add(current)
            pending.extend(children[current])
        ancestor = parents[path]
        while ancestor:
            selected_paths.add(ancestor)
            ancestor = parents[ancestor]

    return (
        layer_nodes,
        {path: path not in selected_paths for path in layer_nodes},
    )


def collect_collection_states(
    layer_collection,
    collection_exclusions=None,
    parent_path="",
    parent_excluded=False,
    states=None,
):
    if states is None:
        states = {}

    collection_name = layer_collection.collection.name
    path = f"{parent_path}/{collection_name}" if parent_path else collection_name
    excluded = (
        collection_exclusions[path]
        if collection_exclusions is not None
        else layer_collection.exclude
    )
    effectively_excluded = parent_excluded or excluded
    states[path] = effectively_excluded

    for child in layer_collection.children:
        collect_collection_states(
            child,
            collection_exclusions=collection_exclusions,
            parent_path=path,
            parent_excluded=effectively_excluded,
            states=states,
        )
    return states


def build_jobs(master, user_config):
    jobs = []
    blend_path = Path(bpy.data.filepath).resolve()
    output_patterns = set()

    if "format" in master:
        raise ValueError("Remove format from the master JSON; use the .blend setting.")

    scene_name = master.get("scene")
    scene = bpy.data.scenes.get(scene_name) if scene_name else bpy.context.scene
    if scene is None:
        raise ValueError(f"Scene not found in .blend: {scene_name!r}")

    output_root_value = master.get("output_root")
    directory_pattern = master.get("output_directory_pattern")
    filename_pattern = master.get("filename_pattern")
    if not all(
        isinstance(value, str) and value
        for value in (output_root_value, directory_pattern, filename_pattern)
    ):
        raise ValueError("Master JSON needs output_root and output patterns.")

    if output_root_value.startswith("//"):
        output_root = Path(bpy.path.abspath(output_root_value)).resolve()
    else:
        output_root = Path(output_root_value)
        if not output_root.is_absolute():
            output_root = blend_path.parent / output_root
        output_root = output_root.resolve()
    try:
        output_root.relative_to(blend_path.parent)
    except ValueError as error:
        raise ValueError("output_root must stay inside the .blend file folder.") from error
    blend_token = safe_path_token(blend_path.stem)

    view_layers = user_config.get("view_layers")
    if not isinstance(view_layers, list) or not view_layers:
        raise ValueError("User JSON must contain at least one View Layer.")
    configured_layer_names = set()

    for layer_data in view_layers:
        layer_name = layer_data.get("name")
        if not isinstance(layer_name, str) or not layer_name:
            raise ValueError("Every user-configured View Layer needs a name.")
        if layer_name in configured_layer_names:
            raise ValueError(f"Duplicate View Layer in user JSON: {layer_name!r}")
        configured_layer_names.add(layer_name)

        view_layer = scene.view_layers.get(layer_name)
        if view_layer is None:
            raise ValueError(
                f"View Layer {layer_name!r} not found in scene {scene.name!r}"
            )

        if "include_collections" in layer_data:
            layer_collections, collection_exclusions = resolve_included_collections(
                view_layer, layer_data["include_collections"]
            )
        else:
            layer_collections, _, _ = collect_layer_collections(
                view_layer.layer_collection
            )
            collection_exclusions = None
        collection_states = collect_collection_states(
            view_layer.layer_collection, collection_exclusions
        )
        segments = layer_data.get("segments")
        if not isinstance(segments, list) or not segments:
            raise ValueError(
                f"View Layer {layer_name!r} must have at least one segment."
            )

        segment_names = set()
        segment_ranges = []
        layer_token = safe_path_token(layer_name)
        for segment in segments:
            segment_name = segment.get("name")
            if not isinstance(segment_name, str) or not segment_name:
                raise ValueError(
                    f"Every segment in View Layer {layer_name!r} needs a name."
                )
            if segment_name in segment_names:
                raise ValueError(
                    f"Duplicate segment name {segment_name!r} "
                    f"in View Layer {layer_name!r}."
                )
            segment_names.add(segment_name)

            start = segment.get("start")
            end = segment.get("end")
            if (
                not isinstance(start, int)
                or isinstance(start, bool)
                or not isinstance(end, int)
                or isinstance(end, bool)
                or start > end
            ):
                raise ValueError(
                    f"Invalid frame range for {layer_name!r}/{segment_name!r}: "
                    f"{start!r}..{end!r}"
                )

            should_render = segment.get("renderizar", True)
            if not isinstance(should_render, bool):
                raise ValueError(
                    f"'renderizar' must be boolean (true/false) for "
                    f"{layer_name!r}/{segment_name!r}"
                )

            if not should_render:
                print(f"  ⏭️  Saltando: {layer_name}/{segment_name} (renderizar: false)", flush=True)
                continue

            for previous_name, previous_start, previous_end in segment_ranges:
                if start <= previous_end and previous_start <= end:
                    print(
                        f"Warning: inclusive frame ranges overlap for "
                        f"{layer_name!r}: {previous_name!r} and {segment_name!r}.",
                        flush=True,
                    )
            segment_ranges.append((segment_name, start, end))

            segment_token = safe_path_token(segment_name)
            directory_relative = Path(
                directory_pattern.format(
                    blend_name=blend_token,
                    view_layer=layer_token,
                    segment=segment_token,
                )
            )
            if directory_relative.is_absolute() or ".." in directory_relative.parts:
                raise ValueError(
                    "output_directory_pattern must stay inside output_root."
                )
            output_directory = output_root / directory_relative
            output_filename = filename_pattern.format(
                blend_name=blend_token,
                view_layer=layer_token,
                segment=segment_token,
            )
            if Path(output_filename).name != output_filename:
                raise ValueError("filename_pattern must produce a filename.")

            output_base = output_directory / output_filename
            pattern_key = str(output_base).casefold()
            if pattern_key in output_patterns:
                raise ValueError(f"Duplicate render output pattern: {output_base}")
            output_patterns.add(pattern_key)

            jobs.append(
                {
                    "scene": scene,
                    "view_layer": view_layer,
                    "segment_name": segment_name,
                    "collection_exclusions": collection_exclusions,
                    "collection_states": collection_states,
                    "layer_collections": layer_collections,
                    "start": start,
                    "end": end,
                    "output_directory": output_directory,
                    "output_base": output_base,
                    "file_format": scene.render.image_settings.file_format,
                }
            )

    if not jobs:
        raise ValueError("The user JSON contains no render segments.")
    return jobs


def job_frame_count(job):
    frame_step = max(1, int(job["scene"].frame_step))
    return (job["end"] - job["start"]) // frame_step + 1


def render_jobs(jobs):
    total_frames = sum(job_frame_count(job) for job in jobs)
    completed_frames = 0
    completed_frame_seconds = 0.0
    render_started_at = time.monotonic()
    last_frame_written_at = render_started_at
    last_heartbeat_at = render_started_at
    frame_started_at = None

    def report_frame_written(scene):
        nonlocal completed_frames, completed_frame_seconds, last_frame_written_at
        nonlocal frame_started_at
        now = time.monotonic()
        start_time = frame_started_at or last_frame_written_at
        frame_seconds = now - start_time
        completed_frame_seconds += frame_seconds
        last_frame_written_at = now
        frame_started_at = None
        completed_frames += 1
        print(
            f"RENDER_PROGRESS|{completed_frames}|{total_frames}|{scene.frame_current}|"
            f"{frame_seconds:.3f}|{completed_frame_seconds:.3f}",
            flush=True,
        )

    def report_frame_started(scene):
        nonlocal frame_started_at
        if completed_frames < total_frames:
            frame_started_at = time.monotonic()
            print(f"RENDER_FRAME_START|{scene.frame_current}", flush=True)

    def report_render_stats(_stats):
        nonlocal last_heartbeat_at
        now = time.monotonic()
        if now - last_heartbeat_at >= 1.0:
            last_heartbeat_at = now
            print("RENDER_HEARTBEAT", flush=True)

    bpy.app.handlers.render_write.append(report_frame_written)
    bpy.app.handlers.frame_change_pre.append(report_frame_started)
    bpy.app.handlers.render_stats.append(report_render_stats)
    try:
        print(f"RENDER_START|{total_frames}", flush=True)
        render_jobs_with_progress(jobs)
    finally:
        bpy.app.handlers.render_write.remove(report_frame_written)
        bpy.app.handlers.frame_change_pre.remove(report_frame_started)
        bpy.app.handlers.render_stats.remove(report_render_stats)


def render_jobs_with_progress(jobs):
    if not jobs:
        return

    scene = jobs[0]["scene"]
    original_view_layer_states = [
        (view_layer, view_layer.use) for view_layer in scene.view_layers
    ]
    try:
        for index, job in enumerate(jobs, start=1):
            scene = job["scene"]
            view_layer = job["view_layer"]
            output_base = job["output_base"]
            output_directory = job["output_directory"]
            file_format = job["file_format"]

            for scene_view_layer in scene.view_layers:
                scene_view_layer.use = scene_view_layer.name == view_layer.name

            # Force only one active view layer: disable all others explicitly
            active_count = sum(1 for vl in scene.view_layers if vl.use)
            if active_count != 1 or not view_layer.use:
                raise RuntimeError(
                    f"Failed to isolate View Layer {view_layer.name!r}: "
                    f"{active_count} view layers are active (expected 1)"
                )

            output_directory.mkdir(parents=True, exist_ok=True)
            if job["collection_exclusions"] is not None:
                for path, excluded in job["collection_exclusions"].items():
                    job["layer_collections"][path].exclude = excluded

            scene.render.filepath = str(output_base)
            scene.render.use_file_extension = True

            print(
                f"[{index}/{len(jobs)}] Rendering {scene.name} / {view_layer.name} / "
                f"{job['segment_name']}: "
                f"frames {job['start']}-{job['end']} to {output_base}",
                flush=True,
            )

            frame_step = max(1, int(scene.frame_step))
            frame = job["start"]
            while frame <= job["end"]:
                scene.frame_set(frame)
                result = bpy.ops.render.render(
                    write_still=True,
                    scene=scene.name,
                    layer=view_layer.name,
                )
                if "CANCELLED" in result:
                    raise KeyboardInterrupt
                if "FINISHED" not in result:
                    raise RuntimeError(
                        f"Blender did not finish rendering frame {frame} for "
                        f"{view_layer.name!r}/{job['segment_name']!r}: {result}"
                    )
                frame += frame_step

    finally:
        for view_layer, use in original_view_layer_states:
            view_layer.use = use


def validate_output_paths(jobs, overwrite_existing=True):
    for job in jobs:
        output_directory = job["output_directory"]
        if not output_directory.exists():
            continue

        filename_glob = job["output_base"].name.replace("#", "?")
        existing_files = list(output_directory.glob(f"{filename_glob}.*"))
        if existing_files and not overwrite_existing:
            raise FileExistsError(
                f"Render outputs already exist for "
                f"{job['view_layer'].name!r}/{job['segment_name']!r}; "
                f"refusing to overwrite: "
                f"{existing_files[0]}"
            )
        if existing_files:
            print(
                f"Will overwrite {len(existing_files)} matching file(s) for "
                f"{job['view_layer'].name!r}/{job['segment_name']!r}.",
                flush=True,
            )


def print_plan(jobs):
    total_frames = 0
    printed_layers = set()
    for job in jobs:
        frame_count = job_frame_count(job)
        total_frames += frame_count
        layer_key = (job["scene"].name, job["view_layer"].name)
        if layer_key not in printed_layers:
            printed_layers.add(layer_key)
            root_name = job["view_layer"].layer_collection.collection.name
            included = [
                path
                for path, excluded in job["collection_states"].items()
                if not excluded and path != root_name
            ]
            excluded = [
                path
                for path, is_excluded in job["collection_states"].items()
                if is_excluded and path != root_name
            ]
            print(f"View Layer: {job['view_layer'].name}", flush=True)
            print(
                "  Colecciones incluidas: "
                + (", ".join(included) if included else "ninguna"),
                flush=True,
            )
            print(
                "  Colecciones excluidas: "
                + (", ".join(excluded) if excluded else "ninguna"),
                flush=True,
            )
        print(
            f"  Segmento: {job['segment_name']} | "
            f"fotogramas {job['start']}-{job['end']} ({frame_count}) | "
            f"{job['file_format']} -> {job['output_base']}",
            flush=True,
        )
    print(
        f"Plan: {len(jobs)} segmentos, {total_frames} fotogramas.",
        flush=True,
    )
    return len(jobs), total_frames


def main():
    if not bpy.data.filepath:
        raise RuntimeError("Open a saved .blend file before running this script.")

    blend_path = Path(bpy.data.filepath).resolve()
    kit_directory = Path(__file__).resolve().parent
    if kit_directory.parent != blend_path.parent:
        raise RuntimeError(
            "Copy the complete blender_render_kit folder next to the .blend file "
            "and run the render script from that copy."
        )

    arguments = get_script_arguments()
    unknown_arguments = [
        argument for argument in arguments
        if argument not in OPTIONS and not argument.lower().endswith(".json")
    ]
    if unknown_arguments:
        raise ValueError(f"Unknown script arguments: {', '.join(unknown_arguments)}")

    master_path = Path(__file__).resolve().with_name("render_master.json")
    if not master_path.is_file():
        raise FileNotFoundError(f"Master JSON not found: {master_path}")
    master = json.loads(master_path.read_text(encoding="utf-8"))
    user_config_filename = master.get("user_config_filename")
    if (
        not isinstance(user_config_filename, str)
        or not user_config_filename
        or Path(user_config_filename).name != user_config_filename
    ):
        raise ValueError("Master JSON needs a simple user_config_filename.")

    config_path = get_config_path(arguments, user_config_filename)
    if not config_path.is_file():
        raise FileNotFoundError(f"User JSON not found: {config_path}")
    user_config = json.loads(config_path.read_text(encoding="utf-8"))
    jobs = build_jobs(master, user_config)
    validate_output_paths(jobs, overwrite_existing=True)
    segment_count, total_frames = print_plan(jobs)

    if "--dry-run" in arguments:
        print(
            f"RESULTADO: OK - dry-run completado: {segment_count} segmentos, "
            f"{total_frames} fotogramas planificados. No se inicio ningun render.",
            flush=True,
        )
        return

    render_jobs(jobs)
    print(
        f"RESULTADO: OK - render completado: {segment_count} segmentos, "
        f"{total_frames} fotogramas. Configuracion: {config_path}",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(
            "RESULTADO: CANCELADO - render interrumpido por el usuario (Ctrl+C).",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(130)
    except Exception as error:
        print(f"RESULTADO: ERROR - {error}", file=sys.stderr, flush=True)
        traceback.print_exc()
        sys.exit(1)
