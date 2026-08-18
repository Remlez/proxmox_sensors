"""Resolve the PVE config entry that should handle a global service call."""

from typing import Any


def _entry_nodes(entry_data: dict[str, Any]) -> set[str]:
    """Return all node names known to one runtime entry."""
    nodes: set[str] = set()

    configured_node = entry_data.get("node")
    if configured_node:
        nodes.add(str(configured_node))

    coordinator = entry_data.get("coordinator")
    coordinator_data = getattr(coordinator, "data", None)
    if isinstance(coordinator_data, dict):
        nodes.update(str(node) for node in coordinator_data.get("cluster_nodes", []))

    return nodes


def resolve_pve_service_target(
    domain_data: dict[str, dict[str, Any]],
    *,
    node: str | None,
    entry_id: str | None = None,
) -> dict[str, Any]:
    """Select one loaded PVE entry, rejecting missing or ambiguous targets."""
    pve_entries = {
        candidate_id: entry_data
        for candidate_id, entry_data in domain_data.items()
        if entry_data.get("server_type") == "PVE"
    }

    if entry_id:
        selected = pve_entries.get(entry_id)
        if selected is None:
            raise ValueError(f"PVE config entry '{entry_id}' is not loaded")
        if node and node not in _entry_nodes(selected):
            raise ValueError(
                f"Node '{node}' does not belong to PVE config entry '{entry_id}'"
            )
        return selected

    matches = [
        entry_data
        for entry_data in pve_entries.values()
        if not node or node in _entry_nodes(entry_data)
    ]
    if not matches:
        target = f" for node '{node}'" if node else ""
        raise ValueError(f"No loaded PVE config entry found{target}")
    if len(matches) > 1:
        raise ValueError(
            "Multiple PVE config entries match this service call; select entry_id"
        )
    return matches[0]
