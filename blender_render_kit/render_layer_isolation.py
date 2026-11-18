"""Isolate view layers for rendering using Blender's use_single_layer flag."""


def isolate_render_layer(scene, target_view_layer):
    """
    Activate use_single_layer in render settings and ensure target view layer is active.
    This prevents multiple view layers from being rendered to the same EXR.

    Args:
        scene: Blender scene object
        target_view_layer: The view layer to isolate for rendering

    Raises:
        RuntimeError: If isolation fails or target layer is not found
    """
    target_found = False

    for view_layer in scene.view_layers:
        is_target = view_layer.name == target_view_layer.name
        view_layer.use = is_target

        if is_target:
            target_found = True

    if not target_found:
        raise RuntimeError(
            f"Target view layer {target_view_layer.name!r} not found in scene {scene.name!r}"
        )

    # Enable use_single_layer: only render the active view layer
    scene.render.use_single_layer = True

    # Validate isolation
    active_count = sum(1 for vl in scene.view_layers if vl.use)
    if active_count != 1:
        raise RuntimeError(
            f"Failed to isolate view layer: {active_count} layers marked as active "
            f"(expected 1). Target was {target_view_layer.name!r}"
        )


def reset_render_layer_isolation(scene):
    """
    Disable use_single_layer and restore default view layer states.

    Args:
        scene: Blender scene object
    """
    scene.render.use_single_layer = False

