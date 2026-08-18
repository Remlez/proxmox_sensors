"""Helpers for derived VM and container metrics."""


def calculate_usage_percentage(used, total):
    """Return a rounded usage percentage or ``None`` for unusable input."""
    try:
        used_value = float(used)
        total_value = float(total)
    except (TypeError, ValueError):
        return None

    if used_value < 0 or total_value <= 0:
        return None

    return round((used_value / total_value) * 100, 2)
