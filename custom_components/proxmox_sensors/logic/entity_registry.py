"""Helpers for safely pruning integration entity registry entries."""


def is_obsolete_sensor_entity(entity_entry, sensor_unique_ids: set[str | None]) -> bool:
    """Return whether an entry belongs to this platform and is no longer created."""
    return (
        getattr(entity_entry, "domain", None) == "sensor"
        and getattr(entity_entry, "unique_id", None) not in sensor_unique_ids
    )
