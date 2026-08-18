"""Helpers for detecting newly discovered entity-producing resources."""

from __future__ import annotations


def entity_topology_keys(data):
    """Return stable keys for resources that require entity creation."""
    if not isinstance(data, dict):
        return set()

    keys = set()
    for section in (
        "hardware",
        "physical_disks",
        "storage",
        "zfs_pools",
        "vms",
        "cts",
        "pbs_datastores",
    ):
        values = data.get(section, {})
        if isinstance(values, dict):
            keys.update(f"{section}:{key}" for key in values)

    memory = data.get("memory", {})
    if isinstance(memory, dict):
        for node, node_data in memory.items():
            if not isinstance(node_data, dict):
                continue
            dimms = node_data.get("dimms", {})
            if isinstance(dimms, dict):
                keys.update(f"memory:{node}:{dimm}" for dimm in dimms)

    return keys
