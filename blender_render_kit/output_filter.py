"""Filter and clean Blender render output for readability."""


def should_print(line):
    """
    Determine if a line should be printed to user.

    Filters out collection verbose output, keeps only important render info.

    Args:
        line: Output line from Blender/Python

    Returns:
        True if line should be printed, False if it should be filtered
    """
    # Keep critical render messages
    if any(x in line for x in [
        "Plan:",
        "[",  # For [X/Y] Rendering lines
        "RENDER_STATUS:",
        "RESULTADO:",
        "Renderizando",  # PowerShell status
        "[Segmento",  # PowerShell segment markers
        "[OK]",  # PowerShell completion
        "[+]",  # PowerShell continuation
    ]):
        return True

    # Filter out verbose collection output
    if any(x in line for x in [
        "Colecciones incluidas:",
        "Colecciones excluidas:",
        "Scene Collection/",
        "View Layer:",
        "INFORME:",
        "CONFIGURACION:",
        "Could not open",
        "Unable to open",
        "ERROR Cannot set slot",
    ]):
        return False

    # Keep empty lines for readability
    if not line.strip():
        return True

    return False


def format_with_blend_name(line, blend_name):
    """
    Add blend filename prefix to important render lines.

    Args:
        line: Output line
        blend_name: Blend file name (without path)

    Returns:
        Formatted line with prefix
    """
    # Only prefix important lines
    if any(x in line for x in ["Plan:", "[1/", "RESULTADO:", "RENDER_STATUS:"]):
        return f"[{blend_name}] {line}"

    return line
