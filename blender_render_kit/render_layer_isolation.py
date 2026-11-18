"""Isolate view layers for rendering using Blender's render_single_layer flag."""


def isolate_render_layer(scene, target_view_layer):
    """
    Activate render_single_layer ONLY for the target view layer.
    All other view layers have it disabled.

    Args:
        scene: Blender scene object
        target_view_layer: The view layer to isolate for rendering

    Raises:
        RuntimeError: If isolation fails or target layer is not found
    """
    target_found = False

    for view_layer in scene.view_layers:
        is_target = view_layer.name == target_view_layer.name
        view_layer.render_single_layer = is_target

        if is_target:
            target_found = True

    if not target_found:
        raise RuntimeError(
            f"Target view layer {target_view_layer.name!r} not found in scene {scene.name!r}"
        )

    # Validate isolation
    isolated_count = sum(1 for vl in scene.view_layers if vl.render_single_layer)
    if isolated_count != 1:
        raise RuntimeError(
            f"Failed to isolate render_single_layer: {isolated_count} layers marked "
            f"(expected 1). Target was {target_view_layer.name!r}"
        )


def reset_render_layer_isolation(scene):
    """
    Disable render_single_layer for all view layers (restore original state).

    Args:
        scene: Blender scene object
    """
    for view_layer in scene.view_layers:
        view_layer.render_single_layer = False
