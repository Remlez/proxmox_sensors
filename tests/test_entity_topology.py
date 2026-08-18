"""Tests for dynamic entity discovery."""

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components/proxmox_sensors/logic/entity_topology.py"
)
SPEC = importlib.util.spec_from_file_location("entity_topology", MODULE_PATH)
entity_topology = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(entity_topology)


class EntityTopologyTests(unittest.TestCase):
    def test_new_zfs_pool_changes_topology(self):
        before = entity_topology.entity_topology_keys({"zfs_pools": {}})
        after = entity_topology.entity_topology_keys(
            {"zfs_pools": {"tank": {"health": "ONLINE"}}}
        )
        self.assertEqual({"zfs_pools:tank"}, after - before)

    def test_new_guest_changes_topology(self):
        before = entity_topology.entity_topology_keys({"vms": {"pve1:100": {}}})
        after = entity_topology.entity_topology_keys(
            {"vms": {"pve1:100": {}, "pve1:101": {}}}
        )
        self.assertEqual({"vms:pve1:101"}, after - before)


if __name__ == "__main__":
    unittest.main()
